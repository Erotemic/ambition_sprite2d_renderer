"""The scene of the History dimension at Budj Bim, in Gunditjmara country.

The History dimension is a grid. East is later, and each floor is a region
of the world. This room is on the floor of Oceania, beside the rooms of
`history_oceania.py`, and uses the same sepia of an old textbook and the
same rules as `history_eras.py`.

- ``history_budj_bim`` (Budj Bim, south-west Victoria, from about 4600 BCE
  to the 1840s). A soft grey day of the south coast, with low clouds. At
  the left the low wooded cone of Budj Bim, a volcano, with the notch of
  its crater on its top. Its lava flow runs out to the right as the stony
  rises: low lumps of dark basalt with moss and lichen, and manna gums and
  blackwoods on them. On the flow the Gunditjmara cut channels and built
  weirs of stacked basalt to trap, hold and grow kooyang (short-finned
  eels); a channel runs through the rises, with a weir across it and an
  eel trap in the gap of the weir. A few houses with low round walls of
  stacked basalt and domed roofs stand on the rises, and thin smoke goes
  up from a hollow manna gum where eels are smoked. At the right the wide
  wetland of Tae Rak (Lake Condah), with reeds and sedges at its edges and
  black swans far off on the water.

The people of this place show the skill of a system of farms of eels that
is one of the oldest in the world. No picture here shows a sacred thing,
rock art, a grave or a weapon. The bright detail is far off or at the
edges, and the middle of the near layer is calm, so the play in front of it
reads. The things that drift in the air are the room's motes
(`terrain/motes.py`), not part of these pictures.
"""

from __future__ import annotations

import math

import numpy as np

from .artkit import Art, Pen, mix, scale, smoothstep
from .history_east_asia_coast import _bank, _grass_blades, _reflected
from .history_eras import REST_BOTTOM, _air, _plume, _reeds, _sun, _textbook
from .history_origins import _arch, _gum, _land, _leaf
from .parts import HORIZON, cloud_mask, fog, haze, solid

BUDJ_BIM = {
    "top": (104, 122, 142),
    "mid": (166, 176, 182),
    "low": (224, 220, 204),
    "glow": (244, 226, 186),
    "sun": (250, 242, 218),
    "cloud": (236, 234, 226),
    "cloud_shadow": (150, 154, 160),
    "water": (100, 118, 120),
    "water_light": (186, 194, 186),
    "water_deep": (66, 82, 84),
    "plain": (138, 146, 122),
    "cone": (82, 98, 74),
    "cone_light": (128, 140, 104),
    "crater": (60, 72, 58),
    "basalt": (72, 70, 70),
    "basalt_light": (132, 130, 124),
    "moss": (104, 124, 70),
    "lichen": (196, 194, 168),
    "grass": (156, 150, 98),
    "sedge": (122, 134, 76),
    "reed_head": (132, 100, 70),
    "gum": (216, 208, 190),
    "leaf": (104, 120, 94),
    "blackwood": (60, 76, 56),
    "wall": (96, 94, 92),
    "roof": (118, 98, 72),
    "turf": (108, 122, 74),
    "trap": (196, 172, 116),
    "smoke": (200, 198, 192),
    "swan": (30, 28, 32),
    "bill": (196, 56, 50),
    "far": (198, 200, 192),
    "near": (30, 32, 30),
    "near_light": (112, 114, 96),
}

#: The level of the stony rises and the water at the foot of the cone.
BUDJ_FOOT = 0.612


def _cone_top(u: float) -> float:
    """The skyline of Budj Bim: a low broad cone with soft sides, and on its
    top the shallow notch of its crater. It stands at the left."""
    x = (u - 0.29) / 0.24
    if abs(x) >= 1.0:
        return 1.0
    rise = (1.0 - abs(x) ** 1.6) ** 0.9
    notch = 0.008 * max(0.0, 1.0 - (x / 0.16) ** 2)
    return HORIZON + 0.004 - 0.090 * rise + notch


def _swan(pen: Pen, bill: Pen, u: float, v: float, s: float, facing: float = 1.0) -> None:
    """A black swan far off on the water: a low boat of a body with its tail
    up, a long neck in an S, and a small red bill."""
    f = facing
    pen.ellipse(u, v - s * 0.18, s * 0.50, s * 0.20)
    pen.poly([(u - f * s * 0.46, v - s * 0.22), (u - f * s * 0.66, v - s * 0.42), (u - f * s * 0.30, v - s * 0.32)])
    pen.line([(u + f * s * 0.32, v - s * 0.26), (u + f * s * 0.46, v - s * 0.60), (u + f * s * 0.36, v - s * 0.92), (u + f * s * 0.44, v - s * 1.06)], s * 0.10)
    pen.ellipse(u + f * s * 0.46, v - s * 1.06, s * 0.08, s * 0.06)
    bill.line([(u + f * s * 0.50, v - s * 1.05), (u + f * s * 0.66, v - s * 1.00)], s * 0.07)


def _stone_house(wall: Pen, roof: Pen, door: Pen, u: float, v: float, w: float, h: float) -> None:
    """A Gunditjmara house far off: a low round wall of stacked basalt, and
    on it a dome of branches covered with turf and bark, with a low dark
    doorway in its wall."""
    wall.rect(u - w, v - h * 0.38, u + w, v + 0.001)
    roof.ellipse(u, v - h * 0.38, w * 1.04, h * 0.62)
    door.rect(u - w * 0.18, v - h * 0.34, u + w * 0.18, v + 0.001)


def _blackwood(trunk: Pen, crown: Pen, rng, u: float, v: float, h: float) -> None:
    """A blackwood: a straight dark trunk and a dense, dark crown, rounder
    and fuller than a gum's."""
    trunk.line([(u, v + 0.004), (u + rng.uniform(-0.004, 0.004), v - h * 0.55)], h * 0.05)
    for _ in range(9):
        crown.ellipse(u + rng.uniform(-0.22, 0.22) * h, v - h * rng.uniform(0.55, 0.92), h * rng.uniform(0.16, 0.24), h * rng.uniform(0.12, 0.18))


def _boulder(pen: Pen, rng, u: float, v: float, w: float, h: float) -> None:
    """A rough block of basalt: a lumpy shape with flat faces, wider than it
    is high, its middle at `(u, v)`."""
    pts = []
    for k in range(9):
        ang = 2.0 * math.pi * (k + rng.uniform(-0.25, 0.25)) / 9.0
        r = rng.uniform(0.80, 1.05)
        y = math.sin(ang) * h * r
        pts.append((u + math.cos(ang) * w * r, v + (min(y, h * 0.7) if y > 0 else y)))
    pen.poly(pts)


def _stones(pens, rng, u0: float, u1: float, v: float, size: float, rows: int) -> None:
    """Basalt stones stacked dry in a low wall from `u0` to `u1`, its foot at
    `v`: rows of rough blocks, each row set over the joints of the row
    under it. The stones go by turns into the pens of `pens`, so the joints
    between them show."""
    for r in range(rows):
        y = v - size * (0.6 + r * 1.05)
        x = u0 + (size * 0.9 if r % 2 else 0.0) + rng.uniform(0.0, size * 0.4)
        k = r
        while x < u1 - size * 0.5:
            w = size * rng.uniform(0.9, 1.5)
            _boulder(pens[k % len(pens)], rng, x + w * 0.5, y + rng.uniform(-0.1, 0.1) * size, w * 0.58, size * rng.uniform(0.58, 0.70))
            x += w * 1.04
            k += 1


def history_budj_bim(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = BUDJ_BIM
    sun_at = (0.70, 0.30)
    foot = BUDJ_FOOT
    if layer_key == "sky":
        # A soft grey day of the south-west: low banks of cloud, a pale sun
        # through them, and under the horizon the still grey water of the
        # wetland.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.90)), (0.26, p["top"]), (0.48, p["mid"]), (HORIZON - 0.004, p["low"]),
                                 (HORIZON + 0.002, mix(p["water_light"], p["low"], 0.40)), (0.68, mix(p["water"], p["water_light"], 0.40)), (1.0, p["water"])]))
        for k, (centre, half, cover, alpha) in enumerate(((0.14, 0.10, 0.58, 0.60), (0.32, 0.08, 0.52, 0.50), (0.48, 0.05, 0.46, 0.40))):
            clouds = cloud_mask(a, ("budj bim cloud", k), centre, half, cells=3.0 + k, cover=cover, soft=0.30, stretch=4.5)
            a.put(layer, clouds, mix(p["cloud"], p["low"], k * 0.2), alpha)
            a.put(layer, clouds * a.band(centre + half * 0.5, half * 0.6), p["cloud_shadow"], 0.22)
        a.light(layer, a.spot(*sun_at, 0.30, 2.0, squash=1.4), p["glow"], 0.35)
        _sun(a, layer, *sun_at, 0.014, p["sun"], p["glow"], 0.30)
        plain, _ = a.ridge("budj bim far plain", HORIZON - 0.006, 0.004, cells=4.0, octaves=3)
        a.put(layer, plain * (a.v < HORIZON + 0.002), mix(p["plain"], p["low"], 0.55))
        lines = smoothstep(0.64, 0.84, a.noise("budj bim far water", cells=60.0, octaves=2, stretch=16.0))
        a.light(layer, (a.v > HORIZON + 0.004) * lines, p["water_light"], 0.18)
        a.tint(layer, fog(a, "budj bim horizon haze", HORIZON, 0.016, 3.0), p["low"], 0.50)
        _textbook(a, layer, 0.08)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far budj bim")
        cols = a.u[0]
        # Budj Bim: a low cone at the left, wooded to its top, with the
        # notch of its crater. Its lava flow runs out to the right as the
        # stony rises: low lumps of dark basalt that fall to the wetland.
        cone_line = np.array([_cone_top(float(u)) for u in cols], dtype=np.float32)
        cone_line = cone_line + (a.line_noise("budj bim cone trees", cells=90.0, octaves=2) - 0.5) * 0.004 * (cone_line < 0.99)
        cone = _land(a, cone_line) * (a.v < foot + 0.004)
        # The stony rises: rows of low hummocks of basalt, the far row
        # first, each hummock grassy on its top with dark rock in its face.
        rows = []
        tops = []
        for r, (v0, u0, u1, n) in enumerate(((foot - 0.004, 0.20, 0.86, 30), (foot + 0.004, 0.06, 0.80, 30), (foot + 0.013, -0.02, 0.66, 28))):
            img, pen = a.drawing()
            u = u0
            while u < u1:
                w = rng.uniform(0.010, 0.026) * (1.0 + 0.3 * r)
                h = rng.uniform(0.004, 0.009) * (1.0 + 0.3 * r)
                pen.ellipse(u + w, v0, w, h)
                pen.rect(u + w * 0.2, v0, u + w * 1.8, v0 + 0.004 + 0.003 * r)
                tops.append((u + w, v0 - h, r))
                u += w * rng.uniform(1.3, 1.8)
            rows.append(a.mask_of(img))
        rises = np.maximum.reduce(rows)

        def top_at(u: float, row: int) -> float:
            near = [t for t in tops if t[2] == row]
            return min(near, key=lambda t: abs(t[0] - u))[1]

        # The wetland of Tae Rak at the right: its shore runs from the foot
        # of the rises at the right down to the left, so the water widens to
        # the eye. A channel runs from it back through the rises, with a
        # weir of stones across it and an eel trap in its gap.
        shore = 0.74 - (a.v - foot) * 3.2 + (a.noise("budj bim shore", cells=10.0, octaves=3) - 0.5) * 0.04
        lake = smoothstep(-0.004, 0.004, a.u - shore) * smoothstep(foot + 0.004, foot + 0.010, a.v) * (a.v < 0.72)
        channel_img, channel_pen = a.drawing()
        path = [(0.16, 0.640), (0.26, 0.634), (0.36, 0.638), (0.44, 0.633), (0.52, 0.637), (0.60, 0.634)]
        channel_pen.line(path, 0.0056)
        channel = a.mask_of(channel_img) * (1.0 - lake)
        weir_a, weir_pa = a.drawing()
        weir_b, weir_pb = a.drawing()
        trap_img, trap_pen = a.drawing()
        wu, wv = 0.360, 0.6380
        for k in range(-3, 4):
            if k == 0:
                continue
            for j in range(2):
                (weir_pa if (k + j) % 2 else weir_pb).ellipse(wu + k * 0.0056 + j * 0.0028, wv - j * 0.0040 + 0.0008 * (k % 2), 0.0034, 0.0026)
        trap_pen.poly([(wu - 0.0024, wv - 0.0050), (wu + 0.0150, wv - 0.0010), (wu - 0.0024, wv + 0.0016)])
        weir_mask = np.maximum(a.mask_of(weir_a), a.mask_of(weir_b))
        trap_mask = a.mask_of(trap_img)
        # Trees: manna gums and blackwoods on the rises.
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        blacks, black_pen = a.drawing()
        for u, row, h in ((0.09, 1, 0.06), (0.17, 2, 0.07), (0.30, 0, 0.05), (0.47, 1, 0.065), (0.56, 0, 0.055), (0.72, 0, 0.06), (0.62, 2, 0.07)):
            _gum(trunk_pen, crown_pen, rng, u, top_at(u, row) + 0.004, h)
        for u, row, h in ((0.13, 1, 0.030), (0.36, 0, 0.028), (0.52, 2, 0.034), (0.79, 0, 0.026), (0.25, 2, 0.032)):
            _blackwood(trunk_pen, black_pen, rng, u, top_at(u, row) + 0.003, h)
        # The houses: low round walls of stacked stone with domed roofs.
        walls, wall_pen = a.drawing()
        roofs, roof_pen = a.drawing()
        doors, door_pen = a.drawing()
        for u, v, s in ((0.43, foot + 0.024, 0.0120), (0.462, foot + 0.022, 0.0100), (0.55, foot + 0.021, 0.0110), (0.24, foot + 0.025, 0.0110)):
            _stone_house(wall_pen, roof_pen, door_pen, u, v, s, s * 1.3)
        # The smoking tree: a hollow manna gum with thin smoke from it.
        su = 0.665
        sv = top_at(su, 1) + 0.004
        _gum(trunk_pen, crown_pen, rng, su, sv, 0.06)
        smoke = np.clip(_plume(a, "budj bim smoking tree", su, sv - 0.004, 0.12, -0.05, 0.016) * 1.4, 0.0, 1.0)
        # Black swans on the wetland, and reeds and sedge along its shore.
        swans, swan_pen = a.drawing()
        bills, bill_pen = a.drawing()
        for u, v, s, f in ((0.78, 0.628, 0.008, 1.0), (0.80, 0.630, 0.007, -1.0), (0.88, 0.650, 0.012, 1.0), (0.905, 0.654, 0.011, 1.0), (0.72, 0.672, 0.014, -1.0), (0.97, 0.640, 0.009, -1.0)):
            _swan(swan_pen, bill_pen, u, v, s, f)
        reeds, reed_pen = a.drawing()
        heads, head_pen = a.drawing()
        rng_r = a.rand("far budj bim reeds")
        for _ in range(900):
            v = rng_r.uniform(foot + 0.008, 0.715)
            u = 0.74 - (v - foot) * 3.2 + rng_r.uniform(-0.035, 0.012)
            h = 0.006 + (v - foot) * 0.22 * rng_r.uniform(0.5, 1.0)
            lean = rng_r.uniform(-0.003, 0.003)
            reed_pen.line([(u, v), (u + lean * 0.4, v - h * 0.6), (u + lean, v - h)], 0.0008 + (v - foot) * 0.006)
            if rng_r.random() < 0.08:
                head_pen.ellipse(u + lean, v - h, 0.0006 + (v - foot) * 0.005, 0.0016 + (v - foot) * 0.014)
        cone_mask = cone * (1.0 - rises)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        black_mask = a.mask_of(blacks)
        wall_mask = a.mask_of(walls)
        roof_mask = a.mask_of(roofs)
        door_mask = a.mask_of(doors) * wall_mask
        swan_mask = a.mask_of(swans)
        bill_mask = a.mask_of(bills)
        reed_mask = a.mask_of(reeds)
        head_mask = a.mask_of(heads)
        flat = smoothstep(foot - 0.002, foot + 0.004, a.v) * (a.v < 0.72)
        land = np.maximum.reduce([cone, rises, flat, trunk_mask, crown_mask, black_mask, roof_mask, wall_mask, reed_mask, head_mask])
        mask = np.maximum.reduce([land, swan_mask, bill_mask])
        layer = solid(a, mask, mix(p["cone"], p["far"], 0.35), mix(p["basalt"], p["far"], 0.25), 0.52, 0.66, "budj bim far", 0.05)
        # The cone: wooded, dark green with lumps of crowns, lit on its left
        # side; a pale band of grass low on its slope.
        a.put(layer, cone_mask, mix(p["cone"], p["far"], 0.38))
        lumps = a.noise("budj bim cone crowns", cells=140.0, octaves=2)
        a.light(layer, cone_mask * smoothstep(0.55, 0.75, lumps), p["cone_light"], 0.30)
        a.shade(layer, cone_mask * smoothstep(0.45, 0.25, lumps), 0.12)
        a.light(layer, cone_mask * smoothstep(0.32, 0.12, a.u) * 0.6, p["glow"], 0.12)
        a.shade(layer, cone_mask * smoothstep(0.30, 0.46, a.u), 0.12)
        a.light(layer, a.rim(cone_mask, 0.002, 0.002, 0.3) * cone_mask, p["glow"], 0.30)
        # The low flat in front of the rises: grass and sedge in long soft
        # bands, a little darker to the eye.
        meadow = flat * (1.0 - rises)
        a.put(layer, meadow, a.ramp([(0.0, mix(p["grass"], p["far"], 0.35)), (0.63, mix(p["grass"], p["far"], 0.35)), (0.72, mix(p["sedge"], p["far"], 0.25)), (1.0, p["sedge"])]))
        a.put(layer, meadow * smoothstep(0.55, 0.75, a.noise("budj bim meadow bands", cells=40.0, octaves=2, stretch=10.0)), mix(p["sedge"], p["far"], 0.30), 0.45)
        tussocks, tussock_pen = a.drawing()
        for _ in range(260):
            v = rng.uniform(foot + 0.016, 0.716)
            tussock_pen.ellipse(rng.uniform(-0.02, 0.80), v, 0.0020 + (v - foot) * 0.06, 0.0008 + (v - foot) * 0.016)
        tussock_mask = a.mask_of(tussocks) * meadow * (1.0 - lake)
        a.put(layer, tussock_mask, mix(p["sedge"], p["far"], 0.15), 0.45)
        a.light(layer, a.rim(tussock_mask, 0.0, 0.001, 0.0) * tussock_mask, p["grass"], 0.25)
        # The rises, the far row first: grass on the tops, dark basalt in
        # the faces with pale lichen, a lit edge on each hummock.
        rock_paint = a.noise("budj bim rise rock", cells=160.0, octaves=2)
        for r, m in enumerate(rows):
            depth = 0.40 - 0.10 * r
            a.put(layer, m, mix(mix(p["grass"], p["moss"], 0.5), p["far"], depth))
            face = m * smoothstep(0.42, 0.60, rock_paint)
            a.put(layer, face, mix(p["basalt"], p["far"], depth * 0.8), 0.85)
            a.put(layer, face * smoothstep(0.80, 0.88, a.noise(("budj bim lichen", r), cells=260.0, octaves=1)), mix(p["lichen"], p["far"], depth * 0.6), 0.7)
            a.light(layer, a.rim(m, 0.0, 0.003, 0.2) * m, p["glow"], 0.40)
            a.shade(layer, a.rim(m, 0.0, -0.003, 0.3) * m, 0.30)
        # The water: the wetland and the channel, with the sky in them.
        water = np.maximum(lake, channel)
        a.put(layer, water, a.ramp([(0.0, mix(p["water_light"], p["low"], 0.25)), (0.62, mix(p["water_light"], p["low"], 0.25)), (0.66, mix(p["water"], p["water_light"], 0.35)), (1.0, p["water"])]))
        lines = smoothstep(0.66, 0.84, a.noise("budj bim lake lines", cells=60.0, octaves=2, stretch=16.0))
        a.light(layer, water * lines, p["water_light"], 0.25)
        a.put(layer, _reflected(a, np.maximum(rises, crown_mask), foot + 0.008, "budj bim lake ripple", lake), mix(p["basalt"], p["water"], 0.55), 0.30)
        a.put(layer, weir_mask, mix(p["basalt"], p["far"], 0.20))
        a.light(layer, a.rim(weir_mask, 0.0, 0.001, 0.0) * weir_mask, p["basalt_light"], 0.40)
        a.put(layer, trap_mask, mix(p["trap"], p["far"], 0.15))
        a.put(layer, reed_mask, mix(p["sedge"], p["far"], 0.25))
        a.shade(layer, reed_mask * smoothstep(0.4, 0.7, a.noise("budj bim reed shade", cells=300.0, octaves=1)), 0.20)
        a.put(layer, head_mask, mix(p["reed_head"], p["far"], 0.35), 0.8)
        # Houses, trees, swans and the smoke.
        a.put(layer, wall_mask, mix(p["wall"], p["far"], 0.20))
        a.light(layer, wall_mask * smoothstep(0.55, 0.75, a.noise("budj bim far wall stones", cells=500.0, octaves=1)), p["basalt_light"], 0.35)
        a.put(layer, roof_mask * (1.0 - wall_mask), mix(p["roof"], p["far"], 0.20))
        a.put(layer, roof_mask * (1.0 - wall_mask) * smoothstep(0.50, 0.70, a.noise("budj bim far turf", cells=300.0, octaves=1)), mix(p["turf"], p["far"], 0.25), 0.7)
        a.light(layer, a.rim(roof_mask, 0.001, 0.002, 0.0) * roof_mask * (1.0 - wall_mask), p["glow"], 0.35)
        a.put(layer, door_mask, mix(p["near"], p["far"], 0.20))
        a.put(layer, trunk_mask, mix(p["gum"], p["far"], 0.25))
        a.put(layer, crown_mask, mix(p["leaf"], p["far"], 0.30))
        a.put(layer, black_mask, mix(p["blackwood"], p["far"], 0.30))
        a.put(layer, swan_mask, mix(p["swan"], p["far"], 0.15))
        a.put(layer, bill_mask, p["bill"], 0.9)
        a.put(layer, smoke, p["smoke"], 0.70)
        mask = np.maximum(mask, smoke * 0.70)
        a.tint(layer, fog(a, "budj bim water mist", foot + 0.004, 0.012, 3.0) * mask, p["low"], 0.30)
        haze(a, layer, p["low"], 0.08, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near budj bim")
        bank, ground, bank_at = _bank(a, "near budj bim", 0.050, 0.056)
        # At the left a lump of the stony rise, rough basalt boulders under
        # moss, with sedges at its foot; at the right a manna gum, and the
        # low stacked wall of a weir going down to a channel, with reeds.
        # The middle is a calm bank of dark earth and grass.
        stones = [a.drawing() for _ in range(3)]
        pens = [s[1] for s in stones]
        base = bank_at(0.10) + 0.008
        for u, v, w, h in ((0.00, base - 0.050, 0.060, 0.052), (0.06, base - 0.072, 0.050, 0.040), (0.115, base - 0.040, 0.040, 0.036),
                           (0.03, base - 0.010, 0.050, 0.040), (0.155, base - 0.012, 0.032, 0.026), (0.09, base - 0.006, 0.040, 0.030),
                           (0.195, base + 0.002, 0.020, 0.014), (-0.02, base - 0.098, 0.040, 0.030), (0.045, base - 0.112, 0.030, 0.022)):
            _boulder(pens[rng.randrange(3)], rng, u, v, w, h * 0.8)
        # Dark gaps between the stones, behind them.
        gaps, gap_pen = a.drawing()
        gap_pen.poly([(-0.02, base + 0.02), (-0.02, base - 0.10), (0.05, base - 0.10), (0.13, base - 0.05), (0.17, base - 0.02), (0.19, base + 0.02)])
        wall_base = bank_at(0.86) + 0.010
        _stones(pens, rng, 0.79, 1.03, wall_base, 0.022, 3)
        gap_pen.poly([(0.805, wall_base + 0.01), (0.81, wall_base - 0.048), (1.03, wall_base - 0.050), (1.03, wall_base + 0.01)])
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        _gum(trunk_pen, crown_pen, rng, 0.90, wall_base - 0.010, 0.62)
        sedges, sedge_pen = a.drawing()
        reeds, reed_pen = a.drawing()
        for u, h in ((0.215, 0.040), (0.245, 0.030), (0.76, 0.044), (0.785, 0.034)):
            _grass_blades(sedge_pen, rng, u, bank_at(u) + 0.004, h, 16, 0.0016, 0.03)
        _reeds(reed_pen, rng, 0.70, 0.79, bank_at(0.75) + 0.004, 0.09, 26)
        grass, grass_pen = a.drawing()
        for _ in range(120):
            u = rng.uniform(0.18, 0.80)
            h = rng.uniform(0.004, 0.009)
            v = bank_at(u) + 0.002
            grass_pen.line([(u, v), (u + rng.uniform(-0.003, 0.003), v - h)], 0.0012)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        stone_masks = [a.mask_of(s[0]) for s in stones]
        gap_mask = a.mask_of(gaps)
        stone_all = np.maximum.reduce(stone_masks)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        sedge_mask = a.mask_of(sedges)
        reed_mask = a.mask_of(reeds)
        grass_mask = a.mask_of(grass)
        mask = np.maximum.reduce([bank_mask, gap_mask, stone_all, trunk_mask, crown_mask, sedge_mask, reed_mask, grass_mask])
        layer = a.blank()
        earth = a.ramp([(0.0, mix(p["near_light"], p["near"], 0.40)), (0.66, mix(p["near_light"], p["near"], 0.40)), (0.80, mix(p["near_light"], p["near"], 0.75)), (1.0, p["near"])])
        a.put(layer, bank_mask, earth)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.20)
        a.put(layer, trunk_mask, mix(p["gum"], p["near"], 0.42))
        a.light(layer, a.rim(trunk_mask, 0.003, 0.0, 0.0) * trunk_mask, p["glow"], 0.25)
        a.put(layer, crown_mask, mix(p["leaf"], p["near"], 0.38))
        a.put(layer, gap_mask, mix(p["basalt"], p["near"], 0.70))
        # The stones: dark basalt, each its own tone, lit on its top and
        # left and dark at its foot, with moss on the tops and lichen.
        for k, m in enumerate(stone_masks):
            a.put(layer, m, mix(mix(p["basalt"], p["basalt_light"], 0.10 * k), p["near"], 0.30))
            a.light(layer, a.rim(m, 0.004, 0.005, 0.3) * m, p["basalt_light"], 0.40)
            a.shade(layer, a.rim(m, -0.004, -0.005, 0.3) * m, 0.35)
        pits = smoothstep(0.70, 0.80, a.noise("budj bim near pits", cells=260.0, octaves=1))
        a.shade(layer, stone_all * pits, 0.25)
        moss = a.rim(stone_all, 0.0, 0.010, 0.5) * stone_all * smoothstep(0.40, 0.56, a.noise("budj bim near moss", cells=40.0, octaves=3))
        a.put(layer, moss, mix(p["moss"], p["near"], 0.30), 0.85)
        a.light(layer, moss * smoothstep(0.6, 0.8, a.noise("budj bim near moss light", cells=200.0, octaves=1)), p["glow"], 0.20)
        a.put(layer, stone_all * smoothstep(0.80, 0.86, a.noise("budj bim near lichen", cells=90.0, octaves=2)), mix(p["lichen"], p["near"], 0.25), 0.55)
        a.put(layer, grass_mask, mix(p["grass"], p["near"], 0.45))
        a.put(layer, sedge_mask, mix(p["sedge"], p["near"], 0.35))
        a.put(layer, reed_mask, mix(p["sedge"], p["near"], 0.40))
        a.put(layer, reed_mask * smoothstep(0.62, 0.60, a.v), mix(p["reed_head"], p["near"], 0.35), 0.5)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.18)
        haze(a, layer, p["low"], 0.10, None)
        return layer
    layer = _air(a, p, "budj bim wetland mist", p["low"], 0.30, scale(p["near"], 0.8), 0.16)
    return layer


def budj_bim_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Sedges stand from below at one place, long blades that arch out, with
    a few tall reeds and their brown heads; a tuft of grass stands at
    another place."""
    del layer_lights
    rng = art_.rand("budj bim foreground")
    u = rng.uniform(0.12, 0.24)
    top = REST_BOTTOM - 0.004
    for k in range(14):
        t = (k - 6.5) / 6.5
        tip = (u + t * 0.09 + rng.uniform(-0.008, 0.008), top + 0.050 * t * t + rng.uniform(0.0, 0.012))
        blade = _arch((u + t * 0.010, 1.0), (u + t * 0.030, tip[1] + 0.09), tip, 12)
        _leaf(pen, blade, 0.0028, 0.25)
    for k in range(3):
        x = u + (k - 1) * 0.020 + rng.uniform(-0.006, 0.006)
        head = top - 0.030 - k * 0.012
        pen.line([(x, 1.0), (x + 0.004, head)], 0.0020)
        pen.ellipse(x + 0.004, head - 0.014, 0.0040, 0.016)
    u2 = 0.70 + rng.uniform(-0.04, 0.04)
    _grass_blades(pen, rng, u2, 1.0, 1.0 - REST_BOTTOM - 0.006, 18, 0.0014, 0.05)
