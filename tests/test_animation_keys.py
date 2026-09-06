from __future__ import annotations

from ambition_sprite2d_renderer.authoring.animation_keys import (
    channel_key_frames,
    neighbor_pose_keys,
    pose_key_frames,
    suggest_pose_key_frames,
    time_to_frame,
)
from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument


def _dense_doc() -> RigDocument:
    doc = RigDocument.new_empty("dense")
    doc.data["clips"]["idle"] = {
        "loop": True,
        "frames": 8,
        "duration_ms": 100,
        "channels": {
            "arm": {
                "keys": [
                    [i / 8.0, value, "smooth"]
                    for i, value in enumerate((0, 20, 40, 20, 0, -20, -40, -20))
                ]
            },
            "root_y": {
                "keys": [
                    [i / 8.0, value, "smooth"]
                    for i, value in enumerate((0, -1, -2, -1, 0, 1, 2, 1))
                ]
            },
        },
    }
    return doc


def test_time_to_frame_matches_loop_and_one_shot_conventions():
    assert time_to_frame(0.25, 8, True) == 2
    assert time_to_frame(0.999, 8, True) == 0
    assert time_to_frame(0.5, 5, False) == 2
    assert time_to_frame(1.0, 5, False) == 4


def test_dense_channel_keys_are_distinct_from_pose_key_suggestions():
    doc = _dense_doc()
    keyed = channel_key_frames(doc.clips["idle"])
    assert keyed["arm"] == set(range(8))

    suggested = suggest_pose_key_frames(doc, "idle")
    assert 0 in suggested
    assert 2 in suggested or 6 in suggested
    assert 3 <= len(suggested) < 8

    resolved, explicit = pose_key_frames(doc, "idle")
    assert resolved == suggested
    assert explicit is False


def test_explicit_pose_keys_override_suggestions_and_find_neighbors():
    doc = _dense_doc()
    doc.clips["idle"]["pose_keys"] = [0, 3, 6]
    resolved, explicit = pose_key_frames(doc, "idle")
    assert resolved == [0, 3, 6]
    assert explicit is True
    assert neighbor_pose_keys(resolved, 4, 8, True) == (3, 6)
    assert neighbor_pose_keys(resolved, 0, 8, True) == (6, 3)
