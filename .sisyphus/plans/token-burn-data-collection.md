# Token Burn Dashboard — Collect Actual Data

## TL;DR

> **Quick Summary**: Collect real token usage data from 3 AI tools (Claude Code derived from sessions, Anthropic estimated, Copilot completions estimated), normalize to daily rows, update dashboard schema, and deploy with real data.
>
> **Deliverables**:
> - Updated source column schema (3 tool-based sources replacing 4 sample ones)
> - Real `daily-burn.json` with data from May 17 – Jun 6+
> - Rebuilt + redeployed dashboard at 192.168.7.205:29243
>
> **Source Column Schema**:
> ```
> claude_code_tokens    — derived from opencode session metadata (msg count × ~800 tok/msg)
> copilot_completions_est — estimated from active coding hours
> anthropic_est         — estimated from Desktop (cowork) + claude.ai usage patterns
> ```
>
> **Key Constraints**:
> - opencode routes through GitHub Copilot credits (no billing visibility)
> - No Anthropic API subscription — Desktop + chat are Pro/free tier
> - All token numbers are estimates except relative session volumes from opencode
>
> **Estimated Effort**: Medium
> **Parallel Execution**: YES - 3 waves
> **Critical Path**: Task 1 → Task 2 → Task 5 → Task 6 → Task 7

---

## Context

### Original Request
"collect actual data" — populate the token-burn dashboard with real usage numbers.

### Interview Summary
**Key Discussions**:
- Sources tracked BY TOOL: Claude Code (opencode), Anthropic (Desktop + claude.ai), Copilot completions
- Claude Desktop usage = "cowork" driver category
- No Anthropic API subscription — estimation only
- opencode routes through GitHub Copilot enterprise credits — no per-user token visibility
- GitHub Copilot moved to credits model — can't see exact amounts
- Time range: as much as possible (opencode has May 17 – Jun 6)

**Research Findings**:
- 7 opencode sessions available via session_list (88–2523 messages each)
- session_info provides: message count, date range, duration, agents, todos, transcript entries
- No direct token count in session metadata — derive from message volume
- Claude Desktop stores only config locally (no conversation logs)
- Dashboard currently has wrong source columns (codex, chatgpt) — needs schema update
- Dashboard is static Next.js build — data changes need rebuild

**Estimation Methodology**:
- Claude Code: message_count × ~800 tokens/message (covers input+output avg for coding tasks)
- Copilot completions: ~2000 tokens/active coding hour (inline suggestions)
- Anthropic (Desktop cowork): ~15,000 tokens/session (longer collaborative conversations)
- Anthropic (claude.ai chat): ~3,000 tokens/session (shorter queries)

### Metis Review
**Identified Gaps (addressed)**:
- Token estimation formula needed → defined below (avg tokens/message heuristic)
- Multi-session days → aggregate by date
- Sessions spanning midnight → attribute to start date
- Zero-usage days → include as zero rows for continuity
- Existing sample data → delete entirely, replace with real data
- No automated pipeline → manual backfill only, out of scope

---

## Work Objectives

### Core Objective
Replace sample data with real token usage data and fix source columns to match actual AI tools used.

### Concrete Deliverables
- `daily-burn.json` with real daily rows (May 17 – Jun 6+)
- Updated `sourceColumns` config (3 sources: Claude Code, Anthropic, Copilot)
- Rebuilt dashboard image deployed to dev-island

### Definition of Done
- [ ] Dashboard at 192.168.7.205:29243 shows real data with correct source labels
- [ ] All 5 views render without error (heatmap, trend, source split, drivers, table)
- [ ] No sample/fake data remains in the deployed app
- [ ] Exact vs estimated fidelity is visually distinguishable

### Must Have
- Real Claude Code data from opencode sessions
- Clear exact vs estimated labeling
- Driver field populated (at minimum: cowork, shipping, research, planning)
- Privacy-safe evidence notes (no file paths, client names, repo names)

### Must NOT Have (Guardrails)
- No automated collection pipeline — manual backfill only
- No new sources beyond the 3 defined
- No UI changes beyond source column relabeling
- No raw logs, chat exports, private project IDs in evidence
- No invented "exact" numbers — if estimated, label it estimated

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed.

### Test Decision
- **Infrastructure exists**: NO (this is data + config work, not code)
- **Automated tests**: None
- **Framework**: N/A

### QA Policy
Every task includes agent-executed QA. Evidence saved to `.sisyphus/evidence/`.

- **Data validation**: Run JSON schema checks on output
- **Dashboard**: curl the deployed app, verify 200 + correct source labels
- **Privacy**: grep output data for forbidden patterns

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — data extraction + schema):
├── Task 1: Extract Claude Code session data from opencode [quick]
├── Task 2: Update dashboard source column schema [quick]
└── Task 3: Interview user for Anthropic + Copilot estimates [blocked: user input]

Wave 2 (After Wave 1 — normalization):
├── Task 4: Normalize all sources into daily-burn.json [unspecified-high]
└── Task 5: Privacy scrub + validate JSON schema [quick]

Wave 3 (After Wave 2 — deploy):
├── Task 6: Rebuild dashboard with real data [quick]
└── Task 7: Verify deployed dashboard [quick]

Final Verification:
└── Task F1: End-to-end dashboard check [oracle]
```

### Dependency Matrix
| Task | Depends On | Blocks |
|------|-----------|--------|
| 1 | — | 4 |
| 2 | — | 6 |
| 3 | — (user input) | 4 |
| 4 | 1, 3 | 5 |
| 5 | 4 | 6 |
| 6 | 2, 5 | 7 |
| 7 | 6 | F1 |

### Agent Dispatch Summary
- **Wave 1**: 3 tasks — T1 `quick`, T2 `quick`, T3 `blocked`
- **Wave 2**: 2 tasks — T4 `unspecified-high`, T5 `quick`
- **Wave 3**: 2 tasks — T6 `quick`, T7 `quick`
- **Final**: 1 task — F1 `oracle`

---

## TODOs

- [ ] 1. Extract Claude Code session data from opencode

  **What to do**:
  - Call `session_list` with high limit to get ALL available sessions
  - For each session, call `session_info` to get: message count, date range, duration, agents
  - Record per-session: session_id, start_date, end_date, message_count, duration_hours
  - For sessions spanning multiple days, split proportionally by duration
  - Calculate token estimate: message_count × 800 (avg tokens/message for coding work)
  - Aggregate by date to produce daily totals
  - Output: intermediate JSON with per-day claude_code_tokens values

  **Must NOT do**:
  - Do NOT read full session content (privacy, performance)
  - Do NOT use session_read — only session_list and session_info
  - Do NOT fabricate sessions that don't exist

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3)
  - **Blocks**: Task 4
  - **Blocked By**: None

  **References**:
  - `session_list` tool: returns session IDs, message counts, date ranges, agents
  - `session_info` tool: returns detailed session metadata
  - Data contract: `C:\Users\afair\.claude\skills\token-burn-all-sources\references\data-contract.md`

  **QA Scenarios**:

  ```
  Scenario: All opencode sessions captured
    Tool: Bash (comparison)
    Steps:
      1. Run session_list with limit=100
      2. Compare count of sessions returned vs count in extraction output
      3. Verify every session_id from session_list appears in output
    Expected Result: 100% session coverage, zero missed sessions
    Evidence: .sisyphus/evidence/task-1-session-coverage.json

  Scenario: Token estimation sanity check
    Tool: Bash (arithmetic)
    Steps:
      1. For the 2523-message session, verify token estimate = 2523 × 800 = ~2,018,400
      2. For the 88-message session, verify token estimate = 88 × 800 = ~70,400
      3. Verify no daily total exceeds 5,000,000 (sanity bound)
    Expected Result: All estimates within expected ranges
    Evidence: .sisyphus/evidence/task-1-token-sanity.txt
  ```

  **Commit**: NO (intermediate data, not deployed)

- [ ] 2. Update dashboard source column schema

  **What to do**:
  - SSH to TrueNAS, locate dashboard source at `/mnt/NAS1Pool/stacks/dev_island/images/token-burn/`
  - Find the sourceColumns definition (likely in a config or component file)
  - Replace current 4-column schema with:
    ```typescript
    export const sourceColumns = [
      { key: "claude_code_tokens", label: "Claude Code", fidelity: "derived" },
      { key: "copilot_completions_est", label: "Copilot", fidelity: "estimated" },
      { key: "anthropic_est", label: "Anthropic", fidelity: "estimated" },
    ];
    ```
  - Update any chart/view components that reference old column keys (codex_tokens, chatgpt_est)
  - Verify TypeScript/build doesn't break with new keys

  **Must NOT do**:
  - Do NOT change UI layout, styles, or chart types
  - Do NOT add new views or features
  - Do NOT touch the deployment config

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3)
  - **Blocks**: Task 6
  - **Blocked By**: None

  **References**:
  - Dashboard source: `/mnt/NAS1Pool/stacks/dev_island/images/token-burn/` on TrueNAS (192.168.7.205)
  - Current sourceColumns (from compressed context): codex_tokens, claude_code_tokens, claude_chat_est, chatgpt_est
  - Skill starter app: `C:\Users\afair\.claude\skills\token-burn-all-sources\assets\dashboard-starter\`

  **QA Scenarios**:

  ```
  Scenario: Schema updated correctly
    Tool: Bash (ssh + grep)
    Steps:
      1. ssh truenas "grep -r 'sourceColumns' /mnt/NAS1Pool/stacks/dev_island/images/token-burn/"
      2. Verify output contains claude_code_tokens, copilot_completions_est, anthropic_est
      3. Verify output does NOT contain codex_tokens or chatgpt_est
    Expected Result: Only new 3-column schema present
    Evidence: .sisyphus/evidence/task-2-schema-grep.txt

  Scenario: No build errors after schema change
    Tool: Bash (ssh + npm)
    Steps:
      1. ssh truenas "cd /mnt/NAS1Pool/stacks/dev_island/images/token-burn && npm run build"
      2. Verify exit code 0
    Expected Result: Clean build with new schema
    Evidence: .sisyphus/evidence/task-2-build-output.txt
  ```

  **Commit**: YES
  - Message: `fix(token-burn): update source columns to match actual tools`
  - Files: source column config + any referencing components
  - Pre-commit: `npm run build` passes

- [ ] 3. Collect Anthropic + Copilot usage estimates from user

  **What to do**:
  - Interview user about their usage patterns for the date range (May 17 – Jun 6):
    - How many Claude Desktop "cowork" sessions per day/week?
    - Typical session length for Desktop cowork?
    - How often do you use claude.ai chat? How many queries/day?
    - How many hours of active coding per day with Copilot inline suggestions?
  - Apply estimation formulas:
    - Desktop cowork: sessions × 15,000 tokens/session
    - claude.ai chat: queries × 3,000 tokens/query
    - Copilot completions: active_hours × 2,000 tokens/hour
  - Produce per-day estimates for `anthropic_est` and `copilot_completions_est`
  - Document all assumptions in evidence file

  **Must NOT do**:
  - Do NOT invent usage patterns — get from user
  - Do NOT label estimates as "exact"
  - Do NOT access any external APIs or billing systems

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - **Note**: This task requires user interaction — may block until user responds

  **Parallelization**:
  - **Can Run In Parallel**: YES (but blocked on user input)
  - **Parallel Group**: Wave 1 (with Tasks 1, 2)
  - **Blocks**: Task 4
  - **Blocked By**: User providing usage estimates

  **QA Scenarios**:

  ```
  Scenario: Estimates documented with methodology
    Tool: Bash (file check)
    Steps:
      1. Verify estimation methodology file exists with assumptions
      2. Verify every day in range has a value (even if 0)
      3. Verify no day exceeds 500,000 anthropic_est (sanity)
    Expected Result: Complete per-day estimates with documented methodology
    Evidence: .sisyphus/evidence/task-3-estimation-methodology.md
  ```

  **Commit**: NO (intermediate data)

- [ ] 4. Normalize all sources into daily-burn.json

  **What to do**:
  - Combine outputs from Tasks 1 and 3 into unified daily rows
  - For each date in range:
    - `claude_code_tokens`: from Task 1 output
    - `copilot_completions_est`: from Task 3 output
    - `anthropic_est`: from Task 3 output
    - `total`: sum of all three
    - `driver`: classify based on highest-burn source that day (cowork if anthropic dominates, shipping if claude_code dominates, etc.)
    - `evidence`: brief sanitized note about what work happened
  - Fill zero-usage days with zero rows (maintain date continuity)
  - All dates in user's local timezone (America/Chicago or America/New_York — confirm)
  - Write to data format matching data-contract.md

  **Must NOT do**:
  - Do NOT include private details in evidence field
  - Do NOT merge estimated into exact columns
  - Do NOT skip days (include zero rows)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 5
  - **Blocked By**: Tasks 1, 3

  **References**:
  - Data contract: `C:\Users\afair\.claude\skills\token-burn-all-sources\references\data-contract.md`
  - Driver labels: shipping, research, review, video, planning, admin, support, writing, cowork

  **QA Scenarios**:

  ```
  Scenario: Complete date coverage
    Tool: Bash (jq)
    Steps:
      1. Parse daily-burn.json
      2. Extract min and max dates
      3. Verify every calendar day between min and max has a row
      4. Verify no duplicate dates
    Expected Result: Continuous date range with one row per day
    Evidence: .sisyphus/evidence/task-4-date-coverage.txt

  Scenario: Totals sum correctly
    Tool: Bash (jq arithmetic)
    Steps:
      1. For each row, verify total = claude_code_tokens + copilot_completions_est + anthropic_est
      2. Verify no negative values
    Expected Result: All totals are correct sums
    Evidence: .sisyphus/evidence/task-4-totals-check.txt
  ```

  **Commit**: NO (intermediate data)

- [ ] 5. Privacy scrub + validate JSON schema

  **What to do**:
  - Grep daily-burn.json for forbidden patterns: file paths, email addresses, client names, repo names, API keys
  - Validate JSON structure matches data-contract.md row shape exactly
  - Verify all required fields present in every row
  - Verify fidelity labels in sourceColumns match actual data derivation
  - Write validated file to deployment location

  **Must NOT do**:
  - Do NOT modify actual data values during scrubbing
  - Do NOT remove rows (only scrub evidence text if needed)

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 6
  - **Blocked By**: Task 4

  **QA Scenarios**:

  ```
  Scenario: No private data in output
    Tool: Bash (grep)
    Steps:
      1. grep -iE "(C:\\\\|/Users/|@.*\\.com|api[_-]?key)" daily-burn.json
      2. Verify zero matches
    Expected Result: No private data patterns found
    Evidence: .sisyphus/evidence/task-5-privacy-scan.txt
  ```

  **Commit**: YES
  - Message: `feat(token-burn): add real usage data May 17 – Jun 6`
  - Files: daily-burn.json
  - Pre-commit: JSON is valid

- [ ] 6. Rebuild dashboard with real data

  **What to do**:
  - Copy validated daily-burn.json to the dashboard data directory on TrueNAS
  - Rebuild the Next.js app (npm run build)
  - Rebuild Docker image: `docker build -t dev-island-token-burn:latest .`
  - Restart the container: `docker compose up -d dev_island_token_burn`
  - Verify the service comes up on port 29243

  **Must NOT do**:
  - Do NOT modify other docker-compose services
  - Do NOT change the port or resource limits
  - Do NOT use broad sed commands on docker-compose.yaml

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`docker-selfhost`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 7
  - **Blocked By**: Tasks 2, 5

  **QA Scenarios**:

  ```
  Scenario: Dashboard serves on correct port
    Tool: Bash (curl)
    Steps:
      1. curl -s -o /dev/null -w "%{http_code}" http://192.168.7.205:29243/
      2. Verify response is 200
    Expected Result: HTTP 200
    Evidence: .sisyphus/evidence/task-6-health-check.txt

  Scenario: New source labels visible
    Tool: Bash (curl + grep)
    Steps:
      1. curl -s http://192.168.7.205:29243/ | grep -o "Claude Code"
      2. curl -s http://192.168.7.205:29243/ | grep -o "Copilot"
      3. curl -s http://192.168.7.205:29243/ | grep -o "Anthropic"
      4. Verify NO matches for "Codex" or "ChatGPT"
    Expected Result: All 3 new labels present, zero old labels
    Evidence: .sisyphus/evidence/task-6-labels-check.txt
  ```

  **Commit**: YES
  - Message: `chore(token-burn): rebuild and deploy with real data`
  - Files: Dockerfile or build artifacts on TrueNAS

- [ ] 7. Verify deployed dashboard end-to-end

  **What to do**:
  - Load http://192.168.7.205:29243/ and verify all 5 views render:
    1. Daily heatmap
    2. Weekly trend
    3. Burn drivers (source split)
    4. Scale equivalents
    5. Moving-average table
  - Verify data is real (check a known date matches expected values)
  - Verify estimated vs derived labels are visually distinguishable
  - Verify no sample data remnants

  **Must NOT do**:
  - Do NOT make UI changes
  - Do NOT modify data

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: [`playwright`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3
  - **Blocks**: F1
  - **Blocked By**: Task 6

  **QA Scenarios**:

  ```
  Scenario: All 5 dashboard views render
    Tool: Playwright
    Steps:
      1. Navigate to http://192.168.7.205:29243/
      2. Verify page loads without console errors
      3. Check for presence of heatmap, trend chart, source split, drivers, table elements
      4. Screenshot each view
    Expected Result: All 5 views visible and populated with data
    Evidence: .sisyphus/evidence/task-7-dashboard-views.png
  ```

  **Commit**: NO (verification only)

---

## Final Verification Wave

- [ ] F1. **End-to-end dashboard verification** — `oracle`

  Read daily-burn.json. Verify: all dates present (no gaps in range), totals sum correctly, fidelity labels match sourceColumns, driver field non-empty for high-burn days. Then curl http://192.168.7.205:29243/ and verify all 5 views render. Check no sample data remnants (no "codex_tokens", no "chatgpt_est" keys).

  Output: `Data [N rows, date range] | Schema [3 sources correct] | Views [5/5 render] | Privacy [CLEAN] | VERDICT`

---

## Commit Strategy

- After Task 2: `fix(token-burn): update source columns to match actual tools`
- After Task 5: `feat(token-burn): add real usage data May 17 – Jun 6`
- After Task 6: `chore(token-burn): rebuild and deploy with real data`

---

## Success Criteria

### Verification Commands
```bash
curl -s http://192.168.7.205:29243/ | grep -c "Claude Code"  # Expected: ≥1
curl -s http://192.168.7.205:29243/ | grep -c "Codex"        # Expected: 0
```

### Final Checklist
- [ ] Dashboard shows 3 real sources (Claude Code, Anthropic, Copilot)
- [ ] All rows use real dates from actual usage
- [ ] Estimated sources clearly labeled
- [ ] No sample/fake data present
- [ ] All 5 dashboard views render correctly
