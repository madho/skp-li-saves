"""Shared helpers for export commands."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .schema import SavedPostRecord


RecordInput = Mapping[str, Any] | SavedPostRecord


EXPORT_FIELDS = (
    "post_id",
    "post_url",
    "author_name",
    "author_role",
    "published_at",
    "text_raw",
    "text_clean",
    "summary",
    "theme_primary",
    "theme_secondary",
    "source_type",
    "source_run_id",
    "schema_version",
)


def load_serialized_records(path: Path) -> list[Mapping[str, Any]]:
    """Load a JSON array or JSONL file into a list of mapping records."""

    text = path.read_text(encoding="utf-8")
    stripped = text.lstrip()
    if not stripped:
        return []
    if stripped.startswith("["):
        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError("expected a JSON array or JSONL records")
        return [record for record in data if isinstance(record, Mapping)]

    records: list[Mapping[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        if isinstance(record, Mapping):
            records.append(record)
    return records


def record_to_export_dict(record: RecordInput) -> dict[str, Any]:
    """Return a normalized dictionary suitable for HTML/XLSX exports."""

    if isinstance(record, SavedPostRecord):
        data = record.to_dict()
    else:
        data = dict(record)

    return {field: data.get(field, "") for field in EXPORT_FIELDS}


def collect_themes(records: list[dict[str, Any]]) -> list[str]:
    themes: set[str] = set()
    for record in records:
        for key in ("theme_primary", "theme_secondary"):
            value = str(record.get(key, "")).strip()
            if value:
                themes.add(value)
    return sorted(themes, key=str.casefold)


def theme_counts(records: list[dict[str, Any]]) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for record in records:
        for key in ("theme_primary", "theme_secondary"):
            value = str(record.get(key, "")).strip()
            if not value:
                continue
            counts[value] = counts.get(value, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0].casefold()))
