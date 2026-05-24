"""FastMCP server exposing TaskQueue as 7 tools.

Run:
    python -m postgres_control_plane.mcp_server

Backend selection via env:
    DATABASE_URL=postgresql://... python -m postgres_control_plane.mcp_server
"""
from __future__ import annotations

import os
from dataclasses import asdict

from fastmcp import FastMCP

from .models import Task, is_valid_transition
from .queue import TaskQueue

BACKEND = os.environ.get("CONTROL_PLANE_BACKEND", "auto")
_backend_kwargs: dict = {}
_db_path = os.environ.get("CONTROL_PLANE_DB_PATH")
if _db_path:
    _backend_kwargs["db_path"] = _db_path
_dsn = os.environ.get("DATABASE_URL")
if _dsn and BACKEND in ("postgres", "auto"):
    _backend_kwargs.setdefault("dsn", _dsn)
queue = TaskQueue(backend=BACKEND, **_backend_kwargs)

mcp = FastMCP("control-plane")


@mcp.tool()
def add_task(task_id: str, job_name: str, metadata: dict | None = None) -> dict:
    """Add a new task in pending status.

    Args:
        task_id: Unique identifier.
        job_name: Job grouping label (e.g., 'data-processing').
        metadata: Optional dict of task-specific data.
    """
    task = Task(id=task_id, job_name=job_name, metadata=metadata or {})
    saved = queue.add(task)
    return asdict(saved)


@mcp.tool()
def list_tasks(job_name: str, status: str = "pending") -> dict:
    """List tasks by job and status. Only 'pending' is currently indexed."""
    if status == "pending":
        tasks = queue.list_pending(job_name)
    else:
        # Fallback: filter from stats (no full enumeration API by design)
        tasks = []
    return {
        "job_name": job_name,
        "status": status,
        "count": len(tasks),
        "tasks": [asdict(t) for t in tasks],
    }


@mcp.tool()
def claim_task(task_id: str, worker_id: str) -> dict:
    """Atomically claim a pending task. Raises if already claimed."""
    task = queue.claim(task_id, worker_id)
    return asdict(task)


@mcp.tool()
def update_task_status(task_id: str, status: str, reason: str = "") -> dict:
    """Update task status. Validates transition (pending->claimed->completed/failed)."""
    task = queue.update_status(task_id, status, reason)
    return asdict(task)


@mcp.tool()
def heartbeat(task_id: str, worker_id: str) -> dict:
    """Refresh claim lease — updates claimed_at to NOW()."""
    task = queue.heartbeat(task_id, worker_id)
    return {"task_id": task.id, "heartbeat": "ok", "claimed_at": task.claimed_at}


@mcp.tool()
def verify_transition(from_status: str, to_status: str) -> dict:
    """Check if a status transition is valid (without mutating)."""
    valid = is_valid_transition(from_status, to_status)
    return {"from": from_status, "to": to_status, "valid": valid}


@mcp.tool()
def get_stats(job_name: str) -> dict:
    """Get task counts by status for a job."""
    stats = queue.get_stats(job_name)
    return {"job_name": job_name, "stats": stats, "total": sum(stats.values())}


def main():
    mcp.run()


if __name__ == "__main__":
    main()
