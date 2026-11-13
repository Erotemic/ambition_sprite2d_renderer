"""Wren, one of the bossofthegame's named agents (`_boss_agent_kit.py`).

Drawn from Jon's concept sheets by `scripts/svg_art/boss_agents_art.py` on
the Director's rig (`data/characters/wren/wren.svg`).
"""

from __future__ import annotations

from ._boss_agent_kit import ROWS, actor_metadata, make_render

TARGET_NAME = "wren"
ACTOR_METADATA = actor_metadata(
    TARGET_NAME,
    "npc_wren",
    "Wren",
    "The Qwen parody among the bossofthegame's agents, the Multilingual Tactician: a dark face with upright gold eyes, a conical hat with a purple feather and gold tassels, a purple scarf, a cream robe and a cape of purple feathers. Fast, worldly and versatile; she fights with a folding fan.",
    ["tactician", "qwen_parody"],
)
#: The colour of the light its swings throw.
TRAIL_TINT = {"body_rgb": [140, 90, 220], "core_rgb": [255, 236, 170]}
render = make_render(TARGET_NAME, ACTOR_METADATA, TRAIL_TINT)

__all__ = ["ACTOR_METADATA", "ROWS", "render"]
