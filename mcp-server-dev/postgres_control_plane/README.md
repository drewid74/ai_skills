# Postgres-Backed Task Queue for AI Agent Coordination

**Minimal, reusable patterns extracted from GoldenMatch/GoldenCheck review queues.**

A generic task queue with pluggable backends (Memory/SQLite/Postgres), atomic claim semantics, and FastMCP tool wrappers for Claude integration.

## Quick Start

### Installation

```bash
pip install fastmcp psycopg2-binary
```

### Basic Usage

```python
from postgres_control_plane import TaskQueue, Task

# Initialize queue (auto-detects backend)
queue = TaskQueue(backend="auto")

# Add a task
task = Task(id="task-1", job_name="data-processing", status="pending")
queue.add(task)

# List pending tasks
pending = queue.list_pending("data-processing")
print(f"Found {len(pending)} pending tasks")

# Claim a task (atomic: only one worker succeeds)
try:
    claimed = queue.claim("task-1", worker_id="worker-1")
    print(f"Claimed by {claimed.claimed_by}")
except ValueError:
    print("Task already claimed by another worker")

# Update status
completed = queue.update_status("task-1", "completed", reason="Success")

# Heartbeat (keep claim alive)
queue.heartbeat("task-1", "worker-1")
```

## Architecture

### Pluggable Backends

| Backend | Use Case | Persistence |
|---------|----------|-------------|
| **Memory** | Testing, development | In-process only |
| **SQLite** | Local persistence, single-machine | `.tasks/queue.db` |
| **Postgres** | Production, multi-worker | Remote database |

Backend auto-detection:
```python
queue = TaskQueue(backend="auto")
# Tries: DATABASE_URL env var → .tasks/ dir → MemoryBackend
```

### Atomic Claim Semantics

The core pattern prevents double-claim race conditions:

```sql
UPDATE tasks SET status='claimed', claimed_by=?, claimed_at=NOW()
WHERE id=? AND status='pending'
```

Only one worker succeeds per task. The `WHERE status='pending'` guard ensures atomicity.

### Task Model

```python
@dataclass
class Task:
    id: str                          # Unique identifier
    job_name: str                    # Job grouping (e.g., "data-processing")
    status: str                      # pending, claimed, completed, failed
    claimed_by: Optional[str] = None # Worker ID
    claimed_at: Optional[str] = None # ISO timestamp
    updated_at: Optional[str] = None # Last update
    reason: Optional[str] = None     # Status change reason
    metadata: Optional[dict] = None  # Custom data
```

## MCP Server Integration

### FastMCP Tools

The `mcp_server.py` module exposes 7 tools for Claude:

#### 1. `add_task`
```python
add_task(task_id: str, job_name: str, metadata: dict | None = None) -> dict
```
Add a new task in pending status.

#### 2. `list_tasks`
```python
list_tasks(job_name: str, status: str = "pending") -> dict
```
List tasks by job and status.

#### 3. `claim_task`
```python
claim_task(task_id: str, worker_id: str) -> dict
```
Claim a task atomically. Raises `ValueError` if already claimed.

#### 4. `update_task_status`
```python
update_task_status(task_id: str, status: str, reason: str = "") -> dict
```
Update task status (pending → claimed → completed/failed). Validates transition.

#### 5. `heartbeat`
```python
heartbeat(task_id: str, worker_id: str) -> dict
```
Refresh claim lease (UPDATE claimed_at=NOW()).

#### 6. `verify_transition`
```python
verify_transition(from_status: str, to_status: str) -> dict
```
Check if status transition is valid (read-only).

#### 7. `get_stats`
```python
get_stats(job_name: str) -> dict
```
Get task counts by status.


### Running the MCP Server

```bash
# Local (SQLite)
python -m postgres_control_plane.mcp_server

# Production (Postgres)
export DATABASE_URL=postgresql://user:pass@localhost/tasks
python -m postgres_control_plane.mcp_server
```

### Claude Desktop Integration

Add to `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "control-plane": {
      "command": "python",
      "args": ["-m", "postgres_control_plane.mcp_server"]
    }
  }
}
```

## Database Schemas

### Postgres

```sql
CREATE TABLE tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  claimed_by TEXT,
  claimed_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  reason TEXT,
  metadata JSONB
);

CREATE INDEX idx_job_status ON tasks(job_name, status);
CREATE INDEX idx_claimed ON tasks(claimed_by, claimed_at);
```

### SQLite

```sql
CREATE TABLE tasks (
  id TEXT PRIMARY KEY,
  job_name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  claimed_by TEXT,
  claimed_at TEXT,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  reason TEXT,
  metadata TEXT
);
```

## Patterns from GoldenMatch/GoldenCheck

This module extracts production patterns from:

- **GoldenMatch review_queue.py** — SQLite-backed review queue with confidence gating
- **GoldenCheck review_queue.py** — Abstract backend interface with Memory/SQLite/Postgres implementations

Key patterns:
1. **Abstract backend ABC** — Pluggable implementations without code duplication
2. **Atomic UPDATE guards** — `WHERE status='pending'` prevents race conditions
3. **Heartbeat refresh** — Simple polling instead of LISTEN/NOTIFY
4. **Status transitions** — Explicit valid state machine (pending → claimed → completed/failed)
5. **JSON metadata** — Flexible task-specific data without schema changes

## Testing

### Claim Atomicity Test

```python
import threading
from postgres_control_plane import TaskQueue, Task

queue = TaskQueue(backend="memory")
task = Task(id="test-1", job_name="demo", status="pending")
queue.add(task)

results = []
def claim_worker(worker_id):
    try:
        queue.claim("test-1", worker_id)
        results.append(worker_id)
    except ValueError:
        pass

t1 = threading.Thread(target=claim_worker, args=("worker-1",))
t2 = threading.Thread(target=claim_worker, args=("worker-2",))
t1.start()
t2.start()
t1.join()
t2.join()

assert len(results) == 1, f"Expected 1 claim, got {len(results)}"
print(f"✓ Claim atomicity verified: {results[0]} won the race")
```

## Deployment

### Docker (Postgres)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install fastmcp psycopg2-binary
ENV DATABASE_URL=postgresql://user:pass@postgres:5432/tasks
CMD ["python", "-m", "postgres_control_plane.mcp_server"]
```

### Docker Compose

```yaml
version: "3.8"
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: tasks
      POSTGRES_PASSWORD: secret
    volumes:
      - postgres_data:/var/lib/postgresql/data

  control-plane:
    build: .
    environment:
      DATABASE_URL: postgresql://postgres:secret@postgres:5432/tasks
    depends_on:
      - postgres
    ports:
      - "8000:8000"

volumes:
  postgres_data:
```

## Design Decisions

### No Overbuilding

- **No LISTEN/NOTIFY** — Polling is simpler and works everywhere
- **No job queue library** — Just Postgres + psycopg2
- **No distributed locking** — Atomic UPDATE guards are sufficient
- **No retry logic** — Caller handles retries
- **No task dependencies** — Each task is independent

### Why Atomic UPDATE?

```sql
UPDATE tasks SET status='claimed', claimed_by=?, claimed_at=NOW()
WHERE id=? AND status='pending'
```

This is simpler and more reliable than:
- SELECT + INSERT (race condition window)
- Distributed locks (complexity, latency)
- LISTEN/NOTIFY (not available in SQLite)

The database guarantees atomicity. Only one worker's UPDATE succeeds.

## File Structure

```
postgres-control-plane/
├── __init__.py          # Package exports
├── models.py            # Task dataclass, TaskStatus enum
├── backend.py           # TaskBackend ABC, Memory/SQLite/Postgres implementations
├── queue.py             # TaskQueue public API
├── mcp_server.py        # FastMCP server with 6 tools
└── README.md            # This file
```

## References

- **GoldenMatch review_queue.py** — `C:\Users\afair\dev\ai_skills\goldenmatch\packages\python\goldenmatch\goldenmatch\core\review_queue.py`
- **GoldenCheck review_queue.py** — `C:\Users\afair\dev\ai_skills\goldenmatch\packages\python\goldencheck\goldencheck\agent\review_queue.py`
- **MCP Server Dev** — `C:\Users\afair\dev\ai_skills\mcp-server-dev\SKILL.md`

## License

MIT
