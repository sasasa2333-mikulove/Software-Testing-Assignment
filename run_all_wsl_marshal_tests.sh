#!/usr/bin/env bash
# Run the full WSL test evidence chain for the Python marshal stability project.
# Designed for WSL. It does NOT modify project source code.
# It only creates result logs under results/wsl_all_<timestamp>/.
#
# Usage from the project root:
#   bash run_all_windows_marshal_tests.sh
#
# Optional:
#   bash run_all_windows_marshal_tests.sh --skip-install
#     Skip uv/Python installation attempts and use existing uv-managed interpreters.

set -Eeuo pipefail

SKIP_INSTALL="${1:-}"
STAMP="$(date +%Y%m%d_%H%M%S)"
RESULT_DIR="results/wsl_all_${STAMP}"
mkdir -p "$RESULT_DIR"

# uv installed by the official shell installer is usually here.
export PATH="$HOME/.local/bin:$PATH"

log() {
  local title="$1"
  printf '\n========== %s ==========' "$title" | tee -a "$RESULT_DIR/00_run_summary.txt"
  printf '\n' | tee -a "$RESULT_DIR/00_run_summary.txt"
}

run_and_save() {
  local name="$1"
  shift
  log "$name"
  echo "+ $*" | tee -a "$RESULT_DIR/00_run_summary.txt"
  "$@" 2>&1 | tee "$RESULT_DIR/${name}.txt"
}

install_uv_if_missing() {
  if command -v uv >/dev/null 2>&1; then
    return 0
  fi

  if [[ "$SKIP_INSTALL" == "--skip-install" ]]; then
    echo "ERROR: uv not found, and --skip-install was given." | tee -a "$RESULT_DIR/00_run_summary.txt"
    exit 1
  fi

  log "install_uv"
  echo "uv not found. Installing uv through the official Unix shell installer..." | tee -a "$RESULT_DIR/00_run_summary.txt"
  curl -LsSf https://astral.sh/uv/install.sh | sh

  export PATH="$HOME/.local/bin:$PATH"

  if ! command -v uv >/dev/null 2>&1; then
    echo "ERROR: uv is still not found. Open a new WSL shell or add \$HOME/.local/bin to PATH." | tee -a "$RESULT_DIR/00_run_summary.txt"
    exit 1
  fi
}

# -------------------------
# 0. Project/environment checks
# -------------------------
log "project_root"
pwd | tee -a "$RESULT_DIR/00_run_summary.txt"

if [[ ! -f "pyproject.toml" || ! -d "tests" || ! -d "src" ]]; then
  echo "ERROR: Please run this script from the project root containing pyproject.toml, src/, and tests/." | tee -a "$RESULT_DIR/00_run_summary.txt"
  exit 1
fi

install_uv_if_missing
run_and_save "01_uv_version" uv --version

# -------------------------
# 1. Install CPython versions for the WSL version matrix
# -------------------------
if [[ "$SKIP_INSTALL" != "--skip-install" ]]; then
  for ver in 3.10 3.11 3.12 3.13 3.14; do
    tag="py${ver/./}"
    run_and_save "02_install_${tag}" uv python install "$ver"
  done
fi

# Make the default project environment deterministic for local/current tests.
run_and_save "03_default_python_version" uv run --python 3.13 python --version
run_and_save "04_uv_sync" uv sync --locked --dev

# -------------------------
# 2. Metadata and style checks
# -------------------------
run_and_save "05_environment" uv run python -c "import sys, platform, marshal; print(sys.version); print(platform.platform()); print(platform.machine()); print('marshal.version =', marshal.version)"
run_and_save "06_ruff_format" uv run ruff format --check .
run_and_save "07_ruff_check" uv run ruff check .
run_and_save "08_collect_only" uv run pytest --collect-only -q

# -------------------------
# 3. Full pytest on WSL CPython 3.10-3.14
# -------------------------
for ver in 3.10 3.11 3.12 3.13 3.14; do
  tag="py${ver/./}"
  run_and_save "09_full_pytest_${tag}" uv run --python "$ver" pytest -q
  run_and_save "10_collect_digest_${tag}" uv run --python "$ver" marshal-stability --output "$RESULT_DIR/digests-wsl-${tag}.json"
done

# -------------------------
# 4. Focused black-box groups for assignment directions
# -------------------------
run_and_save "11_blackbox_float_complex_specials" \
  uv run pytest -q tests/test_documented_types.py tests/test_source_informed_marshal.py \
  -k "float or complex or nan or inf or zero"

run_and_save "12_blackbox_recursive_cyclic_shared" \
  uv run pytest -q tests/test_correctness.py tests/test_documented_types.py tests/test_source_informed_marshal.py \
  -k "recursive or cyclic or reference or shared"

run_and_save "13_blackbox_empty_large_boundary_nested" \
  uv run pytest -q tests/test_case_catalog.py tests/test_documented_types.py tests/test_source_informed_marshal.py \
  -k "empty or large or boundary or nested"

run_and_save "14_negative_invalid_unsupported" \
  uv run pytest -q tests/test_invalid_inputs.py tests/test_correctness.py tests/test_source_informed_marshal.py \
  -k "invalid or unsupported or reject or raises or error"

# -------------------------
# 5. Stability, fuzzing, and source-informed white-box groups
# -------------------------
run_and_save "15_stability_determinism_hash_process" \
  uv run pytest -q tests/test_stability.py tests/test_collector_cli.py tests/test_compare_digests.py

run_and_save "16_fuzzing_property_based" \
  uv run pytest -q tests/test_fuzzing.py

run_and_save "17_source_informed_whitebox" \
  uv run pytest -q tests/test_source_informed_marshal.py

run_and_save "18_code_object_format_version" \
  uv run pytest -q tests/test_format_versions.py tests/test_source_informed_marshal.py \
  -k "code or format or allow_code or version"

# -------------------------
# 6. Same-version repeated digest collection and strict comparison
# -------------------------
run_and_save "19_collect_digest_py313_run1" \
  uv run --python 3.13 marshal-stability --output "$RESULT_DIR/digests-wsl-py313-run1.json"

run_and_save "20_collect_digest_py313_run2" \
  uv run --python 3.13 marshal-stability --output "$RESULT_DIR/digests-wsl-py313-run2.json"

run_and_save "21_compare_py313_run1_run2_strict" \
  uv run python scripts/compare_digests.py \
  "$RESULT_DIR/digests-wsl-py313-run1.json" \
  "$RESULT_DIR/digests-wsl-py313-run2.json" \
  --expect-same-python-minor --strict

# -------------------------
# 7. Cross-version digest summary and observational comparisons
# Cross-version differences are recorded as findings, not automatic failures.
# -------------------------
run_and_save "22_summarize_wsl_digest_matrix" \
  uv run python scripts/summarize_digest_matrix.py \
  "$RESULT_DIR"/digests-wsl-py*.json \
  --output "$RESULT_DIR/digest-matrix-wsl-summary.json"

run_and_save "23_compare_py310_py314_observation" \
  uv run python scripts/compare_digests.py \
  "$RESULT_DIR/digests-wsl-py310.json" \
  "$RESULT_DIR/digests-wsl-py314.json"

run_and_save "24_compare_py313_py314_observation" \
  uv run python scripts/compare_digests.py \
  "$RESULT_DIR/digests-wsl-py313.json" \
  "$RESULT_DIR/digests-wsl-py314.json"

# -------------------------
# 8. Final summary
# -------------------------
log "done"
echo "All WSL tests finished." | tee -a "$RESULT_DIR/00_run_summary.txt"
echo "Result directory: $RESULT_DIR" | tee -a "$RESULT_DIR/00_run_summary.txt"
echo "Key files:" | tee -a "$RESULT_DIR/00_run_summary.txt"
echo "  00_run_summary.txt" | tee -a "$RESULT_DIR/00_run_summary.txt"
echo "  09_full_pytest_py310.txt ... 09_full_pytest_py314.txt" | tee -a "$RESULT_DIR/00_run_summary.txt"
echo "  11_blackbox_float_complex_specials.txt" | tee -a "$RESULT_DIR/00_run_summary.txt"
echo "  12_blackbox_recursive_cyclic_shared.txt" | tee -a "$RESULT_DIR/00_run_summary.txt"
echo "  13_blackbox_empty_large_boundary_nested.txt" | tee -a "$RESULT_DIR/00_run_summary.txt"
echo "  17_source_informed_whitebox.txt" | tee -a "$RESULT_DIR/00_run_summary.txt"
echo "  digest-matrix-wsl-summary.json" | tee -a "$RESULT_DIR/00_run_summary.txt"
