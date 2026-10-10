"""The scenes of the rooms that are inside: the lab, the lab with its alarm
on, the foundry and the cave."""

from __future__ import annotations

import math

import numpy as np

from .artkit import Art, Pen, mix, polar, scale, smoothstep
from .parts import HORIZON, cloud_mask, crystal_cluster, fog, haze, lamps, shafts, solid, vignette, window_grid

# ---------------------------------------------------------------------------
# The lab: the hall of a reactor
# ---------------------------------------------------------------------------

LAB = {
    "deep": (6, 22, 34),
    "wall": (12, 52, 66),
    "air": (24, 92, 104),
    "glow": (120, 236, 220),
    "steel": (9, 34, 46),
    "steel_light": (30, 84, 98),
    "amber": (255, 188, 96),
}


#: The lab with its power out and its alarm on: the raid. The air is dark and
#: cold, and the light is the red of the beacons.
ALARM = {
    "deep": (5, 6, 12),
    "wall": (15, 18, 30),
    "air": (36, 38, 58),
    "glow": (255, 78, 62),
    "steel": (7, 8, 15),
    "steel_light": (40, 44, 64),
    "amber": (255, 196, 104),
}


def lab(layer_key: str, art: Art) -> np.ndarray:
    return _lab(layer_key, art, LAB, False)


def alarm(layer_key: str, art: Art) -> np.ndarray:
    return _lab(layer_key, art, ALARM, True)


def _lab(layer_key: str, art: Art, p: dict, raided: bool) -> np.ndarray:
    core = (0.66, 0.47)
    if layer_key == "sky":
        layer = art.opaque(art.ramp([(0.0, p["deep"]), (0.38, p["wall"]), (0.60, p["air"]), (0.80, p["wall"]), (1.0, p["deep"])]))
        # The far wall: ribs, beams and panels, almost the colour of the air.
        ribs, pen = art.drawing()
        for i in range(17):
            u = i / 16.0
            pen.rect(u - 0.006, 0.0, u + 0.006, 1.0, value=150)
            pen.rect(u - 0.016, 0.0, u - 0.013, 1.0, value=70)
        for v in (0.22, 0.34, 0.74, 0.86):
            pen.rect(0.0, v - 0.005, 1.0, v + 0.005, value=130)
        rng = art.rand("panels")
        for _ in range(40):
            u, v = rng.randint(0, 15) / 16.0 + 0.012, rng.choice([0.24, 0.36, 0.64, 0.76])
            pen.rect(u, v, u + 0.04, v + 0.07, value=rng.randint(20, 60))
        art.shade(layer, art.mask_of(ribs, blur=0.6), 0.34)
        # The reactor: a ring window in the wall, and the light it gives.
        art.light(layer, art.spot(*core, 0.62, 1.8, squash=1.3), p["glow"], 0.34)
        ring, pen = art.drawing()
        for r, w, value in ((0.150, 0.014, 255), (0.118, 0.004, 150), (0.185, 0.003, 110)):
            pen.ring(*core, r, w, value)
        for k in range(12):
            a = k * 30.0
            pen.line([polar(*core, 0.152, a), polar(*core, 0.186, a)], 0.004, 150)
        art.shade(layer, art.mask_of(ring, blur=0.5), 0.45)
        eye, pen = art.drawing()
        pen.ellipse(*core, 0.112)
        swirl = art.noise("core swirl", cells=7.0, octaves=4)
        art.light(layer, art.mask_of(eye, blur=1.5) * (0.45 + 0.55 * swirl), p["glow"], 0.62)
        art.light(layer, art.spot(*core, 0.07, 1.4), (230, 255, 248), 0.55)
        art.shade(layer, art.noise("stain", cells=3.0, octaves=5) * art.band(0.5, 0.6, 0.6), 0.16)
        if raided:
            # A beacon on each third rib of the wall, and smoke under the roof.
            beacons = [(u, 0.275, 0.0035) for u in (0.0625, 0.25, 0.4375, 0.875)]
            for u, v, _ in beacons:
                art.light(layer, art.spot(u, v, 0.15, 1.7), p["glow"], 0.30)
            lamps(art, layer, beacons, p["glow"], halo=6.0, strength=1.0)
            art.shade(layer, fog(art, "smoke", 0.10, 0.22, cells=3.0), 0.55)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        # Rows of tanks and server towers with their small lights.
        rng = art.rand("tanks")
        image, pen = art.drawing()
        lights, light_pen = art.drawing()
        warm, warm_pen = art.drawing()
        u = -0.02
        while u < 1.02:
            w = rng.uniform(0.045, 0.085)
            top = HORIZON - rng.uniform(0.10, 0.27)
            kind = rng.choice(["tank", "tank", "tower", "stack"])
            if 0.50 < u + w * 0.5 < 0.82:
                # Low in front of the reactor, so the ring is seen.
                top, kind = HORIZON - rng.uniform(0.02, 0.05), "tower"
            if kind == "tank":
                pen.rect(u, top + w * 0.5, u + w, 1.0)
                pen.ellipse(u + w * 0.5, top + w * 0.5, w * 0.5, w * 0.5)
                for band in range(1, 5):
                    light_pen.rect(u + 0.004, top + w * 0.5 + band * 0.045, u + w - 0.004, top + w * 0.5 + band * 0.045 + 0.003, value=60)
                light_pen.rect(u + w * 0.42, top + w * 0.7, u + w * 0.58, HORIZON - 0.02, value=rng.randint(90, 170))
            elif kind == "tower":
                pen.rect(u, top, u + w, 1.0)
                pen.rect(u + w * 0.3, top - 0.03, u + w * 0.42, top)
                window_grid(light_pen, rng, u + 0.006, top + 0.012, u + w - 0.006, HORIZON - 0.01, 0.012, 0.016, 0.45)
                if rng.random() < 0.6:
                    warm_pen.rect(u + w * 0.2, top + 0.03, u + w * 0.8, top + 0.036)
            else:
                pen.rect(u + w * 0.3, top - 0.06, u + w * 0.7, 1.0)
                pen.rect(u, top + 0.12, u + w, 1.0)
                warm_pen.ellipse(u + w * 0.5, top - 0.065, 0.004)
            u += w + rng.uniform(0.004, 0.03)
        # A catwalk that joins them.
        for v in (HORIZON - 0.075,):
            pen.rect(0.0, v, 1.0, v + 0.006)
            for k in range(40):
                pen.rect(k / 40.0, v - 0.012, k / 40.0 + 0.0015, v)
            pen.rect(0.0, v - 0.013, 1.0, v - 0.011)
        mask = art.mask_of(image)
        layer = solid(art, mask, mix(p["steel_light"], p["air"], 0.35), p["steel"], HORIZON - 0.3, HORIZON + 0.1, "tank metal", 0.06)
        art.light(layer, art.rim(mask, 0.004, 0.0, 0.5) * mask, p["glow"], 0.20)
        art.light(layer, art.mask_of(lights, blur=0.4) * mask, p["glow"], 0.55)
        art.put(layer, art.mask_of(warm, blur=0.5), p["amber"], 0.9)
        art.put(layer, art.mask_of(warm, blur=5.0), p["amber"], 0.25)
        haze(art, layer, p["air"], 0.40, HORIZON + 0.02)
        return layer
    if layer_key == "near_background":
        # Pipes, a gantry and machines, close to the play and dark.
        rng = art.rand("gantry")
        image, pen = art.drawing()
        # Pipes that run the length of the hall, with flanges.
        for v, r in ((0.355, 0.016), (0.392, 0.008), (0.655, 0.02)):
            pen.rect(0.0, v - r, 1.0, v + r)
            for k in range(9):
                u = (k + rng.uniform(0.2, 0.8)) / 9.0
                pen.rect(u - 0.005, v - r - 0.006, u + 0.005, v + r + 0.006)
        # Drops from the pipes, with elbows.
        for _ in range(5):
            u = rng.choice([rng.uniform(0.03, 0.50), rng.uniform(0.84, 0.97)])
            v1 = rng.uniform(0.45, 0.62)
            pen.rect(u - 0.007, 0.37, u + 0.007, v1)
            pen.rect(u - 0.007, v1 - 0.007, u + rng.choice([-1, 1]) * 0.06, v1 + 0.007)
        # Gantry columns with braces.
        for u in (0.10, 0.44, 0.88):
            pen.rect(u - 0.012, 0.30, u + 0.012, 1.0)
            pen.rect(u - 0.03, 0.30, u + 0.03, 0.318)
            for k in range(6):
                v = 0.42 + k * 0.05
                pen.line([(u - 0.012, v), (u + 0.012, v + 0.05)], 0.003)
        # Machines on the floor: cabinets and a low tank.
        cabinets = []
        u = 0.02
        while u < 0.98:
            w = rng.uniform(0.04, 0.09)
            h = rng.uniform(0.05, 0.13)
            if rng.random() < 0.72:
                pen.rect(u, 0.69 - h, u + w, 1.0)
                pen.rect(u + w * 0.15, 0.69 - h - 0.008, u + w * 0.85, 0.69 - h)
                cabinets.append((u, 0.69 - h, w, h))
            u += w + rng.uniform(0.01, 0.07)
        pen.rect(0.0, 0.69, 1.0, 1.0)
        # Cables that hang from the roof.
        for _ in range(9):
            a, b = rng.uniform(-0.05, 1.0), rng.uniform(0.08, 0.3)
            pen.curve((a, 0.0), (a + b, 0.0), rng.uniform(0.07, 0.19), 0.0028)
        sparks = []
        if raided:
            # A beam of the gantry that came down, and cables that are cut:
            # each one hangs straight, with a spark at its end.
            pen.line([(0.20, 0.318), (0.335, 0.69)], 0.016)
            pen.line([(0.335, 0.69), (0.39, 0.66)], 0.010)
            for u in (0.27, 0.52, 0.61, 0.79):
                end = rng.uniform(0.40, 0.56)
                pen.line([(u, 0.0), (u + rng.uniform(-0.008, 0.008), end)], 0.0028)
                sparks.append((u, end, 0.0026))
        mask = art.mask_of(image)
        layer = solid(art, mask, mix(p["steel"], p["steel_light"], 0.42), scale(p["steel"], 0.8), 0.30, 0.72, "near metal", 0.07)
        art.light(layer, art.rim(mask, 0.0, 0.0035, 0.4) * mask, p["glow"], 0.34)
        art.light(layer, art.rim(mask, -0.003, 0.0, 0.4) * mask, p["glow"], 0.14)
        art.shade(layer, art.rim(mask, 0.0, -0.006, 1.2) * mask, 0.35)
        # Lights on the machines.
        points, warm_points = [], []
        for u, v, w, h in cabinets:
            for k in range(rng.randint(1, 3)):
                spot = (u + w * rng.uniform(0.2, 0.8), v + h * rng.uniform(0.15, 0.6), 0.0022)
                (warm_points if rng.random() < 0.3 else points).append(spot)
        lamps(art, layer, points, p["glow"], halo=4.0, strength=0.85)
        lamps(art, layer, warm_points, p["amber"], halo=4.0, strength=0.85)
        lamps(art, layer, sparks, (255, 240, 200), halo=7.0, strength=1.0)
        haze(art, layer, p["wall"], 0.16, 0.70)
        return layer
    # The air in front: beams of light from the roof, dust, mist on the floor.
    layer = art.blank()
    if raided:
        # The beams are the red of the beacons and there are fewer. Smoke
        # hangs under the roof.
        art.put(layer, shafts(art, "shafts", 3, 0.16, 0.0, 0.82, 0.06), p["glow"], 0.13)
        art.put(layer, fog(art, "roof smoke", 0.08, 0.20, cells=3.0), p["deep"], 0.55)
        art.put(layer, fog(art, "floor mist", 0.69, 0.16), mix(p["air"], p["glow"], 0.22), 0.30)
        vignette(art, layer, p["deep"], 0.42)
        return layer
    art.put(layer, shafts(art, "shafts", 5, 0.10, 0.0, 0.82, 0.045), p["glow"], 0.17)
    art.put(layer, fog(art, "floor mist", 0.69, 0.16), mix(p["air"], p["glow"], 0.35), 0.34)
    vignette(art, layer, p["deep"], 0.30)
    return layer


# ---------------------------------------------------------------------------
# The basement: a foundry under the hub
# ---------------------------------------------------------------------------

FOUNDRY = {
    "soot": (16, 9, 9),
    "brick": (58, 28, 22),
    "air": (112, 50, 26),
    "fire": (255, 150, 60),
    "hot": (255, 222, 150),
    "iron": (24, 13, 12),
    "iron_light": (74, 38, 28),
}


def _arcade(pen: Pen, u0: float, u1: float, count: int, spring_v: float, top_v: float, pier: float) -> list[tuple[float, float, float]]:
    """A row of round arches between `u0` and `u1`: the mask is the wall, and
    the answer is the `(centre u, spring v, radius)` of each opening."""
    span = (u1 - u0) / count
    openings = []
    pen.rect(u0, top_v, u1, 1.0)
    for k in range(count):
        cu = u0 + span * (k + 0.5)
        r = span * 0.5 - pier * 0.5
        pen.rect(cu - r, spring_v, cu + r, 1.0, value=0)
        pen.ellipse(cu, spring_v, r, r, value=0)
        openings.append((cu, spring_v, r))
    return openings


def foundry(layer_key: str, art: Art) -> np.ndarray:
    p = FOUNDRY
    if layer_key == "sky":
        layer = art.opaque(art.ramp([(0.0, p["soot"]), (0.34, p["brick"]), (0.62, p["air"]), (0.78, p["brick"]), (1.0, p["soot"])]))
        # A brick wall far back: courses, and large blind vaults in it.
        courses = (np.sin(art.v * math.pi * 2.0 * 46.0) > 0.86).astype(np.float32)
        joints = (np.sin((art.u + np.floor(art.v * 46.0) * 0.5 * 0.031) * math.pi * 2.0 * 32.0) > 0.93).astype(np.float32)
        art.shade(layer, art.blur(np.maximum(courses, joints), 0.4), 0.16)
        vaults, pen = art.drawing()
        for cu in (0.14, 0.5, 0.86):
            pen.rect(cu - 0.15, 0.50, cu + 0.15, 1.0)
            pen.ellipse(cu, 0.50, 0.15, 0.15)
        vault = art.mask_of(vaults, blur=1.0)
        art.shade(layer, vault, 0.30)
        art.light(layer, art.rim(vault, 0.0, 0.006, 1.5), p["fire"], 0.14)
        # Fire below: its light comes up the wall.
        art.light(layer, art.band(0.70, 0.36, 1.6) * (0.55 + 0.45 * art.noise("fire flicker", cells=5.0, octaves=3, stretch=2.0)), p["fire"], 0.50)
        art.light(layer, art.spot(0.5, 0.74, 0.30, 2.0, squash=2.4), p["hot"], 0.30)
        # Smoke under the roof.
        art.shade(layer, cloud_mask(art, "smoke", 0.30, 0.20, cells=3.0, cover=0.62, soft=0.3), 0.42)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        # An arcade of furnaces, and stacks that go up to the roof.
        image, pen = art.drawing()
        openings = _arcade(pen, -0.04, 1.04, 6, HORIZON - 0.04, HORIZON - 0.20, 0.05)
        rng = art.rand("stacks")
        for cu, _, r in openings:
            if rng.random() < 0.7:
                w = rng.uniform(0.018, 0.03)
                u = cu + r + 0.025 - w * 0.5
                pen.poly([(u, HORIZON - 0.2), (u + w, HORIZON - 0.2), (u + w * 0.8, 0.12), (u + w * 0.2, 0.12)])
                pen.rect(u - 0.004, 0.115, u + w + 0.004, 0.128)
        pen.rect(-0.04, HORIZON - 0.215, 1.04, HORIZON - 0.2)
        mask = art.mask_of(image)
        layer = solid(art, mask, p["iron_light"], p["iron"], HORIZON - 0.22, HORIZON + 0.1, "arcade brick", 0.10)
        # The fire in each furnace mouth, behind the wall.
        fire = art.blank()
        mouths, mouth_pen = art.drawing()
        for cu, v, r in openings:
            mouth_pen.rect(cu - r, v, cu + r, 1.0)
            mouth_pen.ellipse(cu, v, r, r)
        glow = art.mask_of(mouths, blur=1.0)
        flames = art.noise("flames", cells=10.0, octaves=4, stretch=0.6)
        heat = smoothstep(HORIZON - 0.10, HORIZON + 0.08, art.v)
        art.put(fire, glow, art.ramp([(0.0, p["air"]), (HORIZON - 0.14, p["air"]), (HORIZON + 0.04, p["fire"]), (1.0, p["hot"])]), 0.95)
        art.light(fire, glow * heat * flames, p["hot"], 0.8)
        layer = art.over(fire, layer)
        art.light(layer, art.rim(mask, 0.0, -0.005, 0.8) * mask, p["fire"], 0.5)
        art.put(layer, art.mask_of(mouths, blur=14.0) * heat, p["fire"], 0.22)
        haze(art, layer, p["air"], 0.30, HORIZON + 0.06)
        return layer
    if layer_key == "near_background":
        rng = art.rand("ironwork")
        image, pen = art.drawing()
        # Brick piers at the sides and a beam across the roof.
        for u0, u1 in ((-0.02, 0.07), (0.93, 1.02)):
            pen.rect(u0, 0.0, u1, 1.0)
            pen.rect(u0 - 0.012, 0.30, u1 + 0.012, 0.318)
            pen.rect(u0 - 0.012, 0.655, u1 + 0.012, 0.675)
        pen.rect(0.0, 0.262, 1.0, 0.292)
        for k in range(26):
            pen.rect(k / 25.0 - 0.003, 0.292, k / 25.0 + 0.003, 0.302)
        # Chains from the beam, with a hook or a ladle at the end.
        ladles = []
        for u in (0.19, 0.31, 0.58, 0.72, 0.86):
            end = rng.uniform(0.40, 0.56)
            v = 0.30
            while v < end:
                pen.ellipse(u, v, 0.0036, 0.0062)
                v += 0.0105
            if rng.random() < 0.5:
                ladles.append((u, end + 0.03))
                pen.poly([(u - 0.036, end + 0.012), (u + 0.036, end + 0.012), (u + 0.027, end + 0.07), (u - 0.027, end + 0.07)])
                pen.arc(u, end + 0.016, 0.036, 180, 360, 0.004)
            else:
                pen.arc(u, end + 0.012, 0.012, 20, 270, 0.004)
        # Gears on the back wall.
        for cu, cv, r, teeth in ((0.42, 0.60, 0.085, 14), (0.515, 0.535, 0.045, 9), (0.80, 0.62, 0.06, 11)):
            pen.ellipse(cu, cv, r)
            for k in range(teeth):
                a = k * 360.0 / teeth + cu * 100.0
                pen.poly([polar(cu, cv, r * 0.9, a - 7), polar(cu, cv, r * 1.14, a - 4), polar(cu, cv, r * 1.14, a + 4), polar(cu, cv, r * 0.9, a + 7)])
            pen.ellipse(cu, cv, r * 0.62, value=0)
            pen.ellipse(cu, cv, r * 0.2)
            for k in range(5):
                pen.line([polar(cu, cv, r * 0.15, k * 72 + 10), polar(cu, cv, r * 0.66, k * 72 + 10)], r * 0.13)
        # Anvil blocks and slag heaps on the floor.
        floor, _ = art.ridge("slag", 0.69, 0.018, cells=7.0, octaves=4)
        mask = np.maximum(art.mask_of(image), floor)
        layer = solid(art, mask, mix(p["iron"], p["iron_light"], 0.45), scale(p["iron"], 0.75), 0.26, 0.74, "iron", 0.10)
        # The fire is below: light on the edges that face down.
        art.light(layer, art.rim(mask, 0.0, -0.004, 0.5) * mask, p["fire"], 0.55)
        art.light(layer, art.rim(mask, 0.0, -0.014, 2.0) * mask, p["fire"], 0.16)
        art.shade(layer, art.rim(mask, 0.0, 0.006, 1.2) * mask, 0.30)
        # Molten metal in the ladles.
        melt, melt_pen = art.drawing()
        for u, v in ladles:
            melt_pen.ellipse(u, v - 0.016, 0.031, 0.006)
        art.put(layer, art.mask_of(melt, blur=0.5), p["hot"], 0.95)
        art.put(layer, art.mask_of(melt, blur=9.0), p["fire"], 0.5)
        haze(art, layer, p["brick"], 0.14, 0.72)
        return layer
    layer = art.blank()
    art.put(layer, fog(art, "heat", 0.70, 0.20), p["fire"], 0.24)
    art.put(layer, cloud_mask(art, "roof smoke", 0.22, 0.2, cells=2.5, cover=0.6, soft=0.3), p["soot"], 0.42)
    vignette(art, layer, p["soot"], 0.36)
    return layer




# ---------------------------------------------------------------------------
# The cave: wet rock, and crystals that give the light
# ---------------------------------------------------------------------------

CAVE = {
    "black": (9, 8, 20),
    "wall": (28, 27, 58),
    "air": (56, 64, 118),
    "glow": (124, 222, 255),
    "pink": (236, 130, 232),
    "rock": (13, 12, 28),
    "rock_light": (50, 50, 96),
}


def _crystals(art: Art, layer: np.ndarray, places, colour, halo: float = 1.0) -> None:
    """Paint crystal clusters at `(u, v, size, up)` on `layer`, with their light."""
    rng = art.rand(("crystals", tuple(places)))
    body, body_pen = art.drawing()
    facet, facet_pen = art.drawing()
    wide, wide_pen = art.drawing()
    for u, v, size, up in places:
        crystal_cluster(body_pen, facet_pen, rng, u, v, size, count=rng.randint(5, 8), up=up, spread=30.0)
        wide_pen.ellipse(u, v + (size * 0.4 if up > 0 else -size * 0.4), size * 0.9)
    art.put(layer, art.mask_of(wide, blur=22.0 * halo), colour, 0.34)
    art.put(layer, art.mask_of(body), scale(colour, 0.55))
    art.put(layer, art.mask_of(facet), mix(colour, (255, 255, 255), 0.35), 0.9)
    art.put(layer, art.mask_of(body, blur=2.0), colour, 0.25)


def cave(layer_key: str, art: Art) -> np.ndarray:
    p = CAVE
    opening = (0.33, 0.43)
    if layer_key == "sky":
        layer = art.opaque(art.ramp([(0.0, p["black"]), (0.34, p["wall"]), (0.58, p["air"]), (0.80, p["wall"]), (1.0, p["black"])]))
        # The beds of the rock, and the dark between them.
        strata = art.noise("strata", cells=5.0, octaves=5, stretch=5.0)
        art.shade(layer, smoothstep(0.42, 0.74, strata), 0.30)
        art.light(layer, smoothstep(0.62, 0.9, art.noise("wet", cells=22.0, octaves=3, stretch=3.0)) * art.band(0.5, 0.3), p["glow"], 0.10)
        # A way out, far back: daylight comes down a shaft.
        art.light(layer, art.spot(*opening, 0.36, 1.7, squash=0.8), p["glow"], 0.40)
        beam, pen = art.drawing()
        pen.poly([(opening[0] - 0.03, 0.0), (opening[0] + 0.05, 0.0), (opening[0] + 0.16, 0.9), (opening[0] - 0.10, 0.9)], 190)
        art.light(layer, art.mask_of(beam, blur=14.0) * smoothstep(0.9, 0.2, art.v), (214, 240, 255), 0.30)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        floor, _ = art.ridge("far floor", HORIZON + 0.03, 0.10, cells=11.0, octaves=4, sharp=0.9)
        roof, _ = art.ridge("far roof", 0.33, -0.12, cells=12.0, octaves=4, sharp=0.9)
        mask = np.maximum(floor, 1.0 - roof)
        layer = solid(art, mask, mix(p["rock_light"], p["wall"], 0.55), p["rock"], 0.30, 0.70, "far rock", 0.10)
        art.light(layer, art.rim(mask, 0.004, 0.0, 0.6) * mask, p["glow"], 0.30)
        _crystals(art, layer, [(0.12, 0.60, 0.06, -90.0), (0.58, 0.63, 0.07, -90.0), (0.86, 0.59, 0.05, -90.0), (0.70, 0.30, 0.05, 90.0)], p["glow"])
        haze(art, layer, p["air"], 0.24, HORIZON + 0.05)
        return layer
    if layer_key == "near_background":
        rng = art.rand("near cave")
        floor, _ = art.ridge("floor", 0.69, 0.05, cells=9.0, octaves=5, sharp=0.75)
        roof, _ = art.ridge("roof", 0.27, -0.13, cells=8.0, octaves=5, sharp=0.9)
        # Columns where a stalactite has met its stalagmite.
        image, pen = art.drawing()
        for u, w in ((0.05, 0.05), (0.60, 0.028), (0.955, 0.045)):
            pts_left, pts_right = [], []
            for k in range(13):
                v = k / 12.0
                waist = 0.55 + 0.45 * abs(v * 2.0 - 1.25) ** 1.5
                pts_left.append((u - w * waist + rng.uniform(-0.004, 0.004), v))
                pts_right.append((u + w * waist + rng.uniform(-0.004, 0.004), v))
            pen.poly(pts_left + pts_right[::-1])
        # Mushrooms on the floor.
        caps = []
        for _ in range(9):
            u, h = rng.uniform(0.1, 0.92), rng.uniform(0.012, 0.03)
            v = 0.69
            pen.rect(u - 0.002, v - h, u + 0.002, v + 0.03)
            pen.draw.pieslice([(u - h * 0.8) * art.n, (v - h * 1.5) * art.n, (u + h * 0.8) * art.n, (v - h * 0.5) * art.n], 180, 360, fill=255)
            caps.append((u, v - h * 0.96, h * 0.75))
        mask = np.maximum.reduce([floor, 1.0 - roof, art.mask_of(image)])
        layer = solid(art, mask, mix(p["rock"], p["rock_light"], 0.4), scale(p["rock"], 0.8), 0.24, 0.74, "near rock", 0.12)
        art.light(layer, art.rim(mask, 0.004, 0.002, 0.5) * mask, p["glow"], 0.36)
        art.shade(layer, art.rim(mask, -0.005, 0.0, 1.4) * mask, 0.30)
        _crystals(art, layer, [(0.20, 0.685, 0.085, -90.0), (0.78, 0.67, 0.07, -90.0), (0.43, 0.30, 0.06, 90.0)], p["pink"], halo=1.2)
        _crystals(art, layer, [(0.33, 0.70, 0.045, -90.0), (0.90, 0.33, 0.05, 90.0)], p["glow"])
        # The under side of each mushroom gives light.
        gills, gill_pen = art.drawing()
        for u, v, r in caps:
            gill_pen.rect(u - r, v, u + r, v + 0.004)
        art.put(layer, art.mask_of(gills, blur=0.6), p["glow"], 0.9)
        art.put(layer, art.mask_of(gills, blur=7.0), p["glow"], 0.45)
        haze(art, layer, p["wall"], 0.10, 0.73)
        return layer
    layer = art.blank()
    art.put(layer, fog(art, "cave mist", 0.70, 0.17), p["air"], 0.36)
    vignette(art, layer, p["black"], 0.40)
    return layer
