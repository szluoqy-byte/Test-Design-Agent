#!/usr/bin/env python3
"""Build a lightweight context-pack.md from local project memory."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


PLACEHOLDER_TERMS = ("待用户确认后补充", "待补充", "暂无")
RE_HEADING = re.compile(r"^#\s+(.+)$")
RE_BRACKET_OBJECT = re.compile(r"【([^】]+)】")


@dataclass
class DomainMatch:
    path: Path
    title: str
    score: int
    reasons: list[str]
    content: str


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def first_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        match = RE_HEADING.match(line.strip())
        if match:
            return match.group(1).strip()
    return fallback


def remove_placeholder_lines(text: str) -> str:
    kept: list[str] = []
    for line in text.splitlines():
        if any(term in line for term in PLACEHOLDER_TERMS):
            continue
        kept.append(line)
    return "\n".join(kept).strip()


def extract_keywords(text: str, title: str, path: Path) -> set[str]:
    keywords: set[str] = set()
    for value in [path.stem, title]:
        value = value.strip()
        if value and value not in {"README", ".gitkeep"}:
            keywords.add(value)
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            if heading:
                keywords.add(heading)
        for obj in RE_BRACKET_OBJECT.findall(stripped):
            if obj:
                keywords.add(obj)
        if "|" in stripped:
            for cell in [cell.strip(" `") for cell in stripped.strip("|").split("|")]:
                if 2 <= len(cell) <= 30 and cell not in {"---", "字段", "内容", "说明"}:
                    keywords.add(cell)
    return {keyword for keyword in keywords if len(keyword) >= 2}


def match_domain(domain_path: Path, input_text: str) -> DomainMatch | None:
    content = read_text(domain_path)
    title = first_title(content, domain_path.stem)
    keywords = extract_keywords(content, title, domain_path)
    reasons: list[str] = []

    for keyword in sorted(keywords, key=len, reverse=True):
        if keyword and keyword in input_text:
            reasons.append(f"输入命中 `{keyword}`")
        if len(reasons) >= 5:
            break

    if not reasons:
        return None
    return DomainMatch(domain_path, title, len(reasons), reasons, remove_placeholder_lines(content))


def relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def build_context(root: Path, input_path: Path, run_dir: Path) -> str:
    input_text = read_text(input_path)
    project_memory = remove_placeholder_lines(read_text(root / "memory" / "project-memory.md"))
    experience_memory = remove_placeholder_lines(read_text(root / "memory" / "testing-experience-memory.md"))
    domain_paths = sorted((root / "memory" / "domains").glob("*.md"))
    matches = sorted(
        (match for path in domain_paths if (match := match_domain(path, input_text))),
        key=lambda item: (-item.score, item.path.name),
    )

    lines: list[str] = [
        "# 测试设计记忆上下文包",
        "",
        "## 1. 本次输入摘要",
        "",
        f"- 输入文件：`{relative(input_path, root)}`",
        f"- 运行目录：`{relative(run_dir, root)}`",
        "",
        "## 2. 匹配到的项目事实",
        "",
    ]
    lines.append(project_memory if project_memory else "未匹配到已确认的项目级事实。")

    lines.extend(["", "## 3. 匹配到的业务域约定", ""])
    if matches:
        for match in matches:
            lines.extend(
                [
                    f"### {match.title}",
                    "",
                    f"- domain 文件：`{relative(match.path, root)}`",
                    f"- 匹配依据：{'; '.join(match.reasons)}",
                    "",
                    match.content or "该 domain 文件没有可直接注入的已确认内容。",
                    "",
                ]
            )
    else:
        lines.append("未匹配到业务域记忆。")

    lines.extend(["", "## 4. 匹配到的历史缺陷和评审偏好", ""])
    lines.append(experience_memory if experience_memory else "未匹配到已确认的历史缺陷或评审偏好。")

    lines.extend(
        [
            "",
            "## 5. 可能冲突或需要用户确认的信息",
            "",
            "未发现可机械识别的 memory 冲突；具体业务冲突仍需由 `clarification-gate` 结合输入语义判断。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build context-pack.md from local memory files.")
    parser.add_argument("input", help="测试点文件或测试用例设计输入包")
    parser.add_argument("--project-root", default=".", help="仓库根目录，默认当前目录")
    parser.add_argument("--run-dir", required=True, help="本次运行目录")
    parser.add_argument("--output", help="输出文件，默认 <run-dir>/context-pack.md")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = root / input_path
    input_path = input_path.resolve()
    run_dir = Path(args.run_dir)
    if not run_dir.is_absolute():
        run_dir = root / run_dir
    run_dir = run_dir.resolve()
    output_path = Path(args.output) if args.output else run_dir / "context-pack.md"
    if not output_path.is_absolute():
        output_path = root / output_path

    if not input_path.exists():
        print(f"输入文件不存在: {input_path}")
        return 2

    run_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_context(root, input_path, run_dir), encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
