# ImageTo3MF - Claude Code Prompt

## Project Name
**ImageTo3MF**

## Overview
Build a Python desktop utility that converts JPG/PNG images into multi-color 3D printable files. The tool maps 4 colors from an image to 4 filament colors, generates separate STL geometry for each color region, and outputs a combined 3MF file suitable for multi-material 3D printers.

---

## Core Requirements

### 1. Image Loading
- Accept local PNG or JPG image files via file dialog or command-line argument
- Support common image sizes (handle large images by providing a resize option)
- Validate file format before processing

### 2. Visual Display & Color Selection
- Display the loaded image in a GUI window
- Allow the user to select exactly 4 colors from the image that will map to 4 filaments
- Provide a color picker or eyedropper tool to sample colors directly from the image
- Show a preview of the image reduced to only the 4 selected colors (color quantization preview)
- Allow adjustment of color tolerance/threshold for mapping similar colors

### 3. Color-to-Geometry Conversion
- For each of the 4 selected colors, create a separate 3D mesh:
  - Each pixel matching a color becomes a raised block/voxel
  - Non-matching pixels for that color remain flat (base level) or are omitted
- All 4 color layers should align and fit together like puzzle pieces
- Configurable parameters:
  - Total model width/height in mm
  - Base thickness in mm
  - Color layer height/extrusion depth in mm
  - Pixel-to-mm scale factor

### 4. 3MF Output
- Combine all 4 STL meshes into a single 3MF file
- Each mesh should be a separate object/component in the 3MF with distinct material assignments
- The 3MF should be compatible with **Orca Slicer** (primary target)
- Include proper material/color metadata so Orca Slicer recognizes the 4 different parts
- Objects should be grouped as a single model with multiple color components

---

## Technical Specifications

### Python Version
- **Target: Python 3.13** - All required libraries have pre-built wheels and work correctly
- Use a virtual environment: `python -m venv venv`

### Recommended Libraries
- **Image Processing**: `Pillow` (PIL) - mature, well-supported
- **GUI**: `tkinter` (built-in) - zero extra dependencies, works out of the box
- **3D Mesh Generation**: `numpy` for array operations
- **3MF Export**: `lib3mf` (official 3MF Consortium library) - **best multi-color support**
- **Color Processing**: `numpy` for array operations, optionally `scikit-learn` for k-means clustering

### Why lib3mf (not trimesh)
- `lib3mf` v2.5.0 has pre-built Windows wheels - installs with simple `pip install lib3mf`
- Native support for `basematerials` and per-object material assignment
- Produces 3MF files with proper `pid`/`pindex` attributes for multi-color models
- trimesh's 3MF export lacks multi-material support

### lib3mf Usage Pattern
```python
import lib3mf
import ctypes

def pos(x, y, z):
    """Create a lib3mf Position"""
    p = lib3mf.Position()
    p.Coordinates = (ctypes.c_float * 3)(x, y, z)
    return p

def tri(i0, i1, i2):
    """Create a lib3mf Triangle"""
    t = lib3mf.Triangle()
    t.Indices = (ctypes.c_uint32 * 3)(i0, i1, i2)
    return t

wrapper = lib3mf.Wrapper()
model = wrapper.CreateModel()

# Create mesh and set geometry
mesh = model.AddMeshObject()
mesh.SetGeometry(vertices_list, triangles_list)
mesh.SetName('ColorName')

# Create material group and assign to mesh
mat_group = model.AddBaseMaterialGroup()
mat_idx = mat_group.AddMaterial('Red', wrapper.RGBAToColor(255, 0, 0, 255))
mesh.SetObjectLevelProperty(mat_group.GetResourceID(), mat_idx)

# Add to build and export
model.AddBuildItem(mesh, wrapper.GetIdentityTransform())
writer = model.QueryWriter('3mf')
writer.WriteToFile('output.3mf')
```

### Target Slicer Compatibility
- **Primary Target: Orca Slicer**
- The 3MF output must be fully compatible with Orca Slicer's multi-color/multi-material workflow
- Orca Slicer expects:
  - Each color as a separate object/mesh within the 3MF
  - Proper object grouping so parts are recognized as a single multi-color model
  - Material/color metadata in the 3MF for automatic filament assignment
- Test the output by opening in Orca Slicer and verifying all 4 parts appear and can be assigned to different filaments

### Suggested Architecture
```
ImageTo3MF/
├── main.py              # Entry point, GUI initialization
├── image_loader.py      # Image loading and validation
├── color_selector.py    # Color picking and quantization logic
├── mesh_generator.py    # Convert color regions to 3D meshes
├── exporter.py          # 3MF file assembly and export
├── requirements.txt     # Dependencies
└── README.md            # Usage instructions
```

### GUI Workflow
1. **Load Image** → User selects file → Display image in canvas
2. **Pick Colors** → User clicks on image to select 4 colors (show selected colors as swatches)
3. **Configure** → User sets output dimensions, layer height, tolerance
4. **Preview** → Show quantized image with only 4 colors
5. **Generate** → Process and create 3MF file
6. **Save** → File dialog to save .3mf output

---

## Detailed Behavior

### Color Mapping Algorithm
1. For each pixel in the image, calculate the Euclidean distance in RGB space to each of the 4 selected colors
2. Assign the pixel to the nearest color (within tolerance threshold)
3. Pixels outside tolerance of all colors can be:
   - Assigned to nearest color anyway, OR
   - Treated as "background" (no extrusion)

### Mesh Generation Strategy
- Create a base plate that all colors share (optional, configurable)
- For each color layer:
  - Generate a heightmap where matching pixels = raised, non-matching = base level
  - Convert heightmap to triangle mesh
  - Optimize mesh by merging coplanar faces where possible
- Ensure watertight (manifold) meshes for 3D printing

### 3MF Structure
The 3MF file should contain:
- 4 mesh objects (one per color)
- Material definitions with RGB values matching selected colors
- Proper alignment so all meshes stack/interlock correctly

---

## Example Usage

```
1. Launch application
2. Click "Load Image" → Select "logo.png"
3. Image displays in window
4. Click on 4 distinct colors in the image (e.g., red, blue, white, black)
5. Adjust settings:
   - Width: 100mm
   - Base height: 2mm  
   - Color layer height: 1mm
   - Color tolerance: 30
6. Click "Preview" → See 4-color quantized version
7. Click "Generate 3MF"
8. Save as "logo.3mf"
9. Open in Orca Slicer → See 4 objects, assign filaments, slice, print
```

---

## Additional Nice-to-Have Features (Optional)
- Auto-detect 4 dominant colors using k-means clustering
- Undo/redo for color selection
- Real-time preview of 3D model (using matplotlib 3D or similar)
- Batch processing multiple images
- Support for more than 4 colors (configurable)
- Edge smoothing/anti-aliasing options for cleaner meshes
- Import/export color presets

---

## Constraints & Considerations
- Keep dependencies minimal and cross-platform where possible
- Ensure the tool works on Windows, macOS, and Linux
- Handle edge cases: very small images, images with fewer than 4 colors, transparent PNGs
- Provide meaningful error messages for invalid inputs
- Include progress indication for large image processing

### Critical: Multi-Color Mesh Strategy
The meshes must fit together correctly for multi-color printing:
- **No overlaps**: Color regions must not overlap in XY space (would cause print conflicts)
- **No gaps**: Adjacent colors should share edges exactly (no visible seams)
- **Same Z-height**: All color layers should have the same total height so they print flush
- Consider a "cookie cutter" approach: each color fills its region like puzzle pieces on a shared base

---

## Testing Checklist
Before considering the project complete:
1. [ ] Load a simple test image with 4 distinct solid colors
2. [ ] Verify color picking selects the correct RGB values
3. [ ] Export 3MF and open in Orca Slicer
4. [ ] Confirm all 4 objects appear in the object list
5. [ ] Assign different filaments to each object
6. [ ] Check preview shows colors in correct positions
7. [ ] Slice and verify no errors/warnings about mesh issues

---

## Deliverables
1. Complete Python source code with modular structure
2. `requirements.txt` with all dependencies:
   ```
   pillow
   numpy
   lib3mf
   ```
3. `README.md` with installation and usage instructions
4. Example test images (or instructions to obtain them)

---

## Success Criteria
- Can load any standard JPG/PNG image
- GUI allows intuitive 4-color selection
- Generates valid, printable 3MF file
- **3MF opens correctly in Orca Slicer** with all 4 color regions as separate assignable objects
- Each color region is a separate object assignable to different filaments





