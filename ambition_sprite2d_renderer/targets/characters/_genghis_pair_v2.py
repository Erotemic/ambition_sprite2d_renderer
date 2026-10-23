"""What Genghis Can and Genghis Can't share in look C: the actor sidecar, the sheet and the portraits.

Each brother is an SVG rig. His drawing is
``data/characters/genghis_<who>_v2/genghis_<who>_v2.svg`` (the rig mode of
``scripts/svg_art/genghis_pair_art.py``), and his skeleton and rows are
``rigged/genghis_<who>_v2/genghis_<who>_v2.rig.json``
(``scripts/build_genghis_pair_v2_rig.py``). The targets ``genghis_can_v2`` and
``genghis_cant_v2`` name the brother; this module draws nobody by itself.

Look C, "steppe" (2026-10-23): a winter deel and a fox-fur hat. Can points the
way, his flaps tied up, a teal deel and an orange sash; Can't cups his chin,
his flaps down, a maroon deel. The procedural pair (``genghis_can``,
``genghis_cant``) is their first design and stays renderable as the lineage.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, Tuple

from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.portrait import FaceGuide, PortraitClip, render_framed_portrait, write_portrait_sheet
from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet

RIGGED = Path(__file__).resolve().parent / "rigged"

Point = Tuple[float, float]


def actor_metadata(*, target: str, character_id: str, display_name: str, sockets: Dict[str, Point], barks, authoring: str,
                   gameplay: str) -> dict:
    """The actor sidecar of one brother. ``sockets`` are frame pixels."""
    tags = ["story", "humanoid", "warlord", "nomad_parody", "paired_character"]
    return {
        "actor": {"character_id": character_id, "display_name": display_name, "actor_id": target},
        "body": {
            "body_plan": "HumanoidBiped",
            "body_kind": "Standard",
            "mass_class": "Medium",
            "traits": list(tags),
            "locomotion_hint": "Walk",
        },
        "capabilities": {
            "traversal": {
                "walk": True, "jump": None, "climb": None, "fly": None, "swim": None, "crawl": None,
                "use_lifts": True, "door_access": ["public"],
            },
            "interactions": {"talk": True, "trade": None, "carry": None, "open_doors": ["public"]},
        },
        "brain": {"default_preset": "patrol_peaceful"},
        "actions": {"default_preset": "peaceful"},
        "visual": {"default_pose": "idle", "portrait": {"animation": "idle", "frame": 0}},
        "tags": list(tags),
        "sockets": {name: {"source": "explicit.profile.humanoid", "point": {"x": x, "y": y}} for name, (x, y) in sockets.items()},
        "animation_bindings": {
            "default": {"animation": "idle", "events": []},
            "locomotion.walk": {"animation": "walk", "events": []},
            "interaction.talk": {"animation": "talk", "events": []},
            "interaction.use": {"animation": "interact", "events": []},
            "emote.taunt": {"animation": "taunt", "events": []},
        },
        "dialogue_hints": {"barks": list(barks)},
        "authoring_description": authoring,
        "gameplay_description": gameplay,
    }


@lru_cache(maxsize=2)
def doc(target: str) -> RigDocument:
    return RigDocument.load(RIGGED / target / f"{target}.rig.json")


def render(target: str, actor: dict, out_dir: str | Path):
    rig = doc(target)

    def render_frame(animation: str, frame_idx: int, frame_count: int):
        return rig.render_frame(animation, frame_idx, frame_count)

    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=target,
        rows=rig.rows(),
        render_fn=render_frame,
        out_dir=Path(out_dir),
        frame_size=(int(rig.data["frame"]["width"]), int(rig.data["frame"]["height"])),
        auto_crop=True,
        crop_margin=4,
        actor_metadata=actor,
        sheet_tuning=rig.sprite_tuning,
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    parts = publish_rig_flipbook(target, rig.rows(), render_frame, outputs, frame_transform, Path(out_dir))
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())


def render_portraits(target: str, head: Point, out_dir: str | Path):
    """The close-ups, from the SVG rig at four times the sheet's size; ``head``
    is the face's centre in frame pixels."""
    rig = doc(target)

    def portrait_frame(animation: str, frame_idx: int, frame_count: int):
        source = rig.render_at(animation, rig.frame_time(animation, frame_idx, frame_count), scale=4)
        face = FaceGuide(center_x=head[0], center_y=head[1] - 4.0, width=34.0, height=40.0,
                         source_width=float(rig.frame["width"]), source_height=float(rig.frame["height"]))
        # Head and shoulders, the tall hat in: tighter than the default view.
        return render_framed_portrait(source, face, view_width=62.0, center_y=head[1] + 2.0)

    clips = {
        "default": PortraitClip.still(portrait_frame("idle", 0, 8)),
        "talking": PortraitClip(tuple(portrait_frame("talk", i, 6) for i in range(6)), duration_ms=108, looping=True),
        "emote": PortraitClip.still(portrait_frame("taunt", 4, 8)),
    }
    return write_portrait_sheet(target, clips, Path(out_dir))
