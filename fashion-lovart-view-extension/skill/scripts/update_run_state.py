#!/usr/bin/env python3
"""Initialize and update resumable Lovart action state."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path


PREFIXES = {"front": "FR", "side": "SI", "back": "BA", "full": "FU"}
VIEW_GENERATION_LIMIT = 10
VIEW_SUPPLEMENTAL_LIMIT = 5
DISPLAY_WIDTH_UNIT = 1.0
HORIZONTAL_GAP_RATIO = 0.08
VERTICAL_GAP_RATIO = 0.08
SKC_GAP_RATIO = 0.25
LAYOUT_CONTRACT_VERSION = "date-skc-four-row-v3"
LAYOUT_VIEW_ORDER = ("front", "side", "back", "full")
QUALITY_REASON_CODES = {
    "identity-drift",
    "head-crop-below-minimum",
    "full-head-incomplete",
    "long-dress-hem-cropped",
}
TRANSITIONS = {
    "pending": {"submitted", "blocked"},
    "submitted": {"queued", "generated", "qualified", "rejected", "blocked"},
    "queued": {"generated", "qualified", "rejected", "blocked"},
    "generated": {"qualified", "rejected", "blocked"},
    "rejected": {"submitted", "blocked"},
    "qualified": set(),
    "blocked": set(),
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _layout_reservation(
    *,
    status: str,
    date_region: str | None,
    skc_label: str | None,
    verified_at: str | None,
) -> dict:
    return {
        "contract_version": LAYOUT_CONTRACT_VERSION,
        "status": status,
        "date_region": date_region,
        "skc_label": skc_label,
        "verified_at": verified_at,
        "view_rows": [
            {"view": view_key, "cells": list(range(1, 11))}
            for view_key in LAYOUT_VIEW_ORDER
        ],
        "horizontal_gap_ratio": HORIZONTAL_GAP_RATIO,
        "vertical_gap_ratio": VERTICAL_GAP_RATIO,
        "skc_gap_ratio": SKC_GAP_RATIO,
    }


def initialize_state(manifest: dict, execution_context: dict | None = None) -> dict:
    views = {}
    for view_key, view_manifest in manifest.get("views", {}).items():
        source_status = view_manifest.get("status", "blocked:manifest")
        if source_status != "ready":
            views[view_key] = {"status": source_status, "actions": {}}
            continue
        prefix = PREFIXES[view_key]
        actions = {
            f"{prefix}{index:02d}": {
                "status": "pending",
                "attempts": 0,
                "submitted_at": None,
                "updated_at": None,
                "lovart_task_label": None,
                "rejection_reasons": [],
                "rejection_reason_codes": [],
                "attempt_history": [],
                "blocker": None,
                "canvas": {
                    "primary_slot": index,
                    "current_attempt": None,
                    "placements": [],
                },
            }
            for index in range(1, 6)
        }
        views[view_key] = {
            "status": "pending",
            "generation_limit": VIEW_GENERATION_LIMIT,
            "generated_count": 0,
            "supplemental_limit": VIEW_SUPPLEMENTAL_LIMIT,
            "actions": actions,
        }
    return {
        "schema_version": 5,
        "skc_id": manifest["skc_id"],
        "status": "pending",
        "updated_at": now_iso(),
        "execution_blocker": None,
        "execution_context": deepcopy(execution_context),
        "layout_reservation": _layout_reservation(
            status="pending",
            date_region=None,
            skc_label=None,
            verified_at=None,
        ),
        "views": views,
    }


def record_layout_reservation(
    state: dict,
    *,
    date_region: str,
    skc_label: str,
    verified: bool,
) -> dict:
    """Record the preallocated ten-cell-by-four-row destination block."""
    if not date_region or not skc_label:
        raise ValueError("date_region and skc_label are required")
    state["layout_reservation"] = _layout_reservation(
        status="verified" if verified else "blocked:canvas-reservation",
        date_region=date_region,
        skc_label=skc_label,
        verified_at=now_iso() if verified else None,
    )
    state["schema_version"] = max(5, state.get("schema_version", 1))
    state["updated_at"] = now_iso()
    return state


def _verified_placements(action: dict) -> set[int]:
    return {
        int(item["attempt"])
        for item in action.get("canvas", {}).get("placements", [])
        if item.get("verified")
    }


def placement_backlog(state: dict) -> list[dict]:
    """Return generated artifacts that do not yet have verified canvas placement."""
    backlog = []
    for view_key, view in state.get("views", {}).items():
        for action_id, action in view.get("actions", {}).items():
            placed = _verified_placements(action)
            for attempt in action.get("attempt_history", []):
                if attempt.get("result_recorded_at") and attempt["attempt"] not in placed:
                    backlog.append(
                        {
                            "view": view_key,
                            "action_id": action_id,
                            "attempt": attempt["attempt"],
                            "artifact_id": attempt.get("artifact_id"),
                        }
                    )
    return backlog


def _has_aware_iso_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _layout_reservation_errors(state: dict) -> list[str]:
    reservation = state.get("layout_reservation")
    if not isinstance(reservation, dict):
        return ["layout_reservation must be an object"]
    errors = []
    if reservation.get("contract_version") != LAYOUT_CONTRACT_VERSION:
        errors.append(f"contract_version must be {LAYOUT_CONTRACT_VERSION}")
    date_region = reservation.get("date_region")
    if not isinstance(date_region, str) or not date_region.strip():
        errors.append("date_region must be a nonblank string")
    skc_label = reservation.get("skc_label")
    if not isinstance(skc_label, str) or not skc_label.strip():
        errors.append("skc_label must be a nonblank string")
    if not _has_aware_iso_timestamp(reservation.get("verified_at")):
        errors.append("verified_at must be a timezone-aware ISO timestamp")
    expected_rows = [
        {"view": view_key, "cells": list(range(1, 11))}
        for view_key in LAYOUT_VIEW_ORDER
    ]
    if reservation.get("view_rows") != expected_rows:
        errors.append("view_rows must be front/side/back/full with cells 1 through 10")
    expected_ratios = {
        "horizontal_gap_ratio": HORIZONTAL_GAP_RATIO,
        "vertical_gap_ratio": VERTICAL_GAP_RATIO,
        "skc_gap_ratio": SKC_GAP_RATIO,
    }
    for field, expected in expected_ratios.items():
        if reservation.get(field) != expected:
            errors.append(f"{field} must be {expected}")
    context = state.get("execution_context")
    if isinstance(context, dict) and context.get("date_region"):
        if date_region != context["date_region"]:
            errors.append("date_region must match the verified execution context")
    skc_id = state.get("skc_id")
    if isinstance(skc_id, str) and skc_id.strip() and isinstance(skc_label, str):
        if skc_id not in skc_label:
            errors.append("skc_label must identify the active SKC")
    return errors


def _assert_submission_gate(state: dict, task_label: str | None) -> None:
    """Reject browser submissions while deterministic preconditions are unmet."""
    reservation = state.get("layout_reservation")
    if not isinstance(reservation, dict) or reservation.get("status") != "verified":
        raise ValueError("layout reservation is not verified")
    layout_errors = _layout_reservation_errors(state)
    if layout_errors:
        raise ValueError(
            "layout reservation is incomplete; run reserve-layout again: "
            + "; ".join(layout_errors)
        )
    context = state.get("execution_context")
    if context is None:
        return
    if context.get("project_verification_status") != "verified":
        raise ValueError("month project is not verified")
    if placement_backlog(state):
        raise ValueError("placement backlog must be zero before submission")
    if not task_label:
        raise ValueError("exact Lovart task label is required")


def evaluate_review_gate(state: dict) -> dict:
    """Allow unified review only after 5 identified, placed base results per view."""
    missing = {}
    identity_missing = []
    for view_key, view in state.get("views", {}).items():
        actions = view.get("actions", {})
        if not actions:
            continue
        base_count = 0
        for action_id, action in actions.items():
            first = next(
                (
                    attempt
                    for attempt in action.get("attempt_history", [])
                    if attempt.get("attempt") == 1 and attempt.get("result_recorded_at")
                ),
                None,
            )
            if first is None:
                continue
            if not first.get("artifact_id") or not first.get("task_label"):
                identity_missing.append(f"{view_key}/{action_id}/1")
                continue
            base_count += 1
        if base_count < 5:
            missing[view_key] = 5 - base_count

    if missing:
        result = {
            "status": "blocked:base-count-incomplete",
            "review_allowed": False,
            "missing_base_results": missing,
            "identity_missing": identity_missing,
            "placement_backlog": placement_backlog(state),
        }
    elif identity_missing:
        result = {
            "status": "blocked:result-identity",
            "review_allowed": False,
            "missing_base_results": {},
            "identity_missing": identity_missing,
            "placement_backlog": placement_backlog(state),
        }
    elif placement_backlog(state):
        result = {
            "status": "blocked:canvas-placement",
            "review_allowed": False,
            "missing_base_results": {},
            "identity_missing": [],
            "placement_backlog": placement_backlog(state),
        }
    else:
        result = {
            "status": "ready",
            "review_allowed": True,
            "missing_base_results": {},
            "identity_missing": [],
            "placement_backlog": [],
        }
    state["review_gate"] = deepcopy(result)
    state["updated_at"] = now_iso()
    return result


def record_project_verification(state: dict, context: dict) -> dict:
    """Persist the latest browser-visible Lovart project verification."""
    state["execution_context"] = deepcopy(context)
    blocker = context.get("blocker")
    if blocker in {
        "blocked:month-project-mismatch",
        "blocked:date-context-ambiguous",
    }:
        state["execution_blocker"] = blocker
    elif context.get("project_verification_status") == "verified":
        state["execution_blocker"] = None
    state["schema_version"] = max(5, state.get("schema_version", 1))
    state["updated_at"] = now_iso()
    _recompute_state(state)
    return state


def mark_project_feedback_sent(state: dict) -> dict:
    """Record that the blocking project-mismatch feedback reached the user."""
    context = state.get("execution_context")
    if not context or not context.get("feedback_required"):
        raise ValueError("no pending project feedback")
    context["feedback_required"] = False
    context["feedback_sent_at"] = now_iso()
    state["schema_version"] = max(5, state.get("schema_version", 1))
    state["updated_at"] = now_iso()
    return state


def place_attempt(
    state: dict,
    view_key: str,
    action_id: str,
    attempt: int,
    *,
    area: str,
    slot: int,
    verified: bool,
) -> dict:
    try:
        view = state["views"][view_key]
        _upgrade_view_state(view)
        action = view["actions"][action_id]
    except KeyError as exc:
        raise ValueError(f"unknown action {view_key}/{action_id}") from exc
    if attempt < 1 or attempt > action.get("attempts", 0):
        raise ValueError(f"attempt {attempt} has not been submitted")
    if area not in {"primary", "supplemental"}:
        raise ValueError("area must be primary or supplemental")
    if slot < 1:
        raise ValueError("slot must be positive")
    if area == "primary" and slot != int(action_id[-2:]):
        raise ValueError("primary slot must match the action number")
    if area == "supplemental" and slot > int(
        view.get("supplemental_limit", VIEW_SUPPLEMENTAL_LIMIT)
    ):
        raise ValueError("supplemental slot exceeds the per-view limit")

    canvas = action.setdefault(
        "canvas",
        {"primary_slot": int(action_id[-2:]), "current_attempt": None, "placements": []},
    )
    placements = canvas.setdefault("placements", [])
    record = next((item for item in placements if item["attempt"] == attempt), None)
    payload = {
        "attempt": attempt,
        "area": area,
        "slot": slot,
        "row_slot": slot,
        "verified": verified,
        "placement_status": "verified" if verified else "unverified",
        "display_width_unit": DISPLAY_WIDTH_UNIT,
        "horizontal_gap_ratio": HORIZONTAL_GAP_RATIO,
        "vertical_gap_ratio": VERTICAL_GAP_RATIO,
        "skc_gap_ratio": SKC_GAP_RATIO,
        "placed_at": now_iso(),
    }
    if record is None:
        placements.append(payload)
    else:
        record.update(payload)
    if area == "primary":
        canvas["current_attempt"] = attempt
    elif canvas.get("current_attempt") == attempt:
        canvas["current_attempt"] = None
    action["updated_at"] = now_iso()
    state["schema_version"] = max(5, state.get("schema_version", 1))
    state["updated_at"] = now_iso()
    return state


def _record_generated_candidate(view: dict, action: dict, result_status: str) -> None:
    if not action.get("attempt_history"):
        raise ValueError("cannot record a generated candidate before submission")
    attempt = action["attempt_history"][-1]
    if attempt.get("result_recorded_at"):
        raise ValueError("generated candidate already recorded for this attempt")
    attempt["result_recorded_at"] = now_iso()
    attempt["result_status"] = result_status
    view["generated_count"] = int(view.get("generated_count", 0)) + 1


def _reserved_candidate_count(view: dict) -> int:
    return sum(
        1
        for action in view.get("actions", {}).values()
        if action.get("status") in {"submitted", "queued"}
    )


def _upgrade_view_state(view: dict) -> None:
    view.setdefault("generation_limit", VIEW_GENERATION_LIMIT)
    view.setdefault("supplemental_limit", VIEW_SUPPLEMENTAL_LIMIT)
    if "generated_count" in view:
        return
    generated = 0
    for action in view.get("actions", {}).values():
        history = action.get("attempt_history", [])
        for index, attempt in enumerate(history):
            rejected = attempt.get("rejection_reason") is not None
            qualified = action.get("status") == "qualified" and index == len(history) - 1
            if rejected or qualified:
                attempt.setdefault("result_recorded_at", action.get("updated_at") or now_iso())
                attempt.setdefault("result_status", "rejected" if rejected else "qualified")
                generated += 1
            else:
                attempt.setdefault("result_recorded_at", None)
                attempt.setdefault("result_status", None)
    view["generated_count"] = generated


def _block_view_at_generation_cap(view: dict) -> None:
    if int(view.get("generated_count", 0)) < int(
        view.get("generation_limit", VIEW_GENERATION_LIMIT)
    ):
        return
    if all(action.get("status") == "qualified" for action in view.get("actions", {}).values()):
        return
    for action in view.get("actions", {}).values():
        if action.get("status") != "qualified":
            action["status"] = "blocked"
            action["blocker"] = "blocked:quality-cap"
            action["updated_at"] = now_iso()


def transition_action(
    state: dict,
    view_key: str,
    action_id: str,
    new_status: str,
    *,
    reason: str | None = None,
    reason_code: str | None = None,
    task_label: str | None = None,
    artifact_id: str | None = None,
) -> dict:
    try:
        view = state["views"][view_key]
        _upgrade_view_state(view)
        action = view["actions"][action_id]
    except KeyError as exc:
        raise ValueError(f"unknown action {view_key}/{action_id}") from exc
    old_status = action["status"]
    if new_status not in TRANSITIONS.get(old_status, set()):
        raise ValueError(f"invalid transition: {old_status} -> {new_status}")
    if reason_code is not None:
        if reason_code not in QUALITY_REASON_CODES:
            raise ValueError(f"unknown quality reason code: {reason_code}")
        if new_status != "rejected":
            raise ValueError("reason_code is only allowed for rejected transitions")
    if new_status == "rejected":
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("rejected transition requires a non-empty string reason")

    if new_status == "submitted":
        _assert_submission_gate(state, task_label)
        generated = int(view.get("generated_count", 0))
        reserved = _reserved_candidate_count(view)
        generation_limit = int(view.get("generation_limit", VIEW_GENERATION_LIMIT))
        if generated + reserved >= generation_limit:
            raise ValueError("per-view generation limit reached")
        action["attempts"] += 1
        action["submitted_at"] = now_iso()
        if task_label:
            action["lovart_task_label"] = task_label
        action["attempt_history"].append(
            {
                "attempt": action["attempts"],
                "submitted_at": action["submitted_at"],
                "task_label": task_label,
                "artifact_id": None,
                "rejection_reason": None,
                "rejection_reason_code": None,
                "result_recorded_at": None,
                "result_status": None,
            }
        )
    if new_status == "generated":
        expected_label = action.get("lovart_task_label")
        if not artifact_id or not task_label or task_label != expected_label:
            action["blocker"] = "blocked:result-identity"
            raise ValueError("artifact identity is required and must match the task label")
        _record_generated_candidate(view, action, "generated")
        action["attempt_history"][-1]["artifact_id"] = artifact_id
    if new_status in {"qualified", "rejected"} and old_status != "generated":
        _record_generated_candidate(view, action, new_status)
    if new_status == "rejected":
        action["rejection_reasons"].append(reason)
        if reason_code is not None:
            action.setdefault("rejection_reason_codes", []).append(reason_code)
        if action["attempt_history"]:
            action["attempt_history"][-1]["rejection_reason"] = reason
            action["attempt_history"][-1]["rejection_reason_code"] = reason_code
    if new_status == "blocked" and not action["blocker"]:
        action["blocker"] = reason or "blocked:unknown"

    action["status"] = new_status
    action["updated_at"] = now_iso()
    _block_view_at_generation_cap(view)
    state["schema_version"] = max(5, state.get("schema_version", 1))
    state["updated_at"] = now_iso()
    _recompute_state(state)
    return state


def _recompute_state(state: dict) -> None:
    view_statuses = []
    for view in state["views"].values():
        actions = view.get("actions", {})
        if not actions:
            view_statuses.append(view["status"])
            continue
        statuses = {action["status"] for action in actions.values()}
        if statuses == {"qualified"}:
            view["status"] = "completed"
        elif "blocked" in statuses:
            view["status"] = "partial"
        elif "queued" in statuses:
            view["status"] = "queued"
        elif "submitted" in statuses or "rejected" in statuses:
            view["status"] = "in_progress"
        else:
            view["status"] = "pending"
        view_statuses.append(view["status"])
    if state.get("execution_blocker"):
        state["status"] = "blocked"
    elif view_statuses and all(status == "completed" for status in view_statuses):
        state["status"] = "completed"
    elif any(status in {"partial"} or status.startswith("blocked:") for status in view_statuses):
        state["status"] = "partial"
    elif any(status in {"queued", "in_progress"} for status in view_statuses):
        state["status"] = "in_progress"
    else:
        state["status"] = "pending"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("manifest", type=Path)
    init.add_argument("state", type=Path)
    init.add_argument("--execution-context", type=Path)
    update = sub.add_parser("transition")
    update.add_argument("state", type=Path)
    update.add_argument("view", choices=tuple(PREFIXES))
    update.add_argument("action_id")
    update.add_argument("status", choices=tuple(TRANSITIONS))
    update.add_argument("--reason")
    update.add_argument("--reason-code")
    update.add_argument("--task-label")
    update.add_argument("--artifact-id")
    place = sub.add_parser("place")
    place.add_argument("state", type=Path)
    place.add_argument("view", choices=tuple(PREFIXES))
    place.add_argument("action_id")
    place.add_argument("attempt", type=int)
    place.add_argument("--area", choices=("primary", "supplemental"), required=True)
    place.add_argument("--slot", type=int, required=True)
    place.add_argument("--verified", action="store_true")
    project = sub.add_parser("project")
    project.add_argument("state", type=Path)
    project.add_argument("context", type=Path)
    feedback = sub.add_parser("feedback-sent")
    feedback.add_argument("state", type=Path)
    reserve_layout = sub.add_parser("reserve-layout")
    reserve_layout.add_argument("state", type=Path)
    reserve_layout.add_argument("--date-region", required=True)
    reserve_layout.add_argument("--skc-label", required=True)
    reserve_layout.add_argument("--verified", action="store_true")
    review_gate = sub.add_parser("review-gate")
    review_gate.add_argument("state", type=Path)
    args = parser.parse_args()

    if args.command == "init":
        execution_context = None
        if args.execution_context:
            execution_context = json.loads(
                args.execution_context.read_text(encoding="utf-8")
            )
        payload = initialize_state(
            json.loads(args.manifest.read_text(encoding="utf-8")),
            execution_context,
        )
        destination = args.state
    elif args.command == "transition":
        destination = args.state
        payload = json.loads(destination.read_text(encoding="utf-8"))
        transition_action(
            payload,
            args.view,
            args.action_id,
            args.status,
            reason=args.reason,
            reason_code=args.reason_code,
            task_label=args.task_label,
            artifact_id=args.artifact_id,
        )
    elif args.command == "place":
        destination = args.state
        payload = json.loads(destination.read_text(encoding="utf-8"))
        place_attempt(
            payload,
            args.view,
            args.action_id,
            args.attempt,
            area=args.area,
            slot=args.slot,
            verified=args.verified,
        )
    elif args.command == "project":
        destination = args.state
        payload = json.loads(destination.read_text(encoding="utf-8"))
        context = json.loads(args.context.read_text(encoding="utf-8"))
        record_project_verification(payload, context)
    elif args.command == "feedback-sent":
        destination = args.state
        payload = json.loads(destination.read_text(encoding="utf-8"))
        mark_project_feedback_sent(payload)
    elif args.command == "reserve-layout":
        destination = args.state
        payload = json.loads(destination.read_text(encoding="utf-8"))
        record_layout_reservation(
            payload,
            date_region=args.date_region,
            skc_label=args.skc_label,
            verified=args.verified,
        )
    else:
        destination = args.state
        payload = json.loads(destination.read_text(encoding="utf-8"))
        gate = evaluate_review_gate(payload)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(destination)
    if args.command == "review-gate" and not gate["review_allowed"]:
        print(json.dumps(gate, ensure_ascii=False))
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
