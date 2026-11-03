"""The Paper Tiger: a big tiger of folded newspaper in the Story Stacks.

A tiger folded from yesterday's newspaper, as origami is: flat faces and
sharp folds, each face a different shade of the page. Its sides are the
orange of a colour page and its belly and cheeks are the white of the
paper. The print shows on it in grey columns, the stripes of a tiger are
bold black ink, and on its side the headline says "ROAR". It has gold
eyes and a zigzag tail.

It looks fierce and is not: it crumples at a touch. It prowls on four
legs. When it sees you it lifts its head and roars. Its windup is a crouch
with its rear up and its tail lashing; its strike is a pounce, paws
first. A hit crumples part of it. At its death it crumples into a ball of
old newspaper.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List, Sequence, Tuple

from . import _art_cast_kit as K

TARGET_NAME = "paper_tiger"
FRAME_SIZE = (192, 128)
ROWS = K.ENEMY_ROWS
GROUND = 124.0

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Paper Tiger", "Quadruped", "Large", "Light", "Walk", ["paper", "origami", "newspaper", "tiger"],
    "A big tiger of folded newspaper from the Story Stacks of the Art dimension, with ROAR printed on its side. It "
    "looks fierce: it crouches and pounces paws first. It is not: a few hits crumple it into a ball.",
)

#: The orange of a colour page, and the white of the plain paper.
NEWS: K.RGBA = (244, 162, 74, 255)
NEWS_LIGHT: K.RGBA = (252, 196, 128, 255)
NEWS_SHADE: K.RGBA = (204, 118, 50, 255)
NEWS_DARK: K.RGBA = (150, 82, 34, 255)
WHITE_PAGE: K.RGBA = (250, 246, 232, 255)
WHITE_SHADE: K.RGBA = (212, 204, 184, 255)
PRINT: K.RGBA = (120, 116, 110, 255)
EYE: K.RGBA = (255, 196, 40, 255)

#: The strokes of the headline's letters, in a box one unit high.
LETTERS = {
    "R": [[(0.0, 1.0), (0.0, 0.0), (0.55, 0.0), (0.72, 0.14), (0.72, 0.36), (0.55, 0.5), (0.0, 0.5)], [(0.3, 0.5), (0.75, 1.0)]],
    "O": [[(0.36, 0.0), (0.66, 0.12), (0.74, 0.5), (0.66, 0.88), (0.36, 1.0), (0.08, 0.88), (0.0, 0.5), (0.08, 0.12), (0.36, 0.0)]],
    "A": [[(0.0, 1.0), (0.37, 0.0), (0.74, 1.0)], [(0.16, 0.62), (0.58, 0.62)]],
}


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    f = K.Frame(FRAME_SIZE)
    rng = random.Random(f"tiger:{anim}:{i}")
    dx, dy, tilt, crouch, rear_up = 0.0, 0.0, 0.0, 0.0, 0.0
    stride, head_up, jaw, tail_lash, eyes, alarm = 0.0, 0.0, 0.0, 0.0, "open", False
    crumple, crinkle, fade, reach = 0.0, 0.0, 1.0, 0.0
    if anim == "idle":
        dy = 1.0 * math.sin(cyc)
        tail_lash = 0.4 * math.sin(cyc)
    elif anim == "walk":
        stride = math.sin(cyc)
        dy = -1.5 * abs(math.cos(cyc))
        tail_lash = 0.5 * math.sin(cyc + 1.0)
    elif anim == "notice":
        k = math.sin(math.pi * min(1.0, t * 1.3))
        head_up, jaw, alarm, tilt, eyes = 10.0 * k, k, True, -4.0 * k, "wide"
    elif anim == "windup":
        crouch, rear_up, tilt = 12.0, 6.0, 5.0
        tail_lash = 1.2 * math.sin(cyc * 2.0)
        head_up, jaw, eyes = -4.0, 0.3, "narrow"
        dx = -4.0 + 1.0 * math.sin(cyc * 2.0)
    elif anim == "attack_side":
        # The pounce: up and forward, the front paws out, and down again.
        u = min(1.0, t * 1.25)
        arc = math.sin(math.pi * u)
        dx, dy, tilt = -4.0 + 20.0 * u, -16.0 * arc, -10.0 * arc + 6.0 * u * (1.0 - arc)
        reach, jaw, eyes = arc, 0.4 + 0.6 * arc, "narrow"
        crouch = 8.0 * (1.0 - u) * (1.0 - arc)
        tail_lash = -1.0 * arc
    elif anim == "hit":
        k = math.sin(math.pi * t)
        crinkle, tilt, dx, eyes, jaw = 0.5 + 0.5 * k, -8.0 * k, -6.0 * k, "shut", 0.3
    elif anim == "death":
        crumple, eyes, jaw = min(1.0, t * 1.3), "shut", 0.2
        crinkle = 0.6 + 0.4 * crumple
        fade = 1.0 - max(0.0, t - 0.7) / 0.3

    hip = (50.0 + dx, GROUND - 58.0 + dy + crouch - rear_up)
    shoulder = (112.0 + dx, GROUND - 60.0 + dy + crouch)
    ball = (92.0, GROUND - 26.0)
    pivot = ((hip[0] + shoulder[0]) / 2.0, (hip[1] + shoulder[1]) / 2.0)

    def xf(points: Sequence[Tuple[float, float]], tilt_it: bool = True) -> List[Tuple[float, float]]:
        """Points of the body to the frame: the tilt of the body, then the
        crinkle of a hit, then the crumple into a ball."""
        pts = K.turn(points, pivot[0], pivot[1], tilt) if tilt_it else list(points)
        out = []
        for k, (x, y) in enumerate(pts):
            if crinkle:
                j = random.Random(f"{anim}:{i}:{k}:{x:.0f}")
                x += j.uniform(-1.6, 1.6) * crinkle
                y += j.uniform(-1.6, 1.6) * crinkle
            if crumple:
                x += (ball[0] - x) * crumple * 0.85
                y += (ball[1] - y) * crumple * 0.85
            out.append((x, y))
        return out

    def leg(top: Tuple[float, float], swing: float, colour: K.RGBA, front: bool) -> None:
        """A leg folded as a tapered strip, and a paw."""
        out = 18.0 * reach if front else -10.0 * reach
        paw_y = GROUND - 2.0 if not reach else min(GROUND - 2.0, top[1] + 30.0 - (16.0 if front else 4.0) * reach)
        paw = (top[0] + 9.0 * swing + out + (4.0 if front else -2.0), paw_y)
        knee = (top[0] + 4.0 * swing + (out * 0.5) + (-4.0 if front else 6.0), (top[1] + paw[1]) / 2.0 + 2.0)
        w0, w1 = 9.0, 5.0
        strip = [(top[0] - w0, top[1]), (top[0] + w0, top[1]), (knee[0] + w1 + 1.0, knee[1]), (paw[0] + w1, paw[1] - 6.0),
                 (paw[0] - w1, paw[1] - 6.0), (knee[0] - w1, knee[1])]
        f.poly(xf(strip, tilt_it=False), colour)
        f.ink(xf([(top[0] + 1.0, top[1] + 2.0), (knee[0] + 1.0, knee[1]), (paw[0], paw[1] - 6.0)], tilt_it=False), 0.8, K.alpha(NEWS_DARK, 0.9))
        f.poly(xf([(paw[0] - w1 - 1.0, paw[1] - 6.0), (paw[0] + w1 + 6.0, paw[1] - 1.0), (paw[0] + w1 + 5.0, paw[1]), (paw[0] - w1 - 1.0, paw[1])], tilt_it=False), colour)
        if reach > 0.3 and front:
            for k in range(3):
                cx = paw[0] + w1 + 5.0
                f.ink([(cx, paw[1] - 4.0 + k * 2.0), (cx + 4.0, paw[1] - 5.0 + k * 2.6)], 1.0, K.INK)
        # A stripe across the leg.
        f.ink(xf([(knee[0] - w1, knee[1] - 4.0), (knee[0] + w1, knee[1] - 6.0)], tilt_it=False), 2.0, K.INK)

    # The far legs, in the shade of the page.
    body_t = K.turn([hip, shoulder], pivot[0], pivot[1], tilt)
    hip_w, sh_w = body_t
    leg((hip_w[0] + 4.0, hip_w[1] + 22.0), -stride, NEWS_SHADE, False)
    leg((sh_w[0] - 2.0, sh_w[1] + 22.0), stride, NEWS_SHADE, True)

    # The tail: a strip folded in a zigzag, up from the rear.
    lash = tail_lash
    tail = [(hip[0] - 6.0, hip[1] + 4.0), (hip[0] - 18.0, hip[1] - 6.0 + 4.0 * lash), (hip[0] - 14.0, hip[1] - 18.0 + 3.0 * lash),
            (hip[0] - 28.0 - 4.0 * lash, hip[1] - 28.0), (hip[0] - 24.0 - 6.0 * lash, hip[1] - 38.0)]
    for k in range(len(tail) - 1):
        f.limb(xf([tail[k], tail[k + 1]]), 6.0 - k * 0.6, NEWS if k % 2 == 0 else NEWS_SHADE)
    for k in range(1, len(tail) - 1):
        f.ink(xf([(tail[k][0] - 3.0, tail[k][1] - 1.0), (tail[k][0] + 3.0, tail[k][1] + 1.0)]), 2.0, K.INK)
    f.limb(xf([tail[-2], tail[-1]]), 4.4, K.INK)

    # The body: a folded box, a lit top face and a side face.
    bx0, bx1 = hip[0] - 8.0, shoulder[0] + 10.0
    top_face = [(bx0, hip[1] + 6.0), (hip[0] + 6.0, hip[1] - 4.0), (shoulder[0], shoulder[1] - 6.0), (bx1, shoulder[1] + 4.0),
                (shoulder[0], shoulder[1] + 8.0), (hip[0] + 4.0, hip[1] + 10.0)]
    side_face = [(bx0, hip[1] + 6.0), (hip[0] + 4.0, hip[1] + 10.0), (shoulder[0], shoulder[1] + 8.0), (bx1, shoulder[1] + 4.0),
                 (bx1 - 4.0, shoulder[1] + 34.0), (shoulder[0] - 10.0, shoulder[1] + 39.0), (hip[0] + 14.0, hip[1] + 38.0),
                 (bx0 + 2.0, hip[1] + 32.0)]
    f.poly(xf(side_face), NEWS)
    f.poly(xf(top_face), NEWS_LIGHT)
    # A fold down the side: the belly is a darker face.
    belly = [(bx0 + 2.0, hip[1] + 32.0), (hip[0] + 14.0, hip[1] + 38.0), (shoulder[0] - 10.0, shoulder[1] + 39.0), (bx1 - 4.0, shoulder[1] + 34.0),
             (bx1 - 6.0, shoulder[1] + 29.0), (hip[0] + 10.0, hip[1] + 31.0)]
    f.poly(xf(belly), WHITE_PAGE, body=False)
    f.ink(xf(belly[-1:] + belly[:1]), 0.8, WHITE_SHADE)
    # The print of the paper: columns of grey lines on the side.
    for col in range(3):
        x0 = hip[0] + 2.0 + col * 20.0
        for row in range(5):
            y = hip[1] + 15.0 + row * 2.6 + (shoulder[1] - hip[1]) * (col / 3.0)
            ln = 14.0 if (row + col) % 3 else 9.0
            f.ink(xf([(x0, y), (x0 + ln, y)]), 0.6, K.alpha(NEWS_DARK, 0.7))
    # The headline: ROAR, bold, across the side.
    size = 10.0
    lx = hip[0] + 8.0
    ly = (hip[1] + shoulder[1]) / 2.0 + 17.0
    for k, ch in enumerate("ROAR"):
        for stroke in LETTERS[ch]:
            pts = [(lx + k * size * 0.98 + x * size, ly + y * size) for x, y in stroke]
            f.ink(xf(pts), 2.1, K.INK)
    # The stripes: black wedges down from the back.
    for k, sx in enumerate((hip[0] - 4.0, hip[0] + 9.0, hip[0] + 22.0, hip[0] + 35.0, hip[0] + 48.0, hip[0] + 60.0)):
        sy = hip[1] + (shoulder[1] - hip[1]) * (sx - hip[0]) / (shoulder[0] - hip[0])
        lean = 3.0 if k % 2 else -2.0
        wedge = [(sx - 4.5, sy - 4.0), (sx + 4.5, sy - 5.0), (sx + 2.0 + lean, sy + 8.0), (sx + lean, sy + 14.0 + (k % 2) * 2.0), (sx - 1.5, sy + 7.0)]
        f.poly(xf(wedge), K.INK, body=False)
        if 0 < k < 5:
            by = hip[1] + 34.0 + (shoulder[1] - hip[1]) * (sx - hip[0]) / (shoulder[0] - hip[0])
            f.poly(xf([(sx + 5.0, by + 2.0), (sx + 12.0, by + 2.0), (sx + 9.0 - lean, by - 6.0)]), K.INK, body=False)

    # The near legs, in front of the body.
    leg((hip_w[0] - 2.0, hip_w[1] + 24.0), stride, NEWS, False)
    leg((sh_w[0] + 4.0, sh_w[1] + 24.0), -stride, NEWS, True)

    # The head: a big folded head with a broad muzzle, white cheeks that
    # stand out in points (a tiger's ruff), two ears and a jaw. It is drawn
    # in a unit box and made `HEAD` times larger about its middle.
    hx, hy = shoulder[0] + 24.0, shoulder[1] - 6.0 - head_up
    if anim == "attack_side":
        hx += 4.0 * reach
    HEAD = 1.3

    def hd(points):
        return xf([(hx + (x - hx) * HEAD, hy + (y - hy) * HEAD) for x, y in points])

    ears = [[(hx - 13.0, hy - 7.0), (hx - 11.0, hy - 21.0 - 2.0 * (head_up > 4.0)), (hx - 3.0, hy - 11.0)],
            [(hx - 4.0, hy - 11.0), (hx + 1.0, hy - 22.0), (hx + 6.0, hy - 9.0)]]
    for ear in ears:
        f.poly(hd(ear), NEWS)
        f.poly(hd([ear[0], ear[1], ((ear[0][0] + ear[2][0]) / 2.0, (ear[0][1] + ear[2][1]) / 2.0)]), K.INK, body=False)
        f.poly(hd([((ear[0][0] + ear[1][0]) / 2.0, (ear[0][1] + ear[1][1]) / 2.0 + 2.0), ((ear[1][0] + ear[2][0]) / 2.0, (ear[1][1] + ear[2][1]) / 2.0 + 2.0), ((ear[0][0] + ear[2][0]) / 2.0, (ear[0][1] + ear[2][1]) / 2.0)]), WHITE_PAGE, body=False)
    gape = 2.0 + 7.0 * jaw
    # The mouth inside, then the lower jaw.
    f.poly(hd([(hx + 2.0, hy + 5.0), (hx + 18.0, hy + 4.0), (hx + 18.0, hy + 5.0 + gape * 0.6), (hx + 10.0, hy + 8.0 + gape)]), (110, 30, 40, 255))
    f.poly(hd([(hx - 4.0, hy + 7.0), (hx + 17.0, hy + 5.0 + gape * 0.6), (hx + 12.0, hy + 10.0 + gape), (hx + 2.0, hy + 11.0 + gape * 0.5)]), WHITE_SHADE)
    # The ruff: white points of paper at the back of the cheek.
    ruff = [(hx - 8.0, hy - 6.0), (hx - 17.0, hy - 2.0), (hx - 12.0, hy + 1.0), (hx - 18.0, hy + 6.0), (hx - 10.0, hy + 7.0), (hx - 13.0, hy + 12.0), (hx - 2.0, hy + 9.0)]
    f.poly(hd(ruff), WHITE_PAGE)
    skull = [(hx - 12.0, hy - 6.0), (hx - 4.0, hy - 12.0), (hx + 6.0, hy - 10.0), (hx + 19.0, hy - 2.0), (hx + 21.0, hy + 3.0),
             (hx + 6.0, hy + 7.0), (hx - 8.0, hy + 8.0)]
    f.poly(hd(skull), NEWS_LIGHT)
    f.poly(hd([(hx - 12.0, hy - 6.0), (hx + 2.0, hy - 2.0), (hx + 19.0, hy - 2.0), (hx + 21.0, hy + 3.0), (hx + 6.0, hy + 7.0), (hx - 8.0, hy + 8.0)]), NEWS, body=False)
    # The white muzzle and cheek, folded.
    f.poly(hd([(hx + 4.0, hy + 0.0), (hx + 19.0, hy - 1.0), (hx + 21.0, hy + 3.0), (hx + 8.0, hy + 7.0), (hx - 2.0, hy + 7.0)]), WHITE_PAGE, body=False)
    f.ink(hd([(hx + 4.0, hy), (hx + 19.0, hy - 1.0)]), 0.8, WHITE_SHADE)
    # The nose, in ink.
    f.poly(hd([(hx + 17.0, hy - 3.0), (hx + 22.0, hy - 1.0), (hx + 19.0, hy + 2.0)]), K.INK, body=False)
    if jaw > 0.4:
        # Fangs, folded points of paper.
        for fx in (hx + 11.0, hx + 15.0):
            f.poly(hd([(fx - 1.4, hy + 4.0), (fx + 1.4, hy + 4.0), (fx, hy + 7.0 + gape * 0.25)]), K.WHITE, body=False)
    # Stripes on the brow and the cheek.
    for k in range(3):
        f.poly(hd([(hx - 6.0 + k * 3.5, hy - 11.0 + k * 0.8), (hx - 3.6 + k * 3.5, hy - 11.0 + k * 0.8), (hx - 3.6 + k * 3.0, hy - 6.0)]), K.INK, body=False)
    for k in range(2):
        f.ink(hd([(hx - 9.0 + k * 3.0, hy + 1.0 + k * 2.0), (hx - 2.0 + k * 2.0, hy + 2.0 + k * 2.0)]), 1.4, K.INK)
    # The eye: a gold slant of ink.
    ex, ey = hx + 5.0, hy - 5.0
    if eyes == "shut":
        f.ink(hd([(ex - 4.0, ey), (ex + 0.0, ey + 1.6), (ex + 4.0, ey - 0.6)]), 1.5, K.INK)
    else:
        h = 3.4 if eyes == "wide" else (1.6 if eyes == "narrow" else 2.4)
        f.poly(hd([(ex - 4.4, ey + 0.4), (ex + 0.4, ey - h), (ex + 4.6, ey - 0.6), (ex + 0.4, ey + h * 0.5)]), K.INK, body=False)
        f.poly(hd([(ex - 2.8, ey + 0.2), (ex + 0.4, ey - h + 1.0), (ex + 3.2, ey - 0.4), (ex + 0.4, ey + h * 0.3)]), EYE, body=False)
        f.dot(*hd([(ex + 0.6, ey - 0.4)])[0], 0.9)
    hx_front = hx + 22.0 * HEAD
    if alarm:
        ax, ay = hx_front + 4.0, max(14.0, hy - 32.0)
        f.limb([(ax, ay - 10.0), (ax, ay)], 2.8, K.MAGENTA)
        f.ellipse(ax, ay + 5.5, 1.8, 1.8, K.MAGENTA)
    if anim == "notice" and jaw > 0.5:
        # The roar: lines out of its mouth, and it is a small one.
        for k in (-1.0, 0.0, 1.0):
            x0 = hx_front + 4.0
            y0 = hy + 8.0 + k * 6.0
            f.glow_line([(x0, y0), (x0 + 8.0, y0 + k * 3.0)], 1.4, K.alpha(K.WHITE, 0.8 * jaw))
    if anim == "attack_side" and 0.15 < t < 0.75:
        # The swipe of its paws through the air.
        a = 1.0 - abs(t - 0.45) / 0.3
        sx = min(hx_front + 6.0, 176.0)
        for k in range(3):
            y0 = hy + 4.0 + k * 7.0
            f.glow_line([(sx - 4.0, y0), (sx + 6.0, y0 + 10.0)], 2.0, K.alpha(K.YELLOW, 0.85 * a))
    if crinkle:
        # The creases of crumpled paper.
        for _ in range(int(5 + 8 * crinkle)):
            px, py = rng.uniform(hip[0], shoulder[0] + 20.0), rng.uniform(hip[1] + 2.0, hip[1] + 28.0)
            p = xf([(px, py), (px + rng.uniform(-6, 6), py + rng.uniform(-5, 5)), (px + rng.uniform(-6, 6), py + rng.uniform(-5, 5))])
            f.ink(p, 0.7, K.alpha(NEWS_DARK, 0.9))
    if crumple > 0.2:
        # The ball of paper it becomes.
        r = 26.0 * min(1.0, (crumple - 0.2) / 0.6)
        ball_pts = K.ellipse_points(ball[0], ball[1] - 2.0, r, r * 0.92, 14, 3.0, rng)
        f.poly(ball_pts, NEWS)
        f.poly(K.ellipse_points(ball[0] + r * 0.2, ball[1] + r * 0.2, r * 0.7, r * 0.6, 10, 2.0, rng), NEWS_SHADE, body=False)
        for _ in range(int(6 + 6 * crumple)):
            a0 = rng.uniform(0, math.tau)
            p0 = (ball[0] + math.cos(a0) * r * 0.2, ball[1] + math.sin(a0) * r * 0.2)
            p1 = (ball[0] + math.cos(a0) * r * 0.8, ball[1] - 2.0 + math.sin(a0) * r * 0.75)
            f.ink([p0, p1], 0.8, NEWS_DARK)
        if r > 12.0:
            # A scrap of the headline, still on the ball.
            for k, ch in enumerate("RO"):
                for stroke in LETTERS[ch]:
                    f.ink([(ball[0] - 8.0 + k * 8.0 + x * 7.0, ball[1] - 6.0 + y * 7.0) for x, y in stroke], 1.6, K.INK)
    return f.finish(width=1.6, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
