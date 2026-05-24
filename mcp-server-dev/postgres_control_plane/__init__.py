"""postgres-control-plane: pluggable task queue with FastMCP server."""
from .backend import (
    MemoryBackend,
    PostgresBackend,
    SQLiteBackend,
    TaskBackend,
    make_backend,
)
from .models import Task, TaskStatus, is_valid_transition
from .queue import TaskQueue

__all__ = [
    "Task",
    "TaskStatus",
    "TaskQueue",
    "TaskBackend",
    "MemoryBackend",
    "SQLiteBackend",
    "PostgresBackend",
    "make_backend",
    "is_valid_transition",
]

__version__ = "0.2.0"
