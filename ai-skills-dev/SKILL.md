---
name: ai-skills-dev
description: "Use this skill whenever the user wants to understand, plan, or develop AI skills, prompts, agents, or workflows for Claude or other AI platforms. Triggers include: any mention of 'skill development', 'prompt engineering', 'agent design', 'build a skill', 'create a prompt', 'system prompt', 'SKILL.md', 'skill file', 'trigger description', 'MCP development', 'tool use', 'agent architecture', 'multi-agent', 'LLM training data', 'fine-tuning', 'RAG', 'retrieval augmented generation', 'embeddings', 'vector database', or requests to design AI workflows, optimize prompts, build custom tools, or understand how AI skills and agents work. Also use when the user asks about best practices for writing instructions that AI follows reliably, or wants to compare capabilities across different AI platforms."
---

# AI Skills Development Skill

## Overview

Guide users through designing, building, testing, and publishing AI skills — reusable instruction sets that teach AI assistants how to perform specific tasks. This covers Claude skills, prompt engineering principles, agent architecture, and cross-platform portability.

## Skill Architecture

### The Claude Skill Format

A skill is a directory with a required `SKILL.md` and optional resources:

```
skill-name/
├── SKILL.md              # Required: YAML frontmatter + markdown instructions
├── scripts/              # Optional: executable code for deterministic tasks
├── references/           # Optional: docs loaded into context as needed
└── assets/               # Optional: templates, fonts, icons
```

### SKILL.md Frontmatter

The frontmatter is the trigger mechanism — Claude reads it to decide whether to invoke the skill.

```yaml
---
name: skill-name              # kebab-case identifier
description: "Detailed trigger description. Include specific phrases,
  file types, keywords, and contexts that should activate this skill.
  Be 'pushy' — list many trigger conditions to avoid under-triggering."
---
```

The description is the single most important piece. It determines whether the skill gets used. Write it to capture every reasonable way a user might phrase a request that needs this skill.

### Description Writing Principles

1. **Start with the capability**: "Use this skill whenever the user wants to..."
2. **List explicit triggers**: Keywords, file extensions, domain terms
3. **Include implicit triggers**: Situations where the user needs the skill but doesn't name it
4. **Add negative boundaries**: "Do NOT use for..." to prevent false triggers
5. **Be specific over general**: "docker compose" beats "container orchestration"

**Example — good description**:
"Use this skill whenever the user wants to create, read, edit, or manipulate Word documents (.docx files). Triggers include: any mention of 'Word doc', 'word document', '.docx', or requests to produce professional documents with formatting like tables of contents, headings, page numbers, or letterheads."

**Example — bad description**:
"Helps with documents." (Too vague, will never trigger or will trigger for everything.)

### Body Writing Principles

The body teaches Claude HOW to do the task:

1. **Explain the why**: Tell the model why each instruction matters. "Always pin Docker image tags because :latest can silently break things when the image updates" beats "ALWAYS use specific tags."
2. **Use imperative form**: "Generate the compose file" not "You should generate"
3. **Include templates**: Show the exact output structure expected
4. **Provide examples**: Input/output pairs for common cases
5. **Progressive disclosure**: Keep SKILL.md under 500 lines. Put deep reference material in `references/` subdirectory with clear pointers about when to read each file.
6. **Avoid rigid MUST/NEVER**: Instead explain the reasoning so the model can generalize

## Prompt Engineering Fundamentals

These principles apply to skills, system prompts, and any AI instruction set:

### Structure
- **Role/context first**: Set the frame before giving instructions
- **Task description**: What to do, in what order
- **Output format**: Be explicit about structure, length, format
- **Examples**: Show 2-3 input/output pairs for ambiguous tasks
- **Constraints**: Boundaries and edge cases last

### Reliability Techniques
- **XML tags for structure**: Use `<context>`, `<instructions>`, `<output>` to section prompts
- **Chain of thought**: "Think step by step" or "Before answering, consider..."
- **Self-verification**: "After generating, verify that..."
- **Prefilled responses**: Start the assistant's response to constrain format

### Common Failure Modes
- **Instruction drift**: Long prompts cause early instructions to fade. Put critical rules at both the beginning and end.
- **Overfitting to examples**: If you give 3 examples that all share an incidental feature, the model may treat that feature as required. Vary your examples.
- **Conflicting instructions**: The model resolves conflicts unpredictably. Audit for contradictions.
- **Ambiguous scope**: "Be concise" means different things for different tasks. Specify word counts or structural limits.

## Agent Architecture Patterns

### Single Agent
One model with tools. Good for straightforward tasks. This is what most skills implement.

### Orchestrator + Workers
One agent plans and delegates to specialized sub-agents. Good for complex multi-step tasks. In Claude, use the Agent tool to spawn workers.

### Pipeline
Sequential agents, each transforming the output of the previous. Good for data processing workflows.

### Evaluator Loop
Agent generates → evaluator critiques → agent revises. Good for quality-sensitive outputs. The skill-creator skill uses this pattern.

## Cross-Platform Portability

When building skills meant to work across platforms:

### What's Portable
- Prompt text and instructions (the core logic)
- Output format specifications
- Domain knowledge and best practices
- Example input/output pairs

### What's Platform-Specific
- Tool calling syntax (Claude tools vs OpenAI functions vs Gemini function calling)
- File access mechanisms
- Memory/persistence systems
- Sub-agent spawning
- MCP integrations

### Portability Strategy
1. Write the core skill as pure markdown instructions (portable)
2. Wrap platform-specific tool calls in clearly marked sections
3. Document which tools are required vs optional
4. Provide fallback instructions for when tools aren't available

## Testing & Iteration

### Quick Testing (Vibe Check)
1. Write the skill
2. Think of 3 realistic user prompts
3. Run them manually
4. Adjust based on outputs

### Formal Testing (Evals)
For skills that need to be reliable at scale:
1. Create 10-20 test prompts covering normal cases, edge cases, and negative cases
2. Run with and without the skill (baseline comparison)
3. Grade outputs on specific criteria
4. Iterate until pass rate is acceptable

The built-in `skill-creator` skill has a full eval framework with blind comparison, automated grading, and benchmark visualization. Use it for production-quality skills.

### Description Optimization
After the skill works well, optimize the trigger description:
1. Generate 20 test queries (10 should-trigger, 10 should-not)
2. Test whether the skill activates correctly for each
3. Refine the description based on false positives and false negatives

## Publishing & Sharing

### As a .skill file
Package the skill directory as a `.skill` zip archive:
```bash
cd /path/to/skill-directory/..
zip -r skill-name.skill skill-name/
```
Users install by opening the `.skill` file in Claude Desktop.

### As a GitHub repo
Push the skill directory to a GitHub repo. Include:
- README.md explaining what the skill does and how to install it
- Example prompts showing it in action
- Screenshots of outputs if visual

### As a portable prompt
For cross-platform sharing, extract the core instructions as a standalone markdown file that can be pasted into any AI system prompt.

## Output Format

When building skills:
1. Always generate a complete, ready-to-use SKILL.md
2. Explain the design decisions made
3. Suggest 3 test prompts to validate it
4. Note any dependencies or required tools
5. Offer to run the skill-creator eval pipeline for formal testing
