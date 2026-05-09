---
name: design-testcases-from-testpoints
description: 主入口 skill。当用户提供测试点文件或测试点文本，并要求生成测试用例设计报告、可执行测试用例明细、追溯矩阵、覆盖审查或质量门禁结果时使用；负责从 $ARGUMENTS 串联 memory 上下文、测试点规范化、澄清治理、测试设计、用例编写、审查校验和 Markdown 产物输出。
---

# 测试用例设计主入口

本 skill 从 `$ARGUMENTS` 指定的测试点文件或用户粘贴的测试点文本生成测试用例设计报告和独立测试用例明细。

## 职责边界

- 负责端到端编排和最终落盘。
- 调用 `testcase-design` 形成设计方案。
- 调用 `testcase-writing` 生成仅包含必需字段的测试用例明细。
- 调用 `testcase-review` 形成追溯、覆盖和质量结论。
- 不在本 skill 中维护具体测试设计模式细节。

## 必需输入

- `$ARGUMENTS`：测试点 Markdown 文件路径，或本次会话中明确提供的测试点文本。

## 项目根目录与输出路径

在生成任何运行产物前，必须先固定 `PROJECT_ROOT`：

1. `PROJECT_ROOT` 等于用户启动当前会话所在的工作目录。
2. 如果 `$ARGUMENTS` 是相对路径，只按 `PROJECT_ROOT` 解析为绝对路径。
3. 禁止把 skill 文件所在目录、插件缓存目录或 `.claude-plugin/` 当作 `PROJECT_ROOT`。
4. 所有运行产物写入 `${PROJECT_ROOT}/outputs/runs/<run-id>/`。

`run-id` 格式为 `<YYYYMMDD-HHMMSS>-<测试点文件名安全短名>-<短哈希>`。同一轮设计内的澄清、修正和质量门禁重跑必须复用同一个运行目录。

## 执行流程

1. 校验输入是测试点文件或测试点文本。
2. 创建运行目录，写出 `context-pack.md`、`clarification-session.md` 的初始文件。
3. 使用 `memory-context-builder` 构建本次相关上下文。
4. 规范化测试点：识别 `TP-*`、模块、测试点、类型、方法、需求依据、级别、风险备注，保留原始编号。
5. 在 `CP-INPUT` 使用 `clarification-gate` 评估是否需要询问用户。
6. 使用 `testcase-design` 为每条测试点选择设计模式、覆盖意图、用例数量和等级。
7. 使用 `testcase-writing` 生成测试用例明细。单条用例只包含用例编号、用例名称、用例等级、前置步骤、测试步骤和预期结果。
8. 使用 `testcase-review` 生成追溯矩阵、覆盖审查、质量门禁结果和专家评分。
9. 运行 `bin/lint-testcase-report.py` 和 `bin/semantic-testcase-check.py`。
10. 输出：
    - `${PROJECT_ROOT}/outputs/runs/<run-id>/<测试点文件名安全短名>.test-cases.md`
    - `${PROJECT_ROOT}/outputs/runs/<run-id>/<测试点文件名安全短名>.testcase-details.md`

## 输出要求

- 完整报告使用 `templates/testcase-report-template.md`。
- 独立明细使用 `templates/testcase-detail-template.md`。
- 报告必须包含测试点输入摘要、用例设计策略、测试用例明细、追溯矩阵、覆盖审查、质量门禁、专家评分、待确认问题和 memory 更新建议。
- 独立明细只包含测试用例主体，不包含追溯矩阵、覆盖审查、质量门禁或 memory 更新建议。
- 测试点关联关系只在追溯矩阵中表达。

## 硬性约束

- 不重新分析原始需求。
- 不生成自动化脚本。
- 不编造业务规则、账号、菜单路径、环境地址或测试数据。
- 不输出只有检查目标、没有可执行步骤的伪用例。
- 不把未确认的信息写入长期 memory。
- 质量门禁失败时必须修正或在待确认问题中说明阻塞原因。
