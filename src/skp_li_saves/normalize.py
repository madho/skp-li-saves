"""Normalization helpers for raw saved-post exports."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .clean import strip_linkedin_ui_junk
from .schema import SavedPostRecord


def _first_non_empty(mapping: Mapping[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = mapping.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            value = value.strip()
        else:
            value = str(value).strip()
        if value:
            return value
    return ""


def normalize_saved_post(raw: Mapping[str, Any], *, source_type: str = "raw_export", source_run_id: str = "") -> SavedPostRecord:
    """Convert one raw saved-post export object into the canonical schema."""

    text_raw = _first_non_empty(raw, ("text_raw", "text", "content", "body", "message"))
    text_clean = strip_linkedin_ui_junk(text_raw)

    return SavedPostRecord(
        post_id=_first_non_empty(raw, ("post_id", "id", "urn", "entityUrn")),
        post_url=_first_non_empty(raw, ("post_url", "url", "permalink", "canonical_url")),
        author_name=_first_non_empty(raw, ("author_name", "author", "name", "actor_name")),
        author_role=_first_non_empty(raw, ("author_role", "role", "headline", "author_title")),
        published_at=_first_non_empty(raw, ("published_at", "publishedAt", "date", "created_at", "timestamp")),
        text_raw=text_raw,
        text_clean=text_clean,
        summary=_first_non_empty(raw, ("summary",)),
        theme_primary=_first_non_empty(raw, ("theme_primary",)),
        theme_secondary=_first_non_empty(raw, ("theme_secondary",)),
        source_type=source_type,
        source_run_id=source_run_id,
    )
