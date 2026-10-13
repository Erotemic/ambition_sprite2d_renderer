#!/usr/bin/env python3
"""Draw the Imperfect Cellular Automaton's two SVGs (see README.md).

    python imperfect_cellular_automaton_art.py            # writes both SVGs
    python imperfect_cellular_automaton_art.py OUT_DIR    # writes them there

THE DESIGN ELEMENTS (a rework must keep these, or say why not):

* She is a parody of Imperfect Cell: hunched, a crown of two prongs open in a
  V, a tail in segments with a sting carried over the head, claws, and feet
  with two toes and a spur. The reference is overt and it is not a copy: she
  has no beak, no beetle wings and no ribbed cheeks.
* She is two halves. One half keeps the rule: green, a clean lattice of lime
  cells. The other half is a fault that grows: purple, pink cells that are
  out of line, a prong whose tip is out of place. The halves are her left
  and her right, so the two views differ. ``CLEAN_NEAR`` is the view with
  the green half toward the camera, and ``FAULT_NEAR`` is the other side.
* Her chest is a cream plate with the grid of an automaton on it. The grid
  runs: the game shows a new state each frame (the ``grid_<n>`` parts), and
  the rule fails on the fault side.
* Her face is a black visor with two eyes that do not match (a lime bar on
  the clean side, pink and violet cells on the fault side) and a grin with
  teeth of cells.
* Her wings are two panes of the grid. A glider is in the clean pane. The
  fault pane has cells missing.
* All of it is flat polygons with one ink line, as the Perfect Cellular
  Automaton is drawn.

Both SVGs are drawn facing right, as every rig is. The game draws the
``FAULT_NEAR`` view as its mirror image, when she faces left.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import svgkit as K

Point = Tuple[float, float]

OUT = Path(__file__).resolve().parents[2] / "ambition_sprite2d_renderer" / "data" / "characters" / "imperfect_cellular_automaton"
#: The design is drawn about its own origin and moved by this onto the page.
OFFSET = (40.0, 70.0)
SIZE = (600, 690)
#: Where she stands on the page: the rig's root (``build_imperfect_cellular_automaton_rig.py``).
#: It is ahead of her hips, because she leans.
CENTER_X, GROUND_Y = 266.0 + OFFSET[0], 520.0 + OFFSET[1]

INK = "#0b1517"
GREEN, GREEN_D, LIME = "#137a5a", "#0d3b31", "#b6f34a"
PURPLE, PURPLE_D, PINK, VIOLET = "#7046a8", "#352253", "#f05cb8", "#b478f0"
CREAM, TAN, BLACK, CYAN = "#efe8cf", "#c9c1a6", "#17262a", "#4fd0e6"

CLEAN = dict(main=GREEN, deep=GREEN_D, cell=LIME, fault=False)
FAULT = dict(main=PURPLE, deep=PURPLE_D, cell=PINK, fault=True)

#: The two views: ``(near half, far half)``.
CLEAN_NEAR = ("clean", CLEAN, FAULT)
FAULT_NEAR = ("fault", FAULT, CLEAN)

LEAN = 14.0
HEAD_TILT = 6.0
HEAD_SCALE = 1.42
PELVIS: Point = (238.0, 352.0)
CHEST: Point = (263.6, 249.1)
HEAD_CENTRE: Point = (323.0, 158.0)
TAIL: List[Point] = [(206, 346), (158, 366), (104, 340), (72, 278), (74, 206), (102, 144), (150, 100), (206, 84)]
TAIL_W = [22, 21, 19, 17, 15, 13, 11, 9]
WING_ANGLE = {"near": 182.0, "far": 222.0}
GRID_COLS, GRID_ROWS, GRID_STATES = 5, 7, 8


def rot(p: Point, deg: float) -> Point:
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def place(pts: Sequence[Point], at: Point, deg: float = 0.0, scale: float = 1.0) -> List[Point]:
    return [(at[0] + rot((x * scale, y * scale), deg)[0], at[1] + rot((x * scale, y * scale), deg)[1]) for x, y in pts]


def body(p: Point) -> Point:
    """A point of the torso, given in the frame of the chest."""
    return place([p], CHEST, LEAN)[0]


def head(pts: Sequence[Point]) -> List[Point]:
    return place(pts, HEAD_CENTRE, HEAD_TILT, HEAD_SCALE)


def angle(a: Point, b: Point) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def poly(pts: Sequence[Point], fill: str, sw: float = 2.2) -> str:
    d = " ".join(K.pt(K.P(x, y)) for x, y in pts)
    stroke = f' stroke="{INK}" stroke-width="{K.f(sw)}" stroke-linejoin="round"' if sw else ""
    return f'<polygon points="{d}" fill="{fill}"{stroke} />'


def cell(at: Point, size: float, deg: float, fill: str, sw: float = 0.9) -> str:
    h = size / 2
    return poly(place([(-h, -h), (h, -h), (h, h), (-h, h)], at, deg), fill, sw)


def limb(a: Point, b: Point, wa: float, wb: float, fill: str, cap: float = 0.45) -> str:
    """A bone as a tapered plate with a facet at each end."""
    deg = angle(a, b)
    d = math.hypot(b[0] - a[0], b[1] - a[1])
    return poly(place([(0, wa), (d, wb), (d + wb * cap, 0), (d, -wb), (0, -wa), (-wa * cap, 0)], a, deg), fill)


def hexagon(at: Point, r: float, fill: str) -> str:
    return poly([(at[0] + r * math.cos(math.radians(k * 60 + 15)), at[1] + r * math.sin(math.radians(k * 60 + 15))) for k in range(6)], fill)


def cells(a: Point, b: Point, layout: Sequence[Tuple[float, float]], size: float, side: dict, on: str) -> List[str]:
    """Cells along the bone a->b, ``(part of the way, across)`` each. On the
    clean half they are in line; on the fault half each is a little turned and
    one in three is the fault's pink."""
    deg = angle(a, b)
    d = math.hypot(b[0] - a[0], b[1] - a[1])
    out = []
    for i, (t, across) in enumerate(layout):
        turn = (11.0 * math.sin(2.1 * i + 1.3)) if side["fault"] else 0.0
        fill = side[on]
        if side["fault"] and i % 3 == 1:
            fill = PINK if fill != PINK else VIOLET
        out.append(cell(place([(d * t, across)], a, deg)[0], size, deg + turn, fill))
    return out


# ---- the parts ----------------------------------------------------------------------


def draw_tail() -> None:
    for i in range(len(TAIL) - 1):
        a, b = TAIL[i], TAIL[i + 1]
        side = CLEAN if i < 3 else FAULT
        items = [limb(a, b, TAIL_W[i], TAIL_W[i + 1], side["main"] if i % 2 == 0 else side["deep"], cap=0.5)]
        items += cells(a, b, [(0.3, -TAIL_W[i] * 0.35), (0.7, TAIL_W[i] * 0.3)], 5.5, side, "cell" if i % 2 else "deep")
        if i == len(TAIL) - 2:
            deg = angle(a, b)
            items.append(poly(place([(-4, -12), (14, -10), (26, 0), (14, 10), (-4, 12)], b, deg), PURPLE_D))
            items.append(poly(place([(20, -6), (86, 8), (20, 7)], b, deg + 12), PINK))
        n = i + 1
        K.part(f"tail-{n}", f"Tail {n}", f"tail_{n}", f"tail_{n}", 2 + 0.1 * n, items)


def wing_root() -> Point:
    return body((-40, -34))


def draw_wing(which: str, side: dict) -> None:
    """A pane of the grid. A glider lives in the clean pane; the fault pane
    has cells missing and the rest are out of line."""
    deg0 = WING_ANGLE[which]
    cs, cols, rows = 19.0, 7, 3
    origin = place([(14, -rows * cs / 2)], wing_root(), deg0)[0]
    if side["fault"]:
        live, gone = {(1, 1), (2, 0), (4, 2), (5, 1), (6, 1)}, {(3, 0), (5, 2), (4, 0)}
    else:
        live, gone = {(2, 0), (3, 1), (1, 2), (2, 2), (3, 2)}, set()
    items = []
    for cx in range(cols):
        for cy in range(rows):
            # the pane is narrow at its tip
            if (cx, cy) in gone or (cx >= cols - 2 and cy != 1):
                continue
            at = place([(cx * cs + cs / 2, cy * cs + cs / 2)], origin, deg0)[0]
            jit = (5 * math.sin(cx * 2.3 + cy)) if side["fault"] else 0.0
            fill = side["cell"] if (cx, cy) in live else side["deep"]
            items.append(cell((at[0] + jit * 0.4, at[1] + jit * 0.3), cs - 1.5, deg0 + jit * 2, fill, sw=1.3))
    K.part(f"wing-{which}", f"Wing - {which}", f"wing_{which}", f"wing_{which}", 4 if which == "far" else 5, items)


LEGS: Dict[str, Tuple[Point, Point, Point, Point]] = {
    "near": ((226, 358), (270, 430), (232, 500), (294, 520)),
    "far": ((254, 356), (312, 420), (288, 500), (346, 516)),
}
ARMS: Dict[str, Tuple[Point, Point, Point]] = {
    "near": ((224, 202), (204, 290), (236, 356)),
    "far": ((317, 225), (332, 306), (372, 362)),
}
HAND_LENGTH = 52.0


def draw_leg(which: str, side: dict, z: float) -> None:
    hip, knee, ankle, toe = LEGS[which]
    upper = [limb(hip, knee, 25, 18, side["main"])] + cells(hip, knee, [(0.3, -8), (0.55, 7), (0.78, -3)], 6.5, side, "deep")
    K.part(f"{which}-leg-u", f"Thigh - {which}", f"{which}_leg_u", f"{which}_leg_u", z, upper)
    d = math.hypot(ankle[0] - knee[0], ankle[1] - knee[1])
    deg = angle(knee, ankle)
    lower = [
        limb(knee, ankle, 16, 12, BLACK),
        poly(place([(d * 0.16, -20), (d * 0.9, -15), (d * 1.0, 0), (d * 0.9, 11), (d * 0.16, 15)], knee, deg), side["deep"]),
    ] + cells(knee, ankle, [(0.38, -5), (0.66, 3)], 6.5, side, "cell") + [hexagon(knee, 13, side["cell"])]
    K.part(f"{which}-leg-l", f"Shin - {which}", f"{which}_leg_l", f"{which}_leg_l", z + 1, lower)
    fdeg = angle(ankle, toe)
    fl = math.hypot(toe[0] - ankle[0], toe[1] - ankle[1])
    foot = [
        poly(place([(-10, -13), (fl * 0.45, -14), (fl * 0.62, 2), (fl * 0.4, 12), (-12, 11), (-30, 15), (-15, 0)], ankle, fdeg), BLACK),
        poly(place([(fl * 0.42, -13), (fl * 1.08, -2), (fl * 0.55, 2)], ankle, fdeg), CREAM),
        poly(place([(fl * 0.36, 1), (fl * 1.0, 13), (fl * 0.36, 12)], ankle, fdeg), CREAM),
    ]
    K.part(f"{which}-leg-foot", f"Foot - {which}", f"{which}_leg_foot", f"{which}_leg_foot", z + 2, foot)


def draw_arm(which: str, side: dict, z: float) -> None:
    sh, el, wr = ARMS[which]
    upper = [limb(sh, el, 17, 13, side["deep"])] + cells(sh, el, [(0.4, -4), (0.7, 4)], 6.0, side, "cell")
    if which == "near":
        # the shoulder plate; the bolts of the perfect one are cells here
        upper.append(poly(place([(-22, -10), (-6, -22), (18, -18), (26, -2), (18, 16), (-10, 18), (-24, 6)], (sh[0] + 2, sh[1] - 6), LEAN), side["main"]))
        for i, (x, y) in enumerate([(-10, -6), (6, -8), (-2, 7)]):
            turn = (13.0 * math.sin(2.4 * i + 0.6)) if side["fault"] else 0.0
            upper.append(cell(place([(x, y)], (sh[0] + 2, sh[1] - 6), LEAN)[0], 7.5, LEAN + turn, side["cell"]))
    K.part(f"{which}-arm-u", f"Upper arm - {which}", f"{which}_arm_u", f"{which}_arm_u", z, upper)
    lower = [limb(el, wr, 17, 12, side["main"])] + cells(el, wr, [(0.3, 5), (0.6, -4), (0.85, 3)], 5.5, side, "deep") + [hexagon(el, 11, side["cell"])]
    K.part(f"{which}-arm-l", f"Forearm - {which}", f"{which}_arm_l", f"{which}_arm_l", z + 1, lower)
    deg = angle(el, wr)
    hand = [
        poly(place([(-6, -12), (7, -13), (7, 13), (-6, 12)], wr, deg), BLACK),
        poly(place([(7, -12), (24, -14), (29, 0), (24, 13), (7, 12)], wr, deg), CREAM),
    ]
    for off, turn, ln in [(-10, -24, 28), (0, 4, 33), (10, 30, 27)]:
        base = place([(24, off)], wr, deg)[0]
        hand.append(poly(place([(0, -5), (ln, 0), (0, 5)], base, deg + turn), CREAM))
        hand.append(poly(place([(ln * 0.55, -2.4), (ln, 0), (ln * 0.55, 2.4)], base, deg + turn), side["cell"], sw=1.0))
    K.part(f"{which}-arm-hand", f"Hand - {which}", f"{which}_arm_hand", f"{which}_arm_hand", z + 2, hand)


def grid_at(cx: int, cy: int, fault: bool) -> Tuple[Point, float]:
    """Where a cell of the chest grid is, and how it is turned. A cell of the
    fault half is out of line."""
    jit = (4 * math.sin(cx * 1.9 + cy * 2.7)) if fault else 0.0
    return body((-13 + cx * 12 + jit * 0.5, -28 + cy * 12.5 + jit * 0.6)), LEAN + jit * 3


def fault_column(cx: int, near: dict) -> bool:
    """The fault half of the grid is the two columns on the fault's side."""
    return cx <= 1 if near["fault"] else cx >= 3


def draw_torso(near: dict, far: dict) -> None:
    K.part("pelvis", "Pelvis", "pelvis", "pelvis", 20,
           [poly(place([(-30, -12), (28, -14), (36, 6), (14, 28), (-22, 26), (-36, 6)], PELVIS, LEAN * 0.4), BLACK)])
    items = [
        poly([body(p) for p in [(-28, 4), (32, 0), (34, 62), (22, 98), (-22, 100), (-34, 60)]], BLACK),
        poly([body(p) for p in [(-52, -44), (-12, -60), (14, -58), (10, 20), (-38, 14), (-60, -12)]], near["main"]),
        poly([body(p) for p in [(14, -58), (40, -54), (60, -26), (54, 6), (24, 22), (10, 20)]], far["main"]),
    ]
    items += cells(body((-48, -32)), body((-44, 6)), [(0.1, -4), (0.55, -7), (0.95, -3)], 7.0, near, "deep")
    items.append(poly([body(p) for p in [(-14, -40), (40, -38), (46, -6), (34, 56), (26, 90), (-14, 92), (-24, 54), (-26, -8)]], CREAM))
    # the empty places of the grid
    for cy in range(GRID_ROWS):
        for cx in range(GRID_COLS):
            at, deg = grid_at(cx, cy, fault_column(cx, near))
            items.append(cell(at, 8.5, deg, TAN, sw=0.5))
    # the neck
    items.append(limb(body((14, -50)), (HEAD_CENTRE[0] - 14, HEAD_CENTRE[1] + 14), 15, 14, BLACK))
    K.part("torso", "Torso", "torso", "torso", 22, items)


def grid_states() -> List[List[List[int]]]:
    """The states the chest grid shows, in turn: Conway's rule on a board
    that wraps, and at each step one cell that does not obey it."""
    board = [[0] * GRID_COLS for _ in range(GRID_ROWS)]
    for cx, cy in [(1, 0), (2, 1), (0, 2), (1, 2), (2, 2), (3, 4), (4, 4), (3, 5), (0, 5), (4, 6)]:
        board[cy][cx] = 1
    states = []
    for step in range(GRID_STATES):
        states.append([row[:] for row in board])
        nxt = [[0] * GRID_COLS for _ in range(GRID_ROWS)]
        for cy in range(GRID_ROWS):
            for cx in range(GRID_COLS):
                n = sum(board[(cy + dy) % GRID_ROWS][(cx + dx) % GRID_COLS]
                        for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dx, dy) != (0, 0))
                nxt[cy][cx] = 1 if n == 3 or (board[cy][cx] and n == 2) else 0
        # the fault: one cell of the fault half is flipped
        fx, fy = 3 + step % 2, (step * 3 + 1) % GRID_ROWS
        nxt[fy][fx] ^= 1
        if sum(map(sum, nxt)) < 6:  # the board must not die: seed it again
            for cx, cy in [(1, 1), (2, 2), (0, 3), (1, 3), (2, 3)]:
                nxt[cy][cx] = 1
        board = nxt
    return states


def draw_grid(near: dict) -> None:
    """The live cells of each state, as its own part: the rig shows one."""
    for n, board in enumerate(grid_states()):
        items = []
        for cy in range(GRID_ROWS):
            for cx in range(GRID_COLS):
                # the board is the board of the clean view; the fault view sees it from the other side
                bx = cx if not near["fault"] else GRID_COLS - 1 - cx
                if not board[cy][bx]:
                    continue
                fault = fault_column(cx, near)
                at, deg = grid_at(cx, cy, fault)
                if fault:
                    fill = PINK if (bx + cy) % 2 else PURPLE
                else:
                    fill = CYAN if (bx + 2 * cy) % 5 == 0 else LIME
                items.append(cell(at, 10.0 if fault else 8.5, deg, fill, sw=0.8))
        K.part(f"grid-{n}", f"Grid state {n}", f"grid_{n}", "torso", 23 + 0.01 * n, items,
               extra=f' data-rig-opacity="grid_{n}"')


#: A prong of the crown at the back of the skull and at the front of it:
#: ``(the straight prong, the fault's shaft, the fault's tip, cells that drift off it)``.
PRONGS = {
    "back": (
        [(-32, -24), (-6, -38), (-44, -100), (-58, -86)],
        [(-32, -24), (-6, -38), (-32, -78), (-48, -70)],
        [(-50, -76), (-34, -84), (-40, -108), (-60, -98)],
        [(-70, -112, 6.0), (-72, -62, 4.5)],
    ),
    "front": (
        [(8, -36), (30, -28), (62, -92), (44, -86)],
        [(8, -36), (30, -28), (54, -70), (38, -72)],
        [(41, -78), (57, -76), (62, -100), (47, -97)],
        [(72, -108, 6.0), (70, -58, 4.5)],
    ),
}


def prong(where: str, side: dict) -> List[str]:
    straight, shaft, tip, drift = PRONGS[where]
    if not side["fault"]:
        a, b = (straight[1], straight[2]) if where == "back" else (straight[0], straight[3])
        mid = lambda t, s: ((a[0] + (b[0] - a[0]) * t) * 1.0 + s, a[1] + (b[1] - a[1]) * t)  # noqa: E731
        return [poly(head(straight), side["main"])] + [
            cell(head([mid(0.3, -8 if where == "back" else 8)])[0], 7.0, HEAD_TILT + angle(a, b), LIME),
            cell(head([mid(0.62, -9 if where == "back" else 9)])[0], 7.0, HEAD_TILT + angle(a, b), LIME),
        ]
    return [poly(head(shaft), side["main"]), poly(head(tip), PINK, sw=1.8)] + [
        cell(head([(x, y)])[0], s, 14.0, PINK if i == 0 else side["main"]) for i, (x, y, s) in enumerate(drift)
    ]


def draw_head(near: dict, far: dict) -> None:
    items = prong("front", far)
    items.append(poly(head([(-38, -6), (-34, -28), (-12, -42), (4, -42), (2, 16), (-22, 16)]), near["deep"]))
    items.append(poly(head([(4, -42), (20, -40), (36, -24), (38, -2), (26, 12), (2, 16)]), far["deep"]))
    items += prong("back", near)
    # the cells of the brow
    for i, (x, y) in enumerate([(-25, -19), (-14, -27), (-26, -6)]):
        turn = (14.0 * math.sin(1.7 * i + 0.4)) if near["fault"] else 0.0
        fill = (PINK if i == 1 else near["main"]) if near["fault"] else (LIME if i == 2 else near["main"])
        items.append(cell(head([(x, y)])[0], 11.0, HEAD_TILT + turn, fill, sw=0.8))
    # the face plate, the visor, and the two eyes that do not match
    items.append(poly(head([(-8, -22), (34, -22), (42, -2), (36, 14), (-2, 16), (-12, -2)]), CREAM))
    items.append(poly(head([(-4, -17), (33, -17), (38, -3), (0, -1)]), BLACK, sw=1.4))
    for where, side in (("back", near), ("front", far)):
        if not side["fault"]:
            bar = [(2, -14), (15, -14), (16, -5), (3, -4.5)] if where == "back" else [(19, -14.5), (32, -14.5), (34, -4.5), (20, -4)]
            items.append(poly(head(bar), LIME, sw=0))
        else:
            x0 = 3.0 if where == "back" else 20.0
            items.append(poly(head([(x0, -15), (x0 + 10, -15), (x0 + 11, -8), (x0 + 1, -8)]), PINK, sw=0))
            items.append(poly(head([(x0 + 5, -10), (x0 + 14, -9), (x0 + 15, -2), (x0 + 6, -3)]), VIOLET, sw=0))
    # the grin: teeth of cells; the teeth of the fault half are out of line
    items.append(poly(head([(2, 10), (38, 8), (40, 22), (30, 31), (8, 31), (0, 22)]), BLACK))
    for x, y in [(7, 15), (15, 15), (23, 15), (31, 15), (11, 24), (19, 24), (27, 24)]:
        side = near if x < 19 else far
        if side["fault"]:
            turn, dy = 16.0 * math.sin(x * 0.9), 1.6 * math.sin(x * 1.7)
            fill = PINK if x in (7, 31) else CREAM
        else:
            turn, dy, fill = 0.0, 0.0, (LIME if (x, y) in ((11, 24), (27, 24)) else CREAM)
        items.append(cell(head([(x, y + dy)])[0], 9.5, HEAD_TILT + turn, fill, sw=0.7))
    K.part("head", "Head", "head", "head", 30, items)


def joints() -> Dict[str, Point]:
    J: Dict[str, Point] = {
        "pelvis": PELVIS,
        "torso": (242.0, 330.0),
        "head": (HEAD_CENTRE[0] - 17, HEAD_CENTRE[1] + 18),
        "wing_root": wing_root(),
    }
    for which, (sh, el, wr) in ARMS.items():
        tip = place([(HAND_LENGTH, 0)], wr, angle(el, wr))[0]
        J.update({f"{which}_shoulder": sh, f"{which}_elbow": el, f"{which}_wrist": wr, f"{which}_hand_tip": tip})
    for which, (hip, knee, ankle, toe) in LEGS.items():
        J.update({f"{which}_hip": hip, f"{which}_knee": knee, f"{which}_ankle": ankle, f"{which}_toe": toe})
    for i, p in enumerate(TAIL):
        J[f"tail_{i}"] = p
    for which, deg in WING_ANGLE.items():
        J[f"wing_{which}_tip"] = place([(150, 0)], wing_root(), deg)[0]
    return J


def draw(view) -> str:
    name, near, far = view
    K.configure(dx=OFFSET[0], dy=OFFSET[1], ink=INK, ow=1.1, colors={})
    draw_tail()
    draw_wing("far", far)
    draw_wing("near", near)
    draw_leg("far", far, 6)
    draw_arm("far", far, 9)
    draw_torso(near, far)
    draw_grid(near)
    draw_head(near, far)
    draw_leg("near", near, 40)
    draw_arm("near", near, 60)
    half = "green (clean)" if name == "clean" else "purple (fault)"
    comment = [
        f"  <!-- The Imperfect Cellular Automaton, her {half} half toward the camera, facing right.",
        "       The design elements are listed in scripts/svg_art/imperfect_cellular_automaton_art.py.",
        "       Each part is a layer with a data-rig-part name; the rigs in",
        "       targets/characters/rigged/imperfect_cellular_automaton/ turn the parts about their joints.",
        "       The grid_<n> layers lie on each other: the rig shows one of them in each frame.",
        "       The hidden Rig Joints layer marks every joint the skeleton is built on. -->",
    ]
    label = "ICA - Clean Side" if name == "clean" else "ICA - Fault Side"
    return K.document(size=SIZE, design=f"imperfect-cellular-automaton-{name}-side-v1", layer_id=f"ica-{name}-side",
                      label=label, comment=comment, joints=K.joints_layer(joints()))


FILES = {
    "imperfect_cellular_automaton.svg": CLEAN_NEAR,
    "imperfect_cellular_automaton_fault_side.svg": FAULT_NEAR,
}


def main(argv: List[str]) -> None:
    out = Path(argv[1]) if len(argv) > 1 else OUT
    out.mkdir(parents=True, exist_ok=True)
    for file, view in FILES.items():
        text = draw(view)
        tmp = out / (file + ".tmp")
        tmp.write_text(text)
        tmp.replace(out / file)
        print(out / file)


if __name__ == "__main__":
    main(sys.argv)
