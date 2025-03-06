import numpy as np
from tkinter import messagebox

def calculate_baseline(app):
    if app.time is None or app.df_f is None:
        messagebox.showwarning(title="Warning", message="No data loaded.")
        return

    window_size = 50  # The size of the sliding window
    percentile = 30  # Use the 30th percentile as the baseline

    # Initialize baseline array
    app.baseline_values = np.zeros_like(app.df_f)

    # Calculate baseline for each point
    for i in range(len(app.df_f)):
        if i < window_size:  # If it's a point at the beginning, use the next points
            window = app.df_f[i:i+window_size]
        else:  # If it's a point at the end, use the previous points
            window = app.df_f[i-window_size:i]
        
        # Calculate the 30th percentile of the window as the baseline
        app.baseline_values[i] = np.percentile(window, percentile)

    mean_baseline = np.nanmean(app.baseline_values, axis=0)
    app.baseline_values = np.nan_to_num(app.baseline_values, nan=mean_baseline, posinf=mean_baseline, neginf=mean_baseline)

    # Remove previous baseline curve (if it exists)
    # if app.baseline_line is not None:
    #     app.baseline_line.remove()
    #     app.baseline_line = None

    # Draw baseline curve
    # app.baseline_line, = app.ax.plot(app.time, app.baseline_values, 'r--', label='Baseline')
    # app.ax.legend()
    # app.canvas.draw()
