# -*- coding: utf-8 -*-
"""
信号桥（signal_bridge）
用于跨线程、跨模块传递信号的统一封装
目前为预留模块，未来可扩展：
- 自定义信号
- 跨线程数据传递
- 多模块事件总线
"""

from PyQt5.QtCore import QObject, pyqtSignal


class 信号桥(QObject):
    """统一信号桥，可扩展更多信号"""

    # 示例信号（可按需扩展）
    日志信号 = pyqtSignal(str)
    进度信号 = pyqtSignal(int, int)
    状态信号 = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
