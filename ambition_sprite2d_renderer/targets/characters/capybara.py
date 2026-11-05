"""The Capybara of the History dimension: the great rodent of the Amazon's banks.

The capybara (Hydrochoerus hydrochaeris) is the largest rodent in the
world. It lives in groups along the rivers, the lakes and the flooded
grasslands of South America, from the Amazon to the south of Brazil. It
eats grass and water plants, and it swims well. Its body is heavy and
shaped like a barrel. Its coarse fur is red-brown. Its head is large and
blunt, with a deep, square muzzle. Its small round ears and its small
eyes sit high on the head, so that it can hear and see with only the top
of its head above the water. It has no tail that you can see. Its legs
are short, and its feet are partly webbed.

At rest it stands calm and still, and chews. It walks steadily on its
short legs. When it sees you it lifts its head and its ears. Its windup
is a crouch: it lowers its head and rocks back. Its strike is a short
charge: it runs forward with its head down and butts you with its head.
A hit makes it shut its eyes and step back; at its death it lies down,
folds its legs, lays its head on the ground, goes still and fades.

The frame is 160 by 96 px: the body box is 56 by 36 world units, and the
capybara faces right.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _history_africa_kit as H

TARGET_NAME = "capybara"
FRAME_SIZE = (160, 96)
ROWS = K.ENEMY_ROWS
#: Nothing is drawn nearer the edge of the frame than this.
MARGIN = 6.0
GROUND = 88.0
#: The capybara is drawn at its size in the frame.
SIZE = 1.0
PIVOT = (80.0, GROUND)

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Capybara", "Quadruped", "Standard", "Medium", "Walk", ["rodent", "capybara", "charge", "headbutt"],
    "The capybara, the largest rodent in the world, of the History dimension's Amazonia and Brazil rooms: a heavy "
    "body shaped like a barrel, coarse red-brown fur, a large blunt head with a deep square muzzle, small round ears "
    "and small eyes high on the head, no tail you can see and short legs with webbed feet. It is calm, but it lowers "
    "its head, charges a short way and butts you with its head.",
)
ACTOR_METADATA["tags"] = ["enemy", "history", "amazonia", "brazil"]

Point = Tuple[float, float]

FUR = (150, 102, 64, 255)
FUR_SHADE = (112, 74, 46, 255)
FUR_LIGHT = (180, 136, 92, 255)
#: The paler, yellow-brown fur under the belly.
BELLY = (170, 132, 88, 255)
#: The bare dark skin of the nose, the ears and the feet.
SKIN_DARK = (74, 50, 38, 255)
#: The dark bump on the top of the snout (the morrillo, a scent gland).
MORRILLO = (92, 62, 44, 255)
EYE = (44, 28, 20, 255)
GLINT = (236, 220, 190, 255)
DUST = (196, 172, 128, 255)
#: The middle of the body at rest, and its half length and half height.
BODY = (60.0, 55.0)
RX, RY = 36.0, 20.0


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = H.ScaledFrame(FRAME_SIZE, SIZE, PIVOT)

    # The pose. `dx` moves the whole animal; `down` lowers the body; `tilt`
    # turns the body (degrees, + is nose down); `hang` turns the head
    # (degrees, + is nose down); `reach` puts the head forward; `ears` 1 is
    # pricked up; `fold` 1 is lying down with the legs folded.
    dx, down, tilt, hang, reach, ears, fold, chew = 0.0, 0.0, 0.0, 8.0, 0.0, 0.0, 0.0, 0.0
    eyes, fade, alarm, walk_ph, stretch, butt = "open", 1.0, False, None, 0.0, -1
    if anim == "idle":
        # It stands calm, breathes, and chews.
        down = 0.6 * math.sin(cyc)
        hang = 8.0 + 1.5 * math.sin(cyc + 0.6)
        chew = max(0.0, math.sin(cyc * 2.0))
        eyes = "shut" if i == 4 else "open"
    elif anim == "walk":
        # A steady walk, the legs in diagonal pairs.
        walk_ph = t
        down = -0.8 * abs(math.sin(cyc * 2.0))
        tilt = 1.0 * math.sin(cyc * 2.0)
        hang = 10.0 + 2.0 * math.sin(cyc * 2.0 + 0.5)
    elif anim == "notice":
        # It lifts its head and pricks its ears.
        k = math.sin(math.pi * min(1.0, t * 1.3))
        hang, ears, eyes, alarm, tilt = 8.0 - 16.0 * k, k, "wide", True, -2.0 * k
    elif anim == "windup":
        # It lowers its head and rocks back, ready to run.
        dx = -4.0 + 1.5 * math.sin(cyc)
        down = 2.0 + 0.6 * math.sin(cyc * 2.0)
        tilt = 4.0 + 1.0 * math.sin(cyc)
        hang, reach, eyes = 26.0, -2.0, "narrow"
    elif anim == "attack_side":
        # The charge and the headbutt, as key frames: dx, down, tilt, hang,
        # reach, stretch. The head goes down for the run and comes up into
        # the butt. `stretch` -1 gathers the legs under the body; 1 reaches
        # them out, the front ones forward and the hind ones back.
        table = [
            (-4.0, 2.0, 4.0, 26.0, -2.0, 0.0),
            (2.0, -1.0, 2.0, 24.0, 2.0, -0.7),
            (8.0, -2.5, 3.0, 22.0, 4.0, 1.0),
            (12.0, 0.0, -3.0, 0.0, 6.0, 0.2),
            (9.0, 0.5, 0.0, 6.0, 2.0, 0.0),
            (3.0, 0.0, 0.0, 8.0, 0.0, 0.0),
        ]
        dx, down, tilt, hang, reach, stretch = table[i]
        eyes, butt = "narrow", i
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        dx, hang, tilt, eyes, down = -6.0 * k, -10.0 * k, -4.0 * k, "shut", 1.0 * k
    elif anim == "death":
        # It lies down: the legs fold, the body comes down to the ground, the
        # head rests on the ground. Then it goes still and fades.
        u = min(1.0, t / 0.6)
        fold = u * u * (3.0 - 2.0 * u)
        hang, eyes = 8.0 + 10.0 * fold, ("shut" if t > 0.3 else "open")
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    # The body comes down to the ground as the legs fold.
    down += fold * (GROUND - 3.0 - (BODY[1] + RY))
    cx, cy = BODY[0] + dx, BODY[1] + down

    def B(*p: Point) -> List[Point]:
        """Points about the middle of the body, turned with it."""
        return K.turn([(cx + x, cy + y) for x, y in p], cx, cy, tilt)

    def leg(fore: bool, near: bool) -> None:
        """A short leg with a webbed foot. The near legs have their own
        outline, so that they show on the body."""
        colour = FUR if near else FUR_SHADE
        root = B(((26.0 if fore else -22.0) + (0.0 if near else -4.0), 10.0))[0]
        fx = root[0] + (2.0 if fore else -1.0)
        lift_ = 0.0
        if walk_ph is not None:
            pair = 0.0 if fore == near else 0.5
            sx, sy = H.gait(walk_ph * 2.0 + pair, 12.0, 4.0)
            fx, lift_ = fx + sx, -sy
        if stretch:
            # In the charge the legs reach out and gather in turn.
            fx += stretch * (9.0 if fore else -9.0) + (0.0 if near else -2.0)
            lift_ = 3.0 * abs(stretch) if near == fore else 1.0 * abs(stretch)
        foot = (fx, GROUND - 2.0 - lift_)
        if fold:
            # Lying down, the feet tuck under the body, a little forward.
            tuck = (root[0] + (8.0 if fore else 6.0), GROUND - 2.5)
            foot = (foot[0] + (tuck[0] - foot[0]) * fold, foot[1] + (tuck[1] - foot[1]) * fold)
        mid = ((root[0] + foot[0]) / 2.0 + (-1.5 if fore else 3.0), (root[1] + foot[1]) / 2.0)
        if fold:
            mid = (mid[0] - 6.0 * fold, mid[1])
        thick, thin = (8.0, 5.6) if fore else (11.0, 6.4)
        if near:
            f.limb([root, mid], thick + 2.4, H.SEPIA_INK, body=False)
            f.limb([mid, foot], thin + 2.4, H.SEPIA_INK, body=False)
        f.limb([root, mid], thick, colour)
        f.limb([mid, foot], thin, colour)
        # The foot: dark toes joined by a web.
        f.ellipse(foot[0] + 2.0, foot[1] + 0.6, 4.4, 1.9, SKIN_DARK)
        for k in range(3):
            f.dot(foot[0] + 0.6 + 2.2 * k, foot[1] + 1.4, 0.6, FUR_SHADE if near else FUR)

    leg(True, False)
    leg(False, False)

    # The body: a barrel, with the rump a little higher than the shoulders.
    f.poly(B(*K.ellipse_points(0.0, 0.0, RX, RY, 36)), FUR)
    f.ellipse(*B((-14.0, -3.0))[0], 23.0, 21.0, FUR)
    # The chest and the thick neck, up to the head.
    f.ellipse(*B((26.0, -4.0))[0], 14.0, 16.0, FUR)
    # The paler belly, the shade along the flank and the light on the back.
    f.poly(B((-26.0, 10.0), (0.0, 14.0), (24.0, 11.0), (28.0, 14.0), (10.0, 19.4), (-14.0, 19.6), (-28.0, 14.0)), BELLY, body=False)
    f.poly(B((-30.0, 6.0), (-6.0, 9.6), (24.0, 7.0), (24.0, 10.4), (-6.0, 13.0), (-30.0, 10.0)), FUR_SHADE, body=False)
    f.poly(B((-30.0, -19.0), (-14.0, -23.6), (6.0, -20.4), (24.0, -16.0), (8.0, -16.0), (-14.0, -18.6), (-28.0, -14.0)), FUR_LIGHT, body=False)
    # The coarse fur: short strokes that lie back along the body.
    rng = random.Random("capybara-fur")
    for _ in range(26):
        u, v = rng.uniform(-0.85, 0.85), rng.uniform(-0.7, 0.5)
        if u * u + v * v > 0.7:
            continue
        x, y = RX * u, RY * v
        f.ink(B((x, y), (x - 3.2, y + 1.6)), 0.7, FUR_SHADE)
    # Tufts of coarse hair along the back and under the belly.
    for x, y, a in ((-30.0, -16.0, -150.0), (-20.0, -22.0, -165.0), (-8.0, -23.0, -175.0), (4.0, -20.0, 175.0), (14.0, -19.0, 170.0),
                    (-24.0, 17.0, 150.0), (-8.0, 20.0, 160.0), (8.0, 19.0, 165.0)):
        r = math.radians(a)
        f.poly(B((x - 2.0, y), (x + 4.0 * math.cos(r), y + 4.0 * math.sin(r)), (x + 2.0, y)), FUR)

    leg(False, True)

    # The head, turned by `hang` about the top of the neck.
    nx, ny = B((32.0 + reach, -10.0))[0]
    hang += tilt
    if fold:
        # Lying down, the chin comes to rest on the ground.
        ny += fold * (GROUND - 13.0 - ny) * 0.6

    def Hd(*p: Point) -> List[Point]:
        return K.turn([(nx + x, ny + y) for x, y in p], nx, ny, hang)

    # The small round ear, high at the back of the head. It stands up when
    # the capybara listens.
    ex, ey = Hd((-3.0 - 1.0 * ears, -14.0 - 1.6 * ears))[0]
    f.ellipse(ex, ey, 3.6, 3.2 + 0.6 * ears, SKIN_DARK)
    f.ellipse(ex + 0.4, ey + 0.4, 2.0, 1.8, FUR_SHADE, body=False)
    # The large blunt head with its deep, square muzzle.
    head = Hd((-8.0, -8.0), (-4.0, -12.6), (6.0, -14.6), (18.0, -14.4), (28.0, -12.0), (33.0, -8.4), (35.0, -3.0), (35.0, 4.0),
              (32.4, 9.0), (24.0, 11.4), (10.0, 11.4), (0.0, 10.0), (-6.0, 6.0))
    f.poly(head, FUR)
    f.poly(Hd((-2.0, -11.6), (6.0, -13.6), (18.0, -13.4), (26.0, -11.0), (18.0, -11.0), (6.0, -10.8)), FUR_LIGHT, body=False)
    # The shade under the jaw, and the line of the big cheek muscle.
    f.poly(Hd((0.0, 7.0), (12.0, 8.6), (24.0, 8.6), (32.0, 7.0), (32.4, 9.0), (24.0, 11.4), (10.0, 11.4), (0.0, 10.0)), FUR_SHADE, body=False)
    f.ink(Hd((2.0, -4.0), (6.0, 2.0), (12.0, 6.0)), 0.8, FUR_SHADE)
    # The morrillo, the dark bump on the top of the snout.
    f.poly(Hd((15.0, -13.4), (20.0, -14.2), (25.0, -12.8), (24.0, -11.4), (16.0, -11.8)), MORRILLO, body=False)
    # The bare dark nose, with its slit nostril.
    f.poly(Hd((31.0, -8.0), (33.6, -8.2), (35.0, -3.0), (35.0, 1.0), (32.0, 0.0), (30.6, -4.0)), SKIN_DARK, body=False)
    f.ink(Hd((32.4, -5.4), (34.0, -2.6)), 0.8, EYE)
    # The mouth: a short line under the nose. When it chews the lower lip
    # moves.
    f.ink(Hd((34.0, 2.0), (33.0, 5.6 + 0.8 * chew), (26.0, 6.4 + 0.6 * chew)), 0.8, EYE)
    # The small eye, high on the head.
    ox, oy = Hd((7.0, -8.0))[0]
    if eyes == "shut":
        f.ink(Hd((4.6, -7.6), (7.0, -7.0), (9.4, -7.6)), 0.9, EYE)
    else:
        r = {"open": 1.5, "wide": 2.0, "narrow": 1.0}[eyes]
        f.ellipse(ox, oy, 1.8, r, EYE, body=False)
        f.dot(ox + 0.6, oy - 0.5, 0.45, GLINT)
        if eyes == "narrow":
            f.ink(Hd((4.0, -10.4), (10.0, -9.6)), 0.9, FUR_SHADE)

    leg(True, True)

    if walk_ph is not None and walk_ph % 0.5 < 0.12:
        H.dust(f, cx - 18.0, GROUND - 1.0, 0.3, f"cap:walk:{i}", spread=0.6, colour=DUST)
    if anim == "attack_side":
        if butt in (1, 2):
            H.dust(f, cx - 24.0, GROUND - 1.0, 0.6, f"cap:run:{i}", spread=0.8, colour=DUST)
        if butt == 3:
            # The headbutt: short lines out from the brow.
            bx, by = Hd((34.0, -8.0))[0]
            for k in (-1.0, 0.0, 1.0):
                f.ink([(bx + 3.0, by + 5.0 * k), (min(FRAME_SIZE[0] - MARGIN - 1.0, bx + 9.0), by + 8.0 * k)], 1.3, K.alpha(K.WHITE, 0.95))
    if anim == "death" and 0.1 < t < 0.8:
        H.dust(f, cx, GROUND - 1.0, min(1.0, (t - 0.1) * 2.0), f"cap:death:{i}", spread=1.6, colour=DUST)
    if alarm:
        hx, hy = Hd((4.0, -16.0))[0]
        H.alarm_mark(f, hx, max(MARGIN + 11.0, hy - 16.0))
    return f.finish(outline=H.SEPIA_INK, width=1.5, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
