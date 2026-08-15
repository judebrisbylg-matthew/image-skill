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


if __name__ == "__main__":
    unittest.main()
