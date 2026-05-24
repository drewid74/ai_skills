# FalkorDB GraphRAG-SDK Integration Guide

## Overview

This guide explains how to integrate FalkorDB GraphRAG-SDK with the existing LiteLLM router infrastructure for Panopticon Phase 3.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ FalkorDB GraphRAG-SDK                                       │
│ ├─ Schema/Ontology Definition                              │
│ ├─ Ingestion Pipeline (apply_changes)                      │
│ └─ Query/Retrieval Interface                               │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ LiteLLMEmbedder (goldenmatch.core.litellm_embedder)        │
│ ├─ Wraps ParallelLLM Client                                │
│ ├─ Supports dimension reduction (256-dim)                  │
│ ├─ Caching (in-memory + disk)                              │
│ └─ Batch processing (async/sync)                           │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ ParallelLLM Client (GER-LLM/ParallelLLM)                   │
│ ├─ LoadBalancer (multi-provider routing)                   │
│ ├─ Rate limiting & quota tracking                          │
│ ├─ Retry policies (fixed, infinite)                        │
│ └─ Health checks                                           │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Embedding APIs (OpenAI, Vertex, Voyage, etc.)              │
│ └─ text-embedding-3-small (1536 → 256 dims)               │
└─────────────────────────────────────────────────────────────┘
```

## Setup Steps

### 1. ParallelLLM Configuration

Create `config/embedding.yaml`:

```yaml
llm:
  use: "openai"
  openai:
    - api_key: "${OPENAI_API_KEY}"
      api_base: "https://api.openai.com/v1/embeddings"
      model: "text-embedding-3-small"
      rate_limit: 10
      quota: 1000000  # tokens

# Alternative: Multiple providers
llm:
  use: "openai,vertex"
  openai:
    - api_key: "${OPENAI_API_KEY}"
      api_base: "https://api.openai.com/v1/embeddings"
      model: "text-embedding-3-small"
      rate_limit: 10
  vertex:
    - api_key: "${VERTEX_API_KEY}"
      api_base: "https://us-central1-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/us-central1/publishers/google/models/text-embedding-004:predict"
      model: "text-embedding-004"
      rate_limit: 5
```

### 2. Initialize LiteLLMEmbedder

```python
from goldenmatch.core.litellm_embedder import create_litellm_embedder

# Create embedder with 256-dimensional output
embedder = create_litellm_embedder(
    config_path="config/embedding.yaml",
    dimensions=256,
    cache_dir=".cache/embeddings"
)
```

### 3. FalkorDB GraphRAG-SDK Setup

```python
from falkordb import FalkorDB
from falkordb.graphrag import GraphRAG

# Connect to FalkorDB instance
db = FalkorDB(host="172.16.8.13", port=6379)

# Initialize GraphRAG with LiteLLMEmbedder
graphrag = GraphRAG(
    db=db,
    embedder=embedder,  # Pass LiteLLMEmbedder instance
    schema={
        "entities": {
            "Person": {"properties": ["name", "description"]},
            "Organization": {"properties": ["name", "industry"]},
            "Location": {"properties": ["name", "coordinates"]},
        },
        "relationships": {
            "WORKS_AT": {"from": "Person", "to": "Organization"},
            "LOCATED_IN": {"from": "Organization", "to": "Location"},
        }
    }
)
```

### 4. Ingestion Pipeline

```python
# Define entities and relationships
entities = [
    {"id": "person_1", "type": "Person", "name": "Alice", "description": "AI researcher"},
    {"id": "org_1", "type": "Organization", "name": "TechCorp", "industry": "AI"},
    {"id": "loc_1", "type": "Location", "name": "San Francisco", "coordinates": [-122.4, 37.8]},
]

relationships = [
    {"from": "person_1", "to": "org_1", "type": "WORKS_AT"},
    {"from": "org_1", "to": "loc_1", "type": "LOCATED_IN"},
]

# Ingest into GraphRAG
changes = {
    "entities": entities,
    "relationships": relationships
}

graphrag.apply_changes(changes)
```

### 5. Query/Retrieval

```python
# Vector similarity search
results = graphrag.query(
    query="AI researcher in San Francisco",
    top_k=5,
    similarity_threshold=0.7
)

# Graph traversal
for result in results:
    print(f"Entity: {result['entity']}")
    print(f"Similarity: {result['score']}")
    print(f"Context: {result['context']}")
```

## Key Integration Points

### Dimension Handling

**OpenAI text-embedding-3-small:**
- Default: 1536 dimensions
- Reduced: 256 dimensions (via `dimensions` parameter)
- Server-side reduction (no quality loss)

**Vertex AI text-embedding-004:**
- Default: 768 dimensions
- Supports dimension reduction via API

**Voyage AI:**
- Default: 1024 dimensions
- Supports dimension reduction

**LiteLLMEmbedder automatically passes `dimensions` to the API:**

```python
# In _call_embedding_api (balancer.py), dimensions is passed through:
request_params = {
    "model": client.config['model'],
    "input": input_text,
    "encoding_format": kwargs.get('encoding_format', 'float'),
    "dimensions": kwargs.get('dimensions')  # ← Automatically included
}
```

### Caching Strategy

**In-memory cache:**
- Keyed by SHA256(text)
- Cleared on `embedder.clear_cache()`
- Fast for repeated texts

**Disk cache:**
- Stored as `.npy` files in `cache_dir`
- Survives process restarts
- Useful for large datasets

**Usage:**

```python
embedder = create_litellm_embedder(
    config_path="config/embedding.yaml",
    dimensions=256,
    cache_dir=".cache/embeddings"  # Enable disk caching
)

# First call: hits API, caches result
emb1 = embedder.embed("text")

# Second call: hits in-memory cache
emb2 = embedder.embed("text")

# After restart: hits disk cache
emb3 = embedder.embed("text")
```

### Batch Processing

**Synchronous (blocking):**

```python
texts = ["text1", "text2", "text3"]
embeddings = embedder.embed_batch(texts)  # shape: (3, 256)
```

**Asynchronous (parallel):**

```python
import asyncio

async def process():
    embeddings = await embedder.embed_batch_async(texts)
    return embeddings

embeddings = asyncio.run(process())
```

**For FalkorDB ingestion:**

```python
# Embed all entity descriptions in parallel
descriptions = [e["description"] for e in entities]
embeddings = embedder.embed_batch(descriptions)

# Attach embeddings to entities
for entity, embedding in zip(entities, embeddings):
    entity["embedding"] = embedding.tolist()

graphrag.apply_changes({"entities": entities})
```

## Configuration Examples

### Single Provider (OpenAI)

```yaml
llm:
  use: "openai"
  openai:
    - api_key: "${OPENAI_API_KEY}"
      api_base: "https://api.openai.com/v1/embeddings"
      model: "text-embedding-3-small"
      rate_limit: 10
```

### Multi-Provider Failover

```yaml
llm:
  use: "openai,vertex"
  openai:
    - api_key: "${OPENAI_API_KEY}"
      api_base: "https://api.openai.com/v1/embeddings"
      model: "text-embedding-3-small"
      rate_limit: 10
  vertex:
    - api_key: "${VERTEX_API_KEY}"
      api_base: "https://us-central1-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/us-central1/publishers/google/models/text-embedding-004:predict"
      model: "text-embedding-004"
      rate_limit: 5
```

### Multiple Keys per Provider (Load Balancing)

```yaml
llm:
  use: "openai"
  openai:
    - api_key: "${OPENAI_API_KEY_1}"
      api_base: "https://api.openai.com/v1/embeddings"
      model: "text-embedding-3-small"
      rate_limit: 10
    - api_key: "${OPENAI_API_KEY_2}"
      api_base: "https://api.openai.com/v1/embeddings"
      model: "text-embedding-3-small"
      rate_limit: 10
```

## Monitoring & Debugging

### Get Embedder Stats

```python
stats = embedder.get_stats()
print(stats)
# Output:
# {
#     "cache_size": 42,
#     "cache_dir": ".cache/embeddings",
#     "dimensions": 256,
#     "config_path": "config/embedding.yaml",
#     "api_stats": {
#         "openai": [
#             {
#                 "id": 0,
#                 "active": True,
#                 "error_count": 0,
#                 "total_requests": 150,
#                 "total_tokens": 45000
#             }
#         ]
#     }
# }
```

### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
embedder = create_litellm_embedder(
    config_path="config/embedding.yaml",
    dimensions=256,
    log_level=logging.DEBUG
)
```

### Check FalkorDB Connection

```python
from falkordb import FalkorDB

db = FalkorDB(host="172.16.8.13", port=6379)
info = db.info()
print(f"FalkorDB version: {info['version']}")
print(f"Connected: {info['connected']}")
```

## Troubleshooting

### Issue: "No available LLM clients"

**Cause:** All clients are rate-limited or inactive.

**Solution:**
1. Check API keys in `config/embedding.yaml`
2. Verify rate limits are not too strict
3. Check API quota usage: `embedder.get_stats()['api_stats']`

### Issue: Dimension mismatch

**Cause:** Model doesn't support dimension reduction.

**Solution:**
1. Check model supports `dimensions` parameter (OpenAI text-embedding-3+, Vertex, Voyage)
2. Remove `dimensions` parameter for models that don't support it
3. Post-process embeddings locally if needed

### Issue: Slow embedding performance

**Cause:** No caching enabled.

**Solution:**
1. Enable disk caching: `cache_dir=".cache/embeddings"`
2. Use batch processing: `embed_batch()` instead of individual calls
3. Increase rate limits if API allows

### Issue: FalkorDB connection refused

**Cause:** FalkorDB instance not running or wrong host/port.

**Solution:**
1. Verify FalkorDB is running: `redis-cli -h 172.16.8.13 ping`
2. Check firewall rules
3. Verify credentials if authentication is enabled

## Next Steps

1. **Schema Design:** Define 7-tier ontology for Panopticon
2. **Data Ingestion:** Prepare entity/relationship data
3. **Query Optimization:** Tune similarity thresholds and top-k values
4. **Performance Testing:** Benchmark embedding latency and throughput
5. **Production Deployment:** Set up monitoring and alerting

## References

- **ParallelLLM:** `C:\Users\afair\dev\ai_skills\GER-LLM\ParallelLLM\`
- **LiteLLMEmbedder:** `C:\Users\afair\dev\ai_skills\goldenmatch\packages\python\goldenmatch\goldenmatch\core\litellm_embedder.py`
- **Example:** `C:\Users\afair\dev\ai_skills\goldenmatch\packages\python\goldenmatch\examples\litellm_embedder_example.py`
- **FalkorDB Docs:** https://docs.falkordb.com/
- **GraphRAG-SDK:** https://github.com/FalkorDB/GraphRAG-SDK
