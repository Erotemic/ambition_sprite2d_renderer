"""The scene of the port of the pirate dimension.

A harbour town in the late afternoon. The sun is low and warm (no disc: its
light only), and heap clouds catch it. Far out on the sea a headland has a
lighthouse, and a skyship goes over it with its sails set. Behind the quay
the town climbs a hill: houses of timber and plaster with red and ochre
roofs. Ships lie at the quay with their sails furled, and gulls go over.
This is the day of the pirate dimension; `cove` is its night.
"""

from __future__ import annotations

import numpy as np

from .artkit import Art, Pen, mix, scale, smoothstep
from .parts import HORIZON, cumulus, fog, haze, lamps, shafts, solid

PORT = {
    "top": (64, 126, 186),
    "mid": (128, 178, 212),
    "warm": (252, 214, 158),
    "sun": (255, 236, 196),
    "sea": (46, 116, 140),
    "deep": (26, 74, 100),
    "glint": (255, 240, 206),
    "cloud": (255, 238, 214),
    "cloud_shade": (176, 160, 176),
    "land": (96, 124, 120),
    "plaster": (236, 216, 178),
    "ochre": (214, 168, 96),
    "roof": (176, 82, 56),
    "roof_ochre": (196, 126, 64),
    "timber": (92, 62, 44),
    "hull": (82, 54, 38),
    "sail": (240, 228, 204),
    "near": (58, 46, 44),
    "near_light": (150, 112, 82),
    "lamp": (255, 200, 120),
}

#: Where the light of the low sun is (no disc is drawn).
SUN = (0.74, HORIZON - 0.15)


def _ship(pen: Pen, rig: Pen, u: float, water: float, size: float, facing: float = 1.0, furled: bool = True, sails: Pen | None = None) -> None:
    """A ship that lies at `water`, `size` long, its bow toward `facing`.
    The hull and masts go on `pen`, the rigging on `rig`, and set sails on
    `sails` (furled sails are a thick line on the yard)."""
    f = facing
    half = size * 0.5
    deck = water - size * 0.12
    bow, stern = u + f * half, u - f * half
    pen.poly([(stern, deck - size * 0.06), (stern + f * size * 0.12, deck - size * 0.06), (stern + f * size * 0.14, deck),
              (bow - f * size * 0.06, deck), (bow, deck - size * 0.03), (bow - f * size * 0.10, water + size * 0.01),
              (stern + f * size * 0.08, water + size * 0.01)])
    # The bowsprit.
    rig.line([(bow - f * size * 0.02, deck - size * 0.02), (bow + f * size * 0.22, deck - size * 0.12)], size * 0.012)
    masts = ((-0.22, 0.95), (0.05, 1.12), (0.30, 0.86))
    for k, h in masts:
        mu = u + f * k * size
        top = deck - h * size
        pen.rect(mu - size * 0.007, top, mu + size * 0.007, deck)
        for j in range(3):
            yard = top + size * (0.10 + j * 0.24) * h
            wide = size * (0.10 + j * 0.035)
            if furled or sails is None:
                pen.rect(mu - wide, yard - size * 0.008, mu + wide, yard + size * 0.008)
            else:
                pen.rect(mu - wide, yard - size * 0.004, mu + wide, yard + size * 0.004)
                drop = size * 0.20 * h
                sails.poly([(mu - wide, yard), (mu + wide, yard), (mu + wide * 1.05, yard + drop), (mu - wide * 1.05, yard + drop)])
        # Stays from the mast top to the deck ends.
        rig.line([(mu, top), (bow, deck - size * 0.02)], size * 0.004)
        rig.line([(mu, top), (stern, deck - size * 0.06)], size * 0.004)


def _house(walls: Pen, roofs: Pen, timber: Pen, windows: Pen, rng, u: float, foot: float, w: float, h: float) -> None:
    """A town house of timber and plaster: a wall, a roof of tiles that
    overhangs it, beams across the plaster, and small windows."""
    top = foot - h
    walls.rect(u, top, u + w, foot + 0.01)
    kind = rng.choice(["gable", "gable", "hip", "lean"])
    over = w * 0.08
    if kind == "gable":
        roofs.poly([(u - over, top + 0.002), (u + w + over, top + 0.002), (u + w * 0.5, top - w * 0.42)])
    elif kind == "hip":
        roofs.poly([(u - over, top + 0.002), (u + w + over, top + 0.002), (u + w * 0.78, top - w * 0.26), (u + w * 0.22, top - w * 0.26)])
    else:
        roofs.poly([(u - over, top + 0.002), (u + w + over, top + 0.002), (u + w + over, top - w * 0.30)])
    # Beams: a sill under each floor, and posts at the corners.
    floors = max(1, int(round(h / (w * 0.45))))
    for k in range(floors + 1):
        v = top + h * k / floors
        timber.rect(u, v - h * 0.012, u + w, v + h * 0.012)
    timber.rect(u, top, u + w * 0.05, foot)
    timber.rect(u + w * 0.95, top, u + w, foot)
    for k in range(floors):
        v0 = top + h * k / floors
        cols = max(1, int(round(w / (h / floors) * 0.9)))
        for c in range(cols):
            if rng.random() < 0.8:
                cu = u + (c + 0.5) * w / cols
                windows.rect(cu - w * 0.07, v0 + h / floors * 0.30, cu + w * 0.07, v0 + h / floors * 0.70)


def pirate_port(layer_key: str, art: Art) -> np.ndarray:
    p = PORT
    if layer_key == "sky":
        layer = art.opaque(art.ramp([(0.0, p["top"]), (0.30, p["mid"]), (HORIZON - 0.03, mix(p["mid"], p["warm"], 0.75)),
                                     (HORIZON - 0.002, p["warm"]), (HORIZON, mix(p["sea"], p["warm"], 0.35)), (0.70, p["sea"]), (1.0, p["deep"])]))
        # The light of the low sun, in the air and on the sea (no disc).
        art.light(layer, art.spot(*SUN, 0.42, 1.8, squash=1.3), p["sun"], 0.55)
        clouds = cumulus(art, "heap clouds", 0.40, 0.11, 3.2, 0.40, p["cloud"], mix(p["cloud_shade"], p["mid"], 0.3))
        clouds[:, :, 3] *= (art.v < HORIZON - 0.03) * 0.92
        layer = art.over(layer, clouds)
        # The far headland and its lighthouse, in the haze of the sea air.
        land, line = art.ridge("headland", HORIZON - 0.015, 0.03, cells=2.0, octaves=4, sharp=0.3)
        land = land * smoothstep(0.62, 0.70, art.u) * (art.v < HORIZON + 0.002)
        image, pen = art.drawing()
        lu = 0.86
        lv = float(line[int(lu * art.n)])
        pen.poly([(lu - 0.006, lv), (lu + 0.006, lv), (lu + 0.004, lv - 0.07), (lu - 0.004, lv - 0.07)])
        pen.rect(lu - 0.007, lv - 0.078, lu + 0.007, lv - 0.07)
        pen.poly([(lu - 0.006, lv - 0.078), (lu + 0.006, lv - 0.078), (lu, lv - 0.092)])
        far = np.maximum(land, art.mask_of(image))
        art.put(layer, far, mix(p["land"], p["warm"], 0.45))
        stripes = art.mask_of(image) * (np.sin(art.v * art.n / 22.0) > 0.4)
        art.put(layer, stripes, mix((190, 70, 60), p["warm"], 0.45), 0.8)
        # The skyship, high over the headland, its sails set.
        ship, ship_pen = art.drawing()
        rig, rig_pen = art.drawing()
        sails, sail_pen = art.drawing()
        su, sv, size = 0.30, 0.42, 0.075
        _ship(ship_pen, rig_pen, su, sv, size, facing=-1.0, furled=False, sails=sail_pen)
        # Its wings: two long fins of sail on spars, and the keel's fin.
        ship_pen.line([(su - 0.01, sv - 0.004), (su + 0.045, sv + 0.004)], 0.0015)
        sail_pen.poly([(su - 0.005, sv - 0.004), (su + 0.045, sv + 0.004), (su + 0.035, sv + 0.016), (su + 0.002, sv + 0.010)])
        ship_pen.poly([(su - 0.01, sv + 0.008), (su + 0.02, sv + 0.008), (su + 0.006, sv + 0.03)])
        tone = mix(p["mid"], p["warm"], 0.4)
        art.put(layer, art.mask_of(ship, blur=0.3), mix(p["hull"], tone, 0.55))
        art.put(layer, art.mask_of(rig, blur=0.3), mix(p["hull"], tone, 0.62), 0.8)
        art.put(layer, art.mask_of(sails, blur=0.3), mix(mix(p["sail"], p["ochre"], 0.2), tone, 0.35))
        art.light(layer, art.mask_of(sails, blur=0.3) * smoothstep(su - 0.05, su + 0.05, art.u), p["sun"], 0.35)
        # Gulls: small curved marks, far and near.
        rng = art.rand("gulls")
        gulls, gull_pen = art.drawing()
        for _ in range(9):
            u, v, s = rng.uniform(0.05, 0.95), rng.uniform(0.30, 0.52), rng.uniform(0.005, 0.011)
            gull_pen.line([(u - s, v - s * 0.3), (u - s * 0.4, v - s * 0.5), (u, v)], s * 0.22)
            gull_pen.line([(u, v), (u + s * 0.4, v - s * 0.5), (u + s, v - s * 0.3)], s * 0.22)
        art.put(layer, art.mask_of(gulls, blur=0.2), mix((60, 70, 86), p["mid"], 0.25), 0.8)
        # The sea: the sun on it in short lines, more of them in its path.
        below = smoothstep(HORIZON, HORIZON + 0.004, art.v)
        ripples = art.noise("ripples", cells=70.0, octaves=2, stretch=7.0)
        depth = np.clip((art.v - HORIZON) / 0.3, 0.0, 1.0)
        path = np.clip(1.0 - np.abs(art.u - SUN[0]) / (0.05 + depth * 0.30), 0.0, 1.0)
        art.light(layer, below * path * smoothstep(0.50, 0.70, ripples) * (1.0 - depth) ** 0.5, p["glint"], 0.70)
        art.light(layer, below * smoothstep(0.64, 0.80, ripples) * (1.0 - depth), p["warm"], 0.18)
        art.grain(layer, "grain")
        return layer
    if layer_key == "far_backplate":
        rng = art.rand("hill town")
        # The hill climbs to the left: the ground of the town.
        slope = HORIZON + 0.035 - np.clip(0.68 - art.u, 0.0, 1.0) * 0.30
        ground = np.clip((art.v - slope) * art.n + 0.5, 0.0, 1.0)
        walls, wall_pen = art.drawing()
        ochre, ochre_pen = art.drawing()
        roofs, roof_pen = art.drawing()
        roofs2, roof2_pen = art.drawing()
        beams, beam_pen = art.drawing()
        wins, win_pen = art.drawing()
        u = -0.02
        while u < 0.74:
            w = rng.uniform(0.030, 0.050)
            foot = HORIZON + 0.035 - max(0.0, 0.68 - (u + w * 0.5)) * 0.30 + 0.012
            h = rng.uniform(0.028, 0.050)
            _house(rng.choice([wall_pen, ochre_pen]), rng.choice([roof_pen, roof_pen, roof2_pen]), beam_pen, win_pen, rng, u, foot, w, h)
            u += w + rng.uniform(-0.006, 0.004)
        # A second row higher on the hill, behind the first.
        u = -0.02
        while u < 0.5:
            w = rng.uniform(0.025, 0.04)
            foot = HORIZON + 0.035 - max(0.0, 0.68 - (u + w * 0.5)) * 0.30 - 0.03
            h = rng.uniform(0.03, 0.05)
            _house(rng.choice([wall_pen, ochre_pen]), rng.choice([roof_pen, roof2_pen]), beam_pen, win_pen, rng, u, foot, w, h)
            u += w + rng.uniform(0.0, 0.01)
        # The harbour wall, and the masts of the ships in the harbour.
        quay, quay_pen = art.drawing()
        quay_pen.rect(0.0, HORIZON + 0.03, 1.0, 1.0)
        masts, mast_pen = art.drawing()
        for k, mu in enumerate((0.70, 0.78, 0.83, 0.92, 0.97)):
            h = rng.uniform(0.12, 0.18)
            mast_pen.rect(mu - 0.0016, HORIZON + 0.03 - h, mu + 0.0016, HORIZON + 0.03)
            for j in range(3):
                yv = HORIZON + 0.03 - h + h * (0.12 + j * 0.24)
                wide = 0.014 + j * 0.004
                mast_pen.rect(mu - wide, yv - 0.0018, mu + wide, yv + 0.0018)
            mast_pen.line([(mu, HORIZON + 0.03 - h), (mu + 0.04, HORIZON + 0.03)], 0.0012)
            mast_pen.line([(mu, HORIZON + 0.03 - h), (mu - 0.035, HORIZON + 0.03)], 0.0012)
        body = np.clip(np.maximum.reduce([ground, art.mask_of(walls), art.mask_of(ochre), art.mask_of(roofs), art.mask_of(roofs2), art.mask_of(quay)]), 0, 1)
        sky_air = mix(p["mid"], p["warm"], 0.55)
        layer = solid(art, ground, mix((132, 128, 84), sky_air, 0.35), mix((104, 100, 70), sky_air, 0.28), HORIZON - 0.2, HORIZON + 0.05, "hill grass", 0.08)
        art.put(layer, art.mask_of(walls), mix(p["plaster"], sky_air, 0.30))
        art.put(layer, art.mask_of(ochre), mix(p["ochre"], sky_air, 0.30))
        art.put(layer, art.mask_of(beams) * np.maximum(art.mask_of(walls), art.mask_of(ochre)), mix(p["timber"], sky_air, 0.35))
        art.put(layer, art.mask_of(wins) * np.maximum(art.mask_of(walls), art.mask_of(ochre)), mix((70, 76, 90), sky_air, 0.35))
        art.put(layer, art.mask_of(roofs), mix(p["roof"], sky_air, 0.30))
        art.put(layer, art.mask_of(roofs2), mix(p["roof_ochre"], sky_air, 0.30))
        art.put(layer, art.mask_of(quay), mix((150, 140, 124), sky_air, 0.35))
        art.put(layer, art.mask_of(masts, blur=0.2), mix(p["hull"], sky_air, 0.40))
        # The sun is to the right: the right edge of each thing is lit.
        lit = art.rim(body, -0.003, 0.0, 0.5) * body
        art.light(layer, lit, p["sun"], 0.40)
        haze(art, layer, sky_air, 0.16, HORIZON + 0.05)
        return layer
    if layer_key == "near_background":
        image, pen = art.drawing()
        rig, rig_pen = art.drawing()
        wins, win_pen = art.drawing()
        # The quay along the bottom.
        pen.rect(0.0, 0.70, 1.0, 1.0)
        # A warehouse at the left: a tall front of timber with a hoist beam.
        pen.rect(-0.01, 0.30, 0.17, 0.71)
        pen.poly([(-0.02, 0.305), (0.18, 0.305), (0.08, 0.22)])
        pen.rect(0.13, 0.34, 0.215, 0.35)
        rig_pen.line([(0.205, 0.35), (0.205, 0.52)], 0.0016)
        pen.rect(0.193, 0.52, 0.217, 0.545)
        for v in (0.40, 0.50, 0.60):
            for u in (0.025, 0.075, 0.125):
                win_pen.rect(u - 0.012, v - 0.022, u + 0.012, v + 0.022)
        # A harbour crane in the middle distance, its jib over the water.
        pen.poly([(0.40, 0.71), (0.43, 0.71), (0.423, 0.44), (0.407, 0.44)])
        rig_pen.line([(0.415, 0.45), (0.56, 0.36)], 0.006)
        rig_pen.line([(0.415, 0.45), (0.56, 0.36), (0.415, 0.56)], 0.0016)
        rig_pen.line([(0.55, 0.365), (0.55, 0.48)], 0.0012)
        pen.rect(0.538, 0.48, 0.562, 0.505)
        # A ship at the quay on the right, its masts up out of the view.
        _ship(pen, rig_pen, 0.82, 0.71, 0.36, facing=-1.0)
        # Bollards and a lamp post along the quay.
        lights = []
        for u in (0.27, 0.62):
            pen.rect(u - 0.0025, 0.62, u + 0.0025, 0.70)
            pen.rect(u - 0.009, 0.605, u + 0.009, 0.625)
            lights.append((u, 0.615, 0.005))
        for u in (0.33, 0.50, 0.68):
            pen.rect(u - 0.007, 0.685, u + 0.007, 0.70)
            pen.ellipse(u, 0.685, 0.009, 0.004)
        mask = np.clip(art.mask_of(image), 0, 1)
        layer = solid(art, mask, mix(p["near"], p["near_light"], 0.25), scale(p["near"], 0.75), 0.25, 0.75, "quay timber", 0.12)
        art.put(layer, art.mask_of(rig, blur=0.2), scale(p["near"], 0.9))
        art.put(layer, art.mask_of(wins) * mask, mix(p["lamp"], p["near"], 0.55))
        body = np.maximum(mask, art.mask_of(rig))
        art.light(layer, art.rim(body, -0.003, 0.002, 0.4) * body, p["sun"], 0.40)
        art.shade(layer, art.rim(mask, 0.005, -0.003, 1.2) * mask, 0.22)
        lamps(art, layer, lights, p["lamp"], halo=6.0, strength=0.8)
        haze(art, layer, mix(p["sea"], p["warm"], 0.4), 0.06, None)
        return layer
    # The air: warm light through the haze, and spray low over the water.
    layer = art.blank()
    art.put(layer, shafts(art, "evening shafts", 4, -0.14, 0.0, 0.8, 0.05), p["sun"], 0.10)
    art.put(layer, fog(art, "sea haze", 0.62, 0.06), mix(p["warm"], p["mid"], 0.4), 0.14)
    return layer
