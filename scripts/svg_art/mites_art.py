#!/usr/bin/env python3
"""The mites, redesigned: round-1 candidates for the Dividing Mite and the Exploding Mite.

    uv run python scripts/svg_art/mites_art.py --all DIR      # side + front SVG of every look, and its strip
    uv run python scripts/svg_art/mites_art.py --sheets DIR   # the same, plus the contact sheets (PNG)

Jon, 2026-10-22: "dividing mite, exploding mite" in the redesign queue. The old
art is two recolours of the procedural robot generator (``replicator_blob_drone``
and ``volatile_bomb_drone`` in ``targets/characters/robot_side.py``): a white
box-headed biped with a sword, the same body as half the robot cast, and
nothing in either drawing says what the mite DOES.

WHAT THEY DO (the code, not the barks):

* ``npc_dividing_mite``: four hit points, slow (run 130), and on death it
  splits into TWO Puppy Slugs, one spawned 30 px to each side of the corpse
  (``divides_into: "npc_puppy_slug"``, ``spawn_split_offspring`` in
  ``damage_drops.rs``). So the drawing shows a body that is visibly two of
  something, held together, that will come apart left and right.
* ``npc_exploding_mite``: two hit points, fast (run 245), and its corpse
  detonates (``explodes_on_death``): a 128 px box, 3 damage, so a point-blank
  kill is punished. So the drawing shows pressure, a fuse, warning colour:
  "don't hit me up close".

THE FAMILY. Both are small robot mites on one chassis: a round body slung low
on eight short jointed legs (high knees, pointed feet, so it reads as a bug and
not as a dog), one dark visor eye with a lit pupil, and a pair of hooked
mandibles at the front -- the mandibles are the swipe both of them attack with
(``dividing_mite_swipe`` / ``exploding_mite_swipe``). The body on that chassis
is what tells them apart: a body that is two (cool teal, the colour of the
Puppy Slugs it releases) or a body under pressure (dark steel, hazard yellow,
a hot core).

THREE LOOKS EACH, ``LOOKS`` below; each is a side view facing right, a front
view, and a 3-frame strip of its signature moment (the split; the wind-up to
the blast -- the blast itself is the hit VFX, not the body).

House style (the redesigned cast's): a thick dark ink outline, flat cel fills
with one shade band below-left and a light band above-right, no drop shadow
ever, and nothing painted that a shader would add. The ink is thick because
these are small: one design unit is about 0.16 world px (the player robot
stands 48), so the 7-unit outline is about one screen pixel at 1x.

CAST, 2026-10-23: look A of each. Jon asked to see the new mites in the game
and did not pick, so the twin-core cell and the bomb were chosen. ``--cast``
writes them as rig-ready side views (``cast_dividing``, ``cast_exploding``)
to ``data/characters/{dividing,exploding}_mite_v2/``, for
``scripts/build_mite_v2_rigs.py`` and the targets ``dividing_mite_v2`` and
``exploding_mite_v2``. Looks B and C stay candidates (``--all``, ``--sheets``):
nothing registers them.

    uv run python scripts/svg_art/mites_art.py --cast       # the two cast drawings
"""
from __future__ import annotations

import io
import math
import sys
from pathlib import Path
from typing import Callable, Dict, List, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import svgkit as svg  # noqa: E402

W = H = 400
GROUND = 354.0
INK = "#1b1a20"
OUT = 7.0  # silhouette ink
IN = 3.6  # interior lines
#: Shade down-left, light up-right (the house light).
SD, LD = (-1.0, 0.65), (1.0, -0.8)
#: Design units to world px: the player robot's 48 px against these bodies.
WORLD_PER_UNIT = 0.16

svg.configure(dx=0, dy=0, ink=INK, ow=OUT / 2, colors={})

Pt = Tuple[float, float]
Items = List[str]

# ---------------------------------------------------------------------------------------------
# drawing helpers (cel copied in spirit from oiler_art.py; svgkit for splines and capsules)
# ---------------------------------------------------------------------------------------------

_N = [0]
#: While True the drawing is about to be mirrored, so the shade/light bands
#: are flipped here and come out below-left / above-right after the mirror.
_MIRROR = [False]


def uid(tag="m") -> str:
    _N[0] += 1
    return f"mite{tag}{_N[0]}"


def f(v: float) -> str:
    return svg.f(v)


def E(cx, cy, rx, ry, rot=0.0) -> str:
    """An exact ellipse as a path (so it can be clipped and banded like any shape)."""
    if rot:
        c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        p1 = (cx - rx * c, cy - rx * s)
        p2 = (cx + rx * c, cy + rx * s)
    else:
        p1, p2 = (cx - rx, cy), (cx + rx, cy)
    return (f"M{f(p1[0])},{f(p1[1])} A{f(rx)},{f(ry)} {f(rot)} 1,0 {f(p2[0])},{f(p2[1])} "
            f"A{f(rx)},{f(ry)} {f(rot)} 1,0 {f(p1[0])},{f(p1[1])} Z")


def sm(points, closed=True, tension=1.0) -> str:
    return svg.smooth(points, closed=closed, tension=tension)


def poly(points) -> str:
    return svg.poly(points)


def P(d, fill="none", stroke=None, sw=None, extra="") -> str:
    return svg.path(d, fill, stroke, sw, extra)


def ln(points, color=INK, sw=IN, tension=1.0) -> str:
    return svg.line(points, color, sw, tension=tension)


def cel(d, base, shade, light=None, items=(), s=11.0, l=6.0, sw=OUT, ink=INK, sdir=SD, ldir=LD) -> Items:
    """A shape: its fill, a ``shade`` band along the edges facing ``sdir`` and a
    ``light`` band along those facing ``ldir`` (clipped inside), the detail
    ``items`` clipped to it, then the ink outline."""
    if _MIRROR[0]:
        sdir, ldir = (-sdir[0], sdir[1]), (-ldir[0], ldir[1])
    cid = uid()
    sx, sy = -sdir[0] * s, -sdir[1] * s
    out = [f'<clipPath id="{cid}"><path d="{d}" /></clipPath>',
           f'<clipPath id="{cid}s"><path d="{d}" transform="translate({sx:.2f} {sy:.2f})" /></clipPath>',
           f'<g clip-path="url(#{cid})">', P(d, shade), f'<g clip-path="url(#{cid}s)">']
    if light:
        lx, ly = -ldir[0] * l, -ldir[1] * l
        out += [P(d, light), P(d, base, extra=f' transform="translate({lx:.2f} {ly:.2f})"')]
    else:
        out.append(P(d, base))
    out.append("</g>")
    out += list(items)
    out.append("</g>")
    if sw:
        out.append(P(d, "none", ink, sw))
    return out


def clip(d, items) -> Items:
    cid = uid("c")
    return [f'<clipPath id="{cid}"><path d="{d}" /></clipPath>', f'<g clip-path="url(#{cid})">', *items, "</g>"]


def disc(cx, cy, r, fill, sw=IN, stroke=INK) -> str:
    return f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}"' + (
        f' stroke="{stroke}" stroke-width="{f(sw)}"' if sw else "") + " />"


def grp(items, tf: str = "", extra: str = "") -> Items:
    return [f'<g{(" transform=" + chr(34) + tf + chr(34)) if tf else ""}{extra}>', *items, "</g>"]


def about(cx, cy, k=1.0, rot=0.0, dx=0.0, dy=0.0, kx=None, ky=None) -> str:
    """A transform that scales by ``k`` (or ``kx``/``ky``) and turns by ``rot``
    degrees about ``(cx, cy)``, then moves by ``(dx, dy)``."""
    kx = k if kx is None else kx
    ky = k if ky is None else ky
    return (f"translate({f(cx + dx)} {f(cy + dy)}) rotate({f(rot)}) scale({f(kx)} {f(ky)}) "
            f"translate({f(-cx)} {f(-cy)})")


def mirror_tf(cx=200.0) -> str:
    return f"translate({f(2 * cx)} 0) scale(-1 1)"


def layer(name: str, items: Items) -> Items:
    """A named part group: what a rig would bind (``data-mite-part``)."""
    return [f'<g data-mite-part="{name}">', *items, "</g>"]


def hook(base: Pt, ang_deg: float, length: float, width: float, curl: float, steps=9) -> List[Pt]:
    """A tapered hook from ``base`` heading ``ang_deg`` and curling by ``curl``
    degrees along its length (positive = clockwise on screen)."""
    pts_l, pts_r = [], []
    x, y = base
    a = math.radians(ang_deg)
    ds = length / steps
    for i in range(steps + 1):
        t = i / steps
        w = width * (1.0 - t) ** 0.8 * 0.5 + 0.4
        nx, ny = -math.sin(a), math.cos(a)
        pts_l.append((x + nx * w, y + ny * w))
        pts_r.append((x - nx * w, y - ny * w))
        x += math.cos(a) * ds
        y += math.sin(a) * ds
        a += math.radians(curl) / steps
    tip = (x - math.cos(a) * ds, y - math.sin(a) * ds)
    return pts_l[:-1] + [(tip[0], tip[1], True)] + list(reversed(pts_r[:-1]))


# ---------------------------------------------------------------------------------------------
# the family chassis: legs, mandibles, the eye
# ---------------------------------------------------------------------------------------------

def leg(hip: Pt, knee: Pt, foot: Pt, pal: Dict, far=False) -> Items:
    """One jointed leg: thigh, shin and a pointed foot, inked as one silhouette
    (the ink of both pieces first, then their fills), and a ball knee."""
    col, sh = (pal["leg_sh"], pal["leg_dk"]) if far else (pal["leg"], pal["leg_sh"])
    thigh = svg.capsule(hip, knee, 7.2, 6.2)
    # the shin ends in a point at the foot
    ang = math.atan2(foot[1] - knee[1], foot[0] - knee[0])
    nx, ny = -math.sin(ang), math.cos(ang)
    mid = (knee[0] + (foot[0] - knee[0]) * 0.72, knee[1] + (foot[1] - knee[1]) * 0.72)
    shin = sm([(knee[0] + nx * 5.4, knee[1] + ny * 5.4), (mid[0] + nx * 3.8, mid[1] + ny * 3.8),
               (foot[0], foot[1], True), (mid[0] - nx * 3.4, mid[1] - ny * 3.4),
               (knee[0] - nx * 5.4, knee[1] - ny * 5.4), (knee[0] - math.cos(ang) * 5.6, knee[1] - math.sin(ang) * 5.6)])
    tip = sm([(mid[0] + nx * 3.8, mid[1] + ny * 3.8), (foot[0], foot[1], True), (mid[0] - nx * 3.4, mid[1] - ny * 3.4),
              ((mid[0] + foot[0]) / 2, (mid[1] + foot[1]) / 2 - 1)])
    out = [P(thigh, INK, INK, OUT), P(shin, INK, INK, OUT)]
    out += cel(thigh, col, sh, None if far else pal.get("leg_lt"), s=4, sw=0)
    out += cel(shin, col, sh, None if far else pal.get("leg_lt"), s=4, sw=0)
    out.append(P(tip, pal["foot"]))
    out.append(disc(knee[0], knee[1], 7.0, pal["joint_sh"] if far else pal["joint"], sw=IN))
    if not far:
        out.append(disc(knee[0] + 2.2, knee[1] - 2.2, 2.4, pal.get("joint_lt", "#ffffff"), sw=0))
    return out


def legs_side(cx: float, by: float, s: float, pal: Dict, which=("rear", "rmid", "fmid", "front"), lift=0.0) -> Tuple[Items, Items]:
    """Eight legs seen from the side: four near, four far (shifted forward,
    darker, behind the body). Every leg arches: the knee rides up and out past
    the body and the shin comes down to a pointed foot further out still, so it
    reads as a mite and not as a table. ``by`` is the body's underside, ``s``
    its half length. Returns (far, near)."""
    spec = {
        # name: hip (dx, dy), knee (dx, dy), foot dx -- dx in units of s, dy in px from by
        "rear": ((-0.55, -30), (-1.42, -66), -1.72),
        "rmid": ((-0.30, -14), (-0.95, -34), -1.12),
        "fmid": ((0.30, -14), (0.95, -34), 1.12),
        "front": ((0.55, -30), (1.42, -68), 1.72),
    }
    far, near = [], []
    for name in which:
        (hx, hy), (kx, ky), fx = spec[name]
        for is_far, off in ((True, 0.22), (False, 0.0)):
            hip = (cx + (hx + off) * s, by + hy - (8 if is_far else 0))
            knee = (cx + (kx * (0.9 if is_far else 1.0) + off * 0.5) * s, by + ky - (18 if is_far else 0) - lift)
            foot = (cx + (fx * (0.8 if is_far else 1.0) + off) * s, GROUND - (6 if is_far else 0))
            (far if is_far else near).extend(leg(hip, knee, foot, pal, far=is_far))
    return far, near


def legs_front(cx: float, by: float, s: float, pal: Dict, lift=0.0) -> Tuple[Items, Items]:
    """Eight legs from the front: the outer pairs arched wide, the inner pairs
    under the body; the back pairs dark behind."""
    far, near = [], []
    for side in (-1, 1):
        for (hx, hy), (kx, ky), fx, is_far in (
            ((0.55, -34), (1.30, -80), 1.58, True),
            ((0.40, -20), (1.02, -48), 1.20, True),
            ((0.60, -26), (1.42, -62), 1.74, False),
            ((0.30, -8), (0.78, -28), 0.94, False),
        ):
            hip = (cx + side * hx * s, by + hy)
            knee = (cx + side * kx * s, by + ky - lift)
            foot = (cx + side * fx * s, GROUND - (6 if is_far else 0))
            (far if is_far else near).extend(leg(hip, knee, foot, pal, far=is_far))
    return far, near


def mandibles_side(base: Pt, pal: Dict, open_=0.0, scale=1.25) -> Tuple[Items, Items]:
    """The swipe: two hooked mandibles under the front of the body, the far one
    behind. Returns (far, near)."""
    far = cel(sm(hook((base[0] - 2, base[1] - 8), 2 - open_ * 30, 36 * scale, 13 * scale, 80)), pal["mand_sh"], pal["mand_dk"], s=3)
    near = cel(sm(hook(base, 18 + open_ * 25, 40 * scale, 15 * scale, 85)), pal["mand"], pal["mand_sh"], pal.get("mand_lt"), s=4, l=3)
    return far, near


def mandibles_front(cx: float, y: float, gap: float, pal: Dict, scale=1.0) -> Items:
    out = []
    for side in (-1, 1):
        ang = 90 - side * 10
        pts = hook((cx + side * (gap + 8), y), ang, 34 * scale, 14 * scale, side * 70)
        out += cel(sm(pts), pal["mand"], pal["mand_sh"], pal.get("mand_lt"), s=4, l=3)
    return out


def eye(cx: float, cy: float, rx: float, ry: float, pal: Dict, look=(4.0, 0.0), rot=0.0, mood="calm", pupil_k=1.0) -> Items:
    """The family eye: a dark visor socket with a lit pupil and a glint.
    ``mood`` "angry" adds a lowered brow plate; "wide" grows the pupil and
    rings it; "x" is a struck-out eye."""
    out = [P(E(cx, cy, rx, ry, rot), pal["socket"], INK, IN + 0.6)]
    px, py = cx + look[0], cy + look[1]
    pr = min(rx, ry) * 0.62 * pupil_k
    if mood == "wide":
        out.append(disc(px, py, pr * 1.25, pal["pupil_glow"], sw=0))
    out.append(P(E(px, py, pr * 0.82, pr, rot), pal["pupil"]))
    out.append(P(E(px, py, pr * 0.42, pr * 0.55, rot), pal["pupil_core"]))
    out.append(disc(px + pr * 0.35, py - pr * 0.45, pr * 0.25, "#ffffff", sw=0))
    if mood == "angry":
        # a brow plate cutting the top of the socket, low at the front
        out += cel(poly([(cx - rx - 4, cy - ry - 6), (cx + rx + 6, cy - ry * 0.25), (cx + rx + 8, cy - ry - 4), (cx - rx - 2, cy - ry - 14)]),
                   pal["brow"], pal["brow_sh"], None, s=3, sw=IN)
    return out


def spark(cx: float, cy: float, r: float, pal: Dict, rot=0.0) -> Items:
    """A fuse spark: an authored star (no glow filter), hot core."""
    out = []
    for k, col, sw in ((1.0, pal["spark"], IN), (0.62, pal["spark_core"], 0)):
        pts = []
        n = 8
        for i in range(2 * n):
            a = math.radians(rot + i * 180 / n)
            rr = r * k * (1.0 if i % 2 == 0 else 0.42) * (1.0 if i % 4 else 1.18)
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr, True))
        out.append(P(poly(pts), col, INK if sw else None, sw))
    out.append(disc(cx, cy, r * 0.18, "#ffffff", sw=0))
    return out


def stripes(x0, y0, x1, y1, step, width, color, ang=45.0) -> Items:
    """Diagonal hazard stripes filling a box (clip them to the band)."""
    out = []
    t = math.tan(math.radians(ang))
    hgt = y1 - y0
    x = x0 - hgt * t
    while x < x1:
        out.append(P(poly([(x, y1), (x + width, y1), (x + width + hgt * t, y0), (x + hgt * t, y0)]), color))
        x += step
    return out


# ---------------------------------------------------------------------------------------------
# palettes
# ---------------------------------------------------------------------------------------------

CHASSIS = dict(
    leg="#8b95a3", leg_sh="#5f6977", leg_dk="#444c57", leg_lt="#b4bdc8",
    joint="#3a3f48", joint_sh="#2a2e35", joint_lt="#7d8693", foot="#2a2e35",
    mand="#7d8795", mand_sh="#555d69", mand_dk="#3a4049", mand_lt="#a7b0bc",
    socket="#15171d", brow="#3a3f48", brow_sh="#262a31",
)
DIV = dict(CHASSIS, pupil="#5ff2dc", pupil_core="#e8fff9", pupil_glow="#2aa894",
           mem="#5fb8a4", mem_sh="#3c8a7b", mem_lt="#93dcc8", mem_dk="#2b6a5f",
           core="#f2e98a", core_sh="#c9b84e", core_dot="#7a6a1e",
           ring="#bff7ea", ring_hot="#ffffff",
           slate="#4a5361", slate_sh="#343b46", slate_lt="#6b7686")
EXP = dict(CHASSIS, pupil="#ff5a3a", pupil_core="#ffe0a0", pupil_glow="#ff9a3a",
           spark="#ffb43a", spark_core="#fff3b0",
           steel="#3e4552", steel_sh="#282d37", steel_lt="#5d6778",
           haz="#f2c230", haz_sh="#c7961c", hot="#ff7a2a", hot_lt="#ffd26a", white_hot="#fff6d8",
           brass="#c9953f", brass_sh="#946a26", brass_lt="#e8c072",
           red="#cf3b2e", red_sh="#982719", red_lt="#ec6a52")


# ---------------------------------------------------------------------------------------------
# DIVIDING MITE
# ---------------------------------------------------------------------------------------------

def nucleus(cx: float, cy: float, r: float, pal: Dict, seed: int = 0) -> Items:
    """A cell nucleus seen through the membrane: a soft lumpy blob (not a
    round eye), coiled chromatin and a nucleolus."""
    pts = []
    for i in range(9):
        a = math.radians(i * 40 + seed * 17)
        rr = r * (1.0 + 0.14 * math.sin(i * 2.3 + seed))
        pts.append((cx + math.cos(a) * rr * 1.12, cy + math.sin(a) * rr * 0.9))
    out = cel(sm(pts), pal["core"], pal["core_sh"], None, s=4, sw=IN)
    out.append(ln([(cx - r * 0.55, cy + r * 0.1), (cx - r * 0.2, cy - r * 0.35), (cx + r * 0.1, cy + r * 0.15),
                   (cx + r * 0.45, cy - r * 0.25)], pal["core_dot"], 3.2))
    out.append(disc(cx + r * 0.25, cy + r * 0.35, r * 0.2, pal["core_dot"], sw=0))
    return out


def div_a(view: str, t: int = 0) -> Items:
    """A: TWIN-CORE CELL. A peanut of two equal lobes, each with its own glowing
    nucleus, its own feeler and its own pair of legs, cinched at the waist by a
    bright cleavage ring: a cell caught halfway through mitosis. The split pulls
    the lobes apart along that ring into two round halves."""
    pal = DIV
    if view == "front":
        cx, cy, by = 200.0, 258.0, 318.0
        far, near = legs_front(cx, by, 78, pal)
        body = []
        # the rear lobe's rim shows round the front lobe, and the ring between them
        body += cel(E(cx, cy - 4, 86, 70), pal["mem_sh"], pal["mem_dk"], None, s=6)
        body += [P(E(cx, cy - 4, 80, 64), "none", pal["ring"], 6), P(E(cx, cy - 4, 80, 64), "none", INK, 1.6)]
        front = cel(E(cx, cy + 2, 72, 62), pal["mem"], pal["mem_sh"], pal["mem_lt"], s=13, l=7,
                    items=nucleus(cx - 30, cy + 24, 15, pal, 1) + nucleus(cx + 30, cy + 24, 15, pal, 3))
        feel = []
        for side in (-1, 1):
            feel += [ln([(cx + side * 22, cy - 52), (cx + side * 34, cy - 84), (cx + side * 48, cy - 100)], INK, 10),
                     ln([(cx + side * 22, cy - 52), (cx + side * 34, cy - 84), (cx + side * 48, cy - 100)], pal["leg_sh"], 4.5),
                     disc(cx + side * 48, cy - 100, 7, pal["pupil"], sw=IN)]
        eyes = eye(cx, cy - 18, 30, 17, pal, look=(0, 2))
        mand = mandibles_front(cx, by - 8, 18, pal)
        return (layer("legs_far", far) + layer("legs_near", near) + layer("feelers", feel) + layer("body", body + front) + layer("eye", eyes)
                + layer("mandibles", mand))
    # side view
    split = (0.0, 9.0, 30.0)[t]
    tilt = (0.0, 4.0, 11.0)[t]
    rcx, fcx, cy = 148.0, 252.0, 268.0
    by = 318.0

    def lobe(cx, sign, core_xy, front: bool) -> Tuple[Items, Items]:
        far, near = legs_side(cx, by, 52, pal, which=("rear", "rmid") if not front else ("fmid", "front"))
        if front:
            mfar, mnear = mandibles_side((cx + 54, by - 12), pal, open_=0.2 * t)
        else:
            mfar, mnear = [], []
        # each lobe a near-round cell; at rest the halves overlap at the waist
        rx = 66.0 if t < 2 else 62.0
        d = E(cx, cy, rx, 58)
        feel_root = (cx + 18 * sign, cy - 52)
        feel_pts = [feel_root, (cx + 30 * sign, cy - 84), (cx + 50 * sign, cy - 98)]
        feel = [ln(feel_pts, INK, 10), ln(feel_pts, pal["leg_sh"], 4.5), disc(feel_pts[-1][0], feel_pts[-1][1], 7, pal["pupil"], sw=IN)]
        core = nucleus(core_xy[0], core_xy[1], 21, pal, 2 if front else 5)
        speck = [disc(cx - 30 * sign, cy - 22, 4, pal["mem_lt"], sw=0), disc(cx - 16 * sign, cy + 30, 3, pal["mem_sh"], sw=0)]
        body = cel(d, pal["mem"], pal["mem_sh"], pal["mem_lt"], s=13, l=7, items=speck + core)
        under = cel(poly([(cx - 52, by - 18), (cx + 52, by - 18), (cx + 40, by + 4), (cx - 40, by + 4)]), pal["slate"], pal["slate_sh"], None, s=4, sw=IN)
        items_far = far + mfar
        items_near = feel + near + under + body + mnear
        return items_far, items_near

    r_far, r_near = lobe(rcx, -1, (rcx - 4, cy + 12), front=False)
    f_far, f_near = lobe(fcx, 1, (fcx - 16, cy + 14), front=True)
    eye_items = eye(fcx + 40, cy - 20, 18, 14, pal, look=(5, 1), rot=-8)
    r_eye: Items = []
    rear_tf = about(rcx, GROUND, rot=-tilt, dx=-split)
    front_tf = about(fcx, GROUND, rot=tilt, dx=split)
    out: Items = []
    out += grp(r_far, rear_tf) + grp(f_far, front_tf)
    out += layer("rear_lobe", grp(r_near + r_eye, rear_tf))
    # the waist: a cleavage ring cinching the two lobes (t0), drawn hot (t1),
    # then a membrane strand stretched between the halves (t2)
    wx = (rcx + fcx) / 2
    if t < 2:
        hot = t == 1
        ring_w = 13.0 if not hot else 9.0
        band = E(wx, cy, ring_w, 50 - 4 * t)
        out += layer("cleavage_ring", cel(band, pal["ring_hot"] if hot else pal["ring"], pal["mem_lt"], None, s=3, sw=OUT)
                     + ([ln([(wx - 4, cy - 62), (wx - 8, cy - 76)], pal["ring"], 4), ln([(wx + 4, cy - 62), (wx + 10, cy - 74)], pal["ring"], 4),
                         ln([(wx, cy + 56), (wx + 2, cy + 70)], pal["ring"], 4)] if hot else []))
    else:
        strand = sm([(wx - 34, cy - 12), (wx, cy - 5), (wx + 34, cy - 12), (wx + 34, cy + 14), (wx, cy + 6), (wx - 34, cy + 14)])
        out += layer("strand", cel(strand, pal["ring"], pal["mem_lt"], None, s=3, sw=IN + 1))
        out += [ln([(wx - 10, cy - 36), (wx - 16, cy - 50)], pal["ring"], 4), ln([(wx + 8, cy - 38), (wx + 16, cy - 52)], pal["ring"], 4),
                ln([(wx, cy + 36), (wx + 4, cy + 52)], pal["ring"], 4)]
    out += layer("front_lobe", grp(f_near + eye_items, front_tf))
    return out


def div_b(view: str, t: int = 0) -> Items:
    """B: BACK-TO-BACK. Two half-mites welded rear to rear by a bolted collar,
    each with its own face, mandibles and four legs, looking opposite ways. It
    walks with the front one; when it dies the collar lets go and each half
    scuttles off its own way -- exactly where the two slugs land."""
    pal = dict(DIV, shell="#8d7bc4", shell_sh="#64559a", shell_lt="#b6a7e6", band="#5fb8a4", band_sh="#3c8a7b")
    if view == "front":
        cx, cy, by = 200.0, 250.0, 316.0
        far, near = legs_front(cx, by, 76, pal)
        collar = cel(E(cx, cy + 4, 92, 74), pal["slate"], pal["slate_sh"], pal["slate_lt"], s=6,
                     items=[disc(cx - 84, cy + 4, 6, pal["leg_lt"], sw=IN), disc(cx + 84, cy + 4, 6, pal["leg_lt"], sw=IN),
                            disc(cx, cy - 66, 6, pal["leg_lt"], sw=IN)])
        dome = sm([(cx - 74, cy + 30), (cx - 70, cy - 20), (cx - 40, cy - 60), (cx, cy - 68), (cx + 40, cy - 60), (cx + 70, cy - 20),
                   (cx + 74, cy + 30), (cx + 50, cy + 62), (cx, cy + 68), (cx - 50, cy + 62)])
        stripe = [P(poly([(cx - 14, cy - 80), (cx + 14, cy - 80), (cx + 14, cy + 80), (cx - 14, cy + 80)]), pal["band"]),
                  P(poly([(cx - 14, cy - 80), (cx - 8, cy - 80), (cx - 8, cy + 80), (cx - 14, cy + 80)]), pal["band_sh"])]
        body = cel(dome, pal["shell"], pal["shell_sh"], pal["shell_lt"], s=13, l=7, items=stripe)
        eyes = eye(cx, cy - 4, 32, 22, pal, look=(0, 2))
        mand = mandibles_front(cx, by - 4, 18, pal)
        return (layer("legs_far", far) + layer("legs_near", near) + layer("collar", collar) + layer("body", body) + layer("eye", eyes)
                + layer("mandibles", mand))

    sep = (0.0, 6.0, 30.0)[t]
    tilt = (0.0, 3.0, 9.0)[t]
    cy, by = 262.0, 316.0

    def half() -> Tuple[Items, Items]:
        """The front half, facing right, its flat back on x = 200."""
        far, near = legs_side(250, by, 58, pal, which=("rmid", "front"))  # one leg under the seam, one out front: each half stands alone
        mfar, mnear = mandibles_side((300, by - 14), pal, open_=0.15 * t)
        dome = sm([(200, cy - 64, True), (240, cy - 66), (282, cy - 46), (306, cy - 6), (304, cy + 30), (282, cy + 52),
                   (240, cy + 58), (200, cy + 58, True)])
        stripe = [P(poly([(222, cy - 80), (240, cy - 80), (240, cy + 80), (222, cy + 80)]), pal["band"]),
                  P(poly([(222, cy - 80), (227, cy - 80), (227, cy + 80), (222, cy + 80)]), pal["band_sh"])]
        speck = [disc(268, cy + 32, 4, pal["shell_sh"], sw=0)]
        body = cel(dome, pal["shell"], pal["shell_sh"], pal["shell_lt"], s=13, l=7, items=stripe + speck)
        belly = cel(poly([(200, by - 22), (290, by - 22), (276, by + 2), (200, by + 2)]), pal["slate"], pal["slate_sh"], None, s=4, sw=IN)
        ey = eye(276, cy - 16, 20, 16, pal, look=(5, 1), rot=-6)
        return far + mfar, near + belly + body + ey + mnear

    front_far, front_near = half()
    _MIRROR[0] = True
    back_far, back_near = half()
    _MIRROR[0] = False
    rear_tf = mirror_tf() + " " + about(200, GROUND, rot=tilt, dx=sep)  # (inside the mirror: moving +x moves it left)
    front_tf = about(200, GROUND, rot=tilt, dx=sep)
    out = grp(back_far, rear_tf) + grp(front_far, front_tf)
    out += layer("rear_half", grp(back_near, rear_tf))
    if t < 2:
        # the collar: a bolted clamp ring over the seam, its bolts springing at t1
        collar = cel(sm([(190, cy - 74), (210, cy - 74), (214, cy), (210, cy + 64), (190, cy + 64), (186, cy)]),
                     pal["slate"], pal["slate_sh"], pal["slate_lt"], s=4)
        bolts = []
        for yy in (cy - 50, cy - 6, cy + 38):
            if t == 0:
                bolts.append(disc(200, yy, 6, pal["leg_lt"], sw=IN))
            else:
                bolts.append(disc(200 + (yy - cy) * 0.1, yy - 10, 6, pal["leg_lt"], sw=IN))
        if t == 1:
            bolts += [ln([(200, cy - 92), (196, cy - 104)], pal["ring"], 4), ln([(214, cy - 84), (226, cy - 94)], pal["ring"], 4),
                      ln([(186, cy - 84), (174, cy - 94)], pal["ring"], 4)]
        out += layer("collar", collar + bolts)
    else:
        # the collar has fallen; two clean backs and a few sparks between them
        out += [ln([(200, cy - 30), (198, cy - 46)], pal["ring"], 4), ln([(194, cy + 6), (180, cy + 2)], pal["ring"], 4),
                ln([(206, cy + 6), (220, cy + 2)], pal["ring"], 4)]
        out += layer("collar", grp(cel(sm([(190, cy - 50), (210, cy - 50), (214, cy), (210, cy + 40), (190, cy + 40), (186, cy)]),
                                       pal["slate"], pal["slate_sh"], pal["slate_lt"], s=4), about(200, cy, k=0.7, rot=-60, dy=-120)))
    out += layer("front_half", grp(front_near, front_tf))
    return out


def puppy_larva(cx: float, cy: float, k: float, flip=False, awake=False) -> Items:
    """A curled Puppy Slug inside a brood bubble: a teal C of body, a brown
    pup's head with a floppy ear and a black nose (the slug the mite releases)."""
    teal, teal_sh, teal_lt = "#4f9f93", "#356f68", "#7ccbbd"
    dog, dog_sh, ear = "#c88a4e", "#9a6234", "#6b3f22"
    s = -1 if flip else 1
    body = sm([(cx - 22 * k * s, cy + 10 * k), (cx - 26 * k * s, cy - 8 * k), (cx - 10 * k * s, cy - 22 * k),
               (cx + 12 * k * s, cy - 20 * k), (cx + 16 * k * s, cy - 6 * k), (cx + 4 * k * s, cy + 2 * k),
               (cx - 8 * k * s, cy + 2 * k), (cx - 6 * k * s, cy + 16 * k), (cx + 12 * k * s, cy + 20 * k), (cx - 10 * k * s, cy + 24 * k)])
    out = cel(body, teal, teal_sh, teal_lt, s=4, l=3, sw=IN, items=[disc(cx - 14 * k * s, cy - 8 * k, 2.4 * k, teal_lt, sw=0)])
    hx, hy = cx + 12 * k * s, cy + 12 * k
    head = sm([(hx - 10 * k * s, hy - 6 * k), (hx + 2 * k * s, hy - 12 * k), (hx + 14 * k * s, hy - 6 * k),
               (hx + 22 * k * s, hy + 2 * k), (hx + 14 * k * s, hy + 10 * k), (hx - 4 * k * s, hy + 10 * k)])
    out += cel(head, dog, dog_sh, None, s=3, sw=IN)
    out.append(P(sm([(hx - 4 * k * s, hy - 8 * k), (hx + 4 * k * s, hy - 6 * k), (hx + 2 * k * s, hy + 8 * k), (hx - 6 * k * s, hy + 4 * k)]), ear, INK, 2.2))
    out.append(disc(hx + 21 * k * s, hy + 1 * k, 3.2 * k, INK, sw=0))
    if awake:
        out.append(disc(hx + 9 * k * s, hy - 3 * k, 2.6 * k, INK, sw=0))
    else:
        out.append(ln([(hx + 6 * k * s, hy - 3 * k), (hx + 12 * k * s, hy - 2 * k)], INK, 2.2))
    return out


def div_c(view: str, t: int = 0) -> Items:
    """C: BROOD CARRIER. A low slate mite carrying a twin brood sac on its back:
    two glass bubbles, one curled Puppy Slug asleep in each, joined by a brass
    clasp. It IS the delivery of the two slugs it releases; the split cracks the
    clasp and the bubbles roll apart, the pups waking."""
    pal = dict(DIV, glass="#cfeff0", glass_sh="#9fcfd3", glass_lt="#f4ffff", fluid="#9ee0d2")
    if view == "front":
        cx, by = 200.0, 318.0
        far, near = legs_front(cx, by, 74, pal)
        chassis = cel(sm([(cx - 76, by - 6), (cx - 70, by - 46), (cx, by - 58), (cx + 70, by - 46), (cx + 76, by - 6), (cx, by + 6)]),
                      pal["slate"], pal["slate_sh"], pal["slate_lt"], s=8)
        bub = cel(E(cx, 214, 64, 58), pal["glass"], pal["glass_sh"], pal["glass_lt"], s=10, l=6,
                  items=[P(E(cx, 238, 60, 40), pal["fluid"])] + puppy_larva(cx, 222, 1.25) +
                  [P(sm([(cx + 26, 172), (cx + 44, 184), (cx + 50, 204)], closed=False), "none", "#ffffff", 5)])
        clasp = cel(poly([(cx - 70, 262), (cx + 70, 262), (cx + 66, 276), (cx - 66, 276)]), pal["core_sh"], "#8a7430", pal["core"], s=3, sw=IN)
        eyes = eye(cx, by - 30, 28, 15, pal, look=(0, 2))
        mand = mandibles_front(cx, by - 4, 18, pal)
        return (layer("legs_far", far) + layer("legs_near", near) + layer("brood_sac", bub) + layer("chassis", chassis + clasp) + layer("eye", eyes)
                + layer("mandibles", mand))

    by = 318.0
    far, near = legs_side(206, by, 76, pal)
    mfar, mnear = mandibles_side((314, by - 10), pal, open_=0.1 * t)
    chassis = cel(sm([(112, by - 6), (118, by - 36), (170, by - 50), (262, by - 52), (292, by - 70), (322, by - 60), (330, by - 30), (314, by - 4), (200, by + 8)]),
                  pal["slate"], pal["slate_sh"], pal["slate_lt"], s=9, l=5,
                  items=[ln([(150, by - 40), (150, by - 4)], pal["slate_sh"], 3), ln([(244, by - 44), (244, by - 4)], pal["slate_sh"], 3)])
    ey = eye(306, by - 44, 16, 13, pal, look=(5, 1), rot=-8)
    sep = (0.0, 4.0, 28.0)[t]
    roll = (0.0, 4.0, 16.0)[t]
    bubbles = []
    for bx, sign in ((158.0, -1), (244.0, 1)):
        cyb = 222.0 - (0.0, 2.0, 6.0)[t]
        bxx = bx + sign * sep
        d = sm([(bxx, cyb - 50), (bxx + 32, cyb - 34), (bxx + 42, cyb + 2), (bxx + 34, cyb + 36), (bxx, cyb + 48),
                (bxx - 34, cyb + 36), (bxx - 42, cyb + 2), (bxx - 32, cyb - 34)])
        crack = []
        if t >= 1:
            ex = bxx - sign * 40
            crack = [ln([(ex, cyb - 30), (ex + sign * 8, cyb - 14), (ex - sign * 2, cyb), (ex + sign * 10, cyb + 14)], INK, 2.6)]
        fl = cyb - 8
        inside = [P(sm([(bxx - 60, fl, True), (bxx - 20, fl - 5), (bxx + 20, fl + 3), (bxx + 60, fl, True), (bxx + 60, cyb + 60, True),
                        (bxx - 60, cyb + 60, True)]), pal["fluid"]),
                  ln([(bxx - 60, fl), (bxx - 20, fl - 5), (bxx + 20, fl + 3), (bxx + 60, fl)], pal["glass_lt"], 3)] + grp(puppy_larva(bxx, cyb + 2, 1.0, flip=sign < 0, awake=t == 2),
                                                                     about(bxx, cyb, rot=sign * roll))
        glint = [P(sm([(bxx + 8, cyb - 40), (bxx + 24, cyb - 30), (bxx + 32, cyb - 14)], closed=False), "none", "#ffffff", 5)]
        bubbles += grp(cel(d, pal["glass"], pal["glass_sh"], pal["glass_lt"], s=9, l=5, items=inside + glint + crack),
                       about(bxx, cyb + 48, rot=sign * roll * 0.6))
    coupler = poly([(180, 214), (222, 214), (222, 240), (180, 240)])
    if t < 2:
        clasp = cel(coupler, pal["core_sh"], "#8a7430", pal["core"], s=3, sw=IN,
                    items=[ln([(192, 212), (192, 242)], "#8a7430", 3), ln([(210, 212), (210, 242)], "#8a7430", 3)])
        if t == 1:
            clasp += [ln([(201, 178), (199, 166)], pal["ring"], 4), ln([(216, 186), (226, 178)], pal["ring"], 4),
                      ln([(186, 186), (176, 178)], pal["ring"], 4)]
    else:
        clasp = grp(cel(coupler, pal["core_sh"], "#8a7430", pal["core"], s=3, sw=IN), about(201, 227, rot=70, dy=-70))
    saddle = cel(sm([(118, 268), (284, 268), (276, 284), (126, 284)]), pal["slate_sh"], "#262b33", None, s=3, sw=IN)
    return (layer("legs_far", far + mfar) + layer("legs_near", near) + layer("chassis", chassis) + layer("brood_sac", bubbles + saddle) + layer("clasp", clasp)
            + layer("mandibles", mnear) + layer("eye", ey))


# ---------------------------------------------------------------------------------------------
# EXPLODING MITE
# ---------------------------------------------------------------------------------------------

def exp_a(view: str, t: int = 0) -> Items:
    """A: BOMB. A round gunmetal pressure shell on short legs, a hazard-striped
    belt, a pressure gauge with its needle in the red, and a lit fuse curling
    off the top. The wind-up burns the fuse down to the cap while the shell
    swells, the belt strains and the seams glow."""
    pal = EXP
    swell = (1.0, 1.08, 1.17)[t]
    if view == "front":
        cx, cy, by = 200.0, 256.0, 322.0
        far, near = legs_front(cx, by, 70, pal)
        d = E(cx, cy, 78, 76)
        band = [P(poly([(cx - 90, cy + 2), (cx + 90, cy + 2), (cx + 90, cy + 30), (cx - 90, cy + 30)]), pal["haz"]),
                *clip(poly([(cx - 90, cy + 2), (cx + 90, cy + 2), (cx + 90, cy + 30), (cx - 90, cy + 30)]),
                      stripes(cx - 90, cy + 2, cx + 90, cy + 30, 22, 11, INK)),
                ln([(cx - 90, cy + 2), (cx + 90, cy + 2)], INK, IN), ln([(cx - 90, cy + 30), (cx + 90, cy + 30)], INK, IN)]
        body = cel(d, pal["steel"], pal["steel_sh"], pal["steel_lt"], s=13, l=7, items=band)
        cap = cel(poly([(cx - 18, cy - 70), (cx + 18, cy - 70), (cx + 15, cy - 88), (cx - 15, cy - 88)]), pal["brass"], pal["brass_sh"], pal["brass_lt"], s=3, sw=IN)
        wick = [ln([(cx, cy - 88), (cx + 6, cy - 110), (cx - 8, cy - 128), (cx - 2, cy - 142)], INK, 9),
                ln([(cx, cy - 88), (cx + 6, cy - 110), (cx - 8, cy - 128), (cx - 2, cy - 142)], "#b89a6a", 4)]
        sp = spark(cx - 2, cy - 146, 18, pal)
        mand = mandibles_front(cx, by - 6, 16, pal)
        return (layer("legs_far", far) + layer("legs_near", near) + layer("fuse", wick + sp) + layer("body", body + cap) + layer("eye", eye(cx, cy - 22, 30, 22, pal, look=(0, 3)))
                + layer("brow", cel(poly([(cx - 42, cy - 54), (cx, cy - 36), (cx + 42, cy - 54), (cx + 42, cy - 42), (cx, cy - 24), (cx - 42, cy - 42)]),
                                    pal["brow"], pal["brow_sh"], None, s=3, sw=IN))
                + layer("mandibles", mand))

    cx, cy, by = 196.0, 262.0, 330.0
    far, near = legs_side(cx, by, 70, pal, lift=(0, 4, 8)[t])
    mfar, mnear = mandibles_side((cx + 70, by - 18), pal, open_=0.3 * t)
    r = 78.0
    d = E(cx, cy, r, r - 2)
    # the belt, sagging a little with the sphere's curve
    b_top = sm([(cx - r - 8, cy + 4), (cx, cy + 14), (cx + r + 8, cy + 4)], closed=False)
    belt_d = sm([(cx - r - 10, cy + 2, True), (cx, cy + 12), (cx + r + 10, cy + 2, True), (cx + r + 10, cy + 30, True), (cx, cy + 40),
                 (cx - r - 10, cy + 30, True)])
    rivets = [disc(cx + x, cy + 26 + 8 * (1 - (x / r) ** 2), 3.2, pal["haz_sh"], sw=0) for x in (-56, -28, 0, 28, 56)]
    belt = [P(belt_d, pal["haz"]), *clip(belt_d, stripes(cx - r - 10, cy - 4, cx + r + 10, cy + 44, 24, 12, INK, ang=35)),
            P(belt_d, "none", INK, IN)]
    glow = []
    if t >= 1:
        # seams glowing hot along the plate lines
        hot = pal["hot"] if t == 1 else pal["white_hot"]
        glow += [ln([(cx - 20, cy - r + 4), (cx - 30, cy - 30), (cx - 26, cy + 2)], INK, 8), ln([(cx - 20, cy - r + 4), (cx - 30, cy - 30), (cx - 26, cy + 2)], hot, 4),
                 ln([(cx + 40, cy + 44), (cx + 36, cy + 70)], INK, 8), ln([(cx + 40, cy + 44), (cx + 36, cy + 70)], hot, 4)]
        if t == 2:
            glow += [ln([(cx + 30, cy - r + 10), (cx + 46, cy - 30)], INK, 8), ln([(cx + 30, cy - r + 10), (cx + 46, cy - 30)], hot, 4),
                     ln([(cx - 60, cy + 44), (cx - 40, cy + 60)], INK, 8), ln([(cx - 60, cy + 44), (cx - 40, cy + 60)], hot, 4)]
    plates = [ln([(cx - 20, cy - r + 4), (cx - 30, cy - 30), (cx - 26, cy + 2)], pal["steel_sh"], 3) if t == 0 else "",
              disc(cx - 40, cy - 40, 3.5, pal["steel_lt"], sw=0), disc(cx + 10, cy - 60, 3.5, pal["steel_lt"], sw=0)]
    body_fill = pal["steel"] if t < 2 else "#5a3e3a"
    body = cel(d, body_fill, pal["steel_sh"], pal["steel_lt"], s=14, l=7, items=plates + belt + rivets + glow)
    # the fuse: a brass cap at the top-back and a wick burning down
    cap_c = (cx - 18, cy - r + 2)
    cap = cel(poly([(cap_c[0] - 18, cap_c[1] + 4), (cap_c[0] + 16, cap_c[1] - 2), (cap_c[0] + 12, cap_c[1] - 20), (cap_c[0] - 16, cap_c[1] - 15)]),
              pal["brass"], pal["brass_sh"], pal["brass_lt"], s=3, sw=IN)
    full = [(cap_c[0] - 2, cap_c[1] - 17), (cap_c[0] - 14, cap_c[1] - 42), (cap_c[0] - 42, cap_c[1] - 58), (cap_c[0] - 54, cap_c[1] - 84)]
    wick_pts = full[: (4, 3, 2)[t]]
    if len(wick_pts) >= 2:
        wick = [ln(wick_pts, INK, 9), ln(wick_pts, "#b89a6a", 4)]
    else:
        wick = []
    sp_at = wick_pts[-1]
    sp = spark(sp_at[0], sp_at[1], (18, 22, 28)[t], pal, rot=t * 11)
    ey = eye(cx + 48, cy - 22, 19, 17, pal, look=(5, 1), rot=-6, mood="wide" if t == 2 else "calm", pupil_k=(1.0, 0.8, 1.15)[t])
    brow = cel(poly([(cx + 24, cy - 48), (cx + 74, cy - 30), (cx + 76, cy - 42), (cx + 28, cy - 60)]), pal["brow"], pal["brow_sh"], None, s=3, sw=IN)
    # a pressure valve on the back: a brass stub and its hand wheel, blowing
    # off a puff once the pressure climbs
    vx, vy = cx - r + 2, cy - 26
    valve = cel(poly([(vx + 8, vy - 6), (vx - 14, vy - 8), (vx - 14, vy + 6), (vx + 8, vy + 8)]), pal["brass"], pal["brass_sh"], pal["brass_lt"], s=2, sw=IN)
    valve += cel(E(vx - 18, vy - 1, 5, 13), pal["red"], pal["red_sh"], pal["red_lt"], s=2, l=2, sw=IN)
    if t >= 1:
        for i, (px_, py_, pr) in enumerate(((vx - 34, vy - 10, 8), (vx - 46, vy - 24, 10), (vx - 54, vy - 42, 12))[: (2, 3)[t - 1]]):
            valve.append(disc(px_, py_, pr, "#eef1f4", sw=IN))
    tf = about(cx, by, k=swell)
    return (layer("legs_far", far + mfar) + layer("legs_near", near)
            + layer("body", grp(valve + body + cap + ey + brow, tf))
            + layer("fuse", grp(wick + sp, tf))
            + layer("mandibles", mnear))


def exp_b(view: str, t: int = 0) -> Items:
    """B: FLASK. The body is a round-bottomed glass flask of glowing orange brew,
    stoppered with a cork under a wire cage (the champagne cork: pressure you
    can see), carried in a steel cradle that holds the legs and the face. The
    wind-up boils the brew, rises the cork against the wire and cracks the
    glass."""
    pal = dict(EXP, glass="#d9eef2", glass_sh="#a8c8d0", glass_lt="#f6ffff", brew="#ff8a2a", brew_sh="#e0561c", brew_lt="#ffc25a",
               cork="#b8865a", cork_sh="#8a5e3a", cork_lt="#d8a878", wire="#c9ced6")
    if view == "front":
        cx, by = 200.0, 324.0
        far, near = legs_front(cx, by, 72, pal)
        flask = sm([(cx - 18, 128, True), (cx + 18, 128, True), (cx + 18, 168), (cx + 64, 200), (cx + 78, 246), (cx + 62, 292),
                    (cx, 312), (cx - 62, 292), (cx - 78, 246), (cx - 64, 200), (cx - 18, 168)])
        brew_d = sm([(cx - 76, 208, True), (cx - 40, 202), (cx, 210), (cx + 40, 202), (cx + 76, 208, True), (cx + 70, 290), (cx, 316), (cx - 70, 290)])
        inside = [*cel(brew_d, pal["brew"], pal["brew_sh"], pal["brew_lt"], s=10, l=5, sw=0),
                  ln([(cx - 76, 208), (cx - 40, 202), (cx, 210), (cx + 40, 202), (cx + 76, 208)], pal["brew_lt"], 4),
                  disc(cx - 20, 262, 8, pal["brew_lt"], sw=2.4), disc(cx + 18, 280, 5, pal["brew_lt"], sw=2.4), disc(cx + 30, 246, 6, pal["brew_lt"], sw=2.4),
                  P(sm([(cx + 30, 184), (cx + 54, 204), (cx + 64, 232)], closed=False), "none", "#ffffff", 6)]
        glass = cel(flask, pal["glass"], pal["glass_sh"], pal["glass_lt"], s=8, l=5, items=inside)
        cork = cel(poly([(cx - 20, 132), (cx + 20, 132), (cx + 24, 104), (cx - 24, 104)]), pal["cork"], pal["cork_sh"], pal["cork_lt"], s=4, sw=IN)
        cage = [ln([(cx - 24, 104), (cx, 96), (cx + 24, 104)], INK, 7), ln([(cx - 24, 104), (cx, 96), (cx + 24, 104)], pal["wire"], 3),
                ln([(cx - 22, 142), (cx - 24, 104)], pal["wire"], 3), ln([(cx + 22, 142), (cx + 24, 104)], pal["wire"], 3),
                P(poly([(cx - 24, 138), (cx + 24, 138), (cx + 24, 146), (cx - 24, 146)]), pal["wire"], INK, 2.6)]
        cradle = cel(sm([(cx - 84, 262), (cx + 84, 262), (cx + 66, 322), (cx, 330), (cx - 66, 322)]), pal["steel"], pal["steel_sh"], pal["steel_lt"], s=8,
                     items=stripes(cx - 90, 262, cx + 90, 278, 22, 11, pal["haz"]) + [ln([(cx - 90, 278), (cx + 90, 278)], INK, IN)])
        eyes = eye(cx, 298, 26, 14, pal, look=(0, 2))
        mand = mandibles_front(cx, by - 2, 16, pal)
        return layer("legs_far", far) + layer("legs_near", near) + layer("flask", glass + cage + cork) + layer("cradle", cradle + eyes) + layer("mandibles", mand)

    cx, by = 196.0, 326.0
    far, near = legs_side(cx, by, 70, pal, lift=(0, 3, 6)[t])
    mfar, mnear = mandibles_side((cx + 96, by - 16), pal, open_=0.3 * t)
    fcx, fcy = cx - 6, 238.0
    wob = (0.0, 6.0, 12.0)[t]
    flask = sm([(fcx - 16, 132, True), (fcx + 16, 132, True), (fcx + 16, 170), (fcx + 60, 198), (fcx + 76, 242), (fcx + 60, 290),
                (fcx, 310), (fcx - 60, 290), (fcx - 76, 242), (fcx - 60, 198), (fcx - 16, 170)])
    level = 206.0 - (0, 8, 18)[t]
    surf = [(fcx - 76, level + 4, True), (fcx - 40, level - wob), (fcx, level + wob * 0.6), (fcx + 40, level - wob * 0.8), (fcx + 76, level + 4, True)]
    brew_d = sm(surf + [(fcx + 70, 292), (fcx, 316), (fcx - 70, 292)])
    bubbles = [disc(fcx - 24, 266, 8, pal["brew_lt"], sw=2.4), disc(fcx + 20, 284, 5, pal["brew_lt"], sw=2.4), disc(fcx + 32, 250, 6, pal["brew_lt"], sw=2.4)]
    if t >= 1:
        bubbles += [disc(fcx - 6, 244, 7, pal["brew_lt"], sw=2.4), disc(fcx - 44, 250, 5, pal["brew_lt"], sw=2.4)]
    if t == 2:
        bubbles += [disc(fcx + 10, 196, 6, pal["brew_lt"], sw=2.4), disc(fcx - 10, 176, 5, pal["brew_lt"], sw=2.4), disc(fcx + 4, 150, 4, pal["brew_lt"], sw=2.4)]
    brew_col = (pal["brew"], pal["brew"], pal["brew_lt"])[t]
    inside = [*cel(brew_d, brew_col, pal["brew_sh"], pal["brew_lt"] if t < 2 else pal["white_hot"], s=10, l=5, sw=0),
              ln([p[:2] for p in surf], pal["brew_lt"] if t < 2 else pal["white_hot"], 4), *bubbles,
              P(sm([(fcx + 26, 184), (fcx + 50, 202), (fcx + 62, 232)], closed=False), "none", "#ffffff", 6)]
    if t >= 1:
        cr = [(fcx - 50, 206), (fcx - 36, 226), (fcx - 46, 240), (fcx - 30, 262)]
        inside += [ln(cr[: (3, 4)[t - 1]], INK, 2.8)]
        if t == 2:
            inside += [ln([(fcx + 40, 286), (fcx + 26, 270), (fcx + 34, 256)], INK, 2.8)]
    glass = cel(flask, pal["glass"], pal["glass_sh"], pal["glass_lt"], s=8, l=5, items=inside)
    rise = (0.0, 8.0, 18.0)[t]
    cork = cel(poly([(fcx - 18, 136 - rise), (fcx + 18, 136 - rise), (fcx + 22, 106 - rise), (fcx - 22, 106 - rise)]), pal["cork"], pal["cork_sh"], pal["cork_lt"], s=4, sw=IN)
    top = 98 - rise
    cage = [ln([(fcx - 22, 106 - rise), (fcx, top), (fcx + 22, 106 - rise)], INK, 7), ln([(fcx - 22, 106 - rise), (fcx, top), (fcx + 22, 106 - rise)], pal["wire"], 3),
            ln([(fcx - 20, 146), (fcx - 22, 106 - rise)], INK, 6), ln([(fcx - 20, 146), (fcx - 22, 106 - rise)], pal["wire"], 2.6),
            ln([(fcx + 20, 146), (fcx + 22, 106 - rise)], INK, 6), ln([(fcx + 20, 146), (fcx + 22, 106 - rise)], pal["wire"], 2.6),
            P(poly([(fcx - 22, 142), (fcx + 22, 142), (fcx + 22, 150), (fcx - 22, 150)]), pal["wire"], INK, 2.6)]
    if t >= 1:
        cage += [ln([(fcx - 30, 124 - rise), (fcx - 40, 116 - rise)], pal["brew_lt"], 4), ln([(fcx + 30, 124 - rise), (fcx + 40, 116 - rise)], pal["brew_lt"], 4)]
    cradle = cel(sm([(cx - 92, 266), (cx + 66, 266), (cx + 94, 284), (cx + 86, 318), (cx, 330), (cx - 80, 320)]), pal["steel"], pal["steel_sh"], pal["steel_lt"], s=8,
                 items=[*stripes(cx - 96, 268, cx + 100, 282, 22, 11, pal["haz"]), ln([(cx - 96, 282), (cx + 100, 282)], INK, IN)])
    head = cel(sm([(cx + 56, 268), (cx + 92, 262), (cx + 114, 280), (cx + 110, 306), (cx + 80, 314), (cx + 58, 300)]),
               pal["steel"], pal["steel_sh"], pal["steel_lt"], s=6, l=4)
    ey = eye(cx + 92, 287, 15, 12, pal, look=(4, 1), rot=-6, mood="wide" if t == 2 else "calm")
    shake = about(fcx, 300, rot=(0, -2.5, 3.5)[t])
    return (layer("legs_far", far + mfar) + layer("legs_near", near) + layer("flask", grp(glass + cage + cork, shake)) + layer("cradle", cradle)
            + layer("head", head + ey) + layer("mandibles", mnear))


def exp_c(view: str, t: int = 0) -> Items:
    """C: SWOLLEN CELL. A red power-cell canister with steel end caps, already
    bulging at the middle, a warning beacon on top and hazard-striped caps --
    the swollen battery everyone knows not to poke. The wind-up swells it
    further, splits its seams on a white-hot core and spins the beacon up."""
    pal = EXP
    if view == "front":
        cx, cy, by = 200.0, 250.0, 318.0
        far, near = legs_front(cx, by, 72, pal)
        cap = cel(E(cx, cy, 74, 70), pal["steel"], pal["steel_sh"], pal["steel_lt"], s=10, l=6,
                  items=[*clip(E(cx, cy, 74, 70), [P(E(cx, cy, 74, 70), "none", pal["haz"], 18), *[]]),
                         P(E(cx, cy, 64, 60), "none", INK, IN), P(E(cx, cy, 82, 78), "none", INK, IN)])
        # hazard ring: yellow with black ticks
        ticks = []
        for i in range(12):
            a = math.radians(i * 30 + 15)
            ticks.append(ln([(cx + math.cos(a) * 64, cy + math.sin(a) * 60), (cx + math.cos(a) * 74, cy + math.sin(a) * 70)], INK, 7))
        face = cel(E(cx, cy, 62, 58), pal["red"], pal["red_sh"], pal["red_lt"], s=10, l=6)
        beacon = cel(sm([(cx - 18, cy - 68, True), (cx - 16, cy - 88), (cx, cy - 98), (cx + 16, cy - 88), (cx + 18, cy - 68, True)]),
                     pal["red_lt"], pal["red"], "#ffd0b8", s=4, sw=IN)
        base = cel(poly([(cx - 24, cy - 62), (cx + 24, cy - 62), (cx + 22, cy - 72), (cx - 22, cy - 72)]), pal["steel"], pal["steel_sh"], None, s=2, sw=IN)
        eyes = eye(cx, cy + 4, 32, 22, pal, look=(0, 2))
        mand = mandibles_front(cx, by - 4, 16, pal)
        return (layer("legs_far", far) + layer("legs_near", near) + layer("body", cap + ticks + face) + layer("beacon", beacon + base) + layer("eye", eyes)
                + layer("mandibles", mand))

    cx, cy, by = 198.0, 262.0, 326.0
    far, near = legs_side(cx, by, 70, pal, lift=(0, 4, 8)[t])
    mfar, mnear = mandibles_side((cx + 84, by - 16), pal, open_=0.3 * t)
    bulge = (26.0, 36.0, 48.0)[t]
    L, R, T, B = cx - 86, cx + 86, cy - 34, cy + 36
    # a canister lying on its side, its wall bowed out between the end caps
    can = sm([(L + 12, T, True), (cx - 40, T - bulge * 0.8), (cx, T - bulge), (cx + 40, T - bulge * 0.8), (R - 12, T, True),
              (R - 12, B, True), (cx + 40, B + bulge * 0.55), (cx, B + bulge * 0.65), (cx - 40, B + bulge * 0.55), (L + 12, B, True)])
    seam: Items = []
    if t >= 1:
        # the wall splits along its length on a hot core
        hot = pal["hot"] if t == 1 else pal["white_hot"]
        w = (0, 5, 11)[t]
        zig = [(L + 26, cy - 4), (cx - 52, cy + 4), (cx - 26, cy - 6), (cx, cy + 5), (cx + 26, cy - 6), (cx + 52, cy + 4), (R - 26, cy - 4)]
        top = [(x, y - w * (1 - abs(x - cx) / 90)) for x, y in zig]
        bot = [(x, y + w * (1 - abs(x - cx) / 90)) for x, y in reversed(zig)]
        seam = [P(poly(top + bot), hot, INK, IN)]
        if t == 2:
            seam += [ln([(cx - 30, T - bulge + 6), (cx - 24, cy - 26), (cx - 34, cy - 10)], INK, 7),
                     ln([(cx - 30, T - bulge + 6), (cx - 24, cy - 26), (cx - 34, cy - 10)], hot, 3),
                     ln([(cx + 34, B + bulge * 0.5 - 4), (cx + 26, cy + 22)], INK, 7), ln([(cx + 34, B + bulge * 0.5 - 4), (cx + 26, cy + 22)], hot, 3)]
    ribs = [ln([(cx - 46, T - bulge * 0.7), (cx - 50, cy), (cx - 46, B + bulge * 0.45)], pal["red_sh"], 3),
            ln([(cx + 46, T - bulge * 0.7), (cx + 50, cy), (cx + 46, B + bulge * 0.45)], pal["red_sh"], 3)]
    body = cel(can, pal["red"], pal["red_sh"], pal["red_lt"], s=14, l=8, items=ribs + seam)
    caps = []
    for x0, x1 in ((L - 6, L + 18), (R - 18, R + 6)):
        d = sm([(x0, T - 4, True), (x1, T - 6, True), (x1, B + 6, True), (x0, B + 4, True)], tension=0.4)
        caps += cel(d, pal["haz"], pal["haz_sh"], None, s=4,
                    items=clip(d, stripes(x0 - 4, T - 10, x1 + 4, B + 10, 26, 13, INK, ang=55)))
    term = cel(poly([(R + 4, cy - 12), (R + 16, cy - 10), (R + 16, cy + 10), (R + 4, cy + 12)]), pal["brass"], pal["brass_sh"], pal["brass_lt"], s=2, sw=IN)
    # the warning beacon: lit at t1/t2 with authored rays
    bx, byy = cx - 22, T - bulge * 0.9 + 6
    lit = t >= 1
    beacon = cel(sm([(bx - 20, byy, True), (bx - 18, byy - 28), (bx, byy - 40), (bx + 18, byy - 28), (bx + 20, byy, True)]),
                 pal["red_lt"] if lit else pal["red"], pal["red"] if lit else pal["red_sh"], "#ffe0c8" if lit else pal["red_lt"], s=4, sw=IN)
    beacon += cel(poly([(bx - 24, byy + 6), (bx + 24, byy + 6), (bx + 22, byy - 4), (bx - 22, byy - 4)]), pal["steel"], pal["steel_sh"], None, s=2, sw=IN)
    if lit:
        n = (3, 5)[t - 1]
        for i in range(n):
            a = math.radians(-90 + (i - (n - 1) / 2) * 32)
            r0, r1 = 40, 40 + (12, 20)[t - 1]
            seg = [(bx + math.cos(a) * r0, byy - 16 + math.sin(a) * r0), (bx + math.cos(a) * r1, byy - 16 + math.sin(a) * r1)]
            beacon += [ln(seg, INK, 8), ln(seg, pal["red_lt"], 4)]
    ey = eye(R - 34, cy - 12, 19, 16, pal, look=(5, 1), rot=-6, mood="wide" if t == 2 else "calm")
    tf = about(cx, by, kx=(1.0, 1.03, 1.06)[t], ky=1.0)
    return (layer("legs_far", far + mfar) + layer("legs_near", near) + layer("body", grp(body + caps + term, tf)) + layer("beacon", grp(beacon, tf))
            + layer("mandibles", mnear) + layer("eye", grp(ey, tf)))


# ---------------------------------------------------------------------------------------------
# looks, documents, CLI
# ---------------------------------------------------------------------------------------------

LOOKS: Dict[str, List[Tuple[str, str, Callable[[str, int], Items]]]] = {
    "dividing_mite": [
        ("A", "twin-core cell", div_a),
        ("B", "back-to-back", div_b),
        ("C", "brood carrier", div_c),
    ],
    "exploding_mite": [
        ("A", "bomb", exp_a),
        ("B", "pressure flask", exp_b),
        ("C", "swollen cell", exp_c),
    ],
}
#: What each strip's three frames show.
STRIP = {"dividing_mite": "the split", "exploding_mite": "the wind-up to the blast"}


def svg_text(mite: str, key: str, view: str, t: int = 0) -> str:
    look = next(l for l in LOOKS[mite] if l[0] == key)
    _N[0] = 0
    body = look[2](view, t)
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'data-character-design="{mite}-r1-{key.lower()}">',
           f"  <!-- CANDIDATE, NOT CAST: {mite.replace('_', ' ')}, look {key} ({look[1]}), {view}"
           + (f", strip frame {t}" if view == "strip" or t else "") + f"; the ground at y={GROUND:g}.",
           "       Drawn by scripts/svg_art/mites_art.py (2026-10-22). -->",
           f'  <g data-view="{view}">']
    out += ["    " + s for s in body if s]
    out += ["  </g>", "</svg>"]
    return "\n".join(out) + "\n"


def write_all(out: Path) -> List[Path]:
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for mite, looks in LOOKS.items():
        for key, _label, _fn in looks:
            stem = f"{mite}_{key.lower()}"
            for view in ("side", "front"):
                p = out / f"{stem}_{view}.svg"
                p.write_text(svg_text(mite, key, view), encoding="utf8")
                written.append(p)
            for t in range(3):
                p = out / f"{stem}_strip{t}.svg"
                p.write_text(svg_text(mite, key, "side", t), encoding="utf8")
                written.append(p)
    return written



# ---------------------------------------------------------------------------------------------
# THE CAST: look A of each mite as a rig-ready side view (2026-10-23)
# ---------------------------------------------------------------------------------------------
#
# Each part is a layer (``data-rig-part``) that turns about one joint of the
# ``rig-joints`` layer. ``scripts/build_mite_v2_rigs.py`` reads ``cast(name)``
# for the bones, the parts and the legs, and authors the rows. The drawing is
# the candidate's at rest (strip frame 0); what changes in a row is a part's
# turn, its place, or which of two drawings of it shows (an opacity channel).

ROOT = Path(__file__).resolve().parents[2]
CAST_NAMES = ("dividing_mite_v2", "exploding_mite_v2")
CAST_VIEW = {"dividing_mite_v2": "Dividing Mite v2 - Side Right", "exploding_mite_v2": "Exploding Mite v2 - Side Right"}
#: The rig frame's middle, in design units.
CAST_CX = 200.0
LEG_SPEC = {
    # position: hip (dx, dy), knee (dx, dy), foot dx -- dx in units of the body's half length s, dy from its underside
    "rear": ((-0.55, -30), (-1.42, -66), -1.72),
    "rmid": ((-0.30, -14), (-0.95, -34), -1.12),
    "fmid": ((0.30, -14), (0.95, -34), 1.12),
    "front": ((0.55, -30), (1.42, -68), 1.72),
}


def leg_points(cx: float, by: float, s: float, which, lift=0.0) -> Dict[str, Tuple[Pt, Pt, Pt]]:
    """The hip, knee and foot of each named leg (``near_front``, ``far_rear``, ...),
    as ``legs_side`` draws them."""
    out = {}
    for name in which:
        (hx, hy), (kx, ky), fx = LEG_SPEC[name]
        for is_far, off in ((True, 0.22), (False, 0.0)):
            hip = (cx + (hx + off) * s, by + hy - (8 if is_far else 0))
            knee = (cx + (kx * (0.9 if is_far else 1.0) + off * 0.5) * s, by + ky - (18 if is_far else 0) - lift)
            foot = (cx + (fx * (0.8 if is_far else 1.0) + off) * s, GROUND - (6 if is_far else 0))
            out[f"{'far' if is_far else 'near'}_{name}"] = (hip, knee, foot)
    return out


def leg_pieces(hip: Pt, knee: Pt, foot: Pt, pal: Dict, far: bool) -> Tuple[Items, Items]:
    """``leg`` cut at the knee: the thigh, and the shin with its pointed foot
    and the ball of the knee over the joint."""
    col, sh = (pal["leg_sh"], pal["leg_dk"]) if far else (pal["leg"], pal["leg_sh"])
    lt = None if far else pal.get("leg_lt")
    thigh = svg.capsule(hip, knee, 7.2, 6.2)
    ang = math.atan2(foot[1] - knee[1], foot[0] - knee[0])
    nx, ny = -math.sin(ang), math.cos(ang)
    mid = (knee[0] + (foot[0] - knee[0]) * 0.72, knee[1] + (foot[1] - knee[1]) * 0.72)
    shin = sm([(knee[0] + nx * 5.4, knee[1] + ny * 5.4), (mid[0] + nx * 3.8, mid[1] + ny * 3.8),
               (foot[0], foot[1], True), (mid[0] - nx * 3.4, mid[1] - ny * 3.4),
               (knee[0] - nx * 5.4, knee[1] - ny * 5.4), (knee[0] - math.cos(ang) * 5.6, knee[1] - math.sin(ang) * 5.6)])
    tip = sm([(mid[0] + nx * 3.8, mid[1] + ny * 3.8), (foot[0], foot[1], True), (mid[0] - nx * 3.4, mid[1] - ny * 3.4),
              ((mid[0] + foot[0]) / 2, (mid[1] + foot[1]) / 2 - 1)])
    t_items = [P(thigh, INK, INK, OUT)] + cel(thigh, col, sh, lt, s=4, sw=0)
    s_items = [P(shin, INK, INK, OUT)] + cel(shin, col, sh, lt, s=4, sw=0) + [P(tip, pal["foot"])]
    s_items.append(disc(knee[0], knee[1], 7.0, pal["joint_sh"] if far else pal["joint"], sw=IN))
    if not far:
        s_items.append(disc(knee[0] + 2.2, knee[1] - 2.2, 2.4, pal.get("joint_lt", "#ffffff"), sw=0))
    return t_items, s_items


class CastRig:
    """What a cast drawing hands the rig build: ``joints`` (bone: (parent, x,
    y), parents first), ``parts`` (group, label, part, bone, z, items, channel,
    shown at rest) and ``legs`` (leg: (parent bone, hip, knee, foot))."""

    def __init__(self) -> None:
        self.joints: Dict[str, Tuple[str, float, float]] = {}
        self.parts: List[Tuple[str, str, str, str, float, Items, str, bool]] = []
        self.legs: Dict[str, Tuple[str, Pt, Pt, Pt]] = {}

    def joint(self, name: str, parent: str, at: Pt) -> None:
        self.joints[name] = (parent, float(at[0]), float(at[1]))

    def part(self, name: str, label: str, bone: str, z: float, items: Items, channel: str = "", on: bool = True) -> None:
        self.parts.append((name.replace("_", "-"), label, name, bone, z, items, channel, on))

    def add_legs(self, parent: str, pts: Dict[str, Tuple[Pt, Pt, Pt]], pal: Dict) -> None:
        for leg, (hip, knee, foot) in pts.items():
            far = leg.startswith("far")
            self.legs[leg] = (parent, hip, knee, foot)
            self.joint(f"{leg}_thigh", parent, hip)
            self.joint(f"{leg}_shin", f"{leg}_thigh", knee)
            thigh, shin = leg_pieces(hip, knee, foot, pal, far)
            z = 10.0 if far else 20.0
            label = leg.replace("_", " ").title()
            self.part(f"{leg}_thigh", f"{label} Leg - Thigh", f"{leg}_thigh", z, thigh)
            self.part(f"{leg}_shin", f"{label} Leg - Shin", f"{leg}_shin", z + 0.5, shin)


def cast_dividing() -> CastRig:
    """Look A, the twin-core cell, cut into parts: each lobe (its membrane,
    nucleus, feeler and four legs) turns about the middle of its underside;
    the cleavage ring has a cool and a hot drawing, and the strand between the
    halves shows only when they are apart."""
    pal = DIV
    rig = CastRig()
    rcx, fcx, cy, by = 148.0, 252.0, 268.0, 318.0
    rig.joint("body", "", (CAST_CX, by))
    for lobe, cx in (("rear_lobe", rcx), ("front_lobe", fcx)):
        rig.joint(lobe, "body", (cx, by))
    rig.add_legs("rear_lobe", leg_points(rcx, by, 52, ("rear", "rmid")), pal)
    rig.add_legs("front_lobe", leg_points(fcx, by, 52, ("fmid", "front")), pal)
    for lobe, cx, sign, core_xy, seed in (("rear_lobe", rcx, -1, (rcx - 4, cy + 12), 5), ("front_lobe", fcx, 1, (fcx - 16, cy + 14), 2)):
        root = (cx + 18 * sign, cy - 52)
        feel_pts = [root, (cx + 30 * sign, cy - 84), (cx + 50 * sign, cy - 98)]
        feeler = f"{lobe.split('_')[0]}_feeler"
        rig.joint(feeler, lobe, root)
        rig.part(feeler, f"{lobe.split('_')[0].title()} Feeler", feeler, 24 + (0 if sign < 0 else 2),
                 [ln(feel_pts, INK, 10), ln(feel_pts, pal["leg_sh"], 4.5), disc(feel_pts[-1][0], feel_pts[-1][1], 7, pal["pupil"], sw=IN)])
        speck = [disc(cx - 30 * sign, cy - 22, 4, pal["mem_lt"], sw=0), disc(cx - 16 * sign, cy + 30, 3, pal["mem_sh"], sw=0)]
        under = cel(poly([(cx - 52, by - 18), (cx + 52, by - 18), (cx + 40, by + 4), (cx - 40, by + 4)]), pal["slate"], pal["slate_sh"], None, s=4, sw=IN)
        body = cel(E(cx, cy, 66.0, 58), pal["mem"], pal["mem_sh"], pal["mem_lt"], s=13, l=7, items=speck + nucleus(core_xy[0], core_xy[1], 21, pal, seed))
        rig.part(lobe, f"{lobe.replace('_', ' ').title()}", lobe, 40 if sign < 0 else 44, under + body)
    # the eye and the mandibles ride on the front lobe
    rig.part("eye", "Eye", "front_lobe", 46, eye(fcx + 40, cy - 20, 18, 14, pal, look=(5, 1), rot=-8))
    base = (fcx + 54, by - 12)
    mfar, mnear = mandibles_side(base, pal)
    rig.joint("mandible_far", "front_lobe", (base[0] - 2, base[1] - 8))
    rig.joint("mandible_near", "front_lobe", base)
    rig.part("mandible_far", "Mandible - Far", "mandible_far", 8, mfar)
    rig.part("mandible_near", "Mandible - Near", "mandible_near", 48, mnear)
    # the waist: the ring cool, the ring hot, and the strand of a split
    wx = CAST_CX
    rig.joint("ring", "body", (wx, cy))
    rig.part("ring_cool", "Cleavage Ring", "ring", 50,
             cel(E(wx, cy, 13.0, 50), pal["ring"], pal["mem_lt"], None, s=3, sw=OUT), "ring_cool", True)
    rig.part("ring_hot", "Cleavage Ring - Hot", "ring", 50.5,
             cel(E(wx, cy, 9.0, 46), pal["ring_hot"], pal["mem_lt"], None, s=3, sw=OUT)
             + [ln([(wx - 4, cy - 62), (wx - 8, cy - 76)], pal["ring"], 4), ln([(wx + 4, cy - 62), (wx + 10, cy - 74)], pal["ring"], 4),
                ln([(wx, cy + 56), (wx + 2, cy + 70)], pal["ring"], 4)], "ring_hot", False)
    strand = sm([(wx - 34, cy - 12), (wx, cy - 5), (wx + 34, cy - 12), (wx + 34, cy + 14), (wx, cy + 6), (wx - 34, cy + 14)])
    rig.part("strand", "Membrane Strand", "ring", 39, cel(strand, pal["ring"], pal["mem_lt"], None, s=3, sw=IN + 1)
             + [ln([(wx - 10, cy - 36), (wx - 16, cy - 50)], pal["ring"], 4), ln([(wx + 8, cy - 38), (wx + 16, cy - 52)], pal["ring"], 4)],
             "strand", False)
    return rig


def _bomb_shell(pal: Dict, t: int, cx: float, cy: float, by: float, r: float) -> Items:
    """The shell of look A at wind-up stage ``t`` (0 rest, 1 hot, 2 white hot):
    valve, shell, belt, cap, eye and brow, swollen about the underside."""
    d = E(cx, cy, r, r - 2)
    belt_d = sm([(cx - r - 10, cy + 2, True), (cx, cy + 12), (cx + r + 10, cy + 2, True), (cx + r + 10, cy + 30, True), (cx, cy + 40),
                 (cx - r - 10, cy + 30, True)])
    rivets = [disc(cx + x, cy + 26 + 8 * (1 - (x / r) ** 2), 3.2, pal["haz_sh"], sw=0) for x in (-56, -28, 0, 28, 56)]
    belt = [P(belt_d, pal["haz"]), *clip(belt_d, stripes(cx - r - 10, cy - 4, cx + r + 10, cy + 44, 24, 12, INK, ang=35)), P(belt_d, "none", INK, IN)]
    glow: Items = []
    if t >= 1:
        hot = pal["hot"] if t == 1 else pal["white_hot"]
        seams = [[(cx - 20, cy - r + 4), (cx - 30, cy - 30), (cx - 26, cy + 2)], [(cx + 40, cy + 44), (cx + 36, cy + 70)]]
        if t == 2:
            seams += [[(cx + 30, cy - r + 10), (cx + 46, cy - 30)], [(cx - 60, cy + 44), (cx - 40, cy + 60)]]
        for s_ in seams:
            glow += [ln(s_, INK, 8), ln(s_, hot, 4)]
    plates = [ln([(cx - 20, cy - r + 4), (cx - 30, cy - 30), (cx - 26, cy + 2)], pal["steel_sh"], 3) if t == 0 else "",
              disc(cx - 40, cy - 40, 3.5, pal["steel_lt"], sw=0), disc(cx + 10, cy - 60, 3.5, pal["steel_lt"], sw=0)]
    body = cel(d, pal["steel"] if t < 2 else "#5a3e3a", pal["steel_sh"], pal["steel_lt"], s=14, l=7, items=plates + belt + rivets + glow)
    cap_c = (cx - 18, cy - r + 2)
    cap = cel(poly([(cap_c[0] - 18, cap_c[1] + 4), (cap_c[0] + 16, cap_c[1] - 2), (cap_c[0] + 12, cap_c[1] - 20), (cap_c[0] - 16, cap_c[1] - 15)]),
              pal["brass"], pal["brass_sh"], pal["brass_lt"], s=3, sw=IN)
    ey = eye(cx + 48, cy - 22, 19, 17, pal, look=(5, 1), rot=-6, mood="wide" if t == 2 else "calm", pupil_k=(1.0, 0.8, 1.15)[t])
    brow = cel(poly([(cx + 24, cy - 48), (cx + 74, cy - 30), (cx + 76, cy - 42), (cx + 28, cy - 60)]), pal["brow"], pal["brow_sh"], None, s=3, sw=IN)
    vx, vy = cx - r + 2, cy - 26
    valve = cel(poly([(vx + 8, vy - 6), (vx - 14, vy - 8), (vx - 14, vy + 6), (vx + 8, vy + 8)]), pal["brass"], pal["brass_sh"], pal["brass_lt"], s=2, sw=IN)
    valve += cel(E(vx - 18, vy - 1, 5, 13), pal["red"], pal["red_sh"], pal["red_lt"], s=2, l=2, sw=IN)
    if t >= 1:
        for px_, py_, pr in ((vx - 34, vy - 10, 8), (vx - 46, vy - 24, 10), (vx - 54, vy - 42, 12))[: (2, 3)[t - 1]]:
            valve.append(disc(px_, py_, pr, "#eef1f4", sw=IN))
    return grp(valve + body + cap + ey + brow, about(cx, by, k=(1.0, 1.08, 1.17)[t]))


def cast_exploding() -> CastRig:
    """Look A, the bomb, cut into parts: eight legs and two mandibles about
    the shell; the shell drawn at the three stages of its wind-up (rest, hot,
    white hot and swollen), the wick at three lengths with its spark, and the
    spark drawn twice so it can flicker."""
    pal = EXP
    rig = CastRig()
    cx, cy, by, r = 196.0, 262.0, 330.0, 78.0
    rig.joint("body", "", (cx, by))
    rig.add_legs("body", leg_points(cx, by, 70, ("rear", "rmid", "fmid", "front")), pal)
    base = (cx + 70, by - 18)
    mfar, mnear = mandibles_side(base, pal)
    rig.joint("mandible_far", "body", (base[0] - 2, base[1] - 8))
    rig.joint("mandible_near", "body", base)
    rig.part("mandible_far", "Mandible - Far", "mandible_far", 8, mfar)
    rig.part("mandible_near", "Mandible - Near", "mandible_near", 48, mnear)
    for t, label in ((0, "Shell"), (1, "Shell - Hot"), (2, "Shell - White Hot")):
        rig.part(f"shell_{t}", label, "body", 40 + t * 0.1, _bomb_shell(pal, t, cx, cy, by, r), f"shell_{t}", t == 0)
    cap_c = (cx - 18, cy - r + 2)
    full = [(cap_c[0] - 2, cap_c[1] - 17), (cap_c[0] - 14, cap_c[1] - 42), (cap_c[0] - 42, cap_c[1] - 58), (cap_c[0] - 54, cap_c[1] - 84)]
    rig.joint("fuse", "body", full[0])
    for t, label in ((0, "Fuse"), (1, "Fuse - Burnt Half"), (2, "Fuse - Burnt Down")):
        pts = full[: (4, 3, 2)[t]]
        tf = about(cx, by, k=(1.0, 1.08, 1.17)[t])
        wick = grp([ln(pts, INK, 9), ln(pts, "#b89a6a", 4)], tf)
        rig.part(f"wick_{t}", label, "fuse", 46 + t * 0.1, wick, f"wick_{t}", t == 0)
        for k, rot in (("a", 0.0), ("b", 23.0)) if t == 0 else (("a", t * 11.0),):
            sp = grp(spark(pts[-1][0], pts[-1][1], (18, 22, 28)[t], pal, rot=rot), tf)
            ch = f"spark_{t}{k}"
            rig.part(ch, f"Spark - {label} {k}", "fuse", 47 + t * 0.1, sp, ch, ch == "spark_0a")
    return rig


CAST = {"dividing_mite_v2": cast_dividing, "exploding_mite_v2": cast_exploding}


def cast_svg_path(name: str) -> Path:
    return ROOT / "ambition_sprite2d_renderer" / "data" / "characters" / name / f"{name}_side.svg"


def cast_svg_text(name: str) -> str:
    _N[0] = 0
    svg.configure(dx=0, dy=0, ink=INK, ow=OUT / 2, colors={})
    rig = CAST[name]()
    for group, label, part, bone, z, items, channel, on in rig.parts:
        extra = ""
        if channel:
            extra = f' data-rig-opacity="{channel}"' + (' data-rig-default="1"' if on else "")
        svg.part(group, label, part, bone, z, [s for s in items if s], extra)
    look = "twin-core cell" if name.startswith("dividing") else "bomb"
    return svg.document(
        size=(W, H), design=f"{name.replace('_', '-')}-a", layer_id=name.replace("_", "-"), label=CAST_VIEW[name],
        comment=[f"  <!-- {name}: look A ({look}), cast 2026-10-23; side view facing right, the ground at y={GROUND:g}.",
                 "       Drawn by scripts/svg_art/mites_art.py (the cast mode); each part turns about its bone's joint. -->"],
        joints=svg.joints_layer({k: (v[1], v[2]) for k, v in rig.joints.items()}),
    )


def write_cast() -> List[Path]:
    out = []
    for name in CAST_NAMES:
        p = cast_svg_path(name)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".svg.tmp")
        tmp.write_text(cast_svg_text(name), encoding="utf8")
        tmp.replace(p)
        out.append(p)
    return out


# ---------------------------------------------------------------------------------------------
# contact sheets (resvg_py + PIL from the tool venv)
# ---------------------------------------------------------------------------------------------

BG = (216, 221, 227, 255)
ROBOT_SHEET = Path(__file__).resolve().parents[4] / "crates/ambition_platformer2d_actor_monolith/assets/sprites/player_robot_v3_spritesheet.png"
#: The robot's first idle frame and its body height in sheet px (its manifest's
#: ``idle`` rect and ``body_pixel_bbox``): 91 sheet px stand 48 world px.
ROBOT_IDLE = (1788, 2007, 71, 101)
ROBOT_BODY_PX, ROBOT_WORLD = 91, 48.0


#: Where each close-up looks, in design units (the side view at 2.2x).
CLOSE = {("dividing_mite", "A"): (236, 262), ("dividing_mite", "B"): (238, 262), ("dividing_mite", "C"): (214, 236),
         ("exploding_mite", "A"): (178, 186), ("exploding_mite", "B"): (196, 176), ("exploding_mite", "C"): (200, 232)}


def render(text: str, px: int):
    import resvg_py
    from PIL import Image
    data = resvg_py.svg_to_bytes(svg_string=text, width=px, height=px, skip_system_fonts=True)
    return Image.open(io.BytesIO(bytes(data))).convert("RGBA")


def _font(size: int):
    from PIL import ImageFont
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def trim(im):
    bb = im.getbbox()
    return im.crop(bb) if bb else im


def game_size(im_full_400):
    """The figure at world size: design units x WORLD_PER_UNIT (rendered from a
    400 px drawing, so units = px), then shown 1x and 3x nearest."""
    from PIL import Image
    fig = trim(im_full_400)
    w, h = fig.size
    gw, gh = max(1, round(w * WORLD_PER_UNIT)), max(1, round(h * WORLD_PER_UNIT))
    small = fig.resize((gw, gh), Image.LANCZOS)
    return small


def robot_game():
    from PIL import Image
    sheet = Image.open(ROBOT_SHEET).convert("RGBA")
    x, y, w, h = ROBOT_IDLE
    fr = trim(sheet.crop((x, y, x + w, y + h)))
    k = ROBOT_WORLD / ROBOT_BODY_PX
    return fr.resize((max(1, round(fr.width * k)), max(1, round(fr.height * k))), Image.LANCZOS)


def paste_ground(canvas, im, x, ground_y):
    canvas.alpha_composite(im, (int(x), int(ground_y - im.height)))


def contact_sheet(mite: str, out_png: Path) -> None:
    from PIL import Image, ImageDraw
    looks = LOOKS[mite]
    FIG = 400
    row_h = 470
    Wd = 2480
    sheet = Image.new("RGBA", (Wd, 60 + row_h * len(looks)), BG)
    dr = ImageDraw.Draw(sheet)
    f_big, f_small = _font(26), _font(17)
    dr.text((20, 16), f"{mite.replace('_', ' ')} -- redesign round 1   (side | front | close-up | {STRIP[mite]} | game size 1x and 3x, robot for scale)",
            fill=(30, 30, 36), font=f_small)
    robot = robot_game()
    for i, (key, label, _fn) in enumerate(looks):
        y0 = 60 + i * row_h
        dr.text((20, y0 + 4), f"{key}: {label}", fill=(25, 25, 30), font=f_big)
        side = render(svg_text(mite, key, "side"), FIG)
        front = render(svg_text(mite, key, "front"), FIG)
        x = 10
        sheet.alpha_composite(side, (x, y0 + 40)); x += FIG
        sheet.alpha_composite(front, (x, y0 + 40)); x += FIG
        # close-up: the top-front of the side view at 2.2x
        big = render(svg_text(mite, key, "side"), 880)
        ux, uy = CLOSE[(mite, key)]
        crop = big.crop((int(ux * 2.2 - 200), int(uy * 2.2 - 200), int(ux * 2.2 + 200), int(uy * 2.2 + 200)))
        tile = Image.new("RGBA", crop.size, BG)
        tile.alpha_composite(crop)
        sheet.alpha_composite(tile, (x + 10, y0 + 40)); x += 430
        # the strip
        for t in range(3):
            fr = render(svg_text(mite, key, "side", t), 300)
            sheet.alpha_composite(fr, (x, y0 + 120))
            dr.text((x + 130, y0 + 96), f"{t + 1}", fill=(60, 60, 70), font=f_small)
            x += 280
        x += 20
        # game size: the mite beside the robot, 1x then 3x nearest
        g = game_size(side)
        gy = y0 + 250
        paste_ground(sheet, robot, x, gy)
        paste_ground(sheet, g, x + robot.width + 6, gy)
        pair = Image.new("RGBA", (robot.width + 6 + g.width, max(robot.height, g.height)), (0, 0, 0, 0))
        paste_ground(pair, robot, 0, pair.height)
        paste_ground(pair, g, robot.width + 6, pair.height)
        pair3 = pair.resize((pair.width * 3, pair.height * 3), Image.NEAREST)
        paste_ground(sheet, pair3, x, y0 + 430)
        dr.line([(x - 4, gy), (x + pair.width + 4, gy)], fill=(150, 155, 165), width=1)
    sheet.convert("RGB").save(out_png)


def family_sheet(out_png: Path) -> None:
    """Every look of both mites at game size beside the robot's idle frame,
    1x and 3x, on one ground line."""
    from PIL import Image, ImageDraw
    robot = robot_game()
    items = [("robot", robot)]
    for mite, looks in LOOKS.items():
        for key, label, _fn in looks:
            items.append((f"{'div' if mite.startswith('div') else 'exp'} {key}", game_size(render(svg_text(mite, key, "side"), 400))))
    gap = 8
    strip_w = sum(im.width for _, im in items) + gap * (len(items) - 1)
    strip_h = max(im.height for _, im in items)
    strip = Image.new("RGBA", (strip_w, strip_h), (0, 0, 0, 0))
    x = 0
    xs = []
    for _, im in items:
        paste_ground(strip, im, x, strip_h)
        xs.append((x, im.width))
        x += im.width + gap
    k = 4
    big = strip.resize((strip_w * k, strip_h * k), Image.NEAREST)
    Wd = max(big.width + 40, 900)
    sheet = Image.new("RGBA", (Wd, 120 + strip_h + 60 + big.height + 60), BG)
    dr = ImageDraw.Draw(sheet)
    f_small = _font(16)
    dr.text((20, 12), "mites, round 1 -- the family at game size beside the player robot (48 world px).  1x, then 4x nearest.",
            fill=(30, 30, 36), font=f_small)
    dr.text((20, 34), f"scale: 1 design unit = {WORLD_PER_UNIT} world px (robot body 91 sheet px = 48 world px)", fill=(70, 70, 80), font=f_small)
    paste_ground(sheet, strip, 20, 80 + strip_h)
    by = 120 + strip_h + big.height
    paste_ground(sheet, big, 20, by)
    for (name, _), (x0, w) in zip(items, xs):
        dr.text((20 + x0 * k + w * k // 2 - 20, by + 10), name, fill=(30, 30, 36), font=f_small)
    sheet.convert("RGB").save(out_png)


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--cast":
        for p in write_cast():
            print(p)
        return
    if len(sys.argv) > 2 and sys.argv[1] in ("--all", "--sheets"):
        out = Path(sys.argv[2])
        for p in write_all(out / "svg"):
            print(p)
        if sys.argv[1] == "--sheets":
            for mite in LOOKS:
                p = out / f"{mite}_r1.png"
                contact_sheet(mite, p)
                print(p)
            p = out / "family_r1.png"
            family_sheet(p)
            print(p)
        return
    raise SystemExit("usage: mites_art.py --cast | --all DIR | --sheets DIR")


if __name__ == "__main__":
    main()
