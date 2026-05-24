"""Pluggable task storage backends: Memory, SQLite, Postgres."""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from .models import Task, is_valid_transition


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TaskBackend(ABC):
    @abstractmethod
    def add(self, task: Task) -> Task: ...

    @abstractmethod
    def get(self, task_id: str) -> Optional[Task]: ...

    @abstractmethod
    def list_pending(self, job_name: str) -> List[Task]: ...

    @abstractmethod
    def claim(self, task_id: str, worker_id: str) -> Task: ...

    @abstractmethod
    def update_status(self, task_id: str, status: str, reason: str = "") -> Task: ...

    @abstractmethod
    def heartbeat(self, task_id: str, worker_id: str) -> Task: ...

    @abstractmethod
    def get_stats(self, job_name: str) -> dict: ...


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------
class MemoryBackend(TaskBackend):
    def __init__(self):
        self._tasks: dict[str, Task] = {}
        self._lock = threading.Lock()

    def add(self, task: Task) -> Task:
        with self._lock:
            task.updated_at = _now()
            self._tasks[task.id] = task
            return task

    def get(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def list_pending(self, job_name: str) -> List[Task]:
        return [t for t in self._tasks.values()
                if t.job_name == job_name and t.status == "pending"]

    def claim(self, task_id: str, worker_id: str) -> Task:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                raise KeyError(f"Task {task_id} not found")
            if task.status != "pending":
                raise ValueError(f"Task {task_id} not pending (status={task.status})")
            task.status = "claimed"
            task.claimed_by = worker_id
            task.claimed_at = _now()
            task.updated_at = task.claimed_at
            return task

    def update_status(self, task_id: str, status: str, reason: str = "") -> Task:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                raise KeyError(f"Task {task_id} not found")
            if not is_valid_transition(task.status, status):
                raise ValueError(f"Invalid transition: {task.status} -> {status}")
            task.status = status
            task.reason = reason
            task.updated_at = _now()
            return task

    def heartbeat(self, task_id: str, worker_id: str) -> Task:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                raise KeyError(f"Task {task_id} not found")
            if task.claimed_by != worker_id:
                raise ValueError(f"Task {task_id} not claimed by {worker_id}")
            task.claimed_at = _now()
            task.updated_at = task.claimed_at
            return task

    def get_stats(self, job_name: str) -> dict:
        tasks = [t for t in self._tasks.values() if t.job_name == job_name]
        return {
            "pending": sum(1 for t in tasks if t.status == "pending"),
            "claimed": sum(1 for t in tasks if t.status == "claimed"),
            "completed": sum(1 for t in tasks if t.status == "completed"),
            "failed": sum(1 for t in tasks if t.status == "failed"),
        }


# ---------------------------------------------------------------------------
# SQLite
# ---------------------------------------------------------------------------
SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
  id TEXT PRIMARY KEY,
  job_name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  claimed_by TEXT,
  claimed_at TEXT,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  reason TEXT,
  metadata TEXT
);
CREATE INDEX IF NOT EXISTS idx_job_status ON tasks(job_name, status);
CREATE INDEX IF NOT EXISTS idx_claimed ON tasks(claimed_by, claimed_at);
"""


def _row_to_task(row) -> Task:
    return Task(
        id=row["id"],
        job_name=row["job_name"],
        status=row["status"],
        claimed_by=row["claimed_by"],
        claimed_at=row["claimed_at"],
        updated_at=row["updated_at"],
        reason=row["reason"],
        metadata=json.loads(row["metadata"]) if row["metadata"] else {},
    )


class SQLiteBackend(TaskBackend):
    def __init__(self, db_path: str = ".tasks/queue.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        with self._conn() as conn:
            conn.executescript(SQLITE_SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, isolation_level=None, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def add(self, task: Task) -> Task:
        task.updated_at = _now()
        with self._lock, self._conn() as conn:
            conn.execute(
                """INSERT INTO tasks(id, job_name, status, claimed_by, claimed_at,
                                     updated_at, reason, metadata)
                   VALUES(?, ?, ?, ?, ?, ?, ?, ?)""",
                (task.id, task.job_name, task.status, task.claimed_by,
                 task.claimed_at, task.updated_at, task.reason,
                 json.dumps(task.metadata or {})),
            )
        return task

    def get(self, task_id: str) -> Optional[Task]:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        return _row_to_task(row) if row else None

    def list_pending(self, job_name: str) -> List[Task]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE job_name=? AND status='pending'",
                (job_name,),
            ).fetchall()
        return [_row_to_task(r) for r in rows]

    def claim(self, task_id: str, worker_id: str) -> Task:
        ts = _now()
        with self._lock, self._conn() as conn:
            cur = conn.execute(
                """UPDATE tasks
                   SET status='claimed', claimed_by=?, claimed_at=?, updated_at=?
                   WHERE id=? AND status='pending'""",
                (worker_id, ts, ts, task_id),
            )
            if cur.rowcount == 0:
                row = conn.execute("SELECT status FROM tasks WHERE id=?", (task_id,)).fetchone()
                if not row:
                    raise KeyError(f"Task {task_id} not found")
                raise ValueError(f"Task {task_id} not pending (status={row['status']})")
        task = self.get(task_id)
        assert task is not None
        return task

    def update_status(self, task_id: str, status: str, reason: str = "") -> Task:
        with self._lock, self._conn() as conn:
            row = conn.execute("SELECT status FROM tasks WHERE id=?", (task_id,)).fetchone()
            if not row:
                raise KeyError(f"Task {task_id} not found")
            if not is_valid_transition(row["status"], status):
                raise ValueError(f"Invalid transition: {row['status']} -> {status}")
            conn.execute(
                "UPDATE tasks SET status=?, reason=?, updated_at=? WHERE id=?",
                (status, reason, _now(), task_id),
            )
        task = self.get(task_id)
        assert task is not None
        return task

    def heartbeat(self, task_id: str, worker_id: str) -> Task:
        ts = _now()
        with self._lock, self._conn() as conn:
            cur = conn.execute(
                "UPDATE tasks SET claimed_at=?, updated_at=? WHERE id=? AND claimed_by=?",
                (ts, ts, task_id, worker_id),
            )
            if cur.rowcount == 0:
                row = conn.execute("SELECT id FROM tasks WHERE id=?", (task_id,)).fetchone()
                if not row:
                    raise KeyError(f"Task {task_id} not found")
                raise ValueError(f"Task {task_id} not claimed by {worker_id}")
        task = self.get(task_id)
        assert task is not None
        return task

    def get_stats(self, job_name: str) -> dict:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) AS n FROM tasks WHERE job_name=? GROUP BY status",
                (job_name,),
            ).fetchall()
        stats = {"pending": 0, "claimed": 0, "completed": 0, "failed": 0}
        for r in rows:
            stats[r["status"]] = r["n"]
        return stats


# ---------------------------------------------------------------------------
# Postgres
# ---------------------------------------------------------------------------
POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
  id TEXT PRIMARY KEY,
  job_name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  claimed_by TEXT,
  claimed_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  reason TEXT,
  metadata JSONB
);
CREATE INDEX IF NOT EXISTS idx_job_status ON tasks(job_name, status);
CREATE INDEX IF NOT EXISTS idx_claimed ON tasks(claimed_by, claimed_at);
"""


class PostgresBackend(TaskBackend):
    def __init__(self, dsn: str):
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor, Json
        except ImportError as e:
            raise RuntimeError(
                "psycopg2-binary required for PostgresBackend. "
                "Install: pip install psycopg2-binary"
            ) from e
        self._psycopg2 = psycopg2
        self._RealDictCursor = RealDictCursor
        self._Json = Json
        self.dsn = dsn
        with self._conn() as conn, conn.cursor() as cur:
            cur.execute(POSTGRES_SCHEMA)
            conn.commit()

    def _conn(self):
        return self._psycopg2.connect(self.dsn)

    def _row_to_task(self, row) -> Task:
        return Task(
            id=row["id"],
            job_name=row["job_name"],
            status=row["status"],
            claimed_by=row["claimed_by"],
            claimed_at=row["claimed_at"].isoformat() if row["claimed_at"] else None,
            updated_at=row["updated_at"].isoformat() if row["updated_at"] else None,
            reason=row["reason"],
            metadata=row["metadata"] or {},
        )

    def add(self, task: Task) -> Task:
        with self._conn() as conn, conn.cursor(cursor_factory=self._RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO tasks(id, job_name, status, claimed_by, claimed_at,
                                     reason, metadata)
                   VALUES(%s, %s, %s, %s, %s, %s, %s)
                   RETURNING *""",
                (task.id, task.job_name, task.status, task.claimed_by,
                 task.claimed_at, task.reason, self._Json(task.metadata or {})),
            )
            row = cur.fetchone()
            conn.commit()
        return self._row_to_task(row)

    def get(self, task_id: str) -> Optional[Task]:
        with self._conn() as conn, conn.cursor(cursor_factory=self._RealDictCursor) as cur:
            cur.execute("SELECT * FROM tasks WHERE id=%s", (task_id,))
            row = cur.fetchone()
        return self._row_to_task(row) if row else None

    def list_pending(self, job_name: str) -> List[Task]:
        with self._conn() as conn, conn.cursor(cursor_factory=self._RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM tasks WHERE job_name=%s AND status='pending'",
                (job_name,),
            )
            rows = cur.fetchall()
        return [self._row_to_task(r) for r in rows]

    def claim(self, task_id: str, worker_id: str) -> Task:
        with self._conn() as conn, conn.cursor(cursor_factory=self._RealDictCursor) as cur:
            cur.execute(
                """UPDATE tasks
                   SET status='claimed', claimed_by=%s, claimed_at=NOW(), updated_at=NOW()
                   WHERE id=%s AND status='pending'
                   RETURNING *""",
                (worker_id, task_id),
            )
            row = cur.fetchone()
            if not row:
                cur.execute("SELECT status FROM tasks WHERE id=%s", (task_id,))
                check = cur.fetchone()
                conn.rollback()
                if not check:
                    raise KeyError(f"Task {task_id} not found")
                raise ValueError(f"Task {task_id} not pending (status={check['status']})")
            conn.commit()
        return self._row_to_task(row)

    def update_status(self, task_id: str, status: str, reason: str = "") -> Task:
        with self._conn() as conn, conn.cursor(cursor_factory=self._RealDictCursor) as cur:
            cur.execute("SELECT status FROM tasks WHERE id=%s", (task_id,))
            row = cur.fetchone()
            if not row:
                raise KeyError(f"Task {task_id} not found")
            if not is_valid_transition(row["status"], status):
                raise ValueError(f"Invalid transition: {row['status']} -> {status}")
            cur.execute(
                """UPDATE tasks SET status=%s, reason=%s, updated_at=NOW()
                   WHERE id=%s RETURNING *""",
                (status, reason, task_id),
            )
            updated = cur.fetchone()
            conn.commit()
        return self._row_to_task(updated)

    def heartbeat(self, task_id: str, worker_id: str) -> Task:
        with self._conn() as conn, conn.cursor(cursor_factory=self._RealDictCursor) as cur:
            cur.execute(
                """UPDATE tasks SET claimed_at=NOW(), updated_at=NOW()
                   WHERE id=%s AND claimed_by=%s
                   RETURNING *""",
                (task_id, worker_id),
            )
            row = cur.fetchone()
            if not row:
                cur.execute("SELECT id FROM tasks WHERE id=%s", (task_id,))
                check = cur.fetchone()
                conn.rollback()
                if not check:
                    raise KeyError(f"Task {task_id} not found")
                raise ValueError(f"Task {task_id} not claimed by {worker_id}")
            conn.commit()
        return self._row_to_task(row)

    def get_stats(self, job_name: str) -> dict:
        with self._conn() as conn, conn.cursor(cursor_factory=self._RealDictCursor) as cur:
            cur.execute(
                "SELECT status, COUNT(*) AS n FROM tasks WHERE job_name=%s GROUP BY status",
                (job_name,),
            )
            rows = cur.fetchall()
        stats = {"pending": 0, "claimed": 0, "completed": 0, "failed": 0}
        for r in rows:
            stats[r["status"]] = r["n"]
        return stats


# ---------------------------------------------------------------------------
# Auto-detect
# ---------------------------------------------------------------------------
def make_backend(backend: str = "auto", **kwargs) -> TaskBackend:
    """Construct a backend.

    backend: "memory" | "sqlite" | "postgres" | "auto"
    auto: DATABASE_URL env -> postgres, else .tasks/ dir present or creatable -> sqlite, else memory
    """
    if backend == "memory":
        return MemoryBackend()
    if backend == "sqlite":
        return SQLiteBackend(kwargs.get("db_path", ".tasks/queue.db"))
    if backend == "postgres":
        dsn = kwargs.get("dsn") or os.environ.get("DATABASE_URL")
        if not dsn:
            raise ValueError("PostgresBackend requires dsn or DATABASE_URL env")
        return PostgresBackend(dsn)
    if backend == "auto":
        dsn = os.environ.get("DATABASE_URL")
        if dsn:
            return PostgresBackend(dsn)
        try:
            return SQLiteBackend(".tasks/queue.db")
        except Exception:
            return MemoryBackend()
    raise ValueError(f"Unknown backend: {backend}")
