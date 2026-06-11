#!/usr/bin/env python3
"""Portable marshal equivalence test for CPython and MicroPython.

This file is intentionally self-contained and avoids pytest and project imports
so the exact same program can run on Linux CPython and MicroPython boards.
It emits one JSON object per case.
"""

try:
    import hashlib
except ImportError:
    try:
        import uhashlib as hashlib
    except ImportError:
        hashlib = None
try:
    import json
except ImportError:
    import ujson as json
import marshal
import sys


def _sha256(data):
    if hashlib is None:
        return None
    try:
        digest = hashlib.sha256(data)
    except AttributeError:
        return None
    if hasattr(digest, "hexdigest"):
        return digest.hexdigest()
    if hasattr(digest, "digest"):
        return _hexlify(digest.digest())
    return None


def _hexlify(data):
    alphabet = "0123456789abcdef"
    chars = []
    for byte in data:
        chars.append(alphabet[byte >> 4])
        chars.append(alphabet[byte & 15])
    return "".join(chars)


def _runtime_info():
    implementation = getattr(sys, "implementation", None)
    name = getattr(implementation, "name", "unknown")
    version = getattr(implementation, "version", ())
    marshal_version = getattr(marshal, "version", None)
    return {
        "implementation": name,
        "version": ".".join(str(part) for part in version),
        "platform": getattr(sys, "platform", "unknown"),
        "marshal_version": marshal_version,
    }


def _float_inf():
    return float("inf")


def _case_none():
    return None


def _case_bool_true():
    return True


def _case_bool_false():
    return False


def _case_int_zero():
    return 0


def _case_int_negative_one():
    return -1


def _case_int_32bit_edge():
    return 2**31 - 1


def _case_float_inf():
    return _float_inf()


def _case_empty_str():
    return ""


def _case_ascii_str():
    return "marshal"


def _case_empty_bytes():
    return b""


def _case_small_bytes():
    return b"abc"


def _case_empty_tuple():
    return ()


def _case_nested_tuple():
    return (1, "a", (2, b"b"))


def _case_empty_list():
    return []


def _case_nested_list():
    return [1, "a", [2, b"b"]]


def _case_empty_dict():
    return {}


def _case_nested_dict():
    return {"a": 1, "b": (2, 3)}


CASES = (
    ("none", _case_none),
    ("bool_true", _case_bool_true),
    ("bool_false", _case_bool_false),
    ("int_zero", _case_int_zero),
    ("int_negative_one", _case_int_negative_one),
    ("int_32bit_edge", _case_int_32bit_edge),
    ("float_inf", _case_float_inf),
    ("empty_str", _case_empty_str),
    ("ascii_str", _case_ascii_str),
    ("empty_bytes", _case_empty_bytes),
    ("small_bytes", _case_small_bytes),
    ("empty_tuple", _case_empty_tuple),
    ("nested_tuple", _case_nested_tuple),
    ("empty_list", _case_empty_list),
    ("nested_list", _case_nested_list),
    ("empty_dict", _case_empty_dict),
    ("nested_dict", _case_nested_dict),
)


def _same_float(left, right):
    return left == right or (left != left and right != right)


def _equivalent(left, right):
    if isinstance(left, float) or isinstance(right, float):
        return (
            isinstance(left, float)
            and isinstance(right, float)
            and _same_float(
                left,
                right,
            )
        )
    if isinstance(left, bytes) or isinstance(right, bytes):
        return isinstance(left, bytes) and isinstance(right, bytes) and left == right
    if isinstance(left, str) or isinstance(right, str):
        return isinstance(left, str) and isinstance(right, str) and left == right
    if isinstance(left, tuple) or isinstance(right, tuple):
        return _same_sequence_type(left, right, tuple)
    if isinstance(left, list) or isinstance(right, list):
        return _same_sequence_type(left, right, list)
    if isinstance(left, dict) or isinstance(right, dict):
        return _same_dict(left, right)
    return left == right


def _same_sequence_type(left, right, sequence_type):
    if not isinstance(left, sequence_type) or not isinstance(right, sequence_type):
        return False
    if len(left) != len(right):
        return False
    index = 0
    while index < len(left):
        if not _equivalent(left[index], right[index]):
            return False
        index += 1
    return True


def _same_dict(left, right):
    if not isinstance(left, dict) or not isinstance(right, dict):
        return False
    if len(left) != len(right):
        return False
    for key in left:
        if key not in right:
            return False
        if not _equivalent(left[key], right[key]):
            return False
    return True


def _record_for_case(case_id, value_factory, runtime):
    record = {
        "case_id": case_id,
        "runtime": runtime,
        "status": "ok",
        "sha256": None,
        "length": None,
        "exception_type": None,
        "first_equals_second": None,
        "roundtrip_equal": None,
    }
    try:
        value = value_factory()
        first = marshal.dumps(value)
        second = marshal.dumps(value)
        loaded = marshal.loads(first)
        record["sha256"] = _sha256(first)
        record["length"] = len(first)
        record["first_equals_second"] = first == second
        record["roundtrip_equal"] = _equivalent(value, loaded)
        if not record["first_equals_second"]:
            record["status"] = "unstable"
        elif not record["roundtrip_equal"]:
            record["status"] = "roundtrip-mismatch"
            record["value_repr"] = repr(value)
            record["loaded_repr"] = repr(loaded)
    except Exception as exc:  # noqa: BLE001 - portable script records runtime failures.
        record["status"] = "error"
        record["exception_type"] = type(exc).__name__
    return record


def main():
    runtime = _runtime_info()
    for case_id, value_factory in CASES:
        print(json.dumps(_record_for_case(case_id, value_factory, runtime)))


if __name__ == "__main__":
    main()
