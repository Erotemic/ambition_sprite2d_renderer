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
