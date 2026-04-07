"""
Command-line test of the ImageTo3MF pipeline without GUI.
Tests the complete flow: load image -> quantize -> generate meshes -> export 3MF
"""

import os
import numpy as np
from image_loader import load_image, get_image_info
from color_selector import quantize_image_fast
from mesh_generator import generate_color_meshes, calculate_model_dimensions
from exporter import export_to_3mf, validate_3mf


def test_pipeline(test_image='test_image.png', output_file='test_output.3mf', colors=None):
    """Test the complete image-to-3MF pipeline."""

    # Default colors (the 4 quadrant colors from test image)
    if colors is None:
        colors = [
            (255, 0, 0),      # Red
            (0, 255, 0),      # Green
            (0, 0, 255),      # Blue
            (255, 255, 0),    # Yellow
        ]

    # Settings
    model_width_mm = 50.0
    base_height_mm = 2.0
    layer_height_mm = 1.0
    tolerance = 50

    print("=" * 60)
    print("ImageTo3MF Pipeline Test")
    print("=" * 60)

    # Step 1: Load image
    print("\n[1/5] Loading image...")
    image_path = os.path.join(os.path.dirname(__file__), test_image)

    if not os.path.exists(image_path):
        print(f"ERROR: Test image not found: {image_path}")
        print("Run 'python create_test_images.py' first.")
        return False

    img = load_image(image_path)
    info = get_image_info(img)
    print(f"  Loaded: {test_image}")
    print(f"  Size: {info['width']} x {info['height']} pixels")
    print(f"  Mode: {info['mode']}")
    print(f"  Has transparency: {info['has_alpha']}")

    # Step 2: Quantize image
    print("\n[2/5] Quantizing image to selected colors...")
    color_map, quantized_img = quantize_image_fast(
        img,
        colors,
        tolerance=tolerance,
        assign_nearest=True
    )
    print(f"  Color map shape: {color_map.shape}")

    # Count pixels per color
    for i, color in enumerate(colors):
        count = np.sum(color_map == i)
        print(f"  Color {i+1} (RGB{color}): {count} pixels")

    # Count transparent/unassigned pixels
    unassigned = np.sum(color_map == -1)
    print(f"  Transparent/Unassigned: {unassigned} pixels")

    # Step 3: Calculate dimensions
    print("\n[3/5] Calculating model dimensions...")
    dims = calculate_model_dimensions(
        img.width, img.height,
        model_width_mm, base_height_mm, layer_height_mm
    )
    print(f"  Model size: {dims['width_mm']:.1f} x {dims['height_mm']:.1f} x {dims['z_height_mm']:.1f} mm")
    print(f"  Pixel size: {dims['pixel_size_mm']:.3f} mm")

    # Step 4: Generate meshes
    print("\n[4/5] Generating 3D meshes...")
    meshes = generate_color_meshes(
        color_map,
        colors,
        model_width_mm,
        base_height_mm,
        layer_height_mm,
        optimize=True
    )

    total_triangles = 0
    for mesh in meshes:
        tri_count = len(mesh.triangles)
        total_triangles += tri_count
        print(f"  {mesh.name}: {len(mesh.vertices)} vertices, {tri_count} triangles")
    print(f"  Total triangles: {total_triangles}")

    # Step 5: Export to 3MF
    print("\n[5/5] Exporting to 3MF...")
    output_path = os.path.join(os.path.dirname(__file__), output_file)
    export_to_3mf(meshes, output_path)
    print(f"  Saved: {output_path}")

    # Validate the output
    print("\nValidating 3MF file...")
    validation = validate_3mf(output_path)
    if validation['valid']:
        print(f"  ✓ Valid 3MF file")
        print(f"  Objects: {validation['object_count']}")
        print(f"  Meshes: {validation['mesh_count']}")
        print(f"  Build items: {validation['build_item_count']}")
    else:
        print(f"  ✗ Invalid: {validation['error']}")
        return False

    # File size
    file_size = os.path.getsize(output_path)
    print(f"  File size: {file_size / 1024:.1f} KB")

    print("\n" + "=" * 60)
    print("✓ Pipeline test completed successfully!")
    print(f"Output file: {output_path}")
    print("Open this file in Orca Slicer to verify multi-color support.")
    print("=" * 60)

    return True


def test_transparency():
    """Test the pipeline with a transparent image."""
    print("\n" + "=" * 60)
    print("TESTING TRANSPARENCY SUPPORT")
    print("=" * 60)

    return test_pipeline(
        test_image='test_transparent.png',
        output_file='test_transparent_output.3mf',
        colors=[
            (255, 0, 0),      # Red
            (0, 255, 0),      # Green
            (0, 0, 255),      # Blue
            (255, 255, 0),    # Yellow
        ]
    )


if __name__ == '__main__':
    # Test with regular image
    success1 = test_pipeline()

    # Test with transparent image
    success2 = test_transparency()

    exit(0 if (success1 and success2) else 1)

