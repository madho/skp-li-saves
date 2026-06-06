import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from skp_li_saves.capture_playwright import dedupe_capture_records, extract_saved_post_records_from_html


class CapturePlaywrightTests(unittest.TestCase):
    def test_extract_saved_post_records_from_html(self) -> None:
        html = """
        <html>
          <body>
            <section data-chameleon-result-urn="urn:li:activity:1">
              <div>First post</div>
              <div>with a line break</div>
            </section>
            <section data-chameleon-result-urn="urn:li:activity:1">
              <div>First post with a much longer description</div>
            </section>
            <section data-chameleon-result-urn="urn:li:activity:2">
              <p>Second post</p>
            </section>
          </body>
        </html>
        """

        records = extract_saved_post_records_from_html(html)
        self.assertEqual([record["urn"] for record in records], ["urn:li:activity:1", "urn:li:activity:2"])
        self.assertIn("First post", records[0]["text"])
        self.assertIn("much longer description", records[0]["text"])
        self.assertEqual(records[1]["text"], "Second post")

    def test_dedupe_capture_records_prefers_longest_text(self) -> None:
        records = dedupe_capture_records(
            [
                {"urn": "urn:li:activity:1", "text": "short"},
                {"urn": "urn:li:activity:1", "text": "a much longer card text"},
                {"urn": "urn:li:activity:2", "text": "second"},
            ]
        )

        self.assertEqual(records, [
            {"urn": "urn:li:activity:1", "text": "a much longer card text"},
            {"urn": "urn:li:activity:2", "text": "second"},
        ])


if __name__ == "__main__":
    unittest.main()
