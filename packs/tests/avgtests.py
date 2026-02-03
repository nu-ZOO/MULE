from packs.ana.analysis_utils import cook_data, suppress_baseline, average_waveforms, remove_secondaries
from packs.core.waveform_utils import collect_index, subtract_baseline, find_nearest
import numpy as np
import tempfile
import h5py


def make_temp_h5(waveforms):
    tmp = tempfile.NamedTemporaryFile(suffix=".h5", delete=False)
    tmp.close()

    with h5py.File(tmp.name, "w") as f:
        f.create_dataset("rwf", data=waveforms)

    return tmp.name


def test_subtract_baseline_mean(): # Tests that the mean is calculated correctly
    data = np.array([1, 2, 3, 4, 5], dtype=float)

    result = subtract_baseline(data, sub_type="mean")

    assert result == 3.0


def test_subtract_baseline_median(): # Tests that median is calculated correctly
    data = np.array([1, 100, 2], dtype=float)

    result = subtract_baseline(data, sub_type="median")

    assert result == 2.0


def test_subtract_baseline_invalid_mode(): # Tests that non mean or median modes get rejected
    data = np.array([1, 2, 3], dtype=float)

    result = subtract_baseline(data, sub_type="not_a_mode")

    assert result == 0



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


def test_cook_data(): # Tests that the cook works

    # Create flat waveforms (baseline subtraction = 0)
    data = np.zeros((3, 20), dtype=float)

    window_args = {
        "WINDOW_START": 0,
        "WINDOW_END": 20,
        "BASELINE_POINT_1": 5,
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
        "WINDOW_END": 10,
        "BASELINE_POINT_1": 2,
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

    # Ones → flipped to -1 → baseline-subtracted back to 0
    for wf in result:
        np.testing.assert_array_equal(wf, np.zeros(10))

def test_average_waveforms_single_file_identical(): # Tests for simple identical waveforms
    n_waveforms = 10
    n_samples = 50

    waveforms = np.tile(np.linspace(0, 100, n_samples), (n_waveforms, 1))
    filepath = make_temp_h5(waveforms)

    try:
        avg = average_waveforms(
            files=[filepath],
            bin_size=1,
            window_args={"signal": [10, 30], "baseline": [0, 5]},
            chunk_size=5,
            negative=False,
            baseline_mode="median",
            verbose=0,
        )

        assert avg.shape == (n_samples,)
        np.testing.assert_allclose(avg, waveforms[0], rtol=1e-6)

    finally:
        os.remove(filepath)

def test_average_waveforms_multiple_files(): #Tests for multiple files averged together
    n_samples = 40

    wf1 = np.tile(np.linspace(0, 10, n_samples), (5, 1))
    wf2 = np.tile(np.linspace(10, 20, n_samples), (5, 1))

    f1 = make_temp_h5(wf1)
    f2 = make_temp_h5(wf2)

    try:
        avg = average_waveforms(
            files=[f1, f2],
            bin_size=1,
            window_args={"signal": [5, 25], "baseline": [0, 3]},
            chunk_size=3,
            negative=False,
            verbose=0,
        )

        expected = (wf1[0] + wf2[0]) / 2
        np.testing.assert_allclose(avg, expected, rtol=1e-6)

    finally:
        os.remove(f1)
        os.remove(f2)

def test_chunk_size_larger_than_data(): #Tests when the chunk size is larger than the number of waveforms
    n_waveforms = 3
    n_samples = 30

    waveforms = np.random.random((n_waveforms, n_samples))
    filepath = make_temp_h5(waveforms)

    try:
        avg = average_waveforms(
            files=[filepath],
            bin_size=1,
            window_args={"signal": [5, 20], "baseline": [0, 3]},
            chunk_size=100,  # bigger than dataset
            negative=False,
            verbose=0,
        )

        expected = np.mean(waveforms, axis=0)
        np.testing.assert_allclose(avg, expected, rtol=1e-6)

    finally:
        os.remove(filepath)

def test_empty_chunk_handling(): #Tests for when a whole chunk gets rejected by cook data
    n_waveforms = 5
    n_samples = 25

    # Construct waveforms that are likely to be rejected
    # (huge secondary peaks)
    waveforms = np.full((n_waveforms, n_samples), 1e6)
    filepath = make_temp_h5(waveforms)

    try:
        avg = average_waveforms(
            files=[filepath],
            bin_size=1,
            window_args={"signal": [10, 15], "baseline": [0, 3]},
            chunk_size=2,
            negative=False,
            peak_threshold=1,  # extremely low so they should be rejected
            verbose=0,
        )

        # If cook_data rejects everything, this should fail loudly
        assert not np.any(np.isnan(avg))
        assert avg.shape == (n_samples,)

    finally:
        os.remove(filepath)

def test_negative_polarity(): #Tests when wfs are negative
    n_waveforms = 6
    n_samples = 40

    waveforms = -np.tile(np.linspace(0, 50, n_samples), (n_waveforms, 1))
    filepath = make_temp_h5(waveforms)

    try:
        avg = average_waveforms(
            files=[filepath],
            bin_size=1,
            window_args={"signal": [10, 30], "baseline": [0, 5]},
            chunk_size=3,
            negative=True,
            verbose=0,
        )

        # After polarity correction, average should be positive
        assert np.all(avg >= 0)

    finally:
        os.remove(filepath)

