from ui.dialogs import DetectPeaksDialog
from core.app_state import clear_plot
from tkinter import messagebox
from scipy.signal import find_peaks

def apply_threshold(app):
    try:
        dialog = DetectPeaksDialog(
            app, 
            peak_threshold=app.last_peak_threshold,
            min_distance=app.last_min_distance,
            width=app.last_width,
            peak_onset_window=app.last_peak_onset_window
        )
        
        # Bind the main window destroy event
        def handle_destroy(event):
            if event.widget == app:
                dialog.user_cancelled = True
                dialog.destroy()
        
        app.bind('<Destroy>', handle_destroy)
        app.wait_window(dialog)
        app.unbind('<Destroy>')
        
        if dialog.user_cancelled or not hasattr(dialog, 'peak_threshold'):
            return

        if not dialog.user_cancelled:
            try:

                peak_threshold = float(dialog.peak_threshold)
                
                # Save user input parameters (including empty values)
                app.last_peak_threshold = dialog.peak_threshold
                app.last_min_distance = dialog.min_distance  # Save original input, not using default value
                app.last_width = dialog.width  # Save original input, not using default value
                app.last_peak_onset_window = dialog.peak_onset_window
                
                # Process optional parameters, set default values
                min_distance = float(dialog.min_distance) if dialog.min_distance else 4
                width = float(dialog.width) if dialog.width else 4

                # Clear previous points
                clear_plot(app, reset_data=False)

                # Redraw baseline when in "Load Raw Data" mode (i.e., not converted to ΔF/F or DR/R)
                if (not getattr(app, 'convert_to_df_f', False)) and hasattr(app, 'baseline_values') and app.baseline_values is not None:
                    # Remove residual references (set to None by clear_plot, just to be safe)
                    if hasattr(app, 'baseline_line') and app.baseline_line is not None:
                        try:
                            app.baseline_line.remove()
                        except Exception:
                            pass
                        app.baseline_line = None

                    # Redraw baseline
                    app.baseline_line, = app.ax.plot(app.time, app.baseline_values, color='deepskyblue', linestyle='--', linewidth=1.5, alpha=0.8, label='Baseline')
                    # Avoid duplicate legend: get existing labels and add as needed
                    handles, labels = app.ax.get_legend_handles_labels()
                    if 'Baseline' not in labels:
                        app.ax.legend(loc='best')
                    app.canvas.draw()

                # Build the parameter dictionary for find_peaks
                peak_params = {'height': peak_threshold}
                if dialog.min_distance:
                    peak_params['distance'] = min_distance
                if dialog.width:
                    peak_params['width'] = width

                # Find peaks with the provided parameters
                peaks, _ = find_peaks(app.df_f, **peak_params)
                total_peaks = len(peaks)

                # Update plot and table
                if peaks.size > 0:
                    app.marked_peaks = []  # Clear existing peaks
                    for i, peak_idx in enumerate(peaks):
                        x_peak = app.time.iloc[peak_idx]
                        y_peak = app.df_f.iloc[peak_idx]
                        point = app.ax.plot(x_peak, y_peak, 'ro')[0]
                        app.points.append(point)
                        app.marked_peaks.append((x_peak, y_peak))
                        app.decay_calculated.append(False)
                        app.rise_calculated.append(False)

                        # Update progress
                        progress = 0.4 * (i + 1) / total_peaks
                        app.progress_bar.set(progress)
                        app.update()
                
                    # Update table and canvas
                    app.update_table()
                    app.canvas.draw()

            except ValueError as e:
                messagebox.showerror(title="Error", message=str(e))
    except Exception as e:
        pass  # Ignore errors when closing