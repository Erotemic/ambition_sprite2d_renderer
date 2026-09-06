"""Non-authoritative Mary-O SVG rigid-bone proof of concept.

This target intentionally coexists with ``mary_o_v2``.  It publishes parallel
``*_svg_poc`` sheets from ``assets/mary_o_v2.svg`` so the editable SVG + rigid
bone workflow can be judged without changing game-facing Mary-O output.

Ordinary side-view animation and the front-facing death pose are assembled
from rigid SVG groups. Arms and legs each have one authored shape per projection
and rotate around shoulder/hip pivots; there is no alternate rotated-arm or
rotated-leg artwork. Presentation flashes and power-change particles remain
Python postprocess effects, following the same separation already used by Noether.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Dict, List

from PIL import Image

from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet
from . import mary_o_v2 as procedural
from ._mary_o_v2_model import (
    FIRE_FORM,
    FRAME_SIZE,
    LABEL_WIDTH,
    MARY_FIRE,
    MARY_FIRE_BLAST,
    MARY_FIRE_FLASH,
    MARY_NORMAL,
    SHORT_FORM,
    SHORT_POSES,
    TALL_FORM,
    TALL_LIKE_POSES,
    poses_for_form,
    FormSpec,
    Pose,
    _form_with_palette,
    _mix_outfit_palette,
    _transition_form,
    form_collision_box,
)
from ._mary_o_v2_svg_poc import (
    build_rig_document,
    composite_effects,
    render_pose_with_doc,
)

TARGET_SUFFIX = "_svg_poc"
ASSET_PATH = Path(__file__).resolve().parents[3] / "assets" / "mary_o_v2.svg"


def _target_name(form: FormSpec) -> str:
    return f"{form.target_name}{TARGET_SUFFIX}"


def _poses_for(form: FormSpec):
    return poses_for_form(form)


def _palette_pairs(source: FormSpec, active: FormSpec):
    fields = ("cap", "shirt", "overalls", "buttons", "gloves", "hair", "skin", "shoes", "accent")
    return [
        (getattr(source.palette, field), getattr(active.palette, field))
        for field in fields
        if getattr(source.palette, field) != getattr(active.palette, field)
    ]


def _recolor(image: Image.Image, source: FormSpec, active: FormSpec) -> Image.Image:
    """Palette-remap solid SVG colors while preserving antialiased alpha.

    This is deliberately a transition-only postprocess.  The canonical editable
    SVG remains ordinary colored artwork; temporary transform flashes do not
    multiply SVG source variants.
    """
    pairs = _palette_pairs(source, active)
    if not pairs:
        return image
    lookup = {(a[0], a[1], a[2]): (b[0], b[1], b[2]) for a, b in pairs}
    out = image.copy()
    pixels = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = pixels[x, y]
            repl = lookup.get((r, g, b))
            if repl is not None:
                pixels[x, y] = (*repl, a)
    return out


def _source_form(active: FormSpec) -> FormSpec:
    if active.power == "short" or not active.tall:
        return SHORT_FORM
    # During the first fire flash use the plain tall SVG until the fire geometry
    # is visually present.  This avoids baking transitional wings into anatomy.
    if float(active.magic_stage) < 1.5:
        return TALL_FORM
    return FIRE_FORM if active.power == "fire" else TALL_FORM


def _rig_pose(docs: Dict[str, RigDocument], active: FormSpec, pose: Pose) -> Image.Image:
    source = _source_form(active)
    frame = render_pose_with_doc(docs[source.target_name], source, pose)
    return _recolor(frame, source, active)


def _effect_frame(
    docs: Dict[str, RigDocument],
    active: FormSpec,
    pose: Pose,
    *,
    animation: str,
    frame_idx: int,
    aura: bool = False,
    power_loss: bool = False,
    fire_loss: bool = False,
    sleeve_wing_boost: float = 0.0,
    extra_star_phase: int = 0,
    show_orb: bool = False,
    fixed_transform_orb: bool = False,
) -> Image.Image:
    return composite_effects(
        _rig_pose(docs, active, pose),
        form=active,
        pose=pose,
        animation=animation,
        frame_idx=frame_idx,
        transform_aura=aura,
        power_loss=power_loss,
        fire_loss=fire_loss,
        sleeve_wing_boost=sleeve_wing_boost,
        extra_star_phase=extra_star_phase,
        show_orb=show_orb,
        fixed_transform_orb=fixed_transform_orb,
    )


def _draw_poc_form(
    host_form: FormSpec,
    docs: Dict[str, RigDocument],
    animation: str,
    frame_idx: int,
    nframes: int,
) -> Image.Image:
    if animation == "grow":
        active = SHORT_FORM if frame_idx % 2 == 0 else TALL_FORM
        return _rig_pose(docs, active, Pose())

    if animation == "transform":
        fire_flash_1 = _mix_outfit_palette(MARY_NORMAL, MARY_FIRE_FLASH, 0.45)
        fire_flash_2 = _mix_outfit_palette(MARY_NORMAL, MARY_FIRE_FLASH, 0.88)
        fire_flash_3 = _mix_outfit_palette(MARY_FIRE_FLASH, MARY_FIRE_BLAST, 0.42)
        fire_flash_4 = _mix_outfit_palette(MARY_FIRE_FLASH, MARY_FIRE_BLAST, 0.82)
        fire_reveal_1 = _mix_outfit_palette(MARY_FIRE_BLAST, MARY_FIRE, 0.18)
        fire_reveal_2 = _mix_outfit_palette(MARY_FIRE_BLAST, MARY_FIRE, 0.42)
        fire_reveal_3 = _mix_outfit_palette(MARY_FIRE_BLAST, MARY_FIRE, 0.72)
        seq = [
            (_transition_form(TALL_FORM, MARY_NORMAL, stage=1.00), Pose(), 0.00, 0, False),
            (_transition_form(TALL_FORM, MARY_NORMAL, stage=1.00), Pose(bob=-0.35, arm_front_angle=118, arm_back_angle=42, leg_front_angle=8, leg_back_angle=-8), 0.00, 1, False),
            (_transition_form(FIRE_FORM, fire_flash_1, stage=1.16, power="tall"), Pose(bob=-0.75, body_lean=0.04, arm_front_angle=96, arm_back_angle=30, leg_front_angle=12, leg_back_angle=-9), 0.18, 2, False),
            (_transition_form(FIRE_FORM, fire_flash_2, stage=1.36, power="tall"), Pose(bob=-1.0, body_lean=0.08, arm_front_angle=90, arm_back_angle=20, leg_front_angle=15, leg_back_angle=-11), 0.56, 3, False),
            (_transition_form(FIRE_FORM, fire_flash_3, stage=1.62, power="fire"), Pose(bob=-1.18, body_lean=0.11, arm_front_angle=98, arm_back_angle=18, leg_front_angle=17, leg_back_angle=-12), 0.92, 3, False),
            (_transition_form(FIRE_FORM, fire_flash_4, stage=1.86, power="fire"), Pose(bob=-1.32, body_lean=0.13, arm_front_angle=106, arm_back_angle=20, leg_front_angle=18, leg_back_angle=-13), 1.18, 3, False),
            (_transition_form(FIRE_FORM, MARY_FIRE_BLAST, stage=2.00, power="fire"), Pose(bob=-1.40, body_lean=0.14, arm_front_angle=112, arm_back_angle=22, leg_front_angle=20, leg_back_angle=-15), 1.34, 3, False),
            (_transition_form(FIRE_FORM, fire_reveal_1, stage=1.94, power="fire"), Pose(bob=-1.08, body_lean=0.14, arm_front_angle=108, arm_back_angle=18, leg_front_angle=18, leg_back_angle=-12), 1.18, 3, False),
            (_transition_form(FIRE_FORM, fire_reveal_2, stage=1.98, power="fire"), Pose(bob=-0.72, body_lean=0.12, arm_front_angle=86, arm_back_angle=6, leg_front_angle=12, leg_back_angle=-8), 1.02, 3, False),
            (_transition_form(FIRE_FORM, fire_reveal_3, stage=2.00, power="fire"), Pose(bob=-0.45, body_lean=0.10, arm_front_angle=70, arm_back_angle=-4, leg_front_angle=10, leg_back_angle=-6), 0.96, 3, True),
            (FIRE_FORM, TALL_LIKE_POSES["fireball"][0], 1.0, 3, True),
        ]
        active, pose, sleeve, stars, orb = seq[frame_idx % len(seq)]
        return _effect_frame(
            docs, active, pose,
            animation=animation, frame_idx=frame_idx, aura=True,
            sleeve_wing_boost=sleeve, extra_star_phase=stars,
            show_orb=orb, fixed_transform_orb=orb,
        )

    if animation == "shrink":
        if host_form.power == "tall":
            fire_dull_1 = _mix_outfit_palette(MARY_FIRE, MARY_NORMAL, 0.22)
            fire_dull_2 = _mix_outfit_palette(MARY_FIRE, MARY_NORMAL, 0.46)
            fire_dull_3 = _mix_outfit_palette(MARY_FIRE, MARY_NORMAL, 0.72)
            seq = [
                (FIRE_FORM, Pose(mode="fireball", bob=0.1, arm_front_angle=35, arm_back_angle=-18, leg_front_angle=-12, leg_back_angle=22), 0.95, 2),
                (_transition_form(FIRE_FORM, fire_dull_1, stage=1.82, power="fire"), Pose(bob=0.35, body_lean=-0.1, arm_front_angle=24, arm_back_angle=-36, leg_front_angle=-8, leg_back_angle=18), 0.70, 1),
                (_transition_form(FIRE_FORM, fire_dull_2, stage=1.56, power="fire"), Pose(bob=0.7, body_lean=-0.18, arm_front_angle=10, arm_back_angle=-58, leg_front_angle=5, leg_back_angle=10), 0.35, 1),
                (_transition_form(FIRE_FORM, fire_dull_3, stage=1.28, power="tall"), Pose(bob=1.0, body_lean=-0.08, arm_front_angle=88, arm_back_angle=-80, leg_front_angle=14, leg_back_angle=4), 0.08, 0),
                (_transition_form(TALL_FORM, _mix_outfit_palette(MARY_NORMAL, MARY_FIRE, 0.18), stage=1.06), Pose(bob=0.75, body_lean=0.02, arm_front_angle=118, arm_back_angle=-48, leg_front_angle=10, leg_back_angle=-2), 0.0, 0),
                (TALL_FORM, Pose(bob=0.3, arm_front_angle=52, arm_back_angle=-12), 0.0, 0),
            ]
            active, pose, sleeve, stars = seq[frame_idx % len(seq)]
            return _effect_frame(docs, active, pose, animation=animation, frame_idx=frame_idx, power_loss=True, fire_loss=True, sleeve_wing_boost=sleeve, extra_star_phase=stars)
        seq = [
            (TALL_FORM, Pose(bob=0.2, body_lean=-0.06, arm_front_angle=24, arm_back_angle=-18, leg_front_angle=-10, leg_back_angle=18), 1),
            (SHORT_FORM, Pose(bob=0.55, body_lean=-0.02, arm_front_angle=40, arm_back_angle=-18, leg_front_angle=-4, leg_back_angle=10), 0),
            (_form_with_palette(TALL_FORM, _mix_outfit_palette(MARY_NORMAL, MARY_FIRE_FLASH, 0.06)), Pose(bob=0.85, body_lean=-0.10, arm_front_angle=88, arm_back_angle=-54, leg_front_angle=8, leg_back_angle=6), 0),
            (SHORT_FORM, Pose(bob=0.35, arm_front_angle=46, arm_back_angle=-10), 0),
        ]
        active, pose, stars = seq[frame_idx % len(seq)]
        return _effect_frame(docs, active, pose, animation=animation, frame_idx=frame_idx, power_loss=True, extra_star_phase=stars)

    if animation == "big_shrink":
        fire_dull_1 = _mix_outfit_palette(MARY_FIRE, MARY_NORMAL, 0.24)
        fire_dull_2 = _mix_outfit_palette(MARY_FIRE, MARY_NORMAL, 0.50)
        fire_dull_3 = _mix_outfit_palette(MARY_FIRE, MARY_NORMAL, 0.78)
        seq = [
            (FIRE_FORM, Pose(mode="fireball", bob=0.1, arm_front_angle=35, arm_back_angle=-18, leg_front_angle=-12, leg_back_angle=22), 1.05, 2),
            (_transition_form(FIRE_FORM, fire_dull_1, stage=1.82, power="fire"), Pose(bob=0.35, body_lean=-0.1, arm_front_angle=24, arm_back_angle=-36, leg_front_angle=-8, leg_back_angle=18), 0.72, 1),
            (_transition_form(FIRE_FORM, fire_dull_2, stage=1.48, power="fire"), Pose(bob=0.7, body_lean=-0.16, arm_front_angle=12, arm_back_angle=-58, leg_front_angle=4, leg_back_angle=12), 0.32, 0),
            (_transition_form(FIRE_FORM, fire_dull_3, stage=1.16, power="tall"), Pose(bob=0.95, body_lean=-0.08, arm_front_angle=84, arm_back_angle=-76, leg_front_angle=12, leg_back_angle=4), 0.0, 0),
            (TALL_FORM, Pose(bob=0.55, body_lean=-0.02, arm_front_angle=58, arm_back_angle=-22, leg_front_angle=-2, leg_back_angle=8), 0.0, 0),
            (SHORT_FORM, Pose(bob=0.78, body_lean=-0.02, arm_front_angle=36, arm_back_angle=-18, leg_front_angle=-2, leg_back_angle=8), 0.0, 0),
            (TALL_FORM, Pose(bob=0.48, arm_front_angle=72, arm_back_angle=-28, leg_front_angle=4, leg_back_angle=2), 0.0, 0),
            (SHORT_FORM, Pose(bob=0.25, arm_front_angle=46, arm_back_angle=-10), 0.0, 0),
        ]
        active, pose, sleeve, stars = seq[frame_idx % len(seq)]
        return _effect_frame(docs, active, pose, animation=animation, frame_idx=frame_idx, power_loss=True, fire_loss=True, sleeve_wing_boost=sleeve, extra_star_phase=stars)

    pose_seq = _poses_for(host_form).get(animation) or SHORT_POSES["idle"]
    pose = pose_seq[frame_idx % len(pose_seq)]
    if animation == "death":
        # Death is a front projection, so it deliberately uses the front SVG
        # component library rather than falling back to procedural rotated limbs.
        return render_pose_with_doc(docs[f"{host_form.target_name}:front"], host_form, pose)
    frame = _rig_pose(docs, host_form, pose)
    if animation == "fireball":
        frame = composite_effects(frame, form=host_form, pose=pose, animation=animation, frame_idx=frame_idx, show_orb=True)
    return frame


def _actor_metadata(form: FormSpec) -> dict:
    metadata = copy.deepcopy(procedural._actor_metadata(form))
    metadata["actor"]["character_id"] = f"pc_{_target_name(form)}"
    metadata["actor"]["display_name"] = f"{form.display_name} SVG POC"
    metadata["body"]["traits"] = [*metadata["body"].get("traits", []), "svg_rigged", "proof_of_concept"]
    metadata.setdefault("visual", {})["canonical_source"] = "assets/mary_o_v2.svg"
    metadata["authoring_description"] = (
        "Proof-of-concept Mary-O paper doll. The SVG owns manually editable idle anatomy "
        "and pivots; Python owns rigid bone motion plus transient transform effects. "
        "The shipped mary_o_v2 targets remain authoritative while this POC is evaluated."
    )
    return metadata


def _render_form(form: FormSpec, out_dir: str | Path) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if not ASSET_PATH.exists():
        raise FileNotFoundError(
            f"Mary-O SVG POC source is missing: {ASSET_PATH}. "
            "Run scripts/export_mary_o_v2_svg.py explicitly to create a fresh seed."
        )

    docs: Dict[str, RigDocument] = {}
    for source in (SHORT_FORM, TALL_FORM, FIRE_FORM):
        docs[source.target_name] = build_rig_document(ASSET_PATH, source, "side")
        docs[f"{source.target_name}:front"] = build_rig_document(ASSET_PATH, source, "front")

    def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
        return _draw_poc_form(form, docs, animation, frame_idx, nframes)

    def body_metrics(fw: int, fh: int):
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
        target=_target_name(form), rows=form.rows, render_fn=render_frame,
        out_dir=out_dir, frame_size=FRAME_SIZE, label_width=LABEL_WIDTH,
        auto_crop=False, actor_metadata=_actor_metadata(form),
        body_metrics_fn=body_metrics,
    )
    return [outputs[k] for k in ("canonical", "canonical_transparent", "spritesheet", "yaml", "ron", "actor", "preview")]


#  NO TARGETS HERE ANY MORE: THIS IS MARY-O'S ONLY RENDERER, AND IT SHIPS
# UNDER HER OWN NAMES. `mary_o_v2`, `mary_o_v2_tall` and `mary_o_v2_fire` call
# `_draw_poc_form` directly now, so registering `*_svg_poc` twins would publish
# the same frames under a second set of names and invite the two to drift. The
# module keeps the drawing code; only the duplicate registration is gone.
TARGETS: dict = {}


def render(out_dir: str | Path, **opts) -> List[Path]:
    return render_mary_o_v2_svg_poc(out_dir, **opts)
