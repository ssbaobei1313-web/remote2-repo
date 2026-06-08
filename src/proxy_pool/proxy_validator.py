import aiohttp
import asyncio
from loguru import logger

TEST_URL = "https://httpbin.org/ip"

class ProxyValidator:
    def __init__(self, timeout=5):
        self.timeout = timeout

    async def validate(self, proxy: str) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    TEST_URL,
                    proxy=f"http://{proxy}",
                    timeout=self.timeout
                ) as resp:
                    if resp.status == 200:
                        logger.info(f"Proxy OK: {proxy}")
                        return True
        except Exception:
            pass
        logger.warning(f"Proxy BAD: {proxy}")
        return False

    async def validate_bulk(self, proxies: list[str]):
        tasks = [self.validate(p) for p in proxies]
        results = await asyncio.gather(*tasks)
        return [p for p, ok in zip(proxies, results) if ok]
