import copy
import importlib.util
import inspect
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "skill" / "scripts" / "validate_manifest.py"
STATE_PATH = ROOT / "skill" / "scripts" / "update_run_state.py"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


validate_manifest = load_module("final_review_validate_manifest", VALIDATOR_PATH)

VIEW_FOLDERS = {
    "front": "正面",
    "side": "侧面",
    "back": "背面",
    "full": "全身",
}
PREFIXES = {"front": "FR", "side": "SI", "back": "BA", "full": "FU"}
CANONICAL_SOURCE = {"relative_path": "正面/1.jpg", "sha256": "a" * 64}
NEGATIVE_PREFIX = "NEGATIVE PROMPT CONTRACT — reject only these defects: "
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


def scanner_record(path, role, hash_character, confidence=0.95):
    return {
        "name": Path(path).name,
        "relative_path": path,
        "sha256": hash_character * 64,
        "size_bytes": 128,
        "role": role,
        "confidence": confidence,
        "reason": f"Visually confirmed {role}",
        "duplicate_group": None,
    }


def valid_view(view):
    folder = VIEW_FOLDERS[view]
    hash_characters = {
        "front": ("a", "b", "c"),
        "side": ("d", "e", "f"),
        "back": ("1", "2", "3"),
        "full": ("4", "5", "6"),
    }[view]
    records = [
        scanner_record(f"{folder}/1.jpg", "model_source", hash_characters[0]),
        scanner_record(f"{folder}/2.jpg", "product_source", hash_characters[1]),
        scanner_record(f"{folder}/3.jpg", "scene_source", hash_characters[2]),
    ]
    return {
        "folder": folder,
        "status": "ready",
        "files": records,
        "roles": {
            "model_source": [records[0]["relative_path"]],
            "product_source": [records[1]["relative_path"]],
            "scene_source": [records[2]["relative_path"]],
            "composition_source": [records[0]["relative_path"]],
            "accessory_source": [],
            "unused": [],
        },
        "composition_fallback": "model_source",
        "blockers": [],
    }


def valid_manifest():
    return {
        "schema_version": 2,
        "skc_id": "ds-final-review",
        "skc_path": "/tmp/ds-final-review",
        "canonical_identity_source": copy.deepcopy(CANONICAL_SOURCE),
        "identity_profile": {
            "canonical_source": copy.deepcopy(CANONICAL_SOURCE),
            "head_visibility": "partial",
            "skin_tone_and_visible_ancestry_cues": "warm medium-tan skin",
            "visible_face_features": "lower face visible",
            "hair_evidence": "dark brown loose strands",
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
        "views": {view: valid_view(view) for view in VIEW_FOLDERS},
    }


def file_binding(manifest, view, relative_path):
    record = next(
        item
        for item in manifest["views"][view]["files"]
        if item["relative_path"] == relative_path
    )
    return {"relative_path": relative_path, "sha256": record["sha256"]}


def source_bindings(manifest, view):
    roles = manifest["views"][view]["roles"]
    bindings = {
        "identity": copy.deepcopy(manifest["canonical_identity_source"]),
        "product": file_binding(manifest, view, roles["product_source"][0]),
        "scene": file_binding(manifest, view, roles["scene_source"][0]),
        "pose_composition": file_binding(
            manifest, view, roles["composition_source"][0]
        ),
    }
    footwear = manifest["views"][view].get("footwear_contract")
    if footwear is not None:
        bindings["footwear"] = [
            file_binding(manifest, view, path) for path in footwear["source_paths"]
        ]
    return bindings


def terminal_suffix(manifest, view):
    profile = manifest["identity_profile"]
    identity_lock = (
        "IDENTITY LOCK: canonical_source=正面/1.jpg; "
        f"head_visibility={profile['head_visibility']}; "
        "skin_tone_and_visible_ancestry_cues="
        f"{profile['skin_tone_and_visible_ancestry_cues']}; "
        f"visible_face_features={profile['visible_face_features']}; "
        f"hair_evidence={profile['hair_evidence']}; "
        f"age_impression={profile['age_impression']}; "
        f"body_profile={profile['body_profile']}; "
        "Noncanonical local pose/composition sources must not control or override "
        "body_profile."
    )
    if view == "full":
        framing = (
            "FULL-BODY HEAD COMPLETION: Even when 正面/1.jpg shows a partial head "
            "or no head, reconstruct a natural complete head using only the visible "
            "skin tone, ancestry cues, partial facial evidence, hair evidence, age "
            "impression, neck/shoulder evidence, and body profile. Do not change "
            "the model's visible identity characteristics."
        )
    else:
        framing = (
            "HEAD CROP FLOOR: The final image must retain at least half of the "
            "model's head. A complete head is allowed. Never crop below the "
            "half-head boundary."
        )
    blocks = [
        (
            "FINAL CONTRACT OVERRIDE: In any conflict, the following identity, "
            "head-crop, full-body, and garment contracts override every earlier "
            "sentence in this prompt."
        ),
        identity_lock,
        framing,
    ]
    if manifest["garment_profile"]["requires_full_garment_frame"]:
        blocks.append(
            "GARMENT FRAME LOCK: Activate only for a visually confirmed below-knee "
            "dress; when active, keep the dress continuously visible from the "
            "shoulder/neckline through the lowest hem point; leave visible safety "
            "margin below the hem; the hem must not touch or cross an image edge; "
            "keep the major hem silhouette unobscured; keep the apparent garment "
            "length unchanged."
        )
    return " ".join(blocks)


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
    return NEGATIVE_PREFIX + "; ".join(defects)


def action_directives(view, index):
    return {
        "action": f"Perform distinct {view} ecommerce action {index}",
        "camera": f"Use camera setup {index} for the requested {view} view",
        "composition": f"Compose action {index} with the complete product visible",
        "scene": f"Extend the bound scene coherently for action {index}",
    }


def expected_positive_prompt(manifest, view, action):
    bindings = action["source_bindings"]
    directives = action["action_directives"]
    parts = [
        (
            f"SKC {manifest['skc_id']} | VIEW {view} | ACTION "
            f"{action['action_id']} | ATTEMPT {action['attempt']}."
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
    parts.extend(
        (
            "Generate with Nano Banana Pro, 4K, 2:3.",
            terminal_suffix(manifest, view),
        )
    )
    return " ".join(parts)


def valid_prompt(view="front", manifest=None):
    manifest = manifest or valid_manifest()
    prefix = PREFIXES[view]
    actions = []
    for index in range(1, 6):
        action = {
            "action_id": f"{prefix}{index:02d}",
            "attempt": 1,
            "title": f"Distinct {view} action {index}",
            "source_bindings": source_bindings(manifest, view),
            "action_directives": action_directives(view, index),
            "correction": None,
            "negative_prompt": canonical_negative_prompt(view, manifest),
        }
        action["prompt_en"] = expected_positive_prompt(manifest, view, action)
        actions.append(action)
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
        "actions": actions,
    }


def retry_run_state(manifest, view="front"):
    prefix = PREFIXES[view]
    actions = {}
    for index in range(1, 6):
        action_id = f"{prefix}{index:02d}"
        actions[action_id] = {
            "status": "pending",
            "attempts": 0,
            "attempt_history": [],
        }
    action = actions[f"{prefix}01"]
    action.update(status="rejected", attempts=1)
    action["attempt_history"] = [
        {
            "attempt": 1,
            "task_label": (
                f"SKC {manifest['skc_id']} | VIEW {view} | ACTION {prefix}01 | "
                "ATTEMPT 1"
            ),
        }
    ]
    return {
        "skc_id": manifest["skc_id"],
        "views": {view: {"actions": actions}},
    }


class ScannerEvidenceContractTests(unittest.TestCase):
    def test_canonical_identity_hash_and_path_must_match_the_front_scanner_record(self):
        mismatch = valid_manifest()
        mismatch["canonical_identity_source"]["sha256"] = "b" * 64
        mismatch["identity_profile"]["canonical_source"]["sha256"] = "b" * 64
        self.assertTrue(validate_manifest.validate_manifest_data(mismatch))

        missing = valid_manifest()
        front = missing["views"]["front"]
        replacement = scanner_record("正面/4.jpg", "model_source", "7")
        front["files"][0] = replacement
        front["roles"]["model_source"] = [replacement["relative_path"]]
        front["roles"]["composition_source"] = [replacement["relative_path"]]
        self.assertTrue(validate_manifest.validate_manifest_data(missing))

    def test_ready_role_evidence_requires_strict_scanner_metadata(self):
        mutations = {
            "missing sha256": lambda record: record.pop("sha256"),
            "missing role": lambda record: record.pop("role"),
            "wrong role": lambda record: record.update(role="unused"),
            "boolean confidence": lambda record: record.update(confidence=True),
            "low confidence": lambda record: record.update(confidence=0.69),
            "blank reason": lambda record: record.update(reason="   "),
        }
        for defect, mutate in mutations.items():
            with self.subTest(defect=defect):
                manifest = valid_manifest()
                mutate(manifest["views"]["front"]["files"][1])
                self.assertTrue(validate_manifest.validate_manifest_data(manifest))

    def test_role_lists_must_obey_primary_cardinality_and_only_legal_fallback_overlap(self):
        collapsed = valid_manifest()
        roles = collapsed["views"]["front"]["roles"]
        for role in ("model_source", "product_source", "scene_source", "composition_source"):
            roles[role] = ["正面/1.jpg"]
        self.assertTrue(validate_manifest.validate_manifest_data(collapsed))

        illegal_overlap = valid_manifest()
        roles = illegal_overlap["views"]["side"]["roles"]
        roles["scene_source"] = list(roles["product_source"])
        self.assertTrue(validate_manifest.validate_manifest_data(illegal_overlap))

    def test_role_membership_validation_does_not_depend_on_json_object_order(self):
        manifest = valid_manifest()
        front = manifest["views"]["front"]
        front["roles"] = {
            key: front["roles"][key]
            for key in (
                "composition_source",
                "unused",
                "scene_source",
                "accessory_source",
                "product_source",
                "model_source",
            )
        }

        self.assertEqual(validate_manifest.validate_manifest_data(manifest), [])

    def test_schema_version_is_strict_json_integer_two(self):
        for value in (2.0, True, "2"):
            with self.subTest(value=value):
                manifest = valid_manifest()
                prompt = valid_prompt(manifest=manifest)
                manifest["schema_version"] = value
                prompt["schema_version"] = value
                self.assertTrue(validate_manifest.validate_manifest_data(manifest))
                self.assertTrue(
                    validate_manifest.validate_prompt_data(prompt, valid_manifest())
                )


class DeterministicPositivePromptContractTests(unittest.TestCase):
    def test_positive_renderer_uses_typed_sources_and_distinct_action_directives(self):
        renderer = getattr(validate_manifest, "render_positive_prompt", None)
        self.assertTrue(callable(renderer), "render_positive_prompt must exist")
        if not callable(renderer):
            return

        manifest = valid_manifest()
        prompt = valid_prompt(manifest=manifest)
        rendered = [
            renderer(manifest["skc_id"], "front", action, manifest)
            for action in prompt["actions"]
        ]
        self.assertEqual(
            rendered,
            [action["prompt_en"] for action in prompt["actions"]],
        )
        self.assertEqual(len(set(rendered)), 5)

    def test_lock_only_clones_and_missing_typed_execution_fields_fail(self):
        manifest = valid_manifest()
        prompt = valid_prompt(manifest=manifest)
        clone = copy.deepcopy(prompt["actions"][0]["action_directives"])
        for action in prompt["actions"]:
            action["action_directives"] = copy.deepcopy(clone)
            action["title"] = "x"
            action["prompt_en"] = expected_positive_prompt(manifest, "front", action)
        self.assertTrue(validate_manifest.validate_prompt_data(prompt, manifest))

        for field, nested in (
            ("source_bindings", "product"),
            ("source_bindings", "pose_composition"),
            ("action_directives", "action"),
            ("action_directives", "camera"),
            ("action_directives", "composition"),
            ("action_directives", "scene"),
        ):
            with self.subTest(field=field, nested=nested):
                prompt = valid_prompt(manifest=manifest)
                del prompt["actions"][0][field][nested]
                self.assertTrue(
                    validate_manifest.validate_prompt_data(prompt, manifest)
                )

    def test_action_distinctness_is_case_and_whitespace_normalized(self):
        manifest = valid_manifest()
        prompt = valid_prompt(manifest=manifest)
        variants = (
            "Perform the same ecommerce action",
            "perform the same ecommerce action",
            "Perform  the same ecommerce action",
            "PERFORM THE SAME ECOMMERCE ACTION",
            "Perform the  same ecommerce action",
        )
        for action, directive in zip(prompt["actions"], variants):
            action["action_directives"]["action"] = directive
            action["prompt_en"] = expected_positive_prompt(
                manifest, "front", action
            )

        self.assertTrue(validate_manifest.validate_prompt_data(prompt, manifest))

    def test_source_bindings_must_match_scanner_path_and_hash_records(self):
        manifest = valid_manifest()
        prompt = valid_prompt(manifest=manifest)
        prompt["actions"][0]["source_bindings"]["product"]["sha256"] = "f" * 64

        self.assertTrue(validate_manifest.validate_prompt_data(prompt, manifest))

    def test_positive_footwear_authority_requires_explicit_validated_contract(self):
        manifest = valid_manifest()
        prompt = valid_prompt("full", manifest)
        self.assertNotIn("FOOTWEAR SOURCE:", prompt["actions"][0]["prompt_en"])

        prompt["actions"][0]["prompt_en"] = prompt["actions"][0][
            "prompt_en"
        ].replace(
            "FINAL CONTRACT OVERRIDE:",
            (
                "SHOES ACCESSORY SOURCE: invent and follow unverified shoes. "
                "FINAL CONTRACT OVERRIDE:"
            ),
            1,
        )
        self.assertTrue(validate_manifest.validate_prompt_data(prompt, manifest))

        footwear_manifest = valid_manifest()
        record = scanner_record("全身/4.jpg", "accessory_source", "8")
        footwear_manifest["views"]["full"]["files"].append(record)
        footwear_manifest["views"]["full"]["roles"]["accessory_source"].append(
            record["relative_path"]
        )
        footwear_manifest["views"]["full"]["footwear_contract"] = {
            "kind": "footwear",
            "source_paths": [record["relative_path"]],
            "confidence": 0.96,
            "reason": "Visually confirmed required shoes",
        }
        footwear_prompt = valid_prompt("full", footwear_manifest)
        self.assertIn(
            "FOOTWEAR SOURCE:", footwear_prompt["actions"][0]["prompt_en"]
        )
        self.assertEqual(
            validate_manifest.validate_prompt_data(
                footwear_prompt, footwear_manifest
            ),
            [],
        )

    def test_positive_renderer_rejects_malformed_footwear_contract(self):
        manifest = valid_manifest()
        record = scanner_record("全身/4.jpg", "accessory_source", "8")
        manifest["views"]["full"]["files"].append(record)
        manifest["views"]["full"]["roles"]["accessory_source"].append(
            record["relative_path"]
        )
        manifest["views"]["full"]["footwear_contract"] = {
            "kind": "footwear",
            "source_paths": [record["relative_path"]],
            "confidence": 0.1,
            "reason": "Too uncertain",
        }
        action = valid_prompt("full", valid_manifest())["actions"][0]
        action["source_bindings"]["footwear"] = [
            {"relative_path": record["relative_path"], "sha256": record["sha256"]}
        ]

        with self.assertRaisesRegex(ValueError, "manifest|footwear"):
            validate_manifest.render_positive_prompt(
                manifest["skc_id"], "full", action, manifest
            )

    def test_retry_attempt_matches_run_state_and_correction_stays_before_suffix(self):
        parameters = inspect.signature(
            validate_manifest.validate_prompt_data
        ).parameters
        self.assertIn("active_run_state", parameters)
        if "active_run_state" not in parameters:
            return

        manifest = valid_manifest()
        run_state = retry_run_state(manifest)
        prompt = valid_prompt(manifest=manifest)
        retry = prompt["actions"][0]
        retry["attempt"] = 2
        retry["correction"] = {
            "fix": "restore the complete long-dress hem",
            "preserve": "the accepted identity product scene pose and camera",
        }
        retry["prompt_en"] = expected_positive_prompt(manifest, "front", retry)

        self.assertEqual(
            validate_manifest.validate_prompt_data(
                prompt, manifest, active_run_state=run_state
            ),
            [],
        )

        stale_state = retry_run_state(manifest)
        stale_state["views"]["front"]["actions"]["FR01"].update(
            status="pending", attempts=0, attempt_history=[]
        )
        self.assertTrue(
            validate_manifest.validate_prompt_data(
                prompt, manifest, active_run_state=stale_state
            )
        )

        prompt["actions"][0]["prompt_en"] += (
            " CORRECTION FOR ATTEMPT 2: placed after the terminal suffix."
        )
        self.assertTrue(
            validate_manifest.validate_prompt_data(
                prompt, manifest, active_run_state=run_state
            )
        )

    def test_attempt_is_a_strict_positive_json_integer(self):
        manifest = valid_manifest()
        for value in (True, 1.0, "1", 0):
            with self.subTest(value=value):
                prompt = valid_prompt(manifest=manifest)
                prompt["actions"][0]["attempt"] = value
                self.assertTrue(
                    validate_manifest.validate_prompt_data(prompt, manifest)
                )

    def test_malformed_retry_history_fails_closed_without_crashing(self):
        manifest = valid_manifest()
        prompt = valid_prompt(manifest=manifest)
        action = prompt["actions"][0]
        action["attempt"] = 2
        action["correction"] = {
            "fix": "Restore the verified hem framing",
            "preserve": "Keep identity product scene and action unchanged",
        }
        action["prompt_en"] = expected_positive_prompt(manifest, "front", action)
        state = retry_run_state(manifest)
        run_action = state["views"]["front"]["actions"]["FR01"]
        run_action.update(status="submitted", attempts=2, attempt_history=None)

        self.assertTrue(
            validate_manifest.validate_prompt_data(prompt, manifest, state)
        )


def verified_execution_context():
    return {
        "source_path": "/Users/chenyiming/Desktop/8月/8月14日",
        "expected_month_project": "8月",
        "date_region": "8月14日",
        "verified_month_project": "8月",
        "project_verification_status": "verified",
        "blocker": None,
        "feedback_required": False,
        "feedback_message": None,
        "feedback_sent_at": None,
    }


def state_with_views(module, skc_id="ds-final-review", views=("front",)):
    state = module.initialize_state(
        {
            "skc_id": skc_id,
            "views": {view: {"status": "ready"} for view in views},
        },
        verified_execution_context(),
    )
    module.record_layout_reservation(
        state,
        date_region="8月14日",
        skc_label=f"{skc_id} · V2测试",
        verified=True,
    )
    return state


def task_label(state, view, action_id, attempt):
    return (
        f"SKC {state['skc_id']} | VIEW {view} | ACTION {action_id} | "
        f"ATTEMPT {attempt}"
    )


def batch_context(*states):
    return {
        "schema_version": 1,
        "skc_ids": [state["skc_id"] for state in states],
        "states": list(states),
    }


def submission_kwargs(module, *states):
    if "batch_context" not in inspect.signature(module.transition_action).parameters:
        return {}
    return {"batch_context": batch_context(*states)}


def submit(module, state, view, action_id, *batch_states, label=None):
    action = state["views"][view]["actions"][action_id]
    attempt = action["attempts"] + 1
    states = batch_states or (state,)
    return module.transition_action(
        state,
        view,
        action_id,
        "submitted",
        task_label=label or task_label(state, view, action_id, attempt),
        **submission_kwargs(module, *states),
    )


def record_result(module, state, view, action_id, artifact_id):
    action = state["views"][view]["actions"][action_id]
    attempt = action["attempts"]
    label = task_label(state, view, action_id, attempt)
    return module.transition_action(
        state,
        view,
        action_id,
        "generated",
        task_label=label,
        artifact_id=artifact_id,
    )


def review_ready_state(module):
    state = state_with_views(
        module,
        views=("front", "side", "back", "full"),
    )
    for view, prefix in PREFIXES.items():
        for index in range(1, 6):
            action_id = f"{prefix}{index:02d}"
            submit(module, state, view, action_id)
            record_result(
                module,
                state,
                view,
                action_id,
                f"review-artifact-{view}-{index}",
            )
            module.place_attempt(
                state,
                view,
                action_id,
                1,
                area="primary",
                slot=index,
                verified=True,
            )
    assert module.evaluate_review_gate(state)["review_allowed"]
    return state


class RunStateFinalReviewContractTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module("final_review_update_run_state", STATE_PATH)

    def test_submission_requires_explicit_complete_batch_context(self):
        self.assertIn(
            "batch_context",
            inspect.signature(self.module.transition_action).parameters,
        )
        state = state_with_views(self.module)
        with self.assertRaisesRegex(ValueError, "batch context"):
            self.module.transition_action(
                state,
                "front",
                "FR01",
                "submitted",
                task_label=task_label(state, "front", "FR01", 1),
            )

    def test_batch_context_must_cover_each_declared_skc_exactly_once(self):
        parameters = inspect.signature(self.module.transition_action).parameters
        self.assertIn("batch_context", parameters)
        if "batch_context" not in parameters:
            return
        current = state_with_views(self.module, "ds-current")
        other = state_with_views(self.module, "ds-other")
        incomplete = {
            "schema_version": 1,
            "skc_ids": ["ds-current", "ds-other"],
            "states": [current],
        }

        with self.assertRaisesRegex(ValueError, "batch context"):
            self.module.transition_action(
                current,
                "front",
                "FR01",
                "submitted",
                task_label=task_label(current, "front", "FR01", 1),
                batch_context=incomplete,
            )

    def test_global_unfinished_limit_counts_every_skc_in_the_batch(self):
        first = state_with_views(
            self.module, "ds-first", views=("front", "side")
        )
        second = state_with_views(self.module, "ds-second", views=("back",))
        states = (first, second)
        for view in ("front", "side"):
            prefix = PREFIXES[view]
            for index in range(1, 6):
                submit(
                    self.module,
                    first,
                    view,
                    f"{prefix}{index:02d}",
                    *states,
                )

        with self.assertRaisesRegex(ValueError, "global unfinished limit"):
            submit(self.module, second, "back", "BA01", *states)

    def test_every_batch_state_must_have_consistent_verified_project_evidence(self):
        current = state_with_views(self.module, "ds-current")
        other = state_with_views(self.module, "ds-other")
        other["execution_context"]["verified_month_project"] = "7月"

        with self.assertRaisesRegex(ValueError, "batch context|month project"):
            submit(self.module, current, "front", "FR01", current, other)

        current = state_with_views(self.module, "ds-current")
        malformed = state_with_views(self.module, "ds-other")
        malformed["views"] = {}
        with self.assertRaisesRegex(ValueError, "batch context|run-state"):
            submit(self.module, current, "front", "FR01", current, malformed)

    def test_project_evidence_and_task_label_must_be_internally_canonical(self):
        mismatched = state_with_views(self.module)
        mismatched["execution_context"].update(
            expected_month_project="8月",
            verified_month_project="7月",
            project_verification_status="verified",
        )
        with self.assertRaisesRegex(ValueError, "month project"):
            submit(self.module, mismatched, "front", "FR01")

        arbitrary_label = state_with_views(self.module)
        with self.assertRaisesRegex(ValueError, "task label"):
            submit(
                self.module,
                arbitrary_label,
                "front",
                "FR01",
                label="anything",
            )

    def test_result_must_exist_with_canonical_unique_identity_before_placement(self):
        state = state_with_views(self.module)
        submit(self.module, state, "front", "FR01")
        with self.assertRaisesRegex(ValueError, "result"):
            self.module.place_attempt(
                state,
                "front",
                "FR01",
                1,
                area="primary",
                slot=1,
                verified=True,
            )

        record_result(self.module, state, "front", "FR01", "artifact-fr01")
        self.module.place_attempt(
            state,
            "front",
            "FR01",
            1,
            area="primary",
            slot=1,
            verified=True,
        )
        submit(self.module, state, "front", "FR02")
        with self.assertRaisesRegex(ValueError, "artifact"):
            record_result(self.module, state, "front", "FR02", "artifact-fr01")

    def test_generated_and_quality_transitions_require_canonical_artifact_flow(self):
        wrong_label = state_with_views(self.module)
        with self.assertRaisesRegex(ValueError, "task label"):
            submit(
                self.module,
                wrong_label,
                "front",
                "FR01",
                label="wrong",
            )

        direct_quality = state_with_views(self.module)
        submit(self.module, direct_quality, "front", "FR01")
        with self.assertRaisesRegex(ValueError, "invalid transition"):
            self.module.transition_action(
                direct_quality, "front", "FR01", "qualified"
            )

        before_review = state_with_views(self.module)
        submit(self.module, before_review, "front", "FR01")
        record_result(
            self.module,
            before_review,
            "front",
            "FR01",
            "artifact-before-review",
        )
        self.module.place_attempt(
            before_review,
            "front",
            "FR01",
            1,
            area="primary",
            slot=1,
            verified=True,
        )
        with self.assertRaisesRegex(ValueError, "review gate"):
            self.module.transition_action(
                before_review, "front", "FR01", "qualified"
            )

        padded_artifact = state_with_views(self.module)
        submit(self.module, padded_artifact, "front", "FR01")
        with self.assertRaisesRegex(ValueError, "artifact"):
            record_result(
                self.module,
                padded_artifact,
                "front",
                "FR01",
                " padded-artifact ",
            )

    def test_quality_review_rejects_malformed_nonprimary_current_placement(self):
        state = review_ready_state(self.module)
        placement = state["views"]["front"]["actions"]["FR01"]["canvas"][
            "placements"
        ][0]
        placement.update(area="supplemental", slot=6, row_slot=6)

        with self.assertRaisesRegex(ValueError, "verified canvas placement"):
            self.module.transition_action(
                state, "front", "FR01", "qualified"
            )

    def test_review_gate_rejects_duplicate_base_artifacts(self):
        state = state_with_views(
            self.module,
            views=("front", "side", "back", "full"),
        )
        for view, prefix in PREFIXES.items():
            for index in range(1, 6):
                action_id = f"{prefix}{index:02d}"
                submit(self.module, state, view, action_id)
                record_result(
                    self.module,
                    state,
                    view,
                    action_id,
                    f"artifact-{view}-{index}",
                )
                self.module.place_attempt(
                    state,
                    view,
                    action_id,
                    1,
                    area="primary",
                    slot=index,
                    verified=True,
                )
        for view in state["views"].values():
            for action in view["actions"].values():
                action["attempt_history"][0]["artifact_id"] = "same-artifact"

        gate = self.module.evaluate_review_gate(state)

        self.assertFalse(gate["review_allowed"])
        self.assertNotEqual(gate["status"], "ready")

    def test_review_gate_fails_closed_on_malformed_legacy_attempt_records(self):
        for malformed_history in ([None], None):
            with self.subTest(malformed_history=malformed_history):
                state = state_with_views(
                    self.module,
                    views=("front", "side", "back", "full"),
                )
                state["views"]["front"]["actions"]["FR01"][
                    "attempt_history"
                ] = malformed_history

                gate = self.module.evaluate_review_gate(state)

                self.assertFalse(gate["review_allowed"])

    def test_completion_requires_a_verified_twenty_base_review_gate(self):
        state = state_with_views(
            self.module,
            views=("front", "side", "back", "full"),
        )
        for view, prefix in PREFIXES.items():
            for index in range(1, 6):
                action_id = f"{prefix}{index:02d}"
                action = state["views"][view]["actions"][action_id]
                action.update(status="qualified", attempts=1)
                action["attempt_history"] = [
                    {
                        "attempt": 1,
                        "task_label": task_label(state, view, action_id, 1),
                        "artifact_id": f"artifact-{view}-{index}",
                        "result_recorded_at": "2026-08-16T00:00:00+00:00",
                        "result_status": "generated",
                    }
                ]
                action["canvas"]["placements"] = [
                    {
                        "attempt": 1,
                        "area": "primary",
                        "slot": index,
                        "row_slot": index,
                        "verified": True,
                        "placement_status": "verified",
                    }
                ]
        self.module._recompute_state(state)
        self.assertNotEqual(state["status"], "completed")

        gate = self.module.evaluate_review_gate(state)
        self.assertTrue(gate["review_allowed"])
        self.module._recompute_state(state)
        self.assertEqual(state["status"], "completed")

        state["views"]["front"]["actions"]["FR01"]["attempt_history"][0][
            "artifact_id"
        ] = ""
        self.module._recompute_state(state)
        self.assertNotEqual(state["status"], "completed")

    def test_attempt_and_slots_are_strict_integers_with_fixed_zones(self):
        state = state_with_views(self.module)
        submit(self.module, state, "front", "FR01")
        record_result(self.module, state, "front", "FR01", "artifact-fr01")
        for attempt, slot in ((True, True), (1.0, 1.0)):
            with self.subTest(attempt=attempt, slot=slot):
                with self.assertRaisesRegex(ValueError, "integer"):
                    self.module.place_attempt(
                        state,
                        "front",
                        "FR01",
                        attempt,
                        area="primary",
                        slot=slot,
                        verified=True,
                    )

        with self.assertRaisesRegex(ValueError, "supplemental.*6.*10"):
            self.module.place_attempt(
                state,
                "front",
                "FR01",
                1,
                area="supplemental",
                slot=1,
                verified=True,
            )

    def test_supplemental_slots_reject_cross_action_collisions(self):
        state = state_with_views(self.module)
        view = state["views"]["front"]
        view["supplemental_limit"] = 10
        for index in (1, 2):
            action_id = f"FR{index:02d}"
            action = view["actions"][action_id]
            action.update(status="generated", attempts=2)
            action["attempt_history"] = [
                {
                    "attempt": attempt,
                    "task_label": task_label(state, "front", action_id, attempt),
                    "artifact_id": f"artifact-{action_id}-{attempt}",
                    "result_recorded_at": "2026-08-16T00:00:00+00:00",
                    "result_status": "generated",
                }
                for attempt in (1, 2)
            ]
            action["canvas"]["placements"] = [
                {
                    "attempt": 1,
                    "area": "primary",
                    "slot": index,
                    "row_slot": index,
                    "verified": True,
                    "placement_status": "verified",
                }
            ]

        later = view["actions"]["FR01"]["attempt_history"][1]
        canonical_later_label = later["task_label"]
        later["task_label"] = "wrong"
        with self.assertRaisesRegex(ValueError, "later returned attempt"):
            self.module.place_attempt(
                state,
                "front",
                "FR01",
                1,
                area="supplemental",
                slot=6,
                verified=True,
            )
        later["task_label"] = canonical_later_label

        self.module.place_attempt(
            state,
            "front",
            "FR01",
            1,
            area="supplemental",
            slot=6,
            verified=True,
        )
        with self.assertRaisesRegex(ValueError, "occupied"):
            self.module.place_attempt(
                state,
                "front",
                "FR02",
                1,
                area="supplemental",
                slot=6,
                verified=True,
            )

    def test_invalid_transition_arguments_do_not_upgrade_or_mutate_legacy_state(self):
        state = state_with_views(self.module)
        del state["views"]["front"]["generated_count"]
        before = copy.deepcopy(state)

        with self.assertRaisesRegex(ValueError, "unknown quality reason code"):
            self.module.transition_action(
                state,
                "front",
                "FR01",
                "submitted",
                reason_code="unknown",
            )

        self.assertEqual(state, before)

    def test_malformed_legacy_history_is_rejected_before_submission_mutation(self):
        state = state_with_views(self.module)
        action = state["views"]["front"]["actions"]["FR01"]
        action["attempt_history"] = None
        before = copy.deepcopy(state)

        with self.assertRaisesRegex(ValueError, "attempt_history"):
            submit(self.module, state, "front", "FR01")

        self.assertEqual(state, before)


if __name__ == "__main__":
    unittest.main()
