# tests/test_runner_retry_and_persistence.py
import os
import tempfile
import pytest
from src.async_runner import runner

def test_persistence_write_and_recover(tmp_path, monkeypatch):
    # 假设 runner 使用 runner.PERSIST_DIR 或类似配置
    monkeypatch.setenv("RUNNER_PERSIST_DIR", str(tmp_path))
    # 模拟写入状态并调用恢复接口
    runner.persist_task_state("task1", {"status":"pending"})
    recovered = runner.load_persisted_tasks()
    assert "task1" in recovered
