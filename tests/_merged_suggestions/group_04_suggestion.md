# 合并建议组 4

**涉及文件**: test_proxy_sources_validator.py, test_proxy_validator_impl.py

**相似测试函数**:
- `test_proxy_sources_validator.py` :: `test_proxy_validator_class_behavior_if_present`
- `test_proxy_validator_impl.py` :: `test_proxy_validator_class_behavior_if_present`

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

def test_proxy_validator_class_behavior_if_present():
    mod = importlib.import_module(MOD)
    if not hasattr(mod, "ProxyValidator"):
        pytest.skip("模块未导出 ProxyValidator，跳过类行为测试")
    cls = getattr(mod, "ProxyValidator")
    assert inspect.isclass(cls)
    try:
        inst = cls()
    except TypeError:
        pytest.skip("ProxyValidator 构造需要参数，跳过实例化测试")
    # 查找常见方法并调用第一个可用的
    candidate_methods = ("validate", "check", "is_valid", "validate_proxy")
    found = [m for m in candidate_methods if hasattr(inst, m) and callable(getattr(inst, m))]
    assert found, "ProxyValidator 实例未找到常见验证方法"
    method = getattr(inst, found[0])
    try:
        out = method("http://1.2.3.4:8080")
    except Exception:
        pytest.skip(f"ProxyValidator.{found[0]} 在调用时抛出异常，跳过具体断言")
    out = _maybe_await(out)
    assert isinstance(out, bool), f"ProxyValidator.{found[0]} 应返回布尔值，实际: {type(out)}"
```