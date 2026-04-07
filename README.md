# ImageTo3MF

A Python desktop utility that converts JPG/PNG images into multi-color 3D printable files. The tool maps up to 4 colors from an image to 4 filament colors, generates separate 3D geometry for each color region, and outputs a combined 3MF file suitable for multi-material 3D printers like those compatible with Orca Slicer.

## Features

- **Image Loading**: Load PNG or JPG images via file dialog or command line
- **Color Picker**: Click on the image to select up to 4 colors for mapping
- **Color Quantization**: Preview how the image will look with only your selected colors
- **Configurable Output**: Set model dimensions, base height, and layer height
- **Optimized Meshes**: Greedy meshing algorithm reduces triangle count
- **Orca Slicer Compatible**: Generates 3MF files with proper multi-material support

## Installation

### Prerequisites
- Python 3.10 or later (tested with 3.13)

### Setup

1. Clone or download this repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Application

```bash
python main.py
```

Or with an image file:
```bash
python main.py path/to/image.png
```

### Workflow

1. **Load Image**: Click "Load Image..." and select a PNG or JPG file
2. **Pick Colors**: Click on 4 distinct colors in the image you want to map to filaments
3. **Configure Settings**:
   - **Model Width**: Final width of the 3D model in millimeters
   - **Base Height**: Thickness of the base layer in mm
   - **Color Layer Height**: Height of the raised color regions in mm
   - **Color Tolerance**: How closely pixels must match selected colors (1-200)
4. **Preview**: Click "Preview Quantized" to see how colors will be mapped
5. **Generate**: Click "Generate 3MF" to create the output file
6. **Open in Slicer**: Load the .3mf file in Orca Slicer to assign filaments and slice

### Settings Explained

- **Model Width (mm)**: The total width of your final 3D model. Height is calculated automatically to maintain aspect ratio.
- **Base Height (mm)**: The thickness of the solid base that all colors share. Recommended: 1-3mm.
- **Color Layer Height (mm)**: How much the colored regions extrude above the base. Recommended: 0.5-2mm.
- **Color Tolerance**: Lower values = stricter color matching. Higher values = more pixels assigned to each color.
- **Assign all pixels to nearest color**: When enabled, every pixel gets assigned to a color. When disabled, pixels far from all colors become unassigned.
- **Optimize mesh**: Uses greedy meshing to combine adjacent pixels into larger rectangles, significantly reducing file size.

## Output Format

The generated 3MF file contains:
- 4 separate mesh objects (one per selected color)
- Material definitions with RGB values matching your selected colors
- Proper grouping for Orca Slicer multi-color workflow

All meshes are aligned so they fit together like puzzle pieces when printed.

## Tips for Best Results

1. **Choose contrasting colors**: Select colors that are clearly different from each other
2. **Start with simple images**: Logos and graphics with solid colors work best
3. **Use the preview**: Always preview before generating to ensure colors are mapped correctly
4. **Adjust tolerance**: If colors bleed into each other, lower the tolerance value
5. **Consider resize**: Very large images produce massive meshes; resize to ~200-500px for reasonable file sizes

## Example

1. Load a logo with 4 colors (e.g., red, blue, white, black)
2. Click on each color to select it
3. Set width to 100mm, base height to 2mm, layer height to 1mm
4. Preview and adjust tolerance if needed
5. Generate 3MF
6. Open in Orca Slicer, assign filaments to each object, slice, and print!

## Project Structure

```
ImageTo3MF/
├── main.py              # Entry point and GUI
├── image_loader.py      # Image loading and validation
├── color_selector.py    # Color picking and quantization
├── mesh_generator.py    # 3D mesh generation
├── exporter.py          # 3MF file export
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## Dependencies

- **Pillow**: Image loading and processing
- **NumPy**: Array operations for color quantization and mesh generation  
- **lib3mf**: Official 3MF Consortium library for multi-color 3MF export

## Troubleshooting

### "No module named 'lib3mf'"
Make sure you've installed dependencies: `pip install -r requirements.txt`

### Slow processing with large images
Resize the image when prompted, or manually resize before loading. Images under 500x500 pixels process quickly.

### Colors don't look right in slicer
Adjust the color tolerance slider and re-preview. Lower tolerance = stricter matching.

### 3MF doesn't open in slicer
Ensure you're using a slicer that supports multi-material 3MF files (Orca Slicer, PrusaSlicer, Bambu Studio).

## License

MIT License - feel free to use and modify for your projects.

