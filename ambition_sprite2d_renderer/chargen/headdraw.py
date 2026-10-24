"""The head: skull and ears, hair, facial hair, hats, and the face's parts.

The face is not one drawing. Each expression (``face.FACES``) draws its own
eyes and brows, each talking emotion its own mouth per viseme, all as parts on
the head bone switched by opacity channels (``face.face_channels``); the
neutral face shows by default. The eyes, brows and mouth are drawn from an
:class:`~.face.Expression` on the head model's layout (``species``), so a
horse frowns with the same parameters as a person, in every view.

The blink (``face_blink``) is its own part, shown by no row: it is for the
engine to lay over whatever row the body is drawing (Jon, 2026-10-09: an
effect of the body, not a row of the sheet).
"""

from __future__ import annotations

import math
from typing import Callable, Dict, List, Optional, Tuple

from .body import Figure
from .drawkit import SIDES, Ctx, Part, all_of, dark_of, shaded_region, surface_line, visible
from .face import EMOTIONS, FACES, TALKING, VISEMES, Expression, brows_part, eyes_part, mouth_part, with_viseme
from .geometry import Loft, Point, RingKey, Vec3, add3, capsule, capsule_band, clip_convex, column_bands, ellipse3, hull, interp_knots, lerp, loft_region, norm3, scale3, smoothstep, sub3, wrap180
from .svgout import FINE, INK, Paint, light, luminance, mix, shade

# ---- skull and ears ---------------------------------------------------------------------------


def _human_ear(fig: Figure, sgn: float) -> Tuple[List[Vec3], List[Vec3]]:
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


def _leaf(base: Vec3, axis: Vec3, across: Vec3, length: float, width: float, n: int = 9, droop: Vec3 = (0.0, 0.0, 0.0)) -> List[Vec3]:
    """A leaf (an animal's ear) from ``base`` along ``axis``, ``width`` across
    in the direction ``across``; ``droop`` bends the tip."""
    pts = []
    for side in (1.0, -1.0):
        for i in range(n + 1):
            s = i / n if side > 0 else 1.0 - i / n
            w = width * 0.5 * math.sin(math.pi * min(1.0, s * 1.08)) ** 0.75 * (1.0 - 0.35 * s)
            c = add3(add3(base, scale3(axis, length * s)), scale3(droop, s * s))
            pts.append(add3(c, scale3(across, side * w)))
    return pts


def _brow_of_coat(coat: str) -> str:
    """An animal's brow: darker than a light coat, lighter than a dark one,
    so it reads against the head either way."""
    h = coat.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    return shade(coat, 0.5) if lum > 110 else mix(coat, "#f0e2cc", 0.5)


def _cupped(leaf: List[Vec3], normal: Vec3, depth: float) -> List[Vec3]:
    """A leaf with the back of its cup: the same outline pushed back along
    ``normal`` (drawn as one hull, so the ear has body in every view)."""
    back = scale3(norm3(normal), -depth)
    return list(leaf) + [add3(q, back) for q in leaf[1:-1]]


def _animal_ears(fig: Figure, kind: str, sgn: float) -> Tuple[List[Vec3], List[Vec3], float]:
    """Outer and inner ear points, and the angle the ear faces (to decide
    whether it is in front of the skull)."""
    hh = fig.hh
    sk = fig.skull
    if kind == "horse":
        base = sk.point(sgn * 32.0, fig.fy(0.07), -0.01 * hh)
        axis = norm3((sgn * 0.22, -1.0, 0.08))
        # The ear's cup opens forward and out, so it reads in every view
        # (a flat ear facing the front is a line from the side).
        across = norm3((1.0, 0.18 * sgn, -sgn * 0.62))
        outer = _cupped(_leaf(base, axis, across, 0.34 * hh, 0.15 * hh), (sgn * 0.53, 0.0, 0.85), 0.07 * hh)
        inner = _leaf(add3(base, (sgn * 0.012 * hh, -0.03 * hh, 0.014 * hh)), axis, across, 0.26 * hh, 0.08 * hh)
        return outer, inner, sgn * 40.0
    if kind == "dog_floppy":
        base = sk.point(sgn * 64.0, fig.fy(0.13), 0.0)
        axis = norm3((sgn * 0.25, 1.0, -0.15))
        across = norm3((0.0, 0.15, 1.0))
        outer = _leaf(base, axis, across, 0.5 * hh, 0.24 * hh, droop=(sgn * 0.04 * hh, 0.0, -0.04 * hh))
        return outer, [], sgn * 85.0
    if kind == "dog_pointed":
        base = sk.point(sgn * 42.0, fig.fy(0.08), 0.0)
        axis = norm3((sgn * 0.45, -1.0, 0.05))
        across = norm3((1.0, 0.3 * sgn, -sgn * 0.5))
        outer = _cupped(_leaf(base, axis, across, 0.32 * hh, 0.2 * hh), (sgn * 0.45, 0.0, 0.9), 0.07 * hh)
        inner = _leaf(add3(base, (0.0, -0.02 * hh, 0.012 * hh)), axis, across, 0.22 * hh, 0.1 * hh)
        return outer, inner, sgn * 40.0
    if kind == "cat":
        base = sk.point(sgn * 40.0, fig.fy(0.06), 0.0)
        axis = norm3((sgn * 0.35, -1.0, 0.1))
        across = norm3((1.0, 0.25 * sgn, -sgn * 0.45))
        outer = _cupped(_leaf(base, axis, across, 0.26 * hh, 0.24 * hh, n=6), (sgn * 0.4, 0.0, 0.92), 0.06 * hh)
        inner = _leaf(add3(base, (0.0, -0.015 * hh, 0.012 * hh)), axis, across, 0.17 * hh, 0.12 * hh, n=6)
        return outer, inner, sgn * 40.0
    if kind == "flap":
        # A small rolled flap low behind the eye, laid back along the head.
        base = sk.point(sgn * 102.0, fig.fy(0.4), 0.0)
        axis = norm3((sgn * 0.3, 0.3, -1.0))
        across = norm3((0.0, 1.0, 0.3))
        outer = _cupped(_leaf(base, axis, across, 0.13 * hh, 0.07 * hh, n=6), (sgn * 1.0, 0.0, 0.0), 0.025 * hh)
        return outer, [], sgn * 100.0
    return [], [], 0.0


def coat_colors(ctx: Ctx) -> Tuple[str, str]:
    """The head's skin and its muzzle's colour."""
    sp = ctx.fig.species
    skin = ctx.skin
    if sp == "horse":
        return skin, mix(skin, "#241a18", 0.35)
    if sp in ("dog", "cat"):
        return skin, mix(skin, "#f4eadb", 0.45)
    if sp == "sea_lion":
        return skin, mix(skin, "#e2d4bc", 0.2)
    return skin, skin


def head_parts(ctx: Ctx) -> List[Part]:
    fig = ctx.fig
    model = fig.model
    pt = ctx.new()
    top_ears = ctx.new()
    hh = fig.hh
    skin, muzzle = coat_colors(ctx)
    ears = []
    if model.ears == "human":
        for _n, _side, sgn in SIDES:
            outer, inner = _human_ear(fig, sgn)
            ears.append((ctx.view.facing(sgn * 90.0) > 0.22, outer, inner, False))
    elif model.ears != "none":
        for _n, _side, sgn in SIDES:
            outer, inner, face_a = _animal_ears(fig, model.ears, sgn)
            ears.append((ctx.view.facing(face_a) > 0.15, outer, inner, model.ears in ("horse", "dog_pointed", "cat")))
    inner_col = mix(skin, "#e8a7a0", 0.45) if fig.species != "human" else ctx.skin_sh
    for front, outer, inner, upright in ears:
        if not front and not upright:
            pt.region([hull(ctx.p(q) for q in outer)], skin, smooth=True)
    hd = fig.head
    shaded_region(ctx, pt, hd, hd.top, hd.bottom, skin, shade_frac=0.17, shade_cap=0.12 * hh)
    if model.muzzle_f:
        mf = model.muzzle_f

        def muzzle_m(a: float, y: float) -> float:
            f = (y - fig.crown) / hh
            return min(f - mf, (75.0 - abs(wrap180(a))) * 0.01)

        pt.flat(loft_region(ctx.view, hd.shell(0.02), fig.fy(mf), hd.bottom, muzzle_m), muzzle)
    for front, outer, inner, upright in ears:
        if front and not upright:
            pt.region([hull(ctx.p(q) for q in outer)], skin, smooth=True)
            if inner:
                pt.flat([hull(ctx.p(q) for q in inner)], inner_col, smooth=True)
            if model.ears == "human":
                pt.line([ctx.p(q) for q in inner[1:-1]], ctx.skin_dk, FINE * 0.8)
    # Upright animal ears stand above the skull (and above a hat).
    for front, outer, inner, upright in sorted(ears, key=lambda e: e[0]):
        if upright:
            top_ears.region([hull(ctx.p(q) for q in outer)], skin, smooth=True)
            if inner and front:
                top_ears.flat([hull(ctx.p(q) for q in inner)], inner_col, smooth=True)
    behind = ctx.new()
    _species_features(ctx, pt, behind)
    out = [Part("head", "head", 50.0, pt.els, "Head")]
    if behind.els:
        out.append(Part("head_behind", "head", 49.5, behind.els, "Beak (behind the head)"))
    if top_ears.els:
        out.append(Part("head_ears", "head", 58.5, top_ears.els, "Ears"))
    return out


def _species_features(ctx: Ctx, pt: Paint, behind: Paint) -> None:
    """The fixed features of an animal's face: nostrils, a nose pad, a beak
    (into ``behind``, drawn under the head, in a view from behind)."""
    fig = ctx.fig
    hd = fig.head
    hh = fig.hh
    lay = fig.face
    kind = lay["nose"]
    if kind == "horse":
        for sgn in (-1.0, 1.0):
            a = sgn * 17.0
            if visible(ctx, a, 0.05):
                c = hd.point(a, fig.fy(0.9), 0.0)
                pts = [ctx.p(add3(c, (0.028 * hh * math.cos(t) * 0.7, 0.04 * hh * math.sin(t), 0.0))) for t in (2 * math.pi * i / 10 for i in range(10))]
                pt.flat([pts], "#2a1d1a", smooth=True)
    elif kind == "dog":
        c = hd.point(0.0, fig.fy(lay["nose_tip_f"]), 0.02 * hh)
        blob = [add3(c, (0.09 * hh * math.cos(t) * math.cos(u), 0.055 * hh * math.sin(u) - 0.01 * hh, 0.05 * hh * math.sin(t) * math.cos(u)))
                for t in (2 * math.pi * i / 10 for i in range(10)) for u in (math.radians(d) for d in (-70, -30, 0, 30, 70))]
        if ctx.view.depth(c) > -0.05 * hh or abs(ctx.view.s) > 0.5:
            pt.region([hull(ctx.p(q) for q in blob)], "#2a2224", smooth=True)
            hl = ctx.p(add3(c, (0.02 * hh, -0.03 * hh, 0.04 * hh)))
            pt.dot(hl, 0.012 * hh * 2.0, "#6a5e62")
        # The line down from the nose to the mouth.
        for run in surface_line(ctx, hd, [(0.0, fig.fy(lay["nose_tip_f"] + 0.05)), (0.0, fig.fy(lay["mouth_f"] - 0.01))], out=0.1, thresh=0.25):
            pt.line(run, shade(ctx.skin, 0.45), FINE)
    elif kind == "cat":
        c = hd.point(0.0, fig.fy(lay["nose_tip_f"]), 0.01 * hh)
        tri = [add3(c, d) for d in ((-0.04 * hh, -0.02 * hh, 0.0), (0.04 * hh, -0.02 * hh, 0.0), (0.0, 0.025 * hh, 0.01 * hh))]
        if visible(ctx, 0.0, 0.05):
            pt.region([[ctx.p(q) for q in tri]], "#d98a8a", outline=FINE * 0.6)
        for sgn in (-1.0, 1.0):
            for k, df in ((0, -0.01), (1, 0.02)):
                a0 = sgn * 18.0
                if visible(ctx, a0, 0.1):
                    p0 = hd.point(a0, fig.fy(lay["nose_tip_f"] + 0.06 + df), 0.05)
                    p1 = add3(p0, (sgn * 0.32 * hh, (-0.03 + 0.05 * k) * hh, 0.02 * hh))
                    pt.line([ctx.p(p0), ctx.p(p1)], shade(ctx.skin, 0.5), FINE * 0.6, smooth=False)
        for run in surface_line(ctx, hd, [(0.0, fig.fy(lay["nose_tip_f"] + 0.03)), (0.0, fig.fy(lay["mouth_f"] - 0.005))], out=0.1, thresh=0.25):
            pt.line(run, shade(ctx.skin, 0.45), FINE)
    elif kind == "bird":
        _beak(ctx, pt if ctx.view.c > -0.05 else behind, open_=0.0)
    elif kind == "sea_lion":
        _sea_lion_nose(ctx, pt)


def _sea_lion_nose(ctx: Ctx, pt: Paint) -> None:
    """A small dark nose pad at the muzzle's tip with two slit nostrils, the
    split down to the mouth, and long whiskers fanned back from the pads."""
    fig = ctx.fig
    hd = fig.head
    hh = fig.hh
    lay = fig.face
    tip = lay["nose_tip_f"]
    c = hd.point(0.0, fig.fy(tip + 0.03), 0.01 * hh)
    pad = [add3(c, (0.06 * hh * math.cos(t) * math.cos(u), 0.04 * hh * math.sin(u), 0.035 * hh * math.sin(t) * math.cos(u)))
           for t in (2 * math.pi * i / 10 for i in range(10)) for u in (math.radians(d) for d in (-70, -30, 0, 30, 70))]
    if ctx.view.depth(c) > -0.05 * hh or abs(ctx.view.s) > 0.5:
        pt.region([hull(ctx.p(q) for q in pad)], "#2c2422", smooth=True)
        for sgn in (-1.0, 1.0):
            if ctx.view.facing(sgn * 12.0) > 0.0:
                a = add3(c, (sgn * 0.014 * hh, -0.006 * hh, 0.036 * hh))
                b = add3(c, (sgn * 0.042 * hh, 0.012 * hh, 0.026 * hh))
                pt.line([ctx.p(a), ctx.p(b)], "#0e0a0a", FINE * 1.1, smooth=False)
    dark = shade(ctx.skin, 0.45)
    for run in surface_line(ctx, hd, [(0.0, fig.fy(tip + 0.08)), (0.0, fig.fy(lay["mouth_f"] - 0.01))], out=0.1, thresh=0.25):
        pt.line(run, dark, FINE)
    # Whiskers: pale on a dark coat, dark on a pale one.
    wcol = "#efe7d8" if luminance(ctx.skin) < 0.5 else shade(ctx.skin, 0.5)
    for sgn in (-1.0, 1.0):
        a0 = sgn * 20.0
        if not visible(ctx, a0, 0.1):
            continue
        for k, (df, dy) in enumerate(((0.0, -0.03), (0.035, 0.03), (0.07, 0.09), (0.1, 0.15))):
            p0 = hd.point(a0 + sgn * 4.0 * k, fig.fy(tip + 0.08 + df), 0.04)
            mid = add3(p0, (sgn * 0.17 * hh, dy * 0.5 * hh, -0.03 * hh))
            p1 = add3(p0, (sgn * 0.3 * hh, (dy + 0.04) * hh, -0.09 * hh))
            pt.line([ctx.p(p0), ctx.p(mid), ctx.p(p1)], wcol, FINE * 0.7)


def _beak(ctx: Ctx, pt: Paint, open_: float) -> None:
    fig = ctx.fig
    hd = fig.head
    hh = fig.hh
    lay = fig.face
    yb = fig.fy(lay["mouth_f"])
    ln = lay.get("beak", 0.34) * hh
    col = "#e0a23a"
    base = [hd.point(a, yb + dy * hh, -0.01 * hh) for a in (-22, -11, 0, 11, 22) for dy in (-0.07, 0.07)]
    tip = add3(hd.point(0.0, yb, 0.0), (0.0, 0.02 * hh, ln))
    upper = base + [add3(tip, (0.0, -0.01 * hh, 0.0))]
    upper = [q for q in upper if q[1] <= yb + 0.01 * hh] + [tip]
    lower = [q for q in base if q[1] >= yb] + [tip]
    if open_ > 0.0:
        lower = [add3(q, (0.0, open_ * 0.12 * hh * (1.0 if q is not tip else 1.6), -open_ * 0.02 * hh)) for q in lower]
        gap = hull([ctx.p(q) for q in lower] + [ctx.p(q) for q in base if q[1] >= yb])
        pt.flat([gap], "#5a2a26", smooth=True)
    pt.region([hull(ctx.p(q) for q in lower)], shade(col, 0.15), smooth=True, outline=0.45)
    pt.region([hull(ctx.p(q) for q in upper)], col, smooth=True, outline=0.45)


# ---- hair ----------------------------------------------------------------------------------------

_SHORT = [(0, 0.19), (28, 0.2), (52, 0.27), (66, 0.56), (78, 0.55), (87, 0.41), (104, 0.43), (124, 0.71), (180, 0.82)]
_TIGHT = [(0, 0.19), (30, 0.2), (55, 0.27), (68, 0.5), (82, 0.42), (106, 0.44), (124, 0.69), (180, 0.79)]
_HAIRLINES: Dict[str, list] = {
    "buzz": [(0, 0.2), (28, 0.21), (52, 0.28), (66, 0.52), (78, 0.5), (87, 0.41), (104, 0.43), (124, 0.68), (180, 0.8)],
    "short": _SHORT,
    "side_part": _SHORT,
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


def hair_thickness(fig: Figure, style: Optional[str] = None) -> float:
    st, v, hh = style or fig.spec.hair.style, fig.spec.hair.volume, fig.hh
    if fig.species != "human":
        return {"horse": 0.04, "dog": 0.04, "cat": 0.04, "bird": 0.05, "sea_lion": 0.0}[fig.species] * hh
    return {
        "buzz": 0.012, "short": 0.03 + 0.03 * v, "side_part": 0.035 + 0.035 * v, "curly": 0.05 + 0.06 * v, "afro": 0.16 + 0.12 * v,
        "pixie": 0.035 + 0.025 * v, "bob": 0.045 + 0.04 * v, "long": 0.035 + 0.04 * v, "ponytail": 0.025, "bun": 0.025, "braid": 0.025,
        "balding": 0.022, "bald": 0.0,
    }.get(st, 0.03) * hh


def _hair_loft(fig: Figure, st: str) -> Loft:
    t = hair_thickness(fig, st)
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
        keys[0] = RingKey(k0.y - t, 0.0, 0.0, 0.0, k0.cl, k0.cz, k0.sq)
        loft = Loft(keys)
    if st in ("curly", "afro"):
        amp = t * (0.28 if st == "curly" else 0.18)
        n = 9 if st == "curly" else 11

        def scallop(alpha: float, y: float, _amp=amp, _n=n, _hh=fig.hh) -> float:
            return _amp * (0.5 + 0.5 * math.sin(math.radians(alpha * _n) + y / _hh * 18.0))

        loft.bumps.append(scallop)
    return loft


def _hair_margin(fig: Figure, st: str) -> Callable[[float, float], float]:
    if fig.species == "horse":
        def m(alpha: float, y: float) -> float:
            al = abs(wrap180(alpha))
            f = (y - fig.crown) / fig.hh
            forelock = min((26.0 - al) * 0.01, 0.31 - f)
            ridge = min(0.2 - abs(math.sin(math.radians(al))), 0.42 - f if al < 90 else 0.62 - f)
            return max(forelock, ridge)

        return m
    if fig.species in ("dog", "cat"):
        return lambda alpha, y: 0.1 - (y - fig.crown) / fig.hh + 0.02 * math.cos(math.radians(alpha * 7.0))
    knots = _HAIRLINES.get(st, _SHORT)
    if fig.spec.body.age > 0.6 and st not in ("bob", "long", "pixie"):
        rec = 0.08 * (fig.spec.body.age - 0.6) / 0.4
        knots = [(a, f - rec * max(0.0, 1.0 - a / 70.0)) for a, f in knots]

    def m(alpha: float, y: float) -> float:
        al = abs(wrap180(alpha))
        f = (y - fig.crown) / fig.hh
        v = interp_knots(al, knots) - f
        if st == "balding":
            v = min(v, (al - 66.0) * 0.004, f - interp_knots(al, [(66, 0.4), (100, 0.3), (180, 0.24)]))
        return v

    return m


def hair_parts(ctx: Ctx, style: str, feature: str) -> List[Part]:
    """The hair of ``style`` (on an animal: its mane, tuft or crest)."""
    fig = ctx.fig
    out = []
    if fig.species == "horse":
        # A horse's mane is part of its neck, whatever style the spec names.
        return _mane_parts(ctx, feature)
    if style == "bald" or fig.model.hair == "none":
        return out
    pt = ctx.new()
    col = ctx.hair
    if fig.species == "bird":
        _crest(ctx, pt, col)
    else:
        loft = _hair_loft(fig, style)
        m = _hair_margin(fig, style)
        if style == "buzz" and fig.species == "human":
            col = mix(ctx.hair, ctx.skin, 0.4)
        polys = loft_region(ctx.view, loft, loft.top, loft.bottom, m, step=0.4)
        if polys:
            pt.region(polys, col)
            pt.flat(column_bands(ctx.view, loft, loft.top, loft.bottom, m, side="left", frac=0.22, cap=0.1 * fig.hh, step=0.4), shade(col, 0.24))
            if style not in ("buzz", "balding"):
                pt.flat(column_bands(ctx.view, loft, loft.top, loft.bottom, m, side="right", frac=0.1, cap=0.05 * fig.hh, step=0.4, y_from=0.02,
                                     y_to=0.4), light(col, 0.22))
            if fig.species == "human" and style not in ("buzz", "balding", "afro"):
                sh = shade(col, 0.32)
                for a0 in (-150, -110, -70, -35, 0, 35, 70, 110, 150, 180):
                    pts = []
                    for i in range(9):
                        f = lerp(0.06, 1.1, i / 8.0)
                        y = fig.fy(f)
                        if y > loft.bottom or m(a0 + 6 * math.sin(i), y) < 0.02:
                            break
                        pts.append((a0 + 8.0 * math.sin(i * 0.7), y))
                    for run in surface_line(ctx, loft, pts, out=0.05, thresh=0.2):
                        if len(run) >= 3:
                            pt.line(run, sh, FINE * 0.9)
            if style == "side_part" and visible(ctx, 32.0, 0.15):
                for run in surface_line(ctx, loft, [(32.0, fig.fy(f)) for f in (0.02, 0.07, 0.12, 0.18)], out=0.05):
                    pt.line(run, shade(col, 0.4), FINE)
    if pt.els:
        out.append(Part("hair", "head", 52.0, pt.els, "Hair", feature=feature))
    back = hair_back(ctx, style)
    if back.els:
        out.append(Part("hair_back", "head", 1.0 if ctx.view.c > 0.3 else 36.0, back.els, "Hair - Back", feature=feature))
    return out


def _crest(ctx: Ctx, pt: Paint, col: str) -> None:
    fig = ctx.fig
    hh = fig.hh
    sk = fig.skull
    for i, (a_off, ln) in enumerate(((0.0, 0.3), (-12.0, 0.24), (12.0, 0.24))):
        base = sk.point(a_off, fig.fy(0.06 + 0.05 * i), 0.0)
        tip = add3(base, (0.0, -ln * hh * 0.7, -ln * hh * 0.75))
        side = add3(base, (0.0, 0.0, -0.1 * hh))
        tri = [base, add3(base, (0.03 * hh, 0.0, 0.03 * hh)), tip, side]
        pt.region([hull(ctx.p(q) for q in tri)], col if i == 0 else shade(col, 0.12), smooth=True)


def _mane_parts(ctx: Ctx, feature: str) -> List[Part]:
    """A horse's mane: a ridge of hair along the back of the neck, from
    behind the ears to the shoulders. The part above the head's carried
    neck (``draw.NECK_SLEEVE``) turns with the head; the part below stays
    with the body; the two overlap, so a turn of the head leaves no gap."""
    from .draw import NECK_SLEEVE, NECK_UPPER_Z

    fig = ctx.fig
    hh = fig.hh
    nk = fig.neck
    sk = fig.skull
    col = ctx.hair

    def ring(y: float, width: float, out_: float) -> RingKey:
        src = nk.section(y) if y >= nk.top else sk.section(y)
        back = src.cz - src.rzb
        return RingKey(y, width * hh, 0.05 * hh, out_ * hh, 0.0, back + 0.02 * hh, 2.0)

    y0 = fig.fy(0.12)
    y_s = nk.top + (nk.bottom - nk.top) * NECK_SLEEVE
    ys = [lerp(y0, nk.bottom - 0.02 * hh, i / 9.0) for i in range(10)]
    keys = [ring(y, 0.075 - 0.02 * (i / 9.0), 0.09 - 0.03 * (i / 9.0)) for i, y in enumerate(ys)]
    lf = Loft(keys)
    front = ctx.view.c > 0.3
    out = []
    for name, bone, a, b, z in (("hair_mane", "head", lf.top, y_s + 0.06 * hh, 1.0 if front else NECK_UPPER_Z + 0.1),
                                ("hair_mane_low", "torso", y_s - 0.06 * hh, lf.bottom, 1.0 if front else 26.5)):
        pt = ctx.new()
        shaded_region(ctx, pt, lf, a, b, col, shade_frac=0.3, shade_cap=0.04 * hh)
        if pt.els:
            out.append(Part(name, bone, z, pt.els, "Mane" + (" (turns with the head)" if bone == "head" else ""), feature=feature))
    return out


def hair_back(ctx: Ctx, style: str) -> Paint:
    fig = ctx.fig
    pt = ctx.new()
    st = style
    col = ctx.hair
    hh = fig.hh
    t = hair_thickness(fig, style)
    sk = fig.skull
    if fig.species != "human":
        return pt
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
        shaded_region(ctx, pt, lf, lf.top, lf.bottom, col, shade_frac=0.24, shade_cap=0.12 * hh)
        sh = shade(col, 0.32)
        for a0 in (-60, -30, 0, 30, 60, 150, 180, -150):
            pts = [(a0 + 6 * math.sin(i), lerp(fig.chin, end - 0.2 * hh, i / 6.0)) for i in range(7)]
            for run in surface_line(ctx, lf, pts, out=0.05, thresh=0.2):
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
        c = add3(sk.point(180.0, fig.fy(0.2), t + 0.12 * hh), (0.0, -0.04 * hh, 0.0))
        r = (0.15 + 0.04 * fig.spec.hair.volume) * hh
        sphere = [add3(c, (r * math.cos(a) * math.cos(b), r * math.sin(b), r * math.sin(a) * math.cos(b)))
                  for a in (2 * math.pi * i / 12 for i in range(12)) for b in (math.radians(d) for d in (-80, -40, 0, 40, 80))]
        pt.region([hull(ctx.p(q) for q in sphere)], col, smooth=True)
        cx, cy = ctx.p(c)
        pt.line([(cx + r * 0.6 * math.cos(a), cy + r * 0.6 * math.sin(a)) for a in (math.radians(d) for d in range(150, 300, 30))],
                shade(col, 0.32), FINE)
    return pt


# ---- facial hair --------------------------------------------------------------------------------


def facial_hair_parts(ctx: Ctx) -> List[Part]:
    fig = ctx.fig
    kind = fig.spec.hair.facial
    if kind == "none" or fig.species != "human":
        return []
    pt = ctx.new()
    hd = fig.head
    hh = fig.hh
    mf = fig.face["mouth_f"]
    tip = fig.face["nose_tip_f"]
    mw = fig.face["mouth_alpha"]

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
        return min((1.0 - u) * 0.05, f - (mf - 0.052 + 0.03 * u * u), (mf - 0.008 + 0.025 * u * u) - f)

    def goatee(a: float, y: float) -> float:
        return min((21.0 - abs(wrap180(a))) * 0.01, f_of(y) - (mf + 0.035))

    def chops(a: float, y: float) -> float:
        al = abs(wrap180(a))
        f = f_of(y)
        return min((al - 52.0) * 0.01, (98.0 - al) * 0.01, f - 0.46, 0.86 - f)

    col = ctx.hair
    beard_loft = Loft(list(hd.keys) + [RingKey(fig.fy(1.07), 0.08 * hh, 0.26 * hh, 0.0, 0.0, 0.05 * hh, 2.0)], list(hd.bumps))
    if kind == "stubble":
        pt.flat(loft_region(ctx.view, beard_loft.shell(0.12), fig.fy(0.5), fig.fy(1.0), all_of(beard, lips_out)), mix(ctx.skin, dark_of(ctx.hair), 0.18))
    if kind == "full_beard":
        sh = beard_loft.shell(0.35 + 0.02 * hh)
        shaded_region(ctx, pt, sh, fig.fy(0.5), sh.bottom, col, all_of(beard, lips_out), shade_frac=0.25, shade_cap=0.08 * hh)
    if kind == "goatee":
        sh = beard_loft.shell(0.3)
        shaded_region(ctx, pt, sh, fig.fy(mf), sh.bottom, col, goatee, shade_frac=0.25, shade_cap=0.05 * hh)
    if kind == "chops":
        shaded_region(ctx, pt, hd.shell(0.3), fig.fy(0.44), fig.fy(0.88), col, chops, shade_frac=0.2, shade_cap=0.05 * hh)
    if kind in ("mustache", "goatee", "full_beard"):
        shaded_region(ctx, pt, hd.shell(0.45), fig.fy(tip + 0.03), fig.fy(mf), col, mustache, shade_frac=0.2, shade_cap=0.04 * hh)
    if not pt.els:
        return []
    # Facial hair lies over the mouth's corners but under its open shapes.
    return [Part("face_beard", "head", 54.5, pt.els, "Facial Hair", feature=f"facial_hair:{kind}")]


# ---- the face's parts --------------------------------------------------------------------------


def _eye_geometry(fig: Figure, sgn: float, e: Expression) -> Dict[str, object]:
    s = fig.spec.face
    hh = fig.hh
    lay = fig.face
    shape = s.eye_shape if fig.species == "human" else {"horse": "almond", "dog": "round", "cat": "almond", "bird": "round",
                                                                "sea_lion": "round"}[fig.species]
    ratio = {"almond": 0.42, "round": 0.56, "narrow": 0.3, "hooded": 0.36, "downturned": 0.42, "upturned": 0.42}[shape]
    ew = lay["eye_w"] * hh * (1.04 if shape == "almond" else 1.0)
    eh = ew * ratio
    ac = sgn * lay["eye_alpha"]
    ye = fig.fy(lay["eye_f"])
    r = fig.skull.section(ye).rx
    d = math.degrees((ew / 2.0) / max(1e-6, r))
    inward = -sgn
    tilt = {"downturned": 0.22, "upturned": -0.22}.get(shape, -0.04) * eh
    if fig.species == "cat":
        tilt = -0.25 * eh
    top_lift = eh * (0.5 if shape != "round" else 0.52)
    bot = eh * (0.42 if shape != "round" else 0.5)
    # The lids: a lowered upper lid comes down, a wide eye opens up, a
    # squint brings the lower lid up.
    top = top_lift * (1.0 - 0.95 * max(0.0, e.lid)) + eh * 0.3 * max(0.0, -e.lid)
    bot = bot * (1.0 - 0.55 * e.squint)
    gx, gy = e.gaze
    return {
        "inner": (ac + inward * d, ye),
        "outer": (ac - inward * d, ye + tilt),
        "top": (ac + inward * 0.12 * d, ye - top),
        "bottom": (ac + inward * 0.05 * d, ye + bot),
        "center": (ac + inward * 0.1 * d + gx * 0.45 * d, ye - gy * eh * 0.28),
        "alpha": ac, "eh": eh, "ew": ew, "y": ye, "shape": shape, "lid": e.lid, "squint": e.squint,
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
    if not visible(ctx, g["alpha"], 0.18):
        return None
    P = {k: ctx.p(hd.point(*g[k], 0.06)) for k in ("inner", "outer", "top", "bottom")}
    top = _quad_curve(P["inner"], P["top"], P["outer"])
    bot = _quad_curve(P["outer"], P["bottom"], P["inner"])
    return {"top": top, "bottom": bot, "shape": top + bot[1:-1]}


def _draw_eye(ctx: Ctx, pt: Paint, g: Dict[str, object], e: Expression) -> None:
    fig = ctx.fig
    sh = _eye_shapes(ctx, g)
    if sh is None:
        return
    eye = sh["shape"]
    shut = g["lid"] > 0.85
    if not shut:
        pt.flat([eye], "#f4efe6")
        eh = g["eh"]
        c3 = add3(fig.head.point(*g["center"], 0.06), (0.0, 0.0, 0.3 * eh + 0.15))
        cx, cy = ctx.p(c3)
        iris_frac = fig.face["iris"]
        ry = eh * (iris_frac if g["shape"] != "narrow" else min(0.62, iris_frac + 0.12))
        rx = ry * max(0.38, abs(ctx.view.c) ** 0.8)
        iris = [(cx + rx * math.cos(a), cy + ry * math.sin(a)) for a in (2 * math.pi * i / 16 for i in range(16))]
        clip = hull(eye)
        cut = clip_convex(iris, clip)
        if len(cut) >= 3:
            eye_col = fig.spec.palette.eyes if fig.species == "human" else {"horse": "#3a261c", "dog": "#4a2e1e", "cat": "#9aa83a",
                                                                             "bird": "#2a2020", "sea_lion": "#1e1612"}[fig.species]
            pt.flat([cut], eye_col)
            pr = 0.5 * e.pupil
            if fig.face.get("pupil") == "slit":
                pupil = [(cx + rx * 0.16 * e.pupil * math.cos(a), cy + ry * 0.95 * math.sin(a)) for a in (2 * math.pi * i / 12 for i in range(12))]
            else:
                pupil = [(cx + rx * pr * math.cos(a), cy + ry * pr * math.sin(a)) for a in (2 * math.pi * i / 12 for i in range(12))]
            pc = clip_convex(pupil, clip)
            if len(pc) >= 3:
                pt.flat([pc], "#1a1412")
            if fig.species != "human":
                pt.dot((cx + rx * 0.3, cy - ry * 0.35), max(0.12, ry * 0.18), "#f8f4ec")
    pt.line(sh["top"], INK, 0.44 if not fig.female else 0.5)
    if fig.female and fig.species == "human" and not shut:
        o, p = sh["top"][-1], sh["top"][-2]
        pt.line([o, (o[0] + (o[0] - p[0]) * 0.9, o[1] - abs(o[0] - p[0]) * 0.5)], INK, 0.3)
    if not shut:
        pt.line(sh["bottom"][2:-2], ctx.skin_dk, FINE * (0.55 + 0.6 * g["squint"]))
    if g["shape"] == "hooded" or g["lid"] > 0.3:
        crease = [(q[0], q[1] - 0.22 * g["eh"]) for q in sh["top"][1:-1]]
        pt.line(crease, ctx.skin_dk, FINE * 0.7)


def _brow(ctx: Ctx, pt: Paint, g: Dict[str, object], sgn: float, e: Expression) -> None:
    fig = ctx.fig
    s = fig.spec.face
    hh = fig.hh
    inward = -sgn
    span = abs(g["inner"][0] - g["outer"][0])
    a_in = g["inner"][0] + inward * 0.12 * span
    a_out = g["outer"][0] - inward * 0.22 * span
    yb = fig.fy(fig.face["brow_f"])
    kind = s.brow if fig.species == "human" else "soft"
    unit = 0.05 * hh
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
        dy -= unit * (e.brow_raise + e.brow_inner * (1.0 - t) + e.brow_outer * t)
        # Knit: the inner ends come in when they come down.
        a += inward * min(0.0, e.brow_inner) * -2.0 * (1.0 - t)
        pts.append((a, yb + dy))
    w = 0.033 * hh * s.brow_weight * {"heavy": 1.4, "soft": 0.75}.get(kind, 1.0) * (1.12 if not fig.female else 0.9)
    col = dark_of(fig.spec.palette.hair) if fig.species == "human" else _brow_of_coat(ctx.skin)
    dark_skin = fig.species == "human" and luminance(ctx.skin) < 0.3
    for run in surface_line(ctx, fig.head, pts, out=0.08, thresh=0.12):
        left, right = [], []
        for i, q in enumerate(run):
            a = run[max(0, i - 1)]
            b = run[min(len(run) - 1, i + 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            n = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / n, dx / n
            frac = i / max(1, len(run) - 1)
            ww = w * (1.0 - 0.45 * frac) / 2.0
            left.append((q[0] + nx * ww, q[1] + ny * ww))
            right.append((q[0] - nx * ww, q[1] - ny * ww))
        if dark_skin:
            # On dark skin a dark brow needs a catch-light on the brow ridge
            # under it, or the expression does not read at sprite size.
            lift = w * 0.55
            glow = [(x, y + lift) for x, y in left] + [(x, y + lift * 1.9) for x, y in reversed(right)]
            pt.flat([glow], light(ctx.skin, 0.32), smooth=True)
        pt.flat([left + list(reversed(right))], col, smooth=True)


def _human_nose(ctx: Ctx, pt: Paint) -> None:
    fig = ctx.fig
    hd = fig.head
    tip = fig.face["nose_tip_f"]
    width = fig.face.get("nose_width", 1.0)
    y_under = fig.fy(tip + 0.035)
    pts = [(a, y_under + 0.006 * fig.hh * (abs(a) / (8.0 * width)) ** 2) for a in [x * width for x in range(-8, 9, 2)]]
    for run in surface_line(ctx, hd, pts, out=0.05, thresh=0.05):
        pt.line(run, ctx.skin_dk, FINE * 1.05)
    sgn = -1.0 if ctx.view.project(hd.point(-10.0, fig.fy(tip), 0))[0] < ctx.view.project(hd.point(10.0, fig.fy(tip), 0))[0] else 1.0
    side = [(sgn * lerp(6.0, 9.5 * width, (i / 5.0) ** 2), fig.fy(lerp(tip - 0.1, tip + 0.012, i / 5.0))) for i in range(6)]
    if abs(ctx.view.s) < 0.9:
        for run in surface_line(ctx, hd, side, out=0.05, thresh=0.2):
            pt.line(run, ctx.skin_dk, FINE * 0.9)
    for ws in (-1.0, 1.0):
        wing = [(ws * a * width, fig.fy(tip + df)) for a, df in ((8.0, 0.005), (12.5, 0.02), (11.0, 0.038))]
        for run in surface_line(ctx, hd, wing, out=0.12, thresh=0.25):
            pt.line(run, ctx.skin_dk, FINE)


def _age_lines(ctx: Ctx, pt: Paint, eyes: Dict[float, Dict[str, object]]) -> None:
    fig = ctx.fig
    if fig.species != "human":
        return
    age = fig.spec.body.age
    hd = fig.head
    col = ctx.skin_dk
    if age > 0.55:
        for sgn in (-1.0, 1.0):
            pts = [(sgn * lerp(14.0, 20.0, t), fig.fy(lerp(fig.face["nose_tip_f"] + 0.035, fig.face["mouth_f"] - 0.01, t))) for t in (0, 0.5, 1.0)]
            for run in surface_line(ctx, hd, pts, out=0.05, thresh=0.25):
                pt.line(run, col, FINE * 0.75)
    if age > 0.8:
        for sgn, g in eyes.items():
            o = g["outer"]
            pts = [(o[0] + sgn * 2.5, o[1] + 0.004 * fig.hh), (o[0] + sgn * 6.0, o[1] + 0.012 * fig.hh)]
            for run in surface_line(ctx, hd, pts, out=0.05, thresh=0.15):
                pt.line(run, col, FINE * 0.7, smooth=False)


def _mouth_points(fig: Figure, e: Expression, lower: bool) -> List[Tuple[float, float]]:
    """The upper (or, with ``lower``, the lower) lip line, as (alpha, y)."""
    lay = fig.face
    mw = lay["mouth_alpha"] * (1.0 + e.wide - 0.45 * e.round)
    ym = fig.fy(lay["mouth_f"])
    hh = fig.hh
    out = []
    for i in range(11):
        t = lerp(-1.0, 1.0, i / 10.0)
        corner = t * t
        lift = -0.018 * e.smile * corner - 0.016 * e.skew * max(0.0, t) ** 2
        y = ym + lift * hh
        if lower:
            open_ = 0.085 * e.open * hh * (1.0 - corner ** (1.0 + 2.0 * (1.0 - e.round)))
            # A round mouth is as deep at the sides as in the middle.
            if e.round:
                open_ = 0.085 * e.open * hh * math.sqrt(max(0.0, 1.0 - corner))
            y += open_
        out.append((t * mw, y))
    return out


def _mouth(ctx: Ctx, pt: Paint, e: Expression) -> None:
    fig = ctx.fig
    hd = fig.head
    kind = fig.face["nose"]
    if kind == "bird":
        # From behind, the beak is the fixed one drawn under the head.
        if ctx.view.c > -0.05:
            _beak(ctx, pt, e.open)
        return
    lip = mix(ctx.skin, "#9c3c3c", 0.32) if fig.species == "human" else shade(ctx.skin, 0.5)
    up = [q for q in _mouth_points(fig, e, False) if ctx.view.facing(q[0]) > 0.04]
    lo = [q for q in _mouth_points(fig, e, True) if ctx.view.facing(q[0]) > 0.04]
    if len(up) < 2:
        return
    out = 0.05 if fig.species == "human" else 0.12
    if e.open > 0.06:
        poly = [ctx.p(hd.point(a, y, out)) for a, y in up] + [ctx.p(hd.point(a, y, out * 0.4)) for a, y in reversed(lo)]
        pt.region([poly], "#5a2a26", outline=0.22, smooth=True)
        if e.teeth > 0.05:
            teeth = [ctx.p(hd.point(a, y + 0.012 * fig.hh * e.teeth, out)) for a, y in up[1:-1]]
            if len(teeth) >= 2:
                pt.line(teeth, "#f2ece2", 0.014 * fig.hh * (1.0 + e.teeth), smooth=True)
        tongue = [ctx.p(hd.point(a * 0.5, y - 0.012 * fig.hh, out * 0.5)) for a, y in lo[2:-2]]
        if len(tongue) >= 2 and e.open > 0.4:
            pt.line(tongue, "#b04a48", 0.012 * fig.hh * 2.0, smooth=True)
    else:
        line = [ctx.p(hd.point(a, y, out)) for a, y in up]
        if e.teeth > 0.3 and fig.species == "human":
            lo2 = [ctx.p(hd.point(a, y + 0.02 * fig.hh, out)) for a, y in up]
            pt.region([line + list(reversed(lo2))], "#f2ece2", outline=0.2, smooth=True)
        pt.line(line, mix(INK, lip, 0.3), 0.38)
    if fig.species == "human":
        ym = fig.fy(fig.face["mouth_f"])
        lower = [(a * 0.55, ym + 0.04 * fig.hh + 0.004 * fig.hh * (a / 9.0) ** 2 + 0.085 * e.open * fig.hh) for a in range(-9, 10, 3)]
        for run in surface_line(ctx, hd, lower, out=0.05, thresh=0.1):
            pt.line(run, mix(ctx.skin_sh, lip, 0.4), 0.26 + 0.12 * fig.spec.face.lips)


def face_parts(ctx: Ctx) -> List[Part]:
    """Every expression's eyes, brows and mouths, the blink, and the fixed
    face lines (the nose, age), as parts on the head bone."""
    fig = ctx.fig
    out: List[Part] = []
    fixed = ctx.new()
    neutral_eyes = {sgn: _eye_geometry(fig, sgn, EMOTIONS["neutral"]) for _n, _s, sgn in SIDES}
    _age_lines(ctx, fixed, neutral_eyes)
    if fig.face["nose"] == "human":
        _human_nose(ctx, fixed)
    if fixed.els:
        out.append(Part("face_lines", "head", 54.0, fixed.els, "Face Lines"))
    for name, e in FACES.items():
        eyes, brows = ctx.new(), ctx.new()
        for _n, _s, sgn in SIDES:
            g = _eye_geometry(fig, sgn, e)
            _draw_eye(ctx, eyes, g, e)
            _brow(ctx, brows, g, sgn, e)
        default = 1 if name == "neutral" else 0
        if eyes.els:
            out.append(Part(eyes_part(name), "head", 54.2, eyes.els, f"Eyes - {name}", eyes_part(name) + "_vis", default))
        if brows.els:
            out.append(Part(brows_part(name), "head", 54.3, brows.els, f"Brows - {name}", brows_part(name) + "_vis", default))
    for name in TALKING:
        for vis in VISEMES:
            mouth = ctx.new()
            _mouth(ctx, mouth, with_viseme(EMOTIONS[name], vis))
            if mouth.els:
                default = 1 if (name, vis) == ("neutral", "rest") else 0
                out.append(Part(mouth_part(name, vis), "head", 54.6, mouth.els, f"Mouth - {name} {vis}", mouth_part(name, vis) + "_vis", default))
    blink = ctx.new()
    for _n, _s, sgn in SIDES:
        g = _eye_geometry(fig, sgn, EMOTIONS["neutral"])
        sh = _eye_shapes(ctx, g)
        if sh is None:
            continue
        lid = [(x, y - 0.06 * g["eh"]) for x, y in sh["top"]] + [(x, y + 0.06 * g["eh"]) for x, y in sh["bottom"][1:-1]]
        blink.region([lid], ctx.skin, outline=0.12)
        blink.line([(x, y + 0.22 * g["eh"]) for x, y in sh["top"]], INK, 0.34)
    if blink.els:
        out.append(Part("face_blink", "head", 55.9, blink.els, "Blink", "face_blink_vis", 0))
    return out


def glasses_parts(ctx: Ctx) -> List[Part]:
    fig = ctx.fig
    if "glasses" not in fig.spec.outfit.accessories:
        return []
    pt = ctx.new()
    hd = fig.head
    frame = "#2b2420"
    eyes = {sgn: _eye_geometry(fig, sgn, EMOTIONS["neutral"]) for _n, _s, sgn in SIDES}
    for sgn, g in eyes.items():
        c = add3(hd.point(*g["center"], 0.0), (0.0, 0.0, 0.9))
        r = g["ew"] * 0.62
        if ctx.view.facing(g["alpha"]) > 0.1:
            rim = [ctx.p(add3(c, (r * math.cos(t), 0.85 * r * math.sin(t), 0.0))) for t in (2 * math.pi * i / 18 for i in range(18))]
            pt.flat([rim], "#dfe8ea", opacity=0.35)
            pt.line(rim + [rim[0]], frame, 0.32)
        a0 = g["alpha"] - (-sgn) * 18.0
        pts = [(lerp(a0, sgn * 92.0, t), g["y"] - 0.01 * fig.hh) for t in (0.0, 0.3, 0.6, 1.0)]
        for run in surface_line(ctx, hd, pts, out=0.4, thresh=0.25):
            pt.line(run, frame, 0.3)
    if visible(ctx, 0.0, 0.2):
        gr, gl = eyes.get(-1.0), eyes.get(1.0)
        a = add3(hd.point(*gr["inner"], 0.0), (0.0, -0.3, 0.9))
        b = add3(hd.point(*gl["inner"], 0.0), (0.0, -0.3, 0.9))
        pt.line([ctx.p(a), ctx.p(add3(scale3(add3(a, b), 0.5), (0.0, -0.4, 0.5))), ctx.p(b)], frame, 0.32)
    return [Part("face_glasses", "head", 56.5, pt.els, "Glasses", feature="acc:glasses")] if pt.els else []


# ---- hats -----------------------------------------------------------------------------------------

_BANDS = {"cap": (0.25, 0.36), "flat_cap": (0.26, 0.33), "beanie": (0.27, 0.34), "headscarf": (0.24, 0.5), "top_hat": (0.24, 0.3),
          "bowler": (0.24, 0.3), "brimmed": (0.23, 0.29)}


def hat_parts(ctx: Ctx, hat: str, color: str, feature: str) -> List[Part]:
    fig = ctx.fig
    pt = ctx.new()
    if hat == "none":
        return []
    hh = fig.hh
    col = color
    front, back = _BANDS[hat]
    # The band sits as far above the brows as on a human head, so a hat
    # never hides an animal's higher-set eyes.
    lift = max(0.0, front - (fig.face["brow_f"] - 0.145))
    front, back = front - lift, back - lift

    def band(a: float) -> float:
        return lerp(back, front, 0.5 + 0.5 * math.cos(math.radians(a)))

    # A hat sits over the fullest hair the head can wear, so a swap never
    # shows hair through it.
    t_hair = max(hair_thickness(fig, "short"), hair_thickness(fig) if fig.spec.hair.style != "bald" else 0.0)
    if fig.spec.hair.style in ("afro",) and fig.species == "human":
        t_hair = hair_thickness(fig)
    sk = fig.skull
    t = t_hair + 0.45

    def under_band(a: float, y: float) -> float:
        return band(a) - (y - fig.crown) / hh

    if hat in ("cap", "flat_cap", "beanie"):
        shell = sk.shell(t + (0.04 * hh if hat == "beanie" else 0.0))
        if hat == "flat_cap":
            shell = Loft([RingKey(kk.y + 0.1 * hh * max(0.0, 1 - (kk.y - fig.crown) / (0.3 * hh)), kk.rx * 1.05, kk.rzf * 1.18, kk.rzb * 0.98,
                                  kk.cl, kk.cz + 0.05 * hh, kk.sq) for kk in shell.keys])
        brim_poly = None
        brim_front = True
        if hat in ("cap", "flat_cap"):
            yb = fig.fy(band(0.0))
            ln = (0.3 if hat == "cap" else 0.16) * hh
            pts3 = [shell.point(a, fig.fy(band(a)), 0.0) for a in range(-70, 71, 10)]
            tip3 = [shell.point(a, yb + (0.1 if hat == "cap" else 0.05) * hh * math.cos(math.radians(a)), ln * math.cos(math.radians(a)) ** 0.7)
                    for a in range(-60, 61, 10)]
            brim_poly = hull(ctx.p(q) for q in pts3 + tip3)
            brim_front = ctx.view.c > -0.2
        if brim_poly and not brim_front:
            pt.region([brim_poly], shade(col, 0.12), smooth=True)
        shaded_region(ctx, pt, shell, shell.top, fig.fy(0.45), col, under_band, lit=True, shade_cap=0.1 * hh)
        if hat == "beanie":
            pt.region(loft_region(ctx.view, shell.shell(0.2), fig.fy(0.2), fig.fy(0.42),
                                  all_of(lambda a, y: band(a) - (y - fig.crown) / hh, lambda a, y: (y - fig.crown) / hh - (band(a) - 0.08))),
                      shade(col, 0.12), outline=FINE)
        if hat == "cap":
            pt.dot(ctx.p(shell.point(0.0, shell.top + 0.01, 0.0)), 0.5, INK)
        if brim_poly and brim_front:
            pt.region([brim_poly], shade(col, 0.08), smooth=True)
    elif hat == "headscarf":
        shell = sk.shell(t + 0.3)
        knots = [(0, 0.22), (40, 0.25), (58, 0.4), (70, 0.95), (180, 1.0)]
        hang = Loft(list(shell.keys) + [RingKey(fig.fy(1.12), shell.section(fig.fy(0.5)).rx * 0.9, 0.15 * hh, 0.4 * hh, 0.0, -0.15 * hh, 2.0)])
        shaded_region(ctx, pt, hang, hang.top, hang.bottom, col, lambda a, y: interp_knots(abs(wrap180(a)), knots) - (y - fig.crown) / hh,
                      lit=True, shade_cap=0.12 * hh)
        if visible(ctx, 180.0, 0.0):
            kn = sk.point(180.0, fig.fy(0.62), t + 0.8)
            pt.region([capsule(ctx.p(kn), ctx.p(add3(kn, (0.0, 0.25 * hh, -0.08 * hh))), 0.08 * hh, 0.05 * hh)], col)
    else:
        yb = fig.fy(band(0.0) + 0.02)
        sec = sk.section(yb)
        rx, rzf, rzb = sec.rx + t + 0.4, sec.rzf + t + 0.4, sec.rzb + t + 0.4
        brim_w = {"brimmed": 0.34, "top_hat": 0.14, "bowler": 0.1}[hat] * hh
        rim = []
        for i in range(24):
            a = 2 * math.pi * i / 24
            rz = (rzf if math.cos(a) >= 0 else rzb) + brim_w
            rim.append(((rx + brim_w) * math.sin(a), yb, sec.cz + rz * math.cos(a)))
            rim.append(((rx + brim_w) * math.sin(a), yb - 0.35, sec.cz + rz * math.cos(a)))
        brim_poly = hull(ctx.p(q) for q in rim)
        height = {"brimmed": 0.36, "top_hat": 0.62, "bowler": 0.36}[hat] * hh
        if hat == "top_hat":
            keys = [RingKey(yb, rx, rzf, rzb, 0.0, sec.cz, 2.2), RingKey(yb - height, rx * 1.05, rzf * 1.05, rzb * 1.05, 0.0, sec.cz, 2.2),
                    RingKey(yb - height - 0.01, 0.0, 0.0, 0.0, 0.0, sec.cz, 2.2)]
        else:
            keys = [RingKey(yb, rx, rzf, rzb, 0.0, sec.cz, 2.0), RingKey(yb - height * 0.6, rx * 0.96, rzf * 0.96, rzb * 0.96, 0.0, sec.cz, 2.0),
                    RingKey(yb - height * 0.9, rx * 0.72, rzf * 0.72, rzb * 0.72, 0.0, sec.cz, 2.0), RingKey(yb - height, 0.0, 0.0, 0.0, 0.0, sec.cz, 2.0)]
        crown = Loft(keys[::-1] if False else keys)
        pt.region([brim_poly], col, smooth=True)
        pt.flat([brim_poly], shade(col, 0.08), smooth=True)
        shaded_region(ctx, pt, crown, crown.top, crown.bottom, col, lit=True, shade_cap=0.12 * hh)
        ribbon = fig.spec.outfit.accent_color if hat != "top_hat" else shade(col, 0.4)
        pt.flat(loft_region(ctx.view, crown, yb - 0.11 * hh, yb - 0.01), ribbon)
    return [Part(f"hat_{hat}", "head", 58.0, pt.els, f"Hat - {hat}", feature=feature)] if pt.els else []


__all__ = ["coat_colors", "face_parts", "facial_hair_parts", "glasses_parts", "hair_parts", "hair_thickness", "hat_parts", "head_parts"]
