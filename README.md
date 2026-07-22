# ScaleBarOn

ScaleBarOn is a Python toolkit for **scaling and compositing multiple elemental imaging maps** so they can be compared on a shared color scale. It ships with a companion GUI, **Muad'Data**, for viewing individual maps, RGB overlays, region statistics, and related analysis.

**Package version:** 1.0.2 (see `setup.py`). The ScaleBarOn window title may still show an older build label (for example, v0.8.8).

## Intended use

ScaleBarOn is aimed at researchers working with laser ablation / elemental imaging matrices (for example, GEOPIXE-style exports). Typical tasks:

- Place many samples of the same element on **one shared scale** for fair visual comparison
- Generate multi-panel **composite figures** with color bars and scale bars
- Review **percentiles and histograms** before choosing a display maximum
- Optionally continue analysis in **Muad'Data** (single maps, RGB overlays, polygons, LOD filtering, map math)

## Key features

**ScaleBarOn**

- Folder-based loading of matrix files (`.xlsx` / `.csv`) with a fixed filename convention
- Optional import of **HDF5 imaging sessions** (CellSpace model; see [limitations](docs/troubleshooting.md#known-limitations))
- Shared **scale maximum** (suggested from the overall 99th percentile) with linear or pseudo-log display
- Statistics table, progress tracking, and **batch processing** across elements/units
- Composite export as **PNG** or **TIFF**, plus optional composite matrix for Muad'Data

**Muad'Data**

- Element Viewer, RGB Overlay, and Z-Stack / Sum tabs
- Detection-limit (LOD) filtering, polygon / magic-wand regions, crop, and map math
- Export of images and matrices for further work

## Installation

**From PyPI (recommended for most users):**

```bash
pip install scalebaron
```

**From GitHub:**

```bash
pip install git+https://github.com/twinmum1277/scalebaron
```

**Optional extras** (specimen-mask refinements, SVG icons, enhanced statistics):

```bash
pip install "scalebaron[optional]"
```

Requires **Python 3.8+** and a working **Tkinter** GUI (usually included with Python).

Full install details, virtual environments, and development (editable) installs: **[docs/installation.md](docs/installation.md)**.

Platform-specific development notes:

- [INSTALL_WINDOWS_DEV.md](INSTALL_WINDOWS_DEV.md)
- [INSTALL_MAC_DEV.md](INSTALL_MAC_DEV.md)

## Quick start

```bash
# Launch ScaleBarOn
scalebaron

# Or launch Muad'Data
muaddata
```

Minimal ScaleBarOn workflow:

1. Choose an **Input** folder of matrix files (or import a supported HDF5 session).
2. Choose an **Output** folder.
3. On **Setup & Statistics**, click **Calculate statistics** (or run **Batch Processing**).
4. On **Preview & Export**, adjust scale max / colormap if needed, then **Preview** and **Save Composite**.

Step-by-step guide: **[docs/quick-start.md](docs/quick-start.md)**.

Example matrices for testing are under [`test/testdata/`](test/testdata/) (including [`test/testdata/csv/`](test/testdata/csv/)). Additional JAAS-related examples live in [`JAAS submission/`](JAAS%20submission/).

## Documentation

| Guide | Contents |
|-------|----------|
| [Installation](docs/installation.md) | PyPI, GitHub, optional deps, editable installs |
| [Quick start](docs/quick-start.md) | First session in ScaleBarOn and Muad'Data |
| [Input files](docs/input-files.md) | Filename rules, CSV/XLSX, HDF5, pixel-size CSV |
| [Scaling methods](docs/scaling-methods.md) | Scale max, linear vs log, layout, colormaps |
| [Outputs](docs/outputs.md) | Folders and file formats produced by the apps |
| [Troubleshooting](docs/troubleshooting.md) | Common problems and known limitations |

## Links

- **PyPI:** [https://pypi.org/project/scalebaron/](https://pypi.org/project/scalebaron/)
- **Source / GitHub:** [https://github.com/twinmum1277/scalebaron](https://github.com/twinmum1277/scalebaron)
- **Issues:** [https://github.com/twinmum1277/scalebaron/issues](https://github.com/twinmum1277/scalebaron/issues)
- **License:** [MIT](LICENSE)
- **Citation:** see [citation.cff](citation.cff). A published DOI is not yet filled in the citation file —  
  `[PLACEHOLDER: published citation / DOI after Zenodo or journal release]`.

## BNEIR software pages and video tutorials

ScaleBarOn and Muad'Data are associated with the **Biomedical National Elemental Imaging Resource (BNEIR)** at Dartmouth.

- **BNEIR website:** [https://sites.dartmouth.edu/bneir/](https://sites.dartmouth.edu/bneir/)
- **BNEIR software landing page:** `[PLACEHOLDER: BNEIR software page URL]`
- **Hosted video tutorials:** `[PLACEHOLDER: hosted video tutorial URL(s)]`
- **Local demo video in this repository:** [`JAAS submission/ScaleBarOn.mov`](JAAS%20submission/ScaleBarOn.mov) (large file; open locally)

Clicking the BNEIR logo in either GUI also opens the BNEIR website.
