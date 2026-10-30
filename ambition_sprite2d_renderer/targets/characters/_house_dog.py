"""What the three house dogs share: each is drawn on the companion dog's rig.

A house dog (``dog_honey``, ``dog_roadie``, ``dog_bezoar``) has its own SVG
and its own rig document, with the companion dog's parts about the companion
dog's joints (``scripts/svg_art/house_dogs_art.py``,
``scripts/build_house_dog_rigs.py``). Its rig document has NO clips. It
borrows the companion dog's clips when the document loads, so the four dogs
move as one: a change to a clip of the companion dog is a change to each.

THE LEGS HAVE THE DOG'S OWN LENGTH (``LEG_SCALE``). Honey is short, Bezoar is
lanky. The drawing, the joints of the rig and the borrowed clips all use the
one number: a clip lowers the body by a distance that was authored for the
companion dog's legs (to sit, to lie down), so a house dog's ``root_y`` is
that distance times its own leg length.
"""

from __future__ import annotations

import copy
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

from ambition_sprite2d_renderer.authoring import rigdoc
from ambition_sprite2d_renderer.authoring.part_flipbook import publish_rig_flipbook
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.authoring.sheet_build import build_sheet

RIGGED = Path(__file__).resolve().parent / "rigged"
COMPANION_RIG_PATH = RIGGED / "companion_dog" / "companion_dog_side.rig.json"


#: How long the legs of each dog are, as a part of the companion dog's.
LEG_SCALE: Dict[str, float] = {"dog_honey": 0.80, "dog_roadie": 1.0, "dog_bezoar": 1.05}
#: How thick the legs of each dog are, as a part of the companion dog's. A
#: fact of the drawing only: no joint moves.
LEG_THICKNESS: Dict[str, float] = {"dog_honey": 1.0, "dog_roadie": 1.0, "dog_bezoar": 0.9}
#: A dog that is not the same on its two sides has a second drawing, of its
#: LEFT side. Honey's right ear has a small flap at its tip.
MIRRORED = "{}~mirrored"
LEFT_SIDE: Dict[str, str] = {"dog_honey": "dog_honey_left_side"}
#: The line of the hips and shoulders in the drawing (SVG units). A leg is
#: made longer or shorter under this line; what is over it does not move.
HIP_Y = 300.0


def leg_y(y: float, scale: float) -> float:
    """Where a height of the companion dog's drawing is on a dog whose legs
    are ``scale`` as long."""
    return y if y <= HIP_Y else HIP_Y + (y - HIP_Y) * scale


def rig_path(target: str, left_side: bool = False) -> Path:
    """The rig document of ``target``: of its right side (it faces right, as
    each character is drawn), or of its left side when it has one."""
    name = LEFT_SIDE[target] if left_side else f"{target}_side"
    return RIGGED / target / f"{name}.rig.json"


def borrowed_clips(target: str) -> Dict[str, Any]:
    """The companion dog's clips, as ``target`` plays them: the body goes
    down by its own leg length, and the mouth at rest is hidden for the
    frames in which the bark mouth is shown."""
    clips = copy.deepcopy(json.loads(COMPANION_RIG_PATH.read_text())["clips"])
    scale = LEG_SCALE[target]
    for clip in clips.values():
        channels = clip.get("channels", {})
        drop = channels.get("root_y")
        if drop is not None and scale != 1.0:
            if set(drop) != {"expr"}:
                raise RuntimeError("a companion dog clip states root_y in a form this loader does not scale")
            drop["expr"] = f"{scale}*({drop['expr']})"
        bark = channels.get("bark_mouth")
        if bark is not None:
            if set(bark) != {"expr"}:
                raise RuntimeError("a companion dog clip states bark_mouth in a form this loader does not turn about")
            channels["rest_mouth"] = {"expr": f"1-({bark['expr']})"}
    return clips


@lru_cache(maxsize=8)
def _load(target: str, left_side: bool, mtime_ns: int, companion_mtime_ns: int) -> RigDocument:
    # One document for each side of a dog in the process: it owns the rasters of its parts.
    del mtime_ns, companion_mtime_ns
    doc = RigDocument.load(rig_path(target, left_side))
    doc.data["clips"] = borrowed_clips(target)
    return doc


def doc(target: str, left_side: bool = False) -> RigDocument:
    path = rig_path(target, left_side)
    return _load(target, left_side, path.stat().st_mtime_ns, COMPANION_RIG_PATH.stat().st_mtime_ns)


def actor_metadata(actor: Dict[str, str], looks: List[str]) -> Dict[str, Any]:
    """The actor contract of a house dog: the companion dog's body and rows,
    with this dog's name and looks. ``actor`` is its id and its name; each
    target spells the id out, so a scan of the targets reads it."""
    return {
        "actor": dict(actor),
        "authoring_description": {
            "visual_inspirations": looks,
            "rigging_notes": [
                "The SVG owns the part shapes. The joints and the motion are the companion dog's.",
                "Each leg has an upper part, a lower part, and a paw.",
            ],
        },
        "body": {
            "body_plan": "Quadruped",
            "body_kind": "Standard",
            "mass_class": "Light",
            "traits": ["animal", "dog", "quadruped", "no_hands", "companion"],
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
                "use_lifts": None,
                "door_access": [],
            },
            "interactions": {"talk": None, "trade": None, "carry": None, "open_doors": []},
        },
        "brain": {"default_preset": "companion_dog_roam"},
        "actions": {"default_preset": "peaceful"},
        "visual": {"default_pose": "idle"},
        "animation_bindings": {
            "default": {"animation": "idle", "events": []},
            "locomotion.walk": {"animation": "walk", "events": []},
            "locomotion.run": {"animation": "run", "events": []},
            "locomotion.jump": {"animation": "jump", "events": []},
            "locomotion.fall": {"animation": "fall", "events": []},
            "interaction.use": {"animation": "happy", "events": []},
            "interaction.talk": {"animation": "sit_idle", "events": []},
            "vocalization.bark": {"animation": "bark", "events": []},
            "life.death": {"animation": "death", "events": []},
        },
        "tags": ["animal", "dog", "quadruped", "companion", "svg_rigged"],
    }


def render(target: str, metadata: Dict[str, Any], out_dir: str | Path):
    """Publish the sheet and the part flipbook of ``target``.

    A dog with a left side has each row a second time, drawn from that side
    and mirrored (``<row>~mirrored``). The game draws that row when the dog
    faces left, so what is on one side of the dog stays on that side."""
    rig = doc(target)
    rows = list(rig.rows())
    mirror_of: Dict[str, str] = {}
    if target in LEFT_SIDE:
        mirror_of = {MIRRORED.format(name): name for name, _frames, _ms in rows}
        rows += [(MIRRORED.format(name), frames, ms) for name, frames, ms in rows]

    def render_frame(animation: str, frame_idx: int, frame_count: int):
        original = mirror_of.get(animation)
        if original is None:
            return rig.render_frame(animation, frame_idx, frame_count)
        return rigdoc.mirrored_canvas(doc(target, left_side=True).render_frame(original, frame_idx, frame_count))

    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=target,
        rows=rows,
        render_fn=render_frame,
        out_dir=Path(out_dir),
        frame_size=(int(rig.data["frame"]["width"]), int(rig.data["frame"]["height"])),
        auto_crop=True,
        crop_margin=4,
        actor_metadata=metadata,
        sheet_tuning=rig.sprite_tuning,
        mirror_of=mirror_of or None,
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    parts = publish_rig_flipbook(target, rows, render_frame, outputs, frame_transform, Path(out_dir))
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())


__all__ = ["HIP_Y", "LEFT_SIDE", "LEG_SCALE", "LEG_THICKNESS", "actor_metadata", "borrowed_clips", "doc", "leg_y", "render", "rig_path"]
