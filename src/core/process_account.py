import time
from typing import Optional

import requests

from core.anti_detect import AntiDetect
from core.page_parser import PageParser
from core.utils import logger


class AccountProcessor:
    BASE_URL = "https://example.com/user/{account}"
    MAX_RETRY_PER_ACCOUNT = 3

    def __init__(self):
        self.session = AntiDetect.build_session()

    def _request_with_anti_bot(self, url: str) -> Optional[str]:
        """
        单次请求封装：带 UA、代理、随机延迟、状态码处理。
        返回 HTML 文本或 None。
        """
        AntiDetect.random_delay()

        headers = AntiDetect.random_headers()
        proxies = AntiDetect.random_proxy()

        try:
            resp: requests.Response = self.session.get(
                url,
                headers=headers,
                proxies=proxies,
                timeout=15,
            )

            status = resp.status_code

            # 针对常见反爬状态码做处理
            if status in (403, 429):
                logger.warning(f"状态码 {status}，可能触发反爬，url={url}")
                return None

            if status >= 400:
                logger.error(f"请求失败，状态码 {status}，url={url}")
                return None

            return resp.text

        except Exception as e:
            logger.error(f"请求异常：{e}，url={url}")
            return None

    def process(self, account: str):
        url = self.BASE_URL.format(account=account)

        for attempt in range(1, self.MAX_RETRY_PER_ACCOUNT + 1):
            logger.info(f"账号 {account} 第 {attempt} 次尝试，请求 {url}")

            html = self._request_with_anti_bot(url)

            if not html:
                # 简单退避等待
                wait_s = 2 * attempt
                logger.info(f"本次失败，等待 {wait_s} 秒后重试...")
                time.sleep(wait_s)
                continue

            try:
                data = PageParser.parse(html)
                data["account"] = account
                return data
            except Exception as e:
                logger.error(f"解析失败：{e}，账号={account}")
                return None

        logger.error(f"账号 {account} 多次重试仍失败，放弃")
        return None
