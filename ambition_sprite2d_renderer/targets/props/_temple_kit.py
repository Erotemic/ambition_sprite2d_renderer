"""The keys and the doors of the Noodly Temple (the level of the Flying
Spaghetti Monster).

A level of locks: each door has a colour, and its key has the same colour.
The colours are sauces: marinara (red), pesto (green), parmesan (gold). The
last door is a colander (steel with holes), and so is its key.

Three kinds of sheet are made here, each by a thin target module:

- a key (``build_key``): a `PickupSpawn` draws its ``idle`` row, a slow bob
  with a glint that goes across the bow. The bow of each key is the thing
  its sauce is made of.
- a door (``build_door``): a `LockWall` draws its one frame over its box
  (32 by 128 world units, drawn at 3 to 1). It is seen from the side: a slab
  that shuts a passage, with a lock plate in its middle.
- the iron grille (``build_grille``): a column that tiles
  (``column_tile``), so one sheet shuts an opening of any height.

No frame has a shadow under the thing in it.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image

from ...authoring.sheet_build import build_sheet
from . import _held_prop_common as hp
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]

SHEET_FILES_SUFFIXES = ("_spritesheet.png", "_spritesheet.yaml", "_spritesheet.ron", "_actor.ron")

#: Each sauce: its colour, its light, its dark.
SAUCES = {
    "marinara": ((198, 50, 42, 255), (240, 112, 84, 255), (116, 22, 26, 255)),
    "pesto": ((70, 150, 66, 255), (140, 204, 98, 255), (32, 88, 44, 255)),
    "parmesan": ((226, 178, 62, 255), (255, 228, 136, 255), (146, 100, 26, 255)),
    "colander": ((150, 160, 178, 255), (220, 228, 240, 255), (82, 90, 108, 255)),
}

STONE = (74, 64, 78, 255)
STONE_HI = (112, 100, 116, 255)
STONE_DARK = (44, 36, 48, 255)
CREAM = (246, 232, 196, 255)
CREAM_DARK = (204, 180, 132, 255)
HOLE = (20, 16, 24, 255)
WOOD = (104, 72, 46, 255)
WOOD_HI = (142, 104, 68, 255)
WOOD_DARK = (62, 42, 28, 255)
WET = (48, 84, 86, 255)
BRONZE = (160, 108, 60, 255)
BRONZE_HI = (214, 164, 100, 255)
BRONZE_DARK = (96, 60, 34, 255)

#: A door frame: 3 to 1 of a `LockWall` of 32 by 128.
DOOR_FRAME = (96, 384)
#: A key frame: the key is about 34 world units across.
KEY_FRAME = (96, 96)
KEY_ROWS: List[Tuple[str, int, int]] = [("idle", 8, 110)]
DOOR_ROWS: List[Tuple[str, int, int]] = [("idle", 1, 1000)]

p = hp.px


def _w(v: float) -> int:
    return max(1, int(round(p(v))))


def _poly(d, pts: Sequence[Tuple[float, float]], fill, outline=None, width: float = 1.4) -> None:
    d.polygon([(p(x), p(y)) for x, y in pts], fill=fill)
    if outline is not None:
        d.line([(p(x), p(y)) for x, y in list(pts) + [pts[0]]], fill=outline, width=_w(width), joint="curve")


def _disc(d, cx: float, cy: float, r: float, fill, outline=None, width: float = 1.4) -> None:
    d.ellipse((p(cx - r), p(cy - r), p(cx + r), p(cy + r)), fill=fill, outline=outline, width=_w(width))


def _rect(d, x0: float, y0: float, x1: float, y1: float, fill, outline=None, width: float = 1.4, radius: float = 0.0) -> None:
    box = (p(x0), p(y0), p(x1), p(y1))
    if radius > 0.0:
        d.rounded_rectangle(box, radius=_w(radius), fill=fill, outline=outline, width=_w(width))
    else:
        d.rectangle(box, fill=fill, outline=outline, width=_w(width))


def _line(d, pts: Sequence[Tuple[float, float]], fill, width: float) -> None:
    d.line([(p(x), p(y)) for x, y in pts], fill=fill, width=_w(width), joint="curve")


def _turn(pts: Sequence[Tuple[float, float]], about: Tuple[float, float], degrees: float) -> List[Tuple[float, float]]:
    a = math.radians(degrees)
    ca, sa = math.cos(a), math.sin(a)
    return [(about[0] + (x - about[0]) * ca - (y - about[1]) * sa, about[1] + (x - about[0]) * sa + (y - about[1]) * ca)
            for x, y in pts]


def _keyhole(d, cx: float, cy: float, s: float) -> None:
    _disc(d, cx, cy - 0.3 * s, 0.42 * s, HOLE)
    _poly(d, [(cx - 0.2 * s, cy - 0.1 * s), (cx + 0.2 * s, cy - 0.1 * s), (cx + 0.36 * s, cy + 0.9 * s), (cx - 0.36 * s, cy + 0.9 * s)], HOLE)


# ---------------------------------------------------------------------------
# The emblem of each sauce, in a box of `s` round `cx`, `cy`.
# ---------------------------------------------------------------------------

def _emblem(d, sauce: str, cx: float, cy: float, s: float, ink: RGBA, ink_dark: RGBA, leaf: RGBA) -> None:
    if sauce == "marinara":
        # A tomato: a round fruit with a star of leaves on it.
        _disc(d, cx, cy + 0.06 * s, 0.44 * s, ink, hp.OUTLINE, 1.2)
        _disc(d, cx - 0.16 * s, cy - 0.1 * s, 0.1 * s, ink_dark)
        for k in range(5):
            a = -math.pi / 2 + k * math.tau / 5
            tip = (cx + math.cos(a) * 0.3 * s, cy - 0.3 * s + math.sin(a) * 0.2 * s)
            _poly(d, [(cx - 0.06 * s, cy - 0.3 * s), (cx + 0.06 * s, cy - 0.3 * s), tip], leaf)
        _line(d, [(cx, cy - 0.32 * s), (cx + 0.04 * s, cy - 0.52 * s)], leaf, 0.07 * s)
    elif sauce == "pesto":
        # A leaf of basil: a pointed leaf with a rib.
        pts = []
        for k in range(24):
            t = k / 23.0
            pts.append((cx + (t - 0.5) * 0.96 * s, cy - math.sin(math.pi * t) * 0.34 * s))
        for k in range(24):
            t = 1.0 - k / 23.0
            pts.append((cx + (t - 0.5) * 0.96 * s, cy + math.sin(math.pi * t) * 0.34 * s))
        pts = _turn(pts, (cx, cy), -32.0)
        _poly(d, pts, ink, hp.OUTLINE, 1.2)
        rib = _turn([(cx - 0.46 * s, cy), (cx + 0.46 * s, cy)], (cx, cy), -32.0)
        _line(d, rib, ink_dark, 0.05 * s)
        for t in (-0.22, 0.0, 0.22):
            a, b = _turn([(cx + t * s, cy), (cx + (t + 0.12) * s, cy - 0.2 * s)], (cx, cy), -32.0)
            _line(d, [a, b], ink_dark, 0.035 * s)
            a, b = _turn([(cx + t * s, cy), (cx + (t + 0.12) * s, cy + 0.2 * s)], (cx, cy), -32.0)
            _line(d, [a, b], ink_dark, 0.035 * s)
    elif sauce == "parmesan":
        # A wedge of cheese, with its holes.
        _poly(d, [(cx - 0.48 * s, cy + 0.3 * s), (cx + 0.48 * s, cy + 0.3 * s), (cx + 0.48 * s, cy - 0.34 * s)], ink, hp.OUTLINE, 1.2)
        _poly(d, [(cx - 0.48 * s, cy + 0.3 * s), (cx + 0.48 * s, cy - 0.34 * s), (cx + 0.3 * s, cy - 0.4 * s)], ink_dark)
        for hx, hy, r in ((0.2, 0.1, 0.09), (0.34, -0.08, 0.06), (-0.04, 0.2, 0.06)):
            _disc(d, cx + hx * s, cy + hy * s, r * s, ink_dark)
    else:
        # A colander: a bowl with holes, two handles and a foot.
        _poly(d, [(cx - 0.5 * s, cy - 0.16 * s), (cx + 0.5 * s, cy - 0.16 * s), (cx + 0.34 * s, cy + 0.28 * s), (cx - 0.34 * s, cy + 0.28 * s)],
              ink, hp.OUTLINE, 1.2)
        _rect(d, cx - 0.56 * s, cy - 0.24 * s, cx + 0.56 * s, cy - 0.12 * s, ink, hp.OUTLINE, 1.0, radius=0.04 * s)
        _rect(d, cx - 0.22 * s, cy + 0.28 * s, cx + 0.22 * s, cy + 0.38 * s, ink_dark, hp.OUTLINE, 1.0)
        for row, n in ((0.0, 5), (0.14, 4)):
            for k in range(n):
                _disc(d, cx + (k - (n - 1) / 2.0) * 0.17 * s, cy + row * s, 0.045 * s, HOLE)


# ---------------------------------------------------------------------------
# Keys.
# ---------------------------------------------------------------------------

def _draw_key(sauce: str, frame_idx: int, nframes: int) -> Image.Image:
    colour, light, dark = SAUCES[sauce]
    canvas = hp.new_super(KEY_FRAME)
    d = blending_draw(canvas)
    phase = frame_idx / max(1, nframes)
    bob = 2.6 * math.sin(math.tau * phase)
    # The key hangs at a lean: its bow up and to the left, its bit down and
    # to the right.
    pivot = (48.0, 48.0 + bob)
    lean = 38.0

    def at(pts):
        return _turn([(x, y + bob) for x, y in pts], pivot, lean)

    # The shaft and the bit, in brass.
    _poly(d, at([(40, 44.5), (84, 44.5), (84, 51.5), (40, 51.5)]), hp.BRASS, hp.OUTLINE)
    _line(d, at([(42, 46.2), (82, 46.2)]), hp.BRASS_HI, 1.4)
    _poly(d, at([(66, 51), (72, 51), (72, 63), (66, 63)]), hp.BRASS, hp.OUTLINE)
    _poly(d, at([(76, 51), (84, 51), (84, 66), (80, 66), (80, 59), (76, 59)]), hp.BRASS, hp.OUTLINE)
    _poly(d, at([(56, 42.5), (60, 42.5), (60, 53.5), (56, 53.5)]), hp.BRASS_DARK, hp.OUTLINE, 1.0)
    # The bow: a ring of brass with the emblem of the sauce in it.
    (bx, by), = at([(26.0, 48.0)])
    _disc(d, bx, by, 21.0, hp.BRASS, hp.OUTLINE, 1.6)
    _disc(d, bx, by, 16.0, dark, hp.OUTLINE, 1.2)
    leaf = SAUCES["pesto"][0] if sauce == "marinara" else light
    _emblem(d, sauce, bx, by, 24.0, colour if sauce != "colander" else light, dark if sauce != "colander" else colour, leaf)
    d.arc((p(bx - 19), p(by - 19), p(bx + 19), p(by + 19)), 200, 290, fill=hp.BRASS_HI, width=_w(1.6))
    # The glint goes round the bow, once each turn of the row.
    a = math.tau * phase - math.pi * 0.75
    gx, gy = bx + math.cos(a) * 18.5, by + math.sin(a) * 18.5
    for r, alpha in ((4.2, 110), (2.4, 230)):
        _disc(d, gx, gy, r, (255, 250, 226, alpha))
    for dx, dy in ((1, 0), (0, 1)):
        _line(d, [(gx - dx * 7.5, gy - dy * 7.5), (gx + dx * 7.5, gy + dy * 7.5)], (255, 250, 226, 200), 0.9)
    return hp.finalize(canvas, KEY_FRAME)


def build_key(out_dir: str | Path, *, target_name: str, sauce: str, display: str) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    def draw(anim: str, frame_idx: int, nframes: int) -> Image.Image:
        if anim != "idle":
            raise ValueError(f"unknown animation: {anim}")
        return _draw_key(sauce, frame_idx, nframes)

    outputs = build_sheet(
        target=target_name,
        rows=KEY_ROWS,
        render_fn=draw,
        out_dir=out_dir,
        frame_size=KEY_FRAME,
        frame_meta_fn=lambda anim, i, n: hp.anchor_meta({"middle": (48.0, 48.0)}),
        auto_crop=False,
        actor_metadata=_actor(target_name, display, "Pickup", ["prop", "key", "pickup", "temple"]),
    )
    return _outputs(outputs)


# ---------------------------------------------------------------------------
# Doors.
# ---------------------------------------------------------------------------

def _slab(d, body: RGBA, body_hi: RGBA, body_dark: RGBA) -> None:
    """The slab of a door, from the top of the frame to its foot: it fills
    the box of the wall, so no gap is at the lintel or at the floor."""
    w, h = DOOR_FRAME
    _rect(d, 3, 0, w - 3, h, body, hp.OUTLINE, 2.0)
    _rect(d, 5, 2, 15, h - 2, body_hi)
    _rect(d, w - 17, 2, w - 5, h - 2, body_dark)
    # Iron bands at the head, the middle and the foot, with their bolts.
    for y0, y1 in ((0, 22), (h - 22, h)):
        _rect(d, 1, y0, w - 1, y1, hp.IRON, hp.OUTLINE, 1.8)
        _rect(d, 3, y0 + 2, w - 3, y0 + 6, hp.IRON_HI)
        for x in (14, w / 2, w - 14):
            _disc(d, x, (y0 + y1) / 2 + 1, 4.2, hp.IRON_DARK, hp.OUTLINE, 1.0)
            _disc(d, x - 1, (y0 + y1) / 2, 1.6, hp.IRON_HI)


def _panel(d, y0: float, y1: float, colour: RGBA, light: RGBA, dark: RGBA) -> None:
    w, _ = DOOR_FRAME
    _rect(d, 16, y0, w - 16, y1, colour, hp.OUTLINE, 1.8, radius=5)
    _line(d, [(20, y1 - 4), (20, y0 + 4), (w - 20, y0 + 4)], light, 2.2)
    _line(d, [(w - 20, y0 + 6), (w - 20, y1 - 4), (22, y1 - 4)], dark, 2.2)


def _lock_plate(d, cy: float, ring: RGBA) -> None:
    w, _ = DOOR_FRAME
    _disc(d, w / 2, cy, 27, hp.BRASS_DARK, hp.OUTLINE, 1.8)
    _disc(d, w / 2, cy, 23, hp.BRASS)
    d.arc((p(w / 2 - 21), p(cy - 21), p(w / 2 + 21), p(cy + 21)), 190, 300, fill=hp.BRASS_HI, width=_w(2.0))
    _disc(d, w / 2, cy, 15.5, ring, hp.OUTLINE, 1.2)
    _keyhole(d, w / 2, cy - 1, 11)


def _noodles(d, y0: float, y1: float, ink: RGBA) -> None:
    """Three noodles down a panel."""
    w, _ = DOOR_FRAME
    for k, x in enumerate((30, 48, 66)):
        pts = [(x + 6.5 * math.sin((y - y0) / 15.0 + k * 1.9), y) for y in range(int(y0), int(y1) + 1, 3)]
        _line(d, pts, ink, 3.4)


def _draw_sauce_door(sauce: str) -> Image.Image:
    colour, light, dark = SAUCES[sauce]
    canvas = hp.new_super(DOOR_FRAME)
    d = blending_draw(canvas)
    if sauce == "colander":
        # Steel, with the holes of a colander from head to foot, and a lock
        # with a ring of gold: the last door.
        _slab(d, colour, light, dark)
        for row in range(11):
            y = 40 + row * 30
            if 150 < y < 236:
                continue
            for k in range(3 if row % 2 == 0 else 2):
                x = (26 + k * 22) if row % 2 == 0 else (37 + k * 22)
                _disc(d, x, y, 5.6, HOLE, hp.OUTLINE, 1.0)
                d.arc((p(x - 5.6), p(y - 5.6), p(x + 5.6), p(y + 5.6)), 20, 160, fill=light, width=_w(1.1))
        _lock_plate(d, 192, SAUCES["parmesan"][0])
        _emblem(d, "colander", 48, 122, 38, light, colour, light)
        return hp.finalize(canvas, DOOR_FRAME)
    _slab(d, STONE, STONE_HI, STONE_DARK)
    _panel(d, 30, 152, colour, light, dark)
    _panel(d, 232, 354, colour, light, dark)
    # The emblem of the sauce, in its own colours on a plate of cream.
    _disc(d, 48, 91, 27, CREAM, hp.OUTLINE, 1.6)
    d.arc((p(48 - 24), p(91 - 24), p(48 + 24), p(91 + 24)), 20, 150, fill=CREAM_DARK, width=_w(2.2))
    _emblem(d, sauce, 48, 92, 36, colour, dark, SAUCES["pesto"][0] if sauce == "marinara" else light)
    _noodles(d, 246, 340, CREAM)
    _lock_plate(d, 192, colour)
    return hp.finalize(canvas, DOOR_FRAME)


def _numeral(d, cx: float, cy: float, n: int, ink: RGBA, s: float = 1.0) -> None:
    """A Roman numeral, I to III."""
    span = 9.0 * s
    _line(d, [(cx - (n * span) / 2 - 3 * s, cy - 11 * s), (cx + (n * span) / 2 + 3 * s, cy - 11 * s)], ink, 2.6 * s)
    _line(d, [(cx - (n * span) / 2 - 3 * s, cy + 11 * s), (cx + (n * span) / 2 + 3 * s, cy + 11 * s)], ink, 2.6 * s)
    for k in range(n):
        x = cx + (k - (n - 1) / 2.0) * span
        _line(d, [(x, cy - 11 * s), (x, cy + 11 * s)], ink, 3.2 * s)


def _draw_sluice(wheel: int, shut_by: bool) -> Image.Image:
    """A sluice of the cistern: boards with iron straps, wet at the foot, and
    a plate with the number of its wheel. A plate of blue is a sluice that
    its wheel opens. A plate of amber with a bar across is a sluice that its
    wheel shuts."""
    w, h = DOOR_FRAME
    canvas = hp.new_super(DOOR_FRAME)
    d = blending_draw(canvas)
    _rect(d, 3, 0, w - 3, h, WOOD, hp.OUTLINE, 2.0)
    for x in (24, 48, 72):
        _line(d, [(x, 2), (x, h - 2)], WOOD_DARK, 1.8)
    for x in (9, 30, 54, 78):
        _line(d, [(x, 26), (x, h - 60)], WOOD_HI, 1.4)
    # The water has been at the foot of it.
    _rect(d, 5, h - 96, w - 5, h - 2, WET)
    for x in (24, 48, 72):
        _line(d, [(x, h - 96), (x, h - 2)], WOOD_DARK, 1.8)
    for k in range(7):
        x = 10 + k * 13
        _line(d, [(x, h - 96), (x + 2, h - 96 + 8 + (k * 5) % 13)], WET, 3.0)
    for y in (0, 150, h - 22):
        _rect(d, 1, y, w - 1, y + 22, hp.IRON, hp.OUTLINE, 1.8)
        _rect(d, 3, y + 2, w - 3, y + 6, hp.IRON_HI)
        for x in (14, w - 14):
            _disc(d, x, y + 12, 4.2, hp.IRON_DARK, hp.OUTLINE, 1.0)
    plate = (224, 150, 48, 255) if shut_by else (72, 150, 196, 255)
    plate_dark = (140, 84, 22, 255) if shut_by else (34, 84, 124, 255)
    _rect(d, 18, 52, w - 18, 124, plate, hp.OUTLINE, 1.8, radius=6)
    _line(d, [(22, 120), (22, 56), (w - 22, 56)], CREAM, 1.6)
    _numeral(d, w / 2, 88, wheel, hp.OUTLINE, 1.25)
    if shut_by:
        _line(d, [(22, 118), (w - 22, 58)], plate_dark, 4.6)
        _line(d, [(22, 118), (w - 22, 58)], hp.OUTLINE, 1.2)
    return hp.finalize(canvas, DOOR_FRAME)


def _draw_bell_seal() -> Image.Image:
    """A seal of the belfry: a slab of bronze with a bell on it."""
    w, h = DOOR_FRAME
    canvas = hp.new_super(DOOR_FRAME)
    d = blending_draw(canvas)
    _slab(d, BRONZE, BRONZE_HI, BRONZE_DARK)
    _panel(d, 30, 354, BRONZE_DARK, BRONZE, hp.OUTLINE)
    cx, cy = w / 2, 176
    # The bell: a crown, a waist that opens to a lip, and its clapper.
    body = [(cx - 9, cy - 46), (cx + 9, cy - 46), (cx + 15, cy - 20), (cx + 19, cy + 18), (cx + 30, cy + 40),
            (cx - 30, cy + 40), (cx - 19, cy + 18), (cx - 15, cy - 20)]
    _poly(d, body, SAUCES["parmesan"][0], hp.OUTLINE, 1.8)
    _line(d, [(cx - 11, cy - 38), (cx - 13, cy - 8), (cx - 17, cy + 22)], SAUCES["parmesan"][1], 3.0)
    _rect(d, cx - 31, cy + 36, cx + 31, cy + 46, SAUCES["parmesan"][2], hp.OUTLINE, 1.4, radius=3)
    _disc(d, cx, cy + 54, 7.5, SAUCES["parmesan"][2], hp.OUTLINE, 1.4)
    _rect(d, cx - 5, cy - 60, cx + 5, cy - 44, SAUCES["parmesan"][2], hp.OUTLINE, 1.4, radius=2)
    for y in (74, 280):
        _noodle_y = y
        pts = [(x, _noodle_y + 5.0 * math.sin(x / 7.0)) for x in range(24, int(w) - 22, 3)]
        _line(d, pts, BRONZE_HI, 3.0)
    return hp.finalize(canvas, DOOR_FRAME)


def build_door(out_dir: str | Path, *, target_name: str, display: str, kind: str, sauce: str = "", wheel: int = 0,
               shut_by: bool = False) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    def draw(anim: str, frame_idx: int, nframes: int) -> Image.Image:
        del frame_idx, nframes
        if anim != "idle":
            raise ValueError(f"unknown animation: {anim}")
        if kind == "sauce":
            return _draw_sauce_door(sauce)
        if kind == "sluice":
            return _draw_sluice(wheel, shut_by)
        if kind == "bell":
            return _draw_bell_seal()
        raise ValueError(f"unknown door: {kind}")

    outputs = build_sheet(
        target=target_name,
        rows=DOOR_ROWS,
        render_fn=draw,
        out_dir=out_dir,
        frame_size=DOOR_FRAME,
        frame_meta_fn=lambda anim, i, n: hp.anchor_meta({"foot": (48.0, 384.0)}, forward=(0.0, -1.0)),
        auto_crop=False,
        actor_metadata=_actor(target_name, display, "Door", ["prop", "door", "lock", "temple"]),
    )
    return _outputs(outputs)


# ---------------------------------------------------------------------------
# The iron grille: a column that tiles.
# ---------------------------------------------------------------------------

#: Rows of the head rail, of the tile and of the foot. Each is a multiple of
#: 12, so each boundary is on a whole texel in the reduced copies.
GRILLE_CAP, GRILLE_TILE, GRILLE_END = 48, 48, 48
GRILLE_FRAME = (96, GRILLE_CAP + GRILLE_TILE + GRILLE_END)
GRILLE_COLUMN_TILE = (GRILLE_CAP, GRILLE_CAP + GRILLE_TILE)
GRILLE_BARS = (18.0, 48.0, 78.0)


def _draw_grille() -> Image.Image:
    w, h = GRILLE_FRAME
    canvas = hp.new_super(GRILLE_FRAME)
    d = blending_draw(canvas)
    # The bars, from the head rail to the points at the foot. A bar is the
    # same in each row of the tile, so the tile joins the next copy of it.
    for x in GRILLE_BARS:
        _rect(d, x - 7, 10, x + 7, h - 22, hp.IRON, hp.OUTLINE, 1.6)
        _rect(d, x - 5, 12, x - 2, h - 22, hp.IRON_HI)
        _rect(d, x + 3, 12, x + 5.4, h - 22, hp.IRON_DARK)
        _poly(d, [(x - 7, h - 23), (x + 7, h - 23), (x, h - 1)], hp.IRON, hp.OUTLINE, 1.6)
        _poly(d, [(x - 5, h - 23), (x - 2, h - 23), (x - 1, h - 9)], hp.IRON_HI)
    # A band across in the cap, in the middle of the tile and in the end.
    for y in (0, GRILLE_CAP + GRILLE_TILE / 2 - 7, GRILLE_CAP + GRILLE_TILE + 4):
        tall = 22 if y == 0 else 14
        _rect(d, 1, y, w - 1, y + tall, hp.IRON_DARK if y else hp.IRON, hp.OUTLINE, 1.6)
        _rect(d, 3, y + 2, w - 3, y + 5, hp.IRON_HI)
        for x in GRILLE_BARS:
            _disc(d, x, y + tall / 2 + 1, 3.6, hp.IRON_DARK, hp.OUTLINE, 1.0)
            _disc(d, x - 0.8, y + tall / 2, 1.3, hp.STEEL_EDGE)
    return hp.finalize(canvas, GRILLE_FRAME)


def build_grille(out_dir: str | Path, *, target_name: str, display: str) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    def draw(anim: str, frame_idx: int, nframes: int) -> Image.Image:
        del frame_idx, nframes
        if anim != "idle":
            raise ValueError(f"unknown animation: {anim}")
        return _draw_grille()

    outputs = build_sheet(
        target=target_name,
        rows=DOOR_ROWS,
        render_fn=draw,
        out_dir=out_dir,
        frame_size=GRILLE_FRAME,
        frame_meta_fn=lambda anim, i, n: hp.anchor_meta({"foot": (48.0, float(GRILLE_FRAME[1]))}, forward=(0.0, -1.0)),
        auto_crop=False,
        actor_metadata=_actor(target_name, display, "Door", ["prop", "door", "grille", "temple"]),
        column_tile=GRILLE_COLUMN_TILE,
    )
    return _outputs(outputs)


def _actor(target_name: str, display: str, body_kind: str, tags: List[str]) -> dict:
    return {
        "actor": {"character_id": f"prop_{target_name}", "display_name": display},
        "body": {
            "body_plan": "Prop",
            "body_kind": body_kind,
            "mass_class": "Heavy" if body_kind == "Door" else "Light",
            "locomotion_hint": "Static",
            "traits": list(tags),
        },
        "brain": {"default_preset": "stand_still"},
        "actions": {"default_preset": "peaceful"},
        "animation_bindings": {"default": {"animation": "idle", "events": []}},
        "sockets": {},
        "tags": list(tags),
    }


def _outputs(outputs: dict) -> List[Path]:
    return [outputs[k] for k in ("canonical", "canonical_transparent", "spritesheet", "yaml", "ron", "actor", "preview")]
