import pandas as pd
import numpy  as np

import h5py
import ast
import configparser

from contextlib import contextmanager

from typing import Optional
from typing import Generator
from typing import Union
from typing import Tuple

from functools import partial

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


@contextmanager
def writer(path        :  str,
           group       :  str,
           overwrite   :  Optional[bool] = True) -> Generator:
    '''
    Standard function that tries to put data into a dataset within a h5 file.
    It will create everything it needs up the chain (dataset, group, path) when
    flag 'w' is created.

    Fixed size is for when you know the size of the output file, so you set the size
    of the df beforehand, saving precious IO operation. The input then becomes a tuple
    of (True, DF_SIZE, INDEX), otherwise its false.
    '''

    # open file if exists, create group or overwrite it
    h5f = h5py.File(path, 'a')
    try:
        if overwrite:
            if group in h5f:
                del h5f[group]

        gr  = h5f.require_group(group)

        def write(dataset     :  str,
                  data        :  np.ndarray,
                  fixed_size  :  Optional[Union[False, Tuple[True, int, int]]] = False):

            if fixed_size is False:
                # create dataset if doesnt exist, if does make larger
                if dataset in gr:
                    dset = gr[dataset]
                    dset.resize((dset.shape[0] + 1, *dset.shape[1:]))
                    dset[-1] = data
                else:
                    max_shape = (None,) + data.shape
                    dset = gr.require_dataset(dataset, shape = (1,) + data.shape,
                                              maxshape = max_shape, dtype = data.dtype,
                                              chunks = True)
                    dset[0] = data
            else:
                index = fixed_size[2]
                # dataset of fixed size
                if dataset in gr:
                    dset = gr[dataset]
                else:
                    dset = gr.require_dataset(dataset, shape = (fixed_size[1],) + data.shape,
                                              maxshape = fixed_size[1], dtype = data.dtype,
                                              chunks = True)
                dset[index] = data

        yield write

    finally:
        h5f.close()

def reader(path     :  str,
           group    :  str,
           dataset  :  str):
    '''
    Standard function that stupidly reads events iteratively from h5 file group.

    Should be redone with this documentation in mind:
    https://docs.h5py.org/en/stable/high/dataset.html#reading-writing-data
    '''

    with h5py.File(path, 'r') as h5f:
        gr = h5f[group]
        dset = gr[dataset]

        for row in dset:
            yield row
