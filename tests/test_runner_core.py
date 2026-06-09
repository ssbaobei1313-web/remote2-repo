# tests/test_runner_core.py
import asyncio
import pytest
from types import SimpleNamespace
from src.async_runner.runner import Runner
from async_runner.task_model import Task, TaskStatus

# -------------------------
# Dummy / Stub implementations
# -------------------------
class DummyScheduler:
    def __init__(self):
        self._q = asyncio.Queue()

    async def push(self, t: Task):
        await self._q.put(t)

    async def pop(self):
        try:
            return self._q.get_nowait()
        except asyncio.QueueEmpty:
            return None

    async def qsize(self):
        return self._q.qsize()

class DummyPersistence:
    def __init__(self, pending=None):
        # pending: list of Task to return on load_pending
        self._pending = pending or []
        self.saved = {}
        self.deleted = set()
        self.save_calls = []
        self.delete_calls = []

    def load_pending(self):
        # synchronous in Runner usage
        return list(self._pending)

    def save_task(self, task: Task):
        self.saved[task.id] = task
        self.save_calls.append(task.id)

    def delete_task(self, task_id):
        # Runner calls delete_task(task.id) but original code passes task.id
        # Accept both Task or id for robustness
        self.deleted.add(task_id)
        self.delete_calls.append(task_id)

class DummyExecutor:
    def __init__(self, behavior_map=None):
        """
        behavior_map: dict task_id -> list of responses to return sequentially.
        Each response is a dict like {'status':'success','result':...} or {'status':'retry'} or {'status':'fail','error':...}
        If list exhausted, last element is reused.
        """
        self.behavior_map = behavior_map or {}
        self.calls = []

    async def execute(self, task: Task, ctx: dict):
        self.calls.append(task.id)
        seq = self.behavior_map.get(task.id, [{'status': 'fail', 'error': 'no-response'}])
        # pop first if list, else reuse last
        if isinstance(seq, list) and len(seq) > 1:
            resp = seq.pop(0)
        else:
            resp = seq[0] if isinstance(seq, list) else seq
        # simulate small async work
        await asyncio.sleep(0)
        return resp

class DummyHooks:
    def __init__(self):
        self.on_task_start = None
        self.on_task_success = None
        self.on_task_fail = None
        self.on_status_update = None

# -------------------------
# Fixtures
# -------------------------
@pytest.fixture
def dummy_scheduler():
    return DummyScheduler()

@pytest.fixture
def dummy_persistence():
    return DummyPersistence()

@pytest.fixture
def hooks():
    return DummyHooks()

# -------------------------
# Tests
# -------------------------
@pytest.mark.asyncio
async def test_success_path_updates_stats_and_persistence(dummy_scheduler, dummy_persistence, hooks):
    """
    验证成功分支：
    - executor 返回 success
    - persistence.delete_task 被调用
    - on_task_start 和 on_task_success 被触发
    - stats['success'] 增加
    """
    # prepare
    t = Task(id="t-success", payload={})
    executor = DummyExecutor({'t-success': [{'status': 'success', 'result': 'ok'}]})
    called = {'start': False, 'success': False, 'status_updates': 0}
    hooks.on_task_start = lambda info: called.__setitem__('start', True)
    hooks.on_task_success = lambda info: called.__setitem__('success', True)
    hooks.on_status_update = lambda stats: called.__setitem__('status_updates', called['status_updates'] + 1)

    r = Runner(run_task_callable=None, concurrency=1, persistence=dummy_persistence)
    r.scheduler = dummy_scheduler
    r.executor = executor
    r.hooks = hooks

    # push and run
    await r.push_task(t)
    await r.start()
    # wait until worker processes task or timeout
    await asyncio.wait_for(asyncio.sleep(0.05), timeout=1)
    await r.stop()

    # assertions
    assert 't-success' in executor.calls
    # persistence.delete_task should have been called with task id
    assert 't-success' in dummy_persistence.deleted
    assert called['start'] is True
    assert called['success'] is True
    assert r.status()['success'] == 1

@pytest.mark.asyncio
async def test_retry_path_requeues_and_saves(dummy_scheduler, dummy_persistence):
    """
    验证重试分支：
    - executor 首次返回 retry，runner 将任务标记为 PENDING 并再次 push
    - persistence.save_task 被调用
    - stats['retries'] 增加
    """
    t = Task(id="t-retry", payload={})
    # executor will return 'retry' twice then 'success'
    executor = DummyExecutor({'t-retry': [
        {'status': 'retry'},
        {'status': 'retry'},
        {'status': 'success', 'result': 'done'}
    ]})
    r = Runner(run_task_callable=None, concurrency=1, persistence=dummy_persistence)
    r.scheduler = dummy_scheduler
    r.executor = executor

    await r.push_task(t)
    await r.start()
    # allow some cycles for retries to occur
    await asyncio.sleep(0.15)
    await r.stop()

    # persistence.save_task should have been called at least once for retry
    assert 't-retry' in dummy_persistence.saved
    # retries count should be >= 1
    assert r.status()['retries'] >= 1
    # eventually success should be recorded
    assert r.status()['success'] >= 1

@pytest.mark.asyncio
async def test_fail_path_saves_and_triggers_hook(dummy_scheduler, dummy_persistence, hooks):
    """
    验证失败分支：
    - executor 返回 fail
    - persistence.save_task 被调用
    - on_task_fail 被触发
    - stats['failed'] 增加
    """
    t = Task(id="t-fail", payload={})
    executor = DummyExecutor({'t-fail': [{'status': 'fail', 'error': 'boom'}]})
    called = {'fail': False}
    hooks.on_task_fail = lambda info: called.__setitem__('fail', True)

    r = Runner(run_task_callable=None, concurrency=1, persistence=dummy_persistence)
    r.scheduler = dummy_scheduler
    r.executor = executor
    r.hooks = hooks

    await r.push_task(t)
    await r.start()
    await asyncio.sleep(0.05)
    await r.stop()

    assert 't-fail' in dummy_persistence.saved
    assert called['fail'] is True
    assert r.status()['failed'] == 1

@pytest.mark.asyncio
async def test_start_restores_pending_and_stop_cleans_up():
    """
    验证 start 恢复 pending 任务并创建 workers，stop 取消并清理 workers
    """
    # create a pending task that should be restored on start
    pending_task = Task(id="t-pending", payload={})
    dummy_persistence = DummyPersistence(pending=[pending_task])
    dummy_scheduler = DummyScheduler()
    executor = DummyExecutor({'t-pending': [{'status': 'success', 'result': 'ok'}]})

    r = Runner(run_task_callable=None, concurrency=2, persistence=dummy_persistence)
    r.scheduler = dummy_scheduler
    r.executor = executor

    # before start, no workers and not running
    assert r._running is False
    assert len(r._workers) == 0

    await r.start()
    # after start, running True and workers created
    assert r._running is True
    assert len(r._workers) == 2

    # allow processing
    await asyncio.sleep(0.05)

    # stop and ensure cleanup
    await asyncio.wait_for(r.stop(), timeout=1)
    assert r._running is False
    assert len(r._workers) == 0
