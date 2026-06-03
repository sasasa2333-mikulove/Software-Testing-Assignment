#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-whitebox}"
MANIFEST="${ROOT}/manifest.json"

if [[ ! -f "${MANIFEST}" ]]; then
  echo "Missing ${MANIFEST}; run scripts/fetch_cpython.py first." >&2
  exit 2
fi

SOURCE_DIR="$(python3 -c "import json; print(json.load(open('${MANIFEST}'))['source_dir'])")"
BUILD_DIR="$(python3 -c "import json; print(json.load(open('${MANIFEST}'))['build_dir'])")"

mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

if [[ ! -f Makefile ]]; then
  "../../../${SOURCE_DIR}/configure" \
    --with-pydebug \
    CFLAGS="-O0 -g --coverage" \
    LDFLAGS="--coverage"
fi

make -j"$(nproc)"
