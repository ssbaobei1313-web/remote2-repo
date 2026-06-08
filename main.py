# main.py
import asyncio
import sys
from PyQt5.QtWidgets import QApplication

# 导入 GUI
from gui.main_gui import MainWindow

# 导入 BrowserPool / ProxyPool / AsyncRunner
from browser_pool.browser_pool import BrowserPool
from proxy_pool.proxy_pool import ProxyPool
from async_runner.runner import Runner
from async_runner.task_model import Task


# -------------------------
# 任务逻辑（你可以替换成真实抓取）
# -------------------------
async def run_task(task: Task, ctx: dict):
    """
    示例任务逻辑：
    - 模拟网络请求
    - 模拟解析
    - 返回结构化数据
    """
    browser = ctx.get("browser")
    proxy = ctx.get("proxy")

    # 模拟 I/O
    await asyncio.sleep(1)

    return {
        "task_id": task.id,
        "url": task.payload.get("url"),
        "browser_id": browser.id if browser else None,
        "proxy": proxy.address if proxy else None,
        "result": "OK"
    }


# -------------------------
# 启动异步后台（BrowserPool / ProxyPool / AsyncRunner）
# -------------------------
async def start_backend(gui_window: MainWindow):
    # 初始化 BrowserPool
    browser_pool = BrowserPool(
        browser_count=3,
        headless=True
    )
    await browser_pool.start()

    # 初始化 ProxyPool
    proxy_pool = ProxyPool(
        proxies=[
            "http://user:pass@1.2.3.4:8000",
            "http://user:pass@5.6.7.8:8000",
            "http://user:pass@9.9.9.9:8000",
        ]
    )
    asyncio.create_task(proxy_pool.start_health_checker())

    # 初始化 AsyncRunner
    runner = Runner(
        run_task_callable=run_task,
        browser_pool=browser_pool,
        proxy_pool=proxy_pool,
        concurrency=3
    )

    # GUI 绑定 Runner
    gui_window.bind_runner(runner)
    gui_window.bind_browser_pool(browser_pool)
    gui_window.bind_proxy_pool(proxy_pool)

    # 启动 Runner
    await runner.start()

    # 自动推送测试任务
    for i in range(20):
        task = Task.new({"url": f"https://example.com/page/{i}"})
        await runner.push_task(task)

    print("后台已启动：BrowserPool + ProxyPool + AsyncRunner")


# -------------------------
# Qt + asyncio 联动
# -------------------------
def run_app():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    loop = asyncio.get_event_loop()
    loop.create_task(start_backend(window))

    # 让 Qt 和 asyncio 共存
    timer = asyncio.get_event_loop().call_later(0.01, lambda: None)

    app.exec_()


if __name__ == "__main__":
    run_app()
