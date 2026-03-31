---
name: sigint-osint-feeds
description: "Use this skill whenever the user wants to build, manage, or analyze open-source intelligence (OSINT) or signals intelligence (SIGINT) data pipelines. Triggers include: any mention of 'OSINT', 'SIGINT', 'open source intelligence', 'threat intelligence', 'CTI', 'APRS', 'ADS-B', 'AIS', 'flight tracking', 'ship tracking', 'vessel tracking', 'RF monitoring', 'SDR', 'RTL-SDR', 'radio scanning', 'GDELT', 'USGS', 'NOAA', 'weather alerts', 'earthquake data', 'satellite tracking', 'TLE', 'space track', 'RSS feed aggregation', 'OPML', 'feed ingestion', 'geospatial', 'PostGIS', 'situational awareness', 'common operating picture', 'COP', 'event correlation', 'NER pipeline', 'entity extraction', 'OpenCTI', 'MISP', 'STIX', 'TAXII', 'threat feed', or requests to aggregate, correlate, or visualize real-time data from public sources. Also use when the user wants to build dashboards for monitoring global events, track RF signals, or create intelligence analysis workflows. If someone says 'I want to monitor X in real-time' where X is any public data source, use this skill."
---

# OSINT/SIGINT Data Ingestion Pipelines

## Overview

Build scalable pipelines that aggregate, normalize, and correlate intelligence from public sources. This skill covers RF signals (APRS, ADS-B, AIS), geospatial events (earthquakes, weather), cyber threat intelligence, news feeds, and satellite tracking. Use this pattern when you need to ingest multiple data streams, correlate events across sources, and surface patterns to analysts.

## Why This Architecture

Separate ingestion from processing via an event bus (Redis Streams, Kafka). Each data source runs in its own worker with independent polling intervals. This decoupling lets you scale workers horizontally, survive failures gracefully, and add new sources without touching production pipelines.

## Architecture Pattern

**Worker model**: One async worker per data source, each with its own polling interval and retry logic.

**Event bus**: Redis Streams or message queue for decoupling ingestion from processing. Workers publish normalized events; processors consume and enrich.

**Storage layer**:
- PostgreSQL + PostGIS for geospatial queries and temporal data
- pgvector for semantic similarity (article deduplication, anomaly detection)
- Graph database (FalkorDB, Neo4j) for entity relationships

**Object store**: MinIO/S3 for raw artifacts (PDFs, satellite imagery, RF captures).

**Processing layer**: NER, classification, entity linking, anomaly detection downstream from ingestion.

**Presentation layer**: Web map (MapLibre/Leaflet), timeline, dashboard with real-time WebSocket updates.

## RF Signal Sources

### APRS (Automatic Packet Reporting System)

Connect to APRS-IS network for real-time position reports from ham radio operators and weather stations:

```
Connection: rotate.aprs2.net:10152 (persistent TCP)
Filter: r/40.7128/-74.0060/50  (lat/lon/radius_km)
Auth: CALLSIGN -1 passcode_hash
```

Use `aprslib` (Python) to parse packets. Data includes callsign, timestamp, lat/lon, altitude, course, speed, comment. Polling is streaming (live TCP), not periodic. Why use APRS: free, global coverage, community-maintained, includes weather stations (pressure, temperature, wind).

### ADS-B (Automatic Dependent Surveillance-Broadcast)

Track aircraft. Use local receiver (RTL-SDR 1090 MHz + dump1090/readsb) or cloud APIs:

- **OpenSky Network**: free tier (300s update interval anonymously, 60s authenticated)
- **ADS-B Exchange**: rapid API via RapidAPI, near real-time
- **Local receiver**: lowest latency, no API limits

Failover pattern: primary API → secondary API → local receiver. Data: ICAO24, callsign, lat/lon, altitude, velocity, heading, on_ground timestamp.

### AIS (Automatic Identification System)

Marine vessel tracking via VHF broadcasts (161.975/162.025 MHz):

- **AISHub**: raw AIS data feed
- **MarineTraffic API**: curated vessel data
- **Local VHF receiver**: RTL-SDR + AIS decoder

Data: MMSI, vessel name, lat/lon, course, speed, ship type, destination, callsign. Why collect: detect anomalies (unusual routes, AIS spoofing), track supply chains, monitor ports.

### RTL-SDR General

$30 hardware dongle for broadband RF monitoring:

```bash
rtl_power -f 88M:108M:100k -i 10 spectrum.csv  # scan FM band
rtl_fm -f 162.55M -M wfm -s 200k | sox ...     # demodulate weather radio
```

Use `rtl_433` Docker container for ISM band decoding (weather stations, tire pressure sensors, door locks). Useful for detecting unmonitored RF activity in an area.

## Geospatial Event Sources

### USGS Earthquakes

Real-time seismic data:

```
https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson
Poll every 5 minutes. Data: magnitude, depth, location, tsunami alert flag.
```

Correlate with GDELT (news coverage), weather alerts, and infrastructure monitoring.

### NOAA Weather Alerts

Severe weather warnings by geographic area:

```
https://api.weather.gov/alerts/active?point=40.7128,-74.0060
Filter by severity (Extreme, Severe, Moderate) and event type.
```

Polling interval: 5 minutes. Why use: structured early warning, correlation with power outages and emergency response data.

### GDELT (Global Database of Events, Language, and Tone)

Real-time event monitoring from news articles and TV transcripts:

```
https://api.gdeltproject.org/api/v2/doc?query=aviation%20accident
Modes: doc (articles), geo (geographic hotspots), timeline
```

Data: CAMEO event codes (protest, conflict, etc.), actors, locations, sentiment tone, source URLs. Polling: 15 minutes. Why use: correlate with RF signals (aircraft down → ADS-B disappearance), geopolitical context.

## News & RSS Feed Aggregation

Organize feeds via OPML files. Use tiered polling:
- Breaking news feeds: 5 minutes
- Daily news: 15 minutes
- Blogs/archives: 60 minutes

Deduplication via URL + title hash or content similarity (embeddings). Enrichment: extract named entities (NER), classify topic/severity, summarize, source attribution. Store full article text in PostgreSQL + embeddings in pgvector.

## Satellite Tracking

Track active satellites, weather satellites, Starlink, ISS:

```python
from sgp4.api import Satrec
# TLE source: space-track.org or celestrak.com
satellite = Satrec.twoline2rv(tle_line1, tle_line2)
lat, lon, alt = satellite.propagate(year, month, day, hour, min, sec)
```

Refresh TLEs every 6–12 hours. Propagate positions every 5 minutes. Why: predict passes (antenna scheduling), detect maneuvers, correlate with RF observations (amateur radio satellite windows).

## Cyber Threat Intelligence

Ingest structured threat feeds:

- **Format**: STIX (Structured Threat Information Expression)
- **Transport**: TAXII (Trusted Automated Exchange of Indicator Information)
- **Platforms**: OpenCTI, MISP for organization and sharing
- **Sources**: AlienVault OTX, Abuse.ch, VirusTotal, Shodan

Indicators: IPs, domains, file hashes, URLs, YARA rules. Pipeline: ingest → normalize to STIX → store → correlate with attack events → alert. Correlation rules: same IP across multiple feeds = higher confidence.

## Database Schema Patterns

### PostgreSQL + PostGIS

```sql
CREATE TABLE events (
  id BIGSERIAL PRIMARY KEY,
  source TEXT,                    -- 'APRS', 'ADS-B', 'USGS', etc.
  timestamp TIMESTAMPTZ,
  geom GEOGRAPHY(POINT),          -- use geography for accurate distance on Earth
  callsign_or_id TEXT,
  raw_data JSONB,                 -- full source payload
  processed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Spatial index for fast geographic queries
CREATE INDEX idx_events_geom ON events USING GIST(geom);

-- Partition by month for high-volume data
CREATE TABLE events_2026_03 PARTITION OF events
  FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');
```

Why geography type: accurate distance calculations on Earth's surface. Why partition: keep index sizes small, enables faster pruning.

### pgvector for Semantic Search

```sql
ALTER TABLE articles ADD COLUMN embedding vector(1536);
CREATE INDEX idx_embedding ON articles USING ivfflat(embedding vector_cosine_ops);

-- Find similar articles
SELECT * FROM articles
WHERE embedding <-> to_query_embedding('[...]') < 0.3
ORDER BY embedding <-> to_query_embedding('[...]')
LIMIT 10;
```

Why pgvector: detect duplicate news stories, find related articles, anomaly detection via distance from normal distribution.

### Graph Database (FalkorDB, Neo4j)

```
Node types: Person, Organization, Location, Vessel, Aircraft, IPAddress
Edge types: mentioned_in, located_at, traveled_to, associated_with, communicated_with

Query: "Find all entities connected to callsign XYZ within 2 hops"
Path: XYZ → [traveled_to] → Location → [attacked_in] → Event
```

Why graph: rapidly traverse entity relationships, detect rings and networks.

## Worker Implementation Pattern

```python
import asyncio
import aiohttp
import json
from redis import asyncio as aioredis

class OSINTWorker:
    """Template for an ingestion worker."""

    def __init__(self, name, interval_seconds, redis_stream):
        self.name = name
        self.interval = interval_seconds
        self.stream = redis_stream
        self.session = None
        self.redis = None

    async def fetch(self):
        """Override: fetch data from source. Return list of events."""
        raise NotImplementedError

    async def normalize(self, raw_event):
        """Override: transform to common schema with source, timestamp, geom."""
        return {
            "source": self.name,
            "timestamp": raw_event.get("timestamp"),
            "lat": raw_event.get("lat"),
            "lon": raw_event.get("lon"),
            "id": raw_event.get("id"),
            "raw": json.dumps(raw_event)
        }

    async def run(self):
        """Main loop: fetch → normalize → publish to Redis stream."""
        self.session = aiohttp.ClientSession()
        self.redis = await aioredis.from_url("redis://localhost")

        while True:
            try:
                events = await self.fetch()
                for event in events:
                    normalized = await self.normalize(event)
                    await self.redis.xadd(self.stream, normalized)

            except Exception as e:
                print(f"{self.name} error: {e}")

            await asyncio.sleep(self.interval)
```

Why this pattern: each worker is independent and can be scaled horizontally. Redis Streams provide durable event replay. Async I/O handles many concurrent connections.

## Correlation & Alerting

**Time-space correlation**: Events within X km and Y minutes are likely related (aircraft crash correlates with GDELT news articles within 2 hours and 10 km).

**Entity correlation**: Same callsign, MMSI, or ICAO across sources increases confidence.

**Anomaly detection**: Train baseline model on normal behavior (typical flight paths, vessel speeds). Flag deviations.

**Alert rules**: Configurable thresholds (magnitude > 5.0, severity = "Extreme", confidence > 0.8). Notify via webhook (Discord/Slack), email, or push notification.

## Visualization

Use **MapLibre GL JS** or **Leaflet** for web map UI:
- Layer per source (toggle APRS, ADS-B, earthquakes, vessels)
- Real-time updates via WebSocket
- Heatmaps for density, polylines for tracks
- Markers with popup details
- Timeline scrubber for temporal analysis
- 3D globe (CesiumJS) for satellite and global views

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Feed returns empty | API rate limit hit, auth token expired, network down | Log API status codes, implement exponential backoff, test connectivity |
| Stale data (5+ min old) | Worker crashed, Redis queue full, consumer lag | Monitor worker health, set queue size limits, track Redis stream lag |
| PostGIS query slow | Missing spatial index, EXPLAIN ANALYZE shows seq scan | `CREATE INDEX idx_geom ON events USING GIST(geom);` |
| Memory spikes | Unbounded queue, holding full dataset in memory | Implement backpressure (pause ingestion if queue > threshold), stream from database |
| Duplicate events | Hash collision or missing dedup logic | Add DISTINCT ON (source, id, timestamp) to queries or implement bloom filter at ingestion |
