"""The Exploding Mite, v2: a round bomb on eight legs, its fuse lit.

Look A of the 2026-10-22 candidates (``scripts/svg_art/mites_art.py``), cast
2026-10-23: Jon asked to see the redesign in the game and did not pick, so A
was chosen. A gunmetal pressure shell with a hazard-striped belt, a brass cap
and a lit fuse, a pressure valve at its back, one red visor eye under a brow
plate, and a pair of hooked mandibles at the front (its swipe).

It has two hit points and its corpse detonates (``explodes_on_death`` in the
catalog). Its ``death`` row is the wind-up: the fuse burns down to the cap
while the shell swells, its seams glow and then go white hot. The blast is
the game's effect, not the sheet's. The first Exploding Mite (a robot-toon
config, ``configs/exploding_mite.yaml``) stays renderable.
"""

from __future__ import annotations

from pathlib import Path

from . import _mite_v2

TARGET_NAME = "exploding_mite_v2"

ACTOR_METADATA = _mite_v2.actor_metadata(
    TARGET_NAME, character_id="npc_exploding_mite", display_name="Exploding Mite", mass_class="Light", trait="volatile",
    live=(0.30, 0.52), head=(244.0, 240.0), chest=(196.0, 262.0), jaws=(266.0, 312.0),
    notes=["The SVG owns the part shapes; each leg segment, mandible and the fuse turn about their own joints.",
           "Each leg is a thigh and a shin solved to a foot target, so the feet stay planted while the body moves.",
           "The shell is drawn at three stages of the wind-up and the wick at three lengths; the spark is drawn twice to flicker.",
           "death: the fuse burns down while the shell swells and goes white hot; the blast is the game's effect."],
)

#: The body: the shell and the reach of the legs, in SVG units (x0, y0, x1, y1).
BODY_BOX = _mite_v2.body_box(TARGET_NAME, *(76.0, 184.0, 316.0, 354.0))


def render(out_dir: str | Path, **opts):
    del opts
    return _mite_v2.render(TARGET_NAME, ACTOR_METADATA, BODY_BOX, out_dir)


__all__ = ["ACTOR_METADATA", "BODY_BOX", "TARGET_NAME", "render"]
