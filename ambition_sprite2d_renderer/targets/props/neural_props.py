"""Scenery of the Neural dimension (gate address LATENT): the Cortex, the
living half, and the Weights, the built half
(`docs/planning/game/neural-dimension.md`).

The rooms are written by
`game/ambition_map_assets/ambition_content/generators/neural/make_specs.py`.
Each piece is drawn in its room's coordinates (`_district_props`): where the
room places a walk line (a synapse cap, a branch of the dendrite tree, a
logic gate), the piece draws the light top edge of the thing walked on at
that y. The numbers here are the generator's; change them together.

- The Callosum (floor y 640): the signpost; the synapse caps (y 560, 464)
  and the arch of fibre over them (y 368).
- The Neural Cathedral (floor y 1024): the gallery of memories over its
  ledge (y 544); the dendrite tree and its branches (y 896, 768, 640).
- The Weights (floor y 1024): the logic gates over the spikes (y 928, 848);
  the classifier's board; the racks (y 896, 768) up to the deck (y 640).
- The Echo Chamber (floor y 512): its ring of screens.

Nothing here is writing: the words of the rooms are their signs.

Animations: ``idle``, 1 frame each.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale

PAL = {
    "stone": (200, 120, 170), "stone_light": (255, 190, 220), "trim": (230, 170, 210), "dark": (30, 16, 40),
    "glass_top": (150, 210, 255), "glass_low": (40, 50, 90), "lamp": (255, 220, 170), "wood": (110, 60, 90),
    "leaf": (110, 200, 190), "iron": (40, 44, 70), "brass": (210, 170, 90), "glaze": (230, 180, 120),
}

FLESH = (204, 104, 156)
FLESH_LIGHT = (255, 178, 210)
FLESH_DARK = (110, 44, 96)
DENDRITE = (150, 70, 130)
DENDRITE_DARK = (80, 32, 76)
GLOW = (255, 228, 160)
SPARK = (255, 244, 200)
FLUID = (100, 236, 220)
FRAME = (210, 170, 110)
FRAME_DARK = (120, 86, 52)
WOOD = (120, 80, 56)
WOOD_DARK = (70, 44, 32)
SIGN = (236, 214, 176)
PANEL = (28, 34, 70)
PANEL_LIGHT = (70, 84, 140)
TRACE = (80, 210, 255)
NODE = (170, 245, 255)
VIOLET = (170, 100, 255)
WARN = (255, 76, 96)
SCREEN = (30, 50, 90)
SCREEN_LIGHT = (120, 180, 240)

#: The Callosum.
CALLOSUM_FLOOR = 640
CAPS = ((1240, 560, 128), (1420, 464, 128))
ARCH = (1600, 2000, 368)
#: The Neural Cathedral.
CATHEDRAL_FLOOR = 1024
GALLERY = (600, 1240, 544)
BRANCHES = ((1300, 1500, 896), (1560, 1760, 768), (1300, 1500, 640))
#: The Weights.
WEIGHTS_FLOOR = 1024
GATES = ((1080, 1200, 928, "and"), (1240, 1360, 848, "or"))
#: The Echo Chamber.
ECHO_FLOOR = 512


# ---------------------------------------------------------------------------
# Parts
# ---------------------------------------------------------------------------


def glow_bulb(c, x, y, r, colour=GLOW, strength=0.6):
    c.light(c.mask(lambda p: p.ellipse(x, y, r * 3.0, r * 3.0), blur=r * 1.5), colour, strength * 0.5)
    c.put(c.mask(lambda p: p.ellipse(x, y, r, r)), mix(colour, (255, 255, 255), 0.4))


def synapse_cap(c, x0, x1, top, stem_to):
    """A synapse cap: a fleshy cap like a mushroom's whose flat top is the
    walk at `top`, glowing underneath, on a stem down to `stem_to`."""
    cx = (x0 + x1) / 2
    stem = c.mask(lambda p: p.poly([(cx - 9, top + 14), (cx + 9, top + 14), (cx + 6, stem_to), (cx - 6, stem_to)]))
    c.put(stem, DENDRITE)
    c.tone(stem * np.clip((c.x - cx) / 9, -1, 1), -0.25)
    cap = c.mask(lambda p: (p.ellipse(cx, top + 4, (x1 - x0) / 2 + 6, 14), p.rect(x0 - 4, top, x1 + 4, top + 6)))
    c.put(cap, FLESH)
    c.put(c.mask(box(x0 - 2, top, x1 + 2, top + 2.5)), FLESH_LIGHT)
    c.light(c.mask(lambda p: p.ellipse(cx, top + 16, (x1 - x0) / 2, 7), blur=4), GLOW, 0.7)
    for k in range(5):
        dx = (k - 2) * (x1 - x0) / 6
        c.put(c.mask(lambda p: p.ellipse(cx + dx, top + 15, 3, 4)), GLOW, 0.8)


def branch(c, pts, w, colour=DENDRITE):
    m = c.mask(lambda p: p.line(pts, w))
    c.put(m, colour)
    c.light(m * c.mask(lambda p: p.line([(x - w * 0.25, y - w * 0.25) for x, y in pts], w * 0.35), blur=1), FLESH_LIGHT, 0.35)
    return m


def picture(c, x0, y0, x1, y1, scene, tag):
    """A memory in a frame: a little picture of a place, a little faded."""
    c.put(c.mask(box(x0 - 5, y0 - 5, x1 + 5, y1 + 5)), FRAME)
    c.put(c.mask(box(x0 - 5, y1 + 2, x1 + 5, y1 + 5)), FRAME_DARK)
    sky = c.mask(box(x0, y0, x1, y1))
    c.paint(sky, c.ramp([(y0, (150, 196, 236)), (y1, (236, 214, 200))]))
    h = y1 - y0
    if scene == "hills":
        c.put(c.mask(lambda p: p.poly([(x0, y1), (x0, y0 + h * 0.6), ((x0 + x1) / 2, y0 + h * 0.4), (x1, y0 + h * 0.65), (x1, y1)])), (110, 170, 110))
        c.put(c.mask(lambda p: p.ellipse(x1 - h * 0.25, y0 + h * 0.25, h * 0.1)), (255, 236, 170))
    elif scene == "house":
        c.put(c.mask(box(x0, y0 + h * 0.75, x1, y1)), (120, 170, 100))
        hx = (x0 + x1) / 2
        c.put(c.mask(box(hx - h * 0.25, y0 + h * 0.45, hx + h * 0.25, y0 + h * 0.78)), (230, 210, 180))
        c.put(c.mask(lambda p: p.poly([(hx - h * 0.32, y0 + h * 0.47), (hx + h * 0.32, y0 + h * 0.47), (hx, y0 + h * 0.22)])), (170, 70, 60))
    elif scene == "sea":
        c.put(c.mask(box(x0, y0 + h * 0.55, x1, y1)), (70, 130, 190))
        c.put(c.mask(lambda p: p.poly([(x0 + h * 0.3, y0 + h * 0.55), (x0 + h * 0.5, y0 + h * 0.2), (x0 + h * 0.55, y0 + h * 0.55)])), (240, 240, 236))
    else:
        c.put(c.mask(box(x0, y0 + h * 0.7, x1, y1)), (150, 120, 90))
        c.put(c.mask(lambda p: p.ellipse((x0 + x1) / 2, y0 + h * 0.5, h * 0.12, h * 0.18)), (90, 70, 60))
    c.tint(sky, (236, 200, 230), 0.25)


# ---------------------------------------------------------------------------
# The Callosum
# ---------------------------------------------------------------------------


def signpost(c, k):
    """The signpost on the Callosum: a post of dendrite with three boards
    (MEMORY west, ATTENTION up, BIASES east: the room's signs), a brain on
    its top, two lamps."""
    g = CALLOSUM_FLOOR
    x = 740
    c.put(c.mask(box(x - 5, 470, x + 5, g)), WOOD)
    c.tone(c.mask(box(x, 470, x + 5, g)), -0.25)
    for y, d in ((500, -1), (540, 0), (580, 1)):
        if d < 0:
            pts = [(x - 70, y), (x + 20, y), (x + 20, y + 26), (x - 70, y + 26), (x - 84, y + 13)]
        elif d > 0:
            pts = [(x - 20, y), (x + 70, y), (x + 84, y + 13), (x + 70, y + 26), (x - 20, y + 26)]
        else:
            pts = [(x - 46, y + 6), (x + 46, y + 6), (x + 46, y + 30), (x - 46, y + 30)]
        board = c.mask(lambda p: p.poly(pts))
        c.put(board, SIGN)
        c.put(c.mask(lambda p: p.line(pts + [pts[0]], 2)), WOOD_DARK)
    brain = c.mask(lambda p: (p.ellipse(x - 8, 462, 16, 12), p.ellipse(x + 8, 462, 16, 12)))
    c.put(brain, FLESH)
    c.put(c.mask(lambda p: [p.line([(x + dx - 6, 458 + dy), (x + dx + 6, 460 + dy)], 1.6) for dx in (-10, 8) for dy in (-4, 2)]), FLESH_DARK)
    for lx in (x - 30, x + 30):
        c.put(c.mask(box(lx - 1.5, 476, lx + 1.5, 500)), WOOD_DARK)
        glow_bulb(c, lx, 474, 4)


def callosum_caps(c, k):
    """The synapse caps that step up off the bridge (y 560, 464), and the
    arch of fibre (y 368) the last one reaches, sparks running along it."""
    g = CALLOSUM_FLOOR
    a0, a1, top = ARCH
    # The arch: a bundle of fibres from the floor, over, and back down.
    for k_ in range(5):
        off = k_ * 3.0
        c.put(c.mask(lambda p: p.line([(a0 - 40, g), (a0 - 10, top + 40 + off), (a0 + 30, top + 6 + off), ((a0 + a1) / 2, top + 2 + off),
                                      (a1 - 30, top + 6 + off), (a1 + 10, top + 40 + off), (a1 + 40, g)], 4)), mix(DENDRITE, FLESH, k_ / 5))
    c.put(c.mask(box(a0, top, a1, top + 3)), FLESH_LIGHT)
    rng = c.rand("arch sparks")
    for _ in range(9):
        glow_bulb(c, rng.uniform(a0 + 20, a1 - 20), top + rng.uniform(5, 14), 2.0, SPARK, 0.8)
    for x0, top_, w in CAPS:
        synapse_cap(c, x0, x0 + w, top_, g)
    # The spark that jumps the gap between the two caps.
    (xa, ya, wa), (xb, yb, wb) = CAPS
    c.light(c.mask(lambda p: p.line([(xa + wa / 2, ya + 16), (xa + wa * 0.7, ya - 20), (xb + 10, yb + 30), (xb + wb / 2, yb + 16)], 2), blur=1), SPARK, 0.9)


# ---------------------------------------------------------------------------
# The Neural Cathedral
# ---------------------------------------------------------------------------


def memory_gallery(c, k):
    """The gallery of memories, its walk at y 544: a balcony of flesh hung
    from the vault on fibres, and on the fibres frames of places, a strip
    of film looping between them."""
    x0, x1, walk = GALLERY
    # The fibres it hangs from, down from the vault.
    fibres = (x0 + 24, x0 + 220, x1 - 220, x1 - 24)
    for n, fx in enumerate(fibres):
        sway = 10 * (1 if n % 2 else -1)
        branch(c, [(fx + sway, 32), (fx - sway * 0.5, 280), (fx, walk)], 7)
    # The balcony: a thick lip of flesh under the walk, a rim of light on it.
    lip = c.mask(lambda p: p.poly([(x0, walk), (x1, walk), (x1 - 12, walk + 18), ((x0 + x1) / 2, walk + 28), (x0 + 12, walk + 18)]))
    c.put(lip, FLESH_DARK)
    c.tone(lip * (c.noise("gallery lip", 12, 4, 3) - 0.5), 0.2)
    c.put(c.mask(box(x0, walk, x1, walk + 3)), FLESH_LIGHT)
    # The frames, each hung on a thread from the fibres' height.
    scenes = ("hills", "house", "sea", "room", "hills", "sea")
    for i, scene in enumerate(scenes):
        fx = x0 + 40 + i * 100
        fy = 340 + (i % 2) * 40
        c.put(c.mask(lambda p: p.line([(fx + 10, fy - 5), (fx + 35, fy - 40), (fx + 60, fy - 5)], 1.5)), FLESH_LIGHT, 0.8)
        c.light(c.mask(lambda p: p.ellipse(fx + 35, fy + 26, 56, 46), blur=12), GLOW, 0.25)
        picture(c, fx, fy, fx + 70, fy + 52, scene, ("memory", i))
    # The film: a strip of frames on a curve across the gallery.
    c.put(c.mask(lambda p: p.line([(x0 + 10, 470), (x0 + 200, 455), (x0 + 400, 480), (x1 - 10, 462)], 18)), (40, 30, 40))
    c.put(c.mask(lambda p: [p.rect(x, 462 + 8 * math.sin(x / 70), x + 14, 472 + 8 * math.sin(x / 70)) for x in np.arange(x0 + 14, x1 - 20, 22)]), (200, 220, 240), 0.7)


def dendrite_tree(c, k):
    """The dendrite tree: a trunk up from the floor, its branches carrying
    the walks (y 896, 768, 640), synapse bulbs at their tips."""
    g = CATHEDRAL_FLOOR
    trunk_x = 1530
    branch(c, [(trunk_x - 20, g), (trunk_x - 10, 900), (trunk_x + 10, 780), (trunk_x - 6, 650), (trunk_x, 600)], 34, DENDRITE_DARK)
    for x0, x1, top in BRANCHES:
        near = x1 if x1 < trunk_x else x0
        branch(c, [(trunk_x, top + 40), ((near + trunk_x) / 2, top + 14), (near, top + 6)], 14)
        walk = c.mask(lambda p: p.poly([(x0, top), (x1, top), (x1 - 8, top + 14), (x0 + 8, top + 14)]))
        c.put(walk, DENDRITE)
        c.put(c.mask(box(x0, top, x1, top + 2.5)), FLESH_LIGHT)
        far = x0 if x1 < trunk_x else x1
        glow_bulb(c, far, top + 6, 5)
    # Roots into the floor.
    for dx in (-60, -30, 25, 55):
        branch(c, [(trunk_x - 10, g - 20), (trunk_x + dx, g)], 10, DENDRITE_DARK)


# ---------------------------------------------------------------------------
# The Weights
# ---------------------------------------------------------------------------


def gate_shape(c, x0, x1, top, kind):
    """A logic gate drawn as its symbol, lying on its back: its flat top is
    the walk. AND is a D; OR is a shield. Inputs run in from the left,
    the output out to the right, lit."""
    cy = top + 26
    w = x1 - x0
    if kind == "and":
        body = c.mask(lambda p: (p.rect(x0, top, x0 + w * 0.55, top + 52), p.ellipse(x0 + w * 0.55, cy, w * 0.45, 26)))
    else:
        body = c.mask(lambda p: p.poly([(x0, top), (x0 + w * 0.5, top), (x1, cy), (x0 + w * 0.5, top + 52), (x0, top + 52), (x0 + w * 0.18, cy)]))
    c.put(body, PANEL)
    c.put(body * c.mask(box(x0, top, x1, top + 3)), TRACE)
    c.light(c.mask(lambda p: p.line([(x0 + 4, top + 4), (x1 - 4, top + 4)], 2), blur=2), TRACE, 0.5)
    edge = body - c.soften(body, 2.0)
    c.put(np.clip(edge * 3, 0, 1), TRACE, 0.8)
    for y in (cy - 12, cy + 12):
        c.put(c.mask(lambda p: p.line([(x0 - 30, y), (x0 + 4, y)], 2)), TRACE, 0.8)
    c.put(c.mask(lambda p: p.line([(x1 - 2, cy), (x1 + 30, cy)], 2)), NODE)
    glow_bulb(c, x1 + 30, cy, 3, NODE, 0.6)


def logic_gates(c, k):
    for x0, x1, top, kind in GATES:
        gate_shape(c, x0, x1, top, kind)


def red_herring_board(c, k):
    """The classifier's board: a screen with a red rabbit on it, sure of
    itself (the words are the room's sign), and a strip of three cats and a
    blank under it."""
    x0, y0, x1, y1 = 1560, 600, 1900, 760
    c.put(c.mask(box(x0 - 8, y0 - 8, x1 + 8, y1 + 8)), PANEL_LIGHT)
    scr = c.mask(box(x0, y0, x1, y1))
    c.put(scr, (40, 12, 22))
    c.put(scr * (0.5 + 0.5 * np.sin(c.y * 1.4)), (60, 16, 30), 0.4)
    # The rabbit, leaping, in red light.
    rx, ry = 1730, 690
    rabbit = c.mask(lambda p: (p.ellipse(rx, ry, 40, 18), p.ellipse(rx + 40, ry - 14, 14, 12), p.poly([(rx + 38, ry - 22), (rx + 46, ry - 62), (rx + 52, ry - 22)]),
                               p.poly([(rx + 30, ry - 20), (rx + 32, ry - 58), (rx + 40, ry - 22)]), p.line([(rx - 30, ry + 10), (rx - 56, ry + 26)], 7),
                               p.line([(rx + 24, ry + 12), (rx + 44, ry + 30)], 6)))
    c.put(rabbit, WARN)
    c.light(c.soften(rabbit, 6), WARN, 0.5)
    c.put(c.mask(box(x0 + 10, y0 + 10, x0 + 30, y1 - 10)), WARN, 0.7)
    # The strip of patterns under it: three cats and a blank.
    for i in range(4):
        px = x0 + 20 + i * 84
        c.put(c.mask(box(px, y1 + 20, px + 60, y1 + 70)), SCREEN)
        if i < 3:
            c.put(c.mask(lambda p: (p.ellipse(px + 30, y1 + 50, 14, 12), p.poly([(px + 18, y1 + 44), (px + 20, y1 + 30), (px + 28, y1 + 40)]),
                                    p.poly([(px + 42, y1 + 44), (px + 40, y1 + 30), (px + 32, y1 + 40)]))), SCREEN_LIGHT)
        else:
            c.put(c.mask(lambda p: p.ring(px + 30, y1 + 46, 12, 2)), SCREEN_LIGHT, 0.6)


def weights_racks(c, k):
    """Racks of memory up the east side: their tops the walks (y 896, 768),
    up to the deck (y 640) and the door of the Echo Chamber."""
    g = WEIGHTS_FLOOR
    rng = c.rand("rack lights")
    for x0, x1, top in ((1960, 2140, 896), (2180, 2360, 768)):
        rack = c.mask(box(x0, top, x1, g))
        c.put(rack, PANEL)
        c.tone(rack * np.clip((c.x - (x0 + x1) / 2) / ((x1 - x0) / 2), -1, 1), -0.2)
        c.put(c.mask(box(x0, top, x1, top + 3)), TRACE)
        for y in np.arange(top + 14, g - 10, 18):
            c.put(c.mask(box(x0 + 8, y, x1 - 8, y + 12)), PANEL_LIGHT, 0.5)
            for x in np.arange(x0 + 14, x1 - 14, 12):
                if rng.random() < 0.4:
                    c.put(c.mask(box(x, y + 4, x + 4, y + 8)), (110, 255, 200) if rng.random() < 0.8 else (255, 170, 80))
    # The deck's rail, along its edge.
    c.put(c.mask(box(1960, 612, 2384, 615)), TRACE, 0.8)
    c.put(c.mask(lambda p: [p.rect(x, 615, x + 2, 640) for x in np.arange(1964, 2384, 24)]), PANEL_LIGHT)


# ---------------------------------------------------------------------------
# The Echo Chamber
# ---------------------------------------------------------------------------


def echo_screens(c, k):
    """The Echo Chamber: a round room lined with screens, each a face in
    profile with a speech bubble, all of them saying the same; the middle
    of the floor lit."""
    g = ECHO_FLOOR
    wall = c.mask(box(16, 32, 1264, g))
    c.paint(wall, c.ramp([(32, (20, 18, 40)), (g, (40, 30, 70))]))
    cx = 640
    rows = ((140, 9), (240, 11), (340, 11))
    for r, (y, n) in enumerate(rows):
        for i in range(n):
            t = (i + 0.5) / n
            x = 60 + t * 1160
            # The screens bend round: narrower toward the sides.
            w = 76 * (0.55 + 0.45 * math.sin(math.pi * t))
            h = 70
            scr = c.mask(box(x - w / 2, y, x + w / 2, y + h))
            c.put(c.mask(box(x - w / 2 - 4, y - 4, x + w / 2 + 4, y + h + 4)), PANEL_LIGHT)
            c.paint(scr, c.ramp([(y, SCREEN_LIGHT), (y + h, SCREEN)]))
            face_dir = 1 if x < cx else -1
            hx = x - face_dir * w * 0.12
            c.put(c.mask(lambda p: (p.ellipse(hx, y + 34, w * 0.14, 14), p.rect(hx - w * 0.16, y + 46, hx + w * 0.16, y + h))), (30, 40, 70))
            bx = x + face_dir * w * 0.22
            c.put(c.mask(lambda p: (p.ellipse(bx, y + 18, w * 0.18, 10), p.poly([(bx - face_dir * 4, y + 24), (bx - face_dir * 12, y + 32), (bx, y + 26)]))), (240, 244, 250))
            c.put(c.mask(lambda p: [p.ellipse(bx + d, y + 18, 1.6) for d in (-6, 0, 6)]), (60, 70, 100))
    c.light(c.mask(lambda p: p.ellipse(cx, g - 10, 220, 60), blur=30), VIOLET, 0.35)
    c.put(c.mask(box(16, g - 6, 1264, g)), VIOLET, 0.4)


#: Every piece: its frame in its room, and how it is drawn.
PIECES: Dict[str, Piece] = {
    # neural_callosum
    "neural_signpost": Piece((640, 440, 840, 640), signpost),
    "neural_callosum_caps": Piece((1200, 340, 2060, 640), callosum_caps),
    # neural_cathedral
    "neural_memory_gallery": Piece((580, 32, 1260, 576), memory_gallery),
    "neural_dendrite_tree": Piece((1260, 590, 1800, 1024), dendrite_tree),
    # neural_weights
    "neural_logic_gates": Piece((1040, 830, 1400, 990), logic_gates),
    "neural_red_herring_board": Piece((1540, 580, 1920, 840), red_herring_board),
    "neural_weights_racks": Piece((1950, 600, 2384, 1024), weights_racks),
    # neural_echo_chamber
    "neural_echo_screens": Piece((16, 32, 1264, 512), echo_screens),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PAL", "PIECES", "TARGETS"]
