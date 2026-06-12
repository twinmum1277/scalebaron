"""Optional integration checks for CSV files placed in test/testdata/csv/."""

import os

import pytest

from scalebaron.csv_matrix import is_csv_path, load_csv_matrix
from scalebaron.matrix_filename import parse_matrix_filename

CSV_FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "testdata", "csv")


def _csv_fixture_paths():
    if not os.path.isdir(CSV_FIXTURE_DIR):
        return []
    return sorted(
        os.path.join(CSV_FIXTURE_DIR, name)
        for name in os.listdir(CSV_FIXTURE_DIR)
        if is_csv_path(name) and os.path.isfile(os.path.join(CSV_FIXTURE_DIR, name))
    )


@pytest.mark.skipif(not _csv_fixture_paths(), reason="No CSV fixtures in test/testdata/csv yet")
def test_csv_fixtures_load_and_parse():
    for path in _csv_fixture_paths():
        mat = load_csv_matrix(path)
        assert mat is not None
        assert mat.ndim == 2
        assert mat.shape[0] >= 2 and mat.shape[1] >= 2

        parsed = parse_matrix_filename(path)
        assert parsed is not None, f"Filename does not match convention: {os.path.basename(path)}"
        sample, analyte, unit_type = parsed
        assert sample
        assert analyte
        assert unit_type in ("ppm", "CPS", "raw")
