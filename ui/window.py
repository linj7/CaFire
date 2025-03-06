import os
import sys
import customtkinter
from tkinter import messagebox
from utils.image_utils import load_svg_image
from ctypes import windll, byref, sizeof, c_int

def set_window_style(window, title_bar_color=0xdddddd, title_text_color=0x666666):
    """
    Set window title bar style, including background color, button color and text color
    
    Args:
        window: Tkinter window object
        title_bar_color: Title bar background color (hexadecimal)
        title_text_color: Title bar text color (hexadecimal)
    """
    try:
        HWND = windll.user32.GetParent(window.winfo_id())
        
        # Set title bar background color
        windll.dwmapi.DwmSetWindowAttribute(
            HWND, 
            34,  # DWMWA_CAPTION_COLOR
            byref(c_int(title_bar_color)), 
            sizeof(c_int)
        )
        
        # Set title bar button background color
        windll.dwmapi.DwmSetWindowAttribute(
            HWND, 
            35,  # DWMWA_CAPTION_BUTTON_COLOR
            byref(c_int(title_bar_color)), 
            sizeof(c_int)
        )
        
        # Set title bar text color
        windll.dwmapi.DwmSetWindowAttribute(
            HWND, 
            36,  # DWMWA_TEXT_COLOR
            byref(c_int(title_text_color)), 
            sizeof(c_int)
        )
        return True
    except:
        # If setting fails (e.g. on non-Windows systems), ignore the error
        return False

def set_window_icon(window, icon_name="ecg_icon.ico"):
    """
    Set window icon
    
    Args:
        window: Tkinter window object
        icon_name: Icon file name (located in the assets directory)
    """
    try:
        if getattr(sys, 'frozen', False):
            # If it's a packaged executable
            base_path = sys._MEIPASS
        else:
            # If it's a development environment
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        icon_path = os.path.join(base_path, 'assets', icon_name)
        
        if os.path.exists(icon_path):
            # Directly set
            try:
                window.iconbitmap(icon_path)
            except Exception as e:
                print(f"Error setting icon: {e}")
            
            # Delay setting (as a backup method)
            window.after(200, lambda: window.iconbitmap(icon_path))
            return True
    except Exception as e:
        print(f"Error setting icon: {e}")
    return False