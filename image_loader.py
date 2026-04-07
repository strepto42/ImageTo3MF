"""
Image loading and validation module for ImageTo3MF.
Handles PNG/JPG image loading, validation, and resizing.
"""

from PIL import Image
import os
from typing import Optional, Tuple


SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg'}
MAX_DIMENSION = 1000  # Maximum dimension before offering resize


def validate_image_path(path: str) -> Tuple[bool, str]:
    """
    Validate that the path points to a supported image file.

    Args:
        path: Path to the image file

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path:
        return False, "No file path provided"

    if not os.path.exists(path):
        return False, f"File not found: {path}"

    ext = os.path.splitext(path)[1].lower()
    if ext not in SUPPORTED_FORMATS:
        return False, f"Unsupported format: {ext}. Supported: {', '.join(SUPPORTED_FORMATS)}"

    return True, ""


def load_image(path: str, preserve_alpha: bool = True) -> Optional[Image.Image]:
    """
    Load an image from the given path.

    Args:
        path: Path to the image file
        preserve_alpha: If True, keep RGBA mode for transparent PNGs

    Returns:
        PIL Image object or None if loading fails
    """
    is_valid, error = validate_image_path(path)
    if not is_valid:
        raise ValueError(error)

    try:
        img = Image.open(path)

        # Handle different image modes
        if img.mode == 'RGBA':
            if preserve_alpha:
                # Keep RGBA to preserve transparency information
                return img
            else:
                # Composite on white background (loses transparency)
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                return background
        elif img.mode == 'RGB':
            return img
        elif img.mode == 'P':
            # Palette mode - may have transparency
            if 'transparency' in img.info:
                img = img.convert('RGBA')
                if preserve_alpha:
                    return img
                else:
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])
                    return background
            else:
                return img.convert('RGB')
        elif img.mode == 'LA':
            # Grayscale with alpha
            img = img.convert('RGBA')
            if preserve_alpha:
                return img
            else:
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                return background
        else:
            # Other modes (L, 1, etc.) - convert to RGB
            return img.convert('RGB')
    except Exception as e:
        raise ValueError(f"Failed to load image: {str(e)}")


def needs_resize(img: Image.Image) -> bool:
    """
    Check if image exceeds maximum recommended dimensions.

    Args:
        img: PIL Image object

    Returns:
        True if image should be resized
    """
    return img.width > MAX_DIMENSION or img.height > MAX_DIMENSION


def resize_image(img: Image.Image, max_dimension: int = MAX_DIMENSION) -> Image.Image:
    """
    Resize image to fit within max_dimension while maintaining aspect ratio.

    Args:
        img: PIL Image object
        max_dimension: Maximum width or height

    Returns:
        Resized PIL Image object
    """
    if img.width <= max_dimension and img.height <= max_dimension:
        return img

    ratio = min(max_dimension / img.width, max_dimension / img.height)
    new_size = (int(img.width * ratio), int(img.height * ratio))
    return img.resize(new_size, Image.Resampling.LANCZOS)


def get_image_info(img: Image.Image) -> dict:
    """
    Get information about the image.

    Args:
        img: PIL Image object

    Returns:
        Dictionary with image information
    """
    return {
        'width': img.width,
        'height': img.height,
        'mode': img.mode,
        'has_alpha': img.mode in ('RGBA', 'LA', 'PA'),
        'pixels': img.width * img.height,
        'needs_resize': needs_resize(img)
    }


def has_transparency(img: Image.Image) -> bool:
    """Check if the image has any transparent pixels."""
    if img.mode != 'RGBA':
        return False

    # Check if any pixel has alpha < 255
    import numpy as np
    alpha = np.array(img)[:, :, 3]
    return np.any(alpha < 255)


