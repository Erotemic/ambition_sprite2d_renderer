"""Sprite generator for the Helpful Liar: a cheerful assistant whose nose grows.

The look (redrawn 2026-10-11): a help-desk robot on one wheel, white and
blue, with a screen for a face, a headset, and a "verified" badge on its
chest. It has a wooden nose that is longer each time it speaks. One hand is
raised to explain; the other is behind its back with two fingers crossed. It
faces right.

It rolls on its wheel. Its shot is its nose: it leans back, says something
with a tick beside it, and the nose shoots out. Struck, the badge turns to a
red cross and the nose droops. Dead, it falls on its back, the screen shows a
flat line, the wheel still turns, and the nose is short at last.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image

from ._ai_era_kit import OUTLINE, WHITE, Kit, Point, RGBA, actor_metadata, ease, mix, turned

TARGET_NAME = "helpful_liar"
FRAME_SIZE = (208, 192)
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 130),
    ("walk", 8, 90),
    ("shoot", 6, 85),
    ("hurt", 4, 90),
    ("death", 8, 110),
]

GROUND = 180.0
CX = 92.0
WHEEL = 13.0

SHELL: RGBA = (238, 244, 255, 255)
SHELL_DARK: RGBA = (196, 208, 236, 255)
BLUE: RGBA = (72, 132, 255, 255)
BLUE_DARK: RGBA = (44, 86, 200, 255)
SCREEN: RGBA = (26, 32, 72, 255)
GLOW: RGBA = (120, 236, 255, 255)
WOOD: RGBA = (222, 168, 104, 255)
WOOD_DARK: RGBA = (168, 112, 66, 255)
LEAF: RGBA = (96, 190, 110, 255)
GREEN: RGBA = (84, 206, 124, 255)
RED: RGBA = (240, 78, 92, 255)
DARK: RGBA = (62, 62, 92, 255)
TYRE: RGBA = (50, 44, 68, 255)
STEEL: RGBA = (172, 180, 204, 255)
INK: RGBA = (40, 30, 60, 255)

K = Kit(FRAME_SIZE)

ACTOR_METADATA = actor_metadata(
    "npc_helpful_liar",
    "Helpful Liar",
    attack_row="shoot",
    ranged=True,
    traits=["ai_era", "assistant", "unreliable", "enemy"],
    description=(
        "The Helpful Liar is a help-desk robot on one wheel with a screen for a face, a 'verified' badge "
        "and a wooden nose that grows when it speaks. It keeps two fingers crossed behind its back."
    ),
    gameplay="A ranged enemy that rolls on its wheel and shoots its nose.",
)

UPPER, FORE = 14.0, 14.0


def _aim(angle: float) -> Point:
    """The direction of a limb: 0 hangs down, 90 points forward, 180 up."""
    a = math.radians(angle)
    return (math.sin(a), math.cos(a))


# ---- The pose ----------------------------------------------------------------


def _pose(anim: str, i: int, n: int) -> Dict[str, object]:
    ph = math.tau * i / max(1, n)
    pose: Dict[str, object] = {
        "x": 0.0,
        "lift": 0.0,
        "tilt": 0.0,
        "head": 0.0,
        "spin": 0.0,
        "nose": 11.0,
        "droop": 0.0,
        "face": "smile",
        "badge": "tick",
        "front_arm": (80.0, 130.0),
        "back_arm": (-22.0, -72.0),
        "bubble": None,
        "lines": 0.0,
    }
    if anim == "idle":
        sway = math.sin(ph)
        pose.update(
            x=1.5 * sway,
            tilt=2.2 * sway,
            head=-1.5 * sway,
            spin=10.0 * sway,
            # Each thing it says is a little longer on its nose.
            nose=(11.0, 12.0, 14.5, 17.0, 19.0, 13.0)[i % 6],
            face=("smile", "smile", "happy", "shifty", "shifty", "smile")[i % 6],
            front_arm=(80.0 + 4.0 * sway, 130.0 + 14.0 * math.sin(ph * 2.0)),
            bubble=(None, "tick", "tick", "tick", None, None)[i % 6],
        )
    elif anim == "walk":
        pose.update(
            tilt=7.0 + 1.5 * math.sin(ph * 2.0),
            lift=0.8 * abs(math.sin(ph * 2.0)),
            head=-3.0,
            spin=45.0 * i,
            nose=12.0,
            face="happy" if i % 4 == 3 else "smile",
            front_arm=(84.0 + 6.0 * math.sin(ph), 100.0 + 8.0 * math.sin(ph + 0.6)),
            back_arm=(-22.0 + 4.0 * math.sin(ph), -72.0),
        )
    elif anim == "shoot":
        keys = [
            # x, tilt, nose, face, front arm, bubble, lines
            (-2.0, -6.0, 9.0, "happy", (70.0, 125.0), None, 0.0),
            (-4.0, -11.0, 8.0, "happy", (64.0, 140.0), "tick", 0.0),
            (3.0, 6.0, 40.0, "smile", (96.0, 92.0), "tick", 0.6),
            (5.0, 9.0, 58.0, "smile", (92.0, 90.0), "tick", 1.0),
            (3.0, 4.0, 34.0, "shifty", (100.0, 120.0), None, 0.3),
            (0.0, 0.0, 15.0, "shifty", (84.0, 124.0), None, 0.0),
        ]
        x, tilt, nose, face, front, bubble, lines = keys[i % len(keys)]
        pose.update(x=x, tilt=tilt, nose=nose, face=face, front_arm=front, bubble=bubble, lines=lines, spin=-x * 8.0)
    elif anim == "hurt":
        pose.update(
            x=(-5.0, -9.0, -6.0, -2.0)[i % 4],
            tilt=(-13.0, -17.0, -10.0, -3.0)[i % 4],
            head=(-6.0, -4.0, -2.0, 0.0)[i % 4],
            spin=(-40.0, -90.0, -120.0, -130.0)[i % 4],
            nose=(16.0, 15.0, 13.0, 12.0)[i % 4],
            droop=(34.0, 44.0, 26.0, 8.0)[i % 4],
            face="hurt" if i < 3 else "shifty",
            badge="cross",
            front_arm=((100.0, 60.0), (110.0, 40.0), (96.0, 80.0), (84.0, 118.0))[i % 4],
            back_arm=((-110.0, -150.0), (-126.0, -160.0), (-80.0, -120.0), (-34.0, -84.0))[i % 4],
            bubble=("cross", "cross", None, None)[i % 4],
        )
    elif anim == "death":
        fall = ease(i / max(1, n - 1) * 1.3)
        pose.update(
            x=56.0 * fall,
            lift=23.0 * fall,
            tilt=-90.0 * fall,
            head=-4.0 * fall,
            # The wheel still turns.
            spin=-60.0 * i,
            nose=max(3.0, 14.0 - 2.0 * i),
            droop=-20.0 * fall,
            face=("hurt", "hurt", "dead", "dead", "dead", "flat", "flat", "off")[i % 8],
            badge="cross",
            front_arm=(80.0, 130.0 - 44.0 * fall),
            back_arm=(-22.0 + 44.0 * fall, -72.0 + 84.0 * fall),
        )
    return pose


# ---- Pieces ------------------------------------------------------------------


def _tyre():
    h = K.home

    def shape(d) -> None:
        K.oval(d, h, WHEEL, WHEEL, WHITE)

    def detail(d) -> None:
        K.oval(d, h, WHEEL - 4.0, WHEEL - 4.0, STEEL)

    return K.solid(("tyre",), shape, TYRE, detail, shade=0.0, rim=0.25)


def _spokes():
    def paint(d) -> None:
        for k in range(3):
            a = math.radians(k * 60.0)
            K.line(d, [K.at(-8.5 * math.cos(a), -8.5 * math.sin(a)), K.at(8.5 * math.cos(a), 8.5 * math.sin(a))], DARK, 1.6)
        K.oval(d, K.home, 3.2, 3.2, BLUE, OUTLINE, 0.8)

    return K.piece(("spokes",), paint)


def _strut():
    def shape(d) -> None:
        K.stroke(d, [K.at(0.0, -2.0), K.at(0.0, -26.0)], WHITE, 7.0)

    return K.solid(("strut",), shape, STEEL)


def _torso(badge: str):
    """The body, its middle at ``home``, with its badge."""
    h = K.home

    def shape(d) -> None:
        K.poly(d, [K.at(-17.0, -20.0), K.at(17.0, -20.0), K.at(21.0, 6.0), K.at(13.0, 21.0), K.at(-13.0, 21.0), K.at(-21.0, 6.0)], WHITE)
        K.oval(d, K.at(0.0, -16.0), 18.0, 10.0, WHITE)
        K.oval(d, K.at(0.0, 12.0), 17.0, 10.0, WHITE)

    def detail(d) -> None:
        K.rrect(d, h[0] - 24.0, h[1] + 10.0, h[0] + 24.0, h[1] + 24.0, 0.0, BLUE)
        K.line(d, [K.at(-22.0, 10.0), K.at(22.0, 10.0)], BLUE_DARK, 1.0)
        # The badge: a seal with scallops round it.
        c = K.at(6.0, -6.0)
        colour = BLUE if badge == "tick" else RED
        for k in range(10):
            a = math.tau * k / 10
            K.oval(d, (c[0] + 7.6 * math.cos(a), c[1] + 7.6 * math.sin(a)), 2.9, 2.9, OUTLINE)
        K.oval(d, c, 8.4, 8.4, OUTLINE)
        for k in range(10):
            a = math.tau * k / 10
            K.oval(d, (c[0] + 7.6 * math.cos(a), c[1] + 7.6 * math.sin(a)), 2.0, 2.0, colour)
        K.oval(d, c, 7.6, 7.6, colour)
        if badge == "tick":
            K.tick(d, (c[0] - 0.4, c[1] + 0.6), 4.0, WHITE, 2.0)
        else:
            K.cross(d, c, 3.4, WHITE, 2.0)

    return K.solid(("torso", badge), shape, SHELL, detail)


def _head(face: str):
    """The head, its middle at ``home``: a screen with a face on it."""
    h = K.home

    def shape(d) -> None:
        K.rrect(d, h[0] - 32.0, h[1] - 26.0, h[0] + 32.0, h[1] + 26.0, 19.0, WHITE)

    def detail(d) -> None:
        K.rrect(d, h[0] - 19.0, h[1] - 17.0, h[0] + 27.0, h[1] + 17.0, 12.0, SCREEN, OUTLINE, 1.0)
        K.line(d, [K.at(-12.0, -13.5), K.at(8.0, -13.5)], (70, 84, 150, 255), 1.2)
        if face == "off":
            K.oval(d, K.at(4.0, 0.0), 1.4, 1.4, mix(SCREEN, GLOW, 0.5))
            return
        if face == "flat":
            K.line(d, [K.at(-13.0, 0.0), K.at(21.0, 0.0)], GLOW, 1.6)
            return
        for x in (-6.0, 15.0):
            eye = K.at(x, -4.0)
            if face == "happy":
                K.stroke(d, [(eye[0] - 4.2, eye[1] + 1.8), (eye[0], eye[1] - 2.8), (eye[0] + 4.2, eye[1] + 1.8)], GLOW, 2.0)
            elif face == "hurt":
                sign = 1.0 if x < 0 else -1.0
                K.stroke(d, [(eye[0] - 3.6 * sign, eye[1] - 3.4), (eye[0] + 3.2 * sign, eye[1]), (eye[0] - 3.6 * sign, eye[1] + 3.4)], GLOW, 2.0)
            elif face == "dead":
                K.cross(d, eye, 3.2, GLOW, 1.9)
            else:
                K.oval(d, eye, 4.2, 5.2, GLOW)
                # Shifty: it looks behind it.
                shift = -1.8 if face == "shifty" else 1.2
                K.oval(d, (eye[0] + shift, eye[1] + 0.4), 1.9, 2.5, SCREEN)
        if face in ("hurt", "dead"):
            K.stroke(d, [K.at(-4.0, 9.0), K.at(0.0, 7.0), K.at(4.0, 9.0), K.at(8.0, 7.0), K.at(12.0, 9.0)], GLOW, 1.6)
        else:
            K.stroke(d, [K.at(-5.0, 6.0), K.at(-1.0, 10.0), K.at(5.0, 11.0), K.at(11.0, 10.0), K.at(15.0, 6.0)], GLOW, 1.9)

    return K.solid(("head", face), shape, SHELL, detail)


def _headset():
    """The headset, placed on the middle of the head."""

    def paint(d) -> None:
        band = [K.at(-30.0, -4.0), K.at(-29.0, -18.0), K.at(-20.0, -27.5), K.at(-4.0, -29.5)]
        K.line(d, band, OUTLINE, 5.6)
        K.line(d, band, DARK, 3.2)
        K.oval(d, K.at(-30.0, 2.0), 7.5, 10.0, DARK, OUTLINE, 1.1)
        K.oval(d, K.at(-30.5, 2.0), 3.2, 5.0, BLUE)
        boom = [K.at(-28.0, 10.0), K.at(-22.0, 24.0), K.at(-8.0, 29.0), K.at(6.0, 27.0)]
        K.line(d, boom, OUTLINE, 3.4)
        K.line(d, boom, DARK, 1.6)
        K.oval(d, K.at(7.0, 27.0), 3.4, 2.8, DARK, OUTLINE, 0.9)

    return K.piece(("headset",), paint)


def _nose(length: float):
    """The nose, from its root at ``home`` along +x."""
    length = round(length * 2.0) / 2.0
    h = K.home

    def shape(d) -> None:
        K.stroke(d, [h, K.at(length, 0.0)], WHITE, 7.0)
        if length > 30.0:
            K.stroke(d, [K.at(length * 0.62, 0.0), K.at(length * 0.62 + 5.0, -7.5)], WHITE, 2.4)
            K.oval(d, K.at(length * 0.62 + 8.0, -10.0), 4.6, 2.8, WHITE)

    def detail(d) -> None:
        for x in range(6, int(length), 7):
            K.line(d, [K.at(x, -3.4), K.at(x + 1.5, 3.4)], WOOD_DARK, 0.7)
        K.oval(d, K.at(length + 0.5, -0.5), 3.0, 3.0, mix(WOOD, WHITE, 0.45))
        if length > 30.0:
            K.oval(d, K.at(length * 0.62 + 8.0, -10.0), 4.6, 2.8, LEAF)

    return K.solid(("nose", length), shape, WOOD, detail, shade_colour=WOOD_DARK, shade=0.55)


def _limb(length: float, width: float, cuff: bool):
    h = K.home

    def shape(d) -> None:
        K.stroke(d, [h, K.at(0.0, length)], WHITE, width)

    def detail(d) -> None:
        if cuff:
            K.rrect(d, h[0] - width, h[1] + length - 3.5, h[0] + width, h[1] + length + width, 0.0, BLUE)

    return K.solid(("limb", length, width, cuff), shape, SHELL, detail)


def _hand(kind: str):
    """A hand from its wrist at ``home`` down: ``point`` holds one finger out,
    ``crossed`` has two fingers crossed."""

    def shape(d) -> None:
        K.oval(d, K.at(0.0, 4.0), 6.0, 6.2, WHITE)
        if kind == "point":
            K.stroke(d, [K.at(1.0, 6.0), K.at(1.5, 18.0)], WHITE, 4.0)
            K.oval(d, K.at(5.0, 2.0), 3.0, 3.6, WHITE)
        else:
            K.stroke(d, [K.at(-2.6, 7.0), K.at(3.8, 22.0)], WHITE, 4.0)
            K.stroke(d, [K.at(3.0, 7.0), K.at(-3.4, 22.0)], WHITE, 4.0)

    def detail(d) -> None:
        if kind == "crossed":
            K.line(d, [K.at(4.4, 8.0), K.at(-1.8, 22.0)], SHELL_DARK, 0.9)

    return K.solid(("hand", kind), shape, SHELL, detail)


def _bubble(kind: str):
    """What it says, with what it says it is."""

    def shape(d) -> None:
        K.rrect(d, K.home[0] - 14.0, K.home[1] - 12.0, K.home[0] + 14.0, K.home[1] + 10.0, 7.0, WHITE)
        K.poly(d, [K.at(-8.0, 8.0), K.at(-13.0, 18.0), K.at(-1.0, 9.0)], WHITE)

    def detail(d) -> None:
        if kind == "tick":
            K.tick(d, K.at(0.0, -0.5), 6.0, GREEN, 3.0)
        else:
            K.cross(d, K.at(0.0, -1.0), 5.0, RED, 3.0)

    return K.solid(("bubble", kind), shape, WHITE, detail, rim=0.0, shade=0.2, shade_colour=(150, 160, 210, 255))


def _lines(strength: float):
    """The lines of speed round the nose when it shoots, from ``home`` along +x."""
    strength = round(strength, 1)

    def paint(d) -> None:
        for y, start, length in ((-9.0, 4.0, 22.0), (9.5, 0.0, 26.0), (-15.0, 16.0, 14.0)):
            K.stroke(d, [K.at(start, y), K.at(start + length * strength, y)], (255, 255, 255, 190), 1.6)

    return K.piece(("lines", strength), paint)


# ---- Frames ------------------------------------------------------------------


def _render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    pose = _pose(anim, frame_idx, nframes)
    img = K.new_frame()
    tilt = float(pose["tilt"])
    hub = (CX + float(pose["x"]), GROUND - WHEEL - float(pose["lift"]))

    def body(x: float, y: float) -> Point:
        """A point of it (from the hub of its wheel, up is negative) in the frame."""
        p = turned((x, y), tilt)
        return (hub[0] + p[0], hub[1] + p[1])

    def put_arm(shoulder: Point, angles: Tuple[float, float], hand: str, name: str) -> None:
        elbow = (shoulder[0] + _aim(angles[0])[0] * UPPER, shoulder[1] + _aim(angles[0])[1] * UPPER)
        wrist = (elbow[0] + _aim(angles[1])[0] * FORE, elbow[1] + _aim(angles[1])[1] * FORE)
        K.place(img, _limb(UPPER, 9.0, False), body(*shoulder), f"{name}_upper", tilt - angles[0])
        K.place(img, _limb(FORE, 8.0, True), body(*elbow), f"{name}_fore", tilt - angles[1])
        K.place(img, _hand(hand), body(*wrist), f"{name}_hand", tilt - angles[1])

    put_arm((-13.0, -58.0), pose["back_arm"], "crossed", "back")  # type: ignore[arg-type]
    K.place(img, _strut(), hub, "strut", tilt)
    K.place(img, _tyre(), hub, "tyre")
    K.place(img, _spokes(), hub, "spokes", float(pose["spin"]))
    K.place(img, _torso(str(pose["badge"])), body(0.0, -46.0), "torso", tilt)

    head_turn = tilt + float(pose["head"])
    head = body(3.0, -96.0)

    def on_head(x: float, y: float) -> Point:
        p = turned((x, y), head_turn)
        return (head[0] + p[0], head[1] + p[1])

    K.place(img, _head(str(pose["face"])), head, "head", head_turn)
    K.place(img, _headset(), head, "headset", head_turn)
    nose_turn = head_turn + float(pose["droop"])
    if float(pose["lines"]) > 0.05:
        K.place(img, _lines(float(pose["lines"])), on_head(22.0, 2.0), "lines", head_turn)
    K.place(img, _nose(float(pose["nose"])), on_head(9.0, 2.0), "nose", nose_turn)
    put_arm((12.0, -60.0), pose["front_arm"], "point", "front")  # type: ignore[arg-type]
    if pose["bubble"] is not None:
        K.place(img, _bubble(str(pose["bubble"])), on_head(44.0, -40.0), "bubble")
    return K.downsample(img)


#: The gameplay body: it as it stands, without its nose and its raised hand.
BODY_BOX = (CX - 30.0, GROUND - 137.0, CX + 36.0, GROUND + 1.0)


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    return K.render(TARGET_NAME, ROWS, _render_frame, out_dir, ACTOR_METADATA, BODY_BOX)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render the Helpful Liar sprite target.")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[2] / "generated" / TARGET_NAME)
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


if __name__ == "__main__":
    raise SystemExit(main())
