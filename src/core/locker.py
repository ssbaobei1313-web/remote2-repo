import portalocker
from loguru import logger

def acquire_lock(lock_file="mydg_crawler.lock", timeout=10):
    logger.info(f"尝试获取文件锁：{lock_file}")
    return portalocker.Lock(lock_file, timeout=timeout)
