import numpy as np
from tkinter import messagebox
from scipy.optimize import curve_fit

def decay_function(t, tau, y0):
    """
    Natural Logarithm of Decay Formula. y = y0 * e^{-t/tau}
    """
    return y0 * np.exp(-t / tau)

def calculate_decay(app, single_peak=None, no_draw=False):
    total_peaks = len(app.marked_peaks)

    # Sort marked peaks by time
    app.marked_peaks = sorted(app.marked_peaks, key=lambda peak: peak[0])

    # If a single peak is provided, only calculate decay for that peak
    if single_peak:
        peak_index = app.marked_peaks.index(single_peak)
        peaks_to_process = [(peak_index, single_peak)]
    else:
        peaks_to_process = list(enumerate(app.marked_peaks))

    # Calculate the standard deviation range of the baseline
    baseline_mean = np.mean(app.baseline_values)
    baseline_std = np.std(app.baseline_values)
    peak_values = [peak[1] for peak in app.marked_peaks]
    mean_peak_value = np.mean(peak_values)
    ratio = (mean_peak_value - baseline_mean) / baseline_std
    if (ratio <= 5):
        baseline_upper = baseline_mean
    elif (ratio > 5 and ratio <= 10):
        baseline_upper = baseline_mean + baseline_std
    else:
        baseline_upper = baseline_mean + 2 * baseline_std
    baseline_range = (baseline_mean - 2 * baseline_std, baseline_upper)

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
        t_data = app.time[current_peak_index:min_index_between_peaks + 1].values
        t_data_range = t_data - t_data[0]  # Make time start from 0
        y_data_original = np.array(app.df_f[current_peak_index:min_index_between_peaks + 1])
        
        # Ensure initial value is valid
        y0 = y_data_original[0]
        if np.isnan(y0) or y0 == 0:
            y0 = 0.001

        # Fit decay function
        try:
            # Calculate scaling factors for normalization
            t_scale = t_data_range.max()
            y_scale = np.max(y_data_original) - np.min(y_data_original)
            if y_scale < 0.01:
                y_scale = 0.01
                
            # Normalize both time and y data
            t_norm = t_data_range / t_scale
            y_data_norm = y_data_original / y_scale
            y0_norm = y0 / y_scale
            
            # Fit using normalized data
            popt, _ = curve_fit(
                lambda t, tau_norm: decay_function(t * t_scale, tau_norm * t_scale, y0_norm),
                t_norm,
                y_data_norm,
                p0=[0.5],
                bounds=(0.0001, np.inf)
            )
            
            # Convert normalized tau back to real scale
            tau_fitted = popt[0] * t_scale
            
            # Generate fitting curve using real time scale
            t_fit = np.linspace(0, t_data_range[-1], 100)
            y_fit_norm = decay_function(t_fit, tau_fitted, y0_norm)
            
            # Scale y values back to original magnitude
            y_fit = y_fit_norm * y_scale
            
            # Plot fitting curve
            decay_line, = app.ax.plot(
                t_data[0] + t_fit,  # Add back actual starting time
                y_fit,
                color='#FF00FF',
                linestyle='--'
            )
            
            app.decay_lines.append(decay_line)
            app.decay_line_map[(current_peak_time, current_peak_value)] = decay_line
            app.tau_values[(current_peak_time, current_peak_value)] = tau_fitted
            app.decay_calculated[i] = True

            # Update progress
            if not single_peak:
                progress = 0.7 + (0.3 * (i + 1) / total_peaks)
                app.progress_bar.set(progress)
                app.update()  # Force update GUI
            
            # 只有在不需要延迟绘图时才立即绘制
            if not no_draw:
                app.canvas.draw()
        except RuntimeError:
            messagebox.showwarning(title="Warning", message=f"Decay fitting failed for peak at {current_peak_time}.")
 
        if not no_draw:
            app.update_table()  # Update table