"""MicroPython marshal subset smoke test.

Run with:
    mpremote connect /dev/ttyACM0 run hardware/micropython/marshal_subset_test.py
"""

try:
    import hashlib
except ImportError:
    hashlib = None
import json
import marshal
import sys


def _sha256(data):
    if hashlib is None:
        return None
    try:
        return hashlib.sha256(data).hexdigest()
    except AttributeError:
        return None


def _board_info():
    implementation = getattr(sys, "implementation", None)
    name = getattr(implementation, "name", "unknown")
    version = getattr(implementation, "version", ())
    return {
        "implementation": name,
        "version": ".".join(str(part) for part in version),
        "platform": getattr(sys, "platform", "unknown"),
    }


CASES = [
    ("none", None),
    ("bool_true", True),
    ("int_zero", 0),
    ("int_negative_one", -1),
    ("int_32bit_edge", 2**31 - 1),
    ("float_inf", float("inf")),
    ("empty_str", ""),
    ("unicode_ascii", "marshal"),
    ("empty_bytes", b""),
    ("small_bytes", b"abc"),
    ("empty_tuple", ()),
    ("nested_tuple", (1, "a", (2, b"b"))),
    ("empty_list", []),
    ("nested_list", [1, "a", [2, b"b"]]),
    ("empty_dict", {}),
    ("nested_dict", {"a": 1, "b": (2, 3)}),
]


def main():
    board = _board_info()
    for case_id, value in CASES:
        record = {
            "case_id": case_id,
            "board": board,
            "status": "ok",
            "sha256": None,
            "length": None,
            "exception_type": None,
        }
        try:
            first = marshal.dumps(value)
            second = marshal.dumps(value)
            loaded = marshal.loads(first)
            record["sha256"] = _sha256(first)
            record["length"] = len(first)
            if first != second:
                record["status"] = "unstable"
            elif repr(value) != repr(loaded):
                record["status"] = "roundtrip-mismatch"
                record["loaded_repr"] = repr(loaded)
                record["value_repr"] = repr(value)
        except Exception as exc:
            record["status"] = "error"
            record["exception_type"] = type(exc).__name__
        print(json.dumps(record))


main()
