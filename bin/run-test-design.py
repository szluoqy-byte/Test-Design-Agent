#!/usr/bin/env python3
"""Prepare a reproducible Test-Design-Agent run directory and optional checks."""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff._-]+", "-", value).strip("-._")
    return slug or "testpoints"


def short_hash(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(data).hexdigest()[:8]


def read_template(root: Path, name: str) -> str:
    return (root / "templates" / name).read_text(encoding="utf-8")


def write_if_missing(path: Path, text: str) -> None:
    if not path.exists():
        path.write_text(text, encoding="utf-8")


def run(cmd: list[str], cwd: Path) -> int:
    print("$ " + " ".join(cmd))
    completed = subprocess.run(cmd, cwd=cwd, text=True)
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a run directory, build context-pack.md, and optionally validate generated outputs."
    )
    parser.add_argument("input", help="测试点文件或测试用例设计输入包")
    parser.add_argument("--project-root", default=".", help="仓库根目录，默认当前目录")
    parser.add_argument("--run-id", help="自定义 run-id；默认按时间、输入文件名和短哈希生成")
    parser.add_argument("--validate", action="store_true", help="如果报告和明细已生成，则运行 lint 和 semantic 检查")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = root / input_path
    input_path = input_path.resolve()
    if not input_path.exists():
        print(f"输入文件不存在: {input_path}", file=sys.stderr)
        return 2

    source_stem = safe_slug(input_path.stem)
    run_id = args.run_id or f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{source_stem}-{short_hash(input_path)}"
    run_dir = root / "outputs" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    context_cmd = [
        sys.executable,
        str(root / "bin" / "build-memory-context.py"),
        str(input_path),
        "--project-root",
        str(root),
        "--run-dir",
        str(run_dir),
    ]
    if run(context_cmd, root) != 0:
        return 1

    clarification_template = read_template(root, "clarification-session-template.md")
    design_plan_template = read_template(root, "testcase-design-plan-template.md")
    report_template = read_template(root, "testcase-report-template.md").replace("<测试点来源名称>", source_stem)
    detail_template = read_template(root, "testcase-detail-template.md").replace("<测试点来源名称>", source_stem)

    report_path = run_dir / f"{source_stem}.test-cases.md"
    detail_path = run_dir / f"{source_stem}.testcase-details.md"
    write_if_missing(run_dir / "clarification-session.md", clarification_template)
    write_if_missing(run_dir / "testcase-design-plan.md", design_plan_template)
    write_if_missing(report_path, report_template)
    write_if_missing(detail_path, detail_template)

    print("\n运行目录已准备完成：")
    print(f"- run-dir: {run_dir}")
    print(f"- context-pack: {run_dir / 'context-pack.md'}")
    print(f"- design-plan: {run_dir / 'testcase-design-plan.md'}")
    print(f"- report: {report_path}")
    print(f"- details: {detail_path}")

    if args.validate:
        commands = [
            [sys.executable, str(root / "bin" / "lint-testcase-report.py"), str(detail_path)],
            [sys.executable, str(root / "bin" / "semantic-testcase-check.py"), str(detail_path)],
            [
                sys.executable,
                str(root / "bin" / "lint-testcase-report.py"),
                str(report_path),
                "--source",
                str(input_path),
            ],
            [sys.executable, str(root / "bin" / "semantic-testcase-check.py"), str(report_path)],
        ]
        failed = False
        for command in commands:
            if run(command, root) != 0:
                failed = True
        return 1 if failed else 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
