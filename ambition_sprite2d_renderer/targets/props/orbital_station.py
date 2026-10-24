"""The orbital station of the Science dimension: its ships, its freight, and
the fittings of its decks.

Jon, 2026-10-24: a small inhabited orbital station on the gate network, "a
docking bay where conventional spacecraft visibly berth", habitation and
service, and "something tangible joining gate logistics to conventional
space travel". Freight comes through the ring, waits at customs, and goes
onto a hauler; no spaceflight engine.

Each piece is an LDtk `Prop` (decoration; a top a body stands on is a still
one-way platform the room places), except the two gates, which are the
`look` of a `LockWall` and fill its box:

- ships: ``orbital_hauler`` (the berthed freighter *Remainder*, with the
  arms of its berth) and ``orbital_shuttle`` (a small crew shuttle);
- freight: ``orbital_freight_stack`` (containers from the ring),
  ``orbital_conveyor`` (the track from the ring to the bay),
  ``orbital_consignment`` (one crate, sealed), ``orbital_customs_desk``,
  ``orbital_manifest_board``, and the gate of the quarantine pen
  ``orbital_quarantine_gate``;
- decks: ``orbital_bunks``, ``orbital_galley``, ``orbital_hydroponics``,
  ``orbital_machinery``, ``orbital_bench``, the hatch of the damaged spur
  ``orbital_spur_hatch``, and the spoke's tram car ``orbital_tram`` (the
  sheet of a moving platform: its floor is the platform's top).

Drawn in world units at `PX` pixels to the unit; the light of the decks is
from above and a little left. No drop shadows, and no portal or ring is
painted (the gate network draws its own).

Animations:

- ``idle``: 1 frame.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Tuple

import numpy as np
from PIL import Image

from ...authoring.sheet_build import build_sheet
from ._town_kit import Canvas, box, mix, scale
from .math_town_interiors import letters

#: Pixels of the frame to one world unit.
PX = 2

HULL = (176, 182, 188)
HULL_DARK = (104, 112, 124)
HULL_LIGHT = (226, 230, 234)
STEEL = (78, 92, 112)
STEEL_DARK = (36, 44, 58)
STEEL_LIGHT = (150, 170, 190)
AMBER = (246, 176, 76)
CYAN = (110, 220, 240)
RED = (214, 72, 60)
GREEN = (96, 200, 120)
NAVY = (34, 52, 96)
CREATE_A = (196, 120, 60)
CREATE_B = (70, 120, 150)
CREATE_C = (150, 160, 80)
INK = (24, 30, 40)
SCREEN = (16, 28, 40)
LEAF = (82, 156, 88)
LEAF_DARK = (44, 96, 56)
CLOTH = (120, 130, 150)
WARM = (255, 214, 150)


# ---- Shared pieces ------------------------------------------------------------------


def plate(c: Canvas, x0, y0, x1, y1, colour, tag, seams=24.0, rivets=True) -> np.ndarray:
    """A box of painted plate: seams, rivets along them, a light top edge and
    a darker foot (form, not a shadow)."""
    m = c.mask(box(x0, y0, x1, y1))
    c.put(m, colour)
    c.tone(m * (c.noise((tag, "paint"), 6, 4, 3) - 0.5), 0.10)
    if seams:
        sm = c.mask(lambda p: [p.rect(x, y0, x + 0.6, y1) for x in np.arange(x0 + seams, x1 - 1, seams)])
        c.put(sm * m, scale(colour, 0.7), 0.8)
        if rivets:
            rv = c.mask(lambda p: [p.ellipse(x + 2.0, y, 0.7) for x in np.arange(x0 + seams, x1 - 1, seams) for y in np.arange(y0 + 4, y1 - 2, 8)])
            c.put(rv * m, mix(colour, (255, 255, 255), 0.35), 0.8)
    c.put(m * c.mask(box(x0, y0, x1, y0 + 1.4)), mix(colour, (255, 255, 255), 0.35))
    c.put(m * c.mask(box(x0, y1 - 1.6, x1, y1)), scale(colour, 0.6))
    c.tone(m * np.clip((c.y - y0) / max(1.0, y1 - y0), 0, 1), -0.12)
    return m


def outline(c: Canvas, pts, width=0.9, ink=INK, a=0.9):
    c.put(c.mask(lambda p: p.line(list(pts) + [pts[0]], width)), ink, a)


def lamp(c: Canvas, x, y, colour, r=1.6, glow=6.0, k=0.6):
    c.light(c.mask(lambda p: p.ellipse(x, y, glow), blur=glow * 0.5), colour, k)
    c.put(c.mask(lambda p: p.ellipse(x, y, r)), mix(colour, (255, 255, 255), 0.4))


def hazard(c: Canvas, x0, y0, x1, y1, step=8.0, tag="hazard"):
    """Yellow and black stripes in a band."""
    m = c.mask(box(x0, y0, x1, y1))
    c.put(m, AMBER)
    stripes = ((c.x + c.y) % step) < step / 2
    c.put(m * stripes, INK, 0.9)
    return m


def screen(c: Canvas, x0, y0, x1, y1, tint=CYAN, rows=4, tag="screen"):
    m = c.mask(box(x0, y0, x1, y1))
    c.put(m, SCREEN)
    rng = c.rand(tag, "rows")
    h = (y1 - y0 - 4) / rows
    for i in range(rows):
        w = rng.uniform(0.4, 0.9) * (x1 - x0 - 4)
        c.put(c.mask(box(x0 + 2, y0 + 2 + i * h, x0 + 2 + w, y0 + 2 + i * h + h * 0.45)), tint, 0.75)
    c.light(m, tint, 0.12)
    outline(c, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 0.8, STEEL_DARK)


# ---- Ships ----------------------------------------------------------------------------


def hauler(c: Canvas, w, h):
    """The freighter *Remainder* in its berth: the drive at the left, a long
    spine of freight bays, the crew section and its windows at the right,
    held by two berth arms from the deck above. Nose to the right."""
    spine_top, spine_bot = h * 0.34, h * 0.78
    # Berth arms from the ceiling to the hull: the bay holds it, it does not float.
    for ax in (w * 0.30, w * 0.66):
        plate(c, ax - 12, 0, ax + 12, spine_top + 6, STEEL, ("arm", ax), seams=0)
        hazard(c, ax - 12, spine_top - 8, ax + 12, spine_top - 2)
        c.put(c.mask(box(ax - 20, spine_top - 2, ax + 20, spine_top + 8)), STEEL_DARK)
    # The drive: bells and the housing.
    for i, (by, r) in enumerate(((h * 0.46, 26), (h * 0.66, 26))):
        bell = [(54, by - r * 0.6), (4, by - r), (4, by + r), (54, by + r * 0.6)]
        c.put(c.mask(lambda p: p.poly(bell)), STEEL_DARK)
        c.put(c.mask(lambda p: p.poly([(10, by - r * 0.8), (6, by - r * 0.9), (6, by + r * 0.9), (10, by + r * 0.8)])), (60, 70, 90))
        outline(c, bell, 1.0)
    plate(c, 50, spine_top - 18, 150, spine_bot + 18, HULL_DARK, "drive", seams=20)
    c.put(c.mask(box(60, spine_top - 6, 140, spine_top)), AMBER, 0.8)
    # The spine and its bays: four doors with their numbers.
    plate(c, 150, spine_top, w * 0.80, spine_bot, HULL, "spine", seams=0)
    bay_w = (w * 0.80 - 160) / 4
    for i in range(4):
        x0 = 160 + i * bay_w
        door = c.mask(box(x0 + 6, spine_top + 10, x0 + bay_w - 6, spine_bot - 10))
        c.put(door, mix(HULL, HULL_DARK, 0.45))
        c.put(c.mask(lambda p: [p.rect(x0 + 6, y, x0 + bay_w - 6, y + 0.8) for y in np.arange(spine_top + 18, spine_bot - 10, 9)]), HULL_DARK, 0.8)
        outline(c, [(x0 + 6, spine_top + 10), (x0 + bay_w - 6, spine_top + 10), (x0 + bay_w - 6, spine_bot - 10), (x0 + 6, spine_bot - 10)], 1.0)
        letters(c, f"0{i + 1}", x0 + bay_w / 2, spine_top + 16, 10, INK, centre=True)
    # A stripe and the ship's name.
    c.put(c.mask(box(150, spine_bot - 8, w * 0.80, spine_bot - 3)), NAVY)
    c.put(c.mask(box(150, spine_bot + 2, w * 0.80, spine_bot + 26)), HULL)
    c.put(c.mask(box(150, spine_bot + 24, w * 0.80, spine_bot + 26)), HULL_DARK)
    letters(c, "REMAINDER", w * 0.47, spine_bot + 7, 14, NAVY, width=1.1, centre=True)
    # The crew section: a rounded nose with its windows.
    nx0 = w * 0.80
    nose = [(nx0, spine_top - 24), (w - 60, spine_top - 24), (w - 4, h * 0.56), (w - 60, spine_bot + 26), (nx0, spine_bot + 26)]
    c.put(c.mask(lambda p: p.poly(nose)), HULL_LIGHT)
    c.tone(c.mask(lambda p: p.poly(nose)) * np.clip((c.y - spine_top) / (spine_bot - spine_top + 50), 0, 1), -0.18)
    outline(c, nose, 1.2)
    win = [(w - 120, spine_top - 8), (w - 62, spine_top - 8), (w - 30, h * 0.50), (w - 120, h * 0.50)]
    c.put(c.mask(lambda p: p.poly(win)), (40, 70, 100))
    c.light(c.mask(lambda p: p.poly(win)) * np.clip((h * 0.50 - c.y) / 40, 0, 1), WARM, 0.35)
    outline(c, win, 1.0)
    for k in range(4):
        c.put(c.mask(lambda p: p.ellipse(nx0 + 20 + k * 22, h * 0.62, 5)), (40, 70, 100))
        lamp(c, nx0 + 20 + k * 22, h * 0.62, WARM, r=2.0, glow=5, k=0.3)
    outline(c, [(150, spine_top), (nx0, spine_top), (nx0, spine_bot), (150, spine_bot)], 1.2)
    # Running lights: red to port, green at the nose.
    lamp(c, 70, spine_top - 18, RED, k=0.8)
    lamp(c, w - 8, h * 0.56, GREEN, k=0.8)
    lamp(c, nx0 + 10, spine_top - 24, AMBER, k=0.6)


def shuttle(c: Canvas, w, h):
    """A small crew shuttle on a cradle: a wedge with a canopy and a ramp."""
    body = [(10, h * 0.45), (w * 0.25, h * 0.20), (w * 0.80, h * 0.18), (w - 4, h * 0.42), (w - 10, h * 0.62), (14, h * 0.66)]
    m = c.mask(lambda p: p.poly(body))
    c.put(m, HULL_LIGHT)
    c.tone(m * np.clip((c.y - h * 0.2) / (h * 0.5), 0, 1), -0.25)
    c.put(m * c.mask(box(0, h * 0.50, w, h * 0.54)), NAVY)
    canopy = [(w * 0.62, h * 0.22), (w * 0.80, h * 0.20), (w * 0.94, h * 0.40), (w * 0.66, h * 0.40)]
    c.put(c.mask(lambda p: p.poly(canopy)), (40, 70, 100))
    c.light(c.mask(lambda p: p.poly(canopy)) * (c.y < h * 0.3), (200, 230, 255), 0.25)
    outline(c, canopy, 0.9)
    outline(c, body, 1.1)
    letters(c, "SC-3", w * 0.38, h * 0.30, 9, NAVY, centre=True)
    # The cradle under it, and the ramp down.
    plate(c, w * 0.15, h * 0.66, w * 0.85, h * 0.80, STEEL, "cradle", seams=16)
    for x in (w * 0.2, w * 0.78):
        c.put(c.mask(box(x - 4, h * 0.80, x + 4, h)), STEEL_DARK)
    hazard(c, w * 0.15, h * 0.80, w * 0.85, h * 0.84)
    lamp(c, w - 6, h * 0.42, GREEN, k=0.7)
    lamp(c, 12, h * 0.46, RED, k=0.7)


# ---- Freight -------------------------------------------------------------------------


def container(c: Canvas, x0, y0, x1, y1, colour, label, tag):
    m = plate(c, x0, y0, x1, y1, colour, tag, seams=0)
    ribs = c.mask(lambda p: [p.rect(x, y0 + 2, x + 1.2, y1 - 2) for x in np.arange(x0 + 4, x1 - 2, 5)])
    c.put(ribs * m, scale(colour, 0.75), 0.8)
    c.put(c.mask(box(x0 + 4, y0 + 4, x0 + 4 + min(40, (x1 - x0) * 0.5), y0 + 14)), HULL_LIGHT, 0.9)
    letters(c, label, x0 + 6, y0 + 6, 6, INK)
    outline(c, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 1.0)


def freight_stack(c: Canvas, w, h):
    """Containers that came through the ring, stacked for the hauler."""
    container(c, 0, h * 0.5, w * 0.55, h, CREATE_A, "TNG-41", "a")
    container(c, w * 0.55, h * 0.5, w, h, CREATE_B, "GNS-07", "b")
    container(c, w * 0.12, 0, w * 0.70, h * 0.5, CREATE_C, "LGL-12", "c")


def consignment(c: Canvas, w, h):
    """One sealed crate, its quarantine tag on its face."""
    container(c, 0, 0, w, h, CREATE_B, "0447", "consignment")
    c.put(c.mask(box(w * 0.55, h * 0.35, w * 0.9, h * 0.75)), (240, 236, 220))
    c.put(c.mask(box(w * 0.55, h * 0.35, w * 0.9, h * 0.45)), RED)
    c.put(c.mask(lambda p: [p.line([(w * 0.6, y), (w * 0.85, y)], 0.6) for y in (h * 0.55, h * 0.65)]), INK)


def conveyor(c: Canvas, w, h):
    """The freight track from the ring to the hauler's bay: a belt on legs,
    rollers along it, an arrow to the bay."""
    belt_top = h * 0.25
    plate(c, 0, belt_top, w, belt_top + 14, STEEL, "track", seams=32)
    c.put(c.mask(box(0, belt_top - 4, w, belt_top)), (40, 40, 44))
    c.put(c.mask(lambda p: [p.rect(x, belt_top - 4, x + 1.2, belt_top) for x in np.arange(0, w, 6)]), (80, 80, 86))
    for x in np.arange(10, w - 6, 48):
        c.put(c.mask(box(x, belt_top + 14, x + 8, h)), STEEL_DARK)
    hazard(c, 0, belt_top + 14, w, belt_top + 18)
    for x in np.arange(30, w - 20, 96):
        c.put(c.mask(lambda p: p.poly([(x, belt_top + 4), (x + 12, belt_top + 7), (x, belt_top + 10)])), AMBER)


def customs_desk(c: Canvas, w, h):
    """The customs and quarantine desk: a counter with a scanner hood, a
    screen, a stamp and the sign over it."""
    top = h * 0.45
    plate(c, 0, top, w, h, (60, 78, 102), "desk", seams=48)
    c.put(c.mask(box(-4, top - 4, w + 4, top + 2)), STEEL_LIGHT)
    hazard(c, 0, h - 6, w, h)
    letters(c, "CUSTOMS", w * 0.5, top + 12, 9, HULL_LIGHT, centre=True)
    letters(c, "QUARANTINE", w * 0.5, top + 26, 7, AMBER, centre=True)
    # The scanner hood at the left, its light.
    c.put(c.mask(lambda p: [p.rect(8, top - 56, 52, top - 48), p.rect(8, top - 56, 13, top - 4), p.rect(47, top - 56, 52, top - 4)]), STEEL)
    c.light(c.mask(box(13, top - 48, 47, top - 4)), CYAN, 0.25)
    lamp(c, 30, top - 52, CYAN, k=0.7)
    # The screen on its arm, and the stamp.
    c.put(c.mask(box(w * 0.66, top - 30, w * 0.66 + 3, top)), STEEL_DARK)
    screen(c, w * 0.58, top - 52, w * 0.86, top - 28, tag="desk screen")
    c.put(c.mask(box(w * 0.40, top - 10, w * 0.46, top - 4)), RED)
    c.put(c.mask(box(w * 0.42, top - 18, w * 0.44, top - 10)), INK)


def manifest_board(c: Canvas, w, h):
    """The manifest board over the gate deck: what came through the ring,
    what goes on the hauler, and what customs holds."""
    plate(c, 0, 0, w, h, STEEL_DARK, "board", seams=0, rivets=False)
    letters(c, "MANIFEST", 10, 8, 10, AMBER, width=1.1)
    letters(c, "RING TO BAY", w - 82, 10, 6, CYAN)
    rows = [
        ("TNG-41", "LENSES", "LOADED", GREEN),
        ("GNS-07", "SEED STOCK", "LOADED", GREEN),
        ("LGL-12", "MAIL", "ON DECK", CYAN),
        ("0447", "SURVEY OPTICS", "AT CUSTOMS", RED),
        ("CTD-02", "PARTS", "BACKLOG", AMBER),
    ]
    rh = (h - 36) / len(rows)
    for i, (code, what, status, colour) in enumerate(rows):
        y = 30 + i * rh
        c.put(c.mask(box(6, y, w - 6, y + rh - 3)), (22, 30, 44))
        letters(c, code, 12, y + 4, 6, HULL_LIGHT)
        letters(c, what, 60, y + 4, 6, HULL_LIGHT)
        letters(c, status, w - 70, y + 4, 6, colour)
        lamp(c, w - 12, y + rh / 2 - 1, colour, r=1.6, glow=4, k=0.5)
    outline(c, [(0, 0), (w, 0), (w, h), (0, h)], 1.2)


def quarantine_gate(c: Canvas, w, h):
    """The gate of the quarantine pen: a mesh in a frame of hazard stripes,
    with its sign. It fills its wall's box."""
    plate(c, 0, 0, w, h, STEEL, "qframe", seams=0)
    mesh_box = (6, 14, w - 6, h - 6)
    c.put(c.mask(box(*mesh_box)), (30, 38, 52), 0.55)
    mesh = (np.abs(((c.x + c.y) % 6.0) - 3.0) < 0.5) | (np.abs(((c.x - c.y) % 6.0) - 3.0) < 0.5)
    c.put(c.mask(box(*mesh_box)) * mesh, STEEL_LIGHT, 0.9)
    hazard(c, 0, 0, w, 12)
    c.put(c.mask(box(w * 0.2, h * 0.42, w * 0.8, h * 0.56)), (240, 236, 220))
    letters(c, "HOLD", w * 0.5, h * 0.44, min(10, w * 0.11), RED, centre=True)
    lamp(c, w - 8, 6, RED, k=0.8)


def spur_hatch(c: Canvas, w, h):
    """The hatch to the damaged spur: a heavy door, its wheel, its stripes and
    a red lamp. It fills its wall's box."""
    plate(c, 0, 0, w, h, (90, 70, 64), "hatch", seams=0)
    hazard(c, 0, 0, w, 10)
    hazard(c, 0, h - 10, w, h)
    cx, cy = w / 2, h * 0.45
    c.put(c.mask(lambda p: p.ring(cx, cy, w * 0.28, 3.0)), STEEL_LIGHT)
    c.put(c.mask(lambda p: [p.line([(cx - w * 0.28, cy), (cx + w * 0.28, cy)], 2.0), p.line([(cx, cy - w * 0.28), (cx, cy + w * 0.28)], 2.0)]), STEEL_LIGHT)
    c.put(c.mask(box(w * 0.15, h * 0.68, w * 0.85, h * 0.80)), (240, 236, 220))
    letters(c, "SPUR", w * 0.5, h * 0.70, min(8, w * 0.1), RED, centre=True)
    lamp(c, w / 2, 16, RED, k=0.9)


# ---- Decks ----------------------------------------------------------------------------


def bunks(c: Canvas, w, h):
    """Two tiers of crew bunks with curtains, lockers between them."""
    for tier, y0 in enumerate((0, h * 0.5)):
        plate(c, 0, y0, w * 0.72, y0 + h * 0.46, (64, 80, 100), ("bunk", tier), seams=0)
        c.put(c.mask(box(6, y0 + 8, w * 0.72 - 6, y0 + h * 0.46 - 6)), (28, 34, 46))
        c.put(c.mask(box(8, y0 + h * 0.30, w * 0.72 - 8, y0 + h * 0.40)), (190, 196, 210))
        curtain = c.mask(box(w * 0.36, y0 + 8, w * 0.72 - 6, y0 + h * 0.46 - 6))
        c.put(curtain, CLOTH)
        c.tone(curtain * (np.abs((c.x % 6.0) - 3.0) / 3.0 - 0.5), 0.3)
        lamp(c, 14, y0 + 14, WARM, r=1.4, glow=10, k=0.35)
    plate(c, w * 0.74, 0, w, h, STEEL, "lockers", seams=w * 0.13)
    for y in (h * 0.2, h * 0.7):
        c.put(c.mask(box(w * 0.78, y, w * 0.80, y + 10)), STEEL_LIGHT)


def galley(c: Canvas, w, h):
    """The galley: a counter, a cooker with its pan, cupboards, a menu screen."""
    top = h * 0.55
    plate(c, 0, top, w, h, (150, 154, 160), "counter", seams=48)
    c.put(c.mask(box(-2, top - 3, w + 2, top + 1)), HULL_LIGHT)
    plate(c, 4, 0, w - 4, h * 0.28, (120, 128, 140), "cupboards", seams=48)
    c.put(c.mask(box(w * 0.55, top - 10, w * 0.80, top - 3)), STEEL_DARK)
    c.put(c.mask(lambda p: p.ellipse(w * 0.67, top - 12, 16, 4)), (60, 60, 66))
    for k in range(3):
        c.light(c.mask(lambda p: p.ellipse(w * 0.62 + k * 6, top - 22 - k * 6, 4, 6), blur=2.0), (230, 230, 230), 0.25)
    screen(c, w * 0.08, h * 0.32, w * 0.40, h * 0.50, tint=AMBER, rows=3, tag="menu")
    for k, colour in enumerate(((210, 90, 70), (230, 200, 90), (90, 160, 110))):
        c.put(c.mask(lambda p: p.ellipse(w * 0.46 + k * 9, top - 5, 3.5)), colour)


def hydroponics(c: Canvas, w, h):
    """Racks of growing trays under grow lights: the station's own greens."""
    for i, y0 in enumerate((h * 0.08, h * 0.55)):
        c.put(c.mask(box(0, y0, w, y0 + 4)), (200, 120, 230), 0.7)
        c.light(c.mask(box(0, y0 + 4, w, y0 + h * 0.36), blur=3.0), (220, 140, 255), 0.18)
        tray_y = y0 + h * 0.36
        plate(c, 0, tray_y, w, tray_y + 8, (200, 204, 210), ("tray", i), seams=0)
        rng = c.rand("leaves", i)
        leaves = c.mask(lambda p: [p.ellipse(x, tray_y - rng.uniform(4, 14), rng.uniform(4, 8), rng.uniform(3, 7)) for x in np.arange(6, w - 4, 7)])
        c.put(leaves, LEAF)
        c.tone(leaves * (c.noise(("leafn", i), 20, 6, 2) - 0.5), 0.4)
        c.put(leaves * (c.y < tray_y - 10), mix(LEAF, (220, 255, 200), 0.3), 0.5)
    for x in (2, w - 6):
        c.put(c.mask(box(x, 0, x + 4, h)), STEEL)


def machinery(c: Canvas, w, h):
    """The service deck's plant: a pump with its pipes, a tank, a panel of
    breakers with lights."""
    plate(c, w * 0.05, h * 0.25, w * 0.42, h, STEEL, "tank", seams=0)
    c.put(c.mask(lambda p: p.ellipse(w * 0.235, h * 0.25, w * 0.185, 10)), STEEL_LIGHT)
    for y in (h * 0.45, h * 0.70):
        c.put(c.mask(box(w * 0.05, y, w * 0.42, y + 4)), STEEL_DARK)
    pipes = c.mask(lambda p: [p.line([(w * 0.42, h * 0.40), (w * 0.60, h * 0.40), (w * 0.60, h * 0.10), (w, h * 0.10)], 6), p.line([(w * 0.42, h * 0.80), (w * 0.95, h * 0.80)], 5)])
    c.put(pipes, (120, 108, 90))
    c.put(pipes * (c.mask(lambda p: [p.line([(w * 0.42, h * 0.40 - 2), (w * 0.60, h * 0.40 - 2)], 1.5), p.line([(w * 0.60, h * 0.10 - 2), (w, h * 0.10 - 2)], 1.5)])), (190, 176, 150), 0.8)
    plate(c, w * 0.66, h * 0.30, w * 0.96, h * 0.72, (52, 62, 80), "breakers", seams=0)
    for i in range(4):
        for j in range(2):
            x, y = w * 0.70 + i * w * 0.065, h * 0.38 + j * h * 0.16
            c.put(c.mask(box(x, y, x + w * 0.04, y + h * 0.10)), (30, 36, 48))
            lamp(c, x + w * 0.02, y + 3, GREEN if (i + j) % 3 else AMBER, r=1.2, glow=3, k=0.6)
    hazard(c, w * 0.05, h - 6, w * 0.42, h)


#: The tram car's floor, in world units of its piece: the platform's top
#: (`TRAM_FLOOR_Y`) and the part of the car's width it covers.
TRAM_FLOOR_Y = 88
TRAM_FLOOR_SPAN = (16, 208)


def tram(c: Canvas, w, h):
    """The spoke's tram car, seen from the side: its floor is the platform a
    body stands on, the back wall and roof of the car behind the body, the
    guides that hold it to the spoke's rail under it."""
    x0, x1 = TRAM_FLOOR_SPAN
    floor = TRAM_FLOOR_Y
    # The back wall, with its windows onto space.
    plate(c, x0 + 4, 20, x1 - 4, floor, (96, 110, 130), "tram wall", seams=0)
    for k in range(3):
        wx = x0 + 18 + k * 60
        win = c.mask(box(wx, 30, wx + 46, 62))
        c.put(win, (16, 24, 44))
        c.light(win * np.clip((c.y - 44) / 18, 0, 1), (120, 186, 255), 0.35)
        outline(c, [(wx, 30), (wx + 46, 30), (wx + 46, 62), (wx, 62)], 0.9, STEEL_DARK)
    c.put(c.mask(box(x0 + 4, 66, x1 - 4, 70)), AMBER, 0.9)
    # The roof, its ends rounded, and the end posts.
    roof = c.mask(lambda p: [p.rect(x0 + 8, 8, x1 - 8, 22), p.ellipse(x0 + 8, 15, 8, 7), p.ellipse(x1 - 8, 15, 8, 7)])
    c.put(roof, HULL_LIGHT)
    c.tone(roof * np.clip((c.y - 8) / 14, 0, 1), -0.2)
    for px in (x0, x1 - 8):
        c.put(c.mask(box(px, 14, px + 8, floor)), STEEL)
    lamp(c, x1 - 4, 30, GREEN, k=0.7)
    lamp(c, x0 + 4, 30, RED, k=0.7)
    # The floor and the guides under it.
    plate(c, x0, floor, x1, floor + 10, STEEL_DARK, "tram floor", seams=0)
    hazard(c, x0, floor, x1, floor + 3)
    for gx in (x0 + 30, x1 - 54):
        c.put(c.mask(box(gx, floor + 10, gx + 24, h - 2)), STEEL)
        c.put(c.mask(lambda p: p.ellipse(gx + 12, h - 6, 5)), STEEL_LIGHT)


def bench(c: Canvas, w, h):
    """A bench before the big window, its seat padded."""
    plate(c, 0, h * 0.35, w, h * 0.60, (60, 70, 90), "seat", seams=0)
    c.put(c.mask(box(2, h * 0.30, w - 2, h * 0.42)), (120, 60, 60))
    for x in (8, w - 16):
        c.put(c.mask(box(x, h * 0.60, x + 8, h)), STEEL_DARK)


#: Each piece: (width, height) in world units, and how it is drawn.
PIECES: Dict[str, Tuple[float, float, Callable]] = {
    "orbital_hauler": (900, 300, hauler),
    "orbital_shuttle": (300, 140, shuttle),
    "orbital_freight_stack": (180, 120, freight_stack),
    "orbital_consignment": (72, 52, consignment),
    "orbital_conveyor": (480, 48, conveyor),
    "orbital_customs_desk": (200, 110, customs_desk),
    "orbital_manifest_board": (300, 150, manifest_board),
    "orbital_quarantine_gate": (96, 144, quarantine_gate),
    "orbital_spur_hatch": (64, 128, spur_hatch),
    "orbital_bunks": (220, 160, bunks),
    "orbital_galley": (260, 120, galley),
    "orbital_hydroponics": (240, 140, hydroponics),
    "orbital_machinery": (300, 200, machinery),
    "orbital_bench": (160, 40, bench),
    "orbital_tram": (224, 112, tram),
}


#: Room round each piece in the frame, so a stroke on its edge is not cut.
MARGIN = 6


def _frame_size(name: str) -> Tuple[int, int]:
    w, h, _ = PIECES[name]
    return (int((w + 2 * MARGIN) * PX), int((h + 2 * MARGIN) * PX))


def _draw(name: str) -> Image.Image:
    w, h, draw = PIECES[name]
    c = Canvas(name, w + 2 * MARGIN, h + 2 * MARGIN, origin=(-MARGIN, -MARGIN), ppu=PX)
    draw(c, w, h)
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
        return {"anchors": {"foot": {"x": fw / 2, "y": float(fh - MARGIN * PX)}}, "forward": {"x": 0.0, "y": -1.0}, "angle_deg": 0.0}

    def render(out_dir: str | Path, **opts) -> List[Path]:
        del opts
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
    return {
        "actor": {"character_id": f"prop_{name}", "display_name": name.replace("_", " ").title()},
        "body": {"body_plan": "Prop", "body_kind": "Scenery", "mass_class": "Heavy", "locomotion_hint": "Static", "traits": ["prop", "scenery"]},
        "brain": {"default_preset": "stand_still"},
        "actions": {"default_preset": "peaceful"},
        "animation_bindings": {"default": {"animation": "idle", "events": []}},
        "tags": ["prop", "scenery", "orbital"],
    }


TARGETS = {name: {"render": _renderer(name), "actor_metadata": _actor(name)} for name in PIECES}

__all__ = ["MARGIN", "PIECES", "PX", "TARGETS"]
