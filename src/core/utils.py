from loguru import logger
import os


os.makedirs("output", exist_ok=True)
logger.add("output/log.txt", encoding="utf-8", rotation="1 MB")
