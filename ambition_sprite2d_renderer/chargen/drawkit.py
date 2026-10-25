"""What every drawing module of the generator shares: the view context, the
rig part record, and the painting helpers for lofts, limbs and surface lines.

A :class:`Part` is one rig part of one view: a name, the bone it rides, its
paint order (``z``), an optional opacity channel (an expression, the blink)
and an optional ``feature`` (a swappable component, ``"slot:kind"``: the
document's ``features`` hide or show it, ``rigdoc.part_visible``).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .body import Figure
from .geometry import Loft, Point, Vec3, View, add3, capsule, capsule_band, column_bands, cross3, ellipse3, loft_region, norm3, scale3, sub3, tube, wrap180
from .svgout import FINE, INK, OUTLINE, Canvas, El, Paint, luminance, mix, shade, style

Margin = Callable[[float, float], float]
#: (depth word, the character's side, the side's sign on ``l``)
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
    feature: Optional[str] = None


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

    @property
    def plan(self) -> Dict[str, object]:
        return self.extra["plan"]  # type: ignore[return-value]


def make_ctx(fig: Figure, view: View, cv: Canvas) -> Ctx:
    ctx = Ctx(fig=fig, view=view, cv=cv)
    pal = fig.spec.palette
    ctx.skin = pal.skin
    ctx.skin_sh = shade(pal.skin, 0.16)
    ctx.skin_dk = shade(pal.skin, 0.34)
    ctx.hair = pal.hair
    ctx.extra["plan"] = outfit_plan(fig)
    return ctx


# ---- painting -----------------------------------------------------------------------------


def shaded_region(ctx: Ctx, pt: Paint, loft: Loft, y0: float, y1: float, color: str, margin: Optional[Margin] = None, *,
                  ink: bool = True, shade_frac: float = 0.2, shade_cap: float = 3.0, lit: bool = False) -> bool:
    """A region of ``loft`` in ``color``, shaded on its left edge; ``lit``
    adds a light band on its right edge. A style with a ``rim`` puts its
    light band on every shaded region."""
    polys = loft_region(ctx.view, loft, y0, y1, margin)
    if not polys:
        return False
    st = style()
    pt.region(polys, color, ink=ink)
    if shade_frac > 0.0:
        pt.flat(column_bands(ctx.view, loft, y0, y1, margin, side="left", frac=shade_frac * st.shade_band, cap=shade_cap * st.shade_band),
                shade(color))
    if st.rim > 0.0 and (lit or shade_frac > 0.0):
        pt.flat(column_bands(ctx.view, loft, y0, y1, margin, side="right", frac=st.rim, cap=1.6 * st.rim / 0.08, y_from=0.03, y_to=0.85),
                mix(color, "#fffaf0", st.rim_mix))
    elif lit:
        pt.flat(column_bands(ctx.view, loft, y0, y1, margin, side="right", frac=0.08, cap=1.2, y_from=0.05, y_to=0.7),
                mix(color, "#fffaf0", 0.18))
    return True


def tube3(ctx: Ctx, pt: Paint, a: Vec3, b: Vec3, r0: float, r1: float, color: str, *, band: bool = True,
          round_a: bool = True, round_b: bool = True, joint_b: bool = False) -> None:
    """A limb tube between 3D points. ``joint_b``: the B end is a joint the
    next limb (drawn UNDER this one) continues from: its cap gets a thin
    crease instead of a full outline, so an elbow or a knee reads as one
    limb bending, not two tubes stacked."""
    A, B = ctx.p(a), ctx.p(b)
    st = style()
    if joint_b and round_a:
        n = 10
        full = capsule(A, B, r0, r1, n)
        b_arc, a_arc = full[: n + 1], full[n + 1:]
        open_path = [b_arc[-1]] + a_arc + [b_arc[0]]
        pt.line(open_path, INK, 2 * st.outline, smooth=False, fixed=True)
        pt.flat([full], color)
        pt.line(b_arc[2:-2], shade(color, 0.45), FINE * 0.8)
    else:
        pt.region([tube(A, B, r0, r1, round_a=round_a, round_b=round_b)], color)
    if band:
        pt.flat([capsule_band(A, B, r0, r1, 0.38 * min(r0, r1) * st.shade_band)], shade(color))
        if st.rim > 0.0:
            pt.flat([capsule_band(A, B, r0, r1, 2.0 * st.rim * min(r0, r1), side="right")], mix(color, "#fffaf0", st.rim_mix))


def segment(a: Vec3, b: Vec3, t0: float, t1: float) -> Tuple[Vec3, Vec3]:
    return (add3(a, scale3(sub3(b, a), t0)), add3(a, scale3(sub3(b, a), t1)))


def visible(ctx: Ctx, alpha: float, thresh: float = 0.1) -> bool:
    return ctx.view.facing(alpha) > thresh


def surface_line(ctx: Ctx, loft: Loft, pts: Sequence[Tuple[float, float]], out: float = 0.05, thresh: float = 0.08) -> List[List[Point]]:
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


def insignia(ctx: Ctx, pt: Paint, c: Vec3, n: Vec3, r: float, thresh: float = 0.15) -> None:
    """The badge of the Faction of Steel at ``c`` on a surface of normal
    ``n``: a white five-point star on an olive roundel in a brass rim, drawn
    in the plane of the surface (an invented emblem). Not drawn when the
    surface faces away from the camera."""
    from .spec import UNIFORM

    n = norm3(n)
    if n[2] * ctx.view.c - n[0] * ctx.view.s < thresh:
        return
    u = norm3(cross3((0.0, -1.0, 0.0), n))
    up = norm3(cross3(n, u))
    rim = [ctx.p(q) for q in ellipse3(c, u, up, r, r, 14)]
    pt.region([rim], UNIFORM["brass"], outline=FINE * 0.7)
    pt.flat([[ctx.p(q) for q in ellipse3(add3(c, scale3(n, 0.05)), u, up, 0.74 * r, 0.74 * r, 14)]], UNIFORM["dark_olive"])
    star = []
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5
        rr = (0.62 if i % 2 == 0 else 0.25) * r
        star.append(ctx.p(add3(c, add3(scale3(n, 0.08), add3(scale3(u, rr * math.cos(a)), scale3(up, rr * math.sin(a)))))))
    pt.flat([star], "#f4f1e6")


def dark_of(c: str) -> str:
    """Brows and lashes: a dark version of the hair, never pale."""
    d = shade(c, 0.45)
    return mix(d, "#2a211d", 0.5) if luminance(d) > 0.35 else d


# ---- margins (coverage) ------------------------------------------------------------------


def all_of(*ms: Margin) -> Margin:
    return lambda a, y: min(m(a, y) for m in ms)


def between(y0: float, y1: float) -> Margin:
    return lambda a, y: min(y - y0, y1 - y)


def bands(centers: Sequence[float], half: float) -> Margin:
    return lambda a, y: max(half - abs(wrap180(a - c)) for c in centers) * 0.2


def half_of(side: str, overlap: float = 12.0) -> Margin:
    """The half of a loft on the character's ``side`` (right: alpha < 0),
    reaching ``overlap`` degrees past the middle at the front and the back."""
    centre = -90.0 if side == "right" else 90.0
    return lambda a, y: (90.0 + overlap - abs(wrap180(a - centre))) * 0.2


# ---- the outfit's plan ------------------------------------------------------------------


def outfit_plan(fig: Figure) -> Dict[str, object]:
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
    tucked = o.tucked and o.top != "tunic"
    plan["tucked"] = tucked
    plan["top_hem"] = fig.y_waist + 0.04 * T if tucked else top_hem
    outer = o.outer
    knee_y = fig.joints["right_knee"][1]
    # Hems near the feet are measured from the soles (geta raise them).
    sole = fig.sole_y
    hem = {"hip": fig.y_hipw + 0.12 * T, "knee": knee_y + 0.06 * T, "ankle": sole - 0.075 * fig.H}[o.outer_length]
    if outer == "vest":
        hem = fig.y_waist + 0.16 * T
    if outer == "cardigan" and o.outer_length == "ankle":
        hem = knee_y + 0.06 * T
    if outer == "apron":
        hem = knee_y + (0.06 * T if o.outer_length == "knee" else 0.5 * (sole - 0.075 * fig.H - knee_y))
    if outer == "robe":
        hem = sole - 0.06 * fig.H
    if outer == "kimono":
        # A kimono's hem is at the ankles, over the top of the foot.
        hem = sole - 0.042 * fig.H
    if outer == "field_jacket":
        # A field jacket always ends at the hips, on the torso.
        hem = fig.y_hipw + 0.08 * T
    plan["outer_hem"] = hem
    plan["outer_t"] = {"vest": 0.6, "jacket": 0.95, "coat": 1.15, "robe": 1.1, "apron": 0.75, "cardigan": 0.8, "field_jacket": 1.0,
                       "kimono": 1.2}.get(outer, 0.0)
    plan["bottom_hem"] = {"skirt": knee_y + 0.04 * T, "long_skirt": sole - 0.085 * fig.H}.get(o.bottom)
    return plan


__all__ = [
    "Ctx", "Margin", "Part", "SIDES", "all_of", "bands", "between", "dark_of", "half_of", "insignia", "make_ctx", "outfit_plan", "segment",
    "shaded_region", "surface_line", "tube3", "visible",
]
