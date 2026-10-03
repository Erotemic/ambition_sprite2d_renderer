"""The swing fighters are drawn from parts (the game repository's
`docs/planning/engine/mary-o-part-realization.md`).

Eight characters (the three polygons, carl_stargan, director, officer,
performer, medic) composite their authored strike effects with
``swing_effects.composite_authored_effect``, through rigdoc's seams, so a swing
trail is one overlay draw a frame. A trail is drawn from the frames before it,
so these targets render a CLIP at once and cache it; their flipbooks record
each clip whole, from the uncached function (``build_rig_flipbook``'s
``render_clip``).

This holds a sample of rows from two of them (a trail and a poke on
pointed_polygon; performer's trapdoor and wire, the effects drawn under and
over the body), and the poisons that prove the measure sees a missing effect.
"""

from __future__ import annotations

import dataclasses

import pytest

from ambition_sprite2d_renderer.authoring.part_flipbook import (
    CONTINUOUS_REPLAY_TOLERANCE as TOLERANCE,
    build_rig_flipbook,
    largest_wrong_blob,
    parity,
)
from ambition_sprite2d_renderer.targets.characters import performer, pointed_polygon

PARITY_BOUND = 0.01
BLOB_BOUND = 6


def _clip_rows(rows, spec_for, effects, plain=1):
    """``plain`` rows with no effect, then one row for each of ``effects``."""
    chosen = [row for row in rows if not spec_for(row[0])][:plain]
    for effect in effects:
        chosen.append(next(row for row in rows if (spec_for(row[0]) or {}).get("effect") == effect))
    return chosen


def _record(target, rows, render, clip):
    size = render(rows[0][0], 0, rows[0][1]).size
    flipbook = build_rig_flipbook(
        target, rows, render, None, (size[0] / 2, float(size[1])), size, render_clip=lambda row, n: list(clip(row, n))
    )
    references = {(name, i): frame for name, n, _ms in rows for i, frame in enumerate(clip(name, n))}
    return flipbook, references


@pytest.fixture(scope="module")
def polygon():
    rows = _clip_rows(pointed_polygon._doc().rows(), pointed_polygon._spec_for, ("trail", "poke"))
    return _record("pointed_polygon", rows, pointed_polygon._render_frame, pointed_polygon._clip_frames.__wrapped__)


@pytest.fixture(scope="module")
def stage():
    fighter = performer._FIGHTER
    rows = _clip_rows(fighter.doc().rows(), fighter.spec_for, ("trapdoor", "wire"))
    clip = lambda row, n: type(fighter)._clip_frames.__wrapped__(fighter, row, n)  # noqa: E731
    return _record("performer", rows, fighter.render_frame, clip)


def _outside(reference, candidate):
    return (
        parity(reference, candidate, **TOLERANCE) > PARITY_BOUND
        or largest_wrong_blob(reference, candidate, **TOLERANCE) > BLOB_BOUND
    )


@pytest.mark.parametrize("which", ["polygon", "stage"])
def test_each_clip_is_drawn_from_parts_and_is_the_published_frame(which, request):
    flipbook, references = request.getfixturevalue(which)
    failures = [f"{name}[{i}]" for (name, i), ref in references.items() if _outside(ref, flipbook.recompose(name, i))]
    assert references and not failures, "frames the flipbook does not reproduce: " + ", ".join(failures)


def test_the_effects_are_overlays_in_paint_order(polygon, stage):
    for flipbook in (polygon[0], stage[0]):
        tracks = {d.track for _row, (_d, frames) in flipbook.clips.items() for frame in frames for d in frame}
        assert "overlay:swing" in tracks, sorted(tracks)
    # The trapdoor opens UNDER the body: its layer is drawn before every part.
    flipbook = stage[0]
    under = [
        frame
        for _row, (_d, frames) in flipbook.clips.items()
        for frame in frames
        if any(d.track == "overlay:swing_under" for d in frame)
    ]
    assert under and all(frame[0].track == "overlay:swing_under" for frame in under)


def _dropped_effect_fails(recorded, track):
    flipbook, references = recorded
    for (name, i), reference in references.items():
        draws = flipbook.clips[name][1][i]
        if not any(d.track == track for d in draws):
            continue
        assert not _outside(reference, flipbook.recompose(name, i))
        poisoned = dataclasses.replace(
            flipbook, clips={**flipbook.clips, name: (0.1, [[d for d in draws if d.track != track]])}
        )
        if _outside(reference, poisoned.recompose(name, 0)):
            return True
    return False


def test_a_dropped_swing_trail_fails(polygon):
    assert _dropped_effect_fails(polygon, "overlay:swing")


def test_a_dropped_trapdoor_fails(stage):
    assert _dropped_effect_fails(stage, "overlay:swing_under")
