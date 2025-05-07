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

        # Matplotlib figure with a frame to maintain aspect ratio
        self.preview_container = ttk.Frame(preview_frame)
        self.preview_container.pack(fill=tk.BOTH, expand=True)
        
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.preview_container)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Bind resize event to update the figure's aspect ratio
        self.preview_container.bind("<Configure>", self.on_resize)

    def select_input_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.input_dir = folder_selected
            self.log_print(f"Input folder updated to: {self.input_dir}")

    def on_resize(self, event):
        # Only update if we have a figure with data
        if hasattr(self, 'current_fig_ratio') and self.current_fig_ratio is not None:
            # Get container dimensions
            width = event.width
            height = event.height
            
            # Calculate the available space while maintaining aspect ratio
            container_ratio = width / height
            
            if container_ratio > self.current_fig_ratio:
                # Container is wider than figure
                new_width = height * self.current_fig_ratio
                new_height = height
            else:
                # Container is taller than figure
                new_width = width
                new_height = width / self.current_fig_ratio
            
            # Update canvas size
            self.canvas.get_tk_widget().config(width=int(new_width), height=int(new_height))

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
        self.generate_composite(preview=False)

    def generate_composite(self, preview=False):
        if not self.matrices:
            self.log_print("⚠️ No data loaded.")
            return

        rows = self.num_rows.get()
        cols = math.ceil(len(self.matrices) / rows)
        fig, axs = plt.subplots(rows, cols + 1, figsize=(4 * (cols + 1), 4 * rows))
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

        for i, (matrix, label) in enumerate(zip(self.matrices, self.labels)):
            r, c = i // cols, i % cols
            ax = axs[r, c] if rows > 1 else axs[c]
            im = ax.imshow(matrix, cmap=cmap, norm=norm)
            ax.set_title(label, color=text_color)
            ax.axis('off')
            ax.set_facecolor(bg_color)

        # Set all subplots in the rightmost column to have axis off and bg_color
        for r in range(rows):
            ax = axs[r, -1] if rows > 1 else axs[-1]
            ax.set_facecolor(bg_color)
            ax.axis('off')

        # Add colorbar in the middle row of the last column
        middle_row = rows // 2
        outer_ax = axs[middle_row, -1] if rows > 1 else axs[-1]
        outer_ax.set_facecolor(bg_color)
        outer_ax.axis('off')

        cax = inset_axes(outer_ax, width="30%", height="100%", loc='center',
                         bbox_to_anchor=(0, 0, 1, 1), bbox_transform=outer_ax.transAxes, borderpad=0)

        cbar = plt.colorbar(im, cax=cax, orientation='vertical')
        cbar.ax.yaxis.set_tick_params(color=text_color)
        cbar.outline.set_edgecolor(text_color)
        plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color=text_color)

        # Add scale bar in the last subplot of the rightmost column
        scale_bar_ax = axs[-1, -1] if rows > 1 else axs[-1]
        scale_bar_length_pixels = self.scale_bar_length_um.get() / self.pixel_size.get()
        scale_bar_ax.set_xlim(0, 1)
        scale_bar_ax.set_ylim(0, 1)
        scale_bar_ax.add_line(plt.Line2D([0.1, 0.1 + scale_bar_length_pixels/100], [0.1, 0.1], 
                                        color=text_color, linewidth=2))
        scale_bar_ax.text(0.1, 0.15, f"{int(self.scale_bar_length_um.get())} µm", 
                         color=text_color, ha='left', va='bottom')
        scale_bar_ax.axis('off')
        scale_bar_ax.set_facecolor(bg_color)

        plt.tight_layout()
        
        # Store the figure's aspect ratio for resizing
        figsize = fig.get_size_inches()
        self.current_fig_ratio = figsize[0] / figsize[1]
        
        if preview:
            # Clear the existing figure
            self.fig.clf()
            
            # Create a new figure with the same properties as the one that would be saved
            self.fig = fig
            
            # Update the canvas with the new figure
            self.canvas.figure = fig
            self.canvas.draw()
            
            # Trigger a resize to maintain aspect ratio
            self.on_resize(type('event', (), {'width': self.preview_container.winfo_width(), 
                                             'height': self.preview_container.winfo_height()})())
        else:
            out_path = os.path.join(self.output_dir, self.element.get(), f"{self.element.get()}_composite.png")
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
            plt.close(fig)
            self.log_print(f"✅ Saved composite to {out_path}")


if __name__ == '__main__':
    root = tk.Tk()
    app = CompositeApp(root)
    root.mainloop()