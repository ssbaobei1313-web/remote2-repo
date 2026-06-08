import os
import yaml
from loguru import logger

CONFIG_PATH = "config/config.yaml"

DEFAULT_CONFIG = {
    "target_url": "https://example.com/login",
    "headless": True,
    "slow_mo": 0,
    "lock_timeout": 10,
    "navigation_timeout": 30000,
    "browser_type": "chromium",
    "screenshot_on_error": True
}

def load_config():
    if not os.path.exists(CONFIG_PATH):
        logger.warning(f"未找到配置文件 {CONFIG_PATH}，使用默认配置。")
        return DEFAULT_CONFIG

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        cfg = {**DEFAULT_CONFIG, **cfg}
        logger.info("配置文件加载完成。")
        return cfg
    except Exception as e:
        logger.exception(f"加载配置文件失败：{e}")
        return DEFAULT_CONFIG
