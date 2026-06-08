import os
import sys
from loguru import logger

LOG_DIR = "logs"

def init_logger():
    os.makedirs(LOG_DIR, exist_ok=True)

    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>"
    )

    logger.add(
        f"{LOG_DIR}/mydg_{'{time:YYYYMMDD}'}.log",
        rotation="00:00",
        retention="7 days",
        encoding="utf-8",
        enqueue=True,
        backtrace=True,
        diagnose=True
    )

    logger.info("日志系统初始化完成。")
    return logger
