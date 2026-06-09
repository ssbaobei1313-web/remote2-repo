# src/async_runner/persistence.py
import sqlite3
import json
import threading
from typing import List, Optional

from src.async_runner.task_model import Task


class SQLitePersistence:
    """
    SQLite persistence for Task objects.

    - For path == ":memory:" we keep a single connection object so the in-memory DB
      persists across calls.
    - For file paths we open a new connection per operation (check_same_thread=False).
    """

    def __init__(self, path: str):
        self.path = path
        self._lock = threading.Lock()
        self._conn_obj: Optional[sqlite3.Connection] = None

        # If using in-memory DB, create and keep a single connection
        if self.path == ":memory:":
            self._conn_obj = sqlite3.connect(self.path, check_same_thread=False)
        # If user passed a shared-memory URI, support it (optional)
        elif self.path.startswith("file:") and "mode=memory" in self.path:
            # user may pass 'file:memdb1?mode=memory&cache=shared' style
            self._conn_obj = sqlite3.connect(self.path, check_same_thread=False, uri=True)

        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        """
        Return a sqlite3.Connection.
        - For in-memory/shared-memory we reuse the same connection object.
        - For file-backed DBs we create a new connection each call.
        """
        if self._conn_obj is not None:
            return self._conn_obj
        return sqlite3.connect(self.path, check_same_thread=False)

    def _init_db(self) -> None:
        """
        Ensure the tasks table exists. Use the connection returned by _conn().
        """
        conn = self._conn()
        # If we created a new connection for this call and it's not the persistent one,
        # ensure we close it after creating the table.
        created_temp_conn = (conn is not self._conn_obj)
        try:
            cur = conn.cursor()
            cur.execute(
                """
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
                """
            )
            conn.commit()
        finally:
            if created_temp_conn:
                conn.close()

    async def save_task(self, task: Task) -> None:
        """
        Insert or replace a task row.
        Accepts Task.status as either a string or Enum-like object.
        """
        status = getattr(task.status, "value", task.status)
        payload_json = json.dumps(task.payload or {})
        meta_json = json.dumps(task.meta or {})

        # Use the connection; if it's a temp connection, close after use.
        conn = self._conn()
        created_temp_conn = (conn is not self._conn_obj)
        try:
            with self._lock:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT OR REPLACE INTO tasks
                    (id, payload, created_at, attempts, max_retries, priority, status, last_error, meta)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        task.id,
                        payload_json,
                        getattr(task, "created_at", None),
                        getattr(task, "attempts", 0),
                        getattr(task, "max_retries", 0),
                        getattr(task, "priority", 0),
                        status,
                        getattr(task, "last_error", None),
                        meta_json,
                    ),
                )
                conn.commit()
        finally:
            if created_temp_conn:
                conn.close()

    async def load_pending(self) -> List[Task]:
        """
        Load tasks whose status equals 'pending'.
        Returns a list of Task instances reconstructed from DB rows.
        """
        conn = self._conn()
        created_temp_conn = (conn is not self._conn_obj)
        try:
            with self._lock:
                cur = conn.cursor()
                cur.execute(
                    "SELECT id, payload, created_at, attempts, max_retries, priority, status, last_error, meta FROM tasks WHERE status = ?",
                    ("pending",),
                )
                rows = cur.fetchall()
        finally:
            if created_temp_conn:
                conn.close()

        tasks: List[Task] = []
        for row in rows:
            payload = json.loads(row[1]) if row[1] else {}
            meta = json.loads(row[8]) if row[8] else {}
            task = Task(
                id=row[0],
                payload=payload,
                created_at=row[2],
                attempts=row[3],
                max_retries=row[4],
                priority=row[5],
                status=row[6],
                last_error=row[7],
                meta=meta,
            )
            tasks.append(task)
        return tasks

    async def delete_task(self, task_id: str) -> None:
        """
        Delete a task by id. Idempotent: deleting a non-existent id is a no-op.
        """
        conn = self._conn()
        created_temp_conn = (conn is not self._conn_obj)
        try:
            with self._lock:
                cur = conn.cursor()
                cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                conn.commit()
        finally:
            if created_temp_conn:
                conn.close()
