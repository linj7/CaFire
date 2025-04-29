import os
import tkinter
import customtkinter
from tkinter import ttk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from utils.file_utils import load_file
from utils.image_utils import load_svg_image
from ui.widgets import Tooltip, SegmentedProgressBar
from ui.window import set_window_style, set_window_icon
from core.event_handlers import handle_canvas_click

def setup_ui(app):
    """
    Set up the UI components for the main application window.
    
    Args:
        app: The main application instance
    """
    # Configure window properties
    app.title("CaFire by Lin - Dickman Lab")

        
    # Add window centering code
    screen_width = app.winfo_screenwidth()
    screen_height = app.winfo_screenheight()
    window_width = 700  # Set default window width
    window_height = 600  # Set default window height
    # Set window minimum size
    app.minsize(window_width, window_height)
    
    # Calculate the center position
    center_x = int((screen_width) / 2)
    center_y = int((screen_height) / 2)
    
    # Set window size and position
    app.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")

    app.grid_rowconfigure(0, weight=0)  # Menu bar
    app.grid_rowconfigure(1, weight=3)  # Canvas area
    app.grid_rowconfigure(2, weight=1)  # Table area
    app.grid_columnconfigure(0, weight=1)  # Main column expandable
    
    # Set window style
    set_window_style(app)
    
    # Create button frame
    setup_button_frame(app)
    
    # Create canvas frame
    setup_canvas_frame(app)
    
    # Create table frame
    setup_table_frame(app)
    
    # Set window icon
    setup_window_icon(app)
    
    # Bind navigation controls
    setup_navigation_controls(app)
    
def setup_button_frame(app):
    """Set up the top button frame with control buttons"""
    app.button_frame = customtkinter.CTkFrame(app)
    app.button_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
    
    # Load button icons
    app.load_file_icon = load_svg_image('assets/load_file.svg', width=24, height=24)
    app.load_file_icon_ctk = customtkinter.CTkImage(
        light_image=app.load_file_icon,
        dark_image=app.load_file_icon,
        size=(20, 20)
    )
    
    app.detect_peaks_icon = load_svg_image('assets/detect_peaks.svg', width=24, height=24)
    app.detect_peaks_icon_ctk = customtkinter.CTkImage(
        light_image=app.detect_peaks_icon,
        dark_image=app.detect_peaks_icon,
        size=(20, 20)
    )
    
    app.partition_evoked_icon = load_svg_image('assets/partition_evoked.svg', width=24, height=24)
    app.partition_evoked_icon_ctk = customtkinter.CTkImage(
        light_image=app.partition_evoked_icon,
        dark_image=app.partition_evoked_icon,
        size=(20, 20)
    )
    
    # Create buttons
    app.load_file_button = customtkinter.CTkButton(
        app.button_frame,
        image=app.load_file_icon_ctk,
        compound="left",
        fg_color="transparent", 
        hover_color="#d5d9df",
        text="Load File",
        text_color="black",
        font=customtkinter.CTkFont(size=12, weight="bold"),
        command=lambda: load_file(app)
    )
    app.load_file_button.pack(side="left", padx=5, pady=5)
    
    app.detect_peaks_button = customtkinter.CTkButton(
        app.button_frame,
        image=app.detect_peaks_icon_ctk,
        compound="left",
        fg_color="transparent", 
        hover_color="#d5d9df",
        text="Detect Peaks",
        text_color="black",
        font=customtkinter.CTkFont(size=12, weight="bold"),
        command=app.detect_peaks
    )
    app.detect_peaks_button.pack(side="left", padx=5, pady=5)
    
    app.partition_evoked_button = customtkinter.CTkButton(
        app.button_frame,
        image=app.partition_evoked_icon_ctk,
        compound="left",
        fg_color="transparent", 
        hover_color="#d5d9df",
        text="Partition Evoked Data",
        text_color="black",
        font=customtkinter.CTkFont(size=12, weight="bold"),
        command=app.handle_partition
    )
    app.partition_evoked_button.pack(side="left", padx=5, pady=5)
    
    # Create progress bar
    app.progress_bar = SegmentedProgressBar(
        app.button_frame,
        segments=8,
        width=120,
        height=15
    )
    app.progress_bar.pack(side="right", padx=20)

def setup_canvas_frame(app):
    """Set up the canvas frame with matplotlib figure and navigation controls"""
    # Create canvas frame
    app.canvas_frame = customtkinter.CTkFrame(app)
    app.canvas_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
    app.canvas_frame.grid_rowconfigure(0, weight=1)
    app.canvas_frame.grid_columnconfigure(0, weight=1)
    
    # Create matplotlib figure
    app.fig, app.ax = plt.subplots()
    app.canvas = FigureCanvasTkAgg(app.fig, master=app.canvas_frame)
    app.canvas_widget = app.canvas.get_tk_widget()
    app.canvas_widget.grid(row=0, column=0, sticky="nsew")
    
    # Add mouse events
    app.canvas.mpl_connect('axes_enter_event', app.on_enter_axes)
    app.canvas.mpl_connect('axes_leave_event', app.on_leave_axes)
    app.canvas.mpl_connect('button_press_event', lambda event: handle_canvas_click(event, app))
    
    # Load navigation icons
    zoom_in_image = load_svg_image('assets/zoom_in.svg', width=24, height=24)
    zoom_out_image = load_svg_image('assets/zoom_out.svg', width=24, height=24)
    prev_page_image = load_svg_image('assets/prev_page.svg', width=24, height=24)
    next_page_image = load_svg_image('assets/next_page.svg', width=24, height=24)
    up_page_image = prev_page_image.rotate(-90, expand=True)
    down_page_image = next_page_image.rotate(-90, expand=True)
    
    # Create CTkImage objects
    app.zoom_in_image_normal = customtkinter.CTkImage(light_image=zoom_in_image, size=(24, 24))
    app.zoom_out_image_normal = customtkinter.CTkImage(light_image=zoom_out_image, size=(24, 24))
    app.prev_page_image_normal = customtkinter.CTkImage(light_image=prev_page_image, size=(24, 24))
    app.next_page_image_normal = customtkinter.CTkImage(light_image=next_page_image, size=(24, 24))
    app.up_page_image_normal = customtkinter.CTkImage(light_image=up_page_image, size=(24, 24))
    app.down_page_image_normal = customtkinter.CTkImage(light_image=down_page_image, size=(24, 24))
    
    # Set up navigation controls
    button_spacing = 40  # Vertical spacing between buttons
    center_offset = 20   # Center offset for pairing buttons
    
    # Create and place navigation controls
    # Zoom in X
    app.zoom_in_x_label = customtkinter.CTkLabel(
        app.canvas_widget,
        text="",
        image=app.zoom_in_image_normal,
        width=24,
        height=24
    )
    app.zoom_in_x_label.place(relx=0.5, rely=1.0, x=-50, y=-center_offset + 5, anchor='e')
    app.zoom_in_x_label.configure(cursor="hand2")
    
    # Zoom out X
    app.zoom_out_x_label = customtkinter.CTkLabel(
        app.canvas_widget,
        text="",
        image=app.zoom_out_image_normal,
        width=24,
        height=24
    )
    app.zoom_out_x_label.place(relx=0.5, rely=1.0, x=-20, y=-center_offset + 5, anchor='e')
    app.zoom_out_x_label.configure(cursor="hand2")
    
    # Zoom in Y
    app.zoom_in_y_label = customtkinter.CTkLabel(
        app.canvas_widget,
        text="",
        image=app.zoom_in_image_normal,
        width=24,
        height=24
    )
    app.zoom_in_y_label.place(relx=1.0, rely=0.5, x=-25, y=-center_offset - button_spacing, anchor='e')
    app.zoom_in_y_label.configure(cursor="hand2")
    
    # Zoom out Y
    app.zoom_out_y_label = customtkinter.CTkLabel(
        app.canvas_widget,
        text="",
        image=app.zoom_out_image_normal,
        width=24,
        height=24
    )
    app.zoom_out_y_label.place(relx=1.0, rely=0.5, x=-25, y=-center_offset, anchor='e')
    app.zoom_out_y_label.configure(cursor="hand2")
    
    # Previous page
    app.prev_page_label = customtkinter.CTkLabel(
        app.canvas_widget,
        text="",
        image=app.prev_page_image_normal,
        width=24,
        height=24
    )
    app.prev_page_label.place(relx=0.5, rely=1.0, x=60, y=-center_offset + 5, anchor='e')
    app.prev_page_label.configure(cursor="hand2")
    
    # Next page
    app.next_page_label = customtkinter.CTkLabel(
        app.canvas_widget,
        text="",
        image=app.next_page_image_normal,
        width=24,
        height=24
    )
    app.next_page_label.place(relx=0.5, rely=1.0, x=90, y=-center_offset + 5, anchor='e')
    app.next_page_label.configure(cursor="hand2")
    
    # Up
    app.up_page_label = customtkinter.CTkLabel(
        app.canvas_widget,
        text="",
        image=app.up_page_image_normal,
        width=24,
        height=24
    )
    app.up_page_label.place(relx=1.0, rely=0.5, x=-25, y=center_offset, anchor='e')
    app.up_page_label.configure(cursor="hand2")
    
    # Down
    app.down_page_label = customtkinter.CTkLabel(
        app.canvas_widget,
        text="",
        image=app.down_page_image_normal,
        width=24,
        height=24
    )
    app.down_page_label.place(relx=1.0, rely=0.5, x=-25, y=center_offset + button_spacing, anchor='e')
    app.down_page_label.configure(cursor="hand2")

def setup_table_frame(app):
    """Set up the table frame with treeview and control buttons"""
    # Create table frame
    app.table_frame = customtkinter.CTkFrame(app)
    app.table_frame.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
    app.table_frame.configure(fg_color="transparent")
    
    # Create table button frame
    app.table_button_frame = customtkinter.CTkFrame(app.table_frame)
    app.table_button_frame.pack(side="left", fill="y", padx=5)
    app.table_button_frame.configure(fg_color="transparent")
    
    # Load button icons
    app.select_all_icon = load_svg_image('assets/select_all.svg', width=24, height=24)
    app.select_all_icon_ctk = customtkinter.CTkImage(
        light_image=app.select_all_icon,
        dark_image=app.select_all_icon,
        size=(20, 20)
    )
    
    app.copy_icon = load_svg_image('assets/copy.svg', width=24, height=24)
    app.copy_icon_ctk = customtkinter.CTkImage(
        light_image=app.copy_icon,
        dark_image=app.copy_icon,
        size=(20, 20)
    )
    
    app.export_icon = load_svg_image('assets/export.svg', width=24, height=24)
    app.export_icon_ctk = customtkinter.CTkImage(
        light_image=app.export_icon,
        dark_image=app.export_icon,
        size=(20, 20)
    )
    
    # Create table operation buttons
    app.select_all_button = customtkinter.CTkButton(
        app.table_button_frame,
        image=app.select_all_icon_ctk,
        text="",
        compound="left",
        fg_color="transparent", 
        hover_color="#d5d9df",
        width=24,
        height=24,
        command=app.select_all_rows,
    )
    app.select_all_button.pack(pady=5)
    Tooltip(app.select_all_button, "Select all rows")
    
    app.copy_button = customtkinter.CTkButton(
        app.table_button_frame,
        image=app.copy_icon_ctk,
        text="",
        compound="left",
        fg_color="transparent", 
        hover_color="#d5d9df",
        width=24,
        height=24,
        command=app.copy_selected_data
    )
    app.copy_button.pack(pady=5)
    Tooltip(app.copy_button, "Copy Selected")
    
    app.export_button = customtkinter.CTkButton(
        app.table_button_frame,
        image=app.export_icon_ctk,
        text="",
        compound="left",
        fg_color="transparent", 
        hover_color="#d5d9df",
        width=24,
        height=24,
        command=app.export_selected_data
    )
    app.export_button.pack(pady=5)
    Tooltip(app.export_button, "Export Selected")
    
    # Create tree frame
    app.tree_frame = customtkinter.CTkFrame(app.table_frame)
    app.tree_frame.pack(side="left", fill="both", expand=True)
    
    # Create treeview
    app.tree = ttk.Treeview(
        app.tree_frame,
        columns=("Time", "ΔF/F", "τ (rise)", "τ (decay)", "Baseline"),
        show="tree headings",
        height=8,
        selectmode="extended"
    )
    
    for col in app.tree["columns"]:
        app.tree.heading(col, text=col)
        app.tree.column(col, width=100, anchor="center")
    
    # Set tree column width
    app.tree.column("#0", width=40, stretch=False)
    
    # Create checkbox images
    app.unchecked_image = app.get_checkbox_image(False)
    app.checked_image = app.get_checkbox_image(True)
    
    # Bind events
    app.tree.bind('<Button-1>', app.handle_tree_click)
    app.tree.bind('<Button-3>', app.handle_tree_right_click)
    
    # Create context menu
    app.context_menu = tkinter.Menu(app, tearoff=0, font=("tahoma", 15, "normal"))
    app.context_menu.add_command(label="recalculate", command=app.recalculate_column)
    
    # Create scrollbar
    scrollbar = ttk.Scrollbar(app.table_frame, orient="vertical", command=app.tree.yview)
    app.tree.configure(yscrollcommand=scrollbar.set)
    
    # Place treeview and scrollbar
    app.tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Set treeview style
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview", rowheight=25, font=('Helvetica', 14))
    style.configure(
        "Treeview.Heading", 
        font=('Segoe UI', 14, 'bold')
    )
    
    # Add selected cell style
    app.tree.tag_configure("selected_cell", background="#CCE8FF")

def setup_window_icon(app):
    """Set up the window icon"""
    app.icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets/ecg_icon.ico')
    if os.path.exists(app.icon_path):
        app.iconbitmap(app.icon_path)

def setup_navigation_controls(app):
    """Bind events to navigation controls"""
    app.zoom_in_x_label.bind("<Button-1>", lambda event: app.on_button_press(app.zoom_in_x_label))
    app.zoom_in_x_label.bind("<ButtonRelease-1>", lambda event: app.on_button_release(app.zoom_in_x_label, app.zoom_in_x))
    
    app.zoom_out_x_label.bind("<Button-1>", lambda event: app.on_button_press(app.zoom_out_x_label))
    app.zoom_out_x_label.bind("<ButtonRelease-1>", lambda event: app.on_button_release(app.zoom_out_x_label, app.zoom_out_x))
    
    app.zoom_in_y_label.bind("<Button-1>", lambda event: app.on_button_press(app.zoom_in_y_label))
    app.zoom_in_y_label.bind("<ButtonRelease-1>", lambda event: app.on_button_release(app.zoom_in_y_label, app.zoom_in_y))
    
    app.zoom_out_y_label.bind("<Button-1>", lambda event: app.on_button_press(app.zoom_out_y_label))
    app.zoom_out_y_label.bind("<ButtonRelease-1>", lambda event: app.on_button_release(app.zoom_out_y_label, app.zoom_out_y))
    
    app.prev_page_label.bind("<Button-1>", lambda event: app.on_button_press(app.prev_page_label))
    app.prev_page_label.bind("<ButtonRelease-1>", lambda event: app.on_button_release(app.prev_page_label, app.prev_page))
    
    app.next_page_label.bind("<Button-1>", lambda event: app.on_button_press(app.next_page_label))
    app.next_page_label.bind("<ButtonRelease-1>", lambda event: app.on_button_release(app.next_page_label, app.next_page))
    
    app.up_page_label.bind("<Button-1>", lambda event: app.on_button_press(app.up_page_label))
    app.up_page_label.bind("<ButtonRelease-1>", lambda event: app.on_button_release(app.up_page_label, app.move_up))
    
    app.down_page_label.bind("<Button-1>", lambda event: app.on_button_press(app.down_page_label))
    app.down_page_label.bind("<ButtonRelease-1>", lambda event: app.on_button_release(app.down_page_label, app.move_down))