"""Compare marshal digest artifacts."""

from __future__ import annotations

import json
import re
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
    status_differences = [
        {
            "case_id": case_id,
            "baseline": baseline[case_id].get("status"),
            "candidate": candidate[case_id].get("status"),
        }
        for case_id in common_ids
        if baseline[case_id].get("status") != candidate[case_id].get("status")
    ]
    baseline_metadata = _metadata(baseline)
    candidate_metadata = _metadata(candidate)
    return {
        "baseline": baseline_path.as_posix(),
        "baseline_metadata": baseline_metadata,
        "candidate": candidate_path.as_posix(),
        "candidate_metadata": candidate_metadata,
        "common_cases": len(common_ids),
        "different_cases": differences,
        "different_status_cases": status_differences,
        "missing_in_candidate": sorted(set(baseline) - set(candidate)),
        "extra_in_candidate": sorted(set(candidate) - set(baseline)),
        "same_python_minor": _same_python_minor(
            baseline_metadata.get("python_minor"),
            candidate_metadata.get("python_minor"),
        ),
    }


def summarize_artifact_matrix(paths: list[Path]) -> dict[str, Any]:
    """Return pairwise comparisons grouped for the course platform matrix."""

    comparisons = []
    for baseline_index, baseline_path in enumerate(paths):
        for candidate_path in paths[baseline_index + 1 :]:
            comparison = compare_artifacts(baseline_path, candidate_path)
            comparison["interpretation"] = _interpret_comparison(comparison)
            comparisons.append(comparison)

    return {
        "artifacts": [
            {"path": path.as_posix(), "metadata": _metadata(_load_records(path))}
            for path in paths
        ],
        "pairwise_comparisons": comparisons,
    }


def _load_records(path: Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {record["case_id"]: record for record in payload["records"]}


def _metadata(records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if not records:
        return {
            "implementation": None,
            "python_version": None,
            "python_minor": None,
            "platform": None,
            "machine": None,
            "marshal_version": None,
        }

    first = next(iter(records.values()))
    python_version = first.get("python_version")
    return {
        "implementation": first.get("implementation"),
        "python_version": python_version,
        "python_minor": _python_minor(str(python_version)),
        "platform": first.get("platform"),
        "machine": first.get("machine"),
        "marshal_version": first.get("marshal_version"),
    }


def _python_minor(version_text: str) -> str | None:
    match = re.match(r"(\d+)\.(\d+)", version_text)
    if not match:
        return None
    return ".".join(match.groups())


def _same_python_minor(left: str | None, right: str | None) -> bool:
    return left is not None and left == right


def _interpret_comparison(comparison: dict[str, Any]) -> str:
    has_shape_problem = bool(
        comparison["missing_in_candidate"]
        or comparison["extra_in_candidate"]
        or comparison["different_status_cases"]
    )
    has_digest_difference = bool(comparison["different_cases"])
    if comparison["same_python_minor"]:
        if has_shape_problem or has_digest_difference:
            return "same-python-version mismatch; investigate as a stability finding"
        return "same-python-version match"
    if has_shape_problem:
        return "cross-version shape/status difference"
    if has_digest_difference:
        return "cross-version digest difference; record as format evolution"
    return "cross-version digest match"
