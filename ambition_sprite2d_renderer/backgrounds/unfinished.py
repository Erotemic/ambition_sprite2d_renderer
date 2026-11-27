"""The scenes of the Unfinished dimension, the one the Boss's agents are still
building (gate address INSTALLING, `docs/planning/game/unfinished-dimension.md`).

Jon (2026-11-24) found the concept sheets too colourful, so the palette here
is held down: blueprint paper, unpainted greys, muted greens, and one accent,
the yellow of a hard hat.

`unfinished`: the building site. A sky of pale blueprint paper with its grid
showing through where the sky is not painted yet; panels of finished sky hung
on wires, waiting to go up. Far off, a range of hills and a castle, painted
at the west and still a wire drawing at the east. Nearer, scaffold towers and
a crane, work lamps on them, and trees drawn only in outline.

`unfinished_void`: where nothing is built yet. Dark, a grid under it all
running off to nowhere, a dim spiral of stars, slabs of concrete waiting to
be placed, the outlines of domes that are only plans.

Nothing on a backdrop is writing (the game draws some backdrops mirrored).
"""

from __future__ import annotations

import math

import numpy as np

from .artkit import Art, Pen, mix, smoothstep
from .parts import HORIZON, fog, haze, lamps, solid

SITE = {
    "paper": (200, 206, 216),
    "paper_low": (184, 186, 200),
    "grid": (226, 232, 240),
    "ink": (120, 140, 176),
    "sky": (150, 176, 210),
    "sky_low": (196, 200, 212),
    "cloud": (236, 238, 242),
    "hill": (120, 140, 116),
    "hill_far": (150, 160, 150),
    "rock": (138, 132, 136),
    "stone": (196, 190, 184),
    "steel": (74, 78, 90),
    "steel_light": (120, 124, 138),
    "hat": (232, 190, 70),
    "lamp": (255, 224, 160),
    "leaf": (110, 132, 104),
    "haze": (200, 202, 212),
}

VOID = {
    "top": (14, 16, 26),
    "mid": (24, 26, 40),
    "low": (36, 38, 56),
    "grid": (70, 80, 120),
    "star": (200, 204, 220),
    "spiral": (150, 140, 180),
    "slab": (44, 47, 65),
    "slab_light": (72, 78, 102),
    "wire": (110, 130, 180),
    "haze": (40, 42, 64),
}


def _wire(art: Art, layer: np.ndarray, image, colour, strength: float = 0.8) -> None:
    """Lay a wire drawing (thin lines) on a layer, with a faint glow."""
    m = art.mask_of(image, blur=0.4)
    art.put(layer, m, colour, strength)
    art.light(layer, art.blur(m, 3.0), colour, 0.2)


def _hills(pen: Pen, u0: float, u1: float, foot: float, rng, peak: float, n: int) -> list[tuple[float, float]]:
    """A run of hill tops from `u0` to `u1`; returns the outline."""
    pts = [(u0, foot)]
    for k in range(n + 1):
        u = u0 + (u1 - u0) * k / n
        pts.append((u, foot - peak * (0.4 + 0.6 * rng.random())))
    pts.append((u1, foot))
    pen.poly(pts)
    return pts


def _castle(pen: Pen, u: float, foot: float, s: float) -> None:
    pen.rect(u - s, foot - s * 0.9, u + s, foot)
    for dx in (-s, s):
        pen.rect(u + dx - s * 0.22, foot - s * 1.5, u + dx + s * 0.22, foot)
        pen.poly([(u + dx - s * 0.28, foot - s * 1.5), (u + dx + s * 0.28, foot - s * 1.5), (u + dx, foot - s * 1.9)])
    pen.rect(u - s * 0.25, foot - s * 1.25, u + s * 0.25, foot - s * 0.9)


def _wire_tree(pen: Pen, u: float, foot: float, h: float, w: float) -> None:
    """A tree drawn only in outline: its trunk and the round of its crown."""
    pen.line([(u, foot), (u, foot - h * 0.45)], 0.0015)
    pen.line([(u - w * 0.08, foot), (u - w * 0.04, foot - h * 0.45)], 0.0015)
    pen.ring(u, foot - h * 0.7, w * 0.5, 0.0015)
    pen.ring(u - w * 0.25, foot - h * 0.55, w * 0.3, 0.0015)
    pen.ring(u + w * 0.25, foot - h * 0.58, w * 0.32, 0.0015)


def _scaffold(pen: Pen, u: float, foot: float, h: float, w: float) -> list[tuple[float, float]]:
    """A scaffold tower: two posts, decks, crossed braces. Returns where its
    work lamps hang."""
    for x in (u, u + w):
        pen.rect(x - 0.003, foot - h, x + 0.003, foot)
    decks = int(h / 0.08)
    out = []
    for k in range(decks + 1):
        v = foot - k * (h / decks)
        pen.rect(u - 0.006, v - 0.004, u + w + 0.006, v)
        if k < decks:
            v2 = v - h / decks
            pen.line([(u, v), (u + w, v2)], 0.0018)
            pen.line([(u + w, v), (u, v2)], 0.0018)
        if k % 2 == 1:
            out.append((u + w + 0.01, v + 0.01))
    return out


def _crane(pen: Pen, u: float, foot: float, h: float, jib: float) -> tuple[float, float]:
    """A tower crane: a lattice mast, its jib and counter-jib, a cab. Returns
    the hook."""
    w = 0.014
    pen.rect(u - w / 2, foot - h, u + w / 2, foot)
    for k in range(int(h / 0.02)):
        v = foot - k * 0.02
        pen.line([(u - w / 2, v), (u + w / 2, v - 0.02)], 0.0012)
    top = foot - h
    pen.rect(u - jib * 0.3, top - 0.008, u + jib, top)
    pen.poly([(u - 0.004, top - 0.008), (u + 0.004, top - 0.008), (u, top - 0.04)])
    pen.line([(u, top - 0.04), (u + jib * 0.8, top - 0.008)], 0.0012)
    pen.line([(u, top - 0.04), (u - jib * 0.28, top - 0.008)], 0.0012)
    pen.rect(u - jib * 0.3, top, u - jib * 0.18, top + 0.02)
    hook = (u + jib * 0.7, top + 0.16)
    pen.line([(hook[0], top), hook], 0.001)
    return hook


# ---------------------------------------------------------------------------
# The building site
# ---------------------------------------------------------------------------


def unfinished(layer_key: str, art: Art) -> np.ndarray:
    p = SITE
    if layer_key == "sky":
        # Blueprint paper, its grid, and the sky painted over part of it.
        layer = art.opaque(art.ramp([(0.0, p["paper"]), (HORIZON, p["paper"]), (1.0, p["paper_low"])]))
        grid = (smoothstep(0.985, 0.999, np.abs(np.cos(art.u * math.pi * 24.0))) + smoothstep(0.985, 0.999, np.abs(np.cos(art.v * math.pi * 24.0)))).clip(0, 1)
        art.put(layer, grid, p["ink"], 0.35)
        # The painted sky: a rough band from the west, as if rolled on.
        painted = smoothstep(0.62, 0.48, art.u + 0.08 * art.noise("roller edge", cells=6.0, octaves=3))
        painted = painted * smoothstep(HORIZON + 0.05, HORIZON - 0.05, art.v)
        art.put(layer, painted, art.ramp([(0.0, p["sky"]), (HORIZON, p["sky_low"])]), 0.9)
        art.put(layer, painted * art.noise("painted clouds", cells=4.0, octaves=4, stretch=2.5).clip(0.55, 1.0) - painted * 0.55, p["cloud"], 0.5)
        # Panels of finished sky hung on wires, waiting to be put up.
        wires, w_pen = art.drawing()
        panels, p_pen = art.drawing()
        clouds, c_pen = art.drawing()
        for k, (u, v) in enumerate(((0.58, 0.16), (0.70, 0.20), (0.82, 0.16))):
            w_pen.line([(u - 0.03, 0.0), (u - 0.03, v - 0.03)], 0.001)
            w_pen.line([(u + 0.03, 0.0), (u + 0.03, v - 0.03)], 0.001)
            p_pen.rect(u - 0.04, v - 0.03, u + 0.04, v + 0.03)
            c_pen.ellipse(u - 0.01, v + 0.008, 0.02, 0.01)
            c_pen.ellipse(u + 0.012, v + 0.004, 0.016, 0.009)
        art.put(layer, art.mask_of(wires, blur=0.3), p["steel_light"], 0.8)
        pm = art.mask_of(panels, blur=0.3)
        art.put(layer, pm, mix(p["sky"], p["paper"], 0.2))
        art.put(layer, art.mask_of(clouds, blur=0.6) * pm, p["cloud"], 0.9)
        art.shade(layer, art.rim(pm, 0.0, 0.004, 0.3) * pm, 0.2)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        # Hills and a castle: painted at the west, wire at the east.
        rng = art.rand("site hills")
        image, pen = art.drawing()
        foot = HORIZON + 0.08
        _hills(pen, -0.02, 1.02, foot, rng, 0.16, 9)
        _castle(pen, 0.38, foot - 0.1, 0.035)
        pen.rect(-0.02, foot, 1.02, 1.0)
        body = art.mask_of(image)
        paint_side = smoothstep(0.62, 0.50, art.u + 0.05 * art.noise("paint edge", cells=5.0, octaves=3))
        layer = solid(art, body * paint_side, mix(p["hill_far"], p["haze"], 0.3), mix(p["hill"], p["haze"], 0.25), HORIZON - 0.2, HORIZON + 0.1, "hills", 0.06)
        art.light(layer, art.rim(body, -0.004, -0.003, 0.5) * body * paint_side, p["cloud"], 0.25)
        castle, c_pen = art.drawing()
        _castle(c_pen, 0.38, foot - 0.1, 0.035)
        art.put(layer, art.mask_of(castle) * paint_side, mix(p["stone"], p["haze"], 0.3))
        # The wire half: the outline of what is still to be painted.
        edge = np.clip(body - art.blur(body, 1.2) * 0.0, 0, 1)
        outline = np.clip(art.rim(body, 0.0, 0.003, 0.0) + art.rim(body, 0.003, 0.0, 0.0), 0, 1) * body
        wire_side = 1.0 - paint_side
        art.put(layer, outline * wire_side, p["ink"], 0.8)
        lattice = (smoothstep(0.90, 0.97, np.abs(np.cos(art.u * math.pi * 60.0))) + smoothstep(0.90, 0.97, np.abs(np.cos(art.v * math.pi * 60.0)))).clip(0, 1)
        art.put(layer, lattice * body * wire_side * edge, p["ink"], 0.35)
        haze(art, layer, p["haze"], 0.18, foot)
        return layer
    if layer_key == "near_background":
        # Scaffold towers, a crane with a slab on its hook, trees in outline.
        image, pen = art.drawing()
        lamp_at = []
        lamp_at += _scaffold(pen, 0.04, 0.86, 0.36, 0.07)
        lamp_at += _scaffold(pen, 0.80, 0.86, 0.28, 0.06)
        hook = _crane(pen, 0.30, 0.86, 0.5, 0.26)
        pen.rect(-0.02, 0.86, 1.02, 1.0)
        body = art.mask_of(image)
        layer = solid(art, body, p["steel_light"], p["steel"], 0.3, 0.9, "steel", 0.05)
        art.light(layer, art.rim(body, -0.003, 0.0, 0.4) * body, p["cloud"], 0.2)
        slab, s_pen = art.drawing()
        s_pen.line([(hook[0], hook[1]), (hook[0] - 0.03, hook[1] + 0.03)], 0.001)
        s_pen.line([(hook[0], hook[1]), (hook[0] + 0.03, hook[1] + 0.03)], 0.001)
        s_pen.rect(hook[0] - 0.04, hook[1] + 0.03, hook[0] + 0.04, hook[1] + 0.06)
        art.put(layer, art.mask_of(slab, blur=0.3), mix(p["hill"], p["rock"], 0.5))
        hats, h_pen = art.drawing()
        h_pen.rect(0.20, 0.355, 0.235, 0.375)
        art.put(layer, art.mask_of(hats, blur=0.3), p["hat"])
        trees, t_pen = art.drawing()
        for u in (0.48, 0.58, 0.70):
            _wire_tree(t_pen, u, 0.86, 0.16, 0.06)
        _wire(art, layer, trees, p["ink"], 0.75)
        lamps(art, layer, [(u, v, 0.004) for u, v in lamp_at], p["lamp"], halo=4.0, strength=0.6)
        haze(art, layer, p["haze"], 0.1, None)
        return layer
    layer = art.blank()
    art.put(layer, fog(art, "site dust", 0.80, 0.10, cells=3.0), p["haze"], 0.25)
    return layer


# ---------------------------------------------------------------------------
# The Void
# ---------------------------------------------------------------------------


def unfinished_void(layer_key: str, art: Art) -> np.ndarray:
    p = VOID
    if layer_key == "sky":
        layer = art.opaque(art.ramp([(0.0, p["top"]), (0.5, p["mid"]), (1.0, p["low"])]))
        rng = art.rand("void stars")
        stars, s_pen = art.drawing()
        for _ in range(160):
            s_pen.ellipse(rng.random(), rng.random(), rng.uniform(0.0008, 0.002), value=rng.randint(80, 255))
        art.light(layer, art.mask_of(stars, blur=0.4), p["star"], 0.7)
        # A dim spiral of stars, low.
        cu, cv = 0.62, 0.74
        r = np.hypot((art.u - cu) * 1.0, (art.v - cv) * 2.4)
        a = np.arctan2((art.v - cv) * 2.4, art.u - cu)
        arms = 0.5 + 0.5 * np.cos(2.0 * a - r * 40.0)
        spiral = arms * smoothstep(0.22, 0.0, r)
        art.light(layer, spiral, p["spiral"], 0.35)
        art.light(layer, smoothstep(0.03, 0.0, r), p["star"], 0.4)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        # The grid under everything, running off to nowhere, and the
        # outlines of domes that are only plans.
        layer = art.blank()
        horizon = HORIZON + 0.05
        lines, l_pen = art.drawing()
        for k in range(-20, 21):
            l_pen.line([(0.5 + k * 0.01, horizon), (0.5 + k * 0.12, 1.1)], 0.0012)
        v = horizon
        step = 0.006
        while v < 1.0:
            l_pen.line([(-0.02, v), (1.02, v)], 0.0012)
            step *= 1.35
            v += step
        grid = art.mask_of(lines, blur=0.4) * smoothstep(horizon - 0.01, horizon + 0.15, art.v)
        art.put(layer, grid, p["grid"], 0.6)
        domes, d_pen = art.drawing()
        for u, w in ((0.18, 0.12), (0.84, 0.16)):
            for k in range(5):
                d_pen.arc(u, horizon, w * (1 - k * 0.18), 180.0, 360.0, 0.0012)
            for k in range(-3, 4):
                d_pen.line([(u + k * w / 4, horizon), (u + k * w / 8, horizon - w * math.sqrt(max(0.0, 1 - (k / 4) ** 2)))], 0.0012)
        _wire(art, layer, domes, p["wire"], 0.55)
        return layer
    if layer_key == "near_background":
        # Tilt the distant blocks so their edges differ from the walkable decks.
        rng = art.rand("void slabs")
        image, pen = art.drawing()
        faces, face_pen = art.drawing()
        for _ in range(9):
            u, v = rng.random(), rng.uniform(0.25, 0.8)
            w, h = rng.uniform(0.03, 0.06), rng.uniform(0.010, 0.018)
            tilt = rng.choice((-1, 1)) * h
            left = (u - w, v - h - tilt)
            ridge = (u + w * 0.36, v - h)
            right = (u + w, v + tilt * 0.65)
            pen.poly([left, ridge, right, (u + w * 0.77, v + h + tilt),
                      (u - w * 0.65, v + h - tilt * 0.45)])
            face_pen.poly([left, ridge, right, (u - w * 0.25, v)])
        body = art.mask_of(image)
        layer = solid(art, body, p["slab_light"], p["slab"], 0.2, 0.9, "slabs", 0.08)
        art.shade(layer, body * (1.0 - art.mask_of(faces)), 0.23)
        haze(art, layer, p["haze"], 0.35, None)
        return layer
    layer = art.blank()
    art.put(layer, fog(art, "void mist", 0.86, 0.10, cells=3.0), p["grid"], 0.12)
    return layer


# ---------------------------------------------------------------------------
# Foregrounds
# ---------------------------------------------------------------------------


def unfinished_foreground(art: Art, pen: Pen, layer_lights: list) -> None:
    """A strip of barrier tape on two posts, from below, and the end of a
    crane's cable across the top of the view."""
    for u in (0.08, 0.30):
        pen.rect(u - 0.003, 0.65, u + 0.003, 0.70)
    pen.rect(0.08, 0.656, 0.30, 0.664)
    pen.rect(0.72, 0.33, 0.724, 0.40)


def void_foreground(art: Art, pen: Pen, layer_lights: list) -> None:
    """A slab's corner from below, and a loose cable."""
    pen.poly([(0.84, 0.70), (0.98, 0.70), (0.98, 0.675), (0.86, 0.68)])
    pen.curve((0.10, 0.33), (0.20, 0.40), 0.02, 0.002)
