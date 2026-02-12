# ScaleBarOn Changelog

## Version 0.8.8 (Current)
**Current Commit:** `bfeb6acd0f8d1322c4f70cc0289e14022cf88334`

### Major Features Added

#### 1. **Tabbed Interface**
- Refactored UI from single window to tabbed navigation
- **Tab 1: Setup & Statistics** - Data loading, element selection, batch processing
- **Tab 2: Preview & Export** - Preview generation, composite saving, matrix export
- Maintains consistent control panel width (280px) on both tabs for usability
- Simplifies navigation and reduces visual clutter

#### 2. **Enhanced Statistics & Progress Tracking**
- **Statistics Table** - Displays 25th, 50th, 75th, 99th percentiles, IQR, and Mean for current element
- **Progress Table** - Shows sample-element processing status with visual indicators:
  - ✓ = Complete (composite generated)
  - ~ = Partial (histograms/statistics generated)
  - X = Missing File (input not found)
  - ☐/☑ = Include/Exclude sample from scaling
- Click-to-toggle sample selection in Progress Table
- Auto-refresh with status checking against output folder

#### 3. **Batch Processing**
- New `batch_process_all_elements()` method processes all elements automatically
- Processes elements sequentially with:
  - Automatic 99th percentile scale max calculation
  - Best layout determination (minimizes empty cells)
  - Histogram and statistics generation
  - Composite saving
- Real-time progress bar and status logging
- Graceful error handling with per-element failure reporting
- Summary statistics on completion

#### 4. **Advanced Layout Controls**
- **Auto Layout Mode** - `use_best_layout` option calculates optimal rows/cols grid
- **`_best_composite_rows()` method** - Minimizes empty cells in grid layout
- Configurable row count for manual layout control
- Better handles variable sample counts without blank subplots

#### 5. **Button Icon System**
- New `load_button_icons()` method with dual-source icon loading:
  - Primary: External PNG files from `icons/` directory
  - Fallback: Base64-encoded embedded icons from `embedded_icons` module
- Icons displayed on buttons for:
  - Summarize (📊)
  - Preview (👁️)
  - Add Label (🏷️)
  - Save (💾)
  - Batch (⚡)
  - Progress (📈)
- Unicode emoji fallback if icons unavailable
- Improves visual appeal and usability

#### 6. **Custom Pixel Size Management**
- **Multiple Pixel Sizes Support** - `use_custom_pixel_sizes` toggle
- `import_custom_pixel_sizes()` - Load custom sizes from CSV
- `generate_pixel_size_template()` - Export template for user customization
- Per-sample pixel size storage in `pixel_sizes_by_sample` dict
- Scales displayed correctly in composite with per-sample labels (if custom sizes enabled)

#### 7. **Preview Window Enhancements**
- **Separate Preview Window** - `show_preview_window()` creates floating preview
- **Responsive Scaling** - Auto-fits image to window with aspect ratio preservation
- **Dynamic Resizing** - `_on_preview_window_resize()` with throttled updates (max 10/sec)
- Embedded control panel with:
  - Font size slider for element labels
  - Add Label and Save buttons
  - Info display (element name, dimensions)
- Center-aligned on screen with max 90% of screen dimensions
- Handles window close gracefully

#### 8. **Improved Composite Matrix Export**
- New `save_composite_matrix()` method exports for Muad'Data compatibility
- Grid-based arrangement with:
  - Sample padding (NaN) for uniform dimensions
  - Row/column separators
  - Supports .xlsx and .csv formats
- Enables polygon selection workflow in Muad'Data
- Preserves spatial relationships in composite layout

#### 9. **Element Label Enhancement**
- `add_element_label()` method with PIL-based drawing
- Displays element name and units (ppm/CPS/counts)
- Font size controlled by user slider
- Position: Bottom-left with adjustable padding
- Works from original unlabeled image (avoids overlapping labels)
- Updates both inline preview and separate window

#### 10. **Status Logging System**
- Dual status logs (Setup tab and Preview tab) for consistency
- `log_print()` method with filtering to reduce clutter
- `set_status()` tracks app state (Idle/Busy/Finishing)
- Status-only logging during batch processing
- Real-time progress feedback

#### 11. **Incremental Processing**
- `load_data()` now checks for existing statistics
- Only processes new samples (skips existing)
- Merges new statistics with existing ones
- Reduces redundant calculations
- Efficient for iterative workflows

#### 12. **Error Handling Improvements**
- Graceful handling of Dropbox sync issues (incomplete files)
- Per-file error reporting without stopping batch
- Detailed error messages for debugging
- File validation before processing

### UI/UX Improvements
- Window minimum size: 600x500 (was smaller)
- Initial window size: 1200x800 (ensures all controls visible)
- Resizable tabs with flexible layouts
- PanedWindow for Statistics/Progress tables (adjustable divider)
- Improved visual hierarchy with labeled sections
- Better spacing and padding throughout

### Bug Fixes
- Fixed progress table widget initialization timing
- Corrected sample filtering for selected elements
- Improved image resizing calculation (avoid zero dimensions)
- Better aspect ratio handling in preview windows

### Performance Optimizations
- Auto-downsampling when >10 samples (preview/save)
- Throttled resize events (max 10/sec)
- Incremental file processing (skip existing)
- Optional downsampling target: 512px max dimension

### Configuration Variables Added
- `use_best_layout: BooleanVar` - Auto layout optimization
- `use_custom_pixel_sizes: BooleanVar` - Multiple pixel size mode
- `use_button_icons: BooleanVar` - Icon toggle (future use)
- `progress_table: Treeview` - Embedded progress tracking
- `stats_table: Treeview` - Statistics display
- `custom_pixel_sizes: dict` - Sample → pixel size mapping
- `pixel_sizes_by_sample: dict` - Runtime pixel size cache

### Methods Added/Refactored
**New Methods:**
- `build_setup_tab()` - Constructs Setup & Statistics tab
- `build_preview_tab()` - Constructs Preview & Export tab
- `load_button_icons()` - Icon loading system
- `show_progress_table_window()` - Progress table display (now embedded)
- `refresh_progress_table()` - Manual progress refresh
- `_on_progress_table_click()` - Sample toggle handler
- `_scan_progress_from_output()` - Infer progress from output folder
- `_check_existing_progress()` - Status checking from files
- `update_statistics_table()` - Statistics display
- `update_progress_table()` - Progress table rendering
- `update_sample_element_progress()` - Per-element progress update
- `check_sample_element_status()` - Status lookup
- `scan_progress_table()` - Input folder scanning
- `get_selected_samples()` - Filtered sample list
- `batch_process_all_elements()` - Batch mode orchestration
- `_best_composite_rows()` - Layout optimization
- `show_preview_window()` - Separate preview window
- `_on_preview_window_resize()` - Preview window resize handler
- `_update_preview_window_image()` - Preview image update
- `_close_preview_window()` - Window cleanup
- `save_composite_matrix()` - Matrix export for Muad'Data
- `add_element_label()` - PIL-based labeling
- `log_print()` - Filtered logging
- `set_status()` - Status tracking

**Refactored Methods:**
- `__init__()` - Additional state variables, icon loading
- `load_data()` - Incremental processing, better error handling
- `generate_composite()` - Preview window support, labeled subplots
- `update_preview_image()` - Aspect ratio preservation, fallback sizing
- `select_input_folder()` - Progress table integration
- `select_output_folder()` - Progress checking

### Dependencies
- PIL/Pillow - Image manipulation
- pandas - Statistics and data handling
- matplotlib - Visualization (existing)
- openpyxl - Excel I/O (existing)
- numpy - Array operations (existing)

### Breaking Changes
- None (backward compatible with existing workflows)

### Known Limitations
- Embedded icons require `embedded_icons.py` module (optional)
- Preview resizing may be throttled during batch processing
- Large composites (>1000 samples) may require downsampling

### Testing Recommendations
- Test batch processing with mixed element types
- Verify progress table persistence across folder changes
- Validate custom pixel size CSV format
- Test icon loading fallback on systems without icon files

---

**Revision Date:** 2026-02-12  
**Version:** 0.8.8  
**Status:** Current Release