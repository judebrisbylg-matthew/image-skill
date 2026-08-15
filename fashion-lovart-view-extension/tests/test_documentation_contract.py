import copy
import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skill" / "SKILL.md"
LOVART = ROOT / "skill" / "references" / "lovart-execution.md"
FOLDER = ROOT / "skill" / "references" / "folder-contract.md"
PROMPT_SCHEMA = ROOT / "skill" / "references" / "prompt-output-schema.md"
README = ROOT / "README.md"
HANDBOOK = ROOT / "docs" / "handbook.html"
SITE_INDEX = ROOT.parent / "docs" / "index.html"
BUILDER = ROOT / "tools" / "build_handbook.mjs"
HANDBOOK_TEMPLATE = ROOT / "tools" / "handbook-template.html"
TEMPLATES = {
    view: ROOT / "skill" / "references" / "templates" / f"{view}.md"
    for view in ("front", "side", "back", "full")
}
VALIDATOR_SCRIPT = ROOT / "skill" / "scripts" / "validate_manifest.py"

VALIDATOR_SPEC = importlib.util.spec_from_file_location(
    "validate_manifest_for_documentation_tests", VALIDATOR_SCRIPT
)
validate_manifest = importlib.util.module_from_spec(VALIDATOR_SPEC)
assert VALIDATOR_SPEC.loader is not None
VALIDATOR_SPEC.loader.exec_module(validate_manifest)

CANONICAL_SOURCE = {"relative_path": "正面/1.jpg", "sha256": "a" * 64}
IDENTITY_FIELDS = (
    "head_visibility",
    "skin_tone_and_visible_ancestry_cues",
    "visible_face_features",
    "hair_evidence",
    "age_impression",
    "body_profile",
)


def representative_view(view):
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


def representative_manifest(head_visibility, *, long_dress):
    return {
        "schema_version": 2,
        "skc_id": "ds-doc-test",
        "canonical_identity_source": copy.deepcopy(CANONICAL_SOURCE),
        "identity_profile": {
            "canonical_source": copy.deepcopy(CANONICAL_SOURCE),
            "head_visibility": head_visibility,
            "skin_tone_and_visible_ancestry_cues": "warm medium-tan skin",
            "visible_face_features": "lower face visible",
            "hair_evidence": "dark brown loose strands",
            "age_impression": "adult 25-35",
            "body_profile": "slim adult build",
            "confidence": 0.86,
            "reason": "Visible evidence only",
        },
        "garment_profile": {
            "garment_type": "dress" if long_dress else "shirt",
            "hem_position": "below_knee" if long_dress else "not_applicable",
            "requires_full_garment_frame": long_dress,
            "reason": "Visible product evidence",
        },
        "views": {
            view: representative_view(view)
            for view in ("front", "side", "back", "full")
        },
    }


def scanner_inventory():
    return {
        "schema_version": 1,
        "skc_id": "ds-doc-test",
        "skc_path": "/tmp/ds-doc-test",
        "canonical_identity_source": copy.deepcopy(CANONICAL_SOURCE),
        "views": {
            view: {
                "status": "blocked:missing-view",
                "files": [],
                "roles": {},
                "composition_fallback": None,
                "blockers": ["missing view folder or supported images"],
            }
            for view in ("front", "side", "back", "full")
        },
    }


def documented_migration_snippet():
    skill = SKILL.read_text(encoding="utf-8")
    section = skill.split(
        "Invoke the schema migration in this order after visual classification:", 1
    )[1]
    match = re.search(r"```python\n(.*?)\n```", section, flags=re.DOTALL)
    if match is None:
        raise AssertionError("documented Python migration snippet is missing")
    return match.group(1)


def template_action_texts(view):
    source = TEMPLATES[view].read_text(encoding="utf-8")
    if view == "full":
        actions = [
            line for line in source.splitlines() if line.startswith("Generate one ")
        ]
    else:
        actions = [
            line
            for line in source.splitlines()
            if re.match(r"^[1-5]\. \*\*", line)
        ]
    if len(actions) != 5:
        raise AssertionError(f"{view} template must expose exactly five actions")
    return actions


def render_template_prompt(view, manifest):
    prefix = {"front": "FR", "side": "SI", "back": "BA", "full": "FU"}[view]
    profile = manifest["identity_profile"]
    actions = []
    for index, template_text in enumerate(template_action_texts(view), start=1):
        rendered = template_text.replace("`", "")
        for field in IDENTITY_FIELDS:
            rendered = re.sub(
                rf"{re.escape(field)}=<[^>]+>",
                f"{field}={profile[field]}",
                rendered,
            )
        if not manifest["garment_profile"]["requires_full_garment_frame"]:
            rendered = rendered.split("GARMENT FRAME LOCK:", 1)[0].rstrip()
        action_id = f"{prefix}{index:02d}"
        actions.append(
            {
                "action_id": action_id,
                "title": f"Documented {view} action {index}",
                "prompt_en": (
                    f"SKC {manifest['skc_id']} | VIEW {view} | ACTION {action_id} | "
                    f"ATTEMPT 1 "
                    f"{'Nano Banana Pro, 4K, 2:3. ' if view != 'full' else ''}"
                    f"{rendered}"
                ),
                "negative_prompt": "Do not alter the product.",
            }
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
        "actions": actions,
    }


class DocumentationContractTests(unittest.TestCase):
    def test_handbook_publishes_identity_framing_and_canvas_rule_cards(self):
        handbook = HANDBOOK.read_text(encoding="utf-8")

        for rule in (
            "正面/1.jpg",
            "半个头部",
            "完整裙摆",
            "identity-drift",
            "date-skc-four-row-v3",
        ):
            self.assertIn(rule, handbook)

    def test_handbook_embeds_all_eight_workspace_markdown_documents(self):
        handbook = HANDBOOK.read_text(encoding="utf-8")
        markdown_paths = (
            "SKILL.md",
            "references/folder-contract.md",
            "references/prompt-output-schema.md",
            "references/lovart-execution.md",
            "references/templates/front.md",
            "references/templates/side.md",
            "references/templates/back.md",
            "references/templates/full.md",
        )

        for relative_path in markdown_paths:
            source = (ROOT / "skill" / relative_path).read_text(encoding="utf-8")
            encoded_source = json.dumps(source, ensure_ascii=False)
            self.assertIn(
                f'"relativePath":"{relative_path}","content":{encoded_source}',
                handbook,
            )

    def test_builder_uses_repository_skill_and_syncs_the_site_index(self):
        builder = BUILDER.read_text(encoding="utf-8")

        self.assertIn(
            "path.resolve(projectRoot, 'fashion-lovart-view-extension')",
            builder,
        )
        self.assertNotIn(".codex/skills", builder)
        self.assertEqual(HANDBOOK.read_bytes(), SITE_INDEX.read_bytes())

    def test_skill_contains_month_gate_and_spacing_ratios(self):
        skill = SKILL.read_text(encoding="utf-8")

        self.assertIn("blocked:month-project-mismatch", skill)
        self.assertIn("resolve_lovart_context.py", skill)
        self.assertIn("8%", skill)
        self.assertIn("25%", skill)
        self.assertIn("immediately report", skill)
        self.assertIn("Do not upload references or submit", skill)

    def test_lovart_reference_requires_reverification_before_resume(self):
        reference = LOVART.read_text(encoding="utf-8")

        self.assertIn("expected month project", reference)
        self.assertIn("re-read the visible project name", reference)
        self.assertIn("do not upload", reference)
        self.assertIn("do not submit", reference)
        self.assertIn("horizontal gap", reference)
        self.assertIn("vertical gap", reference)

    def test_readme_explains_daily_path_mapping_and_immediate_pause(self):
        readme = README.read_text(encoding="utf-8")

        self.assertIn("/Users/chenyiming/Desktop/8月/8月15日", readme)
        self.assertIn("Lovart 项目：8月", readme)
        self.assertIn("日期区：8月15日", readme)
        self.assertIn("立即暂停", readme)
        self.assertIn("8% / 8% / 25%", readme)

    def test_execution_contract_blocks_review_and_submission_when_results_are_incomplete(self):
        skill = SKILL.read_text(encoding="utf-8")
        reference = LOVART.read_text(encoding="utf-8")

        for document in (skill, reference):
            self.assertIn("blocked:base-count-incomplete", document)
            self.assertIn("blocked:result-identity", document)
            self.assertIn("placement backlog", document)
            self.assertIn("five identified and verified base results", document)
            self.assertIn("reserve", document)

    def test_skill_declares_canonical_identity_and_framing_rules(self):
        skill = SKILL.read_text(encoding="utf-8")

        self.assertIn("正面/1.jpg", skill)
        self.assertIn("IDENTITY MODEL SOURCE", skill)
        self.assertIn("HEAD CROP FLOOR", skill)
        self.assertIn("FULL-BODY HEAD COMPLETION", skill)
        self.assertIn("GARMENT FRAME LOCK", skill)
        self.assertIn("identity_model_01", skill)
        self.assertIn("full-head-incomplete", skill)

    def test_partial_or_absent_head_visibility_never_blocks_an_otherwise_ready_view(self):
        skill = SKILL.read_text(encoding="utf-8")
        folder = FOLDER.read_text(encoding="utf-8")
        rule = (
            "head_visibility of `partial` or `absent` alone never lowers a view's "
            "ready status and never triggers `blocked:role-ambiguous`"
        )
        confidence_scope = (
            "Every classified file with confidence below 0.7—including optional "
            "`accessory_source` and `unused` files—triggers `blocked:role-ambiguous`"
        )
        no_penalty = (
            "`partial` or `absent` head_visibility is not itself a confidence penalty"
        )

        for document in (skill, folder):
            self.assertIn(rule, document)
            self.assertIn(confidence_scope, document)
            self.assertIn(no_penalty, document)
            self.assertNotIn("Confidence below 0.7 for a required role assignment", document)

    def test_folder_contract_keeps_identity_source_first_without_duplicate_upload(self):
        folder = FOLDER.read_text(encoding="utf-8")

        self.assertIn("正面/1.jpg", folder)
        self.assertIn("IDENTITY MODEL SOURCE", folder)
        self.assertIn("identity_profile", folder)
        self.assertIn("identity_model_01", folder)
        self.assertIn("byte-identical", folder)

    def test_execution_and_readme_publish_the_exact_canvas_contract(self):
        reference = LOVART.read_text(encoding="utf-8")
        readme = README.read_text(encoding="utf-8")

        for document in (reference, readme):
            self.assertIn("date-skc-four-row-v3", document)
            self.assertIn("date -> SKC -> front/side/back/full -> primary/supplemental", document)
            self.assertIn("long-dress-hem-cropped", document)
            self.assertIn("full-head-incomplete", document)
            self.assertNotIn("full-body-head-incomplete", document)
            self.assertIn("identity", document.lower())
            self.assertIn("crop", document.lower())

    def test_rejection_docs_connect_reason_codes_to_the_transition_cli(self):
        skill = SKILL.read_text(encoding="utf-8")
        reference = LOVART.read_text(encoding="utf-8")
        command = re.compile(
            r"update_run_state\.py transition <state> <view> <action-id> rejected \\\n"
            r"\s+--reason \"<observed defect>\" --reason-code <code>"
        )
        ordinary_command = re.compile(
            r"update_run_state\.py transition <state> <view> <action-id> rejected \\\n"
            r"\s+--reason \"<ordinary quality defect>\"\n"
        )
        mappings = (
            "`identity-drift` — canonical identity mismatch",
            "`head-crop-below-minimum` — front/side/back crop below the half-head floor",
            "`full-head-incomplete` — full-body head or hair crown incomplete",
            "`long-dress-hem-cropped` — confirmed below-knee dress hem cropped",
        )

        for document in (skill, reference):
            self.assertRegex(document, command)
            self.assertRegex(document, ordinary_command)
            self.assertIn(
                "Use `--reason-code` only for these four hard-rule failures",
                document,
            )
            self.assertIn(
                "Ordinary garment, hands, scene, light, or anatomy rejection uses "
                "free-form `--reason` only",
                document,
            )
            self.assertNotIn("For every quality rejection", document)
            self.assertNotIn("Record every failed review through the structured rejection CLI", document)
            for mapping in mappings:
                self.assertIn(mapping, document)

    def test_every_template_action_carries_identity_and_conditional_garment_locks(self):
        for view, path in TEMPLATES.items():
            with self.subTest(view=view):
                template = path.read_text(encoding="utf-8")
                self.assertGreaterEqual(template.count("IDENTITY LOCK:"), 5)
                self.assertGreaterEqual(template.count("GARMENT FRAME LOCK:"), 5)
                self.assertIn("visually confirmed below-knee dress", template)

    def test_templates_distinguish_logical_roles_from_upload_order(self):
        for view, path in TEMPLATES.items():
            with self.subTest(view=view):
                template = path.read_text(encoding="utf-8")
                self.assertIn("identity_model_01", template)
                self.assertIn("logical role", template)
                self.assertIn("upload index", template)

    def test_templates_split_canonical_identity_from_local_pose_in_chinese_contracts(self):
        source_rule = (
            "IDENTITY MODEL SOURCE = 正面/1.jpg，仅控制身份；本视角 "
            "POSE/COMPOSITION SOURCE 仅控制姿势、裁切、身体方向和构图，不得覆盖身份"
        )
        for view, path in TEMPLATES.items():
            with self.subTest(view=view):
                template = path.read_text(encoding="utf-8")
                self.assertGreaterEqual(template.count(source_rule), 2)
                self.assertNotIn("图1（模特人物图）", template)
                self.assertNotIn("人物身份、体态、肤色、发型、气质和可复用配饰取自图1", template)

    def test_partial_view_templates_set_head_floor_without_banning_complete_heads(self):
        for view in ("front", "side", "back"):
            with self.subTest(view=view):
                template = TEMPLATES[view].read_text(encoding="utf-8")
                self.assertGreaterEqual(template.count("HEAD CROP FLOOR:"), 5)
                negative_prompt = template.split("## 通用负面提示词", 1)[1]
                negative_prompt = negative_prompt.split("## 输出参数", 1)[0].lower()
                self.assertNotIn("full head", negative_prompt)
                self.assertNotIn("complete face", negative_prompt)

    def test_full_template_reconstructs_head_without_weakening_full_body_frame(self):
        template = TEMPLATES["full"].read_text(encoding="utf-8")

        self.assertGreaterEqual(template.count("FULL-BODY HEAD COMPLETION:"), 5)
        self.assertIn("complete hair crown", template)
        self.assertIn("shoe soles", template)

    def test_skill_executes_schema_one_to_two_visual_contract_migration(self):
        skill = SKILL.read_text(encoding="utf-8")
        self.assertIn("New run migration", skill)
        self.assertIn("Resume migration", skill)
        self.assertIn("schema-1", skill)
        self.assertIn("schema-2", skill)
        for field in (
            "skin_tone_and_visible_ancestry_cues",
            "visible_face_features",
            "hair_evidence",
            "age_impression",
            "body_profile",
            "confidence",
            "reason",
            "garment_type",
            "hem_position",
            "requires_full_garment_frame",
        ):
            self.assertIn(field, skill)

    def test_documented_batch_snippet_and_all_template_actions_execute(self):
        inventory = scanner_inventory()
        batch_payload = {"skcs": [inventory]}
        long_manifest = representative_manifest("full", long_dress=True)

        with self.subTest(contract="scanner batch wrapper"):
            with tempfile.TemporaryDirectory() as temp_dir:
                batch_inventory_path = Path(temp_dir) / "batch-inventory.json"
                batch_inventory_path.write_text(
                    json.dumps(batch_payload, ensure_ascii=False), encoding="utf-8"
                )
                namespace = {
                    "batch_inventory_path": batch_inventory_path,
                    "assignments_by_skc": {"ds-doc-test": {}},
                    "identity_profiles": {
                        "ds-doc-test": copy.deepcopy(
                            long_manifest["identity_profile"]
                        )
                    },
                    "garment_profiles": {
                        "ds-doc-test": copy.deepcopy(
                            long_manifest["garment_profile"]
                        )
                    },
                    # Exercise the old documented shape against the real wrapper too.
                    "inventory": copy.deepcopy(batch_payload),
                    "assignments": {},
                    "identity_profile": copy.deepcopy(
                        long_manifest["identity_profile"]
                    ),
                    "garment_profile": copy.deepcopy(
                        long_manifest["garment_profile"]
                    ),
                }
                sys.path.insert(0, str(ROOT / "skill"))
                try:
                    exec(
                        compile(
                            documented_migration_snippet(),
                            str(SKILL),
                            "exec",
                        ),
                        namespace,
                    )
                except Exception as exc:
                    self.fail(f"documented scanner-output snippet failed: {exc}")
                finally:
                    sys.path.remove(str(ROOT / "skill"))

            self.assertEqual(namespace["batch_payload"]["skcs"][0]["skc_id"], "ds-doc-test")
            self.assertEqual(
                validate_manifest.validate_manifest_data(namespace["manifest"]), []
            )

        cases = {
            "front": representative_manifest("full", long_dress=True),
            "side": representative_manifest("partial", long_dress=True),
            "back": representative_manifest("absent", long_dress=False),
            "full": representative_manifest("partial", long_dress=True),
        }
        for view, manifest in cases.items():
            with self.subTest(contract="template actions", view=view):
                prompt = render_template_prompt(view, manifest)

                self.assertEqual(
                    validate_manifest.validate_prompt_data(prompt, manifest), []
                )

    def test_retry_docs_rebuild_terminal_contract_after_inserting_correction(self):
        ordered_steps = (
            "Remove the existing terminal block from FINAL CONTRACT OVERRIDE through the end of the prompt.",
            "Insert the evidence-based correction into the action prose before the terminal block.",
            "Rebuild and append the entire manifest-derived terminal block",
            "Validate the rebuilt prompt; never append correction text after the terminal block.",
        )
        for document in (SKILL, LOVART):
            with self.subTest(document=document.name):
                source = document.read_text(encoding="utf-8")
                for step in ordered_steps:
                    self.assertIn(step, source)
                positions = [source.index(step) for step in ordered_steps]
                self.assertEqual(positions, sorted(positions))

    def test_full_literal_actions_place_generation_settings_before_terminal_suffix(self):
        source = TEMPLATES["full"].read_text(encoding="utf-8")
        self.assertNotIn(
            "Output parameters: 4K resolution, 2:3 aspect ratio, model: nano banana pro",
            source,
        )
        for index, action in enumerate(template_action_texts("full"), start=1):
            with self.subTest(action=index):
                lowered = action.casefold()
                suffix_start = lowered.index("final contract override:")
                literal_prefix = lowered[:suffix_start]
                for setting in ("nano banana pro", "4k", "2:3"):
                    self.assertIn(setting, literal_prefix)

        negative_prompt = source.split(
            "## 二、通用负面提示词（Negative Prompt，全方案共用）", 1
        )[1].split("`", 2)[1]
        manifest = representative_manifest("partial", long_dress=True)
        prompt = render_template_prompt("full", manifest)
        for action in prompt["actions"]:
            action["negative_prompt"] = negative_prompt
        self.assertEqual(validate_manifest.validate_prompt_data(prompt, manifest), [])

    def test_handbook_names_the_sole_identity_filename_exception_and_denies_generic_models(self):
        required = (
            "正面/1.jpg is the sole filename-based exception.",
            (
                "A generic model_source or local pose/composition source must never "
                "supply canonical identity or body_profile."
            ),
        )
        for artifact in (SKILL, HANDBOOK, SITE_INDEX):
            with self.subTest(artifact=artifact.name):
                source = artifact.read_text(encoding="utf-8")
                for statement in required:
                    self.assertIn(statement, source)

    def test_noncanonical_local_models_never_control_body_profile(self):
        required_guard = (
            "Noncanonical local pose/composition sources must not control or override "
            "`body_profile`"
        )
        documents = (
            SKILL,
            FOLDER,
            PROMPT_SCHEMA,
            LOVART,
            README,
            *TEMPLATES.values(),
        )
        for document in documents:
            with self.subTest(document=document.name):
                self.assertIn(required_guard, document.read_text(encoding="utf-8"))

        folder = FOLDER.read_text(encoding="utf-8")
        readme = README.read_text(encoding="utf-8")
        self.assertNotIn("model identity, body, styling base", folder)
        self.assertNotIn("动作、构图和身体比例", readme)

    def test_templates_require_concrete_identity_values_inside_every_action_lock(self):
        required_fields = (
            "head_visibility=",
            "skin_tone_and_visible_ancestry_cues=",
            "visible_face_features=",
            "hair_evidence=",
            "age_impression=",
            "body_profile=",
        )
        for view, path in TEMPLATES.items():
            with self.subTest(view=view):
                source = path.read_text(encoding="utf-8")
                for field in required_fields:
                    self.assertGreaterEqual(source.count(field), 5)
                self.assertGreaterEqual(
                    source.count(
                        "body_profile=<exact active value>; Noncanonical local "
                        "pose/composition sources must not control or override "
                        "body_profile."
                    ),
                    5,
                )
                self.assertNotIn(
                    "`IDENTITY LOCK:` Preserve the identity_profile", source
                )

    def test_skill_and_prompt_schema_validate_prompts_against_active_manifest(self):
        skill = SKILL.read_text(encoding="utf-8")
        schema = PROMPT_SCHEMA.read_text(encoding="utf-8")
        command = (
            "python3 scripts/validate_manifest.py prompt "
            "<skc>/_codex/prompts/<view>.json <skc>/_codex/manifest.json"
        )

        self.assertIn(command, skill)
        self.assertIn("active schema-2 manifest", skill)
        self.assertIn("active schema-2 manifest", schema)
        self.assertIn("must match `identity_profile` exactly", schema)
        self.assertIn("must match `garment_profile` exactly", schema)

    def test_skill_and_prompt_schema_publish_exact_positive_lock_syntax(self):
        required_clauses = (
            "The final image must retain at least half of the model's head.",
            "A complete head is allowed.",
            "Never crop below the half-head boundary.",
            (
                "Even when 正面/1.jpg shows a partial head or no head, reconstruct a "
                "natural complete head using only the visible skin tone, ancestry "
                "cues, partial facial evidence, hair evidence, age impression, "
                "neck/shoulder evidence, and body profile."
            ),
            "Do not change the model's visible identity characteristics.",
            "Activate only for a visually confirmed below-knee dress;",
            "fixed semicolon-delimited order",
        )
        for document in (SKILL, PROMPT_SCHEMA):
            with self.subTest(document=document.name):
                source = document.read_text(encoding="utf-8")
                for clause in required_clauses:
                    self.assertIn(clause, source)

    def test_every_long_dress_template_contains_the_complete_hem_safety_contract(self):
        required_clauses = (
            "shoulder/neckline through the lowest hem point",
            "visible safety margin below the hem",
            "must not touch or cross an image edge",
            "major hem silhouette unobscured",
            "apparent garment length unchanged",
        )
        for view, path in TEMPLATES.items():
            with self.subTest(view=view):
                template = path.read_text(encoding="utf-8")
                for clause in required_clauses:
                    self.assertGreaterEqual(template.count(clause), 5)

    def test_skill_and_lovart_review_enforce_the_complete_hem_safety_contract(self):
        required_clauses = (
            "shoulder/neckline through the lowest hem point",
            "visible safety margin below the hem",
            "must not touch or cross an image edge",
            "major hem silhouette unobscured",
            "apparent garment length unchanged",
        )
        for document in (SKILL, LOVART):
            with self.subTest(document=document.name):
                source = document.read_text(encoding="utf-8")
                for clause in required_clauses:
                    self.assertIn(clause, source)

    def test_handbook_canvas_uses_ten_equal_continuous_cells(self):
        for artifact in (HANDBOOK_TEMPLATE, HANDBOOK, SITE_INDEX):
            with self.subTest(artifact=artifact.name):
                source = artifact.read_text(encoding="utf-8")
                self.assertIn(
                    ".cell-strip { display: grid; grid-template-columns: repeat(10, 1fr); gap: 7px; }",
                    source,
                )
                self.assertIn("Array.from({length:10}", source)
                self.assertNotIn("retry-cell", source)
                self.assertNotIn("width: 31px", source)
                self.assertNotIn("border-left: 1px dashed", source)

    def test_handbook_upload_step_places_identity_first_and_optional_pose_second(self):
        for artifact in (HANDBOOK_TEMPLATE, HANDBOOK, SITE_INDEX):
            with self.subTest(artifact=artifact.name):
                source = artifact.read_text(encoding="utf-8")
                upload_stage = source.split("{n:'06', name:'准备参考图'", 1)[1]
                upload_stage = upload_stage.split("},", 1)[0]
                identity = upload_stage.index("identity_model_01")
                pose = upload_stage.index("pose_model_01")
                product = upload_stage.index("product_01")
                self.assertLess(identity, pose)
                self.assertLess(pose, product)
                self.assertIn("可选", upload_stage)


if __name__ == "__main__":
    unittest.main()
