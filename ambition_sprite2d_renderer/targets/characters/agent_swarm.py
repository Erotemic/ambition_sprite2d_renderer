"""Sprite generator for the Agent Swarm: seven small agents and the lines
between them.

The look (redrawn 2026-10-11): seven of the same small flying robot, each
with one eye, a rotor and a stripe of its own colour. Thin lines join the
ones that are near each other, and a bead goes along each line: the plan is
in the lines, not in any one of them. Standing, they are a loose cloud, each
on its own beat; two of them face each other and vote, one with a tick and
one with a cross. It faces right.

To walk they make an arrowhead. To attack they close into a spear, all of
their eyes the same, and thrust. Struck, they scatter and the lines break.
Dead, they drop to the ground one after another.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image

from ._ai_era_kit import WHITE, Kit, Point, RGBA, actor_metadata, ease, lerp

TARGET_NAME = "agent_swarm"
FRAME_SIZE = (224, 192)
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 6, 130),
    ("walk", 8, 95),
    ("slash", 6, 80),
    ("hurt", 4, 90),
    ("death", 8, 110),
]

GROUND = 180.0
CX = 104.0
#: The middle of the cloud, above the ground.
HOVER = 84.0
COUNT = 7
#: How large an agent is drawn.
SIZE = 1.4

BODY: RGBA = (104, 118, 204, 255)
BODY_DEAD: RGBA = (120, 124, 150, 255)
EYE: RGBA = (250, 252, 255, 255)
INK: RGBA = (32, 26, 58, 255)
LINK: RGBA = (150, 224, 255, 170)
BEAD: RGBA = (255, 255, 255, 255)
GREEN: RGBA = (84, 206, 124, 255)
RED: RGBA = (240, 78, 92, 255)
#: The stripe of each agent.
STRIPES: Tuple[RGBA, ...] = (
    (96, 228, 240, 255),
    (255, 120, 196, 255),
    (255, 220, 96, 255),
    (120, 232, 140, 255),
    (255, 158, 90, 255),
    (190, 150, 255, 255),
    (255, 255, 255, 255),
)

K = Kit(FRAME_SIZE)

ACTOR_METADATA = actor_metadata(
    "npc_agent_swarm",
    "Agent Swarm",
    attack_row="slash",
    ranged=False,
    traits=["ai_era", "swarm", "enemy"],
    description=(
        "The Agent Swarm is seven of the same small flying robot and the lines between them. No one of "
        "them has the plan: two of them are always voting, one for and one against."
    ),
    gameplay="A melee enemy. It moves as an arrowhead and attacks by closing into a spear and thrusting.",
)

#: Where each agent is in the cloud, from its middle.
CLOUD: Tuple[Point, ...] = ((0.0, 2.0), (-42.0, -23.0), (37.0, -30.0), (-48.0, 25.0), (46.0, 18.0), (-5.0, -53.0), (2.0, 50.0))
#: The arrowhead, its point before it.
ARROW: Tuple[Point, ...] = ((54.0, 0.0), (26.0, -24.0), (26.0, 24.0), (-2.0, -48.0), (-2.0, 48.0), (8.0, 0.0), (-38.0, 0.0))
#: The spear: a short point and a shaft.
SPEAR: Tuple[Point, ...] = ((56.0, 0.0), (28.0, -14.0), (28.0, 14.0), (0.0, 0.0), (-28.0, -8.0), (-28.0, 8.0), (-56.0, 0.0))
#: Where each lies when it has fallen: (x from the middle, how it is turned).
FALLEN: Tuple[Tuple[float, float], ...] = ((4.0, 84.0), (-52.0, -78.0), (52.0, 96.0), (-82.0, 100.0), (82.0, -84.0), (-24.0, 180.0), (28.0, -96.0))


# ---- The pose ----------------------------------------------------------------


def _pose(anim: str, i: int, n: int) -> List[Dict[str, object]]:
    """Each agent of the frame: where it is (from the middle of the cloud),
    which way it faces, its eye, how it is turned, whether its rotor turns."""
    ph = math.tau * i / max(1, n)
    agents: List[Dict[str, object]] = []
    for k in range(COUNT):
        own = k * 2.4
        agent: Dict[str, object] = {"at": CLOUD[k], "facing": 1, "eye": "open", "turn": 0.0, "rotor": True, "mark": None, "linked": True,
                                    "dead": False}
        if anim == "idle":
            x, y = CLOUD[k]
            # Each on its own beat.
            agent["at"] = (x + 2.5 * math.sin(ph + own), y + 3.2 * math.sin(ph * (2 if k % 3 == 0 else 1) + own * 1.7))
            agent["turn"] = 4.0 * math.sin(ph + own)
            agent["eye"] = "blink" if (i + k * 2) % 6 == 5 else "open"
            # Two of them vote.
            if k == 2:
                agent.update(facing=-1, mark="cross" if i in (2, 3, 4) else None)
            if k == 0:
                agent.update(mark="tick" if i in (0, 1, 2) else None)
        elif anim == "walk":
            x, y = ARROW[k]
            wave = math.sin(ph - x * 0.06)
            agent["at"] = (x + 2.0 * math.sin(ph * 2.0 + own), y + 4.0 * wave)
            agent["turn"] = 8.0 + 4.0 * wave
        elif anim == "slash":
            #  how far they have closed, how far the spear is thrust
            closed, thrust = ((0.6, -12.0), (1.0, -22.0), (1.0, 26.0), (1.0, 38.0), (0.7, 18.0), (0.2, 4.0))[i % 6]
            (cx, cy), (sx, sy) = CLOUD[k], SPEAR[k]
            agent["at"] = (lerp(cx, sx, closed) + thrust, lerp(cy, sy, closed))
            agent["eye"] = "angry" if 1 <= i <= 4 else "open"
            agent["turn"] = (0.0, -8.0, 12.0, 14.0, 8.0, 2.0)[i % 6]
        elif anim == "hurt":
            spread = (1.3, 1.5, 1.3, 1.1)[i % 4]
            x, y = CLOUD[k]
            agent["at"] = (x * spread - (6.0, 9.0, 6.0, 2.0)[i % 4], y * (1.0 + (spread - 1.0) * 0.4))
            agent["eye"] = "wide"
            agent["turn"] = (38.0, 60.0, 30.0, 8.0)[i % 4] * (1.0 if k % 2 else -1.0)
            agent["facing"] = 1 if k % 3 else -1
            agent["linked"] = i == 3
        elif anim == "death":
            # They drop one after another.
            fall = ease((i - k * 0.55) / 2.6)
            x, y = CLOUD[k]
            lie_x, lie_turn = FALLEN[k]
            agent["at"] = (lerp(x, lie_x, fall), lerp(y + 3.0 * math.sin(ph + own), HOVER - 15.0, fall * fall))
            agent["turn"] = lie_turn * fall
            agent["dead"] = fall > 0.02
            agent["eye"] = "dead" if fall > 0.02 else "wide"
            agent["rotor"] = fall < 0.02
            agent["linked"] = fall < 0.02
        agents.append(agent)
    return agents


# ---- Pieces ------------------------------------------------------------------


def _agent(k: int, facing: int, eye: str, dead: bool):
    """One agent, its middle at ``home``."""
    f = float(facing)
    z = SIZE
    stripe = STRIPES[k]

    def P(x: float, y: float) -> Point:
        return K.at(x * z, y * z)

    def box(d, x0: float, y0: float, x1: float, y1: float, radius: float, fill: RGBA) -> None:
        (ax, ay), (bx, by) = P(min(x0, x1), y0), P(max(x0, x1), y1)
        K.rrect(d, ax, ay, bx, by, radius * z, fill)

    def shape(d) -> None:
        box(d, -12.0, -10.0, 12.0, 10.0, 7.0, WHITE)
        K.stroke(d, [P(-3.0 * f, -9.0), P(-3.0 * f, -15.0)], WHITE, 2.6 * z)
        for x in (-5.0, 5.0):
            K.stroke(d, [P(x, 9.0), P(x * 1.2, 14.0)], WHITE, 2.4 * z)

    def detail(d) -> None:
        box(d, -13.0, 4.5, 13.0, 11.0, 0.0, stripe)
        box(d, -14.0, 9.5, 14.0, 16.0, 0.0, INK)
        box(d, -4.0 * f - 2.4, -16.0, -4.0 * f + 2.4, -12.0, 0.0, stripe)
        K.oval(d, P(-5.5, -5.5), 3.4 * z, 1.5 * z, (255, 255, 255, 90))
        c = P(4.0 * f, -2.0)
        r = 6.2 * z
        if eye == "dead":
            K.oval(d, c, r, r, (200, 204, 222, 255), INK, 0.9)
            K.cross(d, c, 2.8 * z, INK, 1.5 * z)
            return
        if eye == "blink":
            K.oval(d, c, r, r, BODY, INK, 0.9)
            K.stroke(d, [(c[0] - 4.0 * z, c[1]), (c[0] + 4.0 * z, c[1])], INK, 1.5 * z)
            return
        K.oval(d, c, r, r, EYE, INK, 0.9)
        pupil = (1.6 if eye == "wide" else 3.0) * z
        K.oval(d, (c[0] + (0.0 if eye == "wide" else 1.5 * f * z), c[1] + 0.3 * z), pupil, pupil, INK)
        if eye != "wide":
            K.oval(d, (c[0] + 0.6 * f * z, c[1] - 1.0 * z), 0.9 * z, 0.9 * z, WHITE)
        if eye == "angry":
            # A lid, down toward where it looks.
            lid = [(c[0] - 7.0 * f * z, c[1] - 7.0 * z), (c[0] + 7.0 * f * z, c[1] - 7.0 * z), (c[0] + 7.0 * f * z, c[1] - 0.6 * z),
                   (c[0] - 7.0 * f * z, c[1] - 4.6 * z)]
            K.poly(d, lid, BODY)
            K.line(d, [(c[0] - 6.0 * f * z, c[1] - 4.6 * z), (c[0] + 6.2 * f * z, c[1] - 0.8 * z)], INK, 1.3 * z)

    return K.solid(("agent", k, facing, eye, dead), shape, BODY_DEAD if dead else BODY, detail, outline=1.2)


def _rotor(wide: bool):
    """The rotor: a blur over the agent, from the top of its mast at ``home``."""

    def paint(d) -> None:
        K.oval(d, K.home, (12.0 if wide else 7.0) * SIZE, 2.3 * SIZE, (255, 255, 255, 150), INK, 0.6)
        K.oval(d, K.home, 1.6 * SIZE, 1.6 * SIZE, INK)

    return K.piece(("rotor", wide), paint)


def _link(length: float):
    """A line between two agents, from ``home`` along +x."""

    def paint(d) -> None:
        K.line(d, [K.home, K.at(length, 0.0)], LINK, 1.3)

    return K.piece(("link", length), paint)


def _bead():
    def paint(d) -> None:
        K.oval(d, K.home, 2.6, 2.6, (150, 224, 255, 120))
        K.oval(d, K.home, 1.5, 1.5, BEAD)

    return K.piece(("bead",), paint)


def _mark(kind: str):
    """A vote: a small bubble over an agent, from its tail at ``home``."""

    def shape(d) -> None:
        K.rrect(d, K.home[0] - 2.0, K.home[1] - 22.0, K.home[0] + 16.0, K.home[1] - 6.0, 5.0, WHITE)
        K.poly(d, [K.at(2.0, -8.0), K.home, K.at(8.0, -7.0)], WHITE)

    def detail(d) -> None:
        if kind == "tick":
            K.tick(d, K.at(7.0, -14.0), 4.2, GREEN, 2.2)
        else:
            K.cross(d, K.at(7.0, -14.0), 3.6, RED, 2.2)

    return K.solid(("mark", kind), shape, WHITE, detail, outline=1.0, rim=0.0, shade=0.0)


def _streak(length: float):
    """A line of speed behind the spear, from ``home`` back along -x."""

    def paint(d) -> None:
        K.stroke(d, [K.home, K.at(-length, 0.0)], (255, 255, 255, 170), 1.6)

    return K.piece(("streak", length), paint)


# ---- Frames ------------------------------------------------------------------


def _render_frame(anim: str, frame_idx: int, nframes: int) -> Image.Image:
    agents = _pose(anim, frame_idx, nframes)
    img = K.new_frame()
    middle = (CX, GROUND - HOVER)
    places = [(middle[0] + a["at"][0], middle[1] + a["at"][1]) for a in agents]  # type: ignore[index]

    # The lines between the ones that are near each other, and a bead on each.
    for a in range(COUNT):
        for b in range(a + 1, COUNT):
            if not (agents[a]["linked"] and agents[b]["linked"]):
                continue
            (ax, ay), (bx, by) = places[a], places[b]
            reach = math.hypot(bx - ax, by - ay)
            if reach > 70.0 or reach < 10.0:
                continue
            length = round(reach * 2.0) / 2.0
            turn = math.degrees(math.atan2(by - ay, bx - ax))
            K.place(img, _link(length), (ax, ay), f"link_{a}_{b}", turn)
            along = ((frame_idx / max(1, nframes)) + 0.37 * (a + b)) % 1.0
            K.place(img, _bead(), (ax + (bx - ax) * along, ay + (by - ay) * along), f"bead_{a}_{b}")

    if anim == "slash" and frame_idx in (2, 3):
        for k, (y, length) in enumerate(((-16.0, 26.0), (0.0, 34.0), (16.0, 22.0))):
            K.place(img, _streak(length), (places[6][0] - 22.0, middle[1] + y), f"streak_{k}")

    # The far ones first: the ones high in the cloud are behind.
    for k in sorted(range(COUNT), key=lambda k: places[k][1]):
        agent = agents[k]
        at, turn = places[k], float(agent["turn"])
        if agent["rotor"]:
            a = math.radians(turn)
            off = (-3.0 * int(agent["facing"]) * SIZE, -16.0 * SIZE)
            mast = (at[0] + off[0] * math.cos(a) - off[1] * math.sin(a), at[1] + off[0] * math.sin(a) + off[1] * math.cos(a))
            K.place(img, _rotor((frame_idx + k) % 2 == 0), mast, f"rotor_{k}", turn)
        K.place(img, _agent(k, int(agent["facing"]), str(agent["eye"]), bool(agent["dead"])), at, f"agent_{k}", turn)
        if agent["mark"] is not None:
            K.place(img, _mark(str(agent["mark"])), (at[0] + 8.0, at[1] - 16.0), f"mark_{k}")
    return K.downsample(img)


#: The gameplay body: the cloud as it stands, down to the ground under it.
BODY_BOX = (CX - 56.0, GROUND - HOVER - 70.0, CX + 58.0, GROUND + 1.0)


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    return K.render(TARGET_NAME, ROWS, _render_frame, out_dir, ACTOR_METADATA, BODY_BOX)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render the Agent Swarm sprite target.")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[2] / "generated" / TARGET_NAME)
    args = parser.parse_args(argv)
    for path in render(args.out_dir):
        print(path)
    return 0


TARGETS = {TARGET_NAME: {"render": render, "actor_metadata": ACTOR_METADATA}}


if __name__ == "__main__":
    raise SystemExit(main())
