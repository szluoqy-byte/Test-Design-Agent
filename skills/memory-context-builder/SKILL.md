---
name: memory-context-builder
description: 当测试用例设计需要注入项目背景信息时使用；从仓库根目录下的 memory/project-memory.md、memory/domains/*.md 和 memory/testing-experience-memory.md 中筛选与当前测试点相关的账号角色、业务域约定、状态规则、历史缺陷和团队偏好，生成本次运行的 context-pack.md；不直接修改长期 memory。
---

# 记忆上下文构建

本 skill 从仓库根目录下的 `memory/` 中选择与当前测试点相关的内容，生成本次运行使用的 `context-pack.md`。

## 路径解析规则

- 本 skill 中所有 `memory/...` 和 `outputs/...` 路径均为仓库根目录相对路径。
- 不要把 memory 文件解析到 `skills/memory-context-builder/` 子目录下。

## 职责边界

- 只读取和筛选长期 memory。
- 只写出本次运行的 `context-pack.md`。
- 不自动修改仓库根目录下的 `memory/` 源文件。
- 与当前输入冲突的 memory 交给 `clarification-gate`。

## 读取范围

- 仓库根目录下的 `memory/project-memory.md`
- 仓库根目录下的 `memory/domains/*.md`，如不存在匹配文件则跳过
- 仓库根目录下的 `memory/testing-experience-memory.md`

读取 `memory/domains/*.md` 时，应从本地工作区读取实际存在的文件；即使 domain 文件被 `.gitignore` 忽略，只要存在于本地工作区，也应参与本次匹配。不要只依赖 git 跟踪文件列表。

## Domain 匹配规则

在生成 `context-pack.md` 前，必须先枚举 `memory/domains/*.md` 的文件名和一级标题，再按以下信号选择相关 domain：

- 当前输入、需求名称、需求描述、测试场景、测试点、文件名或用户消息中直接出现 domain 文件名、产品名或一级标题。
- 当前输入出现 domain memory 中的稳定入口、菜单、模块、页面、系统名或角色名称。
- 当前输入没有明确产品名，但出现多个 domain memory 的稳定关键词时，选择匹配度最高的 domain，并在 context-pack 中说明匹配依据。
- 如果当前输入只给出较短入口、业务入口、目标页面或页签，而 domain memory 给出稳定父级菜单链路，应视为入口补全，不视为冲突；context-pack 中应输出“补全后的建议入口路径”，并说明由当前输入目标页面/页签和 domain memory 父级入口组合而来。
- 只有当前输入和 domain memory 在同一入口层级给出不同菜单、页面、页签名称，或当前输入明确声明另一条完整路径时，才视为冲突。冲突时当前输入优先，并在“可能冲突或需要用户确认的信息”中记录冲突，不直接用 domain memory 覆盖。
- 如果没有匹配到任何 domain，应在 context-pack 中明确写明“未匹配到业务域记忆”，不要静默省略。

## 输出

写入 `${PROJECT_ROOT}/outputs/runs/<run-id>/context-pack.md`，包含：

1. 本次测试点摘要。
2. 匹配到的项目事实。
3. 匹配到的业务域约定，并列出命中的 domain 文件名和匹配依据；如命中菜单、页面、入口清单，应尽量保留原始表格层级，不要压平成一段泛化描述。
4. 匹配到的历史缺陷和评审偏好。
5. 可能冲突或需要用户确认的信息。

业务域约定应按用途拆分，便于后续 skill 使用：

- 可用于前置步骤的事实：账号角色、权限前提、环境依赖、数据准备前提。
- 可用于测试步骤的事实：入口路径、菜单层级、页面、页签、按钮、触发方式。
- 可用于预期断言的事实：稳定可观察的页面区域、字段、状态、提示或结果载体。
- 仅作设计约束的事实：状态集合、枚举值、取值区间、规则边界、覆盖约束。
- 需确认或不可直接写入用例的信息：当前输入与 memory 冲突、缺少层级、缺少按钮文案、缺少数据准备方式。

## 规则

- 只注入与本次测试点相关的内容，不全量搬运 memory。
- 不把未确认推断写入长期 memory。
- 如果 memory 与当前输入冲突，当前输入优先，并把冲突交给 `clarification-gate`。
- 过滤“待用户确认后补充”“待补充”“暂无”等占位信息，不把占位内容当作事实写入 context-pack；未匹配到对应事实时，直接写明未匹配到。
- context-pack 中的运行编号、输出路径和文件名必须来自本次真实运行目录，不使用 `abc123`、`TODO`、`示例 run-id` 等占位值。
- 输出可以作为本次运行快照被后续 skill 读取。
