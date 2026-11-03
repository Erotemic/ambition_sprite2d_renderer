"""The Clay Golem: a figure of wet clay from the Workshop Deeps.

A heavy figure of terracotta clay that nobody finished. Its lower half was
thrown on a potter's wheel: a round pot, smooth, with the rings of the
throw round it. Its upper half was made by hand: a rough chest, arms made
of coils of clay, and a lump of a head with the top pinched off. The
fingerprints of its maker are pressed into it. It is still wet: slip runs
down it and it shines. Its eyes are two holes pressed in by a thumb, and
the fire of the kiln is lit in them.

It walks on two short legs, heavy and slow. Its windup lifts both fists
over its head; its strike is a slam of both fists onto the floor in front
of it, which splashes clay and cracks the floor. Its arms are wet clay, so
they stretch to reach the floor. A hit dents it and knocks a lump of clay
off its back; at its death it slumps into a heap of clay.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List

from . import _art_cast_kit as K

TARGET_NAME = "clay_golem"
FRAME_SIZE = (192, 192)
ROWS = K.ENEMY_ROWS
GROUND = 186.0
#: The scale of the figure in the frame. It leaves room over its head for
#: its fists and room in front of it for the slam.
Z = 0.82

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Clay Golem", "Biped", "Large", "Heavy", "Walk", ["clay", "golem", "unfinished"],
    "A heavy figure of wet clay in the Workshop Deeps of the Art dimension: a pot thrown on a wheel for its legs and "
    "belly, coils of clay for arms, and the fingerprints of its maker all over it. It lifts both fists and slams them "
    "onto the floor in front of it. Slow to start, and it hits hard.",
)

#: Terracotta: the clay when it is wet, its shade, its light, and its slip.
CLAY = (198, 108, 70, 255)
CLAY_SHADE = (150, 74, 50, 255)
CLAY_LIGHT = (232, 156, 116, 255)
CLAY_DARK = (110, 52, 36, 255)
SLIP = (176, 90, 60, 255)
KILN = (255, 150, 44, 255)
KILN_HOT = (255, 226, 130, 255)
OUTLINE = (58, 24, 22, 255)


def _whorl(f: K.Frame, cx: float, cy: float, r: float, spin: float, a: float = 0.4) -> None:
    """A fingerprint pressed into the clay: three rings that are not closed."""
    for k in range(3):
        rr = r * (0.4 + 0.3 * k)
        pts = [(cx + rr * math.cos(spin + u * 0.25), cy + rr * 0.75 * math.sin(spin + u * 0.25)) for u in range(20)]
        f.ink(pts, 0.7, K.alpha(CLAY_DARK, a))


def _bezier(p0, p1, p2, u: float):
    return ((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0], (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1])


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    rng = random.Random(f"golem:{anim}:{i}")
    f = K.Frame(FRAME_SIZE)
    cx = 66.0
    # The pose: the tilt of the upper body (degrees, + is forward), the bob,
    # the squash, the arms (`raise_`: 0 hang, 1 over the head; `slam`: 0..1
    # brings the fists from over the head to the floor in front), the stride
    # of the legs and the glow of the eyes.
    tilt, bob, sx, sy, raise_, slam, stride, glow = 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.55
    eyes, fade, drip, lump, dent, splash, sag = "open", 1.0, t, 0.0, 0.0, 0.0, 0.0
    if anim == "idle":
        sy = 1.0 + 0.025 * math.sin(cyc)
        sx = 1.0 - 0.015 * math.sin(cyc)
        glow = 0.5 + 0.15 * math.sin(cyc)
        raise_ = 0.06 + 0.05 * math.sin(cyc)
    elif anim == "walk":
        stride = math.sin(cyc)
        bob = 3.0 * abs(math.cos(cyc))
        tilt = 5.0 + 3.0 * math.sin(cyc)
        raise_ = 0.1 + 0.08 * math.cos(cyc)
    elif anim == "notice":
        rise = math.sin(math.pi * t)
        bob, glow, sy, eyes = 5.0 * rise, 0.6 + 0.4 * rise, 1.0 + 0.05 * rise, "wide"
        raise_ = 0.3 * rise
    elif anim == "windup":
        tilt, raise_, glow, sy, sx = -9.0 + 1.5 * math.sin(cyc * 2.0), 1.0, 0.95, 1.04, 0.97
        bob = 2.0 + 1.0 * math.sin(cyc * 2.0)
    elif anim == "attack_side":
        # The fists come down fast, stay on the floor, and come a little way
        # up at the end.
        down = min(1.0, t / 0.4)
        slam = down * down if t < 0.8 else 1.0 - 0.3 * (t - 0.8) / 0.2
        raise_ = 1.0
        tilt, glow = -9.0 + 26.0 * slam, 1.0
        sy, sx = 1.0 - 0.07 * slam, 1.0 + 0.05 * slam
        splash = max(0.0, (t - 0.35) / 0.65)
    elif anim == "hit":
        k = math.sin(math.pi * min(1.0, 0.3 + t))
        tilt, sx, sy, eyes, glow = -12.0 * k - 2.0, 1.08, 0.92, "shut", 0.2
        lump, dent = 0.2 + 0.8 * t, 1.0
    elif anim == "death":
        sag, eyes, glow = t, "shut", 0.5 * (1.0 - t)
        fade = 1.0 - max(0.0, t - 0.75) / 0.25

    # A body that slumps grows wide and low, and its arms hang.
    sy *= 1.0 - 0.6 * sag
    sx *= 1.0 + 0.4 * sag
    tilt += 5.0 * sag
    raise_ *= 1.0 - sag
    legs = max(0.0, 1.0 - 1.6 * sag)

    hip = (cx, GROUND - (12.0 + 26.0 * legs) * sy * Z - bob)

    def up(dx: float, dy: float):
        """A point of the upper body: `dx` forward and `dy` up from the hip."""
        p = (hip[0] + dx * sx * Z, hip[1] - dy * sy * Z)
        return K.turn([p], hip[0], hip[1], tilt)[0]

    def ups(points):
        return [up(x, y) for x, y in points]

    # -- the legs: two stumps, and flat feet -----------------------------------
    for side, shade in ((-1.0, CLAY_SHADE), (1.0, CLAY)):
        swing = stride * side
        lift = 6.0 * max(0.0, swing) if anim == "walk" else 0.0
        fx = cx + (side * 12.0 + 10.0 * swing) * Z
        ankle = (fx + 2.0, GROUND - 13.0 - lift)
        if legs > 0.0:
            knee = (cx + (side * 12.0 + 4.0 * swing) * Z, (hip[1] + ankle[1]) / 2.0)
            f.limb([(hip[0] + side * 11.0 * Z, hip[1] - 4.0), knee, ankle], 18.0 * Z, shade)
        f.ellipse(ankle[0] + 4.0, GROUND - 6.5 - lift, 13.5 * Z * sx, 6.0, shade)

    # -- the arms ----------------------------------------------------------------
    def arm(side: float, colour):
        shoulder = up(side * 34.0 + 4.0, 74.0)
        back = 7.0 if side < 0 else 0.0
        if slam > 0.0:
            # From over the head to the floor in front, on a curve: wet clay
            # stretches to reach the floor.
            over = up(side * 6.0 - 2.0, 146.0)
            floor = (cx + 90.0 - back, GROUND - 13.0)
            fist = _bezier(over, (cx + 104.0, over[1] + 6.0), floor, slam)
            elbow = ((shoulder[0] + fist[0]) / 2.0 + 4.0, min(shoulder[1], fist[1]) - 10.0 + 6.0 * slam)
        elif raise_ > 0.5:
            fist = up(side * 6.0 - 2.0, 146.0)
            elbow = up(side * 38.0, 116.0)
        else:
            lift = raise_ * 2.0
            fist = up(side * 50.0 + 8.0 * lift, 16.0 + 40.0 * lift + 26.0 * sag)
            elbow = up(side * 50.0, 46.0 + 24.0 * lift + 10.0 * sag)
        pts = [shoulder, elbow, fist]
        w = 16.0 * Z
        # A ring of ink round the arm, so it reads in front of the body.
        f.limb(pts, w + 3.2, OUTLINE, body=False)
        f.ellipse(fist[0], fist[1], 11.0 * Z * 1.1 + 1.6, 10.0 * Z * 1.1 + 1.6, OUTLINE, body=False)
        f.limb(pts, w, colour)
        # The coils that the arm is made of.
        for a_, b_ in ((shoulder, elbow), (elbow, fist)):
            dx, dy = b_[0] - a_[0], b_[1] - a_[1]
            ln = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / ln, dx / ln
            count = max(2, int(ln / 9.0))
            for k in range(1, count):
                u = k / float(count)
                mx, my = a_[0] + dx * u, a_[1] + dy * u
                h = w * 0.46
                f.ink([(mx - nx * h, my - ny * h), (mx + dx / ln * 2.0, my + dy / ln * 2.0), (mx + nx * h, my + ny * h)], 1.0,
                      K.alpha(CLAY_DARK, 0.55))
        f.ellipse(fist[0], fist[1], 11.0 * Z * 1.1, 10.0 * Z * 1.1, colour)
        f.ink([(fist[0] + 1.0, fist[1] - 6.0), (fist[0] + 7.0, fist[1] - 2.0)], 1.0, K.alpha(CLAY_DARK, 0.6))
        f.ink([(fist[0] + 0.0, fist[1] - 0.5), (fist[0] + 8.0, fist[1] + 3.5)], 1.0, K.alpha(CLAY_DARK, 0.6))
        return fist

    arm(-1.0, CLAY_SHADE)

    # -- the heap it slumps into ----------------------------------------------
    if sag > 0.2:
        spread = (sag - 0.2) / 0.8
        mound = [(cx - (40.0 + 24.0 * spread) * Z, GROUND - 1.0)]
        mound += [(cx + 4.0 + math.cos(a) * (44.0 + 24.0 * spread) * Z, GROUND - 1.0 - math.sin(a) * (8.0 + 8.0 * spread))
                  for a in [math.pi * (1.0 - u / 10.0) for u in range(11)]]
        f.poly(mound, CLAY)

    # -- the belly: a pot thrown on a wheel -----------------------------------
    right = [(18.0, -4.0), (35.0, 6.0), (42.0, 20.0), (40.0, 34.0), (32.0, 44.0), (27.0, 50.0)]
    f.poly(ups(right + [(-x, y) for x, y in reversed(right)]), CLAY)
    f.poly(ups([(-18.0, -4.0), (-35.0, 6.0), (-42.0, 20.0), (-40.0, 34.0), (-32.0, 44.0), (-27.0, 50.0), (-14.0, 50.0), (-22.0, 30.0),
                (-10.0, -4.0)]), CLAY_SHADE, body=False)
    # The rings of the throw: curves across the pot, dark under a light rim.
    for k, y in enumerate((4.0, 13.0, 22.0, 31.0, 40.0)):
        w = (36.0, 41.0, 42.0, 39.0, 33.0)[k] - 1.0
        ring = [up(w * math.cos(a), y - 3.0 * math.sin(a)) for a in [math.pi * u / 12.0 for u in range(13)]]
        f.ink(ring, 1.1, K.alpha(CLAY_DARK, 0.45))
        f.ink([up(w * 0.92 * math.cos(a), y - 3.0 * math.sin(a) + 1.8) for a in [math.pi * (0.06 + 0.36 * u / 6.0) for u in range(7)]],
              1.0, K.alpha(CLAY_LIGHT, 0.65))
    # The wet shine on its belly: a stripe of light down its round side.
    f.ink(ups([(30.0, 36.0), (35.0, 26.0), (35.0, 14.0), (31.0, 6.0)]), 2.6, K.alpha(CLAY_LIGHT, 0.95))
    f.dot(*up(34.0, 28.0), 1.3, K.alpha(K.WHITE, 0.9))

    # -- the chest: built by hand, rough -------------------------------------
    crng = random.Random("golem:chest")
    chest_pts = [(30.0, 44.0), (38.0, 58.0), (44.0, 72.0), (38.0, 84.0), (20.0, 90.0), (-2.0, 91.0), (-22.0, 88.0), (-38.0, 80.0),
                 (-40.0, 66.0), (-30.0, 46.0)]
    chest_pts = [(x + crng.uniform(-1.6, 1.6), y + crng.uniform(-1.6, 1.6)) for x, y in chest_pts]
    f.poly(ups(chest_pts), CLAY)
    f.poly(ups([(-30.0, 46.0), (-40.0, 66.0), (-38.0, 80.0), (-22.0, 88.0), (-14.0, 80.0), (-20.0, 62.0), (-14.0, 46.0)]), CLAY_SHADE, body=False)
    # The seam where the chest meets the pot: smeared down with a thumb.
    f.ink(ups([(-30.0, 47.0), (-12.0, 44.0), (8.0, 47.0), (30.0, 45.0)]), 1.6, K.alpha(CLAY_DARK, 0.6))
    for k in range(5):
        x = -24.0 + k * 12.0
        f.ink(ups([(x, 47.0), (x + 3.0, 54.0)]), 1.0, K.alpha(CLAY_DARK, 0.5))
    # The fingerprints of its maker.
    _whorl(f, *up(16.0, 70.0), 7.0, 0.3)
    _whorl(f, *up(-6.0, 60.0), 6.0, 2.0)
    _whorl(f, *up(-26.0, 74.0), 5.5, 4.0, 0.3)
    # A handprint where a hit dented it.
    if dent:
        hx, hy = up(8.0, 64.0)
        f.ellipse(hx, hy, 6.0, 5.0, CLAY_SHADE, body=False)
        for k in range(4):
            a = math.radians(-125.0 + k * 22.0)
            f.limb([(hx, hy), (hx + math.cos(a) * 9.0, hy + math.sin(a) * 9.0)], 2.6, CLAY_SHADE, body=False)

    # -- the head: a lump with its top pinched off -----------------------------
    hc = up(8.0, 102.0)
    hrot = tilt * 0.3 - (8.0 if eyes == "wide" else 0.0)
    hrx, hry = 18.0 * Z * sx, 16.0 * Z * sy

    def hp(dx: float, dy: float):
        return K.turn([(hc[0] + dx, hc[1] + dy)], hc[0], hc[1], hrot)[0]

    f.poly(K.turn(K.ellipse_points(hc[0], hc[1], hrx, hry, 24), hc[0], hc[1], hrot), CLAY)
    f.poly([hp(-5.0, -hry + 2.0), hp(1.0, -hry - 9.0 * sy), hp(6.0, -hry - 6.0 * sy), hp(5.0, -hry + 3.0)], CLAY)
    f.ink([hp(0.0, -hry - 1.0), hp(2.5, -hry - 6.0 * sy)], 0.9, K.alpha(CLAY_DARK, 0.6))
    f.poly([hp(-hrx, 0.0), hp(-7.0, -hry + 2.0), hp(-5.0, 4.0), hp(-8.0, hry - 1.0)], CLAY_SHADE, body=False)
    _whorl(f, *hp(-5.0, -5.0), 4.5, 1.0, 0.35)
    # The eyes: two holes pressed in by a thumb, with the kiln lit in them.
    for ox in (-0.5, 11.5):
        ex, ey = hp(ox * sx, -2.0)
        big = 1.25 if eyes == "wide" else 1.0
        if eyes == "shut":
            f.ink([(ex - 2.8, ey), (ex + 2.8, ey + 0.8)], 1.5, CLAY_DARK)
            continue
        f.ellipse(ex, ey, 2.7 * big, 3.3 * big, CLAY_DARK, body=False)
        f.ellipse(ex + 0.4, ey + 0.4, 1.6 * big, 2.0 * big, K.alpha(KILN, 0.5 + 0.5 * glow), body=False)
        f.dot(ex + 0.5, ey, 0.9 * big, K.alpha(KILN_HOT, 0.4 + 0.6 * glow))
        f.glow(ex, ey, 2.0 + 3.5 * glow, K.alpha(KILN, 0.4 * glow))
    # A mouth: a slit drawn with the edge of a tool; open as it slams.
    mx, my = hp(7.0 * sx, 7.0)
    if anim in ("windup", "attack_side"):
        f.ellipse(mx + 1.0, my, 4.0, 2.2 + (1.0 if anim == "attack_side" else 0.0), CLAY_DARK, body=False)
    else:
        f.ink([(mx - 4.5, my), (mx + 1.0, my + 0.8), (mx + 5.0, my - 0.5)], 1.2, CLAY_DARK)

    # -- slip: wet clay that runs down it --------------------------------------
    for k, (x, y0, length) in enumerate(((22.0, 88.0, 14.0), (-12.0, 47.0, 10.0), (33.0, 43.0, 12.0))):
        run = length * (0.55 + 0.45 * ((drip + k * 0.37) % 1.0))
        a_, b_ = up(x, y0), up(x + 0.5, y0 - run)
        f.limb([a_, b_], 2.8, SLIP, body=False)
        f.ellipse(b_[0], b_[1] + 1.0, 2.2, 2.6, SLIP, body=False)

    fist = arm(1.0, K.shade(CLAY, 1.06))

    # -- the strike, the hit, and the notice ---------------------------------------
    if splash > 0.0:
        # Clay splashed up round its fists, and cracks in the floor.
        fx = fist[0]
        crown = []
        for k in range(9):
            u = k / 8.0
            x = fx - 18.0 - 6.0 * splash + u * (36.0 + 12.0 * splash)
            spike = (7.0 + 5.0 * splash) * (1.0 - splash * 0.6) if k % 2 else 2.0
            crown.append((x, GROUND - 1.0 - spike))
        f.poly([(fx - 18.0 - 6.0 * splash, GROUND - 1.0)] + crown + [(fx + 18.0 + 6.0 * splash, GROUND - 1.0)], CLAY_SHADE)
        for k in range(5):
            a = math.radians(-160.0 + k * 35.0)
            r = 10.0 + 24.0 * splash
            px = fx + math.cos(a) * r
            py = GROUND - 14.0 + math.sin(a) * r * 0.8 + 20.0 * splash * splash
            if py < GROUND - 4.0 and px < 184.0:
                f.ellipse(px, py, 2.8 - 1.0 * splash, 2.4 - 0.8 * splash, CLAY)
        for k in range(3):
            x0 = fx - 22.0 + k * 22.0
            f.ink([(x0, GROUND - 1.0), (x0 + 5.0, GROUND - 4.0), (x0 + 2.0, GROUND - 8.0)], 1.0, OUTLINE)
    if lump > 0.0:
        # A lump of clay knocked off its back.
        lx = max(14.0, cx - 40.0 - 24.0 * lump)
        ly = GROUND - 120.0 + 70.0 * lump * lump - 10.0 * lump
        f.poly(K.ellipse_points(lx, ly, 6.5, 5.0, 9, 1.0, rng), CLAY)
        for k in range(3):
            f.ellipse(lx + 4.0 + 5.0 * k, ly - 4.0 + 3.0 * k, 1.5, 1.5, SLIP, body=False)
    if anim == "notice":
        ax, ay = hc[0] + 26.0, hc[1] - 30.0
        f.limb([(ax, ay - 10.0), (ax, ay)], 3.4, KILN)
        f.ellipse(ax, ay + 6.0, 2.2, 2.2, KILN)
    return f.finish(outline=OUTLINE, width=2.0, glow_blur=2.5, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
