"""The scene of the central town of the Math dimension.

A clear morning. Far off are mountains that are polyhedra: faceted peaks, each
face lit by how it turns to the sun, in the haze. A few small solids float in
the air, the sign of the dimension. Nearer, the town goes on round its torus:
white houses on terraces, with domes and gables, and a viaduct that crosses
them. The colours are limestone, whitewash, the blue of a dome, terracotta,
and the blue of the sky.

There are no rings or discs in the sky (Jon, 2026-10-14). The look-dev this
was taken from is `untracked/art-candidates/town/town_vertical.py`.
"""

from __future__ import annotations

import math

import numpy as np

from .artkit import Art, Pen, mix, scale, smoothstep
from .parts import HORIZON, cloud_mask, fog, haze, solid

MATH = {
    "top": (62, 112, 192),
    "mid": (124, 176, 228),
    "low": (214, 230, 242),
    "haze": (232, 238, 242),
    "sun": (255, 246, 220),
    "peak": (150, 166, 198),
    "solid": (160, 182, 216),
    "lime": (226, 216, 194),
    "white": (244, 242, 236),
    "dome": (78, 124, 186),
    "roof": (190, 112, 82),
    "near": (120, 136, 162),
    "near_light": (236, 230, 214),
    "window": (96, 120, 160),
}


def _solid(art: Art, layer: np.ndarray, cu: float, cv: float, r: float, kind: str, rot: float, colour, sun=(-0.6, -0.8)) -> None:
    """A Platonic solid in flat facets, `r` in parts of the panel. Each face
    has a tone by how much it faces the sun; the faces turned away are not
    drawn. `kind` is "octa", "tetra" or "cube"."""
    cr, sr = math.cos(rot), math.sin(rot)

    def turn(x, y, z):
        x, z = x * cr - z * sr, x * sr + z * cr
        y, z = y * 0.94 - z * 0.34, y * 0.34 + z * 0.94
        return np.array((x, y, z))

    if kind == "octa":
        v = [turn(*p) for p in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]
        faces = [(0, 2, 4), (0, 4, 3), (0, 3, 5), (0, 5, 2), (1, 4, 2), (1, 3, 4), (1, 5, 3), (1, 2, 5)]
    elif kind == "tetra":
        v = [turn(*p) for p in ((1, 1, 1), (-1, -1, 1), (-1, 1, -1), (1, -1, -1))]
        faces = [(0, 1, 2), (0, 3, 1), (0, 2, 3), (1, 3, 2)]
    else:
        v = [turn(x, y, z) for x in (-0.7, 0.7) for y in (-0.7, 0.7) for z in (-0.7, 0.7)]
        faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    centre = np.mean(v, axis=0)
    drawn = []
    for f in faces:
        pts = [v[i] for i in f]
        n = np.cross(pts[1] - pts[0], pts[2] - pts[0])
        if np.dot(n, np.mean(pts, axis=0) - centre) < 0:
            n = -n
        if n[2] <= 0:
            continue
        n = n / (np.linalg.norm(n) + 1e-9)
        lit = max(0.0, -(n[0] * sun[0] + n[1] * sun[1]) * 0.8 + n[2] * 0.4)
        drawn.append((float(np.mean([q[2] for q in pts])), [(cu + q[0] * r, cv + q[1] * r) for q in pts], lit))
    for _, poly, lit in sorted(drawn):
        face, pen = art.drawing()
        pen.poly(poly)
        art.put(layer, art.mask_of(face), mix(scale(colour, 0.80), (255, 255, 255), lit * 0.55))


def _peaks(art: Art, layer: np.ndarray, tag: str, base: float, h0: float, h1: float, w0: float, w1: float, colour) -> None:
    """A range of faceted peaks along `base`: five facets to a peak, the
    two that face the sun light, the two away from it dark."""
    rng = art.rand(tag)
    u = -0.06
    while u < 1.06:
        w, h = rng.uniform(w0, w1), rng.uniform(h0, h1)
        ax, ay = u + w * rng.uniform(0.38, 0.62), base - h
        sl = (u + w * rng.uniform(0.12, 0.28), base - h * rng.uniform(0.25, 0.5))
        sr = (u + w * rng.uniform(0.72, 0.88), base - h * rng.uniform(0.25, 0.5))
        mid = (ax + rng.uniform(-0.005, 0.005), base - h * 0.35)
        for poly, lit in (([(u, base), sl, (ax, ay), mid], 0.10), ([sl, (ax, ay), mid], 0.15), ([(ax, ay), sr, mid], -0.04), ([sr, (u + w, base), mid], -0.08), ([(u, base), mid, (u + w, base)], 0.0)):
            face, pen = art.drawing()
            pen.poly(poly)
            art.put(layer, art.mask_of(face, blur=0.3), scale(colour, 1 + lit))
        u += w * rng.uniform(0.55, 0.85)


def _half_dome(pen: Pen, cu: float, base: float, rx: float, ry: float) -> None:
    """The top half of an ellipse standing on `base`: a dome on a roof."""
    pen.poly([(cu + rx * math.cos(a), base - ry * math.sin(a)) for a in np.linspace(0.0, math.pi, 25)])


def _houses(art: Art, walls: list, windows: Pen, rng, u0: float, u1: float, foot: float, h0: float, h1: float, w0: float, w1: float, roofs: Pen, domes: Pen) -> None:
    """A row of houses standing on `foot`. Each wall goes on one of the pens
    of `walls` (one for each plaster colour), its windows (arched, in rows)
    on `windows`, a tile roof on `roofs` and a dome on `domes`."""
    u = u0
    while u < u1:
        w = rng.uniform(w0, w1)
        h = rng.uniform(h0, h1)
        top = foot - h
        rng.choice(walls).rect(u, top, u + w, foot + 0.2)
        kind = rng.choice(["gable", "gable", "hipped", "dome", "flat"])
        if kind == "gable":
            roofs.poly([(u - w * 0.06, top), (u + w * 1.06, top), (u + w * 0.5, top - w * 0.28)])
        elif kind == "hipped":
            roofs.poly([(u - w * 0.06, top), (u + w * 1.06, top), (u + w * 0.78, top - w * 0.16), (u + w * 0.22, top - w * 0.16)])
        elif kind == "dome":
            _half_dome(domes, u + w * 0.5, top, w * 0.32, w * 0.26)
        cols = max(1, int(round(w / (w0 * 0.42))))
        rows = max(1, int(h / (w0 * 0.75)))
        ww, wh = w0 * 0.10, w0 * 0.20
        for r in range(rows):
            for k in range(cols):
                if rng.random() < 0.75:
                    cu = u + (k + 0.5) * w / cols
                    cv = top + (r + 0.55) * h / rows
                    windows.rect(cu - ww, cv - wh * 0.5, cu + ww, cv + wh * 0.5)
                    windows.ellipse(cu, cv - wh * 0.5, ww, ww)
        u += w + rng.uniform(-w0 * 0.12, w0 * 0.02)


def math_town(layer_key: str, art: Art) -> np.ndarray:
    p = MATH
    if layer_key == "sky":
        layer = art.opaque(art.ramp([(0.0, p["top"]), (0.32, p["mid"]), (HORIZON - 0.02, p["low"]), (HORIZON + 0.06, p["haze"]), (1.0, p["haze"])]))
        art.light(layer, art.spot(0.18, HORIZON - 0.18, 0.5, 1.6), p["sun"], 0.35)
        art.light(layer, cloud_mask(art, "high cloud", 0.30, 0.10, cells=3.0, cover=0.42, soft=0.35, stretch=3.6), (255, 255, 255), 0.45)
        art.light(layer, cloud_mask(art, "low cloud", 0.45, 0.06, cells=4.0, cover=0.38, soft=0.3, stretch=5.0), (255, 255, 255), 0.30)
        # Small solids that float in the morning air, far off.
        rng = art.rand("solids")
        for kind, u, v, r in (("octa", 0.22, 0.34, 0.016), ("tetra", 0.61, 0.29, 0.011), ("cube", 0.80, 0.40, 0.008), ("octa", 0.43, 0.44, 0.006)):
            _solid(art, layer, u, v, r, kind, rng.uniform(0, math.tau), mix(p["solid"], p["low"], 0.35 if r > 0.01 else 0.55))
        # The mountains that are polyhedra: two ranges, the far one in more haze.
        _peaks(art, layer, "far peaks", HORIZON + 0.03, 0.10, 0.19, 0.07, 0.13, mix(p["peak"], p["haze"], 0.70))
        _peaks(art, layer, "near peaks", HORIZON + 0.05, 0.06, 0.12, 0.06, 0.11, mix(p["peak"], p["haze"], 0.50))
        art.tint(layer, art.band(HORIZON + 0.05, 0.08, 1.2), p["haze"], 0.45)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        rng = art.rand("far town")
        image, pen = art.drawing()
        wins, win_pen = art.drawing()
        roofs, roof_pen = art.drawing()
        far_domes, far_dome_pen = art.drawing()
        # The town on the far side of the torus: terraces of white houses
        # that climb from the right, and a viaduct that crosses them.
        ground, line = art.ridge("far terraces", HORIZON + 0.05, 0.015, cells=3.0, octaves=2)
        for k, (u0, u1, foot) in enumerate(((0.0, 0.42, HORIZON + 0.05), (0.38, 0.74, HORIZON + 0.02), (0.68, 1.0, HORIZON - 0.02))):
            pen.rect(u0, foot, u1, 1.0)
            _houses(art, [pen], win_pen, rng, u0, u1, foot, 0.025, 0.07, 0.022, 0.04, roof_pen, far_dome_pen)
        # The viaduct, high over the far terraces.
        deck = HORIZON - 0.12
        pen.rect(0.0, deck, 1.0, deck + 0.008)
        for u in np.arange(0.0, 1.02, 0.045):
            pen.rect(u, deck + 0.008, u + 0.006, HORIZON + 0.04)
        holes, hole_pen = art.drawing()
        for u in np.arange(0.0, 1.02, 0.045):
            hole_pen.ellipse(u + 0.0255, deck + 0.022, 0.0195, 0.012)
        span, span_pen = art.drawing()
        span_pen.rect(0.0, deck + 0.008, 1.0, deck + 0.022)
        body = np.clip(np.maximum.reduce([ground, art.mask_of(image), art.mask_of(far_domes), np.clip(art.mask_of(span) - art.mask_of(holes), 0, 1)]), 0, 1)
        layer = solid(art, body, mix(p["white"], p["low"], 0.45), mix(p["lime"], p["low"], 0.40), HORIZON - 0.2, HORIZON + 0.1, "stone", 0.05)
        art.put(layer, art.mask_of(roofs), mix(p["roof"], p["low"], 0.55))
        art.put(layer, art.mask_of(far_domes), mix(p["dome"], p["low"], 0.55))
        art.put(layer, art.mask_of(wins) * body, mix(p["window"], p["low"], 0.45))
        art.light(layer, art.rim(body, 0.003, 0.0, 0.5) * body, (255, 255, 255), 0.35)
        haze(art, layer, p["haze"], 0.18, HORIZON + 0.06)
        return layer
    if layer_key == "near_background":
        rng = art.rand("near town")
        groups = [art.drawing() for _ in range(3)]
        wins, win_pen = art.drawing()
        roofs, roof_pen = art.drawing()
        domes, dome_pen = art.drawing()
        # The town behind the play: a row of houses that fills the view below
        # its middle, so no sky shows through the body of the town.
        _houses(art, [g[1] for g in groups], win_pen, rng, -0.02, 1.02, 0.80, 0.14, 0.30, 0.05, 0.085, roof_pen, dome_pen)
        groups[0][1].rect(0.0, 0.79, 1.0, 1.0)
        plasters = (p["near_light"], mix(p["white"], p["near"], 0.1), mix((236, 214, 176), p["near"], 0.1))
        layer = art.blank()
        mask = np.zeros_like(art.u)
        for (image, _pen), plaster in zip(groups, plasters):
            m = art.mask_of(image)
            mask = np.maximum(mask, m)
            art.put(layer, m, mix(plaster, p["near"], 0.35))
        art.put(layer, art.mask_of(roofs), mix(p["roof"], p["near"], 0.30))
        art.put(layer, art.mask_of(domes), mix(p["dome"], p["near"], 0.20))
        art.light(layer, art.mask_of(domes) * smoothstep(0.02, -0.02, art.u - art.u.mean()) * 0.0, (255, 255, 255), 0.0)
        art.put(layer, art.mask_of(wins) * mask, mix(p["window"], p["near"], 0.25))
        body = np.clip(mask + art.mask_of(roofs) + art.mask_of(domes), 0, 1)
        art.light(layer, art.rim(body, 0.003, 0.0, 0.4) * body, (255, 250, 236), 0.35)
        art.shade(layer, art.rim(body, -0.004, 0.0, 0.8) * body, 0.10)
        haze(art, layer, p["low"], 0.14, None)
        return layer
    # The air: a little morning haze low down, nothing in the view's middle.
    layer = art.blank()
    art.put(layer, fog(art, "morning haze", 0.70, 0.12), p["haze"], 0.22)
    art.put(layer, smoothstep(0.55, 0.80, art.v) * 0.5, p["haze"], 0.10)
    return layer
