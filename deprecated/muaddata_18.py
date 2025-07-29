# Muad'Data v17 - Fully Functional Element Viewer + RGB Overlay Tabs
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os

class MuadDataViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Muad'Data - Elemental Map Viewer")

        # Single Element Viewer state
        self.single_matrix = None
        self.single_colormap = tk.StringVar(value='viridis')
        self.single_min = tk.DoubleVar()
        self.single_max = tk.DoubleVar()
        self.show_colorbar = tk.IntVar()
        self.show_scalebar = tk.IntVar()
        self.pixel_size = tk.DoubleVar(value=1.0)
        self.scale_length = tk.DoubleVar(value=50)

        # RGB Overlay state
        self.rgb_data = {'R': None, 'G': None, 'B': None}
        self.rgb_sliders = {}
        self.rgb_labels = {}
        self.file_root_label = None
        self.normalize_var = tk.IntVar()

        # Tabs
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill=tk.BOTH, expand=True)

        self.single_tab = tk.Frame(self.tabs)
        self.rgb_tab = tk.Frame(self.tabs)

        self.tabs.add(self.single_tab, text="Element Viewer")
        self.tabs.add(self.rgb_tab, text="RGB Overlay")

        self.build_single_tab()
        self.build_rgb_tab()

    def build_single_tab(self):
        control_frame = tk.Frame(self.single_tab, padx=10, pady=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y)

        display_frame = tk.Frame(self.single_tab)
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Button(control_frame, text="Load Matrix File", command=self.load_single_file, font=("Arial", 13)).pack(fill=tk.X, pady=(6, 2))

        tk.Label(control_frame, text="Colormap", font=("Arial", 13)).pack()
        cmap_menu = ttk.Combobox(control_frame, textvariable=self.single_colormap, values=plt.colormaps(), font=("Arial", 12))
        cmap_menu.pack(fill=tk.X)

        tk.Label(control_frame, text="Min Value", font=("Arial", 13)).pack()
        self.min_slider = tk.Scale(control_frame, from_=0, to=1, resolution=0.01, orient=tk.HORIZONTAL, variable=self.single_min, font=("Arial", 13))
        self.min_slider.pack(fill=tk.X)

        tk.Label(control_frame, text="Max Value", font=("Arial", 13)).pack()
        self.max_slider = tk.Scale(control_frame, from_=0, to=1, resolution=0.01, orient=tk.HORIZONTAL, variable=self.single_max, font=("Arial", 13))
        self.max_slider.pack(fill=tk.X)

        tk.Checkbutton(control_frame, text="Show Color Bar", variable=self.show_colorbar, font=("Arial", 13)).pack(anchor='w')
        tk.Checkbutton(control_frame, text="Show Scale Bar", variable=self.show_scalebar, font=("Arial", 13)).pack(anchor='w')

        tk.Label(control_frame, text="Pixel size (µm)", font=("Arial", 13)).pack(pady=(10, 0))
        tk.Entry(control_frame, textvariable=self.pixel_size, font=("Arial", 13)).pack(fill=tk.X)

        tk.Label(control_frame, text="Scale bar length (µm)", font=("Arial", 13)).pack(pady=(10, 0))
        tk.Entry(control_frame, textvariable=self.scale_length, font=("Arial", 13)).pack(fill=tk.X)

        tk.Button(control_frame, text="View Map", command=self.view_single_map, font=("Arial", 13)).pack(fill=tk.X, pady=(10, 2))
        tk.Button(control_frame, text="Save PNG", command=self.save_single_image, font=("Arial", 13)).pack(fill=tk.X)

        self.single_figure, self.single_ax = plt.subplots()
        self.single_ax.axis('off')
        self.single_canvas = FigureCanvasTkAgg(self.single_figure, master=display_frame)
        self.single_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def build_rgb_tab(self):
        control_frame = tk.Frame(self.rgb_tab, padx=10, pady=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y)

        display_frame = tk.Frame(self.rgb_tab)
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.file_root_label = tk.Label(control_frame, text="Dataset: None", font=("Arial", 13, "italic"))
        self.file_root_label.pack(pady=(0, 10))

        for color in ['Red', 'Green', 'Blue']:
            ch = color[0]
            tk.Button(control_frame, text=f"Load {color} Channel", command=lambda c=ch: self.load_rgb_file(c), font=("Arial", 13)).pack(fill=tk.X, pady=(6, 2))
            elem_label = tk.Label(control_frame, text=f"Loaded Element: None", font=("Arial", 13, "italic"))
            elem_label.pack()
            gradient_canvas = tk.Canvas(control_frame, height=10)
            gradient_canvas.pack(fill=tk.X, padx=5, pady=2)
            self.draw_gradient(gradient_canvas, color.lower())
            max_slider = tk.Scale(control_frame, from_=0, to=1, resolution=0.01, orient=tk.HORIZONTAL, label=f"{color} Max", font=("Arial", 13))
            max_slider.set(1)
            max_slider.pack(fill=tk.X)
            max_slider.bind("<B1-Motion>", lambda e, c=ch: self.view_rgb_overlay())
            self.rgb_sliders[ch] = {'max': max_slider}
            self.rgb_labels[ch] = {'elem': elem_label}

        tk.Checkbutton(control_frame, text="Normalize to 99th Percentile", variable=self.normalize_var, font=("Arial", 13)).pack(anchor='w', pady=(10, 5))
        tk.Button(control_frame, text="View Overlay", command=self.view_rgb_overlay, font=("Arial", 13)).pack(fill=tk.X, pady=(10, 2))
        tk.Button(control_frame, text="Save RGB Image", command=self.save_rgb_image, font=("Arial", 13)).pack(fill=tk.X)

        self.rgb_figure, self.rgb_ax = plt.subplots()
        self.rgb_ax.axis('off')
        self.rgb_canvas = FigureCanvasTkAgg(self.rgb_figure, master=display_frame)
        self.rgb_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def draw_gradient(self, canvas, color):
        canvas.delete("all")
        for i in range(256):
            c = {'red': f'#{i:02x}0000', 'green': f'#00{i:02x}00', 'blue': f'#0000{i:02x}'}[color]
            canvas.create_line(i, 0, i, 10, fill=c)

    def load_single_file(self):
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")])
        if not path:
            return
        try:
            df = pd.read_excel(path, header=None) if path.endswith('.xlsx') else pd.read_csv(path, header=None)
            df = df.apply(pd.to_numeric, errors='coerce').dropna(how='all').dropna(axis=1, how='all')
            mat = df.to_numpy()
            self.single_matrix = mat
            self.single_min.set(np.nanmin(mat))
            self.single_max.set(np.nanmax(mat))
            self.min_slider.config(from_=self.single_min.get(), to=self.single_max.get())
            self.max_slider.config(from_=self.single_min.get(), to=self.single_max.get())
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load matrix file:\n{e}")

    def view_single_map(self):
        if self.single_matrix is None:
            return
        mat = np.array(self.single_matrix, dtype=float)
        mat[np.isnan(mat)] = 0
        vmin = self.single_min.get()
        vmax = self.single_max.get()
        self.single_ax.clear()
        im = self.single_ax.imshow(mat, cmap=self.single_colormap.get(), vmin=vmin, vmax=vmax)
        self.single_ax.axis('off')
        if self.show_colorbar.get():
            self.single_figure.colorbar(im, ax=self.single_ax, fraction=0.046, pad=0.04, label="Intensity")
        if self.show_scalebar.get():
            bar_length = self.scale_length.get() / self.pixel_size.get()
            x = 5
            y = mat.shape[0] - 15
            self.single_ax.plot([x, x + bar_length], [y, y], color='black', lw=3)
            self.single_ax.text(x, y - 10, f"{int(self.scale_length.get())} µm", color='black', fontsize=10, ha='left')
        self.single_figure.tight_layout()
        self.single_canvas.draw()

    def save_single_image(self):
        if self.single_matrix is None:
            return
        out_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if out_path:
            self.single_figure.savefig(out_path, dpi=300, bbox_inches='tight')

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
        rgb = np.stack(composite, axis=2)
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

if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("1100x700")
    app = MuadDataViewer(root)
    root.mainloop()
