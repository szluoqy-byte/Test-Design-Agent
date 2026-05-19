# Test Design Agent Project Rules

This repository is a portable test case design agent package. Keep the core workflow in Markdown skills and lightweight Python validation scripts so it can run in Claude Code, OpenCode, and other agent runtimes.

## Runtime Entry Points

- Claude Code uses `.claude-plugin/plugin.json` and the root `skills/` directory.
- OpenCode uses `opencode.json`, `AGENTS.md`, `.opencode/commands/`, and `.opencode/skills/`.
- The main workflow is `skills/design-testcases-from-testpoints/SKILL.md`.
- Do not reintroduce plugin-level `agents/`; role-specific behavior belongs in skills, knowledge files, or quality gates.

## Skill Source Of Truth

- Treat `skills/` as the only manually edited skill source.
- Treat `.opencode/skills/` as a generated mirror for OpenCode discovery.
- After changing any `skills/*/SKILL.md`, run `python bin/sync-opencode-skills.py`.
- After changing runtime wiring, run `python bin/validate-agent-runtime.py`.

## Path Rules

- Resolve all `skills/...`, `knowledge/...`, `templates/...`, `quality-gates/...`, `memory/...`, `bin/...`, and `outputs/...` paths from the repository root.
- Do not resolve paths relative to a skill directory, `.claude-plugin/`, `.opencode/`, or an input file directory.
- Runtime outputs belong under `outputs/runs/<run-id>/`.

## Test Case Design Workflow

- For requests to generate test cases from testpoints, use `design-testcases-from-testpoints`.
- Use `memory-context-builder`, `clarification-gate`, `testcase-design`, `testcase-writing`, and `testcase-review` as the staged skill actions.
- Do not invent business facts, accounts, menus, environment URLs, or test data.
- Run deterministic checks from `bin/` before considering generated reports complete.

## Validation Commands

- Runtime wiring: `python bin/validate-agent-runtime.py`
- OpenCode skill mirror: `python bin/sync-opencode-skills.py --check`
- Example output smoke test: `python bin/smoke-test-design.py`
