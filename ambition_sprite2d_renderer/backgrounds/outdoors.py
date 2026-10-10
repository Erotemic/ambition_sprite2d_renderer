"""The scenes of the rooms that are under a sky: the cove."""

from __future__ import annotations

import math

import numpy as np

from .artkit import Art, Pen, mix, polar, scale, smoothstep
from .parts import HORIZON, cloud_mask, cumulus, fog, haze, lamps, moon, motes, palm, pine, shafts, solid, stars, vignette

# ---------------------------------------------------------------------------
# The cove: a coast at night under the moon
# ---------------------------------------------------------------------------

COVE = {
    "zenith": (8, 20, 48),
    "sky": (20, 58, 96),
    "horizon": (86, 150, 160),
    "sea": (10, 44, 66),
    "deep": (5, 20, 34),
    "moon": (236, 244, 232),
    "halo": (150, 214, 220),
    "rock": (9, 26, 40),
    "rock_light": (40, 84, 100),
    "lantern": (255, 196, 110),
}


def cove(layer_key: str, art: Art) -> np.ndarray:
    p = COVE
    moon_at = (0.30, 0.385)
    if layer_key == "sky":
        layer = art.opaque(
            art.ramp([(0.0, p["zenith"]), (0.30, p["sky"]), (HORIZON - 0.005, p["horizon"]), (HORIZON, p["sea"]), (0.80, p["deep"]), (1.0, p["deep"])])
        )
        stars(art, layer, 520, (220, 240, 255), HORIZON - 0.04)
        # Clouds with the moon behind them: the edge that faces it is light.
        clouds = cloud_mask(art, "clouds", 0.43, 0.16, cells=3.0, cover=0.47, soft=0.16) * (art.v < HORIZON - 0.01)
        art.tint(layer, clouds, mix(p["sky"], p["zenith"], 0.45), 0.86)
        lit = np.clip(clouds - art.shift(clouds, 0.004, 0.012), 0.0, 1.0)
        art.light(layer, art.blur(lit, 1.0) * art.spot(*moon_at, 0.6, 1.0), p["halo"], 0.75)
        moon(art, layer, *moon_at, 0.046, p["moon"], p["halo"])
        # The sea: the light of the moon in a path to the eye, in short lines.
        below = smoothstep(HORIZON, HORIZON + 0.004, art.v)
        ripples = art.noise("ripples", cells=70.0, octaves=2, stretch=7.0)
        depth = np.clip((art.v - HORIZON) / 0.3, 0.0, 1.0)
        path = np.clip(1.0 - np.abs(art.u - moon_at[0]) / (0.03 + depth * 0.20), 0.0, 1.0)
        art.light(layer, below * path * smoothstep(0.50, 0.72, ripples) * (1.0 - depth) ** 0.6, p["moon"], 0.72)
        art.light(layer, below * smoothstep(0.62, 0.8, ripples) * (1.0 - depth), p["halo"], 0.20)
        art.light(layer, art.band(HORIZON, 0.05, 2.0), p["horizon"], 0.36)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        # Headlands on the horizon, a lighthouse, and a ship far out.
        land, line = art.ridge("headland", HORIZON - 0.012, 0.05, cells=2.5, octaves=5, sharp=0.35)
        gap = smoothstep(0.24, 0.40, art.u) * smoothstep(0.66, 0.52, art.u)
        land = land * (1.0 - gap) * (art.v < HORIZON + 0.004)
        image, pen = art.drawing()
        lu = 0.80
        lv = float(line[int(lu * art.n)])
        pen.poly([(lu - 0.008, lv), (lu + 0.008, lv), (lu + 0.005, lv - 0.085), (lu - 0.005, lv - 0.085)])
        pen.rect(lu - 0.009, lv - 0.094, lu + 0.009, lv - 0.085)
        pen.poly([(lu - 0.007, lv - 0.094), (lu + 0.007, lv - 0.094), (lu, lv - 0.11)])
        # The ship: a hull, three masts, square sails.
        su, sv = 0.47, HORIZON
        pen.poly([(su - 0.05, sv - 0.014), (su + 0.055, sv - 0.014), (su + 0.045, sv + 0.002), (su - 0.04, sv + 0.002)])
        pen.line([(su + 0.05, sv - 0.014), (su + 0.08, sv - 0.03)], 0.002)
        for k, h in ((-0.028, 0.075), (0.004, 0.092), (0.034, 0.07)):
            pen.rect(su + k - 0.001, sv - 0.014 - h, su + k + 0.001, sv - 0.014)
            for j in range(3):
                top = sv - 0.02 - h + j * h * 0.31
                wide = 0.016 - (2 - j) * 0.003
                pen.poly([(su + k - wide, top + h * 0.26), (su + k + wide, top + h * 0.26), (su + k + wide * 0.8, top), (su + k - wide * 0.8, top)], 215)
        mask = np.maximum(land, art.mask_of(image))
        layer = solid(art, mask, mix(p["rock_light"], p["sky"], 0.5), mix(p["rock"], p["sea"], 0.5), HORIZON - 0.12, HORIZON, "headland rock", 0.08)
        art.light(layer, art.rim(mask, 0.004, 0.004, 0.6) * mask, p["halo"], 0.30)
        # The light of the lighthouse: a beam, and the lamp.
        beam, beam_pen = art.drawing()
        beam_pen.poly([(lu, lv - 0.09), (lu - 0.55, lv - 0.17), (lu - 0.55, lv - 0.06)], 200)
        art.put(layer, art.mask_of(beam, blur=5.0) * smoothstep(lu - 0.55, lu, art.u), p["lantern"], 0.30)
        lamps(art, layer, [(lu, lv - 0.09, 0.004)], p["lantern"], halo=6.0, strength=1.0)
        lamps(art, layer, [(su - 0.03, sv - 0.02, 0.0016), (su + 0.045, sv - 0.022, 0.0016)], p["lantern"], halo=4.0, strength=0.8)
        haze(art, layer, p["horizon"], 0.30, None)
        return layer
    if layer_key == "near_background":
        rng = art.rand("shore")
        # A cliff with an arch on the left, rocks on the right, a pier between.
        cliff, _ = art.ridge("cliff", 0.40, 0.07, cells=5.0, octaves=5, sharp=0.5)
        cliff = cliff * smoothstep(0.204, 0.20, art.u + (art.noise("cliff face", cells=6.0, octaves=4) - 0.5) * 0.10)
        rocks, _ = art.ridge("rocks", 0.615, 0.05, cells=8.0, octaves=5, sharp=0.6)
        rocks = rocks * smoothstep(0.776, 0.78, art.u + (art.noise("rock face", cells=6.0, octaves=3) - 0.5) * 0.08)
        shore, _ = art.ridge("shore", 0.70, 0.012, cells=5.0, octaves=3)
        image, pen = art.drawing()
        # The pier: a deck on posts, with lantern poles.
        deck_v = 0.645
        pen.rect(0.22, deck_v, 0.74, deck_v + 0.012)
        poles = []
        for k in range(11):
            u = 0.235 + k * 0.05
            pen.rect(u - 0.004, deck_v, u + 0.004, 1.0)
            pen.line([(u, deck_v + 0.012), (u + 0.05, deck_v + 0.06)], 0.002)
            if k % 3 == 1:
                pen.rect(u - 0.002, deck_v - 0.085, u + 0.002, deck_v)
                pen.line([(u, deck_v - 0.085), (u + 0.018, deck_v - 0.085)], 0.002)
                pen.rect(u + 0.013, deck_v - 0.083, u + 0.023, deck_v - 0.066)
                poles.append((u + 0.018, deck_v - 0.074, 0.0042))
        pen.curve((0.22, deck_v - 0.03), (0.74, deck_v - 0.03), 0.012, 0.0016)
        # Palms on the cliff and the rocks.
        for u, v, h, lean in ((0.07, 0.40, 0.13, 0.03), (0.15, 0.43, 0.10, -0.025), (0.86, 0.60, 0.16, -0.04), (0.94, 0.61, 0.11, 0.025)):
            palm(pen, rng, u, v, h, lean)
        # A wreck's ribs in the shallows.
        for k in range(6):
            u = 0.57 + k * 0.022
            pen.arc(u, 0.70, 0.06 - abs(k - 2.5) * 0.008, 200, 290, 0.004)
        mask = np.maximum.reduce([cliff, rocks, shore, art.mask_of(image)])
        layer = solid(art, mask, mix(p["rock"], p["rock_light"], 0.32), scale(p["rock"], 0.8), 0.34, 0.72, "shore rock", 0.10)
        art.light(layer, art.rim(mask, 0.003, 0.004, 0.5) * mask, p["halo"], 0.42)
        art.shade(layer, art.rim(mask, -0.004, -0.006, 1.2) * mask, 0.30)
        lamps(art, layer, poles, p["lantern"], halo=7.0, strength=1.0)
        haze(art, layer, p["sea"], 0.12, 0.73)
        return layer
    layer = art.blank()
    art.put(layer, fog(art, "sea mist", 0.66, 0.15), p["horizon"], 0.30)
    art.put(layer, motes(art, "spray", 60, 0.3, 0.8, 0.001, 0.0024), p["moon"], 0.45)
    vignette(art, layer, p["zenith"], 0.34)
    return layer




# ---------------------------------------------------------------------------
# The skybridge: a bridge between islands in the day sky
# ---------------------------------------------------------------------------

SKYBRIDGE = {
    "zenith": (54, 108, 190),
    "mid": (118, 174, 228),
    "horizon": (240, 226, 204),
    "sun": (255, 244, 214),
    "cloud": (252, 252, 255),
    "cloud_shade": (150, 178, 218),
    "stone": (66, 86, 134),
    "stone_light": (150, 170, 208),
    "grass": (96, 150, 124),
}


def _island(pen: Pen, grass: Pen, rng, u: float, v: float, w: float, h: float) -> None:
    """An island in the air: a flat top with grass, and rock that comes to a
    point below it."""
    left, right = [], []
    for k in range(9):
        t = k / 8.0
        half = w * (1.0 - t) ** 0.75 * rng.uniform(0.82, 1.0)
        left.append((u - half + w * 0.12 * t, v + h * t))
        right.append((u + half + w * 0.12 * t, v + h * t))
    pen.poly(left + right[::-1])
    pen.ellipse(u, v, w, w * 0.07)
    grass.ellipse(u, v - w * 0.02, w * 1.02, w * 0.075)


def skybridge(layer_key: str, art: Art) -> np.ndarray:
    p = SKYBRIDGE
    sun_at = (0.72, 0.40)
    if layer_key == "sky":
        layer = art.opaque(art.ramp([(0.0, p["zenith"]), (0.36, p["mid"]), (HORIZON, p["horizon"]), (0.74, (206, 222, 244)), (1.0, (150, 184, 228))]))
        art.light(layer, art.spot(*sun_at, 0.52, 2.0), p["sun"], 0.55)
        art.light(layer, art.spot(*sun_at, 0.10, 1.5), (255, 255, 244), 0.9)
        disc, pen = art.drawing()
        pen.ellipse(*sun_at, 0.03)
        art.put(layer, art.mask_of(disc, blur=0.8), (255, 254, 240))
        # High thin cloud, then a bank of heap cloud on the horizon, then the
        # top of the cloud that the islands stand in.
        art.tint(layer, cloud_mask(art, "cirrus", 0.34, 0.12, cells=4.0, cover=0.42, soft=0.3, stretch=6.0), p["cloud"], 0.5)
        layer = art.over(layer, cumulus(art, "bank", HORIZON + 0.01, 0.13, 6.0, 0.50, p["cloud"], p["cloud_shade"]))
        layer = art.over(layer, cumulus(art, "sea", 0.82, 0.24, 4.0, 0.62, (238, 244, 255), (158, 186, 226)))
        art.grain(layer, "grain", 1.0)
        return layer
    if layer_key == "far_backplate":
        rng = art.rand("islands")
        image, pen = art.drawing()
        grass, grass_pen = art.drawing()
        falls, fall_pen = art.drawing()
        places = [(0.16, 0.50, 0.085, 0.13), (0.44, 0.565, 0.06, 0.09), (0.69, 0.48, 0.07, 0.12), (0.93, 0.555, 0.075, 0.10)]
        for u, v, w, h in places:
            _island(pen, grass_pen, rng, u, v, w, h)
            # A tower or a few trees on each one.
            if rng.random() < 0.6:
                pen.rect(u - 0.008, v - 0.07, u + 0.008, v)
                pen.poly([(u - 0.012, v - 0.07), (u + 0.012, v - 0.07), (u, v - 0.098)])
            for _ in range(3):
                tu = u + rng.uniform(-0.7, 0.7) * w
                pen.rect(tu - 0.0015, v - 0.022, tu + 0.0015, v)
                grass_pen.ellipse(tu, v - 0.026, 0.011, 0.013)
            fall_pen.rect(u + w * 0.5, v, u + w * 0.5 + 0.006, v + h * 1.5, value=200)
        # A far viaduct between two of them.
        for k in range(7):
            cu = 0.225 + k * 0.026
            pen.arc(cu, 0.515, 0.013, 180, 360, 0.003)
        pen.rect(0.21, 0.497, 0.395, 0.503)
        mask = art.mask_of(image)
        layer = solid(art, mask, p["stone_light"], p["stone"], 0.40, 0.72, "island rock", 0.08)
        art.put(layer, art.mask_of(grass) , p["grass"])
        art.light(layer, art.rim(np.maximum(mask, art.mask_of(grass)), -0.004, 0.003, 0.6), p["sun"], 0.40)
        art.put(layer, art.mask_of(falls, blur=1.4) * smoothstep(0.72, 0.5, art.v), p["cloud"], 0.55)
        haze(art, layer, p["mid"], 0.46, None)
        return layer
    if layer_key == "near_background":
        image, pen = art.drawing()
        flags, flag_pen = art.drawing()
        deck_v = 0.66
        towers = (0.17, 0.80)
        for u in towers:
            pen.poly([(u - 0.030, 1.0), (u - 0.020, 0.32), (u + 0.020, 0.32), (u + 0.030, 1.0)])
            pen.rect(u - 0.030, 0.31, u + 0.030, 0.325)
            pen.poly([(u - 0.026, 0.31), (u + 0.026, 0.31), (u, 0.262)])
            pen.rect(u - 0.0015, 0.215, u + 0.0015, 0.27)
            flag_pen.poly([(u + 0.0015, 0.218), (u + 0.045, 0.228), (u + 0.0015, 0.243)])
            # An arch through each tower, for the deck.
            pen.rect(u - 0.011, deck_v - 0.075, u + 0.011, deck_v, value=0)
            pen.ellipse(u, deck_v - 0.075, 0.011, 0.016, value=0)
        # The main cables and the hangers down to the deck.
        spans = [(towers[0] - 0.4, towers[0]), (towers[0], towers[1]), (towers[1], towers[1] + 0.4)]
        for a, b in spans:
            sag = 0.24 if b - a > 0.5 else 0.17
            pen.curve((a, 0.325), (b, 0.325), sag, 0.0045)
            for k in range(1, 24):
                t = k / 24.0
                u = a + (b - a) * t
                pen.rect(u - 0.0009, 0.325 + sag * 4.0 * t * (1.0 - t), u + 0.0009, deck_v)
        pen.rect(0.0, deck_v, 1.0, deck_v + 0.016)
        pen.rect(0.0, deck_v - 0.014, 1.0, deck_v - 0.011)
        for k in range(80):
            pen.rect(k / 80.0, deck_v - 0.014, k / 80.0 + 0.0012, deck_v)
        mask = art.mask_of(image)
        layer = solid(art, mask, mix(p["stone"], p["stone_light"], 0.35), scale(p["stone"], 0.82), 0.26, 0.70, "bridge stone", 0.07)
        art.light(layer, art.rim(mask, -0.004, 0.002, 0.4) * mask, p["sun"], 0.55)
        art.shade(layer, art.rim(mask, 0.005, 0.0, 1.2) * mask, 0.22)
        art.put(layer, art.mask_of(flags), (226, 96, 88))
        haze(art, layer, p["mid"], 0.14, None)
        return layer
    layer = art.blank()
    art.put(layer, cloud_mask(art, "low wisps", 0.70, 0.12, cells=3.0, cover=0.5, soft=0.35, stretch=5.0), p["cloud"], 0.50)
    art.put(layer, cloud_mask(art, "high wisps", 0.26, 0.10, cells=3.0, cover=0.4, soft=0.35, stretch=6.0), p["cloud"], 0.30)
    birds, pen = art.drawing()
    rng = art.rand("birds")
    for _ in range(9):
        u, v, s = rng.uniform(0.1, 0.9), rng.uniform(0.34, 0.52), rng.uniform(0.006, 0.011)
        pen.line([(u - s, v - s * 0.35), (u, v), (u + s, v - s * 0.45)], 0.0016)
    art.put(layer, art.mask_of(birds), p["stone"], 0.7)
    return layer


# ---------------------------------------------------------------------------
# The forest: a dojo gate in bamboo, in the mist before dark
# ---------------------------------------------------------------------------

FOREST = {
    "top": (20, 44, 52),
    "mid": (62, 108, 98),
    "glow": (232, 222, 150),
    "mist": (150, 192, 164),
    "far": (38, 78, 76),
    "near": (9, 25, 24),
    "near_light": (36, 74, 58),
    "lantern": (255, 172, 92),
    "red": (128, 40, 34),
}


def _bamboo(pen: Pen, rng, u: float, v0: float, v1: float, width: float) -> None:
    lean = rng.uniform(-0.03, 0.03)
    node = v1
    while node > v0:
        t = (v1 - node) / (v1 - v0)
        seg = rng.uniform(0.035, 0.05)
        x0, x1 = u + lean * t**2, u + lean * ((v1 - node + seg) / (v1 - v0)) ** 2
        pen.line([(x0, node), (x1, node - seg + 0.003)], width)
        if t > 0.35 and rng.random() < 0.7:
            side = rng.choice([-1, 1])
            tip = (x1 + side * rng.uniform(0.03, 0.06), node - seg + rng.uniform(-0.01, 0.02))
            pen.line([(x1, node - seg), tip], 0.0014)
            for _ in range(3):
                d = rng.uniform(0.3, 1.0)
                leaf = (x1 + (tip[0] - x1) * d, node - seg + (tip[1] - node + seg) * d)
                pen.poly([leaf, (leaf[0] + side * 0.016, leaf[1] + 0.011), (leaf[0] + side * 0.006, leaf[1] + 0.015)])
        node -= seg


def forest(layer_key: str, art: Art) -> np.ndarray:
    p = FOREST
    sun_at = (0.62, 0.50)
    if layer_key == "sky":
        horizon = mix(p["mid"], p["glow"], 0.55)
        layer = art.opaque(art.ramp([(0.0, p["top"]), (0.36, p["mid"]), (HORIZON - 0.02, horizon), (0.72, p["far"]), (1.0, p["top"])]))
        art.light(layer, art.spot(*sun_at, 0.50, 2.0, squash=1.4), p["glow"], 0.50)
        # Two far ranges, each paler than the one in front of it, with mist between.
        for tag, base, amp, colour, amount in (("range a", 0.52, 0.10, mix(p["mid"], p["glow"], 0.30), 0.70), ("range b", 0.57, 0.07, mix(p["far"], p["mid"], 0.55), 0.85)):
            hills, _ = art.ridge(tag, base, amp, cells=3.0, octaves=5, sharp=0.45)
            art.tint(layer, hills, colour, amount)
            art.tint(layer, fog(art, (tag, "mist"), base + 0.06, 0.07), p["mist"], 0.50)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        rng = art.rand("pines")
        ground, line = art.ridge("pine ridge", HORIZON + 0.01, 0.04, cells=4.0, octaves=4)
        image, pen = art.drawing()
        for _ in range(60):
            u = rng.random()
            v = float(line[min(art.n - 1, int(u * art.n))])
            h = rng.uniform(0.07, 0.16)
            pine(pen, u, v + 0.01, h, h * 0.42, tiers=rng.randint(4, 6))
        # A pagoda over the trees.
        cu, base = 0.32, HORIZON - 0.05
        for k in range(4):
            w = 0.060 - k * 0.011
            v = base - k * 0.052
            pen.rect(cu - w * 0.62, v - 0.04, cu + w * 0.62, v)
            pen.poly([(cu - w * 1.25, v - 0.034), (cu - w * 0.9, v - 0.046), (cu, v - 0.058), (cu + w * 0.9, v - 0.046), (cu + w * 1.25, v - 0.034), (cu + w, v - 0.04), (cu - w, v - 0.04)])
        pen.rect(cu - 0.0015, base - 0.29, cu + 0.0015, base - 0.2)
        mask = np.maximum(ground, art.mask_of(image))
        layer = solid(art, mask, mix(p["far"], p["mid"], 0.4), p["far"], 0.36, 0.66, "pine", 0.08)
        art.light(layer, art.rim(mask, -0.003, 0.003, 0.6) * mask, p["glow"], 0.30)
        lamps(art, layer, [(cu, base - 0.02 - k * 0.052, 0.0022) for k in range(4)], p["lantern"], halo=4.0, strength=0.8)
        haze(art, layer, p["mist"], 0.34, HORIZON + 0.04)
        return layer
    if layer_key == "near_background":
        rng = art.rand("grove")
        image, pen = art.drawing()
        red, red_pen = art.drawing()
        ground, _ = art.ridge("ground", 0.69, 0.014, cells=5.0, octaves=3)
        # Bamboo at each side, and a few stalks across.
        for _ in range(26):
            side = rng.choice([rng.uniform(0.0, 0.26), rng.uniform(0.74, 1.0), rng.uniform(0.0, 1.0)])
            _bamboo(pen, rng, side, 0.0, 0.72, rng.uniform(0.0045, 0.008))
        # The gate: two posts and two beams, the top one with its curve.
        cu, foot, w, h = 0.52, 0.70, 0.11, 0.25
        for pen_ in (pen, red_pen):
            for side in (-1, 1):
                pen_.poly([(cu + side * w * 0.80, foot), (cu + side * w * 0.72, foot - h), (cu + side * w * 0.62, foot - h), (cu + side * w * 0.66, foot)])
            pen_.rect(cu - w * 0.92, foot - h * 0.80, cu + w * 0.92, foot - h * 0.74)
            pen_.poly([(cu - w * 1.22, foot - h - 0.022), (cu - w * 0.6, foot - h - 0.006), (cu + w * 0.6, foot - h - 0.006), (cu + w * 1.22, foot - h - 0.022), (cu + w * 1.16, foot - h + 0.012), (cu - w * 1.16, foot - h + 0.012)])
            pen_.rect(cu - 0.008, foot - h * 0.98, cu + 0.008, foot - h * 0.74)
        # Stone lanterns along the path.
        lights = []
        for u in (0.33, 0.71):
            pen.rect(u - 0.004, 0.655, u + 0.004, 0.70)
            pen.rect(u - 0.011, 0.63, u + 0.011, 0.655)
            pen.poly([(u - 0.017, 0.63), (u + 0.017, 0.63), (u, 0.612)])
            lights.append((u, 0.643, 0.0055))
        # Leaves that hang from the trees over the view.
        canopy = smoothstep(0.50, 0.56, art.noise("canopy", cells=9.0, octaves=5) * smoothstep(0.34, 0.14, art.v))
        mask = np.maximum.reduce([ground, art.mask_of(image), canopy])
        layer = solid(art, mask, mix(p["near"], p["near_light"], 0.5), p["near"], 0.26, 0.72, "leaves", 0.12)
        art.tint(layer, art.mask_of(red), p["red"], 0.55)
        art.light(layer, art.rim(mask, -0.003, 0.003, 0.4) * mask, p["glow"], 0.36)
        art.shade(layer, art.rim(mask, 0.005, -0.003, 1.2) * mask, 0.28)
        lamps(art, layer, lights, p["lantern"], halo=6.0, strength=1.0)
        haze(art, layer, p["far"], 0.12, 0.73)
        return layer
    layer = art.blank()
    art.put(layer, shafts(art, "sun shafts", 5, -0.12, 0.0, 0.80, 0.05), p["glow"], 0.15)
    art.put(layer, fog(art, "ground mist", 0.68, 0.16), p["mist"], 0.38)
    art.put(layer, motes(art, "fireflies", 46, 0.38, 0.74, 0.0014, 0.0028), (226, 255, 150), 0.8)
    vignette(art, layer, p["top"], 0.34)
    return layer


# ---------------------------------------------------------------------------
# The water: under the sea, by a drowned ruin
# ---------------------------------------------------------------------------

WATER = {
    "surface": (118, 212, 214),
    "top": (28, 118, 142),
    "mid": (12, 70, 106),
    "deep": (5, 26, 54),
    "ray": (190, 250, 240),
    "rock": (6, 30, 50),
    "rock_light": (26, 86, 108),
    "coral": (255, 130, 124),
    "kelp": (8, 54, 56),
}


def water(layer_key: str, art: Art) -> np.ndarray:
    p = WATER
    if layer_key == "sky":
        layer = art.opaque(art.ramp([(0.0, p["surface"]), (0.24, p["top"]), (0.52, p["mid"]), (0.80, p["deep"]), (1.0, p["deep"])]))
        art.light(layer, shafts(art, "sun rays", 8, 0.16, 0.0, 0.86, 0.04), p["ray"], 0.34)
        # The pattern the waves make on the light, near the surface.
        net = art.noise("caustics", cells=26.0, octaves=2)
        art.light(layer, smoothstep(0.08, 0.0, np.abs(net - 0.5)) * smoothstep(0.52, 0.22, art.v), p["ray"], 0.16)
        # A whale, a long way off.
        whale, pen = art.drawing()
        wu, wv = 0.30, 0.40
        pen.ellipse(wu, wv, 0.10, 0.028)
        pen.poly([(wu + 0.08, wv - 0.012), (wu + 0.16, wv - 0.004), (wu + 0.08, wv + 0.014)])
        pen.poly([(wu + 0.15, wv - 0.004), (wu + 0.19, wv - 0.03), (wu + 0.175, wv - 0.002), (wu + 0.19, wv + 0.022)])
        pen.poly([(wu - 0.02, wv + 0.02), (wu + 0.01, wv + 0.055), (wu + 0.025, wv + 0.02)])
        art.tint(layer, art.mask_of(whale, blur=1.6), mix(p["mid"], p["deep"], 0.5), 0.45)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        rng = art.rand("ruin")
        bed, line = art.ridge("far bed", HORIZON + 0.04, 0.035, cells=4.0, octaves=4)
        image, pen = art.drawing()
        # Columns of a temple, some of them broken, and an arch that still stands.
        for k in range(9):
            u = 0.08 + k * 0.105 + rng.uniform(-0.01, 0.01)
            top = HORIZON - rng.choice([0.22, 0.22, 0.12, 0.05, 0.22])
            pen.rect(u - 0.012, top, u + 0.012, 1.0)
            if top < HORIZON - 0.2:
                pen.rect(u - 0.019, top - 0.012, u + 0.019, top)
            else:
                pen.poly([(u - 0.012, top), (u + 0.012, top + 0.02), (u + 0.012, top + 0.03), (u - 0.012, top + 0.03)], value=0)
            for flute in (-0.005, 0.005):
                pen.rect(u + flute - 0.0008, top + 0.01, u + flute + 0.0008, HORIZON, value=190)
        pen.rect(0.06, HORIZON - 0.245, 0.31, HORIZON - 0.225)
        pen.poly([(0.06, HORIZON - 0.245), (0.31, HORIZON - 0.245), (0.185, HORIZON - 0.30)])
        mask = np.maximum(bed, art.mask_of(image))
        layer = solid(art, mask, p["rock_light"], p["rock"], 0.34, 0.70, "ruin stone", 0.10)
        art.light(layer, art.rim(mask, 0.0, 0.004, 0.6) * mask, p["ray"], 0.32)
        haze(art, layer, p["mid"], 0.50, HORIZON + 0.06)
        return layer
    if layer_key == "near_background":
        rng = art.rand("reef")
        bed, line = art.ridge("bed", 0.685, 0.035, cells=6.0, octaves=5, sharp=0.3)
        image, pen = art.drawing()
        coral, coral_pen = art.drawing()
        # Kelp: long ribbons that sway, with blades.
        for _ in range(22):
            u = rng.choice([rng.uniform(0.0, 0.3), rng.uniform(0.68, 1.0), rng.uniform(0.0, 1.0)])
            top = rng.uniform(0.26, 0.5)
            phase, sway = rng.uniform(0, 6.28), rng.uniform(0.008, 0.02)
            pts = []
            for k in range(25):
                v = 0.72 - (0.72 - top) * k / 24.0
                pts.append((u + math.sin(v * 26.0 + phase) * sway * (k / 24.0) ** 0.5, v))
            pen.line(pts, rng.uniform(0.003, 0.0055))
            for k in range(3, 25, 2):
                x, y = pts[k]
                side = 1 if k % 4 == 1 else -1
                pen.ellipse(x + side * 0.008, y - 0.008, 0.0085, 0.0038)
        # Coral: fans of branches.
        def branch(u: float, v: float, angle: float, length: float, depth: int) -> None:
            tip = polar(u, v, length, angle)
            coral_pen.line([(u, v), tip], 0.0022 + depth * 0.0012)
            if depth > 0:
                for turn in (-28.0, 24.0):
                    branch(tip[0], tip[1], angle + turn + rng.uniform(-8, 8), length * 0.72, depth - 1)

        for u in (0.36, 0.47, 0.60, 0.14, 0.86):
            v = float(line[int(u * art.n)]) + 0.005
            branch(u, v, -90.0 + rng.uniform(-10, 10), rng.uniform(0.024, 0.036), 3)
        # Rocks on the bed.
        for _ in range(8):
            u, r = rng.random(), rng.uniform(0.02, 0.05)
            pen.ellipse(u, 0.70, r, r * 0.6)
        mask = np.maximum(bed, art.mask_of(image))
        layer = solid(art, mask, mix(p["kelp"], p["rock_light"], 0.35), p["rock"], 0.26, 0.74, "reef", 0.10)
        art.put(layer, art.mask_of(coral), mix(p["coral"], p["mid"], 0.35))
        whole = np.maximum(mask, art.mask_of(coral))
        art.light(layer, art.rim(whole, 0.0, 0.004, 0.4) * whole, p["ray"], 0.38)
        haze(art, layer, p["deep"], 0.12, 0.74)
        return layer
    layer = art.blank()
    art.put(layer, shafts(art, "near rays", 4, 0.20, 0.0, 0.8, 0.06), p["ray"], 0.12)
    rng = art.rand("bubbles")
    bubbles, pen = art.drawing()
    for _ in range(7):
        u = rng.uniform(0.05, 0.95)
        v = rng.uniform(0.45, 0.75)
        for k in range(rng.randint(4, 9)):
            r = rng.uniform(0.002, 0.006)
            pen.ring(u + rng.uniform(-0.012, 0.012), v - k * rng.uniform(0.022, 0.04), r, 0.0012, value=rng.randint(140, 255))
    art.put(layer, art.mask_of(bubbles, blur=0.3), p["ray"], 0.75)
    art.put(layer, motes(art, "plankton", 120, 0.15, 0.9, 0.0008, 0.002), p["ray"], 0.45)
    vignette(art, layer, p["deep"], 0.36)
    return layer


# ---------------------------------------------------------------------------
# The open sky: cloud and nothing else
# ---------------------------------------------------------------------------


def open_sky(layer_key: str, art: Art) -> np.ndarray:
    """The Mockingbird's air chase. The game scrolls this scene and draws it
    again mirrored at each seam, so it has no sun and no land: a thing that
    is a place would come round twice."""
    light, shadow = (252, 252, 255), (156, 184, 222)
    if layer_key == "sky":
        layer = art.opaque(art.ramp([(0.0, (60, 118, 200)), (0.40, (124, 178, 230)), (0.70, (200, 224, 244)), (1.0, (226, 238, 250))]))
        art.tint(layer, cloud_mask(art, "cirrus", 0.36, 0.14, cells=4.0, cover=0.45, soft=0.3, stretch=7.0), light, 0.45)
        art.grain(layer, "grain", 1.0)
        return layer
    if layer_key == "far_backplate":
        layer = cumulus(art, "far bank", 0.62, 0.16, 9.0, 0.60, light, shadow)
        art.tint(layer, np.ones((art.n, art.n), dtype=np.float32), (170, 204, 238), 0.34)
        return layer
    if layer_key == "near_background":
        layer = cumulus(art, "near bank", 0.70, 0.18, 6.0, 0.60, light, shadow)
        return art.over(cumulus(art, "high heaps", 0.40, 0.12, 7.0, 0.44, light, mix(shadow, light, 0.3)), layer)
    layer = art.blank()
    art.put(layer, cloud_mask(art, "streaks", 0.55, 0.3, cells=3.0, cover=0.42, soft=0.4, stretch=9.0), light, 0.34)
    return layer
