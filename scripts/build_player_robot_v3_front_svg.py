"""Write the first drawing of player robot v3 seen from the FRONT.

    uv run python scripts/build_player_robot_v3_front_svg.py [--force]

The output is ``data/characters/player_robot_v3_svg/player-robot-v3-front.svg``:
one view layer, ``Player Robot - Front``, with the same contract as the side
and the back views (part groups, joint markers, depth on each part). The
turnaround draws its middle frames from it.

⛔ After this script writes the file, the SVG is the authority. An artist edits
it in Inkscape. The script does not write the file again unless ``--force`` is
given, because that replaces the edits.

The joints, the colours, the line weight and the limb shapes are those of the
back view (``build_player_robot_v3_back_svg.py``), mirrored: the robot's
right side ("near", the side of its one ear cup and antenna) is at the LEFT
of this picture. The face is the side view's visor and eyes seen face on, and
the chest has the side view's cyan light.

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
from typing import Sequence

from build_player_robot_v3_back_svg import (
    ANKLE, ANTENNA_AT, ANTENNA_BALL, ANTENNA_TUBE, ANTENNA_TURN, BOOT, BOOT_SOLE, CX, EAR_CUP,
    EAR_CUP_AT, EAR_CUP_LIGHT, ELBOW, FOREARM, HAND, HAND_D, HAND_LINES, HANDTIP, HEAD, HIP, HIP_Y,
    INK, KNEE, LINK, NECK, NECK_FILL, PELVIS, PELVIS_D, PURPLE, SHOULDER, STROKE, TOE, TORSO, WAIST,
    WHITE, WRIST, Layer, Point, _fmt, along, link, path, placed, style,
)

ROOT = Path(__file__).resolve().parents[1]
SVG_PATH = ROOT / "ambition_sprite2d_renderer/data/characters/player_robot_v3_svg/player-robot-v3-front.svg"
VIEW_LABEL = "Player Robot - Front"

EYE = "#0defff"
VISOR = "#000000"

# The head is as high as the side view's (39 against the back view's 34.6).
# The back view is lower because the camera is below it; a front view that
# low read as a robot that looks up (Jon, 2026-10-13).
HEAD_HIGH = 39.0 / 34.6
# The visor, from the neck: the side view's black screen seen face on. It is
# in the lower half of the shell, where the side view has it, so the eyes look
# straight ahead.
VISOR_D = ("M -12,-29 C -4,-29.8 4,-29.8 12,-29 C 16.4,-28.4 17.2,-25.2 17.2,-17.2 "
           "C 17.2,-10 16.2,-7 12,-6.2 C 4,-5.2 -4,-5.2 -12,-6.2 C -16.2,-7 -17.2,-10 -17.2,-17.2 "
           "C -17.2,-25.2 -16.4,-28.4 -12,-29 Z")
# The two eyes: the side view's tall cyan ovals, a little below the middle of
# the visor.
EYES = ((-6.0, -16.6), (6.0, -16.6))
EYE_RX, EYE_RY = 2.4, 5.6
# The chest light, from the waist: the side view's cyan icon seen face on.
CHEST_LIGHT = "M -2.6,-11.6 L 2.6,-11.6 L 2.8,-6.6 L -2.8,-6.6 Z"


def build_layer() -> Layer:
    layer = Layer()
    # "near" is the robot's right side: the LEFT of this picture.
    for side, sgn in (("far", 1.0), ("near", -1.0)):
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
        # The forearm and the hand hang beside the torso, in front of its edge.
        layer.part(f"{side}_arm_l", f"Lower Arm - {title}", f"{side}_arm_l", 44 + step, [
            path(placed(FOREARM, elbow, along(elbow, wrist)), WHITE),
        ])
        layer.part(f"{side}_hand", f"Hand - {title}", f"{side}_arm_hand", 45 + step, [
            path(placed(HAND_D, wrist, along(wrist, handtip)), HAND),
            *(path(placed(d, wrist, along(wrist, handtip)), "none", 0.75, "#2b2b2b") for d in HAND_LINES),
        ])
        for name, point in (("shoulder", shoulder), ("elbow", elbow), ("wrist", wrist), ("handtip", handtip),
                            ("hip", hip), ("knee", knee), ("ankle", ankle), ("toe", toe)):
            layer.joint(f"{side}_{name}", point)

    hips = (CX, HIP_Y)
    layer.part("pelvis_front", "Pelvis", "pelvis", 30, [path(placed(PELVIS_D, hips), PELVIS)])
    layer.part("neck_ring", "Neck Ring", "torso", 38, [
        f'<rect style="{style(NECK_FILL)}" x="{_fmt(CX - 7.6)}" y="{_fmt(NECK[1] - 1.5)}" width="15.2" height="7" />',
    ])
    layer.part("torso_front", "Torso Front", "torso", 40, [
        path(placed(TORSO, WAIST), WHITE),
        path(placed(CHEST_LIGHT, WAIST), "#00f5fc"),
    ])
    # The ear cup and the antenna are on the robot's right ear: the left of
    # this picture, the back view's placement mirrored.
    antenna = (NECK[0] - ANTENNA_AT[0], NECK[1] + ANTENNA_AT[1] * HEAD_HIGH)
    turn = -ANTENNA_TURN
    c, s = math.cos(math.radians(turn)), math.sin(math.radians(turn))
    (bx, by), radius = ANTENNA_BALL
    bx = -bx
    layer.part("antenna_near", "Antenna", "head", 59.1, [
        path(placed(ANTENNA_TUBE, antenna, turn, flip=True), PURPLE),
        f'<circle style="{style(PURPLE)}" cx="{_fmt(antenna[0] + bx * c - by * s)}" cy="{_fmt(antenna[1] + bx * s + by * c)}" r="{_fmt(radius)}" />',
    ])
    cup = (NECK[0] - EAR_CUP_AT[0], NECK[1] + EAR_CUP_AT[1] * HEAD_HIGH)
    layer.part("head_side", "Head Side (the ear cup, on its edge)", "head", 59.5, [
        path(placed(EAR_CUP, cup, flip=True), PURPLE),
        f'<path style="fill:none;stroke:#fefefe;stroke-width:0.565;stroke-linecap:round;stroke-opacity:0.457964" d="{placed(EAR_CUP_LIGHT, cup, flip=True)}" />',
    ])
    tall_head = re.sub(
        r"(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)",
        lambda m: f"{m.group(1)},{_fmt(float(m.group(2)) * HEAD_HIGH)}",
        HEAD,
    )
    layer.part("head", "Head (the front of the shell)", "head", 60, [path(placed(tall_head, NECK), WHITE)])
    layer.part("face_open", "Face / Visor - Open", "head", 61, [
        path(placed(VISOR_D, NECK), VISOR, STROKE, INK),
        *(
            f'<ellipse style="fill:{EYE};fill-opacity:1;stroke:none" cx="{_fmt(NECK[0] + x)}" cy="{_fmt(NECK[1] + y)}" '
            f'rx="{_fmt(EYE_RX)}" ry="{_fmt(EYE_RY)}" />'
            for x, y in EYES
        ),
    ])
    layer.joint("waist", WAIST)
    layer.joint("neck", NECK)
    return layer


def document() -> str:
    layer = build_layer()
    parts = "\n".join(body for _z, body in sorted(layer.parts, key=lambda item: item[0]))
    joints = "\n".join(layer.joints)
    # The ids of the back view's helper start with "back-"; this view's are
    # its own.
    parts = parts.replace('id="back-', 'id="front-').replace('id="part-back-', 'id="part-front-')
    joints = joints.replace('id="joint-back-', 'id="joint-front-')
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
   width="68mm"
   height="92mm"
   viewBox="228 116 68 92"
   version="1.1"
   id="player-robot-front-svg"
   xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
   xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
   xmlns="http://www.w3.org/2000/svg"
   xmlns:svg="http://www.w3.org/2000/svg">
  <!--Player Robot v3 from the front. Part grouping, depth, and joint markers are authored here.-->
  <g
     id="view-player-robot-front"
     inkscape:label="{VIEW_LABEL}"
     inkscape:groupmode="layer">
{parts}
    <g
       id="front-joint-markers"
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
