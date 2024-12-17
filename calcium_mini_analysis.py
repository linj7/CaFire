import io
import os
import sys
import cairosvg
import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageEnhance
import tkinter
import customtkinter
from tkinter import filedialog, messagebox

# Set up CustomTkinter appearance
customtkinter.set_appearance_mode("System")  # Modes: "System", "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"

def load_svg_image(filename, width=None, height=None):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    svg_path = os.path.join(base_path, filename)
    
    # Read SVG file
    with open(svg_path, 'rb') as svg_file:
        svg_data = svg_file.read()

    # Convert SVG into PNG
    png_data = cairosvg.svg2png(bytestring=svg_data, output_width=width, output_height=height)

    # Load PNG data into PIL Image
    image = Image.open(io.BytesIO(png_data))

    return image

class LoadFileDialog(customtkinter.CTkToplevel):
    def __init__(self, parent, default_sheet_name="", default_x_col="", default_y_col=""):
        super().__init__(parent)
        self.title("Enter Fields")
        self.geometry("200x300")

        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        offset_x = 100  # Horizontal offset from parent window
        offset_y = 100  # Vertical offset from parent window
        self.geometry(f"+{parent_x + offset_x}+{parent_y + offset_y}")

        # Set default values from parameters
        self.sheet_name = default_sheet_name
        self.x_col = default_x_col
        self.y_col = default_y_col
        self.user_cancelled = False

        # Create labels and entry fields with pre-filled values
        self.label_sheet = customtkinter.CTkLabel(self, text="Enter sheet name:")
        self.label_sheet.pack(pady=(20, 0), padx=20)
        self.entry_sheet = customtkinter.CTkEntry(self, width=200)
        self.entry_sheet.insert(0, default_sheet_name)  # Pre-fill with last used value
        self.entry_sheet.pack(pady=(5, 10), padx=20)

        self.label_x_col = customtkinter.CTkLabel(self, text="Enter X column name:")
        self.label_x_col.pack(padx=20)
        self.entry_x_col = customtkinter.CTkEntry(self, width=200)
        self.entry_x_col.insert(0, default_x_col) 
        self.entry_x_col.pack(pady=(5, 10), padx=20)

        self.label_y_col = customtkinter.CTkLabel(self, text="Enter Y column name:")
        self.label_y_col.pack(padx=20)
        self.entry_y_col = customtkinter.CTkEntry(self, width=200)
        self.entry_y_col.insert(0, default_y_col)  
        self.entry_y_col.pack(pady=(5, 10), padx=20)

        self.confirm_button = customtkinter.CTkButton(self, text="Confirm", command=self.on_confirm)
        self.confirm_button.pack(pady=(10, 20))

        # Handle window close event
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_confirm(self):
        self.sheet_name = self.entry_sheet.get().strip()  
        self.x_col = self.entry_x_col.get().strip() 
        self.y_col = self.entry_y_col.get().strip() 
        if not self.sheet_name or not self.x_col or not self.y_col:
            messagebox.showwarning(title="Warning", message="All fields must be filled out.", parent=self)
            return
        self.grab_release()
        self.destroy()

    def on_close(self):
        self.user_cancelled = True
        self.grab_release()
        self.destroy()

class BaselineDialog(customtkinter.CTkToplevel):
    def __init__(self, parent, default_first_start="", default_first_end="",
                 default_second_start="", default_second_end=""):
        super().__init__(parent)
        self.title("Baseline Parameters")
        self.geometry("200x380") 

        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        offset_x = 100  # Horizontal offset from parent window
        offset_y = 100  # Vertical offset from parent window
        self.geometry(f"+{parent_x + offset_x}+{parent_y + offset_y}")

        # Center the dialog over the parent window
        self.transient(parent)
        self.grab_set()

        self.first_interval_start = None
        self.first_interval_end = None
        self.second_interval_start = None
        self.second_interval_end = None
        self.user_cancelled = False

        self.label_first_start = customtkinter.CTkLabel(self, text="First Interval Start Index:")
        self.label_first_start.pack(pady=(20, 0), padx=20)
        self.entry_first_start = customtkinter.CTkEntry(self)
        self.entry_first_start.insert(0, default_first_start)  # Pre-fill with default value
        self.entry_first_start.pack(pady=(5, 10), padx=20, fill="x")

        self.label_first_end = customtkinter.CTkLabel(self, text="First Interval End Index:")
        self.label_first_end.pack(padx=20)
        self.entry_first_end = customtkinter.CTkEntry(self)
        self.entry_first_end.insert(0, default_first_end)  
        self.entry_first_end.pack(pady=(5, 10), padx=20, fill="x")

        self.label_second_start = customtkinter.CTkLabel(self, text="Second Interval Start Index:")
        self.label_second_start.pack(padx=20)
        self.entry_second_start = customtkinter.CTkEntry(self)
        self.entry_second_start.insert(0, default_second_start) 
        self.entry_second_start.pack(pady=(5, 10), padx=20, fill="x")

        self.label_second_end = customtkinter.CTkLabel(self, text="Second Interval End Index:")
        self.label_second_end.pack(padx=20)
        self.entry_second_end = customtkinter.CTkEntry(self)
        self.entry_second_end.insert(0, default_second_end) 
        self.entry_second_end.pack(pady=(5, 10), padx=20, fill="x")

        self.calculate_button = customtkinter.CTkButton(self, text="Calculate", command=self.on_calculate)
        self.calculate_button.pack(pady=(10, 20))

        # Handle window close event
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Allow resizing
        self.resizable(True, True)

    def on_calculate(self):
        self.first_interval_start = self.entry_first_start.get()
        self.first_interval_end = self.entry_first_end.get()
        self.second_interval_start = self.entry_second_start.get()
        self.second_interval_end = self.entry_second_end.get()
        if (not self.first_interval_start or not self.first_interval_end or
            not self.second_interval_start or not self.second_interval_end):
            messagebox.showwarning(title="Warning", message="All fields must be filled out.", parent=self)
            return
        self.grab_release()
        self.destroy()

    def on_close(self):
        # When the user closes the dialog without confirming
        self.user_cancelled = True
        self.grab_release()
        self.destroy()

class SNRDialog(customtkinter.CTkToplevel):
    def __init__(self, parent, default_snr="3"):
        super().__init__(parent)
        self.title("Apply SNR")
        self.geometry("150x150") 

        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        offset_x = 100  # Horizontal offset from parent window
        offset_y = 100  # Vertical offset from parent window
        self.geometry(f"+{parent_x + offset_x}+{parent_y + offset_y}")

        # Center the dialog over the parent window
        self.transient(parent)
        self.grab_set()

        self.snr_threshold = None
        self.user_cancelled = False

        self.label_snr = customtkinter.CTkLabel(self, text="Enter SNR:")
        self.label_snr.pack(pady=(20, 0), padx=20)
        self.entry_snr = customtkinter.CTkEntry(self,width = 100)
        self.entry_snr.insert(0, default_snr)  # Pre-fill with default value
        self.entry_snr.pack(pady=(5, 10), padx=20)

        self.confirm_button = customtkinter.CTkButton(self, text="Confirm", command=self.on_confirm, width = 100)
        self.confirm_button.pack(pady=(10, 20), padx=20)

        # Handle window close event
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Allow resizing
        self.resizable(True, True)

    def on_confirm(self):
        self.snr_threshold = self.entry_snr.get()
        if not self.snr_threshold:
            messagebox.showwarning(title="Warning", message="Please enter an SNR threshold.", parent=self)
            return
        self.grab_release()
        self.destroy()

    def on_close(self):
        # When the user closes the dialog without confirming
        self.user_cancelled = True
        self.grab_release()
        self.destroy()

class ThresholdDialog(customtkinter.CTkToplevel):
    def __init__(self, parent, peak_threshold="", min_distance=""):
        super().__init__(parent)
        self.title("Apply Threshold")
        self.geometry("250x250")

        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        offset_x = 100  
        offset_y = 100 
        self.geometry(f"+{parent_x + offset_x}+{parent_y + offset_y}")

        # Center the dialog over the parent window
        self.transient(parent)
        self.grab_set()

        self.peak_threshold = None
        self.min_distance = None
        self.user_cancelled = False

        self.label_threshold = customtkinter.CTkLabel(self, text="Peak Threshold:")
        self.label_threshold.pack(pady=(20, 0), padx=20)
        self.entry_threshold = customtkinter.CTkEntry(self, width=150)
        self.entry_threshold.insert(0, peak_threshold)  # Pre-fill with last used value if provided
        self.entry_threshold.pack(pady=(5, 10), padx=20)

        self.label_distance = customtkinter.CTkLabel(self, text="Min Distance Between Peaks:")
        self.label_distance.pack(pady=(5, 0), padx=20)
        self.entry_distance = customtkinter.CTkEntry(self, width=150)
        self.entry_distance.insert(0, min_distance) 
        self.entry_distance.pack(pady=(5, 10), padx=20)

        self.confirm_button = customtkinter.CTkButton(self, text="Confirm", command=self.on_confirm, width=100)
        self.confirm_button.pack(pady=(10, 20), padx=20)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_confirm(self):
        self.peak_threshold = self.entry_threshold.get()
        self.min_distance = self.entry_distance.get()

        if not self.peak_threshold or not self.min_distance:
            messagebox.showwarning(title="Warning", message="Both fields must be filled out.", parent=self)
            return
        self.grab_release()
        self.destroy()

    def on_close(self):
        self.user_cancelled = True
        self.grab_release()
        self.destroy()

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # Set window icon
        self.icon_path = os.path.join(os.path.dirname(__file__), 'assets/ecg_icon.ico')
        if os.path.exists(self.icon_path):
            self.iconbitmap(self.icon_path)

        self.title("Calcium Mini Analysis by Lin - Dickman Lab")
        self.geometry(f"{1200}x{700}")

        # Configure grid layout
        self.grid_columnconfigure(0, weight=0)  # Left sidebar
        self.grid_columnconfigure(1, weight=1)  # Plot area
        self.grid_rowconfigure(0, weight=1)

        # Create left sidebar frame with navigation widgets
        self.left_sidebar_frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="#ebebeb")
        self.left_sidebar_frame.grid(row=0, column=0, sticky="nsew")

        row_counter = 0
        width = 80

        # Load file button
        self.load_button = customtkinter.CTkButton(self.left_sidebar_frame, text="Load File", command=self.load_file)
        self.load_button.grid(row=row_counter, column=0, padx=10, pady=(20, 15), sticky="we")
        row_counter += 1

        separator = customtkinter.CTkFrame(self.left_sidebar_frame, height=2, width=width, fg_color="#DDDDDD")
        separator.grid(row=row_counter, column=0, sticky="we", padx=10)
        row_counter += 1

        # Find peaks label
        self.peak_area_label = customtkinter.CTkLabel(
            self.left_sidebar_frame,
            text="Find peaks",
            font=("Helvetica", 15, "bold"),  
            anchor="w"  
        )
        self.peak_area_label.grid(row=row_counter, column=0, padx=10, pady=(10, 0), sticky="w")
        row_counter += 1

        # Automatic label
        self.automatic_label = customtkinter.CTkLabel(
            self.left_sidebar_frame,
            text="Automatic",
            font=("Helvetica", 14), 
            anchor="w"  
        )
        self.automatic_label.grid(row=row_counter, column=0, padx=10, pady=(5, 0), sticky="w")
        row_counter += 1

        # Apply SNR button
        self.apply_snr_button = customtkinter.CTkButton(
            self.left_sidebar_frame, 
            text="Apply SNR",
            command=self.apply_snr
        )
        self.apply_snr_button.grid(row=row_counter, column=0, padx=10, pady=5, sticky="we")
        row_counter += 1

        # Apply Threshold button
        self.apply_threshold_button = customtkinter.CTkButton(
            self.left_sidebar_frame, 
            text="Apply Threshold",
            command=self.apply_threshold
        )
        self.apply_threshold_button.grid(row=row_counter, column=0, padx=10, pady=5, sticky="we")
        row_counter += 1

        # Manual label
        self.automatic_label = customtkinter.CTkLabel(
            self.left_sidebar_frame,
            text="Manual",
            font=("Helvetica", 14), 
            anchor="w"  
        )
        self.automatic_label.grid(row=row_counter, column=0, padx=10, pady=(5, 0), sticky="w")
        row_counter += 1

        # Window size label and entry
        self.window_size_label = customtkinter.CTkLabel(
            self.left_sidebar_frame,
            text="Window size",
            text_color="#b5b5b5",
            anchor="w"
        )
        self.window_size_label.grid(row=row_counter, column=0, padx=(10, 0), pady=5, sticky="w")

        self.window_size_entry = customtkinter.CTkEntry(
            self.left_sidebar_frame, 
            placeholder_text="default 5",
            width=80
        )
        self.window_size_entry.grid(row=row_counter, column=0, padx=(110, 10), pady=5, sticky="w")
        row_counter += 1

        # Peak threshold label and entry
        self.peak_threshold_label = customtkinter.CTkLabel(
            self.left_sidebar_frame,
            text="Peak threshold",
            text_color="#b5b5b5",
            anchor="w"
        )
        self.peak_threshold_label.grid(row=row_counter, column=0, padx=10, pady=(5, 15), sticky="w")

        self.peak_threshold_entry = customtkinter.CTkEntry(
            self.left_sidebar_frame, 
            width=80
        )
        self.peak_threshold_entry.grid(row=row_counter, column=0, padx=(110, 10), pady=(5, 15), sticky="w")
        row_counter += 1

        separator = customtkinter.CTkFrame(self.left_sidebar_frame, height=2, width=width, fg_color="#DDDDDD")
        separator.grid(row=row_counter, column=0, sticky="we", padx=10)
        row_counter += 1

        # Calculate baseline button
        self.calculate_baseline_button = customtkinter.CTkButton(self.left_sidebar_frame, text="Calculate Baseline",
                                                                 command=self.calculate_baseline)
        self.calculate_baseline_button.grid(row=row_counter, column=0, padx=10, pady=15, sticky="we")
        row_counter += 1

        separator = customtkinter.CTkFrame(self.left_sidebar_frame, height=2, width=width, fg_color="#DDDDDD")
        separator.grid(row=row_counter, column=0, sticky="we", padx=10)
        row_counter += 1

        # Calculate amplitude button
        self.calculate_amplitude_button = customtkinter.CTkButton(self.left_sidebar_frame, text="Calculate Amplitude",
                                                                  command=self.calculate_amplitude)
        self.calculate_amplitude_button.grid(row=row_counter, column=0, padx=10, pady=15, sticky="we")
        row_counter += 1

        separator = customtkinter.CTkFrame(self.left_sidebar_frame, height=2, width=width, fg_color="#DDDDDD")
        separator.grid(row=row_counter, column=0, sticky="we", padx=10)
        row_counter += 1

        # Calculate rise button
        self.calculate_rise_button = customtkinter.CTkButton(self.left_sidebar_frame, text="Calculate Rise",
                                                                  command=self.calculate_rise)
        self.calculate_rise_button.grid(row=row_counter, column=0, padx=10, pady=15, sticky="we")
        row_counter += 1

        separator = customtkinter.CTkFrame(self.left_sidebar_frame, height=2, width=width, fg_color="#DDDDDD")
        separator.grid(row=row_counter, column=0, sticky="we", padx=10)
        row_counter += 1

        self.left_sidebar_frame.columnconfigure(0, weight=1) 

        # Calculate decay button
        self.calculate_decay_button = customtkinter.CTkButton(self.left_sidebar_frame, text="Calculate Decay",
                                                              command=self.calculate_decay)
        self.calculate_decay_button.grid(row=row_counter, column=0, padx=10, pady=15, sticky="we")
        row_counter += 1

        separator = customtkinter.CTkFrame(self.left_sidebar_frame, height=2, width=width, fg_color="#DDDDDD")
        separator.grid(row=row_counter, column=0, sticky="we", padx=10)
        row_counter += 1

        # Export stats button
        self.export_button = customtkinter.CTkButton(self.left_sidebar_frame, text="Export Stats",
                                                     command=self.export_stats)
        self.export_button.grid(row=row_counter, column=0, padx=10, pady=15, sticky="we")
        row_counter += 1

        # Version label
        self.left_sidebar_frame.grid_rowconfigure(row_counter, weight=1)  # Push version label to bottom
        self.version_label = customtkinter.CTkLabel(self.left_sidebar_frame, text="v.1.0.2")
        self.version_label.grid(row=row_counter, column=0, padx=10, pady=10, sticky="se")
        
        # Create a frame for the canvas and overlay widgets
        self.canvas_frame = customtkinter.CTkFrame(self)
        self.canvas_frame.grid(row=0, column=1, padx=0, pady=20, sticky="nsew")
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)

        # Create a matplotlib figure and add it to the Tkinter window
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=0, column=0, sticky="nsew")

        # Load svg
        zoom_in_image = load_svg_image('assets/zoom_in.svg', width=24, height=24)
        zoom_out_image = load_svg_image('assets/zoom_out.svg', width=24, height=24)
        prev_page_image = load_svg_image('assets/prev_page.svg', width=24, height=24)
        next_page_image = load_svg_image('assets/next_page.svg', width=24, height=24)

        # Create CTkImage
        self.zoom_in_image_normal = customtkinter.CTkImage(light_image=zoom_in_image, size=(24, 24))
        self.zoom_out_image_normal = customtkinter.CTkImage(light_image=zoom_out_image, size=(24, 24))
        self.prev_page_image_normal = customtkinter.CTkImage(light_image=prev_page_image, size=(24, 24))
        self.next_page_image_normal = customtkinter.CTkImage(light_image=next_page_image, size=(24, 24))

        button_spacing = 40  # Vertical spacing between buttons
        center_offset = 20   # Center offset for pairing buttons

        # Zoom in label
        self.zoom_in_label = customtkinter.CTkLabel(
            self.canvas_widget,
            text="",
            image=self.zoom_in_image_normal,
            width=24,
            height=24
        )
        self.zoom_in_label.place(relx=1.0, rely=0.5, x=-25, y=-center_offset - button_spacing, anchor='e')
        self.zoom_in_label.configure(cursor="hand2")

        # Zoom out label
        self.zoom_out_label = customtkinter.CTkLabel(
            self.canvas_widget,
            text="",
            image=self.zoom_out_image_normal,
            width=24,
            height=24
        )
        self.zoom_out_label.place(relx=1.0, rely=0.5, x=-25, y=-center_offset, anchor='e')
        self.zoom_out_label.configure(cursor="hand2")

        # Previous page
        self.prev_page_label = customtkinter.CTkLabel(
            self.canvas_widget,
            text="",
            image=self.prev_page_image_normal,
            width=24,
            height=24
        )
        self.prev_page_label.place(relx=1.0, rely=0.5, x=-25, y=center_offset, anchor='e')
        self.prev_page_label.configure(cursor="hand2")

        # Next page
        self.next_page_label = customtkinter.CTkLabel(
            self.canvas_widget,
            text="",
            image=self.next_page_image_normal,
            width=24,
            height=24
        )
        self.next_page_label.place(relx=1.0, rely=0.5, x=-23, y=center_offset + button_spacing, anchor='e')
        self.next_page_label.configure(cursor="hand2")


        self.zoom_in_label.bind("<Button-1>", lambda event: self.on_button_press(self.zoom_in_label))
        self.zoom_in_label.bind("<ButtonRelease-1>", lambda event: self.on_button_release(self.zoom_in_label, self.zoom_in))

        self.zoom_out_label.bind("<Button-1>", lambda event: self.on_button_press(self.zoom_out_label))
        self.zoom_out_label.bind("<ButtonRelease-1>", lambda event: self.on_button_release(self.zoom_out_label, self.zoom_out))

        self.prev_page_label.bind("<Button-1>", lambda event: self.on_button_press(self.prev_page_label))
        self.prev_page_label.bind("<ButtonRelease-1>", lambda event: self.on_button_release(self.prev_page_label, self.prev_page))

        self.next_page_label.bind("<Button-1>", lambda event: self.on_button_press(self.next_page_label))
        self.next_page_label.bind("<ButtonRelease-1>", lambda event: self.on_button_release(self.next_page_label, self.next_page))

        self.time = None
        self.df_f = None
        self.points = []
        self.texts = []
        self.marked_peaks = []
        self.decay_lines = []
        self.decay_calculated = [] 
        self.decay_line_map = {} 
        self.rise_lines = []
        self.rise_calculated = [] 
        self.rise_line_map = {}
        self.rise_times = {}  
        self.tau_values = {}  
        self.amplitudes = {} 
        self.baseline_line = None
        self.baseline_values = None

        # Store last parameters
        self.last_sheet_name = ""
        self.last_x_col = ""
        self.last_y_col = ""
        self.last_snr_threshold = "3"
        self.last_peak_threshold = ""
        self.last_min_distance = ""
        self.last_first_interval_start = ""
        self.last_first_interval_end = ""
        self.last_second_interval_start = ""
        self.last_second_interval_end = ""

        self.canvas.mpl_connect('button_press_event', self.onclick)
    
    def on_button_press(self, label):
        # Simulate visual effect of pressed by moving label
        current_place_info = label.place_info()
        x = int(current_place_info['x'])
        y = int(current_place_info['y'])
        label.place_configure(x=x + 1, y=y + 1)

    def on_button_release(self, label, func):
        current_place_info = label.place_info()
        x = int(current_place_info['x'])
        y = int(current_place_info['y'])
        label.place_configure(x=x - 1, y=y - 1)
        func()  

    def load_file(self):
        # Create and show the input dialog with last used inputs
        load_file_dialog = LoadFileDialog(
            self,
            default_sheet_name=self.last_sheet_name,
            default_x_col=self.last_x_col,
            default_y_col=self.last_y_col
        )
        self.wait_window(load_file_dialog)  # Wait until the dialog is closed

        # Check if the user cancelled the operation
        if load_file_dialog.user_cancelled:
            return

        # Get the inputs from the dialog
        sheet_name = load_file_dialog.sheet_name
        x_col = load_file_dialog.x_col
        y_col = load_file_dialog.y_col

        if not sheet_name or not x_col or not y_col:
            messagebox.showwarning(title="Warning", message="All fields must be filled out.")
            return

        # Update the last used input values
        self.last_sheet_name = sheet_name
        self.last_x_col = x_col
        self.last_y_col = y_col

        # Use file dialog to select file
        file_path = filedialog.askopenfilename()

        if not file_path:
            messagebox.showwarning(title="Warning", message="No file selected.")
            return

        # Clear previous plot
        self.clear_plot()

        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
            self.time = df[x_col]
            self.df_f = df[y_col]
        except Exception as e:
            messagebox.showerror(title="Error", message=f"Error loading file: {e}")
            return

        self.ax.clear()
        self.ax.plot(self.time, self.df_f, color='blue')
        self.ax.set_ylim(np.min(self.df_f), np.max(self.df_f))
        self.ax.grid(True)
        self.canvas.draw()

    def apply_snr(self):
        if self.time is None or self.df_f is None:
            messagebox.showwarning(title="Warning", message="No data loaded.")
            return

        # Create and show the SNRDialog with default value
        snr_dialog = SNRDialog(self, default_snr=self.last_snr_threshold)
        self.wait_window(snr_dialog)  # Wait until the dialog is closed

        # Check if the user cancelled the operation
        if snr_dialog.user_cancelled:
            return

        # Get the SNR threshold from the input box
        try:
            snr_threshold = float(snr_dialog.snr_threshold)
            self.last_snr_threshold = snr_dialog.snr_threshold  # Store the last input
        except ValueError:
            messagebox.showwarning(title="Warning", message="Invalid SNR value.")
            return

        # Clear previous points, texts, and decay lines
        self.clear_plot(clear=True)

        # Signal-to-noise ratio (SNR) based peak detection
        noise_level = np.std(self.df_f)  # Estimate noise level using standard deviation of the signal

        # Find peaks
        peaks, properties = find_peaks(self.df_f, height=noise_level * snr_threshold)

        # Update the x-axis limits to ensure all detected peaks are within view
        if peaks.size > 0:
            min_peak_x = np.min(self.time.iloc[peaks])
            max_peak_x = np.max(self.time.iloc[peaks])
            current_xlim = self.ax.get_xlim()
            new_xlim = (min(current_xlim[0], min_peak_x), max(current_xlim[1], max_peak_x))
            self.ax.set_xlim(new_xlim)

        # Mark peaks on the plot
        xlims = self.ax.get_xlim()
        for peak in peaks:
            if xlims[0] <= self.time.iloc[peak] <= xlims[1]:  # Only plot peaks within the current view limits
                if (self.time.iloc[peak], self.df_f.iloc[peak]) not in self.marked_peaks:  # Avoid duplicate peaks
                    point, = self.ax.plot(self.time.iloc[peak], self.df_f.iloc[peak], 'ro')
                    text = self.ax.text(self.time.iloc[peak], self.df_f.iloc[peak],
                                        f'({self.time.iloc[peak]}, {self.df_f.iloc[peak]:.4f})', fontsize=8,
                                        color='red')
                    self.points.append(point)
                    self.texts.append(text)
                    self.marked_peaks.append((self.time.iloc[peak], self.df_f.iloc[peak]))
                    self.decay_calculated.append(False)
                    self.rise_calculated.append(False)
        self.marked_peaks.sort()
        self.canvas.draw()

    def apply_threshold(self):
        if self.time is None or self.df_f is None:
            messagebox.showwarning(title="Warning", message="No data loaded.")
            return

        # Show the ThresholdDialog with last used values
        threshold_dialog = ThresholdDialog(
            self,
            peak_threshold=self.last_peak_threshold,
            min_distance=self.last_min_distance
        )
        self.wait_window(threshold_dialog)  # Wait until the dialog is closed

        # Check if the user cancelled the operation
        if threshold_dialog.user_cancelled:
            return

        # Get the Peak threshold and Min distance from the input boxes
        try:
            peak_threshold = float(threshold_dialog.peak_threshold)
            min_distance = int(threshold_dialog.min_distance)
            # Update last used values
            self.last_peak_threshold = threshold_dialog.peak_threshold
            self.last_min_distance = threshold_dialog.min_distance
        except ValueError:
            messagebox.showwarning(title="Warning", message="Invalid values for threshold or distance.")
            return

        # Clear previous points, texts, and decay lines
        self.clear_plot(clear=True)

        # Find peaks with the provided threshold and distance
        peaks, _ = find_peaks(self.df_f, height=peak_threshold, distance=min_distance)

        # Update the x-axis limits to ensure all detected peaks are within view
        if peaks.size > 0:
            min_peak_x = np.min(self.time.iloc[peaks])
            max_peak_x = np.max(self.time.iloc[peaks])
            current_xlim = self.ax.get_xlim()
            new_xlim = (min(current_xlim[0], min_peak_x), max(current_xlim[1], max_peak_x))
            self.ax.set_xlim(new_xlim)

        # Mark peaks on the plot
        xlims = self.ax.get_xlim()
        for peak in peaks:
            if xlims[0] <= self.time.iloc[peak] <= xlims[1]:  # Only plot peaks within the current view limits
                if (self.time.iloc[peak], self.df_f.iloc[peak]) not in self.marked_peaks:  # Avoid duplicate peaks
                    point, = self.ax.plot(self.time.iloc[peak], self.df_f.iloc[peak], 'ro')
                    text = self.ax.text(self.time.iloc[peak], self.df_f.iloc[peak],
                                        f'({self.time.iloc[peak]}, {self.df_f.iloc[peak]:.4f})', fontsize=8,
                                        color='red')
                    self.points.append(point)
                    self.texts.append(text)
                    self.marked_peaks.append((self.time.iloc[peak], self.df_f.iloc[peak]))
                    self.decay_calculated.append(False)
                    self.rise_calculated.append(False)
        self.marked_peaks.sort()
        self.canvas.draw()

    @staticmethod
    def calculate_baseline_by_fitted_line(data_series, first_interval_start, first_interval_end, second_interval_start, second_interval_end):
        """
        Calculate baseline as a line connecting the average values of two specified intervals.
        """
        start_mean = np.mean(data_series[first_interval_start:first_interval_end])
        end_mean = np.mean(data_series[second_interval_start:second_interval_end])

        # Linear fit between two points: (0, start_mean) and (len(data_series) - 1, end_mean)
        x_values = np.array([0, len(data_series) - 1])
        y_values = np.array([start_mean, end_mean])

        # Calculate linear fit parameters
        a, b = np.polyfit(x_values, y_values, 1)

        # Calculate baseline values for each point in data_series
        baseline_values = a * np.arange(len(data_series)) + b
        
        return baseline_values

    def calculate_baseline(self):
        if self.time is None or self.df_f is None:
            messagebox.showwarning(title="Warning", message="No data loaded.")
            return

        # Create and show the BaselineDialog with default values
        baseline_dialog = BaselineDialog(
            self,
            default_first_start=self.last_first_interval_start,
            default_first_end=self.last_first_interval_end,
            default_second_start=self.last_second_interval_start,
            default_second_end=self.last_second_interval_end
        )
        self.wait_window(baseline_dialog)  # Wait until the dialog is closed

        # Check if the user cancelled the operation
        if baseline_dialog.user_cancelled:
            return

        # Get user input for intervals
        try:
            first_interval_start = int(baseline_dialog.first_interval_start)
            first_interval_end = int(baseline_dialog.first_interval_end)
            second_interval_start = int(baseline_dialog.second_interval_start)
            second_interval_end = int(baseline_dialog.second_interval_end)
        except ValueError:
            messagebox.showwarning(title="Warning", message="Invalid interval values.")
            return

        # Store the last inputs
        self.last_first_interval_start = baseline_dialog.first_interval_start
        self.last_first_interval_end = baseline_dialog.first_interval_end
        self.last_second_interval_start = baseline_dialog.second_interval_start
        self.last_second_interval_end = baseline_dialog.second_interval_end

        # Calculate baseline values
        self.baseline_values = self.calculate_baseline_by_fitted_line(
            self.df_f,
            first_interval_start,
            first_interval_end,
            second_interval_start,
            second_interval_end
        )

        # Clear previous baseline line if exists
        if self.baseline_line is not None:
            self.baseline_line.remove()

        self.baseline_line, = self.ax.plot(self.time, self.baseline_values, color='m')
        self.canvas.draw()

    def calculate_amplitude(self):
        if not self.marked_peaks:
            messagebox.showwarning(title="Warning", message="No peaks available for amplitude calculation.")
            return
        # if self.baseline_values is None:
        #     messagebox.showwarning(title="Warning", message="Baseline not calculated. Please calculate the baseline first.")
        #     return

        # Calculate amplitude for each marked peak
        # for peak in self.marked_peaks:
        #     peak_time, peak_value = peak
        #     peak_index = self.time[self.time == peak_time].index[0]
        #     baseline_value_at_peak = self.baseline_values[peak_index]
        #     amplitude = peak_value - baseline_value_at_peak
        #     self.amplitudes[peak] = amplitude

        messagebox.showinfo(title="Success", message="Amplitudes successfully calculated for all peaks.")

    def export_stats(self):
        if self.time is None or not self.marked_peaks:
            messagebox.showwarning(title="Warning", message="No stats to export.")
            return

        # Extract peak data (both automatically and manually marked)
        peak_times = [peak[0] for peak in self.marked_peaks]
        peak_values = [peak[1] for peak in self.marked_peaks]
        amplitude_values = [self.amplitudes.get(peak, None) for peak in self.marked_peaks]
        tau_values = [self.tau_values.get(peak, None) for peak in self.marked_peaks]
        rise_times = [self.rise_times.get(peak, None) for peak in self.marked_peaks] 

        # Create a DataFrame and sort by Time
        df_export = pd.DataFrame({
            "Time": peak_times,
            # "Peaks": peak_values,
            "Amplitude": peak_values,
            "Rise Time": rise_times,
            "Decay Time": tau_values
        })
        df_export = df_export.sort_values(by="Time")

        export_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if export_path:
            try:
                df_export.to_excel(export_path, index=False, engine='openpyxl')
                messagebox.showinfo(title="Success", message="Stats successfully exported.")
            except Exception as e:
                messagebox.showerror(title="Error", message=f"Error exporting stats: {e}")

    def calculate_decay(self):
        if not self.marked_peaks:
            messagebox.showwarning(title="Warning", message="No peaks available for decay calculation.")
            return

        # Sort marked peaks by time
        self.marked_peaks = sorted(self.marked_peaks, key=lambda peak: peak[0])

        for i, (current_peak_time, current_peak_value) in enumerate(self.marked_peaks):
            # Skip if decay has already been calculated for this peak
            if self.decay_calculated[i]:
                continue

            current_peak_index = self.time[self.time == current_peak_time].index[0]

            # Define next peak index if it exists and peaks are sufficiently close
            if i + 1 < len(self.marked_peaks):
                next_peak_index = self.time[self.time == self.marked_peaks[i + 1][0]].index[0]
                distance_between_peaks = next_peak_index - current_peak_index
                
                if distance_between_peaks > 50 or next_peak_index <= current_peak_index: # Check if peaks are too far apart
                    next_peak_index = None
            else:
                next_peak_index = None

            # print(f"Current_peak_index:{current_peak_index} and Next_peak_index:{next_peak_index}")

            # Determine min index between peaks or 20 points after the current peak
            if next_peak_index is None:
                min_index_between_peaks = current_peak_index + 20
                if min_index_between_peaks >= len(self.df_f):
                    min_index_between_peaks = len(self.df_f) - 1
            else:
                min_index_between_peaks = np.argmin(self.df_f[current_peak_index:next_peak_index]) + current_peak_index

            # Prepare data for fitting
            t_data = np.arange(current_peak_index, min_index_between_peaks + 1)
            y_data = self.df_f[current_peak_index:min_index_between_peaks + 1]
            y_data = np.array(y_data)
            y0 = y_data[0]
            t_data_range = t_data - current_peak_index

            # Fit decay function
            try:
                popt, pcov = curve_fit(lambda t, tau: self.decay_function(t, tau, y0), t_data_range, y_data, p0=[0.5], bounds=(0.001, np.inf))
                tau_fitted = popt[0]
                t_fit = t_data_range
                y_fit = self.decay_function(t_fit, tau_fitted, y0)
                decay_line, = self.ax.plot(self.time[current_peak_index:min_index_between_peaks + 1], y_fit, color='k', linestyle='--')
                self.decay_lines.append(decay_line)
                self.decay_line_map[(current_peak_time, current_peak_value)] = decay_line
                self.tau_values[(current_peak_time, current_peak_value)] = tau_fitted
                self.decay_calculated[i] = True
                self.canvas.draw()
            except RuntimeError:
                messagebox.showwarning(title="Warning", message=f"Decay fitting failed for peak at {current_peak_time}.")
        messagebox.showinfo(title="Success", message="Decay time successfully calculated for all peaks.")

    def calculate_rise(self):
        if self.time is None or self.df_f is None:
            messagebox.showwarning(title="Warning", message="No data loaded.")
            return

        # Sort marked peaks by time
        self.marked_peaks = sorted(self.marked_peaks, key=lambda peak: peak[0])

        for i, (peak_time, peak_value) in enumerate(self.marked_peaks):
            # Skip if rise has already been calculated for this peak
            if self.rise_calculated[i]:
                continue

            peak_index = self.time[self.time == peak_time].index[0]

            rise_start_index = None
            rise_end_index = peak_index

            # Search leftward from the peak to find the first local minimum as the initial rise start point
            for j in range(peak_index - 1, 0, -1):
                if self.df_f[j] < self.df_f[j - 1] and self.df_f[j] < self.df_f[j + 1]:
                    rise_start_index = j
                    break
            if rise_start_index is None:
                rise_start_index = 0  # If no local minimum is found, set it as the starting point of the data

            # Check if the identified rise_start_index meets the conditions; if not, continue searching
            while self.df_f[rise_start_index] >= 0.37 * peak_value and rise_start_index > 0:
                for j in range(rise_start_index - 1, 0, -1):
                    if self.df_f[j] < self.df_f[j - 1] and self.df_f[j] < self.df_f[j + 1]:
                        rise_start_index = j
                        break
                else:
                    break  # Exit if no new local minimum is found

            # Fit rise function
            interval_data = self.df_f
            t_data = np.arange(rise_start_index, peak_index + 1)
            t_data_range = t_data - rise_start_index
            y_data = interval_data[rise_start_index : peak_index + 1]
            y_data = np.array(y_data)  # Ensure y_data is a numpy array
            y0 = max(y_data[0], 0.01)

            try:
                popt, pcov = curve_fit(lambda t, tau: self.rise_function(t, tau, y0), t_data_range, y_data, p0=[0.5], bounds=(0.001, np.inf))
                tau_fitted = popt[0]
                t_fit = np.linspace(0, t_data_range[-1], 100)
                y_fit = self.rise_function(t_fit, tau_fitted, y0)
                rise_line, = self.ax.plot(self.time[rise_start_index] + t_fit, y_fit, 'r--', label=f'Rise Fit')   
                self.rise_lines.append(rise_line)
                self.rise_line_map[(peak_time, peak_value)] = rise_line
                self.rise_times[(peak_time, peak_value)] = tau_fitted
                self.rise_calculated[i] = True
            except RuntimeError:
                messagebox.showwarning(title="Warning", message=f"Rise fitting failed for peak at {peak_time}.")

        # Update the plot
        self.canvas.draw()
        messagebox.showinfo(title="Success", message="Rise time successfully calculated for all peaks.")
    
    def clear_plot(self, clear=False):
        for point, text in zip(self.points, self.texts):
            point.remove()
            text.remove()
        self.points.clear()
        self.texts.clear()
        self.marked_peaks.clear()
        self.decay_calculated.clear()
        self.rise_calculated.clear()
        if clear:
            for line in self.decay_lines:
                line.remove()
            self.decay_lines.clear()
            self.decay_line_map.clear()
            for line in self.rise_lines:
                line.remove()
            self.rise_lines.clear()
            self.rise_line_map.clear()
            self.rise_times.clear()
            self.tau_values.clear()
            self.amplitudes.clear()
        if self.baseline_line is not None:
            self.baseline_line.remove()
            self.baseline_line = None
        self.canvas.draw()

    @staticmethod
    def decay_function(t, tau, y0):
        """
        Natural Logarithm of Decay Formula. y = y0 * e^{-t/tau}
        """
        return y0 * np.exp(-t / tau)

    @staticmethod
    def rise_function(t, tau, y0_baseline):
        """
        Exponential growth: y = y0 x e^{t/tau}
        REF: https://www.graphpad.com/guides/prism/latest/curve-fitting/reg_exponential_growth.htm
        """
        return y0_baseline * np.exp(t / tau)

    def onclick(self, event):
        if self.time is None or self.df_f is None:
            messagebox.showwarning(title="Warning", message="No data loaded. Please load data before interacting with the plot.")
            return
        if event.inaxes == self.ax:
            if event.button == 1:  # Left click to add point
                # Get the window size from the input box, default to 5 if not provided
                try:
                    window_size = float(self.window_size_entry.get())
                except ValueError:
                    window_size = 5

                # Get the peak threshold from the input box, if provided
                try:
                    peak_threshold = float(self.peak_threshold_entry.get())
                except ValueError:
                    peak_threshold = None

                # Find the nearest peak within a given window size
                x_clicked = event.xdata

                # Create a mask to find data points within the window
                window_mask = (self.time >= x_clicked - window_size) & (self.time <= x_clicked + window_size)
                window_time = self.time[window_mask]
                window_df_f = self.df_f[window_mask]
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
                        if (x_peak, y_peak) not in self.marked_peaks:
                            # Plot and annotate the peak
                            point, = self.ax.plot(x_peak, y_peak, 'ro')
                            text = self.ax.text(x_peak, y_peak, f'({x_peak}, {y_peak:.4f})', fontsize=8, color='red')
                            self.points.append(point)
                            self.texts.append(text)
                            self.marked_peaks.append((x_peak, y_peak))
                            self.decay_calculated.append(False)
                            self.rise_calculated.append(False)

                            # Sort marked_peaks and synchronize other lists
                            sorted_data = sorted(zip(self.marked_peaks, self.points, self.texts, self.decay_calculated, self.rise_calculated), key=lambda x: x[0][0])
                            self.marked_peaks, self.points, self.texts, self.decay_calculated, self.rise_calculated = map(list, zip(*sorted_data))

                            self.canvas.draw()
                    else:
                        messagebox.showinfo(title="Info", message="No peaks found within the window.")
                else:
                    messagebox.showwarning(title="Warning", message="Window is too small or contains insufficient data.")

            elif event.button == 3:  # Right click to remove the nearest point
                if self.points:
                    # Find the nearest point to the click
                    x_clicked = event.xdata
                    distances = [abs(point.get_xdata()[0] - x_clicked) for point in self.points]
                    nearest_idx = np.argmin(distances)
                    point = self.points.pop(nearest_idx)
                    text = self.texts.pop(nearest_idx)
                    point.remove()
                    text.remove()
                    peak = self.marked_peaks.pop(nearest_idx)
                    # Remove corresponding decay line if exists
                    if peak in self.decay_line_map:
                        decay_line = self.decay_line_map.pop(peak)
                        if decay_line in self.decay_lines:
                            self.decay_lines.remove(decay_line)
                        decay_line.remove()
                    # Remove corresponding rise line if exists
                    if peak in self.rise_line_map:
                        rise_line = self.rise_line_map.pop(peak)
                        if rise_line in self.rise_lines:
                            self.rise_lines.remove(rise_line)
                        rise_line.remove()
                    if peak in self.rise_times:
                        del self.rise_times[peak]
                    if peak in self.tau_values:
                        del self.tau_values[peak]
                    if peak in self.amplitudes:
                        del self.amplitudes[peak]
                    self.decay_calculated.pop(nearest_idx)
                    self.rise_calculated.pop(nearest_idx)
                    self.canvas.draw()

    def next_page(self):
        if self.time is not None:
            xlims = self.ax.get_xlim()
            range_width = xlims[1] - xlims[0]
            new_xlims = [xlims[0] + range_width, xlims[1] + range_width]
            self.ax.set_xlim(new_xlims)
            self.update_annotations()
            self.canvas.draw()

    def prev_page(self):
        if self.time is not None:
            xlims = self.ax.get_xlim()
            range_width = xlims[1] - xlims[0]
            new_xlims = [xlims[0] - range_width, xlims[1] - range_width]
            self.ax.set_xlim(new_xlims)
            self.update_annotations()
            self.canvas.draw()

    def zoom_in(self):
        if self.time is not None:
            xlims = self.ax.get_xlim()
            new_xlims = [xlims[0] + (xlims[1] - xlims[0]) * 0.1, xlims[1] - (xlims[1] - xlims[0]) * 0.1]
            self.ax.set_xlim(new_xlims)
            self.update_annotations()
            self.canvas.draw()

    def zoom_out(self):
        if self.time is not None:
            xlims = self.ax.get_xlim()
            new_xlims = [xlims[0] - (xlims[1] - xlims[0]) * 0.1, xlims[1] + (xlims[1] - xlims[0]) * 0.1]
            self.ax.set_xlim(new_xlims)
            self.update_annotations()
            self.canvas.draw()

    def update_annotations(self):
        xlims = self.ax.get_xlim()
        ylims = self.ax.get_ylim()
        for point, text in zip(self.points, self.texts):
            x, y = point.get_xdata()[0], point.get_ydata()[0]
            if xlims[0] <= x <= xlims[1] and ylims[0] <= y <= ylims[1]: # Check if the point is within the current view limits
                point.set_visible(True)
                text.set_visible(True)
            else:
                point.set_visible(False)
                text.set_visible(False)
        self.canvas.draw()

if __name__ == "__main__":
    app = App()
    app.mainloop()
