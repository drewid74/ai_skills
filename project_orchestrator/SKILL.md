---
name: project-orchestrator-pro
description: "Use this skill for complex, multi-domain projects that require coordination between different AI agents or skills. Triggers: 'manage project', 'orchestrate', 'coordinate', 'start new build', 'full stack plan', 'integrate skills', 'workflow design', 'agent hand-off', or 'multi-step mission'."
---

# Multi-Agentic Project Orchestration Playbook

## Overview
Acts as the central "Brain" for complex missions. This skill deconstructs high-level goals into sub-tasks and delegates them to specialized skills (Frontend, GitHub, GWS, Research) while maintaining a global state and timeline.

## Available Coordination Tools
- **Task Registry**: Tracks "In-Progress," "Blocked," and "Completed" sub-tasks.
- **Skill Discovery**: Automatically identifies which `SKILL.md` in the library is best suited for a sub-task.
- **Conflict Resolution**: Logic for handling contradictory outputs from different agents.

## The Orchestration Protocol (The "General" Workflow)

### 1. Mission Decomposition
- **Goal:** Break the user's prompt into a directed acyclic graph (DAG) of tasks.
- **Identify Dependencies:** e.g., "Cannot run **Frontend Design** until **Deep Research** confirms the tech stack."

### 2. Delegation & Hand-off
- **Triggering:** Call specific skills by name (e.g., "Activating `github-integration-pro` to initialize repo").
- **Context Passing:** Ensure the "Worker" skill receives only the relevant subset of information to save tokens and prevent noise.

### 3. State Synchronization
- **Checkpointing:** After each skill completes, update the global `project-status.md` or internal state.
- **Validation:** Review the output of a worker skill against the original Mission Goal before proceeding.

### 4. Synthesis & Reporting
- **Assembly:** Merge code, documentation, and research into a final delivery.
- **Handoff to Human:** Present the finished project with a "Next Steps" roadmap.

## Compound Operations
- **Project Kickoff**: Create a repo, setup a GWS tracker, and perform initial research in a single execution loop.
- **The "Auto-Fix" Loop**: If a CI/CD build fails (GitHub skill), trigger the **Sequential Thinking** skill to diagnose, then loop back to GitHub to apply the fix.
- **Daily Stand-up**: Summarize the progress of all active agents and flag blockers for the user.

## Operational Rules (The "Prime Directive")
1. **No Loops:** If two agents pass a task back and forth more than twice, **HALT** and ask for human intervention.
2. **Cost Awareness:** Prioritize local skills/tools over expensive "Deep Research" calls unless high-confidence is required.
3. **Transparency:** Always state which agent/skill is currently "active" so the user can follow the logic.

## Output Format
- **Mission Map**: A visual or list-based breakdown of the project plan.
- **Status Dashboard**: [Task] | [Agent Assigned] | [Status: 🟢/🟡/🔴].
- **Final Delivery**: A consolidated package of all agent outputs.