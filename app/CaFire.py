import customtkinter 
from tkinter import messagebox

from ui.main_window import setup_ui
from ui.window import set_window_style
from ui.event_handlers import apply_event_handlers
from ui.widgets import Tooltip, SegmentedProgressBar
from ui.dialogs import LoadFileDialog, DetectPeaksDialog, PartitionEvokedDialog
from utils.image_utils import load_svg_image
from utils.navigation_utils import apply_navigation_operations
from utils.table_operations_utils import apply_table_operations
from core.event_handlers import handle_canvas_click
from core.app_state import initialize_app_state, clear_plot
from core.apply_threshold import apply_threshold
from core.calculate_rise import calculate_rise
from core.calculate_decay import calculate_decay
from core.calculate_baseline import calculate_baseline

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        setup_ui(self)
        initialize_app_state(self)

    def detect_peaks(self):
        if self.time is None or self.df_f is None:
            messagebox.showwarning(title="Warning", message="No data loaded.")
            return
        
        self.progress_bar.set(0)

        # Step 1: Apply threshold to find all peaks
        apply_threshold(self)

        # Step 2: Calculate rise time for the detected peaks and plot the rise fit curve
        calculate_rise(self)

        # Step 3: Calculate decay time for the detected peaks and plot the decay fit curve
        calculate_decay(self)

        self.after(500, lambda: self.progress_bar.set(0))
    
    def handle_partition(self):
        if self.time is None or self.df_f is None:
            messagebox.showwarning(title="Warning", message="No data loaded.")
            return

        # Check if there are marked peaks
        if not hasattr(self, 'marked_peaks') or not self.marked_peaks:
            messagebox.showwarning(title="Warning", message="No peaks detected. Please identify peaks before partitioning.")
            return

        # Show the PartitionEvokedDialog
        partition_dialog = PartitionEvokedDialog(
            self,
            default_peak_num=self.last_peak_num,
            default_interval_size=self.last_interval_size,
            default_offset=self.last_offset
        )
                
        # # Clear previous partition lines and labels
        # for line in self.partition_lines:
        #     line.remove()
        # for label in self.partition_labels:
        #     label.remove()
        # self.partition_lines.clear()
        # self.partition_labels.clear()
    
apply_event_handlers(App)
apply_table_operations(App)
apply_navigation_operations(App)
