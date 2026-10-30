"""Scenery of the Pirate Cove (`pirate_cove`, PvN dimension): the pirates' sea
cave under the hub, with the Mockingbird's arena through its far mouth.

Drawn in the room's coordinates (`_district_props`) over its walk lines: the
floor (y 608), the lookout ledges (y 384, x 320..512; y 320, x 720..912).

- `cove_cave`: the cave round the room: rock walls, the great mouth open on
  the night sea (the backdrop shows through it), dripping stalactites, the
  Jolly Roger, lanterns on chains, the wanted board.
- `cove_ledges`: the two lookouts, rope-lashed plank scaffolds on posts, and
  the ladder from the right one up the rock to the sky hatch (y 224..320).
- `cove_doorways`: the stair passage to the hub (x 56), the timber tunnel to
  the port's docks (x 808), the scorched mouth to the arena (x 1180).
- `cove_dressing`: a beached longboat, the quartermaster's treasure heap,
  barrels, rope and the parrot's perch.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .pirate_port_props import PAL, PLANK, PLANK_DARK, PLANK_LIGHT, ROPE, TIMBER, barrel, coil, crate, deck_edge, lantern, post, rope_line, sag

W, H, FLOOR = 1280, 640, 608
LEDGE_L = (320, 512, 384)
LEDGE_R = (720, 912, 320)
HATCH_X = 792
ROCK = (62, 70, 78)
ROCK_DARK = (34, 40, 48)
ROCK_LIGHT = (108, 120, 128)
WET = (150, 190, 200)
SEA_NIGHT = (24, 52, 72)
GOLD = (236, 196, 84)
EMBER = (255, 140, 60)


def rock(c, m, tag):
    """Rock in `m`: a base, broken by noise into slabs, lit from the mouth."""
    c.put(m, ROCK)
    n = c.noise((tag, "slabs"), 18, 10, 4)
    c.tone(m * (n - 0.5), 0.45)
    seams = np.clip(1 - np.abs(c.noise((tag, "seams"), 10, 6, 2) - 0.5) * 30, 0, 1)
    c.put(m * seams, ROCK_DARK, 0.6)


def cove_cave(c, k):
    """The cave round the room, its mouth open on the night sea."""
    full = c.mask(box(0, 0, W, FLOOR))
    mouth = c.mask(lambda p: p.ellipse(640, 250, 330, 190), blur=6) * c.mask(box(0, 0, W, FLOOR - 120))
    m = np.clip(full - mouth, 0, 1)
    rock(c, m, "cove_rock")
    # The rim of the mouth catches the moonlight.
    rim = np.clip(c.mask(lambda p: p.ellipse(640, 250, 342, 202), blur=4) - c.mask(lambda p: p.ellipse(640, 250, 330, 190), blur=4), 0, 1)
    c.put(rim * m, ROCK_LIGHT, 0.7)
    c.tone(m * np.clip(1 - np.hypot((c.x - 640) / 520, (c.y - 260) / 360), 0, 1), 0.25)
    # The sea seen through the mouth, low in it, with a moon path.
    sea = mouth * c.mask(box(0, 360, W, FLOOR))
    c.put(sea, SEA_NIGHT)
    c.put(sea * c.mask(lambda p: [p.rect(560 + (i * 37) % 160, 372 + i * 9, 600 + (i * 37) % 160 + 30, 374 + i * 9) for i in range(12)]), WET, 0.5)
    # Stalactites from the roof, each with a drop.
    rng = c.rand("stalactites")
    tips = []
    for x in np.arange(30, W, 46):
        top = 0 if not (300 < x < 980) else max(0, 250 - 190 * math.sqrt(max(0, 1 - ((x - 640) / 330) ** 2)) - 10)
        length = rng.uniform(26, 70)
        if top + length > 120 and 300 < x < 980:
            continue
        tips.append((x, top, length))
    c.put(c.mask(lambda p: [p.poly([(x - 9, t), (x + 9, t), (x + 1, t + L), (x - 1, t + L)]) for x, t, L in tips]), ROCK_DARK)
    c.put(c.mask(lambda p: [p.ellipse(x, t + L + 6, 1.6, 2.4) for x, t, L in tips[::3]]), WET, 0.8)
    # The Jolly Roger on the rock over the hub door.
    fx0, fy0 = 120, 150
    c.put(c.mask(box(fx0, fy0, fx0 + 120, fy0 + 76)), (22, 22, 26))
    c.put(c.mask(lambda p: [p.poly([(fx0 + 120, fy0 + y), (fx0 + 128, fy0 + y + 6), (fx0 + 120, fy0 + y + 12)]) for y in range(0, 72, 12)]), (22, 22, 26))
    skull = (236, 230, 214)
    sx, sy = fx0 + 60, fy0 + 32
    c.put(c.mask(lambda p: (p.ellipse(sx, sy, 15, 13), p.rect(sx - 8, sy + 8, sx + 8, sy + 17))), skull)
    c.put(c.mask(lambda p: (p.ellipse(sx - 6, sy, 4), p.ellipse(sx + 6, sy, 4), p.poly([(sx, sy + 5), (sx - 2, sy + 9), (sx + 2, sy + 9)]))), (22, 22, 26))
    c.put(c.mask(lambda p: (p.line([(sx - 30, sy + 24), (sx + 30, sy + 40)], 5), p.line([(sx - 30, sy + 40), (sx + 30, sy + 24)], 5))), skull)
    c.put(c.mask(lambda p: [p.ellipse(x, y, 4) for x, y in ((sx - 32, sy + 23), (sx - 32, sy + 41), (sx + 32, sy + 23), (sx + 32, sy + 41))]), skull)
    for x in (fx0, fx0 + 120):
        c.put(c.mask(lambda p: p.line([(x, fy0 - 2), (x + (8 if x == fx0 else -8), fy0 - 14)], 1.4)), ROPE)
    # The wanted board: three faces on a plank, a dagger through one.
    bx0, by0 = 1000, 330
    c.put(c.mask(box(bx0, by0, bx0 + 150, by0 + 96)), PLANK_DARK)
    for i, (px, tilt) in enumerate(((bx0 + 10, -3), (bx0 + 56, 2), (bx0 + 102, -1))):
        poster = c.mask(lambda p: p.poly([(px, by0 + 10 + tilt), (px + 40, by0 + 10 - tilt), (px + 40, by0 + 82 - tilt), (px, by0 + 82 + tilt)]))
        c.put(poster, (222, 206, 168))
        c.put(c.mask(lambda p: (p.ellipse(px + 20, by0 + 36, 10, 12), p.rect(px + 8, by0 + 50, px + 32, by0 + 66))), (90, 70, 56), 0.8)
        c.put(c.mask(lambda p: p.rect(px + 6, by0 + 70, px + 34, by0 + 74)), (150, 60, 50), 0.8)
    c.put(c.mask(lambda p: (p.line([(bx0 + 76, by0 + 30), (bx0 + 76, by0 + 4)], 2.2), p.rect(bx0 + 70, by0 + 2, bx0 + 82, by0 + 6))), (200, 200, 210))
    # Lanterns on chains from the roof.
    for lx, ly in ((240, 120), (620, 60), (1080, 120)):
        c.put(c.mask(lambda p: p.line([(lx, 0), (lx, ly)], 0.9)), PAL["iron"])
        lantern(c, k, lx, ly + 10, 0.9)


def cove_ledges(c, k):
    """The two lookouts and the ladder to the sky hatch."""
    for x0, x1, y in (LEDGE_L, LEDGE_R):
        for px in (x0 + 14, x1 - 14):
            post(c, px, y + 5, FLOOR, 7, TIMBER)
        rope_line(c, [(x0 + 14, y + 40), (x1 - 14, FLOOR - 40)], 1.4)
        rope_line(c, [(x1 - 14, y + 40), (x0 + 14, FLOOR - 40)], 1.4)
        c.put(c.mask(box(x0, y, x1, y + 12)), PLANK)
        c.put(c.mask(lambda p: [p.rect(x, y, x + 0.8, y + 12) for x in np.arange(x0 + 16, x1, 16)]), PLANK_DARK, 0.9)
        deck_edge(c, x0 - 4, x1 + 4, y, PLANK_LIGHT)
        # Rope lashings round the posts.
        for px in (x0 + 14, x1 - 14):
            c.put(c.mask(lambda p: [p.rect(px - 5, yy, px + 5, yy + 1.4) for yy in (y + 14, y + 18, y + 22)]), ROPE)
        rope_line(c, sag((x0, y - 26), (x1, y - 26), 6), 1.1)
        for px in (x0 + 2, x1 - 2):
            post(c, px, y - 30, y, 3, TIMBER)
    # The ladder from the right lookout up the rock to the hatch, and the
    # hatch itself: a trapdoor in the roof with the sky over it.
    lx = HATCH_X
    for side in (-12, 12):
        c.put(c.mask(box(lx + side - 2, 16, lx + side + 2, LEDGE_R[2])), PLANK_DARK)
    c.put(c.mask(lambda p: [p.rect(lx - 12, y, lx + 12, y + 3) for y in np.arange(36, LEDGE_R[2], 18)]), PLANK)
    hatch = c.mask(box(lx - 26, 8, lx + 26, 26))
    c.put(hatch, PLANK_DARK)
    c.light(c.mask(box(lx - 22, 10, lx + 22, 22)), (150, 190, 230), 0.4)


def cove_doorways(c, k):
    """The ways out: stairs to the hub, the tunnel to the docks, the arena."""
    # The hub door (x 56..104): a passage cut in the rock with steps going up.
    c.put(c.mask(lambda p: p.arch(46, FLOOR - 126, 114, FLOOR)), ROCK_DARK)
    c.put(c.mask(lambda p: [p.rect(52 + i * 6, FLOOR - 16 - i * 14, 108, FLOOR - 2 - i * 14) for i in range(6)]), ROCK_LIGHT, 0.6)
    # The docks door (x 808..856): a timber-framed tunnel with a lantern and
    # an anchor board.
    c.put(c.mask(box(798, FLOOR - 112, 866, FLOOR)), (20, 24, 30))
    for x in (798, 860):
        post(c, x + 3, FLOOR - 116, FLOOR, 8, TIMBER)
    c.put(c.mask(box(792, FLOOR - 120, 872, FLOOR - 108)), TIMBER)
    lantern(c, k, 880, FLOOR - 104, 0.8)
    ax, ay = 832, FLOOR - 140
    c.put(c.mask(box(ax - 18, ay - 12, ax + 18, ay + 12)), PLANK)
    c.put(c.mask(lambda p: (p.line([(ax, ay - 8), (ax, ay + 8)], 1.6), p.line([(ax - 8, ay + 2), (ax, ay + 9), (ax + 8, ay + 2)], 1.4), p.ring(ax, ay - 9, 2.4, 1.0))), (40, 44, 52))
    # The arena door (x 1180..1228): a scorched mouth glowing like a furnace,
    # with feathers blown out of it.
    mouth = c.mask(lambda p: p.arch(1164, FLOOR - 150, 1250, FLOOR))
    c.put(mouth, (30, 14, 10))
    c.light(c.mask(lambda p: p.ellipse(1207, FLOOR - 40, 46, 70), blur=18), EMBER, 0.7)
    c.put(np.clip(c.mask(lambda p: p.arch(1158, FLOOR - 158, 1256, FLOOR), blur=3) - mouth, 0, 1), (20, 18, 20), 0.8)
    rng = c.rand("feathers")
    for _ in range(9):
        fx, fy, a = rng.uniform(1080, 1250), rng.uniform(FLOOR - 160, FLOOR - 4), rng.uniform(0, math.pi)
        ca, sa = math.cos(a), math.sin(a)
        vane = [(fx + ca * t * 12 - sa * w, fy + sa * t * 12 + ca * w) for t, w in ((-1, 0), (-0.4, 4), (0.6, 3), (1, 0), (0.6, -2.5), (-0.4, -3))]
        c.put(c.mask(lambda p: p.poly(vane)), (196, 200, 208))
        c.put(c.mask(lambda p: p.line([(fx - ca * 15, fy - sa * 15), (fx + ca * 12, fy + sa * 12)], 0.8)), (80, 82, 90))


def cove_dressing(c, k):
    """What the pirates keep here."""
    k.ground = FLOOR
    # A longboat drawn up on the boards, oars across it.
    bx0, bx1, by = 520, 700, FLOOR
    hull = c.mask(lambda p: p.poly([(bx0, by - 34), (bx1, by - 40), (bx1 - 16, by - 4), (bx0 + 20, by)]))
    c.put(hull, (110, 70, 44))
    c.put(c.mask(lambda p: [p.line([(bx0 + 4, by - 34 + i * 8), (bx1 - 4 - i * 4, by - 40 + i * 8)], 0.8) for i in range(1, 4)]) * hull, (70, 44, 28), 0.9)
    c.put(c.mask(lambda p: p.line([(bx0, by - 35), (bx1, by - 41)], 2.4)), PLANK_LIGHT)
    c.put(c.mask(lambda p: (p.line([(bx0 + 40, by - 50), (bx1 - 30, by - 30)], 2.2), p.line([(bx0 + 70, by - 28), (bx1 - 10, by - 56)], 2.2))), PLANK)
    # The quartermaster's heap: a chest spilling coins.
    tx, ty = 940, FLOOR
    c.put(c.mask(lambda p: p.ellipse(tx + 10, ty, 70, 22) ), GOLD)
    c.tone(c.mask(lambda p: p.ellipse(tx + 10, ty, 70, 22)) * (c.noise("coins", 60, 20, 1) - 0.5), 0.5)
    c.put(c.mask(box(tx - 24, ty - 50, tx + 30, ty - 12)), (120, 70, 40))
    c.put(c.mask(lambda p: p.poly([(tx - 26, ty - 50), (tx + 32, ty - 50), (tx + 40, ty - 82), (tx - 18, ty - 82)])), (140, 84, 48))
    c.put(c.mask(lambda p: (p.rect(tx - 24, ty - 52, tx + 30, ty - 48), p.rect(tx - 2, ty - 50, tx + 6, ty - 12))), (60, 60, 64))
    c.put(c.mask(box(tx - 22, ty - 50, tx + 28, ty - 44)), GOLD)
    c.light(c.mask(lambda p: p.ellipse(tx + 4, ty - 46, 40, 14), blur=8), GOLD, 0.5)
    rng = c.rand("loose coins")
    c.put(c.mask(lambda p: [p.ellipse(rng.uniform(tx - 70, tx + 90), ty - rng.uniform(1, 5), 3, 1.6) for _ in range(30)]), GOLD)
    # Barrels and rope by the hub door, crates by the ledge.
    for bxp in (150, 172):
        barrel(c, bxp, FLOOR, 18, 26)
    coil(c, 200, FLOOR, 11)
    crate(c, 250, FLOOR - 34, 290, FLOOR, mark=(150, 60, 50))
    crate(c, 286, FLOOR - 28, 316, FLOOR)
    # The parrot's perch (it stands on the boards at x 1040..1104).
    px = 1072
    c.put(c.mask(lambda p: (p.rect(px - 2, FLOOR - 100, px + 2, FLOOR), p.rect(px - 22, FLOOR - 4, px + 22, FLOOR), p.rect(px - 26, FLOOR - 102, px + 26, FLOOR - 98))), TIMBER)
    c.put(c.mask(lambda p: p.ellipse(px + 22, FLOOR - 92, 5, 4)), (230, 200, 90))


PIECES: Dict[str, Piece] = {
    "cove_cave": Piece((0, 0, W, FLOOR), cove_cave),
    "cove_ledges": Piece((300, 0, 940, FLOOR), cove_ledges),
    "cove_doorways": Piece((40, FLOOR - 170, 1260, FLOOR), cove_doorways),
    "cove_dressing": Piece((120, FLOOR - 110, 1130, FLOOR), cove_dressing),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
