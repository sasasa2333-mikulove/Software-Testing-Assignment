#!/usr/bin/env python3
"""Run the assignment-specific source-informed marshal workload."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results",
        type=Path,
        default=Path("whitebox/results"),
        help="Directory for assignment white-box result JSON files.",
    )
    parser.add_argument(
        "--digest-repetitions",
        type=int,
        default=3,
        help="Repeated dumps per value in the driver workload.",
    )
    return parser


def main() -> int:
    _ensure_src_on_path()

    import marshal

    from marshal_stability.checks import (
        assert_digest_stable,
        assert_round_trip_equivalent,
        round_trip,
        supports_allow_code,
    )
    from marshal_stability.source_informed import (
        assignment_value_cases,
        format_version_cases,
        hash_seed_cases,
        hash_seed_digest_classes,
        hash_seed_result_dict,
        invalid_stream_cases,
        observation_dict,
        observe_loads,
        run_hash_seed_child,
        stable_dump_exception_type,
        validate_reference_shape,
    )

    args = build_parser().parse_args()
    args.results.mkdir(parents=True, exist_ok=True)

    value_results = []
    for case in assignment_value_cases(include_large=True):
        value_results.append(
            _run_value_case(
                case,
                assert_digest_stable=assert_digest_stable,
                assert_round_trip_equivalent=assert_round_trip_equivalent,
                round_trip=round_trip,
                stable_dump_exception_type=stable_dump_exception_type,
                validate_reference_shape=validate_reference_shape,
                repetitions=args.digest_repetitions,
            )
        )

    stream_results = [
        {
            "case_id": case.case_id,
            "wb_id": case.wb_id,
            "description": case.description,
            "observation": observation_dict(observe_loads(case.payload_factory())),
        }
        for case in invalid_stream_cases()
    ]

    version_results = []
    for version in range(marshal.version + 1):
        for case in format_version_cases(version):
            version_results.append(
                _run_value_case(
                    case,
                    assert_digest_stable=assert_digest_stable,
                    assert_round_trip_equivalent=assert_round_trip_equivalent,
                    round_trip=round_trip,
                    stable_dump_exception_type=stable_dump_exception_type,
                    validate_reference_shape=validate_reference_shape,
                    repetitions=args.digest_repetitions,
                    version=version,
                )
            )

    hash_seed_results = [
        run_hash_seed_child(case_name, seed)
        for case_name in hash_seed_cases()
        for seed in (1, 2, 3)
    ]
    hash_seed_payload = {
        "results": [hash_seed_result_dict(result) for result in hash_seed_results],
        "digest_classes": hash_seed_digest_classes(hash_seed_results),
    }
    hash_seed_output = args.results / "assignment_hash_seed_observations.json"
    hash_seed_output.write_text(
        json.dumps(hash_seed_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    summary = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "marshal_version": marshal.version,
        "workload": "assignment-specific source-informed marshal driver",
        "value_results": value_results,
        "stream_results": stream_results,
        "version_results": version_results,
        "hash_seed_results_path": hash_seed_output.as_posix(),
        "allow_code_supported": supports_allow_code(),
        "notes": [
            "CPython official test_marshal is an external baseline, "
            "not counted as assignment-specific white-box results.",
            "Stable unsupported buffer-like values are recorded by exception type.",
        ],
    }
    output = args.results / "assignment_whitebox_driver.json"
    output.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))

    failures = [
        result
        for group in (value_results, version_results)
        for result in group
        if result["status"] == "error"
    ]
    hash_seed_failures = [
        result
        for result in hash_seed_results
        if result.returncode != 0 or not result.digest
    ]
    return 1 if failures or hash_seed_failures else 0


def _run_value_case(
    case: Any,
    *,
    assert_digest_stable: Any,
    assert_round_trip_equivalent: Any,
    round_trip: Any,
    stable_dump_exception_type: Any,
    validate_reference_shape: Any,
    repetitions: int,
    version: int | None = None,
) -> dict[str, Any]:
    try:
        if case.allow_stable_exception:
            exception_type = stable_dump_exception_type(
                case.value_factory,
                version=version,
            )
            if exception_type is not None:
                return {
                    "case_id": case.case_id,
                    "wb_id": case.wb_id,
                    "source_area": case.source_area,
                    "version": version,
                    "status": "stable_exception",
                    "exception_type": exception_type,
                }

        value = case.value_factory()
        digest = assert_digest_stable(
            value,
            repetitions=repetitions,
            version=version,
        )
        loaded = round_trip(value, version=version)
        assert_round_trip_equivalent(value, loaded)
        validate_reference_shape(case.case_id, loaded)
    except Exception as exc:  # noqa: BLE001 - driver records failures as data.
        return {
            "case_id": case.case_id,
            "wb_id": case.wb_id,
            "source_area": case.source_area,
            "version": version,
            "status": "error",
            "exception_type": type(exc).__name__,
            "message": str(exc),
        }

    return {
        "case_id": case.case_id,
        "wb_id": case.wb_id,
        "source_area": case.source_area,
        "version": version,
        "status": "ok",
        "digest": digest,
    }


def _ensure_src_on_path() -> None:
    root = Path(__file__).resolve().parents[2]
    src = root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


if __name__ == "__main__":
    raise SystemExit(main())
