#from pathlib import Path
import os
import pytest

@pytest.fixture(scope="session")
def MULE_dir():
    return str(os.environ['MULE_DIR'])

@pytest.fixture(scope="session")
def data_dir(MULE_dir):
    return MULE_dir + '/packs/tests/data/'

@pytest.fixture(scope="session")
def ch3wd2_dir(data_dir):
    return data_dir + 'three_channels_WD2.bin'