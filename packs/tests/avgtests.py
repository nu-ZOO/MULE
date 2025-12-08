from packs.ana.analysis_utils import cook_data, suppress_baseline, average_waveforms, remove_secondaries
from packs.core.waveform_utils import collect_index, subtract_baseline, find_nearest
import numpy as np

time = np.array(1,2,3,4,5,6,7)
neg_wf_data = np.array(-1,-1,-1,-1,-1,-1,-1)
suppressing_data = np.array(1,4,2,10,11,11,11)
secondary_data = np.array(10,10,10,10,10,10,10)
subtraction_data = np.array(1,1,10)
window_args = {'WINDOW_START'     : 4e2,
    'WINDOW_END'       : 3e4,
    'BASELINE_POINT_1' : 1e6,
    'BASELINE_POINT_2' :  1.5e6,
    'BASELINE_RANGE_1'  : 40e3,
    'BASELINE_RANGE_2'  : 40e3}

def test_negatives(neg_wf_data):
    assert suppress_baseline(neg_wf_data,10) == 0

def test_remove_secondaries(secondary_data):
    assert remove_secondaries(secondary_data, 10, time, 1, 0, 3) == None

def test_suppression(suppressing_data):
    threshold = 10
    sup_data = suppress_baseline(suppressing_data, threshold)
    assert sup_data == np.array(0,0,0,10,11,11,11)

def test_subtraction(subtraction_data):
    assert subtract_baseline(subtraction_data, sub_type='mean') == 4
    assert subtract_baseline(subtraction_data, 'median') == 1

def test_collect_index(time):
    assert collect_index(time,2) == 1

def test_cook_data(neg_wf_data):
    assert cook_data(neg_wf_data,1,window_args,1,1,True, suppression_threshold=0) == np.array(1,1,1,1,1,1,1)
    assert cook_data(neg_wf_data,1,window_args,1,1,False, suppression_threshold=0) == neg_wf_data
