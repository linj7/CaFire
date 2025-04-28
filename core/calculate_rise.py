import numpy as np
from tkinter import messagebox
from scipy.optimize import curve_fit
from core.calculate_baseline import calculate_baseline

def rise_function(t, tau, y0_baseline):
    """
    Exponential growth: y = y0 x e^{t/tau}
    REF: https://www.graphpad.com/guides/prism/latest/curve-fitting/reg_exponential_growth.htm
    """
    return y0_baseline * np.exp(t / tau)


def calculate_rise(app, single_peak=None, no_draw=False):
    calculate_baseline(app)
    total_peaks = len(app.marked_peaks)

    # Sort marked peaks by time
    app.marked_peaks = sorted(app.marked_peaks, key=lambda peak: peak[0])

    if single_peak:
        peak_index = app.marked_peaks.index(single_peak)
        peaks_to_process = [(peak_index, single_peak)]
    else:
        peaks_to_process = list(enumerate(app.marked_peaks))

    peak_onset_window = int(app.last_peak_onset_window) if app.last_peak_onset_window else None
    peak_values = [peak[1] for peak in app.marked_peaks]
    mean_peak_value = np.mean(peak_values)
    baseline_mean = np.mean(app.baseline_values)
    baseline_std = np.std(app.baseline_values)
    baseline_lower = baseline_mean - 8 * baseline_std
    ratio = (mean_peak_value - baseline_mean) / baseline_std
    if (ratio <= 10):
        baseline_upper = baseline_mean
    else:
        baseline_upper = baseline_mean + 2 * baseline_std

    for i, (peak_time, peak_value) in peaks_to_process:
        if app.rise_calculated[i]:
            continue

        peak_index = app.time[app.time == peak_time].index[0]
        rise_start_index = None

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
        
        
        if (peak_onset_window is not None):
            # Find all local minima within the window
            local_mins = []
            for j in range(peak_index - peak_onset_window + 1, peak_index - 1):
                if app.df_f[j] < app.df_f[j-1] and app.df_f[j] < app.df_f[j+1]:
                    local_mins.append(j)
            
            # If local minima are found, select the index of the smallest value
            if local_mins:
                min_values = [app.df_f[idx] for idx in local_mins]
                rise_start_index = local_mins[np.argmin(min_values)]
            else:
                # If no local minima are found, use the minimum value point in the window
                rise_start_index = peak_index - peak_onset_window + np.argmin(app.df_f[peak_index - peak_onset_window:peak_index])

        rise_start_value = app.df_f[rise_start_index]
        app.baseline_values[peak_index] = rise_start_value

        # Prepare fitting data
        t_data = app.time[rise_start_index:peak_index + 1].values  # Use actual time values
        t_data_range = t_data - t_data[0]  # Make time start from 0
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
            # Ensure y0 is not 0, use a smaller value of 0.001
            y0 = max(y0_original, 0.001)

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
                lambda t, tau_norm: rise_function(t * t_scale, tau_norm * t_scale, y0_norm),
                t_norm,
                y_data_norm,
                p0=[0.5],
                bounds=(0.0001, np.inf)
            )

            # Convert normalized tau back to real scale
            tau_fitted = popt[0] * t_scale

            # Generate fitting curve using real time scale
            t_fit = np.linspace(0, t_data_range[-1], 100)
            y_fit_norm = rise_function(t_fit, tau_fitted, y0_norm)
            
            # Scale y values back to original magnitude
            y_fit = y_fit_norm * y_scale

            # Force the starting point to be equal
            if len(y_fit) > 0:
                y_fit[0] = app.df_f[rise_start_index]
                if is_negative_start:
                    y_fit[0] = app.df_f[rise_start_index] + offset
            
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
            
            # Add a Bezier curve to the peak
            if len(t_fit) > 0 and y_fit[-1] < peak_value:
                def bezier_curve(P0, P1, P2, num=30):
                    t = np.linspace(0, 1, num)
                    curve_x = (1-t)**2 * P0[0] + 2*(1-t)*t * P1[0] + t**2 * P2[0]
                    curve_y = (1-t)**2 * P0[1] + 2*(1-t)*t * P1[1] + t**2 * P2[1]
                    return curve_x, curve_y

                # The last point of the fitting curve
                P0 = (t_data[0] + t_fit[-1], y_fit[-1])
                # Control point - horizontal extension
                P1 = (peak_time, y_fit[-1])
                # Peak point
                P2 = (peak_time, peak_value)

                bx, by = bezier_curve(P0, P1, P2, num=20)
                
                # Ensure the Bezier curve is smoothly connected to the fitting curve
                # Remove the first point of the Bezier curve to avoid repetition
                bx = bx[1:]
                by = by[1:]
                
                # Combine the fitting curve and the Bezier curve
                combined_x = np.concatenate([t_data[0] + t_fit, bx])
                combined_y = np.concatenate([y_fit, by])
            else:
                combined_x = t_data[0] + t_fit
                combined_y = y_fit

            # Plot the combined rise curve
            rise_line, = app.ax.plot(
                combined_x,
                combined_y,
                color='#00FF00',
                linestyle='--'
            )
            app.rise_lines.append(rise_line)
            app.rise_line_map[(peak_time, peak_value)] = rise_line
            app.rise_times[(peak_time, peak_value)] = tau_fitted
            app.rise_calculated[i] = True
            
            # Update progress
            if not single_peak:
                progress = 0.4 + (0.3 * (i + 1) / total_peaks)
                app.progress_bar.set(progress)
                app.update()  # Force update GUI
            
            # Only draw immediately when not delaying
            if single_peak and not no_draw:
                app.canvas.draw()
                app.update_table()
                
        except (RuntimeError, ValueError) as e:
            # If the fitting fails, display a warning
            if single_peak:
                messagebox.showwarning(title="Warning", message=f"Rise fitting failed for peak at {peak_time}. Error: {str(e)}")
            else:
                return False

    if not single_peak:
        process_abnormal_tau_values(app)
        app.canvas.draw()
        app.update_table()
    
    if single_peak:
        process_abnormal_tau_values(app, single_peak)
        
    return True

# Define the function to process abnormal tau values
def process_abnormal_tau_values(app, single_peak=None):
    """Process abnormal tau values, use Bezier curve and 63.2% method to recalculate"""
    # Calculate the average and standard deviation of all valid tau values
    valid_taus = [tau for tau in app.rise_times.values() if isinstance(tau, (int, float))]
    if len(valid_taus) < 3:  # Ensure there are enough samples to calculate the standard deviation
        return
        
    tau_average = np.mean(valid_taus)
    tau_std = np.std(valid_taus)
    
    # Determine the peaks that need to be processed
    outlier_peaks = []
    if single_peak:
        # Only check if the current peak being processed is abnormal
        peak_time, peak_value = single_peak
        tau = app.rise_times.get((peak_time, peak_value))
        if isinstance(tau, (float, int)) and (tau < tau_average - 2*tau_std or tau > tau_average + 2*tau_std):
            outlier_peaks.append(single_peak)
    else:
        # Check all peaks
        for peak, tau in list(app.rise_times.items()):
            if isinstance(tau, (float, int)) and (tau < tau_average - 2*tau_std or tau > tau_average + 2*tau_std):
                outlier_peaks.append(peak)
    
    # Process each abnormal peak
    for peak in outlier_peaks:
        peak_time, peak_value = peak
        
        try:
            # Find the corresponding index
            i = app.marked_peaks.index(peak)
            peak_index = app.time[app.time == peak_time].index[0]
            
            # Find the rise start point of this peak
            rise_marker = app.rise_start_markers.get(peak)
            if rise_marker:
                rise_x_data = rise_marker.get_xdata()[0]
                rise_start_index = app.time[app.time == rise_x_data].index[0]
                
                # Delete the existing fitting line
                if peak in app.rise_line_map:
                    existing_line = app.rise_line_map[peak]
                    if existing_line in app.rise_lines:
                        app.rise_lines.remove(existing_line)
                    existing_line.remove()
                    app.rise_line_map.pop(peak)
                    
                # Prepare data
                t_data = app.time[rise_start_index:peak_index + 1].values
                y_data = app.df_f[rise_start_index:peak_index + 1].values
                
                # Use Bezier curve to connect onset and peak
                def bezier_curve_multi(points, num=100):
                    """Create a multi-point Bezier curve"""
                    n = len(points) - 1
                    t = np.linspace(0, 1, num)
                    curve_x = np.zeros(num)
                    curve_y = np.zeros(num)
                    
                    for i, point in enumerate(points):
                        # Calculate the Bernstein polynomial
                        binomial = np.math.comb(n, i)
                        curve_x += binomial * (1-t)**(n-i) * t**i * point[0]
                        curve_y += binomial * (1-t)**(n-i) * t**i * point[1]
                    
                    return curve_x, curve_y

                # Create control points
                control_points = []
                # Add the starting point
                control_points.append((t_data[0], y_data[0]))

                # Add control points between data points
                if len(t_data) > 2:
                    # Take several key points as control points
                    sample_indices = np.linspace(1, len(t_data) - 2, min(5, len(t_data) - 2)).astype(int)
                    for idx in sample_indices:
                        control_points.append((t_data[idx], y_data[idx]))

                # Add the ending point
                control_points.append((t_data[-1], y_data[-1]))

                # Generate the Bezier curve
                t_smooth, y_smooth = bezier_curve_multi(control_points, num=100)
                
                # Calculate the new tau value: use the 63.2% rise time method
                y0 = y_data[0]
                y_peak = y_data[-1]
                # Calculate the y value of the 63.2% point
                y63 = y0 + 0.632 * (y_peak - y0)
                
                # Find the first point on the smoothed Bezier curve that is greater than or equal to y63
                target_indices = np.where(y_smooth >= y63)[0]
                if len(target_indices) > 0:
                    target_idx = target_indices[0]
                    
                    # If it is not the first point and needs more accurate interpolation
                    if target_idx > 0:
                        # Find the two points before and after y63
                        t_before, y_before = t_smooth[target_idx-1], y_smooth[target_idx-1]
                        t_after, y_after = t_smooth[target_idx], y_smooth[target_idx]
                        
                        # Linear interpolation to find a more accurate t63
                        if y_after != y_before:  # Avoid division by zero
                            fraction = (y63 - y_before) / (y_after - y_before)
                            t63 = t_before + fraction * (t_after - t_before)
                        else:
                            t63 = t_after
                    else:
                        t63 = t_smooth[target_idx]
                        
                    tau_new = t63 - t_data[0]
                else:
                    # If no suitable point is found, use the default value
                    tau_new = 0.5 * (t_data[-1] - t_data[0])
                
                # Draw the new fitting curve
                new_line, = app.ax.plot(
                    t_smooth, 
                    y_smooth, 
                    color='#00FF00', 
                    linestyle='--'
                )
                
                # Update the application state
                app.rise_lines.append(new_line)
                app.rise_line_map[(peak_time, peak_value)] = new_line
                app.rise_times[(peak_time, peak_value)] = tau_new
                
        except (ValueError, IndexError) as e:
            print(f"Error reprocessing peak {peak}: {e}")
            continue
    
    # Update the canvas and table (only needed in single_peak mode)
    if single_peak:
        app.canvas.draw()
        app.update_table()
