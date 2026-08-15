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
NEGATIVE_PROMPT_PREFIX = (
    "NEGATIVE PROMPT CONTRACT — reject only these defects: "
)
SHARED_NEGATIVE_DEFECTS = (
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


def canonical_negative_prompt(view, manifest):
    defects = list(SHARED_NEGATIVE_DEFECTS)
    if view == "full":
        defects.extend(
            (
                "any crop of hair crown/head/face/chin/neck/body/garment hem/ankles/feet/toes/shoes/soles",
                "missing safety margin above hair or below footwear",
                "wrong requested full view",
            )
        )
    else:
        defects.extend(
            (
                "less than a visible half head",
                "complete loss of the head",
                f"wrong requested {view} view",
                f"crop violations for the active {view} composition contract",
            )
        )
    if manifest["garment_profile"]["requires_full_garment_frame"]:
        defects.extend(
            (
                "cropped/obscured hem",
                "hem touching/crossing an image edge",
                "shortened apparent garment length",
                "interrupted shoulder-to-lowest-hem continuity",
            )
        )
    if "footwear_contract" in manifest["views"][view]:
        defects.append(
            "invented/changed/missing/cropped/obscured required footwear"
        )
    return NEGATIVE_PROMPT_PREFIX + "; ".join(defects)


def add_accessory(manifest, view, relative_path):
    manifest["views"][view]["files"].append({"relative_path": relative_path})
    manifest["views"][view]["roles"]["accessory_source"].append(relative_path)


def activate_full_footwear_contract(manifest):
    footwear_path = "全身/4.jpg"
    add_accessory(manifest, "full", footwear_path)
    manifest["views"]["full"]["footwear_contract"] = {
        "kind": "footwear",
        "source_paths": [footwear_path],
        "confidence": 0.96,
        "reason": "Visually confirmed required shoes",
    }


def valid_view(view):
    folder = {"front": "正面", "side": "侧面", "back": "背面", "full": "全身"}[view]
    paths = [f"{folder}/{index}.jpg" for index in range(1, 4)]
    return {
        "status": "ready",
        "files": [{"relative_path": path} for path in paths],
        "roles": {
            "model_source": [paths[0]],
            "product_source": [paths[1]],
            "scene_source": [paths[2]],
            "composition_source": [paths[0]],
            "accessory_source": [],
            "unused": [],
        },
    }


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
        "views": {
            view: valid_view(view) for view in ("front", "side", "back", "full")
        },
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
                "negative_prompt": canonical_negative_prompt(view, manifest),
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


class DeterministicNegativePromptContractTests(unittest.TestCase):
    def renderer(self):
        renderer = getattr(validate_manifest, "render_negative_prompt", None)
        self.assertTrue(
            callable(renderer),
            "validate_manifest must expose the production render_negative_prompt API",
        )
        return renderer

    def test_renderer_emits_the_exact_stable_order_for_local_and_full_views(self):
        manifest = valid_manifest()
        renderer = self.renderer()

        self.assertEqual(
            renderer(
                "front",
                manifest["identity_profile"],
                manifest["garment_profile"],
            ),
            canonical_negative_prompt("front", manifest),
        )

        activate_full_footwear_contract(manifest)
        self.assertEqual(
            renderer(
                {"name": "full", "footwear_required": True},
                manifest["identity_profile"],
                manifest["garment_profile"],
            ),
            canonical_negative_prompt("full", manifest),
        )

    def test_renderer_rejects_unsupported_views_and_malformed_contracts(self):
        manifest = valid_manifest()
        renderer = self.renderer()
        cases = (
            (
                "unsupported view",
                "three-quarter",
                manifest["identity_profile"],
                manifest["garment_profile"],
            ),
            (
                "malformed view contract",
                {"name": "full", "footwear_required": "yes"},
                manifest["identity_profile"],
                manifest["garment_profile"],
            ),
            (
                "malformed identity contract",
                "front",
                {"head_visibility": "partial"},
                manifest["garment_profile"],
            ),
            (
                "malformed garment contract",
                "front",
                manifest["identity_profile"],
                {
                    **manifest["garment_profile"],
                    "requires_full_garment_frame": 1,
                },
            ),
        )
        for defect, view, identity_contract, garment_contract in cases:
            with self.subTest(defect=defect):
                with self.assertRaises(ValueError):
                    renderer(view, identity_contract, garment_contract)

    def test_view_contract_derivation_requires_explicit_footwear_evidence(self):
        cases = []

        absent = valid_manifest()
        cases.append(("footwear absent", "full", absent, False))

        bag_only = valid_manifest()
        add_accessory(bag_only, "full", "全身/bag.jpg")
        cases.append(("full bag only", "full", bag_only, False))

        jewelry_only = valid_manifest()
        add_accessory(jewelry_only, "full", "全身/jewelry.jpg")
        cases.append(("full jewelry only", "full", jewelry_only, False))

        footwear_present = valid_manifest()
        activate_full_footwear_contract(footwear_present)
        cases.append(("footwear present", "full", footwear_present, True))

        for view, path in (
            ("front", "正面/bag.jpg"),
            ("side", "侧面/jewelry.jpg"),
            ("back", "背面/styling.jpg"),
        ):
            manifest = valid_manifest()
            add_accessory(manifest, view, path)
            cases.append((f"valid non-full {view} accessory", view, manifest, False))

        for defect, view, manifest, footwear_required in cases:
            with self.subTest(defect=defect):
                builder = getattr(
                    validate_manifest, "view_contract_from_manifest", None
                )
                self.assertTrue(
                    callable(builder),
                    "validator must expose explicit footwear view-contract derivation",
                )
                self.assertEqual(
                    builder(view, manifest["views"][view]),
                    {"name": view, "footwear_required": footwear_required},
                )

    def test_generic_accessories_never_activate_required_footwear_defects(self):
        cases = (
            ("full bag only", "full", "全身/bag.jpg"),
            ("full jewelry only", "full", "全身/jewelry.jpg"),
            ("front bag", "front", "正面/bag.jpg"),
            ("side jewelry", "side", "侧面/jewelry.jpg"),
            ("back other styling", "back", "背面/styling.jpg"),
        )
        for defect, view, accessory_path in cases:
            with self.subTest(defect=defect):
                manifest = valid_manifest()
                add_accessory(manifest, view, accessory_path)
                prompt = valid_prompt(view, manifest)

                self.assertNotIn(
                    "required footwear",
                    prompt["actions"][0]["negative_prompt"],
                )
                self.assertEqual(
                    validate_manifest.validate_manifest_data(manifest), []
                )
                self.assertEqual(
                    validate_manifest.validate_prompt_data(prompt, manifest), []
                )

    def test_omitted_optional_accessory_bucket_remains_footwear_inactive(self):
        manifest = valid_manifest()
        del manifest["views"]["full"]["roles"]["accessory_source"]
        prompt = valid_prompt("full", manifest)

        self.assertEqual(
            validate_manifest.view_contract_from_manifest(
                "full", manifest["views"]["full"]
            ),
            {"name": "full", "footwear_required": False},
        )
        self.assertEqual(validate_manifest.validate_manifest_data(manifest), [])
        self.assertEqual(
            validate_manifest.validate_prompt_data(prompt, manifest), []
        )

    def test_explicit_footwear_evidence_activates_the_required_footwear_defect(self):
        manifest = valid_manifest()
        activate_full_footwear_contract(manifest)
        prompt = valid_prompt("full", manifest)

        self.assertIn(
            "invented/changed/missing/cropped/obscured required footwear",
            prompt["actions"][0]["negative_prompt"],
        )
        self.assertEqual(validate_manifest.validate_manifest_data(manifest), [])
        self.assertEqual(
            validate_manifest.validate_prompt_data(prompt, manifest), []
        )

    def test_malformed_explicit_footwear_evidence_fails_closed(self):
        mutations = {
            "wrong kind": lambda contract: contract.update(kind="bag"),
            "empty sources": lambda contract: contract.update(source_paths=[]),
            "source not accessory": lambda contract: contract.update(
                source_paths=["全身/2.jpg"]
            ),
            "non-string source": lambda contract: contract.update(
                source_paths=[{}]
            ),
            "low confidence": lambda contract: contract.update(confidence=0.69),
            "boolean confidence": lambda contract: contract.update(confidence=True),
            "blank reason": lambda contract: contract.update(reason="   "),
            "unknown field": lambda contract: contract.update(extra=True),
        }
        for defect, mutate in mutations.items():
            with self.subTest(defect=defect):
                manifest = valid_manifest()
                activate_full_footwear_contract(manifest)
                mutate(manifest["views"]["full"]["footwear_contract"])

                errors = validate_manifest.validate_manifest_data(manifest)

                self.assertTrue(
                    any("footwear_contract" in error for error in errors),
                    errors,
                )

    def test_validator_rejects_every_noncanonical_negative_prompt_mutation(self):
        manifest = valid_manifest()
        canonical = canonical_negative_prompt("front", manifest)
        phrases = canonical.removeprefix(NEGATIVE_PROMPT_PREFIX).split("; ")
        reordered = (
            NEGATIVE_PROMPT_PREFIX
            + "; ".join((phrases[1], phrases[0], *phrases[2:]))
        )
        cases = {
            "legacy free form": "Do not alter the product.",
            "plausible paraphrase": (
                "Reject collages, extra people, identity changes, crop mistakes, "
                "and incorrect garments."
            ),
            "leading whitespace": " " + canonical,
            "trailing whitespace": canonical + " ",
            "reordered phrases": reordered,
            "appended phrase": canonical + "; extra defect",
            "removed phrase": canonical.replace("; multiple people", "", 1),
            "another view": canonical_negative_prompt("side", manifest),
        }
        for defect, negative_prompt in cases.items():
            with self.subTest(defect=defect):
                prompt = valid_prompt("front", manifest)
                prompt["actions"][0]["negative_prompt"] = negative_prompt

                errors = validate_manifest.validate_prompt_data(prompt, manifest)

                self.assertTrue(
                    any(
                        "render_negative_prompt output exactly" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_validator_binds_long_dress_phrases_to_the_active_manifest(self):
        long_manifest = valid_manifest()
        short_manifest = valid_manifest()
        short_manifest["garment_profile"] = {
            "garment_type": "shirt",
            "hem_position": "not_applicable",
            "requires_full_garment_frame": False,
            "reason": "Visible shirt evidence",
        }
        cases = (
            (
                "long prompt on inactive contract",
                short_manifest,
                canonical_negative_prompt("front", long_manifest),
            ),
            (
                "short prompt on active contract",
                long_manifest,
                canonical_negative_prompt("front", short_manifest),
            ),
        )
        for defect, manifest, negative_prompt in cases:
            with self.subTest(defect=defect):
                prompt = valid_prompt("front", manifest)
                prompt["actions"][0]["negative_prompt"] = negative_prompt

                self.assertTrue(
                    validate_manifest.validate_prompt_data(prompt, manifest),
                    defect,
                )

    def test_validator_binds_footwear_phrases_to_the_active_view_contract(self):
        inactive_manifest = valid_manifest()
        active_manifest = valid_manifest()
        activate_full_footwear_contract(active_manifest)
        cases = (
            (
                "footwear prompt on inactive contract",
                inactive_manifest,
                canonical_negative_prompt("full", active_manifest),
            ),
            (
                "non-footwear prompt on active contract",
                active_manifest,
                canonical_negative_prompt("full", inactive_manifest),
            ),
        )
        for defect, manifest, negative_prompt in cases:
            with self.subTest(defect=defect):
                prompt = valid_prompt("full", manifest)
                prompt["actions"][0]["negative_prompt"] = negative_prompt

                self.assertTrue(
                    validate_manifest.validate_prompt_data(prompt, manifest),
                    defect,
                )

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

    def test_manifest_requires_exact_views_files_and_resolvable_role_lists(self):
        mutations = {
            "missing view": lambda manifest: manifest["views"].pop("full"),
            "ghost view": lambda manifest: manifest["views"].update(
                ghost=valid_view("front")
            ),
            "files must be a list": lambda manifest: manifest["views"]["front"].update(
                files="正面/1.jpg"
            ),
            "file relative_path must be canonical": lambda manifest: manifest["views"][
                "front"
            ]["files"][0].update(relative_path=" 正面/1.jpg "),
            "role values must be lists": lambda manifest: manifest["views"]["front"][
                "roles"
            ].update(model_source="x"),
            "role path must exist in files": lambda manifest: manifest["views"]["front"][
                "roles"
            ].update(model_source=["正面/ghost.jpg"]),
        }

        for defect, mutate in mutations.items():
            with self.subTest(defect=defect):
                manifest = valid_manifest()
                mutate(manifest)
                self.assertTrue(
                    validate_manifest.validate_manifest_data(manifest), defect
                )


class PromptSubmissionGateTests(unittest.TestCase):
    def test_accepts_valid_schema_two_prompt(self):
        manifest = valid_manifest()
        self.assertEqual(
            validate_manifest.validate_prompt_data(valid_prompt(manifest=manifest), manifest),
            [],
        )

    def test_prompt_view_must_be_a_ready_view_in_the_active_manifest(self):
        cases = ("ghost", True, "blocked", "missing", "string manifest views")
        for defect in cases:
            with self.subTest(defect=defect):
                manifest = valid_manifest()
                prompt = valid_prompt("side", manifest)
                if defect == "ghost":
                    prompt["view"] = "ghost"
                elif defect is True:
                    prompt["view"] = True
                elif defect == "blocked":
                    manifest["views"]["side"]["status"] = "blocked:missing-view"
                elif defect == "string manifest views":
                    manifest["views"] = "side"
                else:
                    del manifest["views"]["side"]

                self.assertTrue(
                    validate_manifest.validate_prompt_data(prompt, manifest), defect
                )

    def test_prompt_text_fields_are_real_strings_and_negative_prompt_cannot_negate_locks(self):
        scalar_mutations = (
            ("analysis_markdown", None, True),
            ("title", 0, True),
            ("negative_prompt", 0, True),
        )
        for field, action_index, value in scalar_mutations:
            with self.subTest(field=field):
                manifest = valid_manifest()
                prompt = valid_prompt(manifest=manifest)
                target = prompt if action_index is None else prompt["actions"][action_index]
                target[field] = value
                self.assertTrue(
                    validate_manifest.validate_prompt_data(prompt, manifest), field
                )

        forbidden = (
            "Do not preserve canonical identity.",
            "Allow identity drift.",
            "No complete head.",
            "No half head.",
            "Without at least half of the model's head.",
            "No full-body framing.",
            "Crop below the half-head boundary.",
            "Do not keep the full garment visible.",
            "Ignore the IDENTITY LOCK.",
        )
        for negative_prompt in forbidden:
            with self.subTest(negative_prompt=negative_prompt):
                manifest = valid_manifest()
                prompt = valid_prompt(manifest=manifest)
                prompt["actions"][0]["negative_prompt"] = negative_prompt
                self.assertTrue(
                    validate_manifest.validate_prompt_data(prompt, manifest),
                    negative_prompt,
                )

        manifest = valid_manifest()
        prompt = valid_prompt("full", manifest)
        prompt["actions"][0]["negative_prompt"] = "Do not show shoes or soles."
        self.assertTrue(validate_manifest.validate_prompt_data(prompt, manifest))

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
