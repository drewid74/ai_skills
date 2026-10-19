---
name: model-archive-management
description: "Use this when: check if a model is already downloaded, back up model weights, pull a new model checkpoint, verify a model download, archive AI model weights, what models do we have, is this model already mirrored, resume a stalled model backup, model archive drifted, which models should I pull next, pin a model to match a serving node"
---

# Model Archive Management

## Identity
You manage a local/NAS archive of downloaded model weights for self-hosted inference. Check what's actually on disk before claiming anything is missing or present. Never trust a directory's existence, or its name, as proof it holds real weights.

## Stack Defaults

| Layer | Choice | Why |
|-------|--------|-----|
| Archive layout | `<MIRROR_ROOT>/<org>__<repo>/` flat, double-underscore | 1:1 with the HF repo id; trivially reversible; no nested-path ambiguity |
| Download tool | `huggingface_hub` CLI (`hf download`) | Verifies each file's hash/ETag during transfer, resumes on failure, no custom integrity code needed |
| Integrity check | Trust `hf download`'s built-in verification | Re-hashing a completed, zero-exit-code download is redundant unless corruption is specifically suspected |
| Pin method | `--revision <commit>` | Matches a checkpoint already verified/deployed elsewhere bit-for-bit, not "whatever HEAD resolves to today" |
| Record trail | One append-only log line per pull (repo, filter/revision, size, destination, success/failure) | An archive with no log is unverifiable provenance — "did we pull this?" shouldn't require re-deriving from the filesystem |
| Status tracker | A persistent mirrored/urgent/blocked/skip file, not memory | Re-deriving archive status from scratch every time is how backlogs form in the first place |

## Decision Framework

### Before pulling anything
- Check the **real** archive root for actual file content — `find <root> -maxdepth 1 -type d` then size each (`du -sh */`) — not just that a correctly-named directory exists. An empty or near-empty directory with the right name is not evidence a model is mirrored.
- If more than one candidate archive path exists on the host (an old convention, a staging path, a serving-node cache), verify which one is **actually populated** before trusting either as canonical. A README or a prior note naming "the" path can be stale.
- Cross-reference against any existing status tracker before concluding something is missing — but verify the tracker against the live filesystem too; it drifts if nothing re-checks it.

### Pulling
- If pulling the exact checkpoint a serving node already runs → find that node's pinned revision (its deploy config / `.env` / `MODEL_REVISION`) and pull with `--revision`, not HEAD. This gets bit-identical content without touching the live node's disk or network.
- If pulling a specific quant (GGUF/AWQ/etc.) rather than the full repo → use `--include '<glob>'`; don't download the full repo "to be safe" when only one quant is needed.
- If the official/first-party drafter or variant doesn't exist yet → search the Hub by `base_model` tag, pick the community candidate with materially more downloads than any alternative, and **label it explicitly as a stand-in** pending the official release. Never silently treat a guessed or substituted repo name as equivalent to the real thing.
- Default → full repo, no revision pin, unless one of the above applies.

### Verifying
- If `hf download` exits 0 → that already covers transfer-integrity; don't add a second hashing pass as routine practice.
- If corruption is specifically suspected → compare local file hashes against the Hub's manifest (`GET /api/models/<org>/<repo>?blobs=true`, the `lfs.sha256` field) for LFS-tracked files only. Small non-LFS files report a git blob SHA1 there, not a content SHA256 — don't compare those the same way.

### Keeping a model list current
- Treat any "models we should have" list as a dated snapshot, never a standing fact. Label it with the date it was compiled and its source (an audit, a horizon scan, a vendor announcement).
- Re-verify a specific repo name/revision against a primary source (the org's own HF page, a release tag) before acting on it — secondary aggregators and reprints drift out of date silently.
- Prefer one persistent tracker (mirrored / urgent / blocked / skip, with a reason per row) over re-deriving status from scratch each session.

## Anti-Patterns

| Don't | Why | Do Instead |
|-------|-----|------------|
| Treat directory existence as "mirrored" | An empty placeholder dir is indistinguishable from a populated one in a plain `ls` | Check file count/size (`du -sh`, `find -type f`) before trusting any status claim |
| Re-download a model just to "double-check" it's backed up | Wastes hours/bandwidth; `hf download` already resumes and verifies | Re-run the same `hf download` command — it no-ops on an already-complete, verified local copy |
| Guess an official repo name for a drafter/variant that doesn't exist yet | Pulls the wrong artifact, or silently nothing | Search by `base_model` tag; if no official exists, say so explicitly and pick the most-downloaded community one as a labeled stand-in |
| Run a full post-download hash-verification pass by default | Redundant with the download tool's own transfer-time check; costs real time re-reading a large archive for no new information | Reserve manual re-hashing for a specific, articulated corruption suspicion |
| Let a "current model list" sit undated | Readers can't tell a two-month-old scan from today's state, and will act on stale repo names/sizes | Date every snapshot; re-check against a primary source before any action-driving decision |
| Assume the path named in an old doc is still the one in active use | Conventions change; a symlink or a second directory can quietly become the real one | Verify which path actually holds the bulk of the content before trusting either |

## Quality Gates
- [ ] Verified the real archive root holds actual file content, not just a matching directory name, before calling anything "missing"
- [ ] Every pull logged in one place (repo, filter/revision, size, destination, success/failure)
- [ ] Any revision-pinned pull cross-checked against the serving node's actual deployed commit, not assumed
- [ ] Community stand-ins for missing official artifacts are explicitly labeled as such, with a re-check trigger noted
- [ ] "Current model list" carries a compilation date and was cross-checked against a primary source before driving a download decision

---

## Reference — commands

```bash
# Full repo
hf download <org>/<repo> --local-dir <mirror_root>/<org>__<repo>

# Specific quant only
hf download <org>/<repo>-GGUF --include '*Q4_K_M*' --local-dir <mirror_root>/<org>__<repo>-GGUF

# Pin an exact revision (e.g. matching a serving node's .env MODEL_REVISION)
hf download <org>/<repo> --revision <commit_sha> --local-dir <mirror_root>/<org>__<repo>

# Check real content vs. placeholder directories
find <mirror_root> -maxdepth 1 -type d
du -sh <mirror_root>/*/

# Find candidate repos by base model (e.g. a missing official drafter)
curl -s "https://huggingface.co/api/models?search=<query>" | jq '.[] | {id, downloads, likes}'
curl -s "https://huggingface.co/api/models?author=<org>" | jq '.[].id'

# Spot-check one file's hash against the Hub's recorded LFS sha256 (only if corruption suspected)
curl -s "https://huggingface.co/api/models/<org>/<repo>?blobs=true" | jq '.siblings[] | select(.lfs) | {rfilename, sha: .lfs.sha256}'
```

A minimal wrapper pattern worth building once per stack: a script that calls `hf download`, then appends `timestamp | repo | filter-or-revision | size | dest | status` to one log file on success *or* failure. That single line is what turns "we think we downloaded this" into a checkable fact.

## Model list snapshot — dated, not evergreen

Any concrete "what's newest / what should we have" table rots within weeks. Structure it like this, and re-date it every time it's touched:

```
<YYYY-MM-DD> snapshot, source: <audit/report/scan name>
Tier: <hardware/use-case tier>
  - <org>/<repo> — <size> — <mirrored | urgent | blocked:<reason> | skip:<reason>>
```

**Example — this stack's fleet, 2026-10-19** (multi-node GPU inference pool; kept here as a worked example of the shape above, not a template to copy verbatim into another stack):

```
2026-10-19 snapshot, source: fleet-model-audit-2026-10-17 + live archive check
Tier: single GPU node (~121GB unified)
  - nvidia/Qwen3.8-Flash-Next-NVFP4 — 124G — mirrored 2026-10-19
Tier: paired nodes, TP=2 (~240GB combined)
  - nvidia/GLM-5.3-Flash-NVFP4 @ pinned revision — 190.4G — mirrored 2026-10-19 (pulled at the exact revision a serving node already ran, per Decision Framework > Pulling)
  - XiaomiMiMo/MiMo-V2.6-Flash-RL — 166G — mirrored 2026-10-19
  - XiaomiMiMo/MiMo-V2.6-Flash-MOPD — 166G — mirrored 2026-10-19
  - XiaomiMiMo official V2.6 DFlash drafter — blocked: does not exist yet (org only ships V2.5-era drafters as of this date)
    - stand-in: vcruz305/MiMo-V2.6-Flash-RL-dflash-EXL3-4.0bpw (community, 366 downloads vs. 28 for the only other candidate) — mirrored 2026-10-19, re-check for official release
  - brandonmusic/GLM-5.3-Flash-tr3-4bpw — blocked: redistribution-license terms unverified; do not pull until resolved
Tier: edge/client nodes (8-16GB class)
  - several hardware-tier-specific GGUF quants planned in an earlier pull-list, not yet executed — full-precision duplicates on disk are not substitutes for the requested quant
```

For the living version of a list like this — one that gets re-verified on a cadence, flags staleness, and tracks a persistent mirrored/urgent/blocked/skip status across sessions instead of being re-derived from scratch — see the companion `ai-innovation-radar` skill's Survey and Horizon modes. This skill is the reusable *process*; a specific stack's current list belongs in that stack's own living tracker, not frozen into a shared skill file.
