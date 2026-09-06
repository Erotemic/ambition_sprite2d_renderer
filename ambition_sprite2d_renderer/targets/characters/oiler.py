"""Oiler's Euler-inspired direct-SVG multiview bone-rig target.

The editable art lives in ``data/characters/oiler/oiler-multiview.svg``.  Three
small rig documents bind its front, three-quarter and side views to the common
FK/IK skeleton.  This module only composes those view rigs into Oiler's runtime
sheet; it contains no character geometry and no per-frame limb placement.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple

from ...authoring.portrait import (
    FaceGuide,
    PortraitClip,
    render_framed_portrait,
    write_portrait_sheet,
)
from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet

TARGET_NAME = "oiler"
RIG_DIR = Path(__file__).resolve().parent / "rigged" / "oiler"
FRAME_SIZE = (256, 256)
# The four the Hall needs, then the eight a fight needs.  A platform-fighter
# move names the row it wants and settles for ``attack_side`` -> ``attack`` ->
# ``slash`` -> ``idle``, so before the second group existed every swing in
# Oiler's repertoire drew his STANDING POSE -- and cost the gameplay nothing to
# do it, which is why it stayed broken.  See
# ``game/ambition_content/src/oiler_moveset.rs``; a Rust test asserts every move
# in that table names a row published here.
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 120),
    ("walk", 8, 100),
    ("talk", 6, 100),
    ("interact", 6, 105),
    ("attack_side", 6, 70),
    ("attack_up", 6, 66),
    ("attack_down", 6, 70),
    ("smash_forward", 8, 64),
    ("special", 8, 72),
    ("hit", 5, 80),
    ("death", 6, 90),
    ("taunt", 8, 100),
]

# Animation -> (view document, clip inside that document).
CLIP_SOURCE: Dict[str, Tuple[str, str]] = {
    "idle": ("oiler_three_quarter.rig.json", "idle"),
    "walk": ("oiler_side.rig.json", "walk"),
    "talk": ("oiler_front.rig.json", "talk"),
    "interact": ("oiler_three_quarter.rig.json", "interact"),
    # Every fight row is SIDE view: a platform fighter is a side-on game, and it
    # is the silhouette his walk already reads in.
    "attack_side": ("oiler_side.rig.json", "attack_side"),
    "attack_up": ("oiler_side.rig.json", "attack_up"),
    "attack_down": ("oiler_side.rig.json", "attack_down"),
    "smash_forward": ("oiler_side.rig.json", "smash_forward"),
    "special": ("oiler_side.rig.json", "special"),
    "hit": ("oiler_side.rig.json", "hit"),
    "death": ("oiler_side.rig.json", "death"),
    "taunt": ("oiler_side.rig.json", "taunt"),
}

ACTOR_METADATA = {
    "actor": {"character_id": "npc_oiler", "display_name": "Oiler"},
    "visual": {"default_pose": "idle"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": ["story", "humanoid", "mechanic", "inventor", "scholar"],
        "locomotion_hint": "Walk",
    },
    "capabilities": {
        "traversal": {
            "walk": True,
            "jump": None,
            "climb": None,
            "fly": None,
            "swim": None,
            "crawl": None,
            "use_lifts": True,
            "door_access": ["public"],
        },
        "interactions": {
            "talk": True,
            "trade": None,
            "carry": None,
            "open_doors": ["public"],
        },
    },
    "brain": {"default_preset": "patrol_peaceful"},
    # Hall behavior is policy (`patrol_peaceful`); attack availability is a
    # capability, so the catalog separately names `striker_swipe`.
    "actions": {"default_preset": "striker_swipe"},
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "action.attack.side": {"animation": "attack_side", "events": []},
        "action.attack.up": {"animation": "attack_up", "events": []},
        "action.attack.down": {"animation": "attack_down", "events": []},
        "action.attack.smash": {"animation": "smash_forward", "events": []},
        "action.attack.special": {"animation": "special", "events": []},
        "reaction.hit": {"animation": "hit", "events": []},
        "reaction.death": {"animation": "death", "events": []},
        "emote.taunt": {"animation": "taunt", "events": []},
    },
    "sockets": {
        "head": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 64.0, "y": 24.0},
        },
        "chest": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 64.0, "y": 54.0},
        },
        "hand_l": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 48.0, "y": 64.0},
        },
        "hand_r": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 80.0, "y": 64.0},
        },
        "speech_bubble": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 64.0, "y": 8.0},
        },
        "tool_grip": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 82.0, "y": 68.0},
        },
    },
    "tags": ["story", "humanoid", "mechanic", "inventor", "scholar"],
}


ACTOR_METADATA.update(
    {
        "authoring_description": (
            "Oiler is a practical mechanic parody of Leonhard Euler. His name reflects an English "
            "pronunciation of Euler, while his workshop, Kernel, formulas, and broad competence turn "
            "one of mathematics' most prolific figures into the person who keeps the game's machinery "
            "moving."
        ),
        "gameplay_description": (
            "Use as a mechanic, early mentor, systems guide, or versatile playable engineer. He "
            "should solve problems with tools and compact identities, value motion over polish, and "
            "understand nearly every subsystem without acting like a ceremonial professor."
        ),
    }
)
ACTOR_METADATA.setdefault("dialogue_hints", {}).setdefault(
    "barks",
    [
        'I am a man with tools and poor boundaries.',
        'Small things are the ones that take the big things down.',
        "You're not scrap until you stop moving.",
    ],
)


@lru_cache(maxsize=3)
def _load_doc(filename: str) -> RigDocument:
    path = RIG_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"missing Oiler rig {path}; rebuild from the SVG with "
            "`uv run python scripts/build_oiler_rig.py build`"
        )
    return RigDocument.load(path)


def _render_frame(animation: str, frame_idx: int, frame_count: int):
    filename, clip = CLIP_SOURCE[animation]
    return _load_doc(filename).render_frame(clip, frame_idx, frame_count)


def render_portraits(out_dir: str | Path, **opts):
    """Publish Oiler's close-up expressions directly from the scalable SVG rig."""
    del opts

    def portrait_frame(animation: str, frame_idx: int, frame_count: int):
        filename, clip = CLIP_SOURCE[animation]
        doc = _load_doc(filename)
        source = doc.render_at(
            clip,
            doc.frame_time(clip, frame_idx, frame_count),
            scale=4,
        )
        face = FaceGuide(
            center_x=64.0,
            center_y=24.0,
            width=27.0,
            height=31.0,
            source_width=float(doc.frame["width"]),
            source_height=float(doc.frame["height"]),
        )
        return render_framed_portrait(source, face)

    clips = {
        "default": PortraitClip.loop(
            tuple(portrait_frame("idle", frame, 8) for frame in range(8)),
            duration_ms=148,
        ),
        # The pose a UI BOX draws. Frame 1 of the same idle — the still
        # this target published before its default began to move.
        "portrait": PortraitClip.still(portrait_frame("idle", 1, 8)),
        "talking": PortraitClip(
            tuple(portrait_frame("talk", frame, 6) for frame in range(6)),
            duration_ms=100,
            looping=True,
        ),
        "inspecting": PortraitClip.still(portrait_frame("interact", 4, 6)),
    }
    return write_portrait_sheet(
        TARGET_NAME, clips, Path(out_dir), still_clip="portrait"
    )


def render(out_dir: str | Path, **opts):
    del opts
    outputs = build_sheet(
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=_render_frame,
        out_dir=Path(out_dir),
        frame_size=FRAME_SIZE,
        auto_crop=True,
        crop_margin=4,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning={"collision_scale": 1.72},
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
