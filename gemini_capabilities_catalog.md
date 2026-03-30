# Gemini Capabilities Catalog

As of March 2026, this catalog covers **Gemini 3 Flash** operating in the **Paid tier** — expanded context windows, higher-fidelity creative tools, and priority access to advanced reasoning kernels.

---

## 1. Built-in Core Tools

Native functions available for real-time world interaction and data processing.

### Google Search
- **Trigger:** Questions about current events, facts, or live data (e.g., "What is the stock price of Alphabet today?")
- **Function:** Retrieves real-time web snippets and verifies information across the live internet
- **Tier:** All tiers; Paid receives faster, more comprehensive grounding

### Python Interpreter (`ds_python_interpreter`)
- **Trigger:** Mathematical operations, data analysis, or requests to "write and run" code
- **Function:** Sandboxed environment to execute Python for complex calculations or data visualization
- **Tier:** All tiers; Paid handles larger datasets and longer execution times

### Nano Banana 2 (Image Generation)
- **Trigger:** "Generate an image of..." or "Create a graphic for..."
- **Function:** Text-to-image/image-to-image; supports 4K resolution, 14 aspect ratios, precise text rendering
- **Tier:** 50–100 uses/day (AI Plus/Pro/Ultra); includes "Redo with Pro" for maximum fidelity

### Veo 3.1 (Video Generation)
- **Trigger:** "Make a video of..." or "Animate this scene..."
- **Function:** Generates 8-second 1080p/4K videos with natively generated audio; supports reference images and frame-specific control
- **Tier:** 3–5 uses/day (Pro/Ultra)

### Lyria 3 Pro (Music Generation)
- **Trigger:** "Write a song about..." or "Generate a lo-fi track for..."
- **Function:** High-fidelity music tracks up to 3 minutes with automated lyrics and realistic vocals across multiple languages
- **Tier:** Higher generation limits and 3-minute length exclusive to Paid users

---

## 2. Connected Integrations / Plugins / Extensions

Deeply integrated with the Google ecosystem and select third-party services via the Extensions framework.

| Integration | Capabilities |
|---|---|
| **Google Workspace** | Gmail (summarization/replies), Google Drive (reading/summarizing), Docs (creation/editing) |
| **Google Maps** | Real-time navigation, "Ask Maps" location insights, immersive views |
| **YouTube** | Search, summary, deep-dive discussions of video content |
| **Google Flights & Hotels** | Live pricing, booking assistance, itinerary planning |
| **GitHub (CLI Extension)** | Version control, repository analysis, "Vibe Coding" support |
| **Third-Party** | OpenTable, WhatsApp — task-specific integrations for communication and logistics |

> Most extensions require a Google account. Paid users get enhanced multi-step reasoning across apps.

---

## 3. Automation & Scheduling

- **Recurring Tasks:** Cannot set cron jobs (e.g., "Email me every Tuesday"). Can interface with Google Calendar and Google Tasks for reminders and schedule management.
- **Background Agents:** Does not run autonomously without a user prompt. Stateless agent that reacts to inputs; maintains context within a session.

---

## 4. Custom Skills / Custom Instructions / Memory

- **Gems:** Create custom specialized versions with specific instructions (e.g., "Coding Coach", "Creative Writing Editor")
- **Persistent Memory:** Remembers preferences, professional context, and preferred tone across sessions if Memory is enabled in settings
- **System Instructions:** Every prompt is influenced by core identity and safety guardrails

---

## 5. Agent / Sub-agent Capabilities

Does not spawn parallel child processes. Uses **Agentic Reasoning**:

- **Multi-Step Planning:** Breaks complex queries into sub-goals and executes sequentially (e.g., Search X → Analyze Y → Generate Z)
- **Tool Inheritance:** Sub-tasks have access to the same core toolset (Python, Search, Images)
- **Concurrency:** Limited to one active tool execution at a time

---

## 6. File Format Support

| Action | Supported Formats |
|---|---|
| **Read / Parse** | PDF, DOCX, XLSX, CSV, TXT, MD, Python, JS, HTML, JPG, PNG, WEBP, MP3, WAV, MP4, MOV |
| **Create / Generate** | Markdown, Code, CSV, Images (Nano Banana 2), Video (Veo), Music (Lyria 3) |
| **Edit In-Place** | Google Docs (via Workspace), Google Sheets, Python scripts in sandbox |

---

## 7. Limitations & Gaps

- **Local Filesystem:** Cannot access your physical hard drive. Only sees explicitly uploaded files or those in connected Google Drive.
- **Real-time Browsing:** Uses search snippets; does not surf websites in real-time — cannot click buttons or bypass paywalls.
- **Autonomous Actions:** Cannot take actions requiring a credit card or legal signature without manual confirmation.
- **Unreliable Features:** Large-scale code refactoring across massive repositories can be hallucination-prone — always review critical logic.

---

## 8. Capability Summary

| Capability | Available? | How | Tier Required | Notes |
|---|---|---|---|---|
| File Read/Write | Yes | Drive/Uploads | Any | Paid has higher file size limits |
| Code Execution | Yes | Python Tool | Any | Sandboxed environment |
| Web Search | Yes | Google Search | Any | Priority grounding for Paid |
| Image Generation | Yes | Nano Banana 2 | Paid (Higher Quota) | 50–100 uses/day |
| Video Generation | Yes | Veo 3.1 | Paid (Pro/Ultra) | 3–5 uses/day |
| Music Generation | Yes | Lyria 3 Pro | Paid | Up to 3-minute tracks |
| GitHub Integration | Yes | CLI Extensions | Any | Requires account linking |
| Persistent Memory | Yes | Settings Toggle | Any | Cross-session memory |
| Custom Skills | Yes | Gems | Paid | Create custom AI personas |
| Sub-agent Spawning | Partial | Agentic Reasoning | Any | Sequential, not parallel |
| MCP Support | Yes | Extension Protocol | Developer/Pro | Uses standard tool protocol |
