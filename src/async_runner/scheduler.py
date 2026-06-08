# async_runner/scheduler.py
import asyncio
import heapq
from typing import Dict, Optional, Tuple
from async_runner.task_model import Task
import time

class PriorityQueue:
    def __init__(self):
        self._heap = []
        self._counter = 0
        self._lock = asyncio.Lock()

    async def put(self, task: Task):
        async with self._lock:
            # 小的 priority 值表示更高优先级
            heapq.heappush(self._heap, (task.priority, self._counter, time.time(), task))
            self._counter += 1

    async def get(self) -> Optional[Task]:
        async with self._lock:
            if not self._heap:
                return None
            _, _, _, task = heapq.heappop(self._heap)
            return task

    async def qsize(self) -> int:
        async with self._lock:
            return len(self._heap)

    async def clear(self):
        async with self._lock:
            self._heap.clear()

class RateLimiter:
    """
    简单令牌桶限流器，支持 per_key 限流（例如 per-browser 或 per-proxy）
    """
    def __init__(self, rate: float, per: float = 1.0):
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.time()

    async def acquire(self):
        while True:
            now = time.time()
            elapsed = now - self.last_check
            self.last_check = now
            self.allowance += elapsed * (self.rate / self.per)
            if self.allowance > self.rate:
                self.allowance = self.rate
            if self.allowance >= 1.0:
                self.allowance -= 1.0
                return
            await asyncio.sleep(0.01)

class Scheduler:
    def __init__(self):
        self.queue = PriorityQueue()
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self._stopped = False

    async def push(self, task: Task):
        await self.queue.put(task)

    async def pop(self) -> Optional[Task]:
        return await self.queue.get()

    async def qsize(self) -> int:
        return await self.queue.qsize()

    def set_rate_limit(self, key: str, rate: float, per: float = 1.0):
        self.rate_limiters[key] = RateLimiter(rate, per)

    async def acquire_rate(self, key: Optional[str] = None):
        if key and key in self.rate_limiters:
            await self.rate_limiters[key].acquire()
        # else no rate limiting
