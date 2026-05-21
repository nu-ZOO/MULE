from datetime import datetime
import os
import sys
import re

import numpy as np
import pandas as pd
import subprocess

import configparser

from pytest                        import mark
from pytest                        import raises
from pytest                        import warns
from pytest                        import fixture

from packs.proc.processing_utils   import process_event_lazy_WD1
from packs.proc.processing_utils   import process_bin_WD1
from packs.proc.processing_utils   import process_bin_WD2_lazy
from packs.proc.processing_utils   import read_defaults_WD2
from packs.proc.processing_utils   import process_header
from packs.proc.processing_utils   import read_binary
from packs.proc.processing_utils   import read_binary_lazy
from packs.proc.processing_utils   import format_wfs
from packs.proc.processing_utils   import check_save_path
from packs.proc.processing_utils   import save_data
from packs.proc.processing_utils   import number_of_events_WD2

from packs.types.types             import generate_wfdtype
from packs.types.types             import rwf_type
from packs.types.types             import event_info_type

from packs.core.core_utils         import MalformedHeaderError

from packs.core.io                 import load_rwf_info
from packs.core.io                 import load_evt_info
from packs.core.io                 import reader

from packs.types                   import types
from hypothesis                    import given
from hypothesis.strategies         import integers


from unittest.mock import patch, MagicMock

@given(integers(min_value = 1, max_value = 1000000))
def test_rwf_type_has_correct_shape(samples):
    x = rwf_type(samples)

    assert x['rwf'].shape[0] == samples


def test_header_components_read_as_expected(wd2_3ch_bin):

    evt_num   = 0
    tstamp    = 1998268
    smpls     = 1000
    smpl_prd  = 8

    with open(wd2_3ch_bin, 'rb') as f:
        event_number, timestamp, samples, sampling_period = read_defaults_WD2(f, sys.byteorder)

    assert event_number        == evt_num
    assert timestamp           == tstamp
    assert samples             == smpls
    assert sampling_period     == smpl_prd


def test_nonexistent_file_raises_error(tmp_path):

    fake_path = '/this/path/does/not/exist.bin'

    with raises(FileNotFoundError):
        process_bin_WD2_lazy(fake_path, f'{tmp_path}/lazy_output.h5')
        #process_header(fake_path)


def test_header_processed_correctly(wd2_3ch_bin):

    smpls     = 1000
    smpl_prd  = 8
    channels  = 3
    wdtype    = generate_wfdtype(channels, smpls) # 3 channels in this case

    with open(wd2_3ch_bin, 'rb') as f:
        result = process_header(f)

    assert result[0] == wdtype
    assert result[1] == smpls
    assert result[2] == smpl_prd
    assert result[3] == channels

def test_header_works_when_data_malformed(data_dir):
    # this test would normally cause a memory error as the data
    # provided is singular channel, and `process_header()` tests
    # for single channel behaviour by analysing it as multi-channel
    # and returning a single channel response if the header breaks.

    # Here,the header will crash out due to a channels value > 10^10.
    # This has been fixed quickly in process_header, but should be
    # optimised in a different fashion.

    file = data_dir + 'malformed_data.bin'

    with warns(UserWarning):
        with open(file, 'rb') as f:
            process_header(f)

@mark.parametrize("function, error", [(process_header, NameError),
                                      (read_defaults_WD2, ValueError)])
def test_endian_error_when_reading(function, error, wd2_3ch_bin):

    byte_order = 'Big' # this will raise a ValueError

    with raises(error):
        with open(wd2_3ch_bin, 'rb') as f:
            holder = function(f, byte_order)


def test_invalid_file_for_reading(data_dir):

    file = data_dir + 'false_data.npy'

    x = read_binary(file, types.generate_wfdtype(1, 1000))

    # if you've malformed the data types on a non-binary file, the result should be empty
    # but this may not always be the case.
    assert len(x) == 0


def test_formatting_works(data_dir, wd2_3ch_bin):

    # collect relevant data from output
    check_file      = data_dir + 'three_channels_WD2.h5'
    check_rwf       = load_rwf_info(check_file, 1000)
    check_evt_info  = load_evt_info(check_file)


    channels = 3
    samples = 1000

    wdtype = types.generate_wfdtype(channels, samples)

    with open(wd2_3ch_bin, 'rb') as file:
        # read in data
        data = read_binary(file, wdtype)

    evt_info, rwf = format_wfs(data, wdtype, samples, channels)

    # modify into dataframes for appropriate comparison
    rwf = pd.DataFrame(list(map(list, rwf)), columns = rwf_type(samples).names)
    evt_info = pd.DataFrame(list(map(list, evt_info)), columns = event_info_type.names)

    assert rwf.equals(check_rwf)
    assert evt_info.equals(check_evt_info)


def test_save_path_exists():

    data_path = 'some/fake/path/three_channels_WD2.h5'

    with raises(FileNotFoundError):
        check_save_path(data_path, overwrite = False)


def test_ensure_new_path_created(data_dir):
    data_path  = data_dir + 'three_channels_WD2.h5'
    found_path = check_save_path(data_path, overwrite=False)

    assert found_path != data_path
    assert found_path.endswith('.h5')
    assert re.search(r'_\d{8}_\d{6}', found_path), "Expected datetime stamp in filename"
    assert not os.path.exists(found_path), "Path should not already exist"


def test_runtime_error_when_too_many_save_files(tmp_path):
    timestamp = "20240101_120000"
    mock_dt = MagicMock()
    mock_dt.now.return_value.strftime.return_value = timestamp

    (tmp_path / f'test_{timestamp}.txt').touch()
    for i in range(1, 101):
        (tmp_path / f'test_{timestamp}_{i}.txt').touch()

    with patch('packs.proc.processing_utils.datetime', mock_dt):
        with raises(RuntimeError):
            check_save_path(str(tmp_path / 'test.txt'), overwrite=False)

@mark.parametrize("config, inpt, output, comparison", [("process_WD2_1channel.conf", "one_channel_WD2.bin", "one_channel_tmp.h5", "one_channel_WD2.h5"),
                                           ("process_WD2_3channel.conf", "three_channels_WD2.bin", "three_channels_tmp.h5", "three_channels_WD2.h5")])
def test_decode_produces_expected_output(config, inpt, output, comparison, MULE_dir, data_dir, tmp_path):

    # ensure path is correct
    file_path       =  data_dir + inpt
    save_path       =  str(tmp_path / output)
    comparison_path =  data_dir + comparison
    config_path     =  data_dir + "configs/" + config
    temp_config = str(tmp_path / config)

    # collect samples from header
    with open(file_path, 'rb') as f:
        _, samples, _, _ = process_header(f)

    # rewrite paths to files
    cnfg = configparser.ConfigParser()
    cnfg.read(config_path)
    cnfg.set('required', 'file_path', "'" +  file_path + "'") # need to add comments around for config reasons
    cnfg.set('required', 'save_path', "'" +  save_path + "'")

    with open(temp_config, 'w') as cfgfile:
        cnfg.write(cfgfile)

    # run processing pack decode
    run_pack = [sys.executable, MULE_dir + "/bin/mule", "proc", temp_config]
    subprocess.run(run_pack)
    # check that the resulting dataframe is as expected
    assert load_evt_info(save_path).equals(load_evt_info(comparison_path))
    assert load_rwf_info(save_path, samples).equals(load_rwf_info(comparison_path, samples))


@mark.parametrize("config, inpt, output, comparison", [("process_WD1_1channel.conf", "one_channel_WD1.dat", "one_channel_WD1_tmp.h5", "one_channel_WD1.h5"),
                                                       ("process_lecroy_csv.conf", "one_channel_LECROYWS4054HD.csv", "one_channel_LECROYWS4054HD_tmp.h5", "one_channel_LECROYWS4054HD.h5")])
def test_WD1_Lecroy_decode_produces_expected_output(config, inpt, output, comparison, MULE_dir, data_dir, tmp_path):
    '''
    This test will be merged with test_decode_produces_expected_output()
    once WD2 processing has been updated to match lazy method of WD1.

    Tests WD1 and Lecroy oscilloscope single channel processing.
    '''

    # ensure path is correct
    file_path       = data_dir + inpt
    save_path       = tmp_path / output # PosixPaths behave differently
    comparison_path = data_dir + comparison
    config_path     = data_dir + "configs/" + config
    temp_config = str(tmp_path / config)

    # rewrite paths to files
    cnfg = configparser.ConfigParser()
    cnfg.read(config_path)
    cnfg.set('required', 'file_path', "'" +  file_path + "'") # need to add comments around for config reasons
    cnfg.set('required', 'save_path', f"'{save_path}'") # PosixPaths behave differently

    with open(temp_config, 'w') as cfgfile:
        cnfg.write(cfgfile)

    # run processing pack decode
    run_pack = [sys.executable, MULE_dir + "/bin/mule", "proc", temp_config]
    subprocess.run(run_pack)

    # load event info from both files for comparison
    saved_event_info      = pd.read_hdf(save_path, 'RAW/event_info')
    comparison_event_info = pd.read_hdf(comparison_path, 'RAW/event_info')

    # compare integer columns exactly
    exact_cols = ['event_number', 'timestamp', 'samples', 'channels']
    assert saved_event_info[exact_cols].equals(comparison_event_info[exact_cols])

    # compare float columns with tolerance to account for floating point precision differences
    np.testing.assert_allclose(saved_event_info['sampling_period'].values,
                               comparison_event_info['sampling_period'].values,
                               rtol=1e-10)

    assert [x for x in reader(save_path, 'RAW', 'rwf')] == [x for x in reader(comparison_path, 'RAW', 'rwf')]


def test_lazy_loading_malformed_data_WD1(MULE_dir):
    '''
    Test that a file you pass through with no appropriate header is flagged if it's
    not functioning correctly.
    ATM the check for this is:
    - event number goes up +1 events
    - number of samples stays the same across two events
    - timestamp increases between events
    These may not always hold, but will ensure the test works as expected
    '''

    data_path = MULE_dir + "/packs/tests/data/malformed_data.bin"

    with raises(MalformedHeaderError):
        with open(data_path, 'rb') as file:
            a = process_event_lazy_WD1(file)
            next(a)
            next(a)

def test_lazy_loading_short_header_WD1(MULE_dir):
    '''
    Test a file that contains only 4 components in its header,
    should return a MalformedHeaderError
    '''

    data_path = MULE_dir + "/packs/tests/data/malformed_short_header.bin"
    with open(data_path, 'rb') as file:
        a = process_event_lazy_WD1(file)
        next(a)

@mark.parametrize("file, samples, channels, header_size, output", [('100bytes.bin', 1, 1, 0, 25), ('100bytes.bin', 1, 1, 46, 2), ('100bytes.bin', 2, 10, 20, 1), ('10000bytes.bin', 4, 8, 72, 50)])
def test_number_of_events_correct(data_dir, file, samples, channels, header_size, output):
    '''
    Simple test to ensure the logic returns the number of events we expect.
    '''
    file_path = data_dir + file

    assert output == number_of_events_WD2(file_path, samples, channels, header_size)


@mark.parametrize("inpt", [("one_channel_WD2.bin"),("three_channels_WD2.bin")])
def test_lazy_eager_WD2_match(data_dir, inpt):
    '''
    test to ensure that lazy and eager WD2
    provide the same result
    '''

    # how many events are we looking at?
    counts = 30

    # extract directory
    file_path = data_dir + inpt

    # collect header info
    with open(file_path, 'rb') as f:
        wdtype, samples, sampling_period, channels = process_header(f)

    # collect lazy data
    lazy_data = []
    with open(file_path) as f:
        binary_lazy_readout   = read_binary_lazy(f, wdtype)
        for i in range(0,counts):
            _, lazy_wf            = next(binary_lazy_readout)
            lazy_data.append(lazy_wf)

    # open eager data
    with open(file_path) as f:
        data                  = read_binary     (f, wdtype, counts)

    for i in range(0,counts):
        assert data[i] == lazy_data[i]
