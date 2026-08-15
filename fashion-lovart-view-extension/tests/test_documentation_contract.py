import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skill" / "SKILL.md"
LOVART = ROOT / "skill" / "references" / "lovart-execution.md"
README = ROOT / "README.md"


class DocumentationContractTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
