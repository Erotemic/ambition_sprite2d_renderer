"""Genghis Can't, look C ("steppe"): the brother with a horde and also reservations.

An SVG rig (``_genghis_pair_v2.py`` says where the drawing and the rows live).
He reads as Genghis Khan first, in the same deel, sash, cuffs and boots as his
brother. The pun is in his body: he stoops, chin down, shoulders up, his brow
lifted in the middle, and cups his chin in thought; everything on him that can
droop droops (the moustache, the tuft, the fox-fur flaps tied under his chin),
and he has gone greyer. A maroon deel, a slate sash, a quiver.

His first design, the procedural ``genghis_cant``, stays renderable as the
lineage; the catalog row ``npc_genghis_cant`` shows this one.
"""

from __future__ import annotations

from pathlib import Path

from . import _genghis_pair_v2 as pair

TARGET_NAME = "genghis_cant_v2"
#: The face's centre in frame pixels (the portraits' guide).
HEAD = (75.7, 56.2)

ACTOR_METADATA = pair.actor_metadata(
    target=TARGET_NAME,
    character_id="npc_genghis_cant",
    display_name="Genghis Can't",
    sockets={"head": HEAD, "chest": (68.4, 89.6), "hand_l": (71.4, 101.9), "hand_r": (77.4, 78.9), "speech_bubble": (78.0, 14.0)},
    barks=(
        "Perhaps we could postpone the invasion.",
        "This map has too many directions.",
        "Retreat is a kind of strategy... probably.",
    ),
    authoring=(
        "Genghis Can't is the hesitant, ethically reflective half of a paired Genghis "
        "Khan parody. The name turns conquest into doubt: he has the same potential "
        "horde as his brother but cannot stop calculating whether taking something is "
        "worth its human cost."
    ),
    gameplay=(
        "Use as a cautious commander, defensive rival, advisor, or paired boss. He "
        "should delay, inspect consequences, and sometimes discover that refusing an "
        "action is the stronger move."
    ),
)


def render(out_dir: str | Path, **opts):
    del opts
    return pair.render(TARGET_NAME, ACTOR_METADATA, out_dir)


def render_portraits(out_dir: str | Path, **opts):
    del opts
    return pair.render_portraits(TARGET_NAME, HEAD, out_dir)


__all__ = ["ACTOR_METADATA", "render", "render_portraits"]
