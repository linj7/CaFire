from tkinter import messagebox

def calculate_amplitude(app):
    if not app.marked_peaks:
        messagebox.showwarning(title="Warning", message="No peaks available for amplitude calculation.")
        return

    # Sort marked peaks by time
    app.marked_peaks = sorted(app.marked_peaks, key=lambda peak: peak[0])

    for i, (peak_time, peak_value) in enumerate(app.marked_peaks):
        peak_index = app.time[app.time == peak_time].index[0]

        # Evoked mode and current peak index is not an integer multiple of peak_num
        if app.evoked_var.get() == "on" and (i) % app.peak_num != 0:
            # Ensure there is a previous peak to calculate the fitted decay curve
            if i > 0:
                prev_peak_time, prev_peak_value = app.marked_peaks[i - 1]
                prev_peak_index = app.time[app.time == prev_peak_time].index[0]

                # Check if there is a previous decay curve
                if (prev_peak_time, prev_peak_value) in app.decay_line_map:
                    # Get the parameters of the previous peak's decay curve
                    prev_decay_line = app.decay_line_map[(prev_peak_time, prev_peak_value)]

                    # Decay function: 计算 decay curve 延伸到当前 peak 的值
                    t_data_range = peak_index - prev_peak_index
                    prev_tau = app.tau_values[(prev_peak_time, prev_peak_value)]
                    prev_y0 = prev_peak_value
                    decay_value = app.decay_function(t_data_range, prev_tau, prev_y0)

                    # Calculate the new amplitude
                    new_amplitude = peak_value - decay_value
                    app.amplitudes[(peak_time, peak_value)] = new_amplitude

                    print(f"Evoked on: Calculated amplitude for peak {i}, Value: {new_amplitude}")
                else:
                    print(f"Warning: No decay line found for peak {i - 1}. Skipping amplitude calculation.")
                    app.amplitudes[(peak_time, peak_value)] = None  
            else:
                print("Warning: First peak cannot calculate amplitude with evoked mode.")
                app.amplitudes[(peak_time, peak_value)] = None  
        else:
            # Non-Evoked mode or peak_num is an integer multiple, use default amplitude calculation
            app.amplitudes[(peak_time, peak_value)] = peak_value
            print(f"Default amplitude for peak {i}, Value: {peak_value}")

    messagebox.showinfo(title="Success", message="Amplitude calculation completed.")
