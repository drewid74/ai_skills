# Token Cache Optimization — ai_skills_paid

## TL;DR

> **Quick Summary**: Restructure 7 SKILL.md files for LLM prompt cache efficiency — prefix-heavy ordering, shared preamble, deduplication, front-loaded triggers.
> 
> **Deliverables**:
> - 7 restructured SKILL.md files with standardized cache-optimized section ordering
> - Proper `name` + `description` frontmatter on all files
> - Deduplicated content between the 430-guide and 430-promptkit pair
> - Zero content loss — only structural reorganization
> 
> **Estimated Effort**: Medium
> **Parallel Execution**: YES — 7 waves (1 foundation + 6 parallel restructures + 1 verify)
> **Critical Path**: Task 1 (define template) → Tasks 2-8 (apply to each file) → Task 9 (verify)

---

## Context

### Original Request
"Further optimize all skills for cached token optimization" — applying 4 strategies: prefix-heavy structure, shared preamble extraction, deduplication, front-loaded triggers.

### Interview Summary
**Key Discussions**:
- Scope: 7 skills in `C:\Users\afair\dev\ai_skills_paid` (6 promptkits + 1 guide + token-burn-all-sources)
- No content loss — fidelity preserved
- All 4 strategies to be applied

**Research Findings**:
- 5/6 promptkit files lack `description` in frontmatter (can't be routed by opencode)
- Duplicate H1 headers in most files (pure token waste — 2 identical H1s)
- The `430-guide` and `430-promptkit` share verbatim blocks: evidence map rules, verification checklist, closing philosophy
- `token-burn-all-sources` already optimized (gold standard: concise, action-oriented, proper frontmatter)
- "How to use" sections are unique per skill (not shared boilerplate)
- Each promptkit has numbered `## Prompt N` sections with ` ```prompt ``` ` blocks containing the actual prompt text

### Metis Review
**Identified Gaps** (addressed):
- Loading pattern: Skills are loaded individually by opencode's skill router — shared preamble benefits repeated invocations of the same skill, not cross-skill caching
- Prompt block preservation: Must be byte-identical — GUARDRAIL added
- Frontmatter `description` addition: Confirmed useful — opencode skill router uses it for matching
- Consolidation of 430 pair: Dedup shared verbatim text, but keep as separate files
- Acceptance criteria: Added token count comparison and byte-diff requirements

---

## Work Objectives

### Core Objective
Restructure each SKILL.md so that static/invariant content occupies the top of the file (maximizing LLM prompt cache hits on repeat invocations) and variable/prompt content sits at the bottom.

### Concrete Deliverables
- 7 SKILL.md files with standardized structure
- Each file follows the canonical section ordering defined in Task 1
- Shared preamble text (identical bytes) at the top of each promptkit file
- `description` field added to all frontmatter blocks

### Definition of Done
- [ ] All 7 files restructured
- [ ] `diff` between old and new shows zero changes inside ` ```prompt ``` ` blocks
- [ ] Token count ≤ original for every file
- [ ] All frontmatter includes `name` and `description`
- [ ] No duplicate H1 headers remain
- [ ] Shared preamble text is byte-identical across all promptkit files

### Must Have
- Byte-identical prompt block content (text inside ` ```prompt ``` ` fences)
- Proper `name` and `description` frontmatter fields
- Standardized section ordering across all files
- Removed duplicate H1 headers
- Front-loaded trigger/description before instructional content

### Must NOT Have (Guardrails)
- DO NOT alter text inside ` ```prompt ``` ` blocks — byte-identical preservation
- DO NOT merge files — the 430-guide and 430-promptkit remain separate
- DO NOT reword trigger phrases from the original content
- DO NOT change `type` or `project` frontmatter values
- DO NOT add content that wasn't in the original files
- DO NOT normalize heading levels inside prompt blocks

---

## Verification Strategy (MANDATORY)

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: N/A (content restructuring, not code)
- **Automated tests**: NO (content files, not executable)
- **Framework**: N/A

### QA Policy
Every task includes agent-executed verification via diff and byte comparison.
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Content preservation**: Byte-compare prompt blocks before/after
- **Structure verification**: Verify section ordering matches template
- **Token efficiency**: Character/word count comparison

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Foundation — define canonical structure):
└── Task 1: Define canonical section template + shared preamble [quick]

Wave 2 (Apply to each file — MAX PARALLEL):
├── Task 2: Restructure agent-product-analytics SKILL.md [quick]
├── Task 3: Restructure ai-office-files-guide SKILL.md [quick]
├── Task 4: Restructure ai-office-files-promptkit SKILL.md [quick]
├── Task 5: Restructure organize-project-files SKILL.md [quick]
├── Task 6: Restructure public-ai-work-apprenticeship SKILL.md [quick]
├── Task 7: Restructure opus-benchmark-routing SKILL.md [quick]
└── Task 8: Update token-burn-all-sources SKILL.md (add description) [quick]

Wave 3 (Deduplication):
└── Task 9: Deduplicate shared content between 430-guide and 430-promptkit [quick]

Wave FINAL (Verification — parallel reviews):
├── Task F1: Byte-diff all prompt blocks (oracle)
├── Task F2: Token count comparison + structure validation (unspecified-high)
└── Task F3: Routing test — verify description triggers match (unspecified-high)
-> Present results -> Get explicit user okay
```

### Dependency Matrix

| Task | Depends On | Blocks |
|------|-----------|--------|
| 1 | — | 2-8 |
| 2-8 | 1 | 9, F1-F3 |
| 9 | 3, 4 | F1-F3 |
| F1-F3 | 2-9 | — |

### Agent Dispatch Summary

- **Wave 1**: 1 task → `quick`
- **Wave 2**: 7 tasks → all `quick`
- **Wave 3**: 1 task → `quick`
- **FINAL**: 3 tasks → `oracle`, `unspecified-high`, `unspecified-high`

---

## TODOs

- [x] 1. Define Canonical Section Template + Shared Preamble

  **What to do**:
  - Create a reference document `.sisyphus/drafts/canonical-skill-template.md` that defines the exact section ordering all skills must follow
  - Define the shared preamble text (byte-identical across all promptkit-type files)
  - Canonical ordering for promptkit type:
    ```
    ---
    name: {slug}
    title: "{original title}"
    description: "{1-2 sentence trigger description for skill routing}"
    type: "promptkit"
    label: "Prompt Kit"
    project: "{original project value}"
    ---

    # {Single H1 title — no duplicates}

    {1-2 sentence summary of what this kit does}

    ## Triggers

    Use this skill when: {comma-separated trigger phrases derived from title + "How to use" section}

    ## How to use this kit

    {Original "How to use" content — preserved verbatim}

    ---

    ## Prompt 1: {Name}

    **Job:** {description}
    **When to use:** {triggers}

    ```prompt
    {BYTE-IDENTICAL original prompt text}
    ```

    [... additional prompts ...]
    ```
  - Canonical ordering for guide type follows same pattern but with `## Job` / `## Use When` / `## Safe To Use Checklist` sections preserved
  - Canonical ordering for token-burn type: already correct, just add `description` field

  **Must NOT do**:
  - Do not invent trigger phrases — derive from existing title/intro text
  - Do not alter the "How to use" section content

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
    - No domain skills needed — pure structural template work

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1 (solo)
  - **Blocks**: Tasks 2-8
  - **Blocked By**: None

  **References**:
  - `token-burn-all-sources/SKILL.md` — Gold standard structure to model after
  - `20260512-161-promptkit-1.md:1-24` — Representative promptkit intro pattern
  - `20260531-43a-promptkit-1.md:1-24` — Another promptkit with clean "How to use"

  **Acceptance Criteria**:
  - [ ] Template document exists at `.sisyphus/drafts/canonical-skill-template.md`
  - [ ] Template specifies exact section ordering for promptkit, guide, and token-burn types
  - [ ] Shared preamble text is defined (the structural sections that will be byte-identical)

  **QA Scenarios**:

  ```
  Scenario: Template covers all 3 file types
    Tool: Bash
    Steps:
      1. Read the template file
      2. Verify it contains sections for: promptkit, guide, token-burn types
      3. Verify each type has explicit section ordering
    Expected Result: All 3 types documented with exact heading hierarchy
    Evidence: .sisyphus/evidence/task-1-template-coverage.txt

  Scenario: Template section ordering matches gold standard
    Tool: Bash
    Steps:
      1. Extract headings from token-burn-all-sources/SKILL.md
      2. Compare against template's token-burn section
      3. Verify ordering is identical
    Expected Result: Heading sequence matches exactly
    Evidence: .sisyphus/evidence/task-1-gold-standard-match.txt
  ```

  **Commit**: NO (template is working artifact, not shipped)

---

- [x] 2. Restructure agent-product-analytics SKILL.md

  **What to do**:
  - Source: `ai_skills_paid/agent-product-analytics/SKILL.md` (after reorg task moves it)
  - Apply canonical template from Task 1
  - Add `name: agent-product-analytics` to frontmatter
  - Add `description:` field derived from title + intro: "Instrument agent product analytics — generate starter event code, turn corrections into eval cases, read completion-vs-acceptance numbers through quadrant framework"
  - Remove duplicate H1 (currently has 2 H1 headers on lines 8 and 10)
  - Keep single H1: "Agent Product Analytics Prompt Kit"
  - Preserve section ordering: frontmatter → H1 → summary → triggers → How to use → prompts
  - Verify all 3 ` ```prompt ``` ` blocks are byte-identical after restructuring

  **Must NOT do**:
  - Do not alter prompt block content
  - Do not change the "How to use this kit" text
  - Do not reword the Job/When to use descriptions

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 3-8)
  - **Blocks**: Task 9, F1-F3
  - **Blocked By**: Task 1

  **References**:
  - `ai_skills_paid/20260512-161-promptkit-1.md` — Source file (322 lines)
  - `.sisyphus/drafts/canonical-skill-template.md` — Template to follow (from Task 1)
  - `token-burn-all-sources/SKILL.md` — Gold standard structure

  **Acceptance Criteria**:
  - [ ] Frontmatter contains `name: agent-product-analytics` and `description: "..."`
  - [ ] Single H1 header (no duplicates)
  - [ ] All 3 prompt blocks byte-identical to original
  - [ ] Character count ≤ original

  **QA Scenarios**:

  ```
  Scenario: Prompt blocks preserved
    Tool: Bash
    Steps:
      1. Extract all text between ```prompt and ``` fences from original file
      2. Extract same from restructured file
      3. diff the two extractions
    Expected Result: Zero differences
    Evidence: .sisyphus/evidence/task-2-prompt-diff.txt

  Scenario: Frontmatter valid
    Tool: Bash
    Steps:
      1. head -10 agent-product-analytics/SKILL.md
      2. Verify contains name:, description:, type:, label:, project:
    Expected Result: All 5 fields present between --- markers
    Evidence: .sisyphus/evidence/task-2-frontmatter.txt

  Scenario: No duplicate H1
    Tool: Bash
    Steps:
      1. grep "^# " agent-product-analytics/SKILL.md | wc -l
    Expected Result: Exactly 1
    Evidence: .sisyphus/evidence/task-2-h1-count.txt
  ```

  **Commit**: YES (groups with Tasks 3-8)
  - Message: `chore(skills): restructure paid skills for token cache optimization`
  - Files: `agent-product-analytics/SKILL.md`

---

- [x] 3. Restructure ai-office-files-guide SKILL.md

  **What to do**:
  - Source: `ai_skills_paid/ai-office-files-guide/SKILL.md`
  - Apply canonical template (guide variant)
  - Add `name: ai-office-files-guide`
  - Add `description:` derived from content: "Practical guide to using AI with Excel and PowerPoint — source verification, formula risk scanning, deck architecture, evidence mapping, and truth-layer workflows for Office files"
  - Remove duplicate H1 (has "Stop Asking AI To Make A Deck" duplicated)
  - This file uses a different structure: `## Job` / `## Use When` / `## Safe To Use Checklist` — preserve these subsection patterns
  - Reorder so: frontmatter → H1 → summary → triggers → "The Pain Map" intro → prompt sections
  - Preserve all ` ```prompt ``` ` blocks byte-identical

  **Must NOT do**:
  - Do not merge with 430-promptkit (separate file)
  - Do not alter prompt blocks
  - Do not remove "Pretty-But-Wrong Checklist" or "The Operating Rule" sections

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 2, 4-8)
  - **Blocks**: Task 9, F1-F3
  - **Blocked By**: Task 1

  **References**:
  - `ai_skills_paid/20260512-430-guide-substack-companion-guide.md` — Source file (417+ lines)
  - `.sisyphus/drafts/canonical-skill-template.md` — Template (guide variant)

  **Acceptance Criteria**:
  - [ ] Frontmatter contains `name` and `description`
  - [ ] Single H1 header
  - [ ] All prompt blocks byte-identical
  - [ ] "Pretty-But-Wrong Checklist" and "The Operating Rule" sections preserved

  **QA Scenarios**:

  ```
  Scenario: Prompt blocks preserved
    Tool: Bash
    Steps:
      1. Extract prompt blocks from original and restructured
      2. diff them
    Expected Result: Zero differences
    Evidence: .sisyphus/evidence/task-3-prompt-diff.txt

  Scenario: Guide-specific sections preserved
    Tool: Bash
    Steps:
      1. grep "## Pretty-But-Wrong" ai-office-files-guide/SKILL.md
      2. grep "## The Operating Rule" ai-office-files-guide/SKILL.md
    Expected Result: Both present
    Evidence: .sisyphus/evidence/task-3-guide-sections.txt
  ```

  **Commit**: YES (groups with Wave 2)

---

- [x] 4. Restructure ai-office-files-promptkit SKILL.md

  **What to do**:
  - Source: `ai_skills_paid/ai-office-files-promptkit/SKILL.md`
  - Apply canonical template (promptkit variant)
  - Add `name: ai-office-files-promptkit`
  - Add `description:` derived from content: "Office file truth workflow prompts — source packet building, workbook inspection, deck architecture, evidence mapping, and pre-share verification for Excel and PowerPoint"
  - Remove duplicate H1
  - This file uses repeated `## Job` / `## Use When` / `## Safe To Use Checklist` pattern for each prompt — preserve this structure
  - Reorder: frontmatter → H1 → summary → triggers → How To Use → prompt groups
  - Preserve all prompt blocks and "Operating Rule" / "Final Human Gate" sections

  **Must NOT do**:
  - Do not merge with 430-guide
  - Do not alter prompt blocks
  - Do not remove "Final Human Gate" or "Operating Rule"

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 9, F1-F3
  - **Blocked By**: Task 1

  **References**:
  - `ai_skills_paid/20260512-430-promptkit-substack-companion-prompt-kit.md` — Source file
  - `.sisyphus/drafts/canonical-skill-template.md` — Template

  **Acceptance Criteria**:
  - [ ] Frontmatter contains `name` and `description`
  - [ ] Single H1 header
  - [ ] All prompt blocks byte-identical
  - [ ] "Final Human Gate" and "Operating Rule" sections preserved

  **QA Scenarios**:

  ```
  Scenario: Prompt blocks preserved
    Tool: Bash
    Steps:
      1. Extract and diff all prompt blocks
    Expected Result: Zero differences
    Evidence: .sisyphus/evidence/task-4-prompt-diff.txt

  Scenario: Gate sections preserved
    Tool: Bash
    Steps:
      1. grep "## Final Human Gate" ai-office-files-promptkit/SKILL.md
      2. grep "## Operating Rule" ai-office-files-promptkit/SKILL.md
    Expected Result: Both present
    Evidence: .sisyphus/evidence/task-4-gate-sections.txt
  ```

  **Commit**: YES (groups with Wave 2)

---

- [x] 5. Restructure organize-project-files SKILL.md

  **What to do**:
  - Source: `ai_skills_paid/organize-project-files/SKILL.md`
  - Apply canonical template
  - Add `name: organize-project-files`
  - Add `description:` derived: "Organize project files before asking AI to write — project room builder, source inventory, grounded draft from clean room, and project room refresh prompts"
  - Remove duplicate H1 (lines 7 and 9 both start with #)
  - Reorder: frontmatter → H1 → summary → triggers → prompts (this file has no "How to use" section)
  - Preserve all 4 prompt blocks

  **Must NOT do**:
  - Do not invent a "How to use" section that doesn't exist
  - Do not alter prompt blocks

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: F1-F3
  - **Blocked By**: Task 1

  **References**:
  - `ai_skills_paid/20260512-721-promptkit-1.md` — Source file
  - `.sisyphus/drafts/canonical-skill-template.md` — Template

  **Acceptance Criteria**:
  - [ ] Frontmatter contains `name` and `description`
  - [ ] Single H1
  - [ ] All 4 prompt blocks byte-identical

  **QA Scenarios**:

  ```
  Scenario: Prompt blocks preserved
    Tool: Bash
    Steps:
      1. Extract and diff all prompt blocks
    Expected Result: Zero differences
    Evidence: .sisyphus/evidence/task-5-prompt-diff.txt
  ```

  **Commit**: YES (groups with Wave 2)

---

- [x] 6. Restructure public-ai-work-apprenticeship SKILL.md

  **What to do**:
  - Source: `ai_skills_paid/public-ai-work-apprenticeship/SKILL.md`
  - Apply canonical template
  - Add `name: public-ai-work-apprenticeship`
  - Add `description:` derived: "Make invisible AI work visible — workflow formatter for public posts, sensitivity boundary drawer, and senior leader public work starter prompts"
  - Remove duplicate H1
  - Preserve "How to use this kit" section verbatim
  - Preserve all 3 prompt blocks

  **Must NOT do**:
  - Do not alter prompt blocks
  - Do not remove the "How to use" guidance about which prompt to use when

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: F1-F3
  - **Blocked By**: Task 1

  **References**:
  - `ai_skills_paid/20260512-837-promptkit-1.md` — Source file
  - `.sisyphus/drafts/canonical-skill-template.md` — Template

  **Acceptance Criteria**:
  - [ ] Frontmatter contains `name` and `description`
  - [ ] Single H1
  - [ ] All 3 prompt blocks byte-identical

  **QA Scenarios**:

  ```
  Scenario: Prompt blocks preserved
    Tool: Bash
    Steps:
      1. Extract and diff all prompt blocks
    Expected Result: Zero differences
    Evidence: .sisyphus/evidence/task-6-prompt-diff.txt
  ```

  **Commit**: YES (groups with Wave 2)

---

- [x] 7. Restructure opus-benchmark-routing SKILL.md

  **What to do**:
  - Source: `ai_skills_paid/opus-benchmark-routing/SKILL.md`
  - Apply canonical template
  - Add `name: opus-benchmark-routing`
  - Add `description:` derived: "Route tasks to the right model — task router, eval set builder, failure-mode verification planner, and outcomes-to-cost mapper for multi-model workflows"
  - Remove duplicate H1
  - Preserve "How to use this kit" section verbatim
  - Preserve all 4 prompt blocks

  **Must NOT do**:
  - Do not alter prompt blocks
  - Do not remove model-specific references (Opus 4.8, Codex/5.5, GPT-5.5)

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: F1-F3
  - **Blocked By**: Task 1

  **References**:
  - `ai_skills_paid/20260531-43a-promptkit-1.md` — Source file (220 lines)
  - `.sisyphus/drafts/canonical-skill-template.md` — Template

  **Acceptance Criteria**:
  - [ ] Frontmatter contains `name` and `description`
  - [ ] Single H1
  - [ ] All 4 prompt blocks byte-identical

  **QA Scenarios**:

  ```
  Scenario: Prompt blocks preserved
    Tool: Bash
    Steps:
      1. Extract and diff all prompt blocks
    Expected Result: Zero differences
    Evidence: .sisyphus/evidence/task-7-prompt-diff.txt
  ```

  **Commit**: YES (groups with Wave 2)

---

- [x] 8. Update token-burn-all-sources SKILL.md (add description)

  **What to do**:
  - Source: `ai_skills_paid/token-burn-all-sources/SKILL.md`
  - Already well-structured — only add `description` field to frontmatter if not present
  - The existing `description:` in frontmatter is already good — verify it matches routing needs
  - No structural changes needed — this is the gold standard

  **Must NOT do**:
  - Do not restructure this file — it's already optimal
  - Do not touch the workflow, source rules, or done means sections

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: F1-F3
  - **Blocked By**: Task 1

  **References**:
  - `ai_skills_paid/token-burn-all-sources/SKILL.md` — Already read, already optimal

  **Acceptance Criteria**:
  - [ ] Frontmatter has `name` and `description` fields
  - [ ] No other changes made

  **QA Scenarios**:

  ```
  Scenario: File unchanged except frontmatter
    Tool: Bash
    Steps:
      1. diff original vs new (excluding frontmatter block)
    Expected Result: Zero differences outside frontmatter
    Evidence: .sisyphus/evidence/task-8-no-change.txt
  ```

  **Commit**: YES (groups with Wave 2)

---

- [x] 9. Deduplicate shared content between 430-guide and 430-promptkit

  **What to do**:
  - After Tasks 3 and 4 complete, identify verbatim-shared blocks between the two files
  - Known shared content:
    - Evidence map verification table format
    - "Use AI everywhere in Office work, but do not let it hide the truth layer" philosophy paragraph
    - "Every claim should know where it came from..." paragraph
    - "That is the difference between an AI-generated Office file..." paragraph
    - Evidence gap review rules block
  - Strategy: Keep the FULL content in the **guide** (it's the comprehensive reference). In the **promptkit**, replace duplicated explanatory text with a brief cross-reference note: `> See ai-office-files-guide for the full rationale behind this workflow.`
  - Only deduplicate EXPLANATORY prose — never touch prompt blocks or operational instructions

  **Must NOT do**:
  - Do not remove content from the guide
  - Do not alter prompt blocks in either file
  - Do not remove "Safe To Use Checklist" or "Operating Rule" from the promptkit
  - Do not merge files

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (sequential after Wave 2)
  - **Blocks**: F1-F3
  - **Blocked By**: Tasks 3, 4

  **References**:
  - `ai-office-files-guide/SKILL.md` — Full guide (post-Task 3)
  - `ai-office-files-promptkit/SKILL.md` — Companion kit (post-Task 4)

  **Acceptance Criteria**:
  - [ ] Promptkit is shorter than before (duplicated prose removed)
  - [ ] Guide is unchanged in content length
  - [ ] All prompt blocks in both files byte-identical to originals
  - [ ] Cross-reference note present in promptkit where text was removed

  **QA Scenarios**:

  ```
  Scenario: Promptkit shorter, guide unchanged
    Tool: Bash
    Steps:
      1. wc -c ai-office-files-guide/SKILL.md (should equal post-Task-3 size)
      2. wc -c ai-office-files-promptkit/SKILL.md (should be < post-Task-4 size)
    Expected Result: Guide same size, promptkit reduced
    Evidence: .sisyphus/evidence/task-9-size-comparison.txt

  Scenario: Prompt blocks untouched
    Tool: Bash
    Steps:
      1. Extract prompt blocks from both files
      2. Diff against originals
    Expected Result: Zero differences in prompt blocks
    Evidence: .sisyphus/evidence/task-9-prompt-diff.txt
  ```

  **Commit**: YES
  - Message: `chore(skills): deduplicate shared content between office-files guide and promptkit`

---

## Final Verification Wave

- [x] F1. **Prompt Block Byte-Diff** — `oracle`
  For every SKILL.md, extract all ` ```prompt ``` ` blocks. Compare byte-for-byte against the original file's prompt blocks. ZERO differences permitted. Any diff = REJECT.
  Output: `Files [7/7] | Prompt Blocks [N/N identical] | VERDICT: APPROVE/REJECT`

- [x] F2. **Token Count + Structure Validation** — `unspecified-high`
  For each file: count characters/tokens before and after. Verify new ≤ old. Verify section ordering matches canonical template from Task 1. Verify no duplicate H1 headers. Verify frontmatter has `name` + `description`.
  Output: `Token delta per file | Structure [7/7 compliant] | VERDICT`

- [x] F3. **Routing Test** — `unspecified-high`
  For each skill's `description` field: verify it contains meaningful trigger phrases that would match user intent. Verify no description is generic/empty. Compare against original title/intro content to ensure trigger coverage.
  Output: `Skills [7/7] | Trigger coverage [HIGH/MED/LOW per skill] | VERDICT`

---

## Commit Strategy

- **Single commit**: `chore(skills): restructure paid skills for token cache optimization`
- Files: all 7 SKILL.md files in `ai_skills_paid/*/`
- Pre-commit: diff verification passes

---

## Success Criteria

### Verification Commands
```bash
# Verify no prompt block content changed
diff <(grep -A999 '```prompt' old/file.md | grep -B999 '```') <(grep -A999 '```prompt' new/file.md | grep -B999 '```')

# Verify token reduction
wc -c old/file.md new/file.md  # new ≤ old

# Verify frontmatter
head -10 */SKILL.md | grep -c "description:"  # should be 7
```

### Final Checklist
- [ ] All prompt blocks byte-identical to originals
- [ ] All files have `name` + `description` in frontmatter
- [ ] No duplicate H1 headers
- [ ] Section ordering matches canonical template
- [ ] Token count ≤ original for every file
- [ ] Shared preamble byte-identical across promptkit files
