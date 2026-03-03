import pytest
from pytest import raises, mark

import numpy as np

from hypothesis.extra.numpy import arrays
from hypothesis import given, strategies as st
from hypothesis import settings
from hypothesis import Verbosity

from packs.proc.waveform_utils import extract_peak, collect_sidebands
from packs.core.core_utils     import PeakRangeError

@settings(max_examples = 500)
@given(st.lists(st.floats(min_value=-1e5, max_value=1e5,
                          allow_nan=False, allow_infinity=False),
                min_size=1,
                max_size=100,
                unique=True))
def test_extract_peak_numpy(data):
    '''
    test whether extract peak returns the maximal value and the
    correct (first) index related to said value.
    '''
    arr = np.array(data)
    peak, idx = extract_peak(arr)
    # ensure position equals what you think it does...
    assert arr[idx] == peak
    # ...and that there are no more maximal points after this
    assert np.all(arr <= peak)


def test_empty_input_returns_none():
    '''
    if array is empty, raise a ValueError
    '''

    y_peak_no_vals = np.array([])

    with raises(ValueError):
        extract_peak(y_peak_no_vals)


@mark.parametrize("sidebands, wf, times, output", [((1, 4), [1,2,3,4,5], [1,2,3,4,5], [1,2,3])])
def test_sidebands_return_as_expected(sidebands, wf, times, output):
    '''
    Given a sidebands index, provides the sidebands.
    This sucks a bit, as the indexing doesn't take the last position
    as part of the sideband.

    eg:
        (1,4) of [1,2,3,4,5] gives [1,2,3]...
        (0,4) of [1,2,3,4,5] gives [1,2,3]...

    This should be changed!
    '''

    cali_params = {'sidebands' : sidebands}
    func_output = collect_sidebands(wf, np.array(times), cali_params)
    assert np.array_equal(func_output, output)
