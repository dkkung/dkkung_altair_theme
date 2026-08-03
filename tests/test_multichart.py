import altair as alt
import polars as pl
import pytest

from dysonsphere import multichart
from dysonsphere.theme import _opt, theme


def _chart():
    df = pl.DataFrame({"g": ["A"] * 6 + ["B"] * 6, "v": [1.0 + i * 0.1 for i in range(12)]})
    return alt.Chart(df).mark_point().encode(x="g:N", y="v:Q")


class TestMultichartSizing:
    """Each member is built while the theme genuinely says its size."""

    def test_derived_options_recompute_at_the_member_size(self):
        # The reason multichart re-runs theme() instead of poking alt.theme.options: markSize and
        # the corner/arc radii derive from min(chartWidth, chartHeight) and must follow the member.
        theme()
        seen = []

        def build():
            seen.append(_opt("markSize"))
            return _chart()

        multichart([(build, 200, 200), (build, 100, 100)])
        assert seen == [20.0, 10.0]
        assert _opt("markSize") == 10.0, "must restore"

    def test_stamps_width_and_height_per_member(self):
        theme()
        spec = multichart([(_chart, 200, 150), (_chart, 60, 40)]).to_dict()
        first, second = spec["hconcat"]
        assert (first["width"], first["height"]) == (200, 150)
        assert (second["width"], second["height"]) == (60, 40)

    def test_bare_builder_uses_the_theme_size(self):
        theme(chartWidth=123, chartHeight=77)
        spec = multichart([_chart, (_chart, 60, 40)]).to_dict()
        assert "width" not in spec["hconcat"][0], "no stamp - it inherits config.view"
        assert spec["hconcat"][1]["width"] == 60
        theme()

    def test_prebuilt_chart_passes_through(self):
        theme()
        prebuilt = _chart().properties(width=42, height=17)
        spec = multichart([prebuilt, (_chart, 60, 40)]).to_dict()
        assert (spec["hconcat"][0]["width"], spec["hconcat"][0]["height"]) == (42, 17)

    def test_nested_multichart_result_is_a_valid_member(self):
        theme()
        row = multichart([(_chart, 60, 40), (_chart, 60, 40)])
        spec = multichart([[row], [(_chart, 90, 40)]]).to_dict()
        assert "hconcat" in spec["vconcat"][0]

    def test_restores_on_exception(self):
        theme()

        def boom():
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            multichart([(boom, 999, 999)])
        assert _opt("chartWidth") == 100

    def test_preserves_explicitly_set_theme_args(self):
        # multichart rebuilds from theme()'s call args, so a caller's explicit settings survive.
        theme(chartWidth=300, fontSize=9)
        seen = {}

        def build():
            seen["fontSize"] = _opt("fontSize")
            return _chart()

        multichart([(build, None, 200)])
        assert seen["fontSize"] == 9
        assert _opt("chartWidth") == 300 and _opt("fontSize") == 9
        theme()


class TestMultichartLayout:
    def test_flat_list_is_one_row(self):
        theme()
        spec = multichart([(_chart, 60, 40), (_chart, 60, 40)]).to_dict()
        assert "hconcat" in spec and "vconcat" not in spec

    def test_nested_lists_are_rows(self):
        theme()
        spec = multichart([[(_chart, 60, 40), (_chart, 60, 40)], [(_chart, 60, 40)]]).to_dict()
        assert len(spec["vconcat"]) == 2
        assert len(spec["vconcat"][0]["hconcat"]) == 2

    def test_single_member_returns_the_chart_itself(self):
        theme()
        spec = multichart([(_chart, 60, 40)]).to_dict()
        assert "hconcat" not in spec and "vconcat" not in spec
        assert spec["width"] == 60

    def test_scalar_spacing_applies_to_both_directions(self):
        theme()
        spec = multichart([[(_chart, 60, 40), (_chart, 60, 40)], [(_chart, 60, 40)]], spacing=12).to_dict()
        assert spec["spacing"] == 12
        assert spec["vconcat"][0]["spacing"] == 12

    def test_dict_spacing_sets_each_direction(self):
        theme()
        spec = multichart(
            [[(_chart, 60, 40), (_chart, 60, 40)], [(_chart, 60, 40)]],
            spacing={"row": 40, "column": 10},
        ).to_dict()
        assert spec["spacing"] == 40
        assert spec["vconcat"][0]["spacing"] == 10

    def test_scales_resolve_independently_without_asking(self):
        # concat already resolves scales independently - multichart must not inject a resolve.
        theme()
        spec = multichart([(_chart, 60, 40), (_chart, 60, 40)]).to_dict()
        assert "resolve" not in spec


class TestMultichartErrors:
    def test_empty_members(self):
        theme()
        with pytest.raises(ValueError, match="at least one member"):
            multichart([])

    def test_empty_row(self):
        theme()
        with pytest.raises(ValueError, match="rows cannot be empty"):
            multichart([[(_chart, 60, 40)], []])

    def test_mixed_rows_and_bare_members(self):
        theme()
        with pytest.raises(ValueError, match="nest every row"):
            multichart([[(_chart, 60, 40)], (_chart, 60, 40)])

    def test_unknown_spacing_key(self):
        theme()
        with pytest.raises(ValueError, match="row.*column"):
            multichart([(_chart, 60, 40)], spacing={"vertical": 10})
