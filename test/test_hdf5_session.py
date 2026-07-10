import base64
import json
import os
import struct
import tempfile

import numpy as np
import pytest

h5py = pytest.importorskip("h5py")

from scalebaron.hdf5_session import (
    ImagingModel,
    is_hdf5_session,
    read_session_metadata,
    reconstruct_cellspace_raster,
    reconstruct_raster,
)

LVG_IO4 = os.path.join(
    os.path.dirname(__file__), "testdata", "LVG TEST4.io4"
)


@pytest.mark.skipif(not os.path.isfile(LVG_IO4), reason="LVG TEST4.io4 not in testdata")
class TestLvgSessionMetadata:
    def test_is_hdf5_session(self):
        assert is_hdf5_session(LVG_IO4)

    def test_imaging_model_from_selections(self):
        meta = read_session_metadata(LVG_IO4)
        assert meta.imaging_model == ImagingModel.FROM_SELECTIONS

    def test_samples_exclude_reference_and_baseline(self):
        meta = read_session_metadata(LVG_IO4)
        names = {s.name for s in meta.samples}
        assert "S0_5" in names
        assert "BASELINE" not in names
        assert "2025_BNEIRGEL_S1" not in names
        assert all("LVGel" not in n for n in names)

    def test_ppm_channels_present(self):
        meta = read_session_metadata(LVG_IO4)
        assert "Ca44" in meta.ppm_channels
        assert "Li7" in meta.ppm_channels

    def test_from_selections_raster_not_implemented(self):
        with pytest.raises(NotImplementedError):
            reconstruct_raster(LVG_IO4, "S0_5", "Ca44", unit="ppm")


def _write_cellspace_fixture(path):
    selections = []
    xs = [0.0, 1.0, 2.0]
    ys = [0.0, 1.0]
    seq = 0
    for y in ys:
        for x in xs:
            selections.append(
                {
                    "StartTime": seq * 0.1,
                    "EndTime": seq * 0.1 + 0.09,
                    "Properties": {
                        "Name": f"spot_{seq}",
                        "Coords": [[x, y], [x, y]],
                        "Spot Width": 1,
                        "Spot Height": 1,
                        "Scan Speed": 100.0,
                    },
                }
            )
            seq += 1

    global_json = {
        "imageType": "CellSpace",
        "selectionMapType": "Raster",
        "cellSpacePlacement": "Interpolated",
        "pixelsPerMicron": 1,
        "groupChannelNames": {"demo": ["Ca44_ppm"]},
    }
    global_json["physicalSize"] = base64.b64encode(
        struct.pack(">dd", 3.0, 2.0)
    ).decode()
    global_json["pixelSize"] = base64.b64encode(struct.pack(">ii", 3, 2)).decode()
    global_json["physicalMin"] = base64.b64encode(struct.pack(">dd", 0.0, 0.0)).decode()

    with h5py.File(path, "w") as handle:
        handle.create_group("SelectionGroups")
        handle["SelectionGroups"].create_dataset(
            "demo",
            data=json.dumps(
                {
                    "Properties": {"Group Type": "Sample", "Name": "demo"},
                    "Selections": selections,
                }
            ),
        )
        handle.create_group("Outputs")
        handle["Outputs"].create_dataset("Ca44_ppm", data=np.arange(6, dtype=float) + 1)
        handle.create_group("Special")
        handle["Special"].create_dataset(
            "IndexTime", data=np.linspace(0, 0.59, 6)
        )
        imaging = handle.create_group("UIPlugins").create_group("Imaging")
        imaging.attrs["Global"] = json.dumps(global_json)
        imaging.attrs["Group"] = "demo"


def test_cellspace_metadata_and_raster():
    with tempfile.NamedTemporaryFile(suffix=".h5", delete=False) as tmp:
        path = tmp.name
    try:
        _write_cellspace_fixture(path)
        meta = read_session_metadata(path)
        assert meta.imaging_model == ImagingModel.CELLSPACE
        assert len(meta.samples) == 1
        assert meta.samples[0].name == "demo"
        assert meta.samples[0].grid_rows == 2
        assert meta.samples[0].grid_cols == 3
        assert "Ca44" in meta.ppm_channels

        grid = reconstruct_cellspace_raster(path, "demo", "Ca44", unit="ppm")
        assert grid.shape == (2, 3)
        assert grid[0, 0] == pytest.approx(1.0)
        assert grid[1, 2] == pytest.approx(6.0)
    finally:
        os.unlink(path)
