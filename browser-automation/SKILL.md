---
name: browser-automation
description: "Use this skill whenever the user wants to automate browser interactions, scrape web content, test web UIs, or build automated workflows that interact with websites. Triggers include: any mention of 'Playwright', 'Puppeteer', 'Selenium', 'browser automation', 'headless browser', 'web scraping', 'scraping', 'crawling', 'spider', 'BeautifulSoup', 'Scrapy', 'Cheerio', 'DOM manipulation', 'screenshot automation', 'PDF generation', 'form filling', 'login automation', 'e2e testing', 'end-to-end testing', 'Cypress', 'UI testing', 'visual regression', 'FlareSolverr', 'Cloudflare bypass', 'anti-bot', 'CAPTCHA', 'user agent', 'cookie management', 'session handling', 'web interaction', 'click automation', 'page monitoring', 'price tracking', or requests to interact with websites programmatically, extract data from web pages, automate repetitive web tasks, or test web applications. Also use when the user asks 'how do I get data from this website?', 'automate this web form', or 'take screenshots of pages'. If someone wants to interact with a website without manually using a browser, use this skill."
---

# Browser Automation & Web Scraping

Automate browser interactions for scraping, testing, monitoring, and workflow automation. This guide covers tool selection, headless browser patterns, content extraction, anti-bot handling, and ethical practices.

## Tool Selection

### Playwright (Recommended)
Multi-browser automation with a modern API. Supports Chromium, Firefox, WebKit from one codebase. Available in Python, JavaScript, Java, .NET. Features auto-wait (waits for elements automatically before interacting), network interception, screenshots, PDFs, video recording, and built-in tracing. Why: reliable, well-maintained, excellent debugging, less flaky than Selenium.

### Puppeteer
Chromium-only, JavaScript/TypeScript only. Lighter weight if you only need Chrome. Good for Chrome DevTools Protocol access. Use when you have existing Node infrastructure or need Chrome-specific features.

### Selenium
Oldest, widest browser support, most language bindings. More verbose API, requires manual waits (flakier than Playwright). Use when existing tests depend on it or you need a specific browser unsupported by Playwright.

### BeautifulSoup + requests (Python)
No browser needed—pure HTTP + HTML parsing. Fast, lightweight, zero resource overhead. Use when pages are server-rendered (no JavaScript required). Not suitable for SPAs, login flows, or dynamic content.

### Scrapy
Full framework for large-scale structured scraping. Built-in rate limiting, retry logic, caching, robots.txt respect. Use for thousands of pages with consistent structure.

### Cypress
Purpose-built for testing (not scraping). Runs inside the browser with excellent DevTools debugging. Use for e2e testing of your own applications.

## Playwright Core Patterns

### Basic Navigation and Extraction
```python
from playwright.async_api import async_playwright

async def scrape_page(url: str) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")

        title = await page.title()
        content = await page.inner_text("body")

        await browser.close()
        return {"title": title, "content": content}
```

### Waiting Strategies
- `wait_until="networkidle"`: waits for all network activity to settle (safest)
- `wait_until="domcontentloaded"`: faster, suitable for most cases
- `page.wait_for_selector(".loaded")`: wait for specific element to exist
- `page.wait_for_load_state("domcontentloaded")`: explicit state wait
- Auto-wait: Playwright automatically waits for elements to be visible/enabled before clicking (more reliable than Selenium)

### Form Interaction
```python
# Playwright auto-waits for elements to be interactive
await page.fill("#username", "user@example.com")
await page.fill("#password", "secret123")
await page.click("button[type='submit']")
await page.wait_for_url("**/dashboard")  # Wait for navigation
```

### Screenshots & PDFs
```python
# Full page screenshot (useful for visual regression testing)
await page.screenshot(path="page.png", full_page=True)

# Element-specific screenshot
element = await page.query_selector(".chart")
await element.screenshot(path="chart.png")

# PDF generation (Chromium only)
await page.pdf(path="page.pdf", format="A4", print_background=True)
```

### Network Interception
```python
# Block resources to speed up scraping
await page.route("**/*.{png,jpg,jpeg,gif,svg}", lambda route: route.abort())

# Capture API responses for structured data extraction
responses = []
def handle_response(response):
    if "/api/" in response.url:
        responses.append(response)
page.on("response", handle_response)
```

### Parallel Scraping with Contexts
```python
# Contexts are isolated like incognito windows (separate cookies, storage)
context = await browser.new_context()
page1 = await context.new_page()
page2 = await context.new_page()
# Use ThreadPoolExecutor or asyncio.gather to run in parallel

# Maintain sessions across pages
context = await browser.new_context(storage_state="session.json")
```

### Session Persistence
```python
# Save cookies and localStorage after login
await context.storage_state(path="session.json")

# Restore session for subsequent runs
context = await browser.new_context(storage_state="session.json")
page = await context.new_page()
```

## Content Extraction

### Structured Data from Tables
```python
rows = await page.query_selector_all("table tbody tr")
data = []
for row in rows:
    cells = await row.query_selector_all("td")
    values = [await cell.inner_text() for cell in cells]
    data.append(values)
```

### Item Lists
```python
# Extract products with specific structure
items = await page.query_selector_all(".product-card")
products = []
for item in items:
    name = await item.query_selector_eval("h3", "el => el.textContent")
    price = await item.query_selector_eval(".price", "el => el.textContent")
    products.append({"name": name, "price": price})
```

### Pagination
```python
while True:
    items = await extract_data(page)
    all_items.extend(items)

    next_button = await page.query_selector("a.next")
    if not next_button:
        break
    await next_button.click()
    await page.wait_for_load_state("networkidle")
```

### Infinite Scroll
```python
prev_height = 0
while True:
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(2000)
    curr_height = await page.evaluate("document.body.scrollHeight")
    if curr_height == prev_height:
        break
    prev_height = curr_height
```

## Anti-Bot Defense Bypass

### Common Protections
Cloudflare, Akamai, PerimeterX, DataDome. Detection methods: browser fingerprinting, TLS fingerprint, behavior analysis, rate limiting.

### Stealth Techniques
```python
# Use real user agents
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
]

# Emulate realistic device
context = await browser.new_context(
    user_agent=random.choice(user_agents),
    viewport={"width": 1280, "height": 720},
    locale="en-US"
)

# Add human-like delays
import time, random
time.sleep(random.uniform(1, 3))

# Avoid detection: scroll, move mouse, randomize actions
await page.evaluate("window.scrollBy(0, window.innerHeight)")
```

### FlareSolverr (Cloudflare Solver)
Use when Cloudflare blocks headless browsers. Run as Docker service, proxy requests through it.
```bash
docker run -p 8191:8191 ghcr.io/flaresolverr/flaresolverr
```
Send requests to `http://localhost:8191/v1/` with target URL, get back HTML and cookies.

### Proxy Rotation
Rotate IP addresses to avoid rate limiting. Use residential proxies (datacenter IPs are easily detected).
```python
proxies = ["http://proxy1:8080", "http://proxy2:8080"]
context = await browser.new_context(proxy={"server": random.choice(proxies)})
```

## Docker Deployment
```yaml
services:
  playwright:
    image: mcr.microsoft.com/playwright:v1.42.0-jammy
    volumes:
      - ./scripts:/app
    working_dir: /app
    command: python scrape.py

  flaresolverr:
    image: ghcr.io/flaresolverr/flaresolverr:latest
    ports:
      - "8191:8191"
```

## E2E Testing Patterns

**Page Object Model**: Abstract page interactions into classes. Encapsulates selectors and actions.

**Test isolation**: Each test gets fresh context (new cookies, storage). Use fixtures/setup/teardown.

**Visual regression**: Capture screenshots between test runs, compare with baseline.

**Accessibility testing**: Integrate axe-core into tests to catch WCAG violations.

**CI integration**: Run headless in GitHub Actions using Playwright's Docker image.

## Page Monitoring

Schedule Playwright to periodically check pages and alert on changes.
```python
# Schedule: cron job or APScheduler
# Extract: Playwright fetches page
# Compare: new content vs stored snapshot
# Alert: send to Discord/Slack on change
# Store: keep historical snapshots
```

Why: detect price changes, availability updates, new content, status changes.

## Ethical Scraping

- **Respect robots.txt**: check before scraping
- **Rate limit**: add delays between requests (don't hammer servers)
- **Identify yourself**: use descriptive user agent with contact info
- **Cache aggressively**: don't re-fetch pages you already have
- **Check ToS**: some sites explicitly prohibit scraping
- **Personal data**: don't scrape without legitimate purpose
- **Prefer APIs**: more reliable and respectful

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Element not found | Page not fully loaded. Use explicit waits, verify selectors in DevTools |
| Timeout errors | Increase timeout, check if page needs interaction before content loads |
| Cloudflare block | Use FlareSolverr, add stealth patches, check TLS fingerprint |
| Memory issues | Close pages/contexts after use, limit concurrent browser instances |
| Flaky tests | Avoid hardcoded waits, use element-based waits, implement retry logic |
| Headless detection | Test with `headless=False`, compare behavior, add stealth patches |
| Docker failures | Use official Playwright image (includes all browser dependencies) |

## Resources

- Playwright docs: https://playwright.dev
- Puppeteer docs: https://pptr.dev
- Selenium docs: https://selenium.dev
- BeautifulSoup: https://www.crummy.com/software/BeautifulSoup
- Scrapy: https://scrapy.org
- FlareSolverr: https://github.com/FlareSolverr/FlareSolverr
