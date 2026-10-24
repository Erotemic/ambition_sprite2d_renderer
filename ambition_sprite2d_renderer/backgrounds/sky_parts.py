"""The parts of the Mockingbird's space: the sky its fight climbs into.

In its third phase the fight leaves the sky (`docs/planning/game/bosses.md`,
"The Mockingbird"): the dark comes down from the top, the stars come out, the
planet's limb falls away below, and the moon crosses the room on its lane.
The game poses these parts as the fight climbs
(`presentation/mockingbird_sky.rs` in `ambition_content`); no part of them is
drawn by a shader. Each part is published as its own picture:

- ``mockingbird_space``: the dark, with the band of dust across it. Its lower
  part fades to clear; that soft edge is the front of the dark. The game
  slides it down from above the room as the fight climbs.
- ``mockingbird_stars_far`` and ``mockingbird_stars_near``: two layers of
  stars that tile, of two sizes, so that the two repeats do not agree.
- ``mockingbird_stars_edge``: a strip of stars that thins out to none, under
  the tiled stars, in the soft edge of the dark.
- ``mockingbird_star_glint``: one bright star; the game twinkles a few.
- ``mockingbird_planet``: the top of the planet with its air above it. The
  game moves it down and makes it smaller as the fight climbs.
- ``mockingbird_moon`` and ``mockingbird_moon_halo``.
- ``mockingbird_lane_dash``: one dash of the moon's lane.

The places and sizes the game gives each part are in parts of the room or of
a disc (the constants below). `ambition_content` has the same numbers: change
the two together. `preview` composes a view as the game poses it, without
the game.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .artkit import SUPERSAMPLE, Art, gaussian, seed_of, smoothstep

# ---------------------------------------------------------------------------
# The geometry the game poses the parts by (`mockingbird_sky.rs`)
# ---------------------------------------------------------------------------

#: The space picture at rest (the fight in space), in parts of the room: it
#: spans these `u` (across) and `v` (down).
SPACE_U = (-0.75, 1.75)
SPACE_V = (-1.0, 2.3 / 1.3)
#: Above this `v` the dark is whole; below it, it fades to clear at the
#: bottom of the picture.
DARK_TO_V = 1.0
#: How much higher the space picture is, in room heights, for each step of
#: the climb that is still to come.
CLIMB_RISE = 2.3 / 1.3

#: The planet picture, in parts of the planet's radius from its centre: `x`
#: from `-PLANET_X` to `PLANET_X`, and `y` (down) over `PLANET_Y`.
PLANET_X = 0.68
PLANET_Y = (-1.14, -0.74)

#: The moon's picture spans this many radii each way from its centre; its
#: halo's picture, this many.
MOON_SPAN = 1.04
HALO_SPAN = 2.2

#: The dash of the lane: its picture covers this many world units.
DASH_SIZE = (32.0, 8.0)

#: The published size of each picture, in pixels. A star tile is drawn one
#: pixel to a world unit.
SIZES = {
    "mockingbird_space": (768, 768),
    "mockingbird_stars_far": (512, 512),
    "mockingbird_stars_near": (768, 768),
    "mockingbird_stars_edge": (512, 384),
    "mockingbird_star_glint": (48, 48),
    "mockingbird_planet": (1536, 496),
    "mockingbird_moon": (512, 512),
    "mockingbird_moon_halo": (256, 256),
    "mockingbird_lane_dash": (64, 16),
}


# ---------------------------------------------------------------------------
# The looks
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Look:
    """One treatment of the parts: a palette and a few choices of style."""

    top: tuple[int, int, int]
    bottom: tuple[int, int, int]
    dust: tuple[int, int, int]
    dust_strength: float
    star: tuple[int, int, int]
    sea: tuple[int, int, int]
    land: tuple[int, int, int]
    cloud: tuple[int, int, int]
    air: tuple[int, int, int]
    #: The colour of the thin line of light on the limb (the air, or a
    #: sunrise).
    limb: tuple[int, int, int]
    moon: tuple[int, int, int]
    moon_sea: float
    halo: tuple[int, int, int]
    dash: tuple[int, int, int]
    #: A dark line round the moon, as the game's sprites have.
    outline: bool = False
    #: A hard edge between the lit and the dark side of the moon.
    cel: bool = False
    #: Some near stars are sparkles of four points.
    sparkles: bool = False
    #: Land in a few large round shapes, not in noise.
    round_land: bool = False
    notes: str = field(default="", compare=False)


LOOKS: dict[str, Look] = {
    # The colours of the fight as it was drawn before these parts.
    "night": Look(
        top=(13, 16, 39),
        bottom=(39, 48, 87),
        dust=(120, 72, 168),
        dust_strength=0.50,
        star=(247, 250, 255),
        sea=(39, 93, 149),
        land=(69, 130, 93),
        cloud=(231, 239, 245),
        air=(130, 197, 255),
        limb=(150, 210, 255),
        moon=(236, 234, 224),
        moon_sea=0.70,
        halo=(229, 234, 245),
        dash=(231, 237, 223),
        notes="today's palette, painted",
    ),
    # Shapes as the game's sprites are drawn: a dark line round the moon, a
    # hard edge to its night side, round land, and sparkles.
    "storybook": Look(
        top=(16, 14, 44),
        bottom=(44, 40, 104),
        dust=(70, 150, 190),
        dust_strength=0.34,
        star=(255, 248, 226),
        sea=(46, 110, 186),
        land=(92, 168, 104),
        cloud=(246, 250, 255),
        air=(120, 200, 255),
        limb=(196, 236, 255),
        moon=(242, 236, 214),
        moon_sea=0.78,
        halo=(240, 236, 214),
        dash=(255, 240, 200),
        outline=True,
        cel=True,
        sparkles=True,
        round_land=True,
        notes="outlined, cel moon, sparkles",
    ),
    # Higher and later: violet space and the sun coming up over the limb.
    "dusk": Look(
        top=(18, 10, 36),
        bottom=(58, 34, 86),
        dust=(200, 90, 150),
        dust_strength=0.28,
        star=(255, 236, 220),
        sea=(34, 72, 130),
        land=(84, 112, 82),
        cloud=(250, 226, 214),
        air=(150, 170, 255),
        limb=(255, 186, 110),
        moon=(246, 230, 196),
        moon_sea=0.74,
        halo=(255, 222, 180),
        dash=(255, 214, 170),
        notes="violet, sunrise on the limb",
    ),
}

#: The look the publish step draws.
PUBLISHED = "night"


# ---------------------------------------------------------------------------
# A canvas of any shape
# ---------------------------------------------------------------------------


def _grid(size: tuple[int, int]) -> tuple[np.ndarray, np.ndarray]:
    """`u` and `v` (0 to 1) of each work pixel of a picture of `size`."""
    w, h = size[0] * SUPERSAMPLE, size[1] * SUPERSAMPLE
    return np.meshgrid((np.arange(w, dtype=np.float32) + 0.5) / w, (np.arange(h, dtype=np.float32) + 0.5) / h)


def _noise(shape: tuple[int, int], tag: object, cells: tuple[float, float], octaves: int = 4) -> np.ndarray:
    """Smooth noise 0 to 1 on a work grid of `shape` (rows, columns), with
    `cells` lumps across and down."""
    rng = np.random.default_rng(seed_of("mockingbird sky", tag) % (2**63))
    rows, cols = shape
    total = np.zeros(shape, dtype=np.float32)
    amplitude, norm = 1.0, 0.0
    for octave in range(octaves):
        gx = max(2, int(round(cells[0] * 2**octave)))
        gy = max(2, int(round(cells[1] * 2**octave))) + 1
        grid = rng.random((gy, gx + 1), dtype=np.float32)
        lump = Image.fromarray((grid * 255).astype(np.uint8), "L").resize((cols, rows), Image.BICUBIC)
        total += np.asarray(lump, dtype=np.float32) / 255.0 * amplitude
        norm += amplitude
        amplitude *= 0.5
    total /= norm
    lo, hi = float(total.min()), float(total.max())
    return (total - lo) / max(hi - lo, 1e-6)


def _publish(rgb: np.ndarray, alpha: np.ndarray, size: tuple[int, int], tag: str) -> Image.Image:
    """A work canvas as the picture to publish, as `Art.publish` makes one:
    made small with its colour multiplied by its alpha, an empty pixel given
    the colour of the full ones near it, and dithered."""
    k = SUPERSAMPLE
    w, h = size
    pre = np.dstack([np.clip(rgb, 0, 255) * alpha[:, :, None], alpha]).astype(np.float32)
    small = pre.reshape(h, k, w, k, 4).mean(axis=(1, 3))
    a = small[:, :, 3:4]
    colour = small[:, :, :3] / np.maximum(a, 1e-4)
    wide = gaussian(small, 5.0)
    wide_a = wide[:, :, 3:4]
    full = a[:, :, 0] > 0.5
    mean = colour[full].mean(axis=0) if full.any() else np.zeros(3, dtype=np.float32)
    colour = np.where(a > 4e-3, colour, np.where(wide_a > 1e-3, wide[:, :, :3] / np.maximum(wide_a, 1e-3), mean))
    dither = np.random.default_rng(seed_of("mockingbird sky dither", tag) % (2**63)).random((h, w, 1), dtype=np.float32) - 0.5
    out = np.dstack([np.clip(colour + dither, 0, 255), np.clip(a * 255.0 + dither, 0, 255)])
    return Image.fromarray(np.rint(out).astype(np.uint8), "RGBA")


def _c(colour) -> np.ndarray:
    return np.asarray(colour, dtype=np.float32)


# ---------------------------------------------------------------------------
# The parts
# ---------------------------------------------------------------------------


def space(look: Look) -> Image.Image:
    """The dark, with its band of dust, and its soft lower edge."""
    size = SIZES["mockingbird_space"]
    u, v = _grid(size)
    room_u = SPACE_U[0] + (SPACE_U[1] - SPACE_U[0]) * u
    room_v = SPACE_V[0] + (SPACE_V[1] - SPACE_V[0]) * v
    # Darkest at the top, a little blue over the room's floor.
    t = np.clip(room_v, 0.0, 1.0)[:, :, None]
    rgb = _c(look.top) * (1.0 - t) + _c(look.bottom) * t
    # A band of dust that crosses the room from the upper left, in lumps.
    lumps = _noise(u.shape, ("dust", look.dust), (7.0, 5.0), octaves=5)
    band = np.clip(1.0 - np.abs((room_v - 0.30) - (room_u - 0.5) * 0.45) / 0.34, 0.0, 1.0) ** 1.5
    dust = smoothstep(0.35, 0.85, lumps) * band * look.dust_strength
    rgb = 255.0 - (255.0 - rgb) * (1.0 - _c(look.dust)[None, None, :] / 255.0 * dust[:, :, None])
    # The front of the dark: whole above `DARK_TO_V`, and clear at the bottom.
    alpha = 1.0 - smoothstep(DARK_TO_V, SPACE_V[1], room_v)
    return _publish(rgb, alpha.astype(np.float32), size, "space")


def _stars(name: str, look: Look, count: int, radius: tuple[float, float], bright: tuple[float, float], fade_down: bool = False) -> Image.Image:
    """`count` stars on a tile that repeats across (and down, unless
    `fade_down`, where there are fewer stars lower on the strip and none at
    its bottom). `radius` is in world units, the same as pixels here."""
    w, h = SIZES[name]
    art_w, art_h = w * SUPERSAMPLE, h * SUPERSAMPLE
    rng = np.random.default_rng(seed_of("mockingbird sky", name) % (2**63))
    dots = Image.new("L", (art_w, art_h), 0)
    glow = Image.new("L", (art_w, art_h), 0)
    spikes = Image.new("L", (art_w, art_h), 0)
    dot_pen, glow_pen, spike_pen = ImageDraw.Draw(dots), ImageDraw.Draw(glow), ImageDraw.Draw(spikes)
    placed = 0
    while placed < count:
        x, y = rng.random() * w, rng.random() * h
        if fade_down:
            # Fewer stars lower down, and none near either edge of the strip.
            if y < 4.0 or y > h - 4.0 or rng.random() > (1.0 - y / h) ** 1.6:
                continue
        r = rng.uniform(*radius)
        value = int(255 * rng.uniform(*bright))
        offsets = [(dx, dy) for dx in (-w, 0, w) for dy in ((-h, 0, h) if not fade_down else (0,))]
        for dx, dy in offsets:
            cx, cy = (x + dx) * SUPERSAMPLE, (y + dy) * SUPERSAMPLE
            rr = r * SUPERSAMPLE
            dot_pen.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=value)
            gr = rr * 2.6
            glow_pen.ellipse([cx - gr, cy - gr, cx + gr, cy + gr], fill=value // 3)
            if look.sparkles and r > radius[1] * 0.8:
                arm, thin = rr * 4.0, max(1.0, rr * 0.35)
                spike_pen.polygon([(cx, cy - arm), (cx + thin, cy), (cx, cy + arm), (cx - thin, cy)], fill=value)
                spike_pen.polygon([(cx - arm, cy), (cx, cy - thin), (cx + arm, cy), (cx, cy + thin)], fill=value)
        placed += 1
    from PIL import ImageFilter

    soft = np.asarray(glow.filter(ImageFilter.GaussianBlur(3.0 * SUPERSAMPLE)), dtype=np.float32) / 255.0
    core = np.asarray(dots.filter(ImageFilter.GaussianBlur(0.35 * SUPERSAMPLE)), dtype=np.float32) / 255.0
    spike = np.asarray(spikes.filter(ImageFilter.GaussianBlur(0.3 * SUPERSAMPLE)), dtype=np.float32) / 255.0
    alpha = np.clip(core + soft * 0.22 + spike * 0.8, 0.0, 1.0)
    rgb = np.broadcast_to(_c(look.star), (art_h, art_w, 3)).copy()
    return _publish(rgb, alpha, (w, h), name)


def stars_far(look: Look) -> Image.Image:
    return _stars("mockingbird_stars_far", look, 110, (0.55, 1.15), (0.30, 0.85))


def stars_near(look: Look) -> Image.Image:
    return _stars("mockingbird_stars_near", look, 22, (0.9, 1.6), (0.6, 1.0))


def stars_edge(look: Look) -> Image.Image:
    return _stars("mockingbird_stars_edge", look, 36, (0.55, 1.5), (0.30, 0.95), fade_down=True)


def star_glint(look: Look) -> Image.Image:
    """One bright star with a soft glow and four short rays."""
    art = Art(SIZES["mockingbird_star_glint"][0], "mockingbird glint")
    layer = art.blank()
    d = np.sqrt((art.u - 0.5) ** 2 + (art.v - 0.5) ** 2)
    glow = np.clip(1.0 - d / 0.5, 0.0, 1.0) ** 3
    rays = np.clip(1.0 - np.abs(art.u - 0.5) / 0.035, 0, 1) * np.clip(1.0 - np.abs(art.v - 0.5) / 0.42, 0, 1) ** 2
    rays = np.maximum(rays, np.clip(1.0 - np.abs(art.v - 0.5) / 0.035, 0, 1) * np.clip(1.0 - np.abs(art.u - 0.5) / 0.42, 0, 1) ** 2)
    core = smoothstep(0.09, 0.03, d)
    art.put(layer, glow * 0.45, look.star)
    art.put(layer, rays * 0.75, look.star)
    art.put(layer, core, (255, 255, 255))
    return art.publish(layer)


def planet(look: Look) -> Image.Image:
    """The top of the planet and the air over it. It is lit by the air near
    its limb and darker into its body, the same all round: the game turns
    and scales it, and no side of it is the sun's."""
    size = SIZES["mockingbird_planet"]
    u, v = _grid(size)
    x = (u * 2.0 - 1.0) * PLANET_X
    y = PLANET_Y[0] + (PLANET_Y[1] - PLANET_Y[0]) * v
    r = np.sqrt(x * x + y * y)
    # Distance outside the limb, in radii (negative inside).
    d = r - 1.0
    edge = 1.5 / (size[1] * SUPERSAMPLE / (PLANET_Y[1] - PLANET_Y[0]))
    disc = smoothstep(edge, -edge, d)
    # The ground, seen on a sphere: squashed toward the limb.
    depth = np.clip(-d, 0.0, 1.0)
    shape = u.shape
    if look.round_land:
        image = Image.new("L", (shape[1], shape[0]), 0)
        pen = ImageDraw.Draw(image)
        rng = np.random.default_rng(seed_of("planet land round") % (2**63))
        for _ in range(26):
            cx, cy = rng.uniform(0.0, 1.0) * shape[1], rng.uniform(0.2, 1.1) * shape[0]
            rx, ry = rng.uniform(0.02, 0.06) * shape[1], rng.uniform(0.08, 0.22) * shape[0]
            pen.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
        from PIL import ImageFilter

        land = np.asarray(image.filter(ImageFilter.GaussianBlur(6)), dtype=np.float32) / 255.0
        land = smoothstep(0.45, 0.55, land)
        cloud = smoothstep(0.62, 0.70, _noise(shape, "planet cloud round", (20.0, 5.0), octaves=3))
    else:
        land = smoothstep(0.50, 0.56, _noise(shape, "planet land", (16.0, 4.0), octaves=5))
        cloud = smoothstep(0.50, 0.76, _noise(shape, "planet cloud", (28.0, 6.0), octaves=5))
    surface = _c(look.sea) * (1.0 - land[:, :, None]) + _c(look.land) * land[:, :, None]
    surface = surface * (1.0 - 0.85 * cloud[:, :, None]) + _c(look.cloud) * (0.85 * cloud[:, :, None])
    # Lit near its limb by the air, darker into its body.
    surface = surface * (1.0 - 0.55 * smoothstep(0.0, 0.26, depth))[:, :, None]
    near_limb = np.exp(np.minimum(d, 0.0) / 0.012)
    surface = 255.0 - (255.0 - surface) * (1.0 - _c(look.air)[None, None, :] / 255.0 * (0.55 * near_limb)[:, :, None])
    # The air: a thin bright line on the limb and a glow over it that fades
    # to nothing before the top of the picture.
    out = np.maximum(d, 0.0)
    line = np.exp(-out / 0.006) * 0.85
    glow = np.exp(-out / 0.03) * 0.42 * smoothstep(-PLANET_Y[0] - 1.0, 0.03, out)
    air_alpha = np.clip(line + glow, 0.0, 1.0) * (1.0 - disc)
    air = (_c(look.limb) * line[:, :, None] + _c(look.air) * glow[:, :, None]) / np.maximum(line + glow, 1e-4)[:, :, None]
    alpha = disc + air_alpha
    weight = (disc / np.maximum(alpha, 1e-4))[:, :, None]
    rgb = surface * weight + air * (1.0 - weight)
    # The limb itself catches the light of the air.
    rim = np.exp(-np.abs(d) / 0.004) * disc
    rgb = rgb * (1.0 - rim[:, :, None] * 0.6) + _c(look.limb) * (rim[:, :, None] * 0.6)
    return _publish(rgb, np.clip(alpha, 0.0, 1.0).astype(np.float32), size, "planet")


def moon(look: Look) -> Image.Image:
    """The moon, lit from the upper left, with seas and craters."""
    art = Art(SIZES["mockingbird_moon"][0], "mockingbird moon")
    qx, qy = (art.u - 0.5) * 2.0 * MOON_SPAN, (art.v - 0.5) * 2.0 * MOON_SPAN
    r = np.sqrt(qx * qx + qy * qy)
    nz = np.sqrt(np.clip(1.0 - r * r, 0.0, 1.0))
    light = np.clip((qx * -0.45 + qy * -0.55 + nz * 0.70) / math.sqrt(0.45**2 + 0.55**2 + 0.70**2), 0.0, 1.0)
    seas = smoothstep(0.50, 0.72, art.noise("moon seas", cells=4.0, octaves=4))
    tone = 0.92 - (0.92 - look.moon_sea * 0.92) * seas
    # Craters: a dark bowl and a bright rim.
    rng = art.rand("craters")
    for _ in range(18):
        cr = rng.uniform(0.05, 0.16)
        while True:
            cx, cy = rng.uniform(-0.9, 0.9), rng.uniform(-0.9, 0.9)
            if math.hypot(cx, cy) + cr * 0.6 < 0.98:
                break
        cd = np.sqrt((qx - cx) ** 2 + (qy - cy) ** 2) / cr
        bowl = 1.0 - smoothstep(0.55, 0.95, cd)
        rim = smoothstep(0.80, 1.0, cd) * (1.0 - smoothstep(1.0, 1.25, cd))
        tone = tone - bowl * 0.11 + rim * 0.06
    if look.cel:
        shade = np.where(light > 0.18, 1.0, 0.42) * (0.85 + 0.15 * light)
    else:
        shade = 0.22 + 0.78 * light
    # Lit in linear light, as light adds.
    linear = (_c(look.moon) / 255.0) ** 2.2
    rgb = 255.0 * (linear[None, None, :] * (tone * shade)[:, :, None]) ** (1.0 / 2.2)
    layer = art.blank()
    edge = 1.2 / (art.n / (2.0 * MOON_SPAN))
    disc = smoothstep(1.0, 1.0 - edge, r)
    art.put(layer, disc, rgb)
    if look.outline:
        ring = smoothstep(1.0 + edge, 1.0, r) * smoothstep(0.96 - edge, 0.96, r)
        art.put(layer, ring, (28, 26, 44))
    return art.publish(layer)


def moon_halo(look: Look) -> Image.Image:
    """The light round the moon, out to `HALO_SPAN` radii."""
    art = Art(SIZES["mockingbird_moon_halo"][0], "mockingbird halo")
    r = np.sqrt((art.u - 0.5) ** 2 + (art.v - 0.5) ** 2) * 2.0 * HALO_SPAN
    halo = np.exp(-np.maximum(r - 1.0, 0.0) * 3.6) * 0.40 * smoothstep(HALO_SPAN, HALO_SPAN - 0.4, r)
    layer = art.blank()
    art.put(layer, halo, look.halo)
    return art.publish(layer)


def lane_dash(look: Look) -> Image.Image:
    """One dash of the moon's lane: a faint pale capsule, 28 by 5 of the
    `DASH_SIZE` world units its picture covers."""
    w, h = SIZES["mockingbird_lane_dash"]
    u, v = _grid((w, h))
    x, y = (u - 0.5) * DASH_SIZE[0], (v - 0.5) * DASH_SIZE[1]
    half_len, half_w = 14.0 - 2.5, 2.5
    dx = np.maximum(np.abs(x) - half_len, 0.0)
    d = np.sqrt(dx * dx + y * y) - half_w
    alpha = smoothstep(0.6, -0.6, d) * 0.30
    rgb = np.broadcast_to(_c(look.dash), u.shape + (3,)).copy()
    return _publish(rgb, alpha.astype(np.float32), (w, h), "dash")


PARTS = {
    "mockingbird_space": space,
    "mockingbird_stars_far": stars_far,
    "mockingbird_stars_near": stars_near,
    "mockingbird_stars_edge": stars_edge,
    "mockingbird_star_glint": star_glint,
    "mockingbird_planet": planet,
    "mockingbird_moon": moon,
    "mockingbird_moon_halo": moon_halo,
    "mockingbird_lane_dash": lane_dash,
}


def render(name: str, look: str = PUBLISHED) -> Image.Image:
    image = PARTS[name](LOOKS[look])
    assert image.size == SIZES[name], (name, image.size)
    return image


# ---------------------------------------------------------------------------
# A view as the game poses the parts (`mockingbird_sky.rs`)
# ---------------------------------------------------------------------------

ROOM = (1280.0, 720.0)
MOON_RADIUS = 120.0
#: The lane of the moon (`moon_lane` in `ambition_content_modules`).
LANE = (ROOM[0] + MOON_RADIUS + 40.0, -MOON_RADIUS - 40.0, ROOM[1] * 0.46, ROOM[1] * 0.07)


def _smooth(lo: float, hi: float, x: float) -> float:
    t = min(max((x - lo) / (hi - lo), 0.0), 1.0)
    return t * t * (3.0 - 2.0 * t)


def _place(canvas: Image.Image, picture: Image.Image, centre: tuple[float, float], size: tuple[float, float], alpha: float, scale: float) -> None:
    w, h = max(1, int(round(size[0] * scale))), max(1, int(round(size[1] * scale)))
    if alpha <= 0.0 or w > 20000 or h > 20000:
        return
    image = picture.resize((w, h), Image.BILINEAR)
    if alpha < 1.0:
        a = np.asarray(image).copy()
        a[:, :, 3] = (a[:, :, 3].astype(np.float32) * alpha).astype(np.uint8)
        image = Image.fromarray(a, "RGBA")
    x0, y0 = int(round(centre[0] * scale - w / 2)), int(round(centre[1] * scale - h / 2))
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    layer.paste(image, (x0, y0))
    canvas.alpha_composite(layer)


def _tile(canvas: Image.Image, tile: Image.Image, top: float, bottom: float, scale: float, alpha: float, wrap_y: bool = True) -> None:
    tw, th = tile.size
    rows = range(int(math.floor(top / th)), int(math.ceil(bottom / th))) if wrap_y else [0]
    for row in rows:
        y = row * th if wrap_y else top
        for col in range(-1, int(ROOM[0] / tw) + 2):
            _place(canvas, tile, (col * tw + tw / 2, y + th / 2), (tw, th), alpha, scale)


def preview(parts: dict[str, Image.Image], backdrop: Image.Image, ascent: float, moon_u: float | None, width: int = 640) -> Image.Image:
    """The room (fit whole into `width` pixels) at `ascent`, with the moon
    `moon_u` of the way along its lane (`None`: no moon), over `backdrop`."""
    scale = width / ROOM[0]
    canvas = backdrop.resize((width, int(ROOM[1] * scale))).convert("RGBA")
    rise = -ROOM[1] * CLIMB_RISE * (1.0 - ascent)
    su, sv = SPACE_U, SPACE_V
    centre = (ROOM[0] * (su[0] + su[1]) / 2, ROOM[1] * (sv[0] + sv[1]) / 2 + rise)
    _place(canvas, parts["mockingbird_space"], centre, (ROOM[0] * (su[1] - su[0]), ROOM[1] * (sv[1] - sv[0])), 1.0, scale)
    stars = _smooth(0.15, 0.7, ascent)
    dark_to = ROOM[1] * DARK_TO_V + rise
    _tile(canvas, parts["mockingbird_stars_far"], dark_to - ROOM[1] * 2.0, dark_to, scale, stars)
    _tile(canvas, parts["mockingbird_stars_near"], dark_to - ROOM[1] * 2.0, dark_to, scale, stars)
    _tile(canvas, parts["mockingbird_stars_edge"], dark_to, dark_to + 384, scale, stars, wrap_y=False)
    climb = _smooth(0.25, 1.0, ascent)
    radius = ROOM[0] * (4.0 + (1.25 - 4.0) * climb)
    top = ROOM[1] * (0.62 + (0.90 - 0.62) * climb)
    py = top + radius + (PLANET_Y[0] + PLANET_Y[1]) / 2 * radius
    _place(canvas, parts["mockingbird_planet"], (ROOM[0] / 2, py), (2 * PLANET_X * radius, (PLANET_Y[1] - PLANET_Y[0]) * radius), _smooth(0.30, 0.75, ascent), scale)
    in_space = _smooth(0.92, 1.0, ascent)
    for k in range(int((LANE[0] - LANE[1]) / 56) + 2):
        x = LANE[1] + 56.0 * (k + 0.75)
        lu = (LANE[0] - x) / (LANE[0] - LANE[1])
        if 0.0 < lu < 1.0:
            _place(canvas, parts["mockingbird_lane_dash"], (x, LANE[2] - LANE[3] * math.sin(lu * math.pi)), DASH_SIZE, in_space, scale)
    if moon_u is not None:
        mx = LANE[0] + (LANE[1] - LANE[0]) * moon_u
        my = LANE[2] - LANE[3] * math.sin(moon_u * math.pi)
        _place(canvas, parts["mockingbird_moon_halo"], (mx, my), (2 * HALO_SPAN * MOON_RADIUS,) * 2, 1.0, scale)
        _place(canvas, parts["mockingbird_moon"], (mx, my), (2 * MOON_SPAN * MOON_RADIUS,) * 2, 1.0, scale)
    return canvas


def candidate_sheet(looks: list[str], backdrop: Image.Image, moments: list[tuple[str, float, float | None]], width: int = 640) -> Image.Image:
    """One row for each look, one column for each moment `(label, ascent,
    moon_u)`, each labelled."""
    label_h = 26
    height = int(ROOM[1] * width / ROOM[0])
    sheet = Image.new("RGB", (width * len(moments), (height + label_h) * len(looks)), (24, 24, 28))
    pen = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 16)
    except OSError:
        font = ImageFont.load_default()
    for row, name in enumerate(looks):
        parts = {part: render(part, name) for part in PARTS}
        for column, (label, ascent, moon_u) in enumerate(moments):
            view = preview(parts, backdrop, ascent, moon_u, width)
            y = row * (height + label_h)
            sheet.paste(view.convert("RGB"), (column * width, y + label_h))
            pen.text((column * width + 8, y + 4), f"{chr(65 + row)}. {name} ({LOOKS[name].notes}): {label}", fill=(235, 235, 235), font=font)
    return sheet


__all__ = ["LOOKS", "PARTS", "PUBLISHED", "SIZES", "candidate_sheet", "preview", "render"]
