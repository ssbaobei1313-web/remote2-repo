import os
import time
from loguru import logger

def wait_for_accounts(file_path="data/Final_accounts_List.txt"):
    if not os.path.exists(file_path):
        logger.warning(f"未找到 {file_path}，等待用户放入文件...")
        while not os.path.exists(file_path):
            time.sleep(1)
        logger.success(f"检测到文件：{file_path}")
    else:
        logger.info(f"检测到账号文件：{file_path}")
