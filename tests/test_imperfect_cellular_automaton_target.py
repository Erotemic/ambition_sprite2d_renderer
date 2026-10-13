from ambition_sprite2d_renderer.authoring import rigdoc
from ambition_sprite2d_renderer.targets.characters import imperfect_cellular_automaton as target


def test_each_row_is_published_from_both_sides():
    base = [name for name, _frames, _duration in target.BASE_ROWS]
    assert base, "premise: she has rows"
    rows = {name: (frames, duration) for name, frames, duration in target.ROWS}
    for name in base:
        assert rows[target.MIRRORED.format(name)] == rows[name]
        assert target.MIRROR_OF[target.MIRRORED.format(name)] == name


def test_the_other_side_of_her_is_not_a_flip_of_this_side():
    # Her halves differ, so the row the game draws when she faces left is
    # drawn from her other side. A flip of this side would be the same pixels.
    this_side = target.render_frame("idle", 0, 10)
    other_side = target.render_frame("idle~mirrored", 0, 10)
    assert this_side.size == other_side.size == target.FRAME_SIZE
    assert this_side.getchannel("A").getbbox() is not None
    assert other_side.tobytes() != rigdoc.mirrored_canvas(this_side).tobytes()


def test_she_stands_at_the_same_place_from_both_sides():
    meta = target.frame_meta("idle", 0, 10)["anchors"]
    mirrored = target.frame_meta("idle~mirrored", 0, 10)["anchors"]
    for name, point in meta.items():
        assert abs(mirrored[name]["x"] - (target.FRAME_SIZE[0] - point["x"])) < 1e-3
        assert mirrored[name]["y"] == point["y"]


def test_the_grid_on_her_chest_changes_state_each_frame():
    states = [target.grid_state("idle", frame) for frame in range(target.GRID_STATES)]
    assert sorted(states) == list(range(target.GRID_STATES))
    assert target.render_frame("idle", 0, 10).tobytes() != target.render_frame("idle", 1, 10).tobytes()


def test_her_rig_has_the_bones_of_the_clips_she_borrows():
    # She plays the perfect one's clips. A channel that names a bone she does
    # not have would be read as a free parameter, and the limb would not move.
    doc = target._doc()
    perfect = rigdoc.RigDocument.load(str(target.PERFECT_RIG_PATH))
    assert {bone["name"] for bone in perfect.bones} <= {bone["name"] for bone in doc.bones}


def test_imperfect_cellular_automaton_declares_model_lineage():
    provenance = target.ACTOR_METADATA["provenance"]
    assert provenance["variant_family"] == target.TARGET_NAME
    assert provenance["lineage"][-1]["revision_id"] == provenance["variant_id"]
    assert provenance["lineage"][-1]["parent_revision_id"] == provenance["lineage"][-2]["revision_id"]
