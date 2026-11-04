"""The Clouded Leopard of the History dimension: the Formosan clouded leopard of Taiwan.

The clouded leopard (Neofelis nebulosa) lives in the forests of South and
Southeast Asia. Its island form, the Formosan clouded leopard, lived in the
mountain forests of Taiwan, the homeland of the Austronesian peoples; it is
now gone from the wild. It is a mid-sized cat with short strong legs and a
very long, thick tail with dark rings, which balances it in the trees. Its
grey-tan coat has large blotches, each with a dark edge and a darker middle:
the "clouds". It has dark stripes on its neck and spots on its head and
legs. For its size its upper canines are the longest of any cat alive.

It walks low and smooth, its long tail held low with the tip curled up.
When it sees you its ears go up and its tail goes still. Its windup is a
crouch: very low, the rump up, the tail tip twitching. Its strike is the
pounce: it leaps at you with its forepaws out and its jaws wide, and lands.
A hit makes it flatten its ears and snarl; at its death it lies down and
fades.

The frame is 224 by 128 px: the body box is 80 by 40 world units, and the
leopard faces right.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List, Sequence, Tuple

from . import _art_cast_kit as K
from . import _history_africa_kit as H
from . import _stage_kit as S

TARGET_NAME = "clouded_leopard"
FRAME_SIZE = (224, 128)
ROWS = K.ENEMY_ROWS
#: Nothing is drawn nearer the edge of the frame than this.
MARGIN = 6.0
GROUND = 121.0
#: The middle of the body, over the ground.
MID_X = 124.0

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Clouded Leopard", "Quadruped", "Large", "Medium", "Walk", ["cat", "leopard", "pounce", "beast"],
    "The Formosan clouded leopard of the History dimension's Taiwan room: a grey-tan cat with large dark-edged blotches "
    "(the clouds), short strong legs, a very long thick ringed tail and long upper canines. It crouches very low with its "
    "tail tip twitching, then pounces at you with its forepaws out.",
)
ACTOR_METADATA["tags"] = ["enemy", "history", "taiwan"]

Point = Tuple[float, float]

COAT = (198, 180, 140, 255)
COAT_SHADE = (156, 138, 104, 255)
COAT_LIGHT = (222, 208, 172, 255)
BELLY = (236, 228, 204, 255)
CLOUD = (150, 128, 92, 255)
RIM = (46, 36, 30, 255)
EYE = (196, 176, 76, 255)
NOSE = (150, 100, 92, 255)
MOUTH = (150, 46, 56, 255)
FANG = (248, 244, 230, 255)
DUST = (196, 176, 140, 255)
#: The distance from the hip to the shoulder, the height of the back over
#: the ground, and the bones of the short legs.
LENGTH = 60.0
HEIGHT = 34.0
FORE = (16.0, 15.0)
HIND = (19.0, 15.0)
#: The tail: its pieces, and the angle of each (degrees on the screen: 180
#: is back, more than 180 is up): it hangs low and its tip curls up.
TAIL_SEGS = 11
#: The size of the head.
HEAD = 1.22
TAIL_SEG = 7.6
TAIL_SHAPE = [140.0, 155.0, 170.0, 180.0, 185.0, 190.0, 196.0, 206.0, 222.0, 242.0, 262.0]


def _along(origin: Point, axis: Point, u: float, v: float) -> Point:
    """The point `u` along the unit `axis` from `origin`, and `v` across it
    (`v` positive is below the axis when the axis points right)."""
    ax, ay = axis
    return (origin[0] + ax * u - ay * v, origin[1] + ay * u + ax * v)


def _keyed(table: Sequence[Sequence[float]], t: float) -> List[float]:
    """The row of `table` at `t` (0..1), mixed between its two nearest rows."""
    x = max(0.0, min(1.0, t)) * (len(table) - 1)
    k = min(len(table) - 2, int(x))
    u = x - k
    return [a + (b - a) * u for a, b in zip(table[k], table[k + 1])]


def _cloud(f: K.Frame, pts: List[Point], rng: random.Random) -> None:
    """One cloud of the coat: a dark rim round a darker middle, open on one
    side as the real marks often are."""
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    f.poly(pts, RIM, body=False)
    inner = [(cx + (x - cx) * 0.62, cy + (y - cy) * 0.62) for x, y in pts]
    f.poly(inner, CLOUD, body=False)
    # A gap in the rim, on its lower side.
    k = rng.randrange(len(pts))
    a, b = pts[k], pts[(k + 1) % len(pts)]
    f.poly([a, b, inner[(k + 1) % len(pts)], inner[k]], CLOUD, body=False)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)

    dx, dy, tilt, crouch, stretch, walk = 0.0, 0.0, 0.0, 0.0, 0.0, None
    head, jaw, ears, eyes, swish, tail_up = 0.0, 0.0, 0.0, "open", 0.0, 0.0
    reach, push, air, fold, fade, alarm = 0.0, 0.0, 0.0, 0.0, 1.0, False
    if anim == "idle":
        dy = 0.5 * math.sin(cyc)
        swish = math.sin(cyc)
        head = 3.0 * math.sin(cyc + 0.6)
        eyes = "shut" if i == 3 else "open"
    elif anim == "walk":
        walk = t
        dy = -0.8 * abs(math.sin(cyc * 2.0))
        head = 6.0 + 2.0 * math.sin(cyc * 2.0)
        swish = 0.5 * math.sin(cyc)
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.3))
        head, ears, eyes, jaw, alarm = -10.0 * k, 1.0, "wide", 0.3 * k, True
        tail_up = 0.3 * k
    elif anim == "windup":
        # Very low, the rump up and wiggling, the tip of the tail twitching.
        crouch, head, ears, eyes, jaw = 1.0, 4.0, -1.0, "narrow", 0.25
        dx = -4.0 + 1.4 * math.sin(cyc * 2.0)
        tilt = 4.0 + 1.5 * math.sin(cyc * 2.0)
        swish = math.sin(cyc * 2.0)
    elif anim == "attack_side":
        # The pounce, as key frames: dx, air, tilt, crouch, stretch, reach,
        # push, jaw, head.
        table = [
            (-4.0, 0.0, -10.0, 0.8, 0.3, 0.2, 0.6, 0.3, -4.0),
            (2.0, 10.0, -9.0, 0.0, 1.0, 1.0, 1.0, 0.9, -4.0),
            (8.0, 13.0, 0.0, 0.0, 1.0, 1.0, 0.8, 1.0, 0.0),
            (12.0, 5.0, 9.0, 0.0, 0.8, 0.7, 0.5, 1.0, 6.0),
            (12.0, 0.0, 6.0, 0.4, 0.3, 0.0, 0.0, 0.6, 8.0),
            (8.0, 0.0, 2.0, 0.2, 0.0, 0.0, 0.0, 0.2, 4.0),
        ]
        dx, air, tilt, crouch, stretch, reach, push, jaw, head = _keyed(table, t)
        ears, eyes, tail_up = -1.0, "narrow", 0.5
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        head, dx, tilt, eyes, jaw, ears = -16.0 * k, -5.0 * k, -4.0 * k, "shut", 0.7 * k, -1.0
    elif anim == "death":
        u = min(1.0, t / 0.8)
        fold = min(1.0, u * 1.4)
        head, tilt, eyes, tail_up = 22.0 * fold, 3.0 * fold, "shut", -0.3 * fold
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    # The body: the hip and the shoulder, turned by `tilt` about their middle.
    ox = MID_X + dx
    drop = 11.0 * crouch + 18.0 * fold
    base = GROUND + dy - air + drop
    half = LENGTH / 2.0
    hip0 = (ox - half - 5.0 * stretch, base - HEIGHT)
    sh0 = (ox + half + 5.0 * stretch, base - HEIGHT - 2.0 + 3.0 * crouch)
    mid = ((hip0[0] + sh0[0]) / 2.0, (hip0[1] + sh0[1]) / 2.0)
    hip, sh = K.turn([hip0, sh0], mid[0], mid[1], tilt)
    length = math.hypot(sh[0] - hip[0], sh[1] - hip[1])
    axis = ((sh[0] - hip[0]) / length, (sh[1] - hip[1]) / length)

    def Bd(u: float, v: float) -> Point:
        return _along(hip, axis, u, v)

    # -- the legs -------------------------------------------------------------
    def foot_of(front: bool, near: bool) -> Point:
        root = sh if front else hip
        fx, fy = root[0] + (3.0 if front else -2.0), GROUND - 3.0
        if walk is not None:
            ph = walk + (0.25 if front else 0.0) + (0.0 if near else 0.5)
            gx, gy = H.gait(ph, 20.0, 6.0)
            fx += gx
            fy += gy
        if air or reach or push:
            w = min(1.0, (reach if front else push) + air / 10.0)
            if front:
                rx, ry = root[0] + 6.0 + 18.0 * reach + (3.0 if near else -2.0), root[1] + 22.0 - 12.0 * reach
            else:
                rx, ry = root[0] - 6.0 - 22.0 * push + (0.0 if near else -3.0), root[1] + 22.0 - 6.0 * push
            fx, fy = fx + (rx - fx) * w, min(GROUND - 3.0, fy + (ry - fy) * w)
        if crouch and not air and not push:
            # Crouched, the paws stay under the body and the legs fold.
            fx = root[0] + (8.0 if front else 4.0)
        if fold:
            fx, fy = root[0] + (14.0 if front else -10.0) * fold + (0.0 if near else 3.0), GROUND - 3.0
        return fx, fy

    def leg(front: bool, near: bool) -> None:
        colour = COAT if near else COAT_SHADE
        foot = foot_of(front, near)
        if front:
            root = Bd(length + 1.0, 4.0)
            # The elbow goes back and up.
            elbow, paw = max((S.joint(root, foot, FORE[0], FORE[1], b) for b in (-1.0, 1.0)), key=lambda jp: -0.5 * jp[0][0] - jp[0][1])
            f.limb([root, elbow], 12.0, colour)
            f.limb([elbow, paw], 8.4, colour)
            f.ellipse(paw[0] + 2.4, paw[1] + 0.6, 5.0, 3.2, colour)
            if near:
                for k in range(2):
                    px, py = elbow[0] + (paw[0] - elbow[0]) * (0.35 + 0.3 * k), elbow[1] + (paw[1] - elbow[1]) * (0.35 + 0.3 * k)
                    f.ellipse(px, py, 1.6, 1.3, RIM, body=False)
                for k in range(3):
                    f.ink([(paw[0] + 2.0 + k * 2.2, paw[1] + 2.8), (paw[0] + 2.6 + k * 2.2, paw[1] + 0.8)], 0.6, COAT_SHADE)
        else:
            root = Bd(2.0, 2.0)
            # The hock goes back and up.
            hock, paw = max((S.joint(root, foot, HIND[0], HIND[1], b) for b in (-1.0, 1.0)), key=lambda jp: -0.2 * jp[0][0] - jp[0][1])
            f.limb([root, hock], 13.0, colour)
            f.limb([hock, paw], 7.4, colour)
            f.ellipse(paw[0] + 2.0, paw[1] + 0.8, 4.8, 3.0, colour)
            if near:
                # The haunch: the big muscle over the hind leg, with spots.
                f.ellipse(*Bd(2.0, -1.0), 14.0, 14.0, COAT)
                f.ink([Bd(-8.0, -8.0), Bd(-10.0, 2.0), Bd(-4.0, 10.0)], 1.0, COAT_SHADE)
                for u, v in ((4.0, -6.0), (-3.0, 2.0), (6.0, 6.0)):
                    f.ellipse(*Bd(u, v), 1.8, 1.5, RIM, body=False)

    leg(False, False)
    leg(True, False)

    # -- the tail: very long and thick, low, its tip curled up --------------
    root = Bd(-12.0, -6.0)
    pts = [root]
    for k in range(TAIL_SEGS):
        u = k / (TAIL_SEGS - 1)
        ang = TAIL_SHAPE[k] + tilt + 26.0 * swish * u * u + 40.0 * tail_up * u + 12.0 * fold * u
        if anim == "attack_side":
            # In the pounce the tail streams out behind, a little up.
            ang = 172.0 + 95.0 * u * u + tilt * 0.5
        x, y = pts[-1]
        x, y = x + math.cos(math.radians(ang)) * TAIL_SEG, y - math.sin(math.radians(ang - 180.0)) * TAIL_SEG
        pts.append((x, min(GROUND - 4.0, y)))
    for k in range(TAIL_SEGS):
        f.limb([pts[k], pts[k + 1]], 9.0 - 2.4 * k / TAIL_SEGS, COAT)
    # The dark rings: a band across the tail in each piece. Near the root
    # they are broken spots; out to the tip they are full and wide.
    for k in range(1, TAIL_SEGS):
        a, b = pts[k], pts[k + 1]
        w = (9.0 - 2.4 * k / TAIL_SEGS) / 2.0 + 0.4
        sx, sy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(sx, sy) or 1.0
        ux, uy = sx / d, sy / d
        nx, ny = -uy, ux
        band = 2.2 + 1.6 * k / TAIL_SEGS
        c = (a[0] + sx * 0.5, a[1] + sy * 0.5)
        if k < 4:
            f.ellipse(c[0] - nx * w * 0.4, c[1] - ny * w * 0.4, 1.8, 1.6, RIM, body=False)
            continue
        f.poly([(c[0] - ux * band / 2 - nx * w, c[1] - uy * band / 2 - ny * w), (c[0] + ux * band / 2 - nx * w, c[1] + uy * band / 2 - ny * w),
                (c[0] + ux * band / 2 + nx * w, c[1] + uy * band / 2 + ny * w), (c[0] - ux * band / 2 + nx * w, c[1] - uy * band / 2 + ny * w)],
               RIM, body=False)
    f.ellipse(pts[-1][0], pts[-1][1], 3.4, 3.4, RIM)

    # -- the body --------------------------------------------------------------
    L = length
    body = [Bd(-15.0, -2.0), Bd(-11.0, -13.0), Bd(0.0, -16.0), Bd(L * 0.45, -14.0 + 2.0 * crouch), Bd(L - 4.0, -17.0), Bd(L + 8.0, -13.0),
            Bd(L + 12.0, 0.0), Bd(L + 8.0, 12.0), Bd(L * 0.55, 14.0 - 2.0 * stretch), Bd(8.0, 13.0), Bd(-10.0, 9.0)]
    f.poly(body, COAT)
    f.poly([Bd(L * 0.15, 9.0), Bd(L * 0.55, 10.0 - 2.0 * stretch), Bd(L + 3.0, 9.0), Bd(L + 8.0, 11.0), Bd(L * 0.55, 14.0 - 2.0 * stretch),
            Bd(8.0, 13.0)], BELLY, body=False)
    f.poly([Bd(-10.0, -11.0), Bd(0.0, -15.0), Bd(L * 0.45, -13.0 + 2.0 * crouch), Bd(L - 4.0, -16.0), Bd(L - 6.0, -12.0), Bd(L * 0.45, -9.5),
            Bd(0.0, -11.0)], COAT_LIGHT, body=False)
    leg(False, True)
    leg(True, True)

    # The clouds: large blotches over the flank, the haunch and the
    # shoulder, smaller near the belly.
    rng = random.Random("clouded leopard clouds")
    for u, v, r in ((-4.0, -2.0, 7.0), (10.0, -6.0, 8.5), (26.0, -7.0, 9.0), (42.0, -6.0, 8.5), (57.0, -5.0, 7.5), (4.0, 7.0, 6.0),
                    (19.0, 6.0, 6.5), (35.0, 6.0, 6.5), (50.0, 6.0, 5.5)):
        pts_c = []
        for k in range(7):
            a = math.tau * k / 7.0 + rng.uniform(-0.25, 0.25)
            rr = r * rng.uniform(0.75, 1.15)
            pts_c.append(Bd(u + math.cos(a) * rr * 1.25, v + math.sin(a) * rr * 0.75))
        _cloud(f, pts_c, rng)
    # Small dark spots on the back.
    for u, v in ((4.0, -12.0), (16.0, -13.0), (30.0, -12.5), (44.0, -13.0), (56.0, -12.0)):
        f.ellipse(*Bd(u, v), 1.6, 1.3, RIM, body=False)


    # -- the head: long and low, on a neck with dark stripes ------------------
    neck = Bd(L + 6.0, -9.0)
    pr = head + tilt
    centre = K.turn([(neck[0] + 13.0, neck[1] - 4.0)], neck[0], neck[1], pr)[0]

    def Hd(*p: Point) -> List[Point]:
        return K.turn([(centre[0] + x * HEAD, centre[1] + y * HEAD) for x, y in p], centre[0], centre[1], pr)

    f.limb([Bd(L - 2.0, -3.0), neck, centre], 19.0, COAT)
    # The stripes of the neck.
    for k in range(3):
        a0 = Bd(L - 4.0 + k * 5.0, -14.0 + k)
        a1 = Bd(L - 1.0 + k * 5.0, -2.0 + k)
        f.ink([a0, a1], 2.0, RIM)
    ear_back = -14.0 * max(0.0, -ears) + 5.0 * max(0.0, ears)
    # The far ear: short and round.
    f.poly(Hd((-2.0, -8.0), (0.0 + ear_back * 0.2, -14.0 - 2.0 * ears), (4.0, -9.0)), COAT_SHADE)
    # The skull and the cheeks.
    f.poly(Hd((-9.0, -2.0), (-6.0, -8.0), (2.0, -10.0), (10.0, -8.0), (16.0, -4.0), (20.0, 1.0), (19.0, 5.0), (10.0, 8.0), (-2.0, 9.0),
              (-8.0, 5.0)), COAT)
    f.poly(Hd((-6.0, 3.0), (2.0, 4.0), (8.0, 7.0), (-2.0, 8.6), (-7.0, 5.0)), COAT_LIGHT, body=False)
    # The spots and the lines of the head.
    for sx, sy in ((1.0, -7.0), (4.0, -8.0), (7.0, -7.0), (-2.0, -4.0), (0.0, 1.0), (3.0, 3.0)):
        f.ellipse(*Hd((sx, sy))[0], 0.9, 0.8, RIM, body=False)
    f.ink(Hd((-4.0, 1.0), (4.0, 5.0)), 1.0, RIM)
    # The lower jaw: it opens wide about its hinge.
    gape = 40.0 * jaw
    hinge = Hd((0.0, 5.0))[0]
    jaw_pts = K.turn(Hd((0.0, 4.0), (16.0, 5.0), (17.0, 8.0), (8.0, 10.6), (-1.0, 9.0)), hinge[0], hinge[1], gape)
    if jaw > 0.05:
        f.poly([Hd((2.0, 5.0))[0], Hd((18.0, 4.0))[0], jaw_pts[2], jaw_pts[3]], MOUTH, body=False)
        # The small lower canine.
        b = jaw_pts[1]
        f.poly([(b[0] - 1.6, b[1]), (b[0] - 0.2, b[1]), (b[0] - 1.0, b[1] - 3.0)], FANG, body=False)
    f.poly(jaw_pts, BELLY)
    # The muzzle and the nose.
    f.poly(Hd((10.0, -2.0), (17.0, -3.4), (21.0, 0.0), (20.6, 4.4), (13.0, 5.0), (9.0, 3.0)), BELLY, body=False)
    f.poly(Hd((18.0, -2.2), (21.4, -0.8), (20.4, 1.8), (17.6, 1.0)), NOSE, body=False)
    f.ink(Hd((20.0, 2.0), (19.6, 4.4), (16.0, 5.0)), 0.8, H.SEPIA_INK)
    for k in range(3):
        f.ink(Hd((14.0, 2.0 + k * 1.3), (22.0 + k, 1.0 + k * 2.2)), 0.4, K.alpha(K.WHITE, 0.8))
    # The long upper canines: they show below the lip even when the mouth
    # is shut, and are long when it opens.
    for k, dxs in enumerate((0.0, -1.4)):
        ln = 6.4 + 2.6 * jaw
        base = Hd((14.6 + dxs, 4.0), (17.0 + dxs, 4.2), (15.4 + dxs, 4.4 + ln))
        f.poly(base, FANG if k == 0 else (226, 218, 198, 255))
    # The eye, with a dark line under it.
    ex, ey = Hd((8.0, -4.0))[0]
    if eyes == "shut":
        f.ink([(ex - 2.4, ey), (ex + 2.4, ey + 0.4)], 1.1, H.SEPIA_INK)
    else:
        ry = {"open": 1.8, "wide": 2.4, "narrow": 1.0}[eyes]
        f.ellipse(ex, ey, 2.6, ry, EYE, body=False)
        f.ellipse(ex + 0.7, ey, 0.8, min(ry, 1.6), H.SEPIA_INK, body=False)
        if eyes == "narrow":
            f.ink([(ex - 3.0, ey - 2.4), (ex + 2.8, ey - 0.8)], 1.1, H.SEPIA_INK)
    f.ink(Hd((9.0, -2.0), (11.0, 2.0)), 0.8, RIM)
    # The near ear.
    f.poly(Hd((-7.0, -5.0), (-5.5 + ear_back * 0.3, -13.0 - 2.0 * ears), (-0.5, -8.0)), COAT)
    f.poly(Hd((-5.4, -6.6), (-5.0 + ear_back * 0.3, -11.0 - 1.6 * ears), (-2.4, -7.8)), RIM, body=False)
    top = Hd((0.0, -15.0))[0]

    if anim == "death" and t > 0.3:
        H.dust(f, ox, GROUND - 1.0, min(1.0, (t - 0.3) * 2.0), f"cl:death:{i}", spread=2.2, colour=DUST)
    if anim == "attack_side" and i >= n - 2:
        H.dust(f, ox + 24.0, GROUND - 1.0, 0.7, f"cl:land:{i}", spread=1.2, colour=DUST)
    if alarm:
        H.alarm_mark(f, min(FRAME_SIZE[0] - MARGIN - 4.0, top[0] + 6.0), max(MARGIN + 11.0, top[1] - 8.0))
    return f.finish(outline=H.SEPIA_INK, width=1.6, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
