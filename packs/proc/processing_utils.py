
import sys
import os
import numpy  as np
import tables as tb
import pandas as pd
import warnings

import h5py

from typing import BinaryIO
from typing import Generic
from typing import Optional

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


def generate_rwf_type(samples  :  int) -> np.ndtype:
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

def read_defaults_WD2(file        :  BinaryIO, 
                      byte_order  :  str) -> (int, int, int, int):
    '''
    Provided with an open WD2 binary file, will provide the header information.

    Parameters
    ----------

        file        (BufferedReader)  :  Opened file
        byte_order  (str)             :  Byte order

    Returns
    -------

        event_number     (int)  :  First event number extracted from file
        timestamp        (int)  :  Timestamp of first event
        samples          (int)  :  Number of samples
        sampling_period  (int)  :  The time value of 1 sample in ns
    '''

    event_number    = int.from_bytes(file.read(4), byteorder=byte_order)
    timestamp       = int.from_bytes(file.read(8), byteorder=byte_order)
    samples         = int.from_bytes(file.read(4), byteorder=byte_order)
    sampling_period = int.from_bytes(file.read(8), byteorder=byte_order)

    return (event_number, timestamp, samples, sampling_period)


def process_header(file_path  :  str, 
                   byte_order :  Optional[str] = None) -> (np.dtype, int, int, int):
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

    The `byte_order` should generally be left alone, but I have left it as an optional argument
    as there may be situations in which the data is recorded as little-endian and the computer you're
    processing it on is big-endian.

    Parameters
    ----------

        file_path  (str)  :  Path to binary file
        byte_order (str)  :  Byte order

    Returns
    -------

        wdtype           (ndtype)  :  Custom data type for extracting information from
                                      binary files
        samples          (int)     :  Number of samples per event
        sampling_period  (int)     :  The time value of 1 sample in ns
        channels         (int)     :  Number of channels in the data
    '''

    # ensure you're using the right byteorder. If you take the data from one machine to another
    # of differing endianness, you may have issues here!
    if byte_order == None:
        warnings.warn("Warning: No byte order provided. This may cause issues if transferring data between machines.")
        byte_order = sys.byteorder
    elif (byte_order != 'little') and (byte_order != 'big'):
        raise Exception(f'Invalid byte order provided: {byteorder}. Please provide the correct byte order for your machine.')
    
    # open file
    file = open(file_path, 'rb')

    event_number, timestamp, samples, sampling_period = read_defaults_WD2(file, byte_order)
    # attempt to read channels
    channels        = int.from_bytes(file.read(4), byteorder=byte_order)

    # then read in a full collection of data, and see if the following header makes sense.
    dataset         = file.read(4*samples*channels)
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
    return wdtype, samples, sampling_period, channels



def binary_to_h5(file_path,
                 wdtype,
                 save_path, channels, samples):
    '''
    DEPRECATED: This function has been refactored and will be removed soon.
    Function that uses the provided datatype from the header, creates the h5 dataframe and saves the binary

    Parameters
    ----------

        file_path  (str)        :  Path to binary file
        wdtype     (ndtype)     :  Custom data type for extracting information from
                                   binary files
        save_path  (str)        :  Path to saved file
        channels   (int)        :  Number of channels in acquisition
        samples    (int)        :  Number of samples per event

    Returns
    -------
        event_information (ndarray)  :  
        waveform_data     (ndarray)  : 


    '''
    # opens file
    with open(file_path, 'rb') as file:
        data = np.fromfile(file, dtype=wdtype)

    
    # remove data component of dtype for event_information table
    e_dtype = np.dtype(wdtype.descr[:-channels])
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
    flat_rwf = np.array(flatten(waveform), dtype = generate_rwf_type(samples))


    ### SEPARATE THIS INTO SEPARATE FUNCTION
    # write event information
    with h5py.File(save_path, 'w') as h5f:
        
        h5f.create_dataset('event_info', data=event_information)
        # write waveforms
        h5f.create_dataset('raw_wf', data=flat_rwf)

def read_binary(file    :  BinaryIO,
                wdtype  :  np.dtype, 
                counts  :  Optional[int] = -1,  
                offset  :  Optional[int] = 0) -> np.ndarray:
    '''
    Reads the binary in with the expected format/offset

    Parameters
    ----------

        file    (BufferedReader)  :  Opened file
        wdtype  (ndarray)         :  Custom data type for extracting information from
                                     binary files
        counts  (int)             :  How many events you want to read in. -1 sets it to take all events.
        offset  (int)             :  Offset at which to start reading the data. Used for chunking purposes
                                     and so should by default be set to zero if not chunking.

    Returns
    -------
        data  (ndarray)  :  Unformatted data from binary file

    '''
    # be aware, you're passing through the open file object
    #print(file, wdtype, counts)
    data = np.fromfile(file, dtype=wdtype, count = counts, offset = offset)

    return data

def format_wfs(data      :  np.ndarray,
               wdtype    :  np.dtype, 
               samples   :  int, 
               channels  :  int) -> (np.ndarray, np.ndarray):
    '''
    Formats the data for saving purposes.

    Parameters
    ----------

        data      (ndarray)  :  Unformatted data from binary file
        wdtype    (ndtype)   :  Custom data type for extracting information from
                                binary files
        samples   (int)      :  Number of samples in each waveform list
        channels  (int)      :  The first event number in the file (generally)

    Returns
    -------
        event_information (ndarray)  :  Reformatted event information
        waveform          (ndarray)  :  Reformatted waveforms

    '''
    # remove data component of dtype for event_information table
    e_dtype = np.dtype(wdtype.descr[:-channels])
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
    waveform = np.array(flatten(waveform), dtype = generate_rwf_type(samples))

    return event_information, waveform

def save_data(event_information  :  np.ndarray, 
              rwf                :  np.ndarray, 
              save_path          :  str, 
              event_number       :  Optional[int] = 0):
    '''
    Produces the h5 files given the event information and raw waveforms

    Parameters
    ----------

        event_information  (ndarray)  :  Event information from the binary file
        rwf                (ndarray)  :  Raw waveforms from the binary file
        save_path          (str)      :  Path to saved file
        event_number       (int)      :  The first event number in the file (generally)

    Returns
    -------

        None

    '''

    # check if first set of events, if so 'w', otherwise 'a'
    if event_number == 0:
        h5f = h5py.File(save_path, 'w')
        evt_info = h5f.create_group('event_information')
        rwf_grp = h5f.create_group('rwf')
    else:
        h5f = h5py.File(save_path, 'a')
        # creates groups if they dont exist
        evt_info = h5f.require_group('event_information')
        rwf_grp = h5f.require_group('rwf')
    
    evt_info.create_dataset('ei_' + str(event_number), data=event_information)
    # write waveforms
    rwf_grp.create_dataset('rwf_' + str(event_number), data=rwf)

    h5f.close()

def check_save_path(save_path  :  str, 
                    overwrite  :  bool, 
                    iterator   :  Optional[int] = 0) -> str:
    '''
    Checks that the save_path is valid/doesn't already exist and if it does, other `overwrite` it
    or create an additional file with the addage '_iterator'

    Parameters
    ----------

        save_path  (str)   :  Path to saved file
        overwrite  (bool)  :  Boolean for overwriting pre-existing files
        iterator   (int)   :  Value to add to the end of the save_path if the previous already exists.

    Returns
    -------
        save_path  (str)  :  Valid path to saved file, either unmodified or altered to add '_N' 
                             where N is number of loops it had to do before finding a valid N
    
    '''

    if os.path.isfile(save_path) and overwrite == False:
        # if this has been done before, change _1 to _2, or _2 to _3, etc.
        new_path = save_path.split('.')
        if iterator > 0: 
            save_path = new_path[0][:-2] + '_' + str(iterator) + '.' + new_path[1]
        else:
            save_path = new_path[0] + '_' + str(iterator) + '.' + new_path[1]

        warnings.warn("File already exists at `save_path` but overwrite described as false. Altering save_path to:")
        iterator += 1
        if iterator > 100:
            raise RuntimeError('Unable to find valid save path after 100 attempts.')
        save_path = check_save_path(save_path, overwrite = overwrite, iterator = iterator)
    else:
        # this is the case where we want to overwrite
        try:
            os.remove(save_path)
        except:
            warnings.warn("Overwriting of saved file failed as it cannot be found.")
            pass

    return save_path


def process_bin_WD2(file_path, save_path, overwrite = False, counts = -1):

    '''
    Takes a binary file and outputs the containing waveform information in a h5 file.

    For particularly large waveforms/number of events. You can 'chunk' the data such that 
    each dataset holds `counts` events.

    Parameters
    ----------

        file_path  (str)   :  Path to binary file
        save_path  (str)   :  Path to saved file
        overwrite  (bool)  :  Boolean for overwriting pre-existing files
        counts     (int)   :  The number of events per chunks. -1 implies no chunking of data.

    Returns
    -------
        None
    '''
    
    # Ensure save path is clear
    save_path = check_save_path(save_path, overwrite)
    print(save_path)

    # collect binary information
    wdtype, samples, sampling_period, channels = process_header(file_path)

    # create header length (bytes) for processing
    if channels == 1:
        header_size = 24
    else:
        header_size = 28
    
    # Process data chunked or unchunked
    if counts == -1:
        print("No chunking selected...")
        # read in data
        with open(file_path, 'rb') as file:
            data = read_binary(file_path, wdtype)

        # format_data
        event_info, rwf = format_wfs(data, wdtype, samples, channels)

        # save data
        save_data(event_info, rwf, save_path, counts)
    else:
        print(f"Chunking by {counts}...")
        # collect data into dataframes based on desired splitting
        counter = 0
        while True:
            with open(file_path, 'rb') as file:
                # create offset equivalent to size of each chunk multiplied
                # by number of events already passed, and read data
                offset = (counter*samples*channels*4) + (header_size * counter) 
                data = read_binary(file_path, wdtype, counts, offset)

                # check binary has content in it
                if len(data) == 0:
                    print("Processing Finished!")
                    return True

                # format_data
                event_info, rwf = format_wfs(data, wdtype, samples, channels)

                # save data
                save_data(event_info, rwf, save_path, counter)
            counter += (counts)
