"""The bossofthegame: the final boss, who is the Director.

The Director (``director``) is the person writing the game, and the final
boss is that person, so this sheet is drawn from the Director's own drawing
and motion library: the same SVG, the same pen, the same poses, with one prop
added, a mechanical keyboard slung across his waist (``director_boss``,
derived by ``scripts/svg_art/director_boss_art.py``). It names his clips by
the boss slots the game's ``boss_sheets.ron`` reads (``rest``,
``floor_slam``, ``side_sweep``, ``spike_halo``, ``hit``, ``death``, in that
order, then ``talk``).

The game's design: ``docs/planning/game/final-boss.md``. He stands on the
shoulders of Full Stack (``full_stack_giant``).
"""

from __future__ import annotations

from pathlib import Path

from ambition_sprite2d_renderer.authoring.part_flipbook import publish_rig_flipbook
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

from ambition_sprite2d_renderer.authoring import strike_axis

from . import director
from ._authored_swing_fighter import AuthoredSwingFighter


class _Director(AuthoredSwingFighter):
    """The Director's sheet pipeline on his boss drawing: his ink-tinted
    ribbons, on the axis measured off his pen (see `director._spec_for` and
    `director._swing_axes`)."""

    def spec_for(self, animation: str) -> dict | None:
        spec = super().spec_for(animation)
        for effect in ("trail", "poke"):
            if spec and isinstance(spec.get(effect), dict):
                spec[effect].update(director.TRAIL_TINT)
        return spec

    def _strike_axes(self, animation: str, frame_count: int, padding):
        if not self.spec_for(animation):
            return None
        return strike_axis.from_part(
            self.doc(), animation, self._sample_times(animation, frame_count), "pen", padding=padding
        )

TARGET_NAME = "bossofthegame_boss"
_FIGHTER = _Director("director_boss")

#: Each boss slot and the Director's clip that plays it. He conducts his
#: agent's moves with the pen raised (`smash_up`), brings it down for the
#: keystroke rain (`smash_down`), and sweeps it for the backspace
#: (`smash_forward`). Beaten, he goes down, and stays down.
BOSS_ROWS = (
    ("rest", "idle"),
    ("floor_slam", "smash_down"),
    ("side_sweep", "smash_forward"),
    ("spike_halo", "smash_up"),
    ("hit", "hit"),
    ("death", "knockdown"),
    ("talk", "talk"),
)
_CLIP_OF = dict(BOSS_ROWS)

ACTOR_METADATA = {
    "actor": {
        "character_id": "npc_bossofthegame",
        "display_name": "bossofthegame",
        "actor_id": "bossofthegame",
    },
    "body": {
        "body_plan": "HumanoidBiped",
        "body_kind": "Standard",
        "mass_class": "Medium",
        "traits": ["story", "humanoid", "boss", "final_boss"],
        "locomotion_hint": "Walk",
    },
    "brain": {"default_preset": "stand_still"},
    "actions": {"default_preset": "peaceful"},
    "visual": {
        "default_pose": "rest",
        "canonical_source": "data/characters/director_boss/director_boss.svg",
    },
    "tags": ["story", "humanoid", "boss", "final_boss"],
    "animation_bindings": {
        "default": {"animation": "rest", "events": []},
        "interaction.talk": {"animation": "talk", "events": []},
    },
    "missing_information": [
        "His fight is authored by the game (boss_profiles.ron, bossofthegame); "
        "the renderer draws his rows only."
    ],
}


def _rows() -> list[tuple[str, int, int]]:
    clips = {name: (count, ms) for name, count, ms in _FIGHTER.doc().rows()}
    return [(row, *clips[clip]) for row, clip in BOSS_ROWS]


def _render_frame(row: str, frame_idx: int, frame_count: int):
    return _FIGHTER.render_frame(_CLIP_OF[row], frame_idx, frame_count)


def render(out_dir: str | Path, **opts):
    del opts
    rows = _rows()
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=rows,
        render_fn=_render_frame,
        out_dir=Path(out_dir),
        frame_size=_FIGHTER.frame_size(),
        auto_crop=True,
        crop_margin=4,
        actor_metadata=ACTOR_METADATA,
        body_metrics_fn=_FIGHTER.body_metrics,
        sheet_tuning=_FIGHTER.doc().sprite_tuning or {"collision_scale": 1.8},
        authored_faces_left=_FIGHTER.doc().authored_faces_left,
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    parts = publish_rig_flipbook(
        TARGET_NAME, rows, _render_frame, outputs, frame_transform, Path(out_dir),
        render_clip=lambda row, count: list(
            AuthoredSwingFighter._clip_frames.__wrapped__(_FIGHTER, _CLIP_OF[row], count)
        ),
    )
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())


__all__ = ["ACTOR_METADATA", "BOSS_ROWS", "render"]
