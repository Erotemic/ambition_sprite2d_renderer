"""A half of a Dividing Mite, v2: what one splits into.

Jon, 2026-11-11: "dividing mite needs to divide into the 2 parts of itself,
not 2 puppy slugs." One lobe of the parent's cell (``cast_dividing_half`` in
``scripts/svg_art/mites_art.py``), the size of one of the parent's lobes, with
its own nucleus and feeler; it grew an eye, mandibles and eight short legs to
live alone, and its back is the pale scar of the split. It cannot split again:
its ``death`` row sags onto its belly.
"""

from __future__ import annotations

from pathlib import Path

from . import _mite_v2

TARGET_NAME = "dividing_mite_half_v2"

ACTOR_METADATA = _mite_v2.actor_metadata(
    TARGET_NAME, character_id="npc_dividing_mite_half", display_name="Dividing Mite Half", mass_class="Light", trait="replicator",
    live=(0.32, 0.56), head=(238.0, 248.0), chest=(200.0, 268.0), jaws=(254.0, 306.0),
    notes=["The SVG owns the part shapes; the lobe, each leg segment, the feeler and the mandibles turn about their own joints.",
           "Each leg is a thigh and a shin solved to a foot target, so the feet stay planted while the body moves.",
           "death: it cannot split again; it shudders and sags onto its belly with its legs splayed."],
)

#: The body: the lobe and the reach of the legs, in SVG units (x0, y0, x1, y1).
BODY_BOX = _mite_v2.body_box(TARGET_NAME, *(124.0, 210.0, 276.0, 354.0))


def render(out_dir: str | Path, **opts):
    del opts
    return _mite_v2.render(TARGET_NAME, ACTOR_METADATA, BODY_BOX, out_dir)


__all__ = ["ACTOR_METADATA", "BODY_BOX", "TARGET_NAME", "render"]
