from ambition_sprite2d_renderer.authoring.humanoid_svg_rig import (
    LimbPoseHint,
    _bend_for_side,
)


def test_pose_hint_controls_ik_branch_independent_of_svg_splay():
    hints = {
        "near": LimbPoseHint(target=(-12.0, -57.0), joint=(2.5, -64.0)),
    }
    common = dict(
        pose_hints=hints,
        overrides=None,
        side="near",
        center_x=88.0,
        ground_y=150.0,
        root=(102.8304, 72.0839),
        l1=18.4378,
        l2=16.1966,
    )

    first = _bend_for_side(
        joint=(140.0, 60.0),
        target=(160.0, 50.0),
        **common,
    )
    second = _bend_for_side(
        joint=(60.0, 120.0),
        target=(35.0, 135.0),
        **common,
    )

    assert first == second == 1.0


def test_svg_joint_layout_remains_fallback_without_pose_authority():
    common = dict(
        pose_hints=None,
        overrides=None,
        side="near",
        center_x=88.0,
        ground_y=150.0,
        root=(102.8304, 72.0839),
        l1=18.4378,
        l2=16.1966,
        target=(76.0, 93.0),
    )

    left_joint = _bend_for_side(joint=(90.5, 85.8), **common)
    right_joint = _bend_for_side(joint=(86.5, 80.7), **common)

    assert left_joint == 1.0
    assert right_joint == -1.0
