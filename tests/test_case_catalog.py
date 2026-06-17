from __future__ import annotations

from marshal_stability.cases import all_cases, supported_cases, unsupported_cases


def test_case_ids_are_unique() -> None:
    cases = all_cases(include_large=True)
    case_ids = [case.case_id for case in cases]

    assert len(case_ids) == len(set(case_ids))


def test_supported_cases_cover_required_strategy_families() -> None:
    strategies = {
        strategy
        for case in supported_cases(include_large=True)
        for strategy in case.strategies
    }

    assert {"EP", "BVA", "white-box", "stability"} <= strategies


def test_unsupported_cases_are_negative_oracles() -> None:
    cases = unsupported_cases()

    assert cases
    assert all(not case.expect_roundtrip for case in cases)
    assert all("negative" in case.strategies for case in cases)


def test_large_cases_are_opt_in() -> None:
    default_ids = {case.case_id for case in supported_cases()}
    large_ids = {case.case_id for case in supported_cases(include_large=True)}

    assert "large_bytes" not in default_ids
    assert "large_list" not in default_ids
    assert {"large_bytes", "large_list"} <= large_ids


def test_supported_cases_cover_planned_common_catalog() -> None:
    case_ids = {case.case_id for case in supported_cases(include_large=True)}

    assert {
        "none",
        "bool_true",
        "bool_false",
        "ellipsis",
        "stop_iteration",
        "int_zero",
        "int_negative_one",
        "int_15bit_edge",
        "int_15bit_overflow",
        "int_32bit_edge",
        "int_32bit_overflow",
        "int_negative_32bit_edge",
        "int_63bit_edge",
        "int_63bit_overflow",
        "int_large",
        "float_zero",
        "float_negative_zero",
        "float_positive",
        "float_negative",
        "float_inf",
        "float_negative_inf",
        "float_nan",
        "float_subnormal",
        "complex_nan_inf",
        "empty_str",
        "ascii_str",
        "unicode_str",
        "empty_bytes",
        "bytes_with_null",
        "bytearray",
        "memoryview",
        "empty_tuple",
        "nested_tuple",
        "empty_list",
        "nested_list",
        "empty_dict",
        "nested_dict",
        "empty_set",
        "set_of_ints",
        "set_of_strings",
        "empty_frozenset",
        "frozenset_of_strings",
        "recursive_list",
        "recursive_dict",
        "shared_child_list",
        "nested_shared_graph",
        "code_object",
        "large_bytes",
        "large_list",
    } <= case_ids


def test_unsupported_cases_cover_planned_negative_catalog() -> None:
    case_ids = {case.case_id for case in unsupported_cases()}

    assert {
        "function_object",
        "plain_object",
        "nested_unsupported_list",
        "nested_unsupported_dict",
    } <= case_ids
