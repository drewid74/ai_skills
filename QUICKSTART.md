# Quick Start: LiteLLMEmbedder for FalkorDB

## 5-Minute Setup

### 1. Create config/embedding.yaml

```yaml
llm:
  use: "openai"
  openai:
    - api_key: "${OPENAI_API_KEY}"
      api_base: "https://api.openai.com/v1/embeddings"
      model: "text-embedding-3-small"
      rate_limit: 10
```

### 2. Set environment variable

```bash
export OPENAI_API_KEY="sk-..."
```

### 3. Python code

```python
from goldenmatch.core.litellm_embedder import create_litellm_embedder

# Create embedder
embedder = create_litellm_embedder(
    config_path="config/embedding.yaml",
    dimensions=256,
    cache_dir=".cache/embeddings"
)

# Embed text
embedding = embedder.embed("Hello, world!")
print(f"Shape: {embedding.shape}")  # (256,)

# Batch embed
embeddings = embedder.embed_batch(["text1", "text2", "text3"])
print(f"Shape: {embeddings.shape}")  # (3, 256)
```

## With FalkorDB

```python
from falkordb import FalkorDB
from falkordb.graphrag import GraphRAG

# Connect to FalkorDB
db = FalkorDB(host="172.16.8.13", port=6379)

# Create GraphRAG with embedder
graphrag = GraphRAG(
    db=db,
    embedder=embedder,
    schema={
        "entities": {
            "Person": {"properties": ["name", "description"]},
        },
        "relationships": {
            "KNOWS": {"from": "Person", "to": "Person"},
        }
    }
)

# Ingest data
graphrag.apply_changes({
    "entities": [
        {"id": "p1", "type": "Person", "name": "Alice", "description": "Engineer"},
        {"id": "p2", "type": "Person", "name": "Bob", "description": "Manager"},
    ],
    "relationships": [
        {"from": "p1", "to": "p2", "type": "KNOWS"},
    ]
})

# Query
results = graphrag.query("Engineer", top_k=5)
for r in results:
    print(f"{r['entity']}: {r['score']:.3f}")
```

## Key Points

- **Dimensions:** 256-dim embeddings (configurable)
- **Caching:** In-memory + disk (optional)
- **Async:** Parallel batch processing supported
- **Multi-provider:** OpenAI, Vertex, Voyage, etc.
- **Rate limiting:** Built-in via ParallelLLM

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "No available LLM clients" | Check API key in config/embedding.yaml |
| Slow embedding | Enable caching: `cache_dir=".cache/embeddings"` |
| FalkorDB connection refused | Verify 172.16.8.13:6379 is reachable |
| Dimension mismatch | Model may not support dimension reduction |

## Files

- **Implementation:** `goldenmatch/packages/python/goldenmatch/goldenmatch/core/litellm_embedder.py`
- **Example:** `goldenmatch/packages/python/goldenmatch/examples/litellm_embedder_example.py`
- **Full Guide:** `FALKORDB_INTEGRATION_GUIDE.md`
- **Summary:** `LITELLM_EMBEDDER_SUMMARY.md`
