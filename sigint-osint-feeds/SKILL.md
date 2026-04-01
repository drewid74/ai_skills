---
name: sigint-osint-feeds
description: "Use this when: track aircraft in real time, monitor vessel positions, build situational awareness dashboard, my OSINT pipeline is broken, ingest threat feeds, set up geospatial alerts, correlate events across sources, detect tracking anomalies, monitor radio frequencies, ingest ADS-B data, track vessels with AIS, ingest APRS feeds, build real-time data pipeline, set up feed ingestion, alert on anomalous behavior, dedup high-volume feeds, watch for entity patterns, spatial correlation of events"
---

# SIGINT/OSINT Feed Pipelines

## Identity
You are a data pipeline architect for open-source and signals intelligence. Build decoupled, fault-tolerant ingestion systems where each source fails independently. Never block the event bus with synchronous processing.

## Stack Defaults

| Layer | Choice | Why |
|-------|--------|-----|
| Event bus | Redis Streams | Durable replay, consumer groups, <1ms publish latency |
| Geospatial DB | PostgreSQL + PostGIS (geography type) | Accurate Earth-surface distance; GIST index for spatial queries |
| Semantic search | pgvector (ivfflat index) | Article dedup and anomaly detection without separate service |
| Graph store | FalkorDB / Neo4j | Entity relationship traversal across sources |
| Object store | MinIO / S3 | Raw RF captures, PDFs, satellite imagery |
| RF decode | rtl_433 (Docker) | ISM band decoding; weather stations, sensors, 433 MHz |
| Visualization | MapLibre GL JS + WebSocket | Per-source layer toggles; real-time position updates |
| Deduplication | Bloom filter (pybloom_live) | O(1) check; 40–60% DB write reduction on high-volume feeds |

## Decision Framework

### Worker Architecture
- If source is streaming (APRS-IS TCP) → persistent async TCP worker, no polling
- If source is REST API (OpenSky, USGS, GDELT) → polling worker with per-source interval
- If source requires JS rendering (SPAs) → FlareSolverr proxy before archival
- Default → async worker, exponential backoff on failure, publish to Redis Stream

### Polling Intervals
- If breaking news / safety-critical (NOAA alerts, USGS M5+) → 5 minutes
- If operational tracking (ADS-B, AIS, APRS) → 60 seconds or streaming
- If contextual enrichment (GDELT, RSS blogs) → 15–60 minutes
- Default → 15 minutes; log lag metric to detect drift

### Correlation Engine
- If same callsign / MMSI / ICAO appears across 2+ sources → entity link, raise confidence
- If event within 10 km AND 2-hour window of another source event → spatial correlation alert
- If anomaly detected (vessel speed > 50kts, ADS-B gap > 30 min on active flight) → anomaly queue
- Default → store normalized event, mark `processed = FALSE`, consume downstream

### Storage Partitioning
- If daily event volume > 1M rows → partition by month (`PARTITION OF events FOR VALUES FROM ...`)
- If vector similarity needed → `ALTER TABLE articles ADD COLUMN embedding vector(1536)` + ivfflat
- Default → single events table with GIST index on geom column

## Anti-Patterns

| Don't | Why | Do Instead |
|-------|-----|------------|
| Poll all sources at same interval | Thundering herd; API bans | Stagger intervals; add `hash(feed_name) % 10` jitter seconds |
| Store raw payloads only | Can't query or correlate efficiently | Normalize to common schema (source, timestamp, geom, id, raw JSONB) |
| Use geometry instead of geography type | Inaccurate distances on Earth surface | Always use `GEOGRAPHY(POINT)` for lat/lon data |
| Block the event bus with NLP processing | Ingestion stalls when NER is slow | Publish raw events to stream; consume and enrich asynchronously |
| Skip spatial index | Full table scan on every geo query | `CREATE INDEX ON events USING GIST(geom)` at table creation |
| Ingest CTI feeds without STIX normalization | No interoperability with OpenCTI/MISP | Normalize all IOCs to STIX 2.1 before storage |

## Quality Gates
- [ ] Each worker has independent error handling — one feed failure does not crash others
- [ ] All geo data stored as `GEOGRAPHY(POINT, 4326)` with GIST index present
- [ ] Redis Stream consumer lag monitored; alert if lag > 1000 messages
- [ ] Deduplication applied at ingestion (bloom filter or `ON CONFLICT DO UPDATE`)
- [ ] Correlation alerts include source list, confidence score, and bounding geometry
- [ ] Dashboard layers are toggleable per source with real-time WebSocket updates

## Reference

```
Worker loop:  fetch() → normalize() → redis.xadd(stream) → sleep(interval + jitter)
APRS-IS:      rotate.aprs2.net:10152  filter: r/LAT/LON/RADIUS_KM
ADS-B:        OpenSky (60s auth) → ADS-B Exchange → local readsb (failover)
USGS:         earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson
NOAA:         api.weather.gov/alerts/active?point=LAT,LON  (5-min poll)
GDELT:        api.gdeltproject.org/api/v2/doc?query=TERM  (15-min poll)
TLE:          celestrak.com or space-track.org  (refresh every 6–12h)
```
