import hashlib
import json
import math
from collections.abc import Sequence
from typing import Any, NamedTuple

import polars as pl

from .theme import _opt

# The public ds.utils API. Everything else here is internal (underscore or not).
__all__ = ["BandGeometry", "band_geometry", "count_n", "ensure_polars"]


class BandGeometry(NamedTuple):
    """Pixel geometry of an n-category band axis - see :func:`band_geometry`."""

    step: float
    centers: tuple[float, ...]
    starts: tuple[float, ...]
    ends: tuple[float, ...]


def band_geometry(
    n: int,
    span: float | None = None,
    *,
    scale: str = "offset",
    bandPadding: float | None = None,
) -> BandGeometry:
    """
    Compute the pixel geometry of an ``n``-category band axis - the single source of
    truth for dysonsphere's band-position math (violin centres, shade rects, bracket
    midpoints, multilabel spans).

    Vega-Lite lowers a nominal axis to a D3 band scale whose step size depends on the
    padding configuration, which differs by mark type. ``scale`` picks the variant, each
    resolving its inner padding from the matching theme key (outer is one shared key,
    ``outerPadding``, because Vega-Lite has no mark-specific outer padding):

    - ``"offset"`` (default) - ``paddingInner=0``, ``paddingOuter=outerPadding``: what an
      ``xOffset`` encoding (``mark_circle``/``mark_strip``) or a ``shade`` rect sees.
    - ``"band"`` - ``paddingInner=barPadding``: what ``mark_bar`` sees.
    - ``"rect"`` - ``paddingInner=rectPadding`` (``0`` by default, so cells abut): what a
      ``mark_rect`` heatmap sees - and also ``mark_boxplot`` (and so ``mark_violin``'s
      embedded boxplot), since Vega-Lite routes "rect and other marks" through the one key.
    - ``"point"`` - a point scale: ``step = span / n``; centre ``i`` is ``step*(0.5+i)``
      (``starts``/``ends`` equal ``centers``).

    For every variant but ``"point"``, ``step = span / (n - inner + 2*outer)``, band ``i``
    starts at ``step*(outer+i)`` and is ``step*(1-inner)`` wide.

    Parameters
    ----------
    n:
        Number of categories.
    span:
        Pixel extent of the axis. ``None`` (default) reads ``chartWidth`` from the
        active theme (pass ``chartHeight`` explicitly for a y-axis).
    scale:
        ``"offset"``, ``"band"``, ``"rect"``, or ``"point"`` (see above).
    bandPadding:
        Override for the outer padding, and for ``scale="band"`` the inner padding too
        (the variant where the two are equal by construction). ``None`` (default) reads
        the active theme.

    Returns
    -------
    BandGeometry
        A named tuple ``(step, centers, starts, ends)``, each position list in
        category-index order.
    """

    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    if span is None:
        span = _opt("chartWidth")
    if scale == "point":
        step = span / n
        centers = tuple(step * (0.5 + i) for i in range(n))
        return BandGeometry(step, centers, centers, centers)
    if scale == "offset":
        inner = 0.0
    elif scale == "band":
        inner = _opt("barPadding") if bandPadding is None else bandPadding
    elif scale == "rect":
        inner = _opt("rectPadding")
    else:
        raise ValueError(f"scale must be 'offset', 'band', 'rect', or 'point', got {scale!r}")
    outer = _opt("outerPadding") if bandPadding is None else bandPadding

    step = span / (n - inner + 2 * outer)
    width = step * (1 - inner)
    starts = tuple(step * (outer + i) for i in range(n))
    centers = tuple(s + width / 2 for s in starts)
    ends = tuple(s + width for s in starts)
    return BandGeometry(step, centers, starts, ends)


def _nested_band_centers(nCategories: int, nLevels: int, span: float | None = None) -> list[list[float]]:
    """Pixel centres of every sub-bar in a grouped (``xOffset``) chart, as ``[category][level]``.

    A nested offset scale uses its own padding keys, not the mark-specific ones: the outer band
    takes ``groupPadding`` (Vega-Lite's ``bandWithNestedOffsetPadding``) and the offset scale
    inside it takes ``subgroupPadding`` (``offsetBandPadding``). Composing ``band_geometry`` with
    each reproduces Vega's rendered sub-bar positions exactly (verified against rendered SVG for
    2-5 levels and 2-3 categories); ``band_geometry``'s own ``"band"``/``"offset"`` variants do
    NOT, because they resolve ``barPadding``/``outerPadding`` instead.
    """
    span = float(_opt("chartWidth")) if span is None else span
    outer = band_geometry(nCategories, span, scale="band", bandPadding=float(_opt("groupPadding")))
    sub = float(_opt("subgroupPadding"))
    out: list[list[float]] = []
    for i in range(nCategories):
        width = outer.ends[i] - outer.starts[i]
        inner = band_geometry(nLevels, width, scale="band", bandPadding=sub)
        out.append([outer.starts[i] + c for c in inner.centers])
    return out


def _nice_domain(lo: float, hi: float, count: int = 10) -> tuple[float, float]:
    """Round ``(lo, hi)`` outward to nice tick-increment multiples - d3's ``nice()`` algorithm.

    Used by ``labels`` to pin the shared scale to nice bounds instead of the raw data extent,
    so the pinned axes read like Vega's own ``nice: true`` (whose rounding this replicates: the
    d3-scale 1/2/5/10 tick increment at ``count`` ~ticks, applied twice so the widened domain can
    settle on a coarser step). Exactness vs Vega does not matter - the caller FORCES the returned
    domain, so whatever this computes is what renders. Degenerate spans return unchanged.
    """
    import math

    if not (hi > lo):
        return lo, hi
    for _ in range(2):
        step = (hi - lo) / count
        power = 10.0 ** math.floor(math.log10(step))
        err = step / power
        # d3's tickIncrement thresholds: sqrt(50), sqrt(10), sqrt(2)
        step = power * (10 if err >= math.sqrt(50) else 5 if err >= math.sqrt(10) else 2 if err >= math.sqrt(2) else 1)
        lo2, hi2 = math.floor(lo / step) * step, math.ceil(hi / step) * step
        if (lo2, hi2) == (lo, hi):
            break
        lo, hi = lo2, hi2
    return lo, hi


def count_n(data: pl.DataFrame, column: str, categories: list[str]) -> list[int]:
    """
    Count the number of rows in ``data`` belonging to each category.

    Parameters
    ----------
    data:
        A ``polars.DataFrame`` or ``pandas.DataFrame``.
    column:
        Column name used for grouping (the x-axis column).
    categories:
        Ordered list of category labels; the returned counts follow this order.
        Categories with no matching rows return 0.

    Returns
    -------
    list[int]
        Per-category row counts in the same order as ``categories``.

    Examples
    --------
    ::

        counts = ds.utils.count_n(data, "group", ["Control", "Group A", "Group B"])
        # [12, 15, 11]
    """
    data = ensure_polars(data)
    return [len(data.filter(pl.col(column) == cat)) for cat in categories]


def ensure_polars(data: pl.DataFrame) -> pl.DataFrame:
    """
    Convert a pandas DataFrame to Polars, or pass a Polars DataFrame through unchanged.

    Accepts either a ``polars.DataFrame`` or a ``pandas.DataFrame`` without
    requiring pandas as a hard dependency — the check is done via the module
    name only.  If ``data`` is neither, a ``TypeError`` is raised.

    Parameters
    ----------
    data:
        A ``polars.DataFrame`` or ``pandas.DataFrame``.

    Returns
    -------
    polars.DataFrame
        The original DataFrame if already Polars, otherwise the result of
        ``polars.from_pandas(data)``.

    Examples
    --------
    ::

        import pandas as pd
        pdf = pd.DataFrame({"group": ["A", "B"], "value": [1.0, 2.0]})
        pldf = ds.utils.ensure_polars(pdf)  # returns a polars.DataFrame
    """
    if isinstance(data, pl.DataFrame):
        return data
    if type(data).__module__.startswith("pandas"):
        return pl.from_pandas(data)
    raise TypeError(f"Expected a polars.DataFrame or pandas.DataFrame, got {type(data).__name__}.")


def _walk(value: Any, scalar) -> Any:
    """Apply ``scalar`` to every leaf of a nested dict/list structure."""
    if isinstance(value, dict):
        return {k: _walk(v, scalar) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_walk(v, scalar) for v in value]
    return scalar(value)


def _json_safe(value: Any) -> Any:
    """Replace non-finite floats with ``None``, recursively - for data that gets WRITTEN.

    ``json.dumps`` renders ``NaN``/``Infinity`` as bare tokens, which are a Python extension and
    not valid JSON: a strict parser (a browser's ``JSON.parse``, ``jq``, ``serde_json``) rejects
    the file.  ``null`` is what Vega-Lite uses for a missing value, and what vl-convert already
    writes into the HTML export - so this makes the JSON agree with its sibling formats.

    Deliberately does NOT touch anything else.  In particular it leaves ``1.0`` as a float, so a
    ``Float64`` column survives a ``save()`` -> ``read(what="data")`` round-trip as ``Float64``;
    collapsing it to ``1`` is a *hashing* concern only (see :func:`_canonicalize`).
    """
    return _walk(value, lambda v: None if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) else v)


def _canonicalize(value: Any) -> Any:
    """Normalize a value so equal data HASHES identically - never used for written output.

    Two spellings of one value would otherwise digest differently:

    - **Non-finite floats become ``None``**, so a missing value has one representation
      (matching :func:`_json_safe`, and making ``NaN`` and ``null`` agree - both mean absent).
    - **Integral floats become ints**, so an ``Int64`` column and a ``Float64`` column holding
      the same values agree.  Matches RFC 8785 (JSON Canonicalization Scheme), where ``1.0``
      serializes as ``1``.  Without this a dtype change alone would alter a data checksum,
      defeating the point of a checksum that is meant to identify data independently of how it
      was drawn.

    Non-JSON-native types (dates, Decimals) are left alone and handled by ``_hash_rows``'s
    ``default=str``, so their digest still depends on Python's ``str()``.
    """

    def _scalar(v: Any) -> Any:
        if isinstance(v, float):
            if math.isnan(v) or math.isinf(v):
                return None
            return int(v) if v.is_integer() else v
        return v

    return _walk(value, _scalar)


_ROW_HASH_PREFIX = "multiset-sha256:"


def _hash_rows(rows: list[dict[str, Any]]) -> str:
    """Order-independent ``multiset-sha256:<hex>`` of a list of record dicts.

    Hashes the *multiset* of per-row canonical-JSON digests (sort the digests, then hash), so a
    reordered-but-identical set yields the same value; duplicate rows are preserved.  The single
    implementation shared by the provenance ``dataChecksum`` (over a spec's inlined datasets) and
    ``metadata.frame_checksum`` (over a raw dataframe), so both compute identical values for identical rows.
    Every row goes through :func:`_canonicalize` first, so a missing value and a dtype change
    cannot alter the digest; ``default=str`` then keeps it total for non-JSON-native cell types
    (dates, Decimals).

    The prefix names the *construction*, not just the hash function.  A bare ``sha256:`` means
    SHA-256 over an artifact's bytes everywhere it is used as a digest label (OCI, in-toto,
    Frictionless), and this is not that - it is a multiset hash, so it cannot be reproduced by
    hashing the file.  ``vegaliteChecksum`` does hash bytes and keeps the plain ``sha256:``.
    """
    digests = sorted(
        hashlib.sha256(
            json.dumps(
                _canonicalize(r), sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
            ).encode()
        ).hexdigest()
        for r in rows
    )
    return _ROW_HASH_PREFIX + hashlib.sha256(json.dumps(digests, separators=(",", ":")).encode()).hexdigest()


def _frame_checksum(data: "pl.DataFrame | Any") -> str:
    """Order-independent ``multiset-sha256:<hex>`` fingerprint of a dataframe's rows.

    Same algorithm as the provenance ``dataChecksum`` (via :func:`_hash_rows`), so identical
    content in any row order yields the same value.  Used to tag a statistics record with the
    identity of the dataframe it was computed from, so records from distinct dataframes are
    distinguishable (and identical-content frames match regardless of ordering).
    """
    return _hash_rows(ensure_polars(data).to_dicts())


# ── Internal-data sentinel ───────────────────────────────────────────────────
# dysonsphere's composite marks / annotations generate their own small "sidecar" data
# (bracket coords, mean/error bars, KDE curves, labels, …).  Altair inlines each of those
# as a separate named dataset in the saved spec, alongside the user's dataframe.  To let
# metadata.read(what="data") return only the USER's frame(s), every internal data source is
# tagged with this sentinel column; read() treats any dataset carrying it as internal.
#
# DISCIPLINE: any NEW code that builds a dysonsphere-generated data source for a chart layer
# MUST route it through `_internal_data(...)` (i.e. `alt.Chart(_internal_data(rows_or_df))`).
# Miss one, and that sidecar leaks as a phantom "user" dataframe on read.  See AGENTS.md.
_INTERNAL_COL = "__dysonsphere__"

# Marks a `shade` background rect so `export._layer_axes_below_marks` can sink it behind the
# grid and axes. Deliberately NOT the `__dysonsphere_` prefix: `metadata._strip_markers` deletes
# that from written output, which would break the fixer after a `ds.load()` round trip.
_SHADE_PREFIX = "__dsshade_"

# Unicode superscript digits 0-9 - the SINGLE source for every notation label that renders an
# exponent: nonlinear.log_label_expr (10ⁿ / bⁿ log labels), stats._superscript (p-value
# ×10ⁿ), and table.py power/scientific columns all index this string. export._fix_superscript_labels
# reverses it (and the superscript minus ⁻) back to raised ASCII at render time - see its design
# point. Kept here (no Altair dependency, imported by all four) so it can't drift between copies.
_SUP = "⁰¹²³⁴⁵⁶⁷⁸⁹"


def _internal_data(data: "list[dict[str, Any]] | pl.DataFrame | Any") -> "Any":
    """Tag dysonsphere-generated (non-user) chart data with the internal sentinel column.

    Accepts a list of record dicts (returned as an ``alt.Data``) or a polars/pandas
    DataFrame (returned as a polars DataFrame with the sentinel column added).  Pass the
    result straight to ``alt.Chart(...)``.
    """
    import altair as alt

    if isinstance(data, list):
        return alt.Data(values=[{**dict(row), _INTERNAL_COL: 1} for row in data])
    return ensure_polars(data).with_columns(pl.lit(1).alias(_INTERNAL_COL))


def _empty_layer() -> "Any":
    """An invisible placeholder layer, for an annotation with nothing to draw.

    Returned so the annotation still composes with ``+`` (``alt.layer()`` requires at least
    one layer). Rides on a tagged internal frame, so ``read(what="data")`` filters it.
    """
    import altair as alt

    return alt.Chart(_internal_data([{}])).mark_point(opacity=0)


def _resolve_dash(value: "bool | Sequence[int | float] | None") -> "list[int | float] | None":
    """Resolve the project-wide ``strokeDash`` convention to a concrete dash array.

    ``True`` -> the theme's ``dashedWidth`` pattern; ``False`` -> ``[0, 0]`` (forced solid);
    a list -> passed through unchanged; ``None`` -> ``None`` (the caller decides what unset
    means - typically omitting the property so the theme config applies).
    """
    if value is True:
        return _opt("dashedWidth")
    if value is False:
        return [0, 0]
    return list(value) if value is not None else None


_CONTINUOUS_TYPES = ("quantitative", "temporal")
_SPEC_CONTAINERS = ("layer", "hconcat", "vconcat", "concat")


def _suppress_nice(spec: dict[str, Any]) -> dict[str, Any]:
    """Turn ``nice`` off on continuous x/y scales so ``viewPadding`` lands exactly.

    Vega pads the domain and *then* nices it, so the rounding compounds the inset: a
    ``viewPadding`` of 15 px renders as 19.7 px at one end and 30 px at the other, and a
    non-negative field can gain a ``-1`` tick where the padded bound crossed zero. Dropping
    ``nice`` while padding is active makes the padding alone set the bounds, so the inset is
    exactly what was asked for and the axis stops where the data does.

    Never overrides an explicit user ``nice``. Mutates *spec* in place and returns it.
    """
    encoding = spec.get("encoding")
    if isinstance(encoding, dict):
        for channel in ("x", "y"):
            channel_def = encoding.get(channel)
            if not isinstance(channel_def, dict) or channel_def.get("type") not in _CONTINUOUS_TYPES:
                continue
            scale = channel_def.get("scale")
            if scale is None:
                scale = channel_def["scale"] = {}
            if isinstance(scale, dict) and "nice" not in scale:
                scale["nice"] = False
    for key in _SPEC_CONTAINERS:
        children = spec.get(key)
        if isinstance(children, list):
            for child in children:
                if isinstance(child, dict):
                    _suppress_nice(child)
    child_spec = spec.get("spec")
    if isinstance(child_spec, dict):
        _suppress_nice(child_spec)
    return spec


def _apply_spec_fixes(spec: dict[str, Any]) -> dict[str, Any]:
    """Run the spec-level transforms shared by every output format.

    Kept as one call so every path that resolves a chart to a spec applies the same transforms:
    ``save``'s JSON/HTML spec, ``_render_fixed_svg``'s SVG/PNG spec, ``metadata``'s checksum path
    and the website's example generator. Lives here rather than in ``export`` so ``metadata`` can
    call it without importing ``export`` - that dependency runs one way only.

    The nice-suppression is gated on ``continuousPadding`` being present IN THE SPEC, not on the
    theme flags that currently imply it (``viewPadding and closed``). Padding is what ``nice``
    conflicts with, so reading the emitted value tracks whatever ``theme.py`` decides to emit -
    including a future default that pads open plots - with no condition to keep in sync.
    """
    if spec.get("config", {}).get("scale", {}).get("continuousPadding"):
        _suppress_nice(spec)
    return spec


def resolve_palette(name_or_list: "str | list[str]") -> list[str]:
    """A palette name → its hex list (via ``colors``), or a hex list passed straight through."""
    if isinstance(name_or_list, list):
        return name_or_list
    from .palettes import colors

    if name_or_list not in colors:
        raise ValueError(f"unknown palette {name_or_list!r}")
    return colors[name_or_list]


def stripe_colors(palette: "str | list[str]", n: int, *, darkmode: bool) -> list[str]:
    """The ``n`` row-striping fills from *palette* - its lightest ``n`` stops, or its darkest in
    darkmode, since a sequential palette runs light to dark.

    Shared by ``mark_table``'s cell stripes and ``add_multilabel``'s row bands. NOT used by
    ``shade``, whose darkmode deliberately discards the caller's palette for greys.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}.")
    pal = resolve_palette(palette)
    return pal[-n:] if darkmode else pal[:n]
