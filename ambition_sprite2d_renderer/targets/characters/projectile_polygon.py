"""SVG-rigged Projectile Polygon beast-biped reference.

This target is deliberately both a playable fighter and an animation reference.
The SVG owns a faceted bestial body with a head-mounted cannon; the shared,
editor-neutral polygon motion library still provides a broad conservative pose
vocabulary. Future beast bipeds can copy or inspect these poses before adding
anatomy-specific exaggeration.

This archetype is intentionally non-humanoid. Projectile identity comes from a
head cannon and ranged play; do not add held props, humanoid hands, hair mass,
or costume details that hide the body plan.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ambition_sprite2d_renderer.authoring.motion_ir import CharacterMotionBinding
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

TARGET_NAME = "projectile_polygon"
MOTION_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "characters"
    / TARGET_NAME
    / f"{TARGET_NAME}.motion.json"
)

# A compact vocabulary to show first when using this target as a beast-biped pose
# reference. The rig itself publishes the full fighter vocabulary (136 clips).
SAFE_POSE_REFERENCE = (
    "idle",
    "walk",
    "run",
    "crouch",
    "jump",
    "fall",
    "land_light",
    "turnaround",
    "roll",
    "spot_dodge",
    "air_dodge",
    "shield_raise",
    "jab",
    "attack_side",
    "attack_up",
    "attack_down",
    "smash_forward",
    "smash_up",
    "smash_down",
    "air_neutral",
    "air_forward",
    "air_back",
    "air_up",
    "air_down",
    "grab",
    "grab_hold",
    "pummel",
    "throw_forward",
    "throw_back",
    "throw_up",
    "throw_down",
    "grabbed",
    "launch",
    "knockdown",
    "getup",
    "tech",
    "ledge_grab",
    "ledge_getup",
    "ledge_attack",
    "ledge_roll",
    "ledge_jump",
    "item_hold",
    "item_throw",
    "shoot",
    "taunt",
    "victory_hold",
    "loss",
)

ACTOR_METADATA = {
    "actor": {
        "character_id": TARGET_NAME,
        "display_name": "Projectile Polygon",
    },
    "authoring_description": {
        "concept": (
            "A 2D faceted beast biped inspired by the anonymous Fighting Polygon "
            "Team idea: a deliberately simple body whose readable silhouette "
            "poses can serve as a safe animation reference for more bespoke "
            "non-humanoid fighters. Projectile Polygon is the ranged member of "
            "the trio: a T-rex-like polygon with a head-mounted cannon rather "
            "than a held weapon."
        ),
        "visual_language": [
            "large flat polygon facets instead of anatomical surface detail",
            "teal/cyan body planes with brighter near-side facets",
            "long horizontal torso, heavy hind legs, and a balancing tail",
            "pronounced upper/lower snout silhouette with an integrated top-mounted cannon and a simple visor slit",
            "small forearms keep the silhouette clearly non-humanoid",
            "no hair mass, drop shadow, or held props",
        ],
        "rigging_notes": [
            "The SVG owns artwork and static rig geometry; editor-neutral motion JSON owns reusable poses and clips.",
            "Projectile Polygon still binds to the same conservative polygon clip library so pose semantics stay comparable across the trio.",
            "Near/far names in the SVG are character-relative layers, not camera-centric gameplay semantics.",
            "This projectile variant demonstrates how the same move vocabulary reads on a bestial silhouette with head, tail, and hind-leg emphasis.",
        ],
    },
    "gameplay_description": {
        "role": "fundamental projectile beast-biped / animation reference fighter",
        "combat_identity": [
            "medium-weight ranged fundamentals fighter with a head cannon, compact forelimbs, and clear projectile spacing",
            "complete grounded, aerial, special, defensive, capture, pummel and throw vocabulary",
            "intentionally legible timings and silhouettes rather than species-specific visual tricks",
        ],
        "authoring_notes": [
            "Use this fighter when a new beast-biped or ranged move needs a safe first pose before bespoke posing.",
            "The gameplay repertoire lives in ambition_content; the rig is reusable pose reference art.",
        ],
    },
    "dialogue_hints": {
        "suggested_barks": [
            "TARGET PROFILED.",
            "MAW ALIGNED.",
            "TRAJECTORY LOCKED.",
            "FACETS ENGAGED.",
        ],
        "fallback_dialogue": [
            "Silhouette first. Teeth and tail second.",
            "The head cannon explains the whole plan.",
            "A strange body still needs readable poses.",
        ],
    },
    "body": {
        "body_plan": "BestialBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": [
            "bestial",
            "polygonal",
            "projectile_fighter",
            "animation_reference",
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
        "interactions": {"talk": True, "carry": True},
    },
    "visual": {
        "default_pose": "idle",
        "canonical_source": "data/characters/projectile_polygon/projectile_polygon.svg",
        "pose_reference": list(SAFE_POSE_REFERENCE),
    },
    "actions": {
        "default_preset": TARGET_NAME,
        "archetype": "projectile_beast_biped",
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "action.melee.primary": {"animation": "jab", "events": []},
        "action.ranged": {"animation": "shoot", "events": []},
        "action.melee.forward": {"animation": "attack_side", "events": []},
        "action.smash.forward": {"animation": "smash_forward", "events": []},
        "action.capture.grab": {"animation": "grab", "events": []},
        "action.capture.pummel": {"animation": "pummel", "events": []},
        "action.capture.throw_forward": {"animation": "throw_forward", "events": []},
        "action.capture.throw_back": {"animation": "throw_back", "events": []},
        "action.capture.throw_up": {"animation": "throw_up", "events": []},
        "action.capture.throw_down": {"animation": "throw_down", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
    },
    "tags": [
        "bestial",
        "polygonal",
        "projectile_fighter",
        "animation_reference",
        "smash",
        "svg_rigged",
    ],
}


@lru_cache(maxsize=1)
def _prepared():
    return CharacterMotionBinding.load(MOTION_PATH).load_prepared()


@lru_cache(maxsize=1)
def _doc() -> RigDocument:
    # RigDocument is a temporary renderer projection.  The editable sources are
    # the SVG static rig plus the shared Ambition pose/clip library selected by
    # this character binding.
    return _prepared().to_rig_document()


@lru_cache(maxsize=1)
def _publication_padding() -> tuple[int, int, int, int]:
    """Minimal overscan for the exact poses published by this sheet.

    The rig's logical frame is an authoring coordinate system, not a clipping
    promise.  Measure the publication samples cheaply at 1x, then render the
    real sheet with enough transparent room to preserve every transformed part.
    """
    prepared = _prepared()
    samples = []
    for animation, frame_count, _duration_ms in _doc().rows():
        clip = prepared.library.clips[animation]
        for frame_idx in range(frame_count):
            at_s = frame_idx * clip.frame_duration_ms / 1000.0
            samples.append(
                (animation, round(at_s / max(clip.duration_s, 1e-9), 9))
            )
    return _doc().measure_render_padding(samples, margin=4)


def _publication_frame_size() -> tuple[int, int]:
    doc = _doc()
    left, top, right, bottom = _publication_padding()
    render_scale = max(1, int(doc.frame.get("render_scale", 1)))
    return (
        (int(doc.frame["width"]) + left + right) * render_scale,
        (int(doc.frame["height"]) + top + bottom) * render_scale,
    )


def _render_frame(animation: str, frame_idx: int, frame_count: int):
    # The shipped sheet still honors each clip's legacy publication cadence.
    # Authored motion itself is normalized against duration_s, so publication
    # samples are converted from absolute seconds explicitly rather than using
    # RigDocument's generic i/(n-1) one-shot convention.
    clip = _prepared().library.clips[animation]
    if frame_count != clip.frame_count:
        raise ValueError(
            f"{animation}: requested {frame_count} publication frames, source declares {clip.frame_count}"
        )
    at_s = frame_idx * clip.frame_duration_ms / 1000.0
    normalized = round(at_s / max(clip.duration_s, 1e-9), 9)
    return _doc().render_at(
        animation,
        normalized,
        padding=_publication_padding(),
    )


def render(out_dir: str | Path, **opts):
    del opts
    doc = _doc()
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=doc.rows(),
        render_fn=_render_frame,
        out_dir=Path(out_dir),
        frame_size=_publication_frame_size(),
        auto_crop=True,
        crop_margin=4,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning=doc.sprite_tuning or {"collision_scale": 1.8},
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
