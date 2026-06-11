# Python marshal 稳定性测试报告中文对照稿

这份中文稿是 `report/report.tex` 的阅读对照，不一定直接提交。正式提交建议用英文 PDF。

## 1. 测试目标和判定标准

本项目测试 Python 的 `marshal` 模块。`marshal` 主要用于 CPython 内部对象的序列化和反序列化，例如 `.pyc` 文件中的 pseudo-compiled bytecode。它不是一个面向长期兼容的数据交换格式，Python 官方也说明 marshal format 可能在不同 Python 版本之间变化。

老师的问题是：

```text
Does the same input always create the same serialized output?
```

我们把这个问题转化为更严格的测试 oracle：

```text
same output = same marshal byte stream = same SHA-256 digest
```

也就是说，`marshal.loads()` 之后逻辑相等还不够。真正的稳定性要求是 `marshal.dumps(x)` 生成的二进制字节流完全一样。

我们使用三个 oracle：

| Oracle | 中文解释 | 用途 |
| --- | --- | --- |
| byte identity | 字节流完全一致，SHA-256 digest 一致 | 稳定性主判定标准 |
| round-trip correctness | dumps 后再 loads 能得到等价对象 | 正确性判定标准 |
| stable failure | 不支持对象和非法输入稳定抛异常 | 负例测试判定标准 |

报告的核心口径是：

```text
整体上，普通数据类型在同版本重复运行时比较稳定；
但是我们确实测出了几个 byte-level digest 差异点。
```

这些差异不一定是 CPython bug，但它们是本作业关心的稳定性发现。

## 2. 需求提炼

根据老师的作业要求和课堂笔记，我们把需求拆成可测试项目：

| 编号 | 测试需求 | 为什么重要 | 证据 |
| --- | --- | --- | --- |
| R1 | 同一输入、同一完整 Python 版本、同一平台，重复运行应稳定 | 在控制 runtime 条件下回答 same input same output | run1/run2 digest 比较 |
| R2 | 同一输入、同一 Python minor version，跨系统/架构比较 | 测试系统和架构敏感性 | same-minor comparison，同时记录 patch version、架构、编译器这些 confounding factors |
| R3 | 跨 Python 版本记录 digest 差异 | marshal 不保证跨版本稳定 | cross-version matrix |
| R4 | 覆盖整数和集合边界值 | 编码边界容易出问题 | BVA cases |
| R5 | 覆盖浮点特殊值 | NaN、Inf、-0.0、subnormal 容易出问题 | NaN-aware tests |
| R6 | 覆盖递归和共享引用 | marshal 有 reference tracking | identity preservation |
| R7 | 覆盖非法输入和不支持对象 | 错误处理也是 correctness | exception behavior |
| R8 | 覆盖无序容器和 hash seed | set/frozenset 可能出现 byte order 差异 | hash seed runs |
| R9 | 覆盖 code object 和 format version | code object 和解释器内部强相关 | code/format tests |
| R10 | MicroPython 使用 portable subset | MicroPython 不等同 CPython | B 的 artifact 待补 |

## 3. 测试用例集设计

测试用例不是简单堆列表，而是按风险分组。

| 输入类别 | 代表值 | 覆盖风险 | 判定方式 |
| --- | --- | --- | --- |
| singletons | `None`, `True`, `False`, `Ellipsis`, `StopIteration` | 基础 type tag dispatch | digest + round trip |
| integers | `0`, `-1`, `2**15`, `2**31`, `2**63`, `2**100` | 小整数、长整数、正负边界 | exact equality |
| float / complex | `-0.0`, `5e-324`, `Inf`, `NaN`, special complex | IEEE 表示、NaN、负零、subnormal | NaN-aware equality |
| text / binary | ASCII, Unicode, 中文/欧洲字符, NUL bytes, bytearray, memoryview | 长度、编码、buffer path | digest + loaded value |
| containers | tuple, list, dict, set, frozenset, nested containers | 容器 writer loop 和嵌套组合 | round trip + digest |
| recursive/shared reference | recursive list/dict, shared child list | `TYPE_REF` 和引用表 | 身份关系保留 |
| code object | function `__code__`, `allow_code=False` | 解释器内部 bytecode 敏感性 | digest 或预期异常 |
| unsupported object | function object, `object()`, nested unsupported object | writer 负例 | expected exception |
| invalid streams | empty bytes, invalid tag, truncation, corrupted bytes, trailing bytes | reader dispatch 和边界检查 | expected exception |
| format version | `version=0..marshal.version`，Python 3.14 的 slice | format evolution | digest observation |

## 4. 测试技术矩阵

| 技术 | 我们怎么用 | 为什么用 |
| --- | --- | --- |
| Equivalence Partitioning | 把输入划分成 primitives、numbers、text/binary、containers、references、code、invalid inputs | 防止只测一种类型 |
| Boundary Value Analysis | 测整数边界、空集合/大集合、subnormal float、truncated bytes | 编码逻辑常在边界切换 |
| Negative Testing | 测 unsupported object 和 malformed byte stream | 正确失败也是 correctness |
| Stability Testing | 同一 case 多次 dumps，同版本 run1/run2 比较 | 直接测试稳定性 |
| Fuzzing | 用 property-based tests 生成嵌套 supported values | 增加人工 case 之外的输入多样性 |
| Source-informed White-box | 根据 `Python/marshal.c` 的结构映射 primitive dispatch、integer branches、float/complex、buffer、container、reference、code、invalid tag、format version | 用源码结构指导测试，但不声称完整 all-definitions/all-uses |
| Platform / Version Matrix | macOS 和 Windows 跑 CPython 3.10-3.14，B 负责 ARM Linux 和 MicroPython | 区分同版本稳定性和跨版本 format evolution |

有些技术我们是“使用但有限制”的：

- 边界值分析值得使用，因为整数大小、collection length、float representation、truncated stream 都有明确边界。
- fuzzing 使用 Hypothesis，但受生成策略和运行时间限制。
- fuzzing 有两个 property-based test functions：round-trip correctness 和 repeatability。
- 每个 fuzzing test 设置 `max_examples=200`，所以一次 focused fuzzing run 大约生成 400 个随机/生成样例。
- recursive strategy 使用 `max_leaves=20`，container 使用 `max_size=6`，避免生成过深或过大的 object graph。
- Hypothesis 可以 shrink failing examples，但报告不声称使用固定随机 seed。
- fuzzing 主要用于 behavioral/property checks；跨平台比较用的 digest artifact 刻意限制为 stable named cases。
- 白盒测试是 source-informed selected obligations，不声称完整 all-definitions/all-uses。
- 不做 exhaustive testing，因为 Python object graph 空间理论上无限。

Source-informed white-box mapping：

| Source-informed target | Related marshal behavior | Test file/function |
| --- | --- | --- |
| Integer encoding branches | small/long integer, sign, magnitude | `test_wb2_integer_encoding_boundaries` |
| Float and complex paths | `NaN`, `Inf`, `-0.0`, subnormal, complex parts | `test_wb3_float_paths`, `test_wb3_complex_paths` |
| Text, bytes, buffer paths | Unicode, NUL bytes, bytearray, memoryview | `test_wb4_string_bytes_and_buffer_paths` |
| Container writer loops | list, tuple, dict, set, frozenset, length boundaries | `test_wb5_container_writer_paths` |
| `TYPE_REF` table | cycles, shared child, nested shared graph | `test_wb6_reference_tracking_and_recursive_structures` |
| Code object path | `__code__`, `allow_code=False` | `test_wb7_code_object_roundtrip`, `test_wb7_allow_code_false_rejects_code_objects_when_supported` |
| Reader error handling | invalid tag, empty stream, truncation, trailing bytes | `test_wb8_reader_dispatch_invalid_and_edge_streams` |
| Format version behavior | accepted marshal versions and reference behavior | `test_wb9_supported_marshal_format_versions` |
| Unordered iteration | set/frozenset/string-key dict under hash seeds | `test_wb10_cross_process_hash_seed_digest_observations` |

## 5. Traceability Matrix

| 需求 | 测试 / artifact | Test file/function | 证据 | 发现状态 |
| --- | --- | --- | --- | --- |
| R1 | digest catalog, run1/run2 compare | `tests/test_stability.py`, `scripts/compare_digests.py` | macOS 47 common cases，Windows 47 common cases | 同一完整版本/平台内重复稳定 |
| R2 | macOS 3.13 vs Windows 3.13 compare | `scripts/compare_digests.py` | 47 common cases，1 different case；记录 patch/architecture/compiler | `code_object` portability finding |
| R3 | Python 3.10-3.14 digest matrix | `scripts/summarize_digest_matrix.py`, digest artifacts | cross-version difference counts | format evolution observed |
| R4 | integer / collection BVA tests | `test_wb2_integer_encoding_boundaries`, `test_wb5_container_writer_paths` | full pytest + focused logs | 未发现同版本不稳定 |
| R5 | floating-point focused group | `test_wb3_float_paths`, `test_fuzzed_supported_values_roundtrip` | macOS 和 Windows 都是 106 passed | 特殊浮点在测试范围内稳定 |
| R6 | recursive/cyclic focused group | `test_wb6_reference_tracking_and_recursive_structures` | macOS 和 Windows 都是 19 passed | 引用关系测试通过 |
| R7 | invalid/unsupported focused group | `tests/test_invalid_inputs.py`, `test_wb8_reader_dispatch_invalid_and_edge_streams` | macOS 和 Windows 都是 22 passed | 异常行为稳定 |
| R8 | determinism/hash + cross-process groups | `tests/test_stability.py`, `test_wb10_cross_process_hash_seed_digest_observations` | 56 passed 和 50 passed groups | 跨版本无序容器差异被发现 |
| R9 | code object / format version group | `test_wb7_code_object_roundtrip`, `test_wb9_supported_marshal_format_versions` | 13 passed, 1 skipped | `code_object` 敏感 |
| R10 | MicroPython portable subset | B 的 portable subset artifact | 等待 B 的 artifact | 待补 |

## 6. Artifact 格式和执行流程

为了让三个人的结果可以比较，我们统一使用 JSON digest artifact，而不是只看截图或口头总结。每条 digest record 都包含相同字段：

| 字段 | 含义 | 用途 |
| --- | --- | --- |
| `case_id` | 测试输入的稳定编号 | 对齐不同系统/版本中的同一个输入 |
| `status` | 序列化成功还是抛出预期异常 | 区分 byte 差异和行为差异 |
| `sha256` / `length` | 序列化字节流的 hash 和长度 | byte identity 的主判定依据 |
| `exception_type` | 负例中的异常类型 | 判断失败行为是否稳定 |
| environment metadata | OS、CPU、Python implementation、完整 Python version、`marshal.version` | 防止误把不同运行条件混在一起比较 |

统一执行流程是：

1. 先运行格式和静态检查。
2. 再运行 full pytest。
3. 然后按老师关心的风险点跑 focused groups。
4. 最后收集 digest artifact，并用统一脚本比较。

focused groups 的数量不能简单相加，因为同一个 test 可能同时属于多个类别。例如 code object 测试也可能属于 format version 测试，递归引用测试也属于 correctness 测试。focused groups 的意义是 traceability，也就是证明每个课堂技术和风险点都被单独执行过。

这里还要解释 digest catalog 的数量。47 条默认 digest records，或者 include-large 时的 49 条 records，是为了跨系统/跨版本比较而保存的 stable named cases。它不等于整个测试套件只测了 47/49 个输入。完整 pytest 还包括 focused tests、source-informed parameterized tests，以及 Hypothesis 生成的随机/属性测试样例。生成的 fuzzing value 会在运行时检查，但不会全部保存成 named digest artifact。

## 7. macOS 测试结果

macOS 环境：

```text
macOS 15.5
arm64
CPython 3.10.19 / 3.11.12 / 3.12.12 / 3.13.5 / 3.14.2
```

完整 pytest 结果：

| Python version | Result | Digest records |
| --- | --- | --- |
| 3.10.19 | 252 passed, 5 skipped | 47 all ok |
| 3.11.12 | 252 passed, 5 skipped | 47 all ok |
| 3.12.12 | 252 passed, 5 skipped | 47 all ok |
| 3.13.5 | 255 passed, 2 skipped | 47 all ok |
| 3.14.2 | 258 passed | 47 all ok |

focused groups：

| Focus area | macOS CPython 3.13 result |
| --- | --- |
| Floating-point special values | 106 passed, 151 deselected |
| Recursive / cyclic structures | 19 passed, 238 deselected |
| Empty / large collections | 50 passed, 207 deselected |
| Invalid / unsupported inputs | 22 passed, 235 deselected |
| Determinism / hash | 56 passed, 201 deselected |
| Cross-process / hash-seed | 50 passed, 207 deselected |
| Fuzzing | 2 passed, 255 deselected |
| Source-informed white-box | 84 passed |
| Code object / format version | 13 passed, 1 skipped, 243 deselected |

macOS 3.13 的 run1/run2 digest 比较：

```text
47 common cases
different_cases: []
different_status_cases: []
```

说明在 macOS 同版本重复采集中，没有发现 digest 不一致。

## 8. Windows 测试结果

Windows 环境：

```text
Windows 11
AMD64
CPython 3.10.20 / 3.11.15 / 3.12.13 / 3.13.13 / 3.14.5
```

完整 pytest 结果：

| Python version | Result | Digest records |
| --- | --- | --- |
| 3.10.20 | 252 passed, 5 skipped | 47 all ok |
| 3.11.15 | 252 passed, 5 skipped | 47 all ok |
| 3.12.13 | 252 passed, 5 skipped | 47 all ok |
| 3.13.13 | 255 passed, 2 skipped | 47 all ok |
| 3.14.5 | 258 passed | 47 all ok |

Windows 的 focused groups 数量和 macOS 对齐：

| Focus area | Windows CPython 3.13 result |
| --- | --- |
| Floating-point special values | 106 passed, 151 deselected |
| Recursive / cyclic structures | 19 passed, 238 deselected |
| Empty / large collections | 50 passed, 207 deselected |
| Invalid / unsupported inputs | 22 passed, 235 deselected |
| Determinism / hash | 56 passed, 201 deselected |
| Cross-process / hash-seed | 50 passed, 207 deselected |
| Fuzzing | 2 passed, 255 deselected |
| Source-informed white-box | 84 passed |
| Code object / format version | 13 passed, 1 skipped, 243 deselected |

Windows 3.13 的 run1/run2 digest 比较也没有发现差异。include-large digest 产生 49 条记录，全部 `ok`。

## 9. 我们发现的 byte-level 差异

这是报告最重要的部分。我们不是只证明“都稳定”，而是确实发现了特定条件下的 digest 差异。

### 9.1 跨 Python 版本差异

macOS 和 Windows 都出现了类似模式：

| 比较 | 不同 case 数 | 不同 case |
| --- | ---: | --- |
| 3.10 vs 3.11 / 3.12 / 3.13 / 3.14 | 3 | `code_object`, `set_of_strings`, `frozenset_of_strings` |
| 3.11 vs 3.12 | 0 | 无 |
| 3.11 / 3.12 / 3.13 / 3.14 中部分比较 | 1 | `code_object` |

解释：

- `code_object` 和 Python 解释器内部字节码表示强相关，所以跨版本 digest 不稳定是合理的风险发现。
- `set_of_strings` 和 `frozenset_of_strings` 是无序容器，跨版本可能出现 byte stream 差异；差异可能由顺序或内部表示变化导致，但测试只证明 byte-level sensitivity，不证明唯一 root cause。
- 这些结果说明逻辑等价不代表 marshal byte stream 完全一致。

关键 digest evidence 示例：

| Case | Environment A | SHA-256 A | Len A | Environment B | SHA-256 B | Len B |
| --- | --- | --- | ---: | --- | --- | ---: |
| `code_object` | macOS 3.13.5 arm64 | `84ea466c3d3db3cf53f89b65f45a7206ca8ed3a82ac64f641408ced7a85550bf` | 366 | Windows 3.13.13 AMD64 | `08c3336e09a9d4eaf3fe976f56d45da8b9d5f750028cfd1c9882c18cabdb94fc` | 182 |
| `set_of_strings` | macOS 3.10.19 arm64 | `cae3b3f92fb2f62c2c0a3a6ee9c616a73a4be9929573365dc307424ecb2e1b5b` | 25 | macOS 3.11.12 arm64 | `a54f651a407ef9585d9ca6ed48b77c5e20aef295f31ac7a168a551cf5ca73c95` | 25 |
| `frozenset_of_strings` | macOS 3.10.19 arm64 | `1a4478734d5d3fa4e88a84c1e4d21f1e70afec3a4139ded086677a351e3c276a` | 25 | macOS 3.11.12 arm64 | `2357b680e1af2b7681c667ac0194a4683dcadb5239026d7f7ba89273d18a88d4` | 25 |

### 9.2 macOS vs Windows 差异

我们比较了：

```text
macOS CPython 3.13.5 arm64
Windows CPython 3.13.13 AMD64
```

结果：

```text
common_cases: 47
different_cases: code_object
different_status_cases: []
missing/extra: []
```

这个发现很重要，但不能夸大为“纯 OS bug”，因为两个环境不仅操作系统不同，还存在：

- patch version 不同：3.13.5 vs 3.13.13
- CPU 架构不同：arm64 vs AMD64
- 编译器不同：Clang vs MSVC

所以最准确的说法是：

```text
code_object 在跨版本/跨平台/跨架构条件下不是 robust byte-identical artifact。
```

这正好支持老师说的“同样输入在不同条件下可能不稳定，要找出具体情况”。

## 10. 结果解释

这组结果不是简单的 pass/fail。更准确的解释是：

- 普通支持类型在同版本重复运行中比较稳定。
- 整数、浮点、bytes、嵌套容器、递归结构在我们测试范围内没有发现同版本 digest 不一致。
- 跨 Python 版本时，`marshal` 本来就不保证格式稳定，因此 digest 差异不能直接算 bug。
- 但是这些差异仍然是本作业关心的发现，因为作业要求的是 hash-identical byte stream。
- 因此报告区分两类东西：stability-relevant differences 和 correctness failures。
- `code_object` 是最敏感的 case，因为它和 Python bytecode、line table、flags 等内部结构相关。
- `set_of_strings` 和 `frozenset_of_strings` 说明无序容器需要单独测试，不能只看逻辑等价。

因此一句话总结是：

```text
The tested catalog was mostly stable, but the suite exposed byte-level differences in specific high-risk cases.
```

中文就是：

```text
整体上大多数用例稳定，但我们确实发现了若干特定条件下的字节级差异。
```

## 11. 个人贡献

| 成员 | 贡献 | 状态 |
| --- | --- | --- |
| 我 | macOS 3.10-3.14 多版本测试、focused groups、digest artifacts、macOS 结果总结 | complete |
| A | Windows 3.10-3.14 多版本测试、focused groups、digest artifacts、Windows 结果总结 | complete |
| B | ARM Linux 和 MicroPython portable subset | awaiting |
| 全组 | 统一测试用例集、traceability matrix、最终报告整合 | in progress |

## 12. 局限性

这套测试已经比较细，但仍然有局限：

- 测试用例集是有限的，不可能穷尽所有 Python 对象图。
- fuzzing 是有界的，受生成策略和运行时间限制。
- extremely large collections 只用 bounded representative cases 表示，没有做到内存极限或文件大小极限的 stress testing。
- 白盒测试是 source-informed，不是完整 all-definitions/all-uses coverage。
- macOS 和 Windows 的 3.13 对比不是完全相同 patch version。
- macOS 和 Windows 的 CPU 架构和编译器也不同，因此 `code_object` 差异不能直接说成纯 OS bug。
- MicroPython 与 CPython 不完全等价，只能作为 portable subset 单独讨论。
- 无法证明所有编译选项、内存状态、平台细节下都稳定。

## 13. 最终结论

最终结论可以这样写：

```text
For the tested catalog, the answer is yes for repeated execution under the same CPython version and platform. However, the answer is no across selected version/platform conditions, especially for code objects and unordered string containers. These results support the assignment motivation: marshal stability must be tested at the byte-stream level rather than only by logical round-trip equality.
```

中文意思是：

```text
对于测试 catalog 来说，在同一个完整 CPython 版本和同一个平台内重复运行，答案基本是 yes；
但是在特定跨版本/跨平台条件下，答案是 no，尤其是 code_object 和无序字符串容器。
macOS vs Windows 3.13 的结论不是 OS-only 结论，因为它是 same-minor，但不是 same-patch，也不是 same-architecture。
这说明 marshal 的稳定性必须从字节流层面测试，不能只看反序列化后是否逻辑相等。
```
