from pathlib import Path

from scripts.build_scientist_fighter_rigs import (
    SPECS,
    _canonical_svg_part_order,
    _neutral,
    _pose,
    _rebase_hand_trajectory,
)
from ambition_sprite2d_renderer.authoring.humanoid_svg_rig import LimbPoseHint


def test_canonical_scientist_part_order_uses_svg_document_order(tmp_path: Path):
    svg = tmp_path / "paperdoll.svg"
    svg.write_text(
        """\
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape">
  <g inkscape:label="Side Left">
    <g data-rig-part="neck" data-rig-bone="torso" data-rig-z="8">
      <path id="neck-art" d="M 0 0 L 1 0 L 1 1 Z" />
    </g>
    <g data-rig-part="torso" data-rig-bone="torso" data-rig-z="7">
      <path id="torso-art" d="M 0 0 L 2 0 L 2 2 Z" />
    </g>
  </g>
</svg>
""",
        encoding="utf8",
    )

    # data-rig-z is intentionally stale after the two Inkscape groups were
    # reordered.  Canonical scientist rigs use paint/document order, so that
    # normal authoring operation must not require a redundant metadata edit.
    assert _canonical_svg_part_order(svg, "Side Left") == ["neck", "torso"]


def _patent_rest():
    return {
        "near_hand_x": 48.0,
        "near_hand_y": -72.0,
        "near_hand_pitch": 0.0,
        "far_hand_x": -35.0,
        "far_hand_y": -72.0,
        "far_hand_pitch": 180.0,
        "near_foot_pitch": 0.0,
        "far_foot_pitch": 0.0,
        "_natural_near_hand_x": -12.0,
        "_natural_near_hand_y": -57.0,
        "_natural_far_hand_x": -20.0,
        "_natural_far_hand_y": -49.0,
        "_hands_follow_forearms": 1.0,
    }


def test_patent_neutral_uses_natural_rig_pose_not_svg_splay():
    rest = _patent_rest()
    neutral = _neutral(rest, compact=True)
    assert neutral["near_hand_x"] == {"const": -12.0}
    assert neutral["near_hand_y"] == {"const": -57.0}
    assert neutral["far_hand_x"] == {"const": -20.0}
    assert neutral["far_hand_y"] == {"const": -49.0}
    assert "near_hand_pitch" not in neutral
    assert "far_hand_pitch" not in neutral


def test_patent_pose_trajectories_rebase_around_natural_arm_pose():
    rest = _patent_rest()
    near_x, near_y = _rebase_hand_trajectory(
        rest, "near_hand", [17.0, 9.0, -5.0], [-50.0, -55.0, -75.0], compact=True
    )
    far_x, far_y = _rebase_hand_trajectory(
        rest, "far_hand", [-13.0, -5.0, 6.0], [-49.0, -54.0, -74.0], compact=True
    )
    assert near_x == [-12.0, -20.0, -34.0]
    assert near_y == [-57.0, -62.0, -82.0]
    assert far_x == [-20.0, -12.0, -1.0]
    assert far_y == [-49.0, -54.0, -74.0]

    pose = _pose(
        rest,
        2,
        60,
        compact=True,
        near_hand=([17.0, 7.0], [-50.0, -45.0], [80.0, 40.0]),
        far_hand=([-13.0, -3.0], [-49.0, -44.0], [100.0, 140.0]),
    )
    assert pose["channels"]["near_hand_x"]["keys"][0][1] == -12.0
    assert pose["channels"]["near_hand_x"]["keys"][1][1] == -22.0
    assert pose["channels"]["near_hand_y"]["keys"][0][1] == -57.0
    assert pose["channels"]["near_hand_y"]["keys"][1][1] == -52.0
    assert pose["channels"]["far_hand_x"]["keys"][0][1] == -20.0
    assert pose["channels"]["far_hand_x"]["keys"][1][1] == -10.0
    assert "near_hand_pitch" not in pose["channels"]
    assert "far_hand_pitch" not in pose["channels"]


def test_patent_natural_arm_pose_is_separate_from_svg_splay():
    spec = SPECS["patent_clerk"]
    assert spec.natural_arm_pose is not None
    assert set(spec.natural_arm_pose) == {"near", "far"}
    # The neutral lower arms point toward west: each hand is left of its elbow.
    assert all(
        hint.target[0] < hint.joint[0]
        for hint in spec.natural_arm_pose.values()
    )
    assert spec.arm_max_reach_ratio == 0.98


def _carl_rest():
    return {
        "near_hand_x": 40.2822,
        "near_hand_y": -72.0327,
        "near_hand_pitch": 7.7977,
        "far_hand_x": -39.0798,
        "far_hand_y": -72.2045,
        "far_hand_pitch": 179.6102,
        "near_foot_pitch": 0.0,
        "far_foot_pitch": 0.0,
        "_natural_near_hand_x": -12.0,
        "_natural_near_hand_y": -58.0,
        "_natural_far_hand_x": -22.0,
        "_natural_far_hand_y": -52.0,
        "_hands_follow_forearms": 1.0,
    }


def test_carl_neutral_uses_natural_rig_pose_not_svg_splay():
    rest = _carl_rest()
    neutral = _neutral(rest, compact=False)
    assert neutral["near_hand_x"] == {"const": -12.0}
    assert neutral["near_hand_y"] == {"const": -58.0}
    assert neutral["far_hand_x"] == {"const": -22.0}
    assert neutral["far_hand_y"] == {"const": -52.0}
    assert "near_hand_pitch" not in neutral
    assert "far_hand_pitch" not in neutral


def test_carl_natural_arm_pose_is_separate_from_svg_splay():
    spec = SPECS["carl_stargan"]
    assert spec.natural_arm_pose is not None
    assert set(spec.natural_arm_pose) == {"near", "far"}
    assert all(
        hint.target[0] < hint.joint[0]
        for hint in spec.natural_arm_pose.values()
    )
    assert spec.arm_max_reach_ratio == 0.98
