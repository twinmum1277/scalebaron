# This script sets up a GUI application version of your command-line tool using tkinter
# Core features: Load data, choose element, layout options, preview, and save composite
# TP: THIS VERSION CLONED from Josh's most recent upload, with user-friendly GUI layout changes, 3 sig fig constraint, ppm or CPS input

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, font
import numpy as np  # pyright: ignore[reportMissingImports]
import matplotlib  # pyright: ignore[reportMissingImports]
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
    
    def parse_matrix_filename(self, filename):
        """
        Parse matrix filename to extract sample name, element, and unit type.
        Supports two formats:
        1. Old format: {sample}[ _]{element}_{ppm|CPS} matrix.xlsx
        2. New format (Iolite raw CPS): {sample} {element} matrix.xlsx
        
        Returns: (sample, element, unit_type) or None if no match
        unit_type will be 'ppm', 'CPS', or 'raw' (for new format)
        """
        basename = os.path.basename(filename)
        
        # Try old format first: {sample}[ _]{element}_{ppm|CPS} matrix.xlsx
        match = re.match(r"(.+?)[ _]([A-Za-z]{1,2}\d{1,3})_(ppm|CPS) matrix\.xlsx", basename)
        if match:
            sample, element, unit_type = match.groups()
            return (sample, element, unit_type)
        
        # Try new format: {sample} {element} matrix.xlsx
        # This matches filenames like "LVG D4 0.6 Se80 matrix.xlsx" or "sample Li7 matrix.xlsx"
        match = re.match(r"(.+?) ([A-Za-z]{1,2}\d{1,3}) matrix\.xlsx", basename)
        if match:
            sample, element = match.groups()
            return (sample, element, 'raw')
        
        return None

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
        self.element_label_font_size = tk.IntVar(value=16)  # Font size for element label (default 16)
        self.scale_max = tk.DoubleVar(value=1.0)  # New variable for scale_max, constrained to 2 decimal places
        self.use_custom_pixel_sizes = tk.BooleanVar(value=False)  # New variable for custom pixel sizes
        self.use_button_icons = tk.BooleanVar(value=False)  # Toggle for icon buttons

        self.input_dir = None
        self.output_dir = "./OUTPUT"
        os.makedirs(self.output_dir, exist_ok=True)

        self.matrices = []
        self.labels = []
        self.preview_file = None
        self.preview_image = None  # Current preview image (may have labels)
        self.original_preview_image = None  # Original unlabeled preview image
        self.custom_pixel_sizes = {}  # Dictionary to store custom pixel sizes
        self.pixel_sizes_by_sample = {}
        
        # Progress tracking
        self.progress_samples = []  # List of sample names
        self.progress_elements = []  # List of element names
        self.progress_table = None  # Treeview widget
        self.progress_data = {}  # {(sample, element): status} where status is 'complete', 'partial', or None
        
        # Status tracking for simplified log
        self.status = "Idle"  # Idle, Busy, Finishing
        
        # Button icons storage
        self.button_icons = {}  # Dictionary to store loaded button icons
        
        style = ttk.Style()
        style.configure("Hint.TLabel", foreground="gray", font=("TkDefaultFont", 12, "italic"))
        # Load icons BEFORE creating buttons so they're available when buttons are created
        self.load_button_icons()
        self.setup_widgets()

    def setup_widgets(self):
        # Create notebook for tabs (similar to Muad'Data style)
        self.tabs = ttk.Notebook(self.master)
        self.tabs.pack(fill=tk.BOTH, expand=True)
        
        # Create tab frames
        self.setup_tab = ttk.Frame(self.tabs)
        self.preview_tab = ttk.Frame(self.tabs)
        
        # Add tabs
        self.tabs.add(self.setup_tab, text="Setup & Statistics")
        self.tabs.add(self.preview_tab, text="Preview & Export")
        
        # Build each tab
        self.build_setup_tab()
        self.build_preview_tab()
        
        # Set minimum window size
        self.master.minsize(600, 500)
        self.master.resizable(True, True)
        
        # Progress table window (created on demand - legacy, not used in tabbed interface)
        self.progress_table_window = None
        # Note: self.progress_table is created in build_setup_tab(), don't overwrite it here!
        
        # Preview window (created on demand) - kept for separate window option
        self.preview_window = None
        self.preview_window_label = None
    
    def build_setup_tab(self):
        """Build the Setup & Statistics tab."""
        # Left side: Controls (fixed width to match Preview tab)
        left_frame = ttk.Frame(self.setup_tab, width=280)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        left_frame.pack_propagate(False)  # Maintain fixed width
        
        # Right side: Two-panel layout (Statistics Table, Progress Table)
        right_frame = ttk.Frame(self.setup_tab)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 1. Select folders
        folders_group = ttk.Frame(left_frame)
        folders_group.pack(pady=5)
        ttk.Label(folders_group, text="1. Select folders", style="Hint.TLabel").pack(pady=(5, 0))
        
        # Input folder
        ttk.Button(folders_group, text="Input", command=self.select_input_folder).pack(pady=(4, 0))
        self.input_folder_label = ttk.Label(folders_group, text="Input: None", font=("TkDefaultFont", 9), foreground="gray")
        self.input_folder_label.pack(pady=(2, 6))
        
        # Output folder
        ttk.Button(folders_group, text="Output", command=self.select_output_folder).pack(pady=(0, 0))
        self.output_folder_label = ttk.Label(folders_group, text=f"Output: {self.output_dir}", font=("TkDefaultFont", 9), foreground="gray")
        self.output_folder_label.pack(pady=(2, 6))
        
        # Control panel
        grid_frame = ttk.Frame(left_frame)
        grid_frame.pack(pady=10)
        
        # Element dropdown
        ttk.Label(grid_frame, text="Element:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        self.element_dropdown = ttk.Combobox(grid_frame, textvariable=self.element, state="disabled", width=12)
        self.element_dropdown.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        # Update statistics table when element changes
        self.element.trace('w', lambda *args: self.update_statistics_table())
        
        # Pixel Size input
        ttk.Label(grid_frame, text="Pixel Size (µm):").grid(row=1, column=0, sticky="e", padx=(0, 2), pady=2)
        pixel_entry_frame = ttk.Frame(grid_frame)
        pixel_entry_frame.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        ttk.Entry(pixel_entry_frame, textvariable=self.pixel_size, width=10).pack(side="left")
        ttk.Label(pixel_entry_frame, text="Hint: In your metadata", style="Hint.TLabel").pack(side="left", padx=(4, 0))
        
        # Multiple sizes checkbox
        multi_size_frame = ttk.Frame(grid_frame)
        multi_size_frame.grid(row=2, column=1, sticky="w", pady=(0, 10))
        ttk.Checkbutton(multi_size_frame, text="Multiple sizes?", variable=self.use_custom_pixel_sizes).pack(side="left")
        ttk.Button(multi_size_frame, text="Pixel Sizes", command=self.handle_pixel_sizes).pack(side="left", padx=(5, 0))
        
        # Calculate statistics button
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(pady=10)
        
        ttk.Label(button_frame, text="2. Calculate statistics", style="Hint.TLabel").grid(row=0, column=0, padx=5, pady=(5, 0), sticky="w")
        summarize_icon = self.button_icons.get('summarize')
        if summarize_icon:
            self.summarize_btn = tk.Button(button_frame, image=summarize_icon, command=self.load_data, 
                                          padx=2, pady=8, bg='#f0f0f0', relief='raised',
                                          activebackground='#4CAF50')
            self.summarize_btn.image = summarize_icon
        else:
            self.summarize_btn = ttk.Button(button_frame, text="📊", command=self.load_data, width=1)
        self.summarize_btn.grid(row=1, column=0, padx=5, pady=(0, 10), sticky="")
        
        # Batch processing
        ttk.Label(button_frame, text="Batch Processing", style="Hint.TLabel").grid(row=2, column=0, padx=5, pady=(0, 0), sticky="w")
        batch_icon = self.button_icons.get('batch')
        if batch_icon:
            batch_button = tk.Button(button_frame, image=batch_icon,
                  command=self.batch_process_all_elements,
                  padx=2, pady=8, bg="#4CAF50", fg="black", relief='raised',
                  activebackground='#45a049')
            batch_button.image = batch_icon
        else:
            batch_button = tk.Button(button_frame, text="⚡", command=self.batch_process_all_elements, 
                  bg="#4CAF50", fg="black", width=1, height=3)
        batch_button.grid(row=3, column=0, padx=5, pady=(0, 10), sticky="")
        
        # Progress table button
        ttk.Label(button_frame, text="View Progress Table", style="Hint.TLabel").grid(row=4, column=0, padx=5, pady=(0, 0), sticky="w")
        progress_icon = self.button_icons.get('progress')
        if progress_icon:
            progress_btn = tk.Button(button_frame, image=progress_icon, command=self.show_progress_table_window,
                                    padx=2, pady=8, bg='#f0f0f0', relief='raised',
                                    activebackground='#4CAF50')
            progress_btn.image = progress_icon
        else:
            progress_btn = ttk.Button(button_frame, text="📊", command=self.show_progress_table_window, width=1)
        progress_btn.grid(row=5, column=0, padx=5, pady=(0, 10), sticky="")
        
        # Progress Log at bottom of control panel
        log_group = ttk.LabelFrame(left_frame, text="Status Log", padding=5)
        log_group.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        log_frame = ttk.Frame(log_group)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        custom_font = font.Font(family="Arial", size=11, slant="roman")
        self.log = tk.Text(log_frame, height=4, width=30, wrap="word", font=custom_font)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log.yview)
        self.log.configure(yscrollcommand=log_scrollbar.set)
        
        self.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Use PanedWindow to create resizable sections
        paned = ttk.PanedWindow(right_frame, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Section 1: Statistics Table (top)
        stats_section = ttk.Frame(paned)
        paned.add(stats_section, weight=1)
        ttk.Label(stats_section, text="Statistics Table (Current Element):", style="Hint.TLabel").pack(anchor="center", padx=5, pady=(5, 0))
        
        stats_frame = ttk.Frame(stats_section)
        stats_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        
        # Create Treeview for statistics
        stats_columns = ('Sample', '25th Percentile', '50th Percentile', '75th Percentile', '99th Percentile', 'IQR', 'Mean')
        self.stats_table = ttk.Treeview(stats_frame, columns=stats_columns, show='headings', height=6)
        stats_xscroll = ttk.Scrollbar(stats_frame, orient=tk.HORIZONTAL, command=self.stats_table.xview)
        stats_yscroll = ttk.Scrollbar(stats_frame, orient=tk.VERTICAL, command=self.stats_table.yview)
        self.stats_table.configure(xscrollcommand=stats_xscroll.set, yscrollcommand=stats_yscroll.set)
        
        # Configure column headings
        for col in stats_columns:
            self.stats_table.heading(col, text=col)
            self.stats_table.column(col, width=100, anchor='center')
        
        self.stats_table.grid(row=0, column=0, sticky='nsew')
        stats_yscroll.grid(row=0, column=1, sticky='ns')
        stats_xscroll.grid(row=1, column=0, sticky='ew')
        stats_frame.grid_rowconfigure(0, weight=1)
        stats_frame.grid_columnconfigure(0, weight=1)
        
        # Section 2: Progress Table (bottom)
        progress_section = ttk.Frame(paned)
        paned.add(progress_section, weight=1)
        ttk.Label(progress_section, text="Progress Table:", style="Hint.TLabel").pack(anchor="center", padx=5, pady=(5, 0))
        
        progress_frame = ttk.Frame(progress_section)
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        
        # Create Treeview for progress table (embedded version)
        self.progress_table = ttk.Treeview(progress_frame, columns=(), show="headings", height=6)
        progress_xscroll = ttk.Scrollbar(progress_frame, orient=tk.HORIZONTAL, command=self.progress_table.xview)
        progress_yscroll = ttk.Scrollbar(progress_frame, orient=tk.VERTICAL, command=self.progress_table.yview)
        self.progress_table.configure(xscrollcommand=progress_xscroll.set, yscrollcommand=progress_yscroll.set)
        
        self.progress_table.grid(row=0, column=0, sticky='nsew')
        progress_yscroll.grid(row=0, column=1, sticky='ns')
        progress_xscroll.grid(row=1, column=0, sticky='ew')
        progress_frame.grid_rowconfigure(0, weight=1)
        progress_frame.grid_columnconfigure(0, weight=1)
        
        # Configure tag colors for progress table
        self.progress_table.tag_configure("complete", background="#90EE90")
        self.progress_table.tag_configure("partial", background="#FFE4B5")
        self.progress_table.tag_configure("missing", background="#FFB6C1")
        self.progress_table.tag_configure("missing_file", background="#D3D3D3", foreground="#666666")
        
        # Add refresh button for progress table
        refresh_frame = ttk.Frame(progress_section)
        refresh_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        ttk.Button(refresh_frame, text="Refresh Progress Table", command=self.refresh_progress_table).pack(side=tk.RIGHT)
    
    def build_preview_tab(self):
        """Build the Preview & Export tab."""
        # Left side: Controls (fixed width to match Setup tab)
        control_frame = ttk.Frame(self.preview_tab, width=280)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        control_frame.pack_propagate(False)  # Maintain fixed width
        
        # Right side: Preview pane
        preview_frame = ttk.Frame(self.preview_tab)
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Element dropdown at top
        element_group = ttk.Frame(control_frame)
        element_group.pack(pady=5)
        ttk.Label(element_group, text="Element:").pack(side=tk.LEFT, padx=5)
        self.element_dropdown_preview = ttk.Combobox(element_group, textvariable=self.element, state="readonly", width=15)
        self.element_dropdown_preview.pack(side=tk.LEFT, padx=5)
        # Update statistics table when element changes (same trace as in setup tab)
        
        # Layout controls
        layout_frame = ttk.LabelFrame(control_frame, text="Layout", padding=10)
        layout_frame.pack(fill=tk.X, pady=5)
        
        # Scale bar length
        ttk.Label(layout_frame, text="Scale bar length (µm):").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        scale_bar_entry = ttk.Entry(layout_frame, textvariable=self.scale_bar_length_um, width=12)
        scale_bar_entry.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        
        # Rows
        ttk.Label(layout_frame, text="Rows:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
        rows_entry = ttk.Entry(layout_frame, textvariable=self.num_rows, width=12)
        rows_entry.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        
        # Display controls
        display_frame = ttk.LabelFrame(control_frame, text="Display", padding=10)
        display_frame.pack(fill=tk.X, pady=5)
        
        # Color scheme
        ttk.Label(display_frame, text="Color Scheme:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        self.color_scheme_dropdown = ttk.Combobox(display_frame, textvariable=self.color_scheme, values=plt.colormaps(), width=12)
        self.color_scheme_dropdown.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        
        # Scale max
        ttk.Label(display_frame, text="Scale Max:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
        scale_max_entry = ttk.Entry(display_frame, textvariable=self.scale_max, width=12)
        scale_max_entry.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        
        # Log Scale
        ttk.Checkbutton(display_frame, text="Log Scale", variable=self.use_log).grid(row=2, column=0, columnspan=2, pady=2)
        
        # Font controls
        font_frame = ttk.LabelFrame(control_frame, text="Fonts", padding=10)
        font_frame.pack(fill=tk.X, pady=5)
        
        # Sample name font size
        ttk.Label(font_frame, text="Sample Name Font:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
        self.sample_name_font_size_dropdown = ttk.Combobox(font_frame, textvariable=self.sample_name_font_size, values=["n/a", "Small", "Medium", "Large"], width=12)
        self.sample_name_font_size_dropdown.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        
        # Element label font size
        ttk.Label(font_frame, text="Element Label Font:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
        element_font_frame = ttk.Frame(font_frame)
        element_font_frame.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        ttk.Scale(element_font_frame, from_=13, to=72, variable=self.element_label_font_size, orient=tk.HORIZONTAL, length=120).pack(side=tk.LEFT)
        self.element_font_size_label = ttk.Label(element_font_frame, text="16")
        self.element_font_size_label.pack(side=tk.LEFT, padx=(5, 0))
        self.element_label_font_size.trace('w', lambda *args: self.element_font_size_label.config(text=str(self.element_label_font_size.get())))
        
        # Action buttons
        action_frame = ttk.Frame(control_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        # Preview button
        ttk.Label(action_frame, text="3. Preview composite", style="Hint.TLabel").pack(pady=(5, 0))
        preview_icon = self.button_icons.get('preview')
        if preview_icon:
            self.preview_btn = tk.Button(action_frame, image=preview_icon, command=self.preview_composite,
                                        padx=2, pady=8, bg='#f0f0f0', relief='raised',
                                        activebackground='#4CAF50')
            self.preview_btn.image = preview_icon
        else:
            self.preview_btn = ttk.Button(action_frame, text="👁️", command=self.preview_composite, width=1)
        self.preview_btn.pack(pady=(0, 10))
        
        # Add Element Label button
        ttk.Label(action_frame, text="4. Add Element Label (optional)", style="Hint.TLabel").pack(pady=(5, 0))
        add_label_icon = self.button_icons.get('add_label')
        if add_label_icon:
            self.add_label_btn = tk.Button(action_frame, image=add_label_icon, command=self.add_element_label,
                                           padx=2, pady=8, bg='#f0f0f0', relief='raised',
                                           activebackground='#4CAF50')
            self.add_label_btn.image = add_label_icon
        else:
            self.add_label_btn = ttk.Button(action_frame, text="🏷️", command=self.add_element_label, width=1)
        self.add_label_btn.pack(pady=(0, 10))
        
        # Save Composite button
        ttk.Label(action_frame, text="5. Save Composite", style="Hint.TLabel").pack(pady=(5, 0))
        save_icon = self.button_icons.get('save')
        if save_icon:
            self.save_btn = tk.Button(action_frame, image=save_icon, command=self.save_composite,
                                     padx=2, pady=8, bg='#f0f0f0', relief='raised',
                                     activebackground='#4CAF50')
            self.save_btn.image = save_icon
        else:
            self.save_btn = ttk.Button(action_frame, text="💾", command=self.save_composite, width=1)
        self.save_btn.pack(pady=(0, 10))
        
        # Progress Log at bottom of control panel
        log_group_preview = ttk.LabelFrame(control_frame, text="Status Log", padding=5)
        log_group_preview.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        log_frame_preview = ttk.Frame(log_group_preview)
        log_frame_preview.pack(fill=tk.BOTH, expand=True)
        
        custom_font_preview = font.Font(family="Arial", size=11, slant="roman")
        self.log_preview = tk.Text(log_frame_preview, height=4, width=30, wrap="word", font=custom_font_preview)
        log_scrollbar_preview = ttk.Scrollbar(log_frame_preview, orient=tk.VERTICAL, command=self.log_preview.yview)
        self.log_preview.configure(yscrollcommand=log_scrollbar_preview.set)
        
        self.log_preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar_preview.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Preview pane
        self.preview_container = ttk.Frame(preview_frame)
        self.preview_container.pack(fill=tk.BOTH, expand=True)
        
        self.preview_label = ttk.Label(self.preview_container, 
                                      text="\n\nCalculate statistics in the 'Setup & Statistics' tab first,\nthen click 'Preview composite' to generate preview here.\n\n",
                                      font=("Arial", 12), foreground="gray", justify=tk.CENTER)
        self.preview_label.pack(fill=tk.BOTH, expand=True)
        
        # Bind resize event to update the preview image's aspect ratio
        self.preview_container.bind("<Configure>", self.on_resize)

    def load_button_icons(self):
        """Load custom button icons from the icons folder if they exist."""
        icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
        icon_files = {
            'summarize': 'summarize.png',
            'preview': 'preview.png',
            'add_label': 'add_label.png',  # Also check for 'label.png' as fallback
            'save': 'save.png',
            'batch': 'batch.png',
            'progress': 'progress.png'
        }
        
        for key, filename in icon_files.items():
            icon_path = os.path.join(icons_dir, filename)
            # Special case: also check for 'label.png' if 'add_label.png' not found
            if key == 'add_label' and not os.path.exists(icon_path):
                alt_path = os.path.join(icons_dir, 'label.png')
                if os.path.exists(alt_path):
                    icon_path = alt_path
            if os.path.exists(icon_path):
                try:
                    # Load with PIL to handle transparency and resize if needed
                    icon_img = Image.open(icon_path)
                    # Resize to 32x32 (larger icons for better visibility)
                    if icon_img.size[0] > 32 or icon_img.size[1] > 32:
                        icon_img = icon_img.resize((32, 32), Image.LANCZOS)
                    elif icon_img.size[0] < 32 or icon_img.size[1] < 32:
                        # Upscale smaller icons
                        icon_img = icon_img.resize((32, 32), Image.LANCZOS)
                    
                    # Convert to PhotoImage for Tkinter
                    self.button_icons[key] = ImageTk.PhotoImage(icon_img)
                    # Use print since log widget doesn't exist yet
                    print(f"✅ Loaded icon: {filename}")
                except Exception as e:
                    error_msg = f"⚠️ Could not load icon {filename}: {e}"
                    print(error_msg)
                    import traceback
                    traceback.print_exc()
            else:
                # Icon not found - will use Unicode/text fallback
                print(f"ℹ️ Icon not found: {filename} (using Unicode fallback)")

    def select_input_folder(self):
        folder_selected = filedialog.askdirectory(initialdir=self.input_dir or ".", title="Select Input Directory")
        if folder_selected:
            self.input_dir = folder_selected
            self.log_print(f"Input folder updated to: {self.input_dir}")
            self.update_element_dropdown()
            if hasattr(self, 'input_folder_label'):
                self.input_folder_label.config(text=f"Input: {self.input_dir}")
            # Scan and populate progress table
            self.scan_progress_table()

    def select_output_folder(self):
        folder_selected = filedialog.askdirectory(initialdir=self.output_dir, title="Select Output Directory")
        if folder_selected:
            self.output_dir = folder_selected
            self.output_folder_label.config(text=f"Output: {self.output_dir}")
            self.log_print(f"Output folder updated to: {self.output_dir}")
            # Re-check existing progress and update table
            if self.progress_samples:
                self._check_existing_progress()
                # Only update table if widget exists
                if hasattr(self, 'progress_table') and self.progress_table is not None:
                    self.update_progress_table()
        # If user cancels, keep the current output directory (no change)

    def show_progress_table_window(self):
        """Refresh the embedded progress table (now in Setup & Statistics tab)."""
        # Debug: Check if progress_table exists
        if not hasattr(self, 'progress_table') or self.progress_table is None:
            self.log_print("⚠️ Progress table widget not initialized. Please restart the application.")
            return
        
        self.set_status("Busy")
        
        # First scan the input folder to build the progress table structure
        if not self.progress_samples or not self.progress_elements:
            if self.input_dir and os.path.isdir(self.input_dir):
                self.log_print("Status: Busy - Scanning input folder...")
                self.scan_progress_table()
            elif self.output_dir and os.path.isdir(self.output_dir):
                # If no input dir but output dir exists, try to infer from output structure
                self.log_print("Status: Busy - Scanning output folder...")
                self._scan_progress_from_output()
            else:
                self.log_print("⚠️ Please select an input or output folder first to view progress table.")
                self.set_status("Idle")
                return
        
        # Always refresh the status to get latest updates
        self._check_existing_progress()
        self.update_progress_table()
        
        # Debug info
        if self.progress_samples and self.progress_elements:
            self.log_print(f"Status: Idle - Progress table updated: {len(self.progress_samples)} samples, {len(self.progress_elements)} elements")
        else:
            self.log_print("⚠️ No progress data found. Please calculate statistics first.")
        
        self.set_status("Idle")
        
        # Switch to Setup & Statistics tab to show the table
        self.tabs.select(0)  # Index 0 is the Setup & Statistics tab
    
    def refresh_progress_table(self):
        """Refresh the progress table by re-scanning and checking status."""
        if not hasattr(self, 'progress_table') or self.progress_table is None:
            self.log_print("⚠️ Progress table widget not initialized.")
            # Try to initialize if not already done
            if self.input_dir and os.path.isdir(self.input_dir):
                self.scan_progress_table()
            elif self.output_dir and os.path.isdir(self.output_dir):
                self._scan_progress_from_output()
            return
        
        self.set_status("Busy")
        self.log_print("Status: Busy - Refreshing progress table...")
        
        # Re-scan and update
        if self.input_dir and os.path.isdir(self.input_dir):
            self.scan_progress_table()
        elif self.output_dir and os.path.isdir(self.output_dir):
            # If we have progress data, just refresh status
            if self.progress_samples and self.progress_elements:
                self._check_existing_progress()
                self.update_progress_table()
            else:
                # Try to infer from output
                self._scan_progress_from_output()
        else:
            self.log_print("⚠️ No input or output folder set.")
            self.set_status("Idle")
            return
        
        self.set_status("Idle")
        if self.progress_samples and self.progress_elements:
            self.log_print(f"Status: Idle - Progress table refreshed: {len(self.progress_samples)} samples, {len(self.progress_elements)} elements")
        else:
            self.log_print("Status: Idle - No progress data found.")
    
    def scan_progress_table(self):
        """Scan input folder and build initial progress table."""
        if not self.input_dir or not os.path.isdir(self.input_dir):
            return
        
        samples = set()
        elements = set()
        files_found = set()  # Track which sample-element pairs have input files
        
        # Scan for all matrix files (both old format with ppm/CPS and new format without)
        for file in glob.glob(os.path.join(self.input_dir, "* matrix.xlsx")):
            parsed = self.parse_matrix_filename(file)
            if parsed:
                sample, element, _ = parsed
                samples.add(sample)
                elements.add(element)
                files_found.add((sample, element))
        
        # Sort elements (symbol + mass)
        def sort_key(elem):
            m = re.search(r"(\D+)(\d+)$", elem)
            if m:
                return (m.group(1), int(m.group(2)))
            return (elem, 0)
        
        self.progress_samples = sorted(samples)
        self.progress_elements = sorted(elements, key=sort_key)
        
        # Build complete grid: mark files that exist vs missing
        self.progress_data = {}
        for sample in self.progress_samples:
            for element in self.progress_elements:
                if (sample, element) in files_found:
                    self.progress_data[(sample, element)] = None  # File exists, not processed yet
                else:
                    self.progress_data[(sample, element)] = 'missing_file'  # Input file doesn't exist
        
        # Check existing output files to determine initial status
        self._check_existing_progress()
        # Only update table if widget exists
        if hasattr(self, 'progress_table') and self.progress_table is not None:
            self.update_progress_table()
    
    def _scan_progress_from_output(self):
        """Scan output folder to infer progress when input folder is not available."""
        if not self.output_dir or not os.path.isdir(self.output_dir):
            return
        
        samples = set()
        elements = set()
        
        # Scan output directories for element folders
        for item in os.listdir(self.output_dir):
            element_dir = os.path.join(self.output_dir, item)
            if os.path.isdir(element_dir):
                # Check if this looks like an element folder (has composite or histograms)
                composite_path = os.path.join(element_dir, f"{item}_composite.png")
                hist_dir = os.path.join(element_dir, 'Histograms')
                
                if os.path.exists(composite_path) or (os.path.isdir(hist_dir) and os.listdir(hist_dir)):
                    elements.add(item)
                    # Try to find samples from histogram files
                    if os.path.isdir(hist_dir):
                        for hist_file in os.listdir(hist_dir):
                            if hist_file.endswith('_histogram.png'):
                                sample = hist_file.replace('_histogram.png', '')
                                samples.add(sample)
        
        if samples and elements:
            # Sort elements
            def sort_key(elem):
                m = re.search(r"(\D+)(\d+)$", elem)
                if m:
                    return (m.group(1), int(m.group(2)))
                return (elem, 0)
            
            self.progress_samples = sorted(samples)
            self.progress_elements = sorted(elements, key=sort_key)
            
            # Build progress data - all will be checked by _check_existing_progress
            self.progress_data = {}
            for sample in self.progress_samples:
                for element in self.progress_elements:
                    self.progress_data[(sample, element)] = None
            
            self._check_existing_progress()
            # Only update table if widget exists
            if hasattr(self, 'progress_table') and self.progress_table is not None:
                self.update_progress_table()
            self.log_print(f"📊 Inferred progress from output: {len(self.progress_samples)} samples, {len(self.progress_elements)} elements")
    
    def _check_existing_progress(self):
        """Check output folder for existing files to determine progress status."""
        if not self.output_dir or not os.path.isdir(self.output_dir):
            # No output dir means nothing is processed yet - keep all as None
            return
        
        # Group by element to check composites (which are per-element, not per-sample)
        elements_with_composite = set()
        for element in self.progress_elements:
            element_dir = os.path.join(self.output_dir, element)
            if not os.path.isdir(element_dir):
                continue
            composite_path = os.path.join(element_dir, f"{element}_composite.png")
            if os.path.exists(composite_path) and os.path.getsize(composite_path) > 0:
                elements_with_composite.add(element)
                # Progress table will show this information, no need to log
        
        # Update status for each sample-element pair
        for (sample, element), current_status in list(self.progress_data.items()):
            # Don't override 'missing_file' status - file doesn't exist, can't be processed
            if current_status == 'missing_file':
                continue
            
            # If composite exists for this element, all samples are complete
            if element in elements_with_composite:
                self.progress_data[(sample, element)] = 'complete'
            else:
                # Check if histogram exists for this specific sample (indicates partial processing)
                element_dir = os.path.join(self.output_dir, element)
                hist_dir = os.path.join(element_dir, 'Histograms')
                if os.path.isdir(hist_dir):
                    hist_path = os.path.join(hist_dir, f"{sample}_histogram.png")
                    if os.path.exists(hist_path) and os.path.getsize(hist_path) > 0:
                        self.progress_data[(sample, element)] = 'partial'
                    else:
                        # No files found - keep as None (not started, but file exists)
                        self.progress_data[(sample, element)] = None
                else:
                    # No histograms directory - keep as None (not started, but file exists)
                    self.progress_data[(sample, element)] = None
    
    def update_statistics_table(self, stats_df=None):
        """Update the statistics table display with current element's statistics."""
        if not hasattr(self, 'stats_table') or self.stats_table is None:
            return
        
        # Clear existing rows
        for item in self.stats_table.get_children():
            self.stats_table.delete(item)
        
        # If no stats_df provided, try to load from file
        if stats_df is None:
            element = self.element.get()
            if not element:
                return
            
            stats_path = os.path.join(self.output_dir, element, f"{element}_statistics.csv")
            if os.path.exists(stats_path):
                try:
                    stats_df = pd.read_csv(stats_path)
                except Exception as e:
                    self.log_print(f"⚠️ Could not load statistics: {e}")
                    return
            else:
                return
        
        # Populate table
        for _, row in stats_df.iterrows():
            values = (
                str(row.get('Sample', '')),
                f"{row.get('25th Percentile', 0):.2f}",
                f"{row.get('50th Percentile', 0):.2f}",
                f"{row.get('75th Percentile', 0):.2f}",
                f"{row.get('99th Percentile', 0):.2f}",
                f"{row.get('IQR', 0):.2f}",
                f"{row.get('Mean', 0):.2f}"
            )
            self.stats_table.insert('', tk.END, values=values)
    
    def update_progress_table(self):
        """Update the progress table display."""
        if not hasattr(self, 'progress_table') or self.progress_table is None:
            # Widget not initialized yet - this is normal during startup
            # Don't log an error, just return silently
            return
        
        try:
            # Clear existing - handle case where columns might be empty
            current_columns = self.progress_table["columns"]
            if current_columns:
                for col in current_columns:
                    try:
                        self.progress_table.heading(col, text="")
                    except:
                        pass
            # Clear all rows
            for item in self.progress_table.get_children():
                try:
                    self.progress_table.delete(item)
                except:
                    pass
        except Exception as e:
            try:
                self.log_print(f"⚠️ Error clearing progress table: {e}")
                import traceback
                self.log_print(traceback.format_exc())
            except:
                pass
            return
        
        if not self.progress_elements:
            # Add a message row if no elements
            try:
                # Configure a single column for the message
                self.progress_table.configure(columns=("message",))
                self.progress_table.heading("message", text="")
                self.progress_table.column("message", width=400)
                self.progress_table.insert('', tk.END, values=["No elements found. Please calculate statistics first."])
            except Exception as e:
                try:
                    self.log_print(f"⚠️ Error adding message to progress table: {e}")
                except:
                    pass
            return
        
        if not self.progress_samples:
            # Add a message row if no samples
            try:
                # Configure a single column for the message
                self.progress_table.configure(columns=("message",))
                self.progress_table.heading("message", text="")
                self.progress_table.column("message", width=400)
                self.progress_table.insert('', tk.END, values=["No samples found. Please calculate statistics first."])
            except Exception as e:
                try:
                    self.log_print(f"⚠️ Error adding message to progress table: {e}")
                except:
                    pass
            return
        
        # Set up columns
        all_cols = ["Sample"] + self.progress_elements
        self.progress_table.configure(columns=all_cols)
        
        for col in all_cols:
            self.progress_table.heading(col, text=col)
            if col == "Sample":
                # Auto-size sample column based on longest sample name
                max_sample_len = max([len(s) for s in self.progress_samples] + [6])  # "Sample" header
                self.progress_table.column(col, width=min(max_sample_len * 8 + 20, 200), anchor="w", minwidth=80)
            else:
                # Element columns - just wide enough for checkmark or element name
                self.progress_table.column(col, width=50, anchor="center", minwidth=40)
        
        # Add rows
        for sample in self.progress_samples:
            values = [sample]
            cell_statuses = []
            for element in self.progress_elements:
                status = self.progress_data.get((sample, element))
                if status == 'complete':
                    values.append("✓")
                    cell_statuses.append('complete')
                elif status == 'partial':
                    values.append("~")
                    cell_statuses.append('partial')
                elif status == 'missing_file':
                    values.append("X")
                    cell_statuses.append('missing_file')
                else:
                    values.append("")
                    cell_statuses.append('missing')
            
            # Determine row color based on status distribution
            # Only mark row as complete if ALL elements are complete (and no missing files)
            # Mark as partial if any are partial or complete (but not all complete)
            # Mark as missing only if all are missing or missing_file
            if all(s == 'complete' for s in cell_statuses):
                row_tag = "complete"
            elif any(s == 'complete' for s in cell_statuses) or any(s == 'partial' for s in cell_statuses):
                row_tag = "partial"
            elif all(s in ('missing', 'missing_file') for s in cell_statuses):
                row_tag = "missing"
            else:
                row_tag = "missing"  # Default
            
            self.progress_table.insert("", tk.END, values=values, tags=(row_tag,))
            
            # Apply per-cell tags for missing_file cells (ttk.Treeview limitation - we'll use row tag for now)
            # Note: Individual cell coloring would require custom drawing, so missing_file cells
            # will show "X" but use row-level coloring
    
    def update_sample_element_progress(self, sample, element, status='complete'):
        """Update progress for a specific sample-element pair."""
        if (sample, element) in self.progress_data:
            # Don't override 'missing_file' status - can't process what doesn't exist
            if self.progress_data[(sample, element)] == 'missing_file':
                return
            self.progress_data[(sample, element)] = status
            # Only update table if window is open
            if self.progress_table and self.progress_table_window and self.progress_table_window.winfo_exists():
                self.update_progress_table()
    
    def check_sample_element_status(self, sample, element):
        """Check the current status of a sample-element pair based on output files."""
        if not self.output_dir:
            return None
        
        element_dir = os.path.join(self.output_dir, element)
        # Check if composite exists (complete)
        composite_path = os.path.join(element_dir, f"{element}_composite.png")
        if os.path.exists(composite_path):
            return 'complete'
        
        # Check if histogram exists (partial)
        hist_path = os.path.join(element_dir, 'Histograms', f"{sample}_histogram.png")
        if os.path.exists(hist_path):
            return 'partial'
        
        return None

    def batch_process_all_elements(self):
        """Process all elements found in the input folder automatically."""
        if not self.input_dir:
            messagebox.showerror("Error", "Please select an input folder first.")
            return
        
        # Only prompt for output folder if not already selected
        if not self.output_dir or not os.path.isdir(self.output_dir):
            self.select_output_folder()
            if not self.output_dir or not os.path.isdir(self.output_dir):
                return  # User cancelled
        
        # Get all elements from input folder
        elements = set()
        for file in glob.glob(os.path.join(self.input_dir, "* matrix.xlsx")):
            parsed = self.parse_matrix_filename(file)
            if parsed:
                _, element, _ = parsed
                elements.add(element)
        
        if not elements:
            messagebox.showwarning("No Elements", "No element files found in the input folder.")
            return
        
        # Sort elements
        def sort_key(elem):
            m = re.search(r"(\D+)(\d+)$", elem)
            if m:
                return (m.group(1), int(m.group(2)))
            return (elem, 0)
        
        sorted_elements = sorted(elements, key=sort_key)
        
        # Ask for confirmation
        num_elements = len(sorted_elements)
        result = messagebox.askyesno(
            "Batch Process Confirmation",
            f"This will process {num_elements} element(s):\n\n" +
            ", ".join(sorted_elements) +
            "\n\nEach element will:\n" +
            "1. Load data and generate histograms/statistics\n" +
            "2. Use the suggested 99th percentile as scale max\n" +
            "3. Generate and save the composite\n\n" +
            "This may take a while. Continue?"
        )
        
        if not result:
            return
        
        # Process each element
        self.log_print(f"\n🚀 Starting batch processing of {num_elements} element(s)...")
        successful = 0
        failed = []
        
        for idx, elem in enumerate(sorted_elements, 1):
            try:
                self.log_print(f"\n[{idx}/{num_elements}] Processing {elem}...")
                
                # Set the element
                self.element.set(elem)
                self.master.update_idletasks()  # Update GUI
                
                # Load data (this sets scale_max automatically to 99th percentile)
                self.load_data()
                
                # Check if data was loaded successfully
                if not self.matrices:
                    self.log_print(f"⚠️  No data loaded for {elem}, skipping...")
                    failed.append((elem, "No data found"))
                    continue
                
                # Generate and save composite directly (no preview)
                self.log_print(f"  Generating composite for {elem}...")
                self.generate_composite(preview=False)
                
                successful += 1
                self.log_print(f"✅ Completed {elem} ({idx}/{num_elements})")
                
                # Update GUI to show progress
                self.master.update_idletasks()
                
            except Exception as e:
                error_msg = str(e)
                self.log_print(f"❌ Error processing {elem}: {error_msg}")
                failed.append((elem, error_msg))
                import traceback
                self.log_print(traceback.format_exc())
                continue
        
        # Summary
        self.log_print(f"\n{'='*50}")
        self.log_print(f"Batch processing complete!")
        self.log_print(f"✅ Successful: {successful}/{num_elements}")
        if failed:
            self.log_print(f"❌ Failed: {len(failed)}")
            for elem, reason in failed:
                self.log_print(f"   - {elem}: {reason}")
        self.log_print(f"{'='*50}")
        
        # Show completion message
        if failed:
            messagebox.showwarning(
                "Batch Processing Complete",
                f"Processed {successful}/{num_elements} elements successfully.\n\n"
                f"{len(failed)} element(s) failed. Check the log for details."
            )
        else:
            messagebox.showinfo(
                "Batch Processing Complete",
                f"Successfully processed all {num_elements} element(s)!"
            )

    def update_element_dropdown(self):
        elements = set()
        for file in glob.glob(os.path.join(self.input_dir, "* matrix.xlsx")):
            parsed = self.parse_matrix_filename(file)
            if parsed:
                _, element, _ = parsed
                elements.add(element)
        
        if elements:
            element_list = sorted(list(elements))
            # Update both dropdowns if they exist
            if hasattr(self, 'element_dropdown'):
                self.element_dropdown['values'] = element_list
                self.element_dropdown['state'] = 'readonly'
            if hasattr(self, 'element_dropdown_preview'):
                self.element_dropdown_preview['values'] = element_list
                self.element_dropdown_preview['state'] = 'readonly'
            # Set the first element as default if no element is currently selected
            if not self.element.get() or self.element.get() not in element_list:
                self.element.set(next(iter(elements)))
        else:
            self.log_print("No valid element files found in the selected directory.")

    def on_resize(self, event):
        """Handle resize events for preview container (legacy - preview now in separate window)."""
        # Only update if preview_image exists and we're still using main window preview
        if hasattr(self, 'preview_image') and self.preview_image is not None:
            # Only update if the resize is significant enough to avoid excessive updates
            if hasattr(self, '_last_resize_time'):
                current_time = time.time()
                if current_time - self._last_resize_time < 0.1:  # Throttle to max 10 updates per second
                    return
                self._last_resize_time = current_time
            else:
                self._last_resize_time = time.time()
            
            self.update_preview_image()

    def log_print(self, message, status_only=False):
        """Print message to log. If status_only=True, only show status-related messages."""
        # Helper function to write to a log widget
        def write_to_log(log_widget):
            if log_widget:
                if status_only:
                    # Only log status changes and important messages
                    if any(keyword in message.lower() for keyword in ['status', 'idle', 'busy', 'finishing', 'complete', 'error', 'warning', '⚠️', '✅', '❌']):
                        log_widget.insert(tk.END, message + "\n")
                        log_widget.see(tk.END)
                else:
                    # Show all messages for now, but we'll filter specific ones
                    # Skip verbose debug and progress messages
                    skip_keywords = ['found composite', 'skipping subplot', 'debug:', 'figure created', 'grid layout']
                    if not any(keyword in message.lower() for keyword in skip_keywords):
                        log_widget.insert(tk.END, message + "\n")
                        log_widget.see(tk.END)
        
        # Write to both log widgets (main log and preview tab log)
        write_to_log(self.log if hasattr(self, 'log') else None)
        write_to_log(self.log_preview if hasattr(self, 'log_preview') else None)
        
        # Update GUI in real-time for better user feedback
        self.master.update_idletasks()
    
    def set_status(self, status):
        """Set the application status (Idle, Busy, Finishing)."""
        self.status = status
        self.log_print(f"Status: {status}", status_only=True)

    def load_matrix_2d(self, path):
        """Load a 2D matrix from an Excel file, with error handling for Dropbox sync issues."""
        try:
            wb = load_workbook(filename=path, read_only=True, data_only=True)
            ws = wb.active
            return np.array([[cell if isinstance(cell, (int, float)) and cell >= 0 else np.nan for cell in row] for row in ws.iter_rows(values_only=True)])
        except KeyError as e:
            # This often happens with Dropbox placeholder files that aren't fully synced
            error_msg = str(e)
            if "Content_Types" in error_msg or "archive" in error_msg.lower():
                raise FileNotFoundError(
                    f"File appears to be incomplete or not fully synced (Dropbox placeholder?): {os.path.basename(path)}\n"
                    f"Please ensure the file is fully downloaded before loading."
                )
            else:
                raise
        except Exception as e:
            # Re-raise with more context
            raise Exception(f"Error loading file {os.path.basename(path)}: {str(e)}")

    def downsample_matrix(self, matrix, target_max=512):
        """Downsample matrix for faster preview rendering."""
        h, w = matrix.shape
        scale = max(h, w) / target_max
        if scale <= 1:
            return matrix
        
        # Calculate downsampling factors
        sh = max(1, int(scale))
        sw = max(1, int(scale))
        
        # Ensure dimensions are divisible by downsampling factors
        new_h = (h // sh) * sh
        new_w = (w // sw) * sw
        
        # Crop to divisible dimensions
        cropped = matrix[:new_h, :new_w]
        
        # Reshape and average
        reshaped = cropped.reshape(new_h//sh, sh, new_w//sw, sw)
        downsampled = reshaped.mean(axis=(1, 3))
        
        return downsampled

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
        for file in glob.glob(os.path.join(self.input_dir, "* matrix.xlsx")):
            parsed = self.parse_matrix_filename(file)
            if parsed:
                sample, _, _ = parsed
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
        # Only prompt for output folder if not already selected
        if not self.output_dir or not os.path.isdir(self.output_dir):
            self.select_output_folder()

        self.set_status("Busy")
        self.log_print("Status: Busy - Calculating statistics...")
        element = self.element.get()
        # Search for files with old format (ppm/CPS) and new format (raw, no unit)
        pattern_ppm = os.path.join(self.input_dir, f"* {element}_ppm matrix.xlsx")
        pattern_CPS = os.path.join(self.input_dir, f"* {element}_CPS matrix.xlsx")
        pattern_raw = os.path.join(self.input_dir, f"* {element} matrix.xlsx")
        files = sorted(glob.glob(pattern_ppm) + glob.glob(pattern_CPS) + glob.glob(pattern_raw))
        # Remove duplicates (in case a file matches multiple patterns)
        files = list(dict.fromkeys(files))

        if not files:
            messagebox.showerror("Error", f"No files found for element {element}")
            return

        # Check for existing statistics.csv to enable incremental processing
        stats_path = os.path.join(self.output_dir, element, f"{element}_statistics.csv")
        existing_stats_df = None
        existing_samples = set()
        
        if os.path.exists(stats_path):
            try:
                existing_stats_df = pd.read_csv(stats_path)
                if 'Sample' in existing_stats_df.columns:
                    existing_samples = set(existing_stats_df['Sample'].tolist())
                    # Progress table will show this information
            except Exception as e:
                self.log_print(f"⚠️ Could not read existing statistics: {e}")

        self.matrices = []
        self.labels = []
        self.pixel_sizes_by_sample = {}
        percentiles = []
        iqrs = []
        means = []
        new_samples = []  # Track which samples are new

        # If using custom pixel sizes, only load data for samples present in the custom file
        samples_to_load = set(self.custom_pixel_sizes.keys()) if self.use_custom_pixel_sizes.get() else None

        for f in files:
            parsed = self.parse_matrix_filename(f)
            if parsed:
                sample, parsed_element, _ = parsed
                # Verify the element matches (safety check)
                if parsed_element != element:
                    continue
                if samples_to_load is None or sample in samples_to_load:
                    # Check if this sample is new
                    is_new = sample not in existing_samples
                    
                    try:
                        matrix = self.load_matrix_2d(f)
                        self.labels.append(sample)
                        self.matrices.append(matrix)
                    except (FileNotFoundError, Exception) as e:
                        # Handle Dropbox sync issues or other file loading errors
                        error_msg = str(e)
                        self.log_print(f"❌ Failed to load {sample}: {error_msg}")
                        # Continue processing other files instead of stopping
                        continue
                    
                    # Get the pixel size for this sample
                    if self.use_custom_pixel_sizes.get() and sample in self.custom_pixel_sizes:
                        pixel_size = self.custom_pixel_sizes[sample]
                    else:
                        pixel_size = self.pixel_size.get()

                    self.pixel_sizes_by_sample[sample] = pixel_size

                    # Only process statistics and histograms for new samples
                    if is_new:
                        new_samples.append(sample)
                        
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
                        hist_path = os.path.join(self.output_dir, element, 'Histograms', f"{sample}_histogram.png")
                        os.makedirs(os.path.dirname(hist_path), exist_ok=True)
                        plt.savefig(hist_path)
                        plt.close()
                        
                        # Update progress table for this sample
                        if hasattr(self, 'progress_table') and self.progress_table:
                            self.update_sample_element_progress(sample, element, 'partial')
                            self.update_progress_table()

        # Merge new statistics with existing ones
        if existing_stats_df is not None and new_samples:
            # Create new statistics DataFrame
            new_percentiles_df = pd.DataFrame(percentiles, columns=['Sample', '25th Percentile', '50th Percentile', '75th Percentile', '99th Percentile'])
            new_iqr_df = pd.DataFrame(iqrs, columns=['Sample', 'IQR'])
            new_mean_df = pd.DataFrame(means, columns=['Sample', 'Mean'])
            new_stats_df = new_percentiles_df.merge(new_iqr_df, on='Sample').merge(new_mean_df, on='Sample')
            
            # Combine with existing
            stats_df = pd.concat([existing_stats_df, new_stats_df], ignore_index=True)
        elif existing_stats_df is not None:
            # No new samples, use existing
            stats_df = existing_stats_df
        else:
            # No existing stats, create new
            percentiles_df = pd.DataFrame(percentiles, columns=['Sample', '25th Percentile', '50th Percentile', '75th Percentile', '99th Percentile'])
            iqr_df = pd.DataFrame(iqrs, columns=['Sample', 'IQR'])
            mean_df = pd.DataFrame(means, columns=['Sample', 'Mean'])
            stats_df = percentiles_df.merge(iqr_df, on='Sample').merge(mean_df, on='Sample')

        # Round statistics and save
        stats_df = stats_df.map(lambda x: float(f"{x:.5g}") if isinstance(x, (int, float)) else x)
        os.makedirs(os.path.dirname(stats_path), exist_ok=True)
        stats_df.to_csv(stats_path, index=False)
        
        # Update statistics table display
        self.update_statistics_table(stats_df)
        
        # Update progress table
        if hasattr(self, 'progress_table') and self.progress_table:
            self._check_existing_progress()
            self.update_progress_table()
        
        self.set_status("Idle")
        self.log_print("Status: Idle - Statistics calculation complete.")

        # Set scale_max based on 99th percentile of ALL data (existing + new)
        overall_99th = np.nanpercentile(np.hstack([m.flatten() for m in self.matrices]), 99)
        self.scale_max.set(round(overall_99th,3))
        self.log_print(f"Scale max set to {self.scale_max.get():.2f} based on overall 99th percentile (all {len(self.matrices)} sample(s))")
        
        # Progress table will show this information - no need to log
        
        # Update progress table - mark as partial (histograms and stats done)
        element = self.element.get()
        for sample in self.labels:
            self.update_sample_element_progress(sample, element, 'partial')
        
        # Update progress table display
        if hasattr(self, 'progress_table') and self.progress_table:
            self._check_existing_progress()
            self.update_progress_table()

    def show_preview_window(self):
        """Display the preview image in a separate window."""
        if not hasattr(self, 'preview_image') or self.preview_image is None:
            return
        
        # Close existing preview window if open
        if self.preview_window is not None and self.preview_window.winfo_exists():
            self.preview_window.destroy()
        
        # Create new preview window
        self.preview_window = tk.Toplevel(self.master)
        element = self.element.get()
        self.preview_window.title(f"Composite Preview - {element}")
        
        # Make window resizable
        self.preview_window.resizable(True, True)
        
        # Get image dimensions
        img_width, img_height = self.preview_image.size
        
        # Set window size to fit image (with some padding), but cap at screen size
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        
        # Scale down if image is larger than 90% of screen
        max_width = int(screen_width * 0.9)
        max_height = int(screen_height * 0.9)
        
        if img_width > max_width or img_height > max_height:
            # Calculate scaling factor
            scale_w = max_width / img_width
            scale_h = max_height / img_height
            scale = min(scale_w, scale_h)
            display_width = int(img_width * scale)
            display_height = int(img_height * scale)
        else:
            display_width = img_width
            display_height = img_height
        
        # Set window geometry (add padding for window chrome and control panel)
        control_panel_height = 100  # Space for controls at bottom
        window_width = display_width + 20
        window_height = display_height + 40 + control_panel_height
        
        # Set minimum size to ensure controls are always visible
        self.preview_window.minsize(400, 300)
        
        # Set initial geometry
        self.preview_window.geometry(f"{window_width}x{window_height}")
        
        # Center the window on screen
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.preview_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Create frame for the image
        preview_frame = tk.Frame(self.preview_window)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create label to display image (store reference for updates)
        # Start with empty label, will be populated after window is laid out
        self.preview_window_label = tk.Label(preview_frame)
        self.preview_window_label.pack(fill=tk.BOTH, expand=True)
        
        # Add info label
        info_label = tk.Label(preview_frame, 
                             text=f"{element} Composite - {img_width}x{img_height} pixels",
                             font=("Arial", 9), foreground="gray")
        info_label.pack(pady=(5, 0))
        
        # Create minimal control panel at bottom
        control_panel = tk.Frame(self.preview_window, bg='#f0f0f0', relief=tk.RAISED, borderwidth=1)
        control_panel.pack(fill=tk.X, side=tk.BOTTOM, padx=0, pady=0)
        
        # Left side: Font size control
        font_frame = tk.Frame(control_panel, bg='#f0f0f0')
        font_frame.pack(side=tk.LEFT, padx=10, pady=8)
        tk.Label(font_frame, text="Label Font:", font=("Arial", 10), bg='#f0f0f0').pack(side=tk.LEFT, padx=(0, 5))
        font_scale = tk.Scale(font_frame, from_=13, to=72, variable=self.element_label_font_size, 
                             orient=tk.HORIZONTAL, length=100, font=("Arial", 9))
        font_scale.pack(side=tk.LEFT)
        font_value_label = tk.Label(font_frame, text=str(self.element_label_font_size.get()), 
                                   font=("Arial", 9), bg='#f0f0f0', width=3)
        font_value_label.pack(side=tk.LEFT, padx=(5, 0))
        # Update label when slider changes
        self.element_label_font_size.trace('w', lambda *args: font_value_label.config(text=str(self.element_label_font_size.get())))
        
        # Right side: Icon buttons
        button_frame = tk.Frame(control_panel, bg='#f0f0f0')
        button_frame.pack(side=tk.RIGHT, padx=10, pady=8)
        
        # Add Element Label button with icon
        add_label_icon = self.button_icons.get('add_label')
        if add_label_icon:
            add_label_btn = tk.Button(button_frame, image=add_label_icon, 
                                    command=self.add_element_label,
                                    padx=2, pady=8, bg='#f0f0f0', relief='raised',
                                    activebackground='#4CAF50')
            add_label_btn.image = add_label_icon  # Keep reference
        else:
            add_label_btn = tk.Button(button_frame, text="🏷️", 
                                    command=self.add_element_label,
                                    padx=2, pady=8, bg='#f0f0f0', relief='raised')
        add_label_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Save Composite button with icon
        save_icon = self.button_icons.get('save')
        if save_icon:
            save_btn = tk.Button(button_frame, image=save_icon, 
                               command=self.save_composite,
                               padx=2, pady=8, bg="#4CAF50", fg="black", relief='raised',
                               activebackground='#45a049')
            save_btn.image = save_icon  # Keep reference
        else:
            save_btn = tk.Button(button_frame, text="💾", 
                                command=self.save_composite,
                                padx=2, pady=8, bg="#4CAF50", fg="black", relief='raised')
        save_btn.pack(side=tk.LEFT)
        
        # Handle window close
        self.preview_window.protocol("WM_DELETE_WINDOW", self._close_preview_window)
        
        # Bind resize event to update image size
        self.preview_window.bind("<Configure>", self._on_preview_window_resize)
        
        # Force window update and then set initial image size after layout is complete
        self.preview_window.update_idletasks()
        self.preview_window.after(10, self._update_preview_window_image)
    
    def _on_preview_window_resize(self, event):
        """Handle resize events for the preview window."""
        # Only update if this is the preview window being resized (not other widgets)
        if event.widget != self.preview_window:
            return
        
        # Throttle resize updates to avoid excessive redraws
        if not hasattr(self, '_preview_resize_time'):
            self._preview_resize_time = time.time()
        
        current_time = time.time()
        if current_time - self._preview_resize_time < 0.1:  # Max 10 updates per second
            return
        self._preview_resize_time = current_time
        
        # Update the image to fit the new window size
        self._update_preview_window_image()
    
    def _update_preview_window_image(self):
        """Update the image displayed in the preview window without recreating the window."""
        if not hasattr(self, 'preview_window_label') or self.preview_window_label is None:
            return
        
        if not hasattr(self, 'preview_image') or self.preview_image is None:
            return
        
        # Get available space from the preview frame (parent of the label)
        if hasattr(self, 'preview_window') and self.preview_window.winfo_exists():
            # Get the frame that contains the label
            preview_frame = self.preview_window_label.master
            # Force update to get accurate dimensions
            preview_frame.update_idletasks()
            frame_width = preview_frame.winfo_width()
            frame_height = preview_frame.winfo_height()
            
            # Account for padding (10px on each side) and info label space (~30px)
            available_width = max(100, frame_width - 20)  # Subtract padding
            available_height = max(100, frame_height - 50)  # Subtract padding and info label space
        else:
            available_width = 400
            available_height = 300
        
        # Get original image dimensions
        img_width, img_height = self.preview_image.size
        
        # Calculate aspect ratios
        img_aspect = img_width / img_height
        available_aspect = available_width / available_height
        
        # Resize to fit available space while maintaining aspect ratio
        if available_aspect > img_aspect:
            # Available space is wider - fit to height
            display_height = available_height
            display_width = int(display_height * img_aspect)
        else:
            # Available space is taller - fit to width
            display_width = available_width
            display_height = int(display_width / img_aspect)
        
        # Ensure minimum size
        display_width = max(100, display_width)
        display_height = max(100, display_height)
        
        # Resize and update image
        display_image = self.preview_image.resize((display_width, display_height), Image.LANCZOS)
        tk_image = ImageTk.PhotoImage(display_image)
        self.preview_window_label.config(image=tk_image)
        self.preview_window_label.image = tk_image  # Keep reference
    
    def _close_preview_window(self):
        """Close the preview window."""
        if self.preview_window:
            self.preview_window.destroy()
            self.preview_window = None
            self.preview_window_label = None
    
    def preview_composite(self):
        try:
            self.generate_composite(preview=True)
            # Track which element was last previewed for safety validation
            self._last_previewed_element = self.element.get()
            self.set_status("Idle")
            self.log_print("Status: Idle - Preview generated.")
        except Exception as e:
            self.set_status("Idle")
            self.log_print(f"❌ Error generating preview: {e}")

    def save_composite(self):
        self.set_status("Busy")
        self.log_print("Status: Busy - Saving composite...")
        if self.preview_file:
            # Additional safety: Warn user if they're saving a preview that might be from a different element
            if not hasattr(self, '_last_previewed_element') or self._last_previewed_element != self.element.get():
                result = messagebox.askyesno("Potential Misidentification Warning", 
                    f"Warning: The preview image may be from a different element than the currently selected '{self.element.get()}'. "
                    f"Do you want to proceed with saving? (It's recommended to generate a new preview first.)")
                if not result:
                    self.log_print("Save cancelled by user due to potential misidentification.")
                    return
            
            out_path = os.path.join(self.output_dir, self.element.get(), f"{self.element.get()}_composite.png")
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            
            # Save the modified preview image (which includes element labels if added)
            if hasattr(self, 'preview_image'):
                self.preview_image.save(out_path, dpi=(300, 300))
            else:
                # Fallback to moving the original file if preview_image is not available
                shutil.move(self.preview_file, out_path)
            
            # Clean up the temporary file
            if os.path.exists(self.preview_file):
                os.remove(self.preview_file)
            self.preview_file = None
            
            # Update progress table - mark as complete
            element = self.element.get()
            for sample in self.labels:
                self.update_sample_element_progress(sample, element, 'complete')
            
            # Update progress table display
            if hasattr(self, 'progress_table') and self.progress_table:
                self._check_existing_progress()
                self.update_progress_table()
            
            self.set_status("Idle")
            self.log_print("Status: Idle - Composite saved.")
        else:
            self.generate_composite(preview=False)

    def generate_composite(self, preview=False):
        if not self.matrices:
            self.log_print("⚠️ No data loaded.")
            return

        self.set_status("Busy")
        if preview:
            self.log_print("Status: Busy - Generating preview...")
        else:
            self.log_print("Status: Busy - Generating composite...")

        # Auto-downsample when many samples (both preview and save)
        use_downsampling = len(self.matrices) > 10
        if use_downsampling:
            downsampled_matrices = [self.downsample_matrix(matrix) for matrix in self.matrices]
            matrices_to_use = downsampled_matrices
        else:
            matrices_to_use = self.matrices

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

        percentiles = []
        iqrs = []
        means = []

        im = None

        for i, (matrix, label) in enumerate(zip(matrices_to_use, self.labels)):
            if preview:
                self.log_print(f"   📊 Generating subplot {i+1}/{len(self.labels)}: {label}")
            r, c = i // cols, i % cols
            ax = axs[r, c] if rows > 1 else axs[c]

            # Get the pixel size for this sample
            pixel_size = self.pixel_sizes_by_sample.get(label, self.pixel_size.get())

            # Determine font size based on selection
            font_size = None
            if self.sample_name_font_size.get() == "Small":
                font_size = 8
            elif self.sample_name_font_size.get() == "Medium":
                font_size = 12
            elif self.sample_name_font_size.get() == "Large":
                font_size = 16

            im = ax.imshow(matrix, cmap=cmap, norm=norm, aspect='equal')
            ax.set_aspect('equal')
            ax.set_title(f"{label}", color=text_color, fontsize=font_size)
            if self.use_custom_pixel_sizes.get():
                pixel_label = f"{int(round(pixel_size))} µm/px"
                subtitle_size = (font_size - 2) if font_size else 9
                subtitle_size = max(subtitle_size, 8)
                ax.text(
                    0.5,
                    -0.08,
                    pixel_label,
                    transform=ax.transAxes,
                    ha='center',
                    va='top',
                    color=text_color,
                    fontsize=subtitle_size
                )
            ax.axis('off')
            ax.set_facecolor(bg_color)

            # Save individual subplot (only if it doesn't exist - incremental processing)
            subplot_path = os.path.join(self.output_dir, self.element.get(), 'subplots', f"{label}.png")
            os.makedirs(os.path.dirname(subplot_path), exist_ok=True)
            
            if not os.path.exists(subplot_path) or os.path.getsize(subplot_path) == 0:
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
                if preview:
                    # Subplot generated - progress table will show status
                    pass
            else:
                # Skipping - progress table will show status
                pass

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
        # Set color for scientific notation offset label (e.g., "1e7")
        offset_text = cbar.ax.yaxis.get_offset_text()
        if offset_text:
            offset_text.set_color(text_color)

        # Add scale bar using a representative pixel size
        if self.use_custom_pixel_sizes.get() and self.labels:
            reference_label = self.labels[0]
            pixel_size_um = self.pixel_sizes_by_sample.get(reference_label, self.pixel_size.get())
            scale_bar_caption = f"{reference_label}: {pixel_size_um:.2f} µm/px"
        else:
            reference_label = None
            pixel_size_um = self.pixel_size.get()
            scale_bar_caption = None

        scale_bar_um = self.scale_bar_length_um.get()  # e.g., 500

        
        # Convert to pixels
        if pixel_size_um <= 0:
            scale_bar_px = 0
        else:
            scale_bar_px = max(1, int(round(scale_bar_um / pixel_size_um)))

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
        label_lines = [f"{scale_bar_um:.0f} µm"]
        if scale_bar_caption:
            label_lines.append(scale_bar_caption)
        scale_ax.text(
            (x_start + x_end) / 2,
            y_pos + 4,  # tighter vertical gap
            "\n".join(label_lines),
            color='white',
            fontsize=8,
            ha='center',
            va='bottom'
        )
        
        # Set background color for all axes
        for ax in np.atleast_1d(axs).flat:
            ax.set_facecolor(bg_color)
            ax.axis('off')
        
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
        # Set color for scientific notation offset label (e.g., "1e7")
        export_offset_text = export_cbar.ax.yaxis.get_offset_text()
        if export_offset_text:
            export_offset_text.set_color(text_color)

        # Save
        colorbar_path = os.path.join(self.output_dir, self.element.get(), f"{self.element.get()}_colorbar.png")
        colorbar_fig.savefig(colorbar_path, dpi=300, bbox_inches='tight', transparent=True)
        plt.close(colorbar_fig)
        
        if preview:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                plt.savefig(tmp_file.name, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
            plt.close(fig)
            
            self.preview_image = Image.open(tmp_file.name)
            # Store the original unlabeled image
            self.original_preview_image = self.preview_image.copy()
            
            # Store the temp file path
            self.preview_file = tmp_file.name
            
            # Update preview in the Preview tab
            self.update_preview_image()
            
            # Switch to Preview tab to show the preview
            self.tabs.select(1)  # Index 1 is the Preview & Export tab
        else:
            out_path = os.path.join(self.output_dir, self.element.get(), f"{self.element.get()}_composite.png")
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
            plt.close(fig)
            
            # Update progress table - mark as complete
            element = self.element.get()
            for sample in self.labels:
                self.update_sample_element_progress(sample, element, 'complete')
            
            # Update progress table display
            if hasattr(self, 'progress_table') and self.progress_table:
                self._check_existing_progress()
                self.update_progress_table()

            # Save percentiles, IQR, and mean table
            percentiles_df = pd.DataFrame(percentiles, columns=['Sample', '25th Percentile', '50th Percentile', '75th Percentile', '99th Percentile'])
            iqr_df = pd.DataFrame(iqrs, columns=['Sample', 'IQR'])
            mean_df = pd.DataFrame(means, columns=['Sample', 'Mean'])
            stats_df = percentiles_df.merge(iqr_df, on='Sample').merge(mean_df, on='Sample')
            stats_path = os.path.join(self.output_dir, self.element.get(), f"{self.element.get()}_statistics.csv")
            stats_df.to_csv(stats_path, index=False)
            
            # Update statistics table display
            self.update_statistics_table(stats_df)
            
            self.set_status("Idle")
            self.log_print("Status: Idle - Composite saved.")

    def update_preview_image(self):
        """Update preview image in the Preview tab."""
        if not hasattr(self, 'preview_image') or self.preview_image is None:
            return
        
        # Force update to get accurate dimensions
        self.master.update_idletasks()
        self.preview_container.update_idletasks()
        
        container_width = self.preview_container.winfo_width()
        container_height = self.preview_container.winfo_height()
        
        # Handle zero or very small dimensions - use minimum sizes
        if container_width <= 10 or container_height <= 10:
            # Get window dimensions as fallback
            window_width = self.master.winfo_width()
            window_height = self.master.winfo_height()
            
            if window_width > 0 and window_height > 0:
                # Use most of the window space for preview, with minimums
                container_width = max(400, window_width - 250)  # Space for control panel
                container_height = max(300, window_height - 100)  # Space for window chrome
            else:
                # Default fallback dimensions - ensure minimum size
                container_width = max(400, 800)
                container_height = max(300, 600)
            
            # Force container to maintain minimum size
            self.preview_container.configure(width=max(400, container_width), height=max(300, container_height))
            
            # If we had to use fallback, schedule a retry to get proper dimensions
            if container_width == 800 and container_height == 600:
                self.master.after(100, self.update_preview_image)
                return
        
        img_width, img_height = self.preview_image.size
        
        # Basic safety check for image dimensions
        if img_width <= 0 or img_height <= 0:
            self.log_print(f"⚠️ Invalid image dimensions: {img_width}x{img_height}")
            return
        
        # Calculate aspect ratios
        img_aspect = img_width / img_height
        container_aspect = container_width / container_height
        
        # Resize to fit container while maintaining aspect ratio
        if container_aspect > img_aspect:
            # Container is wider - fit to height
            new_height = container_height
            new_width = int(new_height * img_aspect)
        else:
            # Container is taller - fit to width
            new_width = container_width
            new_height = int(new_width / img_aspect)
        
        # Ensure minimum size
        if new_width < 10 or new_height < 10:
            self.log_print(f"⚠️ Calculated size too small: {new_width}x{new_height}, using fallback")
            new_width = max(400, container_width)
            new_height = max(300, container_height)
        
        try:
            resized_image = self.preview_image.resize((new_width, new_height), Image.LANCZOS)
            tk_image = ImageTk.PhotoImage(resized_image)
            
            self.preview_label.config(image=tk_image)
            self.preview_label.image = tk_image  # Keep a reference to prevent garbage collection
        except Exception as e:
            # Log the error but don't crash the application
            self.log_print(f"⚠️ Warning: Failed to resize preview image: {e}")
            import traceback
            self.log_print(traceback.format_exc())

    def add_element_label(self):
        """Add element label to the current preview image using PIL."""
        if not hasattr(self, 'preview_image'):
            messagebox.showwarning("No Preview", "Please generate a preview first.")
            return
        
        try:
            self.log_print("Adding element label...")
            
            # Get element name and units
            element_name = self.element.get()
            units = "ppm"  # Default
            # Check all files for this element to determine unit type
            for file in glob.glob(os.path.join(self.input_dir, "* matrix.xlsx")):
                parsed = self.parse_matrix_filename(file)
                if parsed:
                    _, element, unit_type = parsed
                    if element == element_name:
                        if unit_type == 'ppm':
                            units = "ppm"
                            break
                        elif unit_type == 'CPS':
                            units = "CPS"
                            break
                        elif unit_type == 'raw':
                            units = "counts"  # Raw counts data (not per second)
                            break
            
            self.log_print("Creating image copy...")
            # Start from the original unlabeled image (if available) to avoid overlapping labels
            if self.original_preview_image is not None:
                labeled_image = self.original_preview_image.copy()
            else:
                # Fallback to current preview_image if original not available
                labeled_image = self.preview_image.copy()
            
            # Get image dimensions
            img_width, img_height = labeled_image.size
            self.log_print(f"Processing image: {img_width}x{img_height}")
            
            # Create a drawing context
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(labeled_image)
            self.log_print("Setting up font...")
            
            # Try to use a nice font, fallback to default if not available
            try:
                # Use user-specified font size, with a minimum based on image size
                min_font_size = max(8, img_width // 80)  # Minimum based on image size
                font_size = max(min_font_size, self.element_label_font_size.get())
                font = ImageFont.truetype("/System/Library/Fonts/Arial Bold.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("arialbd.ttf", font_size)  # Arial Bold
                except:
                    try:
                        font = ImageFont.truetype("arial.ttf", font_size)
                    except:
                        font = ImageFont.load_default()
            
            # Prepare the text
            element_text = f"{element_name} ({units})"
            
            # Get text dimensions
            bbox = draw.textbbox((0, 0), element_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Position text at bottom left corner with more padding
            x = 50  # 50 pixels from left edge (increased from 20)
            y = img_height - text_height - 50  # 50 pixels from bottom edge (increased from 20)
            
            self.log_print("Drawing label...")
            # Draw the text in white (no background)
            draw.text((x, y), element_text, fill=(255, 255, 255), font=font)
            
            self.log_print("Updating preview...")
            # Update the preview image
            self.preview_image = labeled_image
            
            # Update the preview in the Preview tab
            self.update_preview_image()
            
            # Also update separate preview window if it exists (for backward compatibility)
            if self.preview_window is not None and self.preview_window.winfo_exists():
                self._update_preview_window_image()
            
            self.log_print(f"✅ Added element label: {element_text}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add element label: {str(e)}")
            self.log_print(f"Error adding element label: {str(e)}")

def main():
    root = tk.Tk()
    app = CompositeApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()