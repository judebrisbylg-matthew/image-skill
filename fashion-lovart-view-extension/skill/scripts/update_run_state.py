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
GLOBAL_UNFINISHED_LIMIT = 10
GLOBAL_UNFINISHED_STATUSES = {"submitted", "queued", "generating", "in_progress"}
DISPLAY_WIDTH_UNIT = 1.0
HORIZONTAL_GAP_RATIO = 0.08
VERTICAL_GAP_RATIO = 0.08
SKC_GAP_RATIO = 0.25
LAYOUT_CONTRACT_VERSION = "date-skc-four-row-v3"
LAYOUT_VIEW_ORDER = ("front", "side", "back", "full")
PRIMARY_ROW_SLOTS = tuple(range(1, 6))
SUPPLEMENTAL_ROW_SLOTS = tuple(range(6, 11))
BATCH_CONTEXT_SCHEMA_VERSION = 1
QUALITY_REASON_CODES = {
    "identity-drift",
    "head-crop-below-minimum",
    "full-head-incomplete",
    "long-dress-hem-cropped",
}
TRANSITIONS = {
    "pending": {"submitted", "blocked"},
    "submitted": {"queued", "generated", "blocked"},
    "queued": {"generated", "blocked"},
    "generated": {"qualified", "rejected", "blocked"},
    "rejected": {"submitted", "blocked"},
    "qualified": set(),
    "blocked": set(),
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_nonblank_string(value: object) -> bool:
    return type(value) is str and bool(value) and value == value.strip()


def canonical_task_label(
    state: dict,
    view_key: str,
    action_id: str,
    attempt: int,
) -> str:
    return (
        f"SKC {state.get('skc_id')} | VIEW {view_key} | ACTION {action_id} | "
        f"ATTEMPT {attempt}"
    )


def _strict_positive_int(value: object) -> bool:
    return type(value) is int and value >= 1


def _attempt_record(action: dict, attempt: int) -> dict | None:
    history = action.get("attempt_history")
    if type(history) is not list:
        return None
    matches = [
        item
        for item in history
        if type(item) is dict and item.get("attempt") == attempt
    ]
    return matches[0] if len(matches) == 1 else None


def _all_artifact_records(state: dict) -> list[tuple[str, str, int, str]]:
    records = []
    views = state.get("views")
    if type(views) is not dict:
        return records
    for view_key, view in views.items():
        if type(view) is not dict:
            continue
        actions = view.get("actions")
        if type(actions) is not dict:
            continue
        for action_id, action in actions.items():
            if type(action) is not dict or type(action.get("attempt_history")) is not list:
                continue
            for attempt in action["attempt_history"]:
                if type(attempt) is not dict:
                    continue
                artifact_id = attempt.get("artifact_id")
                if _canonical_nonblank_string(artifact_id):
                    records.append(
                        (view_key, action_id, attempt.get("attempt"), artifact_id)
                    )
    return records


def _batch_context_errors(state: dict, batch_context: object) -> list[str]:
    if type(batch_context) is not dict:
        return ["batch context is required for submission"]
    if set(batch_context) != {"schema_version", "skc_ids", "states"}:
        return [
            "batch context must contain exactly schema_version, skc_ids, and states"
        ]
    errors = []
    if (
        type(batch_context.get("schema_version")) is not int
        or batch_context["schema_version"] != BATCH_CONTEXT_SCHEMA_VERSION
    ):
        errors.append("batch context schema_version must be strict integer 1")
    skc_ids = batch_context.get("skc_ids")
    states = batch_context.get("states")
    if (
        type(skc_ids) is not list
        or not skc_ids
        or any(not _canonical_nonblank_string(item) for item in skc_ids)
        or len(set(skc_ids)) != len(skc_ids)
    ):
        errors.append("batch context skc_ids must be unique canonical strings")
    if type(states) is not list or type(skc_ids) is not list or len(states) != len(skc_ids):
        errors.append("batch context states must cover every declared SKC exactly once")
        return errors
    current_matches = 0
    current_context = state.get("execution_context")
    for expected_skc_id, candidate in zip(skc_ids, states):
        if type(candidate) is not dict or candidate.get("skc_id") != expected_skc_id:
            errors.append(
                "batch context states must match skc_ids in deterministic order"
            )
            continue
        if candidate is state:
            current_matches += 1
        candidate_views = candidate.get("views")
        if (
            type(candidate.get("schema_version")) is not int
            or candidate["schema_version"] < 5
            or type(candidate_views) is not dict
            or not candidate_views
        ):
            errors.append(
                f"batch context state {expected_skc_id} is not a current run-state"
            )
        elif any(
            type(candidate_view) is not dict
            or type(candidate_view.get("actions")) is not dict
            or any(
                type(action) is not dict
                or action.get("status") not in TRANSITIONS
                for action in candidate_view["actions"].values()
            )
            for candidate_view in candidate_views.values()
        ):
            errors.append(
                f"batch context state {expected_skc_id} has malformed action state"
            )
        candidate_context = candidate.get("execution_context")
        if type(candidate_context) is not dict:
            errors.append(
                f"batch context state {expected_skc_id} lacks execution context"
            )
            continue
        candidate_expected = candidate_context.get("expected_month_project")
        candidate_verified = candidate_context.get("verified_month_project")
        if (
            not _canonical_nonblank_string(candidate_expected)
            or not _canonical_nonblank_string(candidate_verified)
            or candidate_expected != candidate_verified
            or candidate_context.get("project_verification_status") != "verified"
            or candidate_context.get("blocker") is not None
            or candidate_context.get("feedback_required") is not False
        ):
            errors.append(
                f"batch context state {expected_skc_id} has inconsistent month project evidence"
            )
        if type(current_context) is dict:
            for field in ("expected_month_project", "date_region"):
                if candidate_context.get(field) != current_context.get(field):
                    errors.append(
                        f"batch context state {expected_skc_id} has mismatched {field}"
                    )
    if current_matches != 1:
        errors.append("batch context must contain the live current state exactly once")
    return errors


def _batch_unfinished_candidate_count(batch_context: dict) -> int:
    return sum(
        _global_unfinished_candidate_count(state)
        for state in batch_context["states"]
    )


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


def _placement_records(action: dict) -> list:
    canvas = action.get("canvas")
    if not isinstance(canvas, dict):
        return []
    placements = canvas.get("placements")
    return placements if isinstance(placements, list) else []


def _verified_placements(action: dict) -> set[int]:
    return {
        item["attempt"]
        for item in _placement_records(action)
        if isinstance(item, dict)
        and type(item.get("attempt")) is int
        and item.get("verified") is True
    }


def placement_backlog(state: dict) -> list[dict]:
    """Return generated artifacts that do not yet have verified canvas placement."""
    backlog = []
    for view_key, view in state.get("views", {}).items():
        for action_id, action in view.get("actions", {}).items():
            placed = _verified_placements(action)
            history = action.get("attempt_history")
            if type(history) is not list:
                backlog.append(
                    {
                        "view": view_key,
                        "action_id": action_id,
                        "attempt": None,
                        "malformed": "attempt_history must be a list",
                    }
                )
                continue
            for attempt in history:
                if type(attempt) is not dict:
                    backlog.append(
                        {
                            "view": view_key,
                            "action_id": action_id,
                            "attempt": None,
                            "malformed": "attempt record must be an object",
                        }
                    )
                    continue
                attempt_number = attempt.get("attempt")
                if attempt.get("result_recorded_at") and (
                    type(attempt_number) is not int or attempt_number not in placed
                ):
                    backlog.append(
                        {
                            "view": view_key,
                            "action_id": action_id,
                            "attempt": attempt_number,
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
    view_rows = reservation.get("view_rows")
    valid_rows = type(view_rows) is list and len(view_rows) == len(LAYOUT_VIEW_ORDER)
    if valid_rows:
        for row, expected_view in zip(view_rows, LAYOUT_VIEW_ORDER):
            if type(row) is not dict or set(row) != {"view", "cells"}:
                valid_rows = False
                break
            cells = row["cells"]
            if (
                row["view"] != expected_view
                or type(cells) is not list
                or len(cells) != 10
                or any(type(cell) is not int for cell in cells)
                or cells != list(range(1, 11))
            ):
                valid_rows = False
                break
    if not valid_rows:
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


def _assert_submission_gate(
    state: dict,
    view_key: str,
    action_id: str,
    attempt: int,
    task_label: str | None,
    batch_context: object,
) -> None:
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
    if not isinstance(context, dict):
        raise ValueError("month project is not verified")
    expected_project = context.get("expected_month_project")
    verified_project = context.get("verified_month_project")
    if (
        context.get("project_verification_status") != "verified"
        or not _canonical_nonblank_string(expected_project)
        or not _canonical_nonblank_string(verified_project)
        or expected_project != verified_project
        or context.get("blocker") is not None
        or context.get("feedback_required") is not False
    ):
        raise ValueError("month project evidence is not internally verified")
    if placement_backlog(state):
        raise ValueError("placement backlog must be zero before submission")
    expected_label = canonical_task_label(state, view_key, action_id, attempt)
    if task_label != expected_label:
        raise ValueError(f"exact canonical task label is required: {expected_label}")
    batch_errors = _batch_context_errors(state, batch_context)
    if batch_errors:
        raise ValueError("invalid batch context: " + "; ".join(batch_errors))
    if _batch_unfinished_candidate_count(batch_context) >= GLOBAL_UNFINISHED_LIMIT:
        raise ValueError("global unfinished limit reached")


def evaluate_review_gate(state: dict) -> dict:
    """Allow unified review only after 5 identified, placed base results per view."""
    missing = {}
    identity_missing = []
    placement_issues = placement_backlog(state)
    base_artifact_ids = []
    base_results = []
    views = state.get("views")
    if type(views) is not dict or set(views) != set(PREFIXES):
        identity_missing.append("views: expected exactly front, side, back, full")
    if type(views) is not dict:
        views = {}
    for view_key, prefix in PREFIXES.items():
        view = views.get(view_key)
        if not isinstance(view, dict):
            missing[view_key] = 5
            continue
        actions = view.get("actions")
        expected_action_ids = {f"{prefix}{index:02d}" for index in range(1, 6)}
        if type(actions) is not dict:
            missing[view_key] = 5
            continue
        if set(actions) != expected_action_ids:
            identity_missing.append(f"{view_key}: expected exactly actions 01 through 05")
        base_count = 0
        for index in range(1, 6):
            action_id = f"{prefix}{index:02d}"
            action = actions.get(action_id)
            if not isinstance(action, dict):
                continue
            attempt_history = action.get("attempt_history")
            if type(attempt_history) is not list:
                continue
            first_attempts = [
                attempt
                for attempt in attempt_history
                if type(attempt) is dict
                and type(attempt.get("attempt")) is int
                and attempt.get("attempt") == 1
                and _has_aware_iso_timestamp(attempt.get("result_recorded_at"))
            ]
            if len(first_attempts) != 1:
                continue
            first = first_attempts[0]
            expected_label = (
                f"SKC {state.get('skc_id')} | VIEW {view_key} | ACTION {action_id} | ATTEMPT 1"
            )
            if (
                not isinstance(first.get("artifact_id"), str)
                or not first["artifact_id"].strip()
                or first["artifact_id"] != first["artifact_id"].strip()
                or first.get("task_label") != expected_label
            ):
                identity_missing.append(f"{view_key}/{action_id}/1")
                continue
            base_count += 1
            base_artifact_ids.append(first["artifact_id"])
            placements = _placement_records(action)
            valid_primary = any(
                type(item) is dict
                and type(item.get("attempt")) is int
                and item.get("attempt") == 1
                and item.get("area") == "primary"
                and type(item.get("slot")) is int
                and item.get("slot") == index
                and type(item.get("row_slot")) is int
                and item.get("row_slot") == index
                and item.get("verified") is True
                and item.get("placement_status") == "verified"
                for item in placements
            )
            if not valid_primary:
                placement_issues.append(
                    {"view": view_key, "action_id": action_id, "attempt": 1}
                )
            else:
                base_results.append(
                    {
                        "view": view_key,
                        "action_id": action_id,
                        "attempt": 1,
                        "task_label": expected_label,
                        "artifact_id": first["artifact_id"],
                        "primary_slot": index,
                        "placement_status": "verified",
                    }
                )
        if base_count < 5:
            missing[view_key] = 5 - base_count

        occupied_slots = {}
        for action_id, action in actions.items():
            if type(action) is not dict:
                continue
            for placement in _placement_records(action):
                if (
                    type(placement) is not dict
                    or placement.get("verified") is not True
                    or type(placement.get("row_slot")) is not int
                ):
                    continue
                row_slot = placement["row_slot"]
                owner = (action_id, placement.get("attempt"))
                if row_slot in occupied_slots and occupied_slots[row_slot] != owner:
                    placement_issues.append(
                        {
                            "view": view_key,
                            "row_slot": row_slot,
                            "collision": [occupied_slots[row_slot], owner],
                        }
                    )
                occupied_slots[row_slot] = owner

    if len(base_artifact_ids) != len(set(base_artifact_ids)):
        identity_missing.append("base artifact_id values must be unique")

    if missing:
        result = {
            "status": "blocked:base-count-incomplete",
            "review_allowed": False,
            "missing_base_results": missing,
            "identity_missing": identity_missing,
            "placement_backlog": placement_issues,
        }
    elif identity_missing:
        result = {
            "status": "blocked:result-identity",
            "review_allowed": False,
            "missing_base_results": {},
            "identity_missing": identity_missing,
            "placement_backlog": placement_issues,
        }
    elif placement_issues:
        result = {
            "status": "blocked:canvas-placement",
            "review_allowed": False,
            "missing_base_results": {},
            "identity_missing": [],
            "placement_backlog": placement_issues,
        }
    else:
        result = {
            "status": "ready",
            "review_allowed": True,
            "missing_base_results": {},
            "identity_missing": [],
            "placement_backlog": [],
            "base_result_count": 20,
            "base_artifact_ids": list(base_artifact_ids),
            "base_results": base_results,
            "verified_at": now_iso(),
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
        action = view["actions"][action_id]
    except KeyError as exc:
        raise ValueError(f"unknown action {view_key}/{action_id}") from exc
    if type(view) is not dict or type(action) is not dict:
        raise ValueError(f"unknown action {view_key}/{action_id}")
    if type(attempt) is not int or type(slot) is not int:
        raise ValueError("attempt and slot must be strict JSON integers")
    if type(verified) is not bool:
        raise ValueError("verified must be boolean")
    attempts = action.get("attempts")
    if type(attempts) is not int or isinstance(attempts, bool):
        raise ValueError("action attempts must be a strict JSON integer")
    if attempt < 1 or attempt > attempts:
        raise ValueError(f"attempt {attempt} has not been submitted")
    if area not in {"primary", "supplemental"}:
        raise ValueError("area must be primary or supplemental")
    action_slot = int(action_id[-2:])
    if area == "primary" and (slot not in PRIMARY_ROW_SLOTS or slot != action_slot):
        raise ValueError("primary slots 1 through 5 must match the action number")
    if area == "supplemental" and slot not in SUPPLEMENTAL_ROW_SLOTS:
        raise ValueError("supplemental slots must be physical row slots 6 through 10")
    attempt_record = _attempt_record(action, attempt)
    expected_label = canonical_task_label(state, view_key, action_id, attempt)
    if (
        type(attempt_record) is not dict
        or not _has_aware_iso_timestamp(attempt_record.get("result_recorded_at"))
        or not _canonical_nonblank_string(attempt_record.get("artifact_id"))
        or attempt_record.get("task_label") != expected_label
    ):
        raise ValueError(
            "result with canonical task label and nonblank artifact must exist before placement"
        )
    artifact_records = _all_artifact_records(state)
    artifact_id = attempt_record["artifact_id"]
    if sum(record[3] == artifact_id for record in artifact_records) != 1:
        raise ValueError("artifact identity must be unique before placement")
    canvas = action.get("canvas")
    placements = canvas.get("placements") if type(canvas) is dict else None
    if type(placements) is not list:
        raise ValueError("action canvas placements must be a list")
    record = next(
        (
            item
            for item in placements
            if type(item) is dict and item.get("attempt") == attempt
        ),
        None,
    )
    if area == "supplemental":
        if (
            type(record) is not dict
            or record.get("area") != "primary"
            or record.get("verified") is not True
            or not any(
                type(candidate) is dict
                and type(candidate.get("attempt")) is int
                and candidate["attempt"] > attempt
                and _has_aware_iso_timestamp(candidate.get("result_recorded_at"))
                and _canonical_nonblank_string(candidate.get("artifact_id"))
                and candidate.get("task_label")
                == canonical_task_label(
                    state, view_key, action_id, candidate["attempt"]
                )
                for candidate in action.get("attempt_history", [])
            )
        ):
            raise ValueError(
                "only a verified primary result displaced by a later returned attempt may move to supplemental"
            )
    for other_action_id, other_action in view.get("actions", {}).items():
        if type(other_action) is not dict:
            continue
        for existing in _placement_records(other_action):
            if type(existing) is not dict:
                continue
            if other_action_id == action_id and existing is record:
                continue
            if existing.get("row_slot") == slot:
                raise ValueError(
                    f"row slot {slot} is already occupied by another placement"
                )
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


def _global_unfinished_candidate_count(state: dict) -> int:
    return sum(
        1
        for view in state.get("views", {}).values()
        if isinstance(view, dict)
        for action in view.get("actions", {}).values()
        if isinstance(action, dict)
        and action.get("status") in GLOBAL_UNFINISHED_STATUSES
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


def _review_gate_is_ready(state: dict) -> bool:
    gate = state.get("review_gate")
    if type(gate) is not dict:
        return False
    artifact_ids = gate.get("base_artifact_ids")
    base_results = gate.get("base_results")
    if not (
        gate.get("status") == "ready"
        and gate.get("review_allowed") is True
        and gate.get("base_result_count") == 20
        and type(artifact_ids) is list
        and len(artifact_ids) == 20
        and all(_canonical_nonblank_string(item) for item in artifact_ids)
        and len(set(artifact_ids)) == 20
        and type(base_results) is list
        and len(base_results) == 20
        and _has_aware_iso_timestamp(gate.get("verified_at"))
    ):
        return False
    expected_results = []
    views = state.get("views")
    if type(views) is not dict or set(views) != set(PREFIXES):
        return False
    for view_key, prefix in PREFIXES.items():
        view = views.get(view_key)
        actions = view.get("actions") if type(view) is dict else None
        expected_action_ids = {f"{prefix}{index:02d}" for index in range(1, 6)}
        if type(actions) is not dict or set(actions) != expected_action_ids:
            return False
        for index in range(1, 6):
            action_id = f"{prefix}{index:02d}"
            action = actions[action_id]
            first = _attempt_record(action, 1) if type(action) is dict else None
            expected_label = canonical_task_label(state, view_key, action_id, 1)
            if (
                type(first) is not dict
                or not _has_aware_iso_timestamp(first.get("result_recorded_at"))
                or not _canonical_nonblank_string(first.get("artifact_id"))
                or first.get("task_label") != expected_label
            ):
                return False
            expected_results.append(
                {
                    "view": view_key,
                    "action_id": action_id,
                    "attempt": 1,
                    "task_label": expected_label,
                    "artifact_id": first["artifact_id"],
                    "primary_slot": index,
                    "placement_status": "verified",
                }
            )
    return (
        artifact_ids == [item["artifact_id"] for item in expected_results]
        and base_results == expected_results
    )


def _attempt_has_verified_placement(
    action: dict, attempt: int, action_id: str
) -> bool:
    primary_slot = int(action_id[-2:])
    return any(
        type(item) is dict
        and item.get("attempt") == attempt
        and item.get("area") == "primary"
        and item.get("slot") == primary_slot
        and item.get("row_slot") == primary_slot
        and item.get("verified") is True
        and item.get("placement_status") == "verified"
        for item in _placement_records(action)
    )


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
    batch_context: dict | None = None,
) -> dict:
    try:
        view = state["views"][view_key]
        action = view["actions"][action_id]
    except KeyError as exc:
        raise ValueError(f"unknown action {view_key}/{action_id}") from exc
    if type(view) is not dict or type(action) is not dict:
        raise ValueError(f"unknown action {view_key}/{action_id}")
    old_status = action["status"]
    if new_status not in TRANSITIONS.get(old_status, set()):
        raise ValueError(f"invalid transition: {old_status} -> {new_status}")
    if reason_code is not None:
        if reason_code not in QUALITY_REASON_CODES:
            raise ValueError(f"unknown quality reason code: {reason_code}")
        if new_status != "rejected":
            raise ValueError("reason_code is only allowed for rejected transitions")
    if new_status == "rejected":
        if not _canonical_nonblank_string(reason):
            raise ValueError("rejected transition requires a non-empty string reason")
    if type(action.get("attempt_history")) is not list:
        raise ValueError("action attempt_history must be a list before transition")
    if new_status == "rejected":
        if type(action.get("rejection_reasons")) is not list:
            raise ValueError("action rejection_reasons must be a list before transition")
        if type(action.get("rejection_reason_codes")) is not list:
            raise ValueError(
                "action rejection_reason_codes must be a list before transition"
            )

    if new_status == "submitted":
        attempts = action.get("attempts")
        if type(attempts) is not int or isinstance(attempts, bool) or attempts < 0:
            raise ValueError("action attempts must be a nonnegative strict JSON integer")
        next_attempt = attempts + 1
        _assert_submission_gate(
            state,
            view_key,
            action_id,
            next_attempt,
            task_label,
            batch_context,
        )
        generated = view.get("generated_count")
        generation_limit = view.get("generation_limit")
        if (
            type(generated) is not int
            or isinstance(generated, bool)
            or generated < 0
            or type(generation_limit) is not int
            or isinstance(generation_limit, bool)
            or generation_limit != VIEW_GENERATION_LIMIT
        ):
            raise ValueError("view generation counters are invalid; migrate run-state")
        reserved = _reserved_candidate_count(view)
        if generated + reserved >= generation_limit:
            raise ValueError("per-view generation limit reached")
    elif new_status == "generated":
        attempts = action.get("attempts")
        if not _strict_positive_int(attempts):
            raise ValueError("generated result requires a submitted attempt")
        expected_label = canonical_task_label(state, view_key, action_id, attempts)
        current_attempt = _attempt_record(action, attempts)
        if (
            task_label != expected_label
            or action.get("lovart_task_label") != expected_label
            or type(current_attempt) is not dict
            or current_attempt.get("task_label") != expected_label
        ):
            raise ValueError("artifact identity is required with the exact canonical task label")
        if not _canonical_nonblank_string(artifact_id):
            raise ValueError("artifact identity must be a canonical nonblank string")
        if current_attempt.get("result_recorded_at") is not None:
            raise ValueError("generated candidate already recorded for this attempt")
        if any(record[3] == artifact_id for record in _all_artifact_records(state)):
            raise ValueError("artifact identity must be unique within the SKC run-state")
        generated = view.get("generated_count")
        if type(generated) is not int or isinstance(generated, bool) or generated < 0:
            raise ValueError("view generated_count is invalid; migrate run-state")
    elif new_status in {"qualified", "rejected"}:
        if not _review_gate_is_ready(state):
            raise ValueError("20-result review gate must be ready before quality review")
        attempts = action.get("attempts")
        current_attempt = (
            _attempt_record(action, attempts)
            if _strict_positive_int(attempts)
            else None
        )
        expected_label = (
            canonical_task_label(state, view_key, action_id, attempts)
            if _strict_positive_int(attempts)
            else None
        )
        if (
            type(current_attempt) is not dict
            or not _has_aware_iso_timestamp(current_attempt.get("result_recorded_at"))
            or not _canonical_nonblank_string(current_attempt.get("artifact_id"))
            or current_attempt.get("task_label") != expected_label
        ):
            raise ValueError("quality review requires a canonical returned artifact")
        if not _attempt_has_verified_placement(action, attempts, action_id):
            raise ValueError("quality review requires verified canvas placement")

    if new_status == "submitted":
        action["attempts"] = next_attempt
        action["submitted_at"] = now_iso()
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
        _record_generated_candidate(view, action, "generated")
        action["attempt_history"][-1]["artifact_id"] = artifact_id
    if new_status in {"qualified", "rejected"}:
        action["attempt_history"][-1]["result_status"] = new_status
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
    if new_status in {"qualified", "rejected"}:
        _block_view_at_generation_cap(view)
    state["schema_version"] = max(5, state.get("schema_version", 1))
    state["updated_at"] = now_iso()
    _recompute_state(state)
    return state


def _recompute_state(state: dict) -> None:
    view_statuses = []
    views = state.get("views")
    if type(views) is not dict:
        state["status"] = "blocked"
        return
    for view_key, view in views.items():
        actions = view.get("actions", {})
        if not actions:
            view_statuses.append(view["status"])
            continue
        statuses = {action["status"] for action in actions.values()}
        qualified_primary = statuses == {"qualified"} and all(
            _strict_positive_int(action.get("attempts"))
            and any(
                type(placement) is dict
                and placement.get("attempt") == action["attempts"]
                and placement.get("area") == "primary"
                and placement.get("slot") == int(action_id[-2:])
                and placement.get("row_slot") == int(action_id[-2:])
                and placement.get("verified") is True
                and placement.get("placement_status") == "verified"
                for placement in _placement_records(action)
            )
            for action_id, action in actions.items()
        )
        if qualified_primary:
            view["status"] = "completed"
        elif statuses == {"qualified"}:
            view["status"] = "partial"
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
    elif (
        set(views) == set(PREFIXES)
        and all(status == "completed" for status in view_statuses)
        and _review_gate_is_ready(state)
        and not placement_backlog(state)
    ):
        state["status"] = "completed"
    elif any(status in {"partial"} or status.startswith("blocked:") for status in view_statuses):
        state["status"] = "partial"
    elif any(status in {"queued", "in_progress"} for status in view_statuses):
        state["status"] = "in_progress"
    else:
        state["status"] = "pending"


def _load_batch_context(
    batch_inventory_path: Path | None,
    current_state_path: Path,
    current_state: dict,
    other_state_paths: list[Path] | None,
) -> dict | None:
    if batch_inventory_path is None:
        return None
    inventory = json.loads(batch_inventory_path.read_text(encoding="utf-8"))
    skcs = inventory.get("skcs") if type(inventory) is dict else None
    if type(skcs) is not list:
        raise ValueError("batch inventory must contain a skcs list")
    skc_ids = [item.get("skc_id") if type(item) is dict else None for item in skcs]
    paths = [current_state_path, *(other_state_paths or [])]
    resolved_paths = [path.expanduser().resolve() for path in paths]
    if len(set(resolved_paths)) != len(resolved_paths):
        raise ValueError("batch state paths must be unique")
    states = []
    for path in resolved_paths:
        if path == current_state_path.expanduser().resolve():
            states.append(current_state)
        else:
            states.append(json.loads(path.read_text(encoding="utf-8")))
    state_by_skc = {
        item.get("skc_id"): item
        for item in states
        if type(item) is dict and _canonical_nonblank_string(item.get("skc_id"))
    }
    ordered_states = [state_by_skc.get(skc_id) for skc_id in skc_ids]
    return {
        "schema_version": BATCH_CONTEXT_SCHEMA_VERSION,
        "skc_ids": skc_ids,
        "states": ordered_states,
    }


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
    update.add_argument("--batch-inventory", type=Path)
    update.add_argument("--batch-state", type=Path, action="append", default=[])
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
        batch_context = _load_batch_context(
            args.batch_inventory,
            destination,
            payload,
            args.batch_state,
        )
        transition_action(
            payload,
            args.view,
            args.action_id,
            args.status,
            reason=args.reason,
            reason_code=args.reason_code,
            task_label=args.task_label,
            artifact_id=args.artifact_id,
            batch_context=batch_context,
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
