import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.colors import to_rgb
import re

class ElementalMapViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Elemental Map Viewer")

        self.matrix = None
        self.filename = None
        self.units = 'ppm'

        # Left panel
        control_frame = tk.Frame(root, padx=10, pady=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y)

        # File loading
        tk.Label(control_frame, text="Load Matrix File").pack(anchor='w')
        tk.Button(control_frame, text="Browse...", command=self.load_file).pack(fill=tk.X)
        self.file_label = tk.Label(control_frame, text="No file selected", wraplength=180, fg="gray")
        self.file_label.pack(anchor='w', pady=(0, 10))

        # Colormap selector
        tk.Label(control_frame, text="Select Colormap").pack(anchor='w')
        self.colormap_var = tk.StringVar()
        colormaps = sorted(m for m in plt.colormaps() if not m.endswith("_r"))
        self.colormap_menu = ttk.Combobox(control_frame, textvariable=self.colormap_var, values=colormaps, state='readonly')
        self.colormap_menu.set('viridis')
        self.colormap_menu.pack(fill=tk.X, pady=(0, 10))

        # Min/Max sliders
        tk.Label(control_frame, text="Set Display Limits").pack(anchor='w')
        self.min_slider = tk.Scale(control_frame, from_=0, to=1, resolution=0.1, orient=tk.HORIZONTAL, label='Min', command=self.update_image)
        self.min_slider.pack(fill=tk.X)
        self.max_slider = tk.Scale(control_frame, from_=1, to=1, resolution=0.1, orient=tk.HORIZONTAL, label='Max', command=self.update_image)
        self.max_slider.pack(fill=tk.X, pady=(0, 10))

        # Scale bar settings
        tk.Label(control_frame, text="Scale bar length (µm):").pack(anchor='w')
        self.scale_length_entry = tk.Entry(control_frame)
        self.scale_length_entry.insert(0, '100')
        self.scale_length_entry.pack(fill=tk.X)

        tk.Label(control_frame, text="Pixel size (µm):").pack(anchor='w')
        self.pixel_size_entry = tk.Entry(control_frame)
        self.pixel_size_entry.insert(0, '1.0')
        self.pixel_size_entry.pack(fill=tk.X, pady=(0, 10))

        self.show_colorbar_var = tk.IntVar(value=0)
        self.show_scalebar_var = tk.IntVar(value=0)
        tk.Checkbutton(control_frame, text="Show Color Bar", variable=self.show_colorbar_var, command=self.update_image).pack(anchor='w')
        tk.Checkbutton(control_frame, text="Show Scale Bar", variable=self.show_scalebar_var, command=self.update_image).pack(anchor='w')

        # Export
        tk.Button(control_frame, text="Save as PNG", command=self.save_image).pack(fill=tk.X, pady=(20, 0))

        # Right panel for image display
        self.figure, self.ax = plt.subplots()
        self.ax.axis('off')
        self.canvas = FigureCanvasTkAgg(self.figure, master=root)
        self.canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")])
        if not file_path:
            return

        try:
            if file_path.endswith(".xlsx"):
                df = pd.read_excel(file_path, header=None)
            else:
                df = pd.read_csv(file_path, header=None)

            df = df.apply(pd.to_numeric, errors='coerce')
            df.dropna(how='all', inplace=True)
            df.dropna(axis=1, how='all', inplace=True)
            matrix = df.to_numpy()

            if np.isnan(matrix).all():
                messagebox.showerror("Error", "Matrix contains no valid numeric data.")
                return

            self.matrix = matrix
            self.filename = file_path.split("/")[-1]
            self.file_label.config(text=self.filename)

            self.units = 'ppm' if 'ppm' in self.filename else 'CPS' if 'CPS' in self.filename else ''

            min_val = float(np.nanmin(self.matrix))
            max_val = float(np.nanmax(self.matrix))
            if not np.isfinite(min_val) or not np.isfinite(max_val):
                messagebox.showerror("Error", "Unable to determine value range.")
                return

            step = (max_val - min_val) / 500 if max_val > min_val else 1.0
            self.min_slider.config(from_=min_val, to=max_val, resolution=step)
            self.max_slider.config(from_=min_val, to=max_val, resolution=step)
            self.min_slider.set(min_val)
            self.max_slider.set(max_val)

            self.update_image()
        except Exception as e:
            messagebox.showerror("File Load Error", f"An error occurred:\n{e}")

    def update_image(self, event=None):
        if self.matrix is None:
            return

        raw_vmin = self.min_slider.get()
        raw_vmax = self.max_slider.get()

        if raw_vmin >= raw_vmax:
            raw_vmax = raw_vmin + 1e-6

        self.ax.clear()

        for cbar_ax in self.figure.axes[1:]:
            self.figure.delaxes(cbar_ax)

        masked_matrix = np.ma.masked_invalid(self.matrix)
        actual_min = np.nanmin(self.matrix)
        actual_max = np.nanmax(self.matrix)
        vmin = max(actual_min, raw_vmin)
        vmax = min(actual_max, raw_vmax)

        cmap_name = self.colormap_var.get()
        cmap = plt.get_cmap(cmap_name).copy()
        rgba_min = cmap((vmin - actual_min) / (actual_max - actual_min + 1e-9))
        cmap.set_bad(color=rgba_min)

        im = self.ax.imshow(masked_matrix, cmap=cmap, vmin=vmin, vmax=vmax)

        if self.show_colorbar_var.get():
            from mpl_toolkits.axes_grid1 import make_axes_locatable
            divider = make_axes_locatable(self.ax)
            cax = divider.append_axes("right", size="5%", pad=0.05)
            cbar = self.figure.colorbar(im, cax=cax, orientation='vertical')
            cbar.set_label(self.units)

        if self.show_scalebar_var.get():
            try:
                pixel_size = float(self.pixel_size_entry.get())
                scale_len = float(self.scale_length_entry.get())
                num_pixels = int(scale_len / pixel_size)

                # Add the scale bar outside image at top-left
                self.figure.subplots_adjust(top=0.90)  # shrink plot slightly to make room
                self.figure.text(0.05, 0.93, f'{scale_len} µm', ha='left', va='center', fontsize=8)
                self.figure.lines.append(plt.Line2D([0.05, 0.05 + (num_pixels / self.matrix.shape[1]) * 0.9], [0.91, 0.91],
                                                    transform=self.figure.transFigure, color='black', linewidth=2))
            except ValueError:
                pass

        self.ax.axis('off')
        self.figure.tight_layout()
        self.canvas.draw()

    def save_image(self):
        if self.matrix is None:
            return
        out_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png")])
        if out_path:
            self.figure.savefig(out_path, dpi=300, bbox_inches='tight')

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x700")
    app = ElementalMapViewer(root)
    root.mainloop()
