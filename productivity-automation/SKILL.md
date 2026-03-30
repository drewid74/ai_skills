---
name: productivity-automation
description: "Use this skill whenever the user wants to automate recurring tasks, manage files and data, schedule things, process batches of files, create productivity workflows, or organize information. Triggers include: any mention of 'automate', 'schedule', 'recurring', 'batch', 'organize files', 'rename files', 'convert files', 'backup', 'monitor', 'alert', 'reminder', 'cron', 'daily task', 'weekly report', 'cleanup', 'archive', or requests to process multiple files, transform data between formats, set up monitoring, or create any kind of repeating workflow. Also use when the user asks to 'set up something that runs every...', 'check on X periodically', 'keep track of', or wants to build any kind of personal automation pipeline."
---

# General Productivity & Automation Skill

## Overview

Help users build personal automation workflows: scheduled tasks, file processing pipelines, data transformation, monitoring, and recurring operations. Leverages scheduled tasks, shell scripting, and file tools to create robust personal automations.

## Scheduled Task Creation

Use the `create_scheduled_task` MCP tool for anything that should run automatically.

### Cron Expression Quick Reference
Cron is in LOCAL time (not UTC). Format: `minute hour dayOfMonth month dayOfWeek`

| Schedule | Expression | Notes |
|----------|-----------|-------|
| Every day at 9 AM | `0 9 * * *` | |
| Weekdays at 8:30 AM | `30 8 * * 1-5` | Mon-Fri |
| Every Monday at 9 AM | `0 9 * * 1` | |
| Every 6 hours | `0 */6 * * *` | At :00 past the hour |
| First of month at midnight | `0 0 1 * *` | |
| Every Sunday at 6 PM | `0 18 * * 0` | |

### Task Prompt Best Practices

When writing the `prompt` for a scheduled task, make it self-contained and explicit:

1. **State the goal clearly**: "Check if service X is responding and report status"
2. **Include all context**: File paths, URLs, expected values — the task runs in a fresh session
3. **Define success/failure**: What should happen in each case
4. **Specify output**: Where to save results, whether to notify

**Example prompt for a monitoring task**:
```
Check if my home server at https://myserver.example.com is responding.
If it returns HTTP 200, log "OK" with timestamp to /path/to/uptime.log.
If it fails or returns non-200, log "DOWN" with the error and timestamp.
```

### One-Time Tasks (Reminders)
Use `fireAt` with ISO 8601 timestamp for one-shot tasks:
```
fireAt: "2026-04-01T14:30:00-05:00"
```
The task fires once and auto-disables. Great for reminders and future actions.

## File Processing Workflows

### Batch File Operations

**Rename patterns**: When the user wants to rename files in bulk:
- Use Glob to find files matching a pattern
- Use Bash for `mv` operations with shell parameter expansion
- Always show the rename plan first, execute after confirmation

**Format conversion**: Common patterns:
- Images: Use ImageMagick (`convert`, `mogrify`) or Python Pillow
- Documents: pandoc for markdown/docx/html/pdf conversion chains
- Data: Python pandas for CSV/Excel/JSON transformations
- Media: ffmpeg for audio/video conversion

**File organization**: When sorting files into directories:
1. Glob to inventory what exists
2. Build a mapping (file → destination) based on rules (date, type, name pattern)
3. Present the plan as a table
4. Execute moves after confirmation

### Data Transformation Pipelines

When the user needs to regularly process data:

1. **Input**: Define the source (file, URL, API, database)
2. **Transform**: Script the processing (Python, jq, awk, etc.)
3. **Output**: Define the destination (file, email, notification)
4. **Schedule**: Wrap in a scheduled task if recurring

**Common transforms**:
- CSV → filtered/aggregated CSV
- JSON API → formatted report
- Log files → summary statistics
- Multiple files → merged single file

## Monitoring & Alerting

### Health Check Patterns

**Website/service monitoring**: Scheduled task that checks HTTP status codes and response times.

**Disk space monitoring**: Check available space and warn when below threshold.

**Container health**: Check Docker container status, restart counts, resource usage.

**SSL certificate expiry**: Check cert dates and warn before expiration.

### Alert Delivery Options
Since we're in a Claude session, alerting options include:
- Write to a log file that another system watches
- Trigger a webhook (if user has one configured)
- Save a report that the user reviews
- Use Open Brain to capture important findings (if connected)

## Backup Automation

### Backup Strategy Template

```
Prompt for scheduled backup task:

1. Run rsync from /source to /backup/$(date +%Y-%m-%d)/
2. Verify the backup completed (check exit code and file count)
3. Remove backups older than 30 days
4. Log results to /backup/backup.log with timestamp
5. If any step fails, log the error clearly
```

### Backup Best Practices
- **3-2-1 rule**: 3 copies, 2 different media, 1 offsite
- **Test restores**: Schedule periodic restore tests
- **Incremental**: Use rsync or restic for efficient incremental backups
- **Databases**: Always dump to SQL before file-level backup

## Workflow Templates

### Daily Summary
A scheduled task that runs each morning:
- Check server status
- Summarize yesterday's activity
- Flag anything that needs attention
- Save as a readable report

### Weekly Cleanup
A weekly task that:
- Removes old temp files
- Archives completed project folders
- Rotates logs
- Reports disk usage

### File Watch Pattern
Check a directory for new files and process them:
- Scheduled every N minutes
- Look for files matching a pattern in a drop folder
- Process each new file (convert, move, rename)
- Log what was processed

## Output Format

When creating automations:
1. Show the complete task configuration before creating it
2. Explain what it will do in plain language
3. Test the logic manually first when possible
4. Provide instructions for checking task status with `list_scheduled_tasks`
5. Mention how to pause/modify with `update_scheduled_task`
