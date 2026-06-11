#!/usr/bin/env python3
"""Run a MicroPython marshal subset test over a serial UART."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--port",
        required=True,
        help="Serial port, for example /dev/ttyACM0.",
    )
    parser.add_argument("--baud", default="115200", help="Serial baud rate.")
    parser.add_argument(
        "--script",
        type=Path,
        default=Path("hardware/portable_marshal_equivalence.py"),
        help="MicroPython script to run on the board.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/hardware/micropython-uart.jsonl"),
        help="Local JSONL result path.",
    )
    parser.add_argument(
        "--mpremote",
        default="mpremote",
        help="mpremote executable name or path.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    command = [
        args.mpremote,
        "connect",
        args.port,
        "resume",
        "run",
        args.script.as_posix(),
    ]
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    result_lines = [
        line for line in completed.stdout.splitlines() if _looks_like_json(line)
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(result_lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(result_lines)} MicroPython records to {args.output}")
    return 0


def _looks_like_json(line: str) -> bool:
    try:
        json.loads(line)
    except json.JSONDecodeError:
        return False
    return True


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FileNotFoundError as exc:
        print(f"Missing executable: {exc.filename}", file=sys.stderr)
        raise SystemExit(127) from exc
