# -*- coding: utf-8 -*-
"""
Playwright 抓取工具 GUI 主窗口（模块化架构）
"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

# ===== 导入模块化组件 =====
from widgets.control_panel import 控制面板
from widgets.log_viewer import 日志窗口
from widgets.status_panel import 状态面板
from widgets.progress_panel import 进度面板
from widgets.browser_detail_panel import 浏览器详情面板

from workers.async_worker import 异步任务线程
from utils.message_box import 弹窗工具


class 主窗口(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Playwright 抓取工具 GUI（模块化版）")
        self.resize(1100, 950)

        # 运行时对象
        self.config_path = None
        self.browser_pool = None
        self.proxy_pool = None
        self.runner = None
        self.worker = None

        # ===== 初始化 UI =====
        self._init_ui()

    # --------------------------
    # UI 初始化
    # --------------------------
    def _init_ui(self):
        layout = QVBoxLayout()

        # 控件：按钮区域
        self.control_panel = 控制面板(self)

        # 控件：状态面板（浏览器池 / 代理池 / 队列 / 失败 / 重试）
        self.status_panel = 状态面板(self)

        # 控件：任务进度条
        self.progress_panel = 进度面板(self)

        # 控件：浏览器实例详情
        self.browser_detail_panel = 浏览器详情面板(self)

        # 控件：日志窗口
        self.log_viewer = 日志窗口(self)

        # 添加到布局
        layout.addWidget(self.control_panel)
        layout.addWidget(self.status_panel)
        layout.addWidget(self.progress_panel)
        layout.addWidget(self.browser_detail_panel)
        layout.addWidget(self.log_viewer)

        self.setLayout(layout)

    # ============================================================
    # 以下方法由 control_panel 调用（主窗口作为控制中心）
    # ============================================================

    def 选择配置文件(self, path: str):
        self.config_path = path
        self.log_viewer.输出日志(f"[INFO] 已选择配置文件：{path}")

    def 启动任务(self, browser_pool, proxy_pool, runner):
        """由 control_panel 调用，启动异步线程"""
        self.browser_pool = browser_pool
        self.proxy_pool = proxy_pool
        self.runner = runner

        # 创建异步线程
        self.worker = 异步任务线程(self.runner)

        # 信号连接
        self.worker.log_signal.connect(self.log_viewer.输出日志)
        self.worker.progress_signal.connect(self.progress_panel.更新进度)
        self.worker.finished_signal.connect(self.任务结束回调)

        # 启动线程
        self.worker.start()
        self.log_viewer.输出日志("[INFO] 任务已启动（后台运行中）")

    def 暂停任务(self):
        if self.runner:
            try:
                self.runner.暂停()
                self.log_viewer.输出日志("[WARNING] 任务已暂停")
            except Exception as e:
                self.log_viewer.输出日志(f"[ERROR] 暂停任务失败：{e}")

    def 恢复任务(self):
        if self.runner:
            try:
                self.runner.恢复()
                self.log_viewer.输出日志("[INFO] 任务已恢复")
            except Exception as e:
                self.log_viewer.输出日志(f"[ERROR] 恢复任务失败：{e}")

    def 停止任务(self):
        if self.worker:
            try:
                self.worker.stop()
                self.log_viewer.输出日志("[WARNING] 正在停止任务…")
            except Exception as e:
                self.log_viewer.输出日志(f"[ERROR] 停止任务失败：{e}")

    def 导出日志(self, text: str):
        """由 control_panel 调用"""
        from workers.export_log import 导出日志到文件
        path = 导出日志到文件(text)
        self.log_viewer.输出日志(f"[INFO] 日志已导出：{path}")

    # --------------------------
    # 任务结束回调
    # --------------------------
    def 任务结束回调(self):
        self.log_viewer.输出日志("[INFO] 任务已结束")
        self.worker = None
        弹窗工具.信息("任务完成", "所有任务已执行完毕！")


# ============================
# 程序入口
# ============================
def main():
    app = QApplication(sys.argv)
    win = 主窗口()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
