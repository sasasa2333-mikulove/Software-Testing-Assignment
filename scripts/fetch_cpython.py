#!/usr/bin/env python3
"""Fetch the pinned CPython source used for marshal.c white-box testing."""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
import urllib.request
from pathlib import Path

DEFAULT_TAG = "v3.13.13"
DEFAULT_ROOT = Path("whitebox")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", default=DEFAULT_TAG)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Download again even when the tarball already exists.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    version = args.tag.removeprefix("v")
    url = f"https://github.com/python/cpython/archive/refs/tags/{args.tag}.tar.gz"
    source_root = args.root / "cpython"
    source_root.mkdir(parents=True, exist_ok=True)
    tarball = source_root / f"{args.tag}.tar.gz"
    extract_dir = source_root / f"cpython-{version}"

    if args.force or not tarball.exists():
        print(f"Downloading {url}")
        urllib.request.urlretrieve(url, tarball)

    sha256 = _sha256(tarball)
    if not extract_dir.exists():
        with tarfile.open(tarball, "r:gz") as archive:
            archive.extractall(source_root, filter="data")
        extracted = source_root / f"cpython-{args.tag.removeprefix('v')}"
        if extracted != extract_dir and extracted.exists():
            extracted.rename(extract_dir)

    manifest = {
        "cpython_tag": args.tag,
        "tarball_url": url,
        "tarball_path": tarball.as_posix(),
        "tarball_sha256": sha256,
        "source_dir": extract_dir.as_posix(),
        "build_dir": (args.root / "build" / f"cpython-{version}-coverage").as_posix(),
        "coverage_target": "Python/marshal.c",
    }
    manifest_path = args.root / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
