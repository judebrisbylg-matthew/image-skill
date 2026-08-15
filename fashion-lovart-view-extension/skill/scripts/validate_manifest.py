#!/usr/bin/env python3
"""Validate manifest and prompt JSON contracts."""

from __future__ import annotations

import argparse
import json
import math
import re
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
IDENTITY_TEXT_FIELDS = (
    "skin_tone_and_visible_ancestry_cues",
    "visible_face_features",
    "hair_evidence",
    "age_impression",
    "body_profile",
    "reason",
)
GARMENT_FIELDS = (
    "garment_type",
    "hem_position",
    "requires_full_garment_frame",
    "reason",
)


def _validate_canonical_source(source: object, field: str) -> list[str]:
    if not isinstance(source, dict):
        return [f"{field} must be an object"]
    errors = []
    if source.get("relative_path") != CANONICAL_IDENTITY_PATH:
        errors.append(f"{field}.relative_path must be {CANONICAL_IDENTITY_PATH}")
    sha256 = source.get("sha256")
    if not isinstance(sha256, str) or re.fullmatch(r"[0-9a-fA-F]{64}", sha256) is None:
        errors.append(f"{field}.sha256 must be a 64-character hexadecimal string")
    return errors


def _validate_identity_profile(profile: object, field: str) -> list[str]:
    if not isinstance(profile, dict):
        return [f"{field} must be an object"]
    errors = _validate_canonical_source(
        profile.get("canonical_source"), f"{field}.canonical_source"
    )
    if profile.get("head_visibility") not in HEAD_VISIBILITY:
        errors.append(f"{field}.head_visibility is invalid")
    for evidence_field in IDENTITY_TEXT_FIELDS:
        value = profile.get(evidence_field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field}.{evidence_field} must be a nonblank string")
    confidence = profile.get("confidence")
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
        or not math.isfinite(confidence)
        or not 0 <= confidence <= 1
    ):
        errors.append(f"{field}.confidence must be a number from 0 to 1")
    return errors


def _validate_garment_profile(profile: object, field: str) -> list[str]:
    if not isinstance(profile, dict):
        return [f"{field} must be an object"]
    errors = []
    for required_field in GARMENT_FIELDS:
        if required_field not in profile:
            errors.append(f"{field}.{required_field} is required")
    garment_type = profile.get("garment_type")
    if not isinstance(garment_type, str) or not garment_type.strip():
        errors.append(f"{field}.garment_type must be a nonblank string")
    hem_position = profile.get("hem_position")
    if hem_position not in HEM_POSITIONS:
        errors.append(f"{field}.hem_position is invalid")
    reason = profile.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        errors.append(f"{field}.reason must be a nonblank string")
    full_frame = profile.get("requires_full_garment_frame")
    if not isinstance(full_frame, bool):
        errors.append(f"{field}.requires_full_garment_frame must be boolean")
    if hem_position == "below_knee" and garment_type != "dress":
        errors.append(f"{field}.hem_position below_knee is valid only for garment_type dress")
    expected_full_frame = garment_type == "dress" and hem_position == "below_knee"
    if isinstance(full_frame, bool) and full_frame is not expected_full_frame:
        errors.append(
            f"{field}.requires_full_garment_frame contradicts garment type and hem"
        )
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
    errors.extend(_validate_identity_profile(identity_profile, "identity_profile"))
    if isinstance(identity_profile, dict):
        if identity_profile.get("canonical_source") != canonical_source:
            errors.append("identity_profile.canonical_source must match canonical_identity_source")
    garment_profile = data.get("garment_profile")
    errors.extend(_validate_garment_profile(garment_profile, "garment_profile"))
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


def validate_prompt_data(data: dict, active_manifest: dict) -> list[str]:
    manifest_errors = validate_manifest_data(active_manifest)
    errors = [f"active manifest: {error}" for error in manifest_errors]
    if data.get("schema_version") != 2:
        errors.append("schema_version must be 2")
    if data.get("skc_id") != active_manifest.get("skc_id"):
        errors.append("skc_id must match the active manifest exactly")
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
    elif identity_contract != active_manifest.get("identity_profile"):
        errors.append("identity_contract must match the active manifest identity_profile exactly")
    garment_contract = data.get("garment_contract")
    if not isinstance(garment_contract, dict):
        errors.append("garment_contract must be an object")
    elif garment_contract != active_manifest.get("garment_profile"):
        errors.append("garment_contract must match the active manifest garment_profile exactly")
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
    parser.add_argument("active_manifest", type=Path, nargs="?")
    args = parser.parse_args()
    if args.kind == "prompt" and args.active_manifest is None:
        parser.error("prompt validation requires an active manifest argument")
    if args.kind == "manifest" and args.active_manifest is not None:
        parser.error("manifest validation accepts only one JSON path")
    try:
        data = json.loads(args.path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"invalid JSON: {exc}")
        return 2
    if args.kind == "manifest":
        errors = validate_manifest_data(data)
    else:
        try:
            active_manifest = json.loads(args.active_manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"invalid active manifest JSON: {exc}")
            return 2
        errors = validate_prompt_data(data, active_manifest)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"OK: valid {args.kind}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
