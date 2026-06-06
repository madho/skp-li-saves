"""CLI for normalizing saved-post exports into JSONL."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from collections.abc import Iterable, Mapping
from typing import Any

from .normalize import normalize_saved_post


def _load_records(path: Path) -> list[Mapping[str, Any]]:
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="skp-li-saves", description="Normalize LinkedIn saved-post exports into canonical JSONL.")
    parser.add_argument("input", type=Path, help="Path to a JSON array file or JSONL file.")
    parser.add_argument("-o", "--output", type=Path, help="Write JSONL to a file instead of stdout.")
    parser.add_argument("--source-type", default="raw_export", help="Source type stored on normalized records.")
    parser.add_argument("--source-run-id", default="", help="Optional run identifier stored on normalized records.")
    return parser


def _emit_jsonl(records: Iterable[Mapping[str, Any]], stream) -> None:
    for record in records:
        stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
        stream.write("\n")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    raw_records = _load_records(args.input)
    normalized = [normalize_saved_post(record, source_type=args.source_type, source_run_id=args.source_run_id).to_dict() for record in raw_records]

    if args.output:
        with args.output.open("w", encoding="utf-8") as stream:
            _emit_jsonl(normalized, stream)
    else:
        _emit_jsonl(normalized, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
