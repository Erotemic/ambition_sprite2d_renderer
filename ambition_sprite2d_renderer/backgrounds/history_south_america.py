"""The scenes of the History dimension: South America.

The History dimension is a grid. East is later, and each floor is a region
of the world. These rooms show the peoples of South America: the first
farmers of the high Andes, and the first cities of the coast of Peru. They
use the same sepia of an old textbook and the same rules as
`history_eras.py` and `history_origins.py`. The people of these places show
skill, invention and a long history of their own; nothing here is a joke on
them.

- ``history_andes`` (the high Andes near Lake Titicaca, 8000-2000 BCE). A
  cold, bright morning at about 3,900 metres. The sky is thin and of a deep
  blue. Far off, a long range of snow peaks stands over the blue of a great
  lake (Titicaca), and two low islands are in the lake. Below the eye is a
  wide plain of tawny puna grass. Near its shore, people farm small fields
  in a patchwork: each field has a wall of stones round it, and the fields
  are green with potatoes, or red and gold with quinoa, or brown and new.
  On the slope at the right are two round houses of stone with roofs of
  thatch, and a little smoke goes up from one of them. Grey rocks and
  tussocks of ichu grass stand at the sides. No llamas are in the scene:
  people tamed them later than the first fields, and they are a creature
  of the room.
- ``history_supe`` (Caral, in the Supe valley of Peru, about 2600 BCE). A
  hazy day on the coast. A narrow green valley of fields (cotton, squash and
  beans) runs along its river through a bare brown desert, to the grey
  Pacific far off at the left, under a low fog of the sea (the garua). Brown
  foothills stand behind. On a terrace of the desert above the valley stand
  the stepped platform pyramids of the city, of grey-tan stone, each with a
  stair up its front; a round sunken plaza is in front of the largest one.
  The city has no walls. Huarango trees and dry scrub stand at the sides.
  No pottery is drawn: Caral is older than pottery in Peru.

The bright detail is far off or at the edges, and the middle of each near
layer is calm, so the play in front of it reads. The things that drift in the
air are the room's motes (`terrain/motes.py`), not part of these pictures.
"""

from __future__ import annotations

import numpy as np

from .artkit import Art, Pen, mix, scale, smoothstep
from .history_eras import REST_BOTTOM, _air, _at, _heaps, _plume, _sun, _textbook
from .history_origins import _arch, _land
from .parts import HORIZON, fog, haze, shafts, solid

# ---------------------------------------------------------------------------
# The high Andes: the first fields over Lake Titicaca
# ---------------------------------------------------------------------------


ANDES = {
    "top": (34, 66, 138),
    "mid": (104, 148, 204),
    "low": (214, 224, 232),
    "glow": (255, 238, 204),
    "sun": (255, 252, 238),
    "cloud": (248, 248, 246),
    "cloud_shadow": (176, 186, 206),
    "snow": (246, 248, 252),
    "snow_shade": (170, 186, 216),
    "peak": (96, 100, 124),
    "lake": (40, 92, 164),
    "lake_light": (176, 210, 236),
    "reeds": (150, 146, 78),
    "puna": (196, 158, 94),
    "puna_light": (228, 198, 132),
    "puna_dark": (140, 108, 68),
    "earth": (124, 86, 60),
    "potato": (104, 132, 70),
    "quinoa_red": (176, 66, 54),
    "quinoa_gold": (218, 168, 66),
    "wall": (156, 148, 136),
    "wall_light": (206, 200, 188),
    "thatch": (200, 170, 104),
    "smoke": (214, 216, 222),
    "far": (190, 198, 210),
    "near": (42, 36, 32),
    "near_light": (132, 116, 98),
    "rock": (110, 106, 102),
    "rock_light": (176, 170, 160),
    "ichu": (196, 164, 98),
    "ichu_light": (232, 206, 146),
}


def _round_house(walls: Pen, roof: Pen, door: Pen, u: float, v: float, w: float, h: float) -> None:
    """A round house of the high plain: a low wall of stones laid in rings,
    a tall cone of thatch on it with a rounded tip, and a low dark door.
    The wall is a little wider at its foot."""
    walls.poly([(u - w * 1.04, v), (u + w * 1.04, v), (u + w, v - h), (u - w, v - h)])
    roof.poly([(u - w * 1.22, v - h * 0.86), (u - w * 0.20, v - h * 2.55), (u + w * 0.20, v - h * 2.55), (u + w * 1.22, v - h * 0.86)])
    roof.ellipse(u, v - h * 2.50, w * 0.22, h * 0.14)
    door.poly([(u - w * 0.20, v), (u + w * 0.20, v), (u + w * 0.16, v - h * 0.72), (u - w * 0.16, v - h * 0.72)])


def _tussock(pen: Pen, rng, u: float, v: float, h: float, blades: int = 9) -> None:
    """A tussock of ichu grass: a dense clump of thin, stiff blades that fan
    up and out from one base and bend a little at their tips."""
    for k in range(blades):
        t = (k + 0.5) / blades - 0.5
        lean = t * h * 1.1 + rng.uniform(-0.15, 0.15) * h
        tip = (u + lean, v - h * (1.0 - abs(t) * 0.7) * rng.uniform(0.85, 1.05))
        pen.line(_arch((u + t * h * 0.12, v), (u + lean * 0.3, v - h * 0.6), tip, 6), max(0.0008, h * 0.022))


def _boulder(pen: Pen, rng, u: float, v: float, w: float, h: float) -> None:
    """A grey boulder of the puna, broken into flat faces."""
    pts = [(u - w, v), (u - w * rng.uniform(0.85, 1.0), v - h * rng.uniform(0.45, 0.6)), (u - w * rng.uniform(0.4, 0.6), v - h * rng.uniform(0.9, 1.0)),
           (u + w * rng.uniform(0.0, 0.3), v - h), (u + w * rng.uniform(0.7, 0.9), v - h * rng.uniform(0.6, 0.8)), (u + w, v - h * rng.uniform(0.1, 0.3)), (u + w, v)]
    pen.poly(pts)


def history_andes(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = ANDES
    sun_at = (0.20, 0.30)
    shore_v = HORIZON - 0.004
    if layer_key == "sky":
        # The thin air of the high plain: a deep blue at the top that is
        # pale only near the far range.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.80)), (0.22, p["top"]), (0.44, p["mid"]), (shore_v - 0.02, p["low"]),
                                 (shore_v, p["lake"]), (1.0, p["lake"])]))
        _sun(a, layer, *sun_at, 0.020, p["sun"], p["glow"], 0.55)
        _heaps(a, layer, "andes heaps", ((0.64, 0.43, 0.05, 0.035), (0.90, 0.46, 0.04, 0.025)), p["cloud"], p["cloud_shadow"], 0.70)
        # The far range: a long line of snow peaks beyond the lake. Each peak
        # is white above the snow line and blue-grey rock below it, lit on
        # the side to the sun at the left.
        for k, (base, amp, cells, sharp, pale) in enumerate(((shore_v - 0.060, 0.045, 7.0, 0.85, 0.55), (shore_v - 0.030, 0.026, 9.0, 0.75, 0.30))):
            mask, line = a.ridge(("andes range", k), base, amp, cells=cells, octaves=5, sharp=sharp)
            mask = mask * (a.v < shore_v + 0.001)
            rock = mix(p["peak"], p["low"], pale)
            a.put(layer, mask, a.ramp([(0.0, rock), (base, rock), (shore_v, mix(rock, p["low"], 0.45)), (1.0, rock)]))
            snow_line = base + amp * (0.15 - 0.5 * k) + (a.noise(("andes snow line", k), cells=40.0, octaves=3) - 0.5) * 0.020
            snow = mask * smoothstep(snow_line + 0.002, snow_line - 0.002, a.v)
            a.put(layer, snow, mix(p["snow_shade"], p["low"], pale * 0.6))
            # The sun is at the left: the faces that look to the left are lit.
            lit = np.clip(a.rim(mask, 0.012, 0.0, 1.5) * 1.6, 0.0, 1.0)
            ribs = smoothstep(0.45, 0.70, a.noise(("andes ribs", k), cells=60.0, octaves=2, stretch=0.25))
            a.put(layer, snow * np.maximum(lit, ribs * 0.6), mix(p["snow"], p["glow"], 0.15), 0.95)
            a.light(layer, (mask - snow).clip(0.0, 1.0) * lit, p["glow"], 0.25)
            a.tint(layer, mask * fog(a, ("andes range mist", k), shore_v - 0.006, 0.014, 3.0), p["low"], 0.55)
        # The lake: deep blue, lighter far off where it shows the sky, with
        # long lines of light on it, and two low islands.
        water = (a.v >= shore_v).astype(np.float32)
        a.put(layer, water * smoothstep(shore_v + 0.05, shore_v, a.v), mix(p["lake"], p["lake_light"], 0.45), 0.8)
        lines = smoothstep(0.62, 0.80, a.noise("andes lake lines", cells=60.0, octaves=2, stretch=14.0))
        a.light(layer, water * lines * smoothstep(shore_v + 0.10, shore_v + 0.005, a.v), p["lake_light"], 0.45)
        glints = smoothstep(0.66, 0.84, a.noise("andes glints", cells=90.0, octaves=2, stretch=6.0))
        a.light(layer, water * glints * a.spot(sun_at[0], shore_v + 0.03, 0.22, 1.0, squash=1.6), (255, 255, 250), 0.6)
        islands, island_pen = a.drawing()
        for u, w, h in ((0.36, 0.060, 0.008), (0.52, 0.026, 0.005)):
            island_pen.poly([(u - w, shore_v + 0.012), (u - w * 0.6, shore_v + 0.012 - h * 0.6), (u - w * 0.1, shore_v + 0.012 - h), (u + w * 0.5, shore_v + 0.012 - h * 0.7),
                             (u + w, shore_v + 0.012)])
        island = a.mask_of(islands)
        a.put(layer, island, mix(p["puna_dark"], p["far"], 0.45))
        a.light(layer, a.rim(island, 0.004, 0.002, 0.3) * island, p["glow"], 0.35)
        _textbook(a, layer, 0.07)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far andes")
        # The near shore of the lake, and the slope of the hill at the right
        # that rises from the plain.
        _, plain = a.ridge("andes shore", shore_v + 0.030, 0.006, cells=4.0, octaves=3)
        _, hill = a.ridge("andes hill", HORIZON - 0.050, 0.020, cells=3.0, octaves=5, sharp=0.4)
        rise = smoothstep(0.62, 0.94, a.u[0])
        top = plain + (hill - plain) * rise
        land = _land(a, top)
        fields = {key: a.drawing() for key in ("potato", "quinoa_red", "quinoa_gold", "earth", "puna")}
        walls, wall_pen = a.drawing()
        reeds, reed_pen = a.drawing()
        house_walls, house_wall_pen = a.drawing()
        roofs, roof_pen = a.drawing()
        doors, door_pen = a.drawing()
        tufts, tuft_pen = a.drawing()
        # The reeds of the shore: a fringe of totora along the water.
        for _ in range(500):
            u = rng.uniform(0.0, 0.78)
            v = _at(top, u) + 0.001
            h = rng.uniform(0.003, 0.007)
            reed_pen.line([(u, v), (u + rng.uniform(-0.001, 0.001), v - h)], 0.0012)
        # The fields: a patchwork of small plots, each with its wall of
        # stones, deeper toward the eye. The rows follow the swell of the
        # ground, so no two plots are quite square. Most plots are near the
        # shore; on the slope at the right they get fewer and the puna takes
        # over.
        v, gap = HORIZON + 0.034, 0.005
        while v < 1.0:
            x = rng.uniform(-0.06, 0.0)
            bend = rng.uniform(0.0, 6.0)
            while x < 1.0:
                length = rng.uniform(0.025, 0.07) * (1.0 + (v - HORIZON) * 4.0)
                wild = smoothstep(0.55, 0.85, x)
                key = rng.choices(("potato", "quinoa_red", "quinoa_gold", "earth", "puna"), (5, 1, 2, 3, 3 + 16 * wild))[0]
                if key != "puna":
                    sway = [gap * 0.35 * np.sin(bend + (x + d) * 18.0) for d in (0.0, length)]
                    quad = [(x, v + sway[0]), (x + length, v + sway[1]), (x + length, v + gap + sway[1]), (x, v + gap + sway[0])]
                    fields[key][1].poly(quad)
                    width = 0.0010 + (v - HORIZON) * 0.005
                    wall_pen.line(quad + [quad[0]], width)
                x += length
            v += gap
            gap *= 1.28
        # Tussocks on the slope, small with the distance.
        for _ in range(260):
            u = rng.uniform(0.62, 1.0)
            v = rng.uniform(_at(top, u) + 0.004, 0.70)
            r = 0.0012 + (v - HORIZON) * 0.02
            tuft_pen.ellipse(u, v, r * 1.6, r)
        # Two round houses of stone and thatch on the slope, and the smoke of
        # a hearth from one of them.
        for u, s in ((0.80, 0.015), (0.865, 0.011)):
            base = _at(top, u) + 0.024
            _round_house(house_wall_pen, roof_pen, door_pen, u, base, s, s * 0.9)
        smoke = _plume(a, "andes smoke", 0.80, _at(top, 0.80) + 0.024 - 0.015 * 0.9 * 2.5, 0.12, 0.05, 0.008)
        ground = land * (a.v > top[None, :] - 0.002)
        field_masks = {key: a.mask_of(img) * ground for key, (img, _) in fields.items()}
        house = np.maximum.reduce([a.mask_of(house_walls), a.mask_of(roofs)])
        mask = np.maximum.reduce([land, a.mask_of(reeds), house])
        layer = solid(a, mask, mix(p["puna"], p["far"], 0.35), mix(p["puna"], p["puna_dark"], 0.25), HORIZON - 0.06, HORIZON + 0.10, "andes far", 0.06)
        # The slope: puna, lit on the side to the sun.
        a.light(layer, a.rim(land, 0.004, 0.003, 0.5) * land, p["glow"], 0.35)
        a.light(layer, land * smoothstep(0.45, 0.75, a.noise("andes slope light", cells=12.0, octaves=3)) * rise[None, :], p["puna_light"], 0.25)
        for key, colour in (("potato", p["potato"]), ("quinoa_red", p["quinoa_red"]), ("quinoa_gold", p["quinoa_gold"]), ("earth", p["earth"]), ("puna", p["puna"])):
            a.put(layer, field_masks[key], mix(mix(colour, p["puna"], 0.25), p["far"], 0.30))
        # Fine rows in the near plots: the ridges where the potatoes grow.
        rows = np.clip(1.0 - np.abs(((a.u * 700.0 + a.v * 30.0) % 1.0) - 0.5) / 0.20, 0.0, 1.0) * smoothstep(0.66, 0.78, a.v)
        a.shade(layer, rows * np.maximum(field_masks["potato"], field_masks["earth"]), 0.14)
        # The walls: grey stones, lit on their tops.
        wall_mask = a.mask_of(walls) * ground
        a.put(layer, wall_mask, mix(p["wall"], p["far"], 0.25), 0.9)
        a.light(layer, a.rim(wall_mask, 0.0, 0.001, 0.0) * wall_mask, p["wall_light"], 0.5)
        a.put(layer, a.mask_of(tufts) * land, mix(p["puna_dark"], p["far"], 0.30), 0.7)
        a.put(layer, a.mask_of(reeds), mix(p["reeds"], p["far"], 0.30))
        # The houses: grey stone, and thatch lit at the left.
        a.put(layer, a.mask_of(house_walls), mix(p["wall"], p["far"], 0.10))
        a.put(layer, a.mask_of(roofs), mix(p["thatch"], p["far"], 0.10))
        a.shade(layer, a.mask_of(roofs) * smoothstep(0.0, 1.0, a.noise("andes thatch", cells=140.0, octaves=1, stretch=0.1)), 0.15)
        a.put(layer, a.mask_of(doors), mix(p["near"], p["far"], 0.30))
        a.light(layer, a.rim(house, 0.002, 0.0, 0.2) * house, p["glow"], 0.45)
        a.put(layer, smoke, p["smoke"], 0.65)
        mask = np.maximum(mask, smoke * 0.65)
        # The cold clear air: a little haze far off, and none near.
        a.tint(layer, fog(a, "andes shore haze", top.min() + 0.010, 0.016, 3.0) * land, p["low"], 0.35)
        haze(a, layer, p["low"], 0.05, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near andes")
        bank, bank_pen = a.drawing()
        rocks, rock_pen = a.drawing()
        tussocks, tussock_pen = a.drawing()
        ground, line = a.ridge("near andes", 0.705, 0.006, cells=4.0, octaves=3)
        # A bank of stony ground along the foot, higher at the two sides.
        pts = [(u, _at(line, u) - 0.05 * smoothstep(0.32, 0.02, u) - 0.035 * smoothstep(0.70, 0.98, u)) for u in np.linspace(0.0, 1.0, 60)]
        bank_pen.poly([(0.0, 1.0)] + pts + [(1.0, 1.0)])

        def bank_at(u: float) -> float:
            return float(np.interp(u, [q[0] for q in pts], [q[1] for q in pts]))

        # Grey rocks: ledges of flat stone at the left, one over the other
        # like the steps of the climb, and a few boulders at the right.
        for k, (u, w, h) in enumerate(((0.020, 0.075, 0.035), (0.045, 0.060, 0.030), (0.060, 0.045, 0.026), (0.075, 0.030, 0.020))):
            base = bank_at(0.06) + 0.012 - sum((0.035, 0.030, 0.026, 0.020)[:k])
            rock_pen.poly([(u - w, base), (u - w * 0.96, base - h * 0.85), (u - w * 0.80, base - h), (u + w * 0.85, base - h * 0.96), (u + w, base - h * 0.4), (u + w * 0.98, base)])
        for u, w, h in ((0.17, 0.035, 0.030), (0.84, 0.040, 0.045), (0.95, 0.055, 0.075)):
            _boulder(rock_pen, rng, u, bank_at(u) + 0.01, w, h)
        # Tussocks of ichu: big at the sides, a few small ones along the bank.
        for u, h in ((0.12, 0.075), (0.21, 0.055), (0.27, 0.035), (0.76, 0.050), (0.89, 0.085), (0.995, 0.070)):
            _tussock(tussock_pen, rng, u, bank_at(u) + 0.004, h, 26)
        for _ in range(16):
            u = rng.uniform(0.32, 0.72)
            _tussock(tussock_pen, rng, u, bank_at(u) + 0.002, rng.uniform(0.012, 0.022), 11)
        bank_mask = np.maximum(a.mask_of(bank), ground)
        rock_mask = a.mask_of(rocks)
        grass = a.mask_of(tussocks)
        mask = np.maximum.reduce([bank_mask, rock_mask, grass])
        layer = a.blank()
        earth = a.ramp([(0.0, mix(p["puna"], p["near"], 0.40)), (0.64, mix(p["puna"], p["near"], 0.40)), (0.80, mix(p["puna_dark"], p["near"], 0.72)),
                        (1.0, p["near"])])
        a.put(layer, bank_mask, earth)
        stones = smoothstep(0.62, 0.70, a.noise("andes near stones", cells=160.0, octaves=1))
        a.light(layer, bank_mask * stones * smoothstep(0.72, 0.68, a.v), mix(p["rock"], p["near"], 0.45), 0.35)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.35)
        # The rocks: grey faces, lit at the left and on the top, with cracks.
        a.put(layer, rock_mask, mix(p["rock"], p["near"], 0.35))
        faces = smoothstep(0.40, 0.60, a.noise("andes rock faces", cells=30.0, octaves=2))
        a.light(layer, rock_mask * faces, mix(p["rock_light"], p["near"], 0.30), 0.35)
        a.light(layer, a.rim(rock_mask, 0.004, 0.004, 0.5) * rock_mask, p["glow"], 0.45)
        a.shade(layer, rock_mask * smoothstep(0.66, 0.74, a.noise("andes rock cracks", cells=70.0, octaves=2, stretch=0.4)), 0.30)
        a.shade(layer, a.rim(rock_mask, 0.0, -0.004, 0.4) * rock_mask, 0.25)
        a.put(layer, grass, mix(p["ichu"], p["near"], 0.38))
        a.light(layer, a.rim(grass, 0.002, 0.002, 0.3) * grass, mix(p["ichu_light"], p["glow"], 0.3), 0.45)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.20)
        haze(a, layer, p["low"], 0.06, None)
        return layer
    layer = _air(a, p, "andes cold air", p["low"], 0.16, scale(p["top"], 0.4), 0.20)
    a.put(layer, shafts(a, "andes shafts", 3, 0.16, 0.0, 0.80, 0.04), p["glow"], 0.06)
    return layer


def andes_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Tussocks of ichu grass that stand from below at two places: thin
    stiff blades that fan out."""
    del layer_lights
    rng = art_.rand("andes foreground")
    for k in range(2):
        u0 = (k + rng.uniform(0.2, 0.8)) / 2.0
        for j in range(22):
            t = j / 21.0 - 0.5
            u = u0 + t * 0.02
            reach = rng.uniform(0.8, 1.0) * (1.0 - abs(t) * 0.6)
            top = REST_BOTTOM - rng.uniform(-0.004, 0.010) + (1.0 - reach) * 0.08
            lean = t * 0.16 + rng.uniform(-0.01, 0.01)
            pen.line(_arch((u, 1.0), (u + lean * 0.3, top + 0.12), (u + lean, top), 12), 0.0014)


# ---------------------------------------------------------------------------
# Caral: the pyramids of the Supe valley
# ---------------------------------------------------------------------------


SUPE = {
    "top": (150, 168, 180),
    "mid": (206, 208, 202),
    "low": (236, 228, 212),
    "glow": (255, 240, 212),
    "sun": (255, 248, 232),
    "sea": (124, 142, 148),
    "sea_light": (214, 218, 214),
    "fog": (234, 232, 226),
    "hills": (150, 116, 84),
    "hills_light": (206, 170, 124),
    "desert": (198, 164, 118),
    "desert_light": (230, 202, 156),
    "desert_dark": (150, 118, 84),
    "green": (88, 126, 56),
    "green_light": (136, 160, 74),
    "beans": (66, 104, 54),
    "cotton": (206, 204, 184),
    "squash": (178, 150, 62),
    "river": (132, 156, 160),
    "stone": (172, 156, 128),
    "stone_light": (226, 214, 188),
    "stone_dark": (118, 104, 86),
    "plaza": (160, 140, 112),
    "tree": (76, 90, 56),
    "tree_light": (140, 148, 94),
    "trunk": (96, 74, 56),
    "far": (204, 198, 186),
    "near": (54, 42, 32),
    "near_light": (156, 124, 88),
}


def _platform_pyramid(pen: Pen, lit: Pen, stair: Pen, top: Pen, u: float, v: float, half: float, h: float, tiers: int) -> None:
    """A stepped platform pyramid of Caral: wide, low tiers of stone, each
    set back from the one under it, with a flat top. A wide stair goes
    straight up the middle of its front to the top, and the top has a low
    room of stone on it. `lit` is the left face of each tier, to the sun."""
    base = v
    step = h / tiers
    for k in range(tiers):
        w = half * (1.0 - 0.55 * k / tiers)
        w_top = half * (1.0 - 0.55 * (k + 0.8) / tiers)
        pen.poly([(u - w, base), (u + w, base), (u + w_top, base - step), (u - w_top, base - step)])
        lit.poly([(u - w, base), (u - w * 0.94, base), (u - w_top * 0.94, base - step), (u - w_top, base - step)])
        top.rect(u - w_top, base - step, u + w_top, base - step + step * 0.12)
        base -= step
    room = half * 0.28
    pen.rect(u - room, base - step * 0.6, u + room, base)
    stair.poly([(u - half * 0.09, v), (u + half * 0.09, v), (u + half * 0.06, base), (u - half * 0.06, base)])


def _sunken_plaza(rim: Pen, floor: Pen, u: float, v: float, ru: float, rv: float) -> None:
    """A round sunken plaza seen from a little above: a ring of stone wall,
    the floor that is lower than the ground, and a stair down on the side
    to the pyramid."""
    rim.ellipse(u, v, ru, rv)
    floor.ellipse(u, v + rv * 0.10, ru * 0.84, rv * 0.76)
    rim.rect(u - ru * 0.08, v - rv * 1.05, u + ru * 0.08, v - rv * 0.55)


def _huarango(trunk: Pen, crown: Pen, rng, u: float, v: float, h: float, lean: float) -> None:
    """A huarango tree of the coast of Peru: a short, thick, twisted trunk
    that splits low into a few long branches that reach out and a little
    down, and a wide, flat, uneven crown of small feathery leaves in many
    clumps, some of which hang at its edge."""
    fork = (u + lean * h * 0.4, v - h * 0.30)
    trunk.poly([(u - h * 0.09, v), (u + h * 0.08, v), (fork[0] + h * 0.06, fork[1]), (fork[0] - h * 0.07, fork[1])])
    trunk.poly([(u - h * 0.14, v), (u - h * 0.05, v - h * 0.06), (u + h * 0.05, v - h * 0.06), (u + h * 0.14, v)])
    for k in range(6):
        t = (k - 2.5) / 2.5
        reach = h * (0.50 + 0.25 * (1.0 - abs(t))) + rng.uniform(-0.04, 0.04) * h
        end = (fork[0] + t * reach + lean * h * 0.3, fork[1] - h * (0.28 + 0.22 * (1.0 - abs(t))) + rng.uniform(-0.03, 0.03) * h)
        ctrl = (fork[0] + t * reach * 0.35, end[1] - h * 0.06)
        trunk.line(_arch(fork, ctrl, end, 8), h * (0.030 - 0.006 * abs(t)))
        # The clumps of leaves along the outer part of the branch, and a
        # few that hang down at its end.
        for _ in range(9):
            q = rng.uniform(0.45, 1.05)
            cu = fork[0] + (end[0] - fork[0]) * q + rng.uniform(-0.07, 0.07) * h
            cv = fork[1] + (end[1] - fork[1]) * q + rng.uniform(-0.05, 0.04) * h
            crown.ellipse(cu, cv, h * rng.uniform(0.09, 0.15), h * rng.uniform(0.035, 0.060))
        for _ in range(2):
            cu = end[0] + rng.uniform(-0.05, 0.05) * h
            crown.ellipse(cu, end[1] + h * rng.uniform(0.04, 0.09), h * 0.030, h * 0.050)


def _scrub(pen: Pen, rng, u: float, v: float, h: float) -> None:
    """A low dry bush of the desert: many thin twigs from one root, with a
    few small leaves at their ends."""
    for _ in range(14):
        a = rng.uniform(-1.1, 1.1)
        end = (u + np.sin(a) * h * 0.9, v - np.cos(a) * h * rng.uniform(0.6, 1.0))
        pen.line([(u, v), ((u + end[0]) * 0.5 + rng.uniform(-0.1, 0.1) * h, (v + end[1]) * 0.5), end], max(0.0008, h * 0.03))
        pen.ellipse(end[0], end[1], h * 0.08, h * 0.05)


def history_supe(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = SUPE
    sun_at = (0.70, 0.31)
    sea_v = HORIZON - 0.004
    coast_u = 0.30
    if layer_key == "sky":
        # A hazy sky of the coast: grey-blue at the top, warm white low down,
        # and the sun a pale disc through the haze.
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.90)), (0.24, p["top"]), (0.46, p["mid"]), (sea_v, p["low"]),
                                 (sea_v + 0.002, p["sea"]), (1.0, p["sea"])]))
        _sun(a, layer, *sun_at, 0.024, p["sun"], p["glow"], 0.45)
        a.tint(layer, fog(a, "supe high haze", 0.26, 0.10, 2.0), p["mid"], 0.35)
        # The grey sea at the left, with a few soft lines of light.
        sea = (a.v > sea_v).astype(np.float32)
        a.light(layer, sea * smoothstep(0.62, 0.80, a.noise("supe sea lines", cells=50.0, octaves=2, stretch=12.0)), p["sea_light"], 0.30)
        # The brown foothills: ranges that go back into the haze, bare and
        # dry, that come down to the sea at the left.
        for k, (base, amp, cells, sharp, pale) in enumerate(((sea_v - 0.090, 0.040, 4.0, 0.70, 0.66), (sea_v - 0.060, 0.034, 5.0, 0.65, 0.46),
                                                             (sea_v - 0.032, 0.024, 7.0, 0.55, 0.26))):
            _, line = a.ridge(("supe hills", k), base, amp, cells=cells, octaves=5, sharp=sharp)
            line = line + (sea_v + 0.003 - line) * smoothstep(0.42 - 0.05 * k, 0.10 + 0.04 * k, a.u[0])
            # At the left the hills end at the sea; at the right their feet go
            # down behind the plain of the far layer.
            foot = sea_v + 0.004 + 0.08 * smoothstep(coast_u - 0.06, coast_u + 0.06, a.u)
            mask = _land(a, line) * smoothstep(foot + 0.002, foot - 0.001, a.v)
            colour = mix(p["hills"], p["low"], pale)
            colour = mix(colour, p["desert_dark"], 0.15 * (2 - k))
            a.put(layer, mask, a.ramp([(0.0, colour), (base, colour), (sea_v, mix(colour, p["low"], 0.40)), (1.0, colour)]))
            gullies = smoothstep(0.60, 0.80, a.noise(("supe gullies", k), cells=60.0, octaves=3, stretch=0.35))
            a.shade(layer, mask * gullies * smoothstep(base + amp * 1.5, base - amp, a.v), 0.08 * (1.0 - pale))
            a.light(layer, a.rim(mask, -0.008, 0.002, 1.5) * mask, mix(p["hills_light"], p["glow"], 0.4), 0.35 * (1.0 - pale * 0.5))
        # The garua: a low fog of the sea that lies on the water and on the
        # feet of the hills.
        a.tint(layer, fog(a, "supe garua", sea_v - 0.004, 0.022, 3.0), p["fog"], 0.85)
        a.tint(layer, fog(a, "supe garua high", sea_v - 0.030, 0.016, 4.0) * smoothstep(0.5, 0.1, a.u), p["fog"], 0.55)
        _textbook(a, layer, 0.08)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far supe")
        # The desert plain, from the coast at the left to the hills at the
        # right. The green valley runs across it.
        _, plain = a.ridge("supe plain", sea_v + 0.003, 0.002, cells=4.0, octaves=2)
        coast = coast_u - (a.v - HORIZON) * 2.0
        land = _land(a, plain) * smoothstep(coast - 0.01, coast + 0.01, a.u)
        # The valley: a band that winds a little, narrow far off at the sea
        # and wider toward the hills.
        mid = HORIZON + 0.022 + 0.006 * np.sin(a.u * 9.0 + 0.6) + 0.004 * np.sin(a.u * 23.0)
        half = 0.008 + 0.006 * a.u
        valley = smoothstep(half + 0.002, half - 0.002, np.abs(a.v - mid)) * land
        river = smoothstep(0.0012, 0.0004, np.abs(a.v - mid - 0.002 * np.sin(a.u * 40.0))) * land
        crops = {key: a.drawing() for key in ("green", "green_light", "beans", "cotton", "squash")}
        for _ in range(900):
            u = rng.uniform(coast_u - 0.04, 1.0)
            v = rng.uniform(HORIZON + 0.008, HORIZON + 0.046)
            key = rng.choices(("green", "green_light", "beans", "cotton", "squash"), (4, 3, 2, 3, 1))[0]
            w = rng.uniform(0.008, 0.022)
            crops[key][1].rect(u, v, u + w, v + rng.uniform(0.002, 0.004))
        trees, tree_pen = a.drawing()
        for _ in range(140):
            u = rng.uniform(coast_u, 1.0)
            v = float(np.interp(u, a.u[0], mid[0])) + rng.choice((-1.0, 1.0)) * float(np.interp(u, a.u[0], half[0])) * rng.uniform(0.7, 1.0)
            tree_pen.ellipse(u, v - 0.002, rng.uniform(0.003, 0.006), rng.uniform(0.002, 0.004))
        # The city on its terrace of desert, on the near side of the valley:
        # the pyramids, the round plaza and low walls of houses.
        stone, stone_pen = a.drawing()
        lit, lit_pen = a.drawing()
        stairs, stair_pen = a.drawing()
        tops, top_pen = a.drawing()
        rims, rim_pen = a.drawing()
        floors, floor_pen = a.drawing()
        houses, house_pen = a.drawing()
        for u, v, half_w, h, tiers in ((0.33, 0.636, 0.050, 0.024, 3), (0.46, 0.642, 0.040, 0.020, 3), (0.62, 0.650, 0.120, 0.055, 5), (0.83, 0.643, 0.060, 0.032, 4),
                                       (0.95, 0.636, 0.034, 0.018, 3)):
            _platform_pyramid(stone_pen, lit_pen, stair_pen, top_pen, u, v, half_w, h, tiers)
        _sunken_plaza(rim_pen, floor_pen, 0.62, 0.664, 0.052, 0.0095)
        _sunken_plaza(rim_pen, floor_pen, 0.83, 0.652, 0.024, 0.0048)
        # Low walls of the rooms and courts of the people, in groups
        # between the pyramids.
        for cu, cv in ((0.40, 0.650), (0.53, 0.656), (0.73, 0.658), (0.90, 0.650)):
            for _ in range(5):
                u = cu + rng.uniform(-0.03, 0.03)
                v = cv + rng.uniform(-0.004, 0.006)
                w = rng.uniform(0.004, 0.009)
                house_pen.rect(u - w, v - 0.0025, u + w, v)
        valley_crops = {key: a.mask_of(img) * valley for key, (img, _) in crops.items()}
        building = np.maximum.reduce([a.mask_of(stone), a.mask_of(rims), a.mask_of(houses)])
        mask = np.maximum(land, building)
        layer = solid(a, mask, mix(p["desert"], p["far"], 0.40), mix(p["desert"], p["desert_dark"], 0.15), HORIZON - 0.02, HORIZON + 0.10, "supe far", 0.06)
        # Low dunes and the tracks of dry gullies in the desert.
        a.light(layer, land * smoothstep(0.55, 0.75, a.noise("supe dunes", cells=24.0, octaves=3, stretch=5.0)), p["desert_light"], 0.25)
        # The valley: its fields, its trees and its river.
        a.put(layer, valley, mix(p["green"], p["far"], 0.35))
        for key in ("green", "green_light", "beans", "cotton", "squash"):
            a.put(layer, valley_crops[key], mix(p[key], p["far"], 0.30))
        a.put(layer, a.mask_of(trees) * land, mix(p["tree"], p["far"], 0.30))
        a.put(layer, river, mix(p["river"], p["sea_light"], 0.3), 0.8)
        # The pyramids: grey-tan stone, the face to the sun at the left lit,
        # the edges of the tiers lit, and the stair lighter.
        a.put(layer, a.mask_of(stone), mix(p["stone"], p["far"], 0.12))
        a.light(layer, a.mask_of(lit), p["stone_light"], 0.35)
        a.light(layer, a.mask_of(tops) * a.mask_of(stone), p["stone_light"], 0.40)
        a.shade(layer, a.mask_of(stone) * smoothstep(0.4, 0.9, a.noise("supe courses", cells=300.0, octaves=1, stretch=8.0)), 0.06)
        a.put(layer, a.mask_of(stairs), mix(p["stone_light"], p["stone"], 0.45))
        steps = np.clip(1.0 - np.abs(((a.v * 900.0) % 1.0) - 0.5) / 0.22, 0.0, 1.0)
        a.shade(layer, a.mask_of(stairs) * steps, 0.20)
        a.light(layer, a.rim(a.mask_of(stone), 0.002, 0.0, 0.2) * a.mask_of(stone), p["glow"], 0.35)
        # The plazas: a ring wall of stone, and the floor lower than the
        # ground, in shade at its far side.
        rim_mask = a.mask_of(rims)
        floor_mask = a.mask_of(floors)
        a.put(layer, rim_mask, mix(p["stone"], p["far"], 0.10))
        a.put(layer, floor_mask, mix(p["plaza"], p["far"], 0.10))
        a.shade(layer, a.rim(floor_mask, 0.0, -0.003, 0.3) * floor_mask, 0.35)
        a.light(layer, a.rim(rim_mask, 0.0, 0.0015, 0.2) * rim_mask, p["stone_light"], 0.5)
        houses_mask = a.mask_of(houses)
        a.put(layer, houses_mask, mix(p["stone"], p["far"], 0.20))
        a.shade(layer, a.rim(houses_mask, 0.0, -0.001, 0.0) * houses_mask, 0.25)
        # The haze of the coast over all, more far off.
        a.tint(layer, fog(a, "supe valley haze", HORIZON + 0.010, 0.020, 3.0), p["low"], 0.40)
        haze(a, layer, p["low"], 0.08, None)
        layer[..., 3] = np.minimum(layer[..., 3], mask)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near supe")
        bank, bank_pen = a.drawing()
        trunks, trunk_pen = a.drawing()
        crowns, crown_pen = a.drawing()
        scrub, scrub_pen = a.drawing()
        ground, line = a.ridge("near supe", 0.705, 0.006, cells=4.0, octaves=3)
        pts = [(u, _at(line, u) - 0.035 * smoothstep(0.30, 0.02, u) - 0.045 * smoothstep(0.72, 0.98, u)) for u in np.linspace(0.0, 1.0, 60)]
        bank_pen.poly([(0.0, 1.0)] + pts + [(1.0, 1.0)])

        def bank_at(u: float) -> float:
            return float(np.interp(u, [q[0] for q in pts], [q[1] for q in pts]))

        # A big huarango at the left and a smaller one at the right; dry
        # scrub along the bank. The middle stays calm.
        _huarango(trunk_pen, crown_pen, rng, 0.09, bank_at(0.09) + 0.004, 0.24, 0.10)
        _huarango(trunk_pen, crown_pen, rng, 0.91, bank_at(0.91) + 0.004, 0.17, -0.12)
        for u, h in ((0.22, 0.030), (0.28, 0.018), (0.74, 0.026), (0.80, 0.020)):
            _scrub(scrub_pen, rng, u, bank_at(u) + 0.002, h)
        for _ in range(12):
            u = rng.uniform(0.32, 0.70)
            _scrub(scrub_pen, rng, u, bank_at(u) + 0.002, rng.uniform(0.008, 0.012))
        bank_mask = np.maximum(a.mask_of(bank), ground)
        plants = np.maximum.reduce([a.mask_of(trunks), a.mask_of(crowns), a.mask_of(scrub)])
        mask = np.maximum(bank_mask, plants)
        layer = a.blank()
        a.put(layer, a.mask_of(crowns), mix(p["tree"], p["near"], 0.30))
        # The leaves: lit on the top of each clump, with a fine texture of
        # small leaflets.
        crown_mask = a.mask_of(crowns)
        a.light(layer, a.rim(crown_mask, 0.0, 0.010, 1.5) * crown_mask, mix(p["tree_light"], p["near"], 0.25), 0.40)
        a.shade(layer, crown_mask * smoothstep(0.50, 0.80, a.noise("supe leaflets", cells=300.0, octaves=1)), 0.12)
        a.shade(layer, a.rim(crown_mask, 0.0, -0.008, 1.5) * crown_mask, 0.20)
        a.put(layer, a.mask_of(trunks), mix(p["trunk"], p["near"], 0.40))
        a.put(layer, a.mask_of(scrub), mix(p["desert_dark"], p["near"], 0.45))
        earth = a.ramp([(0.0, mix(p["near_light"], p["near"], 0.20)), (0.64, mix(p["near_light"], p["near"], 0.20)), (0.80, mix(p["near_light"], p["near"], 0.70)),
                        (1.0, p["near"])])
        a.put(layer, bank_mask, earth)
        pebbles = smoothstep(0.64, 0.70, a.noise("supe near pebbles", cells=180.0, octaves=1))
        a.shade(layer, bank_mask * pebbles, 0.08)
        a.light(layer, bank_mask * smoothstep(0.55, 0.75, a.noise("supe near drifts", cells=16.0, octaves=2, stretch=4.0)), p["near_light"], 0.12)
        a.light(layer, a.rim(bank_mask, 0.0, 0.003, 0.4) * bank_mask, p["glow"], 0.35)
        a.light(layer, a.rim(plants, -0.003, 0.002, 0.4) * plants, p["glow"], 0.30)
        a.shade(layer, a.rim(mask, 0.004, -0.003, 1.0) * mask, 0.20)
        haze(a, layer, p["low"], 0.10, None)
        return layer
    layer = _air(a, p, "supe dusty haze", p["low"], 0.26, p["near"], 0.20)
    a.put(layer, shafts(a, "supe shafts", 3, -0.14, 0.0, 0.85, 0.06), p["glow"], 0.06)
    return layer


def supe_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """A branch of a huarango that hangs into the top of the view at one
    place, with clumps of small leaves, and dry twigs of scrub that stand
    from below at another place."""
    del layer_lights
    rng = art_.rand("supe foreground")
    u0 = rng.uniform(0.10, 0.30)
    branch = _arch((u0 - 0.06, 0.0), (u0 + 0.02, 0.20), (u0 + 0.16, 0.33), 16)
    pen.line(branch, 0.0040)
    # Twigs along the branch, each with a feathery leaf: a stalk with small
    # leaflets in pairs.
    for i, (x, y) in enumerate(branch[2:], 2):
        side = 1.0 if i % 2 else -1.0
        tip = (x + side * 0.035, min(0.384, y + 0.040))
        pen.line([(x, y), tip], 0.0014)
        for j in range(1, 7):
            t = j / 7.0
            cx, cy = x + (tip[0] - x) * t, y + (tip[1] - y) * t
            for flip in (-1.0, 1.0):
                pen.line([(cx, cy), (cx + 0.006 * flip, min(0.388, cy + 0.006))], 0.0010)
    u1 = rng.uniform(0.65, 0.85)
    for _ in range(10):
        u = u1 + rng.uniform(-0.015, 0.015)
        top = REST_BOTTOM - rng.uniform(-0.004, 0.012)
        lean = rng.uniform(-0.06, 0.06)
        twig = _arch((u, 1.0), (u + lean * 0.3, top + 0.08), (u + lean, top), 8)
        pen.line(twig, 0.0018)
        x, y = twig[-1]
        pen.line([(x, y + 0.02), (x + lean * 0.4 + 0.01, y + 0.008)], 0.0012)
