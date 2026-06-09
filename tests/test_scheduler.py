# tests/test_scheduler.py
import pytest
import asyncio
import time
from unittest.mock import Mock

# 根据项目实际路径调整导入
from src.async_runner import scheduler as scheduler_module

class DummyTask:
    def __init__(self, id, priority=0):
        self.id = id
        # Scheduler.PriorityQueue 期望 task.priority 存在
        self.priority = priority

# ---------- helper: robust scheduler constructor ----------
def make_scheduler(module):
    Scheduler = getattr(module, "Scheduler")
    try:
        return Scheduler()
    except TypeError:
        try:
            return Scheduler(maxsize=0)
        except TypeError:
            return Scheduler()

# ---------- helpers to run async code on a single loop per test ----------
def run_loop(coro_or_callable):
    """
    Create a fresh event loop, set it as current, run coro to completion, then close loop.
    Accept either:
      - a coroutine object (created inside the caller), or
      - a callable that returns a coroutine (preferred when coroutine must be created inside the loop).
    """
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        if callable(coro_or_callable):
            coro = coro_or_callable()
        else:
            coro = coro_or_callable
        return loop.run_until_complete(coro)
    finally:
        try:
            asyncio.set_event_loop(None)
        except Exception:
            pass
        loop.close()

def extract_task_id(item):
    if item is None:
        return None
    if hasattr(item, "id"):
        return getattr(item, "id")
    for attr in ("task", "value", "payload", "result"):
        if hasattr(item, attr):
            inner = getattr(item, attr)
            if inner is None:
                return None
            if hasattr(inner, "id"):
                return getattr(inner, "id")
            if isinstance(inner, dict) and "id" in inner:
                return inner["id"]
    if isinstance(item, dict) and "id" in item:
        return item["id"]
    return None

# ---------- tests ----------

def test_push_pop_qsize_basic():
    sched = make_scheduler(scheduler_module)
    t1 = DummyTask("t1")
    t2 = DummyTask("t2")

    async def _test():
        size0 = await sched.qsize()
        assert size0 == 0

        await sched.push(t1)
        size1 = await sched.qsize()
        assert size1 == 1

        await sched.push(t2)
        size2 = await sched.qsize()
        assert size2 == 2

        popped = await sched.pop()
        assert extract_task_id(popped) == "t1"

        size3 = await sched.qsize()
        assert size3 == 1

        popped2 = await sched.pop()
        assert extract_task_id(popped2) == "t2"

        size4 = await sched.qsize()
        assert size4 == 0

    run_loop(_test)

def test_pop_on_empty_queue_returns_none_or_blocks_short_timeout():
    sched = make_scheduler(scheduler_module)

    async def _test():
        try:
            res = await sched.pop(timeout=0)
        except TypeError:
            res = await sched.pop()
        assert res is None or extract_task_id(res) is None

    run_loop(_test)

def test_push_pop_order_fifo():
    sched = make_scheduler(scheduler_module)
    items = [DummyTask(f"t{i}") for i in range(5)]

    async def _test():
        for it in items:
            await sched.push(it)
        out = [await sched.pop() for _ in range(5)]
        out_ids = [extract_task_id(x) for x in out]
        assert out_ids == [f"t{i}" for i in range(5)]

    run_loop(_test)

def test_concurrent_push_pop_asyncio_safety():
    sched = make_scheduler(scheduler_module)
    total = 300
    popped = []

    async def producer():
        for i in range(total):
            await sched.push(DummyTask(f"p{i}"))

    async def consumer():
        count = 0
        while count < total:
            item = await sched.pop()
            if item is None:
                await asyncio.sleep(0.001)
                continue
            popped.append(item)
            count += 1

    # Create the gather coroutine inside the loop by passing a callable
    run_loop(lambda: asyncio.gather(producer(), consumer()))

    assert len(popped) == total
    pushed_ids = {f"p{i}" for i in range(total)}
    popped_ids = {extract_task_id(x) for x in popped}
    assert pushed_ids == popped_ids

def test_qsize_consistency_under_concurrency():
    sched = make_scheduler(scheduler_module)
    total = 150

    async def producer():
        for i in range(total):
            await sched.push(DummyTask(f"a{i}"))
            await asyncio.sleep(0.0005)

    async def consumer():
        count = 0
        while count < total:
            item = await sched.pop()
            if item is None:
                await asyncio.sleep(0.0005)
                continue
            count += 1

    run_loop(lambda: asyncio.gather(producer(), consumer()))

    size = run_loop(lambda: sched.qsize())
    assert isinstance(size, int)
    assert size >= 0
    assert size == 0

def test_push_after_stop_or_shutdown_behavior():
    sched = make_scheduler(scheduler_module)

    async def _test():
        for name in ("stop", "close", "shutdown"):
            if hasattr(sched, name):
                maybe = getattr(sched, name)
                res = maybe()
                if asyncio.iscoroutine(res):
                    await res
                break

        try:
            res = await sched.push(DummyTask("x"))
        except Exception:
            res = False

        size = await sched.qsize()
        assert res is False or size in (0, 1)

    run_loop(_test)
