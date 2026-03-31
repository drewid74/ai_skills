---
name: mcp-server-dev
description: "Use this skill whenever the user wants to build, debug, test, or deploy an MCP (Model Context Protocol) server. Triggers include: any mention of 'MCP', 'Model Context Protocol', 'MCP server', 'MCP tool', 'FastMCP', 'mcp.run', 'tool registration', 'MCP client', 'Claude tool', 'custom tool', 'tool_use', 'MCP transport', 'stdio transport', 'SSE transport', 'MCP resource', 'MCP prompt', or requests to expose an API as a Claude tool, build a bridge between Claude and an external service, create a server that Claude can call, or wrap an existing API for LLM tool use. Also use when the user is debugging MCP connection issues, designing tool schemas, packaging MCP servers as Docker containers, or building federated multi-server architectures. If someone says 'I want Claude to be able to talk to X' where X is any external service, use this skill."
---

## Overview

MCP (Model Context Protocol) is the open protocol for connecting LLMs to external tools, data sources, and services. Build servers that expose capabilities as tools and resources that Claude and other LLMs can invoke. Use this skill to architect anything from single-tool servers to federated multi-server systems.

## Quick Start: FastMCP (Python)

FastMCP is the fastest way to build MCP servers. Minimal setup, automatic schema generation from type hints.

```python
from fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def search_docs(query: str) -> str:
    """Search documentation by keyword."""
    return f"Found results for: {query}"

if __name__ == "__main__":
    mcp.run()  # stdio mode by default
```

Run with `python server.py`. Claude Desktop or Claude Code auto-detects and connects via stdio.

**Why FastMCP**: Decorator-based tool registration is fast to write. Type hints automatically generate JSON schemas. Perfect for local development and simple integrations.

## Quick Start: TypeScript SDK

For Node.js environments or when you need ecosystem tooling.

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new Server({ name: "my-server", version: "1.0.0" });

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "search_docs") {
    return { content: [{ type: "text", text: "Search results..." }] };
  }
  throw new Error("Unknown tool");
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

Run with `node server.js`. More verbose than FastMCP but gives you full control over request/response handling.

## Tool Design Patterns

**Keep tools focused**: One tool = one atomic action. Don't create a mega-tool that does query, insert, update, delete. Create `query_database`, `insert_row`, `update_row`, `delete_row` instead. This lets the LLM reason about each action independently and retry safely.

**Naming conventions**: Use `verb_noun` format: `search_documents`, `create_issue`, `get_user_profile`, `send_email`. Avoid generic names like `do_thing` or `action`. The tool name is part of the LLM's reasoning.

**Parameter design**: Use descriptive names and add docstring descriptions for each parameter. Set sensible defaults. Avoid boolean flags when you can use enums (clearer semantics).

```python
@mcp.tool()
def query_database(
    sql: str,
    timeout_seconds: int = 30,
    readonly: bool = True
) -> str:
    """Execute a SQL query against the database.
    
    Args:
        sql: The SQL query to execute
        timeout_seconds: Query timeout (default 30s, max 120s)
        readonly: If True, reject INSERT/UPDATE/DELETE (safety default)
    """
```

**Return values**: Return structured data (dicts, lists, objects), not pre-formatted strings. The LLM formats output for the user. If you return JSON, return it as a dict, not a string.

```python
# Good: return structured data
return {
    "user_id": 123,
    "name": "Alice",
    "email": "alice@example.com"
}

# Avoid: pre-formatted string
return "User: Alice (123) - alice@example.com"
```

**Error handling**: Raise descriptive exceptions, don't return error messages as success. The MCP protocol separates content from errors.

```python
# Good
if not sql.strip().upper().startswith("SELECT"):
    raise ValueError("Only SELECT queries allowed (readonly mode)")

# Avoid
if not sql.strip().upper().startswith("SELECT"):
    return {"error": "Only SELECT queries allowed"}
```

**Idempotency**: Design tools to be safe to retry. If a tool creates a resource, make it idempotent (`create_if_not_exists`). This handles network retries gracefully and reduces LLM error handling complexity.

## Resources and Prompts

**Resources** expose read-only data. Use them for documents, configuration, context that the LLM reads but doesn't modify. Example: expose the current user's profile, team membership, or documentation.

```python
@mcp.resource("file://my_docs/{doc_id}")
def get_documentation(doc_id: str) -> str:
    """Retrieve documentation by ID."""
    return fetch_doc(doc_id)
```

**Prompts** are reusable prompt templates with parameters. Use them to inject domain knowledge or structured guidelines into Claude's reasoning.

```python
@mcp.prompt("debug_error")
def debug_error_prompt(error_type: str, stack_trace: str) -> str:
    return f"""Help me debug this {error_type}:
{stack_trace}

Focus on the root cause."""
```

**When to use which**: Read-only data that the LLM references often → resource. Reusable instructions for the LLM → prompt. Everything else → tool.

## Transport Modes

**stdio**: Default for local development. Process-to-process communication. Used by Claude Desktop and Claude Code. No network overhead, no firewall issues. Perfect for single-machine setups.

**SSE (Server-Sent Events)**: HTTP-based transport for remote servers. Server listens on a port, client opens an HTTP connection. Works through firewalls. Slower than stdio but necessary for Docker/cloud deployments.

**Streamable HTTP**: Newer transport combining HTTP request/response with streaming. Better latency than SSE for large messages. Check SDK documentation for availability.

**When to use which**:
- Local development: stdio
- Docker container: SSE or HTTP
- Remote server: SSE or HTTP
- High-performance remote: HTTP if available

## Docker Packaging

Python MCP server with SSE transport:

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

```python
# server.py with SSE support
if __name__ == "__main__":
    import sys
    transport_mode = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    
    if "sse" in transport_mode:
        from mcp.server.sse import SseServerTransport
        transport = SseServerTransport(url="http://0.0.0.0:8000")
    else:
        transport = StdioServerTransport()
    
    mcp.run(transport=transport)
```

**docker-compose.yml**:

```yaml
version: '3.9'
services:
  mcp-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - API_KEY=${API_KEY}
      - DATABASE_URL=${DATABASE_URL}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 3s
      retries: 3
    restart: unless-stopped
```

**IPv6 gotcha**: Docker bridge networks can have IPv6 issues. Use `enable_ipv6: false` on the network, or use AF_INET with aiohttp connector for outbound calls.

## Authentication and Security

**Never hardcode credentials**. Always inject via environment variables.

```python
import os

API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY environment variable not set")

@mcp.tool()
def call_external_api(endpoint: str) -> dict:
    headers = {"Authorization": f"Bearer {API_KEY}"}
    return requests.get(endpoint, headers=headers).json()
```

**Validate all inputs**: Sanitize SQL queries, validate file paths, check parameter ranges. Don't trust the LLM or user input.

```python
import os

@mcp.tool()
def read_file(path: str) -> str:
    """Read a file from the safe directory."""
    # Resolve to absolute path and ensure it's within allowed directory
    base = "/safe/data"
    safe_path = os.path.abspath(os.path.join(base, path))
    
    if not safe_path.startswith(base):
        raise ValueError("Path traversal not allowed")
    
    with open(safe_path) as f:
        return f.read()
```

**Rate limiting**: If the server integrates with rate-limited APIs, implement backoff and quotas.

**Principle of least privilege**: Expose only the tools needed. Don't expose admin tools. Use readonly mode for databases. Separate write and read tools if permissions differ.

## Testing MCP Servers

**Inspector UI** (`mcp dev`): Run your server and inspect available tools/resources in a web UI. Fast manual testing.

```bash
mcp dev python server.py
```

**CLI testing** (`claude -p`): Test with the Claude CLI in pipe mode.

```bash
echo '{"tool": "search_docs", "query": "testing"}' | claude -p server.py
```

**Unit testing**: Test tool functions independently before integration.

```python
import pytest

def test_search_docs():
    result = search_docs("python")
    assert "python" in result.lower()

def test_query_validation():
    with pytest.raises(ValueError):
        query_database("DROP TABLE users")
```

**Integration testing**: Start the server and test full request/response cycle. Use the official MCP test client if available.

**Debugging**: Set `MCP_LOG_LEVEL=debug` environment variable and check logs for connection/schema issues.

## Multi-Server Architecture

Run multiple MCP servers simultaneously, each owning a domain:
- Database server (query, insert, update, delete)
- Git server (commit, push, create PR)
- Search server (full-text search)
- Email server (send, draft)

Each server has its own process, its own connection to Claude. They don't communicate with each other (no coupling).

**Federated architecture pattern**: Servers are sovereign. If one server needs data from another, it goes through Claude as the orchestrator. Claude handles cross-server reasoning.

**Client configuration**:

`claude_desktop_config.json` (Claude Desktop):
```json
{
  "mcpServers": {
    "database": {
      "command": "python",
      "args": ["/path/to/db_server.py"]
    },
    "git": {
      "command": "python",
      "args": ["/path/to/git_server.py"]
    }
  }
}
```

`.mcp.json` (Claude Code):
```json
{
  "mcpServers": {
    "database": { "command": "python server.py", "cwd": "/path/to/db" },
    "git": { "command": "python server.py", "cwd": "/path/to/git" }
  }
}
```

## Common Patterns

**Database wrapper**: Expose query/insert/update as separate tools. Use readonly mode by default. Validate queries against a whitelist if possible.

**API bridge**: Wrap REST endpoints as tools. Forward authentication. Handle pagination and rate limits transparently.

**File system access**: Sandbox to a specific directory. Validate all paths. Support glob patterns for listing.

**Search integration**: Wrap SearXNG, Elasticsearch, or similar as a tool. Return ranked results with source URLs.

**Memory/knowledge base**: Store notes/facts with vector embeddings. Retrieve by semantic similarity. Let Claude iterate on the knowledge base.

## Deployment

**Local dev**: Run server directly, Claude Desktop/Code auto-connects via stdio.

**Docker**: Build image, run with docker-compose. Expose on a port. Register in config with SSE transport URL.

**Health monitoring**: Include `/health` endpoint. Set `restart: unless-stopped` in compose. Monitor exit codes.

**Claude Desktop registration**: Copy config to `~/.config/Claude/claude_desktop_config.json`.

**Claude Code registration**: Create `.mcp.json` in project root or `~/.mcp.json`.

## Troubleshooting

**Connection refused**: Check transport mode (stdio vs SSE). Verify port is bound. Check firewall rules. Look for port conflicts with `lsof -i :8000`.

**Tool not appearing**: Verify tool is registered with decorator/handler. Check server logs. Restart Claude Desktop. Verify JSON schema is valid.

**Timeout issues**: Long-running tools need async execution. Return early with a status, let the LLM poll. Or implement streaming responses.

**IPv6 Docker issue**: Use `enable_ipv6: false` in docker-compose networks section. Or use `AF_INET` constraint on aiohttp connectors.

**Schema validation errors**: Type hints must match actual return types. `str` function must return `str`, not `None` or `dict`. Check MCP logs for schema details.

**LLM not using tool**: Tool name unclear or too similar to others. Parameter names confusing. Return format inconsistent. Refactor tool name/parameters and regenerate schema.
