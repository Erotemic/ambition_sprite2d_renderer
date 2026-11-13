"""Props for the haunted floors of Hylbert's Hotel (the Math dimension).
Jon, 2026-10-31: "background and room props so we can actually build a
level. part of the hotel will have a spectral Gap ... even though it looks
like a big hole in the ground, it actually stabilizes the entire space
preventing it from rotating wildly."

Each prop is its own target (``TARGETS``), drawn on its own canvas, feet
(or its hanging point) on the canvas edge it meets:

- ``hylbert_spectral_gap``: the SPECTRAL GAP, a hole in the floor. In it two
  glowing bands, its eigenvalues (lambda-1 near the lip, lambda-2 deep), with
  dark between them (the gap), and over it a ghostly GIMBAL whose rings hold
  dead level while everything else sways: it is what steadies the room.
  ``idle`` 8 frames (the bands breathe, the gimbal's light circles).
- ``hylbert_wallpaper_panel``: a background wall section, plum damask of
  ellipses and their axes over a wainscot, the paper peeling. Panels laid
  side by side meet with no seam.
- ``hylbert_room_door``: a guest room door, its brass plate an infinity
  (there is always one more room), teal light under it; ``idle`` 4 (the light
  flickers).
- ``hylbert_lift_gate``: the service lift's brass scissor gate, shut, chained
  and padlocked, an OUT OF ORDER tag on the chain; ``idle`` 4 (the tag
  swings, light leaks round the lock). The barrier in front of the lift.
- ``hylbert_treasury_seal``: the treasury's iron grille with a ring of
  spectral light locked across it; ``idle`` 8 (the ring pulses and turns).
  The barrier the Gram Reaper's fall takes away.
- ``hylbert_wall_sconce``: a brass sconce with a teal ghost flame, ``idle`` 6.
- ``hylbert_chandelier``: a cobwebbed brass chandelier with teal flames,
  hanging from its top edge, ``idle`` 6.
- ``hylbert_luggage_cart``: the bellhop's brass luggage cart, cases piled on.
- ``hylbert_floor_strip``: a strip of cracked checker marble floor that tiles.

No drop shadows; the art is the look (shaders only polish it).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
SUPER = 4

OUTLINE: RGBA = (22, 14, 30, 255)
PLUM: RGBA = (74, 36, 78, 255)
PLUM_DARK: RGBA = (46, 22, 52, 255)
PLUM_LIGHT: RGBA = (112, 62, 116, 255)
WOOD: RGBA = (70, 40, 34, 255)
WOOD_LIGHT: RGBA = (108, 66, 52, 255)
BRASS: RGBA = (204, 156, 72, 255)
BRASS_DARK: RGBA = (134, 96, 44, 255)
VOID: RGBA = (8, 6, 16, 255)
TEAL: RGBA = (92, 238, 214, 255)
TEAL_CORE: RGBA = (214, 255, 246, 255)
MARBLE_A: RGBA = (196, 188, 204, 255)
MARBLE_B: RGBA = (62, 52, 76, 255)
LEATHER: RGBA = (120, 60, 40, 255)
WEB: RGBA = (220, 220, 230, 110)


def _a(c: RGBA, a: float) -> RGBA:
    return (c[0], c[1], c[2], int(max(0.0, min(1.0, a)) * c[3]))


class _Canvas:
    """A supersampled RGBA canvas in frame pixels."""

    def __init__(self, size: Tuple[int, int]):
        self.size = size
        self.img = Image.new("RGBA", (size[0] * SUPER, size[1] * SUPER), (0, 0, 0, 0))
        self.d = blending_draw(self.img)

    @staticmethod
    def p(*xy: float) -> List[float]:
        return [v * SUPER for v in xy]

    def rect(self, x0, y0, x1, y1, fill, outline=OUTLINE, w=1.2):
        self.d.rectangle(self.p(x0, y0, x1, y1), fill=fill, outline=outline, width=int(w * SUPER) if outline else 0)

    def ellipse(self, x0, y0, x1, y1, fill=None, outline=OUTLINE, w=1.2):
        self.d.ellipse(self.p(x0, y0, x1, y1), fill=fill, outline=outline, width=int(w * SUPER) if outline else 0)

    def poly(self, pts, fill, outline=OUTLINE):
        self.d.polygon([(x * SUPER, y * SUPER) for x, y in pts], fill=fill, outline=outline)

    def line(self, pts, fill, w=1.0):
        self.d.line([(x * SUPER, y * SUPER) for x, y in pts], fill=fill, width=max(1, int(w * SUPER)), joint="curve")

    def glow(self, draw_fn: Callable[[ImageDraw.ImageDraw], None], blur: float):
        """Light: drawn on its own layer, softened, laid over."""
        layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        draw_fn(blending_draw(layer))
        self.img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(blur * SUPER)))
        self.d = blending_draw(self.img)

    def done(self) -> Image.Image:
        return self.img.resize(self.size, Image.Resampling.LANCZOS)


# --- the haunt: what makes any prop spooky ----------------------------------------


def _shade_and_grime(c: _Canvas, top: float = 0.55, bottom: float = 0.75, seed: int = 0, wrap_x: bool = False) -> None:
    """SHADING and GRIME over everything drawn so far: darker toward the top
    and the foot (lit from a ghost light at the middle), a mottle of grime,
    and a cold teal cast in the shadows. Alpha is kept.

    ``wrap_x``: the grime wraps round from the right edge to the left, so a
    prop laid end to end (a wall, a floor) shows no seam where two meet."""
    px = np.asarray(c.img, np.float32)
    h, w = px.shape[:2]
    y = np.linspace(0.0, 1.0, h)[:, None]
    light = 1.0 - (1.0 - top) * np.clip(1.0 - y / 0.5, 0, 1) ** 1.5 - (1.0 - bottom) * np.clip((y - 0.5) / 0.5, 0, 1) ** 1.5
    rng = np.random.default_rng(seed)
    cells = (rng.random((max(1, h // 24), max(1, w // 24))) * 255).astype(np.uint8)
    if wrap_x:
        # Three copies side by side, scaled together: the middle one meets
        # its own edges on both sides.
        grime = Image.fromarray(np.tile(cells, (1, 3))).resize((w * 3, h), Image.Resampling.BICUBIC).crop((w, 0, w * 2, h))
    else:
        grime = Image.fromarray(cells).resize((w, h), Image.Resampling.BICUBIC)
    grime = 0.82 + 0.18 * np.asarray(grime, np.float32)[..., None] / 255.0
    rgb = px[..., :3] * light[..., None] * grime
    # The shadows go cold: a teal cast where it is dark.
    dark = np.clip(1.0 - rgb.mean(axis=2, keepdims=True) / 110.0, 0, 1)
    rgb = rgb + dark * np.array([0.0, 14.0, 16.0], np.float32)
    px[..., :3] = np.clip(rgb, 0, 255)
    c.img = Image.fromarray(px.astype(np.uint8), "RGBA")
    c.d = blending_draw(c.img)


def _fog(c: _Canvas, y: float, t: float, strength: float = 0.5, wrap_x: bool = False) -> None:
    """Teal FOG pooling along a floor at ``y``: drifting, soft lobes.

    ``wrap_x``: the lobes repeat with the width (a multiple of 24), so a prop
    laid end to end has one bank of fog."""
    W = c.size[0]
    n = max(1, round(W / 24))

    def lobes(d):
        for k in range(-2 if wrap_x else 0, n + 2):
            phase = k % n if wrap_x else k
            x = k * 24.0 + 10.0 * math.sin(t * math.tau + phase * 1.3)
            r = 14.0 + 5.0 * math.sin(phase * 2.1 + t * math.tau)
            d.ellipse(c.p(x - r * 1.6, y - r * 0.55, x + r * 1.6, y + r * 0.35), fill=_a(TEAL, 0.22 * strength))

    c.glow(lobes, 4.0)


def _motes(c: _Canvas, t: float, n: int = 10, seed: int = 1, rise: float = 30.0) -> None:
    """Spectral MOTES drifting up, each twinkling on its own clock.

    Each mote rises ``rise`` px over one loop of the row, from its own phase,
    and fades in at the foot of its path and out at the top. So the row loops
    with no jump: a mote that goes back to the foot is not drawn there."""
    rng = np.random.default_rng(seed)
    W, H = c.size
    rise = min(rise, H * 0.6)
    # (x, the foot of its path, its phase): the whole path is on the canvas.
    pts = [(rng.random() * W, rise + rng.random() * (H - rise), rng.random()) for _ in range(n)]

    def dots(d):
        for x, foot, ph in pts:
            life = (t + ph) % 1.0
            yy = foot - life * rise
            a = math.sin(life * math.pi) * (0.3 + 0.7 * abs(math.sin((t + ph) * math.tau * 2.0)))
            d.ellipse(c.p(x - 1.4, yy - 1.4, x + 1.4, yy + 1.4), fill=_a(TEAL_CORE, a))

    c.glow(dots, 0.8)
    dots(c.d)


def _drips(c: _Canvas, xs, y: float, t: float, length: float = 14.0) -> None:
    """ECTOPLASM DRIPS hanging from an edge at ``y``, glowing, each a run and
    a bead."""
    for k, x in enumerate(xs):
        L = length * (0.6 + 0.4 * math.sin(k * 1.9 + t * math.tau))
        c.glow(lambda d, x=x, L=L: d.line(c.p(x, y, x, y + L), fill=_a(TEAL, 0.8), width=int(2.4 * SUPER)), 1.0)
        c.line([(x, y), (x, y + L)], _a(TEAL_CORE, 0.9), w=1.0)
        c.ellipse(x - 1.8, y + L - 1.0, x + 1.8, y + L + 2.6, fill=TEAL_CORE, outline=None)


def _glow_crack(c: _Canvas, pts, strength: float = 1.0) -> None:
    """A CRACK with teal light welling out of it."""
    c.glow(lambda d: d.line([(x * SUPER, y * SUPER) for x, y in pts], fill=_a(TEAL, 0.9 * strength), width=int(3 * SUPER), joint="curve"), 1.6)
    c.line(pts, _a(TEAL_CORE, strength), w=0.8)


def _ghost_hand(c: _Canvas, x: float, y: float, h: float, lean: float, alpha: float) -> None:
    """A translucent GHOST HAND reaching up out of the dark, fingers spread."""
    def hand(d):
        arm = [(x - h * 0.12, y), (x + lean - h * 0.1, y - h * 0.6), (x + lean + h * 0.1, y - h * 0.6), (x + h * 0.12, y)]
        d.polygon([(px * SUPER, py * SUPER) for px, py in arm], fill=_a(TEAL, 0.55 * alpha))
        palm = (x + lean, y - h * 0.68)
        d.ellipse(c.p(palm[0] - h * 0.13, palm[1] - h * 0.1, palm[0] + h * 0.13, palm[1] + h * 0.12), fill=_a(TEAL, 0.6 * alpha))
        for k, ang in enumerate((-50, -20, 0, 20, 45)):
            a = math.radians(ang - 90 + lean)
            L = h * (0.28 if k in (1, 2, 3) else 0.2)
            d.line(c.p(palm[0], palm[1], palm[0] + math.cos(a) * L, palm[1] + math.sin(a) * L), fill=_a(TEAL_CORE, 0.6 * alpha), width=int(1.6 * SUPER))

    c.glow(hand, 1.2)
    hand(c.d)


def _eyes_in_dark(c: _Canvas, x: float, y: float, t: float, size: float = 2.0) -> None:
    """A pair of EYES watching from the dark, blinking now and then."""
    open_ = 0.15 if (t * 8.0) % 8.0 < 0.6 else 1.0
    for dx in (-size * 1.8, size * 1.8):
        c.glow(lambda d, dx=dx: d.ellipse(c.p(x + dx - size, y - size * open_, x + dx + size, y + size * open_), fill=TEAL_CORE), 1.0)


def _ghost_flame(c: _Canvas, x: float, y: float, h: float, t: float) -> None:
    """A teal GHOST FLAME standing on (x, y), flickering with ``t``."""
    sway = math.sin(t * math.tau) * h * 0.12
    pts = [(x - h * 0.28, y), (x - h * 0.2, y - h * 0.5), (x + sway, y - h), (x + h * 0.22, y - h * 0.45), (x + h * 0.28, y)]
    c.glow(lambda d: d.polygon([(px * SUPER, py * SUPER) for px, py in pts], fill=_a(TEAL, 0.9)), h * 0.18)
    core = [(x - h * 0.12, y), (x + sway * 0.5, y - h * 0.6), (x + h * 0.12, y)]
    c.poly(core, TEAL_CORE, outline=None)


# --- the spectral gap -------------------------------------------------------------


def spectral_gap(t: float) -> Image.Image:
    """The SPECTRAL GAP: a hole in the floor, its two eigenvalue bands with
    the dark gap between them, and the level GIMBAL that steadies the room."""
    W, H = 256, 144
    c = _Canvas((W, H))
    floor = 64.0  # the floor line the hole is cut in
    # The floor's lip on either side, cracked marble.
    c.rect(0, floor, 40, H, MARBLE_B)
    c.rect(W - 40, floor, W, H, MARBLE_B)
    for x0 in (0, W - 40):
        for k in range(0, 40, 10):
            c.rect(x0 + k, floor, x0 + k + 10, floor + 6, MARBLE_A if (k // 10) % 2 == 0 else MARBLE_B, w=0.8)
    _shade_and_grime(c, seed=3)
    # The hole: a void with a ragged rim, stars of the far side deep in it.
    rim = [(40, floor)] + [(40 + k * 11.0, floor + 3.0 * math.sin(k * 1.7)) for k in range(1, 16)] + [(W - 40, floor), (W - 40, H), (40, H)]
    c.poly(rim, VOID)
    rng = np.random.default_rng(7)
    for _ in range(30):
        x, y = 46 + rng.random() * (W - 92), floor + 30 + rng.random() * (H - floor - 30)
        c.ellipse(x - 0.6, y - 0.6, x + 0.6, y + 0.6, fill=_a(TEAL_CORE, 0.3 + 0.5 * rng.random()), outline=None)
    # Light wells up the rim and out through cracks in the floor.
    c.glow(lambda d: d.line([(px * SUPER, py * SUPER) for px, py in rim[:17]], fill=_a(TEAL, 0.9), width=int(4 * SUPER)), 2.5)
    for pts in (((40, floor + 2), (30, floor + 10), (22, floor + 8), (12, floor + 22)),
                ((W - 40, floor + 2), (W - 28, floor + 12), (W - 20, floor + 9), (W - 6, floor + 26)),
                ((40, floor + 30), (28, floor + 44), (34, floor + 60))):
        _glow_crack(c, pts, 0.7 + 0.3 * math.sin(t * math.tau))
    # Ghost hands reaching up out of the gap, swaying.
    for k, (hx, hh) in enumerate(((80, 46), (124, 38), (176, 52))):
        _ghost_hand(c, hx, H - 4, hh, 8.0 * math.sin(t * math.tau + k * 2.0), 0.55 + 0.25 * math.sin(t * math.tau + k))
    # The eigenvalue bands: lambda-1 near the lip, lambda-2 deep, both
    # breathing; between them, the dark gap (the stabilizing distance).
    breathe = 0.5 + 0.5 * math.sin(t * math.tau)
    for y, strength in ((floor + 22.0, 1.0), (floor + 64.0, 0.75)):
        c.glow(lambda d, y=y, s=strength: d.rectangle(c.p(46, y - 3, W - 46, y + 3), fill=_a(TEAL, (0.6 + 0.3 * breathe) * s)), 3.0)
        c.line([(46, y), (W - 46, y)], _a(TEAL_CORE, 0.9 * strength), w=1.0)
    # The gap between them: spectral ticks measuring it.
    gx = W / 2
    c.line([(gx, floor + 26), (gx, floor + 60)], _a(TEAL_CORE, 0.8), w=0.8)
    for y in (floor + 26, floor + 60):
        c.line([(gx - 5, y), (gx + 5, y)], _a(TEAL_CORE, 0.8), w=0.8)
    # The gimbal: ghostly rings hanging level over the hole, their light
    # running round them (the rings never tilt: that is the point).
    cx, cy = gx, floor - 30.0
    for rx, ry, a in ((46.0, 12.0, 0.55), (30.0, 22.0, 0.45), (16.0, 16.0, 0.7)):
        c.glow(lambda d, rx=rx, ry=ry, a=a: d.ellipse(c.p(cx - rx, cy - ry, cx + rx, cy + ry), outline=_a(TEAL, a), width=int(2.0 * SUPER)), 1.2)
        c.ellipse(cx - rx, cy - ry, cx + rx, cy + ry, outline=_a(TEAL_CORE, a), w=0.6)
    # The level bubble at its heart, dead centre.
    c.ellipse(cx - 3, cy - 3, cx + 3, cy + 3, fill=TEAL_CORE, outline=None)
    spark = (cx + math.cos(t * math.tau) * 46.0, cy + math.sin(t * math.tau) * 12.0)
    c.glow(lambda d: d.ellipse(c.p(spark[0] - 3, spark[1] - 3, spark[0] + 3, spark[1] + 3), fill=TEAL_CORE), 1.5)
    # A plumb line of light from the gimbal to the deep band.
    c.line([(cx, cy + 16), (cx, floor + 20)], _a(TEAL, 0.5), w=0.6)
    # Mist streaming up out of the gap, and motes.
    def mist(d):
        for k in range(6):
            x = 60 + k * 28 + 6 * math.sin(t * math.tau + k)
            pts = [(x + 5 * math.sin(j * 0.9 + t * math.tau + k), floor + 20 - j * 7) for j in range(8)]
            d.line([(px * SUPER, py * SUPER) for px, py in pts], fill=_a(TEAL, 0.35), width=int(6 * SUPER), joint="curve")
    c.glow(mist, 3.0)
    _motes(c, t, 16, seed=11)
    return c.done()


# --- the wall, the door and the lights --------------------------------------------


def wallpaper_panel(t: float) -> Image.Image:
    """A WALL SECTION: plum damask of ellipses and their axes, a wainscot of
    dark wood below, a strip of paper peeling.

    It tiles side by side: the damask and the wainscot repeat each quarter of
    the width, the rail runs off both edges, and the grime and the fog wrap
    round, so a wall of panels shows no seam. A room lays panels a whole or a
    quarter panel apart (the haunted wing's generator), so nothing drawn
    crosses a quarter line: the damask, the wainscot's panels, the scratches,
    the peel and the stain each stand between two."""
    W, H = 192, 256
    c = _Canvas((W, H))
    c.rect(0, 0, W, H, PLUM, outline=None)
    for row in range(6):
        for col in range(W // 48):
            x = col * 48 + (36 if row % 2 else 12)
            y = 16 + row * 30
            c.ellipse(x - 9, y - 6, x + 9, y + 6, outline=PLUM_LIGHT, w=0.8)
            c.line([(x - 9, y), (x + 9, y)], PLUM_LIGHT, w=0.5)
            c.line([(x, y - 6), (x, y + 6)], PLUM_DARK, w=0.5)
    # The wainscot and its rail.
    c.rect(0, 188, W, H, WOOD, outline=None)
    c.rect(-4, 184, W + 4, 190, WOOD_LIGHT)
    for x in range(6, W, 48):
        c.rect(x, 198, x + 36, H - 10, WOOD, outline=WOOD_LIGHT, w=0.8)
    # The peeling strip: a curl of paper off the seam, its back pale.
    c.poly([(120, 40), (136, 44), (140, 92), (128, 86)], (196, 176, 190, 255))
    c.poly([(120, 40), (128, 86), (122, 96)], PLUM_DARK)
    _shade_and_grime(c, top=0.45, bottom=0.6, seed=5, wrap_x=True)
    # Claw scratches torn down the paper, teal in them.
    for k in range(4):
        _glow_crack(c, [(56 + k * 7, 70 + k * 3), (62 + k * 7, 110 + k * 2), (60 + k * 7, 150)], 0.6)
    # A water stain shaped like a face, watching.
    c.ellipse(150, 120, 186, 166, fill=(52, 30, 58, 150), outline=None)
    _eyes_in_dark(c, 168, 136, t, 2.2)
    # Ectoplasm running down from the cornice; fog at the skirting.
    _drips(c, (14, 70, 104, 168), 0, t, 18.0)
    _fog(c, H - 4, t, 0.8, wrap_x=True)
    return c.done()


def room_door(t: float) -> Image.Image:
    """A GUEST ROOM DOOR: dark panelled wood in a frame, a brass infinity on
    its plate (there is always one more room), teal light under it."""
    W, H = 96, 168
    c = _Canvas((W, H))
    c.rect(4, 8, W - 4, H, WOOD_LIGHT)
    c.rect(12, 16, W - 12, H, WOOD)
    for y0, y1 in ((26, 80), (90, 150)):
        c.rect(20, y0, W - 20, y1, WOOD, outline=WOOD_LIGHT, w=1.0)
    c.ellipse(W - 26, 96, W - 20, 102, fill=BRASS)
    # The plate and its infinity.
    c.rect(34, 30, W - 34, 44, BRASS, w=0.8)
    for sx in (-1, 1):
        c.ellipse(W / 2 + sx * 6 - 5, 33, W / 2 + sx * 6 + 5, 41, outline=BRASS_DARK, w=1.0)
    flicker = 0.65 + 0.35 * abs(math.sin(t * math.tau * 2.3))
    _shade_and_grime(c, top=0.6, bottom=0.7, seed=9)
    # Light from the other side: under the door, round its edge, through
    # the keyhole; eyes looking out from the crack.
    c.glow(lambda d: d.rectangle(c.p(14, H - 6, W - 14, H), fill=_a(TEAL, flicker)), 3.0)
    c.glow(lambda d: d.line(c.p(W - 12, 18, W - 12, H), fill=_a(TEAL, 0.7 * flicker), width=int(2 * SUPER)), 2.0)
    c.glow(lambda d: d.ellipse(c.p(W - 26, 104, W - 21, 110), fill=_a(TEAL_CORE, flicker)), 1.2)
    _eyes_in_dark(c, W / 2, H - 10, t, 1.6)
    # A ghostly handprint smeared on its upper panel.
    _ghost_hand(c, W / 2 - 4, 76, 30, -4.0, 0.5)
    _fog(c, H - 2, t, 0.9)
    return c.done()


def lift_gate(t: float) -> Image.Image:
    """The SERVICE LIFT'S GATE, drawn shut: a brass scissor gate across the
    lift's doorway, a chain and padlock through it and an OUT OF ORDER tag on
    the chain. The doorway behind shows dark through the lattice. It stands
    where the lift is locked; the breaker takes it away."""
    W, H = 96, 168
    c = _Canvas((W, H))
    # The frame of the gate: a brass track over it and a post each side.
    c.rect(2, 4, W - 2, 14, BRASS_DARK)
    c.rect(2, H - 8, W - 2, H, BRASS_DARK)
    for x0 in (2, W - 12):
        c.rect(x0, 4, x0 + 10, H, BRASS)
    # The lattice: crossed bars between the posts, hinged where they cross.
    cols, rows = 4, 7
    x0, x1, y0, y1 = 12.0, W - 12.0, 14.0, H - 8.0
    dx, dy = (x1 - x0) / cols, (y1 - y0) / rows
    for i in range(cols + 1):
        x = x0 + i * dx
        c.line([(x, y0), (x, y1)], BRASS, w=2.4)
    for j in range(rows):
        for i in range(cols):
            xa, ya = x0 + i * dx, y0 + j * dy
            c.line([(xa, ya), (xa + dx, ya + dy)], BRASS_DARK, w=1.6)
            c.line([(xa + dx, ya), (xa, ya + dy)], BRASS_DARK, w=1.6)
            c.ellipse(xa + dx / 2 - 1.6, ya + dy / 2 - 1.6, xa + dx / 2 + 1.6, ya + dy / 2 + 1.6, fill=BRASS, outline=None)
    # The chain round the middle bars, and its padlock.
    cy = H * 0.52
    for k in range(9):
        x = W / 2 - 22 + k * 5.5
        y = cy + 2.0 * math.sin(k * 0.9)
        c.ellipse(x - 3, y - 2, x + 3, y + 2, outline=(150, 150, 160, 255), w=1.0)
    c.rect(W / 2 - 7, cy + 2, W / 2 + 7, cy + 16, BRASS)
    c.ellipse(W / 2 - 5, cy - 6, W / 2 + 5, cy + 6, outline=BRASS_DARK, w=1.6)
    c.ellipse(W / 2 - 1.5, cy + 7, W / 2 + 1.5, cy + 10, fill=OUTLINE, outline=None)
    # The tag on the chain, swinging a little.
    sway = 2.0 * math.sin(t * math.tau)
    tag = [(W / 2 + 14 + sway, cy + 4), (W / 2 + 34 + sway, cy + 4), (W / 2 + 32 + sway, cy + 22), (W / 2 + 12 + sway, cy + 22)]
    c.line([(W / 2 + 14, cy + 1), (W / 2 + 22 + sway, cy + 4)], (150, 150, 160, 255), w=0.8)
    c.poly(tag, (226, 214, 180, 255))
    for k, y in enumerate((cy + 9, cy + 13, cy + 17)):
        c.line([(W / 2 + 16 + sway, y), (W / 2 + 29 + sway - (k == 2) * 4, y)], (150, 40, 40, 255), w=0.8)
    _shade_and_grime(c, top=0.65, bottom=0.75, seed=21)
    # Teal light leaks round the lock: the lift is dead, not empty.
    flicker = 0.55 + 0.45 * abs(math.sin(t * math.tau * 2.0))
    c.glow(lambda d: d.ellipse(c.p(W / 2 - 4, cy + 6, W / 2 + 4, cy + 12), fill=_a(TEAL, flicker)), 1.5)
    return c.done()


def treasury_seal(t: float) -> Image.Image:
    """The TREASURY SEAL: the vault's iron grille, barred and riveted, with a
    ghostly ring of light locked across it, an infinity (the hotel's mark) in
    its middle. It stands in the treasury's doorway while the Gram Reaper
    stands; the reaper's fall takes it away."""
    W, H = 96, 168
    c = _Canvas((W, H))
    IRON = (54, 50, 62, 255)
    IRON_LIGHT = (96, 92, 108, 255)
    c.rect(0, 0, W, H, (16, 10, 24, 255), outline=None)
    for x in range(8, W, 16):
        c.rect(x - 3, 0, x + 3, H, IRON, outline=OUTLINE, w=0.8)
        c.line([(x - 1, 2), (x - 1, H - 2)], IRON_LIGHT, w=0.6)
    for y in (10, H / 2, H - 12):
        c.rect(0, y - 4, W, y + 4, IRON, outline=OUTLINE, w=0.8)
        for x in range(8, W, 16):
            c.ellipse(x - 1.6, y - 1.6, x + 1.6, y + 1.6, fill=IRON_LIGHT, outline=None)
    _shade_and_grime(c, top=0.6, bottom=0.7, seed=23)
    # The seal: a ring of light with its runes turning, and the infinity.
    cx, cy = W / 2, H / 2
    pulse = 0.65 + 0.35 * math.sin(t * math.tau)
    c.glow(lambda d: d.ellipse(c.p(cx - 30, cy - 30, cx + 30, cy + 30), outline=_a(TEAL, pulse), width=int(4 * SUPER)), 2.5)
    c.ellipse(cx - 30, cy - 30, cx + 30, cy + 30, outline=_a(TEAL_CORE, 0.9), w=1.0)
    for k in range(8):
        a = (k / 8.0 + t / 8.0) * math.tau
        x, y = cx + math.cos(a) * 24, cy + math.sin(a) * 24
        c.ellipse(x - 1.8, y - 1.8, x + 1.8, y + 1.8, fill=_a(TEAL_CORE, 0.6 + 0.4 * pulse), outline=None)
    for sx in (-1, 1):
        c.glow(lambda d, sx=sx: d.ellipse(c.p(cx + sx * 7 - 7, cy - 5, cx + sx * 7 + 7, cy + 5), outline=_a(TEAL, pulse), width=int(2 * SUPER)), 1.2)
        c.ellipse(cx + sx * 7 - 7, cy - 5, cx + sx * 7 + 7, cy + 5, outline=TEAL_CORE, w=0.8)
    _motes(c, t, 8, seed=24)
    return c.done()


def wall_sconce(t: float) -> Image.Image:
    """A WALL SCONCE: a brass back plate, an arm, a cup, a ghost flame."""
    W, H = 48, 72
    c = _Canvas((W, H))
    c.ellipse(18, 30, 30, 60, fill=BRASS)
    c.line([(24, 50), (24, 44), (34, 40)], BRASS_DARK, w=2.2)
    c.rect(28, 36, 40, 40, BRASS)
    _shade_and_grime(c, seed=2)
    c.glow(lambda d: d.ellipse(c.p(16, 14, 44, 42), fill=_a(TEAL, 0.25)), 3.0)
    _ghost_flame(c, 34, 36, 22, t)
    _motes(c, t, 4, seed=4)
    return c.done()


def chandelier(t: float) -> Image.Image:
    """A CHANDELIER hanging from its top edge: a brass ring of arms with ghost
    flames, crystals, and cobwebs strung between the arms."""
    W, H = 160, 128
    c = _Canvas((W, H))
    c.line([(W / 2, 0), (W / 2, 40)], BRASS_DARK, w=1.6)
    c.ellipse(W / 2 - 52, 66, W / 2 + 52, 82, outline=BRASS, w=2.4)
    c.ellipse(W / 2 - 8, 40, W / 2 + 8, 70, fill=BRASS)
    for k in range(5):
        x = W / 2 - 48 + k * 24
        c.line([(W / 2, 62), (x, 74)], BRASS_DARK, w=1.2)
        c.rect(x - 3, 64, x + 3, 74, BRASS, w=0.6)
        _ghost_flame(c, x, 64, 16, t + k * 0.2)
        c.poly([(x - 2, 82), (x + 2, 82), (x, 92)], _a(TEAL_CORE, 0.7), outline=None)
    for k in range(4):
        x0, x1 = W / 2 - 48 + k * 24, W / 2 - 24 + k * 24
        c.line([(x0, 76), ((x0 + x1) / 2, 88), (x1, 76)], WEB, w=0.5)
        c.line([(x0, 76), ((x0 + x1) / 2, 82), (x1, 76)], WEB, w=0.3)
    _shade_and_grime(c, seed=6)
    c.glow(lambda d: d.ellipse(c.p(W / 2 - 70, 40, W / 2 + 70, 100), fill=_a(TEAL, 0.18)), 8.0)
    # Long cobweb streamers hanging off it, swaying.
    for k, x in enumerate((W / 2 - 50, W / 2 + 48)):
        sway = 3 * math.sin(t * math.tau + k)
        c.line([(x, 76), (x + sway, 100), (x - sway, 120)], WEB, w=0.6)
    _drips(c, (W / 2 - 24, W / 2 + 24), 82, t, 10.0)
    _motes(c, t, 8, seed=8)
    return c.done()


def luggage_cart(t: float) -> Image.Image:
    """The bellhop's LUGGAGE CART: a brass frame on wheels, its arch over a
    pile of old cases, one strapped open and leaking teal light."""
    W, H = 128, 120
    c = _Canvas((W, H))
    c.line([(16, 100), (16, 20), (W - 16, 20), (W - 16, 100)], BRASS, w=2.6)
    c.rect(10, 96, W - 10, 104, BRASS_DARK)
    for x in (22, W - 22):
        c.ellipse(x - 8, 104, x + 8, H, fill=OUTLINE, outline=BRASS_DARK, w=1.2)
    c.rect(22, 70, 74, 96, LEATHER)
    c.rect(78, 60, 108, 96, (86, 44, 92, 255))
    c.rect(28, 46, 66, 70, (150, 110, 70, 255))
    c.glow(lambda d: d.rectangle(c.p(30, 66, 64, 70), fill=_a(TEAL, 0.8)), 2.0)
    for x0, x1, y in ((22, 74, 82), (78, 108, 76)):
        c.line([(x0, y), (x1, y)], BRASS_DARK, w=1.0)
    _shade_and_grime(c, seed=12)
    # Something in the open case watches; a ghost hand hangs out of it.
    _eyes_in_dark(c, 47, 64, t, 1.6)
    _ghost_hand(c, 70, 70, 26, 14.0, 0.5)
    c.line([(16, 20), (8, 34), (16, 48)], WEB, w=0.5)
    _fog(c, H - 6, t, 0.8)
    return c.done()


def floor_strip(t: float) -> Image.Image:
    """A strip of CHECKER MARBLE FLOOR, cracked, that tiles end to end."""
    W, H = 128, 32
    c = _Canvas((W, H))
    for k in range(8):
        for r in range(2):
            c.rect(k * 16, r * 16, k * 16 + 16, r * 16 + 16, MARBLE_A if (k + r) % 2 == 0 else MARBLE_B, w=0.6)
    _shade_and_grime(c, top=0.85, bottom=0.6, seed=14, wrap_x=True)
    _glow_crack(c, [(30, 2), (38, 12), (34, 22), (44, 30)], 0.8)
    _glow_crack(c, [(90, 0), (86, 10), (96, 18)], 0.6)
    return c.done()


#: Each prop: (its drawing, its canvas, its idle frames and frame time).
PROPS: Dict[str, Tuple[Callable[[float], Image.Image], Tuple[int, int], int, int]] = {
    "hylbert_spectral_gap": (spectral_gap, (256, 144), 8, 120),
    "hylbert_wallpaper_panel": (wallpaper_panel, (192, 256), 6, 160),
    "hylbert_room_door": (room_door, (96, 168), 4, 140),
    "hylbert_lift_gate": (lift_gate, (96, 168), 4, 160),
    "hylbert_treasury_seal": (treasury_seal, (96, 168), 8, 120),
    "hylbert_wall_sconce": (wall_sconce, (48, 72), 6, 110),
    "hylbert_chandelier": (chandelier, (160, 128), 6, 120),
    "hylbert_luggage_cart": (luggage_cart, (128, 120), 6, 150),
    "hylbert_floor_strip": (floor_strip, (128, 32), 1, 1000),
}


def _make_render(name: str):
    draw_fn, size, frames, ms = PROPS[name]
    meta = {
        "actor": {"character_id": name, "display_name": name.replace("_", " ").title()},
        "body": {"body_plan": "Prop", "body_kind": "Object", "mass_class": "Heavy", "traits": ["scenery", "hylberts_hotel"], "locomotion_hint": "None"},
        "visual": {"default_pose": "idle", "portrait": {"animation": "idle", "frame": 0}},
        "tags": ["prop", "scenery", "math", "hylberts_hotel"],
        "animation_bindings": {"default": {"animation": "idle", "events": []}},
    }

    def render(out_dir: str | Path, **opts) -> List[Path]:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        outputs = build_sheet(
            target=name,
            rows=[("idle", frames, ms)],
            render_fn=lambda _anim, i, n: draw_fn(i / max(1, n)),
            out_dir=out_dir,
            frame_size=size,
            auto_crop=False,
            actor_metadata=meta,
            animation_key_map={"idle": "idle"},
        )
        return [outputs[k] for k in ("spritesheet", "yaml", "ron", "actor", "preview", "canonical", "canonical_transparent")]

    return render, meta


TARGETS = {name: dict(zip(("render", "actor_metadata"), _make_render(name))) for name in PROPS}
