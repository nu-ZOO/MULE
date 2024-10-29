"""
Processing utilities

This file holds all the relevant functions for processing data from WaveDump 1/2 into
the h5 format.
"""




def raw_to_h5_WD1():
    '''
    Takes binary files data files (.dat) produced using Wavedump 1
    and decodes them into waveforms, that are then inserted into 
    pandas dataframes.

    These dataframes can then be saved as h5 files for further use.

    Args:
        PATH        (str)       :       File path of interest
        save_h5     (bool)      :       Flag for saving data
        verbose     (bool)      :       Flag for outputting information
        print_mod   (int)       :       Print modifier

    Returns:
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



def raw_to_h5_WD2():
    '''
    
    '''