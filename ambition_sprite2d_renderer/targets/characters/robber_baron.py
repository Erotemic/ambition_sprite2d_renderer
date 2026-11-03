"""The Robber Baron: a tycoon of the Industrial Age, who throws coins.

A portly man in a tall black top hat with a gold band and a long fur coat
with a thick fur collar and cuffs, a gold waistcoat over a round belly with
a watch chain, a white shirt front and a black bow tie. Big white mutton
chops and a moustache, a red nose, a fat cigar. In his far hand he holds a
sack of money with a dollar sign on it.

He keeps his distance and throws coins at you (the game draws the coin
that flies: here it is only in his hand). His windup takes a coin out of
the sack and lifts it back over his shoulder; his strike throws it, and his
hand opens. A hit knocks his hat off and banknotes out of the sack; at his
death he falls back onto his money, and the notes blow away.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List

from . import _art_cast_kit as K
from . import _history_modern_kit as H
from . import _stage_kit as S

TARGET_NAME = "robber_baron"
FRAME_SIZE = (128, 128)
ROWS = K.ENEMY_ROWS
GROUND = 123.0

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Robber Baron", "Biped", "Standard", "Medium", "Walk", ["history", "industrial", "tycoon", "coin"],
    "A tycoon of the Industrial Age in the History dimension: a top hat, a fur coat, mutton chops, a cigar and a sack "
    "of money. He keeps his distance and throws coins.",
)
ACTOR_METADATA["tags"] = ["enemy", "history"]

THIGH, SHIN = 9.5, 9.5
UPPER_ARM, FOREARM = 8.6, 8.6
TORSO = 21.0
HEAD_R = 7.0
COAT = (88, 56, 40, 255)
COAT_SHADE = (62, 38, 26, 255)
WAISTCOAT = (226, 176, 64, 255)
WAISTCOAT_SHADE = (176, 126, 36, 255)
TROUSERS = (66, 64, 76, 255)
TROUSERS_SHADE = (44, 42, 54, 255)
WHISKERS = (240, 238, 232, 255)
WHISKERS_SHADE = (196, 194, 190, 255)
FACE = (246, 200, 172, 255)
NOSE = (234, 130, 120, 255)
SACK = (196, 166, 110, 255)
SACK_SHADE = (150, 120, 72, 255)
HAT = (34, 32, 38, 255)


def _fur_edge(pen: S.Pen, pts, r: float, colour, rng: random.Random) -> None:
    """A fur trim along `pts`: round tufts that overlap."""
    for k in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[k], pts[k + 1]
        steps = max(1, int(math.hypot(x1 - x0, y1 - y0) / (r * 0.9)))
        for s in range(steps):
            u = s / steps
            pen.ellipse(x0 + (x1 - x0) * u + rng.uniform(-0.4, 0.4), y0 + (y1 - y0) * u + rng.uniform(-0.4, 0.4), r * rng.uniform(0.85, 1.1), r * rng.uniform(0.85, 1.1), colour)


def _sack(pen: S.Pen, x: float, y: float, swing: float = 0.0) -> None:
    """The sack of money, held at its neck at `(x, y)`."""
    def T(px, py):
        return K.turn([(x + px, y + py)], x, y, swing)[0]

    body = [T(-2.0, 1.5), T(2.0, 1.5), T(7.0, 6.0), T(8.0, 11.0), T(5.0, 15.0), T(-5.0, 15.0), T(-8.0, 11.0), T(-7.0, 6.0)]
    pen.poly(body, SACK)
    pen.poly([T(2.0, 1.5), T(7.0, 6.0), T(8.0, 11.0), T(5.0, 15.0), T(2.0, 15.0), T(4.0, 8.0)], SACK_SHADE, body=False)
    # The neck and its tie, and the ears of cloth over it.
    pen.poly([T(-3.0, -2.4), T(0.0, 0.0), T(3.0, -2.4), T(2.0, 1.6), T(-2.0, 1.6)], SACK)
    pen.ink([T(-2.4, 1.2), T(2.4, 1.2)], 1.0, H.SEAL_RED)
    # A dollar sign on its belly.
    cx, cy = T(0.0, 9.0)
    pen.ink([(cx + 2.0, cy - 2.6), (cx - 0.6, cy - 3.0), (cx - 2.0, cy - 1.6), (cx - 0.4, cy - 0.2), (cx + 1.4, cy + 0.8),
             (cx + 1.6, cy + 2.4), (cx - 0.6, cy + 3.0), (cx - 2.4, cy + 2.4)], 1.0, H.OUTLINE)
    pen.ink([(cx, cy - 4.2), (cx, cy + 4.2)], 0.8, H.OUTLINE)


def _top_hat(hp: S.Pen, cx: float, cy: float, spin: float) -> None:
    def T(pts):
        return K.turn([(cx + x, cy + y) for x, y in pts], cx, cy, spin)

    hp.poly(T([(-7.6, 5.6), (7.6, 4.4), (8.0, 6.0), (-7.4, 7.0)]), HAT)
    hp.poly(T([(-4.8, 4.8), (5.0, 4.4), (5.8, -9.0), (-4.4, -9.0)]), HAT)
    hp.poly(T([(-4.7, 2.4), (5.1, 1.8), (5.3, -0.6), (-4.5, 0.0)]), H.GOLD, body=False)
    hp.ink(T([(-4.0, -8.4), (5.4, -8.4)]), 0.8, (90, 88, 100, 255))
    hp.ink(T([(3.2, -7.0), (3.8, 0.0)]), 0.8, (70, 68, 80, 255))


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    rng = random.Random(f"robber_baron:{anim}:{i}")
    f = K.Frame(FRAME_SIZE)

    hip_x, crouch, lean, stride, bob, belly_bounce = 50.0, 0.0, -5.0, 0.0, 0.0, 0.0
    brows, eyes, mouth, alarm, fade, rot = "smug", "lidded", "cigar", False, 1.0, 0.0
    near, far = "belly", "sack"
    coin_in_hand, hat_off, notes, smoke = False, None, 0, 0.0
    sack_swing = 0.0
    if anim == "idle":
        # He puffs his cigar, pats his belly, and the sack bounces in his hand.
        bob = 0.6 * math.sin(cyc)
        belly_bounce = 0.6 * math.sin(cyc * 2.0)
        smoke = t
        near = ("pat", math.sin(cyc * 2.0))
        sack_swing = 6.0 * math.sin(cyc)
    elif anim == "walk":
        # A strut: nose up, belly first, the sack swinging.
        stride = math.sin(cyc)
        bob = -1.2 * abs(math.sin(cyc))
        belly_bounce = 1.0 * abs(math.sin(cyc))
        lean = -6.0
        near = ("swing", math.sin(cyc))
        sack_swing = 14.0 * math.sin(cyc)
        smoke = (t * 2.0) % 1.0
    elif anim == "notice":
        # He sees you and hugs his money.
        brows, eyes, mouth, alarm = "up", "wide", "o", True
        bob = -2.5 * math.sin(math.pi * t)
        far = "hug"
        near = "hug"
    elif anim == "windup":
        # A coin out of the sack and back over his shoulder.
        lean, crouch, stride = -12.0, 2.0, 0.5
        near, coin_in_hand = "back", True
        brows, eyes, mouth = "down", "lidded", "grin"
        bob = 0.5 * math.sin(cyc * 2.0)
    elif anim == "attack_side":
        throw = min(1.0, t * 1.6)
        lean = -12.0 + 24.0 * math.sin(math.pi * 0.5 * throw)
        crouch, stride = 2.0 + 2.0 * throw, 0.5 + 0.4 * throw
        near = ("throw", throw)
        coin_in_hand = throw < 0.5
        brows, eyes, mouth = "down", "lidded", "grin"
        hip_x += 4.0 * throw
    elif anim == "hit":
        lean, crouch = -16.0, 3.0
        hip_x -= 4.0 * math.sin(math.pi * t)
        brows, eyes, mouth = "up", "x", "o"
        hat_off = (hip_x + 6.0 + 10.0 * t, 52.0 - 12.0 * t, -40.0 * t)
        notes = 3
        near, far = "flail", "flail"
    elif anim == "death":
        fall = min(1.0, t / 0.85)
        brows, eyes, mouth = "up", "shut", "o"
        near, far = "limp", "limp"
        lean = -6.0 - 8.0 * fall
        crouch = 6.0 * min(1.0, fall * 2.0)
        hip_x += 28.0 * fall
        rot = -82.0 * max(0.0, (fall - 0.3) / 0.7) ** 1.3
        drop = min(1.0, fall * 1.6)
        hat_off = (hip_x + 4.0 + 26.0 * fall, 62.0 + (GROUND - 70.0) * drop * drop, 120.0 * fall)
        notes = 2 + int(5 * t)
        # The sack falls from his hand and lies open by him.
        far = "limp"
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    pen = S.Pen(f, (hip_x - 14.0, GROUND - 4.0), rot, (0.0, 7.0 * rot / 82.0))
    flat = S.Pen(f)
    hip_y = GROUND - (THIGH + SHIN - 1.0) + crouch + bob
    lr = math.radians(lean)

    def up(p, length):
        return (p[0] + math.sin(lr) * length, p[1] - math.cos(lr) * length)

    def across(p, w):
        return (p[0] + math.cos(lr) * w, p[1] + math.sin(lr) * w)

    hip = (hip_x, hip_y)
    belly = up(across(hip, 4.0), 9.0 - belly_bounce)
    shoulder = up(hip, TORSO - 4.0)
    neck = up(hip, TORSO)
    head = up(across(neck, 1.0), HEAD_R + 1.0)
    hx, hy = head

    # The hands.
    if near == "back":
        nh = (shoulder[0] - 11.0, shoulder[1] - 8.0 + 1.0 * math.sin(cyc * 2.0))
    elif near == "hug":
        nh = (belly[0] + 6.0, belly[1] - 6.0)
    elif near == "flail":
        nh = (shoulder[0] + 9.0, shoulder[1] - 13.0)
    elif near == "limp":
        nh = (hip_x + 10.0, hip_y + 2.0)
    elif isinstance(near, tuple) and near[0] == "throw":
        a = math.radians(200.0 + 150.0 * near[1])
        nh = (shoulder[0] + 2.0 + math.cos(a) * 16.0, shoulder[1] + math.sin(a) * 16.0)
    elif isinstance(near, tuple) and near[0] == "pat":
        nh = (belly[0] + 9.5, belly[1] - 1.0 - 1.2 * near[1])
    elif isinstance(near, tuple):
        nh = (hip_x + 9.0 + 4.0 * near[1], hip_y - 1.0)
    else:
        nh = (belly[0] + 9.0, belly[1])
    if far == "hug":
        fh = (belly[0] + 8.0, belly[1] - 2.0)
    elif far == "flail":
        fh = (shoulder[0] - 8.0, shoulder[1] - 12.0)
    elif far == "limp":
        fh = (hip_x - 10.0, hip_y + 2.0)
    else:
        # He keeps the sack behind him, out of your reach.
        fh = (hip_x - 13.0, hip_y - 1.0 + 0.6 * math.sin(cyc))

    # The fur coat behind it all: long, to below the knee.
    back_sh = across(shoulder, -7.0)
    hem_y = hip_y + 15.0 - crouch
    coat = [(back_sh[0] + 2.0, back_sh[1] - 2.0), (neck[0] + 3.0, neck[1]), (hip_x + 4.0, hem_y - 1.0),
            (hip_x - 12.0, hem_y), (back_sh[0] - 4.0, back_sh[1] + 8.0)]
    pen.poly(coat, COAT)
    pen.ink([(back_sh[0] - 1.0, back_sh[1] + 8.0), (hip_x - 8.0, hem_y - 1.0)], 0.8, COAT_SHADE)
    _fur_edge(pen, [(hip_x - 12.0, hem_y), (hip_x + 3.0, hem_y - 1.0)], 2.2, H.FUR_LIGHT, rng)

    def leg(side: float, colour):
        swing = stride * side
        foot = (hip_x + 7.0 * swing + side * 2.5 + 1.0, GROUND - 2.0)
        knee, foot = S.joint((hip_x + side * 1.5, hip_y), foot, THIGH, SHIN, -1.0)
        pen.limb([(hip_x + side * 1.5, hip_y), knee, foot], 5.6, colour)
        pen.poly([(foot[0] - 2.5, foot[1] - 2.0), (foot[0] + 5.0, foot[1] - 1.0), (foot[0] + 5.5, foot[1] + 1.8), (foot[0] - 2.5, foot[1] + 1.8)], K.INK)
        pen.dot(foot[0] + 2.5, foot[1] - 0.6, 0.6, K.alpha(K.WHITE, 0.8))

    def arm(hand, sleeve):
        elbow, hand = S.joint(shoulder, hand, UPPER_ARM, FOREARM, 1.0)
        pen.limb([shoulder, elbow, hand], 5.0, sleeve)
        cuff = (elbow[0] * 0.25 + hand[0] * 0.75, elbow[1] * 0.25 + hand[1] * 0.75)
        pen.ellipse(cuff[0], cuff[1], 3.0, 3.0, H.FUR_LIGHT)
        pen.ellipse(hand[0], hand[1], 2.4, 2.4, FACE)
        return hand

    leg(-1.0, TROUSERS_SHADE)
    fhand = arm(fh, COAT_SHADE)
    if far in ("sack", "flail", "hug") and anim != "death":
        _sack(pen, fhand[0], fhand[1] + 1.0, sack_swing if far == "sack" else (-30.0 if far == "flail" else 0.0))
        pen.ellipse(fhand[0], fhand[1], 2.4, 2.4, FACE)

    # The body: a round belly in a gold waistcoat, the shirt and a bow tie.
    hb, hf = across(hip, -6.0), across(hip, 7.0)
    sb, sf = across(shoulder, -6.5), across(shoulder, 5.0)
    nb, nf = across(neck, -3.5), across(neck, 3.0)
    bf = across(belly, 8.0)
    pen.poly([hb, hf, bf, sf, nf, nb, sb], WAISTCOAT)
    pen.ellipse(belly[0] + 1.5, belly[1] + 1.0, 10.0, 9.5, WAISTCOAT)
    pen.poly([hb, across(hip, -1.0), across(up(hip, 8.0), -1.5), across(shoulder, -2.0), sb], WAISTCOAT_SHADE, body=False)
    shirt = [across(up(hip, 9.0), 4.5), across(up(hip, 9.0), 6.8), nf, across(neck, 0.5)]
    pen.poly(shirt, K.WHITE, body=False)
    for k in range(3):
        b = across(up(hip, 3.0 + k * 3.5), 7.2 + (1.4 if k < 2 else 0.4))
        pen.dot(b[0], b[1], 0.8, WAISTCOAT_SHADE)
    pen.ink([across(up(hip, 4.0), 0.0), across(up(hip, 2.5), 4.5), across(up(hip, 5.0), 8.0)], 0.8, H.GOLD_DARK)
    bt = across(up(neck, -1.0), 2.5)
    pen.poly([(bt[0] - 2.4, bt[1] - 1.6), (bt[0], bt[1]), (bt[0] - 2.4, bt[1] + 1.6)], K.INK, body=False)
    pen.poly([(bt[0] + 2.4, bt[1] - 1.6), (bt[0], bt[1]), (bt[0] + 2.4, bt[1] + 1.6)], K.INK, body=False)
    # The front of the fur coat, open over the belly, and its great collar.
    front = [across(shoulder, 2.0), across(up(hip, 6.0), -1.0), (hip_x - 1.0, hem_y), (hip_x - 6.0, hem_y), across(shoulder, -6.0)]
    pen.poly(front, COAT)
    pen.ink([across(shoulder, 0.0), (hip_x - 3.0, hem_y - 1.0)], 0.7, COAT_SHADE)
    _fur_edge(pen, [across(neck, -6.0), across(up(neck, -3.0), -2.0), across(up(hip, 6.0), -1.0), (hip_x - 1.0, hem_y)], 2.4, H.FUR_LIGHT, rng)
    _fur_edge(pen, [across(up(neck, 1.0), -7.0), across(up(neck, 2.5), -2.0)], 3.0, H.FUR, rng)
    leg(1.0, TROUSERS)

    # The head: nose up, white chops, a red nose and a cigar.
    tilt = -5.0 + lean * 0.3
    pen.ellipse(hx, hy, HEAD_R, HEAD_R * 1.02, FACE)

    def Hp(x, y):
        return K.turn([(hx + x, hy + y)], hx, hy, tilt)[0]

    # The mutton chops: two white masses down the cheeks, and the moustache.
    pen.poly([Hp(-4.0, -1.0), Hp(0.0, 0.0), Hp(2.0, 4.0), Hp(1.0, 8.4), Hp(-3.0, 8.0), Hp(-5.6, 3.0)], WHISKERS)
    pen.ink([Hp(-3.0, 2.0), Hp(-1.0, 6.0)], 0.6, WHISKERS_SHADE)
    pen.poly([Hp(5.2, -1.4), Hp(9.0, 0.8), Hp(5.6, 2.6)], FACE)
    pen.ellipse(*Hp(8.0, 1.0), 2.0, 1.8, NOSE)
    pen.poly([Hp(1.6, 3.0), Hp(4.4, 2.2), Hp(8.0, 2.6), Hp(9.6, 4.6), Hp(6.4, 5.0), Hp(4.0, 5.6), Hp(1.6, 5.4)], WHISKERS)
    pen.ink([Hp(9.0, 4.4), Hp(10.6, 3.4)], 1.0, WHISKERS)
    if mouth == "o":
        pen.ellipse(*Hp(5.6, 7.0), 1.4, 1.6, K.INK, body=False)
    elif mouth == "grin":
        pen.poly([Hp(3.6, 6.4), Hp(7.6, 6.0), Hp(6.8, 7.8), Hp(4.2, 7.8)], K.WHITE, body=False)
        pen.ink([Hp(3.6, 6.4), Hp(7.6, 6.0)], 0.6, H.OUTLINE)
    if mouth in ("cigar", "grin"):
        # The cigar, with its gold band, its ember and its smoke.
        c0, c1 = Hp(5.6, 6.2), Hp(12.6, 4.6)
        pen.limb([c0, c1], 2.4, (120, 76, 44, 255))
        bx, by = Hp(7.4, 5.8)
        pen.dot(bx, by, 1.0, H.GOLD)
        f.glow(c1[0] + 0.6, c1[1] - 0.2, 1.6, K.alpha(H.FIRE, 0.9))
        f.dot(c1[0] + 0.6, c1[1] - 0.2, 0.9, H.FIRE)
        if anim in ("idle", "walk"):
            for k in range(2):
                u = (smoke + k * 0.5) % 1.0
                H.puff(flat, c1[0] + 2.0 + 6.0 * u, c1[1] - 3.0 - 14.0 * u, 1.4 + 2.4 * u, K.alpha(H.STEAM_SHADE, 0.75 * (1.0 - u)),
                       random.Random(f"smoke:{k}:{int(smoke * 10)}"), 4, body=False)
    ex, ey = Hp(3.4, -1.6)
    if eyes == "x":
        pen.ink([(ex - 1.2, ey - 1.2), (ex + 1.2, ey + 1.2)], 0.9)
        pen.ink([(ex - 1.2, ey + 1.2), (ex + 1.2, ey - 1.2)], 0.9)
    elif eyes == "shut":
        pen.ink([(ex - 1.5, ey), (ex, ey + 0.8), (ex + 1.5, ey)], 0.9)
    elif eyes == "wide":
        pen.ellipse(ex, ey, 1.7, 2.0, K.WHITE, body=False)
        pen.dot(ex + 0.4, ey, 0.9)
    else:
        pen.ellipse(ex, ey, 1.4, 1.1, K.WHITE, body=False)
        pen.poly([(ex - 1.6, ey - 1.3), (ex + 1.6, ey - 1.3), (ex + 1.6, ey + 0.1), (ex - 1.6, ey + 0.1)], FACE, body=False)
        pen.ink([(ex - 1.6, ey + 0.1), (ex + 1.6, ey + 0.1)], 0.7)
        pen.dot(ex + 0.3, ey + 0.6, 0.6)
    brow_y = {"smug": -4.4, "up": -5.4, "down": -3.2}[brows]
    tip = -1.0 if brows == "down" else 0.6
    pen.ink([Hp(1.6, brow_y - 0.4), Hp(5.4, brow_y + tip)], 1.3, WHISKERS)

    if hat_off is None:
        hc = Hp(0.0, -10.6)
        _top_hat(pen, hc[0], hc[1], tilt)
    else:
        pen.ellipse(*Hp(-1.0, -5.4), 4.6, 2.2, WHISKERS_SHADE, body=False)
        _top_hat(flat, *hat_off)

    hand = arm(nh, COAT)
    if anim == "death":
        _sack(flat, min(112.0, hip_x + 14.0 + 10.0 * t), GROUND - 18.0, 70.0 * min(1.0, t * 2.0))
    if coin_in_hand:
        H.coin(pen, hand[0] + 0.6, hand[1] - 3.2, 3.0, 0.15)
        f.glow(*pen.at(hand[0] - 0.4, hand[1] - 4.6), 1.6, K.alpha(H.GOLD_LIGHT, 0.9))
        pen.ellipse(hand[0], hand[1], 2.4, 2.4, FACE)

    for k in range(notes):
        px = hip_x - 16.0 + rng.uniform(-6.0, 40.0) + (24.0 * t if anim == "death" else 0.0)
        py = hip_y - 28.0 + rng.uniform(-10.0, 18.0) - 10.0 * t
        px, py = min(116.0, max(12.0, px)), min(GROUND - 8.0, max(12.0, py))
        H.banknote(flat, px, py, rng.uniform(-50.0, 50.0))

    if alarm:
        H.alarm_mark(f, hx + 13.0, hy - 24.0)
    return H.finish(f, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
