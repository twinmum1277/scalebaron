# Muad'Data v17 - Fully Functional Element Viewer + RGB Overlay Tabs
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, colorchooser
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
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

        # RGB Overlay state
        self.rgb_data = {'R': None, 'G': None, 'B': None}
        self.rgb_sliders = {}
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
        # Update plot and histogram when min slider is changed
        self.min_slider.bind("<ButtonRelease-1>", lambda e: self.update_histogram_and_view())
        self.min_slider.bind("<B1-Motion>", lambda e: self.update_histogram_and_view())

        # Add histogram frame above Max Value
        histogram_frame = tk.Frame(control_frame)
        histogram_frame.pack(fill=tk.X, pady=(5, 0))
        tk.Label(histogram_frame, text="Data Distribution", font=("Arial", 11)).pack()
        self.histogram_canvas = tk.Canvas(histogram_frame, height=60, width=200, bg='white', relief='sunken', bd=1)
        self.histogram_canvas.pack(fill=tk.X, pady=(2, 5))

        # --- Max Value controls ---
        tk.Label(control_frame, text="Max Value", font=("Arial", 13)).pack()

        # Frame for max slider
        max_slider_frame = tk.Frame(control_frame)
        max_slider_frame.pack(fill=tk.X)

        self.max_slider = tk.Scale(max_slider_frame, from_=0, to=1, resolution=0.01, orient=tk.HORIZONTAL, variable=self.single_max, font=("Arial", 13))
        self.max_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        # Update plot and histogram when max slider is changed
        self.max_slider.bind("<ButtonRelease-1>", lambda e: self.update_histogram_and_view())
        self.max_slider.bind("<B1-Motion>", lambda e: self.update_histogram_and_view())

        # Entry for setting the max value of the slider (now below the slider)
        slider_max_frame = tk.Frame(control_frame)
        slider_max_frame.pack(fill=tk.X, pady=(2, 0))
        tk.Label(slider_max_frame, text="Slider Max:", font=("Arial", 12)).pack(side=tk.LEFT)
        self.max_slider_limit_entry = tk.Entry(slider_max_frame, textvariable=self.max_slider_limit, width=8, font=("Arial", 11))
        self.max_slider_limit_entry.pack(side=tk.LEFT)
        self.max_slider_limit_entry.bind("<Return>", lambda e: self.set_max_slider_limit())
        self.max_slider_limit_entry.bind("<FocusOut>", lambda e: self.set_max_slider_limit())

        tk.Checkbutton(control_frame, text="Show Color Bar", variable=self.show_colorbar, font=("Arial", 13)).pack(anchor='w')
        tk.Checkbutton(control_frame, text="Show Scale Bar", variable=self.show_scalebar, font=("Arial", 13)).pack(anchor='w')
        
        # Scale bar color picker
        scalebar_color_frame = tk.Frame(control_frame)
        scalebar_color_frame.pack(fill=tk.X, pady=(5, 0))
        tk.Label(scalebar_color_frame, text="Scale Bar Color:", font=("Arial", 11)).pack(side=tk.LEFT)
        self.scalebar_color_btn = tk.Button(scalebar_color_frame, text="Pick Color", bg=self.scalebar_color, fg='black', 
                                          font=("Arial", 10, "bold"), command=self.pick_scalebar_color)
        self.scalebar_color_btn.pack(side=tk.LEFT, padx=(5, 0))

        tk.Label(control_frame, text="Pixel size (µm)", font=("Arial", 13)).pack(pady=(10, 0))
        tk.Entry(control_frame, textvariable=self.pixel_size, font=("Arial", 13)).pack(fill=tk.X)

        tk.Label(control_frame, text="Scale bar length (µm)", font=("Arial", 13)).pack(pady=(10, 0))
        tk.Entry(control_frame, textvariable=self.scale_length, font=("Arial", 13)).pack(fill=tk.X)

        tk.Button(control_frame, text="View Map", command=self.view_single_map, font=("Arial", 13)).pack(fill=tk.X, pady=(10, 2))
        tk.Button(control_frame, text="Save PNG", command=self.save_single_image, font=("Arial", 13)).pack(fill=tk.X)

        # --- Math Expression Button ---
        tk.Button(control_frame, text="Map Math", command=self.open_map_math, font=("Arial", 13, "bold"), bg="#4CAF50", fg="black").pack(fill=tk.X, pady=(10, 2))

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
            # Round to nearest integer
            val = round(val)
            min_val = self.max_slider.cget('from')
            if val > min_val:
                self.max_slider.config(to=val)
                # If the current slider value is above the new max, set it to the new max
                if self.single_max.get() > val:
                    self.single_max.set(val)
                # Update the entry to show the rounded integer value
                self.max_slider_limit.set(val)
            else:
                # If entered value is not valid, reset to current slider max
                self.max_slider_limit.set(self.max_slider.cget('to'))
        except Exception:
            # If invalid input, reset to current slider max
            self.max_slider_limit.set(self.max_slider.cget('to'))

    def update_histogram_and_view(self):
        self.update_histogram()
        self.view_single_map(update_layout=False)

    def update_histogram(self):
        """Update the data distribution histogram based on current min/max slider values."""
        if self.single_matrix is None or self.histogram_canvas is None:
            return

        self.histogram_canvas.delete("all")

        # Get data and create histogram (only in current slider range)
        data = self.single_matrix.flatten()
        data = data[~np.isnan(data)]  # Remove NaN values
        current_min = self.single_min.get()
        current_max = self.single_max.get()
        data = data[(data >= current_min) & (data <= current_max)]

        if len(data) == 0:
            return

        # Create histogram
        hist, bin_edges = np.histogram(data, bins=50)

        # Get canvas dimensions
        canvas_width = self.histogram_canvas.winfo_width()
        canvas_height = self.histogram_canvas.winfo_height()

        if canvas_width <= 1:  # Canvas not yet drawn
            canvas_width = 200
            canvas_height = 60

        # Normalize histogram to fit canvas
        max_hist = np.max(hist)
        if max_hist == 0:
            return

        # Draw smooth curve like photo editors
        x_coords = []
        y_coords = []
        for i, count in enumerate(hist):
            if count > 0:
                x = (i / len(hist)) * canvas_width
                y = canvas_height - 5 - (count / max_hist) * (canvas_height - 10)
                x_coords.append(x)
                y_coords.append(y)

        # Create smooth curve with more points for better smoothing
        if len(x_coords) >= 2:
            # Create filled area under the curve (like photo editors)
            fill_points = []

            # Start at bottom-left
            fill_points.extend([0, canvas_height - 5])

            # Add curve points
            for i in range(len(x_coords)):
                fill_points.extend([x_coords[i], y_coords[i]])

            # End at bottom-right
            fill_points.extend([canvas_width, canvas_height - 5])

            # Draw filled area with light gray
            if len(fill_points) >= 6:
                self.histogram_canvas.create_polygon(fill_points, fill='lightgray', outline='', smooth=True)

            # Draw the curve line on top
            curve_points = []
            for i in range(len(x_coords)):
                curve_points.extend([x_coords[i], y_coords[i]])

            # Draw the smooth curve with anti-aliasing
            if len(curve_points) >= 4:
                self.histogram_canvas.create_line(curve_points, fill='darkgray', width=2, smooth=True, capstyle='round')

        # Add min/max indicators (always at left/right of canvas now)
        self.histogram_canvas.create_line(0, 0, 0, canvas_height, fill='red', width=2)
        self.histogram_canvas.create_line(canvas_width, 0, canvas_width, canvas_height, fill='blue', width=2)

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
                
                # Set the max_slider_limit variable and entry to the new max
                self.max_slider_limit.set(max_val)
                
                # Update histogram and view
                self.update_histogram()
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
            self.single_file_label.config(text=f"Loaded file: {self.single_file_name} (modified)")
        else:
            self.single_file_label.config(text="Loaded file: None")

    # --- End Math Expression Functionality ---

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
            color_btn = tk.Button(color_picker_frame, text="Pick Color", bg=self.rgb_colors[ch], fg='white', font=("Arial", 10, "bold"),
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

        tk.Checkbutton(control_frame, text="Normalize to 99th Percentile", variable=self.normalize_var, font=("Arial", 13)).pack(anchor='w', pady=(10, 5))
        tk.Button(control_frame, text="View Overlay", command=self.view_rgb_overlay, font=("Arial", 13)).pack(fill=tk.X, pady=(10, 2))
        tk.Button(control_frame, text="Save RGB Image", command=self.save_rgb_image, font=("Arial", 13)).pack(fill=tk.X)

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
            # Set the max_slider_limit variable and entry to the default max
            self.max_slider_limit.set(max_val)
            # Update loaded file label
            self.single_file_name = os.path.basename(path)
            self.single_file_label.config(text=f"Loaded file: {self.single_file_name}")
            self.update_histogram()
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
        # Remove previous colorbar if it exists
        if hasattr(self, '_single_colorbar') and self._single_colorbar is not None:
            try:
                self._single_colorbar.remove()
            except Exception:
                pass
            self._single_colorbar = None
        if self.show_colorbar.get():
            self._single_colorbar = self.single_figure.colorbar(im, ax=self.single_ax, fraction=0.046, pad=0.04, label="PPM")
        if self.show_scalebar.get():
            bar_length = self.scale_length.get() / self.pixel_size.get()
            x = 5
            y = mat.shape[0] - 15
            self.single_ax.plot([x, x + bar_length], [y, y], color=self.scalebar_color, lw=3)
            self.single_ax.text(x, y - 10, f"{int(self.scale_length.get())} µm", color=self.scalebar_color, fontsize=10, ha='left')
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
            self.rgb_colorbar_ax.text(v0[0]/240, 1-v0[1]/120-0.05, labels[0], color=colors[0], fontsize=10, ha='center', va='top', fontweight='bold')
            self.rgb_colorbar_ax.text(v1[0]/240+0.04, 1-v1[1]/120, labels[1], color=colors[1], fontsize=10, ha='left', va='center', fontweight='bold')
            self.rgb_colorbar_ax.text(v2[0]/240-0.04, 1-v2[1]/120, labels[2], color=colors[2], fontsize=10, ha='right', va='center', fontweight='bold')
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
            self.rgb_colorbar_ax.text(0, 1.05, labels[0], color=colors[0], fontsize=10, ha='left', va='bottom', fontweight='bold')
            self.rgb_colorbar_ax.text(1, 1.05, labels[1], color=colors[1], fontsize=10, ha='right', va='bottom', fontweight='bold')
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
            self.rgb_colorbar_ax.text(1, 1.05, labels[0], color=colors[0], fontsize=10, ha='right', va='bottom', fontweight='bold')
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
            self.rgb_figure.savefig(out_path, dpi=300, bbox_inches='tight')

def main():
    root = tk.Tk()
    root.geometry("1100x700")
    app = MuadDataViewer(root)
    root.mainloop()

if __name__ == '__main__':
    main()
