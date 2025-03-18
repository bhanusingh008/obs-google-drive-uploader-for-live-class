"""
Script to generate the application icon.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import os


def generate_icon():
    """Generate the application icon."""
    # Create a 256x256 image with a blue background
    size = 256
    image = Image.new('RGBA', (size, size), (33, 150, 243, 255))
    draw = ImageDraw.Draw(image)
    
    # Draw a white circle
    margin = 20
    draw.ellipse([margin, margin, size - margin, size - margin], 
                 fill=(255, 255, 255, 255))
    
    # Draw an up arrow
    arrow_color = (33, 150, 243, 255)
    center_x = size // 2
    center_y = size // 2
    arrow_size = size // 3
    
    # Draw the arrow shaft
    shaft_width = size // 8
    shaft_height = arrow_size // 2
    draw.rectangle([
        center_x - shaft_width // 2,
        center_y + shaft_height // 2,
        center_x + shaft_width // 2,
        center_y + arrow_size // 2
    ], fill=arrow_color)
    
    # Draw the arrow head
    points = [
        (center_x, center_y - arrow_size // 2),  # Top point
        (center_x - arrow_size // 3, center_y + shaft_height // 2),  # Left point
        (center_x + arrow_size // 3, center_y + shaft_height // 2),  # Right point
    ]
    draw.polygon(points, fill=arrow_color)
    
    # Save the icon
    icon_path = Path(__file__).parent.parent / "resources" / "icon.ico"
    icon_path.parent.mkdir(exist_ok=True)
    image.save(icon_path, format='ICO')


if __name__ == "__main__":
    generate_icon() 