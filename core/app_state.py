def initialize_data_state(app):
    """
    Initialize data-related state variables
    
    Args:
        app: Main application instance
    """
    app.time = None
    app.df_f = None
    app.raw_values = None
    app.raw_baseline = None
    app.baseline_values = None
    app.convert_to_df_f = False

def initialize_ui_elements(app):
    """
    Initialize UI element states
    
    Args:
        app: Main application instance
    """
    app.points = []
    app.texts = []
    app.marked_peaks = []
    app.decay_lines = []
    app.rise_lines = []
    app.baseline_line = None
    app.partition_lines = []
    app.partition_labels = []
    app.rise_start_markers = {}  

def initialize_calculation_state(app):
    """
    Initialize calculation result storage
    
    Args:
        app: Main application instance
    """
    app.decay_calculated = [] 
    app.rise_calculated = [] 
    app.decay_line_map = {} 
    app.rise_line_map = {}
    app.rise_times = {}  
    app.tau_values = {}  
    app.amplitudes = {} 

def initialize_parameters(app):
    """
    Initialize parameter settings
    
    Args:
        app: Main application instance
    """
    app.peak_num = None
    app.window_size = None
    app.click_window_size = None
    app.baseline_window_size = None
    app.baseline_percentage = None
    app.manual_select_peak_threshold = None
    app.evoked_status = None

def initialize_last_used_values(app):
    """
    Initialize last used parameter values
    
    Args:
        app: Main application instance
    """
    app.last_sheet_name = ""
    app.last_x_col = ""
    app.last_y_col = ""
    app.last_RFP_col = ""
    app.last_baseline_window_size = ""
    app.last_baseline_percentage = ""
    app.last_peak_threshold = ""
    app.last_min_distance = ""
    app.last_peak_onset_window = ""
    app.last_peak_num = "" 
    app.last_interval_size = ""
    app.last_offset = ""
    app.last_width = ""  

def initialize_app_state(app):
    """
    Initialize all application states
    
    Args:
        app: Main application instance
    """
    initialize_data_state(app)
    initialize_ui_elements(app)
    initialize_calculation_state(app)
    initialize_parameters(app)
    initialize_last_used_values(app)

def clear_plot(app, reset_data=False):
    """
    Clear all elements on the plot and optionally reset the data state
    
    Args:
        app: Main application instance
        reset_data: Whether to reset the data state
    """
    for point in app.points:
        if point in app.ax.lines:
            point.remove()
    app.points = []
    
    for text in app.texts:
        if text in app.ax.texts:
            text.remove()
    app.texts = []
    
    app.marked_peaks = []
    
    for line in app.decay_lines:
        if line in app.ax.lines:
            line.remove()
    app.decay_lines = []
    app.decay_calculated = []
    app.decay_line_map = {}
    
    for line in app.rise_lines:
        if line in app.ax.lines:
            line.remove()
    app.rise_lines = []
    app.rise_calculated = []
    app.rise_line_map = {}
    app.rise_times = {}
    app.tau_values = {}
    app.amplitudes = {}
    
    for key in list(app.rise_start_markers.keys()):
        marker = app.rise_start_markers[key]
        if marker in app.ax.lines:
            marker.remove()
    app.rise_start_markers = {}
    
    if app.baseline_line is not None and app.baseline_line in app.ax.lines:
        app.baseline_line.remove()
    app.baseline_line = None
    
    for line in app.partition_lines:
        if line in app.ax.lines:
            line.remove()
    app.partition_lines = []
    
    for label in app.partition_labels:
        if label in app.ax.texts:
            label.remove()
    app.partition_labels = []
    
    if hasattr(app, 'tree') and app.tree is not None:
        for item in app.tree.get_children():
            app.tree.delete(item)
    
    if reset_data:
        app.time = None
        app.df_f = None
        app.raw_values = None
        app.raw_baseline = None
        app.baseline_values = None
        app.baseline_window_size = None
        app.baseline_percentage = None
        app.peak_num = None
        app.click_window_size = None
        if hasattr(app, 'evoked_var') and app.evoked_var is not None:
            app.evoked_var.set("off")
    
    if hasattr(app, 'canvas') and app.canvas is not None:
        app.canvas.draw()