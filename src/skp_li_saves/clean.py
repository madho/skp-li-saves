"""Text cleaning helpers for LinkedIn saved-post exports."""

from __future__ import annotations

import re

_ZERO_WIDTH_RE = re.compile(r"[\u200b\u200c\u200d\ufeff]")
_WHITESPACE_RE = re.compile(r"\s+")
_UI_JUNK_LINES = {
    "like",
    "comment",
    "share",
    "repost",
    "send",
    "copy link",
    "see more",
    "show more",
    "view more",
    "view all comments",
    "see all comments",
    "see translation",
    "translate",
}


def normalize_whitespace(text: str | None) -> str:
    """Collapse whitespace and trim leading/trailing spaces."""

    if not text:
        return ""
    return _WHITESPACE_RE.sub(" ", _ZERO_WIDTH_RE.sub("", text)).strip()


def strip_linkedin_ui_junk(text: str | None) -> str:
    """Remove obvious LinkedIn UI artifacts from copied/extracted text."""

    if not text:
        return ""

    raw_text = _ZERO_WIDTH_RE.sub("", text)
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    cleaned_lines: list[str] = []
    for line in lines:
        collapsed = normalize_whitespace(line).lower()
        if collapsed in _UI_JUNK_LINES:
            continue
        if re.search(r"\bsee more\.?$", collapsed, flags=re.IGNORECASE):
            # Remove the common LinkedIn truncation marker if it is appended to content.
            line = re.sub(r"\s*…?\s*see more\.?\s*$", "", line, flags=re.IGNORECASE)
            line = re.sub(r"\s*see more\.?\s*$", "", line, flags=re.IGNORECASE)
        cleaned = normalize_whitespace(line)
        if not cleaned:
            continue
        lower = cleaned.lower()
        if lower in _UI_JUNK_LINES:
            continue
        cleaned_lines.append(cleaned)

    return normalize_whitespace("\n".join(cleaned_lines))
