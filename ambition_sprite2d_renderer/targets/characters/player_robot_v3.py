"""Shipping player robot, rendered from the user-authored SVG paper-doll rig.

This module intentionally has the same target name as ``configs/player_robot_v3.yaml``.
Module targets win discovery conflicts, so publishing ``player_robot_v3`` now uses
this SVG/bone rig while preserving the existing runtime filenames, animation
row vocabulary, timings, actor id, and attack hitbox metadata.
"""

from __future__ import annotations

import math
import random
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFilter

from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet, write_canonical
from .robot_side import SideRobotGenerator

TARGET_NAME = "player_robot_v3"
FRAME_SIZE = (224, 224)
RIG_PATH = (
    Path(__file__).resolve().parent
    / "rigged/player_robot_v3/player_robot_v3.rig.json"
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
            "`uv run python scripts/build_player_robot_v3_svg.py build`"
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
    layer: Image.Image,
    origin,
    *,
    phase: float,
    size: float,
    intensity: float,
    angle_deg: float,
) -> None:
    """Draw a layered, gently irregular boot-thruster plume.

    ``size`` controls the silhouette independently of ``intensity`` so slow
    fall can use a visibly smaller exhaust without looking like a dimmed copy
    of full flight.  The shapes are deliberately asymmetric and mildly
    animated: a perfectly mirrored triangle reads as a UI marker, whereas the
    tapered shoulders, waist, and wandering tip read as hot moving exhaust.
    """
    size = max(0.1, float(size))
    intensity = max(0.0, min(1.0, float(intensity)))

    # Keep flicker subtle enough that the nozzle remains visually attached to
    # the boot.  Most of the motion happens at the plume tip.
    pulse = 0.94 + 0.08 * math.sin(phase)
    tip_wander = math.sin(phase * 1.73 + 0.6)
    angle = math.radians(angle_deg + 1.8 * tip_wander)
    dx, dy = math.cos(angle), math.sin(angle)
    px, py = -dy, dx
    ox, oy = origin

    # Make both hover and slow-fall exhaust read as punchier boot jets:
    # shorter overall but with a broader silhouette.
    length = 34.0 * size * pulse
    width = 13.5 * size * (0.98 + 0.07 * math.cos(phase * 1.31))

    def point(distance: float, lateral: float = 0.0):
        return (
            ox + dx * distance + px * lateral,
            oy + dy * distance + py * lateral,
        )

    def plume_points(length_scale: float, width_scale: float, wander: float):
        plume_len = length * length_scale
        plume_w = width * width_scale
        # Broad nozzle shoulders taper through a narrow waist before ending in
        # an off-center tip.  The unequal sides avoid the old flat triangle.
        return [
            point(0.0, -plume_w * 0.42),
            point(0.0, plume_w * 0.42),
            point(plume_len * 0.14, plume_w * 0.82),
            point(plume_len * 0.38, plume_w * 0.56),
            point(plume_len * 0.68, plume_w * 0.34),
            point(plume_len, plume_w * 0.13 * wander),
            point(plume_len * 0.66, -plume_w * 0.29),
            point(plume_len * 0.36, -plume_w * 0.50),
            point(plume_len * 0.13, -plume_w * 0.74),
        ]

    outer = plume_points(1.0, 1.0, tip_wander)
    middle = plume_points(0.72, 0.68, -tip_wander)
    core = plume_points(0.42, 0.38, tip_wander * 0.35)

    # A blurred cyan bloom provides volume without turning the flame into a
    # solid opaque wedge.  It is intentionally much softer during slow fall.
    glow = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow, "RGBA")
    glow_draw.polygon(
        outer,
        fill=(20, 231, 255, int((42 + 42 * intensity) * intensity)),
    )
    nozzle_r = 4.0 * size
    glow_draw.ellipse(
        (ox - nozzle_r, oy - nozzle_r, ox + nozzle_r, oy + nozzle_r),
        fill=(154, 250, 255, int(75 + 65 * intensity)),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(radius=2.0 + 2.5 * size))
    layer.alpha_composite(glow)

    draw = ImageDraw.Draw(layer, "RGBA")
    draw.polygon(
        outer,
        fill=(18, 208, 255, int(115 + 90 * intensity)),
    )
    draw.polygon(
        middle,
        fill=(76, 236, 255, int(160 + 72 * intensity)),
    )
    draw.polygon(
        core,
        fill=(250, 255, 244, int(205 + 45 * intensity)),
    )

    # Short bright nozzle lip and tiny exhaust motes make the source read as a
    # boot engine rather than a detached flame sprite.
    lip_a = point(0.8, -width * 0.31)
    lip_b = point(0.8, width * 0.31)
    draw.line(
        [lip_a, lip_b],
        fill=(232, 255, 255, 235),
        width=max(1, round(2 * size)),
    )

    mote_count = 2 if size >= 0.8 else 1
    for index in range(mote_count):
        mote_phase = phase + index * 2.1
        distance = length * (
            0.78 + 0.13 * index + 0.035 * math.sin(mote_phase)
        )
        lateral = width * 0.18 * math.sin(mote_phase * 1.9)
        mx, my = point(distance, lateral)
        radius = max(0.7, size * (1.15 - index * 0.25))
        draw.ellipse(
            (mx - radius, my - radius, mx + radius, my + radius),
            fill=(92, 239, 255, int(95 + 70 * intensity)),
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
        # Full flight uses a long, bright plume.  ``float_glide`` is the slow-
        # fall state, so its jets are deliberately smaller, softer, and angled
        # slightly backward instead of reusing the full-flight silhouette.
        slow_fall = animation == "float_glide"
        for side_idx, side in enumerate(("far", "near")):
            foot = world[f"{side}_leg_foot"]
            origin = _boot_thruster_origin(foot)
            _draw_thruster_plume(
                foreground,
                origin,
                phase=frame_idx * 1.7 + side_idx * math.pi / 2.0,
                size=0.56 if slow_fall else 1.0,
                intensity=0.68 if slow_fall else 1.0,
                angle_deg=102.0 if slow_fall else 90.0,
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



# ── The protagonist's slash geometry ─────────────────────────────────────────
#
# ⚠ THIS BELONGS TO v3, and lives here for that reason (Jon, 2026-08-02: "not
# every character should inherit this particular slash vfx, sfx, hurtbox. This
# belongs to the player v3"). `SideRobotGenerator` is shared by every robot in
# the family — the enemies and their variants — so authoring the protagonist's
# swing there gave a goblin-tier robot the hero's reach.
#
# **Slashes are HALF DISCS, not cones.** A cone is narrow at the body and flares
# outward, which is backwards for a swing: close to the pivot the blade passes
# through every angle of the arc, and only the forward part of it ever reaches
# full distance. So the swept region is flat and TALL against the body, bulges,
# and tapers to a blunt point.
#
# The numbers come from measuring Jon's sketch: 6.6 player-widths across, 1.9
# player-heights tall, near edge 86% of full height and far end 38%.
#
# ⚠ SCALE ASSUMPTION. The sketch's player box is drawn at aspect 0.31 where the
# real collision body is 0.63, so scaling by its width and by its height
# disagree by 2x (reach 197 vs 99 world units). These take the HEIGHT reading,
# which keeps reach where it already was and makes this a pure SHAPE change
# rather than a shape-and-balance one. `SLASH_REACH` is the single knob.
SLASH_REACH = 128 * 1.53
SLASH_NEAR = 128 * 0.59
SLASH_FAR = 128 * 0.27
# How far above the body's centre the swing's axis sits. A slash comes down
# across the chest, not out of the navel — but it was h*0.28 and Jon read that
# as "tilts too much upward in the side jab", so it is a nudge now, not a lift.
SLASH_RISE = 128 * 0.0
# Samples per control-point segment on the arc. The outline used to be the five
# control points themselves, which read as a faceted polyline exactly where the
# blade is widest.
SLASH_ARC_STEPS = 6


def _slash_spline(control, steps: int = SLASH_ARC_STEPS):
    """Catmull-Rom through the envelope's control points, clamped at the ends.

    The control points ARE the shape's definition — editing the swing means
    editing them — and this only decides how smoothly the outline passes
    through them. "Smooth like a sword slash" is a curve, not a polyline.
    """
    pts = []
    ext = [control[0]] + list(control) + [control[-1]]
    for i in range(len(ext) - 3):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        for s in range(steps):
            u = s / steps
            u2, u3 = u * u, u * u * u
            pts.append(
                tuple(
                    0.5
                    * (
                        2 * p1[k]
                        + (-p0[k] + p2[k]) * u
                        + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * u2
                        + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * u3
                    )
                    for k in (0, 1)
                )
            )
    pts.append(control[-1])
    return pts


def _convex_hull(points):
    """Monotone-chain hull, counter-clockwise.

    **The authored polygon must BE the tested polygon.** The runtime lowers a
    convex volume through `ConvexPolygon::from_convex_hull`, so a concave
    authored outline is silently played as its hull — a shape nobody drew and
    the debug overlay does not show. Catmull-Rom overshoots slightly at the
    belly, which is exactly enough to make that happen. Hulling here also gives
    Jon's rule for free: the volume is a convex poly AROUND the art, never
    inside it, so nothing that is drawn fails to hit.
    """
    pts = sorted(set((round(x, 4), round(y, 4)) for x, y in points))
    if len(pts) < 3:
        return list(pts)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _half_disc(ox, oy, dx, dy, reach, near_half, far_half, belly=1.16):
    """The swept region of a SLASH: flat against the body, round outside.

    `(ox, oy)` is the midpoint of the flat near edge and `(dx, dy)` the cardinal
    swing direction. The outline runs up the near edge, bulges through `belly`,
    bevels in at the shoulder and closes on a blunt point at `reach`.

    The opposite taper to a cone: `near_half > far_half`, and that inversion is
    the point. Presentation is fine with it — `SwingShape::oriented_bounds`
    takes the wider END, so a near-heavy volume gets a correct enclosing quad
    with no runtime change.
    """
    plen = math.hypot(dx, dy) or 1.0
    ux, uy = dx / plen, dy / plen
    px, py = -uy, ux
    shoulder = far_half + (near_half - far_half) * 0.45
    control = [
        (0.0, near_half),
        (0.42, near_half * belly),
        (0.66, shoulder),
        (0.88, far_half),
        (1.0, 0.0),
    ]
    arc = _slash_spline(control)

    def at(t, half):
        return (ox + ux * reach * t + px * half, oy + uy * reach * t + py * half)

    outline = [at(t, half) for t, half in arc]
    outline += [at(t, -half) for t, half in reversed(arc[:-1])]
    return _convex_hull(outline)


def _player_attack_hitboxes(size: Tuple[int, int]) -> Dict[str, dict]:
    """v3's OWN attack geometry. Half discs everywhere but the down-tilt.

    The down-tilt stays a Marth-like poke by Jon's call: a thrust reads by
    reach, not by area. `air_neutral` stays the family's ring — a half disc has
    a direction and a spin has none — and no move binds that row anyway.
    """
    w, h = size
    cx = w // 2
    body_cy = h * 0.47
    slash_y = body_cy - SLASH_RISE
    family = SideRobotGenerator().attack_hitboxes(size)

    def shaped(poly):
        """One authored shape, and a bbox DERIVED from it.

        The bbox used to be hand-written beside the poly and the two disagreed
        badly — the hull reached 1.8x further than the rectangle next to it, and
        which one hurt you depended on which system did the asking.
        """
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        x0, y0 = int(math.floor(min(xs))), int(math.floor(min(ys)))
        x1, y1 = int(math.ceil(max(xs))), int(math.ceil(max(ys)))
        return {
            "active_frames": [0, 1, 2],
            "bbox": (x0, y0, x1 - x0, y1 - y0),
            "poly": poly,
        }

    return {
        "attack_side": shaped(
            _half_disc(cx - w * 0.06, slash_y, 1.0, 0.0, SLASH_REACH, SLASH_NEAR, SLASH_FAR)
        ),
        "attack_up": shaped(
            _half_disc(cx, body_cy - h * 0.04, 0.0, -1.0,
                       SLASH_REACH * 0.88, SLASH_NEAR * 0.92, SLASH_FAR)
        ),
        "air_up": shaped(
            _half_disc(cx, body_cy - h * 0.04, 0.0, -1.0,
                       SLASH_REACH * 0.84, SLASH_NEAR * 0.88, SLASH_FAR)
        ),
        # The one attack that is not a slash.
        "attack_down": family["attack_down"],
        "air_down": shaped(
            _half_disc(cx, body_cy + h * 0.04, 0.0, 1.0,
                       SLASH_REACH * 0.84, SLASH_NEAR * 0.88, SLASH_FAR)
        ),
        "air_forward": shaped(
            _half_disc(cx - w * 0.02, slash_y, 1.0, 0.0,
                       SLASH_REACH * 0.94, SLASH_NEAR, SLASH_FAR)
        ),
        "air_back": shaped(
            _half_disc(cx + w * 0.02, slash_y, -1.0, 0.0,
                       SLASH_REACH * 0.86, SLASH_NEAR * 0.94, SLASH_FAR)
        ),
        # Unbound by any move, and a ring rather than a half disc. Left as the
        # family authored it.
        "air_neutral": family["air_neutral"],
    }


def _translated_legacy_hitboxes() -> Dict[str, dict]:
    """Keep combat geometry at its authored 128px size.

    The SVG rig uses a larger logical canvas so a rotating roll and long boot
    flames cannot clip. Scaling the hitbox authoring with that canvas would
    incorrectly enlarge every attack, so translate the 128px geometry into the
    new root/ground coordinate system without changing its dimensions.
    """
    hitboxes: Dict[str, dict] = _player_attack_hitboxes((128, 128))
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
