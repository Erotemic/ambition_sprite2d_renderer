"""The scene of the Noodly Temple: the house of the Flying Spaghetti Monster.

All of it is pasta. The roof of the world is a colander, and the light of
the scene is what comes through its holes. Far off are hills of meatballs
under steam, with columns of rigatoni and arches of macaroni on them, and
noodles that hang between. Near are great columns of rigatoni and curtains
of noodles that hang from above.

The colours are those of a kitchen: wheat, butter, tomato, and a little
basil. The air is warm and it is full of steam.
"""

from __future__ import annotations

import math

import numpy as np

from .artkit import Art, Pen, mix, scale, smoothstep
from .parts import HORIZON, cloud_mask, fog, haze, shafts, solid, vignette

NOODLY = {
    "top": (64, 24, 20),
    "mid": (176, 84, 44),
    "low": (232, 150, 76),
    "glow": (255, 226, 150),
    "steam": (250, 234, 210),
    "steel": (112, 104, 110),
    "far": (150, 82, 52),
    "sauce": (164, 44, 32),
    "near": (44, 20, 14),
    "near_light": (124, 66, 36),
    "noodle": (236, 202, 128),
    "noodle_dark": (166, 122, 62),
    "basil": (70, 132, 66),
}


def _strand(pen: Pen, rng, u: float, v0: float, length: float, width: float, wave: float, curl: bool = True) -> None:
    """One noodle that hangs from `(u, v0)`: it goes down `length` with a
    slow wave, and its end turns up in a curl."""
    phase = rng.uniform(0.0, math.tau)
    period = rng.uniform(0.06, 0.11)
    pts = []
    steps = max(8, int(length / 0.008))
    for i in range(steps + 1):
        t = i / steps
        pts.append((u + math.sin(phase + t * length / period * math.tau) * wave * (0.25 + 0.75 * t), v0 + length * t))
    if curl:
        cu, cv = pts[-1]
        side = rng.choice([-1.0, 1.0])
        r = rng.uniform(0.006, 0.012)
        for k in range(1, 9):
            a = k / 8.0 * math.pi * 1.4
            pts.append((cu + side * (r - r * math.cos(a)), cv + r * math.sin(a) * 0.9 - r * 0.2 * (a / math.pi)))
    pen.line(pts, width)


def _rigatoni(pen: Pen, ribs: Pen, u: float, v_top: float, v_foot: float, w: float) -> None:
    """A column of rigatoni: a tube that stands, with the ridges of the pasta
    down it and an open mouth at its head. `ribs` takes the ridges."""
    pen.rect(u - w, v_top, u + w, v_foot)
    pen.ellipse(u, v_top, w, w * 0.34)
    for k in range(-2, 3):
        x = u + k * w * 0.4
        ribs.rect(x - w * 0.045, v_top + w * 0.2, x + w * 0.045, v_foot)


def _macaroni(pen: Pen, u0: float, u1: float, v_foot: float, rise: float, width: float) -> None:
    """An arch of macaroni from `u0` to `u1`: an elbow of pasta."""
    pts = []
    for i in range(25):
        t = i / 24.0
        pts.append((u0 + (u1 - u0) * t, v_foot - rise * math.sin(math.pi * t) ** 0.8))
    pen.line(pts, width)


def _fork(pen: Pen, u: float, v_foot: float, h: float, w: float, lean: float) -> None:
    """A fork that stands with its tines up, a long way off: a spire."""
    top = v_foot - h
    pen.poly([(u - w * 0.16, v_foot), (u + w * 0.16, v_foot), (u + lean + w * 0.12, top + h * 0.38), (u + lean - w * 0.12, top + h * 0.38)])
    pen.poly([(u + lean - w * 0.5, top + h * 0.40), (u + lean + w * 0.5, top + h * 0.40), (u + lean + w * 0.5, top + h * 0.26), (u + lean - w * 0.5, top + h * 0.26)])
    for k in range(4):
        x = u + lean + (k - 1.5) * w * 0.3
        pen.poly([(x - w * 0.085, top + h * 0.28), (x + w * 0.085, top + h * 0.28), (x + lean * 0.4, top)])


def noodly(layer_key: str, art: Art) -> np.ndarray:
    p = NOODLY
    #: The colander: the middle of its rim, half its width, and how deep it is.
    bowl_u, bowl_v, bowl_w, bowl_h = 0.50, 0.185, 0.46, 0.30
    if layer_key == "sky":
        layer = art.opaque(art.ramp([(0.0, p["top"]), (0.30, mix(p["top"], p["mid"], 0.7)), (HORIZON - 0.03, p["low"]), (HORIZON + 0.06, mix(p["low"], p["glow"], 0.4)), (0.80, p["mid"]), (1.0, p["top"])]))
        # The colander over the world, seen from under it: a bowl of steel.
        bowl, pen = art.drawing()
        pen.ellipse(bowl_u, bowl_v, bowl_w, bowl_h)
        pen.rect(0.0, 0.0, 1.0, bowl_v)
        steel = art.mask_of(bowl, blur=0.8)
        art.tint(layer, steel, mix(p["steel"], p["top"], 0.45), 0.86)
        # It is lit from under, by the kitchen: light on its low side.
        depth = np.clip((art.v - bowl_v) / bowl_h, 0.0, 1.0)
        art.light(layer, steel * depth**2, p["low"], 0.34)
        # The holes: rings of them round the bowl, each a point of the light
        # that is over it. A ring is an ellipse, as the bowl is seen.
        holes, hole_pen = art.drawing()
        rays, ray_pen = art.drawing()
        rng = art.rand("holes")
        for ring in range(1, 8):
            t = ring / 8.0
            ru, rv = bowl_w * t, bowl_h * t
            count = 6 + ring * 5
            for k in range(count):
                a = math.pi * (k + 0.5 * (ring % 2)) / count
                u, v = bowl_u + math.cos(a) * ru, bowl_v + math.sin(a) * rv
                if v < bowl_v + 0.012:
                    continue
                r = 0.0052 * (1.0 - 0.45 * t)
                hole_pen.ellipse(u, v, r, r * (0.55 + 0.45 * (1.0 - t)))
                if rng.random() < 0.26:
                    # A beam through a hole, down into the steam.
                    reach = rng.uniform(0.16, 0.34)
                    lean = (u - bowl_u) * 0.5
                    ray_pen.poly([(u - r, v), (u + r, v), (u + lean + r * 7.0, v + reach), (u + lean - r * 7.0, v + reach)], rng.randint(70, 170))
        art.light(layer, art.mask_of(holes, blur=1.4), p["glow"], 0.75)
        art.put(layer, art.mask_of(holes), mix(p["glow"], (255, 255, 255), 0.4))
        art.light(layer, art.mask_of(rays, blur=5.0) * smoothstep(0.86, 0.3, art.v), p["glow"], 0.36)
        # The rim of the bowl is out of the view at each side: its two
        # handles are what a view shows of it.
        art.light(layer, art.band(HORIZON + 0.02, 0.13, 2.0), p["glow"], 0.42)
        # Steam that goes up from the land.
        art.tint(layer, cloud_mask(art, "steam high", 0.40, 0.12, cells=3.0, cover=0.46, soft=0.3, stretch=3.4), p["steam"], 0.30)
        art.tint(layer, cloud_mask(art, "steam low", 0.55, 0.09, cells=4.0, cover=0.62, soft=0.3, stretch=4.6), p["steam"], 0.46)
        # Hills of meatballs a long way off: two ranges of round heads.
        for tag, base, r0, r1, colour, amount in (("far balls", 0.585, 0.030, 0.060, mix(p["far"], p["low"], 0.55), 0.78), ("near balls", 0.625, 0.036, 0.074, mix(p["far"], p["low"], 0.26), 0.90)):
            balls, ball_pen = art.drawing()
            rng = art.rand(tag)
            u = -0.04
            while u < 1.04:
                r = rng.uniform(r0, r1)
                ball_pen.ellipse(u, base + rng.uniform(0.0, 0.02), r, r * 0.86)
                u += r * rng.uniform(0.9, 1.5)
            ball_pen.rect(0.0, base + 0.01, 1.0, 1.0)
            mask = art.mask_of(balls, blur=0.5)
            art.tint(layer, mask, colour, amount)
            art.light(layer, art.rim(mask, 0.0, 0.004, 0.8) * mask, p["glow"], 0.26)
            art.tint(layer, fog(art, (tag, "steam"), base + 0.035, 0.05), p["steam"], 0.5)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        rng = art.rand("far pasta")
        ground, line = art.ridge("pasta ridge", HORIZON + 0.035, 0.022, cells=4.0, octaves=3)
        image, pen = art.drawing()
        ribs, rib_pen = art.drawing()
        strands, strand_pen = art.drawing()

        def foot(u: float) -> float:
            return float(line[min(art.n - 1, max(0, int(u * art.n)))]) + 0.012

        # Columns of rigatoni in two groups, with arches of macaroni between
        # the columns of a group. The middle of the scene is open.
        heads = []
        for group in ((0.05, 0.13, 0.20, 0.29), (0.71, 0.79, 0.88, 0.96)):
            tops = []
            for u in group:
                u += rng.uniform(-0.01, 0.01)
                h, w = rng.uniform(0.17, 0.30), rng.uniform(0.012, 0.018)
                _rigatoni(pen, rib_pen, u, HORIZON - h, foot(u), w)
                tops.append((u, HORIZON - h))
            heads.extend(tops)
            for (u0, v0), (u1, v1) in zip(tops, tops[1:]):
                _macaroni(pen, u0, u1, min(v0, v1) + 0.05, rng.uniform(0.04, 0.07), 0.012)
        # Forks that stand in the land with their tines up.
        for u in (0.385, 0.455, 0.56, 0.635):
            _fork(pen, u, foot(u), rng.uniform(0.11, 0.19), rng.uniform(0.022, 0.030), rng.uniform(-0.008, 0.008))
        # Noodles that hang between the heads of the columns, and from them.
        heads.sort()
        for (u0, v0), (u1, v1) in zip(heads, heads[1:]):
            for _ in range(2 if u1 - u0 < 0.2 else 3):
                strand_pen.curve((u0, v0 + rng.uniform(0.0, 0.03)), (u1, v1 + rng.uniform(0.0, 0.03)), rng.uniform(0.03, 0.12), 0.0032)
        for u, v in heads:
            for _ in range(3):
                _strand(strand_pen, rng, u + rng.uniform(-0.012, 0.012), v, rng.uniform(0.04, 0.10), 0.0028, 0.004)
        # Meatballs on the land, at the feet of the columns.
        for _ in range(12):
            u = rng.random()
            r = rng.uniform(0.012, 0.026)
            pen.ellipse(u, foot(u) - r * 0.5, r, r * 0.9)
        body = np.maximum(ground, art.mask_of(image))
        layer = solid(art, body, mix(p["far"], p["low"], 0.34), scale(p["far"], 0.72), HORIZON - 0.3, HORIZON + 0.10, "pasta", 0.08)
        art.shade(layer, art.mask_of(ribs) * body, 0.26)
        art.light(layer, art.rim(body, -0.003, 0.003, 0.6) * body, p["glow"], 0.38)
        noodles = art.mask_of(strands)
        art.put(layer, noodles, mix(p["noodle"], p["far"], 0.35))
        art.light(layer, art.rim(noodles, -0.0015, 0.0, 0.3) * noodles, p["glow"], 0.30)
        haze(art, layer, p["steam"], 0.16, HORIZON + 0.06)
        return layer
    if layer_key == "near_background":
        rng = art.rand("near pasta")
        image, pen = art.drawing()
        ribs, rib_pen = art.drawing()
        strands, strand_pen = art.drawing()
        back, back_pen = art.drawing()
        # A land of noodles in heaps: the lower edge of the view.
        ground, _ = art.ridge("heaps", 0.705, 0.018, cells=5.0, octaves=3)
        # Great columns of rigatoni at each side, from above the view to the land.
        for u, w in ((0.05, 0.034), (0.19, 0.020), (0.83, 0.024), (0.955, 0.038)):
            _rigatoni(pen, rib_pen, u, -0.05, 0.74, w)
            # A band of pasta round the column at two heights.
            for v in (0.30, 0.56):
                pen.rect(u - w * 1.16, v, u + w * 1.16, v + 0.012)
        # A sheet of lasagne that hangs from side to side over the view: its
        # lower edge is a row of waves.
        sheet = []
        for i in range(61):
            t = i / 60.0
            sheet.append((t, 0.085 + 0.045 * 4.0 * t * (1.0 - t) + 0.008 * math.sin(t * math.tau * 14.0)))
        pen.poly([(0.0, 0.0)] + sheet + [(1.0, 0.0)])
        # Curtains of noodles from the sheet: those behind are short and
        # many, those in front are long and few.
        for _ in range(70):
            u = rng.random()
            v0 = 0.08 + 0.045 * 4.0 * u * (1.0 - u)
            _strand(back_pen, rng, u, v0, rng.uniform(0.05, 0.16), 0.0030, 0.004)
        for _ in range(26):
            u = rng.choice([rng.uniform(0.0, 0.30), rng.uniform(0.70, 1.0), rng.uniform(0.0, 1.0)])
            v0 = 0.08 + 0.045 * 4.0 * u * (1.0 - u)
            _strand(strand_pen, rng, u, v0, rng.uniform(0.14, 0.34), rng.choice([0.0042, 0.0052]), 0.007)
        # Meatballs in the heaps, and one that hangs in a net of noodles.
        for _ in range(9):
            u = rng.random()
            r = rng.uniform(0.016, 0.030)
            pen.ellipse(u, 0.705 - r * 0.2, r, r * 0.92)
        mask = np.maximum.reduce([ground, art.mask_of(image)])
        layer = solid(art, mask, mix(p["near"], p["near_light"], 0.62), p["near"], 0.16, 0.74, "pasta", 0.10)
        art.shade(layer, art.mask_of(ribs) * mask, 0.30)
        art.light(layer, art.rim(mask, -0.003, 0.003, 0.4) * mask, p["glow"], 0.30)
        art.shade(layer, art.rim(mask, 0.005, -0.003, 1.2) * mask, 0.26)
        behind = art.mask_of(back)
        art.put(layer, behind, mix(p["noodle_dark"], p["near"], 0.30))
        front = art.mask_of(strands)
        art.put(layer, front, mix(p["noodle"], p["near_light"], 0.30))
        art.light(layer, art.rim(front, -0.0018, 0.0, 0.3) * front, p["glow"], 0.42)
        art.shade(layer, art.rim(front, 0.0018, 0.0, 0.3) * front, 0.30)
        haze(art, layer, p["mid"], 0.10, 0.73)
        return layer
    layer = art.blank()
    art.put(layer, shafts(art, "hole shafts", 7, 0.05, 0.0, 0.84, 0.035), p["glow"], 0.17)
    art.put(layer, fog(art, "steam", 0.68, 0.17), p["steam"], 0.30)
    art.put(layer, cloud_mask(art, "steam drift", 0.44, 0.16, cells=2.4, cover=0.36, soft=0.4, stretch=3.0), p["steam"], 0.12)
    vignette(art, layer, p["near"], 0.36)
    return layer


def foreground(art: Art, pen: Pen, layer_lights: list) -> None:
    """Noodles that hang from above, apart. Nothing stands from below."""
    del layer_lights
    rng = art.rand("noodly foreground")
    for k in range(7):
        u = (k + rng.uniform(0.2, 0.8)) / 7.0
        for _ in range(rng.choice([1, 2, 2, 3])):
            end = rng.uniform(0.375, 0.415)
            _strand(pen, rng, u + rng.uniform(-0.014, 0.014), 0.0, end, rng.choice([0.0050, 0.0062]), 0.006)
