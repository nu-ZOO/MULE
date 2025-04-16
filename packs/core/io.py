import os

import pandas as pd

import h5py
import ast
import configparser


from packs.types import types


def load_evt_info(file_path, merge = False):
    '''
    Loads in a processed WD .h5 file as pandas DataFrame, extracting event information tables.

    Parameters
    ----------

    file_path (str)   :  Path to saved data
    merge     (bool)  :  Flag for merging chunked data

    Returns
    -------

    (pd.DataFrame)  :  Dataframe of event information
    '''

    h5_data = []
    with h5py.File(file_path) as f:
        # extract event info
        evt_info = f.get('event_information')
        for i in evt_info.keys():
            q = evt_info.get(str(i))
            for j in q:
                h5_data.append(j)


    return pd.DataFrame(map(list, h5_data), columns = (types.event_info_type).names)


def load_rwf_info(file_path  :  str,
                  samples    :  int) -> list:
    '''
    Loads in a processed WD .h5 file as pandas dataframe, extracting raw waveform tables.
    Samples must be provided, and can be found using `load_evt_info()`.

    Parameters
    ----------

    file_path (str)  :  Path to saved data
    samples   (int)  :  Number of samples in each raw waveform

    Returns
    -------

    (pd.DataFrame)  :  Dataframe of raw waveform information
    '''
    h5_data = []
    with h5py.File(file_path) as f:
        rwf_info = f.get('rwf')
        for i in rwf_info.keys():
            q = rwf_info.get(str(i))
            for j in q:
                h5_data.append(j)

    return pd.DataFrame(map(list, h5_data), columns = (types.rwf_type(samples)).names)


def read_config_file(file_path  :  str) -> dict:
    '''
    Read config file passed in via 'mule' and extract relevant information for pack.
    Example:

    >> mule proc config.conf

    This function collects the relevant information from `config.conf` and passes it to the `proc` pack.

    Parameters
    ----------

    file_path (str)  :  Path to config file

    Returns
    -------

    arg_dict (dict)  :  Dictionary of relevant arguments for the pack
    '''
    # setup config parser
    config = configparser.ConfigParser()

    if not os.path.exists(file_path):
        raise FileNotFoundError(2, 'No such config file', file_path)
        

    # read in arguments, require the required ones
    config.read(file_path)
    arg_dict = {}
    for section in config.sections():
        for key in config[section]:
            # the config should be written in such a way that the python evaluator
            # can determine its type
            #
            # we can setup stricter rules at some other time
            arg_dict[key] = ast.literal_eval(config[section][key])

    return arg_dict
