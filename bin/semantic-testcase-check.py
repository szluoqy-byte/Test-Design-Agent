#!/usr/bin/env python3
"""Heuristic semantic checks for Markdown test cases."""

from __future__ import annotations

import re
import sys
from pathlib import Path


RE_CASE_HEADING = re.compile(r"^###\s+(TC-\d{3})\b")
VAGUE_PHRASES = [
    "功能正常",
    "流程正常",
    "结果正确",
    "符合预期",
    "正常显示",
    "正常处理",
    "检查结果",
    "进行测试",
]
OBSERVABLE_TERMS = [
    "展示",
    "显示",
    "提示",
    "状态",
    "生成",
    "保存",
    "返回",
    "响应",
    "错误码",
    "记录",
    "日志",
    "通知",
    "拦截",
    "不可",
    "成功",
    "失败",
]


def find_case_blocks(lines: list[str]) -> list[tuple[str, int, list[str]]]:
    starts: list[tuple[str, int]] = []
    for index, line in enumerate(lines):
        match = RE_CASE_HEADING.match(line)
        if match:
            starts.append((match.group(1), index))
    blocks: list[tuple[str, int, list[str]]] = []
    for offset, (case_id, start) in enumerate(starts):
        end = starts[offset + 1][1] if offset + 1 < len(starts) else len(lines)
        blocks.append((case_id, start + 1, lines[start:end]))
    return blocks


def collect_numbered_after(block: list[str], marker: str) -> list[str]:
    try:
        start = block.index(marker)
    except ValueError:
        return []
    items: list[str] = []
    for line in block[start + 1 :]:
        if line.startswith("- ") and line != marker:
            break
        match = re.match(r"\s+\d+\.\s+(.+)", line)
        if match:
            items.append(match.group(1).strip())
    return items


def main() -> int:
    if len(sys.argv) != 2:
        print("用法: semantic-testcase-check.py <报告.md>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"文件不存在: {path}", file=sys.stderr)
        return 2

    lines = path.read_text(encoding="utf-8").splitlines()
    errors: list[str] = []
    warnings: list[str] = []

    for case_id, line_number, block in find_case_blocks(lines):
        text = "\n".join(block)
        for phrase in VAGUE_PHRASES:
            if phrase in text:
                errors.append(f"第 {line_number} 行 {case_id}：存在空泛描述 `{phrase}`")

        preconditions = collect_numbered_after(block, "- 前置步骤：")
        steps = collect_numbered_after(block, "- 测试步骤：")
        expected = collect_numbered_after(block, "- 预期结果：")

        if steps and len(expected) != len(steps):
            errors.append(
                f"第 {line_number} 行 {case_id}：测试步骤数量为 {len(steps)}，预期结果数量为 {len(expected)}，必须一一对应"
            )

        for item in steps:
            if "进入" in item and ("菜单" in item or "入口" in item) and ">" not in item and "【" not in item:
                warnings.append(f"第 {line_number} 行 {case_id}：入口步骤 `{item}` 建议写成可点击菜单路径")

        if not any(any(term in item for term in OBSERVABLE_TERMS) for item in expected):
            warnings.append(f"第 {line_number} 行 {case_id}：预期结果缺少明显可观察对象")

        if not preconditions:
            errors.append(f"第 {line_number} 行 {case_id}：缺少可执行前置步骤")

        if any(item.endswith("。") is False and item.endswith(".") is False for item in steps + expected):
            warnings.append(f"第 {line_number} 行 {case_id}：部分步骤或预期缺少句末标点")

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        for warning in warnings:
            print(f"WARNING: {warning}")
        return 1

    print("PASS")
    for warning in warnings:
        print(f"WARNING: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
