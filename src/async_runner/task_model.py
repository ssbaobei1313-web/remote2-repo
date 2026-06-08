# async_runner/task_model.py
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from typing import Any, Dict, Optional
import time
import uuid
import json

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"
    CANCELLED = "cancelled"

@dataclass
class Task:
    id: str
    payload: Dict[str, Any]
    created_at: float = field(default_factory=lambda: time.time())
    attempts: int = 0
    max_retries: int = 3
    priority: int = 0
    status: TaskStatus = TaskStatus.PENDING
    last_error: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def new(payload: Dict[str, Any], max_retries: int = 3, priority: int = 0) -> "Task":
        return Task(id=str(uuid.uuid4()), payload=payload, max_retries=max_retries, priority=priority)

    def to_json(self) -> str:
        d = asdict(self)
        d['status'] = self.status.value
        return json.dumps(d)

    @staticmethod
    def from_json(s: str) -> "Task":
        d = json.loads(s)
        d['status'] = TaskStatus(d['status'])
        return Task(**d)
