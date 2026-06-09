# tests/test_runner_worker.py
import asyncio
import pytest
from types import SimpleNamespace
from src.async_runner.runner import Runner
from async_runner.task_model import Task, TaskStatus

class DummyScheduler:
    def __init__(self):
        self._q = asyncio.Queue()
    async def push(self, t):
        await self._q.put(t)
    async def pop(self):
        try:
            return self._q.get_nowait()
        except asyncio.QueueEmpty:
            return None
    async def qsize(self):
        return self._q.qsize()

class DummyPersistence:
    def __init__(self):
        self.saved = {}
        self.deleted = set()
    def load_pending(self):
        return []  # default empty
    def save_task(self, task):
        self.saved[task.id] = task
    def delete_task(self, task_id):
        self.deleted.add(task_id)

class DummyExecutor:
    def __init__(self, responses):
        # responses: dict task_id -> response dict
        self.responses = responses
        self.calls = []
    async def execute(self, task, ctx):
        self.calls.append(task.id)
        return self.responses.get(task.id, {'status': 'fail', 'error': 'no-response'})

class DummyHooks:
    def __init__(self):
        self.on_task_start = None
        self.on_task_success = None
        self.on_task_fail = None
        self.on_status_update = None

@pytest.mark.asyncio
async def test_worker_success_path(monkeypatch):
    # prepare runner with dummy components
    dummy_persistence = DummyPersistence()
    dummy_scheduler = DummyScheduler()
    # create a task
    t = Task(id="t1", payload={})
    # executor will return success for t1
    dummy_executor = DummyExecutor({'t1': {'status': 'success', 'result': 'ok'}})
    hooks = DummyHooks()
    # capture hook calls
    called = {'start': False, 'success': False, 'status_updates': 0}
    hooks.on_task_start = lambda info: called.__setitem__('start', True)
    hooks.on_task_success = lambda info: called.__setitem__('success', True)
    hooks.on_status_update = lambda stats: called.__setitem__('status_updates', called['status_updates'] + 1)

    r = Runner(run_task_callable=None, concurrency=1, persistence=dummy_persistence)
    # inject fakes
    r.scheduler = dummy_scheduler
    r.executor = dummy_executor
    r.hooks = hooks

    # push task and start runner
    await r.push_task(t)
    await r.start()
    # give worker some time to process
    await asyncio.sleep(0.05)
    await r.stop()

    assert 't1' in dummy_executor.calls
    assert 't1' in dummy_persistence.deleted or 't1' in dummy_persistence.deleted  # deleted set
    assert called['start'] is True
    assert called['success'] is True
    assert r.status()['success'] == 1

@pytest.mark.asyncio
async def test_worker_retry_path(monkeypatch):
    dummy_persistence = DummyPersistence()
    dummy_scheduler = DummyScheduler()
    t = Task(id="t2", payload={})
    # first response is retry; second time no response -> fail
    # simulate by returning 'retry' always; runner should push again and save
    dummy_executor = DummyExecutor({'t2': {'status': 'retry'}})
    r = Runner(run_task_callable=None, concurrency=1, persistence=dummy_persistence)
    r.scheduler = dummy_scheduler
    r.executor = dummy_executor

    await r.push_task(t)
    await r.start()
    await asyncio.sleep(0.05)
    await r.stop()

    # persistence.save_task should have been called (saved in saved dict)
    assert 't2' in dummy_persistence.saved
    assert r.status()['retries'] >= 1

@pytest.mark.asyncio
async def test_push_task_updates_stats_and_persistence(monkeypatch):
    dummy_persistence = DummyPersistence()
    dummy_scheduler = DummyScheduler()
    r = Runner(run_task_callable=None, concurrency=1, persistence=dummy_persistence)
    r.scheduler = dummy_scheduler
    # create task and push
    t = Task(id="t3", payload={})
    await r.push_task(t)
    # qsize should reflect pending
    assert r.status()['pending'] == 1
    assert 't3' in dummy_persistence.saved
