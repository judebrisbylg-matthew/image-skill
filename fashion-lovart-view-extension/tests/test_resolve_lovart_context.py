import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skill" / "scripts" / "resolve_lovart_context.py"


def load_module():
    spec = importlib.util.spec_from_file_location("resolve_lovart_context", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LovartContextTests(unittest.TestCase):
    def test_resolves_month_project_and_date_region_from_daily_path(self):
        module = load_module()
        context = module.resolve_lovart_context(
            Path("/Users/chenyiming/Desktop/8月/8月15日")
        )

        self.assertEqual(context["expected_month_project"], "8月")
        self.assertEqual(context["date_region"], "8月15日")
        self.assertEqual(context["project_verification_status"], "pending")
        self.assertIsNone(context["blocker"])

    def test_resolves_context_from_an_skc_nested_below_the_daily_path(self):
        module = load_module()
        context = module.resolve_lovart_context(
            Path("/Users/chenyiming/Desktop/8月/8月15日/ds726301071")
        )

        self.assertEqual(context["expected_month_project"], "8月")
        self.assertEqual(context["date_region"], "8月15日")

    def test_blocks_when_the_date_context_is_ambiguous(self):
        module = load_module()
        context = module.resolve_lovart_context(Path("/Users/chenyiming/Desktop/batch"))

        self.assertEqual(context["blocker"], "blocked:date-context-ambiguous")
        self.assertTrue(context["feedback_required"])
        self.assertIn("无法从输入路径识别月份和日期", context["feedback_message"])

    def test_blocks_and_builds_immediate_feedback_when_project_mismatches(self):
        module = load_module()
        context = module.resolve_lovart_context(
            Path("/Users/chenyiming/Desktop/8月/8月15日")
        )

        verified = module.verify_visible_project(context, "7月")

        self.assertEqual(verified["blocker"], "blocked:month-project-mismatch")
        self.assertTrue(verified["feedback_required"])
        self.assertIn("输入路径：/Users/chenyiming/Desktop/8月/8月15日", verified["feedback_message"])
        self.assertIn("预期项目：8月", verified["feedback_message"])
        self.assertIn("当前项目：7月", verified["feedback_message"])
        self.assertIn("回复“已修正”", verified["feedback_message"])

    def test_blocks_when_the_visible_project_cannot_be_read(self):
        module = load_module()
        context = module.resolve_lovart_context(
            Path("/Users/chenyiming/Desktop/8月/8月15日")
        )

        verified = module.verify_visible_project(context, None)

        self.assertEqual(verified["blocker"], "blocked:month-project-mismatch")
        self.assertIn("当前项目：无法确认", verified["feedback_message"])

    def test_requires_reverification_after_a_mismatch(self):
        module = load_module()
        context = module.resolve_lovart_context(
            Path("/Users/chenyiming/Desktop/8月/8月15日")
        )
        blocked = module.verify_visible_project(context, "7月")

        recovered = module.verify_visible_project(blocked, "8月")

        self.assertEqual(recovered["project_verification_status"], "verified")
        self.assertEqual(recovered["verified_month_project"], "8月")
        self.assertIsNone(recovered["blocker"])
        self.assertFalse(recovered["feedback_required"])
        self.assertIsNone(recovered["feedback_message"])

    def test_cli_writes_a_context_file_and_returns_blocked_exit_code_on_mismatch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "context.json"
            resolved = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "resolve",
                    "/Users/chenyiming/Desktop/8月/8月15日",
                    "--output",
                    str(output),
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(resolved.returncode, 0, resolved.stderr)

            verified = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "verify",
                    str(output),
                    "--visible-project",
                    "7月",
                    "--output",
                    str(output),
                ],
                text=True,
                capture_output=True,
            )
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(verified.returncode, 3)
            self.assertEqual(payload["blocker"], "blocked:month-project-mismatch")
            self.assertIn("任务已暂停", verified.stdout)


if __name__ == "__main__":
    unittest.main()
