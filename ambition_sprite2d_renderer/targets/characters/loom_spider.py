"""The Loom Spider: a spider of brass and thread from the Workshop Deeps.

A spider that a weaver built. Its body is a spool of brass, wound with
thread in the colours of the dimension (magenta, cyan and yellow); its head
is a little brass dome with four lenses lit cyan, and its jaws are a pair
of scissors. It stands on eight legs of brass rod with copper joints, and
each leg ends in a needle.

It weaves as it walks: a thread runs out of the back of its spool and its
last leg lays it down behind it. It is a skirmisher: quick, light, and
always at your ankles. Its windup is a rear, with its front legs up and
its scissors open; its strike is a lunge that stabs both front needles
down in front of it and snips. A hit knocks it back and throws sparks; at
its death its legs curl up under it and its thread comes loose.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List

from . import _art_cast_kit as K

TARGET_NAME = "loom_spider"
FRAME_SIZE = (128, 128)
ROWS = K.ENEMY_ROWS
GROUND = 124.0

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Loom Spider", "Multileg", "Small", "Light", "Walk", ["brass", "thread", "spider", "machine"],
    "A spider of brass and thread from the Workshop Deeps of the Art dimension: a spool wound with coloured thread on "
    "eight needle legs, with scissors for jaws. It weaves a thread behind it as it walks, darts in, stabs and snips, "
    "and darts out again.",
)

BRASS = (226, 180, 76, 255)
BRASS_LIGHT = (252, 226, 150, 255)
BRASS_DARK = (150, 106, 38, 255)
COPPER = (206, 112, 62, 255)
COPPER_DARK = (134, 64, 36, 255)
NEEDLE = (226, 230, 240, 255)
OUTLINE = (44, 26, 30, 255)
#: The threads wound on its spool, back to front.
THREADS = (K.MAGENTA, K.CYAN, K.YELLOW)


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    cx = 54.0
    # The pose: the height of the body over the floor, its tilt (degrees, +
    # leans forward, about the back of the body), its shift forward, the
    # front legs (`lift_front`: 0 down, 1 up), `stab` (0..1 the front needles
    # come down in front), the scissors (0 shut, 1 open), the gait, the eyes.
    height, tilt, shift, lift_front, stab, snip, gait, eye = 22.0, 0.0, 0.0, 0.0, 0.0, 0.35, None, 0.7
    curl, fade, spin, sparks, recoil, reach = 0.0, 1.0, 0.0, 0, 0.0, 0.0
    if anim == "idle":
        height += 1.2 * math.sin(cyc)
        snip = 0.3 + 0.25 * max(0.0, math.sin(cyc * 2.0))
        lift_front = 0.12 + 0.1 * math.sin(cyc)
        eye = 0.6 + 0.2 * math.sin(cyc)
    elif anim == "walk":
        gait = cyc
        height += 1.4 * abs(math.sin(cyc * 2.0))
        spin = t
        tilt = 3.0
    elif anim == "notice":
        rise = math.sin(math.pi * t)
        height += 8.0 * rise
        lift_front, eye, snip = 0.4 * rise, 0.7 + 0.3 * rise, 0.7
    elif anim == "windup":
        height += 6.0
        tilt, lift_front, snip, eye = -14.0 + 1.5 * math.sin(cyc * 2.0), 1.0, 1.0, 1.0
        shift = -5.0
    elif anim == "attack_side":
        # The front needles come down from over its head (the first half),
        # stand in the floor, and draw back at the end.
        strike = math.sin(math.pi * min(1.0, t * 1.4))
        shift = -5.0 + 19.0 * strike
        stab = min(1.0, t / 0.45)
        reach = stab if t < 0.75 else 1.0 - (t - 0.75) / 0.25
        tilt = -14.0 + 24.0 * stab
        snip, eye = (1.0 if t < 0.3 else 0.0), 1.0
        height += 6.0 - 6.0 * stab
    elif anim == "hit":
        k = math.sin(math.pi * min(1.0, 0.35 + t))
        tilt, shift, eye, sparks, recoil = -10.0 * k, -6.0 * k, 0.15, 5, k
        height -= 3.0
    elif anim == "death":
        curl, eye = t, 0.6 * (1.0 - t)
        height = 22.0 - 11.0 * t
        tilt = 6.0 * t
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    base = (cx + shift, GROUND - height)
    pivot = (base[0] - 30.0, base[1] + 6.0)

    def b(dx: float, dy: float):
        """A point of the body: `dx` forward and `dy` down from its middle."""
        return K.turn([(base[0] + dx, base[1] + dy)], pivot[0], pivot[1], tilt)[0]

    def bs(points):
        return [b(x, y) for x, y in points]

    # -- the legs ------------------------------------------------------------
    # Each: its root on the body, where its needle stands on the floor, and
    # the step of its gait (the legs move in two sets of four).
    near_tips = (46.0, 27.0, -15.0, -38.0)
    far_tips = (38.0, 19.0, -7.0, -30.0)
    roots = (12.0, 9.0, 6.0, 3.0)
    #: How far forward (+) or back (-) of its root each knee stands.
    knees = (18.0, 7.0, -9.0, -21.0)

    def leg(k: int, near: bool):
        root = b(roots[k] + (0.0 if near else 2.0), 4.0 if near else 0.0)
        tip_x = cx + (near_tips[k] if near else far_tips[k])
        tip_y = GROUND - 2.0
        if gait is not None:
            ph = gait + (0.0 if (k % 2 == 0) == near else math.pi)
            tip_x += 7.0 * math.cos(ph)
            tip_y -= 7.0 * max(0.0, math.sin(ph))
        else:
            tip_x += shift * (0.5 if k < 2 else 0.15)
        if k == 0 and anim == "attack_side":
            # The needle comes down in front, past where it stood.
            tip_x += 18.0 * reach + 6.0 * (1.0 - stab)
            tip_y = GROUND - 2.0 - 46.0 * (1.0 - stab) ** 2
        elif k == 0 and lift_front > 0.0:
            tip_x += 6.0 * lift_front
            tip_y -= 46.0 * lift_front
        if k == 1 and lift_front > 0.6:
            tip_y -= 10.0 * (lift_front - 0.6) / 0.4
        if recoil:
            tip_x += (k - 1.5) * 4.0 * recoil
        if curl > 0.0:
            # The legs curl up under the body.
            tip_x += (base[0] + roots[k] - tip_x) * 0.75 * curl
            tip_y += (base[1] + 8.0 - tip_y) * 0.8 * curl
        tip = (tip_x, tip_y)
        knee_y = min(root[1] - 4.0, tip[1]) - (27.0 - 2.5 * abs(k - 1.5)) * (1.0 - 0.6 * curl)
        knee = (root[0] + knees[k] * (1.0 - 0.5 * curl) + (tip[0] - cx - near_tips[k]) * 0.3, knee_y)
        if k == 0 and (lift_front > 0.5 or (anim == "attack_side" and stab < 0.5)):
            knee = (root[0] + 12.0, root[1] - 18.0)
        metal = BRASS if near else BRASS_DARK
        if near:
            # A ring of ink round a near leg, so it reads over the body.
            f.limb([root, knee, tip], 4.6, OUTLINE, body=False)
        f.limb([root, knee], 3.0, metal)
        f.limb([knee, tip], 2.4, metal)
        if near:
            f.ink([root, knee], 0.8, K.alpha(BRASS_LIGHT, 0.9))
        # The needle at its end: steel, sharp, and a glint.
        dx, dy = tip[0] - knee[0], tip[1] - knee[1]
        ln = math.hypot(dx, dy) or 1.0
        point = (tip[0] + dx / ln * 5.0, tip[1] + dy / ln * 5.0)
        if point[1] > GROUND:
            point = (point[0], GROUND)
        f.limb([tip, point], 1.6, NEEDLE)
        f.ellipse(knee[0], knee[1], 2.2, 2.2, COPPER if near else COPPER_DARK)
        return tip, point

    for k in range(4):
        leg(k, near=False)
    # The near legs come out from under the body: it hides their roots.
    tips = [leg(k, near=True) for k in range(4)]

    def ring(points, d: float = 1.3) -> None:
        """A ring of ink under a part of the body, so it reads over the legs."""
        f.poly(K.grow(points, d), OUTLINE, body=False)

    # -- the thread it weaves ------------------------------------------------
    # The last near leg lays the thread down on the floor.
    spinneret = b(-34.0, 1.0)
    trail_end = tips[3][1]
    wave = 3.0 * math.sin(cyc * 2.0) if anim in ("idle", "walk") else 0.0
    trail = []
    for k in range(9):
        u = k / 8.0
        x = spinneret[0] + (trail_end[0] - spinneret[0]) * u
        y = spinneret[1] + (trail_end[1] - spinneret[1]) * u * u + wave * math.sin(math.pi * u)
        trail.append((x, y))
    if curl > 0.0:
        # The thread comes loose: it falls in loops on the floor.
        trail = [(x, min(GROUND - 2.0, y + 10.0 * curl * math.sin(k * 1.3) ** 2)) for k, (x, y) in enumerate(trail)]
    if anim != "hit":
        f.ink(trail, 1.4, K.MAGENTA)
        f.glow_line(trail, 1.0, K.alpha(K.MAGENTA_LIGHT, 0.35))
    else:
        # The thread snaps: its end curls.
        cut = trail[:4]
        f.ink(cut + [(cut[-1][0] + 2.0, cut[-1][1] - 5.0)], 1.4, K.MAGENTA)

    # -- the body: a spool of brass, wound with thread ------------------------
    spool = bs([(-30.0, -10.0), (-6.0, -10.0), (-6.0, 9.0), (-30.0, 9.0)])
    ring(spool)
    f.poly(spool, THREADS[0])
    band_w = 8.0
    for k, colour in enumerate(THREADS):
        x0 = -30.0 + k * band_w
        f.poly(bs([(x0, -9.5), (x0 + band_w, -9.5), (x0 + band_w, 8.5), (x0, 8.5)]), colour, body=False)
        f.poly(bs([(x0, 3.0), (x0 + band_w, 3.0), (x0 + band_w, 8.5), (x0, 8.5)]), K.shade(colour, 0.72), body=False)
        # The turns of the thread, which slide round as the spool turns.
        for s in range(4):
            xs = x0 + ((s * 2.0 + spin * 8.0) % band_w)
            f.ink(bs([(xs, -9.0), (xs + 1.2, 8.0)]), 0.6, K.alpha(K.shade(colour, 0.6), 0.7))
    f.ink(bs([(-29.0, -6.5), (-7.0, -6.5)]), 1.0, K.alpha(K.WHITE, 0.55))
    # The flanges of the spool: discs of brass at each end.
    for x, colour in ((-32.0, BRASS_DARK), (-5.0, BRASS)):
        disc = K.turn(K.ellipse_points(b(x, 0.0)[0], b(x, 0.0)[1], 3.4, 13.0, 20), b(x, 0.0)[0], b(x, 0.0)[1], tilt)
        ring(disc)
        f.poly(disc, colour)
        c = b(x, 0.0)
        f.ellipse(c[0], c[1], 1.6, 1.6, BRASS_LIGHT, body=False)
    # The body behind the head: a dome of brass, riveted, with a copper plate.
    th = b(8.0, -1.0)
    dome = K.turn(K.ellipse_points(th[0], th[1], 11.0, 9.0, 24), th[0], th[1], tilt)
    ring(dome)
    f.poly(dome, BRASS)
    f.poly(K.turn([(th[0] - 9.0, th[1] + 3.0), (th[0] + 9.0, th[1] + 3.0), (th[0] + 6.0, th[1] + 7.0), (th[0] - 6.0, th[1] + 7.0)],
                  th[0], th[1], tilt), BRASS_DARK, body=False)
    f.poly(K.turn([(th[0] - 4.0, th[1] - 7.0), (th[0] + 5.0, th[1] - 7.0), (th[0] + 5.0, th[1] - 2.0), (th[0] - 4.0, th[1] - 2.0)],
                  th[0], th[1], tilt), COPPER, body=False)
    for k in range(4):
        rx, ry = K.turn([(th[0] - 7.5 + k * 5.0, th[1] + 1.0)], th[0], th[1], tilt)[0]
        f.dot(rx, ry, 0.9, BRASS_DARK)
    f.ink(K.turn([(th[0] - 7.0, th[1] - 4.0), (th[0] - 3.5, th[1] - 7.0)], th[0], th[1], tilt), 1.2, K.alpha(BRASS_LIGHT, 0.9))

    # -- the head, its lenses and its scissors --------------------------------
    hd = b(22.0, 1.0)
    # The scissors: two blades from a rivet at the front of the head.
    pivot_s = b(28.0, 4.0)
    opening = 10.0 + 26.0 * snip
    for k, sign in enumerate((-1.0, 1.0)):
        a = math.radians(tilt + 8.0 + sign * opening / 2.0)
        tip = (pivot_s[0] + math.cos(a) * 13.0, pivot_s[1] + math.sin(a) * 13.0)
        nrm = (-math.sin(a) * sign, math.cos(a) * sign)
        blade = [pivot_s, (pivot_s[0] + math.cos(a) * 6.0 + nrm[0] * 2.4, pivot_s[1] + math.sin(a) * 6.0 + nrm[1] * 2.4), tip]
        f.poly(blade, NEEDLE)
        f.ink([pivot_s, tip], 0.7, K.STEEL_SHADE)
    head = K.turn(K.ellipse_points(hd[0], hd[1], 8.5, 7.5, 20), hd[0], hd[1], tilt)
    ring(head)
    f.poly(head, BRASS)
    f.poly(K.turn([(hd[0] - 6.0, hd[1] + 3.0), (hd[0] + 7.0, hd[1] + 3.0), (hd[0] + 5.0, hd[1] + 7.0), (hd[0] - 5.0, hd[1] + 7.0)],
                  hd[0], hd[1], tilt), BRASS_DARK, body=False)
    f.dot(pivot_s[0], pivot_s[1], 1.6, COPPER)
    # Four lenses: two large in front, two small over them.
    for ox, oy, r in ((4.0, -1.0, 2.6), (-1.5, -1.5, 2.2), (2.0, -5.5, 1.4), (-3.0, -5.0, 1.2)):
        ex, ey = K.turn([(hd[0] + ox, hd[1] + oy)], hd[0], hd[1], tilt)[0]
        f.ellipse(ex, ey, r + 0.6, r + 0.6, OUTLINE, body=False)
        f.ellipse(ex, ey, r, r, K.alpha(K.CYAN, 0.35 + 0.65 * eye), body=False)
        f.dot(ex - r * 0.3, ey - r * 0.3, r * 0.35, K.alpha(K.WHITE, 0.9 * eye))
        if eye > 0.3:
            f.glow(ex, ey, r + 1.2 * eye, K.alpha(K.CYAN, 0.35 * eye))

    if anim == "attack_side" and 0.2 < t < 0.85:
        # The stroke of its needles: lines in the air where they came down.
        a = 1.0 - abs(t - 0.5) * 2.0
        tx, ty = tips[0][1]
        for k in range(3):
            f.glow_line([(tx - 10.0 + k * 4.0, ty - 26.0), (tx - 2.0 + k * 4.0, ty - 6.0)], 1.2, K.alpha(K.CYAN_LIGHT, 0.9 * a))
    if anim == "attack_side" and 0.3 <= t < 0.6:
        # The snip: a flash between the blades.
        sx, sy = b(46.0, 6.0)
        f.glow(sx, sy, 5.0, K.alpha(K.WHITE, 0.8))
        f.glow_line([(sx - 4.0, sy - 4.0), (sx + 4.0, sy + 4.0)], 1.2, K.alpha(K.WHITE, 0.9))
        f.glow_line([(sx - 4.0, sy + 4.0), (sx + 4.0, sy - 4.0)], 1.2, K.alpha(K.WHITE, 0.9))
    for k in range(sparks):
        a = math.radians(-150.0 + k * 30.0)
        r = 14.0 + 16.0 * t
        sx, sy = th[0] + math.cos(a) * r, th[1] - 4.0 + math.sin(a) * r
        f.glow_line([(sx, sy), (sx + math.cos(a) * 6.0, sy + math.sin(a) * 6.0)], 1.8, K.alpha(K.YELLOW, 1.0 - t * 0.5))
        f.glow(sx, sy, 1.6, K.alpha(K.WHITE, 1.0 - t * 0.5))
    if anim == "notice":
        ax, ay = hd[0] + 14.0, hd[1] - 26.0
        f.limb([(ax, ay - 9.0), (ax, ay)], 3.0, K.CYAN)
        f.ellipse(ax, ay + 5.0, 2.0, 2.0, K.CYAN)
    return f.finish(outline=OUTLINE, width=1.4, glow_blur=2.0, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
