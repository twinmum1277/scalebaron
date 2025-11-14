# -*- coding: utf-8 -*-
# Muad'Data v18 - Element Viewer + RGB Overlay + Zoom/Crop Feature
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, colorchooser
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import RectangleSelector
from matplotlib.gridspec import GridSpec
import os

# --- Math Expression Dialog (lifted from prior version) ---
class MathExpressionDialog:
    def __init__(self, parent, title="Enter Mathematical Expression"):
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # Build the dialog interface immediately
        self.build_dialog()
        
        # Make dialog modal
        self.dialog.focus_set()
        self.dialog.wait_window()
    
    def build_dialog(self):
        # Main frame
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(main_frame, text="Map Math - Mathematical Expression", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Instructions
        instructions = tk.Label(main_frame, text="Enter a mathematical expression using 'x' as the variable.\nExample: x * 0.001 (to convert CPS to ppm)", 
                              font=("Arial", 11), justify=tk.LEFT)
        instructions.pack(pady=(0, 15))
        
        # Expression entry
        tk.Label(main_frame, text="Expression:", font=("Arial", 12)).pack(anchor='w')
        self.expression_entry = tk.Entry(main_frame, font=("Arial", 12), width=50)
        self.expression_entry.pack(fill=tk.X, pady=(5, 15))
        self.expression_entry.insert(0, "x * 0.001")
        self.expression_entry.focus()
        
        # Common expressions frame
        common_frame = tk.Frame(main_frame)
        common_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(common_frame, text="Common expressions:", font=("Arial", 11, "bold")).pack(anchor='w')
        
        # Common expression buttons
        common_expressions = [
            ("Square root", "np.sqrt(x)"),
            ("Log base 10", "np.log10(x)"),
            ("Natural log", "np.log(x)"),
            ("Square", "x ** 2")
        ]
        
        for label, expr in common_expressions:
            btn = tk.Button(common_frame, text=label, command=lambda e=expr: self.expression_entry.delete(0, tk.END) or self.expression_entry.insert(0, e),
                           font=("Arial", 10))
            btn.pack(side=tk.LEFT, padx=(0, 5), pady=2)
        
        # Buttons frame
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Apply button
        apply_btn = tk.Button(button_frame, text="Apply Expression", command=self.apply_expression, 
                             font=("Arial", 12, "bold"), bg="#4CAF50", fg="black", padx=20)
        apply_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Cancel button
        cancel_btn = tk.Button(button_frame, text="Cancel", command=self.cancel, 
                              font=("Arial", 12), padx=20)
        cancel_btn.pack(side=tk.RIGHT)
        
        # Bind Enter key to apply
        self.expression_entry.bind("<Return>", lambda e: self.apply_expression())
        self.expression_entry.bind("<Escape>", lambda e: self.cancel())
        
        # Bind window close button
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
    
    def apply_expression(self):
        expression = self.expression_entry.get().strip()
        if not expression:
            messagebox.showerror("Error", "Please enter a mathematical expression.")
            return
        
        # Validate expression
        try:
            # Test with a sample value
            x = 1.0
            eval(expression, {"__builtins__": {}}, {"x": x, "np": np})
            self.result = expression
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Invalid Expression", f"The expression contains an error:\n{str(e)}\n\nPlease check your syntax.")
    
    def cancel(self):
        self.dialog.destroy()

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
        self.scalebar_color = '#ffffff'  # Default to white for good contrast
        self.single_file_label = None  # For displaying loaded file info
        self.single_file_name = None   # Store loaded file name
        self._single_colorbar = None   # Store the colorbar object for removal

        # Add a variable for the user-settable max slider value
        self.max_slider_limit = tk.DoubleVar()

        # Histogram state
        self.histogram_canvas = None

        # Math expression state
        self.original_matrix = None  # For storing the original matrix before math ops

        # Zoom/Crop state
        self.zoom_active = False  # Whether zoom selection mode is active
        self.rectangle_selector = None  # RectangleSelector widget
        self.cropped_matrix = None  # Store the cropped matrix
        self.crop_bounds = None  # Store crop bounds (x1, x2, y1, y2)
        self.is_zoomed = False  # Whether we're currently viewing a zoomed region

        # RGB Overlay state
        self.rgb_data = {'R': None, 'G': None, 'B': None}
        self.rgb_sliders = {}
        self.rgb_max_limits = {}
        self.rgb_labels = {}
        self.rgb_colors = {'R': '#ff0000', 'G': '#00ff00', 'B': '#0000ff'}  # Default colors
        self.rgb_color_buttons = {}
        self.rgb_gradient_canvases = {}
        self.file_root_label = None
        self.normalize_var = tk.IntVar()

        # Responsive colorbar for RGB overlay
        self.rgb_colorbar_figure = None
        self.rgb_colorbar_ax = None
        self.rgb_colorbar_canvas = None

        # Correlation/Ratio Analysis state
        self.correlation_elem1 = tk.StringVar(value='R')
        self.correlation_elem2 = tk.StringVar(value='G')
        self.ratio_matrix = None
        self.correlation_coefficient = None
        self.ratio_figure = None
        self.ratio_ax = None
        self.ratio_canvas = None

        # Tabs
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill=tk.BOTH, expand=True)

        self.single_tab = tk.Frame(self.tabs)
        self.rgb_tab = tk.Frame(self.tabs)
        self.zstack_tab = tk.Frame(self.tabs)

        self.tabs.add(self.single_tab, text="Element Viewer")
        self.tabs.add(self.rgb_tab, text="RGB Overlay")
        self.tabs.add(self.zstack_tab, text="Z-Stack / Sum")

        # Z-Stack state
        self.zstack_slices = []  # list of numpy arrays
        self.zstack_offsets = []  # list of (dy, dx) per slice
        self.zstack_file_labels = []  # list of file base names
        self.zstack_show_overlay = tk.BooleanVar(value=True)
        self.zstack_auto_pad = tk.BooleanVar(value=True)
        self.zstack_colormap = tk.StringVar(value='viridis')
        self.zstack_min = tk.DoubleVar(value=0.0)
        self.zstack_max = tk.DoubleVar(value=1.0)
        self.zmax_slider_limit = tk.DoubleVar(value=1.0)
        self.zstack_nudge_step = tk.IntVar(value=1)
        self.zstack_sum_matrix = None
        self.zstack_figure = None
        self._zstack_colorbar = None  # Store the colorbar object for removal
        self.zstack_ax = None
        self.zstack_canvas = None

        self.build_single_tab()
        self.build_rgb_tab()
        self.build_zstack_tab()

    def pad_slices_to_same_size(self, slices):
        """Pad smaller matrices with zeros so all have the same shape as the largest (rows, cols)."""
        if not slices:
            return []
        max_rows = max(s.shape[0] for s in slices)
        max_cols = max(s.shape[1] for s in slices)
        padded = []
        for s in slices:
            r, c = s.shape
            if r == max_rows and c == max_cols:
                padded.append(s)
                continue
            pad_rows = max_rows - r
            pad_cols = max_cols - c
            # Pad on the right and bottom with zeros
            padded_s = np.pad(s, ((0, pad_rows), (0, pad_cols)), mode='constant', constant_values=0)
            padded.append(padded_s)
        return padded

    def apply_offsets_to_slices(self, slices, offsets):
        """Shift each slice by (dy, dx) using zero padding; keep same shape as input."""
        if not slices:
            return []
        H, W = slices[0].shape
        shifted = []
        for s, (dy, dx) in zip(slices, offsets):
            out = np.zeros_like(s)
            # Compute source and destination bounds
            src_y0 = max(0, -dy)
            src_y1 = min(H, H - dy)
            dst_y0 = max(0, dy)
            dst_y1 = dst_y0 + (src_y1 - src_y0)

            src_x0 = max(0, -dx)
            src_x1 = min(W, W - dx)
            dst_x0 = max(0, dx)
            dst_x1 = dst_x0 + (src_x1 - src_x0)

            if src_y1 > src_y0 and src_x1 > src_x0 and dst_y1 > dst_y0 and dst_x1 > dst_x0:
                out[dst_y0:dst_y1, dst_x0:dst_x1] = s[src_y0:src_y1, src_x0:src_x1]
            shifted.append(out)
        return shifted

    def build_zstack_tab(self):
        control_frame = tk.Frame(self.zstack_tab, padx=10, pady=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y)

        display_frame = tk.Frame(self.zstack_tab)
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Button(control_frame, text="Add Slice", command=self.zstack_add_slice, font=("Arial", 13)).pack(fill=tk.X, pady=(6, 2))
        tk.Button(control_frame, text="Clear Slices", command=self.zstack_clear_slices, font=("Arial", 13)).pack(fill=tk.X, pady=(0, 6))

        self.zstack_listbox = tk.Listbox(control_frame, height=6)
        self.zstack_listbox.pack(fill=tk.BOTH, expand=False, pady=(0, 10))
        self.zstack_listbox.bind('<<ListboxSelect>>', lambda e: self.update_zstack_offset_label())

        # Offset controls
        self.zstack_offset_label = tk.Label(control_frame, text="Offset (dy, dx): --, --", font=("Arial", 11, "italic"))
        self.zstack_offset_label.pack(pady=(0, 6))

        nudge_frame = tk.Frame(control_frame)
        nudge_frame.pack(pady=(0, 8))
        up_btn = tk.Button(nudge_frame, text="↑", width=4, command=lambda: self.zstack_nudge_selected( -1,  0))
        lf_btn = tk.Button(nudge_frame, text="←", width=4, command=lambda: self.zstack_nudge_selected(  0, -1))
        dn_btn = tk.Button(nudge_frame, text="↓", width=4, command=lambda: self.zstack_nudge_selected(  1,  0))
        rt_btn = tk.Button(nudge_frame, text="→", width=4, command=lambda: self.zstack_nudge_selected(  0,  1))
        up_btn.grid(row=0, column=1)
        lf_btn.grid(row=1, column=0)
        dn_btn.grid(row=1, column=1)
        rt_btn.grid(row=1, column=2)

        # Nudge step selector
        step_frame = tk.Frame(control_frame)
        step_frame.pack(pady=(0, 8), anchor='w')
        tk.Label(step_frame, text="Nudge step (px):", font=("Arial", 11)).pack(side=tk.LEFT)
        self.zstack_step_spin = tk.Spinbox(step_frame, from_=1, to=100, increment=1, width=5, textvariable=self.zstack_nudge_step)
        self.zstack_step_spin.pack(side=tk.LEFT, padx=(6, 0))
        # Quick buttons for common steps
        tk.Button(step_frame, text="1", width=3, command=lambda: self.zstack_nudge_step.set(1)).pack(side=tk.LEFT, padx=(6, 0))
        tk.Button(step_frame, text="5", width=3, command=lambda: self.zstack_nudge_step.set(5)).pack(side=tk.LEFT)
        tk.Button(step_frame, text="10", width=3, command=lambda: self.zstack_nudge_step.set(10)).pack(side=tk.LEFT)

        reset_frame = tk.Frame(control_frame)
        reset_frame.pack(pady=(0, 10))
        tk.Button(reset_frame, text="Reset Selected", command=self.zstack_reset_selected_offset).pack(side=tk.LEFT, padx=(0, 6))
        tk.Button(reset_frame, text="Reset All", command=self.zstack_reset_all_offsets).pack(side=tk.LEFT)

        tk.Label(control_frame, text="Colormap", font=("Arial", 13)).pack()
        zcmap_menu = ttk.Combobox(control_frame, textvariable=self.zstack_colormap, values=plt.colormaps(), font=("Arial", 13))
        zcmap_menu.pack(fill=tk.X)

        tk.Label(control_frame, text="Min Value", font=("Arial", 13)).pack(pady=(6, 0))
        self.zmin_slider = tk.Scale(control_frame, from_=0, to=1, resolution=0.01, orient=tk.HORIZONTAL, variable=self.zstack_min, font=("Arial", 13))
        self.zmin_slider.pack(fill=tk.X)
        self.zmin_slider.bind("<B1-Motion>", lambda e: self.zstack_render_preview())

        tk.Label(control_frame, text="Max Value", font=("Arial", 13)).pack()
        self.zmax_slider = tk.Scale(control_frame, from_=0, to=1, resolution=0.01, orient=tk.HORIZONTAL, variable=self.zstack_max, font=("Arial", 13))
        self.zmax_slider.pack(fill=tk.X)
        self.zmax_slider.bind("<B1-Motion>", lambda e: self.zstack_render_preview())

        # Entry for setting z-stack max slider cap
        zcap_frame = tk.Frame(control_frame)
        zcap_frame.pack(fill=tk.X, pady=(2, 0))
        tk.Label(zcap_frame, text="Slider Max:", font=("Arial", 11)).pack(side=tk.LEFT)
        zcap_entry = tk.Entry(zcap_frame, textvariable=self.zmax_slider_limit, width=8, font=("Arial", 11))
        zcap_entry.pack(side=tk.LEFT)
        zcap_entry.bind("<Return>", lambda e: self.set_zmax_slider_limit())
        zcap_entry.bind("<FocusOut>", lambda e: self.set_zmax_slider_limit())

        tk.Checkbutton(control_frame, text="Auto-pad smaller to largest", variable=self.zstack_auto_pad, font=("Arial", 13)).pack(anchor='w', pady=(6, 0))
        tk.Checkbutton(control_frame, text="Show overlay preview", variable=self.zstack_show_overlay, font=("Arial", 13)).pack(anchor='w')

        tk.Button(control_frame, text="Preview Alignment", command=self.zstack_render_preview, font=("Arial", 13)).pack(fill=tk.X, pady=(10, 2))
        tk.Button(control_frame, text="Sum Slices", command=self.zstack_sum_slices, font=("Arial", 13), bg="#4CAF50", fg="black").pack(fill=tk.X)
        tk.Button(control_frame, text="Save Summed Matrix", command=self.zstack_save_sum, font=("Arial", 13)).pack(fill=tk.X, pady=(6, 0))

        self.zstack_figure, self.zstack_ax = plt.subplots()
        self.zstack_ax.axis('off')
        self.zstack_canvas = FigureCanvasTkAgg(self.zstack_figure, master=display_frame)
        self.zstack_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def zstack_add_slice(self):
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")])
        if not path:
            return
        try:
            df = pd.read_excel(path, header=None) if path.endswith('.xlsx') else pd.read_csv(path, header=None)
            df = df.apply(pd.to_numeric, errors='coerce').dropna(how='all').dropna(axis=1, how='all')
            mat = df.to_numpy()
            self.zstack_slices.append(mat)
            self.zstack_offsets.append((0, 0))
            self.zstack_file_labels.append(os.path.basename(path))
            self.zstack_listbox.insert(tk.END, f"{os.path.basename(path)}  {mat.shape}")
            # Update sliders to data range
            min_val = float(np.nanmin(mat)) if np.isfinite(np.nanmin(mat)) else 0.0
            max_val = float(np.nanmax(mat)) if np.isfinite(np.nanmax(mat)) else 1.0
            self.zstack_min.set(min_val)
            self.zstack_max.set(max_val)
            self.zmin_slider.config(from_=min_val, to=max_val)
            self.zmax_slider.config(from_=min_val, to=max_val)
            self.zmin_slider.set(min_val)
            self.zmax_slider.set(max_val)
            self.zmax_slider_limit.set(round(max_val))
            self.zstack_render_preview()
            self.update_zstack_offset_label()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load slice:\n{e}")

    def set_zmax_slider_limit(self):
        try:
            val = float(self.zmax_slider_limit.get())
            min_val = self.zmax_slider.cget('from')
            if val > min_val:
                self.zmax_slider.config(to=val)
                # Adjust min slider upper bound as well to maintain consistency
                self.zmin_slider.config(to=val)
                if self.zstack_max.get() > val:
                    self.zstack_max.set(val)
                self.zmax_slider_limit.set(val)
                self.zstack_render_preview()
            else:
                self.zmax_slider_limit.set(self.zmax_slider.cget('to'))
        except Exception:
            self.zmax_slider_limit.set(self.zmax_slider.cget('to'))

    def zstack_clear_slices(self):
        self.zstack_slices = []
        self.zstack_offsets = []
        self.zstack_file_labels = []
        self.zstack_listbox.delete(0, tk.END)
        self.zstack_ax.clear()
        self.zstack_ax.axis('off')
        # Remove colorbar if it exists
        if self._zstack_colorbar is not None:
            try:
                self._zstack_colorbar.remove()
            except Exception:
                pass
            self._zstack_colorbar = None
        self.zstack_canvas.draw()

    def update_zstack_offset_label(self):
        try:
            idxs = self.zstack_listbox.curselection()
            if not idxs:
                self.zstack_offset_label.config(text="Offset (dy, dx): --, --")
                return
            i = idxs[0]
            dy, dx = self.zstack_offsets[i]
            self.zstack_offset_label.config(text=f"Offset (dy, dx): {dy}, {dx}")
        except Exception:
            self.zstack_offset_label.config(text="Offset (dy, dx): --, --")

    def zstack_nudge_selected(self, dy, dx):
        idxs = self.zstack_listbox.curselection()
        if not idxs:
            return
        i = idxs[0]
        step = max(1, int(self.zstack_nudge_step.get()))
        cur_dy, cur_dx = self.zstack_offsets[i]
        self.zstack_offsets[i] = (cur_dy + dy * step, cur_dx + dx * step)
        self.update_zstack_offset_label()
        self.zstack_render_preview()

    def zstack_reset_selected_offset(self):
        idxs = self.zstack_listbox.curselection()
        if not idxs:
            return
        i = idxs[0]
        self.zstack_offsets[i] = (0, 0)
        self.update_zstack_offset_label()
        self.zstack_render_preview()

    def zstack_reset_all_offsets(self):
        self.zstack_offsets = [(0, 0) for _ in self.zstack_offsets]
        self.update_zstack_offset_label()
        self.zstack_render_preview()

    def zstack_render_preview(self):
        if not self.zstack_slices:
            return
        slices = [np.array(s, dtype=float) for s in self.zstack_slices]
        for s in slices:
            s[np.isnan(s)] = 0
        if self.zstack_auto_pad.get():
            slices = self.pad_slices_to_same_size(slices)
        # Apply offsets (ensure list matches length)
        if len(self.zstack_offsets) == len(slices):
            slices = self.apply_offsets_to_slices(slices, self.zstack_offsets)
        self.zstack_ax.clear()
        self.zstack_ax.axis('off')
        # Remove colorbar if it exists (preview doesn't show colorbar)
        if self._zstack_colorbar is not None:
            try:
                self._zstack_colorbar.remove()
            except Exception:
                pass
            self._zstack_colorbar = None
        vmin = self.zstack_min.get()
        vmax = self.zstack_max.get()
        if self.zstack_show_overlay.get():
            # Overlay with decreasing alpha so all are visible
            num = len(slices)
            base_alpha = 0.6 if num <= 2 else max(0.25, 0.8/num)
            for idx, s in enumerate(slices):
                alpha = base_alpha
                im = self.zstack_ax.imshow(s, cmap=self.zstack_colormap.get(), vmin=vmin, vmax=vmax, alpha=alpha)
        else:
            # Show first slice only
            im = self.zstack_ax.imshow(slices[0], cmap=self.zstack_colormap.get(), vmin=vmin, vmax=vmax)
        self.zstack_figure.tight_layout()
        self.zstack_canvas.draw()

    def zstack_sum_slices(self):
        if not self.zstack_slices:
            messagebox.showwarning("No Slices", "Please add at least one slice.")
            return
        slices = [np.array(s, dtype=float) for s in self.zstack_slices]
        for s in slices:
            s[np.isnan(s)] = 0
        if self.zstack_auto_pad.get():
            slices = self.pad_slices_to_same_size(slices)
        if len(self.zstack_offsets) == len(slices):
            slices = self.apply_offsets_to_slices(slices, self.zstack_offsets)
        # Sum pixel-wise
        total = np.zeros_like(slices[0], dtype=float)
        for s in slices:
            total += s
        self.zstack_sum_matrix = total
        # Render summed
        self.zstack_ax.clear()
        self.zstack_ax.axis('off')
        # Remove existing colorbar if it exists
        if self._zstack_colorbar is not None:
            try:
                self._zstack_colorbar.remove()
            except Exception:
                pass
            self._zstack_colorbar = None
        im = self.zstack_ax.imshow(total, cmap=self.zstack_colormap.get(), vmin=self.zstack_min.get(), vmax=self.zstack_max.get())
        self._zstack_colorbar = self.zstack_figure.colorbar(im, ax=self.zstack_ax, fraction=0.046, pad=0.04, shrink=0.4, label="Sum")
        self._zstack_colorbar.set_label("Sum", fontfamily='Arial', fontsize=14)
        self._zstack_colorbar.ax.tick_params(labelsize=12)
        self.zstack_figure.tight_layout()
        self.zstack_canvas.draw()
        messagebox.showinfo("Done", f"Summed {len(slices)} slice(s).")

    def zstack_save_sum(self):
        if self.zstack_sum_matrix is None:
            messagebox.showwarning("Nothing to Save", "Please sum slices first.")
            return
        out_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv"), ("Excel", "*.xlsx")])
        if not out_path:
            return
        try:
            if out_path.endswith('.xlsx'):
                # Save to Excel via pandas
                df = pd.DataFrame(self.zstack_sum_matrix)
                df.to_excel(out_path, header=False, index=False)
            else:
                # Default to CSV
                np.savetxt(out_path, self.zstack_sum_matrix, delimiter=",", fmt='%g')
            messagebox.showinfo("Saved", f"Saved summed matrix to: {out_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save summed matrix:\n{e}")

    def build_single_tab(self):
        control_frame = tk.Frame(self.single_tab, padx=10, pady=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y)

        display_frame = tk.Frame(self.single_tab)
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Button(control_frame, text="Load Matrix File", command=self.load_single_file, font=("Arial", 13)).pack(fill=tk.X, pady=(6, 2))

        tk.Label(control_frame, text="Colormap", font=("Arial", 13)).pack()
        cmap_menu = ttk.Combobox(control_frame, textvariable=self.single_colormap, values=plt.colormaps(), font=("Arial", 13))
        cmap_menu.pack(fill=tk.X)

        tk.Label(control_frame, text="Min Value", font=("Arial", 13)).pack()
        self.min_slider = tk.Scale(control_frame, from_=0, to=1, resolution=0.01, orient=tk.HORIZONTAL, variable=self.single_min, font=("Arial", 13))
        self.min_slider.pack(fill=tk.X)
        # Update plot when min slider is changed
        self.min_slider.bind("<ButtonRelease-1>", lambda e: self.view_single_map(update_layout=False))
        self.min_slider.bind("<B1-Motion>", lambda e: self.view_single_map(update_layout=False))

        # --- Max Value controls ---
        tk.Label(control_frame, text="Max Value", font=("Arial", 13)).pack()

        # Frame for max slider
        max_slider_frame = tk.Frame(control_frame)
        max_slider_frame.pack(fill=tk.X)

        self.max_slider = tk.Scale(max_slider_frame, from_=0, to=1, resolution=0.01, orient=tk.HORIZONTAL, variable=self.single_max, font=("Arial", 13))
        self.max_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        # Update plot when max slider is changed
        self.max_slider.bind("<ButtonRelease-1>", lambda e: self.view_single_map(update_layout=False))
        self.max_slider.bind("<B1-Motion>", lambda e: self.view_single_map(update_layout=False))

        # Entry for setting the max value of the slider (now below the slider)
        slider_max_frame = tk.Frame(control_frame)
        slider_max_frame.pack(fill=tk.X, pady=(2, 0))
        tk.Label(slider_max_frame, text="Slider Max:", font=("Arial", 13)).pack(side=tk.LEFT)
        self.max_slider_limit_entry = tk.Entry(slider_max_frame, textvariable=self.max_slider_limit, width=8, font=("Arial", 13))
        self.max_slider_limit_entry.pack(side=tk.LEFT)
        self.max_slider_limit_entry.bind("<Return>", lambda e: self.set_max_slider_limit())
        self.max_slider_limit_entry.bind("<FocusOut>", lambda e: self.set_max_slider_limit())

        tk.Checkbutton(control_frame, text="Show Color Bar", variable=self.show_colorbar, font=("Arial", 13)).pack(anchor='w')
        tk.Checkbutton(control_frame, text="Show Scale Bar", variable=self.show_scalebar, font=("Arial", 13)).pack(anchor='w')
        
        # Scale bar color picker
        scalebar_color_frame = tk.Frame(control_frame)
        scalebar_color_frame.pack(fill=tk.X, pady=(5, 0))
        tk.Label(scalebar_color_frame, text="Scale Bar Color:", font=("Arial", 13)).pack(side=tk.LEFT)
        self.scalebar_color_btn = tk.Button(scalebar_color_frame, text="Pick Color", bg=self.scalebar_color, fg='black', 
                                          font=("Arial", 10, "bold"), command=self.pick_scalebar_color)
        self.scalebar_color_btn.pack(side=tk.LEFT, padx=(5, 0))

        tk.Label(control_frame, text="Pixel size (µm)", font=("Arial", 13)).pack(pady=(10, 0))
        self.pixel_size_entry = tk.Entry(control_frame, textvariable=self.pixel_size, font=("Arial", 13))
        self.pixel_size_entry.pack(fill=tk.X)
        self.pixel_size_entry.bind("<Return>", lambda e: self.view_single_map())
        self.pixel_size_entry.bind("<FocusOut>", lambda e: self.view_single_map())

        tk.Label(control_frame, text="Scale bar length (µm)", font=("Arial", 13)).pack(pady=(10, 0))
        self.scale_length_entry = tk.Entry(control_frame, textvariable=self.scale_length, font=("Arial", 13))
        self.scale_length_entry.pack(fill=tk.X)
        self.scale_length_entry.bind("<Return>", lambda e: self.view_single_map())
        self.scale_length_entry.bind("<FocusOut>", lambda e: self.view_single_map())

        tk.Button(control_frame, text="View Map", command=self.view_single_map, font=("Arial", 13)).pack(fill=tk.X, pady=(10, 2))
        tk.Button(control_frame, text="Save PNG", command=self.save_single_image, font=("Arial", 13)).pack(fill=tk.X)

        # --- Math Expression Button ---
        tk.Button(control_frame, text="Map Math", command=self.open_map_math, font=("Arial", 13, "bold"), bg="#4CAF50", fg="black").pack(fill=tk.X, pady=(10, 2))

        # --- Zoom/Crop Buttons ---
        tk.Label(control_frame, text="Zoom & Crop", font=("Arial", 13, "bold")).pack(pady=(10, 5))
        self.zoom_button = tk.Button(control_frame, text="Select Region to Zoom", command=self.toggle_zoom_mode, font=("Arial", 13), bg="#2196F3", fg="black")
        self.zoom_button.pack(fill=tk.X, pady=(0, 2))
        
        self.save_crop_button = tk.Button(control_frame, text="Save Cropped Matrix", command=self.save_cropped_matrix, font=("Arial", 13), state=tk.DISABLED, fg="black", disabledforeground="gray")
        self.save_crop_button.pack(fill=tk.X, pady=(0, 2))
        
        self.reset_zoom_button = tk.Button(control_frame, text="Reset to Full View", command=self.reset_zoom, font=("Arial", 13), state=tk.DISABLED, fg="black", disabledforeground="gray")
        self.reset_zoom_button.pack(fill=tk.X, pady=(0, 2))

        # Add a label at the bottom left to display loaded file info
        self.single_file_label = tk.Label(control_frame, text="Loaded file: None", font=("Arial", 13, "italic"), anchor="w", justify="left", wraplength=200)
        self.single_file_label.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        self.single_figure, self.single_ax = plt.subplots()
        self.single_ax.axis('off')
        self.single_canvas = FigureCanvasTkAgg(self.single_figure, master=display_frame)
        self.single_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def set_max_slider_limit(self):
        """Set the maximum value of the max slider from the entry box."""
        try:
            val = float(self.max_slider_limit.get())
            min_val = self.max_slider.cget('from')
            if val > min_val:
                self.max_slider.config(to=val)
                # Keep min slider's upper bound consistent with max slider's upper bound
                self.min_slider.config(to=val)
                # If the current slider value is above the new max, set it to the new max
                if self.single_max.get() > val:
                    self.single_max.set(val)
                # Update the entry to show the value actually applied
                self.max_slider_limit.set(val)
                # Update the map (layout will be updated only if colorbar changes)
                self.view_single_map()
            else:
                # If entered value is not valid, reset to current slider max
                self.max_slider_limit.set(self.max_slider.cget('to'))
        except Exception:
            # If invalid input, reset to current slider max
            self.max_slider_limit.set(self.max_slider.cget('to'))

    # Removed histogram functions and UI per request

    # --- Math Expression Functionality ---
    def open_map_math(self):
        """Open the map math dialog and apply mathematical expressions to the loaded matrix."""
        if self.single_matrix is None:
            messagebox.showwarning("No Data", "Please load a matrix file first.")
            return
        
        # Create and show the math expression dialog
        dialog = MathExpressionDialog(self.root)
        
        if dialog.result:
            try:
                # Store original matrix if not already stored
                if self.original_matrix is None:
                    self.original_matrix = np.array(self.single_matrix, copy=True)
                
                # Create a copy of the current matrix for processing
                mat = np.array(self.single_matrix, dtype=float)
                
                # Create a mask for non-empty cells (where there are actual values)
                # We'll consider cells with values > 0 as non-empty
                non_empty_mask = (mat > 0) & ~np.isnan(mat)
                
                # Apply the expression only to non-empty cells
                result_mat = np.array(mat, copy=True)
                
                # For each non-empty cell, apply the expression
                for i in range(mat.shape[0]):
                    for j in range(mat.shape[1]):
                        if non_empty_mask[i, j]:
                            x = mat[i, j]
                            try:
                                # Safely evaluate the expression for this cell
                                result = eval(dialog.result, {"__builtins__": {}}, {"x": x, "np": np})
                                result_mat[i, j] = result
                            except Exception as e:
                                messagebox.showerror("Evaluation Error", f"Error evaluating expression for cell [{i},{j}]:\n{str(e)}")
                                return
                
                # Update the current matrix with the result
                self.single_matrix = result_mat
                
                # Update min/max values and sliders
                min_val = np.nanmin(result_mat)
                max_val = np.nanmax(result_mat)
                self.single_min.set(min_val)
                self.single_max.set(max_val)
                self.min_slider.config(from_=min_val, to=max_val)
                self.max_slider.config(from_=min_val, to=max_val)
                self.min_slider.set(min_val)
                self.max_slider.set(max_val)
                
                # Set the max_slider_limit variable and entry to the new max (rounded to integer)
                self.max_slider_limit.set(round(max_val))
                # Update view
                self.view_single_map()
                
                # Update file label to show modification status
                self.update_file_label()
                
                # Ask user if they want to save the result
                save_result = messagebox.askyesno("Save Result", 
                                                "Expression applied successfully!\n\nWould you like to save the result to a file?")
                
                if save_result:
                    self.save_math_result(result_mat, dialog.result)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to apply expression:\n{str(e)}")

    def save_math_result(self, result_matrix, expression):
        """Save the math result to a file with automatic naming."""
        if self.single_file_name is None:
            # Fallback if no original filename
            default_name = "math_result.xlsx"
        else:
            # Create filename with _math suffix
            name_without_ext = os.path.splitext(self.single_file_name)[0]
            default_name = f"{name_without_ext}_math.xlsx"
        
        # Ask user for save location with pre-filled name
        save_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[
                ("Excel files", "*.xlsx"),
                ("CSV files", "*.csv")
            ],
            initialfile=default_name
        )
        
        if save_path:
            try:
                if save_path.endswith('.xlsx'):
                    # Save as Excel
                    df = pd.DataFrame(result_matrix)
                    df.to_excel(save_path, header=False, index=False)
                elif save_path.endswith('.csv'):
                    # Save as CSV
                    df = pd.DataFrame(result_matrix)
                    df.to_csv(save_path, header=False, index=False)
                
                messagebox.showinfo("Saved", 
                                  f"Math result saved successfully!\n\n"
                                  f"File: {os.path.basename(save_path)}\n"
                                  f"Expression: {expression}\n"
                                  f"Matrix shape: {result_matrix.shape}")
                
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save the result:\n{str(e)}")

    def update_file_label(self):
        """Update the file label to show loaded file and math status."""
        if self.single_file_name is not None:
            status = ""
            if self.is_zoomed:
                status = " (zoomed)"
            elif self.original_matrix is not None:
                status = " (modified)"
            self.single_file_label.config(text=f"Loaded file: {self.single_file_name}{status}")
        else:
            self.single_file_label.config(text="Loaded file: None")

    # --- End Math Expression Functionality ---

    # --- Zoom/Crop Functionality ---
    def toggle_zoom_mode(self):
        """Toggle zoom selection mode on/off."""
        if self.single_matrix is None:
            messagebox.showwarning("No Data", "Please load a matrix file first.")
            return
        
        if not self.zoom_active:
            # Activate zoom mode
            self.zoom_active = True
            self.zoom_button.config(text="Cancel Selection", bg="#FF5722", fg="black")
            
            # Create rectangle selector with white edge color for visibility
            self.rectangle_selector = RectangleSelector(
                self.single_ax,
                self.on_select,
                useblit=True,
                button=[1],  # Left mouse button
                minspanx=5,
                minspany=5,
                spancoords='pixels',
                interactive=False,
                props=dict(facecolor='none', edgecolor='white', linewidth=1, linestyle='--')
            )
        else:
            # Deactivate zoom mode
            self.deactivate_zoom_mode()
    
    def deactivate_zoom_mode(self):
        """Deactivate zoom selection mode."""
        self.zoom_active = False
        self.zoom_button.config(text="Select Region to Zoom", bg="#2196F3", fg="black")
        
        if self.rectangle_selector is not None:
            self.rectangle_selector.set_active(False)
            self.rectangle_selector = None
        
        # Redraw to remove selection rectangle
        self.view_single_map()
    
    def on_select(self, eclick, erelease):
        """Callback when a rectangle selection is made."""
        if not self.zoom_active:
            return
        
        # Get the coordinates of the selection (in data coordinates)
        x1, y1 = int(eclick.xdata), int(eclick.ydata)
        x2, y2 = int(erelease.xdata), int(erelease.ydata)
        
        # Ensure coordinates are in the right order
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)
        
        # Validate bounds
        if x1 < 0 or y1 < 0 or x2 > self.single_matrix.shape[1] or y2 > self.single_matrix.shape[0]:
            messagebox.showerror("Invalid Selection", "Selection is out of bounds. Please try again.")
            return
        
        if x2 - x1 < 5 or y2 - y1 < 5:
            messagebox.showwarning("Selection Too Small", "Please select a larger region.")
            return
        
        # Store the crop bounds
        self.crop_bounds = (x1, x2, y1, y2)
        
        # Deactivate zoom mode
        self.deactivate_zoom_mode()
        
        # Automatically zoom to the selected region
        self.crop_to_selection()
    
    def crop_to_selection(self):
        """Crop the matrix to the selected region and update display."""
        if self.crop_bounds is None or self.single_matrix is None:
            return
        
        x1, x2, y1, y2 = self.crop_bounds
        
        # Crop the matrix (note: matrix is [rows, cols] = [y, x])
        self.cropped_matrix = self.single_matrix[y1:y2, x1:x2].copy()
        
        # Temporarily store the full matrix if not already stored
        if not self.is_zoomed:
            self.full_matrix_backup = self.single_matrix.copy()
        
        # Replace the current matrix with the cropped version
        self.single_matrix = self.cropped_matrix
        
        # Update state
        self.is_zoomed = True
        
        # Update min/max sliders for the new data range
        min_val = np.nanmin(self.cropped_matrix)
        max_val = np.nanmax(self.cropped_matrix)
        self.single_min.set(min_val)
        self.single_max.set(max_val)
        self.min_slider.config(from_=min_val, to=max_val)
        self.max_slider.config(from_=min_val, to=max_val)
        self.min_slider.set(min_val)
        self.max_slider.set(max_val)
        self.max_slider_limit.set(round(max_val))
        
        # Enable save and reset buttons
        self.save_crop_button.config(state=tk.NORMAL)
        self.reset_zoom_button.config(state=tk.NORMAL)
        
        # Update display
        self.view_single_map()
        self.update_file_label()
    
    def save_cropped_matrix(self):
        """Save the cropped matrix to a file."""
        if self.cropped_matrix is None:
            messagebox.showwarning("No Cropped Data", "Please select and zoom to a region first.")
            return
        
        # Generate default filename
        if self.single_file_name is not None:
            name_without_ext = os.path.splitext(self.single_file_name)[0]
            x1, x2, y1, y2 = self.crop_bounds
            default_name = f"{name_without_ext}_cropped_{x1}-{x2}_{y1}-{y2}.xlsx"
        else:
            default_name = "cropped_matrix.xlsx"
        
        # Ask user for save location
        save_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[
                ("Excel files", "*.xlsx"),
                ("CSV files", "*.csv")
            ],
            initialfile=default_name
        )
        
        if save_path:
            try:
                if save_path.endswith('.xlsx'):
                    df = pd.DataFrame(self.cropped_matrix)
                    df.to_excel(save_path, header=False, index=False)
                elif save_path.endswith('.csv'):
                    df = pd.DataFrame(self.cropped_matrix)
                    df.to_csv(save_path, header=False, index=False)
                
                x1, x2, y1, y2 = self.crop_bounds
                messagebox.showinfo("Saved", 
                                  f"Cropped matrix saved successfully!\n\n"
                                  f"File: {os.path.basename(save_path)}\n"
                                  f"Region: ({x1}, {y1}) to ({x2}, {y2})\n"
                                  f"Matrix shape: {self.cropped_matrix.shape}\n\n"
                                  f"You can now import this into ScaleBaron!")
                
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save cropped matrix:\n{str(e)}")
    
    def reset_zoom(self):
        """Reset to the full matrix view."""
        if not self.is_zoomed:
            return
        
        # Restore the full matrix
        if hasattr(self, 'full_matrix_backup'):
            self.single_matrix = self.full_matrix_backup
            delattr(self, 'full_matrix_backup')
        
        # Reset state
        self.is_zoomed = False
        self.cropped_matrix = None
        self.crop_bounds = None
        
        # Update min/max sliders for the full data range
        min_val = np.nanmin(self.single_matrix)
        max_val = np.nanmax(self.single_matrix)
        self.single_min.set(min_val)
        self.single_max.set(max_val)
        self.min_slider.config(from_=min_val, to=max_val)
        self.max_slider.config(from_=min_val, to=max_val)
        self.min_slider.set(min_val)
        self.max_slider.set(max_val)
        self.max_slider_limit.set(round(max_val))
        
        # Disable save and reset buttons
        self.save_crop_button.config(state=tk.DISABLED)
        self.reset_zoom_button.config(state=tk.DISABLED)
        
        # Update display
        self.view_single_map()
        self.update_file_label()
    
    # --- End Zoom/Crop Functionality ---

    # --- The rest of the code (RGB tab, etc) remains unchanged ---

    def build_rgb_tab(self):
        control_frame = tk.Frame(self.rgb_tab, padx=10, pady=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y)

        display_frame = tk.Frame(self.rgb_tab, bg="black")
        display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.file_root_label = tk.Label(control_frame, text="Dataset: None", font=("Arial", 13, "italic"))
        self.file_root_label.pack(pady=(0, 10))

        color_names = {'R': 'Red', 'G': 'Green', 'B': 'Blue'}
        default_colors = {'R': '#ff0000', 'G': '#00ff00', 'B': '#0000ff'}

        for ch in ['R', 'G', 'B']:
            color = color_names[ch]
            tk.Button(control_frame, text=f"Load {color} Channel", command=lambda c=ch: self.load_rgb_file(c), font=("Arial", 13)).pack(fill=tk.X, pady=(6, 2))
            elem_label = tk.Label(control_frame, text=f"Loaded Element: None", font=("Arial", 13, "italic"))
            elem_label.pack()
            # Color picker and gradient
            color_picker_frame = tk.Frame(control_frame)
            color_picker_frame.pack(fill=tk.X, padx=5, pady=2)
            color_btn = tk.Button(color_picker_frame, text="Pick Color", bg=self.rgb_colors[ch], fg='black', font=("Arial", 13, "bold"),
                                  command=lambda c=ch: self.pick_channel_color(c))
            color_btn.pack(side=tk.LEFT, padx=(0, 5))
            gradient_canvas = tk.Canvas(color_picker_frame, height=10, width=256)
            gradient_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.draw_gradient(gradient_canvas, self.rgb_colors[ch])
            self.rgb_color_buttons[ch] = color_btn
            self.rgb_gradient_canvases[ch] = gradient_canvas

            max_slider = tk.Scale(control_frame, from_=0, to=1, resolution=0.01, orient=tk.HORIZONTAL, label=f"{color} Max", font=("Arial", 13))
            max_slider.set(1)
            max_slider.pack(fill=tk.X)
            max_slider.bind("<B1-Motion>", lambda e, c=ch: self.view_rgb_overlay())
            self.rgb_sliders[ch] = {'max': max_slider}
            self.rgb_labels[ch] = {'elem': elem_label}

            # Entry to cap the max slider value
            cap_frame = tk.Frame(control_frame)
            cap_frame.pack(fill=tk.X, pady=(0, 4))
            tk.Label(cap_frame, text=f"{color} Slider Max:", font=("Arial", 11)).pack(side=tk.LEFT)
            self.rgb_max_limits[ch] = tk.DoubleVar(value=1.0)
            cap_entry = tk.Entry(cap_frame, textvariable=self.rgb_max_limits[ch], width=8, font=("Arial", 11))
            cap_entry.pack(side=tk.LEFT)
            cap_entry.bind("<Return>", lambda e, c=ch: self.set_rgb_max_slider_limit(c))
            cap_entry.bind("<FocusOut>", lambda e, c=ch: self.set_rgb_max_slider_limit(c))

        tk.Checkbutton(control_frame, text="Normalize to 99th Percentile", variable=self.normalize_var, font=("Arial", 13)).pack(anchor='w', pady=(10, 5))
        tk.Button(control_frame, text="View Overlay", command=self.view_rgb_overlay, font=("Arial", 13)).pack(fill=tk.X, pady=(10, 2))
        tk.Button(control_frame, text="Save RGB Image", command=self.save_rgb_image, font=("Arial", 13)).pack(fill=tk.X)

        # --- Correlation & Ratio Analysis Section ---
        tk.Label(control_frame, text="Correlation & Ratio Analysis", font=("Arial", 13, "bold")).pack(pady=(15, 5))
        
        # Element 1 selection
        tk.Label(control_frame, text="Element 1 (numerator):", font=("Arial", 11)).pack(anchor='w')
        elem1_menu = ttk.Combobox(control_frame, textvariable=self.correlation_elem1, values=['R', 'G', 'B'], 
                                  state='readonly', font=("Arial", 11), width=10)
        elem1_menu.pack(fill=tk.X, pady=(0, 5))
        
        # Element 2 selection
        tk.Label(control_frame, text="Element 2 (denominator):", font=("Arial", 11)).pack(anchor='w')
        elem2_menu = ttk.Combobox(control_frame, textvariable=self.correlation_elem2, values=['R', 'G', 'B'], 
                                  state='readonly', font=("Arial", 11), width=10)
        elem2_menu.pack(fill=tk.X, pady=(0, 5))
        
        # Calculate button
        tk.Button(control_frame, text="Calculate Ratio Map", command=self.calculate_ratio_map, 
                  font=("Arial", 12, "bold"), bg="#9C27B0", fg="white").pack(fill=tk.X, pady=(5, 2))
        
        # Correlation coefficient display
        self.correlation_label = tk.Label(control_frame, text="Pearson r: --", font=("Arial", 11, "italic"))
        self.correlation_label.pack(pady=(2, 5))
        
        # Save ratio matrix button
        tk.Button(control_frame, text="Save Ratio Matrix", command=self.save_ratio_matrix, 
                  font=("Arial", 12), fg="black").pack(fill=tk.X, pady=(0, 2))

        # Add responsive colorbar canvas for RGB overlay
        colorbar_frame = tk.Frame(display_frame, bg="black")
        colorbar_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))
        self.rgb_colorbar_figure, self.rgb_colorbar_ax = plt.subplots(figsize=(3, 1.2), dpi=100, facecolor='black')
        self.rgb_colorbar_ax.set_facecolor('black')
        self.rgb_colorbar_ax.axis('off')
        self.rgb_colorbar_canvas = FigureCanvasTkAgg(self.rgb_colorbar_figure, master=colorbar_frame)
        self.rgb_colorbar_canvas.get_tk_widget().configure(bg="black", highlightthickness=0, bd=0)
        self.rgb_colorbar_canvas.get_tk_widget().pack(fill=tk.X, expand=True)

        self.rgb_figure, self.rgb_ax = plt.subplots(facecolor='black')
        self.rgb_ax.set_facecolor('black')
        self.rgb_ax.axis('off')
        self.rgb_canvas = FigureCanvasTkAgg(self.rgb_figure, master=display_frame)
        self.rgb_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def pick_channel_color(self, channel):
        # Open color chooser and update color for the channel
        initial_color = self.rgb_colors[channel]
        color_code = colorchooser.askcolor(title=f"Pick color for channel {channel}", color=initial_color)
        if color_code and color_code[1]:
            self.rgb_colors[channel] = color_code[1]
            # Update button color
            self.rgb_color_buttons[channel].configure(bg=color_code[1])
            # Redraw gradient
            self.draw_gradient(self.rgb_gradient_canvases[channel], color_code[1])
            # Update overlay if visible
            self.view_rgb_overlay()

    def set_rgb_max_slider_limit(self, channel):
        try:
            val = float(self.rgb_max_limits[channel].get())
            val = float(val)
            min_val = self.rgb_sliders[channel]['max'].cget('from')
            if val > min_val:
                self.rgb_sliders[channel]['max'].config(to=val)
                if self.rgb_sliders[channel]['max'].get() > val:
                    self.rgb_sliders[channel]['max'].set(val)
                self.rgb_max_limits[channel].set(val)
                self.view_rgb_overlay()
            else:
                self.rgb_max_limits[channel].set(self.rgb_sliders[channel]['max'].cget('to'))
        except Exception:
            self.rgb_max_limits[channel].set(self.rgb_sliders[channel]['max'].cget('to'))

    def pick_scalebar_color(self):
        """Open color chooser for scale bar color and update the scale bar."""
        initial_color = self.scalebar_color
        color_code = colorchooser.askcolor(title="Pick Scale Bar Color", color=initial_color)
        if color_code and color_code[1]:
            self.scalebar_color = color_code[1]
            # Update button color
            self.scalebar_color_btn.configure(bg=color_code[1])
            # Update scale bar if visible
            if self.show_scalebar.get():
                self.view_single_map()

    def draw_gradient(self, canvas, color):
        # Accepts either a color name ('red', 'green', 'blue') or a hex color
        canvas.delete("all")
        # If color is a hex string, interpolate from black to that color
        if isinstance(color, str) and color.startswith('#') and len(color) == 7:
            # Get RGB values
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            for i in range(256):
                frac = i / 255.0
                rr = int(r * frac)
                gg = int(g * frac)
                bb = int(b * frac)
                c = f'#{rr:02x}{gg:02x}{bb:02x}'
                canvas.create_line(i, 0, i, 10, fill=c)
        else:
            # Fallback to old behavior for 'red', 'green', 'blue'
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
            # Update min/max values and sliders
            min_val = np.nanmin(mat)
            max_val = np.nanmax(mat)
            self.single_min.set(min_val)
            self.single_max.set(max_val)
            self.min_slider.config(from_=min_val, to=max_val)
            self.max_slider.config(from_=min_val, to=max_val)
            self.min_slider.set(min_val)
            self.max_slider.set(max_val)
            # Set the max_slider_limit variable and entry to the default max (rounded to integer)
            self.max_slider_limit.set(round(max_val))
            # Update loaded file label
            self.single_file_name = os.path.basename(path)
            self.single_file_label.config(text=f"Loaded file: {self.single_file_name}")
            self.view_single_map()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load matrix file:\n{e}")
            self.single_file_label.config(text="Loaded file: None")
            self.single_file_name = None

    def view_single_map(self, update_layout=True):
        if self.single_matrix is None:
            return
        mat = np.array(self.single_matrix, dtype=float)
        mat[np.isnan(mat)] = 0
        # Update min/max values from sliders in case they changed
        vmin = self.single_min.get()
        vmax = self.single_max.get()
        self.single_ax.clear()
        im = self.single_ax.imshow(mat, cmap=self.single_colormap.get(), vmin=vmin, vmax=vmax)
        self.single_ax.axis('off')
        
        # Handle colorbar creation/removal
        colorbar_needed = self.show_colorbar.get()
        colorbar_exists = hasattr(self, '_single_colorbar') and self._single_colorbar is not None
        
        if colorbar_exists and not colorbar_needed:
            # Remove colorbar if it exists but shouldn't
            try:
                self._single_colorbar.remove()
            except Exception:
                pass
            self._single_colorbar = None
            # Layout needs to be updated when colorbar is removed
            update_layout = True
        elif not colorbar_exists and colorbar_needed:
            # Create colorbar if it doesn't exist but should
            self._single_colorbar = self.single_figure.colorbar(im, ax=self.single_ax, fraction=0.046, pad=0.04, shrink=0.4, label="PPM")
            self._single_colorbar.set_label("PPM", fontfamily='Arial', fontsize=14)
            # Set tick labels to use Arial font
            self._single_colorbar.ax.tick_params(labelsize=12)
            for label in self._single_colorbar.ax.get_yticklabels():
                label.set_fontfamily('Arial')
            # Layout needs to be updated when colorbar is created
            update_layout = True
        elif colorbar_exists and colorbar_needed:
            # Update existing colorbar without recreating it
            self._single_colorbar.update_normal(im)
            # Ensure fonts are updated
            try:
                self._single_colorbar.set_label("PPM", fontfamily='Arial', fontsize=14)
                self._single_colorbar.ax.tick_params(labelsize=12)
                for label in self._single_colorbar.ax.get_yticklabels():
                    label.set_fontfamily('Arial')
            except Exception:
                pass
        
        if self.show_scalebar.get():
            bar_length = self.scale_length.get() / self.pixel_size.get()
            x = 5
            y = mat.shape[0] - 15
            self.single_ax.plot([x, x + bar_length], [y, y], color=self.scalebar_color, lw=3)
            self.single_ax.text(x, y - 10, f"{int(self.scale_length.get())} µm", color=self.scalebar_color, fontsize=10, ha='left', fontfamily='Arial')
        
        if update_layout:
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
                # initialize per-channel slider cap
                if channel in self.rgb_max_limits:
                    self.rgb_max_limits[channel].set(round(max_val))
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
        # Now, instead of stacking as RGB, use the selected color for each channel
        rgb = np.zeros((shape[0], shape[1], 3), dtype=float)
        for idx, ch in enumerate('RGB'):
            color_hex = self.rgb_colors[ch]
            r = int(color_hex[1:3], 16) / 255.0
            g = int(color_hex[3:5], 16) / 255.0
            b = int(color_hex[5:7], 16) / 255.0
            # Add the channel's scaled matrix times the color
            rgb[..., 0] += composite[idx] * r
            rgb[..., 1] += composite[idx] * g
            rgb[..., 2] += composite[idx] * b
        rgb = np.clip(rgb, 0, 1)
        rgb[np.isnan(rgb)] = 0
        black_mask = np.all(rgb == 0, axis=2)
        rgb[black_mask] = [0, 0, 0]
        self.rgb_ax.clear()
        self.rgb_ax.imshow(rgb)
        self.rgb_ax.axis('off')
        self.rgb_figure.tight_layout()
        self.rgb_canvas.draw()
        # Draw responsive colorbar
        self.draw_rgb_colorbar()

    def draw_rgb_colorbar(self):
        # Determine which channels are loaded
        loaded = [ch for ch in 'RGB' if self.rgb_data[ch] is not None]
        colors = [self.rgb_colors[ch] for ch in loaded]
        labels = []
        for ch in loaded:
            label = self.rgb_labels[ch]['elem'].cget("text")
            if label.startswith("Loaded Element: "):
                label = label[len("Loaded Element: "):]
            labels.append(label if label != "None" else ch)
        self.rgb_colorbar_ax.clear()
        self.rgb_colorbar_ax.axis('off')
        if len(loaded) == 3:
            # Draw a triangle with each vertex colored
            triangle = np.zeros((120, 240, 3), dtype=float)
            # Get RGB for each color
            rgb_vals = []
            for c in colors:
                r = int(c[1:3], 16) / 255.0
                g = int(c[3:5], 16) / 255.0
                b = int(c[5:7], 16) / 255.0
                rgb_vals.append([r, g, b])
            # Triangle vertices
            v0 = np.array([120, 10])   # left
            v1 = np.array([230, 110])  # right
            v2 = np.array([10, 110])   # bottom
            # For each pixel, barycentric interpolation
            for y in range(120):
                for x in range(240):
                    p = np.array([x, y])
                    # Compute barycentric coordinates
                    denom = ((v1[1] - v2[1])*(v0[0] - v2[0]) + (v2[0] - v1[0])*(v0[1] - v2[1]))
                    if denom == 0:
                        continue
                    l1 = ((v1[1] - v2[1])*(p[0] - v2[0]) + (v2[0] - v1[0])*(p[1] - v2[1])) / denom
                    l2 = ((v2[1] - v0[1])*(p[0] - v2[0]) + (v0[0] - v2[0])*(p[1] - v2[1])) / denom
                    l3 = 1 - l1 - l2
                    if (l1 >= 0) and (l2 >= 0) and (l3 >= 0):
                        color = l1 * np.array(rgb_vals[0]) + l2 * np.array(rgb_vals[1]) + l3 * np.array(rgb_vals[2])
                        triangle[y, x, :] = color
            self.rgb_colorbar_ax.imshow(triangle, origin='upper', extent=[0, 1, 0, 1])
            # Draw triangle outline
            self.rgb_colorbar_ax.plot([v0[0]/240, v1[0]/240], [1-v0[1]/120, 1-v1[1]/120], color='k', lw=1)
            self.rgb_colorbar_ax.plot([v1[0]/240, v2[0]/240], [1-v1[1]/120, 1-v2[1]/120], color='k', lw=1)
            self.rgb_colorbar_ax.plot([v2[0]/240, v0[0]/240], [1-v2[1]/120, 1-v0[1]/120], color='k', lw=1)
            # Place labels at vertices
            self.rgb_colorbar_ax.text(v0[0]/240, 1-v0[1]/120-0.05, labels[0], color=colors[0], fontsize=10, ha='center', va='top', fontweight='bold', fontfamily='Arial')
            self.rgb_colorbar_ax.text(v1[0]/240+0.04, 1-v1[1]/120, labels[1], color=colors[1], fontsize=10, ha='left', va='center', fontweight='bold', fontfamily='Arial')
            self.rgb_colorbar_ax.text(v2[0]/240-0.04, 1-v2[1]/120, labels[2], color=colors[2], fontsize=10, ha='right', va='center', fontweight='bold', fontfamily='Arial')
            self.rgb_colorbar_ax.set_xlim(0, 1)
            self.rgb_colorbar_ax.set_ylim(0, 1)
        elif len(loaded) == 2:
            # Draw a horizontal gradient bar between the two colors
            width = 240
            height = 30
            grad = np.zeros((height, width, 3), dtype=float)
            rgb0 = [int(colors[0][1:3], 16)/255.0, int(colors[0][3:5], 16)/255.0, int(colors[0][5:7], 16)/255.0]
            rgb1 = [int(colors[1][1:3], 16)/255.0, int(colors[1][3:5], 16)/255.0, int(colors[1][5:7], 16)/255.0]
            for x in range(width):
                frac = x / (width-1)
                color = (1-frac)*np.array(rgb0) + frac*np.array(rgb1)
                grad[:, x, :] = color
            self.rgb_colorbar_ax.imshow(grad, origin='upper', extent=[0, 1, 0, 1])
            # Draw bar outline
            self.rgb_colorbar_ax.plot([0, 1], [0, 0], color='k', lw=1)
            self.rgb_colorbar_ax.plot([0, 1], [1, 1], color='k', lw=1)
            self.rgb_colorbar_ax.plot([0, 0], [0, 1], color='k', lw=1)
            self.rgb_colorbar_ax.plot([1, 1], [0, 1], color='k', lw=1)
            # Place labels at ends
            self.rgb_colorbar_ax.text(0, 1.05, labels[0], color=colors[0], fontsize=10, ha='left', va='bottom', fontweight='bold', fontfamily='Arial')
            self.rgb_colorbar_ax.text(1, 1.05, labels[1], color=colors[1], fontsize=10, ha='right', va='bottom', fontweight='bold', fontfamily='Arial')
            self.rgb_colorbar_ax.set_xlim(0, 1)
            self.rgb_colorbar_ax.set_ylim(0, 1)
        elif len(loaded) == 1:
            # Draw a single color bar
            width = 240
            height = 30
            grad = np.zeros((height, width, 3), dtype=float)
            rgb0 = [int(colors[0][1:3], 16)/255.0, int(colors[0][3:5], 16)/255.0, int(colors[0][5:7], 16)/255.0]
            for x in range(width):
                frac = x / (width-1)
                color = frac*np.array(rgb0)
                grad[:, x, :] = color
            self.rgb_colorbar_ax.imshow(grad, origin='upper', extent=[0, 1, 0, 1])
            self.rgb_colorbar_ax.plot([0, 1], [0, 0], color='k', lw=1)
            self.rgb_colorbar_ax.plot([0, 1], [1, 1], color='k', lw=1)
            self.rgb_colorbar_ax.plot([0, 0], [0, 1], color='k', lw=1)
            self.rgb_colorbar_ax.plot([1, 1], [0, 1], color='k', lw=1)
            self.rgb_colorbar_ax.text(1, 1.05, labels[0], color=colors[0], fontsize=10, ha='right', va='bottom', fontweight='bold', fontfamily='Arial')
            self.rgb_colorbar_ax.set_xlim(0, 1)
            self.rgb_colorbar_ax.set_ylim(0, 1)
        else:
            # No channels loaded, clear
            self.rgb_colorbar_ax.set_xlim(0, 1)
            self.rgb_colorbar_ax.set_ylim(0, 1)
        self.rgb_colorbar_figure.tight_layout()
        self.rgb_colorbar_canvas.draw()

    def save_rgb_image(self):
        if all(self.rgb_data[c] is None for c in 'RGB'):
            return
        out_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if out_path:
            # Check if we should save with or without colorbar
            save_with_colorbar = messagebox.askyesno(
                "Save Options",
                "Would you like to save the image with the colorbar?\n\n"
                "Yes: Save RGB image + colorbar combined\n"
                "No: Save RGB image only (no colorbar)"
            )
            
            if save_with_colorbar:
                # Create a combined figure with RGB image and colorbar
                # Get the RGB image data from the current figure
                img_array = self.rgb_ax.get_images()[0].get_array()
                extent = self.rgb_ax.get_images()[0].get_extent()
                
                # Create new figure with proper proportions for colorbar
                fig = plt.figure(figsize=(8, 8))
                gs = GridSpec(2, 1, figure=fig, height_ratios=[10, 1], hspace=0.05)
                
                # Main RGB plot (larger)
                ax_main = fig.add_subplot(gs[0])
                ax_main.imshow(img_array, extent=extent, aspect='auto')
                ax_main.axis('off')
                
                # Colorbar at bottom (smaller)
                ax_cbar = fig.add_subplot(gs[1])
                
                # Determine which channels are loaded and draw colorbar
                loaded = [ch for ch in 'RGB' if self.rgb_data[ch] is not None]
                colors = [self.rgb_colors[ch] for ch in loaded]
                labels = []
                for ch in loaded:
                    label = self.rgb_labels[ch]['elem'].cget("text")
                    if label.startswith("Loaded Element: "):
                        label = label[len("Loaded Element: "):]
                    labels.append(label if label != "None" else ch)
                
                ax_cbar.axis('off')
                
                if len(loaded) == 3:
                    # Draw triangle colorbar
                    triangle = np.zeros((100, 200, 3), dtype=float)
                    rgb_vals = []
                    for c in colors:
                        r = int(c[1:3], 16) / 255.0
                        g = int(c[3:5], 16) / 255.0
                        b = int(c[5:7], 16) / 255.0
                        rgb_vals.append([r, g, b])
                    v0 = np.array([100, 10])
                    v1 = np.array([190, 90])
                    v2 = np.array([10, 90])
                    for y in range(100):
                        for x in range(200):
                            p = np.array([x, y])
                            denom = ((v1[1] - v2[1])*(v0[0] - v2[0]) + (v2[0] - v1[0])*(v0[1] - v2[1]))
                            if denom == 0:
                                continue
                            l1 = ((v1[1] - v2[1])*(p[0] - v2[0]) + (v2[0] - v1[0])*(p[1] - v2[1])) / denom
                            l2 = ((v2[1] - v0[1])*(p[0] - v2[0]) + (v0[0] - v2[0])*(p[1] - v2[1])) / denom
                            l3 = 1 - l1 - l2
                            if (l1 >= 0) and (l2 >= 0) and (l3 >= 0):
                                color = l1 * np.array(rgb_vals[0]) + l2 * np.array(rgb_vals[1]) + l3 * np.array(rgb_vals[2])
                                triangle[y, x, :] = color
                    ax_cbar.imshow(triangle, origin='upper', extent=[0, 1, 0, 1])
                    ax_cbar.plot([v0[0]/200, v1[0]/200], [1-v0[1]/100, 1-v1[1]/100], color='k', lw=1)
                    ax_cbar.plot([v1[0]/200, v2[0]/200], [1-v1[1]/100, 1-v2[1]/100], color='k', lw=1)
                    ax_cbar.plot([v2[0]/200, v0[0]/200], [1-v2[1]/100, 1-v0[1]/100], color='k', lw=1)
                    ax_cbar.text(v0[0]/200, 1-v0[1]/100-0.1, labels[0], color=colors[0], fontsize=8, ha='center', va='top', fontweight='bold', fontfamily='Arial')
                    ax_cbar.text(v1[0]/200+0.05, 1-v1[1]/100, labels[1], color=colors[1], fontsize=8, ha='left', va='center', fontweight='bold', fontfamily='Arial')
                    ax_cbar.text(v2[0]/200-0.05, 1-v2[1]/100, labels[2], color=colors[2], fontsize=8, ha='right', va='center', fontweight='bold', fontfamily='Arial')
                elif len(loaded) == 2:
                    # Draw horizontal gradient bar
                    width = 200
                    height = 30
                    grad = np.zeros((height, width, 3), dtype=float)
                    rgb0 = [int(colors[0][1:3], 16)/255.0, int(colors[0][3:5], 16)/255.0, int(colors[0][5:7], 16)/255.0]
                    rgb1 = [int(colors[1][1:3], 16)/255.0, int(colors[1][3:5], 16)/255.0, int(colors[1][5:7], 16)/255.0]
                    for x in range(width):
                        frac = x / (width-1)
                        color = (1-frac)*np.array(rgb0) + frac*np.array(rgb1)
                        grad[:, x, :] = color
                    ax_cbar.imshow(grad, origin='upper', extent=[0, 1, 0, 1])
                    ax_cbar.plot([0, 1], [0, 0], color='k', lw=1)
                    ax_cbar.plot([0, 1], [1, 1], color='k', lw=1)
                    ax_cbar.plot([0, 0], [0, 1], color='k', lw=1)
                    ax_cbar.plot([1, 1], [0, 1], color='k', lw=1)
                    ax_cbar.text(0, 1.1, labels[0], color=colors[0], fontsize=8, ha='left', va='bottom', fontweight='bold', fontfamily='Arial')
                    ax_cbar.text(1, 1.1, labels[1], color=colors[1], fontsize=8, ha='right', va='bottom', fontweight='bold', fontfamily='Arial')
                elif len(loaded) == 1:
                    # Draw single color bar
                    width = 200
                    height = 30
                    grad = np.zeros((height, width, 3), dtype=float)
                    rgb0 = [int(colors[0][1:3], 16)/255.0, int(colors[0][3:5], 16)/255.0, int(colors[0][5:7], 16)/255.0]
                    for x in range(width):
                        frac = x / (width-1)
                        color = frac*np.array(rgb0)
                        grad[:, x, :] = color
                    ax_cbar.imshow(grad, origin='upper', extent=[0, 1, 0, 1])
                    ax_cbar.plot([0, 1], [0, 0], color='k', lw=1)
                    ax_cbar.plot([0, 1], [1, 1], color='k', lw=1)
                    ax_cbar.plot([0, 0], [0, 1], color='k', lw=1)
                    ax_cbar.plot([1, 1], [0, 1], color='k', lw=1)
                    ax_cbar.text(1, 1.1, labels[0], color=colors[0], fontsize=8, ha='right', va='bottom', fontweight='bold', fontfamily='Arial')
                
                ax_cbar.set_xlim(0, 1)
                ax_cbar.set_ylim(0, 1)
                
                fig.tight_layout()
                fig.savefig(out_path, dpi=300, bbox_inches='tight')
                plt.close(fig)
            else:
                # Save without colorbar (original behavior)
                self.rgb_figure.savefig(out_path, dpi=300, bbox_inches='tight')

    # --- Correlation & Ratio Analysis Functions ---
    def calculate_ratio_map(self):
        """Calculate the ratio map between two selected elements."""
        elem1 = self.correlation_elem1.get()
        elem2 = self.correlation_elem2.get()
        
        # Check if both elements are loaded
        if self.rgb_data[elem1] is None:
            messagebox.showwarning("Missing Data", f"Please load data for {elem1} channel first.")
            return
        if self.rgb_data[elem2] is None:
            messagebox.showwarning("Missing Data", f"Please load data for {elem2} channel first.")
            return
        
        # Check if trying to divide element by itself
        if elem1 == elem2:
            messagebox.showwarning("Invalid Selection", "Please select two different elements.")
            return
        
        # Get the matrices
        mat1 = self.rgb_data[elem1]
        mat2 = self.rgb_data[elem2]
        
        # Check if matrices have the same shape
        if mat1.shape != mat2.shape:
            messagebox.showerror("Shape Mismatch", 
                                f"Element matrices have different shapes:\n"
                                f"{elem1}: {mat1.shape}\n{elem2}: {mat2.shape}\n"
                                f"Cannot calculate ratio.")
            return
        
        # Calculate ratio (handle division by zero)
        with np.errstate(divide='ignore', invalid='ignore'):
            ratio = mat1 / mat2
            # Set infinite values to NaN
            ratio[np.isinf(ratio)] = np.nan
        
        self.ratio_matrix = ratio
        
        # Calculate Pearson correlation coefficient
        # Flatten and remove NaN values for correlation
        flat1 = mat1.flatten()
        flat2 = mat2.flatten()
        valid_mask = ~(np.isnan(flat1) | np.isnan(flat2) | (flat1 == 0) | (flat2 == 0))
        
        if np.sum(valid_mask) > 2:  # Need at least 2 points for correlation
            from scipy.stats import pearsonr
            r_value, p_value = pearsonr(flat1[valid_mask], flat2[valid_mask])
            self.correlation_coefficient = r_value
            self.correlation_label.config(text=f"Pearson r: {r_value:.4f} (p={p_value:.2e})")
        else:
            self.correlation_coefficient = None
            self.correlation_label.config(text="Pearson r: insufficient data")
        
        # Get element names from labels
        elem1_name = self.rgb_labels[elem1]['elem'].cget("text").replace("Loaded Element: ", "")
        elem2_name = self.rgb_labels[elem2]['elem'].cget("text").replace("Loaded Element: ", "")
        if elem1_name == "None":
            elem1_name = elem1
        if elem2_name == "None":
            elem2_name = elem2
        
        # Display the ratio map in a new window
        self.display_ratio_map(ratio, elem1_name, elem2_name)
    
    def display_ratio_map(self, ratio, elem1_name, elem2_name):
        """Display the ratio map in a new window."""
        # Create a new window
        ratio_window = tk.Toplevel(self.root)
        ratio_window.title(f"Ratio Map: {elem1_name} / {elem2_name}")
        ratio_window.geometry("800x700")
        
        # Create figure
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Display ratio map with a diverging colormap
        # Calculate sensible vmin/vmax (exclude extreme outliers)
        valid_ratios = ratio[~np.isnan(ratio)]
        if len(valid_ratios) > 0:
            vmin = np.nanpercentile(ratio, 5)
            vmax = np.nanpercentile(ratio, 95)
        else:
            vmin, vmax = 0, 1
        
        im = ax.imshow(ratio, cmap='RdYlBu_r', vmin=vmin, vmax=vmax)
        ax.axis('off')
        
        # Add colorbar
        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, shrink=0.4)
        cbar.set_label(f"{elem1_name} / {elem2_name}", fontfamily='Arial', fontsize=14)
        cbar.ax.tick_params(labelsize=12)
        for label in cbar.ax.get_yticklabels():
            label.set_fontfamily('Arial')
        
        # Add title with correlation info
        if self.correlation_coefficient is not None:
            ax.set_title(f"Ratio Map: {elem1_name} / {elem2_name}\nPearson r = {self.correlation_coefficient:.4f}", 
                        fontfamily='Arial', fontsize=14, pad=10)
        else:
            ax.set_title(f"Ratio Map: {elem1_name} / {elem2_name}", 
                        fontfamily='Arial', fontsize=14, pad=10)
        
        fig.tight_layout()
        
        # Embed in tkinter window
        canvas = FigureCanvasTkAgg(fig, master=ratio_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add buttons at the bottom
        button_frame = tk.Frame(ratio_window)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        tk.Button(button_frame, text="Save Ratio Matrix", command=self.save_ratio_matrix, 
                  font=("Arial", 12), fg="black").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Save as PNG", 
                  command=lambda: self.save_ratio_image(fig), 
                  font=("Arial", 12), fg="black").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Close", command=ratio_window.destroy, 
                  font=("Arial", 12), fg="black").pack(side=tk.RIGHT, padx=5)
        
        # Store references
        self.ratio_figure = fig
        self.ratio_ax = ax
    
    def save_ratio_matrix(self):
        """Save the ratio matrix to an Excel or CSV file."""
        if self.ratio_matrix is None:
            messagebox.showwarning("No Ratio Data", "Please calculate a ratio map first.")
            return
        
        # Get element names for filename
        elem1 = self.correlation_elem1.get()
        elem2 = self.correlation_elem2.get()
        elem1_name = self.rgb_labels[elem1]['elem'].cget("text").replace("Loaded Element: ", "")
        elem2_name = self.rgb_labels[elem2]['elem'].cget("text").replace("Loaded Element: ", "")
        if elem1_name == "None":
            elem1_name = elem1
        if elem2_name == "None":
            elem2_name = elem2
        
        # Generate default filename
        default_name = f"{elem1_name}_over_{elem2_name}_ratio.xlsx"
        
        # Ask user for save location
        save_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[
                ("Excel files", "*.xlsx"),
                ("CSV files", "*.csv")
            ],
            initialfile=default_name
        )
        
        if save_path:
            try:
                if save_path.endswith('.xlsx'):
                    df = pd.DataFrame(self.ratio_matrix)
                    df.to_excel(save_path, header=False, index=False)
                elif save_path.endswith('.csv'):
                    df = pd.DataFrame(self.ratio_matrix)
                    df.to_csv(save_path, header=False, index=False)
                
                corr_text = ""
                if self.correlation_coefficient is not None:
                    corr_text = f"\nPearson r = {self.correlation_coefficient:.4f}"
                
                messagebox.showinfo("Saved", 
                                  f"Ratio matrix saved successfully!\n\n"
                                  f"File: {os.path.basename(save_path)}\n"
                                  f"Ratio: {elem1_name} / {elem2_name}\n"
                                  f"Matrix shape: {self.ratio_matrix.shape}{corr_text}")
                
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save ratio matrix:\n{str(e)}")
    
    def save_ratio_image(self, figure):
        """Save the ratio map figure as a PNG."""
        out_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if out_path:
            figure.savefig(out_path, dpi=300, bbox_inches='tight')
            messagebox.showinfo("Saved", f"Ratio map image saved to:\n{os.path.basename(out_path)}")
    
    # --- End Correlation & Ratio Analysis Functions ---

def main():
    root = tk.Tk()
    root.geometry("1100x850")
    app = MuadDataViewer(root)
    root.mainloop()

if __name__ == '__main__':
    main()
