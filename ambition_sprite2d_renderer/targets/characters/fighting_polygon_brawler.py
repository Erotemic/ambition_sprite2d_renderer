"""SVG-rigged Fighting Polygon brawler humanoid.

This target is deliberately both a playable fighter and an animation reference.
The SVG owns simple faceted body parts and static rig geometry; a shared,
editor-neutral motion library owns the broad conservative humanoid pose vocabulary.  Future humanoid characters can copy or inspect these
poses before adding anatomy-specific exaggeration.

This archetype is intentionally unarmed. Do not add held props or shadows to the base character.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ambition_sprite2d_renderer.authoring.motion_ir import CharacterMotionBinding
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

TARGET_NAME = "fighting_polygon_brawler"
MOTION_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "characters"
    / TARGET_NAME
    / f"{TARGET_NAME}.motion.json"
)

# A compact vocabulary to show first when using this target as a humanoid pose
# reference.  The rig itself publishes the full fighter vocabulary (136 clips).
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
    "taunt",
    "victory_hold",
    "loss",
)

ACTOR_METADATA = {
    "actor": {
        "character_id": TARGET_NAME,
        "display_name": "Fighting Polygon Brawler",
    },
    "authoring_description": {
        "concept": (
            "A 2D faceted humanoid inspired by the anonymous Fighting Polygon "
            "Team idea: a deliberately simple body whose readable joint and "
            "silhouette poses can serve as a safe animation reference for more "
            "bespoke humanoid characters. This archetype is the unarmed brawler reference."
        ),
        "visual_language": [
            "large flat polygon facets instead of anatomical surface detail",
            "warm crimson body planes with amber highlights on the near-side facets",
            "no face identity beyond a small reflective head facet",
            "large polygon fists with no integral held weapon",
            "no drop shadow and no unrelated held props",
        ],
        "rigging_notes": [
            "The SVG owns artwork and static rig geometry; editor-neutral motion JSON owns reusable poses and clips.",
            "Sword and brawler share the same backend-neutral humanoid motion library; character artwork binds to it independently.",
            "Near/far names in the SVG are character-relative layers, not camera-centric gameplay semantics.",
            "This brawler variant is the reference for unarmed humanoids and intentionally shares the sword rig's skeleton vocabulary.",
        ],
    },
    "gameplay_description": {
        "role": "fundamental brawler humanoid / animation reference fighter",
        "combat_identity": [
            "medium-weight close-range fundamentals fighter with clear punch, kick, uppercut, and throw silhouettes",
            "complete grounded, aerial, special, defensive, capture, pummel and throw vocabulary",
            "intentionally legible timings and silhouettes rather than character-specific visual tricks",
        ],
        "authoring_notes": [
            "Use this fighter when a new humanoid move needs a safe first pose before bespoke posing.",
            "The gameplay repertoire lives in ambition_content; the rig is reusable pose reference art.",
        ],
    },
    "dialogue_hints": {
        "suggested_barks": [
            "POSE ACCEPTED.",
            "EDGE ALIGNED.",
            "REFERENCE STANCE.",
            "FACET LOCKED.",
        ],
        "fallback_dialogue": [
            "A simple pose is easier to trust.",
            "Start with the silhouette. Add personality later.",
            "Every complicated fighter begins as a few good angles.",
        ],
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": [
            "humanoid",
            "polygonal",
            "brawler",
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
        "canonical_source": "data/characters/fighting_polygon_brawler/fighting_polygon_brawler.svg",
        "pose_reference": list(SAFE_POSE_REFERENCE),
    },
    "actions": {
        "default_preset": TARGET_NAME,
        "archetype": "brawler_humanoid",
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "action.melee.primary": {"animation": "jab", "events": []},
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
        "humanoid",
        "polygonal",
        "brawler",
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
    return _doc().render_at(animation, normalized)


def render(out_dir: str | Path, **opts):
    del opts
    doc = _doc()
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=doc.rows(),
        render_fn=_render_frame,
        out_dir=Path(out_dir),
        frame_size=(int(doc.frame["width"]), int(doc.frame["height"])),
        auto_crop=True,
        crop_margin=4,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning=doc.sprite_tuning or {"collision_scale": 1.8},
        trim=False,
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
