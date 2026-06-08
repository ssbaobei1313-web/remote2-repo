@echo off
chcp 65001 >nul
title Run Python Project

echo ============================================
echo   正在启动 Python 爬虫项目...
echo   Author: Bei
echo ============================================
echo.

cd /d D:\PROJECT

echo 激活虚拟环境...
call venv\Scripts\activate

echo 运行 main.py...
python main.py

echo.
echo ============================================
echo   程序运行结束
echo ============================================
pause
