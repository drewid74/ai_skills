---
name: continue-from-accepted
description: Continue iterative work from the last ACCEPTED result plus only the new requested change, instead of replaying the conversation. Use during long multi-turn editing of a document, config, or code file; when the user says "keep going from what we had", asks for a follow-up change to something already approved, or is near plan/token limits in an iterative session. Saves one integrity-checked accepted result, builds a minimal continuation prompt, and never carries rejected drafts or transcript history forward.
---

# Continue from accepted

Carry forward the *result*, not the history that produced it. After a user
accepts a version, later changes need only (accepted result + new change) —
not the transcript, not rejected drafts, not the reasoning that got there.

## State rules (read first)

- **The state file is EPHEMERAL working state, not a durable store.** Keep it
  under the OS temp directory: `<tmp>/continue-from-accepted/<task-slug>.json`
  (resolve `<tmp>` via `python3 -c "import tempfile;print(tempfile.gettempdir())"`).
  Do NOT create per-repo state directories. Durable facts belong in the
  memory system; the deliverable itself belongs in the repo. This skill's
  state is a session-scoped snapshot, nothing more.
- **Only acceptance promotes.** Save when the user accepts a version
  (explicitly, or by asking for a further change that keeps the rest).
  A rejected result is never saved. No accepted result yet → work normally.
- **One current result.** Each new acceptance replaces the previous state.
  No history accumulates.
- **No secrets in state.** If the accepted result contains credentials,
  do not save it; continue without this skill.

## Workflow

Resolve `<skill-dir>` from where this skill is installed. Do this yourself —
never ask the human to run these commands, restate prior work, or manage the
state file.

**1. On acceptance — save:**

```bash
python3 <skill-dir>/scripts/state_delta.py save \
  --state <tmp>/continue-from-accepted/<task-slug>.json \
  --accepted-file <path-to-accepted-result>
```

**2. On the next change — build the continuation prompt:**

```bash
python3 <skill-dir>/scripts/state_delta.py packet \
  --state <tmp>/continue-from-accepted/<task-slug>.json \
  --change "<the user's new requested change>" \
  --max-packet-bytes 16000 \
  --output <tmp>/continue-from-accepted/<task-slug>-packet.txt
```

Use the packet as the working input (e.g. as a fresh subagent's prompt)
instead of re-sending conversation history. The packet instructs the worker:
continue from the accepted result, apply only the new change, return the
updated result only.

**3. Check without exposing content:** `state_delta.py inspect --state <file>`
prints byte count + sha256 only.

## Failure handling

- The state file is sha256-integrity-checked on load; a hash mismatch means
  the file was modified outside `save` — discard it and re-save from the
  actual accepted artifact. Do not hand-edit state files.
- If `packet` refuses because the result exceeds the byte cap: select only
  the relevant passages of the accepted result for this change (search
  tooling), don't raise the cap reflexively.
- **Never retry a token-limit or usage-limit failure unchanged.** Reduce the
  input, pick a cheaper path, or stop and say so.

## Provenance

`scripts/state_delta.py` extracted UNCHANGED from the token-saver skill
(Unlock AI / Ringer, 2026) — reviewed: pure stdlib, no network, no telemetry.
sha256: 0c2d953c5712cbf5d125cbb1dbdbf29eb851f067b783fc9f8b897729858b0c7b
The original's per-repo `.token-saver/` state convention was dropped
deliberately: it conflicts with the fleet rule against inventing new state
stores. Temp-dir state is this skill's policy, set here, not in the script.
