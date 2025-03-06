import tkinter
import customtkinter
from PIL import Image, ImageDraw, ImageTk

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        # Get button position and size
        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 5  # Show on right side, offset 5 pixels
        y = self.widget.winfo_rooty() + self.widget.winfo_height()//2  # Center vertically
        self.tip_window = tw = tkinter.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tkinter.Label(tw, text=self.text, justify='left',
                         background="#f4f4f3", relief='solid', borderwidth=1,
                         font=("tahoma", "15", "normal"))
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

class SegmentedProgressBar(customtkinter.CTkFrame):
    def __init__(self, master, segments=4, **kwargs):
        super().__init__(
            master, 
            fg_color="transparent",  # Set to transparent
            **kwargs
        )
        
        # Create segments progress blocks
        self.segments = []
        for i in range(segments):
            segment = customtkinter.CTkLabel(
                self,
                text="",
                width=12,         
                height=8,
                fg_color="#dddddd",  # Initial white
                corner_radius=0   
            )
            segment.pack(side="left", padx=1.3)  # Keep small square spacing
            self.segments.append(segment)
            
    def set(self, value):
        """
        Set progress, value range is 0-1
        """
        total_segments = len(self.segments)
        active_segments = int(value * total_segments)
        
        # Update segments display
        for i in range(total_segments):
            if i < active_segments:
                self.segments[i].configure(fg_color="black")  # Activated segment turns black
            else:
                self.segments[i].configure(fg_color="#dddddd")  # Inactive segment remains white
                
