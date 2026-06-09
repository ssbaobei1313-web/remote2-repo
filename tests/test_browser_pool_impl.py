# tests/test_browser_pool_impl.py
import asyncio
import importlib
import pytest
from unittest.mock import MagicMock, AsyncMock

# 导入实际模块
MODULE_PATH = "src.browser_pool.browser_pool"
bp_mod = importlib.import_module(MODULE_PATH)

# 获取中文类名
浏览器池 = getattr(bp_mod, "浏览器池", None)
浏览器实例 = getattr(bp_mod, "浏览器实例", None)

assert 浏览器池 is not None, "模块未导出 浏览器池 类，请确认 src/browser_pool/browser_pool.py"
assert 浏览器实例 is not None, "模块未导出 浏览器实例 dataclass，请确认 src/browser_pool/browser_pool.py"


def test_init_and_stats_and_details():
    cfg = {"browser_count": 3, "default_user_agent": "UA-TEST"}
    pool = 浏览器池(cfg)

    # 总数与空闲数
    assert pool.总浏览器数() == 3
    assert pool.空闲浏览器数() == 3

    # 获取空闲浏览器与详情结构
    inst = pool.获取空闲浏览器()
    assert isinstance(inst, 浏览器实例)
    details = pool.获取浏览器详情()
    assert isinstance(details, list)
    assert len(details) == 3
    for d in details:
        assert "id" in d and "user_agent" in d and "ip" in d and "status" in d

    # 标记为忙/空闲
    pool.标记为忙(inst.id, "task-1")
    assert pool.空闲浏览器数() == 2
    pool.标记为空闲(inst.id)
    assert pool.空闲浏览器数() == 3


@pytest.mark.asyncio
async def test_初始化真实浏览器_and_ip(monkeypatch):
    """
    模拟 async_playwright 行为，测试 初始化真实浏览器() 能正确设置 browser/context/page/ip 字段
    并在 evaluate 抛异常时回退为 '未知'
    """
    # fake page.evaluate 返回 ip
    fake_page = MagicMock()
    fake_page.evaluate = AsyncMock(return_value="1.2.3.4")
    fake_context = MagicMock()
    fake_context.new_page = AsyncMock(return_value=fake_page)
    fake_browser = MagicMock()
    fake_browser.new_context = AsyncMock(return_value=fake_context)

    # fake_playwright.chromium.launch 返回 fake_browser
    fake_playwright = MagicMock()
    fake_playwright.chromium = MagicMock()
    fake_playwright.chromium.launch = AsyncMock(return_value=fake_browser)

    # async_playwright 必须是可调用的函数，返回一个对象，该对象的 start 是 async 函数
    def fake_async_playwright():
        return MagicMock(start=AsyncMock(return_value=fake_playwright))

    # patch async_playwright 名称到模块
    monkeypatch.setitem(bp_mod.__dict__, "async_playwright", fake_async_playwright)

    cfg = {"browser_count": 2, "default_user_agent": "UA-TEST", "headless": True}
    pool = 浏览器池(cfg)

    # 调用初始化真实浏览器
    await pool.初始化真实浏览器()

    # 每个实例应有 browser/context/page/ip 被设置
    for inst in pool.browser_list:
        assert inst.browser is fake_browser
        assert inst.context is fake_context
        assert inst.page is fake_page
        assert inst.ip == "1.2.3.4"

    # 关闭所有浏览器应能调用 page/context/browser.close 与 playwright.stop
    fake_page.close = AsyncMock()
    fake_context.close = AsyncMock()
    fake_browser.close = AsyncMock()
    fake_playwright.stop = AsyncMock()

    await pool.关闭所有浏览器()

    # 断言关闭被调用
    assert fake_page.close.await_count >= 1
    assert fake_context.close.await_count >= 1
    assert fake_browser.close.await_count >= 1
    assert fake_playwright.stop.await_count == 1


@pytest.mark.asyncio
async def test_初始化真实浏览器_evaluate_exception(monkeypatch):
    """
    当 page.evaluate 抛异常时，ip 应为 '未知'，且不会抛出未捕获异常
    """
    fake_page = MagicMock()
    fake_page.evaluate = AsyncMock(side_effect=Exception("net error"))
    fake_context = MagicMock()
    fake_context.new_page = AsyncMock(return_value=fake_page)
    fake_browser = MagicMock()
    fake_browser.new_context = AsyncMock(return_value=fake_context)

    fake_playwright = MagicMock()
    fake_playwright.chromium = MagicMock()
    fake_playwright.chromium.launch = AsyncMock(return_value=fake_browser)

    def fake_async_playwright():
        return MagicMock(start=AsyncMock(return_value=fake_playwright))

    monkeypatch.setitem(bp_mod.__dict__, "async_playwright", fake_async_playwright)

    cfg = {"browser_count": 1, "default_user_agent": "UA-TEST"}
    pool = 浏览器池(cfg)

    await pool.初始化真实浏览器()

    inst = pool.browser_list[0]
    assert inst.ip == "未知"

    # 清理
    fake_page.close = AsyncMock()
    fake_context.close = AsyncMock()
    fake_browser.close = AsyncMock()
    fake_playwright.stop = AsyncMock()
    await pool.关闭所有浏览器()
