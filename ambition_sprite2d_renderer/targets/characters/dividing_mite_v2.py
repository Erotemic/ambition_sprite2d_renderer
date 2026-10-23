"""The Dividing Mite, v2: a cell caught halfway through dividing, on eight legs.

Look A of the 2026-10-22 candidates (``scripts/svg_art/mites_art.py``), cast
2026-10-23: Jon asked to see the redesign in the game and did not pick, so A
was chosen. A peanut of two teal lobes, each with its own nucleus, feeler and
four legs, cinched at the waist by a bright cleavage ring; one dark visor eye
and a pair of hooked mandibles at the front (its swipe).

It has four hit points and on death splits into two Puppy Slugs, one each
side of the corpse (``divides_into`` in the catalog). Its ``death`` row shows
that: it strains, the ring goes hot, and the lobes pull apart left and right.
The first Dividing Mite (a robot-toon config, ``configs/dividing_mite.yaml``)
stays renderable.
"""

from __future__ import annotations

from pathlib import Path

from . import _mite_v2

TARGET_NAME = "dividing_mite_v2"

ACTOR_METADATA = _mite_v2.actor_metadata(
    TARGET_NAME, character_id="npc_dividing_mite", display_name="Dividing Mite", mass_class="Medium", trait="replicator",
    live=(0.32, 0.56), head=(292.0, 248.0), chest=(200.0, 268.0), jaws=(306.0, 306.0),
    notes=["The SVG owns the part shapes; each lobe, leg segment, feeler and mandible turns about its own joint.",
           "Each leg is a thigh and a shin solved to a foot target, so the feet stay planted while the body moves.",
           "death: the cleavage ring goes hot, then the two lobes pull apart; the game spawns the two Puppy Slugs."],
)

#: The body: both lobes and the reach of the legs, in SVG units (x0, y0, x1, y1).
BODY_BOX = _mite_v2.body_box(TARGET_NAME, *(58.0, 210.0, 342.0, 354.0))


def render(out_dir: str | Path, **opts):
    del opts
    return _mite_v2.render(TARGET_NAME, ACTOR_METADATA, BODY_BOX, out_dir)


__all__ = ["ACTOR_METADATA", "BODY_BOX", "TARGET_NAME", "render"]
