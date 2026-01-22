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


def test_writer_overwriting(tmp_path, data_dir):
    '''
    Testing the 'overwrite' flag works when true,
    this test writes random data over the prior file and check
    that the reader reads out exactly the same input, with no extra information
    '''

    file = f'{tmp_path}/overwriter_test.h5'
    # generate junk data
    test_dtype = np.dtype([
                    ('int', int),
                    ('float', float),
                    ('bool', bool),
                    ('bigfloat', float),
                    ])

    test_data       = [np.array((0, 1.0, False, 25000.323232), dtype = test_dtype),
                       np.array((1, 4.0, True, 23456789.321), dtype = test_dtype)]

    overwrite_data  = [np.array((1, 2.0, True, 30123.323232), dtype = test_dtype),
                       np.array((4, 5.0, False, 2.321), dtype = test_dtype)]

    # write file with junk data
    with writer(file, 'RAW', overwrite = True) as scribe:
        for data in test_data:
            scribe('rwf', data)
    initial_data = []
    # check the output is correct
    for data in reader(file, 'RAW', 'rwf'):
        initial_data.append(data)


    # overwrite file with new junk data
    with writer(file, 'RAW', overwrite = True) as scribe:
        for data in overwrite_data:
            scribe('rwf', data)
    # readout of overwrite data
    output_data = []
    for data in reader(file, 'RAW', 'rwf'):
        output_data.append(data)


    # ensure that these two lists arent identical
    assert not np.array_equal(np.array(output_data), np.array(initial_data))
    # sanity check that the output is what you expect it is
    assert np.array_equal(np.array(output_data), np.array(overwrite_data))


def test_writer_not_overwriting(tmp_path, data_dir):
    '''
    Testing 'overwrite' flag when false,
    this test writes random data to the end of the prior file
    and checks that the reader reads out both new and old data
    '''
    file = f'{tmp_path}/overwriter_test_2.h5'
    # generate junk data
    test_dtype = np.dtype([
                    ('int', int),
                    ('float', float),
                    ('bool', bool),
                    ('bigfloat', float),
                    ])

    test_data       = [np.array((0, 1.0, False, 25000.323232), dtype = test_dtype),
                       np.array((1, 4.0, True, 23456789.321), dtype = test_dtype)]

    append_data     = [np.array((1, 2.0, True, 30123.323232), dtype = test_dtype),
                       np.array((4, 5.0, False, 2.321), dtype = test_dtype)]

    total_data      = test_data + append_data

    # write file with junk data
    with writer(file, 'RAW', overwrite = True) as scribe:
        for data in test_data:
            scribe('rwf', data)
    initial_data = []
    # check the output is correct
    for data in reader(file, 'RAW', 'rwf'):
        initial_data.append(data)


    # append file with new junk data
    with writer(file, 'RAW', overwrite = False) as scribe:
        for data in append_data:
            scribe('rwf', data)
    # readout of overwrite data
    output_data = []
    for data in reader(file, 'RAW', 'rwf'):
        output_data.append(data)


    # ensure that these two lists are identical
    assert np.array_equal(np.array(output_data), np.array(total_data))



def test_writer_fixed_size_correct_output(tmp_path):
    '''
    provide a particular size of dataframe, see if it
    returns as expected
    '''

    file = f'{tmp_path}/fixed_size_tester.h5'

    test_dtype = np.dtype([
                    ('int', int),
                    ('float', float),
                    ('bool', bool),
                    ('bigfloat', float),
                    ])


    test_data       = [np.array((0, 1.0, False, 25000.323232), dtype = test_dtype),
                       np.array((1, 4.0, True, 23456789.321), dtype = test_dtype),
                       np.array((1, 2.0, True, 30123.323232), dtype = test_dtype),
                       np.array((4, 5.0, False, 2.321), dtype = test_dtype)]

    # write the data
    with writer(file, 'RAW', overwrite = True) as scribe:
        for i, data in enumerate(test_data):
            scribe('rwf', data, (True, len(test_data), i))

    # read and check the data
    for data_in, data_out in zip(test_data, reader(file, 'RAW', 'rwf')):
        assert data_in == data_out

def test_writer_fixed_size_provided_incorrectly(tmp_path):
    '''
    if you provide a fixed size for the writer, then try and write to it
    with more events than chosen
    '''

    file = f'{tmp_path}/fixed_size_tester_2.h5'

    test_dtype = np.dtype([
                    ('int', int),
                    ('float', float),
                    ('bool', bool),
                    ('bigfloat', float),
                    ])


    test_data       = [np.array((0, 1.0, False, 25000.323232), dtype = test_dtype),
                       np.array((1, 4.0, True, 23456789.321), dtype = test_dtype),
                       np.array((1, 2.0, True, 30123.323232), dtype = test_dtype),
                       np.array((4, 5.0, False, 2.321), dtype = test_dtype)]

    # expect IndexError when reading out
    with raises(IndexError):
        with writer(file, 'RAW', overwrite = True) as scribe:
            for i, data in enumerate(test_data):
                scribe('rwf', data, (True, len(test_data)-1, i))


