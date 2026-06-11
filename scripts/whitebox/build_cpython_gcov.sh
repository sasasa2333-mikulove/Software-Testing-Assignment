#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SOURCE_DIR=""
BUILD_DIR="${ROOT}/whitebox/build/cpython-gcov"
TAG="v3.13.13"
CLONE=0
JOBS="$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 2)"

usage() {
  cat <<'USAGE'
Usage:
  bash scripts/whitebox/build_cpython_gcov.sh --source-dir <cpython-source> [--build-dir <dir>]
  bash scripts/whitebox/build_cpython_gcov.sh --clone --tag <tag> [--source-dir <dir>] [--build-dir <dir>]

Builds an instrumented CPython with GCC/gcov flags. It does not require root.
CPython is cloned only when --clone is supplied explicitly.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source-dir)
      SOURCE_DIR="$2"
      shift 2
      ;;
    --build-dir)
      BUILD_DIR="$2"
      shift 2
      ;;
    --tag)
      TAG="$2"
      shift 2
      ;;
    --clone)
      CLONE=1
      shift
      ;;
    --jobs)
      JOBS="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "${SOURCE_DIR}" ]]; then
  SOURCE_DIR="${ROOT}/whitebox/cpython/cpython-${TAG#v}"
fi

if [[ "${CLONE}" -eq 1 && ! -d "${SOURCE_DIR}" ]]; then
  mkdir -p "$(dirname "${SOURCE_DIR}")"
  git clone --depth 1 --branch "${TAG}" https://github.com/python/cpython.git "${SOURCE_DIR}"
fi

if [[ ! -f "${SOURCE_DIR}/configure" ]]; then
  echo "Missing CPython configure script at ${SOURCE_DIR}/configure." >&2
  echo "Pass --source-dir <cpython-source>, or use --clone --tag <tag> explicitly." >&2
  exit 2
fi

mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

if [[ ! -f Makefile ]]; then
  "${SOURCE_DIR}/configure" \
    --with-pydebug \
    CFLAGS="-O0 -g --coverage" \
    LDFLAGS="--coverage"
fi

make -j"${JOBS}"
echo "${BUILD_DIR}/python"
