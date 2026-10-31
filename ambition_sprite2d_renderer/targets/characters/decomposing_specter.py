"""The Decomposing Specter: a half-zombie, half-ghost bellhop haunting
Hylbert's Hotel (the Math dimension). A former guest whose spectrum is
unravelling: it shambles, then decomposes into its spectral components
(eigenmode ghosts) when defeated. Jon, 2026-10-31, with a concept sheet.

A PAPER DOLL: every part is its own drawing, posed from one joint table
(``Pose``) per frame, so new poses and rows are new numbers, not new art.

Parts (back to front): the SPECTRAL WISPS trailing from its back; the far
LEG and far ARM; the TORSO (a tattered purple bellhop jacket, gold buttons
and epaulettes, ribs showing through a rip); the near LEG; the HEAD (a skull
under a pillbox cap, teal eyes); the near ARM (a purple sleeve, a bony
forearm, a clawed hand); and the effects: the SPECTRAL SLASH crescent and,
in death, the EIGENMODE GHOSTS (low mode: big and slow; high mode: small and
fast; null mode: two eyes that linger).

Rows (Hollow Knight pattern: approach, telegraph, attack, recovery):
``idle`` 6, ``walk`` 8 (a shamble), ``dash`` 6 (a lunge), ``attack_side`` 16
(anticipation 0-3, telegraph 4-6, active 7-10, recovery 11-15), ``hurt`` 3,
``death`` 12 (it collapses and decomposes into its modes).

Facing right; its feet on the canvas foot (``GROUND``). No drop shadow.
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

TARGET_NAME = "decomposing_specter"
FRAME_SIZE = (208, 176)
SUPER = 4
GROUND = 166.0
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 140),
    ("walk", 8, 110),
    ("dash", 6, 70),
    ("attack_side", 16, 60),
    ("hurt", 3, 90),
    ("death", 12, 100),
]

# The concept's palette.
OUTLINE: RGBA = (22, 14, 30, 255)
COAT: RGBA = (110, 46, 112, 255)
COAT_DARK: RGBA = (72, 30, 80, 255)
COAT_LIGHT: RGBA = (150, 74, 150, 255)
GOLD: RGBA = (226, 172, 74, 255)
BONE: RGBA = (226, 222, 200, 255)
BONE_SHADE: RGBA = (160, 156, 138, 255)
SOCKET: RGBA = (30, 26, 40, 255)
TEAL: RGBA = (92, 238, 214, 255)
TEAL_CORE: RGBA = (210, 255, 246, 255)
CAP: RGBA = (128, 42, 92, 255)

#: Limb lengths (frame pixels).
TORSO = 28.0
NECK = 9.0
UPPER_ARM = 15.0
FOREARM = 16.0
THIGH = 17.0
SHIN = 18.0


@dataclass(frozen=True)
class Pose:
    """One frame's joint table. Angles in degrees from straight down,
    positive toward its facing (right); the torso's ``lean`` from upright."""

    hip: Point = (94.0, GROUND - THIGH - SHIN + 2.0)
    lean: float = 32.0
    head_tilt: float = 10.0
    jaw: float = 0.0
    near_arm: Tuple[float, float] = (30.0, 70.0)
    far_arm: Tuple[float, float] = (10.0, 50.0)
    near_leg: Tuple[float, float] = (15.0, -15.0)
    far_leg: Tuple[float, float] = (-15.0, -30.0)
    wisp: float = 0.0
    glow: float = 0.7
    slash: float = -1.0
    telegraph: float = 0.0
    fade: float = 1.0


def _s(p: Point) -> Point:
    return (p[0] * SUPER, p[1] * SUPER)


def _along(p: Point, deg: float, length: float) -> Point:
    a = math.radians(deg)
    return (p[0] + math.sin(a) * length, p[1] + math.cos(a) * length)


def _alpha(c: RGBA, a: float) -> RGBA:
    return (c[0], c[1], c[2], int(max(0.0, min(1.0, a)) * c[3]))


def _bone_segment(d, a: Point, b: Point, width: float, colour: RGBA) -> None:
    """A limb segment: an outlined round-capped stroke."""
    w = width * SUPER
    for colour_, ww in ((OUTLINE, w + 2.4 * SUPER), (colour, w)):
        d.line([_s(a), _s(b)], fill=colour_, width=int(ww))
        for p in (a, b):
            r = ww / 2.0
            d.ellipse((_s(p)[0] - r, _s(p)[1] - r, _s(p)[0] + r, _s(p)[1] + r), fill=colour_)


def _joints(pose: Pose):
    """The skeleton: shoulder, neck top, and each limb's joints."""
    hip = pose.hip
    shoulder = _along(hip, 180.0 - pose.lean, TORSO)
    neck = _along(shoulder, 180.0 - pose.lean - 10.0, NECK)
    return hip, shoulder, neck


# --- parts ------------------------------------------------------------------------


def draw_spectral_wisps(layer: Image.Image, shoulder: Point, hip: Point, phase: float, glow: float) -> None:
    """The SPECTRAL WISPS: teal ribbons streaming back from its shoulders and
    its hips, waving, softly glowing."""
    halo = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    hd = blending_draw(halo)
    for base, length, amp in ((shoulder, 34.0, 5.0), (hip, 26.0, 4.0), (_along(shoulder, 200, 6), 22.0, 3.0)):
        pts = []
        for k in range(14):
            t = k / 13.0
            pts.append((base[0] - t * length, base[1] - 4.0 + math.sin(t * 5.0 + phase) * amp * t))
        hd.line([_s(p) for p in pts], fill=_alpha(TEAL, 0.75 * glow), width=int(4.5 * SUPER), joint="curve")
        hd.line([_s(p) for p in pts[:9]], fill=_alpha(TEAL_CORE, 0.6 * glow), width=int(1.6 * SUPER), joint="curve")
    layer.alpha_composite(halo.filter(ImageFilter.GaussianBlur(1.2 * SUPER)))


def draw_leg(d, hip: Point, angles: Tuple[float, float], near: bool) -> None:
    """A LEG: a tattered purple trouser over the thigh and knee, then a bony
    shin and foot pointing forward."""
    knee = _along(hip, angles[0], THIGH)
    ankle = _along(knee, angles[0] + angles[1], SHIN)
    coat = COAT if near else COAT_DARK
    _bone_segment(d, knee, ankle, 3.4, BONE if near else BONE_SHADE)
    toe = (ankle[0] + 7.0, ankle[1] + 1.0)
    _bone_segment(d, ankle, toe, 3.0, BONE if near else BONE_SHADE)
    _bone_segment(d, hip, knee, 8.5, coat)
    # The trouser's ragged cuff below the knee.
    cuff = _along(knee, angles[0] + angles[1], 6.0)
    rag = [_s(_along(knee, angles[0] + 90, 4.5)), _s(_along(cuff, angles[0] + 100, 3.0)), _s(_along(cuff, angles[0] + angles[1], 2.0)),
           _s(_along(cuff, angles[0] - 80, 3.5)), _s(_along(knee, angles[0] - 90, 4.5))]
    d.polygon(rag, fill=coat, outline=OUTLINE)


def draw_arm(d, shoulder: Point, angles: Tuple[float, float], near: bool) -> None:
    """An ARM: a purple sleeve with a gold cuff, a bony forearm and a hand of
    three long claws."""
    elbow = _along(shoulder, angles[0], UPPER_ARM)
    wrist = _along(elbow, angles[0] + angles[1], FOREARM)
    bone = BONE if near else BONE_SHADE
    _bone_segment(d, elbow, wrist, 3.0, bone)
    _bone_segment(d, shoulder, elbow, 7.0, COAT_LIGHT if near else COAT_DARK)
    cuff = _along(elbow, angles[0] + angles[1], 1.5)
    _bone_segment(d, elbow, cuff, 6.2, GOLD if near else _alpha(GOLD, 0.7))
    # The claws: three curved fingers fanning from the wrist.
    base = angles[0] + angles[1]
    for spread in (-28.0, 0.0, 26.0):
        mid = _along(wrist, base + spread, 5.0)
        tip = _along(mid, base + spread + 25.0, 5.0)
        d.line([_s(wrist), _s(mid), _s(tip)], fill=OUTLINE, width=int(2.4 * SUPER), joint="curve")
        d.line([_s(wrist), _s(mid), _s(tip)], fill=bone, width=int(1.2 * SUPER), joint="curve")


def draw_torso(d, hip: Point, shoulder: Point, lean: float) -> None:
    """The TORSO: the bellhop's jacket, hunched, its hem torn into tatters,
    gold buttons down its front, an epaulette, and ribs through a rip."""
    across = 180.0 - lean + 90.0  # toward its back
    back_hip, front_hip = _along(hip, across, 8.0), _along(hip, across + 180.0, 8.0)
    back_sh, front_sh = _along(shoulder, across, 9.0), _along(shoulder, across + 180.0, 7.0)
    jacket = [back_sh, front_sh, front_hip, back_hip]
    d.polygon([_s(p) for p in jacket], fill=COAT, outline=OUTLINE, width=int(1.2 * SUPER))
    # The tattered hem: points hanging below the hips.
    hem = []
    for k in range(6):
        t = k / 5.0
        top = (back_hip[0] + (front_hip[0] - back_hip[0]) * t, back_hip[1] + (front_hip[1] - back_hip[1]) * t)
        hem.append(top)
        if k < 5:
            hem.append((top[0] + 2.0, top[1] + (7.0 if k % 2 == 0 else 4.0)))
    d.polygon([_s(p) for p in [back_hip] + hem + [front_hip]], fill=COAT_DARK, outline=OUTLINE)
    # The rip: ribs on the dark of its chest.
    chest = ((shoulder[0] + hip[0]) / 2.0 + 1.0, (shoulder[1] + hip[1]) / 2.0)
    d.ellipse((*_s((chest[0] - 4.5, chest[1] - 6.0)), *_s((chest[0] + 4.5, chest[1] + 6.0))), fill=SOCKET)
    for k in range(4):
        y = chest[1] - 4.0 + k * 2.6
        d.line([_s((chest[0] - 3.4, y)), _s((chest[0] + 3.4, y + 0.6))], fill=BONE_SHADE, width=int(1.0 * SUPER))
    # Buttons down the front edge, and the gold epaulette on the shoulder.
    for k in range(3):
        t = 0.25 + k * 0.25
        p = (front_sh[0] + (front_hip[0] - front_sh[0]) * t - 1.5, front_sh[1] + (front_hip[1] - front_sh[1]) * t)
        d.ellipse((*_s((p[0] - 1.3, p[1] - 1.3)), *_s((p[0] + 1.3, p[1] + 1.3))), fill=GOLD, outline=OUTLINE)
    ep = _along(shoulder, across, 3.0)
    d.ellipse((*_s((ep[0] - 5.0, ep[1] - 2.6)), *_s((ep[0] + 5.0, ep[1] + 2.6))), fill=GOLD, outline=OUTLINE)


def draw_head(layer: Image.Image, d, neck: Point, tilt: float, jaw: float, glow: float) -> None:
    """The HEAD: a skull with a hanging jaw and teal eyes, under a purple
    pillbox cap with a gold band."""
    c = (neck[0] + 4.0, neck[1] - 7.0)
    d.ellipse((*_s((c[0] - 8.5, c[1] - 8.0)), *_s((c[0] + 8.5, c[1] + 7.0))), fill=BONE, outline=OUTLINE, width=int(1.2 * SUPER))
    jaw_top = c[1] + 4.0
    jaw_drop = 3.0 + 4.0 * jaw
    d.polygon([_s((c[0] - 1.0, jaw_top)), _s((c[0] + 8.0, jaw_top)), _s((c[0] + 7.0, jaw_top + jaw_drop)), _s((c[0] + 0.0, jaw_top + jaw_drop - 1.0))],
              fill=BONE_SHADE, outline=OUTLINE)
    for k in range(4):
        x = c[0] + 1.0 + k * 1.8
        d.line([_s((x, jaw_top)), _s((x, jaw_top + 1.6))], fill=OUTLINE, width=int(0.6 * SUPER))
    # The eyes: dark sockets, teal light in them.
    halo = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    hd = blending_draw(halo)
    for side, ex in ((-1, c[0] + 0.3), (1, c[0] + 6.0)):
        ey = c[1] - 0.5
        # A deep socket, its brow ridge cut down toward the nose (a glare),
        # a burning teal point in it.
        d.ellipse((*_s((ex - 2.9, ey - 2.7)), *_s((ex + 2.9, ey + 2.7))), fill=SOCKET)
        inner = ex - side * 2.6
        d.polygon([_s((ex - 3.2, ey - 3.2)), _s((ex + 3.2, ey - 3.2)), _s((ex + side * 3.2, ey - 1.6)), _s((inner, ey - 0.2))], fill=BONE)
        d.ellipse((*_s((ex - 1.4, ey - 0.6)), *_s((ex + 1.4, ey + 1.6))), fill=TEAL_CORE)
        hd.ellipse((*_s((ex - 3.0, ey - 2.0)), *_s((ex + 3.0, ey + 3.0))), fill=_alpha(TEAL, 0.75 * glow))
    layer.alpha_composite(halo.filter(ImageFilter.GaussianBlur(1.0 * SUPER)))
    # The cap, tipped with the head.
    cap = [(c[0] - 7.0, c[1] - 6.0), (c[0] + 6.0, c[1] - 7.5), (c[0] + 6.5, c[1] - 15.0), (c[0] - 6.0, c[1] - 14.0)]
    cap = [(x + tilt * 0.08 * (c[1] - y), y) for x, y in cap]
    d.polygon([_s(p) for p in cap], fill=CAP, outline=OUTLINE, width=int(1.2 * SUPER))
    d.line([_s(cap[0]), _s(cap[1])], fill=GOLD, width=int(2.0 * SUPER))


def draw_spectral_slash(layer: Image.Image, shoulder: Point, u: float) -> None:
    """The SPECTRAL SLASH: a wide teal crescent sweeping down in front of it,
    ``u`` (0..1) through its swing."""
    if u < 0.0:
        return
    halo = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    hd = blending_draw(halo)
    centre = (shoulder[0] + 6.0, shoulder[1] + 10.0)
    r_out, r_in = 44.0, 30.0
    sweep_end = -70.0 + 170.0 * u
    sweep_start = sweep_end - 110.0
    fade = 1.0 - max(0.0, (u - 0.7) / 0.3)
    pts_out, pts_in = [], []
    for k in range(25):
        a = math.radians(sweep_start + (sweep_end - sweep_start) * k / 24.0)
        thick = math.sin(math.pi * k / 24.0)
        pts_out.append((centre[0] + math.cos(a) * r_out, centre[1] + math.sin(a) * r_out))
        pts_in.append((centre[0] + math.cos(a) * (r_out - (r_out - r_in) * thick), centre[1] + math.sin(a) * (r_out - (r_out - r_in) * thick)))
    poly = [_s(p) for p in pts_out + pts_in[::-1]]
    hd.polygon(poly, fill=_alpha(TEAL, 0.85 * fade))
    layer.alpha_composite(halo.filter(ImageFilter.GaussianBlur(1.6 * SUPER)))
    blending_draw(layer).polygon(poly, fill=_alpha(TEAL_CORE, 0.75 * fade))


def draw_telegraph_marks(d, head: Point, u: float) -> None:
    """The TELEGRAPH: three teal strokes flaring over its head (the tell)."""
    if u <= 0.0:
        return
    for k, ang in enumerate((-40.0, 0.0, 40.0)):
        a = math.radians(ang - 90.0)
        p0 = (head[0] + math.cos(a) * 14.0, head[1] - 8.0 + math.sin(a) * 14.0)
        p1 = (head[0] + math.cos(a) * (14.0 + 6.0 * u), head[1] - 8.0 + math.sin(a) * (14.0 + 6.0 * u))
        d.line([_s(p0), _s(p1)], fill=_alpha(TEAL, u), width=int(2.2 * SUPER))


def draw_eigenmode_ghost(layer: Image.Image, at: Point, size: float, stretch: float, alpha: float) -> None:
    """An EIGENMODE GHOST: a small teal ghost the specter decomposes into;
    ``stretch`` draws it out along its way (a high mode is long and thin)."""
    if alpha <= 0.0:
        return
    g = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    gd = blending_draw(g)
    w, h = size * stretch, size / max(0.6, stretch ** 0.5)
    gd.ellipse((*_s((at[0] - w, at[1] - h)), *_s((at[0] + w, at[1] + h))), fill=_alpha(TEAL, 0.85 * alpha))
    gd.polygon([_s((at[0] - w, at[1])), _s((at[0] - w * 2.4, at[1] + h * 0.3)), _s((at[0] - w * 0.2, at[1] + h))], fill=_alpha(TEAL, 0.6 * alpha))
    layer.alpha_composite(g.filter(ImageFilter.GaussianBlur(0.8 * SUPER)))
    d = blending_draw(layer)
    for ex in (at[0] + w * 0.15, at[0] + w * 0.55):
        d.ellipse((*_s((ex - 1.1, at[1] - 1.6)), *_s((ex + 1.1, at[1] + 1.0))), fill=_alpha(SOCKET, alpha))


# --- assembly ---------------------------------------------------------------------


def draw_specter(pose: Pose, phase: float) -> Image.Image:
    img = Image.new("RGBA", (FRAME_SIZE[0] * SUPER, FRAME_SIZE[1] * SUPER), (0, 0, 0, 0))
    hip, shoulder, neck = _joints(pose)
    draw_spectral_wisps(img, shoulder, hip, phase, pose.glow)
    d = blending_draw(img)
    draw_leg(d, hip, pose.far_leg, near=False)
    draw_arm(d, shoulder, pose.far_arm, near=False)
    draw_torso(d, hip, shoulder, pose.lean)
    draw_leg(d, hip, pose.near_leg, near=True)
    # A claw raised high goes behind the head, so the skull still reads.
    raised = pose.near_arm[0] > 100.0
    if raised:
        draw_arm(d, shoulder, pose.near_arm, near=True)
    draw_head(img, d, neck, pose.head_tilt, pose.jaw, pose.glow)
    if not raised:
        draw_arm(d, shoulder, pose.near_arm, near=True)
    draw_telegraph_marks(d, (neck[0] + 4.0, neck[1] - 14.0), pose.telegraph)
    draw_spectral_slash(img, shoulder, pose.slash)
    img = polish(img, phase)
    if pose.fade < 1.0:
        img.putalpha(img.getchannel("A").point(lambda v: int(v * max(0.0, pose.fade))))
    return img


#: The figure is drawn this much bigger than its joint table (it read thin
#: and small), about its feet.
ZOOM = 1.35
ZOOM_ANCHOR = (96.0, GROUND)


def polish(img: Image.Image, phase: float) -> Image.Image:
    """The POLISH over the drawn figure: SHADING (lit at the head, darker to
    the feet, the shadows going cold teal), a teal RIM LIGHT along its back
    from the spectral glow behind it, its lower legs DISSOLVING into
    flickering spectral energy (as its spectrum unravels), a teal AURA under
    it all and MOTES drifting up; then the whole ZOOMED about its feet."""
    px = np.asarray(img, np.float32)
    h, w = px.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    yf, xf = ys / SUPER, xs / SUPER
    a = px[..., 3] / 255.0
    # Shading.
    light = np.clip(1.08 - 0.42 * np.clip((yf - 70.0) / 82.0, 0, 1), 0.55, 1.1)
    rgb = px[..., :3] * light[..., None]
    dark = np.clip(1.0 - rgb.mean(axis=2, keepdims=True) / 90.0, 0, 1)
    rgb = rgb + dark * np.array([0.0, 16.0, 18.0], np.float32)
    # Rim light on its back edge (left): where alpha falls off to the left.
    e = int(1.2 * SUPER)
    left = np.roll(a, e, axis=1)
    rim = np.clip(a - left, 0, 1) * (a > 0.5)
    rim_img = Image.fromarray((rim * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6 * SUPER))
    rim = np.asarray(rim_img, np.float32) / 255.0
    rgb = rgb + rim[..., None] * np.array(TEAL[:3], np.float32) * 0.9
    # The lower legs dissolve: alpha eaten by a flickering noise from the
    # shins down, the eaten edge glowing teal.
    rng = np.random.default_rng(int(phase * 1000) % 2**31)
    grain = Image.fromarray((rng.random((h // 8, w // 8)) * 255).astype(np.uint8)).resize((w, h), Image.Resampling.BICUBIC)
    n = np.asarray(grain, np.float32) / 255.0
    depth = np.clip((yf - (GROUND - 16.0)) / 16.0, 0, 1)
    burn = depth * 1.2 - n * 0.7
    eaten = np.clip((burn - 0.1) / 0.25, 0, 1)
    ember = np.clip(burn / 0.1, 0, 1) * (1 - eaten) * a
    rgb = rgb + ember[..., None] * np.array(TEAL[:3], np.float32) * 0.8
    alpha = a * (1 - eaten)
    out = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), alpha * 255]).astype(np.uint8), "RGBA")
    # The aura: its silhouette, blurred and teal, under it.
    aura = Image.new("RGBA", out.size, TEAL[:3] + (0,))
    aura.putalpha(out.getchannel("A").point(lambda v: int(v * 0.35)).filter(ImageFilter.GaussianBlur(4.0 * SUPER)))
    base = Image.new("RGBA", out.size, (0, 0, 0, 0))
    base.alpha_composite(aura)
    base.alpha_composite(out)
    d = blending_draw(base)
    rng = np.random.default_rng(7)
    for _ in range(10):
        x, y, ph = 66 + rng.random() * 60, 84 + rng.random() * 80, rng.random()
        yy = y - ((phase / math.tau + ph) % 1.0) * 18
        d.ellipse((*_s((x - 0.8, yy - 0.8)), *_s((x + 0.8, yy + 0.8))), fill=_alpha(TEAL_CORE, 0.7))
    # The zoom about its feet.
    zw, zh = int(w * ZOOM), int(h * ZOOM)
    big = base.resize((zw, zh), Image.Resampling.LANCZOS)
    ax, ay = ZOOM_ANCHOR[0] * SUPER, ZOOM_ANCHOR[1] * SUPER
    canvas = Image.new("RGBA", base.size, (0, 0, 0, 0))
    canvas.paste(big, (int(round(ax - ax * ZOOM)), int(round(ay - ay * ZOOM))), big)
    return canvas


def _pose_for(animation: str, i: int, n: int) -> Tuple[Pose, float]:
    t = i / max(1, n)
    u = i / max(1, n - 1)
    sway = math.sin(t * math.tau)
    base = Pose()
    if animation == "idle":
        return replace(base, hip=(94.0, base.hip[1] + 1.0 * sway), lean=32.0 + 2.0 * sway,
                       near_arm=(30.0 + 4.0 * sway, 70.0), far_arm=(12.0 - 3.0 * sway, 50.0), jaw=0.3 + 0.3 * sway), t * math.tau
    if animation == "walk":
        # A shamble: legs drag, the body lurches, the arms hang and swing late.
        s = math.sin(t * math.tau)
        c = math.cos(t * math.tau)
        return replace(base, hip=(94.0 + 2.0 * s, base.hip[1] + 1.6 * abs(c) - 1.0), lean=36.0 + 4.0 * abs(s),
                       near_leg=(10.0 + 24.0 * s, -10.0 - 22.0 * max(0.0, c)), far_leg=(10.0 - 24.0 * s, -10.0 - 22.0 * max(0.0, -c)),
                       near_arm=(28.0 - 16.0 * s, 60.0), far_arm=(18.0 + 16.0 * s, 45.0), head_tilt=6.0 * s, jaw=0.4), t * math.tau * 1.5
    if animation == "dash":
        k = math.sin(u * math.pi)
        return replace(base, hip=(90.0 + 10.0 * u, base.hip[1] - 2.0 * k), lean=55.0 + 10.0 * k,
                       near_leg=(-35.0, -20.0), far_leg=(40.0, -50.0), near_arm=(80.0 + 10.0 * k, 20.0),
                       far_arm=(60.0, 30.0), wisp=1.0, glow=1.0, jaw=0.6), t * math.tau * 2.0
    if animation == "attack_side":
        if i <= 3:  # anticipation: it coils back, claw raised
            k = i / 3.0
            return replace(base, lean=32.0 - 14.0 * k, hip=(94.0 - 4.0 * k, base.hip[1]), near_arm=(30.0 + 120.0 * k, 70.0 - 30.0 * k),
                           near_leg=(10.0, -20.0), far_leg=(-25.0, -25.0), jaw=0.2), t * math.tau
        if i <= 6:  # telegraph: it holds, gathering light, the tell flares
            k = (i - 3) / 3.0
            return replace(base, lean=18.0, hip=(90.0, base.hip[1]), near_arm=(150.0, 40.0), near_leg=(10.0, -20.0),
                           far_leg=(-25.0, -25.0), glow=0.8 + 0.2 * k, telegraph=k, jaw=1.0), t * math.tau
        if i <= 10:  # active: the slash sweeps down and through
            k = (i - 7) / 3.0
            return replace(base, lean=40.0 + 20.0 * k, hip=(92.0 + 6.0 * k, base.hip[1] + 2.0 * k), near_arm=(150.0 - 150.0 * k, 20.0 + 30.0 * k),
                           near_leg=(35.0, -40.0), far_leg=(-30.0, -10.0), glow=1.0, slash=0.15 + 0.85 * k, jaw=1.0), t * math.tau
        k = (i - 11) / 4.0  # recovery: open, slumped, slowly righting
        return replace(base, lean=60.0 - 28.0 * k, hip=(98.0 - 4.0 * k, base.hip[1] + 2.0 - 2.0 * k), near_arm=(5.0 + 25.0 * k, 40.0 + 30.0 * k),
                       near_leg=(30.0 - 15.0 * k, -40.0 + 25.0 * k), far_leg=(-30.0 + 15.0 * k, -10.0 - 20.0 * k), glow=0.5, jaw=0.6 * (1 - k)), t * math.tau
    if animation == "hurt":
        k = 1.0 - u
        return replace(base, lean=15.0 + 10.0 * (1 - k), hip=(70.0 - 3.0 * k, base.hip[1]), head_tilt=-15.0 * k,
                       near_arm=(-20.0 * k + 30.0 * (1 - k), 90.0), far_arm=(-30.0 * k, 60.0), jaw=1.0, glow=1.0), t * math.tau
    if animation == "death":
        k = min(1.0, u / 0.45)  # it crumples to its knees, then falls apart
        return replace(base, lean=32.0 + 45.0 * k, hip=(94.0 + 4.0 * k, base.hip[1] + 14.0 * k), near_leg=(60.0 * k + 15.0 * (1 - k), -120.0 * k - 15.0 * (1 - k)),
                       far_leg=(50.0 * k - 15.0 * (1 - k), -110.0 * k - 30.0 * (1 - k)), near_arm=(20.0, 20.0), far_arm=(10.0, 20.0),
                       jaw=1.0, glow=1.0, fade=1.0 - max(0.0, (u - 0.35) / 0.3)), t * math.tau
    raise ValueError(f"{TARGET_NAME}: no row {animation!r}")


def _render_frame(animation: str, frame_index: int, nframes: int) -> Image.Image:
    pose, phase = _pose_for(animation, frame_index, nframes)
    img = draw_specter(pose, phase)
    if animation == "death":
        # It decomposes into its eigenmodes: they rise out of the body as it
        # fades, the low mode slow, the high mode fast, the null mode (its
        # eyes) lingering last.
        u = frame_index / max(1, nframes - 1)
        k = max(0.0, (u - 0.3) / 0.7)
        if k > 0.0:
            fade = 1.0 - max(0.0, (u - 0.9) / 0.1)
            draw_eigenmode_ghost(img, (92.0 - 6.0 * k, 134.0 - 40.0 * k), 9.0, 1.0, min(1.0, k * 3) * (1.0 - max(0.0, (k - 0.75) / 0.25)))
            draw_eigenmode_ghost(img, (100.0 + 26.0 * k, 126.0 - 60.0 * k), 4.5, 2.2, min(1.0, k * 3) * (1.0 - max(0.0, (k - 0.6) / 0.3)))
            d = blending_draw(img)
            for ex in (88.0, 96.0):
                ey = 118.0 - 10.0 * k
                d.ellipse((*_s((ex - 2.2, ey - 2.2)), *_s((ex + 2.2, ey + 2.2))), fill=_alpha(TEAL_CORE, min(1.0, k * 2) * fade))
    return img.resize(FRAME_SIZE, Image.Resampling.LANCZOS)


ACTOR_METADATA = {
    "actor": {"character_id": TARGET_NAME, "display_name": "Decomposing Specter"},
    "body": {
        "body_plan": "Humanoid",
        "body_kind": "Undead",
        "mass_class": "Medium",
        "traits": ["spectral", "undead", "bellhop", "math"],
        "locomotion_hint": "Walk",
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
    return [
        outputs[key]
        for key in ("spritesheet", "yaml", "ron", "actor", "preview", "canonical", "canonical_transparent")
    ]


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
