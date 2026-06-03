#set document(
  title: "Testing the Stability and Correctness of Python's marshal Module",
  author: "HerveyB3B4",
)
#set page(paper: "a4", margin: (x: 1.45cm, y: 1.35cm), numbering: "1")
#set text(font: "Liberation Serif", size: 8.7pt, lang: "en")
#set par(justify: true, leading: 0.38em)
#set heading(numbering: "1.1")
#show heading.where(level: 1): set text(size: 11.2pt)
#show heading.where(level: 2): set text(size: 9.6pt)
#show raw: set text(size: 7.8pt)
#show link: set text(fill: blue)

#align(center)[
  #text(14pt, strong[Testing the Stability and Correctness of Python's marshal Module])

  #v(0.2em)
  HerveyB3B4

  Repository: #link("https://github.com/<your-username>/softwaretestingassignment")
]

= Objective and Model

The question is whether the same input always creates the same serialized output in Python's `marshal` module. I use byte identity as the oracle: repeated `marshal.dumps(x)` calls must produce identical byte streams and therefore identical SHA-256 digests. The Python documentation says `marshal` is intended for internal Python object serialization and `.pyc` files. It is designed to be architecture-independent for one Python version, but not stable across Python versions. Cross-version differences are therefore findings, not automatic failures.

"Complete black-box testing" in this report means complete coverage of the documented API/type model used for the assignment: `dump`, `dumps`, `load`, `loads`, supported documented types, unsupported objects, invalid bytes, `version`, `allow_code`, recursive containers, and file API behavior. It does not mean infinite input exhaustion. White-box testing targets CPython `v3.13.13` `Python/marshal.c` built with GCC/gcov. It reports reachable statement/branch coverage and a def-use obligation matrix.

= Test Suite and Techniques

#table(
  columns: (22%, 34%, 44%),
  inset: 3pt,
  stroke: 0.35pt,
  [*Technique*], [*Where used*], [*Reason*],
  [Equivalence partitioning], [Documented scalar, binary, container, code-object, recursive, and unsupported classes], [The marshal behavior is type-directed, so partition representatives give high signal.],
  [Boundary value analysis], [Integer size transitions, empty/large collections, `-0.0`, subnormal, `Inf`, `NaN`], [Known fault locations are near encoding and representation boundaries.],
  [Fuzzing], [Hypothesis recursive values with bounded size], [Finds nested combinations not covered by the hand-written catalog.],
  [Stability experiments], [`PYTHONHASHSEED`, Docker versions, OS matrix, digest artifacts], [Checks byte identity across processes, versions, and platforms.],
  [White-box testing], [Instrumented CPython `marshal.c`, CPython `test_marshal`, project smoke, def-use matrix], [Measures actual C statement/branch execution and maps source-level data flow obligations.],
)

The deterministic catalog covers singletons, booleans, integers, floats, complex numbers, strings, bytes, bytearray, memoryview, tuple/list/dict/set/frozenset, recursive containers, and code objects. Additional black-box tests cover `dump/dumps/load/loads`, trailing bytes, file API, invalid tags, truncation, non-bytes input, `version`, and `allow_code=False`. `slice` is tested only when Python is 3.14+ and marshal format version is at least 5.

= Traceability Matrix

#table(
  columns: (24%, 23%, 30%, 23%),
  inset: 2.8pt,
  stroke: 0.3pt,
  [*Requirement / risk*], [*Technique*], [*Representative coverage*], [*Tests / artifacts*],
  [Documented API surface], [Black-box EP], [`dump`, `dumps`, `load`, `loads`, file objects], [`test_api_surface.py`],
  [Supported documented types], [Black-box EP], [numeric, text, binary, containers, code, recursion], [`test_documented_types.py`, `cases.py`],
  [Encoding boundaries], [BVA], [`2**31-1`, `2**31`, large int, empty/large collections], [`test_correctness.py`],
  [Float special values], [BVA], [`-0.0`, subnormal, `Inf`, `NaN`, complex], [`test_documented_types.py`, fuzzing],
  [Invalid input handling], [Negative EP], [invalid tag, truncated bytes, non-bytes, nested unsupported], [`test_invalid_inputs.py`],
  [Format/version behavior], [Black-box + docs], [`version`, too-high version, `allow_code`], [`test_format_versions.py`],
  [Repeatability], [Stability], [same process and different hash seeds], [`test_stability.py`, digest CLI],
  [C statement/branch coverage], [White-box], [`Python/marshal.c` gcov], [`marshal_coverage.json`],
  [C def-use obligations], [White-box data flow], [10 marshal data-flow obligations], [`marshal_def_use.csv`],
  [Platform evidence], [Experiment matrix], [Linux/macOS/Windows, Docker amd64/arm64, hardware placeholders], [CI, Docker, `RUNNING.md`],
)

= Findings

Local CPython 3.13.13 Linux tests passed with `131 passed, 2 skipped`; the two skips are Python 3.14-only `slice` checks. Docker Linux `amd64` passed on Python 3.10, 3.11, 3.12, 3.13, and 3.14 with 78 tests in the earlier suite; after black-box expansion the same Docker commands should be rerun and recorded. Docker/QEMU `arm64` CPython 3.13 previously passed with `78 passed in 135.05s`; rerun after the expanded test suite is the next required result.

The CPython white-box run built CPython `v3.13.13` with GCC/gcov and ran CPython's own `test_marshal`: 66 tests ran, 7 memory-heavy tests skipped, result successful. The project smoke run on the instrumented interpreter collected 33 marshal records with zero errors. The gcov summary for `Python/marshal.c` reported 831/973 statements covered (85.41%) and 726/794 branches covered (91.44%). The def-use matrix records 10/10 selected marshal data-flow obligations as covered. This is strong source-level evidence, but not 100% statement/branch coverage.

No hash-seed difference was observed for sampled unordered string set/frozenset cases under `PYTHONHASHSEED=1` and `2`. A useful behavioral finding from test development is that `memoryview(b"abc")` is accepted by CPython 3.13 and loads back as `bytes`.

= Platform Result Log

#table(
  columns: (24%, 25%, 22%, 29%),
  inset: 2.6pt,
  stroke: 0.3pt,
  [*Platform*], [*Runtime*], [*Command / program*], [*Result*],
  [Local Linux x86_64], [CPython 3.13.13], [`uv run pytest -q`], [`131 passed, 2 skipped`],
  [Docker Linux amd64], [CPython 3.10-3.14], [`docker compose run py310..py314`], [Previously all passed; rerun after expansion: pending],
  [Docker Linux arm64/QEMU], [CPython 3.13], [`docker run --platform linux/arm64 ...`], [Previously passed; rerun after expansion: pending],
  [GitHub Actions], [Linux/macOS/Windows 3.13], [CI artifact digest collection], [Fill after public push: pending],
  [ARM Linux board], [CPython + uv], [`scripts/arm_ssh_runner.py`], [Board/Python/result: pending],
  [MicroPython MCU], [MicroPython subset], [`scripts/micropython_uart_runner.py`], [Board/version/result: pending],
  [Optional VM], [Alpine/FreeBSD/32-bit/etc.], [`uv run pytest`, digest CLI], [Platform/result: pending],
)

= Reproducibility

Main commands:

```text
uv sync --locked --dev
uv run ruff format --check .
uv run ruff check .
uv run pytest -q
uv run marshal-stability --output results/local.json
```

White-box commands:

```text
uv run python scripts/fetch_cpython.py --tag v3.13.13
bash scripts/build_cpython_coverage.sh
bash scripts/run_marshal_whitebox.sh
uv run python scripts/summarize_whitebox_coverage.py
```

`RUNNING.md` gives platform-specific commands for Docker, GitHub Actions, ARM Linux, MicroPython UART, and optional VMs.

= Limitations

The suite cannot prove universal determinism over all possible inputs, sizes, recursion depths, platforms, compiler options, or Python versions. The black-box suite is complete against the documented model, not against an infinite domain. The white-box result is for CPython `v3.13.13` on this Linux/GCC build; branches requiring unavailable memory, alternate operating systems, different compile-time macros, or impossible failure injection remain outside the measured run. MicroPython results are supplemental because MicroPython's marshal subset differs from CPython. Replace the repository placeholder with the public GitHub/GitLab URL before submission.
