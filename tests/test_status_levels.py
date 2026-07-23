"""Poison test for honest conversion status levels (GPT 5.6 review item 3).

The bug: a conversion was called ``captured`` when only a small SAMPLE of
frames (six by default) had been raster-verified — establishing nothing about
the other frames. ``captured`` must mean *every* published frame was verified;
a clean-but-sampled result is ``sampled``; anything with a gap is ``partial``.

``_classify_status`` is a pure function precisely so this boundary is pinned
directly, not inferred from a full render.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from equivalence_harness import _classify_status  # noqa: E402


def test_sampled_is_not_captured() -> None:
    """The exact review scenario: 6 of 36 frames verified, no gaps, sampling
    run. This must NOT be 'captured'."""
    s = _classify_status(complete=True, unsupported=set(), dangling=[],
                         failed=0, verified=6, total=36, full=False)
    assert s == "sampled", s


def test_full_all_frames_verified_is_captured() -> None:
    s = _classify_status(True, set(), [], 0, 36, 36, full=True)
    assert s == "captured", s


def test_full_but_not_every_frame_verified_is_sampled() -> None:
    """A --full run where some frames were skipped (missing row/rect) cannot
    claim full fidelity."""
    s = _classify_status(True, set(), [], 0, 30, 36, full=True)
    assert s == "sampled", s


def test_gaps_are_partial() -> None:
    assert _classify_status(False, set(), [], 0, 36, 36, True) == "partial"
    assert _classify_status(True, {"paste"}, [], 0, 36, 36, True) == "partial"
    assert _classify_status(True, set(), ["part_009"], 0, 36, 36, True) == "partial"
    assert _classify_status(True, set(), [], 2, 36, 36, True) == "partial"


def test_nothing_verifiable_is_partial_not_captured() -> None:
    """resvg absent / no comparable frame: fidelity is unestablished, so the
    result is never 'captured' or 'sampled'."""
    s = _classify_status(True, set(), [], 0, 0, 36, full=True)
    assert s == "partial", s
