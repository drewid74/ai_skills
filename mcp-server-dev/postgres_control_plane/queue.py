"""TaskQueue public API. Delegates to a pluggable backend."""
from __future__ import annotations

from typing import List, Optional

from .backend import TaskBackend, make_backend
from .models import Task


class TaskQueue:
    """Generic task queue with pluggable backend.

    Examples
    --------
    >>> q = TaskQueue()                       # auto-detect backend
    >>> q = TaskQueue(backend="memory")       # explicit
    >>> q = TaskQueue(backend="sqlite", db_path=".tasks/q.db")
    >>> q = TaskQueue(backend="postgres", dsn="postgresql://...")
    """

    def __init__(self, backend: str = "auto", **backend_kwargs):
        if isinstance(backend, TaskBackend):
            self.backend: TaskBackend = backend
        else:
            self.backend = make_backend(backend, **backend_kwargs)

    def add(self, task: Task) -> Task:
        return self.backend.add(task)

    def get(self, task_id: str) -> Optional[Task]:
        return self.backend.get(task_id)

    def list_pending(self, job_name: str) -> List[Task]:
        return self.backend.list_pending(job_name)

    def claim(self, task_id: str, worker_id: str) -> Task:
        return self.backend.claim(task_id, worker_id)

    def update_status(self, task_id: str, status: str, reason: str = "") -> Task:
        return self.backend.update_status(task_id, status, reason)

    def heartbeat(self, task_id: str, worker_id: str) -> Task:
        return self.backend.heartbeat(task_id, worker_id)

    def get_stats(self, job_name: str) -> dict:
        return self.backend.get_stats(job_name)
