# Source-Informed White-Box Testing

This directory contains assignment-specific white-box evidence for CPython's
`Python/marshal.c`. The selected obligations are source-informed targets, not a
claim of complete all-definitions/all-uses coverage.

The counted workload is created in this repository:

```bash
uv run pytest -q tests/test_source_informed_marshal.py
uv run python scripts/whitebox/run_assignment_whitebox_driver.py
```

When an instrumented CPython build is available, collect C-level coverage with:

```bash
bash scripts/whitebox/run_assignment_gcov.sh <path-to-instrumented-python>
```

The gcov workflow writes:

- `whitebox/results/assignment_whitebox_driver.json`
- `whitebox/results/assignment_hash_seed_observations.json`
- `whitebox/results/assignment_gcov_summary.json`

CPython's official `test_marshal` is an external baseline, not counted as
assignment-specific white-box results.
