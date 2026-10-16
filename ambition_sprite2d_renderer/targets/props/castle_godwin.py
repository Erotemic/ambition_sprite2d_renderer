"""Castle Godwin of the Evil dimension: its entrance, its sign, the thorns at
its foot.

- ``castle_godwin_entrance``: the front of the castle where the forest ends,
  after the fortress doors of Super Mario World: a tower of big blue-grey
  blocks with battlements, a black doorway under a raised portcullis, and the
  name CASTLE GODWIN cut in a stone over the door. Red banners with the mark
  of the regime hang at each side; the slit windows glow with fire. It is
  scenery (an LDtk `Prop`): the room puts the door that is walked through
  over the doorway (`DOOR` gives where it is).
- ``castle_godwin_sign``: a board on two posts at the road, with the name of
  the castle. A body reads it (an `NpcSpawn` with a dialogue).
- ``evil_thorn_bush``: a black-green bush of thorns, after the round bushes
  at a Mario fortress.

The mark of the regime is a black gear on a white disc on red. It is an
invented mark: no real symbol of a real regime is drawn.

Drawn in world units at `PX` pixels to the unit; the bottom of the frame is
the ground. No drop shadow is drawn.

Animations:

- ``idle``: 1 frame.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import numpy as np
from PIL import Image

from ...authoring.sheet_build import build_sheet
from ._town_kit import Canvas, box, mix, scale

#: Pixels of the frame to one world unit.
PX = 2

STONE = (92, 104, 128)
STONE_LIGHT = (150, 162, 184)
STONE_DARK = (40, 46, 62)
MORTAR = (18, 20, 28)
PLAQUE = (170, 168, 156)
RED = (150, 18, 22)
RED_DARK = (86, 8, 14)
WHITE = (226, 222, 214)
BLACK = (10, 8, 10)
FIRE = (255, 120, 50)
IRON = (34, 34, 40)
WOOD = (62, 42, 32)
WOOD_LIGHT = (104, 74, 54)

# ---------------------------------------------------------------------------
# Letters: block capitals as strokes on a 4 x 6 grid
# ---------------------------------------------------------------------------

GLYPHS: Dict[str, List[List[Tuple[float, float]]]] = {
    "A": [[(0, 6), (0, 1), (1, 0), (3, 0), (4, 1), (4, 6)], [(0, 3.2), (4, 3.2)]],
    "C": [[(4, 0), (0.6, 0), (0, 0.6), (0, 5.4), (0.6, 6), (4, 6)]],
    "D": [[(0, 0), (3, 0), (4, 1), (4, 5), (3, 6), (0, 6), (0, 0)]],
    "E": [[(4, 0), (0, 0), (0, 6), (4, 6)], [(0, 3), (3, 3)]],
    "G": [[(4, 0), (0.6, 0), (0, 0.6), (0, 5.4), (0.6, 6), (4, 6), (4, 3.2), (2.2, 3.2)]],
    "I": [[(0.8, 0), (3.2, 0)], [(2, 0), (2, 6)], [(0.8, 6), (3.2, 6)]],
    "L": [[(0, 0), (0, 6), (4, 6)]],
    "N": [[(0, 6), (0, 0), (4, 6), (4, 0)]],
    "O": [[(0.6, 0), (3.4, 0), (4, 0.6), (4, 5.4), (3.4, 6), (0.6, 6), (0, 5.4), (0, 0.6), (0.6, 0)]],
    "S": [[(4, 0), (0.6, 0), (0, 0.6), (0, 2.6), (0.6, 3), (3.4, 3), (4, 3.4), (4, 5.4), (3.4, 6), (0, 6)]],
    "T": [[(0, 0), (4, 0)], [(2, 0), (2, 6)]],
    "W": [[(0, 0), (1, 6), (2, 2.6), (3, 6), (4, 0)]],
    "B": [[(0, 0), (3, 0), (4, 0.8), (4, 2.2), (3, 3), (0, 3)], [(3, 3), (4, 3.8), (4, 5.2), (3, 6), (0, 6), (0, 0)]],
    "F": [[(4, 0), (0, 0), (0, 6)], [(0, 3), (3, 3)]],
    "H": [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]],
    "K": [[(0, 0), (0, 6)], [(4, 0), (0, 3.4)], [(1.2, 2.6), (4, 6)]],
    "M": [[(0, 6), (0, 0), (2, 3), (4, 0), (4, 6)]],
    "P": [[(0, 6), (0, 0), (3, 0), (4, 0.8), (4, 2.4), (3, 3.2), (0, 3.2)]],
    "R": [[(0, 6), (0, 0), (3, 0), (4, 0.8), (4, 2.4), (3, 3.2), (0, 3.2)], [(1.6, 3.2), (4, 6)]],
    "U": [[(0, 0), (0, 5.4), (0.6, 6), (3.4, 6), (4, 5.4), (4, 0)]],
    "V": [[(0, 0), (2, 6), (4, 0)]],
    "Y": [[(0, 0), (2, 3), (4, 0)], [(2, 3), (2, 6)]],
    "0": [[(0.6, 0), (3.4, 0), (4, 0.6), (4, 5.4), (3.4, 6), (0.6, 6), (0, 5.4), (0, 0.6), (0.6, 0)]],
    "1": [[(0.8, 1.2), (2.2, 0), (2.2, 6)], [(0.8, 6), (3.6, 6)]],
    "2": [[(0, 0.8), (0.8, 0), (3.2, 0), (4, 0.8), (4, 2.4), (0, 6), (4, 6)]],
    "3": [[(0, 0), (4, 0), (2, 2.6), (3.4, 2.6), (4, 3.4), (4, 5.4), (3.4, 6), (0, 6)]],
    "5": [[(4, 0), (0, 0), (0, 2.6), (3.4, 2.6), (4, 3.2), (4, 5.4), (3.4, 6), (0, 6)]],
    "7": [[(0, 0), (4, 0), (1.6, 6)]],
    ",": [[(2.2, 5.0), (2.2, 6.0), (1.2, 7.2)]],
    ":": [[(2, 1.6), (2, 2.2)], [(2, 4.6), (2, 5.2)]],
    "!": [[(2, 0), (2, 4.0)], [(2, 5.4), (2, 6)]],
}


def lettering(c: Canvas, text: str, cx: float, top: float, h: float, ink, light=None) -> None:
    """`text` in block capitals `h` high, centred on `cx`. With `light`, the
    letters are cut: dark strokes with a light edge under them."""
    unit = h / 6.0
    adv = unit * 5.4
    width = adv * len(text) - unit * 1.4
    x = cx - width / 2
    stroke = unit * 1.0
    strokes = []
    for ch in text:
        for path in GLYPHS.get(ch, []):
            strokes.append([(x + px * unit, top + py * unit) for px, py in path])
        x += adv
    if light is not None:
        c.put(c.mask(lambda p: [p.line([(a + unit * 0.25, b + unit * 0.35) for a, b in s], stroke) for s in strokes]), light, 0.8)
    c.put(c.mask(lambda p: [p.line(s, stroke) for s in strokes]), ink)


def emblem(c: Canvas, cx: float, cy: float, r: float) -> None:
    """The mark of the regime: a black eight-tooth gear on a white disc."""
    c.put(c.mask(lambda p: p.ellipse(cx, cy, r)), WHITE)
    teeth = 8
    pts = []
    for k in range(teeth * 4):
        a = math.tau * k / (teeth * 4)
        rr = r * (0.80 if (k % 4) in (1, 2) else 0.60)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    gear = c.mask(lambda p: p.poly(pts)) * (1.0 - c.mask(lambda p: p.ellipse(cx, cy, r * 0.22)))
    c.put(gear, BLACK)


def banner(c: Canvas, cx: float, top: float, w: float, h: float) -> None:
    """A long red banner with a pointed foot and the mark of the regime."""
    pts = [(cx - w / 2, top), (cx + w / 2, top), (cx + w / 2, top + h), (cx, top + h - w * 0.45), (cx - w / 2, top + h)]
    m = c.mask(lambda p: p.poly(pts))
    c.paint(m, c.ramp([(top, RED), (top + h, RED_DARK)]))
    # Folds: soft dark bands down the cloth.
    folds = 0.5 + 0.5 * np.sin((c.x - cx) / w * math.pi * 3.0)
    c.tone(m * folds, -0.22)
    c.put(c.mask(box(cx - w / 2 - 2, top - 3, cx + w / 2 + 2, top + 1)), IRON)
    emblem(c, cx, top + h * 0.32, w * 0.36)


# ---------------------------------------------------------------------------
# The blocks of a Mario fortress
# ---------------------------------------------------------------------------


def blocks(c: Canvas, x0: float, y0: float, x1: float, y1: float, tag, row_h: float = 32.0) -> np.ndarray:
    """A wall of big rounded blocks from (x0, y0) to (x1, y1), courses from
    the bottom: each block a little lighter or darker, lit at its top edge,
    dark at its foot, with the spots of a Mario fortress stone. Returns the
    mask of the wall."""
    rng = c.rand(tag, "blocks")
    wall = c.mask(box(x0, y0, x1, y1))
    c.put(wall, MORTAR)
    y = y1
    row = 0
    while y > y0 + 0.5:
        top = max(y0, y - row_h)
        x = x0 - (rng.uniform(8, 28) if row % 2 else 0)
        while x < x1:
            w = rng.choice((32.0, 40.0, 48.0, 56.0, 64.0))
            bx0, bx1 = max(x0, x) + 1.2, min(x1, x + w) - 1.2
            if bx1 > bx0 + 2:
                m = c.mask(box(bx0, top + 1.2, bx1, y - 1.2), blur=0.9) * wall
                c.put(m, scale(STONE, rng.uniform(0.9, 1.08)))
                c.put(m * c.mask(box(bx0, top + 1.2, bx1, top + 4.0), blur=0.8), STONE_LIGHT, 0.75)
                c.put(m * c.mask(box(bx0, top + 1.2, bx0 + 3.0, y - 1.2), blur=0.8), STONE_LIGHT, 0.35)
                c.put(m * c.mask(box(bx0, y - 5.0, bx1, y - 1.2), blur=0.8), STONE_DARK, 0.6)
                c.put(m * c.mask(box(bx1 - 3.5, top + 1.2, bx1, y - 1.2), blur=0.8), STONE_DARK, 0.4)
            x += w
        y = top
        row += 1
    # The spots of the stone.
    spots = (c.noise((tag, "spots"), 70, 70, 2) > 0.66).astype(np.float32)
    c.put(c.soften(spots, 0.5) * wall * (c.mask(box(x0, y0, x1, y1)) > 0), STONE_DARK, 0.45)
    return wall


def battlements(c: Canvas, x0: float, x1: float, top: float, merlon: float = 28.0, gap: float = 20.0, h: float = 26.0, tag="merlons") -> None:
    """Merlons along the top of a wall from `x0` to `x1`; `top` is the top of the wall."""
    x = x0
    k = 0
    while x + merlon <= x1 + 0.5:
        blocks(c, x, top - h, x + merlon, top, (tag, k), row_h=h)
        x += merlon + gap
        k += 1


def slit(c: Canvas, cx: float, top: float, h: float, w: float = 8.0) -> None:
    """A slit window with the light of fire in it."""
    m = c.mask(lambda p: (p.rect(cx - w / 2, top + w / 2, cx + w / 2, top + h), p.ellipse(cx, top + w / 2, w / 2)))
    c.put(m, mix(FIRE, BLACK, 0.35))
    c.light(m * c.mask(box(cx - w / 2, top + h * 0.5, cx + w / 2, top + h)), FIRE, 0.6)


# ---------------------------------------------------------------------------
# The entrance
# ---------------------------------------------------------------------------

#: The front of the castle, in world units: its width and height.
ENTRANCE_W, ENTRANCE_H = 352, 448
#: The doorway: its left edge, its width and its height over the ground. The
#: room's door (a 48 x 96 `LoadingZone`) goes in it.
DOOR = (144, 72, 112)


def _entrance(c: Canvas) -> None:
    w, h = ENTRANCE_W, ENTRANCE_H
    g = h
    wall_top = 104
    # The tower: the wall, its battlements, and a turret on the left.
    blocks(c, 0, wall_top, w, g, "front")
    battlements(c, 0, w, wall_top, tag="front merlons")
    blocks(c, 24, 26, 120, wall_top, "turret")
    battlements(c, 24, 120, 26, merlon=20, gap=18, h=22, tag="turret merlons")
    slit(c, 72, 44, 40)
    for cx in (36, 316):
        slit(c, cx, 150, 48)
    # The doorway: a frame of lighter dressed stone, then the dark.
    dx, dw, dh = DOOR
    top = g - dh
    c.put(c.mask(box(dx - 14, top - 18, dx + dw + 14, g)), MORTAR)
    blocks(c, dx - 14, top - 18, dx - 1, g, "jamb l", row_h=24)
    blocks(c, dx + dw + 1, top - 18, dx + dw + 14, g, "jamb r", row_h=24)
    blocks(c, dx - 14, top - 18, dx + dw + 14, top - 1, "lintel", row_h=17)
    dark = c.mask(box(dx, top, dx + dw, g))
    c.put(dark, BLACK)
    # Far inside, the red of fire.
    c.light(dark * np.clip((c.y - (g - 40)) / 40.0, 0, 1) * np.exp(-((c.x - (dx + dw / 2)) / (dw * 0.4)) ** 2), FIRE, 0.35)
    # The portcullis, raised: its teeth under the lintel.
    bars = c.mask(lambda p: [p.rect(dx + 4 + k * 10, top, dx + 7 + k * 10, top + 14) for k in range(int(dw // 10))])
    teeth = c.mask(lambda p: [p.poly([(dx + 3 + k * 10, top + 14), (dx + 8 + k * 10, top + 14), (dx + 5.5 + k * 10, top + 20)]) for k in range(int(dw // 10))])
    c.put(c.mask(box(dx, top, dx + dw, top + 4)), IRON)
    c.put(np.maximum(bars, teeth), IRON)
    c.put(np.maximum(bars, teeth) * c.mask(box(dx, top, dx + dw, top + 20)) * (np.mod(c.x, 10) < 1.2), (80, 80, 92), 0.7)
    # The name, cut in a stone over the door.
    py0, py1 = top - 70, top - 30
    px0, px1 = dx + dw / 2 - 92, dx + dw / 2 + 92
    plaque = c.mask(box(px0, py0, px1, py1), blur=0.6)
    c.put(c.mask(box(px0 - 3, py0 - 3, px1 + 3, py1 + 3)), MORTAR)
    c.put(plaque, PLAQUE)
    c.put(plaque * c.mask(box(px0, py0, px1, py0 + 3)), (214, 210, 198), 0.8)
    c.put(plaque * c.mask(box(px0, py1 - 3, px1, py1)), scale(PLAQUE, 0.6), 0.8)
    lettering(c, "CASTLE", dx + dw / 2, py0 + 5, 13, (30, 26, 28), light=(230, 226, 214))
    lettering(c, "GODWIN", dx + dw / 2, py0 + 22, 13, (30, 26, 28), light=(230, 226, 214))
    # The banners of the regime, at each side of the door.
    for cx in (dx - 48, dx + dw + 48):
        banner(c, cx, wall_top + 20, 40, 132)
    # Torches in iron cages at the door.
    for cx in (dx - 22, dx + dw + 22):
        c.put(c.mask(lambda p: (p.rect(cx - 2, top + 12, cx + 2, top + 34), p.poly([(cx - 7, top + 4), (cx + 7, top + 4), (cx + 4, top + 14), (cx - 4, top + 14)]))), IRON)
        flame = c.mask(lambda p: p.poly([(cx - 5, top + 5), (cx + 5, top + 5), (cx + 1, top - 10), (cx - 1, top - 4)]), blur=0.6)
        c.put(flame, FIRE)
        c.put(c.mask(lambda p: p.ellipse(cx, top + 1, 2.5, 3.5), blur=0.6), (255, 220, 150))
        c.light(c.mask(lambda p: p.ellipse(cx, top, 26), blur=12.0) * (c.alpha > 0.5), FIRE, 0.30)


def _sign(c: Canvas) -> None:
    """A board on two posts with the name of the castle, and the mark."""
    w, h = SIGN_W, SIGN_H
    g = h
    for px in (10, w - 14):
        post = c.mask(box(px, 20, px + 5, g))
        c.put(post, WOOD)
        c.put(post * c.mask(box(px, 20, px + 1.5, g)), WOOD_LIGHT, 0.6)
    board = c.mask(box(2, 8, w - 2, 46), blur=0.4)
    c.put(c.mask(box(0, 6, w, 48)), (24, 16, 12))
    c.paint(board, c.ramp([(8, WOOD_LIGHT), (46, WOOD)]))
    grain = c.noise("sign grain", 3, 30, 3)
    c.tone(board * (grain - 0.5), 0.3)
    lettering(c, "CASTLE", w / 2 + 6, 13, 10, (236, 226, 200))
    lettering(c, "GODWIN", w / 2 + 6, 29, 10, (236, 226, 200))
    c.put(c.mask(box(4, 10, 20, 44)), RED)
    emblem(c, 12, 27, 6.5)
    # Nails, and a dark smear of paint that ran.
    c.put(c.mask(lambda p: [p.ellipse(x, y, 1.0) for x, y in ((5, 11), (w - 5, 11), (5, 43), (w - 5, 43))]), (20, 20, 22))
    c.put(c.mask(lambda p: p.line([(w - 30, 44), (w - 30, 52)], 1.4)), RED_DARK, 0.8)


SIGN_W, SIGN_H = 96, 72


def _thorn_bush(c: Canvas) -> None:
    """Round lumps of black-green leaf, with thorns at the edge."""
    w, h = BUSH_W, BUSH_H
    rng = c.rand("thorn bush")
    lumps = [(w * 0.30, h - 18, 18), (w * 0.55, h - 26, 24), (w * 0.78, h - 16, 16), (w * 0.45, h - 12, 14)]
    body = c.mask(lambda p: [p.ellipse(x, y, r, r * 0.95) for x, y, r in lumps] + [p.rect(w * 0.14, h - 12, w * 0.92, h)])
    c.paint(body, c.ramp([(0, (40, 56, 36)), (h, (12, 20, 14))]))
    for x, y, r in lumps:
        c.put(body * c.mask(lambda p: p.ellipse(x - r * 0.3, y - r * 0.35, r * 0.55), blur=2.0), (70, 90, 52), 0.5)
    thorns = []
    for _ in range(26):
        x, y, r = rng.choice(lumps)
        a = rng.uniform(math.pi * 0.9, math.pi * 2.1)
        bx, by = x + r * math.cos(a), y + r * 0.95 * math.sin(a)
        tx, ty = x + (r + 5) * math.cos(a), y + (r + 5) * 0.95 * math.sin(a)
        n = (-math.sin(a) * 1.6, math.cos(a) * 1.6)
        thorns.append([(bx + n[0], by + n[1]), (bx - n[0], by - n[1]), (tx, ty)])
    c.put(c.mask(lambda p: [p.poly(t) for t in thorns]), (20, 26, 18))
    # A few red berries.
    c.put(c.mask(lambda p: [p.ellipse(rng.uniform(w * 0.2, w * 0.85), rng.uniform(h - 34, h - 8), 1.6) for _ in range(7)]), (190, 24, 30))


BUSH_W, BUSH_H = 96, 56


PROPS: Dict[str, Tuple[float, float, Callable[[Canvas], None], List[str]]] = {
    # name: (width, height, draw, tags)
    "castle_godwin_entrance": (ENTRANCE_W, ENTRANCE_H, _entrance, ["prop", "scenery", "castle"]),
    "castle_godwin_sign": (SIGN_W, SIGN_H, _sign, ["prop", "sign"]),
    "evil_thorn_bush": (BUSH_W, BUSH_H, _thorn_bush, ["prop", "scenery", "plant"]),
}


def _frame_size(name: str) -> Tuple[int, int]:
    w, h, _, _ = PROPS[name]
    return (int(w * PX), int(h * PX))


def _draw(name: str) -> Image.Image:
    w, h, draw, _ = PROPS[name]
    c = Canvas(name, w, h, origin=(0.0, 0.0), ppu=PX)
    draw(c)
    return c.image()


def _renderer(name: str):
    def render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
        del frame_idx, nframes
        if anim != "idle":
            raise ValueError(f"unknown animation: {anim}")
        return _draw(name)

    def frame_meta(anim: str, frame_idx: int, nframes: int) -> dict:
        del anim, frame_idx, nframes
        fw, fh = _frame_size(name)
        return {"anchors": {"foot": {"x": fw / 2, "y": float(fh)}}, "forward": {"x": 0.0, "y": -1.0}, "angle_deg": 0.0}

    def render(out_dir: str | Path, **opts) -> List[Path]:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        outputs = build_sheet(
            target=name,
            rows=[("idle", 1, 400)],
            render_fn=render_frame,
            out_dir=out_dir,
            frame_size=_frame_size(name),
            frame_meta_fn=frame_meta,
            auto_crop=False,
            actor_metadata=_actor(name),
        )
        return [outputs[key] for key in ("canonical", "canonical_transparent", "spritesheet", "yaml", "ron", "actor", "preview")]

    return render


def _actor(name: str) -> dict:
    tags = PROPS[name][3]
    return {
        "actor": {"character_id": f"prop_{name}", "display_name": name.replace("_", " ").title()},
        "body": {"body_plan": "Prop", "body_kind": "Scenery", "mass_class": "Heavy", "locomotion_hint": "Static", "traits": tags},
        "brain": {"default_preset": "stand_still"},
        "actions": {"default_preset": "peaceful"},
        "animation_bindings": {"default": {"animation": "idle", "events": []}},
        "tags": tags,
    }


TARGETS = {name: {"render": _renderer(name), "actor_metadata": _actor(name)} for name in PROPS}

__all__ = ["PROPS", "PX", "DOOR", "ENTRANCE_W", "ENTRANCE_H", "TARGETS"]
