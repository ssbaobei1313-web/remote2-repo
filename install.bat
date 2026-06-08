@echo off
chcp 65001 >nul
title Python Environment Setup

echo ============================================
echo   正在安装所有依赖
echo   Author: Bei
echo ============================================
echo.

cd /d D:\PROJECT

echo [1/5] 创建虚拟环境 venv...
python -m venv venv

echo [2/5] 激活虚拟环境...
call venv\Scripts\activate

echo [3/5] 升级 pip...
python -m pip install --upgrade pip

echo [4/5] 安装 requirements.txt 依赖...
pip install -r requirements.txt

echo [5/5] 安装 Playwright 浏览器（如不需要可注释掉）...
playwright install

echo.
echo ============================================
echo   所有依赖安装完成！
echo   现在可以运行 main.py 了
echo ============================================
pause
