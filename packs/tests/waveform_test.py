import pytest
from pytest import raises, mark

import numpy as np

from hypothesis.extra.numpy import arrays
from hypothesis import given, strategies as st
from hypothesis import settings
from hypothesis import Verbosity

from packs.proc.waveform_utils import extract_peak, collect_sidebands, collect_integration_window, calibrate
from packs.core.io             import reader
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


@mark.parametrize("sidebands, wf, times, output",
                  [((  1,  4), [1,2,3,4,5], [1,2,3,4,5], [1,2,3]),
                   ((  2,  5), [1,2,3,4,5], [1,2,3,4,5], [2,3,4]),
                   ((  2,  4), [1,2,3,4,5], [1,2,3,4,5], [2,3]  ),
                   (( -1,  4), [1,2,3,4,5], [1,2,3,4,5], [1,2,3]), # negative finds closest timepoint as 1
                   ((-13, -2), [1,2,3,4,5], [1,2,3,4,5], []     ), # closest timepoint is 1 for both, no output
                   ((  0,  0), [1,2,3,4,5], [1,2,3,4,5], []     ), # no difference in index, no output
                   ((  5,  3), [1,2,3,4,5], [1,2,3,4,5], []     ), # wrong order, no output
                   ((( 1,  3), (6,8)), [1,2,3,4,5,6,7,8,9,10], [1,2,3,4,5,6,7,8,9,10], [1,2,6,7] ),
                   (((-4, -8), (0,0)), [1,2,3,4,5,6,7,8,9,10], [1,2,3,4,5,6,7,8,9,10], []        ),
                   ((( 1,  4), (2,6)), [1,2,3,4,5,6,7,8,9,10], [1,2,3,4,5,6,7,8,9,10], [1,2,3,4,5]), # overlap
                   ])
def test_sidebands_return_as_expected(sidebands, wf, times, output):
    '''
    Given a sidebands index, provides the sidebands.
    This sucks a bit, as the indexing doesn't take the last position
    as part of the sideband.

    eg:
        (1,4) of [1,2,3,4,5] gives [1,2,3]...
        (0,4) of [1,2,3,4,5] gives [1,2,3]...
        (2,5) of [1,2,3,4,5] gives [2,3,4]...
        (2,4) of [1,2,3,4,5] gives [2,3]

    This should be changed!
    '''

    cali_params = {'sidebands' : sidebands}
    func_output = collect_sidebands(wf, np.array(times), cali_params)
    assert np.array_equal(func_output, output)


@mark.parametrize("sideband",
                  [((np.nan, np.nan)),
                   (('str', 'str')),
                   (('one_value')),
                   ((True, False))
                   ])
def test_sidebands_raise_error_with_malformed_sidebands(sideband):
    '''
    raise TypeError when the input is incorrect.
    NOTE: This error could be a bit more helpful to the user.
    '''
    wf = [1,2,3,4,5]
    cali_params = {'sidebands' : sideband}
    with raises(TypeError):
        collect_sidebands(wf, np.array(wf))


@mark.parametrize("method, window_0, window_1, H_index, time, output",
                  [('manual', 2, 4, 0, [1,2,3,4,5], (1, 3)), # 1st and 3rd index --> 2 & 4
                   ('manual', 1, 5, 0, [1,2,3,4,5], (0, 4)), # 0th and 4th index --> 1 & 5
                   ('height', 1, 1, 2, [1,2,3,4,5], (1, 3)), # padding around central peak
                   # add more here!
                   ])
def test_collect_integration_window_generic(method, window_0, window_1, H_index, time, output):
    '''
    test each method generally
    '''
    cali_params = {'method' : method,
                   'window' : [window_0, window_1]}
    start, end = collect_integration_window(np.array(time), cali_params, H_index)
    assert (start, end) == output


@mark.parametrize('time',
                  [([5,4,3,2,1]), # monotonically decreasing
                   ([6,3,1]),     # decreasing non monotonically
                   ([1,3,6]),     # increasing non monotonically
                   ([0,0,0])      # edge case, time bugs out
                   ])
def test_inaccurate_time_axis_breaks_integration_window(time):
    '''

    '''
    cali_params = {'method' : 'manual',
                   'window' : [2, 4]}
    H_index = 0

    with raises(ValueError):
        _, _ = collect_integration_window(np.array(time), cali_params, H_index)


@mark.parametrize('window',
                  [([4,2]),
                   ([0,0])
                   ])
def test_incorrect_window_setting(window):
    '''
    if the window is set such that the indices are misordered ((5, 4) not (4,5))
    this should raise a value error
    '''
    time = [1,2,3,4,5]
    cali_params = {'method' : 'manual',
                   'window' : window} # misordered
    H_index = 0

    with raises(ValueError):
        _, _ = collect_integration_window(np.array(time), cali_params, H_index)


def test_calibrate_works_as_intended(tmp_path, data_dir):
    '''
    simple test that the calibrate function works as intended
    '''
    file      = data_dir + 'three_channels_WD2.h5'
    save_path = str(tmp_path / 'three_channels_calib_WD2.h5')
    overwrite = True
    visualise = False
    cali_params      = {
        'method'         : 'manual',
        'window'         : (5000, 6000),
        'baseline_sub'   : 'median',
        'sidebands'      : ((100, 300), (2900, 3100)),
        'negative'       : True}


    # run calibrate()
    calibrate(file, cali_params, save_path, overwrite, visualise)

    # crosscheck with prior sample
    cross_check = reader(data_dir + 'three_channels_calib_WD2.h5', 'CALI', 'wf_info')
    new_data    = reader(data_dir + 'three_channels_calib_WD2.h5', 'CALI', 'wf_info')

    # read old and new data, compare
    for i in range(0,20):
        assert next(cross_check).tolist() == next(new_data).tolist()

    # overwrite, check the other part
    cross_check = reader(data_dir + 'three_channels_calib_WD2.h5', 'CALI', 'subwf-1')
    new_data    = reader(data_dir + 'three_channels_calib_WD2.h5', 'CALI', 'subwf-1')

    # read old and new data, compare
    for i in range(0,20):
        assert next(cross_check) == next(new_data)


