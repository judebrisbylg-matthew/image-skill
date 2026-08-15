#!/usr/bin/env python3
"""Render the immutable negative-prompt contract for one validated view."""

from __future__ import annotations

import math
import re


NEGATIVE_PROMPT_PREFIX = (
    "NEGATIVE PROMPT CONTRACT — reject only these defects: "
)
VIEW_NAMES = {"front", "side", "back", "full"}
HEAD_VISIBILITY = {"full", "partial", "absent"}
HEM_POSITIONS = {"above_knee", "at_knee", "below_knee", "not_applicable"}
CANONICAL_IDENTITY_PATH = "正面/1.jpg"

SHARED_DEFECTS = (
    "collage/multiple panels",
    "multiple people",
    "text",
    "watermark",
    "logo-like marks",
    "distorted anatomy/hands",
    "pasted-on/cutout/halo/edge glow",
    "mismatched lighting/color temperature/shadows",
    "wrong scene",
    "wrong product identity",
    "wrong garment color/neckline/sleeves/length/material",
    "identity drift",
    "ethnicity/visible-ancestry drift",
    "skin-tone drift",
    "age drift",
    "hair drift",
    "body-profile drift",
    "phone/selfie behavior",
    "bag on ground",
    "military stance",
    "both hands hanging straight down",
)
FULL_VIEW_DEFECTS = (
    "any crop of hair crown/head/face/chin/neck/body/garment hem/ankles/feet/toes/shoes/soles",
    "missing safety margin above hair or below footwear",
    "wrong requested full view",
)
LONG_DRESS_DEFECTS = (
    "cropped/obscured hem",
    "hem touching/crossing an image edge",
    "shortened apparent garment length",
    "interrupted shoulder-to-lowest-hem continuity",
)
FOOTWEAR_DEFECT = (
    "invented/changed/missing/cropped/obscured required footwear"
)
IDENTITY_TEXT_FIELDS = (
    "skin_tone_and_visible_ancestry_cues",
    "visible_face_features",
    "hair_evidence",
    "age_impression",
    "body_profile",
    "reason",
)
FOOTWEAR_CONTRACT_FIELDS = {
    "kind",
    "source_paths",
    "confidence",
    "reason",
}


def _is_canonical_nonblank_string(value: object) -> bool:
    return type(value) is str and bool(value) and value == value.strip()


def _validate_view(view: object) -> tuple[str, bool]:
    if type(view) is str:
        name = view
        footwear_required = False
    elif type(view) is dict and set(view) == {"name", "footwear_required"}:
        name = view["name"]
        footwear_required = view["footwear_required"]
        if not isinstance(footwear_required, bool):
            raise ValueError("view.footwear_required must be boolean")
    else:
        raise ValueError(
            "view must be a supported view name or an exact name/footwear_required contract"
        )
    if type(name) is not str or name not in VIEW_NAMES:
        raise ValueError("view name must be front, side, back, or full")
    return name, footwear_required


def _validate_identity_contract(contract: object) -> None:
    if not isinstance(contract, dict):
        raise ValueError("identity_contract must be an object")
    source = contract.get("canonical_source")
    if not isinstance(source, dict):
        raise ValueError("identity_contract.canonical_source must be an object")
    if source.get("relative_path") != CANONICAL_IDENTITY_PATH:
        raise ValueError(
            f"identity_contract.canonical_source.relative_path must be {CANONICAL_IDENTITY_PATH}"
        )
    sha256 = source.get("sha256")
    if type(sha256) is not str or re.fullmatch(r"[0-9a-fA-F]{64}", sha256) is None:
        raise ValueError(
            "identity_contract.canonical_source.sha256 must be a 64-character hexadecimal string"
        )
    if contract.get("head_visibility") not in HEAD_VISIBILITY:
        raise ValueError("identity_contract.head_visibility is invalid")
    for field in IDENTITY_TEXT_FIELDS:
        if not _is_canonical_nonblank_string(contract.get(field)):
            raise ValueError(
                f"identity_contract.{field} must be a canonical nonblank string"
            )
    confidence = contract.get("confidence")
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
        or not math.isfinite(confidence)
        or not 0 <= confidence <= 1
    ):
        raise ValueError("identity_contract.confidence must be a number from 0 to 1")


def _validate_garment_contract(contract: object) -> None:
    if not isinstance(contract, dict):
        raise ValueError("garment_contract must be an object")
    garment_type = contract.get("garment_type")
    hem_position = contract.get("hem_position")
    reason = contract.get("reason")
    full_frame = contract.get("requires_full_garment_frame")
    if not _is_canonical_nonblank_string(garment_type):
        raise ValueError("garment_contract.garment_type must be a canonical nonblank string")
    if hem_position not in HEM_POSITIONS:
        raise ValueError("garment_contract.hem_position is invalid")
    if not isinstance(full_frame, bool):
        raise ValueError("garment_contract.requires_full_garment_frame must be boolean")
    if not _is_canonical_nonblank_string(reason):
        raise ValueError("garment_contract.reason must be a canonical nonblank string")
    if hem_position == "below_knee" and garment_type != "dress":
        raise ValueError(
            "garment_contract.hem_position below_knee is valid only for garment_type dress"
        )
    expected_full_frame = garment_type == "dress" and hem_position == "below_knee"
    if full_frame is not expected_full_frame:
        raise ValueError(
            "garment_contract.requires_full_garment_frame contradicts garment type and hem"
        )


def view_contract_from_manifest(view: object, manifest_view: object) -> dict:
    """Derive footwear state only from explicit validated manifest evidence."""
    if type(view) is not str:
        raise ValueError("view name must be front, side, back, or full")
    view_name, _ = _validate_view(view)
    if not isinstance(manifest_view, dict):
        raise ValueError("manifest view must be an object")
    roles = manifest_view.get("roles")
    if not isinstance(roles, dict):
        raise ValueError("manifest view roles must be an object")
    accessory_sources = roles.get("accessory_source", [])
    if type(accessory_sources) is not list:
        raise ValueError("manifest view accessory_source must be a list")

    if "footwear_contract" not in manifest_view:
        return {"name": view_name, "footwear_required": False}
    contract = manifest_view["footwear_contract"]
    if not isinstance(contract, dict):
        raise ValueError("footwear_contract must be an object")
    if set(contract) != FOOTWEAR_CONTRACT_FIELDS:
        raise ValueError(
            "footwear_contract must contain exactly kind, source_paths, confidence, and reason"
        )
    if contract.get("kind") != "footwear":
        raise ValueError("footwear_contract.kind must be footwear")
    source_paths = contract.get("source_paths")
    if type(source_paths) is not list or not source_paths:
        raise ValueError("footwear_contract.source_paths must be a non-empty list")
    for source_path in source_paths:
        if not _is_canonical_nonblank_string(source_path):
            raise ValueError(
                "footwear_contract.source_paths must contain canonical nonblank strings"
            )
        if source_path not in accessory_sources:
            raise ValueError(
                "footwear_contract.source_paths must resolve to accessory_source paths"
            )
    if len(set(source_paths)) != len(source_paths):
        raise ValueError("footwear_contract.source_paths must be unique")
    confidence = contract.get("confidence")
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
        or not math.isfinite(confidence)
        or not 0.7 <= confidence <= 1
    ):
        raise ValueError("footwear_contract.confidence must be a number from 0.7 to 1")
    if not _is_canonical_nonblank_string(contract.get("reason")):
        raise ValueError("footwear_contract.reason must be a canonical nonblank string")
    return {"name": view_name, "footwear_required": True}


def _deduplicate_in_order(phrases: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered = []
    for phrase in phrases:
        if phrase not in seen:
            seen.add(phrase)
            ordered.append(phrase)
    return ordered


def render_negative_prompt(
    view: object, identity_contract: object, garment_contract: object
) -> str:
    """Return the one canonical negative prompt for the validated contracts."""
    view_name, footwear_required = _validate_view(view)
    _validate_identity_contract(identity_contract)
    _validate_garment_contract(garment_contract)

    defects = list(SHARED_DEFECTS)
    if view_name == "full":
        defects.extend(FULL_VIEW_DEFECTS)
    else:
        defects.extend(
            (
                "less than a visible half head",
                "complete loss of the head",
                f"wrong requested {view_name} view",
                f"crop violations for the active {view_name} composition contract",
            )
        )
    if garment_contract["requires_full_garment_frame"]:
        defects.extend(LONG_DRESS_DEFECTS)
    if footwear_required:
        defects.append(FOOTWEAR_DEFECT)
    return NEGATIVE_PROMPT_PREFIX + "; ".join(_deduplicate_in_order(defects))
