"""Mary-O is drawn entirely from parts: every row of every form, the
transitions' recolours and effect layers included
(`docs/planning/engine/mary-o-part-realization.md` in the game repository).

Her ``RigDocument`` paints every body pixel as a rigid part, and her effects go
through ``rigdoc``'s compositing seams, so the flipbook is recorded from the
real render (``build_rig_flipbook``). Each frame is recomposed from the
PUBLISHED part atlas and draw table and diffed against the same frame of the
PUBLISHED sheet, by two measures:

* ``parity``: the share of drawn pixels that differ;
* ``largest_wrong_blob``: the largest connected run of differing pixels. A
  missing star or orb barely moves ``parity`` (1.43% on the median frame for a
  whole dropped effect layer) but is one blob.

A rig flipbook places parts the way the baked render does (whole-pixel pivots
and points, the same rotation), so the two are the same picture up to one level
of compositing rounding. The comparison is therefore strict: no positional
slack, and a channel tolerance only for that rounding. Measured when this was
written: 0 wrong pixels on all 87 frames.
"""

from __future__ import annotations

import dataclasses
import math
from pathlib import Path

import pytest
import yaml
from PIL import Image

from ambition_sprite2d_renderer.authoring import part_flipbook
from ambition_sprite2d_renderer.authoring.part_flipbook import largest_wrong_blob, parity
from ambition_sprite2d_renderer.targets.characters._mary_o_v2_model import FIRE_FORM, SHORT_FORM, TALL_FORM
from ambition_sprite2d_renderer.targets.characters.mary_o_v2 import _render_form_with_products

FORMS = (SHORT_FORM, TALL_FORM, FIRE_FORM)

#: Strict comparison: no positional slack, 8 levels of channel tolerance.
STRICT = {"threshold": 8, "radius": 0}
PARITY_BOUND = 0.01
BLOB_BOUND = 6
#: Packed part pages over baked sheet pages, all three forms. Measured 0.541
#: when every row moved to parts (865,937 / 1,601,774 texels).
TEXEL_CEILING = 0.60


@pytest.fixture(scope="module")
def published(tmp_path_factory):
    """Each form rendered and published once: (sheet yaml, atlas, flipbook)."""
    out = {}
    for form in FORMS:
        root = tmp_path_factory.mktemp(form.target_name)
        paths, products = _render_form_with_products(form, root)
        flipbook = products["parts"]
        ron = root / f"{form.target_name}_parts.ron"
        assert ron in paths and ron.read_text() == flipbook.to_ron()
        sheet = yaml.safe_load(Path(products["outputs"]["yaml"]).read_text())
        atlas = Image.open(root / sheet["image"]).convert("RGBA")
        out[form.target_name] = (sheet, atlas, flipbook)
    return out


def _published_frame(atlas, row, index, frame_size):
    rect = row["rects"][index]
    frame = Image.new("RGBA", frame_size, (0, 0, 0, 0))
    frame.paste(
        atlas.crop((rect["x"], rect["y"], rect["x"] + rect["w"], rect["y"] + rect["h"])),
        tuple(rect["off"]),
    )
    return frame


@pytest.mark.parametrize("form", FORMS, ids=lambda form: form.target_name)
def test_every_row_is_drawn_from_parts_and_is_the_published_frame(form, published):
    sheet, atlas, flipbook = published[form.target_name]
    assert flipbook.baked_clips == []
    rows = {row["animation"]: row for row in sheet["rows"]}
    # The census is the SHEET's, not the flipbook's: a row or frame the
    # flipbook dropped cannot shrink what is checked.
    assert sorted(flipbook.clips) == sorted(rows)
    checked = 0
    failures = []
    for name, row in rows.items():
        _duration, frames = flipbook.clips[name]
        assert len(frames) == len(row["rects"]), name
        for index in range(len(row["rects"])):
            reference = _published_frame(atlas, row, index, flipbook.frame_size)
            candidate = flipbook.recompose(name, index)
            wrong = parity(reference, candidate, **STRICT)
            blob = largest_wrong_blob(reference, candidate, **STRICT)
            checked += 1
            if wrong > PARITY_BOUND or blob > BLOB_BOUND:
                failures.append(f"{name}[{index}]: {wrong:.4f} of pixels, blob {blob}")
    assert checked == sum(len(row["rects"]) for row in rows.values()) > 0
    assert not failures, "frames the flipbook does not reproduce:\n" + "\n".join(failures)


def test_the_part_pages_are_smaller_than_the_sheets(published):
    parts = sum(flipbook.packed_texels() for _sheet, _atlas, flipbook in published.values())
    sheets = sum(atlas.width * atlas.height for _sheet, atlas, _flipbook in published.values())
    assert parts / sheets <= TEXEL_CEILING, f"part pages are {parts / sheets:.3f} of the sheets"


# -- the measures can fail --------------------------------------------------------


def _fire_transform(published, index):
    sheet, atlas, flipbook = published[FIRE_FORM.target_name]
    row = {row["animation"]: row for row in sheet["rows"]}["transform"]
    return flipbook, _published_frame(atlas, row, index, flipbook.frame_size)


def _recompose_with(flipbook, row, index, draws):
    poisoned = dataclasses.replace(flipbook, clips={**flipbook.clips, row: (flipbook.clips[row][0], [draws])})
    return poisoned.recompose(row, 0)


def test_a_dropped_effect_layer_is_a_blob(published):
    flipbook, reference = _fire_transform(published, 4)
    draws = flipbook.clips["transform"][1][4]
    overlays = [d for d in draws if (d.track or "").startswith("overlay:outfit_stars")]
    assert overlays, "the poison needs the outfit stars on this frame"
    candidate = _recompose_with(flipbook, "transform", 4, [d for d in draws if d is not overlays[0]])
    assert largest_wrong_blob(reference, candidate, **STRICT) > BLOB_BOUND


def test_a_part_one_pixel_off_is_a_blob(published):
    flipbook, reference = _fire_transform(published, 4)
    draws = list(flipbook.clips["transform"][1][4])
    index = next(i for i, d in enumerate(draws) if d.track == "head")
    draws[index] = dataclasses.replace(draws[index], at=(draws[index].at[0] + 1.0, draws[index].at[1]))
    candidate = _recompose_with(flipbook, "transform", 4, draws)
    assert largest_wrong_blob(reference, candidate, **STRICT) > BLOB_BOUND


def test_two_overlapping_draws_in_the_wrong_order_are_a_blob(published):
    flipbook, reference = _fire_transform(published, 4)
    draws = list(flipbook.clips["transform"][1][4])
    torso = next(i for i, d in enumerate(draws) if d.track == "torso")
    near_arm = next(i for i, d in enumerate(draws) if d.track == "near_arm")
    draws[torso], draws[near_arm] = draws[near_arm], draws[torso]
    candidate = _recompose_with(flipbook, "transform", 4, draws)
    assert largest_wrong_blob(reference, candidate, **STRICT) > BLOB_BOUND


def test_a_frame_painted_outside_the_seams_is_refused():
    """A whole-frame post-process (how transitions used to recolour) is a
    picture no draw carries: the recorder refuses the flipbook."""
    from ambition_sprite2d_renderer.targets.characters import mary_o_v2_svg_poc as poc
    from ambition_sprite2d_renderer.targets.characters._mary_o_v2_model import FRAME_SIZE
    from ambition_sprite2d_renderer.targets.characters._mary_o_v2_svg_poc import build_rig_document

    docs = {SHORT_FORM.target_name: build_rig_document(poc.ASSET_PATH, SHORT_FORM, "side")}

    def render(row, index, count):
        frame = poc._rig_pose(docs, SHORT_FORM, poc._poses_for(SHORT_FORM)[row][index])
        for x in range(40, 120):
            frame.putpixel((x, 100), (255, 0, 0, 255))
        return frame

    with pytest.raises(AssertionError, match="outside rigdoc's seams"):
        part_flipbook.build_rig_flipbook("poison", [("idle", 1, 100)], render, None, (80.0, 190.0), FRAME_SIZE)


# -- in-betweens ------------------------------------------------------------------


def _lerp_pose(a, b, t):
    from ambition_sprite2d_renderer.targets.characters._mary_o_v2_model import Pose

    values = {}
    for f in dataclasses.fields(Pose):
        va, vb = getattr(a, f.name), getattr(b, f.name)
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)) and not isinstance(va, bool):
            values[f.name] = va + (vb - va) * t
        else:
            assert va == vb, f"{f.name} cannot be tweened: {va!r} -> {vb!r}"
            values[f.name] = va
    return Pose(**values)


#: How far a tweened part may sit from where the renderer puts it in the
#: lerped pose, in frame pixels. Each published keyframe is the renderer's
#: placement ROUNDED to whole pixels (the baked road), so an in-between of two
#: rounded places can sit up to a pixel from the unrounded in-between.
TWEEN_PLACE_PX = 1.0
TWEEN_TURN_DEG = 0.01


def _tween_errors(flipbook, form, docs, row, index, t, draws):
    """Per track: (place error px, turn error deg) of ``draws`` against the
    renderer's own placement of the lerped pose."""
    from ambition_sprite2d_renderer.targets.characters import mary_o_v2_svg_poc as poc

    poses = poc._poses_for(form)[row]
    a, b = poses[index % len(poses)], poses[(index + 1) % len(poses)]
    with part_flipbook.recorded_paint() as record:
        truth = poc._rig_pose(docs, form, _lerp_pose(a, b, t))
    placed = {op.name: op for op in record.ops_for(truth)}
    errors = {}
    for d in draws:
        op = placed[d.track]
        pivot = flipbook.parts[d.part].pivot
        corner = (d.at[0] + flipbook.feet[0] - pivot[0], d.at[1] + flipbook.feet[1] - pivot[1])
        exact = (op.world[0] - op.pivot[0], op.world[1] - op.pivot[1])
        place = max(abs(corner[0] - exact[0]), abs(corner[1] - exact[1]))
        turn = abs((math.degrees(d.rotation) - op.degrees + 180.0) % 360.0 - 180.0)
        errors[d.track] = (place, turn)
    return errors


@pytest.mark.parametrize("form", FORMS, ids=lambda form: form.target_name)
def test_a_tweened_clip_places_each_part_where_the_in_between_pose_does(form, published):
    """The runtime's tween (``tween_draws``: each track lerps to its place in
    the next frame) against the renderer placing the LERPED POSE: the
    in-between frames have an oracle even though no sheet publishes them.

    Geometry, not pixels: the GPU draws a tweened part between whole pixels and
    does not round it, so a PIL raster of the oracle (which rounds each part's
    place and pivot on its own) would measure PIL's rounding, not the tween."""
    from ambition_sprite2d_renderer.targets.characters import mary_o_v2_svg_poc as poc
    from ambition_sprite2d_renderer.targets.characters._mary_o_v2_svg_poc import build_rig_document
    from ambition_sprite2d_renderer.targets.characters.mary_o_v2 import TWEENED_ROWS

    _sheet, _atlas, flipbook = published[form.target_name]
    tweened = [row for row in flipbook.clips if flipbook.tweens.get(row) == part_flipbook.TWEEN_LINEAR]
    assert tweened == [row for row in flipbook.clips if row in TWEENED_ROWS] and tweened
    docs = {form.target_name: build_rig_document(poc.ASSET_PATH, form, "side")}
    failures, checked, moved = [], 0, 0
    for row in tweened:
        frames = flipbook.clips[row][1]
        for index in range(len(frames)):
            for t in (0.25, 0.5, 0.75):
                draws = part_flipbook.tween_draws(flipbook, row, index, t)
                moved += sum(1 for d, f in zip(draws, frames[index]) if d.at != f.at or d.rotation != f.rotation)
                for track, (place, turn) in _tween_errors(flipbook, form, docs, row, index, t, draws).items():
                    checked += 1
                    if place > TWEEN_PLACE_PX or turn > TWEEN_TURN_DEG:
                        failures.append(f"{row}[{index}] t={t} {track}: {place:.2f} px, {turn:.3f} deg")
    # ⛔ Premise: the tween MOVED something. A tween that holds every draw still
    # agrees with a pose that barely moves.
    assert checked > 0 and moved > 0
    assert not failures, "in-betweens the tween misplaces:\n" + "\n".join(failures)


def test_a_tween_that_does_not_move_is_caught(published):
    """The measure can fail: the frame itself, offered as the half-way pose of
    a swim stroke, misplaces its limbs."""
    from ambition_sprite2d_renderer.targets.characters import mary_o_v2_svg_poc as poc
    from ambition_sprite2d_renderer.targets.characters._mary_o_v2_svg_poc import build_rig_document

    _sheet, _atlas, flipbook = published[TALL_FORM.target_name]
    docs = {TALL_FORM.target_name: build_rig_document(poc.ASSET_PATH, TALL_FORM, "side")}
    held = flipbook.clips["swim"][1][4]
    errors = _tween_errors(flipbook, TALL_FORM, docs, "swim", 4, 0.5, held)
    assert max(max(place / TWEEN_PLACE_PX, turn / TWEEN_TURN_DEG) for place, turn in errors.values()) > 1.0


def test_a_clip_that_steps_holds_its_frame(published):
    _sheet, _atlas, flipbook = published[FIRE_FORM.target_name]
    assert flipbook.tweens.get("transform") is None
    assert part_flipbook.tween_draws(flipbook, "transform", 3, 0.5) == flipbook.clips["transform"][1][3]


def test_the_published_file_carries_tracks_and_tweens(published, tmp_path):
    _sheet, _atlas, flipbook = published[TALL_FORM.target_name]
    flipbook.write(tmp_path)
    back = part_flipbook.PartFlipbook.from_published(tmp_path / f"{TALL_FORM.target_name}_parts.ron", "snapped")
    assert back.tweens == flipbook.tweens
    assert [[d.track for d in frame] for frame in back.clips["walk"][1]] == [
        [d.track for d in frame] for frame in flipbook.clips["walk"][1]
    ]
