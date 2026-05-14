---
name: design-testcases-from-testpoints
description: 主入口 skill。当用户提供测试用例设计输入包、测试点文件或测试点文本，并要求生成测试用例设计报告、可执行测试用例明细、追溯矩阵、覆盖审查或质量门禁结果时使用；负责从 $ARGUMENTS 串联 memory 上下文、测试点规范化、澄清治理、测试设计、用例编写、审查校验和 Markdown 产物输出。
---

# 测试用例设计主入口

本 skill 从 `$ARGUMENTS` 指定的测试用例设计输入包、测试点文件或用户粘贴的测试点文本生成测试用例设计报告和独立测试用例明细。推荐输入包模板见仓库根目录下的 `templates/testcase-design-input-template.md`。测试场景、场景测试条件、测试点和测试用例的粒度边界遵循仓库根目录下的 `knowledge/test-scenario-point-case-boundary.md`。所有 `knowledge/...`、`templates/...`、`quality-gates/...` 路径均从仓库根目录解析，不得解析到当前 skill 子目录下。

## 路径解析规则

- 本 skill 中所有 `knowledge/...`、`templates/...`、`quality-gates/...`、`bin/...`、`memory/...` 和 `outputs/...` 路径均为仓库根目录相对路径。
- 固定当前会话工作目录为 `PROJECT_ROOT`，不要从输入文件路径、当前 skill 目录或输出目录反推项目根目录。
- 不要把知识、模板、门禁、脚本或 memory 文件解析到 `skills/design-testcases-from-testpoints/` 子目录下。

## 职责边界

- 负责端到端编排和最终落盘。
- 调用 `testcase-design` 形成设计方案。
- 调用 `testcase-writing` 生成仅包含必需字段的测试用例明细。
- 调用 `testcase-review` 形成追溯、覆盖和质量结论。
- 不在本 skill 中维护具体测试设计模式细节。

## 必需输入

- `$ARGUMENTS`：测试用例设计输入包 Markdown 文件路径、测试点 Markdown 文件路径，或本次会话中明确提供的测试点文本。

## 项目根目录与输出路径

在生成任何运行产物前，必须先固定 `PROJECT_ROOT`：

1. `PROJECT_ROOT` 等于用户启动当前会话所在的工作目录。
2. 如果 `$ARGUMENTS` 是相对路径，只按 `PROJECT_ROOT` 解析为绝对路径。
3. 禁止把 skill 文件所在目录、插件缓存目录或 `.claude-plugin/` 当作 `PROJECT_ROOT`。
4. 所有运行产物写入 `${PROJECT_ROOT}/outputs/runs/<run-id>/`。

`run-id` 格式为 `<YYYYMMDD-HHMMSS>-<测试点文件名安全短名>-<短哈希>`。同一轮设计内的澄清、修正和质量门禁重跑必须复用同一个运行目录。

## 无人值守执行策略

- 默认连续执行到完整测试用例设计报告和独立测试用例明细落盘，不在阶段之间等待用户输入。
- 除非 `clarification-gate` 判定存在 `MustAsk` 级阻塞问题，不得中断流程询问用户是否继续。
- `ShouldAsk` 和 `RecordOnly` 问题默认写入待确认问题，并继续生成保守可执行用例。
- 缺少具体账号、菜单、按钮、配置、测试数据或提示文案时，如果不影响用例结构和基本判定，应使用中性可替换表达继续生成，并在待确认问题中记录缺口。
- 每个阶段完成后直接进入下一阶段；最终输出报告路径、明细路径、检查结果和未解决待确认问题。

## 执行流程

1. 校验输入是测试用例设计输入包、测试点文件或测试点文本。
2. 创建运行目录，写出 `context-pack.md`、`clarification-session.md` 的初始文件。
3. 使用 `memory-context-builder` 构建本次相关上下文；必须让其枚举并匹配 `memory/domains/*.md` 中的本地业务域记忆，context-pack 中应写明命中的 domain 文件名和匹配依据，未命中时也要明确说明。
4. 规范化输入：优先识别“需求 -> 测试场景 -> 场景测试条件 -> 测试点”和“接口测试清单 -> 接口测试详情 -> 接口测试点”结构，并按仓库根目录下的 `knowledge/test-scenario-point-case-boundary.md` 检查是否存在场景、接口、测试点和用例粒度混写；保留场景测试条件中的场景入口/触发方式、执行用户/角色、前置条件、测试数据因子、业务设计约束和补充说明，作为后续设计与用例写作输入；若输入只有测试点，则识别 `TP-*` 和 `ITP-*`、模块、测试点、类型、需求依据、风险备注，保留原始编号；若历史输入携带级别，仅作为参考信息，不要求测试点携带级别。测试设计方法和预期判定由后续设计阶段推导。
5. 在 `CP-INPUT` 使用 `clarification-gate` 评估是否需要询问用户。
6. 使用 `testcase-design` 为每条测试点选择设计模式、覆盖意图、用例数量和等级。
7. 使用 `testcase-writing` 生成测试用例明细。单条用例只包含用例编号、用例名称、用例等级、前置步骤、测试步骤和预期结果。
8. 对独立测试用例明细先运行仓库根目录下的 `bin/lint-testcase-report.py` 和 `bin/semantic-testcase-check.py`；如失败，将确定性错误交回 `testcase-writing` 定向修正，并在同一运行目录重跑脚本，直到通过或记录阻塞原因。
9. 使用 `testcase-review` 生成追溯矩阵、覆盖审查、质量门禁结果和专家评分。此时默认用例明细已经通过脚本预检，review 重点复核测试步骤和 GUI 自动化可执行性；覆盖、追溯、等级、去重和专家评分只做轻量一致性检查，不承担大段重写。
10. 对完整报告再次运行 `bin/lint-testcase-report.py` 和 `bin/semantic-testcase-check.py`；如失败，优先修正报告结构、追溯引用或脚本明确指出的单点问题，不重新展开全量评审。
11. 输出：
    - `${PROJECT_ROOT}/outputs/runs/<run-id>/<测试点文件名安全短名>.test-cases.md`
    - `${PROJECT_ROOT}/outputs/runs/<run-id>/<测试点文件名安全短名>.testcase-details.md`

## 输出要求

- 完整报告使用仓库根目录下的 `templates/testcase-report-template.md`。
- 独立明细使用仓库根目录下的 `templates/testcase-detail-template.md`。
- 报告必须包含测试点输入摘要、用例设计策略、测试用例明细、追溯矩阵、覆盖审查、质量门禁、专家评分、待确认问题和 memory 更新建议。
- 独立明细只包含测试用例主体，不包含追溯矩阵、覆盖审查、质量门禁或 memory 更新建议。
- 测试点关联关系只在追溯矩阵中表达。

## 硬性约束

- 不重新分析原始需求。
- 不生成自动化脚本。
- 不编造业务规则、账号、菜单路径、环境地址或测试数据。
- 不输出只有检查目标、没有可执行步骤的伪用例。
- 不把未确认的信息写入长期 memory。
- 质量门禁失败时必须形成精确问题清单，优先交回对应阶段定向修正；无法可靠修正时才在待确认问题中说明阻塞原因。
