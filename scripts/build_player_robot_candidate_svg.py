from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Sequence, Tuple

from ambition_sprite2d_renderer.authoring.humanoid_svg_rig import (
    HumanoidViewSpec,
    build_humanoid_view_document,
)

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "ambition_sprite2d_renderer"
SVG_PATH = (
    PKG
    / "data/characters/player_robot_candidate_svg/player-robot-candidate-rigged.svg"
)
RIG_DIR = PKG / "targets/characters/rigged/player_robot_candidate_svg"
RIG_JSON = RIG_DIR / "player_robot_candidate_side.rig.json"
VIEW_LABEL = "Player Robot Candidate - Side Right"

Pair = Tuple[float, float]


def K(*pairs: Pair) -> Dict[str, list[list[float]]]:
    return {"keys": [[float(t), float(v)] for t, v in pairs]}


def C(value: float) -> Dict[str, float]:
    return {"const": float(value)}


def _chain(doc: dict, side: str) -> dict:
    return next(
        c for c in doc["ik_chains"] if c["channel_prefix"] == f"{side}_hand"
    )


def _leg(doc: dict, side: str) -> dict:
    return next(
        c for c in doc["ik_legs"] if c["channel_prefix"] == f"{side}_foot"
    )


def make_clips(doc: dict) -> dict:
    nh = _chain(doc, "near")
    fh = _chain(doc, "far")
    nl = _leg(doc, "near")
    fl = _leg(doc, "far")

    nx, ny, np = nh["rest_x"], nh["rest_y"], nh["rest_pitch"]
    fx, fy, fp = fh["rest_x"], fh["rest_y"], fh["rest_pitch"]
    nfx, nfl, nfp = nl["rest_x"], nl["rest_lift"], nl["rest_pitch"]
    ffx, ffl, ffp = fl["rest_x"], fl["rest_lift"], fl["rest_pitch"]

    return {
        "idle": {
            "loop": True,
            "frames": 8,
            "duration_ms": 120,
            "channels": {
                "root_y": K((0.0, 0.0), (0.25, 0.7), (0.5, 0.0), (0.75, -0.5), (1.0, 0.0)),
                "pelvis": K((0.0, 0.0), (0.5, 0.8), (1.0, 0.0)),
                "torso": K((0.0, 0.0), (0.5, -1.1), (1.0, 0.0)),
                "head": K((0.0, 0.0), (0.5, 1.0), (1.0, 0.0)),
                "near_hand_x": K((0.0, nx), (0.5, nx + 0.4), (1.0, nx)),
                "near_hand_y": K((0.0, ny), (0.5, ny + 0.5), (1.0, ny)),
                "near_hand_pitch": K((0.0, np), (0.5, np + 1.5), (1.0, np)),
                "far_hand_x": K((0.0, fx), (0.5, fx - 0.3), (1.0, fx)),
                "far_hand_y": K((0.0, fy), (0.5, fy + 0.4), (1.0, fy)),
                "far_hand_pitch": K((0.0, fp), (0.5, fp - 1.2), (1.0, fp)),
            },
        },
        "walk": {
            "loop": True,
            "frames": 8,
            "duration_ms": 95,
            "channels": {
                "root_y": K((0.0, 0.2), (0.25, 0.9), (0.5, 0.2), (0.75, -0.4), (1.0, 0.2)),
                "pelvis": K((0.0, 1.5), (0.25, -1.0), (0.5, -1.5), (0.75, 1.0), (1.0, 1.5)),
                "torso": K((0.0, -1.0), (0.25, 0.7), (0.5, 1.0), (0.75, -0.7), (1.0, -1.0)),
                "head": K((0.0, 0.7), (0.25, -0.4), (0.5, -0.7), (0.75, 0.4), (1.0, 0.7)),
                "near_foot_x": K((0.0, nfx + 5.0), (0.25, nfx + 1.0), (0.5, nfx - 5.0), (0.75, nfx - 1.0), (1.0, nfx + 5.0)),
                "near_foot_lift": K((0.0, nfl), (0.25, nfl), (0.5, nfl), (0.75, nfl + 4.3), (1.0, nfl)),
                "near_foot_pitch": K((0.0, nfp - 8.0), (0.25, nfp), (0.5, nfp + 10.0), (0.75, nfp - 12.0), (1.0, nfp - 8.0)),
                "far_foot_x": K((0.0, ffx - 5.0), (0.25, ffx - 1.0), (0.5, ffx + 5.0), (0.75, ffx + 1.0), (1.0, ffx - 5.0)),
                "far_foot_lift": K((0.0, ffl), (0.25, ffl + 4.3), (0.5, ffl), (0.75, ffl), (1.0, ffl)),
                "far_foot_pitch": K((0.0, ffp + 10.0), (0.25, ffp - 12.0), (0.5, ffp - 8.0), (0.75, ffp), (1.0, ffp + 10.0)),
                "near_hand_x": K((0.0, nx - 3.5), (0.25, nx), (0.5, nx + 3.5), (0.75, nx), (1.0, nx - 3.5)),
                "near_hand_y": K((0.0, ny), (0.25, ny + 0.5), (0.5, ny), (0.75, ny - 0.5), (1.0, ny)),
                "near_hand_pitch": K((0.0, np - 8.0), (0.5, np + 8.0), (1.0, np - 8.0)),
                "far_hand_x": K((0.0, fx + 3.5), (0.25, fx), (0.5, fx - 3.5), (0.75, fx), (1.0, fx + 3.5)),
                "far_hand_y": K((0.0, fy), (0.25, fy - 0.5), (0.5, fy), (0.75, fy + 0.5), (1.0, fy)),
                "far_hand_pitch": K((0.0, fp + 8.0), (0.5, fp - 8.0), (1.0, fp + 8.0)),
            },
        },
        "run": {
            "loop": True,
            "frames": 8,
            "duration_ms": 75,
            "channels": {
                "root_y": K((0.0, 0.8), (0.25, 1.6), (0.5, 0.2), (0.75, -0.8), (1.0, 0.8)),
                "pelvis": K((0.0, 3.0), (0.25, -2.0), (0.5, -3.0), (0.75, 2.0), (1.0, 3.0)),
                "torso": K((0.0, 7.0), (0.25, 5.0), (0.5, 7.0), (0.75, 9.0), (1.0, 7.0)),
                "head": K((0.0, -3.0), (0.25, -2.0), (0.5, -3.0), (0.75, -4.0), (1.0, -3.0)),
                "near_foot_x": K((0.0, nfx + 8.0), (0.25, nfx + 1.0), (0.5, nfx - 7.0), (0.75, nfx - 1.0), (1.0, nfx + 8.0)),
                "near_foot_lift": K((0.0, nfl), (0.25, nfl), (0.5, nfl), (0.75, nfl + 6.5), (1.0, nfl)),
                "near_foot_pitch": K((0.0, nfp - 10.0), (0.25, nfp), (0.5, nfp + 14.0), (0.75, nfp - 18.0), (1.0, nfp - 10.0)),
                "far_foot_x": K((0.0, ffx - 7.0), (0.25, ffx - 1.0), (0.5, ffx + 8.0), (0.75, ffx + 1.0), (1.0, ffx - 7.0)),
                "far_foot_lift": K((0.0, ffl), (0.25, ffl + 6.5), (0.5, ffl), (0.75, ffl), (1.0, ffl)),
                "far_foot_pitch": K((0.0, ffp + 14.0), (0.25, ffp - 18.0), (0.5, ffp - 10.0), (0.75, ffp), (1.0, ffp + 14.0)),
                "near_hand_x": K((0.0, nx - 5.5), (0.25, nx), (0.5, nx + 6.0), (0.75, nx), (1.0, nx - 5.5)),
                "near_hand_y": K((0.0, ny - 1.0), (0.25, ny), (0.5, ny + 1.0), (0.75, ny), (1.0, ny - 1.0)),
                "near_hand_pitch": K((0.0, np - 14.0), (0.5, np + 15.0), (1.0, np - 14.0)),
                "far_hand_x": K((0.0, fx + 5.5), (0.25, fx), (0.5, fx - 6.0), (0.75, fx), (1.0, fx + 5.5)),
                "far_hand_y": K((0.0, fy + 1.0), (0.25, fy), (0.5, fy - 1.0), (0.75, fy), (1.0, fy + 1.0)),
                "far_hand_pitch": K((0.0, fp + 15.0), (0.5, fp - 14.0), (1.0, fp + 15.0)),
            },
        },
        "jump": {
            "loop": False,
            "frames": 6,
            "duration_ms": 80,
            "channels": {
                "root_y": K((0.0, 0.0), (0.2, 2.0), (0.42, -4.0), (1.0, -9.0)),
                "pelvis": K((0.0, 0.0), (0.2, -5.0), (0.42, 3.0), (1.0, 4.0)),
                "torso": K((0.0, 0.0), (0.2, -6.0), (0.42, 7.0), (1.0, 5.0)),
                "head": K((0.0, 0.0), (0.2, -2.0), (0.42, 3.0), (1.0, 2.0)),
                "near_foot_x": K((0.0, nfx), (0.2, nfx), (0.42, nfx + 1.0), (1.0, nfx + 2.0)),
                "near_foot_lift": K((0.0, nfl), (0.2, nfl), (0.42, nfl + 4.0), (1.0, nfl + 8.0)),
                "near_foot_pitch": K((0.0, nfp), (0.42, nfp + 10.0), (1.0, nfp + 5.0)),
                "far_foot_x": K((0.0, ffx), (0.2, ffx), (0.42, ffx - 1.0), (1.0, ffx - 2.0)),
                "far_foot_lift": K((0.0, ffl), (0.2, ffl), (0.42, ffl + 3.5), (1.0, ffl + 7.0)),
                "far_foot_pitch": K((0.0, ffp), (0.42, ffp + 8.0), (1.0, ffp + 4.0)),
                "near_hand_x": K((0.0, nx), (0.2, nx - 2.0), (0.42, nx + 2.0), (1.0, nx + 3.0)),
                "near_hand_y": K((0.0, ny), (0.2, ny + 2.0), (0.42, ny - 4.0), (1.0, ny - 6.0)),
                "near_hand_pitch": K((0.0, np), (0.42, np - 20.0), (1.0, np - 32.0)),
                "far_hand_x": K((0.0, fx), (0.2, fx + 2.0), (0.42, fx - 2.0), (1.0, fx - 3.0)),
                "far_hand_y": K((0.0, fy), (0.2, fy + 2.0), (0.42, fy - 3.0), (1.0, fy - 5.0)),
                "far_hand_pitch": K((0.0, fp), (0.42, fp + 18.0), (1.0, fp + 28.0)),
            },
        },
        "fall": {
            "loop": True,
            "frames": 6,
            "duration_ms": 85,
            "channels": {
                "root_y": C(-8.0),
                "pelvis": K((0.0, 3.0), (0.5, 4.0), (1.0, 3.0)),
                "torso": K((0.0, 5.0), (0.5, 4.0), (1.0, 5.0)),
                "head": K((0.0, 2.0), (0.5, 1.0), (1.0, 2.0)),
                "near_foot_x": C(nfx + 1.0),
                "near_foot_lift": C(nfl + 7.0),
                "near_foot_pitch": C(nfp - 5.0),
                "far_foot_x": C(ffx - 1.0),
                "far_foot_lift": C(ffl + 6.0),
                "far_foot_pitch": C(ffp - 3.0),
                "near_hand_x": C(nx + 2.0),
                "near_hand_y": C(ny - 1.0),
                "near_hand_pitch": C(np + 12.0),
                "far_hand_x": C(fx - 2.0),
                "far_hand_y": C(fy - 1.0),
                "far_hand_pitch": C(fp - 12.0),
            },
        },
        "dash": {
            "loop": False,
            "frames": 6,
            "duration_ms": 62,
            "channels": {
                "root_y": K((0.0, 1.0), (0.25, 2.0), (0.6, 0.5), (1.0, 0.0)),
                "pelvis": K((0.0, 6.0), (0.25, 10.0), (0.6, 8.0), (1.0, 3.0)),
                "torso": K((0.0, 10.0), (0.25, 18.0), (0.6, 15.0), (1.0, 7.0)),
                "head": K((0.0, -4.0), (0.25, -7.0), (0.6, -5.0), (1.0, -2.0)),
                "near_foot_x": K((0.0, nfx + 3.0), (0.25, nfx + 5.0), (1.0, nfx + 2.0)),
                "near_foot_lift": C(nfl),
                "near_foot_pitch": K((0.0, nfp - 4.0), (0.25, nfp + 5.0), (1.0, nfp)),
                "far_foot_x": K((0.0, ffx - 3.0), (0.25, ffx - 5.0), (1.0, ffx - 2.0)),
                "far_foot_lift": C(ffl),
                "far_foot_pitch": K((0.0, ffp + 3.0), (0.25, ffp + 8.0), (1.0, ffp)),
                "near_hand_x": K((0.0, nx - 1.0), (0.25, nx - 6.0), (0.6, nx - 5.0), (1.0, nx - 2.0)),
                "near_hand_y": K((0.0, ny), (0.25, ny - 2.0), (0.6, ny - 1.5), (1.0, ny)),
                "near_hand_pitch": K((0.0, np), (0.25, np + 18.0), (0.6, np + 12.0), (1.0, np)),
                "far_hand_x": K((0.0, fx - 1.0), (0.25, fx - 5.0), (0.6, fx - 4.0), (1.0, fx - 1.0)),
                "far_hand_y": K((0.0, fy), (0.25, fy - 2.0), (0.6, fy - 1.5), (1.0, fy)),
                "far_hand_pitch": K((0.0, fp), (0.25, fp + 14.0), (0.6, fp + 10.0), (1.0, fp)),
            },
        },
        "attack_side": {
            "loop": False,
            "frames": 7,
            "duration_ms": 62,
            "channels": {
                "root_x": K((0.0, 0.0), (0.22, -1.0), (0.46, 2.5), (0.7, 3.0), (1.0, 0.5)),
                "root_y": K((0.0, 0.0), (0.22, 1.0), (0.46, 0.0), (1.0, 0.0)),
                "pelvis": K((0.0, 0.0), (0.22, -8.0), (0.46, 10.0), (0.7, 12.0), (1.0, 2.0)),
                "torso": K((0.0, 0.0), (0.22, -12.0), (0.46, 16.0), (0.7, 12.0), (1.0, 2.0)),
                "head": K((0.0, 0.0), (0.22, -4.0), (0.46, 5.0), (0.7, 3.0), (1.0, 0.0)),
                "near_foot_x": K((0.0, nfx), (0.46, nfx + 2.5), (1.0, nfx + 1.0)),
                "far_foot_x": K((0.0, ffx), (0.46, ffx - 2.0), (1.0, ffx - 1.0)),
                "near_hand_x": K((0.0, nx), (0.22, nx - 7.0), (0.46, nx + 9.0), (0.7, nx + 12.0), (1.0, nx + 1.0)),
                "near_hand_y": K((0.0, ny), (0.22, ny - 5.0), (0.46, ny - 1.0), (0.7, ny + 1.0), (1.0, ny)),
                "near_hand_pitch": K((0.0, np), (0.22, np - 48.0), (0.46, np + 8.0), (0.7, np + 14.0), (1.0, np)),
                "far_hand_x": K((0.0, fx), (0.22, fx + 3.0), (0.46, fx - 3.0), (1.0, fx)),
                "far_hand_y": K((0.0, fy), (0.22, fy + 2.0), (0.46, fy - 1.0), (1.0, fy)),
                "far_hand_pitch": K((0.0, fp), (0.22, fp - 10.0), (0.46, fp + 6.0), (1.0, fp)),
            },
        },
        "attack_up": {
            "loop": False,
            "frames": 6,
            "duration_ms": 68,
            "channels": {
                "root_y": K((0.0, 0.0), (0.25, 1.0), (0.5, -0.5), (1.0, 0.0)),
                "pelvis": K((0.0, 0.0), (0.25, -4.0), (0.5, 4.0), (1.0, 0.0)),
                "torso": K((0.0, 0.0), (0.25, -7.0), (0.5, -4.0), (1.0, 0.0)),
                "head": K((0.0, 0.0), (0.25, -8.0), (0.5, -15.0), (1.0, -4.0)),
                "near_hand_x": K((0.0, nx), (0.25, nx - 3.0), (0.5, nx - 1.0), (0.7, nx + 1.0), (1.0, nx)),
                "near_hand_y": K((0.0, ny), (0.25, ny - 6.0), (0.5, ny - 15.0), (0.7, ny - 18.0), (1.0, ny - 5.0)),
                "near_hand_pitch": K((0.0, np), (0.25, np - 45.0), (0.5, -90.0), (0.7, -100.0), (1.0, np - 20.0)),
                "far_hand_x": K((0.0, fx), (0.5, fx - 2.0), (1.0, fx)),
                "far_hand_y": K((0.0, fy), (0.5, fy - 2.0), (1.0, fy)),
            },
        },
        "air_back": {
            "loop": False,
            "frames": 6,
            "duration_ms": 68,
            "channels": {
                "root_y": C(-7.0),
                "pelvis": K((0.0, 4.0), (0.3, 8.0), (0.55, -6.0), (1.0, -2.0)),
                "torso": K((0.0, 6.0), (0.3, 12.0), (0.55, -12.0), (1.0, -4.0)),
                "head": K((0.0, 3.0), (0.3, 8.0), (0.55, -15.0), (1.0, -7.0)),
                "near_foot_x": C(nfx + 1.0),
                "near_foot_lift": C(nfl + 6.0),
                "far_foot_x": C(ffx - 1.0),
                "far_foot_lift": C(ffl + 5.0),
                "near_hand_x": K((0.0, nx), (0.3, nx - 7.0), (0.55, nx - 12.0), (0.75, nx - 9.0), (1.0, nx - 2.0)),
                "near_hand_y": K((0.0, ny - 1.0), (0.3, ny - 5.0), (0.55, ny + 1.0), (0.75, ny + 3.0), (1.0, ny)),
                "near_hand_pitch": K((0.0, np), (0.3, np - 45.0), (0.55, 145.0), (0.75, 125.0), (1.0, np + 20.0)),
                "far_hand_x": K((0.0, fx), (0.55, fx + 4.0), (1.0, fx)),
                "far_hand_y": K((0.0, fy), (0.55, fy - 2.0), (1.0, fy)),
            },
        },
    }


def build_doc_map() -> dict:
    spec = HumanoidViewSpec(
        view=VIEW_LABEL,
        name="player_robot_candidate_side",
        target_height=108.0,
        collision_scale=1.65,
    )
    RIG_DIR.mkdir(parents=True, exist_ok=True)
    doc = build_humanoid_view_document(SVG_PATH, RIG_DIR, spec)
    doc["clips"] = make_clips(doc)
    return doc


def cmd_build() -> None:
    doc = build_doc_map()
    RIG_JSON.write_text(json.dumps(doc, indent=2))
    print(RIG_JSON)


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", nargs="?", default="build", choices=["build"])
    args = parser.parse_args(argv)
    if args.command == "build":
        cmd_build()


if __name__ == "__main__":
    main()
