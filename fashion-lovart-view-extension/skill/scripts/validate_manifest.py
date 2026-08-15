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
CANONICAL_IDENTITY_PATH = "正面/1.jpg"
HEAD_VISIBILITY = {"full", "partial", "absent"}
HEM_POSITIONS = {"above_knee", "at_knee", "below_knee", "not_applicable"}
IDENTITY_MARKER = "IDENTITY LOCK:"
HEAD_CROP_MARKER = "HEAD CROP FLOOR:"
FULL_HEAD_MARKER = "FULL-BODY HEAD COMPLETION:"
GARMENT_FRAME_MARKER = "GARMENT FRAME LOCK:"


def _validate_canonical_source(source: object, field: str) -> list[str]:
    if not isinstance(source, dict):
        return [f"{field} must be an object"]
    errors = []
    if source.get("relative_path") != CANONICAL_IDENTITY_PATH:
        errors.append(f"{field}.relative_path must be {CANONICAL_IDENTITY_PATH}")
    sha256 = source.get("sha256")
    if not isinstance(sha256, str) or len(sha256) != 64:
        errors.append(f"{field}.sha256 must be a 64-character string")
    return errors


def validate_manifest_data(data: dict) -> list[str]:
    errors = []
    if data.get("schema_version") != 2:
        errors.append("schema_version must be 2")
    if not str(data.get("skc_id", "")).strip():
        errors.append("skc_id is required")
    canonical_source = data.get("canonical_identity_source")
    errors.extend(_validate_canonical_source(canonical_source, "canonical_identity_source"))
    identity_profile = data.get("identity_profile")
    if not isinstance(identity_profile, dict):
        errors.append("identity_profile must be an object")
    else:
        errors.extend(_validate_canonical_source(identity_profile.get("canonical_source"), "identity_profile.canonical_source"))
        if identity_profile.get("canonical_source") != canonical_source:
            errors.append("identity_profile.canonical_source must match canonical_identity_source")
        if identity_profile.get("head_visibility") not in HEAD_VISIBILITY:
            errors.append("identity_profile.head_visibility is invalid")
    garment_profile = data.get("garment_profile")
    if not isinstance(garment_profile, dict):
        errors.append("garment_profile must be an object")
    else:
        if garment_profile.get("hem_position") not in HEM_POSITIONS:
            errors.append("garment_profile.hem_position is invalid")
        expected_full_frame = (
            garment_profile.get("garment_type") == "dress"
            and garment_profile.get("hem_position") == "below_knee"
        )
        if garment_profile.get("requires_full_garment_frame") is not expected_full_frame:
            errors.append("garment_profile.requires_full_garment_frame contradicts garment type and hem")
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
    if data.get("schema_version") != 2:
        errors.append("schema_version must be 2")
    if data.get("view") not in VIEW_KEYS:
        errors.append("view must be front, side, back, or full")
    generation = data.get("generation", {})
    expected = {"model": "nano banana pro", "resolution": "4K", "aspect_ratio": "2:3"}
    for key, value in expected.items():
        if generation.get(key) != value:
            errors.append(f"generation.{key} must be {value}")
    if not str(data.get("analysis_markdown", "")).strip():
        errors.append("analysis_markdown is required")
    identity_contract = data.get("identity_contract")
    if not isinstance(identity_contract, dict):
        errors.append("identity_contract must be an object")
    else:
        if identity_contract.get("canonical_source") != CANONICAL_IDENTITY_PATH:
            errors.append(f"identity_contract.canonical_source must be {CANONICAL_IDENTITY_PATH}")
        if identity_contract.get("head_visibility") not in HEAD_VISIBILITY:
            errors.append("identity_contract.head_visibility is invalid")
    garment_contract = data.get("garment_contract")
    if not isinstance(garment_contract, dict):
        errors.append("garment_contract must be an object")
    else:
        if garment_contract.get("hem_position") not in HEM_POSITIONS:
            errors.append("garment_contract.hem_position is invalid")
        expected_full_frame = (
            garment_contract.get("garment_type") == "dress"
            and garment_contract.get("hem_position") == "below_knee"
        )
        if garment_contract.get("requires_full_garment_frame") is not expected_full_frame:
            errors.append("garment_contract.requires_full_garment_frame contradicts garment type and hem")
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
        if IDENTITY_MARKER not in prompt:
            errors.append(f"action {index}: prompt_en must contain {IDENTITY_MARKER}")
        if view in {"front", "side", "back"} and HEAD_CROP_MARKER not in prompt:
            errors.append(f"action {index}: prompt_en must contain {HEAD_CROP_MARKER}")
        if view == "full" and FULL_HEAD_MARKER not in prompt:
            errors.append(f"action {index}: prompt_en must contain {FULL_HEAD_MARKER}")
        if isinstance(garment_contract, dict) and garment_contract.get("requires_full_garment_frame") is True and GARMENT_FRAME_MARKER not in prompt:
            errors.append(f"action {index}: prompt_en must contain {GARMENT_FRAME_MARKER}")
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
