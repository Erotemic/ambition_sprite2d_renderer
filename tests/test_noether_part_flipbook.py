"""Noether is drawn from parts (`docs/planning/engine/mary-o-part-realization.md`
in the game repository).

Her rig is supersampled (2x at render scale 2), so her flipbook is continuous,
as the robot's is. What she adds is the ETHEREAL HUM: a breathing two-radius
glow of her own silhouette behind every frame. It is painted at an eighth of
the frame's resolution (``noether_effects.HUM_REDUCTION``) and published as
one overlay a frame, drawn eight times enlarged (a draw's ``scale``). Her
special moves' effects go through ``compose_rig_frame``'s seams.

The publish replays every frame (``build_rig_flipbook``); this holds a sample
that covers each mechanism, and the poisons that prove the measure sees each
go wrong.
"""

from __future__ import annotations

import dataclasses

import pytest
from PIL import Image, ImageFilter

from ambition_sprite2d_renderer.authoring.part_flipbook import (
    CONTINUOUS_REPLAY_TOLERANCE as TOLERANCE,
    PLACEMENT_CONTINUOUS,
    build_rig_flipbook,
    largest_wrong_blob,
    parity,
)
from ambition_sprite2d_renderer.targets.characters import noether, noether_effects

PARITY_BOUND = 0.01
BLOB_BOUND = 6

#: Rigid parts and the hum at its quiet and its full breath (idle), a tweened
#: loop (walk), effects behind and in front of the body (symmetry_proof,
#: noether_theorem).
SAMPLE = ("idle", "walk", "symmetry_proof", "noether_theorem")


@pytest.fixture(scope="module")
def sample():
    rows = [row for row in noether.ROWS if row[0] in SAMPLE]
    assert sorted(name for name, _n, _ms in rows) == sorted(SAMPLE)
    size = noether.frame_size()
    metrics = noether.authored_body_metrics(size[0], size[1], noether._silhouette_profile())
    feet = (metrics["feet_pixel"]["x"], metrics["feet_pixel"]["y"])
    tweened = [name for name in noether.TWEENED_ROWS if name in SAMPLE]
    flipbook = build_rig_flipbook(noether.TARGET_NAME, rows, noether.render_frame, None, feet, size, tweened)
    references = {
        (name, index): noether.render_frame(name, index, count) for name, count, _ms in rows for index in range(count)
    }
    return flipbook, references


def _outside(reference, candidate):
    return (
        parity(reference, candidate, **TOLERANCE) > PARITY_BOUND
        or largest_wrong_blob(reference, candidate, **TOLERANCE) > BLOB_BOUND
    )


def test_the_sample_is_drawn_from_parts_and_is_the_published_frame(sample):
    flipbook, references = sample
    assert flipbook.placement == PLACEMENT_CONTINUOUS
    failures = [f"{name}[{index}]" for (name, index), ref in references.items() if _outside(ref, flipbook.recompose(name, index))]
    assert len(references) == sum(n for name, n, _ms in noether.ROWS if name in SAMPLE) > 0
    assert not failures, "frames the flipbook does not reproduce: " + ", ".join(failures)


def test_the_hum_is_one_reduced_overlay_a_frame(sample):
    flipbook, _references = sample
    for name in SAMPLE:
        for frame in flipbook.clips[name][1]:
            hums = [d for d in frame if d.track == "overlay:hum"]
            k = float(noether_effects.HUM_REDUCTION)
            assert len(hums) == 1 and hums[0].scale == (k, k), name
            assert frame[0].track == "overlay:hum", "the hum is drawn first, behind everything"
    tracks = {d.track for frame in flipbook.clips["symmetry_proof"][1] for d in frame}
    assert {"overlay:fx_behind", "overlay:fx_front"} & tracks, tracks


def test_the_reduced_hum_is_the_full_resolution_hum():
    """The hum painted small and enlarged against the hum painted at full size
    (the formula as it was before the reduction): no pixel of the composed
    frame differs by more than 16 levels."""
    doc = noether._doc()
    for row, count in (("idle", 8), ("walk", 8)):
        for index in (0, count // 2):
            t = doc.frame_time(row, index, count)
            rig = doc.render_at(row, t, solved=doc.solve(row, t), padding=noether.RIG_RENDER_PADDING)
            full = _full_resolution_hum(rig, t)
            assert parity(full, noether_effects.apply_ethereal_hum(rig, rig, t), threshold=16, radius=0) == 0.0


def _full_resolution_hum(frame, t):
    import math

    from ambition_sprite2d_renderer.targets.characters.noether_effects import ETHER, VIOLET, _alpha_scaled

    alpha = frame.getchannel("A")
    breath = 0.5 + 0.5 * math.sin(t * math.tau - math.pi * 0.5)
    bloom = breath * breath
    close = alpha.filter(ImageFilter.GaussianBlur(5.5 + 3.5 * breath))
    broad = alpha.filter(ImageFilter.GaussianBlur(18.0 + 16.0 * bloom))
    aura = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    violet = Image.new("RGBA", frame.size, VIOLET[:3] + (0,))
    violet.putalpha(_alpha_scaled(broad, 0.28 + 0.30 * bloom))
    aura.alpha_composite(violet)
    cyan = Image.new("RGBA", frame.size, ETHER[:3] + (0,))
    cyan.putalpha(_alpha_scaled(close, 0.55 + 0.30 * breath))
    aura.alpha_composite(cyan)
    aura.alpha_composite(frame)
    return aura


# -- the measures can fail --------------------------------------------------------


def _fails(sample, row, index, change):
    flipbook, references = sample
    reference = references[(row, index)]
    assert not _outside(reference, flipbook.recompose(row, index)), "the honest frame is already outside"
    draws = change(list(flipbook.clips[row][1][index]))
    poisoned = dataclasses.replace(flipbook, clips={**flipbook.clips, row: (flipbook.clips[row][0], [draws])})
    return _outside(reference, poisoned.recompose(row, 0))


def test_a_dropped_hum_fails(sample):
    assert _fails(sample, "idle", 0, lambda draws: [d for d in draws if d.track != "overlay:hum"])


def test_a_hum_drawn_unscaled_fails(sample):
    def unscaled(draws):
        return [dataclasses.replace(d, scale=(1.0, 1.0)) if d.track == "overlay:hum" else d for d in draws]

    assert _fails(sample, "idle", 4, unscaled)


@pytest.mark.parametrize("track", ["head_base", "near_arm_l"])
def test_a_visible_part_a_pixel_off_fails(sample, track):
    def nudge(draws):
        assert any(d.track == track for d in draws), sorted({d.track for d in draws})
        return [dataclasses.replace(d, at=(d.at[0] + 1.0, d.at[1])) if d.track == track else d for d in draws]

    assert _fails(sample, "idle", 0, nudge)
