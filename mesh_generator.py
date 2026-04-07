"""
Mesh generation module for ImageTo3MF.
Converts color region masks to 3D triangle meshes.
"""

import numpy as np
from typing import List, Tuple, Dict
from dataclasses import dataclass


@dataclass
class MeshData:
    """Container for mesh geometry data."""
    vertices: List[Tuple[float, float, float]]
    triangles: List[Tuple[int, int, int]]
    color: Tuple[int, int, int]
    name: str


def create_box_mesh(
    x: float, y: float, z: float,
    width: float, depth: float, height: float,
    vertex_offset: int = 0
) -> Tuple[List[Tuple[float, float, float]], List[Tuple[int, int, int]]]:
    """
    Create vertices and triangles for a single box/voxel.

    Args:
        x, y, z: Position of the box corner (minimum coordinates)
        width, depth, height: Dimensions of the box
        vertex_offset: Offset to add to vertex indices

    Returns:
        Tuple of (vertices list, triangles list)
    """
    # 8 vertices of a box
    vertices = [
        (x, y, z),                          # 0: front-bottom-left
        (x + width, y, z),                  # 1: front-bottom-right
        (x + width, y + depth, z),          # 2: back-bottom-right
        (x, y + depth, z),                  # 3: back-bottom-left
        (x, y, z + height),                 # 4: front-top-left
        (x + width, y, z + height),         # 5: front-top-right
        (x + width, y + depth, z + height), # 6: back-top-right
        (x, y + depth, z + height),         # 7: back-top-left
    ]

    # 12 triangles (2 per face, 6 faces)
    v = vertex_offset
    triangles = [
        # Bottom face (z = 0)
        (v+0, v+2, v+1), (v+0, v+3, v+2),
        # Top face (z = height)
        (v+4, v+5, v+6), (v+4, v+6, v+7),
        # Front face (y = 0)
        (v+0, v+1, v+5), (v+0, v+5, v+4),
        # Back face (y = depth)
        (v+2, v+3, v+7), (v+2, v+7, v+6),
        # Left face (x = 0)
        (v+0, v+4, v+7), (v+0, v+7, v+3),
        # Right face (x = width)
        (v+1, v+2, v+6), (v+1, v+6, v+5),
    ]

    return vertices, triangles


def generate_heightmap_mesh(
    mask: np.ndarray,
    pixel_size_mm: float,
    base_height_mm: float,
    layer_height_mm: float,
    color: Tuple[int, int, int],
    name: str
) -> MeshData:
    """
    Generate a mesh from a binary mask using heightmap approach.
    Creates a solid mesh where each pixel in the mask becomes a raised block.

    Args:
        mask: Binary numpy array (1 = raised, 0 = not part of this color)
        pixel_size_mm: Size of each pixel in mm
        base_height_mm: Height of the base in mm
        layer_height_mm: Additional height for colored regions
        color: RGB color tuple
        name: Name for this mesh

    Returns:
        MeshData object containing vertices and triangles
    """
    height, width = mask.shape
    vertices = []
    triangles = []

    total_height = base_height_mm + layer_height_mm

    # Find all pixels that belong to this color
    for y in range(height):
        for x in range(width):
            if mask[y, x] == 1:
                # Create a box for this pixel
                px = x * pixel_size_mm
                # Flip Y axis so image top is at positive Y in 3D
                py = (height - 1 - y) * pixel_size_mm

                box_verts, box_tris = create_box_mesh(
                    px, py, 0,
                    pixel_size_mm, pixel_size_mm, total_height,
                    len(vertices)
                )
                vertices.extend(box_verts)
                triangles.extend(box_tris)

    return MeshData(
        vertices=vertices,
        triangles=triangles,
        color=color,
        name=name
    )


def generate_optimized_mesh(
    mask: np.ndarray,
    pixel_size_mm: float,
    base_height_mm: float,
    layer_height_mm: float,
    color: Tuple[int, int, int],
    name: str
) -> MeshData:
    """
    Generate an optimized mesh using greedy meshing to reduce triangle count.
    Merges adjacent pixels into larger rectangles where possible.

    Args:
        mask: Binary numpy array (1 = raised, 0 = not part of this color)
        pixel_size_mm: Size of each pixel in mm
        base_height_mm: Height of the base in mm
        layer_height_mm: Additional height for colored regions
        color: RGB color tuple
        name: Name for this mesh

    Returns:
        MeshData object containing vertices and triangles
    """
    height, width = mask.shape
    vertices = []
    triangles = []

    total_height = base_height_mm + layer_height_mm

    # Create a copy of mask to track processed pixels
    processed = np.zeros_like(mask, dtype=bool)

    # Greedy meshing: find rectangular regions
    for y in range(height):
        for x in range(width):
            if mask[y, x] == 1 and not processed[y, x]:
                # Find the largest rectangle starting at (x, y)
                # First, extend in x direction
                x_end = x
                while x_end < width and mask[y, x_end] == 1 and not processed[y, x_end]:
                    x_end += 1

                # Then, extend in y direction as far as the full x range allows
                y_end = y
                can_extend = True
                while can_extend and y_end < height:
                    for xi in range(x, x_end):
                        if mask[y_end, xi] != 1 or processed[y_end, xi]:
                            can_extend = False
                            break
                    if can_extend:
                        y_end += 1

                # Mark all pixels in this rectangle as processed
                for yi in range(y, y_end):
                    for xi in range(x, x_end):
                        processed[yi, xi] = True

                # Create a box for this rectangle
                rect_width = (x_end - x) * pixel_size_mm
                rect_depth = (y_end - y) * pixel_size_mm
                px = x * pixel_size_mm
                # Flip Y axis
                py = (height - y_end) * pixel_size_mm

                box_verts, box_tris = create_box_mesh(
                    px, py, 0,
                    rect_width, rect_depth, total_height,
                    len(vertices)
                )
                vertices.extend(box_verts)
                triangles.extend(box_tris)

    return MeshData(
        vertices=vertices,
        triangles=triangles,
        color=color,
        name=name
    )


def generate_color_meshes(
    color_map: np.ndarray,
    colors: List[Tuple[int, int, int]],
    model_width_mm: float,
    base_height_mm: float,
    layer_height_mm: float,
    optimize: bool = True
) -> List[MeshData]:
    """
    Generate meshes for all colors in the color map.

    Args:
        color_map: Array where each value is the color index (0-3) or -1
        colors: List of RGB color tuples
        model_width_mm: Desired width of the final model in mm
        base_height_mm: Height of the base in mm
        layer_height_mm: Additional height for colored regions
        optimize: If True, use greedy meshing for fewer triangles

    Returns:
        List of MeshData objects, one per color
    """
    height, width = color_map.shape

    # Calculate pixel size to achieve desired model width
    pixel_size_mm = model_width_mm / width

    meshes = []
    color_names = ['Color1', 'Color2', 'Color3', 'Color4']

    for i, color in enumerate(colors):
        # Create mask for this color
        mask = (color_map == i).astype(np.uint8)

        # Skip if no pixels for this color
        if not np.any(mask):
            continue

        # Generate mesh
        if optimize:
            mesh = generate_optimized_mesh(
                mask, pixel_size_mm, base_height_mm, layer_height_mm,
                color, color_names[i] if i < len(color_names) else f'Color{i+1}'
            )
        else:
            mesh = generate_heightmap_mesh(
                mask, pixel_size_mm, base_height_mm, layer_height_mm,
                color, color_names[i] if i < len(color_names) else f'Color{i+1}'
            )

        if mesh.vertices:  # Only add if mesh has geometry
            meshes.append(mesh)

    return meshes


def calculate_model_dimensions(
    image_width: int,
    image_height: int,
    model_width_mm: float,
    base_height_mm: float,
    layer_height_mm: float
) -> Dict[str, float]:
    """
    Calculate the final model dimensions.

    Args:
        image_width: Width of the source image in pixels
        image_height: Height of the source image in pixels
        model_width_mm: Desired width of the model in mm
        base_height_mm: Height of the base
        layer_height_mm: Height of the color layer

    Returns:
        Dictionary with model dimensions
    """
    aspect_ratio = image_height / image_width
    model_height_mm = model_width_mm * aspect_ratio
    total_z_height = base_height_mm + layer_height_mm
    pixel_size_mm = model_width_mm / image_width

    return {
        'width_mm': model_width_mm,
        'height_mm': model_height_mm,
        'z_height_mm': total_z_height,
        'pixel_size_mm': pixel_size_mm,
        'pixels_x': image_width,
        'pixels_y': image_height
    }

