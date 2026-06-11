#set document(
  title: "Testing the Stability and Correctness of Python's marshal Module",
  author: "HerveyB3B4",
)
#set page(paper: "a4", margin: (x: 1.35cm, y: 1.25cm), numbering: "1")
#set text(font: "Liberation Serif", size: 8.2pt, lang: "en")
#set par(justify: true, leading: 0.34em)
#set heading(numbering: "1.1")
#show heading.where(level: 1): set text(size: 10.7pt)
#show heading.where(level: 2): set text(size: 9.2pt)
#show raw: set text(size: 7.2pt)
#show link: set text(fill: blue)

#align(center)[
  #text(13.5pt, strong[Testing the Stability and Correctness of Python's marshal Module])

  #v(0.15em)
  HerveyB3B4

  Repository: #text(red)[TODO: repository link]
]

= Objective and Oracle

The module under test is Python's `marshal` serializer. The main requirement is stability: the same supported input should create the same serialized byte stream under the same relevant conditions. I therefore use byte identity, represented by SHA-256 of `marshal.dumps(x)`, as the oracle. Logical equality after `marshal.loads` is necessary for correctness, but it is not enough for stability.

The expected result depends on the condition being tested. Within one Python major.minor version, repeated runs and cross-platform artifacts should be hash-identical for the same test case. Across Python versions, digest differences are recorded as marshal format evolution rather than automatic failures because the format is explicitly not guaranteed to be stable across versions. MicroPython is treated as a supplemental portable subset because its marshal support is smaller than CPython's.

= Requirements and Test Design

#table(
  columns: (22%, 25%, 28%, 25%),
  inset: 2.4pt,
  stroke: 0.3pt,
  [*Requirement / risk*], [*Technique*], [*Representative cases*], [*Oracle / artifact*],
  [Same input repeatability], [Stability testing], [all catalog values, repeated `dumps`], [identical bytes / SHA-256],
  [Type-directed behavior], [Equivalence partitioning], [singletons, numbers, text, binary, containers, code], [round-trip equivalence and digest record],
  [Encoding boundaries], [Boundary value analysis], [`0`, `-1`, `2**15`, `2**31`, `2**63`, empty/large collections], [stable digest and exact round trip],
  [Floating-point edge cases], [BVA + EP], [`-0.0`, subnormal, `Inf`, `NaN`, complex special values], [NaN-aware equivalence and stable bytes],
  [Reference tracking], [White-box informed + EP], [recursive list/dict, shared child list, nested shared graph], [identity preservation after load],
  [Invalid input handling], [Negative testing], [unsupported objects, invalid tag, truncation, non-bytes input], [documented stable exception behavior],
  [Unordered iteration], [Cross-process stability], [sets/frozensets/string-key dict under `PYTHONHASHSEED`], [valid digest classes and no hidden crash],
  [Version/platform behavior], [Experiment matrix], [Python 3.10-3.14, macOS/Windows/ARM Linux], [same-version compare; cross-version observation],
)

#table(
  columns: (16%, 26%, 24%, 34%),
  inset: 2.2pt,
  stroke: 0.3pt,
  [*Input class*], [*Representative values*], [*Files*], [*Reason*],
  [Singletons], [`None`, booleans, `Ellipsis`, `StopIteration`], [`cases.py`, `test_documented_types.py`], [primitive tag dispatch],
  [Integers], [`2**15`, `2**31`, `2**63`, large int], [`cases.py`, `test_source_informed_marshal.py`], [compact/long integer branch boundaries],
  [Float/complex], [`-0.0`, `5e-324`, `Inf`, `NaN`, special complex], [`test_documented_types.py`, fuzzing], [binary representation risks],
  [Text/binary], [ASCII, Unicode, bytes with `NUL`, bytearray, memoryview], [`cases.py`, white-box WB4], [length, UTF-8, and buffer paths],
  [Containers], [tuple, list, dict, set, frozenset, nested values], [`test_correctness.py`, fuzzing], [writer loops and nested composition],
  [References], [cycles and shared objects], [`test_correctness.py`, WB6], [`TYPE_REF` and reference table behavior],
  [Code object], [simple function `__code__`, `allow_code=False`], [`test_format_versions.py`, WB7], [code-object acceptance/rejection branch],
  [Invalid streams], [empty bytes, invalid tag, truncation, trailing bytes], [`test_invalid_inputs.py`, WB8], [reader dispatch and error paths],
)

= White-Box Mapping

The white-box part is source-informed. It targets selected `Python/marshal.c` obligations rather than claiming complete all-definitions/all-uses coverage. The obligation file maps each source risk to an assignment test and oracle.

#table(
  columns: (12%, 28%, 34%, 26%),
  inset: 2.2pt,
  stroke: 0.3pt,
  [*ID*], [*Source area*], [*Risk*], [*Assignment test*],
  [WB1], [primitive dispatch], [wrong singleton tags], [`test_wb1_primitive_singleton_type_dispatch`],
  [WB2], [integer encoding], [wrong boundary classification], [`test_wb2_integer_encoding_boundaries`],
  [WB3], [float/complex], [loss of special bit patterns], [`test_wb3_float_paths`; `test_wb3_complex_paths`],
  [WB4], [text/bytes/buffer], [length or payload handling changes], [`test_wb4_string_bytes_and_buffer_paths`],
  [WB5], [container loops], [length/nesting regressions], [`test_wb5_container_writer_paths`],
  [WB6], [reference table], [cycles or shared identity lost], [`test_wb6_reference_tracking_and_recursive_structures`],
  [WB7], [code objects], [allowed/disallowed code confused], [`test_wb7_code_object_roundtrip`],
  [WB8], [reader dispatch], [invalid bytes crash or misdispatch], [`test_wb8_reader_dispatch_invalid_and_edge_streams`],
  [WB9], [format version], [version behavior assumed universal], [`test_wb9_supported_marshal_format_versions`],
  [WB10], [unordered iteration], [hash-seed order hidden], [`test_wb10_cross_process_hash_seed_digest_observations`],
)

= macOS Results

On macOS 15.5 arm64, I tested CPython 3.10.19, 3.11.12, 3.12.12, 3.13.5, and 3.14.2. Each version generated 47 digest records and every record had status `ok`.

#table(
  columns: (17%, 25%, 18%, 18%, 22%),
  inset: 2.2pt,
  stroke: 0.3pt,
  [*Runtime*], [*Pytest result*], [*Digest records*], [*marshal version*], [*Conclusion*],
  [CPython 3.10.19], [`252 passed, 5 skipped`], [47 all `ok`], [4], [stable within tested cases],
  [CPython 3.11.12], [`252 passed, 5 skipped`], [47 all `ok`], [4], [stable within tested cases],
  [CPython 3.12.12], [`252 passed, 5 skipped`], [47 all `ok`], [4], [stable within tested cases],
  [CPython 3.13.5], [`255 passed, 2 skipped`], [47 all `ok`], [4], [stable within tested cases],
  [CPython 3.14.2], [`258 passed`], [47 all `ok`], [5], [stable within tested cases],
)

Cross-version digest differences were observed on macOS. These are findings about format evolution, not correctness failures.

#table(
  columns: (24%, 23%, 53%),
  inset: 2.2pt,
  stroke: 0.3pt,
  [*Comparison*], [*Different digest cases*], [*Interpretation*],
  [3.10 vs 3.11], [3], [cross-version marshal format evolution],
  [3.10 vs 3.12], [3], [cross-version marshal format evolution],
  [3.10 vs 3.13], [3], [cross-version marshal format evolution],
  [3.10 vs 3.14], [3], [cross-version marshal format evolution],
  [3.11 vs 3.12], [0], [cross-version digest match for the tested catalog],
  [3.11 vs 3.13], [1], [cross-version marshal format evolution],
  [3.11 vs 3.14], [1], [cross-version marshal format evolution],
  [3.12 vs 3.13], [1], [cross-version marshal format evolution],
  [3.12 vs 3.14], [1], [cross-version marshal format evolution],
  [3.13 vs 3.14], [1], [cross-version marshal format evolution],
)

= Platform Matrix and Contributions

The group uses the same repository, case catalog, command interface, digest schema, and comparison scripts. Same-version cross-platform digest mismatches will be treated as potential stability findings. Cross-version mismatches are recorded separately.

#table(
  columns: (20%, 27%, 25%, 28%),
  inset: 2.2pt,
  stroke: 0.3pt,
  [*Owner*], [*Platform / scope*], [*Artifacts*], [*Status*],
  [Me], [macOS arm64, CPython 3.10-3.14], [`digests-macos-py310..py314.json`; `macos-test-results.md`], [complete; no within-version instability found],
  [A], [Windows, target CPython 3.13], [`digests-windows-py313.json`], [awaiting teammate artifact],
  [B], [ARM Linux, target CPython 3.13], [`digests-arm-linux-py313.json`], [awaiting teammate artifact],
  [B], [MicroPython portable subset], [`micropython-portable-equivalence.jsonl`], [awaiting teammate artifact],
  [Group], [shared test design and report], [case catalog, matrices, final comparison], [in progress],
)

= Findings

No macOS within-version instability was observed. All tested macOS Python versions passed the suite, and all generated digest records had status `ok`. Cross-version digest differences were observed, especially between CPython 3.10 and later versions; this matches the documented expectation that marshal is not a cross-version stable format. Python 3.14 reports marshal version 5, while Python 3.10 through 3.13 report marshal version 4.

The current evidence is strongest for macOS because its five-version matrix is complete. Windows, ARM Linux, and MicroPython results will be merged when teammate artifacts arrive. The same-version comparison command is:

```text
uv run python scripts/compare_digests.py \
  results/digests-macos-py313.json \
  results/digests-windows-py313.json \
  --expect-same-python-minor --strict
```

= Reproducibility

Main commands:

```text
uv sync --locked --dev
uv run ruff format --check .
uv run ruff check .
uv run pytest -q
uv run marshal-stability --output results/digests-<platform>-py313.json
```

macOS version matrix:

```text
uv run --python 3.10 pytest -q
uv run --python 3.10 marshal-stability --output results/digests-macos-py310.json
...
uv run --python 3.14 pytest -q
uv run --python 3.14 marshal-stability --output results/digests-macos-py314.json
```

MicroPython portable subset:

```text
micropython hardware/portable_marshal_equivalence.py \
  > results/hardware/micropython-portable-equivalence.jsonl
```

= Limitations

This suite cannot prove universal determinism over infinite input values, all object graph sizes, all operating systems, all CPU architectures, all compiler options, or all memory-failure branches. Fuzzing is bounded, and selected boundary values are representative rather than exhaustive. The white-box work is source-informed and obligation-driven, not complete all-definitions/all-uses coverage of `marshal.c`. MicroPython results are supplemental because MicroPython's marshal subset differs from CPython. Final cross-platform conclusions require Windows and ARM Linux artifacts from teammates.
