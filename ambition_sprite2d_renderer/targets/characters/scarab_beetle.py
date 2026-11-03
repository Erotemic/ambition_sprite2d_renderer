"""The Scarab Beetle: a big scarab of the Nile that rolls a dung ball.

A beetle as big as a cat, its shell the blue-green of glazed faience with a
sheen of violet and gold, as the scarab of an amulet is. It has a toothed
rake on the front of its head, fans for antennae, and six legs; its front
legs are toothed for digging. It rolls a ball of dung in front of it, as
the sun god Khepri rolls the sun across the sky (and it is still dung).

It scurries fast, and the ball rolls. When it sees you it rears up behind
its ball with its fans spread. Its windup backs off and digs in, kicking up
dust; its strike shoves the ball at you and runs in behind it. A hit pops
its wing cases open; at its death it falls on its back and its legs wave,
and then stop.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List, Sequence, Tuple

from . import _art_cast_kit as K
from . import _history_ancient_kit as H

TARGET_NAME = "scarab_beetle"
FRAME_SIZE = (96, 96)
ROWS = K.ENEMY_ROWS
GROUND = 90.0

ACTOR_METADATA = H.enemy_metadata(
    TARGET_NAME, "Scarab Beetle", "nile", "Multileg", "Small", "Light", "Walk", ["beetle", "scarab", "faience"],
    "A big blue-green scarab of the History dimension's Nile that rolls a dung ball in front of it. It scurries "
    "fast, backs off and digs in, then shoves the ball at you and runs in behind it.",
)

SHELL = (38, 152, 150, 255)
SHELL_LIGHT = (120, 226, 206, 255)
SHELL_DARK = (20, 82, 98, 255)
SHEEN = (150, 110, 220, 255)
LEG = (24, 60, 76, 255)
DUNG = (122, 86, 52, 255)
DUNG_LIGHT = (164, 124, 80, 255)
DUNG_DARK = (82, 56, 34, 255)
STRAW = (222, 190, 110, 255)

Point = Tuple[float, float]

#: The beetle is drawn at this size about its middle on the ground.
SIZE = 0.85


class _Body:
    """Draws the beetle through a turn about its middle, and a flip onto its
    back (a mirror in its own horizontal line)."""

    def __init__(self, f: K.Frame, mid: Point, tilt: float, flip: float, shift: Point, pivot: Point = None) -> None:
        self.f, self.mid, self.tilt, self.flip, self.shift = f, mid, tilt, flip, shift
        self.pivot = pivot or mid

    def p(self, pts: Sequence[Point]) -> List[Point]:
        mx, my = self.mid
        out = [(x, 2.0 * my - y) if self.flip else (x, y) for x, y in pts]
        out = [(mx + (x - mx) * SIZE, GROUND + (y - GROUND) * SIZE) for x, y in out]
        out = K.turn(out, self.pivot[0], self.pivot[1], self.tilt)
        return [(x + self.shift[0], y + self.shift[1]) for x, y in out]

    def poly(self, pts, fill, body=True):
        self.f.poly(self.p(pts), fill, body)

    def limb(self, pts, w, fill, body=True):
        self.f.limb(self.p(pts), w, fill, body)

    def ink(self, pts, w=1.0, fill=H.OUTLINE):
        self.f.ink(self.p(pts), w, fill)

    def ellipse(self, cx, cy, rx, ry, fill, body=True, count=24):
        self.f.poly(self.p(K.ellipse_points(cx, cy, rx, ry, count)), fill, body)

    def dot(self, cx, cy, r, fill=H.OUTLINE):
        x, y = self.p([(cx, cy)])[0]
        self.f.dot(x, y, r, fill)


def _ball(f: K.Frame, cx: float, cy: float, r: float, spin: float) -> None:
    """The dung ball: lumpy, with straw in it; `spin` turns its marks."""
    rng = random.Random("scarab:ball")
    f.poly(K.ellipse_points(cx, cy, r, r, 26, 0.8, rng), DUNG)
    f.poly(K.ellipse_points(cx + r * 0.35, cy + r * 0.45, r * 0.5, r * 0.35, 18), DUNG_DARK, body=False)
    f.poly(K.ellipse_points(cx - r * 0.35, cy - r * 0.4, r * 0.35, r * 0.25, 14), DUNG_LIGHT, body=False)
    for k in range(6):
        a = spin + k * math.tau / 6.0 + rng.uniform(-0.3, 0.3)
        d = r * rng.uniform(0.35, 0.78)
        x, y = cx + math.cos(a) * d, cy + math.sin(a) * d
        if k % 2:
            b = a + 1.2
            f.ink([(x, y), (x + math.cos(b) * 3.5, y + math.sin(b) * 3.5)], 0.9, STRAW)
        else:
            f.dot(x, y, 1.4, DUNG_DARK)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)

    bx, tilt, flip, bob, gait, legs_wave = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    ball_dx, ball_spin, ball_dy, elytra, fans, eyes, fade = 0.0, 0.0, 0.0, 0.0, 0.5, "open", 1.0
    dig, speed, alarm = 0.0, 0.0, False
    if anim == "idle":
        bob = 0.5 * math.sin(cyc)
        fans = 0.5 + 0.3 * math.sin(cyc * 2.0)
        gait = 0.25 * math.sin(cyc)
    elif anim == "walk":
        gait = math.sin(cyc * 2.0)
        bob = -0.8 * abs(math.sin(cyc * 2.0))
        ball_spin = cyc
        fans = 0.4
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.3))
        tilt, fans, eyes, alarm = -18.0 * k, 0.5 + 0.5 * k, "wide", True
        bx = -2.0 * k
    elif anim == "windup":
        bx, tilt = -4.0, 6.0
        dig = 0.7 + 0.3 * math.sin(cyc * 2.0)
        gait = math.sin(cyc * 3.0)
        tilt += 1.5 * math.sin(cyc * 4.0)
        fans, eyes = 0.2, "narrow"
    elif anim == "attack_side":
        # The shove: the ball goes out fast, and the beetle runs in behind it.
        u = min(1.0, t * 1.4)
        push = math.sin(math.pi * 0.5 * u)
        bx = -6.0 + 11.0 * push
        ball_dx = 4.0 * push
        ball_spin = 4.0 * push
        gait = math.sin(cyc * 3.0)
        speed = math.sin(math.pi * u)
        tilt, eyes = 4.0 - 6.0 * push, "narrow"
    elif anim == "hit":
        k = math.sin(math.pi * t)
        bx, tilt, elytra, eyes = -3.0 * k, -10.0 * k, 0.9 * k, "shut"
        fans = 0.9 * k
    elif anim == "death":
        # It rolls over backwards: up to its tail, then down on its back.
        u = min(1.0, t / 0.6)
        flip = 1.0 if u >= 0.5 else 0.0
        tilt = -90.0 * (2.0 * u) if u < 0.5 else -90.0 * (1.0 - 2.0 * (u - 0.5))
        bob = -6.0 * math.sin(math.pi * u)
        legs_wave = (1.0 - t) * math.sin(cyc * 5.0)
        ball_dx = 4.0 * u
        ball_spin = 1.5 * u
        eyes = "x"
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    # The ball, in front of the beetle.
    br = 13.0
    bcx, bcy = 74.0 + ball_dx, GROUND - br + ball_dy
    if speed > 0.1:
        for k in range(3):
            y = bcy - 8.0 + k * 8.0
            f.ink([(bcx - br - 4.0 - 6.0 * speed, y), (bcx - br - 4.0 - 16.0 * speed, y)], 1.2, K.alpha(K.WHITE, 0.7 * speed))

    mid = (33.0 + bx, GROUND - 14.0)
    pivot = None
    if anim in ("notice", "hit"):
        # It rears up on its back legs.
        pivot = (mid[0] - 14.0, GROUND - 4.0)
    if anim == "death":
        # It rolls over its tail: the turn is about the back of its shell.
        mid = (mid[0] + 6.0, GROUND - 14.0)
        pivot = (mid[0] - 18.0 * SIZE, mid[1])
    pen = _Body(f, mid, tilt, flip, (0.0, bob), pivot)
    mx, my = mid

    def leg(root: Point, foot: Point, phase: float, near: bool) -> None:
        lift = max(0.0, math.sin(phase)) * 3.0
        step = math.cos(phase) * 3.0
        if flip > 0.5:
            # On its back: the legs wave in the air.
            fx, fy = root[0] + (foot[0] - root[0]) * 0.8 + 3.0 * legs_wave * (1 if near else -1), foot[1] - 2.0 + 2.0 * legs_wave
            knee = ((root[0] + fx) / 2.0 + 2.0, (root[1] + fy) / 2.0 - 3.0)
            pen.limb([root, knee, (fx, fy)], 2.4 if near else 2.0, LEG)
            return
        fx, fy = foot[0] + step, foot[1] - lift
        knee = ((root[0] + fx) / 2.0 + (5.0 if fx > root[0] else -5.0), (root[1] + fy) / 2.0 - 4.0)
        pen.limb([root, knee, (fx, fy)], 2.2 if near else 1.8, LEG)
        # The teeth on the leg.
        pen.ink([(knee[0], knee[1] + 1.0), (knee[0] + 1.6, knee[1] - 1.2)], 0.9, SHELL_DARK)

    g = math.pi * (gait + 1.0)
    # The far legs, behind the body.
    leg((mx - 6.0, my + 4.0), (mx - 18.0 - 3.0 * dig, GROUND - 1.0), g + 0.0, False)
    leg((mx + 2.0, my + 5.0), (mx + 2.0, GROUND - 1.0), g + math.pi, False)
    leg((mx + 12.0, my + 3.0), (mx + 24.0, GROUND - 8.0), g + 0.0, False)

    if anim != "death" or flip < 0.5:
        _ball(f, bcx, bcy, br, ball_spin)

    # The wing cases: one high oval shell; a hit pops them open at the back.
    shell = K.ellipse_points(mx - 4.0, my - 1.0, 17.0, 12.5, 30)
    shell = [(x, min(y, my + 7.0)) for x, y in shell]
    hinge = (mx + 10.0, my - 6.0)
    if elytra > 0.05:
        # The thin wings under the cases.
        pen.poly([(mx - 16.0, my - 2.0), (mx - 20.0 - 4.0 * elytra, my - 14.0 - 8.0 * elytra), (mx - 4.0, my - 9.0)], K.alpha((220, 230, 240, 255), 0.75), body=False)
        pen.ellipse(mx - 4.0, my + 2.0, 15.0, 6.0, SHELL_DARK)
        shell = K.turn(shell, hinge[0], hinge[1], -28.0 * elytra)
    pen.poly(shell, SHELL)
    lit = K.ellipse_points(mx - 7.0, my - 5.0, 10.0, 6.0, 20)
    pen.poly(K.turn(lit, hinge[0], hinge[1], -28.0 * elytra) if elytra > 0.05 else lit, SHELL_LIGHT, body=False)
    if elytra <= 0.05:
        pen.poly([(mx - 20.0, my + 4.0), (mx + 12.0, my + 4.0), (mx + 12.0, my + 7.0), (mx - 18.0, my + 7.0)], SHELL_DARK, body=False)
        # The sheen of violet and gold, and the grooves of the cases.
        pen.ink([(mx - 12.0, my - 8.0), (mx - 4.0, my - 11.0), (mx + 4.0, my - 10.0)], 1.5, K.alpha(SHEEN, 0.85))
        pen.ink([(mx - 15.0, my - 4.0), (mx - 11.0, my - 7.0)], 1.0, K.alpha(H.GOLD, 0.8))
        for k in range(3):
            pen.ink([(mx - 18.0 + k * 3.0, my + 3.0), (mx - 10.0 + k * 6.0, my - 6.0 + k * 0.5), (mx + 6.0 + k * 2.0, my - 3.0 + k * 2.0)], 0.6, K.alpha(SHELL_DARK, 0.7))

    # The pronotum (the shield behind the head), and the head with its rake.
    pen.poly(K.ellipse_points(mx + 15.0, my, 9.0, 8.0, 22), SHELL)
    pen.poly(K.ellipse_points(mx + 13.0, my - 3.0, 5.0, 3.5, 16), SHELL_LIGHT, body=False)
    pen.ink([(mx + 7.0, my - 5.0), (mx + 9.0, my + 5.0)], 0.9, SHELL_DARK)
    head = [(mx + 23.0, my - 3.0), (mx + 30.0, my - 4.0), (mx + 33.0, my + 0.0), (mx + 31.0, my + 5.0), (mx + 23.0, my + 5.0)]
    pen.poly(head, SHELL_DARK)
    for k in range(4):
        # The rake: the teeth on the front edge of the head.
        y = my - 3.0 + k * 2.4
        pen.poly([(mx + 31.0, y), (mx + 34.5, y + 0.8), (mx + 31.0, y + 1.8)], SHELL_DARK)
    ex, ey = mx + 27.0, my - 0.5
    if eyes == "x":
        pen.ink([(ex - 1.2, ey - 1.2), (ex + 1.2, ey + 1.2)], 0.8, K.WHITE)
        pen.ink([(ex - 1.2, ey + 1.2), (ex + 1.2, ey - 1.2)], 0.8, K.WHITE)
    elif eyes == "shut":
        pen.ink([(ex - 1.4, ey), (ex + 1.4, ey + 0.4)], 0.9, K.WHITE)
    else:
        r = {"open": 1.4, "wide": 1.9, "narrow": 1.0}[eyes]
        pen.ellipse(ex, ey, r * 1.2, r, H.GOLD, body=False)
        pen.dot(ex + 0.4, ey, r * 0.5)
    # The antennae: a stalk and a fan of three leaves at its end.
    for k, dx in enumerate((0.0, 2.0)):
        root = (mx + 28.0 + dx, my - 3.0)
        tip = (root[0] + 4.0 + 2.0 * fans, root[1] - 6.0 - 3.0 * fans)
        pen.ink([root, tip], 0.9, LEG)
        for j in range(3):
            a = math.radians(-90.0 - 30.0 + j * 30.0 * (0.5 + fans))
            pen.limb([tip, (tip[0] + math.cos(a) * 3.0, tip[1] + math.sin(a) * 3.0)], 1.4, LEG, body=k == 1)

    # The near legs, in front.
    leg((mx - 8.0, my + 6.0), (mx - 14.0 - 4.0 * dig, GROUND - 1.0), g + math.pi, True)
    leg((mx + 4.0, my + 7.0), (mx + 6.0, GROUND - 1.0), g, True)
    leg((mx + 16.0, my + 5.0), (mx + 28.0, GROUND - 10.0 + (-6.0 if anim == "notice" else 0.0)), g + math.pi, True)

    if anim == "death" and flip >= 0.5:
        _ball(f, bcx, bcy, br, ball_spin)
    H.dust(f, mx - 14.0, GROUND - 2.0, dig, f"scarab:dig:{i}", spread=0.8)
    if anim == "attack_side":
        H.dust(f, mx - 12.0, GROUND - 2.0, 0.8 * speed, f"scarab:run:{i}", spread=0.8)
    if alarm:
        H.alarm_mark(f, mx + 8.0, my - 30.0)
    return f.finish(outline=H.OUTLINE, width=1.3, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
