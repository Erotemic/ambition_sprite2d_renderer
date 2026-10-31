"""The Spectral Perturbation: a floating spectral creature of the haunted
floors of Hylbert's Hotel (the Math dimension), Jon, 2026-10-31, with a
concept sheet. An orchid, a manta and a jellyfish at once: a violet-cyan
CORE among four articulated EIGEN-SHARDS (blade-like petals), a tilted,
turning HALO, a DORSAL CREST, SHELL PLATES and flowing RIBBON tendrils. Its
nearly degenerate modes make it unstable: a small disturbance and it
reconfigures, all at once and committed.

A PAPER DOLL: every part is its own drawing, posed from one joint table
(``Pose``) per frame. Layering, back to front: ribbons and stabilizer fins,
the halo's far half, the rear shell plate, the lower shards, the core, the
upper shards, the front shell plate, the dorsal crest, the halo's near half,
then effects (lunge streaks, the split's second lobe, decoherence motes).

Rows: ``idle`` 8 (it hovers, the halo turns); ``walk`` 8 (a drifting bank);
``attack_side`` 14, the core lunge (telegraph 0-4: the ring tilts, the
shards draw in, the core flares; active 5-8: it stretches into a committed
dart, streaking forward; recovery 9-13: overextended, shards splayed, the
ring misaligned: the punish window); ``split`` 10, the mode split (the core
flares double-lobed, then two lobes diverge up and down); ``hurt`` 3;
``death`` 10 (eigenmode decoherence: the ring cracks, the shards decouple
and drift, it dissolves into fading contours and motes).

Facing right; it floats, its lowest ribbon tip near the canvas foot. No drop
shadow.
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

TARGET_NAME = "spectral_perturbation"
FRAME_SIZE = (176, 176)
SUPER = 4
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 120),
    ("walk", 8, 110),
    ("attack_side", 14, 60),
    ("split", 10, 70),
    ("hurt", 3, 90),
    ("death", 10, 110),
]

OUTLINE: RGBA = (26, 12, 42, 255)
PALE: RGBA = (226, 214, 246, 225)
PALE_SHADE: RGBA = (168, 146, 208, 225)
VIOLET: RGBA = (150, 70, 224, 255)
MAGENTA: RGBA = (226, 92, 206, 255)
CYAN: RGBA = (112, 242, 240, 255)
WHITE: RGBA = (246, 250, 255, 255)
CORE_DARK: RGBA = (70, 24, 120, 255)


def _a(c: RGBA, a: float) -> RGBA:
    return (c[0], c[1], c[2], int(max(0.0, min(1.0, a)) * c[3]))


def _s(p: Point) -> Tuple[float, float]:
    return (p[0] * SUPER, p[1] * SUPER)


def _polar(c: Point, deg: float, r: float) -> Point:
    a = math.radians(deg)
    return (c[0] + math.cos(a) * r, c[1] + math.sin(a) * r)


@dataclass(frozen=True)
class Pose:
    """One frame's joint table. Shard angles are degrees (0 = its facing,
    right; y down), lengths in frame pixels."""

    centre: Point = (84.0, 74.0)
    upper: Tuple[float, float] = (-22.0, -158.0)  # upper right, upper left
    lower: Tuple[float, float] = (34.0, 146.0)  # lower right, lower left
    shard_len: Tuple[float, float, float, float] = (48.0, 48.0, 34.0, 34.0)
    halo_tilt: float = -14.0
    halo_spin: float = 0.0
    halo_crack: float = 0.0
    crest: float = -90.0
    core_glow: float = 0.7
    core_lobes: float = 0.0
    stretch: float = 1.0  # along its facing (the lunge's dart)
    ribbon_phase: float = 0.0
    ribbon_back: float = 0.0  # ribbons swept back
    streak: float = 0.0
    split: float = 0.0
    decohere: float = 0.0
    alpha: float = 1.0


def _xf(pose: Pose, p: Point) -> Point:
    """Stretch a point about the centre along its facing (the dart)."""
    c = pose.centre
    return (c[0] + (p[0] - c[0]) * pose.stretch, c[1] + (p[1] - c[1]) / math.sqrt(pose.stretch))


def _glow(layer: Image.Image, fn, blur: float) -> None:
    g = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    fn(blending_draw(g))
    layer.alpha_composite(g.filter(ImageFilter.GaussianBlur(blur * SUPER)))


# --- parts ------------------------------------------------------------------------


def draw_ribbon_tails(layer: Image.Image, pose: Pose) -> None:
    """RIBBON TAILS: four long translucent tendrils flowing down and back,
    waving out of phase, magenta fading to cyan."""
    c = pose.centre
    d = blending_draw(layer)
    for k, (dx, length, colour) in enumerate(((-10, 58, MAGENTA), (-3, 70, CYAN), (4, 64, MAGENTA), (11, 50, VIOLET))):
        pts = []
        for j in range(16):
            t = j / 15.0
            sweep = -pose.ribbon_back * 40.0 * t * t
            x = c[0] + dx + 7.0 * math.sin(t * 4.0 + pose.ribbon_phase + k * 1.4) * t + sweep
            y = c[1] + 10 + length * t * (1.0 - 0.4 * pose.ribbon_back)
            pts.append(_xf(pose, (x, y)))
        _glow(layer, lambda g, pts=pts, colour=colour: g.line([_s(p) for p in pts], fill=_a(colour, 0.6), width=int(4 * SUPER), joint="curve"), 1.2)
        d.line([_s(p) for p in pts], fill=_a(colour, 0.85), width=int(1.6 * SUPER), joint="curve")
    # The STABILIZER FINS: two small slivers either side of the tails.
    for side in (-1, 1):
        base = (c[0] + side * 6, c[1] + 14)
        fin = [base, (base[0] + side * 8, base[1] + 14), (base[0] + side * 2, base[1] + 26)]
        d.polygon([_s(_xf(pose, p)) for p in fin], fill=_a(PALE_SHADE, 0.8), outline=OUTLINE)


def _halo_points(pose: Pose, near: bool) -> List[List[Point]]:
    """The HALO's ellipse, tilted, as runs of points on its near or far half
    (a crack opens gaps in it)."""
    c = (pose.centre[0] - 2, pose.centre[1] - 12)
    rx, ry = 54.0, 13.0
    tilt = math.radians(pose.halo_tilt)
    runs: List[List[Point]] = []
    run: List[Point] = []
    for k in range(73):
        a = math.radians(k * 5.0)
        front = math.sin(a) > 0
        gap = pose.halo_crack > 0 and (k % 12) < int(pose.halo_crack * 6)
        if front != near or gap:
            if run:
                runs.append(run)
                run = []
            continue
        x, y = math.cos(a) * rx, math.sin(a) * ry
        run.append((c[0] + x * math.cos(tilt) - y * math.sin(tilt), c[1] + x * math.sin(tilt) + y * math.cos(tilt)))
    if run:
        runs.append(run)
    return runs


def draw_halo(layer: Image.Image, pose: Pose, near: bool) -> None:
    """The HALO RING (its near or far half): a cyan band with magenta glitch
    dashes, a bright spark running round it with its spin."""
    alpha = 1.0 if near else 0.6
    runs = [[_xf(pose, p) for p in run] for run in _halo_points(pose, near)]
    for run in runs:
        if len(run) < 2:
            continue
        _glow(layer, lambda g, run=run: g.line([_s(p) for p in run], fill=_a(CYAN, 0.6 * alpha), width=int(4 * SUPER), joint="curve"), 1.4)
        blending_draw(layer).line([_s(p) for p in run], fill=_a(WHITE, 0.9 * alpha), width=int(1.2 * SUPER), joint="curve")
    d = blending_draw(layer)
    flat = [p for run in runs for p in run]
    for k in range(0, len(flat), 7):
        p = flat[k]
        d.line([_s(p), _s((p[0] + 5, p[1] - 1))], fill=_a(MAGENTA, 0.8 * alpha), width=int(1.4 * SUPER))
    if near and flat:
        spark = flat[int((pose.halo_spin % 1.0) * (len(flat) - 1))]
        _glow(layer, lambda g: g.ellipse((*_s((spark[0] - 3, spark[1] - 3)), *_s((spark[0] + 3, spark[1] + 3))), fill=WHITE), 1.0)


def _blade(base: Point, deg: float, length: float, width: float) -> List[Point]:
    """A curved blade: a lens from its base to its tip, its far edge bowed."""
    pts = []
    for k in range(13):
        t = k / 12.0
        p = _polar(base, deg, length * t)
        pts.append(_polar(p, deg - 90, width * math.sin(t * math.pi) * (1.1 - 0.5 * t)))
    for k in range(12, -1, -1):
        t = k / 12.0
        p = _polar(base, deg + 8.0 * t, length * t)
        pts.append(_polar(p, deg + 90, width * 0.45 * math.sin(t * math.pi)))
    return pts


def draw_eigen_shard(layer: Image.Image, pose: Pose, deg: float, length: float, drift: Point = (0.0, 0.0)) -> None:
    """An EIGEN-SHARD: a translucent pale blade with a cyan edge, a violet
    vein and a small spiral of rings (its mode) on it."""
    base = (pose.centre[0] + drift[0], pose.centre[1] + drift[1])
    pts = [_xf(pose, p) for p in _blade(_polar(base, deg, 6.0), deg, length, length * 0.32)]
    d = blending_draw(layer)
    alpha = pose.alpha
    d.polygon([_s(p) for p in pts], fill=_a(PALE, alpha))
    # The far half shaded, the edge lit cyan, the vein violet.
    half = pts[: len(pts) // 2]
    d.line([_s(p) for p in half], fill=_a(CYAN, 0.9 * alpha), width=int(1.4 * SUPER), joint="curve")
    d.line([_s(p) for p in pts + [pts[0]]], fill=_a(OUTLINE, alpha), width=int(1.0 * SUPER), joint="curve")
    vein = [_xf(pose, _polar(base, deg, length * t)) for t in (0.2, 0.9)]
    d.line([_s(p) for p in vein], fill=_a(VIOLET, 0.8 * alpha), width=int(0.8 * SUPER))
    mid = _xf(pose, _polar(_polar(base, deg, length * 0.5), deg - 90, length * 0.08))
    for r in (2.0, 3.6, 5.2):
        d.ellipse((*_s((mid[0] - r, mid[1] - r)), *_s((mid[0] + r, mid[1] + r))), outline=_a(VIOLET, 0.6 * alpha), width=int(0.6 * SUPER))


def draw_shell_plate(layer: Image.Image, pose: Pose, front: bool) -> None:
    """A SHELL PLATE: a small curved carapace over (front) or behind (rear)
    the core, its two horns swept back."""
    c = pose.centre
    sx = 1.0 if front else -1.0
    pts = [(c[0] + sx * 4, c[1] - 12), (c[0] + sx * 16, c[1] - 4), (c[0] + sx * 20, c[1] + 10), (c[0] + sx * 10, c[1] + 4), (c[0] + sx * 6, c[1] + 12)]
    d = blending_draw(layer)
    d.polygon([_s(_xf(pose, p)) for p in pts], fill=_a(PALE_SHADE if not front else PALE, pose.alpha), outline=_a(OUTLINE, pose.alpha))


def draw_core(layer: Image.Image, pose: Pose, offset: Point = (0.0, 0.0), scale: float = 1.0) -> None:
    """The CORE: a violet lens with a white-cyan slit of light, its glow
    pulsing; a split shows two close lobes (near-degenerate modes)."""
    c = (pose.centre[0] + offset[0], pose.centre[1] + offset[1])
    h, w = 18.0 * scale, 10.0 * scale
    lobes = [(0.0, 0.0)] if pose.core_lobes <= 0 else [(0.0, -4.0 * pose.core_lobes), (0.0, 4.0 * pose.core_lobes)]
    for lx, ly in lobes:
        cc = (c[0] + lx, c[1] + ly)
        lens = [_xf(pose, p) for p in ((cc[0], cc[1] - h), (cc[0] + w, cc[1]), (cc[0], cc[1] + h), (cc[0] - w, cc[1]))]
        _glow(layer, lambda g, lens=lens: g.polygon([_s(p) for p in lens], fill=_a(VIOLET, 0.9 * pose.core_glow * pose.alpha)), 4.0 * scale)
        d = blending_draw(layer)
        d.polygon([_s(p) for p in lens], fill=_a(CORE_DARK, pose.alpha), outline=_a(OUTLINE, pose.alpha))
        inner = [_xf(pose, p) for p in ((cc[0], cc[1] - h * 0.7), (cc[0] + w * 0.4, cc[1]), (cc[0], cc[1] + h * 0.7), (cc[0] - w * 0.4, cc[1]))]
        _glow(layer, lambda g, inner=inner: g.polygon([_s(p) for p in inner], fill=_a(CYAN, pose.core_glow * pose.alpha)), 1.5)
        blending_draw(layer).polygon([_s(p) for p in inner], fill=_a(WHITE, (0.5 + 0.5 * pose.core_glow) * pose.alpha))


def draw_dorsal_crest(layer: Image.Image, pose: Pose) -> None:
    """The DORSAL CREST: a tall pale blade rising from the core (the
    silhouette's mark), a thin sliver beside it."""
    base = (pose.centre[0], pose.centre[1] - 12)
    draw_eigen_shard(layer, replace(pose, centre=base), pose.crest, 34.0)
    draw_eigen_shard(layer, replace(pose, centre=base), pose.crest + 22.0, 16.0)


def draw_lunge_streaks(layer: Image.Image, pose: Pose) -> None:
    """The LUNGE STREAKS: violet-cyan speed lines trailing the dart."""
    if pose.streak <= 0:
        return
    c = pose.centre
    for k, dy in enumerate((-10, -3, 4, 11)):
        length = (40 + 12 * (k % 2)) * pose.streak
        _glow(layer, lambda g, dy=dy, length=length, k=k: g.line([_s((c[0] - 18, c[1] + dy)), _s((c[0] - 18 - length, c[1] + dy))],
                                                              fill=_a(CYAN if k % 2 else VIOLET, 0.8), width=int(2.6 * SUPER)), 1.0)


def draw_decoherence(layer: Image.Image, pose: Pose) -> None:
    """DECOHERENCE: fading contour loops and spectral motes where it was."""
    if pose.decohere <= 0:
        return
    c = pose.centre
    rng = np.random.default_rng(3)
    d = blending_draw(layer)
    for k in range(4):
        r = 14 + k * 9 + pose.decohere * 14
        a = (1.0 - pose.decohere) * 0.7 * (1 - k * 0.15)
        _glow(layer, lambda g, r=r, a=a, k=k: g.arc((*_s((c[0] - r, c[1] - r * 0.6)), *_s((c[0] + r, c[1] + r * 0.6))), 20 + k * 40, 220 + k * 40,
                                                   fill=_a(VIOLET if k % 2 else CYAN, a), width=int(1.4 * SUPER)), 0.8)
    for _ in range(24):
        ang, rad = rng.random() * math.tau, 10 + rng.random() * 50 * (0.4 + pose.decohere)
        p = (c[0] + math.cos(ang) * rad, c[1] + math.sin(ang) * rad * 0.7 - pose.decohere * 10)
        d.ellipse((*_s((p[0] - 1, p[1] - 1)), *_s((p[0] + 1, p[1] + 1))), fill=_a(WHITE, 0.8 * (1.0 - pose.decohere * 0.8)))


# --- assembly ---------------------------------------------------------------------


def draw_perturbation(pose: Pose) -> Image.Image:
    img = Image.new("RGBA", (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER), (0, 0, 0, 0))
    drift = pose.decohere * 18.0
    if pose.alpha > 0.02:
        # Its AURA: a soft violet-magenta bloom it floats in.
        c = pose.centre
        _glow(img, lambda g: g.ellipse((*_s((c[0] - 44 * pose.stretch, c[1] - 30)), *_s((c[0] + 44 * pose.stretch, c[1] + 26))),
                                       fill=_a(VIOLET, 0.28 * pose.alpha * (0.6 + 0.4 * pose.core_glow))), 10.0)
        draw_lunge_streaks(img, pose)
        draw_ribbon_tails(img, pose)
        draw_halo(img, pose, near=False)
        draw_shell_plate(img, pose, front=False)
        draw_eigen_shard(img, pose, pose.lower[0], pose.shard_len[2], (drift, drift))
        draw_eigen_shard(img, pose, pose.lower[1], pose.shard_len[3], (-drift, drift))
        draw_eigen_shard(img, pose, pose.upper[0], pose.shard_len[0], (drift, -drift))
        draw_eigen_shard(img, pose, pose.upper[1], pose.shard_len[1], (-drift, -drift))
        draw_dorsal_crest(img, pose)
        draw_shell_plate(img, pose, front=True)
        draw_core(img, pose)
        draw_halo(img, pose, near=True)
    if pose.split > 0:
        # The mode split: the core's second lobe peels away down and forward.
        draw_core(img, pose, offset=(30 * pose.split, 22 * pose.split), scale=0.8)
        draw_core(img, pose, offset=(30 * pose.split, -22 * pose.split), scale=0.8)
    draw_decoherence(img, pose)
    if pose.alpha < 1.0:
        a = np.asarray(img.getchannel("A"), np.float32) * max(0.0, pose.alpha) ** 0.5 if pose.decohere <= 0 else np.asarray(img.getchannel("A"), np.float32)
        img.putalpha(Image.fromarray(a.astype(np.uint8)))
    return img


def _pose_for(animation: str, i: int, n: int) -> Pose:
    t = i / max(1, n)
    u = i / max(1, n - 1)
    w = math.sin(t * math.tau)
    base = Pose(centre=(84.0, 74.0 + 2.0 * w), halo_spin=t, ribbon_phase=t * math.tau,
                upper=(-22.0 + 5 * w, -158.0 - 5 * w), lower=(34.0 - 4 * w, 146.0 + 4 * w), core_glow=0.65 + 0.2 * w)
    if animation == "idle":
        return base
    if animation == "walk":
        return replace(base, halo_tilt=-24.0 + 6 * w, centre=(84.0 + 3 * w, 74.0), ribbon_back=0.35,
                       upper=(-30.0, -150.0), lower=(46.0, 132.0), crest=-80.0)
    if animation == "attack_side":
        if i <= 4:  # telegraph: the ring tilts, the shards draw in, the core flares
            k = i / 4.0
            return replace(base, halo_tilt=-14.0 - 24.0 * k, upper=(-38.0 + 18 * k, -142.0 - 18 * k), lower=(40.0 - 18 * k, 140.0 + 18 * k),
                           shard_len=(40 - 6 * k, 40 - 6 * k, 30 - 4 * k, 30 - 4 * k), core_glow=0.7 + 0.3 * k)
        if i <= 8:  # active: a committed dart, shards swept back, streaking
            k = (i - 5) / 3.0
            return replace(base, centre=(80.0 + 14 * k, 74.0), stretch=1.55, upper=(-160.0, -170.0), lower=(160.0, 170.0),
                           shard_len=(44, 40, 36, 32), crest=-150.0, halo_tilt=-6.0, ribbon_back=1.0, streak=1.0, core_glow=1.0)
        k = (i - 9) / 4.0  # recovery: overextended, splayed, the ring askew
        return replace(base, centre=(94.0 - 10 * k, 76.0), upper=(-10.0 - 28 * k, -170.0 + 28 * k), lower=(70.0 - 30 * k, 110.0 + 30 * k),
                       halo_tilt=26.0 - 40 * k, crest=-60.0 - 30 * k, core_glow=0.4 + 0.3 * k, ribbon_back=0.6 * (1 - k))
    if animation == "split":
        if i <= 3:  # the telegraph: a double-lobed flare
            k = i / 3.0
            return replace(base, core_lobes=k, core_glow=0.8 + 0.2 * k, upper=(-60.0, -120.0), lower=(60.0, 120.0), halo_tilt=-14 - 10 * k)
        k = (i - 4) / 5.0  # two lobes diverge along committed paths
        return replace(base, core_lobes=1.0, split=k, core_glow=1.0, upper=(-70.0, -110.0), lower=(70.0, 110.0), halo_tilt=-24 + 20 * k)
    if animation == "hurt":
        k = 1.0 - u
        return replace(base, centre=(80.0 - 4 * k, 74.0), halo_tilt=30.0 * k - 14, upper=(-20.0 - 30 * k, -160.0 + 30 * k),
                       lower=(60.0, 120.0), core_glow=1.0 * k + 0.4, halo_crack=0.3 * k)
    if animation == "death":
        crack = min(1.0, u / 0.3)
        dec = max(0.0, (u - 0.25) / 0.75)
        return replace(base, halo_crack=crack, decohere=dec, alpha=1.0 - dec, core_glow=1.0 - dec * 0.8,
                       upper=(-38.0 - 30 * dec, -142.0 + 30 * dec), lower=(40.0 + 30 * dec, 140.0 - 30 * dec))
    raise ValueError(f"{TARGET_NAME}: no row {animation!r}")


def _render_frame(animation: str, frame_index: int, nframes: int) -> Image.Image:
    return draw_perturbation(_pose_for(animation, frame_index, nframes)).resize(FRAME_SIZE, Image.Resampling.LANCZOS)


ACTOR_METADATA = {
    "actor": {"character_id": TARGET_NAME, "display_name": "Spectral Perturbation"},
    "body": {
        "body_plan": "Amorphous",
        "body_kind": "Entity",
        "mass_class": "Light",
        "traits": ["spectral", "floating", "math", "eigen"],
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
