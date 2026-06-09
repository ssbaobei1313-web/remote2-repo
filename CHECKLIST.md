CHECKLIST.md 模板
# 合并检查清单

## 合并前检查
- [ ] 当前分支已提交所有更改
- [ ] 已创建 Git 快照：`git commit -m "refactor: 合并前快照"`
- [ ] 已阅读并理解合并建议内容
- [ ] 确认 `runner.run_coroutine` 异常行为设计（返回 `None` 或抛出）

## 合并后检查
- [ ] 运行单文件测试：`pytest tests/test_runner_basic.py -q`
- [ ] 运行全量测试：`pytest --maxfail=1 -q`
- [ ] 检查覆盖率：`pytest --cov=src --cov-report=term-missing`
- [ ] 确认无循环导入：`pydeps src/async_runner --show-deps`
- [ ] 确认无 fixture 作用域冲突（session vs function）

## 提交前检查
- [ ] 所有测试通过
- [ ] 无代码异味（`flake8 src/`）
- [ ] 更新 `PROJECT_STATUS.md`
- [ ] 提交信息规范：`git commit -m "test: 合并 group_XX 建议"`