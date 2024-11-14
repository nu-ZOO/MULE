import os
import sys

from pytest                        import mark
from pytest                        import raises

from packs.proc.processing_utils   import read_defaults_WD2
from packs.proc.processing_utils   import generate_rwf_type

from hypothesis                    import given
from hypothesis.strategies         import integers

@given(integers(min_value = 1, max_value = 1000000))
def test_rwf_type_has_correct_shape(samples):
    x = generate_rwf_type(samples)

    assert x['rwf'].shape[0] == samples


def test_header_components_read_as_expected():
    
    MULE_dir = str(os.environ['MULE_DIR'])
    file = MULE_dir + '/packs/tests/data/three_channels_WD2.bin'

    evt_num   = 0
    tstamp    = 1998268
    smpls     = 1000
    smpl_prd  = 8

    file = open(file, 'rb')
    event_number, timestamp, samples, sampling_period = read_defaults_WD2(file, sys.byteorder)
    file.close()

    assert event_number        == evt_num
    assert timestamp           == tstamp
    assert samples             == smpls
    assert sampling_period     == smpl_prd

