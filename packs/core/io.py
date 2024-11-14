import pandas as pd

import h5py

from packs.types import types


def load_evt_info(save_path, merge = False):
    '''
    Loads in a processed WD2 h5 file as pandas DataFrame

    Parameters
    ----------

    merge  (bool)  :  Flag for merging chunked data

    Returns
    -------

    merge  (dataframe)  :  Dataframe of event information
    '''

    h5_data = []
    with h5py.File(save_path) as f:
        # extract event info
        evt_info = f.get('event_information')
        for i in evt_info.keys():
            q = evt_info.get(str(i))
            for j in q:
                h5_data.append(j)

    
    return pd.DataFrame(list(map(list, h5_data)), columns = (types.event_info_type).names)


def load_rwf_info(file_path  :  str,
                  samples    :  int) -> list:
    '''
    Collates the event information and rwf data into alist
    '''
    h5_data = []
    with h5py.File(file_path) as f:
        rwf_info = f.get('rwf')
        for i in rwf_info.keys():
                        q = rwf_info.get(str(i))
                        for j in q:
                            h5_data.append(j)

    return pd.DataFrame(list(map(list, h5_data)), columns = (types.rwf_type(samples)).names)


