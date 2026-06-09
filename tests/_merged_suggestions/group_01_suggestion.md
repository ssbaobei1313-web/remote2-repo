# 合并建议组 1

**涉及文件**: test_executor.py

**相似测试函数**:
- `test_executor.py` :: `browser_pool`
- `test_executor.py` :: `proxy_pool`

**建议**:
- 选择最通用、覆盖面最广的断言作为保留版本。
- 统一 fixture 名称与作用域（session/function）。
- 将重复的 setup/teardown 提取到 `conftest.py`。
- 如果存在同步/异步差异，保留两个版本并在名字中标注 `_async` 或 `_sync`。

**自动合并草案（仅供参考，需人工审查）**

```python
# tests/test_executor.py
import pytest
from unittest.mock import Mock
import types
import asyncio

# 调整为你项目中实际的导入路径
from src.async_runner import executor as executor_module

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
```