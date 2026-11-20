"""The scenes of the Frontier's first slice, west of Dry Dock (Ambition's
`docs/planning/game/techno-western-frontier-first-slice.md`).

`frontier_siding`: Halfway Siding on the rim of the gulch, mid-morning. A
pale blue sky going to dust at the horizon, the ringed planet low in it; the
far rim of the gulch in red and buff bands, buttes beyond it; nearer, the
backs of a few houses, a windmill and a line of telegraph poles. The trestle
itself is in the play plane (its own room's art), so it is not here.

`frontier_rails`: the floor of the gulch seen from a train at speed. The
rooms of the freight scroll it (`sky_scroll`), each layer at its own rate
and wrapped every two panels (every other one mirrored), so nothing on it is
writing and its two edges need not match. Walls of banded rock close in on
both sides, a strip of sky above; nearer, boulders and telegraph poles.

`frontier_works`: Clinker Flats, the smelter town down the line, at noon
under its own smoke. Stacks and furnace houses on a terrace, slag heaps with
a glowing pour down one, cranes; nearer, tin shacks and a water tank.

Nothing on a backdrop is writing (the game draws some backdrops mirrored).
"""

from __future__ import annotations

import numpy as np

from .artkit import Art, Pen, mix, scale, smoothstep
from .frontier import FRONTIER, _flare, _mesa, _pole, _sky, _strata, _water_tower
from .parts import HORIZON, fog, haze, solid

SIDING = dict(
    FRONTIER,
    top=(46, 92, 150),
    high=(110, 156, 196),
    mid=(196, 186, 168),
    low=(232, 206, 168),
    haze=(236, 214, 186),
    mesa=(170, 104, 74),
    mesa_light=(220, 168, 120),
    mesa_dark=(108, 64, 50),
)

RAILS = dict(
    FRONTIER,
    top=(70, 110, 160),
    high=(140, 170, 196),
    mid=(220, 190, 150),
    low=(236, 200, 150),
    haze=(226, 190, 150),
    rock=(150, 82, 56),
    rock_light=(206, 136, 92),
    rock_dark=(86, 44, 34),
)

WORKS = dict(
    FRONTIER,
    top=(66, 70, 92),
    high=(122, 112, 118),
    mid=(176, 140, 116),
    low=(206, 160, 118),
    haze=(170, 140, 120),
    smoke=(92, 84, 84),
    slag=(64, 56, 58),
    slag_light=(118, 100, 96),
    glow=(255, 140, 50),
    iron=(70, 64, 66),
    iron_light=(140, 124, 116),
    tin=(128, 120, 112),
)


# ---------------------------------------------------------------------------
# Halfway Siding
# ---------------------------------------------------------------------------


def _buttes(pen: Pen, rng, u0: float, u1: float, base: float, h0: float, h1: float) -> None:
    """Far mesas and buttes: a flat cap rock, sheer cliffs down most of the
    height, then a straight talus slope out to the foot, which runs under the
    far rim. Mostly broad mesas, now and then a narrow butte."""
    u = u0 + rng.uniform(0.0, 0.05)
    while u < u1:
        w = rng.uniform(0.03, 0.06) if rng.random() < 0.3 else rng.uniform(0.1, 0.24)
        top = base - rng.uniform(h0, h1) * (0.75 if w < 0.07 else 1.0)
        cliff = top + (base - top) * 0.72
        talus = (base - top) * 0.4
        pen.poly([(u - talus, base + 0.04), (u - 0.004, cliff), (u, top), (u + w, top), (u + w + 0.004, cliff),
                  (u + w + talus, base + 0.04)])
        u += w + talus + rng.uniform(0.05, 0.2)


def _windmill(pen: Pen, u: float, base: float, h: float) -> None:
    """A stock windmill: a lattice tower, its wheel of vanes and its tail."""
    w = h * 0.22
    pen.line([(u - w * 0.5, base), (u - w * 0.1, base - h)], h * 0.018)
    pen.line([(u + w * 0.5, base), (u + w * 0.1, base - h)], h * 0.018)
    for k in range(4):
        y = base - h * (k + 1) / 5.0
        f = 1.0 - (k + 1) / 5.0
        pen.line([(u - w * 0.5 * f - w * 0.1, y), (u + w * 0.5 * f + w * 0.1, y)], h * 0.01)
    cu, cv = u, base - h - h * 0.02
    for k in range(12):
        a = k * np.pi / 6.0
        pen.line([(cu, cv), (cu + np.cos(a) * h * 0.16, cv + np.sin(a) * h * 0.16)], h * 0.012)
    pen.ring(cu, cv, h * 0.15, h * 0.012)
    pen.poly([(cu, cv - h * 0.01), (cu + h * 0.22, cv - h * 0.04), (cu + h * 0.22, cv + h * 0.03), (cu, cv + h * 0.01)])


def _houses(pen: Pen, wins: Pen, rng, u0: float, u1: float, foot: float) -> None:
    """The backs of a few houses with pitched tin roofs and stovepipes, spread
    out, with yard between them."""
    u = u0
    while u < u1:
        w = rng.uniform(0.06, 0.1)
        h = rng.uniform(0.06, 0.1)
        top = foot - h
        pen.rect(u, top, u + w, foot + 0.2)
        pen.poly([(u - w * 0.06, top), (u + w * 1.06, top), (u + w * 0.5, top - w * 0.32)])
        pen.rect(u + w * 0.75, top - w * 0.38, u + w * 0.8, top - w * 0.1)
        if rng.random() < 0.7:
            wins.rect(u + w * 0.3, top + h * 0.3, u + w * 0.45, top + h * 0.6)
        u += w + rng.uniform(0.05, 0.16)


def frontier_siding(layer_key: str, art: Art) -> np.ndarray:
    p = SIDING
    if layer_key == "sky":
        layer = _sky(art, p, (0.78, HORIZON - 0.22), planet=True)
        rng = art.rand("siding buttes")
        far, pen = art.drawing()
        _buttes(pen, rng, -0.04, 1.04, HORIZON + 0.02, 0.07, 0.15)
        buttes = art.mask_of(far, blur=0.5)
        art.put(layer, buttes, mix(p["mesa"], p["mid"], 0.62))
        _strata(art, layer, buttes, HORIZON - 0.16, HORIZON - 0.02, mix(p["mesa_light"], p["mid"], 0.55), mix(p["mesa_dark"], p["mid"], 0.55))
        art.tint(layer, fog(art, "far haze", HORIZON - 0.01, 0.05), p["haze"], 0.6)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        # The far rim of the gulch: a long wall of banded rock with a flat top,
        # notched where side canyons come in; the gulch itself a dark cleft
        # under it.
        body, _ = art.ridge("far rim", HORIZON + 0.02, 0.012, cells=3.0, octaves=3)
        layer = art.blank()
        art.put(layer, body, mix(p["mesa"], p["haze"], 0.3))
        _strata(art, layer, body, HORIZON, HORIZON + 0.2, mix(p["mesa_light"], p["haze"], 0.25), mix(p["mesa_dark"], p["haze"], 0.25))
        art.light(layer, art.rim(body, 0.0, 0.004, 0.6) * body, p["sun"], 0.3)
        cleft = art.band(HORIZON + 0.16, 0.035, 2.0) * body
        art.shade(layer, cleft, 0.45)
        haze(art, layer, p["haze"], 0.28, HORIZON + 0.05)
        return layer
    if layer_key == "near_background":
        rng = art.rand("siding houses")
        image, pen = art.drawing()
        wins, win_pen = art.drawing()
        foot = 0.80
        _houses(pen, win_pen, rng, 0.02, 0.98, foot)
        _windmill(pen, 0.47, foot, 0.22)
        _water_tower(pen, 0.82, foot, 0.20, 0.05)
        for u in (0.12, 0.38, 0.64, 0.90):
            _pole(pen, u, foot, 0.30)
        pen.rect(0.0, foot, 1.0, 1.0)
        wire, wire_pen = art.drawing()
        for a, b in ((0.12, 0.38), (0.38, 0.64), (0.64, 0.90), (0.90, 1.16), (-0.14, 0.12)):
            wire_pen.curve((a, foot - 0.276), (b, foot - 0.276), 0.025, 0.0012)
        body = art.mask_of(image)
        layer = art.blank()
        paint = art.ramp([(0.0, (176, 150, 128)), (0.6, (136, 108, 84)), (1.0, (96, 74, 58))])
        art.put(layer, body, paint)
        art.put(layer, art.mask_of(wins) * body, (70, 60, 56))
        art.put(layer, art.mask_of(wire, blur=0.3), (80, 60, 46), 0.8)
        art.light(layer, art.rim(body, -0.003, 0.0, 0.4) * body, p["sun"], 0.3)
        haze(art, layer, p["haze"], 0.24, None)
        return layer
    layer = art.blank()
    art.put(layer, fog(art, "rim dust", 0.76, 0.08, cells=3.0), p["dust"], 0.2)
    return layer


# ---------------------------------------------------------------------------
# The gulch at speed
# ---------------------------------------------------------------------------


def _boulders(pen: Pen, rng, foot: float, count: int, r0: float, r1: float) -> None:
    for _ in range(count):
        u = rng.random()
        r = rng.uniform(r0, r1)
        pen.ellipse(u, foot - r * 0.5, r * 1.3, r * 0.8)


def frontier_rails(layer_key: str, art: Art) -> np.ndarray:
    p = RAILS
    if layer_key == "sky":
        # A strip of sky between the gulch's walls, the far wall in the air's
        # colour.
        layer = art.opaque(art.ramp([(0.0, p["top"]), (0.3, p["high"]), (0.55, p["mid"]), (1.0, p["haze"])]))
        art.light(layer, art.spot(0.3, 0.15, 0.4, 2.0), p["sun"], 0.3)
        wall, _ = art.ridge("far wall", 0.30, 0.05, cells=4.0, octaves=4)
        art.put(layer, wall, mix(p["rock"], p["haze"], 0.55))
        _strata(art, layer, wall, 0.3, 0.9, mix(p["rock_light"], p["haze"], 0.5), mix(p["rock_dark"], p["haze"], 0.5))
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        # The near wall of the gulch: banded cliffs with ledges, darker below.
        wall, _ = art.ridge("near wall", 0.42, 0.07, cells=5.0, octaves=4)
        layer = art.blank()
        paint = art.ramp([(0.3, p["rock_light"]), (0.7, p["rock"]), (1.0, p["rock_dark"])])
        art.put(layer, wall, paint)
        _strata(art, layer, wall, 0.4, 1.0, p["rock_light"], p["rock_dark"])
        ledges = 0.5 + 0.5 * np.sin(art.v * 90.0 + art.noise("ledges", cells=6.0, octaves=2) * 3.0)
        art.shade(layer, wall * smoothstep(0.85, 1.0, ledges), 0.25)
        streaks = art.noise("varnish", cells=3.0, octaves=2, stretch=0.08)
        streaks = smoothstep(0.62, 0.8, streaks) * smoothstep(0.42, 0.75, art.v)
        art.tint(layer, wall * streaks, (60, 34, 30), 0.35)
        art.light(layer, art.rim(wall, 0.0, 0.004, 0.6) * wall, p["sun"], 0.3)
        haze(art, layer, p["haze"], 0.2, 0.7)
        return layer
    if layer_key == "near_background":
        # Boulders and scrub on the gulch floor beside the line, and the
        # telegraph poles that follow it.
        rng = art.rand("gulch floor")
        image, pen = art.drawing()
        foot = 0.84
        pen.rect(0.0, foot, 1.0, 1.0)
        _boulders(pen, rng, foot + 0.005, 9, 0.012, 0.05)
        for u in (0.1, 0.43, 0.76):
            _pole(pen, u, foot, 0.34)
        wire, wire_pen = art.drawing()
        for a, b in ((0.1, 0.43), (0.43, 0.76), (0.76, 1.09), (-0.23, 0.1)):
            wire_pen.curve((a, foot - 0.316), (b, foot - 0.316), 0.03, 0.0012)
        body = art.mask_of(image)
        layer = solid(art, body, p["rock_light"], p["rock_dark"], 0.6, 1.0, "gulch stones", 0.10)
        art.put(layer, art.mask_of(wire, blur=0.3), (70, 50, 40), 0.8)
        art.light(layer, art.rim(body, 0.0, 0.004, 0.5) * body, p["sun"], 0.3)
        return layer
    # The dust the train raises, low down.
    layer = art.blank()
    art.put(layer, fog(art, "train dust", 0.86, 0.08, cells=4.0), p["dust"], 0.35)
    return layer


# ---------------------------------------------------------------------------
# Clinker Flats
# ---------------------------------------------------------------------------


def _stack(pen: Pen, u: float, foot: float, h: float, w: float) -> tuple[float, float]:
    """A brick smelter stack with a band near its top; its mouth."""
    pen.poly([(u - w * 0.6, foot), (u + w * 0.6, foot), (u + w * 0.45, foot - h), (u - w * 0.45, foot - h)])
    pen.rect(u - w * 0.55, foot - h, u + w * 0.55, foot - h + w * 0.25)
    return u, foot - h


def _furnace_house(pen: Pen, u: float, foot: float, w: float, h: float) -> None:
    """A long shed with a monitor roof (a raised strip of windows along it)."""
    pen.rect(u, foot - h, u + w, foot)
    pen.poly([(u - w * 0.02, foot - h), (u + w * 1.02, foot - h), (u + w * 0.8, foot - h * 1.3), (u + w * 0.2, foot - h * 1.3)])
    pen.rect(u + w * 0.3, foot - h * 1.5, u + w * 0.7, foot - h * 1.3)


def _crane(pen: Pen, u: float, foot: float, h: float, reach: float) -> None:
    """A gantry crane's leg and its boom, a hook on a cable."""
    pen.line([(u, foot), (u, foot - h)], 0.006)
    pen.line([(u + 0.03, foot), (u + 0.03, foot - h)], 0.006)
    for k in range(5):
        y = foot - h * (k + 0.5) / 5
        pen.line([(u, y), (u + 0.03, y - h * 0.08)], 0.003)
    pen.rect(u - 0.01, foot - h - 0.012, u + reach, foot - h)
    pen.line([(u + reach * 0.8, foot - h), (u + reach * 0.8, foot - h * 0.55)], 0.0015)
    pen.ring(u + reach * 0.8, foot - h * 0.53, 0.006, 0.002)


def frontier_works(layer_key: str, art: Art) -> np.ndarray:
    p = WORKS
    if layer_key == "sky":
        layer = art.opaque(art.ramp([(0.0, p["top"]), (0.3, p["high"]), (0.5, p["mid"]), (HORIZON, p["low"]), (1.0, p["haze"])]))
        art.light(layer, art.spot(0.62, 0.18, 0.3, 2.0), (255, 220, 170), 0.45)
        # The town's own smoke, in long brown banks across the sky.
        from .parts import cloud_mask
        smoke = cloud_mask(art, "smoke banks", 0.28, 0.12, cells=3.0, cover=0.5, soft=0.35, stretch=4.0)
        art.put(layer, smoke, p["smoke"], 0.45)
        far, pen = art.drawing()
        _mesa(pen, -0.1, 0.3, HORIZON - 0.08, HORIZON + 0.04, 0.02)
        _mesa(pen, 0.7, 1.1, HORIZON - 0.06, HORIZON + 0.04, 0.02)
        mesas = art.mask_of(far, blur=0.5)
        art.put(layer, mesas, mix(p["mesa"], p["haze"], 0.78))
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        # The works on its terrace: stacks, furnace houses, a crane; slag
        # heaps either side, one with a glowing pour down it.
        land, _ = art.ridge("works terrace", HORIZON + 0.06, 0.006, cells=2.0, octaves=2)
        image, pen = art.drawing()
        mouths = []
        for u, h in ((0.30, 0.30), (0.36, 0.34), (0.55, 0.26), (0.70, 0.32)):
            mouths.append(_stack(pen, u, HORIZON + 0.06, h, 0.018))
        _furnace_house(pen, 0.26, HORIZON + 0.06, 0.16, 0.08)
        _furnace_house(pen, 0.52, HORIZON + 0.06, 0.22, 0.07)
        _crane(pen, 0.78, HORIZON + 0.06, 0.16, 0.12)
        heaps, heap_pen = art.drawing()
        heap_pen.poly([(-0.05, HORIZON + 0.07), (0.08, HORIZON - 0.06), (0.22, HORIZON + 0.07)])
        heap_pen.poly([(0.84, HORIZON + 0.07), (0.95, HORIZON - 0.04), (1.08, HORIZON + 0.07)])
        heap = art.mask_of(heaps, blur=0.6)
        body = np.clip(land + art.mask_of(image), 0, 1)
        layer = solid(art, body, mix(p["iron_light"], p["haze"], 0.35), mix(p["iron"], p["haze"], 0.25), HORIZON - 0.3, HORIZON + 0.1, "soot", 0.08)
        art.put(layer, heap, mix(p["slag"], p["haze"], 0.25))
        art.light(layer, art.rim(heap, 0.002, 0.0, 0.5) * heap, p["slag_light"], 0.3)
        # The pour: a bright run of slag down the west heap's face.
        pour, pour_pen = art.drawing()
        pour_pen.line([(0.08, HORIZON - 0.055), (0.11, HORIZON - 0.02), (0.13, HORIZON + 0.02), (0.16, HORIZON + 0.06)], 0.006)
        pmask = art.mask_of(pour, blur=0.6)
        art.light(layer, art.blur(pmask, 10.0), p["glow"], 0.6)
        art.put(layer, pmask, (255, 196, 96))
        # Furnace glow in the shed windows, smoke from the stacks.
        art.light(layer, art.band(HORIZON + 0.02, 0.02, 2.0) * art.mask_of(image), p["glow"], 0.25)
        for at in mouths:
            art.put(layer, art.spot(at[0] + 0.06, at[1] - 0.06, 0.08, 2.0, squash=2.5) * 0.7, p["smoke"], 0.6)
            _flare(art, layer, at, 0.004, p["glow"])
        haze(art, layer, p["haze"], 0.22, HORIZON + 0.07)
        return layer
    if layer_key == "near_background":
        rng = art.rand("clinker shacks")
        image, pen = art.drawing()
        wins, win_pen = art.drawing()
        foot = 0.80
        u = -0.02
        while u < 1.02:
            w = rng.uniform(0.05, 0.09)
            h = rng.uniform(0.05, 0.09)
            top = foot - h
            pen.rect(u, top, u + w, foot + 0.2)
            # A lean-to roof, high at one side.
            if rng.random() < 0.5:
                pen.poly([(u - w * 0.05, top), (u + w * 1.05, top - h * 0.25), (u + w * 1.05, top), (u - w * 0.05, top + h * 0.04)])
            else:
                pen.poly([(u - w * 0.05, top - h * 0.25), (u + w * 1.05, top), (u + w * 1.05, top + h * 0.04), (u - w * 0.05, top)])
            pen.rect(u + w * 0.15, top - h * 0.6, u + w * 0.2, top)
            if rng.random() < 0.6:
                win_pen.rect(u + w * 0.5, top + h * 0.3, u + w * 0.7, top + h * 0.55)
            u += w + rng.uniform(0.0, 0.05)
        _water_tower(pen, 0.62, foot - 0.04, 0.24, 0.05)
        pen.rect(0.0, foot, 1.0, 1.0)
        body = art.mask_of(image)
        layer = solid(art, body, p["tin"], (54, 50, 50), 0.5, 0.95, "rust", 0.12)
        art.put(layer, art.mask_of(wins) * body, (255, 190, 110), 0.85)
        art.light(layer, art.rim(body, 0.0, 0.004, 0.4) * body, (255, 210, 160), 0.25)
        haze(art, layer, p["haze"], 0.2, None)
        return layer
    layer = art.blank()
    art.put(layer, fog(art, "soot", 0.5, 0.2, cells=2.5), p["smoke"], 0.18)
    art.put(layer, fog(art, "ash", 0.8, 0.08, cells=3.0), (140, 130, 126), 0.25)
    return layer


# ---------------------------------------------------------------------------
# Foregrounds
# ---------------------------------------------------------------------------


def siding_foreground(art: Art, pen: Pen, layer_lights: list) -> None:
    """A telegraph wire across the top, a fence post and dry grass below."""
    for a, b, sag in ((-0.1, 0.5, 0.03), (0.5, 1.1, 0.03)):
        pen.curve((a, 0.37), (b, 0.37), sag, 0.0016)
    rng = art.rand("siding grass")
    for u in (0.3, 0.8):
        pen.rect(u, 0.61, u + 0.008, 0.70)
    for _ in range(12):
        u = rng.random()
        h = rng.uniform(0.012, 0.03)
        for k in range(3):
            lean = rng.uniform(-0.008, 0.008)
            pen.poly([(u + k * 0.003, 0.70), (u + k * 0.003 + 0.0015, 0.70), (u + k * 0.003 + lean, 0.70 - h)])


def rails_foreground(art: Art, pen: Pen, layer_lights: list) -> None:
    """Scrub and stones flying past low down; a pole's crossarm at the top."""
    rng = art.rand("rails scrub")
    for _ in range(10):
        u = rng.random()
        r = rng.uniform(0.006, 0.016)
        pen.ellipse(u, 0.70, r * 1.6, r)
    pen.rect(0.55, 0.34, 0.6, 0.346)
    pen.rect(0.574, 0.34, 0.578, 0.40)


def works_foreground(art: Art, pen: Pen, layer_lights: list) -> None:
    """A crane's chain and hook hanging into the view, and a heap of cinders."""
    pen.rect(0.32, 0.30, 0.334, 0.31)
    for k in range(10):
        pen.ellipse(0.327, 0.315 + k * 0.008, 0.003, 0.005)
    pen.ring(0.327, 0.40, 0.012, 0.004)
    pen.poly([(0.7, 0.70), (0.78, 0.66), (0.86, 0.70)])
