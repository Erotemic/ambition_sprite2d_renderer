"""Clothes, hats and worn accessories, each as its own rig parts.

Every component is a set of parts tagged with one ``feature``
(``"slot:kind"``, e.g. ``"outer:coat"``) and painted at a fixed depth above
the body segment it covers (``LAYER``), so a component can be hidden or
swapped for another without redrawing anything else, in every view and pose.
A sleeve rides its arm bone, a trouser leg its leg bone, a coat's skirt the
thigh on its side (the right half of the coat on the right thigh): when a
leg swings, its half of the skirt swings with it.

What hangs below the knees (a long skirt, a robe, a long coat) is also drawn
down each leg in its cloth (the *drape*), so a stride never cuts a bare leg
through the rigid skirt.
"""

from __future__ import annotations

import math
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .body import Figure
from .drawkit import (
    SIDES,
    Ctx,
    Part,
    all_of,
    bands,
    between,
    half_of,
    segment,
    shaded_region,
    surface_line,
    tube3,
    visible,
)
from .family import family_of
from .geometry import Loft, RingKey, Vec3, add3, hull, lerp, loft_region, smoothstep, wrap180
from .svgout import FINE, INK, Paint, light, shade

#: How far above its segment each slot paints.
LAYER = {"legwear": 0.1, "top": 0.2, "outer": 0.3, "footwear": 0.35, "acc": 0.4}


def _part(name: str, bone: str, z: float, pt: Paint, label: str, feature: str) -> Optional[Part]:
    return Part(name, bone, z, pt.els, label, feature=feature) if pt.els else None


# ---- shared garment geometry ----------------------------------------------------------------


def neckline(fig: Figure, kind: str):
    T = fig.T
    top = fig.y_nb + 0.4

    def m(alpha: float, y: float) -> float:
        al = abs(wrap180(alpha))
        if kind == "v":
            depth = 0.2 * T * max(0.0, 1.0 - al / 24.0)
        elif kind == "scoop":
            depth = 0.11 * T * max(0.0, math.cos(math.radians(min(90.0, al * 1.6))))
        else:
            depth = 0.0
        return y - (top + depth)

    return m


def opening(fig: Figure, half: float, lapel: float):
    """Covered away from a front opening of ``half`` degrees, wider by
    ``lapel`` at the neck (a V down to the chest)."""
    T = fig.T

    def m(alpha: float, y: float) -> float:
        w = half + lapel * (1.0 - smoothstep(fig.y_nb, fig.y_chest + 0.12 * T, y))
        return (abs(wrap180(alpha)) - w) * 0.2

    return m


def skirt_loft(fig: Figure, y_top: float, hem: float, t: float, flare: float) -> Loft:
    tk = fig.torso
    w, h, c = tk.section(fig.y_waist), tk.section(fig.y_hipw), tk.section(fig.y_crotch)
    knee = fig.joints["right_knee"]
    leg_x = abs(knee[0]) + fig.leg_r[1] + 1.2
    keys = [
        RingKey(y_top, w.rx + t, w.rzf + t, w.rzb + t, 0.0, w.cz, 2.3),
        RingKey(fig.y_hipw, h.rx + t, h.rzf + t, h.rzb + t, 0.0, 0.0, 2.3),
        RingKey(fig.y_crotch, max(c.rx, h.rx * 0.98) + t * 1.2, h.rzf + t * 1.1, h.rzb + t * 1.1, 0.0, 0.0, 2.2),
    ]
    rx_hem = max(leg_x, (h.rx + t) * flare)
    keys.append(RingKey(hem, rx_hem, max(h.rzf + t, 10.0 * fig.k) * (0.9 + 0.25 * (flare - 1.0)) + 1.5,
                        (h.rzb + t) * (0.95 + 0.2 * (flare - 1.0)), 0.0, 0.0, 2.1))
    return Loft([kk for kk in keys if kk.y <= hem + 1e-6])


def lobe_parts(ctx: Ctx, slot: str, feature: str, loft: Loft, y0: float, y1: float, color: str, margin=None, *,
               z: Tuple[float, float], lit: bool = True, extra: Optional[Callable[[Paint, str], None]] = None,
               solid: bool = True) -> List[Part]:
    """A hanging garment as two halves, one on each leg: the right half (the
    near side) above the left one. A half that hangs well past the knee is
    cut there: the part above rides the thigh, the part below the shin, so a
    long skirt or robe bends with the stride instead of swinging out as one
    rigid board."""
    out = []
    knee = ctx.fig.joints["right_knee"][1]
    split = y1 > knee + 0.12 * (knee - y0)
    lap = 0.05 * (knee - y0)
    for depth, side, _sgn in SIDES:
        m = half_of(side) if margin is None else all_of(margin, half_of(side))
        zz = z[0] if depth == "far" else z[1]
        pieces = [(y0, knee + lap, "leg_u", ""), (knee - lap, y1, "leg_l", "_lower")] if split else [(y0, y1, "leg_u", "")]
        for a, b, bone, suffix in pieces:
            pt = ctx.new()
            # Each piece is drawn whole (its back as well as its front; not an
            # apron, a front panel only), so
            # a leg swinging out behind keeps its cloth. The shin's piece is
            # inked from the knee down but filled from above it, so its top
            # edge hides under its own cloth: no seam at the knee.
            pt.region(loft_region(ctx.view, loft, knee if suffix else a, b, m, solid=solid), color)
            if suffix:
                pt.flat(loft_region(ctx.view, loft, a, b, m, solid=solid), color)
            shaded_region(ctx, pt, loft, a, b, color, m, lit=lit, ink=False)
            if extra and not suffix:
                extra(pt, side)
            p = _part(f"{depth}_skirt{suffix}__{slot}", f"{depth}_{bone}", zz + (0.05 if suffix else 0.0), pt,
                      f"Skirt{' (below the knee)' if suffix else ''} - {depth.title()} ({slot})", feature)
            if p:
                out.append(p)
    return out


def drape_color(ctx: Ctx, slot: str) -> Optional[Tuple[str, float]]:
    """The cloth of ``slot`` that hangs over the knees, and its hem."""
    fig, o, plan = ctx.fig, ctx.fig.spec.outfit, ctx.plan
    knee = fig.joints["right_knee"][1]
    found = None
    if slot == "legwear" and plan["bottom_hem"] and plan["bottom_hem"] > knee:
        found = (o.bottom_color, plan["bottom_hem"])
    if slot == "top" and o.top == "tunic" and not plan["tucked"] and plan["top_hem"] > knee:
        found = (o.top_color, plan["top_hem"])
    if slot == "outer" and o.outer in ("coat", "robe", "cardigan") and plan["outer_hem"] > knee:
        found = (o.outer_color, plan["outer_hem"])
    # Stop short of the hem: at rest the drape stays under the skirt, whose
    # hem curves up at the sides in a view from a little above.
    return None if found is None else (found[0], found[1] - 0.06 * fig.T)


def drape_parts(ctx: Ctx, slot: str, feature: str, zmap: Dict[str, float]) -> List[Part]:
    d = drape_color(ctx, slot)
    if d is None:
        return []
    fig = ctx.fig
    out = []
    j = fig.joints
    rt, rk, rc, ra = fig.leg_r
    for depth, side, _sgn in SIDES:
        Hp, K, A = j[f"{side}_hip"], j[f"{side}_knee"], j[f"{side}_ankle"]
        pt = ctx.new()
        f = max(0.0, min(1.0, (d[1] - Hp[1]) / max(1e-6, K[1] - Hp[1])))
        aa, bb = segment(Hp, K, 0.0, f)
        tube3(ctx, pt, aa, bb, rt + 2.5, lerp(rt, rk, f) + 3.0, d[0], round_b=f >= 1.0)
        p = _part(f"{depth}_leg_u__{slot}_drape", f"{depth}_leg_u", zmap[f"{depth}_leg_u"] + LAYER[slot] + 0.02, pt, f"Thigh drape - {depth}",
                  feature)
        if p:
            out.append(p)
        f2 = max(0.0, min(1.0, (d[1] - K[1]) / max(1e-6, A[1] - K[1])))
        if f2 > 0.02:
            pt = ctx.new()
            aa, bb = segment(K, A, 0.0, f2)
            tube3(ctx, pt, aa, bb, rc + 3.0, lerp(rc, ra, f2) + 3.6, d[0], round_b=False)
            p = _part(f"{depth}_leg_l__{slot}_drape", f"{depth}_leg_l", zmap[f"{depth}_leg_l"] + LAYER[slot] + 0.02, pt,
                      f"Shin drape - {depth}", feature)
            if p:
                out.append(p)
    return out


def _sleeve(ctx: Ctx, side: str, piece: str, reach: float, add: float, color: str, *, rolled: bool = False, cuff: bool = False,
            wide: float = 0.0) -> Paint:
    """A sleeve over one arm segment, from the shoulder to ``reach`` (0 the
    shoulder, 1 the wrist)."""
    fig = ctx.fig
    j = fig.joints
    S, E, W = (j[f"{side}_{n}"] for n in ("shoulder", "elbow", "wrist"))
    rs, re, rw = fig.arm_r
    ua, fa = math.dist(S, E), math.dist(E, W)
    total = ua + fa
    pt = ctx.new()
    if piece == "upper":
        a, b, r0, r1, f0, f1 = S, E, rs * 0.86, re, 0.0, ua / total
    else:
        a, b, r0, r1, f0, f1 = E, W, re * 0.97, rw, ua / total, 1.0
    if reach <= f0:
        return pt
    tt = min(1.0, (reach - f0) / (f1 - f0))
    aa, bb = segment(a, b, 0.0, tt)
    rr1 = lerp(r0, r1, tt) + add + (wide if piece == "lower" else 0.0)
    joint = tt >= 1.0 and piece == "upper"
    tube3(ctx, pt, aa, bb, r0 + add * (0.55 if piece == "upper" else 1.0), rr1, color, round_b=joint, joint_b=joint)
    if rolled and tt < 1.0:
        ca, cb = segment(a, b, max(0.0, tt - 0.16), tt)
        tube3(ctx, pt, ca, cb, lerp(r0, r1, tt - 0.16) + add + 0.5, rr1 + 0.5, light(color, 0.12), band=False, round_a=False, round_b=False)
    elif cuff and tt >= 1.0 and piece == "lower":
        ca, cb = segment(a, b, 0.84, 1.0)
        tube3(ctx, pt, ca, cb, lerp(r0, r1, 0.84) + add + 0.25, rr1 + 0.25, shade(color, 0.12), band=False, round_a=False, round_b=False)
    return pt


def sleeve_parts(ctx: Ctx, slot: str, feature: str, reach: float, add: float, color: str, zmap: Dict[str, float], **kw) -> List[Part]:
    out = []
    for depth, side, _sgn in SIDES:
        for piece, seg in (("upper", "arm_u"), ("lower", "arm_l")):
            pt = _sleeve(ctx, side, piece, reach, add, color, **kw)
            p = _part(f"{depth}_{seg}__{slot}", f"{depth}_{seg}", zmap[f"{depth}_{seg}"] + LAYER[slot], pt, f"Sleeve - {depth} {piece}",
                      feature)
            if p:
                out.append(p)
    return out


# ---- the top ----------------------------------------------------------------------------------


def top_parts(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    fig, o, plan = ctx.fig, ctx.fig.spec.outfit, ctx.plan
    feature = f"top:{o.top}"
    T = fig.T
    pt = ctx.new()
    shirt = fig.torso.shell(0.3)
    top = fig.torso.top
    lower = o.top == "tunic" and not plan["tucked"]
    # The body of the top covers the torso down to its hem or the crotch
    # (a tunic's skirt over the legs is its lobes), so no skin shows
    # between the top and what hangs from it.
    hem = min(plan["top_hem"], fig.y_crotch)
    neck = neckline(fig, o.neckline)
    shaded_region(ctx, pt, shirt, top, hem, o.top_color, all_of(neck, between(top - 1, hem)), lit=True)
    if o.top == "sweater":
        rib = shade(o.top_color, 0.12)
        pt.flat(loft_region(ctx.view, shirt, top, fig.y_nb + 1.6, all_of(neck, between(fig.y_nb + 0.2, fig.y_nb + 1.6))), rib)
        if not lower:
            pt.flat(loft_region(ctx.view, shirt, hem - 2.2, hem), rib)
    if o.neckline == "collar":
        _collar(ctx, pt, shirt, o.top_color)
        if o.top in ("shirt", "blouse"):
            _buttons(ctx, pt, shirt, [0.0], fig.y_nb + 0.12 * T, hem - 0.06 * T, 4, light(o.top_color, 0.35))
    out = [Part("torso__top", "torso", zmap["torso"] + LAYER["top"], pt.els, "Top", feature=feature)]
    reach = {"short": 0.3 if o.top != "tshirt" else 0.28, "long": 1.0, "rolled": 0.62}[o.sleeves]
    if o.top == "sweater":
        reach = max(reach, 0.62)
    out += sleeve_parts(ctx, "top", feature, reach, 0.45 + (0.25 if o.top == "sweater" else 0.0), o.top_color, zmap,
                        rolled=o.sleeves == "rolled")
    if lower:
        tk = skirt_loft(fig, fig.y_waist, plan["top_hem"], 0.9, 1.08)
        out += lobe_parts(ctx, "top", feature, tk, fig.y_waist, plan["top_hem"], o.top_color, z=(21.0, 21.5))
        out += drape_parts(ctx, "top", feature, zmap)
    return out


def _collar(ctx: Ctx, pt: Paint, shell: Loft, color: str) -> None:
    fig = ctx.fig
    y = fig.y_nb + 0.6
    for sgn in (-1.0, 1.0):
        a0, a1 = sgn * 6.0, sgn * 34.0
        if not (visible(ctx, a0, 0.0) or visible(ctx, a1, 0.0)):
            continue
        tri = [shell.point(a0, y - 0.3, 0.6), shell.point(a1, y - 0.6, 0.8), shell.point(sgn * 14.0, y + 0.075 * fig.T, 0.9)]
        pt.region([[ctx.p(q) for q in tri]], light(color, 0.12), outline=FINE * 0.8)


def _buttons(ctx: Ctx, pt: Paint, shell: Loft, alphas: Sequence[float], y0: float, y1: float, n: int, color: str) -> None:
    for a in alphas:
        if not visible(ctx, a, 0.25):
            continue
        for i in range(n):
            y = lerp(y0, y1, i / max(1, n - 1))
            pt.dot(ctx.p(shell.point(a, y, 0.3)), 0.45, INK)
            pt.dot(ctx.p(shell.point(a, y, 0.35)), 0.3, color)


# ---- the outer layer ---------------------------------------------------------------------------


def outer_parts(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    fig, o, plan = ctx.fig, ctx.fig.spec.outfit, ctx.plan
    if o.outer == "none":
        return []
    feature = f"outer:{o.outer}"
    T = fig.T
    t = plan["outer_t"]
    shell = fig.torso.shell(t)
    col = o.outer_color
    top = fig.torso.top
    hem = plan["outer_hem"]
    torso_bottom = min(hem, fig.y_waist + 0.06 * T) if hem > fig.y_crotch - 0.05 * T else min(hem, fig.y_crotch)
    pt = ctx.new()
    out: List[Part] = []
    lower_margin = None
    if o.outer == "apron":
        bib = fig.y_chest - 0.04 * T

        def m(a: float, y: float) -> float:
            w = lerp(26.0, 50.0, smoothstep(fig.y_under - 0.05 * T, fig.y_under + 0.05 * T, y))
            return min((w - abs(wrap180(a))) * 0.2, y - bib)

        shaded_region(ctx, pt, shell, bib, torso_bottom, col, m)
        straps = [(-24.0, bib), (-30.0, fig.y_nb + 2.0), (-90.0, fig.y_nb - 0.5), (-150.0, fig.y_nb + 1.0)]
        for sgn in (1.0, -1.0):
            for run in surface_line(ctx, shell, [(sgn * a, y) for a, y in straps], out=0.1, thresh=0.0):
                pt.line(run, INK, 1.25, smooth=True)
                pt.line(run, col, 0.7, smooth=True)
        pt.flat(loft_region(ctx.view, shell, fig.y_waist - 0.025 * T, fig.y_waist + 0.025 * T), shade(col, 0.15))
        if visible(ctx, 180.0, 0.4):
            c = shell.point(180.0, fig.y_waist, 0.5)
            k = 1 if ctx.view.c < 0 else -1
            for dx in (-1.0, 1.0):
                bow = [ctx.p(add3(c, d)) for d in ((0, -0.6, 0), (dx * 3.2 * k, -1.8, 0), (dx * 3.2 * k, 1.6, 0), (0, 0.6, 0))]
                pt.region([bow], col, outline=FINE)
        lower_margin = lambda a, y: (50.0 - abs(wrap180(a))) * 0.2  # noqa: E731
    elif o.outer == "robe":
        shaded_region(ctx, pt, shell, top, torso_bottom, col, None, lit=True)
        line = [(lerp(-34.0, 12.0, i / 10.0), lerp(fig.y_nb + 0.5, fig.y_under, i / 10.0)) for i in range(11)]
        for run in surface_line(ctx, shell, line, out=0.1):
            pt.line(run, INK, FINE * 1.3)
        pt.region(loft_region(ctx.view, shell.shell(0.3), fig.y_waist - 0.04 * T, fig.y_waist + 0.04 * T), o.accent_color, outline=FINE)
    elif o.outer == "field_jacket":
        _field_jacket(ctx, pt, shell, torso_bottom)
    else:
        half, lapel = {"vest": (6.0, 30.0), "jacket": (9.0, 22.0), "coat": (10.0, 24.0), "cardigan": (11.0, 16.0)}[o.outer]
        if not o.outer_open and o.outer != "vest":
            half, lapel = 0.0, 18.0 if o.outer != "cardigan" else 12.0
        shaded_region(ctx, pt, shell, top, torso_bottom, col, opening(fig, half, lapel), lit=True)
        if o.outer in ("jacket", "coat") and lapel:
            for sgn in (-1.0, 1.0):
                pts = [(sgn * (half + lapel * (1.0 - smoothstep(fig.y_nb, fig.y_chest + 0.12 * T, y)) + 7.0), y)
                       for y in (fig.y_nb + 0.5 + i * (fig.y_chest + 0.1 * T - fig.y_nb) / 6.0 for i in range(7))]
                for run in surface_line(ctx, shell, pts, out=0.15):
                    pt.line(run, INK, FINE)
        if not o.outer_open and o.outer != "vest":
            _buttons(ctx, pt, shell, [3.0], fig.y_chest, torso_bottom - 0.06 * T, 4 if o.outer != "cardigan" else 5, light(col, 0.35))
        elif o.outer in ("vest", "cardigan"):
            _buttons(ctx, pt, shell, [-(half + 2.5)], fig.y_chest + 0.05 * T, torso_bottom - 0.04 * T, 4, light(col, 0.4))
        open_lower = (o.outer_open or o.outer == "vest") and o.outer != "robe"
        if open_lower:
            hw = 6.0 if o.outer == "vest" else 11.0
            lower_margin = lambda a, y, _w=hw: (abs(wrap180(a)) - _w) * 0.2  # noqa: E731
    out.append(Part("torso__outer", "torso", 33.0, pt.els, "Outer", feature=feature))
    if o.outer in ("jacket", "coat", "robe", "cardigan", "field_jacket"):
        out += sleeve_parts(ctx, "outer", feature, 0.97 if o.outer == "robe" else 1.0, 1.0 + (0.9 if o.outer == "robe" else 0.0), col, zmap,
                            cuff=o.outer in ("coat", "jacket", "field_jacket"), wide=2.0 if o.outer == "robe" else 0.0)
    if hem > torso_bottom + 0.02 * T:
        flare = {"robe": 1.3, "coat": 1.2, "apron": 1.0, "cardigan": 1.1, "jacket": 1.05, "vest": 1.0}.get(o.outer, 1.1)
        lo = skirt_loft(fig, fig.y_waist, hem, t + 0.6, flare)

        def extra(p: Paint, side: str) -> None:
            if o.outer == "robe":
                p.region(loft_region(ctx.view, lo.shell(0.3), fig.y_waist - 0.04 * T, fig.y_waist + 0.04 * T, half_of(side)),
                         o.accent_color, outline=FINE)

        # An apron is a front panel only: drawn whole it would show on the back.
        out += lobe_parts(ctx, "outer", feature, lo, fig.y_waist, hem, col, lower_margin, z=(32.0, 32.5), extra=extra,
                          solid=o.outer != "apron")
        out += drape_parts(ctx, "outer", feature, zmap)
    return out


def _box(alpha: float, half: float, y0: float, y1: float):
    """Covered inside a box on a loft: ``half`` degrees each side of
    ``alpha``, from ``y0`` down to ``y1``."""
    return lambda a, y: min((half - abs(wrap180(a - alpha))) * 0.2, y - y0, y1 - y)


def _field_jacket(ctx: Ctx, pt: Paint, shell: Loft, bottom: float) -> None:
    """A military field jacket: buttoned up to a small collar (or open), a
    cloth belt at the waist, four flap pockets and a strap on each
    shoulder. Buttons are the accent colour (brass on a uniform)."""
    fig, o = ctx.fig, ctx.fig.spec.outfit
    T = fig.T
    col = o.outer_color
    button = o.accent_color
    half, lapel = (9.0, 18.0) if o.outer_open else (0.0, 9.0)
    front = opening(fig, half, lapel)
    shaded_region(ctx, pt, shell, fig.torso.top, bottom, col, front, lit=True)
    _collar(ctx, pt, shell, col)
    if o.outer_open:
        for sgn in (-1.0, 1.0):
            pts = [(sgn * (half + lapel * (1.0 - smoothstep(fig.y_nb, fig.y_chest + 0.12 * T, y)) + 0.5), y)
                   for y in (lerp(fig.y_nb + 0.5, bottom - 0.5, i / 8.0) for i in range(9))]
            for run in surface_line(ctx, shell, pts, out=0.15):
                pt.line(run, INK, FINE)
    else:
        for run in surface_line(ctx, shell, [(2.0, lerp(fig.y_nb + 2.0, bottom - 0.3, i / 6.0)) for i in range(7)], out=0.12, thresh=0.2):
            pt.line(run, shade(col, 0.45), FINE)
        _buttons(ctx, pt, shell, [5.0], fig.y_chest - 0.02 * T, bottom - 0.08 * T, 5, button)
    # Four flap pockets: two on the chest, two below the belt.
    pocket = shell.shell(0.12)
    for sgn in (-1.0, 1.0):
        for c, w, y0, y1 in ((sgn * 33.0, 13.0, fig.y_chest - 0.03 * T, fig.y_chest + 0.13 * T),
                             (sgn * 36.0, 15.0, fig.y_waist + 0.07 * T, bottom - 0.04 * T)):
            if not visible(ctx, c, 0.05):
                continue
            box = all_of(_box(c, w, y0, y1), front)
            pt.region(loft_region(ctx.view, pocket, y0, y1, box), light(col, 0.04), outline=FINE * 0.8)
            fy1 = y0 + 0.05 * T
            pt.region(loft_region(ctx.view, pocket.shell(0.12), y0 - 0.005 * T, fy1, all_of(_box(c, w + 1.5, y0 - 0.005 * T, fy1), front)),
                      shade(col, 0.1), outline=FINE * 0.8)
            if visible(ctx, c, 0.3) and front(c, fy1) > 0.0:
                pt.dot(ctx.p(pocket.point(c, fy1 - 0.012 * T, 0.35)), 0.42, INK)
                pt.dot(ctx.p(pocket.point(c, fy1 - 0.012 * T, 0.4)), 0.3, button)
    # The cloth belt and its buckle.
    belt = shell.shell(0.3)
    pt.region(loft_region(ctx.view, belt, fig.y_waist - 0.03 * T, fig.y_waist + 0.03 * T), shade(col, 0.18), outline=FINE * 0.8)
    if visible(ctx, 0.0, 0.3):
        cb = belt.point(0.0, fig.y_waist, 0.2)
        q = [ctx.p(add3(cb, d)) for d in ((-1.3, -1.1, 0), (1.3, -1.1, 0), (1.3, 1.1, 0), (-1.3, 1.1, 0))]
        pt.region([q], button, outline=FINE * 0.7)
    _shoulder_straps(ctx, pt, shell, col, button)


def _shoulder_straps(ctx: Ctx, pt: Paint, shell: Loft, col: str, button: str) -> None:
    """A strap (an epaulette) along the top of each shoulder, from the
    collar to the shoulder seam, with a button at the collar end: a thin
    slab of 3D points on the shoulder's top."""
    fig = ctx.fig
    k = fig.k
    y_end = fig.y_sh + 2.4 * k
    for _depth, side, sgn in SIDES:
        ys = [lerp(fig.y_nb + 0.4, y_end, i / 4.0) for i in range(5)]
        rail = [shell.point(sgn * 90.0, y, 0.0) for y in ys]
        for a, b in zip(rail, rail[1:]):
            pts3 = [add3(q, (0.0, dy, dz)) for q in (a, b) for dy in (-0.15, -0.75) for dz in (-1.6 * k, 1.6 * k)]
            pt.region([hull(ctx.p(q) for q in pts3)], light(col, 0.05), outline=FINE * 0.7)
        btn = add3(rail[1], (0.0, -0.8, 0.0))
        pt.dot(ctx.p(btn), 0.42, INK)
        pt.dot(ctx.p(btn), 0.3, button)


# ---- legwear -------------------------------------------------------------------------------------


def legwear_parts(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    fig, o, plan = ctx.fig, ctx.fig.spec.outfit, ctx.plan
    feature = f"legwear:{o.bottom}"
    T = fig.T
    col = o.bottom_color
    out: List[Part] = []
    pt = ctx.new()
    shell = fig.torso.shell(0.45)
    y0 = fig.y_waist - 0.05 * T
    skirted = o.bottom in ("skirt", "long_skirt")
    if skirted:
        shaded_region(ctx, pt, shell, y0, fig.y_hipw, col)
    else:
        def crotch(a: float, y: float) -> float:
            al = abs(wrap180(a))
            # Leg holes: the crotch is low at the front and back, high at the sides.
            lift = 0.07 * T * abs(math.sin(math.radians(al))) ** 0.8
            return (fig.y_crotch - lift) - y

        shaded_region(ctx, pt, shell, y0, fig.y_crotch, col, crotch)
        if o.bottom == "trousers" and visible(ctx, 0.0, 0.3):
            for run in surface_line(ctx, shell, [(0.0, fig.y_waist + 0.05 * T), (0.0, fig.y_crotch - 0.02 * T)], out=0.1, thresh=0.3):
                pt.line(run, shade(col, 0.35), FINE)
    if plan["tucked"]:
        pt.region(loft_region(ctx.view, shell.shell(0.1), fig.y_waist - 0.03 * T, fig.y_waist + 0.035 * T), shade(col, 0.1), outline=FINE * 0.8)
    out.append(Part("pelvis__legwear", "pelvis", zmap["pelvis"] + LAYER["legwear"], pt.els, "Legwear", feature=feature))
    j = fig.joints
    rt, rk, rc, ra = fig.leg_r
    for depth, side, _sgn in SIDES:
        Hp, K, A = j[f"{side}_hip"], j[f"{side}_knee"], j[f"{side}_ankle"]
        if o.bottom == "trousers":
            pu = ctx.new()
            tube3(ctx, pu, Hp, K, rt + 0.5, rk * 1.05 + 0.6, col, joint_b=True)
            pl = ctx.new()
            tube3(ctx, pl, K, A, rc + 0.6, ra + 0.9, col, round_b=False)
        elif o.bottom == "shorts":
            pu = ctx.new()
            aa, bb = segment(Hp, K, 0.0, 0.72)
            tube3(ctx, pu, aa, bb, rt + 0.7, lerp(rt, rk, 0.72) + 1.1, col, round_b=False)
            pl = ctx.new()
        else:
            pu, pl = ctx.new(), ctx.new()
        for seg, p in (("leg_u", pu), ("leg_l", pl)):
            part = _part(f"{depth}_{seg}__legwear", f"{depth}_{seg}", zmap[f"{depth}_{seg}"] + LAYER["legwear"], p, f"Legwear - {depth} {seg}",
                         feature)
            if part:
                out.append(part)
    if skirted:
        flare = 1.12 if o.bottom == "skirt" else 1.28
        sk = skirt_loft(fig, fig.y_waist, plan["bottom_hem"], 0.5, flare)
        out += lobe_parts(ctx, "legwear", feature, sk, fig.y_waist, plan["bottom_hem"], col, z=(12.9, 16.0))
        out += drape_parts(ctx, "legwear", feature, zmap)
    return out


# ---- footwear --------------------------------------------------------------------------------------


def foot_points(fig: Figure, side: str, k_size: float = 1.0) -> Tuple[List, List, List]:
    A = fig.joints[f"{side}_ankle"]
    k = fig.k * (0.95 if fig.female else 1.0) * k_size
    # The family's foot: length, width and height multipliers.
    FL, FW, FH = family_of(fig.spec).body.foot
    l0, z0 = A[0], A[2]
    ah = -A[1]
    sole, top = [], []
    for z, w, h in ((-5.2, 3.3, 0.72), (-2.0, 4.0, 0.95), (5.5, 4.6, 0.62), (11.5, 4.9, 0.45), (16.0, 4.3, 0.33), (18.6, 2.9, 0.26)):
        for s in (-1.0, 1.0):
            sole.append((l0 + s * w * k * FW, 0.0, z0 + z * k * FL))
            top.append((l0 + s * w * k * FW * 0.92, -ah * h * FH * 1.05, z0 + z * k * FL))
    collar = [(l0 + 4.0 * k * FW * math.cos(t), -ah * FH * 1.05, z0 + 3.6 * k * FW * math.sin(t)) for t in (2 * math.pi * i / 10 for i in range(10))]
    return sole, top, collar


def footwear_parts(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    fig, o = ctx.fig, ctx.fig.spec.outfit
    feature = f"footwear:{o.shoes}"
    out: List[Part] = []
    j = fig.joints
    rt, rk, rc, ra = fig.leg_r
    for depth, side, _sgn in SIDES:
        pt = ctx.new()
        sole, top, collar = foot_points(fig, side)
        shoe = hull(ctx.p(q) for q in sole + top + collar)
        pt.region([shoe], o.shoe_color, smooth=True)
        k = fig.k
        sole_band = hull([ctx.p(q) for q in sole] + [ctx.p((q[0], -1.3 * k, q[2])) for q in sole])
        pt.flat([sole_band], shade(o.shoe_color, 0.4), smooth=True)
        A = j[f"{side}_ankle"]
        from .geometry import capsule_band

        pt.flat([capsule_band(ctx.p(A), ctx.p((A[0], -1.5, A[2] + 15.0 * k)), 3.0, 2.0, 1.2)], shade(o.shoe_color, 0.18))
        p = _part(f"{depth}_foot__footwear", f"{depth}_leg_foot", zmap[f"{depth}_leg_foot"] + LAYER["footwear"], pt, f"Shoe - {depth}", feature)
        if p:
            out.append(p)
        if o.shoes == "boots":
            K = j[f"{side}_knee"]
            pb = ctx.new()
            aa, bb = segment(K, A, 0.42, 1.0)
            tube3(ctx, pb, aa, bb, lerp(rc, ra, 0.42) + 1.2, ra + 1.25, o.shoe_color, round_a=False)
            ca, cb = segment(K, A, 0.42, 0.49)
            tube3(ctx, pb, ca, cb, lerp(rc, ra, 0.42) + 1.4, lerp(rc, ra, 0.49) + 1.4, shade(o.shoe_color, 0.15), band=False, round_a=False,
                  round_b=False)
            p = _part(f"{depth}_leg_l__footwear", f"{depth}_leg_l", zmap[f"{depth}_leg_l"] + LAYER["footwear"], pb, f"Boot - {depth}", feature)
            if p:
                out.append(p)
    return out


# ---- accessories on the body ----------------------------------------------------------------------


def _belt(ctx: Ctx, pt: Paint, shell: Loft, y: float) -> None:
    fig = ctx.fig
    w = 0.035 * fig.T
    col = fig.spec.outfit.shoe_color
    polys = loft_region(ctx.view, shell, y - w, y + w)
    pt.region(polys, col, outline=FINE * 0.9)
    if visible(ctx, 0.0, 0.3):
        c = shell.point(0.0, y, 0.3)
        q = [ctx.p(add3(c, d)) for d in ((-1.1, -1.0, 0), (1.1, -1.0, 0), (1.1, 1.0, 0), (-1.1, 1.0, 0))]
        pt.region([q], "#c9a24a", outline=FINE * 0.7)


def accessory_parts(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    fig, o, plan = ctx.fig, ctx.fig.spec.outfit, ctx.plan
    out: List[Part] = []
    T = fig.T
    if "belt" in o.accessories:
        pt = ctx.new()
        if plan["tucked"] or o.top == "tunic":
            if plan["tucked"]:
                _belt(ctx, pt, fig.torso.shell(0.6), fig.y_waist + 0.01 * T)
                out.append(Part("pelvis__belt", "pelvis", zmap["pelvis"] + LAYER["acc"], pt.els, "Belt", feature="acc:belt"))
            else:
                _belt(ctx, pt, fig.torso.shell(1.3), fig.y_waist)
                out.append(Part("torso__belt", "torso", 33.2, pt.els, "Belt", feature="acc:belt"))
        else:
            _belt(ctx, pt, fig.torso.shell(0.55), fig.y_waist)
            out.append(Part("torso__belt", "torso", zmap["torso"] + LAYER["acc"], pt.els, "Belt", feature="acc:belt"))
    if "suspenders" in o.accessories:
        pt = ctx.new()
        pt.flat(loft_region(ctx.view, fig.torso.shell(0.4), fig.torso.top, fig.y_waist + 0.06 * T, bands([22.0, -22.0, 158.0, -158.0], 3.4)),
                o.accent_color)
        out.append(Part("torso__suspenders", "torso", zmap["torso"] + LAYER["top"] + 0.05, pt.els, "Suspenders", feature="acc:suspenders"))
    if "necklace" in o.accessories:
        pt = ctx.new()
        shell = fig.torso.shell(0.35)
        pts = [(a, fig.y_nb + 0.6 + 0.07 * T * math.cos(math.radians(a * 1.3))) for a in range(-60, 61, 6)]
        for run in surface_line(ctx, shell, pts, out=0.25):
            pt.line(run, o.accent_color, 0.35)
        if visible(ctx, 0.0, 0.3):
            pt.dot(ctx.p(shell.point(0.0, fig.y_nb + 0.6 + 0.08 * T, 0.4)), 0.7, INK)
            pt.dot(ctx.p(shell.point(0.0, fig.y_nb + 0.6 + 0.08 * T, 0.45)), 0.5, "#d8b450")
        if pt.els:
            out.append(Part("torso__necklace", "torso", zmap["torso"] + LAYER["top"] + 0.08, pt.els, "Necklace", feature="acc:necklace"))
    if "scarf" in o.accessories:
        pt = ctx.new()
        col = o.accent_color
        nk = fig.neck.keys[-1]
        ring = Loft([RingKey(fig.y_nb - 2.6, nk.rx + 1.6, nk.rzf + 1.6, nk.rzb + 1.6, 0.0, -1.2),
                     RingKey(fig.y_nb + 1.4, nk.rx + 3.0, nk.rzf + 2.6, nk.rzb + 2.2, 0.0, -0.6)])
        ends = fig.torso.shell(1.4)
        shaded_region(ctx, pt, ends, fig.y_nb, fig.y_chest + 0.12 * T, col, lambda a, y: (7.0 - abs(wrap180(a) + 19.0)) * 0.3)
        shaded_region(ctx, pt, ends.shell(0.3), fig.y_nb, fig.y_chest + 0.02 * T, shade(col, 0.1), lambda a, y: (6.0 - abs(wrap180(a) + 7.0)) * 0.3)
        shaded_region(ctx, pt, ring, ring.top, ring.bottom, col)
        out.append(Part("torso__scarf", "torso", 34.0, pt.els, "Scarf", feature="acc:scarf"))
    if "webbing" in o.accessories:
        out += _webbing(ctx, zmap)
    if "dog_tags" in o.accessories:
        pt = ctx.new()
        shell = fig.torso.shell(0.35)
        pts = [(a, fig.y_nb + 0.4 + 0.11 * T * math.cos(math.radians(a * 1.4)) ** 2) for a in range(-60, 61, 6)]
        for run in surface_line(ctx, shell, pts, out=0.25):
            pt.line(run, "#a9aaa5", 0.28)
        if visible(ctx, 0.0, 0.3):
            for dx, dy in ((-0.5, 0.0), (0.6, 0.4)):
                c = shell.point(0.0, fig.y_nb + 0.4 + 0.12 * T + dy, 0.45)
                q = [ctx.p(add3(c, (dx + ex, ey, 0.0))) for ex, ey in ((-0.8, -1.2), (0.8, -1.2), (0.8, 1.2), (-0.8, 1.2))]
                pt.region([q], "#c9ccc8", outline=FINE * 0.6)
        if pt.els:
            out.append(Part("torso__dog_tags", "torso", zmap["torso"] + LAYER["top"] + 0.08, pt.els, "Dog tags", feature="acc:dog_tags"))
    return out


def _webbing(ctx: Ctx, zmap: Dict[str, float]) -> List[Part]:
    """A duty belt of canvas webbing with a brass buckle, four pouches on
    it, and a strap over each shoulder from the belt in front to the belt
    behind. It is worn over everything on the torso."""
    from .spec import UNIFORM

    fig, o, plan = ctx.fig, ctx.fig.spec.outfit, ctx.plan
    T, k = fig.T, fig.k
    web = UNIFORM["webbing"]
    t = (plan["outer_t"] if o.outer != "none" else 0.45) + 0.7
    shell = fig.torso.shell(t)
    y = fig.y_waist + 0.015 * T
    w = 0.04 * T
    pt = ctx.new()
    # The shoulder straps first: the belt and the pouches go over their ends.
    for sgn in (-1.0, 1.0):
        path = [(sgn * 26.0, y), (sgn * 27.0, fig.y_under), (sgn * 30.0, fig.y_chest), (sgn * 40.0, fig.y_sh), (sgn * 62.0, fig.y_nb + 1.2),
                (sgn * 90.0, fig.y_nb + 0.6), (sgn * 120.0, fig.y_nb + 1.2), (sgn * 148.0, fig.y_sh), (sgn * 154.0, fig.y_chest),
                (sgn * 156.0, y)]
        dense = [(lerp(a0, a1, i / 4.0), lerp(y0, y1, i / 4.0)) for (a0, y0), (a1, y1) in zip(path, path[1:]) for i in range(4)] + [path[-1]]
        for run in surface_line(ctx, shell, dense, out=0.2, thresh=0.0):
            pt.line(run, INK, 1.8, smooth=True)
            pt.line(run, web, 1.2, smooth=True)
        if visible(ctx, sgn * 27.0, 0.2):
            c = shell.point(sgn * 27.0, fig.y_under + 0.02 * T, 0.5)
            q = [ctx.p(add3(c, d)) for d in ((-0.9, -0.7, 0), (0.9, -0.7, 0), (0.9, 0.7, 0), (-0.9, 0.7, 0))]
            pt.region([q], UNIFORM["brass"], outline=FINE * 0.6)
    pt.region(loft_region(ctx.view, shell, y - w, y + w), web, outline=FINE)
    if visible(ctx, 0.0, 0.3):
        c = shell.point(0.0, y, 0.3)
        q = [ctx.p(add3(c, d)) for d in ((-1.6, -1.3, 0), (1.6, -1.3, 0), (1.6, 1.3, 0), (-1.6, 1.3, 0))]
        pt.region([q], UNIFORM["brass"], outline=FINE * 0.8)
        pt.flat([[ctx.p(add3(c, d)) for d in ((-0.8, -0.6, 0.1), (0.8, -0.6, 0.1), (0.8, 0.6, 0.1), (-0.8, 0.6, 0.1))]], shade(UNIFORM["brass"], 0.35))
    # Pouches: boxes of 3D points hung on the belt, each with a flap.
    for a in (-48.0, 48.0, -100.0, 100.0):
        if not visible(ctx, a, -0.3):
            continue
        ra = math.radians(a)
        n, tg = (math.sin(ra), 0.0, math.cos(ra)), (math.cos(ra), 0.0, -math.sin(ra))
        base = shell.point(a, y, 0.0)
        hw, d = 3.0 * k, 3.2 * k
        top, bot = -0.03 * T, 0.075 * T

        def corner(u: float, v: float, e: float, _b=base, _n=n, _t=tg) -> Vec3:
            return add3(_b, (_t[0] * u + _n[0] * e, v, _t[2] * u + _n[2] * e))

        box = [corner(u, v, e) for u in (-hw, hw) for v in (top, bot) for e in (0.0, d)]
        pt.region([hull(ctx.p(q) for q in box)], shade(web, 0.06), outline=FINE)
        flap = [corner(u, v, e) for u in (-hw * 1.04, hw * 1.04) for v in (top - 0.2, top + 0.38 * (bot - top)) for e in (0.0, d + 0.25)]
        pt.region([hull(ctx.p(q) for q in flap)], shade(web, 0.2), outline=FINE * 0.8)
        if visible(ctx, a, 0.2):
            pt.dot(ctx.p(corner(0.0, top + 0.3 * (bot - top), d + 0.3)), 0.32, UNIFORM["brass"])
    return [Part("torso__webbing", "torso", 33.6, pt.els, "Webbing", feature="acc:webbing")] if pt.els else []


__all__ = ["accessory_parts", "drape_color", "foot_points", "footwear_parts", "legwear_parts", "outer_parts", "skirt_loft", "top_parts"]
