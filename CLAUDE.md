# Claude Code 项目规则

本仓库同时是 Claude Code 插件和兼容 OpenCode 的 Agent 包。

请遵循 `AGENTS.md` 中的同一套项目规则。简要版本如下：

- Claude Code 加载 `.claude-plugin/plugin.json` 和仓库根目录下的 `skills/`。
- 主流程入口是 `skills/design-testcases-from-testpoints/SKILL.md`。
- `skills/` 是唯一手工维护的 skill 来源。
- `.opencode/skills/` 从 `skills/` 生成，不要直接编辑。
- 修改 skill 后，运行 `python bin/sync-opencode-skills.py`。
- 修改运行时入口或配置后，运行 `python bin/validate-agent-runtime.py`。
- 仓库内路径必须从项目根目录解析，不要从 `.claude-plugin/`、`.opencode/`、skill 目录或输入文件目录解析。
- 不要重新引入插件级 `agents/`；角色化行为应放在 skill、knowledge 文件或 quality gate 中。
