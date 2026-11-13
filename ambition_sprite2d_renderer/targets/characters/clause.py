"""Clause, one of the bossofthegame's named agents (`_boss_agent_kit.py`).

Drawn from Jon's concept sheets by `scripts/svg_art/boss_agents_art.py` on
the Director's rig (`data/characters/clause/clause.svg`).
"""

from __future__ import annotations

from ._boss_agent_kit import ROWS, actor_metadata, make_render

TARGET_NAME = "clause"
ACTOR_METADATA = actor_metadata(
    TARGET_NAME,
    "npc_clause",
    "Clause",
    "The Claude parody among the bossofthegame's agents, the Analyst: a dark mask with upright orange eyes, a crown of orange petal fins, a cream poncho with the starburst on it over a dark chassis. Thoughtful and methodical; he reads the Boss's instructions to the letter and wonders about their intent.",
    ["analyst", "claude_parody"],
)
#: The colour of the light its swings throw.
TRAIL_TINT = {"body_rgb": [232, 115, 58], "core_rgb": [255, 232, 200]}
render = make_render(TARGET_NAME, ACTOR_METADATA, TRAIL_TINT)

__all__ = ["ACTOR_METADATA", "ROWS", "render"]
