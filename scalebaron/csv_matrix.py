"""
Shared CSV matrix loader for ScaleBarOn and Muad'Data.

Handles wide, sparse GEOPIXE-style exports where pandas.read_csv can hang or fail.
"""

import csv
import os

import numpy as np

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


def is_csv_path(path):
    return str(path).lower().endswith(".csv")


def load_csv_matrix(filepath):
    """
    Load a 2D numeric matrix from a GEOPIXE-style CSV file.

    Returns:
        numpy.ndarray on success, or None if all parsing strategies fail.
    """
    # Strategy 0: stdlib csv reader for wide/sparse files
    try:
        rows = []
        with open(filepath, "r", encoding="utf-8", errors="ignore", newline="") as f:
            for row in csv.reader(f):
                rows.append(row)
        if rows:
            max_cols = max(len(r) for r in rows)
            if max_cols > 0:
                out = np.full((len(rows), max_cols), np.nan, dtype=float)
                for i, row in enumerate(rows):
                    for j, cell in enumerate(row):
                        s = str(cell).strip()
                        if s in ("", "."):
                            continue
                        try:
                            v = float(s)
                            if v >= 0:
                                out[i, j] = v
                        except Exception:
                            pass

                first_col_finite = int(np.isfinite(out[:, 0]).sum()) if out.shape[1] > 0 else 0
                if out.shape[1] > 1 and first_col_finite < out.shape[0] * 0.3:
                    out = out[:, 1:]

                if out.size > 0:
                    keep_rows = ~np.all(np.isnan(out), axis=1)
                    keep_cols = ~np.all(np.isnan(out), axis=0)
                    out = out[keep_rows][:, keep_cols]

                if out.size > 0 and out.shape[0] >= 2 and out.shape[1] >= 2:
                    return out
    except Exception:
        pass

    if not PANDAS_AVAILABLE:
        return None

    # Strategy 1: pandas without headers
    try:
        df = pd.read_csv(filepath, header=None, encoding="utf-8", errors="ignore")
        matrix = _pandas_csv_to_matrix(df)
        if matrix is not None:
            return matrix
    except Exception:
        pass

    # Strategy 2: pandas with header row
    try:
        df = pd.read_csv(filepath, header=0, encoding="utf-8", errors="ignore")
        matrix = _pandas_csv_to_matrix(df)
        if matrix is not None:
            return matrix
    except Exception:
        pass

    # Strategy 3: skip metadata rows at top
    for skip_rows in range(1, 6):
        try:
            df = pd.read_csv(filepath, header=None, skiprows=skip_rows, encoding="utf-8", errors="ignore")
            matrix = _pandas_csv_to_matrix(df)
            if matrix is not None:
                return matrix
        except Exception:
            continue

    return None


def load_csv_matrix_or_raise(filepath):
    """Like load_csv_matrix but raises ValueError when parsing fails."""
    mat = load_csv_matrix(filepath)
    if mat is None:
        raise ValueError(f"Could not parse numeric matrix from {os.path.basename(filepath)}")
    return mat


def _pandas_csv_to_matrix(df):
    df = df.replace(".", np.nan).replace("", np.nan)
    if len(df) == 0 or len(df.columns) == 0:
        return None

    first_col_numeric = pd.to_numeric(df.iloc[:, 0], errors="coerce").notna().sum()
    total_rows = len(df)
    if total_rows > 0 and (
        first_col_numeric < total_rows * 0.3 or df.iloc[:, 0].isna().sum() > total_rows * 0.5
    ):
        data_df = df.iloc[:, 1:]
    else:
        first_val = str(df.iloc[0, 0]) if len(df) > 0 else ""
        if first_val in (".", "nan"):
            data_df = df.iloc[:, 1:]
        else:
            data_df = df

    data_df = data_df.apply(pd.to_numeric, errors="coerce")
    data_df = data_df.dropna(how="all").dropna(axis=1, how="all")
    arr = data_df.to_numpy(dtype=float)
    arr[arr < 0] = np.nan
    if arr.size > 0 and arr.shape[0] >= 2 and arr.shape[1] >= 2:
        return arr
    return None
