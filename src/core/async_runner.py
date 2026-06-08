import asyncio
from loguru import logger
from crawler.account_processor import process_account
from core.screenshot import take_screenshot

class AsyncRunner:
    def __init__(self, browser_pool, accounts, config):
        self.browser_pool = browser_pool
        self.accounts = accounts
        self.config = config

    async def worker(self, account):
        page = await self.browser_pool.acquire_page()
        try:
            await process_account(page, account, self.config)
        except Exception as e:
            logger.exception(f"账号 {account} 处理失败：{e}")
            if self.config["screenshot_on_error"]:
                take_screenshot(page, prefix=f"{account}_error")
        finally:
            await self.browser_pool.release_page(page)

    async def run(self):
        tasks = [self.worker(account) for account in self.accounts]
        await asyncio.gather(*tasks)
