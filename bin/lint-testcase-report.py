#!/usr/bin/env python3
"""Lint a Markdown test case report or standalone test case detail file."""

from __future__ import annotations

import re
import sys
import argparse
from pathlib import Path


FULL_REQUIRED_SECTIONS = [
    "# ",
    "## 1. 设计范围",
    "## 2. 记忆上下文包摘要",
    "## 3. 测试点输入摘要",
    "## 4. 待确认处理摘要",
    "## 5. 用例设计策略",
    "## 6. 测试用例明细",
    "## 7. 测试点到用例追溯矩阵",
    "## 8. 覆盖审查结果",
    "## 9. 质量门禁结果",
    "## 10. 待确认问题",
    "## 11. 专家评审评分",
    "## 12. 建议沉淀的记忆更新",
]

DETAIL_REQUIRED_SECTIONS = [
    "# ",
]

TRACE_HEADER = "| 测试点 ID | 测试点摘要 | 覆盖用例 | 覆盖状态 | 备注 |"
QUALITY_GATE_HEADER = "| 门禁 | 结果 | 说明 |"
ALLOWED_LEVELS = {"Level 0", "Level 1", "Level 2", "Level 3", "Level 4"}
ALLOWED_COVERAGE = {"已覆盖", "部分覆盖", "待确认", "未覆盖"}
ALLOWED_GATE_RESULTS = {"通过", "未通过", "待确认", "不适用"}
REQUIRED_QUALITY_GATES = [
    "结构字段",
    "可执行性",
    "预期可判定",
    "追溯覆盖",
    "覆盖完整性",
    "等级一致性",
    "重复用例",
]
RE_CASE_HEADING = re.compile(r"^###\s+(TC-\d{3})\b")
RE_TEST_POINT_ID = re.compile(r"(?:TP|ITP)-\d{3}")
RE_TC_ID = re.compile(r"TC-\d{3}")
RE_TEMPLATE_PLACEHOLDER = re.compile(r"<[^>\n]{1,120}>")
BANNED_CASE_FIELDS = {
    "关联测试点",
    "模块",
    "用例类型",
    "测试数据",
    "适用环境",
    "自动化建议",
    "风险/备注",
    "风险备注",
}


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def find_case_blocks(lines: list[str]) -> list[tuple[str, int, int, list[str]]]:
    starts: list[tuple[str, int]] = []
    for index, line in enumerate(lines):
        match = RE_CASE_HEADING.match(line)
        if match:
            starts.append((match.group(1), index))

    blocks: list[tuple[str, int, int, list[str]]] = []
    for offset, (case_id, start) in enumerate(starts):
        end = starts[offset + 1][1] if offset + 1 < len(starts) else len(lines)
        blocks.append((case_id, start + 1, end, lines[start:end]))
    return blocks


def collect_trace_rows(lines: list[str]) -> list[tuple[int, list[str]]]:
    rows: list[tuple[int, list[str]]] = []
    try:
        header_index = lines.index(TRACE_HEADER)
    except ValueError:
        return rows

    for index in range(header_index + 2, len(lines)):
        line = lines[index]
        if not line.startswith("|"):
            break
        cells = split_row(line)
        if cells and RE_TEST_POINT_ID.fullmatch(cells[0]):
            rows.append((index + 1, cells))
    return rows


def collect_table_rows(lines: list[str], header: str) -> list[tuple[int, list[str]]]:
    rows: list[tuple[int, list[str]]] = []
    try:
        header_index = lines.index(header)
    except ValueError:
        return rows

    for index in range(header_index + 2, len(lines)):
        line = lines[index]
        if not line.startswith("|"):
            break
        cells = split_row(line)
        if cells:
            rows.append((index + 1, cells))
    return rows


def is_placeholder(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return True
    if stripped in {"-", "—", "无", "不适用"}:
        return True
    return stripped.startswith("<") and stripped.endswith(">")


def collect_template_placeholders(text: str, lines: list[str]) -> list[str]:
    errors: list[str] = []
    for line_number, line in enumerate(lines, start=1):
        for match in RE_TEMPLATE_PLACEHOLDER.finditer(line):
            errors.append(f"第 {line_number} 行：存在未替换模板占位符 {match.group(0)}")
    if "{{" in text or "}}" in text:
        errors.append("存在未替换模板占位符 {{...}}")
    return errors


def collect_source_test_points(path: Path) -> tuple[set[str], list[str]]:
    errors: list[str] = []
    if not path.exists():
        return set(), [f"源测试点文件不存在: {path}"]

    source_ids: set[str] = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.startswith("|"):
            continue
        cells = split_row(line)
        if not cells or not RE_TEST_POINT_ID.fullmatch(cells[0]):
            continue

        summary = cells[1] if len(cells) > 1 else ""
        if is_placeholder(summary):
            continue
        if cells[0] in source_ids:
            errors.append(f"源测试点第 {line_number} 行：重复测试点 ID {cells[0]}")
        source_ids.add(cells[0])

    if not source_ids:
        errors.append(f"源测试点文件未解析到有效 TP-* 或 ITP-* 行: {path}")
    return source_ids, errors


def validate_case_block(case_id: str, line_number: int, block: list[str]) -> list[str]:
    errors: list[str] = []
    text = "\n".join(block)

    required_fields = [
        f"- 用例编号：{case_id}",
        "- 用例名称：",
        "- 用例等级：",
        "- 前置步骤：",
        "- 测试步骤：",
        "- 预期结果：",
    ]
    for field in required_fields:
        if field not in text:
            errors.append(f"第 {line_number} 行 {case_id}：缺少字段 {field}")

    for field in BANNED_CASE_FIELDS:
        if f"- {field}：" in text or f"- {field}:" in text:
            errors.append(f"第 {line_number} 行 {case_id}：单条用例明细不应包含字段 {field}")

    level_line = next((line for line in block if line.startswith("- 用例等级：")), "")
    level = level_line.split("：", 1)[1].strip() if "：" in level_line else ""
    if level and level not in ALLOWED_LEVELS:
        errors.append(f"第 {line_number} 行 {case_id}：非法用例等级 {level}")

    for section in ["前置步骤", "测试步骤", "预期结果"]:
        marker = f"- {section}："
        if marker in text:
            marker_index = next(i for i, line in enumerate(block) if line == marker)
            numbered = False
            for line in block[marker_index + 1 :]:
                if line.startswith("- ") and line != marker:
                    break
                if re.match(r"\s+\d+\.\s+\S+", line):
                    numbered = True
                    break
            if not numbered:
                errors.append(f"第 {line_number} 行 {case_id}：{section} 缺少有序步骤")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint a Markdown test case report or detail file.")
    parser.add_argument("report", help="测试用例设计报告或独立明细 Markdown 文件")
    parser.add_argument(
        "--source",
        help="原始测试点或测试用例设计输入包 Markdown 文件；提供后校验每个有效 TP-* / ITP-* 都出现在追溯矩阵中",
    )
    args = parser.parse_args()

    path = Path(args.report)
    if not path.exists():
        print(f"文件不存在: {path}", file=sys.stderr)
        return 2

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    errors: list[str] = []

    is_full_report = "## 1. 设计范围" in text
    required_sections = FULL_REQUIRED_SECTIONS if is_full_report else DETAIL_REQUIRED_SECTIONS

    for section in required_sections:
        if section == "# ":
            if not lines or not lines[0].startswith("# "):
                errors.append("缺少 Markdown 一级标题")
        elif section not in text:
            errors.append(f"缺少必需章节: {section}")

    errors.extend(collect_template_placeholders(text, lines))

    blocks = find_case_blocks(lines)
    if not blocks:
        errors.append("未找到 `### TC-001` 格式的测试用例")

    seen_case_ids: set[str] = set()
    for expected_index, (case_id, line_number, _end, block) in enumerate(blocks, start=1):
        expected_id = f"TC-{expected_index:03d}"
        if case_id != expected_id:
            errors.append(f"第 {line_number} 行：期望用例编号 {expected_id}，实际 {case_id}")
        if case_id in seen_case_ids:
            errors.append(f"第 {line_number} 行：重复用例编号 {case_id}")
        seen_case_ids.add(case_id)
        errors.extend(validate_case_block(case_id, line_number, block))

    if is_full_report:
        if TRACE_HEADER not in text:
            errors.append("缺少测试点到用例追溯矩阵表头")
        trace_rows = collect_trace_rows(lines)
        if not trace_rows:
            errors.append("追溯矩阵中未找到 TP-* 或 ITP-* 行")

        traced_points: set[str] = set()
        covered_cases: set[str] = set()
        for line_number, cells in trace_rows:
            if len(cells) != 5:
                errors.append(f"第 {line_number} 行：追溯矩阵期望 5 列，实际 {len(cells)} 列")
                continue
            tp_id, summary, case_refs, status, note = cells
            if not RE_TEST_POINT_ID.fullmatch(tp_id):
                errors.append(f"第 {line_number} 行：非法测试点 ID {tp_id}")
            else:
                traced_points.add(tp_id)
            if not summary:
                errors.append(f"第 {line_number} 行：测试点摘要为空")
            if status not in ALLOWED_COVERAGE:
                errors.append(f"第 {line_number} 行：非法覆盖状态 {status}")
            refs = set(RE_TC_ID.findall(case_refs))
            if status == "已覆盖" and not refs:
                errors.append(f"第 {line_number} 行：已覆盖状态必须填写覆盖用例")
            if status in {"部分覆盖", "待确认", "未覆盖"} and not note:
                errors.append(f"第 {line_number} 行：{status} 必须填写备注")
            for ref in refs:
                if ref not in seen_case_ids:
                    errors.append(f"第 {line_number} 行：追溯矩阵引用了不存在的用例 {ref}")
                covered_cases.add(ref)

        for case_id in sorted(seen_case_ids - covered_cases):
            errors.append(f"用例 {case_id} 未出现在追溯矩阵中")

        if args.source:
            source_ids, source_errors = collect_source_test_points(Path(args.source))
            errors.extend(source_errors)
            missing_points = source_ids - traced_points
            extra_points = traced_points - source_ids
            for tp_id in sorted(missing_points):
                errors.append(f"源测试点 {tp_id} 未出现在追溯矩阵中")
            for tp_id in sorted(extra_points):
                errors.append(f"追溯矩阵包含源输入中不存在的测试点 {tp_id}")

        if QUALITY_GATE_HEADER not in text:
            errors.append("缺少质量门禁结果表头")
        gate_rows = collect_table_rows(lines, QUALITY_GATE_HEADER)
        if not gate_rows:
            errors.append("质量门禁结果表中未找到门禁行")
        seen_gates: set[str] = set()
        for line_number, cells in gate_rows:
            if len(cells) != 3:
                errors.append(f"第 {line_number} 行：质量门禁结果期望 3 列，实际 {len(cells)} 列")
                continue
            gate_name, result, note = cells
            if gate_name in seen_gates:
                errors.append(f"第 {line_number} 行：重复质量门禁 {gate_name}")
            seen_gates.add(gate_name)
            if result not in ALLOWED_GATE_RESULTS:
                errors.append(f"第 {line_number} 行：质量门禁 {gate_name} 使用了非法结果 {result}")
            if result in {"未通过", "待确认", "不适用"} and not note:
                errors.append(f"第 {line_number} 行：质量门禁 {gate_name} 为 {result} 时必须填写说明")

        for gate_name in REQUIRED_QUALITY_GATES:
            if gate_name not in seen_gates:
                errors.append(f"质量门禁结果缺少必需门禁: {gate_name}")

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
