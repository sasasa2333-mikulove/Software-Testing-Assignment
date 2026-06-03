"""Command line interface for marshal stability experiments."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from marshal_stability.collector import collect_records


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect deterministic marshal digest records."
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON file path. Writes JSON to stdout when omitted.",
    )
    parser.add_argument(
        "--include-large",
        action="store_true",
        help="Include larger boundary cases that are slower on small machines.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    records = collect_records(include_large=args.include_large)
    payload = {
        "records": [record.to_json() for record in records],
    }
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
