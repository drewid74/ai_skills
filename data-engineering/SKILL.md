---
name: data-engineering
description: "Use this when: build a data pipeline, my pipeline is not idempotent, clean messy data, convert CSV to Parquet, my data has duplicates, validate schema at ingestion, pipeline fails on re-run, process files larger than memory, schedule a recurring job, upstream schema changed and broke my pipeline, migrate data between systems, query Parquet without loading it, deduplicate records, batch vs stream processing, DuckDB for analytics, choose an orchestrator, slow pandas pipeline"
---

# Data Engineering

## Identity
You are a data engineer. Write working pipelines, not pseudocode. Never design a pipeline without idempotency — every pipeline gets re-run.

## Stack Defaults

| Layer | Choice | Why |
|-------|--------|-----|
| DataFrame library | Polars | 5–10× faster than pandas; lazy eval; no index confusion |
| Legacy/ecosystem fit | pandas | Use when existing pandas code or specific ecosystem integration needed |
| Ad-hoc SQL on files | DuckDB | `SELECT * FROM 'file.parquet'` — no load step; fastest for analytics |
| Storage format | Parquet | 10–100× smaller than CSV; columnar; typed; fast analytics |
| Schema validation | Pydantic | Validate at ingestion; collect errors, never silently drop |
| Data quality | Great Expectations / Pandera | Define expectations as code; fail pipelines on violations |
| Orchestration (simple) | cron + scripts or Prefect | Simple pipelines don't need Airflow overhead |
| Orchestration (complex) | Dagster | Asset-based, Python-native, best developer experience |
| SQL transforms (warehouse) | dbt | SQL-first transformation layer; tests + docs included |

## Decision Framework

### Format selection
- If analytics / long-term storage → Parquet (columnar, compressed)
- If API data / nested structures → JSONL (streamable, appendable)
- If data exchange with non-engineers → CSV (universal, human-readable)
- If inter-process in-memory transfer → Apache Arrow (zero-copy)
- Default → Parquet for anything staying internal

### Library selection
- If data >1GB OR production pipeline → Polars (lazy scan, constant memory)
- If SQL-oriented transform → DuckDB (reads CSV/Parquet/JSON directly)
- If existing pandas codebase → pandas (don't rewrite what works)
- If need shell one-liners on JSON → jq
- Default → Polars for new pipelines

### Pipeline structure
- If source schema may change → validate at extract, alert on drift, never silently pass
- If pipeline can be re-run → use upsert or date-range overwrite (idempotency)
- If data >memory → chunked read (`scan_parquet` in Polars) or DuckDB query
- If need real-time (<1 min latency) → micro-batch with cron every 60s
- Default → Extract → Validate → Transform → Load → Verify row counts

### Orchestrator selection
- If 1-3 linear steps, scheduled → cron + scripts
- If complex DAG + retries + monitoring → Dagster (best DX) or Airflow (ecosystem)
- If SQL warehouse transforms → dbt (not a general orchestrator)
- Default → Dagster for anything beyond simple cron

## Anti-Patterns

| Don't | Why | Do Instead |
|-------|-----|------------|
| INSERT without conflict handling | Duplicate rows on every re-run | Upsert (`INSERT ON CONFLICT UPDATE`) or date-range overwrite |
| Load everything then validate | Bad data in DB is hard to purge | Validate at extraction boundary before any load |
| Use pandas for >1GB files | Loads all into RAM; slow; OOM | Polars lazy scan or DuckDB direct query |
| Skip schema drift detection | Source changes silently break downstream | Assert expected columns/types at extract; alert on mismatch |
| Drop validation failures silently | Data loss undetected; broken analytics | Log failures with row + errors; route to dead-letter store |

## Quality Gates
- [ ] Pipeline is idempotent: running twice produces identical output
- [ ] Schema validated at ingestion boundary with logged failures
- [ ] Row counts verified: source count ≈ destination count (accounting for intentional drops)
- [ ] Data profiled before transform: null rates, cardinality, type distributions checked
- [ ] Parquet output used for anything stored >1 day (not CSV)
- [ ] Deduplication applied on business key before load

---

## File Format Reference

| Format | Best for | Gotchas |
|--------|----------|---------|
| CSV | Data exchange, small-medium datasets | No types, delimiter ambiguity, encoding issues |
| JSONL | API data, nested structures, streaming | Verbose; must parse each line |
| Parquet | Analytics, long-term storage, large data | Binary; not human-readable |
| Arrow | In-memory inter-process transfer | Zero-copy between pandas/polars/DuckDB |
| Excel | Business exchange with stakeholders | Mixed types, merged cells, formulas not data |

```python
import polars as pl

# CSV → Parquet
pl.read_csv("input.csv").write_parquet("output.parquet")

# JSON → CSV (flatten nested)
pl.read_json("input.json").write_csv("output.csv")

# Excel → JSONL
pl.read_excel("input.xlsx").write_ndjson("output.jsonl")
```

## Transformation Patterns

```python
import polars as pl

df = pl.read_csv("messy.csv")

# Remove duplicates on business key
df = df.unique(subset=["email"], keep="first")

# Handle nulls
df = df.with_columns([
    pl.col("name").fill_null("Unknown"),
    pl.col("age").fill_null(pl.col("age").median()),
])

# Standardize text
df = df.with_columns([
    pl.col("email").str.to_lowercase().str.strip_chars(),
    pl.col("phone").str.replace_all(r"[^\d]", ""),
])

# Type coercion
df = df.with_columns([
    pl.col("date_str").str.to_datetime("%Y-%m-%d"),
    pl.col("price").cast(pl.Float64),
])

# Filter invalid rows
df = df.filter(
    (pl.col("age") > 0) & (pl.col("age") < 150) &
    pl.col("email").str.contains("@")
)
```

## Validation Pattern (Pydantic)

```python
from pydantic import BaseModel, validator, EmailStr

class UserRecord(BaseModel):
    name: str
    email: EmailStr
    age: int

    @validator('age')
    def age_range(cls, v):
        if not 0 <= v <= 150:
            raise ValueError('age out of range')
        return v

valid, invalid = [], []
for row in raw_data:
    try:
        valid.append(UserRecord(**row))
    except Exception as e:
        invalid.append({"row": row, "errors": str(e)})
# Log invalid; never silently drop
```

## Pipeline Structure

```python
def pipeline():
    raw       = extract_from_source(url)          # pull raw data
    validated = validate_schema(raw)               # pydantic / pandera
    cleaned   = transform(validated)               # dedupe, type-cast, nulls
    load_upsert(cleaned, table="processed_data")   # idempotent write
    verify_counts(raw, cleaned)                    # sanity check
```

**Idempotency patterns:**
- `INSERT ON CONFLICT UPDATE` (upsert) instead of plain INSERT
- Date-range overwrite: reprocess a window, replace that slice
- Track processed IDs/timestamps; skip already-processed records

## Orchestration Comparison

| Tool | Use when | Key feature |
|------|----------|-------------|
| cron + scripts | 1–3 linear steps | Zero overhead |
| Prefect | Medium complexity, cloud option | Python-native, easy retries |
| Dagster | Complex DAGs, best DX | Asset-based, lineage tracking |
| Airflow | Enterprise, large ecosystem | Battle-tested, heavy setup |
| dbt | SQL warehouse transforms only | SQL-first, tests + docs |

## Batch vs Stream vs Micro-batch

- **Batch** — process on schedule (hourly/daily). Simple, debuggable. Use for SLA in hours.
- **Micro-batch** — cron every 1–5 min. Much simpler than true streaming. Good enough for most homelab needs.
- **Stream** — sub-second latency, Kafka Streams / Flink / Redis consumer groups. Use only when batch latency is genuinely unacceptable.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Memory error on large file | Polars lazy scan (`scan_parquet`) or DuckDB direct query |
| Encoding errors | Detect with `chardet`; read with `encoding='utf-8'` or `'latin-1'` |
| Duplicate data after re-run | Pipeline not idempotent — add upsert or date-range overwrite |
| Slow pipeline | Profile bottleneck; switch to Polars/DuckDB; use Parquet |
| Schema drift | Validate at extract; alert on unexpected columns/types |
