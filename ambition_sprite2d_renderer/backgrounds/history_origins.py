"""The scenes of the History dimension, second pass: the places before the
cities.

The second pass of the History dimension is a grid. East is later, and each
floor is a region of the world. These are the rooms of the first people and
the first farmers: ten outdoor places with their own skies, and one painted
cave. They stand beside the eight eras of `history_eras.py`, so they use the
same sepia of an old textbook and the same rules.

- ``history_savanna`` (the Great Rift Valley). A gold dawn. The wall of the
  rift stands at the left, a lake shines under it, flat-topped acacias stand
  on the gold grass, and giraffes walk far off. Smoke goes up from a fire.
- ``history_green_sahara`` (the Sahara when it was green). A bright morning
  of white clouds. A lake with hippos in it, grass to the horizon, herds of
  piebald cattle, and rock shelters of red sandstone with small paintings.
- ``history_ice_age`` (the Ice Age). A pale low sun and an aurora over the
  tundra. A glacier of blue ice fills the far valley, and woolly mammoths
  walk in a line on the snow.
- ``history_megalith`` (the megalith builders). A grey sky with the sun that
  breaks through it. A circle of standing stones on the green downs, a
  longhouse with smoke, a white chalk path, and oak woods.
- ``history_northwoods`` (the Celtic and Viking north). A misty morning in a
  fjord. Steep sides of dark pines, a hillfort with its palisade, and a
  longship with a striped sail on the still water.
- ``history_indus`` (the plains of South Asia). Monsoon clouds over a big
  brown river. A city of red brick stands on its mound, with its citadel and
  its granary, among palms and neem trees. Rain falls far off.
- ``history_yellow_river`` (the Yellow River). Misty mountains in layers, as
  in an ink painting. Terraced hills of yellow loess with cave houses, the
  yellow river, fields of millet and mulberry trees.
- ``history_maize`` (the first farmers of the Americas). A warm afternoon in
  the highlands. A volcano with a plume of smoke, terraces on the far
  mountains, fields of maize, and prickly pear and agave at the sides.
- ``history_sahul`` (ancient Australia). The blue hour after sunset. The
  first stars, the sea crossing behind, red earth, boab and eucalyptus trees,
  a rock shelter with the glow of a fire, and giant wombats far off. There
  are no sacred designs here.
- ``history_highlands`` (the New Guinea highlands). Cloud in the valleys of
  green rainforest mountains. Gardens on raised beds in the swamp, round
  houses, tree ferns, bananas and sugar cane.
- ``history_painted_cave`` (inside, no sky). The back wall of a deep cave in
  torchlight, with horses, aurochs and deer in red ochre and charcoal, and
  stencils of hands. Torches burn on the pillars at the sides.

The bright detail is far off or at the edges, and the middle of each near
layer is calm, so the play in front of it reads. The things that drift in the
air are the room's motes (`terrain/motes.py`), not part of these pictures.
"""

from __future__ import annotations

import math

import numpy as np

from .artkit import Art, Pen, mix, polar, scale, smoothstep
from .history_eras import REST_BOTTOM, _air, _at, _date_palm, _heaps, _plume, _reeds, _sun, _textbook
from .parts import HORIZON, cloud_mask, fog, haze, pine, shafts, solid, stars, vignette

SAVANNA = {
    "top": (38, 70, 118),
    "mid": (122, 146, 168),
    "low": (255, 200, 120),
    "glow": (255, 206, 130),
    "sun": (255, 240, 196),
    "grass": (218, 172, 84),
    "earth": (190, 108, 60),
    "hills": (104, 116, 160),
    "lake": (130, 168, 186),
    "tree": (58, 44, 36),
    "far": (176, 140, 124),
    "near": (54, 34, 22),
    "near_light": (178, 116, 60),
}

GREEN_SAHARA = {
    "top": (34, 112, 186),
    "mid": (110, 180, 220),
    "low": (224, 236, 214),
    "cloud": (255, 255, 250),
    "cloud_shadow": (160, 186, 206),
    "grass": (124, 166, 72),
    "grass_light": (190, 196, 96),
    "rock": (204, 128, 78),
    "rock_shadow": (140, 76, 56),
    "lake": (52, 136, 160),
    "ochre": (170, 60, 40),
    "far": (150, 180, 172),
    "near": (40, 46, 24),
    "near_light": (150, 160, 70),
}

ICE_AGE = {
    "top": (22, 30, 70),
    "mid": (86, 112, 168),
    "low": (236, 222, 212),
    "pink": (226, 176, 182),
    "sun": (255, 250, 236),
    "glow": (255, 230, 200),
    "aurora": (110, 236, 170),
    "aurora_violet": (170, 120, 230),
    "snow": (236, 242, 250),
    "snow_shadow": (150, 170, 206),
    "ice": (130, 196, 230),
    "ice_deep": (60, 120, 180),
    "beast": (82, 58, 48),
    "far": (168, 182, 212),
    "near": (36, 46, 70),
    "near_light": (190, 208, 236),
}

MEGALITH = {
    "top": (88, 98, 116),
    "mid": (146, 154, 164),
    "low": (236, 226, 196),
    "sun": (255, 246, 214),
    "cloud": (196, 200, 204),
    "cloud_shadow": (110, 116, 130),
    "downs": (112, 150, 80),
    "downs_light": (170, 190, 100),
    "chalk": (240, 236, 222),
    "stone": (156, 154, 148),
    "thatch": (176, 140, 84),
    "oak": (58, 80, 46),
    "far": (140, 158, 150),
    "near": (30, 40, 28),
    "near_light": (130, 150, 90),
}

NORTHWOODS = {
    "top": (64, 92, 118),
    "mid": (138, 160, 172),
    "low": (218, 218, 204),
    "sun": (255, 248, 226),
    "water": (58, 86, 104),
    "water_light": (170, 196, 204),
    "cliff": (80, 92, 102),
    "pine": (34, 60, 52),
    "sail_red": (172, 54, 44),
    "sail_white": (232, 226, 210),
    "wood": (110, 74, 48),
    "far": (128, 150, 158),
    "near": (20, 32, 30),
    "near_light": (110, 134, 116),
}

INDUS = {
    "top": (58, 64, 86),
    "mid": (128, 128, 140),
    "low": (248, 204, 150),
    "glow": (255, 214, 150),
    "cloud": (244, 232, 220),
    "cloud_shadow": (86, 92, 116),
    "brick": (190, 98, 62),
    "brick_light": (236, 156, 104),
    "river": (126, 120, 96),
    "river_light": (236, 210, 170),
    "plain": (176, 140, 88),
    "neem": (66, 96, 50),
    "far": (168, 140, 132),
    "near": (60, 30, 22),
    "near_light": (196, 112, 70),
}

YELLOW_RIVER = {
    "top": (118, 150, 160),
    "mid": (188, 200, 190),
    "low": (242, 228, 198),
    "sun": (255, 246, 222),
    "ink": (84, 108, 108),
    "jade": (120, 150, 130),
    "loess": (216, 178, 112),
    "loess_dark": (160, 118, 70),
    "river": (210, 164, 84),
    "millet": (176, 172, 82),
    "mulberry": (64, 98, 62),
    "far": (182, 182, 162),
    "near": (54, 44, 30),
    "near_light": (176, 142, 80),
}

MAIZE = {
    "top": (52, 90, 162),
    "mid": (146, 172, 206),
    "low": (252, 216, 156),
    "glow": (255, 220, 160),
    "sun": (255, 246, 220),
    "volcano": (98, 84, 96),
    "snow": (250, 248, 244),
    "smoke": (214, 206, 204),
    "terrace": (160, 140, 100),
    "terrace_green": (120, 146, 80),
    "maize": (104, 150, 62),
    "tassel": (234, 200, 92),
    "cactus": (82, 130, 92),
    "far": (136, 152, 182),
    "near": (40, 42, 30),
    "near_light": (160, 152, 80),
}

SAHUL = {
    "top": (22, 28, 74),
    "mid": (70, 70, 136),
    "low": (250, 132, 70),
    "band": (255, 186, 110),
    "star": (255, 246, 226),
    "sea": (36, 60, 112),
    "sea_light": (250, 160, 110),
    "earth": (196, 88, 44),
    "earth_dark": (120, 52, 34),
    "gum": (226, 216, 196),
    "leaf": (104, 124, 98),
    "boab": (150, 108, 86),
    "fire": (255, 170, 80),
    "far": (132, 86, 104),
    "near": (36, 18, 18),
    "near_light": (200, 96, 56),
}

HIGHLANDS = {
    "top": (104, 136, 146),
    "mid": (168, 190, 188),
    "low": (222, 228, 216),
    "cloud": (246, 248, 244),
    "cloud_shadow": (170, 186, 186),
    "forest": (54, 96, 66),
    "forest_light": (100, 148, 84),
    "swamp": (96, 116, 96),
    "garden": (110, 150, 70),
    "banana": (96, 156, 74),
    "thatch": (150, 124, 84),
    "far": (126, 160, 146),
    "near": (18, 36, 24),
    "near_light": (96, 146, 74),
}

PAINTED_CAVE = {
    "top": (20, 12, 10),
    "mid": (70, 44, 32),
    "wall": (150, 106, 76),
    "wall_light": (214, 166, 120),
    "rock": (100, 70, 52),
    "ochre": (170, 60, 36),
    "ochre_light": (212, 110, 56),
    "charcoal": (40, 26, 22),
    "torch": (255, 170, 80),
    "glow": (255, 196, 120),
    "near": (30, 18, 14),
    "near_light": (160, 104, 66),
}


# ---------------------------------------------------------------------------
# Parts that more than one place has
# ---------------------------------------------------------------------------


def _land(a: Art, line: np.ndarray) -> np.ndarray:
    """The mask of the land under a ridge line that a scene made itself."""
    return np.clip((a.v - line[None, :]) * a.n + 0.5, 0.0, 1.0).astype(np.float32)


def _layers(a: Art, layer: np.ndarray, tag: str, ranges, colours, fog_colour, fog_amount: float) -> None:
    """Ranges of mountains in layers, each `(base, amp, cells, sharp)`, the far
    one first. As in an ink painting, each range is darkest at its crest and
    goes into the mist at its foot, and the far ranges are pale."""
    for k, ((base, amp, cells, sharp), colour) in enumerate(zip(ranges, colours)):
        mask, _ = a.ridge((tag, k), base, amp, cells=cells, octaves=5, sharp=sharp)
        paint = a.ramp([(0.0, colour), (base - amp, colour), (base + amp * 1.4, mix(colour, fog_colour, fog_amount)), (1.0, mix(colour, fog_colour, fog_amount))])
        a.put(layer, mask, paint)


def _leaf(pen: Pen, rib, width: float, bulge: float = 0.7) -> None:
    """A leaf along the line `rib`: wide in its middle and pointed at its two
    ends. `bulge` less than 1 makes the leaf wider near its base."""
    pts = [np.asarray(p, dtype=float) for p in rib]
    left, right = [], []
    for i, p in enumerate(pts):
        t = i / (len(pts) - 1)
        d = pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]
        n = np.array([-d[1], d[0]]) / max(float(np.hypot(*d)), 1e-9)
        w = width * math.sin(math.pi * t**bulge)
        left.append(tuple(p + n * w))
        right.append(tuple(p - n * w))
    pen.poly(left + right[::-1])


def _arch(start, ctrl, end, steps: int = 10):
    """The points of a curve from `start` to `end` that bends to `ctrl`."""
    out = []
    for i in range(steps + 1):
        t = i / steps
        out.append(((1 - t) ** 2 * start[0] + 2 * (1 - t) * t * ctrl[0] + t * t * end[0], (1 - t) ** 2 * start[1] + 2 * (1 - t) * t * ctrl[1] + t * t * end[1]))
    return out


def _rain(a: Art, tag: object, u0: float, u1: float, v0: float, v1: float, lean: float) -> np.ndarray:
    """Rain that falls from the base of a cloud: thin slanted streaks in a
    soft curtain."""
    slant = a.u - (a.v - v0) * lean
    across = smoothstep(u0, u0 + 0.05, slant) * smoothstep(u1, u1 - 0.05, slant)
    down = smoothstep(v0, v0 + 0.02, a.v) * smoothstep(v1, v1 - 0.08, a.v)
    columns = a.line_noise(tag, cells=60.0, octaves=2)
    index = np.clip((slant % 1.0) * a.n, 0, a.n - 1).astype(int)
    streaks = smoothstep(0.35, 0.75, columns[index])
    return across * down * (0.45 + 0.55 * streaks)


def _acacia(trunk: Pen, crown: Pen, rng, u: float, v: float, h: float, w: float) -> None:
    """An umbrella thorn: a trunk that forks in two or three, and a crown that
    is flat on its top and its base, in layers."""
    fork = (u + rng.uniform(-0.1, 0.1) * w, v - h * 0.42)
    trunk.line([(u, v + 0.01), fork], h * 0.045)
    for k in range(3):
        tip = (u + (k - 1) * w * 0.55 + rng.uniform(-0.1, 0.1) * w, v - h * 0.86)
        trunk.line([fork, ((fork[0] + tip[0]) * 0.5, (fork[1] + tip[1]) * 0.5 + h * 0.02), tip], h * 0.026)
    for k in range(7):
        cu = u + (k / 6.0 - 0.5) * w * 1.5 + rng.uniform(-0.08, 0.08) * w
        cv = v - h * rng.uniform(0.86, 0.98)
        crown.ellipse(cu, cv, w * rng.uniform(0.28, 0.42), h * rng.uniform(0.05, 0.08))
    crown.ellipse(u, v - h * 0.94, w * 0.9, h * 0.06)


def _giraffe(pen: Pen, u: float, v: float, s: float, facing: float = 1.0) -> None:
    """A giraffe that walks: a short body high on long legs, a long neck that
    leans forward, a small head with its horns."""
    f = facing
    pen.ellipse(u, v - s * 1.12, s * 0.48, s * 0.24)
    for du, dk in ((-0.36, 0.06), (-0.22, -0.04), (0.26, 0.05), (0.40, -0.06)):
        pen.line([(u + f * du * s, v - s * 1.0), (u + f * (du + dk) * s, v)], s * 0.07)
    pen.poly([(u + f * 0.24 * s, v - s * 1.30), (u + f * 0.50 * s, v - s * 1.10), (u + f * 0.90 * s, v - s * 2.30), (u + f * 0.78 * s, v - s * 2.36)])
    pen.ellipse(u + f * 0.94 * s, v - s * 2.32, s * 0.17, s * 0.08)
    pen.line([(u + f * 0.82 * s, v - s * 2.36), (u + f * 0.80 * s, v - s * 2.52)], s * 0.04)
    pen.line([(u - f * 0.46 * s, v - s * 1.14), (u - f * 0.56 * s, v - s * 0.70)], s * 0.04)


def _cow(pen: Pen, patches: Pen | None, u: float, v: float, s: float, facing: float = 1.0, graze: bool = False) -> None:
    """A cow of the herders, with horns in the shape of a lyre. `patches`
    gets the white patches of a piebald coat."""
    f = facing
    pen.ellipse(u, v - s * 0.62, s * 0.60, s * 0.26)
    pen.rect(u - s * 0.5, v - s * 0.76, u + s * 0.5, v - s * 0.48)
    for du in (-0.44, -0.30, 0.30, 0.44):
        pen.line([(u + f * du * s, v - s * 0.55), (u + f * du * s, v)], s * 0.08)
    head = (u + f * 0.80 * s, v - s * (0.40 if graze else 0.80))
    pen.line([(u + f * 0.50 * s, v - s * 0.70), head], s * 0.20)
    pen.ellipse(head[0] + f * 0.08 * s, head[1] + s * 0.06, s * 0.13, s * 0.10)
    for side in (-1.0, 1.0):
        pen.line([(head[0] - f * 0.02 * s, head[1] - s * 0.06), (head[0] + side * 0.16 * s, head[1] - s * 0.30), (head[0] + side * 0.10 * s, head[1] - s * 0.48)], s * 0.045)
    pen.line([(u - f * 0.58 * s, v - s * 0.70), (u - f * 0.66 * s, v - s * 0.30)], s * 0.04)
    if patches is not None:
        patches.ellipse(u - f * 0.20 * s, v - s * 0.66, s * 0.22, s * 0.14)
        patches.ellipse(u + f * 0.26 * s, v - s * 0.56, s * 0.14, s * 0.10)


def _hippo(pen: Pen, u: float, v: float, s: float) -> None:
    """A hippo low in the water: a long back, the hump of its head, two small
    ears and the bumps of its eyes."""
    pen.ellipse(u, v, s * 1.0, s * 0.26)
    pen.ellipse(u + s * 0.82, v - s * 0.10, s * 0.36, s * 0.22)
    for du in (0.70, 0.90):
        pen.ellipse(u + s * du, v - s * 0.30, s * 0.06, s * 0.07)
    pen.ellipse(u + s * 0.62, v - s * 0.34, s * 0.05, s * 0.07)


def _shelter(pen: Pen, under: Pen, u: float, v: float, w: float, h: float) -> None:
    """A rock shelter: a block of sandstone with a round top and an overhang,
    and the dark hollow under it."""
    pts = [(u - w, v), (u - w * 0.92, v - h * 0.55), (u - w * 0.70, v - h * 0.92), (u - w * 0.2, v - h), (u + w * 0.45, v - h * 0.96), (u + w * 0.86, v - h * 0.70), (u + w, v - h * 0.30), (u + w * 0.96, v)]
    pen.poly(pts)
    under.poly([(u - w * 0.78, v), (u - w * 0.84, v - h * 0.30), (u - w * 0.50, v - h * 0.50), (u + w * 0.30, v - h * 0.52), (u + w * 0.62, v - h * 0.36), (u + w * 0.70, v)])


def _mammoth(pen: Pen, tusk: Pen, u: float, v: float, s: float, facing: float = 1.0) -> None:
    """A woolly mammoth: a high hump over the shoulders, a domed head, a long
    trunk, a skirt of hair, and tusks that curve out and up."""
    f = facing
    pen.ellipse(u - f * 0.05 * s, v - s * 0.92, s * 0.70, s * 0.46)
    pen.ellipse(u + f * 0.25 * s, v - s * 1.22, s * 0.40, s * 0.34)
    pen.ellipse(u + f * 0.66 * s, v - s * 1.18, s * 0.28, s * 0.34)
    pen.line([(u + f * 0.86 * s, v - s * 1.05), (u + f * 0.98 * s, v - s * 0.55), (u + f * 0.90 * s, v - s * 0.20), (u + f * 0.96 * s, v - s * 0.12)], s * 0.12)
    for du in (-0.52, -0.30, 0.22, 0.46):
        pen.rect(u + f * du * s - s * 0.09, v - s * 0.70, u + f * du * s + s * 0.09, v)
    pen.poly([(u - f * 0.70 * s, v - s * 0.80), (u + f * 0.62 * s, v - s * 0.80), (u + f * 0.55 * s, v - s * 0.36), (u - f * 0.62 * s, v - s * 0.40)])
    pen.line([(u - f * 0.72 * s, v - s * 1.0), (u - f * 0.84 * s, v - s * 0.70)], s * 0.05)
    tusk.line([(u + f * 0.80 * s, v - s * 0.86), (u + f * 1.10 * s, v - s * 0.58), (u + f * 1.38 * s, v - s * 0.70), (u + f * 1.42 * s, v - s * 0.92)], s * 0.07)


def _trilithon(pen: Pen, u: float, v: float, w: float, h: float) -> None:
    """Two standing stones with a lintel over them."""
    for side in (-1.0, 1.0):
        x = u + side * w * 0.32
        pen.poly([(x - w * 0.18, v), (x + w * 0.18, v), (x + w * 0.15, v - h * 0.88), (x - w * 0.15, v - h * 0.88)])
    pen.rect(u - w * 0.52, v - h, u + w * 0.52, v - h * 0.86)


def _longhouse(pen: Pen, door: Pen, u: float, v: float, w: float, h: float) -> None:
    """A longhouse of the first farmers of Europe: low walls of wattle under a
    long, high roof of thatch, and a dark door at its end."""
    pen.rect(u - w, v - h * 0.35, u + w, v)
    pen.poly([(u - w * 1.08, v - h * 0.30), (u - w * 0.80, v - h), (u + w * 0.80, v - h), (u + w * 1.08, v - h * 0.30)])
    door.rect(u - w * 0.84, v - h * 0.28, u - w * 0.70, v)


def _oak(trunk: Pen, crown: Pen, rng, u: float, v: float, h: float) -> None:
    """An oak: a short thick trunk that splits into wide limbs, and a broad
    round crown of many lumps."""
    w = h * 0.08
    trunk.poly([(u - w, v + 0.01), (u + w, v + 0.01), (u + w * 0.6, v - h * 0.40), (u - w * 0.6, v - h * 0.40)])
    for side in (-1.0, 1.0):
        trunk.line([(u, v - h * 0.38), (u + side * h * 0.24, v - h * 0.62)], w * 0.7)
    for _ in range(16):
        ang = rng.uniform(0.0, math.tau)
        r = rng.uniform(0.0, 1.0)
        cu = u + math.cos(ang) * r * h * 0.36
        cv = v - h * 0.70 + math.sin(ang) * r * h * 0.22
        crown.ellipse(cu, cv, h * rng.uniform(0.12, 0.18), h * rng.uniform(0.10, 0.15))


def _longship(pen: Pen, sail: Pen, stripes: Pen, shields: Pen, u: float, v: float, s: float) -> None:
    """A longship: a long low hull with a high stem and stern that curl, one
    square sail with red stripes, and a row of round shields on the side."""
    hull = [(u - s, v - s * 0.10)]
    for k in range(13):
        t = k / 12.0
        hull.append((u - s + 2.0 * s * t, v + s * 0.10 * math.sin(math.pi * t) + s * 0.02))
    hull += [(u + s, v - s * 0.10), (u + s * 1.12, v - s * 0.42), (u + s * 1.06, v - s * 0.48), (u + s * 0.92, v - s * 0.16), (u - s * 0.92, v - s * 0.16), (u - s * 1.06, v - s * 0.48), (u - s * 1.12, v - s * 0.42)]
    pen.poly(hull)
    pen.line([(u, v - s * 0.14), (u, v - s * 1.10)], s * 0.025)
    pen.line([(u - s * 0.40, v - s * 1.02), (u + s * 0.40, v - s * 1.02)], s * 0.02)
    sail.poly([(u - s * 0.40, v - s * 1.02), (u + s * 0.40, v - s * 1.02), (u + s * 0.44, v - s * 0.36), (u - s * 0.36, v - s * 0.34)])
    for k in range(4):
        x0 = u - s * 0.40 + k * s * 0.21
        stripes.poly([(x0, v - s * 1.02), (x0 + s * 0.10, v - s * 1.02), (x0 + s * 0.12, v - s * 0.34), (x0 + s * 0.02, v - s * 0.34)])
    for k in range(9):
        shields.ellipse(u - s * 0.72 + k * s * 0.18, v - s * 0.10, s * 0.07)


def _hillfort(pen: Pen, posts: Pen, u: float, v: float, w: float, h: float) -> None:
    """A hillfort on a round hill: a palisade of posts round its top and two
    roundhouses with cone roofs inside it."""
    pen.poly([(u - w, v), (u - w * 0.55, v - h * 0.70), (u - w * 0.2, v - h), (u + w * 0.25, v - h), (u + w * 0.60, v - h * 0.68), (u + w, v)])
    top = v - h
    for k in range(24):
        x = u - w * 0.36 + k * w * 0.032
        posts.rect(x - w * 0.008, top - h * 0.16, x + w * 0.008, top + h * 0.06)
    for du, r in ((-0.08, 0.10), (0.14, 0.08)):
        cu = u + du * w
        posts.rect(cu - r * w, top - h * 0.12, cu + r * w, top)
        posts.poly([(cu - r * w * 1.25, top - h * 0.12), (cu, top - h * 0.12 - r * w * 1.2), (cu + r * w * 1.25, top - h * 0.12)])


def _city_block(pen: Pen, holes: Pen, rng, u0: float, u1: float, v: float, h0: float, h1: float) -> None:
    """Houses of brick in a row along a street: flat roofs of each height, a
    small dark door or window in some."""
    u = u0
    while u < u1:
        w = rng.uniform(0.008, 0.016)
        h = rng.uniform(h0, h1)
        pen.rect(u, v - h, u + w, v + 0.004)
        if rng.random() < 0.5:
            holes.rect(u + w * 0.35, v - h * 0.55, u + w * 0.6, v - h * 0.30)
        u += w + rng.uniform(0.0, 0.003)


def _neem(trunk: Pen, crown: Pen, rng, u: float, v: float, h: float) -> None:
    """A neem: a straight trunk and a dense round crown."""
    trunk.line([(u, v + 0.01), (u, v - h * 0.55)], h * 0.05)
    for _ in range(12):
        ang = rng.uniform(0.0, math.tau)
        r = rng.uniform(0.0, 1.0)
        crown.ellipse(u + math.cos(ang) * r * h * 0.24, v - h * 0.72 + math.sin(ang) * r * h * 0.18, h * 0.12, h * 0.10)


def _mulberry(trunk: Pen, crown: Pen, rng, u: float, v: float, h: float) -> None:
    """A mulberry kept low for its leaves: a short gnarled trunk, a few bent
    limbs, and leafy clumps at their ends."""
    w = h * 0.07
    trunk.poly([(u - w, v + 0.01), (u + w, v + 0.01), (u + w * 0.8, v - h * 0.35), (u - w * 0.8, v - h * 0.32)])
    ends = []
    for k in range(4):
        ang = -160.0 + k * 45.0 + rng.uniform(-10.0, 10.0)
        mid = polar(u, v - h * 0.34, h * 0.20, ang)
        end = polar(mid[0], mid[1], h * 0.22, ang + rng.uniform(-30.0, 30.0))
        trunk.line([(u, v - h * 0.34), mid, end], w * 0.45)
        ends.append(end)
    for eu, ev in ends:
        for _ in range(4):
            crown.ellipse(eu + rng.uniform(-0.6, 0.6) * h * 0.1, ev + rng.uniform(-0.8, 0.4) * h * 0.08, h * rng.uniform(0.08, 0.12), h * rng.uniform(0.06, 0.09))


def _millet(pen: Pen, rng, u0: float, u1: float, v: float, h: float, count: int) -> None:
    """Millet that stands in a field: thin stalks with heavy heads that bend."""
    for _ in range(count):
        u = rng.uniform(u0, u1)
        top = h * rng.uniform(0.7, 1.0)
        lean = rng.uniform(-0.006, 0.012)
        tip = (u + lean, v - top)
        pen.line([(u, v + 0.01), (u + lean * 0.4, v - top * 0.6), tip], 0.0018)
        pen.line([tip, (tip[0] + 0.006, tip[1] + 0.004), (tip[0] + 0.010, tip[1] + 0.016)], 0.0040)


def _volcano(pen: Pen, snow: Pen, u: float, v: float, w: float, h: float) -> None:
    """A cone of a volcano with a crater at the top and a cap of snow."""
    top = v - h
    pen.poly([(u - w, v), (u - w * 0.30, top + h * 0.12), (u - w * 0.08, top), (u + w * 0.08, top), (u + w * 0.30, top + h * 0.10), (u + w, v)])
    snow.poly([(u - w * 0.30, top + h * 0.12), (u - w * 0.08, top), (u + w * 0.08, top), (u + w * 0.30, top + h * 0.10), (u + w * 0.38, top + h * 0.22), (u + w * 0.26, top + h * 0.19), (u + w * 0.18, top + h * 0.26), (u + w * 0.06, top + h * 0.18), (u - w * 0.08, top + h * 0.26), (u - w * 0.20, top + h * 0.18), (u - w * 0.36, top + h * 0.24)])


def _maize(stalk: Pen, rng, u: float, v: float, h: float) -> None:
    """A plant of maize: a stalk, long leaves that arch out and hang, a
    tassel at the top and a cob on its side."""
    lean = rng.uniform(-0.01, 0.01) * h / 0.3
    top = (u + lean, v - h)
    stalk.line([(u, v + 0.01), (u + lean * 0.5, v - h * 0.5), top], h * 0.022)
    for k in range(6):
        t = 0.18 + k * 0.13
        base = (u + lean * t, v - h * t)
        side = -1.0 if k % 2 else 1.0
        tip = (base[0] + side * h * rng.uniform(0.22, 0.30), base[1] + h * rng.uniform(0.04, 0.12))
        ctrl = (base[0] + side * h * 0.10, base[1] - h * 0.14)
        _leaf(stalk, _arch(base, ctrl, tip), h * 0.022, 0.6)
    for k in range(5):
        stalk.line([top, polar(top[0], top[1], h * 0.09, -90.0 + (k - 2) * 22.0)], h * 0.008)
    cob = (u + lean * 0.55 + h * 0.03, v - h * 0.52)
    stalk.ellipse(cob[0], cob[1], h * 0.022, h * 0.06)


def _nopal(pen: Pen, rng, u: float, v: float, h: float) -> None:
    """A prickly pear: flat round pads that grow on each other, with a few
    red fruits on the top edges."""
    pads = [(u, v - h * 0.22, 0.0)]
    pen.ellipse(u, v - h * 0.22, h * 0.13, h * 0.24)
    for k in range(6):
        pu, pv, _ = pads[rng.randrange(len(pads))]
        ang = rng.uniform(-150.0, -30.0)
        cu, cv = polar(pu, pv, h * 0.30, ang)
        if cv > v - h * 0.20:
            continue
        pads.append((cu, cv, ang))
        pen.ellipse(cu, cv, h * 0.11, h * 0.19)


def _agave(pen: Pen, rng, u: float, v: float, h: float, spike: bool = False) -> None:
    """An agave: a rosette of stiff pointed leaves. With `spike`, a tall
    stalk of flowers stands from its middle."""
    for k in range(11):
        ang = -170.0 + k * 16.0 + rng.uniform(-5.0, 5.0)
        length = h * (0.55 + 0.45 * math.sin(math.radians(-ang))) * rng.uniform(0.85, 1.0)
        tip = polar(u, v, length, ang)
        normal = polar(0.0, 0.0, h * 0.06, ang + 90.0)
        pen.poly([(u - normal[0], v - normal[1]), (u + normal[0], v + normal[1]), tip])
    if spike:
        pen.line([(u, v), (u + h * 0.05, v - h * 3.0)], h * 0.04)
        for k in range(5):
            y = v - h * (1.8 + k * 0.25)
            pen.ellipse(u + h * 0.05 * (1.8 + k * 0.25) / 3.0 + h * 0.12, y, h * 0.10, h * 0.05)
            pen.ellipse(u + h * 0.05 * (1.8 + k * 0.25) / 3.0 - h * 0.10, y + h * 0.04, h * 0.09, h * 0.05)


def _boab(pen: Pen, rng, u: float, v: float, h: float) -> None:
    """A boab: a trunk as fat as a bottle, and short bare limbs at its top
    with a few tufts of leaves."""
    w = h * 0.24
    pen.poly([(u - w * 0.9, v + 0.01), (u - w, v - h * 0.30), (u - w * 0.70, v - h * 0.62), (u - w * 0.36, v - h * 0.70), (u + w * 0.36, v - h * 0.70), (u + w * 0.70, v - h * 0.60), (u + w, v - h * 0.30), (u + w * 0.9, v + 0.01)])
    for k in range(6):
        ang = -160.0 + k * 28.0 + rng.uniform(-8.0, 8.0)
        start = (u + (k / 5.0 - 0.5) * w * 0.8, v - h * 0.68)
        mid = polar(*start, h * 0.16, ang)
        end = polar(*mid, h * 0.12, ang + rng.uniform(-25.0, 25.0))
        pen.line([start, mid, end], h * 0.025)
        pen.ellipse(end[0], end[1], h * 0.05, h * 0.03)


def _gum(trunk: Pen, crown: Pen, rng, u: float, v: float, h: float) -> None:
    """A eucalyptus: a pale trunk that twists, limbs that fork up, and thin
    clumps of leaves that hang from them."""
    w = h * 0.035
    pts = [(u + math.sin(t * 3.0) * h * 0.03, v + 0.01 - h * 0.55 * t) for t in np.linspace(0.0, 1.0, 8)]
    trunk.line(pts, w)
    top = pts[-1]
    for k in range(4):
        ang = -130.0 + k * 27.0 + rng.uniform(-8.0, 8.0)
        mid = polar(*top, h * 0.18, ang)
        end = polar(*mid, h * 0.18, ang + rng.uniform(-20.0, 20.0))
        trunk.line([top, mid, end], w * 0.5)
        for _ in range(3):
            cu, cv = end[0] + rng.uniform(-1.0, 1.0) * h * 0.08, end[1] + rng.uniform(-0.6, 0.6) * h * 0.06
            crown.ellipse(cu, cv, h * rng.uniform(0.06, 0.10), h * rng.uniform(0.04, 0.07))


def _diprotodon(pen: Pen, u: float, v: float, s: float, facing: float = 1.0) -> None:
    """A diprotodon: a wombat as big as a hippo, with a deep body, a large
    head, small ears and short thick legs."""
    f = facing
    pen.ellipse(u, v - s * 0.55, s * 0.80, s * 0.40)
    pen.ellipse(u + f * 0.82 * s, v - s * 0.52, s * 0.30, s * 0.26)
    pen.ellipse(u + f * 1.02 * s, v - s * 0.42, s * 0.14, s * 0.12)
    pen.ellipse(u + f * 0.70 * s, v - s * 0.80, s * 0.07, s * 0.08)
    for du in (-0.50, -0.30, 0.34, 0.56):
        pen.rect(u + f * du * s - s * 0.10, v - s * 0.40, u + f * du * s + s * 0.10, v)


def _tree_fern(trunk: Pen, fronds: Pen, rng, u: float, v: float, h: float, lean: float) -> None:
    """A tree fern: a thin dark trunk, and a crown of long fronds that arch
    out and down, each with fine leaflets."""
    top = (u + lean, v - h)
    trunk.line([(u + lean * t * t, v + 0.01 - (h + 0.01) * t) for t in np.linspace(0.0, 1.0, 8)], h * 0.03)
    for k in range(9):
        ang = -190.0 + k * 25.0 + rng.uniform(-6.0, 6.0)
        length = h * rng.uniform(0.32, 0.42)
        prev = top
        for i in range(1, 11):
            t = i / 10.0
            p = polar(top[0], top[1], length * t, ang)
            p = (p[0], p[1] + length * 0.55 * t * t)
            fronds.line([prev, p], h * 0.010)
            side = h * 0.035 * (1.0 - t * 0.6)
            fronds.line([p, (p[0] + side * 0.6, p[1] + side)], h * 0.006)
            fronds.line([p, (p[0] - side * 0.6, p[1] + side)], h * 0.006)
            prev = p


def _banana(stem: Pen, leaves: Pen, rng, u: float, v: float, h: float) -> None:
    """A banana plant: a stem of leaf sheaths, and big paddle leaves on long
    midribs that arch out; some leaves are torn by the wind."""
    stem.poly([(u - h * 0.04, v + 0.01), (u + h * 0.04, v + 0.01), (u + h * 0.025, v - h * 0.55), (u - h * 0.025, v - h * 0.55)])
    top = (u, v - h * 0.55)
    for k in range(6):
        ang = -165.0 + k * 30.0 + rng.uniform(-8.0, 8.0)
        length = h * rng.uniform(0.40, 0.52)
        tip = polar(*top, length, ang)
        tip = (tip[0], tip[1] + length * 0.45)
        ctrl = polar(*top, length * 0.6, ang)
        ctrl = (ctrl[0], ctrl[1] - length * 0.30)
        rib = _arch(top, ctrl, tip, 12)
        stem.line(rib[:4], h * 0.010)
        _leaf(leaves, rib, h * rng.uniform(0.07, 0.09), 0.9)


def _cane(pen: Pen, rng, u: float, v: float, h: float) -> None:
    """A clump of sugar cane: tall stalks in joints, and long thin leaves."""
    for _ in range(5):
        x = u + rng.uniform(-0.012, 0.012)
        lean = rng.uniform(-0.02, 0.02)
        top = (x + lean, v - h * rng.uniform(0.8, 1.0))
        pen.line([(x, v + 0.01), top], h * 0.012)
        for k in range(3):
            t = 0.55 + k * 0.17
            base = (x + lean * t, v - (v - top[1]) * t)
            side = -1.0 if (k + int(x * 1000)) % 2 else 1.0
            _leaf(pen, _arch(base, (base[0] + side * h * 0.10, base[1] - h * 0.08), (base[0] + side * h * 0.24, base[1] + h * 0.06)), h * 0.010)


def _roundhouse(pen: Pen, u: float, v: float, w: float) -> None:
    """A round house of the highlands: a low wall, and a tall cone of thatch
    with a point at its top."""
    pen.rect(u - w, v - w * 0.45, u + w, v)
    pen.poly([(u - w * 1.15, v - w * 0.40), (u, v - w * 1.5), (u + w * 1.15, v - w * 0.40)])
    pen.line([(u, v - w * 1.5), (u, v - w * 1.75)], w * 0.08)


def _flame(pen: Pen, u: float, v: float, s: float) -> None:
    """A flame on a torch: a tongue that leans a little."""
    pen.poly([(u - s * 0.5, v), (u - s * 0.4, v - s * 0.8), (u - s * 0.05, v - s * 1.4), (u + s * 0.10, v - s * 2.1), (u + s * 0.3, v - s * 1.2), (u + s * 0.5, v - s * 0.6), (u + s * 0.45, v)])


def _paint_horse(pen: Pen, u: float, v: float, s: float, facing: float = 1.0) -> None:
    """A horse as the painters of the caves drew it: a round belly, a short
    neck with a stiff mane, a heavy head, and legs that end in points."""
    f = facing
    pen.ellipse(u, v, s * 0.62, s * 0.30)
    pen.poly([(u + f * 0.40 * s, v - s * 0.20), (u + f * 0.62 * s, v - s * 0.62), (u + f * 0.86 * s, v - s * 0.50), (u + f * 0.66 * s, v - s * 0.06)])
    pen.ellipse(u + f * 0.90 * s, v - s * 0.38, s * 0.16, s * 0.12)
    for du in (-0.40, -0.26, 0.28, 0.42):
        pen.poly([(u + f * du * s - s * 0.05, v + s * 0.16), (u + f * du * s + s * 0.05, v + s * 0.16), (u + f * du * s, v + s * 0.62)])
    pen.line([(u - f * 0.60 * s, v - s * 0.06), (u - f * 0.80 * s, v + s * 0.32)], s * 0.07)


def _paint_aurochs(pen: Pen, u: float, v: float, s: float, facing: float = 1.0) -> None:
    """An aurochs as the painters drew it: a deep chest and a hump, a small
    head with long horns that curve forward."""
    f = facing
    pen.ellipse(u, v, s * 0.75, s * 0.32)
    pen.ellipse(u + f * 0.30 * s, v - s * 0.18, s * 0.42, s * 0.30)
    pen.ellipse(u + f * 0.84 * s, v - s * 0.10, s * 0.15, s * 0.13)
    pen.line([(u + f * 0.82 * s, v - s * 0.20), (u + f * 0.90 * s, v - s * 0.52), (u + f * 1.10 * s, v - s * 0.58)], s * 0.05)
    pen.line([(u + f * 0.86 * s, v - s * 0.20), (u + f * 1.02 * s, v - s * 0.44), (u + f * 1.20 * s, v - s * 0.44)], s * 0.05)
    for du in (-0.50, -0.34, 0.36, 0.52):
        pen.poly([(u + f * du * s - s * 0.06, v + s * 0.18), (u + f * du * s + s * 0.06, v + s * 0.18), (u + f * du * s, v + s * 0.66)])
    pen.line([(u - f * 0.74 * s, v - s * 0.06), (u - f * 0.90 * s, v + s * 0.30)], s * 0.05)


def _paint_deer(pen: Pen, u: float, v: float, s: float, facing: float = 1.0) -> None:
    """A red deer as the painters drew it: a slim body, a neck held up, and
    antlers with many tines."""
    f = facing
    pen.ellipse(u, v, s * 0.50, s * 0.20)
    pen.line([(u + f * 0.40 * s, v - s * 0.08), (u + f * 0.62 * s, v - s * 0.52)], s * 0.12)
    pen.ellipse(u + f * 0.72 * s, v - s * 0.54, s * 0.13, s * 0.07)
    base = (u + f * 0.62 * s, v - s * 0.60)
    for side in (-1.0, 1.0):
        beam = [base, (base[0] + f * side * 0.10 * s - f * 0.10 * s, base[1] - s * 0.30), (base[0] - f * 0.06 * s + side * 0.14 * s, base[1] - s * 0.62)]
        pen.line(beam, s * 0.03)
        for t in (0.3, 0.6):
            p = (beam[0][0] + (beam[2][0] - beam[0][0]) * t, beam[0][1] + (beam[2][1] - beam[0][1]) * t)
            pen.line([p, (p[0] + f * 0.12 * s, p[1] - s * 0.08)], s * 0.025)
    for du in (-0.34, -0.22, 0.24, 0.36):
        pen.line([(u + f * du * s, v + s * 0.10), (u + f * du * s, v + s * 0.56)], s * 0.04)


def _hand(pen: Pen, u: float, v: float, s: float, turn: float) -> None:
    """The shape of a hand with its fingers spread: a palm and five
    fingers. `turn` turns it, in degrees."""
    pen.ellipse(u, v, s * 0.42, s * 0.48)
    for k, (ang, length) in enumerate(((-150.0, 0.55), (-115.0, 0.85), (-92.0, 0.95), (-70.0, 0.88), (-48.0, 0.70))):
        a0 = ang + turn
        start = polar(u, v, s * 0.30, a0)
        end = polar(u, v, s * (0.30 + length), a0)
        pen.line([start, end], s * (0.20 if k else 0.22))


# ---------------------------------------------------------------------------
# 1. The Great Rift Valley: a gold dawn
# ---------------------------------------------------------------------------


def history_savanna(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = SAVANNA
    sun_at = (0.64, HORIZON - 0.07)
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.85)), (0.24, p["top"]), (0.44, p["mid"]), (HORIZON - 0.02, p["low"]), (HORIZON + 0.06, mix(p["low"], p["grass"], 0.6)), (1.0, p["earth"])]))
        _sun(a, layer, *sun_at, 0.045, p["sun"], p["glow"], 0.75)
        streaks = cloud_mask(a, "rift streaks", 0.42, 0.10, cells=2.4, cover=0.30, soft=0.12, stretch=8.0)
        a.tint(layer, streaks, mix(p["mid"], p["hills"], 0.4), 0.45)
        a.light(layer, streaks * smoothstep(0.36, 0.50, a.v), p["glow"], 0.55)
        # The blue hills far off over the valley floor.
        hills, _ = a.ridge("rift far hills", HORIZON - 0.025, 0.02, cells=3.0, octaves=4, sharp=0.4)
        a.tint(layer, hills, mix(p["hills"], p["low"], 0.45), 0.85)
        _textbook(a, layer)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far savanna")
        # The wall of the rift: a high flat edge at the left that falls in a
        # steep scarp to the valley floor.
        _, line = a.ridge("valley floor", HORIZON + 0.02, 0.004, cells=3.0, octaves=3)
        wall = line - 0.11 * smoothstep(0.34, 0.24, a.u[0]) - 0.012 * (a.line_noise("scarp", cells=8.0) - 0.5) * smoothstep(0.36, 0.20, a.u[0])
        ground = _land(a, wall)
        image, pen = a.drawing()
        trees, tree_pen = a.drawing()
        herd, herd_pen = a.drawing()
        # Acacias on the valley floor, and giraffes that walk between them.
        for u in (0.38, 0.45, 0.76, 0.84, 0.90):
            v = _at(line, u) + 0.004
            _acacia(tree_pen, tree_pen, rng, u, v, rng.uniform(0.05, 0.075), rng.uniform(0.028, 0.042))
        for u, s in ((0.56, 0.016), (0.585, 0.013), (0.61, 0.015)):
            _giraffe(herd_pen, u, _at(line, u) + 0.004, s, 1.0)
        # The smoke of a fire at the foot of the scarp.
        smoke = _plume(a, "fire smoke", 0.30, _at(line, 0.30), 0.14, 0.06, 0.004)
        mask = np.maximum.reduce([ground, a.mask_of(image), a.mask_of(trees), a.mask_of(herd)])
        layer = solid(a, mask, mix(p["grass"], p["far"], 0.30), p["grass"], HORIZON - 0.02, HORIZON + 0.06, "rift far", 0.05)
        # The face of the scarp: red rock in bands, in shade at its foot.
        face = ground * smoothstep(0.37, 0.31, a.u) * (a.v < _at(line, 0.3) - 0.002)
        a.put(layer, face, mix(p["earth"], p["far"], 0.35))
        bands = 0.5 + 0.5 * np.sin(a.v * 380.0 + a.noise("scarp bands", cells=8.0) * 4.0)
        a.shade(layer, face * bands, 0.10)
        a.shade(layer, face * smoothstep(HORIZON - 0.06, HORIZON + 0.02, a.v), 0.18)
        a.put(layer, a.mask_of(trees), mix(p["tree"], p["far"], 0.25))
        a.put(layer, a.mask_of(herd), mix(p["tree"], p["far"], 0.25))
        # The lake under the scarp, with the sun in it.
        v0 = _at(line, 0.5) + 0.016
        lake = a.band(v0, 0.012, 0.5) * ground * smoothstep(0.20, 0.30, a.u) * smoothstep(0.80, 0.70, a.u)
        a.put(layer, lake, mix(p["lake"], p["far"], 0.10))
        ripples = smoothstep(0.5, 0.75, a.noise("lake ripples", cells=60.0, octaves=2, stretch=8.0))
        a.light(layer, lake * ripples * a.spot(sun_at[0], v0, 0.25, 1.0, squash=2.0), p["sun"], 0.9)
        a.glow(layer, smoke, mix(p["glow"], p["mid"], 0.5), 0.40)
        a.light(layer, a.rim(mask, -0.003, 0.0015, 0.6) * mask, p["glow"], 0.40)
        haze(a, layer, p["low"], 0.10, HORIZON + 0.04)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near savanna")
        image, pen = a.drawing()
        crowns, crown_pen = a.drawing()
        grass, grass_pen = a.drawing()
        ground, _ = a.ridge("near savanna", 0.70, 0.008, cells=4.0, octaves=3)
        # A great acacia at the left, a smaller one and a termite mound at
        # the right.
        _acacia(pen, crown_pen, rng, 0.10, 0.72, 0.40, 0.11)
        _acacia(pen, crown_pen, rng, 0.90, 0.72, 0.30, 0.08)
        pen.poly([(0.77, 0.72), (0.775, 0.66), (0.782, 0.62), (0.788, 0.63), (0.793, 0.60), (0.80, 0.65), (0.806, 0.72)])
        # Tall gold grass at the sides.
        for _ in range(170):
            u = rng.choice([rng.uniform(0.0, 0.28), rng.uniform(0.72, 1.0)])
            h = rng.uniform(0.02, 0.08)
            lean = rng.uniform(-0.02, 0.02)
            grass_pen.poly([(u - 0.0022, 0.72), (u + 0.0022, 0.72), (u + lean, 0.70 - h)])
        mask = np.maximum.reduce([ground, a.mask_of(image), a.mask_of(crowns), a.mask_of(grass)])
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.40), p["near"], 0.30, 0.74, "savanna near", 0.08)
        a.put(layer, a.mask_of(crowns), mix((70, 80, 44), p["near"], 0.40))
        a.put(layer, a.mask_of(grass) * (a.v < 0.70), mix(p["grass"], p["near"], 0.40))
        a.light(layer, a.rim(mask, -0.003, 0.002, 0.4) * mask, p["glow"], 0.42)
        a.shade(layer, a.rim(mask, 0.004, -0.003, 1.0) * mask, 0.22)
        haze(a, layer, p["far"], 0.08, 0.73)
        return layer
    layer = _air(a, p, "savanna dust", p["glow"], 0.20, p["near"], 0.24)
    a.put(layer, shafts(a, "savanna shafts", 4, 0.10, 0.0, 0.8, 0.05), p["glow"], 0.10)
    return layer


def savanna_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Heads of tall grass that stand from below at a few places."""
    del layer_lights
    rng = art_.rand("savanna foreground")
    for k in range(4):
        u0 = (k + rng.uniform(0.2, 0.8)) / 4.0
        for _ in range(8):
            u = u0 + rng.uniform(-0.03, 0.03)
            top = REST_BOTTOM - rng.uniform(0.0, 0.014)
            lean = rng.uniform(-0.012, 0.012)
            pen.line([(u, 1.0), (u + lean * 0.5, top + 0.02), (u + lean, top)], 0.0016)
            pen.ellipse(u + lean, top + 0.006, 0.0022, 0.008)


# ---------------------------------------------------------------------------
# 2. The Green Sahara: lakes and herds where the desert is now
# ---------------------------------------------------------------------------


def history_green_sahara(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = GREEN_SAHARA
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.85)), (0.25, p["top"]), (0.46, p["mid"]), (HORIZON - 0.01, p["low"]), (HORIZON + 0.05, p["grass_light"]), (1.0, p["grass"])]))
        a.light(layer, a.spot(0.80, 0.18, 0.55, 2.0), p["cloud"], 0.30)
        _heaps(a, layer, "sahara heaps", ((0.20, 0.36, 0.11, 0.12), (0.62, 0.30, 0.09, 0.10), (0.92, 0.40, 0.08, 0.09)), p["cloud"], p["cloud_shadow"])
        _heaps(a, layer, "sahara far heaps", ((0.08, HORIZON - 0.07, 0.04, 0.03), (0.40, HORIZON - 0.08, 0.05, 0.04), (0.76, HORIZON - 0.065, 0.035, 0.025)), mix(p["cloud"], p["low"], 0.3), mix(p["cloud_shadow"], p["low"], 0.45), 0.85)
        _textbook(a, layer, 0.06)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far sahara")
        ground, line = a.ridge("sahara plain", HORIZON + 0.015, 0.005, cells=3.0, octaves=3)
        image, pen = a.drawing()
        under, under_pen = a.drawing()
        herd, herd_pen = a.drawing()
        patches, patch_pen = a.drawing()
        art, art_pen = a.drawing()
        water, water_pen = a.drawing()
        hippos, hippo_pen = a.drawing()
        # Rock shelters of red sandstone at the left and the right, with
        # small cattle painted in the hollow under each one.
        for u, w, h in ((0.19, 0.075, 0.11), (0.29, 0.035, 0.05), (0.82, 0.08, 0.12)):
            v = _at(line, u) + 0.006
            _shelter(pen, under_pen, u, v, w, h)
            for k in range(3):
                _cow(art_pen, None, u - w * 0.40 + k * w * 0.32, v - h * 0.12 - (k % 2) * h * 0.10, h * 0.11, 1.0 if k % 2 else -1.0)
        # A herd of piebald cattle on the grass, and the herders' camp.
        for _ in range(12):
            u = rng.uniform(0.34, 0.56)
            _cow(herd_pen, patch_pen, u, _at(line, u) + rng.uniform(0.004, 0.016), rng.uniform(0.013, 0.017), rng.choice([-1.0, 1.0]), rng.random() < 0.5)
        # The lake, with hippos in it and reeds on its edge.
        v0 = _at(line, 0.7) + 0.02
        water_pen.ellipse(0.70, v0, 0.12, 0.012)
        for u in (0.66, 0.70, 0.735):
            _hippo(hippo_pen, u, v0 - 0.001, 0.008)
        _reeds(herd_pen, rng, 0.58, 0.61, v0, 0.025, 14)
        mask = np.maximum.reduce([ground, a.mask_of(image), a.mask_of(herd)])
        layer = solid(a, mask, mix(p["grass"], p["far"], 0.25), mix(p["grass"], p["grass_light"], 0.35), HORIZON - 0.06, HORIZON + 0.06, "sahara far", 0.05)
        rock = a.mask_of(image)
        a.put(layer, rock, mix(p["rock"], p["far"], 0.25))
        a.shade(layer, rock * (0.5 + 0.5 * np.sin(a.v * 500.0 + a.noise("shelter strata", cells=6.0) * 3.0)), 0.08)
        a.light(layer, a.rim(rock, 0.003, 0.004, 0.5) * rock, p["cloud"], 0.35)
        a.put(layer, a.mask_of(under, blur=0.5) * rock, mix(p["rock_shadow"], p["far"], 0.25))
        a.put(layer, a.mask_of(art, blur=0.2) * a.mask_of(under), mix(p["ochre"], (240, 230, 214), 0.15), 0.9)
        a.put(layer, a.mask_of(herd), mix((90, 54, 36), p["far"], 0.30))
        a.put(layer, a.mask_of(patches) * a.mask_of(herd), mix((240, 232, 214), p["far"], 0.20))
        lake = a.mask_of(water, blur=0.5)
        a.put(layer, lake, mix(p["lake"], p["far"], 0.20))
        a.light(layer, lake * smoothstep(0.5, 0.8, a.noise("sahara ripples", cells=60.0, octaves=2, stretch=8.0)), p["cloud"], 0.5)
        a.put(layer, a.mask_of(hippos), mix((80, 70, 80), p["far"], 0.25))
        waves = smoothstep(0.55, 0.8, a.noise("sahara wind", cells=8.0, octaves=3, stretch=6.0))
        a.light(layer, waves * ground * smoothstep(HORIZON, HORIZON + 0.03, a.v), p["grass_light"], 0.25)
        haze(a, layer, p["low"], 0.12, None)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near sahara")
        image, pen = a.drawing()
        rock, rock_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        grass, grass_pen = a.drawing()
        ground, _ = a.ridge("near sahara", 0.70, 0.008, cells=4.0, octaves=3)
        # A boulder of sandstone at the left, a doum palm and an acacia at the
        # right.
        rock_pen.poly([(0.0, 0.73), (0.0, 0.50), (0.05, 0.46), (0.14, 0.47), (0.19, 0.52), (0.22, 0.60), (0.24, 0.73)])
        _date_palm(pen, crown_pen, rng, 0.93, 0.72, 0.42, -0.02)
        _date_palm(pen, crown_pen, rng, 0.84, 0.72, 0.30, 0.02)
        for _ in range(150):
            u = rng.choice([rng.uniform(0.0, 0.30), rng.uniform(0.70, 1.0)])
            h = rng.uniform(0.02, 0.06)
            lean = rng.uniform(-0.02, 0.02)
            grass_pen.poly([(u - 0.0025, 0.72), (u + 0.0025, 0.72), (u + lean, 0.70 - h)])
        mask = np.maximum.reduce([ground, a.mask_of(image), a.mask_of(rock), a.mask_of(crowns), a.mask_of(grass)])
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.40), p["near"], 0.30, 0.74, "sahara near", 0.08)
        boulder = a.mask_of(rock)
        a.put(layer, boulder, mix(p["rock_shadow"], p["near"], 0.45))
        strata = (0.5 + 0.5 * np.sin(a.v * 300.0 + a.noise("boulder strata", cells=6.0) * 3.0))
        a.shade(layer, boulder * strata, 0.18)
        a.put(layer, a.mask_of(crowns), mix(p["grass"], p["near"], 0.50))
        a.put(layer, a.mask_of(grass) * (a.v < 0.70), mix(p["grass"], p["near"], 0.40))
        a.light(layer, a.rim(mask, 0.002, 0.003, 0.4) * mask, p["cloud"], 0.34)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.22)
        haze(a, layer, p["far"], 0.08, 0.73)
        return layer
    return _air(a, p, "sahara air", p["low"], 0.14, p["near"], 0.20)


def green_sahara_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Grass that stands from below, in tufts, with seed heads."""
    del layer_lights
    rng = art_.rand("sahara foreground")
    for k in range(5):
        u0 = (k + rng.uniform(0.15, 0.85)) / 5.0
        for _ in range(10):
            u = u0 + rng.uniform(-0.025, 0.025)
            h = rng.uniform(0.004, 0.020)
            lean = rng.uniform(-0.014, 0.014)
            pen.poly([(u - 0.0022, 1.0), (u + 0.0022, 1.0), (u + lean * 0.5 + 0.001, REST_BOTTOM - h * 0.4), (u + lean, REST_BOTTOM - h)])


# ---------------------------------------------------------------------------
# 3. The Ice Age: tundra, a glacier and mammoths under an aurora
# ---------------------------------------------------------------------------


def history_ice_age(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = ICE_AGE
    sun_at = (0.55, HORIZON - 0.075)
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, p["top"]), (0.30, mix(p["top"], p["mid"], 0.5)), (0.46, p["mid"]), (HORIZON - 0.06, p["pink"]), (HORIZON - 0.02, p["low"]), (HORIZON + 0.05, p["snow"]), (1.0, p["snow_shadow"])]))
        stars(a, layer, 110, p["sun"], v_max=0.42, tag="ice stars")
        # The aurora: curtains of green light that hang in folds from a
        # line that waves, violet at their tops.
        wave = 0.40 + 0.03 * np.sin(a.u * 8.0 + 1.0) + 0.03 * (a.line_noise("aurora path", cells=4.0)[None, :] - 0.5)
        folds = 0.5 + 0.5 * np.sin(a.u * 120.0 + a.noise("aurora folds", cells=5.0, octaves=2) * 8.0)
        hang = np.clip((a.v - wave + 0.11) / 0.11, 0.0, 1.0) ** 1.5 * np.clip(1.0 - (a.v - wave) / 0.012, 0.0, 1.0)
        curtain = hang * (0.30 + 0.70 * folds) * smoothstep(0.02, 0.20, a.u) * smoothstep(0.98, 0.72, a.u)
        a.light(layer, a.blur(curtain, 3.0), p["aurora"], 0.50)
        a.light(layer, curtain * np.clip(1.0 - (a.v - wave + 0.11) / 0.04, 0.0, 1.0), p["aurora_violet"], 0.40)
        _sun(a, layer, *sun_at, 0.022, p["sun"], p["glow"], 0.50)
        streaks = cloud_mask(a, "ice streaks", HORIZON - 0.05, 0.03, cells=2.0, cover=0.30, soft=0.12, stretch=9.0)
        a.tint(layer, streaks, mix(p["pink"], p["mid"], 0.4), 0.40)
        _textbook(a, layer, 0.05)
        return layer
    if layer_key == "far_backplate":
        ground, line = a.ridge("tundra", HORIZON + 0.02, 0.006, cells=3.0, octaves=3)
        # Dark mountains with caps of snow at each side, and between them the
        # tongue of a glacier that comes down the valley and ends in a cliff
        # of blue ice.
        _, rough = a.ridge("ice peaks", 0.0, 0.025, cells=5.0, octaves=5, sharp=0.7)
        valley = np.clip(np.abs(a.u[0] - 0.53) / 0.30, 0.0, 1.0) ** 1.6
        pline = HORIZON - 0.005 - 0.10 * valley + rough * valley
        rock = _land(a, pline)
        ice_top = HORIZON - 0.012 - 0.03 * valley + 0.004 * (a.line_noise("ice top", cells=10.0) - 0.5)
        ice = _land(a, np.maximum(ice_top, pline + 0.004))
        image, pen = a.drawing()
        tusks, tusk_pen = a.drawing()
        # Mammoths that walk in a line on the snow, and two far off.
        for u, s in ((0.16, 0.026), (0.21, 0.023), (0.255, 0.019), (0.29, 0.014)):
            _mammoth(pen, tusk_pen, u, _at(line, u) + 0.008, s, 1.0)
        for u in (0.72, 0.745):
            _mammoth(pen, tusk_pen, u, _at(line, u) + 0.004, 0.011, -1.0)
        mask = np.maximum.reduce([ground, rock, ice, a.mask_of(image)])
        layer = solid(a, mask, mix(p["snow"], p["far"], 0.35), mix(p["snow"], p["snow_shadow"], 0.3), HORIZON - 0.04, HORIZON + 0.06, "tundra far", 0.04)
        hills = rock * (1.0 - ice) * (1.0 - ground)
        a.put(layer, hills, mix((70, 80, 112), p["far"], 0.40))
        caps = hills * smoothstep(0.004, 0.0, a.v - pline[None, :] - 0.010 - 0.020 * a.noise("snow caps", cells=24.0, octaves=3))
        a.put(layer, caps, mix(p["snow"], p["far"], 0.20), 0.9)
        a.light(layer, a.rim(hills, 0.003, 0.0, 0.3) * hills, p["glow"], 0.35)
        top = ice * (1.0 - ground)
        a.put(layer, top, mix(p["snow"], p["ice"], 0.35))
        face = top * smoothstep(HORIZON - 0.014, HORIZON - 0.004, a.v)
        a.put(layer, face, mix(p["ice"], p["far"], 0.15))
        cracks = np.clip(1.0 - np.abs(((a.u * 110.0 + a.noise("crevasse", cells=14.0) * 3.0) % 1.0) - 0.5) / 0.10, 0.0, 1.0)
        a.put(layer, face * cracks, mix(p["ice_deep"], p["far"], 0.15), 0.7)
        a.light(layer, a.rim(top, 0.0, 0.002, 0.3) * top, p["snow"], 0.6)
        a.put(layer, a.mask_of(image), mix(p["beast"], p["far"], 0.12))
        a.put(layer, a.mask_of(tusks), mix((236, 226, 200), p["far"], 0.15))
        a.light(layer, a.rim(a.mask_of(image), -0.002, 0.0, 0.3), p["glow"], 0.45)
        haze(a, layer, p["low"], 0.10, HORIZON + 0.04)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near ice")
        image, pen = a.drawing()
        hide, hide_pen = a.drawing()
        bones, bone_pen = a.drawing()
        grass, grass_pen = a.drawing()
        ground, _ = a.ridge("near snow", 0.70, 0.010, cells=4.0, octaves=3)
        # Round drifts of snow at the left; at the right, a hut of hides
        # over a frame of mammoth tusks, with jaw bones round its foot.
        for u, r, h in ((0.02, 0.10, 0.14), (0.12, 0.08, 0.08), (0.21, 0.06, 0.04)):
            pen.ellipse(u, 0.72, r, h)
        hide_pen.ellipse(0.86, 0.72, 0.085, 0.075)
        for side in (-1.0, 1.0):
            bone_pen.line(_arch((0.86 + side * 0.08, 0.72), (0.86 + side * 0.06, 0.62), (0.86 - side * 0.02, 0.635)), 0.006)
        door, door_pen = a.drawing()
        door_pen.ellipse(0.86, 0.72, 0.016, 0.03)
        for _ in range(60):
            u = rng.choice([rng.uniform(0.26, 0.34), rng.uniform(0.68, 0.76)])
            h = rng.uniform(0.01, 0.035)
            grass_pen.line([(u, 0.72), (u + rng.uniform(-0.008, 0.008), 0.70 - h)], 0.0016)
        mask = np.maximum.reduce([ground, a.mask_of(image), a.mask_of(hide), a.mask_of(bones), a.mask_of(grass)])
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.55), p["near"], 0.40, 0.74, "snow near", 0.05)
        a.put(layer, a.mask_of(hide), mix((126, 88, 62), p["near"], 0.35))
        a.shade(layer, a.mask_of(door), 0.6)
        a.put(layer, a.mask_of(bones), mix((224, 214, 190), p["near"], 0.40))
        a.put(layer, a.mask_of(grass) * (a.v < 0.70), mix((150, 120, 80), p["near"], 0.45))
        a.light(layer, a.rim(mask, 0.002, 0.004, 0.5) * mask, p["snow"], 0.50)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.20)
        haze(a, layer, p["far"], 0.08, 0.73)
        return layer
    return _air(a, p, "ice mist", p["snow"], 0.20, p["near"], 0.22)


# ---------------------------------------------------------------------------
# 4. The megalith builders: standing stones on the green downs
# ---------------------------------------------------------------------------


def history_megalith(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = MEGALITH
    sun_at = (0.62, 0.30)
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.85)), (0.30, p["top"]), (0.48, p["mid"]), (HORIZON - 0.01, p["low"]), (HORIZON + 0.05, p["downs_light"]), (1.0, p["downs"])]))
        # A low roof of grey cloud, with a gap that the sun breaks through.
        roof = cloud_mask(a, "grey roof", 0.30, 0.20, cells=3.0, cover=0.75, soft=0.20, stretch=3.0)
        gap = a.spot(*sun_at, 0.16, 1.2, squash=1.6)
        a.tint(layer, roof * (1.0 - gap), p["cloud"], 0.65)
        a.shade(layer, roof * (1.0 - gap) * smoothstep(0.20, 0.42, a.v), 0.15)
        _sun(a, layer, *sun_at, 0.020, p["sun"], p["sun"], 0.55)
        a.light(layer, a.rim(roof, 0.0, -0.006, 2.0) * gap * 2.0, p["sun"], 0.7)
        a.light(layer, shafts(a, "megalith shafts", 6, -0.10, 0.30, 0.70, 0.04) * a.spot(sun_at[0], 0.55, 0.30, 1.0, squash=1.2), p["sun"], 0.25)
        _textbook(a, layer, 0.06)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far megalith")
        ground, line = a.ridge("downs", HORIZON + 0.012, 0.020, cells=2.0, octaves=3)
        image, pen = a.drawing()
        stones, stone_pen = a.drawing()
        houses, house_pen = a.drawing()
        doors, door_pen = a.drawing()
        woods, wood_pen = a.drawing()
        # The circle of stones on the crest of the downs: trilithons and
        # single stones.
        cu = 0.52
        cv = _at(line, cu) + 0.004
        for k in range(9):
            t = (k / 8.0 - 0.5) * 2.0
            u = cu + t * 0.075
            v = cv + 0.006 * (1.0 - t * t)
            if k % 3 == 1:
                _trilithon(stone_pen, u, v, 0.026, 0.046)
            else:
                stone_pen.poly([(u - 0.006, v), (u + 0.006, v), (u + 0.005, v - 0.036), (u - 0.005, v - 0.038)])
        # A longhouse with its smoke at the left, and oak woods at the edges.
        smoke = np.zeros((a.n, a.n), dtype=np.float32)
        for k, (u, w) in enumerate(((0.22, 0.040), (0.30, 0.026))):
            v = _at(line, u) + 0.006
            _longhouse(house_pen, door_pen, u, v, w, 0.030)
            smoke = np.maximum(smoke, _plume(a, ("long smoke", k), u, v - 0.03, 0.10, -0.04, 0.004))
        for u0, u1 in ((0.0, 0.14), (0.78, 1.0)):
            for _ in range(10):
                u = rng.uniform(u0, u1)
                _oak(wood_pen, wood_pen, rng, u, _at(line, u) + 0.01, rng.uniform(0.05, 0.08))
        # A white path of chalk that winds up to the circle.
        path, path_pen = a.drawing()
        path_pen.line([(0.40, 1.0), (0.42, HORIZON + 0.08), (0.47, HORIZON + 0.04), (0.50, cv + 0.003)], 0.006)
        mask = np.maximum.reduce([ground, a.mask_of(stones), a.mask_of(houses), a.mask_of(woods)])
        layer = solid(a, mask, mix(p["downs"], p["far"], 0.15), p["downs"], HORIZON - 0.06, HORIZON + 0.08, "downs far", 0.05)
        a.put(layer, a.mask_of(path, blur=1.0) * ground, mix(p["chalk"], p["far"], 0.25), 0.8)
        a.put(layer, a.mask_of(woods), mix(p["oak"], p["far"], 0.35))
        a.put(layer, a.mask_of(houses), mix(p["thatch"], p["far"], 0.30))
        a.shade(layer, a.mask_of(doors), 0.5)
        st = a.mask_of(stones)
        a.put(layer, st, mix(p["stone"], p["cloud_shadow"], 0.35))
        a.shade(layer, st * (a.u > cu), 0.15)
        a.light(layer, a.rim(st, 0.002, 0.0, 0.3) * st, p["sun"], 0.60)
        a.glow(layer, smoke, mix(p["cloud"], p["mid"], 0.3), 0.40)
        # The sun on the downs where the light breaks through.
        a.light(layer, ground * a.spot(sun_at[0], HORIZON + 0.04, 0.25, 1.5, squash=2.0), p["sun"], 0.25)
        haze(a, layer, p["low"], 0.06, HORIZON + 0.03)
        del image, pen
        return layer
    if layer_key == "near_background":
        rng = a.rand("near megalith")
        image, pen = a.drawing()
        crowns, crown_pen = a.drawing()
        fern, fern_pen = a.drawing()
        ground, _ = a.ridge("near downs", 0.70, 0.010, cells=4.0, octaves=3)
        # A great oak at the left and a single standing stone at the right.
        _oak(pen, crown_pen, rng, 0.08, 0.72, 0.50)
        pen.poly([(0.84, 0.73), (0.90, 0.73), (0.895, 0.56), (0.875, 0.50), (0.855, 0.52), (0.845, 0.58)])
        for _ in range(26):
            u = rng.choice([rng.uniform(0.18, 0.30), rng.uniform(0.72, 0.82), rng.uniform(0.92, 1.0)])
            for k in range(5):
                tip = polar(u, 0.72, rng.uniform(0.02, 0.045), -90.0 + (k - 2) * 24.0 + rng.uniform(-6.0, 6.0))
                fern_pen.line([(u, 0.72), tip], 0.0028)
        mask = np.maximum.reduce([ground, a.mask_of(image), a.mask_of(crowns), a.mask_of(fern)])
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.40), p["near"], 0.30, 0.74, "downs near", 0.08)
        a.put(layer, a.mask_of(crowns), mix(p["oak"], p["near"], 0.35))
        stone = a.mask_of(image) * (a.u > 0.82)
        a.put(layer, stone, mix(p["stone"], p["near"], 0.55))
        lichen = smoothstep(0.6, 0.75, a.noise("lichen", cells=40.0, octaves=2)) * stone
        a.put(layer, lichen, mix((190, 190, 120), p["near"], 0.4), 0.5)
        a.put(layer, a.mask_of(fern) * (a.v < 0.71), mix((110, 130, 60), p["near"], 0.45))
        a.light(layer, a.rim(mask, 0.002, 0.004, 0.4) * mask, p["sun"], 0.30)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.22)
        haze(a, layer, p["far"], 0.08, 0.73)
        return layer
    layer = _air(a, p, "downs mist", p["low"], 0.18, p["near"], 0.22)
    return layer


# ---------------------------------------------------------------------------
# 5. The north: a fjord, pines, a hillfort and a longship
# ---------------------------------------------------------------------------


def history_northwoods(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = NORTHWOODS
    water_v = HORIZON + 0.02
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.85)), (0.30, p["top"]), (0.48, p["mid"]), (HORIZON - 0.01, p["low"]), (HORIZON + 0.04, p["water_light"]), (1.0, p["water"])]))
        a.light(layer, a.spot(0.52, 0.46, 0.30, 2.0, squash=1.6), p["sun"], 0.55)
        # The far mountains at the end of the fjord, with snow on their tops.
        _layers(a, layer, "fjord ranges", ((HORIZON - 0.06, 0.035, 4.0, 0.8), (HORIZON - 0.03, 0.025, 5.0, 0.6)), (mix(p["cliff"], p["low"], 0.55), mix(p["cliff"], p["low"], 0.35)), p["low"], 0.7)
        streaks = cloud_mask(a, "north streaks", 0.38, 0.10, cells=2.0, cover=0.40, soft=0.15, stretch=6.0)
        a.tint(layer, streaks, p["low"], 0.35)
        _textbook(a, layer, 0.05)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far north")
        # The steep sides of the fjord, high at the left and at the right,
        # and the low end of it far off. The still water is in front.
        left = HORIZON - 0.03 - 0.14 * smoothstep(0.36, 0.08, a.u[0]) - 0.02 * a.line_noise("left side", cells=6.0)
        right = HORIZON - 0.03 - 0.12 * smoothstep(0.66, 0.92, a.u[0]) - 0.02 * a.line_noise("right side", cells=6.0)
        top = np.minimum(left, right)
        image, pen = a.drawing()
        trees, tree_pen = a.drawing()
        posts, post_pen = a.drawing()
        ship, ship_pen = a.drawing()
        sail, sail_pen = a.drawing()
        stripes, stripe_pen = a.drawing()
        shields, shield_pen = a.drawing()
        # Pines on the slopes.
        for _ in range(90):
            u = rng.choice([rng.uniform(0.0, 0.38), rng.uniform(0.64, 1.0)])
            v = rng.uniform(_at(top, u) + 0.012, water_v + 0.004)
            h = rng.uniform(0.02, 0.04)
            pine(tree_pen, u, v, h, h * 0.42, 4)
        # The hillfort on a knoll at the right.
        _hillfort(pen, post_pen, 0.80, _at(top, 0.80) + 0.03, 0.09, 0.04)
        land = np.maximum.reduce([_land(a, top), a.mask_of(image), a.mask_of(trees)]) * (a.v < water_v)
        # The water mirrors the land: each row under the water line takes the
        # row the same distance over it.
        rows = np.clip(np.rint(2.0 * water_v * a.n - np.arange(a.n)), 0, a.n - 1).astype(int)
        mirror = land[rows, :] * (a.v >= water_v)
        water = (a.v >= water_v).astype(np.float32)
        _longship(ship_pen, sail_pen, stripe_pen, shield_pen, 0.50, water_v + 0.035, 0.035)
        boat = np.maximum(a.mask_of(ship), a.mask_of(sail))
        layer = solid(a, land, mix(p["cliff"], p["far"], 0.40), mix(p["cliff"], p["far"], 0.15), HORIZON - 0.15, HORIZON + 0.02, "fjord far", 0.08)
        a.put(layer, a.mask_of(trees) * land, mix(p["pine"], p["far"], 0.35))
        a.put(layer, a.mask_of(posts), mix(p["wood"], p["far"], 0.30))
        a.light(layer, a.rim(land, -0.002, 0.003, 0.5) * land, p["sun"], 0.25)
        a.put(layer, water, a.ramp([(0.0, p["water_light"]), (water_v, mix(p["water_light"], p["low"], 0.3)), (water_v + 0.08, p["water"]), (1.0, p["water"])]))
        a.put(layer, mirror, mix(p["cliff"], p["water"], 0.55), 0.85)
        ripples = smoothstep(0.55, 0.8, a.noise("fjord ripples", cells=70.0, octaves=2, stretch=10.0)) * water
        a.light(layer, ripples * a.spot(0.52, water_v + 0.02, 0.30, 1.0, squash=1.8), p["water_light"], 0.45)
        a.put(layer, a.mask_of(ship), mix(p["wood"], p["far"], 0.15))
        a.put(layer, a.mask_of(sail), mix(p["sail_white"], p["far"], 0.10))
        a.put(layer, a.mask_of(stripes) * a.mask_of(sail), mix(p["sail_red"], p["far"], 0.10))
        a.put(layer, a.mask_of(shields), mix((200, 170, 70), p["far"], 0.20))
        # The wake of the ship.
        wake = a.band(water_v + 0.037, 0.0025) * smoothstep(0.42, 0.47, a.u) * smoothstep(0.62, 0.53, a.u)
        a.put(layer, wake, p["water_light"], 0.5)
        # Mist that lies on the water at the foot of the slopes.
        a.tint(layer, fog(a, "fjord mist", water_v - 0.006, 0.025, 3.0), p["low"], 0.55)
        haze(a, layer, p["low"], 0.10, None)
        del boat
        return layer
    if layer_key == "near_background":
        rng = a.rand("near north")
        image, pen = a.drawing()
        trees, tree_pen = a.drawing()
        ground, _ = a.ridge("near north", 0.70, 0.010, cells=4.0, octaves=3)
        # Tall pines at both sides, a rock with a runestone at the right.
        for u, h in ((0.03, 0.62), (0.10, 0.48), (0.17, 0.36), (0.88, 0.40), (0.97, 0.58)):
            pine(tree_pen, u, 0.72, h, h * 0.36, 7)
        pen.poly([(0.74, 0.73), (0.745, 0.62), (0.755, 0.585), (0.775, 0.58), (0.785, 0.61), (0.79, 0.73)])
        pen.poly([(0.66, 0.73), (0.68, 0.69), (0.72, 0.68), (0.76, 0.70), (0.80, 0.73)])
        mask = np.maximum.reduce([ground, a.mask_of(image), a.mask_of(trees)])
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.35), p["near"], 0.30, 0.74, "north near", 0.08)
        a.put(layer, a.mask_of(trees), mix(p["pine"], p["near"], 0.45))
        stone = a.mask_of(image) * (a.v < 0.68) * (np.abs(a.u - 0.767) < 0.03)
        a.put(layer, stone, mix((110, 116, 120), p["near"], 0.5))
        # A band of carving that runs up one side of the stone and down the
        # other, painted red.
        carve, carve_pen = a.drawing()
        carve_pen.arc(0.767, 0.612, 0.010, 180.0, 360.0, 0.002)
        for x in (0.757, 0.777):
            carve_pen.line([(x, 0.612), (x, 0.672)], 0.002)
        a.put(layer, a.mask_of(carve) * stone, mix(p["sail_red"], p["near"], 0.30), 0.85)
        a.light(layer, a.rim(mask, -0.002, 0.003, 0.4) * mask, p["low"], 0.30)
        a.shade(layer, a.rim(mask, 0.004, -0.003, 1.0) * mask, 0.22)
        haze(a, layer, p["far"], 0.10, 0.73)
        return layer
    return _air(a, p, "north mist", p["low"], 0.26, p["near"], 0.26)


def northwoods_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Boughs of pine that hang from above at two places."""
    del layer_lights
    rng = art_.rand("north foreground")
    for k in range(2):
        u0 = (k + rng.uniform(0.25, 0.75)) / 2.0
        end = (u0 + rng.uniform(0.08, 0.12) * (1 if k else -1), 0.385)
        start = (u0, 0.0)
        pen.line([start, ((start[0] + end[0]) * 0.5, 0.30), end], 0.004)
        for i in range(24):
            t = i / 24.0
            x = start[0] + (end[0] - start[0]) * t
            y = 0.30 * t / 0.5 if t < 0.5 else 0.30 + (end[1] - 0.30) * (t - 0.5) / 0.5
            for side in (-1.0, 1.0):
                pen.line([(x, y), (x + side * 0.010, y + 0.016)], 0.0013)


# ---------------------------------------------------------------------------
# 6. The plains of South Asia: a brick city under the monsoon
# ---------------------------------------------------------------------------


def history_indus(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = INDUS
    sun_at = (0.36, 0.44)
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.85)), (0.30, p["top"]), (0.48, p["mid"]), (HORIZON - 0.01, p["low"]), (HORIZON + 0.05, mix(p["low"], p["plain"], 0.6)), (1.0, p["plain"])]))
        a.light(layer, a.spot(*sun_at, 0.30, 2.0, squash=1.6), p["glow"], 0.45)
        # Towers of monsoon cloud, dark at their bases, and rain under the
        # one at the right.
        # A bank of monsoon cloud: towers that rise from a dark, flat base,
        # their tops lit by the sun; and rain under the bank at the right.
        base = 0.45 + 0.012 * (a.line_noise("monsoon base", cells=5.0)[None, :] - 0.5)
        tops = 0.22 + 0.10 * a.line_noise("monsoon tops", cells=7.0, octaves=4)[None, :]
        lumps = a.noise("monsoon lumps", cells=14.0, octaves=4)
        bank = smoothstep(-0.01, 0.01, a.v - tops - (lumps - 0.5) * 0.05) * smoothstep(0.012, -0.004, a.v - base)
        bank *= np.maximum(smoothstep(0.30, 0.22, a.u), smoothstep(0.50, 0.58, a.u))
        lit = np.clip(1.0 - (a.v - tops) / np.maximum(base - tops, 0.05), 0.0, 1.0) ** 1.4
        paint = a.flat(p["cloud_shadow"]) + (a.flat(p["cloud"]) - a.flat(p["cloud_shadow"])) * (lit * (0.6 + 0.4 * lumps))[:, :, None]
        a.put(layer, a.blur(bank, 2.0), paint, 0.95)
        a.light(layer, a.rim(bank, 0.004, 0.006, 3.0) * bank, p["glow"], 0.45)
        a.tint(layer, _rain(a, "monsoon rain", 0.62, 0.86, 0.45, HORIZON + 0.01, 0.10), mix(p["cloud_shadow"], p["mid"], 0.4), 0.50)
        a.light(layer, shafts(a, "indus shafts", 3, 0.08, 0.36, 0.62, 0.04) * a.spot(sun_at[0], 0.52, 0.30, 1.0), p["glow"], 0.25)
        _textbook(a, layer, 0.07)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far indus")
        ground, line = a.ridge("indus plain", HORIZON + 0.010, 0.004, cells=3.0, octaves=3)
        image, pen = a.drawing()
        holes, hole_pen = a.drawing()
        trees, tree_pen = a.drawing()
        mound, mound_pen = a.drawing()
        # The city on its mound: the citadel at the left with the granary on
        # it, and the lower town of streets in a grid to the right.
        base = _at(line, 0.45) + 0.004
        mound_pen.poly([(0.16, base), (0.20, base - 0.034), (0.36, base - 0.038), (0.40, base - 0.012), (0.68, base - 0.014), (0.72, base)])
        # The citadel: a wall with towers, the granary on its blocks, and a
        # tall house with steps.
        pen.rect(0.20, base - 0.050, 0.37, base - 0.034)
        for u in (0.20, 0.25, 0.31, 0.37):
            pen.rect(u - 0.006, base - 0.058, u + 0.006, base - 0.034)
        pen.rect(0.255, base - 0.074, 0.31, base - 0.050)
        for k in range(7):
            hole_pen.rect(0.258 + k * 0.0075, base - 0.072, 0.261 + k * 0.0075, base - 0.054)
        pen.rect(0.33, base - 0.070, 0.35, base - 0.050)
        _city_block(pen, hole_pen, rng, 0.40, 0.67, base - 0.012, 0.012, 0.028)
        # Palms and neem trees on the plain.
        for u in (0.05, 0.11, 0.74, 0.80, 0.93):
            v = _at(line, u) + 0.004
            if rng.random() < 0.5:
                _date_palm(tree_pen, tree_pen, rng, u, v, rng.uniform(0.04, 0.06), rng.uniform(-0.006, 0.006), 9)
            else:
                _neem(tree_pen, tree_pen, rng, u, v, rng.uniform(0.04, 0.06))
        mask = np.maximum.reduce([ground, a.mask_of(image), a.mask_of(mound), a.mask_of(trees)])
        layer = solid(a, mask, mix(p["plain"], p["far"], 0.40), mix(p["plain"], p["low"], 0.15), HORIZON - 0.08, HORIZON + 0.06, "indus far", 0.05)
        city = np.maximum(a.mask_of(image), a.mask_of(mound))
        a.put(layer, city, mix(p["brick"], p["far"], 0.15))
        courses = ((a.v * 900.0) % 1.0 < 0.3).astype(np.float32)
        a.shade(layer, city * courses, 0.08)
        a.shade(layer, a.mask_of(holes) * city, 0.40)
        a.light(layer, a.rim(city, 0.002, 0.002, 0.3) * city, p["brick_light"], 0.40)
        a.put(layer, a.mask_of(trees), mix(p["neem"], p["far"], 0.35))
        # The wide brown river in front of the city.
        v0 = _at(line, 0.5) + 0.03
        river = a.band(v0, 0.016, 0.4) * ground
        a.put(layer, river, mix(p["river"], p["far"], 0.10))
        a.light(layer, river * smoothstep(0.55, 0.8, a.noise("indus ripples", cells=60.0, octaves=2, stretch=8.0)) * a.spot(sun_at[0], v0, 0.3, 1.0, squash=2.0), p["river_light"], 0.7)
        haze(a, layer, p["low"], 0.10, HORIZON + 0.04)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near indus")
        image, pen = a.drawing()
        crowns, crown_pen = a.drawing()
        ground, _ = a.ridge("near indus", 0.70, 0.008, cells=4.0, octaves=3)
        # A wall of brick at the left with a round well in front of it; a neem
        # and a palm at the right.
        pen.poly([(0.0, 0.74), (0.0, 0.52), (0.12, 0.52), (0.12, 0.56), (0.17, 0.56), (0.17, 0.62), (0.20, 0.62), (0.20, 0.74)])
        pen.rect(0.24, 0.665, 0.30, 0.74)
        pen.ellipse(0.27, 0.665, 0.030, 0.006)
        _neem(pen, crown_pen, rng, 0.84, 0.72, 0.40)
        _date_palm(pen, crown_pen, rng, 0.95, 0.72, 0.46, -0.03)
        mask = np.maximum.reduce([ground, a.mask_of(image), a.mask_of(crowns)])
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.40), p["near"], 0.30, 0.74, "indus near", 0.08)
        wall = a.mask_of(image) * (a.u < 0.31) * (a.v < 0.72)
        a.put(layer, wall, mix(p["brick"], p["near"], 0.45))
        # English bond: a course of headers, a course of stretchers.
        row = np.floor(a.v * 160.0)
        joint = ((a.v * 160.0) % 1.0 < 0.14) | (((a.u * np.where(row % 2 == 0, 160.0, 80.0)) % 1.0) < 0.08)
        a.shade(layer, wall * joint.astype(np.float32), 0.32)
        a.put(layer, a.mask_of(crowns), mix(p["neem"], p["near"], 0.40))
        a.light(layer, a.rim(mask, 0.003, 0.002, 0.4) * mask, p["glow"], 0.34)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.22)
        haze(a, layer, p["far"], 0.08, 0.73)
        return layer
    return _air(a, p, "monsoon damp", p["low"], 0.20, p["near"], 0.24)


# ---------------------------------------------------------------------------
# 7. The Yellow River: loess hills and misty mountains
# ---------------------------------------------------------------------------


def history_yellow_river(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = YELLOW_RIVER
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.9)), (0.30, p["top"]), (0.46, p["mid"]), (HORIZON - 0.01, p["low"]), (HORIZON + 0.05, p["loess"]), (1.0, p["loess_dark"])]))
        _sun(a, layer, 0.78, 0.34, 0.03, p["sun"], p["low"], 0.40)
        # Ranges of misty mountains in layers, tall and steep, the far ones
        # pale, as in an ink painting.
        _layers(a, layer, "ink ranges", ((0.40, 0.07, 3.0, 0.9), (0.47, 0.06, 4.0, 0.85), (0.54, 0.05, 5.0, 0.8)), (mix(p["ink"], p["low"], 0.75), mix(p["ink"], p["low"], 0.60), mix(p["jade"], p["low"], 0.45)), p["low"], 0.75)
        _textbook(a, layer, 0.08)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far yellow")
        # Loess hills, flat on their tops and cut in terraces, with cave
        # houses in their faces.
        hills, line = a.ridge("loess hills", HORIZON - 0.01, 0.025, cells=3.0, octaves=3)
        image, pen = a.drawing()
        doors, door_pen = a.drawing()
        trees, tree_pen = a.drawing()
        field, field_pen = a.drawing()
        for k in range(8):
            u = 0.06 + k * 0.035 + rng.uniform(-0.006, 0.006)
            if 0.30 < u < 0.62:
                continue
            v = _at(line, u) + 0.03 + rng.uniform(0.0, 0.02)
            door_pen.ellipse(u, v - 0.006, 0.005, 0.006)
            door_pen.rect(u - 0.005, v - 0.006, u + 0.005, v)
        for u in (0.68, 0.72, 0.90):
            _mulberry(tree_pen, tree_pen, rng, u, HORIZON + 0.045, rng.uniform(0.035, 0.05))
        _millet(field_pen, rng, 0.74, 0.88, HORIZON + 0.05, 0.02, 60)
        mask = np.maximum.reduce([hills, a.mask_of(trees), a.mask_of(field)])
        layer = solid(a, mask, mix(p["loess"], p["far"], 0.35), mix(p["loess"], p["loess_dark"], 0.3), HORIZON - 0.06, HORIZON + 0.08, "loess far", 0.05)
        # The terraces: level steps that follow the hills, each with a light
        # lip and green crops on it.
        steps = (a.v - line[None, :] * 0.6) * 220.0
        lip = (steps % 1.0 < 0.18).astype(np.float32) * hills
        a.light(layer, lip, p["low"], 0.30)
        a.shade(layer, ((steps % 1.0) > 0.85).astype(np.float32) * hills, 0.18)
        crops = smoothstep(0.5, 0.65, a.noise("terrace crops", cells=10.0, octaves=3, stretch=3.0)) * hills * (a.v < HORIZON + 0.03)
        a.put(layer, crops * ((steps % 1.0) < 0.5), mix(p["millet"], p["far"], 0.30), 0.55)
        a.shade(layer, a.mask_of(doors, blur=0.3) * hills, 0.55)
        a.put(layer, a.mask_of(trees), mix(p["mulberry"], p["far"], 0.35))
        a.put(layer, a.mask_of(field), mix(p["millet"], p["far"], 0.25))
        # The yellow river that winds out of the hills.
        river, river_pen = a.drawing()
        river_pen.line([(0.36, HORIZON + 0.02), (0.44, HORIZON + 0.03), (0.40, HORIZON + 0.045), (0.52, HORIZON + 0.06), (0.62, HORIZON + 0.08)], 0.012)
        rv = a.mask_of(river, blur=1.5) * hills
        a.put(layer, rv, mix(p["river"], p["far"], 0.20))
        a.light(layer, rv * smoothstep(0.55, 0.8, a.noise("yellow ripples", cells=50.0, octaves=2, stretch=6.0)), p["sun"], 0.35)
        a.tint(layer, fog(a, "loess mist", HORIZON + 0.005, 0.03, 3.0), p["low"], 0.40)
        a.light(layer, a.rim(mask, 0.002, 0.003, 0.5) * mask, p["sun"], 0.30)
        haze(a, layer, p["low"], 0.14, None)
        del image, pen
        return layer
    if layer_key == "near_background":
        rng = a.rand("near yellow")
        image, pen = a.drawing()
        crowns, crown_pen = a.drawing()
        stalks, stalk_pen = a.drawing()
        ground, _ = a.ridge("near loess", 0.70, 0.008, cells=4.0, octaves=3)
        # A face of loess at the left, cut straight down, with a cave door;
        # a mulberry and a stand of millet at the right.
        pen.poly([(0.0, 0.74), (0.0, 0.48), (0.10, 0.48), (0.13, 0.50), (0.16, 0.50), (0.16, 0.74)])
        _mulberry(pen, crown_pen, rng, 0.88, 0.72, 0.34)
        _millet(stalk_pen, rng, 0.70, 0.80, 0.72, 0.10, 40)
        _millet(stalk_pen, rng, 0.18, 0.28, 0.72, 0.08, 30)
        mask = np.maximum.reduce([ground, a.mask_of(image), a.mask_of(crowns), a.mask_of(stalks)])
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.40), p["near"], 0.30, 0.74, "loess near", 0.08)
        face = a.mask_of(image) * (a.u < 0.17) * (a.v < 0.72)
        a.put(layer, face, mix(p["loess_dark"], p["near"], 0.45))
        a.shade(layer, face * np.clip(1.0 - np.abs(((a.u * 120.0 + a.noise("loess joints", cells=8.0) * 2.0) % 1.0) - 0.5) / 0.06, 0.0, 1.0), 0.25)
        cave, cave_pen = a.drawing()
        cave_pen.ellipse(0.075, 0.62, 0.030, 0.035)
        cave_pen.rect(0.045, 0.62, 0.105, 0.72)
        a.shade(layer, a.mask_of(cave, blur=0.5) * face, 0.55)
        a.put(layer, a.mask_of(crowns), mix(p["mulberry"], p["near"], 0.40))
        a.put(layer, a.mask_of(stalks) * (a.v < 0.71), mix(p["millet"], p["near"], 0.45))
        a.light(layer, a.rim(mask, 0.002, 0.003, 0.4) * mask, p["low"], 0.34)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.22)
        haze(a, layer, p["far"], 0.10, 0.73)
        return layer
    return _air(a, p, "loess haze", p["low"], 0.24, p["near"], 0.22)


def yellow_river_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Heads of millet that stand from below and bend."""
    del layer_lights
    rng = art_.rand("yellow foreground")
    for k in range(4):
        u0 = (k + rng.uniform(0.2, 0.8)) / 4.0
        for _ in range(6):
            u = u0 + rng.uniform(-0.025, 0.025)
            top = REST_BOTTOM - rng.uniform(0.0, 0.012)
            lean = rng.uniform(-0.006, 0.010)
            tip = (u + lean, top)
            pen.line([(u, 1.0), (u + lean * 0.5, top + 0.03), tip], 0.0018)
            pen.line([tip, (tip[0] + 0.006, tip[1] + 0.004), (tip[0] + 0.010, tip[1] + 0.020)], 0.0042)


# ---------------------------------------------------------------------------
# 8. The first maize: a volcano over the highland fields
# ---------------------------------------------------------------------------


def history_maize(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = MAIZE
    sun_at = (0.20, 0.36)
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.85)), (0.26, p["top"]), (0.46, p["mid"]), (HORIZON - 0.01, p["low"]), (HORIZON + 0.05, mix(p["low"], p["terrace"], 0.6)), (1.0, p["terrace"])]))
        _sun(a, layer, *sun_at, 0.028, p["sun"], p["glow"], 0.60)
        _heaps(a, layer, "maize heaps", ((0.42, 0.34, 0.07, 0.07), (0.80, 0.40, 0.05, 0.045)), mix(p["snow"], p["glow"], 0.3), mix(p["mid"], p["volcano"], 0.3), 0.9)
        # The far mountains, with the lines of terraces on their sides.
        far, fline = a.ridge("andes", HORIZON - 0.04, 0.035, cells=4.0, octaves=5, sharp=0.6)
        a.tint(layer, far, mix(p["far"], p["low"], 0.35), 0.75)
        steps = (a.v - fline[None, :] * 0.5) * 160.0
        lines = np.clip(1.0 - np.abs(steps % 1.0 - 0.5) / 0.18, 0.0, 1.0) * far * smoothstep(0.30, 0.6, a.noise("terrace patches", cells=6.0, octaves=2))
        a.tint(layer, lines, mix(p["terrace_green"], p["far"], 0.45), 0.25)
        _textbook(a, layer, 0.06)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far maize")
        ground, line = a.ridge("maize valley", HORIZON + 0.015, 0.008, cells=3.0, octaves=3)
        image, pen = a.drawing()
        snow, snow_pen = a.drawing()
        field, field_pen = a.drawing()
        # The volcano, and the plume of smoke that leans from it.
        vu = 0.64
        _volcano(pen, snow_pen, vu, _at(line, vu) + 0.01, 0.17, 0.16)
        puffs, puff_pen = a.drawing()
        crater = _at(line, vu) + 0.01 - 0.16
        for i in range(12):
            t = i / 11.0
            puff_pen.ellipse(vu + 0.12 * t**1.4 + rng.uniform(-0.004, 0.004), crater - 0.12 * t, 0.006 + 0.024 * t, 0.005 + 0.016 * t, value=int(255 * (1.0 - 0.55 * t)))
        plume = a.mask_of(puffs, blur=3.0) * (0.75 + 0.25 * a.noise("plume lumps", cells=40.0, octaves=2))
        # Fields of maize in rows on the valley floor.
        for _ in range(140):
            u = rng.uniform(0.0, 1.0)
            if 0.35 < u < 0.55:
                continue
            v = _at(line, u) + rng.uniform(0.006, 0.03)
            h = rng.uniform(0.012, 0.02) * (1.0 + (v - HORIZON) * 8.0)
            field_pen.line([(u, v), (u, v - h)], 0.0016)
            field_pen.line([(u, v - h * 0.6), (u + h * 0.35, v - h * 0.4)], 0.0012)
            field_pen.line([(u, v - h * 0.5), (u - h * 0.35, v - h * 0.3)], 0.0012)
        mask = np.maximum.reduce([ground, a.mask_of(image), a.mask_of(field)])
        layer = solid(a, mask, mix(p["terrace"], p["far"], 0.30), mix(p["terrace"], p["terrace_green"], 0.35), HORIZON - 0.10, HORIZON + 0.06, "maize far", 0.05)
        cone = a.mask_of(image)
        a.put(layer, cone, mix(p["volcano"], p["far"], 0.35))
        a.light(layer, cone * smoothstep(vu + 0.02, vu - 0.10, a.u), p["glow"], 0.25)
        a.shade(layer, cone * smoothstep(vu - 0.01, vu + 0.08, a.u), 0.18)
        a.shade(layer, cone * smoothstep(0.55, 0.8, a.noise("cone gullies", cells=30.0, octaves=2, stretch=0.2)), 0.10)
        a.put(layer, a.mask_of(snow, blur=0.4), mix(p["snow"], p["far"], 0.10))
        a.glow(layer, plume, mix(p["smoke"], p["mid"], 0.20), 0.85)
        a.put(layer, a.mask_of(field), mix(p["maize"], p["far"], 0.30))
        a.light(layer, a.rim(mask, 0.003, 0.002, 0.5) * mask, p["glow"], 0.35)
        haze(a, layer, p["low"], 0.12, HORIZON + 0.04)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near maize")
        image, pen = a.drawing()
        plants, plant_pen = a.drawing()
        cactus, cactus_pen = a.drawing()
        ground, _ = a.ridge("near maize", 0.70, 0.008, cells=4.0, octaves=3)
        # A prickly pear and an agave in flower at the left; maize at the
        # right, and a terrace wall of stone at the foot.
        _nopal(cactus_pen, rng, 0.08, 0.72, 0.36)
        _agave(cactus_pen, rng, 0.20, 0.72, 0.08, spike=True)
        for u in (0.80, 0.86, 0.92, 0.98):
            _maize(plant_pen, rng, u + rng.uniform(-0.01, 0.01), 0.72, rng.uniform(0.24, 0.30))
        _agave(cactus_pen, rng, 0.72, 0.72, 0.05)
        pen.rect(0.0, 0.705, 1.0, 0.74)
        mask = np.maximum.reduce([ground, a.mask_of(image), a.mask_of(plants), a.mask_of(cactus)])
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.40), p["near"], 0.30, 0.74, "maize near", 0.08)
        a.put(layer, a.mask_of(cactus), mix(p["cactus"], p["near"], 0.55))
        a.put(layer, a.mask_of(plants) * (a.v < 0.70), mix(p["maize"], p["near"], 0.55))
        a.light(layer, a.rim(mask, -0.003, 0.002, 0.4) * mask, p["glow"], 0.38)
        a.shade(layer, a.rim(mask, 0.004, -0.003, 1.0) * mask, 0.22)
        haze(a, layer, p["far"], 0.08, 0.73)
        return layer
    layer = _air(a, p, "highland haze", p["glow"], 0.18, p["near"], 0.22)
    return layer


# ---------------------------------------------------------------------------
# 9. Sahul: red earth at the blue hour, and the sea crossing behind
# ---------------------------------------------------------------------------


def history_sahul(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = SAHUL
    sea_v = HORIZON + 0.006
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.8)), (0.28, p["top"]), (0.46, p["mid"]), (HORIZON - 0.04, mix(p["mid"], p["low"], 0.6)), (HORIZON - 0.005, p["band"]), (HORIZON + 0.01, p["sea"]), (1.0, scale(p["sea"], 0.7))]))
        stars(a, layer, 140, p["star"], v_max=0.46, tag="sahul stars")
        # The thin new moon over the sea.
        moon, moon_pen = a.drawing()
        moon_pen.ellipse(0.72, 0.36, 0.016)
        cut, cut_pen = a.drawing()
        cut_pen.ellipse(0.726, 0.355, 0.015)
        a.put(layer, a.mask_of(moon, blur=0.6) * (1.0 - a.mask_of(cut, blur=0.6)), p["star"], 0.9)
        a.light(layer, a.spot(0.40, HORIZON, 0.40, 2.0, squash=2.5), p["band"], 0.35)
        streaks = cloud_mask(a, "sahul streaks", HORIZON - 0.06, 0.04, cells=2.0, cover=0.32, soft=0.10, stretch=9.0)
        a.tint(layer, streaks, mix(p["far"], p["low"], 0.3), 0.55)
        # The sea crossing: the light of the sky on the water, and the far
        # islands the people came from.
        a.light(layer, a.band(sea_v + 0.01, 0.01) * smoothstep(0.55, 0.80, a.noise("sea glints", cells=50.0, octaves=2, stretch=8.0)), p["sea_light"], 0.55)
        islands, _ = a.ridge("islands", HORIZON - 0.004, 0.006, cells=6.0, octaves=3, sharp=0.6)
        a.tint(layer, islands * (a.v < sea_v) * smoothstep(0.55, 0.50, np.abs(a.u - 0.55) + 0.2), mix(p["far"], p["sea"], 0.4), 0.8)
        _textbook(a, layer, 0.05)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far sahul")
        _, line = a.ridge("sahul plain", HORIZON + 0.03, 0.005, cells=3.0, octaves=3)
        # The red land: a low escarpment of sandstone at the left with a rock
        # shelter in it, the shore at the right.
        scarp = line - 0.07 * smoothstep(0.34, 0.26, a.u[0]) - 0.01 * a.line_noise("sahul scarp", cells=10.0) * smoothstep(0.36, 0.22, a.u[0])
        shore = line + 0.025 * smoothstep(0.62, 0.78, a.u[0])
        ground = _land(a, np.minimum(scarp, shore))
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        hollow, hollow_pen = a.drawing()
        beasts, beast_pen = a.drawing()
        boat, boat_pen = a.drawing()
        hu, hv = 0.21, _at(line, 0.21)
        hollow_pen.poly([(hu - 0.07, hv), (hu - 0.06, hv - 0.03), (hu - 0.01, hv - 0.042), (hu + 0.05, hv - 0.034), (hu + 0.07, hv)])
        for u, h in ((0.40, 0.08), (0.60, 0.06)):
            _boab(trunk_pen, rng, u, _at(line, u) + 0.004, h)
        for u in (0.34, 0.50, 0.66):
            _gum(trunk_pen, crown_pen, rng, u, _at(line, u) + 0.004, rng.uniform(0.07, 0.10))
        for u, s, f in ((0.45, 0.020, 1.0), (0.53, 0.017, 1.0), (0.57, 0.013, -1.0)):
            _diprotodon(beast_pen, u, _at(line, u) + 0.008, s, f)
        # A raft that comes in over the sea.
        bu, bv = 0.76, sea_v + 0.012
        boat_pen.rect(bu - 0.018, bv - 0.002, bu + 0.018, bv + 0.002)
        boat_pen.line([(bu - 0.006, bv - 0.002), (bu - 0.004, bv - 0.020)], 0.0016)
        boat_pen.line([(bu + 0.010, bv - 0.002), (bu + 0.012, bv - 0.018)], 0.0016)
        mask = np.maximum.reduce([ground, a.mask_of(trunks), a.mask_of(crowns), a.mask_of(beasts), a.mask_of(boat)])
        layer = solid(a, mask, mix(p["earth"], p["far"], 0.40), mix(p["earth"], p["earth_dark"], 0.3), HORIZON - 0.08, HORIZON + 0.08, "sahul far", 0.06)
        a.put(layer, a.mask_of(trunks), mix(p["boab"], p["near"], 0.45))
        a.put(layer, a.mask_of(crowns), mix(p["leaf"], p["near"], 0.35))
        a.put(layer, a.mask_of(beasts), mix((70, 40, 36), p["far"], 0.30))
        a.put(layer, a.mask_of(boat), mix((40, 30, 30), p["far"], 0.40))
        # The rock shelter, and the glow of a fire in it.
        a.put(layer, a.mask_of(hollow, blur=0.8) * ground, mix(p["earth_dark"], p["near"], 0.5), 0.8)
        a.glow(layer, a.spot(hu, hv - 0.008, 0.035, 2.0) * ground, p["fire"], 0.55)
        a.glow(layer, a.spot(hu, hv - 0.004, 0.006, 1.5), mix(p["fire"], (255, 255, 220), 0.4), 0.9)
        a.light(layer, a.rim(mask, 0.002, 0.003, 0.5) * mask, p["band"], 0.40)
        # Each layer of the face of the scarp.
        a.shade(layer, ground * smoothstep(0.34, 0.28, a.u) * (0.5 + 0.5 * np.sin(a.v * 500.0)) * 0.5, 0.14)
        haze(a, layer, mix(p["mid"], p["low"], 0.3), 0.14, HORIZON + 0.05)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near sahul")
        image, pen = a.drawing()
        crowns, crown_pen = a.drawing()
        grass, grass_pen = a.drawing()
        ground, _ = a.ridge("near sahul", 0.70, 0.008, cells=4.0, octaves=3)
        # A great boab at the left, a ghost gum at the right, and tufts of
        # spinifex grass on the red earth.
        _boab(pen, rng, 0.11, 0.72, 0.36)
        _gum(pen, crown_pen, rng, 0.90, 0.72, 0.56)
        for _ in range(16):
            u = rng.choice([rng.uniform(0.22, 0.32), rng.uniform(0.70, 0.84)])
            for k in range(9):
                tip = polar(u, 0.715, rng.uniform(0.015, 0.03), -90.0 + (k - 4) * 18.0)
                grass_pen.line([(u, 0.715), tip], 0.0020)
        mask = np.maximum.reduce([ground, a.mask_of(image), a.mask_of(crowns), a.mask_of(grass)])
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.35), p["near"], 0.30, 0.74, "sahul near", 0.08)
        trunk = a.mask_of(image) * (a.u > 0.84) * (a.v < 0.72)
        a.put(layer, trunk, mix(p["gum"], p["near"], 0.45))
        a.put(layer, a.mask_of(crowns), mix(p["leaf"], p["near"], 0.45))
        a.put(layer, a.mask_of(grass) * (a.v < 0.71), mix((170, 160, 100), p["near"], 0.45))
        a.light(layer, a.rim(mask, 0.002, 0.004, 0.4) * mask, p["band"], 0.36)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.22)
        haze(a, layer, p["far"], 0.08, 0.73)
        return layer
    return _air(a, p, "sahul dusk", mix(p["mid"], p["low"], 0.3), 0.14, p["near"], 0.26)


def sahul_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Tufts of spinifex that stand from below: round mounds of stiff,
    spiky blades."""
    del layer_lights
    rng = art_.rand("sahul foreground")
    for k in range(4):
        u = (k + rng.uniform(0.2, 0.8)) / 4.0
        for j in range(15):
            ang = -90.0 + (j - 7) * 11.0 + rng.uniform(-4.0, 4.0)
            tip = polar(u, REST_BOTTOM + 0.05, rng.uniform(0.04, 0.06), ang)
            pen.line([(u, 1.0), (u, REST_BOTTOM + 0.05), tip], 0.0016)


# ---------------------------------------------------------------------------
# 10. The New Guinea highlands: gardens in the swamp under cloud
# ---------------------------------------------------------------------------


def history_highlands(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = HIGHLANDS
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.85)), (0.30, p["top"]), (0.46, p["mid"]), (HORIZON - 0.01, p["low"]), (HORIZON + 0.05, p["swamp"]), (1.0, scale(p["swamp"], 0.8))]))
        a.light(layer, a.spot(0.30, 0.30, 0.45, 2.0), p["cloud"], 0.35)
        # Ranges of rainforest in layers, with cloud in each valley.
        _layers(a, layer, "highland ranges", ((0.44, 0.06, 3.0, 0.5), (0.50, 0.05, 4.0, 0.45), (0.555, 0.04, 5.0, 0.4)), (mix(p["forest"], p["mid"], 0.55), mix(p["forest"], p["mid"], 0.38), mix(p["forest"], p["mid"], 0.20)), p["cloud"], 0.70)
        _heaps(a, layer, "highland heaps", ((0.12, 0.30, 0.09, 0.08), (0.58, 0.26, 0.12, 0.09), (0.92, 0.32, 0.08, 0.07)), p["cloud"], p["cloud_shadow"], 0.9)
        _textbook(a, layer, 0.05)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far highlands")
        ground, line = a.ridge("highland valley", HORIZON + 0.005, 0.006, cells=3.0, octaves=3)
        slope = line - 0.09 * smoothstep(0.28, 0.06, a.u[0]) - 0.07 * smoothstep(0.74, 0.96, a.u[0])
        land = _land(a, slope + 0.006 * (a.line_noise("highland canopy", cells=40.0) - 0.5))
        image, pen = a.drawing()
        crowns, crown_pen = a.drawing()
        houses, house_pen = a.drawing()
        # Round houses with smoke on a rise, and the forest on the slopes.
        smoke = np.zeros((a.n, a.n), dtype=np.float32)
        for k, u in enumerate((0.33, 0.36, 0.64)):
            v = _at(line, u) + 0.004
            _roundhouse(house_pen, u, v, 0.010)
            smoke = np.maximum(smoke, _plume(a, ("house smoke", k), u, v - 0.016, 0.07, 0.03, 0.003))
        for _ in range(40):
            u = rng.choice([rng.uniform(0.0, 0.28), rng.uniform(0.74, 1.0)])
            crown_pen.ellipse(u, _at(slope, u) + rng.uniform(0.0, 0.03), rng.uniform(0.012, 0.02), rng.uniform(0.010, 0.016))
        for u in (0.26, 0.42, 0.56, 0.72):
            _banana(crown_pen, crown_pen, rng, u, _at(line, u) + 0.008, 0.04)
        mask = np.maximum.reduce([land, a.mask_of(crowns), a.mask_of(houses)])
        layer = solid(a, mask, mix(p["forest"], p["far"], 0.35), mix(p["garden"], p["swamp"], 0.3), HORIZON - 0.10, HORIZON + 0.06, "highland far", 0.06)
        a.put(layer, a.mask_of(crowns), mix(p["forest_light"], p["far"], 0.40))
        a.put(layer, a.mask_of(houses), mix(p["thatch"], p["far"], 0.30))
        # The gardens of the swamp: long raised beds with ditches of still
        # water between them, that run back to the foot of the hills.
        v0 = HORIZON + 0.022
        ditches, ditch_pen = a.drawing()
        plants, plant_pen = a.drawing()
        v, gap = v0, 0.006
        while v < 1.0:
            x = rng.uniform(-0.10, 0.0)
            width = 0.0010 + (v - v0) * 0.012
            while x < 1.0:
                length = rng.uniform(0.06, 0.24)
                ditch_pen.line([(x, v), (x + length, v)], width)
                x += length + rng.uniform(0.004, 0.03)
            for _ in range(int(30 + (v - v0) * 80)):
                plant_pen.ellipse(rng.uniform(0.0, 1.0), v + gap * rng.uniform(0.3, 0.7), gap * 0.18, gap * 0.12)
            v += gap
            gap *= 1.32
        for k in range(-14, 15):
            if rng.random() < 0.35:
                continue
            ditch_pen.line([(0.5 + k * 0.022, v0), (0.5 + k * 0.30, 1.0)], 0.0012)
        swamp = ground * (a.v > v0 - 0.002)
        a.put(layer, a.mask_of(plants, blur=0.4) * swamp, mix(p["forest"], p["far"], 0.15), 0.6)
        a.put(layer, a.mask_of(ditches, blur=0.4) * swamp, mix(p["low"], p["swamp"], 0.45), 0.55)
        a.glow(layer, smoke, mix(p["cloud"], p["mid"], 0.3), 0.40)
        a.tint(layer, fog(a, "valley cloud", HORIZON - 0.02, 0.035, 3.0), p["cloud"], 0.65)
        a.light(layer, a.rim(mask, 0.002, 0.003, 0.5) * mask, p["cloud"], 0.25)
        haze(a, layer, p["low"], 0.12, None)
        del image, pen
        return layer
    if layer_key == "near_background":
        rng = a.rand("near highlands")
        image, pen = a.drawing()
        fronds, frond_pen = a.drawing()
        leaves, leaf_pen = a.drawing()
        ground, _ = a.ridge("near highlands", 0.70, 0.008, cells=4.0, octaves=3)
        # Tree ferns at the left, bananas and sugar cane at the right.
        _tree_fern(pen, frond_pen, rng, 0.06, 0.72, 0.48, 0.02)
        _tree_fern(pen, frond_pen, rng, 0.17, 0.72, 0.32, -0.01)
        _banana(pen, leaf_pen, rng, 0.86, 0.72, 0.38)
        _banana(pen, leaf_pen, rng, 0.97, 0.72, 0.44)
        _cane(leaf_pen, rng, 0.76, 0.72, 0.30)
        mask = np.maximum.reduce([ground, a.mask_of(image), a.mask_of(fronds), a.mask_of(leaves)])
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.35), p["near"], 0.30, 0.74, "highland near", 0.08)
        a.put(layer, a.mask_of(fronds), mix(p["forest_light"], p["near"], 0.45))
        a.put(layer, a.mask_of(leaves), mix(p["banana"], p["near"], 0.40))
        a.light(layer, a.rim(mask, 0.002, 0.004, 0.4) * mask, p["cloud"], 0.30)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.22)
        haze(a, layer, p["far"], 0.10, 0.73)
        return layer
    return _air(a, p, "highland cloud", p["cloud"], 0.28, p["near"], 0.24)


def highlands_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Fronds of fern that hang from above at two places, each with its
    leaflets."""
    del layer_lights
    rng = art_.rand("highland foreground")
    for k in range(2):
        u0 = (k + rng.uniform(0.2, 0.8)) / 2.0
        for j in range(2):
            start = (u0 + j * 0.03, 0.0)
            end = (start[0] + rng.uniform(-0.06, 0.06), 0.39 - rng.uniform(0.0, 0.01))
            prev = start
            for i in range(1, 21):
                t = i / 20.0
                pt = (start[0] + (end[0] - start[0]) * t * t, start[1] + (end[1] - start[1]) * t)
                pen.line([prev, pt], 0.0024)
                side = 0.016 * (1.0 - t * 0.6)
                pen.line([pt, (pt[0] + side, pt[1] - side * 0.3)], 0.0016)
                pen.line([pt, (pt[0] - side, pt[1] - side * 0.3)], 0.0016)
                prev = pt


# ---------------------------------------------------------------------------
# 11. The painted cave: torchlight on the paintings
# ---------------------------------------------------------------------------


def history_painted_cave(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = PAINTED_CAVE
    if layer_key == "sky":
        # The back wall of the cave, warm where the torches light it and
        # dark at the roof and the floor.
        layer = a.opaque(a.ramp([(0.0, p["top"]), (0.22, p["mid"]), (0.40, p["wall"]), (HORIZON + 0.02, mix(p["wall"], p["mid"], 0.4)), (0.80, p["mid"]), (1.0, p["top"])]))
        bumps = a.noise("wall bumps", cells=10.0, octaves=5)
        layer[:, :, :3] *= (0.80 + 0.40 * bumps)[:, :, None]
        a.light(layer, a.spot(0.18, 0.48, 0.40, 1.6), p["torch"], 0.35)
        a.light(layer, a.spot(0.84, 0.46, 0.36, 1.6), p["torch"], 0.30)
        # The paintings: a frieze of animals in red ochre and charcoal, and
        # stencils of hands.
        red, red_pen = a.drawing()
        black, black_pen = a.drawing()
        _paint_horse(black_pen, 0.16, 0.42, 0.050, 1.0)
        _paint_horse(red_pen, 0.25, 0.47, 0.040, 1.0)
        _paint_aurochs(black_pen, 0.40, 0.36, 0.070, -1.0)
        _paint_aurochs(red_pen, 0.62, 0.40, 0.060, 1.0)
        _paint_deer(red_pen, 0.80, 0.44, 0.050, -1.0)
        _paint_horse(black_pen, 0.88, 0.50, 0.035, -1.0)
        paint = smoothstep(0.35, 0.75, a.noise("paint wear", cells=30.0, octaves=3)) * 0.4 + 0.6
        a.put(layer, a.mask_of(red, blur=0.6) * paint, p["ochre"], 0.62)
        a.put(layer, a.mask_of(black, blur=0.6) * paint, p["charcoal"], 0.55)
        hands, hand_pen = a.drawing()
        spray, spray_pen = a.drawing()
        for u, v, turn in ((0.08, 0.54, -10.0), (0.12, 0.58, 15.0), (0.52, 0.30, 5.0), (0.93, 0.36, -20.0), (0.96, 0.42, 10.0)):
            spray_pen.ellipse(u, v - 0.008, 0.026)
            _hand(hand_pen, u, v, 0.015, turn)
        halo = a.mask_of(spray, blur=6.0) * (1.0 - a.mask_of(hands, blur=0.5))
        a.put(layer, halo, mix(p["ochre"], p["charcoal"], 0.25), 0.50)
        a.grain(layer, "cave grain", 2.0)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far painted cave")
        image, pen = a.drawing()
        roof = 1.0 - a.ridge("cave roof", 0.17, 0.05, cells=4.0, octaves=4)[0]
        for _ in range(18):
            u = rng.random()
            length = rng.uniform(0.04, 0.12)
            w = rng.uniform(0.006, 0.014)
            pen.poly([(u - w, 0.10), (u + w, 0.10), (u + w * 0.2, 0.12 + length), (u - w * 0.2, 0.12 + length)])
        ground, line = a.ridge("cave floor", HORIZON + 0.07, 0.025, cells=4.0, octaves=4)
        # Columns where stalactite and stalagmite met, at the edges.
        for u, w in ((0.04, 0.03), (0.95, 0.035)):
            pen.poly([(u - w, 1.0), (u - w * 0.4, 0.40), (u - w * 0.6, 0.0), (u + w * 0.6, 0.0), (u + w * 0.4, 0.40), (u + w, 1.0)])
        for u in (0.30, 0.68):
            h = rng.uniform(0.04, 0.07)
            v = _at(line, u) + 0.01
            pen.poly([(u - 0.012, v), (u - 0.004, v - h), (u + 0.004, v - h), (u + 0.012, v)])
        mask = np.maximum.reduce([roof, ground, a.mask_of(image)])
        layer = solid(a, mask, mix(p["rock"], p["wall"], 0.3), p["rock"], 0.20, 0.75, "cave rock", 0.12)
        a.light(layer, a.rim(mask, -0.003, 0.0, 0.5) * mask * smoothstep(0.6, 0.2, a.u), p["torch"], 0.35)
        a.light(layer, a.rim(mask, 0.003, 0.0, 0.5) * mask * smoothstep(0.4, 0.8, a.u), p["torch"], 0.30)
        a.shade(layer, a.rim(mask, 0.0, -0.004, 1.0) * mask, 0.25)
        haze(a, layer, p["mid"], 0.14, HORIZON + 0.07)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near painted cave")
        image, pen = a.drawing()
        torches, torch_pen = a.drawing()
        flames, flame_pen = a.drawing()
        ground, _ = a.ridge("near cave floor", 0.70, 0.014, cells=5.0, octaves=3)
        roof = smoothstep(0.52, 0.56, a.noise("near cave roof", cells=6.0, octaves=4) * smoothstep(0.26, 0.06, a.v))
        # Pillars of rock at the sides, each with a torch in a crack.
        for u, w in ((0.0, 0.10), (0.11, 0.05), (0.89, 0.05), (1.0, 0.10)):
            pen.poly([(u - w, 0.74), (u - w * 0.6, 0.0), (u + w * 0.6, 0.0), (u + w, 0.74)])
        for _ in range(10):
            u = rng.random()
            length = rng.uniform(0.04, 0.12)
            w = rng.uniform(0.008, 0.016)
            pen.poly([(u - w, 0.0), (u + w, 0.0), (u, length)])
        lights = []
        for u, side in ((0.15, 1.0), (0.85, -1.0)):
            base = (u, 0.50)
            tip = (u + side * 0.035, 0.44)
            torch_pen.line([base, tip], 0.006)
            _flame(flame_pen, tip[0], tip[1], 0.016)
            lights.append(tip)
        # A small fire on the floor at the right, its stones round it.
        flame_pen.ellipse(0.78, 0.705, 0.012, 0.010)
        _flame(flame_pen, 0.78, 0.705, 0.012)
        pen.ellipse(0.76, 0.712, 0.006, 0.004)
        pen.ellipse(0.80, 0.712, 0.006, 0.004)
        mask = np.maximum.reduce([ground, roof, a.mask_of(image), a.mask_of(torches)])
        layer = solid(a, mask, p["near_light"], p["near"], 0.20, 0.74, "cave near", 0.12)
        a.light(layer, a.rim(mask, -0.004, 0.0, 0.6) * mask * (a.u < 0.5), p["torch"], 0.40)
        a.light(layer, a.rim(mask, 0.004, 0.0, 0.6) * mask * (a.u > 0.5), p["torch"], 0.40)
        a.shade(layer, a.rim(mask, 0.0, -0.004, 1.0) * mask, 0.30)
        for u, v in lights:
            a.light(layer, a.spot(u, v, 0.10, 1.5) * mask, p["torch"], 0.45)
        a.light(layer, a.spot(0.78, 0.70, 0.12, 1.5) * mask, p["torch"], 0.40)
        flame = a.mask_of(flames, blur=0.4)
        a.glow(layer, a.blur(flame, 14.0), p["torch"], 0.55)
        a.put(layer, flame, p["glow"])
        a.put(layer, a.mask_of(flames, blur=0.0) * a.blur(flame, 2.0) * 0.6, (255, 244, 210))
        return layer
    layer = a.blank()
    a.put(layer, fog(a, "cave smoke", 0.42, 0.20), p["mid"], 0.16)
    vignette(a, layer, p["top"], 0.40)
    return layer


def painted_cave_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Stalactites that hang from above at a few places, with a drop of
    water at the tip of the long ones."""
    del layer_lights
    rng = art_.rand("cave foreground")
    for k in range(4):
        u0 = (k + rng.uniform(0.2, 0.8)) / 4.0
        for j in range(3):
            u = u0 + (j - 1) * 0.012 + rng.uniform(-0.004, 0.004)
            end = 0.385 - rng.uniform(0.0, 0.03) - (0.0 if j == 1 else 0.02)
            w = rng.uniform(0.004, 0.007)
            pen.poly([(u - w, 0.0), (u + w, 0.0), (u + w * 0.3, end - 0.01), (u, end), (u - w * 0.3, end - 0.01)])
