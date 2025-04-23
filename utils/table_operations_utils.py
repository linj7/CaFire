"""
Table operation function module
Contains functions for handling table selection, copying, exporting, and event handling
"""
import pandas as pd
from PIL import Image, ImageDraw, ImageTk
from tkinter import messagebox, filedialog
from core.calculate_decay import calculate_decay

def get_checkbox_image(app, checked=False):
    """
    Get the checkbox image
    
    Args:
        app: The application instance
        checked: Whether the checkbox is checked
    
    Returns:
        ImageTk.PhotoImage: The checkbox image
    """
    if not hasattr(app, '_checkbox_images'):
        app._checkbox_images = {}
        
    if checked not in app._checkbox_images:
        # Create the checkbox image
        size = 20
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        
        # Draw the border
        d.rectangle([2, 2, size-3, size-3], outline='#666666', width=1)
        
        if checked:
            # Draw the checkmark
            d.line([4, size//2, size//2-2, size-6], fill='#000000', width=2)
            d.line([size//2-2, size-6, size-4, 4], fill='#000000', width=2)
        
        app._checkbox_images[checked] = ImageTk.PhotoImage(img)
    
    return app._checkbox_images[checked]

def select_all_rows(app):
    """
    Select all rows in the table
    
    Args:
        app: The application instance
    """
    for item in app.tree.get_children():
        app.tree.item(item, tags=("checked",), image=app.checked_image)
        app.tree.selection_add(item)

def copy_selected_data(app):
    """
    Copy the selected data to the clipboard
    
    Args:
        app: The application instance
    """
    # Get all the checked items
    checked_items = []
    for item in app.tree.get_children():
        # Check if the item is checked using the tag
        if 'checked' in app.tree.item(item, 'tags'):
            checked_items.append(item)
            
    if not checked_items:
        messagebox.showwarning("Warning", "Please check the items you want to copy.")
        return
    
    try:
        data_text = ""
        columns = app.tree["columns"]
        header = "\t".join(columns)
        data_text += header + "\n"

        for item in checked_items:
            values = app.tree.item(item)["values"]
            row = "\t".join(str(value) for value in values)
            data_text += row + "\n"
        
        app.clipboard_clear()
        app.clipboard_append(data_text)
        messagebox.showinfo("Success", "Data copied to clipboard.")
        
    except Exception as e:
        messagebox.showerror("Error", f"Copy failed:\n{str(e)}")

def export_selected_data(app):
    """
    Export the selected data to an Excel file
    
    Args:
        app: The application instance
    """
    # Get all the checked items
    checked_items = []
    for item in app.tree.get_children():
        # Check if the item is checked using the tag
        if 'checked' in app.tree.item(item, 'tags'):
            checked_items.append(item)
            
    if not checked_items:
        messagebox.showwarning("Warning", "Please check the items you want to export.")
        return
    
    try:
        # Select the save path
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        if not file_path:  # User cancelled the save
            return
        
        # Create a DataFrame
        data = []
        columns = app.tree["columns"]
        
        for item in checked_items:
            values = app.tree.item(item)["values"]
            data.append(values)
        
        df = pd.DataFrame(data, columns=columns)
        
        # Save to Excel
        df.to_excel(file_path, index=False)
        messagebox.showinfo("Success", f"Data exported successfully to:\n{file_path}")
        
    except Exception as e:
        messagebox.showerror("Error", f"Export failed:\n{str(e)}")

def handle_checkbox_click(app, event):
    """
    Handle the checkbox click event
    
    Args:
        app: The application instance
        event: The event object
    """
    region = app.tree.identify_region(event.x, event.y)
    if region == "tree":  # Clicked on the tree column area
        item = app.tree.identify_row(event.y)
        if item:
            # Toggle the selected state
            is_checked = app.tree.set(item, "checked")
            if is_checked == "True":
                app.tree.set(item, "checked", False)
                app.tree.selection_remove(item)
                app.tree.item(item, image=app.get_checkbox_image(False))
            else:
                app.tree.set(item, "checked", True)
                app.tree.selection_add(item)
                app.tree.item(item, image=app.get_checkbox_image(True))
            return "break"  # Prevent the event from propagating

def handle_tree_click(app, event):
    """
    Handle the table click event
    
    Args:
        app: The application instance
        event: The event object
    """
    region = app.tree.identify_region(event.x, event.y)
    if region == "tree":
        item = app.tree.identify_row(event.y)
        if item:
            # Toggle the selected state
            current_tags = app.tree.item(item, 'tags')
            if current_tags and 'checked' in current_tags:
                # Uncheck
                app.tree.item(item, image=app.unchecked_image, tags=())
            else:
                # Check
                app.tree.item(item, image=app.checked_image, tags=('checked',))

def handle_tree_right_click(app, event):
    """
    Handle the table right-click event
    
    Args:
        app: The application instance
        event: The event object
    """
    region = app.tree.identify_region(event.x, event.y)
    column = app.tree.identify_column(event.x)
    
    # Check if the click is on the column header
    if region == "heading":
        # Get the column name
        column_id = int(column.replace('#', ''))
        if column_id > 0 and column_id <= len(app.tree["columns"]):
            column_name = app.tree["columns"][column_id - 1]
            
            # If the column is Decay Time, show the context menu
            if column_name == "Decay Time":
                app.right_clicked_column = column_name
                app.context_menu.post(event.x_root, event.y_root)
    
    return "break"  # Prevent the event from propagating
    
def update_table(app):
    # Clear the table
    for item in app.tree.get_children():
        app.tree.delete(item)
    
    # Get all peaks data and sort
    peaks_data = []
    for peak_time, peak_value in app.marked_peaks:
        rise_time = app.rise_times.get((peak_time, peak_value), "N/A")
        decay_time = app.tau_values.get((peak_time, peak_value), "N/A")
        
        # Get the baseline
        peak_index = app.time[app.time == peak_time].index[0]
        if app.baseline_values is not None and peak_index < len(app.baseline_values):
            baseline = app.baseline_values[peak_index]
            # Calculate ΔF/F
            if app.convert_to_df_f == True:
                delta_f_f = peak_value
            else: 
                delta_f_f = (peak_value - baseline) / baseline
        else:
            baseline = "N/A"
            delta_f_f = "N/A"

        peaks_data.append((
            f"{int(peak_time)}",
            f"{peak_value:.6f}",
            f"{rise_time:.6f}" if isinstance(rise_time, float) else rise_time,
            f"{decay_time:.6f}" if isinstance(decay_time, float) else decay_time,
            f"{baseline:.6f}" if isinstance(baseline, float) else baseline,
            f"{delta_f_f:.6f}" if isinstance(delta_f_f, float) else delta_f_f
        ))
    
    # Sort by time
    peaks_data.sort(key=lambda x: float(x[0]))
    
    # Add to the table, default display blank checkbox
    for data in peaks_data:
        app.tree.insert("", "end", text="", values=data, image=app.unchecked_image)

def recalculate_column(app):
    """Recalculate the selected column"""
    if hasattr(app, 'right_clicked_column') and app.right_clicked_column == "Decay Time":
        # Clear all decay curves
        for line in app.decay_lines:
            line.remove()
        app.decay_lines.clear()
        app.decay_line_map.clear()
        
        # Recalculate the decay time of all peaks
        app.decay_calculated = [False] * len(app.marked_peaks)
        calculate_decay(app)
        app.update_table()
        messagebox.showinfo("Success", "Decay Time recalculated successfully.")
        app.after(500, lambda: app.progress_bar.set(0))


def apply_table_operations(app_class):
    """
    Apply the table operation functions to the application class
    
    Args:
        app_class: The application class
    """
    app_class.select_all_rows = select_all_rows
    app_class.copy_selected_data = copy_selected_data
    app_class.export_selected_data = export_selected_data
    app_class.handle_checkbox_click = handle_checkbox_click
    app_class.handle_tree_click = handle_tree_click
    app_class.handle_tree_right_click = handle_tree_right_click
    app_class.get_checkbox_image = get_checkbox_image
    app_class.recalculate_column = recalculate_column
    app_class.update_table = update_table