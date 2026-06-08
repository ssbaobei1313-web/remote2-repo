# -*- coding: utf-8 -*-
"""
弹窗工具（message_box）
负责：
- 信息提示
- 警告提示
- 错误提示
"""

from PyQt5.QtWidgets import QMessageBox


class 弹窗工具:
    """统一封装 QMessageBox"""

    @staticmethod
    def 信息(title: str, text: str):
        QMessageBox.information(None, title, text)

    @staticmethod
    def 警告(title: str, text: str):
        QMessageBox.warning(None, title, text)

    @staticmethod
    def 错误(title: str, text: str):
        QMessageBox.critical(None, title, text)
