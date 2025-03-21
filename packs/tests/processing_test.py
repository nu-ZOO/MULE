import os
import sys

import numpy as np

import pandas as pd
import subprocess

import configparser

from pytest                        import mark
from pytest                        import raises
from pytest                        import warns

from packs.proc.processing_utils   import process_bin_WD1, process_event_lazy_WD1, read_defaults_WD2
from packs.proc.processing_utils   import process_header
from packs.proc.processing_utils   import read_binary
from packs.proc.processing_utils   import format_wfs
from packs.proc.processing_utils   import check_save_path
from packs.proc.processing_utils   import save_data

from packs.types.types             import generate_wfdtype
from packs.types.types             import rwf_type
from packs.types.types             import event_info_type

from packs.core.core_utils import MalformedHeaderError

from packs.core.io                 import load_rwf_info
from packs.core.io                 import load_evt_info
from packs.core.io                 import reader

from packs.types                   import types
from hypothesis                    import given
from hypothesis.strategies         import integers

@given(integers(min_value = 1, max_value = 1000000))
def test_rwf_type_has_correct_shape(samples):
    x = rwf_type(samples)

    assert x['rwf'].shape[0] == samples


def test_header_components_read_as_expected():

    MULE_dir = str(os.environ['MULE_DIR'])
    file = MULE_dir + '/packs/tests/data/three_channels_WD2.bin'

    evt_num   = 0
    tstamp    = 1998268
    smpls     = 1000
    smpl_prd  = 8

    with open(file, 'rb') as f:
        event_number, timestamp, samples, sampling_period = read_defaults_WD2(f, sys.byteorder)

    assert event_number        == evt_num
    assert timestamp           == tstamp
    assert samples             == smpls
    assert sampling_period     == smpl_prd


def test_header_processed_correctly():

    MULE_dir = str(os.environ['MULE_DIR'])
    file = MULE_dir + '/packs/tests/data/three_channels_WD2.bin'

    smpls     = 1000
    smpl_prd  = 8
    channels  = 3
    wdtype    = generate_wfdtype(channels, smpls) # 3 channels in this case

    result = process_header(file)

    assert result[0] == wdtype
    assert result[1] == smpls
    assert result[2] == smpl_prd
    assert result[3] == channels

def test_header_works_when_data_malformed():
    # this test would normally cause a memory error as the data
    # provided is singular channel, and `process_header()` tests
    # for single channel behaviour by analysing it as multi-channel
    # and returning a single channel response if the header breaks.

    # Here,the header will crash out due to a channels value > 10^10.
    # This has been fixed quickly in process_header, but should be
    # optimised in a different fashion.

    MULE_dir = str(os.environ['MULE_DIR'])
    file = MULE_dir + '/packs/tests/data/malformed_data.bin'

    with warns(UserWarning):
        process_header(file)

@mark.parametrize("function, error", [(process_header, NameError),
                                      (read_defaults_WD2, ValueError)])
def test_endian_error_when_reading(function, error):

    MULE_dir = str(os.environ['MULE_DIR'])
    file = MULE_dir + '/packs/tests/data/three_channels_WD2.bin'


    byte_order = 'Big' # this will raise a ValueError

    with raises(error):
        with open(file, 'rb') as f:
            holder = function(f, byte_order)


def test_invalid_file_for_reading():

    MULE_dir = str(os.environ['MULE_DIR'])
    file = MULE_dir + '/packs/tests/data/false_data.npy'


    x = read_binary(file, types.generate_wfdtype(1, 1000))

    # if you've malformed the data types on a non-binary file, the result should be empty
    # but this may not always be the case.
    assert len(x) == 0


def test_formatting_works():

    MULE_dir = str(os.environ['MULE_DIR'])

    file_path  = MULE_dir + '/packs/tests/data/three_channels_WD2.bin'

    # collect relevant data from output
    check_file      = MULE_dir + '/packs/tests/data/three_channels_WD2.h5'
    check_rwf       = load_rwf_info(check_file, 1000)
    check_evt_info  = load_evt_info(check_file)


    channels = 3
    samples = 1000

    wdtype = types.generate_wfdtype(channels, samples)

    with open(file_path, 'rb') as file:
        # read in data
        data = read_binary(file, wdtype)

    evt_info, rwf = format_wfs(data, wdtype, samples, channels)

    # modify into dataframes for appropriate comparison
    rwf = pd.DataFrame(list(map(list, rwf)), columns = rwf_type(samples).names)
    evt_info = pd.DataFrame(list(map(list, evt_info)), columns = event_info_type.names)

    assert rwf.equals(check_rwf)
    assert evt_info.equals(check_evt_info)


def test_ensure_new_path_created():

    MULE_dir = str(os.environ['MULE_DIR'])
    data_path     = MULE_dir + '/packs/tests/data/three_channels_WD2.h5'
    new_data_path = MULE_dir + '/packs/tests/data/three_channels_WD21.h5'

    found_path    = check_save_path(data_path, overwrite = False)

    assert found_path == new_data_path


def test_runtime_error_when_too_many_save_files():

    MULE_dir     = str(os.environ['MULE_DIR'])
    relevant_dir = MULE_dir + '/packs/tests/data/repetitive_data/'
    # generate 101 empty files
    with open(relevant_dir + f'test_.txt', 'w'):
            pass
    for i in range(1, 101):
        with open(relevant_dir + f'test_{i}.txt', 'w'):
            pass
    with raises(RuntimeError):
        check_save_path(relevant_dir + 'test_.txt', overwrite=False)


@mark.parametrize("config, inpt, output, comparison", [("process_WD2_1channel.conf", "one_channel_WD2.bin", "one_channel_tmp.h5", "one_channel_WD2.h5"),
                                                       ("process_WD2_3channel.conf", "three_channels_WD2.bin", "three_channels_tmp.h5", "three_channels_WD2.h5")])
def test_decode_produces_expected_output(config, inpt, output, comparison):

    MULE_dir     = str(os.environ['MULE_DIR'])
    data_dir     = "/packs/tests/data/"

    # ensure path is correct
    file_path       = MULE_dir + data_dir + inpt
    save_path       = MULE_dir + data_dir + output
    comparison_path = MULE_dir + data_dir + comparison
    config_path     = MULE_dir + data_dir + "configs/" + config

    # collect samples from header
    _, samples, _, _ = process_header(file_path)

    # rewrite paths to files
    cnfg = configparser.ConfigParser()
    cnfg.read(config_path)
    cnfg.set('required', 'file_path', "'" +  file_path + "'") # need to add comments around for config reasons
    cnfg.set('required', 'save_path', "'" +  save_path + "'")

    with open(config_path, 'w') as cfgfile:
        cnfg.write(cfgfile)

    # run processing pack decode
    run_pack = ['python3', MULE_dir + "/bin/mule", "proc", config_path]
    subprocess.run(run_pack)
    # check that the resulting dataframe is as expected
    assert load_evt_info(save_path).equals(load_evt_info(comparison_path))
    assert load_rwf_info(save_path, samples).equals(load_rwf_info(comparison_path, samples))

@mark.parametrize("config, inpt, output, comparison", [("process_WD1_1channel.conf", "one_channel_WD1.dat", "one_channel_WD1_tmp.h5", "one_channel_WD1.h5")])
def test_WD1_decode_produces_expected_output(config, inpt, output, comparison):
    '''
    This test will be merged with test_decode_produces_expected_output()
    once WD2 processing has been updated to match lazy method of WD1
    '''

    MULE_dir     = str(os.environ['MULE_DIR'])
    data_dir     = "/packs/tests/data/"

    # ensure path is correct
    file_path       = MULE_dir + data_dir + inpt
    save_path       = MULE_dir + data_dir + output
    comparison_path = MULE_dir + data_dir + comparison
    config_path     = MULE_dir + data_dir + "configs/" + config

    # rewrite paths to files
    cnfg = configparser.ConfigParser()
    cnfg.read(config_path)
    cnfg.set('required', 'file_path', "'" +  file_path + "'") # need to add comments around for config reasons
    cnfg.set('required', 'save_path', "'" +  save_path + "'")

    with open(config_path, 'w') as cfgfile:
        cnfg.write(cfgfile)

    # run processing pack decode
    run_pack = ['python3', MULE_dir + "/bin/mule", "proc", config_path]
    subprocess.run(run_pack)

    # the event info can be read out like a normal h5, the RWF cannot due to how they're structured
    assert pd.read_hdf(save_path, 'RAW/event_info').equals(pd.read_hdf(comparison_path, 'RAW/event_info'))
    assert [x for x in reader(save_path, 'RAW', 'rwf')] == [x for x in reader(comparison_path, 'RAW', 'rwf')]

def test_lazy_loading_malformed_data():
    '''
    Test that a file you pass through with no appropriate header is flagged if it's
    not functioning correctly.

    ATM the check for this is:
    - event number goes up +1 events
    - number of samples stays the same across two events
    - timestamp increases between events
    These may not always hold, but will ensure the test works as expected
    '''

    MULE_dir = str(os.environ['MULE_DIR'])
    data_path = MULE_dir + "/packs/tests/data/malformed_data.bin"

    with raises(MalformedHeaderError):
        with open(data_path, 'rb') as file:
            a = process_event_lazy_WD1(file, sample_size = 2)
            next(a)
            next(a)

