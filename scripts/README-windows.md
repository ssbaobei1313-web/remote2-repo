# Windows: enable python3 in venv

PowerShell (project root):

# 创建轻量转发器（推荐）
@'
@echo off
"%~dp0python.exe" %*
'@ | Set-Content -Path .\.venv\Scripts\python3.cmd -Encoding ascii

# 如需 exe 副本（仅当工具要求）
Copy-Item .\.venv\Scripts\python.exe .\.venv\Scripts\python3.exe -Force

# 删除（撤销）
Remove-Item .\.venv\Scripts\python3.cmd -ErrorAction SilentlyContinue
Remove-Item .\.venv\Scripts\python3.exe -ErrorAction SilentlyContinue
