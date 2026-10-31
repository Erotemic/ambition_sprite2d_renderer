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

from PIL import Image, ImageChops, ImageFilter

from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "eigenghost"
FRAME_SIZE = (128, 128)
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
CENTRE = (60.0, 58.0)
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


def _draw_eigen_grid(layer: Image.Image, cx: float, cy: float, lam1: float, lam2: float, alpha: float) -> None:
    """Faint lines inside the shroud: the unit grid it has transformed,
    stretched along its axes (a haunting of graph paper)."""
    d = blending_draw(layer)
    for k in (-1, 0, 1):
        x = cx + k * lam1 * 0.42
        d.line([_s((x, cy - lam2 * 0.7)), _s((x, cy + lam2 * 1.3))], fill=_with_alpha(GRID, alpha), width=SUPER)
        y = cy + k * lam2 * 0.42 + lam2 * 0.3
        d.line([_s((cx - lam1 * 0.8, y)), _s((cx + lam1 * 0.8, y))], fill=_with_alpha(GRID, alpha), width=SUPER)


def _draw_eigen_arm(layer: Image.Image, start: Point, end: Point, glow: float) -> None:
    """One EIGENVECTOR ARM: a glowing arrow from the shroud along its axis,
    its head a triangle."""
    halo = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    hd = blending_draw(halo)
    hd.line([_s(start), _s(end)], fill=_with_alpha(AXIS_GLOW, 0.55 * glow), width=int(5 * SUPER))
    halo = halo.filter(ImageFilter.GaussianBlur(2.2 * SUPER))
    layer.alpha_composite(halo)
    d = blending_draw(layer)
    d.line([_s(start), _s(end)], fill=AXIS_CORE, width=int(1.8 * SUPER))
    ang = math.atan2(end[1] - start[1], end[0] - start[0])
    size = 5.0
    tip = (end[0] + math.cos(ang) * size, end[1] + math.sin(ang) * size)
    left = (end[0] + math.cos(ang + 2.3) * size * 0.8, end[1] + math.sin(ang + 2.3) * size * 0.8)
    right = (end[0] + math.cos(ang - 2.3) * size * 0.8, end[1] + math.sin(ang - 2.3) * size * 0.8)
    d.polygon([_s(tip), _s(left), _s(right)], fill=AXIS_CORE, outline=OUTLINE)


def _draw_eyes(layer: Image.Image, cx: float, cy: float, lam1: float, lam2: float, squint: float) -> None:
    """Two hollow EYES, looking right, set in the upper shroud."""
    d = blending_draw(layer)
    for dx in (0.05, 0.5):
        ex, ey = cx + lam1 * dx, cy - lam2 * 0.2
        h = 5.2 * (1.0 - squint) + 0.8
        d.ellipse((*_s((ex - 3.4, ey - h)), *_s((ex + 3.4, ey + h))), fill=EYE)


def _draw_ghost(cx: float, cy: float, lam1: float, lam2: float, hem: float, phase: float,
                arm1: float, arm2: float, glow: float, squint: float, alpha: float) -> Image.Image:
    img = Image.new("RGBA", (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER), (0, 0, 0, 0))
    if alpha <= 0.0:
        return img
    body = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = blending_draw(body)
    outline = [_s(p) for p in _shroud_outline(cx, cy, lam1, lam2, hem, phase)]
    d.polygon(outline, fill=SHROUD)
    # A cold shade down its far side (the light is from the upper left).
    shade = [_s(p) for p in _shroud_outline(cx + lam1 * 0.35, cy + 2, lam1 * 0.7, lam2 * 0.9, hem * 0.95, phase)]
    shade_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    blending_draw(shade_layer).polygon(shade, fill=_with_alpha(SHROUD_SHADE, 0.55))
    # The shade stays inside the shroud.
    shade_layer.putalpha(ImageChops.darker(shade_layer.getchannel("A"), body.getchannel("A")))
    body.alpha_composite(shade_layer)
    _draw_eigen_grid(body, cx, cy, lam1, lam2, 0.8)
    d = blending_draw(body)
    d.line(outline + [outline[0]], fill=OUTLINE, width=int(1.6 * SUPER), joint="curve")
    _draw_eyes(body, cx, cy, lam1, lam2, squint)
    # The arms: lambda-1 out to the right (its facing), lambda-2 straight up.
    if arm2 > 0.0:
        _draw_eigen_arm(body, (cx - lam1 * 0.15, cy - lam2 * 0.75), (cx - lam1 * 0.15, cy - lam2 * 0.75 - arm2), glow)
    if arm1 > 0.0:
        _draw_eigen_arm(body, (cx + lam1 * 0.9, cy + lam2 * 0.35), (cx + lam1 * 0.9 + arm1, cy + lam2 * 0.35), glow)
    if alpha < 1.0:
        a = body.getchannel("A").point(lambda v: int(v * alpha))
        body.putalpha(a)
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
