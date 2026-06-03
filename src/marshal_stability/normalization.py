"""Comparison helpers for values loaded through marshal."""

from __future__ import annotations

import math
import types
from collections.abc import Mapping, Sequence, Set
from typing import Any


def marshal_equal(left: Any, right: Any) -> bool:
    """Return whether two values are equivalent for marshal roundtrip checks."""

    if isinstance(left, float) and isinstance(right, float):
        if math.isnan(left) and math.isnan(right):
            return True
        return left == right and math.copysign(1.0, left) == math.copysign(1.0, right)

    if isinstance(left, complex) and isinstance(right, complex):
        return marshal_equal(left.real, right.real) and marshal_equal(
            left.imag, right.imag
        )

    if isinstance(left, types.CodeType) and isinstance(right, types.CodeType):
        return left.co_code == right.co_code and left.co_consts == right.co_consts

    if isinstance(left, bytearray) and isinstance(right, bytearray):
        return bytes(left) == bytes(right)

    if isinstance(left, tuple) and isinstance(right, tuple):
        return _sequence_equal(left, right)

    if isinstance(left, list) and isinstance(right, list):
        if _same_recursive_list_shape(left, right):
            return True
        return _sequence_equal(left, right)

    if isinstance(left, Mapping) and isinstance(right, Mapping):
        if _same_recursive_dict_shape(left, right):
            return True
        if left.keys() != right.keys():
            return False
        return all(marshal_equal(left[key], right[key]) for key in left)

    if isinstance(left, Set) and isinstance(right, Set) and not isinstance(
        left, (str, bytes, bytearray)
    ):
        return left == right

    return left == right


def _sequence_equal(left: Sequence[Any], right: Sequence[Any]) -> bool:
    return len(left) == len(right) and all(
        marshal_equal(left_value, right_value)
        for left_value, right_value in zip(left, right)
    )


def _same_recursive_list_shape(left: list[Any], right: list[Any]) -> bool:
    return len(left) == 1 and len(right) == 1 and left[0] is left and right[0] is right


def _same_recursive_dict_shape(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return (
        len(left) == 1
        and len(right) == 1
        and "self" in left
        and "self" in right
        and left["self"] is left
        and right["self"] is right
    )
