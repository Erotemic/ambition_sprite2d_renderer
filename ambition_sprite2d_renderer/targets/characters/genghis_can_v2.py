"""Genghis Can, look C ("steppe"): the brother who says yes before he checks.

An SVG rig (``_genghis_pair_v2.py`` says where the drawing and the rows live).
He reads as Genghis Khan first: the deel crossed to the right with its trimmed
closure and knot buttons, a broad sash, horse-hoof cuffs, gutal boots with
turned-up toes, the long moustache and chin tuft of the Yuan court portrait,
the hair looped behind the ear. The pun is in his body: he stands tall, chest
out, chin up, and points the way; everything on him that can stand up stands
up (the fox-fur flaps are tied up). A teal deel, an orange sash, a quiver.

His first design, the procedural ``genghis_can``, stays renderable as the
lineage; the catalog row ``npc_genghis_can`` shows this one.
"""

from __future__ import annotations

from pathlib import Path

from . import _genghis_pair_v2 as pair

TARGET_NAME = "genghis_can_v2"
#: The face's centre in frame pixels (the portraits' guide).
HEAD = (62.2, 51.9)

ACTOR_METADATA = pair.actor_metadata(
    target=TARGET_NAME,
    character_id="npc_genghis_can",
    display_name="Genghis Can",
    sockets={"head": HEAD, "chest": (64.1, 87.1), "hand_l": (61.3, 104.2), "hand_r": (87.1, 71.1), "speech_bubble": (58.0, 10.0)},
    barks=(
        "Can I conquer this realm? Genghis Can.",
        "Every border is a suggestion.",
        "Advance. History hates hesitation.",
    ),
    authoring=(
        "Genghis Can is the unstoppable half of a paired Genghis Khan parody. "
        "He turns the conqueror's name into pure affirmative momentum: move first, "
        "claim the horizon, and correct mistakes while already advancing."
    ),
    gameplay=(
        "Use as an aggressive commander, rushdown rival, quest instigator, or paired "
        "boss. He should favor immediate expansion and confident improvisation, in "
        "contrast to his reflective brother Genghis Can't."
    ),
)


def render(out_dir: str | Path, **opts):
    del opts
    return pair.render(TARGET_NAME, ACTOR_METADATA, out_dir)


def render_portraits(out_dir: str | Path, **opts):
    del opts
    return pair.render_portraits(TARGET_NAME, HEAD, out_dir)


__all__ = ["ACTOR_METADATA", "render", "render_portraits"]
