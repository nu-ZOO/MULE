import io
import sys
import os
import h5py
import argparse
import math   as m
import numpy  as np
import pandas as pd
import warnings
import matplotlib

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk

from packs.core.io import load_evt_info, load_rwf_info, reader, check_chunking
from packs.types import types
from packs.proc.waveform_utils import subtract_baseline, collect_sidebands

def visualise(
        file_path     :  str,
        vis_params   :  dict):
    
    filename = (file_path.rsplit('.')[1]).rsplit('/')[0]

    # Load event + waveform info
    wf_evt = load_evt_info(file_path)
    samples = int(wf_evt.loc[0].samples)
    wf_rwf = load_rwf_info(file_path, samples)
    print(' ... number of samples ... ', samples)

    max_wf = len(wf_rwf['rwf']) - 1

    # --- GUI setup ---
    root = tk.Tk()
    root.title(f"Waveform Viewer — {filename}")

    fig, ax = plt.subplots(layout='constrained', figsize=(8, 4))
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def plot_waveform(wf_num):
        ax.clear()
        single_wf = wf_rwf['rwf'][wf_num]
        if vis_params['negative']:
            single_wf = -single_wf

        # check if chunked for backwards compatibility
        chunked, keys, l_keys, e_keys = check_chunking(file_path)

        # extract relevant information from event info (assuming static)
        scout                                    = reader(file_path, 'event_information', e_keys[0])
        _, _, samples, sampling_period, channels = next(scout)
        del scout

        calibration_info_type = types.calibration_info_type
        wf_dtype              = types.rwf_type(samples)

        print(f'file: {file_path}\nsamples: {samples}\nsampling_period: {sampling_period}\nchannels: {channels}')

        time = np.linspace(0,samples * sampling_period, num = samples)

        sideband_values = collect_sidebands(single_wf, time, vis_params)
        single_wf = single_wf - subtract_baseline(sideband_values, sub_type = vis_params['baseline_sub'])
        ax.plot(time, single_wf,
                marker='o', markerfacecolor='None', linestyle='None', markersize=1)
        ax.set_title(f'Waveform #{wf_num}')
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('ADC')
        canvas.draw()

    # Controls frame
    ctrl = ttk.Frame(root, padding=8)
    ctrl.pack(fill=tk.X)

    ttk.Label(ctrl, text="Waveform #").pack(side=tk.LEFT)

    # Number entry
    entry_var = tk.StringVar(value="0")

    def on_entry(event=None):
        try:
            val = int(entry_var.get())
            val = max(0, min(val, max_wf))
            entry_var.set(val)
            slider_var.set(val)
            plot_waveform(val)
        except ValueError:
            pass

    entry = ttk.Entry(ctrl, textvariable=entry_var, width=7)
    entry.pack(side=tk.LEFT, padx=4)
    entry.bind("<Return>", on_entry)
    entry.bind("<FocusOut>", on_entry)

    # Slider
    slider_var = tk.IntVar(value=0)

    def on_slider(event=None):
        val = slider_var.get()
        entry_var.set(str(val))
        plot_waveform(val)

    slider = ttk.Scale(ctrl, from_=0, to=max_wf, orient=tk.HORIZONTAL,
                    variable=slider_var, command=on_slider, length=400)
    slider.pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True)

    ttk.Label(ctrl, text=f"(0 – {max_wf})").pack(side=tk.LEFT)

    # Draw initial waveform
    plot_waveform(0)
    root.mainloop()