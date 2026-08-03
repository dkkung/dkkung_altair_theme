from typing import Any

import altair as alt

from .export import _AltairChart
from .theme import _active_args, theme

# The module's public API - star-imported into the dysonsphere namespace. Everything
# else here is internal (underscore or not); keep this list in sync with __init__.__all__.
__all__ = ["multichart"]

# A member is a builder, a builder with its size, or an already-built chart.
_Member = Any
_Spacing = float | dict[str, float] | None


def _build(member: _Member) -> _AltairChart:
    """Build one member at its own size, then stamp that size on the chart."""
    if not callable(member) and not isinstance(member, tuple):
        return member  # already a chart - the caller fixed its size when they built it
    fn, width, height = (member, None, None) if callable(member) else member
    overrides = {k: v for k, v in (("chartWidth", width), ("chartHeight", height)) if v is not None}
    if not overrides:
        return fn()
    prev = _active_args()  # explicit args, so derived options re-derive at the new size
    theme(**{**prev, **overrides})
    try:
        chart = fn()
    finally:
        theme(**prev)
    size = {p: overrides[k] for k, p in (("chartWidth", "width"), ("chartHeight", "height")) if k in overrides}
    return chart.properties(**size)


def _spacing_kwargs(gap: float | None) -> dict[str, float]:
    return {} if gap is None else {"spacing": gap}


def multichart(members: list[_Member], *, spacing: _Spacing = None) -> _AltairChart:
    """
    Compose several charts into one figure, each built at its own size.

    Charts in one figure share a single ``config.view``, so :func:`theme` alone cannot give
    them different sizes - the last call wins. Sizing with ``.properties()`` instead leaves
    ``markSize``, the corner and arc radii, and the pixel geometry of every annotation
    (``add_shade`` spans, comparison brackets, ``add_labels`` placement) computed for the
    theme's size rather than the one the chart renders at. ``multichart`` builds each member
    while the theme genuinely says its size, so those all land correctly, then stamps the
    size on the chart so the shared config cannot override it.

    Size only: Vega-Lite's ``config`` is spec-level, so palettes, fonts and axis styling
    cannot differ between charts in one figure. Set those on the encoding instead - e.g.
    ``alt.Color(..., scale=alt.Scale(range=ds.palette("ds_cat_2", 3)))`` - which is per-view
    and survives. Scales are not shared: concat resolves them independently already.

    Parameters
    ----------
    members:
        The charts, in layout order. Each is a ``(builder, width, height)`` tuple, a bare
        zero-argument builder (built at the theme's current size), or an already-built chart
        (used as-is, so a ``multichart`` result can nest inside another). Nest lists to make
        rows: ``[[a, b], [c, d]]`` is two rows of two, a flat list is a single row.
    spacing:
        Gap between charts in pixels - a number for both directions, or
        ``{"row": 40, "column": 10}`` to set them independently. ``None`` uses Vega-Lite's
        default.

    Returns
    -------
    An Altair concat chart, so ``.resolve_scale()``, ``.properties()`` and further nesting
    all work on the result.

    Examples
    --------
    A wide time course beside a narrow endpoint comparison::

        figure = ds.multichart(
            [(time_course, 210, 130), (endpoint_quant, 95, 130)],
            spacing=34,
        )

    Two rows, with more room between the rows than within them::

        figure = ds.multichart(
            [
                [(time_course, 190, 110), (endpoint_quant, 90, 110)],
                [(heatmap, 130, 110), (activity_fit, 150, 110)],
            ],
            spacing={"row": 40, "column": 10},
        )
    """
    if not members:
        raise ValueError("multichart() needs at least one member")
    if isinstance(spacing, dict):
        unknown = set(spacing) - {"row", "column"}
        if unknown:
            raise ValueError(f"spacing keys must be 'row' and/or 'column', got {sorted(unknown)}")
        row_gap, column_gap = spacing.get("row"), spacing.get("column")
    else:
        row_gap = column_gap = spacing

    rows = members if isinstance(members[0], list) else [members]
    built: list[_AltairChart] = []
    for row in rows:
        if not isinstance(row, list):
            raise ValueError("mix of rows and bare members - nest every row in its own list, or nest none")
        if not row:
            raise ValueError("multichart() rows cannot be empty")
        charts = [_build(m) for m in row]
        built.append(charts[0] if len(charts) == 1 else alt.hconcat(*charts, **_spacing_kwargs(column_gap)))
    return built[0] if len(built) == 1 else alt.vconcat(*built, **_spacing_kwargs(row_gap))
