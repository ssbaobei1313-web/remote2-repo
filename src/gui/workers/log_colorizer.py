# -*- coding: utf-8 -*-
"""
日志着色器（log_colorizer）
负责将日志文本根据等级转换为彩色 HTML
"""

class 日志着色器:
    """将日志文本转换为彩色 HTML"""

    @staticmethod
    def 着色(text: str) -> str:
        """
        根据日志等级自动着色：
        INFO → 蓝色
        WARNING → 橙色
        ERROR → 红色
        DEBUG → 灰色
        其他 → 白色
        """

        color = "white"
        upper = text.upper()

        if "[INFO]" in upper:
            color = "#4da6ff"   # 蓝色
        elif "[WARNING]" in upper:
            color = "#ff9900"   # 橙色
        elif "[ERROR]" in upper:
            color = "#ff4d4d"   # 红色
        elif "[DEBUG]" in upper:
            color = "#bfbfbf"   # 灰色

        return f'<span style="color:{color};">{text}</span>'
