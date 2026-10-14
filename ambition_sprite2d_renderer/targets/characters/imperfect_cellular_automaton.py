"""The Imperfect Cellular Automaton: an SVG rig that is drawn from both sides.

The SVGs own the art (``data/characters/imperfect_cellular_automaton/``), and
their design elements are listed in
``scripts/svg_art/imperfect_cellular_automaton_art.py``. This module supplies
what publication needs.

* THE MOTION IS THE PERFECT ONE'S. She plays the Perfect Cellular Automaton's
  move table, so her rig has the perfect one's bone names and borrows its
  clips when a document loads (``_borrow_clips``). A clip's angles are added
  to her own rest pose: she does every move hunched. Her tail, her wings and
  the grid on her chest are hers, and ``_author_own_motion`` moves them.
* SHE IS NOT THE SAME ON HER TWO SIDES: one half is green and keeps the rule,
  the other is purple and is a fault. A flip of the sheet would move the
  fault to her other half each time she turns. So each row is published a
  second time, drawn from her other side and mirrored (``<row>~mirrored``),
  and the game draws that row when she faces left.
* THE GRID ON HER CHEST RUNS. The SVG has the live cells of each state as
  its own part (``grid_<n>``), and each frame shows the next state.

Publish:

    ./scripts/regen/sprites.sh --target imperfect_cellular_automaton
"""

from __future__ import annotations

import copy
import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image

from ...authoring import rigdoc
from ...authoring.part_flipbook import publish_rig_flipbook
from ...authoring.rigdoc import RigDocument, sample_channel_spec
from ...authoring.sheet_build import build_sheet, write_canonical
from ._svg_fighter_effects import compose_rig_frame
from .pca_combat_authoring import author_pca_combat_clips
from .pca_effects import EFFECTFUL_ANIMATIONS, draw_pca_behind, draw_pca_front
from .pca_motion import PCA_ROWS

TARGET_NAME = "imperfect_cellular_automaton"
_RIGGED = Path(__file__).resolve().parent / "rigged"
RIG_PATH = _RIGGED / "imperfect_cellular_automaton" / "imperfect_cellular_automaton.rig.json"
FAULT_SIDE_RIG_PATH = _RIGGED / "imperfect_cellular_automaton" / "imperfect_cellular_automaton_fault_side.rig.json"
PERFECT_RIG_PATH = _RIGGED / "perfect_cellular_automaton.rig.json"

RIG_SIZE = (160, 192)
RENDER_SCALE = 2
#: Room about the rig frame for her tail and for a reach, in rig units.
PADDING = 45
FRAME_SIZE = ((RIG_SIZE[0] + 2 * PADDING) * RENDER_SCALE, (RIG_SIZE[1] + 2 * PADDING) * RENDER_SCALE)
RIG_RENDER_SUPERSAMPLE = 2

MIRRORED = "{}~mirrored"
#: The rows she is drawn in, of the perfect one's.
BASE_ROWS: List[Tuple[str, int, int]] = list(PCA_ROWS)
MIRROR_OF: Dict[str, str] = {MIRRORED.format(name): name for name, _frames, _duration in BASE_ROWS}
ROWS: List[Tuple[str, int, int]] = BASE_ROWS + [
    (MIRRORED.format(name), frames, duration) for name, frames, duration in BASE_ROWS
]

#: The states of the grid on her chest (the ``grid_<n>`` parts of the SVG).
GRID_STATES = 8
TAIL_BONES = 7

#: Rows in which she is off the ground: her wings beat.
_AIR = frozenset({
    "jump", "double_jump", "fall", "fall_special", "tumble", "air_dodge", "air_neutral", "air_forward", "air_back",
    "air_up", "air_down", "fly", "hover", "float_glide", "wall_jump", "ledge_jump", "footstool_jump", "launch",
})
#: Rows in which her feet step on the ground. The perfect one's feet point
#: down and may turn far; hers are flat, so they turn half as far.
_GAIT = frozenset({"idle", "walk", "walk_stop", "turnaround", "dash_startup", "dash", "run", "crouch_walk", "stumble"})

ACTOR_METADATA = {
    "actor": {
        # Spelled out, not `TARGET_NAME`: the game's census of rendered
        # identities reads the id as text (`rendered_identities_are_registered`).
        "character_id": "imperfect_cellular_automaton",
        "display_name": "Imperfect Cellular Automaton",
    },
    "body": {
        "body_plan": "HumanoidBipedWithTail",
        "body_kind": "Floating",
        "traits": ["bio_android", "cellular_automaton", "aerial_melee", "mutable", "svg_rigged"],
    },
    "visual": {
        "default_pose": "idle",
        "facing_policy": "side_right_faces_positive_x",
    },
    "provenance": {
        "variant_family": TARGET_NAME,
        "variant_id": "opus_5_5_svg_rig_2026_10_13",
        "lineage": [
            {
                "revision_id": "legacy_unattributed",
                "creator_kind": "unknown",
                "creator": "unattributed",
                "contribution": "predecessor_design",
                "derived_from": "player_robot_fable",
                "certainty": "partial",
            },
            {
                "revision_id": "gpt_5_6_redesign_2026_07_15",
                "creator_kind": "model",
                "creator": "gpt-5.6-thinking",
                "contribution": "complete_visual_redesign_and_animation_polish",
                "parent_revision_id": "legacy_unattributed",
                "date": "2026-07-15",
            },
            {
                "revision_id": "gpt_5_6_zorder_polish_2026_07_15",
                "creator_kind": "model",
                "creator": "gpt-5.6-thinking",
                "contribution": "arm_visibility_zorder_contract_and_shadow_removal",
                "parent_revision_id": "gpt_5_6_redesign_2026_07_15",
                "date": "2026-07-15",
            },
            {
                "revision_id": "opus_5_5_svg_rig_2026_10_13",
                "creator_kind": "model",
                "creator": "claude-opus-5-5",
                "contribution": "redesign_as_a_two_sided_svg_rig_on_the_perfect_automatons_clips",
                "parent_revision_id": "gpt_5_6_zorder_polish_2026_07_15",
                "date": "2026-10-13",
            },
        ],
    },
    "tags": ["aerial", "enemy", "custom", "cellular", "mutable"],
    "authoring_description": (
        "Parody of Imperfect Cell from DBZ, combined with CS fun. The Imperfect Cellular Automaton "
        "personifies cellular-automaton mathematics as a character who sometimes violates its own local "
        "rule. It is a philosophical foil to the Perfect Cellular Automaton: asymmetry, mutation, "
        "accumulated exceptions, and emergent evolution are treated as identity rather than damage."
    ),
    "gameplay_description": (
        "Use as an adaptive enemy, unstable ally, mutation mechanic, or playable rule-breaker. "
        "Its state should visibly propagate across cells while occasional exceptions create "
        "abilities or futures that a flawless deterministic counterpart cannot reach."
    ),
    "dialogue_hints": {
        "barks": [
            "I follow my rule MOSTLY.",
            "The exceptions become the new rule.",
            "I'm the written-down noise.",
        ],
    },
}


def _keys(clip: dict, name: str, fn, samples: int = 9) -> None:
    """Key the channel ``name`` of ``clip`` from ``fn(t)``."""
    clip["channels"][name] = {"keys": [[i / (samples - 1), round(fn(i / (samples - 1)), 3), "sine"] for i in range(samples)]}


def _author_own_motion(clips: Dict[str, dict], rest_pitch: Dict[str, float]) -> None:
    """Move the parts the perfect one does not have, in every clip, and fit
    its steps to her feet."""
    for name, clip in clips.items():
        loop = bool(clip.get("loop", True))
        channels = clip.setdefault("channels", {})
        torso = channels.get("torso")

        # The tail. In a loop it sways from root to tip, twice in a stride. In
        # a move it goes against the turn of her torso, the tip last.
        for n in range(1, TAIL_BONES + 1):
            if loop:
                cycles = 2 if name in ("walk", "run", "crouch_walk") else 1
                channels[f"tail_{n}"] = {"expr": f"{1.2 + 0.25 * n:.2f}*sin(tau*({cycles}*t-{0.08 * n:.2f}))"}
            elif torso is not None:
                lag = 0.05 * n
                _keys(clip, f"tail_{n}", lambda t, lag=lag: -0.14 * sample_channel_spec(torso, max(0.0, t - lag), False))

        # The wings: they beat when she is off the ground, against each other.
        if name in _AIR:
            channels["wing_near"] = {"expr": "9+11*sin(tau*3*t)"}
            channels["wing_far"] = {"expr": "-9-11*sin(tau*3*t)"}
        elif loop:
            channels["wing_near"] = {"expr": "1.5*sin(tau*t)"}
            channels["wing_far"] = {"expr": "-1.5*sin(tau*(t-0.2))"}

        if name in _GAIT:
            for prefix, rest in rest_pitch.items():
                spec = channels.get(f"{prefix}_pitch")
                if spec is None:
                    continue
                if "const" in spec:
                    spec["const"] = rest + 0.5 * (float(spec["const"]) - rest)
                elif "keys" in spec:
                    spec["keys"] = [[key[0], round(rest + 0.5 * (float(key[1]) - rest), 3), *key[2:]] for key in spec["keys"]]


def _borrow_clips(doc: RigDocument) -> RigDocument:
    """Give ``doc`` the perfect one's clips, as its own target plays them,
    and then her own motion."""
    doc.data["clips"] = copy.deepcopy(json.loads(PERFECT_RIG_PATH.read_text())["clips"])
    author_pca_combat_clips(doc.data)
    rest_pitch = {str(leg["channel_prefix"]): float(leg["rest_pitch"]) for leg in doc.ik_legs}
    _author_own_motion(doc.data["clips"], rest_pitch)
    missing = [name for name, _frames, _duration in BASE_ROWS if name not in doc.clips]
    if missing:
        raise RuntimeError("the perfect automaton's rig has no clip for: " + ", ".join(missing[:12]))
    return doc


@lru_cache(maxsize=4)
def _load_doc_cached(path_text: str, mtime_ns: int, perfect_mtime_ns: int) -> RigDocument:
    # One document for the whole process: it owns the rasters of its parts.
    del mtime_ns, perfect_mtime_ns
    return _borrow_clips(RigDocument.load(path_text))


def _doc(fault_side: bool = False) -> RigDocument:
    path = FAULT_SIDE_RIG_PATH if fault_side else RIG_PATH
    return _load_doc_cached(str(path), path.stat().st_mtime_ns, PERFECT_RIG_PATH.stat().st_mtime_ns)


def _row(animation: str) -> Tuple[str, bool]:
    """The clip a sheet row plays, and whether the row is the other side of her."""
    original = MIRROR_OF.get(animation)
    return (original, True) if original is not None else (animation, False)


_ROW_INDEX = {name: index for index, (name, _frames, _duration) in enumerate(BASE_ROWS)}


def grid_state(row: str, frame_idx: int) -> int:
    """The state the grid on her chest shows in a frame. It goes on from row
    to row; both sides of her show the same state."""
    return (3 * _ROW_INDEX.get(row, 0) + frame_idx) % GRID_STATES


def _solve(row: str, mirrored: bool, frame_idx: int, frame_count: int):
    doc = _doc(mirrored)
    t = doc.frame_time(row, frame_idx, frame_count)
    world, params = doc.solve(row, t)
    params = dict(params)
    state = grid_state(row, frame_idx)
    params.update({f"grid_{n}": 1.0 if n == state else 0.0 for n in range(GRID_STATES)})
    return doc, t, (world, params)


def render_frame(animation: str, frame_idx: int, frame_count: int) -> Image.Image:
    row, mirrored = _row(animation)
    doc, t, solved = _solve(row, mirrored, frame_idx, frame_count)
    if row in EFFECTFUL_ANIMATIONS:
        # The effects of the perfect one's moves, about her own joints.
        frame = compose_rig_frame(
            doc,
            row,
            frame_idx,
            frame_count,
            solved=solved,
            behind=lambda canvas, t, world, params: draw_pca_behind(row, canvas, t, world, params),
            front=lambda canvas, t, world, params: draw_pca_front(row, canvas, t, world, params),
            padding=PADDING,
            rig_supersample=RIG_RENDER_SUPERSAMPLE,
        )
    else:
        frame = doc.render_at(row, t, solved=solved, padding=PADDING, supersample=RIG_RENDER_SUPERSAMPLE)
    # Mirrored about the centre of the frame: the published frame is what a
    # flip of the whole frame would place, so the game keeps one feet anchor.
    return rigdoc.mirrored_canvas(frame) if mirrored else frame


def _out_point(point) -> list:
    return [round((float(point[0]) + PADDING) * RENDER_SCALE, 3), round((float(point[1]) + PADDING) * RENDER_SCALE, 3)]


def frame_meta(animation: str, frame_idx: int, frame_count: int) -> dict:
    row, mirrored = _row(animation)
    _doc_, _t, (world, _params) = _solve(row, mirrored, frame_idx, frame_count)
    near, far = world["near_arm_hand"].origin, world["far_arm_hand"].origin
    forward, rear = (near, far) if near[0] >= far[0] else (far, near)
    anchors = {
        "cell_core": _out_point(world["torso"].origin),
        "pelvis": _out_point(world["pelvis"].origin),
        "head": _out_point(world["head"].origin),
        "forward_hand": _out_point(forward),
        "rear_hand": _out_point(rear),
        "near_foot": _out_point(world["near_leg_foot"].origin),
        "far_foot": _out_point(world["far_leg_foot"].origin),
        "sting": _out_point(world[f"tail_{TAIL_BONES}"].tip),
    }
    if mirrored:
        anchors = {name: [round(FRAME_SIZE[0] - x, 3), y] for name, (x, y) in anchors.items()}
    return {"anchors": {name: {"x": x, "y": y} for name, (x, y) in anchors.items()}}


def body_metrics(fw: int, fh: int) -> dict:
    """Her body, authored: from the ground to the top of her skull, as wide as
    her trunk. Her crown, her tail and her arms are not her body."""
    x, y, w, h = 58, 46, 46, 130
    feet_x = float((80 + PADDING) * RENDER_SCALE)
    feet_y = float((176 + PADDING) * RENDER_SCALE)
    return {
        "body_pixel_bbox": {
            "x": (x + PADDING) * RENDER_SCALE,
            "y": (y + PADDING) * RENDER_SCALE,
            "w": w * RENDER_SCALE,
            "h": h * RENDER_SCALE,
        },
        "feet_pixel": {"x": feet_x, "y": feet_y},
        "feet_anchor_norm": {"x": round(feet_x / fw - 0.5, 6), "y": round(0.5 - feet_y / fh, 6)},
    }


def render(out_dir: str | Path, **opts) -> List[Path]:
    del opts
    frame_transform: dict = {}
    outputs = build_sheet(
        frame_transform_out=frame_transform,
        target=TARGET_NAME,
        rows=ROWS,
        render_fn=render_frame,
        out_dir=Path(out_dir),
        frame_size=FRAME_SIZE,
        frame_meta_fn=frame_meta,
        auto_crop=False,
        actor_metadata=ACTOR_METADATA,
        body_metrics_fn=body_metrics,
        sheet_tuning={"collision_scale": 1.12, "frame_sample_inset": 1},
        animation_key_map={name: name for name, _frames, _duration in BASE_ROWS},
        mirror_of=MIRROR_OF,
    )
    keys = ("spritesheet", "yaml", "ron", "actor", "canonical", "canonical_transparent", "preview")
    parts = publish_rig_flipbook(TARGET_NAME, ROWS, render_frame, outputs, frame_transform, Path(out_dir))
    return [Path(outputs[key]) for key in keys if outputs.get(key)] + list(parts.values())


def render_canonical(out_dir: str | Path, **opts):
    del opts
    return write_canonical(TARGET_NAME, ROWS, render_frame, Path(out_dir), frame_size=FRAME_SIZE)


__all__ = [
    "ACTOR_METADATA",
    "FRAME_SIZE",
    "MIRROR_OF",
    "ROWS",
    "TARGET_NAME",
    "body_metrics",
    "frame_meta",
    "grid_state",
    "render",
    "render_canonical",
    "render_frame",
]
