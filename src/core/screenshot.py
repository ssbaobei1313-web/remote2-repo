import os
from datetime import datetime
from loguru import logger

SNAPSHOT_DIR = "snapshots"

def take_screenshot(page, prefix="error"):
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    filename = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    path = os.path.join(SNAPSHOT_DIR, filename)
    page.screenshot(path=path, full_page=True)
    logger.error(f"错误快照已保存：{path}")
