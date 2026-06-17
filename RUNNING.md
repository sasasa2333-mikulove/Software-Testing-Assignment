# Running Guide

This project separates correctness tests, digest collection, platform checks,
hardware checks, and CPython `marshal.c` white-box coverage.

## Local CPython

Run on a normal development machine with Python 3.10+ and `uv`.

```bash
uv sync --locked --dev
uv run ruff format --check .
uv run ruff check .
uv run pytest -q
uv run marshal-stability --output results/local.json
```

For the shared course matrix, use a stable artifact naming scheme:

```bash
uv run marshal-stability --output results/digests-macos-py313.json
uv run marshal-stability --output results/digests-windows-py313.json
uv run marshal-stability --output results/digests-arm-linux-py313.json
```

Compare same-version, cross-OS artifacts strictly:

```bash
uv run python scripts/compare_digests.py \
  results/digests-macos-py313.json \
  results/digests-windows-py313.json \
  --expect-same-python-minor \
  --strict
```

Summarize a larger platform/version matrix with:

```bash
uv run python scripts/summarize_digest_matrix.py results/digests-*.json \
  --output results/digest-matrix-summary.json
```

Digest differences within the same Python major.minor version should be
investigated as stability findings. Digest differences across Python versions
are recorded as marshal format evolution, not automatic failures.

## Docker Linux amd64

Run on a machine with Docker enabled. This covers CPython 3.10 through 3.14 on
Linux amd64.

```bash
docker compose build
docker compose run --rm py310
docker compose run --rm py311
docker compose run --rm py312
docker compose run --rm py313
docker compose run --rm py314
```

## Docker Linux arm64/QEMU

Run on a machine with Docker buildx and QEMU enabled.

```bash
docker buildx build \
  --platform linux/arm64 \
  --build-arg PYTHON_VERSION=3.13 \
  --load \
  -t marshal-stability:py313-arm64 .
docker run --rm --platform linux/arm64 marshal-stability:py313-arm64
```

## GitHub Actions

Push to the public repository. The workflow runs:

- Ruff format and lint checks.
- Pytest on Linux with Python 3.10 through 3.13.
- Digest collection on Linux, macOS, and Windows with Python 3.13.
- Docker tests for Linux amd64 and arm64.

Download the uploaded digest artifacts and compare them with:

```bash
uv run python scripts/compare_digests.py baseline.json candidate.json
```

## ARM Linux Hardware

Run when the target board has Linux, SSH, Python 3, and `uv`.

```bash
python scripts/arm_ssh_runner.py \
  --host <arm-linux-host> \
  --user <ssh-user> \
  --remote-dir <repo-on-board>
```

Record the board model, CPU architecture, Python version, and result path in
the report result table.

For an exactly matched ARM Linux vs MicroPython comparison, run the portable
single-file equivalence workload directly on the ARM board:

```bash
python3 hardware/portable_marshal_equivalence.py \
  > results/hardware/arm-linux-portable-equivalence.jsonl
```

## MicroPython MCU over UART

Run the same file directly on the target board or MicroPython runtime:

```bash
micropython hardware/portable_marshal_equivalence.py \
  > results/hardware/micropython-portable-equivalence.jsonl
```

On a microcontroller, copy `hardware/portable_marshal_equivalence.py` to the
board and execute it with the board's normal MicroPython file runner. This is
exactly equivalent to the portable ARM Linux workload: the same test program,
case list, checks, and JSONL schema. It is still a portable subset and is not
equivalent to the complete CPython pytest/white-box suite.

Compare the two portable JSONL artifacts with:

```bash
python scripts/compare_portable_equivalence.py \
  results/hardware/arm-linux-portable-equivalence.jsonl \
  results/hardware/micropython-portable-equivalence.jsonl
```

Use `--strict-digest` only when you expect byte-identical marshal output across
the two runtimes.

## Optional VMs

Use VMs for supplemental environments not covered by GitHub Actions or Docker,
for example Alpine/musl, FreeBSD, 32-bit Linux, or big-endian systems.

In each VM, run:

```bash
uv sync --locked --dev
uv run pytest -q
uv run marshal-stability --output results/<platform>.json
```

## CPython marshal.c Source-Informed White-box Coverage

The counted white-box workload is assignment-specific. CPython's official
`test_marshal` is an external baseline, not counted as assignment-specific
white-box results.

```bash
uv run pytest -q tests/test_source_informed_marshal.py
uv run python scripts/whitebox/run_assignment_whitebox_driver.py
```

When CPython source is already available, build an instrumented interpreter:

```bash
bash scripts/whitebox/build_cpython_gcov.sh --source-dir <cpython-source>
```

Only clone CPython when you explicitly request it:

```bash
bash scripts/whitebox/build_cpython_gcov.sh --clone --tag v3.13.13
```

Then run C-level coverage using the instrumented interpreter:

```bash
bash scripts/whitebox/run_assignment_gcov.sh <path-to-instrumented-python>
```

The summary is written to
`whitebox/results/assignment_gcov_summary.json`. Report gcov percentages only
when that file was generated by the assignment-specific driver. Generated
source, build files, and coverage output are ignored by Git.
