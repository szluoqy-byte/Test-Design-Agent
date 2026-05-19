---
description: Generate test case design reports from testpoint input
agent: build
---

Use the repository skill `design-testcases-from-testpoints`.

Treat the command arguments below as the skill `$ARGUMENTS`:

```text
$ARGUMENTS
```

Keep `PROJECT_ROOT` fixed to the current repository root. Write outputs under `outputs/runs/<run-id>/`, run the deterministic checks from `bin/`, and report the final report path, detail path, check result, and unresolved confirmation questions.
