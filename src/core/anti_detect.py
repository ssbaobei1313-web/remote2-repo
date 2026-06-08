import random
import time
from typing import Optional, Dict

import requests
from fake_useragent import UserAgent
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class AntiDetect:
    # 简单 UA 池，可按需扩展
    UA_POOL = [
        # 可放一些常见浏览器 UA
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    ]

    # 简单代理池示例（可改为从文件或接口读取）
    PROXY_POOL = [
        # "http://user:pass@ip:port",
        # "http://ip:port",
    ]

    @classmethod
    def random_user_agent(cls) -> str:
        try:
            return UserAgent().random
        except Exception:
            return random.choice(cls.UA_POOL)

    @classmethod
    def random_headers(cls) -> Dict[str, str]:
        return {
            "User-Agent": cls.random_user_agent(),
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Connection": "keep-alive",
        }

    @staticmethod
    def random_delay(min_s: float = 1.0, max_s: float = 3.0):
        time.sleep(random.uniform(min_s, max_s))

    @classmethod
    def random_proxy(cls) -> Optional[Dict[str, str]]:
        if not cls.PROXY_POOL:
            return None
        proxy = random.choice(cls.PROXY_POOL)
        return {
            "http": proxy,
            "https": proxy,
        }

    @staticmethod
    def build_session() -> requests.Session:
        session = requests.Session()

        retry_strategy = Retry(
            total=5,
            backoff_factor=1,  # 指数退避：1, 2, 4, 8...
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session
