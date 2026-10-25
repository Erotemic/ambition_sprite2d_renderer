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

The spec's family (``family.FaceStyle``) sets the eyes' size and opening,
the pupil (a coloured iris or a dark dot) and the brows' weight.
"""

from __future__ import annotations

import math
from typing import Callable, Dict, List, Optional, Tuple

from .body import Figure
from .drawkit import SIDES, Ctx, Part, all_of, dark_of, insignia, shaded_region, surface_line, visible
from .face import EMOTIONS, FACES, TALKING, VISEMES, Expression, brows_part, eyes_part, mouth_part, with_viseme
from .geometry import Loft, Point, RingKey, Vec3, add3, capsule, capsule_band, clip_convex, column_bands, ellipse3, gauss, hull, interp_knots, lerp, loft_region, norm3, scale3, smoothstep, sub3, wrap180
from .family import family_of
from .svgout import FINE, INK, Paint, light, luminance, mix, shade, style

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
    if sp == "alligator":
        # A pale cream underside of the jaw and the throat.
        return skin, mix(skin, "#ece2bf", 0.82)
    return skin, skin


#: Face paint (``face.makeup``): white oshiroi, and the red of the lips and
#: the corners of the eyes.
PAINT = "#f6f1e8"
PAINT_RED = "#c3202b"


def face_skin(ctx: Ctx) -> str:
    """The colour of the face round the eyes: the skin, or the face paint."""
    return PAINT if ctx.fig.spec.face.makeup == "geisha" else ctx.skin


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
            return min(f - mf, (model.muzzle_alpha - abs(wrap180(a))) * 0.01)

        pt.flat(loft_region(ctx.view, hd.shell(0.02), fig.fy(mf), hd.bottom, muzzle_m), muzzle)
    if fig.spec.face.makeup == "geisha":
        _face_paint(ctx, pt)
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
    elif kind == "alligator":
        _alligator_features(ctx, pt)


def _face_paint(ctx: Ctx, pt: Paint) -> None:
    """White face paint over the front of the face, from under the hairline
    (on an animal, from over the brows) down to the chin; the ears and the
    back of the head stay bare."""
    fig = ctx.fig
    hh = fig.hh
    human = fig.species == "human"
    f0 = 0.17 if human else fig.face["brow_f"] - 0.07
    reach = 80.0 if human else 96.0
    # On an animal the paint stops at the jaw line: the pale underside of
    # the jaw stays its own colour.
    f1 = 1.0 if human else (fig.model.muzzle_f or 1.0)

    def m(a: float, y: float) -> float:
        f = (y - fig.crown) / hh
        return min(f - f0, f1 - f, (reach - abs(wrap180(a))) * 0.01)

    pt.flat(loft_region(ctx.view, fig.head.shell(0.03), fig.fy(f0), fig.fy(f1), m), PAINT)


def _alligator_features(ctx: Ctx, pt: Paint) -> None:
    """The fixed marks of an alligator's head: two nostrils on the knob at
    the tip of the snout, an ear slit behind each eye, a row of small pits
    along the upper jaw, and rows of bony scutes on the back of the head."""
    fig = ctx.fig
    hd = fig.head
    hh = fig.hh
    lay = fig.face
    dark = shade(ctx.skin, 0.55)
    knob = lay["nose_tip_f"] - 0.035
    for sgn in (-1.0, 1.0):
        a = sgn * 8.0
        if visible(ctx, a, 0.05):
            c = hd.point(a, fig.fy(knob), 0.005 * hh)
            q = [ctx.p(add3(c, (0.03 * hh * math.cos(t), -0.012 * hh * abs(math.sin(t)) - 0.004 * hh, 0.014 * hh * math.sin(t))))
                 for t in (2 * math.pi * i / 10 for i in range(10))]
            pt.flat([hull(q)], "#141210", smooth=True)
    for sgn in (-1.0, 1.0):
        a0 = sgn * (lay["eye_alpha"] + 36.0)
        pts = [(a0, fig.fy(lay["eye_f"] + 0.02)), (a0 + sgn * 5.0, fig.fy(lay["eye_f"] + 0.05)), (a0 + sgn * 12.0, fig.fy(lay["eye_f"] + 0.06))]
        for run in surface_line(ctx, hd, pts, out=0.05, thresh=0.15):
            pt.line(run, dark, FINE * 1.1)
    pit = shade(ctx.skin, 0.35)
    for sgn in (-1.0, 1.0):
        for a in (6.0, 18.0, 30.0, 44.0, 60.0):
            if visible(ctx, sgn * a, 0.2):
                pt.dot(ctx.p(hd.point(sgn * a, fig.fy(lay["mouth_f"] - 0.075), 0.04)), 0.011 * hh, pit)
    # Two rows of bony scutes down the back of the head: short raised dashes.
    ridge = shade(ctx.skin, 0.4)
    for sgn in (-1.0, 1.0):
        for f in (0.5, 0.62, 0.74, 0.86):
            for run in surface_line(ctx, hd, [(sgn * 168.0, fig.fy(f)), (sgn * 168.0, fig.fy(f + 0.07))], out=0.01 * hh, thresh=0.2):
                pt.line(run, ridge, FINE * 1.4, smooth=False)


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
    if st == "nihongami":
        # A wig: as thick on any head.
        return 0.05 * hh
    if fig.species != "human":
        return {"horse": 0.04, "dog": 0.04, "cat": 0.04, "bird": 0.05, "sea_lion": 0.0, "alligator": 0.0}[fig.species] * hh
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
    if style == "nihongami":
        return _nihongami_parts(ctx, feature)
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


def _ellipsoid(c: Vec3, rx: float, ry: float, rz: float) -> List[Vec3]:
    return [add3(c, (rx * math.cos(a) * math.cos(b), ry * math.sin(b), rz * math.sin(a) * math.cos(b)))
            for a in (2 * math.pi * i / 14 for i in range(14)) for b in (math.radians(d) for d in (-75, -45, -15, 15, 45, 75))]


def _nihongami_parts(ctx: Ctx, feature: str) -> List[Part]:
    """The geisha's up-do (nihongami, a shimada), worn like a wig on any
    head: smooth lacquered hair swept up from a front puff (maegami), swelling
    out over the temples (bin) and at the nape (tabo), to a topknot of two
    lobes tied in the middle (mage) with a band (tegara). On it, the
    ornaments (kanzashi) ``hair.ornaments`` asks for, in order: a comb in
    front of the knot, a bar through it, a cluster of blossoms on the left,
    a ball pin on the right, silver strips hanging on the right, a ball pin
    on the left. The ornaments are not symmetric: a left view (a mirror)
    shows them on the other side.

    On a head whose eyes sit high (an animal's), the hairline in front goes
    up with the brows, so the wig never covers the eyes."""
    fig = ctx.fig
    hh = fig.hh
    sk = fig.skull
    col = ctx.hair
    hs = fig.spec.hair
    orn = hs.ornament_color or fig.spec.outfit.accent_color
    t = hair_thickness(fig, "nihongami")
    d = min(0.0, fig.face["brow_f"] - 0.395)
    knots = [(0, 0.2), (35, 0.22), (60, 0.36), (85, 0.5), (110, 0.56), (140, 0.74), (180, 0.8)]
    knots = [(a, max(0.03, f + d * (1.0 - smoothstep(90.0, 150.0, a)))) for a, f in knots]
    f_front, f_side = knots[0][1], interp_knots(85.0, knots)

    def f_of(y: float) -> float:
        return (y - fig.crown) / hh

    def puffs(alpha: float, y: float) -> float:
        f = f_of(y)
        al = wrap180(alpha)
        v = 0.09 * gauss(f, f_front + 0.03, 0.06) * gauss(al, 0.0, 32.0)
        v += 0.13 * gauss(f, f_side - 0.08, 0.11) * (gauss(al, 82.0, 26.0) + gauss(al, -82.0, 26.0))
        v += 0.19 * gauss(f, 0.64, 0.1) * gauss(wrap180(al - 180.0), 0.0, 34.0)
        return hh * v

    wig = sk.shell(t, cap_top=True)
    wig.bumps.append(puffs)

    def m(alpha: float, y: float) -> float:
        return interp_knots(abs(wrap180(alpha)), knots) - f_of(y)

    top = sk.top - t
    cz = sk.section(fig.fy(0.05)).cz
    view = ctx.view
    centre = (0.0, fig.fy(0.4), cz)
    # (depth toward the camera, painter); the far ones go under the wig.
    items: List[Tuple[float, Callable[[Paint], None]]] = []

    def lobe(c: Vec3, rx: float, ry: float, rz: float, color: str) -> None:
        pts = _ellipsoid(c, rx, ry, rz)

        def paint(p: Paint, _pts=pts, _c=c, _ry=ry) -> None:
            p.region([hull(ctx.p(q) for q in _pts)], color, smooth=True)
            if color == col:
                cx, cy = ctx.p(add3(_c, (0.0, -0.45 * _ry, 0.0)))
                p.dot((cx + 0.15 * rx, cy), 0.28 * min(rx, _ry), light(col, 0.28))

        items.append((view.depth(c), paint))

    lobe((0.0, top - 0.085 * hh, cz + 0.03 * hh), 0.17 * hh, 0.1 * hh, 0.13 * hh, col)
    lobe((0.0, top - 0.06 * hh, cz - 0.24 * hh), 0.16 * hh, 0.11 * hh, 0.14 * hh, col)
    lobe((0.0, top - 0.07 * hh, cz - 0.1 * hh), 0.12 * hh, 0.085 * hh, 0.04 * hh, orn)
    lacquer, gold, silver = "#241815", "#d4b04a", "#c9ccc8"

    def comb(p: Paint) -> None:
        c = (0.0, top - 0.005 * hh, cz + 0.17 * hh)
        arc = [add3(c, (0.2 * hh * math.cos(a), -0.085 * hh * math.sin(a), dz)) for a in (math.pi * i / 12 for i in range(13))
               for dz in (-0.012 * hh, 0.012 * hh)]
        p.region([hull(ctx.p(q) for q in arc)], lacquer, outline=FINE)
        p.line([ctx.p(add3(c, (0.17 * hh * math.cos(a), -0.068 * hh * math.sin(a), 0.014 * hh))) for a in (math.pi * i / 10 for i in range(11))],
               gold, FINE * 1.2)

    def kogai(p: Paint) -> None:
        a, b = (-0.3 * hh, top - 0.07 * hh, cz - 0.1 * hh), (0.3 * hh, top - 0.07 * hh, cz - 0.1 * hh)
        p.region([capsule(ctx.p(a), ctx.p(b), 0.02 * hh, 0.02 * hh)], lacquer, outline=FINE)
        for q in (a, b):
            p.dot(ctx.p(q), 0.025 * hh, gold)

    def hana(p: Paint) -> None:
        base = (0.2 * hh, top + 0.03 * hh, cz + 0.06 * hh)
        for dx, dy, dz in ((0.0, 0.0, 0.0), (0.05, 0.05, -0.03), (-0.02, 0.07, 0.04), (0.06, -0.03, 0.05), (0.03, 0.1, 0.0)):
            c = add3(base, (dx * hh, dy * hh, dz * hh))
            for i in range(5):
                a = math.pi / 2 + i * 2 * math.pi / 5
                p.dot(ctx.p(add3(c, (0.03 * hh * math.cos(a), 0.03 * hh * math.sin(a), 0.0))), 0.024 * hh, orn)
            p.dot(ctx.p(c), 0.012 * hh, gold)
        for dz in (-0.02, 0.03):
            a = add3(base, (0.06 * hh, 0.12 * hh, dz * hh))
            b = add3(a, (0.01 * hh, 0.16 * hh, 0.0))
            p.line([ctx.p(a), ctx.p(b)], gold, FINE * 0.7, smooth=False)
            p.dot(ctx.p(b), 0.018 * hh, orn)

    def tama(sx: float) -> Callable[[Paint], None]:
        def paint(p: Paint) -> None:
            ball = (sx * 0.17 * hh, top - 0.13 * hh, cz - 0.27 * hh)
            stick = add3(ball, (-sx * 0.12 * hh, 0.1 * hh, 0.04 * hh))
            p.line([ctx.p(ball), ctx.p(stick)], gold, FINE * 1.1, smooth=False)
            p.region([[ctx.p(q) for q in ellipse3(ball, (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), 0.04 * hh, 0.04 * hh, 12)]], orn, outline=FINE)
            p.dot(ctx.p(add3(ball, (0.012 * hh, -0.014 * hh, 0.03 * hh))), 0.01 * hh, "#f8f4ec")
        return paint

    def bira(p: Paint) -> None:
        base = (-0.21 * hh, top + 0.02 * hh, cz + 0.02 * hh)
        p.dot(ctx.p(base), 0.03 * hh, silver)
        for i in range(5):
            end = add3(base, ((-0.04 + 0.02 * i) * hh, 0.17 * hh, (0.04 - 0.02 * i) * hh))
            p.line([ctx.p(base), ctx.p(end)], silver, FINE * 0.8, smooth=False)

    placed = [((0.0, top, cz + 0.17 * hh), comb), ((0.0, top - 0.07 * hh, cz - 0.1 * hh), kogai), ((0.2 * hh, top, cz + 0.06 * hh), hana),
              ((-0.17 * hh, top - 0.13 * hh, cz - 0.27 * hh), tama(-1.0)), ((-0.21 * hh, top, cz + 0.02 * hh), bira),
              ((0.17 * hh, top - 0.13 * hh, cz - 0.27 * hh), tama(1.0))]
    behind: List[Callable[[Paint], None]] = []
    for anchor, fn in placed[:max(0, min(6, hs.ornaments))]:
        dd = view.depth(sub3(anchor, centre))
        if dd < -0.3 * hh and anchor[1] > top - 0.02 * hh:
            behind.append(fn)
        else:
            items.append((view.depth(anchor), fn))
    pt = ctx.new()
    for fn in behind:
        fn(pt)
    polys = loft_region(view, wig, wig.top, wig.bottom, m, step=0.4)
    if polys:
        pt.region(polys, col)
        pt.flat(column_bands(view, wig, wig.top, wig.bottom, m, side="left", frac=0.2, cap=0.08 * hh, step=0.4), shade(col, 0.3))
        pt.flat(column_bands(view, wig, wig.top, wig.bottom, m, side="right", frac=0.12, cap=0.05 * hh, step=0.4, y_from=0.1, y_to=0.6),
                light(col, 0.22))
    for _d, fn in sorted(items, key=lambda it: it[0]):
        fn(pt)
    return [Part("hair", "head", 52.0, pt.els, "Hair", feature=feature)] if pt.els else []


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
                                                                "sea_lion": "round", "alligator": "almond"}[fig.species]
    ratio = {"almond": 0.42, "round": 0.56, "narrow": 0.3, "hooded": 0.36, "downturned": 0.42, "upturned": 0.42}[shape]
    if fig.species == "human":
        ratio *= family_of(fig.spec).face.eye_open
    ew = lay["eye_w"] * hh * (1.04 if shape == "almond" else 1.0)
    eh = ew * ratio
    ac = sgn * lay["eye_alpha"]
    ye = fig.fy(lay["eye_f"])
    r = fig.skull.section(ye).rx
    d = math.degrees((ew / 2.0) / max(1e-6, r))
    inward = -sgn
    tilt = {"downturned": 0.22, "upturned": -0.22}.get(shape, -0.04) * eh
    if fig.species in ("cat", "alligator"):
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
                                                                             "bird": "#2a2020", "sea_lion": "#1e1612",
                                                                             "alligator": "#b39a3c"}[fig.species]
            if fig.species == "human" and family_of(fig.spec).face.pupil == "dot":
                # A dark pupil with the iris' colour in it, and a catch-light.
                pt.flat([cut], mix(eye_col, "#1a1412", 0.6))
                pt.dot((cx - rx * 0.3, cy - ry * 0.35), max(0.12, ry * 0.3), "#f8f4ec")
            else:
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
    w = 0.033 * hh * s.brow_weight * {"heavy": 1.4, "soft": 0.75}.get(kind, 1.0) * (1.12 if not fig.female else 0.9) * family_of(fig.spec).face.brow
    col = dark_of(fig.spec.palette.hair) if fig.species == "human" else _brow_of_coat(ctx.skin)
    if fig.spec.face.makeup == "geisha":
        # Painted brows: a soft charcoal on the white.
        col = "#3a2a2a"
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
    if kind == "alligator":
        _alligator_mouth(ctx, pt, e)
        return
    painted = fig.spec.face.makeup == "geisha" and fig.species == "human"
    if painted:
        _painted_lips(ctx, pt, e)
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
                pt.line(teeth, "#f2ece2", 0.014 * fig.hh * (1.0 + e.teeth), smooth=True, fixed=True)
        tongue = [ctx.p(hd.point(a * 0.5, y - 0.012 * fig.hh, out * 0.5)) for a, y in lo[2:-2]]
        if len(tongue) >= 2 and e.open > 0.4:
            pt.line(tongue, "#b04a48", 0.012 * fig.hh * 2.0, smooth=True, fixed=True)
    else:
        line = [ctx.p(hd.point(a, y, out)) for a, y in up]
        if e.teeth > 0.3 and fig.species == "human":
            lo2 = [ctx.p(hd.point(a, y + 0.02 * fig.hh, out)) for a, y in up]
            pt.region([line + list(reversed(lo2))], "#f2ece2", outline=0.2, smooth=True)
        pt.line(line, mix(style().ink, lip, 0.3), 0.38 * (family_of(fig.spec).face.lip if fig.species == "human" else 1.0))
    if fig.species == "human" and not painted:
        ym = fig.fy(fig.face["mouth_f"])
        lower = [(a * 0.55, ym + 0.04 * fig.hh + 0.004 * fig.hh * (a / 9.0) ** 2 + 0.085 * e.open * fig.hh) for a in range(-9, 10, 3)]
        for run in surface_line(ctx, hd, lower, out=0.05, thresh=0.1):
            pt.line(run, mix(ctx.skin_sh, lip, 0.4), 0.26 + 0.12 * fig.spec.face.lips)


def _painted_lips(ctx: Ctx, pt: Paint, e: Expression) -> None:
    """A geisha's painted lips: red, smaller than the mouth (a bud in the
    middle of it), on the upper and the lower lip."""
    fig = ctx.fig
    hd = fig.head
    hh = fig.hh
    up = [(a * 0.55, y) for a, y in _mouth_points(fig, e, False)]
    lo = [(a * 0.55, y) for a, y in _mouth_points(fig, e, True)]
    top = [(a, y - 0.022 * hh * (1.0 - (i / 5.0 - 1.0) ** 2) - 0.004 * hh) for i, (a, y) in enumerate(up)]
    bot = [(a, y + 0.03 * hh * (1.0 - (i / 5.0 - 1.0) ** 2) + 0.004 * hh) for i, (a, y) in enumerate(lo)]
    poly = [ctx.p(hd.point(a, y, 0.06)) for a, y in top if ctx.view.facing(a) > 0.04]
    poly += [ctx.p(hd.point(a, y, 0.06)) for a, y in reversed(bot) if ctx.view.facing(a) > 0.04]
    if len(poly) >= 4:
        pt.flat([poly], PAINT_RED, smooth=True)


def _jaw_line(fig: Figure, e: Expression, lower: bool) -> List[Tuple[float, float]]:
    """An alligator's jaw line along the snout (or, with ``lower``, the lower
    jaw's edge when the mouth is open), as (alpha, y): it runs back from the
    tip along each side, waves a little, and turns up at the corner behind
    (a smile turns it up more). The jaw opens on a hinge at the back, so an
    open mouth is widest at the tip."""
    lay = fig.face
    hh = fig.hh
    mw = lay["mouth_alpha"] * (1.0 + 0.4 * e.wide)
    ym = fig.fy(lay["mouth_f"])
    wave = lay.get("mouth_wave", 0.0)
    out = []
    for i in range(25):
        t = lerp(-1.0, 1.0, i / 24.0)
        u = abs(t)
        y = ym + wave * hh * math.sin(math.pi * min(1.0, u / 0.8)) - (0.035 + 0.03 * e.smile) * hh * smoothstep(0.72, 1.0, u)
        y -= 0.02 * e.skew * hh * smoothstep(0.6, 1.0, max(0.0, t))
        if lower:
            y += 0.12 * e.open * hh * (1.0 - u) ** 0.85
        out.append((t * mw, y))
    return out


def _alligator_mouth(ctx: Ctx, pt: Paint, e: Expression) -> None:
    """The jaw line and the teeth. Shut, the upper teeth show along the jaw
    line (the lower ones fit inside the upper jaw); open, the mouth is a
    wedge from the hinge with teeth on both edges. Face paint puts red on the
    front of the jaw line."""
    fig = ctx.fig
    hd = fig.head
    hh = fig.hh
    up = [q for q in _jaw_line(fig, e, False) if ctx.view.facing(q[0]) > 0.04]
    lo = [q for q in _jaw_line(fig, e, True) if ctx.view.facing(q[0]) > 0.04]
    if len(up) < 2:
        return
    out = 0.06
    tooth = "#efe8d2"
    is_open = e.open > 0.06

    def teeth(line: List[Tuple[float, float]], down: float) -> None:
        # Small cones along the line, every other sample, pointing ``down``
        # (+1) or up (-1); none in the corners.
        for i in range(1, len(line) - 1, 1):
            a, y = line[i]
            if abs(a) > 0.86 * fig.face["mouth_alpha"] or not visible(ctx, a, 0.12):
                continue
            if i % 2:
                continue
            ln = 0.034 * hh * (1.0 - 0.35 * abs(a) / fig.face["mouth_alpha"])
            da = 2.6
            tri = [ctx.p(hd.point(a - da, y, out)), ctx.p(hd.point(a + da, y, out)), ctx.p(hd.point(a, y + down * ln, out + 0.004 * hh))]
            pt.region([tri], tooth, outline=FINE * 0.45)

    if is_open:
        poly = [ctx.p(hd.point(a, y, out)) for a, y in up] + [ctx.p(hd.point(a, y, out * 0.5)) for a, y in reversed(lo)]
        pt.region([poly], "#4a2422", outline=0.22, smooth=True)
        tongue = [ctx.p(hd.point(a * 0.7, y - 0.018 * hh, out * 0.5)) for a, y in lo if abs(a) < 0.6 * fig.face["mouth_alpha"]]
        if len(tongue) >= 2 and e.open > 0.3:
            pt.line(tongue, "#b8746a", 0.03 * hh, smooth=True, fixed=True)
        teeth(lo, -1.0)
    teeth(up, 1.0)
    line = [ctx.p(hd.point(a, y, out)) for a, y in up]
    pt.line(line, mix(style().ink, shade(ctx.skin, 0.5), 0.2), 0.42)
    if fig.spec.face.makeup == "geisha":
        # Red on the front of the jaw line, like painted lips.
        for edge in ((up, lo) if is_open else (up,)):
            front = [ctx.p(hd.point(a, y, out + 0.01)) for a, y in edge if abs(a) < 0.3 * fig.face["mouth_alpha"]]
            if len(front) >= 2:
                pt.line(front, PAINT_RED, 0.022 * hh, smooth=True)


def _eye_corners(ctx: Ctx, pt: Paint, eyes: Dict[float, Dict[str, object]]) -> None:
    """Face paint's red at the outer corner of each eye (mejiri)."""
    fig = ctx.fig
    for sgn, g in eyes.items():
        o = g["outer"]
        pts = [(o[0] - sgn * 1.5, o[1] - 0.2 * g["eh"]), (o[0] + sgn * 3.0, o[1] - 0.45 * g["eh"]), (o[0] + sgn * 7.0, o[1] - 0.5 * g["eh"])]
        for run in surface_line(ctx, fig.head, pts, out=0.07, thresh=0.2):
            pt.line(run, PAINT_RED, 0.32 * g["eh"], smooth=True)


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
    if fig.spec.face.makeup == "geisha":
        _eye_corners(ctx, fixed, neutral_eyes)
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
        blink.region([lid], face_skin(ctx), outline=0.12)
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
          "bowler": (0.24, 0.3), "brimmed": (0.23, 0.29), "campaign": (0.23, 0.29), "helmet": (0.22, 0.46), "beret": (0.2, 0.3),
          "garrison_cap": (0.17, 0.24), "peaked_cap": (0.24, 0.28)}
#: The military hats: drawn by ``_military_hat``.
_MILITARY = ("helmet", "beret", "garrison_cap", "peaked_cap")


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
    # A head whose eyes sit at its very top (an alligator's) wears the band
    # on the crown, not above it.
    lift = min(lift, max(0.0, front - 0.05))
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
            # The crown is flattened (less on a head that wears its band on the crown).
            flat = fig.face.get("hat_flat", 0.1) * hh
            shell = Loft([RingKey(kk.y + flat * max(0.0, 1 - (kk.y - fig.crown) / (0.3 * hh)), kk.rx * 1.05, kk.rzf * 1.18, kk.rzb * 0.98,
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
    elif hat in _MILITARY:
        _military_hat(ctx, pt, hat, col, t, band, lift)
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
        brim_w = {"brimmed": 0.34, "top_hat": 0.14, "bowler": 0.1, "campaign": 0.4}[hat] * hh
        rim = []
        for i in range(24):
            a = 2 * math.pi * i / 24
            rz = (rzf if math.cos(a) >= 0 else rzb) + brim_w
            rim.append(((rx + brim_w) * math.sin(a), yb, sec.cz + rz * math.cos(a)))
            rim.append(((rx + brim_w) * math.sin(a), yb - 0.35, sec.cz + rz * math.cos(a)))
        brim_poly = hull(ctx.p(q) for q in rim)
        # A head that rises above the crown (a sea lion's crest) raises the crown of the hat.
        height = {"brimmed": 0.36, "top_hat": 0.62, "bowler": 0.36, "campaign": 0.44}[hat] * hh + max(0.0, fig.crown - sk.top)
        bumps = []
        if hat == "campaign":
            # The crown rises to a peak with four dents (a pinch) round it.
            keys = [RingKey(yb, rx, rzf, rzb, 0.0, sec.cz, 2.0), RingKey(yb - height * 0.55, rx * 0.97, rzf * 0.97, rzb * 0.97, 0.0, sec.cz, 2.0),
                    RingKey(yb - height * 0.88, rx * 0.62, rzf * 0.62, rzb * 0.62, 0.0, sec.cz, 2.0),
                    RingKey(yb - height, 0.0, 0.0, 0.0, 0.0, sec.cz, 2.0)]

            def pinch(a: float, y: float, _y0=yb - 0.35 * height, _y1=yb - 0.9 * height, _d=0.075 * hh) -> float:
                return -_d * smoothstep(_y0, _y1, y) * (0.5 + 0.5 * math.cos(math.radians(4.0 * (a - 45.0)))) ** 2

            bumps.append(pinch)
        elif hat == "top_hat":
            keys = [RingKey(yb, rx, rzf, rzb, 0.0, sec.cz, 2.2), RingKey(yb - height, rx * 1.05, rzf * 1.05, rzb * 1.05, 0.0, sec.cz, 2.2),
                    RingKey(yb - height - 0.01, 0.0, 0.0, 0.0, 0.0, sec.cz, 2.2)]
        else:
            keys = [RingKey(yb, rx, rzf, rzb, 0.0, sec.cz, 2.0), RingKey(yb - height * 0.6, rx * 0.96, rzf * 0.96, rzb * 0.96, 0.0, sec.cz, 2.0),
                    RingKey(yb - height * 0.9, rx * 0.72, rzf * 0.72, rzb * 0.72, 0.0, sec.cz, 2.0), RingKey(yb - height, 0.0, 0.0, 0.0, 0.0, sec.cz, 2.0)]
        crown = Loft(keys, bumps)
        pt.region([brim_poly], col, smooth=True)
        pt.flat([brim_poly], shade(col, 0.08), smooth=True)
        shaded_region(ctx, pt, crown, crown.top, crown.bottom, col, lit=True, shade_cap=0.12 * hh)
        ribbon = {"top_hat": shade(col, 0.4), "campaign": shade(col, 0.45)}.get(hat, fig.spec.outfit.accent_color)
        pt.flat(loft_region(ctx.view, crown, yb - 0.11 * hh, yb - 0.01), ribbon)
        if hat == "campaign":
            # The pinch's four dents: a crease down the middle of each.
            for a0 in (45.0, 135.0, -45.0, -135.0):
                for run in surface_line(ctx, crown, [(a0, lerp(yb - 0.5 * height, yb - 0.86 * height, i / 4.0)) for i in range(5)], out=-0.03 * hh,
                                        thresh=0.2):
                    pt.line(run, shade(col, 0.3), FINE)
    return [Part(f"hat_{hat}", "head", 58.0, pt.els, f"Hat - {hat}", feature=feature)] if pt.els else []


def _cover(sk: Loft, y: float, t: float, rx: float, rzf: float, rzb: float, cl: float, cz: float, sq: float) -> RingKey:
    """A ring of a hat at ``y``: the given one, made at least as large as the
    skull there plus ``t`` all round, so the hat never cuts into the head."""
    if y < sk.top:
        return RingKey(y, rx, rzf, rzb, cl, cz, sq)
    sec = sk.section(y)
    return RingKey(y, max(rx, sec.rx + t + abs(cl)), max(rzf, sec.rzf + t + max(0.0, sec.cz - cz)), max(rzb, sec.rzb + t + max(0.0, cz - sec.cz)),
                   cl, cz, sq)


def _military_hat(ctx: Ctx, pt: Paint, hat: str, col: str, t: float, band: Callable[[float], float], lift: float) -> None:
    """A helmet, a beret, a garrison cap or a peaked cap, drawn from the
    skull loft (``t``: the hat's distance from the skull, over the hair). On a
    head that rises above the crown (a sea lion's crest) the top of the hat
    goes up with it."""
    from .spec import UNIFORM

    fig = ctx.fig
    hh = fig.hh
    sk = fig.skull
    rise = max(0.0, fig.crown - sk.top)
    # The widest ring of the skull above the jaw (above a long snout).
    widest = max(sk.keys, key=lambda kk: kk.rx if kk.y < fig.fy(fig.face.get("crown_f", 0.7)) else -1.0)

    def f_of(y: float) -> float:
        return (y - fig.crown) / hh

    if hat == "helmet":
        # A round steel shell: the skull, rounded out to a dome over its
        # top (a crest stays under a dome, not a ridge), and a little lip
        # all round its rim. The rim is low at the sides and back, over the
        # tops of the ears.
        tt = t + 0.075 * hh
        knots = [(0, 0.22 - lift), (50, 0.27 - lift), (95, 0.43 - lift), (140, 0.47 - lift), (180, 0.46 - lift)]

        def rim(a: float) -> float:
            return interp_knots(abs(wrap180(a)), knots)

        y_top = sk.top - tt
        y_mid = widest.y
        keys = [RingKey(y_top, 0.0, 0.0, 0.0, 0.0, widest.cz, 2.0)]
        for i in range(1, 9):
            y = lerp(y_top, y_mid, i / 8.0)
            u = (y_mid - y) / max(1e-6, y_mid - y_top)
            d = math.sqrt(max(0.0, 1.0 - u * u))
            keys.append(_cover(sk, y, tt, (widest.rx + tt) * d, (widest.rzf + tt) * d, (widest.rzb + tt) * d, 0.0, widest.cz, 2.0))
        for f in (0.55, 0.62):
            sec = sk.section(fig.fy(f))
            keys.append(RingKey(fig.fy(f), max(sec.rx, widest.rx) + tt, max(sec.rzf, widest.rzf) + tt, max(sec.rzb, widest.rzb) + tt, 0.0,
                                widest.cz, 2.0))
        shell = Loft(keys)
        cover = lambda a, y: rim(a) - f_of(y)  # noqa: E731
        shaded_region(ctx, pt, shell, shell.top, shell.bottom, col, cover, lit=True, shade_frac=0.26, shade_cap=0.12 * hh)
        lip = shell.shell(0.035 * hh)
        pt.region(loft_region(ctx.view, lip, lip.top, lip.bottom, all_of(cover, lambda a, y: f_of(y) - (rim(a) - 0.045))), shade(col, 0.12),
                  outline=FINE)
        # The chinstrap: from the rim at each side down the cheek and under the chin.
        hd = fig.head
        for sgn in (-1.0, 1.0):
            pts = [(sgn * 84.0, fig.fy(rim(84.0) - 0.01)), (sgn * 74.0, fig.fy(0.62)), (sgn * 58.0, fig.fy(0.82)), (sgn * 36.0, fig.fy(0.95)),
                   (sgn * 12.0, fig.fy(1.0)), (0.0, fig.fy(1.0))]
            dense = [(lerp(a0, a1, i / 4.0), lerp(y0, y1, i / 4.0)) for (a0, y0), (a1, y1) in zip(pts, pts[1:]) for i in range(4)] + [pts[-1]]
            for run in surface_line(ctx, hd, dense, out=0.25, thresh=0.05):
                pt.line(run, INK, 0.75)
                pt.line(run, "#4a4630", 0.42)
    elif hat == "beret":
        # A soft crown that flares out over a narrow band and is pulled down
        # over the right ear: the right side swells out and hangs lower. The
        # badge sits over the left eye.
        def edge(a: float) -> float:
            return band(a) + 0.09 * max(0.0, -math.sin(math.radians(a))) ** 1.5

        f_band = band(0.0)
        y_puff = fig.fy(f_band - 0.06) - rise * 0.5
        keys = [_cover(sk, fig.fy(0.5), t + 0.25, 0.0, 0.0, 0.0, 0.0, widest.cz, 2.0),
                _cover(sk, fig.fy(f_band + 0.02), t + 0.3, 0.0, 0.0, 0.0, 0.0, widest.cz, 2.0)]
        for y, k in ((y_puff, 1.2), (fig.fy(f_band - 0.13) - rise, 1.1), (fig.fy(f_band - 0.17) - rise, 0.72)):
            keys.append(_cover(sk, y, t + 0.4, widest.rx * k, widest.rzf * k * 0.98, widest.rzb * k * 0.95, 0.0, widest.cz, 2.2))
        y_top = min(keys[-1].y, sk.top - t) - 0.012 * hh
        keys.append(RingKey(y_top, 0.0, 0.0, 0.0, 0.0, widest.cz, 2.2))

        def droop(a: float, y: float, _y0=fig.fy(f_band + 0.12), _y1=y_puff, _hh=hh) -> float:
            return 0.1 * _hh * max(0.0, -math.sin(math.radians(a))) ** 1.5 * smoothstep(_y0, _y1, y)

        body = Loft(keys, [droop])
        cover = lambda a, y: edge(a) - f_of(y)  # noqa: E731
        shaded_region(ctx, pt, body, body.top, body.bottom, col, cover, lit=True, shade_frac=0.3, shade_cap=0.1 * hh)
        # The leather trim of the band.
        pt.flat(loft_region(ctx.view, body.shell(0.05), body.top, body.bottom, all_of(cover, lambda a, y: f_of(y) - (edge(a) - 0.03))),
                shade(col, 0.45))
        c = body.point(30.0, fig.fy(band(30.0) - 0.07), 0.15)
        insignia(ctx, pt, c, (math.sin(math.radians(30.0)), -0.2, math.cos(math.radians(30.0))), 0.075 * hh)
    elif hat == "garrison_cap":
        # A folded side cap: a narrow wedge on top of the head, long from
        # front to back, its two sides meeting in a ridge, worn a little
        # down on the right. The turned-up curtain round its lower part is a
        # darker band under a fold line.
        def edge(a: float) -> float:
            return band(a) + 0.035 * max(0.0, -math.sin(math.radians(a)))

        y0 = fig.fy(max(band(0.0), band(180.0)) + 0.06)
        sec = sk.section(fig.fy(band(0.0)))
        y_top = min(fig.fy(band(0.0) - 0.15), sk.top - 0.04 * hh) - 0.02 * hh
        keys = []
        for i in range(6):
            u = i / 5.0
            y = lerp(y0, y_top, u)
            ring = RingKey(y, (sec.rx + t) * lerp(1.0, 0.14, u ** 1.2), (sec.rzf + t) * lerp(1.0, 1.06, u), (sec.rzb + t) * lerp(1.0, 1.06, u),
                           -0.02 * hh * u, sec.cz, 2.6)
            if rise > 0.0 and y < fig.fy(0.1):
                # Over a crest the cap must still cover it.
                ring = _cover(sk, y, t * 0.5, ring.rx, ring.rzf, ring.rzb, ring.cl, ring.cz, ring.sq)
            keys.append(ring)
        cap = Loft(keys)
        cover = lambda a, y: edge(a) - f_of(y)  # noqa: E731
        shaded_region(ctx, pt, cap, cap.top, cap.bottom, col, cover, lit=True, shade_frac=0.3, shade_cap=0.08 * hh)
        y_fold = lerp(fig.fy(band(0.0)), y_top, 0.45)
        fold = lambda a, y: y - (y_fold + 0.025 * hh * math.sin(math.radians(abs(wrap180(a)))))  # noqa: E731
        pt.flat(loft_region(ctx.view, cap.shell(0.04), cap.top, cap.bottom, all_of(cover, fold)), shade(col, 0.14))
        line = [(a, y_fold + 0.025 * hh * math.sin(math.radians(abs(a)))) for a in range(-180, 181, 10)]
        for run in surface_line(ctx, cap, line, out=0.06, thresh=0.05):
            pt.line(run, shade(col, 0.5), FINE * 1.2)
    else:
        # An officer's service cap: a stiff band, a wide flat crown over it
        # that stands out at the front, a short black visor, a brass chin
        # cord and the badge on the crown's front.
        yb = fig.fy(band(0.0))
        sec = sk.section(yb)
        rx, rzf, rzb = sec.rx + t + 0.3, sec.rzf + t + 0.3, sec.rzb + t + 0.3
        y_bt = yb - 0.13 * hh - rise
        band_loft = Loft([RingKey(yb + 0.04 * hh, rx, rzf, rzb, 0.0, sec.cz, 2.1), RingKey(y_bt, rx * 1.01, rzf * 1.01, rzb * 1.01, 0.0, sec.cz, 2.1)])
        crown = Loft([RingKey(y_bt + 0.01 * hh, rx * 1.01, rzf * 1.01, rzb * 1.01, 0.0, sec.cz, 2.1),
                      RingKey(y_bt - 0.05 * hh, rx * 1.14, rzf * 1.3, rzb * 1.08, 0.0, sec.cz + 0.04 * hh, 2.3),
                      RingKey(y_bt - 0.085 * hh, rx * 1.1, rzf * 1.26, rzb * 1.05, 0.0, sec.cz + 0.04 * hh, 2.4),
                      RingKey(y_bt - 0.09 * hh, 0.0, 0.0, 0.0, 0.0, sec.cz + 0.04 * hh, 2.4)])
        visor_col = "#2a2622"
        pts3 = [band_loft.point(a, yb + 0.03 * hh, 0.0) for a in range(-75, 76, 10)]
        tip3 = [band_loft.point(a, yb + 0.03 * hh + 0.11 * hh * math.cos(math.radians(a)), 0.2 * hh * math.cos(math.radians(a)) ** 0.8)
                for a in range(-70, 71, 10)]
        visor = hull(ctx.p(q) for q in pts3 + tip3)
        visor_front = ctx.view.c > -0.2
        if not visor_front:
            pt.region([visor], visor_col, smooth=True)
        cover = lambda a, y: band(a) + 0.04 - f_of(y)  # noqa: E731
        shaded_region(ctx, pt, band_loft, band_loft.top, band_loft.bottom, shade(col, 0.3), cover, shade_frac=0.25, shade_cap=0.06 * hh)
        for run in surface_line(ctx, band_loft, [(a, yb - 0.035 * hh) for a in range(-80, 81, 10)], out=0.12, thresh=0.05):
            pt.line(run, INK, 0.7)
            pt.line(run, UNIFORM["brass"], 0.4)
        shaded_region(ctx, pt, crown, crown.top, crown.bottom, col, lit=True, shade_frac=0.22, shade_cap=0.08 * hh)
        insignia(ctx, pt, crown.point(0.0, y_bt - 0.035 * hh, 0.1), (0.0, -0.25, 1.0), 0.08 * hh)
        if visor_front:
            pt.region([visor], visor_col, smooth=True)
            pt.flat([hull(ctx.p(q) for q in pts3[3:-3] + tip3[3:-3])], light(visor_col, 0.12), smooth=True)


__all__ = ["coat_colors", "face_parts", "facial_hair_parts", "glasses_parts", "hair_parts", "hair_thickness", "hat_parts", "head_parts"]
