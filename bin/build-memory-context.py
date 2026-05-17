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
RE_FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
RE_ENTRY_PATH = re.compile(r"[\u4e00-\u9fffA-Za-z0-9_【】/（）() -]+(?:\s*>\s*[\u4e00-\u9fffA-Za-z0-9_【】/（）() -]+)+")


@dataclass
class DomainMatch:
    path: Path
    title: str
    score: int
    reasons: list[str]
    content: str
    entry_paths: list[str]


@dataclass
class DomainInfo:
    path: Path
    title: str
    content: str
    metadata: dict[str, list[str]]


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def parse_front_matter(text: str) -> tuple[dict[str, list[str]], str]:
    match = RE_FRONT_MATTER.match(text)
    if not match:
        return {}, text

    metadata: dict[str, list[str]] = {}
    current_key = ""
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("- ") and current_key:
            metadata.setdefault(current_key, []).append(line[2:].strip().strip("\"'"))
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        current_key = key.strip()
        value = value.strip()
        if not value:
            metadata.setdefault(current_key, [])
            continue
        values = [item.strip().strip("\"'") for item in value.split(",")]
        metadata[current_key] = [item for item in values if item]

    return metadata, text[match.end() :]


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


def extract_entry_paths(text: str, metadata: dict[str, list[str]]) -> list[str]:
    paths: list[str] = []
    paths.extend(metadata.get("entry_paths", []))
    paths.extend(metadata.get("entry-paths", []))
    paths.extend(metadata.get("入口路径", []))
    for match in RE_ENTRY_PATH.findall(text):
        normalized = normalize_entry_path(match)
        if normalized:
            paths.append(normalized)
    return dedupe(paths)


def normalize_entry_path(path: str) -> str:
    parts = [part.strip(" `|【】") for part in path.split(">")]
    parts = [part for part in parts if part and part not in {"示例", "例如"}]
    if len(parts) < 2:
        return ""
    return " > ".join(parts)


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def load_domain(path: Path) -> DomainInfo:
    raw_content = read_text(path)
    metadata, body = parse_front_matter(raw_content)
    title = metadata.get("title", [first_title(body, path.stem)])[0]
    return DomainInfo(path, title, body, metadata)


def extract_keywords(info: DomainInfo) -> set[str]:
    keywords: set[str] = set()
    metadata_keywords: list[str] = []
    for key in ["keywords", "aliases", "products", "systems", "关键词", "别名"]:
        metadata_keywords.extend(info.metadata.get(key, []))
    for value in [info.path.stem, info.title, *metadata_keywords]:
        value = value.strip()
        if value and value not in {"README", ".gitkeep"}:
            keywords.add(value)
    for line in info.content.splitlines():
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


def path_target(path: str) -> str:
    parts = [part.strip() for part in path.split(">") if part.strip()]
    return parts[-1] if parts else ""


def collect_input_entry_paths(input_text: str) -> list[str]:
    return dedupe([normalize_entry_path(match) for match in RE_ENTRY_PATH.findall(input_text)])


def collect_entry_conflicts(input_paths: list[str], matches: list[DomainMatch], root: Path) -> list[str]:
    conflicts: list[str] = []
    if not input_paths or not matches:
        return conflicts

    domain_paths: list[tuple[str, Path]] = []
    for match in matches:
        for entry_path in match.entry_paths:
            domain_paths.append((entry_path, match.path))

    for input_path in input_paths:
        input_target = path_target(input_path)
        if not input_target:
            continue
        for domain_path, domain_file in domain_paths:
            if path_target(domain_path) == input_target and domain_path != input_path:
                conflicts.append(
                    f"| `{input_path}` | `{domain_path}` | `{relative(domain_file, root)}` | 同一目标入口路径不一致 |"
                )
    return dedupe(conflicts)


def match_domain(domain_path: Path, input_text: str) -> DomainMatch | None:
    info = load_domain(domain_path)
    keywords = extract_keywords(info)
    entry_paths = extract_entry_paths(info.content, info.metadata)
    reasons: list[str] = []

    for keyword in sorted(keywords, key=len, reverse=True):
        if keyword and keyword in input_text:
            reasons.append(f"输入命中 `{keyword}`")
        if len(reasons) >= 5:
            break
    for entry_path in entry_paths:
        target = path_target(entry_path)
        if entry_path in input_text:
            reasons.append(f"输入命中完整入口 `{entry_path}`")
        elif target and target in input_text:
            reasons.append(f"输入命中入口目标 `{target}`")
        if len(reasons) >= 5:
            break

    if not reasons:
        return None
    return DomainMatch(
        domain_path,
        info.title,
        len(reasons),
        reasons,
        remove_placeholder_lines(info.content),
        entry_paths,
    )


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
    input_entry_paths = collect_input_entry_paths(input_text)
    entry_conflicts = collect_entry_conflicts(input_entry_paths, matches, root)

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
            entry_path_lines = [f"- `{entry_path}`" for entry_path in match.entry_paths]
            lines.extend(
                [
                    f"### {match.title}",
                    "",
                    f"- domain 文件：`{relative(match.path, root)}`",
                    f"- 匹配依据：{'; '.join(match.reasons)}",
                    "",
                    "#### 可用于入口补全的路径",
                    "",
                    *(entry_path_lines if entry_path_lines else ["未声明可机械识别的入口路径。"]),
                    "",
                    "#### 已确认内容",
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
        ]
    )
    if entry_conflicts:
        lines.extend(
            [
                "| 当前输入入口路径 | memory 入口路径 | domain 文件 | 冲突说明 |",
                "|---|---|---|---|",
                *entry_conflicts,
                "",
                "上述冲突仅表示入口路径文本不一致，具体以当前输入优先，并交给 `clarification-gate` 判断是否需要确认。",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "未发现可机械识别的 memory 入口路径冲突；具体业务冲突仍需由 `clarification-gate` 结合输入语义判断。",
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
