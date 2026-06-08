# async_runner/executor.py
import asyncio
from typing import Callable, Optional, Dict, Any
from async_runner.task_model import Task, TaskStatus
from async_runner.retry_policy import RetryPolicy, ErrorClassifier

class Executor:
    def __init__(
        self,
        browser_pool,
        proxy_pool,
        run_task_callable: Callable[[Task, Dict[str, Any]], asyncio.Future],
        retry_policy: Optional[RetryPolicy] = None,
        error_classifier: Optional[ErrorClassifier] = None,
        default_timeout: float = 60.0,
    ):
        """
        run_task_callable: 用户提供的协程函数，签名 async def run_task(task: Task, ctx: Dict) -> result
        browser_pool / proxy_pool: 你的 BrowserPool / ProxyPool 实例（可为 None）
        """
        self.browser_pool = browser_pool
        self.proxy_pool = proxy_pool
        self.run_task_callable = run_task_callable
        self.retry_policy = retry_policy or RetryPolicy()
        self.error_classifier = error_classifier or ErrorClassifier()
        self.default_timeout = default_timeout

    async def execute(self, task: Task, ctx: Dict[str, Any]) -> Dict[str, Any]:
        task.status = TaskStatus.RUNNING
        task.attempts += 1
        try:
            # 可选：从 proxy_pool 获取代理
            if self.proxy_pool:
                proxy = await self.proxy_pool.acquire()
                ctx['proxy'] = proxy
            # 可选：从 browser_pool 获取浏览器实例
            if self.browser_pool:
                browser = await self.browser_pool.acquire()
                ctx['browser'] = browser

            # 执行用户提供的任务协程，带超时保护
            coro = self.run_task_callable(task, ctx)
            result = await asyncio.wait_for(coro, timeout=self.default_timeout)

            task.status = TaskStatus.SUCCESS
            return {"status": "success", "result": result}
        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            raise
        except Exception as exc:
            task.last_error = f"{exc.__class__.__name__}: {str(exc)}"
            # classify whether retryable
            retryable = self.error_classifier.classify(exc)
            if retryable and task.attempts <= task.max_retries:
                task.status = TaskStatus.RETRY
                await self.retry_policy.wait_before_retry(task.attempts)
                return {"status": "retry", "error": task.last_error}
            else:
                task.status = TaskStatus.FAILED
                return {"status": "failed", "error": task.last_error}
        finally:
            # 释放资源
            if self.browser_pool and 'browser' in ctx:
                await self.browser_pool.release(ctx['browser'])
            if self.proxy_pool and 'proxy' in ctx:
                await self.proxy_pool.release(ctx['proxy'])
