#!/usr/bin/env python3
"""Summarize gcov/gcovr results for CPython Python/marshal.c."""

from __future__ import annotations

import argparse
import json
import marshal
import platform
import re
import sys
from pathlib import Path

DEFAULT_OUTPUT = Path("whitebox/results/assignment_gcov_summary.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--coverage-source",
        choices=["gcov", "gcovr", "unavailable"],
        default="unavailable",
    )
    parser.add_argument("--coverage-file", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--command", default="")
    parser.add_argument("--notes", action="append", default=[])
    return parser


def main() -> int:
    args = build_parser().parse_args()
    coverage = _empty_coverage()
    notes = list(args.notes)

    if args.coverage_source == "gcovr" and args.coverage_file:
        coverage = _parse_gcovr_json(args.coverage_file)
    elif args.coverage_source == "gcov" and args.coverage_file:
        coverage = _parse_gcov_file(args.coverage_file)
    elif args.coverage_source == "unavailable":
        notes.append("No gcov or gcovr executable was available.")

    summary = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "marshal_version": marshal.version,
        "coverage_source": _coverage_source_label(
            args.coverage_source,
            args.coverage_file,
        ),
        "statement_covered": coverage["statement_covered"],
        "statement_total": coverage["statement_total"],
        "statement_percent": coverage["statement_percent"],
        "branch_covered": coverage["branch_covered"],
        "branch_total": coverage["branch_total"],
        "branch_percent": coverage["branch_percent"],
        "command": args.command,
        "notes": notes,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def _parse_gcovr_json(path: Path) -> dict[str, int | float | None]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    files = payload.get("files", [])
    marshal_files = [
        file_payload
        for file_payload in files
        if str(file_payload.get("file", ""))
        .replace("\\", "/")
        .endswith("Python/marshal.c")
    ]
    if not marshal_files:
        return _empty_coverage()

    statements_total = 0
    statements_covered = 0
    branches_total = 0
    branches_covered = 0
    for file_payload in marshal_files:
        for line in file_payload.get("lines", []):
            count = line.get("count")
            if count is not None:
                statements_total += 1
                if int(count) > 0:
                    statements_covered += 1
            for branch in line.get("branches", []):
                branches_total += 1
                if int(branch.get("count", 0)) > 0:
                    branches_covered += 1

    return _coverage(
        statements_covered,
        statements_total,
        branches_covered,
        branches_total,
    )


def _parse_gcov_file(path: Path) -> dict[str, int | float | None]:
    statements_total = 0
    statements_covered = 0
    branches_total = 0
    branches_covered = 0

    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        count_text, _, _source = line.partition(":")
        count_text = count_text.strip()
        if count_text == "#####":
            statements_total += 1
        elif count_text.isdigit():
            statements_total += 1
            if int(count_text) > 0:
                statements_covered += 1

        branch_match = re.match(
            r"\s*branch\s+\d+\s+(never executed|taken\s+(\d+))",
            line,
        )
        if branch_match:
            branches_total += 1
            taken_count = branch_match.group(2)
            if taken_count is not None and int(taken_count) > 0:
                branches_covered += 1

    return _coverage(
        statements_covered,
        statements_total,
        branches_covered,
        branches_total,
    )


def _coverage(
    statement_covered: int,
    statement_total: int,
    branch_covered: int,
    branch_total: int,
) -> dict[str, int | float | None]:
    return {
        "statement_covered": statement_covered,
        "statement_total": statement_total,
        "statement_percent": _percent(statement_covered, statement_total),
        "branch_covered": branch_covered,
        "branch_total": branch_total,
        "branch_percent": _percent(branch_covered, branch_total),
    }


def _empty_coverage() -> dict[str, int | float | None]:
    return {
        "statement_covered": None,
        "statement_total": None,
        "statement_percent": None,
        "branch_covered": None,
        "branch_total": None,
        "branch_percent": None,
    }


def _percent(covered: int, total: int) -> float | None:
    if total == 0:
        return None
    return round((covered / total) * 100, 2)


def _coverage_source_label(source: str, coverage_file: Path | None) -> str:
    if coverage_file is None:
        return source
    return f"{source}:{coverage_file.as_posix()}"


if __name__ == "__main__":
    raise SystemExit(main())
