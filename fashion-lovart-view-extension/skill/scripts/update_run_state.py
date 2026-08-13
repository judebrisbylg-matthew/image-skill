#!/usr/bin/env python3
"""Initialize and update resumable Lovart action state."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


PREFIXES = {"front": "FR", "side": "SI", "back": "BA", "full": "FU"}
VIEW_GENERATION_LIMIT = 10
VIEW_SUPPLEMENTAL_LIMIT = 5
TRANSITIONS = {
    "pending": {"submitted", "blocked"},
    "submitted": {"queued", "qualified", "rejected", "blocked"},
    "queued": {"qualified", "rejected", "blocked"},
    "rejected": {"submitted", "blocked"},
    "qualified": set(),
    "blocked": set(),
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def initialize_state(manifest: dict) -> dict:
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
    return {"schema_version": 3, "skc_id": manifest["skc_id"], "status": "pending", "views": views}


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
        "verified": verified,
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
    state["schema_version"] = max(3, state.get("schema_version", 1))
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


def transition_action(state: dict, view_key: str, action_id: str, new_status: str, *, reason: str | None = None, task_label: str | None = None) -> dict:
    try:
        view = state["views"][view_key]
        _upgrade_view_state(view)
        action = view["actions"][action_id]
    except KeyError as exc:
        raise ValueError(f"unknown action {view_key}/{action_id}") from exc
    old_status = action["status"]
    if new_status not in TRANSITIONS.get(old_status, set()):
        raise ValueError(f"invalid transition: {old_status} -> {new_status}")

    if new_status == "submitted":
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
                "rejection_reason": None,
                "result_recorded_at": None,
                "result_status": None,
            }
        )
    if new_status in {"qualified", "rejected"}:
        _record_generated_candidate(view, action, new_status)
    if new_status == "rejected":
        if not reason:
            raise ValueError("rejected transition requires a reason")
        action["rejection_reasons"].append(reason)
        if action["attempt_history"]:
            action["attempt_history"][-1]["rejection_reason"] = reason
    if new_status == "blocked" and not action["blocker"]:
        action["blocker"] = reason or "blocked:unknown"

    action["status"] = new_status
    action["updated_at"] = now_iso()
    _block_view_at_generation_cap(view)
    state["schema_version"] = max(3, state.get("schema_version", 1))
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
    if view_statuses and all(status == "completed" for status in view_statuses):
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
    update = sub.add_parser("transition")
    update.add_argument("state", type=Path)
    update.add_argument("view", choices=tuple(PREFIXES))
    update.add_argument("action_id")
    update.add_argument("status", choices=tuple(TRANSITIONS))
    update.add_argument("--reason")
    update.add_argument("--task-label")
    place = sub.add_parser("place")
    place.add_argument("state", type=Path)
    place.add_argument("view", choices=tuple(PREFIXES))
    place.add_argument("action_id")
    place.add_argument("attempt", type=int)
    place.add_argument("--area", choices=("primary", "supplemental"), required=True)
    place.add_argument("--slot", type=int, required=True)
    place.add_argument("--verified", action="store_true")
    args = parser.parse_args()

    if args.command == "init":
        payload = initialize_state(json.loads(args.manifest.read_text(encoding="utf-8")))
        destination = args.state
    elif args.command == "transition":
        destination = args.state
        payload = json.loads(destination.read_text(encoding="utf-8"))
        transition_action(payload, args.view, args.action_id, args.status, reason=args.reason, task_label=args.task_label)
    else:
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
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
