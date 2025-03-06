"""
Navigation and zooming tool functions
This module contains functions for chart navigation and zooming
"""

def next_page(app):
    """
    Move the chart to the right by one page
    
    Args:
        app: The application instance
    """
    if app.time is not None:
        xlims = app.ax.get_xlim()
        range_width = xlims[1] - xlims[0]
        new_xlims = [xlims[0] + range_width, xlims[1] + range_width]
        app.ax.set_xlim(new_xlims)
        update_annotations(app)
        app.canvas.draw()

def prev_page(app):
    """
    Move the chart to the left by one page
    
    Args:
        app: The application instance
    """
    if app.time is not None:
        xlims = app.ax.get_xlim()
        range_width = xlims[1] - xlims[0]
        new_xlims = [xlims[0] - range_width, xlims[1] - range_width]
        app.ax.set_xlim(new_xlims)
        update_annotations(app)
        app.canvas.draw()

def move_up(app):
    """
    Move the chart up by one page
    
    Args:
        app: The application instance
    """
    if app.time is not None:
        ylims = app.ax.get_ylim()
        range_height = ylims[1] - ylims[0]
        shift = range_height * 0.1  # Shift up by 10% of the current range
        new_ylims = [ylims[0] + shift, ylims[1] + shift]
        app.ax.set_ylim(new_ylims)
        update_annotations(app)
        app.canvas.draw()

def move_down(app):
    """
    Move the chart down by one page
    
    Args:
        app: The application instance
    """
    if app.time is not None:
        ylims = app.ax.get_ylim()
        range_height = ylims[1] - ylims[0]
        shift = range_height * 0.1  # Shift down by 10% of the current range
        new_ylims = [ylims[0] - shift, ylims[1] - shift]
        app.ax.set_ylim(new_ylims)
        update_annotations(app)
        app.canvas.draw()

def zoom_in_x(app):
    """
    Zoom in on the X-axis
    
    Args:
        app: The application instance
    """
    if app.time is not None:
        xlims = app.ax.get_xlim()
        new_xlims = [xlims[0] + (xlims[1] - xlims[0]) * 0.1, xlims[1] - (xlims[1] - xlims[0]) * 0.1]
        app.ax.set_xlim(new_xlims)
        update_annotations(app)
        app.canvas.draw()

def zoom_out_x(app):
    """
    Zoom out on the X-axis
    
    Args:
        app: The application instance
    """
    if app.time is not None:
        xlims = app.ax.get_xlim()
        new_xlims = [xlims[0] - (xlims[1] - xlims[0]) * 0.1, xlims[1] + (xlims[1] - xlims[0]) * 0.1]
        app.ax.set_xlim(new_xlims)
        update_annotations(app)
        app.canvas.draw()

def zoom_in_y(app):
    """
    Zoom in on the Y-axis
    
    Args:
        app: The application instance
    """
    if app.df_f is not None:
        ylims = app.ax.get_ylim()
        new_ylims = [ylims[0] + (ylims[1] - ylims[0]) * 0.1, ylims[1] - (ylims[1] - ylims[0]) * 0.1]
        app.ax.set_ylim(new_ylims)
        update_annotations(app)
        app.canvas.draw()

def zoom_out_y(app):
    """
    Zoom out on the Y-axis
    
    Args:
        app: The application instance
    """
    if app.df_f is not None:
        ylims = app.ax.get_ylim()
        new_ylims = [ylims[0] - (ylims[1] - ylims[0]) * 0.1, ylims[1] + (ylims[1] - ylims[0]) * 0.1]
        app.ax.set_ylim(new_ylims)
        update_annotations(app)
        app.canvas.draw()

def update_annotations(app):
    """
    Update the annotations on the chart, showing or hiding them based on the current view range
    
    Args:
        app: The application instance
    """
    xlims = app.ax.get_xlim()
    ylims = app.ax.get_ylim()

    for point, text in zip(app.points, app.texts):
        x, y = point.get_xdata()[0], point.get_ydata()[0]
        if xlims[0] <= x <= xlims[1] and ylims[0] <= y <= ylims[1]:  # Check if the point is within the current view range
            point.set_visible(True)
            text.set_visible(True)
        else:
            point.set_visible(False)
            text.set_visible(False)

    for line, label in zip(app.partition_lines, app.partition_labels):
        x = line.get_xdata()[0]
        if xlims[0] <= x <= xlims[1]:
            line.set_visible(True)
            label.set_visible(True)
        else:
            line.set_visible(False)
            label.set_visible(False)

def apply_navigation_operations(app_class):
    """
    Apply the table operation functions to the application class
    
    Args:
        app_class: The application class
    """
    app_class.next_page = next_page
    app_class.prev_page = prev_page
    app_class.move_up = move_up
    app_class.move_down = move_down
    app_class.zoom_in_x = zoom_in_x
    app_class.zoom_in_y = zoom_in_y
    app_class.zoom_out_x = zoom_out_x
    app_class.zoom_out_y = zoom_out_y