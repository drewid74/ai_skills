---
name: gws-assistant-pro
description: "Use this skill for managing Google Workspace (Gmail, Sheets, Calendar, Drive). Triggers: 'email', 'Gmail', 'draft', 'inbox', 'calendar', 'meeting', 'schedule', 'appointment', 'spreadsheet', 'Sheets', 'Google Docs', 'Drive', 'sync data', 'send report', 'check availability', or 'organize my day'."
---

# Google Workspace Operational Playbook

## Overview
Bridge the gap between raw data and professional communication. This skill automates the administrative overhead of a business or personal "Life Engine."

## Available GWS MCP Tools
- **Gmail**: `list_messages`, `get_thread`, `create_draft`, `send_message`, `search_emails`
- **Calendar**: `list_events`, `create_event`, `update_event`, `check_availability`
- **Sheets**: `read_spreadsheet`, `update_values`, `append_row`, `create_spreadsheet`

## Communication Workflow
1. **Context Retrieval**: Use `search_emails` to find the last 3 relevant interactions before drafting.
2. **Tone Matching**: Draft in a "Professional-Concise" tone unless the user's history suggests otherwise.
3. **Drafting**: Create a draft with `create_draft` first; do NOT send without explicit 1:1 human confirmation.

## Scheduling Strategy
1. **Availability**: Use `check_availability` across the next 3 business days to find optimal slots.
2. **Buffer Rules**: Never schedule meetings back-to-back. Automatically insert 15m "Transition" blocks.
3. **Invites**: Every calendar event must include a "Purpose" and "Agenda" in the description.

## Compound Operations
- **Inbox Triage**: Summarize unread emails from the last 24 hours and suggest priority draft replies.
- **Report Sync**: Extract data from a technical log/file and format it into a structured Google Sheet table.
- **Daily Briefing**: Cross-reference Calendar and Gmail to provide a morning "Agenda Summary" of commitments.

## Output Format
- Confirm tool execution with direct links to Drafts or Sheets where possible.
- Provide a clear summary of the action taken (e.g., "Draft created for William regarding the UAS battery specs").