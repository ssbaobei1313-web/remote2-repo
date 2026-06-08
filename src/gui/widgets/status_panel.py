# -*- coding: utf-8 -*-
"""
状态面板（status_panel）
负责显示：
- 浏览器池状态
- 代理池状态
- 任务队列 / 失败 / 重试
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import QTimer
from workers.status_updater import 状态更新器


class 状态面板(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self._init_ui()
        self._init_timer()

    def _init_ui(self):
        layout = QVBoxLayout()

        self.browser_label = QLabel("浏览器池状态：未启动")
        self.browser_label.setStyleSheet("font-size: 14px; color: #00ccff;")

        self.proxy_label = QLabel("代理池状态：未启动")
        self.proxy_label.setStyleSheet("font-size: 14px; color: #ffcc00;")

        self.queue_label = QLabel("任务队列：未开始")
        self.queue_label.setStyleSheet("font-size: 14px; color: #ffaa00;")

        self.fail_label = QLabel("失败任务：0")
        self.fail_label.setStyleSheet("font-size: 14px; color: #ff4444;")

        self.retry_label = QLabel("重试次数：0")
        self.retry_label.setStyleSheet("font-size: 14px; color: #ff66cc;")

        layout.addWidget(self.browser_label)
        layout.addWidget(self.proxy_label)
        layout.addWidget(self.queue_label)
        layout.addWidget(self.fail_label)
        layout.addWidget(self.retry_label)

        self.setLayout(layout)

    # --------------------------
    # 定时刷新
    # --------------------------
    def _init_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.刷新状态)
        self.timer.start(1000)

    # --------------------------
    # 刷新所有状态
    # --------------------------
    def 刷新状态(self):
        # 浏览器池
        b = 状态更新器.获取浏览器池状态(self.main.browser_pool)
        self.browser_label.setText(
            f"浏览器池状态：总数 {b['total']} | 空闲 {b['idle']} | 运行中 {b['busy']}"
        )

        # 代理池
        p = 状态更新器.获取代理池状态(self.main.proxy_pool)
        self.proxy_label.setText(
            f"代理池状态：总数 {p['total']} | 可用 {p['available']} | 不可用 {p['bad']}"
        )

        # 任务状态
        t = 状态更新器.获取任务状态(self.main.runner)
        self.queue_label.setText(f"任务队列剩余：{t['queue']}")
        self.fail_label.setText(f"失败任务：{t['fail']}")
        self.retry_label.setText(f"重试次数：{t['retry']}")
