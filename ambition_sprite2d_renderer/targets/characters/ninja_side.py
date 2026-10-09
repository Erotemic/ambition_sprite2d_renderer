"""Distinct masked ninja / shadow-duelist target.

This target is intentionally semi-independent from the generic toon lane.  It
shares the adapter/YAML/sheet pipeline so the output has the same manifest
format as the rest of the runtime sprites, but the art is drawn by a bespoke
silhouette-first renderer: slate-gray cloth, red eye slits, angular armor
panels, a long katana, and scarf / sash tails that give it a readable outline.

The first-pass animation poses are deliberately conservative.  The canonical
idle frame is the art-review source of truth; the other rows provide enough
movement placeholders to exercise spritesheet + YAML generation until we author
proper action keys.
"""

from __future__ import annotations

import math
import random
from dataclasses import asdict, dataclass
from typing import Dict, Optional, Tuple

from PIL import Image, ImageColor
from ambition_sprite2d_renderer.core.draw import rgba, with_alpha

from ...profiling import profile
from ...authoring.animation_vocab import CORE_CHARACTER_ANIMATION_ORDER, DEFAULT_CORE_TIMINGS, ordered_subset
from ...authoring.rig import add, clamp, vec
from ...authoring import rigdoc, shape_rig
from ...authoring.common_draw import RESAMPLING, draw_capsule
from ...authoring.generator import CharacterGenerator
from ...registry import CharacterJob

Color = Tuple[int, int, int, int]
Point = Tuple[float, float]






def parse_background(value: str) -> Optional[Color]:
    return None if str(value).lower() == "transparent" else rgba(str(value))


def _mix(a: Color, b: Color, t: float) -> Color:
    t = clamp(t, 0.0, 1.0)
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
        int(a[3] + (b[3] - a[3]) * t),
    )


def _place(canvas: Image.Image, part: Tuple[Image.Image, Point], at: Point, degrees: float, name: str, opacity: float = 1.0) -> None:
    """``shape_rig.place`` at an ``opacity`` (a fading frame's pieces)."""
    if opacity <= 0.0:
        return
    image, pivot = part
    rigdoc.blit_rotated(canvas, image, pivot, at, degrees, min(1.0, opacity), part_name=name)


def _capsule(canvas: Image.Image, a: Point, b: Point, radius: float, fill: Color, outline: Color, outline_w: float, name: str, length: float, opacity: float = 1.0) -> None:
    """``shape_rig.capsule`` (a bone of fixed ``length`` from ``a`` toward
    ``b``) at an ``opacity``."""
    span = round(length * 4) / 4
    pad = radius + outline_w + 2
    key = ("capsule", span, round(radius, 3), fill, outline, round(outline_w, 3))
    part = shape_rig.piece(key, (span + 2 * pad, 2 * pad), (pad, pad), lambda draw: draw_capsule(draw, (pad, pad), (pad + span, pad), radius, fill, outline, outline_w))
    _place(canvas, part, a, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])), name, opacity)


def _two_bone(root: Point, target: Point, upper: float, lower: float, hint: Point, soft: float = 0.0) -> Tuple[Point, Point]:
    """Elbow and end of a two-bone chain of fixed lengths reaching toward
    ``target`` from ``root``, bending to the side of ``hint``.

    ``soft`` (pixels) eases the last ``soft`` of the reach: a target that far
    from full extension or farther is reached short, along an exponential
    approach to straight. Without it the bend is infinitely sensitive at full
    reach, and the oni leader's idle arm, whose hand rests a pixel either side
    of it, snapped between straight and bent 9 degrees every other frame
    (2026-10-04)."""
    dx, dy = target[0] - root[0], target[1] - root[1]
    dist = max(1e-6, math.hypot(dx, dy))
    if soft > 0.0 and dist > upper + lower - soft:
        knee = upper + lower - soft
        dist = knee + soft * (1.0 - math.exp(-(dist - knee) / soft))
    reach = clamp(dist, abs(upper - lower) + 1e-3, upper + lower - 1e-3)
    base = math.atan2(dy, dx)
    bend = math.acos(clamp((upper * upper + reach * reach - lower * lower) / (2 * upper * reach), -1.0, 1.0))
    best = None
    for side in (1.0, -1.0):
        elbow = (root[0] + upper * math.cos(base + side * bend), root[1] + upper * math.sin(base + side * bend))
        miss = math.hypot(elbow[0] - hint[0], elbow[1] - hint[1])
        if best is None or miss < best[0]:
            best = (miss, elbow)
    elbow = best[1]
    ex, ey = target[0] - elbow[0], target[1] - elbow[1]
    norm = max(1e-6, math.hypot(ex, ey))
    return elbow, (elbow[0] + ex / norm * lower, elbow[1] + ey / norm * lower)


@dataclass(frozen=True)
class NinjaSpec:
    target: str
    seed: int
    archetype: str
    name: str
    palette_name: str
    blade_style: str
    rank: str
    horn_len: float
    banner_len: float
    pauldron_scale: float
    skirt_len: float
    armor_bulk: float
    crest_scale: float
    sword_len: float
    head_w: float
    head_h: float
    shoulder_w: float
    torso_w: float
    torso_h: float
    hip_w: float
    arm_upper: float
    arm_lower: float
    arm_radius: float
    leg_upper: float
    leg_lower: float
    leg_radius: float
    hand_r: float
    foot_w: float
    foot_h: float
    scarf_len: float
    sash_len: float
    eye_glow: float

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass
class NinjaPose:
    root_x: float = 0.0
    root_y: float = 0.0
    bob: float = 0.0
    lean: float = 0.0
    crouch: float = 0.0
    torso_tilt: float = 0.0
    head_tilt: float = 0.0
    sword_angle: float = -108.0
    sword_shift_x: float = 0.0
    sword_shift_y: float = 0.0
    near_arm_upper: float = 168.0
    near_arm_lower: float = 188.0
    far_arm_upper: float = 220.0
    far_arm_lower: float = 170.0
    near_leg_upper: float = 83.0
    near_leg_lower: float = 75.0
    far_leg_upper: float = 102.0
    far_leg_lower: float = 91.0
    scarf_swing: float = 0.0
    sash_swing: float = 0.0
    eye_squint: float = 0.0
    dash: float = 0.0
    slash: float = 0.0
    hit: float = 0.0
    fade: float = 0.0
    dead: bool = False


class NinjaSideGenerator(CharacterGenerator):
    #: Every frame is painted through rigdoc's seams: the sheet publishes its
    #: part flipbook (``authoring.sheet.publish_generator_flipbook``).
    publishes_part_flipbook = True

    name = "ninja"
    target = "ninja"

    ANIMATIONS: Dict[str, Dict[str, int]] = ordered_subset(
        {
            **DEFAULT_CORE_TIMINGS,
            # A faster slash helps sell this as a duelist even before the full
            # attack breakdown is authored.
            "slash": {"frames": 8, "duration_ms": 68},
            "dash": {"frames": 6, "duration_ms": 58},
        },
        CORE_CHARACTER_ANIMATION_ORDER,
    )

    PALETTES = {
        "moon_steel": {
            "outline": rgba("#11131A"),
            "cloth_dark": rgba("#272B31"),
            "cloth": rgba("#626970"),
            "cloth_mid": rgba("#777F86"),
            "cloth_light": rgba("#B8BEC2"),
            "armor": rgba("#434A52"),
            "armor_dark": rgba("#22262C"),
            "wrap": rgba("#151922"),
            "sash": rgba("#6D425E"),
            "sash_dark": rgba("#3D2638"),
            "eye": rgba("#E51424"),
            "eye_hot": rgba("#FF6B5A"),
            "blade": rgba("#EFF4F6"),
            "blade_shadow": rgba("#A8B0B5"),
            "blade_edge": rgba("#FFFFFF"),
            "brass": rgba("#B18C38"),
            "shadow": rgba("#000000", 54),
            "smoke": rgba("#465061", 58),
        }
    }

    PRESETS = {
        "shadow_duelist": {
            "name": "Shadow Duelist",
            "palette_name": "moon_steel",
            "blade_style": "long_katana",
            "rank": "duelist",
            "horn_len": 0.0,
            "banner_len": 0.0,
            "pauldron_scale": 1.0,
            "skirt_len": 0.0,
            "armor_bulk": 1.0,
            "crest_scale": 1.0,
            "sword_len": 88.0,
            "head_w": 27.0,
            "head_h": 27.5,
            "shoulder_w": 43.0,
            "torso_w": 34.0,
            "torso_h": 35.0,
            "hip_w": 27.0,
            "arm_upper": 18.5,
            "arm_lower": 17.5,
            "arm_radius": 4.7,
            "leg_upper": 25.0,
            "leg_lower": 24.0,
            "leg_radius": 5.2,
            "hand_r": 4.3,
            "foot_w": 16.5,
            "foot_h": 7.4,
            "scarf_len": 30.0,
            "sash_len": 34.0,
            "eye_glow": 1.0,
        },
        "shadow_oni_leader": {
            "name": "Shadow Oni Leader",
            "palette_name": "moon_steel",
            "blade_style": "commander_katana",
            "rank": "leader",
            "horn_len": 18.5,
            "banner_len": 45.0,
            "pauldron_scale": 1.55,
            "skirt_len": 31.0,
            "armor_bulk": 1.22,
            "crest_scale": 1.55,
            "sword_len": 78.0,
            "head_w": 29.0,
            "head_h": 30.0,
            "shoulder_w": 54.0,
            "torso_w": 38.0,
            "torso_h": 38.0,
            "hip_w": 34.0,
            "arm_upper": 19.5,
            "arm_lower": 19.0,
            "arm_radius": 5.4,
            "leg_upper": 25.5,
            "leg_lower": 24.5,
            "leg_radius": 5.7,
            "hand_r": 4.8,
            "foot_w": 17.8,
            "foot_h": 7.8,
            "scarf_len": 39.0,
            "sash_len": 42.0,
            "eye_glow": 1.16,
        },
    }

    def spec_dict(self, spec: NinjaSpec) -> Dict[str, object]:
        return spec.to_dict()

    @profile
    def render_frame(
        self,
        spec: NinjaSpec,
        animation: str,
        frame_index: int,
        size: Tuple[int, int],
        job: CharacterJob,
    ) -> Image.Image:
        anim = self.animations()[animation]
        return self.render_animation_frame(
            spec,
            animation,
            frame_index % anim["frames"],
            anim["frames"],
            size,
            background=parse_background(job.render.background),
            supersample=job.render.supersample,
            downsample=job.render.downsample,
        )

    def build_spec(self, job: CharacterJob) -> NinjaSpec:
        seed, archetype = job.seed, job.archetype
        preset = dict(self.PRESETS.get(archetype, self.PRESETS["shadow_duelist"]))
        rng = random.Random(seed)
        # Tiny deterministic variation only in secondary details.  The main
        # silhouette remains stable for animation authoring.
        preset["eye_glow"] = round(float(preset["eye_glow"]) * rng.uniform(0.92, 1.08), 3)
        preset["scarf_len"] = round(float(preset["scarf_len"]) + rng.uniform(-1.0, 1.2), 3)
        return NinjaSpec(target="ninja", seed=seed, archetype=archetype, **preset)

    def _palette(self, spec: NinjaSpec) -> Dict[str, Color]:
        return dict(self.PALETTES.get(spec.palette_name, self.PALETTES["moon_steel"]))

    def pose_for_animation(self, animation: str, frame_index: int, frame_count: int, _spec: NinjaSpec) -> NinjaPose:
        denom = max(1, frame_count)
        phase = math.sin((frame_index / denom) * math.tau)
        cphase = math.cos((frame_index / denom) * math.tau)
        p = NinjaPose()
        p.bob = phase * 1.0
        p.scarf_swing = phase * 3.5
        p.sash_swing = -phase * 3.2
        p.eye_squint = 0.15 + 0.05 * cphase

        if animation == "walk":
            p.root_x = phase * 1.6
            p.bob = abs(phase) * 1.6
            p.lean = 2.0
            p.near_leg_upper = 68.0 + phase * 18.0
            p.near_leg_lower = 73.0 - phase * 12.0
            p.far_leg_upper = 104.0 - phase * 16.0
            p.far_leg_lower = 91.0 + phase * 10.0
            p.near_arm_upper = 166.0 - phase * 16.0
            p.far_arm_upper = 218.0 + phase * 14.0
            p.scarf_swing = -phase * 5.0
        elif animation == "run":
            p.root_x = phase * 2.4
            p.bob = abs(phase) * 2.0
            p.lean = 5.0
            p.torso_tilt = -5.0
            p.near_leg_upper = 61.0 + phase * 24.0
            p.near_leg_lower = 70.0 - phase * 18.0
            p.far_leg_upper = 112.0 - phase * 20.0
            p.far_leg_lower = 91.0 + phase * 16.0
            p.sword_angle = -104.0 + phase * 2.0
            p.scarf_swing = -7.0 + -phase * 7.0
            p.sash_swing = -phase * 8.0
        elif animation == "jump":
            t = frame_index / max(1, frame_count - 1)
            arc = math.sin(t * math.pi)
            p.root_y = -20.0 * arc
            p.lean = 2.0
            p.crouch = 2.0 * (1.0 - arc)
            p.near_leg_upper = 68.0
            p.near_leg_lower = 48.0
            p.far_leg_upper = 118.0
            p.far_leg_lower = 134.0
            p.sash_swing = 6.0
            p.scarf_swing = -8.0
        elif animation == "fall":
            t = frame_index / max(1, frame_count - 1)
            p.root_y = -16.0 + 10.0 * t
            p.lean = -1.0
            p.sword_angle = -112.0
            p.near_leg_upper = 75.0
            p.near_leg_lower = 86.0
            p.far_leg_upper = 96.0
            p.far_leg_lower = 78.0
            p.scarf_swing = 9.0
        elif animation == "slash":
            t = frame_index / max(1, frame_count - 1)
            wind = max(0.0, 1.0 - t / 0.30)
            strike = max(0.0, min(1.0, (t - 0.18) / 0.42))
            recover = max(0.0, (t - 0.65) / 0.35)
            p.slash = strike
            p.root_x = -4.0 * wind + 8.0 * strike - 3.0 * recover
            p.lean = -6.0 * wind + 9.0 * strike
            p.torso_tilt = -11.0 * wind + 15.0 * strike
            p.sword_angle = -126.0 * wind + 25.0 * strike - 72.0 * recover
            p.sword_shift_x = -4.0 * wind + 5.0 * strike
            p.sword_shift_y = 3.0 * wind - 2.0 * strike
            p.near_arm_upper = 142.0 - 62.0 * strike
            p.near_arm_lower = 202.0 - 104.0 * strike
            p.far_arm_upper = 232.0 - 128.0 * strike
            p.far_arm_lower = 160.0 - 58.0 * strike
            p.scarf_swing = -12.0 * strike
            p.sash_swing = 11.0 * strike
            p.eye_squint = 0.75
        elif animation == "hit":
            t = frame_index / max(1, frame_count - 1)
            p.hit = 1.0 - t
            p.root_x = -5.0 * (1.0 - t)
            p.lean = -8.0 * (1.0 - t)
            p.torso_tilt = -9.0 * (1.0 - t)
            p.eye_squint = 0.8
        elif animation == "death":
            t = frame_index / max(1, frame_count - 1)
            p.dead = t > 0.45
            p.root_x = -8.0 * t
            p.root_y = 12.0 * t
            p.lean = -18.0 * t
            p.torso_tilt = -72.0 * t
            p.head_tilt = -45.0 * t
            p.sword_angle = -42.0 - 45.0 * t
            p.eye_squint = 1.0
            p.scarf_swing = 12.0 * t
            p.sash_swing = 10.0 * t
            p.fade = 0.25 * t
        # ⛔ THE BLINK ROWS ARE PLAIN POSES: no `fade`. The game takes the body
        # apart (the engine's teleport warp), and only for a row that draws the
        # body whole. The smoke of `dash` is an effect and no part of the body.
        elif animation == "blink_out":
            t = frame_index / max(1, frame_count - 1)
            p.dash = t
            p.root_x = 18.0 * t
            p.root_y = -8.0 * math.sin(t * math.pi)
            p.lean = 12.0
            p.scarf_swing = -16.0
        elif animation == "blink_in":
            t = frame_index / max(1, frame_count - 1)
            inv = 1.0 - t
            p.dash = inv
            p.root_x = -18.0 * inv
            p.root_y = -8.0 * math.sin(t * math.pi)
            p.lean = 8.0
            p.scarf_swing = -16.0 * inv
        elif animation == "dash":
            t = frame_index / max(1, frame_count - 1)
            p.dash = 1.0
            p.root_x = 8.0 * math.sin(t * math.pi)
            p.lean = 18.0
            p.torso_tilt = -12.0
            p.sword_angle = -105.0
            p.scarf_swing = -22.0
            p.sash_swing = -14.0
            p.eye_squint = 0.65
        return p

    # -- the ninja as a rig ------------------------------------------------
    #
    # Every rigid piece is painted ONCE in its own frame (``shape_rig.piece``,
    # in the 128-unit design space scaled by ``S``) and turned into place, so a
    # part flipbook stores it once (``authoring/shape_rig.py``). A fading frame
    # places its pieces at the fade's opacity instead of repainting them in
    # faded colours. Cloth tails are painted at rest and turned about their
    # anchor by the swing; limbs are capsule bones of fixed length.

    def _piece(self, key: tuple, S: float, half: Tuple[float, float], paint) -> Tuple[Image.Image, Point]:
        """A piece ``2 * half`` design units across, its pivot at the centre;
        ``paint(d, lp)`` paints with ``lp`` mapping a design offset from the
        pivot to local pixels."""
        hx, hy = half

        def lp(off: Point) -> Point:
            return ((off[0] + hx) * S, (off[1] + hy) * S)

        return shape_rig.piece(("ninja",) + key + (round(S, 4),), (2 * hx * S, 2 * hy * S), (hx * S, hy * S), lambda d: paint(d, lp))

    def _tail_piece(self, rest: Tuple[Point, ...], fill: Color, outline: Color, S: float) -> Tuple[Image.Image, Point]:
        """A scarf / sash tail at rest, its pivot at its anchor ``rest[0]``
        (design offsets from that anchor)."""
        reach = max(max(abs(x), abs(y)) for x, y in rest) + 8.0

        def paint(d, lp) -> None:
            pts = [lp(pt) for pt in rest]
            d.line(pts, fill=outline, width=5, joint="curve")
            d.line(pts, fill=fill, width=3, joint="curve")
            tip = pts[-1]
            d.polygon([tip, (tip[0] - 5.0, tip[1] - 2.0), (tip[0] - 2.5, tip[1] + 4.0)], fill=fill, outline=outline)

        key = ("tail", tuple((round(x, 3), round(y, 3)) for x, y in rest), fill, outline)
        return self._piece(key, S, (reach, reach), paint)

    def _place_tail(self, img: Image.Image, anchor: Point, rest: Tuple[Point, ...], swung: Tuple[Point, ...], fill: Color, outline: Color, S: float, name: str, opacity: float) -> None:
        """The tail painted at ``rest`` turned about ``anchor`` so its tip
        points where the swung tail's tip did."""
        turn = math.degrees(math.atan2(swung[-1][1], swung[-1][0]) - math.atan2(rest[-1][1], rest[-1][0]))
        _place(img, self._tail_piece(rest, fill, outline, S), (anchor[0] * S, anchor[1] * S), turn, name, opacity)

    def _blade_piece(self, length: float, width: float, pal: Dict[str, Color], S: float) -> Tuple[Image.Image, Point]:
        """The blade along +x, its pivot at the hilt (design units)."""
        pad = width + 2.0

        def paint(d, _lp) -> None:
            hx, hy = pad * S, pad * S
            L, W = length * S, width * S
            tip = (hx + L, hy)
            base_l, base_r = (hx, hy + W * 0.55), (hx, hy - W * 0.55)
            mid_l, mid_r = (hx + L * 0.78, hy + W * 0.33), (hx + L * 0.78, hy - W * 0.33)
            d.polygon([base_l, mid_l, tip, mid_r, base_r], fill=pal["outline"])
            inset = max(1.2, W * 0.23)
            d.polygon(
                [(base_l[0], base_l[1] - inset), (mid_l[0], mid_l[1] - inset * 0.6), tip, (mid_r[0], mid_r[1] + inset * 0.15), (base_r[0], base_r[1] + inset * 0.15)],
                fill=pal["blade"],
            )
            d.polygon([base_r, mid_r, tip, (mid_r[0], mid_r[1] + 0.7)], fill=pal["blade_shadow"])
            d.line([base_l, tip], fill=pal["blade_edge"], width=1)

        image, _pivot = shape_rig.piece(("ninja_blade", round(length, 3), round(width, 3), pal["blade"], round(S, 4)), ((length + 2 * pad) * S, 2 * pad * S), (pad * S, pad * S), lambda d: paint(d, None))
        return image, (pad * S, pad * S)

    def _draw_ninja(self, img: Image.Image, spec: NinjaSpec, p: NinjaPose, scale: float) -> None:
        pal = self._palette(spec)
        S = scale
        leader = spec.rank == "leader"
        fade = 1.0 - max(0.0, p.fade)

        def sp(pt: Point) -> Point:
            return (pt[0] * S, pt[1] * S)

        def sc(v: float) -> float:
            return v * S

        def w(v: float, least: int = 1) -> int:
            return max(least, int(sc(v)))

        root = (64.0 + p.root_x, 0.0 + p.root_y)
        hip = (root[0] + p.lean * 0.38, 80.0 + p.root_y - p.bob + p.crouch)
        torso = (root[0] + p.lean, 55.0 + p.root_y - p.bob + p.crouch * 0.45)
        neck = (torso[0] + 0.5, torso[1] - 21.0)
        head = (torso[0] + 1.5, torso[1] - 34.0)
        # The body is one rigid piece on the spine (torso over hip), turned by
        # the lean; the shoulders ride it.
        spine = ((torso[0] + hip[0]) / 2.0, (torso[1] + hip[1]) / 2.0)
        body_turn = math.degrees(math.atan2(torso[0] - hip[0], hip[1] - torso[1]))
        half_spine = 12.5

        def on_body(off: Point) -> Point:
            """A point at ``off`` from the torso, riding the turned body."""
            x, y = off[0], off[1] - half_spine
            c, s = math.cos(math.radians(body_turn)), math.sin(math.radians(body_turn))
            return (spine[0] + x * c - y * s, spine[1] + x * s + y * c)

        # Ground shadow removed; dash smoke crescents are intentional VFX.
        if p.dash > 0.0:
            for i, alpha in enumerate((72, 44, 25)):
                ew, eh = 30.0 + i * 8.0, 7.0
                part = self._piece(
                    ("smoke", i, pal["smoke"]),
                    S,
                    (ew / 2 + 1, eh / 2 + 1),
                    lambda d, lp, ew=ew, eh=eh, alpha=alpha: d.ellipse((*lp((-ew / 2, -eh / 2)), *lp((ew / 2, eh / 2))), fill=with_alpha(pal["smoke"], alpha)),
                )
                _place(img, part, sp((50.0 - i * 12.0, 75.0 + i * 5.0 + p.root_y * 0.3)), 0.0, f"smoke{i}", 1.0 - p.fade * 0.5)

        # Back cloth tails first so the body cuts in front of them.
        scarf_anchor = (head[0] + 11.0, head[1] - 4.0)
        if leader:
            # The leader's ragged command banner, painted at rest and turned
            # about its top by the swing.
            L = spec.banner_len
            top = (scarf_anchor[0] + 7.0, scarf_anchor[1] - 11.0 + p.scarf_swing * 0.10)
            rest = [(0.0, 0.0), (L * 0.62, -7.0), (L, 0.5), (L * 0.78, 8.5), (L * 0.95, 19.0), (L * 0.58, 15.5), (L * 0.48, 27.0), (3.0, 17.0)]
            crest_r = 6.5 * spec.crest_scale

            def paint_banner(d, lp) -> None:
                d.polygon([lp(pt) for pt in rest], fill=pal["cloth_dark"], outline=pal["outline"])
                cx, cy = lp((L * 0.55, 6.5))
                r = sc(crest_r)
                crest = with_alpha(pal["eye"], 86)
                d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=crest, width=w(1.5))
                d.line((cx, cy - r * 0.88, cx, cy + r * 0.88), fill=crest, width=w(1.3))
                d.line((cx - r * 0.58, cy + r * 0.15, cx + r * 0.58, cy - r * 0.18), fill=crest, width=w(1.0))

            reach = L + 4.0
            banner = self._piece(("banner", spec), S, (reach, reach), paint_banner)
            turn = math.degrees(math.atan2(0.22 * p.scarf_swing, 0.8 * L))
            _place(img, banner, sp(top), turn, "banner", fade)
        swing = p.scarf_swing
        self._place_tail(
            img,
            scarf_anchor,
            ((0.0, 0.0), (10.0, -10.0), (spec.scarf_len * 0.55, -3.0), (spec.scarf_len, -7.0)),
            ((0.0, 0.0), (10.0, -10.0 + swing * 0.15), (spec.scarf_len * 0.55, -3.0 + swing), (spec.scarf_len, -7.0 + swing * 1.1)),
            pal["cloth_dark"],
            pal["outline"],
            S,
            "scarf",
            fade,
        )
        anchor2 = (scarf_anchor[0] + 1.0, scarf_anchor[1] + 4.0)
        self._place_tail(
            img,
            anchor2,
            ((0.0, 0.0), (11.0, 4.0), (spec.scarf_len * 0.50 - 1.0, 9.0), (spec.scarf_len * 0.92 - 1.0, 8.0)),
            ((0.0, 0.0), (11.0, 4.0 + swing * 0.10), (spec.scarf_len * 0.50 - 1.0, 9.0 + swing * 0.7), (spec.scarf_len * 0.92 - 1.0, 8.0 + swing * 0.9)),
            pal["sash_dark"],
            pal["outline"],
            S,
            "scarf2",
            fade,
        )

        # Sword / scabbard.  Duelists keep the long read-at-a-distance blade;
        # leaders default to a sheathed command-katana so the silhouette comes
        # from horns, banner, pauldrons, and skirt instead of the same sword pose.
        hilt = (torso[0] - (25.5 if leader else 21.5) + p.sword_shift_x, torso[1] + (30.5 if leader else 28.5) + p.sword_shift_y)
        leader_blade_active = (not leader) or p.slash > 0.08 or p.dash > 0.25
        if leader and not leader_blade_active:

            def paint_sheath(d, lp) -> None:
                a, b = lp((16.0, -6.5)), lp((28.0, 30.0))
                d.line([a, b], fill=pal["outline"], width=w(6.5))
                d.line([a, b], fill=pal["armor_dark"], width=w(4.0))
                d.line([lp((14.2, -4.5)), lp((19.0, -8.0))], fill=pal["brass"], width=w(2.0))

            _place(img, self._piece(("sheath",), S, (34.0, 34.0), paint_sheath), sp(hip), 0.0, "sheath", fade)
        else:
            _place(img, self._blade_piece(spec.sword_len, 8.4 * spec.armor_bulk, pal, S), sp(hilt), p.sword_angle, "blade", fade)
        if p.slash > 0.08:

            def paint_slash(d, lp) -> None:
                for off, alpha in ((0, 52), (7, 32), (14, 18)):
                    d.arc((*lp((29.0 + off - 70.0, 18.0 - 57.0)), *lp((111.0 + off - 70.0, 96.0 - 57.0))), 208, 332, fill=with_alpha(pal["blade_edge"], alpha), width=w(3.2))

            _place(img, self._piece(("slash", pal["blade_edge"]), S, (60.0, 44.0), paint_slash), sp((70.0 + p.root_x, 57.0 + p.root_y)), 0.0, "slash_arc", p.slash)

        # Legs: capsule bones of fixed length.
        def limb(a: Point, b: Point, c: Point, upper: float, lower: float, radius: float, fill: Color, name: str) -> None:
            _capsule(img, sp(a), sp(b), sc(radius), fill, pal["outline"], sc(1.25), f"{name}_upper", sc(upper), fade)
            _capsule(img, sp(b), sp(c), sc(radius * 0.95), fill, pal["outline"], sc(1.25), f"{name}_lower", sc(lower), fade)

        def leg_points(is_near: bool) -> Tuple[Point, Point, Point]:
            sign = 1.0 if is_near else -1.0
            upper = p.near_leg_upper if is_near else p.far_leg_upper
            lower = p.near_leg_lower if is_near else p.far_leg_lower
            start = (hip[0] + sign * spec.hip_w * 0.28, hip[1] + 1.0)
            knee = add(start, vec(spec.leg_upper, upper + p.torso_tilt * 0.07))
            ankle = add(knee, vec(spec.leg_lower, lower + p.torso_tilt * 0.05))
            return start, knee, ankle

        far_hip, far_knee, far_ankle = leg_points(False)
        near_hip, near_knee, near_ankle = leg_points(True)
        limb(far_hip, far_knee, far_ankle, spec.leg_upper, spec.leg_lower, spec.leg_radius, pal["cloth_dark"], "far_leg")
        limb(near_hip, near_knee, near_ankle, spec.leg_upper, spec.leg_lower, spec.leg_radius, pal["cloth"], "near_leg")
        for ankle, sign, fill, name in ((far_ankle, -1.0, pal["wrap"], "far_foot"), (near_ankle, 1.0, pal["armor_dark"], "near_foot")):
            fw, fh = spec.foot_w, spec.foot_h

            def paint_foot(d, lp, fill=fill, fw=fw, fh=fh) -> None:
                d.ellipse((*lp((-fw / 2, -fh / 2)), *lp((fw / 2, fh / 2))), fill=pal["outline"])
                o = 1.1
                d.ellipse((*lp((-fw / 2 + o, -fh / 2 + o)), *lp((fw / 2 - o, fh / 2 - o))), fill=fill)

            part = self._piece(("foot", round(fw, 3), round(fh, 3), fill), S, (fw / 2 + 1, fh / 2 + 1), paint_foot)
            _place(img, part, sp((ankle[0] + sign * 4.3, ankle[1] + 2.5)), -7.0 * sign, name, fade)

        # Torso: one piece on the spine (offsets from the torso, ``ty``; from
        # the hip, ``hy``), turned by the lean.
        ty, hy = -half_spine, half_spine
        hw, shw = spec.hip_w / 2.0, spec.shoulder_w / 2.0

        def paint_body(d, lp) -> None:
            def T(x: float, y: float) -> Point:
                return lp((x, y + ty))

            def H(x: float, y: float) -> Point:
                return lp((x, y + hy))

            d.polygon([T(-shw, -13.0), T(shw, -11.0), H(hw, -5.0), H(-hw, -4.0)], fill=pal["outline"])
            d.polygon([T(-shw + 3.0, -10.5), T(shw - 3.0, -9.0), H(hw - 3.0, -7.0), H(-hw + 3.0, -6.0)], fill=pal["cloth"])
            # Chest armor: angular panels instead of generic shirt shapes.
            d.polygon([T(-15.0, -9.0), T(-1.0, -12.0), T(-3.0, 5.0), T(-14.0, 8.0)], fill=pal["armor"])
            d.polygon([T(1.0, -11.0), T(15.0, -8.0), T(13.0, 7.0), T(2.0, 4.0)], fill=pal["armor_dark"])
            d.line([T(-11.0, -11.0), T(-2.0, -13.0)], fill=pal["cloth_light"], width=w(1.2))
            d.line([T(4.0, -11.0), T(15.0, -8.0)], fill=with_alpha(pal["cloth_light"], 150), width=w(1.0))
            # Little cyan-gray moon glyph for recognizability at review scale.
            d.arc((*T(-4.5, -2.0), *T(5.5, 8.0)), 70, 275, fill=with_alpha(pal["blade_shadow"], 180), width=w(1.2))
            if leader:
                # Lamellar commander plates: broad, square, and red-riveted.
                for yoff in (-4.0, 2.5, 8.5):
                    d.line([T(-15.5, yoff), T(15.0, yoff + 1.0)], fill=with_alpha(pal["outline"], 190), width=w(0.9))
                for xoff in (-9.0, 0.0, 9.0):
                    d.line([T(xoff, -9.0), T(xoff * 0.75, 12.0)], fill=with_alpha(pal["outline"], 155), width=w(0.8))
                for xoff in (-12.5, -4.0, 5.0, 13.0):
                    d.ellipse((*T(xoff - 1.0, 2.0), *T(xoff + 1.0, 4.0)), fill=with_alpha(pal["eye"], 120))

        body = self._piece(("body", spec), S, (shw + 6.0, half_spine + 26.0), paint_body)
        _place(img, body, sp(spine), body_turn, "body", fade)

        # Belt / sash (and the leader's skirt panels): one piece riding the hip.
        def paint_hip(d, lp) -> None:
            if leader:
                skirt = spec.skirt_len
                panels = [
                    [(-20.0, -2.0), (-7.0, 0.5), (-10.5, skirt - 4.0), (-25.0, skirt + 1.5)],
                    [(-8.5, -1.0), (8.5, -1.0), (5.5, skirt + 4.0), (-2.0, skirt + 8.0), (-10.0, skirt + 2.0)],
                    [(7.0, 0.0), (22.0, -2.0), (27.0, skirt + 1.0), (11.0, skirt - 3.0)],
                ]
                for idx, pts in enumerate(panels):
                    d.polygon([lp(pt) for pt in pts], fill=pal["outline"])
                    d.polygon([lp((x * 0.92, y * 0.96)) for x, y in pts], fill=pal["cloth_dark" if idx != 1 else "wrap"])
                cx, cy = lp((-1.5, 19.0))
                r = sc(4.6 * spec.crest_scale)
                crest = with_alpha(pal["eye"], 132)
                d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=crest, width=w(1.2))
                d.line((cx, cy - r * 0.85, cx, cy + r * 0.85), fill=crest, width=w(1.0))
            # The sash band, turned -2 degrees (counter-clockwise) about its centre.
            bw, bh = 33.0 * spec.armor_bulk, 8.0
            cx, cy = 0.5, -3.0
            t = math.radians(2.0)

            def rot(x: float, y: float) -> Point:
                return lp((cx + x * math.cos(t) - y * math.sin(t), cy + x * math.sin(t) + y * math.cos(t)))

            d.polygon([rot(-bw / 2 - 0.6, -bh / 2 - 0.6), rot(bw / 2 + 0.6, -bh / 2 - 0.6), rot(bw / 2 + 0.6, bh / 2 + 0.6), rot(-bw / 2 - 0.6, bh / 2 + 0.6)], fill=pal["outline"])
            d.polygon([rot(-bw / 2 + 0.6, -bh / 2 + 0.6), rot(bw / 2 - 0.6, -bh / 2 + 0.6), rot(bw / 2 - 0.6, bh / 2 - 0.6), rot(-bw / 2 + 0.6, bh / 2 - 0.6)], fill=pal["sash"])
            d.rectangle((*lp((-4.0, -7.0)), *lp((5.0, -1.0))), fill=pal["brass"])

        hip_part = self._piece(("hip", spec), S, (32.0, spec.skirt_len + 14.0), paint_hip)
        _place(img, hip_part, sp(hip), 0.0, "sash_belt", fade)
        sash_len = spec.sash_len
        self._place_tail(
            img,
            (hip[0] + 14.0, hip[1] - 5.0),
            ((0.0, 0.0), (10.0, -3.0), (sash_len * 0.72 - 14.0, 4.0), (sash_len - 14.0, 2.0)),
            ((0.0, 0.0), (10.0, -3.0 + p.sash_swing * 0.3), (sash_len * 0.72 - 14.0, 4.0 + p.sash_swing * 0.7), (sash_len - 14.0, 2.0 + p.sash_swing)),
            pal["sash"],
            pal["outline"],
            S,
            "sash_tail",
            fade,
        )

        # Arms and hands; far arm first. The hands are pulled toward the hilt
        # and the arm reaches them by two-bone IK of fixed lengths.
        def arm_points(is_near: bool) -> Tuple[Point, Point, Point, float]:
            if is_near:
                shoulder = on_body((spec.shoulder_w * (0.39 if leader else 0.34), -10.0))
                if leader and p.slash <= 0.08:
                    upper = 74.0 + p.torso_tilt * 0.06
                    lower = 92.0 + p.torso_tilt * 0.05
                else:
                    upper = p.near_arm_upper + p.torso_tilt * 0.10
                    lower = p.near_arm_lower + p.torso_tilt * 0.08
            else:
                shoulder = on_body((-spec.shoulder_w * (0.39 if leader else 0.34), -10.5))
                if leader and p.slash <= 0.08:
                    upper = 106.0 + p.torso_tilt * 0.06
                    lower = 84.0 + p.torso_tilt * 0.05
                else:
                    upper = p.far_arm_upper + p.torso_tilt * 0.08
                    lower = p.far_arm_lower + p.torso_tilt * 0.08
            elbow = add(shoulder, vec(spec.arm_upper, upper))
            hand = add(elbow, vec(spec.arm_lower, lower))
            if leader and p.slash <= 0.08:
                # A commanding idle: one hand rests near the sword, the other
                # drops naturally.
                if not is_near:
                    hand = _mix((hand[0], hand[1], 0, 255), (hilt[0] - 0.5, hilt[1] + 0.5, 0, 255), 0.24)
            else:
                # Pull both hands toward the sword hilt in the duelist / slash poses.
                hand = _mix((hand[0], hand[1], 0, 255), (hilt[0] + (2.5 if is_near else -2.0), hilt[1] + (2.5 if is_near else -2.5), 0, 255), 0.52)
            # The old painter stretched the forearm to the pulled hand; a held
            # pose keeps that reach as the bone's (fixed) length.
            forearm = spec.arm_lower if leader and p.slash <= 0.08 else spec.arm_lower * (1.4 if is_near else 1.55)
            elbow, hand = _two_bone(shoulder, (hand[0], hand[1]), spec.arm_upper, forearm, elbow, soft=0.1 * (spec.arm_upper + forearm))
            return shoulder, elbow, hand, forearm

        far_sh, far_el, far_hand, far_fore = arm_points(False)
        near_sh, near_el, near_hand, near_fore = arm_points(True)
        limb(far_sh, far_el, far_hand, spec.arm_upper, far_fore, spec.arm_radius, pal["cloth_dark"], "far_arm")
        limb(near_sh, near_el, near_hand, spec.arm_upper, near_fore, spec.arm_radius, pal["cloth_mid"], "near_arm")
        if leader:
            # Hard pauldrons over the arm capsules, riding the turned body.
            def paint_pauldrons(d, lp) -> None:
                for sign in (-1.0, 1.0):
                    sx = sign * spec.shoulder_w * 0.45
                    sy = -11.5 + ty
                    outer = sx + sign * 13.5 * spec.pauldron_scale
                    pts = [(sx - sign * 3.0, sy - 5.5), (outer, sy - 2.0), (outer - sign * 3.5, sy + 13.5), (sx - sign * 8.0, sy + 11.0)]
                    d.polygon([lp(pt) for pt in pts], fill=pal["outline"])
                    d.polygon([lp((x * 0.88 + sx * 0.12, y * 0.90 + sy * 0.10)) for x, y in pts], fill=pal["armor_dark"])
                    spike = [(sx + sign * 1.0, sy - 5.0), (outer + sign * 2.0, sy - 8.5), (sx + sign * 5.0, sy + 0.5)]
                    d.polygon([lp(pt) for pt in spike], fill=pal["outline"])
                    d.line([lp((sx - sign * 1.0, sy + 2.0)), lp((outer - sign * 4.0, sy + 3.0))], fill=with_alpha(pal["cloth_light"], 120), width=w(0.9))

            reach = spec.shoulder_w * 0.45 + 13.5 * spec.pauldron_scale + 6.0
            pauldrons = self._piece(("pauldrons", spec), S, (reach, reach), paint_pauldrons)
            _place(img, pauldrons, sp(spine), body_turn, "pauldrons", fade)
        # Hand wraps / guards.
        hr = spec.hand_r

        def paint_hand(d, lp) -> None:
            d.ellipse((*lp((-hr, -hr)), *lp((hr, hr))), fill=pal["wrap"], outline=pal["outline"], width=w(1.0))

        hand_part = self._piece(("hand", round(hr, 3)), S, (hr + 1.0, hr + 1.0), paint_hand)
        _place(img, hand_part, sp(far_hand), 0.0, "far_hand", fade)
        _place(img, hand_part, sp(near_hand), 0.0, "near_hand", fade)

        # Hilt drawn after hands so the grip reads as held: the guard across
        # the blade, painted with the blade along +x and turned with it.
        def paint_hilt(d, lp) -> None:
            h0, h1 = lp((0.0, -9.0)), lp((0.0, 9.0))
            d.line([h0, h1], fill=pal["outline"], width=w(5.0))
            d.line([h0, h1], fill=pal["brass"], width=w(2.7))
            d.rounded_rectangle((*lp((-2.0, -7.0)), *lp((2.0, 7.0))), radius=sc(2.0), fill=pal["armor_dark"], outline=pal["outline"], width=w(1.0))

        _place(img, self._piece(("hilt",), S, (12.0, 12.0), paint_hilt), sp(hilt), p.sword_angle, "hilt", fade)

        # Neck.
        def paint_neck(d, lp) -> None:
            d.rounded_rectangle((*lp((-4.5, -6.5)), *lp((4.5, 6.5))), radius=sc(3.0), fill=pal["cloth_dark"], outline=pal["outline"], width=w(1.0))

        _place(img, self._piece(("neck",), S, (7.0, 9.0), paint_neck), sp(neck), -p.head_tilt, "neck", fade)

        # Horns and head: one piece per eye height, turned by the head tilt.
        eye_h = round(max(1.5, 3.3 - p.eye_squint * 1.4) * 4.0) / 4.0

        def paint_head(d, lp) -> None:
            if spec.horn_len > 0.0:
                for sign in (-1.0, 1.0):
                    # Wide, curved oni horns outside the helmet ellipse.
                    base = (sign * 7.0, -12.0)
                    mid = (sign * (12.5 + spec.horn_len * 0.20), -19.0)
                    tip_pt = (sign * (16.0 + spec.horn_len * 0.20), -20.0 - spec.horn_len * 0.45)
                    path = [lp(base), lp(mid), lp(tip_pt)]
                    d.line(path, fill=pal["outline"], width=w(5.4, 3), joint="curve")
                    d.line(path, fill=pal["sash_dark"], width=w(3.1, 2), joint="curve")
                    d.polygon([lp(tip_pt), lp((tip_pt[0] - sign * 2.8, tip_pt[1] + 5.0)), lp((tip_pt[0] - sign * 0.2, tip_pt[1] + 1.0))], fill=pal["outline"])
                    d.line([lp(base), lp(tip_pt)], fill=with_alpha(pal["eye_hot"], 92), width=w(0.9))
            hw2, hh2 = (spec.head_w + 2.5) / 2.0, (spec.head_h + 1.5) / 2.0
            d.ellipse((*lp((-hw2, -hh2)), *lp((hw2, hh2))), fill=pal["outline"])
            d.ellipse((*lp((-0.7 - spec.head_w / 2, -0.5 - spec.head_h / 2)), *lp((-0.7 + spec.head_w / 2, -0.5 + spec.head_h / 2))), fill=pal["cloth"])
            # Hood top cap / brow wrap.
            cw = spec.head_w * 0.90 / 2.0
            d.rounded_rectangle((*lp((-0.8 - cw, -13.0)), *lp((-0.8 + cw, -5.0))), radius=sc(4.0), fill=pal["cloth_mid"])
            bw = spec.head_w * 0.92 / 2.0
            d.rounded_rectangle((*lp((-0.3 - bw, -1.5 - 3.65)), *lp((-0.3 + bw, -1.5 + 3.65))), radius=sc(3.0), fill=pal["wrap"], outline=pal["outline"], width=w(0.9))
            # Face-mask lower half with a cheek highlight and nose plane.
            d.arc((*lp((-11.0, 1.0)), *lp((12.0, 15.0))), 10, 165, fill=pal["outline"], width=w(1.0))
            d.line([lp((5.5, -10.5)), lp((11.0, -6.0))], fill=with_alpha(pal["cloth_light"], 145), width=w(1.0))
            d.line([lp((-5.0, 9.0)), lp((2.0, 11.0))], fill=pal["armor_dark"], width=w(1.2))
            if leader:
                tusk = with_alpha(pal["blade_shadow"], 210)
                d.polygon([lp((-8.5, 5.0)), lp((-5.0, 7.8)), lp((-7.2, 12.0))], fill=tusk, outline=pal["outline"])
                d.polygon([lp((8.5, 4.6)), lp((5.0, 7.5)), lp((7.4, 11.6))], fill=tusk, outline=pal["outline"])
            # Red eye slits: sharp triangular slashes.
            eye_alpha = min(255, int(230 * spec.eye_glow))
            left_eye = [lp((-8.3, -3.5)), lp((-1.7, -2.6)), lp((-3.4, -2.6 + eye_h))]
            right_eye = [lp((2.0, -2.9)), lp((9.2, -4.4)), lp((6.2, -1.1 + eye_h))]
            d.polygon(left_eye, fill=with_alpha(pal["eye"], eye_alpha))
            d.polygon(right_eye, fill=with_alpha(pal["eye"], eye_alpha))
            hot = with_alpha(pal["eye_hot"], min(255, eye_alpha + 35))
            d.line([left_eye[0], left_eye[1]], fill=hot, width=w(0.8))
            d.line([right_eye[0], right_eye[1]], fill=hot, width=w(0.8))

        reach = 22.0 + spec.horn_len * 0.7
        head_part = self._piece(("head", spec, eye_h), S, (reach, reach), paint_head)
        _place(img, head_part, sp(head), -p.head_tilt, "head", fade)

        if p.hit > 0:
            # Brief red rim on hit frames.
            def paint_rim(d, lp) -> None:
                d.arc((*lp((-36.5, -48.0)), *lp((36.5, 48.0))), 205, 305, fill=with_alpha(pal["eye"], 110), width=w(2.0))

            _place(img, self._piece(("rim", pal["eye"]), S, (38.0, 50.0), paint_rim), sp((64.5, 70.0)), 0.0, "hit_rim", p.hit)

    @profile
    def render_animation_frame(
        self,
        spec: NinjaSpec,
        animation: str,
        frame_index: int,
        frame_count: int,
        size: Tuple[int, int] = (128, 128),
        *,
        background: Optional[Color] = None,
        supersample: int = 4,
        downsample: str = "lanczos",
    ) -> Image.Image:
        w, h = size
        ss = max(1, int(supersample))
        high = Image.new("RGBA", (w * ss, h * ss), background or (0, 0, 0, 0))
        scale = (w / 128.0) * ss
        pose = self.pose_for_animation(animation, frame_index, frame_count, spec)
        self._draw_ninja(high, spec, pose, scale)
        resample = RESAMPLING.NEAREST if downsample == "nearest" else RESAMPLING.LANCZOS
        return rigdoc.downsampled_canvas(high, size, resample)
