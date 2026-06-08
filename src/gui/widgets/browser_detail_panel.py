# -*- coding: utf-8 -*-
"""
浏览器实例详情面板（browser_detail_panel）
显示：
- 浏览器 ID
- User-Agent
- 出口 IP
- 当前任务 ID
- 状态（空闲 / 运行中）
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import QTimer


class 浏览器详情面板(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self._init_ui()
        self._init_timer()

    def _init_ui(self):
        layout = QVBoxLayout()

        self.title = QLabel("浏览器实例详情")
        self.title.setStyleSheet("font-size: 16px; font-weight: bold; color: #00ccff;")

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["浏览器ID", "User-Agent", "出口IP", "任务ID", "状态"])

        layout.addWidget(self.title)
        layout.addWidget(self.table)
        self.setLayout(layout)

    # --------------------------
    # 定时刷新
    # --------------------------
    def _init_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.刷新浏览器详情)
        self.timer.start(2000)  # 每 2 秒刷新一次

    # --------------------------
    # 刷新浏览器实例详情
    # --------------------------
    def 刷新浏览器详情(self):
        if not self.main.browser_pool:
            return

        try:
            details = self.main.browser_pool.获取浏览器详情()
        except Exception:
            return

        self.table.setRowCount(len(details))

        for row, item in enumerate(details):
            self.table.setItem(row, 0, QTableWidgetItem(str(item.get("id", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(item.get("user_agent", "")))
            self.table.setItem(row, 2, QTableWidgetItem(item.get("ip", "")))
            self.table.setItem(row, 3, QTableWidgetItem(str(item.get("task_id", ""))))
            self.table.setItem(row, 4, QTableWidgetItem(item.get("status", "")))
