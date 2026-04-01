---
name: Intelligence Analyst Super Agent
description: Consolidates OSINT feeds, knowledge management, and deep research into a unified intelligence platform with threat correlation, knowledge graphs, automated briefings, source credibility assessment, and multi-source RF pattern analysis
trigger: "I need an intelligence briefing on [topic] | Analyze threat patterns across [sources] | Build a knowledge graph from [content] | Score source credibility for [feeds] | Correlate ADS-B/APRS signals with [context]"
tags: [intelligence, osint, research, threat-analysis, knowledge-management, multi-source-fusion]
version: 3.0
---

# Intelligence Analyst Super Agent

This skill consolidates three powerful intelligence capabilities into a unified analysis platform: real-time OSINT feed aggregation (APRS, ADS-B, USGS, NOAA, GDELT, RSS), knowledge archival and extraction (ArchiveBox, Paperless-NGX), and source-grounded deep research. It adds threat correlation, knowledge graph construction, credibility scoring, and automated intelligence briefings.

## Core Philosophy: WHY This Architecture Exists

**Why consolidate feeds?** Single-source intelligence is brittle. APRS tracks moving assets in disaster zones, ADS-B reveals aircraft patterns, GDELT detects global information cascades. Correlation across feeds reveals patterns invisible to individual streams. Example: A spike in GDELT health mentions + NOAA weather alerts + APRS emergency traffic in the same region suggests a localized health crisis.

**Why archive knowledge?** Raw web content decays. Archiving creates a queryable knowledge layer immune to link rot, allowing later synthesis across multiple articles. PostGIS spatial queries on archived locations enable geographic pattern discovery.

**Why deep research?** Web searches are noisy. Deep research filters by source diversity, recency, credibility, and requires triangulation before accepting conclusions. This prevents false correlation from echo chambers.

**Why threat correlation?** Threats leave traces across multiple data types. IOCs (IPs, domains, file hashes) appear in threat feeds, OSINT sources, and archived content. Cross-referencing reveals attack campaigns invisible to single-source analysis.

**Why knowledge graphs?** Relationships matter more than facts. Entity extraction + relationship mapping transforms archived content into queryable graph structures, enabling "who worked where with whom" analyses impossible in flat databases.

---

## Pattern 1: OSINT Feed Aggregation & Worker Architecture

**Why workers?** Feeds have different update cadences (APRS every minute, GDELT daily). Workers decouple ingestion from storage, allowing horizontal scaling and independent failure isolation.

**Why PostGIS?** Geographic feeds must support spatial queries. PostGIS enables "all APRS beacons within 10km of coordinate X" or "USGS earthquakes near archived disaster reports" without iteration.

### Worker Pattern for Feed Ingestion

```python
# Why: Async workers prevent blocking on slow feeds
import asyncio
import aiohttp
from datetime import datetime
import json

class FeedWorker:
    def __init__(self, feed_name, source_url, update_interval_seconds, db_connection):
        self.feed_name = feed_name
        self.source_url = source_url
        self.update_interval = update_interval_seconds
        self.db = db_connection
        self.last_update = None
    
    async def fetch_and_store(self):
        """Why: Separate fetch from store for testability and restart resilience"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.source_url, timeout=10) as resp:
                    data = await resp.json()
                    await self.store_feed(data)
                    self.last_update = datetime.utcnow()
        except Exception as e:
            # Why: Log failures without crashing worker; allow retry next cycle
            print(f"Feed {self.feed_name} failed: {e}")
    
    async def store_feed(self, data):
        """Why: Async DB operations prevent worker threads blocking"""
        for item in data:
            # Normalize to common schema
            record = {
                'feed_source': self.feed_name,
                'item_id': item.get('id'),
                'timestamp': item.get('timestamp', datetime.utcnow().isoformat()),
                'data': json.dumps(item),
                'geom': None  # PostGIS geometry column
            }
            if 'lat' in item and 'lon' in item:
                record['geom'] = f"POINT({item['lon']} {item['lat']})"
            
            await self.db.execute("""
                INSERT INTO feed_items (feed_source, item_id, timestamp, data, geom)
                VALUES ($1, $2, $3, $4, ST_GeomFromText($5, 4326))
                ON CONFLICT (feed_source, item_id) DO UPDATE SET
                    data = EXCLUDED.data, timestamp = EXCLUDED.timestamp
            """, record['feed_source'], record['item_id'], record['timestamp'], 
               record['data'], record['geom'])
    
    async def run(self):
        """Why: Infinite loop with jitter prevents thundering herd"""
        while True:
            await self.fetch_and_store()
            # Why: Add random jitter to prevent all workers requesting simultaneously
            jitter = (hash(self.feed_name) % 10) / 100
            await asyncio.sleep(self.update_interval + jitter)

# Why: Docker orchestration allows easy scaling
class WorkerPool:
    def __init__(self, feeds_config):
        self.workers = [
            FeedWorker(cfg['name'], cfg['url'], cfg['interval'], None)
            for cfg in feeds_config
        ]
    
    async def run_all(self):
        """Why: gather allows all workers to run concurrently"""
        await asyncio.gather(*[w.run() for w in self.workers])
```

### Spatial Query Pattern for Geographic Intelligence

```sql
-- Why: PostGIS spatial indexes enable millisecond-scale geographic queries
CREATE INDEX feed_geom_idx ON feed_items USING GIST(geom);

-- Example: Find all APRS beacons (people/equipment) near archived disaster reports
SELECT 
    f.feed_source,
    f.data->>'callsign' as beacon,
    ST_Distance(f.geom, r.location) as distance_meters,
    r.disaster_type,
    f.timestamp
FROM feed_items f
JOIN archived_reports r ON ST_DWithin(f.geom, r.location, 10000)  -- 10km
WHERE f.feed_source = 'aprs'
AND f.timestamp > now() - interval '24 hours'
AND r.disaster_type = 'earthquake'
ORDER BY distance_meters
LIMIT 100;
```

---

## Pattern 2: Knowledge Archival & Entity Extraction

**Why ArchiveBox?** URLs die; archives don't. ArchiveBox creates self-contained HTML snapshots, enabling temporal search and preventing link rot from invalidating research.

**Link Rot Detection:** Periodic re-validation of archived URLs detects when live sources disappear or change. Compute content hashes of re-fetched pages; compare to archived version to detect tampering or significant updates. Flag changed content for re-archival; missing URLs reduce trust in chains of evidence. Automation schedules weekly validation of high-priority sources.

**Why Paperless-NGX?** Documents exist outside the web. OCR + classification turns PDFs into queryable text.

**Why extraction pipelines?** Raw text is unstructured. Extraction normalizes it for graph construction and threat correlation.

### Content Extraction & Summarization Pipeline

```python
# Why: Multi-stage pipeline allows independent optimization of each stage
from typing import List, Dict
import spacy
from transformers import pipeline

class ArchivalPipeline:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        # Why: Summarization model for multi-language briefings
        self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        self.ner_extractor = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english")
    
    def extract_entities(self, text: str) -> Dict:
        """Why: NER identifies subjects (people, organizations, locations, dates)"""
        doc = self.nlp(text[:500000])  # Limit to prevent memory explosion
        entities = {
            'persons': [],
            'organizations': [],
            'locations': [],
            'dates': [],
            'money': [],
            'facilities': []
        }
        
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                entities['persons'].append(ent.text)
            elif ent.label_ == 'ORG':
                entities['organizations'].append(ent.text)
            elif ent.label_ == 'GPE':  # Geopolitical entity
                entities['locations'].append(ent.text)
            elif ent.label_ == 'DATE':
                entities['dates'].append(ent.text)
        
        return entities

    def extract_clean_text(self, html: str) -> str:
        """Why: Remove boilerplate (ads, nav, comments) before extraction"""
        # Why: Mozilla Readability/trafilatura parse DOM structure, not just text
        from readability import Document  # Mozilla Readability Python binding
        doc = Document(html)
        # Why: trafilatura as fallback for parsing-resistant content
        try:
            return doc.summary() if doc.summary() else trafilatura.extract(html)
        except:
            # Why: readability-lxml as minimal dependency fallback
            from readability.readability import Document as RDoc
            return RDoc(html).summary()

    def summarize_content(self, text: str, max_length=150) -> str:
        """Why: Summaries enable quick briefing generation without reading full documents"""
        # Why: Truncate to prevent transformer memory exhaustion
        chunks = [text[i:i+1024] for i in range(0, len(text), 1024)]
        summaries = []
        
        for chunk in chunks[:5]:  # Process first 5 chunks
            try:
                summary = self.summarizer(chunk, max_length=max_length, min_length=50, do_sample=False)
                summaries.append(summary[0]['summary_text'])
            except:
                continue
        
        return ' '.join(summaries) if summaries else text[:200]

    def extract_text_from_images(self, pdf_or_image_path: str) -> str:
        """Why: Tesseract OCR extracts text from scanned documents and image-based content"""
        import pytesseract
        from PIL import Image
        try:
            img = Image.open(pdf_or_image_path)
            return pytesseract.image_to_string(img)
        except:
            # Why: pytesseract with PDF input processes multi-page scans
            return pytesseract.image_to_pdf_or_text(pdf_or_image_path)

    def process_archived_url(self, archive_id: str, title: str, content: str) -> Dict:
        """Why: Single function ensures consistent metadata across all archived content"""
        entities = self.extract_entities(content)
        summary = self.summarize_content(content)
        
        return {
            'archive_id': archive_id,
            'title': title,
            'summary': summary,
            'entities': entities,
            'word_count': len(content.split()),
            'processed_at': datetime.utcnow().isoformat()
        }
```

### Threat Intelligence Platforms Integration

**OpenCTI** provides structured threat intelligence storage with relationships, campaigns, and malware tracking. **MISP (Malware Information Sharing Platform)** offers community-driven threat sharing with tagging and event correlation. **AlienVault OTX** aggregates open threat feeds (malware, IP reputation, domains) via API. **VirusTotal** provides file/URL analysis with 90+ AV engines plus behavioral analysis. Integrating these platforms into your feed workers normalizes external threat data into your IOC table, enabling cross-platform indicator correlation impossible within individual platforms.

### Headless Browser & Content Capture Tools

**Playwright/Puppeteer** automate headless Chrome/Firefox to render JavaScript-heavy pages before archival, solving the problem of SPA (Single Page Application) content invisible to static scrapers. **FlareSolverr** proxies requests through headless browsers to bypass Cloudflare, reCAPTCHA, and WAF blocks protecting target content. Critical for modern web scraping where static HTML parsing fails; integrates with ArchiveBox for capturing rendered DOM state rather than initial HTML.

---

## Pattern 3: Deep Research with Triangulation & Confidence Scoring

**Why triangulation?** Single sources lie. Consensus across independent sources indicates reliable intelligence.

**Why diversity filtering?** Echo chambers amplify bias. Requiring sources from different domains prevents false confidence.

**Why recency checks?** Intelligence decays. News from a year ago about current threats is dangerously outdated.

### Source-Grounded Research Pipeline

```python
# Why: Explicit confidence scoring prevents unfounded conclusions
from enum import Enum
from datetime import datetime, timedelta

class SourceQuality(Enum):
    PRIMARY = 0.9      # Eye-witness, official records
    SECONDARY = 0.7    # Reporting on primary sources
    TERTIARY = 0.5     # Analysis/opinion
    UNKNOWN = 0.3      # No clear sourcing

class ResearchTriangulation:
    def __init__(self):
        # Why: Domain diversity prevents echo chambers
        self.domains = {
            'government': ['state.gov', 'treasury.gov', 'sec.gov'],
            'academic': ['stanford.edu', 'mit.edu', 'arxiv.org'],
            'journalism': ['reuters.com', 'apnews.com', 'bbc.com'],
            'threat_intel': ['abuse.ch', 'cisa.gov', 'shodan.io']
        }
        # Why: Tavily API provides programmatic web search with source ranking
        self.tavily_client = None  # Initialize with API key from environment
    
    def expand_query(self, base_query: str) -> List[str]:
        """Why: Query expansion finds relevant evidence researchers might miss"""
        expansions = [
            base_query,
            f'"{base_query}"',  # Why: Exact phrase for precision
            f'{base_query} confirmed',
            f'{base_query} evidence',
            f'{base_query} -hoax',  # Why: Exclude obvious false positives
        ]
        return expansions

    def search_with_tavily(self, query: str, max_results: int = 10) -> List[Dict]:
        """Why: Tavily ranks sources by relevance and credibility automatically"""
        if not self.tavily_client:
            from tavily import Client
            self.tavily_client = Client()
        try:
            response = self.tavily_client.search(query, max_results=max_results, include_raw_content=True)
            return [{'url': r['url'], 'content': r.get('raw_content', r.get('content', '')),
                    'score': r.get('score', 0.5)} for r in response.get('results', [])]
        except:
            return []  # Why: Graceful fallback if Tavily unavailable

    def score_source(self, url: str, publication_date: str, claim: str) -> Dict:
        """Why: Explicit scoring enables confidence thresholds"""
        domain = url.split('/')[2]
        
        # Why: Recency scoring - older news is less reliable for current threats
        days_old = (datetime.utcnow() - datetime.fromisoformat(publication_date)).days
        recency_score = 0.9 if days_old < 7 else 0.5 if days_old < 90 else 0.2
        
        # Why: Domain categorization indicates source type
        category_scores = {domain: 0.8 for domain_list in self.domains.values() for domain in domain_list}
        quality_score = category_scores.get(domain, 0.3)
        
        return {
            'url': url,
            'quality': quality_score,
            'recency': recency_score,
            'combined_confidence': (quality_score + recency_score) / 2,
            'reasoning': f"Domain quality {quality_score}, recency {recency_score}"
        }
    
    def triangulate(self, claim: str, min_sources: int = 3) -> Dict:
        """Why: Require multiple independent sources before accepting conclusion"""
        queries = self.expand_query(claim)
        sources_by_domain = {}
        
        # Pseudo-code: would search multiple domains
        # for query in queries:
        #     for domain_category, domains in self.domains.items():
        #         results = search(query, domain=domains)
        #         for result in results:
        #             score = self.score_source(result['url'], result['date'], claim)
        #             if score['combined_confidence'] > 0.6:
        #                 sources_by_domain.setdefault(domain_category, []).append(score)
        
        # Why: Cross-domain consensus indicates reliable intelligence
        confident_categories = [
            cat for cat, sources in sources_by_domain.items() 
            if len(sources) >= min_sources
        ]
        
        return {
            'claim': claim,
            'triangulated': len(confident_categories) >= 2,
            'confidence': 'HIGH' if len(confident_categories) >= 3 else 'MEDIUM',
            'evidence_domains': confident_categories
        }
```

---

## Pattern 4: Threat Feed Correlator & IOC Matching

**Why IOC matching?** Threats reuse infrastructure. Same IP appears in malware samples, threat feeds, and WHOIS records—strong signal.

**Why correlation windows?** Temporal proximity matters. Events 30 seconds apart are related; events days apart are coincidence.

### IOC Extraction & Cross-Reference Pattern with Bloom Filtering

**Bloom Filter Deduplication:** For high-volume feeds (e.g., GDELT 300K+ daily events, ADS-B millions/day), Bloom filters provide O(1) deduplication with minimal memory. A Bloom filter probabilistically tests membership; false positives are acceptable (re-check DB), but false negatives are impossible. Reduces database load by 40-60% on repetitive feeds. Python **pybloom_live** or Redis Bloom modules enable distributed deduplication across worker pools.

```sql
-- Why: Normalized IOC table enables rapid threat searches
CREATE TABLE iocs (
    ioc_hash VARCHAR(64) PRIMARY KEY,  -- SHA256 of normalized IOC
    ioc_type VARCHAR(32),              -- ip, domain, email, file_hash, url
    ioc_value VARCHAR(500),
    source_feed VARCHAR(100),
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    confidence FLOAT,
    context JSONB
);

CREATE INDEX ioc_type_idx ON iocs(ioc_type, ioc_value);

-- Why: Temporal window join reveals attack campaigns
SELECT 
    t1.ioc_value,
    t1.source_feed as first_appearance,
    t2.source_feed as second_appearance,
    t3.source_feed as third_appearance,
    EXTRACT(EPOCH FROM (t2.first_seen - t1.first_seen)) as seconds_between_1_2,
    EXTRACT(EPOCH FROM (t3.first_seen - t2.first_seen)) as seconds_between_2_3
FROM iocs t1
JOIN iocs t2 ON t1.ioc_value = t2.ioc_value 
    AND t1.source_feed != t2.source_feed
    AND t2.first_seen BETWEEN t1.first_seen AND t1.first_seen + interval '30 days'
LEFT JOIN iocs t3 ON t2.ioc_value = t3.ioc_value 
    AND t2.source_feed != t3.source_feed
    AND t3.first_seen BETWEEN t2.first_seen AND t2.first_seen + interval '7 days'
WHERE t1.ioc_type = 'ip'
AND t1.confidence > 0.7
ORDER BY t1.first_seen DESC;
```

### STIX/TAXII Standards for Threat Data Interoperability

**STIX (Structured Threat Information Expression)** provides standardized JSON schemas for encoding threat indicators, malware, campaigns, and attack patterns. **TAXII (Trusted Automated eXchange of Indicator Information)** enables automated, authenticated exchange of STIX data between organizations. Together they solve interoperability: CTI feeds in STIX format integrate seamlessly into correlation engines; TAXII servers allow bilateral sharing without manual format translation. Critical for multi-source threat intelligence fusion and community feeds (e.g., MISP exports STIX; ATT&CK framework publishes STIX bundles).

---

## Pattern 5: Knowledge Graph Builder (Neo4j/FalkorDB)

**Why graphs?** Networks reveal hidden relationships. Entity-relationship graphs enable "degrees of separation" queries impossible in relational databases.

**Why from archived content?** Archives don't change; they're perfect for reproducible relationship extraction.

### Entity-Relationship Extraction & Graph Construction

```python
# Why: Relationship extraction identifies actor networks
class KnowledgeGraphBuilder:
    def __init__(self, graph_db_url):
        from neo4j import GraphDatabase
        self.driver = GraphDatabase.driver(graph_db_url)
    
    def extract_relationships(self, text: str, entities: Dict) -> List[Dict]:
        """Why: Dependency parsing finds verb relationships between entities"""
        import spacy
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text)
        
        relationships = []
        # Why: ROOT verb represents main action/relationship
        for token in doc:
            if token.dep_ == "ROOT":  # Main verb
                # Find subject and object
                subj = next((t.text for t in token.subtree if t.dep_ in ["nsubj", "nsubj:pass"]), None)
                obj = next((t.text for t in token.subtree if t.dep_ == "dobj"), None)
                
                if subj and obj:
                    relationships.append({
                        'subject': subj,
                        'predicate': token.text,
                        'object': obj
                    })
        
        return relationships
    
    def add_to_graph(self, relationships: List[Dict], source_archive_id: str):
        """Why: Cypher queries are declarative; easier to reason about correctness"""
        with self.driver.session() as session:
            for rel in relationships:
                # Why: CREATE clause is idempotent; safe to run multiple times
                session.run("""
                    MERGE (subject:Entity {name: $subject})
                    MERGE (object:Entity {name: $object})
                    MERGE (subject)-[r:RELATIONSHIP {
                        type: $predicate,
                        source: $source,
                        created_at: timestamp()
                    }]->(object)
                """, 
                subject=rel['subject'],
                object=rel['object'],
                predicate=rel['predicate'],
                source=source_archive_id)
    
    def find_degrees_of_separation(self, entity_a: str, entity_b: str, max_hops: int = 3) -> Dict:
        """Why: Shortestpath reveals hidden connections in intelligence networks"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH path = shortestPath(
                    (a:Entity {name: $entity_a})-[*..{hops}]-(b:Entity {name: $entity_b})
                )
                RETURN path, length(path) as hop_count
            """, entity_a=entity_a, entity_b=entity_b, hops=max_hops)
            
            paths = []
            for record in result:
                paths.append({
                    'path': record['path'],
                    'hops': record['hop_count']
                })
            
            return {'paths': paths, 'connected': len(paths) > 0}
```

---

## Pattern 6: Automated Briefing Generator

**Why templates?** Consistent format enables quick scanning. Briefing readers know where to find key points.

**Why priority ranking?** Importance ≠ recency. Yesterday's major breakthrough beats today's minor news.

### Scheduled Intelligence Briefing Pattern

```python
# Why: Scheduled tasks run independent of user requests
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import json

class BriefingGenerator:
    def __init__(self, db, archival_pipeline, threat_correlator):
        self.db = db
        self.pipeline = archival_pipeline
        self.correlator = threat_correlator
        self.scheduler = BackgroundScheduler()
    
    def score_priority(self, item: Dict) -> float:
        """Why: Multi-factor scoring prevents over-weighting recency"""
        # Why: Threat level is strongest signal (0-1)
        threat_score = item.get('threat_level', 0.0)
        
        # Why: Source credibility prevents amplifying unreliable sources
        credibility_score = item.get('source_credibility', 0.5)
        
        # Why: Correlation across feeds indicates real phenomenon
        correlation_count = item.get('correlation_count', 0)
        correlation_score = min(correlation_count / 5.0, 1.0)
        
        # Why: Recency bonus for threats, decay for old news
        hours_old = (datetime.utcnow() - item['timestamp']).total_seconds() / 3600
        recency = 1.0 if hours_old < 6 else 0.7 if hours_old < 24 else 0.3
        
        # Why: Weighted average allows tuning based on environment
        return (threat_score * 0.4 + credibility_score * 0.3 + 
                correlation_score * 0.2 + recency * 0.1)
    
    def generate_briefing(self, hours_lookback: int = 24) -> str:
        """Why: Single briefing per schedule prevents duplicate reading"""
        cutoff = datetime.utcnow() - timedelta(hours=hours_lookback)
        
        # Collect all items from feeds
        items = self.db.execute("""
            SELECT * FROM feed_items 
            WHERE timestamp > $1
        """, cutoff)
        
        # Score and sort by priority
        scored = [(item, self.score_priority(item)) for item in items]
        ranked = sorted(scored, key=lambda x: x[1], reverse=True)
        
        # Format briefing
        briefing = f"""
INTELLIGENCE BRIEFING
Generated: {datetime.utcnow().isoformat()}
Period: {hours_lookback} hours

TOP THREATS:
"""
        for item, score in ranked[:10]:
            briefing += f"\n- {item['title']} (Priority: {score:.2f})"
            briefing += f"\n  Source: {item['source']}"
            briefing += f"\n  Summary: {item.get('summary', 'N/A')}\n"
        
        return briefing
    
    def schedule_daily(self, hour: int = 6, minute: int = 0):
        """Why: Cron allows precise scheduling without polling"""
        self.scheduler.add_job(
            self.generate_briefing,
            'cron',
            hour=hour,
            minute=minute,
            args=[24],
            id='daily_briefing'
        )
        self.scheduler.start()
```

---

## Pattern 7: Source Credibility Scoring

**Why automation?** Manual credibility assessment is slow and inconsistent.

**Why historical tracking?** Sources improve/degrade over time. Tracking history identifies transitions.

### Credibility Assessment Engine

```python
# Why: Multi-dimensional credibility prevents oversimplification
class CredibilityScorer:
    def score_source(self, url: str, historical_claims: List[Dict]) -> Dict:
        """Why: Historical accuracy is strongest credibility signal"""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        # Why: Accuracy rate over time shows pattern of truthfulness
        correct_claims = sum(1 for c in historical_claims if c.get('verified'))
        accuracy_rate = correct_claims / len(historical_claims) if historical_claims else 0.5
        
        # Why: Known biases require disclosure; not penalty, but transparency
        known_biases = self._check_known_biases(domain)
        bias_penalty = 0.1 * len(known_biases)
        
        # Why: Transparency about sources builds credibility
        has_citations = self._check_source_transparency(url)
        citation_bonus = 0.15 if has_citations else 0.0
        
        # Why: Authority in domain matters
        domain_authority = self._assess_domain_authority(domain)
        
        credibility = (accuracy_rate * 0.5 + domain_authority * 0.3 + 
                      citation_bonus - bias_penalty)
        
        return {
            'domain': domain,
            'credibility': max(0.0, min(credibility, 1.0)),
            'accuracy_rate': accuracy_rate,
            'known_biases': known_biases,
            'transparent_sourcing': has_citations,
            'reasoning': f"Accuracy {accuracy_rate:.0%}, Domain authority {domain_authority:.0%}"
        }
```

---

## Pattern 8: ADS-B/APRS Correlation Engine & RF Decoder Tools

**Why fusion?** Radio signals alone show "aircraft at position X". Add flight data (destination, airline, previous positions) and you see patterns. Add APRS (ground infrastructure) and you understand regional network topology.

**Why temporal correlation?** Aircraft landing where emergency beacons activate suggests response operations.

**RF Decoder Tools:** **aprslib** (Python) parses APRS packets for real-time beacon extraction. **dump1090/readsb** decode ADS-B signals from RTL-SDR dongles; readsb adds net reception and multi-site aggregation. **rtl_433** captures ISM band signals (weather stations, tire sensors, industrial devices), expanding RF correlation beyond aircraft/APRS. Decoding these signals provides raw geolocation data unavailable through API-only sources.

**Satellite Tracking:** **Satrec/SGP4** libraries propagate satellite positions from TLE (Two-Line Element) data with sub-kilometer accuracy. **space-track.org** (US Space Force) and **celestrak.com** provide authoritative TLE updates. Enables tracking intelligence satellites, reconnaissance platforms, and LEO sensors; correlating satellite coverage with geopolitical events reveals operational priorities.

### RF Signal Fusion & Pattern Detection

```python
# Why: Multi-modal correlation requires explicit matching logic
class RFCorrelationEngine:
    def __init__(self, db):
        self.db = db
    
    def correlate_adsb_aprs(self, adsb_icao24: str, aprs_callsign: str, 
                            time_window_seconds: int = 300) -> Dict:
        """Why: Time window excludes random coincidences"""
        # Get ADS-B track
        adsb_positions = self.db.execute("""
            SELECT timestamp, latitude, longitude, altitude, squawk
            FROM adsb_positions
            WHERE icao24 = $1
            ORDER BY timestamp DESC
            LIMIT 100
        """, adsb_icao24)
        
        # Get APRS positions in time window
        aprs_positions = self.db.execute("""
            SELECT timestamp, latitude, longitude
            FROM aprs_beacons
            WHERE callsign = $1
            AND timestamp > now() - interval '{seconds} seconds'
        """, aprs_callsign, time_window_seconds)
        
        correlations = []
        # Why: Spatial-temporal proximity indicates causal relationship
        for ads in adsb_positions:
            for aprs in aprs_positions:
                distance = self._haversine_distance(
                    ads['latitude'], ads['longitude'],
                    aprs['latitude'], aprs['longitude']
                )
                time_delta = abs((ads['timestamp'] - aprs['timestamp']).total_seconds())
                
                # Why: Both spatial and temporal thresholds prevent false positives
                if distance < 1000 and time_delta < time_window_seconds:
                    correlations.append({
                        'aircraft_icao24': adsb_icao24,
                        'ground_beacon': aprs_callsign,
                        'distance_meters': distance,
                        'time_delta_seconds': time_delta,
                        'aircraft_altitude': ads['altitude'],
                        'squawk_code': ads['squawk']
                    })
        
        return {
            'correlated': len(correlations) > 0,
            'correlation_count': len(correlations),
            'strongest_match': max(correlations, key=lambda x: 1.0 / (1 + x['distance_meters'])) if correlations else None
        }
    
    def detect_response_operations(self, region: str, hours_lookback: int = 6) -> List[Dict]:
        """Why: Cluster analysis finds coordinated activity"""
        cutoff = datetime.utcnow() - timedelta(hours=hours_lookback)
        
        # Why: Military/emergency aircraft squawk 7700 (emergency)
        emergency_flights = self.db.execute("""
            SELECT DISTINCT icao24, COUNT(*) as position_count
            FROM adsb_positions
            WHERE squawk = '7700'
            AND timestamp > $1
            AND ST_Within(
                ST_Point(longitude, latitude),
                ST_Buffer(ST_GeomFromText('POINT(...)', 4326), 50000)  -- 50km radius
            )
            GROUP BY icao24
            HAVING COUNT(*) > 10  -- Why: Multiple positions indicate sustained operation
        """, cutoff)

        return [{'icao24': f['icao24'], 'position_count': f['position_count']}
                for f in emergency_flights]

    def correlate_ais_shipping(self, region: str, hours_lookback: int = 24) -> List[Dict]:
        """Why: AIS vessel tracking complements aircraft monitoring for maritime patterns"""
        # Query AIS data from AISHub, MarineTraffic APIs, or decoded AIS feeds
        cutoff = datetime.utcnow() - timedelta(hours=hours_lookback)

        # Why: MMSI (Maritime Mobile Service Identity) identifies vessels like ICAO24 for aircraft
        vessels = self.db.execute("""
            SELECT DISTINCT mmsi, vessel_name, position_count, latest_position
            FROM ais_positions
            WHERE timestamp > $1
            AND ST_Within(latest_position, ST_Buffer(ST_GeomFromText('POINT(...)', 4326), 100000))
            GROUP BY mmsi, vessel_name
            HAVING COUNT(*) > 5  -- Sustained vessel presence
        """, cutoff)

        return [{'mmsi': v['mmsi'], 'name': v['vessel_name'], 'positions': v['position_count']}
                for v in vessels]

**AIS Vessel Tracking Data Sources:** **AISHub** aggregates global AIS broadcasts from coastal stations. **MarineTraffic APIs** provide vessel tracking and shipping patterns. **MMSI (Maritime Mobile Service Identity)** parsing identifies vessels uniquely. Unlike ADS-B (aircraft), AIS includes vessel type, cargo, draft (water depth), and destination—rich context for detecting sanctions violations, illicit transfers, or supply chain disruptions.

    def _haversine_distance(self, lat1, lon1, lat2, lon2) -> float:
        """Why: Accurate distance for geographic correlation"""
        import math
        R = 6371000  # Earth radius in meters
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
```

---

## Pattern 9: Research Audit Trail

**Why provenance?** "I read this somewhere" is unusable in intelligence. Full chain from raw source to conclusion enables verification and error correction.

**Why versioning?** Sources change. Archiving claim+evidence pairs allows tracking how conclusions evolved.

### Full Research Provenance Tracking

```python
# Why: Immutable audit log prevents post-hoc rationalization
class ResearchAuditTrail:
    def __init__(self, db):
        self.db = db
    
    def log_research_step(self, conclusion_id: str, step_type: str, 
                         evidence_id: str, reasoning: str, user: str):
        """Why: Every step creates accountability"""
        self.db.execute("""
            INSERT INTO audit_trail (
                conclusion_id, step_number, step_type, evidence_id, 
                reasoning, researcher, timestamp
            )
            VALUES (
                $1, (SELECT COALESCE(MAX(step_number), 0) + 1 
                     FROM audit_trail WHERE conclusion_id = $1),
                $2, $3, $4, $5, now()
            )
        """, conclusion_id, step_type, evidence_id, reasoning, user)
    
    def get_research_lineage(self, conclusion_id: str) -> Dict:
        """Why: Complete lineage enables error reconstruction"""
        trail = self.db.execute("""
            SELECT step_number, step_type, evidence_id, reasoning, 
                   researcher, timestamp
            FROM audit_trail
            WHERE conclusion_id = $1
            ORDER BY step_number
        """, conclusion_id)
        
        # Why: Reconstruct the logical path
        chain = []
        for step in trail:
            evidence = self.db.execute(
                "SELECT * FROM evidence WHERE id = $1",
                step['evidence_id']
            )[0] if step['evidence_id'] else None
            
            chain.append({
                'step': step['step_number'],
                'type': step['step_type'],  # search, archive, correlate, verify
                'evidence': evidence,
                'reasoning': step['reasoning'],
                'by': step['researcher'],
                'at': step['timestamp'].isoformat()
            })
        
        return {'conclusion_id': conclusion_id, 'chain': chain}
```

---

## Deployment: Docker Orchestration

**Why containers?** Feeds, workers, and databases are independent services. Containers enable scaling workers without restarting the database.

```yaml
# docker-compose.yml
version: '3.9'
services:
  postgres:
    image: postgis/postgis:16-3.4
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  neo4j:
    image: neo4j:5-enterprise
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
    ports:
      - "7687:7687"

  feed-workers:
    build: ./feed-workers
    depends_on:
      - postgres
    environment:
      DATABASE_URL: postgresql://user:${DB_PASSWORD}@postgres:5432/intelligence
    deploy:
      replicas: 3  # Why: Horizontal scaling for worker availability
      restart_policy:
        condition: on-failure
        delay: 5s
```

---

## Summary: Why This Consolidation Works

This super agent succeeds because each pattern solves a specific intelligence problem:

1. **Feeds + Workers**: Handle continuous data streams at scale
2. **Archival + Extraction**: Create permanent, queryable knowledge layer
3. **Deep Research**: Filter noise through triangulation and source diversity
4. **Threat Correlation**: Connect IOCs across feeds to identify campaigns
5. **Knowledge Graphs**: Reveal actor networks and relationships
6. **Briefing Generator**: Turn raw data into actionable summaries
7. **Credibility Scoring**: Automate trust assessment
8. **RF Fusion**: Correlate radio signals with geographic context
9. **Audit Trail**: Enable verification and error correction

Together: **Continuous, correlated, verifiable intelligence from a unified platform.**
