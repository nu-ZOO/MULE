import io
import sys
import os
import math   as m
import numpy  as np
import tables as tb
import pandas as pd
import warnings
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm


import h5py

from typing import BinaryIO
from typing import Generic
from typing import Optional
from typing import Union
from typing import Tuple

from packs.core.io import writer, reader, check_chunking, check_rows
from packs.types import types
from packs.core.waveform_utils import collect_index, subtract_baseline

from tqdm import tqdm

"""
Calibration utilities

This file holds relevant functions for processing waveforms.
"""


def integrate(y_data):
    '''
    Collect the integral across an event by summing y components
    '''
    return np.sum(y_data)
    

def extract_peak(y_data) :
    '''
    Collects peak and index of peak in data.
    '''
    return (np.max(y_data), np.argmax(y_data))


def visualise_waveforms(file, cali_params, time, key):
    '''
    Visualise waveforms and ask the user if the sidebands
    and integration window are acceptable.
    '''
    for i, waveform in enumerate(reader(file, 'rwf', key, 'r+')):
        plt.plot(time, waveform['rwf'], alpha = 0.2, zorder = 1)
        if i > 100: # ensures minimal plotting
            break
    if cali_params['baseline_sub'] is not None:
        for i, band in enumerate(cali_params['sidebands']):
            plt.axvspan(band[0], band[1], alpha = 0.2, label = f'Baseline band {i}', zorder = 2)
    if cali_params['method'] == 'manual':
        plt.axvspan(cali_params['window'][0], cali_params['window'][1], color = 'red', alpha = 0.2, label = f'Integration window', zorder = 2)

    plt.legend()
    plt.xlabel('Time (ns)')
    plt.ylabel('Waveform signal (ADC)') 
    plt.show()
    # ask if the user is happy with these bands?
    response = input("Are the bands acceptable? [y/n]: ").strip().lower()
    if response not in ['y', 'yes']:
        print("Please reset the bands and process again")
        exit()


def collect_sidebands(wf, time, cali_params):
    '''
    extract the sideband components of the waveform
    '''
    sideband_values = []
    for i, band in enumerate(cali_params['sidebands']):
        # extract the baseline indexes from time and collect y values
        bl_range = [collect_index(time, band[0]), collect_index(time, band[1])]
        sideband_values.append(wf[bl_range[0]:bl_range[1]])

    return sideband_values


def collect_integration_window(time, cali_params, H_index):
    '''
    extract the integration window index of the waveform
    '''
    match cali_params['method']:
        case 'manual':
            start_index = collect_index(time, cali_params['window'][0])
            end_index   = collect_index(time, cali_params['window'][1])
        case 'height':
            start_index = collect_index(time, time[H_index] - cali_params['window'][0])
            end_index = collect_index(time, time[H_index] + cali_params['window'][1])
        case _:
            raise ValueError(f'{cali_params['method']} is not a valid integration method.')
    
    return (start_index, end_index)
        


def calibrate(file_path     :  str,
              cali_params   :  dict,
              save_path     :  Optional[Union[str, None]]                                     = None,
              overwrite     :  Optional[bool]                                                 = False,
              visualise     :  Optional[bool]                                                 = True):

    '''
    Writes relevant charge output for each channel, allowing for simple
    calibration to be applied to the resultant data.

    Initially, the charge, height and subtracted waveforms are returned.
    More may be added later.

    WARNING: This function wont work if you chunked the file in decoding.
             Chunking will be removed soon.

    Parameters
    ----------

        file_path     (str)                     :  Path to binary file
        cali_params   (dict)                    :  Dictionary describing the relevant parameters for integrating:
                                                        method  (str)              :  method of calibration:
                                                            manual - set a window and calibrate around it
                                                            height - set integration window based on highest peak
                                                                     (NOT IMPLEMENTED) 
                                                        window  (int, int)         :  window to integrate over if required (ns)
                                                                                      For height method, this is the distance
                                                                                      +- around the peak.
                                                        baseline_sub (str)         :  baseline subtraction flag and the method implemented:
                                                            median
                                                            mean
                                                        sidebands    ((int, int), 
                                                                      (int, int))  :  windows to extract a baseline over (ns)
                                                        negative     (bool)        :  glag for flipping the waveform
        save_path     (str)                     :  Path to save to if desired
        overwrite     (bool)                    :  Boolean for overwriting pre-existing datasets
        visualise     (bool)                    :  visualiser for the and signal extraction area

    '''
    # check if chunked for backwards compatibility
    chunked, keys, l_keys, e_keys = check_chunking(file_path)

    # check the number of rows for fixed_size calculations
    num_rows = 0
    if chunked:
        for key in keys:
            num_rows += check_rows(file_path, 'rwf', key)
    else:
        num_rows = check_rows(file_path, 'rwf', keys[0])

    # extract relevant information from event info (assuming static)
    scout                                    = reader(file_path, 'event_information', e_keys[0])
    _, _, samples, sampling_period, channels = next(scout)
    del scout

    calibration_info_type = types.calibration_info_type
    wf_dtype              = types.rwf_type(samples)

    print(f'file: {file_path}\nsamples: {samples}\nsampling_period: {sampling_period}\nchannels: {channels}')

    time = np.linspace(0,samples * sampling_period, num = samples) 

    # visualise the first 100 waveforms to ensure the sidebands are correct
    if visualise:
        visualise_waveforms(file_path, cali_params, time, keys[0])

    # ensure correct file path output
    if save_path is None:
        file = file_path
    else:
        file = save_path

    # process
    with writer(file, 'CALI', overwrite = True) as scribe:
        for key in tqdm(keys):
            for i, waveform in enumerate(reader(file_path, 'rwf', key, 'r+')):

                evt_num  = waveform['event_number']
                channels = waveform['channels']
                wf       = waveform['rwf']

                # flip the waveform
                if cali_params['negative']:
                    wf = -wf

                # baseline subtraction
                if cali_params['baseline_sub'] is not None:
                    sideband_values = collect_sidebands(wf, time, cali_params)
                    wf = wf - subtract_baseline(sideband_values, sub_type = cali_params['baseline_sub'])

                # extract height and its index
                H_val, H_index = extract_peak(wf)

                start_index, end_index = collect_integration_window(time, cali_params, H_index)
                Q_val = integrate(wf[start_index:end_index])

                # write with correct format
                info = np.array([(evt_num, channels, Q_val, H_val)], dtype = calibration_info_type)
                swf  = np.array((evt_num, channels, wf), dtype = wf_dtype)
                scribe('waveform_information', info, (True, num_rows, i))
                scribe('subwf-1', swf, (True, num_rows, i))
