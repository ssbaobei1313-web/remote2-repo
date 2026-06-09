# tests/test_async_runner_runner.py
import inspect
import importlib
import pytest

MODULE = "src.async_runner.runner"

def test_module_importable():
    """模块可导入"""
    m = importlib.import_module(MODULE)
    assert m is not None

def test_common_symbols_exist():
    """检查常见类/函数是否存在（Runner, run, stop, schedule）"""
    m = importlib.import_module(MODULE)
    expected = ["Runner", "run", "stop", "schedule", "Task", "TaskResult"]
    found = {name for name in expected if hasattr(m, name)}
    assert found, f"None of expected symbols found in {MODULE}. Available: {sorted([n for n in dir(m) if not n.startswith('_')])}"

def test_runner_class_basic_signature():
    """若存在 Runner 类，检查其可实例化且有 start/stop/submit 等方法（非强制）"""
    m = importlib.import_module(MODULE)
    if not hasattr(m, "Runner"):
        pytest.skip("Runner class not present; skipping Runner behavior checks")
    Runner = getattr(m, "Runner")
    assert inspect.isclass(Runner)
    try:
        inst = Runner()
    except TypeError:
        pytest.skip("Runner requires constructor args; skip instantiation test")
    for method in ("start", "stop", "submit", "run"):
        if hasattr(inst, method):
            attr = getattr(inst, method)
            assert callable(attr), f"Runner.{method} exists but is not callable"

def test_run_function_signature_if_present():
    """若存在顶级 run 函数，检查其为可调用对象"""
    m = importlib.import_module(MODULE)
    if hasattr(m, "run"):
        assert callable(getattr(m, "run"))
