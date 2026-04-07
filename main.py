"""
ImageTo3MF - Convert images to multi-color 3D printable 3MF files.
Main entry point and GUI application.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import sys
from typing import List, Tuple, Optional

from image_loader import load_image, needs_resize, resize_image, get_image_info, validate_image_path, has_transparency
from color_selector import get_pixel_color, quantize_image_fast, color_to_hex, is_pixel_transparent
from mesh_generator import generate_color_meshes, calculate_model_dimensions
from exporter import export_to_3mf, export_to_3mf_separate


class ColorSwatch(tk.Frame):
    """A widget displaying a color swatch with remove button."""

    def __init__(self, parent, color: Tuple[int, int, int], index: int, on_remove):
        super().__init__(parent, relief=tk.RAISED, borderwidth=1)

        self.color = color
        self.index = index
        self.on_remove = on_remove

        # Color display
        hex_color = color_to_hex(color)
        self.color_label = tk.Label(
            self,
            bg=hex_color,
            width=4,
            height=2
        )
        self.color_label.pack(side=tk.LEFT, padx=2, pady=2)

        # RGB text
        self.rgb_label = tk.Label(
            self,
            text=f"R:{color[0]}\nG:{color[1]}\nB:{color[2]}",
            font=('Consolas', 8)
        )
        self.rgb_label.pack(side=tk.LEFT, padx=2)

        # Remove button
        self.remove_btn = tk.Button(
            self,
            text="✕",
            command=self._on_remove,
            width=2,
            font=('Arial', 8)
        )
        self.remove_btn.pack(side=tk.RIGHT, padx=2)

    def _on_remove(self):
        self.on_remove(self.index)


class ImageTo3MFApp:
    """Main application class."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("ImageTo3MF - Multi-Color 3D Print Generator")
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)

        # State
        self.original_image: Optional[Image.Image] = None
        self.display_image: Optional[Image.Image] = None
        self.quantized_image: Optional[Image.Image] = None
        self.photo_image: Optional[ImageTk.PhotoImage] = None
        self.selected_colors: List[Tuple[int, int, int]] = []
        self.color_map: Optional[any] = None
        self.image_path: str = ""

        # Display scale factor
        self.display_scale = 1.0

        self._setup_ui()
        self._bind_events()

        # Handle command line argument
        if len(sys.argv) > 1:
            self._load_image_from_path(sys.argv[1])

    def _setup_ui(self):
        """Set up the user interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left panel - Image display
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Image canvas with scrollbars
        canvas_frame = ttk.Frame(left_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg='#404040', cursor='crosshair')
        v_scroll = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scroll = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)

        self.canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Status bar under canvas
        self.status_var = tk.StringVar(value="Load an image to begin")
        status_bar = ttk.Label(left_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=(5, 0))

        # Right panel - Controls
        right_frame = ttk.Frame(main_frame, width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        right_frame.pack_propagate(False)

        # File section
        file_frame = ttk.LabelFrame(right_frame, text="Image", padding="5")
        file_frame.pack(fill=tk.X, pady=(0, 10))

        self.load_btn = ttk.Button(file_frame, text="Load Image...", command=self._load_image)
        self.load_btn.pack(fill=tk.X)

        self.image_info_var = tk.StringVar(value="No image loaded")
        ttk.Label(file_frame, textvariable=self.image_info_var, wraplength=280).pack(fill=tk.X, pady=(5, 0))

        # Color selection section
        color_frame = ttk.LabelFrame(right_frame, text="Colors (Click image to pick, max 4)", padding="5")
        color_frame.pack(fill=tk.X, pady=(0, 10))

        self.colors_container = ttk.Frame(color_frame)
        self.colors_container.pack(fill=tk.X)

        self.color_hint = ttk.Label(color_frame, text="Click on the image to select colors", foreground='gray')
        self.color_hint.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(color_frame, text="Clear All Colors", command=self._clear_colors).pack(fill=tk.X, pady=(5, 0))

        # Settings section
        settings_frame = ttk.LabelFrame(right_frame, text="Settings", padding="5")
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        # Model width
        ttk.Label(settings_frame, text="Model Width (mm):").pack(anchor=tk.W)
        self.width_var = tk.StringVar(value="100")
        width_entry = ttk.Entry(settings_frame, textvariable=self.width_var, width=10)
        width_entry.pack(anchor=tk.W, pady=(0, 5))

        # Base height
        ttk.Label(settings_frame, text="Base Height (mm):").pack(anchor=tk.W)
        self.base_height_var = tk.StringVar(value="2.0")
        base_entry = ttk.Entry(settings_frame, textvariable=self.base_height_var, width=10)
        base_entry.pack(anchor=tk.W, pady=(0, 5))

        # Layer height
        ttk.Label(settings_frame, text="Color Layer Height (mm):").pack(anchor=tk.W)
        self.layer_height_var = tk.StringVar(value="1.0")
        layer_entry = ttk.Entry(settings_frame, textvariable=self.layer_height_var, width=10)
        layer_entry.pack(anchor=tk.W, pady=(0, 5))

        # Color tolerance
        ttk.Label(settings_frame, text="Color Tolerance:").pack(anchor=tk.W)
        self.tolerance_var = tk.IntVar(value=50)
        tolerance_frame = ttk.Frame(settings_frame)
        tolerance_frame.pack(fill=tk.X, pady=(0, 5))

        self.tolerance_scale = ttk.Scale(
            tolerance_frame,
            from_=1,
            to=200,
            variable=self.tolerance_var,
            orient=tk.HORIZONTAL
        )
        self.tolerance_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.tolerance_label = ttk.Label(tolerance_frame, text="50")
        self.tolerance_label.pack(side=tk.RIGHT, padx=(5, 0))

        # Assign nearest checkbox
        self.assign_nearest_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            settings_frame,
            text="Assign all pixels to nearest color",
            variable=self.assign_nearest_var
        ).pack(anchor=tk.W)

        # Optimize mesh checkbox
        self.optimize_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            settings_frame,
            text="Optimize mesh (fewer triangles)",
            variable=self.optimize_var
        ).pack(anchor=tk.W)

        # Preview section
        preview_frame = ttk.LabelFrame(right_frame, text="Preview", padding="5")
        preview_frame.pack(fill=tk.X, pady=(0, 10))

        self.preview_btn = ttk.Button(preview_frame, text="Preview Quantized", command=self._preview_quantized, state=tk.DISABLED)
        self.preview_btn.pack(fill=tk.X)

        self.show_original_btn = ttk.Button(preview_frame, text="Show Original", command=self._show_original, state=tk.DISABLED)
        self.show_original_btn.pack(fill=tk.X, pady=(5, 0))

        # Model info
        self.model_info_var = tk.StringVar(value="")
        ttk.Label(preview_frame, textvariable=self.model_info_var, wraplength=280).pack(fill=tk.X, pady=(5, 0))

        # Generate section
        generate_frame = ttk.LabelFrame(right_frame, text="Generate", padding="5")
        generate_frame.pack(fill=tk.X, pady=(0, 10))

        self.generate_btn = ttk.Button(
            generate_frame,
            text="Generate 3MF",
            command=self._generate_3mf,
            state=tk.DISABLED
        )
        self.generate_btn.pack(fill=tk.X)

        # Progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(generate_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))

    def _bind_events(self):
        """Bind event handlers."""
        self.canvas.bind('<Button-1>', self._on_canvas_click)
        self.canvas.bind('<Motion>', self._on_canvas_motion)
        self.tolerance_scale.configure(command=self._on_tolerance_change)

    def _on_tolerance_change(self, value):
        """Handle tolerance slider change."""
        self.tolerance_label.configure(text=str(int(float(value))))

    def _load_image(self):
        """Open file dialog and load an image."""
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.PNG *.JPG *.JPEG"),
                ("PNG files", "*.png *.PNG"),
                ("JPEG files", "*.jpg *.jpeg *.JPG *.JPEG"),
                ("All files", "*.*")
            ]
        )

        if file_path:
            self._load_image_from_path(file_path)

    def _load_image_from_path(self, file_path: str):
        """Load an image from the given path."""
        try:
            is_valid, error = validate_image_path(file_path)
            if not is_valid:
                messagebox.showerror("Error", error)
                return

            self.original_image = load_image(file_path)
            self.image_path = file_path

            # Check if resize is needed
            if needs_resize(self.original_image):
                result = messagebox.askyesno(
                    "Large Image",
                    f"Image is {self.original_image.width}x{self.original_image.height} pixels.\n"
                    "Large images may be slow to process.\n\n"
                    "Would you like to resize it to max 1000px?"
                )
                if result:
                    self.original_image = resize_image(self.original_image)

            self.display_image = self.original_image.copy()
            self._display_current_image()

            # Update info
            info = get_image_info(self.original_image)
            info_text = f"{os.path.basename(file_path)}\n{info['width']} x {info['height']} pixels"
            if info['has_alpha']:
                info_text += "\n(Has transparency)"
            self.image_info_var.set(info_text)

            # Reset state
            self.selected_colors = []
            self.quantized_image = None
            self.color_map = None
            self._update_color_swatches()
            self._update_buttons()

            self.status_var.set("Image loaded. Click on the image to select colors.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")

    def _display_current_image(self):
        """Display the current image on the canvas."""
        if self.display_image is None:
            return

        # Calculate scale to fit in canvas
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600

        img_width = self.display_image.width
        img_height = self.display_image.height

        # Calculate scale to fit
        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        self.display_scale = min(scale_x, scale_y, 1.0)  # Don't upscale

        # Create display image
        display_w = int(img_width * self.display_scale)
        display_h = int(img_height * self.display_scale)

        if self.display_scale < 1.0:
            resized = self.display_image.resize((display_w, display_h), Image.Resampling.LANCZOS)
        else:
            resized = self.display_image

        self.photo_image = ImageTk.PhotoImage(resized)

        # Update canvas
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image)
        self.canvas.configure(scrollregion=(0, 0, display_w, display_h))

    def _on_canvas_click(self, event):
        """Handle click on canvas to pick a color."""
        if self.original_image is None:
            return

        if len(self.selected_colors) >= 4:
            messagebox.showinfo("Info", "Maximum 4 colors selected. Remove one to add another.")
            return

        # Convert canvas coordinates to image coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        img_x = int(canvas_x / self.display_scale)
        img_y = int(canvas_y / self.display_scale)

        # Check bounds
        if img_x < 0 or img_x >= self.original_image.width or img_y < 0 or img_y >= self.original_image.height:
            return

        try:
            # Check if pixel is transparent
            if is_pixel_transparent(self.original_image, img_x, img_y):
                self.status_var.set(f"Pixel ({img_x}, {img_y}) is transparent - no color to pick")
                return
            
            color = get_pixel_color(self.original_image, img_x, img_y)

            # Check if color already selected (with small tolerance)
            for existing in self.selected_colors:
                if all(abs(a - b) < 5 for a, b in zip(color, existing)):
                    self.status_var.set(f"Color RGB{color} already selected")
                    return

            self.selected_colors.append(color)
            self._update_color_swatches()
            self._update_buttons()
            self.status_var.set(f"Selected color {len(self.selected_colors)}: RGB{color}")

        except Exception as e:
            self.status_var.set(f"Error picking color: {str(e)}")

    def _on_canvas_motion(self, event):
        """Handle mouse motion to show color under cursor."""
        if self.original_image is None:
            return

        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        img_x = int(canvas_x / self.display_scale)
        img_y = int(canvas_y / self.display_scale)

        if 0 <= img_x < self.original_image.width and 0 <= img_y < self.original_image.height:
            try:
                if is_pixel_transparent(self.original_image, img_x, img_y):
                    self.status_var.set(f"Pixel ({img_x}, {img_y}) - Transparent")
                else:
                    color = get_pixel_color(self.original_image, img_x, img_y)
                    self.status_var.set(f"Pixel ({img_x}, {img_y}) - RGB{color}")
            except:
                pass

    def _update_color_swatches(self):
        """Update the color swatch display."""
        # Clear existing swatches
        for widget in self.colors_container.winfo_children():
            widget.destroy()

        # Create new swatches
        for i, color in enumerate(self.selected_colors):
            swatch = ColorSwatch(self.colors_container, color, i, self._remove_color)
            swatch.pack(fill=tk.X, pady=2)

        # Update hint
        remaining = 4 - len(self.selected_colors)
        if remaining > 0:
            self.color_hint.configure(text=f"Click image to select {remaining} more color(s)")
        else:
            self.color_hint.configure(text="All 4 colors selected!")

    def _remove_color(self, index: int):
        """Remove a color from the selection."""
        if 0 <= index < len(self.selected_colors):
            self.selected_colors.pop(index)
            self._update_color_swatches()
            self._update_buttons()

    def _clear_colors(self):
        """Clear all selected colors."""
        self.selected_colors = []
        self.quantized_image = None
        self.color_map = None
        self._update_color_swatches()
        self._update_buttons()

        if self.original_image:
            self.display_image = self.original_image.copy()
            self._display_current_image()

    def _update_buttons(self):
        """Update button states based on current state."""
        has_image = self.original_image is not None
        has_colors = len(self.selected_colors) > 0

        self.preview_btn.configure(state=tk.NORMAL if (has_image and has_colors) else tk.DISABLED)
        self.show_original_btn.configure(state=tk.NORMAL if has_image else tk.DISABLED)
        self.generate_btn.configure(state=tk.NORMAL if (has_image and has_colors) else tk.DISABLED)

        # Update model info
        if has_image:
            try:
                width_mm = float(self.width_var.get())
                base_h = float(self.base_height_var.get())
                layer_h = float(self.layer_height_var.get())

                dims = calculate_model_dimensions(
                    self.original_image.width,
                    self.original_image.height,
                    width_mm,
                    base_h,
                    layer_h
                )

                self.model_info_var.set(
                    f"Model: {dims['width_mm']:.1f} x {dims['height_mm']:.1f} x {dims['z_height_mm']:.1f} mm\n"
                    f"Pixel size: {dims['pixel_size_mm']:.3f} mm"
                )
            except:
                self.model_info_var.set("")

    def _preview_quantized(self):
        """Show preview of quantized image."""
        if self.original_image is None or not self.selected_colors:
            return

        try:
            self.status_var.set("Generating preview...")
            self.root.update()

            tolerance = self.tolerance_var.get()
            assign_nearest = self.assign_nearest_var.get()

            self.color_map, self.quantized_image = quantize_image_fast(
                self.original_image,
                self.selected_colors,
                tolerance,
                assign_nearest
            )

            self.display_image = self.quantized_image
            self._display_current_image()

            self.status_var.set("Showing quantized preview. Click 'Show Original' to see original image.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate preview: {str(e)}")
            self.status_var.set("Preview failed")

    def _show_original(self):
        """Show the original image."""
        if self.original_image is None:
            return

        self.display_image = self.original_image.copy()
        self._display_current_image()
        self.status_var.set("Showing original image")

    def _generate_3mf(self):
        """Generate the 3MF file."""
        if self.original_image is None or not self.selected_colors:
            messagebox.showerror("Error", "Please load an image and select colors first")
            return

        # Get output path
        output_path = filedialog.asksaveasfilename(
            title="Save 3MF File",
            defaultextension=".3mf",
            filetypes=[("3MF files", "*.3mf"), ("All files", "*.*")],
            initialfile=os.path.splitext(os.path.basename(self.image_path))[0] + ".3mf"
        )

        if not output_path:
            return

        try:
            self.progress_var.set(0)
            self.status_var.set("Generating 3MF file...")
            self.root.update()

            # Get settings
            width_mm = float(self.width_var.get())
            base_height = float(self.base_height_var.get())
            layer_height = float(self.layer_height_var.get())
            tolerance = self.tolerance_var.get()
            assign_nearest = self.assign_nearest_var.get()
            optimize = self.optimize_var.get()

            # Generate color map if not already done
            self.progress_var.set(20)
            self.status_var.set("Quantizing image...")
            self.root.update()

            self.color_map, self.quantized_image = quantize_image_fast(
                self.original_image,
                self.selected_colors,
                tolerance,
                assign_nearest
            )

            # Generate meshes
            self.progress_var.set(40)
            self.status_var.set("Generating meshes...")
            self.root.update()

            meshes = generate_color_meshes(
                self.color_map,
                self.selected_colors,
                width_mm,
                base_height,
                layer_height,
                optimize
            )

            if not meshes:
                messagebox.showerror("Error", "No meshes generated. Check that colors are present in the image.")
                self.progress_var.set(0)
                return

            # Export to 3MF
            self.progress_var.set(70)
            self.status_var.set("Exporting to 3MF...")
            self.root.update()

            export_to_3mf(meshes, output_path)

            self.progress_var.set(100)

            # Calculate stats
            total_triangles = sum(len(m.triangles) for m in meshes)

            self.status_var.set(f"Saved: {os.path.basename(output_path)}")
            messagebox.showinfo(
                "Success",
                f"3MF file saved successfully!\n\n"
                f"File: {output_path}\n"
                f"Objects: {len(meshes)}\n"
                f"Total triangles: {total_triangles:,}\n\n"
                f"Open in Orca Slicer to assign filaments and slice."
            )

            self.progress_var.set(0)

        except Exception as e:
            self.progress_var.set(0)
            messagebox.showerror("Error", f"Failed to generate 3MF: {str(e)}")
            self.status_var.set("Generation failed")


def main():
    """Main entry point."""
    root = tk.Tk()

    # Set icon if available
    try:
        # You could add an icon file here
        pass
    except:
        pass

    app = ImageTo3MFApp(root)

    # Center window on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() - root.winfo_width()) // 2
    y = (root.winfo_screenheight() - root.winfo_height()) // 2
    root.geometry(f"+{x}+{y}")

    root.mainloop()


if __name__ == '__main__':
    main()
