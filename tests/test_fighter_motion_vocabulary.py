from ambition_sprite2d_renderer.authoring.fighter_motion_catalog import (
    applicable_categories,
    load_fighter_motion_catalog,
    validate_motion_coverage,
)
from ambition_sprite2d_renderer.targets.characters.patent_clerk_motion import (
    APPLICABLE_MOTION_SCOPES,
    FIGHTER_MOTION_COVERAGE,
    PATENT_ROWS,
)
from scripts import build_scientist_fighter_rigs as scientist_builder



def _fake_patent_rig_source():
    # _patent_clips only needs the rest targets from the extracted rig. This
    # deliberately avoids SVG rasterization: the test is about category/clip
    # completeness, not resvg fidelity.
    return {
        "ik_legs": [
            {
                "channel_prefix": "near_foot",
                "rest_x": 10.0,
                "rest_lift": 0.0,
                "rest_pitch": 0.0,
                "bend": 1.0,
            },
            {
                "channel_prefix": "far_foot",
                "rest_x": -10.0,
                "rest_lift": 0.0,
                "rest_pitch": 0.0,
                "bend": 1.0,
            },
        ],
        "ik_chains": [
            {
                "channel_prefix": "near_hand",
                "rest_x": -12.0,
                "rest_y": -57.0,
                "rest_pitch": 0.0,
                "bend": 1.0,
            },
            {
                "channel_prefix": "far_hand",
                "rest_x": -20.0,
                "rest_y": -49.0,
                "rest_pitch": 0.0,
                "bend": 1.0,
            },
        ],
    }


def test_fighter_motion_catalog_preserves_supplied_motion_list():
    data = load_fighter_motion_catalog()
    motions = data["motions"]
    labels = [entry["label"] for entry in motions]
    ids = [entry["id"] for entry in motions]

    assert data["schema_version"] == 1
    assert len(motions) == 271
    assert len(labels) == len(set(labels))
    assert len(ids) == len(set(ids))
    assert labels[0] == "Primary idle"
    assert labels[-1] == "Electric hit reaction"


def test_patent_clerk_covers_every_current_applicable_motion_category():
    required = applicable_categories(APPLICABLE_MOTION_SCOPES)
    row_names = {name for name, _frames, _duration in PATENT_ROWS}

    assert set(FIGHTER_MOTION_COVERAGE) == required
    validate_motion_coverage(
        row_names=row_names,
        coverage=FIGHTER_MOTION_COVERAGE,
        scopes=APPLICABLE_MOTION_SCOPES,
        character="patent_clerk",
    )


def test_patent_clerk_builder_authors_every_declared_row():
    clips = scientist_builder._patent_clips(
        scientist_builder.SPECS["patent_clerk"],
        _fake_patent_rig_source(),
    )
    row_names = {name for name, _frames, _duration in PATENT_ROWS}

    assert set(clips) == row_names
    assert all(int(clips[name]["frames"]) > 0 for name in row_names)
    assert all(int(clips[name]["duration_ms"]) > 0 for name in row_names)


def test_patent_clerk_has_requested_high_value_motion_rows():
    rows = {name for name, _frames, _duration in PATENT_ROWS}
    assert {
        "idle_look_up",
        "crouch_walk",
        "double_jump",
        "roll",
        "roll_back",
        "spot_dodge",
        "air_dodge",
        "getup",
        "getup_attack",
        "ledge_attack",
        "ledge_roll",
        "smash_up",
        "smash_down",
        "air_neutral",
        "air_forward",
        "air_back",
        "air_up",
        "air_down",
    } <= rows
