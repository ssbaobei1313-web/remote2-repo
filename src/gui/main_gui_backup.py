# coding: utf-8
"""
PyQt GUI 控制台：
- 选择账号文件
- 启动 / 停止爬虫
- 实时日志输出
"""

import sys
import asyncio
import threading
from pathlib import Path

# 关键：把项目根目录加入 Python 搜索路径
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject

from loguru import logger

from main import 加载配置
from async_runner.runner import 异步运行器
from browser_pool.browser_pool import 浏览器池
from proxy_pool.proxy_pool import ProxyPool


class 信号桥(QObject):
    日志信号 = pyqtSignal(str)
    完成信号 = pyqtSignal()


class 爬虫线程(threading.Thread):
    def __init__(self, 账号文件: Path, 信号: 信号桥):
        super().__init__(daemon=True)
        self.账号文件 = 账号文件
        self.信号 = 信号
        self._停止标记 = False

    def 停止(self):
        self._停止标记 = True

    def run(self):
        asyncio.run(self._运行异步())

    async def _运行异步(self):
        try:
            配置 = 加载配置()

            代理池 = None
            if 配置["proxy_pool"]["enable"]:
                代理池 = ProxyPool(配置["proxy_pool"])
                asyncio.create_task(代理池.auto_refresh_loop())

            浏览器池实例 = 浏览器池(配置["browser_pool"], 代理池=代理池)
            await 浏览器池实例.启动()

            运行器 = 异步运行器(
                配置=配置,
                浏览器池实例=浏览器池实例,
                账号文件=self.账号文件,
                日志回调=self._日志,
            )

            await 运行器.运行()

        except Exception as e:
            self._日志(f"[GUI ERROR] {e}")

        finally:
            self.信号.完成信号.emit()

    def _日志(self, msg: str):
        self.信号.日志信号.emit(msg)


class GUI窗口(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("企业级爬虫控制台")
        self.resize(900, 600)

        self.账号文件: Path | None = None
        self.线程: 爬虫线程 | None = None
        self.信号 = 信号桥()

        self._构建界面()
        self._连接信号()

    def _构建界面(self):
        布局 = QVBoxLayout()

        文件布局 = QHBoxLayout()
        self.文件标签 = QLabel("账号文件：未选择")
        self.选择按钮 = QPushButton("选择账号文件")
        文件布局.addWidget(self.文件标签)
        文件布局.addWidget(self.选择按钮)

        按钮布局 = QHBoxLayout()
        self.开始按钮 = QPushButton("开始运行")
        self.停止按钮 = QPushButton("停止运行")
        self.停止按钮.setEnabled(False)
        按钮布局.addWidget(self.开始按钮)
        按钮布局.addWidget(self.停止按钮)

        self.日志框 = QTextEdit()
        self.日志框.setReadOnly(True)

        布局.addLayout(文件布局)
        布局.addLayout(按钮布局)
        布局.addWidget(QLabel("运行日志："))
        布局.addWidget(self.日志框)

        self.setLayout(布局)

    def _连接信号(self):
        self.选择按钮.clicked.connect(self.选择账号文件)
        self.开始按钮.clicked.connect(self.开始运行)
        self.停止按钮.clicked.connect(self.停止运行)

        self.信号.日志信号.connect(self.追加日志)
        self.信号.完成信号.connect(self.运行结束)

    def 选择账号文件(self):
        文件路径, _ = QFileDialog.getOpenFileName(
            self, "选择账号文件", "", "Text Files (*.txt);;All Files (*)"
        )
        if 文件路径:
            self.账号文件 = Path(文件路径)
            self.文件标签.setText(f"账号文件：{self.账号文件}")
            self.追加日志(f"已选择账号文件：{self.账号文件}")

    def 开始运行(self):
        if not self.账号文件:
            self.追加日志("请先选择账号文件")
            return

        self.追加日志("开始运行爬虫任务...")
        self.开始按钮.setEnabled(False)
        self.停止按钮.setEnabled(True)

        self.线程 = 爬虫线程(self.账号文件, self.信号)
        self.线程.start()

    def 停止运行(self):
        if self.线程:
            self.追加日志("正在请求停止任务...")
            self.线程.停止()

    def 追加日志(self, msg: str):
        self.日志框.append(msg)
        self.日志框.moveCursor(self.日志框.textCursor().End)

    def 运行结束(self):
        self.追加日志("任务已结束。")
        self.开始按钮.setEnabled(True)
        self.停止按钮.setEnabled(False)
        self.线程 = None


def main():
    app = QApplication(sys.argv)
    窗口 = GUI窗口()
    窗口.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
