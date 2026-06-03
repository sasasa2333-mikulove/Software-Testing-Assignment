#set document(
  title: "Testing the Stability and Correctness of Python's marshal Module",
  author: "HerveyB3B4",
)
#set page(
  paper: "a4",
  margin: (x: 1.55cm, y: 1.45cm),
  numbering: "1",
)
#set text(font: "Liberation Serif", size: 9.2pt, lang: "en")
#set par(justify: true, leading: 0.45em)
#set heading(numbering: "1.1")
#show heading.where(level: 1): set text(size: 12pt)
#show heading.where(level: 2): set text(size: 10.2pt)
#show raw: set text(size: 8.2pt)
#show link: set text(fill: blue)

#align(center)[
  #text(15pt, strong[Testing the Stability and Correctness of Python's marshal Module])

  #v(0.25em)
  HerveyB3B4

  #v(0.15em)
  Repository: #link("https://github.com/<your-username>/softwaretestingassignment")
]

= Objective

The assignment asks whether the same input always creates the same serialized output in Python's `marshal` module. I define sameness exactly as byte identity: for a value `x`, repeated calls to `marshal.dumps(x)` must produce identical byte streams, and the SHA-256 digest of those bytes must therefore match. Logical equivalence alone is not accepted as stability evidence.

The official documentation says that `marshal` serializes Python internal object types and is mainly used for `.pyc` files. It is designed to be machine independent for one Python version, but it is deliberately not a stable cross-version format. The suite therefore separates strict pass/fail requirements from observation-only experiments: same interpreter checks must pass; cross-version and cross-platform comparisons are collected and reported without assuming that all digests must match.

= Test Suite

The project is a `uv` Python package with a `src/` layout. The command `marshal-stability` collects JSON digest records for each curated case. The main automated checks are:

#table(
  columns: (24%, 38%, 38%),
  inset: 4pt,
  stroke: 0.4pt,
  [*Test group*], [*Purpose*], [*Oracle*],
  [`test_correctness.py`], [Supported and unsupported examples], [Supported values roundtrip and repeat bytes; unsupported values raise `ValueError`.],
  [`test_stability.py`], [Cross-process digest checks under different `PYTHONHASHSEED` values], [Ordered values keep identical digests; unordered string sets are explicitly sampled as risk cases.],
  [`test_fuzzing.py`], [Generation-based fuzzing of marshal-supported values], [For generated values, `loads(dumps(x))` is normalized-equal and repeated dumps match.],
  [`test_collector_cli.py`], [Experiment artifact generation], [CLI emits JSON records with case id, digest, platform, Python version, and strategy metadata.],
  [`hardware/` + `scripts/`], [Supplemental ARM Linux and MicroPython experiments], [ARM Linux runs the CPython suite over SSH; MicroPython runs a small UART subset and emits JSON lines.],
)

The deterministic catalog covers singletons, booleans, integers, floats, complex numbers, strings, bytes, bytearray, memoryview, tuples, lists, dictionaries, sets, frozensets, recursive structures, and code objects. The negative catalog covers function objects and arbitrary instances.

= Applied Test Design Techniques

== Equivalence Partitioning

Equivalence partitioning was the primary black-box technique because the input domain is too large for exhaustive testing. The partitions are based on the documented marshal-supported families: scalar values, binary/text values, mutable containers, immutable containers, unordered containers, recursive containers, code objects, and unsupported objects. One or more representative values were selected from each partition. For example, `none`, `unicode_str`, `nested_dict`, `recursive_list`, `code_object`, and `plain_object` each represent a different expected behavior class.

This technique was useful because most marshal behavior is type-directed. A representative list and a representative tuple exercise different serialization tags even when they contain similar payloads. Negative partitions are also important because a correct serializer must reject unsupported objects instead of silently producing bytes with unclear meaning.

== Boundary Value Analysis

Boundary value analysis was used where marshal encoding has natural size or representation boundaries. The integer cases include `0`, `-1`, `2**31 - 1`, `2**31`, and a large arbitrary-precision integer. These values target the transition between compact integer paths and long-integer paths. Collection boundaries include empty, singleton-like, nested, and opt-in large containers. Floating-point boundaries include `-0.0`, a subnormal value, infinity, NaN, and complex values built from special floats.

BVA was not used for every type. For example, there is no meaningful numeric boundary for `None` or `Ellipsis`; testing many copies of those values would not increase fault-detection power.

== Fuzzing

I used Hypothesis for generation-based fuzzing. The generator creates bounded recursive values from marshal-supported scalars, lists, tuples, dictionaries, sets, and frozensets. The bounds keep the test suitable for CI and avoid memory-heavy examples. The fuzzing oracle checks two properties: roundtrip preservation under a normalization function, and same-process byte repeatability.

Fuzzing is appropriate here because nested combinations can expose bugs that a hand-written catalog may miss. It is still bounded: recursive cycles and code objects are handled by explicit tests instead of Hypothesis because arbitrary generation of those values is difficult and likely to obscure failures.

== White-box Guidance

CPython's `Python/marshal.c` was used to choose source-guided cases: integer size transitions, reference tracking for recursive containers, buffer-like binary input, code objects, and marshal version behavior. I did not attempt full all-definitions/all-uses coverage for the C implementation because that would require building and instrumenting CPython itself. For this assignment, source-guided branch family coverage is a better cost/benefit tradeoff.

= Traceability Matrix

#table(
  columns: (22%, 27%, 31%, 20%),
  inset: 3.5pt,
  stroke: 0.35pt,
  [*Requirement / risk*], [*Technique*], [*Representative cases*], [*Tests*],
  [Supported primitives are stable], [EP], [`none`, `bool_true`, `unicode_str`, `empty_bytes`], [`test_correctness`, `test_fuzzing`],
  [Integer encoding boundaries], [BVA + white-box], [`int_32bit_edge`, `int_32bit_overflow`, `int_large`], [`test_correctness`],
  [Float special values], [BVA], [`float_negative_zero`, `float_subnormal`, `float_inf`, `float_nan`], [`test_correctness`, `test_fuzzing`],
  [Nested and empty containers], [EP + BVA], [`empty_list`, `nested_tuple`, `nested_dict`], [`test_correctness`, `test_fuzzing`],
  [Recursive/cyclic structures], [White-box], [`recursive_list`, `recursive_dict`], [`test_correctness`],
  [Unordered container stability], [EP + stability experiment], [`set_of_strings`, `frozenset_of_strings`], [`test_stability`],
  [Unsupported inputs fail safely], [Negative EP], [`function_object`, `plain_object`], [`test_correctness`],
  [Cross-process reproducibility], [Stability experiment], [all catalog cases under different hash seeds], [`test_stability`, CLI digests],
  [Cross-version/platform evidence], [Experiment matrix], [catalog digests on Python 3.10-3.14 and OS matrix], [GitHub Actions, Docker],
  [ARM hardware evidence], [Supplemental platform testing], [ARM Linux CPython, MicroPython subset], [`arm_ssh_runner.py`, `micropython_uart_runner.py`],
)

= Findings

On the local CPython 3.13.13 Linux run, all same-interpreter correctness and stability tests passed: 76 pytest tests passed. Repeated `marshal.dumps()` calls produced identical bytes for the curated supported values, including recursive lists and dictionaries.

No hash-seed difference was observed for the sampled unordered string set and frozenset cases under `PYTHONHASHSEED=1` and `PYTHONHASHSEED=2`. The suite still keeps these cases because unordered containers remain a plausible stability risk and should be sampled across interpreters and platforms.

One useful finding came from test development: `memoryview(b"abc")` is accepted by CPython 3.13's `marshal.dumps()` and loads back as `bytes`. It was initially treated as unsupported, but the oracle was corrected after the test exposed the actual behavior. This is now represented as a supported buffer-protocol case.

Cross-version digest differences are expected and are not treated as bugs. The documentation explicitly says the marshal format is not stable across Python versions. The CI and Docker matrix collect these differences as evidence rather than failing the build for them.

= Reproducibility and Automation

The project uses `uv sync --locked --dev` to recreate the environment from `uv.lock`. The main commands are:

```text
uv run ruff format --check .
uv run ruff check .
uv run pytest -q
uv run marshal-stability --output results/local.json
```

GitHub Actions runs formatting, linting, pytest, and digest collection on Linux, macOS, and Windows. Docker runs the suite against official Python images for versions 3.10 through 3.14, with `linux/amd64` and `linux/arm64` targets through buildx/QEMU where available. Physical ARM tests are intentionally supplemental: ARM Linux can run the full CPython suite over SSH, while MicroPython boards run a smaller UART script because MicroPython's supported marshal subset and memory budget differ from CPython.

= Limitations

The suite cannot prove universal determinism. It samples important equivalence classes, boundaries, generated values, operating systems, versions, and hardware targets, but exhaustive testing is infeasible. Hypothesis fuzzing is bounded, so it may miss very deep structures or memory-pressure failures.

The white-box part is source-guided rather than coverage-complete. Full statement, branch, all-definitions, or all-uses coverage of `marshal.c` would require an instrumented CPython build and is outside this submission.

The MicroPython hardware test is not equivalent to CPython testing. It is a supplemental ARM embedded check for a smaller subset, not evidence that CPython marshal behaves identically on a microcontroller runtime.

Finally, the repository link is a placeholder and must be replaced with the public GitHub or GitLab URL before submission.
