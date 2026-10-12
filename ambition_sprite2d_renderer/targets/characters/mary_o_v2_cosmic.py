"""Eternal Cosmic Mary-O: her ultimate form, and the transformation into it.

One target, ``mary_o_v2_cosmic``: the rows of her grown forms, with wings
that beat in a jump and that hold the air in a fall, and the row
``transform``, the transformation from her fire form in 36 frames. The sheet
is of the form arrived at, as each transition of Mary-O is.

The painter is :mod:`._mary_o_v2_cosmic_art`. Each frame is drawn on one
stage, large enough for the transformation; the sheet builder packs each
frame to what is drawn in it, so the room is not paid for in the page.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image

from ...authoring.sheet_build import build_sheet
from . import _mary_o_v2_model as M
from ._mary_o_v2_cosmic_art import COSMIC_FORM, Look, Pose, Stage, frame
from .mary_o_v2 import _actor_metadata

TARGET = "mary_o_v2_cosmic"
LABEL_WIDTH = 122

#: The canvas of each frame: room for her wings over her head and behind
#: her, and, in the transformation, for the star that comes down, for the
#: column of light, and for the star behind her last pose.
STAGE = Stage(w=72, h=84, ox=24.0, oy=38.0)

TRANSFORM_FRAMES = 36
TRANSFORM_FRAME_MS = 95

ROWS: List[Tuple[str, int, int]] = [
    ("idle", 4, 180),
    ("death", 1, 120),
    ("walk", 3, 95),
    # A jump is one beat of her wings: up, hard down, and back. The row goes
    # round while she rises, so a line of jumps in the air is a flight.
    ("jump", 8, 70),
    ("fall", 2, 140),
    ("skid", 1, 110),
    ("crouch", 1, 120),
    ("crouch_walk", 3, 110),
    ("crouch_jump", 1, 120),
    ("climb", 2, 120),
    ("swim", 6, 100),
    ("shoot", 3, 60),
    # The transformation, from her fire form. The game holds her in this row
    # for as long as it takes to draw (`cosmic.rs`).
    ("transform", TRANSFORM_FRAMES, TRANSFORM_FRAME_MS),
]

POSES: Dict[str, List[Pose]] = M.poses_for_form(COSMIC_FORM)

#: The beat of her wings in a jump: `(beat, fan, sway of her hair)`.
WING_BEAT = ((-22, 1.2, -0.6), (-34, 1.3, -1.0), (14, 1.0, 0.4), (58, 0.72, 1.6), (74, 0.6, 1.9), (46, 0.8, 1.0), (16, 0.95, 0.3), (0, 1.0, 0.0))


def mix(a: float, b: float, t: float) -> float:
    return a + (b - a) * max(0.0, min(1.0, t))


def look_for(animation: str, frame_idx: int) -> Look:
    """Her look in one frame of a row of the form."""
    poses = POSES.get(animation) or POSES["jump" if animation == "fall" else "idle"]
    pose = poses[frame_idx % len(poses)]
    if animation == "idle":
        breath = (0.0, 0.5, 1.0, 0.5)[frame_idx % 4]
        return Look(pose=pose, anim=animation, beat=-7.0 * breath, sway=0.5 * breath, crown=(0.4 * breath, 1.0, -90.0))
    if animation == "jump":
        beat, fan, sway = WING_BEAT[frame_idx % len(WING_BEAT)]
        return Look(pose=pose, anim=animation, beat=beat, fan=fan, sway=sway)
    if animation == "fall":
        # Her wings are wide and high, and they hold the air: she comes down slowly.
        return Look(pose=pose, anim="jump", beat=(-24.0, -19.0)[frame_idx % 2], fan=1.28, sway=-1.2)
    if animation in ("walk", "crouch_walk", "climb", "swim"):
        swing = (1.0, 0.0, -1.0, 0.0)[frame_idx % 4]
        return Look(pose=pose, anim=animation, beat=4.0 * swing, sway=0.4 * swing)
    if animation in ("crouch", "crouch_jump"):
        # Her wings are closed at her back: she is as small as she can be.
        return Look(pose=pose, anim=animation, beat=34.0, fan=0.6)
    return Look(pose=pose, anim=animation)


def transformation() -> List[Look]:
    """The transformation, from her fire form: 36 frames."""
    looks: List[Look] = []
    reach = Pose(bob=-0.4, arm_front_angle=165, arm_back_angle=-12, leg_front_angle=4, leg_back_angle=-4)
    # 1. The call: she lifts her hand, and the star comes down to her in a column of light.
    for i in range(6):
        t = i / 5
        looks.append(Look(cosmic=False, pose=Pose(bob=-0.4 * t, arm_front_angle=mix(15, 165, t), arm_back_angle=mix(0, -12, t)),
                          crown=(mix(34, 9, t), mix(0.6, 1.1, t), -90 + i * 24), column=t, lift=mix(0, 1.5, t)))
    # 2. Light: she is a figure of light, and she turns one time about.
    for i, spin in enumerate((1.0, 0.45, -0.45, -1.0, -0.45, 0.45)):
        looks.append(Look(cosmic=i >= 3, hair=0, wing=0, ring=0, pose=reach, light=min(1.0, 0.55 + i * 0.45), spin=spin,
                          crown=(9, 1.1, -90 + (6 + i) * 24), column=1.0, lift=mix(1.5, 5, i / 5), wing_boost=0.9 if i < 3 else 0.0))
    # 3. The gown: a ring of light goes up her, and under it she is the new form.
    for i in range(5):
        t = i / 4
        looks.append(Look(hair=0, wing=0, ring=0, pose=reach, light=1.0, reveal=t * 0.86, sweep=t * 0.9, crown=(9, 1.1, -90 + (12 + i) * 24), column=1.0, lift=5))
    # 4. Her hair: out and down, in three steps.
    for i, t in enumerate((0.35, 0.75, 1.0)):
        looks.append(Look(hair=t, wing=0, ring=0, sway=-1.5 + i * 0.6, pose=Pose(bob=-0.4, arm_front_angle=mix(165, 120, t), arm_back_angle=-12),
                          crown=(9, 1.1, -90 + (17 + i) * 24), column=mix(1.0, 0.6, t), lift=5))
    # 5. The ring, and the star comes down on her head.
    for i, t in enumerate((0.34, 0.67, 1.0)):
        looks.append(Look(wing=0, ring=t, pose=Pose(bob=-0.4, arm_front_angle=mix(120, 60, t), arm_back_angle=-12),
                          crown=(mix(9, 0, t), mix(1.1, 1.0, t), -90 + (20 + i) * 24 * (1 - t)), column=mix(0.6, 0.25, t), lift=5))
    # 6. Her wings: from closed at her back to open over her head.
    for i, (size, beat, fan) in enumerate(((0.35, 62, 0.45), (0.65, 40, 0.7), (0.9, 8, 1.0), (1.0, -26, 1.25))):
        looks.append(Look(wing=size, beat=beat, fan=fan, pose=Pose(bob=-0.4, arm_front_angle=mix(60, 30, i / 3), arm_back_angle=mix(-12, -30, i / 3)), column=mix(0.25, 0.0, i / 3), lift=5))
    # 7. The pose: her hand up, her wings wide, and a star behind her.
    final = Pose(bob=-0.8, body_lean=0.3, arm_front_angle=152, arm_back_angle=-46, leg_front_angle=16, leg_back_angle=-12)
    for i, (burst, beat, fan) in enumerate(((0.55, -30, 1.3), (1.0, -34, 1.35), (1.0, -30, 1.3), (0.9, -26, 1.28), (0.6, -22, 1.2))):
        looks.append(Look(pose=final, anim="jump", beat=beat, fan=fan, burst=burst, burst_turn=i * 7.5, lift=5 + (1.0 if i in (1, 2) else 0.0), sway=-0.8))
    # 8. She comes down to the ground, and her wings come to rest. The last
    # frame is the first frame of her idle.
    for i in range(4):
        t = (i + 1) / 4
        if i == 3:
            looks.append(look_for("idle", 0))
            break
        looks.append(Look(pose=Pose(bob=-0.8 * (1 - t), arm_front_angle=mix(152, 10, t), arm_back_angle=mix(-46, 0, t)), beat=mix(-22, 0, t), fan=mix(1.2, 1.0, t), lift=mix(5, 0, t), sway=mix(-0.8, 0, t)))
    assert len(looks) == TRANSFORM_FRAMES, len(looks)
    return looks


def _body_metrics(stage: Stage):
    def metrics(fw: int, fh: int) -> dict:
        box = stage.body_box_px()
        feet_x, feet_y = stage.feet_px
        return {
            "body_pixel_bbox": box,
            "feet_pixel": {"x": round(feet_x, 3), "y": round(feet_y, 3)},
            "feet_anchor_norm": {"x": round(feet_x / fw - 0.5, 6), "y": round(0.5 - feet_y / fh, 6)},
        }

    return metrics


def _cosmic_metadata() -> dict:
    """Her actor metadata: that of the fire form, with her own name, her own
    frame and a row of her own for a fall."""
    metadata = copy.deepcopy(_actor_metadata(M.FIRE_FORM))
    metadata["actor"] = {"character_id": f"pc_{TARGET}", "display_name": "Eternal Cosmic Mary-O"}
    metadata["body"]["traits"] = ["hero", "retro", "platformer", "cosmic"]
    metadata["tags"] = [tag for tag in metadata["tags"] if tag != "fire"] + ["cosmic"]
    # A socket of the fire form is in the pixels of its published frame: two
    # times the authored 80 by 96, with her 72 by 96 drawing in its middle.
    for socket in metadata["sockets"].values():
        socket["source"] = f"{TARGET}.geometry"
        point = socket["point"]
        point["x"] = STAGE.ox * 3 + point["x"] / M.OUTPUT_RESOLUTION_SCALE - 4.0
        point["y"] = STAGE.oy * 3 + point["y"] / M.OUTPUT_RESOLUTION_SCALE
    bindings = metadata["animation_bindings"]
    bindings["locomotion.fall"] = {"animation": "fall", "events": []}
    bindings["power.transform"] = {"animation": "transform", "events": []}
    metadata["authoring_description"] = (
        "Eternal Cosmic Mary-O is the ultimate form of Mary-O v2: a gown of the night sky, hair of "
        "starlight, wings of crystal, the ring of a planet about her head and a star over her cap."
    )
    metadata["gameplay_description"] = (
        "Use the Eternal Cosmic Mary-O sheet for her ultimate form: she is not hurt, each jump in "
        "the air is a beat of her wings, and she is faster than her other forms."
    )
    return metadata


def render_cosmic(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    looks = transformation()

    def render_frame(animation: str, frame_idx: int, nframes: int) -> Image.Image:
        del nframes
        if animation == "transform":
            return frame(STAGE, looks[frame_idx])
        return frame(STAGE, look_for(animation, frame_idx))

    frame_transform: dict = {}
    outputs = build_sheet(
        target=TARGET,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=out_dir,
        frame_transform_out=frame_transform,
        frame_size=STAGE.frame_px,
        label_width=LABEL_WIDTH,
        auto_crop=False,
        actor_metadata=_cosmic_metadata(),
        body_metrics_fn=_body_metrics(STAGE),
        animation_key_map={name: name for name, _frames, _duration in ROWS},
        # Her body is the authored box in each pose. Her wings and her hair
        # are not her body: a measured body would be as wide as her wings.
        pose_bodies="authored",
    )
    parts = _publish_parts(render_frame, outputs, frame_transform, out_dir)
    return [outputs[key] for key in ("canonical", "canonical_transparent", "spritesheet", "yaml", "ron", "actor", "preview")] + list(parts.values())


def _publish_parts(render_frame, outputs, frame_transform, out_dir: Path) -> dict:
    """Her part flipbook: each row but the transformation, as its layers.

    A reader in the game draws about her body and not about her wings (the
    barrier of the form), and the tracks say which is which
    (`_mary_o_v2_cosmic_art.BODY_TRACKS`). So she is drawn from parts for what
    the tracks say, and the cost of the pages does not decide it. The
    transformation has light on the whole figure and a turn of it, which no
    part carries: its row stays the sheet's."""
    import yaml

    from ...authoring import rigdoc
    from ...authoring.part_flipbook import REALIZE_PARTS, build_rig_flipbook, sheet_feet
    from ...authoring.sheet_build import rendering_canonical_only, rendering_quality_tier

    if rendering_canonical_only() or rendering_quality_tier() or "yaml" not in outputs:
        return {}
    sheet = yaml.safe_load(Path(outputs["yaml"]).read_text())
    size = (int(sheet["frame_width"]), int(sheet["frame_height"]))
    dx, dy = int(frame_transform.get("dx", 0)), int(frame_transform.get("dy", 0))

    def published(row: str, index: int, count: int) -> Image.Image:
        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
        rigdoc.composite_canvas(canvas, render_frame(row, index, count), (dx, dy))
        return canvas

    part_rows = [name for name, _frames, _duration in ROWS if name != "transform"]
    flipbook = build_rig_flipbook(TARGET, ROWS, published, part_rows, sheet_feet(Path(outputs["yaml"])), size)
    flipbook.pack()
    flipbook.realize = REALIZE_PARTS
    print(f"[part flipbook] {TARGET}: realize parts (a reader needs her tracks), {flipbook.packed_texels()} texels", flush=True)
    return flipbook.write(out_dir)


TARGETS = {
    TARGET: {"render": render_cosmic, "actor_metadata": _cosmic_metadata()},
}


def render(out_dir: str | Path, **opts) -> List[Path]:
    return render_cosmic(out_dir, **opts)
