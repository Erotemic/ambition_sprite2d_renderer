"""The props of the Amphitheatre, the performance quarter of the Art dimension.

They are drawn in the cel style of the dimension's cast
(`targets/characters/_art_cast_kit.py`), in the colours of the stage: red
velvet, gold, black and spotlight white (`_stage_kit.py`).

- ``art_curtain``: a door (the look of a `LockWall`). A heavy theatre
  curtain of red velvet, shut, under a scalloped valance with a gold fringe
  and gold tassels. The encounter of the stage (`art_audition`) opens it.
- ``art_spotlight``: scenery. A stage spotlight on a tripod, aimed up and
  forward, with its beam.
- ``art_theatre_masks``: scenery. The masks of comedy and of tragedy on a
  pole, with ribbons.
- ``art_costume_trunk``: scenery. An open trunk that spills costumes: a
  red cape, a feather boa, a crown, a ruff and a jester's cap.

Each frame leaves a margin round the drawing: art that touches the edge of
its frame is cut. Animations: ``idle``. No drop shadows: the game draws
them.
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

from ..characters import _art_cast_kit as K
from ..characters import _stage_kit as S
from .art_props import _publisher

STILL: List[Tuple[str, int, int]] = [("idle", 1, 1000)]
SCENERY = ["prop", "scenery", "art", "stage"]

CURTAIN_FRAME = (128, 384)
SPOTLIGHT_FRAME = (128, 192)
MASKS_FRAME = (192, 256)
TRUNK_FRAME = (160, 96)

VELVET_LIGHT = (226, 64, 84, 255)
BOA = (240, 90, 190, 255)
CLOTH_GREEN = (70, 150, 110, 255)
CLOTH_BLUE = (90, 120, 210, 255)


# ---------------------------------------------------------------------------
# The curtain (a door).
# ---------------------------------------------------------------------------


def _draw_curtain():
    w, h = CURTAIN_FRAME
    f = K.Frame(CURTAIN_FRAME)
    m = 3.0
    top, foot = m, h - m
    # The cloth: two halves that meet at the middle, in deep folds. Each
    # fold is a light stripe and a dark stripe; the hem waves with the folds.
    folds = 8
    fold_w = (w - 2.0 * m) / folds
    hem = []
    for k in range(folds + 1):
        x = m + k * fold_w
        hem.append((x, foot - (0.0 if k % 2 else 5.0)))
    f.poly([(m, top + 20.0)] + hem + [(w - m, top + 20.0)], S.VELVET)
    for k in range(folds):
        x0 = m + k * fold_w
        f.poly([(x0 + fold_w * 0.55, top + 30.0), (x0 + fold_w, top + 30.0), (x0 + fold_w, foot - (0.0 if (k + 1) % 2 else 5.0)),
                (x0 + fold_w * 0.55, foot - 2.5)], S.VELVET_DARK, body=False)
        f.ink([(x0 + fold_w * 0.22, top + 34.0), (x0 + fold_w * 0.18, foot - 14.0)], 2.2, K.alpha(VELVET_LIGHT, 0.85))
    # Where the two halves meet: a dark seam, a little overlap.
    f.limb([(w / 2.0, top + 26.0), (w / 2.0 + 1.0, foot - 3.0)], 2.4, K.shade(S.VELVET_DARK, 0.6), body=False)
    # The gold fringe along the hem.
    for k in range(int((w - 2.0 * m) / 4.0)):
        x = m + 2.0 + k * 4.0
        y = foot - 6.0
        f.ink([(x, y), (x, y + 4.0)], 1.4, K.GOLD_DARK)
    f.limb([(m + 1.0, foot - 7.0), (w - m - 1.0, foot - 7.0)], 2.6, K.GOLD, body=False)
    # The valance: a band of velvet with scallops, a gold edge and a tassel
    # at each point.
    f.poly([(m, top), (w - m, top), (w - m, top + 20.0), (m, top + 20.0)], S.VELVET_DARK)
    scallops = 4
    sw = (w - 2.0 * m) / scallops
    for k in range(scallops):
        x0 = m + k * sw
        arc = [(x0 + sw * u, top + 20.0 + 12.0 * math.sin(math.pi * u)) for u in [j / 10.0 for j in range(11)]]
        f.poly([(x0, top + 18.0)] + arc + [(x0 + sw, top + 18.0)], S.VELVET)
        f.ink(arc, 2.4, K.GOLD)
        # A tassel under the bottom of each scallop.
        tx, ty = x0 + sw / 2.0, top + 32.0
        f.limb([(tx, ty - 1.0), (tx, ty + 6.0)], 1.4, K.GOLD_DARK)
        f.ellipse(tx, ty + 7.0, 2.6, 2.4, K.GOLD)
        f.poly([(tx - 2.6, ty + 8.0), (tx + 2.6, ty + 8.0), (tx + 4.0, ty + 18.0), (tx - 4.0, ty + 18.0)], K.GOLD)
        for j in range(-2, 3):
            f.ink([(tx + j * 1.3, ty + 10.0), (tx + j * 1.8, ty + 17.5)], 0.6, K.GOLD_DARK)
    f.limb([(m + 1.0, top + 3.0), (w - m - 1.0, top + 3.0)], 3.0, K.GOLD, body=False)
    f.ink([(m + 2.0, top + 2.0), (w - m - 2.0, top + 2.0)], 0.8, K.shade(K.GOLD, 1.4))
    # A gold star on the middle of the valance: the door of the stage.
    star = []
    for k in range(10):
        a = -math.pi / 2.0 + k * math.pi / 5.0
        r = 6.5 if k % 2 == 0 else 2.8
        star.append((w / 2.0 + math.cos(a) * r, top + 12.0 + math.sin(a) * r))
    f.poly(star, K.YELLOW, body=False)
    return f.finish(width=1.6)


# ---------------------------------------------------------------------------
# Scenery.
# ---------------------------------------------------------------------------


def _draw_spotlight():
    w, h = SPOTLIGHT_FRAME
    f = K.Frame(SPOTLIGHT_FRAME)
    foot = h - 4.0
    hub = (44.0, 116.0)
    # The beam first, behind everything: a soft cone up and forward.
    lens = (64.0, 70.0)
    f.glow_poly([(lens[0] - 3.0, lens[1] - 7.0), (w - 10.0, 10.0), (w - 10.0, 64.0), (lens[0] + 4.0, lens[1] + 6.0)], K.alpha(S.SPOT, 0.30))
    f.glow_poly([(lens[0], lens[1] - 4.0), (w - 14.0, 22.0), (w - 14.0, 50.0), (lens[0] + 2.0, lens[1] + 3.0)], K.alpha(S.SPOT, 0.35))
    # Dust in the beam.
    for x, y in ((84.0, 50.0), (96.0, 36.0), (104.0, 52.0), (110.0, 30.0), (92.0, 58.0)):
        f.dot(x, y, 0.9, K.alpha(K.WHITE, 0.9))
    # The tripod: three legs from the hub, and a post up to the yoke.
    for fx, colour in ((14.0, K.STEEL_SHADE), (74.0, K.STEEL_SHADE), (46.0, K.STEEL)):
        f.limb([hub, (fx, foot - 2.0)], 3.0, colour)
        f.ellipse(fx, foot - 1.5, 3.0, 1.6, K.INK)
    f.limb([hub, (hub[0], 92.0)], 4.0, K.STEEL)
    f.ellipse(hub[0], hub[1], 4.0, 4.0, K.STEEL_SHADE)
    # The yoke: a U of black steel that holds the lamp.
    f.limb([(hub[0] - 10.0, 72.0), (hub[0] - 10.0, 92.0), (hub[0] + 10.0, 92.0), (hub[0] + 10.0, 72.0)], 3.2, S.BLACK_CLOTH)
    # The lamp: a black can, aimed up and forward, with barn doors at its mouth.
    tilt = -30.0
    cx, cy = 42.0, 76.0

    def T(pts):
        return K.turn([(cx + x, cy + y) for x, y in pts], cx, cy, tilt)

    f.poly(T([(-22.0, -12.0), (14.0, -14.0), (14.0, 14.0), (-22.0, 12.0)]), S.BLACK_CLOTH)
    f.poly(T([(-22.0, 4.0), (14.0, 6.0), (14.0, 14.0), (-22.0, 12.0)]), S.BLACK_SHADE, body=False)
    for k in range(4):
        x = -18.0 + k * 6.0
        f.ink(T([(x, -11.0), (x, -5.0)]), 1.2, S.BLACK_LIGHT)
    f.poly(T([(-26.0, -8.0), (-22.0, -10.0), (-22.0, 10.0), (-26.0, 8.0)]), S.BLACK_SHADE)
    f.ellipse(cx, cy, 3.0, 3.0, K.GOLD)
    # The front ring and the barn doors.
    f.poly(T([(14.0, -16.0), (19.0, -16.0), (19.0, 16.0), (14.0, 16.0)]), K.GOLD)
    f.poly(T([(19.0, -16.0), (28.0, -22.0), (29.0, -19.0), (19.0, -12.0)]), S.BLACK_CLOTH)
    f.poly(T([(19.0, 16.0), (28.0, 22.0), (29.0, 19.0), (19.0, 12.0)]), S.BLACK_CLOTH)
    lx, ly = T([(19.5, 0.0)])[0]
    f.ellipse(lx, ly, 3.0, 11.0, S.SPOT, body=False)
    f.glow(lx, ly, 10.0, K.alpha(S.SPOT, 0.6))
    # A cable from the lamp down the post to the floor.
    f.ink([(hub[0] - 8.0, 86.0), (hub[0] - 4.0, 120.0), (hub[0] - 18.0, foot - 4.0), (hub[0] - 36.0, foot - 2.0)], 1.4, K.INK)
    return f.finish(width=1.6, glow_blur=4.0)


def _mask(f: K.Frame, cx: float, cy: float, spin: float, face: str) -> None:
    """A theatre mask: comedy (a gold face that laughs) or tragedy (a violet
    face that weeps)."""
    if face == "comedy":
        base, shade, line = K.GOLD, K.GOLD_DARK, K.INK
    else:
        base, shade, line = (150, 120, 220, 255), K.VIOLET_DARK, K.INK

    def T(pts):
        return K.turn([(cx + x, cy + y) for x, y in pts], cx, cy, spin)

    outline = [(-24.0, -26.0), (-10.0, -32.0), (10.0, -32.0), (24.0, -26.0), (27.0, -6.0), (22.0, 14.0), (12.0, 28.0), (0.0, 33.0), (-12.0, 28.0),
               (-22.0, 14.0), (-27.0, -6.0)]
    f.poly(T(outline), base)
    f.poly(T([(8.0, -31.0), (24.0, -26.0), (27.0, -6.0), (22.0, 14.0), (12.0, 28.0), (0.0, 33.0), (10.0, 18.0), (16.0, -4.0)]), shade, body=False)
    f.ink(T([(-20.0, -24.0), (-6.0, -29.0)]), 1.4, K.alpha(K.WHITE, 0.7))
    if face == "comedy":
        # Eyes that laugh (arcs up), brows high, a wide grin.
        for ex in (-10.0, 10.0):
            f.poly(T([(ex - 7.0, -6.0), (ex, -13.0), (ex + 7.0, -6.0), (ex + 5.0, -4.0), (ex, -8.5), (ex - 5.0, -4.0)]), line, body=False)
            f.ink(T([(ex - 7.0, -18.0), (ex, -22.0), (ex + 7.0, -18.0)]), 1.6, line)
        grin = [(-16.0, 8.0), (-8.0, 18.0), (0.0, 21.0), (8.0, 18.0), (16.0, 8.0), (8.0, 11.0), (0.0, 12.0), (-8.0, 11.0)]
        f.poly(T(grin), line, body=False)
        f.poly(T([(-10.0, 12.0), (10.0, 12.0), (7.0, 16.0), (-7.0, 16.0)]), S.VELVET, body=False)
        f.ellipse(*T([(-17.0, 3.0)])[0], 4.0, 2.6, K.alpha(S.VELVET, 0.45), body=False)
        f.ellipse(*T([(17.0, 3.0)])[0], 4.0, 2.6, K.alpha(S.VELVET, 0.45), body=False)
    else:
        # Eyes that weep (arcs down), brows up in the middle, a mouth turned down.
        for ex in (-10.0, 10.0):
            f.poly(T([(ex - 7.0, -10.0), (ex, -4.0), (ex + 7.0, -10.0), (ex + 5.0, -12.0), (ex, -8.0), (ex - 5.0, -12.0)]), line, body=False)
            inner = 1.0 if ex < 0 else -1.0
            f.ink(T([(ex - 7.0 * inner, -17.0), (ex + 6.0 * inner, -23.0)]), 1.6, line)
        mouth = [(-14.0, 22.0), (-8.0, 12.0), (0.0, 10.0), (8.0, 12.0), (14.0, 22.0), (8.0, 17.0), (0.0, 16.0), (-8.0, 17.0)]
        f.poly(T(mouth), line, body=False)
        for tx, ty in ((-12.0, 0.0), (11.0, 2.0)):
            f.poly(T([(tx, ty - 3.0), (tx + 2.4, ty + 3.0), (tx, ty + 5.0), (tx - 2.4, ty + 3.0)]), K.CYAN_LIGHT, body=False)


def _draw_masks():
    w, h = MASKS_FRAME
    f = K.Frame(MASKS_FRAME)
    foot = h - 4.0
    px = w / 2.0
    # The base and the pole.
    f.poly([(px - 26.0, foot), (px + 26.0, foot), (px + 20.0, foot - 10.0), (px - 20.0, foot - 10.0)], K.WOOD_DARK)
    f.poly([(px - 20.0, foot - 10.0), (px + 20.0, foot - 10.0), (px + 14.0, foot - 16.0), (px - 14.0, foot - 16.0)], K.WOOD)
    f.limb([(px, foot - 14.0), (px, 64.0)], 6.0, K.GOLD)
    f.ink([(px - 1.2, foot - 16.0), (px - 1.2, 66.0)], 1.2, K.shade(K.GOLD, 1.35))
    f.ellipse(px, 60.0, 6.0, 6.0, K.GOLD)
    f.dot(px - 2.0, 58.0, 1.6, K.shade(K.GOLD, 1.4))
    # The ribbons from the top of the pole, behind the masks.
    for side in (-1.0, 1.0):
        f.limb([(px, 98.0), (px + side * 10.0, 120.0), (px + side * 6.0, 146.0), (px + side * 16.0, 170.0)], 4.0, S.VELVET)
        f.limb([(px + side * 16.0, 170.0), (px + side * 22.0, 178.0)], 4.0, S.VELVET_DARK)
    f.ellipse(px, 98.0, 7.0, 4.0, S.VELVET)
    f.ellipse(px - 6.0, 98.0, 4.0, 3.0, S.VELVET_DARK)
    f.ellipse(px + 6.0, 98.0, 4.0, 3.0, S.VELVET_DARK)
    # The masks, one each side of the pole and over it, a little turned.
    _mask(f, px - 30.0, 100.0, -14.0, "tragedy")
    _mask(f, px + 30.0, 92.0, 12.0, "comedy")
    return f.finish(width=1.8)


def _draw_trunk():
    w, h = TRUNK_FRAME
    f = K.Frame(TRUNK_FRAME)
    foot = h - 4.0
    x0, x1 = 24.0, 128.0
    top = foot - 44.0
    # The lid, open and leaned back, behind the box.
    lid = [(x0 + 2.0, top), (x1 - 2.0, top), (x1 + 8.0, top - 34.0), (x0 + 12.0, top - 36.0)]
    f.poly(lid, K.WOOD_DARK)
    f.poly([(x0 + 8.0, top - 3.0), (x1 - 6.0, top - 3.0), (x1 + 2.0, top - 30.0), (x0 + 15.0, top - 32.0)], S.VELVET_DARK, body=False)
    f.ink([(x0 + 4.0, top - 1.0), (x0 + 13.0, top - 35.0)], 2.2, K.GOLD)
    f.ink([(x1 - 4.0, top - 1.0), (x1 + 7.0, top - 33.0)], 2.2, K.GOLD)
    # The heap of clothes that fills the box, over its rim.
    heap = [(x0 + 4.0, top + 2.0), (x0 + 8.0, top - 10.0), (x0 + 22.0, top - 14.0), (x0 + 40.0, top - 10.0), (x0 + 56.0, top - 16.0),
            (x0 + 76.0, top - 12.0), (x0 + 92.0, top - 16.0), (x1 - 4.0, top - 6.0), (x1 - 4.0, top + 2.0)]
    f.poly(heap, CLOTH_GREEN)
    f.poly([(x0 + 50.0, top + 2.0), (x0 + 56.0, top - 16.0), (x0 + 76.0, top - 12.0), (x0 + 82.0, top + 2.0)], CLOTH_BLUE, body=False)
    for dx, dy in ((x0 + 60.0, top - 10.0), (x0 + 68.0, top - 6.0), (x0 + 74.0, top - 11.0), (x0 + 64.0, top - 2.0)):
        f.dot(dx, dy, 1.3, K.WHITE)
    f.ink([(x0 + 10.0, top - 6.0), (x0 + 24.0, top - 10.0), (x0 + 40.0, top - 6.0)], 1.2, K.shade(CLOTH_GREEN, 0.7))
    # A jester's cap on the heap: two floppy points, each with a bell.
    jx, jy = x0 + 90.0, top - 14.0
    f.poly([(jx - 10.0, jy + 4.0), (jx + 10.0, jy + 4.0), (jx + 6.0, jy - 4.0), (jx - 6.0, jy - 4.0)], K.YELLOW)
    f.poly([(jx - 6.0, jy - 3.0), (jx, jy - 2.0), (jx - 10.0, jy - 16.0), (jx - 18.0, jy - 16.0)], K.CYAN)
    f.poly([(jx, jy - 2.0), (jx + 6.0, jy - 3.0), (jx + 18.0, jy - 12.0), (jx + 14.0, jy - 18.0)], K.YELLOW)
    f.ellipse(jx - 19.0, jy - 16.0, 2.6, 2.6, K.GOLD)
    f.ellipse(jx + 17.0, jy - 17.0, 2.6, 2.6, K.GOLD)
    f.limb([(jx - 10.0, jy + 3.0), (jx + 10.0, jy + 3.0)], 2.0, S.VELVET, body=False)
    # The crown on the heap.
    cx, cy = x0 + 64.0, top - 18.0
    crown = [(cx - 12.0, cy + 6.0), (cx + 12.0, cy + 6.0), (cx + 13.0, cy - 8.0), (cx + 7.0, cy - 2.0), (cx, cy - 12.0), (cx - 7.0, cy - 2.0),
             (cx - 13.0, cy - 8.0)]
    f.poly(crown, K.GOLD)
    f.poly([(cx - 12.0, cy + 6.0), (cx + 12.0, cy + 6.0), (cx + 12.0, cy + 2.0), (cx - 12.0, cy + 2.0)], K.GOLD_DARK, body=False)
    for gx, colour in ((cx - 6.0, K.CYAN), (cx, S.VELVET), (cx + 6.0, K.CYAN)):
        f.dot(gx, cy + 4.0, 1.6, colour)
    f.dot(cx, cy - 12.0, 1.8, K.WHITE)
    # A white ruff, a ring of folds, laid on the heap.
    rx, ry = x0 + 26.0, top - 14.0
    f.ellipse(rx, ry, 14.0, 6.0, K.WHITE)
    for k in range(9):
        a = math.pi * k / 8.0
        f.ink([(rx + math.cos(a) * 6.0, ry - math.sin(a) * 2.5), (rx + math.cos(a) * 13.0, ry - math.sin(a) * 5.0)], 0.8, K.STEEL_SHADE)
    f.ellipse(rx, ry, 5.0, 2.0, K.PAPER_SHADE, body=False)
    # The box: wood with gold bands and brass corners.
    f.poly([(x0, foot), (x1, foot), (x1, top), (x0, top)], K.WOOD)
    f.poly([(x1 - 20.0, foot), (x1, foot), (x1, top), (x1 - 20.0, top)], K.WOOD_DARK, body=False)
    for y in (top + 4.0, foot - 6.0):
        f.limb([(x0 + 1.0, y), (x1 - 1.0, y)], 3.0, K.GOLD, body=False)
    for x in (x0 + 24.0, x1 - 24.0):
        f.limb([(x, top + 1.0), (x, foot - 1.0)], 3.0, K.GOLD_DARK, body=False)
    for x, y in ((x0, top), (x1, top), (x0, foot), (x1, foot)):
        sx = 5.0 if x == x0 else -5.0
        sy = 5.0 if y == top else -5.0
        f.poly([(x, y), (x + sx, y), (x + sx, y + sy), (x, y + sy)], K.GOLD, body=False)
    mid = (x0 + x1) / 2.0
    f.poly([(mid - 5.0, top + 2.0), (mid + 5.0, top + 2.0), (mid + 5.0, top + 12.0), (mid - 5.0, top + 12.0)], K.GOLD, body=False)
    f.dot(mid, top + 8.0, 1.4, K.INK)
    # The red cape that spills over the front edge and onto the floor.
    cape = [(x0 + 44.0, top - 2.0), (x0 + 66.0, top - 2.0), (x0 + 70.0, top + 18.0), (x0 + 60.0, foot - 8.0), (x0 + 62.0, foot - 2.0),
            (x0 + 34.0, foot - 1.0), (x0 + 42.0, top + 22.0)]
    f.poly(cape, S.VELVET)
    f.poly([(x0 + 58.0, top - 2.0), (x0 + 66.0, top - 2.0), (x0 + 70.0, top + 18.0), (x0 + 60.0, foot - 8.0), (x0 + 56.0, top + 20.0)], S.VELVET_DARK, body=False)
    f.ink([(x0 + 48.0, top + 2.0), (x0 + 46.0, top + 26.0), (x0 + 40.0, foot - 4.0)], 1.4, VELVET_LIGHT)
    f.ellipse(x0 + 55.0, top + 1.0, 3.2, 3.2, K.GOLD)
    # A feather boa over the side, in puffs of pink.
    boa = [(x1 - 14.0, top - 4.0), (x1 + 2.0, top + 4.0), (x1 + 10.0, top + 18.0), (x1 + 6.0, top + 30.0), (x1 + 14.0, foot - 5.0), (x1 + 20.0, foot - 4.0)]
    for k in range(len(boa) - 1):
        for u in (0.0, 0.25, 0.5, 0.75):
            x = boa[k][0] + (boa[k + 1][0] - boa[k][0]) * u
            y = boa[k][1] + (boa[k + 1][1] - boa[k][1]) * u
            # A puff of feathers: a ring of points, not a smooth ball.
            puff = []
            for j in range(14):
                a = math.tau * j / 14.0 + k + u
                r = 5.2 if j % 2 == 0 else 3.2
                puff.append((x + math.cos(a) * r, y + math.sin(a) * r * 0.9))
            f.poly(puff, BOA)
            f.ink([(x - 2.0, y - 1.0), (x + 1.0, y - 3.0)], 0.8, K.MAGENTA_LIGHT)
            f.dot(x + 1.2, y + 1.4, 0.9, K.MAGENTA)
    return f.finish(width=1.6)


# ---------------------------------------------------------------------------
# Publication.
# ---------------------------------------------------------------------------

TARGETS: Dict[str, dict] = {
    "art_curtain": _publisher("art_curtain", "Stage Curtain", STILL, CURTAIN_FRAME, lambda anim, i, n: _draw_curtain(), {"foot": (64.0, 384.0)}, "Door",
                              ["prop", "door", "curtain", "art", "stage"], forward=(0.0, -1.0)),
    "art_spotlight": _publisher("art_spotlight", "Spotlight", STILL, SPOTLIGHT_FRAME, lambda anim, i, n: _draw_spotlight(), {"foot": (44.0, 192.0)}, "Scenery",
                                SCENERY),
    "art_theatre_masks": _publisher("art_theatre_masks", "Theatre Masks", STILL, MASKS_FRAME, lambda anim, i, n: _draw_masks(), {"foot": (96.0, 256.0)},
                                    "Scenery", SCENERY),
    "art_costume_trunk": _publisher("art_costume_trunk", "Costume Trunk", STILL, TRUNK_FRAME, lambda anim, i, n: _draw_trunk(), {"foot": (80.0, 96.0)},
                                    "Scenery", SCENERY),
}
