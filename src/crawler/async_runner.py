from loguru import logger
from core.screenshot import take_screenshot
from crawler.account_processor import process_account
from core.browser import create_browser

def run_accounts(playwright, accounts, config):
    browser = None
    context = None
    page = None

    try:
        browser = create_browser(playwright, config)
        context = browser.new_context()
        page = context.new_page()

        for idx, account in enumerate(accounts, start=1):
            logger.info(f"===== {idx}/{len(accounts)} =====")
            try:
                process_account(page, account, config)
            except Exception as e:
                logger.exception(f"账号 {account} 处理失败：{e}")
                if config["screenshot_on_error"]:
                    take_screenshot(page, prefix=f"account_{idx}_error")

    finally:
        if context:
            context.close()
        if browser:
            browser.close()
        logger.info("浏览器已关闭。")
