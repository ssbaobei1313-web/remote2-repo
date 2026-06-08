# -*- coding: utf-8 -*-
"""
控制面板（control_panel）
负责：
- 选择配置文件
- 开始任务
- 暂停任务
- 恢复任务
- 停止任务
- 导出日志
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QFileDialog
from pathlib import Path
from main import 加载配置 as load_config
from browser_pool.browser_pool import 浏览器池 as BrowserPool
from proxy_pool.proxy_pool import ProxyPool
from async_runner.runner import 异步运行器 as AsyncRunner


class 控制面板(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout()

        self.btn_select = QPushButton("选择配置文件")
        self.btn_start = QPushButton("开始运行")
        self.btn_pause = QPushButton("暂停任务")
        self.btn_resume = QPushButton("恢复任务")
        self.btn_stop = QPushButton("停止任务")
        self.btn_export = QPushButton("导出日志")

        self.btn_select.clicked.connect(self.选择配置文件)
        self.btn_start.clicked.connect(self.开始任务)
        self.btn_pause.clicked.connect(self.main.暂停任务)
        self.btn_resume.clicked.connect(self.main.恢复任务)
        self.btn_stop.clicked.connect(self.main.停止任务)
        self.btn_export.clicked.connect(self.导出日志)

        layout.addWidget(self.btn_select)
        layout.addWidget(self.btn_start)
        layout.addWidget(self.btn_pause)
        layout.addWidget(self.btn_resume)
        layout.addWidget(self.btn_stop)
        layout.addWidget(self.btn_export)

        self.setLayout(layout)

    # --------------------------
    # 选择配置文件
    # --------------------------
    def 选择配置文件(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择配置文件",
            str(Path.cwd()),
            "JSON Files (*.json);;All Files (*.*)"
        )
        if file_path:
            self.main.选择配置文件(file_path)

    # --------------------------
    # 开始任务
    # --------------------------
    def 开始任务(self):
        if not self.main.config_path:
            self.main.log_viewer.输出日志("[WARNING] 请先选择配置文件")
            return

        config = load_config(self.main.config_path)

        browser_pool = BrowserPool(config)
        proxy_pool = ProxyPool(config)
        runner = AsyncRunner(config, browser_pool, proxy_pool, self.main)

        self.main.启动任务(browser_pool, proxy_pool, runner)

    # --------------------------
    # 导出日志
    # --------------------------
    def 导出日志(self):
        text = self.main.log_viewer.获取纯文本()
        self.main.导出日志(text)
