from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, Sequence, Tuple

from ambition_sprite2d_renderer.authoring.humanoid_svg_rig import (
    HumanoidViewSpec,
    build_humanoid_view_document,
)
from ambition_sprite2d_renderer.targets.characters.robot25d import Pose
from ambition_sprite2d_renderer.targets.characters.robot_side import SideRobotGenerator

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "ambition_sprite2d_renderer"
SVG_PATH = PKG / "data/characters/player_robot_svg/player-robot.svg"
RIG_DIR = PKG / "targets/characters/rigged/player_robot"
RIG_JSON = RIG_DIR / "player_robot.rig.json"
VIEW_LABEL = "Player Robot - Side Right"

FRAME_WIDTH = 224
FRAME_HEIGHT = 224
CENTER_X = 112.0
GROUND_Y = 158.0

# Exact row vocabulary currently published by configs/player_robot.yaml.
ANIMATION_ORDER = [
    "idle",
    "walk",
    "run",
    "jump",
    "fall",
    "slash",
    "hit",
    "death",
    "blink_out",
    "blink_in",
    "dash",
    "hover",
    "ledge_grab",
    "dash_startup",
    "land_hard",
    "land_recovery",
    "wall_grab",
    "ledge_climb",
    "ledge_getup",
    "float_glide",
    "attack_side",
    "attack_up",
    "attack_down",
    "air_neutral",
    "air_forward",
    "air_back",
    "air_down",
    "air_up",
    "ledge_roll",
    "ledge_getup_attack",
    "crouch",
    "crouch_walk",
    "slide",
    "climb",
    "swim",
    "block",
    "roll",
    "wall_jump",
    "shoot",
    "aim",
    "charge",
    "interact",
]

LOOPING = {
    "idle",
    "walk",
    "run",
    "fall",
    "hover",
    "ledge_grab",
    "wall_grab",
    "float_glide",
    "crouch",
    "crouch_walk",
    "climb",
    "swim",
    "block",
    "aim",
    "charge",
}

Pair = Tuple[float, float]


def _keys(values: Iterable[Pair]) -> Dict[str, list[list[float]]]:
    return {"keys": [[round(float(t), 6), round(float(v), 5)] for t, v in values]}


def _times(nframes: int, loop: bool) -> list[float]:
    if loop:
        return [i / nframes for i in range(nframes)]
    return [i / max(1, nframes - 1) for i in range(nframes)]


def _channel(values: list[float], *, loop: bool) -> dict:
    times = _times(len(values), loop)
    pairs = list(zip(times, values))
    if loop and values:
        pairs.append((1.0, values[0]))
    return _keys(pairs)


def _bone_maps(doc: dict):
    bones = {b["name"]: b for b in doc["bones"]}
    rest = {name: float(b.get("rest_angle", 0.0)) for name, b in bones.items()}
    parent = {name: b.get("parent") for name, b in bones.items()}
    world: dict[str, float] = {}

    def solve(name: str) -> float:
        if name in world:
            return world[name]
        par = parent[name]
        world[name] = (solve(par) if par else 0.0) + rest[name]
        return world[name]

    for name in bones:
        solve(name)
    return rest, parent, world


def _foot_pitch(animation: str, frame: int, side: str, body_tilt: float) -> float:
    if animation == "walk":
        seq = (-6, -4, -2, 2, 6, 4, 2, -2)
        value = seq[frame % 8]
        return value if side == "near" else -seq[(frame + 4) % 8]
    if animation == "run":
        seq = (-8, -5, -2, 3, 8, 5, 2, -3)
        value = seq[frame % 8]
        return value if side == "near" else -seq[(frame + 4) % 8]
    if animation in {"jump", "wall_jump"}:
        return -8.0 + frame * 2.0
    if animation in {"fall", "float_glide", "hover", "swim"}:
        return -8.0
    if animation in {"roll", "ledge_roll", "death"}:
        return body_tilt * 0.35
    return 0.0


def make_clips(doc: dict) -> dict:
    generator = SideRobotGenerator()
    default = Pose()
    rest, _parent, canonical = _bone_maps(doc)

    clips: dict[str, dict] = {}
    for animation in ANIMATION_ORDER:
        info = generator.ANIMATIONS[animation]
        nframes = int(info["frames"])
        duration_ms = int(info["duration_ms"])
        loop = animation in LOOPING
        poses = [generator.pose_for_animation(animation, i, nframes) for i in range(nframes)]

        channels: dict[str, dict] = {}

        def vals(fn):
            return [float(fn(p, i)) for i, p in enumerate(poses)]

        # Root translation. body_bob is folded into root_y because this rig is a
        # rigid paper doll and does not have a separate torso translation channel.
        channels["root_x"] = _channel(vals(lambda p, _i: p.root_x), loop=loop)
        channels["root_y"] = _channel(vals(lambda p, _i: p.root_y + p.body_bob), loop=loop)

        pelvis_world = vals(lambda p, _i: p.whole_body_rotation + p.body_tilt * 0.25)
        torso_world = vals(lambda p, _i: p.whole_body_rotation + p.body_tilt)
        head_world = vals(lambda p, _i: p.whole_body_rotation + p.head_tilt)

        channels["pelvis"] = _channel(
            [v - rest["pelvis"] for v in pelvis_world], loop=loop
        )
        channels["torso"] = _channel(
            [torso_world[i] - pelvis_world[i] - rest["torso"] for i in range(nframes)],
            loop=loop,
        )
        channels["head"] = _channel(
            [head_world[i] - torso_world[i] - rest["head"] for i in range(nframes)],
            loop=loop,
        )

        # Limb choreography is transferred as DELTAS from the old canonical
        # pose onto the new SVG's authored rest angles. This preserves the
        # user's joint placement and avoids snapping the new art to the old
        # robot's absolute geometry.
        for side in ("far", "near"):
            upper_name = f"{side}_arm_u"
            lower_name = f"{side}_arm_l"
            hand_name = f"{side}_arm_hand"
            old_upper0 = getattr(default, f"{side}_arm_upper")
            old_lower0 = getattr(default, f"{side}_arm_lower")
            upper_world = [
                canonical[upper_name]
                + (getattr(p, f"{side}_arm_upper") - old_upper0)
                + p.whole_body_rotation
                for p in poses
            ]
            lower_world = [
                canonical[lower_name]
                + (getattr(p, f"{side}_arm_lower") - old_lower0)
                + p.whole_body_rotation
                for p in poses
            ]
            channels[upper_name] = _channel(
                [upper_world[i] - torso_world[i] - rest[upper_name] for i in range(nframes)],
                loop=loop,
            )
            channels[lower_name] = _channel(
                [lower_world[i] - upper_world[i] - rest[lower_name] for i in range(nframes)],
                loop=loop,
            )
            # Keep fingers rigidly attached to the mitten. The hand bone follows
            # the forearm's authored rest relationship; no independent finger or
            # hand animation is generated.
            channels[hand_name] = _channel([0.0] * nframes, loop=loop)

        for side in ("far", "near"):
            upper_name = f"{side}_leg_u"
            lower_name = f"{side}_leg_l"
            foot_name = f"{side}_leg_foot"
            old_upper0 = getattr(default, f"{side}_leg_upper")
            old_lower0 = getattr(default, f"{side}_leg_lower")
            upper_delta = [
                getattr(p, f"{side}_leg_upper") - old_upper0 for p in poses
            ]
            lower_delta = [
                getattr(p, f"{side}_leg_lower") - old_lower0 for p in poses
            ]
            upper_world = [
                canonical[upper_name] + upper_delta[i] + poses[i].whole_body_rotation
                for i in range(nframes)
            ]
            # The canonical SVG authors distinct upper-leg, lower-leg, and foot
            # parts, so preserve the full knee motion from the source pose.
            lower_world = [
                canonical[lower_name]
                + lower_delta[i]
                + poses[i].whole_body_rotation
                for i in range(nframes)
            ]
            foot_world = [
                canonical[foot_name]
                + _foot_pitch(animation, i, side, poses[i].body_tilt)
                + poses[i].whole_body_rotation
                for i in range(nframes)
            ]
            channels[upper_name] = _channel(
                [upper_world[i] - pelvis_world[i] - rest[upper_name] for i in range(nframes)],
                loop=loop,
            )
            channels[lower_name] = _channel(
                [lower_world[i] - upper_world[i] - rest[lower_name] for i in range(nframes)],
                loop=loop,
            )
            channels[foot_name] = _channel(
                [foot_world[i] - lower_world[i] - rest[foot_name] for i in range(nframes)],
                loop=loop,
            )

        # Non-bone channels remain editable in the rig editor and drive target
        # presentation effects (blade, teleport pixels, shield, thrusters, etc.).
        # Facial blink is authored as two mutually exclusive SVG parts. The
        # open visor owns the ordinary eyes; the blink visor has a slightly
        # softer silhouette and closed cyan eye arcs. Keeping both states as
        # explicit rig parts makes the blink visible/editable in the timeline
        # without special-case drawing code or runtime alpha-bound derivation.
        blink_values = [1.0 if pose.blink else 0.0 for pose in poses]
        channels["face_open_vis"] = _channel(
            [1.0 - value for value in blink_values], loop=loop
        )
        channels["blink_vis"] = _channel(blink_values, loop=loop)
        channels["eye_squint"] = _channel(
            [p.eye_squint for p in poses], loop=loop
        )
        channels["slash"] = _channel([p.slash for p in poses], loop=loop)
        channels["slash_arc"] = _channel([p.slash_arc for p in poses], loop=loop)
        channels["dash_fx"] = _channel([p.dash for p in poses], loop=loop)
        channels["collapse"] = _channel([p.collapse for p in poses], loop=loop)
        channels["dead"] = _channel([1.0 if p.dead else 0.0 for p in poses], loop=loop)
        channels["head_look"] = _channel([p.head_look for p in poses], loop=loop)

        clips[animation] = {
            "loop": loop,
            "frames": nframes,
            "duration_ms": duration_ms,
            "channels": channels,
        }
    return clips


def build_doc() -> dict:
    RIG_DIR.mkdir(parents=True, exist_ok=True)
    spec = HumanoidViewSpec(
        view=VIEW_LABEL,
        name="player_robot",
        frame_width=FRAME_WIDTH,
        frame_height=FRAME_HEIGHT,
        center_x=CENTER_X,
        ground_y=GROUND_Y,
        target_height=101.0,
        ref_dpi=25.4,
        supersample=4,
        render_scale=1,
        collision_scale=1.65,
    )
    doc = build_humanoid_view_document(SVG_PATH, RIG_DIR, spec)
    # Animation is authored as explicit bone channels. Keeping the generated IK
    # chains would overwrite those channels every frame with rest targets.
    doc["ik_chains"] = []
    doc["ik_legs"] = []

    # Part grouping and z-order are authored in the canonical SVG. The builder
    # must not silently replace those artist-editable values with a second copy.

    doc["clips"] = make_clips(doc)
    doc["features"] = {
        "paper_doll": True,
        "split_leg_artwork": True,
        "fingers_locked_to_hands": True,
        "toe_caps_locked_to_boots": True,
        "source_animation_vocabulary": "configs/player_robot.yaml",
        "logical_frame": [FRAME_WIDTH, FRAME_HEIGHT],
        "trimmed_runtime_frames": True,
        "roll_has_expanded_canvas": True,
        "far_arm_behind_torso": True,
        "near_arm_above_torso": True,
        "authored_face_states": ["face_open", "face_blink"],
        "idle_eye_blink": True,
    }
    return doc


def _preserved_authoring_blocks() -> dict[str, dict]:
    """Keep GUI-authored metadata across deterministic rig regeneration.

    The builder owns SVG/bone/clip generation, but it must not erase manually
    authored gameplay geometry or continuous animation constraints.
    """
    if not RIG_JSON.exists():
        return {}
    try:
        existing = json.loads(RIG_JSON.read_text(encoding="utf8"))
    except (OSError, ValueError):
        return {}
    preserved = {}
    for key in ("gameplay_geometry", "animation_constraints"):
        value = existing.get(key)
        if isinstance(value, dict):
            preserved[key] = value
    return preserved


def _preserved_gameplay_geometry() -> dict | None:
    """Backward-compatible accessor retained for existing tests/tools."""
    return _preserved_authoring_blocks().get("gameplay_geometry")


def cmd_build() -> None:
    preserved = _preserved_authoring_blocks()
    doc = build_doc()
    doc.update(preserved)
    RIG_JSON.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf8")
    print(RIG_JSON)


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", nargs="?", default="build", choices=["build"])
    args = parser.parse_args(argv)
    if args.command == "build":
        cmd_build()


if __name__ == "__main__":
    main()
