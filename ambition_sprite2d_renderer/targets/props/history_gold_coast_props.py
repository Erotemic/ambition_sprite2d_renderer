"""The props of the fort on the Gold Coast (the History dimension).

From the late 1400s the trading companies of Europe built forts and castles
of stone along the Gold Coast (now Ghana). They came first for gold. Then,
for more than two hundred years, they bought and held people there: men,
women and children waited in the dungeons under the walls until a ship
came, and they went out to it through a narrow door to the sea. People
call it the Door of No Return. The Fante towns of fishers lived beside the
forts, and their canoes still go out through the surf from the same
beaches.

These props are drawn in the cel style of the dimension's cast
(`targets/characters/_history_americas_kit.py`): flat colour, one shade, a
bold warm outline. The room is sober: they show places and things, with
no joke and no spectacle.

- ``history_fante_canoe``: scenery, a Fante fishing canoe drawn up on the
  sand: a long dugout with a raised beak at each end, painted in bright
  bands of yellow, red, green and blue, with a painted name panel of plain
  shapes (no words) and a rolled net with its floats in it. Its keel rests
  in a low bank of sand.
- ``history_fort_cannon``: scenery, an old cannon of iron on a wooden
  carriage with four small wheels, pointing to the right (to the sea).

The numbers are frame pixels; the game shows each prop at half its frame.
No drop shadows: the game draws them.
"""

from __future__ import annotations

import math
from typing import Callable, Dict, List, Tuple

from ..characters import _art_cast_kit as K
from ..characters import _history_americas_kit as A
from .art_props import _publisher

Point = Tuple[float, float]
STILL: List[Tuple[str, int, int]] = [("idle", 1, 1000)]

CANOE_FRAME = (384, 128)
CANNON_FRAME = (160, 96)

WOOD = (138, 94, 58, 255)
WOOD_LIGHT = (176, 130, 84, 255)
WOOD_DARK = (88, 58, 36, 255)
HULL_IN = (110, 74, 46, 255)
YELLOW = (238, 196, 60, 255)
YELLOW_SHADE = (196, 150, 40, 255)
RED = (196, 52, 44, 255)
RED_SHADE = (146, 36, 32, 255)
GREEN = (54, 136, 84, 255)
GREEN_SHADE = (36, 98, 60, 255)
BLUE = (44, 96, 164, 255)
BLUE_SHADE = (30, 66, 120, 255)
WHITE = (240, 236, 224, 255)
BLACK = (40, 34, 32, 255)
NET = (176, 168, 140, 255)
NET_SHADE = (126, 118, 96, 255)
FLOAT = (226, 118, 52, 255)
SAND = (226, 210, 170, 255)
SAND_SHADE = (190, 170, 126, 255)
IRON = (64, 64, 68, 255)
IRON_LIGHT = (112, 114, 120, 255)
IRON_DARK = (36, 36, 40, 255)
RUST = (122, 78, 52, 255)


def _phase(i: int, n: int) -> float:
    return i / float(max(1, n))


# ---------------------------------------------------------------------------
# The Fante canoe.
# ---------------------------------------------------------------------------


def _hull_edges(x: float, x0: float, x1: float, keel: float, gun: float, rise: float) -> Tuple[float, float]:
    """The top (gunwale) and the foot (keel) of the hull at `x`. The keel
    curves up toward each end, and the gunwale rises a little to each end."""
    u = (x - x0) / (x1 - x0) * 2.0 - 1.0
    top = gun - rise * abs(u) ** 3
    foot = keel - (keel - gun) * 0.55 * abs(u) ** 4
    return top, foot


def _draw_canoe(anim: str, i: int, n: int):
    w, h = CANOE_FRAME
    f = K.Frame(CANOE_FRAME)
    foot = h - 8.0
    # The low bank of sand that the hull rests in: the canoe was pulled
    # up the beach and sank a little into it.
    bank = [(x, foot - 16.0 * math.sin(math.pi * (x - 14.0) / 356.0) ** 0.5) for x in (14.0 + 356.0 * k / 40.0 for k in range(41))]
    f.poly(bank, SAND)
    x0, x1 = 30.0, 354.0
    keel, gun, rise = foot - 10.0, foot - 54.0, 8.0
    xs = [x0 + (x1 - x0) * k / 60.0 for k in range(61)]
    tops = [_hull_edges(x, x0, x1, keel, gun, rise)[0] for x in xs]
    feet = [_hull_edges(x, x0, x1, keel, gun, rise)[1] for x in xs]
    # The beaks: each end of the hull runs out into a raised point, as on
    # the canoes of the coast.
    stern = [(x0 + 2.0, tops[0] + 4.0), (x0 - 18.0, tops[0] - 8.0), (x0 - 20.0, tops[0] - 3.0), (x0 - 4.0, feet[0] - 4.0)]
    bow = [(x1 - 2.0, tops[-1] + 4.0), (x1 + 18.0, tops[-1] - 8.0), (x1 + 20.0, tops[-1] - 3.0), (x1 + 4.0, feet[-1] - 4.0)]
    f.poly(stern, WOOD)
    f.poly(bow, WOOD)
    hull = list(zip(xs, tops)) + list(zip(xs[::-1], feet[::-1]))
    f.poly(hull, WOOD)

    def band(v0: float, v1: float, colour) -> None:
        """A band of paint along the hull, between the fractions `v0` and
        `v1` of its depth from the gunwale."""
        up = [(x, t + (b - t) * v0) for x, t, b in zip(xs, tops, feet)]
        lo = [(x, t + (b - t) * v1) for x, t, b in zip(xs[::-1], tops[::-1], feet[::-1])]
        f.poly(up + lo, colour, body=False)

    # The painted bands: yellow at the gunwale, then red, green and blue
    # down to the keel, each with a thin white line between.
    band(0.00, 0.20, YELLOW)
    band(0.20, 0.24, WHITE)
    band(0.24, 0.48, RED)
    band(0.48, 0.52, WHITE)
    band(0.52, 0.76, GREEN)
    band(0.76, 0.80, WHITE)
    band(0.80, 1.00, BLUE)
    # The lower half of each band is in shade, as the hull curves under.
    for v0, v1, c in ((0.12, 0.20, YELLOW_SHADE), (0.40, 0.48, RED_SHADE), (0.68, 0.76, GREEN_SHADE), (0.90, 1.00, BLUE_SHADE)):
        band(v0, v1, c)
    # The beaks are painted too: red with a yellow tip.
    for pts, sx in ((stern, -1.0), (bow, 1.0)):
        f.poly(pts, RED, body=False)
        tip = pts[1]
        f.poly([(tip[0] - sx * 6.0, tip[1] + 1.0), tip, (tip[0] + sx * 1.0, tip[1] + 5.0), (tip[0] - sx * 6.0, tip[1] + 6.0)], YELLOW, body=False)
        f.ink([pts[0], pts[3]], 1.0, WOOD_DARK)
    # The name panel: a white panel in the middle of the red band, with
    # plain painted shapes on it (a sun, a star and two leaves); no words.
    px0, px1 = 160.0, 230.0
    py0 = _hull_edges(px0, x0, x1, keel, gun, rise)[0] + 8.0
    py1 = py0 + 24.0
    f.poly([(px0, py0), (px1, py0), (px1, py1), (px0, py1)], WHITE, body=False)
    f.ink([(px0, py0), (px1, py0), (px1, py1), (px0, py1), (px0, py0)], 1.2, BLACK)
    cy = (py0 + py1) / 2.0
    f.ellipse(px0 + 12.0, cy, 6.4, 6.4, YELLOW, body=False)
    f.ellipse(px0 + 12.0, cy, 3.0, 3.0, RED, body=False)
    star = [(px0 + 35.0 + (7.0 if k % 2 == 0 else 3.0) * math.cos(math.radians(-90.0 + 36.0 * k)),
             cy + (7.0 if k % 2 == 0 else 3.0) * math.sin(math.radians(-90.0 + 36.0 * k))) for k in range(10)]
    f.poly(star, BLUE, body=False)
    for k, sx in enumerate((52.0, 61.0)):
        f.poly([(px0 + sx - 3.0, cy + 6.0), (px0 + sx, cy - 7.0), (px0 + sx + 3.0, cy + 6.0)], GREEN if k == 0 else RED, body=False)
    # Small painted triangles along the yellow band, as a border.
    x = x0 + 26.0
    while x < x1 - 30.0:
        t = _hull_edges(x, x0, x1, keel, gun, rise)[0]
        f.poly([(x - 3.0, t + 9.0), (x + 3.0, t + 9.0), (x, t + 3.4)], RED, body=False)
        x += 14.0
    # The sand in front of the foot of the hull: the keel sank into it.
    front = [(x, foot - 4.0 - 12.0 * math.sin(math.pi * (x - 40.0) / 300.0) ** 0.6 - 1.4 * math.sin(x * 0.09)) for x in (40.0 + 300.0 * k / 40.0 for k in range(41))]
    f.poly(front + [(340.0, foot), (40.0, foot)], SAND, body=False)
    f.ink(front, 1.0, SAND_SHADE)
    for x, y in ((120.0, foot - 5.0), (200.0, foot - 4.0), (262.0, foot - 6.0), (160.0, foot - 9.0), (300.0, foot - 4.0)):
        f.ink([(x - 6.0, y), (x + 6.0, y - 1.0)], 0.8, SAND_SHADE)
    for x, y in ((88.0, foot - 4.0), (232.0, foot - 3.0)):
        f.ellipse(x, y, 2.4, 1.4, WHITE, body=False)
    # The gunwale: a thick rim of bare wood, lit on top, and the inside of
    # the far side of the hull that shows above it toward each end.
    f.limb([(x, t - 0.5) for x, t in zip(xs, tops)], 4.0, WOOD_LIGHT)
    f.ink([(x, t + 1.6) for x, t in zip(xs, tops)], 1.0, WOOD_DARK)
    # Two thwarts (seats) cross the hull and stand above the gunwale.
    for x in (120.0, 270.0):
        t = _hull_edges(x, x0, x1, keel, gun, rise)[0]
        f.poly([(x - 6.0, t - 6.0), (x + 6.0, t - 6.0), (x + 6.0, t + 1.0), (x - 6.0, t + 1.0)], WOOD_DARK)
        f.ink([(x - 5.0, t - 5.0), (x + 5.0, t - 5.0)], 0.8, WOOD_LIGHT)
    # The rolled net in the hull: a long soft roll that rises over the
    # gunwale, with its mesh, and a line of orange floats along it.
    nx0, nx1 = 140.0, 254.0
    t = _hull_edges((nx0 + nx1) / 2.0, x0, x1, keel, gun, rise)[0]
    roll = [(nx0 + (nx1 - nx0) * k / 20.0, t - 12.0 - 4.0 * math.sin(math.pi * k / 20.0)) for k in range(21)]
    net = roll + [(nx1 + 4.0, t + 1.0), (nx0 - 4.0, t + 1.0)]
    f.poly(net, NET)
    f.poly([(x, y + 7.0) for x, y in roll] + [(nx1 + 4.0, t + 1.0), (nx0 - 4.0, t + 1.0)], NET_SHADE, body=False)
    for k in range(1, 24):
        x = nx0 + (nx1 - nx0) * k / 24.0
        y = roll[min(20, int(k / 24.0 * 20))][1]
        f.ink([(x - 3.0, y + 1.0), (x + 3.0, t)], 0.6, NET_SHADE)
        f.ink([(x + 3.0, y + 1.0), (x - 3.0, t)], 0.6, NET_SHADE)
    for k in range(7):
        x = nx0 + 10.0 + k * (nx1 - nx0 - 20.0) / 6.0
        y = roll[min(20, int((x - nx0) / (nx1 - nx0) * 20))][1] + 2.0
        f.ellipse(x, y, 4.0, 2.8, FLOAT, body=False)
        f.ink([(x - 2.0, y - 1.0), (x + 1.0, y - 1.4)], 0.6, WHITE)
    # A paddle laid along the hull, its blade over the gunwale near the bow.
    t1 = _hull_edges(300.0, x0, x1, keel, gun, rise)[0]
    f.limb([(262.0, t1 - 9.0), (318.0, t1 - 7.0)], 2.6, WOOD_DARK)
    f.poly([(318.0, t1 - 11.0), (340.0, t1 - 9.0), (342.0, t1 - 5.0), (318.0, t1 - 3.0)], WOOD)
    f.ink([(320.0, t1 - 7.0), (340.0, t1 - 7.0)], 0.7, WOOD_DARK)
    return A.finish(f, width=1.6)


# ---------------------------------------------------------------------------
# The cannon of the fort.
# ---------------------------------------------------------------------------


def _wheel(f: K.Frame, cx: float, cy: float, r: float) -> None:
    """A small solid wheel (a truck) of wood with an iron axle cap."""
    f.ellipse(cx, cy, r, r, WOOD)
    f.ellipse(cx + r * 0.25, cy + r * 0.2, r * 0.70, r * 0.70, WOOD_DARK, body=False)
    f.ellipse(cx, cy, r * 0.80, r * 0.80, WOOD, body=False)
    f.ellipse(cx, cy, r * 0.30, r * 0.30, IRON, body=False)
    f.ink([(cx - r * 0.6, cy - r * 0.5), (cx - r * 0.2, cy - r * 0.75)], 0.8, WOOD_LIGHT)


def _draw_cannon(anim: str, i: int, n: int):
    w, h = CANNON_FRAME
    f = K.Frame(CANNON_FRAME)
    foot = h - 6.0
    # The carriage: two stepped cheeks of heavy timber on a bed, low at the
    # back and high at the front, on four small wheels.
    r = 9.0
    cheek = [(18.0, foot - 12.0), (18.0, foot - 24.0), (30.0, foot - 24.0), (30.0, foot - 32.0), (44.0, foot - 32.0), (44.0, foot - 40.0),
             (70.0, foot - 40.0), (78.0, foot - 46.0), (96.0, foot - 46.0), (102.0, foot - 30.0), (104.0, foot - 12.0)]
    f.poly(cheek, WOOD)
    f.poly([(18.0, foot - 18.0), (104.0, foot - 18.0), (104.0, foot - 12.0), (18.0, foot - 12.0)], WOOD_DARK, body=False)
    f.ink([(20.0, foot - 23.0), (30.0, foot - 23.0), (30.0, foot - 31.0), (44.0, foot - 31.0), (44.0, foot - 39.0), (70.0, foot - 39.0)], 1.0, WOOD_LIGHT)
    # The bolts of iron through the cheek, and the iron cap square over
    # the trunnion.
    for x, y in ((26.0, foot - 16.0), (52.0, foot - 30.0), (92.0, foot - 24.0), (64.0, foot - 16.0)):
        f.dot(x, y, 1.6, IRON_DARK)
    for cx in (34.0, 92.0):
        _wheel(f, cx, foot - r, r)
    # The barrel: a long tube of iron that tapers to the muzzle, with
    # raised rings, a swell at the muzzle and a knob (the cascabel) at the
    # breech. It lies on the cheeks at the trunnion.
    bx0, bx1, by = 22.0, 150.0, foot - 50.0

    def radius(x: float) -> float:
        u = (x - bx0) / (bx1 - bx0)
        return 11.0 - 4.4 * u

    top = [(x, by - radius(x)) for x in (bx0 + (bx1 - bx0) * k / 20.0 for k in range(21))]
    bot = [(x, by + radius(x)) for x in (bx1 - (bx1 - bx0) * k / 20.0 for k in range(21))]
    f.poly(top + bot, IRON)
    f.poly([(x, by + radius(x) * 0.25) for x, _ in top] + bot, IRON_DARK, body=False)
    f.ink([(x, by - radius(x) * 0.55) for x, _ in top[1:-1]], 1.4, IRON_LIGHT)
    # The rings round it, and the swell at the muzzle.
    for x in (bx0 + 4.0, 58.0, 96.0):
        rr = radius(x) + 1.6
        f.poly([(x - 2.0, by - rr), (x + 2.0, by - rr), (x + 2.0, by + rr), (x - 2.0, by + rr)], IRON)
        f.ink([(x - 1.0, by - rr + 1.0), (x - 1.0, by - 1.0)], 0.8, IRON_LIGHT)
    mx = bx1 - 7.0
    mr = radius(bx1) + 2.4
    f.poly([(mx, by - mr), (bx1, by - mr), (bx1, by + mr), (mx, by + mr)], IRON)
    f.ink([(mx + 1.0, by - mr + 1.0), (bx1 - 1.0, by - mr + 1.0)], 0.8, IRON_LIGHT)
    f.ellipse(bx1, by, 1.6, radius(bx1) * 0.55, IRON_DARK, body=False)
    # The cascabel at the breech.
    f.limb([(bx0, by), (bx0 - 8.0, by)], 4.0, IRON)
    f.ellipse(bx0 - 10.0, by, 4.2, 4.2, IRON)
    f.dot(bx0 - 11.0, by - 1.4, 1.2, IRON_LIGHT)
    # The trunnion and its cap square, over the front step of the cheek.
    f.ellipse(86.0, by + 2.0, 4.6, 4.6, IRON_DARK)
    f.poly([(80.0, by - 4.0), (92.0, by - 4.0), (92.0, by + 0.0), (80.0, by + 0.0)], IRON)
    # A little rust in the hollows of the old iron.
    for x, y, rx in ((70.0, by + 4.0, 5.0), (118.0, by + 3.0, 4.0), (40.0, by + 6.0, 4.0)):
        f.ellipse(x, y, rx, 1.6, K.alpha(RUST, 0.55), body=False)
    # The touch hole on top of the breech.
    f.dot(bx0 + 10.0, by - radius(bx0 + 10.0) + 1.2, 1.0, IRON_DARK)
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# Publication.
# ---------------------------------------------------------------------------

SCENERY = ["prop", "scenery", "history", "africa"]

FRAMES: Dict[str, Tuple[int, int]] = {
    "history_fante_canoe": CANOE_FRAME,
    "history_fort_cannon": CANNON_FRAME,
}
DRAW: Dict[str, Callable] = {
    "history_fante_canoe": _draw_canoe,
    "history_fort_cannon": _draw_cannon,
}
DISPLAY = {
    "history_fante_canoe": "Fante Fishing Canoe",
    "history_fort_cannon": "Cannon of the Fort",
}
ROWS: Dict[str, List[Tuple[str, int, int]]] = {}


def _foot(name: str) -> Dict[str, Tuple[float, float]]:
    w, h = FRAMES[name]
    return {"foot": (w / 2.0, float(h))}


TARGETS: Dict[str, dict] = {
    name: _publisher(name, DISPLAY[name], ROWS.get(name, STILL), FRAMES[name], DRAW[name], _foot(name), "Scenery", SCENERY) for name in DISPLAY
}
