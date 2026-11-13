"""Wren, one of the bossofthegame's named agents (the Generalist: hood, short cape, wrench).

Drawn by the character generator in every view (``_band_agent_sheet.py``):
the spec ``data/characters/wren/wren.chargen.yaml``, the agent's own parts
in ``_band_agents_gear.py`` and the band's instruments in
``_band_instruments.py``.
"""

from __future__ import annotations

from ._band_agent_sheet import ROWS, actor_metadata, make_render
from ._band_agents_gear import wren_parts

TARGET_NAME = "wren"
ACTOR_METADATA = actor_metadata(
    TARGET_NAME,
    "npc_wren",
    "Wren",
    "Wren, the Generalist: the Qwen parody among the bossofthegame's named agents, after Jon's concept sheet (the Field Agent's hood, the Engineer's wrench). A dark visor with two golden glowing eyes, a purple hood and a short purple cape with a gold edge, an open cream robe over a dark tunic, a purple scarf and belt, lilac boots, and a big wrench. Versatile; in the Boss's band she plays rhythm guitar.",
    ['generalist', 'qwen_parody', 'band_guitar'],
)
render = make_render(TARGET_NAME, wren_parts, ACTOR_METADATA, grip="tool", own_props={'prop.wrench': 1.0})

__all__ = ["ACTOR_METADATA", "ROWS", "render"]
