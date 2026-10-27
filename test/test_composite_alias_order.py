from scalebaron.scalebaron import CompositeApp


def test_panels_sort_by_alias_numerically():
    app = CompositeApp.__new__(CompositeApp)
    app.sample_aliases = {
        "a": "16-1",
        "b": "4-1",
        "c": "46-1",
        "d": "6-1",
        "e": "40-1",
        "f": "22-1",
        "g": "34-1",
        "h": "28-1",
    }
    app.labels = ["a", "b", "c", "d", "e", "f", "g", "h"]
    app.matrices = [i for i in range(8)]

    app._order_panels_by_alias()

    assert [app.sample_aliases[s] for s in app.labels] == [
        "4-1", "6-1", "16-1", "22-1", "28-1", "34-1", "40-1", "46-1",
    ]
    assert app.matrices == [1, 3, 0, 5, 7, 6, 4, 2]


def test_panels_without_alias_sort_by_sample_id():
    app = CompositeApp.__new__(CompositeApp)
    app.sample_aliases = {}
    app.labels = ["s10", "s2"]
    app.matrices = ["ten", "two"]

    app._order_panels_by_alias()

    assert app.labels == ["s2", "s10"]
    assert app.matrices == ["two", "ten"]
