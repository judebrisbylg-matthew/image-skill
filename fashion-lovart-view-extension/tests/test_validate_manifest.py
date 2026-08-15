import copy
import importlib.util
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


def valid_prompt(view="front"):
    prefix = {"front": "FR", "side": "SI", "back": "BA", "full": "FU"}[view]
    markers = ["IDENTITY LOCK:", "GARMENT FRAME LOCK:"]
    markers.append("FULL-BODY HEAD COMPLETION:" if view == "full" else "HEAD CROP FLOOR:")
    return {
        "schema_version": 2,
        "skc_id": "ds726301071",
        "view": view,
        "generation": {
            "model": "nano banana pro",
            "resolution": "4K",
            "aspect_ratio": "2:3",
        },
        "identity_contract": {
            "canonical_source": "正面/1.jpg",
            "head_visibility": "partial",
        },
        "garment_contract": {
            "garment_type": "dress",
            "hem_position": "below_knee",
            "requires_full_garment_frame": True,
        },
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


class PromptSubmissionGateTests(unittest.TestCase):
    def test_accepts_valid_schema_two_prompt(self):
        self.assertEqual(validate_manifest.validate_prompt_data(valid_prompt()), [])

    def test_rejects_prompt_without_identity_lock(self):
        prompt = valid_prompt()
        prompt["actions"][0]["prompt_en"] = prompt["actions"][0]["prompt_en"].replace("IDENTITY LOCK: ", "")
        self.assertTrue(validate_manifest.validate_prompt_data(prompt))

    def test_rejects_local_view_prompt_without_head_crop_floor(self):
        prompt = valid_prompt("side")
        prompt["actions"][0]["prompt_en"] = prompt["actions"][0]["prompt_en"].replace("HEAD CROP FLOOR: ", "")
        self.assertTrue(validate_manifest.validate_prompt_data(prompt))

    def test_rejects_full_prompt_without_head_completion(self):
        prompt = valid_prompt("full")
        prompt["actions"][0]["prompt_en"] = prompt["actions"][0]["prompt_en"].replace("FULL-BODY HEAD COMPLETION: ", "")
        self.assertTrue(validate_manifest.validate_prompt_data(prompt))

    def test_rejects_below_knee_dress_prompt_without_garment_frame_lock(self):
        prompt = valid_prompt()
        prompt["actions"][0]["prompt_en"] = prompt["actions"][0]["prompt_en"].replace("GARMENT FRAME LOCK: ", "")
        self.assertTrue(validate_manifest.validate_prompt_data(prompt))


if __name__ == "__main__":
    unittest.main()
