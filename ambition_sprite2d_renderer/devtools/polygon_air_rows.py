"""Pointed Polygon's fall and landing rows, written as FK clips.

`fall` is a closed loop: arms thrown up and out (the sword up and forward,
clear of the legs), legs dangling, the whole body fluttering on one clock.

The landings are taken in the knees, with no squish: the crouch overshoots
the rest crouch on impact, holds, and she rises to standing.

A crouch is placed by `CROUCH`: the drop of the root against the leg and
torso angles that keep both feet planted, from the legacy bake of her crouch.
A drop between two rows is a linear blend of them (the feet stay within a
pixel), and no drop goes below the deepest row.

The game draws `land_recovery` for a soft landing and `land_hard` for a hard
one; `land_light` is the same as `land_recovery`.

Run `python -m ambition_sprite2d_renderer.devtools.polygon_air_rows` after a
change; it writes the four clips.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

LIBRARY = Path(__file__).resolve().parent.parent / "data" / "motion" / "humanoid" / "fighting_polygon_v1"

CROUCH_BONES = ("far_leg_u", "far_leg_l", "far_leg_foot", "near_leg_u", "near_leg_l", "near_leg_foot", "torso")
#: (root drop, angles of `CROUCH_BONES`), shallowest first.
CROUCH: Tuple[Tuple[float, Tuple[float, ...]], ...] = (
    (0.0, (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)),
    (12.7188, (-12.59, 23.3808, -10.7908, -12.4663, 27.7608, -15.2945, 2.6562)),
    (40.7, (-27.0291, 49.633, -22.6038, -23.3667, 54.6567, -31.29, 8.5)),
    (68.6813, (-38.0037, 68.2105, -30.2068, -29.8939, 73.3788, -43.4849, 14.3438)),
    (81.4001, (-43.1785, 76.6284, -33.447, -31.677, 79.5479, -47.8749, 17.0)),
    (89.3107, (-45.5291, 80.9608, -36.5948, -33.2151, 84.0067, -51.9618, 19.0408)),
    (103.1542, (-49.51, 88.195, -41.8889, -35.5955, 91.4128, -59.0282, 22.6122)),
    (107.9305, (-50.9302, 90.7547, -43.6872, -36.3846, 93.9786, -61.4869, 23.8704)),
)

#: (near_arm_u, near_arm_l, far_arm_u, far_arm_l) of one frame.
Arms = Tuple[float, float, float, float]


def crouch(drop: float) -> Dict[str, float]:
    for (d0, a), (d1, b) in zip(CROUCH, CROUCH[1:]):
        if d0 <= drop <= d1:
            u = (drop - d0) / (d1 - d0)
            return {name: x + (y - x) * u for name, x, y in zip(CROUCH_BONES, a, b)}
    raise ValueError(f"a drop of {drop} is outside the crouch she was baked with")


def _key(frame: int, step_s: float, bones: Dict[str, float], root_y: float) -> dict:
    state: dict = {
        "root": {"position": [0.0, round(root_y, 4)]},
        "bones": {name: {"rotation_deg": round(deg, 4)} for name, deg in sorted(bones.items())},
    }
    return {"at_s": round(frame * step_s, 6), "frame": frame, "state": state}


def _write_clip(name: str, keys: List[dict], loop: bool, step_ms: int, note: str) -> None:
    path = LIBRARY / "clips" / f"{name}.clip.json"
    clip = json.loads(path.read_text())
    clip.update({
        "loop": loop,
        "duration_s": round(len(keys) * step_ms / 1000.0, 6),
        "sampling": {"frame_count": len(keys), "frame_duration_ms": step_ms},
        "source": {
            "kind": "authored",
            "clip": name,
            "note": f"{note} Written by devtools/polygon_air_rows.py; edit it, not this file.",
        },
        "pose_keys": keys,
    })
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(clip, indent=2) + "\n")
    tmp.replace(path)


def fall() -> None:
    frames, step_ms = 6, 90
    keys = []
    for i in range(frames):
        phase = i / frames
        w, v = math.sin(phase * math.tau), math.sin(phase * math.tau + 1.2)
        keys.append(_key(i, step_ms / 1000.0, {
            "torso": -4 + 2 * v, "pelvis": -2, "head": -4 + 2 * w,
            "near_arm_u": -122 + 3 * w, "near_arm_l": 16 + 4 * v,
            "far_arm_u": 100 - 8 * w, "far_arm_l": -26 - 12 * v,
            "near_leg_u": -10 + 7 * w, "near_leg_l": 26 + 8 * v, "near_leg_foot": -10 - 4 * v,
            "far_leg_u": 12 - 7 * w, "far_leg_l": 20 - 8 * v, "far_leg_foot": -6 + 4 * v,
        }, root_y=-6 + 3 * w))
    _write_clip("fall", keys, True, step_ms,
                "Arms thrown up and out, the sword up and forward and clear of the legs, legs dangling.")


def _landing(name: str, drops: Sequence[float], arms: Sequence[Arms], step_ms: int, note: str) -> None:
    assert len(drops) == len(arms)
    keys = []
    for i, (drop, (near_u, near_l, far_u, far_l)) in enumerate(zip(drops, arms)):
        bones = crouch(drop)
        bones.update({"head": 2 * drop / 81, "near_arm_u": near_u, "near_arm_l": near_l,
                      "far_arm_u": far_u, "far_arm_l": far_l})
        keys.append(_key(i, step_ms / 1000.0, bones, root_y=drop))
    _write_clip(name, keys, False, step_ms, note)


SOFT = dict(
    drops=[88, 98, 66, 26, 6, 0],
    arms=[(-70, -20, -24, -38), (-60, -18, -22, -36), (-38, -10, -14, -22),
          (-14, -4, -5, -8), (-4, -1, -1, -2), (0, 0, 0, 0)],
    step_ms=55,
)
SOFT_NOTE = "Taken in the knees: the crouch overshoots, then she stands."


def land_recovery() -> None:
    _landing("land_recovery", note=SOFT_NOTE, **SOFT)


def land_light() -> None:
    _landing("land_light", note=SOFT_NOTE, **SOFT)


def land_hard() -> None:
    _landing(
        "land_hard",
        drops=[100, 106, 104, 94, 72, 38, 10, 0],
        arms=[(-80, -24, -30, -40), (-74, -22, -28, -40), (-70, -21, -27, -38), (-62, -19, -24, -34),
              (-46, -14, -18, -26), (-22, -6, -8, -12), (-6, -2, -2, -3), (0, 0, 0, 0)],
        step_ms=55,
        note="A heavy impact taken in the knees: the deepest crouch, held, then she rises.",
    )


def main() -> None:
    for write in (fall, land_recovery, land_light, land_hard):
        write()


if __name__ == "__main__":
    main()
