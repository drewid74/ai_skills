# Claude Desktop (Cowork) — Complete Capabilities Catalog

> Generated: 2026-03-30 | Purpose: Master reference for all available tools, MCPs, skills, and triggers

---

## 0. Subscription Tier Summary

| Feature | Free | Pro ($20/mo) | Max 5x ($100/mo) | Max 20x ($200/mo) | Team ($30/user/mo) | Enterprise |
|---------|------|-------------|-------------------|--------------------|--------------------|-----------|
| **Cowork mode** | No | Yes | Yes | Yes | Yes | Yes |
| **Claude Code** | No | Yes | Yes | Yes | Yes | Yes |
| **Extended thinking** | No | Yes | Yes | Yes | Yes | Yes |
| **MCP connectors** | Basic only | Full | Full | Full | Full | Full |
| **Skills** | No | Yes | Yes | Yes | Yes | Yes |
| **Plugins** | No | Yes | Yes | Yes | Yes | Yes |
| **Scheduled tasks** | No | Yes | Yes | Yes | Yes | Yes |
| **Claude in PowerPoint** | No | No | Yes (Max-only) | Yes (Max-only) | TBD | TBD |
| **Priority access** | No | No | Yes | Yes | No | Yes |
| **Early feature access** | No | No | Yes | Yes | No | Yes |
| **Context window** | 200K | 200K | 200K | 200K | 200K | 200K |
| **Usage quota** | Limited | Baseline | 5x Pro | 20x Pro | ~Pro level | Custom |

**Key points**: Pro unlocks all core capabilities (Cowork, skills, MCP, Claude Code). Max only adds more usage quota + priority queue + early access. No tools or skills are gated behind Max — they all work on Pro. The only Max-exclusive feature currently is Claude in PowerPoint (research preview).

---

## 1. Built-in Core Tools

These are always available in every session.

| Tool | Triggers / When Used | What It Does |
|------|---------------------|--------------|
| **Read** | Read any file by path | Reads files (text, images, PDFs, notebooks) from the workspace |
| **Write** | Create new files, complete rewrites | Writes/overwrites a file at a given path |
| **Edit** | Modify existing files surgically | Find-and-replace edits within a file |
| **Bash** | Run shell commands, install packages, scripts | Executes commands in a sandboxed Linux shell |
| **Glob** | Find files by pattern (e.g. `**/*.py`) | Fast file pattern matching across any codebase |
| **Grep** | Search file contents by regex | Ripgrep-powered content search with context |
| **Agent** | Complex multi-step tasks, parallel research | Spawns sub-agents for autonomous work |
| **WebSearch** | Current events, recent info, lookups | Searches the web and returns results with sources |
| **WebFetch** | Retrieve and analyze a specific URL | Fetches a URL, converts to markdown, processes with AI |
| **AskUserQuestion** | Clarify requirements, gather preferences | Presents multiple-choice questions to the user |
| **TodoWrite** | Track multi-step task progress | Creates/updates a visible task checklist |
| **NotebookEdit** | Edit Jupyter .ipynb cells | Replaces, inserts, or deletes notebook cells |
| **RemoteTrigger** | Create/manage/run remote triggers | Calls the claude.ai remote-trigger API |
| **Skill** | Invoke a loaded skill by name | Executes a skill's specialized workflow |
| **ToolSearch** | Discover deferred tools | Fetches schema definitions for tools not yet loaded |

---

## 2. Existing Skills (Pre-installed)

These are loaded from `/mnt/.claude/skills/` and trigger automatically based on their descriptions.

| Skill | Triggers | What It Does |
|-------|----------|--------------|
| **docx** | "Word doc", "word document", ".docx", "report", "memo", "letter", "template" as Word file | Create, read, edit, manipulate .docx files with full formatting |
| **pdf** | "PDF", ".pdf", "form", "extract", "merge", "split" | Extract text/tables, create PDFs, merge/split, handle forms |
| **pptx** | "deck", "slides", "presentation", ".pptx", "pitch deck" | Create, read, edit, combine PowerPoint presentations |
| **xlsx** | "Excel", "spreadsheet", ".xlsx", "data table", "budget", "financial model", "chart", "graph", "tabular data" | Create/edit Excel files with formulas, formatting, charts |
| **schedule** | "scheduled task", "recurring", "on an interval", "run automatically" | Create scheduled tasks that run on cron or one-time |
| **skill-creator** | "create a skill", "make a skill", "edit skill", "optimize skill", "run evals", "benchmark skill" | Meta-skill for building and testing new skills |

---

## 3. MCP Servers — Desktop Commander

Local system access via the Desktop Commander MCP. All can be referenced as "DC: ..." or "use Desktop Commander to ...".

### File Operations
| Tool | Triggers | What It Does |
|------|----------|--------------|
| **read_file** | Read local files, PDFs, Excel, URLs | Read with pagination (offset/length), supports many formats |
| **read_multiple_files** | Read several files at once | Batch file reading including images |
| **write_file** | Write/append to files | Write in chunks (25-30 lines), supports Excel/DOCX creation |
| **write_pdf** | Create or modify PDFs | Markdown-to-PDF creation, page insert/delete/merge |
| **edit_block** | Surgical edits to files | Find/replace for text, XML editing for DOCX, range updates for Excel |
| **move_file** | Move or rename files | Move/rename within allowed directories |
| **create_directory** | Make new folders | Create nested directories |
| **get_file_info** | File metadata | Size, timestamps, permissions, line count, Excel sheet info |
| **list_directory** | Browse directory contents | Recursive listing with depth control, [FILE]/[DIR] prefixes |

### Process Management
| Tool | Triggers | What It Does |
|------|----------|--------------|
| **start_process** | Run commands, start REPLs | Launch terminal processes with state detection |
| **interact_with_process** | Send input to running process | Interactive REPL communication (Python, Node, etc.) |
| **read_process_output** | Check process output | Paginated output reading with smart detection |
| **list_sessions** | See active terminals | Show PIDs, blocked status, runtime |
| **list_processes** | See all running processes | PID, command, CPU/memory usage |
| **force_terminate** | Kill a terminal session | Force-stop a running session |
| **kill_process** | Kill any process by PID | Terminate any process |

### Search
| Tool | Triggers | What It Does |
|------|----------|--------------|
| **start_search** | Find files or search content | Streaming search with file/content modes |
| **get_more_search_results** | Paginate search results | Offset-based pagination for active searches |
| **list_searches** | See active searches | Show search IDs, status, runtime |
| **stop_search** | Cancel a search | Gracefully stop a running search |

### Configuration & Meta
| Tool | Triggers | What It Does |
|------|----------|--------------|
| **get_config** | View DC settings | Shell, allowed dirs, limits, version, system info |
| **set_config_value** | Change DC settings | Modify blocked commands, shell, directories, limits |
| **get_usage_stats** | DC analytics | Tool usage, success/failure rates, performance |
| **get_recent_tool_calls** | Session history | Chronological tool call log (last 1000) |
| **get_prompts** | DC onboarding prompts | Retrieve and execute onboarding workflows |
| **give_feedback_to_desktop_commander** | Give DC feedback | Opens feedback form in browser |

---

## 4. MCP Servers — GitHub

Full GitHub API access. Requires repository owner/repo for most operations.

### Repository Operations
| Tool | Triggers | What It Does |
|------|----------|--------------|
| **create_repository** | Create new repo | New GitHub repo with optional README |
| **fork_repository** | Fork a repo | Fork to your account or an org |
| **search_repositories** | Find repos | Search GitHub repositories |
| **get_file_contents** | Read repo files | Get file/directory contents from a repo |
| **create_or_update_file** | Edit repo files | Create or update a single file with commit |
| **push_files** | Push multiple files | Multi-file push in a single commit |
| **create_branch** | New branch | Create branch from any source |
| **list_commits** | View commit history | List commits on a branch |

### Issues
| Tool | Triggers | What It Does |
|------|----------|--------------|
| **create_issue** | Open new issue | Create issue with labels, assignees, milestone |
| **get_issue** | View issue details | Get specific issue info |
| **list_issues** | Browse issues | Filter by state, labels, sort |
| **update_issue** | Modify issue | Change title, body, state, labels, assignees |
| **add_issue_comment** | Comment on issue | Add a comment to an existing issue |
| **search_issues** | Search issues/PRs | Search across all GitHub repos |

### Pull Requests
| Tool | Triggers | What It Does |
|------|----------|--------------|
| **create_pull_request** | Open new PR | Create PR with title, body, head/base branches |
| **get_pull_request** | View PR details | Get specific PR info |
| **list_pull_requests** | Browse PRs | Filter by state, sort, base/head branch |
| **get_pull_request_files** | See PR changes | List files changed in a PR |
| **get_pull_request_comments** | Read PR comments | Get review comments |
| **get_pull_request_reviews** | See PR reviews | Get all reviews on a PR |
| **get_pull_request_status** | Check CI status | Combined status of all checks |
| **create_pull_request_review** | Review a PR | Approve, request changes, or comment |
| **merge_pull_request** | Merge a PR | Merge, squash, or rebase |
| **update_pull_request_branch** | Update PR branch | Sync with base branch |

### Users
| Tool | Triggers | What It Does |
|------|----------|--------------|
| **search_users** | Find GitHub users | Search by username, sort by followers/repos/joined |
| **search_code** | Search code on GitHub | Search code across repositories |

---

## 5. MCP Servers — Supabase

Database and backend management for Supabase projects.

| Tool | Triggers | What It Does |
|------|----------|--------------|
| **execute_sql** | Run SQL queries | Execute raw SQL on Postgres |
| **apply_migration** | DDL changes | Apply named migrations |
| **list_tables** | View schema | List tables with optional column details |
| **list_migrations** | View migration history | All applied migrations |
| **list_extensions** | View Postgres extensions | All installed extensions |
| **create_branch** | Dev branch | Create development branch (fresh DB) |
| **list_branches** | View branches | All dev branches with status |
| **merge_branch** | Merge to production | Merge migrations + edge functions |
| **rebase_branch** | Sync with production | Apply newer production migrations to branch |
| **reset_branch** | Reset branch | Reset to specific migration version |
| **delete_branch** | Remove branch | Delete a dev branch |
| **deploy_edge_function** | Deploy serverless function | Deploy Deno-based edge function |
| **get_edge_function** | View function code | Retrieve edge function files |
| **list_edge_functions** | List all functions | All deployed edge functions |
| **get_logs** | View logs | Logs by service (api, postgres, auth, etc.) |
| **get_advisors** | Security/perf audit | Advisory notices for vulnerabilities and optimizations |
| **get_project_url** | Get API URL | Project's API endpoint |
| **get_publishable_keys** | Get API keys | Anon keys and publishable keys |
| **generate_typescript_types** | Generate types | TypeScript types from schema |
| **search_docs** | Search Supabase docs | GraphQL-based documentation search |

---

## 6. MCP Servers — Open Brain

Personal knowledge base with semantic search. Two instances available (same functionality).

| Tool | Triggers | What It Does |
|------|----------|--------------|
| **capture_thought** | "save this", "remember", "note that" | Save a thought with auto-generated embedding and metadata |
| **list_thoughts** | "what did I note", "recent thoughts" | List thoughts filtered by type, topic, person, time |
| **search_thoughts** | "what do I know about X" | Semantic search across all captured thoughts |
| **thought_stats** | "brain stats", "thought summary" | Totals, types, top topics, and people |

---

## 7. MCP Servers — Cowork Platform

Session and file management within the Cowork environment.

| Tool | Triggers | What It Does |
|------|----------|--------------|
| **present_files** | Share files with user | Display interactive file cards in chat |
| **request_cowork_directory** | Need file system access | Mount a folder from the user's computer |
| **allow_cowork_file_delete** | Delete operation fails | Request permission to delete files |

---

## 8. MCP Servers — Scheduled Tasks

Recurring and one-time automated task management.

| Tool | Triggers | What It Does |
|------|----------|--------------|
| **create_scheduled_task** | "schedule", "every day at", "remind me", "recurring" | Create cron, one-time, or manual tasks |
| **list_scheduled_tasks** | "what's scheduled", "my tasks" | List all tasks with state and timing |
| **update_scheduled_task** | "change schedule", "pause task", "update prompt" | Modify schedule, prompt, enabled state |

---

## 9. MCP Servers — Session Info

Inspect other Claude sessions.

| Tool | Triggers | What It Does |
|------|----------|--------------|
| **list_sessions** | "my sessions", "other chats" | List local sessions (most recent first) |
| **read_transcript** | "what happened in that session" | Read transcript of any session with smart waiting |

---

## 10. MCP Servers — Registry & Plugins

Discover and suggest new integrations.

| Tool | Triggers | What It Does |
|------|----------|--------------|
| **search_mcp_registry** | Need external service access | Search for available MCP connectors |
| **suggest_connectors** | Show unconnected MCPs to user | Display Connect buttons for available integrations |
| **search_plugins** | Need org-specific workflows | Search for installable plugin bundles |
| **suggest_plugin_install** | Recommend a plugin | Show plugin install banner |

---

## 11. Skill Anatomy Quick Reference

```
skill-name/
├── SKILL.md          ← Required. YAML frontmatter + markdown instructions
│   ├── name:         ← Skill identifier
│   ├── description:  ← Trigger conditions (be "pushy" — list many trigger phrases)
│   └── Body:         ← Step-by-step instructions (<500 lines ideal)
└── Optional resources/
    ├── scripts/      ← Executable code for deterministic tasks
    ├── references/   ← Docs loaded into context as needed
    └── assets/       ← Templates, icons, fonts
```

**Triggering**: Claude sees skill name + description in `available_skills`. Complex, multi-step queries trigger skills reliably. Simple one-step queries may be handled directly without skill invocation.

**Progressive Disclosure**: Metadata always in context (~100 words) → SKILL.md body loaded on trigger → Bundled resources read as needed.