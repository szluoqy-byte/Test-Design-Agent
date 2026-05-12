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
