"""The Scorpion Man: the guard of the mountain in the Epic of Gilgamesh.

In the epic, scorpion men guard the gate of the mountain where the sun
goes in and out. This one is a man above and a scorpion below. The man has
a long curled beard, black as lapis is dark, and the tall horned cap of the
gods; he wears a belt of lapis where the man ends and the scorpion begins.
The scorpion has a shell of dark bronze, eight legs and a long tail that
arches over his head to a stinger with an amber tip.

He scuttles. He holds up one hand, palm out: no one passes. When he sees
you he points at you and his tail rises. His windup cocks the tail high and
back, and the stinger glints; his strike brings the stinger over his head
and down in front of him. A hit makes the tail droop; at his death his legs
fold under him and he sinks.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _history_ancient_kit as H
from . import _stage_kit as S

TARGET_NAME = "scorpion_man"
FRAME_SIZE = (160, 160)
ROWS = K.ENEMY_ROWS
GROUND = 154.0

ACTOR_METADATA = H.enemy_metadata(
    TARGET_NAME, "Scorpion Man", "crescent", "Multileg", "Standard", "Medium", "Walk", ["epic", "scorpion", "guard"],
    "The guard of the mountain from the Epic of Gilgamesh, in the History dimension's Fertile Crescent: a bearded man "
    "in a horned cap above, a scorpion below. He holds up a hand (no one passes), cocks his tail and stings over his "
    "head.",
)

SKIN = (198, 136, 92, 255)
SKIN_SHADE = (156, 98, 62, 255)
BEARD = (40, 36, 62, 255)
BEARD_LIGHT = (84, 80, 120, 255)
SHELL = (124, 74, 46, 255)
SHELL_LIGHT = (178, 116, 70, 255)
SHELL_DARK = (78, 44, 30, 255)
STING = (255, 170, 40, 255)
CAP = H.GOLD
CAP_SHADE = H.GOLD_DARK

Point = Tuple[float, float]


def _tail(root: Point, a0: float, curl: float, seg: float = 16.0, count: int = 8) -> List[Point]:
    """The joints of the tail from its root. Each segment turns from the
    one before it (clockwise on the screen), little at the root and much at
    the tip, so the tail rises and then curls over."""
    pts = [root]
    a = a0
    for k in range(count):
        r = math.radians(a)
        x, y = pts[-1]
        ln = seg * (1.0 - 0.05 * k)
        pts.append((x + math.cos(r) * ln, y + math.sin(r) * ln))
        a += curl * (0.2 + 1.6 * k / (count - 1))
    return pts


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)

    bx, bob, lean, gait, sink, fold = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    a0, curl = -105.0, 26.0
    hand, eyes, mouth, glint, fade, alarm = "halt", "open", "frown", 0.0, 1.0, False
    if anim == "idle":
        bob = 0.8 * math.sin(cyc)
        a0 += 4.0 * math.sin(cyc)
        curl += 2.0 * math.sin(cyc + 1.0)
        gait = 0.15 * math.sin(cyc)
    elif anim == "walk":
        gait = cyc
        bob = -1.0 * abs(math.sin(cyc * 2.0))
        a0 += 3.0 * math.sin(cyc * 2.0)
        hand = "swing"
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.3))
        a0, curl = -105.0 + 8.0 * k, 26.0 - 2.0 * k
        hand, eyes, mouth, alarm = "point", "wide", "open", True
        lean = 4.0 * k
    elif anim == "windup":
        a0, curl = -122.0 + 2.0 * math.sin(cyc * 2.0), 26.0
        lean, bx = -8.0, -4.0
        hand, eyes, mouth = "guard", "narrow", "grit"
        glint = 0.6 + 0.4 * math.sin(cyc * 2.0)
    elif anim == "attack_side":
        # The sting: from cocked (0) over the head and down in front (0.5),
        # then back.
        u = min(1.0, t * 1.4)
        s = math.sin(math.pi * 0.5 * min(1.0, u * 1.6))
        back = max(0.0, u - 0.7) / 0.3
        a0 = -122.0 + 70.0 * s - 22.0 * back
        curl = 26.0 - 9.0 * s + 9.0 * back
        lean, bx = -8.0 + 20.0 * s - 6.0 * back, -4.0 + 8.0 * s
        hand, eyes, mouth = "guard", "narrow", "open"
        glint = 1.0 - back
    elif anim == "hit":
        k = math.sin(math.pi * t)
        a0, curl = -105.0 - 25.0 * k, 26.0 - 8.0 * k
        lean, bx = -12.0 * k, -5.0 * k
        hand, eyes, mouth = "flail", "shut", "open"
    elif anim == "death":
        u = min(1.0, t / 0.8)
        fold, sink = u, 14.0 * u
        a0, curl = -105.0 + 15.0 * u, 26.0 + 6.0 * u
        lean = 30.0 * u
        hand, eyes, mouth = "limp", "shut", "open"
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    # The scorpion's body: a head shell in front, the long back behind it.
    by = GROUND - 22.0 + bob + sink
    back_x, front_x = 44.0 + bx, 100.0 + bx
    hip = (front_x - 8.0, by - 10.0)

    def leg(x: float, phase: float, near: bool) -> None:
        lift = max(0.0, math.sin(phase)) * 4.0 if anim == "walk" else 0.0
        step = math.cos(phase) * 5.0 if anim == "walk" else 2.0 * math.sin(phase)
        root = (x, by + 2.0)
        spread = 22.0 if near else 15.0
        foot = (x + step + (spread if x > (back_x + front_x) / 2.0 else -spread), GROUND - 2.0 - lift)
        if fold:
            foot = (x + (foot[0] - x) * (1.0 - 0.6 * fold), foot[1] - 10.0 * fold)
        # The knee stands high and out, as a scorpion's does.
        knee = (root[0] + (foot[0] - root[0]) * 0.55, by - 13.0 + 8.0 * fold)
        colour = SHELL if near else SHELL_DARK
        f.limb([root, knee], 4.6 if near else 3.8, colour)
        f.limb([knee, foot], 3.2 if near else 2.6, colour)
        f.limb([(foot[0], foot[1] - 1.0), (foot[0] + (2.0 if foot[0] > root[0] else -2.0), foot[1])], 2.0, colour)
        f.ink([(knee[0] - 1.0, knee[1] + 1.0), (knee[0] + 1.0, knee[1] - 1.0)], 1.0, SHELL_LIGHT if near else SHELL)

    xs = [back_x + 12.0, back_x + 24.0, back_x + 36.0, back_x + 46.0]
    for k, x in enumerate(xs):
        leg(x - 2.0, gait + k * 1.6 + math.pi, False)

    def draw_tail() -> None:
        """The tail and its stinger."""
        root = (back_x + 2.0, by - 8.0)
        tail = _tail(root, a0, curl)
        if tail_in_front:
            # Over the man, the tail needs its own ink edge.
            f.limb(tail, 12.4, H.OUTLINE, body=False)
        for k in range(len(tail) - 1):
            w = 10.0 - 0.6 * k
            f.limb([tail[k], tail[k + 1]], w, SHELL if k % 2 == 0 else SHELL_LIGHT)
            f.ink([tail[k + 1], (tail[k + 1][0] + 0.1, tail[k + 1][1] + 0.1)], w * 0.9, SHELL_DARK)
        # The stinger: a bulb and a hooked point.
        tip = tail[-1]
        prev = tail[-2]
        ang = math.atan2(tip[1] - prev[1], tip[0] - prev[0])
        bulb = (tip[0] + math.cos(ang) * 4.0, tip[1] + math.sin(ang) * 4.0)
        f.ellipse(bulb[0], bulb[1], 5.5, 5.0, SHELL_LIGHT)
        hook_a = ang + math.radians(50.0)
        point = (bulb[0] + math.cos(hook_a) * 9.0, bulb[1] + math.sin(hook_a) * 9.0)
        side = (math.cos(hook_a + math.pi / 2.0) * 2.2, math.sin(hook_a + math.pi / 2.0) * 2.2)
        f.poly([(bulb[0] + side[0], bulb[1] + side[1]), point, (bulb[0] - side[0], bulb[1] - side[1])], STING)
        if glint:
            f.glow(point[0], point[1], 3.5 + 2.0 * glint, K.alpha(STING, 0.6 * glint))
            f.ink([(point[0] - 3.0, point[1]), (point[0] + 3.0, point[1])], 0.8, K.alpha(K.WHITE, glint))
            f.ink([(point[0], point[1] - 3.0), (point[0], point[1] + 3.0)], 0.8, K.alpha(K.WHITE, glint))

    # The tail is behind the man, but in front of him when it strikes.
    tail_in_front = anim == "attack_side" and 0.15 < t < 0.8
    if not tail_in_front:
        draw_tail()

    # The back: plates in a row.
    f.poly([(back_x - 2.0, by - 6.0), (back_x + 6.0, by - 12.0), (front_x - 14.0, by - 14.0), (front_x - 4.0, by - 10.0), (front_x - 2.0, by + 2.0),
            (back_x + 6.0, by + 4.0), (back_x - 2.0, by + 1.0)], SHELL)
    f.poly([(back_x + 2.0, by - 8.0), (back_x + 6.0, by - 11.0), (front_x - 14.0, by - 13.0), (front_x - 8.0, by - 9.0), (back_x + 6.0, by - 6.0)],
           SHELL_LIGHT, body=False)
    for k in range(5):
        x = back_x + 8.0 + k * 10.0
        f.ink([(x, by - 12.0 + 0.2 * k), (x - 1.0, by + 3.0)], 1.2, SHELL_DARK)

    for k, x in enumerate(xs):
        leg(x + 2.0, gait + k * 1.6, True)

    # The man: from the belt up, on the front of the shell.
    lr = math.radians(lean)

    def up(p, length):
        return (p[0] + math.sin(lr) * length, p[1] - math.cos(lr) * length)

    def across(p, w):
        return (p[0] + math.cos(lr) * w, p[1] + math.sin(lr) * w)

    waist = hip
    shoulder = up(waist, 26.0)
    neck = up(waist, 30.0)
    head = up(across(neck, 1.5), 10.0)
    hx, hy = head
    pen = S.Pen(f)

    def arm(hand_pt, colour, near: bool):
        sh = across(shoulder, 4.0 if near else -4.0)
        elbow, hnd = S.joint(sh, hand_pt, 15.0, 14.0, 1.0)
        pen.limb([sh, elbow, hnd], 6.4, colour)
        pen.ellipse(hnd[0], hnd[1], 3.6, 3.4, colour)
        # A gold band on the wrist.
        pen.limb([(hnd[0] - (hnd[0] - elbow[0]) * 0.25, hnd[1] - (hnd[1] - elbow[1]) * 0.25), (hnd[0] - (hnd[0] - elbow[0]) * 0.32, hnd[1] - (hnd[1] - elbow[1]) * 0.32)],
                 6.8, H.GOLD, body=False)
        return hnd

    sx, sy = shoulder
    if hand == "halt":
        near_h, far_h = (sx + 22.0, sy - 14.0), (sx - 4.0, sy + 22.0)
    elif hand == "swing":
        sw = math.sin(cyc * 2.0)
        near_h, far_h = (sx + 8.0 + 6.0 * sw, sy + 24.0), (sx - 6.0 - 6.0 * sw, sy + 22.0)
    elif hand == "point":
        near_h, far_h = (sx + 30.0, sy - 2.0), (sx - 6.0, sy + 20.0)
    elif hand == "guard":
        near_h, far_h = (sx + 20.0, sy + 6.0), (sx + 16.0, sy - 8.0)
    elif hand == "flail":
        near_h, far_h = (sx + 14.0, sy - 22.0), (sx - 14.0, sy - 18.0)
    else:
        near_h, far_h = (sx + 12.0, sy + 26.0), (sx + 2.0, sy + 26.0)

    arm(far_h, SKIN_SHADE, False)
    # The trunk: broad shoulders, a lapis belt at the shell.
    wb, wf = across(waist, -9.0), across(waist, 9.0)
    sb, sf = across(shoulder, -11.0), across(shoulder, 10.0)
    f.poly([wb, wf, across(up(waist, 14.0), 11.0), sf, across(neck, 4.0), across(neck, -4.0), sb, across(up(waist, 14.0), -10.0)], SKIN)
    f.poly([wb, across(waist, -3.0), across(up(waist, 16.0), -4.0), across(shoulder, -5.0), sb, across(up(waist, 14.0), -10.0)], SKIN_SHADE, body=False)
    f.ink([across(up(waist, 20.0), 0.0), across(up(waist, 22.0), 7.0)], 1.0, SKIN_SHADE)
    f.poly([across(waist, -10.0), across(waist, 10.0), across(up(waist, 6.0), 10.0), across(up(waist, 6.0), -10.0)], H.LAPIS)
    f.ink([across(up(waist, 3.0), -10.0), across(up(waist, 3.0), 10.0)], 1.2, H.GOLD)

    # The head: a long curled beard, the horned cap.
    f.ellipse(hx, hy, 8.6, 9.6, SKIN)
    tilt = lean * 0.4

    def Hd(x, y):
        return K.turn([(hx + x, hy + y)], hx, hy, tilt)[0]

    nose = [Hd(6.0, -2.0), Hd(11.0, 2.4), Hd(6.5, 3.6)]
    f.poly(nose, SKIN)
    # The beard: rows of curls down to the chest.
    beard = [Hd(-6.0, 0.0), Hd(-2.0, 4.0), Hd(7.0, 5.0), Hd(9.0, 9.0), Hd(7.0, 22.0), Hd(0.0, 24.0), Hd(-5.0, 18.0)]
    f.poly(beard, BEARD)
    for row in range(4):
        for col in range(3):
            cx0, cy0 = Hd(-2.5 + col * 3.6, 8.0 + row * 4.2)
            f.ink([(cx0 - 1.2, cy0 + 0.6), (cx0, cy0 - 0.8), (cx0 + 1.2, cy0 + 0.6)], 0.8, BEARD_LIGHT)
    # The moustache over the mouth, and the mouth.
    f.ink([Hd(2.0, 4.6), Hd(6.0, 5.0), Hd(9.0, 4.4)], 1.6, BEARD)
    if mouth == "open":
        f.ellipse(*Hd(6.8, 6.8), 1.6, 1.4, (100, 30, 30, 255), body=False)
    elif mouth == "grit":
        f.poly([Hd(4.5, 6.0), Hd(8.6, 6.0), Hd(8.6, 7.6), Hd(4.5, 7.6)], K.WHITE, body=False)
    # Hair down the back of the neck, in curls.
    f.poly([Hd(-8.0, -4.0), Hd(-2.0, -6.0), Hd(-3.0, 2.0), Hd(-6.0, 10.0), Hd(-10.0, 8.0)], BEARD)
    f.ink([Hd(-8.0, 6.0), Hd(-6.0, 5.0)], 0.8, BEARD_LIGHT)
    ex, ey = Hd(4.4, -1.6)
    if eyes == "shut":
        f.ink([(ex - 1.8, ey), (ex + 1.8, ey + 0.4)], 1.0, H.OUTLINE)
    else:
        r = {"open": 1.6, "wide": 2.0, "narrow": 1.1}[eyes]
        f.ellipse(ex, ey, 2.2, r, K.WHITE, body=False)
        f.dot(ex + 0.8, ey + 0.1, 1.0, H.OUTLINE)
    brow = -4.4 if eyes != "narrow" else -3.4
    f.ink([Hd(1.4, brow - (0.6 if eyes == "narrow" else 0.0)), Hd(7.4, brow + (0.8 if eyes == "narrow" else -0.4))], 1.6, BEARD)
    # The horned cap: a tall drum of gold with three pairs of horns round it.
    cap = [Hd(-8.0, -6.0), Hd(8.0, -6.0), Hd(7.0, -21.0), Hd(-7.0, -21.0)]
    f.poly(cap, CAP)
    f.poly([Hd(2.0, -6.0), Hd(8.0, -6.0), Hd(7.0, -21.0), Hd(3.0, -21.0)], CAP_SHADE, body=False)
    for k in range(3):
        y = -9.0 - k * 4.5
        f.ink([Hd(-8.0 + 0.3 * k, y), Hd(-1.0, y + 2.2), Hd(8.0 - 0.3 * k, y)], 1.6, H.OUTLINE)
        f.limb([Hd(8.0 - 0.3 * k, y), Hd(11.0 - 0.3 * k, y - 3.0)], 1.8, CAP_SHADE)
    f.poly([Hd(-7.5, -21.0), Hd(7.5, -21.0), Hd(6.0, -24.0), Hd(-6.0, -24.0)], H.LAPIS)
    f.ellipse(*Hd(0.0, -25.5), 2.6, 2.2, CAP)

    nh = arm(near_h, SKIN, True)
    if hand == "halt":
        # The palm out: fingers up.
        for k in range(3):
            f.limb([(nh[0] - 1.6 + k * 1.6, nh[1] - 2.0), (nh[0] - 1.8 + k * 1.8, nh[1] - 6.0)], 1.6, SKIN)
    elif hand == "point":
        f.limb([(nh[0] + 2.0, nh[1]), (nh[0] + 8.0, nh[1] - 0.6)], 1.8, SKIN)

    if tail_in_front:
        draw_tail()
    if alarm:
        H.alarm_mark(f, hx + 16.0, max(16.0, hy - 24.0))
    return f.finish(outline=H.OUTLINE, width=1.5, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
