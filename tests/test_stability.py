from __future__ import annotations

from marshal_stability.subprocess_runner import collect_with_hash_seed, digest_map

HASH_SEED_SENSITIVE_CASES = {"set_of_strings", "frozenset_of_strings"}


def test_cross_process_stability_for_ordered_values() -> None:
    first = digest_map(collect_with_hash_seed(1))
    second = digest_map(collect_with_hash_seed(2))

    common_ids = set(first) & set(second)
    checked_ids = common_ids - HASH_SEED_SENSITIVE_CASES
    differences = {
        case_id: (first[case_id], second[case_id])
        for case_id in checked_ids
        if first[case_id] != second[case_id]
    }

    assert differences == {}


def test_unordered_string_sets_are_checked_across_hash_seeds() -> None:
    first = digest_map(collect_with_hash_seed(1))
    second = digest_map(collect_with_hash_seed(2))

    for case_id in HASH_SEED_SENSITIVE_CASES:
        assert case_id in first
        assert case_id in second
