"""Oiler's Euler-inspired direct-SVG multiview bone-rig target.

The art is drawn by ``scripts/svg_art/oiler_art.py`` into
``data/characters/oiler/oiler-multiview.svg``; five rig documents bind its
views (front, three-quarter and side, and the three-quarter and side of his
other side) to the common FK/IK skeleton.  This module only composes those
view rigs into Oiler's runtime sheet; it contains no character geometry and no
per-frame limb placement.

Oiler is ASYMMETRIC (his right eye fails), so the game must not flip him to
face left. Every row has a ``<row>~mirrored`` twin (``SheetRow::mirror_of``),
drawn unflipped when he faces left: the three-quarter and side rows from his
left-side views, mirrored here; the front rows as they are, since from the
front he is the same picture whichever way he faces.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple

from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.portrait import (
    FaceGuide,
    PortraitClip,
    render_framed_portrait,
    write_portrait_sheet,
)
from ...authoring import rigdoc
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
MOVE_ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 120),
    ("walk", 8, 100),
    ("talk", 6, 100),
    ("interact", 6, 105),
    ("attack_side", 8, 53),
    ("attack_up", 8, 53),
    ("attack_down", 8, 50),
    ("smash_forward", 10, 70),
    ("special", 8, 72),
    # The rest of a Smash table: a row per move, struck on the frames its move
    # is live (`scripts/build_oiler_rig.py` SMASH_ROW_WINDOWS).
    ("jab", 8, 40),
    ("dash_attack", 10, 42),
    ("smash_up", 10, 67),
    ("smash_down", 10, 68),
    ("air_neutral", 8, 49),
    ("air_forward", 8, 54),
    ("air_back", 8, 56),
    ("air_up", 8, 49),
    ("air_down", 8, 61),
    ("convergence", 12, 42),
    ("special_side", 10, 66),
    ("special_up", 12, 100),
    ("special_down", 10, 48),
    ("hit", 5, 80),
    ("death", 6, 90),
    ("taunt", 8, 100),
]
#: The rest of a fighter's body language, in the vocabulary's names
#: (``data/fighter_motion_vocabulary.yaml``): movement, reactions, defence,
#: ledge and grab. Side view; authored in ``scripts/oiler_fighter_vocabulary.py``,
#: which these frame counts and timings must match.
FIGHTER_ROWS: List[Tuple[str, int, int]] = [
    ("run", 8, 75),
    ("dash", 6, 62),
    ("dash_startup", 4, 50),
    ("skid", 4, 60),
    ("walk_stop", 4, 70),
    ("run_stop", 5, 70),
    ("jump_squat", 3, 40),
    ("jump", 6, 70),
    ("double_jump", 6, 58),
    ("fall", 4, 110),
    ("land_light", 3, 50),
    ("land_hard", 4, 70),
    ("crouch_start", 3, 50),
    ("crouch", 4, 140),
    ("crouch_end", 3, 50),
    ("teeter", 6, 100),
    ("hit_high", 4, 70),
    ("hit_mid", 4, 70),
    ("hit_low", 4, 70),
    ("hit_air", 4, 70),
    ("launch_up", 4, 60),
    ("launch_horizontal", 4, 60),
    ("launch_down", 4, 60),
    ("launch", 4, 60),
    ("meteor", 4, 60),
    ("tumble", 8, 60),
    ("prone_face_up", 4, 160),
    ("prone_face_down", 4, 160),
    ("prone", 4, 160),
    ("knockdown", 6, 70),
    ("getup", 6, 80),
    ("getup_roll", 6, 70),
    ("getup_attack", 6, 60),
    ("tech", 5, 60),
    ("tech_roll", 6, 60),
    ("shield_raise", 3, 40),
    ("block", 4, 120),
    ("shield_hit", 3, 50),
    ("shield_release", 3, 50),
    ("roll", 6, 60),
    ("roll_back", 6, 60),
    ("spot_dodge", 5, 60),
    ("air_dodge", 4, 60),
    ("ledge_catch", 4, 60),
    ("ledge_grab", 4, 140),
    ("ledge_climb", 6, 70),
    ("ledge_getup", 6, 60),
    ("ledge_roll", 6, 60),
    ("ledge_jump", 5, 60),
    ("grab", 5, 50),
    ("grab_hold", 4, 140),
    ("pummel", 4, 50),
    ("throw_forward", 6, 60),
    ("throw_back", 6, 60),
    ("throw_up", 6, 60),
    ("throw_down", 6, 60),
    ("grabbed", 4, 120),
    ("grabbed_pummel", 3, 60),
    ("grab_escape", 4, 60),
    ("smash_charge", 4, 50),
    ("parry", 3, 50),
    ("dizzy", 6, 130),
    # He turns through his views: profile, three-quarter, front, and round.
    ("turnaround", 5, 44),
]
#: Every row as he faces right; each has a `~mirrored` twin.
BASE_ROWS: List[Tuple[str, int, int]] = MOVE_ROWS + FIGHTER_ROWS
MIRRORED = "{}~mirrored"
ROWS: List[Tuple[str, int, int]] = BASE_ROWS + [(MIRRORED.format(name), frames, ms) for name, frames, ms in BASE_ROWS]
MIRROR_OF: Dict[str, str] = {MIRRORED.format(name): name for name, _frames, _ms in BASE_ROWS}
#: A right-facing view document -> the document of his left side, drawn facing
#: right (mirror its frames to face left). The front has none: it is not mirrored.
LEFT_SIDE_OF: Dict[str, str] = {
    "oiler_three_quarter.rig.json": "oiler_three_quarter_left.rig.json",
    "oiler_side.rig.json": "oiler_side_left.rig.json",
}
#: The expressions every view draws (``face_<name>`` stills in the
#: three-quarter document); each is published as a portrait clip of that name.
FACES = ("knowing", "pleased", "delighted", "surprised", "thinking", "stern", "worried", "hurt")

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
    "jab": ("oiler_side.rig.json", "jab"),
    "dash_attack": ("oiler_side.rig.json", "dash_attack"),
    "smash_up": ("oiler_side.rig.json", "smash_up"),
    "smash_down": ("oiler_side.rig.json", "smash_down"),
    "air_neutral": ("oiler_side.rig.json", "air_neutral"),
    "air_forward": ("oiler_side.rig.json", "air_forward"),
    "air_back": ("oiler_side.rig.json", "air_back"),
    "air_up": ("oiler_side.rig.json", "air_up"),
    "air_down": ("oiler_side.rig.json", "air_down"),
    "convergence": ("oiler_side.rig.json", "convergence"),
    "special_side": ("oiler_side.rig.json", "special_side"),
    "special_up": ("oiler_side.rig.json", "special_up"),
    "special_down": ("oiler_side.rig.json", "special_down"),
    "hit": ("oiler_side.rig.json", "hit"),
    "death": ("oiler_side.rig.json", "death"),
    "taunt": ("oiler_side.rig.json", "taunt"),
    **{name: ("oiler_side.rig.json", name) for name, _frames, _ms in FIGHTER_ROWS if name != "turnaround"},
}
#: The ``turnaround`` row, frame by frame: (view document, mirrored), ending in
#: the facing it is drawn for -- the game draws a turn in the NEW facing. Each
#: view lends its ``turnaround`` still. The ``~mirrored`` twin turns the other
#: way round, from his right profile to his left.
TURN_VIEWS: List[Tuple[str, bool]] = [
    ("oiler_side_left.rig.json", True),
    ("oiler_three_quarter_left.rig.json", True),
    ("oiler_front.rig.json", False),
    ("oiler_three_quarter.rig.json", False),
    ("oiler_side.rig.json", False),
]
TURN_VIEWS_MIRRORED: List[Tuple[str, bool]] = [
    ("oiler_side.rig.json", False),
    ("oiler_three_quarter.rig.json", False),
    ("oiler_front.rig.json", False),
    ("oiler_three_quarter_left.rig.json", True),
    ("oiler_side_left.rig.json", True),
]

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
        "locomotion.run": {"animation": "run", "events": []},
        "locomotion.dash": {"animation": "dash", "events": []},
        "locomotion.skid": {"animation": "skid", "events": []},
        "locomotion.jump": {"animation": "jump", "events": []},
        "locomotion.fall": {"animation": "fall", "events": []},
        "locomotion.land": {"animation": "land_light", "events": []},
        "locomotion.crouch": {"animation": "crouch", "events": []},
        "locomotion.ledge_grab": {"animation": "ledge_grab", "events": []},
        "locomotion.ledge_climb": {"animation": "ledge_climb", "events": []},
        "defense.block": {"animation": "block", "events": []},
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
            "point": {"x": 64.0, "y": 28.0},
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


@lru_cache(maxsize=5)
def _load_doc(filename: str) -> RigDocument:
    path = RIG_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"missing Oiler rig {path}; rebuild from the SVG with "
            "`uv run python scripts/build_oiler_rig.py build`"
        )
    return RigDocument.load(path)


def _render_frame(animation: str, frame_idx: int, frame_count: int):
    base = animation.removesuffix("~mirrored")
    if base == "turnaround":
        views = TURN_VIEWS if base == animation else TURN_VIEWS_MIRRORED
        filename, mirrored = views[frame_idx * len(views) // frame_count]
        frame = _load_doc(filename).render_frame("turnaround", 0, 1)
        return rigdoc.mirrored_canvas(frame) if mirrored else frame
    filename, clip = CLIP_SOURCE[base]
    if base != animation and filename in LEFT_SIDE_OF:
        frame = _load_doc(LEFT_SIDE_OF[filename]).render_frame(clip, frame_idx, frame_count)
        return rigdoc.mirrored_canvas(frame)
    return _load_doc(filename).render_frame(clip, frame_idx, frame_count)


def render_portraits(out_dir: str | Path, **opts):
    """Publish Oiler's close-up expressions directly from the scalable SVG rig."""
    del opts

    def portrait_frame(animation: str, frame_idx: int, frame_count: int, filename: str | None = None):
        filename, clip = (filename, animation) if filename else CLIP_SOURCE[animation]
        doc = _load_doc(filename)
        source = doc.render_at(
            clip,
            doc.frame_time(clip, frame_idx, frame_count),
            scale=4,
        )
        face = FaceGuide(
            center_x=65.0,
            center_y=28.5,
            width=27.0,
            height=33.0,
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
        # His expressions, for `<<portrait_clip "name">>`: knowing (his rest
        # face), pleased, delighted, surprised, thinking, stern, worried, hurt.
        **{
            face: PortraitClip.still(portrait_frame(f"face_{face}", 0, 1, "oiler_three_quarter.rig.json"))
            for face in FACES
        },
    }
    return write_portrait_sheet(
        TARGET_NAME, clips, Path(out_dir), still_clip="portrait"
    )


def render(out_dir: str | Path, **opts):
    del opts
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=_render_frame,
        out_dir=Path(out_dir),
        frame_size=FRAME_SIZE,
        auto_crop=True,
        crop_margin=4,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning={"collision_scale": 1.72},
        mirror_of=MIRROR_OF,
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
    parts = publish_rig_flipbook(
        TARGET_NAME, ROWS, _render_frame, outputs, frame_transform, Path(out_dir),
    )
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())


__all__ = ["ACTOR_METADATA", "render", "render_portraits"]
