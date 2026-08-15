import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "skill" / "scripts" / "scan_skc.py"
SPEC = importlib.util.spec_from_file_location("scan_skc", MODULE_PATH)
scan_skc = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(scan_skc)

VALIDATOR_PATH = MODULE_PATH.with_name("validate_manifest.py")
VALIDATOR_SPEC = importlib.util.spec_from_file_location(
    "validate_manifest_for_scan_tests", VALIDATOR_PATH
)
validate_manifest = importlib.util.module_from_spec(VALIDATOR_SPEC)
assert VALIDATOR_SPEC.loader is not None
VALIDATOR_SPEC.loader.exec_module(validate_manifest)


def valid_inventory():
    return {
        "schema_version": 1,
        "skc_id": "ds123",
        "canonical_identity_source": {
            "relative_path": "正面/1.jpg",
            "sha256": "a" * 64,
        },
        "views": {"front": {"status": "blocked:missing-view", "roles": {}}},
    }


def valid_identity_profile(**updates):
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
    profile.update(updates)
    return profile


def valid_garment_profile(**updates):
    profile = {
        "garment_type": "dress",
        "hem_position": "below_knee",
        "requires_full_garment_frame": True,
        "reason": "Hem extends below both knees.",
    }
    profile.update(updates)
    return profile


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

    def test_role_assignments_reject_boolean_confidence_and_non_string_reason(self):
        def inventory_with_one_file():
            inventory = valid_inventory()
            inventory["views"] = {
                view: {"files": [], "roles": {}, "status": "blocked:missing-view"}
                for view in scan_skc.VIEW_ORDER
            }
            inventory["views"]["front"]["files"] = [
                {"relative_path": "正面/1.jpg"}
            ]
            return inventory

        for assignment in (
            {"role": "model_source", "confidence": True, "reason": "visible"},
            {"role": "model_source", "confidence": 0.9, "reason": 123},
        ):
            with self.subTest(assignment=assignment):
                with self.assertRaises(ValueError):
                    scan_skc.apply_role_assignments(
                        inventory_with_one_file(), {"正面/1.jpg": assignment}
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

    def test_attached_evidence_is_trimmed_and_manifest_rejects_padded_evidence(self):
        string_fields = {
            "identity_profile": {
                "head_visibility": "partial",
                "skin_tone_and_visible_ancestry_cues": "warm medium-tan skin",
                "visible_face_features": "lower face visible",
                "hair_evidence": "dark brown loose strands",
                "age_impression": "adult, approximately 25-35",
                "body_profile": "slim adult build",
                "reason": "Visible evidence only",
            },
            "garment_profile": {
                "garment_type": "dress",
                "hem_position": "below_knee",
                "reason": "Hem extends below both knees.",
            },
        }

        for profile_key, fields in string_fields.items():
            for field, canonical in fields.items():
                with self.subTest(contract="attachment", field=field):
                    identity = valid_identity_profile()
                    garment = valid_garment_profile()
                    target = identity if profile_key == "identity_profile" else garment
                    target[field] = f" {canonical} "
                    try:
                        attached = scan_skc.attach_visual_contracts(
                            valid_inventory(), identity, garment
                        )
                    except ValueError as exc:
                        self.fail(f"attachment must normalize {field}: {exc}")
                    self.assertEqual(attached[profile_key][field], canonical)

                with self.subTest(contract="manifest", field=field):
                    attached = scan_skc.attach_visual_contracts(
                        valid_inventory(),
                        valid_identity_profile(),
                        valid_garment_profile(),
                    )
                    attached[profile_key][field] = f" {canonical} "
                    self.assertTrue(
                        validate_manifest.validate_manifest_data(attached)
                    )

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
