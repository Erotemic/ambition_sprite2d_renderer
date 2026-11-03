"""The Scurvy Ghost: the pale ghost of a sailor of the Age of Sail.

A sailor who died of scurvy on a long voyage: the upper half of a man in a
faded striped shirt and a knitted cap, a wisp of a tail where his legs
were, hollow eyes with a green light in them, and a big soft mouth with no
teeth in it at all. He glows a little. He wants a lemon (vitamin C; nobody
on his ship knew).

He floats and he comes at you. He dreams of a lemon when he is idle. His
windup lifts his arms and opens his mouth wide; his strike is a lunge and a
bite with no teeth. A hit makes him ripple; at his death a lemon at last
falls into his hands, he smiles, and he rises and fades away.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List

from . import _art_cast_kit as K
from . import _history_modern_kit as H
from . import _stage_kit as S

TARGET_NAME = "scurvy_ghost"
FRAME_SIZE = (128, 128)
ROWS = K.ENEMY_ROWS

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Scurvy Ghost", "Blob", "Small", "Light", "Float", ["history", "sail", "ghost", "floating"],
    "The pale ghost of a sailor who died of scurvy in the Age of Sail of the History dimension: a striped shirt, a "
    "knitted cap, a wisp for legs and no teeth. He floats at you and bites with his gums. He wants a lemon.",
)
ACTOR_METADATA["tags"] = ["enemy", "history"]

GHOST = (214, 240, 226, 255)
GHOST_SHADE = (150, 200, 184, 255)
GHOST_DEEP = (96, 150, 138, 255)
STRIPE = (120, 170, 196, 255)
CAP = (110, 150, 176, 255)
GUMS = (232, 150, 160, 255)
EYE_LIGHT = (170, 255, 200, 255)
OUTLINE = (34, 70, 64, 255)


def _lemon(pen, x: float, y: float, r: float = 4.0, angle: float = -20.0) -> None:
    pts = K.turn(K.ellipse_points(x, y, r * 1.3, r, 20) + [], x, y, angle)
    pen.poly(pts, H.LEMON)
    tip = K.turn([(x + r * 1.55, y)], x, y, angle)[0]
    pen.ellipse(tip[0], tip[1], r * 0.35, r * 0.3, H.LEMON)
    pen.ellipse(*K.turn([(x + r * 0.2, y + r * 0.35)], x, y, angle)[0], r * 0.9, r * 0.45, H.LEMON_DARK, body=False)
    pen.dot(*K.turn([(x - r * 0.4, y - r * 0.4)], x, y, angle)[0], r * 0.22, K.alpha(H.WHITE, 0.9))
    leaf = K.turn([(x - r * 1.2, y - r * 0.6), (x - r * 2.2, y - r * 1.4), (x - r * 1.0, y - r * 1.3)], x, y, angle)
    pen.poly(leaf, (90, 160, 70, 255))


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    flat = S.Pen(f)

    cx, cy = 58.0, 68.0
    lean, sx, sy = 0.0, 1.0, 1.0
    eyes, mouth, arms, fade, alarm = "hollow", 0.25, "hang", 1.0, False
    tail_swing, dream, lemon_held, ripple = math.sin(cyc), 0.0, False, 0.0
    if anim == "idle":
        cy += 2.5 * math.sin(cyc)
        mouth = 0.2 + 0.15 * max(0.0, math.sin(cyc * 2.0))
        # He dreams of a lemon: a bubble grows over his head and fades.
        dream = math.sin(math.pi * t)
    elif anim == "walk":
        cy += 1.5 * math.sin(cyc * 2.0)
        lean, arms = 16.0, "reach"
        tail_swing = 0.6 * math.sin(cyc * 2.0) - 0.8
        mouth = 0.4
    elif anim == "notice":
        sy = 1.0 + 0.1 * math.sin(math.pi * t)
        eyes, mouth, alarm, arms = "wide", 0.7, True, "up"
        cy -= 3.0 * math.sin(math.pi * t)
    elif anim == "windup":
        lean, arms, eyes = -14.0, "up", "glare"
        mouth = 0.95 + 0.05 * math.sin(cyc * 2.0)
        sx, sy = 1.06, 1.06
        cx -= 3.0
        tail_swing = 0.4 * math.sin(cyc * 2.0) + 0.6
    elif anim == "attack_side":
        u = min(1.0, t * 1.6)
        strike = math.sin(math.pi * 0.5 * u)
        lean = -14.0 + 34.0 * strike
        cx += 14.0 * strike
        cy += 3.0 * strike
        arms, eyes = "grab", "glare"
        # The bite: wide open, then the gums clap shut.
        mouth = 1.0 if u < 0.55 else max(0.05, 1.0 - (u - 0.55) * 3.0)
        tail_swing = -1.0
    elif anim == "hit":
        sx, sy = 1.15, 0.85
        eyes, mouth, arms = "shut", 0.5, "flail"
        ripple = 1.0 - t
        cx -= 5.0 * math.sin(math.pi * t)
        fade = 0.75 + 0.25 * t
    elif anim == "death":
        # A lemon falls into his hands. He smiles. He goes up, and away.
        eyes, mouth, arms, lemon_held = "happy", -1.0, "hold", True
        cy -= 30.0 * max(0.0, t - 0.3) ** 1.2
        fade = 1.0 - max(0.0, t - 0.5) / 0.5

    lr = math.radians(lean)

    def P(x, y):
        """A point of the body, turned with the lean about the waist."""
        dx, dy = (x - cx) * sx, (y - cy) * sy
        return (cx + dx * math.cos(lr) - dy * math.sin(lr), cy + dx * math.sin(lr) + dy * math.cos(lr))

    def wob(k: float) -> float:
        return ripple * 2.0 * math.sin(k * 1.7 + t * 9.0)

    # The tail: a wisp that thins and curls under him, behind the body.
    tail = []
    for k in range(10):
        u = k / 9.0
        tail.append(P(cx - 2.0 - 10.0 * u * u * (1.0 + 0.6 * tail_swing) + 4.0 * math.sin(u * 3.0 + cyc), cy + 12.0 + 24.0 * u))
    widths = [24.0 * (1.0 - u / 10.0) ** 1.4 + 1.5 for u in range(10)]
    left, right = H.tapered(tail, widths)
    f.poly(left + right[::-1], GHOST)
    f.poly([((a[0] + b[0]) / 2.0 + 2.0, (a[1] + b[1]) / 2.0) for a, b in zip(left, right)][2:] + right[::-1][:-2], GHOST_SHADE, body=False)
    end = tail[-1]
    f.limb([end, (end[0] + 3.0, end[1] + 2.0), (end[0] + 5.0, end[1] - 1.5)], 2.0, GHOST)

    # The far arm, behind the body.
    def arm(sh, kind, near: bool):
        if kind == "reach":
            hand = (sh[0] + 17.0, sh[1] + 2.0 + 2.0 * math.sin(cyc * 2.0 + (0 if near else 1.5)))
        elif kind == "up":
            hand = (sh[0] + (4.0 if near else -2.0), sh[1] - 16.0)
        elif kind == "grab":
            hand = (sh[0] + 19.0, sh[1] + (-3.0 if near else 3.0))
        elif kind == "flail":
            hand = (sh[0] + (8.0 if near else -10.0), sh[1] - 12.0)
        elif kind == "hold":
            hand = (sh[0] + 10.0, sh[1] + 9.0)
        else:
            hand = (sh[0] + 4.0 + 2.0 * math.sin(cyc + (0 if near else 1.0)), sh[1] + 14.0)
        elbow, hand = S.joint(sh, hand, 9.0, 9.0, 1.0)
        f.limb([sh, elbow, hand], 4.4, GHOST if near else GHOST_SHADE)
        # Long thin fingers.
        for k in range(3):
            a = math.atan2(hand[1] - elbow[1], hand[0] - elbow[0]) + (k - 1) * 0.45
            f.limb([hand, (hand[0] + math.cos(a) * 3.6, hand[1] + math.sin(a) * 3.6)], 1.4, GHOST if near else GHOST_SHADE)
        return hand

    far_sh = P(cx - 3.0, cy - 14.0)
    arm(far_sh, arms, False)

    # The body: a sailor's shirt with faded stripes, a waist that goes to wisp.
    body = [P(cx - 11.0 + wob(1), cy - 16.0), P(cx + 9.0 + wob(2), cy - 16.0), P(cx + 12.0 + wob(3), cy - 2.0),
            P(cx + 10.0, cy + 14.0), P(cx - 12.0, cy + 14.0), P(cx - 13.0 + wob(4), cy - 2.0)]
    f.poly(body, GHOST)
    for k in range(4):
        y = cy - 10.0 + k * 6.0
        f.poly([P(cx - 12.4, y), P(cx + 11.0, y), P(cx + 11.0, y + 2.4), P(cx - 12.4, y + 2.4)], K.alpha(STRIPE, 0.75), body=False)
    f.poly([P(cx - 13.0, cy - 2.0), P(cx - 6.0, cy - 6.0), P(cx - 6.0, cy + 14.0), P(cx - 12.0, cy + 14.0)], K.alpha(GHOST_DEEP, 0.35), body=False)
    # A sailor's collar: a flap of the shirt, and a knotted kerchief.
    f.poly([P(cx - 10.0, cy - 16.0), P(cx - 2.0, cy - 16.0), P(cx - 4.0, cy - 9.0), P(cx - 12.0, cy - 10.0)], STRIPE, body=False)
    f.poly([P(cx + 2.0, cy - 15.0), P(cx + 6.0, cy - 15.0), P(cx + 5.0, cy - 8.0), P(cx + 2.4, cy - 10.0)], K.alpha(H.SEAL_RED, 0.7), body=False)

    # The head: gaunt, a knitted cap, hollow eyes and a soft open mouth.
    hx, hy = P(cx + 1.0, cy - 25.0)
    f.ellipse(hx, hy, 9.0 * sx, 10.0 * sy, GHOST)
    f.ellipse(hx - 4.0, hy + 2.0, 3.0, 4.0, K.alpha(GHOST_DEEP, 0.35), body=False)
    cap = [(hx - 9.4, hy - 2.0), (hx - 8.0, hy - 8.0), (hx - 2.0, hy - 11.6), (hx + 5.0, hy - 10.4), (hx + 9.0, hy - 5.0), (hx + 9.6, hy - 2.6)]
    f.poly(cap + [(hx + 9.6, hy - 1.0), (hx - 9.4, hy - 0.2)], CAP)
    f.poly([(hx - 9.4, hy - 3.0), (hx + 9.6, hy - 3.6), (hx + 9.6, hy - 0.8), (hx - 9.4, hy - 0.2)], K.shade(CAP, 0.75), body=False)
    for k in range(4):
        x = hx - 6.0 + k * 4.0
        f.ink([(x, hy - 4.0), (x + 0.6, hy - 8.5)], 0.6, K.shade(CAP, 0.8))
    # The bobble of the cap, which floats behind like the rest of him.
    f.ellipse(hx - 9.0 - lean * 0.1, hy - 10.0, 2.6, 2.6, K.shade(CAP, 1.15))

    ex = hx + 3.4
    for k, ox in enumerate((-4.0, 3.2)):
        x, y = ex + ox, hy + 1.6
        if eyes == "shut":
            f.ink([(x - 2.0, y), (x + 2.0, y + 0.8)], 1.2, GHOST_DEEP)
        elif eyes == "happy":
            f.ink([(x - 2.0, y + 0.8), (x, y - 1.0), (x + 2.0, y + 0.8)], 1.1, GHOST_DEEP)
        else:
            big = 1.25 if eyes == "wide" else 1.0
            f.ellipse(x, y, 2.7 * big, 3.3 * big, GHOST_DEEP, body=False)
            if eyes == "glare":
                f.poly([(x - 2.8, y - 3.4), (x + 2.8, y - 1.0 if k == 0 else y - 3.4), (x + 2.8, y - 4.4), (x - 2.8, y - 4.4)], GHOST, body=False)
            f.dot(x + 0.4, y + 0.3, 1.2 * big, EYE_LIGHT)
            f.glow(x + 0.4, y + 0.3, 2.4 * big, K.alpha(EYE_LIGHT, 0.6))
    # The mouth: soft pink gums and not one tooth.
    mx, my = hx + 3.0, hy + 6.6
    if mouth < 0.0:
        f.ink([(mx - 3.4, my - 0.6), (mx, my + 1.4), (mx + 3.4, my - 0.6)], 1.0, GHOST_DEEP)
    else:
        oh = 1.0 + 4.2 * mouth
        f.ellipse(mx, my + oh * 0.3, 3.2 + 1.2 * mouth, oh, GUMS, body=False)
        f.ellipse(mx, my + oh * 0.35, 2.2 + 0.8 * mouth, oh * 0.62, (70, 40, 60, 255), body=False)
        if mouth > 0.5:
            f.ellipse(mx + 0.5, my + oh * 0.75, 1.6, 1.0, (210, 90, 110, 255), body=False)

    near_sh = P(cx + 6.0, cy - 13.0)
    hand = arm(near_sh, arms, True)
    if lemon_held:
        # The lemon falls from above into his hands.
        drop = min(1.0, t / 0.3)
        lx, ly = hand[0] + 2.0, hand[1] - 3.0 - 30.0 * (1.0 - drop) ** 2
        _lemon(flat, lx, ly, 4.0, -20.0 + 60.0 * (1.0 - drop))
        if drop >= 1.0:
            for k in range(3):
                a = math.radians(-120.0 + k * 30.0)
                f.ink([(lx + math.cos(a) * 7.0, ly + math.sin(a) * 7.0), (lx + math.cos(a) * 10.0, ly + math.sin(a) * 10.0)], 1.0, H.LEMON)

    if dream > 0.15:
        # The dream: a bubble with a lemon in it, and two small bubbles.
        bx, by = hx - 20.0, hy - 18.0
        r = 9.0 * dream
        f.ellipse(hx - 9.0, hy - 9.0, 1.4 * dream, 1.4 * dream, K.alpha(H.WHITE, 0.9))
        f.ellipse(hx - 12.5, hy - 12.0, 2.2 * dream, 2.2 * dream, K.alpha(H.WHITE, 0.9))
        f.ellipse(bx, by, r, r * 0.85, K.alpha(H.WHITE, 0.95))
        if dream > 0.5:
            _lemon(flat, bx, by, 3.6 * dream, -20.0)
    if ripple > 0.0:
        for k in range(5):
            a = math.tau * k / 5.0 + 0.4
            f.ellipse(cx + math.cos(a) * 24.0, cy + math.sin(a) * 22.0, 1.8, 1.8, K.alpha(GHOST, 0.85))
    f.glow(cx, cy - 8.0, 14.0, K.alpha(GHOST, 0.12 * fade))
    if alarm:
        H.alarm_mark(f, hx + 12.0, hy - 22.0)
    return H.finish(f, fade=fade, outline=OUTLINE, glow_blur=3.0)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
