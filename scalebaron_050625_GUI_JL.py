# This script sets up a GUI application version of your command-line tool using tkinter
# Core features: Load data, choose element, layout options, preview, and save composite

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.colors import Normalize
from matplotlib import cm
from openpyxl import load_workbook
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import math
import glob
import re
import tempfile
from PIL import Image, ImageTk
import shutil

class CompositeApp:
    def __init__(self, master):
        self.master = master
        master.title("ScaleBarOn v0.8.6")

        self.pixel_size = tk.DoubleVar(value=6.0)
        self.scale_bar_length_um = tk.DoubleVar(value=500.0)
        self.num_rows = tk.IntVar(value=2)
        self.use_log = tk.BooleanVar(value=False)
        self.color_scheme = tk.StringVar(value="jet")
        self.rotate = tk.BooleanVar(value=False)
        self.element = tk.StringVar(value="Cu63")

        self.input_dir = "./testdata"
        self.output_dir = "./OUTPUT"
        os.makedirs(self.output_dir, exist_ok=True)

        self.matrices = []
        self.labels = []
        self.preview_file = None

        self.setup_widgets()

    def setup_widgets(self):
        control_frame = ttk.Frame(self.master)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        preview_frame = ttk.Frame(self.master)
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Controls
        grid_frame = ttk.Frame(control_frame)
        grid_frame.pack(pady=10)

        ttk.Label(grid_frame, text="Element:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(grid_frame, textvariable=self.element).grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(grid_frame, text="Pixel size (µm):").grid(row=1, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(grid_frame, textvariable=self.pixel_size).grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(grid_frame, text="Scale bar length (µm):").grid(row=2, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(grid_frame, textvariable=self.scale_bar_length_um).grid(row=2, column=1, padx=5, pady=2)

        ttk.Label(grid_frame, text="Rows:").grid(row=3, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(grid_frame, textvariable=self.num_rows).grid(row=3, column=1, padx=5, pady=2)

        ttk.Label(grid_frame, text="Color Scheme:").grid(row=4, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(grid_frame, textvariable=self.color_scheme).grid(row=4, column=1, padx=5, pady=2)

        ttk.Checkbutton(grid_frame, text="Use Pseudo-log", variable=self.use_log).grid(row=5, column=0, columnspan=2, pady=2)
        ttk.Checkbutton(grid_frame, text="Rotate Images", variable=self.rotate).grid(row=6, column=0, columnspan=2, pady=2)

        button_frame = ttk.Frame(control_frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Select Input Folder", command=self.select_input_folder).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(button_frame, text="Load Data", command=self.load_data).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(button_frame, text="Preview", command=self.preview_composite).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(button_frame, text="Save", command=self.save_composite).grid(row=1, column=1, padx=5, pady=5)

        self.log = tk.Text(control_frame, height=20, width=40)
        self.log.pack(pady=10)

        # Preview frame
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

    def on_resize(self, event):
        if hasattr(self, 'preview_image'):
            self.update_preview_image()

    def log_print(self, message):
        self.log.insert(tk.END, message + "\n")
        self.log.see(tk.END)
        self.master.update_idletasks()  # Force update of the GUI

    def load_matrix_2d(self, path):
        wb = load_workbook(filename=path, read_only=True, data_only=True)
        ws = wb.active
        return np.array([[cell if isinstance(cell, (int, float)) else np.nan for cell in row] for row in ws.iter_rows(values_only=True)])

    def load_data(self):
        self.log_print("\n🔍 Scanning INPUT folder...")
        element = self.element.get()
        pattern = os.path.join(self.input_dir, f"* {element}_ppm matrix.xlsx")
        files = sorted(glob.glob(pattern))

        if not files:
            messagebox.showerror("Error", f"No files found for element {element}")
            return

        self.matrices = []
        self.labels = []

        for f in files:
            match = re.match(r"(.+)[ _]([A-Za-z]{1,2}\d{2,3})_(ppm|CPS) matrix\.xlsx", os.path.basename(f))
            if match:
                sample, _, _ = match.groups()
                self.labels.append(sample)
                self.matrices.append(self.load_matrix_2d(f))
                self.log_print(f"Loaded: {sample}")

        self.log_print(f"✅ Loaded {len(self.matrices)} matrix files.")

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

        rows = self.num_rows.get()
        cols = math.ceil(len(self.matrices) / rows)
        fig, axs = plt.subplots(rows, cols + 1, figsize=(4 * cols + 1, 4 * rows), gridspec_kw={'width_ratios': [1] * cols + [0.2]})
        cmap = cm.get_cmap(self.color_scheme.get())

        flat_all = np.concatenate([m.flatten() for m in self.matrices])
        scale_max = np.nanpercentile(flat_all, 99)

        if self.use_log.get():
            norm = Normalize(vmin=0, vmax=scale_max)
        else:
            norm = Normalize(vmin=0, vmax=scale_max)

        bg_color = cmap(0)
        fig.patch.set_facecolor(bg_color)
        text_color = 'white' if np.mean(bg_color[:3]) < 0.5 else 'black'

        # Find the maximum dimensions of all matrices
        max_height = max(matrix.shape[0] for matrix in self.matrices)
        max_width = max(matrix.shape[1] for matrix in self.matrices)

        for i, (matrix, label) in enumerate(zip(self.matrices, self.labels)):
            r, c = i // cols, i % cols
            ax = axs[r, c] if rows > 1 else axs[c]

            # Calculate padding to center the matrix
            pad_height = (max_height - matrix.shape[0]) // 2
            pad_width = (max_width - matrix.shape[1]) // 2

            # Pad the matrix to match the maximum dimensions and center it
            padded_matrix = np.pad(matrix, 
                                   ((pad_height, max_height - matrix.shape[0] - pad_height), 
                                    (pad_width, max_width - matrix.shape[1] - pad_width)), 
                                   mode='constant', constant_values=np.nan)
            
            im = ax.imshow(padded_matrix, cmap=cmap, norm=norm, aspect='equal')
            ax.set_title(label, color=text_color)
            ax.axis('off')
            ax.set_facecolor(bg_color)

        # Set color to bg_color and drop axes for the final column of subplots
        for r in range(rows):
            ax = axs[r, -1] if rows > 1 else axs[-1]
            ax.set_facecolor(bg_color)
            ax.axis('off')

        # Add color bar and scale bar to the last column
        last_ax = axs[-1, -1] if rows > 1 else axs[-1]
        last_ax.axis('off')
        last_ax.set_facecolor(bg_color)

        # Create two inset axes for color bar and scale bar
        color_ax = inset_axes(last_ax, width="50%", height="60%", loc='upper left',
                              bbox_to_anchor=(0, 1, 1, 0.6), bbox_transform=last_ax.transAxes)
        scale_ax = inset_axes(last_ax, width="100%", height="40%", loc='lower left',
                              bbox_to_anchor=(0, 0, 1, 0.4), bbox_transform=last_ax.transAxes)

        # Add color bar
        cbar = plt.colorbar(im, cax=color_ax, orientation='vertical')
        cbar.ax.yaxis.set_tick_params(color=text_color)
        cbar.outline.set_edgecolor(text_color)
        plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color=text_color)

        # Add scale bar
        scale_bar_length_pixels = self.scale_bar_length_um.get() / self.pixel_size.get()
        scale_bar_width = scale_bar_length_pixels / max_width
        scale_ax.add_line(plt.Line2D([0.1, 0.1 + scale_bar_width], [0.5, 0.5], color=text_color, linewidth=2, transform=scale_ax.transAxes))
        scale_ax.text(0.1, 0.7, f"{int(self.scale_bar_length_um.get())} µm", color=text_color, ha='left', va='bottom', transform=scale_ax.transAxes)
        scale_ax.axis('off')

        plt.tight_layout()
        
        if preview:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                plt.savefig(tmp_file.name, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
            plt.close(fig)
            
            self.preview_image = Image.open(tmp_file.name)
            self.update_preview_image()
            
            self.preview_file = tmp_file.name
            self.log_print("Preview generated. Click 'Save' to keep this image.")
        else:
            out_path = os.path.join(self.output_dir, self.element.get(), f"{self.element.get()}_composite.png")
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
            plt.close(fig)
            self.log_print(f"✅ Saved composite to {out_path}")

    def update_preview_image(self):
        if hasattr(self, 'preview_image'):
            container_width = self.preview_container.winfo_width()
            container_height = self.preview_container.winfo_height()
            
            img_width, img_height = self.preview_image.size
            aspect_ratio = img_width / img_height
            
            if container_width / container_height > aspect_ratio:
                new_height = container_height
                new_width = int(new_height * aspect_ratio)
            else:
                new_width = container_width
                new_height = int(new_width / aspect_ratio)
            
            resized_image = self.preview_image.resize((new_width, new_height), Image.LANCZOS)
            tk_image = ImageTk.PhotoImage(resized_image)
            
            self.preview_label.config(image=tk_image)
            self.preview_label.image = tk_image  # Keep a reference to prevent garbage collection

if __name__ == '__main__':
    root = tk.Tk()
    app = CompositeApp(root)
    root.mainloop()