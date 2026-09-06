from ambition_sprite2d_renderer.authoring.motion_evaluation import sample_clip_state
from ambition_sprite2d_renderer.authoring.motion_ir import (
    ClipDefinition,
    ClipPoseKey,
    PoseState,
    ScalarKey,
    ScalarTrack,
    Transform2D,
)
from ambition_sprite2d_renderer.devtools.godot_motion_tool import DEFAULT_BINDINGS, repo_root
from ambition_sprite2d_renderer.authoring.motion_ir import CharacterMotionBinding


def _library():
    binding = CharacterMotionBinding.load(repo_root() / DEFAULT_BINDINGS[0])
    return binding.load_prepared().library


def test_scalar_tracks_override_pose_backbone_at_arbitrary_time():
    clip = ClipDefinition(
        id="synthetic",
        loop=False,
        duration_s=1.0,
        frame_count=2,
        frame_duration_ms=500,
        pose_keys=(
            ClipPoseKey(
                at_s=0.0,
                state=PoseState(
                    root=Transform2D(position=(0.0, 0.0)),
                    bones={"near_arm_u": Transform2D(rotation_deg=0.0)},
                ),
            ),
            ClipPoseKey(
                at_s=1.0,
                state=PoseState(
                    root=Transform2D(position=(10.0, 0.0)),
                    bones={"near_arm_u": Transform2D(rotation_deg=20.0)},
                ),
            ),
        ),
        tracks=(
            ScalarTrack(
                target="bone.near_arm_u.rotation_deg",
                keys=(
                    ScalarKey(at_s=0.0, value=100.0),
                    ScalarKey(at_s=1.0, value=200.0),
                ),
            ),
        ),
    )

    state = sample_clip_state(_library(), clip, 0.5, bone_ids=("near_arm_u",))
    assert state.root.position == (5.0, 0.0)
    assert state.bones["near_arm_u"].rotation_deg == 150.0


def test_hold_track_is_stepwise_in_continuous_clip_time():
    clip = ClipDefinition(
        id="hold",
        loop=False,
        duration_s=1.0,
        frame_count=2,
        frame_duration_ms=500,
        pose_keys=(
            ClipPoseKey(at_s=0.0, state=PoseState()),
            ClipPoseKey(at_s=1.0, state=PoseState()),
        ),
        tracks=(
            ScalarTrack(
                target="root.position.x",
                keys=(
                    ScalarKey(at_s=0.0, value=2.0, interpolation="hold"),
                    ScalarKey(at_s=0.6, value=9.0, interpolation="hold"),
                ),
            ),
        ),
    )

    assert sample_clip_state(_library(), clip, 0.59).root.position[0] == 2.0
    assert sample_clip_state(_library(), clip, 0.6).root.position[0] == 9.0
