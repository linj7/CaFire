import io
import os
import sys
import cairosvg
from PIL import Image

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