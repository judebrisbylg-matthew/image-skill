#!/usr/bin/env python3
"""Resolve a dated input path and verify the visible Lovart month project."""

from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from pathlib import Path


MONTH_RE = re.compile(r"^(?P<month>[1-9]|1[0-2])月$")
DATE_RE = re.compile(r"^(?P<month>[1-9]|1[0-2])月(?P<day>[1-9]|[12]\d|3[01])日$")


def _base_context(source_path: Path | str) -> dict:
    return {
        "source_path": str(Path(source_path).expanduser().resolve()),
        "expected_month_project": None,
        "date_region": None,
        "verified_month_project": None,
        "project_verification_status": "pending",
        "blocker": None,
        "feedback_required": False,
        "feedback_message": None,
        "feedback_sent_at": None,
    }


def resolve_lovart_context(source_path: Path | str) -> dict:
    """Derive the exact Lovart month project and date region from a path."""
    context = _base_context(source_path)
    path = Path(context["source_path"])
    candidates = (path, *path.parents)
    for candidate in candidates:
        date_match = DATE_RE.fullmatch(candidate.name)
        month_match = MONTH_RE.fullmatch(candidate.parent.name)
        if not date_match or not month_match:
            continue
        if date_match.group("month") != month_match.group("month"):
            continue
        context["expected_month_project"] = candidate.parent.name
        context["date_region"] = candidate.name
        return context

    context["project_verification_status"] = "blocked"
    context["blocker"] = "blocked:date-context-ambiguous"
    context["feedback_required"] = True
    context["feedback_message"] = (
        "任务已暂停：无法从输入路径识别月份和日期\n"
        f"输入路径：{context['source_path']}\n"
        "请提供形如“/月份/月份日期”的目录，例如“/8月/8月15日”。"
    )
    return context


def verify_visible_project(context: dict, visible_project: str | None) -> dict:
    """Return a copy of context updated with exact visible-project verification."""
    verified = deepcopy(context)
    expected = verified.get("expected_month_project")
    if not expected:
        raise ValueError("context has no expected_month_project")

    current = visible_project.strip() if isinstance(visible_project, str) else ""
    verified["verified_month_project"] = current or None
    if current == expected:
        verified["project_verification_status"] = "verified"
        verified["blocker"] = None
        verified["feedback_required"] = False
        verified["feedback_message"] = None
        verified["feedback_sent_at"] = None
        return verified

    current_label = current or "无法确认"
    verified["project_verification_status"] = "blocked"
    verified["blocker"] = "blocked:month-project-mismatch"
    verified["feedback_required"] = True
    verified["feedback_sent_at"] = None
    verified["feedback_message"] = (
        "任务已暂停：Lovart 月份项目不匹配\n"
        f"输入路径：{verified['source_path']}\n"
        f"预期项目：{expected}\n"
        f"当前项目：{current_label}\n"
        f"请进入或创建“{expected}”项目后回复“已修正”，"
        "我会重新验证并从当前进度继续。"
    )
    return verified


def _write_payload(payload: dict, destination: Path | None) -> None:
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if destination is None:
        print(rendered, end="")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(rendered, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    resolve = sub.add_parser("resolve")
    resolve.add_argument("source_path", type=Path)
    resolve.add_argument("--output", type=Path)

    verify = sub.add_parser("verify")
    verify.add_argument("context", type=Path)
    verify.add_argument("--visible-project", required=True)
    verify.add_argument("--output", type=Path)

    args = parser.parse_args()
    if args.command == "resolve":
        payload = resolve_lovart_context(args.source_path)
        _write_payload(payload, args.output)
        if payload["feedback_required"]:
            print(payload["feedback_message"])
            return 2
        return 0

    payload = json.loads(args.context.read_text(encoding="utf-8"))
    payload = verify_visible_project(payload, args.visible_project)
    _write_payload(payload, args.output or args.context)
    if payload["feedback_required"]:
        print(payload["feedback_message"])
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
