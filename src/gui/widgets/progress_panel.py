# -*- coding: utf-8 -*-
"""
任务进度条（progress_panel）
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from workers.progress_handler import 进度处理器


class 进度面板(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        self.label = QLabel("任务进度：未开始")
        self.label.setStyleSheet("font-size: 14px; color: #00ff99;")

        self.bar = QProgressBar()
        self.bar.setMinimum(0)
        self.bar.setMaximum(100)
        self.bar.setValue(0)

        layout.addWidget(self.label)
        layout.addWidget(self.bar)
        self.setLayout(layout)

    # --------------------------
    # 更新进度
    # --------------------------
    def 更新进度(self, done: int, total: int):
        percent = 进度处理器.计算百分比(done, total)
        text = 进度处理器.生成进度文本(done, total, percent)

        self.label.setText(text)
        self.bar.setValue(percent)
