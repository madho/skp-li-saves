import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


class CliTests(unittest.TestCase):
    def test_module_help_works(self) -> None:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT / "src")
        result = subprocess.run(
            [sys.executable, "-m", "skp_li_saves", "--help"],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Normalize LinkedIn saved-post exports", result.stdout)

    def test_normalizes_json_array_fixture_to_jsonl(self) -> None:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT / "src")
        fixture = REPO_ROOT / "tests" / "fixtures" / "raw_saved_posts.json"
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "normalized.jsonl"
            result = subprocess.run(
                [sys.executable, "-m", "skp_li_saves", str(fixture), "--output", str(output_path), "--source-type", "linkedin_export", "--source-run-id", "run-123"],
                cwd=REPO_ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            lines = output_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)

            first = json.loads(lines[0])
            self.assertEqual(first["post_id"], "urn:li:activity:1")
            self.assertEqual(first["text_clean"], "Hello world from LinkedIn")
            self.assertEqual(first["source_type"], "linkedin_export")
            self.assertEqual(first["source_run_id"], "run-123")


if __name__ == "__main__":
    unittest.main()
