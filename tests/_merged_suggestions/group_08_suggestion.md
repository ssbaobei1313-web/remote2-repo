# 合并建议组 8

**涉及文件**: test_safe_query_extra.py

**相似测试函数**:
- `test_safe_query_extra.py` :: `test_safe_query_sql_not_string`
- `test_safe_query_extra.py` :: `test_bulk_query_sql_not_string`

**建议**:
- 选择最通用、覆盖面最广的断言作为保留版本。
- 统一 fixture 名称与作用域（session/function）。
- 将重复的 setup/teardown 提取到 `conftest.py`。
- 如果存在同步/异步差异，保留两个版本并在名字中标注 `_async` 或 `_sync`。

**自动合并草案（仅供参考，需人工审查）**

```python
﻿# -*- coding: utf-8 -*-
"""
补充对 src/core/safe_query.py 的单元测试，覆盖各种异常分支与正常分支。
目标函数：safe_ident, safe_order_by, safe_query, bulk_query
"""

import pytest
import importlib

# 明确以模块方式导入，避免 package-level 导出造成的歧义
sq = importlib.import_module("core.safe_query")


# -------------------------
# safe_ident
# -------------------------

def test_bulk_query_sql_not_string():
    with pytest.raises(ValueError):
        sq.bulk_query(None, [{"a": 1}])
```