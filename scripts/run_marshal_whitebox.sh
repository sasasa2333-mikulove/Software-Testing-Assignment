#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-whitebox}"
MANIFEST="${ROOT}/manifest.json"

if [[ ! -f "${MANIFEST}" ]]; then
  echo "Missing ${MANIFEST}; run scripts/fetch_cpython.py first." >&2
  exit 2
fi

BUILD_DIR="$(python3 -c "import json; print(json.load(open('${MANIFEST}'))['build_dir'])")"
PYTHON="${BUILD_DIR}/python"
RESULTS="${ROOT}/results"

if [[ ! -x "${PYTHON}" ]]; then
  echo "Missing ${PYTHON}; run scripts/build_cpython_coverage.sh first." >&2
  exit 2
fi

mkdir -p "${RESULTS}"

"${PYTHON}" -m test test_marshal -v | tee "${RESULTS}/cpython_test_marshal.log"
"${PYTHON}" -m pip install -e . >/dev/null
"${PYTHON}" -m pip install pytest hypothesis >/dev/null
"${PYTHON}" -m pytest tests -q | tee "${RESULTS}/project_pytest_on_instrumented_cpython.log"

(
  cd "${BUILD_DIR}"
  gcov -b Python/marshal.c > "../../results/gcov_marshal_stdout.txt"
)
