---
title: AI Systems Architect
slug: ai-systems-architect
description: |
  Design production-grade agentic AI systems end-to-end: architect complex agent workflows (ReAct, Plan-and-Execute, multi-agent coordination), build and federate MCP servers for tool integration, design intelligent RAG pipelines with embedding optimization and hybrid retrieval, develop AI skills with progressive disclosure, and evaluate systems for safety and cost efficiency. This is your domain-owning specialist for the entire stack—from agent choreography and memory federation to MCP scaffolding and skill security auditing.
triggers:
  - "design a system for <agent/workflow>"
  - "build an MCP server for <domain>"
  - "architect a RAG pipeline for <use case>"
  - "secure and evaluate my AI system"
  - "create a skill that <requirement>"
  - "set up federated memory across <agents/services>"
  - "optimize <agent> for cost and latency"
tags: ["agents", "MCP", "RAG", "memory", "skills", "evaluation", "architecture"]
---

## Why This Matters

Building production AI systems requires coordinating multiple layers: agents that decide *what* to do, tools (via MCP) that let them *do* it, memory that lets them *remember*, and RAG pipelines that let them *know*. Each layer has patterns and pitfalls. This skill consolidates that knowledge and explains the WHY behind every architectural choice.

---

## Part 1: Agentic Architecture

### The Core Agent Loop

Agents follow a thinking-act-observe cycle. The dominant pattern is **ReAct** (Reasoning + Acting):

```
User Input → [Thought: reason about goal]
           → [Action: call tool with args]
           → [Observation: see result]
           → [repeat until done or max steps]
           → Final Answer
```

**Why ReAct works:** It gives the model explicit space to reason before acting, reducing hallucination and enabling error recovery. The transcript becomes auditable.

### When to Use Agent Patterns

| Pattern | Best For | Trade-offs |
|---------|----------|-----------|
| **ReAct** | Exploratory tasks, debugging, complex reasoning | More tokens (verbose thinking), slower |
| **Plan-and-Execute** | Well-defined workflows, structured goals | Requires upfront planning capability |
| **Multi-Agent** | Specialized roles (researcher, validator, coder) | Coordination overhead, latency |
| **Router** | Many use cases, customer segmentation | Requires good routing logic |
| **Evaluator-Optimizer** | Quality gates, iterative improvement | Extra forward pass, cost |

### Building Reliable Agents

**Tool Use Pattern:**
```python
# Define tools with clear descriptions and parameter schemas
tools = [
    {
        "name": "search_knowledge_base",
        "description": "Find relevant documents. Use when user asks factual questions.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search terms (3-5 words)"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 10}
            },
            "required": ["query"]
        }
    }
]
```

**Why:** Clear descriptions let the model invoke tools correctly. Parameter schemas prevent invalid calls.

**Context Window Management:**
- Reserve 20-30% for output
- Trim tool history: keep last N observations (5-10), summarize earlier ones
- Use sliding window: when approaching limit, archive to external memory
- Implement `truncate_transcript()` that collapses repeated tool calls

**Guardrails Pattern:**
```python
def guardrail_validator(action, state):
    # Prevent loops: reject if same action called 3x consecutively
    if (state['history'][-3:] == [action, action, action]):
        return False, "Repeating action—try a different approach"

    # Prevent escapes: deny tools outside allowed set
    if action['tool'] not in ALLOWED_TOOLS:
        return False, f"Tool {action['tool']} not available"

    return True, None
```

### Evaluating Agent Quality

Create evaluation datasets:
```json
{
  "test_cases": [
    {
      "input": "Find the Q3 revenue and summarize performance",
      "expected_steps": ["query_database", "analyze_results"],
      "rubric": ["correct_figure", "identifies_trend", "uses_search_first"]
    }
  ]
}
```

**Why:** LLM agents are stochastic. Test with 20+ cases. Use LLM-as-judge for semantic correctness.

---

## Part 2: MCP Server Architecture

### What MCP Is and Why It Matters

MCP (Model Context Protocol) is a *standardized transport* for tools. Instead of embedding tool definitions in prompts, MCP lets you:
- Version tools independently
- Secure tool access with auth
- Scale across services
- Test tools without AI in the loop

### MCP Server Fundamentals

**FastMCP (Python):**
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-tool-service", implementation="my_implementation")

@mcp.tool()
def search_database(query: str, limit: int = 10) -> str:
    """Search for records. Why: Provides factual grounding."""
    results = db.search(query, limit=limit)
    return format_results(results)

# Register resources for context
@mcp.resource("documents://recent")
def recent_docs():
    """Return recent docs without tool invocation."""
    return get_recent()
```

**Why this structure:**
- `@mcp.tool()` auto-generates OpenAPI schema
- Docstring becomes tool description
- Type hints become parameter schemas
- Resources let you serve static/computed context

**TypeScript SDK pattern:**
```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new Server({
  name: "example-server",
  version: "1.0.0",
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "search_api") {
    const result = await fetch(`${API_BASE}?q=${args.query}`)
      .then(r => r.json());
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }

  throw new Error(`Unknown tool: ${name}`);
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

### Choosing Transport Modes

| Mode | Use Case | Pros | Cons |
|------|----------|------|------|
| **stdio** | Local, single client | Simple, no network | Single process |
| **SSE** | Streaming, async | Real-time updates | Requires HTTPS |
| **HTTP** | Multi-client, stateless | Scalable | Polling overhead |
| **WebSocket** | Bi-directional | Low latency | Connection management |

**Decision:** Use stdio for development, SSE for single-client apps, HTTP for multi-tenant services.

### MCP Auto-Scaffolder

Generate servers from OpenAPI specs automatically:

```python
def scaffold_mcp_from_openapi(openapi_spec_path: str, output_dir: str):
    """
    Why: Reduces boilerplate, ensures consistency, catches API changes.
    """
    spec = load_openapi(openapi_spec_path)

    for endpoint in spec['paths']:
        tool_name = endpoint['operationId']  # e.g., 'search_documents'
        params = endpoint['parameters']

        # Generate tool function
        tool_code = f"""
@mcp.tool()
def {tool_name}({', '.join(f'{p["name"]}: {python_type(p)}' for p in params)}) -> str:
    '''Why: {endpoint['description']}'''
    result = requests.{endpoint['method'].lower()}(
        '{endpoint['path']}',
        params={{{', '.join(f'"{p["name"]}": {p["name"]}' for p in params)}}}
    )
    return json.dumps(result.json())
"""
        write_file(f"{output_dir}/{tool_name}.py", tool_code)
```

### Multi-Server Federation

**Why federate:** Different domains own different tools. Coordinate without coupling.

```python
# Server 1: Search service
@mcp.tool()
def search(query: str) -> str:
    return client.search(query)

# Server 2: Analysis service
@mcp.tool()
def analyze(results: str) -> str:
    """Calls back to search service via MCP."""
    search_client = MCPClient("search_server")
    context = search_client.call_tool("search", query=results)
    return analyze_with_context(context)
```

**Why:** Loose coupling. Services can be deployed, updated, or scaled independently.

### Securing MCP Servers

```python
from functools import wraps
import hmac

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = os.getenv("MCP_API_KEY")
        provided = request.headers.get("X-API-Key")
        if not hmac.compare_digest(key, provided or ""):
            raise PermissionError("Invalid API key")
        return f(*args, **kwargs)
    return decorated

@mcp.tool()
@require_api_key
def protected_tool():
    """This tool requires authentication."""
    pass
```

### Docker Packaging for MCP

Deploy MCP servers reliably using Docker + docker-compose for SSE transport (HTTP-based, works with proxies):

```dockerfile
# Dockerfile for MCP service
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy MCP server code
COPY mcp_server/ ./

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run SSE transport (HTTP)
CMD ["python", "-m", "mcp.server.sse", "--port", "8000"]
```

```yaml
# docker-compose.yml for MCP service federation
version: '3.8'

services:
  mcp-search:
    image: mcp-search-service:latest
    ports:
      - "8001:8000"
    environment:
      SEARCH_API_KEY: ${SEARCH_API_KEY}
      LOG_LEVEL: info
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3

  mcp-analysis:
    image: mcp-analysis-service:latest
    ports:
      - "8002:8000"
    environment:
      DB_URL: postgresql://user:pass@db:5432/analysis
    depends_on:
      - db
    restart: unless-stopped

  # Reverse proxy (SSE requires stable endpoint)
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - mcp-search
      - mcp-analysis

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: analysis
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pg_data:/var/lib/postgresql/data

volumes:
  pg_data:
```

**Why Docker for MCP:** Consistent environment, easy versioning, multi-server federation, isolated dependencies, production-ready deployment.

---

## Part 3: Federated Memory Architecture

### The Three-Layer Model

Memory operates at three scales:

1. **Working Memory** (conversation): Last 10-20 turns, in-context
   - Why: Current task context. Fits in prompt.
   - Tech: Simple list in request object

2. **Recall Memory** (session): Relevant facts from this conversation history
   - Why: Retrieve past context without full history bloat.
   - Tech: Vector embeddings, semantic search

3. **Archival Memory** (persistent): Lessons, patterns, reference data
   - Why: Stable knowledge. Survives session restarts.
   - Tech: Graph DB or structured knowledge base

### Vector Store Selection

| Store | Embedding Cost | Latency | Scalability | Best For |
|-------|-----------------|---------|-------------|----------|
| **pgvector** | None (in-DB) | ~50ms | Single DB | Co-located services, <1M vectors |
| **Qdrant** | Vectorized client-side | ~10ms | Distributed | High QPS, multi-tenancy |
| **ChromaDB** | Minimal (local) | ~5ms | Single machine | Prototyping, small corpora |
| **Pinecone** | Client pays | ~5ms | Fully managed | Hands-off scaling |

**Decision framework:** Use pgvector if you already run Postgres. Use Qdrant for high throughput. Use ChromaDB for rapid iteration.

### Embedding Model Strategy

```python
# Strategy 1: Dense embedding (most cases)
from sentence_transformers import SentenceTransformer
embedder = SentenceTransformer("all-MiniLM-L6-v2")  # Fast, good quality
embeddings = embedder.encode(texts, normalize_embeddings=True)

# Strategy 2: Sparse embedding (keyword relevance)
from sklearn.feature_extraction.text import TfidfVectorizer
vectorizer = TfidfVectorizer(max_features=1000)
sparse_vecs = vectorizer.fit_transform(texts)

# Strategy 3: Hybrid (best recall)
# Combine dense + sparse, rerank by BM25, then semantic relevance
dense_scores = cosine_similarity(query_dense, doc_dense)
sparse_scores = bm25_similarity(query, docs)
combined = 0.7 * dense_scores + 0.3 * sparse_scores
top_k = argsort(combined)[-k:]
```

**Why hybrid:** Catches both semantic AND lexical matches. Example: query "CEO compensation" should match both "executive pay" (semantic) and documents with the literal term "CEO" (lexical).

### Federated Memory Banks

**Pattern:** Each agent or service owns a memory bank. Coordinate via MCP.

```python
# Agent 1: Research Agent
class ResearchAgent:
    def __init__(self):
        self.memory = MemoryBank("research")  # Sovereign

    def capture_insight(self, fact: str):
        """Why: Persist findings without central authority."""
        self.memory.store(
            content=fact,
            metadata={"type": "finding", "confidence": 0.9},
            embedding=embed(fact)
        )

# Shared Access via MCP
@mcp.tool()
def query_research_memory(query: str) -> str:
    """Search any agent's memory."""
    agent = get_agent(request.agent_id)  # Per-agent auth
    results = agent.memory.search(query, top_k=5)
    return format_results(results)
```

**Why federated:** Agents control their own data. Queries are explicit. Easy to audit/compliance.

### Graph Knowledge for Relationships

```python
# Capture relationships, not just facts
memory.store_relationship(
    source="Task-123",
    relation="depends_on",
    target="Task-456",
    confidence=0.95
)

# Query the graph
dependent_tasks = memory.graph.query(
    "MATCH (t:Task {id: 'Task-123'}) -[:depends_on]-> (dep:Task) RETURN dep"
)
```

**Why:** Structured reasoning. Example: agent can infer "Task-123 is blocked" by traversing dependency graph.

---

## Part 4: RAG Pipeline Architecture

### Chunking Strategy (The Foundation)

**Why chunking matters:** Too small = lost context. Too large = noise.

```python
def chunk_intelligently(text: str, strategy: str = "semantic"):
    """Why: Different content types need different chunk sizes."""

    if strategy == "semantic":
        # Split on sentence boundaries, group into ~300 token chunks
        sentences = split_sentences(text)
        chunks = []
        current = []
        for sent in sentences:
            current.append(sent)
            if count_tokens(current) >= 300:
                chunks.append(" ".join(current))
                current = [sent]  # Overlap by 1 sentence
        return chunks

    elif strategy == "hierarchical":
        # Preserve document structure
        return [
            {"type": "section", "title": h1, "content": section}
            for h1, section in parse_sections(text)
        ]

    elif strategy == "sliding_window":
        # For code: chunks of 200 tokens, 50-token overlap
        tokens = tokenize(text)
        return [
            tokens[i:i+200]
            for i in range(0, len(tokens), 150)  # 50-token step
        ]
```

### Retrieval Optimization

**Basic RAG (naive):**
```python
def naive_retrieval(query: str, k: int = 5):
    query_vec = embed(query)
    scores = cosine_similarity(query_vec, all_doc_vecs)
    return top_k_indices(scores, k)
```

**Why this fails:** Query embeddings are shallow. "What is the CEO's strategy?" won't match "exec compensation" even if both are in strategy docs.

**Better: Multi-stage retrieval**
```python
def smart_retrieval(query: str, k: int = 5):
    """Why: Broad recall first, then precision."""

    # Stage 1: Semantic search (broad)
    query_vec = embed(query)
    semantic_candidates = vector_search(query_vec, k * 3)

    # Stage 2: Lexical filter (precision)
    query_keywords = extract_keywords(query)
    candidates = [
        c for c in semantic_candidates
        if any(kw in c['text'].lower() for kw in query_keywords)
    ]

    # Stage 3: Rerank (quality)
    reranked = rerank_by_relevance(query, candidates, model="cross-encoder")
    return reranked[:k]
```

### Hybrid Search

```python
def hybrid_search(query: str, k: int = 5):
    """Why: Dense + sparse catches both semantic and keyword matches."""

    # Dense: semantic similarity
    query_dense = embed(query)
    dense_scores = vector_db.search(query_dense, k * 2)  # Get more candidates

    # Sparse: BM25 on exact terms
    query_sparse = vectorizer.transform([query])
    sparse_scores = bm25_search(query_sparse, k * 2)

    # Combine: weight semantic + lexical
    combined = {}
    for doc_id, score in dense_scores:
        combined[doc_id] = 0.6 * score
    for doc_id, score in sparse_scores:
        combined[doc_id] = combined.get(doc_id, 0) + 0.4 * score

    return sorted(combined.items(), key=lambda x: x[1], reverse=True)[:k]
```

### Building End-to-End RAG

```python
class RAGPipeline:
    def __init__(self, vector_store, llm):
        self.vector_store = vector_store
        self.llm = llm

    def ingest(self, documents: List[str]):
        """Why: Chunk once, embed once, index once."""
        for doc in documents:
            chunks = chunk_intelligently(doc, strategy="semantic")
            for chunk in chunks:
                vec = embed(chunk)
                self.vector_store.store(chunk, vec)

    def query(self, user_query: str) -> str:
        """Why: Retrieve → Augment → Generate."""

        # Retrieve
        retrieved = self.vector_store.search(user_query, k=5)

        # Augment: format retrieved context
        context = "\n\n".join([
            f"[Source {i+1}]\n{chunk}"
            for i, chunk in enumerate(retrieved)
        ])

        # Generate
        prompt = f"""Answer based on this context:

{context}

Question: {user_query}

Answer:"""

        answer = self.llm.generate(prompt)
        return answer
```

### RAG Quality Evaluation

```python
def evaluate_rag(test_cases: List[dict], pipeline: RAGPipeline):
    """Why: RAG fails silently. Measure retrieval quality."""

    results = {"retrieval_hits": 0, "generation_quality": 0}

    for case in test_cases:
        query = case["query"]
        expected_doc_ids = case["relevant_docs"]
        expected_answer = case["gold_answer"]

        # Metric 1: Did we retrieve the right docs?
        retrieved = pipeline.vector_store.search(query, k=5)
        retrieved_ids = [r["doc_id"] for r in retrieved]
        hits = len(set(retrieved_ids) & set(expected_doc_ids))
        results["retrieval_hits"] += hits / len(expected_doc_ids)

        # Metric 2: Does the answer match?
        answer = pipeline.query(query)
        similarity = semantic_similarity(answer, expected_answer)
        results["generation_quality"] += similarity

    return {k: v / len(test_cases) for k, v in results.items()}
```

---

## Part 5: AI Skills Development

### SKILL.md Format: YAML Frontmatter Structure

Every skill file opens with YAML frontmatter (metadata between `---` delimiters), followed by Markdown content:

```yaml
---
title: Skill Name
slug: kebab-case-name
description: |
  One paragraph describing WHAT this skill does and WHY you need it.
  Include trigger patterns. Keep to 2-3 sentences.
triggers:
  - "when I need to <action>"
  - "help me <task>"
tags: ["domain", "category"]
---

## Section 1: Core Concept
Why it matters. Decision framework.

## Section 2: Implementation
Code examples. Best practices.

## Section 3: Troubleshooting
Common pitfalls and solutions.
```

**Why YAML frontmatter:** Parseable metadata. Tools extract title, triggers, tags without reading full Markdown. Enables discoverability, tagging, and skill indexing. **Progressive disclosure:** Headers let you scan. Code is concrete. Triggers make it discoverable.

### Prompt Engineering Fundamentals

**Pattern: Role + Task + Constraints + Examples**
```
You are a <ROLE>. Your job is to <TASK>.

Constraints:
- <constraint_1>
- <constraint_2>

Examples:
Input: "..."
Output: "..."

Now, <ACTUAL_TASK>
```

**Why:** Clear role reduces hallucination. Examples ground behavior.

### Structured Output: Constraining Agent Responses

Unstructured LLM outputs are unparseable. Force structured output using JSON mode, schemas, or validation:

```python
import json
from pydantic import BaseModel, Field

# 1. Pydantic validation: Type-safe response parsing
class TaskResult(BaseModel):
    success: bool
    task_id: str
    findings: list[str] = Field(default_factory=list)
    error: str | None = None

# In your agent:
llm_response = llm.generate_with_schema(
    prompt="Find risks in this code",
    schema=TaskResult.model_json_schema()
)
result = TaskResult(**json.loads(llm_response))  # Type-safe parsing

# 2. JSON mode (native in Claude/GPT-4)
response = client.messages.create(
    model="claude-opus-4-1",
    max_tokens=1024,
    messages=[...],
    temperature=1,  # Required for JSON mode
    betas=["interleaved-thinking-2025-05-14"],  # Extended thinking
)

# Response is guaranteed JSON
json_output = json.loads(response.content[0].text)

# 3. XML tags (alternative to JSON for some models)
prompt = """Analyze the code. Return results in XML:
<analysis>
  <risk_level>high|medium|low</risk_level>
  <findings>
    <finding>...</finding>
  </findings>
  <recommendation>...</recommendation>
</analysis>"""

# Parse XML response
import xml.etree.ElementTree as ET
root = ET.fromstring(llm_response)
risk_level = root.find("risk_level").text
```

**Why structured output:** Prevents parsing errors. Enables downstream automation (automatically file issues, trigger workflows). Reduces hallucination—model "thinks inside the schema."

### Security Auditing Skills Before Use

```python
def audit_skill_for_injection(skill_path: str) -> List[str]:
    """Why: Skills are user-supplied code. Check before exec."""

    warnings = []
    content = read_file(skill_path)

    # Red flags
    dangerous_patterns = {
        "os.system": "Shell injection risk",
        "eval(": "Code injection",
        "subprocess.call(": "Command execution",
        "__import__": "Dynamic import",
    }

    for pattern, reason in dangerous_patterns.items():
        if pattern in content:
            warnings.append(f"UNSAFE: {reason} in {skill_path}")

    return warnings
```

---

## Part 6: Cost Optimization & Evaluation

### Token Usage Estimator

```python
def estimate_cost(architecture: dict, request_count: int = 1000) -> dict:
    """Why: Multi-agent systems can be expensive. Plan upfront."""

    config = {
        "llm_model": "gpt-4-turbo",
        "input_tokens_per_request": 2000,
        "output_tokens_per_request": 500,
        "agents": 3,
        "tool_calls_per_agent": 2,  # Feedback loops
    }

    total_input = (
        request_count
        * config["input_tokens_per_request"]
        * config["agents"]
        * (1 + 0.1 * config["tool_calls_per_agent"])  # Redundancy
    )

    total_output = request_count * config["output_tokens_per_request"] * config["agents"]

    cost = (
        (total_input / 1000) * INPUT_PRICE +
        (total_output / 1000) * OUTPUT_PRICE
    )

    return {
        "total_cost": cost,
        "per_request": cost / request_count,
        "input_tokens": total_input,
        "output_tokens": total_output,
    }
```

### Evaluator-Optimizer Loop

```python
class EvaluatorOptimizer:
    def __init__(self, agent, evaluator_llm):
        self.agent = agent
        self.evaluator = evaluator_llm

    def run_with_evaluation(self, task: str, max_iterations: int = 3):
        """Why: Iterative improvement beats single-pass."""

        for i in range(max_iterations):
            # Generate candidate
            result = self.agent.run(task)

            # Evaluate
            score = self.evaluator.score(
                task=task,
                result=result,
                rubric=["accuracy", "completeness", "clarity"]
            )

            if score > 0.8:  # Good enough
                return result

            # Provide feedback
            self.agent.feedback = self.evaluator.critique(task, result)

        return result
```

---

## Troubleshooting Decision Trees

### Agent Gets Stuck in Loops

**Symptom:** Same tool called repeatedly.

**Why it happens:** Agent doesn't know what else to try.

**Fix:**
1. Add guardrail that rejects repeated actions
2. Expand tool descriptions so agent knows alternatives
3. Increase context window so agent sees history
4. Add explicit "try something different" instruction

### RAG Retrieves Wrong Documents

**Why it happens:** Query embedding is different from doc embedding distribution.

**Fix:**
1. Test with hardcoded synonyms first
2. Switch to hybrid search
3. Use query expansion (rewrite query as multiple phrasings)
4. Rerank with cross-encoder

### MCP Server Not Accessible

**Why it happens:** Transport not set up correctly.

**Fix:**
1. Verify stdio fd 0/1 are clean (no debug prints)
2. Check SSE endpoint returns event-stream content-type
3. For HTTP, ensure CORS headers if cross-origin
4. Test with `mcp-cli` before using in production

---

## Cross-Platform Portability for AI Systems

What's portable vs. platform-specific when deploying AI systems:

**Portable (write once, run anywhere):**
- **LLM API calls** (Claude, GPT, Llama via API): Same code works Linux/macOS/Windows
- **MCP servers** with stdio: Cross-platform (JSON-RPC over stdin/stdout)
- **Vector databases** (Qdrant, Pinecone): Language-agnostic APIs
- **Python/Node AI frameworks**: If dependencies lock to same versions (pyproject.toml, package-lock.json)
- **Docker containers**: Standardize environments across platforms

**Platform-specific (extra care needed):**
- **File paths**: Use `pathlib.Path` (Python) or `path.join()` (Node), not hardcoded `/data/` or `C:\data\`
- **Shell scripts** (bash, PowerShell): Write platform-agnostic alternatives (Python scripts, Node CLIs)
- **Subprocess calls**: Use `subprocess.run()` with `shell=False` for portability; avoid shell-specific syntax
- **Line endings**: Git: `core.autocrlf = true` to normalize CRLF/LF
- **Temp directories**: Use `tempfile.TemporaryDirectory()` not `/tmp` (doesn't exist on Windows)
- **Environment variables**: Case-sensitive on Linux (use lowercase, access via `os.environ.get()`)

**Checklist for portable AI systems:**
```python
# DON'T: Hardcoded paths
skill_dir = "/home/user/skills"

# DO: Use pathlib or os.path
from pathlib import Path
skill_dir = Path.home() / "skills"

# DON'T: Shell-specific syntax
subprocess.run(f"cat {file} | grep error", shell=True)

# DO: Python equivalents
with open(file) as f:
    for line in f:
        if "error" in line:
            print(line)

# DON'T: Assume Unix paths in MCP
mcp_config = {
    "server_path": "/opt/mcp-servers/search"
}

# DO: Use cross-platform resolution
import shutil
mcp_server = shutil.which("mcp-search") or Path.home() / ".local" / "bin" / "mcp-search"
```

---

## When To Use Each Pattern

- **Use ReAct** when reasoning is the bottleneck
- **Use Plan-and-Execute** when you have a clear goal structure
- **Use Multi-Agent** when tasks are parallelizable
- **Use pgvector** when memory is co-located with data
- **Use hybrid search** when your domain mixes keywords and semantics
- **Use federated memory** when multiple services need to coordinate
- **Use MCP** whenever you want tool versioning and portability
- **Use Docker** for consistent, cross-platform deployment
- **Use structured output** to eliminate parsing errors and enable automation

---

## Key Principles

1. **Explain the why:** Every pattern exists to solve a problem.
2. **Measure quality:** You can't optimize what you don't measure.
3. **Start simple:** ReAct → Plan-and-Execute → Multi-Agent as you scale.
4. **Modularize:** Separate agents, memory, tools, and evaluation.
5. **Security first:** Audit skills, validate tool calls, use auth on MCP servers.
6. **Cost transparency:** Estimate before building. Monitor during.
7. **Portability matters:** Write code that works across Linux, macOS, Windows.

