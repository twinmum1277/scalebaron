# Supported file formats

ScaleBarOn and Muad'Data accept the following input formats today. Matrix files must also follow the [filename convention](_synced/input-files.md#matrix-filename-convention).

| Extension | Kind | Notes |
|-----------|------|--------|
| **`.io4`** | Imaging session | Iolite session files. Opened via **HDF5** / **Import HDF5** (same dialog as `.h5`). |
| **`.h5` / `.hdf5`** | Imaging session | HDF5 imaging sessions. **CellSpace** is supported; **FromSelections** is not yet. See [input files](_synced/input-files.md#hdf5-imaging-sessions). |
| **`.xlsx`** | Matrix | Excel matrices, including **iolite exports**, read with openpyxl. Non-numeric or negative cells become missing (`NaN`). |
| **`.csv`** | Matrix | Dense grids and some wide/sparse GEOPIXE-style exports. Empty cells and `.` are treated as missing; negatives become missing. |

Session dialogs also list `*.vit` alongside `*.h5`, `*.hdf5`, and `*.io4`.

For folder workflows, naming rules, pixel-size CSVs, and HDF5 limitations, see [Input files](_synced/input-files.md).
