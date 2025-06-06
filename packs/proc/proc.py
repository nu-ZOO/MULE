import os

from packs.core.io                import read_config_file
from packs.proc.processing_utils  import process_bin_WD2
from packs.proc.processing_utils  import process_bin_WD1
from packs.proc.waveform_utils    import calibrate
from packs.core.core_utils        import check_test

def proc(config_file):
    print("Starting the processing pack...")

    # checks if test, if so ends run
    if check_test(config_file):
        return

    # take full path
    full_path = os.path.expandvars(config_file)

    conf_dict = read_config_file(full_path)
    
    # check the method implemented, currently just process
    match conf_dict['process']:
        case 'decode':
            # removing the first two components so that the other arguments are passed correctly
            arg_dict  = dict(list(conf_dict.items())[2:])
            if conf_dict['wavedump_edition'] == 2:
                process_bin_WD2(**arg_dict)
            elif conf_dict['wavedump_edition'] == 1:
                process_bin_WD1(**arg_dict)
            else:
                raise RuntimeError(f"wavedump edition {conf_dict['wavedump_edition']} decoding isn't currently implemented.")
        case 'calibrate':
            # removing the first component so that the other arguments are passed correctly
            arg_dict  = dict(list(conf_dict.items())[1:])
            calibrate(**arg_dict)
        case default:
            raise RuntimeError(f"process {conf_dict['process']} not currently implemented.")
