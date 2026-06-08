# ================================
# SQL-SAFE 一键开发脚本
# 作者：Bei 专属自动化脚本
# 功能：安装依赖 → 运行测试 → 打开覆盖率 → 自动提交 Git
# ================================

# 颜色输出函数
function Write-Info($msg)  { Write-Host "[INFO]  $msg" -ForegroundColor Cyan }
function Write-OK($msg)    { Write-Host "[OK]    $msg" -ForegroundColor Green }
function Write-Warn($msg)  { Write-Host "[WARN]  $msg" -ForegroundColor Yellow }
function Write-Err($msg)   { Write-Host "[ERR]   $msg" -ForegroundColor Red }

# 捕获错误
$ErrorActionPreference = "Stop"

Write-Info "切换到脚本所在目录..."
Set-Location -Path $PSScriptRoot

# -------------------------------
# 1. 激活虚拟环境
# -------------------------------
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    Write-Info "激活虚拟环境 .venv ..."
    . .\.venv\Scripts\Activate.ps1
    Write-OK "虚拟环境已激活"
} else {
    Write-Err "未找到 .venv，请先创建虚拟环境：python -m venv .venv"
    exit 1
}

# -------------------------------
# 2. 升级 pip
# -------------------------------
Write-Info "升级 pip ..."
python -m pip install --upgrade pip
Write-OK "pip 已升级"

# -------------------------------
# 3. 安装依赖
# -------------------------------
Write-Info "安装开发依赖 pytest / pytest-cov / sqlalchemy / pymysql ..."
pip install pytest pytest-cov sqlalchemy pymysql
Write-OK "依赖安装完成"

# -------------------------------
# 4. 运行测试 + 覆盖率
# -------------------------------
Write-Info "运行 pytest 并生成覆盖率报告 ..."
python -m pytest --cov=src --cov-report=term-missing --cov-report=html -q

if ($LASTEXITCODE -ne 0) {
    Write-Err "测试失败，请检查错误输出"
    exit 1
}

Write-OK "测试全部通过，覆盖率报告已生成"

# -------------------------------
# 5. 打开 HTML 覆盖率报告
# -------------------------------
$reportPath = ".\htmlcov\index.html"
if (Test-Path $reportPath) {
    Write-Info "打开覆盖率报告 ..."
    Start-Process $reportPath
    Write-OK "覆盖率报告已打开"
} else {
    Write-Warn "未找到 htmlcov/index.html"
}

# -------------------------------
# 6. 自动 Git 提交（可选）
# -------------------------------
param(
    [switch]$Commit
)

if ($Commit) {
    Write-Info "执行 Git 提交 ..."
    git add .
    git commit -m "chore: auto test & coverage update"
    Write-OK "Git 提交完成"
} else {
    Write-Warn "未启用自动 Git 提交（如需提交请加参数：-Commit）"
}

Write-OK "全部流程完成！"
