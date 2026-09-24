import os

from scalebaron.muaddata import crop_export_basename, matching_sample_matrix_paths


def test_crop_export_basename_includes_bounds():
    name = crop_export_basename("liver 1", "Ca44", "Crop 2", (10, 40, 5, 25))
    assert name == "liver_1_Ca44_Crop_2_10-40_5-25"


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
