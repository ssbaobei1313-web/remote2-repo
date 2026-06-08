import asyncio
import aiohttp
from loguru import logger

class ProxySources:
    def __init__(self, sources: list[str]):
        self.sources = sources

    async def fetch_source(self, session, url):
        try:
            async with session.get(url, timeout=10) as resp:
                text = await resp.text()
                proxies = [line.strip() for line in text.split("\n") if ":" in line]
                logger.info(f"Fetched {len(proxies)} proxies from {url}")
                return proxies
        except Exception as e:
            logger.error(f"Failed to fetch proxies from {url}: {e}")
            return []

    async def fetch_all(self):
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_source(session, url) for url in self.sources]
            results = await asyncio.gather(*tasks)
            proxies = set()
            for r in results:
                proxies.update(r)
            return list(proxies)
