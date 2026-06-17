# Marshal Stability Project Handoff

This folder is the clean handoff package for the Python `marshal` software testing final project. It contains the shared test suite, scripts, macOS results, Windows results, report drafts, and instructions for the next teammate.

## 1. Project Goal

The project tests the stability and correctness of Python's `marshal` module.

The key question is:

```text
Does the same input always create the same serialized output?
```

The main oracle is byte identity:

```text
same output = same marshal byte stream = same SHA-256 digest
```

Round-trip equality after `marshal.loads()` is also tested, but logical equality alone is not enough for the assignment.

## 2. Folder Map

| Path | Contents | Notes |
| --- | --- | --- |
| `src/marshal_stability/` | Project source code | Case catalog, digest collection, normalization, comparison helpers, CLI. |
| `tests/` | CPython pytest suite | Correctness, stability, fuzzing, invalid inputs, format versions, source-informed white-box tests. |
| `scripts/` | Utility scripts | Digest comparison, matrix summary, ARM SSH runner, MicroPython UART runner, CPython white-box scripts. |
| `hardware/` | Portable subset workload | Used by ARM Linux and MicroPython. |
| `whitebox/` | White-box notes and evidence | Includes source-informed obligations and assignment evidence JSON files. |
| `.github/workflows/ci.yml` | GitHub Actions workflow | Runs lint, pytest, digest collection, Docker matrix. |
| `report/report.tex` | Main English LaTeX report | Current formal report source. |
| `report/report.pdf` | Compiled report PDF | Current report is 6 pages. |
| `report/report_zh.md` | Chinese reading companion | For understanding and handoff, not necessarily for final submission. |
| `report/report.typ` | Older Typst draft | Keep only as reference; LaTeX is now the main report. |
| `results/` | macOS result artifacts | macOS CPython 3.10-3.14 pytest/digest results and focused logs. |
| `windows_results_final/` | Windows teammate artifacts | Windows CPython 3.10-3.14 pytest/digest results and focused logs. |
| `RUNNING.md` | General running guide | Existing detailed command reference. |
| `pyproject.toml`, `uv.lock` | Python project config | Use `uv sync --locked --dev`. |
| `Dockerfile`, `docker-compose.yml` | Docker test setup | Optional Linux/Docker matrix. |

## 3. Basic Local Run

Use Python 3.10+ and `uv`.

```bash
uv sync --locked --dev
uv run ruff format --check .
uv run ruff check .
uv run pytest -q
uv run marshal-stability --output results/digests-<platform>-py313.json
```

Example artifact names:

```bash
uv run marshal-stability --output results/digests-macos-py313.json
uv run marshal-stability --output results/digests-windows-py313.json
uv run marshal-stability --output results/digests-arm-linux-py313.json
```

## 4. Multi-Version CPython Runs

Run the same suite under multiple CPython versions when those versions are available locally.

```bash
uv run --python 3.10 pytest -q
uv run --python 3.11 pytest -q
uv run --python 3.12 pytest -q
uv run --python 3.13 pytest -q
uv run --python 3.14 pytest -q
```

Collect digest artifacts with the same Python versions:

```bash
uv run --python 3.10 marshal-stability --output results/digests-<platform>-py310.json
uv run --python 3.11 marshal-stability --output results/digests-<platform>-py311.json
uv run --python 3.12 marshal-stability --output results/digests-<platform>-py312.json
uv run --python 3.13 marshal-stability --output results/digests-<platform>-py313.json
uv run --python 3.14 marshal-stability --output results/digests-<platform>-py314.json
```

## 5. Focused Test Groups

These commands are useful for screenshots and report evidence. They correspond to the teacher's risk categories.

```bash
uv run pytest -q -k "float or complex"
uv run pytest -q -k "recursive or cyclic or reference"
uv run pytest -q -k "empty or large"
uv run pytest -q -k "invalid or unsupported"
uv run pytest -q -k "determinism or hash"
uv run pytest -q -k "cross_process or hash_seed"
uv run pytest -q tests/test_fuzzing.py -q
uv run pytest -q tests/test_source_informed_marshal.py
uv run pytest -q tests/test_format_versions.py
```

Note: focused group counts overlap. Do not add them together as a total number of unique tests.

## 6. Digest Comparison

Compare same-minor artifacts strictly:

```bash
uv run python scripts/compare_digests.py A.json B.json --expect-same-python-minor --strict
```

Example:

```bash
uv run python scripts/compare_digests.py \
  results/digests-macos-py313.json \
  windows_results_final/digests-windows-py313.json \
  --expect-same-python-minor \
  --strict
```

Summarize a multi-version matrix:

```bash
uv run python scripts/summarize_digest_matrix.py results/digests-*.json \
  --output results/digest-matrix-summary.json
```

Interpretation rule:

- Same full Python version + same platform repeated-run differences are potential determinism issues.
- Same minor but different patch/platform/architecture differences are stability-relevant findings, but not OS-only proof.
- Cross-version digest differences are reported as marshal format evolution, not automatic CPython bugs.

## 7. Report Build

The formal report is LaTeX.

```bash
xelatex -interaction=nonstopmode -halt-on-error -output-directory report report/report.tex
xelatex -interaction=nonstopmode -halt-on-error -output-directory report report/report.tex
```

Current status:

- `report/report.pdf` exists.
- Current PDF length: 6 pages.
- The report includes digest evidence for `code_object`, `set_of_strings`, and `frozenset_of_strings`.
- The Chinese companion is `report/report_zh.md`.

## 8. Current Completed Work

### macOS

Completed by current owner:

- CPython 3.10.19: `252 passed, 5 skipped`, 47 digest records all `ok`.
- CPython 3.11.12: `252 passed, 5 skipped`, 47 digest records all `ok`.
- CPython 3.12.12: `252 passed, 5 skipped`, 47 digest records all `ok`.
- CPython 3.13.5: `255 passed, 2 skipped`, 47 digest records all `ok`.
- CPython 3.14.2: `258 passed`, 47 digest records all `ok`.
- Focused groups and same-version run1/run2 digest comparison are stored in `results/`.

### Windows

Completed by teammate A:

- CPython 3.10.20: `252 passed, 5 skipped`, 47 digest records all `ok`.
- CPython 3.11.15: `252 passed, 5 skipped`, 47 digest records all `ok`.
- CPython 3.12.13: `252 passed, 5 skipped`, 47 digest records all `ok`.
- CPython 3.13.13: `255 passed, 2 skipped`, 47 digest records all `ok`.
- CPython 3.14.5: `258 passed`, 47 digest records all `ok`.
- Focused groups and same-version run1/run2 digest comparison are stored in `windows_results_final/`.

### Findings Already Written in Report

The report currently emphasizes these stability-relevant findings:

- `code_object` differs across selected version/platform conditions.
- `set_of_strings` differs across Python 3.10 vs later versions.
- `frozenset_of_strings` differs across Python 3.10 vs later versions.
- macOS 3.13.5 vs Windows 3.13.13 found one differing case: `code_object`.

Important wording:

- Do not call the macOS-vs-Windows finding an OS-only bug.
- It is same-minor, but not same-patch and not same-architecture.
- Treat it as a portability/stability-relevant finding.

## 9. ARM Linux and MicroPython Work Still Needed

B still needs to provide ARM Linux and MicroPython artifacts.

Portable ARM Linux run:

```bash
python3 hardware/portable_marshal_equivalence.py \
  > results/hardware/arm-linux-portable-equivalence.jsonl
```

MicroPython run:

```bash
micropython hardware/portable_marshal_equivalence.py \
  > results/hardware/micropython-portable-equivalence.jsonl
```

Compare portable artifacts:

```bash
python scripts/compare_portable_equivalence.py \
  results/hardware/arm-linux-portable-equivalence.jsonl \
  results/hardware/micropython-portable-equivalence.jsonl
```

Use `--strict-digest` only if byte-identical output is expected across both runtimes.

After B sends results, update:

- `report/report.tex`
- `report/report_zh.md`
- ARM/MicroPython rows in result tables
- contribution table
- conclusion and limitations if B finds differences
- recompile `report/report.pdf`

## 10. Final Submission Checklist

Before final submission:

- Replace repository placeholder in `report/report.tex`.
- Replace author/team placeholder with final member names.
- Add B's ARM Linux and MicroPython artifact paths and results.
- Recompile `report/report.pdf` twice with XeLaTeX.
- Confirm final report is no more than 8 pages.
- Confirm public GitHub/GitLab repository contains code and instructions.
- Confirm the repository does not include `.venv`, caches, `.DS_Store`, or local temporary files.

## 11. Cleanliness Notes

This handoff package intentionally keeps result evidence even though `results/` is ignored by `.gitignore` in the normal repository. The result folders are needed for the next teammate to continue report integration.

This handoff package should not contain:

- `.venv/`
- `.pytest_cache/`
- `.ruff_cache/`
- `.hypothesis/`
- `__pycache__/`
- `.DS_Store`
- `report/*.aux`
- `report/*.log`
- `report/*.out`

## 12. Recommended Next Steps for the Teammate

1. Read `report/report.pdf` first for the current final-report shape.
2. Read `report/report_zh.md` if Chinese explanation is easier.
3. Check `results/` and `windows_results_final/` to understand completed macOS/Windows evidence.
4. Ask B for ARM Linux and MicroPython artifacts.
5. Insert B's results into the report.
6. Replace repository and member placeholders.
7. Recompile the report and check page count.
8. Push the final clean project to GitHub/GitLab.
