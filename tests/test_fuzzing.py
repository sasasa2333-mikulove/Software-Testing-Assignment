from __future__ import annotations

import marshal

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from marshal_stability.normalization import marshal_equal

scalar_values = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-(2**128), max_value=2**128),
    st.floats(width=64, allow_nan=True, allow_infinity=True),
    st.builds(
        complex,
        st.floats(width=64, allow_nan=True, allow_infinity=True),
        st.floats(width=64, allow_nan=True, allow_infinity=True),
    ),
    st.text(max_size=64),
    st.binary(max_size=64),
    st.builds(bytearray, st.binary(max_size=64)),
)


marshal_values = st.recursive(
    scalar_values,
    lambda children: st.one_of(
        st.lists(children, max_size=6),
        st.tuples(children, children),
        st.dictionaries(st.text(max_size=32), children, max_size=6),
        st.sets(st.integers(min_value=-1000, max_value=1000), max_size=6),
        st.frozensets(st.integers(min_value=-1000, max_value=1000), max_size=6),
    ),
    max_leaves=20,
)


@settings(
    max_examples=200,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(marshal_values)
def test_fuzzed_supported_values_roundtrip(value) -> None:
    data = marshal.dumps(value)
    loaded = marshal.loads(data)

    assert marshal_equal(value, loaded)


@settings(max_examples=200, deadline=None)
@given(marshal_values)
def test_fuzzed_supported_values_are_repeatable(value) -> None:
    first = marshal.dumps(value)
    second = marshal.dumps(value)

    assert first == second
