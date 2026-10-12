"""Sprite generator for Sanic's goal post: the sign at the end of an act.

A steel post on a foot, with a round sign on top. The sign has two sides: a
badnik's grin on violet until the act is cleared, and a gold star on Sanic's
blue after it. Rows: ``idle`` (the badnik side, a shine going across it),
``spin`` (the sign turns over two and a half times and stops on the star) and
``cleared`` (the star side, with sparkles).

The game stands one at the goal of each act and plays ``spin`` when the act
is cleared.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import List, Tuple

from PIL import Image

from ..characters._ai_era_kit import OUTLINE, WHITE, Kit, Point, RGBA, ease, mix

TARGET_NAME = "sanic_goal_post"
FRAME_SIZE = (96, 136)
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 4, 170),
    ("spin", 12, 55),
    ("cleared", 4, 150),
]

GROUND = 130.0
CX = 48.0
#: The middle of the sign above the ground, and its radius.
SIGN_UP, SIGN_R = 96.0, 24.0

STEEL: RGBA = (196, 204, 222, 255)
STEEL_DARK: RGBA = (120, 130, 160, 255)
GOLD: RGBA = (250, 206, 84, 255)
GOLD_DARK: RGBA = (196, 146, 50, 255)
VIOLET: RGBA = (150, 110, 232, 255)
PINK: RGBA = (255, 138, 190, 255)
BLUE: RGBA = (56, 112, 226, 255)
BLUE_LIGHT: RGBA = (120, 170, 255, 255)
INK: RGBA = (40, 26, 58, 255)
TOOTH: RGBA = (255, 252, 240, 255)

K = Kit(FRAME_SIZE)

ACTOR_METADATA = {
    "actor": {"character_id": "prop_sanic_goal_post", "display_name": "Sanic Goal Post"},
    "body": {"body_plan": "PropActor", "body_kind": "PropLike", "mass_class": "Light", "traits": ["prop", "sanic"], "locomotion_hint": "Static"},
    "visual": {"default_pose": "idle"},
    "tags": ["prop", "sanic", "goal"],
    "animation_bindings": {"default": {"animation": "idle", "events": []}},
    "authoring_description": "The sign at the end of a Sanic act: a badnik's grin until the act is cleared, a gold star after.",
    "gameplay_description": "Scenery. The game plays its spin when the act is cleared.",
}


def _post():
    """The foot and the pole, from the ground under them at ``home``."""
    h = K.home

    def shape(d) -> None:
        K.poly(d, [K.at(-17.0, 0.0), K.at(17.0, 0.0), K.at(12.0, -9.0), K.at(-12.0, -9.0)], WHITE)
        K.stroke(d, [K.at(0.0, -8.0), K.at(0.0, -SIGN_UP + SIGN_R - 2.0)], WHITE, 6.5)

    def detail(d) -> None:
        K.line(d, [K.at(-1.4, -12.0), K.at(-1.4, -SIGN_UP + SIGN_R)], WHITE, 1.3)
        for y in (-22.0, -44.0, -66.0):
            K.rrect(d, h[0] - 4.0, h[1] + y, h[0] + 4.0, h[1] + y + 4.0, 0.0, BLUE)
        for x in (-11.0, 11.0):
            K.oval(d, K.at(x, -3.4), 1.6, 1.6, STEEL_DARK)

    return K.solid(("post",), shape, STEEL, detail, shade_colour=STEEL_DARK, shade=0.7)


def _star(d, c: Point, r: float, squeeze: float, fill: RGBA) -> None:
    pts = []
    for i in range(10):
        a = math.radians(i * 36.0 - 90.0)
        rr = r if i % 2 == 0 else r * 0.44
        pts.append((c[0] + math.cos(a) * rr * squeeze, c[1] + math.sin(a) * rr))
    K.poly(d, pts, fill, OUTLINE, 1.0)


def _sign(turn: float, shine: float):
    """The sign, its middle at ``home``, turned ``turn`` radians about the
    post: at 0 the badnik side faces us, at pi the star side."""
    across = math.cos(turn)
    squeeze = round(abs(across), 3)
    star_side = across < 0.0
    shine = round(shine, 2)
    h = K.home

    def shape(d) -> None:
        if squeeze < 0.12:
            # Edge on: the rim of it.
            K.stroke(d, [K.at(0.0, -SIGN_R), K.at(0.0, SIGN_R)], WHITE, 4.6)
        else:
            K.oval(d, h, SIGN_R * squeeze, SIGN_R, WHITE)

    def detail(d) -> None:
        if squeeze < 0.12:
            return

        def P(x: float, y: float) -> Point:
            return K.at(x * squeeze, y)

        K.oval(d, h, (SIGN_R - 3.6) * squeeze, SIGN_R - 3.6, BLUE if star_side else VIOLET)
        if star_side:
            K.oval(d, P(-6.0, -8.0), 9.0 * squeeze, 5.0, BLUE_LIGHT)
            _star(d, K.at(0.0, 0.5), 13.5, squeeze, GOLD)
            _star(d, K.at(-1.2 * squeeze, -0.6), 6.0, squeeze, (255, 240, 170, 255))
        else:
            # A badnik's face: two eyes that do not match, and too many teeth.
            K.poly(d, [P(-17.0, 6.0), P(17.0, 6.0), P(13.0, 17.0), P(-13.0, 17.0)], PINK)
            for x, rx, ry in ((-7.0, 4.6, 5.8), (6.5, 6.0, 7.4)):
                K.oval(d, P(x, -5.0), rx * squeeze, ry, WHITE, INK, 0.9)
                K.oval(d, P(x + 1.2, -4.4), rx * 0.5 * squeeze, ry * 0.5, INK)
            grin = [P(-11.0, 6.0), P(-6.0, 11.0), P(0.0, 12.4), P(6.0, 11.0), P(11.0, 6.0)]
            K.poly(d, grin, TOOTH, INK, 1.0)
            for x in (-7.0, -3.5, 0.0, 3.5, 7.0):
                K.line(d, [P(x, 6.4), P(x, 11.0)], INK, 0.5)
            K.line(d, [P(-11.0, 6.0), P(11.0, 6.0)], INK, 1.0)
        if shine > 0.0:
            x = -SIGN_R + 2.0 * SIGN_R * shine
            K.poly(d, [P(x - 5.0, -SIGN_R), P(x + 1.0, -SIGN_R), P(x - 7.0, SIGN_R), P(x - 13.0, SIGN_R)], (255, 255, 255, 96))

    return K.solid(("sign", squeeze, star_side, shine), shape, GOLD, detail, shade_colour=GOLD_DARK, shade=0.7, rim=0.5)


def _sparkle(r: float):
    def paint(d) -> None:
        K.star4(d, K.home, r, (255, 240, 160, 255))
        K.star4(d, K.home, r * 0.46, (255, 255, 240, 255), None, 0.0, 0.4)

    return K.piece(("sparkle", r), paint)


def _render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    img = K.new_frame()
    base = (CX, GROUND)
    sign = (CX, GROUND - SIGN_UP)
    K.place(img, _post(), base, "post")
    if anim == "idle":
        K.place(img, _sign(0.0, (0.0, 0.3, 0.62, 0.94)[frame_idx % 4]), sign, "sign")
    elif anim == "spin":
        # Two and a half turns, and it slows to a stop on the star.
        turn = math.pi * 5.0 * ease(frame_idx / max(1, nframes - 1))
        K.place(img, _sign(turn, 0.0), sign, "sign")
    else:
        K.place(img, _sign(math.pi, 0.0), (sign[0], sign[1] - (0.0, 1.0, 0.0, -1.0)[frame_idx % 4]), "sign")
        for k, (x, y, r) in enumerate(((-30.0, -22.0, 6.0), (30.0, -14.0, 5.0), (22.0, 26.0, 4.0), (-26.0, 22.0, 4.5))):
            size = r * (0.55 + 0.45 * math.sin(math.tau * (frame_idx + k) / 4.0) ** 2)
            K.place(img, _sparkle(round(size * 2.0) / 2.0), (sign[0] + x, sign[1] + y), f"sparkle_{k}")
    return K.downsample(img)


#: The body of the prop: the post and the sign.
BODY_BOX = (CX - SIGN_R, GROUND - SIGN_UP - SIGN_R, CX + SIGN_R, GROUND + 1.0)


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    return K.render(TARGET_NAME, ROWS, _render_frame, out_dir, ACTOR_METADATA, BODY_BOX)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render Sanic's goal post.")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[2] / "generated" / TARGET_NAME)
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


if __name__ == "__main__":
    raise SystemExit(main())
