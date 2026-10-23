#!/usr/bin/env python3
"""The Steel Man and the Straw Man: their candidates and the drawings of ``steel_man`` and ``straw_man``.

    uv run python scripts/svg_art/steel_and_straw_man_art.py --all DIR      # every look: one SVG each (side and front cells)
    uv run python scripts/svg_art/steel_and_straw_man_art.py --sheets DIR   # the contact sheets (resvg_py + PIL)

Jon, 2026-10-23: "two new characters are the steel Man and the straw man. I'm
going to take some philosophical positions in the game, but I'm going to work
to check my biases and give the opposing point of view the best light
possible. and the straw man is going to effectively be comic relief. in my
mind they look like the characters from wizard of Oz tin Man in a scarecrow,
but I want to avoid that."

WHO THEY ARE.

* THE STEEL MAN is the opposing argument at its strongest: formidable,
  dignified, honest, well built, someone you respect while you disagree. He is
  made of STRUCTURAL steel, forged and riveted like a bridge or a foundry
  casting, not of tin: no funnel hat, no oil can, no axe, no heart clock, no
  stovepipe limbs and no silver-grey Oz palette. A calm face; an orator's
  stance; he stands still. 196 cm.
* THE STRAW MAN is the flimsy misrepresentation that is easy to knock down:
  comic relief. He is made of straw like a harvest sheaf, a wicker effigy or a
  corn dolly, not like a scarecrow: no floppy pointed hat, no burlap sack face
  with stitches, no patched farm clothes, no crows, no pole. Loosely tied,
  shedding, over-confident, falling apart a little; funny, but an adult figure
  in the game's style, not a baby-faced mascot. 185 cm and gangly.

THE LOOKS (three each; the cast look is ``CAST``, the others are KEPT, NOT CAST):

* steel A, the girder: blued plate riveted over red-lead I-beam limbs with
  lightening holes, pin-bolted joints, footings bolted like a column's base, a
  brass builder's plate on the chest.
* steel B, the forged statesman: blackened forged steel with temper colours at
  the edges, a long coat of overlapping plates, a hammered-rod beard.
* steel C, the bridge pier: red-oxide paint, an X-braced lattice waist and
  forearms, a riveted dome over the brow.
* straw A, the sheaf: a wheat sheaf bound at the neck, waist, knees and ankles
  with jute, ears of wheat for a quiff, a blue first-prize rosette he awarded
  himself.
* straw B, the wicker effigy: woven willow over a frame, a wicker ball head.
* straw C, the corn dolly: plaited straw, red harvest ribbons at the neck and
  the wrists.

HOW IT IS DRAWN. House style of ``runge_kutta_duo_art.py`` and ``oiler_art.py``:
flat cel fills, one shade band down-back and a light band up-front, a thick
warm ink line, NO drop shadow. Every view is a cell of ONE SVG (Jon,
2026-10-21: views in a grid): the side view facing right in the cell at the
origin, the front view in the cell to its right. The small parts both views
draw (a rivet, a bolt head, a straw end) are ``<use>`` clones of one source
in ``<defs>``. Each part of the side view is its own layer on its bone (the
README layer contract), so ``scripts/build_steel_and_straw_man_rigs.py`` can
rig the cast look; that script writes the SVG and the rig.
"""
from __future__ import annotations

import io
import math
import random
import sys
from pathlib import Path
from typing import Callable, Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import svgkit as svg  # noqa: E402
from svgkit import capsule, line, path, smooth  # noqa: E402

W = H = 560
GROUND = 502.0
CX = 280.0
INK = "#1d1714"
OUT = 3.2   # silhouette ink
FINE = 1.4  # inner ink
SD, LD = (-1.0, 0.6), (1.0, -0.8)
#: The second cell (the front view) starts this far right of the first.
CELL_DX = 560.0

# ============================================================================================
# colour and cel shading
# ============================================================================================


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _hex(c):
    return "#" + "".join(f"{max(0, min(255, int(round(v)))):02x}" for v in c)


def dark(h, k=0.74):
    """The shade tone: darker and a touch cooler."""
    r, g, b = _rgb(h)
    return _hex((r * k * 0.97, g * k, b * k * 1.06 + 4))


def lite(h, k=0.22):
    r, g, b = _rgb(h)
    return _hex((r + (255 - r) * k, g + (255 - g) * k, b + (255 - b) * k * 0.85))


def mix(a, b, t):
    ra, rb = _rgb(a), _rgb(b)
    return _hex(tuple(x + (y - x) * t for x, y in zip(ra, rb)))


_N = [0]


def uid():
    _N[0] += 1
    return f"ss{_N[0]}"


def cel(d, base, sh, lt=None, items=(), sdir=SD, ldir=LD, s=5.0, l=3.0, sw=None, ink=None, edges=None):
    """A fill, a shade band on the edges facing ``sdir``, a light band on
    those facing ``ldir``, the ``items`` clipped inside, then the ink (or only
    the ``edges`` runs)."""
    cid = uid()
    sx, sy = -sdir[0] * s, -sdir[1] * s
    out = [f'<clipPath id="{cid}"><path d="{d}" /></clipPath>',
           f'<clipPath id="{cid}s"><path d="{d}" transform="translate({sx:.2f} {sy:.2f})" /></clipPath>',
           f'<g clip-path="url(#{cid})">', path(d, sh), f'<g clip-path="url(#{cid}s)">']
    if lt:
        lx, ly = -ldir[0] * l, -ldir[1] * l
        out += [path(d, lt), path(d, base, extra=f' transform="translate({lx:.2f} {ly:.2f})"')]
    else:
        out.append(path(d, base))
    out.append("</g>")
    out += list(items)
    out.append("</g>")
    if edges is None:
        out.append(path(d, "none", ink or INK, sw or OUT))
    else:
        out += [path(svg.smooth(run, closed=False), "none", ink or INK, sw or OUT) for run in edges]
    return out


def K(key, items=(), **kw):
    """Cel-shade in the look's colour ``key`` (its ``_sh`` and ``_lt`` tones)."""
    return lambda d: cel(d, O[key], O[key + "_sh"], O[key + "_lt"], items, **kw)


def paint(d, key, items=(), far=False, **kw):
    if far:
        kw["s"] = min(2.0, kw.get("s", 2.0))
        return cel(d, O[key + "_sh"], dark(O[key + "_sh"], 0.86), None, items, **kw)
    return cel(d, O[key], O[key + "_sh"], O[key + "_lt"], items, **kw)


def frame(origin, a):
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    return lambda t, s: (origin[0] + ux * t + nx * s, origin[1] + uy * t + ny * s)


def ang(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0])


def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def poly(pts):
    return "M" + " L".join(svg.pt(p) for p in pts) + " Z"


def circle(x, y, r, fill, stroke=None, sw=None):
    s = f'<circle cx="{svg.f(x)}" cy="{svg.f(y)}" r="{svg.f(r)}" fill="{fill}"'
    if stroke:
        s += f' stroke="{stroke}" stroke-width="{svg.f(sw)}"'
    return s + " />"


def clone(ref, x, y, k=1.0, rot=0.0):
    """A ``<use>`` clone of a ``<defs>`` source at ``(x, y)``."""
    t = f"translate({svg.f(x)} {svg.f(y)})"
    if rot:
        t += f" rotate({svg.f(rot)})"
    if k != 1.0:
        t += f" scale({svg.f(k)})"
    return f'<use xlink:href="#{ref}" transform="{t}" />'


def tube(a, b, r0, r1, square=False):
    """A tapered piece from ``a`` to ``b``: round ends, or near-square ones."""
    if not square:
        return capsule(a, b, r0, r1)
    p = frame(a, ang(a, b))
    L = dist(a, b)
    c = min(r0, r1) * 0.35
    pts = [p(-c, -r0 + c), p(0, -r0), p(L, -r1), p(L + c, -r1 + c), p(L + c, r1 - c), p(L, r1), p(0, r0), p(-c, r0 - c)]
    return poly(pts)


# ============================================================================================
# the clones both views share (``<defs>``)
# ============================================================================================

def defs() -> List[str]:
    """Rivets and bolt heads (steel); a loose straw end and a wheat ear (straw)."""
    if O["who"] == "steel":
        r, rs, rl = O["rivet"], dark(O["rivet"], 0.62), lite(O["rivet"], 0.45)
        return [
            '<g id="rivet">',
            f'  <circle r="2.6" fill="{rs}" stroke="{INK}" stroke-width="1.1" />',
            f'  <circle cx="-0.5" cy="-0.5" r="1.7" fill="{r}" />',
            f'  <circle cx="-0.9" cy="-0.9" r="0.7" fill="{rl}" />',
            '</g>',
            '<g id="bolt">',
            f'  <path d="M-5.2,0 L-2.6,-4.5 L2.6,-4.5 L5.2,0 L2.6,4.5 L-2.6,4.5 Z" fill="{rs}" stroke="{INK}" stroke-width="1.3" />',
            f'  <path d="M-3.6,0 L-1.8,-3.1 L1.8,-3.1 L3.6,0 L1.8,3.1 L-1.8,3.1 Z" fill="{r}" />',
            f'  <circle r="1.5" fill="{rs}" />',
            '</g>',
        ]
    s, sh, lt = O["straw"], O["straw_sh"], O["straw_lt"]
    return [
        '<g id="straw-end">',
        f'  <path d="M0,-1.0 L12,-0.6 L14,0 L12,0.6 L0,1.0 Z" fill="{lt}" stroke="{INK}" stroke-width="0.6" stroke-linejoin="round" />',
        f'  <path d="M1,0 L12,0" stroke="{sh}" stroke-width="0.5" />',
        '</g>',
        '<g id="wheat-ear">',
        f'  <path d="M0,0 L0,-14" stroke="{INK}" stroke-width="2.6" stroke-linecap="round" />',
        f'  <path d="M0,0 L0,-14" stroke="{sh}" stroke-width="1.1" stroke-linecap="round" />',
        *[f'  <ellipse cx="{side * 2.2:.1f}" cy="{-15 - i * 4.2:.1f}" rx="2.2" ry="3.3" transform="rotate({side * 24} {side * 2.2:.1f} {-15 - i * 4.2:.1f})" '
          f'fill="{lt if side < 0 else s}" stroke="{INK}" stroke-width="0.9" />'
          for i in range(4) for side in (-1, 1)],
        f'  <ellipse cx="0" cy="-33" rx="1.9" ry="3.4" fill="{lt}" stroke="{INK}" stroke-width="0.9" />',
        f'  <path d="M0,-35 L-1.5,-46 M0,-35 L1.8,-45" stroke="{INK}" stroke-width="0.6" />',
        '</g>',
    ]


def rivets(pts, k=1.0):
    return [clone("rivet", x, y, k) for x, y in pts]


def rivet_run(a, b, n, k=1.0):
    return rivets([(a[0] + (b[0] - a[0]) * i / (n - 1), a[1] + (b[1] - a[1]) * i / (n - 1)) for i in range(n)], k)


# ============================================================================================
# the looks
# ============================================================================================

LOOKS: Dict[str, Dict[str, dict]] = {
    "steel": {
        "A": dict(label="A: the girder - blued plate riveted over red-lead I-beams, a builder's plate",
                  plate="#4b6077", girder="#9e4a33", rivet="#9fb2c6", eye="#e9e2cf", iris="#3a5a7a",
                  brass="#c9a24a", style="girder"),
        "B": dict(label="B: the forged statesman - blackened steel, temper colours, a coat of plates, a rod beard",
                  plate="#50535d", girder="#50535d", rivet="#8d93a0", eye="#e6dfcf", iris="#5a4a3a",
                  brass="#b8873e", temper=("#c9a04e", "#8a5e98", "#4f74b0"), style="forged"),
        "C": dict(label="C: the bridge pier - red-oxide steel, X-braced lattice, a riveted dome",
                  plate="#8e4431", girder="#7a3a2b", rivet="#c4a08e", eye="#ece5d2", iris="#3c4e5e",
                  brass="#c9a24a", style="pier"),
    },
    "straw": {
        "A": dict(label="A: the sheaf - wheat bound in jute, an ear-of-wheat quiff, a first prize he gave himself",
                  straw="#dab35a", twine="#7c5536", ribbon="#2f5fa8", seed="#2a1d14", style="sheaf"),
        "B": dict(label="B: the wicker effigy - woven willow over a frame, a wicker ball head",
                  straw="#c08d4f", twine="#6e4a2c", ribbon="#2f5fa8", seed="#22170f", style="wicker"),
        "C": dict(label="C: the corn dolly - plaited pale straw, red harvest ribbons",
                  straw="#e6cd84", twine="#a7832f", ribbon="#b8322b", seed="#2a1d14", style="dolly"),
    },
}

#: The look each character is built in (the others are kept, not cast).
CAST = {"steel": "A", "straw": "A"}

O: Dict = {}
G: Dict = {}


def use(who: str, look: str) -> None:
    O.clear()
    O.update(LOOKS[who][look])
    O["who"], O["look"] = who, look
    for key in ("plate", "girder", "straw", "twine", "ribbon", "brass"):
        if key in O:
            O.setdefault(key + "_sh", dark(O[key]))
            O.setdefault(key + "_lt", lite(O[key]))
    G.clear()
    G.update(BUILDS[who])
    _N[0] = 0


# ============================================================================================
# the builds: joints of the side view (facing right) and of the front view
# ============================================================================================

BUILDS = {
    "steel": dict(
        eye=(304.0, 180.0), hk=0.8, neck=(282.0, 216.0), crown=150.0,
        n_sh=(284.0, 248.0), n_el=(288.0, 314.0), n_wr=(292.0, 372.0),
        f_sh=(272.0, 246.0), f_el=(266.0, 312.0), f_wr=(270.0, 370.0),
        body=(281.0, 342.0),
        n_hip=(289.0, 356.0), n_knee=(291.0, 428.0), n_ank=(287.0, 486.0),
        f_hip=(272.0, 356.0), f_knee=(270.0, 428.0), f_ank=(265.0, 486.0),
        r_up=(16.0, 13.5), r_fore=(14.0, 11.5), r_thigh=(19.5, 15.5), r_shin=(15.5, 12.5),
        # front view: x is the offset from the centre line (his right is screen-left, -x)
        fr_sh=(58.0, 250.0), fr_el=(66.0, 314.0), fr_wr=(68.0, 372.0), fr_hip=(21.0, 356.0), fr_knee=(23.0, 428.0), fr_ank=(22.0, 486.0),
        f_eye=(180.0, 11.0), f_crown=150.0,
    ),
    "straw": dict(
        eye=(310.0, 192.0), hk=0.78, neck=(284.0, 230.0), crown=160.0,
        n_sh=(286.0, 256.0), n_el=(292.0, 316.0), n_wr=(298.0, 370.0),
        f_sh=(274.0, 254.0), f_el=(268.0, 314.0), f_wr=(272.0, 368.0),
        body=(280.0, 338.0),
        n_hip=(287.0, 352.0), n_knee=(292.0, 424.0), n_ank=(288.0, 488.0),
        f_hip=(273.0, 352.0), f_knee=(271.0, 424.0), f_ank=(266.0, 488.0),
        r_up=(7.5, 6.5), r_fore=(6.8, 5.6), r_thigh=(10.5, 8.0), r_shin=(8.0, 6.5),
        fr_sh=(40.0, 256.0), fr_el=(48.0, 316.0), fr_wr=(50.0, 370.0), fr_hip=(14.0, 352.0), fr_knee=(17.0, 424.0), fr_ank=(18.0, 488.0),
        f_eye=(192.0, 10.0), f_crown=160.0,
    ),
}


def head_xf(view="side"):
    """A head point (drawn about the eye, ``hk`` scale) to the drawing."""
    if view == "side":
        ex, ey = G["eye"]
        k = G["hk"]
        return lambda x, y: (ex + x * k, ey + y * k)
    ey, eo = G["f_eye"]
    k = G["hk"]
    return lambda x, y: (CX + x * k, ey + y * k)


def HP(pts, view="side"):
    t = head_xf(view)
    return [t(p[0], p[1]) + tuple(p[2:]) for p in pts]


# ============================================================================================
# STEEL: limbs, hands, feet
# ============================================================================================

def steel_piece(a, b, r0, r1, far=False, holes=False, boss_at_b=True, boss_at_a=False):
    """An upper or lower limb of the steel man from joint ``a`` to joint ``b``.

    The girder: a red-lead I-beam web between two blued flanges with
    lightening holes. The forged: a rounded forging with hammer facets. The
    pier: a red-oxide box with X-bracing. The joint boss at ``b`` (a pin bolt)
    covers the next piece's root."""
    style = O["style"]
    L = dist(a, b)
    p = frame(a, ang(a, b))
    d = tube(a, b, r0, r1, square=(style != "forged"))
    items: List[str] = []
    fl = 0.36 * min(r0, r1) + 1.0
    if style == "girder":
        web = poly([p(2, -r0 + fl), p(L - 2, -r1 + fl), p(L - 2, r1 - fl), p(2, r0 - fl)])
        items += [path(web, O["girder_sh"] if far else O["girder"]),
                  path(poly([p(2, -r0 + fl), p(L - 2, -r1 + fl), p(L - 2, -r1 + fl + 1.6), p(2, -r0 + fl + 1.6)]), O["girder_lt"] if not far else O["girder_sh"]),
                  line([p(0, -r0 + fl), p(L, -r1 + fl)], INK, 1.0), line([p(0, r0 - fl), p(L, r1 - fl)], INK, 1.0)]
        if holes:
            for t in (0.36, 0.66):
                c = p(L * t, 0)
                rr = (r0 + (r1 - r0) * t - fl) * 0.55
                items += [circle(c[0], c[1], rr, dark(O["girder"], 0.45), INK, 1.0)]
        items += rivets([p(5, -r0 + 1.8), p(L * 0.5, -(r0 + r1) / 2 + 1.8), p(L - 5, -r1 + 1.8)], 0.7)
    elif style == "forged":
        tc = O["temper"]
        items += [line([p(3, -r0 + 1.6), p(L - 3, -r1 + 1.6)], tc[0], 1.6), line([p(3, -r0 + 3.2), p(L - 3, -r1 + 3.2)], tc[1], 1.2),
                  line([p(3, -r0 + 4.4), p(L - 3, -r1 + 4.4)], tc[2], 1.0)]
        for t in (0.25, 0.5, 0.75):
            items.append(line([p(L * t - 3, r0 * 0.1), p(L * t + 2, r0 * 0.45)], O["plate_sh"], 1.1))
    else:
        inner = [p(4, -r0 + 3.5), p(L - 4, -r1 + 3.5), p(L - 4, r1 - 3.5), p(4, r0 - 3.5)]
        items += [path(poly(inner), dark(O["plate"], 0.5)),
                  line([inner[0], inner[2]], O["plate"], 2.6), line([inner[1], inner[3]], O["plate"], 2.6),
                  line([inner[0], inner[2]], INK, 0.6), line([inner[1], inner[3]], INK, 0.6),
                  path(poly(inner), "none", INK, 1.0)]
        items += rivets([p(4, -r0 + 1.8), p(L - 4, -r1 + 1.8), p(4, r0 - 1.8), p(L - 4, r1 - 1.8)], 0.6)
    out = paint(d, "plate", items, far=far, s=4)
    for at, on in ((b, boss_at_b), (a, boss_at_a)):
        if on:
            r = (r1 if at is b else r0) * 0.86
            ring = [(at[0] + r * 0.62 * math.cos(t), at[1] + r * 0.62 * math.sin(t)) for t in (i * math.pi / 3 + 0.5 for i in range(6))]
            out += paint(svg.smooth([(at[0] + r * math.cos(t), at[1] + r * math.sin(t)) for t in (i * math.pi / 6 for i in range(12))]),
                         "plate", rivets(ring, 0.5), far=far, s=2.5)
            out.append(clone("bolt", at[0], at[1], 0.55))
    return out


def steel_hand(wrist, a, far=False, open_palm=False):
    """A plate hand hanging from ``wrist`` at angle ``a``: a knuckled back
    plate, four jointed fingers, a thumb; seen from its back."""
    q = frame(wrist, a)
    k = 1.45
    p = lambda t, s: q(k * t, -k * s)
    key = "plate"
    out: List[str] = []
    thumb = svg.smooth([p(2, 5), p(9, 9.5), p(15, 10.5), p(17, 8.0), p(12, 5), p(6, 3)])
    out += paint(thumb, key, [line([p(10, 7.4), p(12.5, 9.8)], INK, 0.9)], far=far, s=1.5, sw=FINE + 0.6)
    for f0, length in ((-5.2, 13.0), (-1.8, 15.0), (1.7, 15.6), (5.0, 13.6)):
        c = 2.2
        fd = poly([p(9, f0 - c), p(9 + length, f0 - c + 0.6), p(10.5 + length, f0), p(9 + length, f0 + c - 0.4), p(9, f0 + c)])
        out += paint(fd, key, [line([p(9 + length * 0.5, f0 - c), p(9 + length * 0.5, f0 + c)], INK, 0.9)], far=far, s=1.2, sw=FINE + 0.4)
    palm = svg.smooth([p(-3, -7.0, ), p(6, -7.6), (lambda z: z + (True,))(p(11, -7.2)), (lambda z: z + (True,))(p(11.5, 7.0)), p(6, 7.4), p(-3, 7.0)])
    items = [line([p(9.5, -6), p(9.5, 6)], INK, 1.0)] + rivets([p(3, -3.5), p(3, 3.5)], 0.55)
    out += paint(palm, key, items, far=far, s=2.5, sw=OUT - 0.6)
    return out


def steel_foot(ankle, far=False):
    """The footing: a sole plate bolted down under a heel block and a toe cap."""
    x, y = ankle
    g = GROUND
    shoe = svg.smooth([(x - 13, y - 8), (x + 6, y - 9), (x + 22, y - 2), (x + 31, g - 6, True), (x + 32, g, True), (x - 15, g, True), (x - 15, y + 2, True)])
    items = [line([(x - 15, g - 5), (x + 32, g - 5)], INK, 1.0)]
    if O["style"] == "girder" or O["style"] == "pier":
        items += [clone("bolt", x - 8, g - 2.6, 0.42), clone("bolt", x + 24, g - 2.6, 0.42)]
    out = paint(shoe, "plate", items, far=far, s=3)
    if O["style"] == "forged":
        out.append(line([(x - 12, y - 4), (x + 18, y - 1)], O["temper"][0], 1.2))
    return out


# ============================================================================================
# STEEL: torso, pelvis, neck, head (side)
# ============================================================================================

STEEL_TORSO = [(264, 224), (253, 234), (249, 258), (249, 294), (253, 322), (257, 346, True), (306, 346, True), (313, 322), (322, 294), (328, 268),
               (324, 244), (306, 228)]


def steel_torso_side() -> List[str]:
    style = O["style"]
    d = svg.smooth(STEEL_TORSO)
    items: List[str] = []
    if style == "girder":
        # lap seams: a riveted strap across the chest and one above the waist
        for y0, x0, x1 in ((282, 250, 320), (318, 254, 312)):
            items += [path(poly([(x0, y0 - 4), (x1, y0 - 4), (x1, y0 + 4), (x0, y0 + 4)]), O["plate_sh"]), line([(x0, y0 - 4), (x1, y0 - 4)], INK, 1.0),
                      line([(x0, y0 + 4), (x1, y0 + 4)], INK, 1.0)]
            items += rivet_run((x0 + 6, y0), (x1 - 6, y0), 7, 0.75)
        # the builder's plate
        items += [svg.ellipse(306, 262, 9, 6.5, O["brass"], INK, 1.2), svg.ellipse(306, 262, 6.5, 4.2, "none", O["brass_sh"], 0.9),
                  line([(301, 262), (311, 262)], O["brass_sh"], 0.9)]
        items += rivets([(262, 300), (262, 336)], 0.75)
    elif style == "forged":
        tc = O["temper"]
        # a coat of plates: lapels and a buttoned front, temper colours along the edges
        items += [path(svg.smooth([(300, 232), (316, 250), (312, 280), (300, 346, True), (290, 346, True), (296, 280), (292, 244)]), O["plate_sh"]),
                  line([(300, 232), (316, 250), (312, 280), (300, 346)], INK, 1.2)]
        items += [line([(262, 240), (300, 236)], tc[0], 1.4), line([(256, 300), (300, 300)], O["plate_sh"], 1.3)]
        items += rivets([(306, 266), (305, 290), (303, 314)], 0.85)
    else:
        # a riveted box chest; the X-braced lattice is the pelvis' (the waist)
        items += [path(poly([(254, 300), (314, 300), (312, 306), (255, 306)]), O["plate_sh"]), line([(254, 300), (316, 300)], INK, 1.0)]
        items += rivet_run((260, 240), (260, 330), 6, 0.7) + rivet_run((300, 238), (312, 290), 4, 0.7)
        items += rivet_run((262, 303), (308, 303), 6, 0.6)
    return paint(d, "plate", items, s=6)


def steel_pelvis_side() -> List[str]:
    style = O["style"]
    if style == "forged":
        # the coat's skirt of plates to mid thigh, split at the side
        d = svg.smooth([(256, 330, True), (306, 330, True), (312, 362), (316, 396, True), (290, 400), (262, 398, True), (252, 364)])
        tc = O["temper"]
        items = [line([(258, 362), (312, 362)], INK, 1.1), line([(258, 381), (315, 381)], INK, 1.1), line([(263, 395), (314, 393)], tc[1], 1.4),
                 path(poly([(256, 330), (308, 330), (308, 342), (256, 342)]), O["plate_sh"]), clone("bolt", 296, 336, 0.6)]
        return paint(d, "plate", items, s=5)
    d = svg.smooth([(256, 332, True), (306, 332, True), (310, 356), (302, 374), (264, 374), (253, 356)])
    items = [path(poly([(250, 332), (312, 332), (312, 346), (250, 346)]), O["girder"] if style == "girder" else O["plate_sh"]),
             line([(250, 332), (312, 332)], INK, 1.0), line([(250, 346), (312, 346)], INK, 1.0)]
    items += rivet_run((260, 339), (304, 339), 5, 0.7)
    if style == "pier":
        items += [line([(262, 348), (302, 372)], INK, 2.6), line([(302, 348), (262, 372)], INK, 2.6),
                  line([(262, 348), (302, 372)], O["plate_lt"], 1.2), line([(302, 348), (262, 372)], O["plate_lt"], 1.2)]
    return paint(d, "plate", items, s=5)


def steel_neck_side() -> List[str]:
    d = svg.smooth([(268, 204), (298, 202), (306, 234, True), (258, 234, True)])
    items = [path(poly([(256, 224), (308, 224), (308, 234), (256, 234)]), O["plate_sh"]), line([(256, 224), (308, 224)], INK, 1.0)]
    items += rivet_run((266, 229), (300, 229), 5, 0.6)
    return paint(d, "plate", items, s=4)


#: The steel head about the eye (unit = 1 at ``hk``): a square jaw, a strong
#: straight nose, a heavy brow; the ear a bolted boss, a riveted crest seam.
STEEL_HEAD = [(-20, -38), (-2, -35), (8, -26), (12, -13, True), (9, -7), (12, 1), (20, 14, True), (12, 17, True), (13, 23), (11, 27), (13, 31),
              (12, 40, True), (5, 45), (-16, 42), (-30, 34, True), (-39, 24), (-47, 8), (-46, -16), (-36, -32)]


def steel_head_side(mouth_open=False) -> List[str]:
    style = O["style"]
    t = head_xf()
    hk = G["hk"]
    d = svg.smooth(HP(STEEL_HEAD))
    items: List[str] = []
    # the face plane: a lighter band down the profile
    items.append(path(svg.smooth(HP([(-10, 4), (8, 4), (14, 30), (4, 44), (-20, 40), (-26, 26)])), mix(O["plate"], O["plate_sh"], 0.45)))
    # brow ridge shading, the cheek plane, the jaw plate seam
    items += [path(svg.smooth(HP([(-12, -10), (13, -14, True), (9, -5), (-8, -2)])), O["plate_sh"]),
              line(HP([(-31, 31), (-18, 39), (-6, 42)]), INK, 1.0),
              line(HP([(-14, -6), (-10, 14), (-6, 22)]), O["plate_sh"], 1.4)]
    # the eye: deep-set, calm, a heavy lid
    ex, ey = t(0, 0)
    items += [svg.ellipse(ex - 0.5, ey + 0.5, 4.6 * hk * 1.3, 3.0 * hk * 1.3, O["eye"], INK, 1.0),
              circle(ex + 1.6, ey + 0.6, 2.2 * hk * 1.3, O["iris"]), circle(ex + 1.9, ey + 0.6, 1.0 * hk * 1.3, INK),
              line(HP([(-7, -4.5), (0, -6.2), (7, -3.4)]), INK, 1.8)]
    # nostril, the closed mouth (a level line, a hint of a smile), the chin cleft
    items += [line(HP([(12, 15), (15, 13)]), INK, 1.1), line(HP([(4, 27), (13, 26.5)]), INK, 1.5), line(HP([(3, 26), (5, 28.5)]), INK, 1.0)]
    # the ear: a bolted boss; the crest seam with rivets
    bx, by = t(-24, 6)
    items += [svg.ellipse(bx, by, 7.0, 9.0, O["plate_sh"], INK, 1.2), clone("bolt", bx, by, 0.75)]
    if style == "pier":
        dome = HP([(-44, -14), (-36, -34), (-18, -42), (0, -38), (10, -24), (13, -15, True), (-46, -10, True)])
        items += [path(svg.smooth(dome), O["girder"]), line(HP([(-46, -12), (12, -15)]), INK, 1.4)]
        items += rivets(HP([(-38, -16), (-26, -17), (-12, -17), (2, -16)]), 0.7)
    else:
        items += rivets(HP([(-40, -22), (-28, -33), (-12, -37)]), 0.7)
    if style == "forged":
        beard = HP([(-26, 30), (-12, 30), (2, 33), (12, 31), (15, 40), (10, 54), (0, 60, True), (-10, 52), (-22, 44)])
        bd = svg.smooth(beard)
        items += cel(bd, mix(O["plate"], "#000000", 0.25), dark(O["plate"], 0.5), O["plate_lt"],
                     [line(HP([(x, 32), (x + 2, 50)]), O["plate_lt"], 0.9) for x in (-16, -8, 0, 6)], s=3)
        items += [line(HP([(6, 24), (14, 24), (16, 29)]), INK, 2.2)]
    return paint(d, "plate", items, s=5)


def steel_mouth_open() -> List[str]:
    """The talking mouth: the lips part on a dark slot."""
    d = svg.smooth(HP([(4, 26.5, True), (13, 25.8, True), (12.5, 29.5), (6, 30)]))
    return [path(d, "#2a1a16", INK, 1.2), line(HP([(6.5, 26.7), (12, 26.3)]), "#e9e2cf", 0.9)]


# ============================================================================================
# STRAW: strands, ties, stray straws
# ============================================================================================

def _rng(tag):
    return random.Random(f"{O['look']}:{tag}")


def strands(a, b, r0, r1, n, tag, far=False, lean=0.0):
    """Straws along a bundle from ``a`` to ``b``: light and shade lines with
    a little jitter (seeded, so a redraw is the same)."""
    rnd = _rng(tag)
    p = frame(a, ang(a, b))
    L = dist(a, b)
    out = []
    for i in range(n):
        s = -1 + 2 * (i + 0.5) / n + rnd.uniform(-0.12, 0.12)
        t0, t1 = rnd.uniform(-0.05, 0.15) * L, rnd.uniform(0.85, 1.05) * L
        col = O["straw_sh"] if (i % 3 == 0 or far) else (O["straw_lt"] if i % 3 == 1 else mix(O["straw"], O["straw_sh"], 0.5))
        out.append(line([p(t0, s * r0 * 0.92), p((t0 + t1) / 2, s * (r0 + r1) / 2 * 0.92 + lean), p(t1, s * r1 * 0.92)], col, 1.25, closed=False))
    return out


def weave(a, b, r0, r1, tag):
    """Wicker: rows of woven bands across the piece."""
    p = frame(a, ang(a, b))
    L = dist(a, b)
    out = []
    n = max(2, int(L / 7))
    for i in range(n + 1):
        t = L * i / n
        r = r0 + (r1 - r0) * i / n
        out.append(line([p(t - 1.5, -r), p(t + 1.8, 0), p(t - 1.5, r)], O["straw_sh"], 1.3))
        out.append(line([p(t + 1.6, -r * 0.8), p(t + 3.4, 0)], O["straw_lt"], 0.9))
    out += [line([p(0, -r0 * 0.15), p(L, -r1 * 0.15)], O["twine_sh"], 0.8)]
    return out


def plait(a, b, r0, r1):
    """A corn-dolly plait: chevrons down the piece."""
    p = frame(a, ang(a, b))
    L = dist(a, b)
    out = []
    n = max(2, int(L / 6.5))
    for i in range(n):
        t = L * (i + 0.5) / n
        r = r0 + (r1 - r0) * (i + 0.5) / n
        out += [path(svg.smooth([p(t - 3, -r), p(t + 2.5, -r * 0.1), p(t - 1, 0), p(t - 5, -r * 0.8)]), O["straw_lt"], INK, 0.7),
                path(svg.smooth([p(t - 3, r), p(t + 2.5, r * 0.1), p(t - 1, 0), p(t - 5, r * 0.8)]), O["straw"], INK, 0.7)]
    return out


def texture(a, b, r0, r1, tag, far=False):
    style = O["style"]
    if style == "wicker":
        return weave(a, b, r0, r1, tag)
    if style == "dolly":
        return plait(a, b, r0, r1)
    return strands(a, b, r0, r1, max(5, int((r0 + r1) * 0.55)), tag, far=far)


def tie(c, a, r, ribbon=False):
    """A binding round a bundle at ``c`` (the bundle runs at angle ``a``)."""
    p = frame(c, a)
    key = "ribbon" if ribbon else "twine"
    d = poly([p(-2.6, -r - 1.2), p(2.6, -r - 1.2), p(2.6, r + 1.2), p(-2.6, r + 1.2)])
    return cel(d, O[key], O[key + "_sh"], O[key + "_lt"], [line([p(0, -r - 1), p(0, r + 1)], O[key + "_sh"], 0.8)], s=1.2, sw=FINE)


def strays(base_pts, tag, k=1.0):
    """A few loose straws sticking out (clones of one straw end)."""
    rnd = _rng(tag)
    return [clone("straw-end", x, y, k * rnd.uniform(0.75, 1.15), a + rnd.uniform(-12, 12)) for x, y, a in base_pts]


def frayed(a, b, r0, r1, tag, step=5.0):
    """A loose bundle's outline from ``a`` to ``b``: it bellies between its
    ties, and straw tips stick out of both edges and both cut ends."""
    rnd = _rng("fray" + tag)
    L = dist(a, b)
    p = frame(a, ang(a, b))
    n = max(3, int(L / step))

    def edge(sign):
        pts = []
        for i in range(n + 1):
            t = L * i / n
            r = (r0 + (r1 - r0) * i / n) * (1.0 + 0.16 * math.sin(math.pi * i / n))
            pts.append(p(t, sign * r))
            if 0 < i < n and rnd.random() < 0.0:
                pts.append(p(t + step * 0.4, sign * (r + rnd.uniform(1.6, 3.6))) + (True,))
                pts.append(p(t + step * 0.55, sign * r) + (True,))
        return pts

    def end(c, r, base, sign):
        pts = []
        for j in range(5):
            th = base + sign * math.pi * (j + 0.5) / 5
            k = r * (1.0 + rnd.uniform(0.05, 0.35) * (j % 2))
            pts.append((c[0] + math.cos(th) * k, c[1] + math.sin(th) * k) + ((True,) if j % 2 else ()))
        return pts

    a0 = ang(a, b)
    top = edge(-1)
    bot = list(reversed(edge(1)))
    pts = top + end(b, r1 * 0.9, a0 - math.pi / 2, 1) + bot + end(a, r0 * 0.9, a0 + math.pi / 2, 1)
    return svg.smooth(pts)


def straw_piece(a, b, r0, r1, tag, far=False, tie_b=True, frayed_b=False):
    """An arm or leg bundle of straw from ``a`` to ``b``, tied at ``b``."""
    L = dist(a, b)
    p = frame(a, ang(a, b))
    style = O["style"]
    if style == "sheaf":
        d = frayed(a, b, r0, r1, tag)
    else:
        d = capsule(a, b, r0, r1)
    out = paint(d, "straw", texture(a, b, r0, r1, tag, far=far), far=far, s=3)
    if style == "sheaf" and not far:
        rnd = _rng("stray" + tag)
        deg = math.degrees(ang(a, b))
        picks = []
        for t, sign in ((rnd.uniform(0.2, 0.45), -1), (rnd.uniform(0.55, 0.85), 1)):
            r = r0 + (r1 - r0) * t
            x, y = p(L * t, sign * r * 0.9)
            picks.append((x, y, deg + sign * rnd.uniform(25, 50)))
        out += strays(picks, "s" + tag, 0.6)
    if tie_b:
        out += tie(b, ang(a, b), r1 * (0.8 if style == "sheaf" else 0.95), ribbon=False)
    return out


def straw_hand(wrist, a, far=False, tag="hand"):
    """A hand: a tuft of straw splayed into four 'fingers' and a thumb, tied at the wrist."""
    q = frame(wrist, a)
    out: List[str] = []
    rnd = _rng(tag)
    fingers = [(-4.2, 16, -0.25), (-1.4, 18, -0.05), (1.4, 17, 0.12), (4.0, 14, 0.3)]
    thumb = (5.0, 11, 0.85)
    for s0, length, spread in fingers + [thumb]:
        a0 = q(4, s0)
        tip = q(4 + length * math.cos(spread), s0 + length * math.sin(spread) * 0.9 + rnd.uniform(-1, 1))
        p = frame(a0, ang(a0, tip))
        L = dist(a0, tip)
        fd = svg.smooth([p(0, -2.4), p(L * 0.6, -2.0), (lambda z: z + (True,))(p(L + 1.5, 0)), p(L * 0.6, 2.0), p(0, 2.4)])
        out += paint(fd, "straw", [line([p(1, 0), p(L - 1, 0)], O["straw_sh"], 0.6)], far=far, s=1.0, sw=FINE + 0.4)
    knot = svg.smooth([q(-2, -5.5), q(6, -6.2), q(8, 0), q(6, 6.2), q(-2, 5.5)])
    out += paint(knot, "straw", [line([q(0, -4), q(7, -4.5)], O["straw_sh"], 0.6)], far=far, s=1.5, sw=FINE + 0.8)
    out += tie(q(0, 0), a, 5.2)
    return out


def straw_foot(ankle, far=False, tag="foot"):
    """A foot: the bundle's cut ends splayed forward on the ground like a broom."""
    x, y = ankle
    g = GROUND
    d = svg.smooth([(x - 9, y - 6), (x + 6, y - 6), (x + 20, g - 9), (x + 30, g - 3, True), (x + 27, g, True), (x - 12, g, True), (x - 12, y + 4)])
    items = strands((x - 6, g - 4), (x + 28, g - 3), 4, 3, 5, tag + "s", far=far) + strands((x, y - 4), (x + 4, g), 6, 8, 6, tag + "v", far=far)
    out = paint(d, "straw", items, far=far, s=2.5)
    out += strays([(x + 24, g - 4, -8), (x + 20, g - 8, -30)], tag, 0.8)
    out += tie((x, y - 2), math.pi / 2, 6.5)
    return out


# ============================================================================================
# STRAW: torso, skirt, neck, head (side)
# ============================================================================================

STRAW_TORSO = [(272, 244), (262, 258), (260, 284), (264, 312), (268, 334, True), (298, 334, True), (306, 312), (318, 288), (322, 268), (314, 252),
               (298, 242)]


def straw_torso_side() -> List[str]:
    style = O["style"]
    d = svg.smooth(STRAW_TORSO)
    if style == "wicker":
        items = weave((290, 244), (283, 334), 30, 18, "torso")
    elif style == "dolly":
        items = plait((292, 246), (284, 334), 26, 16) + plait((272, 250), (272, 330), 10, 8)
    else:
        items = strands((290, 244), (283, 336), 30, 17, 16, "torso", lean=2.0)
    out = paint(d, "straw", items, s=5)
    out += strays([(318, 278, -20), (262, 270, 200), (314, 300, 10), (266, 300, 160)], "torso")
    if style == "sheaf":
        # the rosette he gave himself
        cx, cy = 312, 272
        petals = svg.smooth([(cx + 9.5 * math.cos(t) * (1 + 0.12 * (i % 2)), cy + 9.5 * math.sin(t) * (1 + 0.12 * (i % 2)))
                             for i, t in enumerate(j * math.pi / 8 for j in range(16))])
        out += [path(svg.smooth([(cx - 3, cy + 4), (cx - 8, cy + 24, True), (cx - 4, cy + 20), (cx - 1, cy + 25, True), (cx + 1, cy + 5)]), O["ribbon"], INK, 1.1),
                path(svg.smooth([(cx + 1, cy + 4), (cx + 4, cy + 23, True), (cx + 6, cy + 19), (cx + 10, cy + 22, True), (cx + 4, cy + 3)]), O["ribbon_sh"], INK, 1.1)]
        out += cel(petals, O["ribbon"], O["ribbon_sh"], O["ribbon_lt"], [], s=2, sw=1.4)
        out += [circle(cx, cy, 4.6, O["brass"] if "brass" in O else "#d9b24a", INK, 1.1), circle(cx - 1, cy - 1, 1.6, "#f4e3a0")]
    return out


def straw_skirt_side() -> List[str]:
    """Below the waist tie the sheaf flares into a fringe of cut ends."""
    style = O["style"]
    if style == "wicker":
        d = svg.smooth([(266, 330, True), (300, 330, True), (306, 352), (302, 366, True), (262, 366, True), (260, 350)])
        out = paint(d, "straw", weave((283, 330), (283, 366), 22, 22, "hips"), s=4)
        return out + tie((283, 333), 0.0, 1, ribbon=False)[:0] + [line([(264, 333), (304, 333)], O["twine"], 4.0), line([(264, 333), (304, 333)], INK, 0.8)]
    pts = [(268, 328, True), (298, 328, True), (308, 350), (316, 372, True), (308, 368), (304, 378, True), (296, 370), (288, 380, True), (282, 370),
           (272, 379, True), (266, 368), (256, 374, True), (258, 352)]
    d = svg.smooth(pts)
    items = strands((283, 328), (283, 378), 16, 26, 14, "skirt", lean=1.0) if style == "sheaf" else plait((283, 330), (283, 374), 16, 24)
    out = paint(d, "straw", items, s=4)
    out += strays([(310, 366, 60), (258, 368, 130), (296, 374, 95)], "skirt")
    # the waist binding
    band = poly([(264, 326), (302, 326), (303, 336), (263, 336)])
    key = "ribbon" if style == "dolly" else "twine"
    out += cel(band, O[key], O[key + "_sh"], O[key + "_lt"], [line([(270, 331), (296, 331)], O[key + "_sh"], 0.8)], s=2, sw=FINE + 0.4)
    knot = svg.smooth([(298, 328), (310, 326), (314, 334), (304, 338)])
    out += cel(knot, O[key], O[key + "_sh"], None, [], s=1.5, sw=FINE)
    for tail in ([(308, 336), (313, 349), (312, 354)], [(305, 337), (304, 350), (306, 355)]):
        out += [line(tail, INK, 3.4), line(tail, O[key], 1.8)]
    return out


def straw_neck_side() -> List[str]:
    d = svg.smooth([(274, 222), (294, 220), (298, 250, True), (272, 250, True)])
    out = paint(d, "straw", strands((284, 220), (285, 250), 11, 12, 6, "neck"), s=3)
    key = "ribbon" if O["style"] == "dolly" else "twine"
    band = poly([(271, 236), (297, 235), (298, 243), (271, 244)])
    out += cel(band, O[key], O[key + "_sh"], O[key + "_lt"], [], s=1.5, sw=FINE + 0.4)
    if O["style"] == "dolly":
        out += [path(svg.smooth([(296, 238), (308, 230, True), (310, 242, True)]), O["ribbon"], INK, 1.2),
                path(svg.smooth([(296, 240), (305, 252, True), (299, 254, True)]), O["ribbon_sh"], INK, 1.2)]
    return out


#: The straw head about the eye: an egg tipped back (chin up), the bundle's
#: top flaring into the quiff; the nose a tied stub.
STRAW_HEAD = [(-30, -30), (-8, -36), (10, -30), (18, -16), (20, -4), (22, 10), (20, 22), (14, 32), (2, 38), (-14, 38), (-28, 30), (-38, 14),
              (-40, -6)]


def straw_head_side() -> List[str]:
    style = O["style"]
    t = head_xf()
    hk = G["hk"]
    out: List[str] = []
    # the quiff behind the head: wheat ears swept back, or a wicker crest, or a plaited loop
    if style == "sheaf":
        for x, y, a in ((-34, -20, -70), (-24, -30, -52), (-12, -35, -34), (0, -35, -18)):
            X, Y = t(x, y)
            out.append(clone("wheat-ear", X, Y, 0.95, a))
    elif style == "dolly":
        loop = svg.smooth(HP([(-14, -32), (-22, -58), (-6, -70), (8, -60), (2, -32)]))
        out += cel(loop, O["straw"], O["straw_sh"], O["straw_lt"], plait(t(-4, -34), t(-6, -66), 6, 4), s=2)
        X, Y = t(-6, -66)
        out += [clone("wheat-ear", X, Y, 0.8, -10), clone("wheat-ear", X, Y, 0.8, 18)]
    d = svg.smooth(HP(STRAW_HEAD))
    if style == "wicker":
        items = [line(HP([(-40, y), (-10, y + 3), (20, y)]), O["straw_sh"], 1.5) for y in range(-30, 40, 7)]
        items += [line(HP([(x, -36), (x + 4, 0), (x, 38)]), O["straw_lt"], 1.0) for x in range(-34, 20, 9)]
    elif style == "dolly":
        items = plait(t(-10, -36), t(-8, 38), 22, 18)
    else:
        items = strands(t(-8, -36), t(-6, 40), 26 * hk, 22 * hk, 13, "head", lean=1.5)
    # the face: a smoother patch where the straw is pressed flat
    items.append(path(svg.smooth(HP([(-6, -22), (14, -18), (20, 6), (16, 26), (2, 34), (-10, 18)])), O["straw_lt"]))
    for x, y in ((-2, -10), (4, 14), (10, 22), (-4, 26)):
        items.append(line(HP([(x, y), (x + 8, y + 2)]), O["straw_sh"], 0.7))
    out += paint(d, "straw", items, s=5)
    # the seed eye under a cocked straw brow
    ex, ey = t(6, 0)
    out += smug_eye(ex, ey)
    out += [path(svg.smooth(HP([(-3, -12), (6, -16), (16, -13), (16, -11.5), (6, -14), (-3, -10)])), O["straw_sh"], INK, 1.2)]
    # the nose: a short tied stub of straw
    nose = svg.smooth(HP([(16, 0), (30, 4), (32, 8, True), (18, 11)]))
    out += cel(nose, O["straw"], O["straw_sh"], O["straw_lt"], [line(HP([(18, 5), (30, 6.5)]), O["straw_sh"], 0.6)], s=1.5, sw=FINE + 0.6)
    out += [line(HP([(20, 1.5), (20, 10.5)]), O["twine"], 2.2), line(HP([(20, 1.5), (20, 10.5)]), INK, 0.6)]
    # the smug grin: one side of the mouth pulled up
    out += [line(HP([(0, 22), (8, 25), (16, 21), (19, 17)]), INK, 1.8)]
    if style == "wicker":
        out += [line(HP([(-36, 14), (-32, 0)]), O["twine_sh"], 1.2)]
    # loose straws escaping the head
    X, Y = t(-38, 2)
    X2, Y2 = t(-32, 26)
    out += strays([(X, Y, 196), (X2, Y2, 150)], "head-loose")
    return out


def smug_eye(ex, ey):
    """A seed eye under a heavy lid: half shut, pleased with itself."""
    return [svg.ellipse(ex, ey + 0.3, 2.8, 3.3, O["seed"], INK, 0.8), circle(ex + 1.0, ey + 1.0, 0.8, "#f6efd8"),
            path(f"M{svg.pt((ex - 3.6, ey - 0.2))} L{svg.pt((ex - 3.6, ey - 4.5))} L{svg.pt((ex + 3.6, ey - 4.5))} L{svg.pt((ex + 3.6, ey - 0.6))} Z",
                 mix(O["straw_lt"], O["straw"], 0.4)),
            line([(ex - 4.0, ey + 0.1), (ex, ey - 1.0), (ex + 4.0, ey - 0.5)], INK, 1.7)]


def straw_mouth_open() -> List[str]:
    d = svg.smooth(HP([(1, 21.5, True), (17, 19, True), (14, 27), (6, 29)]))
    return [path(d, "#3a2216", INK, 1.4)]


# ============================================================================================
# the side view as rig parts
# ============================================================================================

def side_parts() -> List[Tuple[str, str, Callable[[], List[str]]]]:
    """The look's side view as ``(part, bone, painter)``, back to front."""
    g = G
    st = O["who"] == "steel"
    L: List[Tuple[str, str, Callable[[], List[str]]]] = []
    if st:
        L += [("far_arm_u", "far_arm_u", lambda: steel_piece(g["f_sh"], g["f_el"], *g["r_up"], far=True)),
              ("far_arm_l", "far_arm_l", lambda: steel_piece(g["f_el"], g["f_wr"], *g["r_fore"], far=True, boss_at_b=False)),
              ("far_hand", "far_hand", lambda: steel_hand(g["f_wr"], ang(g["f_el"], g["f_wr"]), far=True))]
        for side, far in (("far", True), ("near", False)):
            pre = side[0]
            L += [(f"{side}_shin", f"{side}_leg_l", lambda pre=pre, far=far: steel_piece(g[f"{pre}_knee"], g[f"{pre}_ank"], *g["r_shin"], far=far,
                                                                                          boss_at_b=False)),
                  (f"{side}_thigh", f"{side}_leg_u", lambda pre=pre, far=far: steel_piece(g[f"{pre}_hip"], g[f"{pre}_knee"], *g["r_thigh"], far=far)),
                  (f"{side}_foot", f"{side}_foot", lambda pre=pre, far=far: steel_foot(g[f"{pre}_ank"], far=far))]
        L += [("pelvis", "body", steel_pelvis_side), ("torso", "torso", steel_torso_side), ("neck", "torso", steel_neck_side),
              ("head", "head", steel_head_side), ("mouth_open", "head", steel_mouth_open),
              ("near_arm_u", "near_arm_u", lambda: steel_piece(g["n_sh"], g["n_el"], *g["r_up"], boss_at_a=True)),
              ("near_arm_l", "near_arm_l", lambda: steel_piece(g["n_el"], g["n_wr"], *g["r_fore"], boss_at_b=False)),
              ("near_hand", "near_hand", lambda: steel_hand(g["n_wr"], ang(g["n_el"], g["n_wr"])))]
        if O["style"] == "girder":
            # the shoulder gusset: a riveted plate over the near shoulder joint
            L.insert(L.index(next(x for x in L if x[0] == "near_arm_u")) + 1, ("near_pauldron", "near_arm_u", steel_pauldron))
        else:
            L.insert(L.index(next(x for x in L if x[0] == "near_arm_u")) + 1, ("near_pauldron", "near_arm_u", steel_pauldron))
        return L
    L += [("far_arm_u", "far_arm_u", lambda: straw_piece(g["f_sh"], g["f_el"], *g["r_up"], "fau", far=True)),
          ("far_arm_l", "far_arm_l", lambda: straw_piece(g["f_el"], g["f_wr"], *g["r_fore"], "fal", far=True, tie_b=False)),
          ("far_hand", "far_hand", lambda: straw_hand(g["f_wr"], ang(g["f_el"], g["f_wr"]), far=True, tag="fh"))]
    for side, far in (("far", True), ("near", False)):
        pre = side[0]
        L += [(f"{side}_shin", f"{side}_leg_l", lambda pre=pre, far=far: straw_piece(g[f"{pre}_knee"], g[f"{pre}_ank"], *g["r_shin"], pre + "s", far=far,
                                                                                      tie_b=False)),
              (f"{side}_thigh", f"{side}_leg_u", lambda pre=pre, far=far: straw_piece(g[f"{pre}_hip"], g[f"{pre}_knee"], *g["r_thigh"], pre + "t", far=far)),
              (f"{side}_foot", f"{side}_foot", lambda pre=pre, far=far: straw_foot(g[f"{pre}_ank"], far=far, tag=pre + "f"))]
    L += [("skirt", "body", straw_skirt_side), ("torso", "torso", straw_torso_side), ("neck", "torso", straw_neck_side),
          ("head", "head", straw_head_side), ("mouth_open", "head", straw_mouth_open),
          ("near_arm_u", "near_arm_u", lambda: straw_piece(g["n_sh"], g["n_el"], *g["r_up"], "nau")),
          ("near_arm_l", "near_arm_l", lambda: straw_piece(g["n_el"], g["n_wr"], *g["r_fore"], "nal", tie_b=False)),
          ("near_hand", "near_hand", lambda: straw_hand(g["n_wr"], ang(g["n_el"], g["n_wr"]), tag="nh"))]
    L += [(name, name, lambda name=name: chaff(name)) for name in CHAFF]
    return L


def steel_pauldron() -> List[str]:
    """A plate over the near shoulder: riveted (girder), a layered spaulder
    (forged), a gusset with a cable eye (pier)."""
    x, y = G["n_sh"]
    style = O["style"]
    d = svg.smooth([(x - 22, y + 6), (x - 18, y - 12), (x - 2, y - 19), (x + 16, y - 14), (x + 23, y + 2), (x + 18, y + 16, True), (x - 18, y + 16, True)])
    if style == "forged":
        tc = O["temper"]
        items = [line([(x - 20, y + 4), (x + 21, y + 4)], INK, 1.1), line([(x - 19, y + 12), (x + 20, y + 12)], tc[0], 1.4),
                 line([(x - 16, y - 8), (x + 14, y - 10)], tc[2], 1.2)]
    else:
        items = rivet_run((x - 16, y + 11), (x + 16, y + 11), 5, 0.75) + rivets([(x - 12, y - 6), (x, y - 12), (x + 12, y - 7)], 0.75)
        if style == "girder":
            items.insert(0, path(svg.smooth([(x - 22, y + 6), (x + 23, y + 2), (x + 18, y + 16, True), (x - 18, y + 16, True)]), O["girder"]))
    return paint(d, "plate", items, s=4)


def side_joints() -> Dict[str, Tuple[str, float, float]]:
    """Where each bone turns: ``bone: (parent, x, y)``, parents first."""
    g = G
    J = {
        "body": ("", *g["body"]),
        "torso": ("body", *g["body"]),
        "head": ("torso", *g["neck"]),
        "near_arm_u": ("torso", *g["n_sh"]), "near_arm_l": ("near_arm_u", *g["n_el"]), "near_hand": ("near_arm_l", *g["n_wr"]),
        "far_arm_u": ("torso", *g["f_sh"]), "far_arm_l": ("far_arm_u", *g["f_el"]), "far_hand": ("far_arm_l", *g["f_wr"]),
    }
    for side in ("near", "far"):
        pre = side[0]
        J[f"{side}_leg_u"] = ("body", *g[f"{pre}_hip"])
        J[f"{side}_leg_l"] = (f"{side}_leg_u", *g[f"{pre}_knee"])
        J[f"{side}_foot"] = (f"{side}_leg_l", *g[f"{pre}_ank"])
    if O["who"] == "straw":
        for name, (x, y, _a) in CHAFF.items():
            J[name] = ("body", x, y)
    return J


# ============================================================================================
# the front view (one drawing; the second cell)
# ============================================================================================

def fpt(side, xy):
    """A front-view joint: ``side`` -1 is his right (screen-left)."""
    return (CX + side * xy[0], xy[1])


def front_steel() -> List[str]:
    g = G
    style = O["style"]
    out: List[str] = []
    # legs, then pelvis, torso, arms, neck, head
    for side in (-1, 1):
        hip, knee, ank = fpt(side, g["fr_hip"]), fpt(side, g["fr_knee"]), fpt(side, g["fr_ank"])
        out += steel_piece(knee, ank, *g["r_shin"], boss_at_b=False)
        out += steel_piece(hip, knee, *g["r_thigh"])
        x, y = ank
        foot = svg.smooth([(x - 15, y - 8), (x + 15, y - 8), (x + 18, GROUND - 6, True), (x + 19, GROUND, True), (x - 19, GROUND, True), (x - 18, GROUND - 6, True)])
        out += paint(foot, "plate", [line([(x - 19, GROUND - 5), (x + 19, GROUND - 5)], INK, 1.0)] +
                     ([clone("bolt", x - 12, GROUND - 2.6, 0.42), clone("bolt", x + 12, GROUND - 2.6, 0.42)] if style != "forged" else []), s=3)
    if style == "forged":
        skirt = svg.smooth([(CX - 40, 330, True), (CX + 40, 330, True), (CX + 46, 398, True), (CX + 4, 400), (CX - 46, 398, True)])
        tc = O["temper"]
        out += paint(skirt, "plate", [line([(CX - 42, 362), (CX + 42, 362)], INK, 1.1), line([(CX - 44, 381), (CX + 44, 381)], INK, 1.1),
                                       line([(CX, 342), (CX, 400)], INK, 1.2), line([(CX - 45, 395), (CX + 45, 395)], tc[1], 1.4)], s=5)
    else:
        pel = svg.smooth([(CX - 40, 332, True), (CX + 40, 332, True), (CX + 40, 356), (CX + 16, 376, True), (CX - 16, 376, True), (CX - 40, 356)])
        items = [path(poly([(CX - 40, 332), (CX + 40, 332), (CX + 40, 346), (CX - 40, 346)]), O["girder"] if style == "girder" else O["plate_sh"]),
                 line([(CX - 40, 346), (CX + 40, 346)], INK, 1.0)] + rivet_run((CX - 32, 339), (CX + 32, 339), 7, 0.7)
        if style == "pier":
            items += [line([(CX - 22, 348), (CX + 22, 374)], INK, 2.6), line([(CX + 22, 348), (CX - 22, 374)], INK, 2.6),
                      line([(CX - 22, 348), (CX + 22, 374)], O["plate_lt"], 1.2), line([(CX + 22, 348), (CX - 22, 374)], O["plate_lt"], 1.2)]
        out += paint(pel, "plate", items, s=5)
    torso = svg.smooth([(CX - 22, 226), (CX - 56, 238), (CX - 62, 256), (CX - 56, 290), (CX - 40, 326), (CX - 36, 346, True), (CX + 36, 346, True),
                        (CX + 40, 326), (CX + 56, 290), (CX + 62, 256), (CX + 56, 238), (CX + 22, 226)])
    items: List[str] = []
    if style == "girder":
        for y0 in (282, 318):
            items += [path(poly([(CX - 60, y0 - 4), (CX + 60, y0 - 4), (CX + 60, y0 + 4), (CX - 60, y0 + 4)]), O["plate_sh"]),
                      line([(CX - 60, y0 - 4), (CX + 60, y0 - 4)], INK, 1.0), line([(CX - 60, y0 + 4), (CX + 60, y0 + 4)], INK, 1.0)]
            items += rivet_run((CX - 46, y0), (CX + 46, y0), 9, 0.75)
        items += [line([(CX, 236), (CX, 278)], INK, 1.1)] + rivet_run((CX - 5, 244), (CX - 5, 272), 4, 0.65) + rivet_run((CX + 5, 244), (CX + 5, 272), 4, 0.65)
        items += [svg.ellipse(CX + 26, 262, 10, 7, O["brass"], INK, 1.2), svg.ellipse(CX + 26, 262, 7, 4.6, "none", O["brass_sh"], 0.9)]
    elif style == "forged":
        tc = O["temper"]
        items += [path(svg.smooth([(CX - 16, 230), (CX - 30, 252), (CX - 8, 346, True), (CX + 8, 346, True), (CX + 30, 252), (CX + 16, 230)]), O["plate_sh"]),
                  line([(CX - 16, 230), (CX - 30, 252), (CX - 8, 346)], INK, 1.2), line([(CX + 16, 230), (CX + 30, 252), (CX + 8, 346)], INK, 1.2),
                  line([(CX - 50, 246), (CX - 20, 236)], tc[0], 1.4), line([(CX + 50, 246), (CX + 20, 236)], tc[0], 1.4)]
        items += rivets([(CX, 266), (CX, 290), (CX, 314)], 0.85)
    else:
        items += [path(poly([(CX - 56, 300), (CX + 56, 300), (CX + 56, 306), (CX - 56, 306)]), O["plate_sh"])]
        items += rivet_run((CX - 44, 242), (CX - 40, 330), 6, 0.7) + rivet_run((CX + 44, 242), (CX + 40, 330), 6, 0.7) + rivet_run((CX - 40, 303), (CX + 40, 303), 9, 0.6)
    out += paint(torso, "plate", items, s=6)
    for side in (-1, 1):
        sh, el, wr = fpt(side, g["fr_sh"]), fpt(side, g["fr_el"]), fpt(side, g["fr_wr"])
        out += steel_piece(sh, el, *g["r_up"])
        out += steel_piece(el, wr, *g["r_fore"], boss_at_b=False)
        out += steel_hand(wr, ang(el, wr) - side * 0.05)
        x, y = sh
        pd = svg.smooth([(x - 20, y + 10), (x - 16, y - 12), (x, y - 19), (x + 16, y - 12), (x + 20, y + 10), (x + 14, y + 18, True), (x - 14, y + 18, True)])
        if style == "forged":
            tc = O["temper"]
            pitems = [line([(x - 18, y + 4), (x + 18, y + 4)], INK, 1.1), line([(x - 16, y + 13), (x + 16, y + 13)], tc[0], 1.4)]
        else:
            pitems = rivet_run((x - 13, y + 12), (x + 13, y + 12), 4, 0.75) + rivets([(x - 9, y - 6), (x + 9, y - 6), (x, y - 12)], 0.75)
            if style == "girder":
                pitems.insert(0, path(poly([(x - 22, y + 6), (x + 22, y + 6), (x + 22, y + 20), (x - 22, y + 20)]), O["girder"]))
        out += paint(pd, "plate", pitems, s=4)
    neck = svg.smooth([(CX - 17, 204), (CX + 17, 204), (CX + 24, 236, True), (CX - 24, 236, True)])
    out += paint(neck, "plate", [path(poly([(CX - 18, 226), (CX + 18, 226), (CX + 18, 234), (CX - 18, 234)]), O["plate_sh"])] +
                 rivet_run((CX - 10, 230), (CX + 10, 230), 4, 0.6), s=3)
    out += front_steel_head()
    return out


def front_steel_head() -> List[str]:
    style = O["style"]
    t = head_xf("front")
    hk = G["hk"]
    pts = [(0, -38), (20, -34), (30, -20), (32, 0), (31, 16), (28, 30, True), (16, 42), (0, 45), (-16, 42), (-28, 30, True), (-31, 16), (-32, 0),
           (-30, -20), (-20, -34)]
    d = svg.smooth(HP(pts, "front"))
    shd = mix(O["plate"], O["plate_sh"], 0.6)
    items = [path(svg.smooth(HP([(-26, -12), (-4, -10), (0, -6, True), (4, -10), (26, -12), (24, -4), (4, -3), (0, 0, True), (-4, -3), (-24, -4)], "front")), shd),
             # the nose: lit on its right plane, shaded on its left; the cheekbones; the jaw plates
             path(svg.smooth(HP([(-3, -2), (-6, 14), (-8, 18, True), (-2, 20), (0, 16)], "front")), shd),
             line(HP([(-7, 18), (-2, 20.5), (2, 20.5), (7, 18)], "front"), INK, 1.3),
             line(HP([(-24, 10), (-17, 18), (-10, 20)], "front"), shd, 2.0), line(HP([(24, 10), (17, 18), (10, 20)], "front"), shd, 2.0),
             line(HP([(-10, 29), (0, 28.6), (10, 29)], "front"), INK, 1.7), line(HP([(-10.5, 29), (-12.5, 27.6)], "front"), INK, 1.0),
             line(HP([(10.5, 29), (12.5, 27.6)], "front"), INK, 1.0), line(HP([(-5, 35), (5, 35)], "front"), shd, 1.6),
             line(HP([(-27, 24), (-16, 40)], "front"), INK, 1.0), line(HP([(27, 24), (16, 40)], "front"), INK, 1.0)]
    for s in (-1, 1):
        ex, ey = t(s * 12, 2)
        items += [svg.ellipse(ex, ey, 5.0 * hk * 1.2, 3.0 * hk * 1.2, O["eye"], INK, 1.0), circle(ex, ey + 0.5, 2.2 * hk * 1.2, O["iris"]),
                  circle(ex, ey + 0.5, 1.0 * hk * 1.2, INK),
                  path(svg.smooth([(ex - 6.2, ey + 0.2), (ex - 3, ey - 3.6), (ex + 3, ey - 3.6), (ex + 6.2, ey + 0.2), (ex + 5.6, ey - 1.0), (ex, ey - 2.6), (ex - 5.6, ey - 1.0)]),
                       O["plate"], INK, 1.3)]
        bx, by = t(s * 33, 6)
        items += [svg.ellipse(bx, by, 5.5, 8.5, O["plate_sh"], INK, 1.2), clone("bolt", bx, by, 0.6)]
    if style == "pier":
        dome = HP([(-31, -14), (-28, -30), (-14, -40), (14, -40), (28, -30), (31, -14)], "front")
        items += [path(svg.smooth(dome + [t(31, -12) + (True,), t(-31, -12) + (True,)]), O["girder"]), line(HP([(-31, -13), (31, -13)], "front"), INK, 1.4)]
        items += rivets(HP([(-22, -17), (-8, -17), (8, -17), (22, -17)], "front"), 0.7)
    else:
        items += rivets(HP([(0, -34), (0, -24)], "front"), 0.7)
        items.append(line(HP([(0, -38), (0, -18)], "front"), INK, 0.9))
    if style == "forged":
        beard = HP([(-26, 24), (-14, 32), (0, 33), (14, 32), (26, 24), (22, 48), (8, 62), (0, 66, True), (-8, 62), (-22, 48)], "front")
        items += cel(svg.smooth(beard), mix(O["plate"], "#000000", 0.25), dark(O["plate"], 0.5), O["plate_lt"],
                     [line(HP([(x, 34), (x * 0.6, 58)], "front"), O["plate_lt"], 0.9) for x in (-16, -6, 6, 16)], s=3)
        items += [path(svg.smooth(HP([(-14, 26), (0, 22), (14, 26), (10, 30), (0, 27), (-10, 30)], "front")), mix(O["plate"], "#000000", 0.3), INK, 1.2)]
    return paint(d, "plate", items, s=5)


def front_straw() -> List[str]:
    g = G
    style = O["style"]
    out: List[str] = []
    for side in (-1, 1):
        hip, knee, ank = fpt(side, g["fr_hip"]), fpt(side, g["fr_knee"]), fpt(side, g["fr_ank"])
        out += straw_piece(knee, ank, *g["r_shin"], f"fs{side}", tie_b=False)
        out += straw_piece(hip, knee, *g["r_thigh"], f"ft{side}")
        x, y = ank
        foot = svg.smooth([(x - 8, y - 6), (x + 8, y - 6), (x + side * 4 + 16, GROUND - 4), (x + side * 6 + 14, GROUND, True), (x + side * 2 - 16, GROUND, True),
                           (x - 13, GROUND - 6)])
        out += paint(foot, "straw", strands((x, y - 6), (x + side * 3, GROUND), 7, 14, 7, f"ff{side}"), s=2.5)
        out += strays([(x + side * 14, GROUND - 3, 90 - side * 70)], f"ffs{side}", 0.7)
        out += tie((x, y - 2), math.pi / 2, 6.5)
    if style == "wicker":
        hips = svg.smooth([(CX - 22, 330, True), (CX + 22, 330, True), (CX + 26, 352), (CX + 24, 366, True), (CX - 24, 366, True), (CX - 26, 352)])
        out += paint(hips, "straw", weave((CX, 330), (CX, 366), 24, 24, "fh"), s=4)
    else:
        sk = [(CX - 22, 328, True), (CX + 22, 328, True), (CX + 34, 352), (CX + 40, 374, True), (CX + 30, 370), (CX + 24, 380, True), (CX + 14, 370),
              (CX + 4, 381, True), (CX - 6, 371), (CX - 16, 380, True), (CX - 26, 370), (CX - 38, 376, True), (CX - 34, 352)]
        out += paint(svg.smooth(sk), "straw", strands((CX, 328), (CX, 380), 22, 38, 18, "fsk") if style == "sheaf" else plait((CX, 330), (CX, 376), 20, 34), s=4)
        out += strays([(CX + 36, 368, 70), (CX - 34, 372, 115)], "fsks")
    key = "ribbon" if style == "dolly" else "twine"
    out += cel(poly([(CX - 24, 325), (CX + 24, 325), (CX + 25, 335), (CX - 25, 335)]), O[key], O[key + "_sh"], O[key + "_lt"], [], s=2, sw=FINE + 0.4)
    torso = svg.smooth([(CX - 14, 242), (CX - 36, 252), (CX - 44, 270), (CX - 38, 300), (CX - 22, 330, True), (CX + 22, 330, True), (CX + 38, 300),
                        (CX + 44, 270), (CX + 36, 252), (CX + 14, 242)])
    if style == "wicker":
        titems = weave((CX, 242), (CX, 332), 44, 24, "ft")
    elif style == "dolly":
        titems = plait((CX, 244), (CX, 332), 30, 18)
    else:
        titems = strands((CX, 242), (CX, 332), 44, 22, 22, "ftorso")
    out += paint(torso, "straw", titems, s=5)
    out += strays([(CX - 42, 268, 200), (CX + 42, 282, -10), (CX - 36, 300, 160)], "fts")
    if style == "sheaf":
        cx, cy = CX + 18, 270
        petals = svg.smooth([(cx + 9.5 * math.cos(t) * (1 + 0.12 * (i % 2)), cy + 9.5 * math.sin(t) * (1 + 0.12 * (i % 2)))
                             for i, t in enumerate(j * math.pi / 8 for j in range(16))])
        out += [path(svg.smooth([(cx - 3, cy + 4), (cx - 8, cy + 24, True), (cx - 4, cy + 20), (cx - 1, cy + 25, True), (cx + 1, cy + 5)]), O["ribbon"], INK, 1.1),
                path(svg.smooth([(cx + 1, cy + 4), (cx + 4, cy + 23, True), (cx + 6, cy + 19), (cx + 10, cy + 22, True), (cx + 4, cy + 3)]), O["ribbon_sh"], INK, 1.1)]
        out += cel(petals, O["ribbon"], O["ribbon_sh"], O["ribbon_lt"], [], s=2, sw=1.4)
        out += [circle(cx, cy, 4.6, "#d9b24a", INK, 1.1), circle(cx - 1, cy - 1, 1.6, "#f4e3a0")]
    for side in (-1, 1):
        sh, el, wr = fpt(side, g["fr_sh"]), fpt(side, g["fr_el"]), fpt(side, g["fr_wr"])
        out += straw_piece(sh, el, *g["r_up"], f"fa{side}")
        out += straw_piece(el, wr, *g["r_fore"], f"fl{side}", tie_b=False)
        out += straw_hand(wr, ang(el, wr) - side * 0.15, tag=f"fhand{side}")
    neck = svg.smooth([(CX - 11, 222), (CX + 11, 222), (CX + 12, 250, True), (CX - 12, 250, True)])
    out += paint(neck, "straw", strands((CX, 222), (CX, 250), 11, 12, 6, "fneck"), s=3)
    out += cel(poly([(CX - 13, 236), (CX + 13, 236), (CX + 13, 244), (CX - 13, 244)]), O[key], O[key + "_sh"], O[key + "_lt"], [], s=1.5, sw=FINE + 0.4)
    if style == "dolly":
        out += [path(svg.smooth([(CX + 4, 240), (CX + 18, 232, True), (CX + 19, 246, True)]), O["ribbon"], INK, 1.2),
                path(svg.smooth([(CX - 4, 240), (CX - 18, 232, True), (CX - 19, 246, True)]), O["ribbon"], INK, 1.2)]
    out += front_straw_head()
    return out


def front_straw_head() -> List[str]:
    style = O["style"]
    t = head_xf("front")
    out: List[str] = []
    if style == "sheaf":
        for x, y, a in ((2, -36, 8), (10, -34, 26), (17, -30, 44), (-6, -36, -6)):
            X, Y = t(x, y)
            out.append(clone("wheat-ear", X, Y, 0.95, a))
    elif style == "dolly":
        loop = svg.smooth(HP([(-8, -32), (-12, -60), (0, -70), (12, -60), (8, -32)], "front"))
        out += cel(loop, O["straw"], O["straw_sh"], O["straw_lt"], plait(t(0, -34), t(0, -66), 6, 4), s=2)
        X, Y = t(0, -66)
        out += [clone("wheat-ear", X, Y, 0.8, -18), clone("wheat-ear", X, Y, 0.8, 18)]
    pts = [(0, -38), (17, -34), (25, -18), (26, 4), (23, 26), (14, 40), (0, 46), (-14, 40), (-23, 26), (-26, 4), (-25, -18), (-17, -34)]
    d = svg.smooth(HP(pts, "front"))
    if style == "wicker":
        items = [line(HP([(-30, y), (0, y + 3), (30, y)], "front"), O["straw_sh"], 1.5) for y in range(-30, 40, 7)]
        items += [line(HP([(x, -36), (x * 1.2, 0), (x, 38)], "front"), O["straw_lt"], 1.0) for x in range(-24, 28, 9)]
    elif style == "dolly":
        items = plait(t(0, -36), t(0, 40), 24, 18)
    else:
        items = strands(t(0, -36), t(0, 40), 22, 18, 13, "fhead")
    items.append(path(svg.smooth(HP([(-18, -20), (18, -20), (20, 10), (10, 30), (-10, 30), (-20, 10)], "front")), O["straw_lt"]))
    out += paint(d, "straw", items, s=5)
    for s in (-1, 1):
        ex, ey = t(s * 11, 0)
        out += smug_eye(ex, ey)
    # brows: the left one cocked higher
    out += [path(svg.smooth(HP([(-20, -11), (-11, -14), (-3, -11), (-3, -9.5), (-11, -12), (-20, -9)], "front")), O["straw_sh"], INK, 1.2),
            path(svg.smooth(HP([(3, -14), (12, -19), (21, -16), (21, -14.5), (12, -17), (3, -12)], "front")), O["straw_sh"], INK, 1.2)]
    nose = svg.smooth(HP([(-3.5, 0), (3.5, 0), (6.5, 13), (0, 16, True), (-6.5, 13)], "front"))
    out += cel(nose, O["straw"], O["straw_sh"], O["straw_lt"], [], s=1.5, sw=FINE + 0.6)
    out += [line(HP([(-4.2, 5), (4.2, 5)], "front"), O["twine"], 2.2)]
    out += [line(HP([(-10, 28), (-1, 30), (8, 28), (13, 23)], "front"), INK, 1.8)]
    X, Y = t(-27, 0)
    X2, Y2 = t(27, 14)
    out += strays([(X, Y, 190), (X2, Y2, -10)], "fhead-loose")
    return out


# ============================================================================================
# the SVG: the side view's part layers (the cell at the origin) and the front view (the next cell)
# ============================================================================================

NAMES = {"steel": "Steel Man", "straw": "Straw Man"}
FILES = {"steel": "steel_man", "straw": "straw_man"}
SIDE_LABEL = "{name} - Side Right"
FRONT_LABEL = "{name} - Front"


def rig_drawing(who: str, look: str | None = None) -> Dict:
    """The look's side view as rig parts: ``parts`` is ``(part, bone, z,
    body)`` back to front; ``joints`` the bones in SVG units."""
    use(who, look or CAST[who])
    svg.configure(dx=0, dy=0, ink=INK, ow=OUT / 2, colors={})
    parts = [(name, bone, i, painter()) for i, (name, bone, painter) in enumerate(side_parts())]
    return {"parts": parts, "joints": side_joints(), "label": O["label"], "height": GROUND - G["crown"]}


#: Parts drawn only while a clip asks for them (``opacity_channel``): the
#: talking mouth and the Straw Man's falling straws.
SWITCHED = {"mouth_open", "chaff_1", "chaff_2", "chaff_3"}

#: The Straw Man's loose straws: where each sits on him before it falls
#: (its bone's joint) and the angle it lies at.
CHAFF = {"chaff_1": (306.0, 296.0, 64.0), "chaff_2": (262.0, 318.0, 118.0), "chaff_3": (300.0, 366.0, 84.0)}


def chaff(name: str) -> List[str]:
    x, y, a = CHAFF[name]
    out = []
    for da, k in ((-14, 1.25), (0, 1.5), (16, 1.15)):
        r = math.radians(a + da)
        out.append(clone("straw-end", x - 10 * k * math.cos(r), y - 10 * k * math.sin(r), k, a + da))
    return out


def svg_text(who: str, look: str | None = None, *, comment: str = "") -> str:
    """The whole drawing: ``<defs>`` (the clones' sources), the side view as
    part layers (the rig's view), the front view in the second cell, and the
    hidden joints layer of the side view."""
    look = look or CAST[who]
    d = rig_drawing(who, look)
    name = NAMES[who]
    shared = defs()
    side_id = FILES[who].replace("_", "-")
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<svg xmlns="http://www.w3.org/2000/svg"',
           '     xmlns:xlink="http://www.w3.org/1999/xlink"',
           '     xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"',
           f'     width="{int(W + CELL_DX)}mm" height="{H}mm" viewBox="0 0 {int(W + CELL_DX)} {H}"',
           f'     data-character-design="{FILES[who]}">',
           f'  <!-- {name}: {O["label"]}. Side view facing right in the left cell (the rig\'s view, the ground at y={GROUND:g});',
           f'       the front view in the right cell. Drawn by scripts/svg_art/steel_and_straw_man_art.py{comment}. -->',
           '  <defs>']
    out += ["    " + s for s in shared]
    out.append('  </defs>')
    out.append(f'  <g id="{side_id}" inkscape:groupmode="layer" inkscape:label="{SIDE_LABEL.format(name=name)}" data-rig-pixel-origin="0 0">')
    for pname, bone, z, body in d["parts"]:
        extra = f' data-rig-opacity="{pname}" data-rig-editor-visibility="editor-only" style="display:none"' if pname in SWITCHED else ""
        out.append(f'    <g id="{pname.replace("_", "-")}" inkscape:groupmode="layer" inkscape:label="{pname.replace("_", " ").title()}" '
                   f'data-rig-part="{pname}" data-rig-bone="{bone}" data-rig-z="{z}"{extra}>')
        out += ["      " + s for s in body]
        out.append("    </g>")
    out.append("  </g>")
    use(who, look)
    _N[0] = 1000
    body = front_steel() if who == "steel" else front_straw()
    out.append(f'  <g id="{side_id}-front" inkscape:groupmode="layer" inkscape:label="{FRONT_LABEL.format(name=name)}" '
               f'transform="translate({svg.f(CELL_DX)} 0)" data-rig-pixel-origin="0 0">')
    out += ["    " + s for s in body]
    out.append("  </g>")
    out += ["  " + s for s in svg.joints_layer({k: (v[1], v[2]) for k, v in d["joints"].items()})]
    out.append("</svg>")
    return "\n".join(out) + "\n"


# ============================================================================================
# contact sheets
# ============================================================================================

def _render(text, zoom, show_switched=False):
    import resvg_py
    from PIL import Image
    text = text.replace(f'width="{int(W + CELL_DX)}mm" height="{H}mm"', f'width="{int(W + CELL_DX)}" height="{H}"')
    if not show_switched:
        text = text.replace('style="display:none">', 'style="display:none" data-hidden="1">')
    png = bytes(resvg_py.svg_to_bytes(svg_string=text, zoom=zoom))
    return Image.open(io.BytesIO(png)).convert("RGBA")


BG = (214, 219, 226, 255)


def _font(size, bold=True):
    from PIL import ImageFont
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}", size)
    except OSError:
        return ImageFont.load_default()


def _cells(text, zoom):
    """The side and front cells, each cropped to the figure (its bottom is the ground)."""
    im = _render(text, zoom)
    w = int(W * zoom)
    out = []
    for i in range(2):
        cell = im.crop((i * w, 0, (i + 1) * w, im.size[1]))
        box = cell.getbbox()
        out.append(cell.crop((box[0] - 8, box[1] - 8, box[2] + 8, int(GROUND * zoom) + 2)))
    return out


#: Game size: the robot (124 cm) is 48 px; the Steel Man 196 cm, the Straw Man 185 cm.
GAME_PX = {"steel": 196 * 48 / 124, "straw": 185 * 48 / 124}


def contact_sheet(out: Path) -> Path:
    """Every look of both: side and front at 1.2x, the head at 3x, and the
    side and front at game size (x3, nearest)."""
    from PIL import Image, ImageDraw
    rows = []
    for who in ("steel", "straw"):
        for look in LOOKS[who]:
            text = svg_text(who, look)
            side, front = _cells(text, 1.2)
            use(who, look)
            ex, ey = G["eye"]
            hz = 3.0
            full = _render(text, hz)
            head = full.crop((int((ex - 70) * hz), int((ey - 58) * hz), int((ex + 50) * hz), int((ey + 62) * hz)))
            gz = GAME_PX[who] / (GROUND - G["crown"])
            g_side, g_front = (c.resize((c.size[0] * 3, c.size[1] * 3), Image.NEAREST) for c in _cells(text, gz))
            tag = "CAST" if CAST[who] == look else "kept, not cast"
            rows.append((f"{NAMES[who]} {O['label']}   [{tag}]", [side, front, head, g_side, g_front]))
    gap, lab = 24, 34
    width = max(max(sum(i.size[0] for i in ims) + gap * (len(ims) + 1), int(_font(20).getlength(label)) + 2 * gap) for label, ims in rows)
    height = sum(max(i.size[1] for i in ims) + lab + gap for _, ims in rows) + 30
    sheet = Image.new("RGBA", (width, height), BG)
    dr = ImageDraw.Draw(sheet)
    y = 0
    for label, ims in rows:
        dr.text((gap, y + 10), label, fill=(24, 24, 28, 255), font=_font(20))
        x = gap
        hrow = max(i.size[1] for i in ims)
        for i, im in enumerate(ims):
            yy = y + lab + (hrow - im.size[1] if i != 2 else 0)
            sheet.alpha_composite(im, (x, yy))
            x += im.size[0] + gap
        y += hrow + lab + gap
    dr.text((gap, height - 26), "side | front | head (3x) | game size x3: side, front  -  Jon 2026-10-23: the Steel Man and the Straw Man, not the Tin Man and the Scarecrow",
            fill=(80, 84, 92, 255), font=_font(14, False))
    out.mkdir(parents=True, exist_ok=True)
    p = out / "steel_and_straw_man_candidates.png"
    sheet.convert("RGB").save(p)
    return p


def main() -> None:
    if len(sys.argv) > 2 and sys.argv[1] == "--all":
        out = Path(sys.argv[2])
        out.mkdir(parents=True, exist_ok=True)
        for who in LOOKS:
            for look in LOOKS[who]:
                p = out / f"{FILES[who]}_{look}.svg"
                p.write_text(svg_text(who, look), encoding="utf8")
                print(p)
        return
    if len(sys.argv) > 2 and sys.argv[1] == "--sheets":
        print(contact_sheet(Path(sys.argv[2])))
        return
    if len(sys.argv) > 3 and sys.argv[1] == "--png":
        who, look = sys.argv[2], sys.argv[3]
        out = Path(sys.argv[4]) if len(sys.argv) > 4 else Path(".")
        im = _render(svg_text(who, look), 2.0, show_switched=False)
        p = out / f"{FILES[who]}_{look}.png"
        bg = __import__("PIL.Image", fromlist=["Image"]).new("RGBA", im.size, BG)
        bg.alpha_composite(im)
        bg.convert("RGB").save(p)
        print(p)
        return
    raise SystemExit("usage: steel_and_straw_man_art.py --all DIR | --sheets DIR | --png WHO LOOK [DIR]")


if __name__ == "__main__":
    main()
