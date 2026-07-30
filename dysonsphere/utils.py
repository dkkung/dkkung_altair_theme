import hashlib
import json
import math
from collections.abc import Sequence
from typing import Any, NamedTuple

import polars as pl

from .theme import _opt

# The module's public API - star-imported into the dysonsphere namespace. Everything
# else here is internal (underscore or not); keep this list in sync with __init__.__all__.
__all__ = ["BandGeometry", "band_geometry", "count_n", "ensure_polars", "frame_checksum"]


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
      ``xOffset`` encoding (``mark_circle``/``mark_strip``) or an ``add_shade`` rect sees.
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


def _nice_domain(lo: float, hi: float, count: int = 10) -> tuple[float, float]:
    """Round ``(lo, hi)`` outward to nice tick-increment multiples - d3's ``nice()`` algorithm.

    Used by ``add_labels`` to pin the shared scale to nice bounds instead of the raw data extent,
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


def count_n(df: pl.DataFrame, xCol: str, categories: list[str]) -> list[int]:
    """
    Count the number of rows in ``df`` belonging to each category.

    Parameters
    ----------
    df:
        A ``polars.DataFrame`` or ``pandas.DataFrame``.
    xCol:
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

        counts = ds.count_n(df, "group", ["Control", "Group A", "Group B"])
        # [12, 15, 11]
    """
    df = ensure_polars(df)
    return [len(df.filter(pl.col(xCol) == cat)) for cat in categories]


def ensure_polars(df: pl.DataFrame) -> pl.DataFrame:
    """
    Convert a pandas DataFrame to Polars, or pass a Polars DataFrame through unchanged.

    Accepts either a ``polars.DataFrame`` or a ``pandas.DataFrame`` without
    requiring pandas as a hard dependency — the check is done via the module
    name only.  If ``df`` is neither, a ``TypeError`` is raised.

    Parameters
    ----------
    df:
        A ``polars.DataFrame`` or ``pandas.DataFrame``.

    Returns
    -------
    polars.DataFrame
        The original DataFrame if already Polars, otherwise the result of
        ``polars.from_pandas(df)``.

    Examples
    --------
    ::

        import pandas as pd
        pdf = pd.DataFrame({"group": ["A", "B"], "value": [1.0, 2.0]})
        pldf = ds.ensure_polars(pdf)  # returns a polars.DataFrame
    """
    if isinstance(df, pl.DataFrame):
        return df
    if type(df).__module__.startswith("pandas"):
        return pl.from_pandas(df)
    raise TypeError(f"Expected a polars.DataFrame or pandas.DataFrame, got {type(df).__name__}.")


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


def _hash_rows(rows: list[dict[str, Any]]) -> str:
    """Order-independent ``sha256:<hex>`` of a list of record dicts.

    Hashes the *multiset* of per-row canonical-JSON digests (sort the digests, then hash), so a
    reordered-but-identical set yields the same value; duplicate rows are preserved.  The single
    implementation shared by the provenance ``dataChecksum`` (over a spec's inlined datasets) and
    ``frame_checksum`` (over a raw dataframe), so both compute identical values for identical rows.
    Every row goes through :func:`_canonicalize` first, so a missing value and a dtype change
    cannot alter the digest; ``default=str`` then keeps it total for non-JSON-native cell types
    (dates, Decimals).
    """
    digests = sorted(
        hashlib.sha256(
            json.dumps(
                _canonicalize(r), sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
            ).encode()
        ).hexdigest()
        for r in rows
    )
    return "sha256:" + hashlib.sha256(json.dumps(digests, separators=(",", ":")).encode()).hexdigest()


def frame_checksum(df: "pl.DataFrame | Any") -> str:
    """Order-independent ``sha256:<hex>`` fingerprint of a dataframe's rows.

    Same algorithm as the provenance ``dataChecksum`` (via :func:`_hash_rows`), so identical
    content in any row order yields the same value.  Used to tag a statistics record with the
    identity of the dataframe it was computed from, so records from distinct dataframes are
    distinguishable (and identical-content frames match regardless of ordering).
    """
    return _hash_rows(ensure_polars(df).to_dicts())


# ── Internal-data sentinel ───────────────────────────────────────────────────
# dysonsphere's composite marks / annotations generate their own small "sidecar" data
# (bracket coords, mean/error bars, KDE curves, labels, …).  Altair inlines each of those
# as a separate named dataset in the saved spec, alongside the user's dataframe.  To let
# export.read(what="data") return only the USER's frame(s), every internal data source is
# tagged with this sentinel column; read() treats any dataset carrying it as internal.
#
# DISCIPLINE: any NEW code that builds a dysonsphere-generated data source for a chart layer
# MUST route it through `_internal_data(...)` (i.e. `alt.Chart(_internal_data(rows_or_df))`).
# Miss one, and that sidecar leaks as a phantom "user" dataframe on read.  See CLAUDE.md.
_INTERNAL_COL = "__dysonsphere__"

# Unicode superscript digits 0-9 - the SINGLE source for every notation label that renders an
# exponent: nonlinear.log_label_expr (10ⁿ / bⁿ log labels), inference._superscript (p-value
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
