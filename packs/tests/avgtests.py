from packs.ana.analysis_utils import cook_data, suppress_baseline, average_waveforms, remove_secondaries, window_overlap_check
from packs.core.waveform_utils import collect_index, subtract_baseline, find_nearest
import numpy as np
import h5py
import pytest
import pandas as pd



def make_temp_h5(tmp_path, waveforms, name="test_waveforms.h5"):
    """
    Writes a test HDF5 file compatible with load_rwf_info()
    Each waveform is a dataset inside the 'rwf' group
    """
    n_waveforms, n_samples = waveforms.shape
    filepath = tmp_path / name

    with h5py.File(filepath, 'w') as f:
        rwf_grp = f.create_group('rwf')

        for i in range(n_waveforms):
            dt = np.dtype([
                ('event_number', np.int32),
                ('channels', np.int32),
                ('rwf', np.float64, (n_samples,))
            ])
            data = np.zeros(1, dtype=dt)
            data['event_number'] = i
            data['channels'] = 0
            data['rwf'] = waveforms[i]

            rwf_grp.create_dataset(str(i), data=data)

    return filepath



def test_subtract_baseline_mean(): # Tests that the mean is calculated correctly
    data = np.array([1, 2, 3, 4, 5], dtype=float)

    result = subtract_baseline(data, sub_type="mean")

    assert result == 3.0


def test_subtract_baseline_median(): # Tests that median is calculated correctly
    data = np.array([1, 100, 2], dtype=float)

    result = subtract_baseline(data, sub_type="median")

    assert result == 2.0


def test_subtract_baseline_raises_on_invalid_sub_type():
    y = np.array([1, 2, 3, 4])

    with pytest.raises(ValueError):
        subtract_baseline(y, sub_type="banana")



def test_find_nearest_exact_match(): # Tests that find nearest finds the nearest when the values match exaclty
    array = np.array([0, 5, 10, 15])

    result = find_nearest(array, 10)

    assert result == 10


def test_find_nearest_lower(): # Tests that find nearest finds the nearest when the value is lower
    array = np.array([0, 5, 10, 15])

    result = find_nearest(array, 7)

    assert result == 5


def test_find_nearest_higher(): # Tests that find nearest finds the nearest when the value is higher
    array = np.array([0, 5, 10, 15])

    result = find_nearest(array, 13)

    assert result == 15


def test_collect_index_exact(): # Tests that coolect index works when value is exact
    time = np.array([0, 1, 2, 3, 4])

    idx = collect_index(time, 3)

    assert idx == 3


def test_collect_index_nearest():# Tests that collect index works when it needs to find nearest
    time = np.array([0, 10, 20, 30])

    idx = collect_index(time, 12)

    assert idx == 1


def test_cook_data(): # Tests that the output shape of cook data matches the shape of the input waveform

    # Create flat waveforms (baseline subtraction = 0)
    data = np.zeros((3, 20), dtype=float)

    window_args = {
        "WINDOW_START": 0,
        "WINDOW_END": 5,
        "BASELINE_POINT_1": 10,
        "BASELINE_POINT_2": 15,
        "BASELINE_RANGE_1": 2,
        "BASELINE_RANGE_2": 2,
    }

    result = cook_data(
        data=data,
        bin_size=1,
        window_args=window_args,
        chunk_size=3,
        chunk_number=0,
        negative=False,
        baseline_mode="median",
        verbose=0,
        peak_threshold=1000,        # very high so no rejection
        suppression_threshold=0,    # nothing should be suppressed
    )

    # All waveforms should survive
    assert len(result) == 3

    # Output shape should match input waveforms
    for wf in result:
        assert wf.shape == (20,)
        np.testing.assert_array_equal(wf, np.zeros(20))

def test_cook_data_negative_flip(): # Tests that negatives are flipped
    data = np.ones((2, 10), dtype=float)

    window_args = {
        "WINDOW_START": 0,
        "WINDOW_END": 2,
        "BASELINE_POINT_1": 5,
        "BASELINE_POINT_2": 8,
        "BASELINE_RANGE_1": 1,
        "BASELINE_RANGE_2": 1,
    }

    result = cook_data(
        data=data,
        bin_size=1,
        window_args=window_args,
        chunk_size=2,
        chunk_number=0,
        negative=True,
        verbose=0,
        peak_threshold=1000,
        suppression_threshold=0,
    )

    # 1 flipped to -1, baseline subtracted back to 0
    for wf in result:
        np.testing.assert_array_equal(wf, np.zeros(10))

def test_average_waveforms_single_file_identical(tmp_path): # Tests for simple identical waveforms
    n_waveforms = 10
    n_samples = 50

    waveforms = np.tile(np.linspace(0, 100, n_samples), (n_waveforms, 1)) # makes a repeating array of linspaces (identical waveforms)
    filepath = make_temp_h5(tmp_path, waveforms)

    avg = average_waveforms(
            files=[filepath],
            bin_size=1,
            window_args={"WINDOW_START": 1, "WINDOW_END": 5, "BASELINE_POINT_1": 10, "BASELINE_POINT_2" :15, "BASELINE_RANGE_1":1, "BASELINE_RANGE_2":1},
            chunk_size=5,
            negative=False,
            baseline_mode= 'none',
            peak_threshold = 1000,
            suppression_threshold=0,
            verbose=0,
        )

    assert avg.shape == (n_samples,) # input shape should match output
    np.testing.assert_allclose(avg, waveforms[0], rtol=1e-6) # average should be equal to one input


def test_average_waveforms_multiple_files(tmp_path): # Tests for multiple different files averged together to make sure that the average comes out as expected
    n_samples = 40

    wf1 = np.tile(np.linspace(0, 10, n_samples), (5, 1))
    wf2 = np.tile(np.linspace(10, 20, n_samples), (5, 1))

    f1 = make_temp_h5(tmp_path, wf1)
    f2 = make_temp_h5(tmp_path, wf2, "test_waveforms2.h5")


    avg = average_waveforms(
            files=[f1, f2],
            bin_size=1,
            window_args={"WINDOW_START": 1, "WINDOW_END": 5, "BASELINE_POINT_1": 10, "BASELINE_POINT_2" :15, "BASELINE_RANGE_1":1, "BASELINE_RANGE_2":1},
            chunk_size=3,
            negative=False,
            peak_threshold = 1000,
            suppression_threshold=0,
            baseline_mode= 'none',
            verbose=0,
        )

    expected = (wf1[0] + wf2[0]) / 2
    np.testing.assert_allclose(avg, expected, rtol=1e-6)


def test_chunk_size_larger_than_data(tmp_path): #Tests when the chunk size is larger than the number of waveforms, this should have no effect
    n_waveforms = 3
    n_samples = 30

    waveforms = np.random.random((n_waveforms, n_samples))
    filepath = make_temp_h5(tmp_path, waveforms)


    avg = average_waveforms(
            files=[filepath],
            bin_size=1,
            window_args={"WINDOW_START": 1, "WINDOW_END": 5, "BASELINE_POINT_1": 10, "BASELINE_POINT_2" :15, "BASELINE_RANGE_1":1, "BASELINE_RANGE_2":1},
            chunk_size=100,  # bigger than dataset
            negative=False,
            peak_threshold = 1000,
            suppression_threshold=0,
            baseline_mode= 'none',
            verbose=0,
        )

    expected = np.mean(waveforms, axis=0)
    np.testing.assert_allclose(avg, expected, rtol=1e-6)

def test_empty_chunk_handling(tmp_path):
    n_waveforms = 5
    n_samples = 25

    waveforms = np.tile(np.linspace(0, 100, n_samples), (n_waveforms, 1))
    filepath = make_temp_h5(tmp_path, waveforms)

    with pytest.raises(ValueError, match="No valid waveforms after processing"):
        average_waveforms(
            files=[filepath],
            bin_size=1,
            window_args={
                "WINDOW_START": 1,
                "WINDOW_END": 5,
                "BASELINE_POINT_1": 10,
                "BASELINE_POINT_2": 15,
                "BASELINE_RANGE_1": 1,
                "BASELINE_RANGE_2": 1
            },
            chunk_size=2,
            negative=False,
            peak_threshold=1,  # very low, so all waveforms rejected
            verbose=0,
        )


def test_negative_polarity(tmp_path): #Tests when wfs are negative
    n_waveforms = 6
    n_samples = 40

    waveforms = -np.tile(np.linspace(0, 50, n_samples), (n_waveforms, 1))
    filepath = make_temp_h5(tmp_path, waveforms)


    avg = average_waveforms(
            files=[filepath],
            bin_size=1,
            window_args={"WINDOW_START": 1, "WINDOW_END": 5, "BASELINE_POINT_1": 10, "BASELINE_POINT_2" :15, "BASELINE_RANGE_1":1, "BASELINE_RANGE_2":1},
            chunk_size=3,
            negative=True,
            peak_threshold = 1000,
            verbose=0,
        )

        # After polarity correction, average should be positive
    assert np.all(avg >= 0)

def test_window_args_neg(): # Tests for a negative window arg input
    window_args={"WINDOW_START": -1, "WINDOW_END": 5, "BASELINE_POINT_1": 10, "BASELINE_POINT_2" :15, "BASELINE_RANGE_1":1, "BASELINE_RANGE_2":1}
    with pytest.raises(ValueError):
        window_overlap_check(window_args)


def test_window_args_bl_window_overlap(): # Tests that an overlap with baseline and window raises error
    window_args = {
        "WINDOW_START": 1,
        "WINDOW_END": 8,
        "BASELINE_POINT_1": 9,
        "BASELINE_POINT_2": 15,
        "BASELINE_RANGE_1": 3,
        "BASELINE_RANGE_2": 1,
    }

    with pytest.raises(ValueError):
        window_overlap_check(window_args)

def test_window_args_bl_overlap(): # Tests for overlapping window args check
    window_args={"WINDOW_START": 1, "WINDOW_END": 5, "BASELINE_POINT_1": 11, "BASELINE_POINT_2" :12, "BASELINE_RANGE_1":3, "BASELINE_RANGE_2":1} 
    with pytest.raises(ValueError):
        window_overlap_check(window_args)

def test_wf_window_mismatch(tmp_path): # checks that skipping mismatch works, wf1 should be ignored in cook
    wf1 = np.linspace(0,10,10).reshape(1, -1)
    wf2 = np.linspace(0,30,30).reshape(1, -1)
    f1 = make_temp_h5(tmp_path, wf1)
    f2 = make_temp_h5(tmp_path, wf2, "test_waveforms2.h5")

    window_args = {
        "WINDOW_START": 1,
        "WINDOW_END": 5,
        "BASELINE_POINT_1": 10,
        "BASELINE_POINT_2": 15,
        "BASELINE_RANGE_1": 2,
        "BASELINE_RANGE_2": 2,
    }

    x = average_waveforms(
        files= [f1,f2],
        bin_size=1,
        window_args=window_args,
        chunk_size=1,
        negative=False,
        baseline_mode="median",
        verbose=0,
        peak_threshold=1000,        # very high so no rejection
        suppression_threshold=0,    # nothing should be suppressed
    )
    y = average_waveforms(
        files = [f2],
        bin_size=1,
        window_args=window_args,
        chunk_size=1,
        negative=False,
        baseline_mode="median",
        verbose=0,
        peak_threshold=1000,        # very high so no rejection
        suppression_threshold=0,    # nothing should be suppressed
    )
    np.testing.assert_array_equal(x, y)
