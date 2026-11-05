"""The Giant Sable of the History dimension: the palanca negra of Angola.

The giant sable antelope (Hippotragus niger variani) lives only in the
dry woodland between the Kwanza and the Luando rivers in Angola. Angola
calls it the palanca negra gigante, and its national football team is the
Palancas Negras. The bull is glossy black, with a white belly and a black
face marked with white: a thin stripe from the eye to the muzzle, and a
white muzzle and chin. A stiff black mane stands up along its neck. Its
horns are huge: they rise from the top of its head and sweep back in a
great curve, ringed with ridges, longer than a man's arm.

It is shy, but a bull fights hard. It grazes and flicks its tail and its
ears. When it sees you it throws up its head and stamps. Its windup lowers
its head until the long horns point at you, and it paws the ground; its
strike is the charge: it runs at you with its head down, then throws its
horns up. A hit jerks its head back; at its death its legs fold under it
and it lays down its head.

The frame is 224 by 192 px: the long horns, the lowered charge and the
lifted head need the room.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Sequence, Tuple

from . import _art_cast_kit as K
from . import _history_africa_kit as H
from . import _stage_kit as S

TARGET_NAME = "giant_sable"
FRAME_SIZE = (224, 192)
ROWS = K.ENEMY_ROWS
GROUND = 184.0
#: Nothing is drawn nearer the edge of the frame than this.
MARGIN = 5.0
#: The bull is drawn at this size about the middle of its ground row: the
#: frame must hold its horns, its lowered charge and its lifted head.
SIZE = 0.8
PIVOT = (112.0, GROUND)

ACTOR_METADATA = H.enemy_metadata(
    TARGET_NAME, "Giant Sable", "ndongo", "Quadruped", "Large", "Heavy", "Walk", ["antelope", "horns", "charge"],
    "The giant sable antelope of Angola (the palanca negra) in the History dimension's Ndongo and Matamba: a glossy black bull "
    "with a white belly, white marks on its black face, a stiff mane and huge horns that sweep back in a curve. It lowers its "
    "horns at you, paws the ground, and charges, then throws its horns up.",
)

COAT = (52, 40, 40, 255)
COAT_SHADE = (30, 24, 26, 255)
COAT_LIGHT = (96, 74, 66, 255)
WHITE = (236, 230, 218, 255)
WHITE_SHADE = (196, 188, 174, 255)
HORN = (74, 60, 52, 255)
HORN_RIDGE = (122, 104, 88, 255)
HOOF = (34, 28, 28, 255)
NOSE = (26, 20, 22, 255)
EYE = (120, 70, 36, 255)
EAR_INNER = (176, 132, 104, 255)

Point = Tuple[float, float]

UPPER, LOWER = 28.0, 32.0


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = H.ScaledFrame(FRAME_SIZE, SIZE, PIVOT)

    # The pose. `dx`/`dy` move the body; `tilt` turns it (degrees, + is
    # nose down); `pitch` turns the head and neck (+ is nose down); `gait`
    # and `gait_amp` move the legs; `paw` lifts and scrapes a forefoot;
    # `fold` folds the legs under the body.
    dx, dy, tilt, pitch, breathe, swish = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    gait, gait_amp, paw, stamp, toss, eyes, fade = 0.0, 0.0, 0.0, 0.0, 0.0, "open", 1.0
    fold_front, fold_back, tail_up, speed, ears, alarm = 0.0, 0.0, 0.0, 0.0, 0.0, False
    if anim == "idle":
        # It stands and breathes; its tail and one ear flick.
        breathe = math.sin(cyc)
        swish = math.sin(cyc)
        pitch = 4.0 + 3.0 * math.sin(cyc)
        ears = 0.3 * max(0.0, math.sin(cyc * 2.0))
        eyes = "shut" if i == 3 else "open"
    elif anim == "walk":
        gait, gait_amp = cyc, 1.0
        dy = -1.2 * abs(math.sin(cyc * 2.0))
        pitch = 6.0 + 3.0 * math.sin(cyc * 2.0)
        swish = 0.6 * math.sin(cyc + 1.0)
    elif anim == "notice":
        # It throws up its head, pricks its ears and stamps a forefoot.
        k = math.sin(math.pi * min(1.0, t * 1.3))
        pitch, eyes, alarm, ears, tail_up = -14.0 * k, "wide", True, k, 0.5 * k
        stamp = k
    elif anim == "windup":
        # Head down, horns pointed at you; a forefoot paws the ground.
        pitch, tilt, dx = 84.0 + 2.0 * math.sin(cyc * 2.0), 4.0, -6.0
        paw = math.sin(cyc * 2.0)
        tail_up, eyes = 0.7, "narrow"
    elif anim == "attack_side":
        # The charge: forward fast with the head down, then a toss up.
        u = min(1.0, t * 1.25)
        dx = -6.0 + 22.0 * math.sin(math.pi * 0.5 * u) - 10.0 * max(0.0, u - 0.7) / 0.3
        toss = max(0.0, math.sin(math.pi * (u - 0.4) / 0.6)) if u > 0.4 else 0.0
        pitch = 84.0 * (1.0 - toss) - 6.0 * toss
        tilt = 4.0 - 8.0 * toss
        gait, gait_amp = cyc * 1.5, 1.3 * (1.0 - toss * 0.5)
        speed = math.sin(math.pi * min(1.0, u * 1.5))
        tail_up, eyes = 1.0, "narrow"
    elif anim == "hit":
        k = math.sin(math.pi * t)
        pitch, dx, tilt, eyes = -16.0 * k, -6.0 * k, -2.0 * k, "shut"
    elif anim == "death":
        # Its legs fold under it, it sinks down and lays its head down.
        u = min(1.0, t / 0.8)
        fold_front = min(1.0, u * 1.6)
        fold_back = max(0.0, min(1.0, (u - 0.2) / 0.6))
        tilt = 8.0 * fold_front - 8.0 * fold_back
        dy = 40.0 * (0.55 * fold_front + 0.45 * fold_back)
        pitch, eyes = 40.0 * fold_front, "shut"
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    # The bull stands left of the middle, to leave room for its charge.
    dx -= 14.0
    shoulder = (140.0 + dx, 104.0 + dy)

    def B(pts: Sequence[Point]) -> List[Point]:
        """Points of the body: turned by the tilt about the shoulder."""
        return K.turn([(x + dx, y + dy + (0.0 if y < 110 else 1.0 * breathe)) for x, y in pts], shoulder[0], shoulder[1], tilt)

    sh_w = B([(140.0, 104.0)])[0]
    hp_w = B([(66.0, 106.0)])[0]

    def leg(root: Point, phase: float, front: bool, near: bool) -> None:
        colour = COAT if near else COAT_SHADE
        swing = math.sin(phase) * gait_amp
        lift = max(0.0, math.cos(phase)) * 8.0 * gait_amp
        fx = root[0] + 14.0 * swing + (2.0 if front else -2.0)
        fy = GROUND - 3.0 - lift
        if front and near and paw:
            # The paw: the foot goes up and back, then scrapes forward.
            fx = root[0] + 7.0 * paw
            fy = GROUND - 3.0 - 9.0 * max(0.0, math.sin(cyc * 2.0 + 0.6))
        if front and near and stamp:
            fy = GROUND - 3.0 - 10.0 * math.sin(math.pi * min(1.0, stamp * 1.2))
        fold = fold_front if front else fold_back
        bend = -1.0 if front else 1.0
        knee, foot = S.joint(root, (fx, fy), UPPER, LOWER, bend)
        if fold:
            # A folded leg lies under the body.
            fk = (root[0] + (8.0 if front else -4.0) + 8.0 * fold, min(GROUND - 6.0, root[1] + 18.0))
            ff = (fk[0] + (-14.0 if front else 12.0) * fold, GROUND - 5.0)
            knee = (knee[0] + (fk[0] - knee[0]) * fold, knee[1] + (fk[1] - knee[1]) * fold)
            foot = (foot[0] + (ff[0] - foot[0]) * fold, foot[1] + (ff[1] - foot[1]) * fold)
        f.limb([root, knee], 10.0 if not front else 8.6, colour)
        f.limb([knee, foot], 4.6, colour)
        # The hoof: a small dark wedge, cloven.
        hx, hy = foot
        f.poly([(hx - 3.6, hy - 2.6), (hx + 3.6, hy - 2.6), (hx + 5.0, hy + 3.0), (hx - 3.6, hy + 3.0)], HOOF)
        f.ink([(hx + 0.8, hy), (hx + 0.8, hy + 3.0)], 0.7, COAT_LIGHT)

    # Far legs.
    leg((hp_w[0] + 6.0, hp_w[1] + 10.0), gait + math.pi, False, False)
    leg((sh_w[0] - 6.0, sh_w[1] + 12.0), gait, True, False)

    # The tail: from the rump, down, with a black tuft.
    rump = B([(50.0, 96.0)])[0]
    lift = 22.0 * tail_up
    tail = [rump, (rump[0] - 5.0 - 0.4 * lift, rump[1] + 12.0 - lift), (rump[0] - 7.0 + 4.0 * swish - 0.6 * lift, rump[1] + 26.0 - 1.3 * lift),
            (rump[0] - 6.0 + 7.0 * swish - 0.8 * lift, rump[1] + 38.0 - 1.8 * lift)]
    f.limb(tail, 3.0, COAT)
    tx, ty = tail[-1]
    f.poly([(tx - 3.0, ty - 5.0), (tx + 3.0, ty - 5.0), (tx + 3.6 + 2.0 * swish, ty + 6.0), (tx - 3.6 + 2.0 * swish, ty + 7.0)], COAT_SHADE)

    # The body: deep at the chest, higher at the withers than the rump.
    body = B([(50.0, 98.0), (62.0, 92.0), (96.0, 92.0), (124.0, 88.0), (140.0, 84.0), (152.0, 90.0), (158.0, 108.0), (152.0, 128.0),
              (130.0, 134.0), (96.0, 132.0), (70.0, 128.0), (54.0, 120.0), (46.0, 108.0)])
    f.poly(body, COAT)
    # The white belly, and the white on the inside of the thigh.
    f.poly(B([(66.0, 124.0), (96.0, 128.0), (130.0, 130.0), (148.0, 126.0), (146.0, 132.0), (130.0, 135.0), (96.0, 133.5), (68.0, 129.5)]), WHITE,
           body=False)
    f.poly(B([(54.0, 116.0), (62.0, 112.0), (66.0, 124.0), (58.0, 124.0)]), WHITE_SHADE, body=False)
    # The gloss of the coat on the back and the shoulder.
    f.poly(B([(62.0, 94.0), (96.0, 94.0), (124.0, 90.0), (138.0, 87.0), (132.0, 92.0), (100.0, 97.0), (66.0, 98.0)]), COAT_LIGHT, body=False)
    f.ink(B([(140.0, 94.0), (134.0, 110.0), (142.0, 124.0)]), 1.1, COAT_SHADE)
    f.ink(B([(64.0, 100.0), (58.0, 112.0), (64.0, 124.0)]), 1.1, COAT_SHADE)

    # Near legs.
    leg((hp_w[0] - 2.0, hp_w[1] + 14.0), gait, False, True)
    leg((sh_w[0] + 4.0, sh_w[1] + 14.0), gait + math.pi, True, True)

    # The neck and the head turn by `pitch` about the base of the neck.
    base = B([(146.0, 96.0)])[0]
    pr = pitch + tilt

    def Hd(pts: Sequence[Point]) -> List[Point]:
        return K.turn([(base[0] + x, base[1] + y) for x, y in pts], base[0], base[1], pr)

    # The neck: thick and upright, with a stiff mane along its top.
    f.poly(Hd([(-12.0, -2.0), (-4.0, -24.0), (8.0, -42.0), (22.0, -44.0), (24.0, -30.0), (16.0, -10.0), (12.0, 12.0), (-6.0, 12.0)]), COAT)
    mane = Hd([(-10.0, -6.0), (-4.0, -26.0), (6.0, -44.0), (10.0, -48.0), (2.0, -46.0), (-12.0, -28.0), (-17.0, -8.0)])
    f.poly(mane, COAT_SHADE)
    for k in range(6):
        a = Hd([(-12.0 + k * 3.0, -8.0 - k * 7.0)])[0]
        b = Hd([(-15.0 + k * 3.0, -10.0 - k * 7.0)])[0]
        f.ink([a, b], 0.8, COAT_LIGHT)
    # The ear: long and narrow, up and back from the top of the head.
    er = 10.0 * ears
    f.poly(Hd([(12.0, -46.0), (0.0 - er * 0.2, -58.0 - er), (-2.0, -56.0 + 0.5 * er), (8.0, -44.0)]), COAT_SHADE)
    f.poly(Hd([(9.0, -46.0), (1.0 - er * 0.2, -55.0 - er * 0.8), (6.0, -45.0)]), EAR_INNER, body=False)
    # The head: long, with the muzzle down and forward.
    head = Hd([(8.0, -46.0), (20.0, -50.0), (30.0, -44.0), (40.0, -30.0), (46.0, -20.0), (46.0, -13.0), (40.0, -11.0), (30.0, -16.0),
               (18.0, -24.0), (10.0, -30.0)])
    f.poly(head, COAT)
    # The white marks of the face: a stripe from the eye to the muzzle,
    # and the white muzzle and chin.
    f.poly(Hd([(20.0, -38.0), (30.0, -31.0), (40.0, -21.0), (39.0, -19.0), (28.0, -28.0), (18.0, -35.0)]), WHITE, body=False)
    f.poly(Hd([(38.0, -22.0), (46.0, -18.0), (46.0, -13.0), (40.0, -11.0), (32.0, -14.6), (34.0, -18.0)]), WHITE, body=False)
    f.poly(Hd([(30.0, -16.0), (40.0, -11.0), (36.0, -9.0), (24.0, -15.0)]), WHITE_SHADE, body=False)
    f.ellipse(*Hd([(44.0, -19.0)])[0], 2.0, 1.4, NOSE, body=False)
    f.ink(Hd([(41.0, -13.0), (45.0, -14.0)]), 0.8, NOSE)
    ex, ey = Hd([(20.0, -40.0)])[0]
    if eyes == "shut":
        f.ink([(ex - 2.0, ey), (ex + 2.0, ey + 0.6)], 1.0, WHITE)
    else:
        r = {"open": 1.6, "wide": 2.2, "narrow": 1.1}[eyes]
        f.ellipse(ex, ey, 2.2, r, EYE, body=False)
        f.dot(ex + 0.5, ey, 0.9, NOSE)
        if eyes == "narrow":
            f.ink([(ex - 3.0, ey - 2.4), (ex + 2.6, ey - 1.2)], 1.1, COAT_SHADE)

    # The horns: from the top of the head, up and back in a great curve,
    # ringed with ridges. The far horn first, a little behind the near one.
    def horn(root: Point, near: bool) -> None:
        # An arc about a centre behind the root: it leaves the head going up
        # and turns back over the neck.
        r = 50.0
        cx, cy = root[0] - r, root[1]
        pts = []
        for k in range(10):
            a = math.radians(-2.0 - 122.0 * (k / 9.0))
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        pts = Hd(pts)
        colour = HORN if near else K.shade(HORN, 0.8)
        for k in range(len(pts) - 1):
            w = (8.4 - 6.0 * k / (len(pts) - 2)) * (1.0 if near else 0.9)
            f.limb([pts[k], pts[k + 1]], w, colour)
        if near:
            for k in range(1, 6):
                (x0, y0), (x1, y1) = pts[k], pts[k + 1]
                mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
                ux, uy = x1 - x0, y1 - y0
                ln = math.hypot(ux, uy) or 1.0
                nx, ny = -uy / ln, ux / ln
                w = 3.4 - 0.4 * k
                f.ink([(mx - nx * w, my - ny * w), (mx + nx * w, my + ny * w)], 0.7, HORN_RIDGE)

    horn((14.0, -48.0), False)
    horn((18.0, -47.0), True)

    if paw or speed > 0.1 or stamp > 0.6:
        for k in range(2):
            amount = (0.6 + 0.4 * abs(paw)) if paw else (speed if speed > 0.1 else 0.5)
            H.dust(f, sh_w[0] - 2.0 - k * 60.0 - (14.0 if speed else 0.0), GROUND - 2.0, amount * (1.0 - 0.3 * k),
                   f"sable:dust:{anim}:{i}:{k}", spread=1.2)
    if speed > 0.1:
        for k in range(3):
            y = 96.0 + k * 14.0 + dy
            f.ink([(max(MARGIN + 2.0, hp_w[0] - 30.0 - 10.0 * speed), y), (max(MARGIN + 6.0, hp_w[0] - 14.0), y)], 1.4, K.alpha(K.WHITE, 0.6 * speed))
    if anim == "death" and t > 0.3:
        H.dust(f, 100.0, GROUND - 2.0, min(1.0, (t - 0.3) * 2.0), f"sable:death:{i}", spread=3.0)
    if alarm:
        ax, ay = Hd([(26.0, -60.0)])[0]
        H.alarm_mark(f, min(FRAME_SIZE[0] - 14.0, ax + 18.0), max(16.0, ay))
    return f.finish(outline=H.SEPIA_INK, width=1.6, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
