"""SVG-part rig for Charley Beagle.

The editable vector art lives in
``data/characters/charley_beagle_svg/charley_beagle_side.svg``. The rig document
owns the FK skeleton, pivots, z-order, and animation clips. This module only
publishes that rig through the normal character sheet and portrait pipelines.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ambition_sprite2d_renderer.authoring.portrait import (
    FaceGuide,
    PortraitClip,
    render_framed_portrait,
    write_portrait_sheet,
)
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

TARGET_NAME = "charley_beagle_svg"
RIG_PATH = (
    Path(__file__).resolve().parent
    / "rigged"
    / TARGET_NAME
    / "charley_beagle_side.rig.json"
)

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_charley_beagle_svg",
        "display_name": "Charley Beagle",
    },
    "authoring_description": {
        "parody_of": "Charles Darwin, Charlie Brown, and Snoopy / the Beagle",
        "core_joke": (
            "A melancholy naturalist beagle who combines Darwin's voyage aboard "
            "the HMS Beagle with Charlie Brown's anxious sincerity and a broad, "
            "instantly readable comic-strip beagle silhouette."
        ),
        "visual_inspirations": [
            "a canine-first anthropomorphic beagle body rather than a thin human with dog details",
            "Darwinian field-naturalist gear: green vest, satchel, notebook, and magnifying glass",
            "a yellow sweater with a black zig-zag band as the restrained Charlie Brown reference",
            "large floppy black ear, white muzzle, worried brow, and compact paws",
        ],
        "rigging_notes": [
            "The SVG is the editable art authority; the rig JSON owns pivots and animation.",
            "Every limb segment overlaps its neighbor around the shared joint pivot, and the pelvis yoke and torso cover the shoulder and hip roots.",
            "Do not add floor ellipses, drop shadows, SVG filters, gradients, or detached decorative limbs.",
            "The head, muzzle, ear, eye, cap, and chin tuft stay in one rigid head part so facial construction cannot separate during animation.",
        ],
        "reference_hooks": [
            "natural selection and adaptation",
            "field observation and specimen notes",
            "HMS Beagle wordplay",
            "worried underdog energy",
        ],
    },
    "gameplay_description": {
        "role": "mobile naturalist / adaptive mid-range trickster",
        "combat_identity": [
            "studies an opponent before committing",
            "uses notebook and magnifier poses as setup language",
            "adapts into a brief empowered state and follows with a pounce",
        ],
        "signature_moves": [
            "Field Notes: observe and mark an enemy",
            "Selective Pressure: trigger an adaptation aura",
            "Voyage of the Beagle: a committed forward pounce",
        ],
        "authoring_notes": [
            "The initial clips are designed to prove the connected SVG rig and can be retimed in the rig editor.",
            "A later pass could add finch, fossil, or specimen props without baking them into the body SVG.",
            "His emotional read should stay gentle, worried, and observant rather than smug.",
        ],
    },
    "dialogue_hints": {
        "suggested_barks": [
            "I have made a note of that.",
            "Curious. Very curious.",
            "Adapt, please adapt!",
            "That seems evolutionarily unsound.",
            "Oh, good grief... fascinating.",
            "Natural selection at work.",
        ],
        "fallback_dialogue": [
            "I do not enjoy conflict, but I do find it highly instructive.",
            "One notices more by watching quietly than by boasting loudly.",
            "Nature is patient. I am trying to be.",
            "I had hoped for a peaceful walk, yet here we are collecting data.",
        ],
    },
    "body": {
        "body_plan": "AnthroCanidBiped",
        "body_kind": "Standard",
        "mass_class": "Light",
        "traits": [
            "story",
            "combatant",
            "scientist_parody",
            "animal_person",
            "dog",
            "beagle",
            "naturalist",
            "svg_rigged",
        ],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": True,
            "climb": None,
            "crawl": None,
            "fly": None,
            "swim": None,
            "use_lifts": True,
            "door_access": ["public"],
        },
        "interactions": {
            "talk": True,
            "trade": None,
            "carry": True,
            "open_doors": ["public"],
        },
    },
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "peaceful"},
    "visual": {
        "default_pose": "idle",
        "portrait_style": "dialog_closeup",
        "portrait_source": TARGET_NAME,
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "action.ability.primary": {
            "animation": "observe",
            "events": [
                {"t": 0.34, "event": "study_start", "source": "charley_beagle_svg.observe"},
                {"t": 0.68, "event": "study_complete", "source": "charley_beagle_svg.observe"},
            ],
        },
        "action.ability.secondary": {
            "animation": "adapt",
            "events": [
                {"t": 0.50, "event": "adaptation_trigger", "source": "charley_beagle_svg.adapt"},
            ],
        },
        "action.melee.primary": {
            "animation": "pounce",
            "events": [
                {"t": 0.42, "event": "hitbox_active_start", "source": "charley_beagle_svg.pounce"},
                {"t": 0.76, "event": "hitbox_active_end", "source": "charley_beagle_svg.pounce"},
            ],
        },
        "damage.hit": {"animation": "hurt", "events": []},
        "lifecycle.death": {"animation": "death", "events": []},
    },
    "sockets": {
        "head": {"source": "charley_beagle_svg.rig", "point": {"x": 72.0, "y": 40.0}},
        "chest": {"source": "charley_beagle_svg.rig", "point": {"x": 64.0, "y": 62.0}},
        "hand_l": {"source": "charley_beagle_svg.rig", "point": {"x": 58.0, "y": 80.0}},
        "hand_r": {"source": "charley_beagle_svg.rig", "point": {"x": 84.0, "y": 76.0}},
        "speech_bubble": {"source": "charley_beagle_svg.rig", "point": {"x": 74.0, "y": 8.0}},
        "item_anchor": {"source": "charley_beagle_svg.rig", "point": {"x": 88.0, "y": 76.0}},
    },
    "tags": [
        "story",
        "combatant",
        "scientist_parody",
        "animal_person",
        "dog",
        "beagle",
        "naturalist",
        "svg_rigged",
        "charles_darwin_parody",
        "charlie_brown_reference",
        "snoopy_reference",
    ],
}


@lru_cache(maxsize=1)
def _doc() -> RigDocument:
    return RigDocument.load(RIG_PATH)


def _render_frame(animation: str, frame_idx: int, frame_count: int):
    return _doc().render_frame(animation, frame_idx, frame_count)


def render_portraits(out_dir: str | Path, **opts):
    del opts
    doc = _doc()

    def portrait_frame(animation: str, frame_idx: int, frame_count: int):
        source = doc.render_at(
            animation,
            doc.frame_time(animation, frame_idx, frame_count),
            supersample=4,
            scale=3,
        )
        face = FaceGuide(
            center_x=74.0,
            center_y=39.0,
            width=54.0,
            height=48.0,
            source_width=128.0,
            source_height=128.0,
        )
        return render_framed_portrait(source, face, view_width=72.0, center_y=47.0)

    clips = {
        "default": PortraitClip.still(portrait_frame("idle", 2, 8)),
        "talking": PortraitClip(
            tuple(portrait_frame("talk", i, 6) for i in (0, 2, 4)),
            duration_ms=112,
            looping=True,
        ),
        "observing": PortraitClip(
            tuple(portrait_frame("observe", i, 8) for i in (1, 3, 5, 7)),
            duration_ms=92,
            looping=True,
        ),
        "adapted": PortraitClip.still(portrait_frame("adapt", 4, 8)),
    }
    return write_portrait_sheet(TARGET_NAME, clips, Path(out_dir))


def render(out_dir: str | Path, **opts):
    del opts
    doc = _doc()
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=doc.rows(),
        render_fn=_render_frame,
        out_dir=Path(out_dir),
        frame_size=(128, 128),
        auto_crop=True,
        crop_margin=4,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning=doc.sprite_tuning or {"collision_scale": 1.5},
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


__all__ = ["ACTOR_METADATA", "render", "render_portraits"]
