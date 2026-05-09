---
name: memory-context-builder
description: 当测试用例设计需要注入项目背景信息时使用；从 memory/project-memory.md、memory/domains/*.md 和 memory/testing-experience-memory.md 中筛选与当前测试点相关的账号角色、业务域约定、状态规则、历史缺陷和团队偏好，生成本次运行的 context-pack.md；不直接修改长期 memory。
---

# 记忆上下文构建

本 skill 从 `memory/` 中选择与当前测试点相关的内容，生成本次运行使用的 `context-pack.md`。

## 职责边界

- 只读取和筛选长期 memory。
- 只写出本次运行的 `context-pack.md`。
- 不自动修改 `memory/` 源文件。
- 与当前输入冲突的 memory 交给 `clarification-gate`。

## 读取范围

- `memory/project-memory.md`
- `memory/domains/*.md`
- `memory/testing-experience-memory.md`

## 输出

写入 `${PROJECT_ROOT}/outputs/runs/<run-id>/context-pack.md`，包含：

1. 本次测试点摘要。
2. 匹配到的项目事实。
3. 匹配到的业务域约定。
4. 匹配到的历史缺陷和评审偏好。
5. 可能冲突或需要用户确认的信息。

## 规则

- 只注入与本次测试点相关的内容，不全量搬运 memory。
- 不把未确认推断写入长期 memory。
- 如果 memory 与当前输入冲突，当前输入优先，并把冲突交给 `clarification-gate`。
- 输出可以作为本次运行快照被后续 skill 读取。
