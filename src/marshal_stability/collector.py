"""Collect marshal digest records."""

from __future__ import annotations

import hashlib
import marshal
import platform
import sys
from dataclasses import dataclass
from typing import Any

from marshal_stability.cases import MarshalCase, supported_cases


@dataclass(frozen=True)
class DigestRecord:
    case_id: str
    status: str
    sha256: str | None
    length: int | None
    exception_type: str | None
    python_version: str
    implementation: str
    platform: str
    machine: str
    marshal_version: int
    strategies: tuple[str, ...]
    requirement: str

    def to_json(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "status": self.status,
            "sha256": self.sha256,
            "length": self.length,
            "exception_type": self.exception_type,
            "python_version": self.python_version,
            "implementation": self.implementation,
            "platform": self.platform,
            "machine": self.machine,
            "marshal_version": self.marshal_version,
            "strategies": list(self.strategies),
            "requirement": self.requirement,
        }


def digest_for_value(value: Any) -> tuple[str, int]:
    data = marshal.dumps(value)
    return hashlib.sha256(data).hexdigest(), len(data)


def collect_records(include_large: bool = False) -> list[DigestRecord]:
    return [record_for_case(case) for case in supported_cases(include_large)]


def record_for_case(case: MarshalCase) -> DigestRecord:
    try:
        sha256, length = digest_for_value(case.value)
    except Exception as exc:  # noqa: BLE001 - recorded as test data
        return _record(case, "error", None, None, type(exc).__name__)
    return _record(case, "ok", sha256, length, None)


def _record(
    case: MarshalCase,
    status: str,
    sha256: str | None,
    length: int | None,
    exception_type: str | None,
) -> DigestRecord:
    return DigestRecord(
        case_id=case.case_id,
        status=status,
        sha256=sha256,
        length=length,
        exception_type=exception_type,
        python_version=sys.version,
        implementation=platform.python_implementation(),
        platform=platform.platform(),
        machine=platform.machine(),
        marshal_version=marshal.version,
        strategies=case.strategies,
        requirement=case.requirement,
    )
