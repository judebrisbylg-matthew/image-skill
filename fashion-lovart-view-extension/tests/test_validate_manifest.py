import copy
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "skill" / "scripts" / "validate_manifest.py"
SPEC = importlib.util.spec_from_file_location("validate_manifest", MODULE_PATH)
validate_manifest = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validate_manifest)


CANONICAL_SOURCE = {"relative_path": "正面/1.jpg", "sha256": "a" * 64}


def valid_manifest():
    return {
        "schema_version": 2,
        "skc_id": "ds726301071",
        "canonical_identity_source": copy.deepcopy(CANONICAL_SOURCE),
        "identity_profile": {
            "canonical_source": copy.deepcopy(CANONICAL_SOURCE),
            "head_visibility": "partial",
            "skin_tone_and_visible_ancestry_cues": "warm medium-tan skin",
            "visible_face_features": "lower face visible",
            "hair_evidence": "dark brown strand",
            "age_impression": "adult 25-35",
            "body_profile": "slim adult build",
            "confidence": 0.86,
            "reason": "Visible evidence only",
        },
        "garment_profile": {
            "garment_type": "dress",
            "hem_position": "below_knee",
            "requires_full_garment_frame": True,
            "reason": "Hem is below knee",
        },
        "views": {"front": {"status": "blocked:missing-view", "roles": {}}},
    }


def identity_lock_text(manifest):
    profile = manifest["identity_profile"]
    return (
        "IDENTITY LOCK: canonical_source=正面/1.jpg; "
        f"head_visibility={profile['head_visibility']}; "
        f"skin_tone_and_visible_ancestry_cues={profile['skin_tone_and_visible_ancestry_cues']}; "
        f"visible_face_features={profile['visible_face_features']}; "
        f"hair_evidence={profile['hair_evidence']}; "
        f"age_impression={profile['age_impression']}; "
        f"body_profile={profile['body_profile']}; "
        "Noncanonical local pose/composition sources must not control or override "
        "body_profile."
    )


def valid_prompt(view="front", manifest=None):
    manifest = manifest or valid_manifest()
    prefix = {"front": "FR", "side": "SI", "back": "BA", "full": "FU"}[view]
    head_lock = (
        "FULL-BODY HEAD COMPLETION: Even when 正面/1.jpg shows a partial head or "
        "no head, reconstruct a natural complete head using only the visible skin "
        "tone, ancestry cues, partial facial evidence, hair evidence, age impression, "
        "neck/shoulder evidence, and body profile. Do not change the model's visible "
        "identity characteristics."
        if view == "full"
        else (
            "HEAD CROP FLOOR: The final image must retain at least half of the "
            "model's head. A complete head is allowed. Never crop below the "
            "half-head boundary."
        )
    )
    final_contract = [
        (
            "FINAL CONTRACT OVERRIDE: In any conflict, the following identity, "
            "head-crop, full-body, and garment contracts override every earlier "
            "sentence in this prompt."
        ),
        identity_lock_text(manifest),
        head_lock,
    ]
    if manifest["garment_profile"]["requires_full_garment_frame"] is True:
        final_contract.append(
            "GARMENT FRAME LOCK: Activate only for a visually confirmed below-knee "
            "dress; when active, keep the dress continuously visible from the "
            "shoulder/neckline through the lowest hem point; leave visible safety "
            "margin below the hem; the hem must not touch or cross an image edge; "
            "keep the major hem silhouette unobscured; keep the apparent garment "
            "length unchanged."
        )
    return {
        "schema_version": 2,
        "skc_id": manifest["skc_id"],
        "view": view,
        "generation": {
            "model": "nano banana pro",
            "resolution": "4K",
            "aspect_ratio": "2:3",
        },
        "identity_contract": copy.deepcopy(manifest["identity_profile"]),
        "garment_contract": copy.deepcopy(manifest["garment_profile"]),
        "analysis_markdown": "# Completed Chinese analysis",
        "actions": [
            {
                "action_id": f"{prefix}{index:02d}",
                "title": f"Action {index}",
                "prompt_en": (
                    f"SKC {manifest['skc_id']} | VIEW {view} | ACTION "
                    f"{prefix}{index:02d} | ATTEMPT 1 Nano Banana Pro, 4K, 2:3. "
                    f"{' '.join(final_contract)}"
                ),
                "negative_prompt": "Do not alter the product.",
            }
            for index in range(1, 6)
        ],
    }


class ManifestSchemaTwoTests(unittest.TestCase):
    def test_accepts_valid_schema_two_manifest(self):
        self.assertEqual(validate_manifest.validate_manifest_data(valid_manifest()), [])

    def test_rejects_noncanonical_identity_path(self):
        manifest = valid_manifest()
        manifest["canonical_identity_source"]["relative_path"] = "侧面/1.jpg"
        self.assertTrue(validate_manifest.validate_manifest_data(manifest))

    def test_rejects_invalid_head_visibility(self):
        manifest = valid_manifest()
        manifest["identity_profile"]["head_visibility"] = "hidden"
        self.assertTrue(validate_manifest.validate_manifest_data(manifest))

    def test_rejects_below_knee_dress_without_full_garment_frame(self):
        manifest = valid_manifest()
        manifest["garment_profile"]["requires_full_garment_frame"] = False
        self.assertTrue(validate_manifest.validate_manifest_data(manifest))

    def test_rejects_missing_or_blank_identity_evidence_fields(self):
        for field in (
            "skin_tone_and_visible_ancestry_cues",
            "visible_face_features",
            "hair_evidence",
            "age_impression",
            "body_profile",
            "reason",
        ):
            with self.subTest(field=field, defect="missing"):
                manifest = valid_manifest()
                del manifest["identity_profile"][field]
                self.assertTrue(validate_manifest.validate_manifest_data(manifest))
            with self.subTest(field=field, defect="blank"):
                manifest = valid_manifest()
                manifest["identity_profile"][field] = "   "
                self.assertTrue(validate_manifest.validate_manifest_data(manifest))

    def test_rejects_invalid_identity_confidence(self):
        for confidence in (-0.01, 1.01, True, "0.86", None):
            with self.subTest(confidence=confidence):
                manifest = valid_manifest()
                manifest["identity_profile"]["confidence"] = confidence
                self.assertTrue(validate_manifest.validate_manifest_data(manifest))

    def test_rejects_incomplete_or_invalid_garment_evidence(self):
        for field in (
            "garment_type",
            "hem_position",
            "requires_full_garment_frame",
            "reason",
        ):
            with self.subTest(field=field, defect="missing"):
                manifest = valid_manifest()
                del manifest["garment_profile"][field]
                self.assertTrue(validate_manifest.validate_manifest_data(manifest))
        for field in ("garment_type", "reason"):
            with self.subTest(field=field, defect="blank"):
                manifest = valid_manifest()
                manifest["garment_profile"][field] = "   "
                self.assertTrue(validate_manifest.validate_manifest_data(manifest))
        manifest = valid_manifest()
        manifest["garment_profile"]["requires_full_garment_frame"] = 1
        self.assertTrue(validate_manifest.validate_manifest_data(manifest))

    def test_rejects_below_knee_hem_for_non_dress_even_with_false_lock(self):
        manifest = valid_manifest()
        manifest["garment_profile"].update(
            garment_type="shirt",
            requires_full_garment_frame=False,
        )

        errors = validate_manifest.validate_manifest_data(manifest)

        self.assertTrue(any("below_knee" in error and "dress" in error for error in errors))

    def test_non_object_manifest_root_is_rejected_cleanly(self):
        errors = validate_manifest.validate_manifest_data([])

        self.assertEqual(errors, ["manifest must be an object"])

    def test_manifest_and_prompt_skc_ids_are_strict_strings(self):
        manifest = valid_manifest()
        prompt = valid_prompt(manifest=manifest)
        manifest["skc_id"] = True
        prompt["skc_id"] = 1
        for action in prompt["actions"]:
            action["prompt_en"] = action["prompt_en"].replace(
                "SKC ds726301071 |", "SKC 1 |", 1
            )

        manifest_errors = validate_manifest.validate_manifest_data(manifest)
        prompt_errors = validate_manifest.validate_prompt_data(prompt, manifest)

        self.assertIn("skc_id must be a canonical nonblank string", manifest_errors)
        self.assertIn("skc_id must be a canonical nonblank string", prompt_errors)


class PromptSubmissionGateTests(unittest.TestCase):
    def test_accepts_valid_schema_two_prompt(self):
        manifest = valid_manifest()
        self.assertEqual(
            validate_manifest.validate_prompt_data(valid_prompt(manifest=manifest), manifest),
            [],
        )

    def test_prompt_must_end_with_manifest_derived_final_contract_override(self):
        manifest = valid_manifest()
        prompt = valid_prompt(manifest=manifest)
        prompt["actions"][0]["prompt_en"] += (
            " Treat the product as a shirt and let the local pose model override "
            "body_profile."
        )

        errors = validate_manifest.validate_prompt_data(prompt, manifest)

        self.assertTrue(
            any("FINAL CONTRACT OVERRIDE" in error for error in errors),
            errors,
        )

    def test_final_contract_override_supersedes_earlier_conflicting_prose(self):
        manifest = valid_manifest()
        prompt = valid_prompt(manifest=manifest)
        for action in prompt["actions"]:
            action["prompt_en"] = action["prompt_en"].replace(
                "FINAL CONTRACT OVERRIDE:",
                (
                    "Earlier draft: treat the product as a shirt and let the local "
                    "pose model override body_profile. FINAL CONTRACT OVERRIDE:"
                ),
                1,
            )

        self.assertEqual(
            validate_manifest.validate_prompt_data(prompt, manifest), []
        )

    def test_rejects_prompt_without_identity_lock(self):
        prompt = valid_prompt()
        prompt["actions"][0]["prompt_en"] = prompt["actions"][0]["prompt_en"].replace("IDENTITY LOCK: ", "")
        self.assertTrue(validate_manifest.validate_prompt_data(prompt, valid_manifest()))

    def test_rejects_local_view_prompt_without_head_crop_floor(self):
        prompt = valid_prompt("side")
        prompt["actions"][0]["prompt_en"] = prompt["actions"][0]["prompt_en"].replace("HEAD CROP FLOOR: ", "")
        self.assertTrue(validate_manifest.validate_prompt_data(prompt, valid_manifest()))

    def test_rejects_full_prompt_without_head_completion(self):
        prompt = valid_prompt("full")
        prompt["actions"][0]["prompt_en"] = prompt["actions"][0]["prompt_en"].replace("FULL-BODY HEAD COMPLETION: ", "")
        self.assertTrue(validate_manifest.validate_prompt_data(prompt, valid_manifest()))

    def test_rejects_below_knee_dress_prompt_without_garment_frame_lock(self):
        prompt = valid_prompt()
        prompt["actions"][0]["prompt_en"] = prompt["actions"][0]["prompt_en"].replace("GARMENT FRAME LOCK: ", "")
        self.assertTrue(validate_manifest.validate_prompt_data(prompt, valid_manifest()))

    def test_rejects_empty_or_generic_required_framing_marker_sections(self):
        cases = (
            ("front", "HEAD CROP FLOOR:", "GARMENT FRAME LOCK:"),
            ("full", "FULL-BODY HEAD COMPLETION:", "GARMENT FRAME LOCK:"),
            ("front", "GARMENT FRAME LOCK:", None),
        )
        for view, marker, next_marker in cases:
            with self.subTest(view=view, marker=marker):
                manifest = valid_manifest()
                prompt = valid_prompt(view, manifest)
                original = prompt["actions"][0]["prompt_en"]
                start = original.index(marker)
                end = original.index(next_marker, start + len(marker)) if next_marker else len(original)
                prompt["actions"][0]["prompt_en"] = (
                    original[:start]
                    + marker
                    + " Preserve framing. "
                    + original[end:]
                )

                errors = validate_manifest.validate_prompt_data(prompt, manifest)

                self.assertTrue(any("actionable" in error for error in errors))

    def test_rejects_negated_hard_lock_clauses(self):
        mutations = (
            (
                "front",
                "The final image must retain at least half of the model's head.",
                "Do not retain at least half of the model's head.",
            ),
            (
                "full",
                (
                    "reconstruct a natural complete head using only the visible skin "
                    "tone"
                ),
                (
                    "do not reconstruct a natural complete head using only the "
                    "visible skin tone"
                ),
            ),
            (
                "front",
                "keep the major hem silhouette unobscured",
                "do not keep the major hem silhouette unobscured",
            ),
        )
        for view, positive, negated in mutations:
            with self.subTest(view=view, positive=positive):
                manifest = valid_manifest()
                prompt = valid_prompt(view, manifest)
                prompt["actions"][0]["prompt_en"] = prompt["actions"][0][
                    "prompt_en"
                ].replace(positive, negated, 1)

                errors = validate_manifest.validate_prompt_data(prompt, manifest)

                self.assertTrue(any("actionable" in error for error in errors))

    def test_rejects_prompt_whose_skc_id_differs_from_active_manifest(self):
        manifest = valid_manifest()
        prompt = valid_prompt(manifest=manifest)
        prompt["skc_id"] = "another-skc"

        errors = validate_manifest.validate_prompt_data(prompt, manifest)

        self.assertTrue(any("skc_id" in error and "active manifest" in error for error in errors))

    def test_rejects_marker_only_identity_contract_instead_of_active_profile(self):
        manifest = valid_manifest()
        prompt = valid_prompt(manifest=manifest)
        prompt["identity_contract"] = {
            "canonical_source": "正面/1.jpg",
            "head_visibility": "partial",
        }

        errors = validate_manifest.validate_prompt_data(prompt, manifest)

        self.assertTrue(any("identity_contract" in error and "active manifest" in error for error in errors))

    def test_rejects_any_canonical_identity_path_hash_or_profile_mismatch(self):
        mutations = {
            "relative_path": lambda contract: contract["canonical_source"].update(
                relative_path="侧面/1.jpg"
            ),
            "sha256": lambda contract: contract["canonical_source"].update(
                sha256="b" * 64
            ),
            "body_profile": lambda contract: contract.update(
                body_profile="different adult build"
            ),
        }
        for field, mutate in mutations.items():
            with self.subTest(field=field):
                manifest = valid_manifest()
                prompt = valid_prompt(manifest=manifest)
                mutate(prompt["identity_contract"])

                errors = validate_manifest.validate_prompt_data(prompt, manifest)

                self.assertTrue(
                    any("identity_contract" in error and "active manifest" in error for error in errors)
                )

    def test_rejects_self_declared_shirt_contract_despite_lock_marker(self):
        manifest = valid_manifest()
        prompt = valid_prompt(manifest=manifest)
        prompt["garment_contract"] = {
            "garment_type": "shirt",
            "hem_position": "not_applicable",
            "requires_full_garment_frame": False,
            "reason": "Prompt self-declares a shirt.",
        }
        self.assertTrue(all("GARMENT FRAME LOCK:" in action["prompt_en"] for action in prompt["actions"]))

        errors = validate_manifest.validate_prompt_data(prompt, manifest)

        self.assertTrue(any("garment_contract" in error and "active manifest" in error for error in errors))

    def test_active_manifest_still_requires_dress_lock_after_prompt_self_declares_shirt(self):
        manifest = valid_manifest()
        prompt = valid_prompt(manifest=manifest)
        prompt["garment_contract"] = {
            "garment_type": "shirt",
            "hem_position": "not_applicable",
            "requires_full_garment_frame": False,
            "reason": "Prompt attempts to weaken the active dress contract.",
        }
        for action in prompt["actions"]:
            action["prompt_en"] = action["prompt_en"].replace(
                "GARMENT FRAME LOCK:", "UNBOUND GARMENT NOTE:"
            )

        errors = validate_manifest.validate_prompt_data(prompt, manifest)

        self.assertTrue(
            any(
                "GARMENT FRAME LOCK:" in error and "actionable" in error
                for error in errors
            )
        )

    def test_rejects_empty_or_generic_identity_lock_sections(self):
        manifest = valid_manifest()
        for replacement in (
            "IDENTITY LOCK: ",
            "IDENTITY LOCK: Preserve the same person. ",
        ):
            with self.subTest(replacement=replacement):
                prompt = valid_prompt(manifest=manifest)
                original = prompt["actions"][0]["prompt_en"]
                section_start = original.index("IDENTITY LOCK:")
                section_end = original.index("HEAD CROP FLOOR:")
                prompt["actions"][0]["prompt_en"] = (
                    original[:section_start] + replacement + original[section_end:]
                )

                errors = validate_manifest.validate_prompt_data(prompt, manifest)

                self.assertTrue(
                    any("concrete active identity_profile" in error for error in errors)
                )

    def test_rejects_identity_values_placed_outside_the_identity_lock_section(self):
        manifest = valid_manifest()
        prompt = valid_prompt(manifest=manifest)
        original = prompt["actions"][0]["prompt_en"]
        section_start = original.index("IDENTITY LOCK:")
        section_end = original.index("HEAD CROP FLOOR:")
        concrete_values = original[
            section_start + len("IDENTITY LOCK:") : section_end
        ]
        prompt["actions"][0]["prompt_en"] = (
            original[:section_start]
            + "IDENTITY LOCK: Preserve the same person. "
            + original[section_end:]
            + " "
            + concrete_values
        )

        errors = validate_manifest.validate_prompt_data(prompt, manifest)

        self.assertTrue(
            any("concrete active identity_profile" in error for error in errors)
        )

    def test_rejects_identity_lock_missing_any_concrete_profile_value(self):
        manifest = valid_manifest()
        for field in (
            "head_visibility",
            "skin_tone_and_visible_ancestry_cues",
            "visible_face_features",
            "hair_evidence",
            "age_impression",
            "body_profile",
        ):
            with self.subTest(field=field):
                prompt = valid_prompt(manifest=manifest)
                value = str(manifest["identity_profile"][field])
                prompt["actions"][0]["prompt_en"] = prompt["actions"][0][
                    "prompt_en"
                ].replace(value, "[omitted]", 1)

                errors = validate_manifest.validate_prompt_data(prompt, manifest)

                self.assertTrue(any(field in error for error in errors))

    def test_rejects_prefixed_or_duplicate_identity_assignment_values(self):
        manifest = valid_manifest()
        active = "body_profile=slim adult build;"
        mutations = (
            "body_profile=slim adult buildx;",
            (
                "body_profile=slim adult build; "
                "body_profile=different adult build;"
            ),
        )
        for replacement in mutations:
            with self.subTest(replacement=replacement):
                prompt = valid_prompt(manifest=manifest)
                prompt["actions"][0]["prompt_en"] = prompt["actions"][0][
                    "prompt_en"
                ].replace(active, replacement, 1)

                errors = validate_manifest.validate_prompt_data(prompt, manifest)

                self.assertTrue(
                    any("identity_profile assignments" in error for error in errors)
                )

    def test_contract_comparison_rejects_boolean_integer_coercion(self):
        identity_manifest = valid_manifest()
        identity_manifest["identity_profile"]["confidence"] = 1
        identity_prompt = valid_prompt(manifest=identity_manifest)
        identity_prompt["identity_contract"]["confidence"] = True

        identity_errors = validate_manifest.validate_prompt_data(
            identity_prompt, identity_manifest
        )

        self.assertTrue(any("identity_contract" in error for error in identity_errors))

        garment_manifest = valid_manifest()
        garment_prompt = valid_prompt(manifest=garment_manifest)
        garment_prompt["garment_contract"]["requires_full_garment_frame"] = 1

        garment_errors = validate_manifest.validate_prompt_data(
            garment_prompt, garment_manifest
        )

        self.assertTrue(any("garment_contract" in error for error in garment_errors))

    def test_rejects_identity_lock_without_local_body_profile_authority_guard(self):
        manifest = valid_manifest()
        prompt = valid_prompt(manifest=manifest)
        prompt["actions"][0]["prompt_en"] = prompt["actions"][0][
            "prompt_en"
        ].replace(
            "Noncanonical local pose/composition sources must not control or override body_profile.",
            "Local pose/composition sources control body_profile.",
        )

        errors = validate_manifest.validate_prompt_data(prompt, manifest)

        self.assertTrue(
            any("must not control or override body_profile" in error for error in errors)
        )

    def test_rejects_prompt_when_active_manifest_itself_is_invalid(self):
        manifest = valid_manifest()
        manifest["identity_profile"]["reason"] = "   "

        errors = validate_manifest.validate_prompt_data(valid_prompt(), manifest)

        self.assertTrue(any(error.startswith("active manifest:") for error in errors))

    def test_cli_prompt_validation_requires_and_uses_manifest_argument(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            prompt_path = root / "front.json"
            manifest_path = root / "manifest.json"
            manifest = valid_manifest()
            prompt_path.write_text(
                json.dumps(valid_prompt(manifest=manifest), ensure_ascii=False),
                encoding="utf-8",
            )
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False),
                encoding="utf-8",
            )

            missing_manifest = subprocess.run(
                ["python3", str(MODULE_PATH), "prompt", str(prompt_path)],
                capture_output=True,
                text=True,
            )
            with_manifest = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "prompt",
                    str(prompt_path),
                    str(manifest_path),
                ],
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(missing_manifest.returncode, 0)
        self.assertIn("manifest", (missing_manifest.stdout + missing_manifest.stderr).lower())
        self.assertEqual(with_manifest.returncode, 0, with_manifest.stdout + with_manifest.stderr)

    def test_non_object_prompt_or_active_manifest_is_rejected_cleanly(self):
        prompt_errors = validate_manifest.validate_prompt_data([], valid_manifest())
        manifest_errors = validate_manifest.validate_prompt_data(valid_prompt(), [])

        self.assertIn("prompt must be an object", prompt_errors)
        self.assertIn("active manifest must be an object", manifest_errors)


if __name__ == "__main__":
    unittest.main()
