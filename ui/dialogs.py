import numpy as np
import pandas as pd
import sys
import os
import customtkinter
from tkinter import filedialog, messagebox
from utils.image_utils import load_svg_image
from ui.window import set_window_style, set_window_icon

class LoadFileDialog(customtkinter.CTkToplevel):
    def __init__(self, parent, default_sheet_name="", default_x_col="", default_y_col=""):
        super().__init__(parent)
        self.parent = parent  # Save parent window reference
        self.parent.bind('<Destroy>', self.on_parent_destroy) # Listen for parent window close event
        self.title("Load")
        self.geometry("200x500")

        set_window_style(self)
        set_window_icon(self)

        # Set window position to the left of the main window
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        self.geometry(f"+{parent_x - 360}+{parent_y}")

        # Set default values from parameters
        self.sheet_name = default_sheet_name
        self.x_col = default_x_col
        self.y_col = default_y_col
        self.user_cancelled = False

        # Create title label
        self.title_label = customtkinter.CTkLabel(
            self, 
            text="Input File Specifications",
            font=("Helvetica", 14, "bold")
        )
        self.title_label.pack(pady=(20, 5), padx=20)

        # Create labels and entry fields with pre-filled values
        self.label_sheet = customtkinter.CTkLabel(
            self, 
            text="Sheet Name",
            font=customtkinter.CTkFont(size=12),
            anchor="w"
        )
        self.label_sheet.pack(pady=(10, 0), padx=20, anchor="w")
        self.entry_sheet = customtkinter.CTkEntry(self, width=200)
        self.entry_sheet.insert(0, default_sheet_name)
        self.entry_sheet.pack(pady=(0, 10), padx=20)

        self.label_x_col = customtkinter.CTkLabel(
            self, 
            text="X Column Name",
            font=customtkinter.CTkFont(size=12),
            anchor="w"
        )
        self.label_x_col.pack(padx=20, anchor="w")
        self.entry_x_col = customtkinter.CTkEntry(self, width=200)
        self.entry_x_col.insert(0, default_x_col)
        self.entry_x_col.pack(pady=(0, 10), padx=20)

        self.label_y_col = customtkinter.CTkLabel(
            self, 
            text="Y Column Name",
            font=customtkinter.CTkFont(size=12),
            anchor="w"
        )
        self.label_y_col.pack(padx=20, anchor="w")
        self.entry_y_col = customtkinter.CTkEntry(self, width=200)
        self.entry_y_col.insert(0, default_y_col)
        self.entry_y_col.pack(pady=(0, 10), padx=20)

        # Create a frame to contain the checkboxes
        self.checkbox_frame = customtkinter.CTkFrame(self)
        self.checkbox_frame.pack(pady=(5, 10), padx=20)
        self.checkbox_frame.configure(fg_color="transparent")

        self.evoked_var = customtkinter.StringVar(value="off")
        self.evoked_checkbox = customtkinter.CTkCheckBox(
            self.checkbox_frame,
            text="evoked", 
            variable=self.evoked_var,
            onvalue="on",
            offvalue="off",
            command=self.on_evoked_changed,
            checkbox_width=18,          
            checkbox_height=18,         
            corner_radius=0,            
            border_width=2,             
            fg_color="#dbdbdb",         
            hover_color="#d5d9df",      
            checkmark_color="black",     
            border_color="black"        
        )
        self.evoked_checkbox.pack(side="left", padx=(0, 3))

        # Add mini checkbox
        self.mini_var = customtkinter.StringVar(value="off")
        self.mini_checkbox = customtkinter.CTkCheckBox(
            self.checkbox_frame,
            text="mini",
            variable=self.mini_var,
            onvalue="on",
            offvalue="off",
            command=self.on_mini_changed,
            checkbox_width=18,          
            checkbox_height=18,         
            corner_radius=0,            
            border_width=2,             
            fg_color="#dbdbdb",         
            hover_color="#d5d9df",      
            checkmark_color="black",     
            border_color="black"  
        )
        self.mini_checkbox.pack(side="left")

        convert_icon = load_svg_image('assets/convert.svg', width=24, height=24)
        convert_icon_ctk = customtkinter.CTkImage(
            light_image=convert_icon,
            dark_image=convert_icon,
            size=(20, 20)
        )
        self.convert_button = customtkinter.CTkButton(
            self,
            image=convert_icon_ctk,
            compound="left",
            fg_color="#dbdbdb", 
            hover_color="#d5d9df",
            text="Convert to ΔF/F",
            text_color="black",
            font=customtkinter.CTkFont(size=12, weight="bold"),
            command=self.on_convert_and_load,
            height=40,
            state="disabled"
        )
        self.convert_button.pack(pady=(5, 5))

        # Add or label
        self.or_label = customtkinter.CTkLabel(
            self,
            text="or",
            font=customtkinter.CTkFont(size=15),
        )
        self.or_label.pack(pady=(0, 0))

        # Load icon
        load_file_icon = load_svg_image('assets/load_file.svg', width=24, height=24)
        load_file_icon_ctk = customtkinter.CTkImage(
            light_image=load_file_icon,
            dark_image=load_file_icon,
            size=(20, 20)
        )
        self.load_file_button = customtkinter.CTkButton(
            self,
            image=load_file_icon_ctk,
            compound="left",
            fg_color="#dbdbdb", 
            hover_color="#d5d9df",
            text="Load Raw Data",
            text_color="black",
            font=customtkinter.CTkFont(size=12, weight="bold"),
            command=self.on_load,
            height=40,
            state="disabled"
        )
        self.load_file_button.pack(pady=(5, 5))

        # Add a new property to mark whether conversion is needed
        self.convert_to_df_f = False
        
        # Handle window close event
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_load(self):
        self.convert_to_df_f = False
        self.on_confirm()

    def on_convert_and_load(self):
        self.convert_to_df_f = True
        self.on_confirm()

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

    def get_evoked_var(self):
        return self.evoked_var.get()  # Return the value of the StringVar ("on" or "off")

    def on_evoked_changed(self):
        if self.evoked_var.get() == "on":
            self.mini_var.set("off")
            self.load_file_button.configure(state="normal")
            self.convert_button.configure(state="normal")
        else:
            self.load_file_button.configure(state="disabled")
            self.convert_button.configure(state="disabled")

    def on_mini_changed(self):
        if self.mini_var.get() == "on":
            self.evoked_var.set("off")
            self.load_file_button.configure(state="normal")
            self.convert_button.configure(state="normal")
        else:
            self.load_file_button.configure(state="disabled")
            self.convert_button.configure(state="disabled")

    def on_parent_destroy(self, event):
        # Check if the main window is being closed
        if event.widget == self.parent:
            self.user_cancelled = True  # Add this line
            self.grab_release()
            self.destroy()

class PartitionEvokedDialog(customtkinter.CTkToplevel):
    def __init__(self, parent, default_peak_num="", default_interval_size="", default_offset=""):
        super().__init__(parent)
        self.parent = parent
        self.title("Partition Parameters")
        self.geometry("200x600")  # Increase height to accommodate new buttons

        set_window_style(self)
        set_window_icon(self)
        
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        self.geometry(f"+{parent_x + parent_width + 10}+{parent_y}")

        self.peak_num = None
        self.interval_size = None
        self.offset = None
        self.user_cancelled = False

        self.title_label = customtkinter.CTkLabel(
            self, 
            text="Partition Specifications",
            font=("Helvetica", 14, "bold")
        )
        self.title_label.pack(pady=(20, 5), padx=20)
        self.title_desc = customtkinter.CTkLabel(
            self,
            text="Applicable only to evoked data",
            font=customtkinter.CTkFont(size=10),
            text_color="gray",
            anchor="w"
        )
        self.title_desc.pack(pady=(0, 0), padx=20, anchor="w")

        self.label_peak_num = customtkinter.CTkLabel(
            self, 
            text="Peak Num",
            font=customtkinter.CTkFont(size=12),
            anchor="w"
        )
        self.label_peak_num.pack(pady=(10, 0), padx=20, anchor="w")
        self.label_peak_num_desc = customtkinter.CTkLabel(
            self,
            text="Number of peaks per interval",
            font=customtkinter.CTkFont(size=10),
            text_color="gray",
            anchor="w"
        )
        self.label_peak_num_desc.pack(pady=(0, 0), padx=20, anchor="w")
        self.entry_peak_num = customtkinter.CTkEntry(self, width=200)
        self.entry_peak_num.insert(0, default_peak_num)  # Pre-fill with default value
        self.entry_peak_num.pack(pady=(5, 10), padx=20, fill="x", anchor="w")

        self.label_interval_length = customtkinter.CTkLabel(
            self, 
            text="Interval Length",
            font=customtkinter.CTkFont(size=12),
            anchor="w"
        )
        self.label_interval_length.pack(pady=(7, 0), padx=20, anchor="w")
        self.entry_interval_length = customtkinter.CTkEntry(self, width=200)
        self.entry_interval_length.insert(0, default_interval_size)  # Pre-fill with default value
        self.entry_interval_length.pack(pady=(5, 10), padx=20, fill="x", anchor="w")

        self.label_offset = customtkinter.CTkLabel(
            self, 
            text="Offset",
            font=customtkinter.CTkFont(size=12),
            anchor="w"
        )
        self.label_offset.pack(pady=(7, 0), padx=20, anchor="w")
        self.label_offset_desc = customtkinter.CTkLabel(
            self,
            text="Offset from interval start",
            font=customtkinter.CTkFont(size=10),
            text_color="gray",
            anchor="w"
        )
        self.label_offset_desc.pack(pady=(0, 0), padx=20, anchor="w")
        self.entry_offset = customtkinter.CTkEntry(self, width=200)
        self.entry_offset.insert(0, default_offset)  # Pre-fill with default value
        self.entry_offset.pack(pady=(5, 10), padx=20, fill="x", anchor="w")

        # Set uniform button width and spacing
        button_pady = 10

        partition_icon = load_svg_image('assets/partition_evoked.svg', width=24, height=24)
        partition_icon_ctk = customtkinter.CTkImage(
            light_image=partition_icon,
            dark_image=partition_icon,
            size=(20, 20)
        )
        self.partition_button = customtkinter.CTkButton(
            self,
            image=partition_icon_ctk,
            compound="left",
            fg_color="#dbdbdb", 
            hover_color="#d5d9df",
            text="Partition",
            text_color="black",
            font=customtkinter.CTkFont(size=12, weight="bold"),
            command=self.on_calculate,
            height=40 
        )
        self.partition_button.pack(pady=(20, 10))

        export_icon = load_svg_image('assets/export_partitioned_data.svg', width=24, height=24)
        export_icon_ctk = customtkinter.CTkImage(
            light_image=export_icon,
            dark_image=export_icon,
            size=(20, 20)
        )
        self.export_button = customtkinter.CTkButton(
            self,
            image=export_icon_ctk,
            compound="left",
            fg_color="#dbdbdb", 
            hover_color="#d5d9df",
            text="Export",
            text_color="black",
            font=customtkinter.CTkFont(size=12, weight="bold"),
            command=self.export_stats,
            height=40 
        )
        self.export_button.pack(pady=button_pady)

        clear_icon = load_svg_image('assets/clear.svg', width=24, height=24)
        clear_icon_ctk = customtkinter.CTkImage(
            light_image=clear_icon,
            dark_image=clear_icon,
            size=(20, 20)
        )
        self.clear_button = customtkinter.CTkButton(
            self,
            image=clear_icon_ctk,
            compound="left",
            fg_color="#dbdbdb", 
            hover_color="#d5d9df",
            text="Clear",
            text_color="black",
            font=customtkinter.CTkFont(size=12, weight="bold"),
            command=self.clear_partition_lines,
            height=40 
        )
        self.clear_button.pack(pady=button_pady)        

        # Handle window close event
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_calculate(self):
        peak_num = self.entry_peak_num.get()
        interval_length = self.entry_interval_length.get()
        offset = self.entry_offset.get()
        
        if not peak_num or not interval_length or not offset:
            messagebox.showwarning(title="Warning", message="All fields must be filled out.", parent=self)
            return
            
        try:
            # Convert input values to integers
            peak_num = int(peak_num)
            interval_length = int(interval_length)
            offset = int(offset)
            
            # Save values without closing the dialog
            self.peak_num = peak_num
            self.interval_length = interval_length
            self.offset = offset
            
            # Call the method of the parent window to perform partitioning
            self.do_partition(peak_num, interval_length, offset)
            
        except ValueError:
            messagebox.showwarning(title="Warning", message="Invalid input values.", parent=self)

    def on_close(self):
        # When the user closes the dialog without confirming
        self.user_cancelled = True
        self.grab_release()
        self.destroy()

    def clear_partition_lines(self):
        # Clear all partition lines and labels
        for line in self.parent.partition_lines:
            line.remove()
        for label in self.parent.partition_labels:
            label.remove()
        self.parent.partition_lines.clear()
        self.parent.partition_labels.clear()
        self.parent.canvas.draw()
    
    def do_partition(self, peak_num, interval_size, offset):
        # Store the last used values
        self.parent.last_peak_num = str(peak_num)
        self.parent.last_interval_size = str(interval_size)
        self.parent.last_offset = str(offset)

        # Clear the previous partition lines and labels
        for line in self.parent.partition_lines:
            line.remove()
        for label in self.parent.partition_labels:
            label.remove() 
        self.parent.partition_lines.clear()
        self.parent.partition_labels.clear()

        # Group the peaks by peak_num
        valid_groups = []
        for i in range(0, len(self.parent.marked_peaks), peak_num):
            group = self.parent.marked_peaks[i:i+peak_num]
            if len(group) == peak_num:
                valid_groups.append(i)

        # Draw the interval lines
        for i in valid_groups:
            peak_time = self.parent.marked_peaks[i][0]
            start_peak = peak_time - offset
            end_peak = start_peak + interval_size

            if start_peak >= self.parent.time.iloc[0]:
                line = self.parent.ax.axvline(x=start_peak, color='g', linestyle='--')
                label = self.parent.ax.text(start_peak, self.parent.ax.get_ylim()[1] * 1.01, 
                                "Start {0}\n(x={1})".format(i // peak_num + 1, start_peak), color='g')
                self.parent.partition_lines.append(line)
                self.parent.partition_labels.append(label)

            if end_peak <= self.parent.time.iloc[-1]:
                line = self.parent.ax.axvline(x=end_peak, color='r', linestyle='--')
                label = self.parent.ax.text(end_peak, self.parent.ax.get_ylim()[1] * 1.01, 
                                "End {0}\n(x={1})".format(i // peak_num + 1, end_peak), color='r')
                self.parent.partition_lines.append(line)
                self.parent.partition_labels.append(label)

        # Update visibility
        xlims = self.parent.ax.get_xlim()
        for line, label in zip(self.parent.partition_lines, self.parent.partition_labels):
            x = line.get_xdata()[0]
            if xlims[0] <= x <= xlims[1]:
                line.set_visible(True)
                label.set_visible(True)
            else:
                line.set_visible(False)
                label.set_visible(False)

        self.parent.canvas.draw()

    def export_stats(self):
        if self.parent.time is None or not self.parent.marked_peaks:
            messagebox.showwarning(title="Warning", message="No stats to export.")
            return
            
        try:
            # Check if there are partition lines
            if len(self.parent.partition_lines) > 0:
                intervals = []
                # Get the data of each interval
                for i in range(0, len(self.parent.partition_lines), 2):
                    start = self.parent.partition_lines[i].get_xdata()[0]
                    if i + 1 < len(self.parent.partition_lines):
                        end = self.parent.partition_lines[i+1].get_xdata()[0]
                    else:
                        end = self.parent.time.iloc[-1]
                        
                    # Get the data of the interval
                    interval_data = self.parent.df_f[(self.parent.time >= start) & (self.parent.time <= end)].values
                    intervals.append(interval_data)
                
                # Find the longest interval length
                max_length = max(len(interval) for interval in intervals)
                
                # Pad all intervals to the same length with NaN
                padded_intervals = []
                for interval in intervals:
                    if len(interval) < max_length:
                        padded = np.pad(interval, (0, max_length - len(interval)), 
                                      mode='constant', constant_values=np.nan)
                    else:
                        padded = interval
                    padded_intervals.append(padded)
                
                # Calculate the average
                padded_intervals = np.array(padded_intervals)
                average_trace = np.nanmean(padded_intervals, axis=0)
                
                # Create a DataFrame
                df_data = {}
                for i in range(len(intervals)):
                    df_data[f'Interval_{i+1}'] = padded_intervals[i]
                df_data['Average'] = average_trace
                
                df = pd.DataFrame(df_data)
                
                # Export to Excel
                file_path = filedialog.asksaveasfilename(defaultextension='.xlsx',
                                                       filetypes=[("Excel files", "*.xlsx")])
                if file_path:
                    df.to_excel(file_path, index=False, engine='openpyxl')
                    messagebox.showinfo("Success", f"Data exported successfully to:\n{file_path}")
            else:
                messagebox.showwarning("Warning", "No partition data found.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error exporting data:\n{str(e)}")

class DetectPeaksDialog(customtkinter.CTkToplevel):
    def __init__(self, parent, peak_threshold="", min_distance="", width=""):
        super().__init__(parent)
        self.title("Peak Detection")  # Modify dialog title
        self.geometry("250x400")

        set_window_style(self)
        set_window_icon(self)

        # Set window position to the left of the main window
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        self.geometry(f"+{parent_x - 450}+{parent_y}")

        self.peak_threshold = None
        self.min_distance = None
        self.width = None
        self.user_cancelled = False

        # Peak Height (Required)
        self.label_threshold = customtkinter.CTkLabel(
            self, 
            text="Peak Height *",
            font=customtkinter.CTkFont(size=12),
            anchor="w"
        )
        self.label_threshold.pack(pady=(20, 0), padx=20, anchor="w")
        
        self.label_threshold_desc = customtkinter.CTkLabel(
            self,
            text="Detect peaks above this threshold (Required)",
            font=customtkinter.CTkFont(size=10),
            text_color="gray",
            anchor="w"
        )
        self.label_threshold_desc.pack(pady=(0, 0), padx=20, anchor="w")
        
        self.entry_threshold = customtkinter.CTkEntry(self, width=200)
        self.entry_threshold.insert(0, peak_threshold)
        self.entry_threshold.pack(pady=(5, 10), padx=20, anchor="w")

        # Min Distance
        self.label_distance = customtkinter.CTkLabel(
            self, 
            text="Min Distance",
            font=customtkinter.CTkFont(size=12),
            anchor="w"
        )
        self.label_distance.pack(pady=(5, 0), padx=20, anchor="w")
        
        self.label_distance_desc = customtkinter.CTkLabel(
            self,
            text="Minimum distance between peaks",
            font=customtkinter.CTkFont(size=10),
            text_color="gray",
            anchor="w"
        )
        self.label_distance_desc.pack(pady=(0, 0), padx=20, anchor="w")
        
        self.entry_distance = customtkinter.CTkEntry(self, width=200)
        self.entry_distance.insert(0, min_distance)  
        self.entry_distance.pack(pady=(5, 10), padx=20, anchor="w")

        # Width
        self.label_width = customtkinter.CTkLabel(
            self, 
            text="Width",
            font=customtkinter.CTkFont(size=12),
            anchor="w"
        )
        self.label_width.pack(pady=(5, 0), padx=20, anchor="w")
        
        self.label_width_desc = customtkinter.CTkLabel(
            self,
            text="Minimum width for each peak",
            font=customtkinter.CTkFont(size=10),
            text_color="gray",
            anchor="w"
        )
        self.label_width_desc.pack(pady=(0, 0), padx=20, anchor="w")
        
        self.entry_width = customtkinter.CTkEntry(self, width=200)
        self.entry_width.insert(0, width)
        self.entry_width.pack(pady=(5, 10), padx=20, anchor="w")

        detect_peaks_icon = load_svg_image('assets/magnifier.svg', width=24, height=24)
        detect_peaks_icon_ctk = customtkinter.CTkImage(
            light_image=detect_peaks_icon,
            dark_image=detect_peaks_icon,
            size=(20, 20)
        )
        self.detect_peaks_button = customtkinter.CTkButton(
            self,
            image=detect_peaks_icon_ctk,
            compound="left",
            fg_color="#dbdbdb", 
            hover_color="#d5d9df",
            text="Detect",
            text_color="black",
            font=customtkinter.CTkFont(size=12, weight="bold"),
            command=self.on_confirm,
            height=40 
        )
        self.detect_peaks_button.pack(pady=(10, 20), padx=20)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_confirm(self):
        self.peak_threshold = self.entry_threshold.get()
        self.min_distance = self.entry_distance.get()
        self.width = self.entry_width.get()

        if not self.peak_threshold:
            messagebox.showwarning(title="Warning", message="Peak height is required.", parent=self)
            return
        self.grab_release()
        self.destroy()

    def on_close(self):
        self.user_cancelled = True
        self.grab_release()
        self.destroy()
