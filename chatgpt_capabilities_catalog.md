1. Built-in Core Tools

These are the native tools I can call internally.

🧠 Core Reasoning (implicit)
Name: Internal language model reasoning
Trigger: Every prompt
What it does: Generates answers, analysis, planning, explanations
Tier: All tiers
🌐 Web Tool (web.run)
Trigger: When info may be outdated, location-based, or needs verification
What it does: Performs live web search, product lookup, local business search, and retrieves current info
Capabilities:
Fast search (general queries)
Slow search (deeper, more thorough)
Local business search (with user location)
Product search (shopping results)
Image search (for UI rendering)
Open webpages
Tier: Available in most tiers (may be limited in free vs paid depending on quotas)
🧮 Python Tool (python)
Trigger: Data analysis, calculations, file parsing, simulations
What it does: Runs Python code in a sandbox
Capabilities:
Dataframes (pandas)
File processing (CSV, Excel, JSON, etc.)
Math / statistics
Visualization (charts)
Tier: Typically paid tiers (Plus/Pro/Enterprise)
🧾 Canvas Tool (canmore)
Trigger: When creating/editing long documents or code
What it does: Creates a collaborative editing workspace
Capabilities:
Write/edit documents
Maintain structured long-form content
Code editing
Tier: Paid tiers primarily
🎨 Image Generation (dalle.text2im)
Trigger: When user asks for image generation
What it does: Generates images from text prompts
Tier: Paid tiers (limits vary)
👤 Account Creation (account_creation)
Trigger: Only when user explicitly wants to create an account
What it does: Handles passwordless signup flow
Tier: N/A (system utility)
💾 Memory Tool (bio)
Trigger: When saving user preferences or info
What it does: Stores persistent memory across sessions
Tier: Available depending on memory feature access (on/off)
2. Connected Integrations / Plugins / Extensions

Important: In this session, there are no active third-party integrations like:

GitHub
Google Drive / Docs / Sheets
Slack
Notion
Dropbox
External APIs
What exists conceptually:
OpenAI supports integrations in some environments (Enterprise, API-based agents, MCP systems)
But right now:
Available integrations: ❌ None connected
Plugin marketplace: ❌ Not exposed in this session
3. Automation & Scheduling
⏱️ Native Scheduling
Status: ❌ Not available
I cannot:
Run tasks later
Set reminders
Execute recurring jobs
Act in the background
🧠 Workaround
I can help you design:
Cron jobs
Automation scripts
Zapier / Make workflows

But I cannot execute them myself.

4. Custom Skills / Memory / Instructions
🧩 Custom Instructions
Users can define:
Preferred tone
Behavior rules
Persistent across sessions: ✅
🧠 Memory (Persistent)
Tool: bio
What it stores:
Preferences
Context about you
Behavior:
Automatically used in future chats
User control: Can view/delete memory
🏗️ Custom GPTs / Skills
Status in this session: ❌ Not directly accessible
(These exist in ChatGPT platform, but not exposed here as callable tools)
📁 Project-Level Context
Not formally supported here
Context is limited to:
Current conversation
Stored memory (if enabled)
5. Agent / Sub-agent Capabilities
🤖 Sub-agents
Status: ❌ Not supported

I cannot:

Spawn independent agents
Run parallel workers
Delegate tasks autonomously
What I can do:
Simulate multi-step reasoning
Role-play multiple perspectives
Break tasks into steps

But all execution is:

Single-threaded
Synchronous
6. File Format Support
📥 Input (Read/Parse)

I can process:

Text: .txt, .md
Data: .csv, .json, .xml
Office:
.xlsx
.docx
.pptx
PDFs: .pdf
Code: .py, .js, .html, etc.
Images: .png, .jpg, .webp
📤 Output (Generate)

I can generate:

Text / Markdown
Code files
CSV / JSON
Excel-like structured data
HTML
Images (via DALL·E)
✏️ Editing
I can:
Rewrite content
Transform formats
Modify structured data
I cannot directly edit files on your device
🚫 Not Supported
Direct filesystem access
Persistent file storage
Executing uploaded binaries
7. Limitations & Gaps
🚫 Major Limitations
No real-world execution
Cannot:
Send emails
Access your computer
Control apps
Run background jobs
No persistent agents
No long-running processes
No memory beyond stored summaries
No true integrations (here)
No direct:
GitHub commits
Google Docs editing
Database queries
Web tool limitations
Requires explicit triggering conditions
Not always perfectly real-time
Some pages inaccessible
Image generation limits
No editing existing images (only generate new ones)
No guaranteed realism/accuracy
Python sandbox limits
No internet access inside Python
Limited compute/time
Temporary environment (resets)
Memory limitations
Not everything is remembered
Must be explicitly saved or inferred
Subscription differences (high-level)
Free: limited usage, fewer tool calls
Plus/Pro: more access (Python, images, higher limits)
Enterprise: best access, privacy controls, integrations
8. Comparison-Ready Summary
Capability	Available?	How	Tier Required	Notes
File read/write (local filesystem)	❌	Not supported	—	No direct disk access
Code execution (sandboxed shell)	✅	Python tool	Paid tiers	No internet
Web search	✅	Web tool	معظم tiers	Live data
Web page fetching	✅	Web tool	معظم tiers	Limited parsing
Image generation	✅	DALL·E	Paid tiers	Prompt-based
Image analysis / vision	✅	Native model	Most tiers	No tool needed
PDF creation/editing	⚠️ Partial	Python / text	Paid tiers	No native editor
Office docs (docx/xlsx/pptx)	⚠️ Partial	Python	Paid tiers	Structured generation
GitHub integration	❌	—	—	Not connected
Database access	❌	—	—	No direct DB connections
Scheduled tasks	❌	—	—	No background execution
Sub-agent spawning	❌	—	—	Single-threaded
Custom reusable workflows	⚠️ Limited	Prompting	All tiers	No true “skills” runtime
Persistent memory	✅	Memory tool	Depends on settings	User-controlled
MCP / tool protocol support	❌ (here)	—	—	Exists in other environments
Plugin marketplace	❌	—	—	Not exposed
Real-time collaboration	⚠️ Limited	Canvas	Paid tiers	Not multi-user live
Bottom line

In this session, you’re interacting with a single, tool-augmented AI agent that has:

✅ Strengths
Strong reasoning + explanation
Web access (current info)
Code execution (Python)
Content + data generation
Image generation
❌ Missing compared to full “agent platforms”
No autonomous workflows
No integrations
No scheduling
No multi-agent systems
No direct control over external systems