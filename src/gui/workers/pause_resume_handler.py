# -*- coding: utf-8 -*-
"""
暂停 / 恢复 任务处理模块（pause_resume_handler）
负责：
- 封装 Runner 的暂停 / 恢复 方法
- 保证 GUI 调用逻辑统一
"""

class 暂停恢复处理器:
    """暂停 / 恢复 任务的统一封装"""

    @staticmethod
    def 暂停(runner):
        """
        调用 Runner 的暂停方法
        """
        if runner is None:
            return False

        try:
            runner.暂停()
            return True
        except Exception:
            return False

    @staticmethod
    def 恢复(runner):
        """
        调用 Runner 的恢复方法
        """
        if runner is None:
            return False

        try:
            runner.恢复()
            return True
        except Exception:
            return False
