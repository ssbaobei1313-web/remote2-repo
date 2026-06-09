# tests/test_persistence.py
import sqlite3
import asyncio
import stat
import pytest
from pathlib import Path

from src.async_runner.persistence import SQLitePersistence
from src.async_runner.task_model import TaskStatus


class TaskStub:
    """
    Minimal Task-like object matching what SQLitePersistence expects:
    - id, status (Enum-like or string), payload (dict), meta (dict)
    - attempts, max_retries, priority
    """
    def __init__(
        self,
        task_id,
        attempts=0,
        max_retries=3,
        priority=0,
        payload=None,
        meta=None,
        status=TaskStatus.PENDING,
    ):
        self.id = task_id
        self.attempts = attempts
        self.max_retries = max_retries
        self.priority = priority
        self.payload = payload or {}
        self.meta = meta or {}
        self.status = status

    def to_dict(self):
        return {
            "id": self.id,
            "attempts": self.attempts,
            "max_retries": self.max_retries,
            "priority": self.priority,
            "payload": self.payload,
            "meta": self.meta,
            "status": getattr(self.status, "value", self.status),
        }


@pytest.fixture
def sample_tasks():
    return [
        TaskStub("t1", attempts=1),
        TaskStub("t2", attempts=0, priority=5),
    ]


@pytest.mark.asyncio
async def test_save_load_delete_tmpfile(tmp_path, sample_tasks):
    db_path = tmp_path / "persistence.db"
    p = SQLitePersistence(str(db_path))

    # save Task-like objects
    for t in sample_tasks:
        await p.save_task(t)

    # load_pending 返回 Task 对象列表（或类似对象）
    loaded = await p.load_pending()
    assert isinstance(loaded, list)
    assert len(loaded) == len(sample_tasks)

    # delete one task
    await p.delete_task(sample_tasks[0].id)
    loaded_after = await p.load_pending()
    assert len(loaded_after) == 1

    # 兼容 Task 对象或 dict 的检查：优先使用属性访问
    def get_id(item):
        if hasattr(item, "id"):
            return item.id
        if isinstance(item, dict):
            return item.get("id")
        raise TypeError("unexpected item type from load_pending")

    assert all(get_id(item) != sample_tasks[0].id for item in loaded_after)


@pytest.mark.asyncio
async def test_save_load_memory_db(sample_tasks):
    p = SQLitePersistence(":memory:")

    for t in sample_tasks:
        await p.save_task(t)

    loaded = await p.load_pending()
    assert len(loaded) == len(sample_tasks)


@pytest.mark.asyncio
async def test_concurrent_saves(tmp_path):
    db_path = tmp_path / "concurrent.db"
    p = SQLitePersistence(str(db_path))

    async def save_one(i):
        t = TaskStub(f"c{i}", attempts=0, max_retries=1, priority=i)
        await p.save_task(t)

    await asyncio.gather(*[save_one(i) for i in range(50)])

    loaded = await p.load_pending()
    assert len(loaded) == 50


def test_corrupt_db_raises(tmp_path):
    db_path = tmp_path / "corrupt.db"
    db_path.write_text("NOT A SQLITE DB")

    with pytest.raises(Exception):
        SQLitePersistence(str(db_path))


def test_permission_error_on_open(tmp_path):
    db_path = tmp_path / "perm.db"
    db_path.write_text("")

    orig_mode = db_path.stat().st_mode
    try:
        db_path.chmod(stat.S_IREAD)
        with pytest.raises(Exception):
            SQLitePersistence(str(db_path))
    finally:
        db_path.chmod(orig_mode)
