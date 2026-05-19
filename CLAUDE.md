# Claude Code Project Rules

This repository is a Claude Code plugin and an OpenCode-compatible agent package.

Follow the same project rules as `AGENTS.md`. The short version:

- Claude Code loads `.claude-plugin/plugin.json` and the root `skills/` directory.
- The main workflow is `skills/design-testcases-from-testpoints/SKILL.md`.
- Keep `skills/` as the only manually edited skill source.
- `.opencode/skills/` is generated from `skills/`; do not edit it directly.
- After changing skills, run `python bin/sync-opencode-skills.py`.
- After changing runtime wiring, run `python bin/validate-agent-runtime.py`.
- Resolve repository paths from the project root, not from `.claude-plugin/`, `.opencode/`, a skill directory, or an input file directory.
- Do not reintroduce plugin-level `agents/`; role-specific behavior belongs in skills, knowledge files, or quality gates.
