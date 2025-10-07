import numpy as np
import matplotlib.pyplot as plt
import os
from packs.core.waveform_utils    import collect_index , subtract_baseline
from packs.core import io

"""
Analysis utilities

This file holds all the relevant functions for analysing data from h5 files.
"""

def remove_secondaries(threshold, wf_data, time, event_number, verbose, WINDOW_END, bin_size):
    '''
    Removes events with large secondary peaks

    Params:
    threshold (int)                 :                   amplitude cutoff for second peak rejection
    wf_data (array)                 :                   data of waveform
    time (array)                    :                   the x axis / time data for the waveform
    event_number (int)              :                   counter passed through to track events
    verbose (str)                   :                   0 for no info, 1 for ommitted event number, 2 for plots of rejected event
    WINDOW_END (float)              :                   end of the first signal
    bin_size (int)                  :                   spacing between time bins in ns
    
    Returns:
    wf_data (array)                 :                   none rejected waveform
    '''
    after_window_wf = wf_data[collect_index(time, WINDOW_END) : len(wf_data)-1]
    time_after = np.linspace(WINDOW_END, 2e6, num=len(after_window_wf), dtype=int) * bin_size # After WINDOW_END
        
    second_peak = np.max(after_window_wf)
    if second_peak > threshold:
        if verbose > 1: 
            plt.plot(time, wf_data)
            plt.xlabel('Time (ns)')
            plt.ylabel('ADCs')
            plt.yscale('log')
            plt.axhline(second_peak, 0, 2e5, c = 'r', ls = '--')
            plt.axvline(WINDOW_END, c = 'r', ls = '--')
            plt.title(f'Event {event_number} subtracted waveform')
            plt.show()
        print(f'Event {event_number} excluded due to large secondary peak')
        return None
    else:
        return wf_data
    

def suppress_baseline(wf_data, threshold):
    '''
    Supresses baseline values, anything below the threshold (including negatives from undershoot) gets set to zero

    Params:
    wf_data (array)                 :                   waveform data
    threshold (int)                 :                   upper cutoff for zero supression
    
    Returns:
    wf_data (array)                 :                   waveform data with suppressed baseline
    '''
    substitute = 0 # This is the zero we set to
    wf_data[wf_data < threshold] = substitute
    return wf_data

def cook_data(data, bin_size, window_args, chunk_size, chunk_number, negative=False, baseline_mode='median', verbose=1, peak_threshold=800
             ):
    '''
    Takes in data and outputs baseline subtracted, baseline suppressed, processed waveforms.

    Args:
        data          (np.array)      :       Waveform data
        bin_size      (float)         :       Size of time bins within data
        window_args   (dict)          :       Dictionary of window values for use in processing
        chunk_size    (int)           :       Size of the 'chunk' of waveform used to ease processing
        chunk_number  (int)           :       Number passed through to track iterations, acts as a label for the chunk
        negative      (bool)          :       Is the waveform negative?
        baseline_mode (string)        :       Mode of the baseline subtraction (median, mode, mean, etc.)
        verbose       (int)           :       Print info: 0 is nothing, 1 is barebones, 2 includes plots
        peak_threshold (float)        :        Threshold for removing peaks

    Returns:
        results(
            sub_data   (array)        :       Baseline subtracted waveforms
        )
    '''
        
    # Make zero values equal to 1
    threshold = 0
    # Unpack window arguments
    WINDOW_START     = window_args['WINDOW_START']
    WINDOW_END       = window_args['WINDOW_END']
    BASELINE_POINT_1 = window_args['BASELINE_POINT_1']
    BASELINE_POINT_2 = window_args['BASELINE_POINT_2']
    BASELINE_RANGE_1 = window_args['BASELINE_RANGE_1']
    BASELINE_RANGE_2 = window_args['BASELINE_RANGE_2']

    # Define the time array
    time = np.linspace(0, len(data[0]), num=len(data[0]), dtype=int) * bin_size

    sub_data = []
    
    
    for i, wf in enumerate(data):  # Process each waveform
        
        event_number = i + chunk_size * chunk_number
        # Make zero values equal to 1
        threshold = 0
        substitute = 1
        wf[wf <= threshold] = substitute
        # Negative flip
        if negative:
            wf = -wf

        # Plot for debugging (if verbose level is 2)
        if verbose > 1:
            plt.plot(time, wf)
            plt.axvspan(WINDOW_START, WINDOW_END, alpha=0.3, color='red', label='Signal window')
            plt.axvspan(BASELINE_POINT_1 - BASELINE_RANGE_1, BASELINE_POINT_1 + BASELINE_RANGE_1, alpha=0.3, color='blue', label='Baseline bands')
            plt.axvspan(BASELINE_POINT_2 - BASELINE_RANGE_2, BASELINE_POINT_2 + BASELINE_RANGE_2, alpha=0.3, color='blue')
            plt.xlabel('Time (us)')
            plt.ylabel('ADCs')
            plt.title(f'Event {i} waveform')
            plt.legend()
            plt.show()

        # ### Baseline subtraction ###
        # Collect the baselisune region data (sidebands)
        bl_range_1 = [collect_index(time, BASELINE_POINT_1 - BASELINE_RANGE_1), collect_index(time, BASELINE_POINT_1 + BASELINE_RANGE_1)]
        bl_range_2 = [collect_index(time, BASELINE_POINT_2 - BASELINE_RANGE_2), collect_index(time, BASELINE_POINT_2 + BASELINE_RANGE_2)]
        y_sideband = wf[bl_range_1[0]:bl_range_1[1]]
        y_sideband = list(y_sideband) + list(wf[bl_range_2[0]:bl_range_2[1]])

        # Subtract the baseline value from the waveform
        sub_wf = wf - subtract_baseline(y_sideband, sub_type=baseline_mode)
        
        # Suppress baseline
        sup_wf = suppress_baseline(sub_wf, 10)
        
        # Remove secondary alphas
        final_wf = remove_secondaries(peak_threshold, sup_wf, time, event_number, verbose, WINDOW_END, bin_size)
        if final_wf is None:
            continue
            
        sub_data.append(final_wf)
        
        if verbose > 1:
            # Plot subtracted waveform for debugging
            plt.plot(time, sub_wf)
            plt.xlabel('Time (us)')
            plt.ylabel('ADCs')
            plt.title(f'Event {i} subtracted waveform')
            plt.show()

    # Return subtracted waveforms
    return sub_data

def average_waveforms(files, bin_size, window_args, chunk_size = 5, negative=False, baseline_mode='median', verbose=1, peak_threshold=800):
    '''
    Averages waveforms

    Params:
    files (list of str)                 :                   list of h5 files contsaining waveform data
    bin_size (int)                      :                   time spacing between bins in ns
    window_args (array)                 :                   array of the 'windows' aka band for signal and baseline sidebands
    chunk_size (int)                    :                   size of data chunks for ease of processing
    negative (bool)                     :                   is the waveform negative in amplitude?
    baseline_mode (str)                 :                   method of baseline subtraction
    verbose (int)                       :                   amount of live infor wanted, 0 for none, 1 for words, 2 for plots
    peak_threshold (int)                :                   amplitude of secondary peaks rejected

    Returns:
    average_waveform (array)            :                   data for final average waveform
    '''

    # Variables to accumulate sum and count
    waveform_sum = None
    num_waveforms = 0
    chunk_number = 0
    # Loop through each file and process the waveforms in chunks
    for filepath in files:
        if os.path.exists(filepath):
            print(f"Processing file: {filepath}")

            x = io.load_rwf_info(filepath, samples=2)
            waveforms = x.rwf.values

            # Get the total number of waveforms in the current file
            total_waveforms = waveforms.shape[0]

            # Process the data in chunks to avoid memory overload, cooks data in chunks also
            for start_idx in range(0, total_waveforms, chunk_size):
                end_idx = min(start_idx + chunk_size, total_waveforms)
                waveform_chunk = waveforms[start_idx:end_idx]

                # Process the chunk, passing the event_number
                sub_wf_chunk = cook_data(
                    waveform_chunk, bin_size, window_args, chunk_size, chunk_number, negative, 
                    baseline_mode, verbose, peak_threshold
                )
            
                # Make the sum array with the shape of the first chunk of waveforms
                if waveform_sum is None:
                    waveform_sum = np.zeros_like(sub_wf_chunk[0], dtype=np.float64)
            
                # Add the chunk of waveforms to the running sum
                if len(sub_wf_chunk) == 0:
                    continue  # Skip this iteration
                waveform_sum += np.sum(sub_wf_chunk, axis=0)
            
                # Update the number of waveforms processed
                num_waveforms += len(sub_wf_chunk)
            
                chunk_number +=1
                
        else:
            print(f"File not found: {filepath}")

    # Average the waveforms (not sum anymore)
    average_waveform = waveform_sum / num_waveforms
    del x
    return average_waveform