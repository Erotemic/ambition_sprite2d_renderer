"""Shipping player robot, rendered from the user-authored SVG paper-doll rig.

This module intentionally has the same target name as ``configs/player_robot.yaml``.
Module targets win discovery conflicts, so publishing ``player_robot`` now uses
this SVG/bone rig while preserving the existing runtime filenames, animation
row vocabulary, timings, actor id, and attack hitbox metadata.
"""

from __future__ import annotations

import math
import random
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image, ImageDraw

from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet, write_canonical
from .robot_side import SideRobotGenerator

TARGET_NAME = "player_robot"
FRAME_SIZE = (224, 224)
RIG_PATH = (
    Path(__file__).resolve().parent
    / "rigged/player_robot/player_robot.rig.json"
)

ANIMATION_ORDER = [
    "idle", "walk", "run", "jump", "fall", "slash", "hit", "death",
    "blink_out", "blink_in", "dash", "hover", "ledge_grab",
    "dash_startup", "land_hard", "land_recovery", "wall_grab",
    "ledge_climb", "ledge_getup", "float_glide", "attack_side",
    "attack_up", "attack_down", "air_neutral", "air_forward", "air_back",
    "air_down", "air_up", "ledge_roll", "ledge_getup_attack", "crouch",
    "crouch_walk", "slide", "climb", "swim", "block", "roll",
    "wall_jump", "shoot", "aim", "charge", "interact",
]

_OLD_ROBOT_FX = SideRobotGenerator()
_ROWS_INFO = SideRobotGenerator.ANIMATIONS
ROWS: List[Tuple[str, int, int]] = [
    (name, int(_ROWS_INFO[name]["frames"]), int(_ROWS_INFO[name]["duration_ms"]))
    for name in ANIMATION_ORDER
]

ACTOR_METADATA = {
    "actor": {"character_id": "player", "display_name": "Player Robot"},
    "visual": {"default_pose": "idle"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": ["robot", "player"],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": {
                "height_px": 42.0,
                "distance_px": 82.0,
                "source": "explicit.profile.robot",
            },
            "climb": None,
            "fly": None,
            "swim": None,
            "crawl": None,
            "use_lifts": True,
            "door_access": ["public"],
        },
        "interactions": {
            "talk": True,
            "trade": None,
            "carry": None,
            "open_doors": ["public"],
        },
    },
    "brain": {"default_preset": "player"},
    "actions": {"default_preset": "player_default"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "action.melee.primary": {
            "animation": "slash",
            "events": [
                {"t": 0.35, "event": "hitbox_active_start", "source": "explicit.profile.robot"},
                {"t": 0.55, "event": "hitbox_active_end", "source": "explicit.profile.robot"},
            ],
        },
        "action.ranged.primary": {
            "animation": "shoot",
            "events": [
                {"t": 0.5, "event": "projectile_release", "source": "explicit.profile.robot"}
            ],
        },
    },
    "sockets": {
        "head": {"source": "explicit.profile.robot", "point": {"x": 112.0, "y": 64.0}},
        "chest": {"source": "explicit.profile.robot", "point": {"x": 112.0, "y": 94.0}},
        "hand_l": {"source": "explicit.profile.robot", "point": {"x": 96.0, "y": 104.0}},
        "hand_r": {"source": "explicit.profile.robot", "point": {"x": 128.0, "y": 104.0}},
        "muzzle": {"source": "explicit.profile.robot", "point": {"x": 138.0, "y": 98.0}},
        "projectile_origin": {"source": "explicit.profile.robot", "point": {"x": 138.0, "y": 98.0}},
    },
    "tags": ["robot", "player", "svg_rig"],
}


@lru_cache(maxsize=1)
def load_doc() -> RigDocument:
    if not RIG_PATH.exists():
        raise FileNotFoundError(
            f"missing rig {RIG_PATH}; rebuild it with "
            "`uv run python scripts/build_player_robot_svg.py build`"
        )
    return RigDocument.load(RIG_PATH)


def _rgba(hex_value: str, alpha: int = 255):
    value = hex_value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4)) + (alpha,)


def _point_along(origin, angle_deg: float, distance: float):
    a = math.radians(angle_deg)
    return (origin[0] + math.cos(a) * distance, origin[1] + math.sin(a) * distance)


def _slash_angle(animation: str, arc: float, hand_angle: float) -> float:
    arc = max(0.0, min(1.0, arc))
    if animation in {"attack_up", "air_up"}:
        return 12.0 - 118.0 * arc
    if animation in {"attack_down", "air_down"}:
        return -18.0 + 106.0 * arc
    if animation == "air_back":
        return 145.0 + 92.0 * arc
    if animation == "air_neutral":
        return hand_angle - 120.0 + 300.0 * arc
    if animation in {"air_forward", "attack_side", "slash", "ledge_getup_attack"}:
        return -62.0 + 94.0 * arc
    return hand_angle


def _draw_blade(draw: ImageDraw.ImageDraw, animation: str, base, hand_angle, slash, arc):
    if slash <= 0.02:
        return
    angle = _slash_angle(animation, arc, hand_angle)
    length = 22.0 + 8.0 * min(1.0, slash)
    tip = _point_along(base, angle, length)
    # Trailing fan: short alpha-stepped line segments avoid a heavy filled blob.
    for k in range(5, 0, -1):
        past = max(0.0, arc - k * 0.055)
        pa = _slash_angle(animation, past, hand_angle)
        ptip = _point_along(base, pa, length * (0.92 + 0.016 * k))
        draw.line([base, ptip], fill=(115, 235, 255, 22 + 18 * (6 - k)), width=max(1, 6 - k))
    draw.line([base, tip], fill=(24, 27, 34, 255), width=5)
    draw.line([base, tip], fill=(190, 128, 255, 255), width=3)
    core = _point_along(base, angle, length * 0.84)
    draw.line([base, core], fill=(245, 255, 255, 235), width=1)


def _pixel_scatter(draw: ImageDraw.ImageDraw, seed: int, center, amount: float, arriving: bool):
    rng = random.Random(seed)
    count = int(10 + amount * 24)
    for i in range(count):
        spread = 12 + 34 * amount
        dx = rng.uniform(-spread, spread)
        dy = rng.uniform(-spread * 0.75, spread * 0.75)
        if arriving:
            dx *= (1.0 - amount * 0.65)
            dy *= (1.0 - amount * 0.65)
        s = rng.choice((1, 1, 2, 2, 3))
        alpha = int(65 + 150 * amount)
        x = center[0] + dx
        y = center[1] + dy
        draw.rectangle((x - s, y - s, x + s, y + s), outline=(35, 226, 255, alpha), width=1)



def _draw_thruster_plume(
    draw: ImageDraw.ImageDraw,
    origin,
    *,
    phase: float,
    glide: bool,
) -> None:
    """Draw a broad, long, three-layer boot jet.

    The prior SVG replacement used a 6px-wide / 14px-long triangle, which read
    as a tiny detached spark. This keeps the old player's white-hot/cyan flame
    construction, but deliberately makes the silhouette wider and longer.
    """
    flicker = 0.72 + 0.28 * math.sin(phase)
    ox, oy = origin
    # Glide thrust leans slightly backward; hover thrust stays vertical.
    angle = math.radians(100.0 if glide else 90.0)
    dx, dy = math.cos(angle), math.sin(angle)
    px, py = -dy, dx

    def point(distance: float, lateral: float = 0.0):
        return (ox + dx * distance + px * lateral, oy + dy * distance + py * lateral)

    halo_len = 38.0 + 14.0 * flicker
    halo_w = 10.0 + 3.0 * flicker
    draw.polygon(
        [point(-1.0, 0.0), point(halo_len, -halo_w), point(halo_len, halo_w)],
        fill=(20, 231, 255, int(64 + 28 * flicker)),
    )

    outer_len = 31.0 + 11.0 * flicker
    outer_w = 7.5 + 2.0 * flicker
    draw.polygon(
        [point(1.0, 0.0), point(outer_len, -outer_w), point(outer_len, outer_w)],
        fill=(20, 231, 255, int(165 + 40 * flicker)),
    )

    inner_len = 21.0 + 7.0 * flicker
    inner_w = 4.2 + 1.0 * flicker
    draw.polygon(
        [point(2.0, 0.0), point(inner_len, -inner_w), point(inner_len, inner_w)],
        fill=(255, 235, 130, int(195 + 35 * flicker)),
    )

    core_len = 12.0 + 5.0 * flicker
    core_w = 2.0 + 0.4 * flicker
    draw.polygon(
        [point(2.0, 0.0), point(core_len, -core_w), point(core_len, core_w)],
        fill=(255, 255, 245, int(225 + 25 * flicker)),
    )


def _boot_thruster_origin(foot_world):
    # Place the nozzle near the middle of the sole rather than at the ankle.
    return (
        foot_world.origin[0] * 0.48 + foot_world.tip[0] * 0.52,
        foot_world.origin[1] * 0.48 + foot_world.tip[1] * 0.52 + 2.0,
    )

def _apply_fx(img: Image.Image, animation: str, frame_idx: int, nframes: int) -> Image.Image:
    doc = load_doc()
    t = doc.frame_time(animation, frame_idx, nframes)
    world, params = doc.solve(animation, t)

    background = Image.new("RGBA", img.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(background, "RGBA")
    foreground = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(foreground, "RGBA")

    if animation in {"dash", "dash_startup", "slide"}:
        strength = 1.0 if animation == "dash" else 0.7
        for i in range(5):
            y = 49 + i * 8
            bd.line([(8 + i * 3, y), (43 + i * 2, y - 2)], fill=(35, 228, 255, int(150 * strength - i * 18)), width=max(1, 4 - i // 2))

    if animation in {"hover", "float_glide"}:
        for side_idx, side in enumerate(("far", "near")):
            foot = world[f"{side}_leg_foot"]
            origin = _boot_thruster_origin(foot)
            _draw_thruster_plume(
                fd,
                origin,
                phase=frame_idx * 1.7 + side_idx * math.pi / 2.0,
                glide=animation == "float_glide",
            )

    if animation == "swim":
        for i in range(5):
            x = 42 + i * 13 + math.sin((t + i) * math.tau) * 3
            y = 24 + ((i * 17 + frame_idx * 5) % 70)
            r = 1 + (i % 2)
            fd.ellipse((x - r, y - r, x + r, y + r), outline=(60, 226, 255, 150), width=1)

    if animation == "block":
        pulse = 1.0 + 0.05 * math.sin(t * math.tau)
        box = (64 - 40 * pulse, 63 - 48 * pulse, 64 + 40 * pulse, 63 + 48 * pulse)
        fd.ellipse(box, fill=(65, 222, 255, 24), outline=(63, 229, 255, 190), width=2)

    hand = world["near_arm_hand"]
    base = hand.tip
    slash = float(params.get("slash", 0.0))
    arc = float(params.get("slash_arc", t))
    if animation in {
        "slash", "attack_side", "attack_up", "attack_down", "air_neutral",
        "air_forward", "air_back", "air_down", "air_up", "ledge_getup_attack",
    }:
        _draw_blade(fd, animation, base, hand.angle, max(0.35, slash), arc)

    if animation in {"aim", "charge", "shoot"}:
        pulse = 0.55 + 0.45 * math.sin((t + 0.1) * math.pi)
        r = 3 + 4 * pulse
        fd.ellipse((base[0] - r, base[1] - r, base[0] + r, base[1] + r), fill=(25, 233, 255, 75), outline=(193, 128, 255, 220), width=2)
        if animation == "shoot" and 0.35 <= t <= 0.72:
            tip = _point_along(base, 0.0, 20 + 15 * (t - 0.35) / 0.37)
            fd.line([base, tip], fill=(245, 255, 255, 240), width=3)
            fd.ellipse((tip[0] - 3, tip[1] - 3, tip[0] + 3, tip[1] + 3), fill=(23, 234, 255, 220))

    if animation == "hit":
        for angle in (-65, -20, 25, 70):
            a = _point_along((78, 48), angle, 7)
            b = _point_along((78, 48), angle, 14)
            fd.line([a, b], fill=(255, 238, 120, 230), width=2)

    if animation in {"blink_out", "blink_in"}:
        # Reuse the original player's authored teleport presentation: portal
        # rings + slivers and horizontally sliced actor fragments. This is much
        # more legible than fading the whole paper doll uniformly.
        fr = doc.frame
        root_x = float(fr.get("center_x", img.width / 2.0)) + float(params.get("root_x", 0.0))
        ground_y = float(fr.get("ground_y", img.height - 2.0)) + float(params.get("root_y", 0.0))
        teleported = Image.new("RGBA", img.size, (0, 0, 0, 0))
        _OLD_ROBOT_FX._composite_teleport_actor(
            teleported,
            img,
            animation,
            frame_idx,
            nframes,
            1.0,
        )
        img = teleported
        if animation == "blink_out":
            _OLD_ROBOT_FX._draw_blink_out_fx(
                background, root_x, ground_y, 1.0, frame_idx, nframes
            )
        else:
            _OLD_ROBOT_FX._draw_blink_in_fx(
                background, root_x, ground_y, 1.0, frame_idx, nframes
            )

    if animation == "death":
        fade = max(0.45, 1.0 - t * 0.48)
        img = img.copy()
        img.putalpha(img.getchannel("A").point(lambda v: int(v * fade)))

    result = Image.new("RGBA", img.size, (0, 0, 0, 0))
    result.alpha_composite(background)
    result.alpha_composite(img)
    result.alpha_composite(foreground)
    return result


def render_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    image = load_doc().render_frame(animation, frame_idx, frame_count)
    return _apply_fx(image, animation, frame_idx, frame_count)


def frame_meta(animation: str, frame_idx: int, frame_count: int) -> dict:
    doc = load_doc()
    world, _params = doc.solve(animation, doc.frame_time(animation, frame_idx, frame_count))
    head = world["head"].origin
    near_hand = world["near_arm_hand"].tip
    far_hand = world["far_arm_hand"].tip
    return {
        "anchors": {
            "head": [round(head[0], 3), round(head[1] - 14.0, 3)],
            "chest": [round(world["torso"].origin[0], 3), round(world["torso"].origin[1], 3)],
            "hand_l": [round(near_hand[0], 3), round(near_hand[1], 3)],
            "hand_r": [round(far_hand[0], 3), round(far_hand[1], 3)],
            "muzzle": [round(near_hand[0], 3), round(near_hand[1], 3)],
            "projectile_origin": [round(near_hand[0], 3), round(near_hand[1], 3)],
        }
    }



def _translated_legacy_hitboxes() -> Dict[str, dict]:
    """Keep legacy combat geometry at its authored 128px size.

    The SVG rig uses a larger logical canvas so a rotating roll and long boot
    flames cannot clip. Scaling the old hitbox authoring with that canvas would
    incorrectly enlarge every attack, so translate the original 128px geometry
    into the new root/ground coordinate system without changing its dimensions.
    """
    hitboxes: Dict[str, dict] = SideRobotGenerator().attack_hitboxes((128, 128))
    dx = load_doc().frame["center_x"] - 64.0
    dy = load_doc().frame["ground_y"] - 118.0
    for spec in hitboxes.values():
        bbox = spec.get("bbox")
        if bbox is not None:
            x, y, w, h = bbox
            spec["bbox"] = (int(round(x + dx)), int(round(y + dy)), w, h)
        poly = spec.get("poly")
        if poly is not None:
            spec["poly"] = [
                (round(float(x) + dx, 4), round(float(y) + dy, 4))
                for x, y in poly
            ]
    return hitboxes

def render(out_dir: str | Path, **opts):
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    hitboxes: Dict[str, dict] = _translated_legacy_hitboxes()
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        frame_meta_fn=frame_meta,
        auto_crop=False,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning={"collision_scale": 1.65},
        animation_key_map={name: name for name in ANIMATION_ORDER},
        attack_hitboxes=hitboxes,
        trim=True,
    )
    keys = (
        "spritesheet", "yaml", "ron", "actor", "canonical",
        "canonical_transparent", "preview",
    )
    return [Path(outputs[key]) for key in keys if outputs.get(key)]


def render_canonical(out_dir: str | Path, **opts):
    del opts
    return write_canonical(
        TARGET_NAME,
        ROWS,
        render_frame,
        Path(out_dir),
        frame_size=FRAME_SIZE,
    )


__all__ = [
    "ACTOR_METADATA", "ANIMATION_ORDER", "FRAME_SIZE", "ROWS", "TARGET_NAME",
    "frame_meta", "load_doc", "render", "render_canonical", "render_frame",
]
