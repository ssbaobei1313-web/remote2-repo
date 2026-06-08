import asyncio
from loguru import logger

class BrowserPool:
    def __init__(self, playwright, config, pool_size=3, pages_per_browser=3):
        self.playwright = playwright
        self.config = config
        self.pool_size = pool_size
        self.pages_per_browser = pages_per_browser
        self.browsers = []
        self.pages = asyncio.Queue()

    async def init_pool(self):
        logger.info(f"初始化浏览器池：{self.pool_size} 个浏览器，每个 {self.pages_per_browser} 个页面")

        browser_type = self.config["browser_type"]
        headless = self.config["headless"]
        slow_mo = self.config["slow_mo"]

        for _ in range(self.pool_size):
            browser = getattr(self.playwright, browser_type).launch(
                headless=headless,
                slow_mo=slow_mo
            )
            context = browser.new_context()

            for _ in range(self.pages_per_browser):
                page = context.new_page()
                await self.pages.put(page)

            self.browsers.append((browser, context))

        logger.success("浏览器池初始化完成。")

    async def acquire_page(self):
        page = await self.pages.get()
        return page

    async def release_page(self, page):
        await self.pages.put(page)

    async def close(self):
        logger.info("关闭浏览器池...")
        for browser, context in self.browsers:
            context.close()
            browser.close()
        logger.success("浏览器池已关闭。")
