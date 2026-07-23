"""Poison tests for the symmetric frame-fidelity metric (GPT 5.6 review).

The bug this pins: the verifier compared colour only inside the *intersection*
of opaque pixels, so a frame that DROPPED geometry (a missing arm/thruster) or
INVENTED geometry scored zero bad pixels and was called ``captured``. A source
with two shapes vs a render with one reproduced as a clean pass.

The fix grades two independent defect fractions (``_frame_defects`` ->
``occupancy`` and ``rgb``) and a frame is ``_frame_verified`` only when BOTH
pass: a tight occupancy bar (completeness — GPT's concern) and a looser rgb bar
(pre-existing resvg-vs-Pillow rasterizer/AA colour slack). These pin:

* an omitted shape fails on occupancy,
* an invented shape fails on occupancy,
* correct RGB but wrong (translucent) alpha fails on occupancy,
* a within-tolerance 1px shift still verifies (no edge wrap),
* a shift beyond tolerance fails,
* pure rasterizer colour noise over complete geometry still verifies
  (occupancy near zero) — mockingbird's real regime.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from equivalence_harness import (  # noqa: E402
    _OCC_TOL,
    _frame_defects,
    _frame_verified,
    _shift_onto_transparent,
)

W = H = 64


def _canvas() -> Image.Image:
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def _two_shapes() -> Image.Image:
    img = _canvas()
    d = ImageDraw.Draw(img)
    d.rectangle((6, 6, 22, 22), fill=(255, 0, 0, 255))
    d.rectangle((42, 42, 58, 58), fill=(0, 0, 255, 255))
    return img


def _one_shape() -> Image.Image:
    img = _canvas()
    ImageDraw.Draw(img).rectangle((6, 6, 22, 22), fill=(255, 0, 0, 255))
    return img


def test_identical_frames_verify() -> None:
    a = _two_shapes()
    d = _frame_defects(a, a.copy())
    assert d.occupancy == 0.0 and d.rgb == 0.0
    assert _frame_verified(a, a.copy())


def test_omitted_shape_fails_on_occupancy() -> None:
    """The core repro: source has two shapes, render has one. The missing
    shape must register as occupancy defect, not be masked away."""
    d = _frame_defects(_two_shapes(), _one_shape())
    assert d.occupancy > _OCC_TOL, d
    assert not _frame_verified(_two_shapes(), _one_shape())


def test_invented_shape_fails_on_occupancy() -> None:
    """Symmetric: render adds geometry the source never had."""
    d = _frame_defects(_one_shape(), _two_shapes())
    assert d.occupancy > _OCC_TOL, d
    assert not _frame_verified(_one_shape(), _two_shapes())


def test_correct_rgb_wrong_alpha_fails() -> None:
    """Same colours, but the render draws the shapes translucent where the
    source is solid — solid occupancy disagrees, so it must not verify."""
    faded = _canvas()
    d = ImageDraw.Draw(faded)
    d.rectangle((6, 6, 22, 22), fill=(255, 0, 0, 80))
    d.rectangle((42, 42, 58, 58), fill=(0, 0, 255, 80))
    assert not _frame_verified(_two_shapes(), faded)
    assert _frame_defects(_two_shapes(), faded).occupancy > _OCC_TOL


def test_within_tolerance_shift_verifies() -> None:
    """A 1px translation is inside the alignment search and must realign to a
    clean pass — and must NOT wrap edge content around."""
    shifted = _shift_onto_transparent(_two_shapes(), 1, 1)
    assert _frame_verified(_two_shapes(), shifted)


def test_beyond_tolerance_shift_fails() -> None:
    """A 3px translation cannot be corrected by the ±1 search, so the
    displaced solid pixels register as missing+extra and it fails."""
    shifted = _shift_onto_transparent(_two_shapes(), 3, 3)
    assert not _frame_verified(_two_shapes(), shifted)
    assert _frame_defects(_two_shapes(), shifted).occupancy > _OCC_TOL


def test_colour_noise_over_complete_geometry_verifies() -> None:
    """Mockingbird's real regime: geometry is complete but resvg vs Pillow
    disagree on interior colour across a minority of solid pixels. Occupancy is
    ~0, so the frame must still verify — completeness, not pixel-exactness, is
    the bar. (Occupancy and colour are graded separately for exactly this.)"""
    src = _two_shapes()  # two 17x17 shapes -> 578 solid px
    noisy = src.copy()
    # Recolour a thin interior strip of one shape: ~9% of the overlap disagrees,
    # like resvg-vs-Pillow AA fringes, well under the whole-region miscolour a
    # dropped/wrong part would produce. Footprint is untouched -> occupancy 0.
    ImageDraw.Draw(noisy).rectangle((6, 6, 22, 8), fill=(20, 235, 40, 255))
    defect = _frame_defects(src, noisy)
    assert defect.occupancy <= _OCC_TOL, defect
    assert 0.0 < defect.rgb <= 0.12, defect
    assert _frame_verified(src, noisy)


def test_shift_does_not_wrap() -> None:
    """The translate helper must lose off-canvas content, not wrap it — else a
    shape pushed off one edge would reappear on the other and hide a defect."""
    edge = _canvas()
    ImageDraw.Draw(edge).rectangle((0, 0, 6, 6), fill=(255, 0, 0, 255))
    moved = _shift_onto_transparent(edge, -10, 0)
    assert moved.split()[3].getbbox() is None
