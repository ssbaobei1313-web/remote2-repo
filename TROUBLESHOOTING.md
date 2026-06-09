TROUBLESHOOTING.md 模板
# 常见问题排查

## 导入错误
- ​**​`ModuleNotFoundError: No module named 'src'`​**​
    - 临时：`$env:PYTHONPATH = "$PWD"`
    - 永久：`pip install -e .`

## 测试失败
- ​**​`pytest` 找不到测试​**​：检查 `pytest.ini` 或 `pyproject.toml` 配置
- ​**​异步测试失败​**​：确认使用了 `@pytest.mark.asyncio` 和 `pytest-asyncio` 插件
- ​**​fixture 作用域冲突​**​：`session` 级别 fixture 不能依赖 `function` 级别的

## 文件编码问题
- ​**​BOM/NUL 字节错误​**​：用 PowerShell 重写为 UTF-8 无 BOM
    - `$bytes = [System.IO.File]::ReadAllBytes("path")`
    - `($bytes[0..7] | ForEach-Object { $_.ToString("X2") }) -join ' '`
- ​**​换行符问题​**​：统一为 LF（Unix 风格）

## 循环依赖
- ​**​检测​**​：`pydeps src/async_runner --show-deps`
- ​**​解决​**​：提取接口/抽象类，使依赖单向流动