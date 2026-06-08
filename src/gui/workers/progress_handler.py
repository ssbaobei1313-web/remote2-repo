# -*- coding: utf-8 -*-
"""
任务进度处理模块（progress_handler）
负责：
- 根据已完成 / 总数 计算百分比
- 生成进度文本
"""

class 进度处理器:
    """任务进度计算与格式化"""

    @staticmethod
    def 计算百分比(done: int, total: int) -> int:
        """根据已完成 / 总数 计算百分比"""
        if total <= 0:
            return 0
        if done < 0:
            done = 0
        if done > total:
            done = total
        return int(done / total * 100)

    @staticmethod
    def 生成进度文本(done: int, total: int, percent: int) -> str:
        """生成进度显示文本"""
        if total <= 0:
            return "任务进度：未开始"
        return f"任务进度：{done} / {total}（{percent}%）"
