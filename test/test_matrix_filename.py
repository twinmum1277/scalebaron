import pytest

from scalebaron.matrix_filename import parse_matrix_filename


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("JM2 Ca44_CPS matrix.csv", ("JM2", "Ca44", "CPS")),
        ("JM2 CaF602_CPS matrix.csv", ("JM2", "CaF602", "CPS")),
        ("JM2 CaF603_CPS matrix.csv", ("JM2", "CaF603", "CPS")),
        ("liver-1 TotalMo_ppm matrix.xlsx", ("liver-1", "TotalMo", "ppm")),
        ("my sample Mo98_ppm matrix.csv", ("my sample", "Mo98", "ppm")),
        ("spotA 278nm_CPS matrix.csv", ("spotA", "278nm", "CPS")),
        ("JM2 Ca44 matrix.xlsx", ("JM2", "Ca44", "raw")),
        ("JM2 CaF602 matrix.csv", ("JM2", "CaF602", "raw")),
        ("/path/to/JM2 Ca44_CPS matrix.CSV", ("JM2", "Ca44", "CPS")),
    ],
)
def test_parse_matrix_filename(filename, expected):
    assert parse_matrix_filename(filename) == expected


@pytest.mark.parametrize(
    "filename",
    [
        "random_data.csv",
        "JM2 Ca44 CPS matrix.csv",  # missing underscore before unit
        "Ca44_ppm matrix.csv",  # missing sample
    ],
)
def test_parse_matrix_filename_rejects(filename):
    assert parse_matrix_filename(filename) is None
