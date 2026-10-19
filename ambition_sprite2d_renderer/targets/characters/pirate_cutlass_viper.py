"""The Pirate Cutlass Viper: the crew's lean duelist, a tricorn over a red bandana, a curved cutlass in her guard.

An SVG rig. The drawing is ``data/characters/pirate_cutlass_viper/pirate_cutlass_viper.svg``
(``scripts/svg_art/pirate_cutlass_viper_art.py``), and the skeleton and the rows are
``rigged/pirate_cutlass_viper/pirate_cutlass_viper.rig.json`` (``scripts/build_pirate_cutlass_viper_rig.py``).

Jon, 2026-10-18, of three redraws: "A for viper, keep the rest". A is
today's Viper redrawn: a tricorn over a red bandana, a long dark ponytail, a
blouse under a laced plum bodice, a gold sash, plum coat tails, blue
breeches, tall boots and a curved cutlass with a brass D-guard. The two other
looks are drawn by the art script and cast nowhere.

She is drawn from the side. The rows are the ten she has always had:
``idle`` (her guard), ``walk``, ``turn_right`` (her guard lowered) and
``profile_right`` (at ease), their mirror images ``turn_left`` and
``profile_left`` (drawn here by flipping the right rows' frames about the
frame's centre, her pelvis), ``slash`` (a rising cut), ``taunt``, ``hurt``,
``death``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ambition_sprite2d_renderer.authoring.part_flipbook import publish_rig_flipbook
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument, mirrored_canvas
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

TARGET_NAME = "pirate_cutlass_viper"
RIG_PATH = Path(__file__).resolve().parent / "rigged" / TARGET_NAME / "pirate_cutlass_viper.rig.json"
#: Rows drawn as the mirror image of another row, frame for frame.
MIRRORED = {"turn_left": "turn_right", "profile_left": "profile_right"}

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_pirate_cutlass_viper",
        "display_name": "Pirate Cutlass Viper",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": [
            "story",
            "humanoid",
            "enemy",
            "combatant",
            "pirate",
            "cutlass",
            "duelist",
        ],
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
    "brain": {"default_preset": "melee_brute_striker"},
    "actions": {"default_preset": "striker_swipe"},
    "visual": {"default_pose": "idle"},
    "tags": ["story", "humanoid", "enemy", "combatant", "pirate", "cutlass", "duelist"],
    "sockets": {
        "head": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 135.6, "y": 90.0},
        },
        "chest": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 131.2, "y": 130.0},
        },
        "hand_l": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 125.6, "y": 146.8},
        },
        "hand_r": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 158.4, "y": 144.8},
        },
        "speech_bubble": {
            "source": "explicit.profile.humanoid",
            "point": {"x": 135.6, "y": 62.0},
        },
        "weapon_grip": {
            "source": "explicit.profile.combat_humanoid",
            "point": {"x": 158.4, "y": 144.8},
        },
        "weapon_tip": {
            "source": "explicit.profile.combat_humanoid",
            "point": {"x": 197.1, "y": 105.9},
        },
        "poison_edge": {
            "source": "explicit.profile.pirate",
            "point": {"x": 192.4, "y": 116.8},
        },
    },
    "animation_bindings": {
        "default": {"animation": "idle", "events": []},
        "locomotion.walk": {"animation": "walk", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
        "interaction.use": {"animation": "interact", "events": []},
        "action.melee.primary": {
            "animation": "slash",
            "events": [
                {
                    "t": 0.34,
                    "event": "hitbox_active_start",
                    "source": "explicit.profile.combat_humanoid",
                },
                {
                    "t": 0.58,
                    "event": "hitbox_active_end",
                    "source": "explicit.profile.combat_humanoid",
                },
            ],
        },
    },
}


@lru_cache(maxsize=1)
def _doc() -> RigDocument:
    return RigDocument.load(RIG_PATH)


def _render_frame(animation: str, frame_idx: int, frame_count: int):
    if animation in MIRRORED:
        return mirrored_canvas(_doc().render_frame(MIRRORED[animation], frame_idx, frame_count))
    return _doc().render_frame(animation, frame_idx, frame_count)


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


__all__ = ["ACTOR_METADATA", "render"]
