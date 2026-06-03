from __future__ import annotations

import marshal
import sys

import pytest

from marshal_stability.cases import sample_function
from marshal_stability.normalization import marshal_equal


DOCUMENTED_VALUES = [
    None,
    Ellipsis,
    StopIteration,
    False,
    True,
    42,
    -(2**63),
    2**100,
    1.25,
    -0.0,
    float("inf"),
    float("nan"),
    complex(1.5, -2.5),
    "",
    "unicode: åäö 中文",
    b"",
    b"\x00\xff",
    bytearray(b"buffer"),
    memoryview(b"view"),
    (),
    (1, "a", b"b"),
    [],
    [1, "a", b"b"],
    {},
    {"a": 1, "b": [2, 3]},
    set(),
    {1, 2, 3},
    frozenset(),
    frozenset({1, 2, 3}),
    sample_function.__code__,
]


@pytest.mark.parametrize("value", DOCUMENTED_VALUES, ids=repr)
def test_documented_supported_types_roundtrip(value) -> None:
    loaded = marshal.loads(marshal.dumps(value))

    assert marshal_equal(value, loaded)


def test_documented_recursive_list_roundtrip() -> None:
    value = []
    value.append(value)

    loaded = marshal.loads(marshal.dumps(value))

    assert loaded[0] is loaded


def test_documented_recursive_dict_roundtrip() -> None:
    value = {}
    value["self"] = value

    loaded = marshal.loads(marshal.dumps(value))

    assert loaded["self"] is loaded


@pytest.mark.skipif(
    sys.version_info < (3, 14) or marshal.version < 5,
    reason="slice marshal support was added in Python 3.14 format version 5",
)
def test_documented_slice_roundtrip_on_python_314() -> None:
    value = slice(1, 10, 2)

    loaded = marshal.loads(marshal.dumps(value))

    assert loaded == value
