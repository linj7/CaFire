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
            # Find the nearest peak within a given window size
            x_clicked = event.xdata

            user_window_size = None
            if hasattr(app, "click_window_size_entry"):
                raw_value = app.click_window_size_entry.get().strip()
                if raw_value:
                    try:
                        user_window_size = float(raw_value)
                        if user_window_size <= 0:
                            raise ValueError
                    except ValueError:
                        messagebox.showwarning(
                            title="Warning",
                            message="Window size must be a positive number."
                        )
                        user_window_size = None

            if user_window_size is not None:
                window_size = user_window_size
            else:
                # Fallback to default calculation when user input is absent or invalid
                time_range = app.time.max() - app.time.min()
                window_size = int(time_range * 0.0008)
                if window_size < 10:
                    window_size = 3
            print("window_size: ", window_size)
            window_mask = (app.time >= x_clicked - window_size) & (app.time <= x_clicked + window_size)
            window_time = app.time[window_mask]
            window_df_f = app.df_f[window_mask]
            if len(window_time) > 1:
                # Detect peaks within this subset, considering peak threshold if provided
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

                        # Find the index of the newly added peak in the sorted list
                        current_peak_index = app.marked_peaks.index((x_peak, y_peak))

                        if (app.evoked_status == "off"):
                            # If current peak is not the first peak, find previous peak and recalculate its decay
                            if current_peak_index > 0:
                                # Get the previous peak
                                prev_peak = app.marked_peaks[current_peak_index-1]
                                
                                # If previous peak has a decay line, remove it first
                                if prev_peak in app.decay_line_map:
                                    prev_decay_line = app.decay_line_map[prev_peak]
                                    if prev_decay_line in app.decay_lines:
                                        app.decay_lines.remove(prev_decay_line)
                                    prev_decay_line.remove()
                                    app.decay_line_map.pop(prev_peak)
                                
                                # Mark that previous peak's decay needs to be recalculated
                                app.decay_calculated[current_peak_index-1] = False
                                
                                # Recalculate decay for previous peak
                                calculate_decay(app, single_peak=prev_peak, no_draw=True)

                            # If current peak is not the last peak, find next peak and recalculate its rise
                            if current_peak_index < len(app.marked_peaks) - 1:
                                # Get next peak
                                next_peak = app.marked_peaks[current_peak_index+1]
                                
                                # If next peak has a rise line, remove it first
                                if next_peak in app.rise_line_map:
                                    next_rise_line = app.rise_line_map[next_peak]
                                    if next_rise_line in app.rise_lines:
                                        app.rise_lines.remove(next_rise_line)
                                    next_rise_line.remove()
                                    app.rise_line_map.pop(next_peak)
                                
                                # If next peak has a rise start marker, remove it first
                                if next_peak in app.rise_start_markers:
                                    next_rise_marker = app.rise_start_markers[next_peak]
                                    next_rise_marker.remove()
                                    app.rise_start_markers.pop(next_peak)
                                
                                # Remove from rise_times if it exists
                                if next_peak in app.rise_times:
                                    del app.rise_times[next_peak]
                                
                                # Mark next peak's rise needs to be recalculated
                                app.rise_calculated[current_peak_index+1] = False
                                
                                # Recalculate next peak's rise
                                calculate_rise(app, single_peak=next_peak, no_draw=True)

                        # Calculate decay and rise for the newly added peak
                        calculate_decay(app, single_peak=(x_peak, y_peak), no_draw=True)
                        calculate_rise(app, single_peak=(x_peak, y_peak), no_draw=True)

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
                peak_to_remove = app.marked_peaks[nearest_idx]

                # To recalculate the decay of the previous peak, we need to determine the position of the current peak in the time sequence
                # Get all peaks and sort them by time
                sorted_peaks = sorted(app.marked_peaks, key=lambda x: x[0])
                current_position = sorted_peaks.index(peak_to_remove)
                
                # Find the previous peak (if it exists)
                prev_peak = None
                if current_position > 0:
                    prev_peak = sorted_peaks[current_position - 1]
                
                # Find the next peak (if it exists)
                next_peak = None
                if current_position < len(sorted_peaks) - 1:
                    next_peak = sorted_peaks[current_position + 1]

                # Now perform the deletion operation
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

                if (app.evoked_status == "off"):
                    
                    # If previous peak exists, recalculate its decay
                    if prev_peak and prev_peak in app.marked_peaks:
                        prev_peak_idx = app.marked_peaks.index(prev_peak)
                        
                        # If previous peak has a decay line, remove it first
                        if prev_peak in app.decay_line_map:
                            prev_decay_line = app.decay_line_map[prev_peak]
                            if prev_decay_line in app.decay_lines:
                                app.decay_lines.remove(prev_decay_line)
                            prev_decay_line.remove()
                            app.decay_line_map.pop(prev_peak)
                        
                        # Mark previous peak's decay needs to be recalculated
                        app.decay_calculated[prev_peak_idx] = False
                        
                        # Recalculate previous peak's decay
                        calculate_decay(app, single_peak=prev_peak, no_draw=True)
                    
                    # If next peak exists, recalculate its rise time
                    if next_peak and next_peak in app.marked_peaks:
                        next_peak_idx = app.marked_peaks.index(next_peak)
                        
                        # If next peak has a rise line, remove it first
                        if next_peak in app.rise_line_map:
                            next_rise_line = app.rise_line_map[next_peak]
                            if next_rise_line in app.rise_lines:
                                app.rise_lines.remove(next_rise_line)
                            next_rise_line.remove()
                            app.rise_line_map.pop(next_peak)
                        
                        # If next peak has a rise start marker, remove it first
                        if next_peak in app.rise_start_markers:
                            next_rise_marker = app.rise_start_markers[next_peak]
                            next_rise_marker.remove()
                            app.rise_start_markers.pop(next_peak)
                        
                        # Remove from rise_times if it exists
                        if next_peak in app.rise_times:
                            del app.rise_times[next_peak]
                        
                        # Mark next peak's rise needs to be recalculated
                        app.rise_calculated[next_peak_idx] = False
                        
                        # Recalculate next peak's rise
                        calculate_rise(app, single_peak=next_peak, no_draw=True)

                app.canvas.draw()
                app.update_table()  # Update table