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
from scripts import build_player_robot_v3_svg as robot_builder
from ambition_sprite2d_renderer.targets.characters import player_robot_v3 as robot_target
from ambition_sprite2d_renderer.targets.characters.player_robot_v3_motion import (
    APPLICABLE_MOTION_SCOPES as ROBOT_MOTION_SCOPES,
    FIGHTER_MOTION_COVERAGE as ROBOT_MOTION_COVERAGE,
    ROBOT_ROWS,
)



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


def _fake_robot_rig_source():
    bones = []

    def add(name, parent=None):
        bones.append({"name": name, "parent": parent, "rest_angle": 0.0})

    add("pelvis")
    add("torso", "pelvis")
    add("head", "torso")
    for side in ("far", "near"):
        add(f"{side}_arm_u", "torso")
        add(f"{side}_arm_l", f"{side}_arm_u")
        add(f"{side}_arm_hand", f"{side}_arm_l")
        add(f"{side}_leg_u", "pelvis")
        add(f"{side}_leg_l", f"{side}_leg_u")
        add(f"{side}_leg_foot", f"{side}_leg_l")
    return {"bones": bones}


def test_player_robot_v3_covers_every_current_applicable_motion_category():
    required = applicable_categories(ROBOT_MOTION_SCOPES)
    row_names = {name for name, _frames, _duration in ROBOT_ROWS}

    assert set(ROBOT_MOTION_COVERAGE) == required
    validate_motion_coverage(
        row_names=row_names,
        coverage=ROBOT_MOTION_COVERAGE,
        scopes=ROBOT_MOTION_SCOPES,
        character="player_robot_v3",
    )


def test_player_robot_v3_builder_authors_every_declared_row():
    clips = robot_builder.make_clips(_fake_robot_rig_source())
    row_names = {name for name, _frames, _duration in ROBOT_ROWS}

    assert set(clips) == row_names
    assert all(int(clips[name]["frames"]) > 0 for name in row_names)
    assert all(int(clips[name]["duration_ms"]) > 0 for name in row_names)


def test_player_robot_v3_has_requested_high_value_motion_rows():
    rows = {name for name, _frames, _duration in ROBOT_ROWS}
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
        "smash_forward",
        "smash_up",
        "smash_down",
        "air_neutral",
        "air_forward",
        "air_back",
        "air_up",
        "air_down",
        "shoot",
        "blink_out",
        "hover",
        "charge",
    } <= rows


def test_player_robot_v3_builder_and_target_share_one_row_declaration():
    expected = list(ROBOT_ROWS)
    assert robot_target.ROWS == expected
    assert robot_builder.ANIMATION_ORDER == [name for name, _frames, _duration in expected]


def test_player_robot_v3_authored_body_tracks_publish_padding():
    left, top, right, bottom = robot_target.PUBLISH_PADDING
    fw = robot_target.FRAME_SIZE[0] + left + right
    fh = robot_target.FRAME_SIZE[1] + top + bottom
    metrics = robot_target.body_metrics(fw, fh)

    assert metrics["body_pixel_bbox"]["x"] == 86 + left
    assert metrics["body_pixel_bbox"]["y"] == robot_target.BODY_BOX_TOP_PX + top
    assert metrics["feet_pixel"] == {"x": 114.0 + left, "y": 157.0 + top}


def test_carl_stargan_covers_every_current_applicable_motion_category():
    from ambition_sprite2d_renderer.targets.characters.carl_stargan_motion import (
        APPLICABLE_MOTION_SCOPES as CARL_SCOPES,
        CARL_ROWS,
        FIGHTER_MOTION_COVERAGE as CARL_COVERAGE,
    )

    required = applicable_categories(CARL_SCOPES)
    row_names = {name for name, _frames, _duration in CARL_ROWS}

    assert set(CARL_COVERAGE) == required
    validate_motion_coverage(
        row_names=row_names,
        coverage=CARL_COVERAGE,
        scopes=CARL_SCOPES,
        character="carl_stargan",
    )


def test_carl_stargan_builder_authors_every_declared_row():
    from ambition_sprite2d_renderer.targets.characters import carl_stargan as carl_target
    from ambition_sprite2d_renderer.targets.characters.carl_stargan_motion import CARL_ROWS

    source = {
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
                "rest_x": 17.0,
                "rest_y": -48.0,
                "rest_pitch": 0.0,
                "bend": 1.0,
            },
            {
                "channel_prefix": "far_hand",
                "rest_x": -13.0,
                "rest_y": -47.0,
                "rest_pitch": 0.0,
                "bend": 1.0,
            },
        ],
    }
    clips = scientist_builder._stargan_clips(
        scientist_builder.SPECS["carl_stargan"],
        source,
    )
    row_names = {name for name, _frames, _duration in CARL_ROWS}

    assert set(clips) == row_names
    assert carl_target.ROWS == list(CARL_ROWS)
    assert all(int(clips[name]["frames"]) > 0 for name in row_names)
    assert all(int(clips[name]["duration_ms"]) > 0 for name in row_names)
    assert clips["roll"]["channels"]["pelvis"]["keys"][1][1] < 0
    assert clips["roll_back"]["channels"]["pelvis"]["keys"][1][1] > 0


def test_carl_stargan_keeps_cosmic_signature_specials():
    from ambition_sprite2d_renderer.targets.characters.carl_stargan_motion import (
        FIGHTER_MOTION_COVERAGE as coverage,
    )

    assert coverage["special_neutral"] == "pale_blue_dot"
    assert coverage["special_side"] == "cosmic_calendar"
    assert coverage["special_up"] == "cosmic_drift"
    assert coverage["special_down"] == "billions_and_billions"
    assert coverage["final_smash"] == "starstuff"


def test_pca_covers_every_current_applicable_motion_category():
    from ambition_sprite2d_renderer.targets.characters.pca_motion import (
        APPLICABLE_MOTION_SCOPES as PCA_SCOPES,
        FIGHTER_MOTION_COVERAGE as PCA_COVERAGE,
        PCA_ROWS,
    )

    required = applicable_categories(PCA_SCOPES)
    row_names = {name for name, _frames, _duration in PCA_ROWS}

    assert set(PCA_COVERAGE) == required
    validate_motion_coverage(
        row_names=row_names,
        coverage=PCA_COVERAGE,
        scopes=PCA_SCOPES,
        character="perfect_cellular_automaton",
    )


def test_pca_checked_in_rig_has_full_fighter_rows_and_real_back_roll():
    import json
    from pathlib import Path

    from ambition_sprite2d_renderer.targets.characters.pca_motion import PCA_ROWS

    path = (
        Path(__file__).resolve().parents[1]
        / "ambition_sprite2d_renderer"
        / "targets"
        / "characters"
        / "rigged"
        / "perfect_cellular_automaton.rig.json"
    )
    doc = json.loads(path.read_text(encoding="utf8"))
    row_names = {name for name, _frames, _duration in PCA_ROWS}

    assert row_names <= set(doc["clips"])
    assert doc["clips"]["roll"]["channels"]["pelvis"]["keys"][1][1] > 0
    assert doc["clips"]["roll_back"]["channels"]["pelvis"]["keys"][1][1] < 0


def test_pca_keeps_existing_signature_specials():
    from ambition_sprite2d_renderer.targets.characters.pca_motion import (
        FIGHTER_MOTION_COVERAGE as coverage,
    )

    assert coverage["special_neutral"] == "shoot"
    assert coverage["special_side"] == "special"
    assert coverage["special_up"] == "fly"
    assert coverage["special_down"] == "charge"
    assert coverage["final_smash"] == "final_smash"
