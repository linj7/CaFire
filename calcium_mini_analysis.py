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

class PartitionEvokedDialog(customtkinter.CTkToplevel):
    def __init__(self, parent, default_peak_num="", default_interval_size="", default_offset=""):
        super().__init__(parent)
        self.title("Partition Evoked Parameters")
        self.geometry("200x350")

        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        offset_x = 100  # Horizontal offset from parent window
        offset_y = 100  # Vertical offset from parent window
        self.geometry(f"+{parent_x + offset_x}+{parent_y + offset_y}")

        # Center the dialog over the parent window
        self.transient(parent)
        self.grab_set()

        self.peak_num = None
        self.interval_size = None
        self.offset = None
        self.user_cancelled = False

        self.label_peak_num = customtkinter.CTkLabel(self, text="Peak Num:")
        self.label_peak_num.pack(pady=(20, 0), padx=20)
        self.entry_peak_num = customtkinter.CTkEntry(self)
        self.entry_peak_num.insert(0, default_peak_num)  # Pre-fill with default value
        self.entry_peak_num.pack(pady=(5, 10), padx=20, fill="x")

        self.label_interval_size = customtkinter.CTkLabel(self, text="Interval Size:")
        self.label_interval_size.pack(padx=20)
        self.entry_interval_size = customtkinter.CTkEntry(self)
        self.entry_interval_size.insert(0, default_interval_size)  # Pre-fill with default value
        self.entry_interval_size.pack(pady=(5, 10), padx=20, fill="x")

        self.label_offset = customtkinter.CTkLabel(self, text="Offset:")
        self.label_offset.pack(padx=20)
        self.entry_offset = customtkinter.CTkEntry(self)
        self.entry_offset.insert(0, default_offset)  # Pre-fill with default value
        self.entry_offset.pack(pady=(5, 10), padx=20, fill="x")

        self.calculate_button = customtkinter.CTkButton(self, text="Partition", command=self.on_calculate)
        self.calculate_button.pack(pady=(10, 20))

        # Handle window close event
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Allow resizing
        self.resizable(True, True)

    def on_calculate(self):
        self.peak_num = self.entry_peak_num.get()
        self.interval_size = self.entry_interval_size.get()
        self.offset = self.entry_offset.get()
        if not self.peak_num or not self.interval_size or not self.offset:
            messagebox.showwarning(title="Warning", message="All fields must be filled out.", parent=self)
            return
        self.grab_release()
        self.destroy()

    def on_close(self):
        # When the user closes the dialog without confirming
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

        self.title("CaFire by Lin - Dickman Lab")
        self.geometry(f"{1200}x{900}")

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
        self.load_button.grid(row=row_counter, column=0, padx=10, pady=(20, 10), sticky="we")
        row_counter += 1

        # Create a frame with a custom background color
        evoked_frame = customtkinter.CTkFrame(self.left_sidebar_frame, fg_color="#ebebeb")  # 设置背景颜色为浅灰色
        evoked_frame.grid(row=row_counter, column=0, padx=10, pady=(0, 15), sticky="w")  # Position the frame

        # Add "Evoked" label on the left
        self.evoked_label = customtkinter.CTkLabel(evoked_frame, text="Evoked")
        self.evoked_label.pack(side="left", padx=(0, 5))  # Add padding between label and checkbox

        # Add checkbox on the right of "Evoked"
        self.evoked_var = customtkinter.StringVar(value="off")  # Variable to store the checkbox state
        self.evoked_checkbox = customtkinter.CTkCheckBox(
            evoked_frame,
            text="",  # No text for checkbox since the label is used
            variable=self.evoked_var,
            onvalue="on",
            offvalue="off",
            command=self.handle_evoked_checkbox_change
        )
        self.evoked_checkbox.pack(side="left", padx=(0, 5))  # Add padding between checkbox and next element
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
        self.calculate_baseline_button.grid(row=row_counter, column=0, padx=10, pady=(15, 5), sticky="we")
        row_counter += 1

        self.calculate_DF_F_button = customtkinter.CTkButton(self.left_sidebar_frame, text="Convert to DF/F",
                                                                 command=self.calculate_DF_F, state="disabled")
        self.calculate_DF_F_button.grid(row=row_counter, column=0, padx=10, pady=(5, 15), sticky="we")
        row_counter += 1

        separator = customtkinter.CTkFrame(self.left_sidebar_frame, height=2, width=width, fg_color="#DDDDDD")
        separator.grid(row=row_counter, column=0, sticky="we", padx=10)
        row_counter += 1

        # Partition button
        self.partition_button = customtkinter.CTkButton(self.left_sidebar_frame, text="Partition Evoked Data",
                                                     command=self.partition_evoked, state="disabled")
        self.partition_button.grid(row=row_counter, column=0, padx=10, pady=15, sticky="we")
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

        # Peak threshold label and entry
        self.peak_to_valley_ratio_label = customtkinter.CTkLabel(
            self.left_sidebar_frame,
            text="Peak-to-Valley Ratio",
            text_color="#b5b5b5",
            anchor="w"
        )
        self.peak_to_valley_ratio_label.grid(row=row_counter, column=0, padx=10, pady=5, sticky="w")

        self.peak_to_valley_ratio_entry = customtkinter.CTkEntry(
            self.left_sidebar_frame, 
            width=50
        )
        self.peak_to_valley_ratio_entry.grid(row=row_counter, column=0, padx=(110, 10), pady=5, sticky="e")
        row_counter += 1

        # Calculate rise button
        self.calculate_rise_button = customtkinter.CTkButton(self.left_sidebar_frame, text="Calculate Rise",
                                                                  command=self.calculate_rise)
        self.calculate_rise_button.grid(row=row_counter, column=0, padx=10, pady=(5, 15), sticky="we")
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
        self.version_label = customtkinter.CTkLabel(self.left_sidebar_frame, text="v1.3")
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
        up_page_image = prev_page_image.rotate(-90, expand=True)
        down_page_image = next_page_image.rotate(-90, expand=True)

        # Create CTkImage
        self.zoom_in_image_normal = customtkinter.CTkImage(light_image=zoom_in_image, size=(24, 24))
        self.zoom_out_image_normal = customtkinter.CTkImage(light_image=zoom_out_image, size=(24, 24))
        self.prev_page_image_normal = customtkinter.CTkImage(light_image=prev_page_image, size=(24, 24))
        self.next_page_image_normal = customtkinter.CTkImage(light_image=next_page_image, size=(24, 24))
        self.up_page_image_normal = customtkinter.CTkImage(light_image=up_page_image, size=(24, 24))
        self.down_page_image_normal = customtkinter.CTkImage(light_image=down_page_image, size=(24, 24))

        button_spacing = 40  # Vertical spacing between buttons
        center_offset = 20   # Center offset for pairing buttons

        # Zoom in label
        self.zoom_in_x_label = customtkinter.CTkLabel(
            self.canvas_widget,
            text="",
            image=self.zoom_in_image_normal,
            width=24,
            height=24
        )
        self.zoom_in_x_label.place(relx=0.5, rely=1.0, x=-40, y=-center_offset - 20, anchor='e')
        self.zoom_in_x_label.configure(cursor="hand2")

        # Zoom out label
        self.zoom_out_x_label = customtkinter.CTkLabel(
            self.canvas_widget,
            text="",
            image=self.zoom_out_image_normal,
            width=24,
            height=24
        )
        self.zoom_out_x_label.place(relx=0.5, rely=1.0, x=-5, y=-center_offset - 20, anchor='e')
        self.zoom_out_x_label.configure(cursor="hand2")

        # Zoom in label
        self.zoom_in_y_label = customtkinter.CTkLabel(
            self.canvas_widget,
            text="",
            image=self.zoom_in_image_normal,
            width=24,
            height=24
        )
        self.zoom_in_y_label.place(relx=1.0, rely=0.5, x=-25, y=-center_offset - button_spacing, anchor='e')
        self.zoom_in_y_label.configure(cursor="hand2")

        # Zoom out label
        self.zoom_out_y_label = customtkinter.CTkLabel(
            self.canvas_widget,
            text="",
            image=self.zoom_out_image_normal,
            width=24,
            height=24
        )
        self.zoom_out_y_label.place(relx=1.0, rely=0.5, x=-25, y=-center_offset, anchor='e')
        self.zoom_out_y_label.configure(cursor="hand2")

        # Previous page
        self.prev_page_label = customtkinter.CTkLabel(
            self.canvas_widget,
            text="",
            image=self.prev_page_image_normal,
            width=24,
            height=24
        )
        self.prev_page_label.place(relx=0.5, rely=1.0, x=60, y=-center_offset - 20, anchor='e')
        self.prev_page_label.configure(cursor="hand2")

        # Next page
        self.next_page_label = customtkinter.CTkLabel(
            self.canvas_widget,
            text="",
            image=self.next_page_image_normal,
            width=24,
            height=24
        )
        self.next_page_label.place(relx=0.5, rely=1.0, x=90, y=-center_offset - 20, anchor='e')
        self.next_page_label.configure(cursor="hand2")

        # Up
        self.up_page_label = customtkinter.CTkLabel(
            self.canvas_widget,
            text="",
            image=self.up_page_image_normal,
            width=24,
            height=24
        )
        self.up_page_label.place(relx=1.0, rely=0.5, x=-25, y=center_offset, anchor='e')
        self.up_page_label.configure(cursor="hand2")

        # Down
        self.down_page_label = customtkinter.CTkLabel(
            self.canvas_widget,
            text="",
            image=self.down_page_image_normal,
            width=24,
            height=24
        )
        self.down_page_label.place(relx=1.0, rely=0.5, x=-25, y=center_offset + button_spacing, anchor='e')
        self.down_page_label.configure(cursor="hand2")


        self.zoom_in_x_label.bind("<Button-1>", lambda event: self.on_button_press(self.zoom_in_x_label))
        self.zoom_in_x_label.bind("<ButtonRelease-1>", lambda event: self.on_button_release(self.zoom_in_x_label, self.zoom_in_x))

        self.zoom_out_x_label.bind("<Button-1>", lambda event: self.on_button_press(self.zoom_out_x_label))
        self.zoom_out_x_label.bind("<ButtonRelease-1>", lambda event: self.on_button_release(self.zoom_out_x_label, self.zoom_out_x))

        self.zoom_in_y_label.bind("<Button-1>", lambda event: self.on_button_press(self.zoom_in_y_label))
        self.zoom_in_y_label.bind("<ButtonRelease-1>", lambda event: self.on_button_release(self.zoom_in_y_label, self.zoom_in_y))

        self.zoom_out_y_label.bind("<Button-1>", lambda event: self.on_button_press(self.zoom_out_y_label))
        self.zoom_out_y_label.bind("<ButtonRelease-1>", lambda event: self.on_button_release(self.zoom_out_y_label, self.zoom_out_y))

        self.prev_page_label.bind("<Button-1>", lambda event: self.on_button_press(self.prev_page_label))
        self.prev_page_label.bind("<ButtonRelease-1>", lambda event: self.on_button_release(self.prev_page_label, self.prev_page))

        self.next_page_label.bind("<Button-1>", lambda event: self.on_button_press(self.next_page_label))
        self.next_page_label.bind("<ButtonRelease-1>", lambda event: self.on_button_release(self.next_page_label, self.next_page))

        self.up_page_label.bind("<Button-1>", lambda event: self.on_button_press(self.up_page_label))
        self.up_page_label.bind("<ButtonRelease-1>", lambda event: self.on_button_release(self.up_page_label, self.move_up))

        self.down_page_label.bind("<Button-1>", lambda event: self.on_button_press(self.down_page_label))
        self.down_page_label.bind("<ButtonRelease-1>", lambda event: self.on_button_release(self.down_page_label, self.move_down))

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
        self.partition_lines = []
        self.partition_labels = []
        self.peak_num = None
        self.rise_start_markers = {}  # 改用字典来存储rise start markers，用peak作为键
        self.default_peak_to_valley_ratio = 0.47  # 添加这个变量来存储计算出的默认值

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
        self.last_peak_num = "" 
        self.last_interval_size = ""
        self.last_offset = ""

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
        if self.df_f is not None:
            self.evoked_var.set("off")
            self.peak_num = None
            # 清空 peak_to_valley_ratio_entry
            self.peak_to_valley_ratio_entry.delete(0, 'end')
            # 清除baseline相关的数据
            self.baseline_values = None
            if self.baseline_line is not None:
                self.baseline_line.remove()
                self.baseline_line = None
            # 禁用Calculate DF/F按钮，因为需要重新计算baseline
            self.calculate_DF_F_button.configure(state="disabled")

        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
            df.columns = df.columns.map(str)
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

    def handle_evoked_checkbox_change(self):
        if self.evoked_var.get() == "on":
            # 弹出对话框并获取用户输入
            dialog = customtkinter.CTkToplevel(self)
            dialog.title("Enter Peak Num")
            dialog.geometry("300x150")  # 设置对话框大小

            # 计算主窗口的位置
            self.update_idletasks()  # 更新窗口尺寸信息
            main_x = self.winfo_x()
            main_y = self.winfo_y()
            main_width = self.winfo_width()
            main_height = self.winfo_height()

            # 计算弹窗的居中位置
            dialog_x = main_x + (main_width - 300) // 2
            dialog_y = main_y + (main_height - 150) // 2
            dialog.geometry(f"300x150+{dialog_x}+{dialog_y}")  # 设置弹窗的位置

            # 添加说明标签
            label = customtkinter.CTkLabel(dialog, text="Enter the peak num in each period:")
            label.pack(pady=10)

            # 添加输入框
            entry = customtkinter.CTkEntry(dialog, width=200)
            entry.pack(pady=5)

            # 定义保存输入的函数
            def save_peak_num():
                try:
                    # 获取用户输入并保存到全局变量
                    self.peak_num = int(entry.get())  # 转换为整数并保存
                    dialog.destroy()  # 关闭对话框

                    # 启用 Partition 按钮
                    self.partition_button.configure(state="normal")
                except ValueError:
                    messagebox.showwarning(title="Warning", message="Please enter a valid integer.")

            # 添加确认按钮
            confirm_button = customtkinter.CTkButton(dialog, text="Confirm", command=save_peak_num)
            confirm_button.pack(pady=10)

            # 让对话框成为模态窗口，阻止主窗口交互
            dialog.transient(self)
            dialog.grab_set()
            self.wait_window(dialog)
            self.partition_button.configure(state="enabled")
            self.calculate_amplitude_button.configure(state="disabled")
        else:
            self.partition_button.configure(state="disabled")
            self.calculate_amplitude_button.configure(state="normal")
            
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
        dialog = ThresholdDialog(self, self.last_peak_threshold, self.last_min_distance)
        self.wait_window(dialog)
        if not dialog.user_cancelled:
            try:
                peak_threshold = float(dialog.peak_threshold)
                min_distance = float(dialog.min_distance)
                self.last_peak_threshold = dialog.peak_threshold
                self.last_min_distance = dialog.min_distance

                # 计算并保存默认的peak to valley ratio
                if self.df_f is not None:
                    max_value = np.max(self.df_f)
                    if max_value != 0:  # 避免除以0
                        self.default_peak_to_valley_ratio = peak_threshold / max_value
                        # 无论entry是否为空，都更新值
                        self.peak_to_valley_ratio_entry.delete(0, 'end')
                        self.peak_to_valley_ratio_entry.insert(0, f"{self.default_peak_to_valley_ratio:.3f}")

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

            except ValueError as e:
                messagebox.showerror(title="Error", message=str(e))

    def calculate_baseline(self):
        if self.time is None or self.df_f is None:
            messagebox.showwarning(title="Warning", message="No data loaded.")
            return

        window_size = 50  # 滑动窗口大小
        percentile = 30  # 使用第20百分位数作为baseline

        # 初始化baseline数组
        self.baseline_values = np.zeros_like(self.df_f)

        # 对每个点计算baseline
        for i in range(len(self.df_f)):
            if i < window_size:  # 如果是前面的点，使用后面的点
                window = self.df_f[i:i+window_size]
            else:  # 否则使用前面的点
                window = self.df_f[i-window_size:i]
            
            # 计算窗口内的第10百分位数作为baseline
            self.baseline_values[i] = np.percentile(window, percentile)

        # 绘制baseline
        if self.baseline_line is not None:
            self.baseline_line.remove()
        self.baseline_line, = self.ax.plot(self.time, self.baseline_values, 'r--', alpha=0.5, label='Baseline')
        self.ax.legend()
        self.canvas.draw()

        # 启用Calculate DF/F按钮
        self.calculate_DF_F_button.configure(state="normal")

    def calculate_DF_F(self):
        """
        Calculate DF/F using the baseline values and update the plot.
        """
        if self.df_f is None or self.baseline_values is None:
            messagebox.showwarning(title="Warning", message="No data or baseline available.")
            return

        try:
            # Calculate new DF/F values
            self.df_f = (self.df_f - self.baseline_values) / self.baseline_values

            # Clear previous plot content
            self.clear_plot()
            self.ax.clear()

            # Plot the updated DF/F values
            self.ax.plot(self.time, self.df_f, color='blue')
            self.ax.set_ylim(np.min(self.df_f), np.max(self.df_f))
            self.ax.grid(True)

            # Update the canvas to show the new plot
            self.canvas.draw()
        except Exception as e:
            messagebox.showerror(title="Error", message=f"An error occurred while calculating DF/F: {e}")

    def calculate_amplitude(self):
        if not self.marked_peaks:
            messagebox.showwarning(title="Warning", message="No peaks available for amplitude calculation.")
            return

        # Sort marked peaks by time
        self.marked_peaks = sorted(self.marked_peaks, key=lambda peak: peak[0])

        for i, (peak_time, peak_value) in enumerate(self.marked_peaks):
            peak_index = self.time[self.time == peak_time].index[0]

            # Evoked模式且当前peak的索引不是peak_num的整数倍
            if self.evoked_var.get() == "on" and (i) % self.peak_num != 0:
                # 确保有上一个峰值以计算fitted decay curve
                if i > 0:
                    prev_peak_time, prev_peak_value = self.marked_peaks[i - 1]
                    prev_peak_index = self.time[self.time == prev_peak_time].index[0]

                    # 检查是否有之前的 decay curve
                    if (prev_peak_time, prev_peak_value) in self.decay_line_map:
                        # 获取上一个峰值的 decay curve 参数
                        prev_decay_line = self.decay_line_map[(prev_peak_time, prev_peak_value)]

                        # Decay function: 计算 decay curve 延伸到当前 peak 的值
                        t_data_range = peak_index - prev_peak_index
                        prev_tau = self.tau_values[(prev_peak_time, prev_peak_value)]
                        prev_y0 = prev_peak_value
                        decay_value = self.decay_function(t_data_range, prev_tau, prev_y0)

                        # 计算新的 amplitude
                        new_amplitude = peak_value - decay_value
                        self.amplitudes[(peak_time, peak_value)] = new_amplitude

                        print(f"Evoked on: Calculated amplitude for peak {i}, Value: {new_amplitude}")
                    else:
                        print(f"Warning: No decay line found for peak {i - 1}. Skipping amplitude calculation.")
                        self.amplitudes[(peak_time, peak_value)] = None  # 未能计算的情况
                else:
                    print("Warning: First peak cannot calculate amplitude with evoked mode.")
                    self.amplitudes[(peak_time, peak_value)] = None  # 未能计算的情况
            else:
                # 非 Evoked 模式或 peak_num 整数倍，使用默认的 amplitude 计算
                self.amplitudes[(peak_time, peak_value)] = peak_value
                print(f"Default amplitude for peak {i}, Value: {peak_value}")

        messagebox.showinfo(title="Success", message="Amplitude calculation completed.")

    def export_stats(self):
        if self.time is None or not self.marked_peaks:
            messagebox.showwarning(title="Warning", message="No stats to export.")
            return

        peak_times = [peak[0] for peak in self.marked_peaks]
        peak_values = [peak[1] for peak in self.marked_peaks]
        amplitude_values = [self.amplitudes.get(peak, None) for peak in self.marked_peaks]
        tau_values = [self.tau_values.get(peak, None) for peak in self.marked_peaks]
        rise_times = [self.rise_times.get(peak, None) for peak in self.marked_peaks]
        
        # 添加baseline值
        baseline_values = []
        if self.baseline_values is not None:
            for peak_time in peak_times:
                # 找到peak_time对应的时间索引
                time_index = self.time[self.time == peak_time].index[0]
                # 获取该位置的baseline值
                baseline_value = self.baseline_values[time_index]
                baseline_values.append(baseline_value)
        else:
            baseline_values = [None] * len(peak_times)

        df_export = pd.DataFrame({
            "Time": peak_times,
            "Amplitude": amplitude_values,
            "Rise Time": rise_times,
            "Decay Time": tau_values,
            "Baseline": baseline_values  # 添加baseline列
        })
        df_export = df_export.sort_values(by="Time")

        export_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if not export_path:
            return

        try:
            # Check if the data has been partitioned
            if len(self.partition_lines) >= 2 and len(self.partition_lines) % 2 == 0:
                intervals = []
                interval_stats = []
                for i in range(0, len(self.partition_lines), 2):
                    start = self.partition_lines[i].get_xdata()[0]
                    end = self.partition_lines[i + 1].get_xdata()[0]
                    if self.time.iloc[0] <= start <= self.time.iloc[-1] and self.time.iloc[0] <= end <= self.time.iloc[-1]:
                        interval_data = self.df_f[(self.time >= start) & (self.time <= end)].values.flatten()
                        intervals.append(interval_data)

                        # Extract statistical data for each interval
                        interval_peaks = [(t, a, r, d) for t, a, r, d in zip(peak_times, peak_values, rise_times, tau_values) if start <= t <= end]
                        interval_stats.append(interval_peaks)

                # Ensure all interval data have consistent lengths (pad with NaN)
                max_length = max(len(stats) for stats in interval_stats)
                detailed_rows = []
                for idx, stats in enumerate(interval_stats):
                    row = [f"{idx + 1}"]
                    row.extend([peak[1] for peak in stats] + [float("nan")] * (max_length - len(stats)))  # Amplitudes
                    row.extend([peak[2] for peak in stats] + [float("nan")] * (max_length - len(stats)))  # Rise Times
                    row.extend([peak[3] for peak in stats] + [float("nan")] * (max_length - len(stats)))  # Decay Times
                    detailed_rows.append(row)

                detailed_columns = ["Interval Number"]
                detailed_columns.extend([f"Amplitude_{i + 1}" for i in range(max_length)])
                detailed_columns.extend([f"Rise Time (𝜏)_{i + 1}" for i in range(max_length)])
                detailed_columns.extend([f"Decay Time (𝜏)_{i + 1}" for i in range(max_length)])
                df_detailed = pd.DataFrame(detailed_rows, columns=detailed_columns)
                detailed_export_path = export_path
                df_detailed.to_excel(detailed_export_path, index=False, engine='openpyxl')

                padded_intervals = [list(interval) + [float("nan")] * (max_length - len(interval)) for interval in intervals]
                average_trace = [sum(filter(lambda x: not pd.isna(x), values)) / len(values) for values in zip(*padded_intervals)]
                padded_intervals.append(average_trace)

                interval_columns = [f"Interval_{i + 1}" for i in range(len(intervals))] + ["Average Trace"]
                df_intervals = pd.DataFrame(padded_intervals).T
                df_intervals.columns = interval_columns
                interval_export_path = export_path.replace(".xlsx", "_intervals.xlsx")
                df_intervals.to_excel(interval_export_path, index=False, engine='openpyxl')

                messagebox.showinfo(title="Success", message=f"Stats successfully exported to:\n{detailed_export_path}\n{interval_export_path}")
            else:
                # Save only the statistical data file
                df_export.to_excel(export_path, index=False, engine='openpyxl')
                messagebox.showinfo(title="Success", message=f"Stats successfully exported to:\n{export_path}")

        except Exception as e:
            messagebox.showerror(title="Error", message=f"Error exporting stats: {e}")

    def partition_evoked(self):
        if self.time is None or self.df_f is None:
            messagebox.showwarning(title="Warning", message="No data loaded.")
            return

        # Show the PartitionEvokedDialog
        partition_dialog = PartitionEvokedDialog(
            self,
            default_peak_num=self.last_peak_num,
            default_interval_size=self.last_interval_size,
            default_offset=self.last_offset
        )
        self.wait_window(partition_dialog)

        # Check if the user cancelled the operation
        if partition_dialog.user_cancelled:
            return

        # Get user input
        try:
            peak_num = int(partition_dialog.peak_num)
            interval_size = int(partition_dialog.interval_size)
            offset = int(partition_dialog.offset)
        except (ValueError, TypeError):
            messagebox.showwarning(title="Warning", message="Invalid input values.")
            return

        # Store last inputs
        self.last_peak_num = partition_dialog.peak_num
        self.last_interval_size = partition_dialog.interval_size
        self.last_offset = partition_dialog.offset

        # Clear previous segmentation lines and annotations
        for line in self.partition_lines:
            line.remove() 
        for label in self.partition_labels:
            label.remove() 
        self.partition_lines.clear()
        self.partition_labels.clear()

        # Draw segmentation lines and annotations
        for i in range(0, len(self.marked_peaks), peak_num):
            peak_time = self.marked_peaks[i][0]  # First element is the time
            start_peak = peak_time - offset
            end_peak = start_peak + interval_size

            if start_peak >= self.time.iloc[0]:
                line = self.ax.axvline(x=start_peak, color='g', linestyle='--')
                label = self.ax.text(start_peak, self.ax.get_ylim()[1] * 1.01, "Start {0}\n(x={1})".format(i // peak_num + 1, start_peak), color='g')
                self.partition_lines.append(line)
                self.partition_labels.append(label)

            if end_peak <= self.time.iloc[-1]:
                line = self.ax.axvline(x=end_peak, color='r', linestyle='--')
                label = self.ax.text(end_peak, self.ax.get_ylim()[1] * 1.01, "End {0}\n(x={1})".format(i // peak_num + 1, end_peak), color='r')
                self.partition_lines.append(line)
                self.partition_labels.append(label)
        
        xlims = self.ax.get_xlim()
        for line, label in zip(self.partition_lines, self.partition_labels):
            x = line.get_xdata()[0]
            if xlims[0] <= x <= xlims[1]:
                line.set_visible(True)
                label.set_visible(True)
            else:
                line.set_visible(False)
                label.set_visible(False)

        self.canvas.draw()

    def calculate_decay(self):
        if not self.marked_peaks:
            messagebox.showwarning(title="Warning", message="No peaks available for decay calculation.")
            return

        self.calculate_amplitude_button.configure(state="normal")

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

        if not self.marked_peaks:
            messagebox.showwarning(title="Warning", message="No peaks available for rise calculation.")
            return

        # 获取peak to valley ratio，优先使用用户输入值，否则使用计算值或默认值
        try:
            peak_to_valley_ratio = float(self.peak_to_valley_ratio_entry.get())
        except ValueError:
            peak_to_valley_ratio = self.default_peak_to_valley_ratio

        # Sort marked peaks by time
        self.marked_peaks = sorted(self.marked_peaks, key=lambda peak: peak[0])

        for i, (peak_time, peak_value) in enumerate(self.marked_peaks):
            # Skip if rise has already been calculated for this peak
            if self.rise_calculated[i]:
                continue

            peak_index = self.time[self.time == peak_time].index[0]
            rise_start_index = None
            rise_end_index = peak_index

            # 如果复选框被勾选且当前 peak 的索引不是 peak_num 的整数倍
            if self.evoked_var.get() == "on" and (i) % self.peak_num != 0:
                print("evoked on")
                if i > 0:  # 确保不是第一个 peak
                    prev_peak_time, _ = self.marked_peaks[i - 1]
                    prev_peak_index = self.time[self.time == prev_peak_time].index[0]
                    rise_start_index = prev_peak_index + np.argmin(self.df_f[prev_peak_index:peak_index])
                else:
                    rise_start_index = None  # 如果是第一个 peak，默认从头开始
                print(f"i:{i}, current peak index: {peak_index}, prev peak index:{prev_peak_index}, rise start index: {rise_start_index}")


            # 如果复选框未勾选或索引是整数倍，按照原逻辑寻找起始点
            if rise_start_index is None:
                for j in range(peak_index - 1, 0, -1):
                    if self.df_f[j] < self.df_f[j - 1] and self.df_f[j] < self.df_f[j + 1]:
                        rise_start_index = j
                        break
                if rise_start_index is None:
                    rise_start_index = 0  # 如果没有找到局部最小值，则从数据开头开始

                try:
                    peak_to_valley_ratio = float(self.peak_to_valley_ratio_entry.get())
                except ValueError:
                    peak_to_valley_ratio = 0.47
                while self.df_f[rise_start_index] >= peak_to_valley_ratio * peak_value and rise_start_index > 0:
                    for j in range(rise_start_index - 1, 0, -1):
                        if self.df_f[j] < self.df_f[j - 1] and self.df_f[j] < self.df_f[j + 1]:
                            rise_start_index = j
                            break
                    else:
                        break  # Exit if no new local minimum is found

            # 在rise_start_index处添加标记
            rise_start_marker, = self.ax.plot(self.time[rise_start_index], self.df_f[rise_start_index], 'gx')
            self.rise_start_markers[(peak_time, peak_value)] = rise_start_marker  # 使用peak作为键来存储marker
            
            # Fit rise function
            interval_data = self.df_f
            t_data = np.arange(rise_start_index, peak_index + 1)
            t_data_range = t_data - rise_start_index
            y_data = interval_data[rise_start_index: peak_index + 1]

            y_data = np.array(y_data)  # Ensure y_data is a numpy array
            y0 = max(y_data[0], 0.01)

            # 检查 t_data_range 和 y_data 是否有效
            if np.any(np.isnan(t_data_range)) or np.any(np.isnan(y_data)):
                print("Error: t_data_range or y_data contains NaN values.")
            if np.any(np.isinf(t_data_range)) or np.any(np.isinf(y_data)):
                print("Error: t_data_range or y_data contains Inf values.")

            try:
                popt, pcov = curve_fit(lambda t, tau: self.rise_function(t, tau, y0), t_data_range, y_data, p0=[0.5], bounds=(0.001, np.inf))
                tau_fitted = popt[0]
                print(f"tau_fitted: {tau_fitted}")
                t_fit = np.linspace(0, t_data_range[-1], 100)
                y_fit = self.rise_function(t_fit, tau_fitted, y0)

                # Clip the fitted curve to not exceed the peak value
                valid_indices = np.where(y_fit <= peak_value)[0]
                if len(valid_indices) > 0:
                    t_fit = t_fit[valid_indices]
                    y_fit = y_fit[valid_indices]

                # Plot the fitted rise curve
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

        for line in self.partition_lines:
            line.remove()
        self.partition_lines.clear()

        for label in self.partition_labels:
            label.remove()
        self.partition_labels.clear()

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

        # 清除rise起始点的标记
        for marker in self.rise_start_markers.values():
            marker.remove()
        self.rise_start_markers.clear()

        self.canvas.draw() # refresh the canvas

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
                        # 删除对应的rise start marker
                        if peak in self.rise_start_markers:
                            marker = self.rise_start_markers.pop(peak)
                            marker.remove()
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

    def move_up(self):
        if self.time is not None:
            ylims = self.ax.get_ylim()
            range_height = ylims[1] - ylims[0]
            shift = range_height * 0.1  # 上移 10% 的当前范围
            new_ylims = [ylims[0] + shift, ylims[1] + shift]
            self.ax.set_ylim(new_ylims)
            self.update_annotations()
            self.canvas.draw()

    def move_down(self):
        if self.time is not None:
            ylims = self.ax.get_ylim()
            range_height = ylims[1] - ylims[0]
            shift = range_height * 0.1  # 下移 10% 的当前范围
            new_ylims = [ylims[0] - shift, ylims[1] - shift]
            self.ax.set_ylim(new_ylims)
            self.update_annotations()
            self.canvas.draw()

    def zoom_in_x(self):
        if self.time is not None:
            xlims = self.ax.get_xlim()
            new_xlims = [xlims[0] + (xlims[1] - xlims[0]) * 0.1, xlims[1] - (xlims[1] - xlims[0]) * 0.1]
            self.ax.set_xlim(new_xlims)
            self.update_annotations()
            self.canvas.draw()

    def zoom_out_x(self):
        if self.time is not None:
            xlims = self.ax.get_xlim()
            new_xlims = [xlims[0] - (xlims[1] - xlims[0]) * 0.1, xlims[1] + (xlims[1] - xlims[0]) * 0.1]
            self.ax.set_xlim(new_xlims)
            self.update_annotations()
            self.canvas.draw()

    def zoom_in_y(self):
        if self.df_f is not None:
            ylims = self.ax.get_ylim()
            new_ylims = [ylims[0] + (ylims[1] - ylims[0]) * 0.1, ylims[1] - (ylims[1] - ylims[0]) * 0.1]
            self.ax.set_ylim(new_ylims)
            self.update_annotations()
            self.canvas.draw()

    def zoom_out_y(self):
        if self.df_f is not None:
            ylims = self.ax.get_ylim()
            new_ylims = [ylims[0] - (ylims[1] - ylims[0]) * 0.1, ylims[1] + (ylims[1] - ylims[0]) * 0.1]
            self.ax.set_ylim(new_ylims)
            self.update_annotations()
            self.canvas.draw()

    def update_annotations(self):
        xlims = self.ax.get_xlim()
        ylims = self.ax.get_ylim()

        for point, text in zip(self.points, self.texts):
            x, y = point.get_xdata()[0], point.get_ydata()[0]
            if xlims[0] <= x <= xlims[1] and ylims[0] <= y <= ylims[1]:  # Check if the point is within the current view limits
                point.set_visible(True)
                text.set_visible(True)
            else:
                point.set_visible(False)
                text.set_visible(False)

        for line, label in zip(self.partition_lines, self.partition_labels):
            x = line.get_xdata()[0]
            if xlims[0] <= x <= xlims[1]:
                line.set_visible(True)
                label.set_visible(True)
            else:
                line.set_visible(False)
                label.set_visible(False)

        self.canvas.draw()

if __name__ == "__main__":
    app = App()
    app.mainloop()
