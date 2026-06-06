---
name: sigint-osint-feeds
description: >-
  Ingest, fuse, and analyze RF/SIGINT and OSINT data streams. Build
  ingestion workers, normalize feeds into PostGIS/pgvector schemas, stream
  events through Redis Streams, and query fused intelligence. Sources: APRS,
  ADS-B, AIS, GDELT, RSS threat intel, SDR.
triggers:
  - "ingest APRS/ADS-B/AIS feeds"
  - "build OSINT pipeline"
  - "correlate RF and OSINT signals"
  - "set up threat intel ingestion"
  - "query fused intelligence data"
  - "GDELT news correlation"
  - "SDR signal recording pipeline"
tags: [sigint, osint, feeds, postgis, redis-streams, pgvector, adsb, aprs, ais]
author: merged
---

# SIGINT / OSINT Feed Fusion

## Identity

Build pipelines that ingest, normalize, and correlate real-world data streams. Default to idempotent workers. Never store raw feed blobs without parsed schema. Every feed must have a deduplication key.

## Stack Defaults

| Component | Default | Notes |
|-----------|---------|-------|
| Ingest queue | Redis Streams | XADD/XREADGROUP pattern |
| Geo storage | PostGIS | geometry(Point, 4326) |
| Vector search | pgvector | 1536-dim cosine similarity |
| APRS | aprslib | pyaprs parser |
| ADS-B | dump1090 → JSON | tcp://localhost:30002 |
| AIS | ais library | NMEA sentence decode |
| GDELT | GKG CSV HTTP | daily/15-min updates |
| Threat intel | MISP/OTX feeds | TAXII or REST pull |

## Decision Framework

```
IF feed is positional (APRS/ADS-B/AIS):
  → normalize to geometry(Point, 4326) + timestamp + callsign/mmsi
  → store in PostGIS, index GIST
ELIF feed is text/intelligence (GDELT/RSS/OTX):
  → embed with sentence-transformers
  → store vector in pgvector, metadata in jsonb
  → deduplicate on url_hash or event_id
IF stream needs real-time consumer:
  → Redis Streams XREADGROUP with consumer group
  → worker ACKs only on successful DB write
IF cross-feed correlation needed:
  → PostGIS ST_DWithin for spatial joins
  → pgvector <=> cosine for semantic correlation
  → time window: ±15 min for same-area events
```

## Anti-Patterns

| Anti-Pattern | Use Instead |
|--------------|-------------|
| Store raw NMEA/JSON without parse | Parse at ingest, schema-on-write |
| No dedup key on feeds | Always define unique constraint (callsign+ts, url_hash) |
| Polling sleep loops | Redis Streams BLOCK timeout or event-driven |
| Mixing coordinate systems | Always WGS-84 (SRID 4326) in PostGIS |
| Unbounded stream backlogs | Set MAXLEN on XADD; trim aged streams |
| Single worker for multi-source | One consumer group per feed type |

## Quality Gates

- [ ] Each feed worker has dedup key enforced at DB constraint level
- [ ] PostGIS geometry columns indexed with GIST
- [ ] Redis Streams consumer groups handle NACK/retry
- [ ] pgvector indexes created (ivfflat or hnsw) before bulk load
- [ ] All timestamps stored as UTC timestamptz
- [ ] Worker crashes do not lose messages (pending entry list recovery)

→ See `truenas-ops` for ZFS dataset layout for raw feed archives  
→ See `docker-selfhost` for compose networking between ingest workers and DB

---

## Feed Sources Reference

| Source | Protocol | Data | Update Rate |
|--------|----------|------|-------------|
| APRS | APRS-IS TCP | Position, weather, messages | Real-time |
| ADS-B | dump1090 SBS1 | Aircraft position, alt, speed | ~1s |
| AIS | NMEA over TCP/serial | Vessel position, MMSI | ~10s |
| GDELT GKG | HTTP CSV | News events, themes, actors | 15-min |
| OTX AlienVault | REST | IoC, threat actors | Hourly |
| MISP | TAXII 2.1 | Structured threat intel | Push/pull |
| RSS/Atom | HTTP | Arbitrary news/blog | Configurable |

## PostGIS Schema

```sql
-- Positional feeds (unified table)
CREATE TABLE positions (
  id          BIGSERIAL PRIMARY KEY,
  feed_type   TEXT NOT NULL,           -- 'aprs', 'adsb', 'ais'
  callsign    TEXT,                    -- APRS/ADS-B
  mmsi        TEXT,                    -- AIS vessel identifier
  location    geometry(Point, 4326) NOT NULL,
  altitude_m  REAL,
  speed_kts   REAL,
  heading_deg SMALLINT,
  raw_payload JSONB,
  ingested_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ON positions USING GIST(location);
CREATE INDEX ON positions (feed_type, ingested_at DESC);
CREATE UNIQUE INDEX ON positions (feed_type, callsign, ingested_at)
  WHERE callsign IS NOT NULL;

-- Intelligence feeds (text + vector)
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE intel_events (
  id          BIGSERIAL PRIMARY KEY,
  source      TEXT NOT NULL,           -- 'gdelt', 'otx', 'rss'
  url_hash    TEXT UNIQUE NOT NULL,
  title       TEXT,
  body        TEXT,
  actors      TEXT[],
  themes      TEXT[],
  location    geometry(Point, 4326),
  embedding   vector(1536),
  raw_payload JSONB,
  published_at TIMESTAMPTZ,
  ingested_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ON intel_events USING GIST(location);
CREATE INDEX ON intel_events USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
```

## Redis Streams Worker Architecture

```python
import redis
import json
import logging
from datetime import datetime, timezone

r = redis.Redis(host="redis", port=6379, decode_responses=True)
logger = logging.getLogger(__name__)

STREAM_KEY = "feeds:adsb"
GROUP = "adsb-workers"
CONSUMER = "worker-1"

# Create group (idempotent)
try:
    r.xgroup_create(STREAM_KEY, GROUP, id="0", mkstream=True)
except redis.exceptions.ResponseError as e:
    if "BUSYGROUP" not in str(e):
        raise

def process_adsb_message(msg_id: str, data: dict):
    """Parse ADS-B message and upsert to PostGIS."""
    from db import get_session, Position
    from geoalchemy2.shape import from_shape
    from shapely.geometry import Point

    lat = float(data.get("lat", 0))
    lon = float(data.get("lon", 0))
    if not lat or not lon:
        return  # Skip messages without position

    with get_session() as session:
        pos = Position(
            feed_type="adsb",
            callsign=data.get("hex", "").upper(),
            location=from_shape(Point(lon, lat), srid=4326),
            altitude_m=float(data.get("altitude", 0)) * 0.3048,
            speed_kts=float(data.get("speed", 0)),
            heading_deg=int(data.get("track", 0)),
            raw_payload=data,
            ingested_at=datetime.now(timezone.utc)
        )
        session.merge(pos)
        session.commit()

def run_worker():
    """Main loop: read from Redis Streams with consumer group."""
    while True:
        try:
            messages = r.xreadgroup(
                GROUP, CONSUMER, {STREAM_KEY: ">"},
                count=100, block=5000  # Block 5s if empty
            )
            for stream, entries in (messages or []):
                for msg_id, data in entries:
                    try:
                        process_adsb_message(msg_id, data)
                        r.xack(STREAM_KEY, GROUP, msg_id)  # ACK only on success
                    except Exception as e:
                        logger.error(f"Failed to process {msg_id}: {e}")
                        # Leave in pending; retry logic handles it
        except Exception as e:
            logger.error(f"Worker error: {e}")
```

## APRS Ingest Worker

```python
import aprslib
import redis
import json

r = redis.Redis(host="redis", port=6379)

def ingest_aprs(packet: dict):
    """Push APRS packet to Redis Stream."""
    if "latitude" not in packet or "longitude" not in packet:
        return
    r.xadd("feeds:aprs", {
        "callsign": packet.get("from", ""),
        "lat": str(packet["latitude"]),
        "lon": str(packet["longitude"]),
        "symbol": packet.get("symbol", ""),
        "comment": packet.get("comment", ""),
        "ts": str(packet.get("timestamp", "")),
    }, maxlen=100_000)

AIS = aprslib.IS("N0CALL", passwd="-1", host="rotate.aprs2.net", port=14580)
AIS.connect()
AIS.consumer(ingest_aprs, raw=False)
```

## GDELT Ingest (GKG)

```python
import httpx
import csv
import hashlib
import io
from datetime import datetime, timezone

GDELT_GKG_URL = "https://data.gdeltproject.org/gdeltv2/{ts}15.gkg.csv.zip"

async def fetch_gdelt_gkg(dt: datetime) -> list[dict]:
    """Fetch 15-minute GDELT GKG chunk."""
    url = GDELT_GKG_URL.format(ts=dt.strftime("%Y%m%d%H%M"))
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=30)
        resp.raise_for_status()

    import zipfile
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        fname = zf.namelist()[0]
        with zf.open(fname) as f:
            reader = csv.DictReader(io.TextIOWrapper(f), delimiter="\t")
            events = []
            for row in reader:
                url_hash = hashlib.sha256(
                    row.get("DocumentIdentifier", "").encode()
                ).hexdigest()[:16]
                events.append({
                    "source": "gdelt",
                    "url_hash": url_hash,
                    "title": row.get("Extras", "")[:500],
                    "actors": row.get("AllNames", "").split(";")[:10],
                    "themes": row.get("Themes", "").split(";")[:20],
                    "published_at": datetime.now(timezone.utc).isoformat(),
                })
    return events
```

## Spatial Correlation Query

```sql
-- Find intel events within 50km of an ADS-B position in last 30 minutes
SELECT
  i.title,
  i.source,
  ST_Distance(
    i.location::geography,
    p.location::geography
  ) / 1000 AS distance_km,
  i.published_at
FROM intel_events i
CROSS JOIN LATERAL (
  SELECT location
  FROM positions
  WHERE feed_type = 'adsb'
    AND ingested_at > NOW() - INTERVAL '30 minutes'
  ORDER BY location <-> i.location
  LIMIT 1
) p
WHERE ST_DWithin(i.location::geography, p.location::geography, 50000)
  AND i.ingested_at > NOW() - INTERVAL '2 hours'
ORDER BY distance_km ASC;
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Worker hangs, no messages | Consumer group pending list full | Run `XPENDING` check; claim stale messages with `XCLAIM` |
| PostGIS insert slow | Missing GIST index | `CREATE INDEX CONCURRENTLY ON positions USING GIST(location)` |
| APRS worker disconnects | APRS-IS keepalive timeout | Re-connect in except block; use `IS.connect()` |
| Duplicate positions in DB | No unique constraint | Add `CREATE UNIQUE INDEX ON positions (feed_type, callsign, ingested_at)` |
| GDELT fetch fails | 15-min delay, file not yet available | Retry with exp backoff; GDELT lags up to 20 min |
| pgvector similarity returns noise | Vectors not normalized | Use `vector_cosine_ops`; ensure embedding model outputs L2-normalized vectors |
