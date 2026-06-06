"""CLI for normalizing saved-post exports and exporting normalized records."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from .export_common import load_serialized_records
from .export_html import export_html
from .export_xlsx import export_xlsx
from .normalize import normalize_saved_post

EXPORT_FORMATS = {"jsonl", "html", "xlsx"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skp-li-saves",
        description="Normalize LinkedIn saved-post exports into canonical JSONL, HTML, or XLSX.",
    )
    parser.add_argument("input", type=Path, help="Path to a JSON array file or JSONL file.")
    parser.add_argument("-o", "--output", type=Path, help="Write output to a file instead of stdout for JSONL.")
    parser.add_argument("--format", choices=sorted(EXPORT_FORMATS), default="jsonl", help="Output format: jsonl (default), html, or xlsx.")
    parser.add_argument("--source-type", default="raw_export", help="Source type stored on normalized records.")
    parser.add_argument("--source-run-id", default="", help="Optional run identifier stored on normalized records.")
    return parser


def _emit_jsonl(records: Iterable[Mapping[str, Any]], stream) -> None:
    for record in records:
        stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
        stream.write("\n")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.format == "jsonl":
        raw_records = load_serialized_records(args.input)
        normalized = [
            normalize_saved_post(record, source_type=args.source_type, source_run_id=args.source_run_id).to_dict()
            for record in raw_records
        ]

        if args.output:
            with args.output.open("w", encoding="utf-8") as stream:
                _emit_jsonl(normalized, stream)
        else:
            _emit_jsonl(normalized, sys.stdout)
        return 0

    records = [dict(record) for record in load_serialized_records(args.input)]
    output_path = args.output or args.input.with_suffix(f".{args.format}")

    if args.format == "html":
        export_html(records, output_path)
    elif args.format == "xlsx":
        export_xlsx(records, output_path)
    else:  # pragma: no cover - argparse choices keep this unreachable
        raise ValueError(f"unsupported format: {args.format}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
