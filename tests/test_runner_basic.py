# tests/test_runner_basic.py
import asyncio
import threading
import time
import pytest
from src.async_runner import runner

@pytest.mark.asyncio
async def test_run_coroutine_in_existing_loop_returns_value():
    async def coro(x):
        await asyncio.sleep(0)
        return x * 2

    # 在已有 loop 中直接调用（避免 RuntimeError）
    result = await runner.run_coroutine(coro(3))
    assert result == 6

def test_run_coroutine_from_sync_thread_returns_value():
    async def coro():
        await asyncio.sleep(0)
        return "ok"

    # 同步上下文调用，runner 应处理创建或使用后台 loop
    result = runner.run_coroutine(coro())
    assert result == "ok"

@pytest.mark.asyncio
async def test_run_coroutine_handles_exception_and_logs(caplog):
    async def bad():
        raise ValueError("boom")

    res = await runner.run_coroutine(bad())
    # 根据实现，可能返回 None 或抛出；这里假设返回 None 并记录日志
    assert res is None
    assert any("boom" in rec.message for rec in caplog.records)
