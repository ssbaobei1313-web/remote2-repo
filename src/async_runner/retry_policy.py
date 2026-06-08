# async_runner/retry_policy.py
import asyncio
import math
from typing import Callable, Optional

class RetryPolicy:
    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0, factor: float = 2.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.factor = factor

    def next_delay(self, attempt: int) -> float:
        delay = self.base_delay * (self.factor ** (attempt - 1))
        return min(delay, self.max_delay)

    async def wait_before_retry(self, attempt: int):
        delay = self.next_delay(attempt)
        await asyncio.sleep(delay)

class ErrorClassifier:
    """
    将异常分类为可重试或不可重试。
    用户可继承并覆盖 classify 方法。
    """
    def classify(self, exc: Exception) -> bool:
        # 默认：网络相关异常可重试，其他不可重试
        # 这里用简单规则，生产中可扩展
        name = exc.__class__.__name__.lower()
        if "timeout" in name or "connection" in name or "network" in name:
            return True
        return False
