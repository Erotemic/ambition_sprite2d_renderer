"""Canonical SVG-rigged fighter target for Noether.

``assets/noether.svg`` is the art, z-order, joint, and source-view authority.
The generated rig owns natural pose, IK anatomy, skirt secondary motion, and
fighter clips. The source SVG is never rewritten by this target or its builder.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from PIL import Image

from ...authoring.canonical_scientist_rig import load_scientist_rig
from ...authoring.portrait import (
    FaceGuide,
    PortraitClip,
    render_framed_portrait,
    write_portrait_sheet,
)
from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet, write_canonical
from ._svg_fighter_effects import compose_rig_frame
from .noether_gameplay import (
    NOETHER_MOVE_BLUEPRINT,
    PADDING as RIG_RENDER_PADDING,
    attack_hitboxes,
    body_metrics as authored_body_metrics,
    hurtbox_parts_for_rows,
)
from .noether_effects import apply_ethereal_hum, draw_noether_behind, draw_noether_front
from .noether_motion import EFFECT_ALIASES, FIGHTER_MOTION_COVERAGE, NOETHER_ROWS

TARGET_NAME = "noether"


def frame_size() -> Tuple[int, int]:
    """The published frame: the RIG's own canvas plus this target's padding.

    ⛔ **not a restated constant.** This used to read `RIG_FRAME_SIZE = (192, 208)`
    beside a `noether_gameplay` that restated the rig's ground line, and when the
    rig was rebuilt only one of the two copies moved — which is how Emmy ended up
    hovering forty pixels above the floor. A function, so the rig document is
    read at render time rather than rebuilt at import time.
    """
    frame = _doc().frame
    #  `render_scale` is the third term and it is easy to forget: the composer
    # pads in RIG units and scales the padded canvas, so a rig published at 2x
    # emits a frame twice this wide. Dropping it here would hand `build_sheet` a
    # frame size the renderer never produces.
    scale = max(1, int(frame.get("render_scale", 1)))
    return (
        (int(frame["width"]) + RIG_RENDER_PADDING * 2) * scale,
        (int(frame["height"]) + RIG_RENDER_PADDING * 2) * scale,
    )


ROWS: List[Tuple[str, int, int]] = list(NOETHER_ROWS)

ACTOR_METADATA = {
    "actor": {
        #  the CANONICAL GAME id, not the target name. `TARGET_NAME` stays
        # "noether" (it names the render target and its output directory); the
        # actor metadata is what the game resolves a body's identity through, and
        # Ambition's catalog row is `npc_emmy_noether`. A mismatch here is what the
        # game-side identity waiver existed for.
        "character_id": "npc_emmy_noether",
        "display_name": "Emmy Ethereal",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": [
            "special_character",
            "humanoid",
            "noether",
            "classification_fighter",
            "playable_candidate",
            "svg_rigged",
        ],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": True,
            "climb": True,
            "swim": True,
            "crawl": True,
            "use_lifts": True,
        },
        "interactions": {
            "talk": True,
            "carry": True,
        },
    },
    "visual": {
        "default_pose": "idle",
        "canonical_source": "assets/noether.svg",
    },
    "actions": {
        "default_preset": "noether",
        "authored_moves": NOETHER_MOVE_BLUEPRINT,
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "action.melee.primary": {"animation": "generator_strike", "events": []},
        "action.special.primary": {"animation": "conservation_law", "events": []},
        "action.special.secondary": {"animation": "symmetry_shift", "events": []},
        "action.special.up": {"animation": "ethereal_lift", "events": []},
        "action.special.down": {"animation": "invariant_field", "events": []},
        "action.super": {"animation": "noether_theorem", "events": []},
        "action.defense.parry": {"animation": "invariant_parry", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
    },
    "authoring_description": (
        "A Noether-inspired fighter whose visual and mechanical language centers on "
        "symmetry, invariants, conservation laws, and an ethereal transformation motif. "
        "The canonical side-view paper doll is manually traced in assets/noether.svg; "
        "generated rig data must not rewrite that source artwork."
    ),
    "gameplay_description": (
        "A technical medium-weight fighter using symmetry transformations and conserved "
        "quantities for spacing, reversals, and control. Her up special is an ethereal "
        "lift/recovery, while the three-panel dress uses restrained rigid secondary "
        "motion rather than cloth simulation."
    ),
}


def _doc() -> RigDocument:
    return load_scientist_rig(TARGET_NAME)


def render_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    doc = _doc()
    t = doc.frame_time(animation, frame_idx, frame_count)
    solved = doc.solve(animation, t)
    rig_image = doc.render_at(
        animation,
        t,
        solved=solved,
        padding=RIG_RENDER_PADDING,
    )
    effect_animation = EFFECT_ALIASES.get(animation, animation)
    frame = compose_rig_frame(
        doc,
        animation,
        frame_idx,
        frame_count,
        behind=lambda canvas, t, world, params: draw_noether_behind(
            effect_animation, canvas, t, world, params
        ),
        front=lambda canvas, t, world, params: draw_noether_front(
            effect_animation, canvas, t, world, params
        ),
        padding=RIG_RENDER_PADDING,
        solved=solved,
        rig_image=rig_image,
    )
    return apply_ethereal_hum(frame, rig_image, t)


def _silhouette_profile() -> dict:
    """Per-column alpha coverage of her idle pose, on the published frame.

    The measurement `body_metrics` trims into a body box. Rendering one frame to
    ask where the character actually IS costs about a second and replaces a
    guessed fraction of her stature — see `noether_gameplay.body_from_silhouette`.
    """
    # Measure the solved body art, not presentation effects. Emmy's persistent
    # ethereal hum intentionally extends beyond her silhouette and must never
    # enlarge gameplay/body metadata.
    frame = _doc().render_frame("idle", 0, 8, padding=RIG_RENDER_PADDING)
    alpha = frame.getchannel("A")
    bounds = alpha.getbbox() or (0, 0, frame.width, frame.height)
    pixels = alpha.load()
    columns = [
        sum(1 for y in range(bounds[1], bounds[3]) if pixels[x, y] > 16)
        for x in range(frame.width)
    ]
    return {"columns": columns, "bounds": bounds}


# Emmy's portrait viewport in her 192x208 rig canvas. Author it in canvas
# coordinates so render scale and supersampling do not move the crop. The view
# centers the face while retaining collar and shoulders.
#
#  the viewport centre is to the RIGHT of the face on purpose. Her art is drawn
# facing east with an extended arm, so centring the crop on the face put 48px of
# dead space behind her head and clipped the hand flush against the frame edge.
# Offsetting gives looking-room in the direction she faces, which is ordinary
# portrait composition and not a fudge for this one rig.
_PORTRAIT_FACE = FaceGuide(
    center_x=101.0,
    center_y=50.0,
    width=40.0,
    height=44.0,
    source_width=192.0,
    source_height=208.0,
)
# Head-and-shoulders. Patent Clerk frames 78 of a 176-wide canvas (0.44); this is
# the same fraction of Emmy's wider canvas, so the two read at one scale when the
# Hall shows them side by side.
_PORTRAIT_VIEW_WIDTH = 86.0
_PORTRAIT_CENTER_Y = 68.0


def render_portraits(out_dir: str | Path, **opts):
    """Publish Emmy's close-ups from her own rig, framed and MOVING.

    ⭐ the default clip loops rather than holding a still. A portrait that never
    moves reads as a broken asset next to a Hall full of animated bodies, and her
    idle already carries the restrained secondary motion the dress was rigged for
    — there was nothing to author, only something to publish.
    """
    del opts
    doc = _doc()

    def frame(animation: str, index: int, count: int) -> Image.Image:
        source = doc.render_at(
            animation,
            doc.frame_time(animation, index, count),
            supersample=4,
            scale=3,
        )
        return render_framed_portrait(
            source,
            _PORTRAIT_FACE,
            view_width=_PORTRAIT_VIEW_WIDTH,
            center_y=_PORTRAIT_CENTER_Y,
        )

    def loop(animation: str, count: int, duration_ms: int) -> PortraitClip:
        return PortraitClip(
            tuple(frame(animation, index, count) for index in range(count)),
            duration_ms=duration_ms,
            looping=True,
        )

    clips = {
        "default": loop("idle", 8, 148),
        "talking": loop("talk", 8, 104),
        "inspecting": PortraitClip.still(frame("interact", 4, 8)),
    }
    return write_portrait_sheet(TARGET_NAME, clips, Path(out_dir))


def render(out_dir: str | Path, **opts):
    del opts
    doc = _doc()
    profile = _silhouette_profile()
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=Path(out_dir),
        frame_size=frame_size(),
        auto_crop=False,
        actor_metadata=ACTOR_METADATA,
        body_metrics_fn=lambda fw, fh: authored_body_metrics(fw, fh, profile),
        sheet_tuning=doc.sprite_tuning or {"collision_scale": 1.86},
        animation_key_map={name: name for name, _frames, _duration in ROWS},
        attack_hitboxes=attack_hitboxes(),
        hurtbox_parts=hurtbox_parts_for_rows(ROWS),
        pose_bodies="authored",
        trim=True,
    )
    keys = (
        "spritesheet",
        "yaml",
        "ron",
        "actor",
        "canonical",
        "canonical_transparent",
        "preview",
    )
    return [Path(outputs[key]) for key in keys if outputs.get(key)]


def render_canonical(out_dir: str | Path, **opts):
    del opts
    return write_canonical(
        TARGET_NAME,
        ROWS,
        render_frame,
        Path(out_dir),
        frame_size=frame_size(),
    )


__all__ = [
    "ACTOR_METADATA",
    "FIGHTER_MOTION_COVERAGE",
    "ROWS",
    "frame_size",
    "TARGET_NAME",
    "render",
    "render_portraits",
    "render_canonical",
    "render_frame",
]
