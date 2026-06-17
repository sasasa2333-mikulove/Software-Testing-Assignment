from __future__ import annotations

import json

from marshal_stability.compare import compare_artifacts, summarize_artifact_matrix


def _artifact(
    digest: str,
    *,
    python_version: str = "3.13.3",
    status: str = "ok",
) -> dict[str, list[dict[str, str]]]:
    return {
        "records": [
            {
                "case_id": "none",
                "implementation": "CPython",
                "machine": "arm64",
                "marshal_version": 4,
                "platform": "test-platform",
                "python_version": python_version,
                "sha256": digest,
                "status": status,
            }
        ]
    }


def test_compare_digests_reports_equal_artifacts(tmp_path) -> None:
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    baseline.write_text(json.dumps(_artifact("abc")), encoding="utf-8")
    candidate.write_text(json.dumps(_artifact("abc")), encoding="utf-8")

    result = compare_artifacts(baseline, candidate)

    assert result["common_cases"] == 1
    assert result["different_cases"] == []
    assert result["same_python_minor"] is True


def test_compare_digests_reports_different_artifacts(tmp_path) -> None:
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    baseline.write_text(json.dumps(_artifact("abc")), encoding="utf-8")
    candidate.write_text(json.dumps(_artifact("def")), encoding="utf-8")

    result = compare_artifacts(baseline, candidate)

    assert result["common_cases"] == 1
    assert result["different_cases"] == [
        {"case_id": "none", "baseline": "abc", "candidate": "def"}
    ]


def test_compare_digests_reports_status_differences(tmp_path) -> None:
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    baseline.write_text(json.dumps(_artifact("abc", status="ok")), encoding="utf-8")
    candidate.write_text(
        json.dumps(_artifact("abc", status="error")),
        encoding="utf-8",
    )

    result = compare_artifacts(baseline, candidate)

    assert result["different_status_cases"] == [
        {"case_id": "none", "baseline": "ok", "candidate": "error"}
    ]


def test_matrix_labels_cross_version_digest_differences(tmp_path) -> None:
    baseline = tmp_path / "py312.json"
    candidate = tmp_path / "py313.json"
    baseline.write_text(
        json.dumps(_artifact("abc", python_version="3.12.7")),
        encoding="utf-8",
    )
    candidate.write_text(
        json.dumps(_artifact("def", python_version="3.13.3")),
        encoding="utf-8",
    )

    result = summarize_artifact_matrix([baseline, candidate])

    comparison = result["pairwise_comparisons"][0]
    assert comparison["same_python_minor"] is False
    assert comparison["interpretation"] == (
        "cross-version digest difference; record as format evolution"
    )
