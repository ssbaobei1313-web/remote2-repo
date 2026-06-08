# -*- coding: utf-8 -*-
"""
状态更新器（status_updater）
负责统一读取：
- 浏览器池状态
- 代理池状态
- 任务状态（队列 / 失败 / 重试）
"""

class 状态更新器:
    """统一封装浏览器池 / 代理池 / 任务状态的读取逻辑"""

    # ============================================================
    # 浏览器池状态
    # ============================================================
    @staticmethod
    def 获取浏览器池状态(browser_pool):
        """
        返回：
        {
            "total": 总数,
            "idle": 空闲,
            "busy": 正在运行
        }
        """
        if not browser_pool:
            return {"total": 0, "idle": 0, "busy": 0}

        try:
            total = browser_pool.总浏览器数()
            idle = browser_pool.空闲浏览器数()
            busy = total - idle
            return {"total": total, "idle": idle, "busy": busy}
        except Exception:
            return {"total": 0, "idle": 0, "busy": 0}

    # ============================================================
    # 代理池状态
    # ============================================================
    @staticmethod
    def 获取代理池状态(proxy_pool):
        """
        返回：
        {
            "total": 总代理数,
            "available": 可用代理数,
            "bad": 不可用代理数
        }
        """
        if not proxy_pool:
            return {"total": 0, "available": 0, "bad": 0}

        try:
            total = proxy_pool.总代理数()
            available = proxy_pool.可用代理数()
            bad = total - available
            return {"total": total, "available": available, "bad": bad}
        except Exception:
            return {"total": 0, "available": 0, "bad": 0}

    # ============================================================
    # 任务状态（队列 / 失败 / 重试）
    # ============================================================
    @staticmethod
    def 获取任务状态(runner):
        """
        返回：
        {
            "queue": 剩余任务数,
            "fail": 失败任务数,
            "retry": 重试次数
        }
        """
        if not runner:
            return {"queue": 0, "fail": 0, "retry": 0}

        try:
            queue = runner.剩余任务数
            fail = runner.失败数
            retry = runner.重试数
            return {"queue": queue, "fail": fail, "retry": retry}
        except Exception:
            return {"queue": 0, "fail": 0, "retry": 0}
