"""The scenes of the Central Hub, the Gate Authority's capital (gate address
LICENSED, `docs/planning/game/central-hub-dimension.md`).

`authority`: Authority Plaza, outdoors. A clear blue sky; far off, a gate
as big as a hill hangs in it, a triangle of gold-trimmed stone with the
wormhole turning inside, and islands float round it with towers on them and
water falling off their edges. Nearer, tall pale towers with lit slits;
nearest, the arches of a bridge across the city, commuters along its rail,
the Authority's banners on its piers.

`authority_hall`: the Concourse and the offices, indoors. A wall of cream
stone with tall arched windows; through them, more arches of the city and
a monorail on its rail. Steel-blue columns with gold collars, the
Authority's banners hung between them, lamps on long rods.

The Authority's sign is the gate's apex: a gold triangle, point up, on navy.
Nothing on a backdrop is writing (the game draws some backdrops mirrored).
"""

from __future__ import annotations

import math

import numpy as np

from .artkit import Art, Pen, mix, smoothstep
from .parts import HORIZON, cloud_mask, cumulus, fog, haze, lamps, solid

PLAZA = {
    "top": (70, 120, 200),
    "high": (120, 166, 230),
    "mid": (170, 200, 240),
    "low": (214, 222, 240),
    "haze": (200, 210, 236),
    "cloud": (250, 250, 255),
    "cloud_shade": (190, 196, 226),
    "sun": (255, 244, 214),
    "stone": (196, 190, 208),
    "stone_light": (232, 226, 236),
    "stone_dark": (120, 116, 146),
    "tower": (150, 156, 196),
    "tower_light": (206, 210, 236),
    "slit": (255, 226, 150),
    "gold": (226, 184, 92),
    "gold_light": (255, 226, 150),
    "wormhole": (120, 200, 255),
    "wormhole_light": (220, 240, 255),
    "island": (110, 140, 110),
    "island_rock": (130, 120, 150),
    "water": (210, 236, 255),
    "banner": (118, 40, 62),
    "navy": (40, 50, 96),
    "commuter": (60, 62, 90),
    "lamp": (255, 220, 150),
}

HALL = {
    "wall": (220, 206, 186),
    "wall_light": (240, 230, 212),
    "wall_dark": (160, 144, 128),
    "sky_top": (90, 150, 220),
    "sky_low": (190, 216, 244),
    "far": (150, 170, 214),
    "far_light": (200, 214, 240),
    "rail": (110, 124, 170),
    "train": (236, 240, 250),
    "train_glow": (120, 230, 255),
    "mullion": (70, 80, 110),
    "steel": (70, 84, 120),
    "steel_light": (120, 136, 176),
    "gold": (226, 184, 92),
    "navy": (34, 46, 96),
    "lamp": (255, 222, 160),
    "air": (200, 214, 240),
}


# ---------------------------------------------------------------------------
# Parts
# ---------------------------------------------------------------------------


def _triangle(cu: float, cv: float, r: float, squash: float = 1.0) -> list[tuple[float, float]]:
    """The corners of a triangle point up, its centre at `(cu, cv)`."""
    return [(cu + r * math.cos(math.radians(a)), cv - r * squash * math.sin(math.radians(a))) for a in (90.0, 210.0, 330.0)]


def _sign(pen: Pen, cu: float, cv: float, r: float) -> None:
    """The Authority's sign: the gate's apex, a triangle point up, open."""
    outer = _triangle(cu, cv, r)
    pen.line(outer + [outer[0]], r * 0.28)


def _banner(pen: Pen, sign: Pen, u: float, top: float, bottom: float, w: float) -> None:
    """A long swallowtailed banner on a rod, the sign on it."""
    pen.rect(u - w * 0.7, top - 0.004, u + w * 0.7, top)
    pen.poly([(u - w * 0.5, top), (u + w * 0.5, top), (u + w * 0.5, bottom), (u, bottom - w * 0.6), (u - w * 0.5, bottom)])
    _sign(sign, u, top + (bottom - top) * 0.36, w * 0.3)


def _island(pen: Pen, rock: Pen, towers: Pen, falls: Pen, rng, u: float, v: float, w: float) -> None:
    """A floating island: a cap of green, a cone of rock under it, a tower or
    two, and sometimes water falling off its edge."""
    pen.ellipse(u, v, w * 0.5, w * 0.08)
    rock.poly([(u - w * 0.5, v), (u + w * 0.5, v), (u + w * 0.15, v + w * 0.35), (u + w * 0.02, v + w * 0.55), (u - w * 0.12, v + w * 0.3)])
    for k in range(rng.randint(1, 2)):
        tu = u + rng.uniform(-0.3, 0.3) * w
        th = w * rng.uniform(0.4, 0.8)
        towers.rect(tu - w * 0.05, v - th, tu + w * 0.05, v)
        towers.poly([(tu - w * 0.07, v - th), (tu + w * 0.07, v - th), (tu, v - th - w * 0.14)])
    if rng.random() < 0.6:
        fu = u + rng.uniform(-0.3, 0.3) * w
        falls.rect(fu - w * 0.025, v, fu + w * 0.025, v + w * 0.9)


def _arches(pen: Pen, holes: Pen, u0: float, u1: float, deck: float, foot: float, span: float, thick: float) -> list[float]:
    """A bridge on arches from `u0` to `u1`: its deck at `deck`, its piers to
    `foot`. Returns the middle of each pier."""
    pen.rect(u0, deck, u1, deck + thick)
    piers = []
    u = u0
    while u < u1:
        pen.rect(u, deck, u + span, foot)
        a0, a1 = u + span * 0.14, u + span * 0.86
        r = (a1 - a0) / 2
        holes.rect(a0, deck + thick + r, a1, foot + 0.01)
        holes.ellipse((a0 + a1) / 2, deck + thick + r, r, r)
        piers.append(u + span * 0.07)
        u += span
    return piers


# ---------------------------------------------------------------------------
# Authority Plaza
# ---------------------------------------------------------------------------


def authority(layer_key: str, art: Art) -> np.ndarray:
    p = PLAZA
    if layer_key == "sky":
        layer = art.opaque(art.ramp([(0.0, p["top"]), (0.25, p["high"]), (0.48, p["mid"]), (HORIZON + 0.02, p["low"]), (1.0, p["haze"])]))
        art.light(layer, art.spot(0.22, 0.18, 0.5, 1.8), p["sun"], 0.3)
        clouds = cumulus(art, "authority clouds", 0.42, 0.10, cells=3.0, cover=0.40, light=p["cloud"], shadow=p["cloud_shade"])
        layer = art.over(layer, clouds * np.array([1, 1, 1, 0.8], dtype=np.float32))
        # The great gate in the sky: a triangle of stone, gold at its edges,
        # the wormhole turning inside it; chevron studs along its sides.
        cu, cv, r = 0.70, 0.34, 0.15
        outer = _triangle(cu, cv, r)
        inner = _triangle(cu, cv + r * 0.06, r * 0.68)
        frame, f_pen = art.drawing()
        f_pen.poly(outer)
        hole, h_pen = art.drawing()
        h_pen.poly(inner)
        hole_mask = art.mask_of(hole, blur=0.6)
        frame_mask = art.mask_of(frame, blur=0.6) * (1.0 - hole_mask)
        art.put(layer, frame_mask, mix(p["stone"], p["mid"], 0.35))
        art.light(layer, art.rim(frame_mask, 0.004, 0.004, 0.6) * frame_mask, p["gold_light"], 0.5)
        swirl = 0.5 + 0.5 * np.sin(np.arctan2(art.v - cv, art.u - cu) * 3.0 + np.hypot(art.u - cu, art.v - cv) * 60.0)
        art.put(layer, hole_mask, mix(p["wormhole"], p["mid"], 0.3))
        art.light(layer, hole_mask * swirl, p["wormhole_light"], 0.45)
        art.light(layer, art.blur(hole_mask, 18.0), p["wormhole"], 0.35)
        studs, s_pen = art.drawing()
        for a, b in zip(outer, outer[1:] + outer[:1]):
            for k in range(1, 6):
                t = k / 6
                s_pen.ellipse(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, 0.005)
        art.light(layer, art.mask_of(studs, blur=0.6), p["gold_light"], 0.8)
        art.light(layer, art.blur(art.mask_of(studs), 5.0), p["wormhole"], 0.4)
        # Islands float round it, far and pale.
        rng = art.rand("islands")
        isl, i_pen = art.drawing()
        rock, r_pen = art.drawing()
        tw, t_pen = art.drawing()
        falls, w_pen = art.drawing()
        for u, v, w in ((0.08, 0.20, 0.07), (0.34, 0.12, 0.05), (0.50, 0.34, 0.04), (0.92, 0.18, 0.06), (0.88, 0.46, 0.045)):
            _island(i_pen, r_pen, t_pen, w_pen, rng, u, v, w)
        art.put(layer, art.mask_of(rock, blur=0.5), mix(p["island_rock"], p["mid"], 0.55))
        art.put(layer, art.mask_of(tw, blur=0.5), mix(p["tower_light"], p["mid"], 0.45))
        art.put(layer, art.mask_of(isl, blur=0.5), mix(p["island"], p["mid"], 0.5))
        art.put(layer, art.mask_of(falls, blur=1.0), p["water"], 0.6)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        # The towers of the capital: tall and pale, a lit slit up each, a
        # spire or a dome on top.
        rng = art.rand("authority towers")
        image, pen = art.drawing()
        slits, s_pen = art.drawing()
        foot = HORIZON + 0.10
        u = -0.02
        while u < 1.02:
            w = rng.uniform(0.03, 0.055)
            h = rng.uniform(0.12, 0.30)
            pen.rect(u, foot - h, u + w, foot)
            if rng.random() < 0.5:
                pen.poly([(u - 0.003, foot - h), (u + w + 0.003, foot - h), (u + w / 2, foot - h - w * 1.4)])
            else:
                pen.ellipse(u + w / 2, foot - h, w * 0.5, w * 0.45)
            for k in range(2 if w > 0.04 else 1):
                su = u + w * (0.35 + 0.3 * k)
                s_pen.rect(su - 0.002, foot - h + 0.02, su + 0.002, foot - 0.02)
            u += w + rng.uniform(0.01, 0.05)
        pen.rect(-0.02, foot, 1.02, 1.0)
        body = art.mask_of(image)
        layer = solid(art, body, mix(p["tower_light"], p["haze"], 0.35), mix(p["tower"], p["haze"], 0.3), HORIZON - 0.3, HORIZON + 0.1, "towers", 0.04)
        art.light(layer, art.rim(body, -0.004, 0.0, 0.5) * body, p["sun"], 0.35)
        art.light(layer, art.mask_of(slits, blur=0.5) * body, p["slit"], 0.55)
        haze(art, layer, p["haze"], 0.22, foot)
        return layer
    if layer_key == "near_background":
        # A bridge on arches across the city, commuters along its rail, the
        # Authority's banners hung on its piers.
        image, pen = art.drawing()
        holes, h_pen = art.drawing()
        deck = 0.46
        piers = _arches(pen, h_pen, -0.02, 1.04, deck, 0.86, 0.13, 0.03)
        rail, r_pen = art.drawing()
        r_pen.rect(-0.02, deck - 0.018, 1.02, deck - 0.014)
        for u in np.arange(0.0, 1.0, 0.02):
            r_pen.rect(float(u), deck - 0.016, float(u) + 0.002, deck)
        people, p_pen = art.drawing()
        rng = art.rand("commuters")
        for _ in range(30):
            u = rng.random()
            h = rng.uniform(0.014, 0.018)
            p_pen.ellipse(u, deck - h, 0.0018, 0.0024)
            p_pen.poly([(u - 0.0026, deck - h + 0.003), (u + 0.0026, deck - h + 0.003), (u + 0.002, deck), (u - 0.002, deck)])
        pen.rect(-0.02, 0.86, 1.02, 1.0)
        body = art.mask_of(image) * (1.0 - art.mask_of(holes))
        layer = solid(art, body, mix(p["stone_light"], p["haze"], 0.2), mix(p["stone_dark"], p["haze"], 0.2), 0.45, 0.9, "bridge stone", 0.06)
        art.shade(layer, art.rim(body, 0.0, 0.004, 0.5) * body, 0.25)
        art.light(layer, art.rim(body, -0.003, 0.0, 0.4) * body, p["sun"], 0.3)
        art.put(layer, art.mask_of(rail, blur=0.3), mix(p["gold"], p["stone_dark"], 0.3))
        art.put(layer, art.mask_of(people, blur=0.3), mix(p["commuter"], p["haze"], 0.25))
        flags, f_pen = art.drawing()
        signs, s_pen = art.drawing()
        for k, u in enumerate(piers):
            if k % 2 == 0:
                _banner(f_pen, s_pen, u + 0.008, deck + 0.04, deck + 0.18, 0.026)
        art.put(layer, art.mask_of(flags, blur=0.3), p["banner"])
        art.put(layer, art.mask_of(signs, blur=0.3), p["gold"])
        haze(art, layer, p["haze"], 0.12, None)
        return layer
    # The air: a little haze low down, and blossom petals.
    layer = art.blank()
    art.put(layer, fog(art, "plaza haze", 0.78, 0.10, cells=3.0), p["haze"], 0.2)
    return layer


# ---------------------------------------------------------------------------
# The Concourse and the offices
# ---------------------------------------------------------------------------


def authority_hall(layer_key: str, art: Art) -> np.ndarray:
    p = HALL
    if layer_key == "sky":
        # Out of the windows: the sky, the arches of the city, a monorail.
        layer = art.opaque(art.ramp([(0.0, p["sky_top"]), (0.55, p["sky_low"]), (1.0, p["sky_low"])]))
        art.light(layer, cloud_mask(art, "hall clouds", 0.25, 0.08, cells=3.0, cover=0.35, soft=0.2), (255, 255, 255), 0.5)
        image, pen = art.drawing()
        holes, h_pen = art.drawing()
        _arches(pen, h_pen, -0.02, 1.04, 0.52, 0.9, 0.09, 0.02)
        _arches(pen, h_pen, -0.05, 1.04, 0.34, 0.52, 0.06, 0.012)
        far = art.mask_of(image, blur=0.5) * (1.0 - art.mask_of(holes, blur=0.5))
        art.put(layer, far, mix(p["far"], p["sky_low"], 0.35))
        art.light(layer, art.rim(far, -0.003, 0.0, 0.5) * far, (255, 255, 255), 0.25)
        rail, r_pen = art.drawing()
        r_pen.curve((-0.02, 0.30), (1.02, 0.24), -0.03, 0.006)
        art.put(layer, art.mask_of(rail, blur=0.4), mix(p["rail"], p["sky_low"], 0.3))
        train, t_pen = art.drawing()
        t_pen.rect(0.58, 0.225, 0.70, 0.250)
        t_pen.ellipse(0.70, 0.2375, 0.012, 0.0125)
        art.put(layer, art.mask_of(train, blur=0.4), p["train"])
        glow, g_pen = art.drawing()
        for k in range(4):
            g_pen.rect(0.595 + k * 0.026, 0.231, 0.613 + k * 0.026, 0.237)
        art.light(layer, art.mask_of(glow, blur=0.4), p["train_glow"], 0.8)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        # The hall's wall: cream stone, tall arched windows, their mullions.
        image, pen = art.drawing()
        pen.rect(-0.02, -0.02, 1.02, 1.02)
        windows, w_pen = art.drawing()
        mull, m_pen = art.drawing()
        for k in range(4):
            u0 = 0.06 + k * 0.25
            u1 = u0 + 0.13
            top = 0.26
            r = (u1 - u0) / 2
            w_pen.rect(u0, top, u1, 0.88)
            w_pen.ellipse(u0 + r, top, r, r)
            m_pen.rect((u0 + u1) / 2 - 0.002, top - r, (u0 + u1) / 2 + 0.002, 0.88)
            for v in np.arange(top + 0.14, 0.88, 0.14):
                m_pen.rect(u0, float(v) - 0.002, u1, float(v) + 0.002)
            m_pen.ring(u0 + r, top, r, 0.006)
        win = art.mask_of(windows, blur=0.4)
        body = art.mask_of(image) * (1.0 - win)
        layer = solid(art, body, p["wall_light"], p["wall"], 0.1, 0.9, "hall stone", 0.05)
        art.shade(layer, art.rim(win, 0.0, -0.004, 0.6) * body, 0.3)
        # Courses of stone, a line every so often.
        art.shade(layer, body * smoothstep(0.92, 1.0, np.abs(np.sin(art.v * math.pi * 24.0))), 0.12)
        art.put(layer, art.mask_of(mull, blur=0.3) * win, p["mullion"])
        art.light(layer, art.spot(0.5, 0.5, 0.7, 1.5) * body, p["wall_light"], 0.1)
        # The Authority's banners on the stone between the windows.
        flags, f_pen = art.drawing()
        signs, s_pen = art.drawing()
        for k in range(4):
            _banner(f_pen, s_pen, 0.25 * k, 0.24, 0.52, 0.04)
        art.put(layer, art.mask_of(flags, blur=0.3), p["navy"])
        art.put(layer, art.mask_of(signs, blur=0.3), p["gold"])
        haze(art, layer, p["air"], 0.10, None)
        return layer
    if layer_key == "near_background":
        # Columns with gold collars, lamps on rods between them.
        image, pen = art.drawing()
        collars, c_pen = art.drawing()
        for u in (0.0, 0.5, 1.0):
            pen.rect(u - 0.018, 0.0, u + 0.018, 1.0)
            for v in (0.18, 0.84):
                c_pen.rect(u - 0.024, v, u + 0.024, v + 0.016)
        # Lamps on long rods between the columns.
        rods, r_pen = art.drawing()
        points = []
        for u in (0.25, 0.75):
            r_pen.rect(u - 0.0012, 0.0, u + 0.0012, 0.36)
            points.append((u, 0.37, 0.006))
        body = art.mask_of(image)
        layer = solid(art, body, p["steel_light"], p["steel"], 0.0, 1.0, "columns", 0.05)
        art.light(layer, art.rim(body, -0.004, 0.0, 0.5) * body, p["wall_light"], 0.3)
        art.put(layer, art.mask_of(collars, blur=0.3), p["gold"])
        art.put(layer, art.mask_of(rods, blur=0.3), p["steel"])
        lamps(art, layer, points, p["lamp"], halo=5.0, strength=0.7)
        return layer
    # The air: daylight in long shafts from the windows.
    layer = art.blank()
    beams, b_pen = art.drawing()
    for k in range(4):
        u = 0.125 + k * 0.25
        b_pen.poly([(u - 0.06, 0.2), (u + 0.06, 0.2), (u + 0.16, 0.95), (u + 0.02, 0.95)])
    art.put(layer, art.mask_of(beams, blur=14.0), p["wall_light"], 0.12)
    return layer


# ---------------------------------------------------------------------------
# Foregrounds
# ---------------------------------------------------------------------------


def authority_foreground(art: Art, pen: Pen, layer_lights: list) -> None:
    """The tops of two clipped hedges from below, and the arm of a lamp post
    across the top of the view."""
    rng = art.rand("authority hedge")
    for u0, u1 in ((0.03, 0.20), (0.76, 0.94)):
        pen.rect(u0, 0.668, u1, 0.70)
        for k in range(int((u1 - u0) / 0.01)):
            pen.ellipse(u0 + k * 0.01 + 0.005, 0.668, 0.007, 0.005 + rng.uniform(0, 0.002))
    pen.rect(0.10, 0.33, 0.106, 0.40)
    pen.curve((0.106, 0.338), (0.17, 0.338), -0.01, 0.0025)


def hall_foreground(art: Art, pen: Pen, layer_lights: list) -> None:
    """A brass rope barrier on two posts, from below, and a lamp rod across
    the top of the view."""
    for u in (0.06, 0.20):
        pen.rect(u - 0.004, 0.64, u + 0.004, 0.70)
        pen.ellipse(u, 0.64, 0.007, 0.006)
    pen.curve((0.06, 0.646), (0.20, 0.646), 0.02, 0.003)
    pen.rect(-0.02, 0.352, 1.02, 0.360)
