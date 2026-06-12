# scalebaron
Python toolkit for composite visualization and scaling of elemental imaging data 

**Windows users installing the development version (from a git clone):** see [INSTALL_WINDOWS_DEV.md](INSTALL_WINDOWS_DEV.md) for step-by-step instructions and dependencies.

To install (core dependencies only):
```bash
pip install git+https://github.com/twinmum1277/scalebaron
```

Or from PyPI:
```bash
pip install scalebaron
```

**Optional packages** (specimen-mask contour refinement, SVG icons, enhanced statistics):
```bash
pip install "scalebaron[optional]"
# or, from a clone:
pip install -r requirements-optional.txt
```

| Package | Used for |
|---------|----------|
| **Core** (`requirements.txt`) | NumPy, Pandas, Matplotlib, openpyxl, Pillow — compositing, map viewing, LOD, region stats, CSV/XLSX I/O |
| **SciPy** (optional) | Mask morphology (beta specimen tool), mode statistic fallback, Pearson *p*-value in RGB ratio |
| **scikit-image** (optional) | `find_contours` in beta specimen mask (Matplotlib fallback if absent) |
| **cairosvg** (optional) | SVG logo/icon rendering (PNG icons used if absent) |

To run ScaleBaron: 
```{bash}
scalebaron
```

To run Muad'Data: 
```{bash}
muaddata
```

To download test data for this package:
```{bash}
download_test_elemental_images
```