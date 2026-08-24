"""Pixel-space label placement - the pure geometry engine behind ``annotations.add_labels``.

No Altair imports here: everything takes and returns plain pixel coordinates, mirroring how
``statistics.py`` is the pure computation engine behind ``inference.py``. Placement is solved
outside the renderer (like ggrepel / adjustText / d3-labeler) because Vega-Lite has no
label-repel primitive; the wrapper feeds the results back to Altair as static positions.
"""

TARGET_GAP = 5.0
W_CROWD = 3.0
W_MARKER = 400.0
W_LABEL = 5000.0
W_DIR = 10.0
POINT_R = 3.0


def _repel_labels(
    anchors: list[tuple[float, float]],
    sizes: list[tuple[float, float]],
    *,
    width: float,
    height: float,
    obstacles: "list[tuple[float, float]] | None" = None,
    iterations: int = 300,
) -> list[tuple[float, float]]:
    """Nearest-clear-spot label placement (deterministic) - the engine behind :func:`add_labels`.

    ``anchors`` are the pixel positions of the points being labelled, ``sizes`` each label's
    ``(width, height)`` box, ``obstacles`` all plotted points to avoid covering (default:
    ``anchors``). Origin top-left, y growing downward. Returns one label-CENTRE position per anchor.

    Greedy takes the nearest ring with a clear spot and the roomiest candidate in it; 2-opt then
    swaps slot ownership and a move pass relocates single labels, alternating to convergence. Cost
    is connector length plus penalties for covering a marker (``W_MARKER``), crowding another label
    (``W_CROWD`` below ``TARGET_GAP``), and sitting inward of the mark (``W_DIR``). Never drops a
    label. ``iterations`` is unused (kept for call compatibility).
    """
    import numpy as np

    n = len(anchors)
    if n == 0:
        return []
    a = np.array(anchors, dtype=float)
    obs = np.array(obstacles if obstacles is not None else anchors, dtype=float)
    half = np.array(sizes, dtype=float) / 2.0 + 2.0
    centroid = obs.mean(axis=0)
    near_r = 0.3 * min(width, height)
    local = np.array([int((np.hypot(obs[:, 0] - a[i, 0], obs[:, 1] - a[i, 1]) < near_r).sum()) for i in range(n)])
    order = list(np.argsort(local, kind="stable"))
    radii = np.arange(0.0, 0.6 * float(np.hypot(width, height)), 1.5)
    base_ang = np.linspace(0.0, 2.0 * np.pi, 36, endpoint=False)

    def angles_for(idx):
        v = a[idx] - centroid
        if np.hypot(v[0], v[1]) < 0.05 * min(width, height):
            d = a[idx] - obs
            dist = np.hypot(d[:, 0], d[:, 1])
            m = (dist > 1e-9) & (dist < near_r)
            v = (d[m] * (1.0 / dist[m] ** 2)[:, None]).sum(axis=0) if m.any() else np.array([0.0, -1.0])
        oa = float(np.arctan2(v[1], v[0])) if np.hypot(v[0], v[1]) > 1e-9 else -np.pi / 2.0
        diff = np.abs((base_ang - oa + np.pi) % (2.0 * np.pi) - np.pi)
        return base_ang[np.argsort(diff, kind="stable")]

    # candidate grid per label, precomputed once (deterministic, outward-ordered)
    cand = {}
    for k in range(n):
        angs = angles_for(k)
        cx = a[k, 0] + np.outer(radii, np.cos(angs)).ravel()
        cy = a[k, 1] + np.outer(radii, np.sin(angs)).ravel()
        hw, hh = half[k]
        ok = (cx - hw >= 0) & (cx + hw <= width) & (cy - hh >= 0) & (cy + hh <= height)
        cand[k] = (cx[ok], cy[ok])

    def marker_hits_vec(k, cx, cy):
        hw, hh = half[k, 0] + POINT_R, half[k, 1] + POINT_R
        return ((np.abs(obs[None, :, 0] - cx[:, None]) < hw) & (np.abs(obs[None, :, 1] - cy[:, None]) < hh)).sum(1)

    def unary_vec(k, cx, cy):
        t = np.hypot(cx - a[k, 0], cy - a[k, 1]) + W_MARKER * marker_hits_vec(k, cx, cy)
        ox, oy = a[k, 0] - centroid[0], a[k, 1] - centroid[1]
        onrm = float(np.hypot(ox, oy))
        if onrm > 1e-9:
            inward = -((cx - a[k, 0]) * ox + (cy - a[k, 1]) * oy) / onrm
            t = t + W_DIR * np.maximum(inward, 0.0)
        return t

    def pair_vec(k, cx, cy, others, opos):
        """crowding cost of candidate positions for k against fixed labels `others`"""
        if not others:
            return np.zeros(len(cx))
        oc = np.array([opos[q] for q in others])
        oh = half[list(others)]
        gx = np.abs(cx[:, None] - oc[None, :, 0]) - (half[k, 0] + oh[None, :, 0])
        gy = np.abs(cy[:, None] - oc[None, :, 1]) - (half[k, 1] + oh[None, :, 1])
        g = np.maximum(gx, gy)
        c = np.where(g < 0.0, W_LABEL, W_CROWD * np.maximum(TARGET_GAP - g, 0.0) ** 2)
        return c.sum(1)

    # ---- greedy: roomiest clear candidate at the smallest radius that has one ----
    result = [(0.0, 0.0)] * n
    placed_pos, placed_ids = {}, []
    per_ang = len(base_ang)
    for idx in order:
        cx_all, cy_all = cand[idx]
        mk = marker_hits_vec(idx, cx_all, cy_all)
        if placed_ids:
            oc = np.array([placed_pos[q] for q in placed_ids])
            oh = half[placed_ids]
            gx = np.abs(cx_all[:, None] - oc[None, :, 0]) - (half[idx, 0] + oh[None, :, 0])
            gy = np.abs(cy_all[:, None] - oc[None, :, 1]) - (half[idx, 1] + oh[None, :, 1])
            g = np.maximum(gx, gy)
            hits = (g < 0.0).sum(1)
            room = g.min(1)
        else:
            hits = np.zeros(len(cx_all), int)
            room = np.full(len(cx_all), 1e9)
        clear = (mk == 0) & (hits == 0)
        if clear.any():
            first = int(np.argmax(clear))  # candidates are radius-major
            band = (np.arange(len(cx_all)) // per_ang) == (first // per_ang)
            sel = np.where(clear & band)[0]
            pick = sel[int(np.argmax(np.minimum(room[sel], TARGET_GAP * 3)))]  # roomiest in that ring
        else:
            pick = int(np.argmin(mk + hits * 1000))
        result[idx] = (float(cx_all[pick]), float(cy_all[pick]))
        placed_pos[idx] = result[idx]
        placed_ids.append(idx)

    def cost_of(k, pos, assign):
        cx = np.array([pos[0]])
        cy = np.array([pos[1]])
        others = [q for q in range(n) if q != k]
        return float(unary_vec(k, cx, cy)[0] + pair_vec(k, cx, cy, others, assign)[0])

    def two_opt():
        moved = False
        for _ in range(20):
            improved = False
            for i in range(n):
                for j in range(i + 1, n):
                    before = cost_of(i, result[i], result) + cost_of(j, result[j], result)
                    result[i], result[j] = result[j], result[i]
                    after = cost_of(i, result[i], result) + cost_of(j, result[j], result)
                    if after < before - 1e-6:
                        improved = True
                        moved = True
                    else:
                        result[i], result[j] = result[j], result[i]
            if not improved:
                break
        return moved

    def move_pass():
        moved = False
        for k in range(n):
            cx_all, cy_all = cand[k]
            others = [q for q in range(n) if q != k]
            tot = unary_vec(k, cx_all, cy_all) + pair_vec(k, cx_all, cy_all, others, result)
            b = int(np.argmin(tot))
            if tot[b] < cost_of(k, result[k], result) - 1e-6:
                result[k] = (float(cx_all[b]), float(cy_all[b]))
                moved = True
        return moved

    for _ in range(8):
        m = move_pass()
        t = two_opt()
        if not (m or t):
            break
    return [(float(cx), float(cy)) for cx, cy in result]


def _sample_spread(xs: list[float], ys: list[float], n: int) -> list[int]:
    """Return the indices of ``n`` points spread as evenly as possible across the (x, y) extent -
    farthest-point sampling, deterministic (no RNG).

    Used by ``add_labels(labels=n)`` to auto-pick a readable, unbiased subset to label without the
    caller cherry-picking. Preferred over a uniform random sample, which is density-weighted and so
    would clump labels in the busiest region. Coordinates are normalized to a unit square (so x and
    y weigh equally); the seed is the point nearest the low corner, then each next point is the one
    farthest from all already-chosen. ``n >= len`` returns every index; ``n <= 0`` returns none.
    """
    import numpy as np

    total = len(xs)
    if n >= total:
        return list(range(total))
    if n <= 0:
        return []
    pts = np.column_stack([xs, ys]).astype(float)
    lo = pts.min(axis=0)
    span = pts.max(axis=0) - lo
    span[span == 0] = 1.0
    p = (pts - lo) / span  # unit square
    chosen = [int(np.argmin(p.sum(axis=1)))]  # deterministic seed: nearest the low corner
    dist = np.linalg.norm(p - p[chosen[0]], axis=1)
    for _ in range(n - 1):
        i = int(np.argmax(dist))
        chosen.append(i)
        dist = np.minimum(dist, np.linalg.norm(p - p[i], axis=1))
    return chosen
