---
name: federated-memory
description: "Use this skill whenever the user wants to design, build, or manage memory systems for AI agents, knowledge graphs, personal knowledge bases, or federated data architectures. Triggers include: any mention of 'agent memory', 'persistent memory', 'knowledge graph', 'knowledge base', 'personal knowledge', 'digital twin', 'memory bank', 'context persistence', 'session memory', 'long-term memory', 'working memory', 'archival memory', 'MemGPT', 'Letta', 'OpenBrain', 'RAG', 'retrieval augmented generation', 'vector store', 'embedding store', 'Qdrant', 'Pinecone', 'Weaviate', 'ChromaDB', 'pgvector', 'semantic search', 'thought capture', 'brain sync', 'memory federation', 'sovereign data', 'cross-agent memory', or requests to make AI remember things across sessions, share context between agents, or build a personal second brain. Also use when the user is designing architectures where multiple AI systems need coordinated access to shared or partitioned knowledge. If someone says 'I want my AI to remember' or 'how do I persist context', use this skill."
---

# Federated Memory for AI Agents

Patterns for building persistent, federated memory systems that let AI agents maintain context across sessions, share knowledge across domains, and respect data sovereignty boundaries.

## Memory Architecture Layers

Use the three-layer model (inspired by MemGPT/Letta):

### Working Memory (Core Memory)
Active context the agent is currently using—analogous to a person's short-term/working memory.

- **Implementation**: Structured text block, key-value store, or small JSON document
- **Size**: Bounded (fits in context window, typically 2-5KB)
- **Update**: Agent edits directly during conversation
- **Persistence**: Saved at session end, restored at session start

Example:
```json
{
  "current_task": "debug database migration",
  "user_preferences": ["prefers async patterns", "likes verbose error messages"],
  "recent_context": "last session discussed pgvector performance",
  "open_questions": ["how to handle schema versioning?"]
}
```

### Recall Memory (Conversation History)
Searchable archive of past conversations. Implemented as vector store with conversation chunks.

- **Query**: Semantic search over past interactions ("what did we discuss about X last month?")
- **Retention**: Configurable (keep everything, or summarize and compress older entries)
- **Chunking**: 200-500 tokens per chunk for good semantic coherence
- **Reranking**: Optional post-filter on semantic search results to reduce noise

### Archival Memory (Knowledge Base)
Long-term structured and unstructured knowledge. The persistent brain that grows over time.

- **Implementation**: Vector store + optional graph database + optional relational DB
- **Ingestion**: Agent writes notes, external systems push data, user uploads documents
- **Query**: Semantic search, graph traversal, SQL queries depending on structure
- **Categories**: Facts, decisions, procedures, preferences, relationships

## Vector Store Selection

Pick based on your scale and infrastructure constraints:

| Store | Best For | Tradeoff |
|-------|----------|----------|
| **pgvector** | Already have PostgreSQL, <1M vectors | Slower than dedicated stores, but no extra infra |
| **Qdrant** | Large collections, production workloads | Requires separate service, but purpose-built |
| **ChromaDB** | Local development, rapid prototyping | Less mature for production, slower at scale |
| **Weaviate** | Want DB to handle vectorization | Heavier setup, multimodal support |

**Practical guidance**: Start with pgvector if you already have PostgreSQL. Migrate to Qdrant when latency matters at scale. Always store source text alongside vectors for retrieval.

**Index types matter**: IVFFlat is faster to build but lower recall; HNSW is slower to build but better recall. Start with IVFFlat, benchmark before switching.

## Embedding Models

Match dimensions to your chosen store:

- **nomic-embed-text** (768d): General-purpose, runs locally via Ollama
- **all-MiniLM-L6-v2** (384d): Fast, lightweight, good for prototyping
- **BGE-large** (1024d): High quality, production-ready RAG
- **text-embedding-3-small** (1536d): OpenAI, highest quality but API-dependent

Self-host via Ollama or dedicated inference server to avoid API latency. Batch embed for bulk ingestion, single embed for real-time. **Never re-embed after changing models**—either migrate all vectors or run both models in parallel during transition.

## Federation Model

The core pattern for multi-domain systems respecting data sovereignty:

### Sovereign Memory Banks

Each domain/project owns its memory bank with full authority over its own data.

- **Write**: Local only (no shared writes across banks)
- **Read**: Exposed to other banks via API/MCP tool
- **No shared database**: Federation happens at query layer, not storage layer
- **Why**: Data sovereignty, failure isolation, independent evolution, security

### Cross-Bank Query Pattern

```
Agent needs info from Bank B:
  1. Agent calls Bank B's read tool (MCP tool / REST API)
  2. Bank B queries its own vector store
  3. Bank B returns results to agent
  4. Agent incorporates results into working memory
  → Bank B's data never leaves Bank B's control
```

### Sync Patterns

- **Local-primary with cloud replica**: Local brain is authoritative, syncs to cloud on interval
- **Offline queue**: Queue writes locally when cloud unreachable, replay when connected
- **Conflict resolution**: Timestamp-wins for simple cases; flag conflicts for human review
- **Selective sync**: Not everything syncs. Secrets and credentials stay local only.

## Thought/Note Capture Pattern

Universal pattern for AI-assisted knowledge capture:

```python
def capture_thought(content: str, tags: list[str], source: str):
    """Store a thought with embedding for semantic retrieval."""
    embedding = embed(content)
    store.insert({
        "content": content,
        "tags": tags,
        "source": source,  # conversation, manual, automated
        "timestamp": now(),
        "embedding": embedding,
        "hash": md5(content)  # dedup: prevent re-capturing same info
    })
```

**Retrieve patterns**:
- **Semantic search**: "find notes about Docker networking" → vector similarity
- **Tag filter**: All thoughts tagged "architecture-decision"
- **Time-based**: "what did I capture this week?"
- **Combined**: Semantic + tag filter + time range

**When to capture**:
- Architecture decisions and their rationale
- Troubleshooting solutions (problem → diagnosis → fix)
- User preferences and conventions
- Project status and milestones
- Links between concepts (this relates to that)

## Graph Knowledge Patterns

Use a graph layer when relationships matter more than individual facts.

### When to add graphs

- Entities have meaningful relationships (person → works_on → project)
- Multi-hop queries needed ("who is connected to X through Y?")
- Temporal relationships matter (entity relationships change over time)

### Options

- **FalkorDB**: Redis-compatible, fast, good for homelab setups
- **Neo4j**: Most mature, best tooling, heavier infrastructure
- **PostgreSQL + Apache AGE**: Graph queries in PostgreSQL (no extra service)

### Common patterns

- People ↔ Organizations ↔ Projects
- Events → involve → Entities
- Documents → mention → Entities
- Decisions → affect → Systems

## Implementation Patterns

### MCP-based memory server

Expose memory operations as MCP tools. Agent calls tools naturally during conversation.

```javascript
// MCP tool: search_memory
{
  query: string,        // semantic query
  tags?: string[],      // filter by tags
  days?: number,        // filter by recency
  limit: number         // result count
}
// Returns: [{content, tags, timestamp, relevance_score}]
```

Clean separation: agent logic in one process, memory infrastructure in another.

### Session continuity

1. **Session start**: Load working memory + retrieve relevant archival context (semantic search for related notes)
2. **During session**: Capture important decisions/facts as they emerge
3. **Session end**: Summarize session, update working memory, archive conversation
4. **Between sessions**: Background processes enrich/link/clean memory

### Multi-agent coordination

- **Shared read access** to common knowledge base (read-only for other agents)
- **Per-agent working memory** (don't pollute other agents' context)
- **Coordination through shared archival memory**, not direct messaging
- **Domain ownership**: Agents own specific domains, write only to their domain

Example: Agent A writes "User prefers async code patterns" to Preferences knowledge bank. Agent B reads it when working on user's code.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Search returns irrelevant results | Embedding model mismatch or bad chunking | Check embedding model matches query model; try 300-token chunks instead of 200 |
| Memory grows unbounded | No retention policy | Summarize entries older than 6 months, archive to cold storage |
| Sync conflicts | Concurrent writes | Log conflicts for review; never silently overwrite |
| Slow semantic search | Wrong index type or full-table scan | Use HNSW index; pre-filter metadata before vector search |
| Agent re-captures same info | No dedup logic | Hash content before insert, check if hash exists first |
| Vector dimensions mismatch | Model swap without migration | Run both models in parallel 1 week, migrate vectors, then deprecate old model |

## Next Steps

1. **Choose your vector store** based on existing infrastructure (prefer pgvector if you have PostgreSQL)
2. **Pick embedding model** and self-host via Ollama for reliable latency
3. **Design working memory structure** specific to your agent's role
4. **Implement MCP tools** for memory read/write/search
5. **Start capturing** from day one—even basic captures compound into useful knowledge over weeks
6. **Monitor retrieval quality** and adjust chunking/embedding if search results drift
