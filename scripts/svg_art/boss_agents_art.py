#!/usr/bin/env python3
"""Draw the bossofthegame's three named agents on the Director's rig.

    uv run python scripts/svg_art/boss_agents_art.py

The final boss (the game's ``docs/planning/game/final-boss.md``) has three
agents beside Full Stack: Geppetto (the GPT parody), Clause (the Claude
parody) and Wren (the Qwen parody). Each one is drawn from Jon's concept
sheets (``assets/concept_art/misc/agent-concepts/`` in the game repo):

- Geppetto, the Emissary form (the sheets "Geppetto - Emissary form", "Pose &
  Animation Sheet" and "Alternate Forms"): a cream mask with a seam down it
  and cyan eyes, white hair swept back, a black top hat with a magenta band
  wound like a spool, a cyan thread halo with beads, a plum tailcoat trimmed
  in magenta over a lilac waistcoat, wooden puppet hands, and a cane with a
  spool for its knob.
- Clause, the Analyst (the sheets "Clause - The Analyst" and "Modular Boss
  Agent"): a dark mask with two upright orange eyes, a crown of orange petal
  fins, a cream poncho with the orange starburst on it over a dark chassis,
  orange plates at the joints. He carries a staff with the starburst on it.
- Wren, the Multilingual Tactician: a dark face with two upright gold eyes, a
  conical hat with a gold band, gold tassels and a purple feather, a purple
  scarf, a cream robe with gold trim, a cape of purple feathers, banded
  trousers. She carries a folding fan.

Each one is the Director's SVG (``data/characters/director/director.svg``)
with the drawing of every rig part replaced and the rig kept, so the
Director's motion library (``director_pen_v1``) moves them, and the prop in
the hand is the part the Director's pen is (``pen``). This script writes
``data/characters/<agent>/<agent>.svg`` and its ``.motion.json``; rerun it
after the Director's rig changes.

The drawing is in the Director's art units (inside his ``scale(4.4585)``
view group), round his joints (``J``). He faces west: the face is toward
smaller x, and the near limbs are drawn over the body, the far ones under it
and darker.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "ambition_sprite2d_renderer" / "data" / "characters"
SOURCE = ROOT / "director" / "director.svg"
MOTION = ROOT / "director" / "director.motion.json"

INK = "#16121c"
SW = 0.55

#: The Director's joints in art units (his rig markers over 4.4585).
J = dict(
    neck=(94.81, 114.39),
    ns=(106.29, 126.91), fs=(83.34, 126.78),
    ne=(113.20, 146.80), fe=(78.66, 147.00),
    nw=(108.06, 161.92), fw=(73.43, 161.37),
    nh=(101.73, 174.02), fh=(71.31, 173.86),
    waist=(90.57, 161.11), hip=(92.21, 165.59),
    nhip=(98.66, 167.71), fhip=(85.77, 167.70),
    nk=(96.61, 194.20), fk=(83.72, 189.45),
    na=(105.11, 217.52), fa=(89.21, 215.29),
    nt=(89.15, 225.39), ft=(75.28, 223.55),
)
#: The pen's line, cap end to nib: the prop in the hand lies along it.
PEN = ((111.0, 162.5), (82.0, 212.0))


# ---------------------------------------------------------------------------
# A small pen
# ---------------------------------------------------------------------------


def _f(v: float) -> str:
    return f"{v:.2f}"


def poly(pts, fill, stroke=INK, sw=SW, opacity=None) -> str:
    d = "M " + " L ".join(f"{_f(x)},{_f(y)}" for x, y in pts) + " Z"
    op = f' opacity="{opacity}"' if opacity is not None else ""
    st = f' stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"' if stroke else ""
    return f'<path d="{d}" fill="{fill}"{st}{op}/>'


def line(pts, color, width) -> str:
    d = "M " + " L ".join(f"{_f(x)},{_f(y)}" for x, y in pts)
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>'


def ellipse(cx, cy, rx, ry, fill, stroke=INK, sw=SW, rot=0.0, opacity=None) -> str:
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    tr = f' transform="rotate({_f(rot)} {_f(cx)} {_f(cy)})"' if rot else ""
    op = f' opacity="{opacity}"' if opacity is not None else ""
    return f'<ellipse cx="{_f(cx)}" cy="{_f(cy)}" rx="{_f(rx)}" ry="{_f(ry)}" fill="{fill}"{st}{tr}{op}/>'


def ring(cx, cy, rx, ry, color, width, opacity=None) -> str:
    op = f' opacity="{opacity}"' if opacity is not None else ""
    return f'<ellipse cx="{_f(cx)}" cy="{_f(cy)}" rx="{_f(rx)}" ry="{_f(ry)}" fill="none" stroke="{color}" stroke-width="{width}"{op}/>'


def capsule(p, q, r0, r1, steps=8):
    """The outline of a limb from `p` (radius r0) to `q` (radius r1)."""
    ang = math.atan2(q[1] - p[1], q[0] - p[0])
    pts = []
    for k in range(steps + 1):
        a = ang + math.pi / 2 + math.pi * k / steps
        pts.append((p[0] + r0 * math.cos(a), p[1] + r0 * math.sin(a)))
    for k in range(steps + 1):
        a = ang - math.pi / 2 + math.pi * k / steps
        pts.append((q[0] + r1 * math.cos(a), q[1] + r1 * math.sin(a)))
    return pts


def along(a, b):
    """``p(t, s)``: t of the way from a to b (0..1), s units to its left."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    nx, ny = -dy / n, dx / n
    return lambda t, s: (a[0] + dx * t + nx * s, a[1] + dy * t + ny * s)


def mix(c1: str, c2: str, t: float) -> str:
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def far(c: str) -> str:
    """The colour of a far limb: in the body's shadow."""
    return mix(c, "#120e1a", 0.32)


def lerp(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


# ---------------------------------------------------------------------------
# The parts every one of them has, in their own colours
# ---------------------------------------------------------------------------


def boot(ankle, toe, fill, trim=None):
    ax, ay = ankle
    tx, ty = toe
    sole = ay + 10.6
    pts = [(ax + 4.0, ay - 3.0), (ax + 5.2, sole), (tx - 2.0, sole), (tx - 3.2, sole - 3.4), (tx + 1.0, ty - 2.4), (ax - 3.6, ay + 1.0), (ax - 3.4, ay - 3.0)]
    out = [poly(pts, fill)]
    if trim:
        out.append(line([(ax - 3.2, ay + 1.4), (ax + 4.6, ay + 0.6)], trim, 1.3))
    out.append(line([(tx - 2.6, sole - 0.6), (ax + 5.0, sole - 0.6)], mix(fill, "#000000", 0.45), 0.9))
    return out


def limb(p, q, r0, r1, fill):
    return [poly(capsule(p, q, r0, r1), fill)]


def hand(wrist, tip, fill, knuckle=None):
    p = along(wrist, tip)
    pts = [p(0.0, -2.3), p(0.55, -2.8), p(1.0, -1.6), p(1.08, 0.4), p(0.9, 2.2), p(0.35, 2.6), p(0.0, 2.2)]
    out = [poly(pts, fill)]
    if knuckle:
        out.append(ellipse(*p(0.05, 0.0), 1.5, 1.5, knuckle))
    return out


# ---------------------------------------------------------------------------
# Geppetto
# ---------------------------------------------------------------------------

GEPPETTO = dict(
    coat="#2e2142", coat_lt="#4a3466", trim="#e0409c", vest="#8a62b0", vest_lt="#a986cc",
    mask="#efe4cc", mask_sh="#cdbf9f", eye="#3ff0ff", hair="#f1eef6", hair_sh="#c6c0d6",
    hat="#221a30", band="#e0409c", band_lt="#ff7cc4", wood="#e8d6b4", wood_sh="#c4ad86",
    thread="#43e6ff", leg="#271d38", boot="#2c2140",
)


def geppetto_parts():
    c = GEPPETTO
    P = {}
    P["neck"] = [poly(capsule((94.5, 112.0), (95.0, 123.0), 3.0, 3.2), c["wood_sh"])]
    # The head: hair swept back, the mask with its seam and its cyan eyes,
    # the top hat with its spool band, the antenna pin and the thread halo.
    head = []
    head.append(poly([(97.0, 90.0), (110.5, 87.0), (106.5, 94.0), (113.5, 98.5), (106.0, 101.5), (110.5, 109.0), (101.0, 107.5), (97.5, 112.0)], c["hair"]))
    head.append(line([(103.0, 93.0), (108.0, 92.0)], c["hair_sh"], 0.8))
    head.append(line([(102.0, 101.0), (107.5, 104.0)], c["hair_sh"], 0.8))
    mask = [(80.5, 96.0), (84.0, 90.5), (92.0, 89.0), (99.5, 92.0), (101.5, 100.0), (99.5, 108.0), (93.0, 113.5), (85.5, 116.5), (82.5, 111.0), (79.5, 104.0)]
    head.append(poly(mask, c["mask"]))
    head.append(poly([(94.0, 90.5), (99.5, 92.0), (101.5, 100.0), (99.5, 108.0), (93.0, 113.5), (95.5, 104.0)], c["mask_sh"], stroke=None))
    head.append(line([(88.5, 90.0), (87.0, 101.0), (85.5, 116.0)], c["mask_sh"], 0.7))
    for ex, rot in ((83.6, -12.0), (91.6, 10.0)):
        head.append(ellipse(ex, 101.5, 4.6, 3.4, c["eye"], stroke=None, rot=rot, opacity=0.35))
        head.append(ellipse(ex, 101.5, 2.7, 1.7, c["eye"], sw=0.4, rot=rot))
        head.append(ellipse(ex - 0.6, 101.0, 0.7, 0.5, "#ffffff", stroke=None))
    head.append(ellipse(98.5, 105.5, 1.1, 1.1, c["band"], sw=0.35))
    # the hat, a little back on the head
    head.append(ellipse(91.0, 90.0, 15.5, 3.4, c["hat"]))
    head.append(poly([(81.5, 89.5), (80.0, 67.5), (102.0, 66.0), (100.5, 89.0)], c["hat"]))
    head.append(ellipse(91.0, 66.8, 11.0, 2.2, mix(c["hat"], "#ffffff", 0.15)))
    head.append(poly([(81.2, 87.8), (80.6, 79.5), (101.2, 78.6), (100.6, 87.4)], c["band"]))
    for y in (80.8, 82.8, 84.8):
        head.append(line([(81.0, y + 0.6), (100.8, y)], c["band_lt"], 0.5))
    head.append(line([(98.0, 72.0), (104.5, 61.5)], "#b8b0c8", 0.9))
    head.append(ellipse(104.8, 61.0, 1.5, 1.5, c["thread"], sw=0.35))
    head.append(ring(90.5, 74.0, 17.5, 4.2, c["thread"], 0.7, opacity=0.9))
    for bx, by in ((74.0, 73.0), (85.0, 78.0), (100.0, 77.8), (107.0, 72.5)):
        head.append(ellipse(bx, by, 1.2, 1.2, c["thread"], sw=0.3))
    P["head"] = head
    # The tailcoat: a high magenta-lined collar, lapels over the lilac
    # waistcoat, a spool on its chest.
    torso = []
    body = [(82.0, 122.0), (88.0, 118.5), (102.0, 118.5), (109.5, 123.0), (108.0, 142.0), (104.0, 161.5), (84.0, 161.5), (80.0, 145.0), (79.5, 130.0)]
    torso.append(poly(body, c["coat"]))
    torso.append(poly([(85.0, 121.0), (93.0, 120.0), (91.0, 158.0), (85.0, 158.0), (82.5, 140.0)], c["vest"]))
    for y in (130.0, 138.0, 146.0, 154.0):
        torso.append(ellipse(89.0, y, 0.9, 0.9, c["band"], sw=0.3))
    torso.append(poly([(85.0, 121.0), (82.0, 131.0), (86.5, 140.0), (88.0, 124.0)], c["coat_lt"]))
    torso.append(line([(85.0, 121.0), (82.0, 131.0), (86.5, 140.0)], c["trim"], 0.9))
    torso.append(poly([(86.5, 112.0), (92.0, 117.0), (102.5, 116.5), (105.5, 111.0), (103.0, 121.0), (88.5, 121.5)], c["coat"]))
    torso.append(line([(86.5, 112.0), (88.5, 121.0)], c["trim"], 0.9))
    torso.append(poly([(86.6, 131.0), (90.6, 131.0), (90.2, 137.0), (86.2, 137.0)], c["band"], sw=0.35))
    torso.append(line([(86.0, 130.6), (91.2, 130.6)], c["wood"], 0.9))
    torso.append(line([(85.6, 137.4), (90.8, 137.4)], c["wood"], 0.9))
    torso.append(line([(104.0, 125.0), (106.0, 150.0)], c["coat_lt"], 0.6))
    P["torso"] = torso
    # The coat's tails, cut in points, to the knee.
    P["pelvis"] = [
        poly([(83.0, 158.0), (105.0, 158.0), (110.5, 186.0), (106.0, 182.0), (103.0, 195.0), (98.5, 186.0), (94.0, 192.0), (91.0, 176.0), (84.5, 172.0)], c["coat"]),
        line([(110.5, 186.0), (106.0, 182.0), (103.0, 195.0), (98.5, 186.0), (94.0, 192.0)], c["trim"], 0.9),
        line([(83.0, 160.5), (104.8, 160.5)], c["coat_lt"], 1.2),
    ]
    for side, s in (("n", "near"), ("f", "far")):
        k = (lambda col: col) if side == "n" else far
        sh, el, wr, tip = J[side + "s"], J[side + "e"], J[side + "w"], J[side + "h"]
        P[f"{s}-arm-u"] = limb(sh, el, 3.4, 3.0, k(c["coat"]))
        lower = limb(el, wr, 3.0, 2.8, k(c["coat"]))
        p = along(el, wr)
        lower.append(poly([p(0.62, -3.6), p(0.95, -3.4), p(0.95, 3.4), p(0.62, 3.6)], k(c["vest"])))
        lower.append(ellipse(*p(0.78, 0.0), 0.8, 0.8, k(c["band"]), sw=0.3))
        P[f"{s}-arm-l"] = lower
        P[f"{s}-sleeve"] = [poly(capsule(sh, lerp(sh, el, 0.45), 4.6, 3.8), k(c["coat"])), line([lerp(sh, el, -0.1), lerp(sh, el, 0.3)], k(c["trim"]), 0.7)]
        P[f"{s}-hand"] = hand(wr, tip, k(c["wood"]), knuckle=k(c["band"]))
        hip, kn, an, toe = J[side + "hip"], J[side + "k"], J[side + "a"], J[side + "t"]
        P[f"{s}-leg-u"] = limb(hip, kn, 3.8, 3.2, k(c["leg"]))
        P[f"{s}-leg-l"] = limb(kn, an, 3.2, 2.7, k(c["leg"])) + [ellipse(*kn, 1.4, 1.4, k(c["band"]), sw=0.3)]
        P[f"{s}-cuff"] = [poly(capsule(lerp(kn, an, 0.82), an, 3.4, 3.4), k(c["vest"]))]
        P[f"{s}-foot"] = boot(an, toe, k(c["boot"]), trim=k(c["band"]))
    # The cane: a plum shaft, a spool for its knob, a cyan tip.
    a, b = PEN
    p = along(a, b)
    cane = [poly(capsule(p(0.05, 0.0), b, 1.0, 0.8), c["hat"])]
    cane.append(poly([p(-0.06, -2.6), p(0.10, -2.6), p(0.10, 2.6), p(-0.06, 2.6)], c["band"]))
    cane.append(line([p(-0.08, -3.1), p(-0.08, 3.1)], c["wood"], 1.3))
    cane.append(line([p(0.12, -3.1), p(0.12, 3.1)], c["wood"], 1.3))
    cane.append(ellipse(*p(1.0, 0.0), 3.4, 3.4, c["thread"], stroke=None, opacity=0.35))
    cane.append(ellipse(*p(1.0, 0.0), 1.6, 1.6, c["thread"], sw=0.35))
    P["near-pen"] = cane
    return P


# ---------------------------------------------------------------------------
# Clause
# ---------------------------------------------------------------------------

CLAUSE = dict(
    chassis="#2b2733", chassis_lt="#4a4456", detail="#5f566e", cloth="#f2e6d2", cloth_sh="#d9c8ae",
    orange="#e8733a", orange_lt="#f6a65c", eye="#ffb35c", mask="#24202c",
)


def burst(cx, cy, r, color, width):
    return [line([(cx + r * math.cos(a), cy + r * math.sin(a)), (cx - r * math.cos(a), cy - r * math.sin(a))], color, width)
            for a in (math.radians(d) for d in (0, 30, 60, 90, 120, 150))]


def clause_parts():
    c = CLAUSE
    P = {}
    P["neck"] = [poly(capsule((94.5, 112.0), (95.0, 123.0), 2.8, 3.0), c["detail"])]
    head = []
    # The petal fins: a crown of blocky petals round the back and the top.
    hub = (95.0, 99.0)
    for k, deg in enumerate(range(-160, 41, 25)):
        a = math.radians(deg)
        w = math.radians(9.0)
        r0, r1 = 9.0, 21.0
        pts = [(hub[0] + r0 * math.cos(a - w * 0.6), hub[1] + r0 * math.sin(a - w * 0.6)),
               (hub[0] + r1 * math.cos(a - w), hub[1] + r1 * math.sin(a - w)),
               (hub[0] + r1 * math.cos(a + w), hub[1] + r1 * math.sin(a + w)),
               (hub[0] + r0 * math.cos(a + w * 0.6), hub[1] + r0 * math.sin(a + w * 0.6))]
        head.append(poly(pts, c["orange"] if k % 2 == 0 else c["orange_lt"]))
    head.append(ellipse(90.5, 103.0, 12.0, 13.5, c["mask"]))
    head.append(ellipse(87.0, 99.0, 6.0, 7.0, mix(c["mask"], "#ffffff", 0.08), stroke=None))
    head.append(ellipse(100.0, 104.0, 4.2, 4.6, c["detail"]))
    head.append(ellipse(100.0, 104.0, 2.0, 2.2, c["chassis_lt"], sw=0.35))
    for ex in (84.5, 91.0):
        head.append(ellipse(ex, 102.5, 3.6, 5.6, c["eye"], stroke=None, opacity=0.3))
        head.append(poly(capsule((ex, 100.0), (ex, 105.0), 1.1, 1.1, steps=5), c["eye"], sw=0.3))
    P["head"] = head
    torso = []
    torso.append(poly([(82.0, 122.0), (88.0, 118.5), (102.0, 118.5), (109.0, 123.0), (107.5, 142.0), (103.5, 161.5), (85.0, 161.5), (81.0, 145.0)], c["chassis"]))
    torso.append(line([(86.0, 150.0), (102.0, 150.0)], c["detail"], 0.8))
    # The poncho: over the shoulders, a point at the front and the back,
    # lined in orange, the starburst on it.
    poncho = [(84.0, 117.0), (104.0, 116.0), (112.0, 128.0), (110.0, 148.0), (100.0, 143.0), (90.0, 152.0), (78.0, 141.0), (79.0, 126.0)]
    torso.append(poly(poncho, c["cloth"]))
    torso.append(line([(110.0, 148.0), (100.0, 143.0), (90.0, 152.0), (78.0, 141.0)], c["orange"], 1.2))
    torso.append(poly([(100.0, 120.0), (109.0, 127.0), (108.0, 144.0), (101.0, 141.0)], c["cloth_sh"], stroke=None))
    torso += burst(93.0, 132.0, 4.6, c["orange"], 1.3)
    torso.append(poly([(86.0, 112.5), (101.5, 112.0), (104.0, 119.0), (84.0, 119.5)], c["cloth"]))
    P["torso"] = torso
    P["pelvis"] = [
        poly([(83.0, 158.0), (105.0, 158.0), (106.5, 170.0), (82.0, 170.0)], c["chassis"]),
        line([(83.0, 160.6), (105.0, 160.6)], c["orange"], 1.4),
        # the back of the cloak, to the knee
        poly([(101.0, 150.0), (111.0, 146.0), (114.0, 186.0), (106.0, 182.0), (103.0, 172.0)], c["cloth"]),
        line([(114.0, 186.0), (106.0, 182.0)], c["orange"], 1.2),
    ]
    for side, s in (("n", "near"), ("f", "far")):
        k = (lambda col: col) if side == "n" else far
        sh, el, wr, tip = J[side + "s"], J[side + "e"], J[side + "w"], J[side + "h"]
        P[f"{s}-arm-u"] = limb(sh, el, 3.0, 2.7, k(c["chassis"]))
        P[f"{s}-arm-l"] = limb(el, wr, 2.7, 2.5, k(c["chassis"])) + [poly([lerp(el, wr, 0.0), *[(el[0] + 2.6 * math.cos(a), el[1] + 2.6 * math.sin(a)) for a in (0.6, 2.2, 3.8, 5.4)]], k(c["orange"]), sw=0.35)]
        P[f"{s}-sleeve"] = [poly(capsule(sh, lerp(sh, el, 0.4), 4.8, 4.2), k(c["cloth"])), line([lerp(sh, el, 0.38), lerp(sh, el, 0.48)], k(c["orange"]), 1.0)]
        P[f"{s}-hand"] = hand(wr, tip, k(c["detail"]))
        hip, kn, an, toe = J[side + "hip"], J[side + "k"], J[side + "a"], J[side + "t"]
        P[f"{s}-leg-u"] = limb(hip, kn, 3.6, 3.0, k(c["chassis"]))
        P[f"{s}-leg-l"] = limb(kn, an, 3.0, 2.5, k(c["chassis"])) + [poly([(kn[0] - 2.4, kn[1]), (kn[0], kn[1] - 2.8), (kn[0] + 2.4, kn[1]), (kn[0], kn[1] + 3.6)], k(c["orange"]), sw=0.35)]
        P[f"{s}-cuff"] = [poly(capsule(lerp(kn, an, 0.8), an, 3.2, 3.2), k(c["orange_lt"]))]
        P[f"{s}-foot"] = boot(an, toe, k(c["cloth"]), trim=k(c["orange"]))
    # The staff: dark, the starburst at its head (the end that strikes).
    a, b = PEN
    p = along(a, b)
    staff = [poly(capsule(p(-0.04, 0.0), p(0.88, 0.0), 0.9, 0.9), c["chassis_lt"])]
    staff.append(ellipse(*b, 6.2, 6.2, c["orange"], stroke=None, opacity=0.3))
    staff += burst(b[0], b[1], 4.6, INK, 2.4)
    staff += burst(b[0], b[1], 4.4, c["orange"], 1.5)
    staff.append(ellipse(*b, 1.3, 1.3, c["orange_lt"], sw=0.3))
    staff.append(line([p(0.0, -1.6), p(0.0, 1.6)], c["orange"], 1.2))
    P["near-pen"] = staff
    return P


# ---------------------------------------------------------------------------
# Wren
# ---------------------------------------------------------------------------

WREN = dict(
    cloth="#f3e3c4", cloth_sh="#d8c39c", gold="#f0bd4c", gold_dk="#b88a2a", lilac="#b590e0",
    purple="#7a4cc8", deep="#46307a", face="#231d30", eye="#ffd166", leg="#3e2d63", wrap="#efe2c6",
)


def feather(base, tip, w, fill):
    p = along(base, tip)
    return poly([p(0.0, 0.0), p(0.35, -w), p(0.8, -w * 0.6), p(1.0, 0.0), p(0.7, w * 0.5), p(0.3, w * 0.6)], fill)


def wren_parts():
    c = WREN
    P = {}
    P["neck"] = [poly(capsule((94.5, 112.0), (95.0, 123.0), 2.8, 3.0), c["deep"])]
    head = []
    head.append(ellipse(90.5, 104.5, 11.0, 12.0, c["face"]))
    head.append(ellipse(99.0, 105.5, 3.8, 4.2, c["gold_dk"]))
    head.append(ellipse(99.0, 105.5, 1.8, 2.0, c["gold"], sw=0.35))
    for ex in (84.5, 90.5):
        head.append(ellipse(ex, 104.0, 3.4, 5.2, c["eye"], stroke=None, opacity=0.3))
        head.append(poly(capsule((ex, 101.6), (ex, 106.4), 1.05, 1.05, steps=5), c["eye"], sw=0.3))
    # The hat: a wide cone, a gold band and rim, tassels at its edge, and a
    # purple feather in it that sweeps back.
    head.append(feather((100.0, 85.0), (117.0, 66.0), 4.6, c["purple"]))
    head.append(feather((97.0, 86.0), (112.0, 70.0), 3.0, c["lilac"]))
    head.append(poly([(68.0, 96.5), (91.5, 76.0), (116.0, 96.0), (110.0, 98.5), (92.0, 97.0), (74.0, 98.8)], c["cloth"]))
    head.append(poly([(74.0, 91.5), (109.0, 91.0), (113.0, 94.0), (71.0, 94.6)], c["gold"], sw=0.35))
    head.append(line([(68.0, 96.5), (74.0, 98.8), (92.0, 97.0), (110.0, 98.5), (116.0, 96.0)], c["gold_dk"], 0.9))
    head.append(line([(91.5, 76.0), (86.0, 92.0)], c["cloth_sh"], 0.6))
    head.append(line([(91.5, 76.0), (100.0, 91.5)], c["cloth_sh"], 0.6))
    for tx in (70.0, 113.5):
        head.append(line([(tx, 97.5), (tx, 105.0)], c["gold_dk"], 0.6))
        head.append(poly([(tx - 1.2, 104.0), (tx + 1.2, 104.0), (tx + 1.5, 109.0), (tx - 1.5, 109.0)], c["gold"], sw=0.35))
    P["head"] = head
    torso = []
    # The cape of purple feathers behind the shoulders.
    for k, (bx, tipx, tipy) in enumerate(((101.0, 113.0, 150.0), (99.0, 108.0, 154.0), (104.0, 115.0, 142.0))):
        torso.append(feather((bx, 120.0), (tipx, tipy), 3.6, c["purple"] if k != 1 else c["deep"]))
    robe = [(82.0, 121.0), (88.0, 118.5), (102.0, 118.5), (108.0, 123.0), (107.0, 142.0), (104.0, 161.5), (84.0, 161.5), (80.0, 145.0)]
    torso.append(poly(robe, c["cloth"]))
    torso.append(line([(84.0, 122.0), (87.0, 160.0)], c["gold"], 1.0))
    torso.append(poly([(88.5, 140.0), (97.0, 140.0), (96.0, 156.0), (88.5, 156.0)], mix(c["cloth"], c["cloth_sh"], 0.6), stroke=None))
    # a mark on the front panel: the tactician's ledger of words
    torso.append(line([(90.0, 143.0), (95.5, 143.0)], c["deep"], 0.8))
    torso.append(line([(92.8, 141.5), (92.8, 143.0)], c["deep"], 0.8))
    torso.append(line([(90.6, 145.0), (95.0, 153.0)], c["deep"], 0.8))
    torso.append(line([(95.0, 145.0), (90.4, 153.0)], c["deep"], 0.8))
    torso.append(line([(82.5, 158.5), (104.5, 158.5)], c["gold_dk"], 1.4))
    # The scarf, wound round the neck, its end blown back.
    torso.append(poly([(85.0, 113.0), (102.5, 112.5), (105.0, 121.0), (84.0, 122.0)], c["purple"]))
    torso.append(poly([(101.0, 117.0), (113.0, 121.0), (116.0, 129.0), (106.0, 125.0)], c["purple"]))
    torso.append(line([(86.0, 117.5), (103.5, 117.0)], c["deep"], 0.6))
    P["torso"] = torso
    P["pelvis"] = [
        poly([(83.0, 158.0), (105.0, 158.0), (108.0, 182.0), (99.0, 186.0), (92.0, 180.0), (84.0, 184.0), (81.0, 170.0)], c["cloth"]),
        poly([(97.0, 159.0), (104.0, 159.0), (106.5, 181.0), (100.0, 184.0)], c["purple"], sw=0.35),
        line([(81.0, 170.0), (84.0, 184.0), (92.0, 180.0), (99.0, 186.0), (108.0, 182.0)], c["gold"], 0.9),
    ]
    for side, s in (("n", "near"), ("f", "far")):
        k = (lambda col: col) if side == "n" else far
        sh, el, wr, tip = J[side + "s"], J[side + "e"], J[side + "w"], J[side + "h"]
        P[f"{s}-arm-u"] = limb(sh, el, 3.0, 2.7, k(c["deep"]))
        lower = limb(el, wr, 2.7, 2.5, k(c["deep"]))
        # the wide sleeve of the robe, open at the wrist
        p = along(el, wr)
        lower.append(poly([p(-0.1, -3.6), p(0.75, -5.6), p(0.85, 5.0), p(-0.1, 3.6)], k(c["cloth"])))
        lower.append(line([p(0.75, -5.6), p(0.85, 5.0)], k(c["gold"]), 0.9))
        P[f"{s}-arm-l"] = lower
        P[f"{s}-sleeve"] = [poly(capsule(sh, lerp(sh, el, 0.55), 5.2, 4.4), k(c["cloth"])), feather(lerp(sh, el, -0.1), lerp(sh, el, 0.7), 2.4, k(c["purple"]))]
        P[f"{s}-hand"] = hand(wr, tip, k(c["deep"]))
        hip, kn, an, toe = J[side + "hip"], J[side + "k"], J[side + "a"], J[side + "t"]
        P[f"{s}-leg-u"] = limb(hip, kn, 4.4, 3.8, k(c["leg"]))
        P[f"{s}-leg-l"] = limb(kn, an, 3.8, 2.6, k(c["leg"]))
        cuff = [poly(capsule(lerp(kn, an, 0.55), an, 3.0, 2.8), k(c["wrap"]))]
        for t in (0.62, 0.74, 0.86):
            q = along(kn, an)
            cuff.append(line([q(t, -3.0), q(t + 0.04, 3.0)], k(c["deep"]), 0.8))
        P[f"{s}-cuff"] = cuff
        P[f"{s}-foot"] = boot(an, toe, k(c["wrap"]), trim=k(c["gold"]))
    # The fan: a short handle, and the fan open past the hand, gold ribs on
    # cream with a purple cloud.
    a, b = PEN
    p = along(a, b)
    fan = [poly(capsule(p(0.05, 0.0), p(0.45, 0.0), 0.9, 0.9), c["gold_dk"])]
    pivot = p(0.40, 0.0)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    r = 21.0
    spread = math.radians(42.0)
    arc = [(pivot[0] + r * math.cos(ang + spread * u), pivot[1] + r * math.sin(ang + spread * u)) for u in [i / 6.0 - 1.0 for i in range(13)]]
    fan.append(poly([pivot, *arc], c["cloth"]))
    for i in range(0, 13, 2):
        fan.append(line([pivot, arc[i]], c["gold_dk"], 0.6))
    inner = [(pivot[0] + 9.0 * math.cos(ang + spread * u), pivot[1] + 9.0 * math.sin(ang + spread * u)) for u in [i / 6.0 - 1.0 for i in range(13)]]
    fan.append(line(inner, c["gold"], 1.0))
    mid = (pivot[0] + 15.0 * math.cos(ang), pivot[1] + 15.0 * math.sin(ang))
    fan.append(ellipse(mid[0] - 1.5, mid[1], 2.4, 1.6, c["lilac"], sw=0.35))
    fan.append(ellipse(mid[0] + 1.8, mid[1] - 0.8, 2.0, 1.5, c["lilac"], sw=0.35))
    fan.append(ellipse(*pivot, 1.2, 1.2, c["gold"], sw=0.35))
    P["near-pen"] = fan
    return P


AGENTS = {"geppetto": geppetto_parts, "clause": clause_parts, "wren": wren_parts}


# ---------------------------------------------------------------------------
# Writing the drawing into the Director's SVG
# ---------------------------------------------------------------------------


def _group_span(svg: str, gid: str) -> tuple[int, int, int]:
    """The start of the group, the end of its open tag, and its end."""
    start = svg.index(f'<g id="{gid}"')
    open_end = svg.index(">", start) + 1
    depth = 0
    for m in re.finditer(r"<g\b|</g>", svg[start:]):
        depth += -1 if m.group() == "</g>" else 1
        if depth == 0:
            return start, open_end, start + m.end()
    raise ValueError(gid)


def _clean_open(tag: str) -> str:
    """The open tag with no placement or pen of its own: the art is drawn
    where the joints are."""
    tag = re.sub(r'\s(transform|stroke|stroke-width|style)="[^"]*"', "", tag)
    return tag


def derive(svg: str, name: str, parts: dict) -> str:
    parts = dict(parts)
    # The turn's torso parts draw the same body.
    parts.setdefault("torso-side", parts["torso"])
    parts.setdefault("torso-back", parts["torso"])
    ids = re.findall(r'<g id="part-([a-z-]+)"', svg)
    nested = {"torso-back-shade", "torso-back-shell", "torso-side-shade", "torso-side-shell"}
    for pid in ids:
        if pid in nested:
            continue
        if pid not in parts:
            raise KeyError(f"{name}: no drawing for part-{pid}")
        start, open_end, end = _group_span(svg, f"part-{pid}")
        body = "".join(parts[pid])
        svg = svg[:start] + _clean_open(svg[start:open_end]) + body + "</g>" + svg[end:]
    svg = re.sub(r'<metadata id="metadata-director">[^<]*</metadata>',
                 f'<metadata id="metadata-{name}">The bossofthegame\'s agent {name}, drawn on the Director\'s rig by scripts/svg_art/boss_agents_art.py.</metadata>', svg)
    svg = svg.replace('id="director-svg"', f'id="{name}-svg"')
    return svg.replace('data-character="director"', f'data-character="{name}"')


def main() -> None:
    source = SOURCE.read_text()
    motion = json.loads(MOTION.read_text())
    for name, make in AGENTS.items():
        out = ROOT / name / f"{name}.svg"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(derive(source, name, make()))
        m = dict(motion, character=name, rig=dict(motion["rig"], svg=f"{name}.svg"))
        (out.parent / f"{name}.motion.json").write_text(json.dumps(m, indent=2) + "\n")
        print(out)


if __name__ == "__main__":
    main()
