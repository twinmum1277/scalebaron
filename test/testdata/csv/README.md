# CSV test matrices

Bundled matrix CSV exports for ScaleBarOn and Muad'Data testing. These mirror the
JAAS paper **S0–S4** sample grid (ppm concentrations) exported from GEOPIXE.

## Inventory (75 files)

| | |
|---|---|
| **Samples** | 15 — `S0_4` … `S4_6` (five sample groups × three replicates) |
| **Elements** | 5 — Ca44, Cu63, Fe56, Mn55, Zn66 |
| **Unit** | ppm only |
| **Matrix size** | 24×24 for `_4` and `_5` samples; 25×25 for `_6` samples |
| **Format** | Dense numeric grid, comma-separated, no header row |

Mg26 is present in the JAAS XLSX bundle but is **not** included here; the remaining
15×5 grid is complete.

### Samples

`S0_4`, `S0_5`, `S0_6`, `S1_4`, `S1_5`, `S1_6`, `S2_4`, `S2_5`, `S2_6`, `S3_4`,
`S3_5`, `S3_6`, `S4_4`, `S4_5`, `S4_6`

### Elements (per sample)

`Ca44_ppm`, `Cu63_ppm`, `Fe56_ppm`, `Mn55_ppm`, `Zn66_ppm`

Example filename: `S0_4 Ca44_ppm matrix.csv`

## Filename convention

Use the same naming as Excel matrices:

```
{sample} {analyte}_{unit} matrix.csv
```

Raw counts (no unit suffix):

```
{sample} {analyte} matrix.csv
```

## Usage

**ScaleBarOn:** set Input folder to this directory.

**Muad'Data:** Load Matrix → pick a file from here.

**Automated check:**

```bash
pytest test/test_csv_fixtures.py -v
```

## Optional additions (not in this bundle)

- CPS or raw-count exports for the same samples
- One wide sparse GEOPIXE-style CSV (parser stress test)
