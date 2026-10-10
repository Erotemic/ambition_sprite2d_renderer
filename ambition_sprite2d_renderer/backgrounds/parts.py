"""Parts that more than one scene has: stars, a moon, clouds, mist, lamps."""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np

from .artkit import Art, Pen, mix, polar, scale, smoothstep

#: Where the far horizon of a scene is, in `v`.
HORIZON = 0.60

#: The published size of each layer. The near layer is drawn the largest in
#: the game, so it has the most pixels; the air in front is soft, so it has
#: the fewest.
LAYER_SIZE = {
    "sky": 1024,
    "far_backplate": 1024,
    "near_background": 1280,
    "foreground_atmosphere": 768,
}

#: The blur of each layer in published pixels: a far thing is not sharp.
LAYER_BLUR = {
    "sky": 0.0,
    "far_backplate": 1.1,
    "near_background": 0.6,
    "foreground_atmosphere": 1.2,
}


# ---------------------------------------------------------------------------
# Parts that more than one scene has
# ---------------------------------------------------------------------------


def solid(
    art: Art,
    mask: np.ndarray,
    top: Sequence[float],
    bottom: Sequence[float],
    v_top: float,
    v_bottom: float,
    texture: object | None = None,
    texture_amount: float = 0.10,
) -> np.ndarray:
    """A layer with `mask` painted from `top` (at `v_top`) to `bottom`."""
    paint = art.ramp([(0.0, top), (v_top, top), (v_bottom, bottom), (1.0, bottom)])
    if texture is not None:
        grain = art.noise(texture, cells=9.0, octaves=4)
        paint = paint * (1.0 - texture_amount + 2.0 * texture_amount * grain)[:, :, None]
    layer = art.blank()
    art.put(layer, mask, paint)
    return layer


def stars(art: Art, layer: np.ndarray, count: int, colour: Sequence[float], v_max: float = 0.62, tag: object = "stars") -> None:
    rng = art.rand(tag)
    small, pen = art.drawing()
    large, big_pen = art.drawing()
    for _ in range(count):
        u, v = rng.random(), rng.random() * v_max
        fade = 1.0 - (v / v_max) ** 2
        value = int(255 * fade * rng.uniform(0.25, 1.0))
        r = rng.choice([0.0007, 0.0007, 0.0009, 0.0012])
        pen.ellipse(u, v, r, value=value)
        if rng.random() < 0.06:
            big_pen.ellipse(u, v, 0.0018, value=int(230 * fade))
    art.light(layer, art.mask_of(small), colour, 0.9)
    art.light(layer, art.mask_of(large), colour, 1.0)
    art.light(layer, art.mask_of(large, blur=3.0), colour, 0.8)


def moon(
    art: Art,
    layer: np.ndarray,
    cu: float,
    cv: float,
    r: float,
    colour: Sequence[float],
    halo: Sequence[float],
    crescent: float = 0.0,
) -> None:
    """A moon with a halo. `crescent` more than 0 cuts that part away."""
    art.light(layer, art.spot(cu, cv, r * 7.0, 2.2), halo, 0.55)
    art.light(layer, art.spot(cu, cv, r * 2.4, 1.6), halo, 0.7)
    disc, pen = art.drawing()
    pen.ellipse(cu, cv, r)
    if crescent > 0.0:
        pen.ellipse(cu + r * crescent * 1.1, cv - r * crescent * 0.35, r * 0.96, value=0)
    mask = art.mask_of(disc)
    face = art.flat(colour) * (0.86 + 0.20 * art.noise("moon face", cells=28.0, octaves=3))[:, :, None]
    seas, sea_pen = art.drawing()
    rng = art.rand("moon seas")
    for _ in range(7):
        a, d = rng.uniform(0, 360), rng.uniform(0.1, 0.7) * r
        sea_pen.ellipse(*polar(cu, cv, d, a), rng.uniform(0.10, 0.26) * r, value=70)
    face = face * (1.0 - art.mask_of(seas, blur=1.2))[:, :, None]
    art.put(layer, mask, face)


def cloud_mask(
    art: Art,
    tag: object,
    centre_v: float,
    half: float,
    cells: float = 3.0,
    cover: float = 0.5,
    soft: float = 0.12,
    stretch: float = 2.6,
) -> np.ndarray:
    """Clouds in a level band. `cover` is how much of the band they fill."""
    lumps = art.noise(tag, cells=cells, octaves=5, stretch=stretch)
    band = art.band(centre_v, half, 1.0)
    return smoothstep(1.0 - cover, 1.0 - cover + soft, lumps * (0.45 + 0.55 * band)) * smoothstep(0.0, 0.35, band)


def fog(art: Art, tag: object, centre_v: float, half: float, cells: float = 2.0) -> np.ndarray:
    """Low mist in a level band, in long lumps."""
    lumps = art.noise(tag, cells=cells, octaves=4, stretch=4.0)
    return art.band(centre_v, half, 1.5) * (0.35 + 0.65 * lumps)


def shafts(art: Art, tag: object, count: int, lean: float, v0: float = 0.0, v1: float = 0.9, width: float = 0.05) -> np.ndarray:
    """Beams of light that come down from `v0` and lean by `lean`."""
    rng = art.rand(tag)
    image, pen = art.drawing()
    for i in range(count):
        u = (i + rng.uniform(0.15, 0.85)) / count
        w = width * rng.uniform(0.5, 1.5)
        value = rng.randint(90, 220)
        pen.poly([(u - w * 0.3, v0), (u + w * 0.3, v0), (u + lean + w, v1), (u + lean - w, v1)], value)
    beams = art.mask_of(image, blur=9.0)
    return beams * smoothstep(v1, v0 + 0.1, art.v) ** 0.7


def motes(art: Art, tag: object, count: int, v0: float, v1: float, r0: float = 0.0012, r1: float = 0.003) -> np.ndarray:
    """Small soft points in the air: dust, embers, plankton."""
    rng = art.rand(tag)
    image, pen = art.drawing()
    for _ in range(count):
        pen.ellipse(rng.random(), rng.uniform(v0, v1), rng.uniform(r0, r1), value=rng.randint(90, 255))
    sharp = art.mask_of(image, blur=0.3)
    return np.clip(sharp + art.mask_of(image, blur=1.6) * 1.2, 0.0, 1.0)


def haze(art: Art, layer: np.ndarray, colour: Sequence[float], amount: float, ground_v: float | None = None) -> None:
    """The air between the eye and the layer: all of it by `amount`, and
    more where it meets its ground."""
    art.tint(layer, np.ones((art.n, art.n), dtype=np.float32), colour, amount)
    if ground_v is not None:
        art.tint(layer, art.band(ground_v, 0.16, 1.4), colour, 0.55)


def lamps(
    art: Art,
    layer: np.ndarray,
    points: Sequence[tuple[float, float, float]],
    colour: Sequence[float],
    halo: float = 5.0,
    strength: float = 0.9,
) -> None:
    """Small lights at `(u, v, radius)`, each with a soft halo in the air."""
    image, pen = art.drawing()
    wide, wide_pen = art.drawing()
    for u, v, r in points:
        pen.ellipse(u, v, r)
        wide_pen.ellipse(u, v, r * halo)
    art.put(layer, art.mask_of(wide, blur=halo * 2.2), colour, 0.42 * strength)
    art.put(layer, art.mask_of(image, blur=0.4), mix(colour, (255, 255, 255), 0.45), strength)


def window_grid(
    pen: Pen, rng, u0: float, v0: float, u1: float, v1: float, du: float, dv: float, lit: float, w: float = 0.42, h: float = 0.5
) -> None:
    """Lit windows in the box `(u0, v0)-(u1, v1)`: one in each cell of
    `du` by `dv`, lit with the chance `lit`."""
    v = v0 + dv * 0.5
    while v + dv * 0.5 < v1:
        u = u0 + du * 0.5
        while u + du * 0.5 < u1:
            if rng.random() < lit:
                pen.rect(u - du * w * 0.5, v - dv * h * 0.5, u + du * w * 0.5, v + dv * h * 0.5, value=rng.randint(120, 255))
            u += du
        v += dv


def palm(pen: Pen, rng, u: float, v: float, h: float, lean: float) -> None:
    """A palm that stands at `(u, v)`: a bent trunk and a head of fronds."""
    top = (u + lean, v - h)
    pen.line([(u + lean * (i / 8.0) ** 1.6, v + 0.02 - (h + 0.02) * (i / 8.0)) for i in range(9)], 0.006)
    pen.ellipse(top[0], top[1] + 0.004, 0.007)
    for k in range(8):
        angle = -200.0 + k * (220.0 / 7.0) + rng.uniform(-7.0, 7.0)
        length = rng.uniform(0.06, 0.085) * (h / 0.13) ** 0.5
        tip = polar(*top, length, angle)
        tip = (tip[0], tip[1] + length * 0.42)
        ctrl = polar(*top, length * 0.6, angle)
        ctrl = (ctrl[0], ctrl[1] - length * 0.32)
        prev = top
        for i in range(1, 13):
            t = i / 12.0
            x = (1 - t) ** 2 * top[0] + 2 * (1 - t) * t * ctrl[0] + t * t * tip[0]
            y = (1 - t) ** 2 * top[1] + 2 * (1 - t) * t * ctrl[1] + t * t * tip[1]
            pen.line([prev, (x, y)], 0.0036 * (1.0 - t * 0.6))
            pen.line([(x, y), (x + (0.003 if x > top[0] else -0.003), y + length * 0.24 * (1.0 - t * 0.55))], 0.0019)
            prev = (x, y)


def vignette(art: Art, layer: np.ndarray, colour: Sequence[float], strength: float) -> None:
    """Dark air at the left and right of the panel, to frame the play."""
    side = smoothstep(0.30, 0.52, np.abs(art.u - 0.5))
    art.put(layer, side, colour, strength)




def crystal_cluster(
    body: Pen, facet: Pen, rng, u: float, v: float, size: float, count: int = 6, up: float = -90.0, spread: float = 55.0
) -> None:
    """Crystals that grow from `(u, v)`. `body` gets each whole crystal and
    `facet` the half of it that faces the light. `up` is the direction they
    grow in (-90 is up, 90 is down)."""
    for _ in range(count):
        angle = up + rng.uniform(-spread, spread)
        length = size * rng.uniform(0.45, 1.0)
        width = length * rng.uniform(0.10, 0.17)
        tip = polar(u, v, length, angle)
        shoulder = polar(u, v, length * 0.76, angle)
        nx, ny = polar(0.0, 0.0, width, angle + 90.0)
        base = (u + rng.uniform(-0.3, 0.3) * size * 0.2, v)
        body.poly([(base[0] - nx, base[1] - ny), (shoulder[0] - nx, shoulder[1] - ny), tip, (shoulder[0] + nx, shoulder[1] + ny), (base[0] + nx, base[1] + ny)])
        facet.poly([(base[0] - nx, base[1] - ny), (shoulder[0] - nx, shoulder[1] - ny), tip, shoulder, base])


def pine(pen: Pen, u: float, v: float, h: float, w: float, tiers: int = 5) -> None:
    """A pine that stands at `(u, v)`: `tiers` of boughs, each wider than the one above."""
    pen.rect(u - w * 0.07, v - h * 0.2, u + w * 0.07, v + 0.02)
    for k in range(tiers):
        t = k / tiers
        top = v - h + h * 0.78 * t
        half = w * (0.22 + 0.78 * (k + 1) / tiers) * 0.5
        pen.poly([(u, top - h * 0.06), (u + half, top + h * 0.26), (u - half, top + h * 0.26)])


def cumulus(art: Art, tag: object, centre_v: float, half: float, cells: float, cover: float, light, shadow) -> np.ndarray:
    """A bank of heap clouds as a layer: light on top, in shadow below."""
    lumps = art.noise(tag, cells=cells, octaves=5, stretch=2.2)
    band = art.band(centre_v, half, 1.0)
    thick = lumps * (0.40 + 0.60 * band) * smoothstep(0.0, 0.3, band) - (1.0 - cover)
    mask = smoothstep(0.0, 0.035, thick)
    top = np.clip(thick * 5.0 + (centre_v - art.v) / half * 0.55 + 0.35, 0.0, 1.0)
    paint = art.flat(shadow) + (art.flat(light) - art.flat(shadow)) * top[:, :, None]
    layer = art.blank()
    art.put(layer, mask, paint)
    return layer
