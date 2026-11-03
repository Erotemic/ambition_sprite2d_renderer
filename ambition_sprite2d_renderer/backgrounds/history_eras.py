"""The scenes of the History dimension: a walk forward in time.

The dimension is a timeline. A player walks east and walks forward in time,
through eight eras that stand side by side on one long road. Each era is an
outdoor room with its own sky, and the eight skies are one day: dawn at the
first farms and dusk at the mills.

- ``history_crescent`` (the Fertile Crescent). Dawn over a river plain. A
  ziggurat stands far off over a town of mudbrick, date palms line the
  canal, and the fields of wheat are gold in the first light.
- ``history_nile`` (the Nile). A red sun low in a dusty sky. The pyramids
  and an obelisk stand on the desert, and the green strip of the river runs
  under them. Papyrus grows at the sides.
- ``history_classical`` (the Classical Shore). Bright noon on the
  Mediterranean. A marble temple stands on a hill, an aqueduct strides out
  from it, and a trireme rows on the wine-dark sea. Olive trees at the sides.
- ``history_silk`` (the Silk Road). A hot afternoon over the dunes. A long
  caravan walks on the skyline, a pagoda and the Great Wall are far off, and
  an oasis lies between. The arch of a caravanserai is at the side.
- ``history_steppe`` (the Mongol Steppe). An enormous sky over grass to the
  end of the world. Felt gers with smoke, a herd of horses, the Great Wall
  on the hills at the west, and a golden eagle high up.
- ``history_monsoon`` (Timbuktu and the Monsoon Coast). Monsoon clouds. The
  west is the Sahel, with a great mosque of mudbrick and its toron spikes;
  the east is a coast of coral stone, and dhows sail under the rain.
- ``history_sail`` (the Age of Sail). A harbour of tall ships with a
  lighthouse on the headland. An old map is drawn on the sky, and its edges
  are not finished.
- ``history_industrial`` (the Industrial Age). A smoky dusk over a mill
  town: red brick mills with rows of lit windows, tall chimneys, and a
  railway viaduct with a train on it. Gas lamps at the sides.

The palette is the warm sepia of an old textbook and a map, and each era
adds its own accent colours. The bright detail is far off or at the edges,
and the middle of each near layer is calm, so the play in front of it reads.
The things that drift in the air are the room's motes (`terrain/motes.py`),
not part of these pictures.
"""

from __future__ import annotations

import math

import numpy as np

from .artkit import Art, Pen, mix, polar, scale, smoothstep
from .parts import HORIZON, cloud_mask, fog, haze, lamps, shafts, solid, vignette, window_grid

#: The bottom of what a view at rest shows of a foreground panel (as
#: `REST_BOTTOM` in `foregrounds.py`): a thing that stands from below ends a
#: little under it.
REST_BOTTOM = 0.628

#: The colour of an old textbook. Each sky is moved a little to it, so the
#: eight eras read as pages of one book.
SEPIA = (206, 172, 124)

CRESCENT = {
    "top": (46, 58, 112),
    "mid": (128, 112, 160),
    "pink": (226, 138, 140),
    "low": (250, 186, 128),
    "glow": (255, 224, 170),
    "sun": (255, 240, 200),
    "mud": (196, 146, 96),
    "mud_dark": (128, 86, 60),
    "wheat": (232, 188, 92),
    "river": (70, 152, 152),
    "lapis": (44, 72, 156),
    "palm": (58, 74, 54),
    "far": (156, 120, 124),
    "near": (48, 32, 30),
    "near_light": (156, 102, 72),
}

NILE = {
    "top": (84, 64, 112),
    "mid": (202, 110, 92),
    "low": (250, 186, 118),
    "glow": (255, 170, 100),
    "sun": (232, 70, 44),
    "sand": (226, 172, 110),
    "sandstone": (220, 180, 124),
    "papyrus": (74, 124, 66),
    "nile": (44, 98, 142),
    "lapis": (38, 62, 152),
    "gold": (238, 190, 70),
    "far": (178, 120, 104),
    "near": (54, 30, 24),
    "near_light": (176, 104, 62),
}

CLASSICAL = {
    "top": (36, 92, 184),
    "mid": (98, 158, 226),
    "low": (208, 228, 242),
    "sun": (255, 252, 236),
    "marble": (242, 238, 228),
    "marble_shade": (168, 170, 188),
    "terracotta": (196, 92, 58),
    "olive": (112, 126, 78),
    "olive_dark": (66, 76, 52),
    "sea": (34, 56, 118),
    "sea_light": (86, 134, 196),
    "land": (190, 162, 104),
    "far": (152, 172, 204),
    "near": (40, 44, 38),
    "near_light": (156, 154, 120),
}

SILK = {
    "top": (98, 142, 192),
    "mid": (190, 196, 196),
    "low": (252, 228, 172),
    "sun": (255, 250, 228),
    "dune": (228, 172, 98),
    "dune_shadow": (178, 112, 72),
    "crimson": (178, 40, 40),
    "saffron": (240, 172, 40),
    "jade": (60, 152, 122),
    "indigo": (42, 52, 112),
    "far": (204, 170, 132),
    "near": (68, 40, 30),
    "near_light": (196, 124, 72),
}

STEPPE = {
    "top": (38, 88, 180),
    "mid": (108, 168, 230),
    "low": (222, 234, 236),
    "cloud": (255, 255, 250),
    "cloud_shadow": (150, 170, 204),
    "grass": (150, 172, 82),
    "gold": (214, 194, 104),
    "felt": (242, 234, 216),
    "saddle": (172, 52, 40),
    "blue": (64, 120, 200),
    "far": (132, 162, 156),
    "near": (40, 48, 28),
    "near_light": (150, 156, 76),
}

MONSOON = {
    "top": (58, 64, 82),
    "mid": (118, 126, 138),
    "low": (234, 208, 160),
    "sun": (255, 222, 150),
    "cloud": (86, 92, 108),
    "cloud_light": (196, 196, 196),
    "rain": (150, 160, 170),
    "adobe": (198, 142, 82),
    "adobe_dark": (132, 88, 52),
    "coral": (230, 218, 194),
    "sea": (44, 170, 168),
    "sea_deep": (30, 100, 120),
    "gold": (238, 188, 60),
    "far": (152, 142, 132),
    "near": (42, 34, 30),
    "near_light": (164, 122, 80),
}

SAIL = {
    "top": (118, 150, 160),
    "mid": (192, 202, 184),
    "low": (240, 226, 190),
    "ink": (104, 76, 48),
    "parchment": (234, 216, 172),
    "sea": (52, 112, 102),
    "sea_light": (132, 182, 162),
    "canvas": (242, 234, 212),
    "tar": (36, 32, 30),
    "brass": (202, 160, 72),
    "red": (170, 60, 44),
    "far": (132, 152, 142),
    "near": (30, 32, 30),
    "near_light": (116, 124, 104),
}

INDUSTRIAL = {
    "top": (50, 44, 62),
    "mid": (132, 78, 72),
    "low": (242, 142, 72),
    "sun": (255, 196, 120),
    "smoke": (92, 80, 80),
    "smoke_light": (176, 134, 112),
    "brick": (152, 72, 52),
    "brick_dark": (84, 42, 36),
    "iron": (70, 72, 80),
    "steam": (232, 228, 222),
    "gas": (255, 212, 124),
    "far": (112, 82, 82),
    "near": (28, 24, 26),
    "near_light": (124, 82, 62),
}


# ---------------------------------------------------------------------------
# Parts that more than one era has
# ---------------------------------------------------------------------------


def _textbook(a: Art, layer: np.ndarray, amount: float = 0.08) -> None:
    """Move a sky a little to the sepia of an old textbook, and give it the
    grain of paper."""
    a.tint(layer, np.ones((a.n, a.n), dtype=np.float32), SEPIA, amount)
    a.grain(layer, "paper grain", 2.0)


def _sun(a: Art, layer: np.ndarray, u: float, v: float, r: float, disc, halo, strength: float = 0.6) -> None:
    """A sun: a disc and a wide soft light round it."""
    a.light(layer, a.spot(u, v, r * 9.0, 2.0, squash=1.4), halo, strength)
    a.light(layer, a.spot(u, v, r * 3.0, 1.6), halo, 0.55)
    image, pen = a.drawing()
    pen.ellipse(u, v, r)
    a.put(layer, a.mask_of(image, blur=0.8), disc, 0.95)


def _at(line: np.ndarray, u: float) -> float:
    """The `v` of a ridge line at `u`."""
    return float(line[min(len(line) - 1, max(0, int(u * len(line))))])


def _outline(a: Art, mask: np.ndarray, d: float) -> np.ndarray:
    """The edge of `mask` all round, `d` wide."""
    return np.clip(a.rim(mask, d, 0.0) + a.rim(mask, -d, 0.0) + a.rim(mask, 0.0, d) + a.rim(mask, 0.0, -d), 0.0, 1.0)


def _air(a: Art, p: dict, tag: str, fog_colour, fog_amount: float, edge, edge_amount: float) -> np.ndarray:
    """The air in front: low mist over the ground and dark air at the sides."""
    layer = a.blank()
    a.put(layer, fog(a, tag, 0.69, 0.13), fog_colour, fog_amount)
    vignette(a, layer, edge, edge_amount)
    return layer


def _plume(a: Art, tag: object, u: float, v: float, rise: float, drift: float, width: float) -> np.ndarray:
    """Smoke that goes up from `(u, v)` by `rise` and leans by `drift`,
    wider as it goes up, in soft lumps."""
    t = np.clip((v - a.v) / rise, 0.0, 1.0)
    centre = u + drift * t**1.4
    half = width * (0.3 + 1.7 * t)
    across = np.clip(1.0 - np.abs(a.u - centre) / np.maximum(half, 1e-4), 0.0, 1.0)
    lumps = a.noise(tag, cells=14.0, octaves=3)
    body = across * (a.v < v) * (a.v > v - rise) * (0.5 + 0.8 * lumps)
    return np.clip(body * smoothstep(0.0, 0.08, t) * (1.0 - t) ** 0.6, 0.0, 1.0)


def _heaps(a: Art, layer: np.ndarray, tag: str, clouds, light, shadow, alpha: float = 1.0) -> None:
    """Heap clouds, each `(u, v_base, half_width, height)`: round puffs that
    get higher to the middle, on a base that is almost flat. The tops are
    lit and the base is in shade."""
    rng = a.rand(tag)
    image, pen = a.drawing()
    for u, base, w, h in clouds:
        pen.ellipse(u, base - h * 0.10, w * 0.95, h * 0.10)
        for side in (-1.0, 1.0):
            pen.ellipse(u + side * w * rng.uniform(0.35, 0.5), base - h * 0.13, w * 0.5, h * 0.12)
        for _ in range(10):
            dx = rng.uniform(-0.75, 0.75)
            r = h * rng.uniform(0.26, 0.40) * (1.0 - abs(dx) * 0.55)
            pen.ellipse(u + dx * w, base - h * 0.22 - (h * 0.55 - r) * (1.0 - abs(dx)) - r * 0.4, r * 1.1, r)
    soft = a.mask_of(image, blur=3.0)
    edge = a.noise((tag, "edge"), cells=24.0, octaves=3)
    mask = smoothstep(0.30, 0.55, soft + (edge - 0.5) * 0.22)
    # A point is lit when there is no cloud over it, in shade when there is
    # no cloud under it: the light comes from above.
    over = a.blur(a.shift(mask, 0.0, 0.03), 12.0)
    under = a.blur(a.shift(mask, 0.0, -0.02), 6.0)
    lit = np.clip(0.30 + 0.9 * (1.0 - over) - 0.45 * (1.0 - under), 0.0, 1.0)
    paint = a.flat(shadow) + (a.flat(light) - a.flat(shadow)) * lit[:, :, None]
    a.put(layer, mask, paint, alpha)


# -- shapes of the Crescent -------------------------------------------------


def _ziggurat(pen: Pen, stair: Pen, u: float, v: float, half: float, h: float) -> None:
    """A ziggurat of three tiers, each with sloped sides, a stair up the
    front, and a small shrine on the top."""
    tiers = ((1.0, 0.42), (0.70, 0.30), (0.44, 0.20))
    base = v
    for width, part in tiers:
        top = base - h * part
        w = half * width
        pen.poly([(u - w, base), (u + w, base), (u + w * 0.94, top), (u - w * 0.94, top)])
        base = top
    pen.rect(u - half * 0.16, base - h * 0.09, u + half * 0.16, base)
    stair.poly([(u - half * 0.07, v), (u + half * 0.07, v), (u + half * 0.05, base), (u - half * 0.05, base)])
    for side in (-1.0, 1.0):
        stair.poly([(u + side * half * 0.62, v), (u + side * half * 0.52, v), (u + side * half * 0.06, v - h * 0.42), (u + side * half * 0.10, v - h * 0.42)])


def _mud_house(pen: Pen, holes: Pen, u: float, v: float, w: float, h: float) -> None:
    """A house of mudbrick: a box with a flat roof, a dark door and a window."""
    pen.rect(u - w, v - h, u + w, v)
    pen.rect(u - w * 1.06, v - h - h * 0.08, u + w * 1.06, v - h)
    holes.rect(u - w * 0.18, v - h * 0.48, u + w * 0.18, v)
    holes.rect(u + w * 0.42, v - h * 0.78, u + w * 0.66, v - h * 0.6)


def _shadoof(pen: Pen, u: float, v: float, h: float) -> None:
    """A shadoof: two posts with a beam on their tops, and a long pole that
    swings on the beam. A lump of mud on the short end is the weight, and a
    bucket hangs on a rope from the long end."""
    for du in (-0.016, 0.016):
        pen.line([(u + du * 1.6, v + 0.02), (u + du * 0.4, v - h)], 0.005)
    pen.rect(u - 0.014, v - h - 0.004, u + 0.014, v - h + 0.004)
    low, high = (u - h * 0.55, v - h * 0.62), (u + h * 0.90, v - h * 1.62)
    pen.line([low, high], 0.0045)
    pen.ellipse(low[0], low[1] + 0.006, 0.016, 0.013)
    drop = h * 0.95
    pen.line([high, (high[0], high[1] + drop)], 0.0016)
    pen.poly([(high[0] - 0.010, high[1] + drop), (high[0] + 0.010, high[1] + drop), (high[0] + 0.007, high[1] + drop + 0.018), (high[0] - 0.007, high[1] + drop + 0.018)])


def _date_palm(trunk: Pen, crown: Pen, rng, u: float, v: float, h: float, lean: float, fronds: int = 11) -> None:
    """A date palm: a trunk that is almost straight, and a crown of stiff
    fronds that arch out and hang, with bunches of dates under it. Each
    width is a part of `h`, so a far palm and a near one have the same
    shape."""
    w = h * 0.032
    top = (u + lean, v - h)
    trunk.line([(u + lean * t**1.3, v + 0.01 - (h + 0.01) * t) for t in np.linspace(0.0, 1.0, 10)], w)
    for k in range(fronds):
        angle = -200.0 + k * (220.0 / (fronds - 1)) + rng.uniform(-6.0, 6.0)
        length = h * rng.uniform(0.30, 0.40)
        tip = polar(*top, length, angle)
        tip = (tip[0], tip[1] + length * 0.55)
        ctrl = polar(*top, length * 0.6, angle)
        ctrl = (ctrl[0], ctrl[1] - length * 0.28)
        prev = top
        for i in range(1, 11):
            t = i / 10.0
            x = (1 - t) ** 2 * top[0] + 2 * (1 - t) * t * ctrl[0] + t * t * tip[0]
            y = (1 - t) ** 2 * top[1] + 2 * (1 - t) * t * ctrl[1] + t * t * tip[1]
            crown.line([prev, (x, y)], w * 0.5 * (1.0 - t * 0.5))
            side = h * 0.05 * (1.0 - t * 0.55)
            crown.line([(x, y), (x + side * 0.5, y + side)], w * 0.22)
            crown.line([(x, y), (x - side * 0.5, y + side)], w * 0.22)
            prev = (x, y)
    for du in (-0.4, 0.5):
        crown.ellipse(top[0] + du * h * 0.06, top[1] + h * 0.06, h * 0.025, h * 0.04)


def _sheaf(pen: Pen, u: float, v: float, h: float) -> None:
    """A sheaf of wheat that stands in the field: stalks that spread at the
    foot, a band round the waist, and a round head of ears."""
    w = h * 0.30
    pen.poly([(u - w, v), (u + w, v), (u + w * 0.30, v - h * 0.45), (u - w * 0.30, v - h * 0.45)])
    pen.rect(u - w * 0.36, v - h * 0.55, u + w * 0.36, v - h * 0.42)
    for k in range(9):
        angle = -90.0 + (k - 4) * 13.0
        tip = polar(u, v - h * 0.5, h * 0.52, angle)
        pen.line([(u, v - h * 0.5), tip], w * 0.22)
        pen.ellipse(tip[0], tip[1], w * 0.12, w * 0.24)


def _reeds(pen: Pen, rng, u0: float, u1: float, v: float, h: float, count: int) -> None:
    """Reeds in a clump along the ground, each with a soft head."""
    for _ in range(count):
        u = rng.uniform(u0, u1)
        top = h * rng.uniform(0.5, 1.0)
        lean = rng.uniform(-0.012, 0.012)
        pen.line([(u, v + 0.01), (u + lean * 0.5, v - top * 0.5), (u + lean, v - top)], 0.0022)
        if rng.random() < 0.5:
            pen.ellipse(u + lean, v - top - 0.008, 0.0022, 0.009)


# -- shapes of the Nile -----------------------------------------------------


def _pyramid(pen: Pen, lit: Pen, u: float, v: float, half: float, h: float, lit_side: float = -1.0) -> None:
    """A smooth pyramid: two faces, and `lit` takes the face on `lit_side`."""
    pen.poly([(u - half, v), (u + half, v), (u, v - h)])
    lit.poly([(u + lit_side * half, v), (u + lit_side * half * 0.12, v + 0.002), (u, v - h)])


def _obelisk(pen: Pen, tip: Pen, u: float, v: float, w: float, h: float) -> None:
    pen.poly([(u - w, v), (u + w, v), (u + w * 0.70, v - h), (u - w * 0.70, v - h)])
    tip.poly([(u - w * 0.70, v - h), (u + w * 0.70, v - h), (u, v - h - w * 1.6)])


def _papyrus(pen: Pen, rng, u: float, v: float, h: float, count: int, spread: float) -> None:
    """A clump of papyrus: tall stems, each with a fan of threads at the top."""
    for _ in range(count):
        x = u + rng.uniform(-spread, spread)
        top = h * rng.uniform(0.6, 1.0)
        lean = rng.uniform(-0.03, 0.03)
        head = (x + lean, v - top)
        pen.line([(x, v + 0.01), ((x + head[0]) * 0.5 + lean * 0.2, v - top * 0.5), head], 0.0045)
        r = top * rng.uniform(0.12, 0.16)
        fan = [head]
        for k in range(13):
            angle = -175.0 + k * 14.0 + rng.uniform(-3.0, 3.0)
            end = polar(head[0], head[1], r, angle)
            end = (end[0], end[1] + r * 0.25 * abs(math.cos(math.radians(angle))))
            pen.line([head, end], 0.0022)
            fan.append(end)
        pen.poly([head, *[(head[0] + (x1 - head[0]) * 0.55, head[1] + (y1 - head[1]) * 0.55) for x1, y1 in fan[1:]]])


def _lotus_column(pen: Pen, band: Pen, u: float, v: float, h: float, w: float) -> None:
    """A column of sandstone with a capital like a lotus that is open."""
    pen.rect(u - w, v - h, u + w, v + 0.02)
    pen.rect(u - w * 1.3, v - 0.012, u + w * 1.3, v + 0.02)
    cap = v - h
    pen.poly([(u - w, cap), (u + w, cap), (u + w * 1.9, cap - h * 0.13), (u + w * 1.6, cap - h * 0.17), (u - w * 1.6, cap - h * 0.17), (u - w * 1.9, cap - h * 0.13)])
    pen.rect(u - w * 1.7, cap - h * 0.20, u + w * 1.7, cap - h * 0.17)
    for k in range(3):
        y = cap + h * (0.06 + k * 0.03)
        band.rect(u - w, y, u + w, y + h * 0.012)


# -- shapes of the Classical Shore ------------------------------------------


def _temple(pen: Pen, gaps: Pen, roof: Pen, u: float, v: float, w: float, h: float, columns: int = 8) -> None:
    """A temple of marble: three steps, a row of columns, the entablature and
    the pediment. `gaps` takes the shade between the columns, `roof` the
    tiles of the pediment."""
    step = h * 0.06
    for k in range(3):
        pen.rect(u - w - (2 - k) * step, v - step * (k + 1), u + w + (2 - k) * step, v - step * k)
    floor = v - step * 3
    col_h = h * 0.58
    pen.rect(u - w, floor - col_h, u + w, floor)
    pitch = 2.0 * w / columns
    for k in range(columns - 1):
        x = u - w + pitch * (k + 1)
        gaps.rect(x - pitch * 0.28, floor - col_h + h * 0.02, x + pitch * 0.28, floor)
    gaps.rect(u - w + pitch * 0.22, floor - col_h + h * 0.02, u - w + pitch * 0.72, floor)
    gaps.rect(u + w - pitch * 0.72, floor - col_h + h * 0.02, u + w - pitch * 0.22, floor)
    top = floor - col_h
    pen.rect(u - w * 1.02, top - h * 0.14, u + w * 1.02, top)
    pen.poly([(u - w * 1.06, top - h * 0.14), (u + w * 1.06, top - h * 0.14), (u, top - h * 0.36)])
    roof.poly([(u - w * 0.86, top - h * 0.16), (u + w * 0.86, top - h * 0.16), (u, top - h * 0.31)])


def _aqueduct(pen: Pen, water: Pen, u0: float, u1: float, v_top: float, v_foot: float, span: float) -> None:
    """An aqueduct: two tiers of arches, and the water channel on the top.
    The arches are cut out of the drawing (`value` 0), so draw it on a
    drawing of its own."""
    height = v_foot - v_top
    pen.rect(u0, v_top, u1, v_foot)
    water.rect(u0, v_top - 0.002, u1, v_top + height * 0.03)
    mid = v_top + height * 0.42
    for t0, t1, s in ((v_top + height * 0.08, mid - height * 0.04, span * 0.5), (mid + height * 0.04, v_foot + 0.01, span)):
        u = u0 + s * 0.5
        while u < u1 - s * 0.3:
            half = s * 0.36
            spring = t0 + half * 1.1
            pen.rect(u - half, spring, u + half, t1, value=0)
            pen.ellipse(u, spring, half, half * 1.1, value=0)
            u += s


def _trireme(pen: Pen, oars: Pen, sail: Pen, u: float, v: float, s: float) -> None:
    """A trireme: a long low hull with a ram at the bow and a curl at the
    stern, a bank of oars, and a square sail on one mast."""
    pen.poly([(u - s, v - s * 0.06), (u + s * 0.9, v - s * 0.06), (u + s * 1.08, v + s * 0.01), (u + s * 0.86, v + s * 0.04), (u - s * 0.8, v + s * 0.04)])
    pen.line([(u - s, v - s * 0.06), (u - s * 1.10, v - s * 0.16), (u - s * 1.02, v - s * 0.22)], s * 0.02)
    for k in range(13):
        x = u - s * 0.7 + k * s * 0.12
        oars.line([(x, v), (x - s * 0.06, v + s * 0.14)], s * 0.008)
    pen.rect(u - s * 0.012, v - s * 0.52, u + s * 0.012, v - s * 0.06)
    sail.poly([(u - s * 0.26, v - s * 0.48), (u + s * 0.26, v - s * 0.48), (u + s * 0.22, v - s * 0.16), (u - s * 0.22, v - s * 0.16)])


def _olive(trunk: Pen, crown: Pen, rng, u: float, v: float, h: float) -> None:
    """An olive tree: a short trunk that twists, and a wide crown in lumps."""
    pts = [(u, v + 0.02)]
    x, y = u, v
    for _ in range(5):
        x += rng.uniform(-0.012, 0.012)
        y -= h * 0.11
        pts.append((x, y))
    trunk.line(pts, h * 0.07)
    for side in (-1.0, 1.0):
        trunk.line([pts[3], (x + side * h * 0.22, y - h * 0.12)], h * 0.035)
    cy = y - h * 0.22
    for _ in range(14):
        crown.ellipse(x + rng.uniform(-h * 0.42, h * 0.42), cy + rng.uniform(-h * 0.18, h * 0.12), h * rng.uniform(0.10, 0.17), h * rng.uniform(0.07, 0.11))


def _cypress(pen: Pen, u: float, v: float, h: float, w: float) -> None:
    pen.poly([(u - w * 0.3, v + 0.005), (u + w * 0.3, v + 0.005), (u + w, v - h * 0.45), (u + w * 0.5, v - h * 0.85), (u, v - h), (u - w * 0.5, v - h * 0.85), (u - w, v - h * 0.45)])


def _column(pen: Pen, flutes: Pen, u: float, v: float, h: float, w: float, broken: float = 0.0) -> None:
    """A Doric column on its foot. `broken` more than 0 breaks off its top
    at a slant, and it has no capital."""
    top = v - h
    if broken > 0.0:
        pen.poly([(u - w, v + 0.02), (u + w, v + 0.02), (u + w * 0.92, top + broken), (u + w * 0.1, top + broken * 0.3), (u - w * 0.5, top + broken * 0.8), (u - w * 0.92, top)])
    else:
        pen.poly([(u - w, v + 0.02), (u + w, v + 0.02), (u + w * 0.86, top), (u - w * 0.86, top)])
        pen.poly([(u - w * 0.86, top), (u + w * 0.86, top), (u + w * 1.25, top - h * 0.04), (u - w * 1.25, top - h * 0.04)])
        pen.rect(u - w * 1.35, top - h * 0.075, u + w * 1.35, top - h * 0.04)
    for k in (-0.55, -0.1, 0.35):
        flutes.rect(u + w * k - w * 0.06, top + (broken if broken else 0.0), u + w * k + w * 0.06, v + 0.02)


# -- shapes of the Silk Road ------------------------------------------------


def _camel(pen: Pen, u: float, v: float, s: float, facing: float = 1.0, load: bool = True) -> None:
    """A camel that walks, seen from the side, its feet on `v`: a body with
    a hump, four legs, and a long neck. `load` puts packs on its back."""
    f = facing
    pen.ellipse(u, v - s * 0.62, s * 0.34, s * 0.16)
    pen.ellipse(u - f * s * 0.04, v - s * 0.78, s * 0.16, s * 0.14)
    for dx, swing in ((-0.24, -0.05), (-0.14, 0.05), (0.16, -0.04), (0.26, 0.05)):
        pen.line([(u + f * s * dx, v - s * 0.58), (u + f * s * (dx + swing * 0.5), v - s * 0.30), (u + f * s * (dx + swing), v)], s * 0.05)
    pen.line([(u + f * s * 0.28, v - s * 0.66), (u + f * s * 0.42, v - s * 0.72), (u + f * s * 0.48, v - s * 0.92)], s * 0.08)
    pen.ellipse(u + f * s * 0.54, v - s * 0.94, s * 0.08, s * 0.045)
    if load:
        pen.rect(u - s * 0.20, v - s * 0.98, u + s * 0.12, v - s * 0.80)
        pen.ellipse(u - s * 0.04, v - s * 0.99, s * 0.14, s * 0.05)


def _pagoda(pen: Pen, u: float, v: float, w: float, h: float, storeys: int = 5) -> None:
    """A pagoda: storeys that get narrower as they go up, each with eaves
    that turn up at the ends, and a spire with rings on the top."""
    storey = h * 0.82 / storeys
    base = v
    for k in range(storeys):
        half = w * (1.0 - k * 0.11)
        top = base - storey
        pen.rect(u - half * 0.62, top + storey * 0.28, u + half * 0.62, base)
        eave = top + storey * 0.30
        pen.poly([(u - half * 1.12, eave - storey * 0.20), (u - half * 0.95, eave), (u + half * 0.95, eave), (u + half * 1.12, eave - storey * 0.20), (u + half * 0.70, eave - storey * 0.12), (u, eave - storey * 0.34), (u - half * 0.70, eave - storey * 0.12)])
        base = top + storey * 0.06
    pen.rect(u - w * 0.03, base - h * 0.18, u + w * 0.03, base)
    for k in range(4):
        pen.ellipse(u, base - h * 0.04 - k * h * 0.035, w * 0.08 * (1.0 - k * 0.15), h * 0.006)


def _wall(pen: Pen, towers: Pen, line: np.ndarray, u0: float, u1: float, height: float, merlon: float, tower_at: tuple[float, ...]) -> None:
    """The Great Wall on a ridge: a band that follows the ridge line from
    `u0` to `u1`, with merlons on its top and towers at `tower_at`."""
    pts_top = [(u, _at(line, u) - height) for u in np.linspace(u0, u1, 80)]
    pts_foot = [(u, _at(line, u) + height * 0.3) for u in np.linspace(u1, u0, 80)]
    pen.poly(pts_top + pts_foot)
    u = u0
    while u < u1:
        y = _at(line, u) - height
        pen.rect(u, y - merlon, u + merlon * 0.9, y + 0.001)
        u += merlon * 2.0
    for t in tower_at:
        y = _at(line, t)
        towers.rect(t - height * 1.1, y - height * 2.6, t + height * 1.1, y + height * 0.3)
        towers.poly([(t - height * 1.4, y - height * 2.6), (t + height * 1.4, y - height * 2.6), (t + height * 1.1, y - height * 3.1), (t - height * 1.1, y - height * 3.1)])


def _pointed_arch(pen: Pen, u: float, v_foot: float, w: float, h: float, value: int = 255) -> None:
    """A pointed arch from the foot `v_foot` up: two sides and a point."""
    spring = v_foot - h * 0.62
    pts = [(u - w, v_foot), (u - w, spring)]
    for k in range(1, 9):
        t = k / 8.0
        pts.append((u - w + w * t, spring - (h - h * 0.62) * math.sin(t * math.pi * 0.5)))
    for k in range(1, 9):
        t = k / 8.0
        pts.append((u + w * t, spring - (h - h * 0.62) * math.cos(t * math.pi * 0.5)))
    pts += [(u + w, v_foot)]
    pen.poly(pts, value)


# -- shapes of the Steppe ---------------------------------------------------


def _ger(pen: Pen, door: Pen, u: float, v: float, w: float) -> None:
    """A ger: a round wall of felt and a low roof like a cone, the smoke ring
    at its crown, and an orange door."""
    h = w * 0.55
    pen.rect(u - w, v - h, u + w, v)
    pen.poly([(u - w * 1.04, v - h), (u + w * 1.04, v - h), (u + w * 0.18, v - h * 1.75), (u - w * 0.18, v - h * 1.75)])
    pen.rect(u - w * 0.14, v - h * 1.85, u + w * 0.14, v - h * 1.72)
    door.rect(u - w * 0.18, v - h * 0.78, u + w * 0.18, v)


def _horse(pen: Pen, u: float, v: float, s: float, facing: float = 1.0, graze: bool = False) -> None:
    """A small sturdy horse of the steppe, its feet on `v`."""
    f = facing
    pen.ellipse(u, v - s * 0.55, s * 0.32, s * 0.15)
    for dx in (-0.24, -0.16, 0.18, 0.26):
        pen.line([(u + f * s * dx, v - s * 0.50), (u + f * s * dx, v)], s * 0.055)
    if graze:
        pen.line([(u + f * s * 0.26, v - s * 0.58), (u + f * s * 0.46, v - s * 0.18)], s * 0.12)
        pen.ellipse(u + f * s * 0.48, v - s * 0.12, s * 0.06, s * 0.08)
    else:
        pen.line([(u + f * s * 0.24, v - s * 0.60), (u + f * s * 0.40, v - s * 0.88)], s * 0.12)
        pen.ellipse(u + f * s * 0.48, v - s * 0.86, s * 0.10, s * 0.055)
    pen.line([(u - f * s * 0.30, v - s * 0.60), (u - f * s * 0.42, v - s * 0.30)], s * 0.05)


def _eagle(pen: Pen, u: float, v: float, s: float) -> None:
    """A golden eagle that soars: broad wings with the tips spread as
    fingers, a fan of a tail."""
    pen.ellipse(u, v, s * 0.16, s * 0.05)
    for side in (-1.0, 1.0):
        pen.poly([(u, v - s * 0.02), (u + side * s * 0.55, v - s * 0.14), (u + side * s * 1.0, v - s * 0.08), (u + side * s * 0.96, v + s * 0.02), (u + side * s * 0.5, v + s * 0.04), (u, v + s * 0.04)])
        for k in range(4):
            x = u + side * s * (0.82 + k * 0.05)
            pen.line([(x, v - s * 0.04), (x + side * s * 0.10, v - s * 0.12 + k * s * 0.04)], s * 0.025)
    pen.poly([(u - s * 0.06, v + s * 0.02), (u + s * 0.06, v + s * 0.02), (u + s * 0.10, v + s * 0.16), (u - s * 0.10, v + s * 0.16)])


def _ovoo(pen: Pen, scarves: Pen, u: float, v: float, h: float) -> None:
    """An ovoo: a cairn of stones, a bundle of poles in it, and blue scarves
    tied on the poles that hang and blow."""
    for k in range(6):
        y = v - k * h * 0.07
        w = h * (0.34 - k * 0.05)
        pen.ellipse(u + (k % 2 - 0.5) * h * 0.03, y, w, h * 0.055)
    tops = []
    for k in range(5):
        top = (u + (k - 2) * h * 0.07, v - h * (0.86 + 0.06 * (k % 2)))
        pen.line([(u + (k - 2) * h * 0.015, v - h * 0.3), top], h * 0.012)
        tops.append(top)
    for k, (x, y) in enumerate(tops):
        for j in range(3):
            y0 = y + h * (0.08 + j * 0.16)
            x0 = u + (x - u) * (1.0 - (0.08 + j * 0.16))
            side = 1.0 if (k + j) % 2 else -1.0
            scarves.poly([(x0, y0), (x0 + side * h * 0.05, y0 + h * 0.03), (x0 + side * h * 0.06, y0 + h * 0.13), (x0 + side * h * 0.01, y0 + h * 0.10)])


def _tug(pen: Pen, u: float, v: float, h: float) -> None:
    """A tug: a standard of horse tails on a pole. A ring of hair hangs from
    a disc under the trident on its top."""
    pen.rect(u - h * 0.008, v - h, u + h * 0.008, v + 0.02)
    pen.ellipse(u, v - h * 0.84, h * 0.045, h * 0.016)
    pen.poly([(u - h * 0.04, v - h * 0.84), (u + h * 0.04, v - h * 0.84), (u + h * 0.07, v - h * 0.62), (u + h * 0.02, v - h * 0.58), (u - h * 0.02, v - h * 0.58), (u - h * 0.07, v - h * 0.62)])
    for k in range(9):
        x = u + (k - 4) * h * 0.016
        pen.line([(x, v - h * 0.82), (x + (k - 4) * h * 0.006, v - h * 0.56 + (k % 3) * h * 0.02)], h * 0.008)
    pen.line([(u - h * 0.035, v - h * 0.97), (u - h * 0.035, v - h * 0.90), (u + h * 0.035, v - h * 0.90), (u + h * 0.035, v - h * 0.97)], h * 0.008)
    pen.poly([(u - h * 0.008, v - h), (u + h * 0.008, v - h), (u, v - h * 1.04)])


# -- shapes of the Monsoon Coast --------------------------------------------


def _mud_tower(pen: Pen, spikes: Pen, u: float, v: float, w: float, h: float) -> None:
    """A tower of mudbrick: it gets narrower as it goes up, its top is round,
    and rows of toron (beams of palm wood) stand out of its sides."""
    pen.poly([(u - w, v), (u + w, v), (u + w * 0.55, v - h), (u - w * 0.55, v - h)])
    pen.ellipse(u, v - h, w * 0.55, w * 0.3)
    pen.rect(u - w * 0.06, v - h - w * 0.62, u + w * 0.06, v - h)
    pen.ellipse(u, v - h - w * 0.64, w * 0.11)
    for row in range(5):
        y = v - h * (0.16 + row * 0.18)
        half = w * (1.0 - (0.16 + row * 0.18) * 0.45)
        for side in (-1.0, 1.0):
            spikes.rect(u + side * half - w * 0.18, y - w * 0.035, u + side * half + w * 0.18, y + w * 0.035)


def _dhow(pen: Pen, sail: Pen, u: float, v: float, s: float, facing: float = 1.0) -> None:
    """A dhow: a hull with a high stern and a long raked bow, and a lateen
    sail (a big triangle on a yard that slopes)."""
    f = facing
    pen.poly([(u - f * s * 0.55, v - s * 0.16), (u + f * s * 0.70, v - s * 0.10), (u + f * s * 0.42, v + s * 0.04), (u - f * s * 0.40, v + s * 0.04)])
    pen.rect(u - s * 0.01, v - s * 0.78, u + s * 0.01, v - s * 0.10)
    yard_a, yard_b = (u - f * s * 0.48, v - s * 0.30), (u + f * s * 0.40, v - s * 0.98)
    pen.line([yard_a, yard_b], s * 0.012)
    sail.poly([yard_a, yard_b, (u + f * s * 0.30, v - s * 0.16)])


def _coral_house(pen: Pen, holes: Pen, u: float, v: float, w: float, h: float) -> None:
    """A house of coral stone, white with lime: a flat roof with a low wall
    round it, and small dark windows."""
    pen.rect(u - w, v - h, u + w, v)
    pen.rect(u - w * 1.04, v - h * 1.10, u - w * 0.70, v - h)
    pen.rect(u + w * 0.70, v - h * 1.10, u + w * 1.04, v - h)
    holes.rect(u - w * 0.5, v - h * 0.7, u - w * 0.3, v - h * 0.5)
    holes.rect(u + w * 0.25, v - h * 0.7, u + w * 0.45, v - h * 0.5)
    holes.rect(u - w * 0.12, v - h * 0.42, u + w * 0.12, v)


# -- shapes of the Age of Sail ----------------------------------------------


def _tall_ship(pen: Pen, sails: Pen, u: float, v: float, s: float, furled: bool = False) -> None:
    """A ship with three masts and square sails, its waterline on `v`."""
    pen.poly([(u - s * 0.50, v - s * 0.14), (u + s * 0.46, v - s * 0.12), (u + s * 0.40, v + s * 0.02), (u - s * 0.40, v + s * 0.02)])
    pen.rect(u - s * 0.52, v - s * 0.22, u - s * 0.34, v - s * 0.12)
    pen.line([(u + s * 0.44, v - s * 0.12), (u + s * 0.72, v - s * 0.26)], s * 0.012)
    for dx, h in ((-0.30, 0.78), (0.02, 0.96), (0.30, 0.74)):
        x = u + dx * s
        pen.rect(x - s * 0.007, v - s * h, x + s * 0.007, v - s * 0.12)
        for j in range(3):
            y = v - s * h + s * (0.06 + j * 0.22)
            wide = s * (0.10 + j * 0.03)
            pen.rect(x - wide, y - s * 0.006, x + wide, y + s * 0.006)
            if furled:
                sails.rect(x - wide * 0.9, y, x + wide * 0.9, y + s * 0.022)
            else:
                sails.poly([(x - wide * 0.96, y), (x + wide * 0.96, y), (x + wide * 1.02, y + s * 0.17), (x - wide * 1.02, y + s * 0.17)])
    pen.line([(u + s * 0.02, v - s * 0.96), (u + s * 0.72, v - s * 0.26)], s * 0.004)
    pen.line([(u + s * 0.02, v - s * 0.96), (u - s * 0.50, v - s * 0.22)], s * 0.004)


def _lighthouse(pen: Pen, bands: Pen, u: float, v: float, w: float, h: float) -> None:
    """A lighthouse: a tower that gets narrower as it goes up, bands round
    it, a gallery, the lantern room and a dome."""
    pen.poly([(u - w, v), (u + w, v), (u + w * 0.62, v - h), (u - w * 0.62, v - h)])
    pen.rect(u - w * 0.9, v - h - w * 0.10, u + w * 0.9, v - h)
    pen.rect(u - w * 0.45, v - h - w * 0.62, u + w * 0.45, v - h - w * 0.10)
    pen.ellipse(u, v - h - w * 0.62, w * 0.48, w * 0.30)
    for k in range(3):
        t0, t1 = 0.18 + k * 0.26, 0.30 + k * 0.26
        w0, w1 = w * (1.0 - t0 * 0.38), w * (1.0 - t1 * 0.38)
        bands.poly([(u - w0, v - h * t0), (u + w0, v - h * t0), (u + w1, v - h * t1), (u - w1, v - h * t1)])


def _gabled_house(pen: Pen, windows: Pen, rng, u: float, v: float, w: float, h: float) -> None:
    """A tall house of a harbour town with a stepped gable, and windows."""
    pen.rect(u - w, v - h, u + w, v)
    steps = 3
    for k in range(steps):
        sw = w * (1.0 - (k + 1) / (steps + 1))
        pen.rect(u - sw, v - h - (k + 1) * w * 0.32, u + sw, v - h - k * w * 0.32 + 0.001)
    for row in range(3):
        for col in (-0.5, 0.5):
            if rng.random() < 0.8:
                y = v - h * (0.25 + row * 0.28)
                windows.rect(u + col * w - w * 0.16, y - h * 0.08, u + col * w + w * 0.16, y + h * 0.04)


def _rigging(pen: Pen, u: float, v_foot: float, h: float, yards: tuple[float, ...], width: float) -> None:
    """A mast seen from near: a spar, its yards across it, and the shrouds
    with ratlines down to the deck at each side."""
    pen.rect(u - width, 0.0, u + width, v_foot)
    for k, y in enumerate(yards):
        half = 0.10 - k * 0.018
        pen.rect(u - half, y - width * 0.6, u + half, y + width * 0.6)
        pen.curve((u - half, y + width * 0.6), (u + half, y + width * 0.6), 0.012, width * 0.25)
    for side in (-1.0, 1.0):
        for k in range(4):
            pen.line([(u, yards[0] + 0.01), (u + side * (0.04 + k * 0.012), v_foot)], width * 0.18)
        for k in range(14):
            t = k / 14.0
            y = yards[0] + 0.02 + (v_foot - yards[0] - 0.02) * t
            pen.line([(u + side * 0.004, y), (u + side * (0.04 + 0.036 * t), y)], width * 0.14)
    del h


# -- shapes of the Industrial Age -------------------------------------------


def _mill(pen: Pen, windows: Pen, rng, u0: float, u1: float, v: float, h: float, floors: int, lit: float) -> None:
    """A cotton mill: a long block of brick with a low pitched roof and rows
    of tall windows, one row on each floor."""
    pen.rect(u0, v - h, u1, v)
    pen.poly([(u0 - 0.004, v - h), (u1 + 0.004, v - h), (u1 - h * 0.15, v - h * 1.14), (u0 + h * 0.15, v - h * 1.14)])
    window_grid(windows, rng, u0 + 0.004, v - h + h * 0.06, u1 - 0.004, v - h * 0.04, 0.012, h / floors, lit, 0.42, 0.58)


def _chimney(pen: Pen, u: float, v: float, w: float, h: float) -> None:
    """A mill chimney: a tall shaft that gets narrower as it goes up, with a
    band of brick near its top."""
    pen.poly([(u - w, v), (u + w, v), (u + w * 0.62, v - h), (u - w * 0.62, v - h)])
    pen.rect(u - w * 0.80, v - h - w * 0.6, u + w * 0.80, v - h)
    pen.rect(u - w * 0.72, v - h + w * 1.4, u + w * 0.72, v - h + w * 2.0)


def _viaduct(pen: Pen, u0: float, u1: float, v_deck: float, v_foot: float, span: float) -> None:
    """A railway viaduct: a deck on tall piers, round arches between them.
    The arches are cut out (`value` 0), so draw it on a drawing of its own."""
    pen.rect(u0, v_deck, u1, v_foot)
    pen.rect(u0, v_deck - 0.006, u1, v_deck)
    u = u0 + span * 0.5
    while u < u1:
        half = span * 0.36
        spring = v_deck + 0.018 + half
        pen.rect(u - half, spring, u + half, v_foot + 0.01, value=0)
        pen.ellipse(u, spring, half, half, value=0)
        u += span


def _train(pen: Pen, u: float, v: float, s: float, cars: int) -> tuple[float, float]:
    """A train that runs to the right on `v`: an engine with a tall stack and
    a cab, a tender, and carriages. Returns the top of its stack."""
    pen.rect(u, v - s * 0.32, u + s * 0.62, v - s * 0.06)
    pen.ellipse(u + s * 0.62, v - s * 0.19, s * 0.04, s * 0.13)
    pen.rect(u - s * 0.02, v - s * 0.52, u + s * 0.20, v - s * 0.06)
    pen.rect(u - s * 0.04, v - s * 0.56, u + s * 0.22, v - s * 0.50)
    stack = (u + s * 0.50, v - s * 0.32)
    pen.poly([(stack[0] - s * 0.04, stack[1]), (stack[0] + s * 0.04, stack[1]), (stack[0] + s * 0.07, stack[1] - s * 0.22), (stack[0] - s * 0.07, stack[1] - s * 0.22)])
    for k in range(4):
        pen.ellipse(u + s * (0.08 + k * 0.17), v - s * 0.06, s * 0.07)
    x = u - s * 0.06
    for k in range(cars + 1):
        length = s * (0.36 if k == 0 else 0.70)
        pen.rect(x - length, v - s * (0.30 if k == 0 else 0.40), x, v - s * 0.06)
        pen.ellipse(x - length * 0.22, v - s * 0.05, s * 0.05)
        pen.ellipse(x - length * 0.78, v - s * 0.05, s * 0.05)
        x -= length + s * 0.04
    return stack[0], stack[1] - s * 0.22


def _gas_lamp(pen: Pen, u: float, v: float, h: float) -> tuple[float, float]:
    """A gas lamp: a post of iron with a cross bar and a glass lantern on
    its top. Returns where its flame is."""
    pen.rect(u - h * 0.012, v - h, u + h * 0.012, v + 0.02)
    pen.rect(u - h * 0.03, v - h * 0.20, u + h * 0.03, v + 0.02)
    pen.rect(u - h * 0.06, v - h * 0.86, u + h * 0.06, v - h * 0.845)
    pen.poly([(u - h * 0.04, v - h), (u + h * 0.04, v - h), (u + h * 0.055, v - h * 1.10), (u - h * 0.055, v - h * 1.10)])
    pen.poly([(u - h * 0.065, v - h * 1.10), (u + h * 0.065, v - h * 1.10), (u, v - h * 1.17)])
    return u, v - h * 1.05


# ---------------------------------------------------------------------------
# 1. The Fertile Crescent: dawn over the river plain
# ---------------------------------------------------------------------------


def history_crescent(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = CRESCENT
    sun_at = (0.70, HORIZON - 0.015)
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, p["top"]), (0.26, p["mid"]), (0.46, p["pink"]), (HORIZON - 0.01, p["low"]), (HORIZON + 0.06, mix(p["low"], p["mud"], 0.5)), (1.0, p["mud_dark"])]))
        _sun(a, layer, *sun_at, 0.032, p["sun"], p["glow"], 0.65)
        # Long thin clouds, lit pink and gold from below by the sun.
        streaks = cloud_mask(a, "dawn streaks", 0.40, 0.11, cells=2.2, cover=0.34, soft=0.12, stretch=7.0)
        a.tint(layer, streaks, mix(p["mid"], p["pink"], 0.4), 0.55)
        a.light(layer, streaks * smoothstep(0.34, 0.47, a.v), p["glow"], 0.45)
        # The mountains far off at the edge of the plain.
        hills, _ = a.ridge("zagros", HORIZON - 0.02, 0.03, cells=3.0, octaves=4, sharp=0.5)
        a.tint(layer, hills, mix(p["far"], p["pink"], 0.5), 0.45)
        _textbook(a, layer)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far crescent")
        ground, line = a.ridge("plain", HORIZON + 0.022, 0.004, cells=3.0, octaves=3)
        image, pen = a.drawing()
        stair, stair_pen = a.drawing()
        holes, hole_pen = a.drawing()
        palms, palm_pen = a.drawing()
        # The ziggurat, and the town of mudbrick at its foot.
        zu = 0.42
        zv = _at(line, zu) + 0.004
        _ziggurat(pen, stair_pen, zu, zv, 0.13, 0.17)
        for _ in range(18):
            u = rng.choice([rng.uniform(0.22, 0.30), rng.uniform(0.54, 0.64)])
            w, h = rng.uniform(0.008, 0.016), rng.uniform(0.010, 0.024)
            _mud_house(pen, hole_pen, u, _at(line, u) + 0.004, w, h)
        # A wall round the town, with towers.
        pen.rect(0.20, _at(line, 0.2) - 0.010, 0.66, _at(line, 0.2) + 0.004)
        for u in (0.20, 0.31, 0.53, 0.66):
            pen.rect(u - 0.006, _at(line, u) - 0.018, u + 0.006, _at(line, u) + 0.004)
        # Date palms in groves along the canal.
        for u0, count in ((0.06, 4), (0.72, 3), (0.88, 4)):
            for k in range(count):
                u = u0 + k * 0.028 + rng.uniform(-0.008, 0.008)
                _date_palm(palm_pen, palm_pen, rng, u, _at(line, u) + 0.004, rng.uniform(0.045, 0.07), rng.uniform(-0.008, 0.008), 9)
        mask = np.maximum.reduce([ground, a.mask_of(image), a.mask_of(palms)])
        layer = solid(a, mask, mix(p["mud"], p["far"], 0.40), mix(p["mud_dark"], p["far"], 0.4), HORIZON - 0.12, HORIZON + 0.06, "mud", 0.06)
        a.put(layer, a.mask_of(palms), mix(p["palm"], p["far"], 0.30))
        a.shade(layer, a.mask_of(holes) * mask, 0.45)
        a.shade(layer, a.mask_of(stair, blur=0.3) * mask, 0.22)
        # Each tier of the ziggurat is lit on its top edge and its east side.
        tower = a.mask_of(image) * (np.abs(a.u - zu) < 0.14) * (a.v < zv)
        a.light(layer, a.rim(tower, -0.002, 0.0015, 0.3) * tower, p["glow"], 0.55)
        # The canal, and the fields of wheat in stripes on the plain.
        v0 = _at(line, 0.5) + 0.01
        a.put(layer, smoothstep(v0 + 0.012, v0 + 0.03, a.v) * ground, mix(p["wheat"], p["far"], 0.30), 0.70)
        canal = a.band(v0 + 0.006, 0.006, 0.8) * ground
        a.put(layer, canal, mix(p["river"], p["far"], 0.20))
        ripples = smoothstep(0.5, 0.75, a.noise("canal ripples", cells=60.0, octaves=2, stretch=8.0))
        a.light(layer, canal * ripples * a.spot(sun_at[0], v0, 0.25, 1.0, squash=2.0), p["sun"], 0.8)
        rows = (0.5 + 0.5 * np.sin((a.v - v0) * 700.0)) * smoothstep(v0 + 0.02, v0 + 0.04, a.v)
        a.shade(layer, rows * ground, 0.10)
        a.light(layer, a.rim(mask, -0.003, 0.0015, 0.6) * mask, p["glow"], 0.40)
        haze(a, layer, p["low"], 0.16, HORIZON + 0.04)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near crescent")
        image, pen = a.drawing()
        fronds, frond_pen = a.drawing()
        ground, _ = a.ridge("near field", 0.70, 0.010, cells=5.0, octaves=3)
        # Date palms at the sides.
        for u, h, lean in ((0.05, 0.46, 0.03), (0.15, 0.34, -0.02), (0.86, 0.36, 0.025), (0.95, 0.48, -0.03)):
            _date_palm(pen, frond_pen, rng, u, 0.72, h, lean)
        # A low wall of mudbrick at the left, its top worn into steps.
        pen.poly([(0.0, 0.74), (0.0, 0.58), (0.10, 0.58), (0.12, 0.61), (0.19, 0.61), (0.21, 0.64), (0.25, 0.65), (0.26, 0.74)])
        # A shadoof at the right, over the canal.
        _shadoof(pen, 0.77, 0.70, 0.12)
        # Sheaves in the field and reeds by the canal.
        for u in (0.29, 0.318):
            _sheaf(pen, u, 0.700, rng.uniform(0.05, 0.06))
        _reeds(pen, rng, 0.62, 0.67, 0.70, 0.06, 18)
        _reeds(pen, rng, 0.34, 0.38, 0.70, 0.05, 12)
        mask = np.maximum.reduce([ground, a.mask_of(image), a.mask_of(fronds)])
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.40), p["near"], 0.30, 0.74, "mud near", 0.10)
        a.put(layer, a.mask_of(fronds), mix(p["palm"], p["near"], 0.40))
        # The courses of the wall.
        wall = a.mask_of(image) * (a.u < 0.27) * (a.v < 0.72) * (a.v > 0.575)
        courses = ((a.v * 140.0) % 1.0 < 0.12).astype(np.float32)
        a.put(layer, wall, mix(p["mud_dark"], p["near"], 0.45))
        a.shade(layer, wall * courses, 0.30)
        a.light(layer, a.rim(mask, -0.003, 0.002, 0.4) * mask, p["glow"], 0.38)
        a.shade(layer, a.rim(mask, 0.004, -0.003, 1.0) * mask, 0.22)
        haze(a, layer, p["far"], 0.08, 0.73)
        return layer
    layer = _air(a, p, "dawn mist", p["glow"], 0.24, p["near"], 0.26)
    a.put(layer, shafts(a, "dawn shafts", 4, -0.12, 0.0, 0.8, 0.05), p["glow"], 0.10)
    return layer


def crescent_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Wheat that stands from below at a few places, each stalk with its
    ear. Nothing hangs."""
    del layer_lights
    rng = art_.rand("crescent foreground")
    for k in range(4):
        u0 = (k + rng.uniform(0.2, 0.8)) / 4.0
        for _ in range(9):
            u = u0 + rng.uniform(-0.03, 0.03)
            top = REST_BOTTOM - rng.uniform(0.0, 0.016)
            lean = rng.uniform(-0.01, 0.01)
            pen.line([(u, 1.0), (u + lean * 0.5, top + 0.02), (u + lean, top)], 0.0018)
            for j in range(4):
                y = top + j * 0.005
                pen.ellipse(u + lean + (0.002 if j % 2 else -0.002), y, 0.0018, 0.003)


# ---------------------------------------------------------------------------
# 2. The Nile: a red sun over the pyramids
# ---------------------------------------------------------------------------


def history_nile(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = NILE
    sun_at = (0.30, 0.47)
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, p["top"]), (0.30, mix(p["top"], p["mid"], 0.55)), (0.48, p["mid"]), (HORIZON - 0.01, p["low"]), (HORIZON + 0.06, mix(p["sand"], p["low"], 0.4)), (1.0, p["sand"])]))
        # The red sun in the dust, cut by thin bands of haze.
        a.light(layer, a.spot(*sun_at, 0.50, 2.0, squash=1.6), p["glow"], 0.55)
        disc, disc_pen = a.drawing()
        disc_pen.ellipse(*sun_at, 0.075)
        sun = a.mask_of(disc, blur=0.8)
        a.put(layer, sun, mix(p["sun"], p["glow"], 0.15), 0.92)
        a.light(layer, sun * a.spot(sun_at[0] - 0.02, sun_at[1] - 0.02, 0.07, 1.5), p["glow"], 0.35)
        bands = cloud_mask(a, "dust bands", 0.48, 0.07, cells=2.0, cover=0.40, soft=0.10, stretch=9.0)
        a.tint(layer, bands, mix(p["mid"], p["top"], 0.3), 0.45)
        # Dunes far off on the west bank.
        dunes, _ = a.ridge("far dunes", HORIZON - 0.01, 0.018, cells=4.0, octaves=3, sharp=0.6)
        a.tint(layer, dunes, mix(p["far"], p["low"], 0.4), 0.55)
        _textbook(a, layer)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far nile")
        ground, line = a.ridge("desert", HORIZON + 0.012, 0.006, cells=2.5, octaves=3)
        image, pen = a.drawing()
        lit, lit_pen = a.drawing()
        tip, tip_pen = a.drawing()
        green, green_pen = a.drawing()
        # The three pyramids on the plateau, the face to the sun lit.
        for u, half, h in ((0.60, 0.075, 0.10), (0.72, 0.095, 0.13), (0.84, 0.055, 0.07)):
            _pyramid(pen, lit_pen, u, _at(line, u) + 0.004, half, h)
        _obelisk(pen, tip_pen, 0.44, _at(line, 0.44) + 0.004, 0.007, 0.13)
        # The green strip by the river: palms and fields.
        for k in range(22):
            u = k * 0.048 + rng.uniform(-0.01, 0.01)
            if rng.random() < 0.6:
                _date_palm(green_pen, green_pen, rng, u, HORIZON + 0.034, rng.uniform(0.026, 0.05), rng.uniform(-0.006, 0.006), 9)
        green_pen.rect(0.0, HORIZON + 0.026, 1.0, HORIZON + 0.040)
        mask = np.maximum.reduce([ground, a.mask_of(image), a.mask_of(green)])
        layer = solid(a, mask, mix(p["sandstone"], p["far"], 0.40), mix(p["sand"], p["far"], 0.35), HORIZON - 0.12, HORIZON + 0.06, "sand", 0.05)
        a.put(layer, a.mask_of(lit, blur=0.3) * mask, mix(p["sandstone"], p["glow"], 0.35), 0.55)
        a.shade(layer, a.mask_of(image) * (1.0 - a.mask_of(lit)) * (a.v < HORIZON + 0.01), 0.12)
        a.put(layer, a.mask_of(tip, blur=0.3), p["gold"])
        a.put(layer, a.mask_of(green), mix(p["papyrus"], p["far"], 0.35))
        # The Nile, with the red sun in it.
        river = a.band(HORIZON + 0.055, 0.016, 0.5) * ground
        a.put(layer, river, mix(p["nile"], p["far"], 0.30))
        ripples = smoothstep(0.55, 0.75, a.noise("nile ripples", cells=60.0, octaves=2, stretch=8.0))
        path = np.clip(1.0 - np.abs(a.u - sun_at[0]) / 0.05, 0.0, 1.0)
        a.light(layer, river * path * ripples, p["glow"], 0.75)
        a.light(layer, a.rim(mask, 0.003, 0.002, 0.6) * mask, p["glow"], 0.40)
        haze(a, layer, p["low"], 0.22, HORIZON + 0.04)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near nile")
        image, pen = a.drawing()
        reeds, reed_pen = a.drawing()
        band, band_pen = a.drawing()
        ground, _ = a.ridge("near bank", 0.70, 0.008, cells=5.0, octaves=3)
        # A column with a lotus capital at the left, a broken one at the right.
        _lotus_column(pen, band_pen, 0.15, 0.72, 0.40, 0.026)
        pen.rect(0.82, 0.61, 0.86, 0.74)
        pen.poly([(0.82, 0.61), (0.835, 0.595), (0.85, 0.605), (0.86, 0.59), (0.86, 0.61)])
        # Papyrus in clumps at the sides, and a palm.
        _papyrus(reed_pen, rng, 0.06, 0.72, 0.34, 9, 0.03)
        _papyrus(reed_pen, rng, 0.22, 0.72, 0.16, 6, 0.025)
        _papyrus(reed_pen, rng, 0.77, 0.72, 0.20, 7, 0.03)
        _date_palm(pen, reed_pen, rng, 0.93, 0.72, 0.44, -0.03)
        mask = np.maximum.reduce([ground, a.mask_of(image), a.mask_of(reeds)])
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.45), p["near"], 0.30, 0.74, "sandstone near", 0.08)
        a.put(layer, a.mask_of(reeds) * (a.v < 0.68), mix(p["papyrus"], p["near"], 0.45))
        a.put(layer, a.mask_of(band, blur=0.3) * a.mask_of(image), mix(p["lapis"], p["near"], 0.30))
        a.light(layer, a.rim(mask, 0.003, 0.002, 0.4) * mask, p["glow"], 0.36)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.22)
        haze(a, layer, p["far"], 0.08, 0.73)
        return layer
    return _air(a, p, "dust", p["low"], 0.26, p["near"], 0.28)


def nile_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Heads of papyrus that stand from below at a few places."""
    del layer_lights
    rng = art_.rand("nile foreground")
    for k in range(3):
        u = (k + rng.uniform(0.2, 0.8)) / 3.0
        for _ in range(4):
            x = u + rng.uniform(-0.02, 0.02)
            top = REST_BOTTOM - rng.uniform(0.0, 0.012)
            pen.line([(x, 1.0), (x + rng.uniform(-0.006, 0.006), top)], 0.0026)
            for j in range(9):
                end = polar(x, top, 0.016, -160.0 + j * 17.5)
                pen.line([(x, top), end], 0.0013)


# ---------------------------------------------------------------------------
# 3. The Classical Shore: noon on the Mediterranean
# ---------------------------------------------------------------------------


def history_classical(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = CLASSICAL
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, p["top"]), (0.32, p["mid"]), (HORIZON - 0.005, p["low"]), (HORIZON, p["sea_light"]), (HORIZON + 0.06, p["sea"]), (1.0, scale(p["sea"], 0.8))]))
        # The sun is high, over the band a view shows: only its light is seen.
        a.light(layer, a.spot(0.80, 0.08, 0.55, 2.0), p["sun"], 0.55)
        # A few small white clouds.
        _heaps(a, layer, "noon clouds", ((0.14, 0.40, 0.05, 0.035), (0.50, 0.33, 0.035, 0.025), (0.86, 0.45, 0.06, 0.04)), p["sun"], mix(p["mid"], p["low"], 0.55))
        # Islands far out on the horizon.
        isles, _ = a.ridge("isles", HORIZON - 0.004, 0.012, cells=5.0, octaves=4, sharp=0.6)
        a.tint(layer, isles * (a.v < HORIZON + 0.002), mix(p["far"], p["low"], 0.35), 0.75)
        # The wine-dark sea: glitter under the sun, darker far out.
        below = smoothstep(HORIZON, HORIZON + 0.004, a.v)
        glitter = smoothstep(0.62, 0.80, a.noise("sea glitter", cells=80.0, octaves=2, stretch=6.0))
        a.light(layer, below * glitter * a.spot(0.72, HORIZON + 0.06, 0.35, 1.0, squash=2.5), p["sun"], 0.55)
        _textbook(a, layer, 0.06)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far shore")
        # The hill of the temple at the left, and a low shore that runs on.
        crest = HORIZON + 0.03 - 0.13 * np.exp(-(((a.u[0] - 0.26) / 0.16) ** 2))
        hill = np.clip((a.v - crest[None, :]) * a.n + 0.5, 0.0, 1.0)
        shore, line = a.ridge("shore", HORIZON + 0.028, 0.006, cells=4.0, octaves=3)
        shore = shore * smoothstep(0.70, 0.62, a.u) + smoothstep(HORIZON + 0.05, HORIZON + 0.052, a.v)
        ground = np.clip(np.maximum(hill, shore), 0.0, 1.0)
        marble, marble_pen = a.drawing()
        gaps, gap_pen = a.drawing()
        roof, roof_pen = a.drawing()
        trees, tree_pen = a.drawing()
        arches, arch_pen = a.drawing()
        water, water_pen = a.drawing()
        ship, ship_pen = a.drawing()
        oars, oar_pen = a.drawing()
        sail, sail_pen = a.drawing()
        tv = float(crest[int(0.26 * a.n)]) + 0.006
        _temple(marble_pen, gap_pen, roof_pen, 0.26, tv, 0.075, 0.085)
        for u in (0.13, 0.15, 0.37, 0.39, 0.42):
            _cypress(tree_pen, u, float(crest[int(u * a.n)]) + 0.006, rng.uniform(0.04, 0.06), 0.006)
        # The aqueduct strides from the hill to the right and stops, broken.
        _aqueduct(arch_pen, water_pen, 0.40, 0.66, HORIZON - 0.06, HORIZON + 0.04, 0.05)
        arch_pen.rect(0.655, HORIZON - 0.06, 0.672, HORIZON + 0.04, value=0)
        arch_pen.poly([(0.64, HORIZON - 0.06), (0.655, HORIZON - 0.06), (0.655, HORIZON - 0.02), (0.645, HORIZON - 0.04)], value=0)
        # The trireme out on the sea.
        _trireme(ship_pen, oar_pen, sail_pen, 0.77, HORIZON + 0.018, 0.06)
        aqueduct = a.mask_of(arches)
        stone = np.maximum(a.mask_of(marble), aqueduct)
        mask = np.maximum.reduce([ground, stone, a.mask_of(trees), a.mask_of(ship), a.mask_of(oars)])
        layer = solid(a, mask, mix(p["land"], p["far"], 0.30), mix(p["olive"], p["far"], 0.25), HORIZON - 0.10, HORIZON + 0.05, "far land", 0.06)
        # Groves of olive on the land: small round trees in rows.
        grove, grove_pen = a.drawing()
        for row in range(14):
            y = HORIZON - 0.05 + row * 0.008
            for x in np.arange(rng.uniform(0.0, 0.01), 1.0, 0.012):
                if float(crest[min(a.n - 1, int(x * a.n))]) < y - 0.006 and x < 0.40 and rng.random() < 0.4:
                    grove_pen.ellipse(x + rng.uniform(-0.002, 0.002), y, 0.0036, 0.0028)
        a.put(layer, a.mask_of(grove, blur=0.5) * ground * (1.0 - stone), mix(p["olive_dark"], p["far"], 0.35), 0.45)
        a.put(layer, stone, mix(p["marble"], p["far"], 0.20))
        a.shade(layer, a.mask_of(gaps, blur=0.3) * stone, 0.30)
        a.put(layer, a.mask_of(roof, blur=0.3), mix(p["terracotta"], p["far"], 0.40), 0.6)
        a.shade(layer, a.rim(aqueduct, -0.003, -0.002, 0.3) * aqueduct, 0.25)
        a.light(layer, a.mask_of(water, blur=0.3) * aqueduct, p["sea_light"], 0.5)
        a.put(layer, a.mask_of(trees), mix(p["olive_dark"], p["far"], 0.35))
        a.put(layer, a.mask_of(ship), mix(p["olive_dark"], p["far"], 0.25))
        a.put(layer, a.mask_of(oars), mix(p["olive_dark"], p["far"], 0.35))
        a.put(layer, a.mask_of(sail, blur=0.3), mix(p["marble"], p["terracotta"], 0.3))
        a.light(layer, a.rim(mask, 0.002, 0.003, 0.5) * mask, p["sun"], 0.40)
        haze(a, layer, p["low"], 0.12, None)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near shore")
        image, pen = a.drawing()
        crowns, crown_pen = a.drawing()
        flutes, flute_pen = a.drawing()
        ground, _ = a.ridge("near shore", 0.70, 0.010, cells=5.0, octaves=3)
        # Olive trees at the sides.
        _olive(pen, crown_pen, rng, 0.08, 0.72, 0.34)
        _olive(pen, crown_pen, rng, 0.90, 0.72, 0.30)
        # A column that stands, one that is broken, and a drum on the ground.
        _column(pen, flute_pen, 0.19, 0.72, 0.36, 0.020)
        _column(pen, flute_pen, 0.80, 0.72, 0.20, 0.022, broken=0.03)
        pen.ellipse(0.25, 0.70, 0.030, 0.016)
        pen.rect(0.25, 0.684, 0.30, 0.716)
        mask = np.maximum.reduce([ground, a.mask_of(image), a.mask_of(crowns)])
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.45), p["near"], 0.30, 0.74, "near stone", 0.08)
        leaves = a.mask_of(crowns)
        a.put(layer, leaves, mix(p["olive"], p["near"], 0.45))
        a.light(layer, leaves * smoothstep(0.55, 0.75, a.noise("olive leaves", cells=40.0, octaves=2)), p["olive"], 0.25)
        cols = a.mask_of(image) * ((np.abs(a.u - 0.19) < 0.03) | (np.abs(a.u - 0.80) < 0.03)) * (a.v < 0.72)
        a.put(layer, cols, mix(p["marble_shade"], p["near"], 0.40))
        a.shade(layer, a.mask_of(flutes) * cols, 0.25)
        a.light(layer, a.rim(mask, 0.002, 0.003, 0.4) * mask, p["sun"], 0.38)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.22)
        haze(a, layer, p["far"], 0.08, 0.73)
        return layer
    return _air(a, p, "sea air", p["low"], 0.20, p["near"], 0.24)


# ---------------------------------------------------------------------------
# 4. The Silk Road: a hot afternoon over the dunes
# ---------------------------------------------------------------------------


def history_silk(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = SILK
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, p["top"]), (0.30, mix(p["top"], p["mid"], 0.6)), (0.48, p["mid"]), (HORIZON - 0.01, p["low"]), (HORIZON + 0.06, p["dune"]), (1.0, p["dune_shadow"])]))
        _sun(a, layer, 0.64, 0.30, 0.028, p["sun"], p["low"], 0.70)
        # The heat of the afternoon: a pale band of air over the sand.
        a.light(layer, a.band(HORIZON - 0.02, 0.05, 1.0), p["low"], 0.25)
        # Mountains with snow far off.
        peaks, line = a.ridge("tian shan", HORIZON - 0.03, 0.035, cells=4.0, octaves=5, sharp=0.8)
        a.tint(layer, peaks, mix(p["far"], p["mid"], 0.55), 0.55)
        snow = peaks * smoothstep(0.012, 0.0, a.v - line[None, :])
        a.tint(layer, snow * (line[None, :] < HORIZON - 0.04), p["sun"], 0.55)
        _textbook(a, layer, 0.07)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far silk")
        # Dunes with sharp crests: the side to the sun is light.
        dunes, line = a.ridge("dunes", HORIZON + 0.02, 0.025, cells=3.0, octaves=3, sharp=0.9)
        ridge, rline = a.ridge("wall hills", HORIZON - 0.005, 0.03, cells=3.0, octaves=4, sharp=0.4)
        ridge = ridge * smoothstep(0.56, 0.64, a.u)
        image, pen = a.drawing()
        towers, tower_pen = a.drawing()
        caravan, caravan_pen = a.drawing()
        oasis, oasis_pen = a.drawing()
        # The Great Wall on the hills at the right, and a pagoda before it.
        _wall(pen, tower_pen, rline, 0.60, 1.0, 0.008, 0.004, (0.68, 0.80, 0.93))
        _pagoda(pen, 0.76, _at(line, 0.76) + 0.004, 0.024, 0.15)
        # The caravan on the crest of a dune: camels nose to tail.
        u = 0.12
        for k in range(8):
            _camel(caravan_pen, u, _at(line, u) + 0.002, 0.034, 1.0, load=k % 3 != 2)
            u += 0.040
        # An oasis in a hollow: a pool and palms.
        oasis_pen.ellipse(0.52, HORIZON + 0.045, 0.06, 0.008)
        for k in range(5):
            x = 0.47 + k * 0.024 + rng.uniform(-0.006, 0.006)
            _date_palm(pen, pen, rng, x, HORIZON + 0.044, rng.uniform(0.04, 0.06), rng.uniform(-0.008, 0.008), 9)
        mask = np.maximum.reduce([dunes, ridge, a.mask_of(image), a.mask_of(towers), a.mask_of(caravan)])
        layer = solid(a, mask, mix(p["dune"], p["far"], 0.35), mix(p["dune_shadow"], p["far"], 0.30), HORIZON - 0.08, HORIZON + 0.06, "sand", 0.05)
        a.put(layer, ridge * (1.0 - dunes), mix(p["far"], p["mid"], 0.35))
        wall = np.maximum(a.mask_of(towers), a.mask_of(image) * (a.u > 0.58) * (a.v < HORIZON + 0.02))
        a.put(layer, wall, mix(p["dune_shadow"], p["far"], 0.45))
        a.put(layer, a.mask_of(caravan), mix(p["near"], p["dune_shadow"], 0.35))
        a.put(layer, a.mask_of(oasis, blur=0.3), mix(p["jade"], p["far"], 0.30))
        palms = a.mask_of(image) * (np.abs(a.u - 0.52) < 0.07)
        a.put(layer, palms, mix(p["jade"], p["near"], 0.55))
        # The face of each dune to the sun is light, the other in shade.
        slope = np.gradient(line)
        lit = (slope[None, :] > 0) * dunes * smoothstep(0.03, 0.0, a.v - line[None, :])
        a.light(layer, a.blur(lit.astype(np.float32), 1.5), p["low"], 0.35)
        a.light(layer, a.rim(mask, -0.002, 0.003, 0.5) * mask, p["sun"], 0.35)
        haze(a, layer, p["low"], 0.18, HORIZON + 0.04)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near silk")
        image, pen = a.drawing()
        tiles, tile_pen = a.drawing()
        ground, _ = a.ridge("near sand", 0.70, 0.012, cells=4.0, octaves=3)
        # The arch of a caravanserai at the left: a pier, a pointed arch cut
        # in a wall, and a band of glazed tiles over it.
        wall, wall_pen = a.drawing()
        wall_pen.rect(0.0, 0.26, 0.23, 0.74)
        _pointed_arch(wall_pen, 0.115, 0.74, 0.06, 0.32, value=0)
        tile_pen.rect(0.0, 0.29, 0.23, 0.33)
        tile_pen.rect(0.0, 0.42, 0.045, 0.74)
        tile_pen.rect(0.185, 0.42, 0.23, 0.74)
        # At the right: a post with a hanging lantern and sacks by it, and a
        # mulberry tree whose leaves feed the silk moths.
        pen.rect(0.835, 0.46, 0.843, 0.74)
        pen.rect(0.80, 0.46, 0.843, 0.468)
        pen.line([(0.808, 0.468), (0.808, 0.49)], 0.0015)
        lantern = (0.808, 0.505)
        for x in (0.86, 0.885):
            pen.ellipse(x, 0.70, 0.016, 0.022)
        crown, crown_pen = a.drawing()
        pen.line([(0.95, 0.74), (0.94, 0.52), (0.955, 0.42)], 0.012)
        for _ in range(12):
            crown_pen.ellipse(0.95 + rng.uniform(-0.06, 0.06), 0.38 + rng.uniform(-0.07, 0.05), rng.uniform(0.03, 0.05), rng.uniform(0.025, 0.04))
        mask = np.maximum.reduce([ground, a.mask_of(image), a.mask_of(wall), a.mask_of(crown)])
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.45), p["near"], 0.30, 0.74, "near sand", 0.08)
        glaze = a.mask_of(tiles) * a.mask_of(wall)
        # Lozenges of cobalt in the turquoise, as in glazed tiles.
        pattern = (np.abs(((a.u * 50.0) % 1.0) - 0.5) + np.abs(((a.v * 50.0) % 1.0) - 0.5) < 0.28).astype(np.float32)
        a.put(layer, glaze, mix(p["jade"], p["near"], 0.40))
        a.put(layer, glaze * pattern, mix(p["indigo"], p["near"], 0.30), 0.7)
        a.put(layer, a.mask_of(crown), mix(p["jade"], p["near"], 0.55))
        a.light(layer, a.rim(mask, -0.002, 0.003, 0.4) * mask, p["sun"], 0.36)
        a.shade(layer, a.rim(mask, 0.004, -0.003, 1.0) * mask, 0.22)
        image2, pen2 = a.drawing()
        pen2.ellipse(lantern[0], lantern[1], 0.010, 0.014)
        pen2.rect(lantern[0] - 0.006, lantern[1] - 0.017, lantern[0] + 0.006, lantern[1] - 0.012)
        body = a.mask_of(image2)
        a.put(layer, body, mix(p["crimson"], p["near"], 0.20))
        lamps(a, layer, [(lantern[0], lantern[1], 0.004)], p["saffron"], halo=5.0, strength=0.6)
        haze(a, layer, p["far"], 0.08, 0.73)
        return layer
    return _air(a, p, "heat haze", p["low"], 0.26, p["near"], 0.24)


def silk_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Strings of paper lanterns that sag across the top of the view, and a
    tassel under each lantern. Nothing stands from below."""
    for a_, b_, sag in ((-0.06, 0.30, 0.040), (0.70, 1.06, 0.040)):
        base = 0.33
        pen.curve((a_, base), (b_, base), sag, 0.0018)
        for k in range(1, 6):
            t = k / 6.0
            u = a_ + (b_ - a_) * t
            v = base + sag * 4.0 * t * (1.0 - t)
            pen.line([(u, v), (u, v + 0.006)], 0.0012)
            pen.ellipse(u, v + 0.016, 0.008, 0.011)
            pen.rect(u - 0.005, v + 0.004, u + 0.005, v + 0.007)
            pen.line([(u, v + 0.027), (u, v + 0.036)], 0.0012)
            layer_lights.append((u, v + 0.016, 0.004, SILK["saffron"]))
    del art_


# ---------------------------------------------------------------------------
# 5. The Mongol Steppe: grass to the end of the world
# ---------------------------------------------------------------------------

#: The horizon of the steppe is low: its sky is the most of the view.
STEPPE_HORIZON = HORIZON + 0.03


def history_steppe(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = STEPPE
    hv = STEPPE_HORIZON
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, scale(p["top"], 0.85)), (0.24, p["top"]), (0.46, p["mid"]), (hv - 0.01, p["low"]), (hv + 0.05, p["gold"]), (1.0, p["grass"])]))
        a.light(layer, a.spot(0.20, 0.20, 0.60, 2.0), p["cloud"], 0.30)
        # Great heaps of cloud, high, and a low row of small ones far off.
        _heaps(a, layer, "steppe heaps", ((0.12, 0.34, 0.10, 0.12), (0.52, 0.28, 0.13, 0.14), (0.88, 0.37, 0.09, 0.10)), p["cloud"], p["cloud_shadow"])
        # Smaller heaps far off, lower, to show how far the land goes.
        far_row = ((0.06, hv - 0.075, 0.035, 0.03), (0.30, hv - 0.09, 0.05, 0.04), (0.47, hv - 0.065, 0.025, 0.02), (0.68, hv - 0.085, 0.045, 0.035), (0.95, hv - 0.07, 0.03, 0.025))
        _heaps(a, layer, "far heaps", far_row, mix(p["cloud"], p["low"], 0.3), mix(p["cloud_shadow"], p["low"], 0.45), 0.85)
        # The golden eagle that soars, small and high.
        bird, bird_pen = a.drawing()
        _eagle(bird_pen, 0.36, 0.30, 0.022)
        a.put(layer, a.mask_of(bird, blur=0.3), mix((70, 54, 40), p["mid"], 0.25))
        _textbook(a, layer, 0.06)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far steppe")
        hills, line = a.ridge("rolling hills", hv + 0.004, 0.012, cells=2.5, octaves=4)
        west, wline = a.ridge("west hills", hv - 0.03, 0.03, cells=3.0, octaves=4, sharp=0.4)
        west = west * smoothstep(0.30, 0.18, a.u)
        image, pen = a.drawing()
        towers, tower_pen = a.drawing()
        doors, door_pen = a.drawing()
        herd, herd_pen = a.drawing()
        # The Great Wall on the hills at the west end.
        _wall(pen, tower_pen, wline, 0.0, 0.26, 0.007, 0.0035, (0.05, 0.15, 0.24))
        # A camp of gers, and the smoke of their stoves.
        smoke = np.zeros((a.n, a.n), dtype=np.float32)
        for k, (u, w) in enumerate(((0.50, 0.020), (0.545, 0.026), (0.60, 0.018), (0.64, 0.022))):
            v = _at(line, u) + 0.004
            _ger(pen, door_pen, u, v, w)
            smoke = np.maximum(smoke, _plume(a, ("ger smoke", k), u, v - w * 1.0, 0.09, 0.05, 0.004))
        # A herd of horses that graze on the right.
        for _ in range(11):
            u = rng.uniform(0.72, 0.90)
            _horse(herd_pen, u, _at(line, u) + rng.uniform(0.004, 0.014), rng.uniform(0.016, 0.020), rng.choice([-1.0, 1.0]), rng.random() < 0.6)
        mask = np.maximum.reduce([hills, west, a.mask_of(image), a.mask_of(towers), a.mask_of(herd)])
        layer = solid(a, mask, mix(p["grass"], p["far"], 0.20), mix(p["grass"], p["gold"], 0.45), hv - 0.06, hv + 0.06, "grass far", 0.05)
        a.put(layer, west * (1.0 - hills), mix(p["far"], p["mid"], 0.30))
        wall = np.maximum(a.mask_of(towers), a.mask_of(image) * (a.u < 0.28))
        a.put(layer, wall, mix((150, 130, 110), p["far"], 0.40))
        felt = a.mask_of(image) * (a.u > 0.45) * (a.u < 0.68)
        a.put(layer, felt, mix(p["felt"], p["far"], 0.15))
        a.shade(layer, felt * (a.v > _at(line, 0.55) - 0.012), 0.10)
        a.put(layer, a.mask_of(doors, blur=0.3), mix((222, 120, 40), p["far"], 0.20))
        a.put(layer, a.mask_of(herd), mix((90, 60, 40), p["far"], 0.30))
        a.glow(layer, smoke, mix(p["felt"], p["mid"], 0.3), 0.45)
        # Wind in the grass: long light waves.
        waves = smoothstep(0.55, 0.8, a.noise("grass wind", cells=8.0, octaves=3, stretch=6.0))
        a.light(layer, waves * hills * smoothstep(hv, hv + 0.03, a.v), p["gold"], 0.25)
        a.light(layer, a.rim(mask, 0.002, 0.003, 0.5) * mask, p["cloud"], 0.35)
        haze(a, layer, p["low"], 0.12, None)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near steppe")
        image, pen = a.drawing()
        blue, blue_pen = a.drawing()
        grass, grass_pen = a.drawing()
        ground, _ = a.ridge("near grass", 0.70, 0.006, cells=4.0, octaves=3)
        _ovoo(pen, blue_pen, 0.19, 0.70, 0.20)
        _tug(pen, 0.83, 0.72, 0.36)
        hair, hair_pen = a.drawing()
        hair_pen.poly([(0.83 - 0.36 * 0.07, 0.72 - 0.36 * 0.62), (0.83 + 0.36 * 0.07, 0.72 - 0.36 * 0.62), (0.83 + 0.36 * 0.045, 0.72 - 0.36 * 0.84), (0.83 - 0.36 * 0.045, 0.72 - 0.36 * 0.84)])
        # Tufts of tall grass at the sides.
        for _ in range(140):
            u = rng.choice([rng.uniform(0.0, 0.26), rng.uniform(0.74, 1.0)])
            h = rng.uniform(0.02, 0.07) * (1.6 if u < 0.08 or u > 0.92 else 1.0)
            lean = rng.uniform(-0.02, 0.02)
            grass_pen.poly([(u - 0.0025, 0.72), (u + 0.0025, 0.72), (u + lean, 0.70 - h)])
        mask = np.maximum.reduce([ground, a.mask_of(image), a.mask_of(grass)])
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.45), p["near"], 0.40, 0.74, "near grass", 0.08)
        a.put(layer, a.mask_of(grass) * (a.v < 0.70), mix(p["grass"], p["near"], 0.45))
        a.put(layer, a.mask_of(blue, blur=0.3), mix(p["blue"], p["near"], 0.15))
        a.put(layer, a.blur(a.mask_of(hair), 1.0) * a.mask_of(image), (30, 24, 22), 0.85)
        a.light(layer, a.rim(mask, 0.002, 0.003, 0.4) * mask, p["cloud"], 0.34)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.22)
        haze(a, layer, p["far"], 0.08, 0.73)
        return layer
    return _air(a, p, "steppe air", p["low"], 0.16, p["near"], 0.20)


def steppe_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Grass that stands from below, in tufts. Nothing hangs."""
    del layer_lights
    rng = art_.rand("steppe foreground")
    for k in range(6):
        u0 = (k + rng.uniform(0.15, 0.85)) / 6.0
        for _ in range(14):
            u = u0 + rng.uniform(-0.025, 0.025)
            h = rng.uniform(0.004, 0.022)
            lean = rng.uniform(-0.014, 0.014)
            pen.poly([(u - 0.0022, 1.0), (u + 0.0022, 1.0), (u + lean * 0.5 + 0.001, REST_BOTTOM - h * 0.4), (u + lean, REST_BOTTOM - h)])


# ---------------------------------------------------------------------------
# 6. Timbuktu and the Monsoon Coast
# ---------------------------------------------------------------------------


def history_monsoon(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = MONSOON
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, p["top"]), (0.30, p["mid"]), (HORIZON - 0.02, mix(p["mid"], p["low"], 0.6)), (HORIZON, p["sea"]), (HORIZON + 0.06, p["sea_deep"]), (1.0, scale(p["sea_deep"], 0.8))]))
        # A break in the cloud low in the west: the hot light of the Sahel.
        a.light(layer, a.spot(0.22, HORIZON - 0.04, 0.40, 1.8, squash=2.2), p["low"], 0.70)
        a.light(layer, a.spot(0.22, HORIZON - 0.03, 0.10, 1.4, squash=2.0), p["sun"], 0.55)
        # The monsoon clouds: a heavy bank, its feet dark, its tops lit.
        heaps = [(0.02 + k * 0.105, 0.42 + (k % 2) * 0.025 + (0.02 if k > 4 else 0.0), 0.085, 0.16 + (k % 3) * 0.04) for k in range(10)]
        _heaps(a, layer, "monsoon heaps", heaps, p["cloud_light"], p["cloud"])
        a.tint(layer, smoothstep(0.30, 0.0, a.v), p["cloud"], 0.55)
        # Rain that falls from the cloud in the east, over the sea: slant
        # streaks in curtains.
        rain, rain_pen = a.drawing()
        rng = a.rand("rain")
        for _ in range(260):
            x = rng.uniform(0.50, 1.02)
            y = rng.uniform(0.42, HORIZON - 0.03)
            length = rng.uniform(0.02, 0.06)
            rain_pen.line([(x, y), (x - length * 0.25, y + length)], 0.0012, value=rng.randint(80, 200))
        curtain = smoothstep(0.50, 0.66, a.u) * smoothstep(0.41, 0.46, a.v) * smoothstep(HORIZON + 0.005, HORIZON - 0.03, a.v)
        curtain = curtain * (0.55 + 0.45 * a.noise("rain curtains", cells=6.0, octaves=2, stretch=0.3))
        a.tint(layer, curtain, p["rain"], 0.45)
        a.tint(layer, a.mask_of(rain, blur=0.4) * curtain, p["cloud_light"], 0.45)
        # The sea: a band of turquoise light on it under the break.
        below = smoothstep(HORIZON, HORIZON + 0.004, a.v)
        glints = smoothstep(0.65, 0.82, a.noise("sea glints", cells=70.0, octaves=2, stretch=6.0))
        a.light(layer, below * glints * (1.0 - smoothstep(0.4, 0.7, a.u)), p["low"], 0.35)
        _textbook(a, layer, 0.06)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far monsoon")
        land, line = a.ridge("sahel", HORIZON + 0.01, 0.006, cells=3.0, octaves=3)
        land = land * smoothstep(0.76, 0.66, a.u + (a.v - HORIZON) * 0.8)
        image, pen = a.drawing()
        spikes, spike_pen = a.drawing()
        coral, coral_pen = a.drawing()
        holes, hole_pen = a.drawing()
        ships, ship_pen = a.drawing()
        sails, sail_pen = a.drawing()
        # The great mosque of mudbrick in the west: a wall with buttresses
        # and two towers, the toron out of each.
        mu = 0.26
        mv = _at(line, mu) + 0.004
        pen.rect(mu - 0.12, mv - 0.035, mu + 0.10, mv)
        for k in range(12):
            x = mu - 0.115 + k * 0.019
            pen.poly([(x - 0.005, mv), (x + 0.005, mv), (x + 0.003, mv - 0.048), (x - 0.003, mv - 0.048)])
            spike_pen.rect(x - 0.007, mv - 0.026, x + 0.007, mv - 0.022)
            spike_pen.rect(x - 0.007, mv - 0.012, x + 0.007, mv - 0.008)
        _mud_tower(pen, spike_pen, mu - 0.04, mv, 0.030, 0.15)
        _mud_tower(pen, spike_pen, mu + 0.07, mv, 0.020, 0.09)
        # Houses of the town round it, and the camels with salt.
        for _ in range(10):
            u = rng.choice([rng.uniform(0.04, 0.12), rng.uniform(0.38, 0.52)])
            _mud_house(pen, hole_pen, u, _at(line, u) + 0.004, rng.uniform(0.008, 0.014), rng.uniform(0.010, 0.02))
        for k in range(4):
            _camel(pen, 0.54 + k * 0.03, _at(line, 0.54) + 0.004, 0.022, 1.0)
        # The coral town on the shore, white, and palms.
        for k in range(6):
            u = 0.60 + k * 0.022
            _coral_house(coral_pen, hole_pen, u, _at(line, u) + 0.006 + k * 0.002, 0.010, rng.uniform(0.014, 0.024))
        for u in (0.585, 0.72):
            _date_palm(pen, pen, rng, u, _at(line, u) + 0.006, 0.05, 0.008, 9)
        # Dhows on the sea under the rain.
        for u, v, s in ((0.82, HORIZON + 0.012, 0.06), (0.93, HORIZON + 0.004, 0.04), (0.74, HORIZON + 0.03, 0.05)):
            _dhow(ship_pen, sail_pen, u, v, s, -1.0)
        mask = np.maximum.reduce([land, a.mask_of(image), a.mask_of(coral), a.mask_of(ships), a.mask_of(sails)])
        layer = solid(a, mask, mix(p["adobe"], p["far"], 0.35), mix(p["adobe_dark"], p["far"], 0.35), HORIZON - 0.12, HORIZON + 0.05, "adobe", 0.06)
        a.put(layer, a.mask_of(spikes, blur=0.3), mix(p["near"], p["adobe_dark"], 0.55))
        a.put(layer, a.mask_of(coral), mix(p["coral"], p["far"], 0.15))
        a.shade(layer, a.mask_of(holes) * mask, 0.45)
        a.put(layer, a.mask_of(ships), mix(p["near"], p["far"], 0.45))
        a.put(layer, a.mask_of(sails, blur=0.3), mix(p["coral"], p["far"], 0.30))
        a.light(layer, a.rim(mask, 0.003, 0.002, 0.5) * mask * smoothstep(0.6, 0.3, a.u), p["sun"], 0.45)
        haze(a, layer, mix(p["mid"], p["low"], 0.5), 0.20, HORIZON + 0.04)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near monsoon")
        image, pen = a.drawing()
        spikes, spike_pen = a.drawing()
        fronds, frond_pen = a.drawing()
        ground, _ = a.ridge("near coast", 0.70, 0.010, cells=5.0, octaves=3)
        # A wall of mudbrick at the left, round at its top, the toron out of it.
        pen.poly([(0.0, 0.74), (0.0, 0.34), (0.14, 0.36), (0.18, 0.39), (0.205, 0.44), (0.215, 0.74)])
        for row in range(6):
            y = 0.42 + row * 0.05
            spike_pen.rect(0.19, y - 0.0045, 0.24, y + 0.0045)
        # Coconut palms that lean out over the sea at the right.
        _date_palm(pen, frond_pen, rng, 0.90, 0.72, 0.42, -0.07)
        _date_palm(pen, frond_pen, rng, 0.82, 0.72, 0.28, -0.04)
        # A boat drawn up on the sand.
        pen.poly([(0.66, 0.69), (0.75, 0.685), (0.77, 0.665), (0.745, 0.70), (0.68, 0.705)])
        mask = np.maximum.reduce([ground, a.mask_of(image), a.mask_of(spikes), a.mask_of(fronds)])
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.45), p["near"], 0.30, 0.74, "near adobe", 0.10)
        wall = a.mask_of(image) * (a.u < 0.22)
        a.put(layer, wall, mix(p["adobe_dark"], p["near"], 0.55))
        a.put(layer, a.mask_of(spikes), mix(p["adobe_dark"], p["near"], 0.75))
        a.put(layer, a.mask_of(fronds), mix((60, 100, 70), p["near"], 0.45))
        a.light(layer, a.rim(mask, 0.003, 0.002, 0.4) * mask * smoothstep(0.7, 0.2, a.u), p["sun"], 0.38)
        a.light(layer, a.rim(mask, -0.002, 0.003, 0.4) * mask * smoothstep(0.5, 0.9, a.u), p["sea"], 0.22)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.22)
        haze(a, layer, p["far"], 0.08, 0.73)
        return layer
    return _air(a, p, "spray", p["cloud_light"], 0.24, p["near"], 0.24)


# ---------------------------------------------------------------------------
# 7. The Age of Sail: a harbour under an old map
# ---------------------------------------------------------------------------


def _map_sky(a: Art, layer: np.ndarray, p: dict) -> None:
    """An old map drawn on the sky in faint ink: a compass rose with its
    rhumb lines, a coast with hatching, a route of dashes and a sea dragon.
    Near its edges the map is not finished: the lines stop."""
    ink, pen = a.drawing()
    rose, rose_pen = a.drawing()
    cu, cv = 0.34, 0.36
    for k in range(16):
        end = polar(cu, cv, 0.9, k * 22.5)
        pen.line([(cu, cv), end], 0.0012 if k % 2 else 0.0018)
    for k in range(8):
        r = 0.05 if k % 2 == 0 else 0.03
        tip = polar(cu, cv, r, k * 45.0 - 90.0)
        left = polar(cu, cv, 0.008, k * 45.0 - 135.0)
        right = polar(cu, cv, 0.008, k * 45.0 - 45.0)
        rose_pen.poly([left, tip, right, (cu, cv)])
    rose_pen.ring(cu, cv, 0.022, 0.0018)
    # A coast in the north east, with hatching inside it.
    rng = a.rand("map coast")
    pts = []
    for k in range(40):
        t = k / 39.0
        pts.append((0.58 + t * 0.40, 0.20 + 0.10 * math.sin(t * 5.0) + rng.uniform(-0.012, 0.012) + t * 0.08))
    pen.line(pts, 0.0022)
    for x, y in pts[::2]:
        pen.line([(x, y - 0.004), (x + 0.010, y - 0.020)], 0.0010)
    # The route of a ship in dashes, and the dragon of the unknown sea.
    for k in range(18):
        t0, t1 = k / 18.0, (k + 0.5) / 18.0
        def at(t: float) -> tuple[float, float]:
            return (0.14 + t * 0.52, 0.48 - 0.16 * math.sin(t * math.pi))
        pen.line([at(t0), at(t1)], 0.0016)
    dragon = [(0.80 + 0.012 * k, 0.40 + 0.012 * math.sin(k * 0.9)) for k in range(12)]
    pen.line(dragon, 0.004)
    pen.ellipse(dragon[0][0] - 0.006, dragon[0][1] - 0.004, 0.009, 0.006)
    for x, y in dragon[2:10:2]:
        pen.poly([(x - 0.004, y - 0.003), (x + 0.004, y - 0.003), (x, y - 0.012)])
    unfinished = smoothstep(0.62, 0.30, np.sqrt(((a.u - 0.52) / 1.3) ** 2 + ((a.v - 0.34) / 0.8) ** 2) + (a.noise("map edge", cells=6.0, octaves=3) - 0.5) * 0.25)
    sky_part = smoothstep(HORIZON - 0.04, HORIZON - 0.12, a.v)
    a.tint(layer, a.mask_of(ink, blur=0.3) * unfinished * sky_part, p["ink"], 0.26)
    a.tint(layer, a.mask_of(rose, blur=0.3) * sky_part, p["ink"], 0.45)
    a.tint(layer, a.mask_of(rose, blur=0.3) * (a.u > cu) * sky_part, p["red"], 0.25)


def history_sail(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = SAIL
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, p["top"]), (0.34, p["mid"]), (HORIZON - 0.01, p["low"]), (HORIZON, p["sea_light"]), (HORIZON + 0.06, p["sea"]), (1.0, scale(p["sea"], 0.8))]))
        # The sky is moved to the colour of old parchment, most at its middle.
        a.tint(layer, a.spot(0.5, 0.36, 0.6, 1.2, squash=1.6) * (a.v < HORIZON), p["parchment"], 0.40)
        a.light(layer, a.spot(0.62, 0.22, 0.40, 2.0), p["canvas"], 0.30)
        clouds = cloud_mask(a, "sail clouds", 0.46, 0.08, cells=3.0, cover=0.34, soft=0.16, stretch=3.0)
        a.tint(layer, clouds, p["canvas"], 0.45)
        _map_sky(a, layer, p)
        below = smoothstep(HORIZON, HORIZON + 0.004, a.v)
        glints = smoothstep(0.62, 0.80, a.noise("harbour glints", cells=80.0, octaves=2, stretch=6.0))
        a.light(layer, below * glints, p["canvas"], 0.30)
        _textbook(a, layer, 0.07)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far harbour")
        town, line = a.ridge("harbour town", HORIZON + 0.012, 0.004, cells=3.0, octaves=3)
        town = town * smoothstep(0.40, 0.36, a.u)
        head, hline = a.ridge("headland", HORIZON - 0.01, 0.02, cells=3.0, octaves=4)
        head = head * smoothstep(0.74, 0.80, a.u)
        image, pen = a.drawing()
        windows, window_pen = a.drawing()
        sails, sail_pen = a.drawing()
        bands, band_pen = a.drawing()
        # The counting houses of the harbour town, with stepped gables.
        u = 0.02
        while u < 0.37:
            w = rng.uniform(0.012, 0.018)
            _gabled_house(pen, window_pen, rng, u + w, _at(line, u) + 0.004, w, rng.uniform(0.04, 0.07))
            u += w * 2.0 + 0.002
        # A quay in front of the town.
        pen.rect(0.0, HORIZON + 0.010, 0.42, HORIZON + 0.02)
        # The lighthouse on the headland.
        lu = 0.86
        lv = _at(hline, lu) + 0.004
        _lighthouse(pen, band_pen, lu, lv, 0.012, 0.10)
        # Tall ships at anchor and one that sails.
        _tall_ship(pen, sail_pen, 0.50, HORIZON + 0.025, 0.11, furled=True)
        _tall_ship(pen, sail_pen, 0.64, HORIZON + 0.015, 0.08, furled=False)
        mask = np.maximum.reduce([town, head, a.mask_of(image)])
        layer = solid(a, mask, mix(p["far"], p["low"], 0.25), mix(p["far"], p["sea"], 0.35), HORIZON - 0.12, HORIZON + 0.04, "harbour", 0.05)
        houses = a.mask_of(image) * (a.u < 0.40) * (a.v < HORIZON + 0.012)
        a.put(layer, houses * (0.5 + 0.5 * a.noise("house paint", cells=40.0, octaves=1)), mix(p["red"], p["far"], 0.45), 0.6)
        a.shade(layer, a.mask_of(windows) * houses, 0.35)
        a.put(layer, a.mask_of(sails, blur=0.3), mix(p["canvas"], p["far"], 0.15))
        a.put(layer, a.mask_of(bands, blur=0.3), mix(p["red"], p["far"], 0.25))
        beam, beam_pen = a.drawing()
        top = (lu, lv - 0.10 - 0.012 * 0.36)
        beam_pen.poly([top, (lu - 0.40, top[1] - 0.06), (lu - 0.40, top[1] + 0.03)], 180)
        a.glow(layer, a.mask_of(beam, blur=5.0) * smoothstep(lu - 0.40, lu, a.u), p["canvas"], 0.22)
        lamps(a, layer, [(top[0], top[1], 0.003)], p["brass"], halo=5.0, strength=0.8)
        # Gulls over the harbour.
        gulls, gull_pen = a.drawing()
        for _ in range(6):
            x, y, s = rng.uniform(0.3, 0.8), rng.uniform(0.40, 0.50), rng.uniform(0.006, 0.010)
            gull_pen.line([(x - s, y - s * 0.3), (x - s * 0.4, y - s * 0.5), (x, y), (x + s * 0.4, y - s * 0.5), (x + s, y - s * 0.3)], 0.0016)
        a.put(layer, a.mask_of(gulls, blur=0.3), mix(p["tar"], p["far"], 0.4), 0.8)
        a.light(layer, a.rim(mask, 0.002, 0.003, 0.5) * mask, p["canvas"], 0.35)
        haze(a, layer, p["low"], 0.18, HORIZON + 0.04)
        return layer
    if layer_key == "near_background":
        rng = a.rand("near harbour")
        image, pen = a.drawing()
        ground, _ = a.ridge("quay", 0.705, 0.0, cells=2.0, octaves=1)
        # Masts and their rigging at the sides, of ships at the quay.
        _rigging(pen, 0.13, 0.72, 0.7, (0.30, 0.46), 0.006)
        _rigging(pen, 0.88, 0.72, 0.7, (0.26, 0.42), 0.006)
        # Pilings and a bollard on the quay, a barrel and crates.
        for u in (0.22, 0.25, 0.75, 0.78):
            pen.rect(u - 0.006, 0.64, u + 0.006, 0.74)
            pen.ellipse(u, 0.64, 0.006, 0.003)
        pen.rect(0.30, 0.670, 0.325, 0.705)
        pen.ellipse(0.69, 0.685, 0.014, 0.02)
        mask = np.maximum.reduce([ground, a.mask_of(image)])
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.45), p["near"], 0.30, 0.74, "near quay", 0.08)
        a.light(layer, a.rim(mask, 0.002, 0.003, 0.4) * mask, p["canvas"], 0.30)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.22)
        wet = a.band(0.712, 0.006) * ground
        a.light(layer, wet * smoothstep(0.5, 0.8, a.noise("wet quay", cells=30.0, octaves=2, stretch=4.0)), p["sea_light"], 0.30)
        haze(a, layer, p["far"], 0.08, 0.73)
        del rng
        return layer
    return _air(a, p, "harbour mist", p["canvas"], 0.22, p["near"], 0.24)


def sail_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Ropes that sag across the top of the view, and a block and tackle
    that hangs on one. Nothing stands from below."""
    del layer_lights
    rng = art_.rand("sail foreground")
    for k in range(3):
        a_ = k * 0.36 + rng.uniform(-0.04, 0.04)
        pen.curve((a_, 0.33), (a_ + rng.uniform(0.24, 0.30), 0.33), rng.uniform(0.045, 0.055), 0.0026)
    for u in (0.30, 0.71):
        end = rng.uniform(0.375, 0.385)
        pen.line([(u, 0.0), (u, end - 0.012)], 0.0020)
        pen.ellipse(u, end - 0.006, 0.0045, 0.007)
        pen.arc(u, end + 0.005, 0.0045, 0, 200, 0.0024)


# ---------------------------------------------------------------------------
# 8. The Industrial Age: a smoky dusk over the mills
# ---------------------------------------------------------------------------


def history_industrial(layer_key: str, art_: Art) -> np.ndarray:
    a = art_
    p = INDUSTRIAL
    sun_at = (0.56, HORIZON - 0.03)
    if layer_key == "sky":
        layer = a.opaque(a.ramp([(0.0, p["top"]), (0.30, mix(p["top"], p["mid"], 0.6)), (0.48, p["mid"]), (HORIZON - 0.01, p["low"]), (HORIZON + 0.06, mix(p["low"], p["brick_dark"], 0.5)), (1.0, p["brick_dark"])]))
        _sun(a, layer, *sun_at, 0.030, p["sun"], p["low"], 0.60)
        # Bands of brown smoke across the dusk, lit orange from under.
        smoke = cloud_mask(a, "smoke bands", 0.40, 0.14, cells=2.4, cover=0.48, soft=0.18, stretch=5.0)
        a.tint(layer, smoke, p["smoke"], 0.60)
        a.light(layer, smoke * smoothstep(0.36, 0.52, a.v), p["low"], 0.35)
        _textbook(a, layer, 0.07)
        return layer
    if layer_key == "far_backplate":
        rng = a.rand("far mills")
        ground, line = a.ridge("town", HORIZON + 0.02, 0.004, cells=3.0, octaves=3)
        image, pen = a.drawing()
        windows, window_pen = a.drawing()
        arches, arch_pen = a.drawing()
        train, train_pen = a.drawing()
        # The mills, long and tall, with rows of lit windows.
        for u0, u1, h, floors in ((0.02, 0.22, 0.12, 6), (0.24, 0.40, 0.09, 5), (0.66, 0.84, 0.13, 6), (0.86, 0.98, 0.10, 5)):
            _mill(pen, window_pen, rng, u0, u1, _at(line, u0) + 0.004, h, floors, 0.55)
        # Terraces of small houses in the middle, low.
        for k in range(14):
            u = 0.40 + k * 0.018
            pen.rect(u, _at(line, u) - 0.018, u + 0.016, _at(line, u) + 0.004)
            pen.poly([(u - 0.001, _at(line, u) - 0.018), (u + 0.017, _at(line, u) - 0.018), (u + 0.008, _at(line, u) - 0.026)])
        # The chimneys, and their smoke that leans to the east.
        smoke = np.zeros((a.n, a.n), dtype=np.float32)
        for k, (u, h) in enumerate(((0.12, 0.26), (0.31, 0.20), (0.74, 0.28), (0.92, 0.19))):
            v = _at(line, u) + 0.004
            _chimney(pen, u, v, 0.009, h)
            smoke = np.maximum(smoke, _plume(a, ("mill smoke", k), u, v - h, 0.30, 0.22, 0.03))
        # The viaduct across the middle distance, and a train on it.
        _viaduct(arch_pen, 0.0, 1.0, HORIZON - 0.012, HORIZON + 0.03, 0.036)
        stack = _train(train_pen, 0.50, HORIZON - 0.018, 0.04, 4)
        steam = _plume(a, "train steam", stack[0], stack[1], 0.10, -0.12, 0.022)
        mask = np.maximum.reduce([ground, a.mask_of(image)])
        layer = solid(a, mask, mix(p["brick"], p["far"], 0.40), mix(p["brick_dark"], p["far"], 0.35), HORIZON - 0.12, HORIZON + 0.05, "brick", 0.06)
        smoke = a.blur(smoke, 3.0)
        a.glow(layer, smoke, mix(p["smoke"], p["top"], 0.4), 0.80)
        a.light(layer, smoke * smoothstep(0.30, 0.50, a.v), p["low"], 0.20)
        lit = a.mask_of(windows) * a.mask_of(image)
        a.put(layer, lit, p["gas"], 0.85)
        a.glow(layer, a.blur(lit, 4.0), p["gas"], 0.30)
        # The viaduct and the train are nearer: darker, in front of the town.
        bridge = np.maximum(a.mask_of(arches), a.mask_of(train))
        a.put(layer, bridge, mix(p["brick_dark"], p["far"], 0.30))
        a.light(layer, a.rim(bridge, 0.0, 0.002, 0.3) * bridge, p["low"], 0.35)
        a.glow(layer, a.blur(steam, 2.0), p["steam"], 0.55)
        lamps(a, layer, [(0.50 + 0.04 * 0.62, HORIZON - 0.018 - 0.04 * 0.19, 0.0018)], p["gas"], halo=5.0, strength=0.9)
        a.light(layer, a.rim(mask, 0.0, 0.002, 0.5) * mask, p["low"], 0.30)
        haze(a, layer, mix(p["low"], p["smoke"], 0.5), 0.16, HORIZON + 0.04)
        return layer
    if layer_key == "near_background":
        image, pen = a.drawing()
        ground, _ = a.ridge("near cobbles", 0.705, 0.0, cells=2.0, octaves=1)
        # An iron bridge frame at the left: a post and a lattice girder.
        pen.rect(0.0, 0.30, 0.20, 0.33)
        pen.rect(0.0, 0.40, 0.20, 0.42)
        for k in range(8):
            x = k * 0.025
            pen.line([(x, 0.33), (x + 0.025, 0.40)], 0.003)
        pen.rect(0.16, 0.30, 0.175, 0.74)
        # Gas lamps.
        flames = [_gas_lamp(pen, u, 0.72, 0.22) for u in (0.24, 0.80)]
        # A stack of barrels and a crate at the right.
        for x, y in ((0.86, 0.70), (0.885, 0.70), (0.872, 0.67)):
            pen.ellipse(x, y, 0.012, 0.016)
        pen.rect(0.90, 0.665, 0.94, 0.72)
        mask = np.maximum.reduce([ground, a.mask_of(image)])
        layer = solid(a, mask, mix(p["near"], p["near_light"], 0.40), p["near"], 0.30, 0.74, "near iron", 0.08)
        a.light(layer, a.rim(mask, 0.0, 0.003, 0.4) * mask, p["low"], 0.30)
        a.shade(layer, a.rim(mask, -0.004, -0.003, 1.0) * mask, 0.22)
        lamps(a, layer, [(u, v, 0.006) for u, v in flames], p["gas"], halo=6.0, strength=0.85)
        haze(a, layer, p["far"], 0.08, 0.73)
        return layer
    layer = _air(a, p, "soot", p["smoke"], 0.32, p["near"], 0.30)
    return layer


def industrial_foreground(art_: Art, pen: Pen, layer_lights: list) -> None:
    """Wires that sag from above, and chains with hooks from a crane. Nothing
    stands from below."""
    del layer_lights
    rng = art_.rand("industrial foreground")
    for k in range(3):
        a_ = k * 0.34 + rng.uniform(-0.03, 0.03)
        pen.curve((a_, 0.34), (a_ + rng.uniform(0.28, 0.34), 0.34), rng.uniform(0.04, 0.05), 0.0018)
    for u in (0.22, 0.63):
        end = rng.uniform(0.38, 0.395)
        v = 0.0
        while v < end:
            pen.ellipse(u, v, 0.0036, 0.006)
            v += 0.0102
        pen.arc(u + 0.004, end + 0.009, 0.009, 0, 200, 0.0036)
