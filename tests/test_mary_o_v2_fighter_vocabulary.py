"""Mary-O tall's fighter body language (`_mary_o_v2_fighter`): every
`fighter_core` category resolves to a row she draws, no row repeats another,
and a body on the floor lies on her shoe line inside the frame."""

from __future__ import annotations

import pytest

# The model first: it imports the fighter module after `Pose` exists.
from ambition_sprite2d_renderer.targets.characters._mary_o_v2_model import (
    FIRE_FORM,
    SHORT_FORM,
    TALL_FORM,
    poses_for_form,
)
from ambition_sprite2d_renderer.authoring.fighter_motion_catalog import validate_motion_coverage
from ambition_sprite2d_renderer.targets.characters._mary_o_v2_fighter import (
    FIGHTER_MOTION_COVERAGE,
    fighter_rows,
)

#: Transition rows composite other forms and have no pose-table entry.
_TRANSITIONS = {"grow", "shrink"}


def test_tall_covers_every_fighter_core_category():
    validate_motion_coverage(
        row_names={name for name, _frames, _ms in TALL_FORM.rows},
        coverage=FIGHTER_MOTION_COVERAGE,
        scopes=("fighter_core",),
        character=TALL_FORM.target_name,
    )


def test_only_the_tall_sheet_hosts_the_fighter_rows():
    new = {name for name, _frames, _ms in fighter_rows()}
    for form in (SHORT_FORM, FIRE_FORM):
        assert not new & {name for name, _frames, _ms in form.rows}, form.target_name


def test_no_row_repeats_another_rows_poses():
    poses = poses_for_form(TALL_FORM)
    seen: dict = {}
    for name, frames, _ms in TALL_FORM.rows:
        if name in _TRANSITIONS:
            continue
        key = tuple(poses[name])
        assert len(poses[name]) == frames, name
        assert key not in seen, f"{name} draws exactly what {seen[key]} draws"
        seen[key] = name


@pytest.fixture(scope="module")
def render_tall():
    from ambition_sprite2d_renderer.targets.characters import mary_o_v2_svg_poc as svg_rig
    from ambition_sprite2d_renderer.targets.characters._mary_o_v2_svg_poc import build_rig_document

    docs = {}
    for source in (SHORT_FORM, TALL_FORM, FIRE_FORM):
        docs[source.target_name] = build_rig_document(svg_rig.ASSET_PATH, source, "side")
        docs[f"{source.target_name}:front"] = build_rig_document(svg_rig.ASSET_PATH, source, "front")
    frames = {name: count for name, count, _ms in TALL_FORM.rows}

    def render(row: str, index: int):
        return svg_rig._draw_poc_form(TALL_FORM, docs, row, index, frames[row])

    return render


@pytest.mark.parametrize("row", ["prone_face_up", "prone_face_down", "prone", "trip_idle", "sleep"])
def test_a_body_on_the_floor_lies_on_her_shoe_line(render_tall, row):
    floor = render_tall("idle", 0).getbbox()[3]
    box = render_tall(row, 0).getbbox()
    assert abs(box[3] - floor) <= 1, f"{row}: lowest paint at {box[3]}, shoe line {floor}"
    assert box[0] > 0 and box[2] < 160, f"{row}: art runs off the frame side {box}"
