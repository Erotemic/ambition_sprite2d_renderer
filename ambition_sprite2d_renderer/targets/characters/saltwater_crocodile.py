"""The Saltwater Crocodile of the History dimension: the great crocodile of the coasts and rivers.

The saltwater crocodile (Crocodylus porosus) is the largest living reptile.
It lives in the mangroves, the rivers and the coasts from India to the
Philippines, Indonesia and northern Australia, and it swims far out to
sea. It is long and low, olive-grey with dark bands across its back and its
tail, and pale cream under its jaw and its belly. Rows of hard ridged
scales (scutes) run down its back, and two rows of tall scutes run along
the top of its heavy tail. Its snout is long and broad, its teeth show
when its mouth is shut, and its eyes and nostrils are on bumps on top of
its head, so that it can see and breathe with the rest of it under water.

It walks low, with its legs out to the sides and its tail on the ground.
When it sees you it lifts its head (the notice row). Its windup opens its
jaws wide; its strike is a lunge forward with the jaws open, and they snap
shut at the end. A hit makes it pull back with its jaws shut. At its death
it sinks flat and fades.

The frame is 288 by 96 px: the body box is 120 by 32 world units, and the
crocodile faces right.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Sequence, Tuple

from . import _art_cast_kit as K
from . import _history_africa_kit as H

TARGET_NAME = "saltwater_crocodile"
FRAME_SIZE = (288, 96)
ROWS = K.ENEMY_ROWS
#: Nothing is drawn nearer the edge of the frame than this.
MARGIN = 6.0
GROUND = 88.0

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Saltwater Crocodile", "Quadruped", "Large", "Heavy", "Walk", ["crocodile", "reptile", "lunge", "jaws"],
    "The saltwater crocodile of the History dimension's rooms of the Austronesian islands and of Dong Son: long and low, "
    "olive-grey with dark bands, with a heavy tail and a long snout full of teeth. It lifts its head when it sees you, "
    "opens its jaws wide, and lunges forward with its jaws open until they snap shut.",
)
ACTOR_METADATA["tags"] = ["enemy", "history", "austronesian_islands", "dong_son"]

HIDE = (112, 114, 84, 255)
HIDE_SHADE = (82, 84, 60, 255)
HIDE_LIGHT = (150, 150, 108, 255)
BAND = (64, 66, 46, 255)
BELLY = (214, 202, 152, 255)
BELLY_SHADE = (178, 164, 116, 255)
MOUTH = (226, 192, 146, 255)
MOUTH_DARK = (164, 104, 86, 255)
TOOTH = (246, 240, 220, 255)
EYE = (208, 190, 72, 255)
PUPIL = (26, 22, 16, 255)
CLAW = (44, 40, 30, 255)
SPLASH = (186, 170, 130, 255)

Point = Tuple[float, float]


def _lerp(pts: Sequence[Point], x: float) -> float:
    """The y of the line `pts` (x goes up along it) at `x`."""
    if x <= pts[0][0]:
        return pts[0][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / max(1e-6, x1 - x0)
    return pts[-1][1]


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    dx, dy, tilt, pitch, gape = 0.0, 0.0, 0.0, 0.0, 0.0
    walk, stride, lift, sway, raise_ = None, 0.0, 0.0, 0.0, 0.0
    eyes, alarm, sink, fade, snap, speed = "open", False, 0.0, 1.0, False, 0.0
    if anim == "idle":
        # It lies still and breathes; its tail moves a little.
        dy = 0.4 * math.sin(cyc)
        sway = 0.5 * math.sin(cyc)
        gape = 4.0 if i in (2, 3) else 0.0
        eyes = "shut" if i == 4 else "open"
    elif anim == "walk":
        # The high walk: the body up off the ground, the legs out at the
        # sides, and the tail swings behind.
        walk, stride, lift = t, 18.0, 5.0
        raise_ = 3.0
        dy = -1.0 * abs(math.sin(cyc * 2.0))
        sway = math.sin(cyc)
        pitch = 1.5 * math.sin(cyc * 2.0)
    elif anim == "notice":
        # The head comes up and the mouth opens a little.
        k = math.sin(math.pi * min(1.0, t * 1.3))
        pitch, gape, eyes, alarm, raise_ = -8.0 * k, 10.0 * k, "wide", True, 2.0 * k
    elif anim == "windup":
        # The jaws open wide; the body draws back and the tail curls.
        dx, raise_ = -6.0, 4.0
        gape = 44.0 + 3.0 * math.sin(cyc * 2.0)
        pitch = -4.0
        sway = 1.2 * math.sin(cyc * 2.0)
        eyes = "narrow"
    elif anim == "attack_side":
        # The lunge: forward with the jaws open (0..2), they snap shut (3),
        # and back (4..5).
        dx = [-6.0, 4.0, 12.0, 14.0, 8.0, 2.0][i]
        gape = [44.0, 48.0, 44.0, 0.0, 0.0, 6.0][i]
        pitch = [-4.0, -2.0, 0.0, 4.0, 2.0, 0.0][i]
        raise_ = [4.0, 6.0, 5.0, 3.0, 2.0, 1.0][i]
        walk, stride, lift, speed = t * 1.5, 22.0, 6.0, [0.3, 1.0, 0.8, 0.6, 0.2, 0.0][i]
        snap, eyes = i == 3, "narrow"
    elif anim == "hit":
        k = math.sin(math.pi * (i + 1) / (n + 1))
        dx, pitch, eyes, sway, tilt = -7.0 * k, -8.0 * k, "shut", -1.0 * k, -2.0 * k
    elif anim == "death":
        sink = min(1.0, t * 1.4)
        gape, eyes, pitch = 14.0 * sink, "shut", 4.0 * sink
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    # The whole crocodile is drawn this far to the left of its body box, so
    # that the snout stays inside the frame at the end of the lunge.
    dx -= 6.0
    lift_body = raise_ - 3.0 * sink
    cx, cy = 150.0 + dx, 62.0 + dy - lift_body

    def B(pts: Sequence[Point]) -> List[Point]:
        """Body points: moved with the body and turned about its middle."""
        return K.turn([(x + dx, y + dy - lift_body) for x, y in pts], cx, cy, tilt)

    hinge = B([(208.0, 64.0)])[0]
    hx, hy = hinge
    up = -0.7 * gape + pitch + tilt
    lo = 0.3 * gape + pitch + tilt

    def U(pts: Sequence[Point]) -> List[Point]:
        """Points of the upper jaw and the skull, about the hinge of the jaw."""
        return K.turn([(hx + x, hy + y) for x, y in pts], hx, hy, up)

    def L(pts: Sequence[Point]) -> List[Point]:
        """Points of the lower jaw, about the hinge of the jaw."""
        return K.turn([(hx + x, hy + y) for x, y in pts], hx, hy, lo)

    def leg(x: float, phase: float, fore: bool, near: bool) -> None:
        colour = HIDE if near else HIDE_SHADE
        top = B([(x, 68.0)])[0]
        gx, gy = (0.0, 0.0)
        if walk is not None:
            gx, gy = H.gait(walk + phase, stride, lift)
        foot = (top[0] + gx + (4.0 if fore else -2.0), GROUND - 1.0 + gy)
        if sink:
            # The legs splay out to the sides as it sinks flat.
            foot = (top[0] + (10.0 if fore else -10.0) * sink, min(GROUND - 1.0, foot[1]))
        # The elbow and the knee stand out from the body: the legs go out to
        # the sides, so the joint is a little behind and below the top.
        joint = (top[0] + (-5.0 if fore else 6.0), (top[1] + foot[1]) / 2.0 + 1.0)
        f.limb([top, joint], 10.0 if fore else 13.0, colour)
        f.limb([joint, (foot[0], foot[1] - 2.0)], 7.0, colour)
        fx, fy = foot
        # The foot: flat, with toes that spread forward, each with a claw.
        f.poly([(fx - 5.0, fy - 3.0), (fx + 4.0, fy - 3.6), (fx + 9.0, fy - 0.6), (fx + 8.0, fy + 0.8), (fx - 5.0, fy + 0.8)], colour)
        for k in range(3):
            f.ink([(fx + 2.0 + k * 2.4, fy - 1.0), (fx + 4.0 + k * 2.4, fy + 0.6)], 0.8, CLAW)

    # The far legs.
    leg(128.0, 0.0, False, False)
    leg(186.0, 0.5, True, False)

    # The tail: heavy and long, wide at the hips and thin at its tip. It lies
    # on the ground behind and swings a little.
    def wave(x: float) -> float:
        return sway * 4.0 * math.sin((112.0 - x) / 28.0) * (112.0 - x) / 90.0

    xs = [112.0, 96.0, 80.0, 64.0, 48.0, 34.0, 24.0]
    top_line = [(x, y + wave(x)) for x, y in zip(xs, (50.0, 56.0, 62.0, 68.0, 74.0, 79.0, 82.0))]
    bot_line = [(x, y + wave(x)) for x, y in zip(xs, (78.0, 80.0, 82.0, 84.0, 85.0, 85.5, 85.0))]
    tip = (16.0, 84.5 + wave(16.0))
    # The two rows of tall scutes on top of the tail.
    for k, x in enumerate(range(106, 30, -7)):
        y = _lerp(top_line[::-1], x)
        h = 5.0 * (x - 20.0) / 90.0 + 1.6
        f.poly(B([(x - 2.6, y + 1.0), (x + 2.6, y + 1.0), (x + 0.4, y - h)]), HIDE_SHADE if k % 2 else HIDE)
    f.poly(B(top_line + [tip] + bot_line[::-1]), HIDE)
    f.poly(B([(x, (yt + yb) * 0.5 + 3.0) for (x, yt), (_, yb) in zip(top_line, bot_line)] + [tip] + bot_line[::-1]), HIDE_SHADE, body=False)
    # The dark bands across the tail.
    for x in (98.0, 82.0, 66.0, 50.0, 36.0):
        yt, yb = _lerp(top_line[::-1], x), _lerp(bot_line[::-1], x)
        w = 3.6 * (x + 20.0) / 120.0
        f.poly(B([(x - w, _lerp(top_line[::-1], x - w) + 0.6), (x + w, _lerp(top_line[::-1], x + w) + 0.6), (x + w * 0.6, yt + (yb - yt) * 0.8),
                  (x - w * 1.2, yt + (yb - yt) * 0.8)]), BAND, body=False)

    # The body: long and low, a little wider at the hips and the shoulders.
    body = B([(108.0, 50.0), (130.0, 46.0), (160.0, 46.0), (186.0, 48.0), (202.0, 52.0), (210.0, 58.0), (206.0, 72.0), (190.0, 77.0), (160.0, 79.0),
              (130.0, 79.0), (108.0, 78.0)])
    f.poly(body, HIDE)
    f.poly(B([(112.0, 72.0), (150.0, 74.0), (196.0, 72.0), (204.0, 70.0), (192.0, 77.0), (160.0, 79.0), (112.0, 78.0)]), BELLY_SHADE, body=False)
    f.poly(B([(116.0, 50.0), (150.0, 48.0), (190.0, 50.0), (170.0, 52.0), (140.0, 52.0)]), HIDE_LIGHT, body=False)
    # The dark bands across the back.
    for x in (124.0, 146.0, 168.0, 190.0):
        f.poly(B([(x - 4.0, 48.0), (x + 4.0, 48.0), (x + 2.0, 64.0), (x - 6.0, 64.0)]), BAND, body=False)
    # The rows of ridged scutes down the back, and the line of the flank.
    for x in range(114, 200, 6):
        y = 47.0 if 124 < x < 186 else 49.0
        f.poly(B([(x - 2.2, y + 1.0), (x + 2.2, y + 1.0), (x, y - 2.6)]), HIDE_SHADE)
        f.dot(*B([(x, y + 4.0)])[0], 0.8, HIDE_SHADE)
    f.ink(B([(112.0, 66.0), (150.0, 67.0), (196.0, 65.0)]), 1.0, HIDE_SHADE)

    # The mouth: the inside shows when the jaws are open.
    if gape > 3.0:
        f.poly([U([(2.0, 1.0)])[0], U([(28.0, 1.0)])[0], U([(50.0, 1.0)])[0], L([(50.0, 1.0)])[0], L([(28.0, 1.0)])[0], L([(2.0, 1.0)])[0]], MOUTH)
        f.poly([U([(2.0, 1.0)])[0], U([(18.0, 1.0)])[0], L([(18.0, 1.0)])[0], L([(2.0, 1.0)])[0]], MOUTH_DARK, body=False)

    # The lower jaw: long and narrow, pale under the chin, with teeth.
    f.poly(L([(-10.0, 2.0), (0.0, 1.0), (50.0, 1.0), (54.0, 3.0), (51.0, 7.0), (24.0, 9.0), (0.0, 10.0), (-10.0, 9.0)]), HIDE)
    f.poly(L([(0.0, 6.6), (24.0, 6.2), (50.0, 5.0), (51.0, 7.0), (24.0, 9.0), (0.0, 10.0)]), BELLY, body=False)
    for x in range(8, 52, 6):
        f.poly(L([(x - 1.2, 1.4), (x + 1.2, 1.4), (x, -1.8 - (1.0 if x in (14, 44) else 0.0))]), TOOTH, body=False)
    # The neck: thick, from the shoulders to the back of the skull.
    f.poly(B([(196.0, 50.0), (206.0, 52.0), (214.0, 58.0), (214.0, 70.0), (204.0, 74.0), (194.0, 72.0)]), HIDE)
    f.poly(B([(198.0, 68.0), (212.0, 68.0), (210.0, 72.0), (200.0, 73.0)]), BELLY, body=False)
    # The upper jaw and the skull: a long broad snout, the eye on a bump
    # and the nostrils on a bump at its tip.
    upper = U([(-10.0, -10.0), (0.0, -13.0), (4.0, -17.0), (11.0, -17.0), (14.0, -12.0), (30.0, -8.0), (44.0, -6.0), (49.0, -8.0), (54.0, -7.0),
               (57.0, -3.0), (56.0, 1.0), (50.0, 1.0), (0.0, 1.0), (-10.0, 3.0)])
    f.poly(upper, HIDE)
    f.poly(U([(14.0, -11.0), (30.0, -7.6), (44.0, -5.6), (52.0, -6.0), (44.0, -4.0), (28.0, -5.0)]), HIDE_LIGHT, body=False)
    f.poly(U([(2.0, -2.0), (50.0, -2.0), (55.0, -1.0), (56.0, 1.0), (0.0, 1.0)]), HIDE_SHADE, body=False)
    for x in range(6, 54, 6):
        # The teeth of the upper jaw. A crocodile shows them with its mouth shut.
        f.poly(U([(x - 1.2, 0.6), (x + 1.2, 0.6), (x, 3.6 + (1.2 if x in (12, 42) else 0.0))]), TOOTH, body=False)
    # Small dark scales on the snout, and the nostril.
    for x, y in ((22.0, -6.0), (30.0, -4.0), (38.0, -4.4), (26.0, -3.0)):
        f.dot(*U([(x, y)])[0], 0.6, HIDE_SHADE)
    f.dot(*U([(53.0, -6.4)])[0], 0.9, PUPIL)
    # The eye on its bump: yellow with a slit pupil.
    ex, ey = U([(8.0, -13.4)])[0]
    if eyes == "shut":
        f.ink([(ex - 2.6, ey), (ex + 2.6, ey + 0.4)], 1.1, PUPIL)
    else:
        r = 2.4 if eyes == "wide" else (1.6 if eyes == "narrow" else 2.0)
        f.ellipse(ex, ey, 2.6, r, EYE, body=False)
        f.ink([(ex + 0.3, ey - r + 0.4), (ex + 0.3, ey + r - 0.4)], 0.9, PUPIL)
        f.ink(U([(3.0, -17.4), (13.0, -15.0)]), 1.2, HIDE_SHADE)

    # The near legs.
    leg(122.0, 0.5, False, True)
    leg(192.0, 0.0, True, True)

    if speed > 0.1:
        x = min(FRAME_SIZE[0] - MARGIN - 20.0, max(MARGIN + 14.0, B([(192.0, 0.0)])[0][0]))
        H.dust(f, x, GROUND - 1.0, speed * 0.8, f"crocodile dust {anim} {i}", spread=1.0, colour=SPLASH)
    if snap:
        # The jaws snap shut: short lines out from the tip of the snout.
        bx, by = U([(58.0, 0.0)])[0]
        for k in (-1.0, 0.0, 1.0):
            f.ink([(bx + 2.0, by + k * 5.0), (min(FRAME_SIZE[0] - MARGIN - 2.0, bx + 8.0), by + k * 8.0)], 1.4, K.alpha(K.WHITE, 0.95))
    if anim == "death" and t > 0.3:
        H.dust(f, cx, GROUND - 1.0, min(1.0, (t - 0.3) * 2.0), f"crocodile death {i}", spread=2.0, colour=SPLASH)
    if alarm:
        ax, _ = U([(10.0, -30.0)])[0]
        H.alarm_mark(f, min(FRAME_SIZE[0] - MARGIN - 4.0, ax), MARGIN + 13.0)
    return f.finish(outline=H.SEPIA_INK, width=1.7, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
