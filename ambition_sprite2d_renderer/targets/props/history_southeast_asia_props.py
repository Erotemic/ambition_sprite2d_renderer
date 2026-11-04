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

From about 650 CE the kingdom of Srivijaya, on Sumatra, held the straits
between India and China. Its ships were big ships of planks, the jong:
they had no outrigger, two or more masts with canted sails of matting, and
two steering oars at the stern. They carried pepper, camphor, cloth and
Chinese jars. In central Java (about 800 CE) the builders of Borobudur
carved ships with outriggers into the walls, and set bell-shaped stupas
with lattice walls on its round terraces. At Angkor (about 1100 CE) the
Khmer built their temples of sandstone on cores of red laterite; oxen
pulled the blocks and the goods in carts with big wheels.

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
- ``history_jong``: the look of a platform, a big ship of planks with no
  outrigger, two masts with canted tanja sails, a deckhouse of thatch and
  two steering oars at the stern. The top of its gunwale is the platform
  (`platform_looks.ron`: `JONG_SPAN` = (24, 424), `JONG_TOP` = 132, in a
  448 x 224 frame).
- ``history_ship_relief``: scenery, a panel of grey andesite carved in the
  style of Borobudur: a ship with an outrigger, its sails and its crew,
  inside a moulded frame. It shows daily life only.
- ``history_bell_stupa``: scenery, a bell-shaped stupa of andesite with
  diamond-shaped holes, on a round base of lotus petals, with a square
  block and a short spire on its top. The space inside is dark.
- ``history_sandstone_blocks``: scenery, dressed blocks of grey-pink
  sandstone, some with pairs of peg holes, a block of red laterite and a
  wooden lever.
- ``history_ox_cart``: scenery, a Khmer cart with two spoked wheels and a
  curved roof of matting, pulled by one zebu ox.
- ``history_trade_goods``: scenery, sacks of black pepper (one open), a
  bundle of camphor wood, two Chinese storage jars and a bolt of cloth.

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
JONG_FRAME = (448, 224)
JONG_SPAN = (24.0, 424.0)
JONG_TOP = 132.0
JONG_DEPTH = 52.0
RELIEF_FRAME = (256, 128)
BELL_STUPA_FRAME = (128, 160)
BLOCKS_FRAME = (160, 80)
OX_CART_FRAME = (192, 128)
GOODS_FRAME = (160, 96)

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

ROPE = (196, 168, 112, 255)
MATTING = (204, 174, 112, 255)
MATTING_LIGHT = (228, 204, 146, 255)
MATTING_SHADE = (166, 134, 80, 255)
MATTING_DARK = (122, 94, 56, 255)

STONE = (148, 144, 138, 255)
STONE_LIGHT = (186, 182, 172, 255)
STONE_SHADE = (118, 114, 110, 255)
STONE_DARK = (80, 76, 74, 255)
LICHEN = (96, 112, 84, 255)
STONE_SUNK = (108, 104, 100, 255)
HOLLOW = (34, 28, 28, 255)

SAND = (168, 148, 142, 255)
SAND_LIGHT = (196, 180, 170, 255)
SAND_SHADE = (132, 112, 108, 255)
SAND_DARK = (88, 72, 70, 255)
LATERITE = (162, 76, 50, 255)
LATERITE_LIGHT = (192, 108, 74, 255)
LATERITE_SHADE = (122, 52, 36, 255)
LATERITE_DARK = (84, 36, 26, 255)

ZEBU = (220, 208, 186, 255)
ZEBU_LIGHT = (240, 232, 214, 255)
ZEBU_SHADE = (176, 160, 136, 255)
ZEBU_DARK = (106, 90, 76, 255)
HORN = (196, 180, 150, 255)
HOOF = (62, 50, 42, 255)
HORN_TIP = (70, 60, 52, 255)

STONEWARE = (190, 172, 140, 255)
GLAZE = (120, 110, 54, 255)
GLAZE_LIGHT = (176, 166, 100, 255)
GLAZE_SHADE = (82, 72, 36, 255)
SACKING = (186, 160, 112, 255)
SACKING_LIGHT = (214, 192, 146, 255)
SACKING_SHADE = (140, 116, 76, 255)
PEPPER = (52, 44, 40, 255)
PEPPER_DARK = (30, 24, 22, 255)
PEPPER_LIGHT = (110, 98, 88, 255)
CAMPHOR = (210, 186, 140, 255)
CAMPHOR_LIGHT = (232, 214, 172, 255)
CAMPHOR_SHADE = (164, 136, 92, 255)
RATTAN = (150, 112, 60, 255)
CLOTH = (58, 72, 128, 255)
CLOTH_LIGHT = (96, 112, 168, 255)
CLOTH_SHADE = (38, 46, 90, 255)
CLOTH_BAND = (176, 60, 44, 255)


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
# Shared parts of the ships: a canted sail of matting.
# ---------------------------------------------------------------------------


def _box(cx: float, cy: float, w: float, h: float, deg: float) -> List[Point]:
    """A rectangle about its middle, turned `deg` clockwise. The corners go
    top left, top right, bottom right, bottom left."""
    pts = [(cx - w / 2.0, cy - h / 2.0), (cx + w / 2.0, cy - h / 2.0), (cx + w / 2.0, cy + h / 2.0), (cx - w / 2.0, cy + h / 2.0)]
    return K.turn(pts, cx, cy, deg)


def _mix(p: Point, q: Point, u: float) -> Point:
    return (p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u)


def _tanja_sail(f: K.Frame, cx: float, cy: float, w: float, h: float, deg: float, boom: float) -> Tuple[Point, Point]:
    """A tanja sail: a rectangle of woven matting, tilted forward, with a
    boom of bamboo along its top and its bottom. The ship sails to the
    right, so a turn clockwise tips the top of the sail to the bow. The
    sailors of the archipelago set the sail at this cant so that it can
    take the wind from the side. The return is the two ends of the lower
    boom (aft, fore), for the sheets."""
    tl, tr, br, bl = _box(cx, cy, w, h, deg)
    f.poly([tl, tr, br, bl], MATTING)
    # The belly of the sail is in shade at its lower aft corner.
    f.poly([_mix(tl, bl, 0.45), _mix(bl, br, 0.0), _mix(bl, br, 0.62), _mix(tr, br, 0.80)], MATTING_SHADE, body=False)
    f.poly([_mix(tl, tr, 0.05), _mix(tl, tr, 0.30), _mix(tl, bl, 0.30), _mix(tl, bl, 0.06)], MATTING_LIGHT, body=False)
    # The seams of the mats run along the booms; short cross strokes show
    # the weave between them.
    rows = max(4, int(h / 11.0))
    for k in range(1, rows):
        u = k / float(rows)
        f.ink([_mix(tl, bl, u), _mix(tr, br, u)], 0.8, MATTING_DARK)
    cols = max(5, int(w / 9.0))
    for k in range(rows):
        for j in range(cols):
            u = (k + 0.5) / rows
            v = (j + 0.5 + 0.5 * (k % 2)) / cols
            if v >= 1.0:
                continue
            a = _mix(_mix(tl, bl, u - 0.25 / rows), _mix(tr, br, u - 0.25 / rows), v)
            b = _mix(_mix(tl, bl, u + 0.25 / rows), _mix(tr, br, u + 0.25 / rows), v)
            f.ink([a, b], 0.6, K.alpha(MATTING_DARK, 0.55))
    # The booms of bamboo stick out a little past the mat, with nodes.
    out = []
    for p, q in ((tl, tr), (bl, br)):
        dx, dy = (q[0] - p[0]) / w, (q[1] - p[1]) / w
        a = (p[0] - dx * boom, p[1] - dy * boom)
        b = (q[0] + dx * boom, q[1] + dy * boom)
        f.limb([a, b], 3.4, BAMBOO)
        f.ink([(a[0], a[1] - 0.9), (b[0], b[1] - 0.9)], 0.8, BAMBOO_LIGHT)
        for k in range(1, 6):
            n = _mix(a, b, k / 6.0)
            f.ink([(n[0] + dy * 1.6, n[1] - dx * 1.6), (n[0] - dy * 1.6, n[1] + dx * 1.6)], 0.8, BAMBOO_SHADE)
        out.append((a, b))
    return out[1]


# ---------------------------------------------------------------------------
# The jong: a big ship of planks (a platform).
# ---------------------------------------------------------------------------


def _jong_sheer(x: float) -> float:
    """The top of the gunwale at `x`: level in the middle, and swept up to
    the high stern and the higher bow."""
    x0, x1 = JONG_SPAN
    u = (x - (x0 + x1) / 2.0) / ((x1 - x0) / 2.0)
    over = max(0.0, (abs(u) - 0.55) / 0.45)
    rise = 38.0 if u > 0 else 32.0
    return JONG_TOP - rise * over ** 2


def _jong_keel(x: float) -> float:
    """The bottom of the hull at `x`. The ends curve up to the stem and the
    sternpost; the middle is deep, for cargo."""
    x0, x1 = JONG_SPAN
    k0, k1 = x0 + 20.0, x1 - 22.0
    u = max(-1.0, min(1.0, (x - (k0 + k1) / 2.0) / ((k1 - k0) / 2.0)))
    return JONG_TOP - 8.0 + (JONG_DEPTH + 8.0) * (1.0 - abs(u) ** 3.2) ** 0.55


def _quarter_rudder(f: K.Frame, top: Point, blade: Point, wood: RGBA, shade: RGBA, body: bool = True) -> None:
    """A steering oar that hangs on the quarter of the ship. Its loom goes
    down from a beam at the stern, and a wide blade goes in the water."""
    f.limb([top, blade], 4.4, wood, body)
    dx, dy = blade[0] - top[0], blade[1] - top[1]
    r = math.hypot(dx, dy)
    ux, uy = dx / r, dy / r
    px, py = -uy, ux
    b0 = (blade[0] - ux * 30.0, blade[1] - uy * 30.0)
    f.poly([(b0[0] + px * 2.4, b0[1] + py * 2.4), (blade[0] + px * 7.0, blade[1] + py * 7.0), (blade[0] + ux * 3.0, blade[1] + uy * 3.0),
            (blade[0] - px * 5.0, blade[1] - py * 5.0), (b0[0] - px * 2.4, b0[1] - py * 2.4)], wood, body)
    f.ink([(b0[0] + px * 0.8, b0[1] + py * 0.8), (blade[0] + px * 1.8, blade[1] + py * 1.8)], 1.0, shade)


def _draw_jong(anim: str, i: int, n: int):
    f = K.Frame(JONG_FRAME)
    x0, x1 = JONG_SPAN
    top = JONG_TOP
    xs = [x0 + (x1 - x0) * k / 80.0 for k in range(81)]
    # The far quarter rudder: only its blade shows under the hull.
    _quarter_rudder(f, (x0 + 46.0, top - 22.0), (x0 + 16.0, top + 64.0), WOOD_DARK, K.shade(WOOD_DARK, 0.7))
    # The two masts, with stays to the bow and the stern.
    main_x, fore_x = 236.0, 338.0
    f.limb([(main_x, top), (main_x, 16.0)], 4.6, WOOD)
    f.limb([(fore_x, top), (fore_x, 36.0)], 4.0, WOOD)
    f.ink([(main_x, 18.0), (x1 - 4.0, _jong_sheer(x1 - 4.0))], 0.9, ROPE)
    f.ink([(main_x, 18.0), (x0 + 30.0, _jong_sheer(x0 + 30.0) - 2.0)], 0.9, ROPE)
    f.ink([(fore_x, 38.0), (x1 - 2.0, _jong_sheer(x1 - 2.0) + 2.0)], 0.9, ROPE)
    # The deckhouse of thatch, aft, on the deck behind the gunwale.
    hx0, hx1 = 62.0, 150.0
    f.poly([(hx0 + 4.0, top - 22.0), (hx1 - 4.0, top - 22.0), (hx1 - 4.0, top), (hx0 + 4.0, top)], WEAVE)
    for y in range(int(top) - 19, int(top), 4):
        f.ink([(hx0 + 6.0, y), (hx1 - 6.0, y)], 0.6, WEAVE_SHADE)
    f.poly([(hx0 + 30.0, top - 18.0), (hx0 + 44.0, top - 18.0), (hx0 + 44.0, top), (hx0 + 30.0, top)], DOORWAY, body=False)
    roof = [(hx0 - 4.0, top - 18.0)] + [(hx0 + (hx1 - hx0) * u, top - 22.0 - 20.0 * math.sin(math.pi * u) ** 0.7) for u in [k / 12.0 for k in range(13)]] + [(hx1 + 4.0, top - 18.0)]
    f.poly(roof + [(hx1 + 2.0, top - 14.0), (hx0 - 2.0, top - 14.0)], THATCH)
    f.poly([(hx0 - 4.0, top - 18.0), (hx1 + 4.0, top - 18.0), (hx1 + 2.0, top - 14.0), (hx0 - 2.0, top - 14.0)], THATCH_SHADE, body=False)
    rng = random.Random("history_jong thatch")
    for k in range(22):
        u = (k + 0.5) / 22.0
        rx, ry = hx0 + (hx1 - hx0) * u, top - 22.0 - 20.0 * math.sin(math.pi * u) ** 0.7
        f.ink([(rx, ry + 3.0), (rx + (u - 0.5) * 8.0 + rng.uniform(-1.0, 1.0), top - 16.0)], 0.7, THATCH_SHADE if k % 2 else THATCH_LIGHT)
    f.ink([(hx0 + (hx1 - hx0) * u, top - 22.0 - 20.0 * math.sin(math.pi * u) ** 0.7) for u in [k / 12.0 for k in range(2, 11)]], 1.4, THATCH_LIGHT)
    # The hull: strakes of planks, edge to edge, joined with wooden dowels.
    # Its gunwale is the platform.
    keel_xs = [x for x in xs if x0 + 20.0 <= x <= x1 - 22.0]
    hull = [(x, _jong_sheer(x)) for x in xs] + [(x, _jong_keel(x)) for x in keel_xs[::-1]]
    f.poly(hull, WOOD)
    f.poly([(x, _jong_sheer(x) + (_jong_keel(x) - _jong_sheer(x)) * 0.58) for x in keel_xs] + [(x, _jong_keel(x)) for x in keel_xs[::-1]], WOOD_DARK, body=False)
    for t in (0.22, 0.40, 0.58, 0.76):
        seam = [(x, _jong_sheer(x) + (_jong_keel(x) - _jong_sheer(x)) * t) for x in keel_xs]
        f.ink(seam, 0.9, K.shade(WOOD_DARK, 0.8))
        for k in range(3, len(seam) - 3, 4):
            f.dot(seam[k][0] + 3.0, seam[k][1] + 4.0, 0.8, K.shade(WOOD_DARK, 0.75))
    # The wale: a heavy timber along the top strake, painted red.
    wale = [(x, _jong_sheer(x) + 7.0) for x in keel_xs]
    f.limb(wale, 4.4, SLIP_SHADE, body=False)
    f.ink([(x, y - 1.0) for x, y in wale], 1.2, SLIP)
    f.ink([(x, _jong_sheer(x) + 1.6) for x in xs[2:-2]], 1.2, WOOD_LIGHT)
    # The stem and the sternpost, a little proud of the planks.
    f.limb([(x1 - 2.0, _jong_sheer(x1 - 2.0) + 1.0), (x1 - 12.0, _jong_keel(x1 - 22.0) - 2.0)], 3.0, WOOD_LIGHT, body=False)
    f.limb([(x0 + 2.0, _jong_sheer(x0 + 2.0) + 1.0), (x0 + 12.0, _jong_keel(x0 + 20.0) - 2.0)], 3.0, WOOD_LIGHT, body=False)
    # The beam at the stern that holds the quarter rudders, and the near
    # rudder in front of the hull.
    f.limb([(x0 + 40.0, top - 12.0), (x0 + 78.0, top - 4.0)], 5.0, WOOD_DARK)
    _quarter_rudder(f, (x0 + 74.0, top - 16.0), (x0 + 46.0, top + 72.0), WOOD_LIGHT, WOOD_DARK)
    f.ellipse(x0 + 69.0, top - 5.0, 3.4, 3.0, ROPE)
    # The sails: a big one on the mainmast and a smaller one forward.
    aft, fore = _tanja_sail(f, main_x + 8.0, 66.0, 100.0, 80.0, 20.0, 8.0)
    f.ink([aft, (main_x - 70.0, top - 1.0)], 0.9, ROPE)
    aft, fore = _tanja_sail(f, fore_x + 10.0, 82.0, 70.0, 58.0, 20.0, 6.0)
    f.ink([aft, (fore_x - 40.0, top - 1.0)], 0.9, ROPE)
    # The halyards: a rope from each masthead to its upper boom.
    f.ink([(main_x, 18.0), (main_x + 2.0, 24.0)], 1.0, ROPE)
    f.ink([(fore_x, 38.0), (fore_x + 2.0, 50.0)], 1.0, ROPE)
    return A.finish(f, width=1.4)


# ---------------------------------------------------------------------------
# A relief of a ship, in the style of Borobudur.
# ---------------------------------------------------------------------------


def _carve_poly(f: K.Frame, pts: Sequence[Point], fill: RGBA = None) -> None:
    """A raised shape in the stone. The light comes from the top left, so
    the shape has a light edge on that side and a dark edge on the other."""
    f.poly([(x + 1.6, y + 1.6) for x, y in pts], STONE_DARK, body=False)
    f.poly([(x - 0.9, y - 0.9) for x, y in pts], STONE_LIGHT, body=False)
    f.poly(pts, fill or STONE, body=False)


def _carve_line(f: K.Frame, pts: Sequence[Point], width: float, fill: RGBA = None) -> None:
    """A raised rod in the stone (a mast, an arm, a rope), lit as `_carve_poly`."""
    f.limb([(x + 1.2, y + 1.2) for x, y in pts], width, STONE_DARK, body=False)
    f.limb([(x - 0.7, y - 0.7) for x, y in pts], width, STONE_LIGHT, body=False)
    f.limb(pts, width, fill or STONE, body=False)


def _groove(f: K.Frame, pts: Sequence[Point], width: float = 0.8) -> None:
    """A line cut into the stone: dark, with a light lip under it."""
    f.ink([(x + 0.5, y + 0.6) for x, y in pts], width, STONE_LIGHT)
    f.ink(pts, width, STONE_DARK)


def _sailor(f: K.Frame, x: float, y: float, reach: Point, step: float = 0.0) -> None:
    """A small carved sailor: a round head with no face, a body, legs and
    two arms to `reach` (a rope, an oar). `y` is the hip."""
    neck = (x + step * 0.3, y - 9.0)
    _carve_line(f, [(x - 2.4 + step, y + 8.0), (x, y), (x + 2.4, y + 8.0)], 1.8)
    _carve_line(f, [(x, y), neck], 3.0)
    _carve_line(f, [(neck[0], neck[1] + 1.0), reach], 1.5)
    _carve_line(f, [(neck[0], neck[1] + 2.0), (reach[0] - 1.5, reach[1] + 3.0)], 1.5)
    f.ellipse(neck[0] + 1.0, neck[1] - 2.0, 2.6, 2.6, STONE_DARK, body=False)
    f.ellipse(neck[0] - 0.4, neck[1] - 3.4, 2.6, 2.6, STONE_LIGHT, body=False)
    f.ellipse(neck[0], neck[1] - 3.0, 2.6, 2.6, STONE, body=False)


def _stone_grain(f: K.Frame, box: Tuple[float, float, float, float], count: int, seed: str) -> None:
    """Andesite is a volcanic stone with small holes; the rain leaves pale
    and dark marks on it."""
    rng = random.Random(seed)
    x0, y0, x1, y1 = box
    for _ in range(count):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        if rng.random() < 0.6:
            f.dot(x, y, rng.uniform(0.4, 0.8), K.alpha(STONE_DARK, 0.6))
        else:
            f.dot(x, y, rng.uniform(0.4, 0.8), K.alpha(STONE_LIGHT, 0.5))
    for _ in range(max(1, count // 40)):
        x, y = rng.uniform(x0 + 8.0, x1 - 8.0), rng.uniform(y0 + 4.0, y1 - 8.0)
        f.ellipse(x, y, rng.uniform(4.0, 9.0), rng.uniform(2.0, 4.0), K.alpha(LICHEN, 0.22), body=False)


def _draw_ship_relief(anim: str, i: int, n: int):
    f = K.Frame(RELIEF_FRAME)
    w, h = RELIEF_FRAME
    x0, y0, x1, y1 = 6.0, 6.0, w - 6.0, h - 6.0
    # The block and its moulded frame: an outer band, a step, and the
    # sunk field of the picture. Each step has a lit top and left and a
    # dark bottom and right.
    f.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], STONE)
    for d, light, dark in ((0.0, STONE_LIGHT, STONE_DARK), (7.0, STONE_DARK, STONE_LIGHT), (10.0, STONE_LIGHT, STONE_DARK)):
        a0, b0, a1, b1 = x0 + d, y0 + d, x1 - d, y1 - d
        f.ink([(a0 + 1.0, b1 - 1.0), (a0 + 1.0, b0 + 1.0), (a1 - 1.0, b0 + 1.0)], 1.4, light)
        f.ink([(a1 - 1.0, b0 + 1.0), (a1 - 1.0, b1 - 1.0), (a0 + 1.0, b1 - 1.0)], 1.4, dark)
    fx0, fy0, fx1, fy1 = x0 + 13.0, y0 + 13.0, x1 - 13.0, y1 - 13.0
    f.poly([(fx0, fy0), (fx1, fy0), (fx1, fy1), (fx0, fy1)], STONE_SUNK, body=False)
    f.ink([(fx0, fy1), (fx0, fy0), (fx1, fy0)], 2.0, STONE_DARK)
    # A row of small carved squares on the outer band, as on the moulding.
    for k in range(int((x1 - x0 - 20.0) / 12.0)):
        bx = x0 + 12.0 + k * 12.0
        f.poly([(bx, y0 + 2.4), (bx + 6.0, y0 + 2.4), (bx + 6.0, y0 + 5.4), (bx, y0 + 5.4)], STONE_LIGHT, body=False)
        f.poly([(bx, y1 - 5.4), (bx + 6.0, y1 - 5.4), (bx + 6.0, y1 - 2.4), (bx, y1 - 2.4)], STONE_DARK, body=False)
    # The sea: rows of waves that curl over, at the foot of the field.
    for row, (wy, step) in enumerate(((fy1 - 12.0, 16.0), (fy1 - 5.0, 16.0))):
        for k in range(int((fx1 - fx0) / step)):
            cx = fx0 + 6.0 + k * step + (step / 2.0 if row else 0.0)
            if cx > fx1 - 8.0:
                continue
            curl = [(cx - 7.0, wy + 3.0), (cx - 3.0, wy - 1.0), (cx + 2.0, wy - 2.6), (cx + 5.0, wy - 1.0), (cx + 4.0, wy + 1.4), (cx + 1.0, wy + 1.0)]
            _carve_line(f, curl, 1.6)
    # The outrigger: a long float under the near side, held by booms.
    sx0, sx1, top = 46.0, 210.0, 74.0
    for bx in (88.0, 160.0):
        _carve_line(f, [(bx, top + 2.0), (bx + 10.0, top + 22.0)], 2.0)
    _carve_poly(f, [(70.0, top + 17.0), (186.0, top + 17.0), (192.0, top + 20.0), (184.0, top + 23.0), (72.0, top + 23.0), (64.0, top + 20.0)])
    # The masts and their canted sails, with stays.
    _carve_line(f, [(100.0, top), (100.0, 22.0)], 2.4)
    _carve_line(f, [(160.0, top), (160.0, 32.0)], 2.2)
    for corners in (_box(104.0, 42.0, 44.0, 32.0, 20.0), _box(164.0, 48.0, 32.0, 26.0, 20.0)):
        tl, tr, br, bl = corners
        _carve_poly(f, corners)
        for u in (0.33, 0.66):
            _groove(f, [_mix(tl, bl, u), _mix(tr, br, u)], 0.7)
        for p, q in ((tl, tr), (bl, br)):
            _carve_line(f, [_mix(q, p, 1.12), _mix(p, q, 1.12)], 1.8)
    _groove(f, [(160.0, 33.0), (sx1 - 2.0, top - 16.0)], 0.6)
    _groove(f, [(100.0, 23.0), (sx0 + 4.0, top - 14.0)], 0.6)
    # The crew: one hauls on a sheet, two stand at the side, and one
    # holds the steering oar at the stern.
    _sailor(f, 128.0, top - 9.0, (138.0, top - 22.0), 1.0)
    _sailor(f, 84.0, top - 9.0, (78.0, top - 22.0), -1.0)
    _sailor(f, 190.0, top - 9.0, (198.0, top - 20.0), 0.0)
    _sailor(f, 60.0, top - 9.0, (52.0, top - 14.0), 0.0)
    _carve_line(f, [(56.0, top - 18.0), (42.0, top + 18.0)], 2.0)
    _carve_poly(f, [(38.0, top + 12.0), (46.0, top + 16.0), (42.0, top + 26.0), (35.0, top + 22.0)])
    # The hull, over the feet of the crew: high ends, and lines of planks.
    hull = [(sx0 - 2.0, top - 16.0), (sx0 + 12.0, top - 4.0), (sx0 + 30.0, top), (sx1 - 30.0, top), (sx1 - 10.0, top - 4.0), (sx1 + 4.0, top - 20.0),
            (sx1 - 4.0, top - 6.0), (sx1 - 22.0, top + 12.0), (sx0 + 26.0, top + 12.0), (sx0 + 6.0, top - 2.0)]
    _carve_poly(f, hull)
    _groove(f, [(sx0 + 20.0, top + 4.0), (sx1 - 18.0, top + 4.0)], 0.7)
    _groove(f, [(sx0 + 22.0, top + 8.0), (sx1 - 20.0, top + 8.0)], 0.7)
    # The stone: grain, holes and lichen over everything, and some wear.
    _stone_grain(f, (x0 + 2.0, y0 + 2.0, x1 - 2.0, y1 - 2.0), 260, "history_ship_relief stone")
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# A bell stupa with a lattice, as on the round terraces of Borobudur.
# ---------------------------------------------------------------------------


def _bell_half_width(y: float) -> float:
    """The half width of the bell at the height `y` (frame pixels). The bell
    is wide at its foot and round at its top."""
    pts = [(48.0, 12.0), (52.0, 20.0), (60.0, 28.0), (72.0, 36.0), (86.0, 41.0), (100.0, 44.0), (114.0, 45.5), (124.0, 46.0)]
    if y <= pts[0][0]:
        return pts[0][1]
    for (ya, wa), (yb, wb) in zip(pts, pts[1:]):
        if y <= yb:
            return wa + (wb - wa) * (y - ya) / (yb - ya)
    return pts[-1][1]


def _draw_bell_stupa(anim: str, i: int, n: int):
    f = K.Frame(BELL_STUPA_FRAME)
    w, h = BELL_STUPA_FRAME
    cx = w / 2.0
    ground = h - 6.0
    # The round base: a low plinth and a cushion of lotus petals.
    f.poly([(cx - 54.0, ground - 12.0), (cx + 54.0, ground - 12.0), (cx + 55.0, ground), (cx - 55.0, ground)], STONE)
    f.ellipse(cx, ground - 12.0, 54.0, 4.0, STONE)
    f.poly([(cx + 20.0, ground - 12.0), (cx + 54.0, ground - 12.0), (cx + 55.0, ground), (cx + 26.0, ground)], STONE_SHADE, body=False)
    f.ink([(cx - 53.0, ground - 10.0), (cx + 53.0, ground - 10.0)], 0.9, STONE_LIGHT)
    lotus_top = 122.0
    f.poly([(cx - 50.0, lotus_top + 2.0), (cx + 50.0, lotus_top + 2.0), (cx + 53.0, ground - 13.0), (cx - 53.0, ground - 13.0)], STONE)
    f.poly([(cx + 22.0, lotus_top + 2.0), (cx + 50.0, lotus_top + 2.0), (cx + 53.0, ground - 13.0), (cx + 26.0, ground - 13.0)], STONE_SHADE, body=False)
    # The petals stand up round the cushion. At the sides they turn away,
    # so they are narrower there.
    for j in range(-6, 7):
        phi = j * math.radians(13.0)
        if abs(phi) > math.radians(82.0):
            continue
        px = cx + 51.0 * math.sin(phi)
        hw = 4.6 * math.cos(phi) + 0.6
        base_y, tip_y = ground - 14.0, lotus_top + 4.0
        petal = [(px - hw, base_y), (px - hw, base_y - 6.0), (px, tip_y), (px + hw, base_y - 6.0), (px + hw, base_y)]
        f.poly(petal, STONE_SHADE if phi > 0.5 else STONE_LIGHT if phi < -0.6 else K.shade(STONE, 1.06), body=False)
        f.ink([(px + hw, base_y), (px + hw, base_y - 6.0), (px, tip_y)], 0.7, STONE_DARK)
    # The bell: a curve on each side, round over the top.
    ys = [lotus_top + 2.0 - k * (lotus_top + 2.0 - 48.0) / 30.0 for k in range(31)]
    left = [(cx - _bell_half_width(y), y) for y in ys]
    right = [(cx + _bell_half_width(y), y) for y in ys]
    cap = [(cx + 12.0 * math.cos(a), 48.0 - 3.0 * math.sin(a)) for a in [math.pi * k / 8.0 for k in range(9)]]
    bell = left + cap[::-1][1:-1] + right[::-1]
    f.poly(bell, STONE)
    f.poly([(cx + _bell_half_width(y) * 0.45, y) for y in ys] + [(cx + _bell_half_width(y) - 0.5, y) for y in ys[::-1]], STONE_SHADE, body=False)
    f.poly([(cx - _bell_half_width(y) + 2.0, y) for y in ys[2:-4]] + [(cx - _bell_half_width(y) * 0.72, y) for y in ys[-5:1:-1]], STONE_LIGHT, body=False)
    # A rim at the foot of the bell.
    f.poly([(cx - 47.0, lotus_top - 4.0), (cx + 47.0, lotus_top - 4.0), (cx + 47.0, lotus_top + 2.0), (cx - 47.0, lotus_top + 2.0)], STONE)
    f.poly([(cx + 20.0, lotus_top - 4.0), (cx + 47.0, lotus_top - 4.0), (cx + 47.0, lotus_top + 2.0), (cx + 20.0, lotus_top + 2.0)], STONE_SHADE, body=False)
    f.ink([(cx - 46.0, lotus_top - 3.0), (cx + 46.0, lotus_top - 3.0)], 0.8, STONE_LIGHT)
    # The lattice: rows of diamond holes in the wall of the bell. The
    # space inside is dark; nothing in it shows.
    for row, (y, hh, step) in enumerate(((106.0, 7.0, 0.30), (88.0, 6.4, 0.32), (71.0, 5.6, 0.36), (57.0, 4.0, 0.46))):
        half = _bell_half_width(y)
        off = 0.5 * step if row % 2 else 0.0
        for j in range(-8, 9):
            phi = j * step + off
            if abs(phi) > 1.20:
                continue
            px = cx + half * math.sin(phi)
            hw = (half * step * 0.30) * math.cos(phi)
            if hw < 1.0:
                continue
            hole = [(px, y - hh), (px + hw, y), (px, y + hh), (px - hw, y)]
            f.poly(hole, HOLLOW, body=False)
            # The lit lower edges of the hole show the thick wall.
            f.ink([(px - hw, y), (px, y + hh), (px + hw, y)], 0.7, STONE_LIGHT if phi < 0.4 else STONE)
    # The harmika: a square block on the top of the bell, and a short
    # spire with eight faces on it.
    f.poly([(cx - 11.0, 46.0), (cx + 11.0, 46.0), (cx + 11.0, 32.0), (cx - 11.0, 32.0)], STONE)
    f.poly([(cx - 13.0, 34.0), (cx + 13.0, 34.0), (cx + 13.0, 30.0), (cx - 13.0, 30.0)], STONE)
    f.poly([(cx + 4.0, 46.0), (cx + 11.0, 46.0), (cx + 11.0, 34.0), (cx + 4.0, 34.0)], STONE_SHADE, body=False)
    f.ink([(cx - 12.0, 31.0), (cx + 12.0, 31.0)], 0.8, STONE_LIGHT)
    f.poly([(cx - 6.0, 30.0), (cx + 6.0, 30.0), (cx + 3.4, 10.0), (cx - 3.4, 10.0)], STONE)
    f.poly([(cx + 1.6, 30.0), (cx + 6.0, 30.0), (cx + 3.4, 10.0), (cx + 1.0, 10.0)], STONE_SHADE, body=False)
    f.ink([(cx - 2.2, 29.0), (cx - 1.4, 11.0)], 0.8, STONE_LIGHT)
    for y in (24.0, 18.0):
        f.ink([(cx - 5.4 + (30.0 - y) * 0.12, y), (cx + 5.4 - (30.0 - y) * 0.12, y)], 0.7, STONE_DARK)
    _stone_grain(f, (cx - 36.0, 60.0, cx + 36.0, lotus_top - 6.0), 70, "history_bell_stupa bell")
    _stone_grain(f, (cx - 48.0, lotus_top + 4.0, cx + 48.0, ground - 3.0), 50, "history_bell_stupa base")
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# Blocks of sandstone and laterite, as the builders of Angkor left them.
# ---------------------------------------------------------------------------


def _block(f: K.Frame, x0: float, y0: float, x1: float, y1: float, depth: Point, face: RGBA, light: RGBA, shade: RGBA, dark: RGBA) -> None:
    """A dressed block seen a little from above and from the left: its front
    face, its top face and its right side. `depth` is how far the back
    edge is from the front edge."""
    dx, dy = depth
    f.poly([(x0, y0), (x1, y0), (x1 + dx, y0 + dy), (x1 + dx, y1 + dy), (x1, y1), (x0, y1)], face)
    f.poly([(x0, y0), (x0 + dx, y0 + dy), (x1 + dx, y0 + dy), (x1, y0)], light, body=False)
    f.poly([(x1, y0), (x1 + dx, y0 + dy), (x1 + dx, y1 + dy), (x1, y1)], shade, body=False)
    f.ink([(x0, y0), (x1, y0), (x1, y1)], 0.8, dark)


def _peg_holes(f: K.Frame, a: Point, b: Point, squash: float = 1.0) -> None:
    """Two small round holes at `a` and `b`. The builders put pegs in them
    to lift the block and set it in its place. `squash` makes the holes
    flat, for a hole in a top face seen at a slant."""
    for px, py in (a, b):
        f.ellipse(px, py, 1.5, 1.6 * squash, SAND_DARK, body=False)
        f.ellipse(px + 0.3, py + 0.5 * squash, 0.8, 0.8 * squash, K.shade(SAND_DARK, 0.6), body=False)


def _draw_sandstone_blocks(anim: str, i: int, n: int):
    f = K.Frame(BLOCKS_FRAME)
    w, h = BLOCKS_FRAME
    ground = h - 12.0
    rng = random.Random("history_sandstone_blocks")
    # The red laterite block, at the back left. Laterite is soft when it is
    # cut and goes hard in the air; its face is full of pits.
    _block(f, 10.0, 32.0, 44.0, ground - 4.0, (7.0, -6.0), LATERITE, LATERITE_LIGHT, LATERITE_SHADE, LATERITE_DARK)
    for _ in range(34):
        px, py = rng.uniform(12.0, 42.0), rng.uniform(34.0, ground - 6.0)
        f.ellipse(px, py, rng.uniform(0.7, 1.6), rng.uniform(0.6, 1.2), LATERITE_DARK, body=False)
    for _ in range(10):
        f.dot(rng.uniform(12.0, 42.0), rng.uniform(34.0, ground - 6.0), 0.7, LATERITE_LIGHT)
    # The sandstone: a long block at the front, one beside it, and one on
    # top. Each is cut square and smooth.
    blocks = ((34.0, 44.0, 96.0, ground), (104.0, 48.0, 142.0, ground), (46.0, 22.0, 92.0, 44.0))
    for k, (x0, y0, x1, y1) in enumerate(blocks):
        _block(f, x0, y0, x1, y1, (8.0, -6.0), K.shade(SAND, 1.0 + 0.03 * k), SAND_LIGHT, SAND_SHADE, SAND_DARK)
    for x0, y0, x1, y1 in blocks:
        # The bedding of the stone shows as faint lines, and the grain of
        # the sand as small specks.
        for k in range(2):
            yy = y0 + (y1 - y0) * (0.4 + 0.3 * k) + rng.uniform(-1.0, 1.0)
            f.ink([(x0 + 3.0, yy), ((x0 + x1) / 2.0, yy + rng.uniform(-0.8, 0.8)), (x1 - 3.0, yy + rng.uniform(-0.8, 0.8))], 0.6, K.alpha(SAND_SHADE, 0.7))
        for _ in range(int((x1 - x0) * (y1 - y0) / 40.0)):
            f.dot(rng.uniform(x0 + 2.0, x1 - 2.0), rng.uniform(y0 + 2.0, y1 - 2.0), 0.5, K.alpha(SAND_DARK if rng.random() < 0.5 else SAND_LIGHT, 0.5))
    # The peg holes, near the top edge of two blocks.
    # The peg holes: a pair on the front of two blocks, near one end, and
    # a pair in the top of the upper block.
    _peg_holes(f, (88.0, 52.0), (88.0, 59.0))
    _peg_holes(f, (136.0, 58.0), (136.0, 65.0))
    _peg_holes(f, (66.0, 19.0), (74.0, 19.0), 0.55)
    # A few chips at the corners.
    f.poly([(96.0, 60.0), (96.0, 66.0), (93.0, 64.0)], SAND_SHADE, body=False)
    f.poly([(46.0, 22.0), (50.0, 22.0), (46.0, 26.0)], SAND_SHADE, body=False)
    # The lever: a long pole of hard wood that lies on the ground in front.
    # The workers put it under a block to move it a little at a time.
    f.limb([(30.0, ground + 6.0), (148.0, ground + 2.5)], 4.6, WOOD)
    f.ink([(32.0, ground + 4.7), (146.0, ground + 1.3)], 1.0, WOOD_LIGHT)
    f.ellipse(148.0, ground + 2.5, 1.4, 2.0, WOOD_DARK, body=False)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# A Khmer ox cart.
# ---------------------------------------------------------------------------


def _wheel(f: K.Frame, cx: float, cy: float, r: float, rim: RGBA, spoke: RGBA, light: RGBA, n_spokes: int = 12) -> None:
    """A spoked wheel: a thick rim, a hub and straight spokes. The ground
    shows between the spokes."""
    for k in range(n_spokes):
        a = math.tau * k / n_spokes + 0.1
        f.limb([(cx + math.cos(a) * 3.0, cy + math.sin(a) * 3.0), (cx + math.cos(a) * (r - 3.0), cy + math.sin(a) * (r - 3.0))], 1.8, spoke)
    ring = K.ellipse_points(cx, cy, r - 2.2, r - 2.2, 48)
    f.limb(ring + ring[:2], 4.4, rim)
    f.ink(K.ellipse_points(cx, cy, r - 1.2, r - 1.2, 48)[26:40], 1.0, light)
    f.ellipse(cx, cy, 5.0, 5.0, rim)
    f.ellipse(cx, cy, 2.2, 2.2, K.shade(spoke, 0.7), body=False)


def _draw_ox_cart(anim: str, i: int, n: int):
    f = K.Frame(OX_CART_FRAME)
    w, h = OX_CART_FRAME
    ground = h - 7.0
    # The far wheel shows a little behind the near wheel.
    wx, wy, wr = 56.0, ground - 25.0, 25.0
    _wheel(f, wx + 7.0, wy - 2.0, wr, WOOD_DARK, K.shade(WOOD_DARK, 0.8), WOOD)
    # The far shaft, behind the ox.
    f.limb([(98.0, wy - 10.0), (165.0, 74.0)], 3.0, WOOD_DARK)
    # The ox: a zebu with a hump on its shoulders, a loose dewlap under the
    # neck, short horns and ears that hang down. It walks to the right. Its
    # body is deep and its legs are short and thick, so it reads as an ox.
    for x0, x1 in ((118.0, 116.0), (152.0, 151.0)):
        f.limb([(x0, 100.0), (x1, ground - 6.0), (x1 + 0.5, ground - 1.0)], 5.0, ZEBU_SHADE)
        f.ellipse(x1 + 1.0, ground - 1.0, 3.0, 1.6, HOOF)
    body = [(104.0, 80.0), (110.0, 74.0), (128.0, 73.0), (142.0, 72.0), (146.0, 66.0), (150.0, 60.0), (158.0, 59.0), (163.0, 64.0),
            (165.0, 70.0), (169.0, 74.0), (171.0, 82.0), (169.0, 92.0), (163.0, 100.0), (155.0, 106.0), (130.0, 107.0), (114.0, 105.0),
            (105.0, 96.0)]
    f.poly(body, ZEBU)
    # The dewlap hangs from the throat to the chest.
    f.poly([(165.0, 90.0), (169.0, 94.0), (164.0, 107.0), (157.0, 111.0), (152.0, 105.0), (158.0, 99.0)], ZEBU)
    f.ink([(166.0, 95.0), (159.0, 107.0)], 0.8, ZEBU_SHADE)
    # The far horn, behind the head.
    f.limb([(174.0, 73.0), (177.0, 66.0), (176.0, 62.0)], 2.4, K.shade(HORN, 0.8))
    # The head: broad and short, carried low, with a square dark muzzle.
    head = [(165.0, 72.0), (175.0, 71.0), (180.0, 77.0), (185.0, 89.0), (185.0, 97.0), (180.0, 100.0), (174.0, 99.0), (169.0, 90.0),
            (164.0, 81.0)]
    f.poly(head, ZEBU)
    f.poly([(179.0, 90.0), (185.0, 90.0), (185.0, 97.0), (180.0, 100.0), (176.0, 97.0)], ZEBU_DARK, body=False)
    f.dot(182.5, 93.5, 0.8, K.shade(ZEBU_DARK, 0.5))
    f.ink([(172.0, 74.0), (178.0, 80.0), (181.0, 88.0)], 0.7, ZEBU_LIGHT)
    f.dot(174.5, 80.0, 1.2, A.OUTLINE)
    # The near horn curves up and out; the ear hangs down beside the head.
    f.limb([(170.0, 73.0), (171.0, 66.0), (168.0, 61.0)], 2.8, HORN)
    f.dot(168.2, 61.4, 1.0, HORN_TIP)
    f.poly([(167.0, 76.0), (160.0, 80.0), (157.0, 87.0), (160.0, 88.0), (168.0, 82.0)], ZEBU_SHADE)
    # The hump is darker, as on many zebu; the back is in light and the
    # belly in shade.
    f.poly([(146.0, 66.0), (150.0, 60.0), (158.0, 59.0), (163.0, 64.0), (160.0, 70.0), (151.0, 72.0)], K.alpha(ZEBU_SHADE, 0.55), body=False)
    f.poly([(108.0, 100.0), (130.0, 103.0), (155.0, 102.0), (163.0, 99.0), (155.0, 106.0), (130.0, 107.0), (114.0, 105.0)], ZEBU_SHADE, body=False)
    f.ink([(110.0, 76.0), (126.0, 75.5), (141.0, 74.5)], 1.2, ZEBU_LIGHT)
    f.ink([(147.0, 74.0), (150.0, 88.0), (154.0, 100.0)], 0.8, ZEBU_SHADE)
    f.ink([(120.0, 78.0), (115.0, 96.0)], 0.8, ZEBU_SHADE)
    # The tail, with a dark tuft.
    f.limb([(105.0, 80.0), (101.0, 92.0), (101.0, 106.0)], 1.4, ZEBU_SHADE)
    f.ellipse(101.0, 108.0, 1.8, 3.0, ZEBU_DARK)
    # The near legs, short and thick.
    for x0, x1 in ((123.0, 122.0), (158.0, 160.0)):
        f.limb([(x0, 102.0), (x1, ground - 6.0), (x1 + 0.5, ground - 1.0)], 5.6, ZEBU)
        f.ellipse(x1 + 1.0, ground - 1.0, 3.2, 1.7, HOOF)
    # The cart: a bed of planks on the axle, low side boards, and a roof
    # of matting bent over hoops, that keeps off the sun and the rain.
    bx0, bx1, bed = 14.0, 100.0, wy - 8.0
    f.poly([(bx0, bed - 18.0), (bx1, bed - 18.0), (bx1, bed + 4.0), (bx0, bed + 4.0)], WOOD)
    f.poly([(bx0, bed - 2.0), (bx1, bed - 2.0), (bx1, bed + 4.0), (bx0, bed + 4.0)], WOOD_DARK, body=False)
    for k in range(1, 6):
        x = bx0 + (bx1 - bx0) * k / 6.0
        f.ink([(x, bed - 17.0), (x, bed - 2.0)], 0.9, WOOD_DARK)
    f.ink([(bx0 + 1.0, bed - 16.0), (bx1 - 1.0, bed - 16.0)], 1.0, WOOD_LIGHT)
    roof_base = bed - 18.0
    arch = [(bx0 - 6.0 + (bx1 - bx0 + 12.0) * u, roof_base - 34.0 * math.sin(math.pi * u) ** 0.55) for u in [k / 16.0 for k in range(17)]]
    f.poly(arch + [(bx1 + 6.0, roof_base + 2.0), (bx0 - 6.0, roof_base + 2.0)], MATTING)
    inner = [(bx0 - 2.0 + (bx1 - bx0 + 4.0) * u, roof_base - 26.0 * math.sin(math.pi * u) ** 0.55) for u in [k / 16.0 for k in range(17)]]
    f.poly(inner[8:] + [(bx1 + 6.0, roof_base + 2.0)] + arch[::-1][:9], MATTING_SHADE, body=False)
    for k in range(1, 8):
        u = k / 8.0
        x = bx0 - 6.0 + (bx1 - bx0 + 12.0) * u
        top_y = roof_base - 34.0 * math.sin(math.pi * u) ** 0.55
        f.ink([(x, top_y + 1.0), (x, roof_base)], 0.9, MATTING_DARK)
    for k in range(1, 4):
        pts = [(bx0 - 6.0 + (bx1 - bx0 + 12.0) * u, roof_base - (34.0 - k * 8.0) * math.sin(math.pi * u) ** 0.55) for u in [q / 16.0 for q in range(1, 16)]]
        f.ink(pts, 0.6, K.alpha(MATTING_DARK, 0.6))
    f.ink(arch[2:-2], 1.0, MATTING_LIGHT)
    f.limb([(bx0 - 6.0, roof_base + 1.0), (bx1 + 6.0, roof_base + 1.0)], 2.4, BAMBOO_SHADE)
    # The near shaft, from the bed to the yoke on the neck of the ox, in
    # front of the hump.
    f.limb([(bx1 - 4.0, bed), (165.0, 76.0)], 3.4, WOOD_LIGHT)
    f.limb([(162.0, 65.0), (166.0, 80.0)], 3.4, WOOD_DARK)
    f.ink([(161.0, 70.0), (168.0, 69.0)], 1.2, ROPE)
    # The near wheel, in front.
    _wheel(f, wx, wy, wr, WOOD, WOOD_DARK, WOOD_LIGHT)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# Goods of the sea trade.
# ---------------------------------------------------------------------------


def _jar(f: K.Frame, cx: float, foot: float, r: float, height: float) -> None:
    """A Chinese storage jar of stoneware: a wide shoulder, a short neck, and
    four small lugs at the shoulder for the cord that ties the lid. The
    glaze is green-brown and stops above the foot, where the grey-buff
    body shows."""
    top = foot - height
    shoulder = top + height * 0.28
    side = [(cx - r * 0.62, foot), (cx - r * 0.80, foot - height * 0.30), (cx - r, shoulder + height * 0.12), (cx - r * 0.86, shoulder - 2.0),
            (cx - r * 0.42, top + 4.0)]
    f.poly(side + [(2 * cx - x, y) for x, y in side[::-1]], STONEWARE)
    glaze_end = foot - height * 0.20
    f.poly([(cx - r * 0.76, glaze_end)] + side[2:] + [(2 * cx - x, y) for x, y in side[2:][::-1]] + [(cx + r * 0.76, glaze_end)], GLAZE, body=False)
    # The drips at the lower edge of the glaze.
    for dx in (-0.5, -0.1, 0.35):
        x = cx + dx * r
        f.poly([(x - 1.6, glaze_end), (x + 1.6, glaze_end), (x + 0.6, glaze_end + 4.0), (x - 0.6, glaze_end + 4.0)], GLAZE, body=False)
    # One shade and one shine.
    f.poly([(cx + r * 0.35, shoulder - 1.0), (cx + r * 0.86, shoulder - 2.0), (cx + r, shoulder + height * 0.12), (cx + r * 0.80, foot - height * 0.30),
            (cx + r * 0.62, foot), (cx + r * 0.42, foot), (cx + r * 0.62, shoulder + height * 0.2)], K.alpha(GLAZE_SHADE, 0.85), body=False)
    f.ellipse(cx - r * 0.5, shoulder + 4.0, r * 0.16, height * 0.09, GLAZE_LIGHT, body=False)
    # The neck and the mouth.
    f.poly([(cx - r * 0.40, top + 5.0), (cx + r * 0.40, top + 5.0), (cx + r * 0.38, top), (cx - r * 0.38, top)], GLAZE)
    f.ellipse(cx, top, r * 0.44, 2.2, GLAZE)
    f.ellipse(cx, top, r * 0.30, 1.2, HOLLOW, body=False)
    # The lugs: small loops at the shoulder. One sticks out at each side;
    # a third is on the front, and the fourth is at the back.
    for sx in (-1.0, 1.0):
        lx, ly = cx + sx * r * 0.88, shoulder - 1.0
        f.poly([(lx - sx * 2.0, ly - 2.0), (lx + sx * 3.2, ly - 2.4), (lx + sx * 3.6, ly + 1.4), (lx - sx * 2.0, ly + 2.0)], GLAZE)
        f.dot(lx + sx * 1.4, ly - 0.4, 0.8, HOLLOW)
    f.poly([(cx - 3.0, shoulder - 5.0), (cx + 3.0, shoulder - 5.0), (cx + 2.4, shoulder - 1.0), (cx - 2.4, shoulder - 1.0)], GLAZE_SHADE, body=False)
    f.ellipse(cx, shoulder - 3.0, 1.2, 1.0, HOLLOW, body=False)


def _sack(f: K.Frame, cx: float, foot: float, r: float, height: float, open_top: bool) -> None:
    """A sack of woven fibre, fat at the foot. A closed sack is tied at the
    top; an open one has its mouth rolled down, and the black pepper shows."""
    top = foot - height
    if open_top:
        shape = [(cx - r * 0.86, foot), (cx - r, foot - height * 0.45), (cx - r * 0.92, top + 4.0), (cx + r * 0.92, top + 4.0), (cx + r, foot - height * 0.45),
                 (cx + r * 0.86, foot)]
    else:
        shape = [(cx - r * 0.86, foot), (cx - r, foot - height * 0.40), (cx - r * 0.70, top + height * 0.28), (cx - 3.0, top + 8.0), (cx + 3.0, top + 8.0),
                 (cx + r * 0.70, top + height * 0.28), (cx + r, foot - height * 0.40), (cx + r * 0.86, foot)]
    f.poly(shape, SACKING)
    f.poly([(cx + r * 0.2, top + 10.0), (cx + r * 0.7, top + height * 0.3), (cx + r, foot - height * 0.4), (cx + r * 0.86, foot), (cx + r * 0.3, foot)],
           SACKING_SHADE, body=False)
    rng = random.Random(f"sack {cx}")
    for k in range(1, int(height / 5.0)):
        y = foot - k * 5.0
        f.ink([(cx - r * 0.8, y + rng.uniform(-0.5, 0.5)), (cx + r * 0.8, y + rng.uniform(-0.5, 0.5))], 0.5, K.alpha(SACKING_SHADE, 0.6))
    if open_top:
        # The heap of pepper, then the rolled lip in front of it.
        f.ellipse(cx, top + 4.0, r * 0.88, 5.0, PEPPER)
        f.poly([(cx - r * 0.8, top + 4.0), (cx - r * 0.4, top - 1.0), (cx, top - 3.0), (cx + r * 0.4, top - 1.0), (cx + r * 0.8, top + 4.0)], PEPPER)
        for _ in range(40):
            a = rng.uniform(0.0, math.tau)
            d = rng.uniform(0.0, 1.0)
            px, py = cx + math.cos(a) * r * 0.75 * d, top + 2.0 + math.sin(a) * 3.0 * d - (1.0 - d) * 3.0
            f.dot(px, py, 0.9, PEPPER_DARK)
            f.dot(px - 0.3, py - 0.3, 0.35, PEPPER_LIGHT)
        f.limb([(cx - r * 0.96, top + 6.0), (cx, top + 9.0), (cx + r * 0.96, top + 6.0)], 4.6, SACKING)
        f.ink([(cx - r * 0.9, top + 5.0), (cx, top + 7.6), (cx + r * 0.9, top + 5.0)], 1.0, SACKING_LIGHT)
    else:
        # The neck, tied with a cord, and the tuft above it.
        f.poly([(cx - 3.4, top + 9.0), (cx + 3.4, top + 9.0), (cx + 5.0, top + 2.0), (cx + 1.0, top), (cx - 5.0, top + 2.0)], SACKING)
        f.limb([(cx - 4.0, top + 7.0), (cx + 4.0, top + 7.0)], 1.8, ROPE)
        f.ink([(cx - r * 0.5, top + height * 0.36), (cx - r * 0.2, top + 12.0)], 0.9, SACKING_LIGHT)


def _draw_trade_goods(anim: str, i: int, n: int):
    f = K.Frame(GOODS_FRAME)
    w, h = GOODS_FRAME
    ground = h - 6.0
    # Two jars at the back left, the taller one behind.
    _jar(f, 24.0, ground - 2.0, 15.0, 54.0)
    _jar(f, 48.0, ground, 13.0, 44.0)
    # The bundle of camphor wood at the back right: split sticks tied with
    # rattan. Camphor came from the forests of Sumatra and Borneo; its
    # crystals are a medicine and a scent.
    bx0, bx1, by = 104.0, 152.0, ground - 20.0
    logs = [(0.0, 6.0), (7.0, 6.2), (14.0, 6.0), (3.5, -0.2), (10.5, 0.0), (7.0, -6.4)]
    for k, (dx, dy) in enumerate(logs):
        y = by + dy
        x = bx0 + dx * 0.3
        f.limb([(x, y), (bx1 - 3.0 - (k * 37 % 5), y - 1.0)], 6.4, CAMPHOR if k % 2 else K.shade(CAMPHOR, 0.94))
        f.ink([(x + 2.0, y - 1.6), (bx1 - 8.0, y - 2.6)], 0.7, CAMPHOR_LIGHT)
        f.ink([(x + 6.0, y + 1.6), (bx1 - 12.0, y + 0.8)], 0.6, CAMPHOR_SHADE)
    # The cut ends of the sticks show at the right, with their rings.
    ends = [(bx1 - 3.0 - (k * 37 % 5), by + dy - 1.0) for k, (dx, dy) in enumerate(logs)]
    for ex, ey in ends:
        f.ellipse(ex, ey, 2.6, 3.2, CAMPHOR_LIGHT)
        f.ellipse(ex, ey, 1.2, 1.6, CAMPHOR_SHADE, body=False)
    for tx in (bx0 + 12.0, bx1 - 12.0):
        f.limb([(tx, by - 10.0), (tx + 1.0, by + 9.0)], 2.2, RATTAN)
    # The pepper: two closed sacks, and an open one in front.
    _sack(f, 80.0, ground - 2.0, 15.0, 40.0, False)
    _sack(f, 106.0, ground, 13.0, 30.0, False)
    _sack(f, 72.0, ground, 15.0, 26.0, True)
    # A bolt of cloth that lies in front: a roll of cotton dyed with indigo,
    # with red bands. Cloth from India was a main good of the trade.
    cx0, cx1, cy, cr = 96.0, 148.0, ground - 6.0, 6.0
    f.poly([(cx0, cy - cr), (cx1, cy - cr), (cx1, cy + cr), (cx0, cy + cr)], CLOTH)
    f.poly([(cx0, cy + 2.0), (cx1, cy + 2.0), (cx1, cy + cr), (cx0, cy + cr)], CLOTH_SHADE, body=False)
    for bx in (cx0 + 12.0, cx0 + 16.0, cx1 - 18.0, cx1 - 14.0):
        f.limb([(bx, cy - cr + 0.6), (bx, cy + cr - 0.6)], 1.6, CLOTH_BAND, body=False)
    f.ink([(cx0 + 2.0, cy - cr + 1.6), (cx1 - 2.0, cy - cr + 1.6)], 1.0, CLOTH_LIGHT)
    f.ellipse(cx1, cy, 3.0, cr, CLOTH)
    spiral = [(cx1 + 0.4 * math.cos(a) * (a / 12.0) * 3.0, cy + math.sin(a) * (a / 12.0) * cr) for a in [k * 0.4 for k in range(31)]]
    f.ink(spiral, 0.6, CLOTH_SHADE)
    return A.finish(f, width=1.2)


# ---------------------------------------------------------------------------
# Publication.
# ---------------------------------------------------------------------------

SCENERY = ["prop", "scenery", "history", "southeast_asia"]
PLATFORM = ["prop", "platform", "history", "southeast_asia"]

FRAMES: Dict[str, Tuple[int, int]] = {
    "history_pig_painting": PIG_PAINTING_FRAME,
    "history_sulawesi_hand_stencils": STENCILS_FRAME,
    "history_bamboo_stilt_house": STILT_HOUSE_FRAME,
    "history_bronze_drum": DRUM_FRAME,
    "history_rice_sheaves": SHEAVES_FRAME,
    "history_red_slip_pots": POTS_FRAME,
    "history_jong": JONG_FRAME,
    "history_ship_relief": RELIEF_FRAME,
    "history_bell_stupa": BELL_STUPA_FRAME,
    "history_sandstone_blocks": BLOCKS_FRAME,
    "history_ox_cart": OX_CART_FRAME,
    "history_trade_goods": GOODS_FRAME,
}
DRAW: Dict[str, Callable] = {
    "history_pig_painting": _draw_pig_painting,
    "history_sulawesi_hand_stencils": _draw_hand_stencils,
    "history_bamboo_stilt_house": _draw_stilt_house,
    "history_bronze_drum": _draw_bronze_drum,
    "history_rice_sheaves": _draw_rice_sheaves,
    "history_red_slip_pots": _draw_red_slip_pots,
    "history_jong": _draw_jong,
    "history_ship_relief": _draw_ship_relief,
    "history_bell_stupa": _draw_bell_stupa,
    "history_sandstone_blocks": _draw_sandstone_blocks,
    "history_ox_cart": _draw_ox_cart,
    "history_trade_goods": _draw_trade_goods,
}
DISPLAY = {
    "history_pig_painting": "Pig Painting",
    "history_sulawesi_hand_stencils": "Sulawesi Hand Stencils",
    "history_bamboo_stilt_house": "Bamboo Stilt House",
    "history_bronze_drum": "Bronze Drum",
    "history_rice_sheaves": "Rice Sheaves",
    "history_red_slip_pots": "Red-Slip Pots",
    "history_jong": "Jong",
    "history_ship_relief": "Ship Relief",
    "history_bell_stupa": "Bell Stupa",
    "history_sandstone_blocks": "Sandstone Blocks",
    "history_ox_cart": "Ox Cart",
    "history_trade_goods": "Trade Goods",
}
ROWS: Dict[str, List[Tuple[str, int, int]]] = {}


def _foot(name: str) -> Dict[str, Tuple[float, float]]:
    w, h = FRAMES[name]
    return {"foot": (w / 2.0, float(h))}


#: The anchors of each prop. A platform has a "top" anchor at the middle of
#: the surface that a player stands on; the other props have a "foot".
ANCHORS: Dict[str, Dict[str, Tuple[float, float]]] = {name: _foot(name) for name in DISPLAY}
ANCHORS["history_jong"] = {"top": ((JONG_SPAN[0] + JONG_SPAN[1]) / 2.0, JONG_TOP)}
TAGS: Dict[str, List[str]] = {name: SCENERY for name in DISPLAY}
TAGS["history_jong"] = PLATFORM

TARGETS: Dict[str, dict] = {
    name: _publisher(name, DISPLAY[name], ROWS.get(name, STILL), FRAMES[name], DRAW[name], ANCHORS[name], "Scenery", TAGS[name]) for name in DISPLAY
}
