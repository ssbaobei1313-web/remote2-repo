# 合并建议组 3

**涉及文件**: test_proxy_sources_validator.py, test_proxy_validator_impl.py

**相似测试函数**:
- `test_proxy_sources_validator.py` :: `test_proxy_validator_exports`
- `test_proxy_validator_impl.py` :: `test_proxy_validator_exports`

**建议**:
- 选择最通用、覆盖面最广的断言作为保留版本。
- 统一 fixture 名称与作用域（session/function）。
- 将重复的 setup/teardown 提取到 `conftest.py`。
- 如果存在同步/异步差异，保留两个版本并在名字中标注 `_async` 或 `_sync`。

**自动合并草案（仅供参考，需人工审查）**

```python
﻿# tests/test_proxy_validator_impl.py
import importlib
import inspect
import asyncio
import pytest

MOD = "src.proxy_pool.proxy_validator"

def test_proxy_validator_exports():
    mod = importlib.import_module(MOD)
    assert mod is not None
    # 至少导出类或函数之一
    assert any(hasattr(mod, name) for name in ("ProxyValidator", "validate_proxy", "is_valid", "check_proxy", "validate")), (
        "proxy_validator 模块应导出 ProxyValidator 或 validate_proxy/is_valid 等函数"
    )
```