import numpy as np
from tkinter import messagebox
from scipy.signal import find_peaks
from core.calculate_decay import calculate_decay
from core.calculate_rise import calculate_rise

def handle_canvas_click(event, app):
    if app.time is None or app.df_f is None:
        messagebox.showwarning(title="Warning", message="No data loaded. Please load data before interacting with the plot.")
        return
    if event.inaxes == app.ax:
        if event.button == 1:  # Left click to add point
            # Get the window size from the input box, default to 5 if not provided
            if app.window_size is None:
                window_size = 5
            else:
                window_size = int(app.window_size)

            # Get the peak threshold from the input box, if provided
            if app.manual_select_peak_threshold is None:
                peak_threshold = None
            else:
                peak_threshold = float(app.manual_select_peak_threshold)

            # Find the nearest peak within a given window size
            x_clicked = event.xdata

            # Create a mask to find data points within the window
            window_mask = (app.time >= x_clicked - window_size) & (app.time <= x_clicked + window_size)
            window_time = app.time[window_mask]
            window_df_f = app.df_f[window_mask]
            if len(window_time) > 1:
                # Detect peaks within this subset, considering peak threshold if provided
                if peak_threshold is not None:
                    peaks, _ = find_peaks(window_df_f, height=peak_threshold)
                else:
                    peaks, _ = find_peaks(window_df_f)  # Adjust prominence based on data characteristics

                # If any peaks were found in the window
                if len(peaks) > 0:
                    # Find the index of the peak with the maximum y-value in this window
                    nearest_peak_idx = peaks[np.argmax(window_df_f.iloc[peaks])]
                    x_peak = window_time.iloc[nearest_peak_idx]
                    y_peak = window_df_f.iloc[nearest_peak_idx]

                    # Check if the peak is already marked
                    if (x_peak, y_peak) not in app.marked_peaks:
                        # Plot the peak without annotation
                        point, = app.ax.plot(x_peak, y_peak, 'ro')
                        app.points.append(point)
                        app.marked_peaks.append((x_peak, y_peak))
                        app.decay_calculated.append(False)
                        app.rise_calculated.append(False)

                        # Sort marked_peaks and synchronize other lists
                        sorted_data = sorted(zip(app.marked_peaks, app.points, app.decay_calculated, app.rise_calculated), key=lambda x: x[0][0])
                        app.marked_peaks, app.points, app.decay_calculated, app.rise_calculated = map(list, zip(*sorted_data))

                        # Calculate decay and rise for the newly added peak
                        calculate_decay(app, single_peak=(x_peak, y_peak))
                        calculate_rise(app, single_peak=(x_peak, y_peak))

                        app.canvas.draw()
                        app.update_table()  # Update table
                else:
                    messagebox.showinfo(title="Info", message="No peaks found within the window.")
            else:
                messagebox.showwarning(title="Warning", message="Window is too small or contains insufficient data.")

        elif event.button == 3:  # Right click to remove the nearest point
            if app.points:
                # Find the nearest point to the click
                x_clicked = event.xdata
                distances = [abs(point.get_xdata()[0] - x_clicked) for point in app.points]
                nearest_idx = np.argmin(distances)
                point = app.points.pop(nearest_idx)
                point.remove()
                peak = app.marked_peaks.pop(nearest_idx)
                # Remove corresponding decay line if exists
                if peak in app.decay_line_map:
                    decay_line = app.decay_line_map.pop(peak)
                    if decay_line in app.decay_lines:
                        app.decay_lines.remove(decay_line)
                    decay_line.remove()
                # Remove corresponding rise line if exists
                if peak in app.rise_line_map:
                    rise_line = app.rise_line_map.pop(peak)
                    if rise_line in app.rise_lines:
                        app.rise_lines.remove(rise_line)
                    rise_line.remove()
                    # Delete the corresponding rise start marker
                    if peak in app.rise_start_markers:
                        marker = app.rise_start_markers.pop(peak)
                        marker.remove()
                if peak in app.rise_times:
                    del app.rise_times[peak]
                if peak in app.tau_values:
                    del app.tau_values[peak]
                if peak in app.amplitudes:
                    del app.amplitudes[peak]
                app.decay_calculated.pop(nearest_idx)
                app.rise_calculated.pop(nearest_idx)
                app.canvas.draw()
                app.update_table()  # Update table