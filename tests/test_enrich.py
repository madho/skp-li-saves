import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skp_li_saves.enrich import classify_theme, enrich_record, summarize_record


class ThemeEnrichmentTests(unittest.TestCase):
    def test_classifier_covers_multiple_themes(self) -> None:
        cases = [
            (
                {"text_clean": "We built an agentic AI system with an LLM and prompt workflows."},
                "AI & Automation",
            ),
            (
                {"text_clean": "The hiring team improved interview loops and recruiter scorecards.", "author_role": "Talent Acquisition Lead"},
                "Career & Hiring",
            ),
            (
                {"text_clean": "Roadmap, positioning, and go-to-market strategy for the next product launch."},
                "Product & Strategy",
            ),
            (
                {"text_clean": "We used content marketing and SEO to grow community and demand."},
                "Marketing & Growth",
            ),
            (
                {"text_clean": "Series A valuation and venture capital lessons for building an investing thesis."},
                "Finance & Investing",
            ),
            (
                {"text_clean": "A completely generic update without strong signals."},
                "General / Other",
            ),
        ]

        for record, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(classify_theme(record), expected)

    def test_summary_helper_uses_first_sentence_or_clause(self) -> None:
        sentence_record = {
            "text_clean": "First sentence is enough. Second sentence should not appear."
        }
        self.assertEqual(summarize_record(sentence_record), "First sentence is enough.")

        clause_record = {
            "text_clean": "Launch checklist: write copy, ship the page, and announce it tomorrow"
        }
        self.assertEqual(summarize_record(clause_record), "Launch checklist")

    def test_enrichment_populates_theme_and_summary(self) -> None:
        record = {
            "post_id": "urn:li:activity:99",
            "author_name": "Maya Patel",
            "author_role": "Growth Lead",
            "text_clean": "We used content marketing and SEO to grow community. It worked surprisingly well.",
            "text_raw": "We used content marketing and SEO to grow community. It worked surprisingly well.",
            "summary": "",
            "theme_primary": "",
            "theme_secondary": "",
        }

        enriched = enrich_record(record)
        self.assertEqual(enriched["theme_primary"], "Marketing & Growth")
        self.assertEqual(enriched["summary"], "We used content marketing and SEO to grow community.")

    def test_cli_enrich_applies_classifier_before_xlsx_export(self) -> None:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / "src")
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            input_path = tmpdir_path / "raw.json"
            input_path.write_text(
                json.dumps(
                    [
                        {
                            "post_id": "urn:li:activity:42",
                            "post_url": "https://www.linkedin.com/feed/update/urn:li:activity:42/",
                            "author_name": "Taylor Nguyen",
                            "author_role": "Growth Lead",
                            "published_at": "2026-06-03T10:00:00Z",
                            "text": "We used content marketing and SEO to grow community. It worked surprisingly well.\nLike\nComment\nShare\n",
                            "summary": "",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, "-m", "skp_li_saves", str(input_path), "--format", "xlsx", "--enrich"],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            output_path = tmpdir_path / "raw.xlsx"
            workbook = load_workbook(output_path)
            posts = workbook["Saved Posts"]
            self.assertEqual(posts[2][4].value, "We used content marketing and SEO to grow community.")
            self.assertEqual(posts[2][5].value, "Marketing & Growth")
            self.assertEqual(workbook["By Theme"]["A2"].value, "Marketing & Growth")


if __name__ == "__main__":
    unittest.main()
