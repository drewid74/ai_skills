---
name: data-engineering
description: "Use this skill whenever the user wants to process, transform, validate, clean, or pipeline data between systems. Triggers include: any mention of 'ETL', 'ELT', 'data pipeline', 'data transformation', 'data cleaning', 'data validation', 'data quality', 'pandas', 'polars', 'DataFrame', 'CSV', 'JSON', 'Parquet', 'Arrow', 'JSONL', 'Excel', 'data import', 'data export', 'data migration', 'data sync', 'batch processing', 'stream processing', 'data lake', 'data warehouse', 'dbt', 'Airflow', 'Dagster', 'Prefect', 'Luigi', 'schema validation', 'Pydantic', 'JSON Schema', 'data catalog', 'data lineage', 'deduplication', 'data normalization', 'regex parsing', 'log parsing', 'file conversion', 'bulk import', 'data enrichment', 'data profiling', or any request to move data between systems, clean messy data, transform file formats, build data pipelines, or process large datasets. Also use when the user says 'clean this data', 'convert this CSV', 'parse these logs', 'merge these files', or has any data wrangling task. If someone needs to get data from point A to point B with transformation in between, use this skill."
---

## Overview

Patterns for moving, transforming, validating, and managing data across systems. Covers file format handling, transformation libraries, pipeline orchestration, data quality, and common data engineering patterns.

## File Format Guide

When to use each format and how to work with them:

### CSV
- Universal, human-readable, every tool understands it
- Gotchas: delimiter ambiguity, quoted fields with embedded commas, encoding issues (UTF-8 vs Latin-1), no type information
- Python read: `pandas.read_csv()` or `polars.read_csv()` or `csv.DictReader()`
- Best for: data exchange, small-medium datasets, spreadsheet import/export

### JSON / JSONL
- JSON: hierarchical, typed (strings, numbers, booleans, nested objects)
- JSONL (JSON Lines): one JSON object per line — streamable, appendable
- Python: `json.loads()`, `pandas.read_json()`, or stream with `for line in file`
- Best for: API data, nested structures, configuration

### Parquet
- Columnar binary format, compressed, typed, supports nested data
- 10-100x smaller than CSV for typical data
- Blazing fast for analytical queries (read only needed columns)
- Python: `pandas.read_parquet()`, `polars.read_parquet()`, `pyarrow`
- Best for: large datasets, analytics, data lakes, long-term storage

### Apache Arrow
- In-memory columnar format, zero-copy reads between tools
- Python: `pyarrow` — shared format between pandas, polars, DuckDB
- Best for: inter-process data transfer, high-performance analytics

### Excel (.xlsx)
- Use: openpyxl (Python), SheetJS (JS), or pandas `read_excel()`
- Gotchas: mixed types in columns, merged cells, multiple sheets, formulas not data
- Best for: business data exchange, when stakeholders use Excel

### Conversion Patterns

```python
import polars as pl

# CSV → Parquet (10x compression, typed)
df = pl.read_csv("input.csv")
df.write_parquet("output.parquet")

# JSON → CSV (flatten nested)
df = pl.read_json("input.json")
df.write_csv("output.csv")

# Excel → JSONL (streaming-friendly)
df = pl.read_excel("input.xlsx")
df.write_ndjson("output.jsonl")

# Parquet → DataFrame for processing
df = pl.read_parquet("data.parquet")
```

## Data Transformation Libraries

### pandas
- De facto standard, massive ecosystem, rich API
- Great for: exploratory analysis, small-medium data (<1GB), notebooks
- Weakness: memory-hungry (loads everything into RAM), slow on large data, confusing indexing
- Key patterns: `df.groupby()`, `df.merge()`, `df.apply()`, `df.pivot_table()`, method chaining

### polars
- Modern DataFrame library, Rust-based, lazy evaluation
- 5-10x faster than pandas, constant memory usage, no index confusion
- Great for: production pipelines, large data, when pandas is too slow
- Key patterns: `df.select()`, `df.filter()`, `df.group_by()`, lazy expressions with `.lazy()` → `.collect()`
- Use polars for new projects; pandas if you have existing pandas code or need specific ecosystem integration

### DuckDB
- In-process SQL database, reads CSV/Parquet/JSON directly
- `SELECT * FROM 'data.parquet' WHERE year > 2020` — no loading step
- Great for: SQL-oriented transformation, ad-hoc analysis, combining files
- Integrates with pandas and polars DataFrames

### jq (CLI)
- JSON processor for shell pipelines
- `cat data.json | jq '.items[] | {name: .name, price: .cost}'`
- Great for: quick JSON transformation in scripts, shell one-liners

## Data Validation

### Pydantic (Python)

```python
from pydantic import BaseModel, validator, EmailStr
from datetime import datetime

class UserRecord(BaseModel):
    name: str
    email: EmailStr
    age: int
    created_at: datetime

    @validator('age')
    def age_must_be_positive(cls, v):
        if v < 0 or v > 150:
            raise ValueError('age must be between 0 and 150')
        return v

# Validate a batch
valid, invalid = [], []
for row in raw_data:
    try:
        valid.append(UserRecord(**row))
    except ValidationError as e:
        invalid.append({"row": row, "errors": e.errors()})
```

- Why validate: bad data propagates silently and breaks downstream systems
- Validate at ingestion (before it enters your pipeline)
- Log validation failures for review, don't silently drop records

### JSON Schema
- Language-agnostic schema definition for JSON data
- Validate API payloads, config files, data exchange formats
- Tools: jsonschema (Python), Ajv (JS)

### Great Expectations / Pandera
- Data quality frameworks for DataFrames
- Define expectations: "column X is never null", "column Y values are in range 0-100"
- Generate data quality reports, fail pipelines on violations

## ETL/ELT Pipeline Patterns

### ETL (Extract, Transform, Load)
```
Source → Extract raw data → Transform (clean, reshape, enrich) → Load to destination
```
- Traditional approach: transform before loading
- Use when: destination has strict schema, you need clean data in the target

### ELT (Extract, Load, Transform)
```
Source → Extract raw data → Load to warehouse → Transform in-place (SQL/dbt)
```
- Modern approach: load raw, transform with SQL in the warehouse
- Use when: target supports transformation (data warehouse, PostgreSQL), schema may evolve

### Pipeline Structure

```python
def pipeline():
    # Extract
    raw = extract_from_api(url, params)

    # Transform
    cleaned = clean_data(raw)         # Remove nulls, fix types
    enriched = enrich_data(cleaned)   # Add derived columns, lookups
    validated = validate_data(enriched) # Check constraints

    # Load
    load_to_database(validated, table="processed_data")

    # Verify
    verify_row_counts(raw, validated)  # Sanity check
```

### Idempotent Pipelines
- Running the same pipeline twice produces the same result (no duplicates, no data loss)
- Pattern: use upsert (INSERT ON CONFLICT UPDATE) instead of INSERT
- Pattern: process data for a specific date range, overwrite that range on re-run
- Pattern: track processed IDs/timestamps, skip already-processed records
- Why: pipelines fail halfway and get re-run — idempotency makes this safe

## Pipeline Orchestration

### When You Need an Orchestrator
- Multiple pipeline steps with dependencies
- Scheduled runs (daily, hourly)
- Retry on failure with alerting
- Monitoring pipeline health and duration

### Options
- **cron + scripts**: simplest, works for linear pipelines with no dependencies
- **Dagster**: modern, Python-native, great developer experience, asset-based
- **Airflow**: industry standard, DAG-based, massive ecosystem, heavier setup
- **Prefect**: Python-native, cloud-hosted option, good for medium complexity
- **dbt**: SQL-first transformation (not a general orchestrator — focused on warehouse transforms)

### dbt Pattern

```sql
-- models/staging/stg_orders.sql
SELECT
    id as order_id,
    customer_id,
    CAST(total_cents AS DECIMAL) / 100 as total_dollars,
    created_at
FROM {{ source('raw', 'orders') }}
WHERE created_at >= '2020-01-01'
```

- SQL-based transformation layer for data warehouses
- Models: SQL files that define transformations
- Tests: schema tests (not_null, unique, accepted_values, relationships)
- Documentation: auto-generated from YAML alongside models

## Data Cleaning Patterns

### Common Operations

```python
import polars as pl

df = pl.read_csv("messy_data.csv")

# Remove duplicates
df = df.unique(subset=["email"], keep="first")

# Handle nulls
df = df.with_columns([
    pl.col("name").fill_null("Unknown"),
    pl.col("age").fill_null(pl.col("age").median()),
])

# Standardize text
df = df.with_columns([
    pl.col("email").str.to_lowercase().str.strip_chars(),
    pl.col("phone").str.replace_all(r"[^\d]", ""),  # digits only
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

### Deduplication Strategies
- **Exact**: hash on all columns, keep first/last
- **Fuzzy**: Levenshtein distance, phonetic matching (Soundex, Metaphone) for names
- **Key-based**: deduplicate on business key (email, ID) regardless of other differences
- **Window-based**: deduplicate within time windows (same user, same action, within 5 minutes)

### Data Profiling
- Before transforming, understand your data: `df.describe()`, `df.null_count()`, unique counts, distribution
- Identify: data types, missing values, outliers, cardinality, patterns
- Tools: ydata-profiling (auto-generates HTML reports), polars `.describe()`

## Streaming vs Batch

### Batch Processing
- Process data in chunks on a schedule (hourly, daily)
- Simpler to build, debug, and reason about
- Use when: data doesn't need to be real-time, SLA is hours not seconds

### Stream Processing
- Process events as they arrive (sub-second latency)
- More complex: need message queue, exactly-once semantics, state management
- Tools: Kafka Streams, Flink, Redis Streams consumer groups
- Use when: real-time dashboards, alerting, event-driven architecture

### Micro-batch (Practical Middle Ground)
- Process every 1-5 minutes instead of real-time or daily
- Much simpler than true streaming, much fresher than daily batch
- Pattern: cron every 5 min → poll for new records → process → load
- Good enough for most homelab and personal project needs

## Troubleshooting

- **Memory error on large file**: use chunked reading (`chunksize` in pandas, lazy scanning in polars), or switch to DuckDB/Parquet
- **Encoding errors**: detect with `chardet`, read with correct encoding (`encoding='utf-8'` or `encoding='latin-1'`)
- **Type mismatches**: profile data first, cast explicitly, handle mixed types in columns
- **Slow pipeline**: profile bottleneck (extract? transform? load?), switch to polars/DuckDB, use Parquet
- **Duplicate data after re-run**: pipeline isn't idempotent — use upsert or date-range overwrite pattern
- **Schema drift (source changed)**: validate schema at extraction, alert on unexpected columns/types
