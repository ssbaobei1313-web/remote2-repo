# tests/test_runner_concurrency.py
import pytest
import asyncio
from src.async_runner import runner

@pytest.mark.asyncio
async def test_concurrent_tasks_complete():
    async def work(i):
        await asyncio.sleep(0.01)
        return i * i

    tasks = [runner.run_coroutine(work(i)) for i in range(20)]
    results = await asyncio.gather(*tasks)
    assert results == [i * i for i in range(20)]
