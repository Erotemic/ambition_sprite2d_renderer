#!/usr/bin/env python3
"""How Full Stack's SVG was first drawn (reference, not authority).

    uv run python scripts/svg_art/full_stack_art.py

Writes ``data/characters/full_stack/full_stack.svg``; the SVG owns the art
after this has run once. ``JOINTS`` says where each part turns and ``LAYERS``
lists the parts; ``scripts/build_full_stack_rig.py`` reads both and authors
the rows.

Who it is (the game's ``docs/planning/game/final-boss.md``): the
bossofthegame's agent at its largest, the giant whose shoulders he stands on.
A square robot built like a guitar amplifier stack, seen from the front: a
robot's head of the 1960s on top (a riveted box of chrome with round bulb
eyes, a grille for a mouth, ear bolts and an antenna with a lamp on it), on a
short ribbed neck that rises out of the amp head; the amp head is its
shoulders (a gold panel of knobs, two VU meters, a handle), a 4x12 cabinet
for a body (four speaker cones behind the grille
cloth), two short boxy legs, two boxy arms, and a red electric guitar slung
across it, the neck up to the headstock past its left shoulder.

THE ART IS THE BODY. The numbers here are the game's (``npc_full_stack`` in
``character_catalog.ron``), at 1.25 world units to a frame pixel:

- the body box is ``BODY_BOX`` (the amp head, the cabinet and the legs; not
  the handle, the arms or the guitar): 320 x 384 px, 400 x 480 world;
- its top (``TOP_Y``) is the robot's back, where the Boss stands: the amp
  head's top, its shoulders. The robot's head stands over the middle of it
  (``ROBOT_HEAD_BOX``, not in the body box), so the Boss stands on the right
  shoulder beside it;
- the guitar's upper edge, from the strap end low at its right to the
  headstock past its left shoulder (``GUITAR_LINE``), is a line a body walks.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _cel_profile_kit as K  # noqa: E402
from _cel_profile_kit import capsule, cel, ellipse, line, path, smooth  # noqa: E402

ROOT = HERE.parents[1]
OUT = ROOT / "ambition_sprite2d_renderer" / "data" / "characters" / "full_stack" / "full_stack.svg"
VIEW = "Full Stack - Front"
SIZE = (600, 520)
GROUND_Y = 500.0
CENTER_X = 300.0
#: World units for each frame pixel (the catalog's `WorldPerPixel`).
WORLD_PER_PX = 1.25

#: The body box: amp head top to the soles, the cabinet's sides.
BODY_BOX = (140.0, 116.0, 460.0, 500.0)
TOP_Y = BODY_BOX[1]
#: The robot's head over the middle of the top: x0, y0, x1, y1 of its box.
ROBOT_HEAD_BOX = (246.0, 26.0, 354.0, 98.0)
#: The walkable upper edge of the guitar, strap end to headstock tip.
GUITAR_LINE = [(470.0, 430.0), (400.0, 372.0), (330.0, 340.0), (80.0, 150.0)]

PAL = dict(
    ink="#141418",
    tolex="#232329", tolex_sh="#141418", tolex_lt="#3a3a44",
    piping="#c8c8cc",
    cloth="#4a4238", cloth_sh="#342e27", cloth_lt="#5e5548",
    cone="#1e1c1a", cone_sh="#0e0d0c", cone_lt="#3a3632", cap="#8a8680",
    gold="#d8b048", gold_sh="#a07c28", gold_lt="#f2d888",
    knob="#1a1a1e", knob_lt="#6a6a72",
    meter="#f4e8c0", needle="#c03030", glow="#ff4a3a",
    metal="#8c919c", metal_sh="#5c616c", metal_lt="#b8bdc6", joint="#3a3e48",
    guitar="#c8282c", guitar_sh="#8a1a1e", guitar_lt="#ee5a50",
    neck="#7a4a26", neck_sh="#52301a", fret="#d8d8d8", string="#f0f0e8",
    pick_guard="#f2ece0", chrome="#d8dce4",
)

#: Where the drawing's joints are (frame px).
JOINTS: Dict[str, Tuple[float, float]] = dict(
    pelvis=(300.0, 440.0),
    neck=(300.0, 176.0),
    robot_neck=(300.0, 110.0),
    far_shoulder=(140.0, 200.0), far_elbow=(104.0, 300.0), far_wrist=(186.0, 238.0),
    near_shoulder=(460.0, 200.0), near_elbow=(506.0, 316.0), near_wrist=(420.0, 382.0),
    guitar=(380.0, 390.0),
    far_hip=(215.0, 440.0), near_hip=(385.0, 440.0),
)

#: Each bone: (parent, the joint it turns about). Parents first.
BONES = {
    "body": ("", "pelvis"),
    "torso": ("body", "pelvis"),
    "head": ("torso", "neck"),
    "robot_head": ("head", "robot_neck"),
    "guitar": ("torso", "guitar"),
    "far_arm_u": ("torso", "far_shoulder"),
    "far_arm_l": ("far_arm_u", "far_elbow"),
    "near_arm_u": ("torso", "near_shoulder"),
    "near_arm_l": ("near_arm_u", "near_elbow"),
    "far_leg": ("body", "far_hip"),
    "near_leg": ("body", "near_hip"),
}


def rect(x0, y0, x1, y1):
    return smooth([(x0, y0, True), (x1, y0, True), (x1, y1, True), (x0, y1, True)])


def leg(x0, x1):
    out = cel(rect(x0, 440, x1, 488), PAL["metal"], PAL["metal_sh"], PAL["metal_lt"], [line([(x0 + 6, 452), (x1 - 6, 452)], PAL["metal_sh"], 2.0)],
              s=(8, -2))
    out += cel(rect(x0 - 10, 486, x1 + 10, 500), PAL["joint"], PAL["tolex_sh"], None, s=(4, -1))
    return out


def cabinet():
    """The 4x12 cabinet: tolex, its piping, the grille cloth, four cones."""
    out = cel(rect(140, 176, 460, 442), PAL["tolex"], PAL["tolex_sh"], PAL["tolex_lt"], s=(12, -4))
    cones = []
    for cx in (222, 378):
        for cy in (244, 374):
            cones.append(ellipse(cx, cy, 58, 58, PAL["cone"]))
            cones.append(ellipse(cx, cy, 42, 42, PAL["cone_sh"]))
            cones.append(ellipse(cx, cy, 16, 16, PAL["cap"]))
            cones.append(ellipse(cx - 4, cy - 4, 6, 6, "#b8b4ae"))
    # the cloth over the cones lets them show through: a weave of light lines
    weave = [line([(156, y), (444, y)], PAL["cloth_lt"], 0.8) for y in range(192, 428, 10)]
    out += cel(rect(156, 190, 444, 428), PAL["cloth"], PAL["cloth_sh"], PAL["cloth_lt"], cones + weave, s=(6, -3))
    # the piping round the grille and a corner on each corner
    out.append(path(rect(154, 188, 446, 430), "none", PAL["piping"], 2.4))
    for x, y in ((140, 176), (448, 176), (140, 430), (448, 430)):
        out += cel(rect(x, y, x + 12, y + 12), PAL["chrome"], PAL["metal_sh"], None, s=(2, -1))
    # the brand plate
    out += cel(rect(268, 194, 332, 210), PAL["gold"], PAL["gold_sh"], PAL["gold_lt"],
               [line([(276, 202), (324, 202)], PAL["tolex"], 2.4)], s=(2, -1))
    return out


def head():
    """The amp head: its face is the gold panel of knobs, two VU meters for
    eyes, and the handle on top."""
    out = [line([(256, 117), (264, 104), (336, 104), (344, 117)], K.INK, 8.0),
           line([(256, 117), (264, 104), (336, 104), (344, 117)], PAL["tolex_lt"], 4.6)]
    out += cel(rect(146, 116, 454, 178), PAL["tolex"], PAL["tolex_sh"], PAL["tolex_lt"], s=(10, -3))
    knobs = []
    for i, x in enumerate((172, 196, 278, 300, 322, 404, 428)):
        knobs.append(ellipse(x, 156, 7, 7, PAL["knob"]))
        knobs.append(line([(x, 156), (x + 4, 150)], PAL["knob_lt"], 1.6))
    eyes = []
    for x in (238, 362):
        eyes.append(path(rect(x - 22, 136, x + 22, 166), PAL["meter"], K.INK, 1.4))
        eyes.append(path(smooth([(x - 18, 160), (x, 142), (x + 18, 160)]), "none", PAL["gold_sh"], 1.0))
        eyes.append(line([(x, 164), (x + 9, 145)], PAL["needle"], 2.0))
    out += cel(rect(156, 132, 444, 170), PAL["gold"], PAL["gold_sh"], PAL["gold_lt"], knobs + eyes, s=(3, -2))
    # an on-light
    out.append(ellipse(434, 124, 3.4, 3.4, PAL["glow"]))
    return out


ROBOT_EYES = ((276.0, 58.0), (324.0, 58.0))


def robot_head():
    """A robot's head as the 1960s drew one: a riveted box of chrome, two
    round bulb eyes in rings, a mouth that is a speaker grille, a bolt for
    each ear and an antenna with a lamp on it. A ribbed neck goes down into
    the amp head behind its handle."""
    x0, y0, x1, y1 = ROBOT_HEAD_BOX
    out = []
    # the neck: three ribs, behind the handle
    for i, y in enumerate((100.0, 106.0, 112.0)):
        out += cel(rect(286 - i, y - 3, 314 + i, y + 3), PAL["metal_sh"], PAL["joint"], PAL["metal"], s=(1, -1))
    # the antenna and its lamp
    out.append(line([(300, y0), (300, 9)], K.INK, 5.0))
    out.append(line([(300, y0), (300, 9)], PAL["metal_lt"], 2.6))
    out.append(ellipse(300, 7, 6.5, 6.5, PAL["glow"]))
    out.append(ellipse(298, 5, 2.2, 2.2, "#ffd0c8"))
    # the ears: a drum on each side with a bolt in it
    for ex, sx in ((x0 - 9, -1), (x1 + 9, 1)):
        out += cel(rect(ex - 8, 44, ex + 8, 80), PAL["metal_sh"], PAL["joint"], PAL["metal"], s=(2, -1))
        out.append(ellipse(ex, 62, 5.0, 5.0, PAL["chrome"]))
        out.append(line([(ex + sx * 4, 46), (ex + sx * 12, 34)], PAL["metal_lt"], 2.0))
        out.append(ellipse(ex + sx * 12, 34, 2.6, 2.6, PAL["gold"]))
    # the box, its face plate, its rivets
    face = []
    face.append(path(rect(x0 + 10, y0 + 12, x1 - 10, y1 - 8), PAL["metal_sh"], K.INK, 1.2))
    for (ex, ey) in ROBOT_EYES:
        face.append(ellipse(ex, ey, 15.0, 15.0, PAL["chrome"]))
        face.append(ellipse(ex, ey, 11.0, 11.0, PAL["cone_sh"]))
        face.append(ellipse(ex, ey, 7.5, 7.5, PAL["glow"]))
        face.append(ellipse(ex - 2.5, ey - 2.5, 2.4, 2.4, "#ffe0d8"))
    # the mouth: a grille of bars, like the cabinet below it
    face.append(path(rect(268, 76, 332, 88), PAL["cone_sh"], K.INK, 1.0))
    face += [line([(x, 77.5), (x, 86.5)], PAL["metal_lt"], 1.4) for x in range(274, 330, 7)]
    for rx in (x0 + 5, x1 - 5):
        for ry in (y0 + 5, y1 - 5):
            face.append(ellipse(rx, ry, 2.2, 2.2, PAL["chrome"]))
    out += cel(rect(x0, y0, x1, y1), PAL["metal"], PAL["metal_sh"], PAL["metal_lt"], face, s=(7, -3))
    return out


def robot_eye_glow():
    """Its bulb eyes and its antenna lamp flare with the feedback."""
    out = [K.glow(ex, ey, 24, 24, PAL["glow"], alpha=0.6) for ex, ey in ROBOT_EYES]
    out.append(K.glow(300, 7, 16, 16, PAL["glow"], alpha=0.6))
    return out


def eye_glow():
    """The meters pinned in the red, and the cones glowing: feedback."""
    out = []
    for x in (238, 362):
        out.append(K.glow(x, 151, 30, 22, PAL["glow"], alpha=0.55))
    for cx in (222, 378):
        for cy in (244, 374):
            out.append(K.glow(cx, cy, 60, 60, PAL["glow"], alpha=0.32))
    return out


def arm_upper(sh, el):
    return cel(capsule(sh, el, 20.0, 17.0), PAL["metal"], PAL["metal_sh"], PAL["metal_lt"], [ellipse(sh[0], sh[1], 12, 12, PAL["joint"])],
               s=(6, -3))


def arm_lower(el, wr):
    out = cel(capsule(el, wr, 16.0, 14.0), PAL["metal"], PAL["metal_sh"], PAL["metal_lt"], [ellipse(el[0], el[1], 10, 10, PAL["joint"])],
              s=(5, -3))
    out += cel(smooth([(wr[0] - 16, wr[1] - 12), (wr[0] + 16, wr[1] - 14), (wr[0] + 18, wr[1] + 12), (wr[0] - 14, wr[1] + 14)]),
               PAL["metal_sh"], PAL["joint"], PAL["metal"], s=(3, -2))
    return out


#: The strings, each this far across the neck's line from its middle: the
#: same on the neck and on the body, so they run straight and parallel from
#: the bridge to the nut.
STRING_OFFSETS = (-6.0, -2.0, 2.0, 6.0)
#: How far down the line from the neck's foot the bridge is.
BRIDGE_T = 108.0


def guitar():
    """A red electric guitar slung across the cabinet: its body low at the
    right, the neck up to the headstock past the left shoulder. The upper
    edge is ``GUITAR_LINE``."""
    out = []
    # the neck, from the body to the headstock
    a, b = (346.0, 352.0), (98.0, 164.0)
    n = K.along(a, b)
    length = ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
    neck = smooth([n(0, -10) + (True,), n(length, -10) + (True,), n(length, 10) + (True,), n(0, 10) + (True,)])
    frets = [line([n(t, -9), n(t, 9)], PAL["fret"], 1.2) for t in range(16, int(length) - 8, 18)]
    strings = [line([n(0, s), n(length, s)], PAL["string"], 0.6) for s in STRING_OFFSETS]
    out += cel(neck, PAL["neck"], PAL["neck_sh"], None, frets + strings, s=(3, 2))
    # the headstock and its tuners
    h = K.along(b, (b[0] - (a[0] - b[0]) * 0.2, b[1] - (a[1] - b[1]) * 0.2))
    hs = smooth([h(-2, -12), h(42, -16), h(48, 0), h(42, 16), h(-2, 12)])
    out += cel(hs, PAL["guitar"], PAL["guitar_sh"], PAL["guitar_lt"],
               [ellipse(*h(t, s), 3.2, 3.2, PAL["chrome"]) for t in (14, 30) for s in (-9, 9)], s=(3, 2))
    # the body
    body = smooth([(332, 344), (366, 330), (404, 352), (440, 366), (478, 404), (480, 440), (452, 470), (404, 470), (366, 456),
                   (332, 440), (318, 404), (322, 370)])
    # The pickups and the bridge sit square across the strings' line, which
    # goes on from the neck's (`n` with t below 0 runs down into the body).
    def across(t0, t1, half):
        return smooth([n(t0, -half) + (True,), n(t1, -half) + (True,), n(t1, half) + (True,), n(t0, half) + (True,)])
    items = [
        path(smooth([(350, 400), (380, 372), (420, 388), (440, 430), (420, 456), (370, 448)]), PAL["pick_guard"]),
        path(across(-44, -32, 12), PAL["chrome"], K.INK, 1.2),
        path(across(-78, -66, 12), PAL["chrome"], K.INK, 1.2),
        path(across(-BRIDGE_T - 5, -BRIDGE_T + 5, 11), PAL["tolex"], K.INK, 1.0),
        ellipse(456, 444, 6, 6, PAL["gold"]),
        ellipse(466, 428, 6, 6, PAL["gold"]),
    ]
    items += [line([n(-BRIDGE_T, s), n(0, s)], PAL["string"], 0.6) for s in STRING_OFFSETS]
    out += cel(body, PAL["guitar"], PAL["guitar_sh"], PAL["guitar_lt"], items, s=(8, -4))
    # the strap button at the low end
    out.append(ellipse(476, 432, 3.4, 3.4, PAL["chrome"]))
    return out


#: The parts, in the order they are drawn: (group id, label, part, bone, z, opacity channel).
LAYERS = [
    ("far-leg", "Far Leg", "far_leg", "far_leg", 10, ""),
    ("near-leg", "Near Leg", "near_leg", "near_leg", 11, ""),
    ("far-arm-upper", "Far Arm - Upper", "far_arm_u", "far_arm_u", 20, ""),
    ("near-arm-upper", "Near Arm - Upper", "near_arm_u", "near_arm_u", 21, ""),
    ("torso", "Cabinet", "torso", "torso", 30, ""),
    ("robot-head", "Robot Head", "robot_head", "robot_head", 35, ""),
    ("robot-glow", "Robot Eye Glow", "robot_glow", "robot_head", 36, "glow"),
    ("head", "Amp Head", "head", "head", 40, ""),
    ("glow", "Feedback Glow", "glow", "head", 41, "glow"),
    ("guitar", "Guitar", "guitar", "guitar", 50, ""),
    ("far-arm-lower", "Far Arm - Lower", "far_arm_l", "far_arm_l", 60, ""),
    ("near-arm-lower", "Near Arm - Lower", "near_arm_l", "near_arm_l", 61, ""),
]


def drawn() -> Dict[str, list]:
    J = JOINTS
    return {
        "far-leg": leg(180, 250), "near-leg": leg(350, 420),
        "far-arm-upper": arm_upper(J["far_shoulder"], J["far_elbow"]),
        "near-arm-upper": arm_upper(J["near_shoulder"], J["near_elbow"]),
        "torso": cabinet(), "head": head(), "glow": eye_glow(), "guitar": guitar(),
        "robot-head": robot_head(), "robot-glow": robot_eye_glow(),
        "far-arm-lower": arm_lower(J["far_elbow"], J["far_wrist"]),
        "near-arm-lower": arm_lower(J["near_elbow"], J["near_wrist"]),
    }


def svg_text() -> str:
    K.begin(PAL["ink"], 1.8)
    parts = drawn()
    for group, label, name, bone, z, channel in LAYERS:
        K.part(group, label, name, bone, z, parts[group], channel)
    return K.document(
        design="full-stack", layer_id="full_stack", label=VIEW,
        comment=["  <!-- Full Stack: the front, the ground at y=500, 1.25 world units to a pixel.",
                 "       Drawn by scripts/svg_art/full_stack_art.py; each part turns about its bone's joint. -->"],
        joints=dict(JOINTS), size=SIZE,
    )


def world(p):
    """A frame point as the game's offset from the body box's centre."""
    cx = (BODY_BOX[0] + BODY_BOX[2]) / 2
    cy = (BODY_BOX[1] + BODY_BOX[3]) / 2
    return (round((p[0] - cx) * WORLD_PER_PX, 1), round((p[1] - cy) * WORLD_PER_PX, 1))


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".svg.tmp")
    tmp.write_text(svg_text(), encoding="utf8")
    tmp.replace(OUT)
    print(f"wrote {OUT.relative_to(ROOT)}")
    print("top (world):", world((BODY_BOX[0], TOP_Y)), world((BODY_BOX[2], TOP_Y)))
    print("guitar line (world):", [world(p) for p in GUITAR_LINE])


if __name__ == "__main__":
    main()
