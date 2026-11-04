import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.colors import Normalize

from scalebaron.scalebaron import CompositeApp


class _Flag:
    def __init__(self, value):
        self._value = value

    def get(self):
        return self._value


def _app(pixel_size=5):
    app = CompositeApp.__new__(CompositeApp)
    app.hdf5_pixel_sizes_xy = {}
    app.pixel_sizes_by_sample = {}
    app.pixel_size = _Flag(pixel_size)
    return app


def _render(app, panels, frame_w, frame_h, rows):
    n = len(panels)
    cols = math.ceil(n / rows)
    fig = plt.figure(figsize=(4 * cols + 1, 4 * rows))
    FigureCanvasAgg(fig)
    gs = fig.add_gridspec(rows, cols + 1, width_ratios=[1] * cols + [0.2])
    norm = Normalize(vmin=0, vmax=1)
    axes = []
    for i, panel in enumerate(panels):
        r, c = divmod(i, cols)
        ax = fig.add_subplot(gs[r, c])
        app._draw_matrix_on_frame(
            ax, panel["matrix"], panel["dx"], panel["dy"], frame_w, frame_h, "viridis", norm
        )
        axes.append(ax)
    fig.canvas.draw()
    return fig, axes


def _shown_width(ax):
    extent = ax.images[0].get_extent()
    data_w = extent[1] - extent[0]
    frame = ax.get_xlim()[1] - ax.get_xlim()[0]
    return data_w / frame * ax.get_window_extent().width


def test_missing_pixel_size_is_rejected():
    app = _app()
    app.pixel_sizes_by_sample = {"a": 0}
    with pytest.raises(ValueError, match="no positive pixel size"):
        app._prepare_shared_scale_panels([np.ones((4, 4))], ["a"], False)


def test_mixed_pixel_sizes_share_one_physical_frame():
    app = _app()
    app.pixel_sizes_by_sample = {"coarse": 10.0, "fine": 5.0}
    matrices = [np.ones((100, 100)), np.ones((200, 200))]
    panels, frame_w, frame_h = app._prepare_shared_scale_panels(
        matrices, ["coarse", "fine"], False
    )
    assert panels[0]["width_um"] == pytest.approx(1000)
    assert panels[1]["width_um"] == pytest.approx(1000)
    assert frame_w == pytest.approx(1000)
    assert frame_h == pytest.approx(1000)


def test_anisotropic_pixels_use_both_axes():
    app = _app()
    app.hdf5_pixel_sizes_xy = {"scan": (5.0, 10.0)}
    panels, frame_w, frame_h = app._prepare_shared_scale_panels(
        [np.ones((4, 8))], ["scan"], False
    )
    assert frame_w == pytest.approx(40)
    assert frame_h == pytest.approx(40)
    assert panels[0]["dx"] == pytest.approx(5)
    assert panels[0]["dy"] == pytest.approx(10)


def test_downsampling_keeps_the_physical_distance_of_the_pixels_shown():
    app = _app()
    labels = [f"s{i}" for i in range(11)]
    matrices = [np.full((20, 20), 3.0) for _ in labels]
    matrices[-1] = np.full((400, 2000), 3.0)
    app.pixel_sizes_by_sample = {label: 5.0 for label in labels}
    panels, frame_w, frame_h = app._prepare_shared_scale_panels(matrices, labels, True)

    big = panels[-1]
    assert big["factor"] == 3
    kept_cols = (2000 // 3) * 3
    kept_rows = (400 // 3) * 3
    assert big["width_um"] == pytest.approx(kept_cols * 5)
    assert big["height_um"] == pytest.approx(kept_rows * 5)
    assert big["matrix"][0, 0] == pytest.approx(3.0)
    assert frame_w == pytest.approx(big["width_um"])
    assert frame_h == pytest.approx(big["height_um"])
    assert panels[0]["factor"] == 1
    assert panels[0]["width_um"] == pytest.approx(100)


def test_layout_cannot_change_spatial_scale_or_scale_bar():
    app = _app()
    shapes = [(200, 200), (200, 600), (600, 200)]
    labels = ["square", "wide", "tall"]
    app.pixel_sizes_by_sample = {label: 5.0 for label in labels}
    matrices = [np.ones((h, w)) for h, w in shapes]
    panels, frame_w, frame_h = app._prepare_shared_scale_panels(matrices, labels, False)
    assert frame_w == pytest.approx(3000)
    assert frame_h == pytest.approx(3000)

    scale_bar_um = 1000
    ratios = []
    for rows in (1, 3):
        fig, axes = _render(app, panels, frame_w, frame_h, rows)
        try:
            widths = [ax.get_window_extent().width for ax in axes]
            assert max(widths) - min(widths) <= 1
            for ax in axes:
                assert ax.get_xlim() == pytest.approx((0, frame_w))
                assert ax.get_ylim() == pytest.approx((0, frame_h))
            square, wide, tall = axes
            assert np.diff(square.images[0].get_extent()[:2])[0] == pytest.approx(1000)
            assert np.diff(wide.images[0].get_extent()[:2])[0] == pytest.approx(3000)
            assert np.diff(tall.images[0].get_extent()[2:])[0] == pytest.approx(3000)
            assert square.images[0].get_extent()[0] == pytest.approx(1000)
            ratios.append(_shown_width(wide) / _shown_width(square))

            um_per_px = frame_w / axes[0].get_window_extent().width
            expected_bar = scale_bar_um / um_per_px
            computed_bar = (scale_bar_um / frame_w) * axes[0].get_position().width * fig.bbox.width
            assert computed_bar == pytest.approx(expected_bar, abs=1)
        finally:
            plt.close(fig)

    assert ratios[0] == pytest.approx(3, rel=0.02)
    assert ratios[1] == pytest.approx(ratios[0], rel=0.02)


def test_scale_bar_keeps_its_length_when_the_slot_is_at_the_edge():
    span = CompositeApp._scale_bar_span_px(center_px=180, bar_length_px=100, image_width=200)
    assert span == (100, 200)
    assert CompositeApp._scale_bar_span_px(10, 100, 200) == (0, 100)
    assert CompositeApp._scale_bar_span_px(100, 250, 200) is None
