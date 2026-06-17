#!/usr/bin/env python3
"""Compare two portable marshal equivalence JSONL artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path, help="Baseline JSONL artifact.")
    parser.add_argument("candidate", type=Path, help="Candidate JSONL artifact.")
    parser.add_argument(
        "--strict-digest",
        action="store_true",
        help="Exit non-zero when common successful cases have different digests.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = compare_jsonl(args.baseline, args.candidate)
    print(json.dumps(result, indent=2, sort_keys=True))
    has_status_or_shape_problem = bool(
        result["missing_in_candidate"]
        or result["extra_in_candidate"]
        or result["different_status_cases"]
    )
    has_digest_problem = bool(result["different_digest_cases"])
    return int(
        has_status_or_shape_problem or (args.strict_digest and has_digest_problem)
    )


def compare_jsonl(baseline_path: Path, candidate_path: Path) -> dict[str, Any]:
    baseline = _load_records(baseline_path)
    candidate = _load_records(candidate_path)
    common_ids = sorted(set(baseline) & set(candidate))
    different_status_cases = [
        {
            "case_id": case_id,
            "baseline": baseline[case_id].get("status"),
            "candidate": candidate[case_id].get("status"),
        }
        for case_id in common_ids
        if baseline[case_id].get("status") != candidate[case_id].get("status")
    ]
    different_digest_cases = [
        {
            "case_id": case_id,
            "baseline": baseline[case_id].get("sha256"),
            "candidate": candidate[case_id].get("sha256"),
        }
        for case_id in common_ids
        if _successful(baseline[case_id])
        and _successful(candidate[case_id])
        and baseline[case_id].get("sha256") != candidate[case_id].get("sha256")
    ]
    return {
        "baseline": baseline_path.as_posix(),
        "candidate": candidate_path.as_posix(),
        "common_cases": len(common_ids),
        "missing_in_candidate": sorted(set(baseline) - set(candidate)),
        "extra_in_candidate": sorted(set(candidate) - set(baseline)),
        "different_status_cases": different_status_cases,
        "different_digest_cases": different_digest_cases,
    }


def _load_records(path: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        if not line.strip():
            continue
        record = json.loads(line)
        case_id = record["case_id"]
        if case_id in records:
            raise ValueError(f"Duplicate case_id {case_id!r} in {path}:{line_number}")
        records[case_id] = record
    return records


def _successful(record: dict[str, Any]) -> bool:
    return (
        record.get("status") == "ok"
        and record.get("first_equals_second") is True
        and record.get("roundtrip_equal") is True
    )


if __name__ == "__main__":
    raise SystemExit(main())
