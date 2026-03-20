import sys

import numpy as np
import pandas as pd
import subprocess
import pytest                      
import configparser

from packs.proc.processing_utils   import process_header

from pytest                        import mark

from packs.proc.proc               import proc

from packs.core.io                 import load_rwf_info
from packs.core.io                 import load_evt_info


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

@mark.parametrize("config, inpt, output, comparison", [("process_WD2_1channel.conf", "one_channel_WD2.bin", "one_channel_tmp.h5", "one_channel_WD2.h5"),
                                           ("process_WD2_3channel.conf", "three_channels_WD2.bin", "three_channels_tmp.h5", "three_channels_WD2.h5")])
def test_changing_config_order(config, inpt, output, comparison, MULE_dir, data_dir):
    """
    Test that ensure that changing the order of the config parameters
    inputted does not affect the code.
    """
    # ensure path is correct
    file_path       =  data_dir + inpt
    save_path       =  data_dir + output
    comparison_path =  data_dir + comparison
    config_path     =  data_dir + "configs/" + config

    # collect samples from header
    _, samples, _, _ = process_header(file_path)

    # keep a copy of the original config file to rewrite after test
    with open(config_path, "r") as f:
        original_content = f.read()

    try:
        # rewrite config file with parameters in different order
        cnfg = configparser.ConfigParser()
        cnfg.read(config_path)

        # Rebuild the section in new order
        new_order = ["save_path", "file_path", "wavedump_edition", "process"]
        reordered = configparser.ConfigParser()
        reordered.add_section("required")

        for key in new_order:
            reordered.set("required", key, cnfg.get("required", key))

        # Write back
        with open(config_path, "w") as f:
            reordered.write(f)

        # run processing pack decode
        run_pack = ['python3', MULE_dir + "/bin/mule", "proc", config_path]
        subprocess.run(run_pack)
        # check that the resulting dataframe is as expected
        assert load_evt_info(save_path).equals(load_evt_info(comparison_path))
        assert load_rwf_info(save_path, samples).equals(load_rwf_info(comparison_path, samples))
    finally:
        # rewrite config file to original state
        with open(config_path, "w") as f:
            f.write(original_content)
