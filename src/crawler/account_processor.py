from loguru import logger

async def process_account(page, account, config):
    logger.info(f"开始处理账号：{account}")

    page.set_default_timeout(config["navigation_timeout"])
    await page.goto(config["target_url"])

    logger.info(f"账号 {account} 已访问目标页面。")

    # TODO: 你的业务逻辑
