# async_runner/persistence.py
import sqlite3
import threading
import json  # ← 修复：补上 json
from typing import Optional, List

from async_runner.task_model import Task, TaskStatus  # ← 修复：补上 TaskStatus


class SQLitePersistence:
    def __init__(self, path: str = "tasks.db"):
        self.path = path
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                payload TEXT,
                created_at REAL,
                attempts INTEGER,
                max_retries INTEGER,
                priority INTEGER,
                status TEXT,
                last_error TEXT,
                meta TEXT
            )
            """)

    def _conn(self):
        return sqlite3.connect(self.path, check_same_thread=False)

    def save_task(self, task: Task):
        with self._lock, self._conn() as conn:
            conn.execute("""
            INSERT OR REPLACE INTO tasks 
            (id, payload, created_at, attempts, max_retries, priority, status, last_error, meta)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.id,
                json.dumps(task.payload),     # ← 修复：json.dumps
                task.created_at,
                task.attempts,
                task.max_retries,
                task.priority,
                task.status.value,            # ← 修复：TaskStatus
                task.last_error,
                json.dumps(task.meta)         # ← 修复：json.dumps
            ))

    def load_pending(self) -> List[Task]:
        with self._lock, self._conn() as conn:
            cur = conn.execute("""
                SELECT id, payload, created_at, attempts, max_retries, priority, status, last_error, meta 
                FROM tasks 
                WHERE status IN ('pending','retry')
            """)
            rows = cur.fetchall()

            tasks = []
            for r in rows:
                t = Task(
                    id=r[0],
                    payload=json.loads(r[1]),          # ← 修复：json.loads
                    created_at=r[2],
                    attempts=r[3],
                    max_retries=r[4],
                    priority=r[5],
                    status=TaskStatus(r[6]),           # ← 修复：TaskStatus
                    last_error=r[7],
                    meta=json.loads(r[8]) if r[8] else {}
                )
                tasks.append(t)
            return tasks

    def delete_task(self, task_id: str):
        with self._lock, self._conn() as conn:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
