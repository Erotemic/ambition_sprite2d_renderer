"""The Dealer's Hand: a spectral hand that tosses the Quantum Dice, on the
haunted floors of Hylbert's Hotel (the Math dimension; Jon, 2026-10-31:
"a spectral hand that can toss the dice. As a different character, they
will be composed in gameplay").

A great ghostly hand with no arm, drifting: translucent pale fingers with
their bones glowing teal inside, a lace dealer's cuff at the wrist that
dissolves into mist. It drums its fingers while it waits. Its attack is the
TOSS: it cups a die and shakes it, then flings its fingers open and the die
is gone (the die is its own character, `quantum_die`, spawned at the
release: the hand shows only a glimpse of one in its grip, and the sparkle
where it leaves).

A PAPER DOLL, posed from one joint table (``Pose``) per frame: the PALM,
four FINGERS of three bones each and a THUMB of two, each joint turned by
its finger's curl; the CUFF and its mist; the DIE GLIMPSE; the RELEASE
sparkle; an aura and motes.

Two VIEWS (``Pose.view``): the PALM (front: its pads, its creases, the
thumb up, the nails hidden) for reaching and for the grasp that cups the
die, and the BACK (dorsal: its knuckles, tendons and nails, the thumb
down) for gliding and the toss's flung-open follow-through.

Rows: ``idle`` 8 (it floats, drumming its fingers), ``walk`` 8 (it glides,
fingers trailing), ``attack_side`` 12 (it cups and shakes (0-5), the toss:
fingers flung open, the release (6-8), held open after (9-11)), ``hurt`` 3
(its fingers splay), ``death`` 8 (it fades from the fingertips in, into
mist).

Facing right; it floats. No drop shadow.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image, ImageFilter

from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "dealers_hand"
FRAME_SIZE = (192, 168)
SUPER = 4
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 120),
    ("walk", 8, 110),
    ("attack_side", 12, 65),
    ("hurt", 3, 90),
    ("death", 8, 110),
]

OUTLINE: RGBA = (24, 16, 44, 255)
FLESH: RGBA = (226, 238, 248, 215)
FLESH_SHADE: RGBA = (150, 168, 210, 215)
BONE: RGBA = (150, 255, 230, 255)
TEAL: RGBA = (110, 240, 220, 255)
VIOLET: RGBA = (176, 120, 255, 255)
LACE: RGBA = (246, 250, 255, 235)
WHITE: RGBA = (250, 252, 255, 255)
NAIL: RGBA = (58, 24, 96, 255)
BRASS: RGBA = (214, 168, 84, 255)
SLEEVE: RGBA = (36, 22, 58, 255)
GARTER: RGBA = (150, 60, 140, 255)

#: THE ONE HAND every pose and both views are drawn from. Each finger: its
#: knuckle's place across the palm (frame px, from the palm's middle line),
#: its width and its three phalanges' lengths. Index, middle, ring, little.
FINGERS = [(-9.0, 5.6, (16.0, 11.0, 8.0)), (-3.0, 5.8, (17.5, 12.0, 8.5)), (3.0, 5.4, (16.0, 11.0, 8.0)), (8.5, 4.8, (12.5, 9.0, 7.0))]
#: The thumb: its metacarpal (inside the thumb's mound) and two phalanges.
THUMB = (9.0, 10.0, 8.0)
THUMB_WIDTH = 6.2
PALM_LENGTH = 26.0
#: How far each joint (knuckle, middle, end) bends at a full curl, degrees.
#: A curl folds the finger INTO DEPTH (toward us from the palm side, away
#: from the back), so its phalanges foreshorten and its tip comes back over
#: the palm; it never turns the finger in the picture plane.
JOINT_BEND = (70.0, 95.0, 70.0)
#: How much of a phalanx's depth shows as a drop down the frame (the hand is
#: seen a little from above).
DEPTH_TILT = 0.5


def _a(c: RGBA, a: float) -> RGBA:
    return (c[0], c[1], c[2], int(max(0.0, min(1.0, a)) * c[3]))


def _s(p: Point) -> Tuple[float, float]:
    return (p[0] * SUPER, p[1] * SUPER)


def _dir(deg: float) -> Point:
    a = math.radians(deg)
    return (math.cos(a), math.sin(a))


def _glow(layer: Image.Image, fn, blur: float) -> None:
    g = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    fn(blending_draw(g))
    layer.alpha_composite(g.filter(ImageFilter.GaussianBlur(blur * SUPER)))


@dataclass(frozen=True)
class Pose:
    """One frame: the wrist's place, the palm's direction (degrees, 0 its
    facing, negative up), each finger's curl (0 straight, 1 closed) and the
    thumb's, and the attack's state."""

    wrist: Point = (62.0, 98.0)
    palm: float = -12.0
    curls: Tuple[float, float, float, float] = (0.3, 0.3, 0.3, 0.3)
    thumb: float = 0.3
    die: float = 0.0
    release: float = -1.0
    glow: float = 0.7
    fade: float = 1.0
    tip_fade: float = 0.0
    #: Which side of the hand faces us: "palm" (front: its pads and creases,
    #: the thumb up) or "back" (dorsal: its knuckles, tendons and nails, the
    #: thumb down). The thumb and the order of the fingers mirror between
    #: them.
    view: str = "palm"


def _side(pose: "Pose") -> float:
    return 1.0 if pose.view == "palm" else -1.0


def _chain(pose: Pose, start: Point, axis: float, bones, curl: float, bends) -> Tuple[List[Point], List[float]]:
    """A digit's joints, from its base along ``axis`` (degrees), each joint
    folding by ``bends`` x ``curl`` into depth. Returns the joints and each
    phalanx's fold (degrees from lying flat along the axis)."""
    d = _dir(axis)
    pts, folds = [start], []
    theta = 0.0
    for bone, bend in zip(bones, bends):
        theta += bend * curl
        t = math.radians(theta)
        p = pts[-1]
        along = bone * math.cos(t)
        drop = bone * math.sin(t) * DEPTH_TILT
        pts.append((p[0] + d[0] * along, p[1] + d[1] * along + drop))
        folds.append(theta)
    return pts, folds


def _finger_chain(pose: Pose, k: int) -> Tuple[List[Point], List[float]]:
    across, _width, bones = FINGERS[k]
    across *= _side(pose)
    d = _dir(pose.palm)
    perp = (-d[1], d[0])
    knuckle = (pose.wrist[0] + d[0] * PALM_LENGTH + perp[0] * across, pose.wrist[1] + d[1] * PALM_LENGTH + perp[1] * across)
    return _chain(pose, knuckle, pose.palm + across * 1.2, bones, pose.curls[k], JOINT_BEND)


def _finger_points(pose: Pose, k: int) -> List[Point]:
    return _finger_chain(pose, k)[0]


def _thumb_chain(pose: Pose) -> Tuple[List[Point], List[float]]:
    """The THUMB, OPPOSED: from its root at the heel of the hand it angles
    well away from the fingers; curling swings it across the palm (in the
    picture plane, as a thumb opposes) and folds its end joint."""
    d = _dir(pose.palm)
    perp = (-d[1], d[0])
    side = _side(pose)
    base = (pose.wrist[0] + d[0] * 5 - perp[0] * 7 * side, pose.wrist[1] + d[1] * 5 - perp[1] * 7 * side)
    # Open, it spreads 58 degrees off the fingers; closed, it lies across them.
    axis = pose.palm - side * (58.0 - 52.0 * pose.thumb)
    return _chain(pose, base, axis, THUMB, pose.thumb, (10.0, 35.0, 55.0))


def _thumb_points(pose: Pose) -> List[Point]:
    return _thumb_chain(pose)[0]


# --- parts ------------------------------------------------------------------------


def draw_digit(layer: Image.Image, pts: List[Point], folds: List[float], width: float, pose: Pose, thumb: bool = False, only_first: bool = False) -> None:
    """A DIGIT, the same rigid parts in every pose and view: each PHALANX a
    separate translucent capsule outlined on its own, a HINGE disk at each
    joint, the bone glowing inside, a rounded FINGERTIP CAP lit teal.

    Which face of a phalanx shows follows from its fold: its PAD (creases,
    pads) when its palm side faces us, its BACK (knuckle highlight, the nail
    on the last one) when its back does. ``tip_fade`` eats it from the tip.
    From the palm a curl folds toward us (drawn base to tip, the tip on
    top); from the back it folds away (tip first, tucked behind).
    ``only_first`` redraws just the first phalanx (from the back, over the
    hand it hangs from)."""
    n = len(pts) - 1
    keep = max(0.0, n * (1.0 - pose.tip_fade))
    palm_view = pose.view == "palm"
    order = range(n) if palm_view else range(n - 1, -1, -1)
    if only_first:
        order = range(1)
    widths = [width * (1.0 - 0.1 * i) for i in range(n)]
    for i in order:
        if i >= keep:
            continue
        a, b = pts[i], pts[i + 1]
        frac = min(1.0, keep - i)
        b = (a[0] + (b[0] - a[0]) * frac, a[1] + (b[1] - a[1]) * frac)
        w = widths[i]
        # Its palm side faces us when it lies flat from the palm, or folds
        # past upright from the back.
        pad_side = (folds[i] < 90.0) == palm_view
        d = blending_draw(layer)
        fill = FLESH
        for colour, ww in ((_a(OUTLINE, pose.fade), w + 1.4), (_a(fill, pose.fade), w)):
            d.line([_s(a), _s(b)], fill=colour, width=int(ww * SUPER))
            for p in (a, b):
                r = ww * SUPER / 2
                d.ellipse((_s(p)[0] - r, _s(p)[1] - r, _s(p)[0] + r, _s(p)[1] + r), fill=colour)
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy)
        ux, uy = (dx / ln, dy / ln) if ln > 0.3 else _dir(pose.palm)
        half = w * 0.42
        bone_strength = 0.35 if pad_side else 1.0
        _glow(layer, lambda g, a=a, b=b, s=bone_strength: g.line([_s(a), _s(b)], fill=_a(BONE, 0.55 * pose.glow * pose.fade * s), width=int(1.8 * SUPER)), 0.8)
        d = blending_draw(layer)
        d.line([_s(a), _s(b)], fill=_a(BONE, 0.8 * pose.fade * bone_strength), width=int(0.6 * SUPER))
        m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        if pad_side and ln > 2.0:
            # The segment's PAD, a soft fuller highlight.
            r = half * 0.55
            d.ellipse((*_s((m[0] - r, m[1] - r)), *_s((m[0] + r, m[1] + r))), fill=(250, 252, 255, int(110 * pose.fade)))
        if i == n - 1 and frac >= 1.0 and not pad_side:
            # The NAIL, set INSIDE the rounded tip (never past it).
            q = (a[0] + dx * 0.62, a[1] + dy * 0.62)
            rl, rw = max(1.3, ln * 0.26), w * 0.26
            nail = [(q[0] + ux * rl * math.cos(t) - uy * rw * math.sin(t), q[1] + uy * rl * math.cos(t) + ux * rw * math.sin(t)) for t in np.linspace(0, math.tau, 14)]
            d.polygon([_s(p) for p in nail], fill=_a(NAIL, 0.9 * pose.fade), outline=_a(OUTLINE, pose.fade))
            d.line([_s((q[0] - ux * rl * 0.4 - uy * rw * 0.4, q[1] - uy * rl * 0.4 + ux * rw * 0.4)), _s((q[0] + ux * rl * 0.3 - uy * rw * 0.4, q[1] + uy * rl * 0.3 + ux * rw * 0.4))], fill=_a(VIOLET, 0.9 * pose.fade), width=int(0.5 * SUPER))
        # The HINGE at the segment's base joint (the knuckle's own is drawn
        # with the palm): a pivot disk, ringed.
        if i > 0:
            hinge_r = w * 0.3
            d.ellipse((*_s((a[0] - hinge_r, a[1] - hinge_r)), *_s((a[0] + hinge_r, a[1] + hinge_r))), fill=_a((196, 214, 240, 255), 0.9 * pose.fade), outline=_a((90, 110, 170, 255), pose.fade), width=max(1, int(0.4 * SUPER)))
            d.ellipse((*_s((a[0] - 0.8, a[1] - 0.8)), *_s((a[0] + 0.8, a[1] + 0.8))), fill=_a(BONE, 0.95 * pose.fade))
            if pad_side:
                # The CREASE across the joint, on the pad side.
                d.line([_s((a[0] - uy * half, a[1] + ux * half)), _s((a[0] - uy * hinge_r, a[1] + ux * hinge_r))], fill=(120, 136, 186, int(190 * pose.fade)), width=int(0.5 * SUPER))
                d.line([_s((a[0] + uy * hinge_r, a[1] - ux * hinge_r)), _s((a[0] + uy * half, a[1] - ux * half))], fill=(120, 136, 186, int(190 * pose.fade)), width=int(0.5 * SUPER))
    if keep >= n and not only_first:
        # The FINGERTIP CAP, the same in every view: a rounded glowing end.
        tip = pts[-1]
        _glow(layer, lambda g: g.ellipse((*_s((tip[0] - 2.4, tip[1] - 2.4)), *_s((tip[0] + 2.4, tip[1] + 2.4))), fill=_a(TEAL, 0.8 * pose.glow * pose.fade)), 1.0)
        r = widths[-1] * 0.28
        blending_draw(layer).ellipse((*_s((tip[0] - r, tip[1] - r)), *_s((tip[0] + r, tip[1] + r))), fill=_a((200, 255, 245, 255), 0.85 * pose.fade))


def draw_palm(layer: Image.Image, pose: Pose) -> None:
    """The PALM: a broad translucent plate from the wrist to the knuckles,
    shaded toward its heel, its metacarpal bones glowing inside."""
    d = _dir(pose.palm)
    perp = (-d[1], d[0])
    w = pose.wrist
    knuckles = [_finger_points(pose, k)[0] for k in range(4)]
    heel_a = (w[0] - perp[0] * 9, w[1] - perp[1] * 9)
    heel_b = (w[0] + perp[0] * 9, w[1] + perp[1] * 9)
    # The knuckle on the heel_a side first, whichever view, so the outline
    # never crosses itself.
    by_side = sorted(knuckles, key=lambda k: (k[0] - w[0]) * perp[0] + (k[1] - w[1]) * perp[1])
    lo, hi = by_side[0], by_side[-1]
    poly = [heel_a, (lo[0] - perp[0] * 3.5, lo[1] - perp[1] * 3.5), (hi[0] + perp[0] * 3.5, hi[1] + perp[1] * 3.5), heel_b]
    dr = blending_draw(layer)
    # The WEB from the thumb's root to the index knuckle (its mound, from
    # the palm), so the thumb grows out of the hand in both views.
    tpts = _thumb_points(pose)
    index = _finger_points(pose, 0)[0]
    web = [tpts[0], tpts[1], ((tpts[1][0] + index[0]) / 2, (tpts[1][1] + index[1]) / 2), index, w]
    dr.polygon([_s(p) for p in web], fill=_a(FLESH, pose.fade), outline=_a(OUTLINE, pose.fade))
    dr.polygon([_s(p) for p in poly], fill=_a(FLESH, pose.fade), outline=_a(OUTLINE, pose.fade))
    shade = [heel_a, (w[0] + d[0] * 10 - perp[0] * 9, w[1] + d[1] * 10 - perp[1] * 9), (w[0] + d[0] * 10 + perp[0] * 9, w[1] + d[1] * 10 + perp[1] * 9), heel_b]
    dr.polygon([_s(p) for p in shade], fill=_a(FLESH_SHADE, 0.6 * pose.fade))
    side = _side(pose)
    if pose.view == "palm":
        # The PADS of the palm: the thumb's mound, the mound opposite, a pad
        # under each knuckle.
        dr = blending_draw(layer)
        for (along, off, rx, ry, a) in ((9.0, -6.5 * side, 7.5, 5.5, 140), (13.0, 6.0 * side, 6.0, 4.5, 110)):
            q = (w[0] + d[0] * along + perp[0] * off, w[1] + d[1] * along + perp[1] * off)
            dr.ellipse((*_s((q[0] - rx, q[1] - ry)), *_s((q[0] + rx, q[1] + ry))), fill=(250, 252, 255, int(a * pose.fade)), outline=(150, 166, 206, int(120 * pose.fade)))
        for k in knuckles:
            q = (k[0] - d[0] * 3.2, k[1] - d[1] * 3.2)
            dr.ellipse((*_s((q[0] - 2.6, q[1] - 2.0)), *_s((q[0] + 2.6, q[1] + 2.0))), fill=(250, 252, 255, int(120 * pose.fade)))
    else:
        # The TENDONS of the back of the hand: one along each metacarpal,
        # each from its own place at the wrist to its own knuckle.
        dr = blending_draw(layer)
        for k in knuckles:
            across = (k[0] - w[0]) * perp[0] + (k[1] - w[1]) * perp[1]
            start = (w[0] + d[0] * 3 + perp[0] * across * 0.45, w[1] + d[1] * 3 + perp[1] * across * 0.45)
            dr.line([_s(start), _s(k)], fill=(250, 252, 255, int(170 * pose.fade)), width=int(1.4 * SUPER))
            dr.line([_s((start[0] + perp[0] * 0.8, start[1] + perp[1] * 0.8)), _s((k[0] + perp[0] * 0.8, k[1] + perp[1] * 0.8))], fill=(120, 140, 190, int(150 * pose.fade)), width=int(0.6 * SUPER))
    # Faint lines of the palm (its life line, its heart line), from the front.
    for t0, t1, off in (((0.25, 0.75, -4.0 * side), (0.45, 0.9, 3.5 * side)) if pose.view == "palm" else ()):
        pa = (w[0] + d[0] * PALM_LENGTH * t0 + perp[0] * off, w[1] + d[1] * PALM_LENGTH * t0 + perp[1] * off)
        pm = (w[0] + d[0] * PALM_LENGTH * (t0 + t1) / 2 + perp[0] * (off + 2), w[1] + d[1] * PALM_LENGTH * (t0 + t1) / 2 + perp[1] * (off + 2))
        pb = (w[0] + d[0] * PALM_LENGTH * t1 + perp[0] * off * 0.5, w[1] + d[1] * PALM_LENGTH * t1 + perp[1] * off * 0.5)
        blending_draw(layer).line([_s(pa), _s(pm), _s(pb)], fill=(120, 140, 190, int(120 * pose.fade)), width=int(0.5 * SUPER), joint="curve")
    for k in knuckles:
        start = (w[0] + (k[0] - w[0]) * 0.18, w[1] + (k[1] - w[1]) * 0.18)
        strength = 0.3 if pose.view == "palm" else 0.9
        _glow(layer, lambda g, start=start, k=k: g.line([_s(start), _s(k)], fill=_a(BONE, 0.5 * pose.glow * pose.fade * strength), width=int(1.6 * SUPER)), 0.8)
        blending_draw(layer).line([_s(start), _s(k)], fill=_a(BONE, 0.75 * pose.fade * strength), width=int(0.6 * SUPER))


def draw_knuckles(layer: Image.Image, pose: Pose) -> None:
    """The KNUCKLE ROW: from the palm each knuckle a pivot disk under its
    finger's root; from the back a raised bump, the more prominent the more
    the fingers curl (the fist's ridge)."""
    d = blending_draw(layer)
    for k in range(4):
        pts, _folds = _finger_chain(pose, k)
        q = pts[0]
        width = FINGERS[k][1]
        if pose.view == "back":
            r = width * (0.5 + 0.22 * pose.curls[k])
            d.ellipse((*_s((q[0] - r, q[1] - r * 0.85)), *_s((q[0] + r, q[1] + r * 0.85))), fill=_a(FLESH, pose.fade), outline=_a(OUTLINE, pose.fade), width=max(1, int(0.5 * SUPER)))
            hr = r * 0.55
            d.ellipse((*_s((q[0] - hr - 0.6, q[1] - hr - 0.9)), *_s((q[0] + hr - 0.6, q[1] + hr * 0.4 - 0.9))), fill=(250, 252, 255, int(170 * pose.fade)))
        r = width * 0.3
        d.ellipse((*_s((q[0] - r, q[1] - r)), *_s((q[0] + r, q[1] + r))), outline=_a((90, 110, 170, 255), pose.fade), width=max(1, int(0.4 * SUPER)))
        d.ellipse((*_s((q[0] - 0.9, q[1] - 0.9)), *_s((q[0] + 0.9, q[1] + 0.9))), fill=_a(BONE, 0.95 * pose.fade))


def draw_cuff(layer: Image.Image, pose: Pose, phase: float) -> None:
    """The CUFF: a lace dealer's cuff at the wrist, scalloped, a cufflink of
    a die's pip on it; behind it the hand dissolves into trailing mist."""
    d = _dir(pose.palm)
    perp = (-d[1], d[0])
    w = pose.wrist

    def mist(g):
        for k in range(4):
            pts = []
            for j in range(9):
                t = j / 8.0
                x = w[0] - d[0] * (6 + 30 * t) + perp[0] * ((k - 1.5) * 4) + 3 * math.sin(phase + j * 0.7 + k)
                y = w[1] - d[1] * (6 + 30 * t) + perp[1] * ((k - 1.5) * 4) + 6 * t
                pts.append(_s((x, y)))
            g.line(pts, fill=_a((190, 230, 240, 255), 0.35 * pose.fade), width=int(5 * SUPER), joint="curve")

    _glow(layer, mist, 2.6)
    # The SLEEVE: a short stub of a dealer's dark sleeve behind the cuff,
    # its striped GARTER band, fading back into the mist.
    sl_a = (w[0] - d[0] * 8 - perp[0] * 10, w[1] - d[1] * 8 - perp[1] * 10)
    sl_b = (w[0] - d[0] * 8 + perp[0] * 10, w[1] - d[1] * 8 + perp[1] * 10)
    sleeve = [sl_a, sl_b, (sl_b[0] - d[0] * 16, sl_b[1] - d[1] * 16 + 3), (sl_a[0] - d[0] * 16, sl_a[1] - d[1] * 16 + 3)]
    dr0 = blending_draw(layer)
    dr0.polygon([_s(p) for p in sleeve], fill=_a(SLEEVE, 0.9 * pose.fade), outline=_a(OUTLINE, pose.fade))
    g_a = (sl_a[0] - d[0] * 9, sl_a[1] - d[1] * 9 + 1.5)
    g_b = (sl_b[0] - d[0] * 9, sl_b[1] - d[1] * 9 + 1.5)
    dr0.line([_s(g_a), _s(g_b)], fill=_a(GARTER, pose.fade), width=int(3.0 * SUPER))
    dr0.line([_s(g_a), _s(g_b)], fill=_a((230, 150, 220, 255), 0.8 * pose.fade), width=int(0.6 * SUPER))
    cuff_c = (w[0] - d[0] * 3, w[1] - d[1] * 3)
    a = (cuff_c[0] - perp[0] * 11, cuff_c[1] - perp[1] * 11)
    b = (cuff_c[0] + perp[0] * 11, cuff_c[1] + perp[1] * 11)
    back = 6.0
    band = [a, b, (b[0] - d[0] * back, b[1] - d[1] * back), (a[0] - d[0] * back, a[1] - d[1] * back)]
    dr = blending_draw(layer)
    dr.polygon([_s(p) for p in band], fill=_a(LACE, pose.fade), outline=_a(OUTLINE, pose.fade))
    for k in range(6):  # its scalloped lace edge
        t = (k + 0.5) / 6
        m = (a[0] + (b[0] - a[0]) * t + d[0] * 1.2, a[1] + (b[1] - a[1]) * t + d[1] * 1.2)
        dr.ellipse((*_s((m[0] - 1.9, m[1] - 1.9)), *_s((m[0] + 1.9, m[1] + 1.9))), fill=_a(LACE, pose.fade), outline=(160, 176, 210, int(180 * pose.fade)))
    link = (cuff_c[0] - d[0] * 3, cuff_c[1] - d[1] * 3)
    dr.rectangle((*_s((link[0] - 2.2, link[1] - 2.2)), *_s((link[0] + 2.2, link[1] + 2.2))), fill=_a(VIOLET, pose.fade), outline=_a(OUTLINE, pose.fade))
    dr.ellipse((*_s((link[0] - 0.7, link[1] - 0.7)), *_s((link[0] + 0.7, link[1] + 0.7))), fill=_a(WHITE, pose.fade))


def draw_die_glimpse(layer: Image.Image, pose: Pose, phase: float) -> None:
    """The DIE GLIMPSE: a glowing violet die caught in its cupped fingers,
    rattling as it shakes (the Quantum Die it will throw)."""
    if pose.die <= 0:
        return
    tips = [_finger_points(pose, k)[2] for k in range(4)]
    c = (sum(p[0] for p in tips) / 4 - 4, sum(p[1] for p in tips) / 4 + 6)
    # A tumbling miniature of the Quantum Die itself (its own drawing).
    from .quantum_die import _rotation, draw_cube

    _glow(layer, lambda g: g.ellipse((*_s((c[0] - 9, c[1] - 9)), *_s((c[0] + 9, c[1] + 9))), fill=_a(VIOLET, 0.6 * pose.die)), 2.0)
    draw_cube(layer, c, _rotation(phase * 1.7, -0.5 + 0.3 * math.sin(phase * 2), phase * 0.9), 5.6, pose.die, 1.0)


def draw_release(layer: Image.Image, pose: Pose) -> None:
    """The RELEASE: a sparkle where the die leaves the fingertips, streaks
    flung forward."""
    if pose.release < 0:
        return
    u = pose.release
    tip = _finger_points(pose, 1)[-1]
    fade = 1.0 - u

    def spark(g):
        for k in range(6):
            a = math.radians(-60 + k * 22)
            p0 = (tip[0] + math.cos(a) * (3 + 10 * u), tip[1] + math.sin(a) * (3 + 10 * u))
            p1 = (tip[0] + math.cos(a) * (8 + 22 * u), tip[1] + math.sin(a) * (8 + 22 * u))
            g.line([_s(p0), _s(p1)], fill=_a(TEAL, fade), width=int(1.4 * SUPER))
        g.ellipse((*_s((tip[0] - 5 * fade, tip[1] - 5 * fade)), *_s((tip[0] + 5 * fade, tip[1] + 5 * fade))), fill=_a(WHITE, fade))

    _glow(layer, spark, 1.6)
    spark(blending_draw(layer))


def draw_ring(layer: Image.Image, pose: Pose) -> None:
    """A brass SIGNET RING on the ring finger's first bone, a die pip of a
    violet gem set in it."""
    if pose.tip_fade > 0.6:
        return
    pts = _finger_points(pose, 2)
    a, b = pts[0], pts[1]
    m = (a[0] + (b[0] - a[0]) * 0.55, a[1] + (b[1] - a[1]) * 0.55)
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy) or 1.0
    px, py = -dy / ln * 3.2, dx / ln * 3.2
    if ln < 2.0:  # its phalanx folded end-on: the ring shows as a hoop
        px, py = 3.2, 0.0
    d = blending_draw(layer)
    d.line([_s((m[0] - px, m[1] - py)), _s((m[0] + px, m[1] + py))], fill=_a(OUTLINE, pose.fade), width=int(2.6 * SUPER))
    d.line([_s((m[0] - px, m[1] - py)), _s((m[0] + px, m[1] + py))], fill=_a(BRASS, pose.fade), width=int(1.6 * SUPER))
    if pose.view == "palm":
        return  # the signet's face is on the back of the finger
    gem = (m[0] - px * 0.9, m[1] - py * 0.9)
    _glow(layer, lambda g: g.ellipse((*_s((gem[0] - 2, gem[1] - 2)), *_s((gem[0] + 2, gem[1] + 2))), fill=_a(VIOLET, 0.9 * pose.fade)), 0.8)
    d = blending_draw(layer)
    d.ellipse((*_s((gem[0] - 1.1, gem[1] - 1.1)), *_s((gem[0] + 1.1, gem[1] + 1.1))), fill=_a(VIOLET, pose.fade), outline=_a(OUTLINE, pose.fade))


def shade_hand(img: Image.Image, pose: Pose) -> Image.Image:
    """SHADING over the drawn hand: lit from the upper left, shadowed toward
    the palm's underside, a teal RIM LIGHT along its upper edges. Alpha is
    kept."""
    px = np.asarray(img, np.float32)
    h, w = px.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    rel = (ys / SUPER - (pose.wrist[1] - 30.0)) / 50.0
    light = np.clip(1.12 - 0.42 * rel - 0.06 * (xs / SUPER - pose.wrist[0]) / 60.0, 0.6, 1.15)
    rgb = px[..., :3] * light[..., None]
    a = px[..., 3] / 255.0
    e = int(1.4 * SUPER)
    above = np.roll(a, e, axis=0)
    rim = np.clip(a - above, 0, 1) * (a > 0.5)
    rim = np.asarray(Image.fromarray((rim * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6 * SUPER)), np.float32) / 255.0
    rgb = rgb + rim[..., None] * np.array(TEAL[:3], np.float32) * 0.7
    px[..., :3] = np.clip(rgb, 0, 255)
    return Image.fromarray(px.astype(np.uint8), "RGBA")


def draw_shake_arcs(layer: Image.Image, pose: Pose) -> None:
    """SHAKE ARCS: quick curved lines either side of the cupped hand while it
    rattles the die."""
    if pose.die <= 0:
        return
    tips = [_finger_points(pose, k)[2] for k in range(4)]
    c = (sum(p[0] for p in tips) / 4, sum(p[1] for p in tips) / 4)

    def arcs(g):
        for sx, a0, a1 in ((-1, 120, 240), (1, -60, 60)):
            for r in (16.0, 21.0):
                g.arc((*_s((c[0] - r, c[1] - r)), *_s((c[0] + r, c[1] + r))), a0 + 30, a1 - 30, fill=_a(WHITE, 0.55 * pose.die), width=int(0.9 * SUPER))

    _glow(layer, arcs, 0.6)
    arcs(blending_draw(layer))


# --- assembly ---------------------------------------------------------------------


def draw_hand(pose: Pose, phase: float) -> Image.Image:
    img = Image.new("RGBA", (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER), (0, 0, 0, 0))
    w = pose.wrist
    _glow(img, lambda g: g.ellipse((*_s((w[0] - 20, w[1] - 46)), *_s((w[0] + 66, w[1] + 22))), fill=_a(TEAL, 0.16 * pose.fade)), 10.0)
    draw_cuff(img, pose, phase)
    fingers = [(_finger_chain(pose, k), FINGERS[k][1]) for k in range(4)]
    thumb = _thumb_chain(pose)
    if pose.view == "palm":
        # From the palm: the palm, the die in its cup, the fingers folding
        # toward us over it (little to index), the thumb across them.
        draw_palm(img, pose)
        draw_knuckles(img, pose)
        draw_die_glimpse(img, pose, phase)
        for (pts, folds), width in reversed(fingers):
            draw_digit(img, pts, folds, width, pose)
        draw_digit(img, *thumb, THUMB_WIDTH, pose, thumb=True)
    else:
        # From the back: the thumb on the far edge, the fingers folding away
        # behind the knuckle row, then the back of the hand over them.
        draw_digit(img, *thumb, THUMB_WIDTH, pose, thumb=True)
        for (pts, folds), width in fingers:
            draw_digit(img, pts, folds, width, pose)
        draw_palm(img, pose)
        for (pts, folds), width in fingers:
            draw_digit(img, pts, folds, width, pose, only_first=True)
        draw_knuckles(img, pose)
        draw_die_glimpse(img, pose, phase)
    draw_ring(img, pose)
    img = shade_hand(img, pose)
    draw_shake_arcs(img, pose)
    draw_release(img, pose)
    rng = np.random.default_rng(6)
    d = blending_draw(img)
    for _ in range(9):
        x, y, ph = w[0] - 20 + rng.random() * 80, w[1] - 50 + rng.random() * 70, rng.random()
        yy = y - ((phase / math.tau + ph) % 1.0) * 14
        d.ellipse((*_s((x - 0.8, yy - 0.8)), *_s((x + 0.8, yy + 0.8))), fill=_a(WHITE, 0.6 * pose.fade))
    return img


def _pose_for(animation: str, i: int, n: int) -> Tuple[Pose, float]:
    t = i / max(1, n)
    u = i / max(1, n - 1)
    w = math.sin(t * math.tau)
    # It drums: each finger taps on its own beat.
    drum = tuple(0.25 + 0.2 * max(0.0, math.sin(t * math.tau * 2 - k * 0.9)) for k in range(4))
    base = Pose(wrist=(62.0, 98.0 + 3 * w), palm=-12.0 + 3 * w, curls=drum, thumb=0.3 + 0.1 * w)
    if animation == "idle":
        return base, t * math.tau
    if animation == "walk":
        return replace(base, palm=-4.0 + 3 * w, curls=(0.15, 0.18, 0.22, 0.26), wrist=(62.0 + 2 * w, 98.0), view="back"), t * math.tau * 1.5
    if animation == "attack_side":
        if i <= 5:  # it cups the die and shakes it
            shake = 4.0 * math.sin(i * 2.6)
            return replace(base, curls=(0.95, 0.95, 0.95, 0.95), thumb=0.95, palm=-28.0, wrist=(60.0, 100.0 + shake), die=1.0, glow=0.8 + 0.2 * (i % 2)), t * math.tau * 3
        if i <= 8:  # the toss: fingers flung open, up and forward
            k = (i - 6) / 2.0
            return replace(base, curls=(0.95 - 1.05 * min(1.0, k * 1.8),) * 4, thumb=0.95 - 1.0 * min(1.0, k * 1.8), palm=-28.0 - 22.0 * k,
                           wrist=(60.0 + 10 * k, 100.0 - 6 * k), release=k, glow=1.0, view="back"), t * math.tau
        k = (i - 9) / 2.0  # held open after, slowly settling
        return replace(base, curls=(-0.1 + 0.3 * k,) * 4, thumb=-0.05 + 0.3 * k, palm=-50.0 + 36.0 * k, wrist=(70.0 - 8 * k, 94.0 + 4 * k), glow=0.5 + 0.2 * k, view="back"), t * math.tau
    if animation == "hurt":
        k = 1.0 - u
        return replace(base, curls=(-0.25 * k,) * 4, thumb=-0.2 * k, palm=-12.0 + 18 * k, wrist=(58.0 - 4 * k, 98.0), glow=1.0), t * math.tau
    if animation == "death":
        return replace(base, tip_fade=u, fade=1.0 - max(0.0, (u - 0.5) / 0.5), curls=(0.5 + 0.3 * u,) * 4, glow=1.0 - u * 0.5), t * math.tau
    raise ValueError(f"{TARGET_NAME}: no row {animation!r}")


def _render_frame(animation: str, frame_index: int, nframes: int) -> Image.Image:
    pose, phase = _pose_for(animation, frame_index, nframes)
    return draw_hand(pose, phase).resize(FRAME_SIZE, Image.Resampling.LANCZOS)


ACTOR_METADATA = {
    "actor": {"character_id": TARGET_NAME, "display_name": "Dealer's Hand"},
    "body": {
        "body_plan": "Amorphous",
        "body_kind": "Entity",
        "mass_class": "Light",
        "traits": ["spectral", "hand", "math", "floating"],
        "locomotion_hint": "Float",
    },
    "visual": {"default_pose": "idle", "portrait": {"animation": "idle", "frame": 0}},
    "tags": ["math", "spectral", "enemy", "hylberts_hotel"],
    "animation_bindings": {"default": {"animation": "idle", "events": []}},
}


def render(out_dir: str | Path, **opts) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=_render_frame,
        out_dir=out_dir,
        frame_size=opts.get("frame_size", FRAME_SIZE),
        auto_crop=False,
        actor_metadata=ACTOR_METADATA,
        animation_key_map={name: name for name, _frames, _duration in ROWS},
    )
    return [outputs[k] for k in ("spritesheet", "yaml", "ron", "actor", "preview", "canonical", "canonical_transparent")]


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
