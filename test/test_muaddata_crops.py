import os

from scalebaron.matrix_filename import parse_matrix_filename
from scalebaron.muaddata import crop_export_filename, matching_sample_matrix_paths


def test_crop_export_filename_follows_matrix_convention():
    name = crop_export_filename("liver 1", "Ca44", "ppm", "Crop 2")
    assert name == "liver 1 C2 Ca44_ppm matrix.xlsx"
    assert parse_matrix_filename(name) == ("liver 1 C2", "Ca44", "ppm")


def test_crop_export_filename_raw_omits_unit():
    name = crop_export_filename("S1", "Fe56", "raw", "Crop 1")
    assert name == "S1 C1 Fe56 matrix.xlsx"
    assert parse_matrix_filename(name) == ("S1 C1", "Fe56", "raw")


def test_matching_sample_matrix_paths_filters_sample_and_unit(tmp_path):
    names = [
        "S1 Ca44_ppm matrix.csv",
        "S1 Fe56_ppm matrix.csv",
        "S1 Zn66_CPS matrix.csv",
        "S2 Ca44_ppm matrix.csv",
        "notes.txt",
    ]
    for name in names:
        (tmp_path / name).write_text("0\n", encoding="utf-8")

    found = [os.path.basename(path) for path in matching_sample_matrix_paths(tmp_path, "S1", "ppm")]
    assert found == ["S1 Ca44_ppm matrix.csv", "S1 Fe56_ppm matrix.csv"]
