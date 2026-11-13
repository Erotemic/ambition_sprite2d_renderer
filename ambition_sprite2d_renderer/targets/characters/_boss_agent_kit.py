"""The sheet of one of the bossofthegame's named agents (Geppetto, Clause,
Wren): the Director's motion library on the agent's own drawing.

Each agent's SVG is the Director's rig with every part drawn again
(``scripts/svg_art/boss_agents_art.py``, from Jon's concept sheets), so it
moves as he does and swings its prop where he swings his pen. The game's
design is ``docs/planning/game/final-boss.md``: the Boss calls them in for
his encore ("Spawn subagents. Parallelize the kill.").
"""

from __future__ import annotations

from pathlib import Path

from ambition_sprite2d_renderer.authoring import strike_axis
from ambition_sprite2d_renderer.authoring.part_flipbook import publish_rig_flipbook
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

from ._authored_swing_fighter import AuthoredSwingFighter

#: Each row of an agent's sheet and the Director's clip that plays it: what
#: a summoned fighter on the stage uses.
ROWS = (
    ("idle", "idle"),
    ("walk", "walk"),
    ("run", "run"),
    ("jump", "jump"),
    ("fall", "fall"),
    ("slash", "slash"),
    ("hurt", "hit"),
    ("death", "knockdown"),
    ("talk", "talk"),
    ("taunt", "taunt"),
)
_CLIP_OF = dict(ROWS)


class _Agent(AuthoredSwingFighter):
    """The swing's axis is measured off the prop in the hand (the part the
    Director's pen is), as his is."""

    def __init__(self, name: str, tint: dict):
        super().__init__(name)
        self._tint = tint

    def spec_for(self, animation: str) -> dict | None:
        spec = super().spec_for(animation)
        for effect in ("trail", "poke"):
            if spec and isinstance(spec.get(effect), dict):
                spec[effect].update(self._tint)
        return spec

    def _strike_axes(self, animation: str, frame_count: int, padding):
        if not self.spec_for(animation):
            return None
        return strike_axis.from_part(self.doc(), animation, self._sample_times(animation, frame_count), "pen", padding=padding)


def actor_metadata(name: str, character_id: str, display_name: str, description: str, traits: list[str]) -> dict:
    return {
        "actor": {"character_id": character_id, "display_name": display_name, "actor_id": name},
        "body": {"body_plan": "HumanoidBiped", "body_kind": "Standard", "mass_class": "Medium",
                 "traits": ["story", "humanoid", "agent", *traits], "locomotion_hint": "Walk"},
        "brain": {"default_preset": "melee_brute_striker"},
        "actions": {"default_preset": "striker_swipe"},
        "visual": {"default_pose": "idle", "canonical_source": f"data/characters/{name}/{name}.svg"},
        "tags": ["story", "agent", "enemy"],
        "animation_bindings": {"default": {"animation": "idle", "events": []}, "interaction.talk": {"animation": "talk", "events": []}},
        "description": description,
        "missing_information": ["The concept sheets show other forms (weight tiers, thinking modes); this sheet is one form."],
    }


def make_render(name: str, metadata: dict, tint: dict):
    fighter = _Agent(name, tint)

    def rows():
        clips = {clip: (count, ms) for clip, count, ms in fighter.doc().rows()}
        return [(row, *clips[clip]) for row, clip in ROWS]

    def frame(row: str, frame_idx: int, frame_count: int):
        return fighter.render_frame(_CLIP_OF[row], frame_idx, frame_count)

    def render(out_dir: str | Path, **opts):
        del opts
        table = rows()
        frame_transform: dict = {}
        outputs = build_sheet(
            frame_transform_out=frame_transform, target=name, rows=table, render_fn=frame, out_dir=Path(out_dir),
            frame_size=fighter.frame_size(), auto_crop=True, crop_margin=4, actor_metadata=metadata,
            body_metrics_fn=fighter.body_metrics, sheet_tuning=fighter.doc().sprite_tuning or {"collision_scale": 1.8},
            authored_faces_left=fighter.doc().authored_faces_left,
        )
        keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
        parts = publish_rig_flipbook(
            name, table, frame, outputs, frame_transform, Path(out_dir),
            render_clip=lambda row, count: list(AuthoredSwingFighter._clip_frames.__wrapped__(fighter, _CLIP_OF[row], count)),
        )
        return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())

    return render
