"""The scene of the military tower: the Iron Bastion of the Faction of Steel.

It is the inside of a tall, narrow tower of poured concrete and riveted
steel: the parade deck at the bottom, the General's war room at the top. The
far wall is concrete in shade, painted olive drab to the height of a man,
with narrow slit windows high up that let in a little day. Steel columns and
cross braces go up the shaft. Nearer, a riveted girder carries pipes, a cable
tray, caged lamps with warm light, and the banners of the faction.

The building is stern but not grim: the colours are olive, khaki, gunmetal,
concrete and brass, with a little signal red for warning stripes.

The insignia of the faction is a white five-point star on an olive roundel
with a brass rim (`insignia`). It is an invented mark: the art shows no real
flag or symbol of a real state. It is not the gear of Castle Godwin.
"""

from __future__ import annotations

import math

import numpy as np

from .artkit import Art, Pen, mix, scale, smoothstep
from .parts import fog, lamps, motes, shafts, solid, vignette

TOWER = {
    "deep": (16, 18, 15),
    "wall": (62, 61, 57),
    "wall_dark": (36, 36, 33),
    "concrete": (142, 140, 132),
    "olive": (91, 97, 54),
    "olive_dark": (46, 50, 28),
    "khaki": (183, 167, 122),
    "steel": (74, 82, 88),
    "steel_dark": (30, 34, 38),
    "brass": (184, 145, 62),
    "red": (168, 56, 44),
    "white": (228, 224, 208),
    "lamp": (255, 198, 124),
    "day": (214, 224, 222),
    "near": (22, 24, 22),
    "near_light": (78, 82, 74),
}

#: Where the olive paint of the walls stops, in `v` of the sky.
DADO = 0.60


def star_points(cu: float, cv: float, r: float, inner: float = 0.40) -> list[tuple[float, float]]:
    """The ten corners of a five-point star at `(cu, cv)` with one point up.
    `r` is the radius of the points and `inner` the part of `r` for the
    corners between them."""
    pts = []
    for k in range(10):
        a = math.radians(-90.0 + k * 36.0)
        rr = r if k % 2 == 0 else r * inner
        pts.append((cu + rr * math.cos(a), cv + rr * math.sin(a)))
    return pts


def insignia(rim: Pen, roundel: Pen, star: Pen, cu: float, cv: float, r: float) -> None:
    """The insignia of the faction at `(cu, cv)`, radius `r`: a brass rim
    (`rim`), an olive roundel in it (`roundel`) and a white star on it
    (`star`). Paint the three masks in that order."""
    rim.ellipse(cu, cv, r)
    roundel.ellipse(cu, cv, r * 0.84)
    star.poly(star_points(cu, cv - r * 0.03, r * 0.66))


def _paint_insignia(art: Art, layer: np.ndarray, rims, roundels, stars, fade: float = 0.0) -> None:
    """Paint the three masks of `insignia` on `layer`. `fade` more than 0
    mixes each colour that much to the wall: a mark painted long ago."""
    p = TOWER
    wall = p["wall"]
    art.put(layer, art.mask_of(rims), mix(p["brass"], wall, fade))
    art.put(layer, art.mask_of(roundels), mix(p["olive"], wall, fade))
    art.put(layer, art.mask_of(stars), mix(p["white"], wall, fade))


# The segments of a stencil digit: `(x0, y0, x1, y1)` in parts of the cell.
_SEGMENTS = {
    "a": (0.0, 0.0, 1.0, 0.16),
    "b": (0.80, 0.0, 1.0, 0.5),
    "c": (0.80, 0.5, 1.0, 1.0),
    "d": (0.0, 0.84, 1.0, 1.0),
    "e": (0.0, 0.5, 0.20, 1.0),
    "f": (0.0, 0.0, 0.20, 0.5),
    "g": (0.0, 0.42, 1.0, 0.58),
}
_DIGITS = {"1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd"}


def stencil(pen: Pen, text: str, u: float, v: float, w: float, h: float) -> None:
    """`text` in stencil digits, its top left at `(u, v)`; each digit is
    `w` by `h`. The segments do not touch: the gaps are the bridges of a
    stencil."""
    gap = 0.07
    for index, ch in enumerate(text):
        x = u + index * w * 1.45
        for name in _DIGITS[ch]:
            x0, y0, x1, y1 = _SEGMENTS[name]
            # Each segment is a little short at its two ends.
            if x1 - x0 > y1 - y0:
                x0, x1 = x0 + gap, x1 - gap
            else:
                y0, y1 = y0 + gap, y1 - gap
            pen.rect(x + x0 * w, v + y0 * h, x + x1 * w, v + y1 * h)


def _i_beam(face: Pen, web: Pen, rivets: Pen, cu: float, half: float, v0: float, v1: float, splices: tuple[float, ...] = ()) -> None:
    """A steel column seen a little from the left: the face of its front
    flange (`face`), its web and the edge of its back flange to the right
    (`web`), and two rows of rivets. A splice plate is at each `v` of
    `splices`."""
    face.rect(cu - half, v0, cu + half, v1)
    web.rect(cu + half, v0, cu + half * 1.45, v1)
    web.rect(cu + half * 1.45, v0, cu + half * 1.75, v1, value=150)
    v = v0 + 0.01
    while v < v1:
        for du in (-0.62, 0.62):
            rivets.ellipse(cu + du * half, v, half * 0.13)
        v += 0.022
    for sv in splices:
        face.rect(cu - half * 1.25, sv - 0.018, cu + half * 1.25, sv + 0.018)
        for du in (-0.9, -0.3, 0.3, 0.9):
            for dv in (-0.010, 0.010):
                rivets.ellipse(cu + du * half, sv + dv, half * 0.14)


def _girder(face: Pen, dark: Pen, rivets: Pen, v0: float, v1: float, bay: float) -> None:
    """A riveted girder across the panel, seen from the side, from `v0` to
    `v1`: a flange at the top and the bottom, the web between them in shade,
    and a stiffener each `bay`."""
    flange = (v1 - v0) * 0.24
    face.rect(0.0, v0, 1.0, v0 + flange)
    face.rect(0.0, v1 - flange, 1.0, v1)
    dark.rect(0.0, v0 + flange, 1.0, v1 - flange)
    count = int(round(1.0 / bay))
    for k in range(count + 1):
        u = k / count
        face.rect(u - 0.003, v0 + flange, u + 0.003, v1 - flange)
    for k in range(count * 4 + 1):
        u = k / (count * 4)
        rivets.ellipse(u, v0 + flange * 0.5, flange * 0.22)
        rivets.ellipse(u, v1 - flange * 0.5, flange * 0.22)


def _caged_lamp(metal: Pen, cage: Pen, u: float, v: float, r: float, cord_from: float | None = None) -> None:
    """A lamp in a wire cage at `(u, v)` with a shade over it, on a cord
    from `cord_from` (none for a lamp on a wall)."""
    if cord_from is not None:
        metal.rect(u - r * 0.10, cord_from, u + r * 0.10, v - r * 1.4)
    metal.poly([(u - r * 0.45, v - r * 1.45), (u + r * 0.45, v - r * 1.45), (u + r * 1.25, v - r * 0.7), (u - r * 1.25, v - r * 0.7)])
    cage.line([(u - r * 0.95, v - r * 0.7), (u - r * 0.95, v + r * 0.6), (u, v + r * 1.15), (u + r * 0.95, v + r * 0.6), (u + r * 0.95, v - r * 0.7)], r * 0.16)
    cage.line([(u, v - r * 0.7), (u, v + r * 1.15)], r * 0.14)
    cage.line([(u - r * 0.95, v + r * 0.05), (u + r * 0.95, v + r * 0.05)], r * 0.14)


def _banner(cloth: Pen, trim: Pen, pole: Pen, rims: Pen, roundels: Pen, stars: Pen, cu: float, top: float, w: float, h: float) -> None:
    """A banner of the faction on a brass pole at `top`: olive cloth with a
    straight foot, a khaki stripe down each side and the insignia on it."""
    pole.rect(cu - w * 0.62, top - w * 0.05, cu + w * 0.62, top + w * 0.05)
    pole.ellipse(cu - w * 0.66, top, w * 0.07)
    pole.ellipse(cu + w * 0.66, top, w * 0.07)
    cloth.rect(cu - w * 0.5, top, cu + w * 0.5, top + h)
    for side in (-1, 1):
        trim.rect(cu + side * w * 0.36 - w * 0.04, top, cu + side * w * 0.36 + w * 0.04, top + h)
    trim.rect(cu - w * 0.5, top + h - w * 0.10, cu + w * 0.5, top + h)
    insignia(rims, roundels, stars, cu, top + h * 0.40, w * 0.27)


def _sky(art: Art) -> np.ndarray:
    """The far wall of the shaft in shade: poured concrete in lifts, olive
    paint below `DADO`, and slit windows with bars high up."""
    p = TOWER
    olive_wall = mix(p["olive_dark"], p["wall"], 0.25)
    layer = art.opaque(art.ramp([(0.0, p["deep"]), (0.20, p["wall_dark"]), (0.42, p["wall"]), (0.82, p["wall_dark"]), (1.0, p["deep"])]))
    art.tint(layer, smoothstep(DADO, DADO + 0.002, art.v), olive_wall, 0.62)
    # The lifts and the panels of the forms, and the holes of the form ties.
    lifts = (np.mod(art.v * 16.0, 1.0) < 0.04).astype(np.float32)
    joints = (np.mod(art.u * 8.0, 1.0) < 0.02).astype(np.float32)
    art.shade(layer, art.blur(np.maximum(lifts, joints), 0.5), 0.20)
    art.shade(layer, art.noise("board marks", cells=10.0, octaves=3, stretch=8.0), 0.07)
    ties, tie_pen = art.drawing()
    for i in range(16):
        for j in range(16):
            tie_pen.ellipse((i + 0.5) / 16.0, (j + 0.5) / 16.0, 0.0016)
    art.shade(layer, art.mask_of(ties, blur=0.3), 0.18)
    # The line of khaki paint at the top of the olive.
    art.put(layer, (np.abs(art.v - DADO) < 0.0028).astype(np.float32), mix(p["khaki"], p["wall"], 0.45), 0.85)
    # Slit windows, with the day in them and two bars across.
    splays, splay_pen = art.drawing()
    glass, glass_pen = art.drawing()
    bars, bar_pen = art.drawing()
    for k in range(5):
        cu = k / 4.0
        splay_pen.poly([(cu - 0.020, 0.235), (cu + 0.020, 0.235), (cu + 0.020, 0.395), (cu - 0.020, 0.395)])
        glass_pen.rect(cu - 0.007, 0.25, cu + 0.007, 0.38)
        bar_pen.rect(cu - 0.0012, 0.25, cu + 0.0012, 0.38)
        for v in (0.29, 0.34):
            bar_pen.rect(cu - 0.008, v - 0.0015, cu + 0.008, v + 0.0015)
        art.light(layer, art.spot(cu, 0.42, 0.09, 1.6, squash=0.55), p["day"], 0.10)
    art.light(layer, art.mask_of(splays, blur=0.6), p["concrete"], 0.12)
    art.put(layer, art.mask_of(glass, blur=0.3), mix(p["day"], p["wall"], 0.15))
    art.light(layer, art.mask_of(glass, blur=9.0), p["day"], 0.22)
    art.put(layer, art.mask_of(bars, blur=0.2), p["steel_dark"])
    # The warm light of the lamps of the shaft on the wall.
    for u in (0.0, 0.5, 1.0):
        art.light(layer, art.spot(u, 0.47, 0.22, 1.6, squash=1.5), p["lamp"], 0.16)
    # The roof and the floor are in deep shade.
    art.shade(layer, smoothstep(0.26, 0.0, art.v), 0.45)
    art.shade(layer, smoothstep(0.80, 1.0, art.v), 0.35)
    art.grain(layer, "grain")
    return layer


def _far(art: Art) -> np.ndarray:
    """The shaft: two steel columns, concrete pilasters, a girder at the deck
    above and at the deck below, and cross braces between them. In the
    middle, between two pilasters with a caged lamp on each, the insignia is
    painted on the wall under a slit window. Each pilaster has a band of
    warning stripes and the number of its bay stencilled on it."""
    p = TOWER
    top, low = 0.10, 0.86
    face, face_pen = art.drawing()
    web, web_pen = art.drawing()
    rivets, rivet_pen = art.drawing()
    braces, brace_pen = art.drawing()
    for cu in (0.25, 0.75):
        _i_beam(face_pen, web_pen, rivet_pen, cu, 0.016, 0.0, 1.0, splices=(0.47,))
    _girder(face_pen, web_pen, rivet_pen, top, top + 0.034, 0.125)
    _girder(face_pen, web_pen, rivet_pen, low, low + 0.034, 0.125)
    # Cross braces of flat bar in the bays at the seam of the panel,
    # with a gusset plate at each end and a plate where they cross.
    for a, b in ((0.03, 0.22), (0.78, 0.97)):
        v0, v1 = top + 0.034, low
        brace_pen.line([(a, v0), (b, v1)], 0.0045)
        brace_pen.line([(b, v0), (a, v1)], 0.0045)
        for gu, gv in ((a, v0), (b, v0), (a, v1), (b, v1)):
            brace_pen.poly([(gu - 0.010, gv), (gu + 0.010, gv), (gu, gv + (0.03 if gv == v0 else -0.03))])
        brace_pen.ellipse((a + b) * 0.5, (v0 + v1) * 0.5, 0.007)
    steel_mask = np.maximum(art.mask_of(face), art.mask_of(braces))
    layer = solid(art, steel_mask, mix(p["steel"], p["concrete"], 0.15), p["steel_dark"], 0.1, 0.9, "steel", 0.06)
    art.shade(layer, art.mask_of(web), 0.42)
    art.put(layer, art.mask_of(web) * (1.0 - steel_mask), mix(p["steel_dark"], p["steel"], 0.35))
    art.light(layer, art.rim(steel_mask, 0.003, 0.0, 0.5) * steel_mask, p["lamp"], 0.16)
    art.shade(layer, art.mask_of(rivets, blur=0.2), 0.32)
    art.light(layer, art.shift(art.mask_of(rivets, blur=0.2), -0.0008, -0.0008) * steel_mask, p["concrete"], 0.18)
    # Concrete pilasters, olive to the height of the wall's paint.
    pilasters, pilaster_pen = art.drawing()
    for cu, half in ((0.0, 0.028), (1.0, 0.028), (0.40, 0.022), (0.60, 0.022)):
        pilaster_pen.rect(cu - half, top + 0.034, cu + half, low)
    pil = art.mask_of(pilasters)
    concrete = solid(art, pil, mix(p["concrete"], p["wall"], 0.45), p["wall_dark"], 0.15, 0.85, "pilaster", 0.10)
    art.tint(concrete, pil * smoothstep(0.585, 0.587, art.v), mix(p["olive"], p["wall_dark"], 0.35), 0.75)
    stripes = (np.mod((art.u + art.v) * 90.0, 1.0) < 0.5).astype(np.float32)
    band = pil * (np.abs(art.v - 0.57) < 0.012)
    art.put(concrete, band * stripes, mix(p["red"], p["wall"], 0.30))
    art.put(concrete, band * (1.0 - stripes), mix(p["khaki"], p["wall"], 0.30))
    numbers, number_pen = art.drawing()
    for cu, text in ((0.40, "2"), (0.60, "3")):
        stencil(number_pen, text, cu - 0.009, 0.47, 0.018, 0.032)
    art.put(concrete, art.mask_of(numbers) * pil, mix(p["khaki"], p["wall"], 0.35))
    art.light(concrete, art.rim(pil, 0.004, 0.0, 0.6) * pil, p["lamp"], 0.12)
    art.shade(concrete, art.rim(pil, -0.005, 0.0, 0.8) * pil, 0.30)
    layer = art.over(concrete, layer)
    # The insignia painted on the wall between the two pilasters, a little
    # faded, and a louvre of a vent in the bay at the seam of the panel.
    rims, rim_pen = art.drawing()
    roundels, roundel_pen = art.drawing()
    stars, star_pen = art.drawing()
    insignia(rim_pen, roundel_pen, star_pen, 0.5, 0.45, 0.050)
    _paint_insignia(art, layer, rims, roundels, stars, fade=0.42)
    louvre, louvre_pen = art.drawing()
    slats, slat_pen = art.drawing()
    for cu in (0.125, 0.875):
        louvre_pen.rect(cu - 0.03, 0.36, cu + 0.03, 0.46)
        for k in range(8):
            slat_pen.rect(cu - 0.026, 0.367 + k * 0.0115, cu + 0.026, 0.372 + k * 0.0115)
    art.put(layer, art.mask_of(louvre), p["steel_dark"])
    art.put(layer, art.mask_of(slats), mix(p["steel"], p["wall"], 0.3))
    art.tint(layer, np.ones_like(art.u), p["wall_dark"], 0.30)
    # A caged lamp on a bracket on each of the two middle pilasters.
    metal, metal_pen = art.drawing()
    cage, cage_pen = art.drawing()
    points = []
    for cu in (0.40, 0.60):
        metal_pen.rect(cu - 0.003, 0.385, cu + 0.003, 0.405)
        _caged_lamp(metal_pen, cage_pen, cu, 0.418, 0.008)
        points.append((cu, 0.418, 0.0055))
    art.put(layer, art.mask_of(metal), p["steel_dark"])
    lamps(art, layer, points, p["lamp"], halo=7.0, strength=0.85)
    art.put(layer, art.mask_of(cage), p["steel_dark"], 0.8)
    return layer


def _near(art: Art) -> np.ndarray:
    """The nearer structure: a riveted girder under the deck above with pipes
    and a cable tray along it, caged lamps and two banners that hang from it,
    a pipe and a conduit that go down, and a lighter girder at the deck below."""
    p = TOWER
    face, face_pen = art.drawing()
    web, web_pen = art.drawing()
    rivets, rivet_pen = art.drawing()
    g0, g1 = 0.285, 0.335
    _girder(face_pen, web_pen, rivet_pen, g0, g1, 0.10)
    _girder(face_pen, web_pen, rivet_pen, 0.775, 0.80, 0.10)
    # Columns at the sides of the shaft.
    for cu in (0.17, 0.83):
        _i_beam(face_pen, web_pen, rivet_pen, cu, 0.022, 0.0, 1.0, splices=(0.56,))
        # A knee brace from the column to the girder.
        side = 1.0 if cu < 0.5 else -1.0
        face_pen.poly([(cu + side * 0.022, g1), (cu + side * 0.09, g1), (cu + side * 0.022, g1 + 0.07)])
        web_pen.poly([(cu + side * 0.034, g1 + 0.006), (cu + side * 0.068, g1 + 0.006), (cu + side * 0.034, g1 + 0.04)])
    # Pipes along under the girder, with flanges, and a cable tray.
    for v, r in ((0.347, 0.0065), (0.362, 0.0045)):
        face_pen.rect(0.0, v - r, 1.0, v + r)
        for k in range(10):
            u = (k + 0.37) / 10.0
            face_pen.rect(u - 0.004, v - r - 0.003, u + 0.004, v + r + 0.003)
    face_pen.rect(0.0, 0.372, 1.0, 0.376)
    for k in range(20):
        face_pen.rect(k / 20.0 - 0.0012, g1, k / 20.0 + 0.0012, 0.376)
    cables, cable_pen = art.drawing()
    for k in range(10):
        a = (k + 0.15) / 10.0
        cable_pen.curve((a, 0.376), (a + 0.085, 0.376), 0.010 + 0.006 * (k % 3), 0.0022)
    # A pipe that goes down with an elbow and a valve wheel, and a conduit.
    face_pen.rect(0.215, 0.347, 0.227, 0.80)
    face_pen.rect(0.211, 0.52, 0.231, 0.528)
    face_pen.ring(0.221, 0.60, 0.016, 0.003)
    face_pen.line([(0.205, 0.60), (0.237, 0.60)], 0.0025)
    face_pen.line([(0.221, 0.584), (0.221, 0.616)], 0.0025)
    face_pen.rect(0.782, 0.362, 0.788, 0.80)
    face_pen.rect(0.774, 0.47, 0.796, 0.50)
    mask = np.maximum(art.mask_of(face), art.mask_of(cables))
    layer = solid(art, mask, mix(p["near"], p["near_light"], 0.55), p["near"], 0.3, 0.8, "near steel", 0.08)
    art.shade(layer, art.mask_of(web), 0.45)
    art.put(layer, art.mask_of(web) * (1.0 - mask), scale(p["near"], 0.8))
    art.shade(layer, art.mask_of(rivets, blur=0.2), 0.40)
    # Warm light from the lamps on the edges that face down.
    art.light(layer, art.rim(mask, 0.0, -0.003, 0.4) * mask, p["lamp"], 0.40)
    art.light(layer, art.rim(mask, 0.002, 0.0, 0.4) * mask, p["lamp"], 0.15)
    # The banners of the faction.
    cloth, cloth_pen = art.drawing()
    trim, trim_pen = art.drawing()
    pole, pole_pen = art.drawing()
    rims, rim_pen = art.drawing()
    roundels, roundel_pen = art.drawing()
    stars, star_pen = art.drawing()
    for cu in (0.35, 0.65):
        _banner(cloth_pen, trim_pen, pole_pen, rim_pen, roundel_pen, star_pen, cu, 0.39, 0.064, 0.17)
    c = art.mask_of(cloth)
    banner = solid(art, c, scale(p["olive"], 0.74), p["olive_dark"], 0.40, 0.56, "cloth", 0.08)
    folds = 0.5 + 0.5 * np.sin(art.u * math.pi * 2.0 * 70.0)
    art.shade(banner, c * folds, 0.16)
    art.put(banner, art.mask_of(trim) * c, mix(p["khaki"], p["olive_dark"], 0.40))
    art.put(banner, art.mask_of(rims) * c, scale(p["brass"], 0.85))
    art.put(banner, art.mask_of(roundels) * c, p["olive_dark"])
    art.put(banner, art.mask_of(stars) * c, scale(p["white"], 0.78))
    art.put(banner, art.mask_of(pole), scale(p["brass"], 0.8))
    art.shade(banner, art.rim(c, -0.003, 0.0, 0.6) * c, 0.30)
    layer = art.over(layer, banner)
    # Caged lamps on cords from the girder.
    metal, metal_pen = art.drawing()
    cage, cage_pen = art.drawing()
    points = []
    for u, v in ((0.27, 0.43), (0.73, 0.43)):
        _caged_lamp(metal_pen, cage_pen, u, v, 0.011, cord_from=0.376)
        points.append((u, v, 0.007))
    art.put(layer, art.mask_of(metal), p["near"])
    lamps(art, layer, points, p["lamp"], halo=7.0, strength=0.9)
    art.put(layer, art.mask_of(cage), p["near"], 0.85)
    return layer


def _air(art: Art) -> np.ndarray:
    """The air in front: faint beams of day from the slits, dust in the
    light of the lamps, and shade at the sides."""
    p = TOWER
    layer = art.blank()
    art.put(layer, shafts(art, "day beams", 4, 0.08, 0.0, 0.80, 0.035), p["day"], 0.07)
    art.put(layer, fog(art, "lamp dust", 0.46, 0.14, cells=3.0), mix(p["lamp"], p["wall"], 0.55), 0.10)
    art.put(layer, fog(art, "floor dust", 0.74, 0.10), p["wall"], 0.14)
    art.put(layer, motes(art, "dust", 70, 0.30, 0.70, 0.0010, 0.0022), mix(p["lamp"], p["white"], 0.5), 0.30)
    vignette(art, layer, p["deep"], 0.38)
    return layer


def military_tower(layer_key: str, art: Art) -> np.ndarray:
    """The inside of the Iron Bastion, the General's tower: a narrow shaft
    of concrete and riveted steel, lit warm by caged lamps."""
    if layer_key == "sky":
        return _sky(art)
    if layer_key == "far_backplate":
        return _far(art)
    if layer_key == "near_background":
        return _near(art)
    return _air(art)
