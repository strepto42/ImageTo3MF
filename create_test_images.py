"""
Create a simple test image with 4 distinct colors for testing ImageTo3MF.
"""

from PIL import Image
import os

def create_test_image():
    """Create a 100x100 test image with 4 quadrants of different colors."""

    # Create a 100x100 RGB image
    img = Image.new('RGB', (100, 100))
    pixels = img.load()

    # Define 4 colors (red, green, blue, yellow)
    colors = [
        (255, 0, 0),      # Red - top-left
        (0, 255, 0),      # Green - top-right
        (0, 0, 255),      # Blue - bottom-left
        (255, 255, 0),    # Yellow - bottom-right
    ]

    # Fill quadrants
    for y in range(100):
        for x in range(100):
            if x < 50 and y < 50:
                pixels[x, y] = colors[0]  # Top-left: Red
            elif x >= 50 and y < 50:
                pixels[x, y] = colors[1]  # Top-right: Green
            elif x < 50 and y >= 50:
                pixels[x, y] = colors[2]  # Bottom-left: Blue
            else:
                pixels[x, y] = colors[3]  # Bottom-right: Yellow

    # Add a small circle in the center using a different shade
    center_x, center_y = 50, 50
    radius = 15
    for y in range(100):
        for x in range(100):
            if (x - center_x) ** 2 + (y - center_y) ** 2 < radius ** 2:
                # White center circle
                pixels[x, y] = (255, 255, 255)

    # Save the image
    output_path = os.path.join(os.path.dirname(__file__), 'test_image.png')
    img.save(output_path)
    print(f"Test image saved to: {output_path}")
    return output_path


def create_test_image_with_transparency():
    """Create a 100x100 test image with transparent background and 4 colored shapes."""

    # Create a 100x100 RGBA image with transparent background
    img = Image.new('RGBA', (100, 100), (0, 0, 0, 0))  # Fully transparent
    pixels = img.load()

    # Define 4 colors (red, green, blue, yellow) with full opacity
    colors = [
        (255, 0, 0, 255),      # Red
        (0, 255, 0, 255),      # Green
        (0, 0, 255, 255),      # Blue
        (255, 255, 0, 255),    # Yellow
    ]

    # Draw 4 circles in corners (leaving transparent background)
    centers = [
        (25, 25),   # Top-left: Red
        (75, 25),   # Top-right: Green
        (25, 75),   # Bottom-left: Blue
        (75, 75),   # Bottom-right: Yellow
    ]
    radius = 20

    for y in range(100):
        for x in range(100):
            for i, (cx, cy) in enumerate(centers):
                if (x - cx) ** 2 + (y - cy) ** 2 < radius ** 2:
                    pixels[x, y] = colors[i]
                    break

    # Save the image
    output_path = os.path.join(os.path.dirname(__file__), 'test_transparent.png')
    img.save(output_path)
    print(f"Transparent test image saved to: {output_path}")
    return output_path


def create_logo_test_image():
    """Create a more complex test image resembling a simple logo."""

    # Create a 200x100 RGB image with white background
    img = Image.new('RGB', (200, 100), (255, 255, 255))
    pixels = img.load()

    # Colors
    black = (0, 0, 0)
    red = (220, 50, 50)
    blue = (50, 100, 200)

    # Draw a simple "3MF" text-like pattern
    # Letter 3 (left side)
    for y in range(20, 80):
        for x in range(20, 60):
            # Top horizontal
            if 20 <= y <= 25 and 25 <= x <= 55:
                pixels[x, y] = black
            # Middle horizontal
            elif 47 <= y <= 53 and 25 <= x <= 55:
                pixels[x, y] = black
            # Bottom horizontal
            elif 75 <= y <= 80 and 25 <= x <= 55:
                pixels[x, y] = black
            # Right vertical top
            elif 50 <= x <= 55 and 20 <= y <= 53:
                pixels[x, y] = black
            # Right vertical bottom
            elif 50 <= x <= 55 and 47 <= y <= 80:
                pixels[x, y] = black

    # Letter M (middle) in red
    for y in range(20, 80):
        for x in range(70, 130):
            # Left vertical
            if 70 <= x <= 77 and 20 <= y <= 80:
                pixels[x, y] = red
            # Right vertical
            elif 123 <= x <= 130 and 20 <= y <= 80:
                pixels[x, y] = red
            # Left diagonal
            elif 77 <= x <= 100:
                target_y = 20 + (x - 77) * 2
                if abs(y - target_y) < 5 and y < 60:
                    pixels[x, y] = red
            # Right diagonal
            elif 100 <= x <= 123:
                target_y = 65 - (x - 100) * 2
                if abs(y - target_y) < 5 and y < 60:
                    pixels[x, y] = red

    # Letter F (right side) in blue
    for y in range(20, 80):
        for x in range(145, 185):
            # Left vertical
            if 145 <= x <= 152 and 20 <= y <= 80:
                pixels[x, y] = blue
            # Top horizontal
            elif 20 <= y <= 27 and 145 <= x <= 185:
                pixels[x, y] = blue
            # Middle horizontal
            elif 47 <= y <= 54 and 145 <= x <= 175:
                pixels[x, y] = blue

    # Save the image
    output_path = os.path.join(os.path.dirname(__file__), 'test_logo.png')
    img.save(output_path)
    print(f"Logo test image saved to: {output_path}")
    return output_path


if __name__ == '__main__':
    create_test_image()
    create_test_image_with_transparency()
    create_logo_test_image()
    print("\nTest images created! Run 'python main.py test_transparent.png' to test transparency.")

