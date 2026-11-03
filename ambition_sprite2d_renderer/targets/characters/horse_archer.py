"""The Horse Archer: a Mongol rider of the Steppe, on a small sturdy horse.

The horse is a steppe horse: short legs, a deep barrel, a big head, a dun
coat and a dark mane that stands up. On it is a red saddle cloth and a
saddle with a high front. The rider wears a green deel with a gold edge, a
fur hat with a red crown, boots in short stirrups, and a quiver of arrows at
the hip. In the near hand is a short recurve bow.

It keeps its distance and shoots arrows. Its walk is a gallop, and the rider
stands in the stirrups and stays level while the horse moves under him. Its
windup draws the bow to the ear and holds it, the horse stamping; its strike
lets the arrow go, and the arrow flies out of the frame. A hit knocks the
rider back; at its death the horse kneels and lies down, and the rider falls
off backwards.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _history_steppe_kit as H
from . import _stage_kit as S

TARGET_NAME = "horse_archer"
FRAME_SIZE = (192, 160)
ROWS = K.ENEMY_ROWS
GROUND = 154.0
#: The rider is drawn this much larger than the horse, to read at game size.
RIDER_SCALE = 1.22

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Horse Archer", "Quadruped", "Large", "Heavy", "Walk", ["history", "steppe", "rider", "horse", "archer"],
    "A Mongol horse archer of the Steppe in the History dimension: a rider in a green deel and a fur hat on a small, "
    "sturdy dun horse. It keeps its distance, draws its short recurve bow to the ear and shoots an arrow.",
)

COAT = (204, 158, 98, 255)
COAT_SHADE = (156, 112, 66, 255)
COAT_LIGHT = (230, 196, 140, 255)
MANE = (62, 42, 32, 255)
HOOF = (54, 40, 36, 255)
DEEL = H.STEPPE_GREEN
DEEL_SHADE = H.STEPPE_GREEN_DARK
TRIM = H.STEPPE_GOLD
BOOT = (92, 44, 34, 255)
BOW = (128, 78, 40, 255)
BOW_DARK = (78, 46, 26, 255)
STRING = (238, 228, 200, 255)
SHAFT = (196, 160, 104, 255)
IRON = (96, 96, 110, 255)

Point = Tuple[float, float]


def _gait(ph: float, stride: float, lift: float) -> Point:
    """The place of a hoof in a gallop at phase `ph`: on the ground it moves
    back under the body; in the air it comes forward and up."""
    ph %= 1.0
    if ph < 0.55:
        u = ph / 0.55
        return (stride * (0.5 - u), 0.0)
    u = (ph - 0.55) / 0.45
    return (stride * (-0.5 + (1.0 - math.cos(math.pi * u)) / 2.0), -lift * math.sin(math.pi * u))


def _arrow(pen: S.Pen, tail: Point, angle: float, length: float = 30.0) -> None:
    """An arrow from its nock at `tail`, at `angle` degrees (0 is to the right)."""
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a)
    tip = (tail[0] + ux * length, tail[1] + uy * length)
    pen.limb([tail, tip], 1.6, SHAFT)
    # The head of iron, and the red and white feathers at the nock.
    nx, ny = -uy, ux
    pen.poly([(tip[0] + ux * 5.0, tip[1] + uy * 5.0), (tip[0] + nx * 2.4, tip[1] + ny * 2.4), (tip[0] - nx * 2.4, tip[1] - ny * 2.4)], IRON)
    for side, colour in ((1.0, H.SADDLE_RED), (-1.0, K.WHITE)):
        b = (tail[0] + ux * 2.0, tail[1] + uy * 2.0)
        e = (tail[0] + ux * 8.0, tail[1] + uy * 8.0)
        pen.poly([b, e, (e[0] - ux * 2.0 + nx * 3.0 * side, e[1] - uy * 2.0 + ny * 3.0 * side), (b[0] + nx * 3.4 * side, b[1] + ny * 3.4 * side)], colour)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)

    dx, dy, pitch, head_turn, tail_swish = 0.0, 0.0, 0.0, 0.0, 0.3 * math.sin(cyc)
    gallop, stamp, sink, rider_lean, rider_dy = None, 0.0, 0.0, 0.0, 0.0
    draw, aim, arrow_out, recoil, alarm, eyes = 0.0, -4.0, None, 0.0, False, "open"
    hat_off, fall, fade, mouth = None, 0.0, 1.0, "shut"
    if anim == "idle":
        dy = 0.6 * math.sin(cyc)
        head_turn = 4.0 * math.sin(cyc) - 2.0
        rider_dy = 0.5 * math.sin(cyc + 0.6)
        draw = -1.0
    elif anim == "walk":
        gallop = t
        dy = -3.0 * abs(math.sin(cyc))
        pitch = 3.0 * math.sin(cyc)
        head_turn = -6.0 * math.sin(cyc + 0.8)
        tail_swish = 1.0 + 0.4 * math.sin(cyc)
        rider_dy = 2.0 * abs(math.sin(cyc))
        rider_lean = 6.0
        draw = -1.0
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.3))
        pitch, head_turn, alarm, eyes = -6.0 * k, -14.0 * k, True, "wide"
        dx = -3.0 * k
        draw = -1.0 + 0.6 * k
        mouth = "open"
    elif anim == "windup":
        # The bow is at full draw, and held; the horse stamps a fore hoof.
        draw, aim = 1.0, -6.0 + 0.8 * math.sin(cyc * 2.0)
        stamp = max(0.0, math.sin(cyc))
        head_turn = -4.0
        rider_lean = -3.0
        eyes = "narrow"
    elif anim == "attack_side":
        # Full draw (0), the release (1), the arrow flies, and the follow-through.
        if i == 0:
            draw, aim = 1.0, -6.0
        else:
            draw, aim = 0.0, -6.0
            u = (i - 1) / float(n - 2)
            arrow_out = 140.0 + 42.0 * u
            recoil = max(0.0, 1.0 - u * 1.6)
        rider_lean = -3.0 + 4.0 * recoil
        eyes = "narrow"
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        dx, pitch, head_turn, rider_lean = -5.0 * k, -8.0 * k, -16.0 * k, -16.0 * k
        eyes, mouth, draw = "shut", "open", -1.0
        hat_off = (104.0 + 6.0 * i, 30.0 - 3.0 * i, 40.0 * i) if i >= 1 else None
    elif anim == "death":
        fall = t
        sink = 26.0 * min(1.0, t * 1.4)
        pitch = 10.0 * min(1.0, t * 2.0) - 14.0 * max(0.0, t - 0.5)
        head_turn = 20.0 * min(1.0, t * 1.5)
        eyes, mouth, draw = "shut", "open", -1.0
        hat_off = (88.0 - 40.0 * t, 34.0 - 12.0 * math.sin(math.pi * min(1.0, t * 1.2)) + 90.0 * t * t, -200.0 * t)
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    pivot = (90.0 + dx, GROUND - 40.0)
    horse = H.ScaledPen(f, pivot, pitch, (dx, dy + sink * 0.55 + 6.0))
    flat = H.ScaledPen(f)

    # -- the horse -----------------------------------------------------------
    hips = {"far": (62.0, 104.0), "near": (68.0, 106.0)}
    shoulders = {"far": (112.0, 106.0), "near": (118.0, 108.0)}

    def leg(top: Point, phase_offset: float, hind: bool, colour) -> None:
        top_w = horse.at(*top)
        reach_down = GROUND - top_w[1]
        if gallop is not None:
            fx, fy = _gait(gallop + phase_offset, 26.0, 13.0)
        else:
            fx, fy = 0.0, 0.0
            if not hind and phase_offset > 0.3 and stamp:
                fx, fy = 4.0 * stamp, -10.0 * stamp
        # A leg that kneels at the death: the knee comes down to the ground.
        if sink:
            fold = min(1.0, sink / 26.0)
            fx += (-14.0 if hind else 10.0) * fold
            fy = min(fy, 0.0)
        foot = (top_w[0] + fx + (-2.0 if hind else 2.0), GROUND - 3.0 + fy)
        l1, l2 = reach_down * 0.5, reach_down * 0.54
        knee, foot = S.joint(top_w, foot, l1, l2, 1.0 if hind else -1.0)
        flat.limb([top_w, knee], 11.0 if hind else 9.5, colour)
        flat.limb([knee, foot], 6.4, colour)
        # The hoof, and a dark fetlock above it.
        flat.ellipse(foot[0] + 0.6, foot[1] - 1.6, 3.4, 2.4, K.shade(colour, 0.85), body=False)
        flat.poly([(foot[0] - 3.2, foot[1] - 1.0), (foot[0] + 4.4, foot[1] - 1.0), (foot[0] + 4.8, foot[1] + 2.6), (foot[0] - 3.4, foot[1] + 2.6)], HOOF)

    # The tail: strands of dark hair from the croup, swishing.
    root = (50.0, 92.0)
    for k, off in enumerate((-3.0, 0.0, 3.0)):
        sw = tail_swish + 0.2 * k
        strand = [root, (root[0] - 8.0 - 3.0 * sw, root[1] + 10.0 + off), (root[0] - 12.0 - 6.0 * sw, root[1] + 24.0 + off),
                  (root[0] - 12.0 - 9.0 * sw, root[1] + 38.0 + off * 0.5)]
        horse.limb(strand, 7.0 - k * 1.2, MANE)
    leg(hips["far"], 0.12, True, COAT_SHADE)
    leg(shoulders["far"], 0.52, False, COAT_SHADE)

    # The body: the rump, the barrel and the chest, in one coat.
    horse.ellipse(64.0, 94.0, 19.0, 17.0, COAT)
    horse.ellipse(90.0, 98.0, 30.0, 15.5, COAT)
    horse.ellipse(114.0, 96.0, 15.0, 15.5, COAT)
    horse.poly([(52.0, 104.0), (126.0, 104.0), (120.0, 111.0), (72.0, 113.0), (56.0, 110.0)], COAT_SHADE, body=False)
    horse.ink([(70.0, 90.0), (72.0, 104.0)], 0.8, K.alpha(COAT_SHADE, 0.9))
    horse.ink([(56.0, 86.0), (66.0, 82.0)], 1.4, COAT_LIGHT)

    # The neck and the head, turned at the poll.
    hp = (142.0, 64.0)
    horse.poly([(104.0, 84.0), (124.0, 86.0), (130.0, 104.0), (148.0, 76.0), (138.0, 58.0)], COAT)
    horse.poly([(124.0, 98.0), (130.0, 104.0), (146.0, 78.0), (140.0, 74.0)], COAT_SHADE, body=False)

    def hd(points):
        return K.turn(points, hp[0], hp[1], head_turn)

    head = [(136.0, 58.0), (146.0, 54.0), (160.0, 64.0), (168.0, 72.0), (167.0, 79.0), (156.0, 80.0), (146.0, 76.0), (138.0, 70.0)]
    horse.poly(hd(head), COAT)
    horse.poly(hd([(150.0, 76.0), (167.0, 79.0), (156.0, 80.0), (146.0, 76.0)]), COAT_SHADE, body=False)
    horse.poly(hd([(158.0, 64.0), (168.0, 72.0), (167.0, 79.0), (160.0, 76.0)]), K.shade(COAT, 0.9), body=False)
    horse.poly(hd([(140.0, 57.0), (138.0, 46.0), (146.0, 54.0)]), COAT)
    horse.poly(hd([(140.5, 55.0), (139.4, 49.0), (143.6, 54.0)]), COAT_SHADE, body=False)
    horse.dot(*hd([(164.0, 73.0)])[0], 1.1, MANE)
    ex, ey = hd([(150.0, 62.0)])[0]
    if eyes == "shut":
        horse.ink([(ex - 2.0, ey), (ex + 2.0, ey + 0.6)], 1.0)
    else:
        r = 2.0 if eyes == "wide" else 1.6
        horse.ellipse(ex, ey, r, r, K.WHITE, body=False)
        horse.dot(ex + 0.5, ey, 1.1, H.SEPIA_INK)
    if mouth == "open":
        horse.ink(hd([(158.0, 79.0), (164.0, 82.0)]), 1.2)
    horse.ink(hd([(150.0, 72.0), (158.0, 70.0), (164.0, 70.0)]), 0.8, H.SADDLE_RED_DARK)
    # The bridle: a red strap over the nose and a rein back to the rider.
    horse.ink(hd([(146.0, 56.0), (148.0, 76.0)]), 1.2, H.SADDLE_RED)

    # The mane: a dark crest that stands up along the neck, and a forelock.
    mane = [(104.0, 84.0)]
    for k in range(6):
        u = (k + 0.5) / 6.0
        x, y = 104.0 + 34.0 * u, 84.0 - 26.0 * u
        mane += [(x - 2.0, y - 4.0 - (k % 2) * 1.5), (x + 3.0, y - 1.0)]
    mane += [(140.0, 60.0), (136.0, 66.0), (110.0, 88.0)]
    horse.poly(mane, MANE)
    horse.poly(hd([(144.0, 55.0), (148.0, 50.0), (150.0, 57.0)]), MANE)

    # The saddle cloth, the saddle and its high front, a stirrup strap.
    horse.poly([(74.0, 82.0), (104.0, 84.0), (106.0, 100.0), (76.0, 100.0)], H.SADDLE_RED)
    horse.poly([(76.0, 96.0), (106.0, 96.0), (106.0, 100.0), (76.0, 100.0)], H.SADDLE_RED_DARK, body=False)
    for x in (80.0, 90.0, 100.0):
        horse.dot(x, 98.0, 0.9, TRIM)
    horse.poly([(78.0, 80.0), (102.0, 80.0), (104.0, 86.0), (78.0, 86.0)], BOW)
    horse.poly([(98.0, 82.0), (104.0, 72.0), (108.0, 74.0), (104.0, 86.0)], BOW)
    horse.poly([(76.0, 84.0), (74.0, 76.0), (80.0, 78.0), (82.0, 84.0)], BOW)

    leg(hips["near"], 0.0, True, COAT)
    leg(shoulders["near"], 0.4, False, COAT)

    # -- the rider -----------------------------------------------------------
    seat = horse.at(90.0, 80.0)
    rider = H.ScaledPen(f, seat, pitch * 0.4 + rider_lean, (0.0, 0.0), RIDER_SCALE)
    if fall:
        # He falls off backwards, over the horse's croup.
        u = min(1.0, fall * 1.4)
        rider = H.ScaledPen(f, seat, pitch * 0.4 - 100.0 * u, (-30.0 * u, -10.0 * math.sin(math.pi * u) + 34.0 * u * u), RIDER_SCALE)
    sx, sy = seat[0], seat[1] - 2.0 - rider_dy

    hip = (sx, sy)
    shoulder = (sx + 2.0, sy - 26.0)
    neck = (sx + 3.0, sy - 30.0)
    head_c = (sx + 4.0, sy - 38.0)

    # The bow hand (near, held out to the front) and the draw hand (far).
    grip = (shoulder[0] + 26.0, shoulder[1] + 1.0 + aim * 0.3)
    if draw <= -0.5:
        grip = (shoulder[0] + 18.0, shoulder[1] + 12.0)
        pull = (shoulder[0] + 12.0, shoulder[1] + 14.0)
    elif draw > 0.5:
        pull = (head_c[0] + 2.0, head_c[1] + 4.0)
    else:
        pull = (grip[0] - 10.0 - 8.0 * recoil, grip[1] - 1.0 - 4.0 * recoil)
        if recoil:
            pull = (head_c[0] - 6.0 * recoil, head_c[1] + 2.0 - 3.0 * recoil)

    def arm(hand: Point, colour, near: bool) -> Point:
        root = (shoulder[0] + (1.0 if near else -1.0), shoulder[1])
        elbow, hand = S.joint(root, hand, 12.0, 12.0, 1.0)
        rider.limb([root, elbow, hand], 5.0, colour)
        rider.poly([(elbow[0] * 0.3 + hand[0] * 0.7 - 2.6, elbow[1] * 0.3 + hand[1] * 0.7 - 2.6),
                    (elbow[0] * 0.3 + hand[0] * 0.7 + 2.6, elbow[1] * 0.3 + hand[1] * 0.7 + 2.6)], TRIM, body=False)
        rider.ellipse(hand[0], hand[1], 2.6, 2.6, H.SKIN)
        return hand

    # The far arm, behind the body: the draw hand.
    pull_hand = arm(pull, DEEL_SHADE, False)

    # The quiver at the far hip, the arrows' feathers up.
    rider.poly([(sx - 12.0, sy - 12.0), (sx - 6.0, sy - 14.0), (sx - 2.0, sy + 6.0), (sx - 8.0, sy + 8.0)], H.SADDLE_RED_DARK)
    for k in range(3):
        rider.ink([(sx - 10.0 + k * 2.0, sy - 13.0), (sx - 11.0 + k * 2.0, sy - 18.0)], 1.6, K.WHITE if k % 2 else H.SADDLE_RED)

    # The leg in its short stirrup, the boot toe turned up.
    knee = (sx + 12.0, sy + 6.0)
    foot = (sx + 8.0, sy + 20.0)
    rider.limb([(sx, sy), knee], 7.0, DEEL)
    rider.limb([knee, foot], 5.0, BOOT)
    rider.poly([(foot[0] - 3.0, foot[1] - 2.0), (foot[0] + 6.0, foot[1] - 1.0), (foot[0] + 8.0, foot[1] - 4.0), (foot[0] + 7.0, foot[1] + 2.0),
                (foot[0] - 3.0, foot[1] + 2.4)], BOOT)
    rider.ink([(foot[0] - 2.0, foot[1] + 3.2), (foot[0] + 5.0, foot[1] + 3.2)], 1.4, IRON)

    # The deel: a long coat, crossed at the chest, a gold edge, an orange sash.
    coat = [(neck[0] - 6.0, neck[1] + 1.0), (neck[0] + 5.0, neck[1] + 1.0), (shoulder[0] + 8.0, shoulder[1] + 10.0),
            (hip[0] + 8.0, hip[1] - 2.0), (hip[0] + 6.0, hip[1] + 6.0), (hip[0] - 9.0, hip[1] + 8.0), (hip[0] - 9.0, hip[1] - 4.0),
            (shoulder[0] - 8.0, shoulder[1] + 6.0)]
    rider.poly(coat, DEEL)
    rider.poly([(hip[0] - 9.0, hip[1] + 8.0), (hip[0] - 9.0, hip[1] - 4.0), (shoulder[0] - 8.0, shoulder[1] + 6.0), (shoulder[0] - 4.0, shoulder[1] + 6.0),
                (hip[0] - 4.0, hip[1] + 8.0)], DEEL_SHADE, body=False)
    rider.ink([(neck[0] + 4.0, neck[1] + 1.0), (shoulder[0] + 7.0, shoulder[1] + 9.0)], 1.6, TRIM)
    rider.ink([(hip[0] - 9.0, hip[1] + 7.0), (hip[0] + 6.0, hip[1] + 5.0)], 1.6, TRIM)
    rider.poly([(hip[0] - 9.0, hip[1] - 8.0), (hip[0] + 8.0, hip[1] - 8.0), (hip[0] + 8.0, hip[1] - 4.0), (hip[0] - 9.0, hip[1] - 4.0)], (232, 132, 48, 255), body=False)

    # The head: a face to the right, a moustache, the fur hat.
    hx, hy = head_c
    rider.ellipse(hx, hy, 6.6, 7.0, H.SKIN)
    rider.poly([(hx + 5.0, hy - 2.0), (hx + 8.6, hy + 1.6), (hx + 5.4, hy + 2.4)], H.SKIN)
    rider.ellipse(hx - 3.0, hy + 1.0, 2.0, 2.4, H.SKIN_SHADE, body=False)
    rider.poly([(hx + 2.0, hy + 3.6), (hx + 7.0, hy + 3.2), (hx + 7.4, hy + 7.4), (hx + 6.2, hy + 4.6), (hx + 3.0, hy + 4.8)], H.HAIR_BLACK, body=False)
    rider.poly([(hx + 4.0, hy + 6.0), (hx + 5.6, hy + 6.2), (hx + 4.8, hy + 9.0)], H.HAIR_BLACK)
    ex, ey = hx + 3.6, hy - 1.2
    if eyes == "shut":
        rider.ink([(ex - 1.6, ey), (ex + 1.4, ey + 0.4)], 0.9)
    elif eyes == "wide":
        rider.ellipse(ex, ey, 1.4, 1.7, K.WHITE, body=False)
        rider.dot(ex + 0.4, ey, 0.8, H.SEPIA_INK)
    else:
        rider.ink([(ex - 1.6, ey + 0.2), (ex + 1.6, ey - 0.2)], 1.1)
    rider.ink([(ex - 2.0, ey - 2.6), (ex + 1.8, ey - 2.0 - (0.8 if eyes == "narrow" else 0.0))], 0.9, H.HAIR_BLACK)
    if mouth == "open":
        rider.ellipse(hx + 5.0, hy + 5.6, 1.0, 1.0, H.SEPIA_INK, body=False)

    def fur_hat(pen: S.Pen, cx: float, cy: float, spin: float) -> None:
        def T(pts):
            return K.turn([(cx + x, cy + y) for x, y in pts], cx, cy, spin)
        pen.poly(T([(-4.0, -3.0), (5.0, -3.0), (1.0, -14.0)]), H.SADDLE_RED)
        pen.poly(T([(1.0, -14.0), (5.0, -3.0), (2.4, -3.0)]), H.SADDLE_RED_DARK, body=False)
        pen.ellipse(*T([(1.0, -15.0)])[0], 1.6, 1.6, TRIM)
        brim = T([(-9.0, 1.0), (-8.0, -4.0), (-3.0, -6.0), (3.0, -6.0), (8.0, -4.0), (9.0, 1.0), (4.0, 2.4), (-4.0, 2.4)])
        pen.poly(brim, H.FUR)
        for k in range(5):
            pen.ink(T([(-7.0 + k * 3.4, -3.6), (-6.0 + k * 3.4, 0.8)]), 0.9, H.FUR_DARK)

    if hat_off is None:
        fur_hat(rider, hx - 0.5, hy - 5.0, 0.0)
    else:
        rider.poly([(hx - 6.0, hy - 3.0), (hx - 2.0, hy - 7.6), (hx + 4.0, hy - 7.0), (hx + 6.0, hy - 3.0)], H.HAIR_BLACK, body=False)
        fur_hat(H.ScaledPen(f, hat_off[:2], 0.0, (0.0, 0.0), RIDER_SCALE), *hat_off)

    # The near arm and the bow in its hand.
    bow_hand = arm(grip, DEEL, True)
    gx, gy = bow_hand
    bend = 6.0 + (7.0 * draw if draw > 0 else 0.0)

    def bow_point(v: float) -> Point:
        # `v` is -1 at the top tip and +1 at the foot; the limbs curve back
        # toward the archer, and the ends flick forward.
        x = gx - bend * (abs(v) ** 0.8) + 4.0 * max(0.0, abs(v) - 0.82) / 0.18
        return (x, gy + 22.0 * v)

    if draw <= -0.5:
        # The bow at rest: held low, slanted, its string straight.
        a = 40.0
        pts = K.turn([bow_point(v / 6.0) for v in range(-6, 7)], gx, gy, a)
        rider.limb(pts, 2.6, BOW)
        rider.ink([pts[1], pts[-2]], 0.8, STRING)
        rider.ink([pts[0], pts[1]], 2.2, BOW_DARK)
        rider.ink([pts[-2], pts[-1]], 2.2, BOW_DARK)
    else:
        pts = K.turn([bow_point(v / 6.0) for v in range(-6, 7)], gx, gy, aim * 0.5)
        rider.limb(pts, 2.6, BOW)
        rider.ink([pts[0], pts[1]], 2.2, BOW_DARK)
        rider.ink([pts[-2], pts[-1]], 2.2, BOW_DARK)
        nock = pull_hand if draw > 0.5 else (gx - bend - 3.0 - 6.0 * recoil * math.sin(i * 2.4), gy)
        rider.ink([pts[1], nock, pts[-2]], 0.8, STRING)
        if draw > 0.5:
            _arrow(rider, nock, aim, 34.0)
        rider.ellipse(gx, gy, 2.6, 2.6, H.SKIN)
    if arrow_out is not None:
        # The arrow in flight, in the frame's own coordinates.
        ay = rider.at(gx, gy)[1] - 1.0 - (arrow_out - 140.0) * 0.06
        _arrow(flat, (arrow_out - 30.0, ay), -2.0, 30.0)
        for k in range(3):
            f.ink([(arrow_out - 40.0 - k * 7.0, ay + 1.0 + (k - 1) * 2.4), (arrow_out - 46.0 - k * 7.0, ay + 1.0 + (k - 1) * 2.4)], 1.0, K.alpha(K.WHITE, 0.8))

    if alarm:
        ax, ay = rider.at(hx + 14.0, hy - 22.0)
        H.alarm_mark(f, ax, max(14.0, ay))
    return f.finish(outline=H.SEPIA_INK, width=1.5, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
