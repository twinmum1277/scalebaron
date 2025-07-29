import tkinter as tk
from tkinter import filedialog, ttk, messagebox, colorchooser
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.colors import to_rgb
import re
import os

class ElementalMapViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Elemental Map Viewer")

        # Single Element Viewer state
        self.matrix = None
        self.filename = None
        self.units = 'ppm'

        # RGB Overlay state
        self.rgb_data = {'R': None, 'G': None, 'B': None}
        self.rgb_sliders = {}
        self.rgb_labels = {}
        self.file_root_label = None
        self.normalize_var = tk.IntVar()
        # Custom color state for each channel, defaulting to Red, Green, Blue
        self.rgb_colors = {
            'R': '#ff0000',
            'G': '#00ff00',
            'B': '#0000ff'
        }
        self.rgb_color_buttons = {}

        # Create tabs
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill=tk.BOTH, expand=True)

        self.single_tab = tk.Frame(self.tabs)
        self.rgb_tab = tk.Frame(self.tabs)

        self.tabs.add(self.single_tab, text="Single Element")
        self.tabs.add(self.rgb_tab, text="RGB Overlay")

        self.build_single_tab()
        self.build_rgb_tab()

    def build_single_tab(self):
        # Left panel
        control_frame = tk.Frame(self.single_tab, padx=10, pady=10)
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
        self.colormap_menu.bind("<<ComboboxSelected>>", lambda event: self.update_image())

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
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.single_tab)
        self.canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def build_rgb_tab(self):
        control_frame = tk.Frame(self.rgb_tab, padx=10, pady=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y)

        display_frame = tk.Frame(self.rgb_tab)
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.file_root_label = tk.Label(control_frame, text="Dataset: None", font=("Arial", 13, "italic"))
        self.file_root_label.pack(pady=(0, 10))

        # For each channel, add color picker
        for color, default_hex in zip(['Red', 'Green', 'Blue'], ['#ff0000', '#00ff00', '#0000ff']):
            ch = color[0]
            row_frame = tk.Frame(control_frame)
            row_frame.pack(fill=tk.X, pady=(6, 2))
            tk.Button(row_frame, text=f"Load {color} Channel", command=lambda c=ch: self.load_rgb_file(c), font=("Arial", 13)).pack(side=tk.LEFT, fill=tk.X, expand=True)
            # Color picker button
            color_btn = tk.Button(row_frame, width=2, bg=self.rgb_colors[ch], relief=tk.RAISED, command=lambda c=ch: self.pick_channel_color(c))
            color_btn.pack(side=tk.LEFT, padx=(6, 0))
            self.rgb_color_buttons[ch] = color_btn

            elem_label = tk.Label(control_frame, text=f"Loaded Element: None", font=("Arial", 13, "italic"))
            elem_label.pack()
            gradient_canvas = tk.Canvas(control_frame, height=10)
            gradient_canvas.pack(fill=tk.X, padx=5, pady=2)
            self.draw_gradient(gradient_canvas, self.rgb_colors[ch])
            max_slider = tk.Scale(control_frame, from_=0, to=1, resolution=0.01, orient=tk.HORIZONTAL, label=f"{color} Max", font=("Arial", 13))
            max_slider.set(1)
            max_slider.pack(fill=tk.X)
            max_slider.bind("<B1-Motion>", lambda e, c=ch: self.view_rgb_overlay())
            self.rgb_sliders[ch] = {'max': max_slider, 'gradient_canvas': gradient_canvas}
            self.rgb_labels[ch] = {'elem': elem_label}

        tk.Checkbutton(control_frame, text="Normalize to 99th Percentile", variable=self.normalize_var, font=("Arial", 13)).pack(anchor='w', pady=(10, 5))
        tk.Button(control_frame, text="View Overlay", command=self.view_rgb_overlay, font=("Arial", 13)).pack(fill=tk.X, pady=(10, 2))
        tk.Button(control_frame, text="Save RGB Image", command=self.save_rgb_image, font=("Arial", 13)).pack(fill=tk.X)

        self.rgb_figure, self.rgb_ax = plt.subplots()
        self.rgb_ax.axis('off')
        self.rgb_canvas = FigureCanvasTkAgg(self.rgb_figure, master=display_frame)
        self.rgb_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def pick_channel_color(self, channel):
        # Open color chooser dialog
        initial_color = self.rgb_colors[channel]
        color_code = colorchooser.askcolor(title=f"Pick color for {channel} channel", initialcolor=initial_color)
        if color_code and color_code[1]:
            self.rgb_colors[channel] = color_code[1]
            # Update button color
            self.rgb_color_buttons[channel].config(bg=color_code[1])
            # Update gradient
            gradient_canvas = self.rgb_sliders[channel]['gradient_canvas']
            self.draw_gradient(gradient_canvas, color_code[1])
            # Update overlay if visible
            self.view_rgb_overlay()

    def draw_gradient(self, canvas, color):
        canvas.delete("all")
        # Accepts either a color name or a hex string
        try:
            rgb = to_rgb(color)
        except Exception:
            # fallback to red, green, blue
            color = color.lower()
            rgb = {'red': (1,0,0), 'green': (0,1,0), 'blue': (0,0,1)}.get(color, (1,1,1))
        for i in range(256):
            r = int(rgb[0] * i)
            g = int(rgb[1] * i)
            b = int(rgb[2] * i)
            c = f'#{r:02x}{g:02x}{b:02x}'
            canvas.create_line(i, 0, i, 10, fill=c)

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

    def load_rgb_file(self, channel):
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")])
        if not path:
            return
        try:
            df = pd.read_excel(path, header=None) if path.endswith('.xlsx') else pd.read_csv(path, header=None)
            df = df.apply(pd.to_numeric, errors='coerce').dropna(how='all').dropna(axis=1, how='all')
            mat = df.to_numpy()
            self.rgb_data[channel] = mat
            file_name = os.path.basename(path)
            root_name = file_name.split()[0]
            elem = next((part for part in file_name.split() if any(e in part for e in ['ppm', 'CPS'])), 'Unknown')
            self.rgb_labels[channel]['elem'].config(text=f"Loaded Element: {elem.split('_')[0]}")
            if self.file_root_label.cget("text") == "Dataset: None":
                self.file_root_label.config(text=f"Dataset: {root_name}")
            max_val = float(np.nanmax(mat))
            if np.isfinite(max_val):
                self.rgb_sliders[channel]['max'].config(from_=0, to=max_val)
                self.rgb_sliders[channel]['max'].set(max_val)
            messagebox.showinfo("Loaded", f"{channel} channel loaded with shape {mat.shape}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load {channel} channel:\n{e}")

    def view_rgb_overlay(self, event=None):
        def rescale(mat, vmax):
            return np.clip(mat / (vmax + 1e-6), 0, 1)
        def get_scaled_matrix(channel):
            mat = self.rgb_data[channel]
            vmax = self.rgb_sliders[channel]['max'].get()
            if self.normalize_var.get():
                p99 = np.nanpercentile(mat, 99)
                vmax = min(vmax, p99)
            scaled = rescale(mat, vmax)
            scaled[np.isnan(scaled)] = 0
            return scaled
        shape = None
        for ch in 'RGB':
            if self.rgb_data[ch] is not None:
                shape = self.rgb_data[ch].shape
                break
        if shape is None:
            messagebox.showwarning("No Data", "Please load at least one channel.")
            return
        composite = []
        for ch in 'RGB':
            mat = self.rgb_data[ch]
            if mat is None:
                composite.append(np.zeros(shape))
            else:
                composite.append(get_scaled_matrix(ch))
        # Instead of stacking as RGB, use the custom color for each channel
        rgb = np.zeros((shape[0], shape[1], 3), dtype=float)
        for idx, ch in enumerate('RGB'):
            # Get the color for this channel as float RGB
            color_hex = self.rgb_colors[ch]
            try:
                color_rgb = to_rgb(color_hex)
            except Exception:
                color_rgb = [0, 0, 0]
            channel_img = composite[idx][..., np.newaxis] * color_rgb
            rgb += channel_img
        rgb = np.clip(rgb, 0, 1)
        rgb[np.isnan(rgb)] = 0
        black_mask = np.all(rgb == 0, axis=2)
        rgb[black_mask] = [0, 0, 0]
        self.rgb_ax.clear()
        self.rgb_ax.imshow(rgb)
        self.rgb_ax.axis('off')
        self.rgb_figure.tight_layout()
        self.rgb_canvas.draw()

    def save_rgb_image(self):
        if all(self.rgb_data[c] is None for c in 'RGB'):
            return
        out_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if out_path:
            self.rgb_figure.savefig(out_path, dpi=300, bbox_inches='tight')

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1100x700")
    app = ElementalMapViewer(root)
    root.mainloop()
