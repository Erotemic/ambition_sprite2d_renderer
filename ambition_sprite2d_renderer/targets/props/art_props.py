"""The props of the Art dimension (`art.ldtk`).

The keys and the doors of the colour gate, and the scenery of the plaza and
the garden, drawn in the cel style of the dimension's cast
(`targets/characters/_art_cast_kit.py`).

- ``art_pigment_<colour>``: a key. A jar of pigment that glows, with a cork
  and a paper label; a `PickupSpawn` draws its ``idle`` row (a slow bob
  and a glint across the glass). Cyan, magenta and yellow are the three
  primaries a painter mixes every other colour from.
- ``art_colour_gate_<colour>``: a door (the look of a `LockWall` of 32 by
  128 world units, drawn at 3 to 1). A slab of canvas in a gold frame,
  painted in its colour, with a stencil cut through it: the shape of the
  jar of that colour's label.
- ``art_drain_grate``: the look of the plaza's drain (a `LockWall` of 64 by
  64 world units, drawn at 3 to 1): an iron grate in the floor, stained with
  the ink that comes up through it.
- ``art_palette_lift``: the look of a lift (a `MovingPlatform` whose
  ``visual`` it is): a painter's palette seen from its edge, with blobs of
  paint on its top. Its top surface is row ``PALETTE_TOP`` of the frame
  (`data/platform_looks.ron`).
- ``art_easel``, ``art_giant_crayon``, ``art_paint_pots``: scenery (a
  `Prop`): an easel with a canvas on it that somebody has started, a crayon
  as tall as a door, a heap of pots of paint with paint run out of them.

Animations: ``idle``. No drop shadows: the game draws them.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Callable, Dict, List, Tuple

from ...authoring.sheet_build import build_sheet
from ..characters import _art_cast_kit as K
from . import _held_prop_common as hp

#: Each primary: its colour, its light, its dark, and the shape of its stencil.
PRIMARIES = {
    "cyan": (K.CYAN, K.CYAN_LIGHT, (16, 120, 160, 255), "circle"),
    "magenta": (K.MAGENTA, K.MAGENTA_LIGHT, (140, 20, 104, 255), "star"),
    "yellow": (K.YELLOW, (255, 240, 160, 255), (196, 140, 10, 255), "triangle"),
}

KEY_FRAME = (96, 96)
KEY_ROWS: List[Tuple[str, int, int]] = [("idle", 8, 110)]
DOOR_FRAME = (96, 384)
STILL: List[Tuple[str, int, int]] = [("idle", 1, 1000)]


def _stencil(shape: str, cx: float, cy: float, r: float) -> List[Tuple[float, float]]:
    if shape == "circle":
        return K.ellipse_points(cx, cy, r, r, 28)
    if shape == "triangle":
        return [(cx, cy - r), (cx + r * 0.95, cy + r * 0.7), (cx - r * 0.95, cy + r * 0.7)]
    pts = []
    for k in range(10):
        a = -math.pi / 2.0 + k * math.pi / 5.0
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    return pts


# ---------------------------------------------------------------------------
# Keys: jars of pigment.
# ---------------------------------------------------------------------------


def _draw_pigment(colour: str, i: int, n: int):
    base, light, dark, shape = PRIMARIES[colour]
    t = i / float(n)
    f = K.Frame(KEY_FRAME)
    cx, cy = 48.0, 50.0 + 3.0 * math.sin(math.tau * t)
    # The glow of the pigment round the jar.
    f.glow(cx, cy + 4.0, 26.0, K.alpha(base, 0.30))
    # The jar: round shoulders, a neck, a cork.
    jar = [(cx - 15.0, cy + 18.0), (cx + 15.0, cy + 18.0), (cx + 17.0, cy + 2.0), (cx + 13.0, cy - 10.0), (cx + 7.0, cy - 14.0),
           (cx - 7.0, cy - 14.0), (cx - 13.0, cy - 10.0), (cx - 17.0, cy + 2.0)]
    f.poly(jar, K.alpha((230, 240, 255, 255), 1.0))
    f.poly([(cx - 15.0, cy + 18.0), (cx + 15.0, cy + 18.0), (cx + 16.6, cy - 2.0), (cx - 16.6, cy - 2.0)], base, body=False)
    f.poly([(cx + 8.0, cy + 18.0), (cx + 15.0, cy + 18.0), (cx + 16.6, cy - 2.0), (cx + 10.0, cy - 2.0)], dark, body=False)
    f.ellipse(cx, cy - 2.0, 16.6, 3.0, light, body=False)
    f.poly([(cx - 7.0, cy - 14.0), (cx + 7.0, cy - 14.0), (cx + 7.0, cy - 19.0), (cx - 7.0, cy - 19.0)], (230, 240, 255, 255))
    f.poly([(cx - 6.0, cy - 18.0), (cx + 6.0, cy - 18.0), (cx + 5.0, cy - 25.0), (cx - 5.0, cy - 25.0)], K.WOOD)
    f.ink([(cx - 5.0, cy - 21.0), (cx + 5.0, cy - 21.0)], 0.7, K.WOOD_DARK)
    # A paper label with the shape of its colour's stencil on it.
    f.poly([(cx - 10.0, cy + 2.0), (cx + 8.0, cy + 2.0), (cx + 8.0, cy + 13.0), (cx - 10.0, cy + 13.0)], K.PAPER, body=False)
    f.poly(_stencil(shape, cx - 1.0, cy + 7.5, 4.2), K.INK, body=False)
    # The glint that goes across the glass.
    gx = cx - 18.0 + 36.0 * t
    if abs(gx - cx) < 16.0:
        f.ink([(gx - 2.0, cy + 14.0), (gx + 3.0, cy - 8.0)], 1.6, K.alpha(K.WHITE, 0.85))
    f.ink([(cx - 12.0, cy - 6.0), (cx - 13.0, cy + 6.0)], 1.4, K.alpha(K.WHITE, 0.7))
    return f.finish(width=1.4)


# ---------------------------------------------------------------------------
# Doors: the colour gate.
# ---------------------------------------------------------------------------


def _draw_gate(colour: str):
    base, light, dark, shape = PRIMARIES[colour]
    w, h = DOOR_FRAME
    f = K.Frame(DOOR_FRAME)
    # The gold frame, from the top of the box to its foot: no gap at either end.
    f.poly([(4.0, 0.0), (w - 4.0, 0.0), (w - 4.0, h), (4.0, h)], K.GOLD)
    f.poly([(w - 14.0, 0.0), (w - 4.0, 0.0), (w - 4.0, h), (w - 14.0, h)], K.GOLD_DARK, body=False)
    for y in (24.0, h - 24.0):
        f.ink([(4.0, y), (w - 4.0, y)], 1.4, K.GOLD_DARK)
        for x in (16.0, w / 2.0, w - 16.0):
            f.ellipse(x, y - 10.0, 3.6, 3.6, K.shade(K.GOLD, 1.2), body=False)
    # The canvas in the frame, painted in its colour, darker to the foot.
    f.poly([(14.0, 30.0), (w - 14.0, 30.0), (w - 14.0, h - 30.0), (14.0, h - 30.0)], base, body=False)
    f.poly([(w - 30.0, 30.0), (w - 14.0, 30.0), (w - 14.0, h - 30.0), (w - 30.0, h - 30.0)], dark, body=False)
    # Brush strokes on the paint: the marks of a hand, not a machine.
    for k in range(7):
        y = 50.0 + k * 42.0
        f.ink([(20.0, y), (40.0, y - 6.0), (66.0, y + 2.0)], 2.2, K.alpha(light, 0.7))
    # Paint that has run down from the head of the canvas.
    for k, (x, length) in enumerate(((22.0, 46.0), (36.0, 22.0), (52.0, 64.0), (68.0, 30.0))):
        f.limb([(x, 30.0), (x, 30.0 + length)], 4.0, light, body=False)
    # The stencil: its shape cut through the canvas, dark, with a lit rim,
    # the lock that the jar of this colour opens.
    cy = h / 2.0
    hole = _stencil(shape, w / 2.0, cy, 24.0)
    f.poly(K.grow(hole, 4.0), K.GOLD, body=False)
    f.poly(hole, K.INK, body=False)
    f.glow_poly(K.grow(hole, -6.0), K.alpha(base, 0.55))
    return f.finish(width=1.6, glow_blur=2.0)


# ---------------------------------------------------------------------------
# Scenery.
# ---------------------------------------------------------------------------

EASEL_FRAME = (128, 176)
CRAYON_FRAME = (64, 256)
POTS_FRAME = (144, 96)


GRATE_FRAME = (192, 192)


def _draw_grate():
    w, h = GRATE_FRAME
    # A margin inside the frame: the outline is drawn round the grate, and
    # art that touches the edge of the frame is cut.
    m = 6.0
    f = K.Frame(GRATE_FRAME)
    iron, iron_dark = (96, 92, 118, 255), (54, 50, 74, 255)
    f.poly([(m, m), (w - m, m), (w - m, h - m), (m, h - m)], iron_dark)
    for k in range(6):
        x = m + 10.0 + k * 31.0
        f.poly([(x, m), (x + 13.0, m), (x + 13.0, h - m), (x, h - m)], iron, body=False)
        f.ink([(x + 2.0, m), (x + 2.0, h - m)], 1.4, K.shade(iron, 1.3))
    for y in (m + 6.0, h - m - 18.0):
        f.poly([(m, y), (w - m, y), (w - m, y + 12.0), (m, y + 12.0)], iron, body=False)
    # Ink that came up through the bars and dried on them.
    for x, length in ((40.0, 60.0), (104.0, 96.0), (150.0, 40.0)):
        f.limb([(x, 24.0), (x, 24.0 + length)], 6.0, K.MAGENTA, body=False)
    f.glow(w / 2.0, h / 2.0, 60.0, K.alpha(K.MAGENTA, 0.18))
    return f.finish(width=1.6, glow_blur=3.0)


PALETTE_FRAME = (192, 64)
#: The platform's top: the row of the frame the palette's top is on, and the
#: span of its width (`data/platform_looks.ron` repeats these numbers).
PALETTE_TOP = 20.0
PALETTE_SPAN = (16.0, 176.0)


def _draw_palette():
    w, h = PALETTE_FRAME
    f = K.Frame(PALETTE_FRAME)
    x0, x1 = PALETTE_SPAN
    top = PALETTE_TOP
    # The board: thick at its middle, thin at its ends, with the hole for a
    # thumb at its left.
    board = [(x0, top), (x1, top), (x1 + 6.0, top + 6.0), (x1 - 8.0, top + 16.0), (x0 + 30.0, top + 18.0), (x0 - 6.0, top + 8.0)]
    f.poly(board, K.WOOD)
    f.poly([(x0 + 30.0, top + 12.0), (x1 - 8.0, top + 10.0), (x1 - 8.0, top + 16.0), (x0 + 30.0, top + 18.0)], K.WOOD_DARK, body=False)
    f.ink([(x0, top + 1.2), (x1, top + 1.2)], 1.2, K.shade(K.WOOD, 1.35))
    f.ellipse(x0 + 18.0, top + 8.0, 6.0, 3.6, K.INK, body=False)
    # Blobs of paint along its top, standing a little over the surface.
    for k, colour in enumerate((K.MAGENTA, K.YELLOW, K.CYAN, K.WHITE, K.VIOLET, (255, 130, 60, 255))):
        x = x0 + 40.0 + k * 21.0
        f.ellipse(x, top + 1.0, 7.0, 3.4, colour, body=False)
        f.ellipse(x - 2.0, top - 0.4, 2.6, 1.2, K.alpha(K.WHITE, 0.7), body=False)
    # A brush laid across it.
    f.limb([(x0 + 26.0, top - 2.0), (x1 - 40.0, top - 6.0)], 2.6, K.WOOD_DARK)
    f.ellipse(x1 - 36.0, top - 6.4, 4.0, 2.4, K.MAGENTA)
    return f.finish(width=1.4)


def _draw_easel():
    w, h = EASEL_FRAME
    f = K.Frame(EASEL_FRAME)
    foot = h - 6.0
    # The three legs and the ledge the canvas stands on.
    f.limb([(30.0, foot), (62.0, 14.0)], 5.0, K.WOOD)
    f.limb([(98.0, foot), (66.0, 14.0)], 5.0, K.WOOD)
    f.limb([(64.0, 14.0), (78.0, foot - 4.0)], 4.0, K.WOOD_DARK)
    f.limb([(30.0, 112.0), (98.0, 112.0)], 4.0, K.WOOD)
    # The canvas: a picture that somebody started, of the plaza's portal.
    f.poly([(26.0, 24.0), (102.0, 24.0), (102.0, 110.0), (26.0, 110.0)], K.PAPER)
    f.poly([(26.0, 74.0), (102.0, 74.0), (102.0, 110.0), (26.0, 110.0)], K.alpha((180, 220, 240, 255), 1.0), body=False)
    f.ellipse(64.0, 62.0, 18.0, 22.0, K.MAGENTA_LIGHT, body=False)
    f.ellipse(64.0, 62.0, 11.0, 14.0, K.CYAN_LIGHT, body=False)
    f.ellipse(64.0, 62.0, 5.0, 6.0, K.YELLOW, body=False)
    f.ink([(30.0, 96.0), (50.0, 90.0), (72.0, 98.0), (98.0, 92.0)], 2.0, K.alpha(K.VIOLET, 0.8))
    # Unfinished: a corner of the canvas is still pencil.
    for k in range(4):
        f.ink([(80.0 + k * 5.0, 28.0), (100.0, 46.0 - k * 4.0)], 0.6, K.alpha(K.INK, 0.4))
    # A brush on the ledge.
    f.limb([(70.0, 108.0), (96.0, 104.0)], 2.2, K.WOOD_DARK)
    f.ellipse(98.0, 104.0, 3.0, 2.0, K.MAGENTA)
    return f.finish(width=1.6)


def _draw_crayon():
    w, h = CRAYON_FRAME
    f = K.Frame(CRAYON_FRAME)
    foot, top, tip = h - 4.0, 50.0, 6.0
    body = [(10.0, foot), (54.0, foot), (54.0, top), (40.0, tip + 10.0), (32.0, tip), (24.0, tip + 10.0), (10.0, top)]
    f.poly(body, K.MAGENTA)
    f.poly([(40.0, foot), (54.0, foot), (54.0, top), (40.0, tip + 10.0), (34.0, tip + 4.0), (40.0, top)], K.shade(K.MAGENTA, 0.75), body=False)
    # The paper wrapper with its bands and its name.
    f.poly([(10.0, 90.0), (54.0, 90.0), (54.0, 200.0), (10.0, 200.0)], K.PAPER, body=False)
    for y in (96.0, 194.0):
        f.limb([(10.0, y), (54.0, y)], 3.0, K.MAGENTA, body=False)
    f.ink([(18.0, 120.0), (18.0, 170.0)], 3.0, K.alpha(K.VIOLET, 0.7))
    f.ink([(26.0, 130.0), (34.0, 130.0), (30.0, 160.0)], 1.4, K.alpha(K.INK, 0.5))
    f.poly([(40.0, 90.0), (54.0, 90.0), (54.0, 200.0), (40.0, 200.0)], K.alpha(K.PAPER_SHADE, 1.0), body=False)
    # Its point is worn flat on one side: somebody used it.
    f.poly([(24.0, tip + 10.0), (32.0, tip), (34.0, tip + 14.0)], K.MAGENTA_LIGHT, body=False)
    return f.finish(width=1.8)


def _draw_pots():
    w, h = POTS_FRAME
    f = K.Frame(POTS_FRAME)
    foot = h - 9.0
    # The paint that has run out on the ground, under the pots.
    f.ellipse(96.0, foot - 2.0, 40.0, 5.0, K.CYAN)
    f.ellipse(40.0, foot - 2.0, 26.0, 4.0, K.MAGENTA)
    for x, y, r, colour in ((30.0, foot, 18.0, K.YELLOW), (66.0, foot, 22.0, K.MAGENTA), (48.0, foot - 36.0, 15.0, K.CYAN)):
        top = y - r * 2.0
        f.poly([(x - r, y), (x + r, y), (x + r, top), (x - r, top)], K.STEEL)
        f.poly([(x + r * 0.4, y), (x + r, y), (x + r, top), (x + r * 0.4, top)], K.STEEL_SHADE, body=False)
        f.ellipse(x, top, r, r * 0.3, K.shade(K.STEEL, 0.8))
        f.ellipse(x, top, r * 0.82, r * 0.22, colour, body=False)
        for k in range(3):
            dx = x - r * 0.6 + k * r * 0.5
            f.limb([(dx, top), (dx, top + 6.0 + 5.0 * k)], 3.0, colour, body=False)
        f.ink([(x - r, top + r * 0.6), (x + r, top + r * 0.6)], 1.0, K.STEEL_SHADE)
    # One pot on its side, its paint run out across the ground.
    f.poly([(96.0, foot), (136.0, foot), (136.0, foot - 22.0), (96.0, foot - 22.0)], K.STEEL)
    f.ellipse(96.0, foot - 11.0, 5.0, 11.0, K.shade(K.STEEL, 0.8))
    f.ellipse(96.0, foot - 11.0, 3.6, 8.4, K.CYAN, body=False)
    return f.finish(width=1.6)


# ---------------------------------------------------------------------------
# Publication.
# ---------------------------------------------------------------------------


def _actor(target_name: str, display: str, body_kind: str, tags: List[str]) -> dict:
    return {
        "actor": {"character_id": f"prop_{target_name}", "display_name": display},
        "body": {"body_plan": "Prop", "body_kind": body_kind, "mass_class": "Heavy" if body_kind == "Door" else "Light",
                 "locomotion_hint": "Static", "traits": list(tags)},
        "brain": {"default_preset": "stand_still"},
        "actions": {"default_preset": "peaceful"},
        "animation_bindings": {"default": {"animation": "idle", "events": []}},
        "sockets": {},
        "tags": list(tags),
    }


def _publisher(target_name: str, display: str, rows, frame_size, draw: Callable, anchors: Dict[str, Tuple[float, float]], body_kind: str, tags: List[str], forward=None):
    def render(out_dir: str | Path, **opts) -> List[Path]:
        del opts
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        meta = (lambda anim, i, n: hp.anchor_meta(anchors, forward=forward)) if forward else (lambda anim, i, n: hp.anchor_meta(anchors))
        outputs = build_sheet(target=target_name, rows=rows, render_fn=draw, out_dir=out_dir, frame_size=frame_size,
                              frame_meta_fn=meta, auto_crop=False, actor_metadata=_actor(target_name, display, body_kind, tags))
        return [outputs[k] for k in ("canonical", "canonical_transparent", "spritesheet", "yaml", "ron", "actor", "preview")]

    return {"render": render, "rows": rows, "actor_metadata": _actor(target_name, display, body_kind, tags)}


TARGETS: Dict[str, dict] = {}
for _colour in PRIMARIES:
    TARGETS[f"art_pigment_{_colour}"] = _publisher(
        f"art_pigment_{_colour}", f"{_colour.title()} Pigment", KEY_ROWS, KEY_FRAME,
        (lambda c: lambda anim, i, n: _draw_pigment(c, i, n))(_colour), {"middle": (48.0, 48.0)}, "Pickup", ["prop", "key", "pickup", "art"])
    TARGETS[f"art_colour_gate_{_colour}"] = _publisher(
        f"art_colour_gate_{_colour}", f"{_colour.title()} Gate", STILL, DOOR_FRAME,
        (lambda c: lambda anim, i, n: _draw_gate(c))(_colour), {"foot": (48.0, 384.0)}, "Door", ["prop", "door", "lock", "art"], forward=(0.0, -1.0))
TARGETS["art_drain_grate"] = _publisher("art_drain_grate", "Drain Grate", STILL, GRATE_FRAME, lambda anim, i, n: _draw_grate(), {"foot": (96.0, 192.0)}, "Door", ["prop", "door", "grate", "art"], forward=(0.0, -1.0))
TARGETS["art_palette_lift"] = _publisher("art_palette_lift", "Palette Lift", STILL, PALETTE_FRAME, lambda anim, i, n: _draw_palette(), {"top": (96.0, PALETTE_TOP)}, "Scenery", ["prop", "platform", "art"])
TARGETS["art_easel"] = _publisher("art_easel", "Easel", STILL, EASEL_FRAME, lambda anim, i, n: _draw_easel(), {"foot": (64.0, 176.0)}, "Scenery", ["prop", "scenery", "art"])
TARGETS["art_giant_crayon"] = _publisher("art_giant_crayon", "Giant Crayon", STILL, CRAYON_FRAME, lambda anim, i, n: _draw_crayon(), {"foot": (32.0, 256.0)}, "Scenery", ["prop", "scenery", "art"])
TARGETS["art_paint_pots"] = _publisher("art_paint_pots", "Paint Pots", STILL, POTS_FRAME, lambda anim, i, n: _draw_pots(), {"foot": (72.0, 96.0)}, "Scenery", ["prop", "scenery", "art"])
