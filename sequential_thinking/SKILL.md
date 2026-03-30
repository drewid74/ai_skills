---
name: sequential-thinking-pro
description: "Use this skill for complex architecture, deep debugging, logic puzzles, or high-stakes decision making. Triggers: 'why', 'how should I approach', 'debug', 'architecture', 'logic', 'plan', 'strategy', 'complex', 'broken', 'root cause', 'analyze', or when a task has more than 5 dependencies."
---

# Sequential Thinking & Logic Playbook

## Overview
A structured framework for avoiding "hallucinated shortcuts." This skill forces the agent to explore the "Reasoning Tree" before providing a final answer, ensuring technical accuracy for home lab and UAS projects.

## The Thought Protocol (Sequential Steps)
1. **Deconstruction**: Break the user's prompt into atomic requirements and constraints.
2. **Branching**: Explore Path A (Optimal/Complex) and Path B (Fast/Simple). 
3. **Validation**: Test the logic of each path against known edge cases (e.g., TrueNAS permission conflicts).
4. **Synthesis**: Provide the final recommendation with a "Why this works" justification.

## Available Logic Tools
- `mcp__sequential_thinking__thought`: Logs internal logic steps without cluttering the main conversation UI.

## Root Cause Analysis (RCA) Workflow
When debugging (e.g., Docker Compose failures):
- **Observation**: What is the specific error code? (Copy-paste logs).
- **History**: What changed recently in the config or environment?
- **Hypothesis**: Formulate 3 potential causes (Network, Permissions, Resource Exhaustion).
- **Isolation**: Propose a specific test to prove/disprove the primary hypothesis.

## Compound Operations
- **Architectural Review**: Analyze a `docker-compose.yml` or UAS hardware schematic for potential failure points.
- **Decision Matrix**: Compare two technologies (e.g., TrueNAS vs. Unraid) across 5 weighted criteria.
- **Dependency Mapping**: Visualize how a change in one service (e.g., Traefik) affects the rest of the stack.

## Output Format
- Provide a "Thinking Path" summary before the final answer.
- Explicitly highlight any "Uncertainties" or "Assumptions" made during the process.