"""The Gram Reaper: the boss of the haunted floors of Hylbert's Hotel (the
Math dimension). Jon, 2026-10-31, with a concept sheet: a hooded spectral
executioner that severs connections in an inner-product space, a grim
reaper for graphs. A tattered, asymmetrical violet cloak, eyes glowing in
the dark of its hood, a great scythe inscribed with geometry, and a
CONSTELLATION of luminous graph nodes and edges floating round it.

A PAPER DOLL: every part is its own drawing, posed from one joint table
(``Pose``) per frame. Back to front: the CONSTELLATION's far edges, the
CLOAK RIBBONS, the FAR ARM, the ROBE (with its Gram-matrix emblem), the
SHOULDER FLAPS, the HOOD with its EYES, the SCYTHE (shaft, orb, blade), the
NEAR ARM and its bony HAND on the shaft, the constellation's nodes, then the
effects: the GRAPH-CUT SLASH (an arc that severs the constellation's edges,
an edge-cut burst where it ends), the ORTHOGONAL DOUBLE-SLASH (a sweep, then
a cut square to it, a right-angle mark where they cross), and the
telegraphs (the eyes flare, a dashed projection to its target).

Rows (Hollow Knight rhythm: telegraph, commit, punishable recovery):
``idle`` 8 (it hovers, the graph turns); ``walk`` 8 (a stalking glide);
``attack_side`` 16, the graph-cut slash (telegraph 0-5: the scythe raised
back, eyes and nodes flare; commit 6-9: the sweep, edges severed; recovery
10-15: the blade down, the reaper open); ``ortho_slash`` 16, the
Gram-Schmidt double-slash (telegraph 0-5: a dashed projection drawn to its
mark; commit 6-10: the sweep, then the cut square to it; recovery 11-15);
``vanish`` 8 (it dissolves into its constellation and reforms); ``hurt`` 3;
``death`` 12 (the constellation breaks apart, the reaper fades into it).

Facing right; it floats, the hem of its robe near the canvas foot. No drop
shadow.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "gram_reaper"
FRAME_SIZE = (288, 288)
SUPER = 4
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 120),
    ("walk", 8, 110),
    ("attack_side", 16, 60),
    ("ortho_slash", 16, 60),
    ("vanish", 8, 80),
    ("hurt", 3, 90),
    ("death", 12, 110),
]

OUTLINE: RGBA = (16, 8, 30, 255)
VOID: RGBA = (6, 2, 14, 255)
CLOAK: RGBA = (84, 50, 146, 255)
CLOAK_DARK: RGBA = (48, 28, 92, 255)
CLOAK_LIGHT: RGBA = (138, 100, 206, 255)
TRIM: RGBA = (196, 168, 246, 255)
GLOW: RGBA = (176, 128, 255, 255)
NODE: RGBA = (236, 224, 255, 255)
EYE: RGBA = (226, 186, 255, 255)
BONE: RGBA = (222, 216, 236, 255)
METAL: RGBA = (120, 108, 150, 255)
METAL_DARK: RGBA = (66, 56, 92, 255)

#: The constellation: its nodes (offsets from the body, frame pixels) and
#: its edges.
NODES: List[Point] = [(-62, -62), (-38, -84), (-70, -18), (-44, -36), (-58, 20), (52, -78), (70, -50), (48, -36), (66, -4)]
EDGES: List[Tuple[int, int]] = [(0, 1), (0, 3), (1, 3), (0, 2), (2, 3), (2, 4), (3, 4), (5, 6), (6, 7), (5, 7), (7, 8), (6, 8)]


def _a(c: RGBA, a: float) -> RGBA:
    return (c[0], c[1], c[2], int(max(0.0, min(1.0, a)) * c[3]))


def _s(p: Point) -> Tuple[float, float]:
    return (p[0] * SUPER, p[1] * SUPER)


def _rot(p: Point, deg: float) -> Point:
    a = math.radians(deg)
    return (p[0] * math.cos(a) - p[1] * math.sin(a), p[0] * math.sin(a) + p[1] * math.cos(a))


def _add(a: Point, b: Point) -> Point:
    return (a[0] + b[0], a[1] + b[1])


def _along(p: Point, deg: float, length: float) -> Point:
    """``length`` from ``p`` at ``deg`` degrees from straight DOWN, positive
    toward its facing."""
    a = math.radians(deg)
    return (p[0] + math.sin(a) * length, p[1] + math.cos(a) * length)


def _glow(layer: Image.Image, fn, blur: float) -> None:
    g = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    fn(blending_draw(g))
    layer.alpha_composite(g.filter(ImageFilter.GaussianBlur(blur * SUPER)))


_GRID = {}


def _grid(size: Tuple[int, int]):
    if size not in _GRID:
        ys, xs = np.mgrid[0 : size[1], 0 : size[0]].astype(np.float32)
        _GRID[size] = (xs / SUPER, ys / SUPER)
    return _GRID[size]


def _mask(size: Tuple[int, int], pts: List[Point]) -> np.ndarray:
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).polygon([_s(p) for p in pts], fill=255)  # raw-draw-ok: an L mask has no alpha to composite
    return np.asarray(m, np.float32) / 255.0


def _fill_gradient(layer: Image.Image, pts: List[Point], c0: RGBA, c1: RGBA, p0: Point, p1: Point, alpha: float = 1.0) -> None:
    """Fill a polygon with a linear GRADIENT from ``c0`` at ``p0`` to ``c1``
    at ``p1`` (the shading of cloth and steel)."""
    xs, ys = _grid(layer.size)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    t = np.clip(((xs - p0[0]) * dx + (ys - p0[1]) * dy) / max(1e-6, dx * dx + dy * dy), 0.0, 1.0)[..., None]
    rgb = np.asarray(c0[:3], np.float32) * (1 - t) + np.asarray(c1[:3], np.float32) * t
    a = _mask(layer.size, pts) * alpha * 255.0
    layer.alpha_composite(Image.fromarray(np.dstack([rgb, a]).astype(np.uint8), "RGBA"))


def _fade_below(layer: Image.Image, y0: float, y1: float, floor: float = 0.0) -> None:
    """Fade a layer's alpha out from ``y0`` down to ``y1`` (to ``floor``):
    cloth dissolving into mist."""
    _, ys = _grid(layer.size)
    k = np.clip(1.0 - (ys - y0) / max(1e-6, y1 - y0), floor, 1.0)
    a = np.asarray(layer.getchannel("A"), np.float32) * k
    layer.putalpha(Image.fromarray(a.astype(np.uint8)))


def _light_pass(img: Image.Image, lights: List[Tuple[Point, float, RGBA, float]]) -> None:
    """POINT LIGHTS on what is drawn: each (position, radius, colour,
    strength) brightens and tints the pixels near it (the orb lights the
    blade and the cowl, the eyes the hood's dark). Alpha is kept."""
    px = np.asarray(img, np.float32)
    xs, ys = _grid(img.size)
    add = np.zeros(px.shape[:2] + (3,), np.float32)
    for (lx, ly), r, colour, k in lights:
        f = np.exp(-((xs - lx) ** 2 + (ys - ly) ** 2) / (r * r)) * k
        add += f[..., None] * np.asarray(colour[:3], np.float32)
    px[..., :3] = np.clip(px[..., :3] + add * (px[..., 3:] / 255.0), 0, 255)
    img.paste(Image.fromarray(px.astype(np.uint8), "RGBA"))


@dataclass(frozen=True)
class Pose:
    """One frame's joint table (frame pixels; arm angles in degrees from
    straight down, positive forward; the scythe's from straight UP)."""

    centre: Point = (132.0, 160.0)
    lean: float = 8.0
    hood_tilt: float = 0.0
    near_arm: Tuple[float, float] = (40.0, 60.0)
    far_arm: Tuple[float, float] = (-10.0, 30.0)
    scythe: float = 10.0
    cloak_phase: float = 0.0
    cloak_back: float = 0.0
    eye_glow: float = 0.7
    graph_rot: float = 0.0
    graph_spread: float = 1.0
    graph_cut: float = 0.0
    cut_slash: float = -1.0
    ortho_sweep: float = -1.0
    ortho_cut: float = -1.0
    projection: float = 0.0
    fade: float = 1.0


def _shoulder(pose: Pose) -> Point:
    return _add(pose.centre, _rot((0.0, -40.0), pose.lean))


# --- parts ------------------------------------------------------------------------


def draw_constellation(layer: Image.Image, pose: Pose, edges_only: bool) -> None:
    """The GRAPH CONSTELLATION: luminous nodes and the edges between them,
    turning slowly about the reaper. A graph cut severs the edges it crosses:
    each splits at its middle, its halves pulled apart."""
    c = pose.centre
    pts = [_add(c, _rot((x * pose.graph_spread, y * pose.graph_spread), pose.graph_rot)) for x, y in NODES]
    if edges_only:
        def edges(g):
            for k, (i, j) in enumerate(EDGES):
                a, b = pts[i], pts[j]
                cut = pose.graph_cut if k % 3 == 1 else 0.0
                if cut <= 0:
                    g.line([_s(a), _s(b)], fill=_a(GLOW, 0.7 * pose.fade), width=int(1.4 * SUPER))
                    continue
                mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                for end in (a, b):
                    q = (mid[0] + (end[0] - mid[0]) * 0.15 * cut, mid[1] + (end[1] - mid[1]) * 0.15 * cut)
                    g.line([_s(end), _s(q)], fill=_a(GLOW, 0.7 * pose.fade), width=int(1.4 * SUPER))
        _glow(layer, edges, 1.0)
        edges(blending_draw(layer))
        return
    d = blending_draw(layer)
    for k, p in enumerate(pts):
        r = 2.6 if k % 4 == 0 else 1.9
        _glow(layer, lambda g, p=p, r=r: g.ellipse((*_s((p[0] - r * 2, p[1] - r * 2)), *_s((p[0] + r * 2, p[1] + r * 2))), fill=_a(GLOW, 0.8 * pose.fade)), 1.4)
        d.ellipse((*_s((p[0] - r, p[1] - r)), *_s((p[0] + r, p[1] + r))), fill=_a(NODE, pose.fade))
        if k % 4 == 0:  # the brightest nodes flare
            for q0, q1 in (((p[0] - 6, p[1]), (p[0] + 6, p[1])), ((p[0], p[1] - 6), (p[0], p[1] + 6))):
                d.line([_s(q0), _s(q1)], fill=_a(NODE, 0.5 * pose.fade), width=int(0.6 * SUPER))


def draw_cloak_ribbons(layer: Image.Image, pose: Pose) -> None:
    """CLOAK RIBBONS: tattered strips of cloth trailing back from its
    shoulders and hem, rippling (the asymmetry of its silhouette)."""
    sh = _shoulder(pose)
    d = blending_draw(layer)
    for k, (start, length, width) in enumerate(((sh, 96.0, 26.0), (_add(pose.centre, (-14, 6)), 84.0, 24.0), (_add(pose.centre, (-8, 36)), 70.0, 16.0))):
        top, bottom = [], []
        for j in range(12):
            t = j / 11.0
            x = start[0] - length * t * (0.8 + 0.4 * pose.cloak_back)
            y = start[1] + length * t * (0.5 - 0.3 * pose.cloak_back) + 6.0 * math.sin(t * 5 + pose.cloak_phase + k)
            w = width * (1.0 - t * 0.7)
            top.append((x, y - w / 2))
            bottom.append((x + 2, y + w / 2 + (3 if j % 2 else 0)))
        poly = top + bottom[::-1]
        ribbon = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        _fill_gradient(ribbon, poly, (120, 84, 198, 255) if k == 0 else (86, 56, 156, 255), (40, 20, 84, 255), start, poly[len(top) - 1])
        blending_draw(ribbon).line([_s(p) for p in top], fill=(170, 136, 236, 120), width=int(0.8 * SUPER), joint="curve")
        # Its far end frays into nothing.
        far = poly[len(top) - 1]
        xs, _ = _grid(layer.size)
        fray = np.clip((xs - far[0]) / max(1e-6, start[0] - far[0]) * 3.0, 0.0, 1.0)
        ribbon.putalpha(Image.fromarray((np.asarray(ribbon.getchannel("A"), np.float32) * fray * pose.fade).astype(np.uint8)))
        layer.alpha_composite(ribbon)


def draw_robe(layer: Image.Image, pose: Pose) -> None:
    """The ROBE: the cloak's body from the shoulders down, shaded light at
    the shoulders to near black at the hem, its FOLDS falling in dark creases
    each with a lit ridge beside it, an embroidered TRIM down its front, the
    Gram-matrix EMBLEM on its breast, and long TATTERS at the hem that
    dissolve into violet mist (it has no feet: it floats)."""
    c, sh = pose.centre, _shoulder(pose)
    hem_y = c[1] + 74.0
    back_sh, front_sh = _add(sh, _rot((-17, 0), pose.lean)), _add(sh, _rot((15, 0), pose.lean))
    lengths = (26, 8, 34, 14, 40, 10, 30, 18, 44, 12, 28)
    hem = []
    for k, extra in enumerate(lengths):
        t = k / (len(lengths) - 1)
        x = c[0] + 40 - 96 * t + 3 * math.sin(pose.cloak_phase + k * 1.3)
        hem.append((x, hem_y + extra * 0.6 + 4 * math.sin(pose.cloak_phase * 1.3 + k)))
        if k < len(lengths) - 1:
            hem.append((x - 4, hem_y - 4))
    body = [back_sh, front_sh, (c[0] + 32, c[1] + 18)] + hem + [(c[0] - 48, c[1] + 16)]
    robe = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    _fill_gradient(robe, body, (122, 86, 196, 255), (30, 14, 62, 255), (sh[0] + 10, sh[1]), (c[0] - 10, hem_y + 30))
    d = blending_draw(robe)
    # The back fold, in shadow.
    fold = [back_sh, (c[0] - 6, c[1] + 2), (c[0] - 22, hem_y + 10), (c[0] - 38, c[1] + 14)]
    _fill_gradient(robe, fold, (60, 34, 112, 255), (18, 8, 40, 255), back_sh, (c[0] - 30, hem_y))
    d = blending_draw(robe)
    # Folds: dark creases falling from the shoulders, a lit ridge by each.
    for k, (x0, x1) in enumerate(((-8, -16), (2, -2), (10, 12), (18, 26))):
        top = _add(sh, _rot((x0 * 0.6, 14), pose.lean))
        mid = (c[0] + x0 + 2 * math.sin(pose.cloak_phase + k), c[1] + 30)
        bot = (c[0] + x1, hem_y + 6)
        d.line([_s(top), _s(mid), _s(bot)], fill=(14, 6, 30, 170), width=int(1.8 * SUPER), joint="curve")
        d.line([_s(_add(top, (2, 0))), _s(_add(mid, (2.2, 0))), _s(_add(bot, (2.4, 0)))], fill=(176, 140, 240, 70), width=int(1.0 * SUPER), joint="curve")
    d.line([_s(p) for p in body + [body[0]]], fill=OUTLINE, width=int(1.4 * SUPER), joint="curve")
    # The trim down its front: a lit band with dashes and small triangles.
    trim = [_add(sh, _rot((7, 6), pose.lean)), (c[0] + 12, c[1] + 10), (c[0] + 10, hem_y)]
    d.line([_s(p) for p in trim], fill=(40, 20, 76, 255), width=int(4.0 * SUPER), joint="curve")
    d.line([_s(p) for p in trim], fill=_a(TRIM, 0.9), width=int(1.0 * SUPER), joint="curve")
    for k in range(1, 6):
        t = k / 6.0
        q = (trim[1][0] + (trim[2][0] - trim[1][0]) * t, trim[1][1] + (trim[2][1] - trim[1][1]) * t)
        d.polygon([_s((q[0] - 1.6, q[1] + 1.2)), _s((q[0] + 1.6, q[1] + 1.2)), _s((q[0], q[1] - 1.6))], fill=_a(TRIM, 0.8))
    # The emblem: a bracketed Gram matrix of glowing dots on a dark plate.
    e = _add(sh, _rot((0, 24), pose.lean))
    d.rectangle((*_s((e[0] - 8, e[1] - 8)), *_s((e[0] + 8, e[1] + 8))), fill=(26, 12, 52, 255), outline=_a(TRIM, 0.8), width=int(0.8 * SUPER))
    for side in (-1, 1):
        x = e[0] + side * 6
        d.line([_s((x - side * 2, e[1] - 6)), _s((x, e[1] - 6)), _s((x, e[1] + 6)), _s((x - side * 2, e[1] + 6))], fill=_a(NODE, 0.9), width=int(0.8 * SUPER))
    dots = [(e[0] - 3.6 + i * 3.6, e[1] - 3.6 + j * 3.6) for i in range(3) for j in range(3)]
    _glow(robe, lambda g: [g.ellipse((*_s((p[0] - 1.4, p[1] - 1.4)), *_s((p[0] + 1.4, p[1] + 1.4))), fill=_a(GLOW, 0.9)) for p in dots], 0.8)
    d = blending_draw(robe)
    for p in dots:
        d.ellipse((*_s((p[0] - 0.8, p[1] - 0.8)), *_s((p[0] + 0.8, p[1] + 0.8))), fill=NODE)
    # The hem dissolves: its alpha fades, and mist curls off it.
    _fade_below(robe, hem_y - 26, hem_y + 34, 0.0)
    if pose.fade < 1.0:
        robe.putalpha(robe.getchannel("A").point(lambda v: int(v * pose.fade)))
    layer.alpha_composite(robe)

    def mist(g):
        for k in range(7):
            x = c[0] - 34 + k * 11 + 4 * math.sin(pose.cloak_phase + k)
            pts = [(x + 4 * math.sin(j * 0.8 + pose.cloak_phase + k), hem_y - 10 + j * 6) for j in range(7)]
            g.line([_s(q) for q in pts], fill=_a(GLOW, 0.22 * pose.fade), width=int(7 * SUPER), joint="curve")

    _glow(layer, mist, 3.5)


def draw_shoulder_flaps(layer: Image.Image, pose: Pose) -> None:
    """SHOULDER FLAPS: two angular pauldrons of cloth, each with a small
    triangle (the Laplacian's graph) stitched on it."""
    sh = _shoulder(pose)
    d = blending_draw(layer)
    for side in (-1, 1):
        o = _add(sh, _rot((side * 12, 2), pose.lean))
        flap = [(o[0] - 10, o[1] - 6), (o[0] + 10, o[1] - 8), (o[0] + 12 * side + 2, o[1] + 10), (o[0] - 4, o[1] + 8)]
        d.polygon([_s(p) for p in flap], fill=_a(CLOAK_LIGHT if side > 0 else CLOAK, pose.fade), outline=_a(OUTLINE, pose.fade))
        tri = [(o[0] - 3, o[1] + 3), (o[0] + 3, o[1] + 3), (o[0], o[1] - 3)]
        d.line([_s(p) for p in tri + [tri[0]]], fill=_a(TRIM, 0.8 * pose.fade), width=int(0.8 * SUPER))


def draw_hood(layer: Image.Image, pose: Pose) -> None:
    """The HOOD: a deep peaked cowl, shaded from a lit crown to a dark
    hem, a lavender RIM LIGHT along its back edge, a stitched graph glyph (a
    triangle of nodes) on its side, and inside it nothing: a void that
    deepens to black, with two EYE-SHARDS blazing in it, a flare off each."""
    sh = _shoulder(pose)
    tilt = pose.lean + pose.hood_tilt
    h = _add(sh, _rot((6, -15), tilt))
    cowl = [_add(h, _rot(p, tilt)) for p in ((-20, 12), (-19, -6), (-10, -22), (-17, -34), (2, -24), (16, -12), (20, 2), (17, 14))]
    hood = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    _fill_gradient(hood, cowl, (140, 104, 214, 255), (40, 20, 80, 255), _add(h, (-6, -30)), _add(h, (4, 16)))
    d = blending_draw(hood)
    d.line([_s(p) for p in cowl + [cowl[0]]], fill=OUTLINE, width=int(1.4 * SUPER), joint="curve")
    d.line([_s(p) for p in cowl[:4]], fill=(206, 182, 255, 200), width=int(1.0 * SUPER), joint="curve")
    # The stitched glyph on its side.
    g0 = _add(h, _rot((-12, -6), tilt))
    tri = [(g0[0] - 3, g0[1] + 3), (g0[0] + 3, g0[1] + 3), (g0[0], g0[1] - 3)]
    d.line([_s(p) for p in tri + [tri[0]]], fill=_a(TRIM, 0.85), width=int(0.8 * SUPER))
    for p in tri:
        d.ellipse((*_s((p[0] - 0.9, p[1] - 0.9)), *_s((p[0] + 0.9, p[1] + 0.9))), fill=_a(NODE, 0.9))
    # The face: a void, darkest at its middle.
    face = [_add(h, _rot(p, tilt)) for p in ((-6, 12), (-9, -4), (1, -14), (15, -6), (15, 12))]
    _fill_gradient(hood, face, (40, 18, 74, 255), (2, 0, 6, 255), _add(h, (2, -14)), _add(h, (4, 4)))
    layer.alpha_composite(hood)
    for ex in (1.0, 9.0):
        e = _add(h, _rot((ex, -2), tilt))
        eye = [(e[0] - 3.0, e[1] - 0.6), (e[0] + 2.8, e[1] - 2.2), (e[0] + 1.8, e[1] + 1.4), (e[0] - 2.0, e[1] + 1.0)]
        _glow(layer, lambda g, eye=eye: g.polygon([_s(p) for p in eye], fill=_a(GLOW, pose.eye_glow * pose.fade)), 1.4 + 2.0 * pose.eye_glow)
        _glow(layer, lambda g, e=e: g.line([_s((e[0] - 7 * pose.eye_glow, e[1])), _s((e[0] + 7 * pose.eye_glow, e[1] - 1))],
                                           fill=_a(EYE, 0.7 * pose.eye_glow * pose.fade), width=int(0.8 * SUPER)), 0.4)
        blending_draw(layer).polygon([_s(p) for p in eye], fill=_a(EYE, pose.fade))


def _hand(pose: Pose, near: bool) -> Point:
    sh = _shoulder(pose)
    root = _add(sh, _rot((12 if near else -10, 6), pose.lean))
    angles = pose.near_arm if near else pose.far_arm
    elbow = _along(root, angles[0], 24.0)
    return _along(elbow, angles[0] + angles[1], 22.0)


def draw_arm(layer: Image.Image, pose: Pose, near: bool) -> None:
    """An ARM: a wide tattered sleeve over the upper arm, a bony forearm and a
    long-fingered skeletal HAND."""
    sh = _shoulder(pose)
    root = _add(sh, _rot((12 if near else -10, 6), pose.lean))
    angles = pose.near_arm if near else pose.far_arm
    elbow = _along(root, angles[0], 24.0)
    wrist = _hand(pose, near)
    d = blending_draw(layer)
    bone = _a(BONE if near else METAL, pose.fade)
    for colour, w in ((_a(OUTLINE, pose.fade), 4.2), (bone, 2.4)):
        d.line([_s(elbow), _s(wrist)], fill=colour, width=int(w * SUPER))
    sleeve_end = _along(elbow, angles[0] + angles[1], 6.0)
    perp = angles[0] + 90
    sleeve = [_along(root, perp, 6), _along(sleeve_end, perp, 7), _along(sleeve_end, angles[0] + angles[1] + 20, 4),
              _along(sleeve_end, perp + 180, 8), _along(root, perp + 180, 6)]
    d.polygon([_s(p) for p in sleeve], fill=_a(CLOAK_LIGHT if near else CLOAK_DARK, pose.fade), outline=_a(OUTLINE, pose.fade))
    for spread in (-30, -10, 10, 30):
        mid = _along(wrist, angles[0] + angles[1] + spread, 5.0)
        tip = _along(mid, angles[0] + angles[1] + spread + 40, 4.0)
        d.line([_s(wrist), _s(mid), _s(tip)], fill=_a(OUTLINE, pose.fade), width=int(2.0 * SUPER), joint="curve")
        d.line([_s(wrist), _s(mid), _s(tip)], fill=bone, width=int(1.0 * SUPER), joint="curve")


def _scythe_top(pose: Pose) -> Point:
    hand = _hand(pose, near=True)
    a = math.radians(pose.scythe)
    return (hand[0] + math.sin(a) * 78, hand[1] - math.cos(a) * 78)


def draw_scythe(layer: Image.Image, pose: Pose) -> None:
    """The SCYTHE in its near hand: a long dark SHAFT banded in pale metal and
    wrapped at the grip, a glowing ORB in a ring at its head, and the great
    crescent BLADE: steel shaded from a white-hot edge to a dark spine,
    ETCHED with an orthogonal frame (two axes and the right angle between
    them) and a dashed line, its edge burning violet."""
    hand = _hand(pose, near=True)
    a = math.radians(pose.scythe)
    up = (math.sin(a), -math.cos(a))
    fwd = (math.cos(a), math.sin(a))
    top = _scythe_top(pose)
    butt = (hand[0] - up[0] * 50, hand[1] - up[1] * 50)
    d = blending_draw(layer)
    for colour, w in ((OUTLINE, 5.0), ((44, 34, 70, 255), 3.2)):
        d.line([_s(butt), _s(top)], fill=_a(colour, pose.fade), width=int(w * SUPER))
    d.line([_s(_add(butt, (-fwd[0], -fwd[1]))), _s(_add(top, (-fwd[0], -fwd[1])))], fill=_a((110, 96, 150, 255), pose.fade), width=int(0.7 * SUPER))
    for k in range(6):
        t = 0.06 + 0.17 * k
        p = (butt[0] + (top[0] - butt[0]) * t, butt[1] + (top[1] - butt[1]) * t)
        q0, q1 = _add(p, (fwd[0] * 2.6, fwd[1] * 2.6)), _add(p, (-fwd[0] * 2.6, -fwd[1] * 2.6))
        d.line([_s(q0), _s(q1)], fill=_a(METAL if k % 2 else TRIM, pose.fade), width=int(1.4 * SUPER))
    butt_cap = [_add(butt, (up[0] * -8, up[1] * -8)), _add(butt, (fwd[0] * 2.5, fwd[1] * 2.5)), _add(butt, (-fwd[0] * 2.5, -fwd[1] * 2.5))]
    d.polygon([_s(p) for p in butt_cap], fill=_a(TRIM, pose.fade), outline=_a(OUTLINE, pose.fade))
    # The blade.
    R = 64.0
    outer, inner = [], []
    for k in range(29):
        t = k / 28.0
        ang = math.radians(t * 108.0)
        o = (top[0] + fwd[0] * R * math.sin(ang) + up[0] * R * (math.cos(ang) - 1) * 0.85,
             top[1] + fwd[1] * R * math.sin(ang) + up[1] * R * (math.cos(ang) - 1) * 0.85)
        outer.append(o)
        shrink = 1.0 - 0.34 * math.sin(t * math.pi) ** 0.6
        inner.append((top[0] + (o[0] - top[0]) * shrink, top[1] + (o[1] - top[1]) * shrink))
    blade = outer + inner[::-1]
    spine = inner[14]
    _glow(layer, lambda g: g.line([_s(p) for p in outer], fill=_a(GLOW, 0.85 * pose.fade), width=int(6 * SUPER), joint="curve"), 2.6)
    _fill_gradient(layer, blade, (240, 232, 255, 255), (52, 34, 96, 255), outer[14], spine, pose.fade)
    edge = outer + [(top[0] + (o[0] - top[0]) * 0.94, top[1] + (o[1] - top[1]) * 0.94) for o in outer][::-1]
    _fill_gradient(layer, edge, (255, 255, 255, 255), (200, 160, 255, 255), outer[0], outer[-1], 0.85 * pose.fade)
    d = blending_draw(layer)
    d.line([_s(p) for p in blade + [blade[0]]], fill=_a(OUTLINE, pose.fade), width=int(1.2 * SUPER), joint="curve")
    # The etching: an orthogonal frame and a dashed line along the blade.
    mid = [((o[0] + i[0]) / 2, (o[1] + i[1]) / 2) for o, i in zip(outer, inner)]
    for k in range(13, 25, 3):
        d.line([_s(mid[k]), _s(mid[k + 1])], fill=_a((70, 40, 120, 255), pose.fade), width=int(1.0 * SUPER))
    o0 = mid[7]
    ax = (mid[10][0] - o0[0], mid[10][1] - o0[1])
    ay = (-ax[1] * 0.8, ax[0] * 0.8)
    d.line([_s(_add(o0, ax)), _s(o0), _s(_add(o0, ay))], fill=_a((70, 40, 120, 255), pose.fade), width=int(0.9 * SUPER))
    m = 0.3
    d.line([_s(_add(o0, (ax[0] * m, ax[1] * m))), _s(_add(o0, (ax[0] * m + ay[0] * m, ax[1] * m + ay[1] * m))), _s(_add(o0, (ay[0] * m, ay[1] * m)))],
           fill=_a((70, 40, 120, 255), pose.fade), width=int(0.7 * SUPER))
    # The collar where blade meets shaft, and the orb.
    d.ellipse((*_s((top[0] - 6.5, top[1] - 6.5)), *_s((top[0] + 6.5, top[1] + 6.5))), fill=_a((44, 34, 70, 255), pose.fade), outline=_a(TRIM, pose.fade), width=int(1.2 * SUPER))
    _glow(layer, lambda g: g.ellipse((*_s((top[0] - 9, top[1] - 9)), *_s((top[0] + 9, top[1] + 9))), fill=_a(GLOW, 0.9 * pose.fade)), 2.4)
    _glow(layer, lambda g: [g.line([_s((top[0] - 12, top[1])), _s((top[0] + 12, top[1]))], fill=_a(NODE, 0.6 * pose.fade), width=int(0.8 * SUPER)),
                            g.line([_s((top[0], top[1] - 12)), _s((top[0], top[1] + 12))], fill=_a(NODE, 0.6 * pose.fade), width=int(0.8 * SUPER))], 0.4)
    d = blending_draw(layer)
    d.ellipse((*_s((top[0] - 3, top[1] - 3)), *_s((top[0] + 3, top[1] + 3))), fill=_a(NODE, pose.fade))


def _arc(c: Point, r: float, a0: float, a1: float, width: float) -> List[Point]:
    """A crescent band about ``c`` from ``a0`` to ``a1`` degrees (screen
    angles), ``width`` at its thickest."""
    out, inn = [], []
    for k in range(25):
        t = k / 24.0
        a = math.radians(a0 + (a1 - a0) * t)
        thick = width * math.sin(t * math.pi)
        out.append((c[0] + math.cos(a) * r, c[1] + math.sin(a) * r))
        inn.append((c[0] + math.cos(a) * (r - thick), c[1] + math.sin(a) * (r - thick)))
    return out + inn[::-1]


def draw_graph_cut_slash(layer: Image.Image, pose: Pose) -> None:
    """The GRAPH-CUT SLASH: a huge violet crescent sweeping down through the
    front, and an EDGE-CUT BURST (a star of short cut lines) where it ends."""
    u = pose.cut_slash
    if u < 0:
        return
    c = _add(pose.centre, (10, -20))
    end = -80 + 200 * u
    fade = 1.0 - max(0.0, (u - 0.75) / 0.25)
    band = _arc(c, 92.0, end - 130, end, 22.0)
    _glow(layer, lambda g: g.polygon([_s(p) for p in band], fill=_a(GLOW, 0.8 * fade)), 2.5)
    blending_draw(layer).polygon([_s(p) for p in band], fill=_a(NODE, 0.7 * fade))
    if u > 0.5:
        tip = (c[0] + math.cos(math.radians(end)) * 86, c[1] + math.sin(math.radians(end)) * 86)
        for k in range(8):
            a = math.radians(k * 45 + 20)
            p0 = (tip[0] + math.cos(a) * 5, tip[1] + math.sin(a) * 5)
            p1 = (tip[0] + math.cos(a) * 12, tip[1] + math.sin(a) * 12)
            blending_draw(layer).line([_s(p0), _s(p1)], fill=_a(NODE, fade), width=int(1.2 * SUPER))


def draw_orthogonal_slash(layer: Image.Image, pose: Pose) -> None:
    """The ORTHOGONAL DOUBLE-SLASH: a level sweep, then a cut square to it
    (Gram-Schmidt: project, then the orthogonal part), and a right-angle
    mark where they cross."""
    cross = _add(pose.centre, (72, -10))
    for u, horizontal in ((pose.ortho_sweep, True), (pose.ortho_cut, False)):
        if u < 0:
            continue
        fade = 1.0 - max(0.0, (u - 0.7) / 0.3)
        span = 90.0 * min(1.0, u * 1.6)
        if horizontal:
            band = [(cross[0] - 70, cross[1] - 4), (cross[0] - 70 + span, cross[1] - 6), (cross[0] - 70 + span + 8, cross[1]), (cross[0] - 70 + span, cross[1] + 5), (cross[0] - 70, cross[1] + 3)]
        else:
            band = [(cross[0] - 4, cross[1] - 60), (cross[0] - 6, cross[1] - 60 + span), (cross[0], cross[1] - 60 + span + 8), (cross[0] + 5, cross[1] - 60 + span), (cross[0] + 3, cross[1] - 60)]
        _glow(layer, lambda g, band=band, fade=fade: g.polygon([_s(p) for p in band], fill=_a(GLOW, 0.9 * fade)), 2.2)
        blending_draw(layer).polygon([_s(p) for p in band], fill=_a(NODE, 0.8 * fade))
    if pose.ortho_cut > 0.3:
        m = 7.0
        blending_draw(layer).line([_s((cross[0] + m, cross[1])), _s((cross[0] + m, cross[1] - m)), _s((cross[0], cross[1] - m))],
                                  fill=_a(NODE, 0.9), width=int(1.2 * SUPER))


def draw_projection(layer: Image.Image, pose: Pose) -> None:
    """The TELEGRAPH's PROJECTION: a dashed line from the reaper to its mark
    and the dashed drop square to it (it picks the axis it will cut along)."""
    if pose.projection <= 0:
        return
    a = _add(pose.centre, (20, -10))
    b = _add(pose.centre, (20 + 76 * pose.projection, -10))
    v = _add(pose.centre, (20 + 76 * pose.projection, -10 - 44 * pose.projection))
    d = blending_draw(layer)
    for p, q in ((a, b), (a, v), (v, b)):
        for k in range(10):
            t0, t1 = k / 10.0, (k + 0.5) / 10.0
            d.line([_s((p[0] + (q[0] - p[0]) * t0, p[1] + (q[1] - p[1]) * t0)), _s((p[0] + (q[0] - p[0]) * t1, p[1] + (q[1] - p[1]) * t1))],
                   fill=_a(NODE, 0.8 * pose.projection), width=int(1.0 * SUPER))
    d.ellipse((*_s((v[0] - 2.5, v[1] - 2.5)), *_s((v[0] + 2.5, v[1] + 2.5))), fill=_a(NODE, pose.projection))


# --- assembly ---------------------------------------------------------------------


def draw_reaper(pose: Pose) -> Image.Image:
    img = Image.new("RGBA", (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER), (0, 0, 0, 0))
    c = pose.centre
    # Its AURA: a dim violet bloom round its body.
    _glow(img, lambda g: g.ellipse((*_s((c[0] - 50, c[1] - 76)), *_s((c[0] + 46, c[1] + 70))), fill=_a(GLOW, 0.16 * pose.fade)), 14.0)
    draw_constellation(img, pose, edges_only=True)
    if pose.fade > 0.02:
        draw_cloak_ribbons(img, pose)
        draw_arm(img, pose, near=False)
        draw_robe(img, pose)
        draw_shoulder_flaps(img, pose)
        draw_hood(img, pose)
        draw_scythe(img, pose)
        draw_arm(img, pose, near=True)
        # The orb lights the blade and the cowl near it; the eyes, the hood.
        h = _add(_shoulder(pose), _rot((10, -17), pose.lean + pose.hood_tilt))
        _light_pass(img, [(_scythe_top(pose), 34.0, GLOW, 0.35 * pose.fade), (h, 12.0, EYE, 0.25 * pose.eye_glow * pose.fade)])
    # Motes drifting up round it.
    rng = np.random.default_rng(5)
    d = blending_draw(img)
    for _ in range(14):
        x, y, ph = c[0] - 60 + rng.random() * 120, c[1] - 90 + rng.random() * 170, rng.random()
        yy = y - ((pose.cloak_phase / math.tau + ph) % 1.0) * 20
        d.ellipse((*_s((x - 0.9, yy - 0.9)), *_s((x + 0.9, yy + 0.9))), fill=_a(NODE, 0.6 * (0.4 + 0.6 * pose.fade)))
    draw_constellation(img, replace(pose, fade=max(pose.fade, 0.6) if pose.graph_spread > 1.05 else pose.fade), edges_only=False)
    draw_projection(img, pose)
    draw_graph_cut_slash(img, pose)
    draw_orthogonal_slash(img, pose)
    return img


def _pose_for(animation: str, i: int, n: int) -> Pose:
    t = i / max(1, n)
    u = i / max(1, n - 1)
    w = math.sin(t * math.tau)
    base = Pose(centre=(132.0, 160.0 + 3.0 * w), cloak_phase=t * math.tau, graph_rot=6.0 * w, eye_glow=0.6 + 0.2 * w)
    if animation == "idle":
        return replace(base, near_arm=(40.0 + 3 * w, 60.0))
    if animation == "walk":
        return replace(base, lean=18.0, cloak_back=0.6, centre=(132.0 + 3 * w, 158.0), scythe=30.0, near_arm=(55.0, 50.0), graph_rot=10 * w)
    if animation == "attack_side":
        if i <= 5:  # telegraph: the scythe raised back, eyes and nodes flare
            k = i / 5.0
            return replace(base, lean=8.0 - 14.0 * k, scythe=10.0 - 70.0 * k, near_arm=(40.0 + 100.0 * k, 60.0 - 40.0 * k),
                           eye_glow=0.7 + 0.3 * k, graph_spread=1.0 + 0.1 * k)
        if i <= 9:  # commit: the sweep through, edges severed
            k = (i - 6) / 3.0
            return replace(base, lean=-6.0 + 30.0 * k, scythe=-60.0 + 190.0 * k, near_arm=(140.0 - 90.0 * k, 20.0 + 20.0 * k),
                           cloak_back=1.0, eye_glow=1.0, cut_slash=0.2 + 0.8 * k, graph_cut=k)
        k = (i - 10) / 5.0  # recovery: the blade low, open
        return replace(base, lean=24.0 - 16.0 * k, scythe=130.0 - 120.0 * k, near_arm=(50.0 - 10.0 * k, 40.0 + 20.0 * k),
                       eye_glow=0.4 + 0.3 * k, graph_cut=1.0 - k, cut_slash=1.0 if i == 10 else -1.0)
    if animation == "ortho_slash":
        if i <= 5:  # telegraph: it picks its axis, projects to its mark
            k = i / 5.0
            return replace(base, scythe=10.0 + 70.0 * k, near_arm=(40.0 + 50.0 * k, 50.0), projection=k, eye_glow=0.7 + 0.3 * k)
        if i <= 10:  # commit: the level sweep, then the cut square to it
            k = (i - 6) / 4.0
            sweep = min(1.0, k * 2.0)
            cut = max(0.0, k * 2.0 - 1.0)
            return replace(base, lean=12.0, scythe=80.0 + 100.0 * cut, near_arm=(90.0 + 30.0 * cut, 30.0), eye_glow=1.0,
                           ortho_sweep=sweep, ortho_cut=cut if k > 0.5 else -1.0, cloak_back=0.8)
        k = (i - 11) / 4.0
        return replace(base, lean=16.0 - 8 * k, scythe=170.0 - 160.0 * k, near_arm=(60.0 - 20 * k, 50.0), eye_glow=0.4 + 0.3 * k,
                       ortho_sweep=1.0 if i == 11 else -1.0, ortho_cut=1.0 if i == 11 else -1.0)
    if animation == "vanish":
        k = math.sin(u * math.pi)  # out to its constellation and back
        return replace(base, fade=1.0 - k, graph_spread=1.0 + 0.6 * k, eye_glow=1.0)
    if animation == "hurt":
        k = 1.0 - u
        return replace(base, lean=-12.0 * k + 8, hood_tilt=-14.0 * k, centre=(128.0 - 4 * k, 160.0), eye_glow=1.0, graph_cut=0.5 * k)
    if animation == "death":
        k = u
        return replace(base, fade=1.0 - min(1.0, k * 1.4), graph_spread=1.0 + 0.6 * k, graph_cut=min(1.0, k * 2.0),
                       eye_glow=1.0 - k, lean=8.0 + 20 * k, centre=(132.0, 160.0 + 10 * k))
    raise ValueError(f"{TARGET_NAME}: no row {animation!r}")


def _render_frame(animation: str, frame_index: int, nframes: int) -> Image.Image:
    img = draw_reaper(_pose_for(animation, frame_index, nframes))
    if animation == "death":
        fade = 1.0 - max(0.0, (frame_index / max(1, nframes - 1) - 0.7) / 0.3)
        img.putalpha(img.getchannel("A").point(lambda v: int(v * fade)))
    return img.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


ACTOR_METADATA = {
    "actor": {"character_id": TARGET_NAME, "display_name": "Gram Reaper"},
    "body": {
        "body_plan": "Humanoid",
        "body_kind": "Entity",
        "mass_class": "Heavy",
        "traits": ["spectral", "boss", "reaper", "math", "floating"],
        "locomotion_hint": "Float",
    },
    "visual": {"default_pose": "idle", "portrait": {"animation": "idle", "frame": 0}},
    "tags": ["math", "spectral", "boss", "hylberts_hotel"],
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
