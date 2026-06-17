from __future__ import annotations

import marshal

import pytest


@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"\xff",
        b"i",
        marshal.dumps([1, 2, 3])[:2],
        marshal.dumps({"a": "b"})[:-1],
    ],
)
def test_loads_rejects_invalid_or_truncated_bytes(payload: bytes) -> None:
    with pytest.raises((EOFError, ValueError, TypeError)):
        marshal.loads(payload)


@pytest.mark.parametrize("payload", [None, 1, "not-bytes", object()])
def test_loads_rejects_non_bytes_input(payload) -> None:
    with pytest.raises(TypeError):
        marshal.loads(payload)


def test_nested_unsupported_value_raises_value_error() -> None:
    with pytest.raises(ValueError):
        marshal.dumps({"unsupported": object()})


def test_recursive_unsupported_container_raises_value_error() -> None:
    value = []
    value.append(object())

    with pytest.raises(ValueError):
        marshal.dumps(value)
