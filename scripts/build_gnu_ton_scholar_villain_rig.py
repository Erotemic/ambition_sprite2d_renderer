#!/usr/bin/env python3
"""Build GNU-ton scholar's articulated SVG rig and actual pose clips.

This is a non-destructive candidate target, separate from the existing
``gnu_ton_rider`` boss atlas. Run the SVG author first, then this builder:

    cd tools/ambition_sprite2d_renderer
    python scripts/svg_art/gnu_ton_scholar_villain_art.py
    python scripts/build_gnu_ton_scholar_villain_rig.py

The result is an ``ambition-svg-rig-v1`` SVG with a validated embedded catalog,
plus a RigDocument registered under the real sprite renderer's ``rigged``
registry. It does NOT switch the current game's rider art on automatically.
"""

from __future__ import annotations

import math
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ambition_sprite2d_renderer.rigbuild import creature_rig as CR  # noqa: E402
from ambition_sprite2d_renderer.rigbuild import humanoid as H  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts" / "svg_art"))
from scholar_svg_labels import label_generated_rig_guides, write_object_inventory  # noqa: E402

PACKAGE = ROOT / "ambition_sprite2d_renderer"
ART = PACKAGE / "data/characters/gnu_ton_scholar_villain/gnu_ton_scholar_villain.svg"
RIG = PACKAGE / "targets/characters/rigged/gnu_ton_scholar_villain.rig.json"
CX, GROUND = 236.0, 478.0
SCALE = 0.46
BODY = H.Body.from_svg(ART, CX, GROUND)


def g(x, lift=0.0, pitch=0.0):
    return ("g", float(x), float(lift), float(pitch))


def b(dx=0.0, dy=0.0, pitch=0.0):
    return ("b", float(dx), float(dy), float(pitch))


# Rest is authored to match the drawn joint geometry. No corrective offset is
# required to hide elbow, wrist or neck separation.
REST = {
    "x": 0.0, "y": 0.0, "spin": 0.0, "lean": 0.0, "head": 0.0,
    "nu": H.heading(BODY.J["near_shoulder"], BODY.J["near_elbow"]),
    "ne": H.heading(BODY.J["near_shoulder"], BODY.J["near_elbow"]) - H.heading(BODY.J["near_elbow"], BODY.J["near_wrist"]),
    "nw": -90.0,
    "fu": H.heading(BODY.J["far_shoulder"], BODY.J["far_elbow"]),
    "fe": H.heading(BODY.J["far_shoulder"], BODY.J["far_elbow"]) - H.heading(BODY.J["far_elbow"], BODY.J["far_wrist"]),
    "fw": -90.0,
    "nf": g(BODY.rest_x("near")), "ff": g(BODY.rest_x("far")),
    "eye": "open", "mouth": "closed", "nhand": "fist", "fhand": "fist",
    "quill": 1.0, "book": 1.0, "book_open": 0.0,
    "stars": 0.0, "apple": 0.0,
    "far_tail": 0.0, "near_tail": 0.0, "queue": 0.0,
}


def arm_depth(offset: float) -> dict:
    """Move the full near arm (not only the sleeve) across the facial plane.

    RigDocument recognizes bone.<name>.z as an animatable sort offset. This
    owns the entire arm including hand and quill; keyed -42 places the limb
    behind the HEAD in death/tumble, without needing alternate baked sprites.
    """
    return {f"bone.{bone}.z": offset
            for bone in ("near_arm_u", "near_arm_l", "near_hand")}


def clip(keys, *, sway=0.0, flutter=0.0, queue=0.0):
    """Use humanoid FK+IK for motion; extend with 3 real secondary bones."""
    def run(i: int, n: int, t: float):
        semantic = H.at(BODY, REST, keys, t)
        result = BODY.channels(semantic)
        # The shared humanoid defaults intentionally only know their standard
        # expression names. These two cartoon-scholar SVG parts have bespoke
        # opacity channels; without explicitly driving them, BRACE loses its
        # startled eyes and DAZED loses its wavy mouth altogether.
        result["eye.surprised"] = float(semantic.get("eye") == "surprised")
        result["mouth.wavy"] = float(semantic.get("mouth") == "wavy")
        w = math.tau * t
        result["tail_far"] = float(semantic["far_tail"]) - sway * math.sin(w + 0.7)
        result["tail_near"] = float(semantic["near_tail"]) + flutter * math.sin(w - 0.6)
        result["wig_queue"] = float(semantic["queue"]) + queue * math.sin(w - 0.9)
        result["prop.quill"] = float(semantic["quill"])
        result["prop.book"] = float(semantic["book"])
        result["prop.book_open"] = float(semantic["book_open"])
        result["fx.stars"] = float(semantic["stars"])
        result["prop.apple"] = float(semantic["apple"])
        result["star_halo"] = 13.0 * math.sin(2 * w) if result["fx.stars"] > 0 else 0.0
        return result
    return run


def idle(_i: int, _n: int, t: float):
    w = math.tau * t
    pose = {
        **REST, "y": 1.5 * math.sin(w), "lean": 0.8 * math.sin(w),
        "head": -1.3 * math.sin(w - 0.8),
        "nu": float(REST["nu"]) + 1.2 * math.sin(w - 0.4),
        "nw": -90 + 2.0 * math.sin(w + 0.3),
    }
    result = BODY.channels(pose)
    result.update({"eye.surprised": 0.0, "mouth.wavy": 0.0,
                   "star_halo": 0.0,
                   "tail_far": -1.3 * math.sin(w + 0.6),
                   "tail_near": 1.8 * math.sin(w - 0.4),
                   "wig_queue": 0.7 * math.sin(w),
                   "prop.quill": 1.0, "prop.book": 1.0,
                   "prop.book_open": 0.0, "fx.stars": 0.0, "prop.apple": 0.0})
    return result


POINT = clip([
    (0.0, REST),
    (0.18, {"lean": 8, "head": -5, "nu": 76, "ne": 135, "nw": -92, "near_tail": -7, "eye": "angry"}),
    (0.46, {"x": 9, "lean": 13, "head": -9, "nu": -9, "ne": -3, "nw": -88, "nf": g(28),
            "far_tail": -4, "near_tail": 14, "queue": 5, "mouth": "smile", "ease": "in"}),
    (0.76, {"x": 10, "lean": 11, "nu": -7, "ne": 0, "nw": -88, "mouth": "closed"}),
    (1.0, REST),
], flutter=2.5, queue=1.2)

CONDUCT = clip([
    # The feather must be nib-down in the fist, vane ABOVE it; conduct is an
    # elevated wrist beat, not a forward-pointed thrust like POINT.
    (0.0, {**REST, "book": 0, "near_tail": -5}),
    (0.25, {"lean": -3, "head": -2, "nu": -32, "ne": 8, "nw": -105,
            "fu": 126, "fe": -12, "fw": 32, "nf": g(17), "ff": g(-24),
            "mouth": "closed"}),
    (0.50, {"lean": 6, "nu": -10, "ne": 2, "nw": -92,
            "fu": 145, "fe": -10, "fw": 18, "near_tail": 8,
            "far_tail": -9, "head": 4, "eye": "angry", "mouth": "grit"}),
    (0.75, {"lean": -4, "nu": -35, "ne": 7, "nw": -103,
            "near_tail": 0}),
    (1.0, {"lean": 0, "nu": -28, "ne": 8, "nw": -100,
           "near_tail": -5}),
], sway=3, flutter=4, queue=2)

INVOKE = clip([
    # The original invocation uses an open book throughout; it must remain
    # visible above the far shoulder rather than hidden behind the head.
    (0.0, {**REST, "book": 0, "book_open": 1,
           "fu": -128, "fe": 5, "fw": -40}),
    (0.22, {"lean": -7, "head": -9, "nu": -45, "ne": 42, "nw": -90,
            "fu": -135, "fe": 0, "fw": -50, "mouth": "smile"}),
    (0.55, {"y": -9, "lean": -13, "head": -17, "nu": -82,
            "ne": 6, "nw": -95, "fu": -142, "fe": 5, "fw": -50,
            "near_tail": 15, "far_tail": -10, "queue": 12, "mouth": "open", "eye": "angry"}),
    (0.83, {"y": -6, "lean": -12, "nu": -70, "ne": 0, "nw": -88, "mouth": "smile"}),
    (1.0, {"y": -6, "nu": -70, "ne": 0, "nw": -88, "mouth": "smile"}),
], sway=4, flutter=5, queue=3)

HIT = clip([
    (0.0, {**REST, "book": 0}),
    (0.33, {"x": -13, "y": 5, "lean": -24, "head": -22, "nu": 60,
            "ne": 12, "nw": -100, "fu": 160, "fe": -18, "mouth": "grit", "eye": "shut",
            "book": 0, "near_tail": -8, "queue": -10}),
    (0.66, {"x": -8, "lean": -13, "head": -13, "near_tail": 4}),
    (1.0, REST),
], flutter=4, queue=3)

BRACE = clip([
    (0.0, {**REST, "book": 0}),
    # Match the shipped read: rear leg long and straight behind, front leg bent
    # under the torso to absorb the recoil.
    (0.38, {"x": -2, "y": 10, "lean": 16, "head": -6,
           "nu": -10, "ne": -2, "nw": -92, "fu": 174, "fe": -5, "fw": 172,
           "nf": g(8, 0, 2), "ff": g(-72, 0, -2), "book": 0,
           "eye": "surprised", "mouth": "open", "near_tail": 16, "far_tail": -12}),
    (0.73, {"x": -3, "y": 12, "lean": 22, "head": -8,
             "nu": -8, "ne": -1, "nw": -88,
             "nf": g(10, 0, 0), "ff": g(-74, 0, -4),
             "eye": "surprised", "mouth": "open"}),
    (1.0, {**REST, "book": 0}),
],flutter=2,queue=2)

TUMBLE = clip([
    # ``head`` in the semantic pose is a WORLD tilt. To make the old shipped
    # tumble read correctly, the head must travel with the body rotation rather
    # than staying world-upright.
    (0.0, {**REST, "book": 0, "quill": 0, "spin_about": 82,
           "head": 0, "lean": 0,
           "nf": b(2,-8), "ff": b(-4,-8), "nu": -22, "ne": 6,
           "fu": -146, "fe": -18, "mouth": "open", "apple": 1,
           **arm_depth(-39)}),
    (0.125, {"spin": 36, "y": 6, "x": -6, "head": 36,
             "nf": b(6,-18), "ff": b(-8,-18), "nu": 2, "ne": 8,
             "fu": -120, "fe": -16, "apple": 1}),
    (0.25, {"spin": 90, "y": 40, "x": -26, "head": 90,
            "nf": b(12,-30,10), "ff": b(-15,-28,-8), "nu": 62, "ne": 18,
            "fu": 104, "fe": -16, "eye": "shut", "mouth": "open", "apple": 1}),
    (0.375, {"spin": 136, "y": 92, "x": -8, "head": 136,
             "nf": b(16,-36,16), "ff": b(-17,-34,-12), "nu": 90, "ne": 24,
             "fu": 152, "fe": -20, "apple": 0}),
    (0.5, {"spin": 180, "y": 170, "x": 8, "head": 180, "lean": 0,
           "nf": b(8,-40,6), "ff": b(-8,-40,-6), "nu": 110, "ne": 26,
           "fu": 204, "fe": -26, "far_tail": 16, "near_tail": -18,
           "queue": 10, "eye": "shut", "mouth": "open", "apple": 0,
           **arm_depth(-42)}),
    (0.625, {"spin": 224, "y": 154, "x": 32, "head": 224,
             "nf": b(16,-38,12), "ff": b(-14,-36,-10), "nu": 72, "ne": 20,
             "fu": 176, "fe": -22}),
    (0.75, {"spin": 270, "y": 48, "x": 56, "head": 270,
            "nf": b(10,-22,6), "ff": b(-9,-22,-5), "nu": 18, "ne": 12,
            "fu": -88, "fe": -18, "eye": "shut"}),
    (0.875, {"spin": 324, "y": 10, "x": 20, "head": 324,
             "nf": b(6,-14), "ff": b(-6,-14), "nu": -12, "ne": 8,
             "fu": -122, "fe": -18}),
    (1.0, {**REST, "book": 0, "quill": 0, "spin": 360,
           "spin_about": 82, "head": 360,
           "nf": b(2,-8), "ff": b(-4,-8), "nu": -22, "ne": 6,
           "fu": -146, "fe": -18,
           "mouth": "open", **arm_depth(-39)}),
], flutter=3, queue=3)

DAZED = clip([
    (0.0, {**REST, "book": 0, "quill": 0, "y": 64, "lean": -24,
           "head": 18, "eye": "dizzy", "mouth": "wavy", "near_tail": -8,
           "nu": 155, "ne": 15, "fu": 150, "fe": 16,
           "nf": g(86), "ff": g(71), "stars": 1, "apple": 1,
           **arm_depth(-35)}),
    (0.5, {"head": 10, "lean": -18, "queue": 8, "eye": "dizzy", "mouth": "wavy"}),
    (1.0, {"head": 18, "lean": -24, "eye": "dizzy", "mouth": "wavy", "queue": 0}),
], flutter=3, queue=2)

CLIMB = clip([
    (0.0, {**REST, "book": 0, "quill": 0, "lean": 20,
            "nu": -72, "ne": -12, "fu": -124, "fe": -16, "eye": "shut",
            "mouth": "grit", "nf": b(7,-24), "ff": b(-6, -2)}),
    (0.50, {"y": -16, "nu": -70, "ne": -6, "fu": -132, "fe": -12,
            "nf": b(22,-52), "ff": b(0, -28),
            "near_tail": -12, "far_tail": -6, "head": -11,
            "eye": "shut", "mouth": "grit"}),
    (1.0, {"y": 0, "nu": -72, "ne": -12, "nf": b(7,-24), "ff": b(-6,-2),
           "eye": "shut", "mouth": "grit"}),
],flutter=4,queue=3)

DEATH = clip([
    (0.0, {**REST, "book": 0, "quill": 0,
           "stars": 1, **arm_depth(0)}),
    (0.16, {"y": -8, "lean": -16, "head": -21, "eye": "shut", "mouth": "open",
            "book": 0, "quill": 0, **arm_depth(-42), "ease": "hold"}),
    (0.52, {"x": 24, "y": -25, "spin": -85, "lean": 0,
            "nf": b(26,-7), "ff": b(-17,18), "nu": 140, "ne": 15,
            "far_tail": 19, "near_tail": -25, "queue": -15,
            **arm_depth(-42)}),
    (0.80, {"x": -12, "y": -3, "spin": -90, "head": -6,
            "eye": "dead", "mouth": "open", **arm_depth(-42)}),
    (1.0, {"x": -15, "y": -10, "spin": -90, "eye": "dead",
           **arm_depth(-42)}),
], flutter=1)

ROWS = [
    ("rest", 10, 110, True), ("point", 8, 70, False),
    ("conduct", 10, 80, True), ("invoke", 8, 80, False),
    ("hit", 6, 80, False), ("death", 10, 105, False),
    ("brace", 6, 80, True), ("tumble", 8, 70, False),
    ("dazed", 8, 120, True), ("climb", 8, 70, True),
]
CLIPS = {
    "rest": idle, "point": POINT, "conduct": CONDUCT, "invoke": INVOKE,
    "hit": HIT, "death": DEATH, "brace": BRACE, "tumble": TUMBLE,
    "dazed": DAZED, "climb": CLIMB,
}


def skeleton(joints):
    bones = H.skeleton(joints, H.HAND_LENGTH * SCALE)
    bones.extend([
        CR.segment("tail_far", "torso", joints["tail_far"], joints["tail_far_tip"]),
        CR.segment("tail_near", "torso", joints["tail_near"], joints["tail_near_tip"]),
        CR.segment("wig_queue", "head", joints["wig_queue"], joints["wig_queue_tip"]),
        CR.segment("star_halo", "head", joints["star_halo"], joints["star_halo_tip"]),
    ])
    return bones


def make_spec():
    spec = H.humanoid_spec(
        name="gnu_ton_scholar_villain", svg_path=ART, rig_path=RIG,
        view_label="GNU-ton Scholar - Three Quarter", scale=SCALE,
        svg_center_x=CX, svg_ground_y=GROUND,
        frame_size=(240, 280), supersample=3,
        rows=ROWS, clips=CLIPS,
        # Art has bent knees slightly to the right (facing +x).
        knee_bend=1.0, far_knee_bend=-1.0,
        defaults={"prop.quill": 1.0, "prop.book": 1.0,
                  "prop.book_open": 0.0, "fx.stars": 0.0, "prop.apple": 0.0},
    )
    return replace(spec, skeleton=skeleton,
                   angle_channels=spec.angle_channels | frozenset({"tail_far", "tail_near", "wig_queue", "star_halo"}))


def main() -> None:
    if not ART.exists():
        raise SystemExit(f"Missing SVG: run scripts/svg_art/gnu_ton_scholar_villain_art.py first")
    files = H.write(make_spec())
    label_generated_rig_guides(ART)
    write_object_inventory(ART, ROOT / "docs" / "authoring" / "gnu_ton_scholar_object_index.csv")
    for file in files:
        print(f"wrote {file.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
