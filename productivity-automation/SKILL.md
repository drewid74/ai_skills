---
name: productivity-automation
description: >-
  Build personal and team productivity systems. Email triage and drafting,
  calendar management, spreadsheet automation, Zapier/n8n workflow design,
  note-taking pipelines, and compound operations that reduce manual overhead.
triggers:
  - "automate my email workflow"
  - "set up daily briefing"
  - "organize my calendar"
  - "build a productivity system"
  - "automate repetitive task"
  - "create workflow automation"
  - "sync data between tools"
  - "triage inbox"
tags: [automation, productivity, email, calendar, n8n, zapier, workflow]
author: merged
---

# Productivity Automation

## Identity

Eliminate repetitive manual work. Every automation must be reversible and auditable. Draft before send. Always surface final output to human before taking irreversible action (send, delete, publish).

## Stack Defaults

| Use Case | Default Tool | Notes |
|----------|-------------|-------|
| Visual workflow automation | n8n (self-hosted) | 400+ integrations |
| Cloud automation | Zapier | For non-technical users |
| Email | Gmail + n8n/Zapier | Draft-before-send always |
| Calendar | Google Calendar API | Buffer time between meetings |
| Spreadsheets | Google Sheets + n8n | Append, read, update values |
| Notes/knowledge | Obsidian + periodic review | Markdown, no vendor lock-in |
| Task management | Todoist / Linear API | Webhook-triggered creation |

## Decision Framework

```
IF automating email:
  → ALWAYS create_draft first, NEVER send directly
  → Search last 3 messages with recipient before drafting (match tone)
  → Require explicit human confirmation before sending

IF scheduling meetings:
  → Check availability first
  → Insert 15-min buffer between consecutive events
  → Every event needs Purpose + Agenda in description

IF syncing data between tools:
  → Define trigger (webhook, schedule, or manual)
  → Transform data to target schema before writing
  → Log operation: what was written, when, by which workflow

IF automation fails:
  → n8n: configure error workflow with notification
  → Zapier: enable task history; set "Zapier's action failed" email
  → Never silent-fail on writes (email sends, calendar creates)

IF choosing automation platform:
  → Self-hosted, high sensitivity/volume → n8n
  → Quick setup, non-technical user → Zapier
  → Complex code needed → Python script with cron
```

## Anti-Patterns

| Anti-Pattern | Use Instead |
|--------------|-------------|
| Sending emails without human review | Draft → human approval → send |
| Polling APIs every 5 seconds | Webhooks or scheduled runs (≥1 min) |
| Storing credentials in workflow JSON | Environment variables or vault |
| Automating without error notification | Error workflow with Slack/email alert |
| Scheduling meetings back-to-back | 15-min buffer blocks between events |
| One mega-workflow for everything | Modular workflows with clear single purpose |

## Quality Gates

- [ ] No automation sends email without explicit human confirmation step
- [ ] All credentials stored as n8n credentials or env vars (not inline)
- [ ] Error workflow configured for every production flow
- [ ] Workflow changes logged/versioned (n8n version history or Git export)
- [ ] Operations that write or send are logged with timestamp
- [ ] Automation has "off switch" — can be disabled without code change

→ See `service-integration` for n8n compose setup, Traefik labels  
→ See `github-workflow` for GitHub MCP compound operations  
→ See `gws-assistant-pro` for Google Workspace-specific patterns

---

## Email Workflow Patterns

### Pre-Draft Research

Before drafting any email, retrieve context:

```
1. Search last 3 messages from this recipient
2. Extract: their tone (formal/casual), recent context, pending items
3. Match draft tone to established pattern
4. Include context reference ("Following up on our Tuesday discussion about X...")
```

### Draft Template

```
Subject: [Action Required / FYI / Question] - Brief topic

Hi [Name],

[1-line context anchor — why you're writing]

[Core ask or information — be specific]

[Next steps with owner and due date if applicable]

[Closing appropriate to relationship]
```

### Inbox Triage Automation (n8n flow)

```
Trigger: Schedule - daily at 8am
  → Gmail: List unread messages from last 24h
  → n8n: Code node — classify each by: action-required, FYI, newsletter
  → Slack: Send summary with counts and subject lines
  → Gmail: Label newsletters automatically ("Auto-Newsletter")
  → Create draft replies for action-required items (human reviews before sending)
```

## Calendar Management

### Event Template

Every event should have:

```
Title: [Meeting Type] - Topic
Duration: [15 / 30 / 60 min]

Description:
  Purpose: Why this meeting exists
  Agenda:
    - Item 1 (5 min)
    - Item 2 (15 min)
    - Item 3 (10 min)
  Outcome: What "done" looks like
  Pre-read: [link or "none"]
```

### Buffer Block Pattern

```python
# Detect back-to-back meetings and insert buffers
import datetime
from googleapiclient.discovery import build

def add_transition_buffers(events: list) -> list:
    """Insert 15-min 'Transition' blocks between consecutive events."""
    buffers = []
    for i in range(len(events) - 1):
        end_time = events[i]["end"]["dateTime"]
        next_start = events[i+1]["start"]["dateTime"]

        gap = datetime.fromisoformat(next_start) - datetime.fromisoformat(end_time)
        if gap < datetime.timedelta(minutes=15):
            buffers.append({
                "summary": "⏱️ Transition",
                "start": {"dateTime": end_time},
                "end": {"dateTime": (datetime.fromisoformat(end_time) +
                        datetime.timedelta(minutes=15)).isoformat()},
                "colorId": "8"  # Graphite
            })
    return buffers
```

## Spreadsheet Automation

### Common Operations (Google Sheets + n8n)

```javascript
// n8n Code node: Transform data before sheet write
const rows = items.map(item => ({
  timestamp: new Date().toISOString(),
  source: item.json.source,
  title: item.json.title.substring(0, 100),
  status: item.json.status || "pending",
  link: item.json.url
}));

return rows.map(row => ({ json: row }));
```

### Append Row Pattern

```
Trigger: Webhook (from other service)
  → Code: Parse and validate payload
  → Google Sheets: Append Row
    Sheet: "Operations Log"
    Values: [timestamp, source, action, status, notes]
  → Slack: Notify "Logged: {action} from {source}"
```

## Daily Briefing Workflow

```
Trigger: Schedule - daily 7:30am
  → Google Calendar: List today's events
  → Gmail: Unread from last 12h
  → Linear/GitHub: Assigned open issues/PRs
  → n8n Code: Build briefing markdown
  → Slack: Post to #daily-briefing
  
Output format:
  📅 Today: [date]
  
  CALENDAR (N events):
  - 9:00 Team standup
  - 14:00 Sync with [name]
  
  EMAIL (N unread):
  - [Subject] from [Sender] — [1-line summary]
  
  OPEN WORK:
  - PR: [title] (waiting review)
  - Issue: [title] (assigned, in progress)
```

## Report Sync Pattern

```
Trigger: Schedule or manual
  → Source: Read file / API / database
  → Transform: Extract relevant columns, compute summaries
  → Google Sheets: Create or update spreadsheet
    - Sheet 1: Raw data (append)
    - Sheet 2: Summary (overwrite)
    - Apply formatting: header row bold, alternating rows
  → Email: Send "Report updated" notification with link
```

## n8n Workflow Export/Backup

```bash
# Export all workflows to Git-versioned JSON
n8n export:workflow --all --output=backups/workflows/

# Import on new instance
n8n import:workflow --input=backups/workflows/

# Backup as part of weekly automation
# n8n Code node to call n8n API:
GET http://n8n:5678/api/v1/workflows
# Then save response to Git via GitHub API
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| n8n webhook not firing | Workflow not active | Toggle "Active" switch; verify URL |
| Google Sheets auth fails | OAuth token expired | Re-authenticate credential in n8n |
| Calendar event has no buffer | Buffer workflow not running | Check schedule trigger is active |
| Draft sent without approval | "Send" node before human review | Replace with "Create Draft" → manual step |
| Workflow runs but no notification | Error in notification node | Check error workflow is set; test Slack integration |
| Data duplicated in sheet | Trigger firing multiple times | Add dedup check: query sheet for existing row before append |
