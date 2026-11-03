"""The big cats of the Americas of the History dimension: one drawing, two cats.

The sabre-toothed cat (`smilodon.py`) and the jaguar (`jaguar.py`)
are one body with two looks. :class:`Look` holds what makes each cat itself
(the coat, its marks, the tail, the sabres); :class:`Pose` holds what one
frame does (a crouch, a leap, the jaw); :func:`draw` draws the cat;
:func:`pose_for` gives the pose of each row of the enemy cycle of a
pouncer.

The cat is drawn in a design space: its body middle stands on the ground
at `origin`. A :class:`~._history_americas_kit.ScaledFrame` sizes it for
each frame.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from . import _art_cast_kit as K
from . import _history_americas_kit as A
from . import _stage_kit as S

Point = Tuple[float, float]
RGBA = Tuple[int, int, int, int]


@dataclass
class Look:
    coat: RGBA
    coat_shade: RGBA
    belly: RGBA
    mark: RGBA
    eye: RGBA = (226, 170, 52, 255)
    nose: RGBA = (120, 70, 66, 255)
    mouth: RGBA = (150, 46, 56, 255)
    #: ``rosettes`` (the jaguar), ``dapples`` (faint spots) or ``none``.
    marks: str = "none"
    #: The length of the tail, in design units.
    tail: float = 40.0
    #: The length of the sabres below the upper lip (0: no sabres).
    sabre: float = 0.0
    #: The thickness of the neck, the forelegs and the chest.
    bulk: float = 1.0
    #: How much higher the shoulders stand than the hips.
    slope: float = 0.0
    #: The size of the head.
    head: float = 1.0
    #: The distance from the hip to the shoulder, and the depth of the body.
    length: float = 50.0
    depth: float = 1.0
    #: The colour of the muzzle (None: the colour of the belly).
    muzzle: Optional[RGBA] = None
    seed: str = "felid"


@dataclass
class Pose:
    dx: float = 0.0
    dy: float = 0.0
    #: The turn of the body in degrees; positive puts the nose down.
    tilt: float = 0.0
    crouch: float = 0.0
    #: 0..1: the body grows long, as in a leap.
    stretch: float = 0.0
    #: The phase of the walk, or None to stand.
    walk: Optional[float] = None
    stride: float = 24.0
    #: The turn of the head in degrees; positive is down.
    head: float = 0.0
    jaw: float = 0.0
    tail_up: float = 0.0
    swish: float = 0.0
    #: -1 flat back (angry) .. 0 relaxed .. 1 up (alert).
    ears: float = 0.0
    eyes: str = "open"
    #: 0..1: the forepaws reach out in front (a leap).
    reach: float = 0.0
    #: 0..1: the hind legs push out behind (a leap).
    push: float = 0.0
    #: The height of the whole cat above the ground (a leap).
    air: float = 0.0
    #: 0..1: the legs fold and the cat lies down (its death).
    fold: float = 0.0
    #: The forepaws stay where the landing put them (they do not follow `dx`).
    plant: float = 0.0
    lift_paw: float = 0.0


def _mark_spots(f: K.Frame, look: Look, hip: Point, axis: Point, length: float, crouch: float) -> None:
    """The marks of the coat on the side of the body."""
    rng = random.Random(look.seed)
    if look.marks == "none":
        return
    spots: List[Tuple[float, float, float]] = []
    count = 13 if look.marks == "rosettes" else 16
    for k in range(count):
        # Spread evenly along the body, with a little chance in each place.
        u = -8.0 + (length + 16.0) * (k + rng.uniform(0.15, 0.85)) / count
        v = rng.uniform(-15.0, 9.0)
        spots.append((u, v, rng.uniform(3.4, 4.2) if look.marks == "rosettes" else rng.uniform(2.6, 3.6)))
    for u, v, r in spots:
        x, y = A.along(hip, axis, u, v)
        if look.marks == "rosettes":
            # A rosette: a broken ring of dark marks round a deeper gold.
            f.ellipse(x, y, r * 0.8, r * 0.7, K.shade(look.coat, 0.86), body=False)
            for k in range(4):
                a = math.tau * k / 4.0 + rng.uniform(0.0, 0.6)
                f.ellipse(x + math.cos(a) * r, y + math.sin(a) * r * 0.85, 1.5, 1.2, look.mark, body=False)
        else:
            f.ellipse(x, y, r * 0.75, r * 0.55, K.alpha(look.mark, 0.6), body=False)


def draw(f: K.Frame, look: Look, pose: Pose, origin: Point) -> Point:
    """Draw the cat with its body middle over `origin` (on the ground).
    Returns the top of its head (for the "!" mark)."""
    ox, ground = origin
    p = pose
    ox += p.dx
    dp = look.depth
    drop = 14.0 * p.crouch + max(0.0, 42.0 - 15.0 * dp - 6.0) * p.fold
    base_y = ground + p.dy - p.air + drop
    half = look.length / 2.0
    hip0 = (ox - half - 1.0 - 6.0 * p.stretch, base_y - 42.0)
    sh0 = (ox + half - 1.0 + 6.0 * p.stretch, base_y - 42.0 - look.slope)
    mid = A.lerp(hip0, sh0, 0.5)
    hip, sh = K.turn([hip0, sh0], mid[0], mid[1], p.tilt)
    axis, length = A.frame_of(hip, sh)

    def Bd(u: float, v: float) -> Point:
        return A.along(hip, axis, u, v * dp)

    b = look.bulk

    # -- the legs ---------------------------------------------------------
    def foot_of(front: bool, near: bool) -> Point:
        root = sh if front else hip
        fx = root[0] + (3.0 if front else -2.0)
        fy = ground - 4.0
        if p.walk is not None:
            ph = p.walk + (0.25 if front else 0.0) + (0.0 if near else 0.5)
            gx, gy = A.gait(ph, p.stride, 7.0)
            fx += gx
            fy += gy
        if front and near and p.lift_paw:
            fx += 6.0 * p.lift_paw
            fy -= 10.0 * p.lift_paw
        if p.air or p.reach or p.push:
            if front:
                rx = root[0] + 6.0 + 20.0 * p.reach + (3.0 if near else -2.0)
                ry = root[1] + 34.0 - 14.0 * p.reach
                fx = fx + (rx - fx) * min(1.0, p.reach + p.air / 10.0)
                fy = min(ground - 4.0, fy + (ry - fy) * min(1.0, p.reach + p.air / 10.0))
            else:
                rx = root[0] - 6.0 - 24.0 * p.push + (0.0 if near else -3.0)
                ry = root[1] + 32.0 - 8.0 * p.push
                fx = fx + (rx - fx) * min(1.0, p.push + p.air / 10.0)
                fy = min(ground - 4.0, fy + (ry - fy) * min(1.0, p.push + p.air / 10.0))
        if p.fold:
            fx = root[0] + (16.0 if front else -14.0) * p.fold + (0.0 if near else 3.0)
            fy = ground - 4.0
        return fx, fy

    def leg(front: bool, near: bool) -> None:
        colour = look.coat if near else look.coat_shade
        if front:
            root = Bd(length + 1.0, 4.0)
            foot = foot_of(True, near)
            elbow, paw = S.joint(root, foot, 22.0, 22.0, 1.0)
            elbow = (elbow[0], min(elbow[1], ground - 7.0 * b))
            f.limb([root, elbow], 13.0 * b, colour)
            f.limb([elbow, paw], 9.0 * b, colour)
            f.ellipse(paw[0] + 2.5, paw[1] + 0.6, 5.4 * b, 3.4, colour)
            if near:
                for k in range(3):
                    f.ink([(paw[0] + 2.0 + k * 2.4, paw[1] + 3.0), (paw[0] + 2.6 + k * 2.4, paw[1] + 0.8)], 0.6, look.coat_shade)
        else:
            root = Bd(2.0, 2.0)
            foot = foot_of(False, near)
            hock, paw = S.joint(root, foot, 26.0, 22.0, 1.0)
            hock = (hock[0], min(hock[1], ground - 7.0))
            f.limb([root, hock], 13.0, colour)
            f.limb([hock, paw], 7.5, colour)
            f.ellipse(paw[0] + 2.0, paw[1] + 0.8, 5.0, 3.0, colour)
            if near:
                # The haunch: the big muscle over the hind leg.
                f.ellipse(*Bd(2.0, -2.0), 14.0, 15.0, look.coat)
                f.ink([Bd(-8.0, -8.0), Bd(-10.0, 2.0), Bd(-4.0, 10.0)], 1.0, look.coat_shade)

    leg(False, False)
    leg(True, False)

    # -- the tail -----------------------------------------------------------
    root = Bd(-12.0, -10.0)
    segs = 7
    seg = look.tail / segs
    pts = [root]
    for k in range(segs):
        u = k / (segs - 1)
        ang = 150.0 - 70.0 * u * u - 70.0 * p.tail_up * (0.6 + 0.4 * u) + 26.0 * p.swish * u + p.tilt
        if look.tail < 25.0:
            ang = 128.0 - 10.0 * u - 70.0 * p.tail_up + 24.0 * p.swish + p.tilt
        x, y = pts[-1]
        pts.append((x + math.cos(math.radians(ang)) * seg, y + math.sin(math.radians(ang)) * seg))
    for k in range(segs):
        w = (6.4 - 2.6 * k / segs) * (1.4 if look.tail < 25.0 else 1.0)
        colour = look.coat
        if look.marks == "rosettes" and k >= segs - 3 and k % 2 == 0:
            colour = look.mark
        f.limb([pts[k], pts[k + 1]], w, colour)
    tip = pts[-1]
    f.ellipse(tip[0], tip[1], 2.8, 2.8, look.mark if look.marks == "rosettes" else K.shade(look.coat, 0.6))

    # -- the body -------------------------------------------------------------
    L = length
    hump = 2.0 * b
    body = [Bd(-16.0, -2.0), Bd(-12.0, -14.0), Bd(0.0, -18.0), Bd(L * 0.45, -15.0 + 2.0 * p.crouch), Bd(L - 4.0, -19.0 - hump),
            Bd(L + 8.0, -14.0), Bd(L + 13.0, 0.0), Bd(L + 9.0, 13.0 * b), Bd(L * 0.55, 15.0 - 2.0 * p.stretch), Bd(8.0, 13.0), Bd(-10.0, 9.0)]
    f.poly(body, look.coat)
    # The pale belly and throat, and the shade of the back.
    f.poly([Bd(L * 0.2, 9.0), Bd(L * 0.55, 11.0 - 2.0 * p.stretch), Bd(L + 4.0, 10.0 * b), Bd(L + 9.0, 12.0 * b), Bd(L * 0.55, 15.0 - 2.0 * p.stretch),
            Bd(8.0, 13.0)], look.belly, body=False)
    f.poly([Bd(-10.0, -12.0), Bd(0.0, -16.5), Bd(L * 0.45, -13.5 + 2.0 * p.crouch), Bd(L - 4.0, -17.5 - hump), Bd(L - 6.0, -13.0 - hump),
            Bd(L * 0.45, -10.0), Bd(0.0, -12.0)], look.coat_shade, body=False)

    leg(False, True)
    leg(True, True)
    _mark_spots(f, look, hip, axis, L, p.crouch)

    # -- the head -------------------------------------------------------------
    neck = Bd(L + 7.0, -10.0)
    hs = look.head
    pr = p.head + p.tilt
    centre = (neck[0] + 12.0 * hs, neck[1] - 4.0 * hs)
    centre = K.turn([centre], neck[0], neck[1], pr)[0]

    def Hd(*pts: Point) -> List[Point]:
        return K.turn([(centre[0] + x * hs, centre[1] + y * hs) for x, y in pts], centre[0], centre[1], pr)

    f.limb([Bd(L - 2.0, -4.0), neck, centre], 18.0 * b, look.coat)
    # The far ear.
    ear_back = -16.0 * max(0.0, -p.ears) + 6.0 * max(0.0, p.ears)
    f.poly(Hd((-2.0, -9.0), (-1.0 + ear_back * 0.2, -16.0 - 2.0 * p.ears), (4.0, -10.0)), look.coat_shade)
    # The skull and the cheeks.
    f.poly(Hd((-10.0, -2.0), (-6.0, -9.0), (2.0, -11.0), (10.0, -9.0), (16.0, -4.0), (19.0, 1.0), (18.0, 6.0), (10.0, 9.0), (-2.0, 10.0),
              (-9.0, 6.0)), look.coat)
    f.poly(Hd((-6.0, 3.0), (2.0, 4.0), (8.0, 8.0), (-2.0, 9.6), (-8.0, 6.0)), K.shade(look.coat, 1.12), body=False)
    # The lower jaw: it opens about its hinge under the ear.
    gape = 34.0 * p.jaw + (12.0 * p.jaw if look.sabre else 0.0)
    hinge = Hd((0.0, 6.0))[0]
    jaw_pts = K.turn(Hd((0.0, 5.0), (15.0, 6.0), (16.5, 9.0), (8.0, 11.5), (-1.0, 10.0)), hinge[0], hinge[1], gape)
    if p.jaw > 0.05:
        # The inside of the mouth.
        f.poly([Hd((2.0, 6.0))[0], Hd((17.0, 5.0))[0], jaw_pts[2], jaw_pts[3]], look.mouth, body=False)
    f.poly(jaw_pts, look.belly)
    if p.jaw > 0.05 and not look.sabre:
        # The canines of a jaguar.
        for tip, base in ((Hd((15.0, 9.5))[0], Hd((14.0, 5.0))[0]), (jaw_pts[1], jaw_pts[1])):
            if tip == base:
                f.poly([(tip[0] - 1.0, tip[1]), (tip[0] + 1.0, tip[1]), (tip[0], tip[1] - 4.0)], K.WHITE, body=False)
            else:
                f.poly([(base[0] - 1.2, base[1]), (base[0] + 1.2, base[1]), tip], K.WHITE, body=False)
    # The muzzle and the nose.
    f.poly(Hd((9.0, -2.0), (16.0, -4.0), (20.0, 0.0), (19.5, 5.0), (12.0, 6.0), (8.0, 3.0)), look.muzzle or look.belly, body=False)
    if look.marks == "rosettes":
        # Small black spots on the brow and the cheek.
        for sx, sy in ((2.0, -7.0), (5.0, -8.5), (-1.0, -4.0), (1.0, 1.0), (4.0, 3.0), (-3.0, 3.5)):
            f.ellipse(*Hd((sx, sy))[0], 0.9 * hs, 0.8 * hs, look.mark, body=False)
    f.poly(Hd((17.0, -2.4), (20.4, -1.0), (19.4, 1.8), (16.6, 1.0)), look.nose, body=False)
    f.ink(Hd((19.0, 2.0), (18.6, 5.0), (15.0, 6.0)), 0.8, A.SEPIA_INK)
    for k in range(3):
        f.ink(Hd((13.0, 2.0 + k * 1.4), (22.0 + k, 1.0 + k * 2.4)), 0.4, K.alpha(K.WHITE, 0.8))
    if look.sabre:
        # The sabres: long flat canines out of the upper jaw, past the chin.
        s = look.sabre
        for k, dxs in enumerate((0.0, -1.2)):
            base = Hd((12.0 + dxs, 4.4), (15.0 + dxs, 4.6), (14.2 + dxs, 5.0 + s * 0.55), (12.0 + dxs, 5.0 + s))
            f.poly([base[0], base[1], base[2], base[3]], K.WHITE if k == 0 else (226, 220, 206, 255))
            f.ink([A.lerp(base[0], base[3], 0.2), A.lerp(base[0], base[3], 0.85)], 0.5, (190, 180, 160, 255))
    # The eye.
    ex, ey = Hd((8.0, -4.0))[0]
    if p.eyes == "shut":
        f.ink([(ex - 2.4, ey), (ex + 2.4, ey + 0.4)], 1.1, A.SEPIA_INK)
    else:
        ry = {"open": 1.9, "wide": 2.5, "narrow": 1.1}[p.eyes]
        f.ellipse(ex, ey, 2.8, ry, look.eye, body=False)
        f.ellipse(ex + 0.8, ey, 0.9, min(ry, 1.7), A.SEPIA_INK, body=False)
        if p.eyes == "narrow":
            f.ink([(ex - 3.2, ey - 2.6), (ex + 3.0, ey - 0.8)], 1.1, A.SEPIA_INK)
    # The tear line of a big cat, from the eye down the muzzle.
    f.ink(Hd((9.0, -2.0), (11.0, 2.0)), 0.7, look.mark)
    # The near ear.
    f.poly(Hd((-7.0, -6.0), (-6.0 + ear_back * 0.3, -15.0 - 2.0 * p.ears), (-0.5, -9.0)), look.coat)
    f.poly(Hd((-5.6, -7.6), (-5.2 + ear_back * 0.3, -12.6 - 1.6 * p.ears), (-2.4, -8.8)), look.mark, body=False)
    top = Hd((0.0, -16.0))[0]
    return top


def pose_for(anim: str, i: int, n: int) -> Tuple[Pose, bool, float]:
    """The pose of a pouncing cat in each row of the enemy cycle. Returns
    the pose, whether the "!" mark shows, and the fade."""
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    p = Pose()
    alarm, fade = False, 1.0
    if anim == "idle":
        p.dy = 0.6 * math.sin(cyc)
        p.swish = math.sin(cyc)
        p.tail_up = 0.1
        p.head = 4.0 * math.sin(cyc + 0.6)
        p.eyes = "shut" if i == 3 else "open"
    elif anim == "walk":
        p.walk = t
        p.dy = -1.0 * abs(math.sin(cyc * 2.0))
        p.head = 8.0 + 2.0 * math.sin(cyc * 2.0)
        p.swish = 0.5 * math.sin(cyc)
        p.tail_up = 0.15
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.3))
        p.head, p.ears, p.eyes, p.jaw, alarm = -10.0 * k, 1.0, "wide", 0.35 * k, True
        p.tail_up = 0.4 * k
    elif anim == "windup":
        # Low on its belly, the rump wiggles and the tail lashes.
        p.crouch, p.head, p.ears, p.eyes = 1.0, 6.0, -1.0, "narrow"
        p.dx = -3.0 + 1.6 * math.sin(cyc * 2.0)
        p.tilt = 3.0 + 1.5 * math.sin(cyc * 2.0)
        p.swish = math.sin(cyc * 2.0)
        p.tail_up = 0.3
        p.jaw = 0.25
    elif anim == "attack_side":
        # The pounce, as key frames: dx, air, tilt, crouch, stretch, reach,
        # push, jaw, head.
        table = [
            (-2.0, 0.0, -14.0, 0.7, 0.3, 0.2, 0.6, 0.3, -4.0),
            (5.0, 8.0, -9.0, 0.0, 1.0, 1.0, 1.0, 0.8, -2.0),
            (10.0, 11.0, 0.0, 0.0, 1.0, 1.0, 0.8, 1.0, 0.0),
            (13.0, 5.0, 10.0, 0.0, 0.8, 0.7, 0.5, 1.0, 6.0),
            (13.0, 0.0, 7.0, 0.4, 0.3, 0.0, 0.0, 0.6, 8.0),
            (8.0, 0.0, 2.0, 0.2, 0.0, 0.0, 0.0, 0.2, 4.0),
        ]
        dx, air, tilt, crouch, stretch, reach, push, jaw, head = A.keyed(table, t)
        p.dx, p.air, p.tilt, p.crouch, p.stretch, p.reach, p.push, p.jaw, p.head = dx, air, tilt, crouch, stretch, reach, push, jaw, head
        p.ears, p.eyes, p.tail_up = -1.0, "narrow", 0.7
    elif anim == "hit":
        k = math.sin(math.pi * t)
        p.head, p.dx, p.tilt, p.eyes, p.jaw, p.ears = -16.0 * k, -5.0 * k, -4.0 * k, "shut", 0.6 * k, -1.0
    elif anim == "death":
        u = min(1.0, t / 0.8)
        p.fold = min(1.0, u * 1.4)
        p.head = 22.0 * p.fold
        p.tilt = 3.0 * p.fold
        p.eyes = "shut"
        p.tail_up = -0.3 * p.fold
        fade = 1.0 - max(0.0, t - 0.75) / 0.25
    return p, alarm, fade
