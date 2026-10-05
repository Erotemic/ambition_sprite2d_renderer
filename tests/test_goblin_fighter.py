"""The goblin's fighter contract.

The runtime-facing promises: every applicable fighter-motion category
resolves to a row the generator can draw; the rows the goblin published
before its moveset keep their names, frame counts and durations; the base
config publishes every row and binds only rows it publishes; and each
strike row publishes a hit volume measured from the pose.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from ambition_sprite2d_renderer.authoring.fighter_motion_catalog import (
    applicable_categories,
    validate_motion_coverage,
)
from ambition_sprite2d_renderer.registry import CharacterJob
from ambition_sprite2d_renderer.registry.character_generators import GENERATORS
from ambition_sprite2d_renderer.targets.characters import _goblin_moves as moves
from ambition_sprite2d_renderer.targets.characters._goblin_motion import (
    APPLICABLE_MOTION_SCOPES,
    FIGHTER_MOTION_COVERAGE,
    GOBLIN_LOOPS,
    GOBLIN_ROWS,
    LEGACY_ROWS,
)

CONFIG = Path(__file__).resolve().parents[1] / "ambition_sprite2d_renderer" / "configs" / "goblin.yaml"
ROW_NAMES = [name for name, _frames, _ms in GOBLIN_ROWS]


def test_goblin_covers_every_current_applicable_motion_category():
    assert set(FIGHTER_MOTION_COVERAGE) == applicable_categories(APPLICABLE_MOTION_SCOPES)
    validate_motion_coverage(
        row_names=set(ROW_NAMES),
        coverage=FIGHTER_MOTION_COVERAGE,
        scopes=APPLICABLE_MOTION_SCOPES,
        character="goblin",
    )


def test_goblin_keeps_its_legacy_rows_and_their_timing():
    anims = GENERATORS["goblin"].animations()
    for name, frames, ms in LEGACY_ROWS:
        assert anims[name] == {"frames": frames, "duration_ms": ms}, name


def test_every_goblin_row_has_a_pose():
    assert len(ROW_NAMES) == len(set(ROW_NAMES))
    assert set(moves.CLIPS) == set(ROW_NAMES)
    assert GOBLIN_LOOPS <= set(ROW_NAMES)
    for name, frames, _ms in GOBLIN_ROWS:
        for i in range(frames):
            pose = moves.pose(name, moves.clip_time(name, i, frames))
            for leg in ("nleg", "fleg"):
                assert pose[leg][0] in ("g", "a", "mix"), (name, i, leg)


def test_goblin_config_publishes_every_row_and_binds_only_published_rows():
    cfg = yaml.safe_load(CONFIG.read_text())
    assert cfg["animations"] == ROW_NAMES
    for key, binding in cfg["animation_bindings"].items():
        assert binding["animation"] in ROW_NAMES, key


def test_goblin_strikes_publish_measured_hit_volumes():
    generator = GENERATORS["goblin"]
    generator.sample_spec(CharacterJob.load(CONFIG))
    boxes = generator.attack_hitboxes((256, 256))
    for row in ("slash", "jab", "jab_3", "smash_forward", "smash_up", "smash_down", "air_forward", "air_back",
                "shiv_lunge", "throw_up", "throw_down", "goblin_frenzy"):
        box = boxes[row]
        assert box["active_frames"], row
        assert len(box["poly"]) >= 3, row
        x, y, w, h = box["bbox"]
        assert w > 0 and h > 0, row
    # A forward strike lands ahead of the goblin's body (centre x 60 of 128),
    # a back air behind it.
    assert boxes["slash"]["bbox"][0] + boxes["slash"]["bbox"][2] > 60 * 2
    assert boxes["air_back"]["bbox"][0] < 60 * 2
