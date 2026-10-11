"""Sprite generator for the Spaghetti Event: a twirl of spaghetti that is a
tangle of calls.

The look (redrawn 2026-10-11): a ball of noodles twirled on a fork, with a
cap of sauce and a leaf of basil. Two meatballs are its eyes, under heavy
lids. It stands on four noodles, each with a loop at its foot. Its noodles
are calls: the one before it ends in an arrowhead, and the one behind it is a
loop that comes back into the ball, with an arrowhead that goes round it and
never arrives. It faces right.

It walks on its noodles. Its attack is the noodle before it, cracked like a
whip. Struck, it is squashed, its lids fly up and sauce flies off. Dead, it
unravels into a plate of spaghetti: the fork falls over and one eye rolls
away.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from PIL import Image

from ._ai_era_kit import OUTLINE, WHITE, Kit, Point, RGBA, actor_metadata, bezier, ease, mix

TARGET_NAME = "spaghetti_event"
FRAME_SIZE = (224, 176)
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 130),
    ("walk", 8, 95),
    ("slash", 6, 80),
    ("hurt", 4, 90),
    ("death", 8, 115),
]

GROUND = 164.0
CX = 100.0
#: The ball at rest: half its width, half its height, how far it is off the ground.
REST_RX, REST_RY, REST_GAP = 54.0, 40.0, 20.0

PASTA: RGBA = (246, 212, 124, 255)
PASTA_LIGHT: RGBA = (255, 238, 176, 255)
PASTA_EDGE: RGBA = (196, 146, 74, 255)
PASTA_DEEP: RGBA = (138, 92, 52, 255)
SAUCE: RGBA = (216, 62, 48, 255)
SAUCE_LIGHT: RGBA = (250, 122, 92, 255)
MEAT: RGBA = (146, 88, 62, 255)
MEAT_DARK: RGBA = (104, 58, 44, 255)
EYE: RGBA = (252, 248, 236, 255)
INK: RGBA = (44, 28, 40, 255)
STEEL: RGBA = (208, 214, 228, 255)
STEEL_DARK: RGBA = (140, 148, 172, 255)
BASIL: RGBA = (86, 172, 92, 255)
BASIL_DARK: RGBA = (52, 124, 70, 255)

K = Kit(FRAME_SIZE)

ACTOR_METADATA = actor_metadata(
    "npc_spaghetti_event",
    "Spaghetti Event",
    attack_row="slash",
    ranged=False,
    traits=["ai_era", "noodle", "enemy"],
    description=(
        "The Spaghetti Event is a twirl of spaghetti on a fork with meatballs for eyes. Its noodles are "
        "calls: one ends in an arrowhead, one is a loop that comes back into the tangle."
    ),
    gameplay="A melee enemy that walks on its noodles and cracks one of them like a whip.",
)


def _hash(k: int, salt: float) -> float:
    """A fixed number in 0..1 for strand ``k``."""
    v = math.sin(k * 12.9898 + salt * 78.233) * 43758.5453
    return v - math.floor(v)


# ---- The pose ----------------------------------------------------------------


def _pose(anim: str, i: int, n: int) -> Dict[str, object]:
    ph = math.tau * i / max(1, n)
    pose: Dict[str, object] = {
        "x": 0.0,
        "rx": REST_RX,
        "ry": REST_RY,
        "gap": REST_GAP,
        "wiggle": ph,
        "loose": 0.0,
        # Each foot: (how far before its root, how far off the ground).
        "feet": ((0.0, 0.0),) * 4,
        "slack": 0.0,
        "fork": -22.0,
        "fork_front": False,
        # The lids: 0 is open wide, 1 is shut.
        "lids": 0.45,
        "look": (1.0, 0.6),
        "mouth": 0.0,
        # The noodle before it: its end from its root, and how it bends.
        "whip": ((30.0, -16.0), -18.0),
        # Where the arrowhead is on the loop behind it, in turns.
        "loop": i / max(1, n),
        "eye_roll": 0.0,
        "drops": (),
    }
    if anim == "idle":
        breath = math.sin(ph)
        pose.update(
            ry=REST_RY + 1.4 * breath,
            rx=REST_RX - 0.8 * breath,
            fork=-22.0 + 3.0 * math.sin(ph + 0.7),
            lids=0.45 if i != 4 else 1.0,
            look=(1.2 * math.cos(ph), 0.6 + 0.5 * math.sin(ph)),
            whip=((30.0 + 2.0 * breath, -16.0 - 4.0 * math.sin(ph + 1.0)), -18.0 + 8.0 * math.sin(ph + 0.4)),
        )
    elif anim == "walk":
        feet = []
        for k in range(4):
            a = ph + k * math.pi * 0.5 + (math.pi if k % 2 else 0.0) * 0.5
            feet.append((9.0 * math.sin(a), 5.5 * max(0.0, math.cos(a))))
        pose.update(
            x=0.0,
            ry=REST_RY + 1.6 * math.sin(ph * 2.0),
            gap=REST_GAP + 1.6 * math.sin(ph * 2.0 + 0.6),
            feet=tuple(feet),
            fork=-26.0 + 5.0 * math.sin(ph),
            look=(1.6, 0.4),
            whip=((32.0, -10.0 + 5.0 * math.sin(ph)), -24.0 + 10.0 * math.sin(ph + 1.0)),
        )
    elif anim == "slash":
        keys = [
            # x, rx, ry, whip end, bend, lids, mouth
            (-3.0, 53.0, 42.0, (4.0, -46.0), -34.0, 0.2, 0.4),
            (-5.0, 52.0, 43.0, (-22.0, -56.0), -46.0, 0.1, 0.7),
            (5.0, 57.0, 37.0, (50.0, -34.0), 30.0, 0.0, 1.0),
            (7.0, 58.0, 36.0, (56.0, 4.0), -8.0, 0.0, 1.0),
            (4.0, 56.0, 38.0, (48.0, 10.0), -30.0, 0.25, 0.5),
            (1.0, 54.0, 40.0, (36.0, -10.0), -22.0, 0.4, 0.1),
        ]
        x, rx, ry, end, bend, lids, mouth = keys[i % len(keys)]
        pose.update(x=x, rx=rx, ry=ry, whip=(end, bend), lids=lids, mouth=mouth, look=(2.0, 0.2), fork=-22.0 - x * 1.4,
                    feet=((x * 0.6, 0.0),) * 4)
        if i == 3:
            pose["drops"] = ((104.0, 64.0, 2.4), (96.0, 80.0, 1.6), (112.0, 30.0, 1.5))
    elif anim == "hurt":
        squash = (0.74, 0.66, 0.80, 0.94)[i % 4]
        pose.update(
            x=(-4.0, -7.0, -4.0, -1.0)[i % 4],
            ry=REST_RY * squash,
            rx=REST_RX * (1.0 + (1.0 - squash) * 0.5),
            gap=REST_GAP * squash,
            loose=(1.0, 0.8, 0.5, 0.15)[i % 4],
            fork=(-44.0, -52.0, -38.0, -26.0)[i % 4],
            lids=0.0,
            look=(-0.6, -0.8),
            mouth=(0.9, 1.0, 0.6, 0.2)[i % 4],
            whip=(((14.0, -48.0), 40.0), ((6.0, -56.0), 52.0), ((20.0, -36.0), 20.0), ((28.0, -20.0), -8.0))[i % 4],
            feet=((-6.0, 0.0), (-3.0, 0.0), (3.0, 0.0), (6.0, 0.0)),
            drops=(((-58.0, 78.0, 2.6), (62.0, 86.0, 2.2), (4.0, 110.0, 2.0)), ((-70.0, 88.0, 2.2), (74.0, 98.0, 1.8), (8.0, 124.0, 1.6)),
                   ((-78.0, 82.0, 1.5), (82.0, 92.0, 1.2)), ())[i % 4],
        )
    elif anim == "death":
        flat = ease(i / max(1, n - 1))
        pose.update(
            ry=REST_RY - 24.0 * flat,
            rx=REST_RX + 14.0 * flat,
            gap=REST_GAP * (1.0 - flat),
            wiggle=ph * 0.4,
            loose=0.5 * flat,
            slack=flat,
            # The fork falls over and lies on the plate of it.
            fork=-22.0 - 76.0 * ease(i / max(1, n - 1) * 1.3),
            fork_front=i >= 4,
            lids=min(1.0, 0.45 + 1.2 * flat),
            look=(0.0, 1.2),
            mouth=0.3 * (1.0 - flat),
            whip=((30.0 + 14.0 * flat, -16.0 + 30.0 * flat), -18.0 + 22.0 * flat),
            loop=0.4,
            eye_roll=ease((i - 2) / 5.0),
        )
    return pose


# ---- Noodles -----------------------------------------------------------------


def _noodle(d, pts: Sequence[Point], width: float, tone: RGBA = PASTA) -> None:
    """One noodle on a canvas: its dark edge, itself, a light along it."""
    K.stroke(d, pts, PASTA_EDGE, width)
    K.stroke(d, pts, tone, width - 1.9)
    if len(pts) > 4:
        K.line(d, [(x - 0.5, y - 0.9) for x, y in pts[1:-1]], PASTA_LIGHT, 0.9)


def _strand(key: tuple, pts: Sequence[Point], width: float = 6.0, arrow: bool = False):
    """A loose noodle (painted about ``home``), with an arrowhead on its end."""

    def head() -> List[Point]:
        (ax, ay), (bx, by) = pts[-3], pts[-1]
        length = math.hypot(bx - ax, by - ay) or 1.0
        ux, uy = (bx - ax) / length, (by - ay) / length
        return [(bx + ux * 8.5, by + uy * 8.5), (bx - uy * 6.2, by + ux * 6.2), (bx + uy * 6.2, by - ux * 6.2)]

    def shape(d) -> None:
        K.stroke(d, pts, WHITE, width)
        if arrow:
            K.poly(d, head(), WHITE)

    def detail(d) -> None:
        _noodle(d, pts, width)
        if arrow:
            K.poly(d, head(), SAUCE)
            tip = head()
            K.line(d, [tip[0], tip[1]], SAUCE_LIGHT, 1.0)

    return K.solid(key, shape, PASTA_EDGE, detail, rim=0.0, shade=0.0)


def _ball_strands(rx: float, ry: float, wiggle: float, loose: float) -> List[List[Point]]:
    """The noodles of the ball, about ``home``: arcs round it, each a little
    off the last."""
    h = K.home
    strands: List[List[Point]] = []
    for k in range(40):
        start = math.radians(k * 137.5) + 0.08 * math.sin(wiggle + k * 1.3)
        sweep = math.radians(110.0 + 80.0 * _hash(k, 1.0)) * (1.0 if k % 2 else -1.0)
        r1 = 0.22 + 0.74 * _hash(k, 2.0)
        r2 = 0.20 + 0.76 * _hash(k, 3.0)
        bulge = 0.10 + 0.20 * _hash(k, 4.0) + 0.22 * loose * _hash(k, 5.0)

        def at(angle: float, r: float) -> Point:
            return (h[0] + rx * r * math.cos(angle), h[1] + ry * r * math.sin(angle))

        strands.append(bezier(at(start, r1), at(start + sweep / 3.0, r1 + bulge), at(start + 2.0 * sweep / 3.0, r2 + bulge), at(start + sweep, r2), 14))
    return strands


def _ball(rx: float, ry: float, wiggle: float, loose: float):
    key = ("ball", rx, ry, wiggle, loose)
    strands = _ball_strands(rx, ry, wiggle, loose)

    def shape(d) -> None:
        K.oval(d, K.home, rx * 0.92, ry * 0.92, WHITE)
        for pts in strands:
            K.stroke(d, pts, WHITE, 7.0)

    def detail(d) -> None:
        for k, pts in enumerate(strands):
            _noodle(d, pts, 7.0, PASTA if k % 3 else mix(PASTA, PASTA_EDGE, 0.22))

    return K.solid(key, shape, mix(PASTA_EDGE, PASTA_DEEP, 0.4), detail, rim=0.0, shade=0.0)


def _sauce():
    """The cap of sauce, its middle at ``home``."""
    h = K.home

    def shape(d) -> None:
        K.oval(d, h, 27.0, 11.5, WHITE)
        for x, length, w in ((-19.0, 15.0, 9.0), (-4.0, 22.0, 10.0), (14.0, 13.0, 8.0), (23.0, 8.0, 6.0)):
            K.stroke(d, [(h[0] + x, h[1]), (h[0] + x, h[1] + length)], WHITE, w)

    def detail(d) -> None:
        K.oval(d, K.at(-7.0, -4.0), 10.0, 3.2, SAUCE_LIGHT)
        K.oval(d, K.at(-4.0, 18.0), 1.9, 2.8, SAUCE_LIGHT)
        # A leaf of basil on it.
        leaf = [K.at(5.0, -2.0), K.at(12.0, -11.0), K.at(24.0, -10.0), K.at(19.0, -1.0), K.at(10.0, 1.5)]
        K.poly(d, leaf, BASIL, BASIL_DARK, 0.9)
        K.line(d, [K.at(6.0, -1.5), K.at(22.0, -9.0)], BASIL_DARK, 0.8)

    return K.solid(("sauce",), shape, SAUCE, detail)


def _fork():
    """The fork: its tines down from ``home``, its handle up."""
    h = K.home

    def shape(d) -> None:
        K.rrect(d, h[0] - 3.4, h[1] - 62.0, h[0] + 3.4, h[1] - 22.0, 3.4, WHITE)
        K.poly(d, [K.at(-2.4, -24.0), K.at(2.4, -24.0), K.at(8.0, -12.0), K.at(-8.0, -12.0)], WHITE)
        for x in (-6.6, -2.2, 2.2, 6.6):
            K.stroke(d, [K.at(x, -13.0), K.at(x, 12.0)], WHITE, 2.9)

    def detail(d) -> None:
        K.line(d, [K.at(-1.2, -58.0), K.at(-1.2, -26.0)], WHITE, 1.1)
        K.oval(d, K.at(0.0, -57.0), 1.3, 1.3, STEEL_DARK)

    return K.solid(("fork",), shape, STEEL, detail, shade_colour=STEEL_DARK, shade=0.6)


def _meatball(r: float, lids: float, look: Point):
    """A meatball that is an eye, its middle at ``home``."""
    h = K.home
    lids = round(lids, 2)

    def shape(d) -> None:
        K.oval(d, h, r, r, WHITE)

    def detail(d) -> None:
        for x, y in ((-0.5, -0.6), (0.5, 0.55), (-0.62, 0.3), (0.2, -0.75)):
            K.oval(d, K.at(x * r, y * r), 0.12 * r, 0.1 * r, MEAT_DARK)
        if lids >= 0.98:
            K.stroke(d, [K.at(-0.55 * r, 0.1 * r), K.at(0.0, 0.3 * r), K.at(0.55 * r, 0.1 * r)], INK, 1.4)
            return
        K.oval(d, K.at(0.08 * r, 0.05 * r), 0.66 * r, 0.66 * r, EYE, INK, 0.8)
        K.oval(d, K.at(0.08 * r + look[0] * 0.2 * r, 0.05 * r + look[1] * 0.2 * r), 0.3 * r, 0.32 * r, INK)
        K.oval(d, K.at(0.0 + look[0] * 0.2 * r, -0.08 * r + look[1] * 0.2 * r), 0.1 * r, 0.1 * r, WHITE)
        if lids > 0.02:
            # The lid: the meatball, down over the eye.
            edge = h[1] - 0.66 * r + 1.32 * r * lids
            K.rrect(d, h[0] - r, h[1] - r, h[0] + r, edge, 0.0, MEAT)
            K.line(d, [(h[0] - 0.7 * r, edge), (h[0] + 0.85 * r, edge)], INK, 1.0)

    return K.solid(("meatball", r, lids, look), shape, MEAT, detail, shade=0.5)


def _mouth(opening: float):
    opening = round(opening, 2)

    def paint(d) -> None:
        h = K.home
        if opening < 0.08:
            K.stroke(d, [K.at(-6.0, 0.0), K.at(-2.0, 1.4), K.at(3.0, -0.4), K.at(7.0, 1.0)], INK, 1.6)
            return
        K.oval(d, h, 7.0 + 1.5 * opening, 1.6 + 5.4 * opening, INK)
        K.oval(d, K.at(0.5, 1.2 + 2.6 * opening), 3.6, 1.2 + 1.6 * opening, SAUCE)
        # A noodle goes across it.
        _noodle(d, [K.at(-9.0, -1.0 - 2.0 * opening), K.at(-2.0, 0.6), K.at(4.0, -2.2 * opening), K.at(10.0, 0.4 - 2.0 * opening)], 3.6)

    return K.piece(("mouth", opening), paint)


def _drop(r: float):
    def paint(d) -> None:
        K.oval(d, K.home, r + 1.1, r + 1.1, OUTLINE)
        K.oval(d, K.home, r, r, SAUCE)
        K.oval(d, K.at(0.3 * r, -0.3 * r), 0.34 * r, 0.34 * r, SAUCE_LIGHT)

    return K.piece(("drop", r), paint)


def _arrowhead():
    """The arrowhead that goes round the loop, pointing along +x from ``home``."""

    def paint(d) -> None:
        K.poly(d, [K.at(7.0, 0.0), K.at(-4.0, -5.6), K.at(-4.0, 5.6)], SAUCE, OUTLINE, 1.0)

    return K.piece(("arrowhead",), paint)


# ---- Frames ------------------------------------------------------------------


def _render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    pose = _pose(anim, frame_idx, nframes)
    img = K.new_frame()
    rx, ry, gap = round(float(pose["rx"]), 1), round(float(pose["ry"]), 1), float(pose["gap"])
    slack = float(pose["slack"])
    centre = (CX + float(pose["x"]), GROUND - gap - ry)
    home = K.home

    def rel(x: float, y: float) -> Point:
        return (round(x, 1), round(y, 1))

    # The loop behind it: a noodle that comes back into the ball.
    loop_c = (centre[0] - rx - 11.0 + 6.0 * slack, centre[1] - 2.0 + (gap + ry - 16.0) * slack)
    loop_r = (18.0, 15.0 - 7.0 * slack)
    ring = [(home[0] + loop_r[0] * math.cos(math.tau * j / 28), home[1] + loop_r[1] * math.sin(math.tau * j / 28)) for j in range(29)]
    K.place(img, _strand(("loop", loop_r), ring), loop_c, "loop")
    turn = math.tau * float(pose["loop"])
    K.place(img, _arrowhead(), (loop_c[0] + loop_r[0] * math.cos(turn), loop_c[1] + loop_r[1] * math.sin(turn)), "loop_arrow",
            math.degrees(math.atan2(loop_r[1] * math.cos(turn), -loop_r[0] * math.sin(turn))))

    fork_at = (centre[0] - 6.0, centre[1] - ry * 0.55)
    if not pose["fork_front"]:
        K.place(img, _fork(), fork_at, "fork", float(pose["fork"]))

    # The noodles it stands on: each from under the ball to its foot, with
    # the loop at its foot.
    for k, (root_x, (ahead, up)) in enumerate(zip((-33.0, -12.0, 10.0, 32.0), pose["feet"])):  # type: ignore[arg-type]
        root = (centre[0] + root_x * rx / REST_RX, centre[1] + ry * 0.7)
        foot = (CX + float(pose["x"]) * 0.4 + root_x * (1.0 + 0.45 * slack) + ahead, GROUND - 3.2 - up)
        dx, dy = rel(foot[0] - root[0], foot[1] - root[1])
        curl = 1.0 if k % 2 else -1.0
        pts = bezier(home, K.at(0.0, max(4.0, dy * 0.5)), K.at(dx - 5.0 * curl, dy - 9.0 * (1.0 - slack)), K.at(dx, dy), 12)
        pts += [K.at(dx + 4.6 * curl * math.sin(a), dy - 3.4 + 3.4 * math.cos(a)) for a in (0.7, 1.4, 2.1, 2.8, 3.5, 4.2, 4.9)]
        K.place(img, _strand(("leg", dx, dy, curl, round(slack, 2)), pts, 6.2), root, f"leg_{k}")

    K.place(img, _ball(rx, ry, round(float(pose["wiggle"]), 3), round(float(pose["loose"]), 2)), centre, "ball")
    K.place(img, _sauce(), (centre[0] - 2.0, centre[1] - ry * 0.80), "sauce")
    if pose["fork_front"]:
        K.place(img, _fork(), fork_at, "fork", float(pose["fork"]))

    # The noodle before it: a call, with an arrowhead.
    (wx, wy), bend = pose["whip"]  # type: ignore[misc]
    wx, wy, bend = round(wx, 1), round(wy, 1), round(bend, 1)
    whip_root = (centre[0] + rx * 0.80, centre[1] + ry * 0.25)
    mid = (wx * 0.5 - wy * bend / 60.0, wy * 0.5 + wx * bend / 60.0)
    whip = bezier(home, K.at(mid[0] * 0.6, mid[1] * 0.6 + 6.0), K.at(mid[0] * 1.3, mid[1] * 1.3), K.at(wx, wy), 18)
    K.place(img, _strand(("whip", wx, wy, bend), whip, 6.4, arrow=True), whip_root, "whip")

    # Its eyes, and its mouth.
    lids, look = float(pose["lids"]), pose["look"]
    look = (round(look[0], 1), round(look[1], 1))  # type: ignore[index]
    roll = float(pose["eye_roll"])
    far = (centre[0] + 0.10 * rx, centre[1] - 0.36 * ry + 8.0 * roll)
    near = (centre[0] + 0.60 * rx + 50.0 * roll, centre[1] - 0.22 * ry + (GROUND - 12.0 - (centre[1] - 0.22 * ry)) * roll)
    K.place(img, _meatball(11.0, lids, look), far, "far_eye", -8.0)
    K.place(img, _meatball(13.0, lids, look), near, "near_eye", 6.0 + 400.0 * roll)
    K.place(img, _mouth(float(pose["mouth"])), (centre[0] + 0.40 * rx, centre[1] + 0.36 * ry), "mouth", 4.0)

    for k, (x, y, r) in enumerate(pose["drops"]):  # type: ignore[arg-type]
        r = round(r * 2.0) / 2.0
        K.place(img, _drop(r), (CX + x, GROUND - y), f"drop_{k}")
    return K.downsample(img)


#: The gameplay body: the ball and the noodles it stands on.
BODY_BOX = (CX - REST_RX - 4.0, GROUND - REST_GAP - 2.0 * REST_RY - 6.0, CX + REST_RX + 4.0, GROUND + 1.0)


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    return K.render(TARGET_NAME, ROWS, _render_frame, out_dir, ACTOR_METADATA, BODY_BOX)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render the Spaghetti Event sprite target.")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[2] / "generated" / TARGET_NAME)
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


if __name__ == "__main__":
    raise SystemExit(main())
