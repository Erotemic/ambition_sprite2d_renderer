from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Dict, Iterable, Sequence, Tuple

from ambition_sprite2d_renderer.authoring.fighter_motion_catalog import validate_motion_coverage
from ambition_sprite2d_renderer.authoring.humanoid_svg_rig import (
    HumanoidViewSpec,
    build_humanoid_view_document,
)
from ambition_sprite2d_renderer.targets.characters.robot25d import Pose
from ambition_sprite2d_renderer.targets.characters.robot_side import SideRobotGenerator
from ambition_sprite2d_renderer.targets.characters.player_robot_v3_motion import (
    APPLICABLE_MOTION_SCOPES,
    FIGHTER_MOTION_COVERAGE,
    LOOPING_ROWS,
    POSE_ALIASES,
    ROBOT_ROWS,
)

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "ambition_sprite2d_renderer"
SVG_PATH = PKG / "data/characters/player_robot_v3_svg/player-robot-v3.svg"
RIG_DIR = PKG / "targets/characters/rigged/player_robot_v3"
RIG_JSON = RIG_DIR / "player_robot_v3.rig.json"
VIEW_LABEL = "Player Robot - Side Right"

FRAME_WIDTH = 224
FRAME_HEIGHT = 224
CENTER_X = 112.0
GROUND_Y = 158.0

# The shipping target and this builder share one row declaration. The full
# future vocabulary remains in data/fighter_motion_vocabulary.yaml; ROBOT_ROWS
# is the current-art category surface plus retained Ambition-specific rows.
ANIMATION_ORDER = [name for name, _frames, _duration in ROBOT_ROWS]
ROW_INFO = {
    name: {"frames": int(frames), "duration_ms": int(duration)}
    for name, frames, duration in ROBOT_ROWS
}
LOOPING = set(LOOPING_ROWS)

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


def _smooth01(value: float) -> float:
    q = max(0.0, min(1.0, float(value)))
    return q * q * (3.0 - 2.0 * q)


def _sample_pose(generator: SideRobotGenerator, animation: str, t: float) -> Pose:
    # Use a dense virtual clip so source choreography can be resampled into a
    # different destination frame count without coupling to its legacy timing.
    count = 101
    index = int(round(max(0.0, min(1.0, t)) * (count - 1)))
    return generator.pose_for_animation(animation, index, count)


def _blend_pose(first: Pose, second: Pose, amount: float) -> Pose:
    q = _smooth01(amount)
    out = Pose()
    for name in Pose.__dataclass_fields__:
        a = getattr(first, name)
        b = getattr(second, name)
        if isinstance(a, bool):
            value = b if q >= 0.5 else a
        elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
            value = float(a) + (float(b) - float(a)) * q
        else:
            value = b if q >= 0.5 else a
        setattr(out, name, value)
    return out


def _pose_for_motion(
    generator: SideRobotGenerator,
    animation: str,
    frame_index: int,
    frame_count: int,
) -> Pose:
    """Resolve one v3 fighter verb into current robot choreography.

    Several current-art categories deliberately borrow a mature source motion,
    but the category remains a real clip and may add a category-specific pose
    adjustment here. This keeps the visual vocabulary complete without making
    SideRobotGenerator's whole robot family inherit protagonist-only Smash rows.
    """

    t = 0.0 if frame_count <= 1 else frame_index / float(frame_count - 1)
    source = POSE_ALIASES.get(animation, animation)

    # Transition rows use a controlled portion of an existing loop/one-shot.
    if animation == "crouch_start":
        pose = _sample_pose(generator, "crouch", 0.5 * t)
    elif animation == "crouch_end":
        pose = _sample_pose(generator, "crouch", 0.5 + 0.5 * t)
    elif animation == "jump_squat":
        pose = _sample_pose(generator, "jump", 0.22 * t)
    elif animation == "shield_raise":
        pose = _blend_pose(Pose(), _sample_pose(generator, "block", 0.25), t)
    elif animation == "shield_release":
        pose = _blend_pose(_sample_pose(generator, "block", 0.25), Pose(), t)
    elif animation == "sleep_start":
        pose = _blend_pose(Pose(), _sample_pose(generator, "sleep", 0.25), t)
    elif animation == "wake":
        pose = _blend_pose(_sample_pose(generator, "sleep", 0.25), Pose(), t)
    elif animation in {"prone", "trip_idle"}:
        pose = _sample_pose(generator, "death", 1.0)
    elif animation in {"getup", "trip_getup", "shield_break_recover"}:
        pose = _sample_pose(generator, "death", 1.0 - t)
        pose.dead = False
        pose.collapse = max(0.0, pose.collapse * (1.0 - t))
    else:
        pose = generator.pose_for_animation(source, frame_index, frame_count)

    wave = math.sin(t * math.tau)
    arc = math.sin(t * math.pi)

    if animation == "idle_look_up":
        pose.head_tilt -= 16.0
        pose.head_dy -= 1.5
        pose.eye_squint *= 0.4
    elif animation == "walk_stop":
        pose.root_x += 4.0 * (1.0 - _smooth01(t))
        pose.body_tilt -= 7.0 * (1.0 - _smooth01(t))
    elif animation == "turnaround":
        pose.head_look = 1.0 - 2.0 * _smooth01(t)
        pose.body_tilt += 8.0 * arc
        pose.head_tilt -= 5.0 * arc
        pose.near_arm_upper -= 10.0 * arc
        pose.far_arm_upper += 10.0 * arc
    elif animation == "stumble":
        pose.root_x += 4.0 * wave
        pose.body_tilt += 12.0 * wave
        pose.head_tilt -= 7.0 * wave
    elif animation == "double_jump":
        pose.root_x *= 0.35
        pose.root_y -= 8.0 * arc
        pose.body_tilt *= 0.55
        pose.whole_body_rotation = -72.0 * arc
    elif animation == "fall_special":
        pose.root_y += 4.0 * t
        pose.body_tilt += 8.0
        pose.eye_squint = max(pose.eye_squint, 0.20)
    elif animation == "tumble":
        pose.root_x *= 0.22
        pose.root_y = -12.0 + 6.0 * t
        pose.whole_body_rotation = -360.0 * _smooth01(t)
    elif animation == "roll_back":
        pose.root_x = -pose.root_x
        pose.whole_body_rotation = -pose.whole_body_rotation
    elif animation == "spot_dodge":
        pose.root_x *= 0.08
        pose.root_y -= 5.0 * arc
        pose.whole_body_rotation *= 0.12
        pose.body_tilt += 18.0 * wave
    elif animation == "air_dodge":
        pose.root_x = 10.0 * math.sin((t - 0.5) * math.pi)
        pose.root_y = -12.0 - 4.0 * arc
        pose.body_tilt = -22.0 + 44.0 * t
        pose.near_leg_upper += 18.0 * arc
        pose.far_leg_upper -= 18.0 * arc
    elif animation == "platform_drop":
        pose.root_y += 8.0 * _smooth01(t)
        pose.body_tilt += 6.0
    elif animation == "footstool_jump":
        pose.root_y -= 7.0 * arc
        pose.near_leg_lower += 22.0 * arc
        pose.far_leg_lower += 22.0 * arc
    elif animation == "teeter_start":
        pose.body_tilt += 11.0 * _smooth01(t)
        pose.head_tilt -= 8.0 * _smooth01(t)
    elif animation == "teeter":
        pose.body_tilt += 11.0 + 4.0 * wave
        pose.head_tilt -= 8.0 + 3.0 * wave
        pose.near_arm_upper -= 12.0 * wave
        pose.far_arm_upper += 12.0 * wave
    elif animation == "parry":
        pose.body_tilt -= 7.0 * arc
        pose.head_tilt -= 4.0 * arc
        pose.eye_squint = 0.08
    elif animation == "shield_hit":
        pose.root_x -= 4.0 * arc
        pose.body_tilt += 14.0 * arc
        pose.eye_squint = 0.35
    elif animation == "launch":
        pose.root_x += 14.0 * t
        pose.root_y -= 10.0 * arc
        pose.whole_body_rotation = -120.0 * t
    elif animation == "meteor":
        pose.root_y += 15.0 * _smooth01(t)
        pose.whole_body_rotation = 120.0 * t
    elif animation in {"impact", "splat", "prone_damage", "grabbed_pummel"}:
        pose.body_tilt += 10.0 * wave
        pose.head_tilt -= 8.0 * wave
    elif animation == "ground_bounce":
        pose.root_y -= 8.0 * arc
        pose.whole_body_rotation = 36.0 * wave
    elif animation == "knockdown":
        pose.dead = False
        pose.collapse *= 0.85
    elif animation == "getup_attack":
        pose.root_x += 3.0 * arc
    elif animation in {"getup_roll", "tech_roll", "trip_roll", "grab_escape"}:
        pose.root_x *= 0.75
    elif animation == "wall_tech":
        pose.root_x -= 4.0
        pose.body_tilt *= 0.4
    elif animation == "ceiling_tech":
        pose.root_y = -14.0 + 8.0 * _smooth01(t)
        pose.whole_body_rotation = 180.0 * (1.0 - _smooth01(t))
    elif animation == "shield_break_launch":
        pose.root_y -= 14.0 * arc
        pose.whole_body_rotation = -180.0 * t
    elif animation == "shield_break_fall":
        pose.whole_body_rotation = -90.0 - 90.0 * t
    elif animation == "shield_break_collapse":
        pose.dead = False
        pose.eye_squint = 0.45
    elif animation == "dizzy":
        pose.head_tilt += 12.0 * wave
        pose.head_look = math.sin(t * math.tau * 2.0)
        pose.eye_squint = 0.45
    elif animation == "bury_start":
        pose.root_y += 10.0 * _smooth01(t)
    elif animation == "buried":
        pose.root_y += 12.0
        pose.body_tilt *= 0.3
    elif animation == "bury_escape":
        pose.root_y -= 10.0 * arc
        pose.near_arm_upper -= 30.0 * wave
        pose.far_arm_upper += 30.0 * wave
    elif animation == "jab":
        pose.root_x *= 0.35
        pose.body_tilt *= 0.55
        pose.slash *= 0.65
    elif animation == "dash_attack":
        pose.root_x += 9.0 * _smooth01(t)
        pose.body_tilt -= 11.0
    elif animation == "smash_forward":
        pose.root_x += 5.0 * arc
        pose.body_tilt -= 10.0 * arc
        pose.slash = max(1.0, pose.slash)
    elif animation == "smash_up":
        pose.root_y -= 4.0 * arc
        pose.slash = max(1.0, pose.slash)
    elif animation == "smash_down":
        pose.root_y += 3.0 * arc
        pose.slash = max(1.0, pose.slash)
    elif animation == "air_land":
        pose.root_y += 2.0 * arc
    elif animation == "final_smash":
        pose.root_y -= 4.0 * arc
        pose.body_tilt -= 10.0 * arc
        pose.near_arm_upper -= 35.0 * arc
        pose.far_arm_upper += 35.0 * arc
        pose.eye_squint = 0.08
    elif animation == "grab":
        pose.root_x += 3.0 * arc
        pose.near_arm_upper -= 20.0 * arc
        pose.near_arm_lower -= 26.0 * arc
    elif animation == "grab_hold":
        pose.near_arm_upper -= 18.0
        pose.near_arm_lower -= 22.0
        pose.far_arm_upper += 12.0
    elif animation == "pummel":
        pose.root_x += 2.0 * arc
        pose.near_arm_upper -= 15.0 * arc
    elif animation == "grabbed":
        pose.near_arm_upper -= 25.0
        pose.far_arm_upper += 25.0
        pose.near_leg_upper += 12.0
        pose.far_leg_upper -= 12.0
    elif animation.startswith("throw_"):
        if animation == "throw_back":
            pose.body_tilt += 18.0 * arc
            pose.whole_body_rotation = 35.0 * arc
        elif animation == "throw_up":
            pose.root_y -= 5.0 * arc
            pose.near_arm_upper -= 28.0 * arc
        elif animation == "throw_down":
            pose.root_y += 4.0 * arc
            pose.near_arm_upper += 24.0 * arc
        else:
            pose.root_x += 5.0 * arc
    elif animation == "ledge_catch":
        pose.root_y -= 4.0 * (1.0 - _smooth01(t))
    elif animation == "ledge_jump":
        pose.root_x *= 0.55
        pose.root_y -= 6.0 * arc
    elif animation == "ledge_drop":
        pose.root_y += 10.0 * _smooth01(t)
    elif animation == "trip_fall":
        pose.dead = False
        pose.collapse *= 0.65
        pose.whole_body_rotation *= 0.35
    elif animation == "trip_attack":
        pose.root_y += 2.0
    elif animation == "item_hold":
        pose.near_arm_upper -= 12.0
        pose.near_arm_lower -= 18.0
    elif animation == "item_hold_crouch":
        pose.near_arm_upper -= 10.0
        pose.near_arm_lower -= 12.0
    elif animation == "item_heavy_pickup":
        pose.body_tilt -= 10.0 * arc
        pose.near_arm_upper -= 16.0 * arc
        pose.far_arm_upper += 16.0 * arc
    elif animation == "item_heavy_carry":
        pose.body_tilt -= 8.0
        pose.near_arm_upper -= 18.0
        pose.far_arm_upper += 18.0
    elif animation == "item_drop":
        pose.near_arm_upper += 15.0 * _smooth01(t)
    elif animation == "item_swing":
        # Body choreography only; the held-item system supplies the item.
        pose.slash = 0.0
    elif animation == "taunt":
        pose.head_tilt -= 8.0 * arc
        pose.head_look = 1.0 - 0.5 * arc
    elif animation == "victory_hold":
        pose.body_bob *= 0.35
        pose.head_tilt -= 5.0
    elif animation == "loss":
        pose.body_tilt += 10.0
        pose.head_tilt += 12.0
        pose.eye_squint = 0.28

    return pose


def make_clips(doc: dict) -> dict:
    generator = SideRobotGenerator()
    default = Pose()
    rest, _parent, canonical = _bone_maps(doc)

    validate_motion_coverage(
        row_names=ANIMATION_ORDER,
        coverage=FIGHTER_MOTION_COVERAGE,
        scopes=APPLICABLE_MOTION_SCOPES,
        character="player_robot_v3",
    )

    clips: dict[str, dict] = {}
    for animation in ANIMATION_ORDER:
        info = ROW_INFO[animation]
        nframes = int(info["frames"])
        duration_ms = int(info["duration_ms"])
        loop = animation in LOOPING
        poses = [
            _pose_for_motion(generator, animation, i, nframes)
            for i in range(nframes)
        ]

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
                + _foot_pitch(POSE_ALIASES.get(animation, animation), i, side, poses[i].body_tilt)
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
        name="player_robot_v3",
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
        "source_animation_vocabulary": "data/fighter_motion_vocabulary.yaml",
        "motion_profile": "targets/characters/player_robot_v3_motion.py",
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
