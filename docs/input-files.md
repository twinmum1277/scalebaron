# Input files

ScaleBarOn and Muad'Data expect elemental maps as **2D numeric matrices**. You can provide them as Excel/CSV files in a folder, or (in supported cases) reconstruct them from an HDF5 imaging session.

## Matrix filename convention

Filenames must follow a fixed pattern. The parser does **not** validate chemistry; analyte labels are treated as opaque text (for example `Ca44`, `CaF602`, `278nm`, `TotalMo`).

### Concentration or counts-per-second

```text
{sample} {analyte}_{unit} matrix.xlsx
{sample} {analyte}_{unit} matrix.csv
```

- `{unit}` must be `ppm` or `CPS` (case-insensitive; CPS is stored as `CPS`)
- Sample and analyte are separated by a space or underscore before the analyte token

**Examples:**

```text
S0_4 Ca44_ppm matrix.csv
LetoII Fe56_ppm matrix.xlsx
sampleA Zn66_CPS matrix.xlsx
```

### Raw counts (no unit suffix)

```text
{sample} {analyte} matrix.xlsx
{sample} {analyte} matrix.csv
```

**Example:**

```text
S0_4 Ca44 matrix.csv
```

Files that do not match these patterns are ignored when ScaleBarOn scans an input folder.

## File formats

| Format | Notes |
|--------|--------|
| **`.xlsx`** | Read with openpyxl. Cells that are non-numeric or negative become missing (`NaN`). |
| **`.csv`** | Parsed by a shared loader that handles dense grids and some wide/sparse GEOPIXE-style exports. Empty cells and `.` are treated as missing; negative values become missing. |

CSV test matrices in this repository are dense comma-separated grids **without a header row**. See [`test/testdata/csv/README.md`](../test/testdata/csv/README.md).

## Folder workflow (ScaleBarOn)

1. Put all matrix files for the study in **one input folder** (subfolders are not scanned by the matrix glob used for loading).
2. In ScaleBarOn, click **Input** and select that folder.
3. The Progress Table lists samples and element–unit columns found by parsing filenames.
4. Choose **Element** and **Unit** so ppm and CPS are never mixed in one composite.

## Custom pixel sizes

Physical pixel size (µm) controls scale bars and image extents.

- Default: a single **Pixel size** value in the GUI.
- **Multiple sizes?** — import a CSV with columns **`Sample`** and **`Pixel Size`**.
- **Pixel Sizes** can generate a template CSV from samples found in the current input (or HDF5 session), then you edit and re-import it.

When multiple pixel sizes are enabled, **Save Composite Matrix** is disabled because that export does not store per-panel scale.

## HDF5 imaging sessions

Both apps can import an HDF5 session via **HDF5** / **Import HDF5**.

Supported today:

- Imaging model **CellSpace** — rasters can be reconstructed for selected samples and channels (`ppm` / CPS channels exposed by the session metadata).

Not supported yet:

- Imaging model **FromSelections** — the apps report that reconstruction is not implemented.

HDF5 import requires **h5py** (installed with the core package). Pixel sizes may be taken from session metadata when available.


## Muad'Data loading

- **Element Viewer:** **Load Matrix** for a single `.xlsx` / `.csv`, or **Import HDF5** then choose Sample / Units / Element.
- **RGB Overlay** and **Z-Stack / Sum:** load matrices (or HDF5 channels) as required by each tab’s controls.

Composite matrices saved from ScaleBarOn (grid of panels with NaN separators) can be opened in Muad'Data for region tools; see [outputs.md](outputs.md).

## Related links

- [Quick start](quick-start.md)
- [Scaling methods](scaling-methods.md)
- [Troubleshooting](troubleshooting.md)
- Back to [README](../README.md)
