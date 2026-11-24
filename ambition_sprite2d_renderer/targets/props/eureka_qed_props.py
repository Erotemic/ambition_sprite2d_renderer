"""QED-TV, Eureka's television station (gate address SCIENCE): its front on
the lecture hall's terrace and its rooms inside, where Will Force, the
Science Horse, reads the evening news.

The rooms are `eureka_quad` and `eureka_qed_studios`
(`game/ambition_map_assets/ambition_content/generators/eureka/make_specs.py`).
Each piece is drawn in its room's own coordinates (`_district_props`) on the
walk lines that the room places:

- `quad_qed_front` (the quad): a cream studio block of the 1970s on the
  terrace (y 576, x 1620..2030), west of the observatory. A band of studio
  windows, a lit ON AIR box over the glass doors (the door zone, x
  1660..1708), the station's sign (a horseshoe magnet with its field lines,
  and QED-TV in lit letters), a dish on the roof and a red-and-white
  transmitter mast with a beacon.
- `qed_reception`: wood panels under burgundy and gold paper, the front desk
  (y 600, x 180..330) with a Petri dish on it, the waiting couch (y 608, x
  440..560), a shelf of the anchor's three EMMC2 awards and a wall of his
  portraits.
- `qed_studio`: the set. The painted backdrop of Eureka and its tether
  behind the anchor desk (y 584, x 780..960), two pedestal cameras with
  teleprompters, the lighting grid (y 340, x 600..1580; its ladder at x
  600..632) with its lamps on the desk, the ON AIR light, and the
  demonstration area: a Van de Graaff generator, the lab bench (y 592, x
  1320..1520) and a board that says what one horsepower is.
- `qed_production`: the production room behind its partition: a wall of
  monitors, the vision mixer (y 600, x 1700..1940), and the weather centre's
  green wall.

Animations: ``idle``, 1 frame each. No drop shadows.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from ._district_props import Piece, targets
from ._town_kit import box, mix, scale
from .eureka_props import BRASS, GOLD, NAVY, OAK, OAK_DARK, OAK_LIGHT, PAL, Batch, pendant
from .math_town_interiors import letters

# ---- The numbers of the rooms (`make_specs.py`) ------------------------------------------------

TERRACE = 576
FRONT = (1620, 2030)
FRONT_TOP = 352
QED_DOOR = (1660, 1708)

FLOOR, CEILING = 640, 32
DESK = (180, 330, 600)
COUCH = (440, 560, 608)
ANCHOR_DESK = (780, 960, 584)
GRID = (600, 1580, 340)
LADDER = (600, 632)
BENCH = (1320, 1520, 592)
CONSOLE = (1700, 1940, 600)
PARTITION = 1600

# ---- The station's colours ----------------------------------------------------------------------

CREAM = (236, 226, 204)
CREAM_DARK = (196, 184, 160)
BURGUNDY = (122, 31, 46)
BURGUNDY_DARK = (82, 20, 32)
TIE_BLUE = (47, 90, 168)
CHROME = (196, 204, 212)
CHROME_DARK = (110, 118, 128)
GLASS = (120, 170, 200)
GLASS_DARK = (40, 64, 86)
ON_AIR = (236, 54, 48)
WARM = (255, 214, 150)
STUDIO_WALL = (34, 36, 46)
STUDIO_FLOOR = (52, 52, 60)
MUSTARD = (201, 154, 60)
ORANGE = (214, 110, 48)
WALNUT = (96, 62, 40)
KEY_GREEN = (64, 176, 84)
SCREEN = (24, 30, 36)
INK = (30, 30, 36)


def magnet(c, cx, cy, r, w=None):
    """The station's mark: a horseshoe magnet, its legs down, red with
    silver poles, and the field lines looping out between the poles."""
    w = w or r * 0.42
    arc = c.mask(lambda p: (p.ring(cx, cy, r, w), ))
    c.put(arc * (c.y <= cy).astype(np.float32), ON_AIR)
    legs = c.mask(lambda p: (p.rect(cx - r - w / 2, cy, cx - r + w / 2, cy + r * 0.9), p.rect(cx + r - w / 2, cy, cx + r + w / 2, cy + r * 0.9)))
    c.put(legs, ON_AIR)
    c.put(c.mask(lambda p: (p.rect(cx - r - w / 2, cy + r * 0.62, cx - r + w / 2, cy + r * 0.9), p.rect(cx + r - w / 2, cy + r * 0.62, cx + r + w / 2, cy + r * 0.9))), CHROME)
    lines = c.mask(lambda p: [p.ring(cx, cy + r * 0.9, rr, max(0.6, r * 0.05)) for rr in (r * 0.35, r * 0.6)])
    c.put(lines * (c.y >= cy + r * 0.9).astype(np.float32), GOLD, 0.9)


def qed_sign(c, x0, y0, x1, y1):
    """The station's sign: a burgundy panel, the magnet, and QED-TV lit."""
    c.put(c.mask(box(x0 - 3, y0 - 3, x1 + 3, y1 + 3)), CHROME_DARK)
    c.put(c.mask(box(x0, y0, x1, y1)), BURGUNDY)
    c.put(c.mask(box(x0, y0, x1, y0 + 2)), mix(BURGUNDY, WARM, 0.4))
    h = y1 - y0
    magnet(c, x0 + h * 0.55, y0 + h * 0.38, h * 0.26)
    tx = x0 + h * 1.05
    letters(c, "QED-TV", tx, y0 + h * 0.22, h * 0.56, WARM, width=1.1)
    c.light(c.mask(box(tx - 4, y0 + h * 0.15, x1 - 6, y1 - h * 0.15), blur=4), WARM, 0.35)


def on_air(c, cx, cy, w=46, h=16, lit=True):
    c.put(c.mask(box(cx - w / 2 - 2, cy - h / 2 - 2, cx + w / 2 + 2, cy + h / 2 + 2)), INK)
    c.put(c.mask(box(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)), ON_AIR if lit else scale(ON_AIR, 0.4))
    letters(c, "ON AIR", cx, cy - h * 0.3, h * 0.6, (255, 240, 230), width=1.0, centre=True)
    if lit:
        c.light(c.mask(lambda p: p.ellipse(cx, cy, w * 0.9, h * 1.4), blur=8), ON_AIR, 0.45)


# ---- The front on the quad ----------------------------------------------------------------------


def front(c, k):
    x0, x1 = FRONT
    top, g = FRONT_TOP, TERRACE
    d0, d1 = QED_DOOR
    # The transmitter mast behind the roof: a lattice in red and white bands,
    # and its beacon.
    mx, m_top = 1960, 70
    bands = c.mask(lambda p: [p.poly([(mx - 14 + (y - m_top) * 0.0, y), (mx + 14, y), (mx + 14, y + 24), (mx - 14, y + 24)]) for y in range(m_top + 10, top, 48)])
    lattice = c.mask(lambda p: (p.line([(mx - 14, top), (mx - 4, m_top + 10)], 2.4), p.line([(mx + 14, top), (mx + 4, m_top + 10)], 2.4),
                                [p.line([(mx - 13 + (y - top) / (m_top - top) * 9, y), (mx + 13 - (y - m_top - 24) / (top - m_top) * 9, y - 24)], 1.2) for y in range(top, m_top + 30, -24)]))
    c.put(lattice, (238, 236, 232))
    c.put(lattice * bands, ON_AIR)
    c.put(c.mask(lambda p: p.rect(mx - 1.2, m_top - 30, mx + 1.2, m_top + 10)), CHROME_DARK)
    c.put(c.mask(lambda p: p.ellipse(mx, m_top - 32, 4.2)), ON_AIR)
    c.light(c.mask(lambda p: p.ellipse(mx, m_top - 32, 16), blur=6), ON_AIR, 0.6)
    # Its signal: three arcs either side of the beacon.
    for r in (14, 24, 34):
        ring = c.mask(lambda p, r=r: p.ring(mx, m_top - 32, r, 1.4))
        c.put(ring * (np.abs(c.x - mx) > r * 0.55).astype(np.float32) * (c.y < m_top - 22).astype(np.float32), WARM, 0.6)
    # The block: cream render, a darker plinth, a parapet.
    c.put(c.mask(box(x0, top, x1, g)), CREAM)
    c.tone(c.mask(box(x0, top, x1, g)) * (c.noise(("qed_front", "render"), 20, 8, 2) - 0.5), 0.06)
    c.put(c.mask(box(x0, g - 22, x1, g)), CREAM_DARK)
    c.put(c.mask(box(x0 - 6, top - 10, x1 + 6, top + 4)), CREAM_DARK)
    c.put(c.mask(box(x0 - 6, top - 10, x1 + 6, top - 8)), mix(CREAM, (255, 255, 255), 0.5))
    # The dish on the roof, looking up at the station.
    dx, dy = 1700, top - 10
    c.put(c.mask(lambda p: (p.rect(dx - 3, dy - 30, dx + 3, dy), p.rect(dx - 12, dy - 6, dx + 12, dy))), CHROME_DARK)
    c.put(c.mask(lambda p: p.poly([(dx - 30, dy - 58), (dx + 18, dy - 74), (dx + 26, dy - 52), (dx - 4, dy - 26)])), CHROME)
    c.put(c.mask(lambda p: p.line([(dx - 2, dy - 46), (dx + 14, dy - 82)], 1.6)), CHROME_DARK)
    # The band of studio windows, a burgundy stripe under it.
    c.put(c.mask(box(x0 + 12, top + 92, x1 - 12, top + 100)), BURGUNDY)
    for wx in range(x0 + 140, x1 - 40, 54):
        w = c.mask(box(wx, top + 108, wx + 42, top + 160))
        c.put(w, GLASS_DARK)
        c.light(w * np.clip((c.y - (top + 108)) / 52, 0, 1), WARM, 0.35)
        c.put(c.mask(box(wx, top + 108, wx + 42, top + 110)), CHROME)
    # The sign over the windows.
    qed_sign(c, x0 + 40, top + 10, x0 + 300, top + 64)
    # The way in: an awning, glass doors in chrome, the ON AIR box.
    c.put(c.mask(box(d0 - 18, g - 112, d1 + 18, g)), CHROME_DARK)
    glass = c.mask(box(d0 - 10, g - 104, d1 + 10, g))
    c.put(glass, GLASS)
    c.light(glass * np.clip((c.y - (g - 104)) / 104, 0, 1), WARM, 0.45)
    c.put(c.mask(lambda p: (p.rect((d0 + d1) / 2 - 1.5, g - 104, (d0 + d1) / 2 + 1.5, g), p.rect(d0 - 10, g - 60, d1 + 10, g - 57))), CHROME_DARK)
    c.put(c.mask(lambda p: p.poly([(d0 - 30, g - 124), (d1 + 30, g - 124), (d1 + 22, g - 112), (d0 - 22, g - 112)])), BURGUNDY)
    on_air(c, (d0 + d1) / 2, g - 138)
    # A planter either side of the doors.
    for px in (d0 - 40, d1 + 40):
        c.put(c.mask(box(px - 12, g - 26, px + 12, g)), CREAM_DARK)
        c.put(c.mask(lambda p, px=px: [p.ellipse(px + dx2, g - 34 - abs(dx2) * 0.3, 8) for dx2 in (-6, 0, 6)]), (70, 122, 64))


# ---- Inside: the reception ----------------------------------------------------------------------


def wallpaper(c, x0, y0, x1, y1, tag):
    """Burgundy paper with gold circles in rows: the station's 1970s."""
    m = c.mask(box(x0, y0, x1, y1))
    c.put(m, BURGUNDY_DARK)
    c.put(m * c.mask(lambda p: [p.ring(x, y, 9, 1.6) for x in range(int(x0) + 12, int(x1), 32) for y in range(int(y0) + 14, int(y1), 32)]), MUSTARD, 0.7)
    c.put(m * c.mask(lambda p: [p.ellipse(x + 16, y + 16, 3) for x in range(int(x0) + 12, int(x1), 32) for y in range(int(y0) + 14, int(y1), 32)]), ORANGE, 0.7)
    c.tone(m * (c.noise((tag, "paper"), 10, 6, 2) - 0.5), 0.08)


def wainscot(c, x0, x1, y0):
    m = c.mask(box(x0, y0, x1, FLOOR))
    c.put(m, WALNUT)
    c.tone(m * (c.noise(("qed", "grain", x0), 4, 30, 2) - 0.5), 0.18)
    c.put(c.mask(lambda p: [p.rect(x, y0 + 8, x + 1.4, FLOOR - 6) for x in range(int(x0) + 40, int(x1), 48)]), scale(WALNUT, 0.7))
    c.put(c.mask(box(x0, y0, x1, y0 + 5)), OAK_LIGHT)


def award(c, x, base):
    """An EMMC2: a gold figure on a plinth, holding up an atom."""
    c.put(c.mask(box(x - 7, base - 8, x + 7, base)), INK)
    c.put(c.mask(lambda p: (p.poly([(x - 4, base - 8), (x + 4, base - 8), (x + 2, base - 26), (x - 2, base - 26)]), p.ellipse(x, base - 30, 3.4))), GOLD)
    c.put(c.mask(lambda p: (p.line([(x - 2, base - 22), (x - 6, base - 38)], 1.6), p.line([(x + 2, base - 22), (x + 6, base - 38)], 1.6))), GOLD)
    c.put(c.mask(lambda p: (p.ring(x, base - 44, 8, 1.0), p.ellipse(x, base - 44, 2.4))), mix(GOLD, (255, 255, 240), 0.3))
    c.light(c.mask(lambda p: p.ellipse(x, base - 36, 12), blur=4), WARM, 0.3)


def portrait(c, x, y, w=54, h=66, pose=0):
    """A framed photograph of Will Force: a horse head with the hair, a
    burgundy suit, a blue bow tie; the pose differs a little."""
    c.put(c.mask(box(x - 4, y - 4, x + w + 4, y + h + 4)), GOLD)
    c.put(c.mask(box(x, y, x + w, y + h)), (70, 96, 132) if pose % 2 else (64, 80, 64))
    cx = x + w / 2 + (pose - 1) * 4
    c.put(c.mask(lambda p: p.poly([(cx - 22, y + h), (cx - 18, y + h - 22), (cx + 18, y + h - 22), (cx + 22, y + h)])), BURGUNDY)
    c.put(c.mask(lambda p: p.poly([(cx - 5, y + h - 22), (cx + 5, y + h - 22), (cx, y + h - 10)])), (240, 236, 226))
    c.put(c.mask(lambda p: (p.ellipse(cx - 4, y + h - 21, 4, 2.4), p.ellipse(cx + 4, y + h - 21, 4, 2.4))), TIE_BLUE)
    c.put(c.mask(lambda p: p.poly([(cx - 9, y + h - 24), (cx - 11, y + 22), (cx - 4, y + 12), (cx + 8, y + 14), (cx + 16, y + 40), (cx + 12, y + h - 26), (cx + 2, y + h - 22)])), (138, 74, 40))
    c.put(c.mask(lambda p: p.ellipse(cx + 1, y + 16, 14, 7)), (58, 36, 22))
    c.put(c.mask(lambda p: p.ellipse(cx + 9, y + 39, 6, 2.2)), (58, 36, 22))
    c.put(c.mask(lambda p: p.ellipse(cx + 2, y + 24, 1.6)), INK)
    c.put(c.mask(box(x, y, x + w, y + 8)), (255, 255, 255), 0.12)


def reception(c, k):
    x0, x1 = 16, PARTITION_STUDIO
    wallpaper(c, x0, CEILING, x1, 470, "qed_reception")
    wainscot(c, x0, x1, 470)
    c.put(c.mask(box(x0, CEILING, x1, CEILING + 14)), CREAM_DARK)
    for lx in (150, 380):
        pendant(c, lx, CEILING + 14, 60)
    # The station's sign over the desk.
    qed_sign(c, 150, 170, 380, 228)
    # The shelf of awards over the sign's foot.
    c.put(c.mask(box(176, 300, 336, 306)), OAK)
    for ax in (210, 256, 302):
        award(c, ax, 300)
    # The wall of portraits over the couch.
    for i, (px, py) in enumerate(((410, 262), (480, 300), (430, 360))):
        portrait(c, px, py, pose=i)
    # The front desk: walnut, curved at the front, the magnet on it; a
    # Petri dish and a bell on its top.
    d0, d1, dy = DESK
    c.put(c.mask(lambda p: p.poly([(d0, dy), (d1, dy), (d1 + 6, FLOOR), (d0 - 6, FLOOR)])), WALNUT)
    c.put(c.mask(box(d0 - 4, dy, d1 + 4, dy + 6)), OAK_LIGHT)
    c.put(c.mask(box(d0 + 10, dy + 14, d1 - 10, dy + 18)), MUSTARD)
    magnet(c, (d0 + d1) / 2, dy + 20, 7)
    c.put(c.mask(lambda p: p.ellipse(d0 + 28, dy - 2.5, 12, 3)), (220, 236, 240), 0.85)
    c.put(c.mask(lambda p: [p.ellipse(d0 + 24 + i * 4, dy - 3, 1.6) for i in range(3)]), (150, 196, 90))
    c.put(c.mask(lambda p: (p.ellipse(d1 - 24, dy - 4, 5, 4), p.rect(d1 - 30, dy - 1, d1 - 18, dy))), BRASS)
    # The waiting couch: orange, low, on chrome feet.
    c0, c1, cy = COUCH
    c.put(c.mask(lambda p: (p.rect(c0, cy - 20, c1, cy + 12), p.ellipse(c0 + 4, cy - 2, 8, 16), p.ellipse(c1 - 4, cy - 2, 8, 16))), ORANGE)
    c.put(c.mask(box(c0 + 6, cy, c1 - 6, cy + 3)), mix(ORANGE, (255, 240, 210), 0.35))
    c.put(c.mask(lambda p: [p.rect(x, cy + 12, x + 3, FLOOR) for x in (c0 + 10, c1 - 13)]), CHROME)
    # The floor: a brown carpet.
    c.put(c.mask(box(x0, FLOOR - 2, x1, FLOOR)), scale(WALNUT, 0.6))


# ---- Inside: the studio -------------------------------------------------------------------------

PARTITION_STUDIO = 600


def camera(c, x, facing, tag):
    """A studio camera on a pedestal: a column on a wheeled base, the body,
    the lens, and the teleprompter's hood over the lens, its glass showing
    the script backwards."""
    g = FLOOR
    c.put(c.mask(lambda p: (p.rect(x - 4, g - 96, x + 4, g - 14), p.poly([(x - 26, g - 6), (x + 26, g - 6), (x + 18, g - 16), (x - 18, g - 16)]))), CHROME_DARK)
    c.put(c.mask(lambda p: [p.ellipse(x + dx, g - 4, 4) for dx in (-22, 0, 22)]), INK)
    bx0, bx1 = (x - 30, x + 14) if facing > 0 else (x - 14, x + 30)
    c.put(c.mask(box(bx0, g - 130, bx1, g - 96)), (70, 74, 82))
    c.put(c.mask(box(bx0, g - 130, bx1, g - 126)), CHROME)
    c.put(c.mask(lambda p: p.ellipse(bx0 + 8 if facing > 0 else bx1 - 8, g - 120, 2.4)), ON_AIR)
    lx = bx1 if facing > 0 else bx0
    c.put(c.mask(box(min(lx, lx + facing * 18), g - 124, max(lx, lx + facing * 18), g - 102)), INK)
    hx = lx + facing * 18
    hood = [(hx, g - 136), (hx + facing * 22, g - 140), (hx + facing * 22, g - 92), (hx, g - 96)]
    c.put(c.mask(lambda p: p.poly(hood)), (40, 42, 50))
    glass = c.mask(lambda p: p.poly([(hx + facing * 3, g - 132), (hx + facing * 19, g - 135), (hx + facing * 19, g - 97), (hx + facing * 3, g - 99)]))
    c.put(glass, (30, 60, 90))
    c.put(glass * c.mask(lambda p: [p.rect(min(hx + facing * 5, hx + facing * 17), y, max(hx + facing * 5, hx + facing * 17), y + 1.2) for y in range(g - 128, g - 100, 5)]), (220, 236, 255), 0.8)
    c.put(c.mask(lambda p: p.line([(x, g - 110), (x - facing * 34, g - 92)], 2.4)), CHROME_DARK)


def fresnel(c, x, y, aim_x, aim_y):
    """A studio lamp hung under the grid, and its light on the set."""
    c.put(c.mask(lambda p: (p.rect(x - 1, y, x + 1, y + 12), p.ellipse(x, y + 20, 9, 8))), INK)
    c.put(c.mask(lambda p: p.ellipse(x + (aim_x - x) * 0.02, y + 24, 6, 4)), WARM)
    c.light(c.mask(lambda p: p.poly([(x - 6, y + 24), (x + 6, y + 24), (aim_x + 70, aim_y), (aim_x - 70, aim_y)]), blur=18), WARM, 0.12)


def studio(c, k):
    x0, x1 = PARTITION_STUDIO, PARTITION
    c.put(c.mask(box(x0, CEILING, x1, FLOOR)), STUDIO_WALL)
    c.tone(c.mask(box(x0, CEILING, x1, FLOOR)) * (c.noise(("qed_studio", "wall"), 12, 6, 2) - 0.5), 0.10)
    # Acoustic panels high on the wall.
    c.put(c.mask(lambda p: [p.rect(x, 60, x + 52, 140) for x in range(x0 + 20, x1 - 40, 64)]), (48, 50, 62))
    # The set: the painted backdrop of Eureka at dusk and its tether.
    s0, s1, sy0, sy1 = 680, 1080, 372, 584
    sky = c.mask(box(s0, sy0, s1, sy1))
    c.put(sky, NAVY)
    c.put(sky * np.clip((c.y - sy0) / (sy1 - sy0), 0, 1)[...], ORANGE, 0.7)
    c.put(c.mask(lambda p: [p.rect(x, sy1 - h, x + w, sy1) for x, w, h in ((690, 50, 50), (744, 30, 86), (780, 70, 40), (860, 40, 70), (940, 60, 46), (1010, 50, 64))]), (30, 28, 44))
    c.put(c.mask(lambda p: p.ellipse(1050, sy0 + 92, 12, 11)), (230, 230, 222))
    c.put(c.mask(lambda p: p.rect(1030, sy0, 1032, sy1 - 64)), (240, 240, 250), 0.8)
    c.put(c.mask(lambda p: [p.ellipse(x, y, 1.0) for x, y in ((700, 392), (760, 446), (990, 452), (1060, 420), (720, 470))]), (255, 255, 240))
    c.put(c.mask(box(s0 - 6, sy0 - 6, s1 + 6, sy0)), BURGUNDY)
    qed_sign(c, 760, sy0 + 14, 1000, sy0 + 66)
    letters(c, "THE EVENING NEWS", 880, sy0 + 76, 10, WARM, width=1.0, centre=True)
    # The riser and the anchor desk: walnut and chrome, the magnet on its front.
    a0, a1, ay = ANCHOR_DESK
    c.put(c.mask(box(a0 - 60, FLOOR - 10, a1 + 60, FLOOR)), BURGUNDY_DARK)
    c.put(c.mask(lambda p: p.poly([(a0, ay), (a1, ay), (a1 - 10, FLOOR - 10), (a0 + 10, FLOOR - 10)])), WALNUT)
    c.put(c.mask(box(a0 - 6, ay, a1 + 6, ay + 7)), CHROME)
    c.put(c.mask(box(a0 + 20, ay + 16, a1 - 20, ay + 20)), BURGUNDY)
    magnet(c, (a0 + a1) / 2, ay + 26, 9)
    c.put(c.mask(lambda p: (p.rect(a0 + 40, ay - 3, a0 + 70, ay), p.rect(a1 - 50, ay - 14, a1 - 48, ay))), (236, 232, 220))
    c.put(c.mask(lambda p: p.ellipse(a1 - 49, ay - 16, 3)), INK)
    # The lighting grid, its lamps on the desk and on the bench, its ladder.
    g0, g1, gy = GRID
    c.put(c.mask(lambda p: (p.rect(g0, gy, g1, gy + 4), p.rect(g0, gy + 14, g1, gy + 17),
                             [p.line([(x, gy + 4), (x + 12, gy + 14), (x + 24, gy + 4)], 1.2) for x in range(g0, g1 - 20, 24)])), CHROME_DARK)
    c.put(c.mask(box(g0, gy, g1, gy + 1.2)), CHROME)
    c.put(c.mask(lambda p: [p.rect(x - 1, CEILING, x + 1, gy) for x in (g0 + 200, g0 + 600, g1 - 20)]), CHROME_DARK)
    for lx, ax in ((720, 840), (820, 880), (1000, 900), (1380, 1420), (1480, 1420)):
        fresnel(c, lx, gy + 17, ax, ANCHOR_DESK[2] if ax < 1200 else BENCH[2])
    l0, l1 = LADDER
    c.put(c.mask(lambda p: (p.rect(l0, gy, l0 + 3, FLOOR), p.rect(l1 - 3, gy, l1, FLOOR), [p.rect(l0, y, l1, y + 2.5) for y in range(gy + 14, FLOOR, 20)])), CHROME)
    # The ON AIR light, hung from the ceiling over the set.
    c.put(c.mask(lambda p: [p.rect(x, CEILING, x + 1, 92) for x in (856, 904)]), CHROME_DARK)
    on_air(c, 880, 104, w=70, h=24)
    # The cameras, one either side of the set, both on the desk.
    camera(c, 640 + 30, 1, "cam_a")
    camera(c, 1180, -1, "cam_b")
    # The demonstration area: a taped line on the floor, the Van de Graaff
    # generator, the board, the bench and its glassware.
    c.put(c.mask(lambda p: [p.rect(x, FLOOR - 3, x + 12, FLOOR - 1) for x in range(1220, 1580, 20)]), MUSTARD)
    vx = 1262
    c.put(c.mask(lambda p: (p.rect(vx - 16, FLOOR - 12, vx + 16, FLOOR), p.rect(vx - 6, FLOOR - 120, vx + 6, FLOOR - 12))), (220, 220, 214))
    c.put(c.mask(lambda p: p.ellipse(vx, FLOOR - 140, 26)), CHROME)
    c.light(c.mask(lambda p: p.ellipse(vx - 8, FLOOR - 150, 9), blur=3), (255, 255, 255), 0.7)
    rng = c.rand("qed", "spark")
    for _ in range(3):
        a = rng.uniform(-2.6, -0.6)
        pts = [(vx + np.cos(a) * 26, FLOOR - 140 + np.sin(a) * 26)]
        for i in range(5):
            pts.append((pts[-1][0] + np.cos(a) * 7 + rng.uniform(-4, 4), pts[-1][1] + np.sin(a) * 7 + rng.uniform(-4, 4)))
        c.put(c.mask(lambda p, pts=pts: p.line(pts, 1.2)), (210, 230, 255))
    bx0, by0 = 1330, 420
    c.put(c.mask(box(bx0 - 4, by0 - 4, bx0 + 184, by0 + 104)), OAK)
    c.put(c.mask(box(bx0, by0, bx0 + 180, by0 + 100)), (40, 58, 50))
    letters(c, "1 HP = 746 W", bx0 + 90, by0 + 16, 14, (232, 236, 228), width=0.9, centre=True)
    letters(c, "F = MA", bx0 + 90, by0 + 48, 12, (232, 236, 228), width=0.9, centre=True)
    c.put(c.mask(lambda p: p.line([(bx0 + 40, by0 + 88), (bx0 + 70, by0 + 76), (bx0 + 110, by0 + 80), (bx0 + 140, by0 + 70)], 1.0)), (232, 236, 228), 0.8)
    b0, b1, by = BENCH
    c.put(c.mask(box(b0, by, b1, FLOOR)), (90, 96, 104))
    c.put(c.mask(box(b0 - 4, by, b1 + 4, by + 6)), (30, 32, 36))
    c.put(c.mask(lambda p: [p.rect(x, by + 14, x + 60, FLOOR - 8) for x in (b0 + 10, b0 + 76, b0 + 140)]), (110, 116, 124))
    for fx, col in ((b0 + 30, (110, 200, 150)), (b0 + 70, (230, 120, 160)), (b0 + 150, (140, 180, 240))):
        c.put(c.mask(lambda p, fx=fx: p.poly([(fx - 3, by - 26), (fx + 3, by - 26), (fx + 3, by - 18), (fx + 11, by), (fx - 11, by), (fx - 3, by - 18)])), (220, 236, 240), 0.8)
        c.put(c.mask(lambda p, fx=fx: p.poly([(fx - 6, by - 9), (fx + 6, by - 9), (fx + 10, by), (fx - 10, by)])), col)
    # A Newton's cradle.
    nx = b0 + 108
    c.put(c.mask(lambda p: (p.rect(nx - 16, by - 28, nx + 16, by - 26), p.rect(nx - 16, by - 28, nx - 14, by), p.rect(nx + 14, by - 28, nx + 16, by))), CHROME_DARK)
    c.put(c.mask(lambda p: [p.ellipse(nx - 8 + i * 4, by - 8, 2) for i in range(5)]), CHROME)
    c.put(c.mask(box(x0, FLOOR - 2, x1, FLOOR)), scale(STUDIO_FLOOR, 0.7))


# ---- Inside: the production room ----------------------------------------------------------------


def monitor(c, x, y, w, h, show):
    c.put(c.mask(box(x - 3, y - 3, x + w + 3, y + h + 3)), (54, 56, 62))
    s = c.mask(box(x, y, x + w, y + h))
    c.put(s, SCREEN)
    if show == "bars":
        for i, col in enumerate(((236, 236, 236), (236, 220, 60), (60, 210, 220), (60, 200, 80), (210, 60, 200), (220, 50, 50), (50, 60, 210))):
            c.put(c.mask(box(x + i * w / 7, y, x + (i + 1) * w / 7, y + h)), col, 0.85)
    elif show == "anchor":
        c.put(s, NAVY)
        cx = x + w / 2
        c.put(c.mask(lambda p: p.poly([(cx - w * 0.3, y + h), (cx - w * 0.25, y + h * 0.7), (cx + w * 0.25, y + h * 0.7), (cx + w * 0.3, y + h)])), BURGUNDY)
        c.put(c.mask(lambda p: p.poly([(cx - w * 0.1, y + h * 0.72), (cx - w * 0.12, y + h * 0.3), (cx + w * 0.05, y + h * 0.15), (cx + w * 0.2, y + h * 0.5), (cx + w * 0.08, y + h * 0.72)])), (138, 74, 40))
        c.put(c.mask(lambda p: p.ellipse(cx - w * 0.02, y + h * 0.2, w * 0.16, h * 0.08)), (58, 36, 22))
    elif show == "logo":
        c.put(s, BURGUNDY)
        magnet(c, x + w / 2, y + h * 0.4, h * 0.22)
    elif show == "weather":
        c.put(s, (60, 120, 70))
        c.put(c.mask(lambda p: p.ellipse(x + w * 0.35, y + h * 0.45, w * 0.18, h * 0.16)), (240, 240, 240))
        c.put(c.mask(lambda p: p.ellipse(x + w * 0.7, y + h * 0.35, w * 0.1)), (250, 210, 60))
    elif show == "station":
        stars_pts = [(x + w * a, y + h * b) for a, b in ((0.2, 0.2), (0.7, 0.3), (0.4, 0.8), (0.85, 0.7))]
        c.put(c.mask(lambda p: [p.ellipse(px, py, 0.8) for px, py in stars_pts]), (255, 255, 240))
        c.put(c.mask(lambda p: (p.ring(x + w / 2, y + h / 2, h * 0.28, 1.4), p.rect(x + w / 2 - 1, y + h * 0.22, x + w / 2 + 1, y + h * 0.78))), CHROME)
    c.light(s, (150, 190, 230), 0.12)


def production(c, k):
    x0, x1 = PARTITION, 2224
    c.put(c.mask(box(x0, CEILING, x1, FLOOR)), (58, 62, 70))
    c.put(c.mask(box(x0, 470, x1, FLOOR)), (70, 72, 80))
    # The partition between the studio and this room: a header and a post,
    # the way through open under it.
    c.put(c.mask(lambda p: (p.rect(x0, CEILING, x0 + 18, 420), p.rect(x0, 400, x0 + 60, 420))), CREAM_DARK)
    c.put(c.mask(box(x0 + 2, 120, x0 + 16, 380)), GLASS, 0.6)
    # The wall of monitors.
    shows = (("anchor", "logo", "bars", "station"), ("weather", "anchor", "station", "bars"), ("logo", "bars", "anchor", "weather"))
    for r, row in enumerate(shows):
        for i, show in enumerate(row):
            monitor(c, 1660 + i * 74, 220 + r * 58, 64, 48, show)
    c.put(c.mask(box(1660 - 6, 212, 1660 + 4 * 74, 216)), INK)
    # The vision mixer: a long sloped desk of faders and lit buttons, two chairs.
    m0, m1, my = CONSOLE
    c.put(c.mask(lambda p: p.poly([(m0, my), (m1, my), (m1 + 8, FLOOR), (m0 - 8, FLOOR)])), (76, 80, 90))
    c.put(c.mask(lambda p: p.poly([(m0 - 4, my - 10), (m1 + 4, my - 10), (m1 + 6, my), (m0 - 6, my)])), (40, 42, 48))
    rng = c.rand("qed", "buttons")
    b = Batch(c)
    for x in range(m0 + 8, m1 - 8, 9):
        b.add(rng.choice(((236, 60, 50), (240, 200, 60), (90, 200, 120), (220, 220, 220))), 0.95, lambda p, x=x: p.rect(x, my - 7, x + 5, my - 4))
        b.add(CHROME, 1.0, lambda p, x=x: p.rect(x + 1, my + 4, x + 3, my + 18))
        b.add((240, 240, 240), 1.0, lambda p, x=x, y=rng.uniform(my + 6, my + 15): p.rect(x - 1, y, x + 5, y + 2))
    b.draw()
    for cx in (1760, 1880):
        c.put(c.mask(lambda p, cx=cx: (p.rect(cx - 12, FLOOR - 40, cx + 12, FLOOR - 30), p.rect(cx - 2, FLOOR - 30, cx + 2, FLOOR - 6), p.rect(cx - 12, FLOOR - 6, cx + 12, FLOOR - 2))), INK)
    # The weather centre: the green wall, a stand of lights, a weather map
    # on a monitor so the weatherman can see where to point.
    c.put(c.mask(box(2000, 280, 2210, FLOOR)), KEY_GREEN)
    c.tone(c.mask(box(2000, 280, 2210, FLOOR)) * (c.noise(("qed", "green"), 6, 6, 2) - 0.5), 0.08)
    monitor(c, 2150, 220, 52, 40, "weather")
    c.put(c.mask(lambda p: (p.rect(2010, FLOOR - 150, 2013, FLOOR), p.ellipse(2012, FLOOR - 158, 10, 8))), INK)
    c.light(c.mask(lambda p: p.ellipse(2060, FLOOR - 100, 70, 90), blur=20), WARM, 0.1)
    # The coffee machine on its cabinet, and the producer's clipboard wall.
    c.put(c.mask(box(1640, FLOOR - 50, 1690, FLOOR)), WALNUT)
    c.put(c.mask(box(1648, FLOOR - 84, 1682, FLOOR - 50)), (40, 40, 44))
    c.put(c.mask(lambda p: p.ellipse(1676, FLOOR - 76, 2)), ON_AIR)
    c.put(c.mask(lambda p: [p.rect(x, 140, x + 26, 180) for x in (1680, 1720, 1760, 1800)]), (236, 228, 204))
    c.put(c.mask(lambda p: [p.rect(x + 4, y, x + 22, y + 1.2) for x in (1680, 1720, 1760, 1800) for y in (150, 158, 166)]), (90, 90, 110))
    on_air(c, 1900, 150, w=56, h=18)
    c.put(c.mask(box(x0, FLOOR - 2, x1, FLOOR)), (40, 42, 48))


PIECES: Dict[str, Piece] = {
    "quad_qed_front": Piece((1600, 10, 2040, TERRACE), front),
    "qed_reception": Piece((16, CEILING, PARTITION_STUDIO, FLOOR), reception),
    "qed_studio": Piece((PARTITION_STUDIO, CEILING, PARTITION, FLOOR), studio),
    "qed_production": Piece((PARTITION, CEILING, 2224, FLOOR), production),
}

TARGETS = targets(PIECES, PAL)

__all__ = ["PIECES", "TARGETS"]
