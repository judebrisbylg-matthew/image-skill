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
FINAL_CONTRACT_OVERRIDE = (
    "FINAL CONTRACT OVERRIDE: In any conflict, the following identity, head-crop, "
    "full-body, and garment contracts override every earlier sentence in this prompt."
)
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
IDENTITY_PROMPT_FIELDS = (
    "head_visibility",
    "skin_tone_and_visible_ancestry_cues",
    "visible_face_features",
    "hair_evidence",
    "age_impression",
    "body_profile",
)
IDENTITY_PROMPT_ASSIGNMENTS = ("canonical_source", *IDENTITY_PROMPT_FIELDS)
IDENTITY_BODY_PROFILE_GUARD = (
    "noncanonical local pose/composition sources must not control or override "
    "body_profile"
)
HEAD_CROP_REQUIREMENTS = (
    "The final image must retain at least half of the model's head",
    "A complete head is allowed",
    "Never crop below the half-head boundary",
)
FULL_HEAD_REQUIREMENTS = (
    (
        "Even when 正面/1.jpg shows a partial head or no head, reconstruct a natural "
        "complete head using only the visible skin tone, ancestry cues, partial "
        "facial evidence, hair evidence, age impression, neck/shoulder evidence, "
        "and body profile"
    ),
    "Do not change the model's visible identity characteristics",
)
GARMENT_FRAME_REQUIREMENTS = (
    "Activate only for a visually confirmed below-knee dress",
    (
        "when active, keep the dress continuously visible from the "
        "shoulder/neckline through the lowest hem point"
    ),
    "leave visible safety margin below the hem",
    "the hem must not touch or cross an image edge",
    "keep the major hem silhouette unobscured",
    "keep the apparent garment length unchanged",
)
PROMPT_MARKERS = (
    IDENTITY_MARKER,
    HEAD_CROP_MARKER,
    FULL_HEAD_MARKER,
    GARMENT_FRAME_MARKER,
)


def _is_canonical_nonblank_string(value: object) -> bool:
    return type(value) is str and bool(value) and value == value.strip()


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
    head_visibility = profile.get("head_visibility")
    if not _is_canonical_nonblank_string(head_visibility):
        errors.append(f"{field}.head_visibility must be a canonical nonblank string")
    elif head_visibility not in HEAD_VISIBILITY:
        errors.append(f"{field}.head_visibility is invalid")
    for evidence_field in IDENTITY_TEXT_FIELDS:
        value = profile.get(evidence_field)
        if not _is_canonical_nonblank_string(value):
            errors.append(
                f"{field}.{evidence_field} must be a canonical nonblank string"
            )
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
    if not _is_canonical_nonblank_string(garment_type):
        errors.append(f"{field}.garment_type must be a canonical nonblank string")
    hem_position = profile.get("hem_position")
    if not _is_canonical_nonblank_string(hem_position):
        errors.append(f"{field}.hem_position must be a canonical nonblank string")
    elif hem_position not in HEM_POSITIONS:
        errors.append(f"{field}.hem_position is invalid")
    reason = profile.get("reason")
    if not _is_canonical_nonblank_string(reason):
        errors.append(f"{field}.reason must be a canonical nonblank string")
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


def _marker_section(prompt: str, marker: str) -> str | None:
    if prompt.count(marker) != 1:
        return None
    start = prompt.index(marker) + len(marker)
    following = [
        prompt.find(candidate, start)
        for candidate in PROMPT_MARKERS
        if candidate != marker and prompt.find(candidate, start) >= 0
    ]
    end = min(following) if following else len(prompt)
    return prompt[start:end].strip()


def _parse_identity_assignments(section: str) -> tuple[dict[str, str], str | None]:
    """Parse the fixed-order identity lock without prefix or duplicate ambiguity."""
    assignments = {}
    cursor = 0
    for index, field in enumerate(IDENTITY_PROMPT_ASSIGNMENTS):
        prefix = f"{field}="
        if not section.startswith(prefix, cursor):
            return {}, f"expected {prefix} in fixed assignment order"
        value_start = cursor + len(prefix)
        if index + 1 < len(IDENTITY_PROMPT_ASSIGNMENTS):
            next_field = IDENTITY_PROMPT_ASSIGNMENTS[index + 1]
            boundary = re.search(
                rf";\s*(?={re.escape(next_field)}=)", section[value_start:]
            )
            if boundary is None:
                return {}, f"missing delimiter before {next_field}="
            value_end = value_start + boundary.start()
            cursor = value_start + boundary.end()
        else:
            guard = re.search(
                rf";\s*{re.escape(IDENTITY_BODY_PROFILE_GUARD)}\.?\s*$",
                section[value_start:],
                flags=re.IGNORECASE,
            )
            if guard is None:
                return {}, (
                    "missing exact guard: noncanonical local pose/composition sources "
                    "must not control or override body_profile"
                )
            value_end = value_start + guard.start()
            cursor = len(section)
        value = section[value_start:value_end].strip()
        if not value:
            return {}, f"{field} must have an exact nonblank value"
        assignments[field] = value
    if cursor != len(section):
        return {}, "unexpected text in identity lock"
    return assignments, None


def _validate_identity_lock(prompt: str, profile: object, action_index: int) -> list[str]:
    if prompt.count(IDENTITY_MARKER) != 1:
        return [
            f"action {action_index}: prompt_en must contain exactly one actionable "
            f"{IDENTITY_MARKER} section"
        ]
    section = _marker_section(prompt, IDENTITY_MARKER) or ""
    if not isinstance(profile, dict):
        return [f"action {action_index}: active identity_profile is unavailable"]
    expected = {"canonical_source": CANONICAL_IDENTITY_PATH}
    for field in IDENTITY_PROMPT_FIELDS:
        expected[field] = profile.get(field)
    assignments, parse_error = _parse_identity_assignments(section)
    mismatched = [
        field for field, expected_value in expected.items()
        if assignments.get(field) != expected_value
    ]
    if parse_error is None and not mismatched:
        return []
    details = []
    if parse_error:
        details.append(parse_error)
    if mismatched:
        details.append("mismatched fields: " + ", ".join(mismatched))
    return [
        f"action {action_index}: {IDENTITY_MARKER} must contain concrete active "
        "identity_profile assignments in fixed order and match the values exactly; "
        + "; ".join(details)
    ]


def _expected_identity_lock(profile: object) -> str | None:
    if not isinstance(profile, dict):
        return None
    values = [profile.get(field) for field in IDENTITY_PROMPT_FIELDS]
    if any(type(value) is not str for value in values):
        return None
    assignments = "; ".join(
        [f"canonical_source={CANONICAL_IDENTITY_PATH}"]
        + [f"{field}={profile[field]}" for field in IDENTITY_PROMPT_FIELDS]
    )
    return (
        f"{IDENTITY_MARKER} {assignments}; "
        "Noncanonical local pose/composition sources must not control or override "
        "body_profile."
    )


def _expected_final_contract_suffix(
    active_manifest: dict, view: object
) -> str | None:
    identity_lock = _expected_identity_lock(active_manifest.get("identity_profile"))
    if identity_lock is None or view not in VIEW_KEYS:
        return None
    if view == "full":
        framing_lock = (
            f"{FULL_HEAD_MARKER} Even when 正面/1.jpg shows a partial head or no "
            "head, reconstruct a natural complete head using only the visible skin "
            "tone, ancestry cues, partial facial evidence, hair evidence, age "
            "impression, neck/shoulder evidence, and body profile. Do not change "
            "the model's visible identity characteristics."
        )
    else:
        framing_lock = (
            f"{HEAD_CROP_MARKER} The final image must retain at least half of the "
            "model's head. A complete head is allowed. Never crop below the "
            "half-head boundary."
        )
    contracts = [FINAL_CONTRACT_OVERRIDE, identity_lock, framing_lock]
    garment_profile = active_manifest.get("garment_profile")
    if (
        isinstance(garment_profile, dict)
        and garment_profile.get("requires_full_garment_frame") is True
    ):
        contracts.append(
            f"{GARMENT_FRAME_MARKER} Activate only for a visually confirmed "
            "below-knee dress; when active, keep the dress continuously visible "
            "from the shoulder/neckline through the lowest hem point; leave visible "
            "safety margin below the hem; the hem must not touch or cross an image "
            "edge; keep the major hem silhouette unobscured; keep the apparent "
            "garment length unchanged."
        )
    return " ".join(contracts)


def _normalized_marker_clauses(section: str) -> list[str]:
    raw_clauses = re.split(r";|\.(?=\s|$)", section)
    return [
        " ".join(clause.strip().split()).casefold()
        for clause in raw_clauses
        if clause.strip()
    ]


def _validate_actionable_marker(
    prompt: str,
    marker: str,
    required_phrases: tuple[str, ...],
    action_index: int,
) -> list[str]:
    if prompt.count(marker) != 1:
        return [
            f"action {action_index}: prompt_en must contain exactly one actionable "
            f"{marker} section"
        ]
    clauses = _normalized_marker_clauses(_marker_section(prompt, marker) or "")
    missing = [
        phrase
        for phrase in required_phrases
        if clauses.count(" ".join(phrase.split()).casefold()) != 1
    ]
    if not missing:
        return []
    return [
        f"action {action_index}: {marker} section must be actionable and include: "
        + "; ".join(missing)
    ]


def _strict_json_equal(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            _strict_json_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _strict_json_equal(left_item, right_item)
            for left_item, right_item in zip(left, right)
        )
    return left == right


def _negative_prompt_conflicts(
    negative_prompt: str, *, view: object, require_full_garment_frame: bool
) -> bool:
    lowered = " ".join(negative_prompt.casefold().split())
    patterns = [
        r"\b(?:no|without)\s+(?:canonical\s+)?identity\b",
        r"\b(?:allow|permit)\s+(?:canonical\s+)?identity\s+drift\b",
        r"\bdo not\s+(?:preserve|match|keep|use)\s+(?:the\s+)?(?:canonical\s+)?identity\b",
        r"\b(?:no|without)\s+(?:the\s+)?(?:final contract override|identity lock|head crop floor|full-body head completion|garment frame lock|full-body framing|head-to-toe framing)\b",
        r"\b(?:ignore|disable|negate|override)\s+(?:the\s+)?(?:final contract override|identity lock|head crop floor|full-body head completion|garment frame lock)\b",
        r"\b(?:no|without)\s+(?:a\s+)?(?:complete|full|half)\s+head\b",
        r"\bwithout\s+at\s+least\s+half\s+(?:of\s+)?(?:the\s+model(?:'s)?\s+)?head\b",
        r"\bcrop\s+below\s+the\s+half-head\s+boundary\b",
        r"\b(?:hide|omit|remove|crop)\s+(?:the\s+)?(?:complete|full|half)?\s*head\b",
        r"\bdo not\s+(?:retain|keep|show|reconstruct)\s+(?:at least\s+half|a\s+complete|the\s+full)?\s*(?:of\s+the\s+model(?:'s)?\s+)?head\b",
    ]
    if require_full_garment_frame:
        patterns.extend(
            (
                r"\b(?:no|without)\s+(?:the\s+)?full\s+(?:garment|dress)\b",
                r"\b(?:hide|omit|remove|crop)\s+(?:the\s+)?(?:garment|dress|hem)\b",
                r"\bdo not\s+(?:keep|show|preserve)\s+(?:the\s+)?full\s+(?:garment|dress)\b",
            )
        )
    if view == "full":
        patterns.extend(
            (
                r"\b(?:no|without)\s+(?:the\s+)?(?:shoes?|soles?)\b",
                r"\b(?:hide|omit|remove|crop)\s+(?:the\s+)?(?:shoes?|soles?)\b",
                r"\bdo not\s+(?:show|include|keep)\s+(?:the\s+)?(?:shoes?|soles?)\b",
            )
        )
    return any(re.search(pattern, lowered) for pattern in patterns)


def validate_manifest_data(data: object) -> list[str]:
    if not isinstance(data, dict):
        return ["manifest must be an object"]
    errors = []
    if data.get("schema_version") != 2:
        errors.append("schema_version must be 2")
    if not _is_canonical_nonblank_string(data.get("skc_id")):
        errors.append("skc_id must be a canonical nonblank string")
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
    if type(views) is not dict:
        return errors + ["views must be an object containing exactly front, side, back, and full"]
    if set(views) != VIEW_KEYS:
        errors.append("views must contain exactly front, side, back, and full")
    for view_key, view in views.items():
        if view_key not in VIEW_KEYS:
            errors.append(f"unknown view: {view_key}")
            continue
        if not isinstance(view, dict):
            errors.append(f"{view_key}: view must be an object")
            continue
        files = view.get("files")
        file_paths = set()
        if type(files) is not list:
            errors.append(f"{view_key}: files must be a list")
        else:
            for index, item in enumerate(files, start=1):
                if type(item) is not dict:
                    errors.append(f"{view_key}: file {index} must be an object")
                    continue
                relative_path = item.get("relative_path")
                if not _is_canonical_nonblank_string(relative_path):
                    errors.append(
                        f"{view_key}: file {index} relative_path must be a canonical nonblank string"
                    )
                    continue
                if relative_path in file_paths:
                    errors.append(f"{view_key}: duplicate file relative_path {relative_path}")
                file_paths.add(relative_path)
        roles = view.get("roles")
        if type(roles) is not dict:
            errors.append(f"{view_key}: roles must be an object")
            continue
        unknown_roles = set(roles) - ROLE_KEYS
        if unknown_roles:
            errors.append(f"{view_key}: unknown roles: {', '.join(sorted(unknown_roles))}")
        valid_roles = True
        for role, values in roles.items():
            if type(values) is not list:
                errors.append(f"{view_key}: role {role} must be a list")
                valid_roles = False
                continue
            for path in values:
                if not _is_canonical_nonblank_string(path):
                    errors.append(
                        f"{view_key}: role {role} paths must be canonical nonblank strings"
                    )
                elif path not in file_paths:
                    errors.append(
                        f"{view_key}: role {role} path {path} must exist in files"
                    )
        if view.get("status") == "ready":
            for role in REQUIRED_ROLES:
                values = roles.get(role, [])
                if type(values) is not list:
                    if valid_roles:
                        errors.append(f"{view_key}: role {role} must be a list")
                elif not values:
                    errors.append(f"{view_key}: missing required role {role}")
                elif len(values) != 1:
                    errors.append(f"{view_key}: required role {role} must contain exactly one source")
            if not roles.get("composition_source"):
                errors.append(f"{view_key}: missing composition_source or model fallback")
    return errors


def validate_prompt_data(data: object, active_manifest: object) -> list[str]:
    if not isinstance(active_manifest, dict):
        errors = ["active manifest must be an object"]
    else:
        manifest_errors = validate_manifest_data(active_manifest)
        errors = [f"active manifest: {error}" for error in manifest_errors]
    if not isinstance(data, dict):
        return errors + ["prompt must be an object"]
    if not isinstance(active_manifest, dict):
        return errors
    if data.get("schema_version") != 2:
        errors.append("schema_version must be 2")
    prompt_skc_id = data.get("skc_id")
    if not _is_canonical_nonblank_string(prompt_skc_id):
        errors.append("skc_id must be a canonical nonblank string")
    elif prompt_skc_id != active_manifest.get("skc_id"):
        errors.append("skc_id must match the active manifest exactly")
    prompt_view = data.get("view")
    if type(prompt_view) is not str or prompt_view not in VIEW_KEYS:
        errors.append("view must be front, side, back, or full")
    else:
        manifest_views = active_manifest.get("views")
        manifest_view = (
            manifest_views.get(prompt_view) if isinstance(manifest_views, dict) else None
        )
        if not isinstance(manifest_view, dict) or manifest_view.get("status") != "ready":
            errors.append("view must exist and be ready in the active manifest")
    generation = data.get("generation", {})
    if not isinstance(generation, dict):
        errors.append("generation must be an object")
        generation = {}
    expected = {"model": "nano banana pro", "resolution": "4K", "aspect_ratio": "2:3"}
    for key, value in expected.items():
        if generation.get(key) != value:
            errors.append(f"generation.{key} must be {value}")
    if type(data.get("analysis_markdown")) is not str or not data["analysis_markdown"].strip():
        errors.append("analysis_markdown must be a nonblank string")
    identity_contract = data.get("identity_contract")
    if not isinstance(identity_contract, dict):
        errors.append("identity_contract must be an object")
    else:
        errors.extend(_validate_identity_profile(identity_contract, "identity_contract"))
        if not _strict_json_equal(
            identity_contract, active_manifest.get("identity_profile")
        ):
            errors.append(
                "identity_contract must match the active manifest identity_profile exactly"
            )
    garment_contract = data.get("garment_contract")
    if not isinstance(garment_contract, dict):
        errors.append("garment_contract must be an object")
    else:
        errors.extend(_validate_garment_profile(garment_contract, "garment_contract"))
        if not _strict_json_equal(
            garment_contract, active_manifest.get("garment_profile")
        ):
            errors.append(
                "garment_contract must match the active manifest garment_profile exactly"
            )
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
            value = action.get(field)
            if type(value) is not str or not value.strip():
                errors.append(f"action {index}: {field} is required")
        prompt = str(action.get("prompt_en", ""))
        negative_prompt = action.get("negative_prompt")
        if type(negative_prompt) is str and negative_prompt.strip():
            garment_profile = active_manifest.get("garment_profile")
            full_garment = (
                isinstance(garment_profile, dict)
                and garment_profile.get("requires_full_garment_frame") is True
            )
            if _negative_prompt_conflicts(
                negative_prompt, view=view, require_full_garment_frame=full_garment
            ):
                errors.append(
                    f"action {index}: negative_prompt must not negate active hard locks"
                )
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
        errors.extend(
            _validate_identity_lock(
                prompt,
                active_manifest.get("identity_profile"),
                index,
            )
        )
        if view in {"front", "side", "back"}:
            errors.extend(
                _validate_actionable_marker(
                    prompt,
                    HEAD_CROP_MARKER,
                    HEAD_CROP_REQUIREMENTS,
                    index,
                )
            )
        if view == "full":
            errors.extend(
                _validate_actionable_marker(
                    prompt,
                    FULL_HEAD_MARKER,
                    FULL_HEAD_REQUIREMENTS,
                    index,
                )
            )
        active_garment_profile = active_manifest.get("garment_profile")
        full_garment_frame = (
            isinstance(active_garment_profile, dict)
            and active_garment_profile.get("requires_full_garment_frame") is True
        )
        if full_garment_frame:
            errors.extend(
                _validate_actionable_marker(
                    prompt,
                    GARMENT_FRAME_MARKER,
                    GARMENT_FRAME_REQUIREMENTS,
                    index,
                )
            )
        elif GARMENT_FRAME_MARKER in prompt:
            errors.append(
                f"action {index}: {GARMENT_FRAME_MARKER} is forbidden when the active "
                "garment contract does not require a full garment frame"
            )
        expected_suffix = _expected_final_contract_suffix(active_manifest, view)
        if expected_suffix is None or not prompt.rstrip().endswith(expected_suffix):
            errors.append(
                f"action {index}: prompt_en must end with the manifest-derived "
                "FINAL CONTRACT OVERRIDE block"
            )
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
