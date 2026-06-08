# -*- coding: utf-8 -*-
"""
浏览器池（BrowserPool）
企业级版本：
- 管理多个浏览器实例
- 提供总数 / 空闲数统计
- 提供浏览器详情给 GUI
- 支持 Playwright 异步初始化
"""

import asyncio
from typing import List, Optional
from dataclasses import dataclass, field

from playwright.async_api import async_playwright


@dataclass
class 浏览器实例:
    """单个浏览器实例的封装"""
    id: int
    user_agent: str = ""
    ip: str = ""
    current_task_id: Optional[str] = None
    is_idle: bool = True

    # Playwright 对象
    browser: object = None
    context: object = None
    page: object = None

    # 扩展字段
    extra: dict = field(default_factory=dict)


class 浏览器池:
    """
    浏览器池：
    - 负责创建 / 管理多个浏览器实例
    - 提供统计信息给 GUI
    """

    def __init__(self, config: dict):
        self.config = config
        self.browser_list: List[浏览器实例] = []
        self.playwright = None
        self._init_from_config()

    # ============================================================
    # 初始化
    # ============================================================
    def _init_from_config(self):
        """
        根据配置初始化浏览器池
        """
        browser_count = int(self.config.get("browser_count", 3))
        default_ua = self.config.get("default_user_agent", "Mozilla/5.0")

        for i in range(browser_count):
            inst = 浏览器实例(
                id=i + 1,
                user_agent=default_ua,
                ip="",
                current_task_id=None,
                is_idle=True,
            )
            self.browser_list.append(inst)

    # ============================================================
    # Playwright 初始化
    # ============================================================
    async def 初始化真实浏览器(self):
        """
        初始化所有浏览器实例
        """
        self.playwright = await async_playwright().start()

        for inst in self.browser_list:
            browser = await self.playwright.chromium.launch(
                headless=self.config.get("headless", True)
            )
            context = await browser.new_context(user_agent=inst.user_agent)
            page = await context.new_page()

            # 获取出口 IP
            try:
                ip = await page.evaluate(
                    """async () => {
                        const res = await fetch("https://api.ipify.org?format=json");
                        const data = await res.json();
                        return data.ip;
                    }"""
                )
            except Exception:
                ip = "未知"

            inst.browser = browser
            inst.context = context
            inst.page = page
            inst.ip = ip

    # ============================================================
    # 统计信息（供 GUI 使用）
    # ============================================================
    def 总浏览器数(self) -> int:
        return len(self.browser_list)

    def 空闲浏览器数(self) -> int:
        return sum(1 for b in self.browser_list if b.is_idle)

    # ============================================================
    # 获取空闲浏览器 / 标记状态
    # ============================================================
    def 获取空闲浏览器(self) -> Optional[浏览器实例]:
        for b in self.browser_list:
            if b.is_idle:
                return b
        return None

    def 标记为忙(self, browser_id: int, task_id: str):
        for b in self.browser_list:
            if b.id == browser_id:
                b.is_idle = False
                b.current_task_id = task_id
                break

    def 标记为空闲(self, browser_id: int):
        for b in self.browser_list:
            if b.id == browser_id:
                b.is_idle = True
                b.current_task_id = None
                break

    # ============================================================
    # 浏览器详情（供 GUI 的 浏览器详情面板 使用）
    # ============================================================
    def 获取浏览器详情(self):
        result = []
        for b in self.browser_list:
            status = "idle" if b.is_idle else "busy"
            result.append(
                {
                    "id": b.id,
                    "user_agent": b.user_agent,
                    "ip": b.ip,
                    "task_id": b.current_task_id or "",
                    "status": status,
                }
            )
        return result

    # ============================================================
    # 关闭所有浏览器
    # ============================================================
    async def 关闭所有浏览器(self):
        for b in self.browser_list:
            try:
                if b.page:
                    await b.page.close()
                if b.context:
                    await b.context.close()
                if b.browser:
                    await b.browser.close()
            except Exception:
                pass

        if self.playwright:
            await self.playwright.stop()
