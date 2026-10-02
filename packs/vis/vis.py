import os
import sys
import traceback

from packs.core.io                import read_config_file
from packs.core.core_utils        import check_test
from packs.vis.visualise_utils   import visualise_waveform

def vis(config_file):
    print("Starting the visualisation pack...")

    # checks if test, if so ends run
    if check_test(config_file):
        return

    # take full path
    full_path = os.path.expandvars(config_file)

    conf_dict = read_config_file(full_path)
    # check the method implemented, currently just process
    try:
        match conf_dict.pop('visualise'):
            case 'waveform':
                visualise_waveform(**conf_dict)
            case other:
                raise RuntimeError(f"process {other} not currently implemented.")
    except KeyError as e:
        print(f"\nError in the configuration file, incorrect or missing argument: {e} \n")
        traceback.print_exc()
        sys.exit(2)