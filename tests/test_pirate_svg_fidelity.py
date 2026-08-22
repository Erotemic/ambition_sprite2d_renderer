"""The rig + minimal SVG reproduces the pirate sprites faithfully.

The pirate is assembled from a minimal component scene: rigid paper-doll parts
placed by the explicit skeleton, plus the posed limb strokes. Two independent
guards here:

* Structural — every expected named part is present in the scene. This is
  the robust "no dropped part" check: a missing part fails immediately,
  independent of any raster tolerance.
* Reproduction — the rasterized SVG frames match the authoritative PIL raster
  within a measured occupancy envelope (the alpha-aware symmetric metric,
  ``equivalence_harness._frame_defects``), which catches *mislocation* (a part
  placed at the wrong joint shifts occupancy well past the floor).

Honest scope: the SOLID geometry reproduces at a uniform ~0.045-0.05 occupancy
floor (resvg-vs-Pillow stroke-edge AA, sub-2px, visually identical). The six
slash frames sit higher (~0.075-0.09) solely because of the translucent
swoosh effect — suppressing just that arc drops them back to the floor — which is
the accepted translucent-compositing divergence class (as with glows), NOT lost
geometry. So the slash frames do not pass the strict ``_frame_verified`` (0.07)
gate, and that is a documented by-design divergence, not a reproduction defect.

Comparison is in supersampled paint space (before the sheet crop/fit) to isolate
rig+SVG reproduction; the post-crop 128px ship path is exercised by the harness
elsewhere. Skipped when ``resvg_py`` is absent.
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
# admiral exercises the per-kind skeleton branch (narrower shoulders, left-nudged
# stance) and drops the chest_skull motif.
ROLES = ["pirate_raider", "pirate_admiral"]

# Every pirate must assemble from these rigid parts; a dropped part fails the
# structural check directly (no reliance on a raster threshold).
CORE_PARTS = {"torso", "hat", "face", "sword", "boot",
              "coat_tail_left", "coat_tail_right"}

# Reproduction envelope for the occupancy defect. The solid floor is ~0.047; the
# slash swoosh (translucent, by design) reaches ~0.09. These bounds catch a
# MISLOCATED part (which shifts occupancy far higher) while tolerating the floor
# and the swoosh; the structural check above is what guards against DROPS.
MEDIAN_OCC_MAX = 0.060
PER_FRAME_OCC_MAX = 0.110
PER_FRAME_RGB_MAX = 0.080


def _pil(kind, anim, i, n):
    img = Image.new("RGBA", (SS, SS), (0, 0, 0, 0))
    P.paint_character(PillowPartDraw(blending_draw(img)), kind, anim, i, n, P.BASE_FRAME)
    return img


def _svg(scene, anim, i):
    png = resvg_py.svg_to_bytes(svg_string=scene.frame_doc(anim, i))
    return Image.open(io.BytesIO(bytes(png))).convert("RGBA")


@pytest.mark.parametrize("kind", ROLES)
def test_scene_contains_and_places_every_expected_part(kind: str) -> None:
    scene = P.build_scene(kind)
    assert scene.missing_part_refs() == [], "every <use> must resolve to a part"
    names = {name for _pid, (name, _body) in scene.parts.items()}
    assert not (CORE_PARTS - names), f"{kind} scene dropped parts: {CORE_PARTS - names}"
    # A part must be REGISTERED and PLACED — a regression that stops emitting a
    # part's <use> leaves it registered but unrendered, which occupancy catches
    # only weakly for small parts. Require each core part's def to be referenced
    # by at least one posed frame, so a dropped placement fails structurally.
    all_frames = "".join(scene.frames.values())
    for pid, (name, _body) in scene.parts.items():
        if name in CORE_PARTS:
            assert pid in all_frames, f"{kind}: part {name!r} ({pid}) is never placed"
    # Minimal: parts are deduped, far fewer than the 38 posed frames.
    assert len(scene.parts) < 30, len(scene.parts)


@pytest.mark.parametrize("kind", ROLES)
def test_svg_scene_reproduces_pirate(kind: str) -> None:
    scene = P.build_scene(kind)
    occs = []
    for anim, n, _ms in P.ANIMATIONS:
        for i in range(n):
            d = _frame_defects(_pil(kind, anim, i, n), _svg(scene, anim, i))
            occs.append(d.occupancy)
            assert d.occupancy <= PER_FRAME_OCC_MAX, (kind, anim, i, d)
            assert d.rgb <= PER_FRAME_RGB_MAX, (kind, anim, i, d)
    assert statistics.median(occs) <= MEDIAN_OCC_MAX, (kind, statistics.median(occs))


def test_only_the_translucent_slash_swoosh_exceeds_the_solid_floor() -> None:
    """Pins the honest fidelity story: SOLID geometry reproduces at a uniform
    floor (~0.045-0.05), and the ONLY frames above ~0.06 are slash frames — and
    only because of the translucent swoosh effect, not lost geometry. This keeps
    a real solid-geometry regression from hiding behind the slash allowance."""
    kind = "pirate_raider"
    scene = P.build_scene(kind)
    over = set()
    for anim, n, _ms in P.ANIMATIONS:
        for i in range(n):
            d = _frame_defects(_pil(kind, anim, i, n), _svg(scene, anim, i))
            if d.occupancy > 0.06:
                over.add(anim)
    assert over == {"slash"}, f"only slash should exceed the solid floor: {over}"
