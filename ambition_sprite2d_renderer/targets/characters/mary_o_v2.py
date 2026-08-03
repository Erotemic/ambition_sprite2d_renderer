"""Mary-O v2 target registration and animation orchestration.

The visual output is intentionally parity-locked to the accepted pre-refactor
implementation. Authored data lives in :mod:`._mary_o_v2_model`; procedural
parts and composition live in :mod:`._mary_o_v2_art`.
"""

from __future__ import annotations

import copy
import math
from pathlib import Path
from typing import Dict, List

from PIL import Image

from ...authoring.sheet_build import build_sheet
from ..super_mary_o_common import bottom_center_canvas, rasterize_logical
from ._mary_o_v2_art import (
    _draw_dead_front,
    _draw_fire_orb,
    _draw_power_loss_sparkles,
    _draw_side_pose,
    _draw_transform_aura,
)
from ._mary_o_v2_model import (
    ACTOR_METADATA_BASE,
    AUTHORING_FRAME_SIZE,
    FIRE_FORM,
    FRAME_SIZE,
    LABEL_WIDTH,
    LOGICAL_SIZE,
    MARY_FIRE,
    MARY_FIRE_BLAST,
    MARY_FIRE_FLASH,
    MARY_NORMAL,
    OUTPUT_RESOLUTION_SCALE,
    SCALE,
    SHORT_FORM,
    SHORT_POSES,
    TALL_FORM,
    TALL_LIKE_POSES,
    FormSpec,
    Pose,
    form_collision_box,
    _form_with_palette,
    _mix_outfit_palette,
    _transition_form,
)

def _poses_for(form: FormSpec) -> Dict[str, List[Pose]]:
    if form.tall:
        return TALL_LIKE_POSES
    return SHORT_POSES


def _publish_frame(sprite: Image.Image) -> Image.Image:
    """Publish the authored frame at exactly 2x native resolution."""
    authored = bottom_center_canvas(sprite, AUTHORING_FRAME_SIZE)
    return authored.resize(FRAME_SIZE, resample=Image.Resampling.NEAREST)


def _draw_form(form: FormSpec, animation: str, frame_idx: int, nframes: int) -> Image.Image:
    if animation == "grow":
        # Hosted by the TALL sheet (the form arrived at). Named explicitly
        # rather than taken from `form` so the clip keeps meaning "small becomes
        # tall" wherever it is hosted, and ends on the form it arrives at.
        alt_form = SHORT_FORM if frame_idx % 2 == 0 else TALL_FORM
        return _draw_form(alt_form, "idle", 0, 1)

    if animation == "transform":
        fire_flash_1 = _mix_outfit_palette(MARY_NORMAL, MARY_FIRE_FLASH, 0.45)
        fire_flash_2 = _mix_outfit_palette(MARY_NORMAL, MARY_FIRE_FLASH, 0.88)
        fire_flash_3 = _mix_outfit_palette(MARY_FIRE_FLASH, MARY_FIRE_BLAST, 0.42)
        fire_flash_4 = _mix_outfit_palette(MARY_FIRE_FLASH, MARY_FIRE_BLAST, 0.82)
        fire_blast = MARY_FIRE_BLAST
        fire_reveal_1 = _mix_outfit_palette(MARY_FIRE_BLAST, MARY_FIRE, 0.18)
        fire_reveal_2 = _mix_outfit_palette(MARY_FIRE_BLAST, MARY_FIRE, 0.42)
        fire_reveal_3 = _mix_outfit_palette(MARY_FIRE_BLAST, MARY_FIRE, 0.72)
        transform_seq = [
            (_transition_form(TALL_FORM, MARY_NORMAL, stage=1.00), Pose(), 0.00, 0.00, 0, False),
            (_transition_form(TALL_FORM, MARY_NORMAL, stage=1.00), Pose(bob=-0.35, arm_front_angle=118, arm_back_angle=42, leg_front_angle=8, leg_back_angle=-8), 0.10, 0.00, 1, False),
            (_transition_form(FIRE_FORM, fire_flash_1, stage=1.16, power="tall"), Pose(bob=-0.75, body_lean=0.04, arm_front_angle=96, arm_back_angle=30, leg_front_angle=12, leg_back_angle=-9), 0.40, 0.18, 2, False),
            (_transition_form(FIRE_FORM, fire_flash_2, stage=1.36, power="tall"), Pose(bob=-1.0, body_lean=0.08, arm_front_angle=90, arm_back_angle=20, leg_front_angle=15, leg_back_angle=-11), 0.88, 0.56, 3, False),
            (_transition_form(FIRE_FORM, fire_flash_3, stage=1.62, power="fire"), Pose(bob=-1.18, body_lean=0.11, arm_front_angle=98, arm_back_angle=18, leg_front_angle=17, leg_back_angle=-12), 1.22, 0.92, 3, False),
            (_transition_form(FIRE_FORM, fire_flash_4, stage=1.86, power="fire"), Pose(bob=-1.32, body_lean=0.13, arm_front_angle=106, arm_back_angle=20, leg_front_angle=18, leg_back_angle=-13), 1.48, 1.18, 3, False),
            (_transition_form(FIRE_FORM, fire_blast, stage=2.00, power="fire"), Pose(bob=-1.40, body_lean=0.14, arm_front_angle=112, arm_back_angle=22, leg_front_angle=20, leg_back_angle=-15), 1.62, 1.34, 3, False),
            (_transition_form(FIRE_FORM, fire_reveal_1, stage=1.94, power="fire"), Pose(bob=-1.08, body_lean=0.14, arm_front_angle=108, arm_back_angle=18, leg_front_angle=18, leg_back_angle=-12), 1.38, 1.18, 3, False),
            (_transition_form(FIRE_FORM, fire_reveal_2, stage=1.98, power="fire"), Pose(bob=-0.72, body_lean=0.12, arm_front_angle=86, arm_back_angle=6, leg_front_angle=12, leg_back_angle=-8), 1.08, 1.02, 3, False),
            (_transition_form(FIRE_FORM, fire_reveal_3, stage=2.00, power="fire"), Pose(bob=-0.45, body_lean=0.10, arm_front_angle=70, arm_back_angle=-4, leg_front_angle=10, leg_back_angle=-6), 0.94, 0.96, 3, True),
            (FIRE_FORM, TALL_LIKE_POSES["fireball"][0], 0.90, 1.0, 3, True),
        ]
        active_form, pose, wing_boost, sleeve_wing_boost, extra_star_phase, show_orb = transform_seq[frame_idx % len(transform_seq)]

        def painter(px) -> None:
            _draw_transform_aura(px, frame_idx)
            _draw_side_pose(
                px,
                active_form,
                pose,
                animation="transform",
                wing_boost=wing_boost,
                sleeve_wing_boost=sleeve_wing_boost,
                extra_star_phase=extra_star_phase,
            )
            if show_orb:
                _draw_fire_orb(px, 19.4, 13.2 + 0.3 * math.sin(frame_idx))

        sprite = rasterize_logical(LOGICAL_SIZE, SCALE, painter)
        return _publish_frame(sprite)

    if animation == "shrink":
        # Two hosts, two clips: the TALL sheet's shrink is "fire became tall"
        # and the SHORT sheet's is "tall became small". Both end on the sheet's
        # own form, which is what makes the arriving-sheet rule hold.
        if form.power == "tall":
            fire_dull_1 = _mix_outfit_palette(MARY_FIRE, MARY_NORMAL, 0.22)
            fire_dull_2 = _mix_outfit_palette(MARY_FIRE, MARY_NORMAL, 0.46)
            fire_dull_3 = _mix_outfit_palette(MARY_FIRE, MARY_NORMAL, 0.72)
            hurt_seq = [
                (FIRE_FORM, Pose(mode="fireball", bob=0.1, arm_front_angle=35, arm_back_angle=-18, leg_front_angle=-12, leg_back_angle=22), 0.85, 0.95, 2),
                (_transition_form(FIRE_FORM, fire_dull_1, stage=1.82, power="fire"), Pose(bob=0.35, body_lean=-0.1, arm_front_angle=24, arm_back_angle=-36, leg_front_angle=-8, leg_back_angle=18), 0.55, 0.70, 1),
                (_transition_form(FIRE_FORM, fire_dull_2, stage=1.56, power="fire"), Pose(bob=0.7, body_lean=-0.18, arm_front_angle=10, arm_back_angle=-58, leg_front_angle=5, leg_back_angle=10), 0.20, 0.35, 1),
                (_transition_form(FIRE_FORM, fire_dull_3, stage=1.28, power="tall"), Pose(bob=1.0, body_lean=-0.08, arm_front_angle=88, arm_back_angle=-80, leg_front_angle=14, leg_back_angle=4), 0.0, 0.08, 0),
                (_transition_form(TALL_FORM, _mix_outfit_palette(MARY_NORMAL, MARY_FIRE, 0.18), stage=1.06), Pose(bob=0.75, body_lean=0.02, arm_front_angle=118, arm_back_angle=-48, leg_front_angle=10, leg_back_angle=-2), 0.0, 0.0, 0),
                (TALL_FORM, Pose(bob=0.3, body_lean=0.0, arm_front_angle=52, arm_back_angle=-12, leg_front_angle=0, leg_back_angle=0), 0.0, 0.0, 0),
            ]
            active_form, pose, wing_boost, sleeve_wing_boost, extra_star_phase = hurt_seq[frame_idx % len(hurt_seq)]

            def painter(px) -> None:
                _draw_power_loss_sparkles(px, frame_idx, fire=True)
                _draw_side_pose(
                    px,
                    active_form,
                    pose,
                    animation="shrink",
                    wing_boost=wing_boost,
                    sleeve_wing_boost=sleeve_wing_boost,
                    extra_star_phase=extra_star_phase,
                )

            sprite = rasterize_logical(LOGICAL_SIZE, SCALE, painter)
            return _publish_frame(sprite)
        else:
            tall_dull = _mix_outfit_palette(MARY_NORMAL, MARY_FIRE_FLASH, 0.06)
            hurt_seq = [
                (TALL_FORM, Pose(bob=0.2, body_lean=-0.06, arm_front_angle=24, arm_back_angle=-18, leg_front_angle=-10, leg_back_angle=18), 1),
                (SHORT_FORM, Pose(bob=0.55, body_lean=-0.02, arm_front_angle=40, arm_back_angle=-18, leg_front_angle=-4, leg_back_angle=10), 0),
                (_form_with_palette(TALL_FORM, tall_dull), Pose(bob=0.85, body_lean=-0.10, arm_front_angle=88, arm_back_angle=-54, leg_front_angle=8, leg_back_angle=6), 0),
                (SHORT_FORM, Pose(bob=0.35, body_lean=0.0, arm_front_angle=46, arm_back_angle=-10, leg_front_angle=0, leg_back_angle=0), 0),
            ]
            active_form, pose, extra_star_phase = hurt_seq[frame_idx % len(hurt_seq)]

            def painter(px) -> None:
                _draw_power_loss_sparkles(px, frame_idx, fire=False)
                _draw_side_pose(px, active_form, pose, animation="shrink", extra_star_phase=extra_star_phase)

            sprite = rasterize_logical(LOGICAL_SIZE, SCALE, painter)
            return _publish_frame(sprite)

    if animation == "big_shrink":
        # Hosted by the SHORT sheet: fire loses two tiers at once and arrives
        # small. No power guard — the sheet that owns the clip is the one it
        # ends on, and only the short sheet lists this row.
        fire_dull_1 = _mix_outfit_palette(MARY_FIRE, MARY_NORMAL, 0.24)
        fire_dull_2 = _mix_outfit_palette(MARY_FIRE, MARY_NORMAL, 0.50)
        fire_dull_3 = _mix_outfit_palette(MARY_FIRE, MARY_NORMAL, 0.78)
        big_shrink_seq = [
            (FIRE_FORM, Pose(mode="fireball", bob=0.1, arm_front_angle=35, arm_back_angle=-18, leg_front_angle=-12, leg_back_angle=22), 0.95, 1.05, 2),
            (_transition_form(FIRE_FORM, fire_dull_1, stage=1.82, power="fire"), Pose(bob=0.35, body_lean=-0.1, arm_front_angle=24, arm_back_angle=-36, leg_front_angle=-8, leg_back_angle=18), 0.60, 0.72, 1),
            (_transition_form(FIRE_FORM, fire_dull_2, stage=1.48, power="fire"), Pose(bob=0.7, body_lean=-0.16, arm_front_angle=12, arm_back_angle=-58, leg_front_angle=4, leg_back_angle=12), 0.18, 0.32, 0),
            (_transition_form(FIRE_FORM, fire_dull_3, stage=1.16, power="tall"), Pose(bob=0.95, body_lean=-0.08, arm_front_angle=84, arm_back_angle=-76, leg_front_angle=12, leg_back_angle=4), 0.0, 0.0, 0),
            (TALL_FORM, Pose(bob=0.55, body_lean=-0.02, arm_front_angle=58, arm_back_angle=-22, leg_front_angle=-2, leg_back_angle=8), 0.0, 0.0, 0),
            (SHORT_FORM, Pose(bob=0.78, body_lean=-0.02, arm_front_angle=36, arm_back_angle=-18, leg_front_angle=-2, leg_back_angle=8), 0.0, 0.0, 0),
            (TALL_FORM, Pose(bob=0.48, body_lean=0.0, arm_front_angle=72, arm_back_angle=-28, leg_front_angle=4, leg_back_angle=2), 0.0, 0.0, 0),
            (SHORT_FORM, Pose(bob=0.25, body_lean=0.0, arm_front_angle=46, arm_back_angle=-10, leg_front_angle=0, leg_back_angle=0), 0.0, 0.0, 0),
        ]
        active_form, pose, wing_boost, sleeve_wing_boost, extra_star_phase = big_shrink_seq[frame_idx % len(big_shrink_seq)]

        def painter(px) -> None:
            _draw_power_loss_sparkles(px, frame_idx, fire=True)
            _draw_side_pose(
                px,
                active_form,
                pose,
                animation="big_shrink",
                wing_boost=wing_boost,
                sleeve_wing_boost=sleeve_wing_boost,
                extra_star_phase=extra_star_phase,
            )

        sprite = rasterize_logical(LOGICAL_SIZE, SCALE, painter)
        return _publish_frame(sprite)

    pose_seq = _poses_for(form).get(animation) or SHORT_POSES["idle"]
    pose = pose_seq[frame_idx % len(pose_seq)]

    def painter(px) -> None:
        if pose.mode == "dead":
            _draw_dead_front(px, form, pose)
        else:
            _draw_side_pose(px, form, pose, animation=animation)

    sprite = rasterize_logical(LOGICAL_SIZE, SCALE, painter)
    return _publish_frame(sprite)


def _actor_metadata(form: FormSpec) -> dict:
    metadata = copy.deepcopy(ACTOR_METADATA_BASE)

    def output_px(value: float) -> float:
        return value * OUTPUT_RESOLUTION_SCALE
    metadata.update(
        {
            "actor": {
                "character_id": f"pc_{form.target_name}",
                "display_name": form.display_name,
            },
            "body": {
                **ACTOR_METADATA_BASE["body"],
                "body_kind": "Tall" if form.tall else "Compact",
                "traits": ["hero", "retro", "platformer", form.power],
            },
            "sockets": {
                "head": {
                    "source": f"{form.target_name}.geometry",
                    "point": {
                        "x": output_px(39.0),
                        "y": output_px(16.0 if form.tall else 20.0),
                    },
                },
                "hand_r": {
                    "source": f"{form.target_name}.geometry",
                    "point": {"x": output_px(58.0), "y": output_px(54.0)},
                },
                "hand_l": {
                    "source": f"{form.target_name}.geometry",
                    "point": {"x": output_px(23.0), "y": output_px(54.0)},
                },
                "foot_r": {
                    "source": f"{form.target_name}.geometry",
                    "point": {"x": output_px(49.0), "y": output_px(88.0)},
                },
                "foot_l": {
                    "source": f"{form.target_name}.geometry",
                    "point": {"x": output_px(35.0), "y": output_px(88.0)},
                },
            },
            "tags": [*ACTOR_METADATA_BASE["tags"], form.power],
            "authoring_description": (
                "Mary-O v2 is an additive second-draft reinterpretation of the accepted "
                "Super Mary-O family. It preserves the platformer movement vocabulary and "
                "form progression while redrafting the silhouette, cap, bodice, skirt, "
                "boots, wing language, and fire-form ornamentation as a coherent costume."
            ),
            "gameplay_description": (
                f"Use the {form.display_name} sheet as a responsive retro-platform hero "
                f"in her {form.power} state. Games may opt into running, jumping, skidding, "
                "climbing, swimming, growth, or fireball actions according to the form's "
                "published animation set."
            ),
            "dialogue_hints": {
                "barks": [
                    "A clear jump is a kind of argument.",
                    "The level can keep its royal road. I brought running shoes.",
                    "One more platform.",
                ]
            },
        }
    )
    bindings = metadata["animation_bindings"]
    if form.tall:
        bindings["locomotion.crouch"] = {"animation": "crouch", "events": []}
    # Each sheet publishes the transitions that ARRIVE at it (see the row
    # tables): the short form knows how it was shrunk into, the tall form knows
    # how it was grown or dropped into, and the fire form knows how it was
    # transformed into.
    if form.power == "short":
        bindings["power.shrink"] = {"animation": "shrink", "events": []}
        bindings["power.big_shrink"] = {"animation": "big_shrink", "events": []}
    if form.power == "tall":
        bindings["power.grow"] = {"animation": "grow", "events": []}
        bindings["power.shrink"] = {"animation": "shrink", "events": []}
    if form.power == "fire":
        bindings["ability.fireball"] = {"animation": "fireball", "events": []}
        bindings["power.transform"] = {"animation": "transform", "events": []}
    return metadata


def _render_form(form: FormSpec, out_dir: str | Path) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
        return _draw_form(form, animation, frame_idx, nframes)

    def body_metrics(fw: int, fh: int):
        """Author the gameplay body instead of measuring the alpha bbox.

        See ``BODY_BOX_WIDTH`` in the model for why: the measured box includes
        her cap tip, ponytail, sleeves, and flame frills, none of which should
        stop her against a wall.
        """
        box = form_collision_box(form)
        feet_x = box["x"] + box["w"] / 2.0
        feet_y = float(box["y"] + box["h"])
        return {
            "body_pixel_bbox": box,
            "feet_pixel": {"x": round(feet_x, 3), "y": round(feet_y, 3)},
            "feet_anchor_norm": {
                "x": round(feet_x / fw - 0.5, 6),
                "y": round(0.5 - feet_y / fh, 6),
            },
        }

    outputs = build_sheet(
        target=form.target_name,
        rows=form.rows,
        render_fn=render_frame,
        out_dir=out_dir,
        frame_size=FRAME_SIZE,
        label_width=LABEL_WIDTH,
        auto_crop=False,
        actor_metadata=_actor_metadata(form),
        body_metrics_fn=body_metrics,
        trim=False,
    )
    return [
        outputs[k]
        for k in (
            "canonical",
            "canonical_transparent",
            "spritesheet",
            "yaml",
            "ron",
            "actor",
            "preview",
        )
    ]


def render_mary_o_v2(out_dir: str | Path, **opts) -> List[Path]:
    return _render_form(SHORT_FORM, out_dir)


def render_mary_o_v2_tall(out_dir: str | Path, **opts) -> List[Path]:
    return _render_form(TALL_FORM, out_dir)


def render_mary_o_v2_fire(out_dir: str | Path, **opts) -> List[Path]:
    return _render_form(FIRE_FORM, out_dir)


TARGETS = {
    SHORT_FORM.target_name: {"render": render_mary_o_v2, "actor_metadata": _actor_metadata(SHORT_FORM)},
    TALL_FORM.target_name: {"render": render_mary_o_v2_tall, "actor_metadata": _actor_metadata(TALL_FORM)},
    FIRE_FORM.target_name: {"render": render_mary_o_v2_fire, "actor_metadata": _actor_metadata(FIRE_FORM)},
}


def render(out_dir: str | Path, **opts) -> List[Path]:
    return render_mary_o_v2(out_dir, **opts)
