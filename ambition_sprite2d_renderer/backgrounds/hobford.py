"""The scenes of Hobford, level 1: hill country joined to the gate network
last year (`docs/planning/game/level-1.md` in the game repository).

- `hobford`: the open country on a clear morning. Rolling hills in fields
  and hedgerows, a few dry-stone walls, the village down by the stream with
  its mill, and on the east hill the old stone ring with new steel on it: a
  scaffold, a crane arm, cable poles marching up to it. Near the play: a
  hedge bank, a fence of split rails, an oak.
- `hobford_woods`: the same morning under broadleaf trees: trunks in rows
  that go paler with distance, light coming through the canopy.
- `creator_workshop`: the inside of the Creator's barn: plank walls, the
  roof trusses, a window of morning light, a pegboard of tools, shelves of
  parts boxes.

Each is a working place, not a postcard: the steel on the ring is new and
does not match the stone.
"""

from __future__ import annotations

import numpy as np

from .artkit import Art, Pen, mix, scale, smoothstep
from .parts import HORIZON, cumulus, fog, haze, shafts, solid, vignette

HOBFORD = {
    "top": (104, 160, 214),
    "mid": (156, 196, 228),
    "low": (214, 230, 236),
    "sun": (255, 244, 214),
    "cloud": (250, 250, 246),
    "cloud_shadow": (176, 190, 206),
    "hill_far": (150, 182, 170),
    "hill_mid": (118, 160, 104),
    "hill_near": (92, 138, 74),
    "field_gold": (196, 180, 104),
    "field_pale": (168, 186, 110),
    "hedge": (60, 98, 56),
    "stone": (168, 160, 146),
    "steel": (120, 128, 138),
    "steel_light": (206, 214, 220),
    "roof": (122, 72, 54),
    "thatch": (184, 152, 96),
    "wall": (226, 214, 190),
    "timber": (84, 62, 44),
    "near": (40, 62, 40),
    "near_light": (118, 150, 88),
    "mist": (226, 236, 232),
}


def _cottage(walls: Pen, roofs: Pen, u: float, foot: float, w: float, h: float, gable: float = 0.55) -> None:
    """A cottage: a pale wall, a steep roof and a chimney."""
    top = foot - h
    walls.rect(u, top, u + w, foot + 0.01)
    roofs.poly([(u - w * 0.08, top + 0.002), (u + w * 1.08, top + 0.002), (u + w * 0.5, top - w * gable)])
    roofs.rect(u + w * 0.70, top - w * 0.45, u + w * 0.80, top - w * 0.20)


def _mill(walls: Pen, roofs: Pen, wheel: Pen, u: float, foot: float, w: float) -> None:
    """The mill: a tall stone house with its wheel on the stream side."""
    h = w * 0.95
    walls.rect(u, foot - h, u + w, foot + 0.01)
    roofs.poly([(u - w * 0.06, foot - h + 0.002), (u + w * 1.06, foot - h + 0.002), (u + w * 0.5, foot - h - w * 0.5)])
    cu, cv, r = u - w * 0.18, foot - w * 0.30, w * 0.34
    wheel.ring(cu, cv, r, w * 0.05)
    for k in range(8):
        a = np.radians(k * 22.5)
        wheel.line([(cu - np.cos(a) * r, cv - np.sin(a) * r), (cu + np.cos(a) * r, cv + np.sin(a) * r)], w * 0.02)


def _ring(stone: Pen, steel: Pen, cu: float, foot: float, r: float) -> None:
    """The old ring on its hill: a ring of stone on a stepped plinth, with new
    steel round it: two towers of scaffold, a crane arm, cable poles."""
    stone.rect(cu - r * 1.25, foot - r * 0.16, cu + r * 1.25, foot + 0.01)
    stone.rect(cu - r * 1.05, foot - r * 0.30, cu + r * 1.05, foot - r * 0.14)
    stone.ring(cu, foot - r * 1.22, r, r * 0.20)
    for side in (-1, 1):
        x = cu + side * r * 1.45
        steel.rect(x - r * 0.10, foot - r * 2.45, x - r * 0.07, foot)
        steel.rect(x + r * 0.07, foot - r * 2.45, x + r * 0.10, foot)
        for k in range(7):
            y = foot - r * 0.35 * (k + 1)
            steel.line([(x - r * 0.09, y), (x + r * 0.09, y - r * 0.32)], r * 0.025)
            steel.rect(x - r * 0.10, y - r * 0.02, x + r * 0.10, y + r * 0.01)
    # The crane: a mast on the right tower and its arm over the ring.
    x = cu + r * 1.45
    steel.rect(x - r * 0.04, foot - r * 3.1, x + r * 0.04, foot - r * 2.4)
    steel.line([(x + r * 0.5, foot - r * 3.0), (cu - r * 0.6, foot - r * 3.0)], r * 0.05)
    steel.line([(x, foot - r * 3.3), (cu - r * 0.6, foot - r * 3.0)], r * 0.015)
    steel.line([(cu - r * 0.2, foot - r * 3.0), (cu - r * 0.2, foot - r * 2.55)], r * 0.012)


def hobford(layer_key: str, art: Art) -> np.ndarray:
    p = HOBFORD
    sun_at = (0.30, 0.34)
    if layer_key == "sky":
        layer = art.opaque(art.ramp([(0.0, p["top"]), (0.35, p["mid"]), (HORIZON, p["low"]), (0.75, mix(p["low"], p["hill_far"], 0.6)), (1.0, p["hill_far"])]))
        art.light(layer, art.spot(*sun_at, 0.40, 2.2), p["sun"], 0.55)
        clouds = cumulus(art, "fair cumulus", 0.38, 0.09, 5.0, 0.40, p["cloud"], p["cloud_shadow"])
        art.tint(clouds, np.ones((art.n, art.n), dtype=np.float32), p["mid"], 0.12)
        layer = art.over(layer, clouds)
        # The far hills: blue with distance, folded in two ranges.
        for tag, base, amp, colour, amount in (
            ("downs far", HORIZON - 0.03, 0.05, mix(p["hill_far"], p["low"], 0.45), 0.85),
            ("downs near", HORIZON + 0.01, 0.04, mix(p["hill_far"], p["hill_mid"], 0.35), 0.95),
        ):
            hills, _ = art.ridge(tag, base, amp, cells=2.5, octaves=4, sharp=0.25)
            art.tint(layer, hills, colour, amount)
            art.tint(layer, fog(art, (tag, "haze"), base + 0.04, 0.04), p["mist"], 0.35)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        rng = art.rand("hobford country")
        ground, line = art.ridge("valley", HORIZON + 0.025, 0.035, cells=2.0, octaves=3, sharp=0.2)
        # The east hill, where the ring stands.
        hill, hill_line = art.ridge("ring hill", HORIZON - 0.02, 0.025, cells=1.2, octaves=3)
        hill = hill * smoothstep(0.55, 0.68, art.u)
        # Fields: bands of colour across the slopes, cut by hedges.
        fields = art.noise("fields", cells=6.0, octaves=2)
        stone, stone_pen = art.drawing()
        steel, steel_pen = art.drawing()
        walls, wall_pen = art.drawing()
        roofs, roof_pen = art.drawing()
        wheel, wheel_pen = art.drawing()
        hedges, hedge_pen = art.drawing()
        # Hedgerows along the field edges: dark lines that follow the slope.
        for k in range(9):
            v0 = HORIZON + 0.03 + k * 0.022
            pts = [(u / 40.0, v0 + 0.006 * np.sin(u * 0.7 + k)) for u in range(41)]
            hedge_pen.line(pts, 0.004)
        for _ in range(26):
            u = rng.uniform(0.0, 1.0)
            v = float(line[min(art.n - 1, int(u * art.n))])
            hedge_pen.ellipse(u, v - 0.006, rng.uniform(0.008, 0.016), rng.uniform(0.008, 0.014))
        # The village down the valley on the left, and the mill by it.
        u = 0.08
        while u < 0.40:
            w = rng.uniform(0.014, 0.022)
            foot = float(line[min(art.n - 1, int((u + w * 0.5) * art.n))]) + 0.006
            _cottage(wall_pen, roof_pen, u, foot, w, w * rng.uniform(0.50, 0.65))
            u += w * rng.uniform(1.5, 2.4)
        mill_u = 0.43
        _mill(wall_pen, roof_pen, wheel_pen, mill_u, float(line[int(mill_u * art.n)]) + 0.006, 0.04)
        # The ring on the east hill, and the cable poles up to it.
        cu = 0.78
        foot = float(hill_line[int(cu * art.n)]) + 0.004
        _ring(stone_pen, steel_pen, cu, foot, 0.035)
        for k in range(6):
            pu = 0.50 + k * 0.045
            pv = float(np.minimum(line, hill_line)[int(pu * art.n)]) if pu > 0.55 else float(line[int(pu * art.n)])
            steel_pen.rect(pu - 0.0012, pv - 0.05, pu + 0.0012, pv)
            steel_pen.rect(pu - 0.006, pv - 0.05, pu + 0.006, pv - 0.047)
        land = np.clip(np.maximum(ground, hill), 0, 1)
        air = p["low"]
        layer = solid(art, land, mix(p["hill_mid"], air, 0.30), mix(p["hill_mid"], air, 0.10), HORIZON - 0.05, HORIZON + 0.08, "turf", 0.05)
        art.tint(layer, land * smoothstep(0.55, 0.62, fields), mix(p["field_gold"], air, 0.25), 0.55)
        art.tint(layer, land * smoothstep(0.35, 0.28, fields), mix(p["field_pale"], air, 0.25), 0.45)
        art.put(layer, art.mask_of(hedges) * land, mix(p["hedge"], air, 0.25))
        art.put(layer, art.mask_of(walls), mix(p["wall"], air, 0.40))
        art.put(layer, art.mask_of(roofs), mix(p["roof"], air, 0.25))
        art.put(layer, art.mask_of(wheel), mix(p["timber"], air, 0.30))
        art.put(layer, art.mask_of(stone), mix(p["stone"], air, 0.25))
        art.put(layer, art.mask_of(steel), mix(p["steel"], air, 0.30))
        body = np.clip(np.maximum.reduce([land, art.mask_of(walls), art.mask_of(roofs), art.mask_of(stone), art.mask_of(steel)]), 0, 1)
        art.light(layer, art.rim(body, 0.003, 0.003, 0.5) * body, p["sun"], 0.30)
        art.light(layer, art.mask_of(steel) * art.rim(art.mask_of(steel), 0.002, 0.0, 0.0), p["steel_light"], 0.45)
        haze(art, layer, p["mist"], 0.16, HORIZON + 0.06)
        return layer
    if layer_key == "near_background":
        rng = art.rand("hobford near")
        image, pen = art.drawing()
        crown, crown_pen = art.drawing()
        ground, _ = art.ridge("bank", 0.70, 0.012, cells=4.0, octaves=3)
        # A fence of split rails along the bank.
        for k in range(14):
            u = 0.34 + k * 0.035
            pen.rect(u - 0.003, 0.645, u + 0.003, 0.705)
        pen.line([(0.33, 0.660), (0.83, 0.655)], 0.004)
        pen.line([(0.33, 0.682), (0.83, 0.679)], 0.004)
        # An oak on the left: a broad trunk, limbs, and a heavy crown.
        pen.poly([(0.10, 0.71), (0.19, 0.71), (0.17, 0.44), (0.16, 0.30), (0.13, 0.30), (0.12, 0.44)])
        pen.line([(0.15, 0.40), (0.06, 0.30)], 0.010)
        pen.line([(0.155, 0.36), (0.27, 0.28)], 0.010)
        pen.line([(0.16, 0.33), (0.20, 0.20)], 0.008)
        for _ in range(40):
            crown_pen.ellipse(0.15 + rng.gauss(0.0, 0.07), 0.22 + rng.gauss(0.0, 0.05), rng.uniform(0.03, 0.06), rng.uniform(0.025, 0.045))
        # A hedge bank on the right.
        for _ in range(30):
            crown_pen.ellipse(0.90 + rng.gauss(0.0, 0.05), 0.66 + rng.gauss(0.0, 0.02), rng.uniform(0.02, 0.04), rng.uniform(0.02, 0.035))
        crown_mask = art.mask_of(crown)
        mask = np.maximum(ground, art.mask_of(image))
        layer = solid(art, mask, mix(p["near"], p["near_light"], 0.35), scale(p["near"], 0.9), 0.30, 0.75, "turf near", 0.10)
        art.put(layer, crown_mask, mix(p["hedge"], p["near"], 0.40))
        art.light(layer, crown_mask * art.noise("leaf light", cells=12.0, octaves=2), p["near_light"], 0.40)
        body = np.maximum(mask, crown_mask)
        art.light(layer, art.rim(body, 0.003, 0.003, 0.4) * body, p["sun"], 0.35)
        haze(art, layer, p["low"], 0.08, 0.74)
        return layer
    layer = art.blank()
    art.put(layer, fog(art, "morning mist", 0.70, 0.07), p["mist"], 0.20)
    art.put(layer, art.spot(*sun_at, 0.45, 2.4), p["sun"], 0.06)
    return layer


def hobford_woods(layer_key: str, art: Art) -> np.ndarray:
    p = HOBFORD
    light = (240, 236, 200)
    leaf = (86, 120, 62)
    leaf_dark = (48, 74, 44)
    bark = (78, 66, 54)
    if layer_key == "sky":
        layer = art.opaque(art.ramp([(0.0, mix(leaf, p["mid"], 0.45)), (0.40, mix(p["mid"], light, 0.4)), (HORIZON, mix(p["low"], leaf, 0.35)), (1.0, mix(leaf, bark, 0.4))]))
        art.light(layer, art.spot(0.35, 0.30, 0.45, 2.0), light, 0.45)
        canopy = smoothstep(0.48, 0.58, art.noise("high canopy", cells=6.0, octaves=5)) * smoothstep(0.45, 0.20, art.v)
        art.tint(layer, canopy, mix(leaf, p["mid"], 0.35), 0.75)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        rng = art.rand("far trunks")
        image, pen = art.drawing()
        for _ in range(34):
            u = rng.random()
            w = rng.uniform(0.006, 0.014)
            pen.rect(u - w, 0.10, u + w, HORIZON + 0.08)
        ground, _ = art.ridge("woods floor far", HORIZON + 0.06, 0.012, cells=4.0, octaves=3)
        canopy = smoothstep(0.50, 0.58, art.noise("far canopy", cells=8.0, octaves=4)) * smoothstep(0.46, 0.30, art.v)
        mask = np.clip(np.maximum.reduce([art.mask_of(image), ground, canopy]), 0, 1)
        air = mix(p["low"], leaf, 0.35)
        layer = solid(art, mask, mix(bark, air, 0.55), mix(leaf_dark, air, 0.45), 0.10, 0.70, "far wood", 0.06)
        art.tint(layer, canopy, mix(leaf, air, 0.40), 0.7)
        art.put(layer, shafts(art, "far shafts", 4, -0.10, 0.10, 0.75, 0.04), light, 0.18)
        haze(art, layer, air, 0.14, HORIZON + 0.07)
        return layer
    if layer_key == "near_background":
        rng = art.rand("near trunks")
        image, pen = art.drawing()
        crown, crown_pen = art.drawing()
        for u in (0.07, 0.27, 0.62, 0.88):
            w = rng.uniform(0.022, 0.034)
            pen.poly([(u - w * 1.4, 0.72), (u + w * 1.4, 0.72), (u + w, 0.60), (u + w * 0.9, 0.0), (u - w * 0.9, 0.0), (u - w, 0.60)])
            pen.line([(u, 0.30), (u + rng.choice([-1, 1]) * 0.08, 0.20)], 0.007)
        ground, _ = art.ridge("woods floor near", 0.71, 0.010, cells=5.0, octaves=3)
        for _ in range(90):
            crown_pen.ellipse(rng.random(), rng.uniform(0.0, 0.34) ** 1.4 + 0.02, rng.uniform(0.03, 0.06), rng.uniform(0.02, 0.04))
        for _ in range(26):
            crown_pen.ellipse(rng.random(), 0.70 + rng.gauss(0.0, 0.008), rng.uniform(0.012, 0.025), rng.uniform(0.010, 0.018))
        mask = np.maximum(ground, art.mask_of(image))
        crown_mask = art.mask_of(crown)
        layer = solid(art, mask, mix(bark, leaf_dark, 0.35), scale(bark, 0.7), 0.20, 0.75, "bark", 0.12)
        art.put(layer, crown_mask, leaf_dark)
        art.light(layer, crown_mask * art.noise("near leaf light", cells=12.0, octaves=2), leaf, 0.40)
        body = np.maximum(mask, crown_mask)
        art.light(layer, art.rim(body, -0.003, 0.002, 0.4) * body, light, 0.30)
        return layer
    layer = art.blank()
    art.put(layer, shafts(art, "sun through leaves", 6, -0.14, 0.0, 0.85, 0.05), light, 0.20)
    art.put(layer, fog(art, "woods mist", 0.70, 0.06), p["mist"], 0.10)
    vignette(art, layer, leaf_dark, 0.25)
    return layer


def creator_workshop(layer_key: str, art: Art) -> np.ndarray:
    plank = (122, 92, 66)
    plank_dark = (70, 52, 40)
    beam = (58, 42, 32)
    window = (236, 230, 196)
    steel = (128, 132, 136)
    box = (168, 132, 88)
    if layer_key == "sky":
        # The back wall: vertical planks, darker at the top under the roof.
        layer = art.opaque(art.ramp([(0.0, scale(plank_dark, 0.8)), (0.35, plank_dark), (0.70, plank), (1.0, plank_dark)]))
        seams = np.zeros_like(art.v)
        for k in range(28):
            seams = np.maximum(seams, smoothstep(0.0025, 0.0, np.abs(art.u - k / 27.0)))
        art.shade(layer, seams, 0.35)
        art.tint(layer, art.noise("wood grain", cells=40.0, octaves=2) * 0.6, plank_dark, 0.25)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        image, pen = art.drawing()
        glass, glass_pen = art.drawing()
        # The roof trusses: rafters and a tie beam per bay.
        for cu in (0.18, 0.50, 0.82):
            pen.line([(cu - 0.16, 0.36), (cu, 0.24)], 0.010)
            pen.line([(cu + 0.16, 0.36), (cu, 0.24)], 0.010)
            pen.rect(cu - 0.17, 0.355, cu + 0.17, 0.368)
            pen.rect(cu - 0.004, 0.24, cu + 0.004, 0.36)
        # A window of morning light, in four panes.
        glass_pen.rect(0.56, 0.38, 0.70, 0.54)
        pen.rect(0.555, 0.375, 0.705, 0.385)
        pen.rect(0.555, 0.535, 0.705, 0.545)
        pen.rect(0.626, 0.38, 0.634, 0.54)
        pen.rect(0.56, 0.456, 0.70, 0.464)
        # Shelves of parts boxes on the left.
        for k in range(3):
            v = 0.44 + k * 0.07
            pen.rect(0.06, v, 0.30, v + 0.008)
            u = 0.07
            while u < 0.29:
                pen.rect(u, v - 0.035, u + 0.03, v)
                u += 0.04
        mask = art.mask_of(image)
        layer = art.blank()
        art.put(layer, art.mask_of(glass), window)
        art.glow(layer, art.blur(art.mask_of(glass), 0.02), window, 0.35)
        art.put(layer, mask, mix(beam, plank_dark, 0.3))
        return layer
    if layer_key == "near_background":
        image, pen = art.drawing()
        tools, tool_pen = art.drawing()
        # A pegboard of tools on the right, and the bench's back edge.
        pen.rect(0.74, 0.40, 0.96, 0.60)
        for k in range(7):
            u = 0.76 + k * 0.03
            tool_pen.rect(u, 0.43, u + 0.006, 0.52)
            tool_pen.ellipse(u + 0.003, 0.42, 0.008, 0.006)
        pen.rect(0.0, 0.70, 1.0, 1.0)
        mask = art.mask_of(image)
        layer = art.blank()
        art.put(layer, mask, mix(plank_dark, beam, 0.5))
        art.put(layer, art.mask_of(tools), steel)
        art.light(layer, art.rim(art.mask_of(tools), -0.002, 0.0, 0.0), window, 0.35)
        return layer
    layer = art.blank()
    art.put(layer, shafts(art, "window light", 2, 0.25, 0.30, 0.95, 0.06), window, 0.12)
    vignette(art, layer, beam, 0.40)
    return layer
