// skill-cache-optimizer / scripts / analyze.js
//
// Pure Node.js (no npm deps). Compatible with Node 18+ and Bun.
// Invoked from a skill agent via ctx_execute. Returns a single JSON object
// matching schemas/analysis_result.md. Never throws on missing files —
// returns structured errors in `errors[]`.
//
// Usage (from ctx_execute):
//   const { analyzeSkill } = require('<abs path>/scripts/analyze.js');
//   const result = analyzeSkill({ target: '<abs path>', compareAgainst: null });

const fs = require('fs');
const path = require('path');

// ---------- constants ----------
const TOKEN_PER_CHAR = 0.25; // chars -> tokens approximation
const LARGE_CODE_FENCE_LINES = 100;
const LARGE_JSON_BLOCK_LINES = 20;
const LARGE_SECTION_BYTES = 2048;
const REPETITION_BLOCK_MIN_CHARS = 80;
const SKIP_FILES = /(^|[\\/])(backup_|\.bak$|\.tmp$|\.swp$|~$|node_modules|\.git)/i;
const SKILL_FILE_PATTERN = /(^|[\\/])(SKILL\.md|skill\.md)$/;

// ---------- entry ----------
function analyzeSkill(opts) {
  const out = {
    target: opts.target,
    compareAgainst: opts.compareAgainst || null,
    generatedAt: new Date().toISOString(),
    inventory: [],
    volume: {},
    findings: [],
    modularization: [],
    refactorPlan: [],
    scorecard: {},
    risks: [],
    errors: [],
    verificationTrail: {
      filesAnalyzed: 0,
      filesSkipped: 0,
      rulesApplied: [],
      ambiguities: []
    }
  };

  try {
    const files = collectFiles(opts.target, out);
    out.inventory = files.map(f => ({
      path: f.relPath,
      bytes: f.bytes,
      estTokens: Math.round(f.bytes * TOKEN_PER_CHAR),
      isSkillFile: SKILL_FILE_PATTERN.test(f.absPath)
    }));

    const totalBytes = files.reduce((a,f) => a + f.bytes, 0);
    out.volume = {
      totalFiles: files.length,
      totalBytes,
      estTotalTokens: Math.round(totalBytes * TOKEN_PER_CHAR),
      method: 'estimated (chars/4)'
    };
    out.verificationTrail.filesAnalyzed = files.length;

    // Run analyzers
    runDynamicContamination(files, out);
    runInlinePayloadRisk(files, out);
    runRepetition(files, out);
    runModularization(files, out);
    runDeterminism(files, out);
    runRetrievalCompleteness(files, out);
    runContextModeUsage(files, out);
    runWordCopilotBlock(files, out);
    runPreservationGates(files, out);

    // Score
    out.scorecard = scoreSkill(out);

    // Refactor plan derived from findings + modularization
    out.refactorPlan = buildRefactorPlan(out);

    // Optional: compare against another skill
    if (opts.compareAgainst) {
      try {
        const other = analyzeSkill({ target: opts.compareAgainst, compareAgainst: null });
        out.comparison = {
          self: { ces: out.scorecard.ces, estTokens: out.volume.estTotalTokens },
          other: { target: opts.compareAgainst, ces: other.scorecard.ces, estTokens: other.volume.estTotalTokens },
          deltaCES: +(out.scorecard.ces - other.scorecard.ces).toFixed(1),
          deltaTokens: out.volume.estTotalTokens - other.volume.estTotalTokens
        };
      } catch (e) { out.errors.push({ where: 'comparison', message: e.message }); }
    }
  } catch (e) {
    out.errors.push({ where: 'top-level', message: e.message, stack: e.stack });
  }

  return out;
}

// ---------- file collection ----------
function collectFiles(target, out) {
  const stat = fs.statSync(target);
  const root = stat.isDirectory() ? target : path.dirname(target);
  const files = [];

  function walk(dir) {
    let entries;
    try { entries = fs.readdirSync(dir, { withFileTypes: true }); }
    catch (e) { out.errors.push({ where: 'walk', dir, message: e.message }); return; }
    for (const e of entries) {
      const abs = path.join(dir, e.name);
      if (SKIP_FILES.test(abs)) { out.verificationTrail.filesSkipped++; continue; }
      if (e.isDirectory()) walk(abs);
      else if (e.isFile() && /\.(md|markdown|txt|json|ya?ml)$/i.test(e.name)) {
        try {
          const content = fs.readFileSync(abs, 'utf8');
          files.push({
            absPath: abs,
            relPath: path.relative(root, abs).replace(/\\/g,'/'),
            bytes: content.length,
            content
          });
        } catch (err) {
          out.errors.push({ where: 'read', file: abs, message: err.message });
        }
      }
    }
  }

  if (stat.isDirectory()) walk(target);
  else {
    const content = fs.readFileSync(target, 'utf8');
    files.push({ absPath: target, relPath: path.basename(target), bytes: content.length, content });
  }

  return files;
}

// ---------- analyzers ----------

function runDynamicContamination(files, out) {
  out.verificationTrail.rulesApplied.push('dynamic-contamination');
  const patterns = [
    { re: /\b\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2})?\b/g, label: 'hard-coded timestamp', severity: 'high' },
    { re: /\{\{[^}]+\}\}/g, label: 'unsubstituted template variable', severity: 'medium' },
    { re: /\b(current_datetime|now\(\)|today|yesterday|right now)\b/gi, label: 'runtime time reference in prompt body', severity: 'high' },
    { re: /\bGenerated:?\s*\d/g, label: 'generation-time stamp in prompt', severity: 'high' }
  ];
  let totalHits = 0;
  for (const f of files) {
    if (!isPromptFile(f)) continue;
    for (const p of patterns) {
      const matches = [...f.content.matchAll(p.re)];
      if (!matches.length) continue;
      totalHits += matches.length;
      for (const m of matches.slice(0, 3)) {
        out.findings.push({
          id: `DYN-${out.findings.length+1}`,
          severity: p.severity,
          category: 'dynamic-contamination',
          file: f.relPath,
          line: lineOf(f.content, m.index),
          excerpt: snippet(m[0]),
          message: `${p.label}: "${snippet(m[0])}"`,
          fix: 'Move runtime values outside the cacheable prefix (into dynamic payload section)'
        });
      }
      if (matches.length > 3) {
        out.findings.push({
          id: `DYN-${out.findings.length+1}`,
          severity: p.severity,
          category: 'dynamic-contamination',
          file: f.relPath,
          message: `${p.label}: ${matches.length} total occurrences (showing first 3 above)`,
          fix: 'Bulk-relocate runtime references out of cacheable static prefix'
        });
      }
    }
  }
  out._dynamicHits = totalHits;
}

function runInlinePayloadRisk(files, out) {
  out.verificationTrail.rulesApplied.push('inline-payload-risk');
  let risk = 0;
  for (const f of files) {
    if (!isPromptFile(f)) continue;
    const lines = f.content.split('\n');
    let inFence = false, fenceStart = 0, fenceLang = '';
    for (let i=0; i<lines.length; i++) {
      const l = lines[i];
      const fenceMatch = l.match(/^```(\w*)/);
      if (fenceMatch) {
        if (!inFence) { inFence = true; fenceStart = i; fenceLang = fenceMatch[1] || ''; }
        else {
          const span = i - fenceStart;
          const isJson = /^(json|jsonc)$/i.test(fenceLang);
          if (span >= LARGE_CODE_FENCE_LINES || (isJson && span >= LARGE_JSON_BLOCK_LINES)) {
            risk += span;
            out.findings.push({
              id: `PAY-${out.findings.length+1}`,
              severity: span >= 200 ? 'critical' : 'high',
              category: 'inline-payload',
              file: f.relPath,
              line: fenceStart + 1,
              message: `Large inline ${fenceLang || 'code'} block (${span} lines)`,
              fix: 'Externalize to a sibling file (e.g., examples/, schemas/, partials/) and reference by path'
            });
          }
          inFence = false; fenceLang = '';
        }
      }
    }
  }
  out._inlinePayloadLines = risk;
}

function runRepetition(files, out) {
  out.verificationTrail.rulesApplied.push('repetition');
  // Hash normalized paragraphs across all prompt files
  const seen = new Map();
  for (const f of files) {
    if (!isPromptFile(f)) continue;
    const blocks = f.content.split(/\n\s*\n/);
    blocks.forEach((b, idx) => {
      const norm = b.replace(/\s+/g,' ').trim().toLowerCase();
      if (norm.length < REPETITION_BLOCK_MIN_CHARS) return;
      const h = hash(norm);
      if (!seen.has(h)) seen.set(h, []);
      seen.get(h).push({ file: f.relPath, blockIdx: idx, preview: snippet(b, 80) });
    });
  }
  let dupChars = 0;
  for (const [h, occs] of seen) {
    if (occs.length < 2) continue;
    dupChars += occs[0].preview.length * (occs.length - 1);
    out.findings.push({
      id: `REP-${out.findings.length+1}`,
      severity: occs.length >= 4 ? 'high' : 'medium',
      category: 'repetition',
      message: `Duplicate paragraph appears ${occs.length}x across ${new Set(occs.map(o=>o.file)).size} file(s): "${occs[0].preview}"`,
      locations: occs.map(o => `${o.file}#block${o.blockIdx}`),
      fix: 'Extract to partials/ and reference once'
    });
  }
  out._duplicateChars = dupChars;
}

function runModularization(files, out) {
  out.verificationTrail.rulesApplied.push('modularization');
  const externalizable = [
    { re: /^#+\s*.*(REGISTRY|REGISTRIES|SERVICE LIST)/im, folder: 'registries/', label: 'service registry' },
    { re: /^#+\s*.*(SCHEMA|SCHEMAS)/im, folder: 'schemas/', label: 'schema definition' },
    { re: /^#+\s*.*(WORD COPILOT|FORMATTING BLOCK|WORD BLOCK)/im, folder: 'templates/', label: 'word copilot block' },
    { re: /^#+\s*.*(TEMPLATE|REPORT TEMPLATE|OUTPUT STRUCTURE)/im, folder: 'templates/', label: 'output template' },
    { re: /^#+\s*.*(EXAMPLE|EXAMPLES|WORKED EXAMPLE)/im, folder: 'examples/', label: 'example block' }
  ];
  for (const f of files) {
    if (!isPromptFile(f)) continue;
    const sections = splitSections(f.content);
    for (const sec of sections) {
      if (sec.body.length < LARGE_SECTION_BYTES) continue;
      for (const rule of externalizable) {
        if (rule.re.test('# ' + sec.heading)) {
          out.modularization.push({
            file: f.relPath,
            heading: sec.heading,
            bytes: sec.body.length,
            estTokensFreed: Math.round(sec.body.length * TOKEN_PER_CHAR),
            proposedTarget: rule.folder + slugify(sec.heading) + '.md',
            label: rule.label
          });
          break;
        }
      }
    }
  }
}

function runDeterminism(files, out) {
  out.verificationTrail.rulesApplied.push('determinism');
  let score = 100;
  for (const f of files) {
    if (!isPromptFile(f)) continue;
    // Detect non-monotonic heading depth jumps
    const headings = [...f.content.matchAll(/^(#{1,6})\s+(.+)$/gm)];
    let prevDepth = 0;
    for (const h of headings) {
      const d = h[1].length;
      if (prevDepth && d > prevDepth + 1) {
        score -= 2;
        out.findings.push({
          id: `DET-${out.findings.length+1}`,
          severity: 'low',
          category: 'determinism',
          file: f.relPath,
          line: lineOf(f.content, h.index),
          message: `Heading depth jumps from H${prevDepth} to H${d}`,
          fix: 'Normalize heading hierarchy (no >1 level jumps)'
        });
      }
      prevDepth = d;
    }
  }
  out._determinismScore = Math.max(0, score);
}

function runRetrievalCompleteness(files, out) {
  out.verificationTrail.rulesApplied.push('retrieval-completeness');
  for (const f of files) {
    if (!isPromptFile(f)) continue;
    const mentionsQuery = /\b(search|query|fetch|retrieve|list).*(incident|record|item|page|result)/i.test(f.content);
    if (!mentionsQuery) continue;
    const missing = [];
    if (!/pagination|nextPageToken|@odata\.count|nextCursor/i.test(f.content)) missing.push('pagination');
    if (!/dedup|deduplicate|unique|distinct/i.test(f.content)) missing.push('deduplication');
    if (!/reconcil|cross-?check|secondary.*pass|completeness/i.test(f.content)) missing.push('reconciliation');
    if (missing.length) {
      out.findings.push({
        id: `RET-${out.findings.length+1}`,
        severity: missing.includes('pagination') ? 'high' : 'medium',
        category: 'retrieval-completeness',
        file: f.relPath,
        message: `Query/retrieval workflow missing: ${missing.join(', ')}`,
        fix: 'Add explicit ' + missing.join(' + ') + ' steps to the retrieval contract'
      });
    }
  }
}

function runContextModeUsage(files, out) {
  out.verificationTrail.rulesApplied.push('context-mode-usage');
  for (const f of files) {
    if (!isPromptFile(f)) continue;
    const hasLargeDataOps = /\b(transcript|bridge|payload|JSON dump|large markdown|>\s*10\s*KB|kusto|telemetry)/i.test(f.content);
    const hasCtxMode = /ctx_execute|ctx_execute_file|ctx_fetch_and_index|ctx_index/i.test(f.content);
    if (hasLargeDataOps && !hasCtxMode) {
      out.findings.push({
        id: `CTX-${out.findings.length+1}`,
        severity: 'high',
        category: 'context-mode-usage',
        file: f.relPath,
        message: 'Skill references large data ops but does not mandate context-mode (ctx_execute / ctx_execute_file)',
        fix: 'Add a CONTEXT-MODE REQUIRED section and route large payload handling through ctx_execute_file'
      });
    }
  }
}

function runWordCopilotBlock(files, out) {
  out.verificationTrail.rulesApplied.push('word-copilot-block');
  const skillFile = files.find(f => SKILL_FILE_PATTERN.test(f.absPath));
  if (!skillFile) return;
  const hasInline = /===\s*INSTRUCTIONS FOR WORD COPILOT\s*===/i.test(skillFile.content);
  const hasExternal = files.some(f => /word[_-]copilot/i.test(f.relPath));
  if (hasInline && !hasExternal) {
    out.findings.push({
      id: `WCB-${out.findings.length+1}`,
      severity: 'low',
      category: 'modularization',
      file: skillFile.relPath,
      message: 'Word Copilot block is inline; recommend externalizing for cache stability',
      fix: 'Move to templates/word_copilot_block.md and reference by path'
    });
  }
}

function runPreservationGates(files, out) {
  out.verificationTrail.rulesApplied.push('preservation-gates');
  // Detect "EXECUTION IS INVALID" presence as a positive signal — note in trail
  let count = 0;
  for (const f of files) {
    if (!isPromptFile(f)) continue;
    count += (f.content.match(/EXECUTION IS INVALID/g) || []).length;
  }
  out._executionGates = count;
}

// ---------- scoring ----------
function scoreSkill(out) {
  const totalChars = out.volume.totalBytes || 1;
  const dynamicContaminationPct = Math.min(100, ((out._dynamicHits || 0) * 50) / Math.max(1, out.volume.totalFiles));
  const inlinePayloadRisk = Math.min(100, ((out._inlinePayloadLines || 0) / 10));
  const repetitionPct = Math.min(100, ((out._duplicateChars || 0) / totalChars) * 100);
  const modularizableBytes = out.modularization.reduce((a,m) => a + m.bytes, 0);
  const modularizationScore = Math.max(0, 100 - Math.min(100, (modularizableBytes / totalChars) * 100));
  const determinismScore = out._determinismScore != null ? out._determinismScore : 100;
  const cacheablePrefixPct = Math.max(0, 100 - dynamicContaminationPct - (repetitionPct * 0.5));

  const ces = Math.round(
    0.30 * cacheablePrefixPct +
    0.20 * (100 - dynamicContaminationPct) +
    0.15 * modularizationScore +
    0.15 * (100 - inlinePayloadRisk) +
    0.10 * determinismScore +
    0.10 * (100 - repetitionPct)
  );

  let band;
  if (ces >= 90) band = 'Excellent';
  else if (ces >= 75) band = 'Good';
  else if (ces >= 60) band = 'Fair';
  else band = 'Poor';

  return {
    ces, band,
    subScores: {
      cacheablePrefixPct: round(cacheablePrefixPct),
      dynamicContaminationPct: round(dynamicContaminationPct),
      modularizationScore: round(modularizationScore),
      inlinePayloadRisk: round(inlinePayloadRisk),
      determinismScore: round(determinismScore),
      repetitionPct: round(repetitionPct)
    },
    method: 'modeled (heuristic weights — see SKILL.md)',
    executionGatesDetected: out._executionGates || 0
  };
}

function buildRefactorPlan(out) {
  const plan = [];
  // Modularization → top priority
  for (const m of out.modularization) {
    plan.push({
      priority: 'high',
      action: `Externalize section "${m.heading}" from ${m.file} → ${m.proposedTarget}`,
      addresses: 'modularization',
      projectedTokenSavings: m.estTokensFreed,
      method: 'estimated',
      risk: 'low',
      preservation: 'No content removed; SKILL.md references the new file path'
    });
  }
  // Critical findings → next
  for (const f of out.findings.filter(x => x.severity === 'critical')) {
    plan.push({
      priority: 'critical',
      action: f.fix || 'Address finding',
      addresses: f.id,
      projectedTokenSavings: null,
      method: 'estimated',
      risk: 'medium',
      preservation: 'Validation rigor must remain identical'
    });
  }
  // High findings
  for (const f of out.findings.filter(x => x.severity === 'high').slice(0, 10)) {
    plan.push({
      priority: 'high',
      action: f.fix || 'Address finding',
      addresses: f.id,
      projectedTokenSavings: null,
      method: 'estimated',
      risk: 'low',
      preservation: 'No semantic change to outputs'
    });
  }
  return plan;
}

// ---------- helpers ----------
function isPromptFile(f) { return /\.md$/i.test(f.absPath); }
function lineOf(content, idx) { return content.slice(0, idx).split('\n').length; }
function snippet(s, n=120) { return s.replace(/\s+/g,' ').slice(0, n); }
function slugify(s) { return s.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'').slice(0, 40); }
function round(n) { return Math.round(n * 10) / 10; }
function hash(s) {
  let h = 5381;
  for (let i=0; i<s.length; i++) h = ((h << 5) + h) ^ s.charCodeAt(i);
  return (h >>> 0).toString(16);
}
function splitSections(md) {
  const lines = md.split('\n');
  const sections = [];
  let cur = { heading: '(prologue)', body: '' };
  for (const l of lines) {
    const h = l.match(/^#{1,3}\s+(.+)$/);
    if (h) { if (cur.body || cur.heading !== '(prologue)') sections.push(cur); cur = { heading: h[1].trim(), body: '' }; }
    else cur.body += l + '\n';
  }
  sections.push(cur);
  return sections;
}

module.exports = { analyzeSkill };
