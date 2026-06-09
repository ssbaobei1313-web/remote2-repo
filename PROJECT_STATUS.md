PROJECT_STATUS.md 模板
# 项目状态看板

## 基本信息
- ​**​项目​**​：Python 爬虫 + 测试重构
- ​**​当前任务​**​：合并 9 组测试建议 (group_01..09)
- ​**​最后更新​**​：2026-06-10
- ​**​虚拟环境​**​：已激活，`pip install -e .` 完成

## 测试状态
- ✅ `tests/test_persistence.py` - 通过
- ✅ `tests/test_async_runner_runner_impl.py` - 通过
- ⏳ `tests/test_runner_basic.py` - 待合并 group_01 后确认
- ⏳ 全量测试 `pytest` - 待完成

## 合并建议进度
- [x] group_01 - 已审查，等待合并
- [ ] group_02..09 - 待处理

## 关键文件
- `tests/_merged_suggestions/group_*.md` - 合并建议 (共 9 组)
- `tests/conftest.py` - 共享 fixtures
- `tests/test_runner_basic.py` - 待合并
- `src/async_runner/runner.py` - 核心逻辑
- `tools/merge_tests.py` - 合并工具

## 已知问题/卡点
- `runner.run_coroutine` 异常行为：当前设计为返回 `None` 并记录日志，需确认是否为最终方案
- `tests/test_runner_basic.py` 需确认 `runner` fixture 来源

## Git 分支信息
- 当前分支：`main` (或你的分支名)
- 上次提交：`refactor: 合并前快照`

## 对话交接记录
| 日期 | 对话主题 | 关键结论 |
|------|----------|----------|
| 2026-06-10 | 测试合并 group_01 | 已审查，fixture 需调整 |

---

## 本次对话目标
- [ ] 审查 group_01 合并建议
- [ ] 合并代码并运行测试
- [ ] 提交结果