import numpy  as np
import pandas as pd
import matplotlib.pyplot as plt

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk

from packs.core.io import load_evt_info, load_rwf_info
from packs.proc.calibration_utils import subtract_baseline, collect_sidebands

def visualise_waveform(file_path     :  str,
                       vis_params    :  dict):
    """
    Launch an interactive Tkinter GUI for browsing raw waveforms from a file.

    Parameters
    ----------
    file_path : str
        Path to the data file. Used to load event/waveform info.
    vis_params : dict
        Visualisation options:
        - 'negative'     (bool) – invert the waveform amplitude.
        - 'baseline_sub' (str)  – method for determining baseline, 'median' or 'mean' 
    """
    # supporting functions
    # ---------------------------------------------------------------------------------
    def plot_waveform(wf_num    :   int):
        """Clear the axes and draw waveform wf_num with baseline subtraction applied."""
        ax.clear()
        single_wf = wf_rwf['rwf'][wf_num]
        if vis_params['negative']:
            single_wf = -single_wf

        sideband_values = collect_sidebands(single_wf, time, vis_params)
        single_wf = single_wf - subtract_baseline(sideband_values, sub_type = vis_params['baseline_sub'])
        ax.plot(time, single_wf,
                marker='o', markerfacecolor='None', linestyle='None', markersize=1)
        ax.set_title(f'Waveform #{wf_num}')
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('ADC')
        canvas.draw()
    
    def on_entry(event      : tk.Event | None = None):
        """Check and apply the waveform index, fixing the diagram to the valid range."""
        try:
            val = int(entry_var.get())
            val = max(0, min(val, max_wf))
            entry_var.set(val)
            slider_var.set(val)
            plot_waveform(val)
        except ValueError:
            pass
    
    def on_slider(value     : str | None = None):
        """Command for ttk.Scale. Sync the entry box to the slider position and redraw the selected waveform."""
        val = slider_var.get()
        entry_var.set(str(val))
        plot_waveform(val)
    # ---------------------------------------------------------------------------------
    
    filename = (file_path.rsplit('.')[1]).rsplit('/')[0]

    # load event + waveform info
    wf_evt = load_evt_info(file_path)
    samples = int(wf_evt.loc[0].samples)
    sampling_period = float(wf_evt.loc[0].sampling_period)
    wf_rwf = load_rwf_info(file_path, samples)
    print(f'file: {file_path}\nsamples: {samples}\nsampling_period: {sampling_period}')
    max_wf = len(wf_rwf['rwf']) - 1
    time = np.linspace(0,samples * sampling_period, num = samples)

    # init GUI 
    root = tk.Tk()
    root.title(f"Waveform Viewer — {filename}")

    # generate plot
    fig, ax = plt.subplots(layout='constrained', figsize=(8, 4))
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # controls frame
    ctrl = ttk.Frame(root, padding=8)
    ctrl.pack(fill=tk.X)

    ttk.Label(ctrl, text="Waveform #").pack(side=tk.LEFT)

    # number entry
    entry_var = tk.StringVar(value="0")

    # controls entry
    entry = ttk.Entry(ctrl, textvariable=entry_var, width=7)
    entry.pack(side=tk.LEFT, padx=4)
    entry.bind("<Return>", on_entry)
    entry.bind("<FocusOut>", on_entry)

    # slider
    slider_var = tk.IntVar(value=0)

    # controls slider
    slider = ttk.Scale(ctrl, from_=0, to=max_wf, orient=tk.HORIZONTAL,
                    variable=slider_var, command=on_slider, length=400)
    slider.pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True)

    ttk.Label(ctrl, text=f"(0 – {max_wf})").pack(side=tk.LEFT)

    # draw initial waveform
    plot_waveform(0)
    root.mainloop()