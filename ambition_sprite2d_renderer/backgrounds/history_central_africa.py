"""The scenes of the History dimension: Central Africa.

The History dimension is a grid. East is later, and each floor is a region
of the world. These rooms are on the floor of Africa. They show the shore of
Lake Edward where people made the Ishango bone; Mbanza Kongo, the capital of
the kingdom of Kongo; the Kwanza valley where Queen Nzinga held her war
camps; and the Congo river in the years of the Congo Free State. They use
the same sepia of an old textbook and the same rules as `history_eras.py`
and `history_atlantic.py`. The people of these places show skill, learning
and courage of their own; nothing here is a joke on them.

- ``history_ishango`` (Ishango, where the Semliki river leaves Lake Edward,
  about 20,000 years ago). A warm morning. The lake is wide and calm. Far
  off at the right, the Rwenzori (the "Mountains of the Moon") stand on the
  horizon, blue with distance, with snow and glaciers on their high peaks
  and cloud at their waists. At the right, a low grassy point with acacias
  and a fig, cut by the mouth of the river; on it, the camp of a band of
  hunter-fishers: a windbreak of brush, a rack of fish that dry, and the
  thin smoke of a fire. Beds of papyrus at the water, hippos far off as
  small humps, and a few birds. No building stands here.
- ``history_mbanza_kongo`` (Mbanza Kongo, the capital of the kingdom of
  Kongo, about 1520). A bright clear day with tall cumulus. A town on a
  hilltop plateau: the long wall of the king's enclosure, of tall panels of
  woven palm mat with a pattern of diagonals and an entrance, and in it and
  round it houses with walls of mat and steep roofs of thatch in two
  slopes. Baobabs, oil palms and fields. At the right the plateau falls away
  to green hills that roll to the horizon, and a river far below in the
  valley. A few people far off.
- ``history_matamba`` (Ndongo and Matamba, the Kwanza valley, about 1630).
  A hot hazy afternoon of the dry season, golden. The broad river with its
  sandbanks, dry miombo woodland with flat crowns and some red new leaves,
  big baobabs almost bare, and dry grass. On a rise at the right, a war
  camp (kilombo): a ring palisade of sharpened stakes with a gate, a
  lookout platform, the roofs of huts inside and a thin smoke. Hills far
  off.
- ``history_congo_river_1900`` (the Congo river about 1900). A sober
  scene: a still grey-green day of low cloud and a little mist on the
  water. The wide brown river. At the right, the dark wall of the
  rainforest on the far bank, with tall emergent trees and vines. At the
  left, on the near bank, a mission station (a bungalow with a verandah and
  a schoolhouse with a roof of thatch) and a trading post (a long store
  with a roof of corrugated iron, a bare flagpole and a timber jetty). Far
  off on the river, a small stern-wheel steamer with a thin smoke.

No picture here shows a deity, a religious sign, a church or a cross. No
person in these pictures is harmed, and no one carries a weapon except at
rest. No flag carries a sign.

The bright detail is far off or at the edges, and the middle of each near
layer is calm, so the play in front of it reads. The things that drift in the
air are the room's motes (`terrain/motes.py`), not part of these pictures.
"""

from __future__ import annotations

import math

import numpy as np

from .artkit import Art, Pen, mix, polar, scale, smoothstep
from .history_americas_pacific import _canopy
from .history_atlantic import _oil_palm
from .history_brazil import _stakes, _thatch_house
from .history_east_asia_coast import _bank, _grass_blades, _lumpy_crown, _reflected
from .history_eras import REST_BOTTOM, _air, _at, _heaps, _papyrus, _plume, _reeds, _sun, _textbook
from .history_origins import _acacia, _arch, _hippo, _land, _leaf
from .history_southeast_asia import _hanging_vine
from .parts import HORIZON, cloud_mask, fog, haze, shafts, solid

# ---------------------------------------------------------------------------
# Parts that more than one room has
# ---------------------------------------------------------------------------


def _bird(pen: Pen, u: float, v: float, s: float, beat: float = 0.0) -> None:
    """A small bird far off in flight: two thin wings in a shallow V.
    `beat` from -1 to 1 lifts or drops the wing tips."""
    lift = s * (0.35 + 0.25 * beat)
    pen.line([(u - s, v - lift), (u - s * 0.45, v - s * 0.10), (u, v), (u + s * 0.45, v - s * 0.10), (u + s, v - lift)], s * 0.14)


def _person(body: Pen, head: Pen, u: float, v: float, s: float) -> None:
    """A person far off, who stands: a long cloth from the shoulders to
    the feet and a round head. `(u, v)` is the feet and `s` the height."""
    body.poly([(u - s * 0.13, v), (u + s * 0.13, v), (u + s * 0.10, v - s * 0.78), (u - s * 0.10, v - s * 0.78)])
    head.ellipse(u, v - s * 0.88, s * 0.085, s * 0.10)


def _miombo(trunk: Pen, crown: Pen, rng, u: float, v: float, h: float) -> None:
    """A tree of the dry miombo woodland: a short trunk that forks low into
    crooked limbs, and a crown that is flat on its top and spreads wide, in
    a few level lumps."""
    w = h * 1.1
    fork = (u + rng.uniform(-0.08, 0.08) * w, v - h * 0.35)
    trunk.line([(u, v + 0.004), fork], h * 0.06)
    for k in range(4):
        tip = (u + (k - 1.5) * w * 0.28 + rng.uniform(-0.05, 0.05) * w, v - h * rng.uniform(0.74, 0.82))
        trunk.line([fork, ((fork[0] + tip[0]) * 0.5 + rng.uniform(-0.02, 0.02) * w, (fork[1] + tip[1]) * 0.5), tip], h * 0.030)
    for k in range(9):
        cu = u + (k / 8.0 - 0.5) * w * 0.95 + rng.uniform(-0.05, 0.05) * w
        crown.ellipse(cu, v - h * rng.uniform(0.84, 0.94), w * rng.uniform(0.14, 0.22), h * rng.uniform(0.07, 0.11))
    crown.ellipse(u, v - h * 0.90, w * 0.50, h * 0.08)


def _baobab(trunk: Pen, crown: Pen | None, rng, u: float, v: float, h: float) -> None:
    """A baobab: a trunk as wide as a house that tapers a little to its top,
    and short thick limbs that fork twice into thin crooked twigs, so the
    crown is wide and low. In the dry season it has no leaves; a `crown`
    pen gives it small tufts of leaves at the ends of the twigs."""
    w = h * 0.20
    trunk.poly([(u - w * 1.20, v + 0.004), (u - w * 1.02, v - h * 0.12), (u - w * 0.90, v - h * 0.40), (u - w * 0.74, v - h * 0.62),
                (u + w * 0.74, v - h * 0.62), (u + w * 0.90, v - h * 0.40), (u + w * 1.02, v - h * 0.12), (u + w * 1.20, v + 0.004)])
    top = v - h * 0.60
    for k in range(7):
        ang = -152.0 + k * 20.7 + rng.uniform(-6.0, 6.0)
        start = (u + (k / 6.0 - 0.5) * w * 1.3, top + h * 0.02)
        mid = polar(*start, h * rng.uniform(0.15, 0.20), ang)
        trunk.line([start, mid], w * 0.30)
        for j in (-1.0, 1.0):
            a2 = ang + j * 24.0 + rng.uniform(-8.0, 8.0)
            end = polar(*mid, h * rng.uniform(0.11, 0.15), a2)
            trunk.line([mid, end], w * 0.13)
            for j2 in (-1.0, 1.0):
                twig = polar(*end, h * rng.uniform(0.05, 0.08), a2 + j2 * 24.0)
                trunk.line([end, twig], w * 0.05)
                if crown is not None:
                    crown.ellipse(twig[0], twig[1], h * 0.035, h * 0.022)


def _fig(trunk: Pen, crown: Pen, rng, u: float, v: float, h: float) -> None:
    """A wild fig of the lake shore: a thick short trunk with a flared foot
    and a wide round crown, dense and dark."""
    w = h * 0.07
    trunk.poly([(u - w * 1.6, v + 0.003), (u + w * 1.6, v + 0.003), (u + w * 0.7, v - h * 0.45), (u - w * 0.7, v - h * 0.45)])
    for side in (-1.0, 1.0):
        trunk.line([(u, v - h * 0.40), (u + side * h * 0.22, v - h * 0.62)], w * 0.7)
    _lumpy_crown(crown, rng, u, v - h * 0.70, h * 0.48, h * 0.26, 70)


# ---------------------------------------------------------------------------
# Ishango: the shore of Lake Edward, about 20,000 years ago
# ---------------------------------------------------------------------------


ISHANGO = {
    "top": (122, 150, 176),
    "mid": (214, 206, 186),
    "low": (248, 228, 190),
    "glow": (255, 208, 140),
    "sun": (255, 242, 214),
    "cloud": (250, 238, 220),
    "cloud_shadow": (190, 174, 168),
    "peak": (80, 102, 146),
    "snow": (248, 246, 244),
    "snow_shade": (176, 188, 212),
    "lake": (126, 150, 160),
    "lake_light": (224, 220, 204),
    "lake_deep": (78, 100, 108),
    "grass": (170, 160, 84),
    "grass_light": (214, 196, 116),
    "earth": (150, 118, 82),
    "papyrus": (86, 124, 58),
    "papyrus_light": (176, 194, 104),
    "tree": (70, 96, 56),
    "tree_light": (150, 164, 92),
    "trunk": (104, 84, 64),
    "brush": (126, 102, 70),
    "fish": (196, 188, 170),
    "hippo": (96, 82, 84),
    "smoke": (206, 198, 190),
    "bird": (60, 50, 46),
    "far": (214, 206, 186),
    "near": (36, 38, 26),
    "near_light": (150, 140, 86),
}

#: The level of the lake, where the far land stands in the water.
ISHANGO_WATER = 0.616


def _ishango_point(u: float) -> float:
    """The top of the low grassy point at the right, where the camp is: it
    starts at a low tip in the lake and rises a little to the right."""
    return float(np.interp(u, [0.50, 0.56, 0.64, 0.74, 1.0], [0.642, 0.612, 0.606, 0.603, 0.598]))


def _ishango_shore(u: float) -> float:
    """The near edge of the point, where it meets the lake in front of it."""
    return float(np.interp(u, [0.50, 0.56, 0.70, 1.0], [0.642, 0.634, 0.640, 0.646]))


def _papyrus_bed(stems: Pen, heads: Pen, rng, u0: float, u1: float, foot, h: float) -> None:
    """A bed of papyrus far off: a dense wall of thin green stems, each
    with a round mop of threads on its top that droops a little. `foot`
    gives the `v` of the water at `u`."""
    for _ in range(int((u1 - u0) * 40.0 / h)):
        u = rng.uniform(u0, u1)
        top = h * rng.uniform(0.55, 1.0)
        lean = rng.uniform(-0.12, 0.12) * h
        v = foot(u)
        stems.line([(u, v + 0.002), (u + lean, v - top)], h * 0.05)
        heads.ellipse(u + lean, v - top + h * 0.03, h * rng.uniform(0.11, 0.16), h * rng.uniform(0.07, 0.10))


def _rack(pen: Pen, fish: Pen, u: float, v: float, w: float, h: float) -> None:
    """A rack where fish dry: two forked poles, a bar over them, and a row
    of split fish that hang from the bar."""
    for x in (u - w, u + w):
        pen.line([(x, v + 0.002), (x, v - h)], h * 0.06)
        pen.line([(x, v - h * 0.92), (x - h * 0.10, v - h * 1.10)], h * 0.04)
        pen.line([(x, v - h * 0.92), (x + h * 0.10, v - h * 1.10)], h * 0.04)
    pen.line([(u - w * 1.15, v - h * 0.98), (u + w * 1.15, v - h * 0.98)], h * 0.05)
    for k in range(7):
        x = u - w * 0.85 + k * w * 1.7 / 6.0
        fish.poly([(x - h * 0.05, v - h * 0.96), (x + h * 0.05, v - h * 0.96), (x + h * 0.035, v - h * 0.60), (x, v - h * 0.52), (x - h * 0.035, v - h * 0.60)])


def _windbreak(pen: Pen, rng, u: float, v: float, w: float, h: float) -> None:
    """A windbreak of cut brush in a low arc, open to the lake: a heap of
    thorny branches, higher at its middle."""
    for _ in range(60):
        t = rng.uniform(-1.0, 1.0)
        x = u + t * w
        top = h * (1.0 - 0.55 * t * t) * rng.uniform(0.6, 1.0)
        pen.ellipse(x, v - top * 0.5, w * rng.uniform(0.05, 0.10), top * 0.55)
    for _ in range(18):
        x = u + rng.uniform(-w, w)
        pen.line([(x, v - h * 0.3), (x + rng.uniform(-0.6, 0.6) * h, v - h * rng.uniform(0.8, 1.3))], h * 0.04)


def history_ishango(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = ISHANGO
    sun_at = (0.20, 0.40)
    water_v = ISHANGO_WATER
    if layer_key == "sky":
        # A warm morning: a sky pale and gold near the low sun, banks of
        # thin cloud, and the long range of the Rwenzori at the right, on
        # the far side of the lake, blue with distance. The lake under it
        # is calm and shows the sky.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.92)), (0.26, p["top"]), (0.48, p["mid"]), (HORIZON - 0.01, p["low"]),
                                 (HORIZON + 0.002, mix(p["lake_light"], p["low"], 0.45)), (0.70, mix(p["lake"], p["lake_light"], 0.45)), (1.0, p["lake"])]))
        clouds = cloud_mask(a, "ishango clouds", 0.30, 0.10, cells=3.0, cover=0.42, soft=0.30, stretch=4.0)
        a.put(layer, clouds, p["cloud"], 0.50)
        a.put(layer, clouds * a.band(0.36, 0.05), p["cloud_shadow"], 0.20)
        a.light(layer, a.spot(*sun_at, 0.26, 2.0, squash=1.3), p["glow"], 0.45)
        _sun(a, layer, *sun_at, 0.022, p["sun"], p["glow"], 0.55)
        # The Rwenzori: a long range that rises from the right half of the
        # horizon. Snow and ice lie on the high peaks, cloud lies at their
        # waists, and the low hills in front of them are blue-grey.
        shore = HORIZON - 0.002
        rise = smoothstep(0.40, 0.62, a.u[0]) * (1.0 - 0.35 * smoothstep(0.92, 1.0, a.u[0]))
        for k, (base, amp, cells, sharp, pale) in enumerate(((shore - 0.080, 0.050, 9.0, 0.90, 0.40), (shore - 0.028, 0.014, 10.0, 0.5, 0.30))):
            _, raw = a.ridge(("ishango range", k), base, amp, cells=cells, octaves=5, sharp=sharp)
            line = shore - (shore - raw) * (rise if k == 0 else np.maximum(rise, 0.35))
            mask = _land(a, line) * (a.v < shore + 0.001)
            rock = mix(p["peak"], p["low"], pale)
            a.put(layer, mask, a.ramp([(0.0, rock), (base, rock), (shore, mix(rock, p["low"], 0.45)), (1.0, rock)]))
            if k == 0:
                snow_line = base - amp * 0.35 + (a.noise("ishango snow line", cells=40.0, octaves=3) - 0.5) * 0.016
                glacier = smoothstep(0.55, 0.62, a.noise("ishango glaciers", cells=30.0, octaves=2, stretch=0.3)) * smoothstep(snow_line + 0.016, snow_line, a.v)
                snow = mask * np.maximum(smoothstep(snow_line + 0.002, snow_line - 0.002, a.v), glacier)
                a.put(layer, snow, mix(p["snow_shade"], p["low"], 0.35))
                lit = np.clip(a.rim(mask, 0.010, 0.0, 1.5) * 1.6, 0.0, 1.0)
                ribs = smoothstep(0.45, 0.70, a.noise("ishango ribs", cells=60.0, octaves=2, stretch=0.25))
                a.put(layer, snow * np.maximum(lit, ribs * 0.6), mix(p["snow"], p["glow"], 0.20), 0.9)
                a.light(layer, (mask - snow).clip(0.0, 1.0) * lit, p["glow"], 0.20)
                # Cloud at the waists of the mountains.
                waist = cloud_mask(a, "ishango waist cloud", base + amp * 0.4, 0.024, cells=9.0, cover=0.55, soft=0.30, stretch=2.0)
                a.put(layer, waist * smoothstep(0.44, 0.56, a.u), mix(p["cloud"], p["low"], 0.2), 0.85)
            a.tint(layer, mask * fog(a, ("ishango range mist", k), shore - 0.006, 0.014, 3.0), p["low"], 0.55)
        # The lake: calm, pale far off, with long lines of light, the road of
        # the sun on it, and the soft picture of the mountains.
        water = (a.v >= shore).astype(np.float32)
        lines = smoothstep(0.62, 0.80, a.noise("ishango lake lines", cells=60.0, octaves=2, stretch=14.0))
        a.light(layer, water * lines * smoothstep(shore + 0.12, shore + 0.004, a.v), p["lake_light"], 0.35)
        glints = smoothstep(0.62, 0.82, a.noise("ishango glints", cells=90.0, octaves=2, stretch=8.0))
        a.light(layer, water * glints * a.spot(sun_at[0], shore + 0.03, 0.20, 1.0, squash=0.8), p["glow"], 0.55)
        a.tint(layer, fog(a, "ishango horizon mist", shore - 0.002, 0.012, 3.0), p["low"], 0.50)
        _textbook(a, layer, 0.08)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far ishango")
        # The point at the right: grass on a low bank of silt, cut by the
        # mouth of the Semliki as it leaves the lake.
        top = np.array([_ishango_point(float(u)) for u in a.u[0]], dtype=np.float32)
        shore = np.array([_ishango_shore(float(u)) for u in a.u[0]], dtype=np.float32)
        point = _land(a, top) * np.clip((shore[None, :] - a.v) * a.n + 0.5, 0.0, 1.0)
        mouth, mouth_pen = a.drawing()
        mouth_pen.poly([(0.790, 0.640), (0.805, 0.611), (1.02, 0.612), (1.02, 0.624), (0.835, 0.628)])
        mouth_mask = a.mask_of(mouth, blur=0.6) * point
        ground = lambda u: _ishango_point(u) + 0.010  # noqa: E731
        point = np.clip(point - mouth_mask, 0.0, 1.0)
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        _acacia(trunk_pen, crown_pen, rng, 0.625, ground(0.625), 0.050, 0.030)
        _acacia(trunk_pen, crown_pen, rng, 0.905, _ishango_point(0.905) + 0.004, 0.062, 0.038)
        _acacia(trunk_pen, crown_pen, rng, 0.985, _ishango_point(0.985) + 0.004, 0.044, 0.026)
        _fig(trunk_pen, crown_pen, rng, 0.76, ground(0.76), 0.055)
        # The papyrus at the edge of the water: a bed on the point, and a
        # bed that stands out in the lake at the far left.
        papyrus, papyrus_pen = a.drawing()
        heads, head_pen = a.drawing()
        _papyrus_bed(papyrus_pen, head_pen, rng, 0.53, 0.64, _ishango_shore, 0.026)
        _papyrus_bed(papyrus_pen, head_pen, rng, 0.83, 0.92, lambda u: 0.627, 0.020)
        _papyrus_bed(papyrus_pen, head_pen, rng, -0.02, 0.17, lambda u: water_v + 0.016 + 0.004 * math.sin(u * 30.0), 0.032)
        _papyrus_bed(papyrus_pen, head_pen, rng, 0.17, 0.22, lambda u: water_v + 0.012, 0.018)
        # The camp: a windbreak of brush, the rack of drying fish and a
        # small fire with its thin smoke.
        brush, brush_pen = a.drawing()
        racks, rack_pen = a.drawing()
        fish, fish_pen = a.drawing()
        _windbreak(brush_pen, rng, 0.705, ground(0.705), 0.024, 0.014)
        _rack(rack_pen, fish_pen, 0.670, ground(0.670) + 0.004, 0.010, 0.016)
        smoke = _plume(a, "ishango hearth smoke", 0.690, ground(0.690) - 0.002, 0.10, -0.04, 0.006)
        # Hippos far off in the lake: the humps of their backs and heads.
        hippos, hippo_pen = a.drawing()
        for hu, hv, s in ((0.34, water_v + 0.010, 0.008), (0.365, water_v + 0.012, 0.006), (0.46, water_v + 0.006, 0.005)):
            _hippo(hippo_pen, hu, hv, s)
        birds, bird_pen = a.drawing()
        for bu, bv, s, beat in ((0.30, 0.47, 0.006, 0.6), (0.33, 0.455, 0.005, -0.4), (0.355, 0.48, 0.005, 0.2), (0.58, 0.43, 0.004, -0.6)):
            _bird(bird_pen, bu, bv, s, beat)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        papyrus_mask = np.maximum(a.mask_of(papyrus), a.mask_of(heads))
        head_mask = a.mask_of(heads)
        brush_mask = a.mask_of(brush)
        rack_mask = a.mask_of(racks)
        fish_mask = a.mask_of(fish)
        hippo_mask = a.mask_of(hippos) * (a.v < water_v + 0.013)
        bird_mask = a.mask_of(birds)
        water = smoothstep(HORIZON + 0.010, HORIZON + 0.016, a.v)
        things = np.maximum.reduce([point, trunk_mask, crown_mask, papyrus_mask, brush_mask, rack_mask, fish_mask])
        mask = np.maximum.reduce([things, water, mouth_mask, hippo_mask, bird_mask])
        layer = solid(a, mask, mix(p["grass"], p["far"], 0.40), p["grass"], 0.58, 0.66, "ishango far", 0.04)
        # The lake near the shore: pale, with the pictures of the point and
        # its trees in it, and the mouth of the river a little browner.
        a.put(layer, water, a.ramp([(0.0, mix(p["lake_light"], p["low"], 0.35)), (HORIZON + 0.016, mix(p["lake_light"], p["low"], 0.35)),
                                     (0.66, mix(p["lake"], p["lake_light"], 0.35)), (0.72, p["lake"]), (1.0, p["lake_deep"])]))
        a.put(layer, mouth_mask, mix(mix(p["lake"], p["lake_light"], 0.45), p["earth"], 0.20))
        a.light(layer, mouth_mask * smoothstep(0.55, 0.75, a.noise("ishango river lines", cells=80.0, octaves=2, stretch=12.0)), p["lake_light"], 0.35)
        a.put(layer, _reflected(a, things, 0.640, "ishango ripple", water * (a.v > 0.640) * (1.0 - point)), mix(p["tree"], p["lake"], 0.55), 0.35)
        lines = smoothstep(0.64, 0.84, a.noise("ishango near lines", cells=60.0, octaves=2, stretch=16.0))
        a.light(layer, water * lines * smoothstep(water_v + 0.004, water_v + 0.05, a.v), p["lake_light"], 0.28)
        # The point: dry grass with a bank of silt at the water.
        a.put(layer, point, mix(p["grass"], p["far"], 0.25))
        a.put(layer, point * smoothstep(0.50, 0.70, a.noise("ishango grass", cells=50.0, octaves=2, stretch=3.0)), mix(p["grass_light"], p["far"], 0.20), 0.5)
        a.put(layer, point * a.rim(point, 0.0, -0.004, 0.3), mix(p["earth"], p["far"], 0.25), 0.8)
        a.light(layer, a.rim(point, 0.0, 0.002, 0.3) * point, p["glow"], 0.35)
        a.put(layer, papyrus_mask, mix(p["papyrus"], p["far"], 0.25))
        a.put(layer, head_mask, mix(p["papyrus_light"], p["far"], 0.30), 0.55)
        a.light(layer, a.rim(head_mask, 0.0015, 0.0015, 0.0) * head_mask, p["glow"], 0.45)
        a.put(layer, trunk_mask, mix(p["trunk"], p["far"], 0.25))
        a.put(layer, crown_mask, mix(p["tree"], p["far"], 0.22))
        a.light(layer, crown_mask * smoothstep(0.55, 0.75, a.noise("ishango crowns", cells=80.0, octaves=2)), mix(p["tree_light"], p["far"], 0.2), 0.40)
        a.light(layer, a.rim(crown_mask, 0.002, 0.002, 0.2) * crown_mask, p["glow"], 0.45)
        a.put(layer, brush_mask, mix(p["brush"], p["far"], 0.20))
        a.shade(layer, brush_mask * smoothstep(0.45, 0.70, a.noise("ishango brush", cells=160.0, octaves=1)), 0.25)
        a.put(layer, rack_mask, mix(p["trunk"], p["near"], 0.30))
        a.put(layer, fish_mask, mix(p["fish"], p["far"], 0.10))
        a.put(layer, hippo_mask, mix(p["hippo"], p["far"], 0.30))
        a.light(layer, a.rim(hippo_mask, 0.0, 0.0012, 0.0) * hippo_mask, p["glow"], 0.45)
        a.put(layer, bird_mask, mix(p["bird"], p["far"], 0.35))
        a.put(layer, smoke, p["smoke"], 0.40)
        mask = np.maximum(mask, smoke * 0.40)
        a.tint(layer, fog(a, "ishango shore mist", water_v - 0.002, 0.010, 3.0) * mask, p["low"], 0.40)
        haze(a, layer, p["low"], 0.07, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near ishango")
        bank, ground, bank_at = _bank(a, "near ishango", 0.034, 0.030)
        papyrus, papyrus_pen = a.drawing()
        reeds, reed_pen = a.drawing()
        grass, grass_pen = a.drawing()
        # Clumps of papyrus at the left, reeds at the right; the middle is
        # a calm bank of short grass.
        for u, h, count in ((0.03, 0.30, 14), (0.12, 0.22, 10), (0.20, 0.13, 6)):
            _papyrus(papyrus_pen, rng, u, bank_at(u) + 0.006, h, count, h * 0.18)
        _reeds(reed_pen, rng, 0.80, 0.86, bank_at(0.83) + 0.002, 0.10, 26)
        _reeds(reed_pen, rng, 0.88, 1.0, bank_at(0.94) + 0.002, 0.17, 40)
        for _ in range(16):
            u = rng.uniform(0.26, 0.76)
            _grass_blades(grass_pen, rng, u, bank_at(u) + 0.002, rng.uniform(0.010, 0.018), 6, 0.0012, 0.010)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        papyrus_mask = a.mask_of(papyrus)
        reed_mask = a.mask_of(reeds)
        grass_mask = a.mask_of(grass)
        mask = np.maximum.reduce([bank_mask, papyrus_mask, reed_mask, grass_mask])
        layer = a.blank()
        earth = a.ramp([(0.0, mix(p["grass"], p["near"], 0.50)), (0.66, mix(p["grass"], p["near"], 0.50)), (0.76, mix(p["earth"], p["near"], 0.70)), (1.0, p["near"])])
        a.put(layer, bank_mask, earth)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.30)
        a.put(layer, grass_mask, mix(p["grass"], p["near"], 0.40))
        a.light(layer, a.rim(grass_mask, 0.0015, 0.0, 0.2) * grass_mask, p["grass_light"], 0.25)
        a.put(layer, reed_mask, mix(p["grass"], p["near"], 0.30))
        a.light(layer, a.rim(reed_mask, 0.0015, 0.0, 0.0) * reed_mask, p["grass_light"], 0.35)
        a.put(layer, papyrus_mask, mix(p["papyrus"], p["near"], 0.30))
        a.light(layer, a.rim(papyrus_mask, 0.002, 0.002, 0.0) * papyrus_mask, p["papyrus_light"], 0.45)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.18)
        haze(a, layer, p["low"], 0.10, None)
        return layer
    layer = _air(a, p, "ishango morning mist", p["low"], 0.34, scale(p["near"], 0.8), 0.14)
    a.put(layer, shafts(a, "ishango shafts", 4, 0.14, 0.0, 0.85, 0.05), p["glow"], 0.07)
    return layer


def _papyrus_head(pen: Pen, rng, head: tuple[float, float], r: float, low: float) -> None:
    """The head of a papyrus stem seen from below and near: a burst of
    fine threads that spread out and droop. No thread goes higher than
    `low` (a `v`), so the head stays out of the middle of the view."""
    for k in range(17):
        angle = -170.0 + k * 10.0 + rng.uniform(-3.0, 3.0)
        end = polar(head[0], head[1], r * rng.uniform(0.8, 1.1), angle)
        end = (end[0], max(low, end[1] + r * 0.30 * abs(math.cos(math.radians(angle)))))
        pen.line([head, ((head[0] + end[0]) * 0.5, min(head[1], end[1]) - r * 0.10), end], 0.0016)


def ishango_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Stems of papyrus stand from below at two places, each with its head
    of fine threads at the bottom of the view. A few reeds stand from
    below beside one of them."""
    del layer_lights
    rng = art_.rand("ishango foreground")
    top = REST_BOTTOM - 0.002
    for k in range(2):
        u0 = 0.16 + (k + rng.uniform(0.2, 0.8)) * 0.34
        for j in range(3):
            x = u0 + (j - 1) * 0.020 + rng.uniform(-0.004, 0.004)
            head = (x + (j - 1) * 0.010, top + 0.018 + j % 2 * 0.012)
            pen.line(_arch((x, 1.0), (x, head[1] + 0.06), head, 8), 0.0026)
            _papyrus_head(pen, rng, head, 0.034, top)
    u = rng.uniform(0.44, 0.56)
    for _ in range(7):
        x = u + rng.uniform(-0.016, 0.016)
        tip = (x + rng.uniform(-0.008, 0.008), top + rng.uniform(0.000, 0.016))
        pen.line(_arch((x, 1.0), (x, tip[1] + 0.05), tip, 8), 0.0016)


# ---------------------------------------------------------------------------
# Mbanza Kongo: the capital of the kingdom of Kongo, about 1520
# ---------------------------------------------------------------------------


MBANZA_KONGO = {
    "top": (78, 132, 186),
    "mid": (184, 206, 214),
    "low": (240, 232, 208),
    "glow": (255, 228, 170),
    "sun": (255, 248, 226),
    "cloud": (252, 250, 242),
    "cloud_shadow": (176, 182, 196),
    "hill": (88, 132, 72),
    "hill_light": (160, 186, 104),
    "valley": (112, 150, 84),
    "river": (172, 196, 200),
    "earth": (176, 88, 54),
    "earth_light": (214, 136, 92),
    "grass": (110, 150, 66),
    "mat": (210, 184, 128),
    "mat_dark": (132, 104, 66),
    "mat_light": (232, 210, 160),
    "thatch": (150, 116, 72),
    "thatch_dark": (100, 76, 48),
    "door": (52, 38, 28),
    "post": (110, 82, 56),
    "palm": (52, 92, 52),
    "palm_light": (138, 168, 86),
    "trunk": (118, 96, 72),
    "nuts": (196, 76, 40),
    "boab": (150, 128, 108),
    "boab_light": (206, 186, 160),
    "cloth": (236, 226, 204),
    "cloth_red": (168, 70, 50),
    "skin": (84, 56, 42),
    "far": (198, 210, 204),
    "near": (40, 32, 24),
    "near_light": (170, 86, 52),
}

#: The level of the top of the plateau where the town stands.
KONGO_PLATEAU = 0.606


def _plateau(u: float) -> float:
    """The top of the plateau: level under the town, then it falls away at
    the right to the valley."""
    return float(np.interp(u, [-0.1, 0.62, 0.68, 0.76, 0.86, 0.96], [KONGO_PLATEAU, KONGO_PLATEAU + 0.004, KONGO_PLATEAU + 0.016, KONGO_PLATEAU + 0.050, KONGO_PLATEAU + 0.130, 1.2]))


def _kongo_house(walls: Pen, roof: Pen, door: Pen, u: float, v: float, w: float, h: float, gable: bool) -> None:
    """A house of Kongo: a rectangle with walls of mat or palm rib in
    panels, and a steep roof of thatch in two slopes. Seen from its long
    side the roof is a tall band over the wall; seen from its end (`gable`)
    it is a steep triangle. The low door is in the middle."""
    walls.rect(u - w, v - h, u + w, v + 0.001)
    if gable:
        roof.poly([(u - w * 1.18, v - h + h * 0.08), (u, v - h - h * 1.25), (u + w * 1.18, v - h + h * 0.08)])
    else:
        roof.poly([(u - w * 1.10, v - h + h * 0.08), (u - w * 0.94, v - h - h * 0.95), (u + w * 0.94, v - h - h * 0.95), (u + w * 1.10, v - h + h * 0.08)])
    door.rect(u - w * 0.14, v - h * 0.62, u + w * 0.14, v + 0.001)


def _mat_weave(a: Art, scale_: float) -> np.ndarray:
    """A pattern of woven mat: bands on the two diagonals, that go over
    and under in turn, so it shows a chevron. 1 on the light strands."""
    d1 = (a.u + a.v) * scale_
    d2 = (a.u - a.v) * scale_
    cell = (np.floor(d1) + np.floor(d2)) % 2
    return np.where(cell > 0.5, (np.abs((d1 % 1.0) - 0.5) < 0.30), (np.abs((d2 % 1.0) - 0.5) < 0.30)).astype(np.float32)


def history_mbanza_kongo(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = MBANZA_KONGO
    sun_at = (0.78, 0.26)
    if layer_key == "sky":
        # A bright clear day: tall heap clouds, and at the right, far below
        # the plateau, green hills that roll away to the horizon, a valley
        # with fields and a river that winds in it.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.88)), (0.24, p["top"]), (0.48, p["mid"]), (HORIZON - 0.004, p["low"]),
                                 (HORIZON + 0.004, mix(p["hill"], p["low"], 0.55)), (0.72, mix(p["valley"], p["low"], 0.20)), (1.0, p["valley"])]))
        _sun(a, layer, *sun_at, 0.020, p["sun"], p["glow"], 0.45)
        _heaps(a, layer, "kongo heaps", ((0.14, 0.44, 0.07, 0.13), (0.42, 0.40, 0.09, 0.17), (0.66, 0.46, 0.06, 0.10), (0.93, 0.42, 0.08, 0.14)), p["cloud"], p["cloud_shadow"], 0.85)
        # The hills, far to near: each range a little greener and darker,
        # with mist in the valleys between them.
        for k, (base, amp, cells, pale) in enumerate(((HORIZON - 0.012, 0.008, 4.0, 0.62), (HORIZON + 0.010, 0.012, 3.0, 0.45), (HORIZON + 0.040, 0.016, 2.5, 0.28))):
            mask, line = a.ridge(("kongo hills", k), base, amp, cells=cells, octaves=4)
            a.put(layer, mask, mix(p["hill"], p["low"], pale))
            a.light(layer, mask * a.rim(mask, 0.006, 0.004, 1.0), mix(p["hill_light"], p["low"], pale * 0.6), 0.45)
            fields = smoothstep(0.58, 0.66, a.noise(("kongo far fields", k), cells=40.0, octaves=1, stretch=6.0))
            a.put(layer, mask * fields * (k > 0), mix(p["hill_light"], p["low"], pale), 0.15)
            a.tint(layer, mask * fog(a, ("kongo valley mist", k), base + amp + 0.012, 0.012, 3.0), p["low"], 0.45)
        river, river_pen = a.drawing()
        pts = [(u, 0.676 + 0.012 * math.sin(u * 17.0) + (u - 0.6) * 0.06) for u in np.linspace(0.45, 1.04, 50)]
        river_pen.line(pts, 0.0030)
        a.put(layer, a.mask_of(river) * (a.v > 0.65), mix(p["river"], p["low"], 0.25), 0.85)
        a.tint(layer, fog(a, "kongo horizon haze", HORIZON, 0.020, 3.0), p["low"], 0.50)
        _textbook(a, layer, 0.07)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far kongo")
        top = np.array([_plateau(float(u)) for u in a.u[0]], dtype=np.float32)
        land = _land(a, top)
        wall_v = KONGO_PLATEAU + 0.010
        wall_h = 0.034
        gate = (0.355, 0.375)
        walls, wall_pen = a.drawing()
        posts, post_pen = a.drawing()
        house_walls, house_wall_pen = a.drawing()
        roofs, roof_pen = a.drawing()
        doors, door_pen = a.drawing()
        # The houses inside the enclosure stand behind its wall: only their
        # roofs show over it. Houses outside it stand on the slope.
        for hu, hw, hh, gable in ((0.16, 0.016, 0.014, False), (0.215, 0.012, 0.014, True), (0.27, 0.020, 0.016, False), (0.33, 0.013, 0.015, True),
                                   (0.41, 0.018, 0.016, False), (0.47, 0.012, 0.014, True), (0.53, 0.020, 0.018, False)):
            _kongo_house(house_wall_pen, roof_pen, door_pen, hu, wall_v - 0.004, hw, hh * 1.6, gable)
        # The wall of the enclosure: tall panels of woven mat between posts,
        # with an entrance under a lintel.
        wall_pen.rect(0.12, wall_v - wall_h, gate[0], wall_v + 0.002)
        wall_pen.rect(gate[1], wall_v - wall_h, 0.58, wall_v + 0.002)
        for x in np.arange(0.12, 0.585, 0.022):
            if gate[0] - 0.004 < x < gate[1] + 0.004:
                continue
            post_pen.rect(x - 0.0014, wall_v - wall_h - 0.004, x + 0.0014, wall_v + 0.002)
        for x in gate:
            post_pen.rect(x - 0.0024, wall_v - wall_h - 0.010, x + 0.0024, wall_v + 0.002)
        post_pen.rect(gate[0] - 0.006, wall_v - wall_h - 0.010, gate[1] + 0.006, wall_v - wall_h - 0.005)
        gate_hole, gate_pen = a.drawing()
        gate_pen.rect(gate[0], wall_v - wall_h + 0.006, gate[1], wall_v + 0.002)
        # Houses outside the wall, at the left and on the right of the
        # plateau, and a few in the fields toward its edge.
        for hu, hw, hh, gable in ((0.035, 0.016, 0.016, False), (0.085, 0.011, 0.013, True), (0.615, 0.014, 0.014, True), (0.655, 0.018, 0.014, False)):
            _kongo_house(house_wall_pen, roof_pen, door_pen, hu, _plateau(hu) + 0.012, hw, hh, gable)
        # Baobabs and oil palms in the town and round it.
        boabs, boab_pen = a.drawing()
        leaves, leaf_pen = a.drawing()
        _baobab(boab_pen, leaf_pen, rng, 0.245, wall_v - 0.004, 0.085)
        _baobab(boab_pen, leaf_pen, rng, 0.72, _plateau(0.72) + 0.004, 0.065)
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        nuts, nut_pen = a.drawing()
        for pu, h in ((0.135, 0.075), (0.30, 0.060), (0.45, 0.080), (0.505, 0.055), (0.60, 0.070), (0.68, 0.050), (0.02, 0.065)):
            _oil_palm(trunk_pen, crown_pen, nut_pen, rng, pu, _plateau(pu) + 0.008 if pu > 0.58 or pu < 0.1 else wall_v - 0.010, h, rng.uniform(-0.01, 0.01))
        # Fields of the town on the near slope of the plateau, and people
        # far off on the open ground in front of the wall.
        fields, field_pen = a.drawing()
        x = -0.02
        while x < 0.66:
            length = rng.uniform(0.07, 0.13)
            depth = rng.uniform(0.014, 0.024)
            v0 = wall_v + 0.010 + rng.uniform(0.0, 0.010)
            field_pen.poly([(x, v0), (x + length, v0 + 0.002), (x + length - 0.006, v0 + depth), (x + 0.006, v0 + depth)])
            x += length + rng.uniform(0.012, 0.03)
        bodies, body_pen = a.drawing()
        reds, red_pen = a.drawing()
        heads, head_pen = a.drawing()
        for k in range(9):
            u = rng.uniform(0.14, 0.60)
            s = rng.uniform(0.012, 0.015)
            _person(red_pen if k % 3 == 0 else body_pen, head_pen, u, wall_v + 0.006 + rng.uniform(0.0, 0.004), s)
        wall_mask = a.mask_of(walls)
        post_mask = a.mask_of(posts)
        gate_mask = a.mask_of(gate_hole) * wall_mask
        hwall_mask = a.mask_of(house_walls)
        roof_mask = a.mask_of(roofs)
        door_mask = a.mask_of(doors) * hwall_mask
        boab_mask = a.mask_of(boabs)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        nut_mask = a.mask_of(nuts) * crown_mask
        field_mask = a.mask_of(fields) * land
        people = np.maximum(a.mask_of(bodies), a.mask_of(reds))
        leaf_mask = a.mask_of(leaves)
        town = np.maximum.reduce([wall_mask, post_mask, hwall_mask, roof_mask, boab_mask, leaf_mask, trunk_mask, crown_mask])
        mask = np.maximum.reduce([land, town, people])
        layer = solid(a, mask, mix(p["grass"], p["far"], 0.35), mix(p["grass"], p["near"], 0.10), 0.58, 0.72, "kongo far", 0.05)
        # The plateau: short grass, the red earth where it is bare and worn,
        # and the fields in rows.
        bare = smoothstep(0.60, 0.70, a.noise("kongo bare earth", cells=40.0, octaves=3, stretch=4.0))
        a.put(layer, land * bare, mix(p["earth"], p["far"], 0.35), 0.40)
        a.put(layer, land * smoothstep(wall_v + 0.004, wall_v - 0.002, a.v) * smoothstep(0.10, 0.14, a.u) * smoothstep(0.62, 0.58, a.u), mix(p["earth_light"], p["far"], 0.25), 0.8)
        a.put(layer, field_mask, mix(p["earth"], p["far"], 0.30), 0.85)
        rows = np.clip(1.0 - np.abs(((a.v * 600.0) % 1.0) - 0.5) / 0.22, 0.0, 1.0)
        a.put(layer, field_mask * rows, mix(p["grass"], p["far"], 0.20), 0.7)
        a.light(layer, a.rim(land, 0.004, 0.003, 0.5) * land, p["glow"], 0.35)
        # The houses: walls of mat in squares, dark low doors, steep roofs
        # of thatch with lines of straw down their slopes.
        a.put(layer, hwall_mask, mix(p["mat"], p["far"], 0.15))
        grid = (np.abs(((a.u * 900.0) % 1.0) - 0.5) > 0.40) | (np.abs(((a.v * 900.0) % 1.0) - 0.5) > 0.40)
        a.put(layer, hwall_mask * grid, mix(p["mat_dark"], p["far"], 0.15), 0.7)
        a.put(layer, door_mask, mix(p["door"], p["far"], 0.15))
        a.put(layer, roof_mask, mix(p["thatch"], p["far"], 0.10))
        straw = np.clip(1.0 - np.abs(((a.u * 800.0) % 1.0) - 0.5) / 0.15, 0.0, 1.0)
        a.shade(layer, roof_mask * straw, 0.14)
        a.light(layer, a.rim(roof_mask, -0.002, 0.0, 0.2) * roof_mask, p["glow"], 0.45)
        a.shade(layer, a.rim(roof_mask, 0.002, 0.0, 0.2) * roof_mask, 0.25)
        a.put(layer, a.rim(roof_mask, 0.0, -0.002, 0.0) * roof_mask, mix(p["thatch_dark"], p["far"], 0.10), 0.7)
        # The wall of the king's enclosure: tall panels of mat woven in
        # diagonals, the posts that hold them, and the dark of the
        # entrance.
        a.put(layer, wall_mask, mix(p["mat"], p["far"], 0.08))
        weave = _mat_weave(a, 220.0)
        a.put(layer, wall_mask * weave, mix(p["mat_light"], p["far"], 0.05), 0.75)
        a.put(layer, wall_mask * (1.0 - weave), mix(p["mat_dark"], p["far"], 0.05), 0.60)
        a.put(layer, wall_mask * a.rim(wall_mask, 0.0, 0.003, 0.0), mix(p["mat_dark"], p["far"], 0.08), 0.8)
        a.light(layer, wall_mask * a.rim(wall_mask, 0.0, 0.0015, 0.0), p["glow"], 0.5)
        a.put(layer, gate_mask, mix(p["door"], p["far"], 0.12))
        a.put(layer, post_mask, mix(p["post"], p["far"], 0.12))
        a.light(layer, a.rim(post_mask, -0.001, 0.0, 0.0) * post_mask, p["glow"], 0.4)
        # The trees.
        a.put(layer, boab_mask, mix(p["boab"], p["far"], 0.15))
        a.light(layer, a.rim(boab_mask, -0.003, 0.0, 0.6) * boab_mask, mix(p["boab_light"], p["glow"], 0.3), 0.55)
        a.shade(layer, a.rim(boab_mask, 0.003, 0.0, 0.6) * boab_mask, 0.25)
        a.put(layer, leaf_mask, mix(p["palm"], p["far"], 0.25))
        a.light(layer, a.rim(leaf_mask, -0.001, 0.001, 0.0) * leaf_mask, mix(p["palm_light"], p["far"], 0.2), 0.45)
        a.put(layer, trunk_mask, mix(p["trunk"], p["far"], 0.20))
        a.put(layer, crown_mask, mix(p["palm"], p["far"], 0.18))
        a.light(layer, a.rim(crown_mask, -0.0015, 0.0015, 0.0) * crown_mask, mix(p["palm_light"], p["far"], 0.2), 0.50)
        a.put(layer, nut_mask, mix(p["nuts"], p["far"], 0.20))
        # The people: cloth of white and of red, a few of each.
        a.put(layer, a.mask_of(bodies), mix(p["cloth"], p["far"], 0.10))
        a.put(layer, a.mask_of(reds), mix(p["cloth_red"], p["far"], 0.10))
        a.put(layer, a.mask_of(heads) * land, mix(p["skin"], p["far"], 0.20))
        a.tint(layer, smoothstep(0.62, 0.74, a.v) * land, p["low"], 0.20)
        haze(a, layer, p["low"], 0.06, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near kongo")
        bank, ground, bank_at = _bank(a, "near kongo", 0.040, 0.034)
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        nuts, nut_pen = a.drawing()
        fronds, frond_pen = a.drawing()
        boabs, boab_pen = a.drawing()
        grass, grass_pen = a.drawing()
        # An oil palm and the great fronds of a raffia palm at the left; a
        # baobab at the right. The middle is a calm bank of red earth and
        # short grass.
        _oil_palm(trunk_pen, crown_pen, nut_pen, rng, 0.07, bank_at(0.07) + 0.004, 0.32, 0.02)
        top = (0.17, bank_at(0.17) - 0.006)
        for k in range(7):
            ang = -168.0 + k * 26.0 + rng.uniform(-6.0, 6.0)
            tip = polar(*top, 0.13 * rng.uniform(0.8, 1.05), ang)
            tip = (tip[0], tip[1] + 0.04)
            rib = _arch(top, polar(*top, 0.08, ang), tip, 12)
            frond_pen.line(rib, 0.0024)
            for i, (x, y) in enumerate(rib[2:], 2):
                side = 0.016 * (1.0 - i / 14.0)
                frond_pen.line([(x, y), (x + side * 0.4, y + side)], 0.0012)
                frond_pen.line([(x, y), (x - side * 0.4, y + side)], 0.0012)
        near_leaves, near_leaf_pen = a.drawing()
        _baobab(boab_pen, near_leaf_pen, rng, 0.93, bank_at(0.93) + 0.006, 0.36)
        for _ in range(170):
            u = rng.uniform(0.0, 1.0)
            h = rng.uniform(0.005, 0.012) * (1.0 + 0.8 * (abs(u - 0.5) > 0.3))
            v = bank_at(u) + 0.002
            grass_pen.line([(u, v), (u + rng.uniform(-0.004, 0.004), v - h)], 0.0013)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        nut_mask = a.mask_of(nuts) * crown_mask
        frond_mask = a.mask_of(fronds)
        boab_mask = a.mask_of(boabs)
        near_leaf_mask = a.mask_of(near_leaves)
        grass_mask = a.mask_of(grass)
        mask = np.maximum.reduce([bank_mask, trunk_mask, crown_mask, frond_mask, boab_mask, near_leaf_mask, grass_mask])
        layer = a.blank()
        earth = a.ramp([(0.0, mix(p["near_light"], p["near"], 0.25)), (0.64, mix(p["near_light"], p["near"], 0.25)), (0.80, mix(p["near_light"], p["near"], 0.70)), (1.0, p["near"])])
        a.put(layer, bank_mask, earth)
        a.shade(layer, bank_mask * smoothstep(0.5, 0.7, a.noise("kongo near earth", cells=60.0, octaves=3, stretch=3.0)), 0.10)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.35)
        a.put(layer, grass_mask, mix(p["grass"], p["near"], 0.45))
        a.put(layer, trunk_mask, mix(p["trunk"], p["near"], 0.45))
        a.put(layer, crown_mask, mix(p["palm"], p["near"], 0.30))
        a.light(layer, a.rim(crown_mask, -0.002, 0.002, 0.0) * crown_mask, p["palm_light"], 0.40)
        a.put(layer, nut_mask, mix(p["nuts"], p["near"], 0.35))
        a.put(layer, frond_mask, mix(p["palm"], p["near"], 0.22))
        a.light(layer, a.rim(frond_mask, -0.002, 0.002, 0.0) * frond_mask, p["palm_light"], 0.35)
        a.put(layer, boab_mask, mix(p["boab"], p["near"], 0.40))
        a.light(layer, a.rim(boab_mask, -0.004, 0.0, 0.8) * boab_mask, p["boab_light"], 0.35)
        a.shade(layer, boab_mask * smoothstep(0.5, 0.75, a.noise("kongo near bark", cells=90.0, octaves=2, stretch=0.2)), 0.15)
        a.put(layer, near_leaf_mask, mix(p["palm_light"], p["near"], 0.35))
        a.shade(layer, a.rim(mask, 0.004, -0.003, 1.0) * mask, 0.18)
        haze(a, layer, p["low"], 0.08, None)
        return layer
    layer = _air(a, p, "kongo bright haze", p["low"], 0.22, p["near"], 0.16)
    a.put(layer, shafts(a, "kongo shafts", 4, -0.16, 0.0, 0.85, 0.05), p["glow"], 0.06)
    return layer


def mbanza_kongo_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """The tips of oil-palm fronds hang into the top of the view at two
    places. A clump of grass stands from below at one place."""
    del layer_lights
    rng = art_.rand("kongo foreground")
    for k in range(2):
        u0 = 0.08 + (k + rng.uniform(0.2, 0.8)) * 0.42
        for j in range(3):
            start = (u0 + (j - 1) * 0.045, 0.0)
            end = (start[0] + (j - 1) * 0.08 + rng.uniform(-0.02, 0.02), 0.380 - rng.uniform(0.0, 0.012))
            ctrl = ((start[0] + end[0]) * 0.5 + (j - 1) * 0.03, 0.20)
            rib = _arch(start, ctrl, end, 20)
            pen.line(rib, 0.0026)
            for i, (x, y) in enumerate(rib[1:], 1):
                side = 0.036 * (1.0 - i / 20.0 * 0.6)
                side = max(0.0, min(side, 0.390 - y))
                pen.line([(x, y), (x + side * 0.30, y + side)], 0.0013)
                pen.line([(x, y), (x - side * 0.30, y + side)], 0.0013)
    u0 = rng.uniform(0.40, 0.60)
    for _ in range(9):
        u = u0 + rng.uniform(-0.02, 0.02)
        top = REST_BOTTOM - rng.uniform(-0.004, 0.012)
        bend = rng.uniform(-0.02, 0.02)
        pen.line(_arch((u, 1.0), (u + bend * 0.2, top + 0.05), (u + bend, top), 8), 0.0018)


# ---------------------------------------------------------------------------
# Matamba: the Kwanza valley, about 1630
# ---------------------------------------------------------------------------


MATAMBA = {
    "top": (120, 150, 172),
    "mid": (226, 212, 176),
    "low": (250, 228, 176),
    "glow": (255, 212, 130),
    "sun": (255, 244, 214),
    "cloud": (250, 238, 214),
    "cloud_shadow": (206, 186, 160),
    "hills": (150, 140, 136),
    "river": (150, 160, 150),
    "river_light": (226, 220, 196),
    "sand": (232, 206, 156),
    "grass": (206, 170, 86),
    "grass_light": (236, 206, 128),
    "earth": (160, 92, 58),
    "earth_light": (204, 136, 86),
    "tree": (104, 112, 56),
    "tree_light": (176, 168, 88),
    "red_leaf": (176, 82, 52),
    "trunk": (96, 72, 54),
    "boab": (164, 140, 118),
    "boab_light": (220, 196, 164),
    "stake": (128, 98, 68),
    "stake_light": (190, 156, 108),
    "thatch": (190, 160, 100),
    "smoke": (214, 206, 196),
    "far": (226, 212, 180),
    "near": (52, 34, 24),
    "near_light": (172, 104, 62),
}

#: The bank of the river in the far layer.
MATAMBA_BANK = 0.662


def _rise(u: float) -> float:
    """The top of the valley side: low by the river at the left, and up to
    a long rise at the right where the war camp stands."""
    return float(np.interp(u, [-0.1, 0.30, 0.46, 0.56, 0.62, 0.80, 1.1], [MATAMBA_BANK, MATAMBA_BANK - 0.004, MATAMBA_BANK - 0.024, 0.592, 0.578, 0.572, 0.578]))


def _lookout(pen: Pen, roof: Pen, u: float, v: float, h: float) -> None:
    """A lookout platform: four poles with braces, a floor at the top, a
    low rail, and a small roof of thatch over it."""
    w = h * 0.22
    for x in (u - w, u - w * 0.35, u + w * 0.35, u + w):
        pen.line([(x, v + 0.002), (x, v - h)], h * 0.035)
    pen.line([(u - w, v - h * 0.15), (u + w, v - h * 0.55)], h * 0.025)
    pen.line([(u + w, v - h * 0.15), (u - w, v - h * 0.55)], h * 0.025)
    pen.rect(u - w * 1.2, v - h * 0.86, u + w * 1.2, v - h * 0.80)
    pen.rect(u - w * 1.2, v - h * 0.98, u + w * 1.2, v - h * 0.95)
    roof.poly([(u - w * 1.45, v - h * 1.0), (u, v - h * 1.32), (u + w * 1.45, v - h * 1.0)])


def history_matamba(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = MATAMBA
    sun_at = (0.36, 0.30)
    if layer_key == "sky":
        # A hot hazy afternoon of the dry season: a pale gold sky, thin high
        # cloud, low blue-grey hills far off, and the broad river with its
        # sandbanks in the plain below them.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.92)), (0.24, p["top"]), (0.46, p["mid"]), (HORIZON - 0.004, p["low"]),
                                 (HORIZON + 0.004, mix(p["grass"], p["low"], 0.55)), (0.70, mix(p["grass"], p["low"], 0.30)), (1.0, p["grass"])]))
        _sun(a, layer, *sun_at, 0.024, p["sun"], p["glow"], 0.70)
        high = cloud_mask(a, "matamba high cloud", 0.22, 0.08, cells=3.0, cover=0.40, soft=0.35, stretch=6.0)
        a.put(layer, high, p["cloud"], 0.35)
        _heaps(a, layer, "matamba heaps", ((0.72, 0.50, 0.06, 0.05), (0.90, 0.52, 0.05, 0.035)), p["cloud"], p["cloud_shadow"], 0.55)
        for k, (base, amp, cells, pale) in enumerate(((HORIZON - 0.020, 0.014, 4.0, 0.62), (HORIZON - 0.006, 0.008, 6.0, 0.48))):
            mask, _ = a.ridge(("matamba far hills", k), base, amp, cells=cells, octaves=4)
            a.put(layer, mask * (a.v < HORIZON + 0.004), mix(p["hills"], p["low"], pale))
        # The river: wide and slow, pale with the haze, with long bars of
        # sand in it.
        river, river_pen = a.drawing()
        bars, bar_pen = a.drawing()
        top = [(u, 0.615 + 0.006 * math.sin(u * 5.0)) for u in np.linspace(-0.02, 1.02, 30)]
        low = [(u, 0.650 + 0.010 * math.sin(u * 4.0 + 1.0)) for u in np.linspace(1.02, -0.02, 30)]
        river_pen.poly(top + low)
        for bu, bv, bw, bh in ((0.12, 0.632, 0.07, 0.006), (0.38, 0.626, 0.05, 0.004), (0.55, 0.640, 0.08, 0.006), (0.86, 0.630, 0.06, 0.005)):
            bar_pen.ellipse(bu, bv, bw, bh)
        river_mask = a.mask_of(river, blur=0.8)
        bar_mask = a.mask_of(bars, blur=0.6) * river_mask
        a.put(layer, river_mask, a.ramp([(0.0, mix(p["river_light"], p["low"], 0.3)), (0.62, mix(p["river_light"], p["low"], 0.3)), (0.66, p["river"]), (1.0, p["river"])]))
        lines = smoothstep(0.62, 0.82, a.noise("matamba river lines", cells=60.0, octaves=2, stretch=14.0))
        a.light(layer, river_mask * lines, p["river_light"], 0.40)
        a.put(layer, bar_mask, p["sand"])
        a.light(layer, bar_mask * a.rim(bar_mask, 0.0, 0.002, 0.0), (255, 248, 230), 0.5)
        a.tint(layer, fog(a, "matamba heat haze", HORIZON, 0.030, 3.0), p["low"], 0.55)
        _textbook(a, layer, 0.09)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far matamba")
        top = np.array([_rise(float(u)) for u in a.u[0]], dtype=np.float32)
        land = _land(a, top)
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        boabs, boab_pen = a.drawing()
        # The miombo woodland on the valley side: low trees with flat
        # crowns, thicker on the slope, thin on the rise near the camp.
        for _ in range(70):
            u = rng.uniform(-0.02, 1.02)
            if 0.58 < u < 0.84 and rng.random() < 0.85:
                continue
            if u < 0.42 and rng.random() < 0.45:
                continue
            v = _rise(u) + rng.uniform(0.002, 0.030)
            _miombo(trunk_pen, crown_pen, rng, u, v, rng.uniform(0.022, 0.034) * (1.0 + (v - 0.6) * 4.0))
        # The baobabs: big, almost bare in the dry season.
        for bu, h in ((0.12, 0.10), (0.40, 0.080), (0.90, 0.075)):
            _baobab(boab_pen, None, rng, bu, _rise(bu) + 0.010, h)
        # The kilombo on the rise: a ring of stakes seen from the side, its
        # far half low over the near one; a gate; a lookout; the roofs of
        # the huts inside and a thin smoke.
        cu, ring_w = 0.71, 0.10
        foot = lambda u: _rise(u) + 0.006  # noqa: E731
        stakes_far, far_pen = a.drawing()
        stakes, stake_pen = a.drawing()
        huts, hut_pen = a.drawing()
        roofs, roof_pen = a.drawing()
        doors, door_pen = a.drawing()
        _stakes(far_pen, cu - ring_w, cu + ring_w, lambda u: foot(u) - 0.012 * math.sqrt(max(0.0, 1.0 - ((u - cu) / ring_w) ** 2)), 0.016, 0.0030)
        for hu, hw in ((0.63, 0.011), (0.665, 0.014), (0.70, 0.010), (0.74, 0.015), (0.78, 0.011)):
            _thatch_house(hut_pen, roof_pen, door_pen, hu, foot(hu) - 0.016, hw, hw * 0.60, 1.6)
        gate_u = 0.68
        _stakes(stake_pen, cu - ring_w, cu + ring_w, lambda u: foot(u) if abs(u - gate_u) > 0.010 else 9.0, 0.024, 0.0036)
        stake_pen.rect(gate_u - 0.012, foot(gate_u) - 0.034, gate_u - 0.008, foot(gate_u) + 0.002)
        stake_pen.rect(gate_u + 0.008, foot(gate_u) - 0.034, gate_u + 0.012, foot(gate_u) + 0.002)
        stake_pen.rect(gate_u - 0.014, foot(gate_u) - 0.036, gate_u + 0.014, foot(gate_u) - 0.031)
        gate, gate_pen = a.drawing()
        gate_pen.rect(gate_u - 0.008, foot(gate_u) - 0.028, gate_u + 0.008, foot(gate_u) + 0.002)
        look, look_pen = a.drawing()
        look_roof, look_roof_pen = a.drawing()
        _lookout(look_pen, look_roof_pen, 0.775, foot(0.775) - 0.004, 0.070)
        smoke = _plume(a, "matamba camp smoke", 0.725, foot(0.725) - 0.016, 0.14, 0.05, 0.005)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        boab_mask = a.mask_of(boabs)
        far_stake_mask = a.mask_of(stakes_far)
        stake_mask = a.mask_of(stakes)
        hut_mask = a.mask_of(huts)
        roof_mask = a.mask_of(roofs)
        gate_mask = a.mask_of(gate)
        look_mask = a.mask_of(look)
        look_roof_mask = a.mask_of(look_roof)
        camp = np.maximum.reduce([far_stake_mask, stake_mask, hut_mask, roof_mask, look_mask, look_roof_mask])
        mask = np.maximum.reduce([land, trunk_mask, crown_mask, boab_mask, camp])
        layer = solid(a, mask, mix(p["grass"], p["far"], 0.35), mix(p["grass"], p["earth"], 0.25), 0.56, 0.72, "matamba far", 0.03)
        # The valley side: dry grass, gold where the sun is on it, with
        # red earth where it shows.
        a.light(layer, land * smoothstep(0.50, 0.70, a.noise("matamba grass", cells=90.0, octaves=3, stretch=4.0)), p["grass_light"], 0.22)
        a.put(layer, land * smoothstep(0.64, 0.72, a.noise("matamba earth", cells=60.0, octaves=3, stretch=3.0)), mix(p["earth"], p["far"], 0.35), 0.40)
        a.light(layer, a.rim(land, -0.003, 0.003, 0.5) * land, p["glow"], 0.45)
        # The woodland: olive crowns, some red with new leaves.
        a.put(layer, trunk_mask, mix(p["trunk"], p["far"], 0.25))
        a.put(layer, crown_mask, mix(p["tree"], p["far"], 0.25))
        a.put(layer, crown_mask * smoothstep(0.60, 0.70, a.noise("matamba new leaves", cells=36.0, octaves=2)), mix(p["red_leaf"], p["far"], 0.20), 0.8)
        a.light(layer, a.rim(crown_mask, 0.0, 0.002, 0.0) * crown_mask, mix(p["tree_light"], p["glow"], 0.3), 0.55)
        a.shade(layer, a.rim(crown_mask, 0.0, -0.002, 0.0) * crown_mask, 0.25)
        a.put(layer, boab_mask, mix(p["boab"], p["far"], 0.20))
        a.light(layer, a.rim(boab_mask, 0.003, 0.0, 0.6) * boab_mask, mix(p["boab_light"], p["glow"], 0.3), 0.50)
        a.shade(layer, a.rim(boab_mask, -0.003, 0.0, 0.6) * boab_mask, 0.25)
        # The camp: the palisade grey-brown and lit on the side to the sun,
        # the far half paler, the huts and the lookout.
        a.put(layer, far_stake_mask, mix(p["stake"], p["far"], 0.40))
        a.put(layer, hut_mask, mix(p["earth_light"], p["far"], 0.25))
        a.put(layer, roof_mask, mix(p["thatch"], p["far"], 0.15))
        a.light(layer, a.rim(roof_mask, 0.002, 0.0, 0.2) * roof_mask, p["glow"], 0.45)
        a.put(layer, stake_mask, mix(p["stake"], p["far"], 0.12))
        a.light(layer, stake_mask * (np.abs(((a.u * 300.0) % 1.0) - 0.25) < 0.18), p["stake_light"], 0.45)
        a.put(layer, gate_mask * stake_mask, mix(p["near"], p["stake"], 0.45))
        a.put(layer, look_mask, mix(p["stake"], p["near"], 0.20))
        a.put(layer, look_roof_mask, mix(p["thatch"], p["far"], 0.10))
        a.put(layer, smoke, p["smoke"], 0.55)
        mask = np.maximum(mask, smoke * 0.55)
        a.tint(layer, fog(a, "matamba valley haze", MATAMBA_BANK, 0.020, 3.0) * mask, p["low"], 0.30)
        haze(a, layer, p["low"], 0.08, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near matamba")
        bank, ground, bank_at = _bank(a, "near matamba", 0.036, 0.040)
        boabs, boab_pen = a.drawing()
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        grass, grass_pen = a.drawing()
        # A great baobab at the left; a miombo tree and dry grass at the
        # right. The middle is a calm bank of red earth and dry grass.
        _baobab(boab_pen, None, rng, 0.07, bank_at(0.07) + 0.008, 0.44)
        _miombo(trunk_pen, crown_pen, rng, 0.90, bank_at(0.90) + 0.004, 0.22)
        for u, h in ((0.17, 0.040), (0.21, 0.028), (0.80, 0.034), (0.97, 0.040)):
            _grass_blades(grass_pen, rng, u, bank_at(u) + 0.004, h, 24, 0.0016, 0.03)
        for _ in range(160):
            u = rng.uniform(0.0, 1.0)
            h = rng.uniform(0.006, 0.014) * (1.0 + 0.8 * (abs(u - 0.5) > 0.3))
            v = bank_at(u) + 0.002
            grass_pen.line([(u, v), (u + rng.uniform(-0.004, 0.004), v - h)], 0.0013)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        boab_mask = a.mask_of(boabs)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        grass_mask = a.mask_of(grass)
        mask = np.maximum.reduce([bank_mask, boab_mask, trunk_mask, crown_mask, grass_mask])
        layer = a.blank()
        earth = a.ramp([(0.0, mix(p["near_light"], p["near"], 0.25)), (0.64, mix(p["near_light"], p["near"], 0.25)), (0.80, mix(p["near_light"], p["near"], 0.70)), (1.0, p["near"])])
        a.put(layer, bank_mask, earth)
        stones = smoothstep(0.70, 0.74, a.noise("matamba near stones", cells=120.0, octaves=2))
        a.light(layer, bank_mask * stones * (a.v > 0.70), p["earth_light"], 0.20)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.40)
        a.put(layer, grass_mask, mix(p["grass"], p["near"], 0.35))
        a.light(layer, a.rim(grass_mask, 0.0015, 0.0, 0.2) * grass_mask, p["grass_light"], 0.35)
        a.put(layer, boab_mask, mix(p["boab"], p["near"], 0.40))
        a.light(layer, a.rim(boab_mask, 0.005, 0.0, 0.8) * boab_mask, p["boab_light"], 0.40)
        a.shade(layer, boab_mask * smoothstep(0.5, 0.75, a.noise("matamba near bark", cells=90.0, octaves=2, stretch=0.2)), 0.15)
        a.put(layer, trunk_mask, mix(p["trunk"], p["near"], 0.45))
        a.put(layer, crown_mask, mix(p["tree"], p["near"], 0.35))
        a.put(layer, crown_mask * smoothstep(0.58, 0.70, a.noise("matamba near leaves", cells=40.0, octaves=2)), mix(p["red_leaf"], p["near"], 0.30), 0.8)
        a.light(layer, a.rim(crown_mask, 0.0, 0.003, 0.0) * crown_mask, p["tree_light"], 0.40)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.18)
        haze(a, layer, p["low"], 0.10, None)
        return layer
    layer = _air(a, p, "matamba dry haze", p["low"], 0.36, p["near"], 0.18)
    a.put(layer, shafts(a, "matamba shafts", 4, 0.10, 0.0, 0.85, 0.06), p["glow"], 0.08)
    return layer


def matamba_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """A bare crooked branch of a baobab reaches into the top of the view
    at one place, with a few small twigs and a hanging fruit. Tufts of dry
    grass stand from below at one place."""
    del layer_lights
    rng = art_.rand("matamba foreground")
    u0 = rng.uniform(0.10, 0.30)
    for k, (start, end, w) in enumerate((((u0 - 0.04, 0.0), (u0 + 0.30, 0.300), 0.012), ((u0 + 0.12, 0.110), (u0 + 0.10, 0.330), 0.006), ((u0 + 0.22, 0.220), (u0 + 0.36, 0.250), 0.005))):
        ctrl = ((start[0] + end[0]) * 0.5 + 0.02, (start[1] + end[1]) * 0.5 - 0.06 * (k == 0))
        rib = _arch(start, ctrl, end, 14)
        for i in range(len(rib) - 1):
            pen.line([rib[i], rib[i + 1]], w * (1.0 - 0.6 * i / 14.0))
        for i in range(4, 14, 3):
            x, y = rib[i]
            side = 1.0 if i % 2 else -1.0
            tip = (x + side * rng.uniform(0.010, 0.022), min(0.380, y + rng.uniform(0.010, 0.030)))
            pen.line([(x, y), tip], 0.0018)
    # A baobab fruit on a long stalk.
    x, y = _arch((u0 - 0.04, 0.0), (u0 + 0.15, 0.09), (u0 + 0.30, 0.300), 14)[9]
    pen.line([(x, y), (x + 0.004, y + 0.040)], 0.0012)
    pen.ellipse(x + 0.004, y + 0.052, 0.006, 0.013)
    u = rng.uniform(0.62, 0.74)
    _grass_blades(pen, rng, u, 1.0, 1.0 - REST_BOTTOM + 0.004, 22, 0.0016, 0.05)
    _grass_blades(pen, rng, u + 0.05, 1.0, 1.0 - REST_BOTTOM - 0.012, 14, 0.0014, 0.04)


# ---------------------------------------------------------------------------
# The Congo river, about 1900
# ---------------------------------------------------------------------------


CONGO_RIVER = {
    "top": (140, 150, 144),
    "mid": (186, 190, 178),
    "low": (214, 212, 196),
    "glow": (226, 220, 196),
    "cloud": (206, 208, 198),
    "cloud_shadow": (150, 154, 148),
    "river": (126, 112, 88),
    "river_light": (186, 182, 164),
    "river_deep": (92, 82, 64),
    "forest": (52, 70, 54),
    "forest_light": (110, 128, 96),
    "forest_dark": (30, 40, 32),
    "trunk": (150, 146, 130),
    "bank": (112, 92, 70),
    "grass": (104, 116, 76),
    "timber": (122, 112, 96),
    "timber_dark": (78, 64, 50),
    "brick": (150, 98, 76),
    "whitewash": (206, 202, 188),
    "tin": (138, 140, 138),
    "tin_light": (184, 186, 182),
    "thatch": (160, 142, 104),
    "hole": (52, 48, 44),
    "hull": (60, 58, 56),
    "house": (200, 196, 182),
    "smoke": (160, 158, 154),
    "far": (190, 192, 180),
    "near": (30, 36, 30),
    "near_light": (98, 104, 82),
}

#: The level of the water at the near bank and at the foot of the far one.
CONGO_WATER = 0.628


def _stern_wheeler(hull: Pen, house: Pen, dark: Pen, u: float, v: float, s: float) -> None:
    """A small stern-wheel steamer of the river far off, going to the
    left: a long low hull, a deckhouse with a deck over it on thin posts, a
    tall thin funnel near the bow, and the paddle wheel at the stern in its
    frame. `(u, v)` is the middle of its waterline and `s` its length."""
    hull.poly([(u - s * 0.52, v - s * 0.05), (u + s * 0.40, v - s * 0.05), (u + s * 0.40, v + s * 0.01), (u - s * 0.44, v + s * 0.01)])
    house.rect(u - s * 0.36, v - s * 0.13, u + s * 0.32, v - s * 0.05)
    house.rect(u - s * 0.40, v - s * 0.155, u + s * 0.36, v - s * 0.13)
    house.rect(u - s * 0.18, v - s * 0.22, u + s * 0.10, v - s * 0.155)
    for k in range(8):
        x = u - s * 0.32 + k * s * 0.085
        dark.rect(x - s * 0.012, v - s * 0.115, x + s * 0.012, v - s * 0.075)
    dark.rect(u - s * 0.30, v - s * 0.46, u - s * 0.26, v - s * 0.155)
    dark.rect(u + s * 0.40, v - s * 0.15, u + s * 0.52, v + s * 0.01)
    for k in range(4):
        x = u + s * (0.41 + k * 0.03)
        house.line([(x, v - s * 0.14), (x, v)], s * 0.006)


def _emergent_tree(trunk: Pen, crown: Pen, rng, u: float, v: float, h: float) -> None:
    """A giant of the rainforest that stands over the canopy: a tall pale
    straight trunk, a few limbs that spread near its top, and a crown that
    is wide and flat, like an umbrella."""
    top = (u + rng.uniform(-0.004, 0.004), v - h * 0.86)
    trunk.line([(u, v), top], h * 0.030)
    for side in (-1.0, 1.0):
        trunk.line([(top[0], top[1] + h * 0.06), (top[0] + side * h * 0.16, top[1] - h * 0.02)], h * 0.014)
    _lumpy_crown(crown, rng, top[0], top[1] - h * 0.04, h * 0.26, h * 0.06, 50)
    crown.ellipse(top[0], top[1] - h * 0.02, h * 0.22, h * 0.035)


def _bungalow(walls: Pen, roof: Pen, holes: Pen, posts: Pen, u: float, v: float, w: float, h: float) -> None:
    """A mission bungalow of brick on a low base: a wide roof of iron that
    comes down over a verandah on thin posts, and a door and windows in
    the shade of the verandah."""
    walls.rect(u - w, v - h, u + w, v + 0.001)
    roof.poly([(u - w * 1.30, v - h * 0.95), (u - w * 0.70, v - h * 1.55), (u + w * 0.70, v - h * 1.55), (u + w * 1.30, v - h * 0.95)])
    for k in range(6):
        x = u - w * 1.22 + k * w * 2.44 / 5.0
        posts.rect(x - w * 0.025, v - h * 0.96, x + w * 0.025, v + 0.001)
    holes.rect(u - w * 0.12, v - h * 0.70, u + w * 0.12, v + 0.001)
    for x in (u - w * 0.60, u + w * 0.60):
        holes.rect(x - w * 0.14, v - h * 0.70, x + w * 0.14, v - h * 0.30)


def _store(walls: Pen, roof: Pen, ribs: Pen, holes: Pen, u: float, v: float, w: float, h: float) -> None:
    """The long store of a trading post: a timber wall with wide doors, a
    low roof of corrugated iron, its ribs running down the slope."""
    walls.rect(u - w, v - h, u + w, v + 0.001)
    roof.poly([(u - w * 1.06, v - h), (u - w * 0.98, v - h * 1.55), (u + w * 0.98, v - h * 1.55), (u + w * 1.06, v - h)])
    for k in range(int(w * 1600)):
        x = u - w + k / 800.0
        ribs.line([(x, v - h * 1.55), (x, v - h)], 0.0006)
    for x in (u - w * 0.55, u, u + w * 0.55):
        holes.rect(x - w * 0.09, v - h * 0.75, x + w * 0.09, v + 0.001)


def history_congo_river_1900(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = CONGO_RIVER
    water_v = CONGO_WATER
    if layer_key == "sky":
        # A still grey-green day: low cloud in soft bands, no sun, a thin
        # line of forest far off where the river turns, and the wide brown
        # water under it, pale with the sky and the mist.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.86)), (0.30, p["top"]), (0.50, p["mid"]), (HORIZON - 0.004, p["low"]),
                                 (HORIZON + 0.004, mix(p["river_light"], p["low"], 0.40)), (0.70, mix(p["river"], p["river_light"], 0.35)), (1.0, p["river"])]))
        for k, (centre, half, cover, alpha) in enumerate(((0.20, 0.12, 0.62, 0.55), (0.40, 0.08, 0.55, 0.45), (0.52, 0.04, 0.50, 0.40))):
            clouds = cloud_mask(a, ("congo cloud", k), centre, half, cells=3.0 + k, cover=cover, soft=0.35, stretch=5.0)
            a.put(layer, clouds, mix(p["cloud"], p["low"], k * 0.25), alpha)
            a.put(layer, clouds * a.band(centre + half * 0.5, half * 0.6), p["cloud_shadow"], 0.20)
        trees, _ = a.ridge("congo far trees", HORIZON - 0.006, 0.004, cells=40.0, octaves=3)
        trees = trees * smoothstep(HORIZON + 0.004, HORIZON + 0.001, a.v)
        a.put(layer, trees, mix(p["forest"], p["low"], 0.62))
        a.tint(layer, fog(a, "congo horizon mist", HORIZON - 0.002, 0.020, 3.0), p["low"], 0.60)
        lines = smoothstep(0.64, 0.84, a.noise("congo far current", cells=60.0, octaves=2, stretch=16.0))
        a.light(layer, (a.v > HORIZON + 0.004) * lines, p["river_light"], 0.20)
        _textbook(a, layer, 0.07)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far congo")
        # The far bank at the right: a dark wall of rainforest that stands
        # in the water, tall trees over it, and vines that hang down its
        # face.
        _, wall_line = a.ridge("congo forest wall", 0.520, 0.012, cells=8.0, octaves=3)
        wall_line = wall_line + 0.11 * smoothstep(0.71, 0.62, a.u[0])
        forest, forest_pen = a.drawing()
        emergents, emergent_pen = a.drawing()
        e_crowns, e_crown_pen = a.drawing()
        vines, vine_pen = a.drawing()
        _canopy(forest_pen, rng, wall_line, 0.62, 1.02, 0.010, 0.010, 0.022, 220)
        forest_pen.poly([(0.63, water_v)] + [(float(u), _at(wall_line, float(u)) + 0.004) for u in np.linspace(0.63, 1.0, 40)] + [(1.02, water_v)])
        for eu, h in ((0.71, 0.18), (0.80, 0.22), (0.90, 0.17), (0.98, 0.20)):
            _emergent_tree(emergent_pen, e_crown_pen, rng, eu, water_v, h)
        for _ in range(40):
            u = rng.uniform(0.66, 1.0)
            v0 = _at(wall_line, u) + 0.006
            pts = [(u + 0.002 * math.sin(t * 6.0 + u * 40.0), v0 + (water_v - 0.006 - v0) * t * rng.uniform(0.5, 1.0)) for t in np.linspace(0.0, 1.0, 8)]
            vine_pen.line(pts, 0.0010)
        # The near bank at the left: forest behind, and in front of it the
        # mission station and the trading post on cleared ground, a jetty
        # into the river, and a flagpole with no flag.
        _, back_line = a.ridge("congo near forest", 0.540, 0.010, cells=6.0, octaves=3)
        back_line = back_line + 0.03 * smoothstep(0.40, 0.54, a.u[0])
        back, back_pen = a.drawing()
        _canopy(back_pen, rng, back_line, -0.02, 0.53, 0.010, 0.010, 0.020, 200)
        back_pen.poly([(-0.02, water_v)] + [(float(u), _at(back_line, float(u)) + 0.006) for u in np.linspace(-0.02, 0.54, 30)] + [(0.54, water_v)])
        ground_v = water_v - 0.004
        clearing, clearing_pen = a.drawing()
        clearing_pen.poly([(-0.02, ground_v - 0.012), (0.46, ground_v - 0.006), (0.50, water_v + 0.002), (-0.02, water_v + 0.002)])
        walls, wall_pen = a.drawing()
        brick, brick_pen = a.drawing()
        roofs, roof_pen = a.drawing()
        thatch, thatch_pen = a.drawing()
        ribs, rib_pen = a.drawing()
        holes, hole_pen = a.drawing()
        posts, post_pen = a.drawing()
        _bungalow(brick_pen, roof_pen, hole_pen, post_pen, 0.075, ground_v - 0.008, 0.046, 0.030)
        # The schoolhouse: plain whitewashed walls, a steep roof of thatch,
        # a row of windows. Nothing stands on its roof.
        sx, sw, sh = 0.200, 0.040, 0.026
        wall_pen.rect(sx - sw, ground_v - 0.006 - sh, sx + sw, ground_v - 0.006)
        thatch_pen.poly([(sx - sw * 1.18, ground_v - 0.006 - sh + 0.002), (sx - sw * 0.80, ground_v - 0.006 - sh * 2.1), (sx + sw * 0.80, ground_v - 0.006 - sh * 2.1), (sx + sw * 1.18, ground_v - 0.006 - sh + 0.002)])
        for k in range(4):
            x = sx - sw * 0.70 + k * sw * 0.47
            hole_pen.rect(x - sw * 0.10, ground_v - 0.006 - sh * 0.75, x + sw * 0.10, ground_v - 0.006 - sh * 0.35)
        _store(wall_pen, roof_pen, rib_pen, hole_pen, 0.37, ground_v - 0.004, 0.080, 0.026)
        pole, pole_pen = a.drawing()
        pole_pen.line([(0.265, ground_v - 0.006), (0.265, ground_v - 0.100)], 0.0018)
        pole_pen.ellipse(0.265, ground_v - 0.101, 0.0024)
        jetty, jetty_pen = a.drawing()
        jetty_pen.rect(0.44, water_v - 0.002, 0.54, water_v + 0.002)
        for x in np.arange(0.45, 0.545, 0.016):
            jetty_pen.line([(x, water_v - 0.002), (x, water_v + 0.010)], 0.0016)
        # Stacks of cut wood for the steamers beside the jetty.
        wood, wood_pen = a.drawing()
        for wx in (0.475, 0.50):
            wood_pen.rect(wx - 0.010, water_v - 0.012, wx + 0.010, water_v - 0.002)
        # The steamer, far off on the river, and its thin smoke.
        hull, hull_pen = a.drawing()
        deck, deck_pen = a.drawing()
        dark, dark_pen = a.drawing()
        steamer = (0.595, water_v - 0.003, 0.085)
        _stern_wheeler(hull_pen, deck_pen, dark_pen, *steamer)
        smoke = _plume(a, "congo steamer smoke", steamer[0] - steamer[2] * 0.28, steamer[1] - steamer[2] * 0.46, 0.10, 0.08, 0.006)
        forest_mask = a.mask_of(forest)
        e_trunk_mask = a.mask_of(emergents) * (a.v < 0.55)
        e_crown_mask = a.mask_of(e_crowns)
        vine_mask = a.mask_of(vines) * forest_mask
        back_mask = a.mask_of(back)
        clearing_mask = a.mask_of(clearing)
        wall_mask = a.mask_of(walls)
        brick_mask = a.mask_of(brick)
        roof_mask = a.mask_of(roofs)
        thatch_mask = a.mask_of(thatch)
        rib_mask = a.mask_of(ribs) * roof_mask
        hole_mask = a.mask_of(holes) * np.maximum(wall_mask, brick_mask)
        post_mask = a.mask_of(posts)
        pole_mask = a.mask_of(pole)
        jetty_mask = a.mask_of(jetty)
        wood_mask = a.mask_of(wood)
        boat = np.maximum.reduce([a.mask_of(hull), a.mask_of(deck), a.mask_of(dark)])
        water = smoothstep(HORIZON + 0.010, HORIZON + 0.016, a.v)
        banks = np.maximum.reduce([forest_mask, e_trunk_mask, e_crown_mask, back_mask])
        station = np.maximum.reduce([clearing_mask, wall_mask, brick_mask, roof_mask, thatch_mask, post_mask, pole_mask, jetty_mask, wood_mask])
        mask = np.maximum.reduce([banks, station, boat, water])
        layer = solid(a, mask, mix(p["forest"], p["far"], 0.40), mix(p["forest"], p["far"], 0.20), 0.46, 0.62, "congo far", 0.05)
        # The river: brown and still, with the dark pictures of the forest
        # in it, faint lines of the current, and mist that lies on it.
        a.put(layer, water, a.ramp([(0.0, mix(p["river_light"], p["low"], 0.30)), (HORIZON + 0.016, mix(p["river_light"], p["low"], 0.30)),
                                     (0.66, mix(p["river"], p["river_light"], 0.30)), (0.72, p["river"]), (1.0, p["river_deep"])]))
        a.put(layer, _reflected(a, banks, water_v, "congo forest ripple", water * (a.v > water_v)), mix(p["forest_dark"], p["river"], 0.45), 0.45)
        a.put(layer, _reflected(a, station, water_v + 0.002, "congo station ripple", water * (a.v > water_v + 0.002)), mix(p["timber"], p["river"], 0.45), 0.30)
        lines = smoothstep(0.64, 0.84, a.noise("congo current", cells=60.0, octaves=2, stretch=18.0))
        a.light(layer, water * lines * smoothstep(water_v + 0.004, water_v + 0.06, a.v), p["river_light"], 0.18)
        # The forests: dark and close, a little lighter on their tops.
        a.put(layer, banks, mix(p["forest"], p["far"], 0.22))
        a.put(layer, back_mask, mix(p["forest"], p["far"], 0.32))
        lumps = a.noise("congo crowns", cells=70.0, octaves=3)
        a.light(layer, banks * smoothstep(0.58, 0.78, lumps), mix(p["forest_light"], p["far"], 0.3), 0.30)
        a.shade(layer, forest_mask * smoothstep(0.55, 0.62, a.v), 0.25)
        a.put(layer, vine_mask, mix(p["forest_dark"], p["far"], 0.15), 0.8)
        a.put(layer, e_trunk_mask * (1.0 - forest_mask), mix(p["trunk"], p["forest"], 0.45))
        a.put(layer, e_crown_mask, mix(p["forest"], p["far"], 0.28))
        a.light(layer, a.rim(e_crown_mask, 0.0, 0.003, 0.3) * e_crown_mask, mix(p["forest_light"], p["glow"], 0.3), 0.40)
        # The station: the cleared bank, the bungalow of brick, the
        # whitewashed school, the store of timber, the iron roofs and the
        # thatch, the jetty and the cut wood.
        a.put(layer, clearing_mask, mix(p["bank"], p["far"], 0.30))
        a.put(layer, clearing_mask * smoothstep(0.50, 0.65, a.noise("congo clearing grass", cells=40.0, octaves=2, stretch=3.0)), mix(p["grass"], p["far"], 0.30), 0.7)
        a.put(layer, brick_mask, mix(p["brick"], p["far"], 0.25))
        a.put(layer, wall_mask, mix(p["whitewash"], p["far"], 0.15))
        a.put(layer, wall_mask * (a.u > 0.28), mix(p["timber"], p["far"], 0.25))
        a.put(layer, wall_mask * (a.u > 0.28) * (np.abs(((a.v * 700.0) % 1.0) - 0.5) > 0.36), mix(p["timber_dark"], p["far"], 0.25), 0.6)
        a.put(layer, hole_mask, mix(p["hole"], p["far"], 0.25))
        a.put(layer, post_mask, mix(p["whitewash"], p["far"], 0.20))
        a.put(layer, roof_mask, mix(p["tin"], p["far"], 0.20))
        a.put(layer, rib_mask, mix(p["tin_light"], p["far"], 0.20), 0.6)
        a.shade(layer, roof_mask * smoothstep(0.5, 0.7, a.noise("congo rust", cells=60.0, octaves=2)), 0.12)
        a.put(layer, thatch_mask, mix(p["thatch"], p["far"], 0.20))
        a.shade(layer, thatch_mask * np.clip(1.0 - np.abs(((a.u * 800.0) % 1.0) - 0.5) / 0.15, 0.0, 1.0), 0.12)
        a.put(layer, pole_mask, mix(p["whitewash"], p["far"], 0.25))
        a.put(layer, jetty_mask, mix(p["timber"], p["far"], 0.20))
        a.put(layer, wood_mask, mix(p["timber"], p["far"], 0.15))
        a.put(layer, wood_mask * (np.abs(((a.v * 1200.0) % 1.0) - 0.5) > 0.35), mix(p["timber_dark"], p["far"], 0.15), 0.8)
        # The steamer.
        a.put(layer, a.mask_of(hull), mix(p["hull"], p["far"], 0.25))
        a.put(layer, a.mask_of(deck), mix(p["house"], p["far"], 0.20))
        a.put(layer, a.mask_of(dark), mix(p["hull"], p["far"], 0.20))
        a.put(layer, _reflected(a, boat, steamer[1] + 0.001, "congo steamer ripple", water * (1.0 - boat)), mix(p["hull"], p["river"], 0.55), 0.30)
        a.put(layer, smoke, p["smoke"], 0.55)
        mask = np.maximum(mask, smoke * 0.55)
        a.tint(layer, fog(a, "congo river mist", water_v - 0.004, 0.014, 3.0) * mask, p["low"], 0.55)
        a.tint(layer, fog(a, "congo forest mist", 0.50, 0.03, 2.5) * banks, p["low"], 0.30)
        haze(a, layer, p["low"], 0.10, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near congo")
        bank, ground, bank_at = _bank(a, "near congo", 0.040, 0.036)
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        leaves, leaf_pen = a.drawing()
        vines, vine_pen = a.drawing()
        grass, grass_pen = a.drawing()
        # A tall tree of the forest with buttress roots at the left, its
        # vines hanging; broad leaves of the undergrowth at the right. The
        # middle is a calm bank of mud and rank grass.
        u, v = 0.06, bank_at(0.06) + 0.006
        trunk_pen.poly([(u - 0.020, v), (u + 0.020, v), (u + 0.012, 0.25), (u - 0.012, 0.25)])
        for side, reach, rise in ((-1.0, 0.055, 0.10), (1.0, 0.060, 0.12), (1.0, 0.030, 0.16)):
            trunk_pen.poly([(u + side * 0.006, v - rise), (u + side * reach, v + 0.002), (u + side * (reach - 0.012), v + 0.002), (u + side * 0.006, v - 0.01)])
        _lumpy_crown(crown_pen, rng, u + 0.04, 0.25, 0.16, 0.07, 160)
        crown_pen.ellipse(u + 0.04, 0.25, 0.13, 0.05)
        for vu in (0.11, 0.15, 0.19):
            _hanging_vine(vine_pen, rng, vu, 0.25, rng.uniform(0.46, 0.56), 0.0016)
        for x, h in ((0.82, 0.10), (0.89, 0.15), (0.96, 0.12), (0.22, 0.07)):
            for k in range(5):
                ang = -90.0 + (k - 2) * 28.0 + rng.uniform(-6.0, 6.0)
                base = (x, bank_at(x) + 0.004)
                tip = polar(*base, h * rng.uniform(0.8, 1.0), ang)
                rib = _arch(base, polar(*base, h * 0.55, ang + (k - 2) * -6.0), (tip[0], tip[1] + h * 0.15), 10)
                leaf_pen.line(rib[:5], 0.0018)
                _leaf(leaf_pen, rib[3:], h * 0.11, 0.6)
        for _ in range(180):
            uu = rng.uniform(0.0, 1.0)
            h = rng.uniform(0.006, 0.016) * (1.0 + 0.8 * (abs(uu - 0.5) > 0.3))
            vv = bank_at(uu) + 0.002
            grass_pen.line([(uu, vv), (uu + rng.uniform(-0.006, 0.006), vv - h)], 0.0013)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        leaf_mask = a.mask_of(leaves)
        vine_mask = a.mask_of(vines)
        grass_mask = a.mask_of(grass)
        mask = np.maximum.reduce([bank_mask, trunk_mask, crown_mask, leaf_mask, vine_mask, grass_mask])
        layer = a.blank()
        earth = a.ramp([(0.0, mix(p["bank"], p["near"], 0.45)), (0.66, mix(p["bank"], p["near"], 0.45)), (0.78, mix(p["near_light"], p["near"], 0.75)), (1.0, p["near"])])
        a.put(layer, bank_mask, earth)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.18)
        a.put(layer, grass_mask, mix(p["grass"], p["near"], 0.45))
        a.put(layer, trunk_mask, mix(p["trunk"], p["near"], 0.55))
        a.light(layer, a.rim(trunk_mask, 0.003, 0.0, 0.0) * trunk_mask, p["glow"], 0.20)
        a.shade(layer, trunk_mask * smoothstep(0.5, 0.75, a.noise("congo near bark", cells=90.0, octaves=2, stretch=0.2)), 0.15)
        a.put(layer, crown_mask, mix(p["forest"], p["near"], 0.40))
        a.light(layer, a.rim(crown_mask, 0.0, 0.003, 0.3) * crown_mask, p["forest_light"], 0.30)
        a.put(layer, vine_mask, mix(p["forest"], p["near"], 0.45))
        a.put(layer, leaf_mask, mix(p["forest"], p["near"], 0.30))
        a.light(layer, a.rim(leaf_mask, 0.002, 0.002, 0.0) * leaf_mask, p["forest_light"], 0.35)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.18)
        haze(a, layer, p["low"], 0.14, None)
        return layer
    layer = _air(a, p, "congo river mist", p["low"], 0.40, scale(p["near"], 0.8), 0.18)
    return layer


def congo_river_1900_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Broad leaves of the rainforest hang into the top of the view at two
    places, and a vine hangs down beside one of them. A few broad leaves
    stand from below at one place."""
    del layer_lights
    rng = art_.rand("congo foreground")
    for k in range(2):
        u0 = 0.08 + (k + rng.uniform(0.2, 0.8)) * 0.42
        stem = _arch((u0, 0.0), (u0 + 0.03, 0.12), (u0 + 0.05, 0.24), 12)
        pen.line(stem, 0.0024)
        for n, i in enumerate((4, 7, 10, 12)):
            x, y = stem[i]
            side = 1.0 if n % 2 else -1.0
            tip = (x + side * rng.uniform(0.03, 0.05), min(0.378, y + rng.uniform(0.09, 0.13)))
            rib = _arch((x, y), (x + side * 0.03, y + 0.01), tip, 10)
            _leaf(pen, rib, 0.016, 0.55)
        if k == 0:
            _hanging_vine(pen, rng, u0 + 0.09, 0.0, 0.380, 0.0016)
    u = rng.uniform(0.44, 0.56)
    for j in range(3):
        base = (u + (j - 1) * 0.02, 1.0)
        tip = (u + (j - 1) * 0.05, REST_BOTTOM - 0.002 + j % 2 * 0.010)
        rib = _arch(base, (base[0], tip[1] + 0.06), tip, 10)
        pen.line(rib[:6], 0.0020)
        _leaf(pen, rib[4:], 0.014, 0.6)
