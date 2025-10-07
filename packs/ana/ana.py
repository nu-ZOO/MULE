import numpy as np
import os
from packs.core.io import read_config_file
from packs.ana.analysis_utils import average_waveforms
from packs.core.core_utils import check_test

def ana(config_file):
    # checks if test, if so ends run
    if check_test(config_file):
        return
    
    conf_args = read_config_file(config_file)
    arg_dict = dict(list(conf_args.items())[:-1])

    if isinstance(conf_args['files'], list):
        print('Averaging waveform....')
        avgwf = average_waveforms(**arg_dict)
        np.savetxt(conf_args['save_path'], avgwf, delimiter = ',')
        print('Average waveform saved as', conf_args['save_path'])

    else:
        print("Please input files as a list.")
    return