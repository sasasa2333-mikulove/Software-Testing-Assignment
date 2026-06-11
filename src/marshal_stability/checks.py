"""Reusable marshal byte-identity and round-trip checks."""

from __future__ import annotations

import hashlib
import inspect
import marshal
from typing import Any

from marshal_stability.normalization import marshal_equal


def marshal_bytes(obj: Any, *, version: int | None = None) -> bytes:
    """Return marshal bytes, keeping the format version positional."""

    if version is None:
        return marshal.dumps(obj)
    return marshal.dumps(obj, version)


def stable_digest(obj: Any, *, version: int | None = None) -> str:
    """Return the SHA-256 digest of the marshal byte stream."""

    return hashlib.sha256(marshal_bytes(obj, version=version)).hexdigest()


def round_trip(obj: Any, *, version: int | None = None) -> Any:
    """Marshal and unmarshal one value."""

    return marshal.loads(marshal_bytes(obj, version=version))


def assert_digest_stable(
    obj: Any,
    repetitions: int = 20,
    *,
    version: int | None = None,
) -> str:
    """Assert that repeated dumps of one value produce the same digest."""

    if repetitions < 1:
        raise ValueError("repetitions must be at least 1")

    expected = stable_digest(obj, version=version)
    for _ in range(repetitions - 1):
        assert stable_digest(obj, version=version) == expected
    return expected


def assert_round_trip_equivalent(original: Any, loaded: Any) -> None:
    """Assert marshal semantic equivalence, including NaN and -0.0 handling."""

    assert marshal_equal(original, loaded)


def supports_allow_code() -> bool:
    """Return whether this runtime exposes marshal allow_code parameters."""

    try:
        dumps_parameters = inspect.signature(marshal.dumps).parameters
        loads_parameters = inspect.signature(marshal.loads).parameters
    except (TypeError, ValueError):
        return False
    return "allow_code" in dumps_parameters and "allow_code" in loads_parameters
