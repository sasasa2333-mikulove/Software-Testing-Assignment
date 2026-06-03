"""Compare marshal digest artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def compare_artifacts(baseline_path: Path, candidate_path: Path) -> dict[str, Any]:
    baseline = _load_records(baseline_path)
    candidate = _load_records(candidate_path)
    common_ids = sorted(set(baseline) & set(candidate))
    differences = [
        {
            "case_id": case_id,
            "baseline": baseline[case_id].get("sha256"),
            "candidate": candidate[case_id].get("sha256"),
        }
        for case_id in common_ids
        if baseline[case_id].get("sha256") != candidate[case_id].get("sha256")
    ]
    return {
        "baseline": baseline_path.as_posix(),
        "candidate": candidate_path.as_posix(),
        "common_cases": len(common_ids),
        "different_cases": differences,
        "missing_in_candidate": sorted(set(baseline) - set(candidate)),
        "extra_in_candidate": sorted(set(candidate) - set(baseline)),
    }


def _load_records(path: Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {record["case_id"]: record for record in payload["records"]}
