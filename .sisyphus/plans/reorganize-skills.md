# Reorganize Loose MD Files into Standalone Skill Directories

## TL;DR

> **Quick Summary**: Move 6 loose `.md` files into their own named directories as `SKILL.md`, matching the existing `token-burn-all-sources/` pattern.
> 
> **Deliverables**: 6 new directories each containing `SKILL.md`
> **Estimated Effort**: Quick
> **Parallel Execution**: YES - 1 wave (all independent)
> **Critical Path**: None - all operations independent

---

## Context

### Original Request
Turn all md files in `C:\Users\afair\dev\ai_skills_paid` into standalone skills with their own directories.

### Current State
- 6 loose `.md` files with cryptic timestamp-based names
- 1 existing directory (`token-burn-all-sources/`) already follows the target pattern: `dirname/SKILL.md`

---

## Work Objectives

### Core Objective
Reorganize 6 markdown files into standalone skill directories matching the existing convention.

### Concrete Deliverables
```
C:\Users\afair\dev\ai_skills_paid\
├── agent-product-analytics/SKILL.md        (was 20260512-161-promptkit-1.md)
├── ai-office-files-guide/SKILL.md          (was 20260512-430-guide-substack-companion-guide.md)
├── ai-office-files-promptkit/SKILL.md      (was 20260512-430-promptkit-substack-companion-prompt-kit.md)
├── organize-project-files/SKILL.md         (was 20260512-721-promptkit-1.md)
├── public-ai-work-apprenticeship/SKILL.md  (was 20260512-837-promptkit-1.md)
├── opus-benchmark-routing/SKILL.md         (was 20260531-43a-promptkit-1.md)
└── token-burn-all-sources/SKILL.md         (already exists, unchanged)
```

### Definition of Done
- [ ] All 6 original `.md` files no longer exist at root level
- [ ] All 6 new directories exist with `SKILL.md` inside
- [ ] Content is identical (no modifications to file content)

### Must NOT Have
- Do NOT modify file content
- Do NOT touch `token-burn-all-sources/`
- Do NOT create empty subdirs (agents/, assets/, references/)

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** - ALL verification is agent-executed.

### Test Decision
- **Automated tests**: None (file operations)
- **QA**: Directory listing comparison

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (All parallel - completely independent):
├── Task 1: Create directories and move files [quick]
```

Single task — all 6 moves are independent and can be done in one script.

---

## TODOs

- [x] 1. Create skill directories and move files

  **What to do**:
  - Create 6 directories under `C:\Users\afair\dev\ai_skills_paid\`:
    - `agent-product-analytics/`
    - `ai-office-files-guide/`
    - `ai-office-files-promptkit/`
    - `organize-project-files/`
    - `public-ai-work-apprenticeship/`
    - `opus-benchmark-routing/`
  - Move each source file into its directory as `SKILL.md`:
    - `20260512-161-promptkit-1.md` → `agent-product-analytics/SKILL.md`
    - `20260512-430-guide-substack-companion-guide.md` → `ai-office-files-guide/SKILL.md`
    - `20260512-430-promptkit-substack-companion-prompt-kit.md` → `ai-office-files-promptkit/SKILL.md`
    - `20260512-721-promptkit-1.md` → `organize-project-files/SKILL.md`
    - `20260512-837-promptkit-1.md` → `public-ai-work-apprenticeship/SKILL.md`
    - `20260531-43a-promptkit-1.md` → `opus-benchmark-routing/SKILL.md`

  **Must NOT do**:
  - Do not modify file content
  - Do not create extra subdirs

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: N/A (single task)
  - **Blocks**: Nothing
  - **Blocked By**: Nothing

  **References**:
  - `C:\Users\afair\dev\ai_skills_paid\token-burn-all-sources\` — existing pattern to match

  **Acceptance Criteria**:
  - [ ] 6 new directories exist
  - [ ] Each contains `SKILL.md` with original content
  - [ ] No `.md` files remain at root level (except inside directories)

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: All directories created with SKILL.md
    Tool: Bash (PowerShell)
    Steps:
      1. Run: Get-ChildItem -LiteralPath "C:\Users\afair\dev\ai_skills_paid" -Directory | Select Name
      2. Assert: 7 directories listed (6 new + token-burn-all-sources)
      3. Run: Get-ChildItem -LiteralPath "C:\Users\afair\dev\ai_skills_paid" -Filter "*.md" -File | Measure
      4. Assert: Count = 0 (no loose .md files at root)
      5. Run: Get-ChildItem -LiteralPath "C:\Users\afair\dev\ai_skills_paid" -Recurse -Filter "SKILL.md" | Measure
      6. Assert: Count = 7 (one per directory)
    Expected Result: 7 dirs, 0 root .md files, 7 SKILL.md files
    Evidence: .sisyphus/evidence/task-1-directories-verified.txt
  ```

  **Commit**: YES
  - Message: `chore: reorganize loose md files into standalone skill directories`
  - Files: all moved files
  - Pre-commit: directory listing verification

---

## Success Criteria

### Verification Commands
```powershell
(Get-ChildItem "C:\Users\afair\dev\ai_skills_paid" -Directory).Count  # Expected: 7
(Get-ChildItem "C:\Users\afair\dev\ai_skills_paid" -Filter "*.md" -File).Count  # Expected: 0
(Get-ChildItem "C:\Users\afair\dev\ai_skills_paid" -Recurse -Filter "SKILL.md").Count  # Expected: 7
```
