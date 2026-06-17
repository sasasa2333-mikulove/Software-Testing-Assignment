from __future__ import annotations

import inspect
import marshal
import sys

import pytest

from marshal_stability.cases import sample_function


def test_all_supported_format_versions_can_dump_simple_value() -> None:
    for version in range(marshal.version + 1):
        data = marshal.dumps({"version": version}, version)
        assert marshal.loads(data) == {"version": version}


def test_too_high_format_version_still_produces_loadable_bytes() -> None:
    data = marshal.dumps("x", marshal.version + 100)

    assert marshal.loads(data) == "x"


@pytest.mark.skipif(
    "allow_code" not in inspect.signature(marshal.dumps).parameters,
    reason="allow_code was added after this Python version",
)
def test_dumps_allow_code_false_rejects_code_object() -> None:
    with pytest.raises(ValueError):
        marshal.dumps(sample_function.__code__, allow_code=False)


@pytest.mark.skipif(
    "allow_code" not in inspect.signature(marshal.loads).parameters,
    reason="allow_code was added after this Python version",
)
def test_loads_allow_code_false_rejects_code_object() -> None:
    data = marshal.dumps(sample_function.__code__, allow_code=True)

    with pytest.raises(ValueError):
        marshal.loads(data, allow_code=False)


@pytest.mark.skipif(
    sys.version_info < (3, 14) or marshal.version < 5,
    reason="slice marshal support was added in Python 3.14 format version 5",
)
def test_slice_requires_latest_format_version() -> None:
    data = marshal.dumps(slice(1, 3), marshal.version)
    assert marshal.loads(data) == slice(1, 3)
