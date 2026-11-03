"""The Silk Moth: a big pale moth of the Silk Road.

A moth as big as a cat: a fat, furry body of cream, pale wings with a
hooked tip and two faint brown bands, black eyes, and two feathered
antennae like combs. The whole Silk Road was named for what its caterpillar
spins.

It floats and it flutters. At rest its wings beat slowly and it bobs. When
it sees you it spreads its wings wide and its antennae stand up. Its
windup lifts its nose and its wings high; its strike is a dive nose first,
wings swept back, with a trail of scale dust. A hit knocks a puff of scales
off it. At its death it folds its wings, wraps itself in silk, and drops as
a cocoon.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List

from . import _art_cast_kit as K
from . import _history_cast_kit as H

TARGET_NAME = "silk_moth"
FRAME_SIZE = (128, 128)
ROWS = K.ENEMY_ROWS

ACTOR_METADATA = H.enemy_metadata(
    TARGET_NAME, "Silk Moth", "Flyer", "Small", "Light", "Float", ["moth", "floating", "silk", "feathered_antennae"],
    "A big pale moth of the Silk Road in the History dimension: a furry cream body, hooked wings and feathered "
    "antennae. It flutters, then dives at you nose first; at its death it wraps itself in silk.",
    "silk",
)

FUR = (246, 238, 220, 255)
FUR_SHADE = (206, 192, 164, 255)
WING = (240, 232, 214, 255)
WING_SHADE = (204, 192, 168, 255)
BAND = (170, 136, 100, 255)
ANTENNA = (120, 84, 50, 255)
EYE = (30, 24, 30, 255)
SILK = (252, 250, 242, 255)

#: The moth is drawn at this size about the middle of its frame.
SCALE = 1.32
MIDDLE = (60.0, 64.0)


class _Bigger(K.Frame):
    """A frame that draws every shape `SCALE` times larger about `MIDDLE`."""

    def _w(self, points):
        mx, my = MIDDLE
        return [((mx + (x - mx) * SCALE) * K.SUPER, (my + (y - my) * SCALE) * K.SUPER) for x, y in points]

    def _at(self, x, y):
        mx, my = MIDDLE
        return mx + (x - mx) * SCALE, my + (y - my) * SCALE

    def ellipse(self, cx, cy, rx, ry, fill, body=True):
        x, y = self._at(cx, cy)
        super().ellipse(x, y, rx * SCALE, ry * SCALE, fill, body)

    def dot(self, cx, cy, r, fill=K.INK):
        x, y = self._at(cx, cy)
        super().dot(x, y, r * SCALE, fill)

    def glow(self, cx, cy, r, fill):
        x, y = self._at(cx, cy)
        super().glow(x, y, r * SCALE, fill)

    def limb(self, points, width, fill, body=True):
        super().limb(points, width * SCALE, fill, body)

    def ink(self, points, width=1.2, fill=K.INK):
        super().ink(points, width * SCALE, fill)

    def glow_line(self, points, width, fill):
        super().glow_line(points, width * SCALE, fill)


#: The wings in wing space: `u` out along the span, `v` forward along the body.
FOREWING = [(0.0, -2.0), (5.0, 5.0), (15.0, 10.0), (25.0, 9.0), (28.0, 5.5), (25.5, 4.0), (24.0, 1.0), (17.0, -4.0), (9.0, -7.0), (2.0, -6.0)]
HINDWING = [(0.0, -5.0), (6.0, -3.0), (14.0, -6.0), (16.0, -11.0), (11.0, -16.0), (4.0, -14.0)]


def _wing(f: K.Frame, root, flap: float, tilt: float, colour, shade_colour, sweep: float = 0.0, scale: float = 1.0):
    """One wing seen from the side: `flap` in degrees (up is positive),
    `sweep` pulls the wing back along the body (0..1)."""
    s = math.sin(math.radians(flap))
    rx, ry = root

    def proj(pts):
        out = []
        for u, v in pts:
            v2 = v - sweep * u * 0.9
            u2 = u * (1.0 - 0.35 * sweep)
            out.append((rx + v2 * scale, ry - u2 * s * scale))
        return K.turn(out, rx, ry, tilt)

    f.poly(proj(HINDWING), shade_colour)
    f.poly(proj(FOREWING), colour)
    if abs(s) > 0.25:
        f.ink(proj([(8.0, -5.0), (12.0, 1.0), (14.0, 7.0)]), 0.8, K.alpha(BAND, 0.8))
        f.ink(proj([(15.0, -3.0), (19.0, 2.0), (21.0, 7.0)]), 0.8, K.alpha(BAND, 0.6))
        f.ink(proj([(25.0, 8.5), (27.6, 5.6)]), 1.0, K.alpha(BAND, 0.9))


def _antenna(f: K.Frame, base, angle: float, length: float, colour) -> None:
    """A feathered antenna: a curved shaft with a comb on each side."""
    pts = []
    for k in range(9):
        u = k / 8.0
        a = math.radians(angle - 40.0 * u)
        if not pts:
            pts.append(base)
        else:
            px, py = pts[-1]
            pts.append((px + math.cos(a) * length / 8.0, py + math.sin(a) * length / 8.0))
    f.ink(pts, 1.2, colour)
    for k in range(1, 8):
        (x0, y0), (x1, y1) = pts[k], pts[k + 1]
        d = math.hypot(x1 - x0, y1 - y0) or 1.0
        nx, ny = -(y1 - y0) / d, (x1 - x0) / d
        w = 2.6 * math.sin(math.pi * k / 8.0) + 0.6
        f.ink([(x0 - nx * w - (x1 - x0) * 0.4, y0 - ny * w - (y1 - y0) * 0.4), (x0, y0), (x0 + nx * w - (x1 - x0) * 0.4, y0 + ny * w - (y1 - y0) * 0.4)],
              0.75, colour)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = _Bigger(FRAME_SIZE)
    cx, cy = 60.0, 62.0
    tilt, flap, sweep, ant, fade = 0.0, 40.0 * math.sin(cyc), 0.0, -100.0, 1.0
    alarm, eyes, scales, cocoon, trail = False, "open", 0.0, 0.0, 0.0
    if anim == "idle":
        cy += 3.0 * math.sin(cyc)
        flap = 15.0 + 55.0 * math.sin(cyc)
        ant = -100.0 + 5.0 * math.sin(cyc)
    elif anim == "walk":
        # Fluttering on, nose a little down.
        cy += 2.0 * math.sin(cyc * 2.0)
        tilt = 8.0
        flap = 15.0 + 60.0 * math.sin(cyc * 2.0)
    elif anim == "notice":
        # Wings spread wide and held; the antennae stand up.
        u = min(1.0, t * 1.6)
        flap = 15.0 + 60.0 * u
        ant = -100.0 + 22.0 * u
        cy -= 3.0 * u
        alarm, eyes = True, "wide"
    elif anim == "windup":
        # Nose up, wings high and quivering.
        tilt = -22.0
        flap = 72.0 + 6.0 * math.sin(cyc * 4.0)
        cx -= 4.0
        cy += 1.0 * math.sin(cyc * 2.0)
        ant = -90.0
    elif anim == "attack_side":
        # The dive: nose first, wings swept back, a trail of scale dust.
        e = math.sin(math.pi * min(1.0, t * 1.2))
        tilt = 26.0 * e - 10.0 * (1.0 - e)
        cx += 24.0 * e
        cy += 8.0 * e
        flap = 40.0 - 20.0 * e
        sweep = e
        trail = e
        ant = -150.0
    elif anim == "hit":
        cx -= 6.0 * math.sin(math.pi * t)
        tilt = -18.0
        flap = -30.0 + 20.0 * t
        eyes = "shut"
        scales = 1.0 - 0.5 * t
    elif anim == "death":
        # It folds its wings, wraps itself in silk, and drops as a cocoon.
        eyes = "shut"
        wrap = min(1.0, t / 0.5)
        flap = 70.0 - 120.0 * wrap
        cocoon = wrap
        fall = max(0.0, (t - 0.35) / 0.65)
        cy += 50.0 * fall * fall
        tilt = 60.0 * fall
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    root = K.turn([(cx - 1.0, cy - 3.0)], cx, cy, tilt)[0]
    body_c = K.turn([(cx - 10.0, cy + 1.5)], cx, cy, tilt)[0]
    head = K.turn([(cx + 7.5, cy - 0.5)], cx, cy, tilt)[0]

    if trail > 0.05:
        for k in range(7):
            u = k / 6.0
            f.ellipse(cx - 14.0 - 22.0 * u * trail, cy - 6.0 - 6.0 * u * trail + 3.0 * math.sin(k * 1.7), 1.2 + 0.6 * (1.0 - u), 1.2 + 0.6 * (1.0 - u),
                      K.alpha(WING, 0.9 * (1.0 - u)), body=False)
        f.glow(cx - 18.0, cy - 6.0, 10.0, K.alpha(K.WHITE, 0.18 * trail))

    # The far wing (in shade), the body, then the near wing.
    if cocoon < 0.95:
        _wing(f, (root[0] - 1.5, root[1] - 0.5), flap * 0.9 + 8.0, tilt, WING_SHADE, K.shade(WING_SHADE, 0.85), sweep, 0.95)
    # The legs, under the thorax.
    for dx in (-2.0, 1.5, 4.5):
        f.ink(K.turn([(cx + dx, cy + 4.0), (cx + dx + 1.5, cy + 8.5), (cx + dx + 3.5, cy + 9.5)], cx, cy, tilt), 1.0, ANTENNA)
    # The abdomen in rings of fur, the thorax, the head.
    abd = K.turn(K.ellipse_points(body_c[0], body_c[1], 9.5, 5.6, 24), body_c[0], body_c[1], tilt + 6.0)
    f.poly(abd, FUR)
    for k in range(3):
        x = body_c[0] - 5.0 + k * 3.6
        f.ink(K.turn([(x, body_c[1] - 4.6), (x - 0.8, body_c[1] + 4.6)], body_c[0], body_c[1], tilt + 6.0), 0.7, FUR_SHADE)
    f.poly(K.turn(K.ellipse_points(body_c[0] + 1.0, body_c[1] + 2.6, 8.0, 2.6, 18), body_c[0], body_c[1], tilt + 6.0), FUR_SHADE, body=False)
    f.ellipse(cx, cy, 6.6, 6.0, FUR)
    for k in range(6):
        a = math.tau * k / 6.0 + 0.4
        f.ink([(cx + math.cos(a) * 4.0, cy + math.sin(a) * 3.6), (cx + math.cos(a) * 6.6, cy + math.sin(a) * 6.0)], 0.6, FUR_SHADE)
    f.ellipse(head[0], head[1], 4.0, 3.8, FUR)
    ex, ey = head[0] + 1.6, head[1] - 0.2
    if eyes == "shut":
        f.ink([(ex - 1.4, ey), (ex + 1.2, ey + 0.4)], 0.9, EYE)
    else:
        r = 2.0 if eyes == "wide" else 1.7
        f.ellipse(ex, ey, r, r, EYE, body=False)
        f.dot(ex - 0.5, ey - 0.6, 0.55, K.WHITE)
    if cocoon < 0.95:
        _wing(f, root, flap, tilt, WING, WING_SHADE, sweep)
    # The feathered antennae, up and back over the head, in front of the wing.
    if cocoon < 0.7:
        _antenna(f, (head[0] - 1.2, head[1] - 3.2), ant + tilt - 16.0, 15.0, K.shade(ANTENNA, 0.75))
        _antenna(f, (head[0] + 0.5, head[1] - 3.0), ant + tilt, 17.0, ANTENNA)
    if cocoon > 0.0:
        # The cocoon: silk wound round it, more with each turn.
        k_turns = int(3 + 9 * cocoon)
        oc = K.turn(K.ellipse_points(cx - 3.0, cy + 0.5, 13.0, 8.0, 28), cx, cy, tilt)
        f.poly(oc, K.alpha(SILK, min(1.0, cocoon * 1.4)))
        for k in range(k_turns):
            u = k / max(1, k_turns - 1)
            x = cx - 14.0 + 22.0 * u
            hgt = 8.0 * math.sqrt(max(0.0, 1.0 - ((x - cx + 3.0) / 13.0) ** 2))
            f.ink(K.turn([(x - 1.5, cy + 0.5 - hgt), (x + 1.5, cy + 0.5 + hgt)], cx, cy, tilt), 0.7, K.alpha(FUR_SHADE, 0.9))
        f.ink(K.turn([(cx + 10.0, cy - 2.0), (cx + 14.0, cy - 12.0 - 6.0 * cocoon)], cx, cy, 0.0), 0.6, K.alpha(SILK, 0.9 * (1.0 - cocoon * 0.5)))
    if scales > 0.0:
        for k in range(8):
            a = math.tau * k / 8.0
            r = 8.0 + 12.0 * scales
            f.ellipse(cx + math.cos(a) * r, cy + math.sin(a) * r * 0.8, 1.4, 1.4, K.alpha(WING, 0.9 * scales), body=False)
    if alarm:
        H.alarm_mark(f, cx + 14.0, cy - 24.0)
    return f.finish(outline=H.SEPIA_INK, width=1.3, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
