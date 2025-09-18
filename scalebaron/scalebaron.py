# This script sets up a GUI application version of your command-line tool using tkinter
# Core features: Load data, choose element, layout options, preview, and save composite
# TP: THIS VERSION CLONED from Josh's most recent upload, with user-friendly GUI layout changes, 3 sig fig constraint, ppm or CPS input

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, font
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.colors import Normalize, LogNorm
from matplotlib import cm
from openpyxl import load_workbook
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import math
import glob
import re
import tempfile
import time
from PIL import Image, ImageTk
import shutil
import pandas as pd

class CompositeApp:
    
    def get_contrasting_text_color(self, cmap_name):
        rgba = plt.get_cmap(cmap_name)(0.0)  # Color for 0 value
        r, g, b = rgba[:3]
        brightness = 0.299 * r + 0.587 * g + 0.114 * b
        return 'black' if brightness > 0.5 else 'white'
    
    def pseudolog_norm(self, vmin=1, vmax=100):
        """
        Returns a Normalize-like object for pseudolog scaling.
        This is a simple implementation: log(x+1) scaling, so that 0 maps to 0.
        """
        class PseudoLogNorm(Normalize):
            def __init__(self, vmin=None, vmax=None, clip=False):
                super().__init__(vmin, vmax, clip)
            def __call__(self, value, clip=None):
                vmin, vmax = self.vmin, self.vmax
                value = np.asarray(value)
                # Avoid negative/NaN
                value = np.where(value < 0, 0, value)
                # log1p for pseudo-log
                normed = (np.log1p(value) - np.log1p(vmin)) / (np.log1p(vmax) - np.log1p(vmin))
                return np.clip(normed, 0, 1)
            def inverse(self, value):
                vmin, vmax = self.vmin, self.vmax
                return np.expm1(value * (np.log1p(vmax) - np.log1p(vmin)) + np.log1p(vmin))
        return PseudoLogNorm(vmin=vmin, vmax=vmax)

    def __init__(self, master):
        self.master = master
        master.title("ScaleBarOn Multi Map Scaler: v0.8.8")

        self.pixel_size = tk.DoubleVar(value=6)
        self.scale_bar_length_um = tk.DoubleVar(value=500)
        self.num_rows = tk.IntVar(value=5)
        self.use_log = tk.BooleanVar(value=False)
        self.color_scheme = tk.StringVar(value="jet")
        self.element = tk.StringVar()
        self.sample_name_font_size = tk.StringVar(value="n/a")  # Default to "n/a"
        self.scale_max = tk.DoubleVar(value=1.0)  # New variable for scale_max, constrained to 2 decimal places
        self.use_custom_pixel_sizes = tk.BooleanVar(value=False)  # New variable for custom pixel sizes

        self.input_dir = None
        self.output_dir = "./OUTPUT"
        os.makedirs(self.output_dir, exist_ok=True)

        self.matrices = []
        self.labels = []
        self.preview_file = None
        self.custom_pixel_sizes = {}  # Dictionary to store custom pixel sizes
        self.adjusted_dimensions = []  # List to store pixel size adjusted dimensions
        self.pixel_sizes_by_sample = {}
        self.scale_factors = {}  # New dictionary to store scale factors for each matrix
        style = ttk.Style()
        style.configure("Hint.TLabel", foreground="gray", font=("TkDefaultFont", 12, "italic"))
        self.setup_widgets()

    def setup_widgets(self):
        control_frame = ttk.Frame(self.master)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        preview_frame = ttk.Frame(self.master)
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

         # Select Input Folder at the top
        ttk.Button(control_frame, text="Select Input Folder", command=self.select_input_folder).pack(pady=5)

        # Control panel inside grid_frame
        grid_frame = ttk.Frame(control_frame)
        grid_frame.pack(pady=10)

        # Element dropdown
        ttk.Label(grid_frame, text="Element:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        self.element_dropdown = ttk.Combobox(grid_frame, textvariable=self.element, state="disabled")
        self.element_dropdown.grid(row=0, column=1, padx=5, pady=2)

        # Pixel Size input
        ttk.Label(grid_frame, text="Pixel Size (µm):").grid(row=1, column=0, sticky="e", padx=(0, 2), pady=2)

        # Create a horizontal frame for entry + hint
        pixel_entry_frame = ttk.Frame(grid_frame)
        pixel_entry_frame.grid(row=1, column=1, sticky="w", padx=5, pady=2)

        # Inside the frame: entry box + grey italic label
        ttk.Entry(pixel_entry_frame, textvariable=self.pixel_size, width=10).pack(side="left")
        ttk.Label(pixel_entry_frame, text="Hint: In your metadata", style="Hint.TLabel").pack(side="left", padx=(4, 0))
        
        # Combine the checkbox and Pixel Sizes button in one horizontal frame
        multi_size_frame = ttk.Frame(grid_frame)
        multi_size_frame.grid(row=2, column=1, columnspan=2, sticky="w", pady=(0, 10))

        ttk.Checkbutton(multi_size_frame, text="Multiple sizes?", variable=self.use_custom_pixel_sizes).pack(side="left")
        ttk.Button(multi_size_frame, text="Pixel Sizes", command=self.handle_pixel_sizes).pack(side="left", padx=(5, 0))

        # Scale bar length
        ttk.Label(grid_frame, text="Scale bar length (µm):").grid(row=3, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(grid_frame, textvariable=self.scale_bar_length_um).grid(row=3, column=1, padx=5, pady=2)

        # Rows
        ttk.Label(grid_frame, text="Rows:").grid(row=4, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(grid_frame, textvariable=self.num_rows).grid(row=4, column=1, padx=5, pady=2)

        # Color scheme
        ttk.Label(grid_frame, text="Color Scheme:").grid(row=5, column=0, sticky="e", padx=5, pady=2)
        self.color_scheme_dropdown = ttk.Combobox(grid_frame, textvariable=self.color_scheme, values=plt.colormaps())
        self.color_scheme_dropdown.grid(row=5, column=1, padx=5, pady=2)

        # Font size
        ttk.Label(grid_frame, text="Sample Name Font Size:").grid(row=6, column=0, sticky="e", padx=5, pady=2)
        self.sample_name_font_size_dropdown = ttk.Combobox(grid_frame, textvariable=self.sample_name_font_size, values=["n/a", "Small", "Medium", "Large"])
        self.sample_name_font_size_dropdown.grid(row=6, column=1, padx=5, pady=2)

        # Scale max
        ttk.Label(grid_frame, text="Scale Max:").grid(row=7, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(grid_frame, textvariable=self.scale_max).grid(row=7, column=1, padx=5, pady=2)

        # Pseudolog Scale option
        ttk.Checkbutton(grid_frame, text="Log Scale", variable=self.use_log).grid(row=8, column=0, columnspan=2, pady=2)

        button_frame = ttk.Frame(control_frame)
        button_frame.pack(pady=10)

        # Step 1: Summarize
        ttk.Label(button_frame, text="Step 1: Calculate statistics", style="Hint.TLabel").grid(row=0, column=0, padx=5, pady=(5, 0), sticky="w")
        ttk.Button(button_frame, text="Summarize Data", command=self.load_data).grid(row=1, column=0, padx=5, pady=(0, 10), sticky="ew")

        # Step 2: Preview
        ttk.Label(button_frame, text="Step 2:", style="Hint.TLabel").grid(row=2, column=0, padx=5, pady=(0, 0), sticky="w")
        ttk.Button(button_frame, text="Preview Composite", command=self.preview_composite).grid(row=3, column=0, padx=5, pady=(0, 10), sticky="ew")

        # Step 3: Export
        ttk.Label(button_frame, text="Step 3:", style="Hint.TLabel").grid(row=4, column=0, padx=5, pady=(0, 0), sticky="w")
        ttk.Button(button_frame, text="Save Composite", command=self.save_composite).grid(row=5, column=0, padx=5, pady=(0, 10), sticky="ew")

        ttk.Label(control_frame, text="Progress:", style="Hint.TLabel").pack(anchor="w", padx=5, pady=(10, 0))

        custom_font = font.Font(family="Arial", size=13, slant="roman")
        self.log = tk.Text(control_frame, height=20, width=40, wrap="word", font=custom_font)
        self.log.pack(pady=10)

        # Window into ScaleBarOn's soul:     
        self.preview_container = ttk.Frame(preview_frame)
        self.preview_container.pack(fill=tk.BOTH, expand=True)
        
        self.preview_label = ttk.Label(self.preview_container)
        self.preview_label.pack(fill=tk.BOTH, expand=True)
        
        # Bind resize event to update the preview image's aspect ratio
        self.preview_container.bind("<Configure>", self.on_resize)

    def select_input_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.input_dir = folder_selected
            self.log_print(f"Input folder updated to: {self.input_dir}")
            self.update_element_dropdown()

    def select_output_folder(self):
        messagebox.showinfo("Directory Selection", "Select Output Directory for Histograms, Statistics, and Plots (Cancel to set default to ./OUTPUT)")

        folder_selected = filedialog.askdirectory(initialdir=".", title="Select Output Directory (Cancel to set default to ./OUTPUT)")
        if folder_selected:
            self.output_dir = folder_selected
            self.log_print(f"Output folder updated to: {self.output_dir}")
        else:
            self.output_dir = "./OUTPUT"
            self.log_print("Using default output folder: ./OUTPUT")

    def update_element_dropdown(self):
        elements = set()
        for file in glob.glob(os.path.join(self.input_dir, "*.xlsx")):
            match = re.search(r"([A-Za-z]{1,2}\d{2,3})_(ppm|CPS) matrix\.xlsx", file)
            if match:
                elements.add(match.group(1))
        
        if elements:
            self.element_dropdown['values'] = sorted(list(elements))
            self.element_dropdown['state'] = 'readonly'
            self.element.set(next(iter(elements)))  # Set the first element as default
        else:
            self.log_print("No valid element files found in the selected directory.")

    def on_resize(self, event):
        if hasattr(self, 'preview_image'):
            # Only update if the resize is significant enough to avoid excessive updates
            if hasattr(self, '_last_resize_time'):
                current_time = time.time()
                if current_time - self._last_resize_time < 0.1:  # Throttle to max 10 updates per second
                    return
                self._last_resize_time = current_time
            else:
                self._last_resize_time = time.time()
            
            self.update_preview_image()

    def log_print(self, message):
        self.log.insert(tk.END, message + "\n")
        self.log.see(tk.END)
        self.master.update_idletasks()  # Force update of the GUI

    def load_matrix_2d(self, path):
        wb = load_workbook(filename=path, read_only=True, data_only=True)
        ws = wb.active
        return np.array([[cell if isinstance(cell, (int, float)) and cell >= 0 else np.nan for cell in row] for row in ws.iter_rows(values_only=True)])

    def import_custom_pixel_sizes(self):
        messagebox.showinfo("Load Custom Physical Pixel Size", "Select CSV file with custom pixel sizes (Cancel to generate template)")

        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")], title="Select Custom Pixel Sizes CSV (Cancel to generate template)")
        if file_path:
            try:
                df = pd.read_csv(file_path)
                self.custom_pixel_sizes = dict(zip(df['Sample'], df['Pixel Size']))
                self.log_print(f"Imported custom pixel sizes for {len(self.custom_pixel_sizes)} samples.")
            except Exception as e:
                self.log_print(f"Error importing custom pixel sizes: {str(e)}")
                self.generate_pixel_size_template()
        else:
            self.generate_pixel_size_template()

    def generate_pixel_size_template(self):
        if not self.input_dir:
            messagebox.showerror("Error", "Please select an input folder first.")
            return

        samples = set()
        for file in glob.glob(os.path.join(self.input_dir, "*.xlsx")):
            match = re.match(r"(.+)[ _]([A-Za-z]{1,2}\d{2,3})_(ppm|CPS) matrix\.xlsx", os.path.basename(file))
            if match:
                sample = match.group(1)
                samples.add(sample)

        if not samples:
            messagebox.showerror("Error", "No valid sample files found in the input directory.")
            return

        df = pd.DataFrame({'Sample': list(samples), 'Pixel Size': self.pixel_size.get()})
        
        save_path = filedialog.asksaveasfilename(
            title="Save Pixel Size Template",
            defaultextension=".csv", 
            filetypes=[("CSV files", "*.csv")]
        )
        if save_path:
            df.to_csv(save_path, index=False)
            self.log_print(f"✅ Saved pixel size template to {save_path}")

    def handle_pixel_sizes(self):
        if not self.input_dir:
            messagebox.showerror("Error", "Please select an input folder first.")
            return

        self.import_custom_pixel_sizes()

    def load_data(self):
        if not self.input_dir:
            messagebox.showerror("Error", "Please select an input folder first.")
            return

        self.select_output_folder()

        self.log_print("\n🔍 Scanning INPUT folder...")
        element = self.element.get()
        pattern_ppm = os.path.join(self.input_dir, f"* {element}_ppm matrix.xlsx")
        pattern_CPS = os.path.join(self.input_dir, f"* {element}_CPS matrix.xlsx")
        files = sorted(glob.glob(pattern_ppm) + glob.glob(pattern_CPS))

        if not files:
            messagebox.showerror("Error", f"No files found for element {element}")
            return

        self.matrices = []
        self.labels = []
        self.adjusted_dimensions = []
        percentiles = []
        iqrs = []
        means = []

        # If using custom pixel sizes, only load data for samples present in the custom file
        samples_to_load = set(self.custom_pixel_sizes.keys()) if self.use_custom_pixel_sizes.get() else None

        max_physical_width = 0
        max_physical_height = 0

        for f in files:
            match = re.match(r"(.+)[ _]([A-Za-z]{1,2}\d{2,3})_(ppm|CPS) matrix\.xlsx", os.path.basename(f))
            if match:
                sample, _, _ = match.groups()
                if samples_to_load is None or sample in samples_to_load:
                    self.labels.append(sample)
                    matrix = self.load_matrix_2d(f)
                    self.matrices.append(matrix)
                    
                    # Get the pixel size for this sample
                    if self.use_custom_pixel_sizes.get() and sample in self.custom_pixel_sizes:
                        pixel_size = self.custom_pixel_sizes[sample]
                    else:
                        pixel_size = self.pixel_size.get()

                    # Calculate physical dimensions
                    physical_height, physical_width = matrix.shape[0] * pixel_size, matrix.shape[1] * pixel_size
                    max_physical_height = max(max_physical_height, physical_height)
                    max_physical_width = max(max_physical_width, physical_width)
                    
                    # Calculate percentiles, IQR, and mean
                    p25, p50, p75, p99 = np.nanpercentile(matrix, [25, 50, 75, 99])
                    iqr = p75 - p25
                    mean = np.nanmean(matrix)
                    percentiles.append((sample, p25, p50, p75, p99))
                    iqrs.append((sample, iqr))
                    means.append((sample, mean))
                    
                    # Generate and save histogram
                    plt.figure(figsize=(10, 6))
                    plt.hist(matrix.flatten(), bins=50, range=(0, np.nanpercentile(matrix, 99)))
                    plt.title(f"Histogram for {sample}")
                    plt.xlabel("Value")
                    plt.ylabel("Frequency")
                    hist_path = os.path.join(self.output_dir, self.element.get(), 'Histograms', f"{sample}_histogram.png")
                    os.makedirs(os.path.dirname(hist_path), exist_ok=True)
                    plt.savefig(hist_path)
                    plt.close()

        # Calculate scale factors and adjusted dimensions
        # max_physical_dim = max(max_physical_height, max_physical_width)
        max_dimension = "height" if max_physical_height > max_physical_width else "width"
        self.reference_pixel_size = None
        for i, (matrix, label) in enumerate(zip(self.matrices, self.labels)):
            pixel_size = self.custom_pixel_sizes.get(label, self.pixel_size.get())
            physical_height, physical_width = matrix.shape[0] * pixel_size, matrix.shape[1] * pixel_size
            if max_dimension == "height":
                scale_factor = physical_height / max_physical_height
            else:
                scale_factor = physical_width / max_physical_width
            self.scale_factors[label] = scale_factor
            if scale_factor == 1.0:
                self.reference_pixel_size = pixel_size
            adjusted_height = int(matrix.shape[0] * scale_factor)
            adjusted_width = int(matrix.shape[1] * scale_factor)
            self.adjusted_dimensions.append((adjusted_height, adjusted_width))
        assert self.reference_pixel_size is not None, "No reference pixel size found"

        self.log_print(f"✅ Loaded {len(self.matrices)} matrix files.")
        self.log_print(f"Histograms saved in: {os.path.join(self.output_dir, self.element.get(), 'histograms')}")

        # Save percentiles, IQR, and mean table
        percentiles_df = pd.DataFrame(percentiles, columns=['Sample', '25th Percentile', '50th Percentile', '75th Percentile', '99th Percentile'])
        iqr_df = pd.DataFrame(iqrs, columns=['Sample', 'IQR'])
        mean_df = pd.DataFrame(means, columns=['Sample', 'Mean'])
        stats_df = percentiles_df.merge(iqr_df, on='Sample').merge(mean_df, on='Sample')
        stats_df = stats_df.map(lambda x: float(f"{x:.5g}") if isinstance(x, (int, float)) else x) # Round Summary Statistics to 5 significant figures
        stats_path = os.path.join(self.output_dir, self.element.get(), f"{self.element.get()}_statistics.csv")
        stats_df.to_csv(stats_path, index=False)
        self.log_print(f"✅ Saved statistics table to {stats_path}")

        # Set scale_max based on 99th percentile of all data
        overall_99th = np.nanpercentile(np.hstack([m.flatten() for m in self.matrices]), 99)
        self.scale_max.set(round(overall_99th,3))
        self.log_print(f"Scale max set to {self.scale_max.get():.2f} based on overall 99th percentile")

    def preview_composite(self):
        self.generate_composite(preview=True)

    def save_composite(self):
        if self.preview_file:
            out_path = os.path.join(self.output_dir, self.element.get(), f"{self.element.get()}_composite.png")
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            shutil.move(self.preview_file, out_path)
            self.log_print(f"✅ Saved composite to {out_path}")
            self.preview_file = None
        else:
            self.generate_composite(preview=False)

    def generate_composite(self, preview=False):
        if not self.matrices:
            self.log_print("⚠️ No data loaded.")
            return

        rows = min(self.num_rows.get(), len(self.matrices))  # Ensure rows don't exceed number of samples
        cols = math.ceil(len(self.matrices) / rows)
        fig, axs = plt.subplots(rows, cols + 1, figsize=(4 * cols + 1, 4 * rows), gridspec_kw={'width_ratios': [1] * cols + [0.2]})
        cmap = matplotlib.colormaps.get_cmap(self.color_scheme.get())

        scale_max = self.scale_max.get()

        if self.use_log.get():
            norm = self.pseudolog_norm(vmin=1, vmax=scale_max)
        else:
            norm = Normalize(vmin=0, vmax=scale_max)

        bg_color = cmap(0)
        fig.patch.set_facecolor(bg_color)
        text_color = 'white' if np.mean(bg_color[:3]) < 0.5 else 'black'

        # Find the maximum dimensions of all adjusted matrices
        max_height = max(dim[0] for dim in self.adjusted_dimensions)
        max_width = max(dim[1] for dim in self.adjusted_dimensions)

        percentiles = []
        iqrs = []
        means = []

        for i, (matrix, label) in enumerate(zip(self.matrices, self.labels)):
            r, c = i // cols, i % cols
            ax = axs[r, c] if rows > 1 else axs[c]

            # Get the pixel size for this sample
            if self.use_custom_pixel_sizes.get() and label in self.custom_pixel_sizes:
                pixel_size = self.custom_pixel_sizes[label]
            else:
                pixel_size = self.pixel_size.get()

            # Use the pre-calculated scale factor
            scale_factor = self.scale_factors[label]

            # Calculate the size of the inset axes
            inset_width = min(1.0, matrix.shape[1] * scale_factor / max_width)
            inset_height = min(1.0, matrix.shape[0] * scale_factor / max_height)

            # Create inset axes
            inset_ax = inset_axes(ax, width=f"{scale_factor*100}%", height=f"{scale_factor*100}%", loc='center',
                                #   bbox_to_anchor=((1-inset_width)/2, (1-inset_height)/2, inset_width, inset_height),
                                  bbox_transform=ax.transAxes)

            # Determine font size based on selection
            font_size = None
            if self.sample_name_font_size.get() == "Small":
                font_size = 8
            elif self.sample_name_font_size.get() == "Medium":
                font_size = 12
            elif self.sample_name_font_size.get() == "Large":
                font_size = 16

            im = inset_ax.imshow(matrix, cmap=cmap, norm=norm, aspect='equal')
            report_custom_pixel_sizes=False
            ax.set_title(f"{label}"+(f"\n({pixel_size:.2f} µm/pixel)" if report_custom_pixel_sizes else ""), color=text_color, fontsize=font_size)
            ax.axis('off')
            inset_ax.axis('off')
            ax.set_facecolor(bg_color)
            inset_ax.set_facecolor(bg_color)

            # Save individual subplot
            subplot_path = os.path.join(self.output_dir, self.element.get(), 'subplots', f"{label}.png")
            os.makedirs(os.path.dirname(subplot_path), exist_ok=True)
            
            # Create a new figure for the individual subplot
            subplot_fig, subplot_ax = plt.subplots()
            subplot_fig.patch.set_facecolor(bg_color)
            subplot_ax.set_facecolor(bg_color)
            
            # Create a masked array for NaN values
            masked_matrix = np.ma.masked_where(np.isnan(matrix), matrix)
            
            # Plot with transparency for NaN values
            subplot_ax.imshow(masked_matrix, cmap=cmap, norm=norm, aspect='equal')
            subplot_ax.set_title(f"{label}", color=text_color, fontsize=font_size)
            subplot_ax.axis('off')
            subplot_fig.savefig(subplot_path, dpi=300, bbox_inches='tight', transparent=True)
            plt.close(subplot_fig)

            # Calculate percentiles, IQR, and mean
            p25, p50, p75, p99 = np.nanpercentile(matrix, [25, 50, 75, 99])
            iqr = p75 - p25
            mean = np.nanmean(matrix)
            percentiles.append((label, p25, p50, p75, p99))
            iqrs.append((label, iqr))
            means.append((label, mean))

        last_ax = axs[-1, -1] if rows > 1 else axs[-1]
        last_ax.axis('off')
        last_ax.set_facecolor(bg_color)

        # Create two inset axes for color bar and scale bar
        color_ax = inset_axes(last_ax, width="100%", height="100%", loc='upper left',
                              bbox_to_anchor=(0, 0.5, 0.5, 0.5), 
                              bbox_transform=last_ax.transAxes)
        color_ax.set_facecolor(bg_color)
        # Shrink inset height to leave less space under colorbar
        scale_ax = inset_axes(
            last_ax, width="100%", height="100%", loc='lower left',
            bbox_to_anchor=(0, 0, 0.5, 0.35),  # reduced height
            bbox_transform=last_ax.transAxes
        )

        scale_ax.set_facecolor(bg_color)

        # Add color bar
        cbar = plt.colorbar(im, cax=color_ax, orientation='vertical')
        cbar.ax.yaxis.set_tick_params(color=text_color)
        cbar.outline.set_edgecolor(text_color)
        plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color=text_color)

        # Add scale bar (fixed calculation)
        max_pixel_size = max(self.custom_pixel_sizes.values()) if self.use_custom_pixel_sizes.get() else self.pixel_size.get()
        pixel_size_um = max_pixel_size  # microns per pixel

        # Assume matrices[0] is representative of image dimensions
        image_width_pixels = self.matrices[0].shape[1]  # get width in pixels

        # --- Draw scale bar in data coordinates ---
        #Avoid crashing when a label isn't found
        # pixel_size_um = self.pixel_sizes_by_sample.get(label, self.pixel_size.get())


        # # Get pixel size for this sample
        # pixel_size_um = self.pixel_sizes_by_sample.get(label, self.pixel_size.get())
        pixel_size_um = self.reference_pixel_size 
        scale_bar_um = self.scale_bar_length_um.get()  # e.g., 500

        
        # Convert to pixels
        scale_bar_px = int(scale_bar_um / pixel_size_um)

        # Position: bottom-left of the image
        bar_height = matrix.shape[0]  # number of rows (height in pixels)
        bar_width = matrix.shape[1]   # number of cols (width in pixels)

        # Padding in pixels from edge
        pad_x = 10
        pad_y = 10

        

        # Keep scale_ax data limits compact
        scale_ax.set_xlim(0, scale_bar_px + 20)
        scale_ax.set_ylim(0, 25)  # lower max = tighter spacing
        scale_ax.axis('off')

        # Redefine layout
        x_start = 10
        x_end = x_start + scale_bar_px
        y_pos = 8  # lower bar

        # Draw bar
        scale_ax.hlines(y=y_pos, xmin=x_start, xmax=x_end, colors='white', linewidth=3)

        # Centered label just above
        scale_ax.text(
            (x_start + x_end) / 2,
            y_pos + 4,  # tighter vertical gap
            f"{scale_bar_um:.0f} µm",
            color='white',
            fontsize=8,
            ha='center',
            va='bottom'
        )
        
        # Set background color for all axes
        for ax in axs.flat:
            ax.set_facecolor(bg_color)
            ax.axis('off')
            # Set background color for any inset axes
            for child in ax.get_children():
                if isinstance(child, plt.Axes):
                    child.set_facecolor(bg_color)
        
        # Create standalone colorbar figure
        colorbar_fig, colorbar_ax = plt.subplots(figsize=(1, 4))
        colorbar_fig.patch.set_alpha(0.0)
        colorbar_ax.set_facecolor('none')

        # Re-create colorbar and apply styles again
        export_cbar = plt.colorbar(im, cax=colorbar_ax, orientation='vertical')

        # Reapply tick and outline styling
        export_cbar.ax.yaxis.set_tick_params(color=text_color)
        export_cbar.outline.set_edgecolor(text_color)
        plt.setp(plt.getp(export_cbar.ax.axes, 'yticklabels'), color=text_color)

        # Save
        colorbar_path = os.path.join(self.output_dir, self.element.get(), f"{self.element.get()}_colorbar.png")
        colorbar_fig.savefig(colorbar_path, dpi=300, bbox_inches='tight', transparent=True)
        plt.close(colorbar_fig)
        self.log_print(f"✅ Saved separate colorbar to {colorbar_path}")
        
        if preview:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                plt.savefig(tmp_file.name, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
            plt.close(fig)
            
            self.log_print(f"Preview image saved to temporary file: {tmp_file.name}")
            self.preview_image = Image.open(tmp_file.name)
            self.log_print(f"Preview image loaded: {self.preview_image.size}")
            
            # Force GUI update and layout before trying to display preview
            self.master.update_idletasks()
            self.preview_container.update_idletasks()
            self.update_preview_image()
            
            self.preview_file = tmp_file.name
            self.log_print("Preview generated. Click 'Save' to keep this image.")
        else:
            out_path = os.path.join(self.output_dir, self.element.get(), f"{self.element.get()}_composite.png")
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
            plt.close(fig)
            self.log_print(f"✅ Saved composite to {out_path}")

            # Save percentiles, IQR, and mean table
            percentiles_df = pd.DataFrame(percentiles, columns=['Sample', '25th Percentile', '50th Percentile', '75th Percentile', '99th Percentile'])
            iqr_df = pd.DataFrame(iqrs, columns=['Sample', 'IQR'])
            mean_df = pd.DataFrame(means, columns=['Sample', 'Mean'])
            stats_df = percentiles_df.merge(iqr_df, on='Sample').merge(mean_df, on='Sample')
            stats_path = os.path.join(self.output_dir, self.element.get(), f"{self.element.get()}_statistics.csv")
            stats_df.to_csv(stats_path, index=False)
            self.log_print(f"✅ Saved statistics table to {stats_path}")

    def update_preview_image(self):
        if hasattr(self, 'preview_image'):
            container_width = self.preview_container.winfo_width()
            container_height = self.preview_container.winfo_height()
            
            # Only handle zero dimensions (the crash case), otherwise use original simple logic
            if container_width <= 0 or container_height <= 0:
                # Get window dimensions as fallback - but be more aggressive about using them
                window_width = self.master.winfo_width()
                window_height = self.master.winfo_height()
                
                if window_width > 0 and window_height > 0:
                    # Use most of the window space, like the original would have
                    container_width = window_width - 200  # Minimal space for control panel
                    container_height = window_height - 50  # Minimal space for window chrome
                else:
                    # Only use fallback if window isn't ready either
                    container_width = 800
                    container_height = 600
                
                # Schedule one retry to get proper container dimensions
                self.master.after(200, self.update_preview_image)
            
            img_width, img_height = self.preview_image.size
            
            # Basic safety check for image dimensions
            if img_width <= 0 or img_height <= 0:
                return
            
            # Original simple aspect ratio logic
            aspect_ratio = img_width / img_height
            
            if container_width / container_height > aspect_ratio:
                new_height = container_height
                new_width = int(new_height * aspect_ratio)
            else:
                new_width = container_width
                new_height = int(new_width / aspect_ratio)
            
            # Basic safety checks
            if new_width <= 0 or new_height <= 0:
                return
            
            try:
                resized_image = self.preview_image.resize((new_width, new_height), Image.LANCZOS)
                tk_image = ImageTk.PhotoImage(resized_image)
                
                self.preview_label.config(image=tk_image)
                self.preview_label.image = tk_image  # Keep a reference to prevent garbage collection
            except Exception as e:
                # Log the error but don't crash the application
                self.log_print(f"Warning: Failed to resize preview image: {e}")

def main():
    root = tk.Tk()
    app = CompositeApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()