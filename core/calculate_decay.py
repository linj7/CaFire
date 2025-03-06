# core/calculate_decay.py
import numpy as np
from scipy.optimize import curve_fit
from tkinter import messagebox
import matplotlib.pyplot as plt

def decay_function(t, tau, y0):
    """
    Natural Logarithm of Decay Formula. y = y0 * e^{-t/tau}
    """
    return y0 * np.exp(-t / tau)

def calculate_decay(app, single_peak=None):
    total_peaks = len(app.marked_peaks)

    # Sort marked peaks by time
    app.marked_peaks = sorted(app.marked_peaks, key=lambda peak: peak[0])

    # If a single peak is provided, only calculate decay for that peak
    if single_peak:
        peak_index = app.marked_peaks.index(single_peak)
        peaks_to_process = [(peak_index, single_peak)]
    else:
        peaks_to_process = list(enumerate(app.marked_peaks))

    for i, (current_peak_time, current_peak_value) in peaks_to_process:
        # Skip if decay has already been calculated for this peak
        if app.decay_calculated[i]:
            continue

        current_peak_index = app.time[app.time == current_peak_time].index[0]

        # Define next peak index if it exists
        if i + 1 < len(app.marked_peaks):
            next_peak_index = app.time[app.time == app.marked_peaks[i + 1][0]].index[0]
        else:
            next_peak_index = len(app.df_f)

        # Calculate the standard deviation range of the baseline
        baseline_mean = np.mean(app.baseline_values)
        baseline_std = np.std(app.baseline_values)
        baseline_range = (baseline_mean - 2 * baseline_std, baseline_mean + 2 * baseline_std)

        # Find the first point in the range between the current peak and the next peak that is in the baseline range
        search_range = app.df_f[current_peak_index:next_peak_index]
        baseline_points = np.where((search_range >= baseline_range[0]) & 
                                    (search_range <= baseline_range[1]))[0]
        
        if len(baseline_points) > 0:
            # Found a point in the baseline range, use the first point
            min_index_between_peaks = current_peak_index + baseline_points[0]
        else:
            # Not found a point in the baseline range, use the minimum value point
            min_index_between_peaks = np.argmin(search_range) + current_peak_index

        # Prepare data for fitting
        t_data = np.arange(current_peak_index, min_index_between_peaks + 1)
        y_data = app.df_f[current_peak_index:min_index_between_peaks + 1]
        y_data = np.array(y_data)
        y0 = y_data[0]
        t_data_range = t_data - current_peak_index

        # Fit decay function
        try:
            popt, pcov = curve_fit(lambda t, tau: decay_function(t, tau, y0), t_data_range, y_data, p0=[0.5], bounds=(0.001, np.inf))
            tau_fitted = popt[0]
            t_fit = t_data_range
            y_fit = decay_function(t_fit, tau_fitted, y0)
            decay_line, = app.ax.plot(app.time[current_peak_index:min_index_between_peaks + 1], y_fit, color='#FF00FF', linestyle='--')
            app.decay_lines.append(decay_line)
            app.decay_line_map[(current_peak_time, current_peak_value)] = decay_line
            app.tau_values[(current_peak_time, current_peak_value)] = tau_fitted
            app.decay_calculated[i] = True
            # Update progress
            if not single_peak:
                progress = 0.7 + (0.3 * (i + 1) / total_peaks)
                app.progress_bar.set(progress)
                app.update()  # Force update GUI
            app.canvas.draw()
        except RuntimeError:
            messagebox.showwarning(title="Warning", message=f"Decay fitting failed for peak at {current_peak_time}.")
    # messagebox.showinfo(title="Success", message="Decay time successfully calculated for all peaks.")
        
        app.update_table()  # Update table
