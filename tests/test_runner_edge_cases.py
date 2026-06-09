import asyncio
import pytest
from unittest.mock import Mock, AsyncMock

from async_runner.runner import Runner
from async_runner.task_model import Task, TaskStatus


@pytest.mark.asyncio
async def test_start_恢复持久化任务并创建_workers():
    """start：应恢复 pending 任务，并创建 concurrency 数量的 worker"""

    # 构造持久化：返回两个 pending 任务
    mock_persistence = Mock()
    mock_persistence.load_pending.return_value = [
        Task(id="t1", payload={"a": 1}),
        Task(id="t2", payload={"b": 2}),
    ]

    # scheduler.push 是 async
    mock_scheduler = AsyncMock()

    # executor 不会被调用
    mock_executor = AsyncMock()

    runner = Runner(
        run_task_callable=lambda: None,
        persistence=mock_persistence,
    )
    runner.scheduler = mock_scheduler
    runner.executor = mock_executor

    await runner.start()

    # pending 任务应被 push
    assert mock_scheduler.push.await_count == 2

    # worker 数量应等于 concurrency
    assert len(runner._workers) == runner.concurrency


@pytest.mark.asyncio
async def test_worker_idle_when_no_task():
    """worker_loop：pop 返回 None 时应 idle 等待，不应调用 executor"""

    mock_scheduler = AsyncMock()
    mock_scheduler.pop.return_value = None

    mock_executor = AsyncMock()
    mock_persistence = Mock()

    runner = Runner(
        run_task_callable=lambda: None,
        persistence=mock_persistence,
    )
    runner.scheduler = mock_scheduler
    runner.executor = mock_executor

    await runner.start()

    # 等待 worker idle 一下
    await asyncio.sleep(0.15)

    mock_executor.execute.assert_not_called()


@pytest.mark.asyncio
async def test_worker_success路径_更新stats并调用hooks():
    """成功路径：delete_task、success_hook、stats 更新"""

    mock_scheduler = AsyncMock()
    mock_scheduler.pop.side_effect = [
        Task(id="t1", payload={}),
        None,  # 第二次 idle
    ]

    mock_executor = AsyncMock()
    mock_executor.execute.return_value = {"status": "success", "result": 123}

    mock_persistence = Mock()

    mock_on_start = Mock()
    mock_on_success = Mock()
    mock_on_update = Mock()

    runner = Runner(
        run_task_callable=lambda: None,
        persistence=mock_persistence,
    )
    runner.scheduler = mock_scheduler
    runner.executor = mock_executor

    # 注入 hooks
    runner.hooks.on_task_start = mock_on_start
    runner.hooks.on_task_success = mock_on_success
    runner.hooks.on_status_update = mock_on_update

    await runner.start()
    await asyncio.sleep(0.1)

    mock_persistence.delete_task.assert_called_once_with("t1")
    mock_on_success.assert_called_once()
    assert runner._stats["success"] == 1


@pytest.mark.asyncio
async def test_worker_retry路径_重新入队并保存任务():
    """retry 路径：task.status 应重置为 PENDING，并重新 push"""

    task = Task(id="t1", payload={})

    mock_scheduler = AsyncMock()
    mock_scheduler.pop.side_effect = [task, None]

    mock_executor = AsyncMock()
    mock_executor.execute.return_value = {"status": "retry", "error": "tmp"}

    mock_persistence = Mock()

    runner = Runner(
        run_task_callable=lambda: None,
        persistence=mock_persistence,
    )
    runner.scheduler = mock_scheduler
    runner.executor = mock_executor

    await runner.start()
    await asyncio.sleep(0.1)

    # 任务应被重新 push
    assert mock_scheduler.push.await_count == 1
    assert task.status == TaskStatus.PENDING
    mock_persistence.save_task.assert_called()


@pytest.mark.asyncio
async def test_worker_failure路径_保存失败并调用hook():
    """failure 路径：save_task、fail_hook、stats"""

    task = Task(id="t1", payload={})

    mock_scheduler = AsyncMock()
    mock_scheduler.pop.side_effect = [task, None]

    mock_executor = AsyncMock()
    mock_executor.execute.return_value = {"status": "fail", "error": "fatal"}

    mock_persistence = Mock()

    mock_on_fail = Mock()

    runner = Runner(
        run_task_callable=lambda: None,
        persistence=mock_persistence,
    )
    runner.scheduler = mock_scheduler
    runner.executor = mock_executor
    runner.hooks.on_task_fail = mock_on_fail

    await runner.start()
    await asyncio.sleep(0.1)

    mock_persistence.save_task.assert_called_once()
    mock_on_fail.assert_called_once()
    assert runner._stats["failed"] == 1


@pytest.mark.asyncio
async def test_pause_resume_控制worker执行():
    """pause/resume：pause 后 worker 不执行任务，resume 后继续"""

    task = Task(id="t1", payload={})

    mock_scheduler = AsyncMock()
    mock_scheduler.pop.return_value = task

    mock_executor = AsyncMock()
    mock_executor.execute.return_value = {"status": "success"}

    mock_persistence = Mock()

    runner = Runner(
        run_task_callable=lambda: None,
        persistence=mock_persistence,
    )
    runner.scheduler = mock_scheduler
    runner.executor = mock_executor

    await runner.start()
    await runner.pause()

    await asyncio.sleep(0.05)
    mock_executor.execute.assert_not_called()

    await runner.resume()
    await asyncio.sleep(0.05)

    mock_executor.execute.assert_called_once()


@pytest.mark.asyncio
async def test_stop_取消所有worker并清空列表():
    """stop：应 cancel 所有 worker，并清空 worker 列表"""

    mock_scheduler = AsyncMock()
    mock_executor = AsyncMock()
    mock_persistence = Mock()

    runner = Runner(
        run_task_callable=lambda: None,
        persistence=mock_persistence,
    )
    runner.scheduler = mock_scheduler
    runner.executor = mock_executor

    await runner.start()
    assert len(runner._workers) > 0

    await runner.stop()

    # 所有 worker 都应被取消
    assert len(runner._workers) == 0
    assert runner._running is False
