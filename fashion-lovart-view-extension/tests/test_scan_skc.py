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
        inventory = {"canonical_identity_source": {"relative_path": "正面/1.jpg", "sha256": "abc"}}
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


if __name__ == "__main__":
    unittest.main()
