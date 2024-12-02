import numpy as np


event_info_type = np.dtype([
            ('event_number', np.uint32), 
            ('timestamp', np.uint64), 
            ('samples', np.uint32), 
            ('sampling_period', np.uint64), 
            ('channels', np.int32),
            ])

def rwf_type(samples  :  int) -> np.dtype:
    """
    Generates the data-type for raw waveforms 

    Parameters
    ----------

        samples  (int)  :  Number of samples per waveform

    Returns
    -------

        (ndtype)  :  Desired data type for processing


    """
    return np.dtype([
            ('event_number', np.uint32), 
            ('channels', np.int32),
            ('rwf', np.float32, (samples,))
        ])


def generate_wfdtype(channels, samples):
    '''
    generates the dtype for collecting the binary data based on samples and number of
    channels
    '''
    if channels >1:
        wdtype = np.dtype([
                ('event_number', np.uint32), 
                ('timestamp', np.uint64), 
                ('samples', np.uint32), 
                ('sampling_period', np.uint64), 
                ('channels', np.int32),
                ] + 
                [(f'chan_{i+1}', np.float32, (samples,)) for i in range(0,channels)]
        )
    else:
        wdtype = np.dtype([
            ('event_number', np.uint32), 
            ('timestamp', np.uint64), 
            ('samples', np.uint32), 
            ('sampling_period', np.uint64),
            ('chan_1', np.float32, (samples,))
        ])

    return wdtype   
