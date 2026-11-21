"""Western gear for generated residents: a cowboy hat, a gun belt with a
holster, a poncho, a basket muzzle, a bushy tail.

The first wearer is Peyote Lean, the coyote outlaw who rides with Marshal
Gallus (``data/townsfolk/frontier_peyote_lean.chargen.yaml``; concept art
``assets/concept_art/misc/Peyote Lean*.png``). Each function draws parts
from the figure in 3D, in every view, as the other gear of
``_townsfolk_gear`` does; a resident names them in ``game.gear``.

Units are the figure's: centimetres, ``x`` to the body's left, ``y`` down
(the ground is 0), ``z`` forward. In a side view the body's right
(``x < 0``) is the near side.
"""

from __future__ import annotations

import math
from typing import Dict, List, Sequence, Tuple

from ...chargen.drawkit import Ctx, Part, bands, shaded_region, surface_line, visible
from ...chargen.geometry import Loft, RingKey, lerp, loft_region
from ...chargen.svgout import FINE, INK, shade

Point = Tuple[float, float]
Vec3 = Tuple[float, float, float]

LEATHER = "#5e3c25"
LEATHER_DARK = "#3e2618"
BRASS = "#c9a04a"
STEEL = "#8f969e"
STEEL_LIGHT = "#cdd2d6"
GUNMETAL = "#4a4d55"
GRIP_WOOD = "#7a4a2a"


def _y(ctx: Ctx, f: float) -> float:
    """The height of the head's fraction ``f`` (0 the crown, 1 the chin)."""
    return ctx.fig.crown + f * ctx.fig.hh


# ---- the hat ---------------------------------------------------------------------------------

HAT = "#5a3f2b"
HAT_BAND = "#8e3a2c"
HAT_BAND_MARK = "#e2d2ae"


def cowboy_hat(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    """A wide-brimmed cowboy hat: a tall crown pinched at the front and
    creased on top, a band, and a brim whose sides turn up. It sits on the
    skull above the brow; a resident's ears stand up through it (the ears
    are drawn over the hat)."""
    fig = ctx.fig
    hh = fig.hh
    sit = fig.crown + 0.24 * hh
    base = fig.skull.section(sit)
    g = 0.03 * hh
    rx, rzf, rzb, cl, cz = base.rx + g, base.rzf + g, base.rzb + g, base.cl, base.cz
    top = sit - 0.48 * hh
    crown = Loft([
        RingKey(top, rx * 0.6, rzf * 0.42, rzb * 0.66, cl, cz - 0.05 * hh, 2.8),
        RingKey(top + 0.08 * hh, rx * 0.86, rzf * 0.74, rzb * 0.9, cl, cz - 0.02 * hh, 2.4),
        RingKey(sit - 0.22 * hh, rx * 0.97, rzf * 0.93, rzb * 0.97, cl, cz, 2.2),
        RingKey(sit - 0.01 * hh, rx, rzf, rzb, cl, cz, 2.2),
    ])
    # The brim: flat at the front and the back, turned up at the sides (the
    # upper ring is wider across and shallower front to back).
    wide = 0.46 * hh
    brim = Loft([
        RingKey(sit - 0.1 * hh, rx + wide * 1.06, rzf + wide * 0.5, rzb + wide * 0.56, cl, cz, 2.3),
        RingKey(sit - 0.01 * hh, rx + wide, rzf + wide * 0.86, rzb + wide * 0.9, cl, cz, 2.2),
        RingKey(sit + 0.03 * hh, rx + wide * 0.9, rzf + wide * 0.8, rzb + wide * 0.84, cl, cz, 2.2),
    ])
    pt = ctx.new()
    shaded_region(ctx, pt, brim, brim.top, brim.bottom, HAT, shade_frac=0.12)
    if not shaded_region(ctx, pt, crown, crown.top, crown.bottom, HAT, lit=True):
        return []
    # The band, with a stepped pattern of pale marks.
    y0, y1 = sit - 0.15 * hh, sit - 0.04 * hh
    shell = crown.shell(0.12)
    pt.region(loft_region(ctx.view, shell, y0, y1), HAT_BAND, outline=FINE)
    pt.flat(loft_region(ctx.view, shell.shell(0.05), y0 + 0.025 * hh, y1 - 0.025 * hh, bands([a for a in range(-180, 180, 30)], 5.0)),
            HAT_BAND_MARK)
    # The crease along the top of the crown, seen from in front or behind.
    crease = [(a, top + 0.05 * hh) for a in (-20.0, -10.0, 0.0)]
    for run in surface_line(ctx, crown, crease + [(180.0, top + 0.05 * hh)], out=0.05, thresh=0.2):
        pt.line(run, INK, FINE * 1.2)
    return [Part("cowboy_hat", "head", 58.0, pt.els, "Cowboy hat")]


# ---- the basket muzzle -----------------------------------------------------------------------


def _snout(ctx: Ctx) -> Tuple[float, float, List[Tuple[float, float, float, float]]]:
    """The snout of an animal head, measured from its loft: the depth of
    its root and of its tip, and at each of eight depths between them the
    snout's half-width and its top and bottom."""
    fig = ctx.fig
    head = fig.head
    # The root: a little behind the front of the snout's top, under the
    # eyes, so the cage does not hide them.
    upper = head.section(_y(ctx, 0.5))
    z_root = upper.cz + upper.rzf * 0.62
    tip_ring = max((head.section(_y(ctx, f / 100.0)) for f in range(45, 90)), key=lambda k: k.cz + k.rzf)
    z_tip = tip_ring.cz + tip_ring.rzf
    out = []
    for i in range(8):
        z = lerp(z_root, z_tip, i / 7.0)
        top, bottom, half = None, None, 0.0
        for f in range(48, 96):
            k = head.section(_y(ctx, f / 100.0))
            reach = k.cz + k.rzf
            if reach < z - 1e-6:
                continue
            u = max(0.0, (z - k.cz) / max(k.rzf, 1e-6)) if z > k.cz else 0.0
            e = max(1.0, k.sq)
            w = k.rx * max(0.0, 1.0 - u ** e) ** (1.0 / e)
            half = max(half, w)
            y = _y(ctx, f / 100.0)
            top = y if top is None else min(top, y)
            bottom = y if bottom is None else max(bottom, y)
        if top is not None:
            out.append((z, half, top, bottom))
    return z_root, z_tip, out


def muzzle_cage(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    """A basket muzzle of steel over an animal's snout: hoops round it and
    bars along it, held by leather straps over the brow and round the back
    of the head, with a brass buckle at the cheek. The bars on the far side
    of the snout are a part of their own under the head: they show only
    where they pass beyond it."""
    fig = ctx.fig
    hh = fig.hh
    z_root, z_tip, rows = _snout(ctx)
    if len(rows) < 3:
        return []
    m = 0.035 * hh
    view = ctx.view
    s, c, sp = view.s, view.c, view.sp

    def hoop_point(i: float, th: float) -> Vec3:
        """The point at ``th`` degrees round the hoop at depth index ``i``
        (0 the top, 90 the body's left, 180 the bottom)."""
        lo = int(min(len(rows) - 2, max(0, math.floor(i))))
        t = i - lo
        z, half, top, bottom = (lerp(a, b, t) for a, b in zip(rows[lo], rows[lo + 1]))
        # The cage runs past the nose and closes in front of it.
        if i >= len(rows) - 1:
            z += m * 0.8
        a = half + m
        b = (bottom - top) / 2.0 + m
        yc = (top + bottom) / 2.0
        r = math.radians(th)
        e = 2.0 / 2.6
        sa, ca = math.sin(r), math.cos(r)
        return (a * math.copysign(abs(sa) ** e, sa), yc - b * math.copysign(abs(ca) ** e, ca), z)

    def faces(th: float) -> float:
        # Seen from behind, the head is between the camera and the cage.
        if c < -0.2:
            return -1.0
        r = math.radians(th)
        return -math.sin(r) * s + math.cos(r) * sp

    near, far = ctx.new(), ctx.new()
    bar_w, ink_w = 0.042 * hh, 0.075 * hh

    def stroke(pt, pts: Sequence[Point]) -> None:
        pt.line(pts, INK, ink_w, fixed=True)
        pt.line(pts, STEEL, bar_w, fixed=True)

    last = len(rows) - 1
    # The bars along the snout.
    for th in range(-144, 181, 36):
        pts = [ctx.p(hoop_point(i * last / 6.0, th)) for i in range(7)]
        pts.append(ctx.p(hoop_point(last + 0.001, th)))
        stroke(near if faces(th) > -0.05 else far, pts)
    # The hoops round it: the root, two between, and the front.
    for i in (0.0, last * 0.4, last * 0.75, float(last)):
        run: List[Point] = []
        side = None
        for th in range(-180, 181, 10):
            vis = faces(th) > -0.05
            if side is not None and vis != side and len(run) >= 2:
                stroke(near if side else far, run)
                run = run[-1:]
            side = vis
            run.append(ctx.p(hoop_point(i, th)))
        if len(run) >= 2:
            stroke(near if side else far, run)
    # The face of the cage in front of the nose: a cross of bars.
    front = [hoop_point(last + 0.001, th) for th in (0.0, 90.0, 180.0, 270.0)]
    tip = (0.0, (front[0][1] + front[2][1]) / 2.0, front[0][2] + 0.25 * m)
    for p in front:
        stroke(near if c > 0.15 else far, [ctx.p(p), ctx.p(tip)])
    # A light glint along the near top bar.
    if c > -0.5:
        glint = [ctx.p(hoop_point(i * last / 4.0, -20.0 if s >= 0 else 20.0)) for i in range(5)]
        near.line(glint, STEEL_LIGHT, bar_w * 0.4, fixed=True)
    # The straps: up the brow to the crown, and from the cheek round the
    # back of the head under the ears.
    head = fig.head
    strap_w, strap_ink = 0.08 * hh, 0.12 * hh
    brow = [(0.0, _y(ctx, f)) for f in (0.47, 0.4, 0.32, 0.24, 0.16)]
    for run in surface_line(ctx, head, brow, out=0.2, thresh=0.0):
        near.line(run, INK, strap_ink, fixed=True)
        near.line(run, LEATHER, strap_w, fixed=True)
    for sgn in (-1.0, 1.0):
        line = [(sgn * a, _y(ctx, lerp(0.56, 0.2, max(0.0, a - 70.0) / 110.0))) for a in range(50, 181, 10)]
        for run in surface_line(ctx, head, line, out=0.2, thresh=0.0):
            near.line(run, INK, strap_ink, fixed=True)
            near.line(run, LEATHER, strap_w, fixed=True)
        if visible(ctx, sgn * 72.0, 0.2):
            b = ctx.p(head.point(sgn * 72.0, _y(ctx, 0.52), 0.35))
            r = 0.07 * hh
            near.region([[(b[0] - r, b[1] - r), (b[0] + r, b[1] - r), (b[0] + r, b[1] + r), (b[0] - r, b[1] + r)]], BRASS, outline=FINE)
    out = []
    if near.els:
        out.append(Part("muzzle_cage", "head", 56.0, near.els, "Muzzle cage"))
    if far.els:
        out.append(Part("muzzle_cage_back", "head", 49.5, far.els, "Muzzle cage (far side)"))
    return out


# ---- the tail --------------------------------------------------------------------------------

TAIL_TIP = "#3b2f27"


def bushy_tail(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    """A long bushy tail that hangs from the base of the spine down behind
    the legs, in the coat's colour with a pale underside and a dark tip,
    its edges in tufts. It is behind the body in a front or a side view and
    over it from behind."""
    fig = ctx.fig
    view = ctx.view
    sec = fig.torso.section(fig.y_hip)
    root = (0.0, fig.y_hip - 2.0, sec.cz - sec.rzb + 1.5)
    spine3 = [root, (0.0, root[1] + 12.0, root[2] - 10.0), (0.0, root[1] + 27.0, root[2] - 18.0),
              (0.0, root[1] + 36.0, root[2] - 22.0), (0.0, root[1] + 46.0, root[2] - 21.0)]
    radius = [2.6, 5.4, 7.0, 6.0, 0.6]
    # Resample the spine: a Catmull-Rom curve through its points.
    pts: List[Vec3] = []
    rad: List[float] = []
    n = 26
    for i in range(n + 1):
        u = i / n * (len(spine3) - 1)
        j = min(int(u), len(spine3) - 2)
        t = u - j
        p0, p1, p2, p3 = spine3[max(j - 1, 0)], spine3[j], spine3[j + 1], spine3[min(j + 2, len(spine3) - 1)]
        pts.append(tuple(0.5 * (2 * b + (-a + cc) * t + (2 * a - 5 * b + 4 * cc - d) * t * t + (-a + 3 * b - 3 * cc + d) * t ** 3)
                         for a, b, cc, d in zip(p0, p1, p2, p3)))
        rad.append(lerp(radius[j], radius[j + 1], t))
    scr = [ctx.p(p) for p in pts]

    def edge(sign: float, scale: float, tufts: bool) -> List[Point]:
        out = []
        for i, (x, y) in enumerate(scr):
            a = scr[max(i - 1, 0)]
            b = scr[min(i + 1, len(scr) - 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            d = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / d, dx / d
            w = rad[i] * scale
            if tufts and 0.2 < i / n < 0.97:
                w *= 1.16 if i % 2 else 0.9
            out.append((x + sign * nx * w, y + sign * ny * w))
        return out

    pt = ctx.new()
    body = edge(1.0, 1.0, True) + edge(-1.0, 1.0, True)[::-1]
    pt.region([body], ctx.skin)
    # The pale underside: the half of the tail toward the ground's side.
    under = edge(1.0, 0.85, False) + scr[::-1]
    lower = under if sum(p[1] for p in edge(1.0, 1.0, False)) > sum(p[1] for p in edge(-1.0, 1.0, False)) else \
        edge(-1.0, 0.85, False) + scr[::-1]
    pt.flat([lower], ctx.hair)
    # The dark tip.
    k = int(n * 0.8)
    tip = edge(1.0, 1.05, False)[k:] + edge(-1.0, 1.05, False)[k:][::-1]
    pt.flat([tip], TAIL_TIP)
    # A few strokes of fur down its length.
    for off in (-0.35, 0.3):
        mid = edge(1.0 if off > 0 else -1.0, abs(off), False)[4:int(n * 0.7)]
        pt.line(mid, shade(ctx.skin, 0.25), FINE * 1.2)
    z = 44.6 if view.c < -0.3 else 0.5
    return [Part("tail", "pelvis", z, pt.els, "Tail")]


# ---- the poncho ------------------------------------------------------------------------------

PONCHO = "#9a3b2b"
PONCHO_BAND = "#e2d2ae"
PONCHO_DARK = "#5c2219"


def poncho(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    """A short poncho over the shoulders and the arms to the waist, in a
    subdued red, with a pale band of stepped marks above its hem and a
    fringe. The arms come out from under it."""
    fig = ctx.fig
    T = fig.H
    j = fig.joints
    neck = fig.torso.section(fig.y_nb)
    chest = fig.torso.section(fig.y_chest)
    shoulder = abs(j["right_shoulder"][0]) + 0.034 * T
    hem = fig.y_waist - 0.012 * T
    loft = Loft([
        RingKey(fig.y_nb - 1.0, neck.rx + 1.2, neck.rzf + 1.4, neck.rzb + 1.2, 0.0, neck.cz, 2.0),
        RingKey(fig.y_sh, shoulder, chest.rzf + 2.4, chest.rzb + 2.4, 0.0, chest.cz, 2.3),
        RingKey(lerp(fig.y_sh, hem, 0.5), shoulder + 1.6, chest.rzf + 4.6, chest.rzb + 4.4, 0.0, chest.cz, 2.3),
        RingKey(hem, shoulder + 3.0, chest.rzf + 6.4, chest.rzb + 6.0, 0.0, chest.cz, 2.3),
    ])
    pt = ctx.new()
    if not shaded_region(ctx, pt, loft, loft.top, loft.bottom, PONCHO, lit=True):
        return []
    # The band and its stepped marks.
    b0, b1 = hem - 0.045 * T, hem - 0.018 * T
    shell = loft.shell(0.05)
    pt.flat(loft_region(ctx.view, shell, b0, b1), PONCHO_BAND)
    mid = (b0 + b1) / 2.0
    pt.flat(loft_region(ctx.view, shell.shell(0.03), b0 + 0.004 * T, mid, bands([a for a in range(-180, 180, 24)], 5.0)), PONCHO)
    pt.flat(loft_region(ctx.view, shell.shell(0.03), mid, b1 - 0.004 * T, bands([a + 12 for a in range(-180, 180, 24)], 5.0)), PONCHO)
    pt.flat(loft_region(ctx.view, shell, hem - 0.012 * T, hem - 0.004 * T), PONCHO_DARK)
    # The fringe under the hem.
    for a in range(-180, 180, 9):
        if not visible(ctx, float(a), 0.05):
            continue
        top = loft.point(float(a), hem, 0.1)
        p0 = ctx.p(top)
        p1 = ctx.p((top[0], top[1] + 0.03 * T, top[2]))
        pt.line([p0, p1], INK, 0.9, smooth=False)
        pt.line([p0, p1], PONCHO_BAND, 0.5, smooth=False)
    # The opening for the head.
    for run in surface_line(ctx, loft, [(a, fig.y_nb - 0.6) for a in range(-180, 181, 10)], out=0.05, thresh=0.0):
        pt.line(run, PONCHO_DARK, FINE * 2.2)
    return [Part("poncho", "torso", 44.5, pt.els, "Poncho")]


# ---- the gun belt ----------------------------------------------------------------------------


def gun_belt(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    """A gun belt over the coat at the waist, its loops full of brass
    cartridges, and a holster on the near hip with the grip of a revolver
    standing out of it."""
    fig = ctx.fig
    T = fig.H
    t = ctx.plan.get("outer_t", 0.6) if isinstance(ctx.plan, dict) else 0.6
    shell = fig.torso.shell(float(t) + 1.1)
    y = fig.y_belt + 0.004 * T
    pt = ctx.new()
    if not shaded_region(ctx, pt, shell, y - 0.016 * T, y + 0.016 * T, LEATHER, shade_frac=0.1):
        return []
    for a in range(-170, 171, 13):
        if abs(a) < 18 or not visible(ctx, float(a), 0.15):
            continue
        p = ctx.p(shell.point(float(a), y, 0.35))
        pt.dot(p, 0.75, INK)
        pt.dot(p, 0.5, BRASS)
    if visible(ctx, 0.0, 0.1):
        c = shell.point(0.0, y, 0.4)
        w, h = 2.2, 1.9
        quad = [ctx.p((c[0] + dx, c[1] + dy, c[2])) for dx, dy in ((-w, -h), (w, -h), (w, h), (-w, h))]
        pt.region([quad], BRASS, outline=FINE)
    out = [Part("gun_belt", "pelvis", 33.4, pt.els, "Gun belt")]
    # The holster on the near (right) hip, and the revolver's grip.
    if ctx.view.facing(-95.0) > -0.35:
        top = shell.point(-98.0, y + 0.012 * T, 0.6)
        x0 = top[0] - 1.2
        y0, z0 = top[1], top[2]
        hol = [(x0, y0, z0 + 3.6), (x0, y0, z0 - 3.2), (x0, y0 + 0.11 * T, z0 - 1.6), (x0, y0 + 0.125 * T, z0 + 1.0),
               (x0, y0 + 0.1 * T, z0 + 3.4)]
        hp = ctx.new()
        grip = [(x0, y0 + 1.0, z0 - 2.4), (x0, y0 - 0.035 * T, z0 - 4.8), (x0, y0 - 0.041 * T, z0 - 2.4), (x0, y0 + 0.5, z0 + 0.4)]
        hp.region([[ctx.p(p) for p in grip]], GRIP_WOOD, outline=FINE)
        hammer = [(x0, y0 - 0.6, z0 + 0.2), (x0, y0 - 0.02 * T, z0 + 0.8), (x0, y0 - 0.012 * T, z0 + 1.8), (x0, y0 + 0.4, z0 + 1.6)]
        hp.region([[ctx.p(p) for p in hammer]], GUNMETAL, outline=FINE)
        hp.region([[ctx.p(p) for p in hol]], LEATHER, outline=FINE * 1.4)
        stitch = [ctx.p((x0 - 0.2, y0 + 0.012 * T, z0 + 2.4)), ctx.p((x0 - 0.2, y0 + 0.095 * T, z0 + 2.2))]
        hp.line(stitch, LEATHER_DARK, FINE * 1.2)
        out.append(Part("holster", "pelvis", 33.6, hp.els, "Holster"))
    return out


__all__ = ["bushy_tail", "cowboy_hat", "gun_belt", "muzzle_cage", "poncho"]
