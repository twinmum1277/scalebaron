import pytest

from scalebaron.scalebaron import CompositeApp


class _Flag:
    def __init__(self, value):
        self._value = value

    def get(self):
        return self._value


def _app(use_best, num_rows):
    app = CompositeApp.__new__(CompositeApp)
    app.use_best_layout = _Flag(use_best)
    app.num_rows = _Flag(num_rows)
    return app


def test_fixed_rows_are_capped_by_sample_count():
    app = _app(use_best=False, num_rows=5)
    assert app._composite_row_count(12) == 5
    assert app._composite_row_count(3) == 3
    assert app._layout_setting_text() == "5 rows"


def test_best_layout_ignores_rows_field():
    app = _app(use_best=True, num_rows=5)
    assert app._composite_row_count(12) == app._best_composite_rows(12)
    assert app._layout_setting_text() == "best layout (auto rows)"


def test_override_rows_wins_over_the_layout_setting():
    app = _app(use_best=True, num_rows=5)
    assert app._composite_row_count(12, override_rows=2) == 2


def test_rows_below_one_are_rejected():
    app = _app(use_best=False, num_rows=0)
    with pytest.raises(ValueError):
        app._layout_setting_text()
    with pytest.raises(ValueError):
        app._composite_row_count(4)
