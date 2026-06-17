"""Curated marshal test cases.

The catalog is intentionally explicit. Each case links one concrete value to
the test-design method that motivated it, which keeps the traceability matrix in
the report honest and makes failures easy to interpret.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MarshalCase:
    """A concrete marshal input with traceability metadata."""

    case_id: str
    value: Any
    strategies: tuple[str, ...]
    requirement: str
    expect_roundtrip: bool = True
    notes: str = ""
    tags: frozenset[str] = field(default_factory=frozenset)


def _recursive_list() -> list[Any]:
    value: list[Any] = []
    value.append(value)
    return value


def _recursive_dict() -> dict[str, Any]:
    value: dict[str, Any] = {}
    value["self"] = value
    return value


def _shared_child_list() -> list[Any]:
    child: list[Any] = ["shared"]
    return [child, child]


def _nested_shared_graph() -> dict[str, list[Any]]:
    child = {"leaf": [1, 2, 3]}
    return {"left": [child], "right": [child]}


def sample_function(value: int = 3) -> int:
    return value + 1


def supported_cases(include_large: bool = False) -> list[MarshalCase]:
    """Return deterministic, supported values for CPython marshal."""

    cases = [
        MarshalCase(
            "none",
            None,
            ("EP",),
            "supported singleton values are serializable",
        ),
        MarshalCase(
            "bool_true",
            True,
            ("EP",),
            "boolean values are serializable",
        ),
        MarshalCase(
            "bool_false",
            False,
            ("EP",),
            "boolean values are serializable",
        ),
        MarshalCase(
            "ellipsis",
            Ellipsis,
            ("EP",),
            "supported singleton values are serializable",
        ),
        MarshalCase(
            "stop_iteration",
            StopIteration,
            ("EP",),
            "supported singleton values are serializable",
        ),
        MarshalCase(
            "int_zero",
            0,
            ("EP", "BVA"),
            "integer boundary values are serializable",
        ),
        MarshalCase(
            "int_negative_one",
            -1,
            ("EP", "BVA"),
            "integer boundary values are serializable",
        ),
        MarshalCase(
            "int_15bit_edge",
            2**15 - 1,
            ("BVA", "white-box"),
            "15-bit integer boundary remains stable",
        ),
        MarshalCase(
            "int_15bit_overflow",
            2**15,
            ("BVA", "white-box"),
            "integer encoding boundary remains stable",
        ),
        MarshalCase(
            "int_32bit_edge",
            2**31 - 1,
            ("BVA", "white-box"),
            "32-bit integer boundary remains stable",
        ),
        MarshalCase(
            "int_32bit_overflow",
            2**31,
            ("BVA", "white-box"),
            "long integer path remains stable",
        ),
        MarshalCase(
            "int_negative_32bit_edge",
            -(2**31),
            ("BVA", "white-box"),
            "negative 32-bit integer boundary remains stable",
        ),
        MarshalCase(
            "int_63bit_edge",
            2**63 - 1,
            ("BVA", "white-box"),
            "63-bit integer boundary remains stable",
        ),
        MarshalCase(
            "int_63bit_overflow",
            2**63,
            ("BVA", "white-box"),
            "large integer encoding boundary remains stable",
        ),
        MarshalCase(
            "int_large",
            2**100 + 12345,
            ("BVA",),
            "large arbitrary precision integers are serializable",
        ),
        MarshalCase(
            "float_zero",
            0.0,
            ("EP", "BVA"),
            "floating-point zero is byte-stable",
        ),
        MarshalCase(
            "float_negative_zero",
            -0.0,
            ("BVA",),
            "floating-point sign edge cases are byte-stable",
        ),
        MarshalCase(
            "float_positive",
            1.5,
            ("EP",),
            "ordinary positive floats are serializable",
        ),
        MarshalCase(
            "float_negative",
            -2.25,
            ("EP",),
            "ordinary negative floats are serializable",
        ),
        MarshalCase(
            "float_subnormal",
            5e-324,
            ("BVA",),
            "subnormal floats are byte-stable",
        ),
        MarshalCase(
            "float_inf",
            float("inf"),
            ("EP", "BVA"),
            "floating-point special values are serializable",
        ),
        MarshalCase(
            "float_negative_inf",
            float("-inf"),
            ("EP", "BVA"),
            "negative infinity is serializable",
        ),
        MarshalCase(
            "float_nan",
            float("nan"),
            ("EP", "BVA"),
            "NaN values are serializable and repeatable",
            notes="Roundtrip semantic equality is normalized because NaN != NaN.",
        ),
        MarshalCase(
            "complex_nan_inf",
            complex(float("nan"), float("-inf")),
            ("EP", "BVA"),
            "complex numbers follow float special-value behavior",
        ),
        MarshalCase(
            "empty_str",
            "",
            ("EP", "BVA"),
            "empty strings are serializable",
        ),
        MarshalCase(
            "ascii_str",
            "marshal",
            ("EP",),
            "ASCII strings are serializable",
        ),
        MarshalCase(
            "unicode_str",
            "marshal stability: åäö 中文",
            ("EP",),
            "unicode strings are serializable",
        ),
        MarshalCase(
            "empty_bytes",
            b"",
            ("EP", "BVA"),
            "empty bytes are serializable",
        ),
        MarshalCase(
            "bytes_with_null",
            b"abc\x00def",
            ("EP", "BVA"),
            "bytes containing NUL bytes are serializable",
        ),
        MarshalCase(
            "bytearray",
            bytearray(b"abc\x00def"),
            ("EP",),
            "bytearrays are serializable",
        ),
        MarshalCase(
            "memoryview",
            memoryview(b"abc"),
            ("EP", "white-box"),
            "buffer protocol inputs serialize through the bytes path",
            notes="CPython loads this value back as bytes.",
        ),
        MarshalCase(
            "empty_tuple",
            (),
            ("EP", "BVA"),
            "empty immutable containers are serializable",
        ),
        MarshalCase(
            "nested_tuple",
            (1, "a", (2, b"b")),
            ("EP",),
            "nested immutable containers are serializable",
        ),
        MarshalCase(
            "empty_list",
            [],
            ("EP", "BVA"),
            "empty mutable containers are serializable",
        ),
        MarshalCase(
            "nested_list",
            [1, "a", [2, b"b"]],
            ("EP",),
            "nested mutable containers are serializable",
        ),
        MarshalCase(
            "recursive_list",
            _recursive_list(),
            ("EP", "white-box"),
            "recursive lists are handled by marshal reference tracking",
            tags=frozenset({"recursive"}),
        ),
        MarshalCase(
            "empty_dict",
            {},
            ("EP", "BVA"),
            "empty dictionaries are serializable",
        ),
        MarshalCase(
            "nested_dict",
            {"a": 1, "b": (2, 3), "c": {"inner": b"x"}},
            ("EP",),
            "nested dictionaries are serializable",
        ),
        MarshalCase(
            "recursive_dict",
            _recursive_dict(),
            ("EP", "white-box"),
            "recursive dictionaries are handled by marshal reference tracking",
            tags=frozenset({"recursive"}),
        ),
        MarshalCase(
            "shared_child_list",
            _shared_child_list(),
            ("EP", "white-box"),
            "shared child containers are handled by marshal reference tracking",
            tags=frozenset({"shared-reference"}),
        ),
        MarshalCase(
            "nested_shared_graph",
            _nested_shared_graph(),
            ("EP", "white-box"),
            "nested shared object graphs preserve shared references",
            tags=frozenset({"shared-reference"}),
        ),
        MarshalCase(
            "empty_set",
            set(),
            ("EP", "BVA"),
            "empty sets are serializable",
        ),
        MarshalCase(
            "set_of_ints",
            {3, 1, 2},
            ("EP",),
            "sets are serializable",
        ),
        MarshalCase(
            "empty_frozenset",
            frozenset(),
            ("EP", "BVA"),
            "empty frozensets are serializable",
        ),
        MarshalCase(
            "set_of_strings",
            {"alpha", "beta", "gamma"},
            ("EP", "stability"),
            "unordered string sets are checked across hash seeds",
            tags=frozenset({"hash-seed-sensitive"}),
        ),
        MarshalCase(
            "frozenset_of_strings",
            frozenset({"alpha", "beta", "gamma"}),
            ("EP", "stability"),
            "unordered string frozensets are checked across hash seeds",
            tags=frozenset({"hash-seed-sensitive"}),
        ),
        MarshalCase(
            "code_object",
            sample_function.__code__,
            ("EP", "white-box"),
            "code objects are serializable when allow_code permits them",
            tags=frozenset({"code-object"}),
        ),
    ]
    if include_large:
        cases.extend(
            [
                MarshalCase(
                    "large_bytes",
                    bytes(range(256)) * 256,
                    ("BVA",),
                    "larger byte sequences remain stable",
                    tags=frozenset({"large"}),
                ),
                MarshalCase(
                    "large_list",
                    list(range(2048)),
                    ("BVA",),
                    "larger collections remain stable",
                    tags=frozenset({"large"}),
                ),
            ]
        )
    return cases


def unsupported_cases() -> list[MarshalCase]:
    """Return values that marshal should reject."""

    return [
        MarshalCase(
            "function_object",
            sample_function,
            ("EP", "negative"),
            "function objects are unsupported",
            expect_roundtrip=False,
        ),
        MarshalCase(
            "plain_object",
            object(),
            ("EP", "negative"),
            "arbitrary object instances are unsupported",
            expect_roundtrip=False,
        ),
        MarshalCase(
            "nested_unsupported_list",
            [object()],
            ("EP", "negative"),
            "unsupported values nested in lists are rejected",
            expect_roundtrip=False,
        ),
        MarshalCase(
            "nested_unsupported_dict",
            {"unsupported": object()},
            ("EP", "negative"),
            "unsupported values nested in dictionaries are rejected",
            expect_roundtrip=False,
        ),
    ]


def all_cases(include_large: bool = False) -> list[MarshalCase]:
    return supported_cases(include_large=include_large) + unsupported_cases()
