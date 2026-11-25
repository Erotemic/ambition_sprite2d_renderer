"""The scenes of the Business dimension: Capital, the city where everyone is
doing business (gate address DEALINGS, `docs/planning/game/business-dimension.md`).

`business`: the city at the golden hour of a long working day. A lavender
sky going to peach at the horizon, heaped clouds, an airliner climbing out
with its contrail. Far off, the towers of the financial district round the
Tower, the head office with a stepped crown and a lit briefcase in it; a
gold-domed exchange; the control tower of the airport; and, rising out of
the district into the clouds, the Corporate Ladder, which has no top in
sight. Nearer, the stone fronts of the plaza district: columns, arcades,
long banners with a tie on them, cypresses and lamps.

`business_office`: inside Records & Processing, a hall of the records of the
city: tall arched bays of binders on shelves, the brass pneumatic tubes that
carry the forms between floors, steel columns, lamps hung on long cords.

Nothing on a backdrop is writing (the game draws some backdrops mirrored).
"""

from __future__ import annotations

import math

import numpy as np

from .artkit import Art, Pen, mix, scale, smoothstep
from .parts import HORIZON, cloud_mask, cumulus, fog, haze, lamps, solid, window_grid

BUSINESS = {
    "top": (92, 94, 168),
    "high": (150, 140, 206),
    "mid": (214, 176, 214),
    "low": (250, 206, 186),
    "haze": (236, 210, 214),
    "sun": (255, 232, 196),
    "cloud": (255, 240, 236),
    "cloud_shade": (176, 150, 196),
    "tower": (132, 124, 176),
    "tower_light": (196, 182, 220),
    "tower_dark": (82, 76, 128),
    "gold": (238, 194, 96),
    "gold_light": (255, 230, 160),
    "glass": (176, 196, 236),
    "window": (255, 222, 150),
    "stone": (200, 184, 176),
    "stone_light": (238, 226, 214),
    "stone_dark": (122, 108, 120),
    "banner": (132, 36, 54),
    "leaf": (70, 110, 84),
    "leaf_dark": (40, 70, 62),
    "lamp": (255, 214, 140),
}

OFFICE = {
    "wall": (64, 50, 70),
    "wall_light": (104, 84, 108),
    "wall_dark": (34, 26, 40),
    "shelf": (82, 56, 48),
    "shelf_dark": (44, 30, 30),
    "spines": ((148, 52, 62), (60, 80, 140), (196, 168, 90), (80, 120, 96), (120, 82, 150), (200, 200, 190)),
    "brass": (214, 170, 90),
    "glass": (190, 214, 236),
    "steel": (70, 70, 88),
    "steel_light": (130, 128, 150),
    "lamp": (255, 214, 150),
    "air": (120, 100, 128),
    "banner": (126, 34, 52),
}


# ---------------------------------------------------------------------------
# Parts
# ---------------------------------------------------------------------------


def _tower(pen: Pen, rng, u: float, w: float, base: float, h: float) -> tuple[float, float, float, float]:
    """An office tower of glass and stone, with a set-back or a spire on top.
    Returns its box (u0, v0, u1, v1) for the windows."""
    top = base - h
    pen.rect(u, top, u + w, base)
    kind = rng.choice(["setback", "spire", "flat", "setback", "crown"])
    if kind == "setback":
        pen.rect(u + w * 0.15, top - h * 0.10, u + w * 0.85, top)
        pen.rect(u + w * 0.30, top - h * 0.17, u + w * 0.70, top - h * 0.10)
    elif kind == "spire":
        pen.poly([(u + w * 0.35, top), (u + w * 0.65, top), (u + w * 0.5, top - h * 0.28)])
    elif kind == "crown":
        pen.poly([(u, top), (u + w, top), (u + w * 0.82, top - h * 0.08), (u + w * 0.18, top - h * 0.08)])
        pen.rect(u + w * 0.47, top - h * 0.22, u + w * 0.53, top - h * 0.08)
    return (u, top, u + w, base)


def _head_office(pen: Pen, crown: Pen, u: float, base: float, h: float, w: float) -> tuple[float, float]:
    """The Tower: the stepped art-deco crown of the head office over the
    district, with an arched niche in its crown where the briefcase is lit.
    Returns the middle of the niche."""
    top = base - h
    pen.rect(u, top, u + w, base)
    for k, (dw, dh) in enumerate(((0.12, 0.07), (0.24, 0.13), (0.34, 0.19))):
        pen.rect(u + w * dw, top - h * dh, u + w * (1 - dw), top - h * (dh - 0.07) + 0.002)
    peak = top - h * 0.19
    pen.poly([(u + w * 0.40, peak), (u + w * 0.60, peak), (u + w * 0.5, peak - h * 0.10)])
    # The fins up its face.
    for x in (0.08, 0.30, 0.70, 0.92):
        crown.rect(u + w * x - 0.0016, top - h * 0.02, u + w * x + 0.0016, base)
    cu, cv = u + w * 0.5, top - h * 0.085
    return cu, cv


def _ladder(pen: Pen, u: float, v_base: float, v_top: float, w: float, lean: float) -> None:
    """The Corporate Ladder: two rails rising out of the district at a lean,
    rungs between them, smaller as they go up."""
    rails = ((u, u + lean), (u + w, u + w + lean * 0.92))
    for a, b in rails:
        pen.poly([(a - 0.004, v_base), (a + 0.004, v_base), (b + 0.0025, v_top), (b - 0.0025, v_top)])
    k = 0
    v = v_base - 0.02
    step = 0.034
    while v > v_top:
        t = (v_base - v) / (v_base - v_top)
        x0 = rails[0][0] + (rails[0][1] - rails[0][0]) * t
        x1 = rails[1][0] + (rails[1][1] - rails[1][0]) * t
        pen.rect(x0, v - 0.0035 * (1 - 0.5 * t), x1, v)
        v -= step * (1.0 - 0.45 * t)
        k += 1


def _airliner(pen: Pen, u: float, v: float, size: float, climb: float) -> None:
    """An airliner seen from the side, nose up to the right."""
    c, s = math.cos(climb), math.sin(climb)

    def at(x: float, y: float) -> tuple[float, float]:
        return (u + (x * c - y * s) * size, v - (x * s + y * c) * size)

    pen.poly([at(-1.0, 0.04), at(0.85, 0.06), at(1.0, 0.0), at(0.85, -0.05), at(-0.95, -0.04)])
    pen.poly([at(-0.1, 0.0), at(0.25, 0.0), at(-0.3, -0.45), at(-0.42, -0.45)])
    pen.poly([at(-0.82, 0.03), at(-0.62, 0.03), at(-0.9, 0.34), at(-1.0, 0.34)])


def _dome(pen: Pen, u: float, base: float, w: float, h: float) -> tuple[float, float, float]:
    """The exchange: a columned drum on a stepped base with a gold dome.
    Returns the dome (middle u, v, radius)."""
    pen.rect(u - w * 0.6, base - h * 0.12, u + w * 0.6, base)
    pen.rect(u - w * 0.45, base - h * 0.55, u + w * 0.45, base - h * 0.12)
    return (u, base - h * 0.55, w * 0.42)


def _facades(pen: Pen, shade: Pen, rng, u0: float, u1: float, foot: float) -> list[tuple[float, float, float]]:
    """The stone fronts of the plaza district: porticoes with columns,
    arcades of round arches, a cornice over each. Returns where the long
    banners hang (u, top, bottom)."""
    banners = []
    u = u0
    while u < u1:
        kind = rng.choice(["portico", "arcade", "block", "arcade"])
        w = rng.uniform(0.12, 0.22)
        h = rng.uniform(0.16, 0.26)
        top = foot - h
        pen.rect(u, top, u + w, foot + 0.2)
        pen.rect(u - 0.006, top - 0.012, u + w + 0.006, top)
        if kind == "portico":
            pen.poly([(u + w * 0.1, top - 0.012), (u + w * 0.9, top - 0.012), (u + w * 0.5, top - 0.05)])
            n = 6
            for k in range(n):
                cx = u + w * (0.14 + 0.72 * k / (n - 1))
                shade.rect(cx + 0.004, top + 0.02, cx + 0.011, foot)
        elif kind == "arcade":
            n = max(3, int(w / 0.035))
            for k in range(n):
                a0 = u + w * k / n + 0.006
                a1 = u + w * (k + 1) / n - 0.006
                shade.rect(a0, foot - h * 0.42, a1, foot)
                shade.ellipse((a0 + a1) / 2, foot - h * 0.42, (a1 - a0) / 2, (a1 - a0) / 2)
            for k in range(n):
                cu = u + w * (k + 0.5) / n
                shade.rect(cu - 0.008, top + h * 0.14, cu + 0.008, top + h * 0.3)
        else:
            for row in range(3):
                for k in range(int(w / 0.03)):
                    cu = u + 0.012 + k * 0.03
                    shade.rect(cu, top + 0.02 + row * h * 0.26, cu + 0.012, top + 0.02 + row * h * 0.26 + h * 0.14)
        if rng.random() < 0.7:
            banners.append((u + w * rng.choice([0.2, 0.8]), top + 0.01, top + h * 0.45))
        u += w + rng.uniform(0.0, 0.02)
    return banners


def _banner(pen: Pen, tie: Pen, u: float, top: float, bottom: float, w: float = 0.022) -> None:
    """A long banner on a rod, swallowtailed, a tie on it (the city's sign)."""
    pen.rect(u - w * 0.7, top - 0.003, u + w * 0.7, top)
    pen.poly([(u - w * 0.5, top), (u + w * 0.5, top), (u + w * 0.5, bottom), (u, bottom - w * 0.6), (u - w * 0.5, bottom)])
    mid = top + (bottom - top) * 0.42
    tie.poly([(u - w * 0.14, mid - w * 0.9), (u + w * 0.14, mid - w * 0.9), (u + w * 0.09, mid - w * 0.62), (u + w * 0.2, mid + w * 1.1),
              (u, mid + w * 1.5), (u - w * 0.2, mid + w * 1.1), (u - w * 0.09, mid - w * 0.62)])


def _cypress(pen: Pen, u: float, foot: float, h: float, w: float) -> None:
    pen.poly([(u - w * 0.5, foot), (u - w * 0.55, foot - h * 0.4), (u - w * 0.3, foot - h * 0.85), (u, foot - h),
              (u + w * 0.3, foot - h * 0.85), (u + w * 0.55, foot - h * 0.4), (u + w * 0.5, foot)])


def _lamp_post(pen: Pen, u: float, foot: float, h: float) -> tuple[float, float]:
    pen.rect(u - 0.0022, foot - h, u + 0.0022, foot)
    pen.rect(u - 0.005, foot - 0.012, u + 0.005, foot)
    pen.ellipse(u, foot - h, 0.0065, 0.008)
    return (u, foot - h)


# ---------------------------------------------------------------------------
# The city
# ---------------------------------------------------------------------------


def business(layer_key: str, art: Art) -> np.ndarray:
    p = BUSINESS
    if layer_key == "sky":
        layer = art.opaque(art.ramp([(0.0, p["top"]), (0.24, p["high"]), (0.44, p["mid"]), (HORIZON - 0.02, p["low"]), (HORIZON + 0.08, p["haze"]), (1.0, p["haze"])]))
        sun = (0.80, HORIZON - 0.07)
        art.light(layer, art.spot(sun[0], sun[1], 0.55, 1.8), p["sun"], 0.35)
        art.light(layer, art.spot(sun[0], sun[1], 0.07, 1.6), p["sun"], 0.75)
        clouds = cumulus(art, "business clouds", 0.34, 0.12, cells=3.0, cover=0.42, light=p["cloud"], shadow=p["cloud_shade"])
        layer = art.over(layer, clouds * np.array([1, 1, 1, 0.85], dtype=np.float32))
        art.light(layer, cloud_mask(art, "business streaks", 0.46, 0.04, cells=3.0, cover=0.3, soft=0.3, stretch=6.0), p["cloud"], 0.35)
        # An airliner climbing out of the city, its contrail behind it.
        trail, trail_pen = art.drawing()
        trail_pen.line([(0.08, 0.36), (0.40, 0.24)], 0.0035)
        art.light(layer, art.mask_of(trail, blur=2.0), p["cloud"], 0.55)
        plane, plane_pen = art.drawing()
        _airliner(plane_pen, 0.43, 0.235, 0.022, math.radians(20.0))
        art.put(layer, art.mask_of(plane, blur=0.3), mix(p["tower_dark"], p["high"], 0.35))
        # The Corporate Ladder, far off and very tall: out of the district
        # and up into the clouds, its top out of sight.
        far, pen = art.drawing()
        _ladder(pen, 0.585, HORIZON + 0.02, 0.0, 0.034, 0.05)
        ladder = art.mask_of(far, blur=0.5)
        art.put(layer, ladder * smoothstep(0.18, 0.40, art.v), mix(p["gold"], p["mid"], 0.55))
        art.put(layer, ladder * (1.0 - smoothstep(0.18, 0.40, art.v)), mix(p["gold"], p["high"], 0.7), 0.8)
        # The clouds it goes up into close round it.
        art.light(layer, cloud_mask(art, "ladder clouds", 0.25, 0.07, cells=4.0, cover=0.4, soft=0.2) * art.band(0.25, 0.08) * smoothstep(0.08, 0.0, np.abs(art.u - 0.62)), p["cloud"], 0.65)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        rng = art.rand("business skyline")
        image, pen = art.drawing()
        fins, fin_pen = art.drawing()
        foot = HORIZON + 0.10
        boxes = []
        u = -0.02
        while u < 1.02:
            w = rng.uniform(0.025, 0.05)
            h = rng.uniform(0.10, 0.26) * (1.0 - 0.45 * abs(u - 0.5))
            boxes.append(_tower(pen, rng, u, w, foot, h))
            u += w + rng.uniform(0.002, 0.012)
        niche = _head_office(pen, fin_pen, 0.40, foot, 0.36, 0.075)
        dome = _dome(pen, 0.20, foot, 0.06, 0.13)
        # The airport's control tower, east.
        pen.rect(0.895, foot - 0.25, 0.905, foot)
        pen.ellipse(0.90, foot - 0.25, 0.022, 0.012)
        pen.rect(0.886, foot - 0.27, 0.914, foot - 0.25)
        body = art.mask_of(image)
        layer = solid(art, body, mix(p["tower_light"], p["haze"], 0.35), mix(p["tower"], p["haze"], 0.25), HORIZON - 0.3, HORIZON + 0.1, "towers", 0.04)
        # Glass: the faces catch the sky, lighter to the west of each.
        art.light(layer, art.rim(body, 0.004, 0.0, 0.5) * body, p["sun"], 0.30)
        art.put(layer, art.mask_of(fins) * body, mix(p["tower_dark"], p["haze"], 0.3), 0.6)
        wins, win_pen = art.drawing()
        for u0, v0, u1, v1 in boxes:
            window_grid(win_pen, rng, u0 + 0.003, v0 + 0.01, u1 - 0.003, v1, 0.007, 0.012, 0.22)
        art.put(layer, art.mask_of(wins, blur=0.3) * body, p["window"], 0.55)
        # The gold dome of the exchange, and the briefcase lit in the Tower's crown.
        d, d_pen = art.drawing()
        d_pen.ellipse(dome[0], dome[1], dome[2], dome[2] * 0.9)
        dome_mask = art.mask_of(d, blur=0.4) * (art.v < dome[1]).astype(np.float32)
        art.put(layer, dome_mask, mix(p["gold"], p["haze"], 0.2))
        art.light(layer, art.rim(dome_mask, 0.004, 0.003, 0.4) * dome_mask, p["gold_light"], 0.6)
        case, case_pen = art.drawing()
        cu, cv = niche
        case_pen.rect(cu - 0.010, cv - 0.004, cu + 0.010, cv + 0.009)
        case_pen.rect(cu - 0.004, cv - 0.008, cu + 0.004, cv - 0.004)
        art.put(layer, art.mask_of(case, blur=0.3), p["gold_light"])
        art.light(layer, art.spot(cu, cv, 0.05, 2.0), p["gold"], 0.45)
        haze(art, layer, p["haze"], 0.20, foot)
        return layer
    if layer_key == "near_background":
        rng = art.rand("business plaza district")
        image, pen = art.drawing()
        shade, shade_pen = art.drawing()
        foot = 0.80
        banner_at = _facades(pen, shade_pen, rng, -0.02, 1.02, foot)
        trees, tree_pen = art.drawing()
        lamp_points = []
        for k in range(9):
            u = 0.05 + k * 0.115 + rng.uniform(-0.02, 0.02)
            _cypress(tree_pen, u, foot, rng.uniform(0.10, 0.15), 0.022)
        for k in range(6):
            lu, lv = _lamp_post(pen, 0.10 + k * 0.17, foot, 0.10)
            lamp_points.append((lu, lv, 0.004))
        pen.rect(-0.02, foot, 1.02, 1.0)
        body = art.mask_of(image)
        layer = solid(art, body, mix(p["stone"], p["tower_dark"], 0.25), mix(p["stone_dark"], p["tower_dark"], 0.5), 0.5, 0.85, "stone", 0.05)
        shade_mask = art.mask_of(shade) * body
        art.shade(layer, shade_mask, 0.45)
        # Some of the windows and arches are lit: people are still at work.
        lit = smoothstep(0.55, 0.75, art.noise("lit offices", cells=14.0, octaves=1))
        art.put(layer, shade_mask * lit, p["window"], 0.55)
        art.light(layer, art.rim(body, -0.003, 0.0, 0.4) * body, p["sun"], 0.40)
        flags, flag_pen = art.drawing()
        ties, tie_pen = art.drawing()
        for u, top, bottom in banner_at:
            _banner(flag_pen, tie_pen, u, top, bottom)
        art.put(layer, art.mask_of(flags, blur=0.3), p["banner"])
        art.put(layer, art.mask_of(ties, blur=0.3), p["gold"])
        tree_mask = art.mask_of(trees, blur=0.3)
        art.put(layer, tree_mask, art.ramp([(0.0, p["leaf"]), (0.75, p["leaf"]), (0.85, p["leaf_dark"]), (1.0, p["leaf_dark"])]))
        art.light(layer, art.rim(tree_mask, -0.003, 0.0, 0.4) * tree_mask, p["sun"], 0.25)
        lamps(art, layer, lamp_points, p["lamp"], halo=4.0, strength=0.6)
        haze(art, layer, p["haze"], 0.14, None)
        return layer
    # The air: a warm haze low down, and the glow of the hour.
    layer = art.blank()
    art.put(layer, fog(art, "business haze", 0.76, 0.10, cells=3.0), p["haze"], 0.22)
    art.put(layer, art.spot(0.8, 0.3, 0.6, 2.0), p["sun"], 0.06)
    return layer


# ---------------------------------------------------------------------------
# Records & Processing
# ---------------------------------------------------------------------------


def _shelf_bay(art: Art, layer: np.ndarray, p: dict, rng, u0: float, u1: float, top: float, bottom: float) -> None:
    """One arched bay of binders: shelves from `top` to `bottom`, each full
    of spines of the ledger colours, a lamp-lit arch over them."""
    bay, pen = art.drawing()
    pen.rect(u0, top, u1, bottom)
    pen.ellipse((u0 + u1) / 2, top, (u1 - u0) / 2, (u1 - u0) * 0.45)
    bay_mask = art.mask_of(bay, blur=0.3)
    art.put(layer, bay_mask, p["shelf_dark"])
    rows = 9
    for r in range(rows):
        v0 = top + (bottom - top) * r / rows
        v1 = top + (bottom - top) * (r + 1) / rows
        spines, sp_pen = art.drawing()
        by_colour = {}
        u = u0 + 0.003
        while u < u1 - 0.004:
            w = rng.uniform(0.006, 0.009)
            c = rng.randrange(len(p["spines"]))
            h = (v1 - v0) * rng.uniform(0.84, 0.9)
            by_colour.setdefault(c, []).append((u, v1 - 0.004 - h, u + w, v1 - 0.004))
            u += w + 0.0008
        for c, rects in by_colour.items():
            img, cp = art.drawing()
            for r_ in rects:
                cp.rect(*r_)
            art.put(layer, art.mask_of(img, blur=0.2) * bay_mask, mix(p["spines"][c], p["wall_dark"], 0.7))
        # The label on each binder's spine, and the ring of its pull.
        labels, lb_pen = art.drawing()
        for rects in by_colour.values():
            for x0, y0, x1, y1 in rects:
                lb_pen.rect(x0 + (x1 - x0) * 0.2, y0 + (y1 - y0) * 0.18, x1 - (x1 - x0) * 0.2, y0 + (y1 - y0) * 0.38)
                lb_pen.ellipse((x0 + x1) / 2, y0 + (y1 - y0) * 0.7, (x1 - x0) * 0.22)
        art.put(layer, art.mask_of(labels, blur=0.2) * bay_mask, mix((226, 218, 200), p["wall_dark"], 0.62))
        board, b_pen = art.drawing()
        b_pen.rect(u0, v1 - 0.004, u1, v1)
        art.put(layer, art.mask_of(board), p["shelf"])


def business_office(layer_key: str, art: Art) -> np.ndarray:
    p = OFFICE
    if layer_key == "sky":
        # The back wall: tall arched bays of binders between pilasters.
        layer = art.opaque(art.ramp([(0.0, p["wall_dark"]), (0.3, p["wall"]), (0.8, p["wall"]), (1.0, p["wall_dark"])]))
        rng = art.rand("records bays")
        for k in range(5):
            u0 = 0.02 + k * 0.2
            _shelf_bay(art, layer, p, rng, u0, u0 + 0.16, 0.16, 0.78)
        pil, pil_pen = art.drawing()
        for k in range(6):
            u = k * 0.2 - 0.02
            pil_pen.rect(u, 0.0, u + 0.04, 1.0)
        pil_mask = art.mask_of(pil)
        art.put(layer, pil_mask, p["wall_light"])
        art.shade(layer, pil_mask * smoothstep(0.0, 0.04, (art.u * 5.0) % 1.0), 0.15)
        # Warm light pooled in each arch.
        for k in range(5):
            art.light(layer, art.spot(0.10 + k * 0.2, 0.22, 0.16, 2.0, squash=1.4), p["lamp"], 0.22)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        # The brass tubes that carry the forms, a run of them across the hall
        # with their bends and collars, and the steel columns.
        image, pen = art.drawing()
        glass, glass_pen = art.drawing()
        for v, w in ((0.30, 0.016), (0.36, 0.012)):
            pen.rect(-0.02, v, 1.02, v + w)
            glass_pen.rect(-0.02, v + w * 0.25, 1.02, v + w * 0.75)
        for u in (0.18, 0.52, 0.86):
            pen.rect(u, 0.30, u + 0.016, 0.72)
            glass_pen.rect(u + 0.004, 0.31, u + 0.012, 0.72)
            for v in (0.40, 0.52, 0.64):
                pen.rect(u - 0.004, v, u + 0.020, v + 0.008)
        cols, col_pen = art.drawing()
        for u in (0.0, 0.34, 0.68):
            col_pen.rect(u + 0.08, 0.0, u + 0.105, 1.0)
            col_pen.rect(u + 0.07, 0.12, u + 0.115, 0.135)
        layer = art.blank()
        col_mask = art.mask_of(cols)
        art.put(layer, col_mask, art.ramp([(0.0, p["steel_light"]), (1.0, p["steel"])]))
        art.shade(layer, art.rim(col_mask, -0.004, 0.0, 0.5) * col_mask, 0.3)
        tube = art.mask_of(image)
        art.put(layer, tube, p["brass"])
        art.put(layer, art.mask_of(glass) * tube, mix(p["glass"], p["air"], 0.3), 0.7)
        art.shade(layer, art.rim(tube, 0.0, -0.004, 0.4) * tube, 0.25)
        haze(art, layer, p["air"], 0.30, None)
        return layer
    if layer_key == "near_background":
        # Lamps hung on long cords down into the view.
        image, pen = art.drawing()
        points = []
        for k, u in enumerate((0.12, 0.38, 0.64, 0.90)):
            v = 0.24 + 0.03 * (k % 2)
            pen.rect(u - 0.0012, 0.0, u + 0.0012, v)
            pen.poly([(u - 0.02, v + 0.02), (u + 0.02, v + 0.02), (u + 0.008, v), (u - 0.008, v)])
            points.append((u, v + 0.022, 0.006))
        layer = art.blank()
        art.put(layer, art.mask_of(image, blur=0.3), p["steel"])
        lamps(art, layer, points, p["lamp"], halo=6.0, strength=0.7)
        return layer
    layer = art.blank()
    art.put(layer, fog(art, "records dust", 0.50, 0.14, cells=2.5), p["lamp"], 0.06)
    return layer


# ---------------------------------------------------------------------------
# Foregrounds
# ---------------------------------------------------------------------------


def business_foreground(art: Art, pen: Pen, layer_lights: list) -> None:
    """The top of a clipped hedge and the urn of a planter from below, and
    the arm of a lamp post across the top of the view."""
    rng = art.rand("business hedge")
    for u0, u1 in ((0.02, 0.24), (0.70, 0.95)):
        pen.rect(u0, 0.668, u1, 0.70)
        for k in range(int((u1 - u0) / 0.01)):
            pen.ellipse(u0 + k * 0.01 + 0.005, 0.668, 0.007, 0.005 + rng.uniform(0, 0.002))
    pen.poly([(0.47, 0.70), (0.53, 0.70), (0.545, 0.672), (0.455, 0.672)])
    pen.rect(0.45, 0.666, 0.55, 0.674)
    pen.rect(0.88, 0.33, 0.886, 0.40)
    pen.curve((0.886, 0.338), (0.95, 0.338), -0.01, 0.0025)


def office_foreground(art: Art, pen: Pen, layer_lights: list) -> None:
    """A stack of files at each side, from below, and the pipe of a tube
    across the top of the view."""
    for u0, u1, h in ((0.04, 0.10, 0.03), (0.11, 0.155, 0.02), (0.84, 0.91, 0.035)):
        for k in range(int(h / 0.005)):
            v = 0.70 - k * 0.005
            pen.rect(u0 + (k % 2) * 0.002, v - 0.004, u1 - ((k + 1) % 2) * 0.002, v)
    pen.rect(-0.02, 0.352, 1.02, 0.366)
    for u in (0.2, 0.6):
        pen.rect(u, 0.348, u + 0.01, 0.370)
