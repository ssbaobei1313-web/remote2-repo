@echo off
chcp 65001 >nul
title Create Project Structure

echo ============================================
echo   正在创建 Python 爬虫项目目录结构
echo   Author: Bei
echo ============================================
echo.

cd /d D:\PROJECT

echo [1/6] 创建 core 目录...
if not exist core mkdir core

echo [2/6] 创建 checkpoint 目录...
if not exist checkpoint mkdir checkpoint

echo [3/6] 创建 output 目录...
if not exist output mkdir output

echo [4/6] 创建 core 模块文件...
type nul > core\excel_writer.py
type nul > core\anti_detect.py
type nul > core\account_reader.py
type nul > core\page_parser.py
type nul > core\process_account.py
type nul > core\utils.py

echo [5/6] 创建 checkpoint 文件...
type nul > checkpoint\checkpoint_utils.py
type nul > checkpoint\processed.txt

echo [6/6] 创建 main.py...
type nul > main.py

echo.
echo ============================================
echo   目录结构创建完成！
echo ============================================
pause
