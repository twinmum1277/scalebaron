# Troubleshooting

## Apps will not start

**`scalebaron: command not found` (or similar)**  
- Confirm the environment where you ran `pip install` is active.  
- Try `python -m scalebaron.scalebaron`.  
- Reinstall: `pip install scalebaron` or `pip install -e .` from a clone.

**Tkinter / display errors**  
- ScaleBarOn and Muad'Data need Tkinter and a graphical session.  
- On some Linux installs, install the distro `python3-tk` package.  
- Remote or headless servers usually cannot run these GUIs without extra display setup (not covered by this package).

## Installation problems

**Optional packages fail (`cairosvg`, etc.)**  
- Core workflows can run without optional extras. Install core only, then add optional packages later if needed.  
- On macOS, Cairo may need Homebrew packages before `cairosvg` works; see [INSTALL_MAC_DEV.md](../INSTALL_MAC_DEV.md).  
- On Windows, see [INSTALL_WINDOWS_DEV.md](../INSTALL_WINDOWS_DEV.md).

**Wrong Python version**  
- Requires **Python ≥ 3.8** (`setup.py`).

## No files appear / “No files for element”

- Check the **filename convention** in [input-files.md](input-files.md). Names must end with `matrix.xlsx` or `matrix.csv` and include the sample and analyte tokens as documented.  
- Put matrices in the **top level** of the Input folder (the loader globs that directory, not nested trees).  
- Select the correct **Unit** (`ppm` vs `CPS` vs raw). Mixing units is blocked when both ppm and CPS exist.  
- Ensure Progress Table **Include** checkboxes are checked for the samples you want.  
- With **Multiple sizes?** enabled, only samples listed in the custom pixel-size CSV are loaded.

## Excel files fail to open

Messages about incomplete archives or missing `Content_Types` often mean a **cloud placeholder** (for example Dropbox) that is not fully downloaded. Fully sync the file and try again.

## HDF5 import

- **FromSelections** sessions are **not implemented**; the app shows a clear error. Use **CellSpace** sessions or export matrices to `.xlsx` / `.csv`.  
- Unrecognized HDF5 layouts raise an error that the file is not a recognized imaging session.  
- `h5py` must be installed (included in core requirements).

## Scaling / appearance

- If panels look washed out or clipped, adjust **Scale max** (see [scaling-methods.md](scaling-methods.md)). Statistics use the **99th percentile** suggestion; you can override it.  
- **Log scale** uses pseudo-log (`log1p`), not a pure logarithmic transform of the raw data.  
- Large sample counts may use downsampled matrices for composite rendering.

## Save Composite Matrix disabled

This button is disabled when **Multiple sizes?** is checked, because the composite matrix file does not store per-panel pixel sizes.

## Test data downloader

```bash
download_test_elemental_images
```

opens a directory picker and tries to download a fixed list of `.xlsx` files from the GitHub repository. Those remote filenames may not match what is currently under `test/testdata/` in every clone. If downloads fail, use:

- [`test/testdata/`](../test/testdata/)
- [`test/testdata/csv/`](../test/testdata/csv/)
- [`JAAS submission/`](../JAAS%20submission/)

## Version labels look inconsistent

- PyPI / `setup.py` package version: **1.0.2**  
- ScaleBarOn window title may still show an older label (for example **v0.8.8**)  
- [`citation.cff`](../citation.cff) may list a different version and still contain placeholder DOI / repository fields  

Prefer the installed package metadata (`pip show scalebaron`) when reporting versions.

## Report a bug

Use **Report Issue** in the GUI, or open a ticket at:

[https://github.com/twinmum1277/scalebaron/issues](https://github.com/twinmum1277/scalebaron/issues)

## Known limitations

Documented from the current codebase (not a complete feature roadmap):

| Limitation | Detail |
|------------|--------|
| GUI only | No CLI arguments for scaling or batch jobs |
| HDF5 FromSelections | Raster reconstruction not implemented |
| Filename convention | Non-conforming names are skipped |
| Input folder depth | Matrix search is in the selected folder, not recursive |
| Composite matrix + multi pixel size | Save Composite Matrix disabled when multiple pixel sizes are used |
| Optional deps | Some specimen-mask / SVG / stats extras need SciPy, scikit-image, or cairosvg |
| Citation DOI | `[PLACEHOLDER: published DOI]` still present in `citation.cff` |

## Related links

- [Installation](installation.md)
- [Input files](input-files.md)
- Back to [README](../README.md)
