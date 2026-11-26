"""Two residents of the Automaton dimension (gate address CELLS,
`docs/planning/game/automaton-dimension.md`).

**Neighbour Moore**, of the Life field: an automaton of dark cubes whose
chest is a three-by-three grid, the Moore neighbourhood. The middle cell is
amber: that is him. The eight round it are his neighbours, and they live
and die as he breathes (a blinker steps through them at rest). His head is a
cube with a visor and two cyan eyes; an antenna with a cell on it.

**The Head**, of the Tape Room: the read/write head of the Busy Beaver's
machine. Its lens reads the cell and its stamp writes it. Five lamps on
the top of the carriage show the current state. Violet enamel and lime
indicators match the Busy Beaver's colours.

Rows: ``idle``, ``talk``, ``hit`` and ``death``. The Head reads and stamps tape
while it talks. Its indicator lights go out when it stops.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _picture_palace_kit as M

ROWS: List[Tuple[str, int, int]] = [("idle", 8, 150), ("talk", 6, 110), ("hit", 3, 90), ("death", 8, 160)]
LOOPS = {"idle", "talk"}

# Neighbour Moore.
CUBE = (40, 40, 82, 255)
CUBE_LIGHT = (74, 76, 128, 255)
CUBE_DARK = (22, 22, 48, 255)
CELL = (120, 220, 255, 255)
CELL_OFF = (34, 52, 96, 255)
AMBER = (255, 184, 70, 255)
VISOR = (14, 16, 34, 255)

# The Head.
BODY = (111, 67, 153, 255)
BODY_LIGHT = (176, 126, 209, 255)
BODY_DARK = (61, 37, 99, 255)
TRIM = (219, 164, 96, 255)
ENAMEL = (240, 224, 178, 255)
LIME = (197, 247, 96, 255)
LIME_OFF = (69, 86, 66, 255)
LENS = (137, 232, 215, 255)
STEEL = (101, 103, 134, 255)
INK = (30, 21, 45, 255)


# ---------------------------------------------------------------------------
# Neighbour Moore
# ---------------------------------------------------------------------------

MOORE_FRAME = (96, 128)
#: The eight neighbours, clockwise from the top left; the blinker through
#: them at rest (a vertical then a horizontal bar of three through the middle).
NEIGHBOURS = ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2), (0, 1))
BLINKER = ({(1, 0), (1, 2)}, {(0, 1), (2, 1)})


def _moore(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in LOOPS)
    cyc = math.tau * t
    f = K.Frame(MOORE_FRAME)
    foot = 124.0
    cx = 48.0
    bob, tilt, lights, sit = 0.0, 0.0, 1.0, 0.0
    lit = BLINKER[(i // 2) % 2]
    if anim == "idle":
        bob = 0.8 * math.sin(cyc)
    elif anim == "talk":
        bob = 0.6 * math.sin(cyc * 2.0)
        lit = set(NEIGHBOURS[k] for k in range(8) if (k + i) % 3 == 0)
    elif anim == "hit":
        tilt = -8.0
        lit = {NEIGHBOURS[(i * 3) % 8]}
    elif anim == "death":
        sit = min(1.0, t * 1.6)
        tilt = 8.0 * sit
        lights = max(0.0, 1.0 - t * 1.3)
        lit = set(NEIGHBOURS[: max(0, int(round(8 * (1.0 - t * 1.4))))]) & set(BLINKER[0] | BLINKER[1])
    top = 36.0 + bob + 20.0 * sit
    pivot = (cx, top + 44.0)

    def turn(pts):
        return K.turn(pts, pivot[0], pivot[1], tilt)

    # Legs: two stacks of cubes.
    for dx in (-10.0, 10.0):
        for k in range(3):
            y0 = top + 58.0 + k * ((foot - top - 58.0) / 3.0)
            y1 = y0 + (foot - top - 58.0) / 3.0 - 1.5
            x0 = cx + dx - 6.0 + (6.0 * sit * k if dx > 0 else 0.0)
            f.poly([(x0, y0), (x0 + 12.0, y0), (x0 + 12.0, y1), (x0, y1)], CUBE if k % 2 else CUBE_LIGHT)
    # Arms: a cube at the shoulder, a thin rod, a cube hand.
    lift = 8.0 * math.sin(cyc * 2.0) if anim == "talk" else 0.0
    for side in (-1.0, 1.0):
        sh = turn([(cx + side * 22.0, top + 26.0)])[0]
        hand = (sh[0] + side * 6.0, sh[1] + 26.0 - (lift if side > 0 else 0.0))
        f.limb([sh, hand], 3.0, CUBE_DARK)
        f.poly([(sh[0] - 4.0, sh[1] - 4.0), (sh[0] + 4.0, sh[1] - 4.0), (sh[0] + 4.0, sh[1] + 4.0), (sh[0] - 4.0, sh[1] + 4.0)], CUBE_LIGHT)
        f.poly([(hand[0] - 4.0, hand[1] - 3.0), (hand[0] + 4.0, hand[1] - 3.0), (hand[0] + 4.0, hand[1] + 5.0), (hand[0] - 4.0, hand[1] + 5.0)], CUBE)
    # The chest: the Moore neighbourhood, him in the middle.
    body = [(cx - 19.0, top + 20.0), (cx + 19.0, top + 20.0), (cx + 19.0, top + 58.0), (cx - 19.0, top + 58.0)]
    f.poly(turn(body), CUBE)
    s = 11.0
    for gy in range(3):
        for gx in range(3):
            x0, y0 = cx - 16.5 + gx * s, top + 22.5 + gy * s
            sq = turn([(x0 + 1.0, y0 + 1.0), (x0 + s - 1.0, y0 + 1.0), (x0 + s - 1.0, y0 + s - 1.0), (x0 + 1.0, y0 + s - 1.0)])
            if (gx, gy) == (1, 1):
                colour = AMBER if lights > 0.0 else CELL_OFF
                f.poly(sq, colour, body=False)
                if lights > 0.0:
                    mx, my = sum(p[0] for p in sq) / 4, sum(p[1] for p in sq) / 4
                    f.glow(mx, my, 8.0, K.alpha(AMBER, 0.5 * lights))
            elif (gx, gy) in lit and lights > 0.0:
                f.poly(sq, CELL, body=False)
                mx, my = sum(p[0] for p in sq) / 4, sum(p[1] for p in sq) / 4
                f.glow(mx, my, 6.0, K.alpha(CELL, 0.4 * lights))
            else:
                f.poly(sq, CELL_OFF, body=False)
    # The head: a cube, its visor and eyes, the antenna with a cell.
    hx, hy = turn([(cx, top + 6.0)])[0]
    head = [(hx - 14.0, hy - 13.0), (hx + 14.0, hy - 13.0), (hx + 14.0, hy + 12.0), (hx - 14.0, hy + 12.0)]
    f.poly(head, CUBE_LIGHT)
    f.poly([(hx - 11.0, hy - 5.0), (hx + 13.0, hy - 5.0), (hx + 13.0, hy + 6.0), (hx - 11.0, hy + 6.0)], VISOR, body=False)
    if lights > 0.0:
        h = 2.6 if not (anim == "idle" and i == 5) else 0.6
        for ex in (hx - 3.0, hx + 7.0):
            f.poly([(ex - 2.4, hy - h), (ex + 2.4, hy - h), (ex + 2.4, hy + h), (ex - 2.4, hy + h)], CELL, body=False)
            f.glow(ex, hy, 5.0, K.alpha(CELL, 0.5 * lights))
    f.limb([(hx + 6.0, hy - 13.0), (hx + 9.0, hy - 22.0)], 1.6, CUBE_DARK)
    f.poly([(hx + 6.0, hy - 28.0), (hx + 12.0, hy - 28.0), (hx + 12.0, hy - 22.0), (hx + 6.0, hy - 22.0)], AMBER if lights > 0.0 else CELL_OFF)
    return f.finish(outline=K.shade(CUBE_DARK, 0.6), width=1.4, glow_blur=2.0)


# ---------------------------------------------------------------------------
# The Head
# ---------------------------------------------------------------------------

HEAD_FRAME = (160, 126)
HEAD_GROUND = 116.0
STATE_LETTERS = (
    ("010", "101", "111", "101"),
    ("110", "101", "110", "111"),
    ("011", "100", "100", "011"),
    ("110", "101", "101", "110"),
    ("111", "110", "100", "111"),
)


def _block_letter(f, turn, x, y, pixels, colour, unit):
    for row, line in enumerate(pixels):
        for column, pixel in enumerate(line):
            if pixel == "1":
                a, b = x + column*unit, y + row*unit
                f.poly(turn([(a,b), (a+unit,b), (a+unit,b+unit), (a,b+unit)]), colour, body=False)


def _head(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in LOOPS)
    cyc = math.tau * t
    f = K.Frame(HEAD_FRAME)
    bob, tilt, lights, stamp, state = 0.0, 0.0, 1.0, 0.0, 2
    look = 2.8 * math.sin(cyc)
    if anim == "idle":
        bob = 0.65 * math.sin(cyc)
    elif anim == "talk":
        stamp = max(0.0, math.sin(cyc - .7))**2
        look = -2.6*stamp
        state = 3 if i >= n//2 else 2
    elif anim == "hit":
        tilt = -9.0 * math.sin(math.pi * (i+1)/(n+1))
        lights = .18 if i == 1 else .75
        look = -3.8
    elif anim == "death":
        tilt = 7.0 * min(1.0, t * 2.0)
        bob = 3.0*t
        lights = max(0.0, 1.0 - t * 1.6)
        state = 4

    def turn(pts):
        return K.turn([(x, y+bob) for x, y in pts], 80.0, 97.0, tilt)

    def panel(pts, colour, body=True):
        f.poly(turn(pts), colour, body=body)

    def rim(x, y, rx, ry, colour, body=True):
        f.poly(turn(K.ellipse_points(x,y,rx,ry)), colour, body=body)

    def seam(pts, w, colour):
        f.ink(turn(pts), w, colour)

    # Flanged wheels share the axle. Only the sprung chassis rocks.
    for x, inset, r in [(56,11,7), (106,11,7), (43,8,8), (100,8,8)]:
        y = HEAD_GROUND-inset
        f.ellipse(x,y,r+2,r,INK)
        f.ellipse(x,y,r-1,r-2,STEEL,body=False)
        f.ellipse(x,y,r-4,r-4,TRIM,body=False)
        f.ink([(x-2,y),(x+2,y)],1.3,INK)
    panel([(31,89),(112,88),(126,93),(123,102),(37,104),(30,100)], BODY_DARK)
    panel([(34,97),(109,96),(105,101),(39,102)],TRIM,False)

    # Separate the enamel shell, side plate, and forward lens carriage.
    panel([(29,54),(44,43),(100,43),(115,51),(119,82),(105,96),(35,96),(26,87)], BODY)
    panel([(29,54),(44,43),(100,43),(115,51),(108,61),(35,62),(26,68)], ENAMEL,False)
    panel([(43,45),(100,45),(109,51),(35,55)], (255,242,202,255),False)
    panel([(26,77),(35,86),(109,86),(113,92),(106,97),(35,97),(26,87)],BODY_DARK,False)
    panel([(32,63),(40,61),(92,61),(101,66),(98,86),(40,86),(32,78)],BODY_DARK,False)
    seam([(35,63),(92,63),(98,67)],1.4,TRIM)

    # Behind the glass, the punched tape advances one cell.
    panel([(39,66),(85,66),(90,70),(88,80),(39,80)],INK,False)
    phase_shift = 2.0 * stamp
    for k in range(5):
        x = 42 + 9*k - phase_shift
        if k == 2:
            panel([(x-1,68),(x+7,68),(x+7,78),(x-1,78)],LIME_OFF,False)
        number = ((k + state) % 2) if k != 2 else int(stamp > .48 or state == 3)
        pattern = ("010", "110", "010", "111") if number else ("111", "101", "101", "111")
        _block_letter(f, turn, x, 69, pattern, K.shade(LIME if k == 2 else ENAMEL, .38+.62*lights), 1.8)
    for x, y in [(37,60),(38,87),(92,62),(96,85)]:
        rim(x,y,1.5,1.5,TRIM,False)
        seam([(x-.8,y),(x+.8,y)],.65,INK)

    # Five labelled cells. One recess glows to show the current state.
    panel([(36,46),(44,33),(99,33),(106,44),(101,53),(43,53)],BODY_DARK)
    panel([(39,45),(46,35),(98,35),(103,43),(99,49),(43,49)],STEEL,False)
    for k in range(5):
        x = 45 + k*10.5
        on = lights if k == state else 0.0
        panel([(x,38),(x+8,38),(x+8,47),(x,47)],K.shade(LIME, .28+.72*on),False)
        _block_letter(f, turn, x+1.7, 39.6, STATE_LETTERS[k], INK if on>.55 else ENAMEL, 1.55)
        if on:
            f.glow(*turn([(x+4,42)])[0],8.5,K.alpha(LIME,.44*on))

    # The right-hand lens swivels in a bronze gimbal above the stamp.
    height = 68.0 + .45*look
    panel([(100,53),(117,49),(128,53),(129,83),(119,92),(104,85)],BODY_DARK)
    rim(119, height, 19, 20, INK)
    rim(121, height, 16, 17, TRIM,False)
    rim(122, height, 12.8, 14, INK,False)
    rim(123, height, 11, 12, K.shade(LENS,.28+.45*lights),False)
    rim(124+look, height+1.8*stamp, 6.2, 8.8, K.shade(LENS,.22+.78*lights),False)
    if lights:
        rim(126+look,height+2*stamp,2.8,5,INK,False)
        rim(124+look,height-4,2.4,2.1,ENAMEL,False)
        f.glow(*turn([(124+look,height)])[0],13,K.alpha(LENS,.5*lights))
    seam([(105,57),(109,53),(115,50)],1.8,ENAMEL)

    drop=8*stamp
    panel([(117,84),(131,84),(134,92),(132,96),(118,96),(115,91)],STEEL)
    panel([(120,93),(128,93),(130,101+drop),(120,101+drop)],ENAMEL)
    seam([(123,94),(124,101+drop)],2.0,INK)
    panel([(116,101+drop),(132,101+drop),(134,105+drop),(117,106+drop)],BODY_DARK)
    seam([(118,104+drop),(131,104+drop)],1.5,K.shade(LIME,.28+.72*lights))
    if stamp>.6:
        f.glow(*turn([(125,104+drop)])[0],6,K.alpha(LIME,.55*stamp))
    return f.finish(outline=INK, width=1.55, glow_blur=2.2)


# ---------------------------------------------------------------------------
# Targets
# ---------------------------------------------------------------------------


def _target(name: str, character_id: str, display_name: str, frame_size, frame, body_plan: str, traits, description: str) -> dict:
    metadata = M.machine_metadata(character_id, display_name, body_plan, "Small", traits, description, walks=False)
    metadata["tags"] = ["townsfolk", "automaton", "peaceful", "machine"]

    def render(out_dir: str | Path, **opts) -> List[Path]:
        return K.render_target(name, ROWS, frame, frame_size, metadata, out_dir, **opts)

    return {"render": render, "actor_metadata": metadata}


TARGETS = {
    "automaton_neighbour_moore": _target(
        "automaton_neighbour_moore", "npc_automaton_neighbour_moore", "Neighbour Moore", MOORE_FRAME, _moore, "Biped",
        ["automaton", "cellular", "cubes"],
        "An automaton of dark cubes whose chest is the Moore neighbourhood: three by three cells, the amber middle one "
        "himself, the eight round it his neighbours, lit cyan as they live. A cube head with a visor and two cyan eyes.",
    ),
    "automaton_head": _target(
        "automaton_head", "npc_automaton_head", "The Head", HEAD_FRAME, _head, "Wheeled",
        ["automaton", "turing_machine", "tape"],
        "The read/write head of the Busy Beaver's machine. Its lens scans the tape. Its piston lowers the stamp, and "
        "the tape cell and state lamp change after it writes.",
    ),
}
