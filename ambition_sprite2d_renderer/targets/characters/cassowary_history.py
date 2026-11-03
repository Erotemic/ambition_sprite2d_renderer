"""The Cassowary of the History dimension: the great bird of the New Guinea highlands.

A tall bird with no wings to speak of, under a coat of black plumage like
coarse hair. Its neck is bright blue, red down its nape, with two red
wattles at its throat; a tall casque of horn rises from its crown. Its
legs are thick and grey, and the inner toe of each foot carries a long
dagger of a claw. (The game has another cassowary, the constraint solver
of the primeval rooms; this one is the History cast's, so its id has the
suffix ``_history``.)

It is fast. It bobs its head and steps high. When it sees you it stands up
tall and booms. Its windup draws one leg up high in front of its body; its
strike is the kick: the leg shoots forward, claw first. A hit ruffles its
plumage; at its death it sinks onto its belly and its neck droops.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _history_americas_kit as A
from . import _stage_kit as S

TARGET_NAME = "cassowary_history"
FRAME_SIZE = (128, 160)
ROWS = K.ENEMY_ROWS
GROUND = 155.0

ACTOR_METADATA = A.enemy_metadata(
    TARGET_NAME, "Cassowary", "highlands", "Biped", "Standard", "Medium", "Walk", ["bird", "casque", "kick"],
    "The cassowary of the History dimension's New Guinea highlands: black plumage, a blue neck with red wattles and "
    "a tall casque. It draws one leg up high, then kicks forward with its dagger claw.",
)

PLUME = (36, 32, 38, 255)
PLUME_SHADE = (22, 20, 26, 255)
PLUME_LIGHT = (84, 80, 96, 255)
NECK = (48, 132, 214, 255)
NECK_LIGHT = (110, 190, 240, 255)
NECK_RED = (214, 52, 52, 255)
WATTLE = (226, 48, 56, 255)
CASQUE = (176, 134, 82, 255)
CASQUE_SHADE = (130, 92, 52, 255)
BEAK = (54, 50, 56, 255)
LEG = (150, 146, 128, 255)
LEG_SHADE = (110, 106, 92, 255)
CLAW = (236, 228, 206, 255)
EYE = (190, 96, 40, 255)

Point = Tuple[float, float]
#: The size of the body and of the head against the legs.
BODY, HEAD = 1.3, 1.3


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)

    dx, dy, lean, neck_lean, head_pitch, walk, kick, chamber, sink, ruffle = 0.0, 0.0, 0.0, 0.0, 0.0, None, 0.0, 0.0, 0.0, 0.0
    eyes, beak, fade, alarm = "open", 0.0, 1.0, False
    if anim == "idle":
        neck_lean = 4.0 * math.sin(cyc)
        head_pitch = 6.0 * math.sin(cyc + 0.8)
        dy = 0.6 * math.sin(cyc * 2.0)
    elif anim == "walk":
        walk = t
        dy = -2.0 * abs(math.sin(cyc))
        neck_lean = 6.0 + 4.0 * math.sin(cyc * 2.0)
        lean = 4.0
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.3))
        neck_lean, head_pitch, beak, eyes, alarm = -8.0 * k, -10.0 * k, 0.6 * k, "wide", True
        dy = -3.0 * k
        ruffle = 0.5 * k
    elif anim == "windup":
        # One leg drawn up high in front of the body; the body leans back.
        chamber = 0.9 + 0.1 * math.sin(cyc * 2.0)
        lean, neck_lean, eyes = -8.0, -6.0, "narrow"
        dy = -2.0
        ruffle = 0.6
    elif anim == "attack_side":
        # The kick: the leg shoots forward, claw first, then comes back.
        u = t
        kick = math.sin(math.pi * min(1.0, u * 1.6)) if u < 0.62 else max(0.0, 1.0 - (u - 0.62) / 0.38) * 0.3
        chamber = max(0.0, 1.0 - u * 3.0)
        lean, neck_lean, eyes = -12.0 * kick - 8.0 * chamber, -6.0, "narrow"
        dx = 6.0 * kick
        dy = -3.0 * kick
        beak = 0.5 * kick
        ruffle = 0.8
    elif anim == "hit":
        k = math.sin(math.pi * t)
        dx, lean, neck_lean, head_pitch, eyes, ruffle = -4.0 * k, -6.0 * k, -14.0 * k, -16.0 * k, "shut", k
    elif anim == "death":
        u = min(1.0, t / 0.8)
        sink = u
        neck_lean, head_pitch, eyes = 42.0 * u, 34.0 * u, "shut"
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    body_c = (50.0 + dx, 92.0 + dy + 13.0 * sink)
    hip = (body_c[0] + 4.0, body_c[1] + 18.0)

    def leg(near: bool, ph: float) -> None:
        colour = LEG if near else LEG_SHADE
        fx, fy = hip[0] + (4.0 if near else -2.0), GROUND - 7.0
        if walk is not None:
            gx, gy = A.gait(ph, 26.0, 12.0)
            fx += gx
            fy += gy
        bend = 1.0
        if near and chamber > kick:
            # The leg drawn up: the foot comes up under the chest.
            fx, fy = hip[0] + 12.0 * chamber, hip[1] + 26.0 - 10.0 * chamber
        if near and kick > chamber:
            fx = hip[0] + 14.0 + 28.0 * kick
            fy = hip[1] + 26.0 - 16.0 * kick
        if sink:
            fx = hip[0] + (10.0 if near else 4.0) * sink
            fy = GROUND - 7.0
        knee, foot = S.joint(hip, (fx, fy), 20.0, 24.0, bend)
        knee = (knee[0], min(knee[1], GROUND - 8.0))
        f.limb([hip, knee], 11.0, colour)
        f.limb([knee, foot], 6.5, colour)
        # The scales down the front of the leg.
        for k in range(4):
            x, y = A.lerp(knee, foot, 0.2 + 0.2 * k)
            f.ink([(x + 1.0, y), (x + 3.0, y + 0.6)], 0.6, LEG_SHADE)
        # The toes, and the dagger claw of the inner toe.
        ang = math.atan2(foot[1] - knee[1], foot[0] - knee[0]) - math.pi / 2.0 if (kick > 0.2 and near) else 0.0
        toes = [(foot[0] + 11.0, foot[1] + 2.0), (foot[0] + 8.0, foot[1] + 3.6), (foot[0] - 5.0, foot[1] + 2.4)]
        toes = K.turn(toes, foot[0], foot[1], math.degrees(ang) * 0.6)
        for tx, ty in toes:
            f.limb([foot, (tx, ty)], 3.4, colour)
        cx, cy = toes[1]
        claw = K.turn([(cx - 1.0, cy - 1.4), (cx + 7.0, cy + 0.4), (cx - 1.0, cy + 1.6)], cx, cy, math.degrees(ang) * 0.6)
        f.poly(claw, CLAW)

    ph = walk or 0.0
    leg(False, ph + 0.5)

    # The body: black plumage like coarse hair, the rump hangs low.
    bx, by = body_c

    def Bd(pts):
        return K.turn([(bx + x * BODY, by + y * BODY) for x, y in pts], bx, by, lean)

    body = Bd([(-30.0, 10.0), (-30.0, -4.0), (-20.0, -18.0), (0.0, -24.0), (18.0, -20.0), (28.0, -8.0), (28.0, 8.0), (20.0, 18.0)])
    # The hanging fringe of plumes under the body.
    fringe = []
    for k in range(9):
        u = k / 8.0
        x = 20.0 - 52.0 * u
        y = 18.0 + 8.0 * math.sin(math.pi * u) + (6.0 if k % 2 else 0.0) + 3.0 * ruffle * (1 if k % 2 else -1)
        fringe.append((x, y))
    f.poly(body + Bd(fringe), PLUME)
    for k in range(9):
        x0 = -26.0 + k * 6.0
        f.ink(Bd([(x0, -10.0 + abs(k - 4) * 2.0), (x0 - 3.0 - 2.0 * ruffle, 6.0 + abs(k - 4) * 1.4)]), 0.9, PLUME_LIGHT)
    f.poly(Bd([(-30.0, 4.0), (-22.0, 16.0), (0.0, 24.0), (20.0, 18.0), (0.0, 18.0), (-20.0, 10.0)]), PLUME_SHADE, body=False)

    leg(True, ph)

    # The neck: up from the front of the body, blue, red down the nape.
    base = Bd([(18.0, -14.0)])[0]
    top = K.turn([(base[0] + 8.0, base[1] - 34.0)], base[0], base[1], neck_lean + lean * 0.5)[0]
    mid = K.turn([(base[0] + 2.0, base[1] - 19.0)], base[0], base[1], neck_lean * 0.7 + lean * 0.5)[0]
    f.limb([base, mid, top], 10.0, NECK)
    f.limb([A.lerp(base, mid, 0.3), mid, A.lerp(mid, top, 0.7)], 3.0, NECK_RED, body=False)
    f.ink([A.lerp(base, mid, 0.5), A.lerp(mid, top, 0.5)], 1.0, NECK_LIGHT)
    # The feathers of the body run up over the base of the neck.
    f.ellipse(base[0] - 1.0, base[1] + 3.0, 8.0, 6.0, PLUME)
    # The wattles hang from the front of the throat.
    wx, wy = A.lerp(mid, top, 0.25)
    for k in range(2):
        f.limb([(wx + 3.0 + k * 1.6, wy), (wx + 5.0 + k * 2.0, wy + 7.0 - k * 1.2)], 3.2 - 0.6 * k, WATTLE)

    # The head, with its casque and its beak.
    pr = head_pitch + neck_lean * 0.3

    def Hd(*pts: Point) -> List[Point]:
        return K.turn([(top[0] + x * HEAD, top[1] + y * HEAD) for x, y in pts], top[0], top[1], pr)

    f.poly(Hd((-6.0, -3.0), (0.0, -6.0), (6.0, -4.0), (8.0, 2.0), (2.0, 5.0), (-5.0, 4.0)), NECK)
    # The casque: a tall blade of horn on the crown.
    f.poly(Hd((-5.0, -4.0), (-6.0, -12.0), (-2.0, -19.0), (4.0, -18.0), (8.0, -10.0), (7.0, -4.0)), CASQUE)
    f.poly(Hd((-4.0, -6.0), (-4.6, -12.0), (-1.6, -17.0), (0.0, -10.0)), CASQUE_SHADE, body=False)
    # The beak: long and dark, it opens to boom.
    hinge = Hd((5.0, 1.0))[0]
    f.poly(K.turn(Hd((5.0, 1.0), (17.0, 2.4), (6.0, 4.0)), hinge[0], hinge[1], 24.0 * beak), BEAK)
    f.poly(Hd((5.0, -3.0), (12.0, -1.6), (18.0, 1.8), (6.0, 1.6)), BEAK)
    ex, ey = Hd((1.0, -1.0))[0]
    if eyes == "shut":
        f.ink([(ex - 2.0, ey), (ex + 2.0, ey + 0.3)], 1.0, A.SEPIA_INK)
    else:
        r = {"open": 1.6, "wide": 2.1, "narrow": 1.0}[eyes]
        f.ellipse(ex, ey, 2.0, r, EYE, body=False)
        f.dot(ex + 0.4, ey, 0.8, A.SEPIA_INK)
        if eyes == "narrow":
            f.ink([(ex - 2.6, ey - 2.2), (ex + 2.4, ey - 1.0)], 1.0, A.SEPIA_INK)

    if beak > 0.3 and anim == "notice":
        # The boom: rings out of the open beak.
        bxx, byy = Hd((18.0, 2.0))[0]
        for k in range(2):
            f.glow_line([(min(122.0, bxx + 4.0 + k * 4.0), byy - 4.0 - k * 2.0), (min(124.0, bxx + 6.0 + k * 4.0), byy + 4.0 + k * 2.0)], 1.0,
                        K.alpha(K.WHITE, 0.7 * beak))
    if anim == "attack_side" and 0.15 < t < 0.65:
        # The swish of the claw.
        for k in range(3):
            y = hip[1] + 6.0 + k * 6.0
            f.glow_line([(hip[0] + 30.0, y), (min(122.0, hip[0] + 56.0), y - 3.0)], 1.2, K.alpha(K.WHITE, 0.6))
    if anim == "death" and t > 0.3:
        A.dust(f, 56.0, GROUND - 4.0, 24.0, min(1.0, (t - 0.3) * 2.0), f"cassowary_history:death:{i}")
    if alarm:
        A.alarm_mark(f, min(118.0, top[0] + 16.0), max(18.0, top[1] - 22.0))
    return A.finish(f, fade=fade, width=1.5)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
