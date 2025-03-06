"""
Event handling function module
Contains functions for processing UI events and interactions
"""

def on_button_press(app, label):
    """
    Simulate the visual effect of a button press
    
    Args:
        app: The application instance
        label: The label control that was pressed
    """
    # Simulate the visual effect by moving the label
    current_place_info = label.place_info()
    x = int(current_place_info['x'])
    y = int(current_place_info['y'])
    label.place_configure(x=x + 1, y=y + 1)

def on_button_release(app, label, func):
    """
    Handle the button release event
    
    Args:
        app: The application instance
        label: The label control that was released
        func: The function to execute after release
    """
    current_place_info = label.place_info()
    x = int(current_place_info['x'])
    y = int(current_place_info['y'])
    label.place_configure(x=x - 1, y=y - 1)
    func()

def on_enter_axes(app, event):
    """
    Called when the mouse enters the chart area
    
    Args:
        app: The application instance
        event: The event object
    """
    app.canvas_widget.configure(cursor="hand2")

def on_leave_axes(app, event):
    """
    Called when the mouse leaves the chart area
    
    Args:
        app: The application instance
        event: The event object
    """
    app.canvas_widget.configure(cursor="")

def apply_event_handlers(app_class):
    """
    Apply event handling functions to the application class
    
    Args:
        app_class: The application class
    """
    app_class.on_button_press = on_button_press
    app_class.on_button_release = on_button_release
    app_class.on_enter_axes = on_enter_axes
    app_class.on_leave_axes = on_leave_axes