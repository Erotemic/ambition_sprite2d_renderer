"""Geppetto, one of the bossofthegame's named agents (the Orchestrator: hat, coat, mantle, baton).

Drawn by the character generator in every view (``_band_agent_sheet.py``):
the spec ``data/characters/geppetto/geppetto.chargen.yaml``, the agent's own parts
in ``_band_agents_gear.py`` and the band's instruments in
``_band_instruments.py``.
"""

from __future__ import annotations

from ._band_agent_sheet import ROWS, actor_metadata, make_render
from ._band_agents_gear import geppetto_parts

TARGET_NAME = "geppetto"
ACTOR_METADATA = actor_metadata(
    TARGET_NAME,
    "npc_geppetto",
    "Geppetto",
    "Geppetto, the Orchestrator: the GPT parody among the bossofthegame's named agents, after Jon's concept sheet. A dark visor for a face with two warm glowing eyes and earpieces, a wide-brimmed plum hat with a magenta band and a gold gear, a long open cream coat with magenta gears on its skirts over a plum shirt, a magenta scarf, a plum mantle down his back, and a conductor's baton: he orchestrates. In the Boss's band he plays the bass.",
    ['orchestrator', 'gpt_parody', 'band_bass'],
)
render = make_render(TARGET_NAME, geppetto_parts, ACTOR_METADATA, grip="blade", own_props={"prop.baton": 1.0})

__all__ = ["ACTOR_METADATA", "ROWS", "render"]
