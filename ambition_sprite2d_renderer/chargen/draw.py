"""One view of a figure, as rig parts of SVG paint.

``draw_view`` returns the parts of one view in the humanoid rig's vocabulary
(``humanoid_svg_rig``): each part names its bone, its paint order (``z``) and,
for the blink and talk overlays, its opacity channel. Every part is drawn by
projecting the figure's 3D primitives through the view, so all five views of
a character agree.

The paint order depends on the view: in the front and back views both arms are
over the body and long hair hangs behind it (front) or over it (back); in the
turned views the far arm and leg are behind the body and the near ones in
front. The near side is always the character's RIGHT (``l < 0``).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .body import Figure
from .geometry import (
    Loft,
    Point,
    RingKey,
    Vec3,
    View,
    add3,
    capsule,
    capsule_band,
    clip_convex,
    column_bands,
    ellipse3,
    hull,
    interp_knots,
    lerp,
    loft_region,
    norm3,
    scale3,
    smoothstep,
    sub3,
    tube,
    wrap180,
)
from .svgout import FINE, INK, Canvas, El, Paint, light, luminance, mix, shade

SIDES = (("near", "right", -1.0), ("far", "left", 1.0))


@dataclass
class Part:
    name: str
    bone: str
    z: float
    els: List[El]
    label: str
    opacity: Optional[str] = None
    opacity_default: Optional[int] = None


# ---- shared helpers -------------------------------------------------------------------------


@dataclass
class Ctx:
    fig: Figure
    view: View
    cv: Canvas
    skin: str = ""
    skin_sh: str = ""
    skin_dk: str = ""
    hair: str = ""
    extra: Dict[str, object] = field(default_factory=dict)

    def p(self, v: Vec3) -> Point:
        return self.view.project(v)

    def new(self) -> Paint:
        return Paint(self.cv)


def _shaded_region(ctx: Ctx, pt: Paint, loft: Loft, y0: float, y1: float, color: str, margin=None, *, ink: bool = True,
                   shade_frac: float = 0.2, shade_cap: float = 3.0, lit: bool = False) -> bool:
    polys = loft_region(ctx.view, loft, y0, y1, margin)
    if not polys:
        return False
    pt.region(polys, color, ink=ink)
    if shade_frac > 0.0:
        pt.flat(column_bands(ctx.view, loft, y0, y1, margin, side="left", frac=shade_frac, cap=shade_cap), shade(color))
    if lit:
        pt.flat(column_bands(ctx.view, loft, y0, y1, margin, side="right", frac=0.08, cap=1.2, y_from=0.05, y_to=0.7), light(color, 0.18))
    return True


def _capsule(ctx: Ctx, pt: Paint, a: Vec3, b: Vec3, r0: float, r1: float, color: str, *, ink: bool = True, band: bool = True,
             round_a: bool = True, round_b: bool = True) -> None:
    A, B = ctx.p(a), ctx.p(b)
    pt.region([tube(A, B, r0, r1, round_a=round_a, round_b=round_b)], color, ink=ink)
    if band:
        pt.flat([capsule_band(A, B, r0, r1, 0.38 * min(r0, r1))], shade(color))


def _segment(a: Vec3, b: Vec3, t0: float, t1: float) -> Tuple[Vec3, Vec3]:
    return (add3(a, scale3(sub3(b, a), t0)), add3(a, scale3(sub3(b, a), t1)))


def _visible(ctx: Ctx, alpha: float, thresh: float = 0.1) -> bool:
    return ctx.view.facing(alpha) > thresh


def _surface_line(ctx: Ctx, loft: Loft, pts: Sequence[Tuple[float, float]], out: float = 0.05, thresh: float = 0.08) -> List[List[Point]]:
    """The visible stretches of a line on a loft, given as (alpha, y) points."""
    runs: List[List[Point]] = []
    cur: List[Point] = []
    for a, y in pts:
        if ctx.view.facing(a) > thresh:
            cur.append(ctx.p(loft.point(a, y, out)))
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return [r for r in runs if len(r) >= 2]


def _dark_of(c: str) -> str:
    """Brows and lashes: a dark version of the hair, never pale."""
    d = shade(c, 0.45)
    return mix(d, "#2a211d", 0.5) if luminance(d) > 0.35 else d


# ---- garments -----------------------------------------------------------------------------


def _outfit_plan(fig: Figure) -> Dict[str, object]:
    o = fig.spec.outfit
    T = fig.T
    plan: Dict[str, object] = {}
    top_hem = {
        "tshirt": fig.y_hipw - 0.02 * T,
        "shirt": fig.y_hipw + 0.02 * T,
        "blouse": fig.y_hipw - 0.04 * T,
        "sweater": fig.y_hipw,
        "tunic": fig.y_crotch + 0.32 * T,
    }[o.top]
    tucked = o.tucked and o.top != "tunic" and o.bottom in ("trousers", "shorts", "skirt", "long_skirt")
    plan["tucked"] = tucked
    plan["top_hem"] = fig.y_waist + 0.04 * T if tucked else top_hem
    outer = o.outer
    knee_y = fig.joints["right_knee"][1]
    hem = {"hip": fig.y_hipw + 0.12 * T, "knee": knee_y + 0.06 * T, "ankle": -0.075 * fig.H}[o.outer_length]
    if outer == "vest":
        hem = fig.y_waist + 0.16 * T
    if outer == "cardigan" and o.outer_length == "ankle":
        hem = knee_y + 0.06 * T
    if outer == "apron":
        hem = knee_y + (0.06 * T if o.outer_length == "knee" else 0.5 * (-0.075 * fig.H - knee_y))
    if outer == "robe":
        hem = -0.06 * fig.H
    plan["outer_hem"] = hem
    plan["outer_t"] = {"vest": 0.6, "jacket": 0.95, "coat": 1.15, "robe": 1.1, "apron": 0.75, "cardigan": 0.8}.get(outer, 0.0)
    bottom_hem = {"skirt": knee_y + 0.04 * T, "long_skirt": -0.085 * fig.H}.get(o.bottom)
    plan["bottom_hem"] = bottom_hem
    # Does anything below the waist hang over the legs?
    plan["skirt_layers"] = bool(bottom_hem) or o.top == "tunic" and not tucked or (outer != "none" and hem > fig.y_crotch + 0.02 * T)
    return plan


def _neckline(fig: Figure, kind: str) -> Callable[[float, float], float]:
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


def _opening(fig: Figure, half: float, lapel: float) -> Callable[[float, float], float]:
    """Covered away from a front opening of ``half`` degrees, wider by
    ``lapel`` at the neck (a V down to the chest)."""
    T = fig.T

    def m(alpha: float, y: float) -> float:
        w = half + lapel * (1.0 - smoothstep(fig.y_nb, fig.y_chest + 0.12 * T, y))
        return (abs(wrap180(alpha)) - w) * 0.2

    return m


def _all(*ms: Callable[[float, float], float]) -> Callable[[float, float], float]:
    return lambda a, y: min(m(a, y) for m in ms)


def _between(y0: float, y1: float) -> Callable[[float, float], float]:
    return lambda a, y: min(y - y0, y1 - y)


def _bands(centers: Sequence[float], half: float) -> Callable[[float, float], float]:
    return lambda a, y: max(half - abs(wrap180(a - c)) for c in centers) * 0.2


def draw_torso(ctx: Ctx) -> Paint:
    fig, o = ctx.fig, ctx.fig.spec.outfit
    plan = ctx.extra["plan"]
    T = fig.T
    pt = ctx.new()
    top = fig.torso.top
    bottom = fig.y_waist + 0.06 * T if plan["tucked"] or plan["skirt_layers"] else min(plan["top_hem"], fig.y_crotch)
    if o.outer in ("jacket", "coat", "cardigan", "robe", "vest") and not plan["skirt_layers"]:
        bottom = max(bottom, min(plan["outer_hem"], fig.y_crotch))
    ctx.extra["torso_bottom"] = bottom
    # The body under the clothes (seen at a V-neck or a scoop).
    _shaded_region(ctx, pt, fig.torso, top, bottom, ctx.skin, shade_cap=2.5)
    shirt = fig.torso.shell(0.3)
    top_color = o.top_color
    hem = min(plan["top_hem"], bottom)
    neck = _neckline(fig, o.neckline)
    _shaded_region(ctx, pt, shirt, top, hem, top_color, _all(neck, _between(top - 1, hem)), lit=True)
    if o.top == "sweater":
        rib = shade(top_color, 0.12)
        pt.flat(loft_region(ctx.view, shirt, top, fig.y_nb + 1.6, _all(neck, _between(fig.y_nb + 0.2, fig.y_nb + 1.6))), rib)
        if hem < bottom + 0.01:
            pt.flat(loft_region(ctx.view, shirt, hem - 2.2, hem), rib)
    if o.neckline == "collar" and o.outer in ("none", "vest", "apron"):
        _collar(ctx, pt, shirt, top_color)
    if o.top in ("shirt", "blouse") and o.neckline == "collar" and o.outer in ("none", "apron"):
        _buttons(ctx, pt, shirt, [0.0], fig.y_nb + 0.12 * T, hem - 0.06 * T, 4, light(top_color, 0.35))
    # Belt over an untucked tunic or shirt.
    if "belt" in o.accessories and not plan["tucked"]:
        _belt(ctx, pt, fig.torso.shell(0.55), fig.y_waist)
    if "suspenders" in o.accessories and plan["tucked"]:
        pt.flat(loft_region(ctx.view, fig.torso.shell(0.4), top, bottom, _bands([22.0, -22.0, 158.0, -158.0], 3.4)), o.accent_color)
    if "necklace" in o.accessories:
        _necklace(ctx, pt, shirt)
    _outer_torso(ctx, pt, bottom)
    if "scarf" in o.accessories:
        _scarf(ctx, pt)
    return pt


def _collar(ctx: Ctx, pt: Paint, shell: Loft, color: str) -> None:
    fig = ctx.fig
    y = fig.y_nb + 0.6
    for sgn in (-1.0, 1.0):
        a0, a1 = sgn * 6.0, sgn * 34.0
        if not (_visible(ctx, a0, 0.0) or _visible(ctx, a1, 0.0)):
            continue
        tri = [shell.point(a0, y - 0.3, 0.6), shell.point(a1, y - 0.6, 0.8), shell.point(sgn * 14.0, y + 0.075 * fig.T, 0.9)]
        pt.region([[ctx.p(q) for q in tri]], light(color, 0.12), outline=FINE * 0.8)


def _buttons(ctx: Ctx, pt: Paint, shell: Loft, alphas: Sequence[float], y0: float, y1: float, n: int, color: str) -> None:
    for a in alphas:
        if not _visible(ctx, a, 0.25):
            continue
        for i in range(n):
            y = lerp(y0, y1, i / max(1, n - 1))
            pt.dot(ctx.p(shell.point(a, y, 0.3)), 0.45, INK)
            pt.dot(ctx.p(shell.point(a, y, 0.35)), 0.3, color)


def _belt(ctx: Ctx, pt: Paint, shell: Loft, y: float) -> None:
    fig = ctx.fig
    w = 0.035 * fig.T
    col = shade(fig.spec.outfit.shoe_color, 0.0)
    polys = loft_region(ctx.view, shell, y - w, y + w)
    pt.region(polys, col, outline=FINE * 0.9)
    if _visible(ctx, 0.0, 0.3):
        c = shell.point(0.0, y, 0.3)
        q = [ctx.p(add3(c, d)) for d in ((-1.1, -1.0, 0), (1.1, -1.0, 0), (1.1, 1.0, 0), (-1.1, 1.0, 0))]
        pt.region([q], "#c9a24a", outline=FINE * 0.7)


def _necklace(ctx: Ctx, pt: Paint, shell: Loft) -> None:
    fig = ctx.fig
    pts = [(a, fig.y_nb + 0.6 + 0.07 * fig.T * math.cos(math.radians(a * 1.3))) for a in range(-60, 61, 6)]
    for run in _surface_line(ctx, shell, pts, out=0.25):
        pt.line(run, fig.spec.outfit.accent_color, 0.35)
    if _visible(ctx, 0.0, 0.3):
        pt.dot(ctx.p(shell.point(0.0, fig.y_nb + 0.6 + 0.08 * fig.T, 0.4)), 0.7, INK)
        pt.dot(ctx.p(shell.point(0.0, fig.y_nb + 0.6 + 0.08 * fig.T, 0.45)), 0.5, "#d8b450")


def _scarf(ctx: Ctx, pt: Paint) -> None:
    fig = ctx.fig
    col = fig.spec.outfit.accent_color
    ring = Loft([RingKey(fig.y_nb - 2.6, fig.neck.keys[-1].rx + 1.6, fig.neck.keys[-1].rzf + 1.6, fig.neck.keys[-1].rzb + 1.6, 0.0, -1.2),
                 RingKey(fig.y_nb + 1.4, fig.neck.keys[-1].rx + 3.0, fig.neck.keys[-1].rzf + 2.6, fig.neck.keys[-1].rzb + 2.2, 0.0, -0.6)])
    # The two ends hang down the chest, on the body's surface.
    ends = fig.torso.shell(1.4)
    _shaded_region(ctx, pt, ends, fig.y_nb, fig.y_chest + 0.12 * fig.T, col, lambda a, y: (7.0 - abs(wrap180(a) + 19.0)) * 0.3)
    _shaded_region(ctx, pt, ends.shell(0.3), fig.y_nb, fig.y_chest + 0.02 * fig.T, shade(col, 0.1), lambda a, y: (6.0 - abs(wrap180(a) + 7.0)) * 0.3)
    _shaded_region(ctx, pt, ring, ring.top, ring.bottom, col)


def _outer_torso(ctx: Ctx, pt: Paint, bottom: float) -> None:
    fig, o = ctx.fig, ctx.fig.spec.outfit
    plan = ctx.extra["plan"]
    if o.outer == "none":
        return
    t = plan["outer_t"]
    shell = fig.torso.shell(t)
    col = o.outer_color
    top = fig.torso.top
    hem = min(plan["outer_hem"], bottom)
    if o.outer == "apron":
        bib = fig.y_chest - 0.04 * fig.T

        def m(a: float, y: float) -> float:
            w = lerp(26.0, 50.0, smoothstep(fig.y_under - 0.05 * fig.T, fig.y_under + 0.05 * fig.T, y))
            return min((w - abs(wrap180(a))) * 0.2, y - bib)

        _shaded_region(ctx, pt, shell, bib, hem, col, m)
        straps = [(-24.0, bib), (-30.0, fig.y_nb + 2.0), (-90.0, fig.y_nb - 0.5), (-150.0, fig.y_nb + 1.0)]
        for sgn in (1.0, -1.0):
            for run in _surface_line(ctx, shell, [(sgn * a, y) for a, y in straps], out=0.1, thresh=0.0):
                pt.line(run, INK, 1.25, smooth=True)
                pt.line(run, col, 0.7, smooth=True)
        pt.flat(loft_region(ctx.view, shell, fig.y_waist - 0.025 * fig.T, fig.y_waist + 0.025 * fig.T), shade(col, 0.15))
        if _visible(ctx, 180.0, 0.4):
            c = shell.point(180.0, fig.y_waist, 0.5)
            for dx in (-1.0, 1.0):
                bow = [ctx.p(add3(c, d)) for d in ((0, -0.6, 0), (dx * 3.2 * (1 if ctx.view.c < 0 else -1), -1.8, 0), (dx * 3.2 * (1 if ctx.view.c < 0 else -1), 1.6, 0), (0, 0.6, 0))]
                pt.region([bow], col, outline=FINE)
        return
    if o.outer == "robe":
        _shaded_region(ctx, pt, shell, top, hem, col, None, lit=True)
        line = [(lerp(-34.0, 12.0, i / 10.0), lerp(fig.y_nb + 0.5, fig.y_under, i / 10.0)) for i in range(11)]
        for run in _surface_line(ctx, shell, line, out=0.1):
            pt.line(run, INK, FINE * 1.3)
        _belt_band(ctx, pt, shell.shell(0.3), fig.y_waist, o.accent_color)
        return
    half, lapel = {"vest": (6.0, 30.0), "jacket": (9.0, 22.0), "coat": (10.0, 24.0), "cardigan": (11.0, 16.0)}[o.outer]
    if not o.outer_open and o.outer != "vest":
        half, lapel = 0.0, 18.0 if o.outer != "cardigan" else 12.0
    m = _opening(fig, half, lapel)
    _shaded_region(ctx, pt, shell, top, hem, col, m, lit=True)
    if o.outer in ("jacket", "coat") and lapel:
        for sgn in (-1.0, 1.0):
            pts = [(sgn * (half + lapel * (1.0 - smoothstep(fig.y_nb, fig.y_chest + 0.12 * fig.T, y)) + 7.0), y)
                   for y in (fig.y_nb + 0.5 + i * (fig.y_chest + 0.1 * fig.T - fig.y_nb) / 6.0 for i in range(7))]
            for run in _surface_line(ctx, shell, pts, out=0.15):
                pt.line(run, INK, FINE)
    if not o.outer_open and o.outer != "vest":
        _buttons(ctx, pt, shell, [3.0], fig.y_chest, hem - 0.08 * fig.T, 4 if o.outer != "cardigan" else 5, light(col, 0.35))
    elif o.outer in ("vest", "cardigan"):
        _buttons(ctx, pt, shell, [-(half + 2.5)], fig.y_chest + 0.05 * fig.T, hem - 0.04 * fig.T, 4, light(col, 0.4))


def _belt_band(ctx: Ctx, pt: Paint, shell: Loft, y: float, col: str) -> None:
    w = 0.04 * ctx.fig.T
    pt.region(loft_region(ctx.view, shell, y - w, y + w), col, outline=FINE)


def draw_pelvis(ctx: Ctx) -> Paint:
    fig, o = ctx.fig, ctx.fig.spec.outfit
    plan = ctx.extra["plan"]
    pt = ctx.new()
    T = fig.T
    y0 = fig.y_waist - 0.05 * T
    col = o.bottom_color
    shell = fig.torso.shell(0.45)

    def crotch(a: float, y: float) -> float:
        al = abs(wrap180(a))
        # Leg holes: the crotch is low at the front and the back, high at the sides.
        lift = 0.07 * T * abs(math.sin(math.radians(al))) ** 0.8
        return (fig.y_crotch - lift) - y

    _shaded_region(ctx, pt, shell, y0, fig.y_crotch, col, crotch)
    if o.bottom == "trousers" and _visible(ctx, 0.0, 0.3):
        for run in _surface_line(ctx, shell, [(0.0, fig.y_waist + 0.05 * T), (0.0, fig.y_crotch - 0.02 * T)], out=0.1, thresh=0.3):
            pt.line(run, shade(col, 0.35), FINE)
    if ("belt" in o.accessories and plan["tucked"]) or (o.bottom in ("trousers", "shorts") and plan["tucked"]):
        if "belt" in o.accessories:
            _belt(ctx, pt, shell.shell(0.15), fig.y_waist + 0.01 * T)
        else:
            pt.region(loft_region(ctx.view, shell.shell(0.1), fig.y_waist - 0.03 * T, fig.y_waist + 0.035 * T), shade(col, 0.1),
                      outline=FINE * 0.8)
    return pt


def _skirt_loft(fig: Figure, y_top: float, hem: float, t: float, flare: float) -> Loft:
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
    keys.append(RingKey(hem, rx_hem, max(h.rzf + t, 10.0 * fig.k) * (0.9 + 0.25 * (flare - 1.0)) + 1.5, (h.rzb + t) * (0.95 + 0.2 * (flare - 1.0)), 0.0,
                        0.0, 2.1))
    keys = [kk for kk in keys if kk.y <= hem + 1e-6]
    return Loft(keys)


def draw_skirt(ctx: Ctx) -> Paint:
    """Everything that hangs from the hips over the legs: a skirt, the lower
    part of a tunic, a coat, a robe or an apron."""
    fig, o = ctx.fig, ctx.fig.spec.outfit
    plan = ctx.extra["plan"]
    pt = ctx.new()
    y_top = fig.y_waist
    T = fig.T
    if plan["bottom_hem"]:
        flare = 1.12 if o.bottom == "skirt" else 1.28
        sk = _skirt_loft(fig, y_top, plan["bottom_hem"], 0.5, flare)
        _shaded_region(ctx, pt, sk, y_top, plan["bottom_hem"], o.bottom_color, lit=True)
        if "belt" in o.accessories and plan["tucked"]:
            _belt(ctx, pt, sk.shell(0.2), fig.y_waist + 0.02 * T)
    if o.top == "tunic" and not plan["tucked"]:
        tk = _skirt_loft(fig, y_top, plan["top_hem"], 0.9, 1.08)
        _shaded_region(ctx, pt, tk, y_top, plan["top_hem"], o.top_color, lit=True)
        if "belt" in o.accessories:
            _belt(ctx, pt, tk.shell(0.3), fig.y_waist + 0.01 * T)
    hem = plan["outer_hem"]
    # The outer garment's lower part, over whatever hangs under it.
    if o.outer != "none" and hem > y_top + 0.03 * T:
        t = plan["outer_t"] + 0.6
        flare = {"robe": 1.3, "coat": 1.2, "apron": 1.0, "cardigan": 1.1, "jacket": 1.05, "vest": 1.0}.get(o.outer, 1.1)
        lo = _skirt_loft(fig, y_top, hem, t, flare)
        if o.outer == "apron":
            m = lambda a, y: (50.0 - abs(wrap180(a))) * 0.2  # noqa: E731
            _shaded_region(ctx, pt, lo, y_top, hem, o.outer_color, m)
            pt.flat(loft_region(ctx.view, lo, y_top, y_top + 0.03 * T, m), shade(o.outer_color, 0.15))
            if _visible(ctx, 0.0, 0.3):
                pocket = [lo.point(a, y, 0.15) for a, y in ((-20, y_top + 0.18 * T), (20, y_top + 0.18 * T), (20, y_top + 0.34 * T), (-20, y_top + 0.34 * T))]
                pt.line([ctx.p(q) for q in pocket] + [ctx.p(pocket[0])], shade(o.outer_color, 0.35), FINE, smooth=False)
        else:
            open_ = (o.outer_open or o.outer == "vest") and o.outer != "robe"
            m = (lambda a, y: (abs(wrap180(a)) - (6.0 if o.outer == "vest" else 11.0)) * 0.2) if open_ else None
            _shaded_region(ctx, pt, lo, y_top, hem, o.outer_color, m, lit=True)
            if o.outer == "robe":
                _belt_band(ctx, pt, lo.shell(0.3), fig.y_waist + 0.01 * T, o.accent_color)
            if o.outer == "coat" and _visible(ctx, 180.0, 0.5):
                for run in _surface_line(ctx, lo, [(180.0, fig.y_crotch), (180.0, hem - 0.3)], out=0.1, thresh=0.5):
                    pt.line(run, INK, FINE)
    return pt


def _sleeve_reach(fig: Figure) -> Tuple[float, float]:
    """How far down the arm the top's sleeve and the outer sleeve reach (0
    the shoulder, 1 the wrist; 0 for none)."""
    o = fig.spec.outfit
    top = {"short": 0.3 if o.top != "tshirt" else 0.28, "long": 1.0, "rolled": 0.62}[o.sleeves]
    if o.top == "sweater":
        top = max(top, 0.62)
    outer = {"jacket": 1.0, "coat": 1.0, "robe": 0.97, "cardigan": 1.0}.get(o.outer, 0.0)
    return top, outer


def draw_arm(ctx: Ctx, side: str, piece: str) -> Paint:
    fig = ctx.fig
    o = fig.spec.outfit
    pt = ctx.new()
    j = fig.joints
    S, E, W, HT = (j[f"{side}_{n}"] for n in ("shoulder", "elbow", "wrist", "handtip"))
    rs, re, rw = fig.arm_r
    ua = math.dist(S, E)
    fa = math.dist(E, W)
    total = ua + fa
    top_reach, outer_reach = _sleeve_reach(fig)
    if piece == "hand":
        _hand(ctx, pt, side)
        return pt
    if piece == "upper":
        a, b, r0, r1, f0, f1 = S, E, rs * 0.86, re, 0.0, ua / total
    else:
        a, b, r0, r1, f0, f1 = E, W, re * 0.97, rw, ua / total, 1.0
    _capsule(ctx, pt, a, b, r0, r1, ctx.skin)
    layers = []
    if top_reach > f0:
        layers.append((top_reach, 0.45 + (0.25 if o.top == "sweater" else 0.0), o.top_color, o.sleeves == "rolled"))
    if outer_reach > f0:
        layers.append((outer_reach, 1.0 + (0.9 if o.outer == "robe" else 0.0), o.outer_color, False))
    for reach, add, col, rolled in layers:
        tt = min(1.0, (reach - f0) / (f1 - f0))
        aa, bb = _segment(a, b, 0.0, tt)
        rr1 = lerp(r0, r1, tt) + add
        if o.outer == "robe" and col == o.outer_color and piece == "lower":
            rr1 += 2.0
        # A sleeve hugs the shoulder (a full radius there reads as a puff).
        _capsule(ctx, pt, aa, bb, r0 + add * (0.55 if piece == "upper" else 1.0), rr1, col, round_b=tt >= 1.0 and piece == "upper")
        if rolled and tt < 1.0:
            ca, cb = _segment(a, b, max(0.0, tt - 0.16), tt)
            _capsule(ctx, pt, ca, cb, lerp(r0, r1, tt - 0.16) + add + 0.5, rr1 + 0.5, light(col, 0.12), band=False, round_a=False, round_b=False)
        elif tt >= 1.0 and piece == "lower" and col == o.outer_color and o.outer in ("coat", "jacket"):
            ca, cb = _segment(a, b, 0.84, 1.0)
            _capsule(ctx, pt, ca, cb, lerp(r0, r1, 0.84) + add + 0.25, rr1 + 0.25, shade(col, 0.12), band=False, round_a=False, round_b=False)
    return pt


def _hand(ctx: Ctx, pt: Paint, side: str) -> None:
    fig = ctx.fig
    j = fig.joints
    W, HT = j[f"{side}_wrist"], j[f"{side}_handtip"]
    sgn = -1.0 if side == "right" else 1.0
    u = norm3(sub3(HT, W))
    L = math.dist(W, HT)
    w_axis = (sgn * -1.0, 0.0, 0.0)  # the palm faces the thigh
    v = norm3((0.0, -u[2], u[1]))  # forward, square to the hand
    k = fig.k * (0.94 if fig.female else 1.0) * (0.9 + 0.1 * fig.spec.body.limbs)
    pts3: List[Vec3] = []
    for t, half_v, half_w, curl in ((0.0, 2.6, 1.7, 0.0), (0.28, 4.2, 2.0, 0.0), (0.55, 4.7, 1.9, 0.0), (0.82, 4.0, 1.5, 0.6), (1.0, 2.8, 1.1, 1.1)):
        c = add3(W, scale3(u, L * t))
        c = add3(c, scale3(w_axis, curl * k))
        for ang in range(0, 360, 45):
            r = math.radians(ang)
            pts3.append(add3(c, add3(scale3(v, half_v * k * math.cos(r)), scale3(w_axis, half_w * k * math.sin(r)))))
    poly = hull(ctx.p(q) for q in pts3)
    thumb_a = add3(add3(W, scale3(u, L * 0.18)), add3(scale3(v, 2.6 * k), scale3(w_axis, 0.9 * k)))
    thumb_b = add3(add3(W, scale3(u, L * 0.55)), add3(scale3(v, 4.0 * k), scale3(w_axis, 1.9 * k)))
    thumb_front = ctx.view.depth(thumb_b) > ctx.view.depth(add3(W, scale3(u, L * 0.5)))
    if not thumb_front:
        _capsule(ctx, pt, thumb_a, thumb_b, 1.25 * k, 1.0 * k, ctx.skin, band=False)
    pt.region([poly], ctx.skin, smooth=True)
    pt.flat([capsule_band(ctx.p(W), ctx.p(HT), 3.0 * k, 2.4 * k, 1.0 * k)], ctx.skin_sh)
    if thumb_front:
        _capsule(ctx, pt, thumb_a, thumb_b, 1.25 * k, 1.0 * k, ctx.skin, band=False)
    # Two creases between the fingers, where the hand is seen broad.
    if abs(ctx.view.s) > 0.5:
        for off in (-1.3, 1.3):
            a = add3(add3(W, scale3(u, L * 0.68)), scale3(v, off * k))
            b = add3(add3(W, scale3(u, L * 0.93)), scale3(v, off * 0.8 * k))
            pt.line([ctx.p(a), ctx.p(b)], ctx.skin_dk, FINE * 0.8, smooth=False)


def _drape(ctx: Ctx) -> Optional[Tuple[str, float]]:
    """The garment that hangs over the knees (its colour and hem), if any.

    A leg under a skirt, a robe or a long coat is drawn in that cloth down to
    the hem: when the leg swings out from under the rigid skirt in a stride,
    the cloth seems to swing with it instead of a bare leg cutting through."""
    fig, o = ctx.fig, ctx.fig.spec.outfit
    plan = ctx.extra["plan"]
    knee = fig.joints["right_knee"][1]
    found: Optional[Tuple[str, float]] = None
    if plan["bottom_hem"] and plan["bottom_hem"] > knee:
        found = (o.bottom_color, plan["bottom_hem"])
    if o.top == "tunic" and not plan["tucked"] and plan["top_hem"] > knee:
        found = (o.top_color, plan["top_hem"])
    if o.outer in ("coat", "robe", "cardigan") and plan["outer_hem"] > knee:
        found = (o.outer_color, plan["outer_hem"])
    # Stop short of the hem: at rest the drape stays hidden under the skirt,
    # whose hem curves up at the sides in a view from a little above.
    return None if found is None else (found[0], found[1] - 0.06 * fig.T)


def draw_leg(ctx: Ctx, side: str, piece: str) -> Paint:
    fig = ctx.fig
    o = fig.spec.outfit
    pt = ctx.new()
    j = fig.joints
    Hp, K, A = j[f"{side}_hip"], j[f"{side}_knee"], j[f"{side}_ankle"]
    rt, rk, rc, ra = fig.leg_r
    if piece == "foot":
        _foot(ctx, pt, side)
        return pt
    trousers = o.bottom == "trousers"
    drape = _drape(ctx)
    if piece == "upper":
        a, b, r0, r1 = Hp, K, rt, rk * 1.05
        _capsule(ctx, pt, a, b, r0, r1, ctx.skin)
        if trousers:
            _capsule(ctx, pt, a, b, r0 + 0.5, r1 + 0.6, o.bottom_color)
        elif o.bottom == "shorts":
            aa, bb = _segment(a, b, 0.0, 0.72)
            _capsule(ctx, pt, aa, bb, r0 + 0.7, lerp(r0, r1, 0.72) + 1.1, o.bottom_color, round_b=False)
        if drape:
            f = max(0.0, min(1.0, (drape[1] - a[1]) / max(1e-6, b[1] - a[1])))
            aa, bb = _segment(a, b, 0.0, f)
            _capsule(ctx, pt, aa, bb, r0 + 2.5, lerp(r0, r1, f) + 3.0, drape[0], round_b=f >= 1.0)
        return pt
    a, b, r0, r1 = K, A, rc, ra
    _capsule(ctx, pt, a, b, r0, r1, ctx.skin)
    if trousers:
        _capsule(ctx, pt, a, b, r0 + 0.6, r1 + 0.9, o.bottom_color, round_b=False)
    if o.shoes == "boots":
        aa, bb = _segment(a, b, 0.42, 1.0)
        _capsule(ctx, pt, aa, bb, lerp(r0, r1, 0.42) + 1.2, r1 + 1.25, o.shoe_color, round_a=False)
        ca, cb = _segment(a, b, 0.42, 0.49)
        _capsule(ctx, pt, ca, cb, lerp(r0, r1, 0.42) + 1.4, lerp(r0, r1, 0.49) + 1.4, shade(o.shoe_color, 0.15), band=False, round_a=False,
                 round_b=False)
    if drape:
        f = max(0.0, min(1.0, (drape[1] - a[1]) / max(1e-6, b[1] - a[1])))
        if f > 0.02:
            aa, bb = _segment(a, b, 0.0, f)
            _capsule(ctx, pt, aa, bb, r0 + 3.0, lerp(r0, r1, f) + 3.6, drape[0], round_b=False)
    return pt


def _foot(ctx: Ctx, pt: Paint, side: str) -> None:
    fig = ctx.fig
    o = fig.spec.outfit
    A = fig.joints[f"{side}_ankle"]
    k = fig.k * (0.95 if fig.female else 1.0)
    l0, z0 = A[0], A[2]
    ah = -A[1]
    sole: List[Vec3] = []
    top: List[Vec3] = []
    for z, w, h in ((-5.2, 3.3, 0.72), (-2.0, 4.0, 0.95), (5.5, 4.6, 0.62), (11.5, 4.9, 0.45), (16.0, 4.3, 0.33), (18.6, 2.9, 0.26)):
        for s in (-1.0, 1.0):
            sole.append((l0 + s * w * k, 0.0, z0 + z * k))
            top.append((l0 + s * w * k * 0.92, -ah * h * 1.05, z0 + z * k))
    collar = [(l0 + 4.0 * k * math.cos(t), -ah * 1.05, z0 + 3.6 * k * math.sin(t)) for t in (2 * math.pi * i / 10 for i in range(10))]
    shoe = hull(ctx.p(q) for q in sole + top + collar)
    pt.region([shoe], o.shoe_color, smooth=True)
    sole_band = hull([ctx.p(q) for q in sole] + [ctx.p((q[0], -1.3 * k, q[2])) for q in sole])
    pt.flat([sole_band], shade(o.shoe_color, 0.4), smooth=True)
    pt.flat([capsule_band(ctx.p((l0, -ah, z0)), ctx.p((l0, -1.5, z0 + 15.0 * k)), 3.0, 2.0, 1.2)], shade(o.shoe_color, 0.18))


def draw_neck(ctx: Ctx) -> Paint:
    fig = ctx.fig
    pt = ctx.new()
    nk = fig.neck
    _shaded_region(ctx, pt, nk, nk.top, nk.bottom, ctx.skin, shade_frac=0.25)
    # The jaw's shade on the neck below it.
    pt.flat(loft_region(ctx.view, nk, nk.top, lerp(nk.top, nk.bottom, 0.55)), ctx.skin_sh)
    return pt


# ---- head ------------------------------------------------------------------------------------


def _ear_points(fig: Figure, sgn: float) -> Tuple[List[Vec3], List[Vec3]]:
    s = fig.spec.face
    hh = fig.hh
    y = fig.fy(0.535)
    p = math.radians(6.0 + 26.0 * s.ear_angle)
    base = fig.skull.point(sgn * 98.0, y, -0.02 * hh)
    u = (sgn * math.sin(p), 0.0, -math.cos(p))
    h = 0.29 * hh * s.ears
    w = 0.15 * hh * s.ears
    c = add3(base, scale3(u, w * 0.45))
    outer = ellipse3(c, (0.0, 1.0, 0.0), u, h / 2.0, w / 2.0, 16)
    root = [add3(base, (0.0, d, 0.0)) for d in (-h * 0.35, 0.0, h * 0.35)]
    inner = [add3(c, add3(scale3((0.0, 1.0, 0.0), h / 2 * 0.55 * math.cos(t)), scale3(u, w / 2 * 0.5 * math.sin(t))))
             for t in (math.radians(a) for a in range(-110, 120, 25))]
    return outer + root, inner


def draw_head(ctx: Ctx) -> Paint:
    fig = ctx.fig
    pt = ctx.new()
    ears = []
    for _name, side, sgn in SIDES:
        outer, inner = _ear_points(fig, sgn)
        front = ctx.view.facing(sgn * 90.0) > 0.22
        ears.append((front, outer, inner))
    for front, outer, inner in ears:
        if not front:
            pt.region([hull(ctx.p(q) for q in outer)], ctx.skin, smooth=True)
            pt.flat([hull(ctx.p(q) for q in inner)], ctx.skin_sh, smooth=True)
    hd = fig.head
    _shaded_region(ctx, pt, hd, hd.top, hd.bottom, ctx.skin, shade_frac=0.17, shade_cap=0.12 * fig.hh)
    for front, outer, inner in ears:
        if front:
            pt.region([hull(ctx.p(q) for q in outer)], ctx.skin, smooth=True)
            pt.flat([hull(ctx.p(q) for q in inner)], ctx.skin_sh, smooth=True)
            pt.line([ctx.p(q) for q in inner[1:-1]], ctx.skin_dk, FINE * 0.8)
    return pt


# ---- hair ------------------------------------------------------------------------------------

_SHORT = [(0, 0.19), (28, 0.2), (52, 0.27), (66, 0.56), (78, 0.55), (87, 0.41), (104, 0.43), (124, 0.71), (180, 0.82)]
_TIGHT = [(0, 0.19), (30, 0.2), (55, 0.27), (68, 0.5), (82, 0.42), (106, 0.44), (124, 0.69), (180, 0.79)]
_HAIRLINES: Dict[str, list] = {
    "buzz": [(0, 0.2), (28, 0.21), (52, 0.28), (66, 0.52), (78, 0.5), (87, 0.41), (104, 0.43), (124, 0.68), (180, 0.8)],
    "short": _SHORT,
    "side_part": [(0, 0.2), (28, 0.21), (52, 0.27), (66, 0.56), (78, 0.55), (87, 0.41), (104, 0.43), (124, 0.71), (180, 0.82)],
    "curly": [(0, 0.2), (28, 0.21), (52, 0.28), (66, 0.55), (78, 0.53), (87, 0.42), (104, 0.44), (124, 0.72), (180, 0.84)],
    "afro": [(0, 0.17), (40, 0.2), (58, 0.3), (70, 0.58), (90, 0.52), (115, 0.58), (140, 0.8), (180, 0.86)],
    "pixie": [(0, 0.31), (22, 0.3), (48, 0.33), (64, 0.58), (78, 0.56), (88, 0.43), (104, 0.45), (124, 0.73), (180, 0.84)],
    "bob": [(0, 0.34), (30, 0.35), (50, 0.4), (60, 0.87), (180, 0.91)],
    "long": [(0, 0.2), (22, 0.21), (46, 0.3), (60, 1.04), (180, 1.04)],
    "ponytail": _TIGHT,
    "bun": _TIGHT,
    "braid": _TIGHT,
    "balding": _SHORT,
}


def _hair_t(fig: Figure) -> float:
    st, v, hh = fig.spec.hair.style, fig.spec.hair.volume, fig.hh
    return {
        "buzz": 0.012, "short": 0.03 + 0.03 * v, "side_part": 0.035 + 0.035 * v, "curly": 0.05 + 0.06 * v, "afro": 0.16 + 0.12 * v,
        "pixie": 0.035 + 0.025 * v, "bob": 0.045 + 0.04 * v, "long": 0.035 + 0.04 * v, "ponytail": 0.025, "bun": 0.025, "braid": 0.025,
        "balding": 0.022,
    }.get(st, 0.03) * hh


def _hat_band_f(fig: Figure) -> Optional[Callable[[float], float]]:
    hat = fig.spec.outfit.hat
    if hat == "none":
        return None
    front, back = {"cap": (0.25, 0.36), "flat_cap": (0.26, 0.33), "beanie": (0.27, 0.34), "headscarf": (0.24, 0.5), "top_hat": (0.24, 0.3),
                   "bowler": (0.24, 0.3), "brimmed": (0.23, 0.29)}[hat]
    return lambda a: lerp(back, front, 0.5 + 0.5 * math.cos(math.radians(a)))


def _hair_loft(fig: Figure) -> Loft:
    st = fig.spec.hair.style
    t = _hair_t(fig)
    sk = fig.skull
    if st not in ("bob", "long"):
        loft = sk.shell(t, cap_top=True)
    else:
        keys = []
        mx = max(kk.rx for kk in sk.keys)
        mzb = max(kk.rzb for kk in sk.keys)
        for kk in sk.keys:
            f = (kk.y - fig.crown) / fig.hh
            if f < 0.45:
                keys.append(RingKey(kk.y, kk.rx + t, kk.rzf + t, kk.rzb + t, kk.cl, kk.cz, kk.sq))
            else:
                hold = smoothstep(0.45, 0.7, f)
                keys.append(RingKey(kk.y, lerp(kk.rx, mx, hold) + t, kk.rzf + t, lerp(kk.rzb, mzb * 0.9, hold) + t, kk.cl, kk.cz, kk.sq))
        if st == "long":
            keys.append(RingKey(fig.fy(1.08), mx + t * 1.1, fig.hh * 0.2, mzb * 0.88 + t, 0.0, -0.08 * fig.hh, 2.0))
        else:
            keys.append(RingKey(fig.fy(0.95), mx + t * 1.05, fig.hh * 0.24, mzb * 0.86 + t, 0.0, -0.05 * fig.hh, 2.0))
        k0 = sk.keys[0]
        loft = Loft([RingKey(k0.y - t, 0.0, 0.0, 0.0, k0.cl, k0.cz, k0.sq)] + keys)
    if st in ("curly", "afro"):
        amp = t * (0.28 if st == "curly" else 0.18)
        n = 9 if st == "curly" else 11

        def scallop(alpha: float, y: float, _amp=amp, _n=n, _hh=fig.hh) -> float:
            return _amp * (0.5 + 0.5 * math.sin(math.radians(alpha * _n) + y / _hh * 18.0))

        loft.bumps.append(scallop)
    return loft


def _hair_margin(fig: Figure) -> Callable[[float, float], float]:
    st = fig.spec.hair.style
    knots = _HAIRLINES.get(st, _SHORT)
    if fig.spec.body.age > 0.6 and st not in ("bob", "long", "pixie"):
        rec = 0.08 * (fig.spec.body.age - 0.6) / 0.4
        knots = [(a, f - rec * max(0.0, 1.0 - a / 70.0)) for a, f in knots]
    band = _hat_band_f(fig)

    def m(alpha: float, y: float) -> float:
        al = abs(wrap180(alpha))
        f = (y - fig.crown) / fig.hh
        v = interp_knots(al, knots) - f
        if st == "balding":
            v = min(v, (al - 66.0) * 0.004, f - interp_knots(al, [(66, 0.4), (100, 0.3), (180, 0.24)]))
        if band is not None:
            v = min(v, f - (band(alpha) - 0.06))
        return v

    return m


def draw_hair(ctx: Ctx) -> Paint:
    fig = ctx.fig
    pt = ctx.new()
    st = fig.spec.hair.style
    if st == "bald":
        return pt
    loft = _hair_loft(fig)
    m = _hair_margin(fig)
    col = ctx.hair
    if st == "buzz":
        col = mix(ctx.hair, ctx.skin, 0.4)
    polys = loft_region(ctx.view, loft, loft.top, loft.bottom, m, step=0.4)
    if not polys:
        return pt
    pt.region(polys, col)
    pt.flat(column_bands(ctx.view, loft, loft.top, loft.bottom, m, side="left", frac=0.22, cap=0.1 * fig.hh, step=0.4), shade(col, 0.24))
    if st not in ("buzz", "balding"):
        pt.flat(column_bands(ctx.view, loft, loft.top, loft.bottom, m, side="right", frac=0.1, cap=0.05 * fig.hh, step=0.4, y_from=0.02, y_to=0.4),
                light(col, 0.22))
    # Clumps: a few lines from the crown down to the hairline.
    if st not in ("buzz", "balding", "afro"):
        sh = shade(col, 0.32)
        for a0 in (-150, -110, -70, -35, 0, 35, 70, 110, 150, 180):
            pts = []
            for i in range(9):
                f = lerp(0.06, 1.1, i / 8.0)
                y = fig.fy(f)
                if y > loft.bottom or m(a0 + 6 * math.sin(i), y) < 0.02:
                    break
                pts.append((a0 + 8.0 * math.sin(i * 0.7), y))
            for run in _surface_line(ctx, loft, pts, out=0.05, thresh=0.2):
                if len(run) >= 3:
                    pt.line(run, sh, FINE * 0.9)
    if st == "side_part" and _visible(ctx, 32.0, 0.15):
        for run in _surface_line(ctx, loft, [(32.0, fig.fy(f)) for f in (0.02, 0.07, 0.12, 0.18)], out=0.05):
            pt.line(run, shade(col, 0.4), FINE)
    if st == "long" and _visible(ctx, 0.0, 0.2):
        for run in _surface_line(ctx, loft, [(0.0, fig.fy(f)) for f in (0.0, 0.05, 0.11, 0.18)], out=0.05):
            pt.line(run, shade(col, 0.4), FINE)
    return pt


def draw_hair_back(ctx: Ctx) -> Paint:
    fig = ctx.fig
    pt = ctx.new()
    st = fig.spec.hair.style
    col = ctx.hair
    hh = fig.hh
    t = _hair_t(fig)
    sk = fig.skull
    if st == "long":
        mx = max(kk.rx for kk in sk.keys)
        back = fig.torso.section(fig.y_sh).rzb
        end = fig.chin + (0.7 + 1.9 * fig.spec.hair.length) * hh
        cz_back = -(back + 1.4)
        keys = [
            RingKey(fig.fy(0.45), mx + t, 0.18 * hh, 0.2 * hh, 0.0, -0.28 * hh, 2.0),
            RingKey(fig.chin, mx + t + 0.03 * hh, 0.12 * hh, 0.16 * hh, 0.0, -0.36 * hh, 2.0),
            RingKey(fig.y_sh, mx + t + 0.12 * hh, 1.6, 1.8, 0.0, cz_back, 2.0),
            RingKey(end - 0.15 * hh, mx + t + 0.08 * hh, 1.4, 1.6, 0.0, cz_back - 0.4, 2.0),
            RingKey(end, (mx + t) * 0.72, 1.2, 1.4, 0.0, cz_back - 0.4, 2.0),
        ]
        lf = Loft(keys)
        _shaded_region(ctx, pt, lf, lf.top, lf.bottom, col, shade_frac=0.24, shade_cap=0.12 * hh)
        sh = shade(col, 0.32)
        for a0 in (-60, -30, 0, 30, 60, 150, 180, -150):
            pts = [(a0 + 6 * math.sin(i), lerp(fig.chin, end - 0.2 * hh, i / 6.0)) for i in range(7)]
            for run in _surface_line(ctx, lf, pts, out=0.05, thresh=0.2):
                pt.line(run, sh, FINE * 0.9)
        return pt
    if st in ("ponytail", "braid"):
        tie = sk.point(180.0, fig.fy(0.36), t + 0.2)
        mid = add3(tie, (0.0, 0.25 * hh, -0.09 * hh))
        end = add3(mid, (0.0, (0.3 + 0.7 * fig.spec.hair.length) * hh, 0.03 * hh))
        if st == "ponytail":
            pt.region([capsule(ctx.p(tie), ctx.p(mid), 0.075 * hh, 0.095 * hh), capsule(ctx.p(mid), ctx.p(end), 0.095 * hh, 0.035 * hh)], col)
            pt.flat([capsule_band(ctx.p(mid), ctx.p(end), 0.095 * hh, 0.035 * hh, 0.035 * hh)], shade(col, 0.24))
        else:
            n = 6
            for i in range(n):
                c = add3(mid, scale3(sub3(end, mid), i / (n - 1)))
                r = 0.1 * hh * (1.0 - 0.45 * i / n)
                pt.region([capsule(ctx.p(add3(c, (0, -r * 0.8, 0))), ctx.p(add3(c, (0, r * 0.8, 0))), r, r * 0.9)], col if i % 2 == 0 else shade(col, 0.12))
            pt.region([capsule(ctx.p(tie), ctx.p(mid), 0.1 * hh, 0.1 * hh)], col)
        pt.region([capsule(ctx.p(add3(tie, (0, -0.02 * hh, 0))), ctx.p(add3(tie, (0, 0.03 * hh, -0.015 * hh))), 0.06 * hh, 0.06 * hh)],
                  fig.spec.outfit.accent_color, outline=FINE)
        return pt
    if st == "bun":
        c = sk.point(180.0, fig.fy(0.2), t + 0.12 * hh)
        c = add3(c, (0.0, -0.04 * hh, 0.0))
        r = (0.15 + 0.04 * fig.spec.hair.volume) * hh
        sphere = [add3(c, (r * math.cos(a) * math.cos(b), r * math.sin(b), r * math.sin(a) * math.cos(b)))
                  for a in (2 * math.pi * i / 12 for i in range(12)) for b in (math.radians(d) for d in (-80, -40, 0, 40, 80))]
        circ = hull(ctx.p(q) for q in sphere)
        pt.region([circ], col, smooth=True)
        cx, cy = ctx.p(c)
        pt.line([(cx + r * 0.6 * math.cos(a), cy + r * 0.6 * math.sin(a)) for a in (math.radians(d) for d in range(150, 300, 30))],
                shade(col, 0.32), FINE)
    return pt


# ---- face ------------------------------------------------------------------------------------


def _eye_geometry(fig: Figure, sgn: float) -> Dict[str, object]:
    s = fig.spec.face
    hh = fig.hh
    shape = s.eye_shape
    ratio = {"almond": 0.42, "round": 0.56, "narrow": 0.3, "hooded": 0.36, "downturned": 0.42, "upturned": 0.42}[shape]
    ew = 0.128 * hh * s.eye_size * (1.04 if shape == "almond" else 1.0)
    eh = ew * ratio
    ac = sgn * fig.face["eye_alpha"]
    ye = fig.fy(fig.face["eye_f"])
    r = fig.skull.section(ye).rx
    d = math.degrees((ew / 2.0) / r)
    inward = -sgn
    tilt = {"downturned": 0.22, "upturned": -0.22}.get(shape, -0.04) * eh
    return {
        "inner": (ac + inward * d, ye),
        "outer": (ac - inward * d, ye + tilt),
        "top": (ac + inward * 0.12 * d, ye - eh * (0.5 if shape != "round" else 0.52)),
        "bottom": (ac + inward * 0.05 * d, ye + eh * (0.42 if shape != "round" else 0.5)),
        "center": (ac + inward * 0.1 * d, ye),
        "alpha": ac,
        "eh": eh,
        "ew": ew,
        "y": ye,
    }


def _quad_curve(a: Point, m: Point, b: Point, n: int = 8) -> List[Point]:
    """Points from ``a`` to ``b`` on the parabola through ``m`` (at the middle)."""
    c = (2 * m[0] - (a[0] + b[0]) / 2, 2 * m[1] - (a[1] + b[1]) / 2)
    out = []
    for i in range(n + 1):
        t = i / n
        out.append(((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * c[0] + t * t * b[0], (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * c[1] + t * t * b[1]))
    return out


def _eye_shapes(ctx: Ctx, g: Dict[str, object]) -> Optional[Dict[str, List[Point]]]:
    hd = ctx.fig.head
    if not _visible(ctx, g["alpha"], 0.18):
        return None
    P = {k: ctx.p(hd.point(*g[k], 0.06)) for k in ("inner", "outer", "top", "bottom")}
    top = _quad_curve(P["inner"], P["top"], P["outer"])
    bot = _quad_curve(P["outer"], P["bottom"], P["inner"])
    return {"top": top, "bottom": bot, "shape": top + bot[1:-1]}


def _draw_eye(ctx: Ctx, pt: Paint, g: Dict[str, object]) -> None:
    fig = ctx.fig
    sh = _eye_shapes(ctx, g)
    if sh is None:
        return
    eye = sh["shape"]
    pt.flat([eye], "#f4efe6")
    eh = g["eh"]
    c3 = fig.head.point(*g["center"], 0.06)
    c3 = add3(c3, (0.0, 0.0, 0.3 * eh + 0.15))
    cx, cy = ctx.p(c3)
    ry = eh * (0.5 if fig.spec.face.eye_shape != "narrow" else 0.62)
    rx = ry * max(0.38, abs(ctx.view.c) ** 0.8)
    iris = [(cx + rx * math.cos(a), cy + ry * math.sin(a)) for a in (2 * math.pi * i / 16 for i in range(16))]
    cut = clip_convex(iris, hull(eye))
    if len(cut) >= 3:
        pt.flat([cut], fig.spec.palette.eyes)
        pupil = [(cx + rx * 0.5 * math.cos(a), cy + ry * 0.5 * math.sin(a)) for a in (2 * math.pi * i / 12 for i in range(12))]
        pc = clip_convex(pupil, hull(eye))
        if len(pc) >= 3:
            pt.flat([pc], "#1a1412")
    pt.line(sh["top"], INK, 0.34 if not fig.female else 0.4)
    if fig.female:
        o = sh["top"][-1]
        p = sh["top"][-2]
        pt.line([o, (o[0] + (o[0] - p[0]) * 0.9, o[1] - abs(o[0] - p[0]) * 0.5)], INK, 0.3)
    pt.line(sh["bottom"][2:-2], ctx.skin_dk, FINE * 0.55)
    if fig.spec.face.eye_shape == "hooded":
        crease = [(q[0], q[1] - 0.22 * eh) for q in sh["top"][1:-1]]
        pt.line(crease, ctx.skin_dk, FINE * 0.7)


def _brow(ctx: Ctx, pt: Paint, g: Dict[str, object], sgn: float) -> None:
    fig = ctx.fig
    s = fig.spec.face
    hh = fig.hh
    inward = -sgn
    a_in = g["inner"][0] + inward * 0.12 * abs(g["inner"][0] - g["outer"][0])
    a_out = g["outer"][0] - inward * 0.22 * abs(g["inner"][0] - g["outer"][0])
    yb = fig.fy(fig.face["brow_f"])
    kind = s.brow
    pts = []
    for i in range(7):
        t = i / 6.0
        a = lerp(a_in, a_out, t)
        if kind == "arched":
            dy = -0.022 * hh * math.sin(math.pi * min(1.0, t * 1.25))
        elif kind == "angled":
            dy = lerp(0.012, -0.016, t) * hh
        elif kind == "soft":
            dy = -0.01 * hh * math.sin(math.pi * t)
        else:
            dy = -0.006 * hh * math.sin(math.pi * t)
        pts.append((a, yb + dy))
    w = 0.026 * hh * s.brow_weight * {"heavy": 1.4, "soft": 0.75}.get(kind, 1.0) * (1.12 if not fig.female else 0.9)
    col = _dark_of(fig.spec.palette.hair)
    for run in _surface_line(ctx, fig.head, pts, out=0.08, thresh=0.12):
        # A brow tapers from the nose outwards.
        left = []
        right = []
        for i, q in enumerate(run):
            a = run[max(0, i - 1)]
            b = run[min(len(run) - 1, i + 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            n = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / n, dx / n
            # Which end is the inner end on screen depends on the view.
            frac = i / max(1, len(run) - 1)
            ww = w * (1.0 - 0.45 * frac) / 2.0
            left.append((q[0] + nx * ww, q[1] + ny * ww))
            right.append((q[0] - nx * ww, q[1] - ny * ww))
        pt.flat([left + list(reversed(right))], col, smooth=True)


def _nose(ctx: Ctx, pt: Paint) -> None:
    fig = ctx.fig
    hd = fig.head
    s = fig.spec.face
    tip = fig.face["nose_tip_f"]
    width = {"broad": 1.35, "button": 1.1}.get(s.nose, 1.0) * (0.9 + 0.2 * s.nose_size)
    y_under = fig.fy(tip + 0.035)
    pts = [(a, y_under + 0.006 * fig.hh * (abs(a) / (8.0 * width)) ** 2) for a in [x * width for x in range(-8, 9, 2)]]
    for run in _surface_line(ctx, hd, pts, out=0.05, thresh=0.05):
        pt.line(run, ctx.skin_dk, FINE * 1.05)
    # The shaded side of the nose: the side that is further left on screen.
    sgn = -1.0 if ctx.view.project(hd.point(-10.0, fig.fy(tip), 0))[0] < ctx.view.project(hd.point(10.0, fig.fy(tip), 0))[0] else 1.0
    side = [(sgn * lerp(6.0, 9.5 * width, (i / 5.0) ** 2), fig.fy(lerp(tip - 0.1, tip + 0.012, i / 5.0))) for i in range(6)]
    if abs(ctx.view.s) < 0.9:
        for run in _surface_line(ctx, hd, side, out=0.05, thresh=0.2):
            pt.line(run, ctx.skin_dk, FINE * 0.9)
    # The wings of the nostrils.
    for ws in (-1.0, 1.0):
        wing = [(ws * a * width, fig.fy(tip + df)) for a, df in ((8.0, 0.005), (12.5, 0.02), (11.0, 0.038))]
        for run in _surface_line(ctx, hd, wing, out=0.12, thresh=0.25):
            pt.line(run, ctx.skin_dk, FINE)


def _mouth_points(fig: Figure, open_: float = 0.0) -> List[Tuple[float, float]]:
    s = fig.spec.face
    mw = 16.5 * s.mouth_width * (0.95 if fig.female else 1.0)
    ym = fig.fy(fig.face["mouth_f"])
    hh = fig.hh
    out = []
    for i in range(11):
        t = lerp(-1.0, 1.0, i / 10.0)
        lift = {"smile": -0.016 * t * t, "frown": 0.012 * t * t, "smirk": -0.016 * max(0.0, t) ** 2, "neutral": -0.003 * t * t}[s.mouth]
        out.append((t * mw, ym + lift * hh + open_ * (1.0 - t * t)))
    return out


def _mouth(ctx: Ctx, pt: Paint) -> None:
    fig = ctx.fig
    hd = fig.head
    lip = mix(ctx.skin, "#9c3c3c", 0.32)
    line = _mouth_points(fig)
    for run in _surface_line(ctx, hd, line, out=0.05, thresh=0.06):
        pt.line(run, mix(INK, lip, 0.35), 0.3)
    ym = fig.fy(fig.face["mouth_f"])
    lower = [(a * 0.55, ym + 0.04 * fig.hh + 0.004 * fig.hh * (a / 9.0) ** 2) for a in range(-9, 10, 3)]
    for run in _surface_line(ctx, hd, lower, out=0.05, thresh=0.1):
        pt.line(run, mix(ctx.skin_sh, lip, 0.4), 0.26 + 0.12 * fig.spec.face.lips)


def _age_lines(ctx: Ctx, pt: Paint, eyes: Dict[float, Dict[str, object]]) -> None:
    fig = ctx.fig
    age = fig.spec.body.age
    hd = fig.head
    col = ctx.skin_dk
    if age > 0.55:
        for sgn in (-1.0, 1.0):
            pts = [(sgn * lerp(14.0, 20.0, t), fig.fy(lerp(fig.face["nose_tip_f"] + 0.035, fig.face["mouth_f"] - 0.01, t))) for t in (0, 0.5, 1.0)]
            for run in _surface_line(ctx, hd, pts, out=0.05, thresh=0.25):
                pt.line(run, col, FINE * 0.75)
    if age > 0.8:
        for sgn, g in eyes.items():
            o = g["outer"]
            pts = [(o[0] + sgn * 2.5, o[1] + 0.004 * fig.hh), (o[0] + sgn * 6.0, o[1] + 0.012 * fig.hh)]
            for run in _surface_line(ctx, hd, pts, out=0.05, thresh=0.15):
                pt.line(run, col, FINE * 0.7, smooth=False)
        if not _hat_band_f(fig):
            for f in (0.28,):
                pts = [(a, fig.fy(f) + 0.004 * fig.hh * math.cos(math.radians(a * 3))) for a in range(-20, 21, 5)]
                for run in _surface_line(ctx, hd, pts, out=0.05, thresh=0.2):
                    pt.line(run, col, FINE * 0.7)


def _facial_hair(ctx: Ctx, pt: Paint) -> None:
    fig = ctx.fig
    kind = fig.spec.hair.facial
    if kind == "none":
        return
    hd = fig.head
    hh = fig.hh
    mf = fig.face["mouth_f"]
    tip = fig.face["nose_tip_f"]
    mw = 16.5 * fig.spec.face.mouth_width

    def f_of(y: float) -> float:
        return (y - fig.crown) / hh

    def lips_out(a: float, y: float) -> float:
        f = f_of(y)
        return max(abs(wrap180(a)) - mw * 1.05, (f - (mf + 0.05)), (mf - 0.022) - f) * 3.0

    def beard(a: float, y: float) -> float:
        al = abs(wrap180(a))
        f = f_of(y)
        cheek = interp_knots(al, [(0, 0.69), (22, 0.71), (42, 0.68), (62, 0.6), (78, 0.53), (96, 0.53)])
        return min((cheek - f) * -1.0, (100.0 - al) * 0.01)

    def mustache(a: float, y: float) -> float:
        al = abs(wrap180(a))
        f = f_of(y)
        u = al / (mw * 1.15)
        top = mf - 0.052 + 0.03 * u * u
        bottom = mf - 0.008 + 0.025 * u * u
        return min((1.0 - u) * 0.05, f - top, bottom - f)

    def goatee(a: float, y: float) -> float:
        al = abs(wrap180(a))
        f = f_of(y)
        return min((21.0 - al) * 0.01, f - (mf + 0.035))

    def chops(a: float, y: float) -> float:
        al = abs(wrap180(a))
        f = f_of(y)
        return min((al - 52.0) * 0.01, (98.0 - al) * 0.01, f - 0.46, 0.86 - f)

    col = ctx.hair
    beard_loft = Loft(list(hd.keys) + [RingKey(fig.fy(1.07), 0.08 * hh, 0.26 * hh, 0.0, 0.0, 0.05 * hh, 2.0)], list(hd.bumps))
    if kind == "stubble":
        sh = beard_loft.shell(0.12)
        pt.flat(loft_region(ctx.view, sh, fig.fy(0.5), fig.fy(1.0), _all(beard, lips_out)), mix(ctx.skin, _dark_of(ctx.hair), 0.18))
        return
    if kind == "full_beard":
        sh = beard_loft.shell(0.35 + 0.02 * hh)
        _shaded_region(ctx, pt, sh, fig.fy(0.5), sh.bottom, col, _all(beard, lips_out), shade_frac=0.25, shade_cap=0.08 * hh)
    if kind == "goatee":
        sh = beard_loft.shell(0.3)
        _shaded_region(ctx, pt, sh, fig.fy(mf), sh.bottom, col, goatee, shade_frac=0.25, shade_cap=0.05 * hh)
    if kind == "chops":
        sh = hd.shell(0.3)
        _shaded_region(ctx, pt, sh, fig.fy(0.44), fig.fy(0.88), col, chops, shade_frac=0.2, shade_cap=0.05 * hh)
    if kind in ("mustache", "goatee", "full_beard"):
        sh = hd.shell(0.45)
        _shaded_region(ctx, pt, sh, fig.fy(tip + 0.03), fig.fy(mf), col, mustache, shade_frac=0.2, shade_cap=0.04 * hh)


def _glasses(ctx: Ctx, pt: Paint, eyes: Dict[float, Dict[str, object]]) -> None:
    fig = ctx.fig
    hd = fig.head
    frame = "#2b2420"
    for sgn, g in eyes.items():
        c = add3(hd.point(*g["center"], 0.0), (0.0, 0.0, 0.9))
        r = g["ew"] * 0.62
        if ctx.view.facing(g["alpha"]) > 0.1:
            rim = [ctx.p(add3(c, (r * math.cos(t), 0.85 * r * math.sin(t), 0.0))) for t in (2 * math.pi * i / 18 for i in range(18))]
            pt.flat([rim], "#dfe8ea", opacity=0.35)
            pt.line(rim + [rim[0]], frame, 0.32)
        # The temple arm runs back to the ear.
        a0 = g["alpha"] - (-sgn) * 18.0
        pts = [(lerp(a0, sgn * 92.0, t), g["y"] - 0.01 * fig.hh) for t in (0.0, 0.3, 0.6, 1.0)]
        for run in _surface_line(ctx, hd, pts, out=0.4, thresh=0.25):
            pt.line(run, frame, 0.3)
    if _visible(ctx, 0.0, 0.2):
        gr, gl = eyes.get(-1.0), eyes.get(1.0)
        if gr and gl:
            a = add3(hd.point(*gr["inner"], 0.0), (0.0, -0.3, 0.9))
            b = add3(hd.point(*gl["inner"], 0.0), (0.0, -0.3, 0.9))
            pt.line([ctx.p(a), ctx.p(add3(scale3(add3(a, b), 0.5), (0.0, -0.4, 0.5))), ctx.p(b)], frame, 0.32)


def draw_face(ctx: Ctx) -> Paint:
    fig = ctx.fig
    pt = ctx.new()
    eyes = {sgn: _eye_geometry(fig, sgn) for _n, _s, sgn in SIDES}
    _age_lines(ctx, pt, eyes)
    _nose(ctx, pt)
    _mouth(ctx, pt)
    _facial_hair(ctx, pt)
    for sgn, g in eyes.items():
        _draw_eye(ctx, pt, g)
        _brow(ctx, pt, g, sgn)
    if "glasses" in fig.spec.outfit.accessories:
        _glasses(ctx, pt, eyes)
    return pt


def draw_blink(ctx: Ctx) -> Paint:
    fig = ctx.fig
    pt = ctx.new()
    for _n, _s, sgn in SIDES:
        g = _eye_geometry(fig, sgn)
        sh = _eye_shapes(ctx, g)
        if sh is None:
            continue
        lid = [(x, y) for x, y in sh["shape"]]
        pt.region([lid], ctx.skin, outline=0.15)
        mid = [(x, y + 0.2 * g["eh"]) for x, y in sh["top"]]
        pt.line(mid, INK, 0.34)
    return pt


def draw_talk(ctx: Ctx) -> Paint:
    fig = ctx.fig
    pt = ctx.new()
    hd = fig.head
    top = _mouth_points(fig)
    bottom = _mouth_points(fig, open_=0.07 * fig.hh)
    ok_top = [q for q in top if ctx.view.facing(q[0]) > 0.06]
    ok_bot = [q for q in bottom if ctx.view.facing(q[0]) > 0.06]
    if len(ok_top) < 2:
        return pt
    poly = [ctx.p(hd.point(a, y, 0.08)) for a, y in ok_top] + [ctx.p(hd.point(a, y, 0.02)) for a, y in reversed(ok_bot)]
    pt.region([poly], "#5a2a26", outline=0.22, smooth=True)
    teeth = [ctx.p(hd.point(a, y + 0.012 * fig.hh, 0.06)) for a, y in ok_top[1:-1]]
    if len(teeth) >= 2:
        pt.line(teeth, "#f2ece2", 0.012 * fig.hh * 1.6, smooth=True)
    return pt


# ---- hats ------------------------------------------------------------------------------------


def draw_hat(ctx: Ctx) -> Paint:
    fig = ctx.fig
    pt = ctx.new()
    hat = fig.spec.outfit.hat
    if hat == "none":
        return pt
    hh = fig.hh
    col = fig.spec.outfit.hat_color
    band = _hat_band_f(fig)
    t_hair = _hair_t(fig) if fig.spec.hair.style not in ("bald",) else 0.0
    sk = fig.skull
    t = t_hair + 0.45

    def under_band(a: float, y: float) -> float:
        return band(a) - (y - fig.crown) / hh

    if hat in ("cap", "flat_cap", "beanie"):
        shell = sk.shell(t + (0.04 * hh if hat == "beanie" else 0.0))
        if hat == "flat_cap":
            shell = Loft([RingKey(kk.y + 0.1 * hh * max(0.0, 1 - (kk.y - fig.crown) / (0.3 * hh)), kk.rx * 1.05, kk.rzf * 1.18, kk.rzb * 0.98,
                                  kk.cl, kk.cz + 0.05 * hh, kk.sq) for kk in shell.keys])
        brim_front = hat in ("cap", "flat_cap")
        brim_poly = None
        brim_front_of_crown = True
        if brim_front:
            yb = fig.fy(band(0.0))
            ln = (0.3 if hat == "cap" else 0.16) * hh
            pts3 = [shell.point(a, fig.fy(band(a)), 0.0) for a in range(-70, 71, 10)]
            tip3 = [shell.point(a, yb + (0.1 if hat == "cap" else 0.05) * hh * math.cos(math.radians(a)), ln * math.cos(math.radians(a)) ** 0.7)
                    for a in range(-60, 61, 10)]
            brim_poly = hull(ctx.p(q) for q in pts3 + tip3)
            brim_front_of_crown = ctx.view.c > -0.2
        if brim_poly and not brim_front_of_crown:
            pt.region([brim_poly], shade(col, 0.12), smooth=True)
        _shaded_region(ctx, pt, shell, shell.top, fig.fy(0.42), col, under_band, lit=True, shade_cap=0.1 * hh)
        if hat == "beanie":
            pt.region(loft_region(ctx.view, shell.shell(0.2), fig.fy(0.2), fig.fy(0.4),
                                  _all(lambda a, y: band(a) - (y - fig.crown) / hh, lambda a, y: (y - fig.crown) / hh - (band(a) - 0.08))),
                      shade(col, 0.12), outline=FINE)
        if hat == "cap" and _visible(ctx, 0.0, -1.0):
            tp = ctx.p(shell.point(0.0, shell.top + 0.01, 0.0))
            pt.dot(tp, 0.5, INK)
        if brim_poly and brim_front_of_crown:
            pt.region([brim_poly], shade(col, 0.08), smooth=True)
        return pt
    if hat == "headscarf":
        shell = sk.shell(t + 0.3)
        knots = [(0, 0.22), (40, 0.25), (58, 0.4), (70, 0.95), (180, 1.0)]

        def m(a: float, y: float) -> float:
            return interp_knots(abs(wrap180(a)), knots) - (y - fig.crown) / hh

        hang = Loft(list(shell.keys) + [RingKey(fig.fy(1.12), shell.section(fig.fy(0.5)).rx * 0.9, 0.15 * hh, 0.4 * hh, 0.0, -0.15 * hh, 2.0)])
        _shaded_region(ctx, pt, hang, hang.top, hang.bottom, col, m, lit=True, shade_cap=0.12 * hh)
        if _visible(ctx, 180.0, 0.0):
            kn = sk.point(180.0, fig.fy(0.62), t + 0.8)
            pt.region([capsule(ctx.p(kn), ctx.p(add3(kn, (0.0, 0.25 * hh, -0.08 * hh))), 0.08 * hh, 0.05 * hh)], col)
        return pt
    # Crowned hats: a brim at the band and a crown above it.
    yb = fig.fy(band(0.0) + 0.02)
    sec = sk.section(yb)
    rx, rzf, rzb = sec.rx + t + 0.4, sec.rzf + t + 0.4, sec.rzb + t + 0.4
    brim_w = {"brimmed": 0.34, "top_hat": 0.14, "bowler": 0.1}[hat] * hh
    rim = []
    for i in range(24):
        a = 2 * math.pi * i / 24
        rz = (rzf if math.cos(a) >= 0 else rzb) + brim_w
        rim.append((((rx + brim_w) * math.sin(a)), yb, sec.cz + rz * math.cos(a)))
        rim.append((((rx + brim_w) * math.sin(a)), yb - 0.35, sec.cz + rz * math.cos(a)))
    brim_poly = hull(ctx.p(q) for q in rim)
    height = {"brimmed": 0.36, "top_hat": 0.62, "bowler": 0.36}[hat] * hh
    if hat == "top_hat":
        keys = [RingKey(yb, rx, rzf, rzb, 0.0, sec.cz, 2.2), RingKey(yb - height, rx * 1.05, rzf * 1.05, rzb * 1.05, 0.0, sec.cz, 2.2),
                RingKey(yb - height - 0.01, 0.0, 0.0, 0.0, 0.0, sec.cz, 2.2)]
    else:
        keys = [RingKey(yb, rx, rzf, rzb, 0.0, sec.cz, 2.0), RingKey(yb - height * 0.6, rx * 0.96, rzf * 0.96, rzb * 0.96, 0.0, sec.cz, 2.0),
                RingKey(yb - height * 0.9, rx * 0.72, rzf * 0.72, rzb * 0.72, 0.0, sec.cz, 2.0), RingKey(yb - height, 0.0, 0.0, 0.0, 0.0, sec.cz, 2.0)]
    crown = Loft(keys)
    pt.region([brim_poly], col, smooth=True)
    pt.flat([brim_poly], shade(col, 0.08), smooth=True)
    _shaded_region(ctx, pt, crown, crown.top, crown.bottom, col, lit=True, shade_cap=0.12 * hh)
    ribbon = fig.spec.outfit.accent_color if hat != "top_hat" else shade(col, 0.4)
    pt.flat(loft_region(ctx.view, crown, yb - 0.11 * hh, yb - 0.01), ribbon)
    return pt


# ---- assembly ------------------------------------------------------------------------------


def _palette(ctx: Ctx) -> None:
    pal = ctx.fig.spec.palette
    ctx.skin = pal.skin
    ctx.skin_sh = shade(pal.skin, 0.16)
    ctx.skin_dk = shade(pal.skin, 0.34)
    ctx.hair = pal.hair


def draw_view(fig: Figure, view: View, canvas: Canvas) -> List[Part]:
    """The rig parts of one view, in paint order. Empty parts are left out."""
    ctx = Ctx(fig=fig, view=view, cv=canvas)
    _palette(ctx)
    ctx.extra["plan"] = _outfit_plan(fig)
    turned = abs(view.s) > 0.5
    front = view.c > 0.3
    tucked = ctx.extra["plan"]["tucked"]
    parts: List[Part] = []

    def add(name: str, bone: str, z: float, paint: Paint, label: str, opacity: Optional[str] = None, default: Optional[int] = None) -> None:
        if paint.els:
            parts.append(Part(name, bone, z, paint.els, label, opacity, default))

    hair_back_z = 1.0 if front else 33.0
    add("hair_back", "head", hair_back_z, draw_hair_back(ctx), "Hair - Back")
    for depth, bone_side, _sgn in SIDES:
        far = depth == "far"
        arm_z = (2.0 if turned else 40.0) if far else 43.0
        leg_z = (6.0 if turned else 10.0) if far else 13.0
        side = bone_side
        # The upper limb is painted over the lower one: its round end is the
        # elbow (or the knee), and the lower limb's end hides under it.
        add(f"{depth}_arm_u", f"{depth}_arm_u", arm_z + 0.5, draw_arm(ctx, side, "upper"), f"Upper Arm - {depth.title()}")
        add(f"{depth}_arm_l", f"{depth}_arm_l", arm_z, draw_arm(ctx, side, "lower"), f"Lower Arm - {depth.title()}")
        add(f"{depth}_hand", f"{depth}_arm_hand", arm_z + 1.0, draw_arm(ctx, side, "hand"), f"Hand - {depth.title()}")
        add(f"{depth}_leg_u", f"{depth}_leg_u", leg_z + 0.5, draw_leg(ctx, side, "upper"), f"Thigh - {depth.title()}")
        add(f"{depth}_leg_l", f"{depth}_leg_l", leg_z, draw_leg(ctx, side, "lower"), f"Shin - {depth.title()}")
        add(f"{depth}_foot", f"{depth}_leg_foot", leg_z + 1.0, draw_leg(ctx, side, "foot"), f"Foot - {depth.title()}")
    torso = draw_torso(ctx)
    add("pelvis", "pelvis", 31.0 if tucked else 20.0, draw_pelvis(ctx), "Pelvis")
    add("neck", "torso", 26.0, draw_neck(ctx), "Neck")
    add("torso", "torso", 30.0, torso, "Torso")
    if ctx.extra["plan"]["skirt_layers"]:
        add("skirt", "pelvis", 32.0, draw_skirt(ctx), "Skirt and Hem")
    add("head", "head", 50.0, draw_head(ctx), "Head")
    add("hair", "head", 52.0, draw_hair(ctx), "Hair")
    add("face", "head", 54.0, draw_face(ctx), "Face")
    add("blink", "head", 55.0, draw_blink(ctx), "Blink", "blink_vis", 0)
    add("talk", "head", 56.0, draw_talk(ctx), "Talk", "talk_vis", 0)
    add("hat", "head", 58.0, draw_hat(ctx), "Hat")
    parts.sort(key=lambda p: p.z)
    return parts


def view_joints(fig: Figure, view: View) -> Dict[str, Point]:
    """The rig joints of one view in screen cm, by the humanoid binder's names."""
    j = fig.joints
    out = {"waist": view.project(j["waist"]), "neck": view.project(j["neck"])}
    for depth, side, _sgn in SIDES:
        for name in ("shoulder", "elbow", "wrist", "handtip", "hip", "knee", "ankle", "toe"):
            out[f"{depth}_{name}"] = view.project(j[f"{side}_{name}"])
    return out


__all__ = ["Part", "draw_view", "view_joints"]
