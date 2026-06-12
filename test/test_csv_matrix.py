import csv
import os
import tempfile

import numpy as np
import pytest

from scalebaron.csv_matrix import is_csv_path, load_csv_matrix


def test_is_csv_path_case_insensitive():
    assert is_csv_path("foo.csv")
    assert is_csv_path("foo.CSV")
    assert not is_csv_path("foo.xlsx")


def test_load_sparse_wide_csv():
  """Simulates GEOPIXE export: many columns, few values per row."""
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    try:
        rows = []
        for r in range(4):
            row = [""] * 200
            row[0] = "."
            row[10 + r] = str(1.5 + r)
            row[50 + r] = str(2.0 + r)
            rows.append(row)
        with open(path, "w", newline="") as f:
            csv.writer(f).writerows(rows)
        mat = load_csv_matrix(path)
        assert mat is not None
        assert mat.shape[0] >= 2 and mat.shape[1] >= 2
        assert np.isfinite(mat).sum() >= 8
    finally:
        os.unlink(path)


def test_load_simple_dense_csv():
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    try:
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow([1.0, 2.0, 3.0])
            w.writerow([4.0, 5.0, 6.0])
        mat = load_csv_matrix(path)
        assert mat.shape == (2, 3)
        np.testing.assert_allclose(mat, [[1, 2, 3], [4, 5, 6]])
    finally:
        os.unlink(path)
