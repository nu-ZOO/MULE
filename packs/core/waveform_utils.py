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

from tqdm import tqdm

"""
Waveform utilities

This file holds relevant functions for processing waveforms.
"""


def subtract_baseline(y_data : np.ndarray,
                       sub_type : Optional[str] = 'median') -> (float):
    '''
    determines the value that should be subtracted to produce baseline using the mean
    or median of a defined window of the waveform data
    '''

    # MEAN METHOD
    # add all ADC values and divide by length (rough), also remove negatives
    match sub_type:
        case 'mean':
            total = (np.sum(y_data)/len(y_data))

        case 'median':
            total = np.median(y_data)

        case _:
            print("Please input a baseline method, exiting...")
            total = 0

    return total

def find_nearest(array : np.ndarray,
                 value : float) -> (float):
    '''
    Finds the array value closest to the provided value
    '''
    idx = np.searchsorted(array, value, side="left")
    if idx > 0 and (idx == len(array) or m.fabs(value - array[idx-1]) < m.fabs(value - array[idx])):
        return array[idx-1]
    else:
        return array[idx]

def collect_index(time : np.ndarray,
                  value : float) -> (int):
    '''
    Collects the array index corresponding to a certain time value

    Args:
        time        (np.array)        :     Time array
        value       (float/int)       :     Value that you wish to locate the index of
    '''
    
    val = find_nearest(time, value)
    index = np.where(time == val)[0]

    if len(index == 1):
        return index[0]
    else:
        raise Exception("Index collection found more than one value with the same value entered.\nAre you sure you entered the right array?")
