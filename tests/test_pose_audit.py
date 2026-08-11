from __future__ import annotations

from pathlib import Path

from ambition_sprite2d_renderer.authoring.pose_audit import (
    audit_document,
    run_pose_audit,
)
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.cli.parser import build_parser


def _probe_doc() -> RigDocument:
    return RigDocument(
        {
            "name": "pose_probe",
            "frame": {
                "width": 128,
                "height": 128,
                "center_x": 64.0,
                "ground_y": 112.0,
                "ankle_h": 0.0,
                "supersample": 1,
            },
            "bones": [
                {"name": "pelvis", "parent": None, "offset": [0, -24], "length": 0, "rest_angle": 0},
                {"name": "torso", "parent": "pelvis", "offset": [0, -18], "length": 0, "rest_angle": 0},
                {"name": "near_arm_u", "parent": "torso", "offset": [8, -14], "length": 18, "rest_angle": 180},
                {"name": "near_arm_l", "parent": "near_arm_u", "offset": [18, 0], "length": 16, "rest_angle": 0},
                {"name": "near_arm_hand", "parent": "near_arm_l", "offset": [16, 0], "length": 5, "rest_angle": 0},
            ],
            "parts": [],
            "ik_legs": [],
            "ik_chains": [
                {
                    "upper": "near_arm_u",
                    "lower": "near_arm_l",
                    "end": "near_arm_hand",
                    "channel_prefix": "near_hand",
                    "rest_x": -18.0,
                    "rest_y": -48.0,
                    "rest_pitch": 180.0,
                    "pitch_mode": "follow_lower",
                    "bend": -1.0,
                    "max_reach_ratio": 0.98,
                }
            ],
            "features": {"source_pose_role": "geometry-layout-only"},
            "natural_pose": {
                "arms": {
                    "near": {
                        "hand": [-18.0, -48.0],
                        "elbow": [-3.0, -58.0],
                    }
                }
            },
            "clips": {
                "idle": {
                    "loop": True,
                    "frames": 2,
                    "duration_ms": 100,
                    "channels": {
                        "near_hand_x": {"const": -18.0},
                        "near_hand_y": {"const": -48.0},
                    },
                },
                "walk_stop": {
                    "loop": False,
                    "frames": 2,
                    "duration_ms": 80,
                    "channels": {
                        # Deliberately point the forearm behind the facing-left
                        # natural pose. The audit should catch this without art.
                        "near_hand_x": {"const": 22.0},
                        "near_hand_y": {"const": -48.0},
                    },
                },
            },
        }
    )


def test_pose_audit_flags_backward_natural_arm_without_rasterization():
    result = audit_document(_probe_doc(), target="pose_probe")
    bad = [frame for frame in result.frames if frame.animation == "walk_stop"]
    assert bad
    assert any(
        finding.code == "arm_points_away_from_natural"
        for frame in bad
        for finding in frame.findings
    )


def test_pose_audit_writes_geometry_products_without_resvg(tmp_path: Path):
    rig_path = tmp_path / "probe.rig.json"
    doc = _probe_doc()
    doc.save(rig_path)
    result = run_pose_audit(
        target="pose_probe",
        rig_path=rig_path,
        out_dir=tmp_path / "audit",
        with_art=False,
    )
    assert result.output_paths["report"].exists()
    assert result.output_paths["skeletons"].exists()
    assert result.output_paths["flagged_skeletons"].exists()
    assert result.output_paths["flagged_detail"].exists()
    assert result.art_preview_status == "disabled"


def test_audit_poses_cli_surface_parses():
    args = build_parser().parse_args(
        ["audit-poses", "carl_stargan", "--no-art", "--fail-on", "error"]
    )
    assert args.target == "carl_stargan"
    assert args.no_art is True
    assert args.fail_on == "error"


def test_carl_walk_stop_now_stays_inside_natural_arm_cone():
    rig_path = (
        Path(__file__).resolve().parents[1]
        / "ambition_sprite2d_renderer"
        / "targets"
        / "characters"
        / "rigged"
        / "carl_stargan"
        / "carl_stargan_side.rig.json"
    )
    result = audit_document(RigDocument.load(rig_path), target="carl_stargan")
    walk_stop = [frame for frame in result.frames if frame.animation == "walk_stop"]
    assert walk_stop
    forbidden = {
        "arm_points_away_from_natural",
        "arm_outside_natural_cone",
        "hand_orientation_detached",
        "elbow_branch_inversion",
    }
    assert not {
        finding.code
        for frame in walk_stop
        for finding in frame.findings
    } & forbidden
