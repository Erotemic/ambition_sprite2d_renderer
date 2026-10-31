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
  ellipses and their axes over a wainscot, the paper peeling.
- ``hylbert_room_door``: a guest room door, its brass plate an infinity
  (there is always one more room), teal light under it; ``idle`` 4 (the light
  flickers).
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
    # The hole: a void with a ragged rim.
    rim = [(40, floor)] + [(40 + k * 11.0, floor + 3.0 * math.sin(k * 1.7)) for k in range(1, 16)] + [(W - 40, floor), (W - 40, H), (40, H)]
    c.poly(rim, VOID)
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
    return c.done()


# --- the wall, the door and the lights --------------------------------------------


def wallpaper_panel(t: float) -> Image.Image:
    """A WALL SECTION: plum damask of ellipses and their axes, a wainscot of
    dark wood below, a strip of paper peeling at the seam."""
    W, H = 192, 256
    c = _Canvas((W, H))
    c.rect(0, 0, W, H, PLUM, outline=None)
    for row in range(6):
        for col in range(5):
            x = col * 40 + (20 if row % 2 else 0)
            y = 16 + row * 30
            c.ellipse(x - 9, y - 6, x + 9, y + 6, outline=PLUM_LIGHT, w=0.8)
            c.line([(x - 9, y), (x + 9, y)], PLUM_LIGHT, w=0.5)
            c.line([(x, y - 6), (x, y + 6)], PLUM_DARK, w=0.5)
    # The wainscot and its rail.
    c.rect(0, 188, W, H, WOOD, outline=None)
    c.rect(0, 184, W, 190, WOOD_LIGHT)
    for x in range(8, W, 46):
        c.rect(x, 198, x + 36, H - 10, WOOD, outline=WOOD_LIGHT, w=0.8)
    # The peeling strip: a curl of paper off the seam, its back pale.
    c.poly([(120, 40), (136, 44), (140, 92), (128, 86)], (196, 176, 190, 255))
    c.poly([(120, 40), (128, 86), (122, 96)], PLUM_DARK)
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
    c.glow(lambda d: d.rectangle(c.p(14, H - 6, W - 14, H), fill=_a(TEAL, flicker)), 3.0)
    return c.done()


def wall_sconce(t: float) -> Image.Image:
    """A WALL SCONCE: a brass back plate, an arm, a cup, a ghost flame."""
    W, H = 48, 72
    c = _Canvas((W, H))
    c.ellipse(18, 30, 30, 60, fill=BRASS)
    c.line([(24, 50), (24, 44), (34, 40)], BRASS_DARK, w=2.2)
    c.rect(28, 36, 40, 40, BRASS)
    _ghost_flame(c, 34, 36, 22, t)
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
    return c.done()


def floor_strip(t: float) -> Image.Image:
    """A strip of CHECKER MARBLE FLOOR, cracked, that tiles end to end."""
    W, H = 128, 32
    c = _Canvas((W, H))
    for k in range(8):
        for r in range(2):
            c.rect(k * 16, r * 16, k * 16 + 16, r * 16 + 16, MARBLE_A if (k + r) % 2 == 0 else MARBLE_B, w=0.6)
    c.line([(30, 2), (38, 12), (34, 22), (44, 30)], OUTLINE, w=0.6)
    c.line([(90, 0), (86, 10), (96, 18)], OUTLINE, w=0.6)
    return c.done()


#: Each prop: (its drawing, its canvas, its idle frames and frame time).
PROPS: Dict[str, Tuple[Callable[[float], Image.Image], Tuple[int, int], int, int]] = {
    "hylbert_spectral_gap": (spectral_gap, (256, 144), 8, 120),
    "hylbert_wallpaper_panel": (wallpaper_panel, (192, 256), 1, 1000),
    "hylbert_room_door": (room_door, (96, 168), 4, 140),
    "hylbert_wall_sconce": (wall_sconce, (48, 72), 6, 110),
    "hylbert_chandelier": (chandelier, (160, 128), 6, 120),
    "hylbert_luggage_cart": (luggage_cart, (128, 120), 1, 1000),
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
