"""The Eigenghost: a generic spectral enemy of the haunted floors of
Hylbert's Hotel (the Math dimension). Jon, 2026-10-31: "spectral enemies
... playing on things like spectral graph theory, eigenvectors, basically
spooky things with math puns".

A ghost that is its own covariance: a pale sheet shaped like an ellipse
(its SHROUD), its two EIGENVECTOR ARMS glowing along its principal axes (the
long one, lambda-1, is the one it strikes with), a hem that hangs in a
SPECTRUM of decaying ripples, and two hollow EYES. It only ever stretches
along its eigenvectors, never turns: transformation, not rotation.

Rows: ``idle`` (it bobs and breathes along its axes), ``walk`` (it drifts,
its hem rippling), ``attack_side`` (it winds up, then its major axis lances
out: lambda-1 grows), ``hurt`` (its eigenvalues jolt apart), ``block`` (it rears along its
vertical eigenvector, the larger eigenvalue, to wall off a jump over it,
widening a little along the horizontal one, then settles) and ``death``
(rank collapse: it flattens to a line, then to a point, then nothing).

Drawn on a fixed canvas facing right, its hem's lowest point near the
canvas foot. No drop shadow.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "eigenghost"
FRAME_SIZE = (184, 288)
SUPER = 4
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 120),
    ("walk", 8, 100),
    ("attack_side", 8, 70),
    ("hurt", 3, 90),
    ("block", 10, 90),
    ("death", 7, 110),
]

# A haunted palette: a cold pale sheet, its axes lit a spectral green.
SHROUD: RGBA = (214, 232, 240, 235)
SHROUD_SHADE: RGBA = (150, 176, 196, 235)
OUTLINE: RGBA = (36, 44, 66, 255)
EYE: RGBA = (20, 18, 40, 255)
AXIS_CORE: RGBA = (226, 255, 236, 255)
AXIS_GLOW: RGBA = (90, 255, 170, 255)
GRID: RGBA = (120, 150, 190, 120)

#: The centre of the shroud at rest, and its semi-axes (frame pixels).
CENTRE = (76.0, 218.0)
MAJOR = 24.0
MINOR = 19.0
#: The length of an eigenvector arm at eigenvalue 1 (the unit axes it was
#: drawn on: at rest both eigenvalues are 1, both arms this long).
UNIT_ARM = 13.0
#: The hem: how far below the centre it hangs, and its spectrum of ripples.
HEM_DROP = 44.0
HEM_MODES = ((1.0, 3.2), (2.0, 1.7), (3.0, 0.9), (5.0, 0.45))

ACTOR_METADATA = {
    "actor": {"character_id": TARGET_NAME, "display_name": "Eigenghost"},
    "body": {
        "body_plan": "Amorphous",
        "body_kind": "Entity",
        "mass_class": "Light",
        "traits": ["spectral", "ghost", "math", "floating"],
        "locomotion_hint": "Float",
    },
    "visual": {"default_pose": "idle", "portrait": {"animation": "idle", "frame": 0}},
    "tags": ["math", "spectral", "enemy"],
    "animation_bindings": {"default": {"animation": "idle", "events": []}},
}


def _s(p: Point) -> Point:
    return (p[0] * SUPER, p[1] * SUPER)


def _with_alpha(c: RGBA, a: float) -> RGBA:
    return (c[0], c[1], c[2], int(max(0.0, min(1.0, a)) * c[3]))


def _shroud_outline(cx: float, cy: float, lam1: float, lam2: float, hem: float, phase: float) -> List[Point]:
    """The SHROUD: the upper half of its covariance ellipse (semi-axes
    ``lam1`` across, ``lam2`` up), then sides falling to a HEM whose edge is a
    sum of decaying sine modes (its spectrum), ``hem`` below the centre."""
    pts: List[Point] = []
    for k in range(0, 41):
        a = math.pi + math.pi * k / 40.0  # left, over the top, to the right
        pts.append((cx + math.cos(a) * lam1, cy + math.sin(a) * lam2))
    # Down the right side, narrowing a little toward the hem.
    for k in range(1, 9):
        t = k / 8.0
        pts.append((cx + lam1 * (1.0 - 0.18 * t), cy + hem * t * 0.82))
    # The hem, right to left: its ripples are its spectrum.
    for k in range(0, 49):
        u = 1.0 - k / 48.0
        x = cx + lam1 * 0.82 * (2.0 * u - 1.0)
        ripple = sum(amp * math.sin(mode * (u * math.tau) + phase * mode) for mode, amp in HEM_MODES)
        pts.append((x, cy + hem * 0.82 + ripple + 3.0 * math.sin(u * math.pi)))
    for k in range(1, 8):
        t = 1.0 - k / 8.0
        pts.append((cx - lam1 * (1.0 - 0.18 * t), cy + hem * t * 0.82))
    return pts


_GRID_XY = {}


def _grid_xy(size):
    if size not in _GRID_XY:
        ys, xs = np.mgrid[0 : size[1], 0 : size[0]].astype(np.float32)
        _GRID_XY[size] = (xs / SUPER, ys / SUPER)
    return _GRID_XY[size]


def _glow(layer: Image.Image, fn, blur: float) -> None:
    g = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    fn(blending_draw(g))
    layer.alpha_composite(g.filter(ImageFilter.GaussianBlur(blur * SUPER)))


def _draw_eigen_grid(layer: Image.Image, cx: float, cy: float, lam1: float, lam2: float, alpha: float) -> None:
    """The LATTICE inside the shroud: the unit grid it has transformed, its
    lines evenly spaced along its two axes and stretched by them (a haunting
    of graph paper), faint, with a node at each crossing near its heart."""
    d = blending_draw(layer)
    xs = [cx + k * lam1 * 0.3 for k in (-2, -1, 0, 1, 2)]
    ys = [cy - lam2 * 0.35 + k * lam2 * 0.35 for k in (0, 1, 2, 3)]
    for x in xs:
        d.line([_s((x, ys[0] - 4)), _s((x, ys[-1] + 4))], fill=_with_alpha(GRID, alpha), width=int(0.7 * SUPER))
    for y in ys:
        d.line([_s((xs[0] - 4, y)), _s((xs[-1] + 4, y))], fill=_with_alpha(GRID, alpha), width=int(0.7 * SUPER))
    for x in xs[1:4]:
        for y in ys[1:3]:
            d.ellipse((*_s((x - 0.9, y - 0.9)), *_s((x + 0.9, y + 0.9))), fill=_with_alpha((170, 230, 220, 255), 0.6 * alpha))


def _draw_eigen_arm(layer: Image.Image, start: Point, end: Point, glow: float) -> None:
    """One EIGENVECTOR ARM: a beam of green light from the shroud along its
    axis, a soft halo round a white-hot core, its head a sharp triangle with
    a flare."""
    _glow(layer, lambda g: g.line([_s(start), _s(end)], fill=_with_alpha(AXIS_GLOW, 0.7 * glow), width=int(6 * SUPER)), 2.4)
    d = blending_draw(layer)
    d.line([_s(start), _s(end)], fill=AXIS_CORE, width=int(1.6 * SUPER))
    ang = math.atan2(end[1] - start[1], end[0] - start[0])
    size = 6.0
    tip = (end[0] + math.cos(ang) * size, end[1] + math.sin(ang) * size)
    left = (end[0] + math.cos(ang + 2.4) * size * 0.8, end[1] + math.sin(ang + 2.4) * size * 0.8)
    right = (end[0] + math.cos(ang - 2.4) * size * 0.8, end[1] + math.sin(ang - 2.4) * size * 0.8)
    _glow(layer, lambda g: g.polygon([_s(tip), _s(left), _s(right)], fill=_with_alpha(AXIS_GLOW, glow)), 1.4)
    blending_draw(layer).polygon([_s(tip), _s(left), _s(right)], fill=AXIS_CORE)
    _glow(layer, lambda g: g.ellipse((*_s((tip[0] - 2, tip[1] - 2)), *_s((tip[0] + 2, tip[1] + 2))), fill=_with_alpha(AXIS_CORE, glow)), 1.0)


def _draw_eyes(layer: Image.Image, cx: float, cy: float, lam1: float, lam2: float, squint: float) -> None:
    """Two EYES in the shroud: deep hollows, inner corners dipping under a
    scowl, a cold green point of light in each (it is watching you)."""
    d = blending_draw(layer)
    for side, dx in ((-1, 0.04), (1, 0.5)):
        ex, ey = cx + lam1 * dx, cy - lam2 * 0.22
        inward = 1.0 if side < 0 else -1.0  # toward the other eye
        open_ = 1.0 - squint
        # A slanted shard: its inner corner dips, its outer corner rises (a
        # scowl), its lower edge a curve.
        shard = [(ex + inward * 3.6, ey + 0.6), (ex - inward * 3.8, ey - 2.4 * open_ - 0.4), (ex - inward * 2.6, ey + 1.6 * open_),
                 (ex, ey + 2.8 * open_ + 0.3), (ex + inward * 2.2, ey + 2.0 * open_)]
        d.polygon([_s(p) for p in shard], fill=EYE)
        g = (ex - inward * 0.4, ey + 0.6 * open_)
        _glow(layer, lambda gg, g=g: gg.ellipse((*_s((g[0] - 2.2, g[1] - 1.4)), *_s((g[0] + 2.2, g[1] + 1.4))), fill=_with_alpha(AXIS_GLOW, 0.9 * (1 - squint * 0.6))), 1.2)
        d = blending_draw(layer)
        d.ellipse((*_s((g[0] - 0.9, g[1] - 0.7)), *_s((g[0] + 0.9, g[1] + 0.7))), fill=_with_alpha(AXIS_CORE, 1 - squint * 0.5))


def _draw_ghost(cx: float, cy: float, lam1: float, lam2: float, hem: float, phase: float,
                arm1: float, arm2: float, glow: float, squint: float, alpha: float,
                eig_x: float = 1.0, eig_y: float = 1.0) -> Image.Image:
    """The whole ghost. Its body is drawn at rest, then WARPED by its
    eigenvalues (``eig_x`` across, ``eig_y`` up) about the foot of its hem,
    and each eigenvector arm drawn at its root in the warped body, its
    length its eigenvalue times the unit: the arms and the shape always
    agree (the axes of the unit square under the same stretch)."""
    img = Image.new("RGBA", (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER), (0, 0, 0, 0))
    if alpha <= 0.0:
        return img
    # Its AURA: a cold green-blue bloom.
    # (warped as its body is, about its foot)
    fy = cy + hem * 0.95
    ax0, ax1 = cx - (lam1 + 8) * eig_x, cx + (lam1 + 8) * eig_x
    ay0, ay1 = fy - (fy - (cy - lam2 - 8)) * eig_y, fy + 4
    _glow(img, lambda g: g.ellipse((*_s((ax0, ay0)), *_s((ax1, ay1))), fill=_with_alpha((120, 220, 210, 255), 0.22 * alpha * min(1.0, eig_x * eig_y * 3))), 7.0)
    body = Image.new("RGBA", img.size, (0, 0, 0, 0))
    outline = _shroud_outline(cx, cy, lam1, lam2, hem, phase)
    # The SHROUD: translucent cloth shaded from a pale lit crown to a cold
    # blue-violet at the hem, lit along its left rim.
    xs, ys = _grid_xy(img.size)
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).polygon([_s(p) for p in outline], fill=255)  # raw-draw-ok: an L mask has no alpha to composite
    t = np.clip((ys - (cy - lam2)) / (lam2 + hem), 0, 1)[..., None]
    top, bottom = np.array([236, 246, 250], np.float32), np.array([96, 110, 168], np.float32)
    rgb = top * (1 - t) + bottom * t
    side = np.clip((xs - cx) / (lam1 * 1.2), -1, 1)[..., None]
    rgb = rgb * (1.0 - 0.18 * np.clip(side, 0, 1))
    a = np.asarray(m, np.float32) * (0.92 - 0.25 * t[..., 0])
    body.alpha_composite(Image.fromarray(np.dstack([np.clip(rgb, 0, 255), a]).astype(np.uint8), "RGBA"))
    _draw_eigen_grid(body, cx, cy, lam1, lam2, 0.9)
    d = blending_draw(body)
    d.line([_s(p) for p in outline + [outline[0]]], fill=OUTLINE, width=int(1.4 * SUPER), joint="curve")
    d.line([_s(p) for p in outline[3:22]], fill=(250, 255, 255, 230), width=int(0.8 * SUPER), joint="curve")
    _draw_eyes(body, cx, cy, lam1, lam2, squint)
    # The hem dissolves into mist.
    fade = np.clip(1.0 - (ys - (cy + hem * 0.55)) / (hem * 0.45), 0.15, 1.0)
    body.putalpha(Image.fromarray((np.asarray(body.getchannel("A"), np.float32) * fade).astype(np.uint8)))
    def mist(g):
        for k in range(5):
            x = cx - lam1 * 0.7 + k * lam1 * 0.35 + 2 * math.sin(phase + k)
            g.line([_s((x + 2 * math.sin(j + phase + k), cy + hem * 0.6 + j * 4)) for j in range(5)], fill=_with_alpha((170, 220, 230, 255), 0.35), width=int(4 * SUPER), joint="curve")
    _glow(body, mist, 2.0)
    # The WARP: stretch the body by its eigenvalues about its foot.
    foot = (cx, cy + hem * 0.95)

    def warp(p: Point) -> Point:
        return (foot[0] + (p[0] - foot[0]) * eig_x, foot[1] + (p[1] - foot[1]) * eig_y)

    if eig_x != 1.0 or eig_y != 1.0:
        W, H = body.size
        scaled = body.resize((max(1, int(W * eig_x)), max(1, int(H * eig_y))), Image.Resampling.LANCZOS)
        fx, fy = foot[0] * SUPER, foot[1] * SUPER
        warped = Image.new("RGBA", body.size, (0, 0, 0, 0))
        warped.paste(scaled, (int(round(fx - fx * eig_x)), int(round(fy - fy * eig_y))), scaled)
        body = warped
    up_root = warp((cx - lam1 * 0.15, cy - lam2 * 0.75))
    side_root = warp((cx + lam1 * 0.9, cy + lam2 * 0.35))
    if arm2 > 0.0:
        _draw_eigen_arm(body, up_root, (up_root[0], up_root[1] - arm2 * eig_y), glow)
    if arm1 > 0.0:
        _draw_eigen_arm(body, side_root, (side_root[0] + arm1 * eig_x, side_root[1]), glow)
    # The arms light the shroud near their roots.
    px = np.asarray(body, np.float32)
    for (lx, ly) in (side_root, up_root):
        f = np.exp(-((xs - lx) ** 2 + (ys - ly) ** 2) / (12.0 ** 2)) * 0.35 * glow
        px[..., :3] = np.clip(px[..., :3] + f[..., None] * np.array(AXIS_GLOW[:3], np.float32) * (px[..., 3:] / 255.0), 0, 255)
    body = Image.fromarray(px.astype(np.uint8), "RGBA")
    # Motes drifting up off it.
    rng = np.random.default_rng(2)
    d = blending_draw(body)
    for _ in range(8):
        x, y, ph = cx - lam1 + rng.random() * lam1 * 2, cy - lam2 + rng.random() * (lam2 + hem), rng.random()
        yy = y - ((phase / math.tau + ph) % 1.0) * 14
        d.ellipse((*_s((x - 0.8, yy - 0.8)), *_s((x + 0.8, yy + 0.8))), fill=(220, 255, 240, 200))
    if alpha < 1.0:
        body.putalpha(body.getchannel("A").point(lambda v: int(v * alpha)))
    img.alpha_composite(body)
    return img


def _render_frame(animation: str, frame_index: int, nframes: int) -> Image.Image:
    t = frame_index / max(1, nframes)
    u = frame_index / max(1, nframes - 1)
    cx, cy = CENTRE
    bob = math.sin(t * math.tau) * 2.0
    breathe = math.sin(t * math.tau)
    # Every row is the same body under a different WARP: its two
    # eigenvalues (across, up), 1 and 1 at rest; the arms are the unit axes
    # under the same warp, so they always agree with the shape.
    args = dict(cx=cx, cy=cy + bob, lam1=MAJOR, lam2=MINOR, hem=HEM_DROP, phase=t * math.tau, arm1=UNIT_ARM, arm2=UNIT_ARM,
                glow=0.7 + 0.3 * breathe, squint=0.0, alpha=1.0, eig_x=1.0 + 0.04 * breathe, eig_y=1.0 - 0.04 * breathe)
    if animation == "walk":
        args.update(cx=cx + 1.5 * math.sin(t * math.tau), phase=t * math.tau * 2.0, eig_x=1.08 + 0.04 * breathe, eig_y=0.95)
    elif animation == "attack_side":
        # Wind up (it squeezes across, swells up), then lance: across grows.
        if u < 0.4:
            k = u / 0.4
            args.update(eig_x=1.0 - 0.25 * k, eig_y=1.0 + 0.2 * k, glow=0.7 + 0.3 * k, squint=0.5 * k)
        else:
            k = math.sin(min(1.0, (u - 0.4) / 0.35) * math.pi * 0.5) * (1.0 - max(0.0, (u - 0.75) / 0.25) * 0.7)
            args.update(eig_x=1.0 + 1.2 * k, eig_y=1.0 - 0.3 * k, glow=1.0, squint=0.5)
    elif animation == "hurt":
        jolt = (1.0 - u)
        args.update(eig_x=1.0 + 0.3 * jolt, eig_y=1.0 - 0.3 * jolt, cx=cx - 3.0 * jolt, squint=0.9, glow=0.4)
    elif animation == "block":
        # It rears along its vertical eigenvector to wall off a jump: up to
        # three times as tall (the larger eigenvalue), a little wider; it
        # holds, quivering, then settles.
        if u <= 0.35:
            k = math.sin(u / 0.35 * math.pi * 0.5)
        elif u <= 0.7:
            k = 1.0
        else:
            k = 1.0 - (u - 0.7) / 0.3
        quiver = 0.04 * math.sin(frame_index * 2.9) * (1.0 if 0.35 < u <= 0.7 else 0.0)
        args.update(eig_y=1.0 + 2.0 * k + quiver, eig_x=1.0 + 0.2 * k, glow=0.7 + 0.3 * k, squint=0.15, cy=cy)
    elif animation == "death":
        # Rank collapse: the vertical eigenvalue goes to zero (a line), then
        # the horizontal one (a point).
        k2 = min(1.0, u / 0.5)
        k1 = max(0.0, (u - 0.5) / 0.5)
        args.update(eig_y=max(0.03, 1.0 - k2), eig_x=max(0.03, 1.0 - k1), squint=1.0, glow=1.0 - k1, cy=cy,
                    alpha=1.0 - max(0.0, (u - 0.85) / 0.15))
    return _draw_ghost(**args).resize(FRAME_SIZE, Image.Resampling.LANCZOS)


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
    return [
        outputs[key]
        for key in ("spritesheet", "yaml", "ron", "actor", "preview", "canonical", "canonical_transparent")
    ]


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
