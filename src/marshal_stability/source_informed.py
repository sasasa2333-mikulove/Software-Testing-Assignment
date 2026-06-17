"""Assignment-specific source-informed cases for CPython marshal.c."""

from __future__ import annotations

import json
import marshal
import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any

from marshal_stability.checks import marshal_bytes


@dataclass(frozen=True)
class SourceCase:
    """A marshal value tied to a selected marshal.c source obligation."""

    case_id: str
    wb_id: str
    source_area: str
    value_factory: Callable[[], Any]
    allow_stable_exception: bool = False
    allowed_exception_types: tuple[type[BaseException], ...] = (
        TypeError,
        ValueError,
    )


@dataclass(frozen=True)
class ByteStreamCase:
    """An invalid or edge-case reader payload."""

    case_id: str
    wb_id: str
    description: str
    payload_factory: Callable[[], bytes]


@dataclass(frozen=True)
class LoadObservation:
    """Stable observation of marshal.loads behavior for one byte stream."""

    status: str
    value_type: str | None = None
    value_repr: str | None = None
    exception_type: str | None = None


@dataclass(frozen=True)
class HashSeedResult:
    """Digest result returned by a hash-seeded child process."""

    case_name: str
    seed: int
    returncode: int
    digest: str
    python_version: str
    stdout: str
    stderr: str


def sample_source_function(value: int = 7) -> int:
    """Small function used to reach the code-object marshal path."""

    return value * 2 + 1


def primitive_cases() -> list[SourceCase]:
    return [
        SourceCase("none", "WB1", "primitive type dispatch", lambda: None),
        SourceCase("true", "WB1", "primitive type dispatch", lambda: True),
        SourceCase("false", "WB1", "primitive type dispatch", lambda: False),
        SourceCase(
            "stop_iteration",
            "WB1",
            "primitive type dispatch",
            lambda: StopIteration,
            allow_stable_exception=True,
        ),
        SourceCase(
            "ellipsis",
            "WB1",
            "primitive type dispatch",
            lambda: Ellipsis,
            allow_stable_exception=True,
        ),
    ]


def integer_cases() -> list[SourceCase]:
    values = [
        ("zero", 0),
        ("one", 1),
        ("minus_one", -1),
        ("int_15bit_max", 2**15 - 1),
        ("int_15bit_boundary", 2**15),
        ("int_negative_15bit_boundary", -(2**15)),
        ("int_31bit_max", 2**31 - 1),
        ("int_31bit_boundary", 2**31),
        ("int_negative_31bit_boundary", -(2**31)),
        ("int_below_negative_31bit_boundary", -(2**31) - 1),
        ("int_63bit_max", 2**63 - 1),
        ("int_63bit_boundary", 2**63),
        ("int_negative_63bit_boundary", -(2**63)),
        ("int_very_large", 2**1000),
    ]
    return [
        SourceCase(
            case_id,
            "WB2",
            "integer encoding branches",
            lambda value=value: value,
        )
        for case_id, value in values
    ]


def float_cases() -> list[SourceCase]:
    values = [
        ("float_zero", 0.0),
        ("float_negative_zero", -0.0),
        ("float_positive", 1.5),
        ("float_negative", -2.25),
        ("float_inf", float("inf")),
        ("float_negative_inf", float("-inf")),
        ("float_nan", float("nan")),
        ("float_subnormal", 5e-324),
    ]
    return [
        SourceCase(
            case_id,
            "WB3",
            "float writer and reader paths",
            lambda value=value: value,
        )
        for case_id, value in values
    ]


def complex_cases() -> list[SourceCase]:
    values = [
        ("complex_normal", complex(1.0, -2.0)),
        ("complex_zeroes", complex(0.0, -0.0)),
        ("complex_special", complex(float("nan"), float("inf"))),
    ]
    return [
        SourceCase(
            case_id,
            "WB3",
            "complex writer and reader paths",
            lambda value=value: value,
        )
        for case_id, value in values
    ]


def text_and_binary_cases() -> list[SourceCase]:
    values: list[SourceCase] = [
        SourceCase("empty_str", "WB4", "unicode string path", lambda: ""),
        SourceCase("ascii_str", "WB4", "unicode string path", lambda: "marshal"),
        SourceCase("unicode_str", "WB4", "unicode string path", lambda: "åäö 中文"),
        SourceCase("emoji_str", "WB4", "unicode string path", lambda: "marshal 🔒"),
        SourceCase("empty_bytes", "WB4", "bytes path", lambda: b""),
        SourceCase("short_bytes", "WB4", "bytes path", lambda: b"abc\x00def"),
        SourceCase("bytes_255", "WB4", "bytes length boundary", lambda: _bytes(255)),
        SourceCase("bytes_256", "WB4", "bytes length boundary", lambda: _bytes(256)),
        SourceCase("bytes_257", "WB4", "bytes length boundary", lambda: _bytes(257)),
        SourceCase("bytes_4096", "WB4", "bytes length boundary", lambda: _bytes(4096)),
        SourceCase(
            "bytearray",
            "WB4",
            "buffer-like input path",
            lambda: bytearray(b"abc\x00def"),
            allow_stable_exception=True,
        ),
        SourceCase(
            "memoryview",
            "WB4",
            "buffer-like input path",
            lambda: memoryview(b"abc\x00def"),
            allow_stable_exception=True,
        ),
    ]
    return values


def container_cases(include_large: bool = False) -> list[SourceCase]:
    cases = [
        SourceCase("empty_tuple", "WB5", "tuple writer loop", lambda: ()),
        SourceCase(
            "non_empty_tuple", "WB5", "tuple writer loop", lambda: (1, "a", b"b")
        ),
        SourceCase("empty_list", "WB5", "list writer loop", list),
        SourceCase(
            "non_empty_list",
            "WB5",
            "list writer loop",
            lambda: [1, "a", b"b"],
        ),
        SourceCase("empty_dict", "WB5", "dict writer loop", dict),
        SourceCase(
            "non_empty_dict", "WB5", "dict writer loop", lambda: {"a": 1, "b": 2}
        ),
        SourceCase("empty_set", "WB5", "set writer loop", set),
        SourceCase("int_set", "WB5", "set writer loop", lambda: {1, 2, 3}),
        SourceCase(
            "string_set", "WB5", "set writer loop", lambda: {"alpha", "beta", "gamma"}
        ),
        SourceCase("empty_frozenset", "WB5", "frozenset writer loop", frozenset),
        SourceCase(
            "string_frozenset",
            "WB5",
            "frozenset writer loop",
            lambda: frozenset({"alpha", "beta", "gamma"}),
        ),
        SourceCase(
            "nested_containers",
            "WB5",
            "nested container recursion",
            lambda: {"items": [(1, 2), [b"x", {"inner": "y"}]]},
        ),
    ]
    if include_large:
        for size in (0, 1, 2, 255, 256, 1000):
            cases.append(
                SourceCase(
                    f"list_size_{size}",
                    "WB5",
                    "list length boundary",
                    lambda size=size: list(range(size)),
                )
            )
            cases.append(
                SourceCase(
                    f"dict_size_{size}",
                    "WB5",
                    "dict length boundary",
                    lambda size=size: {str(index): index for index in range(size)},
                )
            )
    return cases


def reference_cases() -> list[SourceCase]:
    return [
        SourceCase("recursive_list", "WB6", "reference table state", _recursive_list),
        SourceCase("recursive_dict", "WB6", "reference table state", _recursive_dict),
        SourceCase("shared_child_list", "WB6", "TYPE_REF reuse", _shared_child_list),
        SourceCase(
            "nested_shared_graph", "WB6", "TYPE_REF reuse", _nested_shared_graph
        ),
    ]


def code_object_cases() -> list[SourceCase]:
    return [
        SourceCase(
            "sample_code_object",
            "WB7",
            "code-object writer and reader path",
            lambda: sample_source_function.__code__,
        )
    ]


def assignment_value_cases(include_large: bool = False) -> list[SourceCase]:
    return (
        primitive_cases()
        + integer_cases()
        + float_cases()
        + complex_cases()
        + text_and_binary_cases()
        + container_cases(include_large=include_large)
        + reference_cases()
        + code_object_cases()
    )


def invalid_stream_cases() -> list[ByteStreamCase]:
    return [
        ByteStreamCase("empty_stream", "WB8", "empty input", lambda: b""),
        ByteStreamCase(
            "invalid_tag", "WB8", "single invalid tag byte", lambda: b"\xff"
        ),
        ByteStreamCase(
            "truncated_valid_dump",
            "WB8",
            "valid dump with final byte removed",
            lambda: marshal_bytes([1, 2, 3])[:-1],
        ),
        ByteStreamCase(
            "corrupted_middle_byte",
            "WB8",
            "valid dump with one middle byte flipped",
            lambda: _corrupt_middle(
                marshal_bytes({"alpha": [1, 2, 3], "omega": "tail"})
            ),
        ),
        ByteStreamCase(
            "trailing_bytes",
            "WB8",
            "valid dump followed by another marshal payload",
            lambda: marshal_bytes("first") + marshal_bytes("second"),
        ),
    ]


def accepted_format_versions() -> list[int]:
    versions = []
    for version in range(marshal.version + 1):
        try:
            marshal_bytes(None, version=version)
        except (TypeError, ValueError):
            continue
        versions.append(version)
    return versions


def format_version_cases(version: int) -> list[SourceCase]:
    cases = [
        SourceCase(f"version_{version}_none", "WB9", "format version", lambda: None),
        SourceCase(f"version_{version}_int", "WB9", "format version", lambda: 2**31),
        SourceCase(
            f"version_{version}_float",
            "WB9",
            "format version",
            lambda: -0.0,
        ),
        SourceCase(
            f"version_{version}_str", "WB9", "format version", lambda: "version"
        ),
        SourceCase(
            f"version_{version}_bytes", "WB9", "format version", lambda: b"bytes"
        ),
        SourceCase(
            f"version_{version}_tuple",
            "WB9",
            "format version",
            lambda: (1, "a", b"b"),
        ),
        SourceCase(
            f"version_{version}_list",
            "WB9",
            "format version",
            lambda: [1, 2, 3],
        ),
        SourceCase(
            f"version_{version}_dict",
            "WB9",
            "format version",
            lambda: {"version": version},
        ),
    ]
    if version_supports_references(version):
        cases.append(
            SourceCase(
                f"version_{version}_recursive_list",
                "WB9",
                "format version reference support",
                _recursive_list,
            )
        )
    return cases


def version_supports_references(version: int) -> bool:
    value = _recursive_list()
    try:
        loaded = marshal.loads(marshal_bytes(value, version=version))
    except (EOFError, TypeError, ValueError):
        return False
    return isinstance(loaded, list) and len(loaded) == 1 and loaded[0] is loaded


def stable_dump_exception_type(
    value_factory: Callable[[], Any],
    *,
    version: int | None = None,
    attempts: int = 3,
) -> str | None:
    exception_types = []
    for _ in range(attempts):
        value = value_factory()
        try:
            marshal_bytes(value, version=version)
        except (TypeError, ValueError) as exc:
            exception_types.append(type(exc).__name__)
        else:
            return None

    if len(set(exception_types)) != 1:
        raise AssertionError(f"unstable exception types: {exception_types}")
    return exception_types[0]


def observe_loads(payload: bytes) -> LoadObservation:
    try:
        value = marshal.loads(payload)
    except Exception as exc:  # noqa: BLE001 - invalid byte streams may fail many ways.
        return LoadObservation(status="error", exception_type=type(exc).__name__)
    return LoadObservation(
        status="ok",
        value_type=type(value).__name__,
        value_repr=repr(value),
    )


def validate_reference_shape(case_id: str, loaded: Any) -> None:
    if case_id == "recursive_list":
        assert isinstance(loaded, list)
        assert len(loaded) == 1
        assert loaded[0] is loaded
    elif case_id == "recursive_dict":
        assert isinstance(loaded, dict)
        assert loaded["self"] is loaded
    elif case_id == "shared_child_list":
        assert isinstance(loaded, list)
        assert loaded[0] is loaded[1]
    elif case_id == "nested_shared_graph":
        assert isinstance(loaded, dict)
        assert loaded["left"][0] is loaded["right"][0]


def hash_seed_cases() -> list[str]:
    return [
        "dict_string_keys",
        "set_strings",
        "frozenset_strings",
        "set_ints",
    ]


def run_hash_seed_child(case_name: str, seed: int) -> HashSeedResult:
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = str(seed)
    completed = subprocess.run(
        [sys.executable, "-c", _HASH_SEED_CHILD_CODE, case_name],
        capture_output=True,
        env=env,
        text=True,
        timeout=10,
        check=False,
    )

    digest = ""
    python_version = ""
    if completed.stdout:
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError:
            payload = {}
        digest = str(payload.get("digest", ""))
        python_version = str(payload.get("python_version", ""))

    return HashSeedResult(
        case_name=case_name,
        seed=seed,
        returncode=completed.returncode,
        digest=digest,
        python_version=python_version,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def hash_seed_digest_classes(
    results: list[HashSeedResult],
) -> dict[str, list[str]]:
    classes: dict[str, set[str]] = {}
    for result in results:
        classes.setdefault(result.case_name, set()).add(result.digest)
    return {
        case_name: sorted(digests)
        for case_name, digests in sorted(classes.items())
        if "" not in digests
    }


def observation_dict(observation: LoadObservation) -> dict[str, str | None]:
    return asdict(observation)


def hash_seed_result_dict(result: HashSeedResult) -> dict[str, str | int]:
    return asdict(result)


def _bytes(size: int) -> bytes:
    return bytes(index % 256 for index in range(size))


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


def _corrupt_middle(data: bytes) -> bytes:
    if not data:
        return data
    payload = bytearray(data)
    payload[len(payload) // 2] ^= 0xFF
    return bytes(payload)


_HASH_SEED_CHILD_CODE = r"""
import hashlib
import json
import marshal
import sys

case_name = sys.argv[1]
cases = {
    "dict_string_keys": {"alpha": 1, "beta": 2, "gamma": 3},
    "set_strings": {"alpha", "beta", "gamma"},
    "frozenset_strings": frozenset({"alpha", "beta", "gamma"}),
    "set_ints": {1, 2, 3, 4, 5},
}
value = cases[case_name]
data = marshal.dumps(value)
print(
    json.dumps(
        {
            "case_name": case_name,
            "digest": hashlib.sha256(data).hexdigest(),
            "python_version": sys.version,
            "marshal_version": marshal.version,
        },
        sort_keys=True,
    )
)
"""
