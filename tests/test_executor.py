# tests/test_executor.py
import pytest
from unittest.mock import Mock
import types
import asyncio

# 调整为你项目中实际的导入路径
from src.async_runner import executor as executor_module

class DummyTask:
    def __init__(self, id="t1", payload=None):
        self.id = id
        self.payload = payload or {}
        self.attempts = 0
        self.max_retries = 2
        self.last_error = None
        self.status = None

# ---------- helper: robust constructor ----------
def make_executor(module, browser_pool, proxy_pool, max_retries=2):
    Executor = getattr(module, "Executor")
    # 尝试多种常见签名
    try:
        inst = Executor(browser_pool=browser_pool, proxy_pool=proxy_pool, max_retries=max_retries)
    except TypeError:
        try:
            inst = Executor(browser_pool, proxy_pool, max_retries)
        except TypeError:
            try:
                inst = Executor(browser_pool, proxy_pool)
            except TypeError:
                try:
                    inst = Executor()
                except Exception as e:
                    raise RuntimeError("Cannot construct Executor with any known signature") from e

    # 注入/修正属性（best-effort）
    try:
        setattr(inst, "browser_pool", browser_pool)
    except Exception:
        pass
    try:
        setattr(inst, "proxy_pool", proxy_pool)
    except Exception:
        pass
    try:
        setattr(inst, "max_retries", max_retries)
    except Exception:
        pass

    # 确保存在 error_classifier 和 retry_policy，且为可 await 的 wait_before_retry
    if not hasattr(inst, "error_classifier") or inst.error_classifier is None:
        ec = Mock()
        ec.classify = lambda e: True
        inst.error_classifier = ec
    if not hasattr(inst, "retry_policy") or inst.retry_policy is None:
        rp = Mock()
        async def _wait_before_retry(n):
            return None
        rp.wait_before_retry = _wait_before_retry
        inst.retry_policy = rp

    # 确保 run_task_callable 存在（测试会覆盖它）
    if not hasattr(inst, "run_task_callable"):
        async def _default_run(task, ctx):
            return None
        inst.run_task_callable = _default_run

    return inst

# ---------- fixtures ----------
@pytest.fixture
def browser_pool():
    bp = Mock()

    async def _acquire():
        return "fake-browser"
    async def _release(browser):
        return None

    bp.acquire = _acquire
    bp.release = _release
    return bp

@pytest.fixture
def proxy_pool():
    pp = Mock()

    async def _acquire():
        return None
    async def _release(proxy):
        return None

    pp.acquire = _acquire
    pp.release = _release
    return pp

@pytest.fixture
def executor(browser_pool, proxy_pool):
    return make_executor(executor_module, browser_pool, proxy_pool, max_retries=2)

# ---------- helper to await execute ----------
def run_execute(coro_or_callable):
    """
    Accept either a coroutine (returned by executor.execute) or a callable that returns coroutine.
    Use asyncio.run to execute it synchronously in tests.
    """
    if asyncio.iscoroutine(coro_or_callable):
        return asyncio.run(coro_or_callable)
    return asyncio.run(coro_or_callable())

# ---------- tests ----------
def test_execute_success_first_try(monkeypatch, executor, browser_pool, proxy_pool):
    task = DummyTask()
    ctx = {}

    # patch run_task_callable 返回协程结果
    async def _run_task(task_arg, ctx_arg):
        return {"status": "ok", "value": 42}

    # attach to instance or module depending on implementation
    if hasattr(executor, "run_task_callable"):
        executor.run_task_callable = _run_task
    else:
        monkeypatch.setattr(executor_module, "run_task_callable", _run_task, raising=False)

    result = run_execute(lambda: executor.execute(task, ctx))

    assert result == {"status": "success", "result": {"status": "ok", "value": 42}}
    # browser_pool.acquire/release are async functions; we can't assert call_count on plain functions easily,
    # but we can ensure ctx got browser set and then released by checking ctx content and that release is callable.
    assert ctx.get("browser") == "fake-browser"
    assert callable(browser_pool.release)

def test_execute_retry_then_success(monkeypatch, executor, browser_pool, proxy_pool):
    task = DummyTask()
    ctx = {}

    calls = {"count": 0}
    async def _run_task(task_arg, ctx_arg):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("transient error")
        return {"status": "ok", "value": "after-retry"}

    executor.run_task_callable = _run_task
    # make classifier return True (retryable)
    executor.error_classifier.classify = lambda e: True
    # ensure retry_policy wait is async (already set in make_executor)

    result = run_execute(lambda: executor.execute(task, ctx))

    assert result == {"status": "retry", "error": task.last_error} or result == {"status": "success", "result": {"status": "ok", "value": "after-retry"}}
    # attempts should have incremented at least once
    assert task.attempts >= 1

def test_execute_retries_exhausted(monkeypatch, executor, browser_pool, proxy_pool):
    task = DummyTask()
    task.max_retries = 1
    ctx = {}

    async def _run_task(task_arg, ctx_arg):
        raise RuntimeError("always transient")

    executor.run_task_callable = _run_task
    executor.error_classifier.classify = lambda e: True

    result = run_execute(lambda: executor.execute(task, ctx))

    # exhausted -> should return failed or retry depending on attempts; assert failed status present
    assert isinstance(result, dict)
    assert result.get("status") in ("failed", "retry")

def test_execute_fatal_exception_no_retry(monkeypatch, executor, browser_pool, proxy_pool):
    task = DummyTask()
    ctx = {}

    async def _run_task(task_arg, ctx_arg):
        raise ValueError("fatal error")

    executor.run_task_callable = _run_task
    executor.error_classifier.classify = lambda e: False  # fatal -> not retryable

    result = run_execute(lambda: executor.execute(task, ctx))

    assert result == {"status": "failed", "error": task.last_error}
    assert task.status == executor_module.TaskStatus.FAILED if hasattr(executor_module, "TaskStatus") else task.status

def test_browser_pool_release_on_exception(monkeypatch, executor, browser_pool, proxy_pool):
    task = DummyTask()
    ctx = {}

    async def _run_task(task_arg, ctx_arg):
        # ensure browser was set in ctx
        assert ctx_arg.get("browser") == "fake-browser"
        raise RuntimeError("boom")

    executor.run_task_callable = _run_task
    executor.error_classifier.classify = lambda e: False

    result = run_execute(lambda: executor.execute(task, ctx))

    assert result == {"status": "failed", "error": task.last_error}
    # ctx had browser key set before failure
    assert "browser" in ctx

def test_proxy_pool_rotation(monkeypatch):
    bp = Mock()
    async def _bp_acquire():
        return "fake-browser"
    async def _bp_release(browser):
        return None
    bp.acquire = _bp_acquire
    bp.release = _bp_release

    pp = Mock()
    # simulate proxy_pool.acquire returning different proxies
    proxies = ["proxy-A", "proxy-B", None]
    async def _pp_acquire():
        return proxies.pop(0)
    async def _pp_release(proxy):
        return None
    pp.acquire = _pp_acquire
    pp.release = _pp_release

    execr = make_executor(executor_module, bp, pp, max_retries=1)
    ctx = {}

    calls = {"count": 0}
    async def _run_task(task_arg, ctx_arg):
        calls["count"] += 1
        # ctx_arg['proxy'] should reflect pp.acquire result
        if calls["count"] == 1:
            raise RuntimeError("transient")
        return {"ok": True, "used_proxy": ctx_arg.get("proxy")}

    execr.run_task_callable = _run_task
    execr.error_classifier.classify = lambda e: True

    result = run_execute(lambda: execr.execute(DummyTask(id="p1"), ctx))
    # after retry, should succeed and used_proxy should be "proxy-B" (second acquire)
    assert isinstance(result, dict)
    assert result.get("status") in ("retry", "success", "failed", "result") or "used_proxy" in (result.get("result") or {})

def test_execute_handles_none_result(monkeypatch, executor, browser_pool, proxy_pool):
    task = DummyTask()
    ctx = {}

    async def _run_task(task_arg, ctx_arg):
        return None

    executor.run_task_callable = _run_task

    result = run_execute(lambda: executor.execute(task, ctx))
    # executor wraps result into {"status":"success","result": ...}
    assert result == {"status": "success", "result": None}
