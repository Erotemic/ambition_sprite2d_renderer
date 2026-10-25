"""Alice's own gear on the character generator's body (``chargen``).

Her spec draws a woman in a teal coat; these are the parts that make her
Alice, drawn from the same 3D figure in every view (``chargen.extras``),
after the first Alice (``alice_cryptographer``):

* her hair, a full bob with a side-swept fringe, over her ears and cut at
  the jaw (the spec's own hair is ``bald``, so this is her only hair),
  with a gold Alice band over the crown, a gold pin at her right temple,
  drop earrings, and freckles;
* her red tie, her brown leather satchel with its brass clasp on her right
  hip and its strap over her left shoulder, the toothed brass cipher wheel
  at her left hip, gold bands on her coat cuffs, and the turned-down cuffs,
  buckles and laces of her boots;
* her surveyor's range pole in her right fist (``prop.staff``), and a sealed
  letter for her left fist (``prop.letter``): she sends messages.

The pole and the letter ride the grip bones and are drawn as the game draws
a held item: through the fist, forward and ``ITEM_REST_ANGLE`` up on screen
in every view, so the clips turn them with the wrist (``Kit.hand(item=)``).

Units are the figure's: centimetres, ``x`` to her left, ``y`` down (the
ground is 0), ``z`` forward. Her right side (``l < 0``) is the near side.

Her right and left are fixed in 3D, so the front and back views show the
satchel, the pin and the pole on the side they are on. A left view of the
sheet is the mirror of its right twin, as it is in the game (a sprite that
faces left is flipped), so in a left view those swap sides.
"""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Dict, List, Tuple

from ...chargen.draw import ITEM_REST_ANGLE, grip_point
from ...chargen.drawkit import Ctx, Part, shaded_region, surface_line, tube3
from ...chargen.geometry import Loft, RingKey, add3, column_bands, ellipse3, hull, interp_knots, lerp, loft_region, norm3, scale3, smoothstep, sub3, wrap180
from ...chargen.svgout import FINE, light, mix, shade, style, using
from ...chargen.wear import skirt_loft

Point = Tuple[float, float]

#: Her colours (the spec holds the skin, hair, coat and trouser colours).
POLE_RED = "#c4463e"
POLE_WHITE = "#f2ece0"
BRASS = "#d99c3e"
BRASS_LIGHT = "#f2c86e"
LEATHER = "#7a4a2a"
LEATHER_DARK = "#4a2c1c"
LENS = "#7fd6d0"
PAPER = "#f3e7c4"
PAPER_DARK = "#cbb88a"
SEAL = "#b23a35"
LEATHER_LIGHT = "#9a6038"
TIE = "#a81c3c"
MAP_INK = "#2f6870"
#: The sheen on her navy hair: a cool blue-teal, as the first Alice had.
HAIR_SHEEN = "#72aed0"
#: Her jewels: garnet and amethyst set in gold. They are across the colour
#: wheel from her teal coat, so they glow on it, and the gold that holds them
#: is the gold of her brass.
GARNET = "#b81e44"
AMETHYST = "#8e3fc4"
#: The bright teals of the first Alice's coat (``assets/alice.svg``): its
#: lapels (``#5ba6aa``), and the light lines on its dark cloth (there
#: ``#6caaa9``; here a little lighter, so they read at game size).
LAPEL = "#5ba6aa"
TEAL_LINE = "#7cc2bf"
#: Her hair band: a near-black amethyst cloth in a gold edge (the gold arc
#: is what reads, as on the first Alice's band).
BAND = "#272238"
#: The ink round her hair: a dark navy, as the first Alice's.
HAIR_INK = "#17212c"

#: The range pole in cm: its length, how far below the fist its shoe is
#: (the rest runs ahead of the fist to the sighting head), its radius, and
#: the length of each red or white band.
POLE_LENGTH = 122.0
POLE_BUTT = 34.0
POLE_R = 1.35
POLE_BAND = 10.0


def gem(pt, x: float, y: float, r: float, color: str, cut: int = 6) -> None:
    """A cut stone on screen at (``x``, ``y``): its colour, an ink edge, and a
    catch-light high on it."""
    pts = [(x + r * math.cos(t), y + r * math.sin(t)) for t in (math.pi / 2 + i * math.tau / cut for i in range(cut))]
    pt.region([pts], color, outline=FINE * 0.6)
    pt.flat([[(x - r * 0.55 + r * 0.28 * math.cos(t), y - r * 0.35 + r * 0.28 * math.sin(t)) for t in (i * math.tau / 6 for i in range(6))]],
            light(color, 0.6))


# ---- hair ---------------------------------------------------------------------------------------

#: Her hairline, after the first Alice's: how far down the head (a part of
#: the head's height from the crown) the hair reaches at each angle round it
#: (0 her face, -90 her right ear, 90 her left, 180 her nape). The fringe
#: runs across her brow, higher over her left eye, and ends in a lock at
#: her left temple; on her right the ear shows, and behind it the bob is
#: cut at the jaw, covering the nape.
HAIRLINE = [(-180.0, 0.8), (-150.0, 0.82), (-124.0, 0.82), (-112.0, 0.8), (-106.0, 0.42), (-86.0, 0.38), (-66.0, 0.33), (-48.0, 0.3), (-20.0, 0.3), (10.0, 0.27), (36.0, 0.22), (52.0, 0.25), (62.0, 0.5),
            (72.0, 0.52), (86.0, 0.74), (110.0, 0.8), (150.0, 0.82), (180.0, 0.8)]
#: The hem is not a ruler line: it ends in soft points (every ``TIP_EVERY``
#: degrees round the head, ``TIP`` of the head's height long).
TIP_EVERY = 22.0
TIP = 0.028
#: Where the part runs (an angle round the head).
PART_AT = -44.0
#: The sheen arcs on her hair, as (angle, part of the head's height) knots.
SHEEN = [[(-150.0, 0.5), (-125.0, 0.32), (-95.0, 0.17), (-55.0, 0.1), (-15.0, 0.1), (20.0, 0.13)],
         [(-135.0, 0.56), (-110.0, 0.4), (-82.0, 0.3), (-60.0, 0.27)],
         [(150.0, 0.5), (125.0, 0.32), (95.0, 0.2), (65.0, 0.14)],
         [(170.0, 0.6), (160.0, 0.4), (135.0, 0.22)]]


def interp_arc(knots, n: int = 24):
    """``n`` points along a polyline of (angle, height) knots."""
    out = []
    for i in range(n):
        u = i / (n - 1) * (len(knots) - 1)
        j = min(int(u), len(knots) - 2)
        t = u - j
        (a0, f0), (a1, f1) = knots[j], knots[j + 1]
        out.append((lerp(a0, a1, t), lerp(f0, f1, t)))
    return out


def _hair_loft(fig) -> Loft:
    """A shell round the skull, after the first Alice's hair: lifted at the
    crown, close at the sides, full at the back of the head, and its ends
    turned under at the jaw."""
    hh = fig.hh
    sk = fig.skull
    mx = max(kk.rx for kk in sk.keys)
    mzb = max(kk.rzb for kk in sk.keys)
    keys = []
    for kk in sk.keys:
        f = (kk.y - fig.crown) / hh
        if f > 0.86:
            break
        hold = smoothstep(0.38, 0.7, f)
        lift = 0.03 * hh * (1.0 - smoothstep(0.08, 0.45, f))
        side = 0.02 * hh * smoothstep(0.04, 0.3, f) + 0.018 * hh * smoothstep(0.4, 0.68, f) * (1.0 - 0.7 * smoothstep(0.74, 0.9, f))
        back = 0.045 * hh * smoothstep(0.08, 0.45, f) * (1.0 - 0.6 * smoothstep(0.72, 0.9, f))
        keys.append(RingKey(kk.y, lerp(kk.rx, mx, hold) + side + 0.5 * lift, kk.rzf + side + lift,
                            lerp(kk.rzb, mzb * 0.95, hold) + side + back + lift, kk.cl, kk.cz, kk.sq))
    last = keys[-1]
    # The ends turn under toward the jaw and the nape.
    keys.append(RingKey(fig.fy(0.97), mx * 0.78 + 0.02 * hh, last.rzf * 0.84, mzb * 0.8, last.cl, last.cz - 0.02 * hh, last.sq))
    k0 = sk.keys[0]
    keys[0] = RingKey(k0.y - 0.035 * hh, 0.0, 0.0, 0.0, k0.cl, k0.cz, k0.sq)
    return Loft(keys)


def _hair_margin(fig):
    def m(alpha: float, y: float) -> float:
        f = (y - fig.crown) / fig.hh
        a = wrap180(alpha)
        line = interp_knots(a, HAIRLINE)
        if line > 0.6:
            # A point every TIP_EVERY degrees along the hem.
            u = (a / TIP_EVERY) % 1.0
            line += TIP * (1.0 - abs(2.0 * u - 1.0)) ** 2
        return line - f

    return m


def hair_parts(ctx: Ctx) -> List[Part]:
    """Her hair, inked in a dark navy (not the body's ink), as the first
    Alice's is."""
    with using(replace(style(), ink=HAIR_INK, outline=0.8 * style().outline)):
        return _hair_parts(ctx)


def _hair_parts(ctx: Ctx) -> List[Part]:
    fig = ctx.fig
    hh = fig.hh
    col = ctx.hair
    loft = _hair_loft(fig)
    m = _hair_margin(fig)
    pt = ctx.new()
    polys = loft_region(ctx.view, loft, loft.top, loft.bottom, m, step=0.4)
    if not polys:
        return []
    pt.region(polys, col)
    pt.flat(column_bands(ctx.view, loft, loft.top, loft.bottom, m, side="left", frac=0.2, cap=0.09 * hh, step=0.4), shade(col, 0.26))
    pt.flat(column_bands(ctx.view, loft, loft.top, loft.bottom, m, side="right", frac=0.08, cap=0.04 * hh, step=0.4, y_from=0.03,
                         y_to=0.35), mix(col, HAIR_SHEEN, 0.55))
    # A few dark strands down the bob.
    sh = shade(col, 0.36)
    for a0 in (-150, 180, 150, 118, 96):
        pts = [(a0 + 4.0 * math.sin(i * 0.7), fig.fy(lerp(0.3, 0.9, i / 9.0))) for i in range(10)]
        pts = [q for q in pts if q[1] <= loft.bottom and m(*q) > 0.015]
        for run in surface_line(ctx, loft, pts, out=0.05, thresh=0.2):
            if len(run) >= 3:
                pt.line(run, sh, FINE * 0.9)
    # The sheen: long arcs swept from the back of the head up over the
    # crown and forward, as on the first Alice.
    hi = mix(col, HAIR_SHEEN, 0.7)
    for arc in SHEEN:
        pts = [(a, fig.fy(f)) for a, f in interp_arc(arc)]
        for run in surface_line(ctx, loft, pts, out=0.06, thresh=0.15):
            if len(run) >= 3:
                pt.line(run, hi, FINE * 1.6)
    out = [Part("hair", "head", 52.0, pt.els, "Hair - Swept Bob", feature="hair:alice_bob")]
    # The back of the bob, seen past her head and neck in a front view: the
    # whole back half of the shell, behind everything.
    back = ctx.new()
    if ctx.view.c > 0.3:
        def nape(alpha: float, y: float) -> float:
            return min(m(alpha, y), (abs(wrap180(alpha)) - 100.0) * 0.01)

        back.region(loft_region(ctx.view, loft, fig.fy(0.3), loft.bottom, nape, step=0.4, solid=True), shade(col, 0.2))
    if back.els:
        out.append(Part("hair_back", "head", 1.0, back.els, "Hair - Back", feature="hair:alice_bob"))
    return out


#: The band's plane leans forward this far (degrees) from upright through
#: her ears, so it crosses the front of her crown; its half-width on top, in
#: degrees of that lean.
BAND_LEAN = 38.0
BAND_HALF = 8.0


def _band_point(fig, loft: Loft, theta: float, off: float) -> Tuple[float, float]:
    """A point of the band on the hair, as (angle, height): ``theta``
    degrees round from straight up (-90 her right ear, 90 her left) in the
    band's plane, ``off`` degrees across it."""
    th, lean = math.radians(theta), math.radians(BAND_LEAN + off)
    d = (math.sin(th), -math.cos(th) * math.cos(lean), math.cos(th) * math.sin(lean))
    c = (0.0, fig.fy(0.5), 0.0)
    alpha = math.degrees(math.atan2(d[0], d[2]))
    h = math.hypot(d[0], d[2])
    lo, hi = 0.0, 1.5 * fig.hh
    for _ in range(30):
        r = 0.5 * (lo + hi)
        y = c[1] + r * d[1]
        if y < loft.top:
            hi = r
            continue
        q = loft.point(alpha, y, 0.0)
        if math.hypot(q[0], q[2]) > r * h:
            lo = r
        else:
            hi = r
    return alpha, c[1] + lo * d[1]


def ornament_parts(ctx: Ctx) -> List[Part]:
    """Her gold hair band over the crown (an Alice band), the gold pin at
    her right temple, her drop earrings, and the freckles on her cheeks."""
    fig = ctx.fig
    hh = fig.hh
    out: List[Part] = []
    loft = _hair_loft(fig)
    band = ctx.new()

    # A crescent over the front of the crown from ear to ear, behind the
    # fringe: widest on top, narrow at its ends; dark cloth, a gold edge.
    def half(th: float) -> float:
        return BAND_HALF * (1.0 - 0.5 * (th / 95.0) ** 2)

    span = range(-95, 96, 3)
    for i in range(7):
        u = -1.0 + i / 3.0
        for run in surface_line(ctx, loft, [_band_point(fig, loft, th, u * half(th)) for th in span], out=0.02 * hh, thresh=0.1):
            band.line(run, BAND, 0.026 * hh, smooth=True, fixed=True)
    for u in (-1.0, 1.0):
        for run in surface_line(ctx, loft, [_band_point(fig, loft, th, u * half(th)) for th in span], out=0.025 * hh, thresh=0.1):
            band.line(run, BRASS_LIGHT, 0.38 * fig.k, smooth=True)
    if ctx.view.facing(-64.0) > 0.15:
        c = loft.point(-66.0, fig.fy(0.27), 0.03 * hh)
        x, y = ctx.p(c)
        r = 1.25 * fig.k
        band.region([[(x, y - r * 1.25), (x + r * 0.9, y), (x, y + r * 1.25), (x - r * 0.9, y)]], BRASS_LIGHT, outline=FINE * 0.7)
        gem(band, x, y, r * 0.52, GARNET, 4)
    if band.els:
        out.append(Part("hair_band", "head", 52.5, band.els, "Hair Band and Pin", feature="acc:alice_band"))
    rings = ctx.new()
    for _depth, _side, sgn in (("near", "right", -1.0), ("far", "left", 1.0)):
        # Her right ear shows past her face; her hair hides the left one
        # unless she turns it to the viewer, and both from behind.
        if ctx.view.facing(sgn * 98.0) < (-0.2 if sgn < 0 else 0.25) or ctx.view.c < -0.3:
            continue
        lobe = fig.skull.point(sgn * 98.0, fig.fy(0.66), 0.01 * hh)
        x, y = ctx.p(lobe)
        r = 0.42 * fig.k
        rings.region([[(x + r * math.cos(t), y + r * math.sin(t)) for t in (i * math.tau / 10 for i in range(10))]], BRASS_LIGHT,
                     outline=FINE * 0.6)
        rings.line([(x, y + r), (x, y + 0.75 * fig.k)], BRASS, 0.18 * fig.k)
        gem(rings, x, y + 1.25 * fig.k, 0.55 * fig.k, GARNET, 5)
    if rings.els:
        # Over the hair that covers her ears, as the first Alice's are.
        out.append(Part("earrings", "head", 52.2, rings.els, "Earrings", feature="acc:earrings"))
    # A warm blush low on each cheek, as the first Alice's skin has.
    blush = ctx.new()
    for sgn in (-1.0, 1.0):
        if ctx.view.facing(sgn * 30.0) < 0.3:
            continue
        c = fig.head.point(sgn * 32.0, fig.fy(0.66), 0.02)
        n = (math.sin(math.radians(sgn * 30.0)), 0.0, math.cos(math.radians(sgn * 30.0)))
        u = norm3((n[2], 0.0, -n[0]))
        blush.flat([[ctx.p(q) for q in ellipse3(c, u, (0.0, 1.0, 0.0), 0.09 * hh, 0.06 * hh, 12)]], mix(ctx.skin, "#d0766a", 0.16), smooth=True)
    if blush.els:
        out.append(Part("blush", "head", 50.3, blush.els, "Blush"))
    dots = ctx.new()
    col = mix(ctx.skin, "#8a4a30", 0.5)
    for sgn in (-1.0, 1.0):
        for a, f in ((22.0, 0.585), (29.0, 0.61), (35.0, 0.585), (27.0, 0.56)):
            if ctx.view.facing(sgn * a) < 0.4:
                continue
            x, y = ctx.p(fig.head.point(sgn * a, fig.fy(f), 0.02))
            r = 0.3 * fig.k
            dots.flat([[(x + r * math.cos(t), y + r * math.sin(t)) for t in (i * math.tau / 6 for i in range(6))]], col)
    if dots.els:
        out.append(Part("freckles", "head", 50.5, dots.els, "Freckles"))
    return out


# ---- the satchel, the tie, the cipher wheel, the cuffs and the boots ----------------------------------------


#: Where the satchel hangs: an angle round her body (her right hip, a
#: little to the front).
SATCHEL_AT = -68.0


def _satchel_frame(fig):
    """The satchel's centre on her right hip (over the coat), its outward
    normal, and the direction round her body."""
    a = math.radians(SATCHEL_AT)
    k = fig.k
    c = fig.torso.point(SATCHEL_AT, fig.y_hipw + 0.01 * fig.T, 1.15 * k + 2.4)
    n = (math.sin(a), 0.0, math.cos(a))
    u = (math.cos(a), 0.0, -math.sin(a))
    return c, n, u


def satchel_parts(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    """Her brown leather satchel with its flap, its brass clasp and its
    stitching, at her right hip; its strap over her left shoulder."""
    fig = ctx.fig
    k = fig.k
    c, n, u = _satchel_frame(fig)
    w, h, d = 9.6 * k, 8.0 * k, 5.4 * k

    def at(su: float, sy: float, sn: float = 0.0):
        return add3(add3(c, scale3(u, su)), add3((0.0, sy, 0.0), scale3(n, sn)))

    pt = ctx.new()
    box = [at(su, sy, sn) for su in (-w, w) for sy in (-h, h) for sn in (0.0, d)]
    pt.region([hull(ctx.p(q) for q in box)], LEATHER, smooth=False)
    facing = ctx.view.facing(SATCHEL_AT)
    if facing > 0.05:
        pt.flat([[ctx.p(at(su, sy, d)) for su, sy in ((-w * 0.92, h * 0.15), (w * 0.92, h * 0.15), (w * 0.92, h * 0.88), (-w * 0.92, h * 0.88))]],
                shade(LEATHER, 0.18))
        flap = [at(-w * 1.03, -h * 1.04, d + 0.3), at(w * 1.03, -h * 1.04, d + 0.3), at(w * 1.03, h * 0.18, d + 0.3), at(0.0, h * 0.42, d + 0.3),
                at(-w * 1.03, h * 0.18, d + 0.3)]
        pt.region([[ctx.p(q) for q in flap]], LEATHER_LIGHT, outline=FINE * 1.0)
        stitch = [at(-w * 0.86, -h * 0.86, d + 0.35), at(w * 0.86, -h * 0.86, d + 0.35), at(w * 0.86, h * 0.06, d + 0.35),
                  at(0.0, h * 0.28, d + 0.35), at(-w * 0.86, h * 0.06, d + 0.35)]
        pt.line([ctx.p(q) for q in stitch + stitch[:1]], shade(LEATHER_LIGHT, 0.35), FINE * 0.6, smooth=False)
        clasp = [at(-1.3 * k, h * 0.22, d + 0.5), at(1.3 * k, h * 0.22, d + 0.5), at(1.3 * k, h * 0.62, d + 0.5), at(-1.3 * k, h * 0.62, d + 0.5)]
        pt.region([[ctx.p(q) for q in clasp]], BRASS, outline=FINE * 0.8)
        gx, gy = ctx.p(at(0.0, h * 0.42, d + 0.6))
        gem(pt, gx, gy, 0.85 * k, GARNET)
    # Seen from the far side, her body hides it: it is painted behind her.
    out = [Part("satchel", "torso", zmap["torso"] + (3.8 if facing > -0.15 else -2.5), pt.els, "Satchel", feature="acc:satchel")]
    # The strap: from her left shoulder across her chest to the satchel, and
    # behind her the same way.
    tor = fig.torso
    out_cm = 1.15 * k + 0.6
    y0, y1 = fig.y_sh + 0.5 * k, fig.y_hipw - 0.04 * fig.T
    front = [(lerp(78.0, SATCHEL_AT - 4.0, i / 12.0), lerp(y0, y1, i / 12.0)) for i in range(13)]
    back = [(lerp(102.0, 356.0 + SATCHEL_AT, i / 12.0), lerp(y0, y1, i / 12.0)) for i in range(13)]
    sp = ctx.new()
    for path in (front, back):
        for run in surface_line(ctx, tor, path, out=out_cm, thresh=0.05):
            sp.line(run, LEATHER_DARK, 1.35 * k, smooth=True)
            sp.line(run, LEATHER, 0.85 * k, smooth=True)
    a, y = 22.0, lerp(y0, y1, 0.32)
    if ctx.view.facing(a) > 0.2:
        cc = tor.point(a, y, out_cm + 0.2)
        nn = norm3((math.sin(math.radians(a)), 0.0, math.cos(math.radians(a))))
        uu = norm3((nn[2], 0.0, -nn[0]))
        sp.region([[ctx.p(q) for q in ellipse3(cc, uu, (0.0, 1.0, 0.0), 1.3 * k, 1.1 * k, 4)]], BRASS, outline=FINE * 0.7)
        sp.flat([[ctx.p(q) for q in ellipse3(cc, uu, (0.0, 1.0, 0.0), 0.65 * k, 0.5 * k, 4)]], LEATHER)
    if sp.els:
        out.append(Part("satchel_strap", "torso", zmap["torso"] + 3.5, sp.els, "Satchel Strap", feature="acc:satchel"))
    return out


def tie_parts(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    """Her red tie, knotted at the collar of her shirt, inside her coat."""
    fig = ctx.fig
    if ctx.view.facing(0.0) < -0.1:
        return []
    k = fig.k
    tor = fig.torso
    out_cm = 0.7
    y_knot = fig.y_nb + 1.6 * k
    y_end = fig.y_waist - 1.5 * k

    def p(y: float, w: float):
        q = tor.point(0.0, y, out_cm)
        return ctx.p((q[0] + w, q[1], q[2])), ctx.p((q[0] - w, q[1], q[2]))

    pt = ctx.new()
    (a0, b0), (a1, b1) = p(y_knot + 1.4 * k, 1.1 * k), p(y_end - 2.0 * k, 1.9 * k)
    tip = ctx.p(tor.point(0.0, y_end, out_cm))
    pt.region([[a0, a1, tip, b1, b0]], TIE, outline=FINE * 0.9)
    pt.line([ctx.p(tor.point(0.0, y_knot + 2.0 * k, out_cm + 0.1)), ctx.p(tor.point(0.0, y_end - 1.0 * k, out_cm + 0.1))], shade(TIE, 0.3),
            FINE * 0.7)
    (ka, kb), (kc, kd) = p(y_knot - 0.6 * k, 1.3 * k), p(y_knot + 1.5 * k, 0.9 * k)
    pt.region([[ka, kc, kd, kb]], shade(TIE, 0.12), outline=FINE * 0.9)
    return [Part("tie", "torso", zmap["torso"] + 1.4, pt.els, "Tie", feature="acc:tie")]


def wheel_parts(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    """The brass cipher wheel hanging from her belt at her left hip: a
    toothed rim, a ring of letters, a dark keyhole hub."""
    fig = ctx.fig
    k = fig.k
    tor = fig.torso
    a = 34.0
    y = fig.y_waist + 5.2 * k
    c = tor.point(a, y, 1.15 * k + 1.2)
    n = norm3((math.sin(math.radians(a)), 0.0, math.cos(math.radians(a))))
    if n[2] * ctx.view.c - n[0] * ctx.view.s < 0.08:
        return []
    uu = norm3((n[2], 0.0, -n[0]))
    vv = (0.0, 1.0, 0.0)
    r = 4.3 * k

    def disc(rad, m=24, lift=0.0):
        return [ctx.p(add3(add3(c, scale3(n, lift)), add3(scale3(uu, rad * math.cos(t)), scale3(vv, rad * math.sin(t)))))
                for t in (i * math.tau / m for i in range(m))]

    pt = ctx.new()
    hook = tor.point(a, fig.y_waist, 1.15 * k + 1.0)
    pt.line([ctx.p(hook), ctx.p(add3(c, (0.0, -r * 1.1, 0.0)))], LEATHER_DARK, 0.6 * k)
    teeth = []
    for i in range(32):
        t = i * math.tau / 32
        rad = r * (1.14 if (i // 2) % 2 == 0 else 1.0)
        teeth.append(ctx.p(add3(c, add3(scale3(uu, rad * math.cos(t)), scale3(vv, rad * math.sin(t))))))
    pt.region([teeth], BRASS, outline=FINE * 0.9)
    pt.flat([disc(r * 0.8, lift=0.1)], BRASS_LIGHT)
    for i in range(12):
        t = i * math.tau / 12
        d = add3(scale3(uu, math.cos(t)), scale3(vv, math.sin(t)))
        pt.line([ctx.p(add3(c, scale3(d, r * 0.58))), ctx.p(add3(c, scale3(d, r * 0.76)))], shade(BRASS, 0.4), FINE * 0.6)
    pt.region([disc(r * 0.42, 16, 0.15)], MAP_INK, outline=FINE * 0.6)
    gx, gy = ctx.p(add3(c, scale3(n, 0.25)))
    gem(pt, gx, gy, r * 0.3, AMETHYST, 8)
    return [Part("cipher_wheel", "torso", zmap["torso"] + 3.6, pt.els, "Cipher Wheel", feature="acc:cipher_wheel")]


def cuff_parts(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    """A gold band round each coat cuff, amethyst piping above it."""
    fig = ctx.fig
    j = fig.joints
    rw = fig.arm_r[2]
    out = []
    for depth, side, _sgn in (("near", "right", -1.0), ("far", "left", 1.0)):
        E, W = j[f"{side}_elbow"], j[f"{side}_wrist"]
        pt = ctx.new()
        a, b = add3(E, scale3(sub3(W, E), 0.84)), add3(E, scale3(sub3(W, E), 0.93))
        tube3(ctx, pt, a, b, rw + 1.35, rw + 1.35, BRASS, round_a=False, round_b=False, band=False)
        a2, b2 = add3(E, scale3(sub3(W, E), 0.76)), add3(E, scale3(sub3(W, E), 0.84))
        tube3(ctx, pt, a2, b2, rw + 1.4, rw + 1.4, AMETHYST, round_a=False, round_b=False, band=False)
        out.append(Part(f"{depth}_cuff", f"{depth}_arm_l", zmap[f"{depth}_arm_l"] + 0.36, pt.els, f"Cuff - {depth}", feature="acc:cuffs"))
    return out


def piping_parts(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    """Garnet piping on the front edges of her open coat, from the collar
    to the waist: down each lapel's inner edge, then the coat's."""
    fig = ctx.fig
    T = fig.T
    shell = fig.torso.shell(ctx.plan["outer_t"])
    half, lapel = 10.0, 24.0
    pt = ctx.new()
    for sgn in (-1.0, 1.0):
        pts = []
        for i in range(13):
            y = lerp(fig.y_nb + 0.6, fig.y_waist + 0.05 * T, i / 12.0)
            pts.append((sgn * (coat_front(fig, lambda yy: half + lapel * (1.0 - smoothstep(fig.y_nb, fig.y_chest + 0.12 * T, yy)), y) + 0.8), y))
        for run in surface_line(ctx, shell, pts, out=0.25, thresh=0.05):
            pt.line(run, GARNET, 0.8 * fig.k, smooth=True)
    if not pt.els:
        return []
    return [Part("coat_piping", "torso", 33.1, pt.els, "Coat Piping", feature="acc:coat_piping")]


#: The outer edge of each lapel, after the first Alice's (``assets/alice.svg``,
#: the ``#5ba6aa`` path of her torso): (part of the way from the base of the
#: neck to the waist, angle round the body). The upper piece (the collar's
#: end) and the lapel meet in a notch; the lapel narrows to the coat's
#: closure on the chest.
LAPEL_EDGE = [(0.0, 40.0), (0.12, 47.0), (0.23, 45.0), (0.27, 31.0), (0.31, 47.0), (0.4, 43.0), (0.66, 4.0)]
#: The inner edge of each lapel (where the shirt shows), the same way.
LAPEL_INNER = [(0.0, 18.0), (0.27, 13.0), (0.66, 4.0)]


def coat_front(fig, edge, y: float) -> float:
    """The angle of the coat's front edge at height ``y``: the lapel's inner
    edge down to the closure, the coat's own edge below it."""
    u = (y - fig.y_nb) / (fig.y_waist - fig.y_nb)
    return interp_knots(u, LAPEL_INNER) if u <= LAPEL_INNER[-1][0] else edge(y)
#: The ink round her lapels and collar: a dark teal.
LAPEL_INK = "#1f5157"


def _lapel_parts(ctx: Ctx, shell: Loft, edge) -> List[Part]:
    """Her lapels: wide and notched, folded back from the collar to the
    closure on her chest, raised off the coat, bright teal in a dark teal
    edge; and the collar turned up behind her neck."""
    fig = ctx.fig
    k = fig.k
    y0, y1 = fig.y_nb, fig.y_waist

    def lapel(a: float, y: float) -> float:
        u = (y - y0) / (y1 - y0)
        if u > LAPEL_EDGE[-1][0]:
            return -1.0
        al = abs(wrap180(a))
        return min(al - interp_knots(u, LAPEL_INNER), interp_knots(u, LAPEL_EDGE) - al, y - y0 + 0.5) * 0.2

    out: List[Part] = []
    with using(replace(style(), ink=LAPEL_INK)):
        pt = ctx.new()
        polys = loft_region(ctx.view, shell.shell(0.45), y0 - 0.5, lerp(y0, y1, 0.67), lapel, step=0.25)
        pt.region(polys, LAPEL, outline=FINE * 0.9)
        # The roll: a light line where each lapel turns back.
        for sgn in (-1.0, 1.0):
            roll = [(sgn * (interp_knots(u, LAPEL_INNER) + 2.5), lerp(y0, y1, u)) for u in (0.02, 0.15, 0.3, 0.45, 0.6)]
            for run in surface_line(ctx, shell, roll, out=0.55, thresh=0.1):
                pt.line(run, light(LAPEL, 0.35), 0.35 * k, smooth=True)
        if pt.els:
            out.append(Part("coat_lapels", "torso", 33.07, pt.els, "Coat Lapels", feature="acc:coat_lapels"))
        # The collar, turned up round the back of the neck from lapel to lapel.
        nk = fig.neck.keys[-1]
        ring = Loft([RingKey(y0 - 3.2 * k, nk.rx + 1.5, nk.rzf + 1.5, nk.rzb + 1.5, 0.0, -0.8),
                     RingKey(y0 + 0.8, nk.rx + 3.2, nk.rzf + 2.6, nk.rzb + 3.0, 0.0, -0.4)])
        cp = ctx.new()

        def collar(a: float, y: float) -> float:
            return (abs(wrap180(a)) - edge(y0) - 6.0) * 0.2

        cp.region(loft_region(ctx.view, ring, ring.top, ring.bottom, collar, step=0.2), LAPEL, outline=FINE * 0.9)
        if cp.els:
            out.append(Part("coat_collar", "torso", 33.2, cp.els, "Coat Collar", feature="acc:coat_lapels"))
    return out


def teal_parts(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    """The first Alice's bright teals on her coat: lapels and a collar
    lighter than the coat, and light lines on its dark cloth (seams down the
    body, the edges, hem and seams of the skirt, the sleeves' folds and the
    top of each cuff)."""
    fig = ctx.fig
    T = fig.T
    k = fig.k
    t = ctx.plan["outer_t"]
    shell = fig.torso.shell(t)
    half, lapel = 10.0, 24.0
    y_lapel = fig.y_chest + 0.12 * T

    def edge(y: float) -> float:
        return half + lapel * (1.0 - smoothstep(fig.y_nb, y_lapel, y))

    out: List[Part] = []
    out += _lapel_parts(ctx, shell, edge)
    pt = ctx.new()
    # Seams down the body, front and back.
    for a in (-62.0, 62.0, -150.0, 150.0, 180.0):
        for run in surface_line(ctx, shell, [(a, lerp(fig.y_sh + 1.0, fig.y_waist + 0.05 * T, i / 8.0)) for i in range(9)], out=0.2, thresh=0.1):
            pt.line(run, TEAL_LINE, 1.0 * k, smooth=True)
    if pt.els:
        out.append(Part("coat_teal", "torso", 33.05, pt.els, "Coat Lapels and Seams", feature="acc:coat_teal"))
    # The skirt, piece by piece as ``chargen.wear.lobe_parts`` cuts it.
    hem = ctx.plan["outer_hem"]
    lo = skirt_loft(fig, fig.y_waist, hem, t + 0.6, 1.2)
    y0 = fig.y_waist
    knee = fig.joints["right_knee"][1]
    split = hem > knee + 0.12 * (knee - y0)
    lap = 0.05 * (knee - y0)
    for depth, side, sgn in (("near", "right", -1.0), ("far", "left", 1.0)):
        pieces = [(y0, knee + lap, "leg_u", ""), (knee - lap, hem, "leg_l", "_lower")] if split else [(y0, hem, "leg_u", "")]
        for a, b, bone, suffix in pieces:
            sp = ctx.new()
            lines = [[(sgn * 12.5, y) for y in (a, lerp(a, b, 0.5), b)], [(sgn * 64.0, y) for y in (a, lerp(a, b, 0.5), b)],
                     [(sgn * 177.0, y) for y in (a, lerp(a, b, 0.5), b)]]
            if suffix or not split:
                lines.append([(sgn * al, hem - 1.6 * k) for al in range(12, 179, 6)])
            for line in lines:
                for run in surface_line(ctx, lo, line, out=0.2, thresh=0.05):
                    sp.line(run, TEAL_LINE, 1.0 * k, smooth=True)
            if sp.els:
                zz = (32.0 if depth == "far" else 32.5) + (0.05 if suffix else 0.0) + 0.02
                out.append(Part(f"{depth}_skirt_teal{suffix}", f"{depth}_{bone}", zz, sp.els, f"Skirt Lines{suffix} - {depth}",
                                feature="acc:coat_teal"))
    # The sleeves: a light fold line down the lit side of each segment, and
    # a light line at the top of each cuff.
    j = fig.joints
    for depth, side, _sgn in (("near", "right", -1.0), ("far", "left", 1.0)):
        S, E, W = j[f"{side}_shoulder"], j[f"{side}_elbow"], j[f"{side}_wrist"]
        for (A, B, bone, r, t0, t1) in ((S, E, "arm_u", fig.arm_r[0] + 1.6, 0.2, 0.85), (E, W, "arm_l", fig.arm_r[2] + 1.4, 0.08, 0.68)):
            sl = ctx.new()
            a2, b2 = ctx.p(add3(A, scale3(sub3(B, A), t0))), ctx.p(add3(A, scale3(sub3(B, A), t1)))
            dx, dy = b2[0] - a2[0], b2[1] - a2[1]
            n = math.hypot(dx, dy) or 1.0
            ox, oy = dy / n, -dx / n
            if ox < 0:
                ox, oy = -ox, -oy
            off = 0.45 * r * ctx.p((1.0, 0.0, 0.0))[0] - 0.45 * r * ctx.p((0.0, 0.0, 0.0))[0]
            off = abs(off) if off else 0.45 * r
            sl.line([(a2[0] + ox * off, a2[1] + oy * off), (b2[0] + ox * off * 0.9, b2[1] + oy * off * 0.9)], TEAL_LINE, 0.95 * k)
            if bone == "arm_l":
                c0, c1 = add3(E, scale3(sub3(W, E), 0.725)), add3(E, scale3(sub3(W, E), 0.755))
                tube3(ctx, sl, c0, c1, fig.arm_r[2] + 1.42, fig.arm_r[2] + 1.42, TEAL_LINE, round_a=False, round_b=False, band=False)
            out.append(Part(f"{depth}_sleeve_teal_{bone}", f"{depth}_{bone}", zmap[f"{depth}_{bone}"] + 0.35, sl.els,
                            f"Sleeve Lines - {depth}", feature="acc:coat_teal"))
    return out


def boot_parts(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    """Her boots' turned-down cuffs (a lighter leather, a brass buckle on
    the outside) and their laces, crossed down the front."""
    fig = ctx.fig
    j = fig.joints
    _rt, _rk, rc, ra = fig.leg_r
    k = fig.k
    col = fig.spec.outfit.shoe_color
    cuff = mix(col, "#f0c0a8", 0.32)
    out = []
    for depth, side, sgn in (("near", "right", -1.0), ("far", "left", 1.0)):
        K, A = j[f"{side}_knee"], j[f"{side}_ankle"]

        def at(t: float, x: float = 0.0, z: float = 0.0):
            p = add3(K, scale3(sub3(A, K), t))
            return (p[0] + x, p[1], p[2] + z)

        def rad(t: float) -> float:
            return lerp(rc, ra, t) + 1.25

        pt = ctx.new()
        tube3(ctx, pt, at(0.38), at(0.47), rad(0.38) + 0.45, rad(0.47) + 0.45, cuff, round_a=False, round_b=False)
        if ctx.view.facing(sgn * 90.0) > -0.3:
            b = at(0.425, sgn * (rad(0.425) + 0.4))
            x, y = ctx.p(b)
            s = 0.7 * k
            pt.region([[(x - s, y - s), (x + s, y - s), (x + s, y + s), (x - s, y + s)]], BRASS, outline=FINE * 0.7)
            gem(pt, x, y, 0.42 * k, AMETHYST, 4)
        if ctx.view.c > -0.25:
            ts = [0.52 + 0.07 * i for i in range(7)]
            for t0, t1 in zip(ts, ts[1:]):
                w0, w1 = 0.42 * rad(t0), 0.42 * rad(t1)
                z0, z1 = rad(t0) * 0.92, rad(t1) * 0.92
                pt.line([ctx.p(at(t0, -w0, z0)), ctx.p(at(t1, w1, z1))], shade(col, 0.45), FINE * 0.75, smooth=False)
                pt.line([ctx.p(at(t0, w0, z0)), ctx.p(at(t1, -w1, z1))], shade(col, 0.45), FINE * 0.75, smooth=False)
        out.append(Part(f"{depth}_boot_detail", f"{depth}_leg_l", zmap[f"{depth}_leg_l"] + 0.4, pt.els, f"Boot Cuff and Laces - {depth}",
                        feature="acc:boot_detail"))
    return out


# ---- held: the range pole and the letter -------------------------------------------------------------


def _held_axis() -> Point:
    """The direction a held item runs through a fist at rest, on screen."""
    a = math.radians(-ITEM_REST_ANGLE)
    return (math.cos(a), math.sin(a))


def pole_paint(pt, g: Point, ux: float, uy: float) -> None:
    """The range pole gripped at ``g``, running along (``ux``, ``uy``) on
    screen: the shoe ``POLE_BUTT`` behind the fist, the sighting head ahead."""
    nx, ny = -uy, ux

    def at(s: float, w: float = 0.0) -> Point:
        return (g[0] + ux * s + nx * w, g[1] + uy * s + ny * w)

    lo, hi = -POLE_BUTT, POLE_LENGTH - POLE_BUTT
    r = POLE_R
    pt.region([[at(lo, r), at(hi - 4.0, r), at(hi - 4.0, -r), at(lo, -r)]], POLE_WHITE)
    s = lo + 4.0
    i = 0
    while s + POLE_BAND < hi - 6.0:
        if i % 2 == 0:
            pt.flat([[at(s, r * 0.94), at(s + POLE_BAND, r * 0.94), at(s + POLE_BAND, -r * 0.94), at(s, -r * 0.94)]], POLE_RED)
        s += POLE_BAND
        i += 1
    pt.flat([[at(lo + 2.0, r * 0.5), at(hi - 6.0, r * 0.5), at(hi - 6.0, r * 0.15), at(lo + 2.0, r * 0.15)]], "#ffffff", opacity=0.55)
    # The leather wrap at the fist, the brass shoe, the sighting head.
    pt.region([[at(-4.5, r * 1.25), at(5.5, r * 1.25), at(5.5, -r * 1.25), at(-4.5, -r * 1.25)]], LEATHER_DARK, outline=FINE * 0.8)
    pt.region([[at(lo + 3.5, r * 1.3), at(lo + 3.5, -r * 1.3), at(lo - 0.5, -r * 0.8), at(lo - 2.6, 0.0), at(lo - 0.5, r * 0.8)]], BRASS,
              outline=FINE * 0.9)
    pt.region([[at(hi - 9.0, r * 1.35), at(hi - 4.0, r * 1.35), at(hi - 4.0, -r * 1.35), at(hi - 9.0, -r * 1.35)]], BRASS, outline=FINE * 0.9)
    c = at(hi - 1.0)
    ring = [(c[0] + 2.7 * math.cos(t), c[1] + 2.7 * math.sin(t)) for t in (i * math.tau / 20 for i in range(20))]
    lens = [(c[0] + 1.6 * math.cos(t), c[1] + 1.6 * math.sin(t)) for t in (i * math.tau / 16 for i in range(16))]
    pt.region([ring], BRASS)
    pt.region([lens], LENS, outline=FINE * 0.8)
    # A short blunt finial: a fine spike flickers as the pole turns.
    pt.region([[at(hi + 1.2, r * 1.35), at(hi + 3.4, r * 0.7), at(hi + 4.6, 0.0), at(hi + 3.4, -r * 0.7), at(hi + 1.2, -r * 1.35)]],
              BRASS_LIGHT, outline=FINE * 0.8)


def pole_parts(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    fig = ctx.fig
    g = ctx.p(grip_point(fig, "right"))
    ux, uy = _held_axis()
    pt = ctx.new()
    pole_paint(pt, g, ux, uy)
    return [Part("pole", "near_grip", zmap["near_arm_hand"] - 0.2, pt.els, "Range Pole (in her right fist)", opacity="prop.staff",
                 opacity_default=1)]


def letter_parts(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    """A sealed letter pinched in her left fist (``prop.letter``)."""
    fig = ctx.fig
    k = fig.k
    g = ctx.p(grip_point(fig, "left"))
    ux, uy = _held_axis()
    nx, ny = -uy, ux
    w, h = 11.0 * k, 7.6 * k

    def at(s: float, t: float) -> Point:
        return (g[0] + ux * s + nx * t, g[1] + uy * s + ny * t)

    pt = ctx.new()
    pt.region([[at(-1.0, -h), at(w, -h), at(w, 0.6 * k), at(-1.0, 0.6 * k)]], PAPER, outline=FINE * 1.1)
    pt.line([at(-1.0, -h), at(w * 0.48, -h * 0.35), at(w, -h)], PAPER_DARK, FINE * 0.9, smooth=False)
    seal = at(w * 0.48, -h * 0.35)
    pt.region([[(seal[0] + 1.1 * k * math.cos(t), seal[1] + 1.1 * k * math.sin(t)) for t in (i * math.tau / 10 for i in range(10))]], SEAL,
              outline=FINE * 0.7)
    return [Part("letter", "far_grip", zmap["far_arm_hand"] + 0.2, pt.els, "Sealed Letter (in her left fist)", opacity="prop.letter",
                 opacity_default=0)]


def alice_parts(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    """Every part of Alice's own (the ``chargen.extras`` hook)."""
    return (hair_parts(ctx) + ornament_parts(ctx) + satchel_parts(ctx, zmap) + tie_parts(ctx, zmap) + wheel_parts(ctx, zmap)
            + teal_parts(ctx, zmap) + piping_parts(ctx, zmap) + cuff_parts(ctx, zmap) + boot_parts(ctx, zmap)
            + pole_parts(ctx, zmap) + letter_parts(ctx, zmap))


__all__ = ["POLE_BUTT", "POLE_LENGTH", "alice_parts", "pole_paint"]
