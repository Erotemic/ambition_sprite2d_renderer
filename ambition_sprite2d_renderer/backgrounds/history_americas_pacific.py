"""The scenes of the History dimension, third pass: the Americas and the
Pacific grow east.

The History dimension is a grid. East is later, and each floor is a region
of the world. These six rooms carry the floor of the Americas and the floor
of Oceania on to the medieval column. They use the same sepia of an old
textbook and the same rules as `history_eras.py` and `history_origins.py`.
The people of these places show skill, invention and age; nothing here is a
joke on them.

- ``history_olmec`` (the Gulf coast of Mexico, 1,200 BCE). A humid, hazy
  morning over the lowlands. A slow brown river winds through swamp forest,
  a mound of clay stands on the plain, the blue Tuxtla mountains (where the
  basalt came from) are far off, and a colossal head of basalt stands half
  in the grass. Cacao and palms at the sides.
- ``history_maya`` (the Maya lowlands, 250-900 CE). A misty morning. Stepped
  temple pyramids with white roof combs rise over the rainforest canopy, and
  a ballcourt lies in a clearing. A ceiba and lianas at the sides.
- ``history_caribbean`` (the Taino islands, 1000-1492 CE). A bright noon. A
  turquoise sea and white sand, green mountains with cloud on their tops,
  round bohios of cane and thatch under royal palms, and a dugout canoe on
  the water.
- ``history_lapita`` (the western Pacific, 1,500 BCE). A gold late
  afternoon over a lagoon. Houses on stilts over the water, a reef line of
  white surf, volcanic islands, and outrigger canoes with crab-claw sails.
- ``history_open_ocean`` (the open Pacific). Dusk at sea: long swells, a sky
  that goes from orange to deep blue with the first stars, a far island under
  its cloud, and frigatebirds. There is no land near: the near layer is the
  sea.
- ``history_rapa_nui`` (Rapa Nui, 1200-1600 CE). A wide, windy sky over
  rolling grassland. The crater of Rano Raraku with moai on its slope, a line
  of moai on an ahu that face inland with their backs to the sea, and sea
  cliffs.

The bright detail is far off or at the edges, and the middle of each near
layer is calm, so the play in front of it reads. The things that drift in the
air are the room's motes (`terrain/motes.py`), not part of these pictures.
"""

from __future__ import annotations

import math

import numpy as np

from .artkit import Art, Pen, mix, polar, scale, smoothstep
from .history_eras import REST_BOTTOM, _air, _at, _heaps, _plume, _reeds, _sun, _textbook
from .history_origins import _arch, _banana, _land, _leaf
from .parts import HORIZON, cloud_mask, fog, haze, shafts, solid, stars, vignette

OLMEC = {
    "top": (78, 120, 146),
    "mid": (160, 186, 184),
    "low": (238, 228, 196),
    "glow": (255, 236, 196),
    "sun": (255, 248, 226),
    "cloud": (246, 244, 236),
    "cloud_shadow": (170, 182, 182),
    "tuxtla": (110, 140, 146),
    "river": (150, 120, 82),
    "river_light": (240, 222, 180),
    "plain": (150, 164, 90),
    "forest": (58, 92, 60),
    "forest_light": (104, 140, 80),
    "clay": (176, 120, 80),
    "basalt": (84, 84, 86),
    "pod": (200, 110, 50),
    "far": (150, 170, 156),
    "near": (28, 40, 26),
    "near_light": (120, 140, 70),
}

MAYA = {
    "top": (62, 108, 140),
    "mid": (150, 190, 190),
    "low": (244, 232, 204),
    "sun": (255, 246, 220),
    "glow": (255, 226, 170),
    "mist": (236, 240, 230),
    "canopy": (44, 96, 64),
    "canopy_light": (96, 150, 86),
    "stone": (220, 210, 186),
    "stone_shadow": (150, 140, 124),
    "red": (176, 64, 46),
    "comb": (244, 240, 226),
    "macaw": (210, 50, 40),
    "far": (140, 176, 160),
    "near": (18, 38, 26),
    "near_light": (84, 140, 72),
}

CARIBBEAN = {
    "top": (30, 100, 180),
    "mid": (110, 180, 226),
    "low": (226, 240, 236),
    "sun": (255, 252, 236),
    "glow": (255, 244, 210),
    "cloud": (255, 255, 252),
    "cloud_shadow": (170, 196, 214),
    "sea": (44, 176, 190),
    "sea_deep": (26, 100, 156),
    "sea_light": (200, 244, 236),
    "sand": (246, 236, 206),
    "mountain": (60, 120, 80),
    "mountain_light": (120, 166, 92),
    "palm": (70, 134, 70),
    "trunk": (196, 190, 176),
    "thatch": (200, 170, 108),
    "far": (130, 180, 190),
    "near": (22, 46, 38),
    "near_light": (110, 170, 120),
}

LAPITA = {
    "top": (70, 96, 150),
    "mid": (196, 170, 170),
    "low": (255, 214, 150),
    "sun": (255, 242, 204),
    "glow": (255, 200, 120),
    "cloud": (255, 226, 196),
    "cloud_shadow": (150, 120, 140),
    "lagoon": (70, 160, 150),
    "lagoon_light": (255, 222, 166),
    "reef": (252, 248, 238),
    "ocean": (44, 84, 124),
    "island": (52, 86, 70),
    "island_light": (130, 146, 84),
    "thatch": (196, 156, 96),
    "wood": (110, 80, 56),
    "sail": (226, 200, 150),
    "far": (176, 150, 150),
    "near": (36, 30, 26),
    "near_light": (190, 140, 80),
}

OPEN_OCEAN = {
    "top": (14, 22, 62),
    "mid": (52, 68, 138),
    "low": (255, 150, 80),
    "band": (255, 198, 124),
    "star": (255, 248, 230),
    "cloud": (110, 84, 116),
    "cloud_light": (255, 170, 116),
    "sea": (24, 48, 96),
    "sea_deep": (10, 22, 54),
    "sea_light": (255, 172, 112),
    "foam": (214, 224, 236),
    "island": (44, 46, 76),
    "bird": (20, 18, 30),
    "far": (64, 66, 116),
    "near": (8, 20, 42),
    "near_light": (60, 110, 150),
}

RAPA_NUI = {
    "top": (46, 96, 170),
    "mid": (130, 176, 214),
    "low": (232, 236, 226),
    "sun": (255, 250, 232),
    "glow": (255, 236, 200),
    "cloud": (250, 250, 248),
    "cloud_shadow": (140, 156, 176),
    "grass": (118, 140, 66),
    "grass_light": (178, 180, 96),
    "tuff": (140, 112, 84),
    "tuff_light": (196, 170, 128),
    "moai": (96, 86, 80),
    "pukao": (172, 72, 52),
    "ahu": (88, 88, 92),
    "sea": (40, 92, 150),
    "sea_light": (200, 230, 240),
    "cliff": (96, 84, 78),
    "far": (140, 160, 176),
    "near": (34, 40, 26),
    "near_light": (150, 160, 82),
}


# ---------------------------------------------------------------------------
# Parts that more than one place has
# ---------------------------------------------------------------------------


def _turn(points, centre, degrees: float):
    """`points` turned about `centre` by `degrees`."""
    a = math.radians(degrees)
    ca, sa = math.cos(a), math.sin(a)
    cx, cy = centre
    return [(cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca) for x, y in points]


def _fronds(pen: Pen, rng, top, h: float, count: int, reach: float, droop: float, width: float, leaflets: float = 0.05) -> None:
    """A head of palm fronds from `top`: each frond arches out and hangs,
    with leaflets that hang from its rib. `reach` and `leaflets` are parts of
    `h`, so a far palm and a near one have the same shape."""
    for k in range(count):
        angle = -200.0 + k * (220.0 / (count - 1)) + rng.uniform(-7.0, 7.0)
        length = h * reach * rng.uniform(0.85, 1.1)
        tip = polar(*top, length, angle)
        tip = (tip[0], tip[1] + length * droop)
        ctrl = polar(*top, length * 0.6, angle)
        ctrl = (ctrl[0], ctrl[1] - length * 0.28)
        prev = top
        for i in range(1, 11):
            t = i / 10.0
            x = (1 - t) ** 2 * top[0] + 2 * (1 - t) * t * ctrl[0] + t * t * tip[0]
            y = (1 - t) ** 2 * top[1] + 2 * (1 - t) * t * ctrl[1] + t * t * tip[1]
            pen.line([prev, (x, y)], width * (1.0 - t * 0.5))
            side = h * leaflets * (1.0 - t * 0.55)
            pen.line([(x, y), (x + side * 0.45, y + side)], width * 0.45)
            pen.line([(x, y), (x - side * 0.45, y + side)], width * 0.45)
            prev = (x, y)


def _royal_palm(trunk: Pen, crown: Pen, rng, u: float, v: float, h: float, lean: float = 0.0) -> None:
    """A royal palm: a tall smooth pale trunk, wide at its foot, a green
    crownshaft on its top, and a crown of long fronds."""
    w = h * 0.026
    pts = [(u + lean * t * t, v + 0.01 - (h * 0.78 + 0.01) * t) for t in np.linspace(0.0, 1.0, 10)]
    trunk.line(pts, w)
    trunk.ellipse(u, v - h * 0.03, w * 0.95, h * 0.05)
    trunk.ellipse(u + lean * 0.25, v - h * 0.40, w * 0.62, h * 0.06)
    top = pts[-1]
    crown.poly([(top[0] - w * 0.55, top[1] + 0.002), (top[0] + w * 0.55, top[1] + 0.002), (top[0] + w * 0.40, top[1] - h * 0.13), (top[0] - w * 0.40, top[1] - h * 0.13)])
    _fronds(crown, rng, (top[0], top[1] - h * 0.13), h, 12, 0.30, 0.55, w * 0.55)


def _coconut_palm(trunk: Pen, crown: Pen, rng, u: float, v: float, h: float, lean: float) -> None:
    """A coconut palm that leans: a ringed trunk that curves, a head of
    fronds, and a bunch of nuts under them."""
    w = h * 0.03
    pts = [(u + lean * t**1.6, v + 0.01 - (h + 0.01) * t) for t in np.linspace(0.0, 1.0, 12)]
    trunk.line(pts, w)
    top = pts[-1]
    _fronds(crown, rng, top, h, 11, 0.32, 0.50, w * 0.55, 0.045)
    for du in (-0.5, 0.2, 0.7):
        crown.ellipse(top[0] + du * w * 1.6, top[1] + h * 0.035, w * 0.7, w * 0.7)


def _canopy(pen: Pen, rng, line: np.ndarray, u0: float, u1: float, lift: float, r0: float, r1: float, count: int) -> None:
    """Crowns of trees in a forest: round heads that stand on `line`, some
    higher than others."""
    for _ in range(count):
        u = rng.uniform(u0, u1)
        r = rng.uniform(r0, r1)
        pen.ellipse(u, _at(line, u) - r * 0.4 - lift * rng.random(), r, r * 0.78)


def _crab_claw(pen: Pen, u: float, v: float, h: float, facing: float = 1.0) -> None:
    """A crab-claw sail: two spars in a V from the foot of the mast, and the
    sail between them, its top edge cut in a deep curve like the claw of a
    crab."""
    f = facing
    foot = (u, v)
    back = (u - f * h * 0.36, v - h * 0.96)
    front = (u + f * h * 0.80, v - h * 0.86)
    edge = _arch(back, (u + f * h * 0.10, v - h * 0.30), front, 10)
    pen.poly([foot, back] + edge[1:-1] + [front])


def _outrigger(hull: Pen, sail: Pen, u: float, v: float, s: float, facing: float = 1.0) -> None:
    """An outrigger canoe: a long hull, the float on two booms beside it, a
    mast, and a crab-claw sail."""
    f = facing
    hull.poly([(u - s * 0.50, v - s * 0.06), (u + s * 0.50, v - s * 0.06), (u + f * s * 0.56, v - s * 0.12), (u + s * 0.38, v), (u - s * 0.38, v), (u - f * s * 0.56, v - s * 0.12)])
    hull.rect(u - s * 0.30, v + s * 0.035, u + s * 0.30, v + s * 0.06)
    for du in (-0.18, 0.18):
        hull.line([(u + du * s, v - s * 0.04), (u + du * s, v + s * 0.045)], s * 0.018)
    hull.line([(u, v - s * 0.05), (u + f * s * 0.04, v - s * 0.50)], s * 0.02)
    _crab_claw(sail, u - f * s * 0.10, v - s * 0.08, s * 0.70, f)


def _voyaging_canoe(hull: Pen, sail: Pen, u: float, v: float, s: float, facing: float = 1.0) -> None:
    """A double-hulled voyaging canoe: two hulls with high ends, a deck
    between them with a small house on it, and two crab-claw sails."""
    f = facing
    for dv, k in ((0.0, 1.0), (-s * 0.04, 0.92)):
        hull.poly([(u - s * 0.50 * k, v - s * 0.06 + dv), (u + s * 0.50 * k, v - s * 0.06 + dv), (u + f * s * 0.60 * k, v - s * 0.20 + dv), (u + s * 0.40 * k, v + dv), (u - s * 0.40 * k, v + dv), (u - f * s * 0.60 * k, v - s * 0.18 + dv)])
    hull.rect(u - s * 0.42, v - s * 0.12, u + s * 0.42, v - s * 0.08)
    hull.poly([(u - s * 0.12, v - s * 0.12), (u + s * 0.10, v - s * 0.12), (u + s * 0.06, v - s * 0.22), (u - s * 0.08, v - s * 0.22)])
    for du, h in ((-0.22, 0.70), (0.20, 0.82)):
        hull.line([(u + du * s, v - s * 0.10), (u + du * s + f * s * 0.03, v - s * h)], s * 0.018)
        _crab_claw(sail, u + du * s + f * s * 0.01, v - s * 0.14, s * h * 0.95, f)


def _frigatebird(pen: Pen, u: float, v: float, s: float, beat: float = 0.0) -> None:
    """A frigatebird that glides: long thin wings bent at the wrist like an
    M, a slim body and a long forked tail."""
    lift = s * 0.18 * beat
    left = [(u - s * 1.0, v + s * 0.10 - lift), (u - s * 0.55, v - s * 0.18 - lift), (u - s * 0.40, v + s * 0.02), (u, v)]
    right = [(u, v), (u + s * 0.40, v + s * 0.02), (u + s * 0.55, v - s * 0.18 - lift), (u + s * 1.0, v + s * 0.10 - lift)]
    pen.line(left + right[1:], s * 0.07)
    pen.ellipse(u, v + s * 0.02, s * 0.06, s * 0.14)
    pen.line([(u, v + s * 0.12), (u - s * 0.07, v + s * 0.42)], s * 0.03)
    pen.line([(u, v + s * 0.12), (u + s * 0.07, v + s * 0.42)], s * 0.03)


# ---------------------------------------------------------------------------
# 1. The Olmec heartland: a humid morning on the Gulf coast
# ---------------------------------------------------------------------------


def _olmec_head(pen: Pen, face: Pen, u: float, v: float, s: float) -> None:
    """A colossal head of basalt seen from the front, its chin in the grass:
    a close helmet with a band and flaps over the ears, a broad face, a
    wide nose and full lips. It is an Olmec head, not a copy of one."""
    pen.ellipse(u, v - s * 1.02, s * 0.56, s * 0.34)
    pen.poly([(u - s * 0.56, v - s * 1.02), (u + s * 0.56, v - s * 1.02), (u + s * 0.54, v - s * 0.30), (u + s * 0.40, v), (u - s * 0.40, v), (u - s * 0.54, v - s * 0.30)])
    for side in (-1.0, 1.0):
        pen.poly([(u + side * s * 0.50, v - s * 0.96), (u + side * s * 0.64, v - s * 0.92), (u + side * s * 0.66, v - s * 0.38), (u + side * s * 0.52, v - s * 0.34)])
    face.line([(u - s * 0.56, v - s * 0.92), (u + s * 0.56, v - s * 0.92)], s * 0.05)
    for side in (-1.0, 1.0):
        face.ellipse(u + side * s * 0.20, v - s * 0.70, s * 0.11, s * 0.035)
    face.line([(u - s * 0.32, v - s * 0.80), (u + s * 0.32, v - s * 0.80)], s * 0.03)
    face.ellipse(u, v - s * 0.50, s * 0.15, s * 0.07)
    face.ellipse(u, v - s * 0.27, s * 0.20, s * 0.055)


def _clay_mound(pen: Pen, u: float, v: float, w: float, h: float) -> None:
    """A tall mound of clay with a round top and fluted sides, as the
    builders of the Gulf coast made them."""
    pts = []
    for k in range(25):
        t = k / 24.0
        x = u - w + 2.0 * w * t
        bump = 0.06 * math.sin(t * math.pi * 10.0) * math.sin(t * math.pi)
        pts.append((x, v - h * (math.sin(t * math.pi) ** 1.4) * (1.0 + bump)))
    pen.poly([(u - w, v)] + pts + [(u + w, v)])


def _cacao(trunk: Pen, leaves: Pen, pods: Pen, rng, u: float, v: float, h: float) -> None:
    """A cacao tree of the forest edge: a short trunk that forks, long
    leaves that hang, and pods that grow straight out of the trunk."""
    fork = (u + h * 0.02, v - h * 0.48)
    trunk.line([(u, v + 0.01), (u - h * 0.01, v - h * 0.25), fork], h * 0.04)
    ends = []
    for k in range(4):
        end = polar(*fork, h * rng.uniform(0.28, 0.38), -150.0 + k * 38.0 + rng.uniform(-8.0, 8.0))
        trunk.line([fork, end], h * 0.018)
        ends.append(end)
    for end in ends:
        for _ in range(9):
            base = (end[0] + rng.uniform(-0.06, 0.06) * h, end[1] + rng.uniform(-0.05, 0.05) * h)
            tip = (base[0] + rng.uniform(-0.12, 0.12) * h, base[1] + h * rng.uniform(0.08, 0.13))
            _leaf(leaves, _arch(base, ((base[0] + tip[0]) * 0.5 + h * 0.02, base[1] + h * 0.01), tip, 8), h * 0.032, 0.8)
    for t, side in ((0.18, 1.0), (0.30, -1.0), (0.40, 1.0), (0.62, -1.0)):
        x = u + h * 0.02 * t / 0.48
        pods.ellipse(x + side * h * 0.035, v - h * t, h * 0.026, h * 0.05)


def _cattails(pen: Pen, rng, u0: float, u1: float, v: float, h: float, count: int) -> None:
    """Cattails of the swamp: stiff stalks with a brown head like a sausage,
    and long thin leaves that bend."""
    for _ in range(count):
        u = rng.uniform(u0, u1)
        top = v - h * rng.uniform(0.6, 1.0)
        lean = rng.uniform(-0.01, 0.01)
        pen.line([(u, v + 0.01), (u + lean, top)], 0.0020)
        if rng.random() < 0.55:
            pen.ellipse(u + lean, top + h * 0.10, 0.0034, h * 0.07)
        else:
            tip = (u + rng.choice([-1.0, 1.0]) * h * 0.2, top + h * 0.15)
            pen.line(_arch((u, v), (u + lean, top), tip, 8), 0.0016)


def history_olmec(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = OLMEC
    sun_at = (0.72, 0.30)
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.85)), (0.24, p["top"]), (0.44, p["mid"]), (HORIZON - 0.02, p["low"]), (HORIZON + 0.05, mix(p["low"], p["plain"], 0.5)), (1.0, p["plain"])]))
        # The sun is a pale disc in the wet air: a wide soft light round it.
        _sun(a, layer, *sun_at, 0.030, p["sun"], p["glow"], 0.70)
        _heaps(a, layer, "olmec heaps", ((0.20, 0.38, 0.09, 0.08), (0.48, 0.44, 0.06, 0.05), (0.92, 0.40, 0.07, 0.06)), p["cloud"], p["cloud_shadow"], 0.75)
        # The Tuxtla mountains far off, where the basalt of the heads came
        # from: a row of old volcanoes, blue in the haze.
        hills, _ = a.ridge("tuxtla", HORIZON - 0.035, 0.028, cells=3.0, octaves=4, sharp=0.5)
        a.tint(layer, hills * smoothstep(0.30, 0.10, np.abs(a.u - 0.30)), mix(p["tuxtla"], p["low"], 0.40), 0.85)
        a.tint(layer, a.band(HORIZON - 0.02, 0.10, 1.4), p["low"], 0.35)
        _textbook(a, layer, 0.07)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far olmec")
        ground, line = a.ridge("olmec plain", HORIZON + 0.012, 0.004, cells=3.0, octaves=3)
        forest, forest_pen = a.drawing()
        palms, palm_pen = a.drawing()
        mound, mound_pen = a.drawing()
        head, head_pen = a.drawing()
        face, face_pen = a.drawing()
        grass, grass_pen = a.drawing()
        # Swamp forest at the two sides, and islands of trees on the plain.
        _canopy(forest_pen, rng, line, 0.0, 0.22, 0.03, 0.012, 0.026, 60)
        _canopy(forest_pen, rng, line, 0.80, 1.0, 0.03, 0.012, 0.026, 50)
        for u0 in (0.36, 0.52):
            _canopy(forest_pen, rng, line, u0, u0 + 0.05, 0.006, 0.006, 0.012, 10)
        for u in (0.25, 0.28, 0.74, 0.78):
            _fronds(palm_pen, rng, (u, _at(line, u) - 0.05), 0.07, 9, 0.30, 0.50, 0.0016)
            palm_pen.line([(u, _at(line, u) + 0.004), (u, _at(line, u) - 0.05)], 0.0022)
        # A mound of clay far off, and the head half in the grass nearer.
        _clay_mound(mound_pen, 0.42, _at(line, 0.42) + 0.003, 0.045, 0.045)
        hu = 0.64
        hv = _at(line, hu) + 0.040
        _olmec_head(head_pen, face_pen, hu, hv, 0.042)
        for _ in range(90):
            u = hu + rng.uniform(-0.05, 0.05)
            gh = rng.uniform(0.004, 0.014)
            grass_pen.line([(u, hv + 0.004), (u + rng.uniform(-0.003, 0.003), hv - gh)], 0.0018)
        mask = np.maximum.reduce([ground, a.mask_of(forest), a.mask_of(palms), a.mask_of(mound), a.mask_of(head)])
        layer = solid(a, mask, mix(p["plain"], p["far"], 0.35), mix(p["plain"], p["forest"], 0.25), HORIZON - 0.06, HORIZON + 0.06, "olmec far", 0.05)
        a.put(layer, a.mask_of(forest), mix(p["forest"], p["far"], 0.35))
        a.light(layer, a.mask_of(forest) * a.rim(a.mask_of(forest), -0.002, 0.003, 0.5), p["forest_light"], 0.45)
        a.put(layer, a.mask_of(palms), mix(p["forest"], p["far"], 0.25))
        mound_mask = a.mask_of(mound)
        a.put(layer, mound_mask, mix(p["clay"], p["far"], 0.35))
        a.shade(layer, mound_mask * smoothstep(0.41, 0.46, a.u), 0.20)
        a.put(layer, mound_mask * smoothstep(0.55, 0.75, a.noise("mound grass", cells=30.0, octaves=2)), mix(p["plain"], p["far"], 0.4), 0.6)
        head_mask = a.mask_of(head)
        a.put(layer, head_mask, p["basalt"])
        a.light(layer, head_mask * smoothstep(hu + 0.01, hu - 0.03, a.u), p["glow"], 0.30)
        a.shade(layer, head_mask * smoothstep(hu + 0.005, hu + 0.03, a.u), 0.25)
        a.shade(layer, a.mask_of(face, blur=0.4) * head_mask, 0.55)
        a.put(layer, a.mask_of(grass), mix(p["plain"], p["far"], 0.2))
        # The slow brown river that winds over the plain towards the eye.
        river, river_pen = a.drawing()
        prev = None
        for k in range(60):
            t = k / 59.0
            v = HORIZON + 0.014 + 0.30 * t**1.6
            u = 0.46 + (0.06 + 0.30 * t) * math.sin(t * 7.0 + 0.4)
            w = 0.003 + 0.08 * t**1.2
            if prev is not None:
                river_pen.poly([(prev[0] - prev[2], prev[1]), (prev[0] + prev[2], prev[1]), (u + w, v), (u - w, v)])
            prev = (u, v, w)
        water = a.mask_of(river, blur=0.6) * ground
        a.put(layer, water, mix(p["river"], p["mid"], 0.25))
        a.shade(layer, water * a.rim(water, 0.0, -0.003, 0.3), 0.25)
        glints = smoothstep(0.55, 0.80, a.noise("river glints", cells=60.0, octaves=2, stretch=8.0))
        a.light(layer, water * glints, p["river_light"], 0.45)
        a.light(layer, a.rim(mask, 0.002, 0.003, 0.5) * mask, p["glow"], 0.30)
        haze(a, layer, p["low"], 0.10, HORIZON + 0.02)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near olmec")
        image, pen = a.drawing()
        leaves, leaf_pen = a.drawing()
        pods, pod_pen = a.drawing()
        sedge, sedge_pen = a.drawing()
        ground, _ = a.ridge("near olmec", 0.70, 0.008, cells=4.0, octaves=3)
        # A cacao tree with its pods at the left, a palm at the right, and
        # cattails at the edge of the swamp.
        _cacao(pen, leaf_pen, pod_pen, rng, 0.16, 0.72, 0.30)
        _cacao(pen, leaf_pen, pod_pen, rng, 0.05, 0.72, 0.36)
        pen.line([(0.88 + 0.02 * t * t, 0.73 - 0.40 * t) for t in np.linspace(0.0, 1.0, 10)], 0.009)
        _fronds(leaf_pen, rng, (0.90, 0.33), 0.40, 13, 0.32, 0.55, 0.0035, 0.045)
        _cattails(sedge_pen, rng, 0.20, 0.30, 0.715, 0.12, 22)
        _cattails(sedge_pen, rng, 0.74, 0.86, 0.715, 0.10, 18)
        mask = np.maximum.reduce([ground, a.mask_of(image), a.mask_of(leaves), a.mask_of(pods), a.mask_of(sedge)])
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.40), p["near"], 0.30, 0.74, "olmec near", 0.08)
        a.put(layer, a.mask_of(leaves), mix(p["forest_light"], p["near"], 0.50))
        a.put(layer, a.mask_of(pods), mix(p["pod"], p["near"], 0.40))
        a.put(layer, a.mask_of(sedge) * (a.v < 0.71), mix((150, 140, 80), p["near"], 0.45))
        a.light(layer, a.rim(mask, 0.003, 0.002, 0.4) * mask, p["glow"], 0.36)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.22)
        haze(a, layer, p["far"], 0.10, 0.73)
        return layer
    layer = _air(a, p, "olmec damp", p["low"], 0.26, p["near"], 0.22)
    a.put(layer, fog(a, "olmec haze", 0.52, 0.14, cells=1.5), p["low"], 0.06)
    return layer


def olmec_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Cattails of the swamp that stand from below at a few places."""
    del layer_lights
    rng = art_.rand("olmec foreground")
    for k in range(3):
        u0 = (k + rng.uniform(0.2, 0.8)) / 3.0
        for _ in range(7):
            u = u0 + rng.uniform(-0.025, 0.025)
            top = REST_BOTTOM - rng.uniform(-0.01, 0.012)
            lean = rng.uniform(-0.01, 0.01)
            pen.line([(u, 1.0), (u + lean, top)], 0.0018)
            if rng.random() < 0.6:
                pen.ellipse(u + lean, top + 0.022, 0.0032, 0.014)
            else:
                pen.line(_arch((u, 0.9), (u + lean, top), (u + rng.choice([-1.0, 1.0]) * 0.03, top + 0.04), 8), 0.0016)


# ---------------------------------------------------------------------------
# 2. The Maya city: temples over the rainforest in the morning mist
# ---------------------------------------------------------------------------


def _maya_pyramid(pen: Pen, lit: Pen, temple: Pen, comb: Pen, holes: Pen, u: float, v: float, half: float, h: float, tiers: int = 8) -> None:
    """A stepped temple pyramid: steep tiers, each set back on the one under
    it, a stair up the front, a temple of one room on the top with a dark
    door, and a tall roof comb with openings in it."""
    top_half = half * 0.30
    body = h * 0.66
    for k in range(tiers):
        t0, t1 = k / tiers, (k + 1) / tiers
        w0 = half + (top_half - half) * t0
        w1 = half + (top_half - half) * t1
        y0, y1 = v - body * t0, v - body * t1
        pen.poly([(u - w0, y0), (u + w0, y0), (u + w1 * 1.03, y1), (u - w1 * 1.03, y1)])
        lit.rect(u - w1 * 1.03, y1, u + w1 * 1.03, y1 + (y0 - y1) * 0.20)
    stair = half * 0.15
    lit.poly([(u - stair, v), (u + stair, v), (u + stair * 0.75, v - body), (u - stair * 0.75, v - body)])
    tw, th = top_half * 0.85, h * 0.15
    temple.rect(u - tw, v - body - th, u + tw, v - body)
    holes.rect(u - tw * 0.22, v - body - th * 0.62, u + tw * 0.22, v - body)
    comb.poly([(u - tw * 0.72, v - body - th), (u + tw * 0.72, v - body - th), (u + tw * 0.46, v - h), (u - tw * 0.46, v - h)])
    for k in range(3):
        y = v - body - th - (h - body - th) * (0.25 + k * 0.25)
        holes.rect(u - tw * 0.16, y - (h - body - th) * 0.08, u + tw * 0.16, y + (h - body - th) * 0.06)


def _ballcourt(pen: Pen, rings: Pen, u: float, v: float, w: float, h: float) -> None:
    """A ballcourt: two long buildings with sloped faces on the two sides of
    a narrow alley, and a stone ring high on each face."""
    for side in (-1.0, 1.0):
        pen.poly([(u + side * w, v), (u + side * w * 0.22, v), (u + side * w * 0.36, v - h * 0.55), (u + side * w * 0.40, v - h), (u + side * w, v - h)])
        rings.ring(u + side * w * 0.40, v - h * 0.78, h * 0.13, h * 0.06)


def _ceiba(trunk: Pen, crown: Pen, rng, u: float, v: float, h: float) -> None:
    """A ceiba, the great tree of the forest: a straight grey trunk with
    tall buttresses at its foot, long level limbs, and a flat crown."""
    w = h * 0.04
    trunk.poly([(u - w * 0.8, v + 0.01), (u + w * 0.8, v + 0.01), (u + w * 0.55, v - h * 0.78), (u - w * 0.55, v - h * 0.78)])
    for side in (-1.0, 1.0):
        trunk.poly([(u + side * w * 0.5, v - h * 0.22), (u + side * w * 3.2, v + 0.01), (u + side * w * 1.8, v + 0.01), (u + side * w * 0.6, v - h * 0.05)])
    top = (u, v - h * 0.78)
    for k in range(5):
        end = (u + (k - 2) * h * 0.14, top[1] - h * rng.uniform(0.04, 0.10))
        trunk.line([top, ((top[0] + end[0]) * 0.5, top[1] - h * 0.02), end], w * 0.30)
        crown.ellipse(end[0], end[1] - h * 0.02, h * rng.uniform(0.08, 0.12), h * rng.uniform(0.03, 0.05))


def _lianas(pen: Pen, rng, u0: float, u1: float, v_top: float, v_bottom: float, count: int, width: float) -> None:
    """Lianas that hang from the canopy: long thin ropes that sway a little,
    each with a few leaves."""
    for _ in range(count):
        u = rng.uniform(u0, u1)
        end = rng.uniform(v_top + (v_bottom - v_top) * 0.4, v_bottom)
        phase = rng.uniform(0.0, 6.28)
        pts = [(u + 0.006 * math.sin(phase + t * 4.0) * t, v_top + (end - v_top) * t) for t in np.linspace(0.0, 1.0, 14)]
        pen.line(pts, width)
        for x, y in pts[4::3]:
            pen.ellipse(x + width * 2.0, y, width * 2.4, width * 1.6)


def history_maya(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = MAYA
    sun_at = (0.26, 0.40)
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.85)), (0.26, p["top"]), (0.46, p["mid"]), (HORIZON - 0.02, p["low"]), (HORIZON + 0.05, mix(p["mist"], p["canopy"], 0.5)), (1.0, p["canopy"])]))
        _sun(a, layer, *sun_at, 0.026, p["sun"], p["glow"], 0.55)
        a.put(layer, shafts(a, "maya sky shafts", 5, 0.20, 0.30, 0.75, 0.04) * (a.v > sun_at[1]), p["glow"], 0.12)
        _heaps(a, layer, "maya heaps", ((0.62, 0.34, 0.08, 0.07), (0.90, 0.30, 0.06, 0.05)), p["mist"], mix(p["mid"], p["canopy"], 0.25), 0.80)
        # A far temple in the haze, and the flat canopy of the forest to the
        # horizon.
        far, far_pen = a.drawing()
        _maya_pyramid(far_pen, far_pen, far_pen, far_pen, far_pen, 0.84, HORIZON - 0.005, 0.040, 0.090, 7)
        a.tint(layer, a.mask_of(far, blur=0.6), mix(p["stone"], p["mid"], 0.45), 0.60)
        canopy, _ = a.ridge("maya far canopy", HORIZON - 0.008, 0.004, cells=40.0, octaves=2)
        a.tint(layer, canopy, mix(p["canopy"], p["mid"], 0.60), 0.80)
        _textbook(a, layer, 0.06)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far maya")
        _, line = a.ridge("maya floor", HORIZON + 0.004, 0.003, cells=3.0, octaves=3)
        image, pen = a.drawing()
        lit, lit_pen = a.drawing()
        temples, temple_pen = a.drawing()
        combs, comb_pen = a.drawing()
        holes, hole_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        court, court_pen = a.drawing()
        rings, ring_pen = a.drawing()
        # The great temple, a smaller one, and a ballcourt in a clearing.
        _maya_pyramid(pen, lit_pen, temple_pen, comb_pen, hole_pen, 0.60, _at(line, 0.60) + 0.01, 0.075, 0.24, 9)
        _maya_pyramid(pen, lit_pen, temple_pen, comb_pen, hole_pen, 0.33, _at(line, 0.33) + 0.01, 0.050, 0.14, 7)
        cu, cv = 0.465, _at(line, 0.465) + 0.022
        _ballcourt(court_pen, ring_pen, cu, cv, 0.040, 0.016)
        # The canopy over the feet of the temples: round crowns in rows that
        # come nearer and get larger down the panel, with a clearing round
        # the ballcourt.
        rows = []
        v, r0 = _at(line, 0.5) - 0.004, 0.010
        while v < 0.80:
            rows.append((v, r0))
            v += r0 * 0.9
            r0 *= 1.18
        for v, r0 in rows:
            for _ in range(int(2.2 / r0)):
                u = rng.random()
                if abs(u - cu) < 0.06 and abs(v - cv) < 0.03:
                    continue
                r = r0 * rng.uniform(0.7, 1.3)
                crown_pen.ellipse(u, v + rng.uniform(-0.3, 0.3) * r0, r, r * 0.8)
        clearing, clearing_pen = a.drawing()
        clearing_pen.ellipse(cu, cv - 0.002, 0.07, 0.014)
        stone = np.maximum.reduce([a.mask_of(image), a.mask_of(temples), a.mask_of(combs), a.mask_of(court)])
        canopy = a.mask_of(crowns)
        floor = smoothstep(_at(line, 0.5) - 0.004, _at(line, 0.5) + 0.004, a.v)
        mask = np.maximum.reduce([stone, canopy, floor])
        layer = solid(a, mask, mix(p["stone"], p["far"], 0.20), mix(p["stone_shadow"], p["far"], 0.20), HORIZON - 0.20, HORIZON, "maya stone", 0.06)
        a.light(layer, a.mask_of(lit) * a.mask_of(image), p["comb"], 0.35)
        a.put(layer, a.mask_of(temples), mix(p["red"], p["far"], 0.25))
        a.put(layer, a.mask_of(combs), mix(p["comb"], p["far"], 0.10))
        a.shade(layer, a.mask_of(holes) * stone, 0.55)
        # The side of each tier away from the sun is in shade.
        a.shade(layer, a.mask_of(image) * (smoothstep(0.60, 0.62, a.u) * smoothstep(0.70, 0.66, a.u) + smoothstep(0.33, 0.345, a.u) * smoothstep(0.40, 0.37, a.u)), 0.18)
        paint = a.ramp([(0.0, mix(p["canopy"], p["far"], 0.45)), (HORIZON, mix(p["canopy"], p["far"], 0.45)), (HORIZON + 0.08, p["canopy"]), (1.0, scale(p["canopy"], 0.8))])
        a.put(layer, np.maximum(canopy, floor), paint)
        a.put(layer, a.mask_of(clearing, blur=1.0) * floor * (1.0 - stone), mix((150, 170, 96), p["far"], 0.25))
        a.light(layer, a.rim(canopy, -0.002, 0.004, 0.6) * canopy, p["canopy_light"], 0.65)
        a.light(layer, a.rim(canopy, -0.002, 0.002, 0.3) * canopy, p["glow"], 0.35)
        a.shade(layer, a.rim(canopy, 0.0, -0.004, 1.0) * canopy, 0.25)
        a.put(layer, a.mask_of(court) * (1.0 - canopy), mix(p["stone"], p["far"], 0.15))
        a.put(layer, a.mask_of(rings, blur=0.3) * (1.0 - canopy), mix(p["stone_shadow"], p["near"], 0.30))
        # Mist in the low places of the forest, round the feet of the temples.
        a.tint(layer, fog(a, "maya valley mist", HORIZON - 0.005, 0.025, 3.0), p["mist"], 0.55)
        a.tint(layer, fog(a, "maya low mist", HORIZON + 0.05, 0.02, 2.0) * canopy, p["mist"], 0.25)
        # Two macaws that fly over the canopy.
        birds, bird_pen = a.drawing()
        for u, v in ((0.70, HORIZON - 0.10), (0.72, HORIZON - 0.095)):
            bird_pen.line([(u - 0.006, v - 0.003), (u, v), (u + 0.006, v - 0.004)], 0.0020)
            bird_pen.line([(u, v), (u - 0.010, v + 0.002)], 0.0014)
        a.glow(layer, a.mask_of(birds, blur=0.3), mix(p["macaw"], p["far"], 0.20), 0.85)
        haze(a, layer, p["mist"], 0.08, None)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near maya")
        image, pen = a.drawing()
        crowns, crown_pen = a.drawing()
        leaves, leaf_pen = a.drawing()
        ground, _ = a.ridge("near maya", 0.70, 0.010, cells=5.0, octaves=3)
        # A ceiba at the left with lianas from its limbs; a fan of big
        # leaves at its foot; palms and lianas at the right.
        _ceiba(pen, crown_pen, rng, 0.09, 0.72, 0.60)
        _lianas(pen, rng, 0.0, 0.20, 0.10, 0.58, 9, 0.0024)
        _lianas(pen, rng, 0.82, 1.0, 0.05, 0.56, 9, 0.0024)
        for u in (0.86, 0.97):
            pen.line([(u, 0.72), (u - 0.02, 0.36)], 0.008)
            _fronds(leaf_pen, rng, (u - 0.02, 0.36), 0.36, 12, 0.36, 0.50, 0.0032, 0.05)
        for k in range(7):
            base = (0.22 + rng.uniform(-0.01, 0.01), 0.715)
            tip = polar(*base, rng.uniform(0.06, 0.09), -160.0 + k * 22.0)
            _leaf(leaf_pen, _arch(base, ((base[0] + tip[0]) * 0.5, tip[1] - 0.02), tip, 8), 0.010, 0.6)
        mask = np.maximum.reduce([ground, a.mask_of(image), a.mask_of(crowns), a.mask_of(leaves)])
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.35), p["near"], 0.30, 0.74, "maya near", 0.08)
        a.put(layer, a.mask_of(image) * (a.u < 0.16) * (a.v > 0.20) * (a.v < 0.72), mix((150, 150, 136), p["near"], 0.55))
        a.put(layer, a.mask_of(crowns), mix(p["canopy"], p["near"], 0.45))
        a.put(layer, a.mask_of(leaves), mix(p["canopy_light"], p["near"], 0.50))
        a.light(layer, a.rim(mask, 0.003, 0.002, 0.4) * mask, p["glow"], 0.34)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.22)
        haze(a, layer, p["mist"], 0.12, 0.73)
        return layer
    layer = _air(a, p, "maya morning mist", p["mist"], 0.34, p["near"], 0.22)
    a.put(layer, shafts(a, "maya shafts", 4, 0.14, 0.0, 0.85, 0.05), p["glow"], 0.10)
    return layer


def maya_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Lianas that sag across the top of the view at two places, with leaves
    in the shape of a heart that hang from them."""
    del layer_lights
    rng = art_.rand("maya foreground")
    for k in range(2):
        u0 = k * 0.5 + rng.uniform(0.04, 0.16)
        u1 = u0 + rng.uniform(0.22, 0.30)
        sag = rng.uniform(0.030, 0.040)
        pen.curve((u0, 0.33), (u1, 0.335), sag, 0.0026)
        for j in range(7):
            t = (j + 0.5) / 7.0
            x = u0 + (u1 - u0) * t
            y = 0.33 + 0.005 * t + sag * 4.0 * t * (1.0 - t)
            drop = rng.uniform(0.004, 0.012)
            if y + drop > 0.392:
                drop = max(0.0, 0.392 - y - 0.006)
            pen.line([(x, y), (x, y + drop)], 0.0012)
            pen.ellipse(x, y + drop + 0.004, 0.0040, 0.0050)


# ---------------------------------------------------------------------------
# 3. The Taino islands: a bright noon on the Caribbean
# ---------------------------------------------------------------------------


def _bohio(pen: Pen, door: Pen, u: float, v: float, w: float) -> None:
    """A bohio, a round house of the Taino: a wall of cane, and a tall cone
    of thatch with a point and a short pole at its top."""
    pen.rect(u - w, v - w * 0.55, u + w, v)
    pen.poly([(u - w * 1.18, v - w * 0.48), (u, v - w * 1.75), (u + w * 1.18, v - w * 0.48)])
    pen.line([(u, v - w * 1.75), (u, v - w * 1.95)], w * 0.07)
    door.rect(u - w * 0.18, v - w * 0.42, u + w * 0.18, v)


def _dugout(hull: Pen, crew: Pen, u: float, v: float, s: float, paddlers: int) -> None:
    """A long dugout canoe of the Taino with its paddlers in a row, each
    with a paddle in the water."""
    hull.poly([(u - s * 0.50, v - s * 0.05), (u + s * 0.52, v - s * 0.06), (u + s * 0.44, v), (u - s * 0.44, v)])
    for k in range(paddlers):
        x = u - s * 0.36 + k * s * 0.72 / max(paddlers - 1, 1)
        crew.ellipse(x, v - s * 0.12, s * 0.018, s * 0.022)
        crew.line([(x, v - s * 0.10), (x, v - s * 0.05)], s * 0.022)
        crew.line([(x + s * 0.02, v - s * 0.11), (x - s * 0.04, v + s * 0.04)], s * 0.008)


def _sea_grape(pen: Pen, rng, u: float, v: float, h: float) -> None:
    """A sea grape bush of the beach: crooked stems and big round leaves."""
    for _ in range(5):
        end = (u + rng.uniform(-0.6, 0.6) * h, v - rng.uniform(0.4, 0.9) * h)
        pen.line([(u + rng.uniform(-0.1, 0.1) * h, v + 0.01), ((u + end[0]) * 0.5, (v + end[1]) * 0.5 + h * 0.1), end], h * 0.025)
    for _ in range(34):
        t = rng.uniform(0.0, 1.0)
        pen.ellipse(u + rng.uniform(-0.85, 0.85) * h * (1.0 - t * 0.4), v - t * h, h * rng.uniform(0.08, 0.12), h * rng.uniform(0.07, 0.10))


def history_caribbean(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = CARIBBEAN
    sea_v = HORIZON + 0.004
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.85)), (0.24, p["top"]), (0.46, p["mid"]), (HORIZON - 0.004, p["low"]), (sea_v, p["sea_deep"]), (HORIZON + 0.05, p["sea"]), (1.0, mix(p["sea"], p["sea_light"], 0.35))]))
        _sun(a, layer, 0.82, 0.22, 0.026, p["sun"], p["glow"], 0.55)
        _heaps(a, layer, "taino heaps", ((0.52, 0.40, 0.07, 0.07), (0.70, 0.46, 0.05, 0.05), (0.94, 0.42, 0.06, 0.06)), p["cloud"], p["cloud_shadow"])
        # The sea: a band of light where the sun is, and the far edge of the
        # reef as a line of pale water.
        glints = smoothstep(0.62, 0.82, a.noise("taino glints", cells=70.0, octaves=2, stretch=7.0))
        a.light(layer, smoothstep(sea_v, sea_v + 0.004, a.v) * glints * a.spot(0.80, HORIZON + 0.06, 0.30, 1.2, squash=1.8), p["sea_light"], 0.55)
        islet, _ = a.ridge("taino islet", HORIZON - 0.006, 0.006, cells=5.0, octaves=3, sharp=0.6)
        a.tint(layer, islet * (a.v < sea_v) * smoothstep(0.08, 0.04, np.abs(a.u - 0.90)), mix(p["mountain"], p["mid"], 0.55), 0.85)
        _textbook(a, layer, 0.05)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far taino")
        _, line = a.ridge("taino shore", HORIZON + 0.022, 0.004, cells=3.0, octaves=3)
        # Green mountains at the left that come down to the shore; a strip of
        # beach at their foot that ends in a point, and the sea at the right
        # and in front.
        _, peaks = a.ridge("taino mountains", HORIZON - 0.11, 0.05, cells=3.0, octaves=5, sharp=0.5)
        slope = peaks + (line - peaks) * smoothstep(0.24, 0.60, a.u[0])
        coast = 0.66 - (a.v - HORIZON) * 1.6
        land = _land(a, slope) * smoothstep(coast + 0.01, coast - 0.01, a.u) * (a.v < line[None, :] + 0.016)
        shore = _land(a, line) * smoothstep(coast + 0.02, coast, a.u) * (a.v < line[None, :] + 0.022)
        image, pen = a.drawing()
        thatch, thatch_pen = a.drawing()
        doors, door_pen = a.drawing()
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        boat, boat_pen = a.drawing()
        crew, crew_pen = a.drawing()
        # The village: round bohios on the sand under royal palms.
        for u, w in ((0.30, 0.016), (0.36, 0.020), (0.43, 0.014), (0.49, 0.017)):
            _bohio(thatch_pen, door_pen, u, _at(line, u) + 0.004, w)
        for u in (0.27, 0.33, 0.40, 0.46, 0.53, 0.58):
            _royal_palm(trunk_pen, crown_pen, rng, u, _at(line, u) + 0.006, rng.uniform(0.06, 0.08), rng.uniform(-0.003, 0.003))
        # A dugout with its paddlers on the turquoise water.
        _dugout(boat_pen, crew_pen, 0.76, sea_v + 0.024, 0.08, 7)
        mountain = land * (1.0 - shore)
        mask = np.maximum.reduce([land, shore, a.mask_of(thatch), a.mask_of(trunks), a.mask_of(crowns), a.mask_of(boat), a.mask_of(crew)])
        layer = solid(a, mask, mix(p["mountain"], p["far"], 0.35), mix(p["mountain"], p["far"], 0.15), HORIZON - 0.14, HORIZON, "taino far", 0.06)
        a.light(layer, mountain * smoothstep(0.35, 0.65, a.noise("taino forest", cells=26.0, octaves=3)), p["mountain_light"], 0.30)
        a.light(layer, a.rim(land, 0.003, 0.003, 0.5) * mountain, p["glow"], 0.35)
        # The beach: white sand, and the line of the wash on it.
        a.put(layer, shore, mix(p["sand"], p["far"], 0.10))
        a.put(layer, a.rim(shore, 0.0, -0.004, 0.4) * shore, p["sea_light"], 0.8)
        a.put(layer, a.mask_of(thatch), mix(p["thatch"], p["far"], 0.20))
        a.shade(layer, a.mask_of(thatch) * a.mask_of(doors), 0.55)
        a.put(layer, a.mask_of(trunks), mix(p["trunk"], p["far"], 0.20))
        a.put(layer, a.mask_of(crowns), mix(p["palm"], p["far"], 0.25))
        a.put(layer, a.mask_of(boat), mix((90, 60, 40), p["far"], 0.25))
        a.put(layer, a.mask_of(crew), mix((120, 60, 40), p["far"], 0.25))
        # Cloud on the tops of the mountains.
        _heaps(a, layer, "taino summit cloud", ((0.08, HORIZON - 0.13, 0.08, 0.05), (0.20, HORIZON - 0.12, 0.06, 0.04)), p["cloud"], p["cloud_shadow"], 0.90)
        a.tint(layer, fog(a, "taino summit mist", HORIZON - 0.12, 0.025, 3.0) * smoothstep(0.34, 0.20, a.u), p["cloud"], 0.70)
        haze(a, layer, p["low"], 0.10, HORIZON + 0.02)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near taino")
        image, pen = a.drawing()
        crowns, crown_pen = a.drawing()
        bush, bush_pen = a.drawing()
        ground, _ = a.ridge("near taino", 0.705, 0.006, cells=4.0, octaves=3)
        # Royal palms at the left, a sea grape bush at the right.
        _royal_palm(pen, crown_pen, rng, 0.07, 0.72, 0.62, 0.01)
        _royal_palm(pen, crown_pen, rng, 0.17, 0.72, 0.48, -0.01)
        _sea_grape(bush_pen, rng, 0.82, 0.72, 0.09)
        _coconut_palm(pen, crown_pen, rng, 0.97, 0.72, 0.42, -0.08)
        mask = np.maximum.reduce([ground, a.mask_of(image), a.mask_of(crowns), a.mask_of(bush)])
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.40), p["near"], 0.30, 0.74, "taino near", 0.08)
        a.put(layer, a.mask_of(image) * (a.v < 0.71), mix(p["trunk"], p["near"], 0.55))
        a.put(layer, a.mask_of(crowns), mix(p["palm"], p["near"], 0.45))
        a.put(layer, a.mask_of(bush), mix(p["palm"], p["near"], 0.40))
        a.put(layer, ground * (1.0 - a.mask_of(image)), mix(p["sand"], p["near"], 0.45))
        a.light(layer, a.rim(mask, 0.003, 0.003, 0.4) * mask, p["glow"], 0.40)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.20)
        haze(a, layer, p["far"], 0.08, 0.73)
        return layer
    return _air(a, p, "taino salt air", p["low"], 0.18, p["near"], 0.18)


def caribbean_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """The tips of palm fronds that hang into the top of the view at two
    places, each with its leaflets."""
    del layer_lights
    rng = art_.rand("taino foreground")
    for k in range(2):
        u0 = (k + rng.uniform(0.15, 0.85)) / 2.0
        for j in range(2):
            start = (u0 + (j - 0.5) * 0.05, 0.0)
            end = (start[0] + (0.08 if j else -0.08) + rng.uniform(-0.02, 0.02), 0.388 - rng.uniform(0.0, 0.01))
            ctrl = ((start[0] + end[0]) * 0.5 + (0.04 if j else -0.04), 0.20)
            rib = _arch(start, ctrl, end, 20)
            pen.line(rib, 0.0026)
            for i, (x, y) in enumerate(rib[1:], 1):
                t = i / 20.0
                side = 0.026 * (1.0 - t * 0.5)
                if y + side * 0.9 > 0.392:
                    side = max(0.0, (0.392 - y) / 0.9)
                pen.line([(x, y), (x + side * 0.45, y + side * 0.9)], 0.0015)
                pen.line([(x, y), (x - side * 0.45, y + side * 0.9)], 0.0015)


# ---------------------------------------------------------------------------
# 4. The Lapita voyagers: a gold afternoon on a lagoon
# ---------------------------------------------------------------------------


def _stilt_house(roof: Pen, posts: Pen, u: float, v_water: float, w: float, h: float) -> None:
    """A house on stilts over a lagoon: a row of tall posts that stand in
    the water, a floor of poles on them with a ladder, low walls, and a
    saddle roof of thatch whose ridge sags and whose ends reach out."""
    floor = v_water - h * 0.45
    for k in range(5):
        x = u - w * 0.85 + k * w * 0.425
        posts.line([(x, v_water + h * 0.03), (x, floor)], w * 0.11)
    posts.rect(u - w * 1.05, floor - h * 0.05, u + w * 1.05, floor)
    posts.rect(u - w * 0.80, floor - h * 0.22, u + w * 0.80, floor - h * 0.05)
    posts.line([(u + w * 1.30, v_water + h * 0.02), (u + w * 1.0, floor)], w * 0.08)
    eave = floor - h * 0.12
    ridge = _arch((u - w * 0.80, floor - h * 0.88), (u, floor - h * 0.70), (u + w * 0.80, floor - h * 0.88), 12)
    roof.poly([(u - w * 1.30, eave), (u + w * 1.30, eave)] + ridge[::-1])


def _volcanic_island(pen: Pen, u: float, v: float, w: float, h: float) -> None:
    """An island that is a volcano: a steep cone with a notch in its top and
    a skirt of low land round it."""
    pen.poly([(u - w, v), (u - w * 0.55, v - h * 0.10), (u - w * 0.22, v - h * 0.75), (u - w * 0.08, v - h), (u + w * 0.02, v - h * 0.90), (u + w * 0.10, v - h * 0.98), (u + w * 0.30, v - h * 0.62), (u + w * 0.60, v - h * 0.12), (u + w, v)])


def _mangrove(trunk: Pen, crown: Pen, rng, u: float, v: float, h: float) -> None:
    """A mangrove in the shallow water: prop roots that arch out of its
    trunk into the water, and a round crown."""
    base = (u, v - h * 0.30)
    for k in range(9):
        foot = (u + (k - 4) * h * 0.06, v + 0.01)
        ctrl = (u + (k - 4) * h * 0.035, v - h * 0.30)
        trunk.line(_arch((u + (k - 4) * h * 0.006, v - h * 0.26), ctrl, foot, 10), h * 0.008)
    top = (u + h * 0.03, v - h * 0.70)
    trunk.line([base, (u + h * 0.01, v - h * 0.50), top], h * 0.03)
    for k in range(3):
        trunk.line([top, polar(*top, h * 0.18, -150.0 + k * 60.0)], h * 0.012)
    for _ in range(16):
        crown.ellipse(top[0] + rng.uniform(-0.22, 0.22) * h, top[1] - rng.uniform(-0.04, 0.16) * h, h * rng.uniform(0.07, 0.11), h * rng.uniform(0.05, 0.08))


def _pandanus(trunk: Pen, leaves: Pen, rng, u: float, v: float, h: float, lean: float) -> None:
    """A pandanus (a screw pine): stilt roots at its foot, a trunk that
    leans and forks, and at the end of each branch a tuft of long leaves like
    straps that bend down."""
    for k in range(5):
        trunk.line([(u + lean * 0.10 + (k - 2) * h * 0.010, v - h * 0.20), (u + (k - 2) * h * 0.05, v + 0.01)], h * 0.010)
    fork = (u + lean * 0.5, v - h * 0.55)
    trunk.line([(u + lean * 0.10, v - h * 0.20), fork], h * 0.026)
    for k in range(3):
        end = polar(*fork, h * rng.uniform(0.22, 0.32), -140.0 + k * 50.0 + rng.uniform(-8.0, 8.0))
        trunk.line([fork, end], h * 0.016)
        for j in range(11):
            ang = -180.0 + j * 18.0 + rng.uniform(-5.0, 5.0)
            length = h * rng.uniform(0.16, 0.24)
            tip = polar(*end, length, ang)
            tip = (tip[0], tip[1] + length * 0.55)
            _leaf(leaves, _arch(end, polar(*end, length * 0.5, ang), tip, 8), h * 0.010, 0.4)


def history_lapita(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = LAPITA
    sun_at = (0.30, HORIZON - 0.07)
    reef_v = HORIZON + 0.012
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.85)), (0.26, p["top"]), (0.44, p["mid"]), (HORIZON - 0.02, p["low"]), (HORIZON, mix(p["low"], p["ocean"], 0.5)), (HORIZON + 0.02, p["ocean"]), (1.0, scale(p["ocean"], 0.8))]))
        _sun(a, layer, *sun_at, 0.034, p["sun"], p["glow"], 0.80)
        streaks = cloud_mask(a, "lapita streaks", 0.40, 0.08, cells=2.4, cover=0.34, soft=0.12, stretch=8.0)
        a.tint(layer, streaks, mix(p["cloud_shadow"], p["mid"], 0.4), 0.50)
        a.light(layer, streaks * smoothstep(0.34, 0.48, a.v), p["glow"], 0.55)
        _heaps(a, layer, "lapita heaps", ((0.74, HORIZON - 0.09, 0.05, 0.05),), p["cloud"], p["cloud_shadow"], 0.85)
        # Two volcanic islands far off, and the reef line of white surf.
        isles, isle_pen = a.drawing()
        _volcanic_island(isle_pen, 0.72, HORIZON + 0.002, 0.07, 0.07)
        _volcanic_island(isle_pen, 0.90, HORIZON + 0.002, 0.05, 0.04)
        a.tint(layer, a.mask_of(isles, blur=0.5), mix(p["island"], p["mid"], 0.30), 0.92)
        a.light(layer, a.mask_of(isles, blur=0.5) * smoothstep(0.76, 0.66, a.u), p["glow"], 0.25)
        a.tint(layer, _plume(a, "isle wisp", 0.715, HORIZON - 0.066, 0.06, 0.04, 0.003), p["cloud"], 0.45)
        a.light(layer, smoothstep(HORIZON, HORIZON + 0.004, a.v) * a.spot(sun_at[0], HORIZON + 0.02, 0.18, 1.0, squash=2.0) * smoothstep(0.55, 0.8, a.noise("lapita glints", cells=60.0, octaves=2, stretch=8.0)), p["lagoon_light"], 0.70)
        _textbook(a, layer, 0.06)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far lapita")
        # The lagoon from the reef to the eye.
        lagoon = smoothstep(reef_v - 0.002, reef_v + 0.002, a.v)
        houses, house_pen = a.drawing()
        posts, post_pen = a.drawing()
        boats, boat_pen = a.drawing()
        sails, sail_pen = a.drawing()
        islet, islet_pen = a.drawing()
        palms, palm_pen = a.drawing()
        # A low islet with palms at the left; the village on stilts over the
        # water in front of it; canoes under sail at the right.
        _, iline = a.ridge("lapita islet", reef_v - 0.004, 0.003, cells=3.0, octaves=2)
        islet_pen.poly([(0.0, reef_v + 0.006), (0.0, reef_v - 0.012)] + [(u, _at(iline, u) - 0.008 * math.sin(u / 0.26 * math.pi)) for u in np.linspace(0.0, 0.26, 12)] + [(0.30, reef_v + 0.006)])
        for u in (0.04, 0.09, 0.15, 0.20):
            _coconut_palm(palm_pen, palm_pen, rng, u, reef_v - 0.006, rng.uniform(0.05, 0.07), rng.uniform(-0.01, 0.01))
        village = ((0.25, reef_v + 0.050, 0.026), (0.34, reef_v + 0.036, 0.020), (0.43, reef_v + 0.056, 0.028), (0.51, reef_v + 0.028, 0.015))
        for u, v, w in village:
            _stilt_house(house_pen, post_pen, u, v, w, w * 2.4)
        for u, v, s, f in ((0.64, reef_v + 0.034, 0.08, 1.0), (0.79, reef_v + 0.018, 0.055, -1.0), (0.90, reef_v + 0.056, 0.09, 1.0)):
            _outrigger(boat_pen, sail_pen, u, v, s, f)
        land = np.maximum(a.mask_of(islet), a.mask_of(palms))
        things = np.maximum.reduce([a.mask_of(houses), a.mask_of(posts), a.mask_of(boats), a.mask_of(sails)])
        mask = np.maximum.reduce([lagoon, land, things])
        layer = solid(a, mask, mix(p["lagoon"], p["far"], 0.30), mix(p["lagoon"], p["ocean"], 0.25), reef_v, 1.0, "lapita far", 0.04)
        # The surf on the reef: a line of white that breaks.
        surf = a.band(reef_v + 0.002, 0.004, 1.0) * smoothstep(0.30, 0.55, a.noise("reef surf", cells=40.0, octaves=3, stretch=3.0))
        a.put(layer, surf, p["reef"], 1.0)
        a.put(layer, a.band(reef_v + 0.007, 0.004, 1.0) * lagoon, mix(p["lagoon"], p["reef"], 0.45), 0.6)
        # The sun on the lagoon, and the ripples.
        ripples = smoothstep(0.5, 0.78, a.noise("lagoon ripples", cells=70.0, octaves=2, stretch=9.0))
        a.light(layer, lagoon * ripples * a.spot(sun_at[0], reef_v + 0.05, 0.30, 1.2, squash=0.8), p["lagoon_light"], 0.65)
        a.light(layer, lagoon * ripples * 0.3, p["lagoon_light"], 0.25)
        a.put(layer, land, mix(p["island"], p["far"], 0.30))
        a.put(layer, a.mask_of(posts), mix(p["wood"], p["far"], 0.25))
        a.put(layer, a.mask_of(houses), mix(p["thatch"], p["far"], 0.15))
        a.shade(layer, a.mask_of(houses) * a.rim(a.mask_of(houses), 0.0, -0.003, 0.0), 0.30)
        a.put(layer, a.mask_of(boats), mix(p["wood"], p["far"], 0.25))
        a.put(layer, a.mask_of(sails), mix(p["sail"], p["far"], 0.15))
        a.shade(layer, a.mask_of(sails) * a.rim(a.mask_of(sails), 0.0, -0.002, 0.0), 0.35)
        # Each house and canoe is in the water: its reflection under it.
        reflection = a.shift(np.maximum(a.mask_of(houses), a.mask_of(posts)), 0.0, 0.0)
        flipped = np.zeros_like(reflection)
        for u, v, w in village:
            row = int(v * a.n)
            span = min(row, a.n - row - 1, int(w * 1.6 * a.n))
            c0, c1 = int((u - w * 1.4) * a.n), int((u + w * 1.4) * a.n)
            flipped[row : row + span, c0:c1] = np.maximum(flipped[row : row + span, c0:c1], reflection[row - span : row, c0:c1][::-1])
        wobble = 0.5 + 0.5 * a.noise("reflection wobble", cells=90.0, octaves=1, stretch=6.0)
        a.put(layer, flipped * wobble * lagoon, mix(p["wood"], p["lagoon"], 0.5), 0.45)
        a.light(layer, a.rim(np.maximum(land, things), 0.003, 0.002, 0.5) * np.maximum(land, things), p["glow"], 0.45)
        haze(a, layer, p["low"], 0.10, reef_v + 0.01)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near lapita")
        image, pen = a.drawing()
        crowns, crown_pen = a.drawing()
        leaves, leaf_pen = a.drawing()
        ground, _ = a.ridge("near lapita", 0.705, 0.006, cells=4.0, octaves=3)
        # A mangrove in the water at the left, a pandanus at the right.
        _mangrove(pen, crown_pen, rng, 0.08, 0.72, 0.42)
        _mangrove(pen, crown_pen, rng, 0.20, 0.72, 0.24)
        _pandanus(pen, leaf_pen, rng, 0.90, 0.72, 0.46, -0.06)
        mask = np.maximum.reduce([ground, a.mask_of(image), a.mask_of(crowns), a.mask_of(leaves)])
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.40), p["near"], 0.30, 0.74, "lapita near", 0.08)
        a.put(layer, a.mask_of(crowns), mix(p["island"], p["near"], 0.40))
        a.put(layer, a.mask_of(leaves), mix(p["island_light"], p["near"], 0.50))
        wet = a.band(0.712, 0.006) * ground
        a.light(layer, wet * smoothstep(0.5, 0.8, a.noise("lapita wet", cells=30.0, octaves=2, stretch=4.0)), p["lagoon_light"], 0.30)
        a.light(layer, a.rim(mask, -0.003, 0.002, 0.4) * mask, p["glow"], 0.45)
        a.shade(layer, a.rim(mask, 0.004, -0.003, 1.0) * mask, 0.22)
        haze(a, layer, p["far"], 0.08, 0.73)
        return layer
    layer = _air(a, p, "lapita haze", p["glow"], 0.20, p["near"], 0.22)
    a.put(layer, shafts(a, "lapita shafts", 4, -0.10, 0.0, 0.8, 0.05), p["glow"], 0.10)
    return layer


def lapita_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Tufts of the long leaves of a pandanus that stand from below at a few
    places, each leaf bent over at its end."""
    del layer_lights
    rng = art_.rand("lapita foreground")
    for k in range(3):
        u = (k + rng.uniform(0.2, 0.8)) / 3.0
        for j in range(9):
            ang = -90.0 + (j - 4) * 14.0 + rng.uniform(-4.0, 4.0)
            length = rng.uniform(0.10, 0.14)
            tip = polar(u, REST_BOTTOM + 0.10, length, ang)
            tip = (tip[0], max(tip[1], REST_BOTTOM - 0.012))
            ctrl = polar(u, REST_BOTTOM + 0.10, length * 0.7, ang + (8.0 if ang > -90.0 else -8.0))
            _leaf(pen, [(u, 1.0)] + _arch((u, REST_BOTTOM + 0.10), ctrl, tip, 8), 0.0030, 0.3)


# ---------------------------------------------------------------------------
# 5. The wayfinders: dusk on the open Pacific
# ---------------------------------------------------------------------------


def _swells(a: Art, tag: str, spacing: float, v0: float) -> tuple[np.ndarray, np.ndarray]:
    """The crests and the troughs of long swells on a sea seen from low:
    rows that are close together far off and far apart near."""
    d = np.maximum(a.v - v0, 2e-3)
    wobble = (a.noise((tag, "wobble"), cells=4.0, octaves=3, stretch=4.0) - 0.5) * 2.0
    phase = (spacing / d + wobble) % 1.0
    crest = np.clip(1.0 - np.abs(phase - 0.12) / 0.12, 0.0, 1.0) ** 1.5
    crest = crest * smoothstep(0.35, 0.65, a.noise((tag, "breaks"), cells=18.0, octaves=2, stretch=6.0))
    trough = np.clip(1.0 - np.abs(phase - 0.55) / 0.30, 0.0, 1.0)
    below = smoothstep(v0, v0 + 0.004, a.v)
    return crest * below, trough * below


def history_open_ocean(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = OPEN_OCEAN
    glow_at = (0.42, HORIZON)
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.8)), (0.24, p["top"]), (0.42, p["mid"]), (HORIZON - 0.05, mix(p["mid"], p["low"], 0.55)), (HORIZON - 0.004, p["band"]), (HORIZON + 0.004, p["sea"]), (1.0, p["sea_deep"])]))
        stars(a, layer, 170, p["star"], v_max=0.46, tag="ocean stars")
        # The evening star, low and bright, that the navigators steer by.
        a.light(layer, a.spot(0.20, 0.40, 0.010, 1.4), p["star"], 0.95)
        a.light(layer, a.spot(0.20, 0.40, 0.035, 2.4), p["star"], 0.35)
        a.light(layer, a.spot(*glow_at, 0.40, 2.0, squash=2.6), p["low"], 0.55)
        streaks = cloud_mask(a, "ocean streaks", HORIZON - 0.07, 0.05, cells=2.0, cover=0.30, soft=0.10, stretch=9.0)
        a.tint(layer, streaks, p["cloud"], 0.55)
        a.light(layer, streaks * a.spot(glow_at[0], HORIZON, 0.4, 1.4, squash=2.0), p["cloud_light"], 0.60)
        # A far island on the horizon, and the cloud that stands over it: a
        # navigator sees the cloud before the land.
        isle, _ = a.ridge("ocean isle", HORIZON - 0.008, 0.006, cells=5.0, octaves=2, sharp=0.6)
        a.tint(layer, isle * (a.v < HORIZON + 0.002) * smoothstep(0.050, 0.025, np.abs(a.u - 0.78)), p["island"], 0.92)
        _heaps(a, layer, "isle cloud", ((0.78, HORIZON - 0.012, 0.040, 0.05), (0.785, HORIZON - 0.040, 0.026, 0.06)), p["cloud_light"], p["cloud"], 0.85)
        # The light of the sky on the sea, in a path under the glow.
        crest, _ = _swells(a, "sky swells", 0.08, HORIZON + 0.004)
        a.light(layer, crest * a.spot(glow_at[0], HORIZON + 0.05, 0.30, 1.0, squash=1.6), p["sea_light"], 0.55)
        # Frigatebirds high over the sea.
        birds, bird_pen = a.drawing()
        for u, v, s, beat in ((0.58, 0.33, 0.022, 0.0), (0.66, 0.37, 0.016, 1.0), (0.30, 0.30, 0.012, 0.5)):
            _frigatebird(bird_pen, u, v, s, beat)
        a.put(layer, a.mask_of(birds, blur=0.4), p["bird"], 0.85)
        _textbook(a, layer, 0.04)
        return layer
    if layer_key == "far_backplate":
        # The sea from the horizon to the eye, in long swells; a voyaging
        # canoe far off.
        sea = smoothstep(HORIZON + 0.002, HORIZON + 0.006, a.v)
        crest, trough = _swells(a, "far swells", 0.10, HORIZON + 0.004)
        hull, hull_pen = a.drawing()
        sail, sail_pen = a.drawing()
        _voyaging_canoe(hull_pen, sail_pen, 0.28, HORIZON + 0.026, 0.10, 1.0)
        boat = np.maximum(a.mask_of(hull), a.mask_of(sail))
        mask = np.maximum(sea, boat)
        layer = solid(a, mask, mix(p["sea"], p["far"], 0.30), p["sea_deep"], HORIZON, 1.0, "ocean far", 0.03)
        a.shade(layer, trough * sea, 0.30)
        a.light(layer, crest * sea * a.spot(glow_at[0], HORIZON + 0.08, 0.50, 0.8, squash=1.4), p["sea_light"], 0.55)
        a.light(layer, crest * sea, p["foam"], 0.12)
        a.put(layer, boat, mix(p["bird"], p["far"], 0.35))
        a.light(layer, a.rim(boat, 0.002, 0.0, 0.3) * boat, p["sea_light"], 0.40)
        haze(a, layer, mix(p["mid"], p["low"], 0.3), 0.10, HORIZON + 0.03)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near ocean")
        # Big swells near: the backs of waves that rise at the sides, a low
        # sea in the middle, and foam on the crests.
        chop = 1.0 - np.abs(a.line_noise("near chop", cells=24.0, octaves=2) * 2.0 - 1.0)
        line = 0.705 - 0.006 * chop
        for u, w, h in ((0.04, 0.12, 0.04), (0.24, 0.06, 0.016), (0.78, 0.07, 0.02), (0.97, 0.12, 0.036)):
            t = np.clip((a.u[0] - (u - w)) / (2.0 * w), 0.0, 1.0)
            # A swell has a long back and a steeper front.
            shape = np.clip(np.where(t < 0.62, np.sin(t / 0.62 * math.pi * 0.5), np.cos((t - 0.62) / 0.38 * math.pi * 0.5)), 0.0, 1.0) ** 1.6
            line = np.minimum(line, 0.705 - h * shape)
        mask = _land(a, line)
        layer = solid(a, mask, mix(p["sea"], p["near_light"], 0.25), p["near"], 0.60, 0.74, "ocean near", 0.03)
        # Light comes through the thin top of each wave.
        a.light(layer, mask * smoothstep(0.022, 0.0, a.v - line[None, :]), p["near_light"], 0.45)
        # The backs of the swells take the orange of the sky, their fronts
        # are dark, and foam runs on each crest.
        a.light(layer, mask * smoothstep(0.03, 0.0, a.v - line[None, :]) * a.spot(glow_at[0], 0.66, 0.7, 1.0, squash=1.4), p["sea_light"], 0.40)
        a.light(layer, a.rim(mask, 0.0, 0.003, 0.4) * mask, p["foam"], 0.70)
        foam, foam_pen = a.drawing()
        for _ in range(180):
            u = rng.random()
            foam_pen.ellipse(u, _at(line, u) + rng.uniform(0.0, 0.006), rng.uniform(0.002, 0.007), rng.uniform(0.0008, 0.0018))
        a.light(layer, a.mask_of(foam, blur=0.4) * mask, p["foam"], 0.40)
        streaks = smoothstep(0.55, 0.80, a.noise("near sea streaks", cells=40.0, octaves=2, stretch=12.0))
        a.light(layer, streaks * mask, p["foam"], 0.14)
        haze(a, layer, p["far"], 0.06, 0.73)
        return layer
    layer = _air(a, p, "ocean spray", mix(p["foam"], p["mid"], 0.5), 0.22, p["near"], 0.26)
    return layer


def open_ocean_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Crests of waves that rise from below at a few places, each with a long
    back and a lip that curls over at its front."""
    del layer_lights
    rng = art_.rand("ocean foreground")
    for k in range(3):
        u = (k + rng.uniform(0.2, 0.8)) / 3.0
        w = rng.uniform(0.09, 0.12)
        top = REST_BOTTOM - rng.uniform(0.004, 0.010)
        back = [(u - w + 2.0 * w * 0.7 * t, top + 0.08 * (1.0 - math.sin(t * math.pi * 0.5)) ** 1.4) for t in np.linspace(0.0, 1.0, 10)]
        lip = [(u + w * 0.46, top + 0.004), (u + w * 0.54, top + 0.012), (u + w * 0.50, top + 0.022), (u + w * 0.56, top + 0.05), (u + w * 0.70, top + 0.09)]
        pen.poly([(u - w, 1.0)] + back + lip + [(u + w * 0.70, 1.0)])


# ---------------------------------------------------------------------------
# 6. Rapa Nui: a wide sky over the grass, and the moai
# ---------------------------------------------------------------------------


def _moai(pen: Pen, face: Pen, u: float, v: float, h: float) -> None:
    """A moai from the front: a torso with its arms along its sides, and a
    long head with a heavy brow, a long nose, a strong chin and long ears."""
    w = h * 0.32
    pen.poly([(u - w * 0.50, v), (u + w * 0.50, v), (u + w * 0.48, v - h * 0.50), (u + w * 0.38, v - h * 0.56), (u - w * 0.38, v - h * 0.56), (u - w * 0.48, v - h * 0.50)])
    pen.poly([(u - w * 0.30, v - h * 0.50), (u + w * 0.30, v - h * 0.50), (u + w * 0.36, v - h * 0.62), (u + w * 0.40, v - h * 0.92), (u + w * 0.34, v - h), (u - w * 0.34, v - h), (u - w * 0.40, v - h * 0.92), (u - w * 0.36, v - h * 0.62)])
    for side in (-1.0, 1.0):
        pen.rect(u + side * w * 0.38, v - h * 0.90, u + side * w * 0.46, v - h * 0.64)
    face.rect(u - w * 0.34, v - h * 0.86, u + w * 0.34, v - h * 0.80)
    face.line([(u, v - h * 0.82), (u, v - h * 0.66)], w * 0.10)
    face.line([(u - w * 0.16, v - h * 0.60), (u + w * 0.16, v - h * 0.60)], w * 0.05)
    for side in (-1.0, 1.0):
        face.line([(u + side * w * 0.46, v - h * 0.40), (u + side * w * 0.40, v - h * 0.10)], w * 0.05)


def _moai_head(pen: Pen, u: float, v: float, h: float, tilt: float, facing: float = 1.0) -> None:
    """The head and neck of a moai that stands deep in the earth of the
    slope, as at the quarry, seen from the side: a flat back, a heavy brow,
    a long nose, a short upper lip, a strong chin, and a long ear."""
    f = facing
    profile = ((-0.30, 0.0), (-0.30, -0.80), (-0.22, -1.0), (0.24, -0.98), (0.31, -0.86), (0.22, -0.80), (0.42, -0.50), (0.27, -0.45), (0.31, -0.37), (0.24, -0.33), (0.33, -0.24), (0.20, -0.14), (0.18, 0.0))
    pen.poly(_turn([(u + f * x * h, v + y * h) for x, y in profile], (u, v), tilt))


def _crater(pen: Pen, cliff: Pen, line: np.ndarray, u0: float, u1: float, h: float) -> None:
    """Rano Raraku: a hill of tuff with a crater in it, high at its left
    and broken low at its right, and the face of the quarry on its side."""
    pts = [(u0, _at(line, u0) + 0.004)]
    for k in range(21):
        t = k / 20.0
        u = u0 + (u1 - u0) * t
        rise = math.sin(min(t / 0.45, 1.0) * math.pi * 0.5) ** 0.8 * (1.0 - smoothstep(0.55, 1.0, np.asarray(t)).item() * 0.85)
        dent = 0.25 * math.exp(-((t - 0.52) / 0.07) ** 2)
        pts.append((u, _at(line, u) - h * max(rise - dent, 0.0)))
    pts.append((u1, _at(line, u1) + 0.004))
    pen.poly(pts)
    cliff.poly([(u0 + (u1 - u0) * 0.18, _at(line, u0) - h * 0.70), (u0 + (u1 - u0) * 0.42, _at(line, u0) - h * 0.98), (u0 + (u1 - u0) * 0.50, _at(line, u0) - h * 0.70), (u0 + (u1 - u0) * 0.40, _at(line, u0) - h * 0.40), (u0 + (u1 - u0) * 0.22, _at(line, u0) - h * 0.45)])


def _manavai(pen: Pen, rng, u: float, v: float, w: float, h: float) -> None:
    """A manavai: a round wall of stones laid dry, that keeps the wind off
    the plants in it. The near half of the ring is seen."""
    for row in range(4):
        y = v - row * h * 0.26
        x = u - w + (row % 2) * w * 0.06
        while x < u + w:
            s = w * rng.uniform(0.10, 0.16)
            pen.ellipse(x + s * 0.5, y - h * 0.12, s * 0.62, h * 0.16)
            x += s


def history_rapa_nui(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = RAPA_NUI
    sun_at = (0.86, 0.28)
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.85)), (0.22, p["top"]), (0.44, p["mid"]), (HORIZON - 0.01, p["low"]), (HORIZON, p["sea"]), (1.0, scale(p["sea"], 0.8))]))
        _sun(a, layer, *sun_at, 0.024, p["sun"], p["glow"], 0.55)
        # A wide sky of clouds that the wind draws out in long rows.
        for k, (v0, cover) in enumerate(((0.24, 0.42), (0.34, 0.46), (0.44, 0.44), (0.52, 0.36))):
            rows = cloud_mask(a, ("rapa rows", k), v0, 0.05, cells=3.0, cover=cover, soft=0.10, stretch=5.0)
            a.tint(layer, rows, mix(p["cloud_shadow"], p["mid"], 0.3), 0.55)
            a.light(layer, rows * a.rim(rows, 0.0, 0.006, 0.6), p["cloud"], 0.60)
            a.light(layer, rows * (1.0 - smoothstep(v0 - 0.02, v0 + 0.03, a.v)), p["cloud"], 0.45)
        _heaps(a, layer, "rapa heaps", ((0.16, HORIZON - 0.04, 0.06, 0.05), (0.54, HORIZON - 0.05, 0.05, 0.04)), p["cloud"], p["cloud_shadow"], 0.85)
        glints = smoothstep(0.62, 0.82, a.noise("rapa glints", cells=70.0, octaves=2, stretch=7.0))
        a.light(layer, smoothstep(HORIZON, HORIZON + 0.004, a.v) * glints, p["sea_light"], 0.40)
        _textbook(a, layer, 0.05)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far rapa nui")
        _, line = a.ridge("rapa hills", HORIZON + 0.004, 0.014, cells=2.0, octaves=3)
        # The land ends at the right in sea cliffs; the sea shows behind them.
        coast = 0.90 + 0.02 * (a.line_noise("rapa coast", cells=6.0) - 0.5)
        edge = line + 0.08 * smoothstep(coast - 0.01, coast + 0.01, a.u[0])
        land = _land(a, edge)
        hill, hill_pen = a.drawing()
        quarry, quarry_pen = a.drawing()
        heads, head_pen = a.drawing()
        platform, platform_pen = a.drawing()
        statues, statue_pen = a.drawing()
        faces, face_pen = a.drawing()
        hats, hat_pen = a.drawing()
        _crater(hill_pen, quarry_pen, line, 0.04, 0.38, 0.10)
        # Moai on the lower slope of the crater, deep in the earth.
        for k in range(8):
            u = 0.08 + k * 0.034 + rng.uniform(-0.006, 0.006)
            base = _at(line, u) - 0.004 - 0.012 * math.sin((u - 0.04) / 0.34 * math.pi) + rng.uniform(-0.003, 0.003)
            _moai_head(head_pen, u, base, rng.uniform(0.026, 0.036), rng.uniform(-10.0, 6.0), -1.0 if k % 3 == 1 else 1.0)
        # The ahu by the sea, and its moai with their red topknots, that face
        # inland with their backs to the sea.
        au0, au1 = 0.58, 0.84
        top = min(_at(line, au0), _at(line, au1)) - 0.008
        platform_pen.poly([(au0 - 0.01, _at(line, au0) + 0.004), (au0, top), (au1, top), (au1 + 0.01, _at(line, au1) + 0.004)])
        for k in range(7):
            u = au0 + 0.022 + k * (au1 - au0 - 0.044) / 6.0
            h = rng.uniform(0.046, 0.054)
            _moai(statue_pen, face_pen, u, top, h)
            hat_pen.ellipse(u, top - h - 0.004, h * 0.12, h * 0.07)
        mask = np.maximum.reduce([land, a.mask_of(hill), a.mask_of(heads), a.mask_of(platform), a.mask_of(statues), a.mask_of(hats)])
        layer = solid(a, mask, mix(p["grass_light"], p["far"], 0.30), mix(p["grass"], p["far"], 0.15), HORIZON - 0.08, HORIZON + 0.06, "rapa far", 0.06)
        a.light(layer, land * smoothstep(0.45, 0.75, a.noise("rapa grass", cells=12.0, octaves=3, stretch=3.0)), p["grass_light"], 0.25)
        hill_mask = a.mask_of(hill)
        a.shade(layer, hill_mask * smoothstep(0.20, 0.34, a.u), 0.12)
        quarry_mask = a.mask_of(quarry, blur=0.6) * hill_mask
        a.put(layer, quarry_mask, mix(p["tuff"], p["far"], 0.20), 0.90)
        a.light(layer, quarry_mask * a.rim(quarry_mask, -0.003, 0.0, 0.3), p["tuff_light"], 0.35)
        head_mask = a.mask_of(heads)
        a.put(layer, head_mask, mix(p["moai"], p["tuff"], 0.45))
        a.light(layer, head_mask * a.rim(head_mask, 0.003, 0.0, 0.2), p["tuff_light"], 0.55)
        a.shade(layer, head_mask * a.rim(head_mask, -0.003, 0.0, 0.2), 0.20)
        a.put(layer, a.mask_of(platform), mix(p["ahu"], p["far"], 0.25))
        a.put(layer, a.mask_of(statues), mix(p["moai"], p["far"], 0.15))
        a.shade(layer, a.mask_of(faces, blur=0.3) * a.mask_of(statues), 0.40)
        a.light(layer, a.mask_of(statues) * a.rim(a.mask_of(statues), -0.002, 0.0, 0.0), p["glow"], 0.30)
        a.put(layer, a.mask_of(hats), mix(p["pukao"], p["far"], 0.20))
        # The cliffs at the coast: dark rock that falls to the sea.
        cliff = land * smoothstep(coast[None, :] - 0.02, coast[None, :] + 0.004, a.u) * (a.v > edge[None, :] - 0.004)
        a.put(layer, cliff * smoothstep(0.004, 0.0, np.abs(a.u - coast[None, :]) - 0.012), mix(p["cliff"], p["far"], 0.30), 0.8)
        a.light(layer, a.rim(mask, -0.002, 0.003, 0.5) * mask, p["glow"], 0.35)
        haze(a, layer, p["low"], 0.05, None)
        a.tint(layer, a.band(HORIZON + 0.01, 0.06, 1.4), p["low"], 0.25)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near rapa nui")
        image, pen = a.drawing()
        stones, stone_pen = a.drawing()
        leaves, leaf_pen = a.drawing()
        grass, grass_pen = a.drawing()
        ground, _ = a.ridge("near rapa nui", 0.70, 0.010, cells=4.0, octaves=3)
        # A lava outcrop at the left; a manavai with a banana in it at the
        # right; tussocks of grass that the wind bends.
        pen.poly([(0.0, 0.73), (0.0, 0.52), (0.04, 0.50), (0.09, 0.53), (0.13, 0.58), (0.16, 0.62), (0.19, 0.67), (0.21, 0.73)])
        _banana(leaf_pen, leaf_pen, rng, 0.84, 0.68, 0.14)
        _banana(leaf_pen, leaf_pen, rng, 0.90, 0.68, 0.11)
        _manavai(stone_pen, rng, 0.86, 0.715, 0.08, 0.06)
        for _ in range(20):
            u = rng.choice([rng.uniform(0.20, 0.34), rng.uniform(0.64, 0.76)])
            for k in range(7):
                tip = polar(u, 0.715, rng.uniform(0.015, 0.03), -70.0 + (k - 3) * 9.0)
                grass_pen.line([(u, 0.715), (tip[0] + 0.006, tip[1])], 0.0020)
        mask = np.maximum.reduce([ground, a.mask_of(image), a.mask_of(stones), a.mask_of(leaves), a.mask_of(grass)])
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.40), p["near"], 0.30, 0.74, "rapa near", 0.08)
        rock = a.mask_of(image)
        a.put(layer, rock, mix(p["cliff"], p["near"], 0.55))
        lichen = smoothstep(0.62, 0.72, a.noise("rapa lichen", cells=40.0, octaves=2))
        a.put(layer, rock * lichen, mix((200, 150, 60), p["near"], 0.45), 0.7)
        a.put(layer, a.mask_of(stones), mix(p["ahu"], p["near"], 0.45))
        a.put(layer, a.mask_of(leaves), mix((96, 150, 74), p["near"], 0.45))
        a.put(layer, a.mask_of(grass) * (a.v < 0.71), mix(p["grass_light"], p["near"], 0.45))
        a.light(layer, a.rim(mask, 0.003, 0.003, 0.4) * mask, p["glow"], 0.36)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.22)
        haze(a, layer, p["far"], 0.08, 0.73)
        return layer
    return _air(a, p, "rapa wind", p["low"], 0.16, p["near"], 0.20)


def rapa_nui_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Blades of grass that stand from below and lean hard in the wind."""
    del layer_lights
    rng = art_.rand("rapa foreground")
    for k in range(4):
        u0 = (k + rng.uniform(0.2, 0.8)) / 4.0
        for _ in range(9):
            u = u0 + rng.uniform(-0.025, 0.025)
            top = REST_BOTTOM - rng.uniform(-0.004, 0.012)
            bend = rng.uniform(0.02, 0.04)
            pen.line(_arch((u, 1.0), (u + bend * 0.2, top + 0.05), (u + bend, top), 8), 0.0018)

