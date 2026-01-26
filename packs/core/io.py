import os

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


@contextmanager
def writer(path        :  str,
           group       :  str,
           overwrite   :  Optional[bool] = True) -> Generator:
    '''
    Outer function for a lazy h5 writer that will iteratively write to a dataset, with the formatting:
    FILE.h5 -> GROUP/DATASET
    Includes overwriting functionality, which will overwrite **GROUPS** at will if needed.
    Parameters
    ----------
    path (str)       :  File path
    group (str)      :  Group within the h5 file
    overwrite(bool)  :  Boolean for overwriting previous dataset (OPTIONAL)

    Returns
    -------
    write (func)     : write function described in write()


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
                  fixed_size  :  Optional[Union[False, Tuple[True, int, int]]] = False) -> None:
            '''
            Writes ndarray to dataset within group defined in writer().
            Fixed size used to speed up writing, if True will
            create a dataset of a fixed size rather than
            increasing the size iteratively.

            Parameters
            ----------
            dataset (str)       :  Dataset name to write to
            data (ndarray)      :  Data to write*
            fixed_size (Union[Bool, Tuple[Bool, int, int]])
                                :  Method that's either enable or disabled.
                                     False (disabled) -> Iteratively increases size of dataframe at runtime
                                     True  (enabled)  -> Requires Tuple containing
                                                            (True, number of events, index to write to)
                                   This method is best seen in action in `process_bin_WD1()`.
            * Data should be in a numpy structured array format, as can be seen in WD1 and WD2 processing
            '''
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
           dataset  :  str) -> Generator:
    '''
    A lazy h5 reader that will iteratively read from a dataset, with the formatting:

    FILE.H5 -> GROUP/DATASET
    Parameters
    ----------
    path (str)       :  File path
    group (str)      :  Group name within the h5 file
    dataset (str)    :  Dataset name within the group
    Returns
    -------
    row (generator)  :  Generator object that returns the next row from the dataset upon being called.
    '''

    with h5py.File(path, 'r') as h5f:
        gr = h5f[group]
        dset = gr[dataset]

        for row in dset:
            yield row
