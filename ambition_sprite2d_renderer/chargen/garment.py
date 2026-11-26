"""Fit and drape of upper-body garments in the character's 3D body frame.

Clothing ease is a length, in reference-body centimetres, not a scale on
anatomy. The shirt hangs from the shoulders, bridges concave sections of the
rib cage, and can be gathered at the belt. The underlying skeleton is not
involved. All views project the same garment surface.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace
from functools import lru_cache
from typing import Callable, Sequence

from .body import Figure
from .drawkit import Ctx
from .geometry import Loft, RingKey, gauss, lerp, smoothstep


@dataclass(frozen=True)
class TopProfile:
    neck: float
    shoulder: float
    chest: float
    waist: float
    hip: float
    cling: float
    sleeve_add: float
    sleeve_wide: float
    hem_flare: float
    blouse: float


# Ease is the extra half-width/depth, not circumference. The neckline stays
# close even on an oversized shirt; the fabric hangs from the shoulder.
_TOP_PROFILES = {
    "fitted": TopProfile(.35, .45, .65, .45, .55, .85, .45, .10, .12, .35),
    "regular": TopProfile(.45, .90, 1.50, 1.45, 1.25, .55, .95, .35, .65, .85),
    "relaxed": TopProfile(.55, 1.35, 2.45, 2.65, 2.15, .28, 1.65, .75, 1.15, 1.5),
    "baggy": TopProfile(.65, 1.95, 3.65, 3.95, 3.25, .08, 2.55, 1.35, 1.9, 2.3),
}
_TOP_DEFAULTS = {"tshirt": "regular", "shirt": "regular", "blouse": "relaxed",
                 "sweater": "relaxed", "tunic": "relaxed"}


def top_profile(fig: Figure, ctx: Ctx) -> TopProfile:
    """Resolve the author's fit preset and continuous extra-ease control."""
    o = fig.spec.outfit
    top_fit = getattr(o, "top_fit", "auto")
    fit = _TOP_DEFAULTS[o.top] if top_fit == "auto" else top_fit
    base = _TOP_PROFILES[fit]
    extra = getattr(o, "top_bagginess", 0.0)
    scale = fig.k * {"tshirt": .92, "shirt": 1., "blouse": 1., "sweater": 1.16, "tunic": 1.08}[o.top]
    # The extra control deliberately affects the body and sleeves much more
    # than the collar. It does not move the shoulder, elbow or wrist pivots.
    def cm(value: float, gain: float) -> float:
        return value * scale + extra * gain * fig.k

    return TopProfile(cm(base.neck, .12), cm(base.shoulder, .65),
                      cm(base.chest, 1.65), cm(base.waist, 2.1), cm(base.hip, 1.9),
                      base.cling * (1. - .50 * extra), cm(base.sleeve_add, 1.1),
                      cm(base.sleeve_wide, .85), cm(base.hem_flare, .8),
                      cm(base.blouse, .9))


class GarmentLoft(Loft):
    """A loft evaluated from a fitted profile at the requested height.

    Use the existing loft projection/ring code. In contrast to interpolating
    a second set of independent keys, the garment can enforce clearance
    against the interpolated body at *every* height. Cache repeated heights
    (the shading and the outline sample the same rings).
    """
    def __init__(self, heights: Sequence[float], section: Callable[[float], RingKey], bumps=()):
        self._profile_section = lru_cache(maxsize=1024)(section)
        super().__init__([self._profile_section(y) for y in heights], list(bumps))

    def section(self, y: float) -> RingKey:
        return self._profile_section(max(self.top, min(self.bottom, y)))

    def shell(self, t: float, *, bumps: bool = True, cap_top: bool = True) -> Loft:
        # Garment lofts are open at the neck (never closed dome caps).
        def section(y: float) -> RingKey:
            r = self.section(y)
            return replace(r, rx=r.rx + t, rzf=r.rzf + t, rzb=r.rzb + t)
        return GarmentLoft([r.y for r in self.keys], section, self.bumps if bumps else ())


def radial_allowance(inner: RingKey, outer: RingKey, alpha: float) -> float:
    """Radial displacement accommodated by a larger superellipse ring.

    The rings share their centre and squareness. Loft._at multiplies the
    radii by superellipse powers but adds bumps along the unit radius.
    The smaller of the two axis allowances is the exact conservative bound.
    """
    a = math.radians(alpha)
    sine, cosine = abs(math.sin(a)), abs(math.cos(a))
    power = 2.0 / max(1.0, inner.sq)
    dx = outer.rx-inner.rx
    dz = outer.rzf-inner.rzf if math.cos(a) >= 0 else outer.rzb-inner.rzb
    return min(dx * sine**(power-1) if sine > 1e-9 else math.inf,
               dz * cosine**(power-1) if cosine > 1e-9 else math.inf)


def top_shell(fig: Figure, plan: dict, profile: TopProfile) -> Loft:
    body = fig.torso
    body_section = lru_cache(maxsize=1024)(body.section)
    hem = min(float(plan["top_hem"]), fig.y_crotch)
    tucked = bool(plan["tucked"])
    # A belted tunic also gathers at the waist; an ordinary loose top hangs
    # uninterrupted unless it is actually tucked.
    gathered = tucked or (fig.spec.outfit.top == "tunic" and "belt" in fig.spec.outfit.accessories)
    gather_y = fig.y_belt if gathered else hem
    start = fig.y_chest
    end = max(start + .12 * fig.T, gather_y)
    chest, bottom = body_section(start), body_section(end)
    hold = 1.0 - profile.cling
    clearance = .28 * fig.k
    k = fig.k

    @lru_cache(maxsize=1024)
    def body_front(y: float) -> float:
        # The garment does not reproduce the individual bust or belly lobes.
        # Bridge the full depth of the front, and retain only the residual
        # directional displacement needed to contain the body.
        return max((sum(b(a, y) for b in body.bumps) for a in range(-85, 86, 5)), default=0.)

    def ease(y: float) -> float:
        # Smooth transitions in physical height, including the neckline.
        ys = (body.top, fig.y_sh + 2.6*k, start, fig.y_waist, fig.y_hipw, body.bottom)
        vs = (profile.neck, profile.shoulder, profile.chest, profile.waist, profile.hip, profile.hip)
        # The landmarks are normally strictly ordered; skip a degenerate
        # interval for an extreme body archetype rather than dividing by it.
        for ya, yb, a, b in zip(ys, ys[1:], vs, vs[1:]):
            if y <= yb:
                return lerp(a, b, smoothstep(ya, yb, y))
        return vs[-1]

    @lru_cache(maxsize=1024)
    def section(y: float) -> RingKey:
        r = body_section(y)
        e = max(clearance, ease(y))
        q = smoothstep(start, end, y)
        # The cloth falls toward a hem dimension instead of reproducing the
        # concavity under the bust and at the waist. Never reduce a dimension
        # below that of the body; keep squareness and centres identical.
        weight = hold * smoothstep(fig.y_sh, start, y)
        hanging_x = lerp(chest.rx, bottom.rx, q)
        hanging_f = lerp(chest.rzf + body_front(start), bottom.rzf + body_front(end), q)
        hanging_b = lerp(chest.rzb, bottom.rzb, q)
        rx = r.rx + e + weight * max(0., hanging_x - r.rx)
        front = r.rzf + e + weight * max(body_front(y), hanging_f - r.rzf, 0.)
        back = r.rzb + e + weight * max(0., hanging_b - r.rzb)
        if gathered:
            # A tuck/waist belt gathers cloth at a narrow ring, but a fold
            # of surplus fabric sits above it (blousing).
            gather = smoothstep(gather_y - .16 * fig.T, gather_y, y) * (1. - smoothstep(gather_y, gather_y + .07 * fig.T, y))
            puff = profile.blouse * gauss(y, gather_y - .115 * fig.T, .07 * fig.T)
            rx = lerp(rx + .45*puff, r.rx + clearance, gather)
            front = lerp(front + .85*puff, r.rzf + clearance, gather)
            back = lerp(back + .28*puff, r.rzb + clearance, gather)
            if tucked and y > gather_y:
                rx, front, back = r.rx + clearance, r.rzf + clearance, r.rzb + clearance
        else:
            flare = profile.hem_flare * smoothstep(fig.y_under, hem, y)
            rx += flare
            front += .7 * flare
            back += .7 * flare
        return replace(r, rx=rx, rzf=front, rzb=back)

    def residual(alpha: float, y: float) -> float:
        bump = sum(b(alpha, y) for b in body.bumps)
        needed = bump + clearance - radial_allowance(body_section(y), section(y), alpha)
        return max(bump * profile.cling, needed, 0.)

    heights = sorted({r.y for r in body.keys} | {hem, gather_y})
    return GarmentLoft(heights, section, (residual,) if body.bumps else ())


def fitted_top(ctx: Ctx) -> tuple[TopProfile, Loft]:
    """One resolved shirt surface per drawing context, reused by accessories."""
    if "fitted_top" not in ctx.extra:
        p = top_profile(ctx.fig, ctx)
        ctx.extra["fitted_top"] = (p, top_shell(ctx.fig, ctx.plan, p))
    return ctx.extra["fitted_top"]  # type: ignore[return-value]


def outer_shell(ctx: Ctx) -> Loft:
    """Clear the shirt under an ordinary generated outer layer.

    Combine the traditional tailored outer shell with the inner garment's
    envelope, rather than adding the entire shirt ease to the coat. Kimono
    has its own wrap/under-collar construction and remains independent.
    """
    if "outer_shell" not in ctx.extra:
        fig, o = ctx.fig, ctx.fig.spec.outfit
        t = float(ctx.plan["outer_t"])
        bare = fig.torso.shell(t)
        if o.outer in ("none", "kimono"):
            return bare if o.outer == "kimono" else fitted_top(ctx)[1]
        _, inner = fitted_top(ctx)
        room = .45 * fig.k
        bare_section = lru_cache(maxsize=1024)(bare.section)
        @lru_cache(maxsize=1024)
        def section(y: float) -> RingKey:
            a, b = bare_section(y), inner.section(y)
            return replace(a, rx=max(a.rx, b.rx+room), rzf=max(a.rzf, b.rzf+room), rzb=max(a.rzb, b.rzb+room))
        def bump(a: float, y: float) -> float:
            g = section(y)
            return max(0., sum(b(a,y) for b in bare.bumps) - radial_allowance(bare_section(y), g, a),
                       sum(b(a,y) for b in inner.bumps) + .20 * fig.k - radial_allowance(inner.section(y), g, a))
        ctx.extra["outer_shell"] = GarmentLoft([r.y for r in bare.keys], section, (bump,) if bare.bumps else ())
    return ctx.extra["outer_shell"]  # type: ignore[return-value]
