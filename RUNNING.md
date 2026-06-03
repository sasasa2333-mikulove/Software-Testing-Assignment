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

## MicroPython MCU over UART

Run when the target board runs MicroPython and is reachable through a serial
port. Install `mpremote` on the host if needed.

```bash
python scripts/micropython_uart_runner.py --port <serial-port>
```

This is a subset test, not equivalent to CPython `marshal`.

## Optional VMs

Use VMs for supplemental environments not covered by GitHub Actions or Docker,
for example Alpine/musl, FreeBSD, 32-bit Linux, or big-endian systems.

In each VM, run:

```bash
uv sync --locked --dev
uv run pytest -q
uv run marshal-stability --output results/<platform>.json
```

## CPython marshal.c White-box Coverage

This builds a pinned CPython source tree with GCC/gcov coverage and summarizes
coverage for `Python/marshal.c`.

```bash
uv run python scripts/fetch_cpython.py --tag v3.13.13
bash scripts/build_cpython_coverage.sh
bash scripts/run_marshal_whitebox.sh
uv run python scripts/summarize_whitebox_coverage.py
```

Generated source, build files, and coverage output are ignored by Git. Commit
only scripts, the obligation matrix, and report text.
