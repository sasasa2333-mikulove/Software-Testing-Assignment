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
