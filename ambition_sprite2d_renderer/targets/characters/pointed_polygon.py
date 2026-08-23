"""SVG-rigged Pointed Polygon humanoid.

This target is deliberately both a playable fighter and an animation reference.
The SVG owns simple faceted body parts and static rig geometry; a shared,
editor-neutral motion library owns the broad conservative humanoid pose vocabulary.  Future humanoid characters can copy or inspect these
poses before adding anatomy-specific exaggeration.

The sword is integral to this archetype and follows the near hand.  Do not add
unrelated held props or shadows to the base character.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from ambition_sprite2d_renderer.authoring.motion_ir import CharacterMotionBinding
from ambition_sprite2d_renderer.authoring import swing_effects
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

TARGET_NAME = "pointed_polygon"
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
        "display_name": "Pointed Polygon",
    },
    "authoring_description": {
        "concept": (
            "A 2D faceted humanoid inspired by the anonymous Fighting Polygon "
            "Team idea: a deliberately simple body whose readable joint and "
            "silhouette poses can serve as a safe animation reference for more "
            "bespoke humanoid characters. This first archetype is a sword user."
        ),
        "visual_language": [
            "large flat polygon facets instead of anatomical surface detail",
            "indigo/purple body planes with brighter near-side facets",
            "no face identity beyond a small reflective head facet",
            "a simple polygon sword permanently attached to the sword archetype",
            "no drop shadow and no unrelated held props",
        ],
        "rigging_notes": [
            "The SVG owns artwork and static rig geometry; editor-neutral motion JSON owns reusable poses and clips.",
            "Sword and brawler share the same backend-neutral humanoid motion library; character artwork binds to it independently.",
            "Near/far names in the SVG are character-relative layers, not camera-centric gameplay semantics.",
            "This sword variant is the reference for armed humanoids; a later brawler variant should share the same skeleton vocabulary without the sword part.",
        ],
    },
    "gameplay_description": {
        "role": "fundamental sword humanoid / animation reference fighter",
        "combat_identity": [
            "medium-weight fundamentals fighter with straightforward sword spacing",
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
            "sword_fighter",
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
        "canonical_source": "data/characters/pointed_polygon/pointed_polygon.svg",
        "pose_reference": list(SAFE_POSE_REFERENCE),
    },
    "actions": {
        "default_preset": TARGET_NAME,
        "archetype": "sword_humanoid",
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
        "sword_fighter",
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
    pose = _doc().measure_render_padding(samples, margin=4)
    # ⛔ AND THE EFFECT REACHES FURTHER THAN THE POSE. The ribbon is drawn from
    # where the blade WAS, so it extends past the sword's own envelope — measure
    # the poses alone and the publish clips 91 frames of trail at the frame edge,
    # which is what the sheet warns about and what nothing downstream can undo.
    return tuple(max(a, b) for a, b in zip(pose, _effect_padding(pose)))


def _effect_padding(pose_padding) -> tuple[int, int, int, int]:
    """Overscan the authored EFFECT needs, on top of the poses'.

    A cheap 1x probe on a generous canvas, the same shape as
    `measure_render_padding`'s: composite each specced clip, measure where the
    light actually lands, and report the smallest overscan that keeps it.
    """
    doc = _doc()
    prepared = _prepared()
    width, height = int(doc.frame["width"]), int(doc.frame["height"])
    probe = max(width, height)
    required = [0, 0, 0, 0]
    for animation, frame_count, _duration_ms in doc.rows():
        spec = _spec_for(animation)
        if not spec:
            continue
        clip = prepared.library.clips[animation]
        frames = []
        for frame_idx in range(frame_count):
            at_s = frame_idx * clip.frame_duration_ms / 1000.0
            frames.append(
                doc.render_at(
                    animation,
                    round(at_s / max(clip.duration_s, 1e-9), 9),
                    supersample=1,
                    scale=1,
                    padding=probe,
                )
            )
        for image in swing_effects.composite_authored_effect(frames, spec):
            bbox = image.getchannel("A").getbbox()
            if bbox is None:
                continue
            required[0] = max(required[0], probe - bbox[0])
            required[1] = max(required[1], probe - bbox[1])
            required[2] = max(required[2], bbox[2] - (probe + width))
            required[3] = max(required[3], bbox[3] - (probe + height))
    return tuple(max(0, value) + 4 for value in required)


def _publication_frame_size() -> tuple[int, int]:
    doc = _doc()
    left, top, right, bottom = _publication_padding()
    render_scale = max(1, int(doc.frame.get("render_scale", 1)))
    return (
        (int(doc.frame["width"]) + left + right) * render_scale,
        (int(doc.frame["height"]) + top + bottom) * render_scale,
    )


@lru_cache(maxsize=1)
def _spec_dir() -> Path:
    """Where the swing specs live — asked of the LIBRARY this character binds.

    Not restated from a path constant: the specs sit beside the clips they
    describe, and the binding already knows which library that is.
    """
    return Path(_prepared().library.path).parent / "specs"


def _spec_for(animation: str) -> dict | None:
    """The authored swing spec for one clip, or `None` for a clip with no swing.

    The SAME file the review tool reads, so what ships is what was reviewed.
    """
    path = _spec_dir() / f"{animation}.spec.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


@lru_cache(maxsize=None)
def _clip_frames(animation: str, frame_count: int) -> tuple:
    """Every frame of one clip, with its authored effect composited on.

    ⛔ **cached per CLIP, not per frame, because a ribbon is not a frame-local
    fact.** The trail a blade leaves on frame 6 is drawn from where the blade
    was on frames 3-5, so the effect cannot be composited by a `render_fn` that
    only ever sees one frame — which is exactly why the published sheet carried
    no ribbons at all while every review artifact showed them.
    """
    raw = [_raw_frame(animation, i, frame_count) for i in range(frame_count)]
    spec = _spec_for(animation)
    if not spec:
        return tuple(raw)
    return tuple(swing_effects.composite_authored_effect(raw, spec))


def _render_frame(animation: str, frame_idx: int, frame_count: int):
    return _clip_frames(animation, frame_count)[frame_idx]


def _raw_frame(animation: str, frame_idx: int, frame_count: int):
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
        authored_faces_left=doc.authored_faces_left,
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
