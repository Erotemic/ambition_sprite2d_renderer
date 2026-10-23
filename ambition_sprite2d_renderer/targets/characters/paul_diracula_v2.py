"""Paul Diracula, redrawn (v2): Paul Dirac as Count Dracula, an SVG rig.

The drawing is ``data/characters/paul_diracula_v2/paul_diracula_v2_side.svg``
(``scripts/svg_art/paul_diracula_art.py``, look A, "the Count"), and the
skeleton and the rows are ``rigged/paul_diracula_v2/paul_diracula_v2_side.rig.json``
(``scripts/build_paul_diracula_v2_rig.py``).

Jon, 2026-10-22: "a new Paul Diracula". Of three looks he picked none, and on
2026-10-23 he asked to see the new art in the game; look A is cast: Lugosi's
evening dress on Dirac's lean frame (a black tailcoat, white tie, the psi
medallion on its ribbon), an opera cape lined in crimson with a standing
collar, Dirac's long narrow face and his side parting under a small widow's
peak, two small fangs. The old procedural target ``paul_diracula`` stays
renderable beside this one; the lineage of looks names both.

The rows: ``idle``, ``walk``, ``run``, ``jump``, ``fall``, ``talk``,
``interact``, ``slash``, ``attack_side`` (the delta spike), ``special`` (pair
creation), ``block`` (the cape closed across him), ``hit``, ``death``. A row
the game asks for and this sheet does not have falls back to its base pose
(``CharacterAnim::base_pose``).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ambition_sprite2d_renderer.authoring.part_flipbook import publish_rig_flipbook
from ambition_sprite2d_renderer.authoring.portrait import FaceGuide, PortraitClip, render_framed_portrait, write_portrait_sheet
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

from .paul_diracula import AUTHORING_DESCRIPTION, FALLBACK_DIALOGUE, GAMEPLAY_DESCRIPTION, SUGGESTED_BARKS

TARGET_NAME = "paul_diracula_v2"
RIG_PATH = Path(__file__).resolve().parent / "rigged" / TARGET_NAME / f"{TARGET_NAME}_side.rig.json"

TRAITS = ["story", "humanoid", "scientist", "mathematician", "physicist", "vampire_parody", "precision_duelist", "playable_candidate"]

ACTOR_METADATA = {
    "actor": {"character_id": "npc_paul_diracula", "display_name": "Paul Diracula"},
    "lineage": {
        "authoring_description": AUTHORING_DESCRIPTION,
        "gameplay_description": GAMEPLAY_DESCRIPTION,
        "suggested_barks": SUGGESTED_BARKS,
        "fallback_dialogue": FALLBACK_DIALOGUE,
        "derived_from": "paul_diracula",
    },
    "dialogue_hints": {
        "suggested_barks": [
            "I vant to annihilate your positron.",
            "The equation demanded a mirror. I merely opened it.",
            "Antimatter, darling. Not undeath.",
            "Symmetry. Always symmetry.",
        ],
    },
    "body": {"body_plan": "HumanoidBiped", "body_kind": "Standard", "mass_class": "Light", "traits": TRAITS, "locomotion_hint": "Walk"},
    "capabilities": {
        "traversal": {"walk": True, "jump": True, "climb": None, "fly": None, "swim": None, "crawl": None, "use_lifts": True, "door_access": ["public"]},
        "interactions": {"talk": True, "trade": None, "carry": None, "open_doors": ["public"]},
    },
    "brain": {"default_preset": "patrol_peaceful"},
    "actions": {"default_preset": "striker_swipe"},
    "visual": {"default_pose": "idle"},
    "tags": TRAITS,
    # Points in the rig's 224x200 frame (ground at y=192).
    "sockets": {
        "head": {"source": "explicit.profile.humanoid", "point": {"x": 107.0, "y": 64.0}},
        "chest": {"source": "explicit.profile.humanoid", "point": {"x": 109.0, "y": 103.0}},
        "hand_l": {"source": "explicit.profile.humanoid", "point": {"x": 96.0, "y": 138.0}},
        "hand_r": {"source": "explicit.profile.humanoid", "point": {"x": 104.0, "y": 139.0}},
        "speech_bubble": {"source": "explicit.profile.humanoid", "point": {"x": 106.0, "y": 38.0}},
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "locomotion.run": {"animation": "run", "events": []},
        "traversal.jump": {"animation": "jump", "events": []},
        "traversal.fall": {"animation": "fall", "events": []},
        "action.melee.primary": {
            "animation": "slash",
            "events": [
                {"t": 0.32, "event": "hitbox_active_start", "source": "explicit.profile.combat_humanoid"},
                {"t": 0.56, "event": "hitbox_active_end", "source": "explicit.profile.combat_humanoid"},
            ],
        },
        "action.special.primary": {"animation": "special", "events": []},
        "action.defense.block": {"animation": "block", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
    },
}

#: His face in the rig's frame: the portrait's crop.
FACE = FaceGuide(center_x=104.0, center_y=58.0, width=30.0, height=42.0, source_width=224.0, source_height=200.0)
#: How much of the frame the portrait shows across: his head and his collar.
PORTRAIT_VIEW_W = 62.0


@lru_cache(maxsize=1)
def _doc() -> RigDocument:
    return RigDocument.load(RIG_PATH)


def _render_frame(animation: str, frame_idx: int, frame_count: int):
    return _doc().render_frame(animation, frame_idx, frame_count)


def _portrait(animation: str, frame_idx: int, frame_count: int):
    doc = _doc()
    source = doc.render_at(animation, doc.frame_time(animation, frame_idx, frame_count), scale=4)
    return render_framed_portrait(source, FACE, view_width=PORTRAIT_VIEW_W)


def render_portraits(out_dir: str | Path, **opts):
    """His close-ups, from the rig at four times the sheet's scale."""
    del opts
    clips = {
        "default": PortraitClip.loop(tuple(_portrait("idle", i, 8) for i in range(8)), duration_ms=160),
        "portrait": PortraitClip.still(_portrait("idle", 0, 8)),
        "talking": PortraitClip(tuple(_portrait("talk", i, 6) for i in range(6)), duration_ms=115, looping=True),
        "inspecting": PortraitClip.still(_portrait("interact", 3, 6)),
    }
    return write_portrait_sheet(TARGET_NAME, clips, Path(out_dir), still_clip="portrait")


def render(out_dir: str | Path, **opts):
    del opts
    doc = _doc()
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=doc.rows(),
        render_fn=_render_frame,
        out_dir=Path(out_dir),
        frame_size=(int(doc.data["frame"]["width"]), int(doc.data["frame"]["height"])),
        auto_crop=True,
        crop_margin=4,
        actor_metadata=ACTOR_METADATA,
        sheet_tuning=doc.sprite_tuning,
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    parts = publish_rig_flipbook(TARGET_NAME, doc.rows(), _render_frame, outputs, frame_transform, Path(out_dir))
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())


__all__ = ["ACTOR_METADATA", "render", "render_portraits"]
