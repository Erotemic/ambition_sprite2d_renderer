"""SVG-rigged Author: the game's author, drawn into his own roster.

An easter-egg fighter, not a reference rig. He is an *armed* humanoid and
therefore follows the Pointed Polygon sword template: one rigid sword part
carried by ``near_arm_hand``, drawn along that bone's axis so every authored
swing in the shared humanoid motion library points the blade where the hand
points. The sword is integral to the archetype — do not add unrelated held
props or shadows.

His swings publish authored ribbons and hit volumes from the same shared specs
the polygon swings use — but they do NOT let `swing_effects` find the blade.
That helper separates blade from anatomy by luminance (``BLADE_LUM``), which
holds for a monochrome polygon and fails here: his skin (#fdcda0) and pale
sneakers are over the threshold, and measured, the inferred "blade" axis ran
from his glasses to his shoes. The rig already knows the answer — the sword is
its own part — so the axis is measured on a sword-only render and handed to the
effect instead of guessed at.
"""

from __future__ import annotations

import copy
import json
from functools import lru_cache
from pathlib import Path

from ambition_sprite2d_renderer.authoring.motion_ir import CharacterMotionBinding
from ambition_sprite2d_renderer.authoring import swing_effects
from ambition_sprite2d_renderer.authoring.rig_gameplay_body import gameplay_body_metrics
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

TARGET_NAME = "author"
MOTION_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "characters"
    / TARGET_NAME
    / f"{TARGET_NAME}.motion.json"
)

# A compact vocabulary to show first when reviewing this fighter. The rig itself
# publishes the full fighter vocabulary (136 clips).
POSE_HIGHLIGHTS = (
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
        "display_name": "The Author",
    },
    "authoring_description": {
        "concept": (
            "The person writing the game, standing in it: red hair, beard, "
            "glasses, work shirt and jeans, holding a plain steel arming sword "
            "he has no business carrying. An easter egg — he is meant to be "
            "found, not advertised."
        ),
        "visual_language": [
            "ordinary contemporary clothing rather than a fighting costume",
            "flat cel shading with a single dark outline, no rendered volume",
            "warm red hair and beard against a cool navy shirt and denim",
            "one plain steel sword: bright fuller, brass guard and pommel, wrapped grip",
            "no drop shadow and no unrelated held props",
        ],
        "rigging_notes": [
            "The SVG owns artwork and static rig geometry; editor-neutral motion JSON owns reusable poses and clips.",
            "He binds to the same humanoid motion library as the polygon reference fighters, so his moveset is theirs until he earns bespoke posing.",
            "Near/far names in the SVG are character-relative layers, not camera-centric gameplay semantics.",
            "The sword is bound to near_arm_hand and drawn along that bone's axis; a swing authored for the polygon sword reads correctly here without retargeting.",
        ],
    },
    "gameplay_description": {
        "role": "easter-egg sword humanoid",
        "combat_identity": [
            "medium-weight fundamentals fighter with straightforward sword spacing",
            "complete grounded, aerial, special, defensive, capture, pummel and throw vocabulary",
            "shares the sword archetype's timings; his identity is who he is, not how he swings",
        ],
        "authoring_notes": [
            "Unlockable/hidden roster material — nothing should depend on him being selectable.",
            "The gameplay repertoire lives in ambition_content; this target publishes art and rig only.",
        ],
    },
    "dialogue_hints": {
        "suggested_barks": [
            "That's not what I wrote.",
            "Committed.",
            "Works on my machine.",
            "Ship it.",
        ],
        "fallback_dialogue": [
            "I built the room. Doesn't mean I know the way out.",
            "Every fight in here started as a line I typed.",
            "If this feels unfair, remember whose fault it is.",
        ],
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": [
            "humanoid",
            "sword_fighter",
            "easter_egg",
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
        "canonical_source": "data/characters/author/author.svg",
        "pose_reference": list(POSE_HIGHLIGHTS),
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
        "sword_fighter",
        "easter_egg",
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
def _sword_doc() -> RigDocument:
    """The same rig with only the sword painted.

    This is how the blade gets identified without a brightness guess: on a frame
    that holds nothing but the sword, the steel is the only thing over
    ``BLADE_LUM`` — the brass guard, the wrapped grip and the pommel all fall
    under it — so `blade_axis` returns exactly the blade, base-toward-grip, for
    whatever pose the clip is in.
    """
    data = copy.deepcopy(_doc().data)
    data["parts"] = [part for part in data["parts"] if part["name"] == "sword"]
    if not data["parts"]:
        raise ValueError(f"{TARGET_NAME}: rig publishes no sword part to swing")
    return RigDocument(data, source_path=_doc().source_path)


def _sample_times(animation: str, frame_count: int) -> list[float]:
    clip = _prepared().library.clips[animation]
    return [
        round(frame_idx * clip.frame_duration_ms / 1000.0 / max(clip.duration_s, 1e-9), 9)
        for frame_idx in range(frame_count)
    ]


def _blade_axes(animation: str, frame_count: int, padding):
    """(base, tip) of the blade per frame, in the pixels of `padding`'s frame.

    Measured at the SAME padding as the frames the effect will be drawn on: an
    axis is a coordinate, and a coordinate in another frame is a wrong answer.
    """
    doc = _sword_doc()
    return [
        swing_effects.blade_axis(doc.render_at(animation, t, supersample=1, padding=padding))
        for t in _sample_times(animation, frame_count)
    ]


@lru_cache(maxsize=1)
def _publication_padding() -> tuple[int, int, int, int]:
    """Minimal overscan for the exact poses published by this sheet.

    The rig's logical frame is an authoring coordinate system, not a clipping
    promise.  Measure the publication samples cheaply at 1x, then render the
    real sheet with enough transparent room to preserve every transformed part —
    a swung sword reaches well past the frame the body needs.
    """
    prepared = _prepared()
    samples = []
    for animation, frame_count, _duration_ms in _doc().rows():
        clip = prepared.library.clips[animation]
        for frame_idx in range(frame_count):
            at_s = frame_idx * clip.frame_duration_ms / 1000.0
            samples.append((animation, round(at_s / max(clip.duration_s, 1e-9), 9)))
    pose = _doc().measure_render_padding(samples, margin=4)
    # ⛔ AND THE EFFECT REACHES FURTHER THAN THE POSE. The ribbon is drawn from
    # where the blade WAS, so it extends past the sword's own envelope; measure
    # the poses alone and the publish clips the trail at the frame edge.
    return tuple(max(a, b) for a, b in zip(pose, _effect_padding()))


def _effect_padding() -> tuple[int, int, int, int]:
    """Overscan the authored EFFECT needs, on top of the poses'.

    A cheap 1x probe on a generous canvas: composite each specced clip, measure
    where the light actually lands, and report the smallest overscan that keeps
    it.
    """
    doc = _doc()
    width, height = int(doc.frame["width"]), int(doc.frame["height"])
    probe = max(width, height)
    required = [0, 0, 0, 0]
    for animation, frame_count, _duration_ms in doc.rows():
        spec = _spec_for(animation)
        if not spec:
            continue
        frames = [
            doc.render_at(animation, t, supersample=1, scale=1, padding=probe)
            for t in _sample_times(animation, frame_count)
        ]
        axes = _blade_axes(animation, frame_count, probe)
        for image in swing_effects.composite_authored_effect(frames, spec, axes=axes):
            bbox = image.getchannel("A").getbbox()
            if bbox is None:
                continue
            required[0] = max(required[0], probe - bbox[0])
            required[1] = max(required[1], probe - bbox[1])
            required[2] = max(required[2], bbox[2] - (probe + width))
            required[3] = max(required[3], bbox[3] - (probe + height))
    return tuple(max(0, value) + 4 for value in required)


@lru_cache(maxsize=1)
def _spec_dir() -> Path:
    """Where the swing specs live — asked of the LIBRARY this character binds.

    Not restated from a path constant: the specs sit beside the clips they
    describe, and the binding already knows which library that is.
    """
    return Path(_prepared().library.path).parent / "specs"


#: His blade is steel, not the polygons' amethyst. Timing, window and reach stay
#: the library's — the swing is shared, the light it throws is his.
TRAIL_TINT = {
    "body_rgb": [104, 184, 255],
    "core_rgb": [238, 250, 255],
}


def _spec_for(animation: str) -> dict | None:
    """The authored swing spec for one clip, or `None` for a clip with no swing.

    The SAME file the review tool reads, so what ships is what was reviewed —
    recoloured, because a trail colour is the character's and the swing is not.
    """
    path = _spec_dir() / f"{animation}.spec.json"
    if not path.exists():
        return None
    spec = json.loads(path.read_text())
    for effect in ("trail", "poke"):
        if isinstance(spec.get(effect), dict):
            spec[effect].update(TRAIL_TINT)
    return spec


@lru_cache(maxsize=None)
def _clip_frames(animation: str, frame_count: int) -> tuple:
    """Every frame of one clip, with its authored effect composited on.

    ⛔ **cached per CLIP, not per frame, because a ribbon is not a frame-local
    fact.** The trail a blade leaves on frame 6 is drawn from where the blade
    was on frames 3-5, so the effect cannot be composited by a `render_fn` that
    only ever sees one frame.
    """
    raw = [_raw_frame(animation, i, frame_count) for i in range(frame_count)]
    spec = _spec_for(animation)
    if not spec:
        return tuple(raw)
    axes = _blade_axes(animation, frame_count, _publication_padding())
    return tuple(swing_effects.composite_authored_effect(raw, spec, axes=axes))


@lru_cache(maxsize=1)
def _attack_hitboxes() -> dict:
    """The authored hit volume for every swing that has a spec.

    `manifest_attack_hitbox_world` prefers an authored convex `poly` over a
    coarse bbox precisely so a blade arc can hit in the shape it was drawn in.
    Derived from the same rig-identified axes as the ribbon, so the volume and
    the light a player sees are one claim.
    """
    out = {}
    padding = _publication_padding()
    for animation, frame_count, _duration_ms in _doc().rows():
        spec = _spec_for(animation)
        if not spec:
            continue
        raw = [_raw_frame(animation, i, frame_count) for i in range(frame_count)]
        axes = _blade_axes(animation, frame_count, padding)
        poly = swing_effects.authored_hit_volume(raw, spec, axes=axes)
        if poly:
            out[animation] = {"poly": poly}
    return out


def _publication_frame_size() -> tuple[int, int]:
    doc = _doc()
    left, top, right, bottom = _publication_padding()
    render_scale = max(1, int(doc.frame.get("render_scale", 1)))
    return (
        (int(doc.frame["width"]) + left + right) * render_scale,
        (int(doc.frame["height"]) + top + bottom) * render_scale,
    )


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
    return _doc().render_at(animation, normalized, padding=_publication_padding())


def _body_metrics(fw: int, fh: int):
    """His gameplay body: the TRUNK, crown of the head to the feet.

    Without this the box is the alpha bbox of the sheet's FIRST FRAME, and a rig
    publishes its rows alphabetically — so it would be `aim`, sword up and arm
    extended, and he would collide with the world using his aiming pose.
    """
    del fw, fh  # the published frame is `_publication_frame_size()`, asked below
    metrics = gameplay_body_metrics(
        _doc(),
        padding=_publication_padding(),
        frame_size=_publication_frame_size(),
    )
    if metrics is None:
        raise ValueError(f"{TARGET_NAME}: no trunk parts to measure a body from")
    return metrics


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
        body_metrics_fn=_body_metrics,
        # His rows are mapped so the swings can carry their volumes. `authored`,
        # not `art`: the measured per-pose road would hand every attack a body
        # the size of its own ribbon.
        animation_key_map={name: name for name, _f, _d in doc.rows()},
        attack_hitboxes=_attack_hitboxes(),
        pose_bodies="authored",
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
