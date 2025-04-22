import os
import sys

import numpy as np
import pandas as pd

from pytest                        import mark
from pytest                        import raises
from pytest                        import warns

from packs.core.io import read_config_file
from packs.core.io import reader
from packs.core.io import writer

def test_missing_config(tmp_path, MULE_dir):
    '''
    Simple test ensuring that when config file path is wrong,
    MULE spits out a `FileNotFoundError`
    '''

    config_path = f'{tmp_path}/false_config.conf'
    
    with raises(FileNotFoundError):
        read_config_file(config_path)


def test_reader_writer(tmp_path):
    '''
    The simplest of tests, ensure the writer produces the expected output.
    This test should be expanded to differing modifications when they are included
    as fixtures. As this isn't the case yet, there is no need.
    '''

    file = tmp_path / 'writer_output_tmp.h5'

    test_dtype = np.dtype([
                    ('int', int),
                    ('float', float),
                    ('bool', bool),
                    ('bigfloat', float),
                    ])

    test_dataset  = [np.array((0, 1.0, False, 25000.323232), dtype = test_dtype),
                     np.array((1, 4.0, True, 23456789.321), dtype = test_dtype)]

    # create the writer object
    with writer(file, 'test_group', overwrite = True) as scribe:
        # write something to it
        scribe('test_dataset', test_dataset[0])
        scribe('test_dataset', test_dataset[1])

    # read it out, should pop an a StopIteration error
    scholar = reader(file, 'test_group', 'test_dataset')
    with raises(StopIteration):
        assert next(scholar).tolist() == test_dataset[0].tolist()
        assert next(scholar).tolist() == test_dataset[1].tolist()
        next(scholar)