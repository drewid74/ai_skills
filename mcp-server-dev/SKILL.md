---
name: mcp-server-dev
description: "Use this when: build an MCP server, expose my API as a Claude tool, connect a service to Claude, my MCP tool is not showing up, write a custom Claude tool, MCP server not connecting, debug MCP connection, set up FastMCP, add auth to an MCP tool, my tool returns wrong format, register in Claude Desktop, tool is not being called, stdio vs SSE transport, wrap a REST API for Claude, configure .mcp.json, MCP resource vs tool, MCP prompt vs tool, Docker MCP container, multi-server setup, path traversal in file tool"
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

---

## FastMCP Quick Start (Python)

```python
from fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def search_docs(query: str) -> dict:
    """Search documentation by keyword."""
    results = fetch_docs(query)
    return {"results": results, "count": len(results)}

if __name__ == "__main__":
    mcp.run()  # stdio by default
```

## TypeScript SDK Quick Start

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new Server({ name: "my-server", version: "1.0.0" });

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "search_docs") {
    return { content: [{ type: "text", text: JSON.stringify(results) }] };
  }
  throw new Error("Unknown tool");
});

await server.connect(new StdioServerTransport());
```

## Tool Design Patterns

```python
# Good: atomic, typed, descriptive
@mcp.tool()
def query_database(
    sql: str,
    timeout_seconds: int = 30,
    readonly: bool = True
) -> dict:
    """Execute a SQL query.
    
    Args:
        sql: The SQL query to execute
        timeout_seconds: Query timeout (default 30s)
        readonly: If True, reject INSERT/UPDATE/DELETE
    """
    if readonly and not sql.strip().upper().startswith("SELECT"):
        raise ValueError("Only SELECT queries in readonly mode")
    return {"rows": run_query(sql), "elapsed_ms": ...}
```

## Resources and Prompts

```python
# Resource: read-only reference data
@mcp.resource("file://docs/{doc_id}")
def get_doc(doc_id: str) -> str:
    """Retrieve a documentation page by ID."""
    return fetch_doc(doc_id)

# Prompt: reusable reasoning scaffold
@mcp.prompt("debug_error")
def debug_prompt(error_type: str, stack_trace: str) -> str:
    return f"Help me debug this {error_type}:\n{stack_trace}\nFocus on root cause."
```

## Docker Packaging

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY server.py .
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:8000/health || exit 1
CMD ["python", "server.py", "--transport=sse", "--host=0.0.0.0", "--port=8000"]
```

```yaml
# docker-compose.yml
services:
  mcp-server:
    build: .
    ports: ["8000:8000"]
    environment:
      - API_KEY=${API_KEY}
      - DATABASE_URL=${DATABASE_URL}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 3s
      retries: 3
    restart: unless-stopped
    networks:
      default:
        enable_ipv6: false   # prevents aiohttp IPv6 connection errors
```

## Security: Secrets and Path Guards

```python
import os

# Fail fast on startup if required env vars missing
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY environment variable not set")

# Path traversal guard for file tools
BASE_DIR = "/safe/data"

@mcp.tool()
def read_file(path: str) -> str:
    """Read a file from the safe directory."""
    safe_path = os.path.abspath(os.path.join(BASE_DIR, path))
    if not safe_path.startswith(BASE_DIR):
        raise ValueError("Path traversal not allowed")
    with open(safe_path) as f:
        return f.read()
```

## Testing

```bash
# Visual inspector (no Claude needed)
mcp dev python server.py

# Unit tests
pytest test_server.py -v
```

```python
def test_query_validation():
    with pytest.raises(ValueError):
        query_database("DROP TABLE users")

def test_path_traversal():
    with pytest.raises(ValueError):
        read_file("../../etc/passwd")
```

## Multi-Server Config

```json
// claude_desktop_config.json  (~/.config/Claude/)
{
  "mcpServers": {
    "database": { "command": "python", "args": ["/path/db_server.py"] },
    "git":      { "command": "python", "args": ["/path/git_server.py"] }
  }
}

// .mcp.json  (Claude Code: project root or ~/.mcp.json)
{
  "mcpServers": {
    "database": { "command": "python server.py", "cwd": "/path/db" }
  }
}
```

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Tool not appearing | Not registered or schema error | Check server logs; restart Claude Desktop |
| Connection refused | Wrong transport or port conflict | Verify stdio vs SSE; `lsof -i :8000` |
| IPv6 error | aiohttp tries IPv6 first | `enable_ipv6: false` in compose network |
| Schema validation error | Return type mismatch | Match type hints to actual return values |
| LLM not using tool | Ambiguous name/params | Rename to `verb_noun`; clarify docstring |
| Timeout | Long-running tool | Make async; return status early, let LLM poll |
