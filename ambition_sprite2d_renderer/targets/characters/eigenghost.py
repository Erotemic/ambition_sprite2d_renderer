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
out: lambda-1 grows), ``hurt`` (its eigenvalues jolt apart) and ``death``
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
FRAME_SIZE = (144, 144)
SUPER = 4
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 120),
    ("walk", 8, 100),
    ("attack_side", 8, 70),
    ("hurt", 3, 90),
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
CENTRE = (66.0, 66.0)
MAJOR = 24.0
MINOR = 19.0
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
        h = 4.6 * (1.0 - squint) + 1.0
        inner = ex + 3.6 * (1 if side < 0 else -1)
        hollow = [(ex - 4.0, ey - h * 0.4 - (1.6 if side > 0 else 0.0) * (1 - squint)), (ex + 4.0, ey - h * 0.4 - (1.6 if side < 0 else 0.0) * (1 - squint)),
                  (ex + 3.4, ey + h * 0.8), (ex, ey + h), (ex - 3.4, ey + h * 0.8)]
        d.polygon([_s(p) for p in hollow], fill=EYE)
        _glow(layer, lambda g, ex=ex, ey=ey: g.ellipse((*_s((ex - 2.2, ey - 1.0)), *_s((ex + 2.2, ey + 2.6))), fill=_with_alpha(AXIS_GLOW, 0.8 * (1 - squint * 0.6))), 1.2)
        d = blending_draw(layer)
        d.ellipse((*_s((ex - 1.0, ey + 0.2)), *_s((ex + 1.0, ey + 2.0))), fill=_with_alpha(AXIS_CORE, 1 - squint * 0.5))


def _draw_ghost(cx: float, cy: float, lam1: float, lam2: float, hem: float, phase: float,
                arm1: float, arm2: float, glow: float, squint: float, alpha: float) -> Image.Image:
    img = Image.new("RGBA", (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER), (0, 0, 0, 0))
    if alpha <= 0.0:
        return img
    # Its AURA: a cold green-blue bloom.
    _glow(img, lambda g: g.ellipse((*_s((cx - lam1 - 8, cy - lam2 - 8)), *_s((cx + lam1 + 8, cy + hem))), fill=_with_alpha((120, 220, 210, 255), 0.22 * alpha)), 7.0)
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
    if arm2 > 0.0:
        _draw_eigen_arm(body, (cx - lam1 * 0.15, cy - lam2 * 0.75), (cx - lam1 * 0.15, cy - lam2 * 0.75 - arm2), glow)
    if arm1 > 0.0:
        _draw_eigen_arm(body, (cx + lam1 * 0.9, cy + lam2 * 0.35), (cx + lam1 * 0.9 + arm1, cy + lam2 * 0.35), glow)
    # The arms light the shroud near their roots.
    px = np.asarray(body, np.float32)
    for (lx, ly) in ((cx + lam1 * 0.9, cy + lam2 * 0.35), (cx - lam1 * 0.15, cy - lam2 * 0.75)):
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
    args = dict(cx=cx, cy=cy + bob, lam1=MAJOR + 1.2 * breathe, lam2=MINOR - 1.0 * breathe, hem=HEM_DROP,
                phase=t * math.tau, arm1=12.0, arm2=9.0, glow=0.7 + 0.3 * breathe, squint=0.0, alpha=1.0)
    if animation == "walk":
        args.update(cx=cx + 1.5 * math.sin(t * math.tau), lam1=MAJOR + 2.0 + 1.5 * breathe, lam2=MINOR - 1.5,
                    phase=t * math.tau * 2.0, arm1=14.0)
    elif animation == "attack_side":
        # Wind up (it squeezes along lambda-1), then lance: lambda-1 grows.
        if u < 0.4:
            k = u / 0.4
            args.update(lam1=MAJOR - 5.0 * k, lam2=MINOR + 3.0 * k, arm1=12.0 - 6.0 * k, glow=0.7 + 0.3 * k, squint=0.5 * k)
        else:
            k = math.sin(min(1.0, (u - 0.4) / 0.35) * math.pi * 0.5) * (1.0 - max(0.0, (u - 0.75) / 0.25) * 0.7)
            args.update(lam1=MAJOR + 6.0 * k, lam2=MINOR - 4.0 * k, arm1=12.0 + 26.0 * k, glow=1.0, squint=0.5)
    elif animation == "hurt":
        jolt = (1.0 - u)
        args.update(lam1=MAJOR + 5.0 * jolt, lam2=MINOR - 5.0 * jolt, cx=cx - 3.0 * jolt, squint=0.9, glow=0.4, arm1=8.0, arm2=6.0)
    elif animation == "death":
        # Rank collapse: lambda-2 goes to zero (a line), then lambda-1 (a point).
        k2 = min(1.0, u / 0.5)
        k1 = max(0.0, (u - 0.5) / 0.5)
        args.update(lam2=max(0.6, MINOR * (1.0 - k2)), hem=HEM_DROP * (1.0 - k2) + 1.0, lam1=max(0.6, MAJOR * (1.0 - k1)),
                    arm2=9.0 * (1.0 - k2), arm1=12.0 * (1.0 - k1), squint=1.0, glow=1.0 - k1,
                    cy=cy + 30.0 * k2, alpha=1.0 - max(0.0, (u - 0.85) / 0.15))
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
