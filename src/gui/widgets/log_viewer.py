# -*- coding: utf-8 -*-
"""
日志窗口（log_viewer）
负责：
- 彩色日志显示
- 自动滚动到底部
"""

from PyQt5.QtWidgets import QTextEdit
from workers.log_colorizer import 日志着色器
from loguru import logger


class 日志窗口(QTextEdit):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self.setReadOnly(True)

    # --------------------------
    # 输出日志（彩色 + 自动滚动）
    # --------------------------
    def 输出日志(self, text: str):
        html = 日志着色器.着色(text)
        self.append(html)

        # 自动滚动到底部
        self.moveCursor(self.textCursor().End)

        # 同步写入 loguru
        logger.info(text)

    # --------------------------
    # 获取纯文本（用于导出）
    # --------------------------
    def 获取纯文本(self) -> str:
        return self.toPlainText()
