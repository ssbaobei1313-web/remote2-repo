# tests/test_async_runner_runner_impl.py
import asyncio
from unittest.mock import Mock, AsyncMock

import pytest

from src.async_runner.runner import Runner
from src.async_runner.task_model import TaskStatus


class SimpleTask:
    def __init__(self, task_id="t1", status=TaskStatus.PENDING):
        self.id = task_id
        self.status = status


@pytest.mark.asyncio
async def test_runner_任务成功路径():
    async def dummy_run(task, ctx):
        return "ok"

    mock_persistence = Mock()
    mock_retry_policy = Mock()
    mock_error_classifier = Mock()

    runner = Runner(
        dummy_run,
        browser_pool=None,
        proxy_pool=None,
        concurrency=1,
        persistence=mock_persistence,
        retry_policy=mock_retry_policy,
        error_classifier=mock_error_classifier,
    )

    mock_executor = AsyncMock()
    mock_executor.execute.return_value = {"status": "success", "result": "执行成功"}
    runner.executor = mock_executor

    mock_scheduler = AsyncMock()
    task = SimpleTask("task-success")
    mock_scheduler.pop.side_effect = [task, None]
    mock_scheduler.qsize.return_value = 0
    runner.scheduler = mock_scheduler

    on_task_start = Mock()
    on_task_success = Mock()
    on_task_fail = Mock()
    on_status_update = Mock()
    runner.hooks.on_task_start = on_task_start
    runner.hooks.on_task_success = on_task_success
    runner.hooks.on_task_fail = on_task_fail
    runner.hooks.on_status_update = on_status_update

    async def run_worker_once():
        worker = asyncio.create_task(runner._worker_loop())
        await asyncio.sleep(0.05)
        runner._stop_event.set()
        await worker

    await run_worker_once()

    mock_executor.execute.assert_awaited_once()
    mock_persistence.delete_task.assert_called_once_with(task.id)
    mock_persistence.save_task.assert_not_called()
    on_task_success.assert_called_once()
    on_task_fail.assert_not_called()


@pytest.mark.asyncio
async def test_runner_任务重试路径():
    async def dummy_run(task, ctx):
        return "ok"

    mock_persistence = Mock()
    mock_retry_policy = Mock()
    mock_error_classifier = Mock()

    runner = Runner(
        dummy_run,
        browser_pool=None,
        proxy_pool=None,
        concurrency=1,
        persistence=mock_persistence,
        retry_policy=mock_retry_policy,
        error_classifier=mock_error_classifier,
    )

    mock_executor = AsyncMock()
    mock_executor.execute.return_value = {"status": "retry", "error": "临时错误"}
    runner.executor = mock_executor

    mock_scheduler = AsyncMock()
    task = SimpleTask("task-retry")
    mock_scheduler.pop.side_effect = [task, None]
    mock_scheduler.qsize.return_value = 0
    runner.scheduler = mock_scheduler

    on_task_success = Mock()
    on_task_fail = Mock()
    runner.hooks.on_task_success = on_task_success
    runner.hooks.on_task_fail = on_task_fail

    async def run_worker_once():
        worker = asyncio.create_task(runner._worker_loop())
        await asyncio.sleep(0.05)
        runner._stop_event.set()
        await worker

    await run_worker_once()

    mock_executor.execute.assert_awaited_once()
    mock_persistence.save_task.assert_called_once_with(task)
    mock_persistence.delete_task.assert_not_called()
    mock_scheduler.push.assert_awaited_once_with(task)
    on_task_fail.assert_not_called()
    on_task_success.assert_not_called()


@pytest.mark.asyncio
async def test_runner_任务失败路径():
    async def dummy_run(task, ctx):
        return "ok"

    mock_persistence = Mock()
    mock_retry_policy = Mock()
    mock_error_classifier = Mock()

    runner = Runner(
        dummy_run,
        browser_pool=None,
        proxy_pool=None,
        concurrency=1,
        persistence=mock_persistence,
        retry_policy=mock_retry_policy,
        error_classifier=mock_error_classifier,
    )

    mock_executor = AsyncMock()
    mock_executor.execute.return_value = {"status": "fail", "error": "致命错误"}
    runner.executor = mock_executor

    mock_scheduler = AsyncMock()
    task = SimpleTask("task-fail")
    mock_scheduler.pop.side_effect = [task, None]
    mock_scheduler.qsize.return_value = 0
    runner.scheduler = mock_scheduler

    on_task_success = Mock()
    on_task_fail = Mock()
    runner.hooks.on_task_success = on_task_success
    runner.hooks.on_task_fail = on_task_fail

    async def run_worker_once():
        worker = asyncio.create_task(runner._worker_loop())
        await asyncio.sleep(0.05)
        runner._stop_event.set()
        await worker

    await run_worker_once()

    mock_executor.execute.assert_awaited_once()
    mock_persistence.save_task.assert_called_once_with(task)
    mock_persistence.delete_task.assert_not_called()
    on_task_fail.assert_called_once()
    on_task_success.assert_not_called()
