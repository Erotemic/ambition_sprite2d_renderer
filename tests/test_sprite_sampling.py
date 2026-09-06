from dataclasses import replace

from ambition_sprite2d_renderer.authoring.motion_ir import (
    CharacterMotionBinding,
    ClipDefinition,
    ClipPoseKey,
    PoseState,
    ScalarKey,
    ScalarTrack,
)
from ambition_sprite2d_renderer.authoring.sprite_sampling import (
    SpriteBakeProfile,
    adaptive_sample_plan,
    uniform_compatibility_plan,
)
from ambition_sprite2d_renderer.devtools.godot_motion_tool import DEFAULT_BINDINGS, repo_root


def _prepared_with(clip: ClipDefinition):
    binding = CharacterMotionBinding.load(repo_root() / DEFAULT_BINDINGS[0])
    prepared = binding.load_prepared()
    library = replace(prepared.library, clips={clip.id: clip})
    return replace(prepared, library=library)


def _base_clip(*, tracks=()):
    return ClipDefinition(
        id="synthetic",
        loop=False,
        duration_s=1.0,
        frame_count=99,
        frame_duration_ms=1,
        pose_keys=(
            ClipPoseKey(at_s=0.0, state=PoseState()),
            ClipPoseKey(at_s=1.0, state=PoseState()),
        ),
        tracks=tracks,
    )


def test_adaptive_sampler_uses_temporal_cap_without_inheriting_source_frame_count():
    clip = _base_clip()
    prepared = _prepared_with(clip)
    profile = SpriteBakeProfile(
        max_joint_error_px=1000.0,
        max_rotation_error_deg=1000.0,
        max_hold_ms=250.0,
        max_frames=16,
        include_named_pose_anchors=False,
        include_markers=False,
    )

    plan = adaptive_sample_plan(prepared, clip.id, profile)
    assert plan.sample_times == (0.0, 0.25, 0.5, 0.75)
    assert plan.frame_count == 4
    assert clip.frame_count == 99
    assert all(sample.duration_s == 0.25 for sample in plan.samples)


def test_adaptive_sampler_subdivides_where_continuous_curve_bends():
    clip = _base_clip(
        tracks=(
            ScalarTrack(
                target="bone.near_arm_u.rotation_deg",
                keys=(
                    ScalarKey(at_s=0.0, value=0.0),
                    ScalarKey(at_s=0.5, value=90.0),
                    ScalarKey(at_s=1.0, value=0.0),
                ),
            ),
        )
    )
    prepared = _prepared_with(clip)
    profile = SpriteBakeProfile(
        max_joint_error_px=1000.0,
        max_rotation_error_deg=5.0,
        max_hold_ms=2000.0,
        max_frames=8,
        include_named_pose_anchors=False,
        include_markers=False,
    )

    plan = adaptive_sample_plan(prepared, clip.id, profile)
    assert 0.5 in plan.sample_times
    assert plan.frame_count >= 2
    assert not plan.budget_exhausted


def test_uniform_compatibility_plan_uses_same_quality_budget_with_one_cadence():
    clip = _base_clip()
    prepared = _prepared_with(clip)
    profile = SpriteBakeProfile(
        max_joint_error_px=1000.0,
        max_rotation_error_deg=1000.0,
        max_hold_ms=250.0,
        max_frames=16,
        include_named_pose_anchors=False,
        include_markers=False,
    )

    plan = uniform_compatibility_plan(prepared, clip.id, profile)
    assert plan.mode == "uniform-compatibility"
    assert plan.frame_count == 4
    assert plan.sample_times == (0.0, 0.25, 0.5, 0.75)
    assert not plan.budget_exhausted
