import numpy  as np
import tables as tb
import pandas as pd

import h5py

# imports start from MULE/
from packs.core.core_utils import flatten

"""
Processing utilities

This file holds all the relevant functions for processing data from WaveDump 1/2 into
the h5 format.
"""




def raw_to_h5_WD1(PATH, save_h5 = False, verbose = False, print_mod = 0):
    '''
    Takes binary files data files (.dat) produced using Wavedump 1
    and decodes them into waveforms, that are then inserted into 
    pandas dataframes.

    These dataframes can then be saved as h5 files for further use.

    Parameters
    ----------

        PATH        (str)       :       File path of interest
        save_h5     (bool)      :       Flag for saving data
        verbose     (bool)      :       Flag for outputting information
        print_mod   (int)       :       Print modifier

    Returns
    -------

        data        (int 2D array) :       2D array of events
                                            First element defines event
                                            Second element defines ADC value
    ''' 

    # Makeup of the header (array[n]) where n is:
    # 0 - event size (ns in our case, with extra 24 samples)
    # 1 - board ID
    # 2 - pattern (not sure exactly what this means)
    # 3 - board channel
    # 4 - event counter
    # 5 - Time-tag for the trigger

    # Output data is a collection of ints defined in size
    # by (event size - 24) // 2

    file = open(PATH, 'rb')
    data = []

    print("File open! Processing...")
    # Collect data, while true loops are always dangerous but lets ignore that here :)
    while (True):

    # take the header information from the file (first 6 elements)
        array = np.fromfile(file, dtype='i', count=6)

        # breaking condition
        if len(array) == 0:
            print("Processing finished! Saving...")
            break
        
        # printing events
        if (array[4] % int(print_mod) == 0):
            print("Event {}".format(array[4]))
        
        # verbose check
        if (verbose == True):
            array_tag = ['event size (ns)', 'board ID', 'pattern', 'board channel', 'event counter', 'trigger tag']
            for i in range(len(array)):
                print("{}: {}".format(array_tag[i], array[i]))
        


        # alter event size to the samples
        array[0] = array[0] - 24

        # collect event
        event_size = array[0] // 2

        int16bit = np.dtype('<H')
        data.append(np.fromfile(file, dtype=int16bit, count=event_size))
    
    if (save_h5 == True):
        print("Saving raw waveforms...")
        # change path to dump the h5 file where
        # the .dat file is
        directory = PATH[:-3] + "h5"

        h5f = h5py.File(directory, 'w')
        h5f.create_dataset('pmtrw', data=data)
        h5f.close()
    else:
        directory = ""

    return data


def generate_rwf_type(samples):
    """
    Generates the data-type for raw waveforms 

    Parameters
    ----------

    Returns
    -------


    """
    return np.dtype([
            ('event_number', np.uint32), 
            ('channels', np.int32),
            ('rwf', np.float32, (samples,))
        ])


def process_header(file_path, byte_order = None):
    '''
    Collect the relevant information from the file's header, and determine if its valid 

    Header is formatted for WD2 as shown:
        Event number    -> uint32 (4 bytes)
        Timestamp       -> uint64 (8 bytes)
        Samples         -> uint32 (4 bytes)
        Sampling Period -> uint64 (8 bytes)
        (OPTIONAL)
        Channels        -> int32 (8 bytes)
    
    Waveform data is 4-byte float (float32).

    This extra optional channel poses problems, so need to consider it.
    The rest are all as expected.

    Parameters
    ----------

    Returns
    -------
    wdtype - The data type format required for collecting the data from the binary
    '''

    # ensure you're using the right byteorder. If you take the data from one machine to another
    # of differing endianness, you may have issues here!
    if byte_order == None:
        warnings.warn("Warning: No byte order provided. This may cause issues if transferring data between machines.")
        byte_order = byteorder
    elif (byte_order != 'little') and (byte_order != 'big'):
        raise Exception(f'Invalid byte order provided: {byteorder}. Please provide the correct byte order for your machine.')
    # open file
    file = open(file_path, 'rb')

    event_number, timestamp, samples, sampling_period = read_defaults_WD2(file, byte_order)
    # attempt to read channels
    channels        = int.from_bytes(file.read(4), byteorder=byte_order)

    # then read in a full collection of data, and see if the following header makes sense.
    dataset         = file.read(4*samples*channels)

    # reread it all in and validate the results
    event_number_1, timestamp_1, samples_1, sampling_period_1 = read_defaults_WD2(file, byte_order)

    # check that event header is as expected
    if (event_number_1 -1 == event_number) and (samples_1 == samples) and sampling_period_1 == (sampling_period):
        print(f"{channels} channels detected. Processing accordingly...")

        # generate data type
        wdtype = np.dtype([
            ('event_number', np.uint32), 
            ('timestamp', np.uint64), 
            ('samples', np.uint32), 
            ('sampling_period', np.uint64), 
            ('channels', np.int32),
            ] + 
            [(f'chan_{i+1}', np.float32, (samples,)) for i in range(0,channels)]
        )

        file.close()
        return wdtype, event_number, timestamp, samples, sampling_period, channels
    else:
        print(f"Single channel detected. If you're expecting more channels, something has gone wrong.\nProcessing accordingly...")
        channels = 1

            
         # generate data type
        wdtype = np.dtype([
            ('event_number', np.uint32), 
            ('timestamp', np.uint64), 
            ('samples', np.uint32), 
            ('sampling_period', np.uint64),
            ('chan_1', np.float32, (samples,))
        ])   
            
        file.close()
        return wdtype, event_number, timestamp, samples, sampling_period, channels


def binary_to_h5(file_path, wdtype, save_path, channels, samples):
    '''
    Function that uses the provided datatype from the header, creates the h5 dataframe and saves the binary

    Parameters
    ----------

    Returns
    -------
    '''
    # opens file
    with open(file_path, 'rb') as file:
        data = np.fromfile(file, dtype=wdtype)
    


    # separates the waveforms from the rest of the data
    # For many channels, formatted as:
    #      waveforms[0]     <- 0th event
    #      waveforms[0][0]  <- 0th event, 0th channel
    #      waveforms[0][1]  <- 0th event, 1st channel
    #
    # For singular channels: 
    #      waveforms[0]     <- 0th event
    #      waveforms[0][0]  <- 0th event, 0th channel
    #      waveforms[0][1]  <- IndexError: list index out of range
    
    # remove data component of dtype for event_information table
    e_dtype = np.dtype(wdtype.descr[:-channels])
    print(f'e_dtype:\n{e_dtype}')
    # if only one channel, select relevant information. Otherwise, split event by channel
    if channels == 1:
        event_information = [list(data[i])[:4] for i in range(len(data))]
        waveform = [[(data[j][0], 0, list(data[j])[-i:][0]) for i in reversed(range(1, channels+1))] for j in range(len(data))]
    else:
        event_information = [list(data[i])[:5] for i in range(len(data))]
        waveform = [[(data[j][0], data[j][4] - i, list(data[j])[-i:][0]) for i in reversed(range(1, channels+1))] for j in range(len(data))]

    # convert to list of tuples and then structured numpy array
    event_information = list(map(tuple, event_information))
    event_information = np.array(event_information, dtype = e_dtype)
    flat_rwf = np.array(flatten(waveform), dtype = generate_rwf_header(samples))
    # write event information
    with h5py.File(save_path, 'w') as h5f:
        
        h5f.create_dataset('event_info', data=event_information)
        # write waveforms
        h5f.create_dataset('raw_wf', data=flat_rwf)


