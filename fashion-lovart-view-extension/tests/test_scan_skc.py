import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "skill" / "scripts" / "scan_skc.py"
SPEC = importlib.util.spec_from_file_location("scan_skc", MODULE_PATH)
scan_skc = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(scan_skc)


class ScanSkcAliasTests(unittest.TestCase):
    def test_full_body_folder_alias_is_recognized_without_renaming(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skc = Path(temp_dir) / "ds123"
            full = skc / "全身图"
            full.mkdir(parents=True)
            (full / "1.jpg").write_bytes(b"reference")

            inventory = scan_skc.build_inventory(skc)

            self.assertEqual(inventory["views"]["full"]["folder"], "全身图")
            self.assertEqual(
                inventory["views"]["full"]["files"][0]["relative_path"],
                "全身图/1.jpg",
            )
            self.assertEqual(
                inventory["views"]["full"]["status"],
                "needs_visual_classification",
            )


class ScanSkcVisualContractTests(unittest.TestCase):
    def make_skc(self, root: Path) -> Path:
        skc = root / "ds123"
        for folder in ("正面", "侧面", "背面", "全身"):
            (skc / folder).mkdir(parents=True)
        return skc

    def test_front_one_is_the_only_canonical_identity_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            skc = self.make_skc(Path(temp_dir))
            (skc / "正面" / "1.jpg").write_bytes(b"canonical-model")
            (skc / "侧面" / "1.jpg").write_bytes(b"side-pose")

            inventory = scan_skc.build_inventory(skc)

            source = inventory["canonical_identity_source"]
            self.assertEqual(source["relative_path"], "正面/1.jpg")
            self.assertEqual(
                source["sha256"], scan_skc.sha256_file(skc / "正面" / "1.jpg")
            )
            self.assertEqual(
                {item["role"] for item in inventory["views"]["side"]["files"]},
                {"unclassified"},
            )

    def test_attaches_partial_head_identity_and_below_knee_dress_contracts(self):
        inventory = {
            "canonical_identity_source": {
                "relative_path": "正面/1.jpg",
                "sha256": "a" * 64,
            }
        }
        profile = {
            "head_visibility": "partial",
            "skin_tone_and_visible_ancestry_cues": "warm medium-tan skin with visible Mediterranean appearance cues",
            "visible_face_features": "lower face and lips visible",
            "hair_evidence": "dark brown loose strands",
            "age_impression": "adult, approximately 25-35",
            "body_profile": "slim adult build",
            "confidence": 0.86,
            "reason": "Derived only from visible evidence in 正面/1.jpg",
        }
        garment = {
            "garment_type": "dress",
            "hem_position": "below_knee",
            "requires_full_garment_frame": True,
            "reason": "The product hem extends below both knees.",
        }

        result = scan_skc.attach_visual_contracts(inventory, profile, garment)

        self.assertEqual(result["identity_profile"]["head_visibility"], "partial")
        self.assertTrue(result["garment_profile"]["requires_full_garment_frame"])

    def test_contract_canonical_source_cannot_be_overridden_by_caller(self):
        inventory = {
            "canonical_identity_source": {
                "relative_path": "正面/1.jpg",
                "sha256": "a" * 64,
            }
        }
        profile = {
            "canonical_source": {"relative_path": "侧面/1.jpg", "sha256": "caller-hash"},
            "head_visibility": "partial",
            "skin_tone_and_visible_ancestry_cues": "warm medium-tan skin",
            "visible_face_features": "lower face and lips visible",
            "hair_evidence": "dark brown loose strands",
            "age_impression": "adult, approximately 25-35",
            "body_profile": "slim adult build",
            "confidence": 0.86,
            "reason": "Derived only from visible evidence in 正面/1.jpg",
        }
        garment = {
            "garment_type": "dress",
            "hem_position": "below_knee",
            "requires_full_garment_frame": True,
            "reason": "The product hem extends below both knees.",
        }

        result = scan_skc.attach_visual_contracts(inventory, profile, garment)

        self.assertEqual(
            result["identity_profile"]["canonical_source"],
            {"relative_path": "正面/1.jpg", "sha256": "a" * 64},
        )

    def test_attach_visual_contracts_rejects_blank_identity_evidence(self):
        inventory = {
            "canonical_identity_source": {
                "relative_path": "正面/1.jpg",
                "sha256": "a" * 64,
            }
        }
        profile = {
            "head_visibility": "partial",
            "skin_tone_and_visible_ancestry_cues": "warm medium-tan skin",
            "visible_face_features": "lower face visible",
            "hair_evidence": "dark brown loose strands",
            "age_impression": "adult, approximately 25-35",
            "body_profile": "slim adult build",
            "confidence": 0.86,
            "reason": "Visible evidence only",
        }
        garment = {
            "garment_type": "dress",
            "hem_position": "below_knee",
            "requires_full_garment_frame": True,
            "reason": "Hem extends below both knees.",
        }
        for field in (
            "skin_tone_and_visible_ancestry_cues",
            "visible_face_features",
            "hair_evidence",
            "age_impression",
            "body_profile",
            "reason",
        ):
            with self.subTest(field=field):
                broken = dict(profile)
                broken[field] = "   "
                with self.assertRaisesRegex(ValueError, field):
                    scan_skc.attach_visual_contracts(
                        dict(inventory), broken, dict(garment)
                    )

    def test_attach_visual_contracts_rejects_invalid_confidence(self):
        inventory = {
            "canonical_identity_source": {
                "relative_path": "正面/1.jpg",
                "sha256": "a" * 64,
            }
        }
        profile = {
            "head_visibility": "partial",
            "skin_tone_and_visible_ancestry_cues": "warm medium-tan skin",
            "visible_face_features": "lower face visible",
            "hair_evidence": "dark brown loose strands",
            "age_impression": "adult, approximately 25-35",
            "body_profile": "slim adult build",
            "confidence": 0.86,
            "reason": "Visible evidence only",
        }
        garment = {
            "garment_type": "dress",
            "hem_position": "below_knee",
            "requires_full_garment_frame": True,
            "reason": "Hem extends below both knees.",
        }
        for confidence in (-0.01, 1.01, True, "0.86", None):
            with self.subTest(confidence=confidence):
                broken = dict(profile)
                broken["confidence"] = confidence
                with self.assertRaisesRegex(ValueError, "confidence"):
                    scan_skc.attach_visual_contracts(
                        dict(inventory), broken, dict(garment)
                    )

    def test_attach_visual_contracts_rejects_incomplete_garment_profile(self):
        inventory = {
            "canonical_identity_source": {
                "relative_path": "正面/1.jpg",
                "sha256": "a" * 64,
            }
        }
        profile = {
            "head_visibility": "partial",
            "skin_tone_and_visible_ancestry_cues": "warm medium-tan skin",
            "visible_face_features": "lower face visible",
            "hair_evidence": "dark brown loose strands",
            "age_impression": "adult, approximately 25-35",
            "body_profile": "slim adult build",
            "confidence": 0.86,
            "reason": "Visible evidence only",
        }
        garment = {
            "garment_type": "dress",
            "hem_position": "below_knee",
            "requires_full_garment_frame": True,
            "reason": "Hem extends below both knees.",
        }
        for field in garment:
            with self.subTest(field=field):
                broken = dict(garment)
                del broken[field]
                with self.assertRaisesRegex(ValueError, field):
                    scan_skc.attach_visual_contracts(
                        dict(inventory), dict(profile), broken
                    )

    def test_attach_visual_contracts_rejects_below_knee_non_dress(self):
        inventory = {
            "canonical_identity_source": {
                "relative_path": "正面/1.jpg",
                "sha256": "a" * 64,
            }
        }
        profile = {
            "head_visibility": "partial",
            "skin_tone_and_visible_ancestry_cues": "warm medium-tan skin",
            "visible_face_features": "lower face visible",
            "hair_evidence": "dark brown loose strands",
            "age_impression": "adult, approximately 25-35",
            "body_profile": "slim adult build",
            "confidence": 0.86,
            "reason": "Visible evidence only",
        }
        garment = {
            "garment_type": "shirt",
            "hem_position": "below_knee",
            "requires_full_garment_frame": False,
            "reason": "Invalid self-declared shirt contract.",
        }

        with self.assertRaisesRegex(ValueError, "below_knee.*dress"):
            scan_skc.attach_visual_contracts(inventory, profile, garment)


if __name__ == "__main__":
    unittest.main()
