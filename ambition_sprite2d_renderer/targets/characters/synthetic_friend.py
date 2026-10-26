"""Sprite generator for the Synthetic Friend: a companion mascot whose smile
is a plate screwed to its face.

The look (redrawn 2026-10-11): a round, soft toy of a robot in cream and
coral, a heart on its chest and one on its antenna, a price tag on its wrist
("check the label"). Its face is a white plate with two happy eyes and a
wide smile. The smile is in every frame: it does not change when it is
struck, when it attacks or when it falls. It faces right.

It walks with both arms out for a hug. Its attack is the hug: the arms open,
it lunges, the arms shut and its eyes are hearts. Struck, the plate slips and
what is behind it shows: a dark socket with one small red eye. Dead, it falls
down where it stood and the plate drops off, and smiles from the ground.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image

from ._ai_era_kit import OUTLINE, WHITE, Kit, Point, RGBA, actor_metadata, ease, turned

TARGET_NAME = "synthetic_friend"
FRAME_SIZE = (208, 192)
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 130),
    ("walk", 8, 95),
    ("slash", 6, 85),
    ("hurt", 4, 90),
    ("death", 8, 110),
]

GROUND = 180.0
#: Where its feet stand when it stands.
FEET_X = 100.0

SHELL: RGBA = (250, 240, 226, 255)
SHELL_DARK: RGBA = (226, 208, 196, 255)
CORAL: RGBA = (255, 122, 116, 255)
CORAL_DARK: RGBA = (214, 82, 96, 255)
PLATE: RGBA = (255, 255, 255, 255)
INK: RGBA = (44, 30, 58, 255)
BLUSH: RGBA = (255, 160, 170, 200)
HEART: RGBA = (255, 84, 120, 255)
HEART_DEAD: RGBA = (150, 140, 156, 255)
SOCKET: RGBA = (36, 22, 48, 255)
RED_EYE: RGBA = (255, 60, 70, 255)
TAG: RGBA = (255, 226, 120, 255)
STEEL: RGBA = (176, 180, 200, 255)

K = Kit(FRAME_SIZE)

ACTOR_METADATA = actor_metadata(
    "npc_synthetic_friend",
    "Synthetic Friend",
    attack_row="slash",
    ranged=False,
    traits=["ai_era", "social", "uncanny", "enemy"],
    description=(
        "The Synthetic Friend is a companion mascot: a soft toy of a robot with a heart on its chest, "
        "a price tag on its wrist and a smile that is a plate screwed to its face. The smile never changes."
    ),
    gameplay=(
        "A melee enemy that walks at its target with its arms out. Its attack is a hug. When it is struck "
        "the plate slips and shows what is behind it."
    ),
)

# Lengths of its limbs.
UPPER, FORE, LEG = 17.0, 16.0, 24.0


def _aim(angle: float) -> Point:
    """The direction of a limb: 0 hangs down, 90 points forward, 180 up."""
    a = math.radians(angle)
    return (math.sin(a), math.cos(a))


# ---- The pose ----------------------------------------------------------------


def _pose(anim: str, i: int, n: int) -> Dict[str, object]:
    ph = math.tau * i / max(1, n)
    pose: Dict[str, object] = {
        "x": 0.0,
        "bob": 0.0,
        "tilt": 0.0,
        # How far it has sat down, 0 to 1.
        "sit": 0.0,
        "head": 0.0,
        # (upper, fore) of the front arm and of the back arm.
        "front_arm": (14.0, 36.0),
        "back_arm": (-12.0, 6.0),
        "legs": (0.0, 0.0),
        "eyes": "happy",
        "plate": (0.0, 0.0, 0.0, False),
        "heart": 1.0,
        "heart_dead": False,
        "antenna": 0.0,
        "tag": 0.0,
        "hearts": (),
        "plate_off": None,
    }
    if anim == "idle":
        breath = math.sin(ph)
        pose.update(
            bob=1.2 * breath,
            head=2.5 * math.sin(ph + 0.8),
            # It waves, with the arm on its far side.
            front_arm=(14.0 + 3.0 * breath, 36.0 + 4.0 * breath),
            back_arm=(-108.0 - 5.0 * breath, -150.0 + 28.0 * math.sin(ph * 2.0)),
            heart=1.0 + 0.14 * max(0.0, math.sin(ph * 2.0)),
            antenna=8.0 * math.sin(ph + 0.4),
            tag=10.0 * math.sin(ph * 2.0 + 1.0),
            hearts=((34.0 + 3.0 * math.sin(ph), 124.0 + 6.0 * i, 5.0 - 0.5 * i),) if i < 5 else (),
        )
    elif anim == "walk":
        step = math.sin(ph)
        pose.update(
            bob=1.6 * abs(math.cos(ph)) - 0.8,
            tilt=5.0,
            head=2.0 * step,
            # Both arms out before it: it wants a hug.
            front_arm=(84.0 + 7.0 * step, 96.0 + 9.0 * step),
            back_arm=(74.0 - 7.0 * step, 88.0 - 9.0 * step),
            legs=(28.0 * step, -28.0 * step),
            antenna=-8.0 + 6.0 * math.sin(ph * 2.0),
            tag=14.0 * math.sin(ph * 2.0),
        )
    elif anim == "slash":
        keys = [
            # x, tilt, front arm, back arm, legs, eyes
            (-2.0, -6.0, (-30.0, -62.0), (-46.0, -70.0), (-6.0, 8.0), "happy"),
            (-5.0, -11.0, (-52.0, -92.0), (-70.0, -104.0), (-12.0, 12.0), "happy"),
            (9.0, 13.0, (104.0, 62.0), (70.0, 112.0), (22.0, -18.0), "heart"),
            (13.0, 17.0, (88.0, 20.0), (84.0, 150.0), (26.0, -20.0), "heart"),
            (8.0, 10.0, (92.0, 60.0), (70.0, 104.0), (14.0, -10.0), "heart"),
            (2.0, 3.0, (50.0, 70.0), (10.0, 30.0), (4.0, -2.0), "happy"),
        ]
        x, tilt, front, back, legs, eyes = keys[i % len(keys)]
        pose.update(x=x, tilt=tilt, front_arm=front, back_arm=back, legs=legs, eyes=eyes, antenna=-tilt, tag=-tilt * 1.5)
        if i == 2:
            pose["hearts"] = ((58.0, 150.0, 4.0),)
        elif i == 3:
            pose["hearts"] = ((30.0, 166.0, 5.5), (62.0, 158.0, 4.5), (86.0, 138.0, 3.5))
        elif i == 4:
            pose["hearts"] = ((26.0, 174.0, 4.5), (66.0, 168.0, 3.5), (92.0, 146.0, 2.5))
    elif anim == "hurt":
        slip = (1.0, 0.8, 0.5, 0.15)[i % 4]
        pose.update(
            x=(-5.0, -8.0, -6.0, -2.0)[i % 4],
            tilt=(-12.0, -16.0, -10.0, -3.0)[i % 4],
            head=(-8.0, -5.0, -3.0, 0.0)[i % 4],
            front_arm=((74.0, 104.0), (62.0, 116.0), (50.0, 82.0), (26.0, 46.0))[i % 4],
            back_arm=((-120.0, -150.0), (-100.0, -130.0), (-60.0, -80.0), (-20.0, -10.0))[i % 4],
            legs=((-14.0, 10.0), (-18.0, 14.0), (-10.0, 8.0), (-3.0, 2.0))[i % 4],
            # The plate slips: (along, down, turn, what is behind shows).
            plate=(7.0 * slip, 13.0 * slip, 16.0 * slip, True),
            antenna=(30.0, 40.0, 22.0, 8.0)[i % 4],
            tag=(-40.0, -55.0, -30.0, -10.0)[i % 4],
        )
    elif anim == "death":
        sit = ease((i - 1) / 3.0)
        pose.update(
            x=-4.0 * sit,
            tilt=-8.0 if i == 0 else -8.0 - 10.0 * sit,
            sit=sit,
            head=24.0 * ease((i - 2) / 3.0),
            front_arm=(14.0 - 4.0 * sit, 36.0 - 30.0 * sit),
            back_arm=(-12.0 + 6.0 * sit, 6.0),
            # Sitting, its legs are out before it.
            legs=(66.0 * sit, 58.0 * sit),
            plate=(5.0, 9.0, 12.0, True) if i < 3 else (0.0, 0.0, 0.0, True),
            heart=1.0 - 0.25 * sit,
            heart_dead=i >= 5,
            antenna=46.0 * sit,
            tag=18.0 * sit,
            # The plate is off: where it is in the frame, how it is turned.
            plate_off=None if i < 3 else ((132.0, 96.0, 28.0), (146.0, 134.0, 64.0), (152.0, 158.0, 34.0), (153.0, 161.0, 20.0),
                                          (153.0, 161.0, 20.0))[i - 3],
        )
    return pose


# ---- Pieces ------------------------------------------------------------------


def _limb(length: float, width: float, colour: RGBA, cuff: RGBA | None = None):
    """A limb from ``home`` down."""
    h = K.home

    def shape(d) -> None:
        K.stroke(d, [h, K.at(0.0, length)], WHITE, width)

    def detail(d) -> None:
        if cuff is not None:
            K.rrect(d, h[0] - width, h[1] + length - 4.5, h[0] + width, h[1] + length + width, 0.0, cuff)

    return K.solid(("limb", length, width, colour, cuff), shape, colour, detail)


def _hand():
    """The mitten, from its wrist at ``home`` down."""

    def shape(d) -> None:
        K.oval(d, K.at(0.0, 5.0), 7.6, 8.2, WHITE)
        K.oval(d, K.at(6.0, 1.5), 3.6, 4.4, WHITE)

    return K.solid(("hand",), shape, SHELL)


def _foot():
    """The shoe, from its ankle at ``home``."""

    def shape(d) -> None:
        K.rrect(d, K.home[0] - 7.0, K.home[1] - 2.0, K.home[0] + 15.0, K.home[1] + 12.0, 6.5, WHITE)

    def detail(d) -> None:
        K.rrect(d, K.home[0] - 8.0, K.home[1] + 8.5, K.home[0] + 16.0, K.home[1] + 13.0, 0.0, WHITE)

    return K.solid(("foot",), shape, CORAL, detail)


def _torso(heart: float, dead: bool):
    h = K.home

    def shape(d) -> None:
        K.oval(d, h, 25.0, 30.0, WHITE)

    def detail(d) -> None:
        # A collar, a seam, and the heart on its chest.
        K.rrect(d, h[0] - 30.0, h[1] - 31.0, h[0] + 30.0, h[1] - 21.0, 0.0, CORAL)
        K.line(d, [(h[0] - 24.0, h[1] + 14.0), (h[0], h[1] + 18.0), (h[0] + 24.0, h[1] + 14.0)], SHELL_DARK, 1.0)
        colour = HEART_DEAD if dead else HEART
        if not dead:
            K.heart(d, K.at(-5.0, -2.0), 11.5 * heart, (255, 150, 170, 110), None)
        K.heart(d, K.at(-5.0, -2.0), 8.5 * heart, colour, OUTLINE, 0.9)
        K.oval(d, K.at(-8.0, -5.5), 1.8 * heart, 1.4 * heart, (255, 255, 255, 190))

    return K.solid(("torso", round(heart, 2), dead), shape, SHELL, detail)


def _head():
    h = K.home

    def shape(d) -> None:
        K.oval(d, h, 36.0, 32.0, WHITE)
        # The ear: a round speaker on the side of its head.
        K.oval(d, K.at(-33.0, 3.0), 8.0, 11.0, WHITE)

    def detail(d) -> None:
        K.oval(d, K.at(-33.0, 3.0), 8.0, 11.0, CORAL)
        K.oval(d, K.at(-33.5, 3.0), 3.6, 5.4, CORAL_DARK)
        K.line(d, [(h[0] - 20.0, h[1] - 27.0), (h[0] + 6.0, h[1] - 32.0)], SHELL_DARK, 0.9)
        K.oval(d, K.at(-8.0, -20.0), 9.0, 4.0, (255, 255, 255, 150))

    return K.solid(("head",), shape, SHELL, detail)


def _socket():
    """What is behind the plate."""
    h = K.home

    def shape(d) -> None:
        K.rrect(d, h[0] - 21.0, h[1] - 17.0, h[0] + 21.0, h[1] + 17.0, 13.0, WHITE)

    def detail(d) -> None:
        for x in (-12.0, -4.0, 14.0):
            K.line(d, [(h[0] + x, h[1] - 17.0), (h[0] + x + 5.0, h[1] + 17.0)], (70, 50, 90, 255), 0.8)
        K.oval(d, K.at(6.0, -3.0), 5.4, 5.4, (255, 60, 70, 90))
        K.oval(d, K.at(6.0, -3.0), 2.6, 2.6, RED_EYE)
        K.oval(d, K.at(5.2, -3.8), 0.9, 0.9, (255, 220, 220, 255))

    return K.solid(("socket",), shape, SOCKET, detail, outline=1.0, rim=0.0, shade=0.0)


def _plate(eyes: str):
    """The face: a plate with its eyes and its smile. The smile is the same
    in every one."""
    h = K.home

    def shape(d) -> None:
        K.rrect(d, h[0] - 24.0, h[1] - 20.0, h[0] + 24.0, h[1] + 20.0, 15.0, WHITE)

    def detail(d) -> None:
        for sign, x in ((-1.0, -9.0), (1.0, 11.0)):
            eye = K.at(x, -5.0)
            if eyes == "heart":
                K.heart(d, eye, 5.6, HEART, OUTLINE, 0.8)
            else:
                arc = [(eye[0] - 5.4, eye[1] + 2.2), (eye[0] - 3.0, eye[1] - 2.4), (eye[0], eye[1] - 3.6), (eye[0] + 3.0, eye[1] - 2.4),
                       (eye[0] + 5.4, eye[1] + 2.2)]
                K.stroke(d, arc, INK, 2.1)
            K.oval(d, (eye[0] + sign * 1.5, eye[1] + 9.0), 5.0, 3.0, BLUSH)
        # The smile: a little too wide.
        smile = [K.at(-15.0, 4.0), K.at(-9.0, 10.5), K.at(1.0, 13.0), K.at(11.0, 10.5), K.at(17.0, 4.0)]
        K.poly(d, smile + [K.at(11.0, 7.5), K.at(1.0, 9.0), K.at(-9.0, 7.5)], PLATE)
        K.stroke(d, smile, INK, 2.2)
        for sign in (-1.0, 1.0):
            K.stroke(d, [K.at(1.0 + sign * 16.0, 4.0), K.at(1.0 + sign * 18.0, 1.6)], INK, 1.6)
        # Two screws hold it on.
        for x, y in ((-19.0, -14.0), (19.0, 14.0)):
            K.oval(d, K.at(x, y), 2.0, 2.0, STEEL, OUTLINE, 0.6)
            K.line(d, [K.at(x - 1.2, y - 1.2), K.at(x + 1.2, y + 1.2)], OUTLINE, 0.6)

    return K.solid(("plate", eyes), shape, PLATE, detail, outline=1.1, rim=0.0, shade=0.22, shade_colour=(150, 140, 190, 255))


def _antenna():
    """The antenna from its foot at ``home`` up, a heart on its end."""

    def paint(d) -> None:
        stalk = [K.home, K.at(1.0, -9.0), K.at(-1.0, -16.0)]
        K.line(d, stalk, OUTLINE, 3.6)
        K.line(d, stalk, STEEL, 1.6)
        K.heart(d, K.at(-1.0, -21.0), 6.4, HEART, OUTLINE, 0.9)
        K.oval(d, K.at(-3.2, -23.4), 1.3, 1.0, (255, 255, 255, 200))

    return K.piece(("antenna",), paint)


def _tag():
    """The price tag, from where its string is tied at ``home`` down."""

    def paint(d) -> None:
        K.line(d, [K.home, K.at(0.0, 7.0)], OUTLINE, 0.9)
        tag = [K.at(0.0, 5.0), K.at(6.0, 10.0), K.at(6.0, 25.0), K.at(-6.0, 25.0), K.at(-6.0, 10.0)]
        K.poly(d, tag, TAG, OUTLINE, 1.0)
        K.oval(d, K.at(0.0, 10.0), 1.3, 1.3, OUTLINE)
        for k, x in enumerate((-4.0, -2.6, -0.8, 0.4, 2.2, 3.8)):
            K.line(d, [K.at(x, 14.0), K.at(x, 22.0)], INK, 0.5 + 0.4 * (k % 2))

    return K.piece(("tag",), paint)


def _float_heart(r: float):
    def paint(d) -> None:
        K.heart(d, K.home, r, HEART, OUTLINE, 0.8)
        K.oval(d, K.at(-0.35 * r, -0.35 * r), 0.2 * r, 0.16 * r, (255, 255, 255, 200))

    return K.piece(("float_heart", r), paint)


# ---- Frames ------------------------------------------------------------------


def _render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    pose = _pose(anim, frame_idx, nframes)
    img = K.new_frame()
    tilt = float(pose["tilt"])
    sit = float(pose["sit"])
    feet = (FEET_X + float(pose["x"]), GROUND)
    # Sitting, its hips are on the ground, and it leans about them.
    drop = 22.0 * sit
    pivot = (0.0, (-34.0 + drop) * sit)
    bob = float(pose["bob"]) + drop

    def body(x: float, y: float) -> Point:
        """A point of its body (from its feet, up is negative) in the frame."""
        p = turned((x - pivot[0], y - pivot[1]), tilt)
        return (feet[0] + pivot[0] + p[0], feet[1] + pivot[1] + p[1])

    def limb_chain(root: Point, angles: Tuple[float, ...], lengths: Tuple[float, ...]) -> List[Point]:
        pts = [root]
        for angle, length in zip(angles, lengths):
            dx, dy = _aim(angle)
            pts.append((pts[-1][0] + dx * length, pts[-1][1] + dy * length))
        return pts

    def put_leg(hip_x: float, angle: float, name: str) -> None:
        hip, ankle = limb_chain((hip_x, -34.0 + drop + (bob - drop) * 0.3), (angle,), (LEG,))
        K.place(img, _limb(LEG, 12.0, SHELL), body(*hip), f"{name}_leg", tilt - angle)
        # A foot is nearly flat on the ground while it stands; sitting, its
        # toes are up.
        K.place(img, _foot(), body(*ankle), f"{name}_foot", -angle * 0.4 * (1.0 - sit) + (tilt - angle) * sit)

    def put_arm(shoulder: Point, angles: Tuple[float, float], name: str, tag: bool = False) -> None:
        s, elbow, wrist = limb_chain(shoulder, angles, (UPPER, FORE))
        K.place(img, _limb(UPPER, 11.0, CORAL), body(*s), f"{name}_upper", tilt - angles[0])
        K.place(img, _limb(FORE, 10.0, SHELL), body(*elbow), f"{name}_fore", tilt - angles[1])
        if tag:
            K.place(img, _tag(), body(*wrist), "tag", float(pose["tag"]))
        K.place(img, _hand(), body(*wrist), f"{name}_hand", tilt - angles[1])

    legs = pose["legs"]
    lift = -62.0 + bob
    put_arm((-12.0, lift - 18.0), pose["back_arm"], "back")  # type: ignore[arg-type]
    put_leg(-9.0, legs[1], "back")  # type: ignore[index]
    put_leg(9.0, legs[0], "front")  # type: ignore[index]
    K.place(img, _torso(float(pose["heart"]), bool(pose["heart_dead"])), body(0.0, lift), "torso", tilt)

    head_turn = tilt + float(pose["head"])
    head = body(2.0, lift - 54.0)

    def on_head(x: float, y: float) -> Point:
        p = turned((x, y), head_turn)
        return (head[0] + p[0], head[1] + p[1])

    K.place(img, _antenna(), on_head(-4.0, -30.0), "antenna", head_turn + float(pose["antenna"]))
    K.place(img, _head(), head, "head", head_turn)
    along, down, plate_turn, shows = pose["plate"]  # type: ignore[misc]
    if shows:
        K.place(img, _socket(), on_head(9.0, 2.0), "socket", head_turn)
    if pose["plate_off"] is None:
        K.place(img, _plate(str(pose["eyes"])), on_head(9.0 + along, 2.0 + down), "plate", head_turn + plate_turn)
    else:
        px, py, turn = pose["plate_off"]  # type: ignore[misc]
        K.place(img, _plate("happy"), (px, py), "plate", turn)
    put_arm((14.0, lift - 18.0), pose["front_arm"], "front", tag=True)  # type: ignore[arg-type]
    for k, (x, y, r) in enumerate(pose["hearts"]):  # type: ignore[arg-type]
        r = round(max(1.5, r) * 2.0) / 2.0
        K.place(img, _float_heart(r), (FEET_X + x, GROUND - y), f"heart_{k}")
    return K.downsample(img)


#: The gameplay body: it as it stands, without its antenna, its tag and its
#: raised arm.
BODY_BOX = (FEET_X - 36.0, GROUND - 150.0, FEET_X + 38.0, GROUND + 1.0)


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    # The floor where its soles are drawn (`Kit.standing_floor`), not `GROUND`:
    # its shoes reach under the ground line.
    floor = K.standing_floor(ROWS, _render_frame)
    return K.render(TARGET_NAME, ROWS, _render_frame, out_dir, ACTOR_METADATA, BODY_BOX[:3] + (floor or BODY_BOX[3],))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render the Synthetic Friend sprite target.")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[2] / "generated" / TARGET_NAME)
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


if __name__ == "__main__":
    raise SystemExit(main())
