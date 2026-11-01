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

The HAND itself is the hand generator's (``handgen``: one 3D hand, posed by
joint angles, drawn in its "spectral" style, no wrist of its own); this
module adds what is the Dealer's: the CUFF and its mist, the signet RING on
its ring finger, the DIE GLIMPSE held in its cupped fingers, the RELEASE
sparkle, the shake arcs, an aura and motes, all hung on the hand's
landmarks.

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

from ... import handgen as HG

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
TEAL: RGBA = (110, 240, 220, 255)
VIOLET: RGBA = (176, 120, 255, 255)
LACE: RGBA = (246, 250, 255, 235)
WHITE: RGBA = (250, 252, 255, 255)
BRASS: RGBA = (214, 168, 84, 255)
SLEEVE: RGBA = (36, 22, 58, 255)
GARTER: RGBA = (150, 60, 140, 255)

#: The hand: the generator's default proportions, its spectral look.
SPEC = HG.HandSpec()
STYLE = HG.STYLES["spectral"]


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
    layer.alpha_composite(g.convert("RGBa").filter(ImageFilter.GaussianBlur(blur * SUPER)).convert("RGBA"))


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


def _camera(pose: Pose) -> HG.Camera:
    return HG.Camera(pose.wrist, pose.palm, 0.0 if pose.view == "palm" else 180.0)


def _hand_pose(pose: Pose) -> HG.HandPose:
    return HG.HandPose(pose.curls, pose.thumb)


def _marks(pose: Pose):
    """The hand's landmarks (joints ``<finger>_<i>``, ``_tip``, ``grip``)."""
    return HG.landmarks(SPEC, _hand_pose(pose), _camera(pose))


def _mid_tips(pose: Pose) -> Point:
    marks = _marks(pose)
    tips = [marks[f"{name}_2"] for name in HG.FINGER_NAMES]
    return (sum(p[0] for p in tips) / 4, sum(p[1] for p in tips) / 4)


# --- parts ------------------------------------------------------------------------


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
    m = _mid_tips(pose)
    c = (m[0] - 4, m[1] + 6)
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
    tip = _marks(pose)["middle_tip"]
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
    # Only while its phalanx is on our side of the palm (from the back, a
    # fist tucks it away).
    ring = HG.digits(SPEC, _hand_pose(pose))["ring"]
    mid = (ring.joints[0] + ring.joints[1]) / 2
    side = 1.0 if pose.view == "palm" else -1.0
    if mid[2] * side < -0.25 * SPEC.palm_depth:
        return
    marks = _marks(pose)
    a, b = marks["ring_0"], marks["ring_1"]
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


def draw_shake_arcs(layer: Image.Image, pose: Pose) -> None:
    """SHAKE ARCS: quick curved lines either side of the cupped hand while it
    rattles the die."""
    if pose.die <= 0:
        return
    c = _mid_tips(pose)

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
    # The hand, from the generator: the die glimpse held over the palm,
    # under the fingers that cup it.
    hand = HG.draw_hand(SPEC, _hand_pose(pose), _camera(pose), FRAME_SIZE, STYLE, SUPER, glow=pose.glow, fade=pose.fade, tip_fade=pose.tip_fade,
                        between=lambda layer, _marks, _ss: draw_die_glimpse(layer, pose, phase), wrist="none")
    img.alpha_composite(hand.image)
    draw_ring(img, pose)
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
