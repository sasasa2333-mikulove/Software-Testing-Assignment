from __future__ import annotations

import marshal

import pytest

from marshal_stability.cases import supported_cases, unsupported_cases
from marshal_stability.normalization import marshal_equal


@pytest.mark.parametrize("case", supported_cases(), ids=lambda case: case.case_id)
def test_supported_values_roundtrip(case) -> None:
    data = marshal.dumps(case.value)
    loaded = marshal.loads(data)

    assert marshal_equal(case.value, loaded)


@pytest.mark.parametrize("case", supported_cases(), ids=lambda case: case.case_id)
def test_supported_values_are_stable_within_process(case) -> None:
    first = marshal.dumps(case.value)
    second = marshal.dumps(case.value)

    assert first == second


@pytest.mark.parametrize("case", unsupported_cases(), ids=lambda case: case.case_id)
def test_unsupported_values_raise_value_error(case) -> None:
    with pytest.raises(ValueError):
        marshal.dumps(case.value)


def test_recursive_list_roundtrip_preserves_cycle() -> None:
    value = []
    value.append(value)

    loaded = marshal.loads(marshal.dumps(value))

    assert loaded[0] is loaded


def test_recursive_dict_roundtrip_preserves_cycle() -> None:
    value = {}
    value["self"] = value

    loaded = marshal.loads(marshal.dumps(value))

    assert loaded["self"] is loaded


def test_shared_child_list_roundtrip_preserves_identity() -> None:
    child = ["shared"]
    value = [child, child]

    loaded = marshal.loads(marshal.dumps(value))

    assert loaded[0] is loaded[1]


def test_nested_shared_graph_roundtrip_preserves_identity() -> None:
    child = {"leaf": [1, 2, 3]}
    value = {"left": [child], "right": [child]}

    loaded = marshal.loads(marshal.dumps(value))

    assert loaded["left"][0] is loaded["right"][0]
