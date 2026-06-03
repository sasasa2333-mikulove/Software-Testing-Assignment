#!/usr/bin/env python3
"""Summarize gcov output for CPython Python/marshal.c."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any

DEFAULT_RESULTS = Path("whitebox/results")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument(
        "--gcov",
        type=Path,
        help="Path to marshal.c.gcov. Defaults to searching under whitebox/build.",
    )
    parser.add_argument(
        "--obligations",
        type=Path,
        default=Path("whitebox/obligations/marshal_def_use.csv"),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    gcov_path = args.gcov or _find_gcov()
    coverage = parse_gcov(gcov_path)
    obligations = read_obligations(args.obligations)
    summary = {
        "gcov_file": gcov_path.as_posix(),
        "statement": coverage["statement"],
        "branch": coverage["branch"],
        "def_use": summarize_obligations(obligations),
    }
    args.results.mkdir(parents=True, exist_ok=True)
    output = args.results / "marshal_coverage.json"
    output.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def parse_gcov(path: Path) -> dict[str, Any]:
    executable = 0
    executed = 0
    branches = 0
    taken = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        count, _, _source = line.partition(":")
        count = count.strip()
        if count and count not in {"-", "#####"} and count.isdigit():
            executable += 1
            if int(count) > 0:
                executed += 1
        elif count == "#####":
            executable += 1
        branch_match = re.match(r"\s*branch\s+\d+\s+(taken|never executed)", line)
        if branch_match:
            branches += 1
            if "taken" in line and "never" not in line:
                taken += 1
    return {
        "statement": {
            "covered": executed,
            "total": executable,
            "percent": _percent(executed, executable),
        },
        "branch": {
            "covered": taken,
            "total": branches,
            "percent": _percent(taken, branches),
        },
    }


def read_obligations(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def summarize_obligations(rows: list[dict[str, str]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for row in rows:
        status = row["status"]
        counts[status] = counts.get(status, 0) + 1
    return {"total": len(rows), "by_status": counts}


def _find_gcov() -> Path:
    candidates = sorted(Path("whitebox").glob("build/**/marshal.c.gcov"))
    if not candidates:
        raise FileNotFoundError("Could not find marshal.c.gcov under whitebox/build")
    return candidates[0]


def _percent(covered: int, total: int) -> float:
    if total == 0:
        return 100.0
    return round((covered / total) * 100, 2)


if __name__ == "__main__":
    raise SystemExit(main())
