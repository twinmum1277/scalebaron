import pytest


def _make_viewer_or_skip():
    try:
        import tkinter as tk
        from scalebaron.muaddata import MuadDataViewer
    except Exception as exc:
        pytest.skip(f"Tkinter environment not available: {exc}")
    root = tk.Tk()
    root.withdraw()
    viewer = MuadDataViewer(root)
    # Avoid heavy rendering/data requirements during tests
    viewer.view_single_map = lambda *args, **kwargs: None
    viewer.zstack_render_preview = lambda *args, **kwargs: None
    return viewer, root


def test_single_set_max_slider_limit_updates_bounds():
    viewer, root = _make_viewer_or_skip()
    try:
        # Ensure starting state is predictable
        viewer.single_max.set(10.0)
        viewer.max_slider_limit.set(5.5)

        viewer.set_max_slider_limit()

        # Max slider upper bound should be updated to entered value
        assert float(viewer.max_slider.cget('to')) == pytest.approx(5.5)
        # Min slider upper bound should match for consistency
        assert float(viewer.min_slider.cget('to')) == pytest.approx(5.5)
        # Current max value should be clamped down to new bound
        assert float(viewer.single_max.get()) == pytest.approx(5.5)
        # Entry reflects applied value
        assert float(viewer.max_slider_limit.get()) == pytest.approx(5.5)
    finally:
        root.destroy()


def test_single_set_max_slider_limit_rejects_below_min():
    viewer, root = _make_viewer_or_skip()
    try:
        # Default 'from' is 0, 'to' is 1 on init
        original_to = float(viewer.max_slider.cget('to'))
        viewer.max_slider_limit.set(-1)

        viewer.set_max_slider_limit()

        # Invalid input should be reset to current slider max
        assert float(viewer.max_slider_limit.get()) == pytest.approx(original_to)
        # Upper bounds remain unchanged
        assert float(viewer.max_slider.cget('to')) == pytest.approx(original_to)
        assert float(viewer.min_slider.cget('to')) == pytest.approx(original_to)
    finally:
        root.destroy()


def test_zstack_set_zmax_slider_limit_updates_bounds():
    viewer, root = _make_viewer_or_skip()
    try:
        viewer.zstack_max.set(9.0)
        viewer.zmax_slider_limit.set(4.2)

        viewer.set_zmax_slider_limit()

        # Max slider upper bound updated
        assert float(viewer.zmax_slider.cget('to')) == pytest.approx(4.2)
        # Min slider upper bound updated to match
        assert float(viewer.zmin_slider.cget('to')) == pytest.approx(4.2)
        # Current z-stack max value clamped
        assert float(viewer.zstack_max.get()) == pytest.approx(4.2)
    finally:
        root.destroy()


