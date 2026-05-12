---
name: testcase-review
description: 当需要审查测试用例设计报告、独立测试用例明细或输出前草稿时使用；负责检查必填字段、可执行性、预期可观察可判定、追溯矩阵覆盖、等级一致性、重复用例、质量门禁和专家评分，并给出修正建议或待确认问题。
---

# 测试用例审查

本 skill 负责在输出前审查测试用例质量，并生成覆盖审查和质量门禁结果。

## 路径解析规则

- 本 skill 中所有 `knowledge/...`、`templates/...`、`quality-gates/...` 路径均为仓库根目录相对路径。
- 不要把知识、模板或门禁文件解析到 `skills/testcase-review/` 子目录下。

## 职责边界

- 负责“是否达标”的审查，不重新生成完整设计方案。
- 可提出修正建议；明显结构错误应要求修正后重跑门禁。
- 信息缺失导致无法修正时，输出待确认问题。
- 不要求单条用例明细写入测试点 ID，追溯只看追溯矩阵。

## 输入

- 测试用例设计报告草稿。
- 独立测试用例明细草稿。
- 规范化测试点清单。
- `context-pack.md`。

## 审查步骤

1. 按仓库根目录下的 `quality-gates/testcase-schema-check.md` 检查用例字段。
2. 按仓库根目录下的 `quality-gates/testcase-executability-check.md` 检查步骤是否可执行。
3. 按仓库根目录下的 `quality-gates/expected-result-check.md` 检查预期是否可观察、可判定。
4. 按仓库根目录下的 `knowledge/coverage-traceability-standard.md` 检查追溯矩阵。
5. 按仓库根目录下的 `quality-gates/coverage-check.md` 检查高风险测试点扩展是否足够。
6. 按仓库根目录下的 `quality-gates/level-consistency-check.md` 检查等级一致性。
7. 按仓库根目录下的 `quality-gates/duplicate-testcase-check.md` 检查重复用例。
8. 按仓库根目录下的 `quality-gates/expert-review-rubric.md` 给出专家评分。

## 输出

- 覆盖审查结果。
- 质量门禁结果。
- 专家评审评分。
- 阻断项和建议修正。

## 规则

- 输出质量问题优先修正，不直接把明显错误留给用户确认。
- 信息不足导致无法可靠修正时，生成待确认问题。
- 追溯关系只在追溯矩阵中维护，不要求单条用例明细写测试点 ID。
