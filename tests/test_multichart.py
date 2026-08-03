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

    def test_legends_survive_composition(self):
        # hconcat defaults legends to shared and DROPS them when the panels' color scales
        # cannot merge, so multichart resolves color independently. Rendered, not inspected:
        # the spec keeps both encodings either way - only the render shows the loss.
        import re

        import vl_convert as vlc

        theme()

        def colored(pal):
            df = pl.DataFrame({"g": ["A", "B"], "v": [1.0, 2.0]})
            return lambda: (
                alt.Chart(df).mark_bar().encode(x="g:N", y="v:Q", color=alt.Color("g:N", scale=alt.Scale(range=pal)))
            )

        figure = multichart([(colored(["#111111", "#222222"]), 60, 40), (colored(["#888888", "#999999"]), 60, 40)])
        assert re.findall("role-legend", vlc.vegalite_to_svg(figure.to_json())), "legends dropped by the concat"


class TestFigureLabels:
    def test_fourth_element_labels_the_chart(self):
        theme()
        spec = multichart([(_chart, 60, 40, "a"), (_chart, 60, 40)]).to_dict()
        first, second = spec["hconcat"]
        assert first["title"]["text"] == "a"
        assert first["vconcat"][0]["width"] == 60, "the label rides a wrapper, chart size intact"
        assert "title" not in second, "a member without a fourth element gets no label"

    def test_text_is_verbatim(self):
        theme()
        spec = multichart([(_chart, 60, 40, "B")]).to_dict()
        assert spec["title"]["text"] == "B", "no case transformation"

    def test_anchors_top_left_in_bold_by_default(self):
        theme()
        title = multichart([(_chart, 60, 40, "a")]).to_dict()["title"]
        assert title["anchor"] == "start"
        assert (title["fontSize"], title["fontWeight"]) == (8, 700)

    def test_color_is_left_to_the_theme_by_default(self):
        # config.title.color is darkmode-aware and resolved when the spec is written, so a
        # save() across both backgrounds gets the right ink without a callable.
        theme()
        assert "color" not in multichart([(_chart, 60, 40, "a")]).to_dict()["title"]
        spec = multichart([(_chart, 60, 40, "a")], labelColor="#ff0000").to_dict()
        assert spec["title"]["color"] == "#ff0000"

    def test_padding_offsets_the_label(self):
        theme()
        default = multichart([(_chart, 60, 40, "a")]).to_dict()["title"]
        assert (default["dx"], default["dy"]) == (-5, 0), "held off the chart like axisOffset"
        one = multichart([(_chart, 60, 40, "a")], labelPadding=3).to_dict()["title"]
        assert (one["dx"], one["dy"]) == (3, 3)
        two = multichart([(_chart, 60, 40, "a")], labelPadding=(-4, 2)).to_dict()["title"]
        assert (two["dx"], two["dy"]) == (-4, 2)

    def test_chart_keeps_its_own_title(self):
        # the label rides a wrapper, so it does not consume the chart's title slot
        theme()

        def titled():
            return _chart().properties(title="Real title")

        spec = multichart([(titled, 60, 40, "a")]).to_dict()
        assert spec["title"]["text"] == "a"
        assert spec["vconcat"][0]["title"] == "Real title"

    def test_anchors_to_the_whole_chart_not_the_plot_area(self):
        # frame="bounds" measures the full bounding box, so the label clears the y-axis
        # labels; frame="group" would stop at the plot area (measured: x=44 vs x=6).
        theme()
        assert multichart([(_chart, 60, 40, "a")]).to_dict()["title"]["frame"] == "bounds"


class TestDictMembers:
    def test_dict_member_matches_the_tuple_form(self):
        theme()
        as_tuple = multichart([(_chart, 60, 40, "a")]).to_dict()
        as_dict = multichart([{"chart": _chart, "width": 60, "height": 40, "label": "a"}]).to_dict()
        assert as_dict == as_tuple

    def test_only_chart_is_required(self):
        theme(chartWidth=123)
        spec = multichart([{"chart": _chart}]).to_dict()
        assert "width" not in spec, "no stamp - it inherits config.view"
        theme()

    def test_dict_takes_a_prebuilt_chart(self):
        theme()
        spec = multichart([{"chart": _chart().properties(width=42, height=17), "label": "a"}]).to_dict()
        assert spec["title"]["text"] == "a"
        assert spec["vconcat"][0]["width"] == 42

    def test_unknown_key_raises(self):
        theme()
        with pytest.raises(ValueError, match="unknown"):
            multichart([{"chart": _chart, "wdith": 60}])

    def test_missing_chart_key_raises(self):
        theme()
        with pytest.raises(ValueError, match="needs a 'chart' key"):
            multichart([{"width": 60, "height": 40}])

    def test_sizing_a_prebuilt_chart_raises(self):
        # its derived pixel values are already baked, so a size could not be honored
        theme()
        with pytest.raises(ValueError, match="already-built chart"):
            multichart([{"chart": _chart(), "width": 60, "height": 40}])

    def test_wrong_length_tuple_raises(self):
        theme()
        with pytest.raises(ValueError, match="member tuple must be"):
            multichart([(_chart, 60)])


class TestBlankSlots:
    def test_none_reserves_space(self):
        theme()
        spec = multichart([(None, 120, 80), (_chart, 60, 40)]).to_dict()
        blank = spec["hconcat"][0]
        assert (blank["width"], blank["height"]) == (120, 80)
        assert blank["mark"]["opacity"] == 0

    def test_blank_can_be_labelled(self):
        theme()
        spec = multichart([(None, 120, 80, "a")]).to_dict()
        assert spec["title"]["text"] == "a"

    def test_blank_dict_form(self):
        theme()
        as_tuple = multichart([(None, 120, 80, "a")]).to_dict()
        as_dict = multichart([{"chart": None, "width": 120, "height": 80, "label": "a"}]).to_dict()
        assert as_dict == as_tuple

    def test_blank_data_is_internal(self, tmp_path):
        # a reserved slot is not part of the figure's data of record
        import dysonsphere as ds

        theme()
        ds.save(multichart([(None, 120, 80), (_chart, 60, 40)]), str(tmp_path / "fig"), format="json")
        frame = ds.read(str(tmp_path / "fig.json"), what="data")
        assert list(frame.columns) == ["g", "v"], "the blank must not surface as a user frame"


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
