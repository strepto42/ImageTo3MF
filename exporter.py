"""
3MF export module for ImageTo3MF.
Handles assembly of meshes into a multi-color 3MF file using lib3mf.
"""

import lib3mf
import ctypes
from typing import List
from mesh_generator import MeshData


def create_position(x: float, y: float, z: float) -> lib3mf.Position:
    """Create a lib3mf Position object."""
    pos = lib3mf.Position()
    pos.Coordinates = (ctypes.c_float * 3)(x, y, z)
    return pos


def create_triangle(i0: int, i1: int, i2: int) -> lib3mf.Triangle:
    """Create a lib3mf Triangle object."""
    tri = lib3mf.Triangle()
    tri.Indices = (ctypes.c_uint32 * 3)(i0, i1, i2)
    return tri


def export_to_3mf(meshes: List[MeshData], output_path: str) -> bool:
    """
    Export meshes to a 3MF file with multi-color support.

    Args:
        meshes: List of MeshData objects to export
        output_path: Path for the output .3mf file

    Returns:
        True if export was successful
    """
    if not meshes:
        raise ValueError("No meshes to export")

    # Create lib3mf wrapper and model
    wrapper = lib3mf.Wrapper()
    model = wrapper.CreateModel()

    # Create a single material group for all colors
    mat_group = model.AddBaseMaterialGroup()

    # Create a components object to group all color parts
    components_object = model.AddComponentsObject()

    # Process each mesh
    for i, mesh_data in enumerate(meshes):
        if not mesh_data.vertices or not mesh_data.triangles:
            continue

        # Add material for this color
        r, g, b = mesh_data.color
        color = wrapper.RGBAToColor(r, g, b, 255)
        mat_idx = mat_group.AddMaterial(mesh_data.name, color)

        # Create mesh object
        mesh_object = model.AddMeshObject()
        mesh_object.SetName(mesh_data.name)

        # Convert vertices to lib3mf format
        vertices = [create_position(v[0], v[1], v[2]) for v in mesh_data.vertices]

        # Convert triangles to lib3mf format
        triangles = [create_triangle(t[0], t[1], t[2]) for t in mesh_data.triangles]

        # Set geometry
        mesh_object.SetGeometry(vertices, triangles)

        # Assign material to this mesh
        mesh_object.SetObjectLevelProperty(mat_group.GetResourceID(), mat_idx)

        # Add this mesh as a component of the group
        # Use identity transform (no translation/rotation)
        transform = wrapper.GetIdentityTransform()
        components_object.AddComponent(mesh_object, transform)

    # Add the components object (grouped model) to the build
    transform = wrapper.GetIdentityTransform()
    model.AddBuildItem(components_object, transform)

    # Write the 3MF file
    writer = model.QueryWriter('3mf')
    writer.WriteToFile(output_path)

    return True


def export_to_3mf_separate(meshes: List[MeshData], output_path: str) -> bool:
    """
    Export meshes to a 3MF file with each color as a separate build item.
    This alternative approach may work better with some slicers.

    Args:
        meshes: List of MeshData objects to export
        output_path: Path for the output .3mf file

    Returns:
        True if export was successful
    """
    if not meshes:
        raise ValueError("No meshes to export")

    # Create lib3mf wrapper and model
    wrapper = lib3mf.Wrapper()
    model = wrapper.CreateModel()

    # Create a single material group for all colors
    mat_group = model.AddBaseMaterialGroup()

    # Process each mesh
    for i, mesh_data in enumerate(meshes):
        if not mesh_data.vertices or not mesh_data.triangles:
            continue

        # Add material for this color
        r, g, b = mesh_data.color
        color = wrapper.RGBAToColor(r, g, b, 255)
        mat_idx = mat_group.AddMaterial(mesh_data.name, color)

        # Create mesh object
        mesh_object = model.AddMeshObject()
        mesh_object.SetName(mesh_data.name)

        # Convert vertices to lib3mf format
        vertices = [create_position(v[0], v[1], v[2]) for v in mesh_data.vertices]

        # Convert triangles to lib3mf format
        triangles = [create_triangle(t[0], t[1], t[2]) for t in mesh_data.triangles]

        # Set geometry
        mesh_object.SetGeometry(vertices, triangles)

        # Assign material to this mesh
        mesh_object.SetObjectLevelProperty(mat_group.GetResourceID(), mat_idx)

        # Add as separate build item
        transform = wrapper.GetIdentityTransform()
        model.AddBuildItem(mesh_object, transform)

    # Write the 3MF file
    writer = model.QueryWriter('3mf')
    writer.WriteToFile(output_path)

    return True


def validate_3mf(file_path: str) -> dict:
    """
    Validate a 3MF file and return information about its contents.

    Args:
        file_path: Path to the 3MF file

    Returns:
        Dictionary with validation results and file info
    """
    try:
        wrapper = lib3mf.Wrapper()
        model = wrapper.CreateModel()
        reader = model.QueryReader('3mf')
        reader.ReadFromFile(file_path)

        # Count objects
        object_iterator = model.GetObjects()
        object_count = 0
        mesh_count = 0

        while object_iterator.MoveNext():
            object_count += 1
            obj = object_iterator.GetCurrent()
            if obj.IsMeshObject():
                mesh_count += 1

        # Count build items
        build_items = model.GetBuildItems()
        build_count = 0
        while build_items.MoveNext():
            build_count += 1

        return {
            'valid': True,
            'object_count': object_count,
            'mesh_count': mesh_count,
            'build_item_count': build_count,
            'error': None
        }
    except Exception as e:
        return {
            'valid': False,
            'object_count': 0,
            'mesh_count': 0,
            'build_item_count': 0,
            'error': str(e)
        }

