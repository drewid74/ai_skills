---
name: content-strategy
description: "Use this skill whenever the user wants to write, plan, or optimize any form of content — technical documentation, blog posts, README files, marketing copy, email campaigns, social media, presentations, or any other written deliverable. Triggers include: any mention of 'write', 'blog post', 'article', 'documentation', 'docs', 'README', 'changelog', 'release notes', 'tutorial', 'guide', 'how-to', 'copywriting', 'copy', 'landing page', 'email', 'newsletter', 'social media', 'tweet', 'LinkedIn post', 'content calendar', 'content plan', 'editorial', 'SEO', 'keywords', 'meta description', 'headline', 'title tag', 'technical writing', 'API documentation', 'developer docs', 'onboarding docs', 'runbook', 'playbook', 'ADR', 'RFC', 'proposal', 'white paper', 'case study', 'press release', 'announcement', 'product description', 'microcopy', 'UX writing', 'error messages', 'tone of voice', 'style guide', 'brand voice', or any request to create, edit, or improve written content for any audience. Also use when the user says 'help me write', 'make this clearer', 'review my docs', or needs to communicate something effectively in writing. If someone needs to put words on a page for any purpose, use this skill."
---

# Content Strategy and Technical Writing

Patterns for creating effective content across technical documentation, developer experience writing, marketing, and communications. Covers writing principles, format-specific guidance, SEO, and content systems.

## Writing Principles (Universal)

### Clarity First
- One idea per sentence, one topic per paragraph
- Active voice over passive: "The server processes the request" not "The request is processed by the server"
- Concrete over abstract: "reduces load time by 40%" not "significantly improves performance"
- Cut filler words: "In order to" → "To", "It is important to note that" → delete it
- Front-load important information (inverted pyramid): conclusion first, details after

### Know Your Audience
- **Developers**: precision matters, show code, skip marketing fluff, link to API refs
- **End users**: focus on tasks ("how to..."), avoid jargon, use screenshots/visuals
- **Executives**: lead with impact (cost, revenue, risk), bullet points, no technical deep-dives
- **Mixed**: layer information (summary → details → appendix) so each audience gets what they need

### Structure for Scannability
- Clear headings that describe content (not clever wordplay)
- Short paragraphs (3-5 sentences max)
- Lists for sequences and options (prose better for narrative)
- Bold key terms on first use or for emphasis (sparingly)
- Code blocks for technical content, commands, file paths

## Technical Documentation

### README.md Pattern
Every project README answers these questions in order:
1. **What is this?** (one sentence)
2. **Why should I care?** (problem it solves)
3. **How do I get started?** (quickstart: install → configure → run)
4. **How do I use it?** (basic usage examples)
5. **How do I configure it?** (environment variables, config files)
6. **How do I contribute?** (link to CONTRIBUTING.md)
7. **License** (one line)

Template structure: heading, description paragraph, Quick Start code block, usage examples with code, configuration table, link to contributing, license line.

### API Documentation
- Every endpoint: method, path, description, parameters, request body, response, error codes
- Include: authentication requirements, rate limits, pagination
- Real examples: show actual request/response JSON (not just schema)
- Auto-generate from code when possible (FastAPI, OpenAPI/Swagger)
- Keep examples up to date (test them in CI)

### Runbooks and Playbooks
Purpose: enable someone unfamiliar to handle a known scenario.
- Trigger: when to use this runbook
- Context: background needed to understand the situation
- Procedure: numbered steps, exact commands, no ambiguity (write for 3am brain)
- Verification: how to confirm the fix worked
- Escalation: when to involve others
Link every alert to its runbook.

### Architecture Decision Records (ADRs)
Structure: Status (Accepted/Proposed/Deprecated) → Context (why we needed to decide) → Decision (what we chose) → Consequences (pros and cons).
Why: creates decision history, prevents re-debating, onboards new team members.

### Changelogs
Follow [Keep a Changelog](https://keepachangelog.com/) format.
- Sections: Added, Changed, Deprecated, Removed, Fixed, Security
- Write for users, not commit hashes ("Fixed bug where passwords weren't hashed" not "Update auth.py line 45")
- Link to PRs/issues for context
- Auto-generate from conventional commits where possible

## Developer Experience Writing

### Error Messages
Say what went wrong, why, and how to fix it:
- Bad: `Error: ENOENT`
- Good: `File not found: config.yaml. Create it by copying config.example.yaml, or set CONFIG_PATH to your config file.`

Include: error, cause, fix, optionally a docs link. Tone: helpful, not blaming.

### CLI Help Text
- First line: what the command does (one sentence)
- Usage pattern: `command [options] <required> [optional]`
- Options: short and long form with description
- Examples: 2-3 real-world usages (most useful part)

### Onboarding Documentation
Goal: new developer goes from zero to productive in under a day.
- Prerequisite checks
- Step-by-step setup
- Architecture overview
- Where things live in the codebase
- Common tasks (running tests, starting the server, deploying)
- Who to ask for help

Test it with an actual new person and fix where they get stuck. Stale onboarding docs waste time AND erode trust.

## Blog Posts and Articles

### Structure
1. **Hook** (1-2 sentences): state the problem or insight
2. **Context**: why this matters, who it's for
3. **Body**: solutions, explanations, code, examples
4. **Takeaway**: what the reader should do next

### Technical Blog Posts
- Show, don't just tell: include code, screenshots, terminal output
- Working examples: reader should be able to follow along and get results
- Be honest about tradeoffs: "Works well for X but not Y"
- Link to sources: credit prior work and documentation

### Headlines
- Specific > vague: "How I Reduced Docker Build Time from 10 Minutes to 45 Seconds" beats "Making Docker Faster"
- Promise value: what does the reader gain?
- Include keywords naturally: use terms people would actually search for

## SEO for Technical Content

### On-Page SEO
- **Title tag**: primary keyword near front, under 60 characters
- **Meta description**: 150-160 characters, includes primary keyword, summarizes page
- **H1**: one per page, matches the topic
- **Headings (H2, H3)**: logical hierarchy, related keywords naturally integrated
- **Internal links**: link to related content on your own site
- **Alt text**: describe images for accessibility and search engines

### Technical SEO for Docs Sites
- Canonical URLs: prevent duplicate content from versioned docs
- Sitemap.xml: auto-generate, submit to search console
- robots.txt: block staging/preview environments
- Page speed: docs sites should load in under 2 seconds (static site generators help)
- Mobile-friendly: developers read docs on phones too

### Keyword Research
- Answer questions people actually ask (Google autocomplete, "People Also Ask", StackOverflow)
- Long-tail keywords: "how to set up Prometheus monitoring for Docker containers" over "monitoring"
- One primary topic per page (don't dilute focus)
- Update existing content rather than creating near-duplicate pages

## Email and Newsletters

### Principles
- Subject line: clear value, under 50 characters, no clickbait
- One CTA (call to action) per email: what do you want them to do?
- Scannable: short paragraphs, bold key info, TL;DR at top for long emails
- Personalization: segment audience, relevant content beats mass blasts
- Plain text version: some prefer it, avoids spam filters

### Developer Newsletter
- Frequency: weekly or bi-weekly (balance between staying top-of-mind and unsubscribe risk)
- Format: curated links + commentary + one original insight
- Value: filter signal from noise, save the reader time

## Social Media for Technical Audiences

### Twitter/X and LinkedIn
- Tweet threads: break into numbered steps, each tweet has standalone value
- Show results: screenshots, demos, before/after
- Ask questions: drives engagement and visibility
- LinkedIn: longer-form, professional context, project updates, career insights
- Avoid: pure self-promotion, engagement bait, controversy for attention

## Content Systems

### Documentation Platforms
- **MkDocs (Material theme)**: Python-based, Markdown, great search, easy setup. Best for most projects.
- **Docusaurus**: React-based, versioned docs, blog integration. Best for large projects, React ecosystem.
- **Astro Starlight**: modern, fast, Markdown/MDX. Best for new projects prioritizing performance.
- **GitBook**: hosted, WYSIWYG + Markdown, collaboration. Best for teams wanting low-maintenance.
- Deploy to: GitHub Pages, Cloudflare Pages, or self-hosted (Nginx/Caddy)

### Style Guides
Define and document:
- Tone (formal/casual), voice (we/you/passive), terminology (pick one term per concept, stick with it)
- Formatting standards, code example style, heading conventions
- Enforce with linting (Vale for prose, markdownlint for Markdown) in CI
- Reference: Google developer documentation style guide is excellent

### Content Calendar
- Plan quarterly or monthly (prevents reactive scrambling)
- Mix content types: tutorials (traffic), announcements (engagement), deep dives (authority)
- Workflow: outline → draft → review → publish → promote → measure
- Track: page views, time on page, bounce rate (not just "did we publish?")

## Troubleshooting

- **Writer's block**: start with outline (headings only), fill in easiest section first
- **Too long**: cut draft by 30% — you'll almost always improve it
- **Too technical**: read aloud — if you stumble, simplify
- **Stale docs**: automate (auto-generated API docs, CI-tested examples), schedule quarterly reviews
- **Low engagement**: lead with value (what reader gets), not setup (what you did)
- **SEO not working**: check if content is actually good, answers real questions. Give 3-6 months before judging.
