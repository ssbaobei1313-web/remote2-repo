# -*- coding: utf-8 -*-
"""
异步任务线程（AsyncWorker）
负责：
- 创建后台线程
- 在线程中运行 asyncio 事件循环
- 执行 AsyncRunner
- 将日志/进度通过信号发回 GUI
- 支持停止任务
"""

import asyncio
import threading
from PyQt5.QtCore import QObject, pyqtSignal


class 异步任务线程(QObject):
    """后台异步执行器：在独立线程中运行 AsyncRunner"""

    # GUI 信号
    log_signal = pyqtSignal(str)          # 日志输出
    progress_signal = pyqtSignal(int, int)  # (已完成, 总数)
    finished_signal = pyqtSignal()        # 任务结束

    def __init__(self, runner):
        """
        runner: AsyncRunner 实例
        """
        super().__init__()
        self.runner = runner
        self.loop = None
        self.thread = None

        # 将 runner 的回调绑定到信号
        self.runner.gui_log_callback = self.log_signal.emit
        self.runner.gui_progress_callback = self.progress_signal.emit

    # ============================================================
    # 启动后台线程
    # ============================================================
    def start(self):
        """启动后台线程"""
        self.thread = threading.Thread(target=self._线程入口, daemon=True)
        self.thread.start()

    # ============================================================
    # 线程入口：创建事件循环并运行爬虫
    # ============================================================
    def _线程入口(self):
        """线程内部执行：创建事件循环并运行 runner"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            self.loop.run_until_complete(self._运行任务())
        except Exception as e:
            self.log_signal.emit(f"[ERROR] 异步线程异常: {e}")
        finally:
            self.loop.close()
            self.finished_signal.emit()

    # ============================================================
    # 执行 AsyncRunner
    # ============================================================
    async def _运行任务(self):
        """执行 AsyncRunner.开始()"""
        try:
            await self.runner.开始()
        except asyncio.CancelledError:
            self.log_signal.emit("[WARNING] 任务已被取消")
        except Exception as e:
            self.log_signal.emit(f"[ERROR] 爬虫运行异常: {e}")

    # ============================================================
    # 停止任务
    # ============================================================
    def stop(self):
        """停止任务：取消所有 asyncio 任务"""
        if self.runner:
            self.runner.停止()

        if self.loop:
            for task in asyncio.all_tasks(loop=self.loop):
                task.cancel()
