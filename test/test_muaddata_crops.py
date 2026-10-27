import os

import numpy as np
import pytest

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


def _viewer_or_skip():
    try:
        import tkinter as tk
        from scalebaron.muaddata import MuadDataViewer
    except Exception as exc:
        pytest.skip(f"Tkinter environment not available: {exc}")
    root = tk.Tk()
    root.withdraw()
    return MuadDataViewer(root), root


def _outline_box(viewer):
    outlines = [artist for artist in viewer._crop_highlight_artists if artist.get_linestyle() == "--"]
    assert len(outlines) == 1
    outline = outlines[0]
    return tuple(outline.get_xy()), outline.get_width(), outline.get_height()


def test_selecting_saved_crop_outlines_it_on_the_full_map():
    viewer, root = _viewer_or_skip()
    try:
        viewer.pixel_size.set(0)
        viewer.single_matrix = np.zeros((20, 30))
        viewer.saved_crops = [
            {"name": "Crop 1", "bounds": [2, 8, 4, 10]},
            {"name": "Crop 2", "bounds": [12, 18, 1, 6]},
        ]
        viewer.saved_crop_shape = (20, 30)
        viewer._refresh_crop_listbox()
        viewer.view_single_map()
        assert viewer._crop_highlight_artists == []

        viewer.crop_listbox.selection_set(0)
        viewer._on_crop_list_select()
        assert _outline_box(viewer) == ((1.5, 3.5), 6, 6)

        viewer.crop_listbox.selection_clear(0)
        viewer.crop_listbox.selection_set(1)
        viewer._on_crop_list_select()
        assert _outline_box(viewer) == ((11.5, 0.5), 6, 5)
    finally:
        root.destroy()
