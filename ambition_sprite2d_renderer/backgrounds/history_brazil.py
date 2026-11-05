"""The scenes of the History dimension: Brazil and Amazonia.

The History dimension is a grid. East is later, and each floor is a region
of the world. These rooms are on the floor of South America. They show the
Amazon floodplain, where people made the forest a garden; Palmares, the free
state that people who escaped slavery made in the hills; and Rio de Janeiro
on the day that slavery ended in Brazil. They use the same sepia of an old
textbook and the same rules as `history_eras.py` and `history_bengal.py`.
The people of these places show skill and courage of their own; nothing
here is a joke on them, and no picture here shows slavery.

- ``history_marajo`` (Marajó island and the Amazon floodplain, about 1000
  CE). An early morning in the season of the flood. A wide brown river goes
  to the horizon under a soft sky with mist. At the left, the forest stands
  in the water, and a giant samaúma (kapok) with tall buttress roots stands
  over it. In the middle and at the right, mounds of earth (tesos) stand
  above the flood, with big houses of thatch, palms and the smoke of a
  fire on them. Leaves of the Victoria water lily lie on the still water
  near the bank, and the back of a pink river dolphin shows far off.
  Heliconia flowers and palm fronds are near.
- ``history_palmares`` (Serra da Barriga, Alagoas, about 1680). A clear
  afternoon. The forested hill goes up at the right, with groves of palms
  (Palmares has its name from them). A palisade of logs goes along it, and
  in it is a village of huts of thatch (mocambos), with fields of maize and
  manioc in front. Smoke goes up from a forge. Far below at the left, the
  flat green plain of sugar cane goes to the horizon. Palm fronds and
  banana leaves are near.
- ``history_rio_1888`` (Rio de Janeiro, May 1888). A bright morning. The
  blue water of Guanabara Bay, and across it the granite dome of the
  Sugarloaf. At the left, the old city at the water: tall houses with
  painted and tiled fronts and red roofs, green and yellow flags and
  bunting on their balconies, a line of royal palms along the quay, and a
  small crowd far off. A steam ferry goes over the bay. Palm fronds and
  flowers are near.

No picture here shows a deity, a religious sign or a church inside. The
far towers of the city are plain towers with no sign on them.

The bright detail is far off or at the edges, and the middle of each near
layer is calm, so the play in front of it reads. The things that drift in the
air are the room's motes (`terrain/motes.py`), not part of these pictures.
"""

from __future__ import annotations

import math

import numpy as np

from .artkit import Art, Pen, mix, polar, scale, smoothstep
from .history_americas_pacific import _canopy, _fronds, _royal_palm
from .history_bengal import _banana, _palm
from .history_east_asia_coast import _bank, _grass_blades, _lumpy_crown, _reflected
from .history_eras import REST_BOTTOM, _air, _at, _heaps, _plume, _sun, _textbook
from .history_origins import _arch, _land, _leaf
from .parts import HORIZON, cloud_mask, fog, haze, shafts, solid

# ---------------------------------------------------------------------------
# Parts that more than one room has
# ---------------------------------------------------------------------------


def _thatch_house(walls: Pen, roof: Pen, door: Pen, u: float, v: float, w: float, h: float, steep: float = 1.4) -> None:
    """A house with low walls and a tall roof of palm thatch that comes
    down far over them, as the houses of the Amazon and of Palmares have.
    `(u, v)` is the middle of its foot, `w` its half width and `h` the
    height of its walls. `steep` sets the height of the roof."""
    walls.rect(u - w, v - h, u + w, v + 0.001)
    roof.poly([(u - w * 1.18, v - h * 0.55), (u - w * 0.30, v - h * (1.0 + steep)), (u + w * 0.30, v - h * (1.0 + steep)), (u + w * 1.18, v - h * 0.55)])
    door.rect(u - w * 0.16, v - h * 0.50, u + w * 0.16, v + 0.001)


def _heliconia(stems: Pen, leaves: Pen, bracts: Pen, tips: Pen, rng, u: float, v: float, h: float) -> None:
    """A heliconia: long paddle leaves on tall stalks that stand up and out,
    and between them a stalk with a hanging chain of red bracts, each
    bract a boat shape with a yellow tip, turned left and right in turn."""
    for k in range(5):
        spread = (k - 2) * 16.0 + rng.uniform(-6.0, 6.0)
        length = h * rng.uniform(0.75, 1.0)
        tip = polar(u, v, length, -90.0 + spread)
        rib = _arch((u, v + 0.004), polar(u, v, length * 0.5, -90.0 + spread * 0.4), tip, 12)
        stems.line(rib[:6], h * 0.010)
        _leaf(leaves, rib[4:], h * 0.075, 0.7)
    # The flower stalk: it stands up, then the chain of bracts hangs from
    # its top.
    top = (u + h * 0.10, v - h * 0.78)
    stems.line(_arch((u, v), (u + h * 0.06, v - h * 0.40), top, 8), h * 0.010)
    y = top[1]
    for i in range(6):
        side = 1.0 if i % 2 == 0 else -1.0
        size = h * (0.075 - i * 0.006)
        cx = top[0] + side * size * 0.45
        bracts.poly([(top[0], y), (cx + side * size * 0.85, y - size * 0.35), (cx + side * size * 0.95, y + size * 0.10), (top[0], y + size * 0.55)])
        tips.ellipse(cx + side * size * 0.85, y - size * 0.30, size * 0.18, size * 0.12)
        y += size * 0.62


def _victoria(rim: Pen, leaf: Pen, flower: Pen, u: float, v: float, r: float, bloom: bool) -> None:
    """A leaf of the Victoria water lily on still water, seen from the side
    and far off: a flat round leaf with a low upturned rim. A flower may
    stand beside it, a round white cup."""
    rim.ellipse(u, v, r, r * 0.20)
    leaf.ellipse(u, v - r * 0.06, r * 0.93, r * 0.13)
    if bloom:
        flower.ellipse(u + r * 1.25, v - r * 0.12, r * 0.22, r * 0.16)


# ---------------------------------------------------------------------------
# Marajó: the Amazon floodplain, about 1000 CE
# ---------------------------------------------------------------------------


MARAJO = {
    "top": (132, 154, 168),
    "mid": (210, 204, 190),
    "low": (244, 224, 194),
    "glow": (255, 210, 156),
    "sun": (255, 242, 216),
    "cloud": (240, 230, 216),
    "cloud_shadow": (172, 164, 162),
    "river": (150, 120, 84),
    "river_light": (214, 196, 164),
    "river_deep": (104, 82, 58),
    "forest": (54, 88, 58),
    "forest_light": (130, 158, 92),
    "samauma": (196, 188, 168),
    "trunk": (98, 84, 66),
    "mound": (112, 82, 56),
    "mound_light": (166, 126, 86),
    "grass": (98, 136, 62),
    "thatch": (186, 154, 98),
    "wall": (150, 112, 74),
    "door": (54, 38, 30),
    "lily": (86, 132, 64),
    "lily_rim": (150, 70, 78),
    "flower": (248, 236, 236),
    "dolphin": (226, 164, 168),
    "canoe": (78, 56, 40),
    "smoke": (196, 190, 184),
    "helico": (204, 52, 40),
    "helico_tip": (242, 204, 72),
    "leaf": (70, 116, 58),
    "leaf_light": (160, 190, 104),
    "far": (210, 204, 190),
    "near": (30, 38, 28),
    "near_light": (130, 136, 88),
}

#: The level where the far forest and the far mounds stand in the water.
MARAJO_WATER = 0.632


def _samauma(trunk: Pen, crown: Pen, rng, u: float, v: float, h: float) -> None:
    """A samaúma, the giant kapok of the Amazon: a straight pale trunk with
    tall thin buttress roots like walls at its foot, long level limbs high
    up, and a wide crown like an umbrella over the forest."""
    w = h * 0.030
    trunk.poly([(u - w, v + 0.004), (u + w, v + 0.004), (u + w * 0.62, v - h * 0.80), (u - w * 0.62, v - h * 0.80)])
    for side, reach, rise in ((-1.0, 4.4, 0.26), (1.0, 3.6, 0.22), (-1.0, 2.2, 0.32), (1.0, 2.0, 0.30)):
        trunk.poly([(u + side * w * 0.4, v - h * rise), (u + side * w * reach, v + 0.004), (u + side * w * (reach - 0.9), v + 0.004), (u + side * w * 0.4, v - h * 0.02)])
    top = (u, v - h * 0.80)
    for k in range(6):
        side = -1.0 if k % 2 else 1.0
        reach = h * rng.uniform(0.24, 0.38)
        start = (u, top[1] + h * (0.08 - k * 0.012))
        end = (u + side * reach, start[1] - h * rng.uniform(0.06, 0.10))
        trunk.line(_arch(start, (u + side * reach * 0.5, start[1] - h * 0.02), end, 6), w * 0.40)
        _lumpy_crown(crown, rng, end[0], end[1] - h * 0.03, h * 0.15, h * 0.05, 40)
    # The crown is an umbrella: wide and flat, its underside nearly level.
    crown.ellipse(u, top[1] - h * 0.10, h * 0.36, h * 0.055)
    _lumpy_crown(crown, rng, u, top[1] - h * 0.13, h * 0.30, h * 0.06, 60)


def _acai(trunk: Pen, crown: Pen, rng, u: float, v: float, h: float) -> None:
    """A clump of açaí palms: three or four thin stems that lean apart, each
    with a small head of fronds whose leaflets hang down."""
    for k in range(4):
        lean = (k - 1.5) * h * 0.08 + rng.uniform(-0.01, 0.01) * h
        hh = h * rng.uniform(0.75, 1.0)
        pts = [(u + lean * t * t, v + 0.003 - hh * t) for t in np.linspace(0.0, 1.0, 8)]
        trunk.line(pts, h * 0.012)
        _fronds(crown, rng, pts[-1], hh, 8, 0.22, 0.85, h * 0.008, 0.07)


def _dugout(hull: Pen, man: Pen, u: float, v: float, s: float, facing: float = 1.0) -> None:
    """A dugout canoe far off, with one person who kneels and paddles."""
    f = facing
    hull.poly([(u - s * 0.5 * f, v - s * 0.05), (u - s * 0.40 * f, v + s * 0.03), (u + s * 0.40 * f, v + s * 0.03), (u + s * 0.52 * f, v - s * 0.06), (u, v - s * 0.02)])
    man.ellipse(u - s * 0.10 * f, v - s * 0.12, s * 0.05, s * 0.09)
    man.ellipse(u - s * 0.10 * f, v - s * 0.24, s * 0.035)
    man.line([(u + s * 0.05 * f, v - s * 0.22), (u + s * 0.20 * f, v + s * 0.06)], s * 0.018)


def history_marajo(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = MARAJO
    sun_at = (0.26, 0.44)
    water_v = MARAJO_WATER
    if layer_key == "sky":
        # An early morning: a soft blue-grey sky over the river, banks of
        # pale cloud, a low sun that is a bright place in the mist, and the
        # far bank as a low line of forest. The river under it shows the sky.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.92)), (0.28, p["top"]), (0.48, p["mid"]), (HORIZON - 0.01, p["low"]),
                                 (HORIZON + 0.002, mix(p["river_light"], p["low"], 0.55)), (1.0, mix(p["river"], p["low"], 0.35))]))
        clouds = cloud_mask(a, "marajo clouds", 0.33, 0.12, cells=3.0, cover=0.50, soft=0.28, stretch=3.8)
        a.put(layer, clouds, p["cloud"], 0.55)
        a.put(layer, clouds * a.band(0.39, 0.06), p["cloud_shadow"], 0.22)
        low = cloud_mask(a, "marajo low clouds", 0.50, 0.05, cells=4.0, cover=0.45, soft=0.30, stretch=5.0)
        a.put(layer, low, mix(p["cloud"], p["glow"], 0.3), 0.40)
        a.light(layer, a.spot(*sun_at, 0.24, 2.0, squash=1.3), p["glow"], 0.45)
        a.light(layer, a.spot(*sun_at, 0.07, 1.4), p["glow"], 0.45)
        a.put(layer, a.spot(*sun_at, 0.028, 0.5), p["sun"], 0.80)
        trees, _ = a.ridge("marajo far trees", HORIZON - 0.005, 0.003, cells=50.0, octaves=3)
        trees = trees * smoothstep(HORIZON + 0.004, HORIZON + 0.001, a.v)
        a.put(layer, trees, mix(p["forest"], p["low"], 0.65))
        a.tint(layer, fog(a, "marajo horizon mist", HORIZON - 0.002, 0.016, 3.0), p["low"], 0.55)
        # The road of the sun on the water.
        glints = smoothstep(0.62, 0.82, a.noise("marajo sky glints", cells=80.0, octaves=2, stretch=9.0))
        a.light(layer, (a.v > HORIZON + 0.002) * glints * a.spot(sun_at[0], HORIZON + 0.02, 0.18, 1.0, squash=0.8), p["glow"], 0.55)
        _textbook(a, layer, 0.08)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far marajo")
        # The flooded forest at the left: crowns on a canopy line, the
        # trunks under them standing in the water, and the samaúma over all.
        _, canopy_line = a.ridge("marajo canopy", 0.565, 0.010, cells=10.0, octaves=3)
        canopy_line = canopy_line + 0.030 * smoothstep(0.30, 0.42, a.u[0])
        crowns, crown_pen = a.drawing()
        trunks, trunk_pen = a.drawing()
        giant, giant_pen = a.drawing()
        giant_crown, giant_crown_pen = a.drawing()
        _canopy(crown_pen, rng, canopy_line, -0.03, 0.40, 0.012, 0.012, 0.024, 150)
        for _ in range(46):
            u = rng.uniform(-0.02, 0.40)
            top = _at(canopy_line, max(0.0, min(0.999, u))) + 0.006
            trunk_pen.line([(u, top), (u + rng.uniform(-0.003, 0.003), water_v + 0.002)], rng.uniform(0.0016, 0.0030))
        _samauma(giant_pen, giant_crown_pen, rng, 0.17, water_v + 0.002, 0.20)
        forest_mask = a.mask_of(crowns) * (a.v < water_v)
        trunk_mask = a.mask_of(trunks) * (1.0 - forest_mask)
        giant_mask = a.mask_of(giant)
        giant_crown_mask = a.mask_of(giant_crown)
        under = smoothstep(0.42, 0.36, a.u) * (a.v > canopy_line[None, :]) * (a.v < water_v)
        # The tesos: a big mound in the middle and a smaller one far off at
        # the right, each with houses of thatch, a few palms and a fire.
        mounds, mound_pen = a.drawing()
        walls, wall_pen = a.drawing()
        roofs, roof_pen = a.drawing()
        doors, door_pen = a.drawing()
        palm_trunks, palm_trunk_pen = a.drawing()
        palm_crowns, palm_crown_pen = a.drawing()
        teso = ((0.62, 0.150, 0.026), (0.93, 0.070, 0.012))
        for k, (mu, half, rise) in enumerate(teso):
            pts = [(mu + half * x, water_v + 0.002 - rise * (1.0 - x * x) ** 0.6) for x in np.linspace(-1.0, 1.0, 40)]
            mound_pen.poly(pts)
        houses = ((0.565, 0.016, 0.009), (0.625, 0.022, 0.011), (0.685, 0.015, 0.008), (0.925, 0.009, 0.005))
        for hu, hw, hh in houses:
            mu, half, rise = teso[0] if hu < 0.8 else teso[1]
            x = (hu - mu) / half
            foot = water_v + 0.002 - rise * max(0.0, 1.0 - x * x) ** 0.6 + 0.002
            _thatch_house(wall_pen, roof_pen, door_pen, hu, foot, hw, hh)
        for pu in (0.51, 0.595, 0.655, 0.72, 0.90, 0.955):
            mu, half, rise = teso[0] if pu < 0.8 else teso[1]
            x = (pu - mu) / half
            foot = water_v + 0.002 - rise * max(0.0, 1.0 - x * x) ** 0.6 + 0.003
            _acai(palm_trunk_pen, palm_crown_pen, rng, pu, foot, rng.uniform(0.040, 0.060) * (0.6 if pu > 0.8 else 1.0))
        smoke = _plume(a, "marajo hearth smoke", 0.655, water_v - 0.020, 0.10, -0.03, 0.006)
        # The water lilies on the still water at the right, near the bank,
        # the back of a river dolphin far off, and a canoe.
        rims, rim_pen = a.drawing()
        pads, pad_pen = a.drawing()
        blooms, bloom_pen = a.drawing()
        for lu, lv, r, bloom in ((0.78, 0.668, 0.028, True), (0.85, 0.676, 0.034, False), (0.93, 0.664, 0.022, False), (0.72, 0.680, 0.024, False),
                                 (0.99, 0.682, 0.030, True), (0.84, 0.655, 0.016, False), (0.47, 0.672, 0.020, False)):
            _victoria(rim_pen, pad_pen, bloom_pen, lu, lv, r, bloom)
        dolphin, dolphin_pen = a.drawing()
        dolphin_pen.poly([(0.452 + 0.022 * t, water_v + 0.012 - 0.006 * math.sin(math.pi * t)) for t in np.linspace(0.0, 1.0, 12)] + [(0.474, water_v + 0.013), (0.452, water_v + 0.013)])
        canoe, canoe_pen = a.drawing()
        crew, crew_pen = a.drawing()
        _dugout(canoe_pen, crew_pen, 0.53, 0.650, 0.050, -1.0)
        mound_mask = a.mask_of(mounds)
        wall_mask = a.mask_of(walls)
        roof_mask = a.mask_of(roofs)
        door_mask = a.mask_of(doors) * wall_mask
        ptrunk_mask = a.mask_of(palm_trunks)
        pcrown_mask = a.mask_of(palm_crowns)
        rim_mask = a.mask_of(rims)
        pad_mask = a.mask_of(pads)
        bloom_mask = a.mask_of(blooms)
        dolphin_mask = a.mask_of(dolphin)
        boat_mask = np.maximum(a.mask_of(canoe), a.mask_of(crew))
        on_water = np.maximum.reduce([rim_mask, bloom_mask, dolphin_mask, boat_mask])
        things = np.maximum.reduce([forest_mask, trunk_mask, giant_mask, giant_crown_mask, mound_mask, wall_mask, roof_mask, ptrunk_mask, pcrown_mask])
        water = smoothstep(HORIZON + 0.010, HORIZON + 0.016, a.v)
        mask = np.maximum.reduce([things, water, on_water, under])
        layer = solid(a, mask, mix(p["forest"], p["far"], 0.45), p["forest"], 0.50, 0.66, "marajo far", 0.03)
        # The river: pale far off where it shows the misty sky, brown
        # toward the eye, with lines of current and the soft pictures of the
        # forest and the mounds in it.
        a.put(layer, water, a.ramp([(0.0, mix(p["river_light"], p["low"], 0.40)), (HORIZON + 0.016, mix(p["river_light"], p["low"], 0.40)),
                                     (0.65, mix(p["river"], p["river_light"], 0.40)), (0.70, p["river"]), (1.0, p["river_deep"])]))
        stand = np.maximum.reduce([forest_mask, trunk_mask, giant_mask, giant_crown_mask, under])
        a.put(layer, _reflected(a, stand, water_v, "marajo forest ripple", water * (a.v > water_v)), mix(p["forest"], p["river"], 0.50), 0.45)
        houses_mask = np.maximum.reduce([mound_mask, wall_mask, roof_mask, ptrunk_mask, pcrown_mask])
        a.put(layer, _reflected(a, houses_mask, water_v + 0.002, "marajo teso ripple", water * (a.v > water_v + 0.002)), mix(p["mound"], p["river"], 0.45), 0.40)
        lines = smoothstep(0.62, 0.84, a.noise("marajo current", cells=60.0, octaves=2, stretch=16.0))
        a.light(layer, water * lines * smoothstep(water_v + 0.004, water_v + 0.05, a.v), p["river_light"], 0.25)
        glitter = water * a.spot(sun_at[0], 0.66, 0.16, 1.2, squash=0.7) * smoothstep(0.55, 0.78, a.noise("marajo glitter", cells=110.0, octaves=2, stretch=10.0))
        a.light(layer, glitter, p["glow"], 0.40)
        # The flooded forest: dark under its crowns, the trunks pale in the
        # gloom, and the crowns lit at their tops by the low sun.
        a.put(layer, under, mix(p["forest"], p["near"], 0.25))
        a.tint(layer, under * fog(a, "marajo forest mist", water_v - 0.012, 0.014, 4.0), p["low"], 0.35)
        a.put(layer, trunk_mask, mix(p["samauma"], p["forest"], 0.55))
        a.put(layer, forest_mask, mix(p["forest"], p["far"], 0.30))
        lumps = a.noise("marajo crowns", cells=70.0, octaves=3)
        a.light(layer, forest_mask * smoothstep(0.55, 0.75, lumps), mix(p["forest_light"], p["far"], 0.3), 0.40)
        a.light(layer, a.rim(forest_mask, 0.0, 0.003, 0.4) * forest_mask, mix(p["forest_light"], p["glow"], 0.4), 0.45)
        # The samaúma: its pale trunk and walls of roots, lit on the side to
        # the sun, and its wide crown.
        a.put(layer, giant_mask, mix(mix(p["samauma"], p["forest"], 0.25), p["far"], 0.20))
        a.shade(layer, giant_mask * a.rim(giant_mask, -0.002, 0.0, 0.0), 0.30)
        a.shade(layer, giant_mask * smoothstep(0.45, 0.70, a.noise("marajo bark", cells=200.0, octaves=1, stretch=0.1)), 0.10)
        a.put(layer, giant_crown_mask, mix(p["forest"], p["far"], 0.22))
        a.light(layer, giant_crown_mask * smoothstep(0.52, 0.72, a.noise("marajo giant lumps", cells=90.0, octaves=2)), mix(p["forest_light"], p["far"], 0.2), 0.45)
        a.light(layer, a.rim(giant_crown_mask, 0.0, 0.003, 0.3) * giant_crown_mask, p["glow"], 0.45)
        # The mounds: dark earth with grass, the houses with walls of
        # wattle and big roofs of thatch, and the palms.
        a.put(layer, mound_mask, mix(p["mound"], p["far"], 0.25))
        a.put(layer, mound_mask * smoothstep(water_v - 0.004, water_v - 0.014, a.v), mix(p["grass"], p["far"], 0.30))
        a.light(layer, a.rim(mound_mask, 0.0, 0.002, 0.3) * mound_mask, mix(p["mound_light"], p["glow"], 0.4), 0.45)
        a.put(layer, wall_mask, mix(p["wall"], p["far"], 0.20))
        a.put(layer, door_mask, mix(p["door"], p["far"], 0.20))
        a.put(layer, roof_mask, mix(p["thatch"], p["far"], 0.15))
        straw = np.clip(1.0 - np.abs(((a.u * 700.0) % 1.0) - 0.5) / 0.15, 0.0, 1.0)
        a.shade(layer, roof_mask * straw, 0.12)
        a.light(layer, a.rim(roof_mask, 0.002, 0.0, 0.2) * roof_mask, p["glow"], 0.45)
        a.shade(layer, a.rim(roof_mask, -0.002, 0.0, 0.2) * roof_mask, 0.20)
        a.put(layer, ptrunk_mask, mix(p["trunk"], p["far"], 0.30))
        a.put(layer, pcrown_mask, mix(p["forest"], p["far"], 0.25))
        a.light(layer, a.rim(pcrown_mask, 0.0015, 0.0015, 0.0) * pcrown_mask, mix(p["forest_light"], p["far"], 0.3), 0.45)
        a.put(layer, smoke, p["smoke"], 0.55)
        mask = np.maximum(mask, smoke * 0.55)
        # The lilies: the red rim, the green top with fine ribs, and the
        # white flowers flushed with pink.
        a.put(layer, rim_mask, mix(p["lily_rim"], p["far"], 0.15))
        a.put(layer, pad_mask, mix(p["lily"], p["far"], 0.15))
        a.light(layer, a.rim(pad_mask, 0.0, 0.002, 0.0) * pad_mask, p["leaf_light"], 0.40)
        a.put(layer, bloom_mask, p["flower"])
        a.put(layer, bloom_mask * a.rim(bloom_mask, 0.0, -0.003, 0.0), p["dolphin"], 0.60)
        a.put(layer, dolphin_mask, mix(p["dolphin"], p["far"], 0.20))
        a.light(layer, a.rim(dolphin_mask, 0.0, 0.0015, 0.0) * dolphin_mask, p["glow"], 0.50)
        a.put(layer, a.mask_of(canoe), mix(p["canoe"], p["far"], 0.20))
        a.put(layer, a.mask_of(crew), mix(p["near"], p["far"], 0.30))
        a.tint(layer, fog(a, "marajo river mist", water_v - 0.004, 0.012, 3.0) * mask, p["low"], 0.50)
        a.tint(layer, fog(a, "marajo low mist", 0.665, 0.012, 2.5) * water, p["low"], 0.35)
        haze(a, layer, p["low"], 0.08, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near marajo")
        bank, ground, bank_at = _bank(a, "near marajo", 0.034, 0.030)
        stems, stem_pen = a.drawing()
        leaves, leaf_pen = a.drawing()
        bracts, bract_pen = a.drawing()
        tips, tip_pen = a.drawing()
        palm_trunks, palm_trunk_pen = a.drawing()
        fronds, frond_pen = a.drawing()
        grass, grass_pen = a.drawing()
        # A clump of açaí at the far left, heliconias at the left and the
        # right; the middle is a calm bank of short grass.
        _acai(palm_trunk_pen, frond_pen, rng, 0.035, bank_at(0.035) + 0.004, 0.30)
        for u, h in ((0.13, 0.12), (0.20, 0.09)):
            _heliconia(stem_pen, leaf_pen, bract_pen, tip_pen, rng, u, bank_at(u) + 0.004, h)
        for u, h in ((0.84, 0.10), (0.92, 0.14), (0.985, 0.11)):
            _heliconia(stem_pen, leaf_pen, bract_pen, tip_pen, rng, u, bank_at(u) + 0.004, h)
        for _ in range(16):
            u = rng.uniform(0.26, 0.76)
            _grass_blades(grass_pen, rng, u, bank_at(u) + 0.002, rng.uniform(0.010, 0.020), 6, 0.0012, 0.010)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        stem_mask = a.mask_of(stems)
        leaf_mask = a.mask_of(leaves)
        bract_mask = a.mask_of(bracts)
        tip_mask = a.mask_of(tips)
        ptrunk_mask = a.mask_of(palm_trunks)
        frond_mask = a.mask_of(fronds)
        grass_mask = a.mask_of(grass)
        mask = np.maximum.reduce([bank_mask, stem_mask, leaf_mask, bract_mask, tip_mask, ptrunk_mask, frond_mask, grass_mask])
        layer = a.blank()
        # The bank: the very dark earth of the gardens, with grass on it.
        earth = a.ramp([(0.0, mix(p["grass"], p["near"], 0.50)), (0.66, mix(p["grass"], p["near"], 0.50)), (0.76, mix(p["mound"], p["near"], 0.75)), (1.0, p["near"])])
        a.put(layer, bank_mask, earth)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.25)
        a.put(layer, grass_mask, mix(p["grass"], p["near"], 0.40))
        a.light(layer, a.rim(grass_mask, -0.0015, 0.0, 0.2) * grass_mask, p["leaf_light"], 0.25)
        a.put(layer, ptrunk_mask, mix(p["trunk"], p["near"], 0.40))
        a.put(layer, frond_mask, mix(p["leaf"], p["near"], 0.40))
        a.light(layer, a.rim(frond_mask, 0.002, 0.002, 0.0) * frond_mask, p["leaf_light"], 0.35)
        a.put(layer, stem_mask, mix(p["leaf"], p["near"], 0.35))
        a.put(layer, leaf_mask, mix(p["leaf"], p["near"], 0.25))
        a.put(layer, leaf_mask * smoothstep(0.45, 0.72, a.noise("marajo leaf shade", cells=18.0, octaves=2)), mix(p["near"], p["leaf"], 0.3), 0.45)
        a.light(layer, a.rim(leaf_mask, 0.002, 0.002, 0.0) * leaf_mask, p["leaf_light"], 0.45)
        a.put(layer, bract_mask, mix(p["helico"], p["near"], 0.18))
        a.light(layer, a.rim(bract_mask, 0.0, 0.0015, 0.0) * bract_mask, p["glow"], 0.35)
        a.put(layer, tip_mask, mix(p["helico_tip"], p["near"], 0.15))
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.18)
        haze(a, layer, p["low"], 0.10, None)
        return layer
    layer = _air(a, p, "marajo morning mist", p["low"], 0.38, scale(p["near"], 0.8), 0.14)
    a.put(layer, shafts(a, "marajo shafts", 4, 0.12, 0.0, 0.85, 0.05), p["glow"], 0.07)
    return layer


def marajo_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """The tips of palm fronds hang into the top of the view at two places.
    A heliconia with its chain of bracts stands from below at one place."""
    del layer_lights
    rng = art_.rand("marajo foreground")
    for k in range(2):
        u0 = 0.08 + (k + rng.uniform(0.2, 0.8)) * 0.42
        for j in range(2):
            start = (u0 + (j - 0.5) * 0.05, 0.0)
            end = (start[0] + (0.08 if j else -0.08) + rng.uniform(-0.02, 0.02), 0.380 - rng.uniform(0.0, 0.01))
            ctrl = ((start[0] + end[0]) * 0.5 + (0.03 if j else -0.03), 0.20)
            rib = _arch(start, ctrl, end, 20)
            pen.line(rib, 0.0026)
            for i, (x, y) in enumerate(rib[1:], 1):
                side = 0.030 * (1.0 - i / 20.0 * 0.6)
                side = max(0.0, min(side, 0.390 - y))
                pen.line([(x, y), (x + side * 0.25, y + side)], 0.0013)
                pen.line([(x, y), (x - side * 0.25, y + side)], 0.0013)
    u = rng.uniform(0.44, 0.56)
    top = REST_BOTTOM - 0.004
    pen.line(_arch((u, 1.0), (u + 0.004, top + 0.08), (u + 0.010, top), 10), 0.0022)
    y = top
    for i in range(5):
        side = 1.0 if i % 2 == 0 else -1.0
        size = 0.012 - i * 0.001
        pen.poly([(u + 0.010, y), (u + 0.010 + side * size * 1.2, y - size * 0.3), (u + 0.010 + side * size * 1.3, y + size * 0.2), (u + 0.010, y + size * 0.6)])
        y += size * 0.65
    for s in (-1.0, 1.0):
        _leaf(pen, _arch((u, 1.0), (u + s * 0.02, top + 0.06), (u + s * 0.05, top + 0.012), 10), 0.009, 0.7)


# ---------------------------------------------------------------------------
# Palmares: Serra da Barriga, about 1680
# ---------------------------------------------------------------------------


PALMARES = {
    "top": (96, 138, 170),
    "mid": (208, 202, 176),
    "low": (246, 226, 180),
    "glow": (255, 214, 150),
    "sun": (255, 242, 210),
    "cloud": (250, 240, 222),
    "cloud_shadow": (196, 178, 166),
    "plain": (124, 160, 82),
    "plain_light": (176, 194, 108),
    "cane": (112, 156, 64),
    "river": (150, 176, 180),
    "hill": (56, 94, 56),
    "hill_light": (128, 158, 84),
    "palm": (44, 78, 44),
    "palm_light": (128, 160, 82),
    "trunk": (122, 102, 78),
    "earth": (166, 84, 50),
    "earth_light": (208, 126, 80),
    "thatch": (182, 150, 94),
    "wall": (160, 112, 74),
    "door": (50, 34, 26),
    "log": (114, 86, 60),
    "log_light": (172, 136, 94),
    "maize": (170, 168, 80),
    "tassel": (226, 204, 120),
    "manioc": (78, 124, 62),
    "smoke": (168, 160, 156),
    "banana": (96, 140, 64),
    "banana_light": (182, 204, 110),
    "banana_dark": (52, 84, 42),
    "far": (208, 202, 176),
    "near": (44, 30, 22),
    "near_light": (158, 86, 52),
}


def _stakes(pen: Pen, u0: float, u1: float, foot, h: float, w: float) -> None:
    """A palisade: a row of logs side by side, each cut to a point. `foot`
    gives the `v` of the ground at `u`."""
    u = u0
    k = 0
    while u < u1:
        v = foot(u)
        hh = h * (1.0 + 0.10 * math.sin(k * 2.3))
        pen.poly([(u - w * 0.5, v + 0.002), (u - w * 0.5, v - hh), (u, v - hh - w * 0.9), (u + w * 0.5, v - hh), (u + w * 0.5, v + 0.002)])
        u += w * 1.02
        k += 1


def history_palmares(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = PALMARES
    sun_at = (0.84, 0.36)
    plain_v = HORIZON - 0.002
    if layer_key == "sky":
        # A clear afternoon: heap clouds, a sun at the right, and far below
        # the flat green plain of sugar cane that goes to the horizon, with
        # blue hills on its far edge and a river that winds over it.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.90)), (0.22, p["top"]), (0.44, p["mid"]), (plain_v, p["low"]),
                                 (plain_v + 0.004, mix(p["plain"], p["low"], 0.55)), (0.70, mix(p["plain"], p["low"], 0.25)), (1.0, p["plain"])]))
        _sun(a, layer, *sun_at, 0.024, p["sun"], p["glow"], 0.65)
        _heaps(a, layer, "palmares heaps", ((0.20, 0.30, 0.08, 0.07), (0.46, 0.25, 0.10, 0.08), (0.66, 0.33, 0.06, 0.05)), p["cloud"], p["cloud_shadow"], 0.80)
        hills, _ = a.ridge("palmares far hills", plain_v - 0.010, 0.008, cells=5.0, octaves=4)
        a.put(layer, hills * smoothstep(plain_v + 0.004, plain_v, a.v), mix(p["top"], p["low"], 0.55))
        # The plain: a patchwork of fields of cane, a little lighter and
        # darker, smaller and paler as they go back.
        below = smoothstep(plain_v + 0.002, plain_v + 0.005, a.v)
        patches = a.noise("palmares plain fields", cells=70.0, octaves=1, stretch=12.0)
        a.light(layer, below * smoothstep(0.55, 0.65, patches), mix(p["plain_light"], p["low"], 0.2), 0.40)
        a.shade(layer, below * smoothstep(0.40, 0.30, patches), 0.10)
        river = a.drawing()
        pts = [(u, plain_v + 0.012 + (u - 0.0) * 0.05 + 0.006 * math.sin(u * 23.0)) for u in np.linspace(-0.02, 0.62, 40)]
        river[1].line(pts, 0.0025)
        a.put(layer, a.mask_of(river[0]) * below, mix(p["river"], p["low"], 0.3), 0.8)
        a.tint(layer, fog(a, "palmares plain haze", plain_v + 0.004, 0.020, 3.0), p["low"], 0.55)
        a.tint(layer, below * smoothstep(0.75, plain_v, a.v), p["low"], 0.25)
        _textbook(a, layer, 0.08)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far palmares")
        # The hill: it rises from the plain at the left to a long round
        # crest at the right.
        _, crest = a.ridge("palmares crest", 0.505, 0.010, cells=4.0, octaves=4)
        rise = smoothstep(0.16, 0.50, a.u[0])
        top = (HORIZON + 0.030) + (crest - (HORIZON + 0.030)) * rise
        hill = _land(a, top)
        terrace = lambda u: _at(top, u) + 0.050 + 0.004 * math.sin(u * 9.0)  # noqa: E731
        forest, forest_pen = a.drawing()
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        stakes, stake_pen = a.drawing()
        walls, wall_pen = a.drawing()
        roofs, roof_pen = a.drawing()
        doors, door_pen = a.drawing()
        maize, maize_pen = a.drawing()
        manioc, manioc_pen = a.drawing()
        # Forest on the crest and on the slopes.
        _canopy(forest_pen, rng, top, 0.20, 1.02, 0.006, 0.008, 0.016, 200)
        # Groves of palms on the slopes, and over the crest.
        for _ in range(40):
            u = rng.uniform(0.18, 1.0)
            if 0.40 < u < 0.97 and rng.random() < 0.6:
                continue
            v = _at(top, u) + rng.uniform(0.002, 0.030 if u < 0.40 else 0.008)
            _palm(trunk_pen, crown_pen, rng, u, v, rng.uniform(0.030, 0.050), rng.uniform(-0.25, 0.25))
        # The palisade on its terrace, with a gate in it; the village of
        # mocambos behind it, up the slope; the fields in front of it.
        _stakes(stake_pen, 0.36, 0.975, lambda u: terrace(u) if abs(u - 0.62) > 0.014 else 9.0, 0.020, 0.0034)
        stake_pen.rect(0.606 - 0.002, terrace(0.606) - 0.030, 0.606 + 0.002, terrace(0.606) + 0.002)
        stake_pen.rect(0.634 - 0.002, terrace(0.634) - 0.030, 0.634 + 0.002, terrace(0.634) + 0.002)
        stake_pen.rect(0.604, terrace(0.62) - 0.032, 0.636, terrace(0.62) - 0.027)
        for hu, dv, hw in ((0.42, 0.026, 0.014), (0.47, 0.034, 0.012), (0.53, 0.024, 0.016), (0.585, 0.036, 0.012), (0.66, 0.028, 0.015),
                           (0.72, 0.036, 0.012), (0.77, 0.024, 0.016), (0.83, 0.032, 0.013), (0.89, 0.026, 0.015), (0.94, 0.034, 0.012)):
            foot = terrace(hu) - dv * 0.35
            _thatch_house(wall_pen, roof_pen, door_pen, hu, foot, hw, hw * 0.55, 1.2)
        plots, plot_pen = a.drawing()
        x = 0.37
        while x < 0.99:
            length = rng.uniform(0.06, 0.12)
            x1 = min(x + length, 1.02)
            depth = rng.uniform(0.020, 0.032)
            top_pts = [(t, terrace(t) + 0.005) for t in np.linspace(x, x1, 8)]
            low_pts = [(t, terrace(t) + 0.005 + depth) for t in np.linspace(x1 - 0.008, x + 0.008, 8)]
            plot_pen.poly(top_pts + low_pts)
            crop = maize_pen if rng.random() < 0.5 else None
            for _ in range(int(length * 260)):
                u = rng.uniform(x + 0.006, x1 - 0.006)
                v = terrace(u) + 0.006 + rng.uniform(0.002, depth - 0.002)
                if crop is not None:
                    crop.line([(u, v), (u + rng.uniform(-0.001, 0.001), v - 0.009)], 0.0015)
                else:
                    manioc_pen.ellipse(u, v - 0.002, 0.0035, 0.0026)
            x = x1 + rng.uniform(0.010, 0.025)
        # A few bushes and young palms on the lower slope.
        for _ in range(26):
            u = rng.uniform(0.26, 1.0)
            v = terrace(u) + rng.uniform(0.045, 0.10)
            if v < _at(top, u) + 0.004:
                continue
            if rng.random() < 0.3:
                _palm(trunk_pen, crown_pen, rng, u, v, rng.uniform(0.020, 0.030), rng.uniform(-0.2, 0.2))
            else:
                _lumpy_crown(forest_pen, rng, u, v - 0.006, rng.uniform(0.008, 0.014), rng.uniform(0.005, 0.008), 12)
        gate, gate_pen = a.drawing()
        gate_pen.rect(0.608, terrace(0.62) - 0.026, 0.632, terrace(0.62) + 0.002)
        smoke = np.maximum(_plume(a, "palmares forge smoke", 0.70, terrace(0.70) - 0.020, 0.14, -0.04, 0.010),
                           _plume(a, "palmares hearth smoke", 0.47, terrace(0.47) - 0.022, 0.09, -0.03, 0.005) * 0.6)
        forest_mask = a.mask_of(forest) * smoothstep(0.16, 0.22, a.u)
        land = np.maximum(hill, forest_mask)
        stake_mask = a.mask_of(stakes)
        wall_mask = a.mask_of(walls)
        roof_mask = a.mask_of(roofs)
        door_mask = a.mask_of(doors) * wall_mask
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        field_band = a.mask_of(plots) * hill
        gate_mask = a.mask_of(gate)
        maize_mask = a.mask_of(maize) * field_band
        manioc_mask = a.mask_of(manioc) * field_band
        building = np.maximum.reduce([stake_mask, wall_mask, roof_mask])
        mask = np.maximum.reduce([land, building, trunk_mask, crown_mask])
        layer = solid(a, mask, mix(p["hill"], p["far"], 0.30), mix(p["hill"], p["near"], 0.10), 0.50, 0.70, "palmares far", 0.05)
        # The slopes: forest lit on the side to the sun, and the red earth
        # that shows where the ground is cleared.
        a.light(layer, forest_mask * smoothstep(0.42, 0.72, a.noise("palmares forest", cells=40.0, octaves=3)), p["hill_light"], 0.35)
        a.light(layer, a.rim(forest_mask, -0.003, 0.003, 0.5) * forest_mask, p["glow"], 0.40)
        a.put(layer, field_band, mix(p["earth"], p["far"], 0.40))
        rows = np.clip(1.0 - np.abs(((a.v * 520.0) % 1.0) - 0.5) / 0.20, 0.0, 1.0)
        a.put(layer, field_band * rows, mix(p["manioc"], p["far"], 0.35), 0.45)
        a.light(layer, a.rim(field_band, 0.0, 0.002, 0.3) * field_band, p["glow"], 0.25)
        a.put(layer, manioc_mask, mix(p["manioc"], p["far"], 0.20))
        a.put(layer, maize_mask, mix(p["maize"], p["far"], 0.15))
        a.put(layer, maize_mask * a.rim(maize_mask, 0.0, 0.002, 0.0), p["tassel"], 0.8)
        # The palisade: grey-brown logs, lit on the side to the sun.
        a.put(layer, stake_mask, mix(p["log"], p["far"], 0.15))
        a.light(layer, stake_mask * (np.abs(((a.u * 300.0) % 1.0) - 0.75) < 0.18), p["log_light"], 0.45)
        a.shade(layer, stake_mask * smoothstep(0.4, 0.8, a.noise("palmares logs", cells=200.0, octaves=1, stretch=0.1)), 0.15)
        a.put(layer, gate_mask, mix(p["door"], p["log"], 0.45))
        a.put(layer, gate_mask * (np.abs(((a.u * 300.0) % 1.0) - 0.5) < 0.12), mix(p["log"], p["far"], 0.15))
        # The mocambos: walls of daub, dark doors, roofs of palm thatch.
        a.put(layer, wall_mask, mix(p["wall"], p["far"], 0.15))
        a.put(layer, door_mask, mix(p["door"], p["far"], 0.15))
        a.put(layer, roof_mask, mix(p["thatch"], p["far"], 0.12))
        straw = np.clip(1.0 - np.abs(((a.u * 700.0) % 1.0) - 0.5) / 0.15, 0.0, 1.0)
        a.shade(layer, roof_mask * straw, 0.12)
        a.light(layer, a.rim(roof_mask, -0.002, 0.0, 0.2) * roof_mask, p["glow"], 0.45)
        a.shade(layer, a.rim(roof_mask, 0.002, 0.0, 0.2) * roof_mask, 0.20)
        # The palms.
        a.put(layer, trunk_mask, mix(p["trunk"], p["far"], 0.25))
        a.put(layer, crown_mask, mix(p["palm"], p["far"], 0.20))
        a.light(layer, a.rim(crown_mask, -0.0015, 0.0015, 0.0) * crown_mask, mix(p["palm_light"], p["far"], 0.2), 0.50)
        a.put(layer, smoke, p["smoke"], 0.70)
        mask = np.maximum(mask, smoke * 0.70)
        a.tint(layer, smoothstep(0.42, 0.66, a.v) * land * smoothstep(0.30, 0.0, a.u), p["low"], 0.35)
        haze(a, layer, p["low"], 0.06, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near palmares")
        bank, ground, bank_at = _bank(a, "near palmares", 0.040, 0.036)
        stems, stem_pen = a.drawing()
        leaves, leaf_pen = a.drawing()
        ribs, rib_pen = a.drawing()
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        grass, grass_pen = a.drawing()
        # Banana plants at the left; a palm and its fronds at the right; the
        # middle is a calm bank of red earth and short grass.
        for u, h, lean in ((0.04, 0.28, 0.02), (0.13, 0.20, -0.04), (0.205, 0.13, 0.03)):
            _banana(stem_pen, leaf_pen, rib_pen, rng, u, bank_at(u) + 0.004, h, lean)
        _palm(trunk_pen, crown_pen, rng, 0.93, bank_at(0.93) + 0.004, 0.34, -0.12)
        _palm(trunk_pen, crown_pen, rng, 0.83, bank_at(0.83) + 0.004, 0.20, 0.10)
        for _ in range(160):
            u = rng.uniform(0.0, 1.0)
            h = rng.uniform(0.006, 0.014) * (1.0 + 0.8 * (abs(u - 0.5) > 0.3))
            v = bank_at(u) + 0.002
            grass_pen.line([(u, v), (u + rng.uniform(-0.004, 0.004), v - h)], 0.0013)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        stem_mask = a.mask_of(stems)
        leaf_mask = a.mask_of(leaves)
        rib_mask = a.mask_of(ribs) * leaf_mask
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        grass_mask = a.mask_of(grass)
        mask = np.maximum.reduce([bank_mask, stem_mask, leaf_mask, trunk_mask, crown_mask, grass_mask])
        layer = a.blank()
        earth = a.ramp([(0.0, mix(p["near_light"], p["near"], 0.25)), (0.64, mix(p["near_light"], p["near"], 0.25)), (0.80, mix(p["near_light"], p["near"], 0.70)), (1.0, p["near"])])
        a.put(layer, bank_mask, earth)
        beds = np.clip(1.0 - np.abs(((a.v * 90.0 + 0.8 * np.sin(a.u * 11.0)) % 1.0) - 0.5) / 0.12, 0.0, 1.0)
        a.shade(layer, bank_mask * beds * a.noise("palmares beds", cells=8.0, octaves=2), 0.25)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.35)
        a.put(layer, grass_mask, mix(p["hill_light"], p["near"], 0.50))
        a.put(layer, trunk_mask, mix(p["trunk"], p["near"], 0.45))
        a.put(layer, crown_mask, mix(p["palm"], p["near"], 0.30))
        a.light(layer, a.rim(crown_mask, -0.002, 0.002, 0.0) * crown_mask, p["palm_light"], 0.40)
        a.put(layer, stem_mask, mix(p["banana_light"], p["near"], 0.40))
        a.put(layer, leaf_mask, mix(p["banana"], p["near"], 0.28))
        a.put(layer, leaf_mask * smoothstep(0.45, 0.72, a.noise("palmares leaf shade", cells=18.0, octaves=2)), mix(p["banana_dark"], p["near"], 0.25), 0.55)
        a.light(layer, a.rim(leaf_mask, -0.002, 0.002, 0.0) * leaf_mask, p["banana_light"], 0.45)
        a.put(layer, rib_mask, mix(p["banana_light"], p["near"], 0.25), 0.7)
        a.shade(layer, a.rim(mask, 0.004, -0.003, 1.0) * mask, 0.18)
        haze(a, layer, p["low"], 0.08, None)
        return layer
    layer = _air(a, p, "palmares warm haze", p["low"], 0.26, p["near"], 0.20)
    a.put(layer, shafts(a, "palmares shafts", 4, -0.18, 0.0, 0.85, 0.05), p["glow"], 0.08)
    return layer


def palmares_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """The tips of palm fronds hang into the top of the view at two places.
    A stalk of maize with its long leaves stands from below at one place."""
    del layer_lights
    rng = art_.rand("palmares foreground")
    for k in range(2):
        u0 = 0.10 + (k + rng.uniform(0.2, 0.8)) * 0.40
        for j in range(3):
            start = (u0 + (j - 1) * 0.04, 0.0)
            end = (start[0] + (j - 1) * 0.07 + rng.uniform(-0.02, 0.02), 0.378 - rng.uniform(0.0, 0.012))
            ctrl = ((start[0] + end[0]) * 0.5 + (j - 1) * 0.03, 0.18)
            rib = _arch(start, ctrl, end, 20)
            pen.line(rib, 0.0024)
            for i, (x, y) in enumerate(rib[1:], 1):
                side = 0.034 * (1.0 - i / 20.0 * 0.6)
                side = max(0.0, min(side, 0.390 - y))
                pen.line([(x, y), (x + side * 0.30, y + side)], 0.0012)
                pen.line([(x, y), (x - side * 0.30, y + side)], 0.0012)
    u = rng.uniform(0.44, 0.56)
    top = REST_BOTTOM - 0.006
    pen.line([(u, 1.0), (u + 0.002, top)], 0.0030)
    for k in range(5):
        y = top + 0.010 + k * 0.016
        side = 1.0 if k % 2 else -1.0
        _leaf(pen, _arch((u, y + 0.010), (u + side * 0.020, y - 0.010), (u + side * 0.050, y + 0.008), 10), 0.0045, 0.5)
    pen.ellipse(u + 0.004, top + 0.040, 0.0040, 0.012)


# ---------------------------------------------------------------------------
# Rio de Janeiro, May 1888
# ---------------------------------------------------------------------------


RIO = {
    "top": (86, 140, 192),
    "mid": (186, 206, 216),
    "low": (240, 230, 206),
    "glow": (255, 230, 176),
    "sun": (255, 246, 222),
    "cloud": (252, 248, 238),
    "cloud_shadow": (186, 190, 198),
    "bay": (72, 128, 150),
    "bay_light": (204, 224, 222),
    "granite": (134, 128, 122),
    "granite_light": (206, 194, 174),
    "forest": (60, 100, 66),
    "forest_light": (136, 164, 96),
    "yellow": (232, 196, 112),
    "pink": (224, 166, 152),
    "blue": (138, 176, 200),
    "white": (240, 234, 220),
    "tile": (96, 136, 196),
    "roof": (178, 94, 62),
    "hole": (60, 50, 50),
    "iron": (46, 44, 48),
    "flag_green": (36, 128, 68),
    "flag_yellow": (248, 206, 48),
    "palm": (52, 92, 54),
    "palm_light": (132, 168, 88),
    "trunk": (200, 190, 170),
    "crowd": (70, 58, 54),
    "hull": (44, 44, 48),
    "smoke": (176, 172, 172),
    "bloom": (206, 62, 120),
    "bloom_light": (240, 140, 180),
    "far": (198, 206, 204),
    "near": (34, 40, 34),
    "near_light": (130, 140, 100),
}

#: The quay where the city meets the bay.
RIO_QUAY = 0.636


def _sobrado(pens: dict, colour: str, u: float, v: float, w: float, h: float, floors: int, tiled: bool, flag: bool) -> None:
    """A town house of old Rio (a sobrado): a narrow front of two or three
    floors under a low red roof with eaves, tall windows in rows, a
    balcony of iron on each upper window, and doors on the street. A front
    may be faced with blue and white tiles. `pens` holds a pen for each
    paint; `colour` is the key of the paint of the front."""
    pens["tile" if tiled else colour].rect(u - w, v - h, u + w, v + 0.001)
    pens["white"].rect(u - w * 1.04, v - h - h * 0.05, u + w * 1.04, v - h + h * 0.02)
    pens["roof"].poly([(u - w * 1.10, v - h - h * 0.04), (u - w * 0.80, v - h - h * 0.24), (u + w * 0.80, v - h - h * 0.24), (u + w * 1.10, v - h - h * 0.04)])
    cols = max(2, int(round(w / (h / floors) * 1.6)))
    for f in range(floors):
        y1 = v - h * f / floors - h * 0.06
        y0 = y1 - h / floors * 0.62
        for c in range(cols):
            x = u - w + (c + 0.5) * 2.0 * w / cols
            pens["hole"].rect(x - w / cols * 0.36, y0, x + w / cols * 0.36, y1)
            pens["white"].rect(x - w / cols * 0.46, y0 - h * 0.025, x + w / cols * 0.46, y0)
            if f > 0:
                pens["iron"].rect(x - w / cols * 0.50, y1 - h * 0.07, x + w / cols * 0.50, y1)
        if f > 0 and flag:
            x = u - w + w / cols
            pens["iron"].line([(x, y1), (x - w * 0.35, y1 - h * 0.28)], w * 0.03)
            fx, fy = x - w * 0.35, y1 - h * 0.28
            pens["flag_green"].poly([(fx, fy), (fx - w * 0.55, fy + h * 0.02), (fx - w * 0.52, fy + h * 0.20), (fx, fy + h * 0.17)])
            cx, cy = fx - w * 0.27, fy + h * 0.10
            pens["flag_yellow"].poly([(cx - w * 0.18, cy), (cx, cy - h * 0.055), (cx + w * 0.18, cy), (cx, cy + h * 0.055)])
            flag = False


def _bunting(green: Pen, yellow: Pen, a: tuple[float, float], b: tuple[float, float], sag: float, size: float) -> None:
    """A line of small pennants that hangs between two points, green and
    yellow in turn."""
    pts = _arch(a, ((a[0] + b[0]) * 0.5, max(a[1], b[1]) + sag), b, 24)
    green.line(pts, size * 0.12)
    for i in range(1, len(pts) - 1, 1):
        x, y = pts[i]
        pen = green if i % 2 else yellow
        pen.poly([(x - size * 0.4, y), (x + size * 0.4, y), (x, y + size)])


def _ferry(hull: Pen, house: Pen, dark: Pen, u: float, v: float, s: float) -> None:
    """A steam ferry of the bay: a long low dark hull, a white deckhouse with
    a row of windows, a big round paddle box at its middle, and a tall thin
    funnel. `(u, v)` is the middle of its waterline and `s` its length."""
    hull.poly([(u - s * 0.5, v - s * 0.06), (u + s * 0.46, v - s * 0.06), (u + s * 0.52, v - s * 0.10), (u + s * 0.44, v + s * 0.01), (u - s * 0.46, v + s * 0.01)])
    house.rect(u - s * 0.40, v - s * 0.15, u + s * 0.34, v - s * 0.06)
    house.rect(u - s * 0.30, v - s * 0.20, u + s * 0.20, v - s * 0.15)
    house.ellipse(u - s * 0.02, v - s * 0.08, s * 0.10, s * 0.09)
    for k in range(9):
        x = u - s * 0.36 + k * s * 0.08
        if abs(x - u + s * 0.02) > s * 0.10:
            dark.rect(x - s * 0.012, v - s * 0.13, x + s * 0.012, v - s * 0.10)
    dark.rect(u + s * 0.04, v - s * 0.44, u + s * 0.08, v - s * 0.18)
    dark.line([(u - s * 0.46, v - s * 0.06), (u - s * 0.46, v - s * 0.34)], s * 0.012)
    dark.line([(u + s * 0.42, v - s * 0.06), (u + s * 0.42, v - s * 0.30)], s * 0.012)


def _tower(pen: Pen, holes: Pen, u: float, v: float, w: float, h: float) -> None:
    """A plain tower far off: a square shaft, a belfry with one opening on
    each face, and a low pointed cap. No sign is on it."""
    pen.rect(u - w, v - h, u + w, v + 0.001)
    pen.rect(u - w * 1.15, v - h - w * 0.2, u + w * 1.15, v - h + w * 0.15)
    pen.poly([(u - w * 1.05, v - h - w * 0.2), (u, v - h - w * 2.0), (u + w * 1.05, v - h - w * 0.2)])
    holes.rect(u - w * 0.35, v - h * 0.86, u + w * 0.35, v - h * 0.70)


def history_rio_1888(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = RIO
    sun_at = (0.18, 0.34)
    bay_v = HORIZON - 0.002
    quay = RIO_QUAY
    if layer_key == "sky":
        # A bright morning: a clear blue sky with a few small white clouds,
        # the blue bay under it, and across the bay the Sugarloaf and the
        # Morro da Urca, steep domes of bare granite with forest at their
        # feet; the far hills of the other shore at the left.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.88)), (0.24, p["top"]), (0.48, p["mid"]), (bay_v, p["low"]),
                                 (bay_v + 0.003, mix(p["bay"], p["low"], 0.45)), (0.70, p["bay"]), (1.0, scale(p["bay"], 0.92))]))
        _sun(a, layer, *sun_at, 0.022, p["sun"], p["glow"], 0.55)
        _heaps(a, layer, "rio heaps", ((0.42, 0.29, 0.06, 0.05), (0.62, 0.24, 0.05, 0.04), (0.95, 0.31, 0.07, 0.05)), p["cloud"], p["cloud_shadow"], 0.75)
        hills, _ = a.ridge("rio far shore", bay_v - 0.016, 0.012, cells=5.0, octaves=4, sharp=0.4)
        a.put(layer, hills * smoothstep(bay_v + 0.003, bay_v, a.v) * smoothstep(0.66, 0.50, a.u), mix(p["forest"], p["low"], 0.62))
        # The Sugarloaf and Urca.
        rocks, rock_pen = a.drawing()
        su, sv, sh, sw = 0.84, bay_v + 0.004, 0.13, 0.055
        dome = []
        for x in np.linspace(-1.0, 1.0, 41):
            height = max(0.0, 1.0 - abs(x) ** 1.8) ** 0.55
            dome.append((su + x * sw * (1.0 if x < 0 else 0.75) + 0.006 * height, sv - sh * height))
        rock_pen.poly(dome)
        rock_pen.poly([(0.70 + 0.11 * t, sv - 0.050 * max(0.0, 1.0 - abs(t * 2.0 - 1.0) ** 2.0) ** 0.6) for t in np.linspace(0.0, 1.0, 30)])
        rock_mask = a.mask_of(rocks)
        a.put(layer, rock_mask, mix(p["granite"], p["low"], 0.40))
        a.light(layer, a.rim(rock_mask, 0.006, 0.0, 1.5) * rock_mask, mix(p["granite_light"], p["glow"], 0.3), 0.55)
        streaks = smoothstep(0.55, 0.75, a.noise("rio rock streaks", cells=40.0, octaves=2, stretch=0.15))
        a.shade(layer, rock_mask * streaks, 0.10)
        a.put(layer, rock_mask * smoothstep(sv - 0.050, sv - 0.010, a.v) * smoothstep(0.5, 0.65, a.noise("rio rock forest", cells=60.0, octaves=2)), mix(p["forest"], p["low"], 0.45))
        a.put(layer, rock_mask * smoothstep(sv - 0.020, sv - 0.004, a.v), mix(p["forest"], p["low"], 0.45))
        a.tint(layer, fog(a, "rio bay haze", bay_v - 0.004, 0.012, 3.0), p["low"], 0.40)
        glints = smoothstep(0.62, 0.82, a.noise("rio glints", cells=90.0, octaves=2, stretch=9.0))
        a.light(layer, (a.v > bay_v + 0.003) * glints * a.spot(sun_at[0], HORIZON + 0.03, 0.30, 1.0, squash=0.9), p["bay_light"], 0.55)
        _textbook(a, layer, 0.07)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far rio")
        # The hills behind the old city, with forest and a few houses; two
        # plain towers far off on the hill.
        _, hill_line = a.ridge("rio city hill", 0.555, 0.014, cells=4.0, octaves=4)
        hill_line = hill_line + 0.08 * smoothstep(0.50, 0.66, a.u[0])
        hill = _land(a, hill_line) * (a.v < quay)
        forest, forest_pen = a.drawing()
        _canopy(forest_pen, rng, hill_line, -0.02, 0.62, 0.004, 0.006, 0.012, 160)
        towers, tower_pen = a.drawing()
        tower_holes, tower_hole_pen = a.drawing()
        for tu in (0.235, 0.262):
            _tower(tower_pen, tower_hole_pen, tu, _at(hill_line, 0.25) + 0.016, 0.006, 0.036)
        tower_pen.rect(0.235, _at(hill_line, 0.25) - 0.006, 0.262, _at(hill_line, 0.25) + 0.016)
        pens = {key: a.drawing() for key in ("yellow", "pink", "blue", "white", "tile", "roof", "hole", "iron", "flag_green", "flag_yellow")}
        pen_of = {key: pen for key, (_, pen) in pens.items()}
        # Two rows of houses: a far row up the slope, and the row on the quay.
        x = -0.02
        k = 0
        colours = ("yellow", "pink", "blue", "white", "yellow", "pink", "white", "blue")
        while x < 0.60:
            w = rng.uniform(0.016, 0.024)
            h = rng.uniform(0.030, 0.040)
            _sobrado(pen_of, colours[k % len(colours)], x + w, quay - 0.034, w * 0.9, h * 0.8, 2, k % 5 == 2, False)
            x += w * 2.0
            k += 1
        x = -0.01
        k = 3
        tops = []
        while x < 0.56:
            w = rng.uniform(0.020, 0.030)
            floors = 3 if rng.random() < 0.5 else 2
            h = 0.016 * floors + rng.uniform(0.0, 0.006)
            _sobrado(pen_of, colours[k % len(colours)], x + w, quay, w, h, floors, k % 4 == 1, k % 3 == 0)
            tops.append((x + w, quay - h))
            x += w * 2.0 + 0.002
            k += 1
        green, green_pen = a.drawing()
        yellow, yellow_pen = a.drawing()
        for (u0, v0), (u1, v1) in zip(tops[:-1], tops[1:]):
            _bunting(green_pen, yellow_pen, (u0 + 0.004, v0 + 0.010), (u1 - 0.004, v1 + 0.010), 0.008, 0.004)
        # The quay: a stone wall at the water, a row of royal palms along
        # it, and the crowd, small, on the street under the palms.
        quay_mask = smoothstep(quay - 0.002, quay, a.v) * smoothstep(quay + 0.010, quay + 0.008, a.v) * smoothstep(0.64, 0.60, a.u)
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        for pu in np.arange(0.03, 0.62, 0.065):
            _royal_palm(trunk_pen, crown_pen, rng, pu + rng.uniform(-0.006, 0.006), quay + 0.004, rng.uniform(0.070, 0.085), rng.uniform(-0.004, 0.004))
        crowd, crowd_pen = a.drawing()
        dress, dress_pen = a.drawing()
        for _ in range(140):
            cu = rng.uniform(0.0, 0.60)
            cv = quay + rng.uniform(0.002, 0.007)
            s = 0.0042
            (dress_pen if rng.random() < 0.35 else crowd_pen).ellipse(cu, cv - s * 0.9, s * 0.45, s * 0.9)
            crowd_pen.ellipse(cu, cv - s * 2.0, s * 0.32)
            if rng.random() < 0.10:
                (green_pen if rng.random() < 0.5 else yellow_pen).rect(cu, cv - s * 4.2, cu + s * 1.2, cv - s * 3.4)
                crowd_pen.line([(cu, cv - s * 2.0), (cu, cv - s * 4.2)], s * 0.12)
        # The bay: the ferry, and small boats with sails.
        ferry_hull, ferry_hull_pen = a.drawing()
        ferry_house, ferry_house_pen = a.drawing()
        ferry_dark, ferry_dark_pen = a.drawing()
        _ferry(ferry_hull_pen, ferry_house_pen, ferry_dark_pen, 0.80, 0.652, 0.10)
        smoke = _plume(a, "rio ferry smoke", 0.806, 0.652 - 0.044, 0.08, -0.06, 0.004)
        sails, sail_pen = a.drawing()
        for bu, bv, s in ((0.68, 0.622, 0.020), (0.93, 0.628, 0.026), (0.62, 0.676, 0.030)):
            ferry_hull_pen.poly([(bu - s * 0.5, bv), (bu + s * 0.5, bv), (bu + s * 0.4, bv + s * 0.12), (bu - s * 0.4, bv + s * 0.12)])
            sail_pen.poly([(bu - s * 0.05, bv - 0.002), (bu - s * 0.05, bv - s * 1.1), (bu + s * 0.45, bv - 0.002)])
        hill_mask = np.maximum(hill, a.mask_of(forest) * (a.v < quay))
        house_masks = {key: a.mask_of(img) for key, (img, _) in pens.items()}
        house = np.maximum.reduce(list(house_masks.values()))
        tower_mask = a.mask_of(towers)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        people = np.maximum(a.mask_of(crowd), a.mask_of(dress))
        boats = np.maximum.reduce([a.mask_of(ferry_hull), a.mask_of(ferry_house), a.mask_of(ferry_dark), a.mask_of(sails)])
        flags = np.maximum(a.mask_of(green), a.mask_of(yellow))
        water = smoothstep(HORIZON + 0.010, HORIZON + 0.016, a.v)
        city = np.maximum.reduce([hill_mask, house, tower_mask, quay_mask])
        mask = np.maximum.reduce([city, trunk_mask, crown_mask, people, boats, flags, water])
        layer = solid(a, mask, mix(p["forest"], p["far"], 0.35), mix(p["forest"], p["far"], 0.15), 0.52, 0.64, "rio far", 0.04)
        # The water of the bay, near the city: blue, with the pictures of
        # the houses in it and the light of the sun on it.
        a.put(layer, water, a.ramp([(0.0, mix(p["bay"], p["low"], 0.40)), (HORIZON + 0.016, mix(p["bay"], p["low"], 0.40)), (0.66, mix(p["bay"], p["bay_light"], 0.15)),
                                     (1.0, scale(p["bay"], 0.85))]))
        a.put(layer, _reflected(a, np.maximum(house, crown_mask), quay + 0.008, "rio city ripple", water * (a.v > quay + 0.008)), mix(p["yellow"], p["bay"], 0.55), 0.35)
        lines = smoothstep(0.62, 0.84, a.noise("rio swell", cells=70.0, octaves=2, stretch=14.0))
        a.light(layer, water * lines * smoothstep(quay, quay + 0.05, a.v), p["bay_light"], 0.25)
        # The hill: forest lit on its top, the plain towers.
        a.light(layer, hill_mask * smoothstep(0.45, 0.72, a.noise("rio hill forest", cells=50.0, octaves=3)), mix(p["forest_light"], p["far"], 0.3), 0.40)
        a.light(layer, a.rim(hill_mask, 0.002, 0.003, 0.5) * hill_mask, p["glow"], 0.35)
        a.put(layer, tower_mask, mix(p["white"], p["far"], 0.25))
        a.put(layer, a.mask_of(tower_holes) * tower_mask, mix(p["hole"], p["far"], 0.35))
        a.light(layer, a.rim(tower_mask, 0.0015, 0.0, 0.0) * tower_mask, p["glow"], 0.45)
        # The houses: painted fronts and tiled ones, white trims, red roofs,
        # dark windows and the iron of the balconies, and the flags.
        for key in ("yellow", "pink", "blue", "white"):
            a.put(layer, house_masks[key], mix(p[key], p["far"], 0.15))
        tiles = house_masks["tile"]
        a.put(layer, tiles, mix(p["white"], p["far"], 0.15))
        checks = ((np.floor(a.u * 900.0) + np.floor(a.v * 900.0)) % 2 == 0).astype(np.float32)
        a.put(layer, tiles * checks, mix(p["tile"], p["far"], 0.15), 0.85)
        a.put(layer, house_masks["roof"], mix(p["roof"], p["far"], 0.15))
        a.put(layer, house_masks["hole"], mix(p["hole"], p["far"], 0.38))
        a.put(layer, house_masks["iron"], mix(p["iron"], p["far"], 0.15))
        a.light(layer, a.rim(house, 0.0015, 0.0, 0.0) * house, p["glow"], 0.40)
        a.shade(layer, a.rim(house, -0.0015, 0.0, 0.0) * house, 0.20)
        a.put(layer, house_masks["flag_green"], p["flag_green"])
        a.put(layer, house_masks["flag_yellow"], p["flag_yellow"])
        a.put(layer, a.mask_of(green), p["flag_green"])
        a.put(layer, a.mask_of(yellow), p["flag_yellow"])
        a.put(layer, quay_mask, mix(p["granite_light"], p["far"], 0.20))
        a.shade(layer, quay_mask * smoothstep(quay + 0.003, quay + 0.009, a.v), 0.35)
        # The palms and the crowd.
        a.put(layer, trunk_mask, mix(p["trunk"], p["far"], 0.15))
        a.put(layer, crown_mask, mix(p["palm"], p["far"], 0.15))
        a.light(layer, a.rim(crown_mask, 0.0015, 0.0015, 0.0) * crown_mask, mix(p["palm_light"], p["far"], 0.2), 0.50)
        a.put(layer, a.mask_of(crowd), mix(p["crowd"], p["far"], 0.20))
        a.put(layer, a.mask_of(dress), mix(p["white"], p["far"], 0.10))
        # The ferry, the boats and the smoke.
        a.put(layer, a.mask_of(ferry_hull), mix(p["hull"], p["far"], 0.15))
        a.put(layer, a.mask_of(ferry_house), mix(p["white"], p["far"], 0.05))
        a.put(layer, a.mask_of(ferry_dark), mix(p["hull"], p["far"], 0.15))
        a.put(layer, a.mask_of(sails), mix(p["white"], p["far"], 0.10))
        a.put(layer, _reflected(a, boats, 0.653, "rio ferry ripple", water * (1.0 - boats)), mix(p["hull"], p["bay"], 0.55), 0.35)
        a.put(layer, smoke, p["smoke"], 0.65)
        mask = np.maximum(mask, smoke * 0.65)
        haze(a, layer, p["low"], 0.06, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near rio")
        bank, ground, bank_at = _bank(a, "near rio", 0.034, 0.030)
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        shrubs, shrub_pen = a.drawing()
        blooms, bloom_pen = a.drawing()
        lamp, lamp_pen = a.drawing()
        glass, glass_pen = a.drawing()
        # A royal palm and a bush of bougainvillea in flower at the left; a
        # gas lamp and more flowers at the right. The middle is a calm
        # garden bed.
        _royal_palm(trunk_pen, crown_pen, rng, 0.06, bank_at(0.06) + 0.004, 0.40, 0.006)
        for u, r in ((0.14, 0.040), (0.20, 0.028), (0.84, 0.030), (0.97, 0.040)):
            base = bank_at(u)
            _lumpy_crown(shrub_pen, rng, u, base - r * 0.8, r, r * 0.75, 30)
            for _ in range(36):
                ang = rng.uniform(0.0, math.tau)
                rr = rng.uniform(0.2, 1.0) ** 0.6
                bloom_pen.ellipse(u + math.cos(ang) * rr * r, base - r * 0.8 + math.sin(ang) * rr * r * 0.75, r * 0.10, r * 0.08)
        lu = 0.905
        lamp_pen.rect(lu - 0.0022, bank_at(lu) - 0.110, lu + 0.0022, bank_at(lu) + 0.004)
        lamp_pen.rect(lu - 0.0050, bank_at(lu) - 0.012, lu + 0.0050, bank_at(lu) + 0.004)
        lamp_pen.poly([(lu - 0.010, bank_at(lu) - 0.110), (lu + 0.010, bank_at(lu) - 0.110), (lu + 0.004, bank_at(lu) - 0.116), (lu - 0.004, bank_at(lu) - 0.116)])
        glass_pen.poly([(lu - 0.0085, bank_at(lu) - 0.138), (lu + 0.0085, bank_at(lu) - 0.138), (lu + 0.0065, bank_at(lu) - 0.112), (lu - 0.0065, bank_at(lu) - 0.112)])
        lamp_pen.poly([(lu - 0.011, bank_at(lu) - 0.137), (lu + 0.011, bank_at(lu) - 0.137), (lu, bank_at(lu) - 0.150)])
        bank_mask = np.maximum(a.mask_of(bank), ground)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        shrub_mask = a.mask_of(shrubs)
        bloom_mask = a.mask_of(blooms) * shrub_mask
        lamp_mask = a.mask_of(lamp)
        glass_mask = a.mask_of(glass)
        mask = np.maximum.reduce([bank_mask, trunk_mask, crown_mask, shrub_mask, lamp_mask, glass_mask])
        layer = a.blank()
        earth = a.ramp([(0.0, mix(p["forest"], p["near"], 0.50)), (0.66, mix(p["forest"], p["near"], 0.50)), (0.78, mix(p["near_light"], p["near"], 0.75)), (1.0, p["near"])])
        a.put(layer, bank_mask, earth)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.25)
        a.put(layer, trunk_mask, mix(p["trunk"], p["near"], 0.45))
        a.light(layer, a.rim(trunk_mask, 0.003, 0.0, 0.0) * trunk_mask, p["glow"], 0.35)
        a.put(layer, crown_mask, mix(p["palm"], p["near"], 0.30))
        a.light(layer, a.rim(crown_mask, 0.002, 0.002, 0.0) * crown_mask, p["palm_light"], 0.40)
        a.put(layer, shrub_mask, mix(p["forest"], p["near"], 0.35))
        a.put(layer, bloom_mask, mix(p["bloom"], p["near"], 0.20))
        a.light(layer, bloom_mask * a.rim(shrub_mask, 0.002, 0.003, 0.5), p["bloom_light"], 0.40)
        a.put(layer, lamp_mask, mix(p["iron"], p["near"], 0.30))
        a.put(layer, glass_mask, mix(p["glow"], p["near"], 0.35))
        a.light(layer, a.rim(lamp_mask, 0.002, 0.0, 0.0) * lamp_mask, p["glow"], 0.30)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.18)
        haze(a, layer, p["low"], 0.08, None)
        return layer
    layer = _air(a, p, "rio sea haze", p["low"], 0.22, p["near"], 0.16)
    a.put(layer, shafts(a, "rio shafts", 4, 0.16, 0.0, 0.85, 0.05), p["glow"], 0.06)
    return layer


def rio_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """The tips of royal palm fronds hang into the top of the view at two
    places. A few stems of a flowering bush stand from below at one
    place."""
    del layer_lights
    rng = art_.rand("rio foreground")
    for k in range(2):
        u0 = 0.10 + (k + rng.uniform(0.2, 0.8)) * 0.40
        for j in range(2):
            start = (u0 + (j - 0.5) * 0.05, 0.0)
            end = (start[0] + (0.09 if j else -0.09) + rng.uniform(-0.02, 0.02), 0.380 - rng.uniform(0.0, 0.010))
            ctrl = ((start[0] + end[0]) * 0.5 + (0.03 if j else -0.03), 0.20)
            rib = _arch(start, ctrl, end, 20)
            pen.line(rib, 0.0026)
            for i, (x, y) in enumerate(rib[1:], 1):
                side = 0.032 * (1.0 - i / 20.0 * 0.6)
                side = max(0.0, min(side, 0.390 - y))
                pen.line([(x, y), (x + side * 0.20, y + side)], 0.0013)
                pen.line([(x, y), (x - side * 0.20, y + side)], 0.0013)
    u = rng.uniform(0.44, 0.56)
    for j in range(4):
        x = u + (j - 1.5) * 0.014
        top = (x + rng.uniform(-0.006, 0.006), REST_BOTTOM - 0.002 - (j % 2) * 0.006)
        stem = _arch((x, 1.0), (x, top[1] + 0.10), top, 10)
        pen.line(stem, 0.0018)
        for i in (2, 4, 6, 8, 10):
            sx, sy = stem[i]
            for s in (-1.0, 1.0):
                pen.ellipse(sx + s * 0.005, sy + 0.002, 0.0045, 0.0035)
