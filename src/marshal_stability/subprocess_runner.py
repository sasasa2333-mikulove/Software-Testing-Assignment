"""Helpers for collecting marshal records in separate Python processes."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SubprocessCollection:
    hash_seed: str
    records: dict[str, dict[str, Any]]


def collect_with_hash_seed(hash_seed: int | str) -> SubprocessCollection:
    """Collect digest records in a fresh process with a fixed hash seed."""

    seed = str(hash_seed)
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = seed
    command = [
        sys.executable,
        "-m",
        "marshal_stability.cli",
    ]
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )
    payload = json.loads(completed.stdout)
    return SubprocessCollection(
        hash_seed=seed,
        records={record["case_id"]: record for record in payload["records"]},
    )


def digest_map(collection: SubprocessCollection) -> dict[str, str | None]:
    return {
        case_id: record.get("sha256")
        for case_id, record in collection.records.items()
        if record.get("status") == "ok"
    }
