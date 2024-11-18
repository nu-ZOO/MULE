import os
import sys

import numpy as np
import pandas as pd

from pytest                        import mark
from pytest                        import raises

from packs.proc.processing_utils   import read_defaults_WD2
from packs.proc.processing_utils   import process_header
from packs.proc.processing_utils   import read_binary
from packs.proc.processing_utils   import format_wfs

from packs.types.types             import generate_wfdtype
from packs.types.types             import rwf_type
from packs.types.types             import event_info_type

from packs.core.io                 import load_rwf_info
from packs.core.io                 import load_evt_info

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


def test_endian_error_when_reading():

    MULE_dir = str(os.environ['MULE_DIR'])
    file = MULE_dir + '/packs/tests/data/three_channels_WD2.bin'


    byte_order = 'Big' # this will raise a ValueError 
    
    with raises(ValueError):
        with open(file, 'rb') as f:
            event_number, timestamp, samples, sampling_period = read_defaults_WD2(f, byte_order)


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