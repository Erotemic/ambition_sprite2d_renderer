#!/usr/bin/env python3
"""Build the author-only paper-doll rig used by the vanity card.

This rig is deliberately outside ``targets/characters/rigged``.  It is an
animation source for the vanity card, not a game actor and not a registry
target.  The hand-authored SVG remains the source of truth; this script binds
its labelled parts and joint markers to the shared humanoid rig document.

Usage::

    uv run python scripts/build_author_vanity_rig.py build
    uv run python scripts/build_author_vanity_rig.py build --fresh
    uv run python scripts/build_author_vanity_rig.py validate
    uv run python scripts/build_author_vanity_rig.py preview

Open the result in the editor with::

    uv run --extra gui python -m ambition_sprite2d_renderer.gui \
        assets/rigs/author_vanity/author_vanity.rig.json
"""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

from ambition_sprite2d_renderer.authoring.humanoid_svg_rig import (
    HumanoidViewSpec,
    build_humanoid_view_document,
    merge_generated_geometry,
)
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument, render_gifs_for_doc

ROOT = Path(__file__).resolve().parents[1]
SVG_PATH = ROOT / "assets/author-rig-labels-joints.svg"
RIG_DIR = ROOT / "assets/rigs/author_vanity"
RIG_PATH = RIG_DIR / "author_vanity.rig.json"
SCRATCH = ROOT / "agent-scratch/author_vanity"
VIEW_LABEL = "Author - Side West"

INK_LABEL = "{http://www.inkscape.org/namespaces/inkscape}label"
INK_GROUPMODE = "{http://www.inkscape.org/namespaces/inkscape}groupmode"
DRAWABLE = {"path", "polygon", "rect", "ellipse", "circle", "line", "image"}

EXPECTED_PARTS = {
    "neck",
    "far_arm_u",
    "far_arm_l",
    "far_sleeve",
    "far_hand",
    "far_foot",
    "far_leg_u",
    "far_leg_l",
    "far_cuff",
    "near_foot",
    "near_leg_u",
    "near_leg_l",
    "near_cuff",
    "pelvis",
    "torso",
    "near_arm_u",
    "near_arm_l",
    "near_sleeve",
    "near_hand",
    "head",
}
EXPECTED_JOINTS = {
    "waist",
    "neck",
    *{
        f"{side}_{joint}"
        for side in ("near", "far")
        for joint in (
            "shoulder",
            "elbow",
            "wrist",
            "handtip",
            "hip",
            "knee",
            "ankle",
            "toe",
        )
    },
}

SPEC = HumanoidViewSpec(
    view=VIEW_LABEL,
    name="author_vanity",
    frame_width=256,
    frame_height=320,
    center_x=128.0,
    ground_y=304.0,
    target_height=270.0,
    ref_dpi=25.4,
    supersample=4,
    render_scale=1,
    collision_scale=1.0,
)


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def validate_svg() -> None:
    root = ET.fromstring(SVG_PATH.read_bytes())
    if root.get("data-asset-role") != "vanity-card-animation":
        raise ValueError("author SVG must declare data-asset-role=vanity-card-animation")

    view = next((elem for elem in root.iter() if elem.get(INK_LABEL) == VIEW_LABEL), None)
    if view is None:
        raise ValueError(f"author SVG is missing view layer {VIEW_LABEL!r}")
    if view.get(INK_GROUPMODE) != "layer":
        raise ValueError("author view must be an Inkscape layer")

    parts = [elem for elem in view.iter() if elem.get("data-rig-part")]
    part_names = [str(elem.get("data-rig-part")) for elem in parts]
    if len(part_names) != len(set(part_names)):
        raise ValueError("author SVG contains duplicate data-rig-part names")
    if set(part_names) != EXPECTED_PARTS:
        raise ValueError(
            "author SVG part contract differs: "
            f"missing={sorted(EXPECTED_PARTS - set(part_names))}, "
            f"extra={sorted(set(part_names) - EXPECTED_PARTS)}"
        )

    ids: set[str] = set()
    for elem in view.iter():
        eid = elem.get("id")
        if eid:
            if eid in ids:
                raise ValueError(f"duplicate SVG id {eid!r}")
            ids.add(eid)

    for part in parts:
        if not part.get("data-rig-bone") or part.get("data-rig-z") is None:
            raise ValueError(f"part {part.get('data-rig-part')!r} lacks rig metadata")
        if not part.get(INK_LABEL):
            raise ValueError(f"part {part.get('data-rig-part')!r} lacks a human label")
        drawables = [elem for elem in part.iter() if _local(elem.tag) in DRAWABLE]
        if not drawables:
            raise ValueError(f"part {part.get('data-rig-part')!r} contains no art")
        missing_ids = [elem for elem in drawables if not elem.get("id")]
        if missing_ids:
            raise ValueError(
                f"part {part.get('data-rig-part')!r} contains drawables without stable ids"
            )

    joints = [elem for elem in view.iter() if elem.get("data-rig-joint")]
    joint_names = [str(elem.get("data-rig-joint")) for elem in joints]
    if len(joint_names) != len(set(joint_names)):
        raise ValueError("author SVG contains duplicate data-rig-joint names")
    if set(joint_names) != EXPECTED_JOINTS:
        raise ValueError(
            "author SVG joint contract differs: "
            f"missing={sorted(EXPECTED_JOINTS - set(joint_names))}, "
            f"extra={sorted(set(joint_names) - EXPECTED_JOINTS)}"
        )


def _keys(*items: tuple[float, float] | tuple[float, float, str]) -> dict:
    return {"keys": [list(item) for item in items]}


def _rest_targets(doc: dict) -> dict[str, float]:
    values: dict[str, float] = {}
    for chain in doc.get("ik_chains", []):
        prefix = str(chain["channel_prefix"])
        values[f"{prefix}_x"] = float(chain.get("rest_x", 0.0))
        values[f"{prefix}_y"] = float(chain.get("rest_y", 0.0))
        values[f"{prefix}_pitch"] = float(chain.get("rest_pitch", 0.0))
        values[f"{prefix}_bend"] = float(chain.get("bend", 1.0))
    for leg in doc.get("ik_legs", []):
        prefix = str(leg["channel_prefix"])
        values[f"{prefix}_x"] = float(leg.get("rest_x", 0.0))
        values[f"{prefix}_lift"] = float(leg.get("rest_lift", 0.0))
        values[f"{prefix}_pitch"] = float(leg.get("rest_pitch", 0.0))
        values[f"{prefix}_bend"] = float(leg.get("bend", 1.0))
    return values


def default_clips(doc: dict) -> dict[str, dict]:
    """Small vanity-card vocabulary, not the gameplay animation vocabulary."""
    r = _rest_targets(doc)
    nx, ny, np = r["near_hand_x"], r["near_hand_y"], r["near_hand_pitch"]
    fx, fy, fp = r["far_hand_x"], r["far_hand_y"], r["far_hand_pitch"]

    idle = {
        "loop": True,
        "frames": 48,
        "duration_ms": 50,
        "channels": {
            "root_y": {"expr": "-0.85 + 0.85*cos(tau*t)"},
            "torso": {"expr": "0.9*sin(tau*t)"},
            "head": {"expr": "-0.55*sin(tau*t + 0.35)"},
            "near_hand_x": {"expr": f"{nx:.4f} + 0.35*sin(tau*t + 0.2)"},
            "near_hand_y": {"expr": f"{ny:.4f} - 0.55 + 0.55*cos(tau*t)"},
            "near_hand_pitch": {"expr": f"{np:.4f} - 0.6*sin(tau*t)"},
            "far_hand_x": {"expr": f"{fx:.4f} - 0.25*sin(tau*t + 0.2)"},
            "far_hand_y": {"expr": f"{fy:.4f} - 0.45 + 0.45*cos(tau*t)"},
            "far_hand_pitch": {"expr": f"{fp:.4f} + 0.45*sin(tau*t)"},
        },
    }

    wave = {
        "loop": False,
        "frames": 36,
        "duration_ms": 50,
        "channels": {
            "root_y": _keys((0.0, 0.0, "smooth"), (0.25, -1.2, "smooth"), (0.78, -0.8, "smooth"), (1.0, 0.0)),
            "torso": _keys((0.0, 0.0, "smooth"), (0.25, -1.8, "smooth"), (0.72, -1.0, "smooth"), (1.0, 0.0)),
            "head": _keys((0.0, 0.0, "smooth"), (0.22, 2.0, "smooth"), (0.42, -2.5, "smooth"), (0.68, 1.6, "smooth"), (1.0, 0.0)),
            "near_hand_x": _keys((0.0, nx, "smooth"), (0.22, nx + 13.0, "smooth"), (0.74, nx + 11.0, "smooth"), (1.0, nx)),
            "near_hand_y": _keys((0.0, ny, "smooth"), (0.22, ny - 54.0, "smooth"), (0.74, ny - 51.0, "smooth"), (1.0, ny)),
            "near_hand_pitch": _keys((0.0, np, "smooth"), (0.22, -88.0, "smooth"), (0.36, -108.0, "smooth"), (0.50, -76.0, "smooth"), (0.64, -106.0, "smooth"), (0.76, -84.0, "smooth"), (1.0, np)),
            "far_hand_x": {"const": fx},
            "far_hand_y": _keys((0.0, fy, "smooth"), (0.3, fy - 1.5, "smooth"), (1.0, fy)),
            "far_hand_pitch": {"const": fp},
        },
    }

    receive = {
        "loop": False,
        "frames": 40,
        "duration_ms": 50,
        "channels": {
            "root_y": _keys((0.0, 0.0, "smooth"), (0.38, -1.5, "smooth"), (0.72, -1.0, "smooth"), (1.0, 0.0)),
            "torso": _keys((0.0, 0.0, "smooth"), (0.38, -4.5, "smooth"), (0.72, -3.0, "smooth"), (1.0, -1.5)),
            "head": _keys((0.0, 0.0, "smooth"), (0.28, 5.0, "smooth"), (0.56, 1.0, "smooth"), (1.0, 0.0)),
            "near_hand_x": _keys((0.0, nx, "smooth"), (0.45, -4.0, "smooth"), (1.0, -4.0)),
            "near_hand_y": _keys((0.0, ny, "smooth"), (0.45, -147.0, "smooth"), (1.0, -147.0)),
            "near_hand_pitch": _keys((0.0, np, "smooth"), (0.45, 168.0, "smooth"), (1.0, 168.0)),
            "far_hand_x": _keys((0.0, fx, "smooth"), (0.45, -34.0, "smooth"), (1.0, -34.0)),
            "far_hand_y": _keys((0.0, fy, "smooth"), (0.45, -145.0, "smooth"), (1.0, -145.0)),
            "far_hand_pitch": _keys((0.0, fp, "smooth"), (0.45, 160.0, "smooth"), (1.0, 160.0)),
        },
    }

    return {
        "vanity_idle": idle,
        "vanity_wave": wave,
        "vanity_receive": receive,
    }


def generated_doc() -> dict:
    validate_svg()
    RIG_DIR.mkdir(parents=True, exist_ok=True)
    doc = build_humanoid_view_document(SVG_PATH, RIG_DIR, SPEC)
    doc["clips"] = default_clips(doc)
    doc["features"] = {
        "paper_doll": True,
        "authoring_only": True,
        "vanity_card_only": True,
        "registered_game_target": False,
        "facing": "west",
    }
    doc["asset_metadata"] = {
        "purpose": "smooth vanity-card animation",
        "character": "author",
        "source_kind": "hand-traced SVG",
    }
    return doc


def build(*, fresh: bool = False) -> Path:
    generated = generated_doc()
    if RIG_PATH.exists() and not fresh:
        existing = json.loads(RIG_PATH.read_text(encoding="utf8"))
        doc = merge_generated_geometry(existing, generated)
        clips = doc.setdefault("clips", {})
        for name, clip in generated["clips"].items():
            clips.setdefault(name, clip)
        doc["features"] = generated["features"]
        doc["asset_metadata"] = generated["asset_metadata"]
    else:
        doc = generated
    RIG_PATH.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf8")
    return RIG_PATH


def cmd_build(args: argparse.Namespace) -> None:
    print(build(fresh=args.fresh))


def cmd_validate(args: argparse.Namespace) -> None:
    path = build(fresh=args.fresh)
    doc = RigDocument.load(path)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    for clip, frames, _duration in doc.rows():
        images = [doc.render_frame(clip, i, frames) for i in range(frames)]
        if any(image.getchannel("A").getbbox() is None for image in images):
            raise RuntimeError(f"{clip!r} produced an empty frame")
        sample_indices = sorted({0, max(0, frames // 4), max(0, frames // 2), max(0, 3 * frames // 4), frames - 1})
        samples = [images[index] for index in sample_indices]
        strip = Image.new("RGBA", (sum(im.width for im in samples), samples[0].height), (0, 0, 0, 0))
        x = 0
        for image in samples:
            strip.alpha_composite(image, (x, 0))
            x += image.width
        out = SCRATCH / f"author_vanity_{clip}_samples.png"
        strip.save(out)
        print(out)


def cmd_preview(args: argparse.Namespace) -> None:
    path = build(fresh=args.fresh)
    doc = RigDocument.load(path)
    for output in render_gifs_for_doc(doc, SCRATCH, scale=args.scale):
        print(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    build_parser = sub.add_parser("build")
    build_parser.add_argument("--fresh", action="store_true")
    build_parser.set_defaults(func=cmd_build)
    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("--fresh", action="store_true")
    validate_parser.set_defaults(func=cmd_validate)
    preview_parser = sub.add_parser("preview")
    preview_parser.add_argument("--fresh", action="store_true")
    preview_parser.add_argument("--scale", type=int, default=1)
    preview_parser.set_defaults(func=cmd_preview)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
