import os
import sys

import numpy as np
import pandas as pd

from pytest                        import mark
from pytest                        import raises
from pytest                        import warns

from packs.core.io import reader
from packs.core.io import writer


def test_reader_writer():
    '''
    The simplest of tests, ensure the writer produces the expected output.

    This test should be expanded to differing modifications when they are included
    as fixtures. As this isn't the case yet, there is no need.
    '''

    MULE_dir = str(os.environ['MULE_DIR'])
    file = MULE_dir + '/packs/tests/data/writer_output_tmp.h5'
    comparison = MULE_dir + '/packs/tests/data/writer_output.h5'

    test_dtype = np.dtype([
                    ('int', int),
                    ('float', float),
                    ('bool', bool),
                    ('bigfloat', float),
                    ])

    test_dataset = np.array((0, 1.0, False, 25000.323232), dtype = test_dtype)

    # create the writer object
    scribe = writer(file, 'test_group', overwrite = True)

    # write something to it
    scribe('test_dataset', test_dataset)

    # read it out
    scholar = reader(file, 'test_group', 'test_dataset')
    scroll  = np.array(next(scholar))

    assert scroll.tolist() == test_dataset.tolist()

