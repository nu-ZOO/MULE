import numpy as np
import pandas as pd
import os
from tqdm import tqdm
import csv
import re

"""
Processing utilities for the Lecroy oscilloscope

This file holds all the relevant functions for the processing of data from csv files to h5.
"""

def parse_lecroy_segmented(lines):
    # Line 1 has to have: Segments,1000,SegmentSize,5002
    segments = int(lines[1][1])
    seg_size = int(lines[1][3])
    
    # Line 2, header is: Segment,TrigTime,TimeSinceSegment1
    # Lines 3 to 3 + segments - 1 are header lines
    header_start = 3
    header_end = header_start + segments
    header_lines = lines[header_start:header_end]
    
    header_df = pd.DataFrame(header_lines, columns=["Segment", "TrigTime", "TimeSinceSegment1"])

    # Find the "Time,Ampl" line
    for i, line in enumerate(lines):
        if line[0].strip() == "Time":
            data_start = i + 1
            break
    else:
        raise ValueError("Time,Ampl line not found")

    # Read the data block (segments × segment size)
    raw_data = lines[data_start:]
    if len(raw_data) < segments * seg_size:
        print(f"Warning: expected {segments * seg_size} rows, got {len(raw_data)}")

    value_list = []
    for j in range(segments):
        segment_data = []
        for k in range(seg_size):
            x = j * seg_size + k
            if x >= len(raw_data): # x = line in the file
                segment_data.append(None)
            else:
                try:
                    value = float(raw_data[x][1])  # column 1 = Amplitude of signal
                    segment_data.append(value)
                except (ValueError, IndexError):
                    segment_data.append(None)
        value_list.append(segment_data)

    value_df = pd.DataFrame(value_list)
    return value_df, header_df
