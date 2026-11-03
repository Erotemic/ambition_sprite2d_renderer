"""The Discord Note: two eighth notes of the Resonant Reach that do not agree.

Two black note heads on two stems, joined at the top by one beam, as two
eighth notes are written. The notes are one step apart, which is the most
sour interval there is, and each head has a sour face that glares at the
other. A jagged line of cyan sound buzzes between them.

It floats. In a fight both faces turn to you. Its windup pulls the two
heads apart and bends the beam like a spring; its strike claps them
together in front of it, with a burst of jagged sound. A hit bends the
beam; at its death the beam snaps and the two notes fall apart.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import List

from . import _art_cast_kit as K

TARGET_NAME = "discord_note"
FRAME_SIZE = (96, 96)
ROWS = K.ENEMY_ROWS

ACTOR_METADATA = K.enemy_metadata(
    TARGET_NAME, "Discord Note", "Amorphous", "Small", "Light", "Float", ["music", "note", "floating"],
    "Two eighth notes of the Resonant Reach of the Art dimension, joined by a beam and one sour step apart: each head "
    "has a sour face that glares at the other. It floats in close, pulls its heads apart, and claps them together.",
)

#: The colours of the Resonant Reach.
EBONY = (30, 24, 46, 255)
EBONY_SHEEN = (84, 92, 168, 255)
SOUND = K.CYAN
SOUND_LIGHT = K.CYAN_LIGHT


def _zigzag(x0: float, y0: float, x1: float, y1: float, teeth: int, amp: float, rng: random.Random) -> list:
    """A jagged line from one point to the other: sound that does not agree."""
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / length, dx / length
    pts = []
    for k in range(teeth + 1):
        u = k / teeth
        a = 0.0 if k in (0, teeth) else amp * (1.0 if k % 2 else -1.0) * rng.uniform(0.7, 1.0)
        pts.append((x0 + dx * u + nx * a, y0 + dy * u + ny * a))
    return pts


def _render_frame(anim: str, i: int, n: int):
    t = K.phase(i, n, anim in K.LOOPS)
    cyc = math.tau * t
    rng = random.Random(f"discord:{anim}:{i}")
    f = K.Frame(FRAME_SIZE)
    cx, cy = 44.0, 54.0
    lean, spread, bend, squash, fade, apart = 0.0, 0.0, 0.0, 0.0, 1.0, 0.0
    bob_a, bob_b = 0.0, 0.0
    look, eyes, buzz, alarm = "each", "sour", 0.6, False
    if anim == "idle":
        cy += 2.0 * math.sin(cyc)
        bob_a, bob_b = 1.6 * math.sin(cyc), 1.6 * math.sin(cyc + math.pi)
        buzz = 0.5 + 0.5 * abs(math.sin(cyc * 2.0))
    elif anim == "walk":
        cy += 1.5 * math.sin(cyc * 2.0)
        lean = 10.0
        bob_a, bob_b = 3.0 * math.sin(cyc), 3.0 * math.sin(cyc + math.pi)
        look, buzz = "front", 0.4
    elif anim == "notice":
        cy -= 7.0 * math.sin(math.pi * t)
        look, eyes, alarm, buzz = "front", "wide", True, 0.0
        spread = 2.0 * math.sin(math.pi * t)
    elif anim == "windup":
        lean, spread = -12.0, 6.0 + 0.8 * math.sin(cyc * 2.0)
        bend = -4.0
        cx -= 2.0
        look, eyes, buzz = "front", "angry", 1.0
        cy += 0.8 * math.sin(cyc * 4.0)
    elif anim == "attack_side":
        strike = math.sin(math.pi * min(1.0, t * 1.6))
        snap = min(1.0, t * 2.5)
        cx += 14.0 * strike
        lean = -12.0 + 30.0 * strike
        spread = 6.0 - 10.0 * snap
        bend = -4.0 + 6.0 * snap
        look, eyes, buzz = "front", "angry", 0.0
    elif anim == "hit":
        squash = 0.25 * math.sin(math.pi * t) + 0.1
        lean, bend, eyes, buzz = -16.0, 6.0, "x", 0.0
        cx -= 5.0 * math.sin(math.pi * t)
    elif anim == "death":
        apart, eyes, buzz = t, "x", 0.0
        fade = 1.0 - max(0.0, t - 0.55) / 0.45

    # The two notes: the back one is low (left), the front one a step higher.
    gap = 10.0 + spread
    heads = [(cx - gap, cy + 16.0 + bob_a), (cx + gap, cy + 12.0 + bob_b)]
    rx, ry = 10.5 * (1.0 + squash * 0.4), 8.0 * (1.0 - squash)
    stem_h = 34.0 * (1.0 - squash * 0.5)

    def place(points, k: int):
        """A note's points: turned and moved apart at its death, then the
        whole body leaned."""
        if apart:
            hx, hy = heads[k]
            side = -1.0 if k == 0 else 1.0
            points = K.turn(points, hx, hy, side * 50.0 * apart)
            points = [(x + side * 12.0 * apart, y + 26.0 * apart * apart) for x, y in points]
        return K.turn(points, cx, cy, lean)

    stems = []
    for k, (hx, hy) in enumerate(heads):
        sx = hx + rx * 0.82
        stems.append(((sx, hy - 2.0), (sx, hy - stem_h)))
    # The beam: thick, from one stem top to the other, bent by `bend`.
    (_, a_top), (_, b_top) = stems[0][1], stems[1][1]
    ax, bx = stems[0][1][0], stems[1][1][0]
    mid = ((ax + bx) / 2.0, (a_top + b_top) / 2.0 + bend)
    if apart:
        # The beam snaps in the middle: each note keeps its half.
        f.poly(place([(ax - 1.4, a_top), (mid[0] - 2.0, mid[1]), (mid[0] - 1.0, mid[1] + 6.0), (ax - 1.4, a_top + 6.0)], 0), EBONY)
        f.poly(place([(mid[0] + 1.0, mid[1] + 1.0), (bx + 1.4, b_top), (bx + 1.4, b_top + 6.0), (mid[0] + 2.0, mid[1] + 7.0)], 1), EBONY)
    else:
        beam = [(ax - 1.4, a_top), mid, (bx + 1.4, b_top), (bx + 1.4, b_top + 6.0), (mid[0], mid[1] + 6.0), (ax - 1.4, a_top + 6.0)]
        f.poly(K.turn(beam, cx, cy, lean), EBONY)
        f.ink(K.turn([(ax + 1.0, a_top + 1.4), mid, (bx - 1.0, b_top + 1.4)], cx, cy, lean), 0.9, EBONY_SHEEN)

    # The jagged sound between the heads: the two of them disagree.
    if buzz > 0.0 and not apart:
        (hx0, hy0), (hx1, hy1) = heads
        zig = K.turn(_zigzag(hx0 + rx * 0.2, hy0 - ry - 3.0, hx1 - rx * 0.3, hy1 - ry - 3.0, 6, 2.6 * buzz, rng), cx, cy, lean)
        f.glow_line(zig, 1.4, K.alpha(SOUND, 0.9))

    for k, (hx, hy) in enumerate(heads):
        (s0, s1) = stems[k]
        f.limb(place([s0, s1], k), 2.6, EBONY)
        tilt = -22.0 + (6.0 if k == 0 else -4.0) * (bob_a if k == 0 else bob_b) / 3.0
        head = K.turn(K.ellipse_points(hx, hy, rx, ry, 26), hx, hy, tilt)
        f.poly(place(head, k), EBONY)
        sheen = K.turn(K.ellipse_points(hx - rx * 0.35, hy - ry * 0.45, rx * 0.45, ry * 0.22, 14), hx, hy, tilt)
        f.poly(place(sheen, k), EBONY_SHEEN, body=False)

        # The face. Each looks at the other, until there is something to fight.
        if look == "each":
            pupil = 1.0 if k == 0 else -1.0
        else:
            pupil = 1.0
        for side in (-1.0, 1.0):
            ex, ey = hx + side * 3.8 + 0.8, hy - 1.0
            if eyes == "x":
                for d in (-1.0, 1.0):
                    f.ink(place([(ex - 1.8, ey - 1.8 * d), (ex + 1.8, ey + 1.8 * d)], k), 1.0, K.WHITE)
                continue
            big = 1.25 if eyes == "wide" else 1.0
            f.ellipse(*place([(ex, ey)], k)[0], 2.4 * big, 2.8 * big, K.WHITE, body=False)
            f.dot(*place([(ex + pupil * 0.9, ey + 0.3)], k)[0], 1.2 * big, K.INK)
            if eyes != "wide":
                # A low, sour brow: down toward the middle of the face.
                f.ink(place([(ex - side * 2.8, ey - 4.4 + (1.2 if eyes == "angry" else 0.4)), (ex + side * 2.0, ey - 2.4)], k), 1.1, SOUND_LIGHT)
        # The mouth: a wavy frown, wide open when it shouts.
        my = hy + 4.2
        if eyes in ("angry", "wide"):
            f.ellipse(*place([(hx + 0.8, my)], k)[0], 2.6, 1.6 if eyes == "wide" else 1.2, K.WHITE, body=False)
        else:
            f.ink(place([(hx - 3.0, my + 1.0), (hx - 1.4, my - 0.4), (hx + 0.4, my + 0.4), (hx + 2.2, my - 0.4), (hx + 3.6, my + 1.2)], k), 0.9, K.WHITE)

    if alarm:
        ax, ay = cx + 24.0, cy - 30.0
        f.limb(K.turn([(ax, ay - 8.0), (ax, ay)], cx, cy, lean), 2.4, SOUND)
        f.ellipse(*K.turn([(ax, ay + 4.5)], cx, cy, lean)[0], 1.6, 1.6, SOUND)
    if anim == "attack_side" and t > 0.25:
        # The clap: a burst of jagged sound in front of the two heads.
        burst = 1.0 - abs(t - 0.6) / 0.4
        bx0, by0 = K.turn([(heads[1][0] + 16.0, heads[1][1] - 4.0)], cx, cy, lean)[0]
        bx0 = min(bx0, 80.0)
        spikes = []
        for k in range(14):
            a = math.tau * k / 14.0
            r = (9.0 if k % 2 else 4.5) * (0.7 + 0.5 * burst)
            spikes.append((bx0 + math.cos(a) * r, by0 + math.sin(a) * r))
        spikes.append(spikes[0])
        f.glow_line(spikes, 1.6, K.alpha(SOUND, max(0.0, burst)))
        f.glow(bx0, by0, 4.0, K.alpha(K.MAGENTA_LIGHT, 0.8 * max(0.0, burst)))
    if anim == "hit":
        for k in range(3):
            y0 = cy - 6.0 + k * 9.0
            f.glow_line(_zigzag(cx - 26.0, y0, cx - 34.0, y0 + 4.0, 3, 1.4, rng), 1.2, K.alpha(SOUND, 0.8))
    if anim == "death":
        # A last sour sound that falls flat.
        a = 0.9 * (1.0 - t)
        f.glow_line(_zigzag(cx - 12.0, cy - 30.0 + 8.0 * t, cx + 12.0, cy - 30.0 + 14.0 * t, 5, 1.6 * (1.0 - t), rng), 1.2, K.alpha(SOUND, a))
    # The edge of the notes is a thin line of light, so a black note reads on
    # the night sky of the Reach.
    return f.finish(outline=(150, 156, 220, 255), width=1.1, glow_blur=1.8, fade=fade)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return K.render_target(TARGET_NAME, ROWS, _render_frame, FRAME_SIZE, ACTOR_METADATA, out_dir, **opts)


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}
