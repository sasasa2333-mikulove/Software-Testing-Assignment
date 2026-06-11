#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RESULTS="${ROOT}/whitebox/results"

if [[ $# -lt 1 ]]; then
  echo "Usage: bash scripts/whitebox/run_assignment_gcov.sh <instrumented-python>" >&2
  exit 2
fi

PYTHON_EXE="$1"
if [[ ! -x "${PYTHON_EXE}" ]]; then
  echo "Instrumented Python is not executable: ${PYTHON_EXE}" >&2
  exit 2
fi

mkdir -p "${RESULTS}"
COMMAND="PYTHONPATH=${ROOT}/src ${PYTHON_EXE} scripts/whitebox/run_assignment_whitebox_driver.py"

PYTHONPATH="${ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}" \
  "${PYTHON_EXE}" \
  "${ROOT}/scripts/whitebox/run_assignment_whitebox_driver.py" \
  --results "${RESULTS}"

BUILD_DIR="$(cd "$(dirname "${PYTHON_EXE}")" && pwd)"
COVERAGE_SOURCE="unavailable"
COVERAGE_FILE=""
NOTES=("Assignment-specific driver completed before coverage summarization.")

if command -v gcovr >/dev/null 2>&1; then
  COVERAGE_SOURCE="gcovr"
  COVERAGE_FILE="${RESULTS}/gcovr_marshal.json"
  gcovr \
    --root "${BUILD_DIR}" \
    --filter '.*Python/marshal\.c' \
    --json-pretty \
    --output "${COVERAGE_FILE}" \
    "${BUILD_DIR}" || {
      NOTES+=("gcovr was available but failed to produce marshal.c coverage.")
      COVERAGE_SOURCE="unavailable"
      COVERAGE_FILE=""
    }
elif command -v gcov >/dev/null 2>&1; then
  COVERAGE_SOURCE="gcov"
  (
    cd "${BUILD_DIR}"
    gcov -b Python/marshal.c
  ) > "${RESULTS}/gcov_marshal_stdout.txt"
  COVERAGE_FILE="$(find "${BUILD_DIR}" -name 'marshal.c.gcov' -print -quit)"
  if [[ -z "${COVERAGE_FILE}" ]]; then
    NOTES+=("gcov ran but marshal.c.gcov was not found.")
    COVERAGE_SOURCE="unavailable"
  fi
else
  NOTES+=("Neither gcovr nor gcov was found; coverage percentages are unavailable.")
fi

SUMMARY_ARGS=(
  --coverage-source "${COVERAGE_SOURCE}"
  --output "${RESULTS}/assignment_gcov_summary.json"
  --command "${COMMAND}"
)

if [[ -n "${COVERAGE_FILE}" ]]; then
  SUMMARY_ARGS+=(--coverage-file "${COVERAGE_FILE}")
fi

for note in "${NOTES[@]}"; do
  SUMMARY_ARGS+=(--notes "${note}")
done

PYTHONPATH="${ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}" \
  "${PYTHON_EXE}" \
  "${ROOT}/scripts/whitebox/summarize_gcov.py" \
  "${SUMMARY_ARGS[@]}"
