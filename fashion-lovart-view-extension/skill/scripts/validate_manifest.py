#!/usr/bin/env python3
"""Validate manifest and prompt JSON contracts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


VIEW_KEYS = {"front", "side", "back", "full"}
ACTION_PREFIXES = {"front": "FR", "side": "SI", "back": "BA", "full": "FU"}
ROLE_KEYS = {
    "model_source",
    "product_source",
    "scene_source",
    "composition_source",
    "accessory_source",
    "unused",
}
REQUIRED_ROLES = ("model_source", "product_source", "scene_source")


def validate_manifest_data(data: dict) -> list[str]:
    errors = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if not str(data.get("skc_id", "")).strip():
        errors.append("skc_id is required")
    views = data.get("views")
    if not isinstance(views, dict) or not views:
        return errors + ["views must be a non-empty object"]
    for view_key, view in views.items():
        if view_key not in VIEW_KEYS:
            errors.append(f"unknown view: {view_key}")
            continue
        if not isinstance(view, dict):
            errors.append(f"{view_key}: view must be an object")
            continue
        roles = view.get("roles")
        if not isinstance(roles, dict):
            errors.append(f"{view_key}: roles must be an object")
            continue
        unknown_roles = set(roles) - ROLE_KEYS
        if unknown_roles:
            errors.append(f"{view_key}: unknown roles: {', '.join(sorted(unknown_roles))}")
        if view.get("status") == "ready":
            for role in REQUIRED_ROLES:
                values = roles.get(role, [])
                if not values:
                    errors.append(f"{view_key}: missing required role {role}")
                elif len(values) != 1:
                    errors.append(f"{view_key}: required role {role} must contain exactly one source")
            if not roles.get("composition_source"):
                errors.append(f"{view_key}: missing composition_source or model fallback")
    return errors


def validate_prompt_data(data: dict) -> list[str]:
    errors = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if data.get("view") not in VIEW_KEYS:
        errors.append("view must be front, side, back, or full")
    generation = data.get("generation", {})
    expected = {"model": "nano banana pro", "resolution": "4K", "aspect_ratio": "2:3"}
    for key, value in expected.items():
        if generation.get(key) != value:
            errors.append(f"generation.{key} must be {value}")
    if not str(data.get("analysis_markdown", "")).strip():
        errors.append("analysis_markdown is required")
    actions = data.get("actions")
    if not isinstance(actions, list) or len(actions) != 5:
        return errors + ["actions must contain exactly five items"]
    ids = []
    view = data.get("view")
    expected_ids = (
        [f"{ACTION_PREFIXES[view]}{index:02d}" for index in range(1, 6)]
        if view in ACTION_PREFIXES
        else []
    )
    for index, action in enumerate(actions, start=1):
        if not isinstance(action, dict):
            errors.append(f"action {index} must be an object")
            continue
        action_id = str(action.get("action_id", "")).strip()
        ids.append(action_id)
        for field in ("action_id", "title", "prompt_en", "negative_prompt"):
            if not str(action.get(field, "")).strip():
                errors.append(f"action {index}: {field} is required")
        prompt = str(action.get("prompt_en", ""))
        if prompt and not any(ch.isascii() and ch.isalpha() for ch in prompt):
            errors.append(f"action {index}: prompt_en must contain English text")
        if action_id and view in ACTION_PREFIXES:
            expected_start = f"SKC {data.get('skc_id')} | VIEW {view} | ACTION {action_id} | ATTEMPT 1"
            if not prompt.startswith(expected_start):
                errors.append(f"action {index}: prompt_en must start with {expected_start}")
        lowered = prompt.casefold()
        if prompt and not (
            "nano banana pro" in lowered and "4k" in lowered and "2:3" in lowered
        ):
            errors.append(f"action {index}: prompt_en must mention Nano Banana Pro, 4K, and 2:3")
    if len(set(ids)) != len(ids):
        errors.append("action_id values must be unique")
    if expected_ids and ids != expected_ids:
        errors.append("action_id sequence must be " + ", ".join(expected_ids))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("manifest", "prompt"))
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"invalid JSON: {exc}")
        return 2
    errors = validate_manifest_data(data) if args.kind == "manifest" else validate_prompt_data(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"OK: valid {args.kind}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
