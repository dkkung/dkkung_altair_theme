"""Pixel-space label placement - the pure geometry engine behind ``annotations.add_labels``.

No Altair imports here: everything takes and returns plain pixel coordinates, mirroring how
``_statistics.py`` is the pure computation engine behind ``stats.py``. Placement is solved
outside the renderer (like ggrepel / adjustText / d3-labeler) because Vega-Lite has no
label-repel primitive; the wrapper feeds the results back to Altair as static positions.
"""

TARGET_GAP = 5.0
W_CROWD = 3.0
W_MARKER = 400.0
W_LABEL = 5000.0
W_DIR = 10.0
POINT_R = 3.0
W_OCCL = 0.0  # leader passing through another label's box
W_CROSS = 0.0  # leader-leader crossing
W_LEN2 = 0.15  # superlinear leader-length cost beyond LEN_FREE px
LEN_FREE = 12.0


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
    (``W_CROWD`` below ``TARGET_GAP``), a leader passing through another label's box (``W_OCCL``),
    leader-leader crossings (``W_CROSS``), and sitting inward of the mark (``W_DIR``). Never drops
    a label. ``iterations`` is unused (kept for call compatibility).
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
        L = np.hypot(cx - a[k, 0], cy - a[k, 1])
        t = L + W_LEN2 * np.maximum(L - LEN_FREE, 0.0) ** 2 + W_MARKER * marker_hits_vec(k, cx, cy)
        ox, oy = a[k, 0] - centroid[0], a[k, 1] - centroid[1]
        onrm = float(np.hypot(ox, oy))
        if onrm > 1e-9:
            inward = -((cx - a[k, 0]) * ox + (cy - a[k, 1]) * oy) / onrm
            t = t + W_DIR * np.maximum(inward, 0.0)
        return t

    def _seg_box(p0x, p0y, p1x, p1y, bcx, bcy, bhx, bhy):
        """segment p0->p1 (arrays) vs AABB centre b, half-extents h (arrays) -> bool, broadcast."""
        dx = (p1x - p0x) / 2.0
        dy = (p1y - p0y) / 2.0
        mx = (p0x + p1x) / 2.0 - bcx
        my = (p0y + p1y) / 2.0 - bcy
        adx, ady = np.abs(dx), np.abs(dy)
        out = (np.abs(mx) <= bhx + adx) & (np.abs(my) <= bhy + ady)
        return out & (np.abs(dx * my - dy * mx) <= bhx * ady + bhy * adx + 1e-9)

    def _seg_seg(p0x, p0y, p1x, p1y, q0x, q0y, q1x, q1y):
        """proper segment-segment intersection (arrays, broadcast) -> bool."""

        def orient(ax_, ay_, bx_, by_, cx_, cy_):
            return (bx_ - ax_) * (cy_ - ay_) - (by_ - ay_) * (cx_ - ax_)

        d1 = orient(q0x, q0y, q1x, q1y, p0x, p0y)
        d2 = orient(q0x, q0y, q1x, q1y, p1x, p1y)
        d3 = orient(p0x, p0y, p1x, p1y, q0x, q0y)
        d4 = orient(p0x, p0y, p1x, p1y, q1x, q1y)
        return ((d1 > 0) != (d2 > 0)) & ((d3 > 0) != (d4 > 0))

    def pair_one(k, cp, q, cq):
        """full pair cost (crowding + occlusion both ways + crossing) of k at cp vs q at cq. Scalar
        Python on purpose: 2-opt calls this per swap trial, where length-1 numpy is all overhead."""
        khx, khy = float(half[k, 0]), float(half[k, 1])
        qhx, qhy = float(half[q, 0]), float(half[q, 1])
        g = max(abs(cp[0] - cq[0]) - (khx + qhx), abs(cp[1] - cq[1]) - (khy + qhy))
        c = W_LABEL if g < 0.0 else (W_CROWD * (TARGET_GAP - g) ** 2 if g < TARGET_GAP else 0.0)
        if not (W_OCCL or W_CROSS):
            return c

        def seg_box(p0x, p0y, p1x, p1y, bx, by, bhx, bhy):
            dx = (p1x - p0x) / 2.0
            dy = (p1y - p0y) / 2.0
            mx = (p0x + p1x) / 2.0 - bx
            my = (p0y + p1y) / 2.0 - by
            adx, ady = abs(dx), abs(dy)
            if abs(mx) > bhx + adx or abs(my) > bhy + ady:
                return False
            return abs(dx * my - dy * mx) <= bhx * ady + bhy * adx + 1e-9

        akx, aky = float(a[k, 0]), float(a[k, 1])
        aqx, aqy = float(a[q, 0]), float(a[q, 1])
        if seg_box(akx, aky, cp[0], cp[1], cq[0], cq[1], qhx, qhy):
            c += W_OCCL
        if seg_box(aqx, aqy, cq[0], cq[1], cp[0], cp[1], khx, khy):
            c += W_OCCL

        def orient(ax_, ay_, bx_, by_, cx_, cy_):
            return (bx_ - ax_) * (cy_ - ay_) - (by_ - ay_) * (cx_ - ax_)

        d1 = orient(aqx, aqy, cq[0], cq[1], akx, aky)
        d2 = orient(aqx, aqy, cq[0], cq[1], cp[0], cp[1])
        d3 = orient(akx, aky, cp[0], cp[1], aqx, aqy)
        d4 = orient(akx, aky, cp[0], cp[1], cq[0], cq[1])
        if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
            c += W_CROSS
        return c

    def pair_vec(k, cx, cy, others, opos):
        """crowding + occlusion + crossing cost of candidates for k against fixed labels `others`"""
        if not others:
            return np.zeros(len(cx))
        oc = np.array([opos[q] for q in others])
        oh = half[list(others)]
        gx = np.abs(cx[:, None] - oc[None, :, 0]) - (half[k, 0] + oh[None, :, 0])
        gy = np.abs(cy[:, None] - oc[None, :, 1]) - (half[k, 1] + oh[None, :, 1])
        g = np.maximum(gx, gy)
        c = np.where(g < 0.0, W_LABEL, W_CROWD * np.maximum(TARGET_GAP - g, 0.0) ** 2)
        tot = c.sum(1)
        if not (W_OCCL or W_CROSS):
            return tot
        # k's candidate leader a[k]->(cx,cy) through other boxes
        occl_a = _seg_box(
            a[k, 0], a[k, 1], cx[:, None], cy[:, None], oc[None, :, 0], oc[None, :, 1], oh[None, :, 0], oh[None, :, 1]
        )
        # others' fixed leaders a[q]->opos[q] through k's candidate box
        oa = a[list(others)]
        occl_b = _seg_box(
            oa[None, :, 0],
            oa[None, :, 1],
            oc[None, :, 0],
            oc[None, :, 1],
            cx[:, None],
            cy[:, None],
            half[k, 0],
            half[k, 1],
        )
        # leader-leader crossings
        cross = _seg_seg(
            a[k, 0], a[k, 1], cx[:, None], cy[:, None], oa[None, :, 0], oa[None, :, 1], oc[None, :, 0], oc[None, :, 1]
        )
        return tot + W_OCCL * (occl_a.sum(1) + occl_b.sum(1)) + W_CROSS * cross.sum(1)

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

    def pair_all(mv, pos, Px, Py):
        """pair cost of every label k at every slot s against label mv fixed at pos -> (n, n)."""
        hx = half[:, 0][:, None]
        hy = half[:, 1][:, None]
        gx = np.abs(Px[None, :] - pos[0]) - (hx + half[mv, 0])
        gy = np.abs(Py[None, :] - pos[1]) - (hy + half[mv, 1])
        g = np.maximum(gx, gy)
        c = np.where(g < 0.0, W_LABEL, W_CROWD * np.maximum(TARGET_GAP - g, 0.0) ** 2)
        if not (W_OCCL or W_CROSS):
            return c
        occ_a = _seg_box(
            a[:, 0][:, None], a[:, 1][:, None], Px[None, :], Py[None, :], pos[0], pos[1], half[mv, 0], half[mv, 1]
        )
        occ_b = _seg_box(a[mv, 0], a[mv, 1], pos[0], pos[1], Px[None, :], Py[None, :], hx, hy)
        crs = _seg_seg(a[:, 0][:, None], a[:, 1][:, None], Px[None, :], Py[None, :], a[mv, 0], a[mv, 1], pos[0], pos[1])
        return c + W_OCCL * (occ_a + occ_b) + W_CROSS * crs

    P: list[tuple[float, float]] = []  # slot positions during a two_opt run (fixed; swaps permute assignment)

    def two_opt():
        """first-improvement 2-opt over slot assignments, evaluated from incremental matrices.

        U2[k, s]: unary cost of label k at slot s. R[k, s]: pair cost of label k at slot s
        against every OTHER label at its current position. Both stay valid across accepted
        swaps except R's terms involving the two swapped labels, which are patched in place.
        """
        nonlocal result
        if n < 2:
            return False
        P[:] = list(result)
        Px = np.array([p_[0] for p_ in P])
        Py = np.array([p_[1] for p_ in P])
        slot_of = list(range(n))  # label k currently occupies slot slot_of[k]
        U2 = np.stack([unary_vec(k, Px, Py) for k in range(n)])
        R = np.zeros((n, n))
        for k in range(n):
            others = [q for q in range(n) if q != k]
            R[k] = pair_vec(k, Px, Py, others, {q: P[slot_of[q]] for q in others})
        moved = False
        for _ in range(20):
            improved = False
            for i_ in range(n):
                for j_ in range(i_ + 1, n):
                    si, sj = slot_of[i_], slot_of[j_]
                    # R rows include the partner at its OLD slot; swap both terms out/in
                    old_c = U2[i_, si] + U2[j_, sj] + R[i_, si] + R[j_, sj] - pair_one(i_, P[si], j_, P[sj])
                    new_c = (
                        U2[i_, sj]
                        + U2[j_, si]
                        + R[i_, sj]
                        - pair_one(i_, P[sj], j_, P[sj])
                        + 0.0
                        + R[j_, si]
                        - pair_one(j_, P[si], i_, P[si])
                        + pair_one(i_, P[sj], j_, P[si])
                    )
                    if new_c < old_c - 1e-6:
                        # patch every R row at once: labels i_ and j_ moved slots
                        for mv, s_old, s_new in ((i_, si, sj), (j_, sj, si)):
                            delta = pair_all(mv, P[s_new], Px, Py) - pair_all(mv, P[s_old], Px, Py)
                            delta[[i_, j_], :] = 0.0
                            R += delta
                        slot_of[i_], slot_of[j_] = sj, si
                        # the swapped labels' own rows contain the partner at its OLD slot in every
                        # entry - the patch above skipped them, so rebuild both outright
                        for mv in (i_, j_):
                            others = [q for q in range(n) if q != mv]
                            R[mv] = pair_vec(mv, Px, Py, others, {q: P[slot_of[q]] for q in others})
                        improved = True
                        moved = True
            if not improved:
                break
        result = [P[slot_of[k]] for k in range(n)]
        return moved

    _unary_cache: dict[int, "np.ndarray"] = {}

    def unary_cached(k):
        if k not in _unary_cache:
            cx_all, cy_all = cand[k]
            _unary_cache[k] = unary_vec(k, cx_all, cy_all)
        return _unary_cache[k]

    def move_pass():
        moved = False
        for k in range(n):
            cx_all, cy_all = cand[k]
            others = [q for q in range(n) if q != k]
            tot = unary_cached(k) + pair_vec(k, cx_all, cy_all, others, result)
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
