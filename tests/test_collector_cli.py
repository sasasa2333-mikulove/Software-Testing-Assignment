from __future__ import annotations

import json

from marshal_stability.cli import main
from marshal_stability.collector import collect_records


def test_collector_returns_json_ready_records() -> None:
    records = collect_records()

    assert records
    for record in records:
        payload = record.to_json()
        assert payload["case_id"]
        assert payload["status"] in {"ok", "error"}
        assert payload["implementation"]
        assert payload["marshal_version"] >= 0


def test_cli_writes_json_file(tmp_path) -> None:
    output = tmp_path / "records.json"

    exit_code = main(["--output", output.as_posix()])

    assert exit_code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["records"]
    assert {record["case_id"] for record in payload["records"]}
