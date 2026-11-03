"""The Stagehand: a crew member of the Amphitheatre, all in black.

A quick, thin figure dressed all in black, as stage crew dress so that the
audience does not see them: a black beanie, a black jumper, black trousers
and soft black shoes. A headset sits over the beanie, with a little boom
microphone and a red light on it. A roll of gaffer tape hangs at the belt.
It carries a sandbag on a rope over its shoulder: the weight that holds
the scenery down.

It moves fast and low, as crew move between scenes. Its windup lifts the
sandbag back over its shoulder on its rope; its strike swings the bag over
its head and down onto whatever is in front of it. A hit knocks the bag out of its hands; at its death it folds up and
falls back, and the sand runs out of the bag.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List

from . import _art_cast_kit as K
from . import _stage_kit as S

TARGET_NAME = "stagehand"
FRAME_SIZE = (128, 128)
ROWS = K.ENEMY_ROWS
GROUND = 124.0

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Stagehand", "Biped", "Standard", "Light", "Walk", ["stage", "crew", "sandbag"],
    "A crew member of the Amphitheatre of the Art dimension, all in black so that nobody sees it, with a headset and "
    "a sandbag on a rope. Fast and low: it lifts the bag back over its shoulder, then swings it over its head and down in front.",
)

THIGH, SHIN = 12.0, 12.0
UPPER_ARM, FOREARM = 10.0, 10.0
TORSO = 19.0
HEAD_R = 7.0
ROPE = 11.0
BURLAP = (200, 166, 108, 255)
BURLAP_SHADE = (150, 116, 70, 255)
ROPE_COLOUR = (132, 98, 56, 255)
TAPE = (150, 152, 168, 255)


def _sandbag(pen: S.Pen, top, angle: float, lying: bool = False) -> None:
    """The sandbag. `top` is its tied neck; `angle` (degrees, on the screen)
    points from the neck to its bottom."""
    a = math.radians(angle)
    d = (math.cos(a), math.sin(a))
    n = (-d[1], d[0])

    def at(s: float, w: float):
        return (top[0] + d[0] * s + n[0] * w, top[1] + d[1] * s + n[1] * w)

    if lying:
        bag = [at(0.0, -1.5), at(3.0, -6.0), at(11.0, -8.0), at(15.0, -4.0), at(15.0, 4.0), at(11.0, 8.0), at(3.0, 6.0), at(0.0, 1.5)]
    else:
        bag = [at(0.0, -1.5), at(2.5, -5.5), at(8.0, -8.0), at(13.0, -6.5), at(15.0, 0.0), at(13.0, 6.5), at(8.0, 8.0), at(2.5, 5.5), at(0.0, 1.5)]
    pen.poly(bag, BURLAP)
    pen.poly([at(8.0, 1.5), at(8.0, 8.0), at(13.0, 6.5), at(15.0, 0.0), at(12.0, 1.5)], BURLAP_SHADE, body=False)
    # The cord that ties its neck, and a stripe of paint: crew mark their weights.
    pen.ink([at(2.0, -3.0), at(2.0, 3.0)], 1.4, ROPE_COLOUR)
    pen.ink([at(7.0, -7.5), at(7.0, 7.5)], 1.8, S.VELVET)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    rng = random.Random(f"stagehand:{anim}:{i}")
    f = K.Frame(FRAME_SIZE)

    hip_x, crouch, lean, stride, bob = 52.0, 2.0, 4.0, 0.0, 0.0
    eyes, mouth, alarm, light, fade = "dot", "flat", False, (i % 2 == 0), 1.0
    carry = "shoulder"          # shoulder, swing, dropped
    swing_angle, swing_hands = 0.0, 0.0
    near_hand = far_hand = None
    rot, fall = 0.0, 0.0
    if anim == "idle":
        bob = 0.8 * math.sin(cyc)
        crouch = 2.0 + 1.0 * math.sin(cyc)
        light = t < 0.5
    elif anim == "walk":
        stride = math.sin(cyc)
        crouch = 6.0 + 1.5 * abs(math.cos(cyc))
        bob = -1.5 * abs(math.sin(cyc))
        lean = 16.0
    elif anim == "notice":
        lean, crouch, alarm, eyes = -4.0, 0.5 - 2.0 * math.sin(math.pi * t), True, "wide"
        mouth = "open"
        near_hand = "ear"
        light = True
    elif anim == "windup":
        carry, lean, crouch = "swing", -8.0, 7.0
        stride = 0.55
        swing_angle = 150.0 + 10.0 * math.sin(cyc)
        swing_hands = 0.0
        mouth = "grit"
    elif anim == "attack_side":
        s = min(1.0, t * 1.25)
        e = 1.0 - (1.0 - s) ** 2
        carry, mouth = "swing", "grit"
        swing_angle = 150.0 + 245.0 * e
        swing_hands = e
        lean = -8.0 + 26.0 * math.sin(math.pi * min(1.0, s * 1.1))
        crouch, stride = 7.0 - 3.0 * e, 0.55 + 0.4 * e
        hip_x += 7.0 * e
    elif anim == "hit":
        carry, eyes, mouth = "dropped", "x", "open"
        lean = -18.0 * (0.6 + 0.4 * math.sin(math.pi * t))
        hip_x -= 5.0 * math.sin(math.pi * t)
        crouch = 4.0
        near_hand = far_hand = "up"
    elif anim == "death":
        carry, eyes, mouth = "dropped", "x", "open"
        fall = min(1.0, t / 0.85)
        crouch = 2.0 + 10.0 * min(1.0, fall * 3.0)
        lean = -10.0 * fall
        hip_x += 14.0 * fall
        rot = -84.0 * max(0.0, (fall - 0.2) / 0.8) ** 1.2
        near_hand = far_hand = "limp"
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    pivot = (hip_x - 6.0, GROUND - 5.0)
    pen = S.Pen(f, pivot, rot)
    flat = S.Pen(f)

    hip_y = GROUND - (THIGH + SHIN - 1.0) + crouch + bob
    lr = math.radians(lean)

    def up(p, length):
        return (p[0] + math.sin(lr) * length, p[1] - math.cos(lr) * length)

    hip = (hip_x, hip_y)
    shoulder = up(hip, TORSO - 3.0)
    neck = up(hip, TORSO)
    head = up(neck, HEAD_R + 1.5)
    hx, hy = head

    # The bag on the ground: dropped, behind everything.
    if carry == "dropped":
        if anim == "death":
            bx = 96.0
            _sandbag(flat, (bx, GROUND - 9.5), 180.0, lying=True)
            # The sand runs out of the bag into a heap.
            heap = 3.0 + 7.0 * t
            flat.poly([(bx + 1.0, GROUND - 1.0), (bx + 3.0 + heap, GROUND - 1.0), (bx + 2.0 + heap * 0.5, GROUND - 1.0 - heap * 0.45)], BURLAP_SHADE)
            for k in range(int(3 + 6 * t)):
                flat.dot(bx + 2.0 + rng.uniform(0.0, heap), GROUND - 2.0 - rng.uniform(0.0, heap * 0.5), 0.6, BURLAP)
        else:
            _sandbag(flat, (hip_x + 28.0, GROUND - 9.5), 0.0, lying=True)

    # The hands: where each one goes.
    if carry == "swing":
        # The grip goes from behind the head, up over it, to in front of the chest.
        back = (shoulder[0] - 8.0, shoulder[1] - 1.0)
        front = (shoulder[0] + 15.0, shoulder[1] + 5.0)
        lift = 6.0 * math.sin(math.pi * swing_hands)
        grip = (back[0] + (front[0] - back[0]) * swing_hands, back[1] + (front[1] - back[1]) * swing_hands - lift)
        nh, fh = (grip[0] + 1.0, grip[1] + 0.5), (grip[0] - 0.5, grip[1] - 0.5)
    else:
        swing_n = math.sin(cyc) if anim == "walk" else 0.0
        nh = (hip_x + 6.0 + 9.0 * swing_n + math.sin(lr) * 8.0, hip_y + 2.0 - abs(swing_n) * 2.0)
        fh = (shoulder[0] + 2.0, shoulder[1] - 4.0)
        if anim == "idle":
            nh = (hip_x + 5.0, hip_y + 1.0 + 0.6 * math.sin(cyc))
    if near_hand == "ear":
        nh = (hx + 4.0, hy + 1.0)
    if near_hand == "up":
        nh = (shoulder[0] + 6.0, shoulder[1] - 15.0)
        fh = (shoulder[0] - 7.0, shoulder[1] - 14.0)
    if near_hand == "limp":
        nh = (hip_x + 9.0, hip_y + 8.0)
        fh = (hip_x - 9.0, hip_y + 6.0)

    # The bag on its rope, or over the shoulder.
    if carry == "shoulder":
        top = (shoulder[0] - 5.0, shoulder[1] - 1.0)
        sway = 4.0 * math.sin(cyc + 0.8) if anim in ("idle", "walk") else 0.0
        _sandbag(pen, top, 102.0 + sway + lean * 0.5)
        pen.limb([fh, top], 1.4, ROPE_COLOUR)
    elif carry == "swing":
        a = math.radians(swing_angle)
        top = (fh[0] + math.cos(a) * ROPE, fh[1] + math.sin(a) * ROPE)
        if anim == "attack_side" and 0.15 < t < 0.7:
            # Lines of speed behind the bag: the path it came along.
            for r_off in (-5.0, 0.0, 5.0):
                arc = []
                for k in range(8):
                    aa = math.radians(swing_angle - 12.0 - 55.0 * k / 7.0)
                    arc.append((fh[0] + math.cos(aa) * (ROPE + 8.0 + r_off), fh[1] + math.sin(aa) * (ROPE + 8.0 + r_off)))
                pen.ink(arc, 1.1, K.alpha(S.SPOT, 0.85))
        pen.limb([fh, top], 1.4, ROPE_COLOUR)
        _sandbag(pen, top, swing_angle)

    # The far leg and the far arm, in shade.
    def leg(side: float, colour):
        swing = stride * side
        foot = (hip_x + 9.0 * swing + side * 1.5 + math.sin(lr) * 3.0, GROUND - 2.0)
        if anim == "walk":
            foot = (foot[0], GROUND - 2.0 - max(0.0, 3.0 * math.sin(cyc + (0.0 if side > 0 else math.pi))))
        knee, foot = S.joint(hip, foot, THIGH, SHIN, -1.0)
        pen.limb([hip, knee, foot], 4.6, colour)
        pen.poly([(foot[0] - 2.5, foot[1] - 1.5), (foot[0] + 5.5, foot[1] - 0.5), (foot[0] + 5.5, foot[1] + 1.8), (foot[0] - 2.5, foot[1] + 1.8)], S.BLACK_SHADE)

    def arm(hand, colour):
        elbow, hand = S.joint(shoulder, hand, UPPER_ARM, FOREARM, 1.0)
        pen.limb([shoulder, elbow, hand], 4.0, colour)
        pen.ellipse(hand[0], hand[1], 2.3, 2.3, S.SKIN)

    leg(-1.0, S.BLACK_SHADE)
    arm(fh, S.BLACK_SHADE)

    # The body: a black jumper, a belt and a roll of tape on it.
    def side_pts(p, w):
        return ((p[0] - math.cos(lr) * w, p[1] - math.sin(lr) * w), (p[0] + math.cos(lr) * w, p[1] + math.sin(lr) * w))

    hb, hf = side_pts(hip, 5.0)
    cb, cf = side_pts(shoulder, 6.0)
    nb, nf = side_pts(neck, 3.0)
    pen.poly([hb, hf, cf, nf, nb, cb], S.BLACK_CLOTH)
    pen.poly([hb, (hip[0] - math.cos(lr) * 1.0, hip[1]), (shoulder[0] - math.cos(lr) * 2.0, shoulder[1]), cb], S.BLACK_SHADE, body=False)
    pen.ink([cf, (hf[0] + 0.5, hf[1] - 1.0)], 0.8, S.BLACK_LIGHT)
    belt = up(hip, 2.0)
    pen.ink(list(side_pts(belt, 5.2)), 1.5, S.BLACK_SHADE)
    tape = up((hip[0] + 4.5, hip[1] + 1.5), 0.0)
    pen.ellipse(tape[0], tape[1], 2.6, 2.6, TAPE)
    pen.ellipse(tape[0], tape[1], 1.1, 1.1, S.BLACK_SHADE, body=False)

    leg(1.0, S.BLACK_CLOTH)

    # The head: skin, a black beanie, the headset over it.
    tilt = lean * 0.4
    pen.ellipse(hx, hy, HEAD_R, HEAD_R, S.SKIN)
    pen.poly([(hx + 6.2, hy + 0.5), (hx + 8.6, hy + 2.2), (hx + 6.4, hy + 3.2)], S.SKIN)
    cap = [(hx - 7.6, hy - 0.5), (hx - 7.0, hy - 4.5), (hx - 3.5, hy - 7.8), (hx + 1.5, hy - 8.4), (hx + 5.5, hy - 6.6), (hx + 7.4, hy - 3.0), (hx + 7.4, hy - 1.6)]
    pen.poly(K.turn(cap, hx, hy, tilt), S.BLACK_CLOTH)
    pen.ink(K.turn([(hx - 7.4, hy - 1.4), (hx + 7.4, hy - 2.4)], hx, hy, tilt), 1.2, S.BLACK_LIGHT)
    pen.ellipse(hx - 1.2, hy + 2.6, 2.0, 1.2, S.SKIN_SHADE, body=False)
    # Headset: a band over the cap, a cup at the ear, a boom to the mouth.
    band = K.turn([(hx - 2.5, hy + 0.5), (hx - 3.5, hy - 6.0), (hx - 1.0, hy - 9.2), (hx + 2.0, hy - 9.0)], hx, hy, tilt)
    pen.ink(band, 1.5, (80, 82, 96, 255))
    cup = K.turn([(hx - 3.0, hy + 0.5)], hx, hy, tilt)[0]
    pen.ellipse(cup[0], cup[1], 2.4, 2.8, (60, 62, 76, 255))
    boom_end = K.turn([(hx + 6.0, hy + 4.6)], hx, hy, tilt)[0]
    pen.ink([cup, ((cup[0] + boom_end[0]) / 2.0, cup[1] + 4.5), boom_end], 1.0, (60, 62, 76, 255))
    pen.dot(boom_end[0], boom_end[1], 1.1, (40, 40, 50, 255))
    if light:
        pen.dot(cup[0] - 1.0, cup[1] - 2.2, 0.9, (255, 70, 70, 255))
        pen.glow(cup[0] - 1.0, cup[1] - 2.2, 1.6, (255, 70, 70, 110))
    # The face.
    ex, ey = K.turn([(hx + 3.4, hy - 0.4)], hx, hy, tilt)[0]
    if eyes == "x":
        pen.ink([(ex - 1.3, ey - 1.3), (ex + 1.3, ey + 1.3)], 0.9)
        pen.ink([(ex - 1.3, ey + 1.3), (ex + 1.3, ey - 1.3)], 0.9)
    elif eyes == "wide":
        pen.ellipse(ex, ey, 1.8, 2.1, K.WHITE, body=False)
        pen.dot(ex + 0.5, ey, 0.9)
    else:
        pen.dot(ex, ey, 1.0)
        pen.ink([(ex - 1.6, ey - 2.2), (ex + 1.6, ey - 2.6)], 0.8)
    mx, my = K.turn([(hx + 4.6, hy + 3.6)], hx, hy, tilt)[0]
    if mouth == "open":
        pen.ellipse(mx, my, 1.2, 1.4, K.INK, body=False)
    elif mouth == "grit":
        pen.poly([(mx - 2.0, my - 0.8), (mx + 1.4, my - 0.8), (mx + 1.4, my + 0.8), (mx - 2.0, my + 0.8)], K.WHITE, body=False)
        pen.ink([(mx - 2.0, my), (mx + 1.4, my)], 0.5)
    else:
        pen.ink([(mx - 1.6, my), (mx + 1.2, my - 0.2)], 0.8)

    arm(nh, S.BLACK_CLOTH)

    if alarm:
        S.alarm_mark(f, hx + 12.0, hy - 16.0)
    if anim == "hit":
        for k in range(4):
            a = math.radians(-60.0 + k * 40.0)
            x0, y0 = hx + math.cos(a) * 11.0, hy + math.sin(a) * 11.0
            f.ink([(x0, y0), (x0 + math.cos(a) * 4.0, y0 + math.sin(a) * 4.0)], 1.0, S.SPOT)
    # A dim violet outline, not ink: a figure in black must still read
    # against the dark of the stage.
    return f.finish(outline=S.CREW_OUTLINE, width=1.4, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
