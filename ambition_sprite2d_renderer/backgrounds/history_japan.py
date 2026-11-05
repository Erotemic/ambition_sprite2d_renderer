"""The scenes of the History dimension: Japan after Heian.

The History dimension is a grid. East is later, and each floor is a region
of the world. These rooms are on the floor of East Asia. They show Hakata
Bay in the summer of 1281, when the warriors of Kyushu held a wall of stone
against the second fleet of the Yuan, and Tokyo in 1872, the year of the
first railway. They use the same sepia of an old textbook and the same
rules as `history_eras.py` and `history_east_asia_coast.py`. The Edo room
has no scene of its own: it uses the houses of the ninja village.

- ``history_kamakura`` (Hakata Bay, northern Kyushu, summer 1281). A warm
  afternoon at the left and a storm that builds at the right. The far
  shore of the bay curves away from the left. A line of black pines grows
  on it, and at its foot, along the beach, is the Genko borui: a wall of
  stones laid dry, with a sloped face to the sea and a flat top. Small
  plain banners stand behind it. The hills of Kyushu are behind. Far out
  on the open sea, at the horizon, is the fleet of the Yuan: many junks
  with high square sterns and sails of battened matting. Over them, dark
  heavy cloud and rain come in: the typhoon that wrecked the fleet. The
  bay is calm near the shore and rough under the storm. Black pines and
  beach grass are near.
- ``history_meiji`` (Tokyo, 1872). A clear morning with high cloud. At the
  left, Ginza: rows of new two-storey brick shops with a colonnade of
  white columns on the street, gas lamps, young trees and telegraph poles
  with their wires. In the middle, Shimbashi station: a two-storey
  building faced with pale stone, a central block and two wings under low
  hipped roofs, tall windows and a porch. A short train stands beside it.
  At the right, the bay at Takanawa: the railway goes out on a long low
  embankment of stone over the water, with a train and its smoke on it,
  and small sailing boats on the bay. Far off, a small Mount Fuji stands
  over the city. A young willow, a telegraph pole and a gas lamp are near.

No picture here shows a battle, a burning ship or a body. The banners are
plain cloth, with no crest or sign. No flag or sign has writing on it.

The bright detail is far off or at the edges, and the middle of each near
layer is calm, so the play in front of it reads. The things that drift in the
air are the room's motes (`terrain/motes.py`), not part of these pictures.
"""

from __future__ import annotations

import math

import numpy as np

from .artkit import Art, Pen, mix, scale, smoothstep
from .history_east_asia_coast import _bank, _grass_blades, _lumpy_crown, _red_pine, _reflected
from .history_eras import REST_BOTTOM, _air, _gas_lamp, _heaps, _plume, _sun, _textbook, _train
from .history_origins import _arch, _rain
from .parts import HORIZON, cloud_mask, fog, haze, shafts, solid

# ---------------------------------------------------------------------------
# Parts that more than one room has
# ---------------------------------------------------------------------------


def _sail_boat(hull: Pen, sail: Pen, u: float, v: float, s: float, facing: float = 1.0) -> None:
    """A small Japanese boat of the coast (a wasen) far off: a low hull with
    a raised bow, one mast, and a tall square sail of cloth. `(u, v)` is
    the middle of its waterline and `s` its length."""
    f = facing
    hull.poly([(u - s * 0.50 * f, v - s * 0.16), (u - s * 0.42 * f, v + s * 0.03), (u + s * 0.40 * f, v + s * 0.03), (u + s * 0.58 * f, v - s * 0.24), (u + s * 0.44 * f, v - s * 0.14)])
    hull.line([(u - s * 0.02 * f, v - s * 0.14), (u - s * 0.02 * f, v - s * 0.90)], s * 0.03)
    sail.rect(u - s * 0.20 * f, v - s * 0.84, u + s * 0.16 * f, v - s * 0.20)


# ---------------------------------------------------------------------------
# Kamakura: Hakata Bay, summer 1281
# ---------------------------------------------------------------------------


KAMAKURA = {
    "top": (110, 140, 162),
    "mid": (206, 200, 182),
    "low": (244, 226, 190),
    "glow": (255, 214, 150),
    "sun": (255, 242, 214),
    "cloud": (250, 240, 222),
    "cloud_shadow": (196, 180, 168),
    "storm": (84, 88, 100),
    "storm_dark": (52, 56, 68),
    "storm_light": (172, 166, 160),
    "rain": (120, 128, 138),
    "bay": (80, 120, 122),
    "bay_light": (196, 208, 196),
    "bay_dark": (48, 72, 80),
    "foam": (226, 230, 224),
    "hill": (88, 112, 92),
    "pine": (36, 62, 46),
    "pine_light": (104, 134, 92),
    "bark": (64, 52, 48),
    "stone": (156, 148, 136),
    "stone_light": (214, 206, 190),
    "stone_dark": (88, 80, 74),
    "sand": (226, 206, 164),
    "sand_dark": (170, 146, 106),
    "earth": (120, 100, 70),
    "banner_white": (238, 232, 216),
    "banner_red": (176, 64, 48),
    "banner_blue": (60, 78, 112),
    "hull": (70, 58, 50),
    "mat": (176, 150, 108),
    "grass": (128, 150, 82),
    "grass_light": (196, 204, 130),
    "far": (198, 198, 186),
    "near": (34, 40, 34),
    "near_light": (150, 136, 100),
}

#: The far end of the shore, where the curve of the bay goes out of view.
KAMAKURA_SPIT = 0.56


def _junk(hull: Pen, sails: Pen, battens: Pen, u: float, v: float, s: float, facing: float = 1.0) -> None:
    """A big ship of the Yuan fleet far off: a hull with a low bow and a high
    square stern, and three masts, each with a lug sail of matting stiffened
    by battens. `(u, v)` is the middle of its waterline and `s` its length."""
    f = facing

    def at(x: float, y: float) -> tuple[float, float]:
        return (u + f * x * s, v - y * s)

    hull.poly([at(-0.52, 0.34), at(-0.36, 0.33), at(-0.32, 0.18), at(0.36, 0.13), at(0.54, 0.19), at(0.46, 0.02), at(-0.38, 0.0), at(-0.50, 0.08)])
    for m, top, reach in ((0.02, 1.00, 1.0), (0.32, 0.74, 0.70), (-0.30, 0.70, 0.62)):
        hull.line([at(m, 0.14), at(m, top)], s * 0.018)
        quad = [at(m - 0.22 * reach, 0.24), at(m + 0.16 * reach, 0.24), at(m + 0.14 * reach, top - 0.04), at(m - 0.26 * reach, top - 0.10)]
        sails.poly(quad)
        for k in range(1, 5):
            t = k / 5.0
            battens.line([(quad[0][0] + (quad[3][0] - quad[0][0]) * t, quad[0][1] + (quad[3][1] - quad[0][1]) * t),
                          (quad[1][0] + (quad[2][0] - quad[1][0]) * t, quad[1][1] + (quad[2][1] - quad[1][1]) * t)], s * 0.012)


def _kamakura_shore(u: float) -> float:
    """The `v` of the foot of the wall on the far shore at `u`: near at the
    left, far at the spit."""
    t = max(0.0, 1.0 - u / KAMAKURA_SPIT)
    return 0.614 + 0.050 * t**1.5


def _kamakura_wall_h(u: float) -> float:
    """The height of the wall at `u`: it gets lower as the shore goes away."""
    t = max(0.0, 1.0 - u / KAMAKURA_SPIT)
    return 0.004 + 0.024 * t**1.6


def _storm_mass(a: Art) -> np.ndarray:
    """The mask of the storm cloud: a dark heavy mass over the right of the
    sky, with a ragged base that comes down toward the sea."""
    lumps = a.noise("kamakura storm", cells=3.0, octaves=5, stretch=1.8)
    reach = smoothstep(0.40, 0.86, a.u + (lumps - 0.5) * 0.25)
    base = 0.47 + 0.07 * a.noise("kamakura storm base", cells=10.0, octaves=3, stretch=2.0) + 0.03 * smoothstep(0.6, 1.0, a.u)
    body = reach * smoothstep(base, base - 0.12, a.v)
    return smoothstep(0.30, 0.48, body * (0.55 + 0.6 * lumps))


def history_kamakura(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = KAMAKURA
    sun_at = (0.14, 0.30)
    spit = KAMAKURA_SPIT
    if layer_key == "sky":
        # A warm summer sky at the left with heap clouds and the sun. At the
        # right the typhoon comes in: dark heavy cloud with rain under it.
        # Under the horizon, the open sea, calm at the left and rough under
        # the storm, and the fleet far off on it.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.92)), (0.26, p["top"]), (0.46, p["mid"]), (HORIZON - 0.01, p["low"]),
                                 (HORIZON + 0.002, mix(p["bay"], p["low"], 0.50)), (0.70, p["bay"]), (1.0, scale(p["bay"], 0.90))]))
        _sun(a, layer, *sun_at, 0.022, p["sun"], p["glow"], 0.60)
        _heaps(a, layer, "kamakura heaps", ((0.10, 0.44, 0.07, 0.06), (0.30, 0.40, 0.08, 0.08)), p["cloud"], p["cloud_shadow"], 0.80)
        storm = _storm_mass(a)
        dusk = smoothstep(0.38, 0.95, a.u)
        a.tint(layer, dusk * (a.v < HORIZON), p["storm"], 0.35)
        paint = a.ramp([(0.0, p["storm_dark"]), (0.30, p["storm"]), (0.50, mix(p["storm"], p["storm_light"], 0.25)), (1.0, p["storm"])])
        a.put(layer, storm, paint, 0.92)
        swirl = smoothstep(0.55, 0.75, a.noise("kamakura storm swirl", cells=7.0, octaves=3, stretch=2.5))
        a.shade(layer, storm * swirl, 0.20)
        a.light(layer, a.rim(storm, 0.010, 0.0, 3.0) * storm, mix(p["storm_light"], p["glow"], 0.35), 0.60)
        # Rain falls from the base of the storm onto the sea far off.
        rain = _rain(a, "kamakura rain", 0.62, 1.10, 0.44, HORIZON + 0.004, -0.18)
        a.put(layer, rain * dusk, mix(p["rain"], p["storm"], 0.4), 0.70)
        a.put(layer, smoothstep(0.40, 0.48, a.v) * smoothstep(HORIZON + 0.01, HORIZON - 0.02, a.v) * smoothstep(0.62, 0.80, a.u), p["rain"], 0.35)
        # The hills of Kyushu, low and blue with haze, behind the far shore.
        hills, _ = a.ridge("kamakura hills", HORIZON - 0.030, 0.014, cells=5.0, octaves=4)
        a.put(layer, hills * smoothstep(HORIZON + 0.003, HORIZON, a.v) * smoothstep(0.62, 0.48, a.u), mix(p["hill"], p["low"], 0.55))
        # The fleet: many junks on the horizon, smaller and paler the further
        # off they are.
        rng = a.rand("kamakura fleet")
        fleet_hull, hull_pen = a.drawing()
        fleet_sail, sail_pen = a.drawing()
        fleet_bat, bat_pen = a.drawing()
        for _ in range(34):
            fu = rng.uniform(0.56, 1.0)
            depth = rng.random()
            fv = HORIZON + 0.0015 + depth * 0.008
            _junk(hull_pen, sail_pen, bat_pen, fu, fv, 0.007 + depth * 0.008, 1.0 if rng.random() < 0.5 else -1.0)
        fleet = np.maximum(a.mask_of(fleet_hull), a.mask_of(fleet_sail))
        a.put(layer, a.mask_of(fleet_sail), mix(p["mat"], p["storm"], 0.45))
        a.put(layer, a.mask_of(fleet_hull), mix(p["hull"], p["storm"], 0.40))
        a.put(layer, a.mask_of(fleet_bat) * fleet, mix(p["hull"], p["storm"], 0.35), 0.6)
        # The sea: long swells, and white caps where the wind of the storm is.
        sea = smoothstep(HORIZON + 0.001, HORIZON + 0.004, a.v)
        a.tint(layer, sea * smoothstep(0.50, 0.90, a.u), p["bay_dark"], 0.45)
        swell = smoothstep(0.60, 0.80, a.noise("kamakura swell", cells=80.0, octaves=2, stretch=10.0))
        a.light(layer, sea * swell * (1.0 - dusk), p["bay_light"], 0.35)
        a.shade(layer, sea * dusk * smoothstep(0.5, 0.2, a.noise("kamakura dark sea", cells=40.0, octaves=3, stretch=6.0)), 0.25)
        caps = smoothstep(0.72, 0.86, a.noise("kamakura caps", cells=120.0, octaves=2, stretch=5.0))
        a.put(layer, sea * caps * dusk * (1.0 - fleet), p["foam"], 0.55)
        glints = smoothstep(0.62, 0.82, a.noise("kamakura glints", cells=90.0, octaves=2, stretch=9.0))
        a.light(layer, sea * glints * a.spot(sun_at[0], HORIZON + 0.03, 0.28, 1.0, squash=0.9), p["glow"], 0.50)
        a.tint(layer, fog(a, "kamakura sea haze", HORIZON - 0.004, 0.012, 3.0) * (1.0 - dusk * 0.6), p["low"], 0.40)
        _textbook(a, layer, 0.08)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far kamakura")
        us = np.linspace(-0.02, spit + 0.02, 120)
        shore = [(u, _kamakura_shore(u)) for u in us]
        wall_top = [(u, _kamakura_shore(u) - _kamakura_wall_h(u)) for u in us]
        # The land behind the wall: a low dune that goes up to the wood of
        # pines, and the hills behind, at the left; it ends at the spit.
        land, land_pen = a.drawing()
        dune = [(u, _kamakura_shore(u) - _kamakura_wall_h(u) * 1.4) for u in us]
        land_pen.poly(dune + [(spit + 0.03, _kamakura_shore(spit) + 0.001)] + shore[::-1])
        cols = np.linspace(0.0, 1.0, a.n)
        hill_line = np.where(cols < spit + 0.02, 0.585 + 0.030 * (cols / spit) ** 1.4 - 0.012 * np.sin(cols * 17.0), 2.0)
        foot_v = np.array([_kamakura_shore(c) for c in cols], dtype=np.float32)
        hill = np.clip((a.v - hill_line[None, :]) * a.n + 0.5, 0.0, 1.0) * (a.v < foot_v[None, :])
        forest, forest_pen = a.drawing()
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        # The wood of pines: a band of dark crowns on the dune, and in front
        # of it single pines that lean, their crowns in flat layers.
        for _ in range(240):
            u = rng.uniform(-0.02, spit)
            t = max(0.0, 1.0 - u / spit)
            v = _kamakura_shore(u) - _kamakura_wall_h(u) * 1.6
            r = 0.004 + 0.016 * t
            _lumpy_crown(forest_pen, rng, u, v - r * rng.uniform(0.8, 2.6), r * 1.4, r * 0.7, 6)
        for k in range(22):
            u = -0.01 + (k + rng.uniform(0.0, 0.8)) * spit / 22.0
            t = max(0.0, 1.0 - u / spit)
            h = 0.016 + 0.090 * t**1.3
            _red_pine(trunk_pen, crown_pen, rng, u, _kamakura_shore(u) - _kamakura_wall_h(u) * 1.3, h, rng.uniform(-0.25, 0.45))
        # The wall: its sloped face of stones, the flat top, and the beach
        # in front of it.
        wall, wall_pen = a.drawing()
        wall_pen.poly(wall_top + shore[::-1])
        top_band, top_pen = a.drawing()
        top_pen.poly(wall_top + [(u, v + _kamakura_wall_h(u) * 0.14) for u, v in wall_top[::-1]])
        stones, stone_pen = a.drawing()
        # The stones of the face: four rows of rounded and split stones of
        # each size, fitted close, each row a half stone along from the
        # one under it.
        rows = 4
        for r in range(rows):
            u = -0.03 + r * 0.002
            while u < spit:
                hh = _kamakura_wall_h(u)
                size = hh * 0.44 * rng.uniform(0.7, 1.3)
                cv = _kamakura_shore(u) - hh * 0.86 * (r + 0.5) / rows
                stone_pen.ellipse(u + size * 0.5, cv + rng.uniform(-0.08, 0.08) * hh / rows, size * 0.47, hh * 0.86 / rows * rng.uniform(0.40, 0.52))
                u += size
        beach, beach_pen = a.drawing()
        beach_pen.poly(shore + [(u, v + 0.002 + 0.010 * max(0.0, 1.0 - u / spit) ** 1.5) for u, v in shore[::-1]])
        # Plain banners on poles behind the wall, at a few places.
        poles, pole_pen = a.drawing()
        cloth = {key: a.drawing() for key in ("banner_white", "banner_red", "banner_blue")}
        for k, bu in enumerate((0.03, 0.10, 0.17, 0.26, 0.34, 0.43, 0.50)):
            hh = _kamakura_wall_h(bu)
            foot = _kamakura_shore(bu) - hh
            tall = hh * 3.2
            pole_pen.line([(bu, foot + hh * 0.2), (bu, foot - tall)], max(0.0008, hh * 0.06))
            pole_pen.line([(bu, foot - tall), (bu + hh * 0.55, foot - tall)], max(0.0006, hh * 0.05))
            colour = ("banner_white", "banner_red", "banner_white", "banner_blue", "banner_white", "banner_red", "banner_white")[k]
            cloth[colour][1].rect(bu + hh * 0.04, foot - tall, bu + hh * 0.52, foot - tall + hh * 1.7)
        # The sea of the bay, and a few junks of the fleet nearer, at the
        # right, under the storm.
        hulls, hull_pen = a.drawing()
        sails, sail_pen = a.drawing()
        bats, bat_pen = a.drawing()
        for ju, jv, s, f in ((0.68, 0.617, 0.030, -1.0), (0.84, 0.620, 0.036, 1.0), (0.95, 0.616, 0.026, -1.0), (0.76, 0.613, 0.020, 1.0)):
            _junk(hull_pen, sail_pen, bat_pen, ju, jv, s, f)
        water = smoothstep(HORIZON + 0.010, HORIZON + 0.016, a.v)
        land_mask = a.mask_of(land)
        hill_mask = hill * smoothstep(spit + 0.03, spit - 0.02, a.u)
        forest_mask = a.mask_of(forest) * smoothstep(spit + 0.02, spit - 0.02, a.u)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        wall_mask = a.mask_of(wall)
        top_mask = a.mask_of(top_band) * wall_mask
        stone_mask = a.mask_of(stones) * wall_mask
        beach_mask = a.mask_of(beach)
        pole_mask = a.mask_of(poles)
        cloth_masks = {key: a.mask_of(img) for key, (img, _) in cloth.items()}
        flags = np.maximum.reduce(list(cloth_masks.values()))
        ships = np.maximum(a.mask_of(hulls), a.mask_of(sails))
        shore_things = np.maximum.reduce([land_mask, hill_mask, forest_mask, trunk_mask, crown_mask, wall_mask, beach_mask, pole_mask, flags])
        mask = np.maximum.reduce([shore_things, water, ships])
        layer = solid(a, mask, mix(p["hill"], p["far"], 0.40), mix(p["pine"], p["far"], 0.20), 0.56, 0.66, "kamakura far", 0.04)
        # The water: grey-green and calm near the far shore, darker and
        # rough at the right under the storm, with the picture of the shore
        # in it.
        dusk = smoothstep(0.45, 0.95, a.u)
        a.put(layer, water, a.ramp([(0.0, mix(p["bay"], p["low"], 0.40)), (HORIZON + 0.016, mix(p["bay"], p["low"], 0.40)), (0.66, mix(p["bay"], p["bay_light"], 0.12)),
                                     (1.0, scale(p["bay"], 0.85))]))
        a.tint(layer, water * dusk, p["bay_dark"], 0.45)
        # Under the far shore the water shows the dark of the pines, broken
        # by the ripples.
        shore_v = np.array([_kamakura_shore(c) + 0.002 + 0.010 * max(0.0, 1.0 - c / spit) ** 1.5 for c in cols], dtype=np.float32)
        below = a.v - shore_v[None, :]
        ripple = 0.6 + 0.4 * smoothstep(0.3, 0.7, a.noise("kamakura shore ripple", cells=120.0, octaves=2, stretch=8.0))
        a.put(layer, water * (below > 0.0) * smoothstep(0.022, 0.0, below) * smoothstep(spit + 0.02, spit - 0.04, a.u) * ripple, mix(p["pine"], p["bay"], 0.55), 0.40)
        lines = smoothstep(0.62, 0.84, a.noise("kamakura bay swell", cells=60.0, octaves=2, stretch=14.0))
        a.light(layer, water * lines * (1.0 - dusk) * (1.0 - land_mask), p["bay_light"], 0.30)
        caps = smoothstep(0.74, 0.88, a.noise("kamakura bay caps", cells=110.0, octaves=2, stretch=5.0))
        a.put(layer, water * caps * dusk * (1.0 - ships) * (1.0 - land_mask), p["foam"], 0.50)
        # The hills, and the wood of pines on the dune.
        a.put(layer, hill_mask, mix(p["hill"], p["far"], 0.45))
        a.light(layer, hill_mask * smoothstep(0.45, 0.72, a.noise("kamakura hill trees", cells=50.0, octaves=3)), mix(p["pine_light"], p["far"], 0.4), 0.35)
        a.put(layer, land_mask, mix(p["earth"], p["far"], 0.30))
        a.put(layer, forest_mask, mix(p["pine"], p["far"], 0.25))
        a.light(layer, forest_mask * smoothstep(0.55, 0.78, a.noise("kamakura pine lumps", cells=80.0, octaves=2)), mix(p["pine_light"], p["far"], 0.3), 0.40)
        a.light(layer, a.rim(forest_mask, 0.0, 0.002, 0.3) * forest_mask, p["glow"], 0.30)
        a.put(layer, trunk_mask, mix(p["bark"], p["far"], 0.25))
        a.put(layer, crown_mask, mix(p["pine"], p["far"], 0.12))
        a.light(layer, a.rim(crown_mask, 0.0, 0.0025, 0.2) * crown_mask, mix(p["pine_light"], p["glow"], 0.3), 0.55)
        # The banners on their poles.
        a.put(layer, pole_mask, mix(p["bark"], p["far"], 0.20))
        for key, m in cloth_masks.items():
            a.put(layer, m, mix(p[key], p["far"], 0.12))
        a.shade(layer, flags * a.rim(flags, -0.0015, 0.0, 0.0), 0.25)
        # The wall: grey stones with dark joints, the flat top pale, the
        # face lit by the sun at the left.
        a.put(layer, wall_mask, mix(p["stone_dark"], p["far"], 0.20))
        tones = a.noise("kamakura wall tones", cells=160.0, octaves=1)
        a.put(layer, stone_mask, mix(p["stone"], p["far"], 0.15))
        a.light(layer, stone_mask * smoothstep(0.5, 0.8, tones), mix(p["stone_light"], p["far"], 0.1), 0.40)
        a.shade(layer, stone_mask * smoothstep(0.4, 0.15, tones), 0.20)
        a.light(layer, a.rim(stone_mask, 0.0008, 0.0008, 0.0) * stone_mask, p["stone_light"], 0.45)
        a.put(layer, top_mask, mix(p["stone_light"], p["far"], 0.15))
        a.shade(layer, wall_mask * smoothstep(0.30, 0.55, a.u), 0.12)
        # The beach: pale sand, with a line of wet sand at the water.
        a.put(layer, beach_mask, mix(p["sand"], p["far"], 0.15))
        a.put(layer, beach_mask * a.rim(beach_mask, 0.0, -0.0025, 0.0), mix(p["sand_dark"], p["far"], 0.20), 0.6)
        a.light(layer, a.rim(beach_mask, 0.0, -0.0012, 0.0) * beach_mask, p["foam"], 0.5)
        # The nearer junks.
        a.put(layer, a.mask_of(sails), mix(p["mat"], p["storm"], 0.25))
        a.put(layer, a.mask_of(bats) * ships, mix(p["hull"], p["storm"], 0.25), 0.7)
        a.put(layer, a.mask_of(hulls), mix(p["hull"], p["storm"], 0.20))
        a.put(layer, _reflected(a, ships, 0.621, "kamakura junk ripple", water * (1.0 - ships)), mix(p["hull"], p["bay"], 0.60), 0.30)
        a.tint(layer, mask * dusk * (a.v < 0.64), p["storm"], 0.20)
        haze(a, layer, p["low"], 0.07, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near kamakura")
        bank, ground, bank_at = _bank(a, "near kamakura", 0.040, 0.034)
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        grass, grass_pen = a.drawing()
        heap, heap_pen = a.drawing()
        # A big black pine at the left that leans in from the sea, a smaller
        # one at the right, and a heap of stones for the wall beside it. The
        # middle is a calm bank of sand with a few tufts of beach grass.
        _red_pine(trunk_pen, crown_pen, rng, 0.05, bank_at(0.05) + 0.004, 0.36, 0.30)
        _red_pine(trunk_pen, crown_pen, rng, 0.955, bank_at(0.955) + 0.004, 0.25, -0.35)
        for _ in range(26):
            su = 0.84 + rng.gauss(0.0, 0.018)
            r = rng.uniform(0.006, 0.011)
            heap_pen.ellipse(su, bank_at(su) - r * rng.uniform(0.2, 1.6), r, r * 0.75)
        for _ in range(12):
            u = rng.uniform(0.0, 0.24) if rng.random() < 0.5 else rng.uniform(0.76, 1.0)
            _grass_blades(grass_pen, rng, u, bank_at(u) + 0.002, rng.uniform(0.016, 0.030), 7, 0.0013, 0.012)
        for _ in range(10):
            u = rng.uniform(0.28, 0.72)
            _grass_blades(grass_pen, rng, u, bank_at(u) + 0.002, rng.uniform(0.008, 0.014), 5, 0.0011, 0.008)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        grass_mask = a.mask_of(grass)
        heap_mask = a.mask_of(heap)
        mask = np.maximum.reduce([bank_mask, trunk_mask, crown_mask, grass_mask, heap_mask])
        layer = a.blank()
        # The bank: pale sand on its top, darker and damp below.
        earth = a.ramp([(0.0, mix(p["sand_dark"], p["near"], 0.30)), (0.68, mix(p["sand_dark"], p["near"], 0.30)), (0.78, mix(p["earth"], p["near"], 0.70)), (1.0, p["near"])])
        a.put(layer, bank_mask, earth)
        ripples = np.clip(1.0 - np.abs(((a.v * 160.0 + 1.2 * np.sin(a.u * 9.0)) % 1.0) - 0.5) / 0.10, 0.0, 1.0)
        a.shade(layer, bank_mask * ripples * smoothstep(0.69, 0.74, a.v) * smoothstep(0.86, 0.76, a.v), 0.10)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.35)
        a.put(layer, heap_mask, mix(p["stone"], p["near"], 0.45))
        a.light(layer, a.rim(heap_mask, 0.0015, 0.0015, 0.0) * heap_mask, p["stone_light"], 0.35)
        a.shade(layer, heap_mask * a.rim(heap_mask, -0.0015, -0.0015, 0.0), 0.35)
        a.put(layer, grass_mask, mix(p["grass"], p["near"], 0.40))
        a.light(layer, a.rim(grass_mask, 0.0015, 0.0, 0.2) * grass_mask, p["grass_light"], 0.30)
        a.put(layer, trunk_mask, mix(p["bark"], p["near"], 0.40))
        a.light(layer, a.rim(trunk_mask, 0.003, 0.0, 0.0) * trunk_mask, p["glow"], 0.30)
        a.put(layer, crown_mask, mix(p["pine"], p["near"], 0.30))
        a.light(layer, crown_mask * smoothstep(0.55, 0.78, a.noise("kamakura near needles", cells=60.0, octaves=2)), mix(p["pine_light"], p["near"], 0.3), 0.35)
        a.light(layer, a.rim(crown_mask, 0.0, 0.004, 0.3) * crown_mask, mix(p["pine_light"], p["glow"], 0.3), 0.45)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.18)
        haze(a, layer, p["low"], 0.08, None)
        return layer
    layer = _air(a, p, "kamakura sea haze", p["low"], 0.26, scale(p["near"], 0.8), 0.18)
    a.tint(layer, smoothstep(0.55, 1.0, a.u) * smoothstep(0.6, 0.0, a.v), p["storm_dark"], 0.12)
    a.put(layer, shafts(a, "kamakura shafts", 3, 0.16, 0.0, 0.85, 0.05) * smoothstep(0.55, 0.20, a.u), p["glow"], 0.08)
    return layer


def _needle_tuft(pen: Pen, rng, x: float, y: float, reach: float, end_v: float) -> None:
    """A tuft of long pine needles that fans out from the tip of a twig, the
    longest at the middle of the fan. No needle goes lower than `end_v`."""
    for k in range(19):
        a = math.radians(-190.0 + k * 11.1 + rng.uniform(-4.0, 4.0))
        r = reach * (0.55 + 0.45 * math.sin(math.pi * k / 18.0)) * rng.uniform(0.85, 1.1)
        tip = (x + math.cos(a) * r, min(end_v, y - math.sin(a) * r * 0.80))
        pen.line([(x, y), tip], 0.0014)


def _pine_bough(pen: Pen, rng, start: tuple[float, float], end: tuple[float, float], bend: float, end_v: float) -> None:
    """A bough of black pine that hangs into the view: a crooked branch with
    short twigs, and on the end of each twig a dense tuft of long needles.
    No needle goes lower than `end_v`."""
    ctrl = ((start[0] + end[0]) * 0.5 + bend, (start[1] + end[1]) * 0.5 - 0.05)
    rib = _arch(start, ctrl, end, 16)
    for i in range(len(rib) - 1):
        pen.line([rib[i], rib[i + 1]], 0.0048 - 0.0026 * i / 16.0)
    side = 1.0
    for i in range(5, 17, 2):
        x, y = rib[i]
        side = -side
        twig = (x + side * rng.uniform(0.020, 0.034), min(end_v - 0.030, y + rng.uniform(0.004, 0.018)))
        pen.line([(x, y), twig], 0.0020)
        _needle_tuft(pen, rng, twig[0], twig[1], 0.036, end_v)
    _needle_tuft(pen, rng, end[0], end[1], 0.044, end_v)


def kamakura_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Boughs of black pine hang into the top of the view at two places.
    A tuft of beach grass and a pine seedling stand from below at one
    place."""
    del layer_lights
    rng = art_.rand("kamakura foreground")
    for k in range(2):
        u0 = 0.08 + (k + rng.uniform(0.2, 0.8)) * 0.42
        side = -1.0 if k % 2 == 0 else 1.0
        _pine_bough(pen, rng, (u0, 0.0), (u0 + side * 0.11, 0.340), side * 0.06, 0.384)
    u = rng.uniform(0.44, 0.56)
    top = REST_BOTTOM - 0.004
    _grass_blades(pen, rng, u, 1.0, 1.0 - top, 20, 0.0016, 0.045)
    # The seedling: a short stem with two whorls of needles that stand up.
    x = u + 0.040
    tip = (x + 0.003, top + 0.026)
    pen.line([(x, 1.0), tip], 0.0028)
    for y, reach in ((tip[1], 0.020), (tip[1] + 0.020, 0.026)):
        for k in range(13):
            a = math.radians(20.0 + k * 11.7)
            pen.line([(x + 0.002, y), (x + 0.002 + math.cos(a) * reach, y - math.sin(a) * reach * 0.8)], 0.0014)


# ---------------------------------------------------------------------------
# Meiji: Tokyo, 1872
# ---------------------------------------------------------------------------


MEIJI = {
    "top": (90, 146, 196),
    "mid": (184, 206, 218),
    "low": (240, 232, 212),
    "glow": (255, 232, 180),
    "sun": (255, 246, 224),
    "cloud": (252, 250, 244),
    "cloud_shadow": (196, 202, 212),
    "bay": (80, 130, 150),
    "bay_light": (204, 224, 222),
    "hill": (120, 140, 140),
    "fuji": (142, 156, 182),
    "snow": (246, 246, 250),
    "brick": (172, 82, 58),
    "brick_dark": (112, 52, 40),
    "stucco": (238, 232, 216),
    "stone": (220, 212, 192),
    "slate": (86, 90, 102),
    "hole": (56, 52, 56),
    "shade": (92, 70, 62),
    "iron": (44, 44, 50),
    "glass": (255, 226, 160),
    "embank": (160, 152, 138),
    "embank_dark": (96, 90, 82),
    "street": (196, 184, 160),
    "tree": (92, 128, 70),
    "tree_light": (160, 186, 106),
    "willow": (130, 162, 86),
    "wood": (120, 92, 66),
    "hull": (78, 62, 50),
    "sail": (242, 238, 224),
    "smoke": (186, 182, 180),
    "crowd": (66, 58, 56),
    "far": (204, 210, 208),
    "near": (40, 38, 36),
    "near_light": (150, 136, 112),
}

#: The level of the street of Ginza and of the foot of the station.
MEIJI_STREET = 0.640
#: Where the shore of the bay is at the level of the street.
MEIJI_SHORE_U = 0.60


def _bricktown(pens: dict, u: float, v: float, w: float, h: float) -> None:
    """A shop of the Ginza Bricktown: a front of red brick of two storeys
    under a cornice of white stucco and a low roof of slate. Over the
    street a verandah of white stucco runs on a colonnade of white columns,
    and under it the shop fronts are in shade. The upper floor has tall
    windows with white trims. `pens` holds a pen for each paint."""
    first = v - h * 0.44
    pens["brick"].rect(u - w, v - h, u + w, first)
    pens["shade"].rect(u - w, first, u + w, v + 0.001)
    pens["stucco"].rect(u - w * 1.02, first - h * 0.02, u + w * 1.02, first + h * 0.05)
    pens["iron"].rect(u - w * 1.02, first - h * 0.10, u + w * 1.02, first - h * 0.085)
    cols = max(3, int(round(w / h * 5.0)))
    for c in range(cols + 1):
        x = u - w + c * 2.0 * w / cols
        pens["stucco"].rect(x - w * 0.025, first + h * 0.05, x + w * 0.025, v + 0.001)
        if c < cols:
            xm = x + w / cols
            pens["hole"].rect(xm - w / cols * 0.55, first + h * 0.14, xm + w / cols * 0.55, v + 0.001)
            pens["hole"].rect(xm - w / cols * 0.20, v - h * 0.88, xm + w / cols * 0.20, first - h * 0.16)
            pens["stucco"].rect(xm - w / cols * 0.28, v - h * 0.92, xm + w / cols * 0.28, v - h * 0.88)
    pens["stucco"].rect(u - w * 1.04, v - h - h * 0.06, u + w * 1.04, v - h + h * 0.02)
    pens["slate"].poly([(u - w * 1.02, v - h - h * 0.06), (u - w * 0.80, v - h - h * 0.20), (u + w * 0.80, v - h - h * 0.20), (u + w * 1.02, v - h - h * 0.06)])


def _station(pens: dict, u: float, v: float, s: float) -> None:
    """Shimbashi station of 1872: a building of two storeys faced with pale
    stone. A central block, a little higher, stands between two wings;
    each part has a low hipped roof of slate. Tall windows stand in even
    rows, and a porch on columns is at the middle of the front. `s` is the
    width of all of it and `(u, v)` the middle of its foot."""
    half = s * 0.5
    core = s * 0.15
    for x0, x1, h in ((u - half, u - core, s * 0.20), (u + core, u + half, s * 0.20), (u - core, u + core, s * 0.25)):
        pens["stone"].rect(x0, v - h, x1, v + 0.001)
        pens["stucco"].rect(x0 - s * 0.006, v - h - s * 0.012, x1 + s * 0.006, v - h + s * 0.004)
        pens["stucco"].rect(x0, v - h * 0.52, x1, v - h * 0.48)
        pens["slate"].poly([(x0 - s * 0.006, v - h - s * 0.012), (x0 + s * 0.035, v - h - s * 0.055), (x1 - s * 0.035, v - h - s * 0.055), (x1 + s * 0.006, v - h - s * 0.012)])
        count = max(3, int(round((x1 - x0) / (s * 0.034))))
        for k in range(count):
            x = x0 + (k + 0.5) * (x1 - x0) / count
            for top, bottom in ((h * 0.88, h * 0.60), (h * 0.40, h * 0.06)):
                pens["hole"].rect(x - s * 0.007, v - top, x + s * 0.007, v - bottom)
                pens["stucco"].rect(x - s * 0.010, v - top - s * 0.006, x + s * 0.010, v - top)
    # The porch on the front of the central block.
    pens["stucco"].rect(u - core * 0.70, v - s * 0.105, u + core * 0.70, v - s * 0.090)
    for k in range(5):
        x = u - core * 0.66 + k * core * 0.33
        pens["stucco"].rect(x - s * 0.004, v - s * 0.090, x + s * 0.004, v + 0.001)


def _telegraph_pole(pen: Pen, u: float, v: float, h: float) -> tuple[float, float]:
    """A telegraph pole: a tall plain post with two short cross arms near its
    top. Returns where its upper arm is."""
    pen.line([(u, v + 0.002), (u, v - h)], h * 0.030)
    for k in range(2):
        y = v - h * (0.94 - k * 0.10)
        pen.line([(u - h * 0.12, y), (u + h * 0.12, y)], h * 0.020)
    return u, v - h * 0.94


def _young_tree(trunk: Pen, crown: Pen, guard: Pen, rng, u: float, v: float, h: float) -> None:
    """A young street tree: a thin trunk with a small round crown, in a
    guard of four posts with a rail round them."""
    trunk.line([(u, v + 0.002), (u, v - h * 0.65)], h * 0.05)
    _lumpy_crown(crown, rng, u, v - h * 0.78, h * 0.20, h * 0.20, 14)
    for x in (u - h * 0.10, u + h * 0.10):
        guard.line([(x, v + 0.002), (x, v - h * 0.30)], h * 0.025)
    guard.line([(u - h * 0.12, v - h * 0.26), (u + h * 0.12, v - h * 0.26)], h * 0.02)


def _street_willow(trunk: Pen, strands: Pen, rng, u: float, v: float, h: float) -> None:
    """A young weeping willow of a street of Ginza, near: a slim trunk, a few
    limbs that arch up and out, and from them long thin strands that hang
    down, each with small narrow leaves on it, so the sky shows through."""
    top = (u + h * 0.03, v - h * 0.62)
    trunk.line(_arch((u, v + 0.002), (u - h * 0.02, v - h * 0.30), top, 10), h * 0.030)
    ends = []
    for k in range(5):
        side = (k - 2) * 0.5
        end = (top[0] + side * h * 0.22, top[1] - h * rng.uniform(0.20, 0.32))
        trunk.line(_arch(top, (top[0] + side * h * 0.06, end[1] - h * 0.02), end, 8), h * 0.012)
        ends.append(end)
    for ex, ey in ends:
        for j in range(7):
            x0 = ex + (j - 3) * h * 0.022
            y0 = ey + abs(j - 3) * h * 0.012
            length = h * rng.uniform(0.32, 0.50)
            pts = [(x0 + h * 0.012 * math.sin(t * 2.4 + j), y0 + t * length) for t in np.linspace(0.0, 1.0, 12)]
            strands.line([(ex, ey)] + pts[:1], h * 0.005)
            strands.line(pts, h * 0.005)
            for i, (sx, sy) in enumerate(pts[1:], 1):
                side = 1.0 if i % 2 else -1.0
                strands.poly([(sx, sy - h * 0.010), (sx + side * h * 0.008, sy + h * 0.004), (sx, sy + h * 0.012)])


def _embankment_top(u: float) -> float:
    """The `v` of the top of the railway embankment at Takanawa at `u`: it
    goes out from the shore and away over the bay."""
    t = (u - MEIJI_SHORE_U) / (1.02 - MEIJI_SHORE_U)
    return MEIJI_STREET + 0.006 - 0.030 * max(0.0, t) ** 0.8


def _embankment_thick(u: float) -> float:
    t = max(0.0, (u - MEIJI_SHORE_U) / (1.02 - MEIJI_SHORE_U))
    return 0.010 - 0.005 * t


def history_meiji(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = MEIJI
    sun_at = (0.10, 0.22)
    street = MEIJI_STREET
    shore_u = MEIJI_SHORE_U
    if layer_key == "sky":
        # A clear morning: a blue sky with thin high cloud, a small Fuji far
        # off over the city at the left, and the bay at the right under the
        # horizon, with the far hills of Boso on its far side.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.88)), (0.24, p["top"]), (0.48, p["mid"]), (HORIZON - 0.01, p["low"]),
                                 (HORIZON + 0.003, mix(p["bay"], p["low"], 0.45)), (0.70, p["bay"]), (1.0, scale(p["bay"], 0.92))]))
        _sun(a, layer, *sun_at, 0.020, p["sun"], p["glow"], 0.55)
        high = cloud_mask(a, "meiji high cloud", 0.20, 0.10, cells=2.5, cover=0.42, soft=0.30, stretch=9.0)
        a.put(layer, high, p["cloud"], 0.55)
        wisps = cloud_mask(a, "meiji wisps", 0.34, 0.06, cells=3.5, cover=0.35, soft=0.25, stretch=12.0)
        a.put(layer, wisps, p["cloud"], 0.40)
        _heaps(a, layer, "meiji heaps", ((0.72, 0.52, 0.05, 0.035), (0.88, 0.54, 0.04, 0.03)), p["cloud"], p["cloud_shadow"], 0.65)
        far_hills, _ = a.ridge("meiji boso", HORIZON - 0.008, 0.006, cells=6.0, octaves=3)
        a.put(layer, far_hills * smoothstep(HORIZON + 0.003, HORIZON, a.v) * smoothstep(0.55, 0.70, a.u), mix(p["hill"], p["low"], 0.62))
        city_hills, _ = a.ridge("meiji musashino", HORIZON - 0.010, 0.006, cells=5.0, octaves=3)
        a.put(layer, city_hills * smoothstep(HORIZON + 0.003, HORIZON, a.v) * smoothstep(0.62, 0.50, a.u), mix(p["hill"], p["low"], 0.55))
        # Fuji: a wide cone with a snow cap, pale with distance.
        fuji, fuji_pen = a.drawing()
        fu, fv, fh, fw = 0.22, HORIZON - 0.004, 0.080, 0.15
        pts = [(fu + x * fw, fv - fh * (1.0 - abs(x)) ** 1.9 - 0.004 * (abs(x) < 0.06)) for x in np.linspace(-1.0, 1.0, 61)]
        fuji_pen.poly(pts)
        fuji_mask = a.mask_of(fuji)
        a.put(layer, fuji_mask, mix(p["fuji"], p["low"], 0.40))
        cap = fuji_mask * smoothstep(fv - fh * 0.50, fv - fh * 0.60, a.v + 0.008 * np.sin(a.u * 260.0))
        a.put(layer, cap, mix(p["snow"], p["low"], 0.20))
        a.light(layer, a.rim(fuji_mask, 0.004, 0.0, 1.0) * fuji_mask, p["glow"], 0.25)
        a.tint(layer, fog(a, "meiji haze", HORIZON - 0.006, 0.016, 3.0), p["low"], 0.45)
        glints = smoothstep(0.62, 0.82, a.noise("meiji glints", cells=90.0, octaves=2, stretch=9.0))
        a.light(layer, (a.v > HORIZON + 0.003) * glints * smoothstep(0.55, 0.75, a.u), p["bay_light"], 0.35)
        _textbook(a, layer, 0.07)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far meiji")
        keys = ("brick", "stucco", "slate", "hole", "shade", "iron", "stone", "glass")
        pens = {key: a.drawing() for key in keys}
        pen_of = {key: pen for key, (_, pen) in pens.items()}
        # Ginza: a far row of brick shops up the street, and the near row
        # with its colonnade.
        x = -0.02
        while x < 0.30:
            w = rng.uniform(0.016, 0.022)
            _bricktown(pen_of, x + w, street - 0.016, w, 0.038)
            x += w * 2.0 + 0.001
        x = -0.015
        fronts = []
        while x < 0.29:
            w = rng.uniform(0.024, 0.034)
            _bricktown(pen_of, x + w, street, w, rng.uniform(0.050, 0.056))
            fronts.append(x + w)
            x += w * 2.0 + 0.0015
        # Shimbashi station, and the track that leaves it to the right.
        _station(pen_of, 0.455, street, 0.27)
        rails, rail_pen = a.drawing()
        rail_pen.rect(0.30, street + 0.002, shore_u + 0.01, street + 0.004)
        rail_pen.rect(0.30, street + 0.006, shore_u + 0.01, street + 0.008)
        # The street furniture of Ginza: gas lamps, young trees and the
        # telegraph poles with their wires; a few people and rickshaws.
        lamps, lamp_pen = a.drawing()
        flames = [_gas_lamp(lamp_pen, lu, street + 0.010, 0.020) for lu in (0.02, 0.09, 0.16, 0.23, 0.30)]
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        guards, guard_pen = a.drawing()
        for tu in (0.055, 0.125, 0.195, 0.265):
            _young_tree(trunk_pen, crown_pen, guard_pen, rng, tu, street + 0.012, 0.030)
        poles, pole_pen = a.drawing()
        tops = [_telegraph_pole(pole_pen, pu, street + 0.008, 0.060) for pu in (-0.03, 0.07, 0.17, 0.27, 0.37)]
        tops += [_telegraph_pole(pole_pen, pu, _embankment_top(pu) + 0.001, 0.050 - (pu - 0.6) * 0.06) for pu in (0.63, 0.73, 0.83, 0.93, 1.03)]
        tops.sort()
        for (u0, v0), (u1, v1) in zip(tops[:-1], tops[1:]):
            if u1 - u0 > 0.15:
                continue
            for k in range(2):
                pole_pen.curve((u0, v0 + k * 0.006), (u1, v1 + k * 0.006), 0.004, 0.0007)
        people, people_pen = a.drawing()
        for _ in range(26):
            cu = rng.uniform(0.0, 0.36)
            cv = street + rng.uniform(0.005, 0.016)
            s = 0.0040
            people_pen.ellipse(cu, cv - s * 0.9, s * 0.42, s * 0.9)
            people_pen.ellipse(cu, cv - s * 2.0, s * 0.32)
        for ru, rv, f in ((0.11, street + 0.015, 1.0), (0.21, street + 0.011, -1.0), (0.34, street + 0.016, 1.0)):
            s = 0.012
            people_pen.ring(ru, rv - s * 0.30, s * 0.30, s * 0.06)
            people_pen.rect(ru - s * 0.30, rv - s * 0.80, ru + s * 0.10, rv - s * 0.42)
            people_pen.poly([(ru - s * 0.32, rv - s * 0.80), (ru - s * 0.30, rv - s * 1.15), (ru + s * 0.02, rv - s * 1.05), (ru + s * 0.04, rv - s * 0.80)])
            people_pen.line([(ru, rv - s * 0.50), (ru + f * s * 0.95, rv - s * 0.45)], s * 0.05)
            people_pen.ellipse(ru + f * s * 1.05, rv - s * 0.55, s * 0.12, s * 0.30)
            people_pen.ellipse(ru + f * s * 1.05, rv - s * 0.98, s * 0.10)
        # The embankment at Takanawa: a long low bank of stone that goes out
        # over the bay, a train on it with its smoke, and the train at the
        # station.
        bank, bank_pen = a.drawing()
        us = np.linspace(shore_u - 0.02, 1.03, 60)
        top_pts = [(u, _embankment_top(u)) for u in us]
        bank_pen.poly(top_pts + [(u, v + _embankment_thick(u)) for u, v in top_pts[::-1]])
        train, train_pen = a.drawing()
        stack = _train(train_pen, 0.80, _embankment_top(0.80) - 0.001, 0.020, 3)
        smoke = _plume(a, "meiji train smoke", stack[0], stack[1], 0.06, -0.09, 0.016)
        stack2 = _train(train_pen, 0.625, street + 0.002, 0.022, 2)
        smoke = np.maximum(smoke, _plume(a, "meiji station steam", stack2[0], stack2[1], 0.05, -0.03, 0.010) * 0.7)
        # The bay: small sailing boats, and the low forts far off on it.
        hulls, hull_pen = a.drawing()
        sails, sail_pen = a.drawing()
        for bu, bv, s in ((0.70, 0.618, 0.022), (0.88, 0.624, 0.026), (0.96, 0.612, 0.016), (0.77, 0.662, 0.030)):
            _sail_boat(hull_pen, sail_pen, bu, bv, s, 1.0 if bu < 0.8 else -1.0)
        forts, fort_pen = a.drawing()
        for fu, fw in ((0.74, 0.014), (0.90, 0.011)):
            fort_pen.poly([(fu - fw, HORIZON + 0.010), (fu - fw * 0.85, HORIZON + 0.006), (fu + fw * 0.85, HORIZON + 0.006), (fu + fw, HORIZON + 0.010)])
            for k in range(6):
                fort_pen.ellipse(fu - fw * 0.7 + k * fw * 0.28, HORIZON + 0.005, fw * 0.12, 0.003)
        # The ground of the city, down to the shore.
        # The ground of the city: the street, and the stone wall of its quay
        # on the canal that goes out to the bay.
        quay = street + 0.020
        city = smoothstep(shore_u + 0.004, shore_u - 0.004, a.u - (a.v - street) * 0.6)
        ground = (a.v > street - 0.0005) * (a.v < quay) * city
        quay_mask = (a.v >= quay) * (a.v < quay + 0.006) * city
        water = smoothstep(HORIZON + 0.004, HORIZON + 0.010, a.v) * (1.0 - ground) * (1.0 - quay_mask)
        masks = {key: a.mask_of(img) for key, (img, _) in pens.items()}
        building = np.maximum.reduce(list(masks.values()))
        rail_mask = a.mask_of(rails)
        lamp_mask = a.mask_of(lamps) * (a.v < street + 0.012)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        guard_mask = a.mask_of(guards)
        pole_mask = a.mask_of(poles) * (a.v < quay)
        people_mask = a.mask_of(people)
        bank_mask = a.mask_of(bank)
        train_mask = a.mask_of(train)
        boats = np.maximum(a.mask_of(hulls), a.mask_of(sails))
        fort_mask = a.mask_of(forts)
        mask = np.maximum.reduce([building, ground, quay_mask, water, rail_mask, lamp_mask, trunk_mask, crown_mask, guard_mask, pole_mask, people_mask, bank_mask, train_mask, boats, fort_mask])
        layer = solid(a, mask, mix(p["street"], p["far"], 0.30), mix(p["street"], p["near"], 0.10), 0.62, 0.70, "meiji far", 0.04)
        # The bay: blue, lighter far off, with the pictures of the
        # embankment and the boats in it.
        a.put(layer, water, a.ramp([(0.0, mix(p["bay"], p["low"], 0.40)), (HORIZON + 0.016, mix(p["bay"], p["low"], 0.40)), (0.66, mix(p["bay"], p["bay_light"], 0.15)),
                                     (1.0, scale(p["bay"], 0.85))]))
        lines = smoothstep(0.62, 0.84, a.noise("meiji swell", cells=70.0, octaves=2, stretch=14.0))
        a.light(layer, water * lines * smoothstep(HORIZON, HORIZON + 0.05, a.v), p["bay_light"], 0.25)
        a.put(layer, _reflected(a, building, quay + 0.006, "meiji city ripple", water * (a.v > quay + 0.006)), mix(p["brick"], p["bay"], 0.60), 0.30)
        # The street: pale gravel, with ruts; the quay wall of grey stone.
        a.put(layer, ground, mix(p["street"], p["far"], 0.15))
        a.shade(layer, ground * smoothstep(0.55, 0.75, a.noise("meiji ruts", cells=50.0, octaves=2, stretch=12.0)), 0.10)
        a.put(layer, quay_mask, mix(p["embank"], p["far"], 0.15))
        a.shade(layer, quay_mask * smoothstep(quay + 0.001, quay + 0.006, a.v), 0.35)
        a.shade(layer, quay_mask * (np.abs(((a.u * 160.0) % 1.0) - 0.5) < 0.04), 0.30)
        a.put(layer, rail_mask, mix(p["iron"], p["far"], 0.30))
        # The buildings.
        a.put(layer, masks["brick"], mix(p["brick"], p["far"], 0.12))
        courses = np.clip(1.0 - np.abs(((a.v * 1400.0) % 1.0) - 0.5) / 0.12, 0.0, 1.0)
        a.shade(layer, masks["brick"] * courses, 0.10)
        a.put(layer, masks["shade"], mix(p["shade"], p["far"], 0.15))
        a.put(layer, masks["stone"], mix(p["stone"], p["far"], 0.10))
        a.shade(layer, masks["stone"] * np.clip(1.0 - np.abs(((a.v * 900.0) % 1.0) - 0.5) / 0.08, 0.0, 1.0), 0.08)
        a.put(layer, masks["slate"], mix(p["slate"], p["far"], 0.20))
        a.put(layer, masks["hole"], mix(p["hole"], p["far"], 0.25))
        a.put(layer, masks["stucco"], mix(p["stucco"], p["far"], 0.05))
        a.put(layer, masks["iron"], mix(p["iron"], p["far"], 0.20))
        a.light(layer, a.rim(building, 0.0015, 0.0, 0.0) * building, p["glow"], 0.40)
        a.shade(layer, a.rim(building, -0.0015, 0.0, 0.0) * building, 0.20)
        # The street things.
        a.put(layer, trunk_mask, mix(p["wood"], p["far"], 0.20))
        a.put(layer, crown_mask, mix(p["tree"], p["far"], 0.15))
        a.light(layer, a.rim(crown_mask, 0.0015, 0.0015, 0.0) * crown_mask, mix(p["tree_light"], p["glow"], 0.3), 0.50)
        a.put(layer, guard_mask, mix(p["wood"], p["far"], 0.10))
        a.put(layer, lamp_mask, mix(p["iron"], p["far"], 0.15))
        for fu, fv in flames:
            a.glow(layer, a.spot(fu, fv, 0.004, 1.2), p["glass"], 0.8)
        a.put(layer, pole_mask, mix(p["wood"], p["near"], 0.30))
        a.put(layer, people_mask, mix(p["crowd"], p["far"], 0.20))
        # The embankment, the trains and the smoke.
        a.put(layer, bank_mask, mix(p["embank"], p["far"], 0.15))
        a.shade(layer, bank_mask * smoothstep(0.0, 1.0, (a.v - np.interp(a.u, us, [v for _, v in top_pts])) / 0.008), 0.35)
        a.light(layer, a.rim(bank_mask, 0.0, 0.0015, 0.0) * bank_mask, p["stucco"], 0.55)
        a.put(layer, train_mask, mix(p["iron"], p["far"], 0.15))
        a.light(layer, a.rim(train_mask, 0.0, 0.0012, 0.0) * train_mask, p["glow"], 0.35)
        a.put(layer, fort_mask, mix(p["embank"], p["far"], 0.45))
        a.put(layer, fort_mask * (a.v < HORIZON + 0.0075), mix(p["tree"], p["far"], 0.45))
        a.put(layer, a.mask_of(hulls), mix(p["hull"], p["far"], 0.20))
        a.put(layer, a.mask_of(sails), mix(p["sail"], p["far"], 0.05))
        a.shade(layer, a.mask_of(sails) * (np.abs(((a.u * 600.0) % 1.0) - 0.5) < 0.08), 0.15)
        a.put(layer, _reflected(a, boats, 0.640, "meiji boat ripple", water * (1.0 - boats) * (1.0 - bank_mask)), mix(p["hull"], p["bay"], 0.55), 0.30)
        a.put(layer, smoke, p["smoke"], 0.85)
        a.shade(layer, smoke * smoothstep(0.4, 0.8, a.noise("meiji smoke lumps", cells=40.0, octaves=2)), 0.15)
        mask = np.maximum(mask, smoke * 0.85)
        haze(a, layer, p["low"], 0.06, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near meiji")
        bank, ground, bank_at = _bank(a, "near meiji", 0.034, 0.030)
        pole, pole_pen = a.drawing()
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        guards, guard_pen = a.drawing()
        lamp, lamp_pen = a.drawing()
        kerb, kerb_pen = a.drawing()
        # A telegraph pole and a young willow in its guard at the left; a gas
        # lamp and a young tree at the right. The middle is a calm verge of
        # gravel with a kerb of stone.
        top = _telegraph_pole(pole_pen, 0.035, bank_at(0.035) + 0.004, 0.34)
        for k in range(2):
            pole_pen.curve((-0.02, top[1] + 0.02 + k * 0.034), (0.035, top[1] + k * 0.034), 0.010, 0.0016)
        _street_willow(trunk_pen, crown_pen, rng, 0.145, bank_at(0.145) + 0.004, 0.24)
        for x in (0.125, 0.165):
            guard_pen.line([(x, bank_at(0.145) + 0.004), (x, bank_at(0.145) - 0.050)], 0.0030)
        guard_pen.line([(0.120, bank_at(0.145) - 0.044), (0.170, bank_at(0.145) - 0.044)], 0.0024)
        flame = _gas_lamp(lamp_pen, 0.88, bank_at(0.88) + 0.004, 0.13)
        _young_tree(trunk_pen, crown_pen, guard_pen, rng, 0.965, bank_at(0.965) + 0.004, 0.20)
        for u in np.linspace(0.0, 1.0, 40):
            kerb_pen.rect(u, bank_at(u) - 0.001, u + 0.026, bank_at(u) + 0.006)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        pole_mask = a.mask_of(pole)
        trunk_mask = a.mask_of(trunks)
        crown_mask = a.mask_of(crowns)
        guard_mask = a.mask_of(guards)
        lamp_mask = a.mask_of(lamp)
        kerb_mask = a.mask_of(kerb) * bank_mask
        mask = np.maximum.reduce([bank_mask, pole_mask, trunk_mask, crown_mask, guard_mask, lamp_mask])
        layer = a.blank()
        earth = a.ramp([(0.0, mix(p["street"], p["near"], 0.45)), (0.68, mix(p["street"], p["near"], 0.45)), (0.78, mix(p["near_light"], p["near"], 0.70)), (1.0, p["near"])])
        a.put(layer, bank_mask, earth)
        a.shade(layer, bank_mask * smoothstep(0.55, 0.80, a.noise("meiji gravel", cells=200.0, octaves=1)), 0.12)
        a.put(layer, kerb_mask, mix(p["embank"], p["near"], 0.40))
        a.light(layer, a.rim(kerb_mask, 0.0, 0.002, 0.0) * kerb_mask, p["glow"], 0.35)
        a.shade(layer, kerb_mask * (np.abs(((a.u * 38.5) % 1.0)) < 0.04), 0.4)
        a.put(layer, pole_mask, mix(p["wood"], p["near"], 0.45))
        a.light(layer, a.rim(pole_mask, 0.002, 0.0, 0.0) * pole_mask, p["glow"], 0.30)
        a.put(layer, trunk_mask, mix(p["wood"], p["near"], 0.45))
        a.put(layer, crown_mask, mix(p["willow"], p["near"], 0.30))
        a.light(layer, a.rim(crown_mask, 0.002, 0.002, 0.0) * crown_mask, p["tree_light"], 0.40)
        a.put(layer, guard_mask, mix(p["wood"], p["near"], 0.30))
        a.put(layer, lamp_mask, mix(p["iron"], p["near"], 0.30))
        a.light(layer, a.rim(lamp_mask, 0.002, 0.0, 0.0) * lamp_mask, p["glow"], 0.30)
        a.glow(layer, a.spot(flame[0], flame[1], 0.010, 1.4), p["glass"], 0.8)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.18)
        haze(a, layer, p["low"], 0.08, None)
        return layer
    layer = _air(a, p, "meiji morning haze", p["low"], 0.22, p["near"], 0.16)
    a.put(layer, shafts(a, "meiji shafts", 4, 0.16, 0.0, 0.85, 0.05), p["glow"], 0.06)
    return layer


def meiji_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Strands of a willow hang into the top of the view at two places. A
    few blades of grass stand from below at one place."""
    del layer_lights
    rng = art_.rand("meiji foreground")
    for k in range(2):
        u0 = 0.10 + (k + rng.uniform(0.2, 0.8)) * 0.40
        pen.line(_arch((u0 - 0.05, 0.0), (u0, 0.03), (u0 + 0.05, 0.02), 10), 0.0028)
        for j in range(11):
            x = u0 - 0.050 + j * 0.010 + rng.uniform(-0.003, 0.003)
            length = rng.uniform(0.22, 0.36)
            sway = rng.uniform(0.006, 0.016) * (1.0 if j % 2 else -1.0)
            strand = [(x + sway * t * t + 0.003 * math.sin(t * 5.0 + j), 0.02 + t * length) for t in np.linspace(0.0, 1.0, 16)]
            pen.line(strand, 0.0013)
            for i, (sx, sy) in enumerate(strand[2:], 2):
                if sy > 0.380:
                    break
                side = 1.0 if i % 2 else -1.0
                pen.poly([(sx, sy - 0.006), (sx + side * 0.0034, sy + 0.002), (sx, sy + 0.008)])
    u = rng.uniform(0.44, 0.56)
    _grass_blades(pen, rng, u, 1.0, 1.0 - (REST_BOTTOM - 0.002), 16, 0.0016, 0.040)
