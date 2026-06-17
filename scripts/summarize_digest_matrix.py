#!/usr/bin/env python3
"""Summarize multiple marshal digest JSON artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from marshal_stability.compare import summarize_artifact_matrix


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "artifacts",
        nargs="+",
        type=Path,
        help="Digest JSON artifacts produced by marshal-stability.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON output path. Writes to stdout when omitted.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = summarize_artifact_matrix(args.artifacts)
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
