# 测试设计 Agent 项目规则

本仓库是一个可移植的测试用例设计 Agent 包。核心流程应沉淀在 Markdown skill 和轻量 Python 校验脚本中，确保同一套能力可以运行在 Claude Code、OpenCode 和其他 Agent 运行环境里。

## 运行入口

- Claude Code 使用 `.claude-plugin/plugin.json` 和仓库根目录下的 `skills/`。
- OpenCode 使用 `opencode.json`、`AGENTS.md`、`.opencode/commands/` 和 `.opencode/skills/`。
- 主流程入口是 `skills/design-testcases-from-testpoints/SKILL.md`。
- 不要重新引入插件级 `agents/`；角色化行为应放在 skill、knowledge 文件或 quality gate 中。

## Skill 唯一事实源

- `skills/` 是唯一手工维护的 skill 来源。
- `.opencode/skills/` 是供 OpenCode 发现 skill 的生成镜像。
- 修改任何 `skills/*/SKILL.md` 后，运行 `python bin/sync-opencode-skills.py`。
- 修改运行时入口或配置后，运行 `python bin/validate-agent-runtime.py`。

## 路径规则

- 所有 `skills/...`、`knowledge/...`、`templates/...`、`quality-gates/...`、`memory/...`、`bin/...` 和 `outputs/...` 路径都从仓库根目录解析。
- 不要从 skill 目录、`.claude-plugin/`、`.opencode/` 或输入文件所在目录解析这些路径。
- 运行产物统一写入 `outputs/runs/<run-id>/`。

## 测试用例设计流程

- 当用户要求基于测试点生成测试用例时，使用 `design-testcases-from-testpoints`。
- 阶段性 skill 动作包括 `memory-context-builder`、`clarification-gate`、`testcase-design`、`testcase-writing` 和 `testcase-review`。
- 不要编造业务事实、账号、菜单、环境地址或测试数据。
- 生成报告完成前，必须运行 `bin/` 下的确定性检查脚本。

## 校验命令

- 运行时入口校验：`python bin/validate-agent-runtime.py`
- OpenCode skill 镜像校验：`python bin/sync-opencode-skills.py --check`
- 示例输出冒烟测试：`python bin/smoke-test-design.py`
