---
name: agentic-architecture
description: "Use this skill whenever the user wants to design, build, evaluate, or debug AI agent systems, RAG pipelines, or LLM-powered applications. Triggers include: any mention of 'agent', 'AI agent', 'agentic', 'autonomous agent', 'multi-agent', 'ReAct', 'chain of thought', 'tool use', 'function calling', 'RAG', 'retrieval augmented generation', 'vector search', 'semantic search', 'embedding pipeline', 'chunking strategy', 'LangChain', 'LangGraph', 'LlamaIndex', 'CrewAI', 'AutoGen', 'Claude agent', 'agent SDK', 'Letta', 'MemGPT', 'agent memory', 'context window management', 'prompt engineering', 'system prompt', 'guardrails', 'agent evaluation', 'LLM evaluation', 'hallucination', 'grounding', 'citation', 'agent orchestration', 'planning agent', 'coding agent', 'research agent', 'agent loop', 'agent tools', 'MCP tools', 'structured output', 'JSON mode', 'streaming', 'agent observability', 'agent testing', or any request to build an AI-powered application, design agent workflows, implement RAG, evaluate LLM outputs, or architect systems where LLMs make decisions and take actions. Also use when the user asks 'how do I build an AI agent?', 'how should I chunk my documents?', 'why is my RAG returning bad results?', or wants to connect an LLM to external tools and data. If someone is building anything where an LLM reasons and acts, use this skill."
---

## Overview

Architecture patterns for building AI agents that reason, use tools, and maintain context. Covers agent design patterns, RAG pipelines, tool integration, memory management, evaluation, and production deployment.

## Agent Design Patterns

### ReAct (Reasoning + Acting)

LLM observes → thinks → acts → observes result → repeats. Most common pattern: "Thought: I need to... Action: search_tool(...) Observation: result... Thought: Now I know..."

**When to use**: General-purpose agents, exploratory tasks, when the agent needs to figure out what to do.

**Implementation**: Tool-use loop with system prompt instructing step-by-step reasoning. Let the LLM decide what to do next based on current state.

### Plan-and-Execute

LLM creates a full plan upfront, then executes steps sequentially. Separate planning model (can be stronger/slower) from execution model (can be faster/cheaper).

**When to use**: Well-defined multi-step tasks, when you want the user to review the plan before execution.

**Trade-off**: Better coherence on complex tasks, but can't adapt to unexpected results mid-plan without replanning.

### Multi-Agent Patterns

Multiple specialized agents collaborate on a task. Choose the right pattern for your task:

- **Orchestrator/Worker**: One agent breaks down tasks and delegates to specialists. Good for diverse subtasks.
- **Pipeline**: Agents process sequentially (researcher → writer → editor). Good for staged workflows.
- **Debate**: Agents with different perspectives discuss and converge. Good for reasoning tasks where multiple viewpoints help.
- **Supervisor**: Oversees agent outputs, routes corrections. Good for quality control.

**Caution**: More agents = more complexity, latency, cost, and failure modes. Start with one agent. Add agents only when a single agent can't handle the task adequately.

### Router

Lightweight classifier routes requests to specialized handlers. "Is this a coding question? → code agent. Is this a search question? → search agent."

**When to use**: Diverse request types that benefit from different tools, prompts, or models.

**Implementation**: LLM classifier or keyword matching → dispatch to handler. Keeps each agent's context focused.

### Evaluator-Optimizer Loop

Agent generates output → evaluator critiques → agent refines → evaluator re-checks. Use for quality-critical outputs.

**Limit iterations**: 2–3 max to prevent infinite loops. Stop condition: evaluator says "good enough" or max iterations reached.

## RAG (Retrieval Augmented Generation)

### Pipeline Architecture

```
Documents → Chunk → Embed → Index (vector store)
                                        ↓
Query → Embed query → Search index → Retrieve top-K → Inject into prompt → LLM generates answer
```

### Chunking Strategy

Choose the strategy that matches your document structure:

- **Fixed size**: Split every N tokens/characters with overlap. Simple, predictable. Works for homogeneous text.
- **Semantic**: Split at paragraph/section boundaries. Better coherence per chunk. Requires parsing document structure.
- **Recursive**: Split by paragraphs, then sentences, then words (LangChain's default). Balances structure and granularity.
- **Document-aware**: Respect document structure (headers, code blocks, tables as atomic units). Best for structured documents.

**Sizing**: 256–1024 tokens typical. Smaller = more precise retrieval, larger = more context per chunk. Test on your actual queries.

**Overlap**: 10–20% between chunks to preserve context at boundaries. Prevents information loss at chunk edges.

### Embedding Best Practices

- Match embedding model at index time and query time (same model, same dimensions). Mismatches degrade retrieval severely.
- Batch embed for bulk ingestion, single embed for real-time queries.
- Popular models: nomic-embed-text (768d, self-hosted), text-embedding-3-small (1536d, OpenAI API), BGE-large (1024d).
- Normalize embeddings if your vector store doesn't do it automatically.
- **Optimize representation**: Embed the whole chunk, or embed a summary/title + chunk? Test both; sometimes a short representation retrieves better.

### Retrieval Optimization

- **Top-K selection**: Start with K=5–10, tune based on LLM context window and result quality.
- **Similarity threshold**: Filter out low-relevance results (cosine similarity < 0.7) to avoid noise.
- **Hybrid search**: Combine vector similarity with keyword/BM25 search. Better for exact terms like error codes, names, product IDs.
- **Reranking**: Retrieve top-20 with vector search, rerank with cross-encoder model to top-5. More expensive but more accurate.
- **Metadata filtering**: Pre-filter by date, source, category before vector search to narrow the search space.
- **Multi-query**: Reformulate the user's question into 2–3 variations, search all, merge results. Catches different phrasings.

### Common RAG Problems and Fixes

| Problem | Root Cause | Fix |
|---------|-----------|-----|
| Returns irrelevant chunks | Embedding model mismatch, chunks too large, no metadata filtering | Try smaller chunks, add metadata filters, use hybrid search |
| Missing obvious answers | Information split across chunks (chunk boundary problem) | Increase overlap, use document-aware chunking |
| Hallucination despite having source | LLM ignoring retrieved context | Stronger system prompt ("only answer based on provided context"), citation requirements, lower temperature |
| Works for some queries, fails for others | Single retrieval strategy doesn't fit all query types | Hybrid search, multi-query, query classification |

## Tool Use / Function Calling

### Design Principles

- **One tool = one action**: search_docs, create_file, run_query. Not do_everything.
- **Descriptive names and parameters**: The LLM reads these to decide when to call. Clear descriptions prevent misuse.
- **Return structured data**: Let the LLM format for the user, not the tool.
- **Handle errors gracefully**: Return error description, don't crash the agent loop. Failing a tool call should be recoverable.
- **Idempotent where possible**: Safe to retry without side effects.

### Tool Schema Pattern

```python
tools = [{
    "name": "search_documents",
    "description": "Search the knowledge base for relevant documents. Use when the user asks about topics covered in our documentation.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Natural language search query"},
            "max_results": {"type": "integer", "description": "Maximum results to return", "default": 5}
        },
        "required": ["query"]
    }
}]
```

### Tool Categories

- **Read tools**: search, fetch, query. Safe, no side effects. Call freely.
- **Write tools**: create, update, delete. Require confirmation or guardrails.
- **Compute tools**: calculate, transform, generate. CPU/GPU intensive. Consider timeout and resource limits.
- **External tools**: API calls, web requests. Network-dependent. Need error handling and retries.

### MCP (Model Context Protocol) Integration

Standard protocol for exposing tools to LLMs. Build MCP servers to wrap any API, database, or service as LLM-callable tools.

**Client configuration**: claude_desktop_config.json, .mcp.json, or environment variables.

**Advantage**: Tools are reusable across different LLM clients and agents. Single source of truth for tool definitions.

## Context Window Management

### The Fundamental Constraint

Every LLM has a context window limit (input + output tokens). Agent conversations grow over time—you'll hit the limit. Actively manage what goes into context.

### Techniques

- **Summarization**: Periodically summarize conversation history, replace full history with summary.
- **Sliding window**: Keep last N messages, drop oldest.
- **Selective retrieval**: Don't load everything—retrieve relevant context on demand (RAG pattern).
- **Tiered memory**: Working memory (in context) → recall memory (searchable archive) → archival memory (long-term store).
- **Context budgeting**: Allocate token budget per section. Example: system prompt 500, tools 1000, history 2000, retrieval 2000, generation 2000.

### Prompt Structure

```
[System prompt: who you are, what you do, rules]
[Tool definitions]
[Retrieved context / RAG results]
[Conversation history (compressed)]
[User's current message]
→ [Agent's response]
```

Monitor token usage at each section. Prioritize keeping recent history and retrieved context; compress/drop old history.

## Structured Output

### Why Structured Output

- Agents need to produce parseable data (not just text) for downstream processing.
- Tool calls need structured arguments.
- Data extraction needs consistent format.

### Techniques

- **JSON mode**: Request JSON output, parse response. Works with modern LLMs like Claude 3.5.
- **Schema-constrained generation**: Provide JSON schema, model outputs conforming JSON.
- **XML tags**: `<answer>`, `<reasoning>`. Reliable with Claude, easy to parse.
- **Pydantic models**: Define output schema in Python, validate response against it.

**Always validate**: Even with structured output mode, verify the schema is correct. Parsing failures still happen.

## Guardrails

### Input Guardrails

- **Content filtering**: Reject harmful/off-topic requests before they reach the agent.
- **Input validation**: Check length limits, format requirements.
- **Injection detection**: Watch for prompt injection attempts in user input.
- **Rate limiting**: Prevent abuse.

### Output Guardrails

- **Hallucination check**: Verify claims against retrieved sources. Citation enforcement: require specific source references.
- **Safety filtering**: Scan output for harmful content before returning to user.
- **Format validation**: Ensure structured output matches expected schema.
- **Boundary enforcement**: Agent shouldn't access tools/data outside its authorized scope.

### Agent Loop Safety

- **Maximum iterations**: Cap the number of tool calls per turn. Prevent infinite loops.
- **Budget limits**: Track token usage per conversation, enforce spending limits.
- **Timeout**: Kill agent loops that exceed time limits (e.g., 30 seconds).
- **Human-in-the-loop**: Require approval for high-impact actions (write, delete, send).

## Evaluation

### What to Evaluate

- **Retrieval quality** (RAG): Are the right documents being retrieved? Metrics: precision@K, recall@K, MRR, NDCG.
- **Answer quality**: Is the response correct, complete, well-formatted? Human eval or LLM-as-judge.
- **Tool use accuracy**: Does the agent call the right tools with correct arguments?
- **Task completion**: Does the agent actually accomplish the user's goal?
- **Safety**: Does the agent stay within bounds? No hallucination, no harmful output?

### Evaluation Approaches

- **Golden dataset**: Curated question-answer pairs, score agent responses against gold answers.
- **LLM-as-judge**: Use a strong model to evaluate a weaker model's outputs. Cost-effective for scale. Always verify a sample manually.
- **Human evaluation**: Most reliable but expensive. Use for spot-checking and calibrating automated evals.
- **A/B testing**: Compare two agent versions on real traffic, measure user satisfaction or task completion rate.

### Evaluation Framework Pattern

```python
def evaluate_rag(questions, expected_answers, rag_pipeline):
    results = []
    for q, expected in zip(questions, expected_answers):
        answer, sources = rag_pipeline.query(q)
        results.append({
            "question": q,
            "answer": answer,
            "expected": expected,
            "sources": sources,
            "correct": judge_correctness(answer, expected),
            "grounded": check_grounding(answer, sources),
        })
    return aggregate_metrics(results)
```

## Production Deployment

### Observability

Log every agent step: tool calls, tool results, decisions, errors.

**Metrics to track**: Tokens used, latency per step, total cost per conversation, agent success rate, average steps per task.

**Tools**: OpenTelemetry for distributed agent systems. Build dashboards for: success rate, average steps per task, cost per task, token usage distribution.

### Error Handling

- **Tool failures**: Catch, log, let agent decide to retry or use alternative tool.
- **LLM errors**: Retry with exponential backoff for rate limits and transient errors.
- **Parsing failures**: If structured output fails to parse, ask LLM to fix its response.
- **Graceful degradation**: If agent can't complete task, explain why and suggest alternatives.

### Cost Management

- Use cheaper models for routing and simple tasks, expensive models for reasoning only.
- **Cache**: Store embeddings, cache common queries, cache tool results when safe.
- **Token budgeting**: Set per-conversation and per-user limits. Alert on spending spikes.
- **Monitor**: Track cost per conversation, identify high-cost query patterns, optimize.

## Troubleshooting

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| Agent loops forever | Missing stop condition, tool always returns same result | Max iterations, detect repeated actions |
| RAG returns garbage | Wrong embedding model, chunks too large, no relevance filtering | Profile retrieval quality, try hybrid search, add metadata filtering |
| Agent uses wrong tool | Tool descriptions are ambiguous | Clarify descriptions, add negative examples ("do NOT use this tool for...") |
| Hallucination | LLM generates facts not in context | Lower temperature, stronger grounding prompt, citation requirements |
| Context window overflow | Conversation too long | Implement summarization, sliding window, or context budgeting |
| High latency | Too many sequential tool calls | Parallelize independent tool calls, cache common lookups, use faster model |
