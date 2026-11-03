"""The Mime: a silent performer of the Amphitheatre, who pushes.

A thin figure in whiteface: a white face with black brows drawn high, a
black tear under one eye and red lips, black hair combed flat. A shirt of
black and white stripes, red braces, black trousers, white gloves and
black shoes. It never makes a sound.

Everything it does is a mime, until it is not. At rest it is trapped in a
box: its palms feel along walls that are not there. It walks on its toes
with high, careful steps. Its windup leans on an invisible wall and pushes
it toward you; its strike pulls an invisible rope, hand over hand, as if
it pulls you in, and then it shoves you, for real, with both hands. A hit
is a silent scream; its death is a long, theatrical one: a hand on the
heart, a sink to the knees, a fall.

The things that are not there are drawn as a faint glint of spotlight: the
edge of a pane of glass at its palms, the line of a rope.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List

from . import _art_cast_kit as K
from . import _stage_kit as S

TARGET_NAME = "mime"
FRAME_SIZE = (128, 128)
ROWS = K.ENEMY_ROWS
GROUND = 124.0

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Mime", "Biped", "Standard", "Light", "Walk", ["stage", "mime", "silent"],
    "A silent performer of the Amphitheatre of the Art dimension: whiteface, a striped shirt, red braces and white "
    "gloves. It leans on an invisible wall, pulls you in on an invisible rope, and then shoves you with both hands.",
)

THIGH, SHIN = 13.0, 13.0
UPPER_ARM, FOREARM = 10.5, 10.0
TORSO = 19.0
HEAD_R = 7.0
STRIPE_DARK = (40, 38, 56, 255)
SHIRT = (246, 244, 240, 255)
TROUSERS = (40, 38, 52, 255)
TROUSERS_SHADE = (26, 24, 36, 255)
BRACES = (214, 36, 56, 255)
HAIR = (30, 26, 40, 255)
LIPS = (214, 30, 52, 255)
GLINT = (236, 248, 255, 255)


def _glove(pen: S.Pen, x: float, y: float, kind: str) -> None:
    """A white glove: a flat palm toward the front, a fist, or an open hand."""
    if kind == "palm":
        pen.ellipse(x, y, 1.9, 3.4, K.WHITE)
        pen.ink([(x + 1.0, y - 2.6), (x + 1.0, y + 2.0)], 0.5, K.alpha(K.STEEL_SHADE, 0.8))
        pen.ellipse(x - 1.2, y + 2.4, 1.2, 1.0, K.WHITE)
    elif kind == "fist":
        pen.ellipse(x, y, 2.5, 2.3, K.WHITE)
        pen.ink([(x + 0.6, y - 1.8), (x + 0.6, y + 1.8)], 0.5, K.alpha(K.STEEL_SHADE, 0.8))
    else:
        pen.ellipse(x, y, 2.4, 2.4, K.WHITE)


def _wall(f: K.Frame, x: float, y0: float, y1: float, a: float) -> None:
    """The edge of a wall that is not there: two faint glints of glass."""
    f.ink([(x, y0), (x, y1)], 1.0, K.alpha(GLINT, 0.55 * a))
    f.ink([(x + 2.0, y0 + 6.0), (x + 2.0, y0 + 11.0)], 0.8, K.alpha(GLINT, 0.8 * a))
    f.ink([(x + 2.0, y1 - 8.0), (x + 2.0, y1 - 5.0)], 0.8, K.alpha(GLINT, 0.8 * a))


def _rope(f: K.Frame, a, b, alpha: float) -> None:
    """A rope that is not there: a dashed glint of a line."""
    n = 9
    for k in range(n):
        if k % 2:
            continue
        u0, u1 = k / n, (k + 1) / n
        f.ink([(a[0] + (b[0] - a[0]) * u0, a[1] + (b[1] - a[1]) * u0), (a[0] + (b[0] - a[0]) * u1, a[1] + (b[1] - a[1]) * u1)], 1.0,
              K.alpha(GLINT, alpha))


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)

    hip_x, crouch, lean, bob = 50.0, 0.0, 0.0, 0.0
    near_foot = far_foot = None      # (dx from hip, lift) or None for a stand
    eyes, mouth, brows, alarm, fade, rot = "open", "smile", 0.0, False, 1.0, 0.0
    nh = fh = None
    n_kind = f_kind = "open"
    wall = rope = None
    impact = 0.0
    if anim == "idle":
        # Trapped in a box: the palms feel along a wall in front, one up and one down.
        bob = 0.5 * math.sin(cyc)
        lean = 2.0
        nh = (64.0, 86.0 + 6.0 * math.sin(cyc))
        fh = (63.0, 86.0 - 6.0 * math.sin(cyc))
        n_kind = f_kind = "palm"
        wall = (66.5, 72.0, 100.0, 1.0)
        mouth, brows = "o_small", 1.0
    elif anim == "walk":
        # On its toes, with high, careful steps: a mime's sneak.
        lean = 6.0
        lift_n = max(0.0, math.sin(cyc))
        lift_f = max(0.0, -math.sin(cyc))
        near_foot = (6.0 * math.cos(cyc), 9.0 * lift_n)
        far_foot = (-6.0 * math.cos(cyc), 9.0 * lift_f)
        bob = -2.0 * abs(math.sin(cyc))
        nh = (hip_x + 6.0 + 4.0 * math.sin(cyc), 78.0 + 2.0 * math.cos(cyc))
        fh = (hip_x + 2.0 - 4.0 * math.sin(cyc), 74.0)
        n_kind = f_kind = "open"
        mouth = "smile"
    elif anim == "notice":
        # A silent gasp: both hands to the cheeks, the body thrown back.
        lean = -10.0 * math.sin(math.pi * min(1.0, t * 1.5))
        bob = -2.0 * math.sin(math.pi * t)
        alarm, eyes, mouth, brows = True, "wide", "o", 2.0
        nh, fh = "cheek", "cheek"
    elif anim == "windup":
        # It leans its weight on an invisible wall and pushes it toward you.
        push = 0.5 + 0.5 * math.sin(cyc * 2.0)
        lean = 22.0 + 2.0 * push
        crouch = 3.0
        near_foot = (-12.0, 0.0)
        far_foot = (5.0, 0.0)
        hip_x -= 3.0
        nh = (76.0 + 1.0 * push, 78.0)
        fh = (75.0 + 1.0 * push, 70.0)
        n_kind = f_kind = "palm"
        wall = (78.5 + 1.0 * push, 56.0, 100.0, 1.0)
        mouth, brows, eyes = "grit", 1.5, "squint"
    elif anim == "attack_side":
        if i <= 2:
            # The rope, hand over hand: reach out, pull back, pull you in.
            k = i
            lean = (12.0, -14.0, -20.0)[k]
            near_foot = ((6.0, 0.0), (-2.0, 0.0), (-6.0, 0.0))[k]
            far_foot = ((-8.0, 0.0), (6.0, 0.0), (8.0, 0.0))[k]
            hip_x += (2.0, -3.0, -6.0)[k]
            crouch = (2.0, 4.0, 5.0)[k]
            nh = ((hip_x + 22.0, 76.0), (hip_x + 10.0, 84.0), (hip_x + 4.0, 90.0))[k]
            fh = ((hip_x + 16.0, 80.0), (hip_x + 16.0, 80.0), (hip_x + 12.0, 84.0))[k]
            n_kind = f_kind = "fist"
            rope = (110.0, (nh[1] + fh[1]) / 2.0 - 4.0 + 2.0 * k)
            mouth, eyes, brows = "grit", "squint", 1.0
        else:
            # The shove: real at last. A big step and both hands out.
            u = (i - 3) / 2.0
            lean = 20.0 - 6.0 * u
            near_foot = (14.0 - 2.0 * u, 0.0)
            far_foot = (-12.0, 0.0)
            hip_x += 8.0 + 4.0 * u
            crouch = 4.0
            reach = 26.0 - 4.0 * u
            nh = fh = ("shove", reach)
            n_kind = f_kind = "palm"
            impact = 1.0 - 0.5 * u
            mouth, eyes, brows = "o", "wide", 2.0
    elif anim == "hit":
        lean = -18.0 * (0.6 + 0.4 * math.sin(math.pi * t))
        hip_x -= 4.0 * math.sin(math.pi * t)
        crouch = 2.0
        nh, fh = "cheek", (hip_x - 16.0, 80.0)
        eyes, mouth, brows = "x", "o", 2.0
    elif anim == "death":
        # A long death on stage: a hand on the heart, the knees, the floor.
        fall = min(1.0, t / 0.85)
        eyes, mouth, brows = ("wide", "o", 2.0) if fall < 0.4 else ("shut", "o_small", 1.0)
        lean = -6.0 if fall < 0.3 else -14.0
        crouch = 14.0 * min(1.0, max(0.0, (fall - 0.15) / 0.4))
        near_foot = (6.0, 0.0)
        far_foot = (-4.0, 0.0)
        hip_x += 30.0 * fall
        rot = -84.0 * max(0.0, (fall - 0.5) / 0.5) ** 1.2
        nh = "heart"
        fh = (hip_x - 18.0 + 6.0 * fall, 52.0 + 20.0 * fall) if fall < 0.6 else (hip_x - 10.0, GROUND - 16.0)
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    pen = S.Pen(f, (hip_x - 14.0, GROUND - 4.0), rot)
    hip_y = GROUND - (THIGH + SHIN - 1.0) + crouch + bob
    lr = math.radians(lean)

    def up(p, length):
        return (p[0] + math.sin(lr) * length, p[1] - math.cos(lr) * length)

    def across(p, w):
        return (p[0] + math.cos(lr) * w, p[1] + math.sin(lr) * w)

    hip = (hip_x, hip_y)
    shoulder = up(hip, TORSO - 3.0)
    neck = up(hip, TORSO)
    head = up(neck, HEAD_R + 1.2)
    hx, hy = head
    if isinstance(nh, tuple) and nh[0] == "shove":
        # Both arms straight out from the shoulder, at the height of a chest.
        reach = nh[1]
        nh = (shoulder[0] + reach, shoulder[1] + 2.0)
        fh = (shoulder[0] + reach - 2.0, shoulder[1] - 4.0)
    if nh == "cheek":
        nh = (hx + 6.0, hy + 3.0)
    if fh == "cheek":
        fh = (hx + 4.0, hy + 4.5)
    if nh == "heart":
        nh = across(up(hip, 13.0), 3.0)
    if nh is None:
        nh = (hip_x + 6.0, hip_y + 1.0)
    if fh is None:
        fh = (hip_x - 4.0, hip_y + 1.0)

    # The far arm and the far leg, in shade.
    def leg(spec, side: float, colour):
        if spec is None:
            spec = (side * 3.0, 0.0)
        dx, lift = spec
        foot = (hip_x + dx + math.sin(lr) * 3.0, GROUND - 2.0 - lift)
        knee, foot = S.joint(hip, foot, THIGH, SHIN, -1.0)
        pen.limb([hip, knee, foot], 4.4, colour)
        # On its toes when it lifts the foot, flat when it stands.
        toe = 5.5
        tip_down = 2.0 if lift > 0.5 else 0.0
        pen.poly([(foot[0] - 2.5, foot[1] - 1.6), (foot[0] + toe, foot[1] - 0.6 + tip_down), (foot[0] + toe, foot[1] + 1.8 + tip_down),
                  (foot[0] - 2.5, foot[1] + 1.8)], K.INK)

    def arm(hand, kind, light: bool):
        elbow, hand = S.joint(shoulder, hand, UPPER_ARM, FOREARM, 1.0)
        sleeve = SHIRT if light else K.shade(SHIRT, 0.82)
        pen.limb([shoulder, elbow, hand], 4.0, sleeve)
        for a, b, u in ((shoulder, elbow, 0.45), (elbow, hand, 0.3), (elbow, hand, 0.7)):
            c = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
            d = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
            nx, ny = -(b[1] - a[1]) / d * 1.9, (b[0] - a[0]) / d * 1.9
            pen.ink([(c[0] - nx, c[1] - ny), (c[0] + nx, c[1] + ny)], 1.1, STRIPE_DARK)
        _glove(pen, hand[0], hand[1], kind)
        return hand

    leg(far_foot, -1.0, TROUSERS_SHADE)
    arm(fh, f_kind, False)

    # The body: a striped shirt and red braces.
    hb, hf = across(hip, -4.5), across(hip, 4.5)
    sb, sf = across(shoulder, -5.5), across(shoulder, 5.5)
    nb, nf = across(neck, -2.6), across(neck, 2.6)
    pen.poly([hb, hf, sf, nf, nb, sb], SHIRT)
    for k in range(4):
        h0, h1 = 3.0 + k * 4.0, 4.8 + k * 4.0
        w0, w1 = 4.5 + (h0 / 16.0), 4.5 + (h1 / 16.0)
        pen.poly([across(up(hip, h0), -w0), across(up(hip, h0), w0), across(up(hip, h1), w1), across(up(hip, h1), -w1)], STRIPE_DARK, body=False)
    pen.poly([hb, across(hip, -2.0), across(shoulder, -3.0), sb], K.alpha(K.STEEL_SHADE, 0.35), body=False)
    # Trousers up to the waist, and braces over the shoulder.
    pen.poly([across(hip, -4.8), across(hip, 4.8), across(up(hip, 3.0), 4.8), across(up(hip, 3.0), -4.8)], TROUSERS)
    pen.limb([across(up(hip, 3.0), 2.2), across(shoulder, 2.6)], 1.4, BRACES, body=False)
    pen.limb([across(up(hip, 3.0), -2.6), across(shoulder, -3.0)], 1.2, K.shade(BRACES, 0.75), body=False)

    leg(near_foot, 1.0, TROUSERS)

    # The head: whiteface.
    tilt = lean * 0.3
    pen.ellipse(hx, hy, HEAD_R, HEAD_R * 1.08, S.FACE_WHITE)

    def H(x, y):
        return K.turn([(hx + x, hy + y)], hx, hy, tilt)[0]

    pen.poly([H(6.0, -1.0), H(8.2, 1.4), H(6.0, 2.4)], S.FACE_WHITE)
    # Hair combed flat and black, from the brow to the back of the head.
    pen.poly([H(-7.2, 1.0), H(-7.0, -4.0), H(-3.0, -7.6), H(2.0, -7.8), H(5.6, -5.6), H(3.0, -5.2), H(-2.0, -4.6), H(-4.6, -1.0)], HAIR)
    pen.ink([H(-4.0, -5.8), H(2.0, -6.8)], 0.6, (90, 86, 120, 255))
    ex, ey = H(3.4, -1.0)
    by = -4.2 - 0.8 * brows
    pen.ink([H(1.6, by + 0.6), H(3.4, by - 0.6), H(5.4, by + 0.4)], 0.8)
    if eyes == "x":
        pen.ink([(ex - 1.2, ey - 1.2), (ex + 1.2, ey + 1.2)], 0.9)
        pen.ink([(ex - 1.2, ey + 1.2), (ex + 1.2, ey - 1.2)], 0.9)
    elif eyes == "shut":
        pen.ink([(ex - 1.5, ey), (ex, ey + 0.9), (ex + 1.5, ey)], 0.9)
    elif eyes == "squint":
        pen.ink([(ex - 1.5, ey - 0.3), (ex + 1.5, ey + 0.2)], 1.0)
    else:
        r = 1.5 if eyes == "wide" else 1.1
        pen.dot(ex, ey, r)
        pen.dot(ex - 0.4, ey - 0.5, 0.4, K.WHITE)
    # The painted tear under the eye.
    tx, ty = H(2.4, 2.0)
    pen.poly([(tx, ty - 1.2), (tx + 0.8, ty + 0.6), (tx - 0.8, ty + 0.6)], K.INK, body=False)
    mx, my = H(5.0, 4.4)
    if mouth == "o":
        pen.ellipse(mx, my, 1.3, 1.8, LIPS, body=False)
        pen.ellipse(mx, my, 0.7, 1.1, K.INK, body=False)
    elif mouth == "o_small":
        pen.ellipse(mx, my, 1.0, 1.1, LIPS, body=False)
    elif mouth == "grit":
        pen.ink([(mx - 1.8, my), (mx + 1.4, my - 0.3)], 1.3, LIPS)
    else:
        pen.ink([(mx - 1.8, my - 0.6), (mx, my + 0.6), (mx + 1.6, my - 0.6)], 1.2, LIPS)

    nh = arm(nh, n_kind, True)

    # The things that are not there.
    if wall:
        x, y0, y1, a = wall
        _wall(f, x, y0, y1, a)
    if rope:
        rx, ry = rope
        _rope(f, (min(nh[0], fh[0]) - 2.0, (nh[1] + fh[1]) / 2.0), (rx, ry), 0.7)
    if impact > 0.0:
        cx, cy = nh[0] + 2.0, nh[1] - 2.0
        for k in range(5):
            a = math.radians(-60.0 + k * 30.0)
            r0 = 5.0
            f.ink([(cx + math.cos(a) * r0, cy + math.sin(a) * r0), (cx + math.cos(a) * (r0 + 6.0 * impact), cy + math.sin(a) * (r0 + 6.0 * impact))],
                  1.2, K.alpha(S.SPOT, 0.95))
    if alarm:
        S.alarm_mark(f, hx + 13.0, hy - 16.0)
    return f.finish(width=1.4, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
