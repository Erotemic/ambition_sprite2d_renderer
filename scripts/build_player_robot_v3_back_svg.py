"""Write the first drawing of player robot v3 seen from BEHIND.

    uv run python scripts/build_player_robot_v3_back_svg.py [--force]

⛔ HISTORY ONLY (2026-10-21): the view this wrote is now a layer of
``player-robot-v3.svg``, a cell of its grid of views
(``merge_player_robot_v3_views.py``), and that file is the authority. Do not
run this again.

The output was ``data/characters/player_robot_v3_svg/player-robot-v3-back.svg``:
one view layer, ``Player Robot - Back``, with the same contract as the side
view (part groups, joint markers, depth on each part).

⛔ After this script writes the file, the SVG is the authority. An artist edits
it in Inkscape. The script does not write the file again unless ``--force`` is
given, because that replaces the edits.

The colours, the line weight and the sizes come from the side view
(``player-robot-v3.svg``). The shapes are new: a back view shows faces of the
parts that the side view does not have.

Rulings (Jon, 2026-10-13):

* The robot has ONE antenna. It stands in the one ear cup. The ear cup is on
  the robot's right ear, which is at the right of this picture.
* The back of the head and the back of the torso have no features.
* The head is less high than in the side view (the camera is below it).

After a change of the SVG, build the rig again
(``scripts/build_player_robot_v3_svg.py``). After ``--force``, also put the rig
catalog block back in the new file:
``python -m ambition_sprite2d_renderer.devtools.svg_rig_tool bootstrap-repo .``
"""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path
from typing import List, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
SVG_PATH = ROOT / "ambition_sprite2d_renderer/data/characters/player_robot_v3_svg/player-robot-v3-back.svg"
VIEW_LABEL = "Player Robot - Back"

Point = Tuple[float, float]

WHITE, INK, PURPLE = "#ffffff", "#000000", "#cb1fff"
LINK, HAND, PELVIS, NECK_FILL = "#131313", "#101010", "#070707", "#222222"
STROKE = 1.5

# The column of the neck and the floor are those of the side view.
CX, GROUND = 262.0, 206.0
NECK: Point = (CX, 164.0)
WAIST: Point = (CX, 181.0)
HIP_Y = 184.0

# Joints, as (distance from the column, y). "near" is the robot's right side:
# the side of the ear cup, at the right of this picture. The builder reads a
# marker to half a unit, so each joint is on a whole unit.
#
# The legs are shorter than in the side view (17.2 against 20.1): in a climb
# the knees point at the wall, and the picture shows less of the leg.
SHOULDER, ELBOW, WRIST, HANDTIP = (13.0, 169.0), (17.0, 174.0), (18.0, 183.0), (18.0, 189.0)
HIP, KNEE, ANKLE, TOE = (5.0, HIP_Y), (7.0, 192.0), (7.0, 201.0), (7.0, 206.0)

# ── The art, each part in its own space ──────────────────────────────────────
# A limb part is drawn from its joint (0, 0) with +y along the bone.

HEAD = ("M -11,-34 C -4,-34.6 4,-34.6 11,-34 C 19.8,-33.1 23,-27.9 23,-17.7 "
        "C 23,-7.8 20.6,-2 13,-0.5 C 6,0.8 -6,0.8 -13,-0.5 C -20.6,-2 -23,-7.8 -23,-17.7 "
        "C -23,-27.9 -19.8,-33.1 -11,-34 Z")
ANTENNA_TUBE = "M -1.8,0.6 L -2.1,-15 L 1.6,-15.4 L 1.8,0.6 Z"
ANTENNA_BALL = ((-0.3, -18.4), 5.1)
ANTENNA_AT, ANTENNA_TURN = (24.2, -19.0), 5.0
EAR_CUP = "M -3,-7.7 C 3.6,-7.9 6.2,-3.6 6.2,0 C 6.2,3.6 3.6,7.9 -3,7.7 Z"
EAR_CUP_LIGHT = "M 3.2,-4.7 C 4.4,-1.8 4.4,1.8 3.2,4.7"
EAR_CUP_AT = (22.0, -13.7)

TORSO = ("M -9.5,-16.4 L 9.5,-16.4 C 12.5,-16.3 14.3,-15.7 14.8,-13.4 C 15.2,-9 14,-3.5 11,0.3 "
         "C 7,0.9 -7,0.9 -11,0.3 C -14,-3.5 -15.2,-9 -14.8,-13.4 C -14.3,-15.7 -12.5,-16.3 -9.5,-16.4 Z")
PELVIS_D = "M -10.6,-3.3 C -11.2,-0.7 -9.6,2.2 -7,2.9 C -3,3.7 3,3.7 7,2.9 C 9.6,2.2 11.2,-0.7 10.6,-3.3 Z"
FOREARM = ("M -2.7,-1.3 C -5.6,1.4 -6.5,6 -5.5,10 C -2.5,8.9 2.5,8.9 5.5,10 "
           "C 6.5,6 5.6,1.4 2.7,-1.3 C 1,-2.1 -1,-2.1 -2.7,-1.3 Z")
HAND_D = ("M -4.4,-0.8 C -5.4,2.2 -5.1,5.6 -3.5,7.3 C -1.5,8.4 1.5,8.4 3.5,7.3 "
          "C 5.1,5.6 5.4,2.2 4.4,-0.8 C 2,-1.7 -2,-1.7 -4.4,-0.8 Z")
HAND_LINES = ("M -1.5,4.6 L -1.5,7.4", "M 1.5,4.6 L 1.5,7.4")
# The boot from the heel. Its bone goes from the ankle straight down to the sole.
# The sole is at 4.2: with the line it ends on the floor, as the side view's does.
BOOT = "M -4.2,-9 C -2,-10 2,-10 4.2,-9 C 5.7,-5 6.5,-0.4 6.4,4.2 L -6.4,4.2 C -6.5,-0.4 -5.7,-5 -4.2,-9 Z"
BOOT_SOLE = "M -6.3,1.6 C -3,0.4 3,0.4 6.3,1.6"


def _fmt(value: float) -> str:
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def placed(d: str, at: Point, turn: float = 0.0, flip: bool = False) -> str:
    """Path data ``d`` (absolute M, L, C, Z) turned, mirrored and moved."""
    c, s = math.cos(math.radians(turn)), math.sin(math.radians(turn))
    out: List[str] = []
    for token in re.findall(r"[MLCZ]|-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?", d):
        if token in "MLCZ":
            out.append(token)
            continue
        x, y = (float(v) for v in token.split(","))
        if flip:
            x = -x
        out.append(f"{_fmt(at[0] + x * c - y * s)},{_fmt(at[1] + x * s + y * c)}")
    return " ".join(out)


def along(a: Point, b: Point) -> float:
    """The turn that puts a part's own +y on the line from ``a`` to ``b``."""
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) - 90.0


def link(a: Point, b: Point, width: float) -> str:
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    px, py = -dy / n * width / 2.0, dx / n * width / 2.0
    pts = [(a[0] + px, a[1] + py), (b[0] + px, b[1] + py), (b[0] - px, b[1] - py), (a[0] - px, a[1] - py)]
    return "M " + " L ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in pts) + " Z"


def style(fill: str, width: float = STROKE, stroke: str = INK, extra: str = "") -> str:
    return (f"fill:{fill};fill-opacity:1;stroke:{stroke};stroke-width:{_fmt(width)};"
            f"stroke-linecap:round;stroke-linejoin:round;stroke-opacity:1{extra}")


class Layer:
    """The part groups and the joint markers of the view, with stable ids."""

    def __init__(self) -> None:
        self.parts: List[Tuple[float, str]] = []
        self.joints: List[str] = []

    def part(self, name: str, label: str, bone: str, z: float, shapes: Sequence[str]) -> None:
        slug = name.replace("_", "-")
        # Each shape starts with its tag; the id goes in after the tag name.
        body = "\n".join(
            "      " + re.sub(r"^<(\w+)", lambda m, i=i: f'<{m.group(1)} id="back-{slug}-{i}"', shape, count=1)
            for i, shape in enumerate(shapes)
        )
        self.parts.append((z, (
            f'    <g\n       id="part-back-{slug}"\n       inkscape:label="{label}"\n'
            f'       inkscape:groupmode="layer"\n       data-rig-part="{name}"\n'
            f'       data-rig-bone="{bone}"\n       data-rig-z="{_fmt(z)}">\n{body}\n    </g>'
        )))

    def joint(self, name: str, at: Point) -> None:
        label = name.replace("_", " ").title()
        self.joints.append(
            f'      <circle\n         id="joint-back-{name.replace("_", "-")}"\n'
            f'         inkscape:label="{label}"\n         cx="{_fmt(at[0])}"\n         cy="{_fmt(at[1])}"\n'
            f'         r="0.78"\n         style="fill:#ff3eb5;fill-opacity:0.42;stroke:#17120e;stroke-width:0.32"\n'
            f'         data-rig-joint="{name}" />'
        )


def path(d: str, fill: str, width: float = STROKE, stroke: str = INK, extra: str = "") -> str:
    return f'<path style="{style(fill, width, stroke, extra)}" d="{d}" />'


def build_layer() -> Layer:
    layer = Layer()
    for side, sgn in (("far", -1.0), ("near", 1.0)):
        step = 0.0 if side == "far" else 0.1

        def at(joint: Point) -> Point:
            return (CX + sgn * joint[0], joint[1])

        shoulder, elbow, wrist, handtip = at(SHOULDER), at(ELBOW), at(WRIST), at(HANDTIP)
        hip, knee, ankle, toe = at(HIP), at(KNEE), at(ANKLE), at(TOE)
        title = side.title()
        layer.part(f"{side}_leg_u", f"Upper Leg - {title}", f"{side}_leg_u", 14 + step, [path(link(hip, knee, 5.4), LINK)])
        layer.part(f"{side}_leg_l", f"Lower Leg Link - {title}", f"{side}_leg_l", 15 + step, [path(link(knee, ankle, 3.8), LINK)])
        layer.part(f"{side}_foot", f"Complete Boot / Foot - {title}", f"{side}_leg_foot", 16 + step, [
            path(placed(BOOT, ankle, along(ankle, toe)), WHITE),
            path(placed(BOOT_SOLE, ankle, along(ankle, toe)), "none"),
        ])
        layer.part(f"{side}_arm_u", f"Upper Arm - {title}", f"{side}_arm_u", 26 + step, [path(link(shoulder, elbow, 4.9), LINK)])
        layer.part(f"{side}_arm_l", f"Lower Arm - {title}", f"{side}_arm_l", 27 + step, [
            path(placed(FOREARM, elbow, along(elbow, wrist)), WHITE),
        ])
        layer.part(f"{side}_hand", f"Hand - {title}", f"{side}_arm_hand", 28 + step, [
            path(placed(HAND_D, wrist, along(wrist, handtip)), HAND),
            *(path(placed(d, wrist, along(wrist, handtip)), "none", 0.75, "#2b2b2b") for d in HAND_LINES),
        ])
        for name, point in (("shoulder", shoulder), ("elbow", elbow), ("wrist", wrist), ("handtip", handtip),
                            ("hip", hip), ("knee", knee), ("ankle", ankle), ("toe", toe)):
            layer.joint(f"{side}_{name}", point)

    hips = (CX, HIP_Y)
    layer.part("pelvis_back", "Pelvis", "pelvis", 30, [path(placed(PELVIS_D, hips), PELVIS)])
    layer.part("neck_ring", "Neck Ring", "torso", 38, [
        f'<rect style="{style(NECK_FILL)}" x="{_fmt(CX - 7.6)}" y="{_fmt(NECK[1] - 1.5)}" width="15.2" height="7" />',
    ])
    layer.part("torso_back", "Torso Back", "torso", 40, [path(placed(TORSO, WAIST), WHITE)])
    antenna = (NECK[0] + ANTENNA_AT[0], NECK[1] + ANTENNA_AT[1])
    c, s = math.cos(math.radians(ANTENNA_TURN)), math.sin(math.radians(ANTENNA_TURN))
    (bx, by), radius = ANTENNA_BALL
    layer.part("antenna_near", "Antenna", "head", 59.1, [
        path(placed(ANTENNA_TUBE, antenna, ANTENNA_TURN), PURPLE),
        f'<circle style="{style(PURPLE)}" cx="{_fmt(antenna[0] + bx * c - by * s)}" cy="{_fmt(antenna[1] + bx * s + by * c)}" r="{_fmt(radius)}" />',
    ])
    cup = (NECK[0] + EAR_CUP_AT[0], NECK[1] + EAR_CUP_AT[1])
    layer.part("head_side", "Head Side (the ear cup, on its edge)", "head", 59.5, [
        path(placed(EAR_CUP, cup), PURPLE),
        f'<path style="fill:none;stroke:#fefefe;stroke-width:0.565;stroke-linecap:round;stroke-opacity:0.457964" d="{placed(EAR_CUP_LIGHT, cup)}" />',
    ])
    layer.part("head", "Head (the back of the shell)", "head", 60, [path(placed(HEAD, NECK), WHITE)])
    layer.joint("waist", WAIST)
    layer.joint("neck", NECK)
    return layer


def document() -> str:
    layer = build_layer()
    parts = "\n".join(body for _z, body in sorted(layer.parts, key=lambda item: item[0]))
    joints = "\n".join(layer.joints)
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
   width="68mm"
   height="92mm"
   viewBox="228 116 68 92"
   version="1.1"
   id="player-robot-back-svg"
   xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
   xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
   xmlns="http://www.w3.org/2000/svg"
   xmlns:svg="http://www.w3.org/2000/svg">
  <!--Player Robot v3 from behind. Part grouping, depth, and joint markers are authored here.-->
  <g
     id="view-player-robot-back"
     inkscape:label="{VIEW_LABEL}"
     inkscape:groupmode="layer">
{parts}
    <g
       id="back-joint-markers"
       inkscape:label="Joint Markers"
       inkscape:groupmode="layer">
{joints}
    </g>
  </g>
</svg>
'''


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--force", action="store_true", help="replace the SVG (and the edits an artist made in it)")
    args = parser.parse_args(argv)
    if SVG_PATH.exists() and not args.force:
        raise SystemExit(f"{SVG_PATH} exists; it is the authority now. Give --force to replace it.")
    SVG_PATH.write_text(document(), encoding="utf8")
    print(SVG_PATH)


if __name__ == "__main__":
    main()
