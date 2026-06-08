from loguru import logger

def create_browser(playwright, config):
    browser_type = config["browser_type"]
    headless = config["headless"]
    slow_mo = config["slow_mo"]

    browser = getattr(playwright, browser_type).launch(
        headless=headless,
        slow_mo=slow_mo
    )

    logger.info(f"浏览器启动：{browser_type}")
    return browser
