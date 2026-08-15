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


def valid_prompt(view="front", manifest=None):
    manifest = manifest or valid_manifest()
    prefix = {"front": "FR", "side": "SI", "back": "BA", "full": "FU"}[view]
    markers = ["IDENTITY LOCK:", "GARMENT FRAME LOCK:"]
    markers.append("FULL-BODY HEAD COMPLETION:" if view == "full" else "HEAD CROP FLOOR:")
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
                    f"SKC ds726301071 | VIEW {view} | ACTION {prefix}{index:02d} | ATTEMPT 1 "
                    f"{' '.join(markers)} Nano Banana Pro, 4K, 2:3."
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


class PromptSubmissionGateTests(unittest.TestCase):
    def test_accepts_valid_schema_two_prompt(self):
        manifest = valid_manifest()
        self.assertEqual(
            validate_manifest.validate_prompt_data(valid_prompt(manifest=manifest), manifest),
            [],
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


if __name__ == "__main__":
    unittest.main()
