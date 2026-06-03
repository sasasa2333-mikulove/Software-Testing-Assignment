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

PYTHONPATH="${PWD}/src" "${PYTHON}" - <<'PY' | tee "${RESULTS}/project_marshal_smoke_on_instrumented_cpython.log"
from marshal_stability.collector import collect_records

records = collect_records(include_large=True)
errors = [record for record in records if record.status != "ok"]
print(f"project marshal smoke records={len(records)} errors={len(errors)}")
if errors:
    raise SystemExit(1)
PY

(
  cd "${BUILD_DIR}"
  gcov -b Python/marshal.c > "../../results/gcov_marshal_stdout.txt"
)
