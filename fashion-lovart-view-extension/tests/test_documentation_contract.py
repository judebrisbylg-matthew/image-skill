import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skill" / "SKILL.md"
LOVART = ROOT / "skill" / "references" / "lovart-execution.md"
FOLDER = ROOT / "skill" / "references" / "folder-contract.md"
README = ROOT / "README.md"
HANDBOOK = ROOT / "docs" / "handbook.html"
SITE_INDEX = ROOT.parent / "docs" / "index.html"
BUILDER = ROOT / "tools" / "build_handbook.mjs"
TEMPLATES = {
    view: ROOT / "skill" / "references" / "templates" / f"{view}.md"
    for view in ("front", "side", "back", "full")
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


if __name__ == "__main__":
    unittest.main()
