#!/usr/bin/env python3
"""Run the CPython marshal suite on an ARM Linux target over SSH."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True, help="SSH host or host alias.")
    parser.add_argument("--user", help="Optional SSH user.")
    parser.add_argument(
        "--remote-dir",
        default="~/softwaretestingassignment",
        help="Directory containing this repository on the ARM target.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/hardware/arm-linux.json"),
        help="Local JSON result path.",
    )
    parser.add_argument(
        "--python",
        default="python3",
        help="Python executable on the remote target.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    target = f"{args.user}@{args.host}" if args.user else args.host
    remote_command = (
        f"cd {args.remote_dir} && "
        "uv sync --dev && "
        "uv run pytest -q && "
        "uv run marshal-stability"
    )
    completed = subprocess.run(
        ["ssh", target, remote_command],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(_last_json_document(completed.stdout))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote ARM Linux result to {args.output}")
    return 0


def _last_json_document(text: str) -> str:
    start = text.rfind("\n{")
    if start == -1:
        start = text.find("{")
    if start == -1:
        raise ValueError("Remote command did not print a JSON document.")
    return text[start + 1 :].strip()


if __name__ == "__main__":
    raise SystemExit(main())
