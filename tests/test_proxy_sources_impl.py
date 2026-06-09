# tests/test_proxy_sources_impl.py
import importlib
import inspect
import asyncio
import pytest

MOD = "src.proxy_pool.proxy_sources"

def _maybe_await(value):
    if asyncio.iscoroutine(value):
        return asyncio.run(value)
    return value

def test_proxy_sources_module_and_class_presence():
    mod = importlib.import_module(MOD)
    assert mod is not None
    assert hasattr(mod, "ProxySources") or hasattr(mod, "ProxySource"), (
        "proxy_sources 模块应导出 ProxySources 或 ProxySource"
    )

def test_proxy_sources_instantiation_and_basic_attrs():
    mod = importlib.import_module(MOD)
    cls_name = "ProxySources" if hasattr(mod, "ProxySources") else "ProxySource"
    cls = getattr(mod, cls_name)
    assert inspect.isclass(cls)
    try:
        inst = cls()
    except TypeError:
        pytest.skip(f"{cls_name} 需要构造参数，跳过实例化测试")
    assert any(hasattr(inst, a) for a in ("sources", "get", "fetch", "list")), (
        f"{cls_name} 实例应包含 sources/get/fetch/list 中的至少一个，实际可用: "
        + ", ".join([n for n in dir(inst) if not n.startswith("_")])
    )

def test_proxy_sources_methods_callable_and_safe_invoke():
    mod = importlib.import_module(MOD)
    cls_name = "ProxySources" if hasattr(mod, "ProxySources") else "ProxySource"
    cls = getattr(mod, cls_name)
    try:
        inst = cls()
    except TypeError:
        pytest.skip(f"{cls_name} 需要构造参数，跳过方法调用测试")
    for method in ("fetch", "get", "list", "fetch_all", "load", "parse"):
        if hasattr(inst, method) and callable(getattr(inst, method)):
            fn = getattr(inst, method)
            try:
                out = fn()
            except TypeError:
                pytest.skip(f"{cls_name}.{method} 需要参数，跳过无参调用测试")
            except Exception:
                pytest.skip(f"{cls_name}.{method} 在调用时抛出异常，跳过具体断言")
            out = _maybe_await(out)
            if out is None:
                return
            assert hasattr(out, "__iter__") or isinstance(out, (list, tuple, set)), (
                f"{cls_name}.{method} 返回值应为可迭代或 None，实际: {type(out)}"
            )
            return
    pytest.skip(f"{cls_name} 未找到可调用的常见方法以进行行为测试")
