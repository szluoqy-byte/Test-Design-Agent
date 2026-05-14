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
GUI_TERMS = [
    "页面",
    "菜单",
    "页签",
    "按钮",
    "输入框",
    "下拉",
    "表格",
    "列表",
    "筛选",
    "分页",
    "弹窗",
    "提示区",
    "点击",
]
GUI_ACTION_TERMS = [
    "点击",
    "输入",
    "选择",
    "清空",
    "打开",
    "切换",
    "关闭",
]
GENERIC_GUI_STEPS = [
    "查看页面",
    "验证布局",
    "检查列表",
    "执行查询",
    "进行操作",
]
LOGIN_TERMS = ["登录", "登陆"]
LOGIN_ENV_LABEL_TERMS = [
    "ADC",
    "FI",
    "Web",
    "WEB",
    "管理后台",
    "后台",
    "控制台",
    "门户",
    "Portal",
    "Console",
]


def contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def has_gui_object(text: str) -> bool:
    return "【" in text and "】" in text


def is_gui_case(text: str, steps: list[str]) -> bool:
    return contains_any(text, GUI_TERMS) or any(contains_any(step, GUI_TERMS) for step in steps)


def is_login_step(step: str) -> bool:
    return contains_any(step, LOGIN_TERMS) and contains_any(step, LOGIN_ENV_LABEL_TERMS)


def is_complete_entry_step(step: str) -> bool:
    return has_gui_object(step) and ">" in step and contains_any(step, ["点击", "进入", "打开", "切换"])


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

        if steps and is_gui_case(text, steps):
            first_step = steps[0]
            if not is_login_step(first_step):
                errors.append(
                    f"第 {line_number} 行 {case_id}：GUI 场景用例的测试步骤第 1 步必须描述登录带环境类型标签的环境，例如 ADC、FI、Web、管理后台"
                )

            if not any(is_complete_entry_step(item) for item in steps[1:]):
                errors.append(
                    f"第 {line_number} 行 {case_id}：GUI 场景用例缺少完整入口链路，入口步骤应包含【对象】和 > 路径"
                )

            for item in steps:
                if contains_any(item, GENERIC_GUI_STEPS) and not has_gui_object(item):
                    errors.append(f"第 {line_number} 行 {case_id}：GUI 步骤 `{item}` 缺少可自动化定位的操作对象")
                if contains_any(item, GUI_ACTION_TERMS) and not is_login_step(item) and not has_gui_object(item):
                    errors.append(f"第 {line_number} 行 {case_id}：GUI 动作 `{item}` 缺少【页面/控件/区域】对象")

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
