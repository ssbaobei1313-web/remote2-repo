# src/async_runner/runner.py
import asyncio
import logging
from typing import Optional, Dict, Any
from async_runner.scheduler import Scheduler
from async_runner.executor import Executor
from async_runner.task_model import Task, TaskStatus
from async_runner.persistence import SQLitePersistence
from async_runner.hooks import Hooks

logger = logging.getLogger(__name__)

def run_coroutine(coro):
    """
    Run or return a coroutine in a way that works from both sync and async contexts.

    - If called from a running event loop (async context), this returns a coroutine
      that the caller should `await`. The coroutine will catch exceptions, log them,
      and return None on error.
    - If called from a synchronous context (no running loop), this will run the
      coroutine to completion using asyncio.run and return the result (or None on error).

    Usage:
        # from async code
        result = await run_coroutine(some_coro())

        # from sync code
        result = run_coroutine(some_coro())
    """
    async def _runner():
        try:
            return await coro
        except Exception:
            logger.exception("Exception while running coroutine")
            return None

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # In an existing event loop: return coroutine to be awaited by caller.
        return _runner()
    else:
        # No running loop: run to completion synchronously.
        return asyncio.run(_runner())


class Runner:
    def __init__(
        self,
        run_task_callable,
        browser_pool=None,
        proxy_pool=None,
        concurrency: int = 5,
        persistence=None,
        retry_policy=None,
        error_classifier=None,
    ):
        self.scheduler = Scheduler()
        self.executor = Executor(browser_pool, proxy_pool, run_task_callable, retry_policy, error_classifier)
        self.concurrency = concurrency
        self._workers = []
        self._stop_event = asyncio.Event()
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # 初始为未暂停
        self._running = False
        self._persistence = persistence or SQLitePersistence()
        self.hooks = Hooks()
        self._stats = {"pending": 0, "running": 0, "failed": 0, "retries": 0, "success": 0}

    async def start(self):
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        # 恢复持久化的 pending 任务
        pending = self._persistence.load_pending()
        for t in pending:
            await self.scheduler.push(t)
        # 启动 worker 协程
        for _ in range(self.concurrency):
            w = asyncio.create_task(self._worker_loop())
            self._workers.append(w)

    async def _worker_loop(self):
        while not self._stop_event.is_set():
            await self._pause_event.wait()
            task = await self.scheduler.pop()
            if task is None:
                await asyncio.sleep(0.1)
                continue
            # update stats
            self._stats['pending'] = await self.scheduler.qsize()
            self._stats['running'] += 1
            if self.hooks.on_task_start:
                self.hooks.on_task_start({"task": task, "stats": self._stats.copy()})
            ctx = {}
            res = await self.executor.execute(task, ctx)
            # handle result
            if res['status'] == 'success':
                self._stats['success'] += 1
                self._persistence.delete_task(task.id)
                if self.hooks.on_task_success:
                    self.hooks.on_task_success({"task": task, "result": res.get('result'), "stats": self._stats.copy()})
            elif res['status'] == 'retry':
                self._stats['retries'] += 1
                task.status = TaskStatus.PENDING
                await self.scheduler.push(task)
                self._persistence.save_task(task)
            else:
                self._stats['failed'] += 1
                self._persistence.save_task(task)
                if self.hooks.on_task_fail:
                    self.hooks.on_task_fail({"task": task, "error": res.get('error'), "stats": self._stats.copy()})
            self._stats['running'] -= 1
            if self.hooks.on_status_update:
                self.hooks.on_status_update(self._stats.copy())

    async def push_task(self, task: Task):
        await self.scheduler.push(task)
        self._persistence.save_task(task)
        self._stats['pending'] = await self.scheduler.qsize()
        if self.hooks.on_status_update:
            self.hooks.on_status_update(self._stats.copy())

    async def pause(self):
        self._pause_event.clear()

    async def resume(self):
        self._pause_event.set()

    async def stop(self):
        self._stop_event.set()
        # 取消 worker
        for w in self._workers:
            w.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        self._running = False

    def status(self) -> Dict[str, int]:
        return self._stats.copy()
