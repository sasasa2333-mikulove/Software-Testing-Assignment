#!/usr/bin/env python3
"""Compare marshal digest JSON artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from marshal_stability.compare import compare_artifacts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path, help="Baseline JSON artifact.")
    parser.add_argument("candidate", type=Path, help="Candidate JSON artifact.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when any common case has a different digest.",
    )
    parser.add_argument(
        "--expect-same-python-minor",
        action="store_true",
        help=(
            "Exit non-zero unless both artifacts use the same Python major.minor. "
            "Use this for cross-OS comparisons, not cross-version observations."
        ),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = compare_artifacts(args.baseline, args.candidate)
    print(json.dumps(result, indent=2, sort_keys=True))
    has_difference = bool(
        result["different_cases"]
        or result["different_status_cases"]
        or result["missing_in_candidate"]
        or result["extra_in_candidate"]
    )
    wrong_python_minor = (
        args.expect_same_python_minor and not result["same_python_minor"]
    )
    return int(wrong_python_minor or (args.strict and has_difference))


if __name__ == "__main__":
    raise SystemExit(main())
