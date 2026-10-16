"""The scenes of the Evil dimension: its dark forest and Castle Godwin.

The Evil dimension is its own place, and it must look evil at a glance: a sky
the colour of old blood under a lid of ash, black trees with thorns, the
fortress on its crag with searchlights that sweep the cloud, and in the castle
cold iron-grey stone, red banners with the mark of the regime and the light of
braziers. Nothing in it is warm or kind.

The mark of the regime is a black gear on a white disc on red (`emblem`). It
is an invented mark: the art shows no real symbol of a real regime.
"""

from __future__ import annotations

import math

import numpy as np

from .artkit import Art, Pen, mix, scale, smoothstep
from .parts import HORIZON, cloud_mask, fog, haze, lamps, shafts, solid, vignette

EVIL = {
    "top": (14, 8, 12),
    "mid": (58, 14, 18),
    "low": (150, 34, 26),
    "glow": (232, 86, 40),
    "ash": (44, 36, 40),
    "ash_lit": (120, 52, 44),
    "far": (36, 18, 24),
    "crag": (24, 14, 20),
    "near": (8, 6, 10),
    "near_rim": (190, 60, 40),
    "beam": (255, 236, 200),
    "window": (255, 120, 50),
    "fog": (110, 30, 30),
}

CASTLE = {
    "deep": (10, 10, 16),
    "stone": (78, 86, 104),
    "stone_dark": (34, 38, 50),
    "mortar": (20, 22, 30),
    "red": (150, 18, 22),
    "red_dark": (84, 8, 14),
    "white": (226, 222, 214),
    "black": (12, 10, 12),
    "fire": (255, 132, 48),
    "window": (220, 50, 30),
    "near": (16, 16, 22),
    "near_light": (70, 74, 90),
}


def emblem(pen_disc: Pen, pen_gear: Pen, cu: float, cv: float, r: float) -> None:
    """The mark of the regime at `(cu, cv)`, radius `r`: a white disc
    (`pen_disc`) and a black eight-tooth gear on it (`pen_gear`). The hole of
    the gear is drawn with value 0 on the gear's pen."""
    pen_disc.ellipse(cu, cv, r)
    teeth = 8
    pts = []
    for k in range(teeth * 4):
        a = math.tau * k / (teeth * 4)
        outer = (k % 4) in (1, 2)
        rr = r * (0.80 if outer else 0.60)
        pts.append((cu + rr * math.cos(a), cv + rr * math.sin(a)))
    pen_gear.poly(pts)
    pen_gear.ellipse(cu, cv, r * 0.22, value=0)


def _dead_tree(pen: Pen, rng, u: float, foot: float, h: float, w: float) -> None:
    """A black dead tree: a crooked trunk and bare branches that end in thorns."""
    lean = rng.uniform(-0.25, 0.25) * w
    top = foot - h
    pen.poly([(u - w * 0.5, foot), (u + w * 0.5, foot), (u + lean + w * 0.12, top), (u + lean - w * 0.12, top)])
    for _ in range(rng.randint(4, 7)):
        t = rng.uniform(0.25, 0.9)
        x0, y0 = u + lean * t, foot - h * t
        side = rng.choice((-1, 1))
        length = h * rng.uniform(0.18, 0.38) * (1.1 - t * 0.5)
        x1 = x0 + side * length * rng.uniform(0.6, 1.0)
        y1 = y0 - length * rng.uniform(0.3, 0.8)
        pen.line([(x0, y0), ((x0 + x1) / 2, (y0 + y1) / 2 + length * 0.05), (x1, y1)], w * 0.16 * (1.0 - t * 0.5))
        # Thorns along the branch.
        for s in (0.35, 0.6, 0.85):
            bx, by = x0 + (x1 - x0) * s, y0 + (y1 - y0) * s
            pen.poly([(bx - w * 0.04, by), (bx + w * 0.04, by), (bx + side * w * 0.05, by - w * 0.22)])


def _fortress(pen: Pen, windows: Pen, cu: float, base: float, s: float) -> None:
    """Castle Godwin far off on its crag: a keep with two towers, all with
    battlements, and slits of red light. `s` is its width in parts of the panel."""
    def block(u0, u1, top, merlons=True):
        pen.rect(u0, top, u1, base + 0.01)
        if merlons:
            n = max(2, int((u1 - u0) / (s * 0.06)))
            step = (u1 - u0) / n
            for k in range(n):
                if k % 2 == 0:
                    pen.rect(u0 + k * step, top - s * 0.035, u0 + (k + 1) * step, top)
    block(cu - s * 0.5, cu + s * 0.5, base - s * 0.30)
    block(cu - s * 0.2, cu + s * 0.2, base - s * 0.62)
    for side in (-1, 1):
        tu = cu + side * s * 0.42
        block(tu - s * 0.09, tu + s * 0.09, base - s * 0.55)
        pen.poly([(tu - s * 0.11, base - s * 0.585), (tu + s * 0.11, base - s * 0.585), (tu, base - s * 0.75)])
    for k in range(-3, 4):
        windows.rect(cu + k * s * 0.11 - s * 0.012, base - s * 0.22, cu + k * s * 0.11 + s * 0.012, base - s * 0.16)
    for k in (-1, 0, 1):
        windows.rect(cu + k * s * 0.10 - s * 0.012, base - s * 0.52, cu + k * s * 0.10 + s * 0.012, base - s * 0.45)


def evil_forest(layer_key: str, art: Art) -> np.ndarray:
    """The dark forest where the gate of the Evil dimension stands. Black
    thorned trees under a blood-red sky; far off, Castle Godwin on its crag,
    its searchlights in the ash cloud."""
    p = EVIL
    keep_u, crag_top = 0.66, HORIZON - 0.06
    if layer_key == "sky":
        layer = art.opaque(art.ramp([(0.0, p["top"]), (0.30, p["mid"]), (HORIZON - 0.03, p["low"]), (HORIZON + 0.05, p["mid"]), (1.0, p["top"])]))
        art.light(layer, art.spot(keep_u, HORIZON, 0.45, 1.8, squash=2.2), p["glow"], 0.45)
        # A lid of ash cloud, lit red from below.
        clouds = cloud_mask(art, "ash lid", 0.22, 0.14, cells=3.0, cover=0.55, soft=0.30, stretch=3.4)
        art.tint(layer, clouds, p["ash"], 0.85)
        art.light(layer, clouds * smoothstep(0.10, 0.36, art.v), p["ash_lit"], 0.45)
        # The searchlights of the fortress, up into the cloud.
        beams, pen = art.drawing()
        for lean, w in ((-0.30, 0.012), (0.22, 0.010), (-0.08, 0.008)):
            pen.poly([(keep_u - 0.002, crag_top - 0.08), (keep_u + 0.002, crag_top - 0.08), (keep_u + lean + w, 0.0), (keep_u + lean - w, 0.0)])
        art.light(layer, art.mask_of(beams, blur=3.0) * smoothstep(0.0, 0.3, art.v), p["beam"], 0.20)
        # The crag, and the far range of the hills.
        hills, _ = art.ridge("far hills", HORIZON + 0.02, 0.03, cells=4.0, octaves=4)
        art.tint(layer, hills, p["far"], 0.85)
        crag, cpen = art.drawing()
        # A jagged crag: broken steps of rock up to the keep's foot.
        cpen.poly([(keep_u - 0.22, HORIZON + 0.03), (keep_u - 0.17, HORIZON - 0.005), (keep_u - 0.14, HORIZON + 0.004),
                   (keep_u - 0.11, crag_top + 0.035), (keep_u - 0.085, crag_top + 0.04), (keep_u - 0.07, crag_top + 0.005),
                   (keep_u + 0.07, crag_top + 0.005), (keep_u + 0.085, crag_top + 0.03), (keep_u + 0.11, crag_top + 0.025),
                   (keep_u + 0.13, HORIZON - 0.01), (keep_u + 0.16, HORIZON), (keep_u + 0.20, HORIZON + 0.03)])
        windows, wpen = art.drawing()
        _fortress(cpen, wpen, keep_u, crag_top, 0.13)
        art.tint(layer, art.mask_of(crag, blur=0.4), p["crag"], 0.95)
        art.put(layer, art.mask_of(windows, blur=0.3), p["window"], 0.9)
        art.tint(layer, fog(art, "crag mist", HORIZON + 0.03, 0.04), p["fog"], 0.5)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        rng = art.rand("far dead wood")
        ground, line = art.ridge("dead ridge", HORIZON + 0.04, 0.02, cells=4.0, octaves=4)
        image, pen = art.drawing()
        for _ in range(34):
            u = rng.random()
            v = float(line[min(art.n - 1, int(u * art.n))])
            h = rng.uniform(0.06, 0.14)
            _dead_tree(pen, rng, u, v + 0.01, h, h * 0.10)
        # Fence posts with wire between them along the ridge.
        for u in np.arange(0.02, 1.0, 0.07):
            v = float(line[min(art.n - 1, int(u * art.n))])
            pen.rect(u - 0.0018, v - 0.035, u + 0.0018, v + 0.01)
            pen.line([(u, v - 0.03), (u + 0.07, float(line[min(art.n - 1, int((u + 0.07) * art.n))]) - 0.03)], 0.0012)
            pen.line([(u, v - 0.015), (u + 0.07, float(line[min(art.n - 1, int((u + 0.07) * art.n))]) - 0.015)], 0.0012)
        mask = np.maximum(ground, art.mask_of(image))
        layer = solid(art, mask, mix(p["far"], p["mid"], 0.3), p["far"], 0.36, 0.66, "bark", 0.06)
        art.light(layer, art.rim(mask, 0.0, -0.003, 0.6) * mask, p["glow"], 0.25)
        haze(art, layer, p["mid"], 0.22, HORIZON + 0.06)
        return layer
    if layer_key == "near_background":
        rng = art.rand("thorn grove")
        image, pen = art.drawing()
        ground, _ = art.ridge("ground", 0.70, 0.012, cells=5.0, octaves=3)
        # Black trees at each side, a few across.
        for _ in range(14):
            u = rng.choice([rng.uniform(-0.02, 0.22), rng.uniform(0.78, 1.02), rng.uniform(0.0, 1.0)])
            h = rng.uniform(0.32, 0.62)
            _dead_tree(pen, rng, u, 0.71, h, rng.uniform(0.018, 0.03))
        # Branches that hang over the view from above.
        canopy = smoothstep(0.55, 0.60, art.noise("thorn canopy", cells=8.0, octaves=5) * smoothstep(0.28, 0.08, art.v))
        mask = np.maximum.reduce([ground, art.mask_of(image), canopy])
        layer = solid(art, mask, p["near"], p["near"], 0.2, 0.8, "bark", 0.15)
        art.light(layer, art.rim(mask, 0.002, -0.003, 0.4) * mask, p["near_rim"], 0.40)
        haze(art, layer, p["mid"], 0.06, 0.74)
        return layer
    # Red fog low down, ash that drifts, and the dark at the edges.
    layer = art.blank()
    art.put(layer, fog(art, "blood fog", 0.70, 0.14), p["fog"], 0.40)
    art.put(layer, smoothstep(0.55, 0.85, art.v) * 0.5, p["mid"], 0.12)
    vignette(art, layer, p["top"], 0.45)
    return layer


def _courses(art: Art, rows: float, cols: float) -> np.ndarray:
    """The mortar of a wall of big blocks: `rows` courses and `cols` blocks
    across the panel, each course half a block along from the one under it."""
    fv = art.v * rows
    course = (np.mod(fv, 1.0) < 0.07).astype(np.float32)
    fu = art.u * cols + np.floor(fv) * 0.5
    joint = (np.mod(fu, 1.0) < 0.035).astype(np.float32)
    return np.maximum(course, joint)


def _banner(pen_red: Pen, pen_disc: Pen, pen_gear: Pen, cu: float, top: float, w: float, h: float) -> None:
    """A long red banner that hangs from `top`, its foot cut in a point, with
    the mark of the regime on it."""
    pen_red.poly([(cu - w / 2, top), (cu + w / 2, top), (cu + w / 2, top + h), (cu, top + h - w * 0.45), (cu - w / 2, top + h)])
    emblem(pen_disc, pen_gear, cu, top + h * 0.50, w * 0.36)


def castle_godwin(layer_key: str, art: Art) -> np.ndarray:
    """Inside Castle Godwin: halls of cold iron-grey blocks, slit windows that
    glow red from the fires outside, long red banners with the mark of the
    regime, chains, and braziers. The stone is the blue-grey of a fortress,
    in the dark."""
    p = CASTLE
    if layer_key == "sky":
        layer = art.opaque(art.ramp([(0.0, p["deep"]), (0.35, p["stone_dark"]), (0.62, mix(p["stone_dark"], p["red_dark"], 0.25)), (1.0, p["deep"])]))
        # The courses of the far wall: big blocks, staggered.
        art.shade(layer, art.blur(_courses(art, 22.0, 14.0), 0.4), 0.30)
        # Slit windows, far back, red with the fires outside.
        windows, wpen = art.drawing()
        for cu in np.arange(0.08, 1.0, 0.14):
            wpen.rect(cu - 0.006, 0.34, cu + 0.006, 0.50)
            wpen.ellipse(cu, 0.34, 0.006, 0.008)
        art.put(layer, art.mask_of(windows, blur=0.4), p["window"], 0.75)
        art.light(layer, art.mask_of(windows, blur=10.0), p["window"], 0.35)
        art.shade(layer, art.band(0.85, 0.25, 1.0), 0.3)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        # The great hall: square piers with battlemented capitals, the
        # banners between them.
        image, pen = art.drawing()
        reds, red_pen = art.drawing()
        discs, disc_pen = art.drawing()
        gears, gear_pen = art.drawing()
        span = 0.25
        for cu in np.arange(0.0, 1.0 + span, span):
            pen.rect(cu - 0.03, 0.12, cu + 0.03, 1.0)
            pen.rect(cu - 0.042, 0.20, cu + 0.042, 0.235)
            for k in range(3):
                pen.rect(cu - 0.042 + k * 0.032, 0.185, cu - 0.042 + k * 0.032 + 0.02, 0.20)
        pen.rect(0.0, 0.10, 1.0, 0.13)
        for cu in np.arange(span / 2, 1.0 + span, span):
            _banner(red_pen, disc_pen, gear_pen, cu, 0.13, 0.075, 0.50)
        body = art.mask_of(image)
        layer = solid(art, body, mix(p["stone"], p["stone_dark"], 0.35), p["stone_dark"], 0.2, 0.9, "stone", 0.10)
        art.shade(layer, art.blur(_courses(art, 30.0, 40.0), 0.3) * body, 0.35)
        art.light(layer, art.rim(body, -0.003, 0.0, 0.5) * body, p["fire"], 0.18)
        art.shade(layer, art.rim(body, 0.004, 0.0, 0.8) * body, 0.35)
        red = art.mask_of(reds)
        banner = solid(art, red, p["red"], p["red_dark"], 0.15, 0.6, "cloth", 0.10)
        layer = art.over(layer, banner)
        art.put(layer, art.mask_of(discs) * red, mix(p["white"], p["stone_dark"], 0.15))
        art.put(layer, art.mask_of(gears) * red, p["black"])
        art.shade(layer, art.rim(red, 0.003, 0.0, 0.6) * red, 0.30)
        haze(art, layer, p["deep"], 0.22, None)
        return layer
    if layer_key == "near_background":
        # Great piers at each side, chains, and a brazier on each pier.
        image, pen = art.drawing()
        chains, chain_pen = art.drawing()
        lights = []
        for cu, w in ((0.035, 0.06), (0.965, 0.06)):
            pen.rect(cu - w / 2, 0.0, cu + w / 2, 1.0)
            pen.rect(cu - w / 2 - 0.012, 0.68, cu + w / 2 + 0.012, 0.71)
            # The brazier: a bowl on a short stand.
            pen.poly([(cu - 0.024, 0.60), (cu + 0.024, 0.60), (cu + 0.014, 0.625), (cu - 0.014, 0.625)])
            pen.rect(cu - 0.004, 0.625, cu + 0.004, 0.68)
            lights.append((cu, 0.592, 0.008))
        for cu in (0.28, 0.72):
            chain_pen.line([(cu, 0.0), (cu, 0.24)], 0.0025)
            pen.poly([(cu - 0.016, 0.24), (cu + 0.016, 0.24), (cu + 0.010, 0.27), (cu - 0.010, 0.27)])
            lights.append((cu, 0.26, 0.006))
        mask = art.mask_of(image)
        layer = solid(art, mask, p["near_light"], p["near"], 0.1, 0.9, "stone", 0.12)
        art.put(layer, art.mask_of(chains), p["near"])
        art.light(layer, art.rim(mask, -0.003, 0.0, 0.5) * mask, p["fire"], 0.30)
        lamps(art, layer, lights, p["fire"], halo=7.0, strength=0.9)
        return layer
    layer = art.blank()
    art.put(layer, fog(art, "smoke", 0.20, 0.10), p["stone_dark"], 0.25)
    art.put(layer, fog(art, "floor smoke", 0.78, 0.10), p["red_dark"], 0.15)
    vignette(art, layer, p["deep"], 0.40)
    return layer
