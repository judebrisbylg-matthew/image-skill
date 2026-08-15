#!/usr/bin/env python3
"""Inventory SKC folders without guessing image semantics."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path


VIEW_FOLDERS = {
    "front": ("正面",),
    "side": ("侧面",),
    "back": ("背面",),
    "full": ("全身", "全身图"),
}
VIEW_ORDER = ("front", "side", "back", "full")
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ROLES = (
    "model_source",
    "product_source",
    "scene_source",
    "composition_source",
    "accessory_source",
    "unused",
)
REQUIRED_ROLES = ("model_source", "product_source", "scene_source")


def is_skc_dir(path: Path) -> bool:
    return path.is_dir() and any(
        (path / name).is_dir()
        for aliases in VIEW_FOLDERS.values()
        for name in aliases
    )


def discover_skc_paths(input_path: Path | str) -> list[Path]:
    path = Path(input_path).expanduser().resolve()
    if is_skc_dir(path):
        return [path]
    if not path.is_dir():
        raise ValueError(f"input path is not a directory: {path}")
    return sorted(
        (child.resolve() for child in path.iterdir() if is_skc_dir(child)),
        key=lambda item: item.name.casefold(),
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_inventory(skc_path: Path | str) -> dict:
    skc = Path(skc_path).expanduser().resolve()
    if not is_skc_dir(skc):
        raise ValueError(f"not an SKC folder: {skc}")

    views = {}
    all_files = []
    for view_key, aliases in VIEW_FOLDERS.items():
        folder_name = next((name for name in aliases if (skc / name).is_dir()), aliases[0])
        view_dir = skc / folder_name
        files = []
        if view_dir.is_dir():
            for image_path in sorted(view_dir.iterdir(), key=lambda item: item.name.casefold()):
                if (
                    image_path.name.startswith(".")
                    or not image_path.is_file()
                    or image_path.suffix.casefold() not in SUPPORTED_EXTENSIONS
                ):
                    continue
                item = {
                    "name": image_path.name,
                    "relative_path": image_path.relative_to(skc).as_posix(),
                    "sha256": sha256_file(image_path),
                    "size_bytes": image_path.stat().st_size,
                    "role": "unclassified",
                    "confidence": None,
                    "reason": "",
                    "duplicate_group": None,
                }
                files.append(item)
                all_files.append(item)
        views[view_key] = {
            "folder": folder_name,
            "status": "needs_visual_classification" if files else "blocked:missing-view",
            "files": files,
            "roles": {role: [] for role in ROLES},
            "composition_fallback": None,
            "blockers": [] if files else ["missing view folder or supported images"],
        }

    groups = defaultdict(list)
    for item in all_files:
        groups[item["sha256"]].append(item)
    duplicate_number = 0
    for same_content in groups.values():
        if len(same_content) < 2:
            continue
        duplicate_number += 1
        group_id = f"dup-{duplicate_number:03d}"
        for item in same_content:
            item["duplicate_group"] = group_id

    return {
        "schema_version": 1,
        "skc_id": skc.name,
        "skc_path": str(skc),
        "views": {key: views[key] for key in VIEW_ORDER},
    }


def apply_role_assignments(inventory: dict, assignments: dict) -> dict:
    """Apply visual classifications produced by Codex, then derive view readiness."""
    for view_key in VIEW_ORDER:
        view = inventory["views"][view_key]
        view["roles"] = {role: [] for role in ROLES}
        for item in view["files"]:
            assignment = assignments.get(item["relative_path"])
            if assignment is None:
                item.update(role="unclassified", confidence=None, reason="")
                continue
            role = assignment.get("role")
            if role not in ROLES:
                raise ValueError(f"invalid role {role!r} for {item['relative_path']}")
            confidence = assignment.get("confidence")
            if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                raise ValueError(f"invalid confidence for {item['relative_path']}")
            reason = str(assignment.get("reason", "")).strip()
            if not reason:
                raise ValueError(f"missing visual reason for {item['relative_path']}")
            item.update(role=role, confidence=float(confidence), reason=reason)
            view["roles"][role].append(item["relative_path"])

        view["composition_fallback"] = None
        if not view["roles"]["composition_source"] and len(view["roles"]["model_source"]) == 1:
            view["roles"]["composition_source"] = list(view["roles"]["model_source"])
            view["composition_fallback"] = "model_source"

        missing = [role for role in REQUIRED_ROLES if len(view["roles"][role]) != 1]
        unclassified = [item["relative_path"] for item in view["files"] if item["role"] == "unclassified"]
        low_confidence = [
            item["relative_path"]
            for item in view["files"]
            if item["role"] != "unclassified" and item["confidence"] < 0.7
        ]
        blockers = []
        if missing:
            blockers.append("required roles must each resolve to exactly one source: " + ", ".join(missing))
        if unclassified:
            blockers.append("unclassified images: " + ", ".join(unclassified))
        if low_confidence:
            blockers.append("low-confidence classifications: " + ", ".join(low_confidence))
        view["blockers"] = blockers
        view["status"] = "ready" if not blockers else "blocked:role-ambiguous"
    return inventory


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_path", type=Path)
    parser.add_argument("--output", type=Path, help="Write one JSON batch inventory here")
    args = parser.parse_args()
    skc_paths = discover_skc_paths(args.input_path)
    payload = {"schema_version": 1, "input_path": str(args.input_path.resolve()), "skcs": [build_inventory(p) for p in skc_paths]}
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if skc_paths else 2


if __name__ == "__main__":
    raise SystemExit(main())
