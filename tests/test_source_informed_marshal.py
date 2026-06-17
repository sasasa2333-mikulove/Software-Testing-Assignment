from __future__ import annotations

import marshal
import re

import pytest

from marshal_stability.checks import (
    assert_digest_stable,
    assert_round_trip_equivalent,
    round_trip,
    stable_digest,
    supports_allow_code,
)
from marshal_stability.source_informed import (
    SourceCase,
    accepted_format_versions,
    code_object_cases,
    complex_cases,
    container_cases,
    float_cases,
    format_version_cases,
    hash_seed_cases,
    hash_seed_digest_classes,
    integer_cases,
    invalid_stream_cases,
    observe_loads,
    primitive_cases,
    reference_cases,
    run_hash_seed_child,
    stable_dump_exception_type,
    text_and_binary_cases,
    validate_reference_shape,
)


def _assert_case_roundtrips_or_has_stable_exception(
    case: SourceCase,
    *,
    repetitions: int = 5,
    version: int | None = None,
) -> None:
    if case.allow_stable_exception:
        exception_type = stable_dump_exception_type(
            case.value_factory,
            version=version,
        )
        if exception_type is not None:
            allowed_names = {
                exception.__name__ for exception in case.allowed_exception_types
            }
            assert exception_type in allowed_names
            return

    value = case.value_factory()
    assert_digest_stable(value, repetitions=repetitions, version=version)
    loaded = round_trip(value, version=version)
    assert_round_trip_equivalent(value, loaded)
    validate_reference_shape(case.case_id, loaded)


@pytest.mark.parametrize("case", primitive_cases(), ids=lambda case: case.case_id)
def test_wb1_primitive_singleton_type_dispatch(case: SourceCase) -> None:
    _assert_case_roundtrips_or_has_stable_exception(case)


@pytest.mark.parametrize("case", integer_cases(), ids=lambda case: case.case_id)
def test_wb2_integer_encoding_boundaries(case: SourceCase) -> None:
    _assert_case_roundtrips_or_has_stable_exception(case)


@pytest.mark.parametrize("case", float_cases(), ids=lambda case: case.case_id)
def test_wb3_float_paths(case: SourceCase) -> None:
    _assert_case_roundtrips_or_has_stable_exception(case)


@pytest.mark.parametrize("case", complex_cases(), ids=lambda case: case.case_id)
def test_wb3_complex_paths(case: SourceCase) -> None:
    _assert_case_roundtrips_or_has_stable_exception(case)


@pytest.mark.parametrize("case", text_and_binary_cases(), ids=lambda case: case.case_id)
def test_wb4_string_bytes_and_buffer_paths(case: SourceCase) -> None:
    _assert_case_roundtrips_or_has_stable_exception(case)


@pytest.mark.parametrize(
    "case",
    container_cases(include_large=True),
    ids=lambda case: case.case_id,
)
def test_wb5_container_writer_paths(case: SourceCase) -> None:
    repetitions = 3 if case.case_id.endswith("_1000") else 5
    _assert_case_roundtrips_or_has_stable_exception(case, repetitions=repetitions)


@pytest.mark.parametrize("case", reference_cases(), ids=lambda case: case.case_id)
def test_wb6_reference_tracking_and_recursive_structures(case: SourceCase) -> None:
    _assert_case_roundtrips_or_has_stable_exception(case)


@pytest.mark.parametrize("case", code_object_cases(), ids=lambda case: case.case_id)
def test_wb7_code_object_roundtrip(case: SourceCase) -> None:
    _assert_case_roundtrips_or_has_stable_exception(case)


def test_wb7_allow_code_false_rejects_code_objects_when_supported() -> None:
    if not supports_allow_code():
        pytest.skip("marshal allow_code parameter is not exposed by this runtime")

    code_object = code_object_cases()[0].value_factory()

    with pytest.raises(ValueError):
        marshal.dumps(code_object, allow_code=False)

    data = marshal.dumps(code_object, allow_code=True)
    with pytest.raises(ValueError):
        marshal.loads(data, allow_code=False)


@pytest.mark.parametrize("case", invalid_stream_cases(), ids=lambda case: case.case_id)
def test_wb8_reader_dispatch_invalid_and_edge_streams(case) -> None:
    first = observe_loads(case.payload_factory())
    second = observe_loads(case.payload_factory())

    assert first == second
    if case.case_id in {"empty_stream", "invalid_tag", "truncated_valid_dump"}:
        assert first.status == "error"
        assert first.exception_type in {"EOFError", "TypeError", "ValueError"}


@pytest.mark.parametrize(
    "version",
    accepted_format_versions(),
    ids=lambda version: f"version_{version}",
)
def test_wb9_supported_marshal_format_versions(version: int) -> None:
    for case in format_version_cases(version):
        _assert_case_roundtrips_or_has_stable_exception(
            case,
            repetitions=3,
            version=version,
        )


def test_wb10_cross_process_hash_seed_digest_observations() -> None:
    results = [
        run_hash_seed_child(case_name, seed)
        for case_name in hash_seed_cases()
        for seed in (1, 2, 3)
    ]

    for result in results:
        assert result.returncode == 0, result.stderr
        assert re.fullmatch(r"[0-9a-f]{64}", result.digest)

    digest_classes = hash_seed_digest_classes(results)
    assert set(digest_classes) == set(hash_seed_cases())


def test_required_digest_helper_uses_sha256() -> None:
    digest = stable_digest({"source": "marshal.c"})

    assert re.fullmatch(r"[0-9a-f]{64}", digest)
