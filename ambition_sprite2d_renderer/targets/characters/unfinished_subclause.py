"""Subclauses: small instances of Clause, the Boss's Analyst, at work on the
Unfinished dimension (gate address INSTALLING,
`docs/planning/game/unfinished-dimension.md`).

A subclause is Clause made small (`docs/planning/game/final-boss.md` draws
the family: a dark visor with two glowing eyes and round earpieces, a crown
of orange petal fins round the back of the head, a cream poncho cut on a
slant with orange edges and a starburst on the breast, over a dark
chassis), dressed for the site: a yellow hard hat over the fins and a vest
with a reflective band.

Two of them, one drawing each: Subclause 4(b), the surveyor, who holds the
spec on a clipboard; Subclause 4(c), the painter, who holds a roller on a
long pole, wet with sky.

Rows: ``idle`` (a breath, the eyes blink), ``talk`` (the eyes change shape,
a hand lifts), ``hit`` (a flinch) and ``death`` (it sits down and the eyes
go out).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

from . import _art_cast_kit as K
from . import _picture_palace_kit as M

FRAME_SIZE = (96, 128)
ROWS: List[Tuple[str, int, int]] = [("idle", 8, 150), ("talk", 6, 110), ("hit", 3, 90), ("death", 8, 160)]
LOOPS = {"idle", "talk"}

CHASSIS = (46, 44, 54, 255)
CHASSIS_LIGHT = (90, 88, 104, 255)
VISOR = (24, 22, 30, 255)
EYE = (255, 160, 70, 255)
CREAM = (232, 222, 200, 255)
ORANGE = (226, 120, 60, 255)
HAT = (232, 190, 70, 255)
HAT_DARK = (180, 140, 40, 255)
VEST = (214, 150, 60, 255)
BAND = (210, 214, 220, 255)
PAPER = (240, 236, 224, 255)
BOARD = (150, 110, 70, 255)
SKY = (150, 180, 214, 255)
POLE = (120, 124, 136, 255)


def _frame(tool: str):
    def render_frame(anim: str, i: int, n: int):
        t = K.phase(i, n, anim in LOOPS)
        cyc = math.tau * t
        f = K.Frame(FRAME_SIZE)
        foot = 122.0
        cx = 46.0
        bob, tilt, eyes, sit = 0.0, 0.0, 1.0, 0.0
        if anim == "idle":
            bob = 0.8 * math.sin(cyc)
            if i == 5:
                eyes = 0.2
        elif anim == "talk":
            bob = 0.6 * math.sin(cyc * 2.0)
        elif anim == "hit":
            tilt = -8.0
            eyes = 0.4
        elif anim == "death":
            sit = min(1.0, t * 1.6)
            tilt = 10.0 * sit
            eyes = max(0.0, 1.0 - t * 1.4)
        top = 40.0 + bob + 22.0 * sit
        # The legs and the boots.
        for dx in (-7.0, 7.0):
            knee = (cx + dx, foot - 20.0 + 10.0 * sit)
            f.limb([(cx + dx * 0.8, top + 52.0), knee, (cx + dx + (8.0 * sit if dx > 0 else 0.0), foot - 4.0)], 6.0, CHASSIS)
            f.poly([(cx + dx - 5.0, foot - 6.0), (cx + dx + 7.0, foot - 6.0), (cx + dx + 8.0, foot), (cx + dx - 5.0, foot)], CREAM)
        body = [(cx - 14.0, top + 24.0), (cx + 14.0, top + 24.0), (cx + 12.0, top + 56.0), (cx - 12.0, top + 56.0)]
        f.poly(K.turn(body, cx, top + 40.0, tilt), CHASSIS)
        # The poncho, cut on a slant, its orange edge; the starburst.
        poncho = [(cx - 17.0, top + 26.0), (cx + 17.0, top + 26.0), (cx + 19.0, top + 46.0), (cx - 15.0, top + 54.0)]
        f.poly(K.turn(poncho, cx, top + 40.0, tilt), CREAM)
        f.ink(K.turn([(cx + 19.0, top + 46.0), (cx - 15.0, top + 54.0)], cx, top + 40.0, tilt), 2.4, ORANGE)
        # The vest over it, its reflective band.
        vest = [(cx - 12.0, top + 26.0), (cx + 12.0, top + 26.0), (cx + 11.0, top + 44.0), (cx - 11.0, top + 46.0)]
        f.poly(K.turn(vest, cx, top + 40.0, tilt), VEST)
        f.ink(K.turn([(cx - 11.0, top + 38.0), (cx + 11.0, top + 37.0)], cx, top + 40.0, tilt), 2.2, BAND)
        sx, sy = K.turn([(cx + 5.0, top + 31.0)], cx, top + 40.0, tilt)[0]
        for k in range(6):
            a = math.tau * k / 6.0
            f.ink([(sx, sy), (sx + 3.0 * math.cos(a), sy + 3.0 * math.sin(a))], 1.0, ORANGE)
        # The arm and the tool.
        shoulder = K.turn([(cx + 10.0, top + 28.0)], cx, top + 40.0, tilt)[0]
        lift = 6.0 * math.sin(cyc * 2.0) if anim == "talk" else 0.0
        if tool == "clipboard":
            hand = (shoulder[0] + 10.0, shoulder[1] + 14.0 - lift)
            f.limb([shoulder, (shoulder[0] + 8.0, shoulder[1] + 8.0), hand], 4.5, CHASSIS)
            board = [(hand[0] - 2.0, hand[1] - 14.0), (hand[0] + 12.0, hand[1] - 12.0), (hand[0] + 10.0, hand[1] + 6.0), (hand[0] - 4.0, hand[1] + 4.0)]
            f.poly(board, BOARD, body=False)
            f.poly(K.grow(board, -1.6), PAPER, body=False)
            for k in range(3):
                y = hand[1] - 8.0 + k * 4.0
                f.ink([(hand[0] + 0.0, y), (hand[0] + 8.0, y + 0.6)], 0.8, CHASSIS_LIGHT)
        else:
            hand = (shoulder[0] + 6.0, shoulder[1] + 6.0 - lift)
            f.limb([shoulder, hand], 4.5, CHASSIS)
            tip = (hand[0] + 18.0, hand[1] - 70.0 - lift)
            f.limb([(hand[0] - 4.0, hand[1] + 12.0), tip], 2.2, POLE, body=False)
            roller = [(tip[0] - 12.0, tip[1] - 5.0), (tip[0] + 12.0, tip[1] - 9.0), (tip[0] + 13.0, tip[1] - 1.0), (tip[0] - 11.0, tip[1] + 3.0)]
            f.poly(roller, SKY, body=False)
            f.dot(tip[0] + 6.0, tip[1] + 6.0, 1.4, SKY)
        # The head: the visor, the earpieces, the eyes, the fins, the hat.
        hx, hy = K.turn([(cx + 1.0, top + 12.0)], cx, top + 40.0, tilt)[0]
        for k in range(5):
            a = math.radians(150.0 + k * 22.0)
            f.poly([(hx - 4.0, hy - 2.0), (hx - 4.0 + 15.0 * math.cos(a - 0.15), hy + 15.0 * math.sin(a - 0.15)),
                    (hx - 4.0 + 17.0 * math.cos(a), hy + 17.0 * math.sin(a)), (hx - 4.0 + 15.0 * math.cos(a + 0.15), hy + 15.0 * math.sin(a + 0.15))], ORANGE)
        f.ellipse(hx, hy, 13.0, 12.0, CHASSIS)
        f.ellipse(hx + 2.0, hy + 1.0, 10.5, 8.5, VISOR, body=False)
        f.ellipse(hx - 11.0, hy + 2.0, 3.6, 4.4, CREAM)
        if eyes > 0.0:
            shape = 2.2 if anim != "talk" else 2.2 + 1.0 * abs(math.sin(cyc * 2.0))
            for ex in (hx - 1.0, hx + 7.0):
                f.ellipse(ex, hy + 1.0, 1.8, shape * eyes, EYE, body=False)
                f.glow(ex, hy + 1.0, 4.0, K.alpha(EYE, 0.5 * eyes))
        f.poly([(hx - 13.0, hy - 6.0), (hx + 15.0, hy - 6.0), (hx + 18.0, hy - 3.0), (hx - 14.0, hy - 3.0)], HAT_DARK)
        f.poly([(hx - 10.0, hy - 6.0), (hx - 8.0, hy - 14.0), (hx + 1.0, hy - 18.0), (hx + 10.0, hy - 14.0), (hx + 12.0, hy - 6.0)], HAT)
        f.ink([(hx + 1.0, hy - 18.0), (hx + 1.0, hy - 6.0)], 1.2, HAT_DARK)
        return f.finish(outline=K.shade(CHASSIS, 0.6), width=1.4, glow_blur=2.0)

    return render_frame


def _target(name: str, character_id: str, display_name: str, tool: str, description: str) -> dict:
    metadata = M.machine_metadata(character_id, display_name, "Biped", "Small", ["agent", "subclause", "hard_hat", tool], description, walks=False)
    metadata["tags"] = ["townsfolk", "unfinished", "peaceful", "agent"]
    frame = _frame(tool)

    def render(out_dir: str | Path, **opts) -> List[Path]:
        return K.render_target(name, ROWS, frame, FRAME_SIZE, metadata, out_dir, **opts)

    return {"render": render, "actor_metadata": metadata}


TARGETS = {
    "unfinished_subclause_surveyor": _target(
        "unfinished_subclause_surveyor", "npc_unfinished_subclause_surveyor", "Subclause 4(b)", "clipboard",
        "A subclause, a small instance of Clause, surveying the Unfinished dimension: a dark visor with two orange eyes, "
        "orange fins under a yellow hard hat, a cream poncho with orange edges under a work vest, and the spec on a clipboard.",
    ),
    "unfinished_subclause_painter": _target(
        "unfinished_subclause_painter", "npc_unfinished_subclause_painter", "Subclause 4(c)", "roller",
        "A subclause, a small instance of Clause, painting the sky of the Unfinished dimension: a dark visor with two "
        "orange eyes, orange fins under a yellow hard hat, a cream poncho with orange edges under a work vest, and a "
        "roller on a long pole, wet with sky.",
    ),
}
