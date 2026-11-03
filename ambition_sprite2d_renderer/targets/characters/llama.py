"""The Llama: the pack animal of the Andes, and it is not impressed.

A woolly llama, cream with brown patches, on slim legs with two-toed feet.
Its neck is long and upright and its head is small, with long curved ears.
The herders of the Andes tie tassels of coloured yarn to the ears of their
llamas; this one has red and pink tassels. Its eyes are always half shut:
it has seen it all before.

It keeps its distance and spits. It chews and flicks an ear. It paces on
long legs (both legs of one side move together). When it sees you it lifts
its head and looks down its nose at you. Its windup pulls its head back,
puts its ears flat and fills its cheeks; its strike thrusts its head
forward and spits a green glob (the shot ``spit``). A hit makes it shut
its eyes and flatten its ears; at its death it folds its legs under it
(as a llama lies down) and drops its head.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Sequence, Tuple

from . import _art_cast_kit as K
from . import _history_americas_kit as A
from . import _stage_kit as S

TARGET_NAME = "llama"
FRAME_SIZE = (128, 128)
ROWS = K.ENEMY_ROWS
GROUND = 123.0

ACTOR_METADATA = A.enemy_metadata(
    TARGET_NAME, "Llama", "first_maize", "Quadruped", "Standard", "Medium", "Walk", ["llama", "spit", "andes"],
    "A woolly llama of the History dimension's Andes, with yarn tassels on its ears and its eyes half shut: it is "
    "not impressed. It keeps its distance, pulls its head back and spits.",
)

WOOL = (238, 228, 206, 255)
WOOL_SHADE = (198, 184, 156, 255)
PATCH = (150, 98, 58, 255)
PATCH_SHADE = (112, 70, 40, 255)
HOOF = (64, 48, 40, 255)
LID = (198, 176, 140, 255)
EYE = (40, 30, 26, 255)
NOSE = (84, 60, 50, 255)
TASSEL_RED = (214, 46, 64, 255)
TASSEL_PINK = (240, 120, 170, 255)
TASSEL_GOLD = (246, 196, 60, 255)
SPIT = (176, 206, 104, 255)
SPIT_LIGHT = (220, 240, 170, 255)

Point = Tuple[float, float]
#: The size of the head against the body.
HEAD = 1.2


def _wool_edge(cx: float, cy: float, rx: float, ry: float, bumps: int, depth: float, phase: float = 0.0) -> List[Point]:
    """An ellipse with a scalloped edge: a fleece."""
    pts = []
    for k in range(bumps * 4):
        a = math.tau * k / (bumps * 4)
        bump = depth * abs(math.sin(a * bumps / 2.0 + phase))
        pts.append((cx + (rx + bump) * math.cos(a), cy + (ry + bump) * math.sin(a)))
    return pts


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)

    dx, dy, neck_lean, head_pitch, ears, lids, chew = 0.0, 0.0, 0.0, 0.0, 0.0, 0.55, 0.0
    gait, cheeks, spit, kneel, fade, alarm, tail = None, 0.0, 0.0, 0.0, 1.0, False, 0.0
    if anim == "idle":
        chew = math.sin(cyc * 2.0)
        ears = 0.3 * max(0.0, math.sin(cyc * 3.0)) if i in (2, 3) else 0.0
        dy = 0.4 * math.sin(cyc)
        lids = 0.55 if i != 4 else 1.0
    elif anim == "walk":
        gait = t
        dy = -1.2 * abs(math.sin(cyc * 2.0))
        neck_lean = 3.0 * math.sin(cyc * 2.0)
        tail = 0.3
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.3))
        neck_lean, head_pitch, ears, alarm = -6.0 * k, -14.0 * k, 1.0, True
        lids = 0.55 - 0.25 * k
        tail = 0.6 * k
    elif anim == "windup":
        # The head goes back, the ears go flat, the cheeks fill.
        neck_lean, head_pitch, ears = -22.0, -16.0, -1.0
        cheeks = 0.8 + 0.2 * math.sin(cyc * 2.0)
        lids, tail = 0.75, 0.8
        dx = -2.0
    elif anim == "attack_side":
        # The spit: the head goes forward fast, and the glob flies.
        u = t
        thrust = math.sin(math.pi * min(1.0, u * 1.6)) if u < 0.62 else max(0.0, 1.0 - (u - 0.62) / 0.38) * 0.4
        neck_lean = -22.0 + 44.0 * thrust
        head_pitch = -16.0 + 26.0 * thrust
        ears = -1.0
        cheeks = max(0.0, 1.0 - u * 3.0)
        spit = u
        lids, tail = 0.7, 0.8
    elif anim == "hit":
        k = math.sin(math.pi * t)
        neck_lean, head_pitch, ears, lids, dx = -10.0 * k, -12.0 * k, -1.0, 1.0, -3.0 * k
    elif anim == "death":
        u = min(1.0, t / 0.8)
        kneel = min(1.0, u * 1.3)
        neck_lean = 10.0 * kneel
        head_pitch = 30.0 * kneel
        lids = 1.0
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    # The body: a woolly barrel on long legs.
    bx, by = 50.0 + dx, 74.0 + dy + 28.0 * kneel
    hip = (bx - 18.0, by + 6.0)
    sh = (bx + 18.0, by + 6.0)

    def leg(root: Point, ph: float, front: bool, near: bool) -> None:
        colour = WOOL if near else WOOL_SHADE
        fx, fy = root[0] + (2.0 if front else -1.0), GROUND - 3.0
        if gait is not None:
            gx, gy = A.gait(ph, 18.0, 6.0)
            fx += gx
            fy += gy
        if kneel:
            # The legs fold under the body.
            fx = root[0] + (6.0 if front else -4.0) * kneel
            fy = GROUND - 3.0
        knee, foot = S.joint(root, (fx, fy), 21.0, 22.0, -1.0 if front else 1.0)
        knee = (knee[0], min(knee[1], GROUND - 5.0))
        f.limb([root, knee], 7.0, colour)
        f.limb([knee, foot], 5.0, colour)
        # The foot: two toes on a soft pad, with small dark nails.
        f.poly([(foot[0] - 3.0, foot[1] - 2.0), (foot[0] + 4.0, foot[1] - 2.0), (foot[0] + 5.0, foot[1] + 2.4), (foot[0] - 3.0, foot[1] + 2.4)], HOOF)
        f.ink([(foot[0] + 1.0, foot[1] - 0.5), (foot[0] + 1.4, foot[1] + 2.2)], 0.6, WOOL_SHADE)

    # The pace: the two legs of one side move together.
    leg((hip[0] + 6.0, hip[1]), (gait or 0.0) + 0.5, False, False)
    leg((sh[0] + 4.0, sh[1]), (gait or 0.0) + 0.5, True, False)

    # The tail: a short woolly tuft, up when it is cross.
    tx, ty = bx - 27.0, by - 6.0
    tail_pts = K.turn([(tx, ty), (tx - 4.0, ty + 3.0), (tx - 6.0, ty + 9.0)], tx, ty, 50.0 * tail)
    f.limb(tail_pts, 6.0, WOOL)

    # The fleece of the body, and its brown patch.
    f.poly(_wool_edge(bx, by, 26.0, 14.0, 9, 1.8), WOOL)
    f.poly(_wool_edge(bx - 6.0, by - 2.0, 11.0, 8.0, 5, 1.2, 0.4), PATCH, body=False)
    f.poly([(bx - 22.0, by + 8.0), (bx + 20.0, by + 8.0), (bx + 16.0, by + 13.0), (bx - 18.0, by + 13.0)], K.alpha(WOOL_SHADE, 0.8), body=False)
    for k in range(5):
        x = bx - 18.0 + k * 9.0
        f.ink([(x, by - 6.0 + (k % 2) * 3.0), (x + 2.0, by - 3.0 + (k % 2) * 3.0)], 0.7, WOOL_SHADE)

    leg((hip[0] - 1.0, hip[1] + 1.0), gait or 0.0, False, True)
    leg((sh[0] + 2.0, sh[1] + 1.0), gait or 0.0, True, True)

    # The neck: up from the chest, a column of wool.
    base = (bx + 19.0, by - 4.0)
    lean = neck_lean
    top = K.turn([(bx + 23.0, by - 41.0)], base[0], base[1], lean)[0]
    f.limb([base, A.lerp(base, top, 0.5), top], 15.0, WOOL)
    f.limb([A.lerp(base, top, 0.35), A.lerp(base, top, 0.75)], 9.0, PATCH, body=False)
    for k in range(4):
        p0 = A.lerp(base, top, 0.15 + k * 0.2)
        f.ink([(p0[0] - 5.0, p0[1]), (p0[0] - 3.0, p0[1] + 2.0)], 0.7, WOOL_SHADE)

    # The head, turned by its pitch about the top of the neck.
    pr = head_pitch + lean * 0.5

    def Hd(*pts: Point) -> List[Point]:
        return K.turn([(top[0] + x * HEAD, top[1] + y * HEAD) for x, y in pts], top[0], top[1], pr)

    # The ears: long, curved like bananas, with tassels of yarn.
    def ear(near: bool) -> None:
        back = -26.0 * max(0.0, -ears) + 8.0 * max(0.0, ears)
        root = Hd((-2.0 if near else 1.0, -6.0))[0]
        pts = K.turn([root, (root[0] - 1.0, root[1] - 7.0), (root[0] + 1.0, root[1] - 13.0)], root[0], root[1], -back + (0.0 if near else 8.0) + pr)
        f.limb(pts, 3.6, WOOL if near else WOOL_SHADE)
        f.ink(pts[:2], 1.0, PATCH_SHADE)
        if near:
            # The tassel hangs from the ear: three short strands of yarn.
            kx, ky = A.lerp(pts[0], pts[1], 0.4)
            for k, colour in enumerate((TASSEL_RED, TASSEL_PINK, TASSEL_GOLD)):
                f.limb([(kx, ky), (kx - 3.0 + k * 1.6, ky + 6.0)], 1.8, colour)
            f.ellipse(kx, ky, 1.6, 1.6, TASSEL_RED)

    ear(False)
    f.poly(Hd((-6.0, -4.0), (0.0, -8.0), (8.0, -6.0), (15.0, -1.0), (18.0, 4.0), (16.0, 8.0), (8.0, 9.0), (-2.0, 7.0), (-6.0, 3.0)), PATCH)
    # The cheeks fill with spit.
    if cheeks:
        f.ellipse(*Hd((7.0, 5.0))[0], 4.0 + 4.0 * cheeks, 3.0 + 3.4 * cheeks, PATCH)
        f.ellipse(*Hd((7.0, 5.6))[0], 2.4 + 1.6 * cheeks, 1.4 + 1.2 * cheeks, K.shade(PATCH, 1.2), body=False)
    # The pale muzzle with its split lip, and the chewing jaw.
    jaw_y = 0.8 * chew
    f.poly(Hd((10.0, 0.0), (16.0, -0.6), (18.6, 3.6), (17.0, 7.4 + jaw_y), (11.0, 8.0 + jaw_y)), WOOL_SHADE, body=False)
    f.ink(Hd((15.0, 1.0), (16.4, 3.2)), 0.8, NOSE)
    f.ink(Hd((17.6, 4.6), (12.0, 5.6 + jaw_y * 0.5)), 0.9, NOSE)
    if spit and spit < 0.7:
        f.ellipse(*Hd((18.0, 5.0))[0], 1.8, 1.4, SPIT, body=False)
    # The eye: half shut, under a heavy lid, with long lashes.
    ex, ey = Hd((5.0, -1.6))[0]
    f.ellipse(ex, ey, 2.7, 2.4, K.WHITE, body=False)
    f.ellipse(ex + 0.6, ey + 0.2, 1.6, 1.8, EYE, body=False)
    cover = max(0.0, min(1.0, lids))
    f.poly([(ex - 3.0, ey - 2.6), (ex + 3.0, ey - 2.6), (ex + 3.0, ey - 2.6 + 5.2 * cover), (ex - 3.0, ey - 2.6 + 5.2 * cover)], PATCH, body=False)
    f.ink([(ex - 3.0, ey - 2.6 + 5.2 * cover), (ex + 3.0, ey - 2.6 + 5.2 * cover - 0.4)], 1.0, A.SEPIA_INK)
    for k in range(3):
        lx = ex - 1.6 + k * 1.6
        ly = ey - 2.6 + 5.2 * cover
        f.ink([(lx, ly), (lx + 0.8, ly + 1.6)], 0.5, A.SEPIA_INK)
    # The tuft of wool on the crown.
    f.poly(_wool_edge(*Hd((-1.0, -6.0))[0], 5.0, 3.0, 4, 1.0), WOOL)
    ear(True)

    if spit:
        # The glob flies straight out of the mouth, with a spray of drops.
        mx, my = Hd((19.0, 5.0))[0]
        if 0.15 < spit < 0.9:
            d = 6.0 + 40.0 * (spit - 0.15) / 0.75
            gx = min(116.0, mx + d)
            f.ellipse(gx, my + 1.0, 5.4, 4.2, SPIT, body=False)
            f.ellipse(gx + 1.4, my - 0.4, 2.0, 1.5, SPIT_LIGHT, body=False)
            for k in range(4):
                f.ellipse(max(mx + 2.0, gx - 6.0 - k * 4.0), my + 1.0 + (k - 1.5) * 1.6, 1.4 - 0.2 * k, 1.2 - 0.2 * k, K.alpha(SPIT, 0.85), body=False)
        if spit > 0.1:
            # The face of a llama that has just spat: the lower lip hangs.
            f.ink(Hd((12.0, 8.0), (16.0, 9.6)), 1.1, NOSE)
    if alarm:
        A.alarm_mark(f, min(118.0, top[0] + 22.0), 17.0)
    return A.finish(f, fade=fade, width=1.4)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
