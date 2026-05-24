"""Task model and status enum."""
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class TaskStatus(str, Enum):
    PENDING = "pending"
    CLAIMED = "claimed"
    COMPLETED = "completed"
    FAILED = "failed"


VALID_TRANSITIONS = {
    "pending": {"claimed"},
    "claimed": {"completed", "failed", "pending"},
    "completed": set(),
    "failed": set(),
}


def is_valid_transition(from_status: str, to_status: str) -> bool:
    return to_status in VALID_TRANSITIONS.get(from_status, set())


@dataclass
class Task:
    id: str
    job_name: str
    status: str = TaskStatus.PENDING.value
    claimed_by: Optional[str] = None
    claimed_at: Optional[str] = None
    updated_at: Optional[str] = None
    reason: Optional[str] = None
    metadata: Optional[dict] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)
