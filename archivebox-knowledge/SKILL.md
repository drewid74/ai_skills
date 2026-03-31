---
name: archivebox-knowledge
description: "Use this skill whenever the user wants to archive web content, build a personal knowledge base from web sources, manage bookmarks and reading lists, or set up automated content capture pipelines. Triggers include: any mention of 'ArchiveBox', 'web archive', 'archive', 'wayback', 'bookmark', 'reading list', 'save for later', 'Pocket', 'Raindrop', 'Wallabag', 'SingleFile', 'Readability', 'web scraping', 'content extraction', 'knowledge capture', 'knowledge management', 'second brain', 'PKM', 'personal knowledge', 'Paperless', 'Paperless-NGX', 'document management', 'OCR', 'RSS to archive', 'save this page', 'firmware tracking', 'changelog monitoring', 'link rot', 'digital preservation', or requests to automatically capture, organize, summarize, or search through web content and documents. Also use when the user wants to build pipelines that ingest content from various sources (browsers, RSS, Discord, email) and archive or summarize it. If someone says 'I want to save everything I read' or 'track changes to a website', use this skill."
---

# Web Archival & Personal Knowledge Management

Build self-hosted pipelines to capture, extract, summarize, and search web content. Own your knowledge base.

## Archival Engines

**ArchiveBox** — Self-hosted web archiving that saves HTML, PDFs, screenshots, WARCs, and media. Provides a browsable index with full-text search.
- Setup: `docker compose up` with official image + PostgreSQL backend
- Input: URLs list, bookmarks HTML, Pocket/Pinboard exports, RSS feeds, stdin, or API
- Key config flags: `SAVE_WARC=True`, `SAVE_PDF=True`, `SAVE_SCREENSHOT=True`, `SAVE_READABILITY=True` (trade storage for redundancy)
- Add URLs via cron job, webhook, or API: `curl -X POST http://localhost:8000/api/v1/add -d '{"url": "https://example.com"}'`
- Search backend: Sonic (lightweight) or Elasticsearch (powerful). Why? Sonic indexes raw text from captured pages in seconds
- Cost: you control storage; no recurring fees

**SingleFile** — Capture entire webpage as single self-contained HTML file (CSS, images, fonts inlined). Browser extension + CLI.
- CLI: `single-file https://example.com output.html` — scriptable for pipelines
- Use when: quick single-page capture, offline reading, or visual fidelity matters (preserves layout exactly)
- Export to ArchiveBox or Paperless for bulk processing

**Wallabag** — Self-hosted "read it later" (Pocket alternative you own). Clean interface, browser extension, tagging, annotations.
- Why? Pocket owns your data; Wallabag doesn't. Full-text search across all saved articles
- API for automation: `POST /api/entries` with URL to queue for capture
- Exports: EPUB, PDF, plain text for knowledge base ingest

## Content Extraction

**Readability** — Extract clean article text from cluttered web pages, removing ads and navigation noise.
- Libraries: Mozilla Readability (JavaScript), readability-lxml (Python), trafilatura (Python)
- Output: title, author, publish date, clean text body
- Use in pipeline: `readability(html) → clean_text → summarize → store`
- Python example:
```python
from readability import Document
html = requests.get(url).text
doc = Document(html)
article = {
    'title': doc.title(),
    'text': doc.summary(),  # Clean HTML
    'content': doc.get_text()  # Plain text
}
```

**Headless Browser Scraping** — For JavaScript-rendered sites that static HTML can't capture.
- Tool: Playwright (Python) or Puppeteer (Node). Async execution.
- Anti-bot bypass: Route through FlareSolverr proxy (solves Cloudflare challenges)
- Why Playwright? Handles modern web; waits for elements; auto-handles timeouts
- Pattern: launch → navigate → wait for content → extract → close
```python
async def scrape_js_site(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url, wait_until='networkidle')
        content = await page.content()
        await browser.close()
        return content
```

**Firmware & Changelog Monitoring** — Track release pages for updates. Store last-seen version in JSON file. On change, alert or auto-archive.
- Pattern: fetch page → extract version string → compare to `state.json` → if new, update + notify
- Use Playwright for JavaScript-rendered release pages, simple requests for static feeds
- Schedule via cron: `0 */6 * * * python monitor_changelog.py`

## Import Pipelines

**Browser Bookmarks** — Migrate from Chrome/Firefox/Safari. Parse HTML, normalize URLs, bulk import.
- Export format: Netscape bookmark HTML (standard across browsers)
- Script: parse HTML → extract `<a>` tags + folder structure as tags → ArchiveBox bulk import
- One-time migration: `archivebox add < bookmarks.html`

**Pocket / Raindrop / Pinboard** — Export JSON/HTML from service, transform to ArchiveBox format, import.
- Ongoing capture: Set up cron to export daily, pipe new URLs to ArchiveBox
- Why own archival? Services shut down; you keep your data

**Discord Messages** — Export with DiscordChatExporter (CLI), extract URLs, archive linked content + metadata.
- Preserves context: save surrounding messages as notes alongside archived link

**RSS Feeds** — OPML file defines organized feed list. Tier polling: news (5 min), blogs (30 min), archives (60 min).
- Pipeline: fetch feed → parse entries → extract URLs → dedup (hash URL) → archive
- Why dedup? Same article shared across feeds; one archive copy with multiple sources noted

**Email Newsletters** — Forward to dedicated mailbox or parse inbox. Extract URLs + email body.
- Archive linked content + save email as PDF for context (Paperless handles this)

## Summarization Pipeline

Extract clean text from archived content, send to LLM, store summary + metadata.

```python
async def summarize_article(url: str, extracted_text: str, llm_client):
    """Summarize captured article via LLM."""
    prompt = f"""Summarize this article. Return JSON:
    - title: inferred title
    - summary: 2-3 sentences
    - key_points: 3-5 takeaways
    - tags: topic tags
    - entities: people, orgs, places mentioned

    Text: {extracted_text[:4000]}"""

    response = await llm_client.create_message(
        model='claude-3-5-sonnet-20241022',
        max_tokens=500,
        messages=[{'role': 'user', 'content': prompt}]
    )
    return json.loads(response.content[0].text)
```

Batch processing: queue articles, process in batches to avoid rate limits. Store summary + URL + tags in knowledge base.

## Document Management (Paperless-NGX)

Self-hosted document archive with OCR. Scans, email forwarding, API, folder watching.
- Setup: `docker compose` with PostgreSQL + Redis + Tesseract
- Consumption directory: any PDF/image dropped here is auto-OCRd and indexed
- Why OCR? Makes scanned documents searchable as if they were typed
- Integration: ArchiveBox exports PDF → consumption directory → Paperless OCRs + indexes

Full-text search across all documents. Tags bridge archive and documents (map ArchiveBox categories to Paperless tags for unified search).

## Knowledge Base Integration

After capture + summarization, push to persistent knowledge store. Dedup by URL before insert.

- Options: vector database (semantic search via embeddings), graph database (relationships), or both
- Enrichment: extract entities → link to existing knowledge (person → organization → project)
- Dedup strategy: hash URL (removes tracking params), compare content hash if URL is new variant
- Why? Prevents duplication; maintains single source of truth; enables relationship discovery

## Search & Retrieval

**Full-text**: Sonic (lightweight, embedded), Elasticsearch (distributed, powerful), or PostgreSQL FTS (no extra infra).

**Semantic**: Embed summaries into vectors → store in vector DB (Milvus, Weaviate, Pinecone) → similarity search on user query.

**Faceted**: Filter by date range, source (Pocket vs RSS vs Discord), content type, tags.

**Combined**: Keyword filter → semantic rerank → return ordered results. Fast + smart.

## Monitoring & Maintenance

- **Storage growth**: Archives expand quickly. Monitor disk usage. Archive periodic disk snapshots (ZFS, rsync to secondary)
- **Dead link detection**: Periodically re-fetch archived URLs. Alert if link rot detected (validates archive value)
- **Archive health**: Verify snapshots are complete (not just error pages or redirects)
- **Backup the archive**: The archive itself needs backing up. 3-2-1 rule: 3 copies, 2 media types, 1 offsite

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Page not archiving | JavaScript-rendered | Use Playwright backend; enable `SAVE_DOM` |
| FlareSolverr failing | Cloudflare updated challenge | Update container; verify proxy config |
| OCR quality poor | Low scan resolution | Re-scan at 300 DPI minimum; verify language packs |
| Search returns nothing | Index not built | Rebuild Sonic index; verify content extracted |
| Storage filling fast | Capturing too much | Disable unneeded formats (`SAVE_MEDIA=False` if not needed) |
| Import fails | Format mismatch | Verify bookmarks are Netscape HTML; URLs are plain one-per-line |

## Getting Started

1. **Self-host ArchiveBox**: `git clone https://github.com/ArchiveBox/ArchiveBox && cd ArchiveBox && docker compose up`
2. **Import bookmarks**: Export from browser, run `archivebox add < bookmarks.html`
3. **Add RSS feed**: `archivebox list bookmarks.json | archivebox add` (or use UI)
4. **Enable search**: Configure Sonic backend in `ArchiveBox.conf`
5. **Automate capture**: Cron job to fetch RSS and feed to ArchiveBox nightly
6. **Build knowledge base**: Export ArchiveBox JSON → extract content → summarize → push to vector DB

Start small (100 URLs), tune retention rules, grow from there. Storage is cheap; knowledge is priceless.
