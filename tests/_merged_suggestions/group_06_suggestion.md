# 合并建议组 6

**涉及文件**: test_runner_core.py, test_runner_worker.py

**相似测试函数**:
- `test_runner_core.py` :: `DummyScheduler`
- `test_runner_worker.py` :: `DummyScheduler`

**建议**:
- 选择最通用、覆盖面最广的断言作为保留版本。
- 统一 fixture 名称与作用域（session/function）。
- 将重复的 setup/teardown 提取到 `conftest.py`。
- 如果存在同步/异步差异，保留两个版本并在名字中标注 `_async` 或 `_sync`。

**自动合并草案（仅供参考，需人工审查）**

```python
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
```