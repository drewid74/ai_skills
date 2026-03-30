---
name: repo-auditor-pro
description: "Use this skill to audit a repository's structure, documentation, link integrity, and standards compliance. Triggers: 'audit repo', 'check repository', 'is this repo clean', 'review structure', 'missing files', 'broken links', 'repo best practices', 'check README', or 'prepare for release'."
---

# Repository Health & Best Practices Playbook

## Overview
Evaluates a local or remote repository against 2026 industry standards for maintainability, AI-readiness, and structural integrity. This skill identifies "technical debt" in documentation and organization.

## Available Audit Tools
- **Filesystem**: `ls -R` (recursive map), `cat` (content review)
- **Link Checking**: `grep` for URLs + `curl --head` (to verify status codes)
- **Search**: `search_code` (to find "TODO" or "FIXME" markers)

## The Audit Protocol (4-Layer Check)

### 1. Structural Integrity (The "Skeleton" Check)
Verify the presence of mandatory 2026 baseline files:
- **README.md**: Must have Setup, Usage, and Architecture sections.
- **LICENSE**: Must be present and valid.
- **.gitignore**: Must be tailored to the project language (no OS junk).
- **llms.txt / AGENTS.md**: (2026 Standard) High-level context for AI tools.
- **.github/workflows/**: Essential CI/CD scaffolding.

### 2. Content Quality (The "Context" Check)
- **Stale Content**: Identify documentation that references deleted files or old versions.
- **Clarity**: Flag sections with "vague" instructions (e.g., "Install the stuff").
- **Consistency**: Ensure naming conventions (kebab-case vs camelCase) are uniform across the directory.

### 3. Link & Dependency Integrity
- **External Links**: Scan all `.md` files for URLs; flag any 404s or 500s.
- **Internal Paths**: Verify that relative links (e.g., `[Docs](docs/setup.md)`) actually point to existing files.
- **Dependency Health**: Check `package.json` or `requirements.txt` for version pinning vs. "latest" (risky).

### 4. AI-Readiness (Agentic Standards)
- **SKILL.md Audit**: If this is an agent repo, verify each skill has correct YAML frontmatter.
- **Entrypoints**: Ensure the main entry point (e.g., `index.ts`, `main.py`) is clearly documented in the README.

## Compound Operations
- **Full Repo Triage**: Run all 4 layers and produce a "Health Report" with a 1-100 score.
- **Broken Link Sweep**: A deep-dive focused specifically on URL and file-path validation.
- **Onboarding Review**: Audit the repo specifically from the perspective of a "New Developer" to find friction points.

## Output Format
- **Executive Summary**: 3-5 bullet points of the most critical issues.
- **Detailed Findings**: Categorized by "Structural," "Content," and "Links."
- **Action Plan**: A prioritized list of "Quick Fixes" ( < 5 mins) vs "Strategic Fixes."