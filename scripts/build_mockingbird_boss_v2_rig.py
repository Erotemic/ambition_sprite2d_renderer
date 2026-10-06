#!/usr/bin/env python3
"""Build the Mockingbird v2's rig document from its SVG.

The SVG ``data/characters/mockingbird_boss_v2/mockingbird_boss_v2.svg`` owns
the art and says where every joint is; ``rigbuild.creature_rig`` derives the
skeleton from it (the gunship anatomy below), binds every part to its bone
and refreshes the SVG's rig catalog. This script supplies only what the
drawing cannot state: the anatomy, the frame, the rows and the clips. It never
draws.

    uv run python scripts/build_mockingbird_boss_v2_rig.py

The rows are the six the Mockingbird's boss sheet already ships
(``rest``, ``thrust``, ``bite``, ``slash``, ``hit``, ``death``) with the same
frame counts and durations, so the redesign can stand in for the first sheet.

Angles are degrees added to the drawing (positive turns clockwise on screen:
a positive ``body`` dips the nose, a positive ``jaw`` opens the mouth, a
positive ``<side>_arm`` swings a claw back under the belly); distances are SVG
units. One-shot rows are key poses, one key per drawn frame (``K``).
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Callable, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ambition_sprite2d_renderer.rigbuild.creature_rig import (  # noqa: E402
    BoneSpec,
    CreatureSpec,
    Point,
    Pose,
    eyes,
    heading,
    dist,
    segment,
    track,
    write,
)

PKG = ROOT / "ambition_sprite2d_renderer"

ROTOR_STATES = ("a", "b", "c")
SIDES = ("far", "near")


def skeleton(J: Dict[str, Point]) -> List[BoneSpec]:
    """A ``body`` at the hull's centre (the root: a clip pitches the whole
    machine with it), a two-segment neck to a ``head`` with a hinged ``jaw``,
    a thruster ``engine``, two rotor masts (``<side>_rotor``) each carrying
    its blades (``<side>_blade``, hub to blade tip) and, per side, a claw arm
    (``<side>_arm``, ``<side>_fore``, ``<side>_claw``). The jet wings and their
    missiles are rigid: they ride ``body``."""
    bones: List[BoneSpec] = [("body", None, J["body"], 0.0, 0.0)]
    bones.append(segment("neck1", "body", J["neck1"], J["neck2"]))
    bones.append(segment("neck2", "neck1", J["neck2"], J["head"]))
    bones.append(segment("head", "neck2", J["head"], J["snout"]))
    bones.append(("jaw", "head", J["jaw"], heading(J["jaw"], J["jaw_tip"]), dist(J["jaw"], J["jaw_tip"])))
    bones.append(segment("engine", "body", J["engine"], J["engine_tip"]))
    for side in SIDES:
        bones.append(segment(f"{side}_rotor", "body", J[f"{side}_rotor"], J[f"{side}_hub"]))
        # the blades: from the hub to the tip of one blade (its length is the
        # blade reach the target sizes the blur disc from)
        bones.append(segment(f"{side}_blade", f"{side}_rotor", J[f"{side}_hub"], J[f"{side}_blade_tip"]))
        bones.append(segment(f"{side}_arm", "body", J[f"{side}_shoulder"], J[f"{side}_elbow"]))
        bones.append(segment(f"{side}_fore", f"{side}_arm", J[f"{side}_elbow"], J[f"{side}_wrist"]))
        bones.append(segment(f"{side}_claw", f"{side}_fore", J[f"{side}_wrist"], J[f"{side}_tip"]))
    return bones


# --- pose helpers -----------------------------------------------------------------


def rotors(i: int, spin: bool = True) -> Pose:
    """Each rotor's spin state for frame ``i`` (the far one a third of a turn
    behind), or both at rest on their full-length state."""
    p: Pose = {}
    for side, lag in (("near", 0), ("far", 1)):
        state = ROTOR_STATES[(i + lag) % 3] if spin else "a"
        p.update({f"{side}_rotor.{s}": 1.0 if s == state else 0.0 for s in ROTOR_STATES})
    return p


def claws(near: str, far: str | None = None) -> Pose:
    far = far or near
    return {
        "near_claw.open": 1.0 if near == "open" else 0.0,
        "near_claw.shut": 1.0 if near == "shut" else 0.0,
        "far_claw.open": 1.0 if far == "open" else 0.0,
        "far_claw.shut": 1.0 if far == "shut" else 0.0,
    }


def hover(t: float, *, bob: float = 7.0, sway: float = 1.0) -> Pose:
    """A held hover: the machine bobs on its rotors, the neck and head
    counter the bob, the claws dangle a beat behind it."""
    w = math.tau * t
    return {
        "root_y": bob * math.sin(w),
        "body": 1.6 * sway * math.sin(w + 0.6),
        "neck1": -2.0 * sway * math.sin(w + 0.2),
        "neck2": -2.4 * sway * math.sin(w - 0.3),
        "head": 2.6 * sway * math.sin(w - 0.9),
        "engine": 1.5 * sway * math.sin(w + 1.4),
        "near_arm": 5.0 * sway * math.sin(w - 1.0),
        "near_fore": 6.0 * sway * math.sin(w - 1.6),
        "near_claw": 8.0 * sway * math.sin(w - 2.2),
        "far_arm": 4.0 * sway * math.sin(w - 1.3),
        "far_fore": 5.0 * sway * math.sin(w - 1.9),
        "far_claw": 7.0 * sway * math.sin(w - 2.5),
    }


# --- clips --------------------------------------------------------------------------


def rest(i: int, n: int, t: float) -> Pose:
    """Hovering, jaw hanging open, the core breathing."""
    p = hover(t)
    p["jaw"] = 13.0 + 3.0 * math.sin(math.tau * t * 2.0)
    p.update(rotors(i))
    p.update(claws("open"))
    p.update(eyes("open"))
    p["fx.jet"] = 0.55 + 0.1 * math.sin(math.tau * t * 2.0)
    p["fx.blur"] = 1.0
    p["fx.glow"] = 0.55 + 0.25 * math.sin(math.tau * t)
    return p


def thrust(i: int, n: int, t: float) -> Pose:
    """The dash: nose down, neck stretched, jaw wide, claws swept back and
    shut, the thruster roaring."""
    p = hover(t, bob=3.0, sway=0.5)
    w = math.tau * t
    p["body"] += 7.0
    p["neck1"] += -6.0
    p["neck2"] += -6.0
    p["head"] += -4.0
    p["jaw"] = 24.0 + 4.0 * math.sin(w * 2.0)
    p["engine"] += -4.0
    for side, k in (("near", 1.0), ("far", 0.85)):
        p[f"{side}_arm"] += 34.0 * k
        p[f"{side}_fore"] += 22.0 * k
        p[f"{side}_claw"] += 18.0 * k
    p.update(rotors(i))
    p.update(claws("shut"))
    p.update(eyes("angry"))
    p["fx.jet"] = 1.0
    p["fx.boost"] = 0.8 + 0.2 * math.sin(w * 3.0)
    p["fx.speed"] = 0.8 + 0.2 * math.sin(w * 2.0)
    p["fx.blur"] = 1.0
    p["fx.glow"] = 0.9
    return p


def K(keys: List[float], i: int) -> float:
    return keys[min(i, len(keys) - 1)]


def bite(i: int, n: int, t: float) -> Pose:
    """The floor slam: rear up with the jaw gaping and the claws reaching,
    then drop on the floor, the jaw snapping shut and the claws closing."""
    p: Pose = {
        "root_y": K([0, -20, -26, 30, 26, 8], i),
        "root_x": K([0, -6, -8, 10, 8, 2], i),
        "body": K([0, -8, -11, 12, 10, 3], i),
        "neck1": K([0, -4, -6, 6, 4, 1], i),
        "neck2": K([0, -4, -6, 7, 5, 1], i),
        "head": K([0, -6, -8, 10, 7, 3], i),
        "jaw": K([14, 30, 36, 0, 4, 12], i),
        "engine": K([0, 6, 8, -6, -4, 0], i),
        "near_arm": K([0, -24, -32, -36, -26, -6], i),
        "near_fore": K([0, -12, -18, -26, -14, -2], i),
        "near_claw": K([0, -10, -14, 6, 4, 0], i),
        "far_arm": K([0, -20, -28, -32, -22, -4], i),
        "far_fore": K([0, -10, -16, -22, -12, -2], i),
        "far_claw": K([0, -8, -12, 6, 4, 0], i),
    }
    p.update(rotors(i))
    p.update(claws("open" if i < 3 else "shut"))
    p.update(eyes("angry" if 0 < i < 5 else "open"))
    p["fx.jet"] = K([0.55, 0.8, 1.0, 0.4, 0.5, 0.55], i)
    p["fx.blur"] = 1.0
    p["fx.glow"] = K([0.6, 0.8, 0.9, 1.0, 0.8, 0.6], i)
    p["fx.bite"] = K([0, 0, 0, 1, 0.3, 0], i)
    p["fx.shock"] = K([0, 0, 0, 0.6, 1, 0.3], i)
    return p


def slash(i: int, n: int, t: float) -> Pose:
    """The fireball tell: rear back, jaw opening wider and wider as the core
    flares and fire gathers in the throat, then spit it, the near wingtip's
    missile firing too."""
    p: Pose = {
        "root_y": K([0, -6, -10, -12, 4, 0], i),
        "root_x": K([0, -12, -18, -22, 10, 2], i),
        "body": K([0, -5, -8, -9, 5, 1], i),
        "neck1": K([0, -4, -6, -7, 4, 1], i),
        "neck2": K([0, -4, -6, -8, 5, 1], i),
        "head": K([0, -6, -9, -11, 6, 2], i),
        "jaw": K([14, 26, 34, 42, 40, 18], i),
        "engine": K([0, 3, 5, 6, -4, 0], i),
        "near_arm": K([0, 10, 16, 18, 4, 0], i),
        "near_fore": K([0, 8, 12, 14, 2, 0], i),
        "far_arm": K([0, 8, 14, 16, 4, 0], i),
        "far_fore": K([0, 6, 10, 12, 2, 0], i),
    }
    p.update(rotors(i))
    p.update(claws("shut"))
    p.update(eyes("angry"))
    p["fx.jet"] = K([0.55, 0.6, 0.7, 0.8, 1.0, 0.6], i)
    p["fx.blur"] = 1.0
    p["fx.glow"] = K([0.6, 0.8, 1.0, 1.0, 0.7, 0.6], i)
    p["fx.charge"] = K([0, 0.35, 0.7, 1.0, 0.2, 0], i)
    p["fx.spit"] = K([0, 0, 0, 0, 1, 0.3], i)
    p["fx.muzzle"] = K([0, 0, 0, 0, 1, 0.2], i)
    return p


def hit(i: int, n: int, t: float) -> Pose:
    """Struck: knocked back, the eye shuttered, sparks off the hull."""
    p: Pose = {
        "root_x": K([0, -20, -12, -4], i),
        "root_y": K([0, -6, -2, 0], i),
        "body": K([0, -10, -6, -2], i),
        "neck1": K([0, -5, -3, -1], i),
        "neck2": K([0, -6, -3, -1], i),
        "head": K([0, -10, -5, -2], i),
        "jaw": K([14, 28, 20, 15], i),
        "near_arm": K([0, 22, 12, 4], i),
        "near_fore": K([0, 18, 10, 3], i),
        "near_claw": K([0, 14, 8, 2], i),
        "far_arm": K([0, 18, 10, 3], i),
        "far_fore": K([0, 14, 8, 2], i),
        "far_claw": K([0, 10, 6, 2], i),
    }
    p.update(rotors(i))
    p.update(claws("open"))
    p.update(eyes("shut" if i in (1, 2) else "open"))
    p["fx.jet"] = K([0.55, 0.2, 0.4, 0.55], i)
    p["fx.blur"] = 1.0
    p["fx.glow"] = K([0.6, 1.0, 0.7, 0.6], i)
    p["fx.spark"] = K([0, 1, 0.5, 0], i)
    return p


def death(i: int, n: int, t: float) -> Pose:
    """Shot down: sparks and smoke, the thruster sputters out, the rotors
    wind down, the nose drops and it sinks, jaw slack, claws trailing."""
    p: Pose = {
        "root_y": K([0, -8, 2, 14, 28, 40, 50, 56], i),
        "root_x": K([0, -14, -10, -4, 4, 10, 14, 16], i),
        "body": K([0, -8, 4, 10, 15, 19, 21, 22], i),
        "neck1": K([0, -5, 3, 6, 8, 9, 10, 10], i),
        "neck2": K([0, -6, 3, 6, 8, 9, 10, 10], i),
        "head": K([0, -10, 4, 8, 10, 12, 13, 14], i),
        "jaw": K([14, 34, 26, 30, 34, 36, 38, 38], i),
        "engine": K([0, 6, -6, 8, -4, 10, 12, 14], i),
        "near_arm": K([0, 24, 34, 44, 52, 56, 58, 60], i),
        "near_fore": K([0, 18, 24, 30, 34, 36, 38, 38], i),
        "near_claw": K([0, 14, 20, 26, 30, 32, 34, 34], i),
        "far_arm": K([0, 20, 30, 40, 48, 52, 54, 56], i),
        "far_fore": K([0, 14, 20, 26, 30, 32, 34, 34], i),
        "far_claw": K([0, 10, 16, 22, 26, 28, 30, 30], i),
    }
    # The rotors wind down: a state a frame, then every other frame, then stop.
    spin_at = [0, 1, 2, 2, 0, 0, 0, 0]
    p.update(rotors(spin_at[i], spin=True))
    p.update(claws("open"))
    p.update(eyes("shut" if i == 1 else "dead" if i >= 2 else "open"))
    p["fx.jet"] = K([0.55, 0.2, 0.6, 0.0, 0.3, 0.0, 0.0, 0.0], i)
    p["fx.blur"] = K([1.0, 1.0, 0.8, 0.6, 0.35, 0.15, 0.0, 0.0], i)
    p["fx.glow"] = K([0.6, 1.0, 0.5, 0.35, 0.2, 0.1, 0.0, 0.0], i)
    p["fx.spark"] = K([0, 1, 0.7, 0.9, 0.5, 0.6, 0.3, 0.2], i)
    p["fx.smoke"] = K([0, 0.3, 0.6, 0.8, 1.0, 1.0, 1.0, 1.0], i)
    return p


CLIPS: Dict[str, Callable[[int, int, float], Pose]] = {
    "rest": rest,
    "thrust": thrust,
    "bite": bite,
    "slash": slash,
    "hit": hit,
    "death": death,
}

DEFAULTS: Pose = {
    "eye.open": 1.0,
    "jaw": 14.0,
    "near_rotor.a": 1.0,
    "far_rotor.a": 1.0,
    "near_claw.open": 1.0,
    "far_claw.open": 1.0,
}

#: Sprite pixels per SVG unit: the drawing is 1140x760 units.
SCALE = 0.5

SPEC = CreatureSpec(
    name="mockingbird_boss_v2",
    svg_path=PKG / "data" / "characters" / "mockingbird_boss_v2" / "mockingbird_boss_v2.svg",
    rig_path=PKG / "targets" / "characters" / "rigged" / "mockingbird_boss_v2" / "mockingbird_boss_v2_side.rig.json",
    view_label="Mockingbird - Side Right",
    skeleton=skeleton,
    legs=(),
    scale=SCALE,
    svg_center_x=570.0,
    svg_ground_y=740.0,
    frame_size=(570, 380),
    # (row, frames, ms, loops): the first sheet's rows. Its one-shots were
    # sampled as loops too; here only the hover and the dash loop.
    rows=[
        ("rest", 6, 110, True),
        ("thrust", 6, 90, True),
        ("bite", 6, 90, False),
        ("slash", 6, 88, False),
        ("hit", 4, 80, False),
        ("death", 8, 105, False),
    ],
    clips=CLIPS,
    defaults=DEFAULTS,
)


def main(argv: List[str] | None = None) -> int:
    del argv
    for path in write(SPEC):
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
