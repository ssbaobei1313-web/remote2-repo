#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
彩票网站数据爬取工具 v5.6 - mydg.live
Sheet2 配置（查询列/查询年/查询月/查询日）+ Sheet1 账号数据
输出：QueryAcct + DrawRange 两列
修复：中断数据保留 / 异常日志 / 日期标志逻辑 / 列越界提示 / 嵌套函数提升
      DrawRange 数值排序 / finally IO 保护 / Playwright 致命错误处理
      ws None 明确报错 / 提取页面数据性能优化 / 输入框等待可见
      sessionid 输出脱敏 / UA 常量命名规范
"""

import pandas as pd
import random
import sys
import re
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from playwright.sync_api import sync_playwright, Page, Error as PlaywrightError

# ============================================================
# ⚙️  配置区（按需修改）
# ============================================================

HEADLESS             = False                    # True=无头，False=显示窗口
OUTPUT_FILE          = "mydg_receipts_all.xlsx" # 输出文件名
ACCOUNT_CACHE        = "accounts_with_data.txt" # 有数据账号缓存文件
ACCOUNT_LIST_KEYWORD = "Final_accounts_List"    # 用户名单文件名匹配关键词

# User-Agent 池，每次启动随机选一个，降低指纹重复率
USER_AGENT_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.122 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
]

# ============================================================
# 反爬工具函数
# ============================================================

def 人类延迟(最小ms: int = 600, 最大ms: int = 1800) -> int:
    """正态分布随机延迟，让操作节奏更接近真人"""
    均值   = (最小ms + 最大ms) / 2
    标准差 = (最大ms - 最小ms) / 6
    结果   = int(random.gauss(均值, 标准差))
    return max(最小ms, min(最大ms, 结果))


def 模拟打字(page: Page, 输入框, 文字: str):
    """逐字符输入，随机键入间隔，模拟人类打字节奏"""
    输入框.click()
    page.keyboard.press("Control+A")
    page.keyboard.press("Delete")
    for 字符 in 文字:
        page.keyboard.type(字符)
        page.wait_for_timeout(random.randint(70, 200))  # 每键 70-200ms


def 随机鼠标游走(page: Page):
    """分段贝塞尔式鼠标移动，模拟人类手部抖动轨迹"""
    起点x = random.randint(300, 900)
    起点y = random.randint(200, 600)
    终点x = random.randint(200, 1400)
    终点y = random.randint(100, 800)
    步数  = random.randint(6, 14)
    for i in range(步数):
        进度 = (i + 1) / 步数
        x = int(起点x + (终点x - 起点x) * 进度 + random.randint(-12, 12))
        y = int(起点y + (终点y - 起点y) * 进度 + random.randint(-8, 8))
        page.mouse.move(x, y)
        page.wait_for_timeout(random.randint(18, 55))


def 随机滚动(page: Page):
    """15% 概率随机上下滚动，模拟人类浏览习惯"""
    if random.random() < 0.15:
        距离 = random.randint(80, 250)
        page.mouse.wheel(0, 距离)
        page.wait_for_timeout(random.randint(200, 500))
        page.mouse.wheel(0, -距离)


def 注入反检测脚本(page: Page):
    """
    注入 JS 脚本隐藏 Playwright/WebDriver 自动化特征，
    使浏览器表现与普通用户一致
    """
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'ms', 'en']
        });
        if (!window.chrome) {
            window.chrome = { runtime: {} };
        }
        const _origQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (params) =>
            params.name === 'notifications'
                ? Promise.resolve({ state: Notification.permission })
                : _origQuery(params);
    """)


# ============================================================
# 工具函数（模块级，可复用）
# ============================================================

def 提取整数(原始值: str, 字段名: str) -> int:
    """
    [修复5] 从字符串提取第一个整数，防止 pandas 将数字读成 "2026.0"。
    原为嵌套函数，提升为模块级避免重复定义，支持复用。
    """
    匹配 = re.search(r'(\d+)', 原始值)
    if not 匹配:
        raise ValueError(f"Sheet2 '{字段名}' 值 '{原始值}' 无法解析为整数")
    return int(匹配.group(1))


def DrawRange排序键(值: str) -> tuple:
    """从 '(N/M) ...' 提取数值排序键，容忍任意空格/填零格式"""
    匹配 = re.match(r'^\((\d+)/(\d+)\)', 值.strip())
    if 匹配:
        return (int(匹配.group(1)), int(匹配.group(2)))
    return (9999, 9999)


# ============================================================
# Excel 读取：从 Final_accounts_List 获取账号列表和查询日期
# ============================================================

def 读取用户名单(folder: str = ".") -> tuple:
    """
    扫描目录，找到文件名含 ACCOUNT_LIST_KEYWORD 的最新 Excel 文件，读取：

    Sheet2（查询配置，第2行为数据行）：
        列A = 查询列字母（A / B / C / D / E / F）
        列B = 查询年（如 2026）
        列C = 查询月（如 5）
        列D = 查询日（如 31）
        → 拼接日期：YYYYMMDD = "20260531"

    Sheet1（账号数据）：
        第1行 = 表头（User A / User B / ...）
        第2行起 = 实际账号

    返回 (账号列表: list, 查询日期: str)
    """
    查询目录 = Path(folder)
    所有xlsx = list(查询目录.glob("*.xlsx")) + list(查询目录.glob("*.xls"))

    候选文件列表 = [
        f for f in 所有xlsx
        if ACCOUNT_LIST_KEYWORD.lower() in f.name.lower()
        and f.name != OUTPUT_FILE
    ]

    if not 候选文件列表:
        raise FileNotFoundError(
            f"当前目录未找到含 '{ACCOUNT_LIST_KEYWORD}' 关键词的 Excel 文件"
        )

    最新文件 = max(候选文件列表, key=lambda f: f.stat().st_mtime)
    print(f"📋 用户名单: {最新文件.name}")

    配置df = pd.read_excel(最新文件, sheet_name=1, header=0, dtype=str)

    配置行    = 配置df.iloc[0]
    查询列字母 = str(配置行["查询列"]).strip().upper()
    查询年原始 = str(配置行["查询年"]).strip()
    查询月原始 = str(配置行["查询月"]).strip()
    查询日原始 = str(配置行["查询日"]).strip()

    查询年 = 提取整数(查询年原始, "查询年")
    查询月 = 提取整数(查询月原始, "查询月")
    查询日 = 提取整数(查询日原始, "查询日")

    if len(查询列字母) != 1 or not 查询列字母.isalpha():
        raise ValueError(f"Sheet2 '查询列' 值 '{查询列字母}' 无效，应为单个字母（A~F）")

    查询日期 = f"{查询年:04d}{查询月:02d}{查询日:02d}"

    账号df    = pd.read_excel(最新文件, sheet_name=0, header=0, dtype=str)
    数据列索引 = ord(查询列字母) - ord('A')

    if 数据列索引 >= len(账号df.columns):
        raise ValueError(
            f"Sheet2 查询列='{查询列字母}'（第 {数据列索引+1} 列），"
            f"但 Sheet1 只有 {len(账号df.columns)} 列，请检查配置"
        )

    列名 = 账号df.columns[数据列索引]

    账号列表 = (
        账号df[列名]
        .dropna()
        .str.strip()
        .tolist()
    )
    账号列表 = [a for a in 账号列表 if a and a.lower() != "nan"]

    return 账号列表, 查询日期


# ============================================================
# 账号缓存：只写不读，记录本次有数据的账号供人工参考
# ============================================================

def 保存有数据账号(账号集合: set):
    """将有返回数据的账号持久化到缓存文件（追加模式，历史记录不丢失）"""
    旧缓存  = set()
    缓存路径 = Path(ACCOUNT_CACHE)
    if 缓存路径.exists():
        旧缓存 = set(缓存路径.read_text(encoding="utf-8").splitlines())

    合并缓存 = 旧缓存 | 账号集合
    缓存路径.write_text(
        "\n".join(sorted(合并缓存)) + "\n",
        encoding="utf-8"
    )
    print(f"💾 缓存已更新: 本次 {len(账号集合)} 个 | 累计 {len(合并缓存)} 个 → {ACCOUNT_CACHE}")


# ============================================================
# 实时写入 Excel（崩溃保护）
# ============================================================

def 追加写入Excel(行数据列表: list, 输出路径: Path):
    """
    [修复1] 崩溃保护：有数据立即追加写入，不等循环结束。
    - 文件不存在：创建并写入表头 + 数据
    - 文件已存在：追加到已有数据末尾（不覆盖历史）
    """
    新行df = pd.DataFrame(行数据列表, columns=["QueryAcct", "DrawRange"])

    if not 输出路径.exists():
        新行df.to_excel(输出路径, index=False)
    else:
        wb = load_workbook(输出路径)
        ws = wb.active
        if ws is None:
            raise RuntimeError(
                f"'{输出路径}' 没有活动工作表，文件可能已损坏，请手动删除后重试"
            )
        for row in dataframe_to_rows(新行df, index=False, header=False):
            ws.append(row)
        wb.save(输出路径)


# ============================================================
# 解析函数
# ============================================================

def 解析DrawRange(文本: str) -> str:
    """
    在 *** 分隔符后，提取第一个 (数字/数字) 令牌。
    示例：*** 后第一行为 (1/29) → 返回 "(1/29)"
    """
    遇到分隔符 = False
    for 行 in (l.strip() for l in 文本.split("\n") if l.strip()):
        if 行 == "***":
            遇到分隔符 = True
        elif 遇到分隔符 and re.match(r"^\(\d+/\d+\)", 行):
            return 行
    return ""


def 提取页面数据(page: Page, 账号: str) -> list:
    """
    遍历页面所有 <td> 文本，识别彩票收据（含日期格式 D:dd/mm/yy 且含 Total(）。
    返回 [{"QueryAcct": ..., "DrawRange": ...}, ...] 列表。
    优化：单次 evaluate 批量获取所有 td 文本，减少 IPC 调用。
    """
    结果列表 = []

    try:
        page.wait_for_selector("td", timeout=2000)
    except Exception:
        pass

    try:
        所有td文本: list[str] = page.evaluate(
            "() => Array.from(document.querySelectorAll('td')).map(td => td.innerText)"
        )
        for 原始文本 in 所有td文本:
            if re.search(r"D:\d+/\d+/\d+", 原始文本) and "Total(" in 原始文本:
                if re.search(r"Void\s*:", 原始文本, re.IGNORECASE):
                    continue
                dr = 解析DrawRange(原始文本)
                if not dr:
                    continue
                结果列表.append({
                    "QueryAcct": 账号,
                    "DrawRange": dr,
                })
    except Exception as e:
        print(f"[错误] 提取页面数据失败（{账号}）: {type(e).__name__}: {e}")

    return 结果列表


# ============================================================
# 主程序
# ============================================================

def main():
    print("=" * 70)
    print("🚀 彩票网站数据爬取工具 v5.6 - mydg.live")
    print("=" * 70)

    try:
        全部账号, 查询日期 = 读取用户名单(".")
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ {e}")
        sys.exit(1)

    print(f"👥 账号总数  : {len(全部账号)} 个")
    print(f"📅 查询日期  : {查询日期}")
    print(f"🌐 浏览器模式: {'无头模式' if HEADLESS else '显示窗口'}")
    print("=" * 70 + "\n")

    有数据账号  = set()
    全部数据    = []
    输出路径    = Path(OUTPUT_FILE)

    if 输出路径.exists():
        输出路径.unlink()
        print(f"🗑️  已清空旧输出文件，本次重新写入")

    with sync_playwright() as p:
        选用UA = random.choice(USER_AGENT_LIST)
        视口宽  = random.randint(1680, 1920)
        视口高  = random.randint(900, 1080)

        浏览器 = None
        序号   = 0

        try:
            浏览器 = p.chromium.launch(
                headless=HEADLESS,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-infobars",
                    f"--window-size={视口宽},{视口高}",
                ],
            )
            上下文 = 浏览器.new_context(
                viewport={"width": 视口宽, "height": 视口高},
                user_agent=选用UA,
                locale="zh-CN",
                timezone_id="Asia/Kuala_Lumpur",
                geolocation={
                    "latitude":  3.14 + random.uniform(-0.3, 0.3),
                    "longitude": 101.69 + random.uniform(-0.3, 0.3),
                },
                permissions=["geolocation"],
            )
            页面 = 上下文.new_page()

            注入反检测脚本(页面)

            print("🌐 正在打开登录页面...")
            页面.goto("https://www.mydg.live/007/loginpage.jsp", wait_until="domcontentloaded")

            print("\n" + "=" * 70)
            print("👤 请在打开的浏览器中手动登录")
            print("   登录成功后将自动跳转，无需按回车")
            print("=" * 70 + "\n")

            print("⏳ 等待登录跳转到公告页面（最多3分钟）...")
            页面.wait_for_url("**/notice.jsp**", timeout=180000)
            print("📢 已到达公告页面，正在自动跳转查询页面...")
            页面.wait_for_timeout(人类延迟(500, 1000))

            当前URL  = 页面.url
            会话匹配 = re.search(r"sessionid=([^&\s]+)", 当前URL)
            if 会话匹配:
                会话ID    = 会话匹配.group(1)
                查询页URL = f"https://www.mydg.live/007C/chkreceipt1.jsp?sessionid={会话ID}"
                页面.goto(查询页URL, wait_until="domcontentloaded")
                长度 = len(会话ID)
                print(f"✅ 已到达查询页面（sessionid=***{会话ID[-3:]}, 长度={长度}）开始爬取...\n")
            else:
                print("⚠️  未取到 sessionid，等待自然跳转...")
                页面.wait_for_url("**/chkreceipt1.jsp**", timeout=30000)
                print("✅ 已到达查询页面，开始爬取...\n")

            页面.wait_for_timeout(人类延迟(1500, 3000))

            日期已填写   = False
            下次休息节点 = random.randint(15, 25)

            for 序号, 账号 in enumerate(全部账号, 1):
                页面.wait_for_timeout(人类延迟(700, 1600))
                随机滚动(页面)

                if 序号 == 下次休息节点:
                    停顿秒 = random.uniform(3.5, 8.0)
                    print(f"   ⏸  模拟休息 {停顿秒:.1f}s ...")
                    页面.wait_for_timeout(int(停顿秒 * 1000))
                    下次休息节点 += random.randint(15, 25)

                print(f"[{序号}/{len(全部账号)}] 🔎 {账号:20s} ", end="", flush=True)

                try:
                    账号输入框 = 页面.locator(
                        "input[name='id1'], input[name='searchId']"
                    ).first
                    账号输入框.wait_for(state="visible", timeout=5000)
                    模拟打字(页面, 账号输入框, 账号)
                    页面.wait_for_timeout(人类延迟(200, 500))

                    if not 日期已填写:
                        日期输入框列表 = 页面.locator(
                            "input[name*='drawdate'], input[name*='date']"
                        ).all()
                        if 日期输入框列表:
                            日期输入框列表[0].wait_for(state="visible", timeout=5000)
                            模拟打字(页面, 日期输入框列表[0], 查询日期)
                            页面.wait_for_timeout(人类延迟(200, 400))
                            日期已填写 = True

                    随机鼠标游走(页面)
                    页面.get_by_role("button", name="Search").first.click()
                    页面.wait_for_timeout(人类延迟(2000, 4500))

                    行数据 = 提取页面数据(页面, 账号)

                    if 行数据:
                        全部数据.extend(行数据)
                        有数据账号.add(账号)
                        追加写入Excel(行数据, 输出路径)
                        print(f"✅ {len(行数据)} 条")
                    else:
                        print("  (无数据)")

                except PlaywrightError as e:
                    print(f"\n❌ Playwright 不可恢复错误，提前终止: {type(e).__name__}: {e}")
                    break
                except Exception as e:
                    print(f"⚠️  {type(e).__name__}: {str(e)[:80]}")
                    continue

        except KeyboardInterrupt:
            print(f"\n⚠️  用户中止爬取（已完成 {序号}/{len(全部账号)}）")

        finally:
            print(f"\n{'='*70}")

            if 全部数据:
                保存有数据账号(有数据账号)
                try:
                    最终df = pd.read_excel(输出路径)
                    去重前 = len(最终df)
                    最终df = 最终df.drop_duplicates(subset=["QueryAcct", "DrawRange"], keep="first")
                    最终df["_排序键"] = 最终df["DrawRange"].apply(DrawRange排序键)
                    最终df = (
                        最终df.sort_values(["QueryAcct", "_排序键"])
                        .drop(columns=["_排序键"])
                        .reset_index(drop=True)
                    )
                    最终df.to_excel(输出路径, index=False)

                    print(f"🎉 爬取完成！")
                    print(f"   原始记录  : {去重前}")
                    print(f"   去重后    : {len(最终df)}")
                    print(f"   有数据账号: {len(有数据账号)} 个")
                    print(f"   查询日期  : {查询日期}")
                    print(f"   输出文件  : {输出路径.absolute()}")
                except Exception as e:
                    print(f"⚠️  最终整理失败: {e}，实时数据已保存，请手动检查 {输出路径}")
            else:
                print("⚠️  未提取到任何数据，未写入文件")

            print(f"{'='*70}\n")

            try:
                if 浏览器 is not None:
                    浏览器.close()
            except Exception:
                pass


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
