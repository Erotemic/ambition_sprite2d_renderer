"""The shared builder of Carl Runga v2 and Martin Cutta v2 (draws nobody itself).

Jon, 2026-10-22: "need a new Carl Runga and Martin Cutta." He was shown three
looks of the pair and did not pick; on 2026-10-23 look A, "the Goettingen
pair", was cast: Runga (Carl Runge) bald, a full grizzled beard, a black frock
coat over a wine waistcoat; Cutta (Martin Kutta) upright, dark hair and a
moustache, a dove-grey lounge suit with a high collar, pince-nez and the green
ledger of coefficients. The first designs (``carl_runga``, ``martin_cutta``)
still render; these are their ``_v2`` targets.

Each character is two SVG rigs: the drawings are
``data/characters/<name>_v2/<name>_v2_{side,front}.svg``
(``scripts/svg_art/runge_kutta_duo_art.py --rig``), the skeletons and clips
``rigged/<name>_v2/<name>_v2_{side,front}.rig.json``
(``scripts/build_runge_kutta_v2_rig.py``). The rows of the game are drawn
from the side view, except ``talk`` and ``taunt``, which face you.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple

from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.portrait import FaceGuide, PortraitClip, render_framed_portrait, write_portrait_sheet
from ...authoring.rigdoc import RigDocument
from ...authoring.sheet_build import build_sheet

RIGGED = Path(__file__).resolve().parent / "rigged"
FRAME_SIZE = (320, 352)

#: (row, frames, ms per frame). ``attack_side`` is the swipe of the game.
ROWS: List[Tuple[str, int, int]] = [
    ("idle", 8, 0),
    ("walk", 8, 0),
    ("talk", 6, 0),
    ("interact", 6, 0),
    ("attack_side", 8, 0),
    ("taunt", 8, 0),
    ("hit", 4, 0),
    ("death", 8, 0),
]
#: Row -> the view whose clip of the same name draws it.
VIEW_OF: Dict[str, str] = {"talk": "front", "taunt": "front"}


def _doc(target: str, view: str) -> RigDocument:
    return _load(str(RIGGED / target / f"{target}_{view}.rig.json"))


@lru_cache(maxsize=8)
def _load(path: str) -> RigDocument:
    return RigDocument.load(Path(path))


def rows(target: str) -> List[Tuple[str, int, int]]:
    """The rows with each clip's own frame count and time."""
    out = []
    for name, _frames, _ms in ROWS:
        clip = _doc(target, VIEW_OF.get(name, "side")).data["clips"][name]
        out.append((name, int(clip["frames"]), int(clip["duration_ms"])))
    return out


def render_frame(target: str, animation: str, frame_idx: int, frame_count: int):
    return _doc(target, VIEW_OF.get(animation, "side")).render_frame(animation, frame_idx, frame_count)


def metadata(target: str, character_id: str, display_name: str, traits: List[str], sockets: dict) -> dict:
    """The actor contract both share; each target names its id and sockets."""
    return {
        "actor": {"character_id": character_id, "display_name": display_name},
        "body": {
            "body_plan": "HumanoidBiped",
            "body_kind": "Standard",
            "mass_class": "Medium",
            "traits": ["npc", "humanoid", "mathematician", "kernel_raider", "numerical_duelist"] + traits,
            "locomotion_hint": "Walk",
        },
        "capabilities": {
            "traversal": {"walk": True, "jump": None, "climb": None, "fly": None, "swim": None, "crawl": None,
                          "use_lifts": True, "door_access": ["public"]},
            "interactions": {"talk": True, "trade": None, "carry": None, "open_doors": ["public"]},
        },
        "brain": {"default_preset": "melee_brute_striker"},
        "actions": {"default_preset": "striker_swipe"},
        "visual": {"default_pose": "idle"},
        "tags": ["npc", "humanoid", "mathematician", "kernel_raider", "numerical_duelist", "svg_rigged"] + traits,
        "sockets": {key: {"source": "explicit.profile.humanoid", "point": {"x": x, "y": y}} for key, (x, y) in sockets.items()},
        "animation_bindings": {
            "default": {"animation": "idle", "events": []},
            "locomotion.walk": {"animation": "walk", "events": []},
            "interaction.talk": {"animation": "talk", "events": []},
            "interaction.use": {"animation": "interact", "events": []},
            "action.melee.primary": {"animation": "attack_side", "events": []},
            "action.attack.side": {"animation": "attack_side", "events": []},
            "reaction.hit": {"animation": "hit", "events": []},
            "reaction.death": {"animation": "death", "events": []},
            "emote.taunt": {"animation": "taunt", "events": []},
        },
    }


def render(target: str, actor_metadata: dict, out_dir: Path) -> List[Path]:
    frame_transform: dict = {}
    sheet_rows = rows(target)
    draw = lambda animation, i, n: render_frame(target, animation, i, n)  # noqa: E731
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=target,
        rows=sheet_rows,
        render_fn=draw,
        out_dir=Path(out_dir),
        frame_size=FRAME_SIZE,
        auto_crop=True,
        crop_margin=4,
        actor_metadata=actor_metadata,
        sheet_tuning=_doc(target, "side").sprite_tuning,
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    parts = publish_rig_flipbook(target, sheet_rows, draw, outputs, frame_transform, Path(out_dir))
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())


def render_portraits(target: str, face_center: Tuple[float, float], face_size: Tuple[float, float], view: Tuple[float, float],
                     out_dir: Path) -> List[Path]:
    """The dialogue's clips, all from the front view: ``default``, ``talking``,
    ``scheming`` (the taunt) and ``seizing`` (he grabs for the Kernel)."""
    doc = _doc(target, "front")

    def frame(clip: str, i: int):
        n = int(doc.data["clips"][clip]["frames"])
        source = doc.render_at(clip, doc.frame_time(clip, i, n), scale=4)
        guide = FaceGuide(center_x=face_center[0], center_y=face_center[1], width=face_size[0], height=face_size[1],
                          source_width=float(FRAME_SIZE[0]), source_height=float(FRAME_SIZE[1]))
        # ``view``: the width of the head and shoulders and their centre's
        # height, in frame pixels.
        return render_framed_portrait(source, guide, view_width=view[0], center_y=view[1])

    clips = {
        "default": PortraitClip.still(frame("front_idle", 0)),
        "talking": PortraitClip(tuple(frame("talk", i) for i in range(6)), duration_ms=110, looping=True),
        "scheming": PortraitClip(tuple(frame("taunt", i) for i in (1, 3, 5, 7)), duration_ms=112, looping=True),
        "seizing": PortraitClip(tuple(frame("seize", i) for i in range(4)), duration_ms=94, looping=True),
    }
    return write_portrait_sheet(target, clips, Path(out_dir))
