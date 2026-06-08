# -*- coding: utf-8 -*-
"""
日志导出模块（export_log）
负责：
- 将日志文本保存到文件
- 自动生成文件名（带时间戳）
"""

import datetime


class 日志导出器:
    """日志导出工具"""

    @staticmethod
    def 导出(text: str) -> str:
        """
        将日志文本保存到文件
        返回：保存的文件路径
        """
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = f"log_{now}.txt"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)

        return file_path


# 供外部调用的简单函数
def 导出日志到文件(text: str) -> str:
    """
    外部统一调用接口
    """
    return 日志导出器.导出(text)
