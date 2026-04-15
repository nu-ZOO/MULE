import numpy as np
import os
from packs.core.io import read_config_file
from packs.ana.analysis_utils import average_waveforms, window_overlap_check
from packs.core.core_utils import check_test
from packs.proc.processing_utils import check_save_path
import h5py

def ana(config_file : str) -> (np.ndarray):
    # checks if test, if so ends run
    if check_test(config_file):
        return
    
    conf_args = read_config_file(config_file)
    window_args = conf_args["window_args"]

    save_path = conf_args.pop('save_path')
    overwrite = conf_args.pop('overwrite')

    window_overlap_check(window_args)

    if isinstance(conf_args["files"], list):
        print("Averaging waveform....")

        avgwf = average_waveforms(**conf_args)

        checked_save_path = check_save_path(
            save_path,
            overwrite
        )

        with h5py.File(checked_save_path, 'w') as f:     # Save as a h5
            f.create_dataset('Average_waveform', data=avgwf)

        print(f"Saved to: {checked_save_path}")

    else:
        print("Please input files as a list.")
    return