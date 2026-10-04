"""Shipping player robot, rendered from the user-authored SVG paper-doll rig.

This is the ONLY definition of ``player_robot_v3``. It preserves the runtime
filenames, animation row vocabulary, timings, actor id and attack hitbox
metadata of the procedural config it replaced.

⛔ There used to be a ``configs/player_robot_v3.yaml`` beside it, kept on the
assumption that "module targets win discovery conflicts". They do not win
reliably: that YAML declared ``target: robot`` while claiming
``output_name: player_robot_v3``, so a SINGLE-target publish rendered this SVG
rig (3072x2468) and a FULL publish rendered the robot rig over the top of it
(2815x2312, byte-identical to ``player_robot_v2``). The game drew the wrong body
and each targeted fix was undone by the next full run. The YAML is deleted; do
not reintroduce a config under a name a module target already claims.
"""

from __future__ import annotations

import dataclasses
import math
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageFilter

from ambition_sprite2d_renderer.core.draw import blending_draw

from ...authoring import rigdoc
from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet, rendering_canonical_only, write_canonical
from ...authoring.portrait import (
    FaceGuide,
    PortraitClip,
    render_framed_portrait,
    write_portrait_sheet,
)
from ...core import slash_envelope
from .robot_side import RigCanvas, SideRobotGenerator, _on_grid, fx_piece, transposed
from .player_robot_v3_gameplay import hurtbox_parts_for_rows
from .player_robot_v3_motion import EFFECT_ALIASES, MIRRORED, ROBOT_ROWS
from .player_robot_v3_strikes import STRIKES

TARGET_NAME = "player_robot_v3"
FRAME_SIZE = (224, 224)
PUBLISH_PADDING = (16, 16, 16, 16)
RIG_PATH = (
    Path(__file__).resolve().parent
    / "rigged/player_robot_v3/player_robot_v3.rig.json"
)

ANIMATION_ORDER = [name for name, _frames, _duration in ROBOT_ROWS]

# The robot is NOT left-right symmetric: it has ONE ear piece, the cup the
# antenna rises from. A facing flip therefore moved it to the other side of the
# head, which anyone watching a turn could see. Every row is published a second
# time drawn from the robot's OTHER side — no ear cup, only the antenna's top
# showing from behind the shell — then mirrored, and
# the game draws that row instead of flipping (`SheetRow::mirror_of`).
MIRROR_OF: Dict[str, str] = {MIRRORED.format(name): name for name in ANIMATION_ORDER}
ROWS: List[Tuple[str, int, int]] = list(ROBOT_ROWS) + [
    (MIRRORED.format(name), frames, duration) for name, frames, duration in ROBOT_ROWS
]


def _row(animation: str) -> Tuple[str, bool]:
    """The authored row a sheet row draws, and whether it is the mirror image."""
    original = MIRROR_OF.get(animation)
    return (original, True) if original is not None else (animation, False)


def _other_side(params: dict) -> dict:
    """Parameters for the head seen from its other side: the robot's one ear
    piece (cup + antenna) is on the far ear, so the cup vanishes and only the
    antenna's top shows behind the shell. A look-back head (the back air)
    already shows the far side, so its mirror shows the near side again."""
    near = float(params.get("near_ear_vis", 1.0))
    far = float(params.get("far_ear_vis", 0.0))
    return {**params, "near_ear_vis": far, "far_ear_vis": near}


#: The robot family's teleport (portal pieces and the warp that takes a body
#: apart), drawn at this rig's scale.
_TELEPORT = SideRobotGenerator()

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


# ── Effects ──────────────────────────────────────────────────────────────────
# Every effect is a set of PIECES: a raster painted once at the rig's supersample
# (``fx_piece``), placed turned and faded by its draw (``RigCanvas.put``) on a
# supersampled effect canvas that is reduced as the body is
# (``rigdoc.downsampled_canvas``). The part flipbook then stores each raster once
# and draws it where the frame puts it. An effect painted straight into the frame
# is a new raster in every frame it changes.
#
# Coordinates below are logical frame pixels; ``_FxLayer`` scales them to the
# supersampled canvas and ``K`` scales sizes a painter draws with.

#: The effect canvases' supersample (the body's is the rig document's own).
K = 4.0
_RASTERS: Dict[tuple, Tuple[Image.Image, Tuple[float, float]]] = {}


def _point_along(origin, angle_deg: float, distance: float):
    a = math.radians(angle_deg)
    return (origin[0] + math.cos(a) * distance, origin[1] + math.sin(a) * distance)


class _FxLayer:
    """One supersampled effect canvas (behind or in front of the body)."""

    def __init__(self, size: Tuple[int, int]) -> None:
        self.size = size
        self._rig: Optional[RigCanvas] = None

    @property
    def rig(self) -> RigCanvas:
        """The supersampled canvas, made when the first piece is placed."""
        if self._rig is None:
            self._rig = RigCanvas(Image.new("RGBA", (int(self.size[0] * K), int(self.size[1] * K)), (0, 0, 0, 0)))
        return self._rig

    def put(self, part, at, degrees: float, name: str, opacity: float = 1.0) -> None:
        """``part`` with its pivot at ``at`` (frame pixels)."""
        self.rig.put(part, (at[0] * K, at[1] * K), degrees, name, opacity)

    def reduced(self) -> Optional[Image.Image]:
        return None if self._rig is None else rigdoc.downsampled_canvas(self._rig.canvas, self.size)


def _raster(key: tuple, make) -> Tuple[Image.Image, Tuple[float, float]]:
    """A piece ``make()`` builds as ``(image, pivot)`` (a blurred glow, a cut
    quarter), cached under ``key``."""
    cached = _RASTERS.get(key)
    if cached is None:
        cached = _RASTERS[key] = make()
    return cached


# -- boot thrusters --------------------------------------------------------------

#: The plume's flicker: a few drawn phases, chosen per frame and boot. Each is
#: one raster; the flicker is which one a frame draws.
_PLUME_PHASES = (0.0, 1.7, 3.4, 5.1)


def _plume_shape(size: float, phase: float):
    """Outer, middle and core polygons, the nozzle lip and the motes of a boot
    plume pointing along +x from the nozzle at the origin (frame pixels)."""
    pulse = 0.94 + 0.08 * math.sin(phase)
    tip_wander = math.sin(phase * 1.73 + 0.6)
    length = 34.0 * size * pulse
    width = 13.5 * size * (0.98 + 0.07 * math.cos(phase * 1.31))

    def plume(length_scale: float, width_scale: float, wander: float):
        n, w = length * length_scale, width * width_scale
        # Broad nozzle shoulders taper through a narrow waist to an off-centre
        # tip: a mirrored triangle reads as a UI marker, not exhaust.
        return [
            (0.0, -w * 0.42), (0.0, w * 0.42), (n * 0.14, w * 0.82), (n * 0.38, w * 0.56),
            (n * 0.68, w * 0.34), (n, w * 0.13 * wander), (n * 0.66, -w * 0.29),
            (n * 0.36, -w * 0.50), (n * 0.13, -w * 0.74),
        ]

    motes = []
    for index in range(2 if size >= 0.8 else 1):
        mote_phase = phase + index * 2.1
        distance = length * (0.78 + 0.13 * index + 0.035 * math.sin(mote_phase))
        motes.append(((distance, width * 0.18 * math.sin(mote_phase * 1.9)), max(0.7, size * (1.15 - index * 0.25))))
    lip = ((0.8, -width * 0.31), (0.8, width * 0.31))
    return plume(1.0, 1.0, tip_wander), plume(0.72, 0.68, -tip_wander), plume(0.42, 0.38, tip_wander * 0.35), lip, motes, length, width


def _plume_glow(size: float, intensity: float):
    """The plume's soft cyan bloom: blurred, so its flicker is not worth a
    raster; one per plume size."""

    def make():
        outer, _middle, _core, _lip, _motes, length, width = _plume_shape(size, _PLUME_PHASES[0])
        blur = (2.0 + 2.5 * size) * K
        margin = int(math.ceil(3 * blur + 4.0 * size * K)) + 2
        w = int(math.ceil(length * 1.1 * K)) + 2 * margin
        h = int(math.ceil(width * 1.7 * K)) + 2 * margin
        ox, oy = float(margin), h / 2.0
        image = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = blending_draw(image)
        d.polygon([(ox + x * K, oy + y * K) for x, y in outer], fill=(20, 231, 255, int((42 + 42 * intensity) * intensity)))
        r = 4.0 * size * K
        d.ellipse((ox - r, oy - r, ox + r, oy + r), fill=(154, 250, 255, int(75 + 65 * intensity)))
        return image.filter(ImageFilter.GaussianBlur(radius=blur)), (ox, oy)

    return _raster(("v3_plume_glow", size, intensity), make)


def _plume(size: float, intensity: float, phase: float):
    outer, middle, core, lip, motes, length, width = _plume_shape(size, phase)

    def paint(d, ox, oy) -> None:
        def at(points):
            return [(ox + x * K, oy + y * K) for x, y in points]

        d.polygon(at(outer), fill=(18, 208, 255, int(115 + 90 * intensity)))
        d.polygon(at(middle), fill=(76, 236, 255, int(160 + 72 * intensity)))
        d.polygon(at(core), fill=(250, 255, 244, int(205 + 45 * intensity)))
        d.line(at(lip), fill=(232, 255, 255, 235), width=int(max(1, round(2 * size)) * K))
        for (mx, my), radius in motes:
            cx, cy, r = ox + mx * K, oy + my * K, radius * K
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(92, 239, 255, int(95 + 70 * intensity)))

    half = width * 0.9 * K
    return fx_piece(("v3_plume", size, intensity, phase), (-2 * K, -half, length * 1.05 * K, half), paint)


def _place_thrusters(front: _FxLayer, world, frame_idx: int, slow_fall: bool) -> None:
    """Both boot jets. Slow fall (``float_glide``) burns smaller, softer and
    angled back; full flight long and bright."""
    size, intensity, angle = (0.56, 0.68, 102.0) if slow_fall else (1.0, 1.0, 90.0)
    for side_idx, side in enumerate(("far", "near")):
        foot = world[f"{side}_leg_foot"]
        # The nozzle sits under the middle of the sole, not the ankle.
        origin = (foot.origin[0] * 0.48 + foot.tip[0] * 0.52, foot.origin[1] * 0.48 + foot.tip[1] * 0.52 + 2.0)
        phase = _PLUME_PHASES[(frame_idx + 2 * side_idx) % len(_PLUME_PHASES)]
        wander = math.sin(phase * 1.73 + 0.6)
        front.put(_plume_glow(size, intensity), origin, angle, f"{side}_jet_glow")
        front.put(_plume(size, intensity, phase), origin, angle + 1.8 * wander, f"{side}_jet")


# -- the line blade of the un-keyed attacks ----------------------------------------


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


def _stroke(length: float, width: float, color, key: str):
    """A straight stroke from the pivot along +x (frame pixels), one raster."""
    w = width * K

    def paint(d, ox, oy) -> None:
        d.line([(ox, oy), (ox + length * K, oy)], fill=color, width=max(1, int(round(w))))

    return fx_piece(("v3_stroke", key, round(length, 2), width, color), (-w, -w, length * K + w, w), paint)


def _blade(length: float):
    def paint(d, ox, oy) -> None:
        tip = (ox + length * K, oy)
        d.line([(ox, oy), tip], fill=(24, 27, 34, 255), width=int(5 * K))
        d.line([(ox, oy), tip], fill=(190, 128, 255, 255), width=int(3 * K))
        d.line([(ox, oy), (ox + length * 0.84 * K, oy)], fill=(245, 255, 255, 235), width=int(K))

    return fx_piece(("v3_line_blade", length), (-3 * K, -3 * K, (length + 3) * K, 3 * K), paint)


def _place_blade(front: _FxLayer, animation: str, base, hand_angle: float, slash: float, arc: float) -> None:
    """The energy blade and its trailing fan: five strokes at the angles the
    blade passed, faded by age. Two blade lengths (charging, full)."""
    if slash <= 0.02:
        return
    angle = _slash_angle(animation, arc, hand_angle)
    length = 22.0 + 8.0 * (0.5 if min(1.0, slash) < 0.7 else 1.0)
    for k in range(5, 0, -1):
        past = _slash_angle(animation, max(0.0, arc - k * 0.055), hand_angle)
        stroke = _stroke(length * (0.92 + 0.016 * k), max(1, 6 - k), (115, 235, 255, 22 + 18 * (6 - k)), f"fan{k}")
        front.put(stroke, base, past, f"blade_fan{k}")
    front.put(_blade(length), base, angle, "line_blade")


# -- the rest ------------------------------------------------------------------------


def _disc(radius: float, fill, outline, outline_w: float, key: str):
    """A filled and/or outlined circle about the pivot (frame pixels)."""
    r, w = radius * K, outline_w * K

    def paint(d, ox, oy) -> None:
        d.ellipse((ox - r, oy - r, ox + r, oy + r), fill=fill, outline=outline, width=int(round(w)))

    return fx_piece(("v3_disc", key, radius, fill, outline, outline_w), (-r - 1, -r - 1, r + 1, r + 1), paint)


def _shield_quarter(scale: float):
    """The lower right quarter of the shield bubble, its centre at the pivot
    (the canvas corner), on the mirror grid: the other three quarters are the
    same raster mirrored (``transposed``)."""

    def make():
        rx, ry, w = int(round(40 * scale * K)), int(round(48 * scale * K)), int(2 * K)
        full = Image.new("RGBA", (2 * rx + 4, 2 * ry + 4), (0, 0, 0, 0))
        # Pixels 2 .. 2 + 2r - 1: symmetric about the pixel EDGE 2 + r, where the
        # quarters meet.
        blending_draw(full).ellipse((2, 2, 2 + 2 * rx - 1, 2 + 2 * ry - 1), fill=(65, 222, 255, 24), outline=(63, 229, 255, 190), width=w)
        quarter = Image.new("RGBA", (_on_grid(rx + 2), _on_grid(ry + 2)), (0, 0, 0, 0))
        quarter.alpha_composite(full.crop((2 + rx, 2 + ry, 2 * rx + 4, 2 * ry + 4)))
        return quarter, (0.0, 0.0)

    return _raster(("v3_shield_quarter", scale), make)


def _place_shield(front: _FxLayer, center, t: float) -> None:
    """The shield bubble on the torso, breathing in three sizes."""
    quarter = _shield_quarter(1.0 + 0.05 * round(math.sin(t * math.tau)))
    for name, part in (
        ("shield_br", quarter),
        ("shield_bl", transposed(quarter, Image.FLIP_LEFT_RIGHT)),
        ("shield_tr", transposed(quarter, Image.FLIP_TOP_BOTTOM)),
        ("shield_tl", transposed(quarter, Image.ROTATE_180)),
    ):
        front.put(part, center, 0.0, name)


def _dash_lines():
    """The speed lines behind a dash, at full strength."""

    def paint(d, ox, oy) -> None:
        for i in range(5):
            y = oy + i * 8 * K
            d.line([(ox + i * 3 * K, y), (ox + (35 + i * 2) * K, y - 2 * K)], fill=(35, 228, 255, 150 - i * 18), width=int(max(1, 4 - i // 2) * K))

    return fx_piece(("v3_dash_lines",), (-2 * K, -5 * K, 46 * K, 35 * K), paint)


def _hit_sparks():
    def paint(d, ox, oy) -> None:
        for angle in (-65, -20, 25, 70):
            a = _point_along((ox, oy), angle, 7 * K)
            b = _point_along((ox, oy), angle, 14 * K)
            d.line([a, b], fill=(255, 238, 120, 230), width=int(2 * K))

    return fx_piece(("v3_hit_sparks",), (-16 * K, -16 * K, 16 * K, 16 * K), paint)


def _shot(length: float):
    """The shot leaving the hand: a beam along +x and its bright head."""

    def paint(d, ox, oy) -> None:
        tip = (ox + length * K, oy)
        d.line([(ox, oy), tip], fill=(245, 255, 255, 240), width=int(3 * K))
        d.ellipse((tip[0] - 3 * K, tip[1] - 3 * K, tip[0] + 3 * K, tip[1] + 3 * K), fill=(23, 234, 255, 220))

    return fx_piece(("v3_shot", length), (-3 * K, -4 * K, (length + 4) * K, 4 * K), paint)


def _render_body(doc: RigDocument, clip: str, t: float, solved, warp=None) -> Image.Image:
    """The rig's frame (``render_at``), or, with ``warp``, the same parts each
    moved and faded by ``warp(place, k) -> (dx, dy, opacity)`` (supersampled
    pixels; ``k`` numbers the BONES, so a head and its face move as one)."""
    if warp is None:
        return doc.render_at(clip, t, solved=solved)
    fr = doc.frame
    size = (int(fr["width"]), int(fr["height"]))
    S = float(max(1, int(fr.get("supersample", 4))))
    img = Image.new("RGBA", (int(size[0] * S), int(size[1] * S)), (0, 0, 0, 0))
    draw = blending_draw(img)
    world, params = solved
    bones: Dict[str, int] = {}
    for part in rigdoc.ordered_parts(rigdoc.visible_parts(doc.parts, doc.features), params):
        bone = part.get("bone")
        sprite = doc.sprite_raster(part, S)
        if bone not in world or sprite is None or rigdoc.part_channel_opacity(part, params) <= 0.01:
            continue
        bw = world[bone]
        dx, dy, fade = warp((bw.origin[0] * S, bw.origin[1] * S), bones.setdefault(bone, len(bones)))
        moved = {**world, bone: dataclasses.replace(bw, origin=(bw.origin[0] + dx / S, bw.origin[1] + dy / S))}
        faded = {**params, "body_opacity": max(0.0, min(1.0, float(params.get("body_opacity", 1.0)))) * fade}
        rigdoc.paint_part(img, draw, part, moved, S, faded, doc.palette, sprite=sprite, transform_cache=doc._sprite_transform_cache)
    return rigdoc.downsampled_canvas(img, size)


def _compose(animation: str, clip: str, t: float, solved, frame_idx: int, nframes: int) -> Image.Image:
    """The frame of ``animation`` (an authored row): the body of ``clip`` posed
    by ``solved`` at ``t``, between the effects behind and in front of it."""
    doc = load_doc()
    world, params = solved
    # A keyed strike is drawn entirely by the rig (its blade is a part), so it
    # borrows no other row's effects: `smash_charge` used to inherit the
    # `charge` orb and every attack the line-blade.
    effect = animation if animation in STRIKES else EFFECT_ALIASES.get(animation, animation)
    size = (int(doc.frame["width"]), int(doc.frame["height"]))
    back, front = _FxLayer(size), _FxLayer(size)
    warp = None

    if effect in {"dash", "dash_startup", "slide"}:
        back.put(_dash_lines(), (8, 49), 0.0, "dash_lines", 1.0 if effect == "dash" else 0.7)

    if effect in {"hover", "float_glide"}:
        _place_thrusters(front, world, frame_idx, slow_fall=effect == "float_glide")

    if effect == "swim":
        for i in range(5):
            x = 42 + i * 13 + math.sin((t + i) * math.tau) * 3
            y = 24 + ((i * 17 + frame_idx * 5) % 70)
            front.put(_disc(1 + (i % 2), None, (60, 226, 255, 150), 1, "bubble"), (x, y), 0.0, f"bubble{i}")

    if effect == "block":
        # Body-attached: centred on the torso.
        _place_shield(front, world["torso"].origin, t)

    hand = world["near_arm_hand"]
    base = hand.tip
    # A keyed strike carries the blade as a rig part on the hand; drawing this
    # line as well would be a second blade.
    if animation not in STRIKES and effect in {
        "slash", "attack_side", "attack_up", "attack_down", "air_neutral",
        "air_forward", "air_back", "air_down", "air_up", "ledge_getup_attack",
    }:
        slash = max(0.35, float(params.get("slash", 0.0)))
        _place_blade(front, effect, base, hand.angle, slash, float(params.get("slash_arc", t)))

    if effect in {"aim", "charge", "shoot"}:
        pulse = 0.55 + 0.45 * math.sin((t + 0.1) * math.pi)
        front.put(_disc(float(round(3 + 4 * pulse)), (25, 233, 255, 75), (193, 128, 255, 220), 2, "orb"), base, 0.0, "orb")
        if effect == "shoot" and 0.35 <= t <= 0.72:
            front.put(_shot(float(round(20 + 15 * (t - 0.35) / 0.37))), base, 0.0, "shot")

    if effect == "hit":
        front.put(_hit_sparks(), (78, 48), 0.0, "hit_sparks")

    if effect in {"blink_out", "blink_in"}:
        # The teleport takes the body apart part by part (robot_side's
        # ``_teleport_warp``) inside its portal rings and slivers.
        root_x = float(doc.frame.get("center_x", size[0] / 2.0)) + float(params.get("root_x", 0.0))
        ground_y = float(doc.frame.get("ground_y", size[1] - 2.0)) + float(params.get("root_y", 0.0))
        body_ss = float(max(1, int(doc.frame.get("supersample", 4))))
        warp = _TELEPORT._teleport_warp(effect, root_x * body_ss, body_ss, frame_idx, nframes)
        root_x, ground_y = root_x * K, ground_y * K
        if effect == "blink_out":
            _TELEPORT._place_blink_out_fx(back.rig, root_x, ground_y, K, frame_idx, nframes)
        else:
            _TELEPORT._place_blink_in_fx(back.rig, root_x, ground_y, K, frame_idx, nframes)
        _TELEPORT._place_teleport_scanlines(front.rig, effect, root_x, ground_y, K, frame_idx, nframes)

    body = _render_body(doc, clip, t, solved, warp)
    if effect == "death":
        # The whole body fades as one picture: its parts do not show through
        # each other.
        body = rigdoc.faded_canvas(body, max(0.45, 1.0 - t * 0.48))

    # Through rigdoc's seams, so the part flipbook knows what the frame is made
    # of (`part_flipbook.build_rig_flipbook`).
    result = Image.new("RGBA", size, (0, 0, 0, 0))
    for layer in (back.reduced(), body, front.reduced()):
        if layer is not None:
            rigdoc.composite_canvas(result, layer)
    return result


def render_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    row, mirrored = _row(animation)
    doc = load_doc()
    # A strike authors its own other-side clip (the blade stays in the hand that
    # holds it, which from this side is the far one); every other row is the
    # same pose seen from the other side.
    clip = MIRRORED.format(row) if mirrored and MIRRORED.format(row) in doc.clips else row
    t = doc.frame_time(clip, frame_idx, frame_count)
    world, params = doc.solve(clip, t)
    frame = _compose(row, clip, t, (world, _other_side(params) if mirrored else params), frame_idx, frame_count)
    # Mirrored about the logical frame's centre, so the published frame is
    # exactly what a flip of the whole frame would place — the runtime keeps
    # the same feet anchor, negated.
    return rigdoc.mirrored_canvas(frame) if mirrored else frame


def published_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    """A sheet frame as published: ``render_frame`` inside ``PUBLISH_PADDING``
    (``build_sheet``'s padding, through rigdoc's seam)."""
    pad_left, pad_top, pad_right, pad_bottom = PUBLISH_PADDING
    frame = render_frame(animation, frame_idx, frame_count)
    padded = Image.new("RGBA", (frame.width + pad_left + pad_right, frame.height + pad_top + pad_bottom), (0, 0, 0, 0))
    rigdoc.composite_canvas(padded, frame, (pad_left, pad_top))
    return padded


def frame_meta(animation: str, frame_idx: int, frame_count: int) -> dict:
    row, mirrored = _row(animation)
    clip = row
    if mirrored and MIRRORED.format(row) in load_doc().clips:
        clip = MIRRORED.format(row)
    meta = _frame_meta(clip, frame_idx, frame_count)
    if mirrored:
        width = float(load_doc().frame["width"])
        meta["anchors"] = {k: [round(width - x, 3), y] for k, (x, y) in meta["anchors"].items()}
    return meta


def _frame_meta(animation: str, frame_idx: int, frame_count: int) -> dict:
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
# This swing belongs to player robot v3, not the shared robot family. The visual
# effect and hit polygon share `core/slash_envelope.py`; art samples the envelope
# densely while collision uses a coarse convex hull. `SwingDescriptor.reach` is
# the single size control, scaled from the character's collision height.
SWING = slash_envelope.PLAYER_ROBOT_SWING
#  The swing's axis must pass through the ATTACKER, and the attacker is the
# body's CENTRE — not the anchor the rest of this file measures from. `118` is
# this authoring frame's ground line (see `_translated_legacy_hitboxes`), and
# the collision body is 48 world units tall at 0.50625 world units per frame
# pixel, so its centre sits half that above the feet.
BODY_CENTER_Y = 118.0 - (48.0 / 0.50625) / 2


def _slash_poly(ox, oy, dx, dy, swing: slash_envelope.SwingDescriptor):
    """The swept region as a COARSE convex polygon, in frame pixels.

    `(ox, oy)` is where the swing starts and `(dx, dy)` its cardinal direction;
    everything about its SIZE comes from the descriptor, which the effect reads
    too.
    """
    plen = math.hypot(dx, dy) or 1.0
    ux, uy = dx / plen, dy / plen
    px, py = -uy, ux
    return [
        (
            ox + ux * swing.reach * t + px * h * swing.half,
            oy + uy * swing.reach * t + py * h * swing.half,
        )
        for t, h in swing.hull()
    ]


# The thrust: long, thin, parallel-sided. Four vertices is the whole shape.
POKE_REACH = 128 * 1.30
POKE_HALF = 128 * 0.11


def _poke_poly(ox, oy, dx, dy, reach, half):
    plen = math.hypot(dx, dy) or 1.0
    ux, uy = dx / plen, dy / plen
    px, py = -uy, ux

    def at(t, h):
        return (ox + ux * reach * t + px * h, oy + uy * reach * t + py * h)

    return [at(0.0, half), at(0.86, half), at(1.0, 0.0), at(0.86, -half), at(0.0, -half)]


def _player_attack_hitboxes(size: Tuple[int, int]) -> Dict[str, dict]:
    """Return player-v3 attack geometry.

    Slashes use the shared swing envelope except down-tilt, which remains a
    directional thrust. `air_neutral` keeps the family's directionless ring.
    """
    w, h = size
    cx = w // 2
    body_cy = BODY_CENTER_Y - SWING.rise
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

    # Start cardinal swings on the body centerline: runtime derives the effect
    # quad from attacker-to-volume centroid, so cross-axis offsets tilt the art.
    return {
        "attack_side": shaped(
            _slash_poly(cx - w * 0.06, body_cy, 1.0, 0.0, SWING)
        ),
        # The neutral attack — the one every player presses first. It had NO
        # sheet volume, so the runtime fell back to the moveset's 36x28 wu box:
        # a tenth of the forward tilt's area, and the crescent fitted to it
        # shrank with it. The same swing, a shade shorter than the tilt.
        "jab": shaped(
            _slash_poly(cx - w * 0.06, body_cy, 1.0, 0.0, SWING.scaled(reach=0.92))
        ),
        "attack_up": shaped(
            _slash_poly(cx, body_cy, 0.0, -1.0, SWING.scaled(reach=0.88, half=0.92))
        ),
        "air_up": shaped(
            _slash_poly(cx, body_cy, 0.0, -1.0, SWING.scaled(reach=0.84, half=0.88))
        ),
        # This thrust is narrow and centered on the attacker-to-volume axis so
        # runtime quad fitting preserves its reach without tilting the art.
        "attack_down": shaped(_poke_poly(cx, body_cy, 1.0, 0.0,
                                         POKE_REACH, POKE_HALF)),
        "air_down": shaped(
            _slash_poly(cx, body_cy, 0.0, 1.0, SWING.scaled(reach=0.84, half=0.88))
        ),
        "air_forward": shaped(
            _slash_poly(cx - w * 0.02, body_cy, 1.0, 0.0, SWING.scaled(reach=0.94))
        ),
        "air_back": shaped(
            _slash_poly(cx + w * 0.02, body_cy, -1.0, 0.0,
                        SWING.scaled(reach=0.86, half=0.94))
        ),
        # Unbound by any move, and a ring rather than a swing. Left as the
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


# --- Authored gameplay collision box -----------------------------------------
#
# The sheet builder's default body box is the idle frame's ALPHA bbox, and for
# v3 that measured x 79..149, y 57..157 — which is wrong in two ways a player
# feels:
#
#   * the TOP sat at y=57, on a 7..14 px antenna spike. The head proper starts
#     at y≈67, so ~10 px of the collider was empty air above their head;
#   * the WIDTH came from the arms at full span (x 79..148 across y 87..97).
#     The torso and legs are 47..56 px wide, so they collided with walls on
#     outstretched arms.
#
# Stated here instead of measured, the same way Mary-O's forms author theirs.
#  the BASE and the feet anchor are deliberately unchanged (bottom edge 158,
# `feet_pixel` 114.0/157.0): this is a collider change, not a change to where they
# stand, and moving both at once would make the standing shift look like a
# physics regression.
BODY_BOX_TOP_PX = 67       # head crest, antenna excluded
BODY_BOX_BOTTOM_PX = 158   # unchanged — the shoe line the old box already used
BODY_BOX_WIDTH_PX = 57     # torso/legs, not the arm span (was 71)
BODY_BOX_CENTER_X = 114.5  # unchanged centroid of the old box


def body_metrics(fw: int, fh: int):
    """Author the gameplay body in the published padded-frame coordinates."""
    pad_left, pad_top, _pad_right, _pad_bottom = PUBLISH_PADDING
    x = int(round(BODY_BOX_CENTER_X - BODY_BOX_WIDTH_PX / 2.0)) + pad_left
    box = {
        "x": x,
        "y": BODY_BOX_TOP_PX + pad_top,
        "w": BODY_BOX_WIDTH_PX,
        "h": BODY_BOX_BOTTOM_PX - BODY_BOX_TOP_PX,
    }
    # Preserve the authored logical-frame feet point, translated by the same
    # publish padding as the rendered robot. The normalized anchor must then be
    # recomputed against the padded frame dimensions supplied by build_sheet.
    feet_x, feet_y = 114.0 + pad_left, 157.0 + pad_top
    return {
        "body_pixel_bbox": box,
        "feet_pixel": {"x": feet_x, "y": feet_y},
        "feet_anchor_norm": {
            "x": round(feet_x / fw - 0.5, 6),
            "y": round(0.5 - feet_y / fh, 6),
        },
    }


#: Locomotion loops, published as tweened clips (both sides); every other clip
#: steps (decision D3 of `docs/planning/engine/mary-o-part-realization.md`).
TWEENED_ROWS = tuple(
    name
    for row in ("walk", "run", "crouch_walk", "climb", "swim")
    for name in (row, MIRRORED.format(row))
)


def render(out_dir: str | Path, **opts):
    return _render_with_products(out_dir, **opts)[0]


def build_part_flipbook():
    """The part flipbook of every row (``part_flipbook.build_rig_flipbook``)."""
    from ...authoring.part_flipbook import build_rig_flipbook

    size = (FRAME_SIZE[0] + PUBLISH_PADDING[0] + PUBLISH_PADDING[2], FRAME_SIZE[1] + PUBLISH_PADDING[1] + PUBLISH_PADDING[3])
    feet = body_metrics(*size)["feet_pixel"]
    return build_rig_flipbook(TARGET_NAME, ROWS, published_frame, None, (feet["x"], feet["y"]), size, TWEENED_ROWS)


def _render_with_products(out_dir: str | Path, **opts):
    """``(outputs, {"parts": flipbook})``: the published files, and the part
    flipbook they include, for a test to recompose."""
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
        frame_padding=PUBLISH_PADDING,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning={"collision_scale": 1.65},
        body_metrics_fn=body_metrics,
        animation_key_map={name: name for name in ANIMATION_ORDER},
        mirror_of=MIRROR_OF,
        attack_hitboxes=hitboxes,
        # ⛔ still not the MEASURED road. `block`'s alpha union is 128 px wide
        # and `dash`'s 143 against a 57 px torso, so a body that followed the
        # art inflates every time they flourish — which is what `pose_bodies`
        # stays `"authored"` to refuse.
        #
        # What changed is that refusing the measurement used to mean refusing
        # per-pose geometry altogether: every row fell through to the one static
        # rectangle, so a crouched robot's body was its standing body and the
        # only pose the sheet could describe was standing. These rects are
        # solved from the rig's own skeleton with margins calibrated so `idle`
        # reproduces `body_metrics` to the pixel — the same authored box,
        # extended to the poses it was never asked about. Arms and antenna are
        # excluded, which is what keeps `block` at 58 rather than 128.
        hurtbox_parts=hurtbox_parts_for_rows(ROBOT_ROWS),
        pose_bodies="authored",
    )
    keys = (
        "spritesheet", "yaml", "ron", "actor", "canonical",
        "canonical_transparent", "preview",
    )
    paths = [Path(outputs[key]) for key in keys if outputs.get(key)]
    # A canonical-only render (a portrait) publishes no sheet, so no flipbook.
    if rendering_canonical_only():
        return paths, {"outputs": outputs}
    flipbook = build_part_flipbook()
    parts = flipbook.write(out_dir)
    return paths + list(parts.values()), {"parts": flipbook, "outputs": outputs}


def render_canonical(out_dir: str | Path, **opts):
    del opts
    return write_canonical(
        TARGET_NAME,
        ROWS,
        render_frame,
        Path(out_dir),
        frame_size=FRAME_SIZE,
        frame_padding=PUBLISH_PADDING,
    )


__all__ = [
    "ACTOR_METADATA", "ANIMATION_ORDER", "FRAME_SIZE", "ROWS", "TARGET_NAME",
    "build_part_flipbook", "frame_meta", "load_doc", "published_frame", "render",
    "render_canonical", "render_frame",
    "render_portraits",
]


# The robot's portrait viewport in his 224x224 rig canvas. Measured off the idle
# pose; his `head` bone sits at (113, 110), which is the neck, and `frame_meta`
# already carries the same knowledge as its own `head[1] - 14.0` offset.
#
# The view is wider than his face on purpose: the headphone and antenna sit off
# to one side and are half of how he reads. Cropping to the visor alone gave a
# symmetrical white oval that could have been any robot.
_PORTRAIT_FACE = FaceGuide(
    center_x=114.0,
    center_y=84.0,
    width=56.0,
    height=48.0,
    source_width=224.0,
    source_height=224.0,
)
_PORTRAIT_VIEW_WIDTH = 82.0
_PORTRAIT_CENTER_Y = 86.0
_PORTRAIT_RENDER_SCALE = 3


def render_portraits(out_dir: str | Path, **opts):
    """Publish the protagonist's close-ups natively from his paper-doll rig.

    He is the character this whole engine is about and he had no portrait hook,
    so the grid drew him from the canonical fallback -- one frozen frame.
    """
    del opts
    doc = load_doc()

    def frame(animation: str, index: int, count: int) -> Image.Image:
        source = doc.render_at(
            animation,
            doc.frame_time(animation, index, count),
            supersample=4,
            scale=_PORTRAIT_RENDER_SCALE,
        )
        return render_framed_portrait(
            source,
            _PORTRAIT_FACE,
            view_width=_PORTRAIT_VIEW_WIDTH,
            center_y=_PORTRAIT_CENTER_Y,
        )

    def loop(animation: str, count: int, duration_ms: int) -> PortraitClip:
        return PortraitClip.loop(
            tuple(frame(animation, index, count) for index in range(count)),
            duration_ms,
        )

    clips = {
        "default": loop("idle", 8, 148),
        "portrait": PortraitClip.still(frame("idle", 2, 8)),
    }
    return write_portrait_sheet(
        TARGET_NAME, clips, Path(out_dir), still_clip="portrait"
    )
