# Software Testing Assignment

This repository contains a reproducible test suite and final Typst report for
testing the stability and correctness of Python's `marshal` module.

The project uses `uv` for environment and lock-file management.

```bash
uv sync --dev
uv run pytest
uv run ruff format --check .
uv run ruff check .
uv run marshal-stability --output results/local.json
```

Detailed platform and white-box instructions are in `RUNNING.md`.
