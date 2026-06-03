from __future__ import annotations

import json

from marshal_stability.compare import compare_artifacts


def _artifact(digest: str) -> dict[str, list[dict[str, str]]]:
    return {
        "records": [
            {
                "case_id": "none",
                "sha256": digest,
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
