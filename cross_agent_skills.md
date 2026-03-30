Cross-Agent Skills & Capabilities Audit Prompt

Use this prompt with any AI agent (Gemini, Copilot, ChatGPT, etc.) to generate a comparable capabilities catalog. Adapt the format section to match that agent's actual tooling.


Prompt
I need you to generate a comprehensive catalog of ALL your current capabilities, tools, functions, plugins, extensions, and integrations available in this session. Organize it as follows:

### 1. Built-in Core Tools
List every tool/function you can call natively (file I/O, web search, code execution, image generation, etc.). For each, include:
- Tool name
- What triggers it / when it's used
- What it does (one line)
- Any subscription tier restrictions (free vs paid vs enterprise)

### 2. Connected Integrations / Plugins / Extensions
List any external service integrations currently available (GitHub, Google Workspace, databases, APIs, etc.). For each:
- Integration name
- Available operations/tools
- Subscription tier required

### 3. Automation & Scheduling
List any capabilities for recurring tasks, scheduled execution, background agents, or persistent workflows.

### 4. Custom Skills / Custom Instructions / Memory
Describe any system for:
- User-defined reusable workflows (skills, custom GPTs, gems, etc.)
- Persistent memory across sessions
- Project-level context or instructions

### 5. Agent / Sub-agent Capabilities
Can you spawn sub-agents or parallel workers? Describe:
- How agents are created
- What tools they inherit
- Concurrency limits

### 6. File Format Support
List all file types you can:
- Read/parse (input)
- Create/generate (output)
- Edit in-place

### 7. Limitations & Gaps
Be honest about:
- What you CANNOT do that users often expect
- Features that exist but are unreliable
- Known restrictions by subscription tier

### 8. Comparison-Ready Summary
Create a table with these columns:
| Capability | Available? | How | Tier Required | Notes |

Categories to cover:
- File read/write (local filesystem)
- Code execution (sandboxed shell)
- Web search
- Web page fetching
- Image generation
- Image analysis/vision
- PDF creation/editing
- Office docs (docx, pptx, xlsx)
- GitHub/Git integration
- Database access
- Scheduled/recurring tasks
- Sub-agent spawning
- Custom reusable skills/workflows
- Persistent memory across sessions
- MCP / tool protocol support
- Plugin/extension marketplace
- Real-time collaboration

Format the output as clean markdown. Be thorough — I want to know EVERYTHING available to me right now, not just the highlights.

Usage Notes

Gemini: Run in Gemini Advanced with extensions enabled. Ask it to list all active extensions.
ChatGPT/Copilot: Run in a session with plugins enabled. Ask it to list all available tools via namespace introspection.
Claude Code (CLI): Run /tools to see available tools, then use this prompt to get the organized catalog.
Open source agents (AutoGPT, CrewAI, etc.): Adapt to list registered tools and available actions from the agent config.

After running against each agent, you can diff the outputs to see feature parity and gaps across providers.