import io
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
from packs.core.core_utils import MalformedHeaderError, flatten
from packs.core.io         import writer
from packs.types import types

"""
Processing utilities

This file holds all the relevant functions for processing data from WaveDump 1/2 into
the h5 format.
"""




def raw_to_h5_WD1(PATH, save_h5 = False, verbose = False, print_mod = 0):
    '''
    **UNTESTED/DEPRECATED. BE AWARE THIS FUNCTION MAY NOT WORK AS DESIRED**

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

    # ensure you're using the right byteorder defined by your machine.
    # If you take the data from one machine to another of differing endianness,
    # you may have issues here!
    if byte_order == None:
        warnings.warn("Warning: No byte order provided. This may cause issues if transferring data between machines.")
        byte_order = sys.byteorder
    elif (byte_order != 'little') and (byte_order != 'big'):
        raise NameError(f'Invalid byte order provided: {byte_order}. Please provide the correct byte order for your machine.')

    # open file
    file = open(file_path, 'rb')

    event_number, timestamp, samples, sampling_period = read_defaults_WD2(file, byte_order)
    # attempt to read channels
    channels        = int.from_bytes(file.read(4), byteorder=byte_order)

    # then read in a full collection of data, and see if the following header makes sense.
    # if it explicitly breaks, assume 1 channel, raise a warning and continue.
    try:
        dataset         = file.read(4*samples*channels)
        event_number_1, timestamp_1, samples_1, sampling_period_1 = read_defaults_WD2(file, byte_order)
    except MemoryError as e:
        warnings.warn("process_header() unable to read file, defaulting to 1-channel description.\nIf this is not what you expect, please ensure your data was collected correctly.")
        event_number_1 = -1
        samples_1 = -1
        sampling_period_1 = -1

    # check that event header is as expected
    if (event_number_1 -1 == event_number) and (samples_1 == samples) and sampling_period_1 == (sampling_period):
        print(f"{channels} channels detected. Processing accordingly...")
    else:
        print(f"Single channel detected. If you're expecting more channels, something has gone wrong.\nProcessing accordingly...")
        channels = 1

    file.close()

    # this is a check to ensure that if you've screwed up the acquisition, it warns you adequately
    if samples == 0:
        raise RuntimeError(r"Unable to decode raw waveforms that have sample size zero. In wavedump 2, when collecting data from a single channel make sure that 'multiple channels per file' isn't checked.")

    # collect data types
    wdtype = types.generate_wfdtype(channels, samples)
    return wdtype, samples, sampling_period, channels


def read_binary(file    :  BinaryIO,
                wdtype  :  np.dtype,
                counts  :  Optional[int] = -1,
                offset  :  Optional[int] = 0) -> np.ndarray:
    '''
    Reads the binary in with the expected format/offset

    Parameters
    ----------

        file    (BufferedReader)  :  Opened file
        wdtype  (ndtype)         :  Custom data type for extracting information from
                                     binary files
        counts  (int)             :  How many events you want to read in. -1 sets it to take all events.
        offset  (int)             :  Offset at which to start reading the data. Used for chunking purposes
                                     and so should by default be set to zero if not chunking.

    Returns
    -------
        data  (ndarray)  :  Unformatted data from binary file

    '''
    # be aware, you're passing through the open file object
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
                                unformatted data
        samples   (int)      :  Number of samples in each waveform list
        channels  (int)      :  The first event number in the file (generally)

    Returns
    -------
        event_information (ndarray)  :  Reformatted event information
        waveform          (ndarray)  :  Reformatted waveforms

    '''
    # remove data component of dtype for event_information table
    e_dtype = types.event_info_type
    # if only one channel, select relevant information. Otherwise, split event by channel
    if channels == 1:
        event_information = [list(data[i])[:4] for i in range(len(data))]
        # add channel = 1 for each row
        [x.append(1) for x in event_information]
        waveform = [[(data[j][0], 0, list(data[j])[-i:][0]) for i in reversed(range(1, channels+1))] for j in range(len(data))]
    else:
        event_information = [list(data[i])[:5] for i in range(len(data))]
        waveform = [[(data[j][0], data[j][4] - i, list(data[j])[-i:][0]) for i in reversed(range(1, channels+1))] for j in range(len(data))]

    # convert to list of tuples and then structured numpy array
    event_information = list(map(tuple, event_information))
    event_information = np.array(event_information, dtype = e_dtype)
    waveform = np.array(flatten(waveform), dtype = types.rwf_type(samples))

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
    try:
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

    finally:
        # `finally` will always run regardless of what happens in the `try` case
        # even if an error occurs, so the file close is here to ensure no matter
        # what happens, the file doesn't stay open.
        h5f.close()



def check_save_path(save_path  :  str,
                    overwrite  :  Optional[bool] = True):
    '''
    Checks that the save_path is valid/doesn't already exist and if it does, other `overwrite` it
    or create an additional file with a number added.

    Parameters
    ----------

        save_path  (str)   :  Path to saved file
        overwrite  (bool)  :  Boolean for overwriting pre-existing files

    Returns
    -------
        save_path  (str)  :  Valid path to saved file, either unmodified or altered to add '_N'
                             where N is number of loops it had to do before finding a valid N

    '''

    name, ext = os.path.splitext(save_path)
    counter = 1

    if overwrite == False:
        while os.path.exists(save_path):
            save_path = name + str(counter) + ext
            counter += 1
            if counter > 100:
                raise RuntimeError("Writing to file went over 100 loops to find a unique name. Sort out your files!")

    return save_path


def process_event_lazy_WD1(file_object  :  BinaryIO,
                           sample_size  :  int):

    '''
    WAVEDUMP 1: Generator that outputs each event iteratively from an opened binary file

    Parameters
    ----------

        file_object  (obj)  :  Opened file object
        sample_size  (int)  :  Time difference between each sample in waveform (2ns for V1730B digitiser)

    Returns
    -------
        data  (generator)  :  Generator object containing one event's worth of data
                              across each event
    '''

    # read first header
    header = np.fromfile(file_object, dtype = 'i', count = 6)

    # header to check against
    sanity_header = header.copy()

    # continue only if data exists
    while len(header) > 0:

        # alter header to match expected size
        header[0] = header[0] - 24
        event_size = header[0] // sample_size

        # collect waveform, no of samples and timestamp
        yield (np.fromfile(file_object, dtype = np.dtype('<H'), count = event_size), event_size, header[-1])

        # collect next header
        header = np.fromfile(file_object, dtype = 'i', count = 6)

        # check if header has correct number of elements and correct information ONCE.
        if sanity_header is not None:
            if len(header) == 6:
                if all([header[0] == sanity_header[0], # event size
                    header[4] == sanity_header[4] + 1,  # event number +1
                    header[5] > sanity_header[5]        # timestamp increases
                    ]):
                    sanity_header = None
                else:
                    raise MalformedHeaderError(sanity_header, header)
            else:
                raise MalformedHeaderError(sanity_header, header)
    print("Processing Finished!")


def process_bin_WD1(file_path    :  str,
                    save_path    :  str,
                    sample_size  :  int,
                    overwrite    :  Optional[bool] = False,
                    counts       :  Optional[int] = -1,
                    print_mod    :  Optional[int] = -1):

    '''
    WAVEDUMP 1: Takes a binary file and outputs the containing information in a h5 file.
    This only works for individual channels at the moment, as wavedump 1 saves each channel
    as a separate file.

    For particularly large waveforms/number of events. You can 'chunk' the data such that
    each dataset holds `counts` events.

    # Makeup of the header (header[n]) where n is:
    # 0 - event size (ns in our case, with extra 24 samples)
    # 1 - board ID
    # 2 - pattern (not sure exactly what this means)
    # 3 - board channel
    # 4 - event counter
    # 5 - Time-tag for the trigger
    # Each of which is a signed 4byte integer


    Parameters
    ----------

        file_path    (str)   :  Path to binary file
        save_path    (str)   :  Path to saved file
        sample_size  (int)   :  Size of each sample in an event (2 ns in the case of V1730B digitiser)
        overwrite    (bool)  :  Boolean for overwriting pre-existing files
        counts       (int)   :  The number of events per chunks. -1 implies no chunking of data.


    Returns
    -------
        None
    '''


    # lets build it here first and break it up later
    # destroy the group within the file if you're overwriting
    save_path = check_save_path(save_path, overwrite)
    print(save_path)


    # open file for reading
    with open(file_path, 'rb') as file:

        # open writer object
        with writer(save_path, 'RAW', overwrite) as write:

            for i, (waveform, samples, timestamp) in enumerate(process_event_lazy_WD1(file, sample_size)):

                if (i % print_mod == 0) and (print_mod != -1):
                    print(f"Event {i}")

                # enforce stucture upon data
                e_dtype = types.event_info_type
                wf_dtype = types.rwf_type_WD1(samples)

                event_info = np.array((i, timestamp, samples, sample_size, 1), dtype = e_dtype)
                waveforms = np.array((i, 0, waveform), dtype = wf_dtype)


                # add data to df lazily
                write('event_info', event_info)
                write('rwf', waveforms)


def process_bin_WD2(file_path  :  str,
                    save_path  :  str,
                    overwrite  :  Optional[bool] = False,
                    counts     :  Optional[int]  = -1):

    '''
    WAVEDUMP 2: Takes a binary file and outputs the containing waveform information in a h5 file.

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
    print(f'\nData input   :  {file_path}\nData output  :  {save_path}')

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
            data = read_binary(file, wdtype)

        # format_data
        event_info, rwf = format_wfs(data, wdtype, samples, channels)

        # save data
        save_data(event_info, rwf, save_path)
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

