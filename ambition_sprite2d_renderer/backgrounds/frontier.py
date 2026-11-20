"""The scenes of the Frontier dimension: Dry Dock, the spaceport town in the
Leaden Saddle (gate address LEADENSADDLE, `docs/planning/game/leadensaddle.md`).

`frontier`: the town in the pass. A hot afternoon under a sky that goes from
deep blue to amber, a pale ringed planet and two small moons in it. Far off,
two mesas in bands of red rock with the saddle between them, the stacks of
the refinery on the east mesa with a flare, and the gantries of the landing
pads with a freighter docked at one. Nearer, the backs of the town: false
fronts, a water tower, telegraph poles.

`frontier_refinery`: the flank of the east mesa, close: cracking towers,
tanks, pipe racks, a flare stack, in the low sun.

`frontier_interior`: the inside of a frontier building (the saloon, the
livery): board walls, posts, windows full of amber light.

Nothing on a backdrop is writing (the game draws some backdrops mirrored).
"""

from __future__ import annotations

import math

import numpy as np

from .artkit import Art, Pen, mix, scale, smoothstep
from .parts import HORIZON, cloud_mask, fog, haze, solid

FRONTIER = {
    "top": (40, 70, 120),
    "high": (92, 126, 168),
    "mid": (214, 160, 108),
    "low": (244, 196, 128),
    "haze": (240, 206, 160),
    "sun": (255, 236, 190),
    "planet": (236, 218, 196),
    "planet_shade": (170, 150, 150),
    "ring": (250, 236, 210),
    "moon": (226, 214, 200),
    "mesa": (178, 92, 62),
    "mesa_light": (222, 140, 92),
    "mesa_dark": (112, 58, 46),
    "steel": (88, 84, 92),
    "steel_light": (150, 140, 136),
    "flare": (255, 168, 72),
    "wood": (120, 78, 50),
    "wood_light": (170, 116, 72),
    "wood_dark": (64, 40, 28),
    "dust": (232, 190, 140),
}


def _mesa(pen: Pen, u0: float, u1: float, top: float, base: float, step: float) -> None:
    """A flat-topped mesa from `u0` to `u1`: steep sides with a ledge, a talus
    slope at its foot."""
    w = u1 - u0
    pen.poly([
        (u0 - w * 0.10, base), (u0 + w * 0.02, base - (base - top) * 0.30), (u0 + w * 0.06, top + step),
        (u0 + w * 0.10, top + step), (u0 + w * 0.12, top), (u1 - w * 0.10, top), (u1 - w * 0.08, top + step * 0.6),
        (u1 - w * 0.04, top + step * 0.6), (u1 + w * 0.02, base - (base - top) * 0.35), (u1 + w * 0.14, base),
    ])


def _strata(art: Art, layer: np.ndarray, mask: np.ndarray, v0: float, v1: float, light, dark) -> None:
    """Bands of rock across a mesa: lighter and darker layers."""
    bands = 0.5 + 0.5 * np.sin((art.v - v0) / max(1e-3, v1 - v0) * math.tau * 3.5 + art.noise("strata wobble", cells=6.0, octaves=2) * 1.5)
    art.put(layer, mask * smoothstep(0.55, 0.85, bands) * 0.35, light)
    art.put(layer, mask * smoothstep(0.45, 0.15, bands) * 0.25, dark)


def _gantry(pen: Pen, u: float, base: float, h: float, w: float) -> None:
    """A launch gantry: two legs, cross bracing, an arm out at the top."""
    leg = w * 0.12
    pen.rect(u, base - h, u + leg, base)
    pen.rect(u + w - leg, base - h, u + w, base)
    for k in range(5):
        y = base - h * (k + 0.5) / 5.0
        pen.line([(u, y), (u + w, y - h * 0.1)], w * 0.03)
        pen.line([(u, y - h * 0.1), (u + w, y)], w * 0.03)
    pen.rect(u - w * 0.4, base - h, u + w * 1.6, base - h + h * 0.05)


def _freighter(pen: Pen, u: float, base: float, length: float) -> None:
    """A stubby freighter standing on its landing legs, nose up and to the right."""
    h = length * 0.38
    body = [(u, base - h * 0.35), (u + length * 0.15, base - h), (u + length * 0.82, base - h * 0.92),
            (u + length, base - h * 0.55), (u + length * 0.86, base - h * 0.25), (u + length * 0.1, base - h * 0.18)]
    pen.poly(body)
    pen.rect(u + length * 0.2, base - h * 1.25, u + length * 0.42, base - h * 0.9)
    for x in (0.18, 0.5, 0.8):
        pen.line([(u + length * x, base - h * 0.2), (u + length * (x - 0.05), base)], length * 0.02)
        pen.rect(u + length * (x - 0.09), base - length * 0.012, u + length * (x - 0.01), base)


def _false_fronts(pen: Pen, windows: Pen, rng, u0: float, u1: float, foot: float, h0: float, h1: float, w0: float, w1: float) -> None:
    """A row of frontier buildings seen from behind and the side: square false
    fronts higher than their roofs, some with a stepped top."""
    u = u0
    while u < u1:
        w = rng.uniform(w0, w1)
        h = rng.uniform(h0, h1)
        top = foot - h
        pen.rect(u, top, u + w, foot + 0.2)
        kind = rng.choice(["flat", "step", "gable", "flat"])
        if kind == "step":
            pen.rect(u + w * 0.2, top - h * 0.12, u + w * 0.8, top)
            pen.rect(u + w * 0.38, top - h * 0.2, u + w * 0.62, top - h * 0.12)
        elif kind == "gable":
            pen.poly([(u - w * 0.04, top), (u + w * 1.04, top), (u + w * 0.5, top - w * 0.3)])
        if rng.random() < 0.6:
            for k in range(rng.randint(1, 3)):
                cu = u + (k + 0.6) * w / 3.4
                windows.rect(cu, top + h * 0.3, cu + w * 0.12, top + h * 0.55)
        u += w + rng.uniform(0.0, w0 * 0.4)


def _water_tower(pen: Pen, u: float, base: float, h: float, w: float) -> None:
    tank_top = base - h
    pen.rect(u, tank_top + h * 0.12, u + w, tank_top + h * 0.45)
    pen.poly([(u - w * 0.08, tank_top + h * 0.12), (u + w * 0.5, tank_top), (u + w * 1.08, tank_top + h * 0.12)])
    for x in (0.08, 0.92):
        pen.line([(u + w * x, tank_top + h * 0.45), (u + w * (x * 1.3 - 0.15), base)], w * 0.06)
    pen.line([(u + w * 0.1, tank_top + h * 0.7), (u + w * 0.9, tank_top + h * 0.6)], w * 0.03)


def _pole(pen: Pen, u: float, base: float, h: float) -> None:
    pen.rect(u - 0.0025, base - h, u + 0.0025, base)
    pen.rect(u - 0.02, base - h * 0.92, u + 0.02, base - h * 0.9)


def _refinery(pen: Pen, flares: list, rng, u0: float, u1: float, foot: float, scale_: float) -> None:
    """Cracking towers, tanks, stacks and pipe racks between `u0` and `u1`."""
    u = u0
    while u < u1:
        kind = rng.choice(["tower", "tank", "stack", "rack", "tank"])
        if kind == "tower":
            w, h = 0.022 * scale_, rng.uniform(0.12, 0.2) * scale_
            pen.rect(u, foot - h, u + w, foot)
            for k in range(4):
                y = foot - h * (k + 1) / 5.0
                pen.rect(u - w * 0.4, y, u + w * 1.4, y + 0.003 * scale_)
            pen.rect(u + w * 0.3, foot - h - 0.02 * scale_, u + w * 0.7, foot - h)
            u += w * 2.2
        elif kind == "tank":
            w, h = rng.uniform(0.04, 0.07) * scale_, rng.uniform(0.04, 0.07) * scale_
            pen.rect(u, foot - h, u + w, foot)
            pen.ellipse(u + w * 0.5, foot - h, w * 0.5, w * 0.12)
            u += w * 1.15
        elif kind == "stack":
            w, h = 0.008 * scale_, rng.uniform(0.18, 0.26) * scale_
            pen.rect(u, foot - h, u + w, foot)
            flares.append((u + w * 0.5, foot - h))
            u += w * 4.0
        else:
            w = rng.uniform(0.05, 0.09) * scale_
            for k in range(3):
                y = foot - 0.02 * scale_ - k * 0.014 * scale_
                pen.rect(u, y, u + w, y + 0.004 * scale_)
            for x in (0.0, 0.5, 1.0):
                pen.rect(u + w * x - 0.002, foot - 0.05 * scale_, u + w * x + 0.002, foot)
            u += w * 1.1


def _flare(art: Art, layer: np.ndarray, at, size: float, colour) -> None:
    art.light(layer, art.spot(at[0], at[1], size * 3.0, 2.0), colour, 0.45)
    flame, pen = art.drawing()
    pen.poly([(at[0] - size * 0.3, at[1]), (at[0] + size * 0.3, at[1]), (at[0] + size * 0.15, at[1] - size * 1.6), (at[0], at[1] - size * 2.4)])
    art.put(layer, art.mask_of(flame, blur=0.6), colour)


def _sky(art: Art, p: dict, sun_at, planet: bool) -> np.ndarray:
    layer = art.opaque(art.ramp([(0.0, p["top"]), (0.26, p["high"]), (0.46, p["mid"]), (HORIZON - 0.01, p["low"]), (HORIZON + 0.06, p["haze"]), (1.0, p["haze"])]))
    art.light(layer, art.spot(sun_at[0], sun_at[1], 0.5, 1.8), p["sun"], 0.40)
    art.light(layer, art.spot(sun_at[0], sun_at[1], 0.08, 1.6), p["sun"], 0.85)
    art.light(layer, cloud_mask(art, "streaks", 0.36, 0.05, cells=3.0, cover=0.30, soft=0.3, stretch=6.0), (255, 236, 214), 0.35)
    if planet:
        # The ringed planet, pale in the day sky, and two small moons.
        cu, cv, r = 0.70, 0.33, 0.07
        disc, pen = art.drawing()
        pen.ellipse(cu, cv, r)
        body = art.mask_of(disc, blur=0.4)
        face = art.ramp([(cv - r, p["planet"]), (cv + r, p["planet_shade"])])
        bands = 0.5 + 0.5 * np.sin((art.v - cv) * 140.0 + art.noise("planet bands", cells=8.0, octaves=2) * 2.0)
        art.put(layer, body, face, 0.55)
        art.tint(layer, body * bands, p["planet_shade"], 0.12)
        ring, ring_pen = art.drawing()
        ring_pen.ellipse(cu, cv, r * 2.1, r * 0.42)
        ring_pen.ellipse(cu, cv, r * 1.55, r * 0.26, value=0)
        ring_mask = art.mask_of(ring, blur=0.4)
        # The ring passes behind the planet above its middle.
        ring_mask = ring_mask * np.where(art.v < cv, 1.0 - body, 1.0)
        art.put(layer, ring_mask, p["ring"], 0.45)
        for mu, mv, mr in ((0.24, 0.24, 0.012), (0.33, 0.30, 0.007)):
            m, mp = art.drawing()
            mp.ellipse(mu, mv, mr)
            art.put(layer, art.mask_of(m, blur=0.3), p["moon"], 0.6)
    return layer


def frontier(layer_key: str, art: Art) -> np.ndarray:
    p = FRONTIER
    if layer_key == "sky":
        layer = _sky(art, p, (0.18, HORIZON - 0.14), planet=True)
        # The two mesas far off, with the saddle between them, in the colour of the air.
        far, pen = art.drawing()
        _mesa(pen, -0.05, 0.36, HORIZON - 0.13, HORIZON + 0.04, 0.03)
        _mesa(pen, 0.62, 1.05, HORIZON - 0.10, HORIZON + 0.04, 0.025)
        pen.poly([(0.30, HORIZON + 0.04), (0.36, HORIZON - 0.04), (0.50, HORIZON - 0.02), (0.64, HORIZON - 0.05), (0.70, HORIZON + 0.04)])
        mesas = art.mask_of(far, blur=0.5)
        art.put(layer, mesas, mix(p["mesa"], p["mid"], 0.55))
        _strata(art, layer, mesas, HORIZON - 0.13, HORIZON + 0.04, mix(p["mesa_light"], p["mid"], 0.5), mix(p["mesa_dark"], p["mid"], 0.5))
        art.light(layer, art.rim(mesas, 0.003, 0.0, 0.6) * mesas, p["sun"], 0.35)
        art.tint(layer, fog(art, "far dust", HORIZON + 0.02, 0.06), p["haze"], 0.55)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        rng = art.rand("far town")
        land, line = art.ridge("saddle floor", HORIZON + 0.08, 0.008, cells=2.0, octaves=2)
        image, pen = art.drawing()
        flares: list = []
        # The pads: gantries, a docked freighter, a second ship coming down.
        _gantry(pen, 0.08, HORIZON + 0.08, 0.16, 0.03)
        _freighter(pen, 0.12, HORIZON + 0.08, 0.16)
        _gantry(pen, 0.30, HORIZON + 0.08, 0.12, 0.025)
        # The refinery on the east side of the pass.
        _refinery(pen, flares, rng, 0.58, 0.98, HORIZON + 0.08, 1.0)
        body = np.clip(land + art.mask_of(image), 0, 1)
        layer = solid(art, body, mix(p["steel_light"], p["haze"], 0.45), mix(p["mesa"], p["haze"], 0.35), HORIZON - 0.15, HORIZON + 0.12, "dust", 0.05)
        art.light(layer, art.rim(body, 0.003, 0.0, 0.5) * body, p["sun"], 0.30)
        for at in flares:
            _flare(art, layer, at, 0.008, p["flare"])
        # Smoke from the stacks drifts east.
        for at in flares:
            art.put(layer, art.spot(at[0] + 0.05, at[1] - 0.05, 0.06, 2.0, squash=2.5) * 0.6, mix((110, 100, 96), p["haze"], 0.4), 0.5)
        haze(art, layer, p["haze"], 0.22, HORIZON + 0.09)
        return layer
    if layer_key == "near_background":
        rng = art.rand("near town")
        image, pen = art.drawing()
        wins, win_pen = art.drawing()
        foot = 0.80
        _false_fronts(pen, win_pen, rng, -0.02, 1.02, foot, 0.10, 0.20, 0.06, 0.11)
        _water_tower(pen, 0.70, foot - 0.08, 0.26, 0.06)
        for u in (0.05, 0.31, 0.57, 0.83):
            _pole(pen, u, foot, 0.32)
        pen.rect(0.0, foot, 1.0, 1.0)
        wire, wire_pen = art.drawing()
        for a, b in ((0.05, 0.31), (0.31, 0.57), (0.57, 0.83), (0.83, 1.09)):
            wire_pen.curve((a, foot - 0.29), (b, foot - 0.29), 0.03, 0.0012)
        body = art.mask_of(image)
        layer = art.blank()
        planks = 0.5 + 0.5 * np.sin(art.u * 900.0)
        paint = art.ramp([(0.0, p["wood_light"]), (0.6, p["wood"]), (1.0, p["wood_dark"])])
        paint = paint * (0.92 + 0.08 * planks)[:, :, None]
        art.put(layer, body, paint)
        art.put(layer, art.mask_of(wins) * body, (64, 48, 40))
        art.put(layer, art.mask_of(wire, blur=0.3), p["wood_dark"], 0.8)
        art.light(layer, art.rim(body, 0.003, 0.0, 0.4) * body, p["sun"], 0.35)
        art.shade(layer, art.rim(body, -0.004, 0.0, 0.8) * body, 0.12)
        haze(art, layer, p["haze"], 0.20, None)
        return layer
    # The air: dust low down, a little heat haze.
    layer = art.blank()
    art.put(layer, fog(art, "blown dust", 0.74, 0.10, cells=3.0), p["dust"], 0.25)
    art.put(layer, smoothstep(0.60, 0.85, art.v) * 0.5, p["haze"], 0.12)
    return layer


def frontier_refinery(layer_key: str, art: Art) -> np.ndarray:
    p = dict(FRONTIER, mid=(222, 140, 92), low=(250, 184, 112), haze=(236, 180, 130))
    if layer_key == "sky":
        layer = _sky(art, p, (0.82, HORIZON - 0.08), planet=False)
        far, pen = art.drawing()
        _mesa(pen, 0.40, 1.10, HORIZON - 0.16, HORIZON + 0.04, 0.03)
        mesas = art.mask_of(far, blur=0.5)
        art.put(layer, mesas, mix(p["mesa"], p["mid"], 0.45))
        _strata(art, layer, mesas, HORIZON - 0.16, HORIZON + 0.04, mix(p["mesa_light"], p["mid"], 0.4), mix(p["mesa_dark"], p["mid"], 0.4))
        art.tint(layer, fog(art, "refinery smog", HORIZON - 0.02, 0.08), (150, 120, 110), 0.35)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        rng = art.rand("far refinery")
        land, _ = art.ridge("refinery shelf", HORIZON + 0.07, 0.01, cells=2.0, octaves=2)
        image, pen = art.drawing()
        flares: list = []
        _refinery(pen, flares, rng, -0.02, 1.02, HORIZON + 0.07, 1.4)
        body = np.clip(land + art.mask_of(image), 0, 1)
        layer = solid(art, body, mix(p["steel_light"], p["haze"], 0.35), mix(p["steel"], p["haze"], 0.3), HORIZON - 0.2, HORIZON + 0.1, "rust", 0.06)
        art.light(layer, art.rim(body, -0.003, 0.0, 0.5) * body, p["flare"], 0.40)
        for at in flares:
            _flare(art, layer, at, 0.011, p["flare"])
        haze(art, layer, p["haze"], 0.20, HORIZON + 0.08)
        return layer
    if layer_key == "near_background":
        image, pen = art.drawing()
        # Big pipes along the shelf, their elbows, a tank half in view.
        foot = 0.80
        for k, v in enumerate((foot - 0.06, foot - 0.13)):
            pen.rect(-0.02, v, 1.02, v + 0.025 - 0.006 * k)
        # Riser pipes that bend over at the top and run off east.
        for u in (0.12, 0.44, 0.76):
            pen.rect(u, foot - 0.30, u + 0.025, foot)
            pen.ellipse(u + 0.025, foot - 0.30, 0.025, 0.025)
            pen.rect(u + 0.025, foot - 0.325, u + 0.12, foot - 0.30)
            pen.rect(u + 0.10, foot - 0.335, u + 0.11, foot - 0.29)
        pen.rect(0.55, foot - 0.22, 0.70, foot)
        pen.ellipse(0.625, foot - 0.22, 0.075, 0.02)
        pen.rect(0.0, foot, 1.0, 1.0)
        body = art.mask_of(image)
        layer = solid(art, body, (122, 104, 96), (60, 50, 50), 0.4, 0.9, "rust", 0.10)
        art.light(layer, art.rim(body, -0.003, 0.0, 0.5) * body, p["flare"], 0.45)
        haze(art, layer, p["haze"], 0.18, None)
        return layer
    layer = art.blank()
    art.put(layer, fog(art, "steam", 0.62, 0.14, cells=2.5), (240, 236, 232), 0.18)
    art.put(layer, fog(art, "low dust", 0.78, 0.08, cells=3.0), p["dust"], 0.22)
    return layer


def frontier_interior(layer_key: str, art: Art) -> np.ndarray:
    p = FRONTIER
    if layer_key == "sky":
        # The back wall: boards, a dado rail, windows of amber light.
        planks = 0.5 + 0.5 * np.sin(art.u * 520.0 + art.noise("grain", cells=12.0, octaves=2) * 1.5)
        paint = art.ramp([(0.0, (70, 44, 30)), (0.5, (104, 66, 42)), (1.0, (64, 40, 28))])
        layer = art.opaque(paint * (0.88 + 0.12 * planks)[:, :, None])
        image, pen = art.drawing()
        for u in (0.12, 0.42, 0.72):
            pen.rect(u, 0.34, u + 0.14, 0.56)
        windows = art.mask_of(image, blur=0.6)
        art.put(layer, windows, p["low"])
        art.light(layer, art.blur(windows, 18.0), p["low"], 0.5)
        bars, bar_pen = art.drawing()
        for u in (0.12, 0.42, 0.72):
            bar_pen.rect(u + 0.067, 0.34, u + 0.073, 0.56)
            bar_pen.rect(u, 0.444, u + 0.14, 0.452)
        art.put(layer, art.mask_of(bars), (60, 40, 28))
        rail, rail_pen = art.drawing()
        rail_pen.rect(0.0, 0.64, 1.0, 0.655)
        art.put(layer, art.mask_of(rail), (52, 32, 22))
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        # Posts and a beam: the frame of the building.
        image, pen = art.drawing()
        for u in (0.0, 0.33, 0.66):
            pen.rect(u, 0.0, u + 0.025, 1.0)
        pen.rect(0.0, 0.22, 1.0, 0.25)
        body = art.mask_of(image)
        layer = solid(art, body, (90, 58, 38), (54, 34, 24), 0.2, 0.9, "wood", 0.10)
        return layer
    if layer_key == "near_background":
        return art.blank()
    layer = art.blank()
    art.put(layer, fog(art, "pipe smoke", 0.42, 0.10, cells=2.5), (230, 210, 180), 0.12)
    return layer


def frontier_foreground(art: Art, pen: Pen, layer_lights: list) -> None:
    """A telegraph wire across the top of the view, and from below a fence
    post and dry grass."""
    for a, b, sag in ((-0.1, 0.42, 0.03), (0.42, 0.95, 0.035)):
        pen.curve((a, 0.372), (b, 0.372), sag, 0.0016)
    rng = art.rand("frontier grass")
    for u in (0.18, 0.66):
        pen.rect(u, 0.60, u + 0.008, 0.70)
        pen.rect(u - 0.002, 0.60, u + 0.010, 0.604)
    for _ in range(14):
        u = rng.random()
        h = rng.uniform(0.012, 0.03)
        for k in range(3):
            lean = rng.uniform(-0.008, 0.008)
            pen.poly([(u + k * 0.003, 0.70), (u + k * 0.003 + 0.0015, 0.70), (u + k * 0.003 + lean, 0.70 - h)])


def refinery_foreground(art: Art, pen: Pen, layer_lights: list) -> None:
    """A big pipe across the top of the view on its hangers, and a valve
    wheel on a riser from below."""
    pen.rect(-0.02, 0.36, 1.02, 0.375)
    for u in (0.1, 0.4, 0.7):
        pen.rect(u, 0.33, u + 0.004, 0.36)
    for u in (0.28, 0.82):
        pen.rect(u, 0.61, u + 0.012, 0.70)
        pen.ring(u + 0.006, 0.612, 0.016, 0.003)
