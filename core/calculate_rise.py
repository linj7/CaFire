# core/calculate_rise.py
import numpy as np
from scipy.optimize import curve_fit
from tkinter import messagebox
import matplotlib.pyplot as plt
from core.calculate_baseline import calculate_baseline


def rise_function(t, tau, y0_baseline):
    """
    Exponential growth: y = y0 x e^{t/tau}
    REF: https://www.graphpad.com/guides/prism/latest/curve-fitting/reg_exponential_growth.htm
    """
    return y0_baseline * np.exp(t / tau)


def calculate_rise(app, single_peak=None):
    calculate_baseline(app)
    total_peaks = len(app.marked_peaks)

    # Sort marked peaks by time
    app.marked_peaks = sorted(app.marked_peaks, key=lambda peak: peak[0])

    if single_peak:
        peak_index = app.marked_peaks.index(single_peak)
        peaks_to_process = [(peak_index, single_peak)]
    else:
        peaks_to_process = list(enumerate(app.marked_peaks))

    baseline_mean = np.mean(app.baseline_values)
    baseline_std = np.std(app.baseline_values)
    baseline_lower = baseline_mean - 8 * baseline_std
    baseline_upper = baseline_mean + 2 * baseline_std

    # Detect data magnitude
    data_range = np.max(app.df_f) - np.min(app.df_f)
    use_signal_amplification = data_range < 0.01

    for i, (peak_time, peak_value) in peaks_to_process:
        if app.rise_calculated[i]:
            continue

        peak_index = app.time[app.time == peak_time].index[0]
        rise_start_index = None
        rise_end_index = peak_index

        if rise_start_index is None:
            prev_peak_time, _ = app.marked_peaks[i - 1] if i > 0 else (None, None)
            prev_peak_index = app.time[app.time == prev_peak_time].index[0] if prev_peak_time is not None else 0
            search_start = prev_peak_index if i > 0 else 0
                
            # Check if there is any data point between the two peaks that is in the baseline range
            between_peaks_data = app.df_f[search_start:peak_index]
            points_near_baseline = np.any((between_peaks_data >= baseline_lower) & (between_peaks_data <= baseline_upper))

            if points_near_baseline: # If there is a data point in this range, find the local minimum
                # Find the local minimum from the current peak to the previous peak
                for j in range(peak_index - 1, search_start - 1, -1):
                    # Check if it is a local minimum
                    if j > 0 and j < len(app.df_f) - 1:
                        if app.df_f[j] < app.df_f[j - 1] and app.df_f[j] < app.df_f[j + 1]:
                            # Check if it is in the baseline range
                            if baseline_lower <= app.df_f[j] <= baseline_upper:
                                rise_start_index = j
                                break
                
                # If no suitable local minimum is found, find the first point in the baseline range
                if rise_start_index is None:
                    for j in range(peak_index - 1, search_start - 1, -1):
                        if baseline_lower <= app.df_f[j] <= baseline_upper:
                            rise_start_index = j
                            break
                    # If still not found, use the starting point of the search range
                    if rise_start_index is None:
                        rise_start_index = search_start
            else: # If there is no data point in this range  
                # Find the lowest point between the two peaks
                min_index = search_start + np.argmin(app.df_f[search_start:peak_index])
                # Check if the lowest point after that is greater than the current peak
                if app.df_f[min_index] < peak_value:
                    rise_start_index = min_index
                else:
                    # Delete the peak and its related data
                    if (peak_time, peak_value) in app.rise_start_markers:
                        app.rise_start_markers[(peak_time, peak_value)].remove()
                    if (peak_time, peak_value) in app.rise_line_map:
                        app.rise_line_map[(peak_time, peak_value)].remove()
                        app.rise_lines.remove(app.rise_line_map[(peak_time, peak_value)])
                    if (peak_time, peak_value) in app.decay_line_map:
                        app.decay_line_map[(peak_time, peak_value)].remove()
                        app.decay_lines.remove(app.decay_line_map[(peak_time, peak_value)])
                    app.points[i].remove()
                    app.points.pop(i)
                    app.marked_peaks.pop(i)
                    app.decay_calculated.pop(i)
                    app.rise_calculated.pop(i)
                    app.canvas.draw()
                    app.update_table()
                    continue

        rise_start_value = app.df_f[rise_start_index]
        app.baseline_values[peak_index] = rise_start_value

        # Prepare fitting data
        t_data = np.arange(rise_start_index, peak_index + 1)
        t_data_range = t_data - rise_start_index
        y_data_original = np.array(app.df_f[rise_start_index:peak_index + 1])
        
        # Handle the case where the starting point is 0, NaN, or negative
        start_value = y_data_original[0]
        
        # Check if the starting point is negative
        is_negative_start = start_value < 0
        
        # If the starting point is negative, shift the entire data sequence so that the starting point is a small positive value
        offset = 0
        if is_negative_start:
            offset = abs(start_value) + 0.001  # The offset is the absolute value of the negative value plus a small positive value
            y_data_original = y_data_original + offset
        # Handle the case where the starting point is 0 or NaN
        elif np.isnan(start_value) or start_value == 0:
            y_data_original[0] = 0.001
        
        y0_original = y_data_original[0]

        try:
            if use_signal_amplification:
                # Signal amplification processing
                # Detect data range
                data_range = np.max(y_data_original) - np.min(y_data_original)
                
                # Calculate the amplification factor - the goal is to amplify the data to the 0.1 magnitude
                scaling_factor = 1.0
                if data_range < 0.01:
                    scaling_factor = 0.1 / data_range
                
                # Amplify the data
                y_data_amplified = y_data_original * scaling_factor
                y0_amplified = y0_original * scaling_factor
                
                # Use the amplified data for fitting
                popt, _ = curve_fit(
                    lambda t, tau: rise_function(t, tau, y0_amplified), 
                    t_data_range, 
                    y_data_amplified, 
                    p0=[0.5], 
                    bounds=(0.0001, np.inf)  # Lower the lower limit to adapt to faster rise
                )
                
                # When drawing the fitting curve, you need to shrink the y value back to the original magnitude
                t_fit = np.linspace(0, t_data_range[-1], 100)
                y_fit_amplified = rise_function(t_fit, popt[0], y0_amplified)
                y_fit = y_fit_amplified / scaling_factor
            else:
                # Use the original method for fitting
                y0 = max(y0_original, 0.001)  # Ensure y0 is not 0, use a smaller value of 0.001
                
                popt, _ = curve_fit(
                    lambda t, tau: rise_function(t, tau, y0), 
                    t_data_range, 
                    y_data_original, 
                    p0=[0.5], 
                    bounds=(0.001, np.inf)  # Lower the lower limit to adapt to faster rise
                )
                
                # Draw the fitting curve
                t_fit = np.linspace(0, t_data_range[-1], 100)
                y_fit = rise_function(t_fit, popt[0], y0)
            
            # If there was an offset, now you need to shift the fitting result back
            if is_negative_start:
                y_fit = y_fit - offset
            
            # If it is a single peak, clear the rise marker before this peak
            if single_peak and (peak_time, peak_value) in app.rise_start_markers:
                app.rise_start_markers[(peak_time, peak_value)].remove()
                if (peak_time, peak_value) in app.rise_line_map:
                    app.rise_line_map[(peak_time, peak_value)].remove()
                    app.rise_lines.remove(app.rise_line_map[(peak_time, peak_value)])

            # Add rise start point marker
            rise_start_marker, = app.ax.plot(
                app.time[rise_start_index], 
                app.df_f[rise_start_index], 
                'gx'
            )
            app.rise_start_markers[(peak_time, peak_value)] = rise_start_marker

            # Limit the fitting curve to not exceed the peak value
            valid_indices = np.where(y_fit <= peak_value)[0]
            if len(valid_indices) > 0:
                t_fit = t_fit[valid_indices]
                y_fit = y_fit[valid_indices]

            rise_line, = app.ax.plot(
                app.time[rise_start_index] + t_fit, 
                y_fit, 
                color='#00FF00', 
                linestyle='--'
            )
            app.rise_lines.append(rise_line)
            app.rise_line_map[(peak_time, peak_value)] = rise_line
            app.rise_times[(peak_time, peak_value)] = popt[0]
            app.rise_calculated[i] = True
            
            # Update progress
            if not single_peak:
                progress = 0.4 + (0.3 * (i + 1) / total_peaks)
                app.progress_bar.set(progress)
                app.update()  # Force update GUI
            
            if single_peak:
                app.canvas.draw()
                app.update_table()
                
        except (RuntimeError, ValueError) as e:
            # If the fitting fails, display a warning
            if single_peak:
                messagebox.showwarning(title="Warning", message=f"Rise fitting failed for peak at {peak_time}. Error: {str(e)}")
            else:
                return False

    if not single_peak:
        app.canvas.draw()
        app.update_table()
    
    return True
