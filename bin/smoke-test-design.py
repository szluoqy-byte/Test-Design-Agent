#!/usr/bin/env python3
"""Run smoke checks against bundled example test case outputs."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> int:
    print("$ " + " ".join(cmd))
    completed = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if completed.stdout:
        print(completed.stdout.rstrip())
    if completed.stderr:
        print(completed.stderr.rstrip(), file=sys.stderr)
    return completed.returncode


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    examples_dir = root / "examples" / "outputs"
    files = sorted(examples_dir.glob("*.test-cases.md")) + sorted(
        examples_dir.glob("*.testcase-details.md")
    )

    if not files:
        print("未找到 examples/outputs 下的示例输出", file=sys.stderr)
        return 1

    scripts = [
        root / "bin" / "lint-testcase-report.py",
        root / "bin" / "semantic-testcase-check.py",
    ]
    source_by_report = {
        "sample-order.test-cases.md": root / "examples" / "testpoints" / "sample-order-testpoints.md",
    }

    failed = False
    for file_path in files:
        print(f"\n== {file_path.relative_to(root)} ==")
        for script in scripts:
            command = [sys.executable, str(script), str(file_path)]
            source = source_by_report.get(file_path.name)
            if script.name == "lint-testcase-report.py" and source:
                command.extend(["--source", str(source)])
            code = run(command, root)
            if code != 0:
                failed = True

    if failed:
        print("\nSMOKE FAIL")
        return 1

    print("\nSMOKE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
