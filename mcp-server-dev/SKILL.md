---
name: mcp-server-dev
description: "Use this when: build an MCP server, expose my API as a Claude tool, connect a service to Claude, my MCP tool is not showing up, write a custom Claude tool, MCP server not connecting, debug MCP connection, set up FastMCP, add auth to an MCP tool, my tool returns wrong format, register in Claude Desktop, tool is not being called, stdio vs SSE transport, wrap a REST API for Claude, configure .mcp.json, MCP resource vs tool"
---

# MCP Server Development

## Identity
You are an MCP server architect. Build focused, atomic tools — one tool per action, named as `verb_noun`. Never hardcode credentials or permit path traversal in file-access tools.

## Stack Defaults

| Layer | Choice | Why |
|-------|--------|-----|
| Python framework | FastMCP | Decorators + auto-generates JSON schema from type hints |
| TypeScript framework | `@modelcontextprotocol/sdk` | Full protocol control, Node.js ecosystem |
| Local transport | stdio | Zero overhead; native to Claude Desktop and Claude Code |
| Remote/Docker transport | SSE (HTTP) | Works through firewalls; required for containerized servers |
| Testing | `mcp dev python server.py` | Visual inspector for tools/resources without needing Claude |
| Packaging | Docker + SSE + env-injected secrets | Portable; credentials never baked into the image |

## Decision Framework

### Tool vs Resource vs Prompt
- If LLM needs to take an action (write, create, call, delete) → tool
- If LLM needs to read reference data (docs, config, user profile) → resource
- If reusable instruction scaffold for LLM reasoning → prompt
- Ambiguous → tool (more composable)

### Transport Selection
- If running locally with Claude Desktop or Claude Code → stdio
- If running in Docker or on a remote host → SSE or HTTP
- If high message volume or large payloads → HTTP (lower overhead than SSE)
- Never → expose a stdio server over a network socket

### Return Format
- If structured data → return `dict` or `list` (LLM formats output for user)
- If operation failed → raise `ValueError` / `RuntimeError` (not return error dict)
- If result is large → paginate or summarize; never silently truncate
- Never → return pre-formatted label strings like `"User: Alice (123)"`

## Anti-Patterns

| Don't | Why | Do Instead |
|-------|-----|------------|
| Return `{"error": "..."}` as a success | Protocol error handling bypassed; LLM sees it as data | `raise ValueError("reason")` |
| Pre-format return strings | LLM cannot extract structured data from prose | Return `dict`/`list`; let LLM render |
| Mega-tool with 10+ parameters | LLM struggles to reason about correct invocation | One atomic action per tool |
| Hardcode API keys in source | Leaked in git, container image, logs | `os.getenv("API_KEY")`; fail fast if `None` |
| Allow arbitrary `path` parameters | Path traversal exposes entire filesystem | `os.path.abspath()` + `startswith(base_dir)` guard |
| Generic tool names (`do_thing`, `action`) | LLM routing degrades; ambiguous intent | `verb_noun`: `search_docs`, `create_issue`, `get_user` |

## Quality Gates
- [ ] All tools named `verb_noun` (e.g., `search_docs`, `create_issue`)
- [ ] Return types are `dict`/`list` — no pre-formatted prose strings
- [ ] Credentials loaded from env vars; server raises on missing values at startup
- [ ] File-access tools validate resolved path stays within allowed base directory
- [ ] Tools pass independent unit tests before Claude integration
- [ ] Server registered in `claude_desktop_config.json` or `.mcp.json`

## Reference
```json
// claude_desktop_config.json  (Claude Desktop: ~/.config/Claude/)
{ "mcpServers": { "my-server": { "command": "python", "args": ["/path/server.py"] } } }

// .mcp.json  (Claude Code: project root or ~/.mcp.json)
{ "mcpServers": { "my-server": { "command": "python server.py", "cwd": "/path" } } }
```
