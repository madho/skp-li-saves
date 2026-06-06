import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skp_li_saves.clean import normalize_whitespace, strip_linkedin_ui_junk


class CleanTextTests(unittest.TestCase):
    def test_normalize_whitespace_collapses_runs(self) -> None:
        self.assertEqual(normalize_whitespace("  hello\n\tworld  "), "hello world")

    def test_strip_linkedin_ui_junk_removes_common_artifacts(self) -> None:
        text = """  Here's a post… see more\nLike\nComment\nShare\n\n  Keep this line  """
        self.assertEqual(strip_linkedin_ui_junk(text), "Here's a post Keep this line")


if __name__ == "__main__":
    unittest.main()
