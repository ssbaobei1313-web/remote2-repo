# mydg_crawler.py
# -*- coding: utf-8 -*-
"""
增强版 Playwright 爬虫：
- loguru 日志
- portalocker 文件锁
- config.yaml 配置支持
- Playwright 致命错误快照
- 自动等待用户放入 Final_accounts_List 文件
- 完整脚本，无省略号
"""

import os
import sys
import time
import traceback
from datetime import datetime

import portalocker
import yaml
from loguru import logger
from playwright.sync_api import sync_playwright, Page, Browser, Playwright

# =========================
# 全局常量
# =========================

CONFIG_PATH = "config.yaml"
ACCOUNTS_FILE = "Final_accounts_List.txt"
LOCK_FILE = "mydg_crawler.lock"
LOG_DIR = "logs"
SNAPSHOT_DIR = "snapshots"


# =========================
# 工具函数区
# =========================

def ensure_directories() -> None:
    """
    确保日志目录、快照目录存在
    """
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)


def init_logger() -> None:
    """
    初始化 loguru 日志
    """
    ensure_directories()

    # 控制台输出
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
    )

    # 文件输出
    log_file_path = os.path.join(LOG_DIR, "mydg_crawler_{time:YYYYMMDD}.log")
    logger.add(
        log_file_path,
        rotation="00:00",
        retention="7 days",
        encoding="utf-8",
        level="INFO",
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    logger.info("日志系统初始化完成。")


def load_config(config_path: str = CONFIG_PATH) -> dict:
    """
    加载 config.yaml 配置文件
    若不存在则使用默认配置并给出提示
    """
    default_config = {
        "target_url": "https://example.com/login",
        "headless": True,
        "slow_mo": 0,
        "lock_timeout": 10,
        "navigation_timeout": 30000,
        "screenshot_on_error": True,
        "browser_type": "chromium",  # chromium / firefox / webkit
    }

    if not os.path.exists(config_path):
        logger.warning(f"未找到配置文件 {config_path}，将使用默认配置。")
        return default_config

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        config = {**default_config, **data}
        logger.info(f"已加载配置文件 {config_path}。")
        return config
    except Exception as e:
        logger.exception(f"加载配置文件 {config_path} 失败，将使用默认配置。错误：{e}")
        return default_config


def wait_for_final_accounts_file(file_path: str = ACCOUNTS_FILE) -> None:
    """
    自动等待用户放入 Final_accounts_List 文件
    """
    if not os.path.exists(file_path):
        logger.warning(f"未找到 {file_path} 文件，请将账号列表放入该文件。")
        logger.warning("程序将持续等待，直到你放入文件为止...\n")

        while not os.path.exists(file_path):
            time.sleep(1)

        logger.success(f"检测到 {file_path} 文件，继续执行程序。")
    else:
        logger.info(f"检测到账号文件 {file_path}，准备读取账号列表。")


def read_accounts(file_path: str = ACCOUNTS_FILE) -> list:
    """
    从账号文件中读取账号列表
    每行一个账号，可根据需要扩展为 账号|密码 等格式
    """
    accounts = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                accounts.append(line)
        logger.info(f"共读取到 {len(accounts)} 个账号。")
    except Exception as e:
        logger.exception(f"读取账号文件 {file_path} 失败：{e}")
        raise
    return accounts


def acquire_file_lock(lock_file: str = LOCK_FILE, timeout: int = 10):
    """
    获取文件锁，防止多进程/多实例同时运行
    使用方法：
        with acquire_file_lock():
            # 受锁保护的代码
    """
    logger.info(f"尝试获取文件锁：{lock_file}，超时时间：{timeout} 秒。")
    lock = portalocker.Lock(
        lock_file,
        mode="a+",
        timeout=timeout,
        flags=portalocker.LOCK_EX
    )
    return lock


def take_error_screenshot(page: Page, prefix: str = "fatal_error") -> str:
    """
    在发生致命错误时截图保存
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.png"
        filepath = os.path.join(SNAPSHOT_DIR, filename)
        page.screenshot(path=filepath, full_page=True)
        logger.error(f"已保存错误快照：{filepath}")
        return filepath
    except Exception as e:
        logger.exception(f"保存错误快照失败：{e}")
        return ""


def create_browser(playwright: Playwright, config: dict) -> Browser:
    """
    根据配置创建浏览器实例
    """
    browser_type = config.get("browser_type", "chromium").lower()
    headless = config.get("headless", True)
    slow_mo = config.get("slow_mo", 0)

    if browser_type == "firefox":
        browser = playwright.firefox.launch(headless=headless, slow_mo=slow_mo)
    elif browser_type == "webkit":
        browser = playwright.webkit.launch(headless=headless, slow_mo=slow_mo)
    else:
        browser = playwright.chromium.launch(headless=headless, slow_mo=slow_mo)

    logger.info(f"已启动浏览器：{browser_type}，headless={headless}, slow_mo={slow_mo}")
    return browser


def process_single_account(page: Page, account: str, config: dict) -> None:
    """
    针对单个账号执行 Playwright 操作
    这里根据你的实际业务逻辑进行修改：
    - 打开登录页
    - 输入账号/密码
    - 提交表单
    - 抓取数据
    """
    target_url = config.get("target_url")
    navigation_timeout = config.get("navigation_timeout", 30000)

    logger.info(f"开始处理账号：{account}")

    # 设置页面超时
    page.set_default_timeout(navigation_timeout)

    # 示例逻辑：打开目标页面
    page.goto(target_url)

    # TODO: 根据你的实际页面结构，填写以下操作
    # 例如：
    # page.fill("input[name='username']", account)
    # page.fill("input[name='password']", "your_password")
    # page.click("button[type='submit']")
    # page.wait_for_load_state("networkidle")

    # 这里仅做示例输出
    logger.info(f"账号 {account} 已访问目标页面：{target_url}")

    # 你可以在这里添加更多业务逻辑，如抓取数据、导出文件等
    # ...


# =========================
# 主逻辑区
# =========================

def main() -> None:
    """
    主入口逻辑：
    - 初始化日志
    - 加载配置
    - 等待账号文件
    - 获取文件锁
    - 启动 Playwright
    - 逐个账号执行任务
    """
    init_logger()
    logger.info("程序启动。")

    config = load_config(CONFIG_PATH)

    # 等待用户放入账号文件
    wait_for_final_accounts_file(ACCOUNTS_FILE)

    # 读取账号列表
    accounts = read_accounts(ACCOUNTS_FILE)
    if not accounts:
        logger.error("账号列表为空，程序结束。")
        return

    # 获取文件锁，防止多实例并发
    lock_timeout = config.get("lock_timeout", 10)
    try:
        with acquire_file_lock(LOCK_FILE, timeout=lock_timeout):
            logger.info("已成功获取文件锁，开始执行爬虫任务。")

            with sync_playwright() as p:
                browser = None
                context = None
                page = None
                try:
                    browser = create_browser(p, config)
                    context = browser.new_context()
                    page = context.new_page()

                    for idx, account in enumerate(accounts, start=1):
                        logger.info(f"===== 正在处理第 {idx}/{len(accounts)} 个账号：{account} =====")
                        try:
                            process_single_account(page, account, config)
                            logger.info(f"账号 {account} 处理完成。")
                        except Exception as e:
                            logger.error(f"处理账号 {account} 时发生错误：{e}")
                            logger.error(traceback.format_exc())
                            if config.get("screenshot_on_error", True) and page is not None:
                                take_error_screenshot(page, prefix=f"account_{idx}_error")

                    logger.info("所有账号处理完成。")

                except Exception as e:
                    logger.error(f"Playwright 全局执行过程中发生致命错误：{e}")
                    logger.error(traceback.format_exc())
                    if config.get("screenshot_on_error", True) and page is not None:
                        take_error_screenshot(page, prefix="fatal_error")
                finally:
                    if context is not None:
                        context.close()
                    if browser is not None:
                        browser.close()
                    logger.info("浏览器已关闭。")

    except portalocker.exceptions.LockException as e:
        logger.error(f"获取文件锁失败，可能已有其他实例在运行：{e}")
    except Exception as e:
        logger.exception(f"主流程发生未捕获异常：{e}")
    finally:
        logger.info("程序结束。")


# =========================
# 程序入口
# =========================

if __name__ == "__main__":
    main()
