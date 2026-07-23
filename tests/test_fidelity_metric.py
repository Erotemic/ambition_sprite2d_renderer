"""Poison tests for the symmetric, alpha-aware frame-fidelity metric.

Two GPT 5.6 review rounds shaped this:

1. The verifier first compared colour only inside the *intersection* of opaque
   pixels, so DROPPED or INVENTED geometry was never scored — a half-empty
   frame passed as ``captured``.
2. The first fix still thresholded alpha at ``>200`` to build a binary "solid"
   mask, which discarded EVERY translucent pixel. A missing/invented/wrong-alpha
   translucent component (glow, beam, cloth, effect) then scored ``(0.0, 0.0)``
   and passed anyway.

The metric is now continuous and alpha-aware (``_frame_defects`` ->
``occupancy`` over the union of meaningful alpha *mass*, and ``rgb`` weighted by
mutual occupancy). A frame is ``_frame_verified`` only when both pass a tight
occupancy bar (completeness, any opacity) and a looser rgb bar (rasterizer/AA
colour slack). These tests pin:

* omitted / invented OPAQUE geometry fails,
* omitted / invented / wrong-alpha TRANSLUCENT geometry fails (the round-2 hole),
* a translucent component is never silently discarded (nonzero occupancy),
* correct RGB but wrong alpha fails,
* in-tolerance 1px shift verifies (no edge wrap), beyond-tolerance fails,
* colour noise over complete geometry still verifies.
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

W = H = 96


def _canvas() -> Image.Image:
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def _body(img: Image.Image) -> Image.Image:
    """A big matching opaque body, present in every fixture so the frames are
    otherwise-identical and the appendage is what the metric must catch."""
    ImageDraw.Draw(img).rectangle((8, 8, 60, 88), fill=(200, 60, 40, 255))
    return img


def _translucent_appendage(img: Image.Image, alpha: int) -> Image.Image:
    """A sizeable translucent limb/beam beside the body."""
    ImageDraw.Draw(img).rectangle((66, 20, 90, 78), fill=(40, 180, 255, alpha))
    return img


def test_identical_frames_verify() -> None:
    a = _translucent_appendage(_body(_canvas()), 120)
    d = _frame_defects(a, a.copy())
    assert d.occupancy == 0.0 and d.rgb == 0.0
    assert _frame_verified(a, a.copy())


# --- round 1: opaque geometry --------------------------------------------------
def _two_opaque() -> Image.Image:
    img = _canvas()
    d = ImageDraw.Draw(img)
    d.rectangle((8, 8, 40, 40), fill=(255, 0, 0, 255))
    d.rectangle((56, 56, 88, 88), fill=(0, 0, 255, 255))
    return img


def _one_opaque() -> Image.Image:
    img = _canvas()
    ImageDraw.Draw(img).rectangle((8, 8, 40, 40), fill=(255, 0, 0, 255))
    return img


def test_omitted_opaque_fails() -> None:
    d = _frame_defects(_two_opaque(), _one_opaque())
    assert d.occupancy > _OCC_TOL, d
    assert not _frame_verified(_two_opaque(), _one_opaque())


def test_invented_opaque_fails() -> None:
    assert not _frame_verified(_one_opaque(), _two_opaque())


# --- round 2: translucent geometry (the reported hole) -------------------------
def test_omitted_translucent_component_fails() -> None:
    """GPT's core round-2 repro: matching opaque body, but the render DROPS a
    translucent appendage. Under the old >200 mask this scored (0,0) and passed;
    it must now register real occupancy and fail."""
    src = _translucent_appendage(_body(_canvas()), 120)
    dropped = _body(_canvas())  # body only, no appendage
    d = _frame_defects(src, dropped)
    assert d.occupancy > _OCC_TOL, d
    assert not _frame_verified(src, dropped)


def test_invented_translucent_component_fails() -> None:
    src = _body(_canvas())
    invented = _translucent_appendage(_body(_canvas()), 120)
    assert not _frame_verified(src, invented)


def test_wrong_subthreshold_alpha_fails() -> None:
    """Two meaningful but sub-threshold alphas (90 vs 200): both would have been
    lumped as either <200 or >200 by the old cutoff. The alpha error must be
    scored on a continuous basis and fail."""
    src = _translucent_appendage(_body(_canvas()), 90)
    wrong = _translucent_appendage(_body(_canvas()), 200)
    d = _frame_defects(src, wrong)
    assert d.occupancy > _OCC_TOL, d
    assert not _frame_verified(src, wrong)


def test_translucent_component_is_never_discarded() -> None:
    """Property test: even a SMALL missing translucent component produces
    strictly-positive occupancy — it is no longer thrown away by an alpha
    cutoff, whether or not it crosses the pass threshold."""
    src = _canvas()
    ImageDraw.Draw(src).rectangle((8, 8, 60, 88), fill=(200, 60, 40, 255))
    ImageDraw.Draw(src).rectangle((70, 40, 78, 56), fill=(40, 180, 255, 100))
    dropped = _canvas()
    ImageDraw.Draw(dropped).rectangle((8, 8, 60, 88), fill=(200, 60, 40, 255))
    assert _frame_defects(src, dropped).occupancy > 0.0


def test_correct_rgb_wrong_alpha_fails() -> None:
    """Same colours, shapes drawn far more translucent than the source — the
    alpha-mass mismatch must fail even though hue matches."""
    src = _translucent_appendage(_body(_canvas()), 255)
    faded = _translucent_appendage(_body(_canvas()), 40)
    assert not _frame_verified(src, faded)


# --- alignment -----------------------------------------------------------------
def test_within_tolerance_shift_verifies() -> None:
    src = _translucent_appendage(_body(_canvas()), 120)
    shifted = _shift_onto_transparent(src, 1, 1)
    assert _frame_verified(src, shifted)


def test_beyond_tolerance_shift_fails() -> None:
    src = _translucent_appendage(_body(_canvas()), 120)
    shifted = _shift_onto_transparent(src, 4, 4)
    assert not _frame_verified(src, shifted)
    assert _frame_defects(src, shifted).occupancy > _OCC_TOL


def test_colour_noise_over_complete_geometry_verifies() -> None:
    """Mockingbird's regime: geometry complete at every opacity, but resvg vs
    Pillow disagree on interior colour across a minority of pixels. Occupancy
    ~0, so it must still verify — completeness, not pixel-exactness, is the bar."""
    src = _translucent_appendage(_body(_canvas()), 200)
    noisy = _translucent_appendage(_body(_canvas()), 200)
    # nudge a thin interior strip's colour; footprint + alpha untouched
    ImageDraw.Draw(noisy).rectangle((8, 8, 60, 14), fill=(160, 40, 30, 255))
    d = _frame_defects(src, noisy)
    assert d.occupancy <= _OCC_TOL, d
    assert d.rgb > 0.0, "the colour nudge should register as rgb defect"
    assert _frame_verified(src, noisy)


def test_shift_does_not_wrap() -> None:
    """The translate helper must lose off-canvas content, not wrap it."""
    edge = _canvas()
    ImageDraw.Draw(edge).rectangle((0, 0, 6, 6), fill=(255, 0, 0, 255))
    moved = _shift_onto_transparent(edge, -10, 0)
    assert moved.split()[3].getbbox() is None
