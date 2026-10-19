"""The Dark Lord: an armoured overlord with a spiked crown helm, a red visor slit and a rune halberd.

An SVG rig. The drawing is ``data/characters/dark_lord/dark_lord.svg``
(``scripts/svg_art/dark_lord_art.py``), and the skeleton and the rows are
``rigged/dark_lord/dark_lord.rig.json`` (``scripts/build_dark_lord_rig.py``).

Jon, 2026-10-18: "Also need new art for dark lord"; of three redraws, "A for
dark lord", and "keep the other dark lord variants around, they are good.
Might be useful as skins." A is the Iron Tyrant: today's kit redrawn, a
spiked crown helm, plate, a long black cape lined in crimson, a short red
tabard, clawed gauntlets and a rune halberd in both fists. The Sorcerer-King
and the Ember Warlord are drawn by the art script on the same parts and cast
nowhere.

The rows are the eight he has always had: ``idle``, ``walk``, ``slash``,
``cast`` (a rune bolt kindled in his free hand), ``summon`` (iron spikes out
of the ground ahead), ``guard``, ``hurt``, ``death`` (to his knees, then on
his face beside his planted halberd).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ambition_sprite2d_renderer.authoring.part_flipbook import publish_rig_flipbook
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

TARGET_NAME = "dark_lord"
RIG_PATH = Path(__file__).resolve().parent / "rigged" / TARGET_NAME / "dark_lord.rig.json"

ACTOR_METADATA = {
    "actor": {"character_id": "npc_dark_lord", "display_name": "Dark Lord"},
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Wide",
        "mass_class": "Heavy",
        "traits": [
            "story",
            "humanoid",
            "enemy",
            "combatant",
            "story",
            "enemy",
            "boss_candidate",
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
    "brain": {"default_preset": "melee_brute_brute"},
    "actions": {"default_preset": "boss_bolt"},
    "visual": {"default_pose": "idle"},
    "tags": [
        "story",
        "humanoid",
        "enemy",
        "combatant",
        "story",
        "enemy",
        "boss_candidate",
    ],
    "sockets": {
        "head": {"source": "explicit.profile.humanoid", "point": {"x": 159.6, "y": 156.0}},
        "chest": {"source": "explicit.profile.humanoid", "point": {"x": 161.6, "y": 192.0}},
        "hand_l": {"source": "explicit.profile.humanoid", "point": {"x": 187.7, "y": 232.0}},
        "hand_r": {"source": "explicit.profile.humanoid", "point": {"x": 186.9, "y": 206.4}},
        "speech_bubble": {"source": "explicit.profile.humanoid", "point": {"x": 158.0, "y": 116.0}},
        "weapon_grip": {"source": "explicit.profile.combat_humanoid", "point": {"x": 186.9, "y": 206.4}},
        "weapon_tip": {"source": "explicit.profile.combat_humanoid", "point": {"x": 185.6, "y": 116.0}},
        "projectile_origin": {"source": "explicit.profile.dark_lord", "point": {"x": 197.2, "y": 231.2}},
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
