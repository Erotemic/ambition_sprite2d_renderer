"""The rig + minimal SVG reproduces the pirate sprites near-perfectly.

The pirate is assembled from a minimal component scene (rigid paper-doll parts
placed by the explicit skeleton, plus the posed limb strokes). These tests pin
that the SVG assembly reproduces the authoritative PIL raster: a dropped or
mislocated part would spike the occupancy defect far past these envelopes.

Comparison is in the supersampled paint space (before the sheet crop/fit), so it
isolates rig+SVG reproduction from the packaging step. It uses the same
alpha-aware, symmetric metric the fidelity verifier uses
(``equivalence_harness._frame_defects``). Skipped when ``resvg_py`` is absent.
"""
from __future__ import annotations

import io
import statistics
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

resvg_py = pytest.importorskip("resvg_py")

from ambition_sprite2d_renderer.authoring.draw_recorder import PillowPartDraw  # noqa: E402
from ambition_sprite2d_renderer.core.draw import blending_draw  # noqa: E402
from ambition_sprite2d_renderer.targets.characters import _pirate_common as P  # noqa: E402
from equivalence_harness import _frame_defects  # noqa: E402

SS = P.BASE_FRAME[0] * P.SCALE
# admiral exercises the per-kind skeleton branch (narrower shoulders, eyepatch).
ROLES = ["pirate_raider", "pirate_admiral"]

# Envelopes from the measured reproduction (median occ ~0.047, worst ~0.091 on
# the slash frames whose translucent swoosh diverges by design). Generous enough
# to absorb resvg-version AA drift, tight enough that a dropped/added part (which
# lands occupancy in the 0.2+ range) fails hard.
MEDIAN_OCC_MAX = 0.060
PER_FRAME_OCC_MAX = 0.110
PER_FRAME_RGB_MAX = 0.080
DROPPED_PART_OCC = 0.150  # any frame above this means real geometry is missing


def _pil(kind, anim, i, n):
    img = Image.new("RGBA", (SS, SS), (0, 0, 0, 0))
    P.paint_character(PillowPartDraw(blending_draw(img)), kind, anim, i, n, P.BASE_FRAME)
    return img


def _svg(scene, anim, i):
    png = resvg_py.svg_to_bytes(svg_string=scene.frame_doc(anim, i))
    return Image.open(io.BytesIO(bytes(png))).convert("RGBA")


@pytest.mark.parametrize("kind", ROLES)
def test_svg_scene_reproduces_pirate(kind: str) -> None:
    scene = P.build_scene(kind)
    assert scene.missing_part_refs() == [], "every <use> must resolve to a part"
    # Minimal: parts are deduped, far fewer than the 38 posed frames.
    assert len(scene.parts) < 30, len(scene.parts)

    occs = []
    for anim, n, _ms in P.ANIMATIONS:
        for i in range(n):
            d = _frame_defects(_pil(kind, anim, i, n), _svg(scene, anim, i))
            occs.append(d.occupancy)
            assert d.occupancy <= PER_FRAME_OCC_MAX, (kind, anim, i, d)
            assert d.occupancy <= DROPPED_PART_OCC, (kind, anim, i, "part missing?", d)
            assert d.rgb <= PER_FRAME_RGB_MAX, (kind, anim, i, d)
    assert statistics.median(occs) <= MEDIAN_OCC_MAX, (kind, statistics.median(occs))


def test_only_the_translucent_slash_swoosh_exceeds_the_solid_floor() -> None:
    """The reproduction of SOLID geometry is uniform (~0.045-0.05). The only
    frames past ~0.06 are slash frames, and only because of the translucent
    swoosh effect (cross-rasterizer compositing divergence, the accepted glow
    class) — not lost character geometry. Pin that story so a real solid-geometry
    regression can't hide behind the slash allowance."""
    kind = "pirate_raider"
    scene = P.build_scene(kind)
    over = []
    for anim, n, _ms in P.ANIMATIONS:
        for i in range(n):
            d = _frame_defects(_pil(kind, anim, i, n), _svg(scene, anim, i))
            if d.occupancy > 0.06:
                over.append(anim)
    assert over, "expected the slash swoosh frames to sit above the solid floor"
    assert set(over) == {"slash"}, f"only slash should exceed the solid floor: {set(over)}"
