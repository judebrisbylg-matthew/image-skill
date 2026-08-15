#!/usr/bin/env python3
"""Validate manifest and prompt JSON contracts."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import re
from pathlib import Path


_NEGATIVE_PROMPT_SPEC = importlib.util.spec_from_file_location(
    "fashion_lovart_view_extension_negative_prompt",
    Path(__file__).with_name("negative_prompt.py"),
)
if _NEGATIVE_PROMPT_SPEC is None or _NEGATIVE_PROMPT_SPEC.loader is None:
    raise RuntimeError("could not load negative_prompt.py")
_negative_prompt_module = importlib.util.module_from_spec(_NEGATIVE_PROMPT_SPEC)
_NEGATIVE_PROMPT_SPEC.loader.exec_module(_negative_prompt_module)
render_negative_prompt = _negative_prompt_module.render_negative_prompt
view_contract_from_manifest = _negative_prompt_module.view_contract_from_manifest


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
FILE_ROLES = ROLE_KEYS | {"unclassified"}
SOURCE_BINDING_KEYS = {"identity", "product", "scene", "pose_composition"}
ACTION_DIRECTIVE_KEYS = {"action", "camera", "composition", "scene"}
CORRECTION_KEYS = {"fix", "preserve"}


def _is_canonical_nonblank_string(value: object) -> bool:
    return type(value) is str and bool(value) and value == value.strip()


def _validate_canonical_source(source: object, field: str) -> list[str]:
    if type(source) is not dict:
        return [f"{field} must be an object"]
    errors = []
    if source.get("relative_path") != CANONICAL_IDENTITY_PATH:
        errors.append(f"{field}.relative_path must be {CANONICAL_IDENTITY_PATH}")
    sha256 = source.get("sha256")
    if type(sha256) is not str or re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
        errors.append(f"{field}.sha256 must be a canonical lowercase SHA-256 string")
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


def _strict_positive_int(value: object) -> bool:
    return type(value) is int and value >= 1


def _scanner_binding(view: dict, relative_path: str, field: str) -> dict:
    files = view.get("files")
    if type(files) is not list:
        raise ValueError(f"{field} cannot resolve without scanner file records")
    matches = [
        item
        for item in files
        if type(item) is dict and item.get("relative_path") == relative_path
    ]
    if len(matches) != 1:
        raise ValueError(f"{field} must resolve to exactly one scanner file record")
    sha256 = matches[0].get("sha256")
    if type(sha256) is not str or re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
        raise ValueError(f"{field} scanner file record has invalid sha256")
    return {"relative_path": relative_path, "sha256": sha256}


def _one_role_path(view: dict, role: str) -> str:
    roles = view.get("roles")
    values = roles.get(role) if type(roles) is dict else None
    if type(values) is not list or len(values) != 1:
        raise ValueError(f"{role} must contain exactly one scanner-backed source")
    path = values[0]
    if not _is_canonical_nonblank_string(path):
        raise ValueError(f"{role} must contain one canonical relative path")
    return path


def _expected_source_bindings(active_manifest: dict, view_key: str) -> dict:
    views = active_manifest.get("views")
    view = views.get(view_key) if type(views) is dict else None
    if type(view) is not dict:
        raise ValueError("active view is unavailable")
    canonical = active_manifest.get("canonical_identity_source")
    if _validate_canonical_source(canonical, "canonical_identity_source"):
        raise ValueError("canonical identity source is invalid")
    bindings = {
        "identity": dict(canonical),
        "product": _scanner_binding(
            view,
            _one_role_path(view, "product_source"),
            "product source",
        ),
        "scene": _scanner_binding(
            view,
            _one_role_path(view, "scene_source"),
            "scene source",
        ),
        "pose_composition": _scanner_binding(
            view,
            _one_role_path(view, "composition_source"),
            "pose/composition source",
        ),
    }
    footwear = view.get("footwear_contract")
    if footwear is not None:
        if type(footwear) is not dict or type(footwear.get("source_paths")) is not list:
            raise ValueError("footwear_contract is invalid")
        bindings["footwear"] = [
            _scanner_binding(view, path, "footwear source")
            for path in footwear["source_paths"]
        ]
    return bindings


def _validate_action_metadata(
    skc_id: object,
    view: object,
    action: object,
    active_manifest: object,
) -> list[str]:
    if type(action) is not dict:
        return ["action must be an object"]
    errors = []
    action_id = action.get("action_id")
    if not _is_canonical_nonblank_string(action_id):
        errors.append("action_id must be a canonical nonblank string")
    attempt = action.get("attempt")
    if not _strict_positive_int(attempt):
        errors.append("attempt must be a strict positive JSON integer")
    bindings = action.get("source_bindings")
    if type(bindings) is not dict:
        errors.append("source_bindings must be an object")
    elif type(active_manifest) is dict and view in VIEW_KEYS:
        try:
            expected_bindings = _expected_source_bindings(active_manifest, view)
        except ValueError as exc:
            errors.append(f"active source bindings are invalid: {exc}")
        else:
            if not _strict_json_equal(bindings, expected_bindings):
                errors.append(
                    "source_bindings must match the active scanner path/hash records exactly"
                )
    directives = action.get("action_directives")
    if type(directives) is not dict or set(directives) != ACTION_DIRECTIVE_KEYS:
        errors.append(
            "action_directives must contain exactly action, camera, composition, and scene"
        )
    else:
        for field in ("action", "camera", "composition", "scene"):
            value = directives[field]
            if not _is_canonical_nonblank_string(value) or not any(
                character.isascii() and character.isalpha() for character in value
            ):
                errors.append(
                    f"action_directives.{field} must be canonical nonblank English prose"
                )
    correction = action.get("correction")
    if attempt == 1:
        if correction is not None:
            errors.append("attempt 1 correction must be null")
    elif _strict_positive_int(attempt):
        if type(correction) is not dict or set(correction) != CORRECTION_KEYS:
            errors.append(
                "retry correction must contain exactly fix and preserve"
            )
        else:
            for field in ("fix", "preserve"):
                value = correction[field]
                if not _is_canonical_nonblank_string(value) or not any(
                    character.isascii() and character.isalpha() for character in value
                ):
                    errors.append(
                        f"correction.{field} must be canonical nonblank English prose"
                    )
    return errors


def render_positive_prompt(
    skc_id: str,
    view: str,
    action: dict,
    active_manifest: dict,
) -> str:
    """Render the only executable positive prompt accepted by the validator."""
    if not _is_canonical_nonblank_string(skc_id):
        raise ValueError("skc_id must be a canonical nonblank string")
    if view not in VIEW_KEYS:
        raise ValueError("view must be front, side, back, or full")
    manifest_errors = validate_manifest_data(active_manifest)
    if manifest_errors:
        raise ValueError(
            "active manifest is invalid: " + "; ".join(manifest_errors)
        )
    metadata_errors = _validate_action_metadata(skc_id, view, action, active_manifest)
    if metadata_errors:
        raise ValueError("; ".join(metadata_errors))
    suffix = _expected_final_contract_suffix(active_manifest, view)
    if suffix is None:
        raise ValueError("manifest-derived terminal contract is unavailable")
    bindings = action["source_bindings"]
    directives = action["action_directives"]
    parts = [
        (
            f"SKC {skc_id} | VIEW {view} | ACTION {action['action_id']} | "
            f"ATTEMPT {action['attempt']}."
        ),
        (
            "IDENTITY MODEL SOURCE: "
            f"path={bindings['identity']['relative_path']}; "
            f"sha256={bindings['identity']['sha256']}."
        ),
        (
            "PRODUCT SOURCE: "
            f"path={bindings['product']['relative_path']}; "
            f"sha256={bindings['product']['sha256']}."
        ),
        (
            "SCENE SOURCE: "
            f"path={bindings['scene']['relative_path']}; "
            f"sha256={bindings['scene']['sha256']}."
        ),
        (
            "POSE/COMPOSITION SOURCE: "
            f"path={bindings['pose_composition']['relative_path']}; "
            f"sha256={bindings['pose_composition']['sha256']}."
        ),
    ]
    if "footwear" in bindings:
        rendered_sources = ", ".join(
            f"path={item['relative_path']}; sha256={item['sha256']}"
            for item in bindings["footwear"]
        )
        parts.append(
            "FOOTWEAR SOURCE: "
            + rendered_sources
            + ". Preserve only this explicitly validated footwear evidence."
        )
    parts.extend(
        (
            f"ACTION: {directives['action']}.",
            f"CAMERA: {directives['camera']}.",
            f"COMPOSITION: {directives['composition']}.",
            f"SCENE: {directives['scene']}.",
        )
    )
    correction = action.get("correction")
    if correction is not None:
        parts.append(
            f"CORRECTION FOR ATTEMPT {action['attempt']}: "
            f"Fix only: {correction['fix']}. Preserve: {correction['preserve']}."
        )
    parts.extend(("Generate with Nano Banana Pro, 4K, 2:3.", suffix))
    return " ".join(parts)


def _retry_state_errors(
    action: dict,
    active_run_state: object,
    skc_id: str,
    view: str,
) -> list[str]:
    attempt = action.get("attempt")
    if not _strict_positive_int(attempt) or attempt == 1:
        return []
    if type(active_run_state) is not dict:
        return ["retry prompt requires an active run-state"]
    if active_run_state.get("skc_id") != skc_id:
        return ["active run-state skc_id must match the prompt exactly"]
    views = active_run_state.get("views")
    run_view = views.get(view) if type(views) is dict else None
    actions = run_view.get("actions") if type(run_view) is dict else None
    run_action = actions.get(action.get("action_id")) if type(actions) is dict else None
    if type(run_action) is not dict:
        return ["retry action must exist in the active run-state"]
    attempts = run_action.get("attempts")
    if type(attempts) is not int or isinstance(attempts, bool):
        return ["active run-state attempts must be a strict JSON integer"]
    attempt_history = run_action.get("attempt_history")
    if type(attempt_history) is not list:
        return ["active run-state attempt_history must be a list"]
    expected_label = (
        f"SKC {skc_id} | VIEW {view} | ACTION {action['action_id']} | "
        f"ATTEMPT {attempt}"
    )
    ready_for_retry = attempts == attempt - 1 and run_action.get("status") == "rejected"
    recorded_attempt = attempts == attempt and any(
        type(item) is dict
        and item.get("attempt") == attempt
        and item.get("task_label") == expected_label
        for item in attempt_history
    )
    if not ready_for_retry and not recorded_attempt:
        return [
            f"ATTEMPT {attempt} is inconsistent with the active run-state"
        ]
    return []


def _validate_view_scanner_evidence(view_key: str, view: dict) -> list[str]:
    errors = []
    files = view.get("files")
    if type(files) is not list:
        return [f"{view_key}: files must be a list of scanner records"]
    records = {}
    for index, item in enumerate(files, start=1):
        if type(item) is not dict:
            errors.append(f"{view_key}: file {index} must be a scanner record object")
            continue
        path = item.get("relative_path")
        if not _is_canonical_nonblank_string(path):
            continue
        if path in records:
            continue
        records[path] = item
        sha256 = item.get("sha256")
        if type(sha256) is not str or re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
            errors.append(
                f"{view_key}: scanner record {path} must contain canonical lowercase sha256"
            )
        role = item.get("role")
        if role not in FILE_ROLES:
            errors.append(f"{view_key}: scanner record {path} has invalid role")
            continue
        confidence = item.get("confidence")
        reason = item.get("reason")
        if role == "unclassified":
            if confidence is not None or reason != "":
                errors.append(
                    f"{view_key}: unclassified scanner record {path} must keep null confidence and blank reason"
                )
            if view.get("status") == "ready":
                errors.append(f"{view_key}: ready view cannot contain unclassified record {path}")
        else:
            if (
                isinstance(confidence, bool)
                or not isinstance(confidence, (int, float))
                or not math.isfinite(confidence)
                or not 0 <= confidence <= 1
            ):
                errors.append(
                    f"{view_key}: scanner record {path} confidence must be a finite number from 0 to 1"
                )
            elif view.get("status") == "ready" and confidence < 0.7:
                errors.append(
                    f"{view_key}: ready scanner record {path} confidence must be at least 0.7"
                )
            if not _is_canonical_nonblank_string(reason):
                errors.append(
                    f"{view_key}: scanner record {path} reason must be canonical nonblank text"
                )

    roles = view.get("roles")
    if type(roles) is not dict:
        return errors
    memberships = {path: [] for path in records}
    for role, paths in roles.items():
        if role not in ROLE_KEYS or type(paths) is not list:
            continue
        for path in paths:
            if path in memberships:
                memberships[path].append(role)

    fallback = view.get("composition_fallback")
    if fallback not in {None, "model_source"}:
        errors.append(f"{view_key}: composition_fallback must be null or model_source")
    model_paths = roles.get("model_source", [])
    composition_paths = roles.get("composition_source", [])
    if fallback == "model_source" and composition_paths != model_paths:
        errors.append(
            f"{view_key}: model_source composition fallback must exactly reuse model_source"
        )
    if fallback is None and composition_paths:
        for path in composition_paths:
            record = records.get(path)
            if type(record) is dict and record.get("role") != "composition_source":
                errors.append(
                    f"{view_key}: composition source {path} must have primary role composition_source"
                )

    for path, record in records.items():
        role = record.get("role")
        memberships_for_path = memberships[path]
        if role not in FILE_ROLES:
            continue
        if role == "unclassified":
            if memberships_for_path:
                errors.append(
                    f"{view_key}: unclassified record {path} cannot appear in role lists"
                )
            continue
        allowed = [role]
        if role == "model_source" and fallback == "model_source":
            allowed.append("composition_source")
        if (
            len(memberships_for_path) != len(allowed)
            or set(memberships_for_path) != set(allowed)
        ):
            errors.append(
                f"{view_key}: scanner record {path} role evidence must equal {', '.join(allowed)}"
            )

    if view.get("status") == "ready":
        for role in (*REQUIRED_ROLES, "composition_source"):
            paths = roles.get(role)
            if type(paths) is not list or len(paths) != 1:
                errors.append(
                    f"{view_key}: ready role {role} must contain exactly one source"
                )
        for path, path_roles in memberships.items():
            if len(path_roles) > 1 and not (
                fallback == "model_source"
                and len(path_roles) == 2
                and set(path_roles) == {"model_source", "composition_source"}
            ):
                errors.append(
                    f"{view_key}: illegal primary role overlap for {path}"
                )
    return errors


def validate_manifest_data(data: object) -> list[str]:
    if not isinstance(data, dict):
        return ["manifest must be an object"]
    errors = []
    if type(data.get("schema_version")) is not int or data.get("schema_version") != 2:
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
        errors.extend(_validate_view_scanner_evidence(view_key, view))
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
        try:
            view_contract_from_manifest(view_key, view)
        except ValueError as exc:
            errors.append(f"{view_key}: {exc}")
    front = views.get("front")
    front_files = front.get("files") if type(front) is dict else None
    canonical_records = (
        [
            item
            for item in front_files
            if type(item) is dict
            and item.get("relative_path") == CANONICAL_IDENTITY_PATH
        ]
        if type(front_files) is list
        else []
    )
    if len(canonical_records) != 1:
        errors.append(
            "canonical_identity_source must resolve to exactly one front scanner record"
        )
    elif type(canonical_source) is dict and canonical_source.get("sha256") != canonical_records[0].get("sha256"):
        errors.append(
            "canonical_identity_source.sha256 must match the front scanner record"
        )
    return errors


def validate_prompt_data(
    data: object,
    active_manifest: object,
    active_run_state: object = None,
) -> list[str]:
    if not isinstance(active_manifest, dict):
        manifest_errors = []
        errors = ["active manifest must be an object"]
    else:
        manifest_errors = validate_manifest_data(active_manifest)
        errors = [f"active manifest: {error}" for error in manifest_errors]
    if not isinstance(data, dict):
        return errors + ["prompt must be an object"]
    if not isinstance(active_manifest, dict):
        return errors
    if type(data.get("schema_version")) is not int or data.get("schema_version") != 2:
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
    expected_negative_prompt = None
    if not manifest_errors and view in VIEW_KEYS:
        manifest_views = active_manifest.get("views")
        active_view = (
            manifest_views.get(view) if isinstance(manifest_views, dict) else None
        )
        try:
            view_contract = view_contract_from_manifest(view, active_view)
            expected_negative_prompt = render_negative_prompt(
                view_contract,
                active_manifest.get("identity_profile"),
                active_manifest.get("garment_profile"),
            )
        except ValueError as exc:
            errors.append(f"active manifest negative prompt contract is invalid: {exc}")
    for index, action in enumerate(actions, start=1):
        if not isinstance(action, dict):
            errors.append(f"action {index} must be an object")
            continue
        action_id_value = action.get("action_id")
        action_id = action_id_value if _is_canonical_nonblank_string(action_id_value) else ""
        ids.append(action_id)
        for field in ("action_id", "title", "prompt_en", "negative_prompt"):
            value = action.get(field)
            if type(value) is not str or not value.strip():
                errors.append(f"action {index}: {field} is required")
        prompt = str(action.get("prompt_en", ""))
        negative_prompt = action.get("negative_prompt")
        if (
            type(negative_prompt) is str
            and expected_negative_prompt is not None
            and negative_prompt != expected_negative_prompt
        ):
            errors.append(
                f"action {index}: negative_prompt must match render_negative_prompt "
                "output exactly"
            )
        if prompt and not any(ch.isascii() and ch.isalpha() for ch in prompt):
            errors.append(f"action {index}: prompt_en must contain English text")
        metadata_errors = _validate_action_metadata(
            data.get("skc_id"), view, action, active_manifest
        )
        errors.extend(
            f"action {index}: {error}" for error in metadata_errors
        )
        errors.extend(
            f"action {index}: {error}"
            for error in _retry_state_errors(
                action,
                active_run_state,
                data.get("skc_id"),
                view,
            )
        )
        if not metadata_errors and not manifest_errors:
            try:
                expected_positive_prompt = render_positive_prompt(
                    data.get("skc_id"), view, action, active_manifest
                )
            except ValueError as exc:
                errors.append(
                    f"action {index}: positive prompt contract is invalid: {exc}"
                )
            else:
                if prompt != expected_positive_prompt:
                    errors.append(
                        f"action {index}: prompt_en must match render_positive_prompt output exactly"
                    )
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
    directive_actions = [
        action.get("action_directives", {}).get("action")
        for action in actions
        if type(action) is dict
        and type(action.get("action_directives")) is dict
        and type(action["action_directives"].get("action")) is str
    ]
    normalized_actions = [
        " ".join(value.split()).casefold() for value in directive_actions
    ]
    if len(normalized_actions) != 5 or len(set(normalized_actions)) != 5:
        errors.append(
            "the five actions must have five distinct action_directives.action values"
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("manifest", "prompt"))
    parser.add_argument("path", type=Path)
    parser.add_argument("active_manifest", type=Path, nargs="?")
    parser.add_argument("active_run_state", type=Path, nargs="?")
    args = parser.parse_args()
    if args.kind == "prompt" and args.active_manifest is None:
        parser.error("prompt validation requires an active manifest argument")
    if args.kind == "manifest" and (
        args.active_manifest is not None or args.active_run_state is not None
    ):
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
        active_run_state = None
        if args.active_run_state is not None:
            try:
                active_run_state = json.loads(
                    args.active_run_state.read_text(encoding="utf-8")
                )
            except (OSError, json.JSONDecodeError) as exc:
                print(f"invalid active run-state JSON: {exc}")
                return 2
        errors = validate_prompt_data(
            data,
            active_manifest,
            active_run_state=active_run_state,
        )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"OK: valid {args.kind}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
