"""The props of Southeast Asia (the History dimension): Sulawesi, the
Austronesian islands and Dong Son.

In the limestone karst of Maros-Pangkep, on Sulawesi, people painted on the
walls of caves in red ochre. At Leang Karampuang a painted scene of a pig
and three small human-like figures is at least 51,200 years old: it is the
oldest known painted story. At Leang Tedongnge a life-size warty pig is at
least 45,500 years old. The painters also blew ochre round their hands, so
that the shape of the hand stays the colour of the rock.

About 2000 BCE the Austronesians came from Taiwan to the Philippines and
Indonesia in outrigger canoes. They built houses on posts, with high roofs
of thatch, and they made round pots with a red slip.

In the Red River delta of northern Vietnam, the Dong Son culture (about
700 BCE to 100 CE) grew rice in flooded fields and cast great bronze drums.
The top of a drum has a star with rays in its middle, rings of patterns
and birds in flight round it, and on many drums small frogs of bronze sit
on the rim.

These props are drawn in the cel style of the dimension's cast
(`targets/characters/_history_americas_kit.py`): flat colour, one shade, a
bold warm outline. They show the skill of the people who made them.

- ``history_pig_painting``: scenery, a section of pale limestone cave wall
  with a red-ochre warty pig, three small human-like figures with spears
  beside it, and two hand stencils.
- ``history_sulawesi_hand_stencils``: scenery, a rock panel with five hand
  stencils in red ochre, of different sizes.
- ``history_bamboo_stilt_house``: scenery, a house of bamboo and thatch on
  posts, with a saddle roof whose ridge curves up at both ends, and a
  ladder.
- ``history_bronze_drum``: scenery, a Dong Son bronze drum, seen a little
  from above: a star with rays, a ring of flying birds, and frogs on the
  rim.
- ``history_rice_sheaves``: scenery, sheaves of harvested rice that stand
  on a dike, and a flat basket.
- ``history_red_slip_pots``: scenery, three round pots with a red slip; one
  has a band of stamped dots.

The numbers are frame pixels; the game shows each prop at half its frame.
No drop shadows: the game draws them.
"""

from __future__ import annotations

import math
import random
from typing import Callable, Dict, List, Sequence, Tuple

from ..characters import _art_cast_kit as K
from ..characters import _history_americas_kit as A
from .art_props import _publisher

Point = Tuple[float, float]
RGBA = Tuple[int, int, int, int]
STILL: List[Tuple[str, int, int]] = [("idle", 1, 1000)]

PIG_PAINTING_FRAME = (256, 128)
STENCILS_FRAME = (128, 96)
STILT_HOUSE_FRAME = (192, 224)
DRUM_FRAME = (96, 80)
SHEAVES_FRAME = (128, 64)
POTS_FRAME = (96, 64)

LIMESTONE = (226, 218, 198, 255)
LIMESTONE_SHADE = (192, 182, 160, 255)
LIMESTONE_DARK = (146, 132, 112, 255)
LIMESTONE_LIGHT = (242, 236, 220, 255)
FLOWSTONE = (214, 196, 160, 255)
OCHRE = (170, 58, 38, 255)
OCHRE_DARK = (124, 38, 28, 255)
OCHRE_MULBERRY = (132, 50, 52, 255)

BAMBOO = (196, 168, 96, 255)
BAMBOO_LIGHT = (226, 204, 136, 255)
BAMBOO_SHADE = (148, 122, 64, 255)
THATCH = (178, 144, 84, 255)
THATCH_LIGHT = (214, 184, 118, 255)
THATCH_SHADE = (128, 98, 56, 255)
WOOD = (132, 92, 58, 255)
WOOD_LIGHT = (172, 128, 84, 255)
WOOD_DARK = (88, 58, 36, 255)
WEAVE = (204, 178, 120, 255)
WEAVE_SHADE = (160, 132, 82, 255)
DOORWAY = (62, 44, 32, 255)

BRONZE = (132, 118, 70, 255)
BRONZE_SHADE = (92, 82, 50, 255)
BRONZE_LIGHT = (184, 166, 102, 255)
BRONZE_DARK = (66, 58, 38, 255)
PATINA = (98, 150, 118, 255)
PATINA_LIGHT = (150, 196, 160, 255)

STRAW = (220, 184, 96, 255)
STRAW_LIGHT = (240, 214, 140, 255)
STRAW_SHADE = (166, 130, 60, 255)
GRAIN = (214, 166, 74, 255)
GRAIN_SHADE = (160, 116, 46, 255)
EARTH = (132, 100, 72, 255)
EARTH_SHADE = (98, 72, 52, 255)
GRASS = (110, 146, 70, 255)
GRASS_SHADE = (78, 108, 50, 255)
BASKET = (186, 150, 90, 255)
BASKET_SHADE = (136, 104, 58, 255)

SLIP = (176, 72, 46, 255)
SLIP_SHADE = (126, 46, 32, 255)
SLIP_LIGHT = (214, 118, 82, 255)
CLAY = (196, 142, 98, 255)


def _lumpy_edge(points: Sequence[Point], rng: random.Random, amount: float, steps: int = 4) -> List[Point]:
    """The polygon `points` with each side cut in `steps` parts and moved a
    little at random. A rock edge is not straight."""
    out: List[Point] = []
    n = len(points)
    for k in range(n):
        (x0, y0), (x1, y1) = points[k], points[(k + 1) % n]
        for j in range(steps):
            u = j / float(steps)
            jit = rng.uniform(-amount, amount) if j else 0.0
            out.append((x0 + (x1 - x0) * u + jit, y0 + (y1 - y0) * u + jit * 0.7))
    return out


def _rock_panel(f: K.Frame, outline: Sequence[Point], seed: str) -> None:
    """A panel of pale limestone: the face of the rock, a shade on its
    lower edge, crusts of flowstone, small pits and fine cracks. Limestone
    of the karst is pale grey and cream, and water leaves streaks on it."""
    rng = random.Random(seed)
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    edge = _lumpy_edge(outline, rng, 1.6)
    # The rock is in shade at its lower edge and its sides: the face turns
    # away from the light there. The lit face is the same shape, a little
    # smaller, and it hangs from the top edge.
    f.poly(edge, LIMESTONE_SHADE)
    cx = (x0 + x1) / 2.0
    kx, ky = 1.0 - 5.0 / (x1 - x0), 1.0 - 6.0 / (y1 - y0)
    f.poly([(cx + (x - cx) * kx, y0 + 1.0 + (y - y0) * ky) for x, y in edge], LIMESTONE, body=False)
    # Streaks of flowstone, where water ran down the wall.
    for _ in range(int((x1 - x0) / 34.0) + 1):
        sx = rng.uniform(x0 + 10.0, x1 - 10.0)
        top = y0 + rng.uniform(12.0, 18.0)
        length = rng.uniform(16.0, (y1 - y0) * 0.6)
        f.poly([(sx - 1.8, top), (sx + 1.8, top), (sx + 1.0, top + length), (sx, top + length + 3.0), (sx - 1.0, top + length)], K.alpha(FLOWSTONE, 0.6), body=False)
    # Pits and small hollows of the stone.
    for _ in range(int((x1 - x0) * (y1 - y0) / 500.0)):
        px, py = rng.uniform(x0 + 6.0, x1 - 6.0), rng.uniform(y0 + 6.0, y1 - 6.0)
        r = rng.uniform(0.6, 1.6)
        f.ellipse(px, py, r * 1.3, r, LIMESTONE_SHADE, body=False)
        f.ellipse(px - 0.3, py - 0.4, r * 0.7, r * 0.5, LIMESTONE_DARK, body=False)
    # Light on the top of the face, just inside its top edge.
    top_edge = sorted((p for p in outline if p[1] < y0 + (y1 - y0) * 0.3), key=lambda p: p[0])
    if len(top_edge) >= 2:
        f.ink([(x + (4.0 if x < cx else -4.0), y + 4.0) for x, y in top_edge], 1.2, LIMESTONE_LIGHT)


def _cracks(f: K.Frame, box: Tuple[float, float, float, float], count: int, seed: str) -> None:
    """Fine cracks in the rock, drawn over the paint, because the rock is
    older than the paint and keeps moving."""
    rng = random.Random(seed)
    x0, y0, x1, y1 = box
    for _ in range(count):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        pts = [(x, y)]
        for _ in range(4):
            x += rng.uniform(-6.0, 6.0)
            y += rng.uniform(2.0, 6.0)
            pts.append((min(x1, max(x0, x)), min(y1, y)))
        f.ink(pts, 0.6, LIMESTONE_DARK)


def _hand(cx: float, cy: float, s: float, angle: float) -> List[Tuple[List[Point], float]]:
    """A hand as round strokes: (points, width) for the palm, the wrist and
    each finger. The fingers point up; `angle` turns the hand."""
    fingers = [(-7.0, 0.0, -14.0, -10.0), (-3.8, -6.0, -6.4, -21.0), (0.4, -6.6, 0.2, -23.5), (4.4, -6.0, 6.8, -21.0), (7.2, -3.0, 12.6, -15.0)]
    strokes = [([(cx + a * s, cy + b * s), (cx + c * s, cy + d * s)], 3.8 * s) for a, b, c, d in fingers]
    strokes.append(([(cx, cy - 1.0 * s), (cx, cy + 5.0 * s)], 15.0 * s))
    strokes.append(([(cx - 0.4 * s, cy + 6.0 * s), (cx - 0.4 * s, cy + 18.0 * s)], 9.6 * s))
    return [(K.turn(pts, cx, cy, angle), wd) for pts, wd in strokes]


def _stencil(f: K.Frame, cx: float, cy: float, s: float, angle: float, spray: RGBA, wall: RGBA, seed: str) -> None:
    """A hand stencil. The painter held a hand flat to the wall and blew
    ochre round it through a tube. The hand stays the colour of the rock,
    inside a cloud of paint that is thick near the hand and thin at its
    edge, with fine drops at the edge."""
    rng = random.Random(seed)
    oy = cy - 4.0 * s
    for k, a in ((1.0, 0.25), (0.86, 0.45), (0.74, 0.70), (0.62, 0.90)):
        f.poly(K.turn(K.ellipse_points(cx, oy, 21.0 * s * k, 27.0 * s * k, 28, 0.04, rng), cx, cy, angle), K.alpha(spray, a), body=False)
    for _ in range(30):
        a = rng.uniform(0.0, math.tau)
        r = rng.uniform(0.95, 1.2)
        x, y = K.turn([(cx + math.cos(a) * 21.0 * s * r, oy + math.sin(a) * 27.0 * s * r)], cx, cy, angle)[0]
        f.dot(x, y, rng.uniform(0.4, 0.9), K.alpha(spray, 0.6))
    for pts, wd in _hand(cx, cy, s, angle):
        f.limb(pts, wd, wall, body=False)


def _faded(f: K.Frame, box: Tuple[float, float, float, float], count: int, wall: RGBA, seed: str) -> None:
    """Small patches where the face of the rock came off and took the paint
    with it. The old paintings of Sulawesi are lost in this way."""
    rng = random.Random(seed)
    x0, y0, x1, y1 = box
    for _ in range(count):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        r = rng.uniform(1.4, 3.6)
        f.poly(K.ellipse_points(x, y, r * 1.4, r, 9, 0.25, rng), K.alpha(wall, 0.85), body=False)


# ---------------------------------------------------------------------------
# The painted story: a warty pig, three figures, two hands.
# ---------------------------------------------------------------------------


def _pig(f: K.Frame, x: float, y: float, s: float) -> None:
    """A Sulawesi warty pig painted in red ochre, as at Leang Tedongnge. It
    faces left. The body is a solid fill of ochre, a little uneven, inside
    a darker line. A crest of short hair stands on the head and the neck,
    and the face has warts. The legs are short."""
    def P(pts: Sequence[Point]) -> List[Point]:
        return [(x + px * s, y + py * s) for px, py in pts]

    body = P([(-46.0, -4.0), (-40.0, -16.0), (-28.0, -24.0), (-8.0, -27.0), (16.0, -27.0), (34.0, -24.0), (46.0, -14.0), (50.0, -2.0),
              (46.0, 10.0), (34.0, 16.0), (10.0, 18.0), (-14.0, 17.0), (-30.0, 12.0), (-40.0, 6.0)])
    head = P([(-40.0, -16.0), (-52.0, -15.0), (-64.0, -9.0), (-74.0, -2.0), (-79.0, 2.0), (-79.0, 8.0), (-72.0, 10.0), (-58.0, 10.0),
              (-42.0, 8.0)])
    ear = P([(-42.0, -14.0), (-40.0, -24.0), (-34.0, -17.0)])
    legs = [P([(-32.0, 8.0), (-29.0, 25.0), (-24.0, 25.0), (-21.0, 12.0)]), P([(-18.0, 14.0), (-16.0, 26.0), (-11.0, 26.0), (-8.0, 15.0)]),
            P([(24.0, 14.0), (27.0, 26.0), (32.0, 26.0), (35.0, 12.0)]), P([(38.0, 10.0), (41.0, 24.0), (46.0, 24.0), (46.0, 4.0)])]
    fill = K.alpha(OCHRE, 0.78)
    for leg in legs:
        f.poly(leg, fill, body=False)
    f.poly(body, fill, body=False)
    f.poly(head, fill, body=False)
    f.poly(ear, fill, body=False)
    # The painter's strokes: lines of thicker paint along the body.
    for k in range(4):
        yy = y + (-16.0 + k * 8.0) * s
        f.ink([(x - 30.0 * s, yy + 2.0 * s), (x, yy), (x + 32.0 * s, yy + 2.0 * s)], 1.6 * s, K.alpha(OCHRE_DARK, 0.22))
    # The snout ends in a flat disc.
    f.ink(P([(-79.0, 2.0), (-80.5, 5.0), (-79.0, 8.0)]), 1.2, K.alpha(OCHRE_DARK, 0.9))
    # The outline in a darker ochre.
    for shape in [body, head, ear] + legs:
        f.ink(shape + [shape[0]], 1.0, K.alpha(OCHRE_DARK, 0.9))
    # The crest: short stiff hairs from the brow back along the neck.
    for k in range(12):
        u = k / 11.0
        bx, by = x + (-50.0 + 44.0 * u) * s, y + (-14.0 - 12.0 * math.sin(math.pi * min(1.0, u * 1.2))) * s
        f.ink([(bx, by), (bx + 1.4 * s, by - 6.0 * s)], 1.0, K.alpha(OCHRE_DARK, 0.9))
    # The warts on the face, and the eye; the tail.
    for wx, wy in ((-58.0, -7.0), (-66.0, -3.0), (-62.0, 5.0)):
        f.dot(x + wx * s, y + wy * s, 1.5 * s, K.alpha(OCHRE_DARK, 0.9))
    f.dot(x - 50.0 * s, y - 6.0 * s, 1.1 * s, LIMESTONE)
    f.ink(P([(49.0, -6.0), (55.0, -2.0), (54.0, 6.0)]), 1.0, K.alpha(OCHRE_DARK, 0.9))


def _figure(f: K.Frame, x: float, y: float, s: float, lean: float, seed: str) -> None:
    """A small human-like figure in ochre: a body, a round head, legs that
    stride and one arm that holds a spear out at the pig. The painters of
    Karampuang drew such figures beside the pig; what they are is not
    known, so they are drawn simply."""
    rng = random.Random(seed)
    c = K.alpha(OCHRE, 0.9)
    hip = (x, y)
    neck = (x - lean * 3.0, y - 12.0 * s)
    f.limb([hip, neck], 2.6 * s, c, body=False)
    f.ellipse(neck[0] - lean * 1.0, neck[1] - 3.4 * s, 2.6 * s, 2.8 * s, c, body=False)
    f.limb([hip, (x - 4.0 * s, y + 10.0 * s)], 1.6 * s, c, body=False)
    f.limb([hip, (x + 3.6 * s, y + 10.0 * s)], 1.6 * s, c, body=False)
    sh = (neck[0], neck[1] + 2.0 * s)
    hand = (sh[0] - 6.0 * s, sh[1] + rng.uniform(-1.0, 2.0) * s)
    f.limb([sh, hand], 1.4 * s, c, body=False)
    f.limb([sh, (sh[0] + 4.0 * s, sh[1] + 7.0 * s)], 1.4 * s, c, body=False)
    # The spear: a long straight line through the hand, its point to the pig.
    f.ink([(hand[0] + 10.0 * s, hand[1] + 3.0 * s), (hand[0] - 16.0 * s, hand[1] - 4.0 * s)], 1.0 * s, K.alpha(OCHRE_DARK, 0.95))


def _draw_pig_painting(anim: str, i: int, n: int):
    w, h = PIG_PAINTING_FRAME
    f = K.Frame(PIG_PAINTING_FRAME)
    outline = [(8.0, 18.0), (40.0, 9.0), (110.0, 6.0), (180.0, 8.0), (232.0, 12.0), (249.0, 30.0), (250.0, 80.0), (246.0, 112.0),
               (220.0, 121.0), (130.0, 122.0), (40.0, 121.0), (10.0, 112.0), (6.0, 60.0)]
    _rock_panel(f, outline, "history_pig_painting rock")
    # The two hand stencils, over the back of the pig and at the left.
    _stencil(f, 32.0, 52.0, 0.72, -14.0, OCHRE, LIMESTONE, "pig stencil a")
    _stencil(f, 140.0, 40.0, 0.66, 10.0, OCHRE_MULBERRY, LIMESTONE, "pig stencil b")
    # The pig, life-like and large, and the three figures at its head and
    # behind it.
    _pig(f, 116.0, 86.0, 1.12)
    for k, (x, y, s, lean) in enumerate(((184.0, 74.0, 1.35, 0.6), (206.0, 90.0, 1.2, -0.3), (226.0, 70.0, 1.15, 0.4))):
        _figure(f, x, y, s, lean, f"figure {k}")
    # Wear: spalled patches and cracks over the paint.
    _faded(f, (40.0, 56.0, 230.0, 108.0), 6, LIMESTONE, "pig wear")
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# A panel of hand stencils.
# ---------------------------------------------------------------------------


def _draw_hand_stencils(anim: str, i: int, n: int):
    w, h = STENCILS_FRAME
    f = K.Frame(STENCILS_FRAME)
    outline = [(8.0, 14.0), (40.0, 7.0), (90.0, 6.0), (119.0, 14.0), (121.0, 50.0), (118.0, 88.0), (80.0, 90.0), (30.0, 90.0), (7.0, 84.0),
               (6.0, 46.0)]
    _rock_panel(f, outline, "history_sulawesi_hand_stencils rock")
    # Five hands of different people: big hands of adults and a small hand
    # of a child. They are turned a little each way, as hands are held.
    hands = [(28.0, 42.0, 0.66, -16.0, OCHRE), (64.0, 36.0, 0.74, 4.0, OCHRE_MULBERRY), (100.0, 44.0, 0.62, 18.0, OCHRE),
             (46.0, 74.0, 0.42, -8.0, OCHRE), (84.0, 76.0, 0.52, 12.0, OCHRE_MULBERRY)]
    for k, (x, y, s, a, colour) in enumerate(hands):
        _stencil(f, x, y, s, a, colour, LIMESTONE, f"stencil {k}")
    _faded(f, (16.0, 20.0, 112.0, 84.0), 3, LIMESTONE, "stencil wear")
    _cracks(f, (100.0, 60.0, 116.0, 86.0), 1, "stencil cracks")
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The stilt house.
# ---------------------------------------------------------------------------


def _draw_stilt_house(anim: str, i: int, n: int):
    w, h = STILT_HOUSE_FRAME
    f = K.Frame(STILT_HOUSE_FRAME)
    ground = h - 9.0
    floor = 140.0
    wall_top = 104.0
    x0, x1 = 44.0, 148.0
    # The posts: logs of hardwood set in the ground. The house stands high
    # over the wet ground and the floods, and air goes under the floor.
    for x, far in ((58.0, True), (96.0, True), (134.0, True)):
        f.limb([(x + 4.0, ground - 6.0), (x + 4.0, floor - 2.0)], 5.0, WOOD_DARK)
    for x in (50.0, 80.0, 112.0, 142.0):
        f.limb([(x, ground), (x, floor)], 6.4, WOOD)
        f.ink([(x - 1.4, ground - 2.0), (x - 1.4, floor + 2.0)], 1.0, WOOD_LIGHT)
        f.ellipse(x, ground, 5.0, 1.6, WOOD_DARK)
    # A cross brace of bamboo, lashed to the posts.
    f.limb([(50.0, ground - 40.0), (112.0, floor + 10.0)], 2.4, BAMBOO)
    f.limb([(80.0, floor + 10.0), (142.0, ground - 40.0)], 2.4, BAMBOO_SHADE)
    # The floor: a frame of beams and a deck of split bamboo.
    f.poly([(x0 - 8.0, floor - 4.0), (x1 + 8.0, floor - 4.0), (x1 + 8.0, floor + 4.0), (x0 - 8.0, floor + 4.0)], WOOD)
    f.ink([(x0 - 6.0, floor - 2.6), (x1 + 6.0, floor - 2.6)], 1.0, WOOD_LIGHT)
    for k in range(8):
        bx = x0 - 6.0 + k * 16.0
        f.ink([(bx, floor - 3.0), (bx, floor + 3.0)], 0.8, WOOD_DARK)
    # The walls: panels of woven split bamboo in a frame of poles.
    f.poly([(x0, wall_top), (x1, wall_top), (x1, floor - 4.0), (x0, floor - 4.0)], WEAVE)
    f.poly([(x0, floor - 12.0), (x1, floor - 12.0), (x1, floor - 4.0), (x0, floor - 4.0)], WEAVE_SHADE, body=False)
    for y in range(int(wall_top) + 3, int(floor - 4.0), 4):
        for x in range(int(x0) + 2, int(x1) - 2, 6):
            off = 3.0 if (y // 4) % 2 else 0.0
            f.ink([(x + off, y), (x + off + 3.0, y)], 0.6, WEAVE_SHADE)
    for x in (x0, (x0 + x1) / 2.0 - 16.0, (x0 + x1) / 2.0 + 16.0, x1):
        f.limb([(x, wall_top), (x, floor - 4.0)], 2.6, BAMBOO)
    f.limb([(x0, wall_top + 1.0), (x1, wall_top + 1.0)], 2.4, BAMBOO)
    # The door, in the middle, and a little light in it.
    dx0, dx1 = 86.0, 106.0
    f.poly([(dx0, wall_top + 6.0), (dx1, wall_top + 6.0), (dx1, floor - 4.0), (dx0, floor - 4.0)], DOORWAY, body=False)
    f.poly([(dx0, wall_top + 6.0), (dx0 + 5.0, wall_top + 6.0), (dx0 + 5.0, floor - 4.0), (dx0, floor - 4.0)], K.shade(DOORWAY, 0.7), body=False)
    for x in (dx0, dx1):
        f.limb([(x, wall_top + 5.0), (x, floor - 4.0)], 2.2, WOOD)
    f.limb([(dx0 - 2.0, wall_top + 5.0), (dx1 + 2.0, wall_top + 5.0)], 2.4, WOOD)
    # The roof: a saddle roof of thatch. Its ridge sags in the middle and
    # rises at the two ends, where the gables jut out over the walls, as
    # the bow and the stern of a boat. Seen from the side it is wider at the
    # ridge than at the eaves.
    eave_y = 112.0
    ridge = []
    for k in range(25):
        u = k / 24.0
        x = 12.0 + (180.0 - 12.0) * u
        # A flat sag in the middle that rises fast near the ends.
        ridge.append((x, 58.0 - 34.0 * abs(2.0 * u - 1.0) ** 2.6))
    roof = [(x0 - 10.0, eave_y)] + ridge + [(x1 + 10.0, eave_y)]
    f.poly(roof, THATCH)
    # The lower band of thatch in shade, and the fall of the straw.
    f.poly([(x0 - 10.0, eave_y), (x1 + 10.0, eave_y), (x1 + 4.0, eave_y - 10.0), (x0 - 4.0, eave_y - 10.0)], THATCH_SHADE, body=False)
    rng = random.Random("history_bamboo_stilt_house thatch")
    for k in range(46):
        u = k / 45.0
        tx, ty = ridge[min(24, int(u * 24.0))]
        bx = x0 - 8.0 + (x1 - x0 + 16.0) * u
        f.ink([(tx + (bx - tx) * 0.15, ty + 6.0), (bx + rng.uniform(-1.0, 1.0), eave_y - 2.0)], 0.7, THATCH_SHADE if k % 2 else THATCH_LIGHT)
    # The ragged edge of the eave.
    for k in range(18):
        ex = x0 - 8.0 + k * (x1 - x0 + 16.0) / 17.0
        f.limb([(ex, eave_y - 1.0), (ex + rng.uniform(-1.0, 1.0), eave_y + rng.uniform(2.0, 4.0))], 1.6, THATCH_SHADE)
    # The ridge: a bound roll of thatch along the top, and the gable ends
    # with their tips that curve up.
    f.limb(ridge, 3.6, THATCH_SHADE)
    f.ink(ridge[2:-2], 1.0, THATCH_LIGHT)
    for k in range(3, 22, 3):
        rx, ry = ridge[k]
        f.ink([(rx - 1.4, ry - 2.0), (rx + 1.4, ry + 2.0)], 1.0, WOOD_DARK)
    # The gable ends: a board under each tip of the ridge, that closes the
    # end of the roof, and a carved finial that turns up like a prow.
    for sx, tip in ((1.0, ridge[0]), (-1.0, ridge[-1])):
        f.poly([tip, (tip[0] + sx * 18.0, tip[1] + 8.0), (tip[0] + sx * 30.0, eave_y - 26.0), (tip[0] + sx * 22.0, eave_y - 26.0)], WOOD)
        f.ink([(tip[0] + sx * 4.0, tip[1] + 6.0), (tip[0] + sx * 22.0, eave_y - 28.0)], 1.0, WOOD_LIGHT)
        f.limb([tip, (tip[0] - sx * 3.0, tip[1] - 6.0)], 2.6, WOOD_DARK)
    # The ladder: two poles with rungs, from the ground to the door.
    for lx in (88.0, 104.0):
        f.limb([(lx - 8.0, ground), (lx, floor + 2.0)], 2.6, BAMBOO)
    for k in range(1, 8):
        u = k / 8.0
        y = ground + (floor + 2.0 - ground) * u
        f.limb([(80.0 + 8.0 * u, y), (96.0 + 8.0 * u, y)], 1.8, BAMBOO_SHADE)
    # A low red-slipped pot and a basket under the floor.
    f.ellipse(64.0, ground - 6.0, 7.0, 6.0, SLIP)
    f.ellipse(62.0, ground - 8.0, 2.4, 1.6, SLIP_LIGHT, body=False)
    f.poly([(120.0, ground), (124.0, ground - 10.0), (138.0, ground - 10.0), (140.0, ground)], BASKET)
    f.ink([(122.0, ground - 5.0), (139.0, ground - 5.0)], 0.8, BASKET_SHADE)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# The bronze drum.
# ---------------------------------------------------------------------------


def _bird(f: K.Frame, x: float, y: float, s: float, a: float, colour: RGBA) -> None:
    """A long-billed bird in flight, as on the tops of Dong Son drums: a
    long body, a long bill in front, wings out and a short tail."""
    def T(pts: Sequence[Point]) -> List[Point]:
        return K.turn([(x + px * s, y + py * s) for px, py in pts], x, y, a)

    f.poly(T([(-4.0, 0.0), (0.0, -0.8), (3.0, -0.4), (6.0, 0.0), (3.0, 0.5), (0.0, 0.8)]), colour, body=False)
    f.ink(T([(5.5, 0.0), (8.0, 0.2)]), 0.4 * s, colour)
    f.poly(T([(-1.0, 0.0), (1.0, 0.0), (-1.5, -3.0)]), colour, body=False)
    f.poly(T([(-4.0, 0.0), (-6.0, -1.0), (-6.0, 1.0)]), colour, body=False)


def _draw_bronze_drum(anim: str, i: int, n: int):
    w, h = DRUM_FRAME
    f = K.Frame(DRUM_FRAME)
    cx = w / 2.0
    top_y, rx, ry = 22.0, 38.0, 14.0
    ground = h - 5.0
    # The body: a bulge under the top (the mantle), a straight waist and a
    # foot that flares. The bronze is brown with green patina in patches.
    profile = [(top_y, 1.00), (28.0, 1.04), (36.0, 0.98), (44.0, 0.84), (54.0, 0.84), (64.0, 0.92), (ground - 2.0, 1.00)]
    left = [(cx - rx * k, y) for y, k in profile]
    right = [(cx + rx * k, y) for y, k in profile]
    f.poly(left + [(cx, ground + 1.0)] + right[::-1], BRONZE)
    f.ellipse(cx, ground - 2.0, rx, 3.0, BRONZE)
    # The shade on the right side, the light on the left side.
    f.poly([(cx + rx * 0.45, y) for y, _ in profile] + [(cx + rx * k - 1.0, y) for y, k in profile[::-1]], BRONZE_SHADE, body=False)
    f.poly([(cx - rx * k + 2.0, y) for y, k in profile[1:-1]] + [(cx - rx * k * 0.7, y) for y, k in profile[-2:0:-1]], BRONZE_LIGHT, body=False)
    # The bands of the mantle: rows of small circles with dots, between lines.
    for y, k in ((30.0, 1.03), (38.0, 0.96)):
        f.ink([(cx - rx * k + 1.0, y), (cx - rx * k * 0.5, y + 1.2), (cx, y + 1.6), (cx + rx * k * 0.5, y + 1.2), (cx + rx * k - 1.0, y)], 0.7, BRONZE_DARK)
    for j in range(9):
        u = (j + 0.5) / 9.0 * 2.0 - 1.0
        px = cx + u * rx * 0.94
        f.ellipse(px, 34.0 + 1.4 * (1.0 - u * u), 1.6, 1.4, BRONZE_DARK, body=False)
        f.dot(px, 34.0 + 1.4 * (1.0 - u * u), 0.5, BRONZE_LIGHT)
    # The bands of the waist: lines and a row of short slanted strokes.
    for y in (48.0, 58.0):
        f.ink([(cx - rx * 0.84 + 1.0, y), (cx, y + 1.4), (cx + rx * 0.84 - 1.0, y)], 0.7, BRONZE_DARK)
    for j in range(10):
        u = (j + 0.5) / 10.0 * 2.0 - 1.0
        px = cx + u * rx * 0.78
        f.ink([(px - 1.0, 50.0 + 1.2 * (1 - u * u)), (px + 1.0, 56.0 + 1.2 * (1 - u * u))], 0.6, BRONZE_DARK)
    # The handles: two small loops on each side, under the mantle.
    for s in (-1.0, 1.0):
        f.limb([(cx + s * rx * 1.02, 30.0), (cx + s * (rx + 4.0), 34.0), (cx + s * rx * 0.94, 40.0)], 1.8, BRONZE_SHADE)
    # Patina: soft green patches.
    rng = random.Random("history_bronze_drum patina")
    for _ in range(4):
        y = rng.uniform(ground - 14.0, ground - 4.0)
        px = cx + rng.uniform(-0.8, 0.8) * rx * 0.86
        f.ellipse(px, y, rng.uniform(5.0, 8.0), rng.uniform(1.2, 2.0), K.alpha(PATINA, 0.35), body=False)
    f.ink([(cx - rx * 0.84 + 2.0, 53.0), (cx, 54.4), (cx + rx * 0.84 - 2.0, 53.0)], 1.2, K.alpha(PATINA, 0.6))
    # The top: a flat round face, seen a little from above.
    f.ellipse(cx, top_y, rx, ry, BRONZE_LIGHT)
    f.ellipse(cx, top_y, rx - 2.0, ry - 1.2, K.shade(BRONZE_LIGHT, 0.86), body=False)
    # The rings of the face.
    for k in (0.84, 0.50):
        pts = K.ellipse_points(cx, top_y, rx * k, ry * k, 32)
        f.ink(pts + [pts[0]], 0.6, BRONZE_SHADE)
    # The ring of birds in flight, between the outer rings. They fly round
    # the star, all the same way.
    for j in range(10):
        a = math.tau * j / 10.0
        bx, by = cx + math.cos(a) * rx * 0.67, top_y + math.sin(a) * ry * 0.67
        heading = math.degrees(math.atan2(math.cos(a) * ry, -math.sin(a) * rx))
        _bird(f, bx, by, 0.95, heading, A.OUTLINE)
    # The star in the middle: twelve rays, and small fans of light between
    # them.
    star = []
    for j in range(24):
        a = math.tau * j / 24.0
        r = 1.0 if j % 2 == 0 else 0.5
        star.append((cx + math.cos(a) * rx * 0.42 * r, top_y + math.sin(a) * ry * 0.46 * r))
    f.poly(star, (240, 214, 132, 255), body=False)
    f.ink(star + [star[0]], 0.5, BRONZE_SHADE)
    f.ellipse(cx, top_y, 2.0, 0.9, BRONZE_SHADE, body=False)
    # The frogs on the rim: small bronze frogs that sit and look in.
    for a_deg in (195.0, 290.0, 345.0, 50.0, 130.0):
        a = math.radians(a_deg)
        fx, fy = cx + math.cos(a) * rx * 0.90, top_y + math.sin(a) * ry * 0.90
        f.ellipse(fx, fy - 1.2, 3.6, 2.6, A.OUTLINE, body=False)
        f.ellipse(fx, fy - 1.2, 2.8, 1.9, BRONZE)
        f.ellipse(fx - 0.6, fy - 1.8, 1.3, 0.8, BRONZE_LIGHT, body=False)
        f.dot(fx - 1.3, fy - 2.6, 0.6, A.OUTLINE)
        f.dot(fx + 1.3, fy - 2.6, 0.6, A.OUTLINE)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# Rice sheaves on a dike.
# ---------------------------------------------------------------------------


def _sheaf(f: K.Frame, cx: float, foot: float, height: float, seed: str) -> None:
    """A sheaf of rice: the stalks bound at the middle with a twist of
    straw, spread at the foot so that it stands, and the heads of grain
    that bend over at the top."""
    rng = random.Random(seed)
    tie = foot - height * 0.45
    top = foot - height
    stalks = []
    for k in range(11):
        u = (k - 5.0) / 5.0
        stalks.append((u, (cx + u * 8.0, foot), (cx + u * 2.0, tie), (cx + u * 7.0, top + abs(u) * 4.0 + rng.uniform(-1.0, 1.0))))
    for u, base, mid, tip in stalks:
        f.limb([base, mid, tip], 1.8, STRAW if abs(u) < 0.6 else STRAW_SHADE)
    for k, (u, base, mid, tip) in enumerate(stalks):
        side = 1.0 if u > 0 or (u == 0 and k % 2) else -1.0
        head = [tip, (tip[0] + side * 4.0, tip[1] - 2.0), (tip[0] + side * 8.0, tip[1] + 4.0), (tip[0] + side * 9.0, tip[1] + 13.0)]
        f.limb(head, 1.2, GRAIN_SHADE)
        for q in range(7):
            v = 0.3 + q * 0.38
            p0, p1 = head[min(3, int(v))], head[min(3, int(v) + 1)]
            v -= int(v)
            gx, gy = p0[0] + (p1[0] - p0[0]) * v, p0[1] + (p1[1] - p0[1]) * v
            f.ellipse(gx + side * 0.9, gy, 1.3, 1.9, GRAIN if q % 2 else K.shade(GRAIN, 1.08))
    f.limb([(cx - 4.0, tie - 1.0), (cx + 4.0, tie + 0.6)], 3.0, STRAW_SHADE)
    f.ink([(cx - 3.0, tie - 1.2), (cx + 3.0, tie)], 0.6, STRAW_LIGHT)


def _draw_rice_sheaves(anim: str, i: int, n: int):
    w, h = SHEAVES_FRAME
    f = K.Frame(SHEAVES_FRAME)
    # The dike: a low bank of earth between two flooded fields, with grass
    # on its top. The farmers walk on the dikes and stand the cut rice on
    # them to dry.
    top = 48.0
    rng = random.Random("history_rice_sheaves")
    bank = [(5.0, h - 5.0), (12.0, top + 1.0)] + [(x, top + rng.uniform(-0.8, 0.8)) for x in range(20, 112, 10)] + [(116.0, top + 1.0), (123.0, h - 5.0)]
    f.poly(bank, EARTH)
    f.poly([(8.0, h - 5.0), (13.0, top + 6.0), (115.0, top + 6.0), (120.0, h - 5.0)], EARTH_SHADE, body=False)
    f.ink([(9.0, h - 6.0), (119.0, h - 6.0)], 1.0, K.alpha((150, 184, 196, 255), 0.9))
    for x in range(10, 120, 4):
        f.ink([(x, top + 1.0), (x + rng.uniform(-1.4, 1.4), top - rng.uniform(1.5, 3.0))], 0.8, GRASS if x % 8 else GRASS_SHADE)
    # Three sheaves.
    _sheaf(f, 26.0, top + 1.0, 36.0, "sheaf a")
    _sheaf(f, 50.0, top + 1.0, 39.0, "sheaf b")
    _sheaf(f, 73.0, top + 1.0, 34.0, "sheaf c")
    # The flat basket: a wide round tray of woven bamboo, for winnowing the
    # grain. It lies on the dike, tilted a little, with grain in it.
    bx, by = 100.0, top - 3.0
    f.ellipse(bx, by, 18.0, 6.0, BASKET)
    f.ellipse(bx, by - 0.6, 15.0, 4.4, BASKET_SHADE, body=False)
    for k in range(-3, 4):
        f.ink([(bx + k * 4.0 - 2.0, by - 4.0), (bx + k * 4.0 + 2.0, by + 4.0)], 0.5, K.shade(BASKET_SHADE, 0.85))
    f.ellipse(bx + 2.0, by, 8.0, 2.4, GRAIN, body=False)
    f.ellipse(bx + 0.6, by - 0.6, 3.6, 1.0, STRAW_LIGHT, body=False)
    f.ink(K.ellipse_points(bx, by, 18.0, 6.0, 28)[16:28] + K.ellipse_points(bx, by, 18.0, 6.0, 28)[0:2], 1.0, STRAW_LIGHT)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# Red-slipped pots.
# ---------------------------------------------------------------------------


def _pot(f: K.Frame, cx: float, foot: float, r: float, neck: float, dots: bool) -> None:
    """A round pot of fired clay with a short neck and a rim that turns out.
    Before the firing the potter coated it with a slip of red clay and
    rubbed it smooth, so it shines a little. With `dots`, a band of dots
    pressed with a toothed stamp goes round the shoulder."""
    cy = foot - r * 0.92
    f.ellipse(cx, cy, r, r * 0.92, SLIP)
    f.poly([(cx - neck, cy - r * 0.80), (cx + neck, cy - r * 0.80), (cx + neck * 0.9, cy - r * 1.04), (cx - neck * 0.9, cy - r * 1.04)], SLIP)
    f.ellipse(cx, cy - r * 1.06, neck * 1.32, r * 0.14, SLIP)
    f.ellipse(cx, cy - r * 1.06, neck * 0.98, r * 0.08, SLIP_SHADE, body=False)
    # One shade on the lower right, and a soft shine on the upper left.
    arc = [math.radians(d) for d in range(-40, 181, 10)]
    outer = [(cx + math.cos(a) * r * 0.98, cy + math.sin(a) * r * 0.90) for a in arc]
    inner = [(cx - r * 0.18 + math.cos(a) * r * 0.86, cy - r * 0.16 + math.sin(a) * r * 0.80) for a in arc]
    f.poly(outer + inner[::-1], SLIP_SHADE, body=False)
    f.ellipse(cx - r * 0.38, cy - r * 0.36, r * 0.24, r * 0.14, SLIP_LIGHT, body=False)
    if dots:
        y = cy - r * 0.42
        f.ink([(cx - r * 0.86, y - 2.2), (cx, y - 1.0), (cx + r * 0.86, y - 2.2)], 0.6, SLIP_SHADE)
        f.ink([(cx - r * 0.86, y + 2.2), (cx, y + 3.4), (cx + r * 0.86, y + 2.2)], 0.6, SLIP_SHADE)
        for j in range(13):
            u = (j + 0.5) / 13.0 * 2.0 - 1.0
            f.dot(cx + u * r * 0.84, y + 1.2 * (1.0 - u * u) - 0.2 * abs(u), 0.95, (232, 196, 150, 255))


def _draw_red_slip_pots(anim: str, i: int, n: int):
    w, h = POTS_FRAME
    f = K.Frame(POTS_FRAME)
    foot = h - 5.0
    # The big pot at the back, then a small one and a middle one in front.
    _pot(f, 54.0, foot - 4.0, 19.0, 9.0, True)
    _pot(f, 22.0, foot, 13.0, 6.0, False)
    _pot(f, 76.0, foot, 12.0, 6.0, False)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# Publication.
# ---------------------------------------------------------------------------

SCENERY = ["prop", "scenery", "history", "southeast_asia"]

FRAMES: Dict[str, Tuple[int, int]] = {
    "history_pig_painting": PIG_PAINTING_FRAME,
    "history_sulawesi_hand_stencils": STENCILS_FRAME,
    "history_bamboo_stilt_house": STILT_HOUSE_FRAME,
    "history_bronze_drum": DRUM_FRAME,
    "history_rice_sheaves": SHEAVES_FRAME,
    "history_red_slip_pots": POTS_FRAME,
}
DRAW: Dict[str, Callable] = {
    "history_pig_painting": _draw_pig_painting,
    "history_sulawesi_hand_stencils": _draw_hand_stencils,
    "history_bamboo_stilt_house": _draw_stilt_house,
    "history_bronze_drum": _draw_bronze_drum,
    "history_rice_sheaves": _draw_rice_sheaves,
    "history_red_slip_pots": _draw_red_slip_pots,
}
DISPLAY = {
    "history_pig_painting": "Pig Painting",
    "history_sulawesi_hand_stencils": "Sulawesi Hand Stencils",
    "history_bamboo_stilt_house": "Bamboo Stilt House",
    "history_bronze_drum": "Bronze Drum",
    "history_rice_sheaves": "Rice Sheaves",
    "history_red_slip_pots": "Red-Slip Pots",
}
ROWS: Dict[str, List[Tuple[str, int, int]]] = {}


def _foot(name: str) -> Dict[str, Tuple[float, float]]:
    w, h = FRAMES[name]
    return {"foot": (w / 2.0, float(h))}


TARGETS: Dict[str, dict] = {
    name: _publisher(name, DISPLAY[name], ROWS.get(name, STILL), FRAMES[name], DRAW[name], _foot(name), "Scenery", SCENERY) for name in DISPLAY
}
