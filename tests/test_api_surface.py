from __future__ import annotations

import io
import marshal

import pytest

from marshal_stability.normalization import marshal_equal


def test_dumps_and_loads_roundtrip_documented_value() -> None:
    value = {"numbers": [1, 2, 3], "text": "marshal"}

    loaded = marshal.loads(marshal.dumps(value))

    assert marshal_equal(value, loaded)


def test_dump_and_load_file_api_roundtrip() -> None:
    value = (None, True, "file-api", b"bytes")
    stream = io.BytesIO()

    marshal.dump(value, stream)
    stream.seek(0)

    assert marshal_equal(value, marshal.load(stream))


def test_dump_rejects_unwritable_file_object() -> None:
    with pytest.raises((AttributeError, TypeError)):
        marshal.dump({"x": 1}, object())


def test_load_rejects_unreadable_file_object() -> None:
    with pytest.raises((AttributeError, TypeError)):
        marshal.load(object())


def test_loads_allows_trailing_bytes_after_one_value() -> None:
    first = marshal.dumps("first")
    trailing = marshal.dumps("second")

    assert marshal.loads(first + trailing) == "first"


def test_load_reads_exactly_one_value_from_stream() -> None:
    stream = io.BytesIO(marshal.dumps("first") + marshal.dumps("second"))

    assert marshal.load(stream) == "first"
    assert marshal.load(stream) == "second"
