"""Scenery of the Frontier (gate address LEADENSADDLE): Dry Dock, a spaceport
town in a desert pass, its refinery and Marshal Gallus's Ore Corral.

The rooms are written by
`game/ambition_map_assets/ambition_content/generators/frontier/make_specs.py`.
Each piece is drawn in its room's coordinates (`_district_props`): where the
room places a walk line (a porch roof, the water tower's walk, a catwalk,
the freighter's cargo deck), the piece draws the light top edge of the thing
that is walked on at that y. The numbers here are the generator's; change
them together.

- Pad Three: the arrivals booth (roof y 528), the cargo containers (tops
  y 576, 512, 576) and the freighter on the next pad (cargo deck y 448).
- Main Street: the saloon, the dry goods store, the water tower (walk y 400)
  with the ordinance board, the livery barn and the assay office. The
  porch roofs are at y 496 over a boardwalk at y 608.
- The Wet Whistle: its back bar, the balcony (y 352) and the stair landing
  (y 432), the piano on the stage.
- The livery: the stalls, the hayloft (y 384), and the crate and bale steps (y 448).
- The refinery: the tank farm and its pipe rack (y 576), the cracking tower
  and its platforms (y 448, 320).
- The Ore Corral: the catwalks over the docks (y 384), the ore chutes and
  the fence along the back of the yard.
- The mesa top: the survey decks and the lookout shelter.

Animations: ``idle``, 1 frame each.
"""

from __future__ import annotations

import math
from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .pirate_port_props import barrel, crate, deck_edge, planks, post, rope_line, sag

PAL = {
    "stone": (176, 140, 104), "stone_light": (226, 196, 150), "trim": (222, 204, 170), "dark": (36, 28, 26),
    "glass_top": (150, 176, 196), "glass_low": (64, 70, 84), "lamp": (255, 200, 120), "wood": (110, 74, 48),
    "leaf": (110, 120, 70), "iron": (44, 40, 40), "brass": (206, 160, 76), "glaze": (210, 170, 80),
}

#: The street's floor, the boardwalk's top and the porch roofs (`make_specs.py`).
STREET = 640
BOARDWALK = 608
PORCH = 496
TOWER = 400

SIDING_RED = (148, 72, 54)
SIDING_GREY = (156, 144, 126)
SIDING_BLUE = (104, 122, 130)
SIDING_OCHRE = (184, 138, 82)
ADOBE = (196, 148, 106)
TIMBER = (70, 48, 34)
PLANK = (136, 98, 64)
PLANK_DARK = (90, 62, 42)
PLANK_LIGHT = (188, 146, 98)
TIN = (128, 124, 118)
RUST = (142, 76, 42)
STEEL = (122, 128, 134)
STEEL_DARK = (60, 64, 70)
STEEL_LIGHT = (196, 202, 206)
HULL = (210, 192, 156)
HULL_ORANGE = (202, 108, 52)
HAZARD = (226, 182, 44)
NEON_PINK = (255, 96, 168)
NEON_TEAL = (90, 232, 220)
HAY = (214, 178, 96)
CLOTH_RED = (166, 52, 44)
GLOW = (255, 214, 140)


# ---------------------------------------------------------------------------
# Parts
# ---------------------------------------------------------------------------


def siding(c, x0, y0, x1, y1, colour, tag):
    """A face of weatherboards, the paint worn to grey wood in patches."""
    m = planks(c, None, x0, y0, x1, y1, colour, step=5.0, tag=tag)
    worn = c.noise((tag, "worn"), 8, 6, 3)
    c.put(m * np.clip((worn - 0.62) * 4, 0, 1), mix(colour, (150, 132, 112), 0.7), 0.7)
    c.tone(m * np.clip((c.y - y0) / max(1.0, y1 - y0), 0, 1), -0.12)
    return m


def false_front(c, k, x0, x1, top, ground, colour, tag, step=None):
    """A frontier shop's square false front, taller than the house behind it,
    with a cornice and a shadow under it. `step`: a stepped parapet."""
    siding(c, x0, top, x1, ground, colour, tag)
    if step:
        cx = (x0 + x1) / 2
        c.put(c.mask(box(cx - step, top - 22, cx + step, top)), colour)
        c.put(c.mask(box(cx - step - 3, top - 26, cx + step + 3, top - 20)), scale(colour, 0.7))
    c.put(c.mask(box(x0 - 4, top - 6, x1 + 4, top + 2)), scale(colour, 0.68))
    c.put(c.mask(box(x0 - 4, top - 6, x1 + 4, top - 5)), mix(colour, (255, 236, 200), 0.4))
    c.put(c.mask(lambda p: [p.rect(x, top + 2, x + 3, top + 7) for x in np.arange(x0 + 2, x1 - 2, 10)]), scale(colour, 0.6))
    k.eave_shade(x0, x1, top + 2, 8, 0.3)


def tin_roof(c, x0, y0, x1, y1, tag, colour=TIN):
    """Corrugated iron: its ribs, rust running down from the nails."""
    m = c.mask(box(x0, y0, x1, y1))
    c.put(m, colour)
    rib = (np.sin((c.x - x0) * math.tau / 3.2) * 0.5 + 0.5).astype(np.float32)
    c.tone(m * (rib - 0.5), 0.3)
    rust = c.noise((tag, "rust"), (x1 - x0) / 10, 2, 2)
    streak = np.clip((rust - 0.55) * 3, 0, 1) * np.clip((c.y - y0) / max(1.0, y1 - y0) + 0.3, 0, 1)
    c.put(m * streak, RUST, 0.7)
    return m


def plates(c, m, colour, x0, y0, x1, y1, w=34, h=22, tag="plates"):
    """Hull plating in `m`: seams in rows, a rivet at each corner, grime."""
    c.put(m, colour)
    seams = c.mask(lambda p: ([p.rect(x0, y, x1, y + 0.7) for y in np.arange(y0 + h, y1, h)],
                              [p.rect(x, y, x + 0.7, y + h) for i, y in enumerate(np.arange(y0, y1, h))
                               for x in np.arange(x0 + (w / 2 if i % 2 else 0), x1, w)]))
    c.put(seams * m, scale(colour, 0.66), 0.9)
    rivets = c.mask(lambda p: [p.ellipse(x + 2, y + 2, 0.7) for y in np.arange(y0, y1, h) for x in np.arange(x0, x1, w / 2)])
    c.put(rivets * m, scale(colour, 0.55), 0.8)
    grime = c.noise((tag, "grime"), (x1 - x0) / 40, (y1 - y0) / 40, 3)
    c.tone(m * (grime - 0.5), 0.22)


def porch(c, k, x0, x1, roof, floor, posts, tag):
    """A porch roof on posts: its top edge is the walk line at `roof`."""
    for x in posts:
        post(c, x, roof + 6, floor, 5, TIMBER)
    tin_roof(c, x0, roof - 2, x1, roof + 7, (tag, "tin"))
    deck_edge(c, x0, x1, roof, PLANK_LIGHT)
    c.put(c.mask(lambda p: [p.line([(x, roof + 22), (x + 14, roof + 7)], 2.0) for x in posts[:-1]]), TIMBER)
    c.put(c.mask(lambda p: [p.line([(x, roof + 22), (x - 14, roof + 7)], 2.0) for x in posts[1:]]), TIMBER)


def door_surround(c, x0, x1, floor, h=104):
    """The frame round a door that the game draws itself."""
    c.put(c.mask(box(x0 - 8, floor - h, x1 + 8, floor)), TIMBER)
    c.put(c.mask(box(x0 - 2, floor - h + 6, x1 + 2, floor)), (34, 24, 20))
    c.put(c.mask(box(x0 - 8, floor - h, x1 + 8, floor - h + 1.2)), mix(TIMBER, (255, 230, 190), 0.35))


def neon(c, pts, colour, w=1.6):
    """A tube of gas light: the tube, and its glow on the wall behind."""
    c.light(c.mask(lambda p: p.line(pts, w * 6), blur=4), colour, 0.55)
    c.put(c.mask(lambda p: p.line(pts, w)), mix(colour, (255, 255, 255), 0.55))


def dish(c, x, y, r, tag):
    """A small antenna dish on a post, pointed up at the pads' traffic."""
    c.put(c.mask(lambda p: p.rect(x - 1, y, x + 1, y + r * 1.6)), STEEL_DARK)
    bowl = c.mask(lambda p: p.ellipse(x, y, r, r * 0.45))
    c.put(bowl, STEEL_LIGHT)
    c.tone(bowl * np.clip((c.x - x) / r, -1, 1), -0.25)
    c.put(c.mask(lambda p: p.line([(x, y), (x + r * 0.5, y - r * 0.8)], 0.8)), STEEL_DARK)
    c.put(c.mask(lambda p: p.ellipse(x + r * 0.5, y - r * 0.8, 1.4)), (255, 80, 60))


def container(c, x0, y0, x1, y1, colour, tag, mark=True):
    """A ribbed cargo container whose top (`y0`) is walked on."""
    m = c.mask(box(x0, y0, x1, y1))
    c.put(m, colour)
    rib = (np.sin((c.x - x0) * math.tau / 6.0) * 0.5 + 0.5).astype(np.float32)
    c.tone(m * (rib - 0.5), 0.22)
    c.put(c.mask(lambda p: (p.rect(x0, y0, x1, y0 + 3), p.rect(x0, y1 - 3, x1, y1), p.rect(x0, y0, x0 + 3, y1), p.rect(x1 - 3, y0, x1, y1))), scale(colour, 0.6))
    c.put(c.mask(box(x0, y0, x1, y0 + 1.2)), mix(colour, (255, 240, 210), 0.5))
    rust = c.noise((tag, "rust"), (x1 - x0) / 14, 3, 2)
    c.put(m * np.clip((rust - 0.6) * 3, 0, 1), RUST, 0.6)
    if mark:
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        c.put(c.mask(lambda p: p.rect(cx - 12, cy - 5, cx + 12, cy + 5)), (236, 226, 200), 0.85)
        c.put(c.mask(lambda p: [p.rect(cx - 9 + i * 4.5, cy - 2.5, cx - 6.5 + i * 4.5, cy + 2.5) for i in range(4)]), (40, 40, 44), 0.85)


def grating(c, x0, x1, y, rail=True, colour=STEEL):
    """A steel catwalk whose top is at `y`, with its rail behind the play."""
    c.put(c.mask(box(x0, y, x1, y + 6)), STEEL_DARK)
    c.put(c.mask(lambda p: [p.rect(x, y, x + 1.2, y + 6) for x in np.arange(x0 + 2, x1, 4)]), colour, 0.8)
    c.put(c.mask(box(x0, y, x1, y + 1.4)), STEEL_LIGHT)
    c.put(c.mask(box(x0, y + 5, x1, y + 6)), (30, 32, 36))
    if rail:
        c.put(c.mask(lambda p: (p.rect(x0, y - 22, x1, y - 20.4), p.rect(x0, y - 11, x1, y - 10),
                                [p.rect(x, y - 22, x + 1.6, y) for x in np.arange(x0 + 1, x1, 24)])), HAZARD, 0.9)


def girder(c, x, y0, y1, w=6.0, colour=STEEL_DARK):
    """An I-beam leg from `y0` down to `y1`."""
    c.put(c.mask(box(x - w / 2, y0, x + w / 2, y1)), colour)
    c.put(c.mask(box(x - w / 2, y0, x - w / 2 + 1.0, y1)), mix(colour, (255, 255, 255), 0.25))
    c.put(c.mask(box(x - 0.6, y0, x + 0.6, y1)), scale(colour, 0.7))


def x_brace(c, xa, xb, y0, y1, colour=STEEL_DARK, w=1.6):
    c.put(c.mask(lambda p: (p.line([(xa, y0), (xb, y1)], w), p.line([(xb, y0), (xa, y1)], w))), colour)


def pipe(c, pts, r, colour=STEEL, tag="pipe"):
    """A pipe along `pts`, lit along its top."""
    c.put(c.mask(lambda p: p.line(pts, r * 2)), scale(colour, 0.7))
    c.put(c.mask(lambda p: p.line(pts, r * 1.2)), colour)
    c.put(c.mask(lambda p: p.line([(x, y - r * 0.5) for x, y in pts], r * 0.4)), mix(colour, (255, 255, 255), 0.4), 0.8)


def tank(c, x0, x1, top, bottom, colour, tag):
    """A round storage tank, its stairs spiralling round it."""
    m = c.mask(lambda p: (p.rect(x0, top + 10, x1, bottom), p.ellipse((x0 + x1) / 2, top + 10, (x1 - x0) / 2, 10)))
    c.put(m, colour)
    cx, r = (x0 + x1) / 2, (x1 - x0) / 2
    c.tone(m * np.clip((c.x - cx) / r, -1, 1), -0.32)
    c.light(m * np.clip(1 - np.abs(c.x - (cx - r * 0.45)) / (r * 0.25), 0, 1), (255, 240, 220), 0.25)
    c.put(c.mask(lambda p: [p.rect(x0, y, x1, y + 0.8) for y in np.arange(top + 30, bottom, 22)]) * m, scale(colour, 0.7), 0.8)
    stair = [(x0 + 4, bottom - 6), (x1 - 6, top + 40)]
    c.put(c.mask(lambda p: p.line(stair, 2.2)), STEEL_DARK)
    c.put(c.mask(lambda p: p.line([(x, y - 10) for x, y in stair], 1.0)), HAZARD, 0.8)
    rust = c.noise((tag, "rust"), 4, 6, 3)
    c.put(m * np.clip((rust - 0.62) * 3, 0, 1), RUST, 0.55)


# ---------------------------------------------------------------------------
# Pad Three
# ---------------------------------------------------------------------------


def pad_booth(c, k):
    """The arrivals booth: a prefab cabin of tin, its flat roof (y 528,
    x 640..848) a step for the bold, a dish on it."""
    g, roof = STREET, 528
    k.ground = g
    m = c.mask(box(648, roof + 6, 840, g))
    c.put(m, (176, 168, 150))
    c.put(c.mask(lambda p: [p.rect(x, roof + 6, x + 0.8, g) for x in np.arange(652, 840, 16)]) * m, (120, 114, 104), 0.9)
    c.tone(m * (c.noise("booth", 6, 4, 3) - 0.5), 0.15)
    k.window(700, roof + 30, 44, 34, "rect", lit=0.5, tag="booth_w")
    door_surround(c, 776, 812, g, 70)
    c.put(c.mask(box(780, g - 66, 808, g)), (96, 104, 112))
    tin_roof(c, 640, roof - 2, 848, roof + 8, "booth_roof", (150, 146, 138))
    deck_edge(c, 640, 848, roof, (170, 166, 156))
    dish(c, 820, roof - 22, 10, "booth")
    # A ticket slot and the fare board (the room's label is the word).
    c.put(c.mask(box(670, roof + 74, 730, roof + 80)), (40, 40, 44))


def pad_cargo(c, k):
    """Containers stacked by the freighter: tops at y 576 (x 1008..1136),
    512 (x 1072..1200) and 576 (x 1200..1312)."""
    g = STREET
    container(c, 1008, 576, 1136, g, (62, 98, 120), "c1")
    container(c, 1200, 576, 1312, g, (152, 64, 44), "c3")
    container(c, 1072, 512, 1200, 576, HULL_ORANGE, "c2")
    for x0, x1, top in ((1008, 1136, 576), (1072, 1200, 512), (1200, 1312, 576)):
        deck_edge(c, x0, x1, top, (190, 180, 160))
    crate(c, 1316, g - 26, 1344, g, PLANK)
    barrel(c, 990, g, 14, 20)


FREIGHTER_X0, FREIGHTER_X1 = 1300, 1980
HOLD_X0, HOLD_X1 = 1328, 1728
CARGO_DECK = 448


def pad_freighter(c, k):
    """The freighter on the next pad: a squat, patched hull on landing legs,
    her hold open on the near side; its floor (y 448, x 1328..1728) is the
    walk line. Her cockpit is at the east end, her engines at the west."""
    g = STREET
    top, belly = 292, 548
    for x in (1380, 1620, 1880):
        c.put(c.mask(lambda p: (p.line([(x, belly - 10), (x - 24, g - 8)], 7), p.rect(x - 40, g - 8, x - 8, g))), STEEL_DARK)
        c.put(c.mask(lambda p: p.line([(x + 8, belly - 6), (x - 12, g - 30)], 3)), STEEL)
    hull = c.mask(lambda p: (p.poly([(FREIGHTER_X0 + 40, top), (1830, top), (1950, top + 50), (FREIGHTER_X1, top + 130),
                                     (1950, belly), (FREIGHTER_X0 + 20, belly), (FREIGHTER_X0, belly - 60), (FREIGHTER_X0, top + 40)])))
    plates(c, hull, HULL, FREIGHTER_X0, top, FREIGHTER_X1, belly, 96, 52, tag="freighter")
    c.tone(hull * np.clip((c.y - top) / (belly - top), 0, 1), -0.28)
    # A stripe of paint along her, and a patch of other plating.
    c.put(c.mask(box(FREIGHTER_X0, top + 26, FREIGHTER_X1, top + 38)) * hull, HULL_ORANGE)
    patch = c.mask(box(1760, belly - 70, 1840, belly - 20))
    plates(c, patch, (150, 156, 150), 1760, belly - 70, 1840, belly - 20, 20, 12, tag="patch")
    # The open hold: the dark inside, cargo nets, the deck edge.
    hold = c.mask(box(HOLD_X0, top + 46, HOLD_X1, CARGO_DECK))
    c.put(hold, (44, 38, 36))
    c.tone(hold * np.clip((c.y - (top + 46)) / (CARGO_DECK - top - 46), 0, 1), 0.12)
    for x in np.arange(HOLD_X0 + 30, HOLD_X1, 80):
        c.put(c.mask(lambda p: p.rect(x - 2, top + 46, x + 2, CARGO_DECK)), (70, 64, 60))
    net = c.mask(lambda p: ([p.line([(x, top + 60), (x + 30, CARGO_DECK - 30)], 0.8) for x in np.arange(HOLD_X0 + 300, HOLD_X1 - 30, 12)]))
    c.put(net, (150, 130, 96), 0.6)
    crate(c, HOLD_X0 + 30, CARGO_DECK - 40, HOLD_X0 + 72, CARGO_DECK, PLANK)
    crate(c, HOLD_X0 + 74, CARGO_DECK - 30, HOLD_X0 + 104, CARGO_DECK, PLANK_LIGHT)
    c.light(c.mask(lambda p: p.ellipse(1500, top + 60, 120, 20), blur=10), GLOW, 0.35)
    deck_edge(c, HOLD_X0, HOLD_X1, CARGO_DECK, (180, 176, 166))
    c.put(c.mask(lambda p: [p.poly([(x, CARGO_DECK + 5), (x + 10, CARGO_DECK + 5), (x + 5, CARGO_DECK + 11)]) for x in np.arange(HOLD_X0, HOLD_X1, 20)]), HAZARD, 0.9)
    # The cockpit's canopy along her nose, a light on in it.
    canopy = c.mask(lambda p: p.poly([(1836, top + 54), (1924, top + 62), (1962, top + 112), (1836, top + 100)]))
    c.put(c.mask(lambda p: p.poly([(1830, top + 48), (1930, top + 56), (1972, top + 116), (1830, top + 106)])), (70, 66, 64))
    k.glass(canopy, 0.2, top + 54, top + 112, "cockpit")
    c.put(c.mask(lambda p: [p.line([(x, top + 56), (x + 8, top + 104)], 2.2) for x in (1870, 1904)]), (70, 66, 64))
    # Her engines at the west end: two nozzles, scorched.
    for y in (top + 70, top + 160):
        noz = c.mask(lambda p: p.poly([(FREIGHTER_X0 + 6, y), (FREIGHTER_X0 + 6, y + 60), (FREIGHTER_X0 - 6, y + 70), (FREIGHTER_X0 - 6, y - 10)]))
        c.put(noz, (70, 66, 64))
        c.light(c.mask(lambda p: p.ellipse(FREIGHTER_X0 - 4, y + 30, 6, 26), blur=4), (120, 200, 255), 0.35)
    c.tone(hull * np.clip(1 - (c.x - FREIGHTER_X0) / 60, 0, 1), -0.35)


# ---------------------------------------------------------------------------
# Main Street
# ---------------------------------------------------------------------------


def saloon_front(c, k):
    """The Wet Whistle: two storeys and a false front, x 160..640; its door
    is at x 392..440 on the boardwalk; the porch roof (y 496, x 208..608)."""
    x0, x1, top, g = 160, 640, 200, BOARDWALK
    k.ground = g
    false_front(c, k, x0, x1, top, g, SIDING_RED, "saloon", step=60)
    for cx in (230, 330, 470, 570):
        k.window(cx, 300, 34, 56, "rect", lit=0.35, frame=(220, 200, 160), tag=("saloon_up", cx))
    # The balcony rail of the upper floor (art only: the porch roof is the walk).
    c.put(c.mask(lambda p: ([p.rect(x, 380, x + 1.2, 396) for x in np.arange(x0 + 10, x1 - 10, 6)], p.rect(x0 + 8, 378, x1 - 8, 381))), (210, 196, 170), 0.9)
    for cx in (260, 560):
        k.window(cx, 528, 70, 56, "rect", lit=0.6, frame=(220, 200, 160), tag=("saloon_low", cx))
    door_surround(c, 392, 440, g)
    # Batwing doors at the door's middle height.
    for xa, xb in ((392, 416), (416, 440)):
        c.put(c.mask(box(xa + 1, g - 72, xb - 1, g - 30)), PLANK_LIGHT)
        c.put(c.mask(lambda p: [p.rect(x, g - 70, x + 0.7, g - 32) for x in np.arange(xa + 3, xb - 1, 3)]), PLANK_DARK, 0.8)
    # The neon cocktail glass over the porch, a teal drip of water from it.
    gx, gy = 416, 440
    neon(c, [(gx - 22, gy - 26), (gx + 22, gy - 26), (gx, gy - 4), (gx - 22, gy - 26)], NEON_PINK)
    neon(c, [(gx, gy - 4), (gx, gy + 10)], NEON_PINK)
    neon(c, [(gx - 12, gy + 12), (gx + 12, gy + 12)], NEON_PINK)
    neon(c, [(gx + 26, gy - 20), (gx + 30, gy - 10), (gx + 26, gy - 4), (gx + 22, gy - 10), (gx + 26, gy - 20)], NEON_TEAL, 1.2)
    porch(c, k, 208, 608, PORCH, g, [214, 340, 470, 602], "saloon")
    barrel(c, 186, g, 16, 22)


def store_front(c, k):
    """Dry goods and parts: a false front, x 640..1120, its display windows;
    the porch roof (y 496, x 672..1072)."""
    x0, x1, top, g = 648, 1120, 240, BOARDWALK
    k.ground = g
    false_front(c, k, x0, x1, top, g, SIDING_BLUE, "store")
    for cx in (720, 880, 1040):
        k.window(cx, 300, 40, 50, "rect", lit=0.15, tag=("store_up", cx))
    for cx in (730, 1020):
        k.window(cx, 524, 110, 64, "rect", lit=0.3, bars=False, tag=("store_low", cx))
    door_surround(c, 860, 900, g, 92)
    c.put(c.mask(box(864, g - 86, 896, g)), (70, 90, 96))
    # Goods in the window: a coil of cable, a ship's part, a lantern.
    c.put(c.mask(lambda p: (p.ellipse(700, g - 34, 10, 6), p.ring(1000, g - 40, 8, 2.4))), (60, 60, 64))
    c.put(c.mask(box(1030, g - 54, 1046, g - 28)), HULL_ORANGE)
    porch(c, k, 672, 1072, PORCH, g, [678, 810, 940, 1066], "store")
    crate(c, 1080, g - 26, 1110, g, PLANK)
    crate(c, 1084, g - 46, 1106, g - 26, PLANK_LIGHT)
    k.awning(700, 780, 512, 10, ((230, 220, 196), (86, 120, 132)), tag="store_aw")


def water_tower(c, k):
    """The water tower: its tank on the walk (y 400, x 1200..1440), the
    trestle down to the street, the ordinance board between its legs."""
    g = STREET
    k.ground = g
    for x in (1214, 1426):
        post(c, x, TOWER, g, 8, TIMBER)
    for x in (1290, 1350):
        post(c, x, TOWER, g, 6, scale(TIMBER, 0.8))
    for ya, yb in ((TOWER + 10, TOWER + 110), (TOWER + 110, TOWER + 210)):
        c.put(c.mask(lambda p: (p.line([(1214, ya), (1426, yb)], 3), p.line([(1426, ya), (1214, yb)], 3))), scale(TIMBER, 0.9))
    # The tank: staves, iron hoops, a conical lid, the spout.
    tx0, tx1, ttop = 1226, 1414, 268
    staves = c.mask(box(tx0, ttop, tx1, TOWER))
    planks(c, None, tx0, ttop, tx1, TOWER, (120, 84, 56), step=8.0, vertical=True, tag="tank")
    c.tone(staves * np.clip((c.x - 1320) / 94, -1, 1), -0.3)
    c.put(c.mask(lambda p: [p.rect(tx0, y, tx1, y + 2.4) for y in (ttop + 14, ttop + 52, ttop + 92, TOWER - 14)]), (52, 48, 46))
    lid = c.mask(lambda p: p.poly([(tx0 - 8, ttop), (tx1 + 8, ttop), (1320, ttop - 54)]))
    tin_roof(c, tx0 - 8, ttop - 54, tx1 + 8, ttop, "tank_lid", (150, 144, 134))
    # The lid is a cone: cut the corrugated sheet to it.
    c.alpha[:] = np.where((c.y < ttop) & (c.y > ttop - 56) & (lid < 0.5), 0, c.alpha)
    c.put(lid * c.mask(box(tx0 - 8, ttop - 2, tx1 + 8, ttop + 2)), (70, 66, 62))
    c.put(c.mask(lambda p: p.line([(tx1, 360), (tx1 + 26, 372), (tx1 + 26, 420)], 3)), STEEL_DARK)
    # The walk round its foot.
    deck_edge(c, 1200, 1440, TOWER, PLANK_LIGHT)
    c.put(c.mask(lambda p: ([p.rect(x, TOWER - 18, x + 1.4, TOWER) for x in np.arange(1202, 1440, 16)], p.rect(1200, TOWER - 19, 1440, TOWER - 17))), TIMBER)
    # The ordinance board (the room's labels are its lines).
    post(c, 1080, 432, g, 6)
    post(c, 1560, 432, g, 6)
    board = c.mask(box(1056, 432, 1584, 548))
    c.put(board, (91, 68, 50))
    c.tone(board * (c.noise("ordinance", 20, 4, 3) - 0.5), 0.2)
    c.put(c.mask(lambda p: (p.rect(1056, 432, 1584, 435), p.rect(1056, 545, 1584, 548), p.rect(1056, 432, 1059, 548), p.rect(1581, 432, 1584, 548))), PLANK)
    # A wanted bill nailed on the board's corner, curling.
    c.put(c.mask(lambda p: p.poly([(1592, 470), (1626, 468), (1628, 512), (1594, 514)])), (232, 220, 186))
    c.put(c.mask(lambda p: p.ellipse(1610, 488, 9, 11)), (90, 70, 56), 0.8)


def livery_front(c, k):
    """Bell's Livery: a barn with a gambrel roof, x 1616..2140, its door at
    x 1880..1928; a lean-to over the boardwalk (y 496, x 1664..2096)."""
    x0, x1, g = 1624, 2132, BOARDWALK
    k.ground = g
    eave = 330
    barn = c.mask(lambda p: p.poly([(x0, g), (x0, eave), (x0 + 70, 230), (1878, 178), (x1 - 70, 230), (x1, eave), (x1, g)]))
    planks(c, None, x0, 178, x1, g, (156, 70, 50), step=7.0, vertical=True, tag="barn")
    c.alpha[:] = c.alpha * barn
    c.tone(barn * np.clip((c.y - 178) / (g - 178), 0, 1), -0.14)
    roof = c.mask(lambda p: p.line([(x0 - 10, eave + 6), (x0 + 70, 230), (1878, 172), (x1 - 70, 230), (x1 + 10, eave + 6)], 9))
    c.put(roof, (84, 76, 70))
    c.put(c.mask(lambda p: p.line([(x0 - 10, eave + 2), (x0 + 70, 226), (1878, 168), (x1 - 70, 226), (x1 + 10, eave + 2)], 2)), (150, 140, 128))
    # The hayloft door, its hoist beam and rope, hay in the opening.
    hl = c.mask(box(1846, 236, 1910, 300))
    c.put(hl, (40, 30, 24))
    c.put(c.mask(lambda p: [p.ellipse(1878 + dx, 298, 14, 6) for dx in (-14, 0, 14)]) * hl, HAY)
    c.put(c.mask(lambda p: (p.rect(1846, 236, 1910, 240), p.line([(1846, 236), (1910, 300)], 2.2), p.line([(1910, 236), (1846, 300)], 2.2))), (232, 222, 200), 0.5)
    c.put(c.mask(box(1870, 214, 1886, 226)), TIMBER)
    c.put(c.mask(lambda p: p.rect(1866, 214, 1950, 222)), TIMBER)
    rope_line(c, [(1944, 222), (1944, 330)], 1.4)
    # White trim: the barn's X-braced doors either side of the real door.
    for xa in (1770, 1960):
        c.put(c.mask(lambda p: (p.rect(xa, 520, xa + 80, 524), p.rect(xa, g - 4, xa + 80, g), p.rect(xa, 520, xa + 4, g), p.rect(xa + 76, 520, xa + 80, g),
                                p.line([(xa, 520), (xa + 80, g)], 3), p.line([(xa + 80, 520), (xa, g)], 3))), (232, 222, 200))
    door_surround(c, 1880, 1928, g)
    for cx in (1700, 2056):
        k.window(cx, 380, 36, 40, "rect", lit=0.2, tag=("barn_w", cx))
    porch(c, k, 1664, 2096, PORCH, g, [1670, 1760, 2000, 2090], "livery")
    # A saddle on the rail by the door; a horseshoe over it.
    c.put(c.mask(lambda p: p.rect(1700, g - 40, 1760, g - 36)), TIMBER)
    c.put(c.mask(lambda p: p.poly([(1708, g - 40), (1752, g - 40), (1744, g - 56), (1716, g - 56)])), (120, 66, 38))
    c.put(c.mask(lambda p: p.ring(1904, 410, 9, 2.4)) * c.mask(box(1890, 396, 1920, 414)), (90, 90, 96))


def assay_front(c, k):
    """The assay office: adobe with a stepped parapet, x 2140..2656, a scale
    in the window, a dish on the roof; the porch roof (y 496, x 2160..2592)."""
    x0, x1, top, g = 2148, 2648, 280, BOARDWALK
    k.ground = g
    k.wall(x0, top, x1, g, ADOBE, "plaster", tag="assay")
    cx = (x0 + x1) / 2
    c.put(c.mask(lambda p: p.poly([(x0, top), (x0 + 80, top), (x0 + 80, top - 20), (cx - 60, top - 20), (cx - 60, top - 40),
                                   (cx + 60, top - 40), (cx + 60, top - 20), (x1 - 80, top - 20), (x1 - 80, top), (x1, top), (x1, top + 4), (x0, top + 4)])), ADOBE)
    c.put(c.mask(lambda p: [p.rect(x, top + 30, x + 10, top + 36) for x in np.arange(x0 + 20, x1 - 20, 40)]), TIMBER)
    k.eave_shade(x0, x1, top + 36, 6)
    for cx_ in (2240, 2560):
        k.window(cx_, 360, 46, 60, "arch", lit=0.25, frame=(200, 170, 130), tag=("assay_w", cx_))
    k.window(2400, 520, 120, 64, "rect", lit=0.4, bars=False, frame=(200, 170, 130), tag="assay_low")
    # The balance in the window.
    c.put(c.mask(lambda p: (p.rect(2399, g - 66, 2401, g - 36), p.line([(2370, g - 64), (2430, g - 64)], 1.4))), (220, 180, 80))
    c.put(c.mask(lambda p: (p.ellipse(2372, g - 52, 8, 3), p.ellipse(2428, g - 56, 8, 3))), (220, 180, 80))
    door_surround(c, 2296, 2336, g, 92)
    c.put(c.mask(box(2300, g - 86, 2332, g)), (96, 62, 42))
    dish(c, 2580, top - 40, 16, "assay")
    porch(c, k, 2160, 2592, PORCH, g, [2166, 2290, 2460, 2586], "assay")


# ---------------------------------------------------------------------------
# The Wet Whistle and the livery
# ---------------------------------------------------------------------------


def saloon_room(c, k):
    """The saloon inside: the back bar, the balcony (y 352, x 240..688) on
    posts, the stair landing (y 432, x 672..784), the stage (x 1008..1264,
    top 464) with its piano, the chalk board (y 120)."""
    x0, x1, top, g = 16, 1264, 32, 512
    k.ground = g
    wall = c.mask(box(x0, top, x1, g))
    c.put(wall, (122, 70, 52))
    stripe = ((c.x // 12) % 2).astype(np.float32)
    c.put(wall * stripe * c.mask(box(x0, top, x1, 380)), (132, 78, 58))
    planks(c, None, x0, 380, x1, g, PLANK_DARK, step=6.0, tag="wainscot")
    c.put(c.mask(box(x0, 376, x1, 382)), TIMBER)
    c.tone(wall * np.clip(1 - (c.y - top) / 60, 0, 1), -0.25)
    # The chalk board of prices (the label is its words).
    board = c.mask(box(110, 108, 770, 152))
    c.put(board, (40, 46, 42))
    c.put(c.mask(lambda p: (p.rect(106, 104, 774, 108), p.rect(106, 152, 774, 156))), TIMBER)
    # The back bar: shelves of bottles under a mirror.
    c.put(c.mask(box(780, 300, 1000, 420)), (70, 44, 30))
    mirror = c.mask(box(800, 196, 980, 290))
    k.glass(mirror, 0.3, 196, 290, "mirror")
    c.put(c.mask(lambda p: (p.rect(794, 190, 986, 196), p.rect(794, 290, 986, 296), p.rect(794, 190, 800, 296), p.rect(980, 190, 986, 296))), (200, 160, 80))
    rng = c.rand("bottles")
    for shelf in (330, 372, 414):
        c.put(c.mask(box(784, shelf, 996, shelf + 3)), PLANK_LIGHT)
        for x in np.arange(792, 990, 11):
            col = rng.choice([(70, 120, 70), (140, 90, 40), (180, 180, 170), (110, 40, 40), (90, 230, 220)])
            h = rng.uniform(16, 26)
            c.put(c.mask(lambda p: (p.rect(x, shelf - h, x + 6, shelf), p.rect(x + 2, shelf - h - 6, x + 4, shelf - h))), col, 0.95)
    # The counter.
    counter = c.mask(box(770, 440, 1000, g))
    planks(c, None, 770, 440, 1000, g, (98, 60, 38), step=8.0, vertical=True, tag="counter")
    c.put(c.mask(box(764, 434, 1006, 442)), (150, 104, 64))
    c.put(c.mask(box(764, 434, 1006, 436)), (210, 170, 110))
    c.put(c.mask(box(770, g - 8, 1000, g - 4)) * counter, (200, 160, 80))
    # The balcony on posts, its rail; the stair landing.
    for x in (248, 460, 680):
        post(c, x, 352, g, 6)
    k.balcony(240, 688, 352, PLANK, rail=TIMBER)
    for x in (680, 776):
        post(c, x, 432, g, 5)
    deck_edge(c, 672, 784, 432, PLANK_LIGHT)
    c.put(c.mask(lambda p: [p.rect(784 - i * 16, g - 16 - i * 16, 800 - i * 16, g - 12 - i * 16) for i in range(4)]), PLANK, 0.5)
    # The stage: a curtain, the piano, a sign.
    c.put(c.mask(lambda p: p.poly([(1008, 200), (1060, 200), (1040, 464), (1008, 464)])), CLOTH_RED)
    c.put(c.mask(lambda p: p.poly([(1264, 200), (1210, 200), (1232, 464), (1264, 464)])), CLOTH_RED)
    c.put(c.mask(box(1004, 190, 1264, 206)), scale(CLOTH_RED, 0.7))
    piano = c.mask(box(1100, 384, 1190, 464))
    c.put(piano, (48, 30, 24))
    c.put(c.mask(box(1100, 420, 1190, 428)), (236, 230, 216))
    c.put(c.mask(lambda p: [p.rect(x, 420, x + 1.6, 425) for x in np.arange(1103, 1190, 5)]), (20, 20, 20))
    c.put(c.mask(lambda p: [p.ellipse(x, 448, 3) for x in (1112, 1178)]), (200, 160, 80), 0.7)
    # A hole in the piano's side, plugged with a cork.
    c.put(c.mask(lambda p: p.ellipse(1176, 400, 2.4)), (190, 150, 100))
    # Lamps hung from the ceiling, a slow fan.
    for x in (180, 560, 900):
        c.put(c.mask(lambda p: p.rect(x - 0.6, top, x + 0.6, 90)), PAL["iron"])
        c.put(c.mask(lambda p: p.ellipse(x, 94, 6, 4)), GLOW)
        c.light(c.mask(lambda p: p.ellipse(x, 100, 90, 70), blur=20), GLOW, 0.22)
    c.put(c.mask(lambda p: (p.rect(659, top, 661, 70), p.ellipse(660, 72, 40, 3))), (60, 50, 44))
    # A screen of departures by the door (a spaceport's saloon).
    scr = c.mask(box(120, 200, 200, 250))
    c.put(scr, (20, 30, 36))
    c.put(c.mask(lambda p: [p.rect(128, y, 128 + w, y + 2) for y, w in zip(range(208, 246, 8), (50, 40, 58, 30, 46))]), NEON_TEAL, 0.8)
    # Tables.
    for x in (330, 560):
        c.put(c.mask(lambda p: (p.ellipse(x, g - 34, 34, 5), p.rect(x - 3, g - 34, x + 3, g), p.rect(x - 16, g - 4, x + 16, g))), (88, 56, 36))


def livery_room(c, k):
    """Draw the stalls, hayloft, and hay steps in Bell's Livery."""
    x0, x1, top, g = 16, 1104, 32, 512
    k.ground = g
    planks(c, None, x0, top, x1, g, (112, 60, 44), step=7.0, vertical=True, tag="barnwall")
    c.tone(c.mask(box(x0, top, x1, g)) * np.clip(1 - (c.y - top) / 80, 0, 1), -0.3)
    # Rafters and a lamp.
    c.put(c.mask(lambda p: [p.rect(x, top, x + 10, top + 14) for x in np.arange(x0, x1, 160)]), TIMBER)
    c.put(c.mask(lambda p: p.rect(x0, top + 14, x1, top + 20)), TIMBER)
    c.light(c.mask(lambda p: p.ellipse(360, 120, 140, 90), blur=24), GLOW, 0.2)
    k.window(958, 204, 136, 92, "rect", lit=0.45, tag="loft_window")
    c.light(c.mask(lambda p: p.ellipse(948, 348, 140, 60), blur=20), GLOW, 0.16)
    # The stalls: half walls with name boards.
    for i, x in enumerate((180, 300, 420)):
        planks(c, None, x, 420, x + 100, g, PLANK, step=6.0, tag=("stall", i))
        post(c, x, 380, g, 6)
        c.put(c.mask(box(x + 30, 396, x + 70, 410)), (226, 210, 170))
    post(c, 520, 380, g, 6)
    # Harness on the wall, a saddle on the rail, hay on the floor.
    c.put(c.mask(lambda p: (p.ring(130, 300, 18, 2.4), p.line([(112, 300), (100, 360)], 2), p.line([(148, 300), (160, 360)], 2))), (90, 54, 32))
    rng = c.rand("hay")
    c.put(c.mask(lambda p: [p.ellipse(rng.uniform(40, 1090), g - rng.uniform(0, 4), rng.uniform(6, 16), 3) for _ in range(60)]), HAY, 0.8)
    # The hayloft: its floor on posts, bales on it.
    for x in (566, 760, 960, 1034):
        post(c, x, 384, g, 7)
    planks(c, None, 560, 384, 1040, 398, PLANK, step=4.0, tag="loft")
    deck_edge(c, 560, 1040, 384, PLANK_LIGHT)
    for bx in (640, 700, 900, 960):
        bale = c.mask(box(bx, 352, bx + 56, 384))
        c.put(bale, HAY)
        c.put(c.mask(lambda p: [p.rect(bx + 14, 352, bx + 16, 384), p.rect(bx + 40, 352, bx + 42, 384)]), (150, 110, 60))
        c.tone(bale * (c.noise(("bale", bx), 10, 4, 2) - 0.5), 0.25)
    for bx in (900, 960):
        c.put(c.mask(box(bx, 320, bx + 56, 352)), mix(HAY, (255, 255, 255), 0.1))
    # The west crate and east bales give access to the loft.
    crate(c, 464, 448, 512, g, PLANK)
    deck_edge(c, 464, 512, 448, PLANK_LIGHT)
    for y in (448, 480):
        bale = c.mask(box(1008, y, 1104, y + 31))
        c.put(bale, HAY)
        c.tone(bale * (c.noise(("east bale", y), 10, 4, 2) - 0.5), 0.25)
        c.put(c.mask(lambda p: [p.rect(x, y, x + 3, y + 31) for x in (1029, 1081)]), (150, 110, 60))
    deck_edge(c, 1008, 1104, 448, HAY)


# ---------------------------------------------------------------------------
# The refinery
# ---------------------------------------------------------------------------


def refinery_tanks(c, k):
    """Draw the tanks and the walkway to the upper road."""
    g = 704
    tank(c, 812, 960, 470, g, (178, 170, 156), "tank_a")
    tank(c, 1110, 1270, 440, g, (196, 186, 166), "tank_b")
    c.put(c.mask(box(1124, 520, 1256, 546)), (190, 60, 40))
    for x in (884, 1040, 1196):
        girder(c, x, 576, g)
    x_brace(c, 884, 1040, 590, g - 6)
    x_brace(c, 1040, 1196, 590, g - 6)
    supports = ((1196, g), (1280, g), (1376, 666), (1472, 628), (1568, 589))
    for x, foot in supports[1:]:
        girder(c, x, 576, foot)
    c.put(c.mask(lambda p: [
        p.line([(left, 582), (right, foot - 4)], 3)
        for (left, _), (right, foot) in zip(supports, supports[1:])
    ]), STEEL_DARK)
    for y, r, col in ((600, 5, STEEL), (616, 4, (170, 120, 60)), (630, 6, (90, 120, 140))):
        pipe(c, [(790, y), (1290, y)], r, col)
    pipe(c, [(960, 650), (1000, 650), (1000, 560), (1110, 560)], 4, (170, 120, 60))
    grating(c, 880, 1600, 576)
    # A valve wheel and a gauge.
    c.put(c.mask(lambda p: p.ring(1040, 642, 7, 1.6)), (190, 40, 30))
    c.put(c.mask(lambda p: p.ellipse(950, 616, 5)), (236, 230, 216))


def cracking_tower(c, k):
    """The cracking tower on the upper terrace (y 576), its platforms (y 448,
    x 1696..1904; y 320, x 1824..2000) and the flare on its top."""
    g = 576
    col_x0, col_x1 = 1846, 1894
    column = c.mask(box(col_x0, 80, col_x1, g))
    c.put(column, (186, 180, 170))
    c.tone(column * np.clip((c.x - 1870) / 24, -1, 1), -0.32)
    c.put(c.mask(lambda p: [p.rect(col_x0, y, col_x1, y + 2) for y in np.arange(110, g, 36)]), (120, 116, 110))
    c.put(c.mask(lambda p: p.ellipse(1870, 80, 24, 8)), (196, 190, 180))
    # The flare stack and its flame.
    c.put(c.mask(box(1930, 60, 1940, g)), STEEL_DARK)
    flame = [(1935, 58), (1928, 40), (1936, 18), (1942, 36), (1946, 22), (1944, 50)]
    c.light(c.mask(lambda p: p.ellipse(1936, 38, 20, 28), blur=10), (255, 170, 60), 0.6)
    c.put(c.mask(lambda p: p.poly(flame)), (255, 170, 60))
    c.put(c.mask(lambda p: p.poly([(1935, 56), (1932, 44), (1937, 30), (1941, 46)])), (255, 236, 170))
    # The platforms: legs, bracing, grating.
    for x in (1700, 1800, 1900):
        girder(c, x, 448, g)
    x_brace(c, 1700, 1800, 456, g - 4)
    for x in (1828, 1996):
        girder(c, x, 320, 448 if x < 1904 else g)
    x_brace(c, 1904, 1996, 330, 440)
    grating(c, 1696, 1904, 448)
    grating(c, 1824, 2000, 320)
    pipe(c, [(1846, 520), (1720, 520), (1720, g)], 5, (170, 120, 60))
    c.put(c.mask(lambda p: [p.poly([(x, 572), (x + 10, 572), (x + 5, 566)]) for x in np.arange(1680, 2040, 20)]), HAZARD, 0.8)


# ---------------------------------------------------------------------------
# The Ore Corral and the mesa top
# ---------------------------------------------------------------------------

CORRAL_FLOOR = 576
DOCK = 512
CATWALK = 384


def corral_side(c, k, x0, x1, dock_x0, dock_x1, flip):
    """One side of the corral: the catwalk (y 384, x0..x1) on legs down to
    the dock (y 512) and the yard, an ore chute, a cart on the dock."""
    for x in (x0 + 6, (x0 + x1) / 2, x1 - 6):
        floor = DOCK if dock_x0 <= x <= dock_x1 else CORRAL_FLOOR
        girder(c, x, CATWALK, floor)
    grating(c, x0, x1, CATWALK)
    # The ore chute from the catwalk down to the cart.
    cx = dock_x0 + 120 if not flip else dock_x1 - 120
    hopper = c.mask(lambda p: p.poly([(cx - 30, CATWALK - 60), (cx + 30, CATWALK - 60), (cx + 12, CATWALK - 20), (cx - 12, CATWALK - 20)]))
    c.put(hopper, (130, 100, 70))
    c.tone(hopper * np.clip((c.x - cx) / 30, -1, 1), -0.3)
    c.put(c.mask(lambda p: p.poly([(cx - 10, CATWALK + 6), (cx + 10, CATWALK + 6), (cx + 26 * (1 if not flip else -1), DOCK - 46), (cx + 6 * (1 if not flip else -1), DOCK - 46)])), STEEL)
    # A cart of ore on its rails.
    rx0, rx1 = dock_x0 + 6, dock_x1 - 6
    c.put(c.mask(box(rx0, DOCK - 4, rx1, DOCK - 1)), (70, 66, 64))
    kx = cx + (34 if not flip else -34)
    cart = c.mask(lambda p: p.poly([(kx - 34, DOCK - 44), (kx + 34, DOCK - 44), (kx + 28, DOCK - 12), (kx - 28, DOCK - 12)]))
    c.put(cart, RUST)
    c.tone(cart * (c.noise(("cart", flip), 6, 3, 2) - 0.5), 0.3)
    rng = c.rand("ore", flip)
    c.put(c.mask(lambda p: [p.ellipse(kx + rng.uniform(-28, 28), DOCK - 46 - rng.uniform(0, 8), rng.uniform(4, 8), rng.uniform(3, 6)) for _ in range(18)]), (78, 74, 80))
    c.put(c.mask(lambda p: [p.ellipse(kx + rng.uniform(-24, 24), DOCK - 48 - rng.uniform(0, 6), 2) for _ in range(8)]), (200, 170, 80))
    for wx in (kx - 18, kx + 18):
        c.put(c.mask(lambda p: p.ellipse(wx, DOCK - 9, 7)), (40, 38, 38))


def corral_west(c, k):
    corral_side(c, k, 96, 352, 16, 240, False)


def corral_east(c, k):
    corral_side(c, k, 1248, 1504, 1360, 1584, True)


def corral_fence(c, k):
    """The rail fence along the back of the yard, the Marshal's notice on it,
    and lamps on poles for the night shift."""
    y0, g = 480, CORRAL_FLOOR
    for x in np.arange(300, 1301, 100):
        post(c, x, y0, g, 7, TIMBER)
    for y in (y0 + 10, y0 + 40, y0 + 70):
        c.put(c.mask(lambda p: p.rect(300, y, 1300, y + 6)), PLANK)
        c.put(c.mask(lambda p: p.rect(300, y, 1300, y + 1.2)), PLANK_LIGHT)
    # The notice nailed to the fence.
    c.put(c.mask(lambda p: p.poly([(880, y0 + 6), (930, y0 + 4), (932, y0 + 56), (882, y0 + 58)])), (232, 220, 186))
    c.put(c.mask(lambda p: p.ellipse(906, y0 + 22, 8, 7)), (60, 40, 30), 0.8)
    c.put(c.mask(lambda p: [p.rect(888, y, 924, y + 1.2) for y in (y0 + 36, y0 + 42, y0 + 48)]), (60, 40, 30), 0.7)
    for x in (420, 1180):
        c.put(c.mask(lambda p: p.rect(x - 2, 300, x + 2, g)), STEEL_DARK)
        c.put(c.mask(lambda p: p.rect(x - 14, 296, x + 14, 304)), STEEL_DARK)
        for dx in (-10, 10):
            c.put(c.mask(lambda p: p.ellipse(x + dx, 306, 4, 3)), GLOW)
        c.light(c.mask(lambda p: p.ellipse(x, 330, 60, 50), blur=16), GLOW, 0.2)


def lookout_post(c, k):
    """Survey decks on the slope and a shelter with a bench on the summit."""
    for x0, x1, deck in ((272, 400, 448), (448, 592, 384), (640, 816, 320)):
        for x in (x0 + 12, x1 - 12):
            ground = 512 - 0.4 * min(max(x - 480, 0), 320)
            post(c, x, deck + 5, ground, 7, TIMBER)
        left_ground = 512 - 0.4 * min(max(x0 + 12 - 480, 0), 320)
        c.put(c.mask(lambda p: p.line([(x0 + 12, left_ground - 8), (x1 - 12, deck + 9)], 4)), PLANK_DARK)
        c.put(c.mask(box(x0, deck + 4, x1, deck + 11)), PLANK_DARK)
        deck_edge(c, x0, x1, deck, PLANK_LIGHT)
    for x in (668, 720, 772):
        post(c, x, 290, 320, 5, TIMBER)
    rope_line(c, [(668, 294), (720, 294), (772, 294)], 3, PLANK_DARK)

    g = 384
    k.ground = g
    for x in (908, 1096):
        post(c, x, 279, g, 7)
    c.put(c.mask(box(896, 285, 1104, 291)), TIMBER)
    tin_roof(c, 880, 272, 1120, 286, "lookout_roof")
    c.put(c.mask(box(880, 272, 1120, 273.2)), STEEL_LIGHT)
    # The bench.
    c.put(c.mask(box(960, g - 30, 1090, g - 24)), PLANK_LIGHT)
    for x in (968, 1080):
        c.put(c.mask(box(x, g - 24, x + 6, g)), TIMBER)
    # The spyglass on its tripod.
    c.put(c.mask(lambda p: (p.line([(1180, g), (1196, g - 46)], 2), p.line([(1212, g), (1196, g - 46)], 2), p.line([(1196, g), (1196, g - 46)], 2))), TIMBER)
    c.put(c.mask(lambda p: p.line([(1180, g - 40), (1230, g - 58)], 6)), (200, 160, 80))
    c.put(c.mask(lambda p: p.line([(1180, g - 40), (1200, g - 47)], 7)), (150, 116, 60))
    # The flag: a star on red, frayed.
    c.put(c.mask(box(1470, 200, 1474, g)), STEEL_DARK)
    flag = c.mask(lambda p: p.poly([(1474, 206), (1540, 214), (1534, 232), (1544, 250), (1474, 248)]))
    c.put(flag, CLOTH_RED)
    c.tone(flag * (c.noise("flag", 6, 2, 2) - 0.5), 0.3)
    star = [(1500 + 10 * math.cos(a - math.pi / 2) * (1 if i % 2 == 0 else 0.45), 228 + 10 * math.sin(a - math.pi / 2) * (1 if i % 2 == 0 else 0.45))
            for i, a in enumerate(np.linspace(0, math.tau, 11)[:-1])]
    c.put(c.mask(lambda p: p.poly(star)), (236, 210, 120))


#: Every piece: its frame in its room, and how it is drawn.
PIECES: Dict[str, Piece] = {
    # frontier_landing_pad
    "frontier_pad_booth": Piece((624, 480, 872, 640), pad_booth),
    "frontier_pad_cargo": Piece((976, 500, 1352, 640), pad_cargo),
    "frontier_pad_freighter": Piece((1280, 280, 1990, 640), pad_freighter),
    # frontier_main_street
    "frontier_saloon_front": Piece((150, 150, 660, 608), saloon_front),
    "frontier_store_front": Piece((640, 210, 1124, 608), store_front),
    "frontier_water_tower": Piece((1040, 200, 1640, 640), water_tower),
    "frontier_livery_front": Piece((1600, 160, 2150, 608), livery_front),
    "frontier_assay_front": Piece((2140, 200, 2660, 608), assay_front),
    # frontier_wet_whistle
    "frontier_saloon_room": Piece((16, 32, 1264, 512), saloon_room),
    # frontier_livery
    "frontier_livery_room": Piece((16, 32, 1104, 512), livery_room),
    # frontier_refinery
    "frontier_refinery_tanks": Piece((780, 420, 1600, 704), refinery_tanks),
    "frontier_cracking_tower": Piece((1660, 0, 2040, 576), cracking_tower),
    # frontier_ore_corral (and the hall's copy)
    "frontier_corral_west": Piece((16, 300, 400, 576), corral_west),
    "frontier_corral_east": Piece((1200, 300, 1584, 576), corral_east),
    "frontier_corral_fence": Piece((280, 280, 1320, 576), corral_fence),
    # frontier_saddle_lookout
    "frontier_lookout_post": Piece((256, 180, 1560, 512), lookout_post),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PAL", "PIECES", "TARGETS"]
