import os
import sys

import numpy as np
import pandas as pd

from pytest                        import mark
from pytest                        import raises
from pytest                        import warns

from packs.core.io import read_config_file


def test_missing_config(tmp_path, MULE_dir):
    '''
    Simple test ensuring that when config file path is wrong,
    MULE spits out a `FileNotFoundError`
    '''

    config_path = f'{tmp_path}/false_config.conf'
    
    with raises(FileNotFoundError):
        read_config_file(config_path)