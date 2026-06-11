# macOS Test Results

## Environment

- Operating system: macOS 15.5
- Architecture: arm64
- Python implementation: CPython
- Tested Python versions: 3.10.19, 3.11.12, 3.12.12, 3.13.5, 3.14.2
- Marshal versions observed:
  - Python 3.10-3.13: marshal version 4
  - Python 3.14: marshal version 5

## Commands

The following commands were used for each Python version:

```bash
uv run --python <version> pytest -q
uv run --python <version> marshal-stability \
  --output results/digests-macos-py<version>.json
```

The cross-version digest matrix was generated with:

```bash
uv run --python 3.14 python scripts/summarize_digest_matrix.py \
  results/digests-macos-py310.json \
  results/digests-macos-py311.json \
  results/digests-macos-py312.json \
  results/digests-macos-py313.json \
  results/digests-macos-py314.json \
  --output results/digest-matrix-macos-py310-py314.json
```

## Pytest Results

| Python version | Result |
| --- | --- |
| 3.10.19 | 252 passed, 5 skipped |
| 3.11.12 | 252 passed, 5 skipped |
| 3.12.12 | 252 passed, 5 skipped |
| 3.13.5 | 255 passed, 2 skipped |
| 3.14.2 | 258 passed |

All tested Python versions passed the test suite. Skipped tests are caused by
runtime-version feature differences, especially Python 3.14-specific marshal
support for `slice` and newer `allow_code` behavior.

## Focused macOS CPython 3.13 Test Groups

To align the macOS evidence with the Windows teammate's report, the same
focused test groups were also executed on macOS using CPython 3.13.5.

| Focus area | Command filter / file | Result | Log artifact |
| --- | --- | --- | --- |
| Floating-point special values | `float or nan or inf or zero or complex` | 106 passed, 151 deselected | `results/06_macos_blackbox_floating_point.txt` |
| Recursive and cyclic structures | `recursive or cyclic or cycle or shared or reference` | 19 passed, 238 deselected | `results/07_macos_blackbox_recursive_cyclic.txt` |
| Empty and large collections | `empty or large or boundary or nested or collection` | 50 passed, 207 deselected | `results/08_macos_blackbox_empty_large_collections.txt` |
| Unsupported objects and invalid streams | `unsupported or invalid or error or exception` | 22 passed, 235 deselected | `results/09_macos_blackbox_invalid_unsupported.txt` |
| Hash-identical determinism | `stable or stability or deterministic or determinism or digest or hash` | 56 passed, 201 deselected | `results/10_macos_blackbox_determinism_hash.txt` |
| Cross-process / hash-seed stability | `process or subprocess or hash_seed` | 50 passed, 207 deselected | `results/11_macos_blackbox_cross_process.txt` |
| Fuzzing / property-based tests | `fuzz or hypothesis or property` | 2 passed, 255 deselected | `results/12_macos_blackbox_fuzzing.txt` |
| Source-informed white-box tests | `tests/test_source_informed_marshal.py` | 84 passed | `results/13_macos_whitebox_source_informed.txt` |
| Code object / format version path | `code_object or allow_code or pyc or format_version` | 13 passed, 1 skipped, 243 deselected | `results/14_macos_whitebox_code_format.txt` |

These focused groups overlap with the full suite and should not be added
together as independent test counts. They are reported to show traceability
between the teacher's requested risk categories and the executed tests.

## Digest Collection Results

Each Python version produced 47 digest records, and every record had status
`ok`.

| Python version | Artifact | Records | Status |
| --- | --- | ---: | --- |
| 3.10.19 | `results/digests-macos-py310.json` | 47 | all ok |
| 3.11.12 | `results/digests-macos-py311.json` | 47 | all ok |
| 3.12.12 | `results/digests-macos-py312.json` | 47 | all ok |
| 3.13.5 | `results/digests-macos-py313.json` | 47 | all ok |
| 3.14.2 | `results/digests-macos-py314.json` | 47 | all ok |

Additional macOS CPython 3.13 digest evidence was collected to match the
Windows evidence style:

| Artifact | Purpose | Result |
| --- | --- | --- |
| `results/digests-macos-py313-run1.json` | repeated same-version digest run 1 | 47 records, all ok |
| `results/digests-macos-py313-run2.json` | repeated same-version digest run 2 | 47 records, all ok |
| `results/15_macos_same_version_digest_compare.txt` | run1 vs run2 strict comparison | 47 common cases, no digest/status differences |
| `results/digests-macos-py313-large.json` | include-large digest catalog | 49 records, all ok |

## Cross-Version Digest Differences

The same test cases were compared across Python versions on macOS. Differences
were observed, but they are treated as marshal format evolution rather than
failures because Python does not guarantee marshal format stability across
Python versions.

| Comparison | Different digest cases | Interpretation |
| --- | ---: | --- |
| 3.10 vs 3.11 | 3 | cross-version format evolution |
| 3.10 vs 3.12 | 3 | cross-version format evolution |
| 3.10 vs 3.13 | 3 | cross-version format evolution |
| 3.10 vs 3.14 | 3 | cross-version format evolution |
| 3.11 vs 3.12 | 0 | cross-version digest match |
| 3.11 vs 3.13 | 1 | cross-version format evolution |
| 3.11 vs 3.14 | 1 | cross-version format evolution |
| 3.12 vs 3.13 | 1 | cross-version format evolution |
| 3.12 vs 3.14 | 1 | cross-version format evolution |
| 3.13 vs 3.14 | 1 | cross-version format evolution |

## Findings

- No within-version instability was observed on macOS.
- All digest records were successfully generated for every tested Python
  version.
- The repeated macOS CPython 3.13 digest comparison found no differences across
  47 common cases.
- The include-large macOS CPython 3.13 digest artifact produced 49 records, all
  with status `ok`.
- Cross-version digest differences were observed, especially between Python
  3.10 and later versions.
- Python 3.11 and Python 3.12 produced matching digest records for the tested
  catalog.
- Python 3.14 uses marshal version 5, while Python 3.10-3.13 use marshal
  version 4.

## Report-Ready Summary

On macOS 15.5 arm64, CPython 3.10.19, 3.11.12, 3.12.12, 3.13.5, and 3.14.2
were tested. All versions passed the test suite. Digest collection produced 47
successful records per version, all with status `ok`. Cross-version digest
differences were observed and recorded as marshal format evolution rather than
correctness failures.
