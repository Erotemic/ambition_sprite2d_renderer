"""The Shift Operator: a ghostly housekeeper of the haunted floors of
Hylbert's Hotel (the Math dimension; Jon, 2026-10-31: "build another enemy
for the region, your choice"). When a new guest arrives at the full hotel,
every guest moves from room n to room n + 1: she is the one who moves them.
Her attack is the SHIFT, a shove that pushes you one room along.

A PAPER DOLL, posed from one joint table (``Pose``) per frame. Parts, back
to front:
- the PLAQUE TRAIL: her hem is not a hem but an endless column of little
  brass room plaques (1, 2, 3, ...) trailing down and away, fading;
- the DRESS: a translucent bell of spectral cloth, shaded from a pale lit
  bodice to a cold teal-violet hem, a rim of light down its back;
- the APRON: a paler panel over it, a "+1" stitched on it in light;
- the FAR ARM, a wisp of sleeve;
- the HEAD: a veiled mob-cap ghost, two hollow eyes glaring under a
  scowling brow, a cold point of light in each;
- the NEAR ARM and the KEY: a great brass skeleton key, its bow a ring
  round an infinity, its bit a staircase of steps; she turns it to shift;
- effects: the SHIFT WAVE (a rank of chevrons, >>>, pushing out ahead of
  the key), motes, an aura.

Rows: ``idle`` 8 (she drifts, the plaques sway), ``walk`` 8 (she glides,
leaning), ``attack_side`` 10 (the key raised and turned (0-3), the shove and
its wave (4-6), a slow recovery, open (7-9)), ``hurt`` 3, ``death`` 8 (the
plaques scatter up, she unravels into "+1" motes).

Facing right; she floats, her trail's last plaque near the canvas foot. No
drop shadow.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from ...authoring.sheet_build import build_sheet
from ambition_sprite2d_renderer.core.draw import blending_draw

RGBA = Tuple[int, int, int, int]
Point = Tuple[float, float]

TARGET_NAME = "shift_operator"
FRAME_SIZE = (236, 236)
SUPER = 4
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 120),
    ("walk", 8, 110),
    ("attack_side", 10, 70),
    ("hurt", 3, 90),
    ("death", 8, 110),
]

OUTLINE: RGBA = (22, 18, 40, 255)
BRASS: RGBA = (214, 168, 84, 255)
BRASS_DARK: RGBA = (130, 92, 40, 255)
TEAL: RGBA = (110, 236, 214, 255)
TEAL_CORE: RGBA = (220, 255, 246, 255)
VIOLET: RGBA = (150, 110, 220, 255)
SOCKET: RGBA = (14, 10, 30, 255)


def _a(c: RGBA, a: float) -> RGBA:
    return (c[0], c[1], c[2], int(max(0.0, min(1.0, a)) * c[3]))


def _s(p: Point) -> Tuple[float, float]:
    return (p[0] * SUPER, p[1] * SUPER)


def _glow(layer: Image.Image, fn, blur: float) -> None:
    g = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    fn(blending_draw(g))
    layer.alpha_composite(g.filter(ImageFilter.GaussianBlur(blur * SUPER)))


_GRID = {}


def _grid(size):
    if size not in _GRID:
        ys, xs = np.mgrid[0 : size[1], 0 : size[0]].astype(np.float32)
        _GRID[size] = (xs / SUPER, ys / SUPER)
    return _GRID[size]


def _fill_gradient(layer: Image.Image, pts: List[Point], c0: RGBA, c1: RGBA, p0: Point, p1: Point) -> None:
    """Fill a polygon with a linear gradient from ``c0`` at ``p0`` to ``c1``
    at ``p1``, each colour's alpha its own (translucent cloth)."""
    xs, ys = _grid(layer.size)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    t = np.clip(((xs - p0[0]) * dx + (ys - p0[1]) * dy) / max(1e-6, dx * dx + dy * dy), 0.0, 1.0)[..., None]
    c = np.asarray(c0, np.float32) * (1 - t) + np.asarray(c1, np.float32) * t
    m = Image.new("L", layer.size, 0)
    ImageDraw.Draw(m).polygon([_s(p) for p in pts], fill=255)  # raw-draw-ok: an L mask has no alpha to composite
    a = np.asarray(m, np.float32) / 255.0 * c[..., 3]
    layer.alpha_composite(Image.fromarray(np.dstack([c[..., :3], a]).astype(np.uint8), "RGBA"))


@dataclass(frozen=True)
class Pose:
    """One frame's joint table (frame pixels; arm angles in degrees from
    straight down, positive toward her facing)."""

    centre: Point = (96.0, 74.0)
    lean: float = 6.0
    sway: float = 0.0
    near_arm: Tuple[float, float] = (40.0, 50.0)
    far_arm: Tuple[float, float] = (-20.0, 30.0)
    key_turn: float = 0.0
    wave: float = -1.0
    glow: float = 0.7
    squint: float = 0.0
    scatter: float = 0.0
    fade: float = 1.0


def _along(p: Point, deg: float, length: float) -> Point:
    a = math.radians(deg)
    return (p[0] + math.sin(a) * length, p[1] + math.cos(a) * length)


# --- parts ------------------------------------------------------------------------


def draw_plaque_trail(layer: Image.Image, pose: Pose, phase: float) -> None:
    """The PLAQUE TRAIL: her hem trails down into an endless column of small
    brass room plaques, 1, 2, 3, ..., each a little smaller and fainter,
    swaying out of step; in death they scatter upward."""
    font = ImageFont.load_default()
    c = pose.centre
    blending_draw(layer).line([_s((c[0] - 4, c[1] + 48)), _s((c[0] - 4, c[1] + 58))], fill=_a(TEAL, 0.6 * pose.fade), width=int(0.6 * SUPER))
    count = 6
    for k in range(count):
        t = k / (count - 1)
        x = c[0] - 4 + 9 * math.sin(phase + k * 0.9) * t + pose.sway * t * 8
        y = c[1] + 62 + k * 17.0 - pose.scatter * (20 + 14 * k)
        x += pose.scatter * (20 * math.sin(k * 2.1))
        w, h = 18.0 * (1 - 0.4 * t), 11.0 * (1 - 0.4 * t)
        alpha = (1.0 - 0.75 * t) * pose.fade * (1.0 - pose.scatter * 0.6)
        tilt = 8 * math.sin(phase * 1.3 + k)
        plate = Image.new("RGBA", (int(w * SUPER * 2), int(h * SUPER * 2)), (0, 0, 0, 0))
        pd = blending_draw(plate)
        pw, ph = plate.size
        pd.rectangle((pw * 0.25, ph * 0.25, pw * 0.75, ph * 0.75), fill=_a(BRASS, alpha), outline=_a(BRASS_DARK, alpha), width=SUPER)
        label = Image.new("L", (24, 12), 0)
        ImageDraw.Draw(label).text((3, 0), str(k + 1), fill=255, font=font)  # raw-draw-ok: an L mask has no alpha to composite
        label = label.resize((int(pw * 0.36), int(ph * 0.42)), Image.Resampling.LANCZOS)
        ink = Image.new("RGBA", label.size, _a(SOCKET, alpha)[:3] + (0,))
        ink.putalpha(label.point(lambda v: int(v * alpha)))
        plate.alpha_composite(ink, (int(pw * 0.36), int(ph * 0.3)))
        plate = plate.rotate(tilt, resample=Image.Resampling.BICUBIC, expand=False)
        layer.alpha_composite(plate, (int(x * SUPER - pw / 2), int(y * SUPER - ph / 2)))
        # A thread of light ties each plaque to the one above.
        if k < count - 1:
            d = blending_draw(layer)
            d.line([_s((x, y + h * 0.4)), _s((x + 9 * math.sin(phase + (k + 1) * 0.9) / (count - 1), y + 18 - h * 0.4))],
                   fill=_a(TEAL, 0.5 * alpha), width=int(0.6 * SUPER))


def draw_dress(layer: Image.Image, pose: Pose, phase: float) -> None:
    """The DRESS: a translucent bell of spectral cloth, lit at the bodice and
    cold at the hem, a rim of light down its back; the APRON over it with a
    "+1" stitched in light."""
    c = pose.centre
    lean = math.radians(pose.lean)
    top = (c[0] + 18 * math.sin(lean), c[1] - 22)
    bell = [(top[0] - 9, top[1]), (top[0] + 9, top[1]), (c[0] + 16, c[1] + 10)]
    for k in range(9):
        t = k / 8.0
        x = c[0] + 26 - 52 * t + 2 * math.sin(phase * 2 + k)
        bell.append((x + pose.sway * 4, c[1] + 50 + (5 if k % 2 else 0) + 2 * math.sin(phase + k)))
    bell.append((c[0] - 18, c[1] + 10))
    _fill_gradient(layer, bell, (232, 244, 250, int(230 * pose.fade)), (90, 120, 170, int(150 * pose.fade)), top, (c[0], c[1] + 56))
    d = blending_draw(layer)
    d.line([_s(p) for p in bell + [bell[0]]], fill=_a(OUTLINE, pose.fade), width=int(1.2 * SUPER), joint="curve")
    back = [bell[0]] + [bell[-1]] + [bell[-2]]
    d.line([_s(p) for p in back], fill=_a(TEAL_CORE, 0.7 * pose.fade), width=int(0.9 * SUPER), joint="curve")
    # Folds of cloth falling to the hem.
    for k in range(3):
        x0 = c[0] - 8 + k * 9
        d.line([_s((x0 + 2, c[1] + 8)), _s((x0 - 2 + k * 2, c[1] + 46))], fill=(60, 80, 130, int(110 * pose.fade)), width=int(1.0 * SUPER))
    # The apron, and its +1.
    apron = [(c[0] - 6, c[1] - 6), (c[0] + 12, c[1] - 6), (c[0] + 16, c[1] + 38), (c[0] - 8, c[1] + 40)]
    _fill_gradient(layer, apron, (250, 252, 255, int(235 * pose.fade)), (170, 200, 220, int(200 * pose.fade)), (c[0], c[1] - 6), (c[0], c[1] + 40))
    d = blending_draw(layer)
    d.polygon([_s(p) for p in apron], outline=_a(OUTLINE, pose.fade))
    m = (c[0] + 4, c[1] + 14)
    plus = lambda g: [g.line([_s((m[0] - 5, m[1])), _s((m[0] - 1, m[1]))], fill=_a(TEAL, pose.fade), width=int(1.2 * SUPER)),
                      g.line([_s((m[0] - 3, m[1] - 2)), _s((m[0] - 3, m[1] + 2))], fill=_a(TEAL, pose.fade), width=int(1.2 * SUPER)),
                      g.line([_s((m[0] + 2, m[1] - 3)), _s((m[0] + 4, m[1] - 4)), _s((m[0] + 4, m[1] + 4))], fill=_a(TEAL, pose.fade), width=int(1.2 * SUPER))]
    _glow(layer, plus, 1.0)
    plus(blending_draw(layer))


def _shoulder(pose: Pose, near: bool) -> Point:
    c = pose.centre
    lean = math.radians(pose.lean)
    return (c[0] + 18 * math.sin(lean) + (8 if near else -8), c[1] - 18)


def draw_arm(layer: Image.Image, pose: Pose, near: bool) -> Point:
    """An ARM: a wisp of translucent sleeve tapering to a pale ghostly hand.
    Returns the hand."""
    sh = _shoulder(pose, near)
    angles = pose.near_arm if near else pose.far_arm
    elbow = _along(sh, angles[0], 14.0)
    hand = _along(elbow, angles[0] + angles[1], 14.0)
    d = blending_draw(layer)
    for colour, w in ((_a(OUTLINE, pose.fade), 6.4), ((214, 232, 244, int(220 * pose.fade)), 4.6)):
        d.line([_s(sh), _s(elbow), _s(hand)], fill=colour, width=int(w * SUPER), joint="curve")
    d.ellipse((*_s((hand[0] - 2.6, hand[1] - 2.6)), *_s((hand[0] + 2.6, hand[1] + 2.6))), fill=(236, 246, 252, int(240 * pose.fade)), outline=_a(OUTLINE, pose.fade))
    return hand


def draw_head(layer: Image.Image, pose: Pose) -> None:
    """The HEAD: a veiled mob-cap ghost, a frill round the cap, the veil
    falling behind; two hollow eyes glaring under a scowl, a cold point of
    light in each."""
    c = pose.centre
    lean = math.radians(pose.lean)
    h = (c[0] + 22 * math.sin(lean) + 2, c[1] - 34)
    d = blending_draw(layer)
    veil = [(h[0] - 10, h[1] - 6), (h[0] - 16, h[1] + 12), (h[0] - 8, h[1] + 10), (h[0] - 2, h[1] + 4)]
    d.polygon([_s(p) for p in veil], fill=(190, 210, 236, int(170 * pose.fade)), outline=_a(OUTLINE, pose.fade))
    d.ellipse((*_s((h[0] - 10, h[1] - 10)), *_s((h[0] + 10, h[1] + 10))), fill=(236, 246, 252, int(245 * pose.fade)), outline=_a(OUTLINE, pose.fade), width=int(1.2 * SUPER))
    cap = [(h[0] - 12, h[1] - 6)] + [(h[0] - 12 + 24 * k / 8, h[1] - 9 - 5 * math.sin(math.pi * k / 8) - (1.2 if k % 2 else 0)) for k in range(9)] + [(h[0] + 12, h[1] - 6)]
    d.polygon([_s(p) for p in cap], fill=(250, 252, 255, int(250 * pose.fade)), outline=_a(OUTLINE, pose.fade))
    for side, ex in ((-1, h[0] - 0.5), (1, h[0] + 6.0)):
        ey = h[1] + 1.0
        inward = 1.0 if side < 0 else -1.0
        open_ = 1.0 - pose.squint
        eye = [(ex + inward * 3.0, ey + 0.8), (ex - inward * 3.2, ey - 2.2 * open_ - 0.3), (ex - inward * 2.2, ey + 1.8 * open_), (ex, ey + 2.8 * open_ + 0.2)]
        d.polygon([_s(p) for p in eye], fill=_a(SOCKET, pose.fade))
        g = (ex - inward * 0.3, ey + 0.6 * open_)
        _glow(layer, lambda gg, g=g: gg.ellipse((*_s((g[0] - 2.2, g[1] - 1.6)), *_s((g[0] + 2.2, g[1] + 1.6))), fill=_a(TEAL, pose.glow * pose.fade)), 1.0)
        d = blending_draw(layer)
        d.ellipse((*_s((g[0] - 0.8, g[1] - 0.6)), *_s((g[0] + 0.8, g[1] + 0.6))), fill=_a(TEAL_CORE, pose.fade))


def draw_key(layer: Image.Image, pose: Pose, hand: Point) -> Point:
    """The KEY: a great brass skeleton key in her hand, held forward: its bow
    a ring round an infinity, its bit a staircase of steps (each room one
    higher). ``key_turn`` turns it (the shift). Returns its tip."""
    turn = math.radians(10 + pose.key_turn)
    fwd = (math.cos(turn), math.sin(turn))
    perp = (-fwd[1], fwd[0])
    bow = (hand[0] - fwd[0] * 6, hand[1] - fwd[1] * 6)
    tip = (hand[0] + fwd[0] * 30, hand[1] + fwd[1] * 30)
    d = blending_draw(layer)
    for colour, w in ((_a(OUTLINE, pose.fade), 3.6), (_a(BRASS, pose.fade), 2.2)):
        d.line([_s(bow), _s(tip)], fill=colour, width=int(w * SUPER))
    d.ellipse((*_s((bow[0] - 6, bow[1] - 6)), *_s((bow[0] + 6, bow[1] + 6))), outline=_a(OUTLINE, pose.fade), width=int(3.4 * SUPER))
    d.ellipse((*_s((bow[0] - 6, bow[1] - 6)), *_s((bow[0] + 6, bow[1] + 6))), outline=_a(BRASS, pose.fade), width=int(2.0 * SUPER))
    for sx in (-1, 1):  # the infinity in the bow
        d.ellipse((*_s((bow[0] + sx * 1.8 - 1.8, bow[1] - 1.4)), *_s((bow[0] + sx * 1.8 + 1.8, bow[1] + 1.4))), outline=_a(BRASS_DARK, pose.fade), width=int(0.7 * SUPER))
    # The bit: a staircase of steps down from the tip.
    steps = [tip]
    for k in range(3):
        a = (tip[0] - fwd[0] * (k * 3.0), tip[1] - fwd[1] * (k * 3.0))
        steps.append((a[0] + perp[0] * (2 + k * 2.2), a[1] + perp[1] * (2 + k * 2.2)))
        steps.append((a[0] - fwd[0] * 3.0 + perp[0] * (2 + k * 2.2), a[1] - fwd[1] * 3.0 + perp[1] * (2 + k * 2.2)))
    steps.append((tip[0] - fwd[0] * 9, tip[1] - fwd[1] * 9))
    d.polygon([_s(p) for p in steps], fill=_a(BRASS, pose.fade), outline=_a(OUTLINE, pose.fade))
    d.line([_s((bow[0] + fwd[0] * 4 - perp[0] * 0.6, bow[1] + fwd[1] * 4 - perp[1] * 0.6)), _s((tip[0] - perp[0] * 0.6, tip[1] - perp[1] * 0.6))],
           fill=_a((250, 220, 150, 255), 0.8 * pose.fade), width=int(0.6 * SUPER))
    return tip


def draw_shift_wave(layer: Image.Image, tip: Point, u: float) -> None:
    """The SHIFT WAVE: a rank of chevrons (>>>) pushing out ahead of the key,
    each a room further on, glowing teal."""
    if u < 0:
        return
    fade = 1.0 - max(0.0, (u - 0.6) / 0.4)
    for k in range(4):
        x = tip[0] + 5 + k * 9 + u * 12
        h = 9.0 - k * 1.2
        pts = [(x - 4, tip[1] - h), (x + 3, tip[1]), (x - 4, tip[1] + h)]
        a = fade * (1.0 - k * 0.18)
        _glow(layer, lambda g, pts=pts, a=a: g.line([_s(p) for p in pts], fill=_a(TEAL, a), width=int(4 * SUPER), joint="curve"), 1.6)
        blending_draw(layer).line([_s(p) for p in pts], fill=_a(TEAL_CORE, a), width=int(1.4 * SUPER), joint="curve")


# --- assembly ---------------------------------------------------------------------


def draw_operator(pose: Pose, phase: float) -> Image.Image:
    img = Image.new("RGBA", (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER), (0, 0, 0, 0))
    c = pose.centre
    # Her AURA.
    _glow(img, lambda g: g.ellipse((*_s((c[0] - 34, c[1] - 50)), *_s((c[0] + 34, c[1] + 60))), fill=_a(TEAL, 0.18 * pose.fade)), 10.0)
    draw_plaque_trail(img, pose, phase)
    if pose.fade > 0.02:
        draw_arm(img, pose, near=False)
        draw_dress(img, pose, phase)
        draw_head(img, pose)
        hand = draw_arm(img, pose, near=True)
        tip = draw_key(img, pose, hand)
        draw_shift_wave(img, tip, pose.wave)
    # Motes: in death, "+1"s drifting up.
    rng = np.random.default_rng(3)
    d = blending_draw(img)
    for _ in range(10 + int(14 * pose.scatter)):
        x, y, ph = c[0] - 40 + rng.random() * 80, c[1] - 20 + rng.random() * 110, rng.random()
        yy = y - ((phase / math.tau + ph) % 1.0) * 16 - pose.scatter * 16
        a = 0.6 * (0.4 + 0.6 * pose.fade) if pose.scatter <= 0 else 0.8 * (1 - pose.scatter * 0.7)
        if pose.scatter > 0:
            d.line([_s((x - 1.5, yy)), _s((x + 1.5, yy))], fill=_a(TEAL_CORE, a), width=int(0.6 * SUPER))
            d.line([_s((x, yy - 1.5)), _s((x, yy + 1.5))], fill=_a(TEAL_CORE, a), width=int(0.6 * SUPER))
        else:
            d.ellipse((*_s((x - 0.8, yy - 0.8)), *_s((x + 0.8, yy + 0.8))), fill=_a(TEAL_CORE, a))
    return img


def _pose_for(animation: str, i: int, n: int) -> Tuple[Pose, float]:
    t = i / max(1, n)
    u = i / max(1, n - 1)
    w = math.sin(t * math.tau)
    base = Pose(centre=(96.0, 74.0 + 2.5 * w), sway=0.4 * w, near_arm=(40.0 + 4 * w, 50.0), glow=0.65 + 0.2 * w)
    if animation == "idle":
        return base, t * math.tau
    if animation == "walk":
        return replace(base, lean=16.0, sway=-0.8, centre=(96.0 + 2 * w, 74.0), near_arm=(55.0, 40.0)), t * math.tau * 1.5
    if animation == "attack_side":
        if i <= 3:  # the key raised and turned back: the tell
            k = i / 3.0
            return replace(base, lean=6.0 - 12 * k, near_arm=(40.0 + 70 * k, 50.0 - 30 * k), key_turn=-60.0 * k, glow=0.7 + 0.3 * k, squint=0.3 * k), t * math.tau
        if i <= 6:  # the shove: the key turns over, the wave goes out
            k = (i - 4) / 2.0
            return replace(base, lean=-6.0 + 26 * k, centre=(96.0 + 8 * k, 74.0), near_arm=(110.0 - 30 * k, 20.0 - 20 * k), key_turn=-60.0 + 70 * k,
                           wave=0.2 + 0.8 * k, glow=1.0, squint=0.4, sway=-1.0), t * math.tau
        k = (i - 7) / 2.0  # open after: leaning out, the key low
        return replace(base, lean=20.0 - 14 * k, centre=(104.0 - 8 * k, 74.0), near_arm=(70.0 - 30 * k, 10.0 + 40 * k), key_turn=30.0 * (1 - k),
                       glow=0.4 + 0.3 * k, wave=1.0 if i == 7 else -1.0), t * math.tau
    if animation == "hurt":
        k = 1.0 - u
        return replace(base, lean=-14.0 * k + 6, centre=(92.0 - 3 * k, 74.0), squint=0.9, glow=1.0, far_arm=(-60.0 * k - 20, 40.0)), t * math.tau
    if animation == "death":
        return replace(base, scatter=u, fade=1.0 - u, squint=1.0, glow=1.0 - u), t * math.tau
    raise ValueError(f"{TARGET_NAME}: no row {animation!r}")


def _render_frame(animation: str, frame_index: int, nframes: int) -> Image.Image:
    pose, phase = _pose_for(animation, frame_index, nframes)
    return draw_operator(pose, phase).resize(FRAME_SIZE, Image.Resampling.LANCZOS)


ACTOR_METADATA = {
    "actor": {"character_id": TARGET_NAME, "display_name": "Shift Operator"},
    "body": {
        "body_plan": "Humanoid",
        "body_kind": "Entity",
        "mass_class": "Light",
        "traits": ["spectral", "ghost", "housekeeper", "math", "floating"],
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
