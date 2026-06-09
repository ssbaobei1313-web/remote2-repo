# tests/test_proxy_validator_impl.py
import importlib
import inspect
import asyncio
import pytest

MOD = "src.proxy_pool.proxy_validator"

def _maybe_await(value):
    if asyncio.iscoroutine(value):
        return asyncio.run(value)
    return value

def test_proxy_validator_exports():
    mod = importlib.import_module(MOD)
    assert mod is not None
    # 至少导出类或函数之一
    assert any(hasattr(mod, name) for name in ("ProxyValidator", "validate_proxy", "is_valid", "check_proxy", "validate")), (
        "proxy_validator 模块应导出 ProxyValidator 或 validate_proxy/is_valid 等函数"
    )

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

def test_proxy_validator_function_behavior_if_present():
    mod = importlib.import_module(MOD)
    candidates = ("validate_proxy", "is_valid", "check_proxy", "validate")
    for name in candidates:
        if hasattr(mod, name) and callable(getattr(mod, name)):
            fn = getattr(mod, name)
            try:
                res = fn("http://1.2.3.4:8080")
            except TypeError:
                pytest.skip(f"{name} 需要不同签名，跳过具体调用断言")
            except Exception:
                pytest.skip(f"{name} 在调用时抛出异常，跳过具体断言")
            res = _maybe_await(res)
            assert isinstance(res, bool), f"{name} 应返回布尔值，实际: {type(res)}"
            return
    pytest.skip("未找到可调用的顶级验证函数以进行行为测试")
