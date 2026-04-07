"""
Color selection and quantization module for ImageTo3MF.
Handles color picking, tolerance-based mapping, and image quantization.
"""

import numpy as np
from PIL import Image
from typing import List, Tuple, Optional


def get_pixel_color(img: Image.Image, x: int, y: int) -> Tuple[int, int, int]:
    """
    Get the RGB color at a specific pixel location.

    Args:
        img: PIL Image object
        x: X coordinate
        y: Y coordinate

    Returns:
        Tuple of (R, G, B) values
    """
    if x < 0 or x >= img.width or y < 0 or y >= img.height:
        raise ValueError(f"Coordinates ({x}, {y}) out of bounds for image size ({img.width}, {img.height})")

    pixel = img.getpixel((x, y))
    if isinstance(pixel, int):  # Grayscale
        return (pixel, pixel, pixel)
    return pixel[:3]  # Return RGB, ignore alpha if present


def is_pixel_transparent(img: Image.Image, x: int, y: int, threshold: int = 128) -> bool:
    """
    Check if a pixel is transparent (alpha below threshold).

    Args:
        img: PIL Image object (RGBA mode)
        x: X coordinate
        y: Y coordinate
        threshold: Alpha value below which pixel is considered transparent (0-255)

    Returns:
        True if pixel is transparent
    """
    if img.mode != 'RGBA':
        return False
    
    pixel = img.getpixel((x, y))
    return pixel[3] < threshold


def color_distance(c1: Tuple[int, int, int], c2: Tuple[int, int, int]) -> float:
    """
    Calculate Euclidean distance between two colors in RGB space.

    Args:
        c1: First color as (R, G, B)
        c2: Second color as (R, G, B)

    Returns:
        Euclidean distance
    """
    return np.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def find_nearest_color(
    pixel: Tuple[int, int, int],
    colors: List[Tuple[int, int, int]],
    tolerance: float = 255.0
) -> Tuple[int, float]:
    """
    Find the nearest color from a list of colors.

    Args:
        pixel: The pixel color as (R, G, B)
        colors: List of target colors
        tolerance: Maximum distance to consider a match

    Returns:
        Tuple of (color_index, distance). Index is -1 if no color within tolerance.
    """
    if not colors:
        return -1, float('inf')

    min_dist = float('inf')
    min_idx = -1

    for i, color in enumerate(colors):
        dist = color_distance(pixel, color)
        if dist < min_dist:
            min_dist = dist
            min_idx = i

    if min_dist > tolerance:
        return -1, min_dist

    return min_idx, min_dist


def quantize_image(
    img: Image.Image,
    colors: List[Tuple[int, int, int]],
    tolerance: float = 100.0,
    assign_nearest: bool = True
) -> Tuple[np.ndarray, Image.Image]:
    """
    Quantize an image to the specified colors.

    Args:
        img: PIL Image object
        colors: List of target colors (up to 4)
        tolerance: Maximum color distance for matching
        assign_nearest: If True, assign to nearest color even if outside tolerance

    Returns:
        Tuple of (color_map array, quantized preview image)
        color_map[y, x] contains the index of the assigned color (0-3), or -1 for unassigned
    """
    if not colors:
        raise ValueError("At least one color must be specified")

    # Convert image to numpy array
    img_array = np.array(img)
    height, width = img_array.shape[:2]

    # Initialize color map (-1 means unassigned)
    color_map = np.full((height, width), -1, dtype=np.int8)

    # Create output image array
    output_array = np.zeros((height, width, 3), dtype=np.uint8)

    # Convert colors to numpy array for vectorized operations
    colors_array = np.array(colors, dtype=np.float32)

    # Process each pixel
    for y in range(height):
        for x in range(width):
            pixel = tuple(img_array[y, x, :3])

            # Find nearest color
            idx, dist = find_nearest_color(pixel, colors, tolerance)

            if idx >= 0 or assign_nearest:
                if idx < 0:
                    # Find absolute nearest if we're assigning anyway
                    idx, _ = find_nearest_color(pixel, colors, float('inf'))

                color_map[y, x] = idx
                output_array[y, x] = colors[idx]
            else:
                # Leave as black/unassigned
                output_array[y, x] = [128, 128, 128]  # Gray for unassigned

    quantized_img = Image.fromarray(output_array, mode='RGB')
    return color_map, quantized_img


def quantize_image_fast(
    img: Image.Image,
    colors: List[Tuple[int, int, int]],
    tolerance: float = 100.0,
    assign_nearest: bool = True,
    alpha_threshold: int = 128
) -> Tuple[np.ndarray, Image.Image]:
    """
    Fast vectorized version of quantize_image.
    Handles transparency - transparent pixels are marked as -1 (unassigned).

    Args:
        img: PIL Image object (RGB or RGBA)
        colors: List of target colors (up to 4)
        tolerance: Maximum color distance for matching
        assign_nearest: If True, assign to nearest color even if outside tolerance
        alpha_threshold: Alpha value below which pixels are considered transparent (0-255)

    Returns:
        Tuple of (color_map array, quantized preview image)
        color_map[y, x] = -1 for transparent/unassigned pixels
    """
    if not colors:
        raise ValueError("At least one color must be specified")

    # Convert image to numpy array
    img_array = np.array(img, dtype=np.float32)
    height, width = img_array.shape[:2]

    # Check for alpha channel
    has_alpha = img.mode == 'RGBA' and img_array.shape[2] == 4

    # Convert colors to numpy array
    colors_array = np.array(colors, dtype=np.float32)
    num_colors = len(colors)

    # Reshape for broadcasting: (H, W, 1, 3) - (1, 1, N, 3) = (H, W, N, 3)
    img_expanded = img_array[:, :, np.newaxis, :3]
    colors_expanded = colors_array[np.newaxis, np.newaxis, :, :]

    # Calculate distances to each color
    distances = np.sqrt(np.sum((img_expanded - colors_expanded) ** 2, axis=3))

    # Find nearest color for each pixel
    nearest_idx = np.argmin(distances, axis=2)
    min_distances = np.min(distances, axis=2)

    # Create color map
    color_map = nearest_idx.astype(np.int8)

    # Mark pixels outside tolerance if not assigning nearest
    if not assign_nearest:
        outside_tolerance = min_distances > tolerance
        color_map[outside_tolerance] = -1

    # Mark transparent pixels as unassigned (-1)
    if has_alpha:
        alpha_channel = img_array[:, :, 3]
        transparent_mask = alpha_channel < alpha_threshold
        color_map[transparent_mask] = -1

    # Create output image (RGBA to show transparency)
    output_array = np.zeros((height, width, 4), dtype=np.uint8)

    for i, color in enumerate(colors):
        mask = color_map == i
        output_array[mask, :3] = color
        output_array[mask, 3] = 255  # Fully opaque

    # Handle unassigned pixels (transparent in preview)
    unassigned = color_map == -1
    output_array[unassigned] = [128, 128, 128, 100]  # Semi-transparent gray

    quantized_img = Image.fromarray(output_array, mode='RGBA')
    return color_map, quantized_img


def get_color_regions(color_map: np.ndarray, color_index: int) -> np.ndarray:
    """
    Extract a binary mask for a specific color index.

    Args:
        color_map: The color map array from quantize_image
        color_index: Index of the color (0-3)

    Returns:
        Binary numpy array where 1 = pixel belongs to this color
    """
    return (color_map == color_index).astype(np.uint8)


def color_to_hex(color: Tuple[int, int, int]) -> str:
    """Convert RGB tuple to hex string."""
    return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"


def hex_to_color(hex_str: str) -> Tuple[int, int, int]:
    """Convert hex string to RGB tuple."""
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

