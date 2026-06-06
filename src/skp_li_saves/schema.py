"""Canonical record schema for normalized saved posts."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass(slots=True)
class SavedPostRecord:
    """Canonical representation of a LinkedIn saved post."""

    post_id: str = ""
    post_url: str = ""
    author_name: str = ""
    author_role: str = ""
    published_at: str = ""
    text_raw: str = ""
    text_clean: str = ""
    summary: str = ""
    theme_primary: str = ""
    theme_secondary: str = ""
    source_type: str = "raw_export"
    source_run_id: str = ""
    schema_version: str = field(default="1")

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable record dictionary."""

        return asdict(self)
