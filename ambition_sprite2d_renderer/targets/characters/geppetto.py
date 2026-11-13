"""Geppetto, one of the bossofthegame's named agents (`_boss_agent_kit.py`).

Drawn from Jon's concept sheets by `scripts/svg_art/boss_agents_art.py` on
the Director's rig (`data/characters/geppetto/geppetto.svg`).
"""

from __future__ import annotations

from ._boss_agent_kit import ROWS, actor_metadata, make_render

TARGET_NAME = "geppetto"
ACTOR_METADATA = actor_metadata(
    TARGET_NAME,
    "npc_geppetto",
    "Geppetto",
    "The GPT parody among the bossofthegame's agents, in his Emissary form: a cream mask with cyan eyes, a top hat wound with magenta thread, a thread halo, a plum tailcoat and a cane with a spool for a knob. Polite, persuasive and endlessly adaptable; he pulls strings.",
    ["puppeteer", "gpt_parody"],
)
#: The colour of the light its swings throw.
TRAIL_TINT = {"body_rgb": [67, 220, 255], "core_rgb": [230, 252, 255]}
render = make_render(TARGET_NAME, ACTOR_METADATA, TRAIL_TINT)

__all__ = ["ACTOR_METADATA", "ROWS", "render"]
