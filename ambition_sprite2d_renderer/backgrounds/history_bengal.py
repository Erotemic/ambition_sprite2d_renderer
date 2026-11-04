"""The scenes of the History dimension: Bengal and the cotton.

The History dimension is a grid. East is later, and each floor is a region
of the world. These rooms show Bengal, the wide green delta of the Ganges
and the Brahmaputra, where the finest cotton cloth of the world was woven.
They use the same sepia of an old textbook and the same rules as
`history_eras.py` and `history_east_asia_coast.py`. The people of these
places show skill, learning and courage of their own; nothing here is a
joke on them.

- ``history_dhaka_river`` (Dhaka on the Buriganga, about 1700). A misty
  morning of the monsoon season. The wide brown-green river is full of
  country boats with tall square sails. The red brick walls and the gateway
  of the Lalbagh fort (begun in 1678 and never finished) stand on the near
  bank at the left. On the far shore are fields of cotton, palms and small
  houses of thatch, and the flat green delta goes to the horizon. Banana
  plants and tall river grass are near.
- ``history_calcutta`` (Calcutta on the Hooghly, about 1800 to 1850). A
  heavy monsoon sky, with rain far off. Tall East Indiamen lie at anchor in
  the river with their sails furled. The low star-shaped earth walls of Fort
  William are at the left, and white Company buildings with tall colonnades
  line the bank at the right, with palms between them. A banyan with its
  hanging roots and plants of indigo are near.
- ``history_dhaka_spring`` (Dhaka in February, the university quarter). A
  clear morning of late winter, under a pale blue sky. The red brick Curzon
  Hall (1904) stands among the trees of the campus, with its tall pointed
  arch, its arcades and its small domed kiosks. Shimul trees (silk-cotton)
  are in red flower on their bare branches, and cycle rickshaws go along the
  road far off. A shimul branch and marigolds are near.

No picture here shows a mosque, a temple, a church or a religious sign. The
domes of Curzon Hall and of the kiosks on the fort are architecture, with a
plain knob on top.

The bright detail is far off or at the edges, and the middle of each near
layer is calm, so the play in front of it reads. The things that drift in the
air are the room's motes (`terrain/motes.py`), not part of these pictures.
"""

from __future__ import annotations

import math

import numpy as np

from .artkit import Art, Pen, mix, polar, scale, smoothstep
from .history_east_asia_coast import _bank, _grass_blades, _lumpy_crown, _reflected
from .history_eras import REST_BOTTOM, _air, _at, _sun, _textbook
from .history_origins import _arch, _land, _leaf, _rain
from .parts import HORIZON, cloud_mask, fog, haze, shafts, solid

# ---------------------------------------------------------------------------
# Parts that more than one room has
# ---------------------------------------------------------------------------


def _pointed_arch(pen: Pen, u: float, foot: float, half: float, spring: float, rise: float, pinch: float = 0.0, value: int = 255) -> None:
    """A pointed arch: straight sides from `foot` up to `spring`, and two
    curves that meet in a point `rise` over the spring. `pinch` more than 0
    makes a horseshoe arch, narrower at its foot than at its spring."""
    left = _arch((u - half, spring), (u - half, spring - rise * 0.75), (u, spring - rise), 10)
    right = _arch((u, spring - rise), (u + half, spring - rise * 0.75), (u + half, spring), 10)
    low = half * (1.0 - pinch)
    shoulder = spring + (foot - spring) * 0.18
    pen.poly([(u - low, foot), (u - half, shoulder)] + left + right[1:] + [(u + half, shoulder), (u + low, foot)], value)


def _chhatri(pen: Pen, u: float, v: float, w: float) -> None:
    """A small kiosk with a dome, as on the corners of a Mughal gate or of
    Curzon Hall: a drum, a round dome, and a plain knob on top. `(u, v)` is
    the middle of its foot."""
    pen.rect(u - w * 0.42, v - w * 0.55, u + w * 0.42, v + w * 0.02)
    pen.rect(u - w * 0.55, v - w * 0.66, u + w * 0.55, v - w * 0.52)
    pen.ellipse(u, v - w * 0.66, w * 0.44, w * 0.48)
    pen.line([(u, v - w * 1.10), (u, v - w * 1.32)], w * 0.10)
    pen.ellipse(u, v - w * 1.34, w * 0.09)


def _palm(trunk: Pen, crown: Pen, rng, u: float, v: float, h: float, lean: float) -> None:
    """A coconut palm: a thin trunk that bends as it goes up, and a head of
    long fronds that arch out and hang down."""
    top = (u + lean * h, v - h)
    pts = [(u + lean * h * t**1.6, v + 0.002 - (h + 0.002) * t) for t in np.linspace(0.0, 1.0, 9)]
    trunk.line(pts, h * 0.040)
    for k in range(9):
        ang = -200.0 + k * (220.0 / 8.0) + rng.uniform(-8.0, 8.0)
        length = h * rng.uniform(0.36, 0.48)
        tip = polar(*top, length, ang)
        tip = (tip[0], tip[1] + length * 0.50)
        ctrl = polar(*top, length * 0.6, ang)
        ctrl = (ctrl[0], ctrl[1] - length * 0.22)
        _leaf(crown, _arch(top, ctrl, tip, 8), h * 0.030, 0.5)
    crown.ellipse(top[0], top[1] + h * 0.01, h * 0.04, h * 0.03)


def _banana(stem: Pen, leaves: Pen, ribs: Pen, rng, u: float, v: float, h: float, lean: float = 0.0) -> None:
    """A banana plant: a thick soft stem of leaf sheaths, and from its top
    long broad leaves. The young leaves stand up; the old ones spread and
    hang, and the wind has torn their edges into strips."""
    top = (u + lean * h, v - h * 0.46)
    w = h * 0.050
    stem.poly([(u - w, v + 0.004), (u + w, v + 0.004), (top[0] + w * 0.55, top[1]), (top[0] - w * 0.55, top[1])])
    spreads = ((-14.0, 0.62, 0.0), (18.0, 0.58, 0.02), (-44.0, 0.64, 0.10), (50.0, 0.66, 0.12), (-74.0, 0.60, 0.24), (80.0, 0.56, 0.26), (-100.0, 0.46, 0.34))
    for spread, length, droop in spreads:
        spread += rng.uniform(-8.0, 8.0)
        base = (top[0], top[1] + h * 0.02)
        d = polar(0.0, 0.0, 1.0, -90.0 + spread)
        tip = (base[0] + d[0] * h * length, base[1] + d[1] * h * length + droop * h)
        ctrl = (base[0] + d[0] * h * length * 0.55, base[1] + d[1] * h * length * 0.55 - h * 0.10)
        rib = _arch(base, ctrl, tip, 14)
        width = h * 0.070
        _leaf(leaves, rib, width, 0.85)
        ribs.line(rib[:-2], h * 0.006)
        # The tears: thin cuts from the edge in to the rib, on the outer
        # side of the old leaves.
        if abs(spread) > 30.0:
            for i in range(4, 13, 2):
                (x0, y0), (x1, y1) = rib[i - 1], rib[i + 1]
                nx, ny = -(y1 - y0), x1 - x0
                norm = math.hypot(nx, ny) or 1.0
                nx, ny = nx / norm, ny / norm
                if ny < 0:
                    nx, ny = -nx, -ny
                x, y = rib[i]
                leaves.line([(x + nx * width * 0.25, y + ny * width * 0.25), (x + nx * width * 1.2, y + ny * width * 1.2)], h * 0.004, value=0)


def _country_boat(hull: Pen, roof: Pen, sail: Pen, rig: Pen, u: float, v: float, s: float, facing: float = 1.0, sail_up: bool = True) -> None:
    """A country boat of the rivers of Bengal: a long hull of planks whose
    two ends rise in high curves, an arched roof of split bamboo and matting
    over its middle, a boatman at the stern with the long steering oar, and
    a tall square sail on one mast. `s` is its length and `(u, v)` the
    middle of its waterline."""
    f = facing

    def at(x: float, y: float) -> tuple[float, float]:
        return (u + f * x * s, v - y * s)

    hull.poly([at(-0.54, 0.22), at(-0.48, 0.12), at(-0.38, 0.03), at(-0.22, -0.012), at(0.24, -0.012), at(0.40, 0.03), at(0.50, 0.12), at(0.58, 0.26),
               at(0.54, 0.26), at(0.45, 0.14), at(0.34, 0.078), at(-0.30, 0.072), at(-0.42, 0.12), at(-0.50, 0.22)])
    roof.poly([at(-0.30, 0.07)] + [at(-0.30 + 0.40 * t, 0.07 + 0.12 * math.sin(math.pi * t) ** 0.5) for t in np.linspace(0.0, 1.0, 12)] + [at(0.10, 0.07)])
    mast = 0.20
    rig.line([at(mast, 0.07), at(mast, 1.0 if sail_up else 0.50)], s * 0.014)
    rig.line([at(-0.42, 0.18), at(-0.62, -0.06)], s * 0.012)
    rig.line([at(-0.42, 0.10), at(-0.42, 0.25)], s * 0.030)
    rig.ellipse(*at(-0.42, 0.28), s * 0.022)
    if sail_up:
        top, foot = 0.96, 0.22
        mid = (top + foot) * 0.5
        sail.poly([at(mast - 0.20, top), at(mast + 0.22, top), at(mast + 0.26, mid), at(mast + 0.22, foot), at(mast - 0.17, foot), at(mast - 0.15, mid)])
        rig.line([at(mast - 0.23, top + 0.01), at(mast + 0.25, top + 0.01)], s * 0.012)
        rig.line([at(mast - 0.17, foot), at(-0.38, 0.20)], s * 0.005)
    else:
        rig.line([at(mast - 0.05, 0.50), at(mast + 0.30, 0.20)], s * 0.020)


# ---------------------------------------------------------------------------
# Dhaka on the Buriganga: a misty morning of the monsoon season, about 1700
# ---------------------------------------------------------------------------


DHAKA_RIVER = {
    "top": (140, 160, 168),
    "mid": (198, 204, 196),
    "low": (236, 228, 204),
    "glow": (255, 226, 172),
    "sun": (255, 244, 216),
    "cloud": (236, 234, 224),
    "cloud_shadow": (164, 170, 170),
    "delta": (104, 134, 78),
    "delta_light": (176, 190, 118),
    "field": (126, 150, 80),
    "cotton": (244, 240, 226),
    "palm": (60, 92, 58),
    "palm_light": (132, 152, 92),
    "trunk": (104, 88, 70),
    "thatch": (176, 146, 96),
    "river": (132, 128, 94),
    "river_light": (204, 200, 170),
    "river_deep": (92, 90, 64),
    "brick": (170, 76, 54),
    "brick_light": (218, 132, 96),
    "brick_dark": (110, 48, 36),
    "plaster": (226, 210, 184),
    "gate_dark": (58, 36, 30),
    "earth": (128, 104, 74),
    "hull": (84, 62, 44),
    "hull_light": (156, 118, 80),
    "sail": (226, 212, 180),
    "sail_shade": (176, 156, 122),
    "mat": (180, 154, 106),
    "rig": (60, 46, 36),
    "grass": (92, 128, 58),
    "grass_light": (172, 184, 104),
    "banana": (96, 140, 64),
    "banana_light": (182, 204, 110),
    "banana_dark": (52, 84, 42),
    "far": (210, 210, 196),
    "near": (34, 40, 28),
    "near_light": (140, 140, 92),
}

#: The level where the far shore meets the river.
DHAKA_SHORE = 0.612
#: The top of the near bank at the left, where the walls of Lalbagh stand,
#: and the level of the water at its foot.
DHAKA_FORT_BANK = 0.655
DHAKA_FORT_WATER = 0.668


def _lalbagh(walls: Pen, panels: Pen, holes: Pen, u0: float, u1: float, v: float, h: float, gate_u: float, gate_w: float) -> None:
    """The river face of the Lalbagh fort: a curtain wall of red brick with
    a row of rounded merlons and a row of blind arches, an octagonal bastion
    at each end with a domed kiosk on it, and the tall gateway: a block with
    a great pointed arch in a frame, small arched windows over it, and a
    slender turret at each corner. The fort was never finished; there is no
    flag and no sign on it."""
    walls.rect(u0, v - h, u1, v + 0.002)
    m = h * 0.22
    x = u0 + m * 0.4
    while x < u1 - m * 0.4:
        walls.rect(x - m * 0.30, v - h - m * 0.7, x + m * 0.30, v - h + 0.001)
        walls.ellipse(x, v - h - m * 0.7, m * 0.30, m * 0.34)
        x += m * 1.05
    # The blind arches along the wall, each a shallow recess of plaster.
    bay = h * 0.75
    x = u0 + bay
    while x < u1 - bay * 0.6:
        if abs(x - gate_u) > gate_w * 0.5 + bay * 0.5:
            _pointed_arch(panels, x, v - h * 0.22, bay * 0.26, v - h * 0.60, h * 0.18)
        x += bay
    for bu in (u0, u1):
        bw = h * 0.55
        walls.rect(bu - bw, v - h * 1.35, bu + bw, v + 0.002)
        walls.rect(bu - bw * 1.08, v - h * 1.42, bu + bw * 1.08, v - h * 1.32)
        _chhatri(walls, bu, v - h * 1.42, bw * 0.95)
        _pointed_arch(panels, bu, v - h * 0.40, bw * 0.30, v - h * 0.85, h * 0.16)
    # The gateway.
    gh = h * 2.2
    half = gate_w * 0.5
    walls.rect(gate_u - half, v - gh, gate_u + half, v + 0.002)
    walls.rect(gate_u - half * 1.06, v - gh - h * 0.08, gate_u + half * 1.06, v - gh + h * 0.04)
    x = gate_u - half + m * 0.6
    while x < gate_u + half - m * 0.3:
        walls.ellipse(x, v - gh - h * 0.12, m * 0.30, m * 0.34)
        x += m * 1.05
    panels.rect(gate_u - half * 0.62, v - gh * 0.78, gate_u + half * 0.62, v + 0.001)
    _pointed_arch(holes, gate_u, v + 0.001, half * 0.40, v - gh * 0.46, gh * 0.16)
    for k in (-1.0, 0.0, 1.0):
        _pointed_arch(holes, gate_u + k * half * 0.40, v - gh * 0.80, half * 0.11, v - gh * 0.86, gh * 0.05)
    for side in (-1.0, 1.0):
        tu = gate_u + side * half
        walls.rect(tu - h * 0.16, v - gh - h * 0.40, tu + h * 0.16, v + 0.002)
        _chhatri(walls, tu, v - gh - h * 0.40, h * 0.42)


def history_dhaka_river(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = DHAKA_RIVER
    sun_at = (0.70, 0.40)
    shore = DHAKA_SHORE
    bank_v = DHAKA_FORT_BANK
    water_v = DHAKA_FORT_WATER
    if layer_key == "sky":
        # A morning of the monsoon: a soft grey-blue sky, wide banks of pale
        # cloud, a sun that is only a bright place in the mist, and the flat
        # delta far off as a low line of trees.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.92)), (0.30, p["top"]), (0.50, p["mid"]), (HORIZON - 0.01, p["low"]),
                                 (HORIZON + 0.002, mix(p["river"], p["low"], 0.50)), (1.0, mix(p["river"], p["low"], 0.30))]))
        clouds = cloud_mask(a, "dhaka clouds", 0.34, 0.14, cells=3.0, cover=0.55, soft=0.28, stretch=3.5)
        a.put(layer, clouds, p["cloud"], 0.55)
        a.put(layer, clouds * a.band(0.40, 0.08), p["cloud_shadow"], 0.25)
        low = cloud_mask(a, "dhaka low clouds", 0.50, 0.06, cells=4.0, cover=0.45, soft=0.30, stretch=5.0)
        a.put(layer, low, mix(p["cloud"], p["low"], 0.4), 0.45)
        # The sun is only a bright place in the mist: a wide glow and a
        # disc with a soft edge.
        a.light(layer, a.spot(*sun_at, 0.22, 2.0, squash=1.3), p["glow"], 0.40)
        a.light(layer, a.spot(*sun_at, 0.07, 1.4), p["glow"], 0.45)
        a.put(layer, a.spot(*sun_at, 0.026, 0.5), p["sun"], 0.75)
        a.tint(layer, a.spot(*sun_at, 0.30, 1.5), p["glow"], 0.15)
        trees, _ = a.ridge("dhaka far trees", HORIZON - 0.004, 0.0025, cells=60.0, octaves=3)
        trees = trees * smoothstep(HORIZON + 0.004, HORIZON + 0.001, a.v)
        a.put(layer, trees, mix(p["delta"], p["low"], 0.62))
        a.tint(layer, fog(a, "dhaka horizon mist", HORIZON - 0.002, 0.014, 3.0), p["low"], 0.55)
        _textbook(a, layer, 0.08)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far dhaka")
        # The far shore: the flat land of the delta, a little above the
        # water, with clumps of trees, palms, houses of thatch and fields.
        far_top = (HORIZON - 0.004 - (a.line_noise("dhaka far bank", cells=24.0, octaves=2) - 0.5) * 0.002).astype(np.float32)
        far_land = _land(a, far_top) * smoothstep(shore + 0.0015, shore - 0.0005, a.v)
        clumps, clump_pen = a.drawing()
        palms, palm_pen = a.drawing()
        trunks, trunk_pen = a.drawing()
        huts, hut_pen = a.drawing()
        roofs, roof_pen = a.drawing()
        u = -0.02
        while u < 1.02:
            base = _at(far_top, max(0.0, min(0.999, u))) + 0.002
            kind = rng.random()
            if 0.50 < u < 0.78:
                # The cotton fields: open land with only a palm here and there.
                if kind < 0.12:
                    _palm(trunk_pen, palm_pen, rng, u, base + 0.004, rng.uniform(0.020, 0.028), rng.uniform(-0.15, 0.15))
                u += rng.uniform(0.03, 0.05)
                continue
            if kind < 0.35:
                _palm(trunk_pen, palm_pen, rng, u, base + 0.003, rng.uniform(0.018, 0.034), rng.uniform(-0.2, 0.2))
            elif kind < 0.48:
                hw = rng.uniform(0.006, 0.009)
                hut_pen.rect(u - hw, base - hw * 0.5, u + hw, base + 0.006)
                roof_pen.poly([(u - hw * 1.3, base - hw * 0.4), (u - hw * 0.5, base - hw * 1.2), (u + hw * 0.5, base - hw * 1.2), (u + hw * 1.3, base - hw * 0.4)])
            else:
                _lumpy_crown(clump_pen, rng, u, base - 0.006, rng.uniform(0.010, 0.018), rng.uniform(0.006, 0.010), 14)
            u += rng.uniform(0.012, 0.028)
        field = far_land * smoothstep(0.49, 0.52, a.u) * smoothstep(0.79, 0.76, a.u) * smoothstep(far_top[None, :] + 0.003, far_top[None, :] + 0.005, a.v)
        # The near bank at the left, where the fort stands, and the steps of
        # a ghat that go down from its gate to the water.
        fort_bank, fort_bank_pen = a.drawing()
        fort_bank_pen.poly([(-0.02, bank_v - 0.001), (0.55, bank_v - 0.001), (0.585, water_v), (-0.02, water_v)])
        fort = {key: a.drawing() for key in ("walls", "panels", "holes")}
        gate_u = 0.31
        _lalbagh(fort["walls"][1], fort["panels"][1], fort["holes"][1], 0.10, 0.51, bank_v, 0.034, gate_u, 0.080)
        behind, behind_pen = a.drawing()
        for bu, r in ((0.16, 0.020), (0.21, 0.016), (0.41, 0.022), (0.45, 0.018), (0.48, 0.015)):
            _lumpy_crown(behind_pen, rng, bu, bank_v - 0.034, r, r * 0.6, 16)
        steps, steps_pen = a.drawing()
        steps_pen.poly([(gate_u - 0.034, bank_v), (gate_u + 0.034, bank_v), (gate_u + 0.044, water_v + 0.002), (gate_u - 0.044, water_v + 0.002)])
        # The boats: two tied at the bank with their sails down, and more on
        # the river under sail, the near ones larger.
        boats = []
        for bu, bv, s, f, up in ((0.17, 0.676, 0.060, 1.0, False), (0.45, 0.680, 0.070, -1.0, False), (0.60, 0.622, 0.040, 1.0, True),
                                 (0.96, 0.622, 0.048, -1.0, True), (0.84, 0.634, 0.075, -1.0, True), (0.70, 0.658, 0.115, 1.0, True), (0.90, 0.692, 0.150, -1.0, True)):
            pens = {key: a.drawing() for key in ("hull", "roof", "sail", "rig")}
            _country_boat(pens["hull"][1], pens["roof"][1], pens["sail"][1], pens["rig"][1], bu, bv, s, f, up)
            boats.append((bv, {key: a.mask_of(img) for key, (img, _) in pens.items()}))
        clump_mask = a.mask_of(clumps)
        palm_mask = a.mask_of(palms)
        trunk_mask = a.mask_of(trunks)
        hut_mask = a.mask_of(huts)
        roof_mask = a.mask_of(roofs)
        on_far = np.maximum.reduce([clump_mask, palm_mask, trunk_mask, hut_mask, roof_mask])
        fort_bank_mask = a.mask_of(fort_bank)
        fm = {key: a.mask_of(img) for key, (img, _) in fort.items()}
        fort_mask = fm["walls"]
        behind_mask = a.mask_of(behind) * (1.0 - fort_mask)
        steps_mask = a.mask_of(steps) * fort_bank_mask
        boat_mask = np.maximum.reduce([np.maximum.reduce(list(bm.values())) for _, bm in boats])
        land = np.maximum.reduce([far_land, on_far, fort_bank_mask, fort_mask, behind_mask])
        water = smoothstep(shore - 0.002, shore + 0.001, a.v) * (1.0 - fort_bank_mask)
        mask = np.maximum.reduce([land, water, boat_mask])
        layer = solid(a, mask, mix(p["delta"], p["far"], 0.45), p["delta"], HORIZON, 0.70, "dhaka far", 0.03)
        # The river: pale where it shows the misty sky far off, brown-green
        # toward the eye, with long lines of current and the soft pictures
        # of the things on it.
        a.put(layer, water, a.ramp([(0.0, mix(p["river_light"], p["low"], 0.35)), (shore, mix(p["river_light"], p["low"], 0.35)),
                                     (0.64, mix(p["river"], p["river_light"], 0.40)), (0.70, p["river"]), (1.0, p["river_deep"])]))
        a.put(layer, _reflected(a, np.maximum(far_land, on_far) * (a.v < shore + 0.001), shore, "dhaka shore ripple", water), mix(p["delta"], p["river"], 0.55), 0.35)
        a.put(layer, _reflected(a, np.maximum(fort_mask, behind_mask), water_v, "dhaka fort ripple", water), mix(p["brick"], p["river"], 0.45), 0.40)
        for k, (bv, bm) in enumerate(boats):
            body = np.maximum.reduce(list(bm.values()))
            a.put(layer, _reflected(a, body, bv + 0.0005, f"dhaka boat ripple {k}", water * (1.0 - boat_mask)), mix(p["sail_shade"], p["river"], 0.50), 0.40)
        lines = smoothstep(0.62, 0.84, a.noise("dhaka current", cells=60.0, octaves=2, stretch=16.0))
        a.light(layer, water * lines * smoothstep(shore + 0.008, shore + 0.05, a.v), p["river_light"], 0.25)
        glitter = water * a.spot(sun_at[0], 0.64, 0.14, 1.2, squash=0.7) * smoothstep(0.55, 0.78, a.noise("dhaka glitter", cells=110.0, octaves=2, stretch=10.0))
        a.light(layer, glitter, p["glow"], 0.40)
        # The far shore: green land, the cotton fields in rows with white
        # bolls, dark clumps of trees, palms, and houses of thatch.
        a.put(layer, far_land, mix(p["delta"], p["far"], 0.40))
        a.put(layer, field, mix(p["field"], p["far"], 0.35))
        rows = np.clip(1.0 - np.abs((((a.v - shore) / 0.0024) % 1.0) - 0.5) / 0.22, 0.0, 1.0)
        bolls = smoothstep(0.62, 0.70, a.noise("dhaka bolls", cells=420.0, octaves=1))
        a.put(layer, field * rows, mix(p["delta"], p["far"], 0.25), 0.55)
        a.put(layer, field * rows * bolls, mix(p["cotton"], p["far"], 0.15), 0.85)
        a.put(layer, clump_mask, mix(p["palm"], p["far"], 0.40))
        a.light(layer, a.rim(clump_mask, -0.002, 0.002, 0.3) * clump_mask, mix(p["delta_light"], p["far"], 0.3), 0.40)
        a.put(layer, hut_mask, mix(p["earth"], p["far"], 0.35))
        a.put(layer, roof_mask, mix(p["thatch"], p["far"], 0.30))
        a.put(layer, trunk_mask, mix(p["trunk"], p["far"], 0.40))
        a.put(layer, palm_mask, mix(p["palm"], p["far"], 0.35))
        a.light(layer, a.rim(palm_mask, -0.0015, 0.0015, 0.0) * palm_mask, mix(p["palm_light"], p["far"], 0.3), 0.45)
        a.tint(layer, fog(a, "dhaka shore mist", shore - 0.006, 0.010, 3.0) * mask, p["low"], 0.45)
        # The near bank: wet brown earth, and the steps of the ghat.
        a.put(layer, fort_bank_mask, mix(p["earth"], p["delta"], 0.30))
        a.put(layer, fort_bank_mask * smoothstep(bank_v + 0.004, water_v, a.v), mix(p["earth"], p["river_deep"], 0.35), 0.7)
        a.put(layer, fort_bank_mask * smoothstep(bank_v + 0.002, bank_v - 0.001, a.v), mix(p["grass"], p["far"], 0.25))
        a.put(layer, steps_mask, mix(p["brick"], p["plaster"], 0.30))
        a.shade(layer, steps_mask * np.clip(1.0 - np.abs((((a.v - bank_v) / 0.0026) % 1.0) - 0.5) / 0.12, 0.0, 1.0), 0.30)
        # The fort: red brick in fine courses, lit on the faces to the sun
        # at the right; the blind arches a pale plaster; the arch of the
        # gate dark.
        a.put(layer, behind_mask, mix(p["palm"], p["far"], 0.30))
        a.light(layer, a.rim(behind_mask, -0.002, 0.002, 0.3) * behind_mask, mix(p["delta_light"], p["far"], 0.3), 0.40)
        a.put(layer, fort_mask, mix(p["brick"], p["far"], 0.12))
        courses = np.clip(1.0 - np.abs((((a.v - bank_v) / 0.0016) % 1.0) - 0.5) / 0.10, 0.0, 1.0)
        a.shade(layer, fort_mask * courses, 0.10)
        a.shade(layer, fort_mask * smoothstep(0.45, 0.75, a.noise("dhaka brick stains", cells=40.0, octaves=3)), 0.12)
        a.put(layer, fm["panels"] * fort_mask, mix(p["brick_dark"], p["brick"], 0.45))
        a.shade(layer, a.rim(fm["panels"], 0.0015, 0.0015, 0.0) * fm["panels"] * fort_mask, 0.35)
        a.light(layer, a.rim(fm["panels"], -0.0012, 0.0, 0.0) * fm["panels"] * fort_mask, p["brick_light"], 0.45)
        a.put(layer, fm["holes"] * fort_mask, p["gate_dark"])
        a.light(layer, a.rim(fort_mask, -0.0025, 0.0, 0.0) * fort_mask, p["brick_light"], 0.55)
        a.light(layer, a.rim(fort_mask, 0.0, 0.0018, 0.0) * fort_mask, mix(p["brick_light"], p["glow"], 0.4), 0.45)
        a.shade(layer, a.rim(fort_mask, 0.0025, 0.0, 0.0) * fort_mask, 0.18)
        # The boats: dark hulls lit on their rims, roofs of matting, pale
        # sails with seams and patches, and the rigging dark.
        for bv, bm in boats:
            a.put(layer, bm["roof"], p["mat"])
            a.shade(layer, bm["roof"] * smoothstep(0.4, 0.8, a.noise("dhaka mat", cells=300.0, octaves=1, stretch=0.2)), 0.18)
            a.put(layer, bm["hull"], p["hull"])
            a.light(layer, a.rim(bm["hull"], 0.0, 0.0015, 0.0) * bm["hull"], p["hull_light"], 0.55)
            a.put(layer, bm["sail"], p["sail"])
            seams = np.clip(1.0 - np.abs(((a.v * 520.0) % 1.0) - 0.5) / 0.10, 0.0, 1.0)
            a.put(layer, bm["sail"] * seams, p["sail_shade"], 0.45)
            a.shade(layer, a.rim(bm["sail"], -0.003, 0.0, 0.4) * bm["sail"], 0.18)
            a.put(layer, bm["rig"], p["rig"])
        a.tint(layer, fog(a, "dhaka river mist", 0.664, 0.010, 3.0) * water, p["low"], 0.40)
        haze(a, layer, p["low"], 0.08, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near dhaka")
        bank, ground, bank_at = _bank(a, "near dhaka", 0.030, 0.026)
        stems, stem_pen = a.drawing()
        leaves, leaf_pen = a.drawing()
        ribs, rib_pen = a.drawing()
        grass, grass_pen = a.drawing()
        tall, tall_pen = a.drawing()
        # Banana plants at the left; tall river grass at the right; the
        # middle is a calm bank of short grass.
        for u, h, lean in ((0.045, 0.27, 0.02), (0.135, 0.19, -0.04), (0.20, 0.12, 0.03)):
            _banana(stem_pen, leaf_pen, rib_pen, rng, u, bank_at(u) + 0.004, h, lean)
        for u, h in ((0.76, 0.07), (0.82, 0.11), (0.87, 0.15), (0.92, 0.12), (0.97, 0.16), (0.995, 0.10)):
            _grass_blades(tall_pen, rng, u, bank_at(u) + 0.004, h, 22, 0.0022, 0.05)
        for _ in range(16):
            u = rng.uniform(0.26, 0.72)
            _grass_blades(grass_pen, rng, u, bank_at(u) + 0.002, rng.uniform(0.010, 0.020), 6, 0.0012, 0.010)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        stem_mask = a.mask_of(stems)
        leaf_mask = a.mask_of(leaves)
        rib_mask = a.mask_of(ribs) * leaf_mask
        grass_mask = a.mask_of(grass)
        tall_mask = a.mask_of(tall)
        mask = np.maximum.reduce([bank_mask, stem_mask, leaf_mask, grass_mask, tall_mask])
        layer = a.blank()
        earth = a.ramp([(0.0, mix(p["grass"], p["near"], 0.45)), (0.66, mix(p["grass"], p["near"], 0.45)), (0.78, mix(p["earth"], p["near"], 0.70)), (1.0, p["near"])])
        a.put(layer, bank_mask, earth)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.25)
        a.put(layer, grass_mask, mix(p["grass"], p["near"], 0.35))
        a.light(layer, a.rim(grass_mask, -0.0015, 0.0, 0.2) * grass_mask, p["grass_light"], 0.30)
        a.put(layer, tall_mask, mix(p["grass"], p["near"], 0.30))
        a.put(layer, tall_mask * smoothstep(0.45, 0.70, a.noise("dhaka grass shade", cells=30.0, octaves=2)), mix(p["banana_dark"], p["near"], 0.30), 0.55)
        a.light(layer, a.rim(tall_mask, -0.0015, 0.0, 0.0) * tall_mask, p["grass_light"], 0.40)
        # The bananas: a pale stem, big leaves of fresh green with a lit
        # rim and a pale rib, the old leaves yellowed at their edges.
        a.put(layer, stem_mask, mix(p["banana_light"], p["near"], 0.35))
        a.shade(layer, stem_mask * smoothstep(0.45, 0.75, a.noise("dhaka stem", cells=200.0, octaves=1, stretch=0.1)), 0.20)
        a.put(layer, leaf_mask, mix(p["banana"], p["near"], 0.25))
        a.put(layer, leaf_mask * smoothstep(0.45, 0.72, a.noise("dhaka leaf shade", cells=18.0, octaves=2)), mix(p["banana_dark"], p["near"], 0.25), 0.55)
        a.put(layer, a.rim(leaf_mask, 0.0, -0.004, 0.6) * leaf_mask * smoothstep(0.55, 0.70, a.noise("dhaka leaf brown", cells=12.0, octaves=2)), mix(p["thatch"], p["near"], 0.25), 0.6)
        a.light(layer, a.rim(leaf_mask, -0.002, 0.002, 0.0) * leaf_mask, p["banana_light"], 0.45)
        a.put(layer, rib_mask, mix(p["banana_light"], p["near"], 0.20), 0.7)
        a.shade(layer, a.rim(mask, 0.004, -0.003, 1.0) * mask, 0.18)
        haze(a, layer, p["low"], 0.10, None)
        return layer
    layer = _air(a, p, "dhaka morning mist", p["low"], 0.34, scale(p["near"], 0.8), 0.14)
    a.put(layer, shafts(a, "dhaka shafts", 4, -0.10, 0.0, 0.85, 0.05), p["glow"], 0.06)
    return layer


def dhaka_river_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Tall river grass stands from below at two places. A torn leaf of a
    banana hangs from above at one place."""
    del layer_lights
    rng = art_.rand("dhaka river foreground")
    for k in range(2):
        u0 = 0.10 + (k + rng.uniform(0.2, 0.8)) * 0.40
        for _ in range(12):
            u = u0 + rng.uniform(-0.014, 0.014)
            top = REST_BOTTOM - rng.uniform(-0.004, 0.012)
            lean = rng.uniform(-0.05, 0.05)
            pen.line(_arch((u, 1.0), (u + lean * 0.3, top + 0.10), (u + lean, top), 10), 0.0016)
    # The banana leaf: a stalk that comes down from above, and the broad
    # blade that hangs from it, cut into strips by the wind.
    u = rng.uniform(0.44, 0.56)
    rib = _arch((u - 0.06, 0.0), (u + 0.02, 0.16), (u + 0.05, 0.372), 16)
    pen.line(rib[:5], 0.0040)
    _leaf(pen, rib[3:], 0.024, 0.8)
    for i in range(6, 16, 2):
        x, y = rib[i]
        for side in (-1.0, 1.0):
            pen.line([(x + side * 0.004, y), (x + side * 0.030, y + 0.010)], 0.0016, value=0)


# ---------------------------------------------------------------------------
# Calcutta on the Hooghly: the monsoon, about 1800 to 1850
# ---------------------------------------------------------------------------


CALCUTTA = {
    "top": (72, 82, 94),
    "mid": (124, 132, 138),
    "low": (214, 206, 184),
    "glow": (246, 224, 172),
    "cloud_dark": (70, 78, 88),
    "cloud": (150, 156, 158),
    "cloud_light": (214, 210, 198),
    "rain": (150, 160, 166),
    "river": (114, 116, 102),
    "river_light": (190, 190, 174),
    "river_deep": (70, 74, 66),
    "land": (96, 116, 84),
    "glacis": (108, 134, 80),
    "glacis_light": (170, 184, 116),
    "rampart": (166, 92, 66),
    "rampart_light": (210, 150, 112),
    "ditch": (84, 98, 80),
    "white": (234, 230, 216),
    "white_shade": (164, 166, 164),
    "colonnade": (96, 98, 96),
    "parapet": (206, 200, 186),
    "steps": (196, 186, 166),
    "hull": (44, 40, 38),
    "band": (206, 170, 90),
    "sail": (220, 214, 196),
    "rig": (56, 48, 42),
    "palm": (58, 86, 58),
    "palm_light": (124, 142, 92),
    "trunk": (100, 88, 72),
    "laterite": (146, 74, 50),
    "laterite_light": (200, 120, 80),
    "bark": (112, 100, 84),
    "bark_light": (172, 160, 136),
    "banyan": (54, 84, 52),
    "banyan_light": (120, 146, 86),
    "indigo": (62, 98, 70),
    "indigo_light": (134, 160, 112),
    "indigo_flower": (172, 98, 150),
    "far": (180, 184, 178),
    "near": (28, 32, 30),
    "near_light": (120, 126, 104),
}

#: The level where the far shore (the Howrah side) meets the river.
CALCUTTA_SHORE = 0.606


def _star_fort(ditch: Pen, top: Pen, lit: Pen, shaded: Pen, u: float, v: float, rx: float, rz: float, h: float, points: int = 5) -> None:
    """A fort with a plan of a star, as Fort William was rebuilt after
    1757: low walls of earth faced with brick, and a bastion at each point.
    The eye is a little above it, so the plan is seen flat: `rx` and `rz`
    are its half width and half depth on the picture, and `h` is the height
    of its walls. The faces that turn to the left take the light. A wide
    ditch goes round it."""
    star = []
    for k in range(points * 2):
        ang = math.pi * 0.5 + k * math.pi / points
        r = 1.0 if k % 2 == 0 else 0.62
        star.append((math.cos(ang) * r, math.sin(ang) * r))
    ditch.poly([(u + x * rx * 1.14, v + z * rz * 1.14 + h * 0.2) for x, z in star])
    for i in range(len(star)):
        x0, z0 = star[i]
        x1, z1 = star[(i + 1) % len(star)]
        b0, b1 = (u + x0 * rx, v + z0 * rz), (u + x1 * rx, v + z1 * rz)
        quad = [b0, b1, (b1[0], b1[1] - h), (b0[0], b0[1] - h)]
        # The outward normal of the face in plan: it faces the eye when it
        # points down the picture.
        nx, nz = z1 - z0, -(x1 - x0)
        if nz <= 0.0:
            continue
        (lit if nx < 0.0 else shaded).poly(quad)
    top.poly([(u + x * rx, v + z * rz - h) for x, z in star])


def _indiaman(hull: Pen, band: Pen, ports: Pen, rig: Pen, sails: Pen, u: float, v: float, s: float, facing: float = 1.0) -> None:
    """An East Indiaman at anchor: a tall black hull with a broad ochre band
    and a row of square gun ports, a high stern with windows, three masts
    with their yards across them and the sails furled on the yards, a long
    bowsprit, and the stays from the mast heads. `s` is its length and
    `(u, v)` the middle of its waterline."""
    f = facing

    def at(x: float, y: float) -> tuple[float, float]:
        return (u + f * x * s, v - y * s)

    hull.poly([at(-0.50, 0.21), at(-0.48, 0.10), at(-0.42, 0.0), at(0.36, 0.0), at(0.45, 0.07), at(0.52, 0.17), at(0.40, 0.155), at(-0.40, 0.17)])
    hull.poly([at(-0.52, 0.27), at(-0.36, 0.27), at(-0.36, 0.16), at(-0.50, 0.16)])
    band.poly([at(-0.48, 0.115), at(0.47, 0.105), at(0.48, 0.125), at(-0.49, 0.140)])
    for k in range(9):
        x = -0.36 + k * 0.088
        y = 0.122 - (x + 0.48) * 0.011
        ports.rect(*at(x - 0.014, y + 0.010), *at(x + 0.014, y - 0.010))
    rig.line([at(0.46, 0.15), at(0.82, 0.30)], s * 0.012)
    masts = ((-0.28, 0.80), (0.04, 1.00), (0.30, 0.82))
    for x, h in masts:
        rig.line([at(x, 0.15), at(x, h)], s * 0.013)
        for j in range(3):
            y = h - 0.06 - j * 0.21
            wide = 0.10 + j * 0.035
            rig.line([at(x - wide, y), at(x + wide, y)], s * 0.007)
            sails.poly([at(x - wide * 0.92, y), at(x + wide * 0.92, y), at(x + wide * 0.80, y - 0.024), at(x - wide * 0.80, y - 0.024)])
    rig.line([at(0.04, 1.0), at(0.82, 0.30)], s * 0.004)
    rig.line([at(0.30, 0.82), at(0.70, 0.26)], s * 0.004)
    rig.line([at(0.04, 1.0), at(-0.28, 0.80)], s * 0.004)
    rig.line([at(-0.28, 0.80), at(-0.50, 0.27)], s * 0.004)


def _company_house(wall: Pen, gaps: Pen, roof: Pen, rng, u: float, v: float, w: float, h: float) -> None:
    """A house of the Company on the bank, white with lime plaster: a plain
    block on a low plinth, a tall colonnade across its front (the dark
    spaces between the columns show the deep veranda behind), a flat roof
    with a parapet, and on some a pediment over the middle of the
    colonnade."""
    x0, x1 = u - w * 0.5, u + w * 0.5
    wall.rect(x0, v - h, x1, v + 0.002)
    roof.rect(x0 - w * 0.02, v - h - h * 0.08, x1 + w * 0.02, v - h + h * 0.04)
    count = max(4, int(round(w / (h * 0.22))))
    pitch = (w * 0.86) / count
    start = x0 + w * 0.07
    for k in range(count):
        gx = start + k * pitch + pitch * 0.30
        gaps.rect(gx, v - h * 0.78, gx + pitch * 0.55, v - h * 0.12)
    if rng.random() < 0.55:
        pw = w * 0.30
        wall.poly([(u - pw, v - h * 0.80), (u + pw, v - h * 0.80), (u, v - h * 1.08)])
        roof.line([(u - pw, v - h * 0.80), (u, v - h * 1.08), (u + pw, v - h * 0.80)], h * 0.05)


def history_calcutta(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = CALCUTTA
    shore = CALCUTTA_SHORE
    if layer_key == "sky":
        # A heavy sky of the monsoon: high dark cloud over all of it, a
        # lower bank with its lit tops, curtains of rain far off, and a pale
        # bright band low over the river where the light comes under the
        # cloud.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.85)), (0.30, p["top"]), (0.50, p["mid"]), (HORIZON - 0.02, mix(p["low"], p["mid"], 0.25)), (HORIZON - 0.004, p["low"]),
                                 (HORIZON + 0.002, mix(p["river"], p["low"], 0.45)), (1.0, mix(p["river"], p["low"], 0.25))]))
        # The high overcast: soft dark lumps, a little lighter on their tops.
        lumps = a.noise("calcutta overcast", cells=4.0, octaves=5, stretch=3.0)
        cover = smoothstep(0.30, 0.70, lumps) * smoothstep(0.56, 0.30, a.v)
        a.put(layer, cover, p["cloud_dark"], 0.70)
        a.light(layer, cover * smoothstep(0.55, 0.85, a.noise("calcutta overcast light", cells=6.0, octaves=4, stretch=2.5)), p["cloud"], 0.25)
        # The rain clouds over the river: a low dark shelf with a ragged
        # base, lighter where its billows catch the light under it, and
        # curtains of rain that fall from its base.
        # The base hangs down in soft round rolls, not in points.
        rolls = a.line_noise("calcutta shelf base", cells=6.0, octaves=2)
        base = (0.492 + np.sqrt(rolls) * 0.030).astype(np.float32)
        shelf = np.clip((base[None, :] - a.v) / 0.016, 0.0, 1.0) * smoothstep(0.30, 0.42, a.v)
        billows = a.noise("calcutta billows", cells=9.0, octaves=4, stretch=2.5)
        a.put(layer, shelf, scale(p["cloud_dark"], 0.92), 0.92)
        a.light(layer, shelf * smoothstep(0.50, 0.80, billows) * smoothstep(0.38, 0.47, a.v), p["cloud"], 0.35)
        a.shade(layer, shelf * np.clip(1.0 - (base[None, :] - a.v) / 0.012, 0.0, 1.0), 0.18)
        for k, (u0, u1, lean) in enumerate(((0.18, 0.40, 0.30), (0.60, 0.86, 0.25), (0.93, 1.06, 0.35))):
            rain = _rain(a, ("calcutta rain", k), u0, u1, 0.48, HORIZON, lean) * np.clip((a.v - base[None, :]) / 0.03, 0.0, 1.0)
            a.tint(layer, rain, p["rain"], 0.42)
        a.light(layer, a.band(HORIZON - 0.012, 0.030, 1.5), p["glow"], 0.25)
        far, _ = a.ridge("calcutta far trees", HORIZON - 0.003, 0.002, cells=70.0, octaves=3)
        far = far * smoothstep(HORIZON + 0.004, HORIZON + 0.001, a.v)
        a.put(layer, far, mix(p["land"], p["low"], 0.62))
        a.tint(layer, fog(a, "calcutta horizon mist", HORIZON - 0.003, 0.012, 3.0), p["low"], 0.45)
        _textbook(a, layer, 0.07)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far calcutta")
        # The far shore, the Howrah side: a low strip with trees and palms.
        far_top = (HORIZON - 0.003 - (a.line_noise("calcutta far bank", cells=24.0, octaves=2) - 0.5) * 0.0015).astype(np.float32)
        far_land = _land(a, far_top) * smoothstep(shore + 0.0015, shore - 0.0005, a.v)
        far_trees, far_tree_pen = a.drawing()
        u = -0.02
        while u < 1.02:
            base = _at(far_top, max(0.0, min(0.999, u))) + 0.002
            if rng.random() < 0.4:
                _palm(far_tree_pen, far_tree_pen, rng, u, base + 0.002, rng.uniform(0.014, 0.024), rng.uniform(-0.2, 0.2))
            else:
                _lumpy_crown(far_tree_pen, rng, u, base - 0.004, rng.uniform(0.008, 0.014), rng.uniform(0.004, 0.007), 10)
            u += rng.uniform(0.012, 0.030)
        # The near bank at the left, with Fort William on it.
        left_bank, left_pen = a.drawing()
        left_pen.poly([(-0.02, 0.604), (0.34, 0.604), (0.40, 0.630), (0.44, 0.660), (-0.02, 0.664)])
        fort = {key: a.drawing() for key in ("ditch", "top", "lit", "shaded")}
        fort_u, fort_v = 0.18, 0.636
        _star_fort(fort["ditch"][1], fort["top"][1], fort["lit"][1], fort["shaded"][1], fort_u, fort_v, 0.17, 0.026, 0.013)
        barracks = {key: a.drawing() for key in ("wall", "gaps", "roof")}
        for bu, bv, bw in ((0.12, 0.622, 0.05), (0.21, 0.620, 0.06), (0.16, 0.630, 0.04)):
            _company_house(barracks["wall"][1], barracks["gaps"][1], barracks["roof"][1], rng, bu, bv, bw, 0.010)
        fort_trees, fort_tree_pen = a.drawing()
        for bu, bv in ((0.07, 0.622), (0.27, 0.624), (0.30, 0.614)):
            _lumpy_crown(fort_tree_pen, rng, bu, bv - 0.008, 0.014, 0.008, 12)
        # The near bank at the right: the quay and the steps of a ghat, and
        # the white houses of the Company in a row along it, with palms.
        right_bank, right_pen = a.drawing()
        right_pen.poly([(0.60, 0.626), (1.02, 0.624), (1.02, 0.660), (0.57, 0.662), (0.585, 0.640)])
        ghat, ghat_pen = a.drawing()
        ghat_pen.poly([(0.585, 0.640), (1.02, 0.639), (1.02, 0.660), (0.57, 0.662)])
        town = {key: a.drawing() for key in ("wall", "gaps", "roof")}
        for row_v, hs in ((0.622, (0.045, 0.060)), (0.640, (0.030, 0.046))):
            x = 0.61 if row_v > 0.63 else 0.63
            while x < 1.03:
                w = rng.uniform(0.05, 0.09)
                if row_v > 0.63 and rng.random() < 0.25:
                    x += w * 0.6
                    continue
                _company_house(town["wall"][1], town["gaps"][1], town["roof"][1], rng, x + w * 0.5, row_v, w, rng.uniform(*hs))
                x += w + rng.uniform(0.004, 0.012)
        palms, palm_pen = a.drawing()
        trunks, trunk_pen = a.drawing()
        for pu, pv, h in ((0.605, 0.640, 0.060), (0.70, 0.641, 0.050), (0.835, 0.640, 0.064), (0.955, 0.640, 0.054), (0.38, 0.632, 0.050), (0.03, 0.640, 0.046)):
            _palm(trunk_pen, palm_pen, rng, pu, pv, h, rng.uniform(-0.18, 0.18))
        # The ships at anchor, the big ones near, and small boats.
        ships = []
        for su, sv, s, f in ((0.47, 0.617, 0.050, 1.0), (0.33, 0.664, 0.110, 1.0), (0.52, 0.682, 0.170, -1.0), (0.81, 0.676, 0.105, -1.0)):
            pens = {key: a.drawing() for key in ("hull", "band", "ports", "rig", "sails")}
            _indiaman(pens["hull"][1], pens["band"][1], pens["ports"][1], pens["rig"][1], pens["sails"][1], su, sv, s, f)
            ships.append((sv, {key: a.mask_of(img) for key, (img, _) in pens.items()}))
        boats = []
        for bu, bv, s, f in ((0.66, 0.668, 0.045, 1.0), (0.44, 0.640, 0.030, -1.0), (0.93, 0.668, 0.040, -1.0)):
            pens = {key: a.drawing() for key in ("hull", "roof", "sail", "rig")}
            _country_boat(pens["hull"][1], pens["roof"][1], pens["sail"][1], pens["rig"][1], bu, bv, s, f, False)
            boats.append((bv, {key: a.mask_of(img) for key, (img, _) in pens.items()}))
        far_tree_mask = a.mask_of(far_trees)
        left_mask = a.mask_of(left_bank)
        right_mask = a.mask_of(right_bank)
        ghat_mask = a.mask_of(ghat)
        fm = {key: a.mask_of(img) for key, (img, _) in fort.items()}
        bm_ = {key: a.mask_of(img) for key, (img, _) in barracks.items()}
        tm = {key: a.mask_of(img) for key, (img, _) in town.items()}
        fort_tree_mask = a.mask_of(fort_trees)
        palm_mask = a.mask_of(palms)
        trunk_mask = a.mask_of(trunks)
        walls_mask = np.maximum(fm["lit"], fm["shaded"])
        fort_mask = np.maximum.reduce([fm["top"], walls_mask])
        town_mask = np.maximum.reduce([tm["wall"], tm["roof"]])
        barrack_mask = np.maximum(bm_["wall"], bm_["roof"])
        ship_mask = np.maximum.reduce([np.maximum.reduce(list(sm.values())) for _, sm in ships])
        boat_mask = np.maximum.reduce([np.maximum.reduce(list(bm.values())) for _, bm in boats])
        land = np.maximum.reduce([far_land, far_tree_mask, left_mask, right_mask, fort_mask, barrack_mask, fort_tree_mask, town_mask, palm_mask, trunk_mask])
        water = smoothstep(shore - 0.002, shore + 0.001, a.v) * (1.0 - np.maximum(left_mask, right_mask))
        mask = np.maximum.reduce([land, water, ship_mask, boat_mask])
        layer = solid(a, mask, mix(p["land"], p["far"], 0.45), p["land"], HORIZON, 0.70, "calcutta far", 0.03)
        # The Hooghly: grey-brown under the grey sky, pale near the far
        # shore, with short broken waves and the pictures of the ships.
        a.put(layer, water, a.ramp([(0.0, mix(p["river_light"], p["low"], 0.35)), (shore, mix(p["river_light"], p["low"], 0.35)),
                                     (0.64, mix(p["river"], p["river_light"], 0.35)), (0.70, p["river"]), (1.0, p["river_deep"])]))
        for k, (sv, sm) in enumerate(ships):
            body = np.maximum.reduce(list(sm.values()))
            a.put(layer, _reflected(a, body, sv + 0.0005, f"calcutta ship ripple {k}", water * (1.0 - ship_mask)), mix(p["hull"], p["river"], 0.45), 0.45)
        a.put(layer, _reflected(a, town_mask * (a.v < 0.641), 0.660, "calcutta town ripple", water), mix(p["white"], p["river"], 0.45), 0.35)
        chop = smoothstep(0.60, 0.82, a.noise("calcutta chop", cells=120.0, octaves=2, stretch=8.0))
        a.light(layer, water * chop * smoothstep(shore + 0.01, shore + 0.06, a.v), p["river_light"], 0.30)
        a.shade(layer, water * smoothstep(0.65, 0.85, a.noise("calcutta chop dark", cells=100.0, octaves=2, stretch=8.0)), 0.10)
        # The far shore.
        a.put(layer, far_land, mix(p["land"], p["far"], 0.45))
        a.put(layer, far_tree_mask, mix(p["palm"], p["far"], 0.45))
        # Fort William: its ditch, the brick faces of its walls (lit on the
        # faces to the left), the grass of its ramparts on top, and in it
        # white barracks and trees.
        a.put(layer, left_mask, mix(p["glacis"], p["far"], 0.20))
        a.put(layer, left_mask * smoothstep(0.645, 0.662, a.v), mix(p["laterite"], p["river_deep"], 0.35), 0.75)
        a.put(layer, fm["ditch"] * left_mask, mix(p["ditch"], p["river"], 0.35))
        a.light(layer, a.rim(fm["ditch"], 0.0, -0.0015, 0.0) * fm["ditch"], p["river_light"], 0.30)
        a.put(layer, fm["shaded"], scale(p["rampart"], 0.78))
        a.put(layer, fm["lit"], p["rampart"])
        a.light(layer, fm["lit"] * smoothstep(0.6, 0.0, a.rim(fm["lit"], 0.0, 0.0015, 0.0)), p["rampart_light"], 0.20)
        courses = np.clip(1.0 - np.abs(((a.v / 0.0018) % 1.0) - 0.5) / 0.12, 0.0, 1.0)
        a.shade(layer, walls_mask * courses, 0.10)
        a.put(layer, fm["top"], p["glacis"])
        a.light(layer, fm["top"] * smoothstep(0.55, 0.78, a.noise("calcutta glacis", cells=50.0, octaves=2)), p["glacis_light"], 0.25)
        a.light(layer, a.rim(fm["top"], 0.0, 0.0015, 0.0) * fm["top"], p["glacis_light"], 0.55)
        a.put(layer, fort_tree_mask, mix(p["palm"], p["far"], 0.25))
        a.light(layer, a.rim(fort_tree_mask, 0.002, 0.002, 0.3) * fort_tree_mask, p["palm_light"], 0.35)
        a.put(layer, bm_["wall"], mix(p["white"], p["far"], 0.20))
        a.put(layer, bm_["gaps"] * bm_["wall"], mix(p["colonnade"], p["far"], 0.30))
        a.put(layer, bm_["roof"], mix(p["parapet"], p["far"], 0.25))
        # The bank at the right: the quay, and the pale stone steps of the
        # ghat that go down to the water in many fine lines.
        a.put(layer, right_mask, mix(p["laterite"], p["far"], 0.30))
        a.put(layer, ghat_mask * right_mask, p["steps"])
        a.shade(layer, ghat_mask * right_mask * np.clip(1.0 - np.abs((((a.v - 0.640) / 0.0024) % 1.0) - 0.5) / 0.14, 0.0, 1.0), 0.28)
        a.put(layer, ghat_mask * right_mask * smoothstep(0.654, 0.660, a.v), mix(p["steps"], p["river_deep"], 0.5), 0.6)
        # The houses of the Company: white, a little grey in the wet air,
        # lit on the faces to the left, with dark colonnades.
        a.put(layer, tm["wall"], mix(p["white"], p["far"], 0.15))
        a.shade(layer, tm["wall"] * smoothstep(0.55, 0.80, a.noise("calcutta damp", cells=40.0, octaves=3)), 0.10)
        a.put(layer, tm["gaps"] * tm["wall"], mix(p["colonnade"], p["far"], 0.20))
        a.shade(layer, tm["gaps"] * tm["wall"] * smoothstep(0.3, 1.0, (a.v * 400.0) % 1.0), 0.15)
        a.put(layer, tm["roof"], mix(p["parapet"], p["far"], 0.15))
        a.light(layer, a.rim(tm["wall"], 0.002, 0.0, 0.0) * tm["wall"], (255, 252, 240), 0.45)
        a.shade(layer, a.rim(tm["wall"], -0.002, 0.0, 0.0) * tm["wall"], 0.20)
        a.put(layer, trunk_mask, mix(p["trunk"], p["far"], 0.20))
        a.put(layer, palm_mask, mix(p["palm"], p["far"], 0.15))
        a.light(layer, a.rim(palm_mask, 0.0015, 0.0015, 0.0) * palm_mask, p["palm_light"], 0.40)
        # The ships: black hulls with an ochre band and dark ports, sails
        # furled pale on the yards, and the rigging dark.
        for sv, sm in ships:
            a.put(layer, sm["hull"], p["hull"])
            a.put(layer, sm["band"] * sm["hull"], p["band"])
            a.put(layer, sm["ports"] * sm["band"], p["hull"], 0.9)
            a.light(layer, a.rim(sm["hull"], 0.0, 0.0015, 0.0) * sm["hull"], p["river_light"], 0.35)
            a.put(layer, sm["rig"], p["rig"])
            a.put(layer, sm["sails"], p["sail"])
            a.shade(layer, sm["sails"] * smoothstep(0.4, 1.0, a.rim(sm["sails"], 0.0, -0.002, 0.0)), 0.25)
        for bv, bm in boats:
            a.put(layer, bm["roof"], mix(p["sail"], p["trunk"], 0.45))
            a.put(layer, bm["hull"], mix(p["hull"], p["trunk"], 0.5))
            a.put(layer, bm["rig"], p["rig"])
        a.tint(layer, fog(a, "calcutta river mist", shore + 0.004, 0.012, 3.0) * mask, p["low"], 0.40)
        rain = _rain(a, "calcutta near rain", 0.62, 0.90, 0.40, 0.70, 0.25)
        a.tint(layer, rain * mask, p["rain"], 0.18)
        haze(a, layer, mix(p["low"], p["mid"], 0.4), 0.10, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near calcutta")
        bank, ground, bank_at = _bank(a, "near calcutta", 0.032, 0.020)
        bark, bark_pen = a.drawing()
        roots, root_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        indigo, indigo_pen = a.drawing()
        flowers, flower_pen = a.drawing()
        grass, grass_pen = a.drawing()
        # The banyan at the left: a thick trunk of many grown-together
        # stems, a long limb that goes out to the right, and from the limb
        # its aerial roots: some reach the ground and are trunks of their
        # own, some still hang in the air.
        foot = bank_at(0.07) + 0.006
        bark_pen.poly([(0.020, foot), (0.125, foot), (0.105, 0.47), (0.085, 0.40), (0.050, 0.40), (0.035, 0.47)])
        limb = _arch((0.08, 0.43), (0.18, 0.37), (0.32, 0.395), 14)
        for i in range(len(limb) - 1):
            bark_pen.line([limb[i], limb[i + 1]], 0.026 * (1.0 - 0.6 * i / len(limb)))
        bark_pen.line(_arch((0.06, 0.42), (0.01, 0.38), (-0.03, 0.40), 8), 0.020)
        for i, (x, y) in enumerate(limb[3:]):
            for j in range(1 + i % 2):
                rx = x + rng.uniform(-0.008, 0.008)
                if (i + j) % 4 == 1:
                    end = bank_at(rx) + 0.004
                    root_pen.line(_arch((rx, y), (rx + rng.uniform(-0.006, 0.006), (y + end) * 0.5), (rx + rng.uniform(-0.01, 0.01), end), 8), rng.uniform(0.003, 0.006))
                else:
                    end = y + rng.uniform(0.06, 0.20)
                    root_pen.line(_arch((rx, y), (rx + rng.uniform(-0.004, 0.004), (y + end) * 0.5), (rx + rng.uniform(-0.008, 0.008), end), 8), rng.uniform(0.0012, 0.0024))
        for cx, cy, rx_, ry_ in ((0.06, 0.37, 0.10, 0.05), (0.18, 0.345, 0.09, 0.040), (0.29, 0.37, 0.06, 0.030)):
            crown_pen.ellipse(cx, cy + ry_ * 0.1, rx_ * 0.80, ry_ * 0.65)
            _lumpy_crown(crown_pen, rng, cx, cy, rx_, ry_, 220)
        # The indigo at the right: small bushes of fine leaves, each with a
        # few short spikes of pink-purple flowers.
        for u in np.arange(0.70, 1.01, 0.034):
            u = float(u) + rng.uniform(-0.008, 0.008)
            base = bank_at(u) + 0.004
            h = rng.uniform(0.035, 0.060)
            for _ in range(7):
                tip = (u + rng.uniform(-0.022, 0.022), base - h * rng.uniform(0.6, 1.0))
                stem = _arch((u, base), (u + (tip[0] - u) * 0.3, base - h * 0.6), tip, 8)
                indigo_pen.line(stem, 0.0014)
                for x, y in stem[3:]:
                    indigo_pen.ellipse(x - 0.0035, y, 0.0035, 0.0018)
                    indigo_pen.ellipse(x + 0.0035, y - 0.001, 0.0035, 0.0018)
                if rng.random() < 0.5:
                    flower_pen.line([tip, (tip[0] + 0.002, tip[1] - 0.012)], 0.0030)
        for _ in range(14):
            u = rng.uniform(0.34, 0.68)
            _grass_blades(grass_pen, rng, u, bank_at(u) + 0.002, rng.uniform(0.008, 0.016), 6, 0.0012, 0.010)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        bark_mask = a.mask_of(bark)
        root_mask = a.mask_of(roots) * (1.0 - bark_mask)
        crown_mask = a.mask_of(crowns)
        indigo_mask = a.mask_of(indigo)
        flower_mask = a.mask_of(flowers)
        grass_mask = a.mask_of(grass)
        mask = np.maximum.reduce([bank_mask, bark_mask, root_mask, crown_mask, indigo_mask, flower_mask, grass_mask])
        layer = a.blank()
        soil = mix(p["laterite"], p["glacis"], 0.40)
        earth = a.ramp([(0.0, mix(soil, p["near"], 0.50)), (0.66, mix(soil, p["near"], 0.50)), (0.80, mix(soil, p["near"], 0.78)), (1.0, p["near"])])
        a.put(layer, bank_mask, earth)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.20)
        a.put(layer, grass_mask, mix(p["glacis"], p["near"], 0.40))
        # The banyan: grey-brown bark, lit on the left, with long furrows;
        # the roots paler; the crown dark and dense.
        a.put(layer, root_mask, mix(p["bark_light"], p["near"], 0.45))
        a.put(layer, bark_mask, mix(p["bark"], p["near"], 0.40))
        a.shade(layer, bark_mask * smoothstep(0.45, 0.75, a.noise("calcutta bark", cells=240.0, octaves=1, stretch=0.08)), 0.30)
        a.light(layer, a.rim(np.maximum(bark_mask, root_mask), 0.003, 0.0, 0.3) * np.maximum(bark_mask, root_mask), p["bark_light"], 0.35)
        a.put(layer, crown_mask, mix(p["banyan"], p["near"], 0.35))
        a.light(layer, crown_mask * smoothstep(0.55, 0.78, a.noise("calcutta crown", cells=80.0, octaves=2)), mix(p["banyan_light"], p["near"], 0.3), 0.30)
        a.light(layer, a.rim(crown_mask, 0.003, 0.004, 0.4) * crown_mask, p["banyan_light"], 0.35)
        # The indigo: blue-green leaves and pink-purple spikes.
        a.put(layer, indigo_mask, mix(p["indigo"], p["near"], 0.30))
        a.light(layer, a.rim(indigo_mask, 0.0015, 0.0015, 0.0) * indigo_mask, p["indigo_light"], 0.35)
        a.put(layer, flower_mask, mix(p["indigo_flower"], p["near"], 0.15))
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.18)
        haze(a, layer, mix(p["low"], p["mid"], 0.5), 0.10, None)
        return layer
    layer = _air(a, p, "calcutta wet air", mix(p["low"], p["mid"], 0.5), 0.30, scale(p["near"], 0.8), 0.18)
    a.put(layer, _rain(a, "calcutta air rain", 0.55, 1.05, 0.10, 0.80, 0.22), p["rain"], 0.10)
    return layer


def calcutta_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Aerial roots of a banyan hang from above at two places, a few thin
    strands each from a limb out of view. A clump of indigo stands from
    below at one place."""
    del layer_lights
    rng = art_.rand("calcutta foreground")
    for k in range(2):
        u0 = 0.12 + (k + rng.uniform(0.2, 0.8)) * 0.38
        pen.line(_arch((u0 - 0.08, 0.0), (u0, 0.04), (u0 + 0.08, 0.02), 10), 0.006)
        for _ in range(6):
            x = u0 + rng.uniform(-0.05, 0.05)
            end = rng.uniform(0.30, 0.385)
            drift = rng.uniform(-0.008, 0.008)
            pen.line(_arch((x, 0.02), (x + drift * 0.3, end * 0.5), (x + drift, end), 10), rng.uniform(0.0012, 0.0026))
            pen.ellipse(x + drift, end, 0.0018, 0.003)
    u = rng.uniform(0.44, 0.56)
    for _ in range(9):
        x = u + rng.uniform(-0.016, 0.016)
        tip = (x + rng.uniform(-0.01, 0.01), REST_BOTTOM - rng.uniform(-0.004, 0.010))
        stem = _arch((x, 1.0), (x, tip[1] + 0.10), tip, 10)
        pen.line(stem, 0.0016)
        for sx, sy in stem[6:]:
            pen.ellipse(sx - 0.004, sy, 0.004, 0.0018)
            pen.ellipse(sx + 0.004, sy - 0.001, 0.004, 0.0018)


# ---------------------------------------------------------------------------
# Dhaka in spring: the university quarter in February
# ---------------------------------------------------------------------------


DHAKA_SPRING = {
    "top": (104, 156, 204),
    "mid": (180, 208, 224),
    "low": (238, 234, 216),
    "glow": (255, 236, 192),
    "sun": (255, 250, 232),
    "cloud": (250, 250, 246),
    "cloud_shadow": (196, 206, 218),
    "trees": (68, 110, 62),
    "trees_light": (148, 176, 92),
    "trees_dark": (40, 74, 46),
    "brick": (180, 72, 52),
    "brick_light": (226, 132, 96),
    "brick_dark": (112, 44, 34),
    "stone": (236, 226, 202),
    "arch_dark": (70, 40, 34),
    "lawn": (112, 152, 72),
    "lawn_light": (176, 198, 104),
    "road": (150, 140, 126),
    "path": (176, 112, 86),
    "bark": (118, 100, 88),
    "bark_light": (184, 166, 146),
    "shimul": (214, 42, 34),
    "shimul_light": (246, 110, 76),
    "rickshaw": ((222, 70, 58), (60, 124, 184), (232, 182, 60), (70, 150, 96)),
    "rig": (50, 44, 40),
    "marigold": (240, 150, 32),
    "marigold_light": (252, 206, 84),
    "leaf": (70, 116, 58),
    "leaf_light": (140, 172, 92),
    "far": (214, 222, 224),
    "near": (36, 34, 28),
    "near_light": (140, 130, 96),
}

#: The foot of Curzon Hall, and the road in front of its lawn.
SPRING_HALL = 0.634
SPRING_ROAD = 0.656


def _curzon_hall(brick: Pen, trim: Pen, surround: Pen, holes: Pen, u: float, v: float, s: float) -> None:
    """Curzon Hall of the University of Dhaka, as it was built in 1904 in
    the Indo-Saracenic style: a central block of red brick with one great
    pointed arch in a tall frame, a slender turret at each corner with a
    small domed kiosk on it, and a long wing at each side with two storeys
    of pointed arches. Bands of pale stone run along it and frame the
    arches. `s` is the width of the central block."""
    hc = s * 0.42
    brick.rect(u - s * 0.5, v - hc, u + s * 0.5, v + 0.002)
    trim.rect(u - s * 0.30, v - hc * 0.94, u + s * 0.30, v + 0.002)
    _pointed_arch(surround, u, v + 0.002, s * 0.26, v - hc * 0.50, s * 0.15, 0.10)
    _pointed_arch(holes, u, v + 0.002, s * 0.21, v - hc * 0.48, s * 0.12, 0.12)
    # The parapet of the central block: small merlons, and a small kiosk
    # over the middle of the arch.
    m = s * 0.04
    x = u - s * 0.46
    while x < u + s * 0.47:
        brick.rect(x, v - hc - m * 1.2, x + m * 0.6, v - hc + 0.001)
        x += m * 1.3
    trim.rect(u - s * 0.5, v - hc - m * 0.1, u + s * 0.5, v - hc + m * 0.4)
    _chhatri(brick, u, v - hc - m * 1.0, s * 0.12)
    for side in (-1.0, 1.0):
        tu = u + side * s * 0.47
        brick.rect(tu - s * 0.05, v - hc * 1.30, tu + s * 0.05, v + 0.002)
        trim.rect(tu - s * 0.06, v - hc * 1.32, tu + s * 0.06, v - hc * 1.26)
        _chhatri(brick, tu, v - hc * 1.32, s * 0.11)
        # The wing: two storeys of arches under a parapet.
        w0, w1 = sorted((u + side * s * 0.52, u + side * s * 1.30))
        hw = hc * 0.68
        brick.rect(w0, v - hw, w1, v + 0.002)
        trim.rect(w0, v - hw - m * 0.1, w1, v - hw + m * 0.35)
        trim.rect(w0, v - hw * 0.52, w1, v - hw * 0.47)
        count = 6
        pitch = (w1 - w0) / count
        for k in range(count):
            cx = w0 + pitch * (k + 0.5)
            _pointed_arch(holes, cx, v + 0.001, pitch * 0.30, v - hw * 0.30, pitch * 0.18, 0.08)
            _pointed_arch(holes, cx, v - hw * 0.55, pitch * 0.24, v - hw * 0.76, pitch * 0.14, 0.08)
        x = w0 + m * 0.3
        while x < w1 - m * 0.3:
            brick.rect(x, v - hw - m * 1.0, x + m * 0.6, v - hw + 0.001)
            x += m * 1.3
        end = u + side * s * 1.30
        brick.rect(end - s * 0.04, v - hw * 1.30, end + s * 0.04, v + 0.002)
        _chhatri(brick, end, v - hw * 1.30, s * 0.09)


def _shimul(trunk: Pen, flowers: Pen, rng, u: float, v: float, h: float, bloom: float = 1.0) -> None:
    """A shimul, the red silk-cotton tree, in February: a tall straight
    trunk with a flared foot, and bare branches that stand out from it in
    level tiers, longer near the foot, each turned up at its end. The
    big red flowers sit along the branches before the leaves come."""
    w = h * 0.030
    trunk.poly([(u - w * 2.0, v + 0.003), (u + w * 2.0, v + 0.003), (u + w * 0.9, v - h * 0.10), (u + w * 0.35, v - h), (u - w * 0.35, v - h), (u - w * 0.9, v - h * 0.10)])
    tiers = 6
    for k in range(tiers):
        t = 0.30 + 0.66 * k / (tiers - 1)
        y = v - h * t
        for side in (-1.0, 1.0):
            reach = h * (0.40 - 0.28 * (k / (tiers - 1))) * rng.uniform(0.8, 1.1)
            tip = (u + side * reach, y - reach * 0.30)
            branch = _arch((u, y), (u + side * reach * 0.6, y + reach * 0.02), tip, 10)
            trunk.line(branch, w * (0.55 - 0.25 * k / tiers))
            for x, yy in branch[3::2]:
                trunk.line([(x, yy), (x + side * reach * 0.10, yy - reach * 0.18)], w * 0.22)
                if rng.random() < bloom:
                    flowers.ellipse(x + side * reach * 0.10, yy - reach * 0.18, h * 0.014, h * 0.012)
                if rng.random() < bloom * 0.7:
                    flowers.ellipse(x, yy - h * 0.008, h * 0.012, h * 0.010)
            flowers.ellipse(tip[0], tip[1] - h * 0.006, h * 0.015, h * 0.012)


def _rickshaw(frame: Pen, hood: Pen, u: float, v: float, s: float, facing: float = 1.0) -> None:
    """A cycle rickshaw far off: a big rear wheel under a seat with a
    folding hood, a frame forward to the small front wheel, and the man
    who pedals it on his saddle. `(u, v)` is where the wheels meet the
    road, and `s` its length."""
    f = facing

    def at(x: float, y: float) -> tuple[float, float]:
        return (u + f * x * s, v - y * s)

    frame.ring(*at(-0.20, 0.22), s * 0.22, s * 0.05)
    frame.ring(*at(0.42, 0.17), s * 0.17, s * 0.05)
    frame.line([at(-0.20, 0.22), at(0.20, 0.40), at(0.42, 0.17)], s * 0.05)
    frame.rect(*at(-0.38, 0.52), *at(-0.02, 0.44))
    hood.poly([at(-0.40, 0.48)] + [at(-0.40 + 0.36 * math.sin(t), 0.48 + 0.42 * math.cos(t)) for t in np.linspace(0.0, math.pi * 0.42, 9)])
    frame.line([at(0.20, 0.40), at(0.24, 0.80)], s * 0.08)
    frame.ellipse(*at(0.26, 0.88), s * 0.07)
    frame.line([at(0.24, 0.66), at(0.42, 0.62)], s * 0.04)


def history_dhaka_spring(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = DHAKA_SPRING
    sun_at = (0.24, 0.30)
    hall_v = SPRING_HALL
    road_v = SPRING_ROAD
    if layer_key == "sky":
        # A clear morning of late winter: a pale clean blue, a few thin
        # high clouds, and the trees of the city on the horizon.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.90)), (0.28, p["top"]), (0.48, p["mid"]), (HORIZON - 0.01, p["low"]),
                                 (HORIZON + 0.002, mix(p["lawn"], p["low"], 0.55)), (1.0, mix(p["lawn"], p["low"], 0.40))]))
        _sun(a, layer, *sun_at, 0.020, p["sun"], p["glow"], 0.50)
        streaks = smoothstep(0.58, 0.82, a.noise("spring streaks", cells=5.0, octaves=3, stretch=12.0)) * a.band(0.36, 0.10, 1.2)
        a.light(layer, streaks, p["cloud"], 0.45)
        puffs = cloud_mask(a, "spring puffs", 0.50, 0.04, cells=7.0, cover=0.35, soft=0.12, stretch=2.4)
        a.put(layer, puffs, p["cloud"], 0.70)
        a.put(layer, puffs * a.band(0.52, 0.02), p["cloud_shadow"], 0.35)
        trees, _ = a.ridge("spring far trees", HORIZON - 0.010, 0.005, cells=50.0, octaves=3)
        trees = trees * smoothstep(HORIZON + 0.004, HORIZON + 0.001, a.v)
        a.put(layer, trees, mix(p["trees"], p["low"], 0.55))
        a.tint(layer, fog(a, "spring horizon haze", HORIZON - 0.004, 0.010, 3.0), p["low"], 0.40)
        _textbook(a, layer, 0.07)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far spring")
        # The campus: a lawn from the trees at the back to the road, Curzon
        # Hall in the middle, big trees at its sides and behind it, and the
        # shimul trees in flower at the left and the right.
        lawn_top = (HORIZON - 0.004 + (a.line_noise("spring lawn", cells=10.0, octaves=2) - 0.5) * 0.002).astype(np.float32)
        lawn = _land(a, lawn_top)
        back_trees, back_pen = a.drawing()
        for u in np.arange(-0.02, 1.03, 0.022):
            base = _at(lawn_top, max(0.0, min(0.999, float(u)))) + 0.004
            _lumpy_crown(back_pen, rng, float(u) + rng.uniform(-0.008, 0.008), base - rng.uniform(0.008, 0.016), rng.uniform(0.016, 0.026), rng.uniform(0.010, 0.016), 14)
        trees, tree_pen = a.drawing()
        tree_trunks, tree_trunk_pen = a.drawing()
        for u, base, r in ((0.22, 0.640, 0.040), (0.28, 0.630, 0.032), (0.72, 0.630, 0.034), (0.79, 0.642, 0.042), (0.36, 0.622, 0.024), (0.64, 0.622, 0.024)):
            tree_trunk_pen.line([(u, base), (u, base - r * 1.3)], 0.004)
            _lumpy_crown(tree_pen, rng, u, base - r * 1.5, r, r * 0.80, 90)
            tree_pen.ellipse(u, base - r * 1.5, r * 0.75, r * 0.6)
        hall = {key: a.drawing() for key in ("brick", "trim", "surround", "holes")}
        _curzon_hall(hall["brick"][1], hall["trim"][1], hall["surround"][1], hall["holes"][1], 0.50, hall_v, 0.13)
        shimul = {key: a.drawing() for key in ("trunk", "flowers")}
        for u, base, h in ((0.07, 0.668, 0.15), (0.13, 0.648, 0.10), (0.93, 0.666, 0.14), (0.86, 0.646, 0.09)):
            _shimul(shimul["trunk"][1], shimul["flowers"][1], rng, u, base, h)
        road, road_pen = a.drawing()
        road_pen.rect(-0.02, road_v - 0.005, 1.02, road_v + 0.004)
        path, path_pen = a.drawing()
        path_pen.poly([(0.485, hall_v), (0.515, hall_v), (0.53, road_v - 0.005), (0.47, road_v - 0.005)])
        hedge, hedge_pen = a.drawing()
        for x in np.arange(-0.02, 1.03, 0.006):
            if abs(float(x) - 0.50) > 0.035:
                hedge_pen.ellipse(float(x), road_v - 0.0065, 0.0045, 0.0028)
        riders = []
        for k, (ru, s, f) in enumerate(((0.30, 0.024, 1.0), (0.385, 0.022, 1.0), (0.60, 0.024, -1.0), (0.69, 0.022, -1.0), (0.97, 0.024, -1.0))):
            pens = {key: a.drawing() for key in ("frame", "hood")}
            _rickshaw(pens["frame"][1], pens["hood"][1], ru, road_v + 0.002, s, f)
            riders.append((k, {key: a.mask_of(img) for key, (img, _) in pens.items()}))
        back_mask = a.mask_of(back_trees)
        tree_mask = a.mask_of(trees)
        trunk_mask = a.mask_of(tree_trunks)
        hm = {key: a.mask_of(img) for key, (img, _) in hall.items()}
        hall_mask = np.maximum.reduce([hm["brick"], hm["trim"], hm["surround"]])
        sm = {key: a.mask_of(img) for key, (img, _) in shimul.items()}
        road_mask = a.mask_of(road)
        path_mask = a.mask_of(path)
        hedge_mask = a.mask_of(hedge)
        rider_mask = np.maximum.reduce([np.maximum.reduce(list(rm.values())) for _, rm in riders])
        mask = np.maximum.reduce([lawn, back_mask, tree_mask, trunk_mask, hall_mask, sm["trunk"], sm["flowers"], rider_mask])
        layer = solid(a, mask, mix(p["lawn"], p["far"], 0.45), p["lawn"], HORIZON, 0.70, "spring far", 0.03)
        # The lawn: cut in wide stripes, lit by the low sun.
        a.put(layer, lawn, a.ramp([(0.0, mix(p["lawn"], p["far"], 0.40)), (HORIZON, mix(p["lawn"], p["far"], 0.40)), (0.68, p["lawn"]), (1.0, mix(p["lawn"], p["near"], 0.3))]))
        mown = smoothstep(0.40, 0.60, a.noise("spring mown", cells=8.0, octaves=2, stretch=12.0))
        a.light(layer, lawn * mown * smoothstep(0.62, 0.66, a.v), p["lawn_light"], 0.12)
        a.put(layer, back_mask, mix(p["trees"], p["far"], 0.45))
        a.light(layer, a.rim(back_mask, 0.002, 0.002, 0.3) * back_mask, mix(p["trees_light"], p["far"], 0.3), 0.40)
        a.put(layer, path_mask, mix(p["path"], p["far"], 0.15))
        a.put(layer, road_mask, mix(p["road"], p["far"], 0.15))
        a.light(layer, road_mask * smoothstep(road_v - 0.004, road_v - 0.005, a.v), p["low"], 0.4)
        a.put(layer, hedge_mask, mix(p["trees_dark"], p["far"], 0.15))
        a.light(layer, a.rim(hedge_mask, 0.001, 0.001, 0.0) * hedge_mask, p["trees_light"], 0.40)
        # The trees of the campus: round dark crowns lit on their tops and
        # on the side to the sun.
        a.put(layer, trunk_mask, mix(p["bark"], p["far"], 0.20))
        a.put(layer, tree_mask, mix(p["trees"], p["far"], 0.25))
        a.light(layer, tree_mask * smoothstep(0.55, 0.78, a.noise("spring crowns", cells=90.0, octaves=2)), mix(p["trees_light"], p["far"], 0.2), 0.35)
        a.light(layer, a.rim(tree_mask, 0.003, 0.003, 0.4) * tree_mask, mix(p["trees_light"], p["glow"], 0.4), 0.50)
        a.shade(layer, a.rim(tree_mask, -0.003, -0.002, 0.6) * tree_mask, 0.15)
        # Curzon Hall: warm red brick, its stone bands and arch frames pale,
        # the arches dark, lit on the faces to the sun at the left.
        a.put(layer, hm["brick"], p["brick"])
        courses = np.clip(1.0 - np.abs((((a.v - hall_v) / 0.0016) % 1.0) - 0.5) / 0.10, 0.0, 1.0)
        a.shade(layer, hm["brick"] * courses, 0.10)
        a.put(layer, hm["trim"], p["stone"])
        a.shade(layer, a.rim(hm["trim"], 0.0, -0.001, 0.0) * hm["trim"], 0.25)
        a.put(layer, hm["surround"], mix(p["brick"], p["brick_light"], 0.25))
        a.light(layer, a.rim(hm["surround"], 0.0015, 0.0015, 0.0) * hm["surround"], p["brick_light"], 0.45)
        a.put(layer, hm["holes"] * hall_mask, p["arch_dark"])
        a.light(layer, hm["holes"] * hall_mask * smoothstep(hall_v - 0.004, hall_v, a.v), p["brick_light"], 0.25)
        a.light(layer, a.rim(hall_mask, 0.0025, 0.0, 0.0) * hall_mask, p["brick_light"], 0.55)
        a.light(layer, a.rim(hall_mask, 0.0, 0.0018, 0.0) * hall_mask, mix(p["brick_light"], p["glow"], 0.5), 0.45)
        a.shade(layer, a.rim(hall_mask, -0.0025, 0.0, 0.0) * hall_mask, 0.20)
        # The shimul trees: grey bark, the red flowers.
        a.put(layer, sm["trunk"], mix(p["bark"], p["far"], 0.15))
        a.light(layer, a.rim(sm["trunk"], 0.0015, 0.0, 0.0) * sm["trunk"], p["bark_light"], 0.45)
        a.put(layer, sm["flowers"], p["shimul"])
        a.light(layer, a.rim(sm["flowers"], 0.0015, 0.0015, 0.0) * sm["flowers"], p["shimul_light"], 0.60)
        # The rickshaws: dark frames, hoods of bright cloth.
        for k, rm in riders:
            a.put(layer, rm["frame"], p["rig"])
            a.put(layer, rm["hood"], p["rickshaw"][k % len(p["rickshaw"])])
            a.light(layer, a.rim(rm["hood"], 0.001, 0.001, 0.0) * rm["hood"], (255, 255, 240), 0.35)
        haze(a, layer, p["low"], 0.07, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near spring")
        bank, ground, bank_at = _bank(a, "near spring", 0.022, 0.030)
        tree = {key: a.drawing() for key in ("trunk", "flowers")}
        leaves, leaf_pen = a.drawing()
        heads, head_pen = a.drawing()
        grass, grass_pen = a.drawing()
        # A shimul at the left, its trunk with blunt thorns and its level
        # branches with red flowers; a bed of marigolds at the right.
        _shimul(tree["trunk"][1], tree["flowers"][1], rng, 0.07, bank_at(0.07) + 0.006, 0.42)
        for k in range(14):
            y = bank_at(0.07) - 0.02 - k * 0.025
            tree["trunk"][1].poly([(0.07 + 0.010, y), (0.07 + 0.017, y - 0.003), (0.07 + 0.010, y - 0.006)])
        for u in np.arange(0.72, 1.01, 0.016):
            u = float(u) + rng.uniform(-0.005, 0.005)
            base = bank_at(u) + 0.004
            h = rng.uniform(0.025, 0.050)
            top = (u + rng.uniform(-0.006, 0.006), base - h)
            leaf_pen.line(_arch((u, base), (u, base - h * 0.5), top, 6), 0.0016)
            for j in range(3):
                ly = base - h * (0.25 + j * 0.22)
                for side in (-1.0, 1.0):
                    _leaf(leaf_pen, [(u, ly), (u + side * 0.006, ly - 0.004), (u + side * 0.012, ly - 0.002)], 0.0022, 0.6)
            head_pen.ellipse(top[0], top[1], rng.uniform(0.0060, 0.0080), rng.uniform(0.0050, 0.0065))
        for _ in range(16):
            u = rng.uniform(0.24, 0.68)
            _grass_blades(grass_pen, rng, u, bank_at(u) + 0.002, rng.uniform(0.006, 0.011), 6, 0.0012, 0.008)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        tm = {key: a.mask_of(img) for key, (img, _) in tree.items()}
        leaf_mask = a.mask_of(leaves)
        head_mask = a.mask_of(heads)
        grass_mask = a.mask_of(grass)
        mask = np.maximum.reduce([bank_mask, tm["trunk"], tm["flowers"], leaf_mask, head_mask, grass_mask])
        layer = a.blank()
        earth = a.ramp([(0.0, mix(p["lawn"], p["near"], 0.40)), (0.66, mix(p["lawn"], p["near"], 0.40)), (0.80, mix(p["lawn"], p["near"], 0.75)), (1.0, p["near"])])
        a.put(layer, bank_mask, earth)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.30)
        a.put(layer, grass_mask, mix(p["lawn"], p["near"], 0.30))
        a.light(layer, a.rim(grass_mask, 0.0015, 0.0, 0.2) * grass_mask, p["lawn_light"], 0.30)
        a.put(layer, tm["trunk"], mix(p["bark"], p["near"], 0.40))
        a.shade(layer, tm["trunk"] * smoothstep(0.45, 0.75, a.noise("spring bark", cells=200.0, octaves=1, stretch=0.1)), 0.25)
        a.light(layer, a.rim(tm["trunk"], 0.003, 0.0, 0.3) * tm["trunk"], p["bark_light"], 0.40)
        a.put(layer, tm["flowers"], mix(p["shimul"], p["near"], 0.12))
        a.light(layer, a.rim(tm["flowers"], 0.002, 0.002, 0.0) * tm["flowers"], p["shimul_light"], 0.60)
        a.put(layer, leaf_mask, mix(p["leaf"], p["near"], 0.30))
        a.light(layer, a.rim(leaf_mask, 0.0015, 0.0015, 0.0) * leaf_mask, p["leaf_light"], 0.35)
        a.put(layer, head_mask, mix(p["marigold"], p["near"], 0.10))
        a.light(layer, a.rim(head_mask, 0.002, 0.002, 0.0) * head_mask, p["marigold_light"], 0.65)
        a.shade(layer, head_mask * smoothstep(0.5, 0.8, a.noise("spring marigold", cells=600.0, octaves=1)), 0.20)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.18)
        haze(a, layer, p["low"], 0.08, None)
        return layer
    layer = _air(a, p, "spring haze", p["low"], 0.20, scale(p["near"], 0.8), 0.12)
    a.put(layer, shafts(a, "spring shafts", 4, 0.12, 0.0, 0.85, 0.05), p["glow"], 0.08)
    return layer


def dhaka_spring_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """A twig of shimul with its red flowers hangs from above at two places.
    Marigolds on their stems stand from below at one place."""
    del layer_lights
    rng = art_.rand("dhaka spring foreground")
    for k in range(2):
        u0 = 0.12 + (k + rng.uniform(0.2, 0.8)) * 0.38
        twig = _arch((u0 - 0.06, 0.0), (u0, 0.22), (u0 + 0.07, 0.30), 12)
        pen.line(twig, 0.0034)
        for i in (5, 7, 9, 11):
            x, y = twig[i]
            end = (x + rng.uniform(-0.010, 0.020), min(0.372, y + rng.uniform(0.020, 0.060)))
            pen.line([(x, y), end], 0.0018)
            r = 0.010
            cy = min(end[1], 0.384 - r * 1.4)
            for j in range(5):
                pu, pv = polar(end[0], cy, r * 0.55, 90.0 + (j - 2) * 34.0)
                pen.ellipse(pu, pv, r * 0.45, r * 0.55)
    u = rng.uniform(0.44, 0.56)
    for j in range(5):
        x = u + (j - 2) * 0.012
        top = (x + rng.uniform(-0.005, 0.005), REST_BOTTOM - 0.002 - (j % 2) * 0.006)
        pen.line(_arch((x, 1.0), (x, top[1] + 0.10), top, 10), 0.0018)
        pen.ellipse(top[0], top[1] + 0.004, 0.009, 0.008)
        lv = top[1] + 0.036
        for s in (-1.0, 1.0):
            _leaf(pen, [(x, lv + 0.004), (x + s * 0.010, lv - 0.004), (x + s * 0.018, lv - 0.002)], 0.0040, 0.6)
