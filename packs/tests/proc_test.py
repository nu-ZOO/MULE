import sys

import numpy as np
import pandas as pd
import subprocess

import configparser

import pytest                      

from packs.proc.proc               import proc


def test_incorrect_key_name(MULE_dir, capsys):
    """
    A simple test that ensures that when an incorrect key name is present in
    the config file, the appropriate error is raised.
    """
    conf = MULE_dir + "/packs/tests/data/configs/incorrect_key_name.conf"
    with pytest.raises(SystemExit) as e: 
        proc(str(conf))
    # captures output
    out = capsys.readouterr().out
    assert "incorrect or missing argument: 'process'" in out