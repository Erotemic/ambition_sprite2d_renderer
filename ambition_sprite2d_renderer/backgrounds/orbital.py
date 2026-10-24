"""The Science dimension's orbital station: inside its decks, and out in the
open trusses of its gravity works, with the planet below.

Jon, 2026-10-24: "gnuton can be consolidated with the orbital station /
space zone ... Maybe he is in the science dimension, which has a space
station space biome."

Two scenes share one palette:

- ``orbital``: inside a deck. Wall plates of painted steel between hull
  ribs, a row of long viewports with the stars and the curve of the planet
  in them, cable trays and lockers in front.
- ``orbital_truss``: out in the open, under glass. The planet fills the lower
  view (its day side to the left), the station's far ring and a hauler's
  running lights over it, and the near lattice of the truss.

The planet is art in these panels, not a shader: with every shader off the
station still has its view.
"""

from __future__ import annotations

import math

import numpy as np

from .artkit import Art, mix, polar, scale, smoothstep
from .parts import HORIZON, haze, lamps, stars, vignette

PAL = {
    "space": (6, 8, 20),
    "space_high": (14, 18, 40),
    "nebula": (60, 44, 96),
    "wall": (44, 54, 72),
    "wall_dark": (24, 30, 44),
    "steel": (78, 92, 112),
    "steel_light": (150, 170, 190),
    "rib": (32, 40, 56),
    "amber": (246, 176, 76),
    "cyan": (110, 220, 240),
    "ocean": (34, 96, 156),
    "ocean_deep": (14, 40, 84),
    "land": (96, 132, 82),
    "desert": (176, 150, 104),
    "cloud": (232, 238, 244),
    "air": (120, 186, 255),
    "night": (10, 16, 34),
    "city": (255, 206, 130),
}


# ---------------------------------------------------------------------------
# The planet
# ---------------------------------------------------------------------------


def planet(art: Art, layer: np.ndarray, cu: float, cv: float, r: float, sun: tuple[float, float] = (-0.8, -0.45), tag: str = "planet") -> None:
    """A world seen from orbit: oceans, land and cloud on a disc, lit from
    `sun` (a direction in `u, v`), its night side with city lights, and a thin
    blue air round its edge. No shadow is cast on anything."""
    du, dv = (art.u - cu) / r, (art.v - cv) / r
    d2 = du * du + dv * dv
    inside = d2 < 1.0
    disc = smoothstep(1.0, 0.996, np.sqrt(d2))
    # A sphere's normal, to light it.
    nz = np.sqrt(np.clip(1.0 - d2, 0.0, 1.0))
    sx, sy = sun
    sz = 0.35
    norm = math.sqrt(sx * sx + sy * sy + sz * sz)
    lit = np.clip((du * sx + dv * sy + nz * sz) / norm, 0.0, 1.0)
    # Seen on a sphere, a map is squashed towards the edge.
    lon = np.where(inside, du / np.maximum(nz, 0.15), 0.0)
    lat = np.where(inside, dv, 0.0)
    land_noise = art.noise((tag, "land"), cells=5.0, octaves=5)
    shifted = np.clip(0.5 + 0.18 * lon, 0.0, 1.0)
    land = smoothstep(0.56, 0.60, land_noise * 0.75 + 0.25 * art.noise((tag, "shape"), cells=2.0, octaves=2)) * inside
    surface = art.flat(PAL["ocean"]) * (0.80 + 0.30 * np.clip(1.0 - np.abs(lat), 0, 1))[:, :, None]
    surface = surface * (1.0 - land[:, :, None]) + art.flat(PAL["land"]) * land[:, :, None]
    dry = smoothstep(0.70, 0.80, art.noise((tag, "dry"), cells=4.0, octaves=3)) * land
    surface = surface * (1.0 - 0.6 * dry[:, :, None]) + art.flat(PAL["desert"]) * (0.6 * dry[:, :, None])
    # A little ice at the pole, which is tipped away from the eye: most of
    # the view is of the temperate world.
    ice = smoothstep(0.95, 0.985, np.abs(lat)) * inside * 0.7
    surface = surface * (1.0 - ice[:, :, None]) + art.flat(PAL["cloud"]) * ice[:, :, None]
    # Cloud bands, long along the lines of latitude.
    cloud = art.noise((tag, "cloud"), cells=7.0, octaves=5, stretch=3.0)
    cloud = smoothstep(0.55, 0.75, cloud * (0.75 + 0.25 * np.cos(lat * 9.0 + shifted * 2.0))) * inside
    surface = surface * (1.0 - 0.85 * cloud[:, :, None]) + art.flat(PAL["cloud"]) * (0.85 * cloud[:, :, None])
    # Day and night.
    day = 0.10 + 0.95 * lit ** 0.8
    shaded = surface * day[:, :, None]
    night = smoothstep(0.08, 0.0, lit) * inside
    cities = smoothstep(0.80, 0.86, art.noise((tag, "cities"), cells=40.0, octaves=2)) * land * night
    layer_paint = shaded + art.flat(PAL["city"]) * (cities * 0.8)[:, :, None]
    art.put(layer, disc, layer_paint)
    # The air: a thin bright line on the lit edge, a soft glow outside it.
    edge = np.clip(1.0 - np.abs(np.sqrt(d2) - 1.0) / 0.035, 0.0, 1.0) ** 2
    rim_lit = np.clip((du * sx + dv * sy) / math.sqrt(sx * sx + sy * sy) + 0.35, 0.0, 1.0)
    art.light(layer, edge * rim_lit, PAL["air"], 0.9)
    outside = np.clip(1.0 - (np.sqrt(d2) - 1.0) / 0.10, 0.0, 1.0) ** 2 * (d2 >= 1.0)
    art.light(layer, outside * rim_lit, PAL["air"], 0.45)


def deep_space(art: Art, tag: str) -> np.ndarray:
    """The black behind everything: a faint band of the galaxy and stars."""
    p = PAL
    layer = art.opaque(art.ramp([(0.0, p["space_high"]), (0.5, p["space"]), (1.0, p["space_high"])]))
    band = np.clip(1.0 - np.abs((art.v - 0.30) - (art.u - 0.5) * 0.35) / 0.16, 0.0, 1.0) ** 2
    art.light(layer, band * art.noise((tag, "milky"), cells=6.0, octaves=5), p["nebula"], 0.35)
    stars(art, layer, 900, (236, 240, 255), v_max=1.0, tag=(tag, "stars"))
    return layer


# ---------------------------------------------------------------------------
# Inside a deck
# ---------------------------------------------------------------------------

#: The viewports of the far wall: their top and bottom, in `v`.
PORT_TOP, PORT_BOTTOM = 0.36, 0.53


def orbital(layer_key: str, art: Art) -> np.ndarray:
    """Inside a deck of the station: plates of steel between hull ribs, long
    viewports with the planet in them, and lockers and cable trays in front."""
    p = PAL
    if layer_key == "sky":
        layer = deep_space(art, "deck")
        planet(art, layer, 0.58, 1.12, 0.66, tag="deck planet")
        # The far wall, round the viewports.
        wall, pen = art.drawing()
        pen.rect(0.0, 0.0, 1.0, PORT_TOP)
        pen.rect(0.0, PORT_BOTTOM, 1.0, 1.0)
        for i in range(9):
            u = i / 8.0
            pen.rect(u - 0.018, PORT_TOP - 0.01, u + 0.018, PORT_BOTTOM + 0.01)
        mask = art.mask_of(wall)
        paint = art.ramp([(0.0, p["wall_dark"]), (0.30, p["wall"]), (0.60, p["wall"]), (1.0, p["wall_dark"])])
        paint = paint * (0.92 + 0.12 * art.noise("plate grain", cells=10.0, octaves=3))[:, :, None]
        art.put(layer, mask, paint)
        # The seams of the plates and their rivets.
        seams, pen = art.drawing()
        for v in (0.12, 0.24, 0.31, 0.58, 0.66, 0.78, 0.90):
            pen.rect(0.0, v, 1.0, v + 0.003)
        for i in range(17):
            pen.rect(i / 16.0, 0.0, i / 16.0 + 0.003, PORT_TOP)
            pen.rect(i / 16.0, PORT_BOTTOM, i / 16.0 + 0.003, 1.0)
        art.shade(layer, art.mask_of(seams, blur=0.4) * mask, 0.35)
        # A light strip over the ports, and its light on the wall.
        strip, pen = art.drawing()
        pen.rect(0.0, PORT_TOP - 0.035, 1.0, PORT_TOP - 0.028)
        art.put(layer, art.mask_of(strip), mix(p["cyan"], p["steel_light"], 0.5))
        art.light(layer, art.band(PORT_TOP - 0.06, 0.06, 1.5) * mask, p["cyan"], 0.14)
        # The frames of the ports catch the planet's light from below.
        frames, pen = art.drawing()
        pen.rect(0.0, PORT_BOTTOM - 0.002, 1.0, PORT_BOTTOM + 0.008)
        art.light(layer, art.mask_of(frames, blur=0.6), p["air"], 0.35)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        # The hull ribs: posts that frame each viewport, and pipe runs.
        image, pen = art.drawing()
        lights, light_pen = art.drawing()
        for i in range(9):
            u = i / 8.0
            pen.rect(u - 0.011, 0.0, u + 0.011, 1.0)
            pen.poly([(u - 0.011, PORT_TOP - 0.02), (u - 0.026, PORT_TOP - 0.06), (u + 0.026, PORT_TOP - 0.06), (u + 0.011, PORT_TOP - 0.02)])
            pen.poly([(u - 0.011, PORT_BOTTOM + 0.02), (u - 0.026, PORT_BOTTOM + 0.06), (u + 0.026, PORT_BOTTOM + 0.06), (u + 0.011, PORT_BOTTOM + 0.02)])
            light_pen.ellipse(u, PORT_BOTTOM + 0.13, 0.004)
        for v in (0.17, 0.20, 0.70):
            pen.rect(0.0, v, 1.0, v + 0.008)
        body = art.mask_of(image)
        layer = art.blank()
        art.put(layer, body, art.ramp([(0.0, p["rib"]), (0.5, scale(p["rib"], 1.25)), (1.0, p["rib"])]))
        art.light(layer, art.rim(body, 0.0, -0.004, 0.4) * body, p["air"], 0.28)
        art.light(layer, art.rim(body, 0.004, 0.0, 0.4) * body, p["steel_light"], 0.18)
        lamps(art, layer, [(i / 8.0, PORT_BOTTOM + 0.13, 0.004) for i in range(9)], p["amber"], halo=5.0, strength=0.9)
        return layer
    if layer_key == "near_background":
        # Lockers, crates and a cable tray: dark, low, with a cool edge.
        rng = art.rand("lockers")
        image, pen = art.drawing()
        lights, light_pen = art.drawing()
        u = -0.02
        while u < 1.02:
            w = rng.uniform(0.05, 0.11)
            top = HORIZON + rng.uniform(0.02, 0.08)
            kind = rng.choice(["locker", "crate", "tank"])
            if kind == "locker":
                pen.rect(u, top, u + w, 1.0)
                light_pen.rect(u + w * 0.15, top + 0.03, u + w * 0.3, top + 0.035, value=rng.randint(120, 220))
            elif kind == "crate":
                pen.rect(u, top + 0.05, u + w, 1.0)
                pen.rect(u + w * 0.1, top, u + w * 0.7, top + 0.05)
            else:
                pen.rect(u, top + w * 0.5, u + w, 1.0)
                pen.ellipse(u + w * 0.5, top + w * 0.5, w * 0.5, w * 0.5)
            u += w + rng.uniform(0.01, 0.05)
        # The tray of cables under the ceiling, and its hangers.
        pen.rect(0.0, 0.06, 1.0, 0.085)
        for k in range(12):
            pen.rect(k / 11.0 - 0.003, 0.0, k / 11.0 + 0.003, 0.07)
        body = art.mask_of(image)
        layer = art.blank()
        art.put(layer, body, art.ramp([(0.0, scale(p["wall_dark"], 0.8)), (1.0, scale(p["wall_dark"], 0.55))]))
        art.light(layer, art.rim(body, 0.0, 0.004, 0.4) * body, p["steel"], 0.35)
        art.light(layer, art.mask_of(lights, blur=0.5), p["cyan"], 0.8)
        haze(art, layer, p["wall"], 0.10, None)
        return layer
    layer = art.blank()
    # The light of the ports in the air of the deck.
    art.put(layer, art.band(0.47, 0.10, 1.5) * art.noise("air light", cells=3.0, octaves=3), p["air"], 0.07)
    art.put(layer, art.band(0.30, 0.04, 2.0), p["cyan"], 0.05)
    return layer


# ---------------------------------------------------------------------------
# Out in the trusses
# ---------------------------------------------------------------------------


def _lattice(pen, u0: float, v0: float, u1: float, v1: float, bays: int, width: float) -> None:
    """A truss beam from `(u0, v0)` to `(u1, v1)`: two chords and the zigzag
    of its web."""
    du, dv = u1 - u0, v1 - v0
    length = math.hypot(du, dv)
    nu, nv = -dv / length * width, du / length * width
    pen.line([(u0 + nu, v0 + nv), (u1 + nu, v1 + nv)], width * 0.16)
    pen.line([(u0 - nu, v0 - nv), (u1 - nu, v1 - nv)], width * 0.16)
    for k in range(bays):
        a, b = k / bays, (k + 1) / bays
        pa = (u0 + du * a + (nu if k % 2 else -nu), v0 + dv * a + (nv if k % 2 else -nv))
        pb = (u0 + du * b + (-nu if k % 2 else nu), v0 + dv * b + (-nv if k % 2 else nv))
        pen.line([pa, pb], width * 0.10)


def orbital_truss(layer_key: str, art: Art) -> np.ndarray:
    """Out in the open trusses of the station: the planet below, its day side
    to the left, the station's far ring over it, and the near lattice."""
    p = PAL
    if layer_key == "sky":
        layer = deep_space(art, "truss")
        # A small moon, high.
        disc, pen = art.drawing()
        pen.ellipse(0.80, 0.30, 0.022)
        moon_mask = art.mask_of(disc)
        art.put(layer, moon_mask, art.flat((196, 190, 180)) * (0.7 + 0.4 * art.noise("moon", cells=40.0, octaves=2))[:, :, None])
        art.shade(layer, art.spot(0.792, 0.296, 0.026, 0.6) * 0 + moon_mask * np.clip((art.u - 0.785) / 0.03, 0, 1), 0.7)
        planet(art, layer, 0.42, 1.18, 0.62, tag="truss planet")
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        # The far side of the station's ring: an arc of modules with lit
        # windows, and the running lights of a hauler on its way out.
        image, pen = art.drawing()
        lights, light_pen = art.drawing()
        panels, panel_pen = art.drawing()
        # A long spar with modules on it, far off and level: boxes of hull,
        # radiator fins and the dark blue of solar wings.
        spar_v = 0.37
        pen.rect(-0.05, spar_v - 0.004, 1.05, spar_v + 0.004)
        rng = art.rand("modules")
        u = -0.04
        while u < 1.04:
            kind = rng.choice(["module", "module", "wing", "tank"])
            if kind == "module":
                w, h = rng.uniform(0.04, 0.08), rng.uniform(0.020, 0.034)
                pen.rect(u, spar_v - h / 2, u + w, spar_v + h / 2)
                for k in range(int(w / 0.012)):
                    if rng.random() < 0.5:
                        light_pen.rect(u + 0.004 + k * 0.012, spar_v - 0.003, u + 0.009 + k * 0.012, spar_v + 0.001, value=rng.randint(120, 220))
            elif kind == "wing":
                w = rng.uniform(0.06, 0.10)
                panel_pen.rect(u, spar_v - 0.055, u + w, spar_v - 0.010)
                panel_pen.rect(u, spar_v + 0.010, u + w, spar_v + 0.055)
                pen.rect(u + w / 2 - 0.002, spar_v - 0.055, u + w / 2 + 0.002, spar_v + 0.055)
            else:
                w = rng.uniform(0.02, 0.03)
                pen.ellipse(u + w / 2, spar_v, w / 2, w * 0.9)
            u += w + rng.uniform(0.01, 0.04)
        body = art.mask_of(image)
        layer = art.blank()
        art.put(layer, body, mix(p["steel"], p["space_high"], 0.35))
        art.light(layer, art.rim(body, 0.003, 0.003, 0.3) * body, p["air"], 0.35)
        wings = art.mask_of(panels)
        art.put(layer, wings, (34, 52, 96))
        grid = (np.abs(((art.u * 160.0) % 1.0) - 0.5) < 0.08) | (np.abs(((art.v * 160.0) % 1.0) - 0.5) < 0.08)
        art.shade(layer, wings * grid, 0.45)
        art.light(layer, wings * art.band(spar_v - 0.04, 0.03, 1.0), p["air"], 0.20)
        art.light(layer, art.mask_of(lights, blur=0.4), p["city"], 0.9)
        # A hauler: a small long hull with its drive light.
        ship, pen = art.drawing()
        pen.poly([(0.17, 0.41), (0.25, 0.405), (0.26, 0.415), (0.17, 0.42)])
        art.put(layer, art.mask_of(ship), scale(p["steel"], 0.9))
        art.light(layer, art.spot(0.165, 0.415, 0.02, 1.4), p["cyan"], 0.9)
        lamps(art, layer, [(0.255, 0.41, 0.002), (0.20, 0.404, 0.0015)], p["amber"], halo=4.0, strength=0.9)
        return layer
    if layer_key == "near_background":
        # The near truss: one beam high, one low, and posts between them.
        image, pen = art.drawing()
        _lattice(pen, -0.05, 0.29, 1.05, 0.25, 14, 0.026)
        _lattice(pen, -0.05, 0.74, 1.05, 0.77, 14, 0.030)
        for u in (0.12, 0.47, 0.83):
            _lattice(pen, u, 0.26, u + 0.01, 0.76, 7, 0.016)
        body = art.mask_of(image)
        layer = art.blank()
        art.put(layer, body, art.ramp([(0.0, scale(p["rib"], 0.9)), (1.0, scale(p["rib"], 0.6))]))
        # Planetshine from below, starlight on the top.
        art.light(layer, art.rim(body, 0.0, -0.003, 0.4) * body, p["air"], 0.45)
        art.light(layer, art.rim(body, 0.0, 0.003, 0.4) * body, p["steel_light"], 0.20)
        lamps(art, layer, [(u + 0.005, 0.27, 0.0035) for u in (0.12, 0.47, 0.83)], p["amber"], halo=5.0, strength=0.9)
        return layer
    layer = art.blank()
    # The glow of the planet's air in the glass of the dome.
    art.put(layer, art.band(0.78, 0.18, 1.6), p["air"], 0.10)
    art.put(layer, art.spot(0.2, 0.7, 0.3, 2.0, squash=1.6), p["cloud"], 0.05)
    return layer


__all__ = ["PAL", "orbital", "orbital_truss", "planet"]
