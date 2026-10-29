"""The scenes of Eureka, the institute town of the Science dimension, and of
the space elevator that rises from it to the orbital station.

Jon, 2026-10-29: the science dimension gets a district of its own, and "the
science dimension should have a space elevator that brings you up to the
orbital station".

- ``eureka``: the town on the planet's surface on a clear bright day, a
  contrast with the evening of the other districts. Low green hills; the
  institute's buildings of pale sandstone and red brick with tall windows, an
  observatory dome, a clock tower, labs of glass and steel, tidy trees, a few
  coil towers. Its landmark is the space elevator: from its ground station on
  the horizon a thin bright tether rises straight up and is lost in the
  zenith, with a climber car partway up and, high over everything, the glint
  of the orbital station. Near the play: the trunk and a branch of a campus
  tree, a lamp post, an iron railing.
- ``eureka_heights``: high on the tether, for the upper room of the elevator's
  shaft. The air goes from deep blue to the black of space, stars come out
  high up, the curve of the planet lies far below with its cloud tops, and
  the tether runs straight through the middle of the view.

No drop shadows; the tether and the station are art in these panels, not a
shader, so they are there with every shader off.
"""

from __future__ import annotations

import numpy as np

from .artkit import Art, Pen, mix, scale, smoothstep
from .orbital import planet
from .parts import HORIZON, cumulus, fog, haze, lamps, motes, stars, solid, window_grid

PAL = {
    "top": (52, 112, 206),
    "mid": (112, 170, 232),
    "low": (206, 226, 242),
    "sun": (255, 246, 214),
    "cloud": (252, 252, 255),
    "cloud_shade": (176, 198, 228),
    "hill_far": (132, 168, 150),
    "hill": (102, 154, 92),
    "lawn": (92, 150, 72),
    "sandstone": (226, 204, 160),
    "brick": (168, 82, 62),
    "slate": (82, 92, 112),
    "glass": (150, 200, 226),
    "steel": (150, 160, 176),
    "copper": (176, 112, 70),
    "dome": (236, 236, 230),
    "tree": (58, 112, 62),
    "tree_light": (126, 180, 86),
    "tether": (240, 246, 255),
    "near": (34, 46, 44),
    "near_light": (126, 150, 120),
    "lamp": (255, 226, 160),
    # The heights.
    "space": (4, 6, 18),
    "high": (12, 30, 86),
    "air": (64, 128, 214),
    "beacon": (255, 120, 92),
}

#: Where the elevator's ground station stands, in `u`, and its tether.
TETHER_U = 0.70


def _sky_day(art: Art, p: dict) -> np.ndarray:
    """A clear day: deep blue overhead, pale at the horizon, a sun high on the
    left, and a few fair-weather clouds."""
    layer = art.opaque(art.ramp([(0.0, p["top"]), (0.36, p["mid"]), (HORIZON - 0.02, p["low"]), (1.0, mix(p["low"], p["hill_far"], 0.4))]))
    art.light(layer, art.spot(0.22, 0.20, 0.40, 1.6), p["sun"], 0.45)
    art.light(layer, art.spot(0.22, 0.20, 0.035, 1.0), p["sun"], 0.95)
    clouds = cumulus(art, "fair clouds", 0.40, 0.10, 6.0, 0.36, p["cloud"], p["cloud_shade"])
    art.tint(clouds, np.ones((art.n, art.n), dtype=np.float32), p["mid"], 0.18)
    layer = art.over(layer, clouds)
    art.grain(layer, "grain", 1.0)
    return layer


def _tether(pen: Pen, glow_pen: Pen, u: float, v_top: float, v_bottom: float, w: float) -> None:
    """The ribbon of the elevator: a thin straight line, with a soft glow."""
    pen.rect(u - w, v_top, u + w, v_bottom)
    glow_pen.rect(u - w * 4.0, v_top, u + w * 4.0, v_bottom)


def _climber(pen: Pen, u: float, v: float, s: float) -> None:
    """The car that climbs the tether: a squat capsule with fins."""
    pen.rect(u - s, v - s * 1.4, u + s, v + s * 1.4)
    pen.ellipse(u, v - s * 1.4, s, s * 0.5)
    pen.ellipse(u, v + s * 1.4, s, s * 0.5)
    pen.poly([(u - s, v - s * 0.6), (u - s * 1.8, v + s * 0.4), (u - s, v + s * 0.8)])
    pen.poly([(u + s, v - s * 0.6), (u + s * 1.8, v + s * 0.4), (u + s, v + s * 0.8)])


def _building(walls: Pen, roofs: Pen, wins: Pen, rng, u: float, foot: float, w: float, h: float) -> None:
    """An institute block: a wall with rows of tall windows and a low roof."""
    top = foot - h
    walls.rect(u, top, u + w, foot + 0.01)
    roofs.rect(u - w * 0.03, top - h * 0.06, u + w * 1.03, top + h * 0.02)
    window_grid(wins, rng, u + w * 0.06, top + h * 0.12, u + w * 0.94, foot - h * 0.08, w / max(3, int(w / 0.012)), h * 0.30, 0.9, w=0.45, h=0.62)


def _clock_tower(pen: Pen, face: Pen, u: float, foot: float, w: float, h: float) -> tuple[float, float, float]:
    """A tall square tower with a clock near its top and a pointed roof.
    Returns the clock's centre and radius."""
    pen.rect(u - w / 2, foot - h, u + w / 2, foot + 0.01)
    pen.rect(u - w * 0.6, foot - h - w * 0.15, u + w * 0.6, foot - h)
    pen.poly([(u - w * 0.6, foot - h - w * 0.15), (u + w * 0.6, foot - h - w * 0.15), (u, foot - h - w * 1.3)])
    cv = foot - h + w * 0.55
    face.ellipse(u, cv, w * 0.32)
    return u, cv, w * 0.32


def _dome(body: Pen, slit: Pen, u: float, foot: float, r: float) -> None:
    """The observatory: a drum and its white dome with the slit open."""
    body.rect(u - r, foot - r * 0.7, u + r, foot + 0.01)
    body.ellipse(u, foot - r * 0.7, r, r)
    slit.poly([(u - r * 0.10, foot - r * 1.68), (u + r * 0.10, foot - r * 1.68), (u + r * 0.14, foot - r * 0.75), (u - r * 0.14, foot - r * 0.75)])


def _lab(glass: Pen, frame: Pen, u: float, foot: float, w: float, h: float) -> None:
    """A lab of glass in a steel frame, with a saw-tooth roof of skylights."""
    glass.rect(u, foot - h, u + w, foot + 0.01)
    for k in range(5):
        x = u + w * k / 4.0
        frame.rect(x - 0.0012, foot - h, x + 0.0012, foot)
    frame.rect(u, foot - h * 0.52, u + w, foot - h * 0.49)
    teeth = 4
    for k in range(teeth):
        x0 = u + w * k / teeth
        glass.poly([(x0, foot - h), (x0 + w / teeth, foot - h), (x0 + w / teeth, foot - h - h * 0.28)])


def _coil(pen: Pen, u: float, foot: float, h: float) -> tuple[float, float]:
    """A coil tower: a lattice mast and the torus at its top. Returns the top."""
    w = h * 0.08
    pen.poly([(u - w * 1.6, foot + 0.01), (u + w * 1.6, foot + 0.01), (u + w * 0.5, foot - h), (u - w * 0.5, foot - h)])
    top = foot - h - h * 0.05
    pen.ellipse(u, top, w * 2.6, w * 0.9)
    return u, top


def _tree(pen: Pen, crown: Pen, rng, u: float, foot: float, h: float) -> None:
    """A tidy campus tree: a straight trunk and a round crown."""
    pen.rect(u - h * 0.03, foot - h * 0.5, u + h * 0.03, foot + 0.01)
    for _ in range(7):
        crown.ellipse(u + rng.uniform(-0.18, 0.18) * h, foot - h * rng.uniform(0.62, 0.88), h * rng.uniform(0.16, 0.24))


def eureka(layer_key: str, art: Art) -> np.ndarray:
    p = PAL
    if layer_key == "sky":
        return _sky_day(art, p)
    if layer_key == "far_backplate":
        rng = art.rand("eureka campus")
        air = mix(p["mid"], p["low"], 0.6)
        hills_far, far_line = art.ridge("far hills", HORIZON - 0.025, 0.03, cells=2.0, octaves=4, sharp=0.2)
        ground, line = art.ridge("campus ground", HORIZON + 0.02, 0.012, cells=3.0, octaves=3)

        def foot_at(u: float) -> float:
            return float(line[min(art.n - 1, max(0, int(u * art.n)))]) + 0.006

        walls, wall_pen = art.drawing()
        bricks, brick_pen = art.drawing()
        roofs, roof_pen = art.drawing()
        wins, win_pen = art.drawing()
        glass, glass_pen = art.drawing()
        frames, frame_pen = art.drawing()
        dome, dome_pen = art.drawing()
        slit, slit_pen = art.drawing()
        tower, tower_pen = art.drawing()
        face, face_pen = art.drawing()
        coils, coil_pen = art.drawing()
        trunks, trunk_pen = art.drawing()
        crowns, crown_pen = art.drawing()
        station, station_pen = art.drawing()
        tether, tether_pen = art.drawing()
        tether_glow, glow_pen = art.drawing()
        car, car_pen = art.drawing()
        orbit, orbit_pen = art.drawing()
        # The institute from left to right: brick halls, the clock tower, the
        # observatory on its rise, the labs, the coil yard, the elevator.
        layout = [
            ("brick", 0.00, 0.08, 0.050), ("tree", 0.085, 0.0, 0.050), ("sand", 0.10, 0.09, 0.060),
            ("tower", 0.215, 0.026, 0.150), ("sand", 0.235, 0.10, 0.055), ("tree", 0.345, 0.0, 0.055),
            ("dome", 0.40, 0.040, 0.0), ("brick", 0.45, 0.07, 0.045), ("lab", 0.53, 0.09, 0.045),
            ("tree", 0.63, 0.0, 0.045), ("coil", 0.645, 0.0, 0.080),
            ("lab", 0.78, 0.07, 0.040), ("coil", 0.865, 0.0, 0.070), ("tree", 0.885, 0.0, 0.050),
            ("brick", 0.90, 0.11, 0.050),
        ]
        coil_tops = []
        clock = None
        for kind, u, w, h in layout:
            foot = foot_at(u + w * 0.5)
            if kind == "brick":
                _building(brick_pen, roof_pen, win_pen, rng, u, foot, w, h)
            elif kind == "sand":
                _building(wall_pen, roof_pen, win_pen, rng, u, foot, w, h)
            elif kind == "tower":
                clock = _clock_tower(tower_pen, face_pen, u, foot, w, h)
            elif kind == "dome":
                _dome(dome_pen, slit_pen, u, foot - 0.008, w)
            elif kind == "lab":
                _lab(glass_pen, frame_pen, u, foot, w, h)
            elif kind == "coil":
                coil_tops.append(_coil(coil_pen, u, foot, h))
            else:
                _tree(trunk_pen, crown_pen, rng, u, foot, h)
        # The elevator's ground station: a broad base, a cone that holds the
        # anchor, and the tether from it straight up, out of the panel.
        su = TETHER_U
        sf = foot_at(su)
        station_pen.poly([(su - 0.055, sf + 0.01), (su + 0.055, sf + 0.01), (su + 0.040, sf - 0.030), (su - 0.040, sf - 0.030)])
        station_pen.poly([(su - 0.022, sf - 0.030), (su + 0.022, sf - 0.030), (su + 0.006, sf - 0.085), (su - 0.006, sf - 0.085)])
        station_pen.rect(su - 0.065, sf - 0.006, su + 0.065, sf + 0.01)
        bands, band_pen = art.drawing()
        for k, (half, v) in enumerate(((0.050, sf - 0.010), (0.044, sf - 0.020), (0.016, sf - 0.045), (0.011, sf - 0.065))):
            band_pen.rect(su - half, v - 0.0025, su + half, v + 0.0025)
        _tether(tether_pen, glow_pen, su, -0.02, sf - 0.08, 0.0013)
        _climber(car_pen, su, 0.33, 0.0055)
        # The orbital station, very high and far: a glint and a thin ring.
        orbit_pen.ellipse(su, 0.045, 0.006)
        orbit_pen.ring(su, 0.045, 0.016, 0.0016)

        layer = solid(art, hills_far, mix(p["hill_far"], air, 0.30), mix(p["hill_far"], air, 0.20), HORIZON - 0.08, HORIZON, "far hills", 0.06)
        art.put(layer, ground, mix(p["hill"], air, 0.25))
        art.put(layer, ground * art.noise("lawn stripes", cells=30.0, octaves=1, stretch=6.0), mix(p["lawn"], air, 0.15), 0.35)
        art.put(layer, art.mask_of(walls), mix(p["sandstone"], air, 0.30))
        art.put(layer, art.mask_of(bricks), mix(p["brick"], air, 0.30))
        art.put(layer, art.mask_of(roofs), mix(p["slate"], air, 0.35))
        building = np.maximum(art.mask_of(walls), art.mask_of(bricks))
        art.put(layer, art.mask_of(wins) * building, mix(p["glass"], scale(p["slate"], 0.6), 0.45), 0.85)
        art.put(layer, art.mask_of(tower), mix(p["sandstone"], air, 0.25))
        art.put(layer, art.mask_of(face), mix((250, 248, 236), air, 0.15))
        if clock is not None:
            hands, hand_pen = art.drawing()
            cu, cv, r = clock
            hand_pen.line([(cu, cv), (cu + r * 0.0, cv - r * 0.75)], r * 0.12)
            hand_pen.line([(cu, cv), (cu + r * 0.55, cv + r * 0.15)], r * 0.12)
            art.put(layer, art.mask_of(hands), scale(p["slate"], 0.7))
        art.put(layer, art.mask_of(dome), mix(p["dome"], air, 0.20))
        art.shade(layer, art.mask_of(dome) * smoothstep(0.38, 0.43, art.u), 0.18)
        art.put(layer, art.mask_of(slit), mix(p["slate"], air, 0.25))
        art.put(layer, art.mask_of(glass), mix(p["glass"], air, 0.30))
        art.light(layer, art.mask_of(glass) * art.noise("glass sheen", cells=8.0, octaves=2, stretch=0.3), p["sun"], 0.25)
        art.put(layer, art.mask_of(frames) * art.mask_of(glass), mix(p["steel"], air, 0.25))
        art.put(layer, art.mask_of(coils), mix(p["copper"], air, 0.35))
        art.put(layer, art.mask_of(trunks), mix((86, 66, 50), air, 0.35))
        art.put(layer, art.mask_of(crowns), mix(p["tree"], air, 0.30))
        art.light(layer, art.mask_of(crowns) * art.noise("crown light", cells=20.0, octaves=2), p["tree_light"], 0.30)
        art.put(layer, art.mask_of(station), mix(scale(p["steel"], 0.75), air, 0.15))
        art.put(layer, art.mask_of(bands) * art.mask_of(station), mix(p["copper"], air, 0.15))
        lamps(art, layer, [(su - 0.045, sf - 0.004, 0.0015), (su + 0.045, sf - 0.004, 0.0015), (su, sf - 0.083, 0.0018)], p["beacon"], halo=4.0, strength=0.8)
        art.light(layer, art.mask_of(tether_glow, blur=3.0), p["tether"], 0.30)
        art.put(layer, art.mask_of(tether), p["tether"], 0.95)
        art.put(layer, art.mask_of(car), mix(p["steel"], (255, 255, 255), 0.4))
        lamps(art, layer, [(su, 0.33 + 0.0055 * 1.4 + 0.003, 0.0012)], p["beacon"], halo=4.0, strength=0.8)
        art.put(layer, art.mask_of(orbit), mix(p["tether"], p["mid"], 0.35), 0.8)
        lamps(art, layer, [(su, 0.045, 0.002)], p["sun"], halo=5.0, strength=0.6)
        # The coils hum: a pale blue light at each top.
        lamps(art, layer, [(u, v, 0.002) for u, v in coil_tops], (170, 220, 255), halo=4.0, strength=0.6)
        body = np.clip(np.maximum.reduce([hills_far, ground, building, art.mask_of(tower), art.mask_of(dome), art.mask_of(glass), art.mask_of(crowns), art.mask_of(station)]), 0, 1)
        art.light(layer, art.rim(body, 0.003, 0.003, 0.4) * body, p["sun"], 0.30)
        haze(art, layer, p["low"], 0.06, HORIZON + 0.03)
        return layer
    if layer_key == "near_background":
        rng = art.rand("near eureka")
        image, pen = art.drawing()
        crown, crown_pen = art.drawing()
        lamp, lamp_pen = art.drawing()
        # The lawn's edge, and a low iron railing along a path.
        pen.rect(0.0, 0.725, 1.0, 1.0)
        pen.rect(0.36, 0.675, 0.70, 0.680)
        pen.rect(0.36, 0.700, 0.70, 0.704)
        for k in range(29):
            u = 0.36 + k * 0.012
            pen.rect(u - 0.0012, 0.672, u + 0.0012, 0.725)
            pen.ellipse(u, 0.671, 0.0025)
        # A lamp post on the right, its lamp a globe on a curled arm.
        pen.rect(0.755, 0.45, 0.762, 0.725)
        pen.rect(0.748, 0.715, 0.769, 0.725)
        pen.line([(0.758, 0.455), (0.772, 0.437), (0.788, 0.444)], 0.003)
        lamp_pen.ellipse(0.789, 0.457, 0.010)
        # The trunk of a campus tree on the left, and a branch over the path,
        # its leaves in thick clumps.
        pen.poly([(0.17, 0.725), (0.215, 0.725), (0.205, 0.45), (0.198, 0.0), (0.176, 0.0), (0.185, 0.45)])
        pen.line([(0.200, 0.40), (0.28, 0.35), (0.40, 0.335)], 0.007)
        pen.line([(0.27, 0.36), (0.32, 0.40)], 0.004)
        clumps = [(0.20, 0.27), (0.27, 0.31), (0.35, 0.31), (0.41, 0.33), (0.16, 0.30), (0.24, 0.24)]
        for _ in range(420):
            cu0, cv0 = clumps[rng.randrange(len(clumps))]
            crown_pen.ellipse(cu0 + rng.gauss(0.0, 0.028), cv0 + rng.gauss(0.0, 0.020), rng.uniform(0.006, 0.012))
        crown_mask = art.mask_of(crown) * smoothstep(0.41, 0.36, art.v)
        mask = art.mask_of(image)
        layer = solid(art, mask, mix(p["near"], p["near_light"], 0.30), scale(p["near"], 0.85), 0.25, 0.75, "campus", 0.08)
        art.put(layer, crown_mask, mix(p["tree"], p["near"], 0.40))
        art.light(layer, crown_mask * art.noise("near leaf light", cells=14.0, octaves=2), p["tree_light"], 0.35)
        body = np.maximum(mask, crown_mask)
        art.light(layer, art.rim(body, 0.003, 0.003, 0.4) * body, p["sun"], 0.35)
        art.put(layer, art.mask_of(lamp), mix(p["lamp"], (255, 255, 255), 0.3), 0.8)
        haze(art, layer, mix(p["mid"], p["low"], 0.5), 0.08, 0.74)
        return layer
    # The air: pollen and a little sun in it.
    layer = art.blank()
    art.put(layer, art.spot(0.22, 0.20, 0.45, 2.0), p["sun"], 0.08)
    art.put(layer, fog(art, "campus haze", 0.70, 0.08), p["low"], 0.10)
    art.put(layer, motes(art, "pollen", 24, 0.25, 0.80, 0.0008, 0.0016), p["sun"], 0.22)
    return layer


def eureka_heights(layer_key: str, art: Art) -> np.ndarray:
    p = PAL
    if layer_key == "sky":
        layer = art.opaque(art.ramp([(0.0, p["space"]), (0.34, p["space"]), (0.50, p["high"]), (0.62, p["air"]), (1.0, mix(p["air"], p["low"], 0.5))]))
        sky_stars = art.blank()
        stars(art, sky_stars, 1100, (236, 240, 255), v_max=0.62, tag="heights stars")
        art.fade(sky_stars, smoothstep(0.62, 0.40, art.v))
        layer = art.over(layer, sky_stars)
        # The planet far below: its curve across the bottom, with its air.
        planet(art, layer, 0.50, 0.64 + 2.4, 2.4, sun=(-0.6, -0.8), tag="eureka world")
        art.light(layer, art.band(0.62, 0.035, 1.4), p["air"], 0.30)
        art.grain(layer, "grain", 0.8)
        return layer
    if layer_key == "far_backplate":
        # The tether, straight through the view, with a beacon on it at
        # every stage, and a second car far below on its way up.
        image, pen = art.drawing()
        glow, glow_pen = art.drawing()
        car, car_pen = art.drawing()
        _tether(pen, glow_pen, 0.5, -0.02, 1.02, 0.0016)
        _climber(car_pen, 0.5, 0.58, 0.004)
        layer = art.blank()
        art.light(layer, art.mask_of(glow, blur=4.0), p["tether"], 0.30)
        art.put(layer, art.mask_of(image), p["tether"], 0.95)
        art.put(layer, art.mask_of(car), mix(p["steel"], p["air"], 0.3))
        lamps(art, layer, [(0.5, v, 0.0016) for v in (0.12, 0.30, 0.48, 0.66)], p["beacon"], halo=4.0, strength=0.8)
        return layer
    if layer_key == "near_background":
        # Thin high cloud far under the car, lit by a sun out of view.
        layer = cumulus(art, "high cirrus", 0.70, 0.06, 5.0, 0.36, (240, 246, 255), (150, 180, 220))
        art.fade(layer, smoothstep(0.62, 0.70, art.v) * 0.6)
        return layer
    # The air: sparse glints of ice.
    layer = art.blank()
    art.put(layer, motes(art, "ice", 30, 0.30, 0.90, 0.0008, 0.002), (230, 244, 255), 0.45)
    return layer
