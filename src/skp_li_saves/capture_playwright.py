"""Playwright-based capture for LinkedIn saved posts.

This module launches a persistent browser profile, opens the LinkedIn saved-posts
page, scrolls and clicks "Show more results" gates, and writes raw capture
records to JSON so they can be normalized by the existing CLI.
"""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Iterable, Sequence
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

DEFAULT_SAVED_POSTS_URL = "https://www.linkedin.com/my-items/saved-posts/"
SHOW_MORE_RESULTS_RE = re.compile(r"show more results", re.IGNORECASE)
BLOCK_TAGS = {"article", "div", "li", "p", "section", "span", "br", "h1", "h2", "h3", "h4", "h5", "h6"}


class _SavedPostsHTMLParser(HTMLParser):
    """Extract saved-post cards from HTML snapshots."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._tag_stack: list[str] = []
        self._card_stack: list[dict[str, Any]] = []
        self.records: list[dict[str, str]] = []

    def _append_spacing(self) -> None:
        if self._card_stack:
            self._card_stack[-1]["text_parts"].append(" ")

    def _finalize_cards(self) -> None:
        while self._card_stack and self._card_stack[-1]["depth"] > len(self._tag_stack):
            card = self._card_stack.pop()
            text = " ".join("".join(card["text_parts"]).split())
            if card["urn"]:
                self.records.append({"urn": card["urn"], "text": text})

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._tag_stack.append(tag)
        attr_map = {name: value or "" for name, value in attrs}
        urn = attr_map.get("data-chameleon-result-urn", "").strip()
        if urn:
            self._card_stack.append({"urn": urn, "text_parts": [], "depth": len(self._tag_stack)})
        if self._card_stack and tag in BLOCK_TAGS:
            self._append_spacing()

    def handle_endtag(self, tag: str) -> None:
        if self._tag_stack:
            self._tag_stack.pop()
        if self._card_stack and tag in BLOCK_TAGS:
            self._append_spacing()
        self._finalize_cards()

    def handle_data(self, data: str) -> None:
        if self._card_stack and data:
            self._card_stack[-1]["text_parts"].append(data)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def close(self) -> None:
        super().close()
        self._finalize_cards()
        self._card_stack.clear()
        self._tag_stack.clear()


def extract_saved_post_records_from_html(html: str) -> list[dict[str, str]]:
    """Parse HTML and extract raw saved-post records.

    The returned objects stay intentionally simple so they can flow directly into
    the existing normalization CLI.
    """

    parser = _SavedPostsHTMLParser()
    parser.feed(html)
    parser.close()
    return dedupe_capture_records(parser.records)


def dedupe_capture_records(records: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    """Deduplicate capture records by URN while preserving the richest text."""

    merged: dict[str, dict[str, str]] = {}
    order: list[str] = []
    for record in records:
        urn = str(record.get("urn", "")).strip()
        if not urn:
            continue
        text = str(record.get("text", "")).strip()
        if urn not in merged:
            merged[urn] = {"urn": urn, "text": text}
            order.append(urn)
        elif len(text) > len(merged[urn]["text"]):
            merged[urn]["text"] = text
    return [merged[urn] for urn in order]


def _load_html_capture(path: Path) -> list[dict[str, str]]:
    return extract_saved_post_records_from_html(path.read_text(encoding="utf-8"))


def _capture_from_playwright(
    *,
    url: str,
    user_data_dir: Path,
    output: Path,
    browser_channel: str | None,
    headless: bool,
    max_scrolls: int,
    settle_ms: int,
    click_wait_ms: int,
    log_every: int,
) -> list[dict[str, str]]:
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover - exercised only when dependency missing
        raise RuntimeError(
            "Playwright is not installed. Install project dependencies and run `playwright install chromium`."
        ) from exc

    user_data_dir.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)

    captured: list[dict[str, str]] = []
    seen_urns: set[str] = set()
    stagnant_rounds = 0
    previous_count = 0

    with sync_playwright() as playwright:
        chromium = playwright.chromium
        context = chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=headless,
            channel=browser_channel or None,
            viewport={"width": 1440, "height": 1800},
        )
        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(settle_ms)

            for index in range(max_scrolls):
                snapshot = page.locator("[data-chameleon-result-urn]").evaluate_all(
                    """
                    nodes => nodes.map(node => ({
                        urn: node.getAttribute('data-chameleon-result-urn') || '',
                        text: node.innerText || ''
                    }))
                    """
                )
                before_count = len(captured)
                for record in snapshot:
                    urn = str(record.get("urn", "")).strip()
                    text = " ".join(str(record.get("text", "")).split())
                    if not urn:
                        continue
                    if urn not in seen_urns:
                        seen_urns.add(urn)
                        captured.append({"urn": urn, "text": text})
                    elif text:
                        for existing in captured:
                            if existing["urn"] == urn and len(text) > len(existing["text"]):
                                existing["text"] = text
                                break

                clicked = False
                for selector in ["button", "a", "div", "span"]:
                    locator = page.locator(selector).filter(has_text=SHOW_MORE_RESULTS_RE)
                    for item_index in range(locator.count()):
                        candidate = locator.nth(item_index)
                        try:
                            if candidate.is_visible():
                                candidate.click(timeout=click_wait_ms)
                                clicked = True
                                break
                        except PlaywrightTimeoutError:
                            continue
                        except Exception:
                            continue
                    if clicked:
                        break

                page.mouse.wheel(0, 4000)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(settle_ms)

                if log_every and (index + 1) % log_every == 0:
                    print(f"Captured {len(captured)} saved posts so far...", flush=True)

                if len(captured) == previous_count and not clicked and before_count == len(captured):
                    stagnant_rounds += 1
                else:
                    stagnant_rounds = 0
                previous_count = len(captured)

                if stagnant_rounds >= 3:
                    break

            captured = dedupe_capture_records(captured)
            output.write_text(json.dumps(captured, indent=2, ensure_ascii=False), encoding="utf-8")
            return captured
        finally:
            context.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skp-li-saves-capture",
        description="Capture LinkedIn saved posts from a logged-in browser session with Playwright.",
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_SAVED_POSTS_URL,
        help="LinkedIn saved-posts page URL to open.",
    )
    parser.add_argument(
        "--profile-dir",
        type=Path,
        default=Path.home() / ".cache" / "skp-li-saves" / "playwright-profile",
        help="Persistent browser profile directory used by Playwright.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("linkedin_saved_posts.json"),
        help="Write raw capture JSON to this file.",
    )
    parser.add_argument(
        "--browser-channel",
        default="",
        help="Optional Playwright browser channel to use (for example: chrome or msedge). Leave empty to use bundled Chromium.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run headless instead of opening a visible browser window.",
    )
    parser.add_argument(
        "--max-scrolls",
        type=int,
        default=60,
        help="Maximum scroll/capture iterations before stopping.",
    )
    parser.add_argument(
        "--settle-ms",
        type=int,
        default=1200,
        help="Delay after scrolling/clicking to let LinkedIn render more results.",
    )
    parser.add_argument(
        "--click-wait-ms",
        type=int,
        default=1500,
        help="Timeout for clicking any visible 'Show more results' gate.",
    )
    parser.add_argument(
        "--log-every",
        type=int,
        default=5,
        help="Print a progress message after every N capture rounds. Set to 0 to disable.",
    )
    parser.add_argument(
        "--html",
        type=Path,
        help="Parse a saved HTML snapshot instead of launching a browser.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.html:
        records = _load_html_capture(args.html)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote {len(records)} records to {args.output}")
        return 0

    records = _capture_from_playwright(
        url=args.url,
        user_data_dir=args.profile_dir,
        output=args.output,
        browser_channel=args.browser_channel,
        headless=args.headless,
        max_scrolls=args.max_scrolls,
        settle_ms=args.settle_ms,
        click_wait_ms=args.click_wait_ms,
        log_every=args.log_every,
    )
    print(f"Wrote {len(records)} records to {args.output}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
