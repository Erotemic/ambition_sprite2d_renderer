"""Clause, one of the bossofthegame's named agents (the Analyst: crown of fins, poncho).

Drawn by the character generator in every view (``_band_agent_sheet.py``):
the spec ``data/characters/clause/clause.chargen.yaml``, the agent's own parts
in ``_band_agents_gear.py`` and the band's instruments in
``_band_instruments.py``.
"""

from __future__ import annotations

from ._band_agent_sheet import ROWS, actor_metadata, make_render
from ._band_agents_gear import clause_parts

TARGET_NAME = "clause"
ACTOR_METADATA = actor_metadata(
    TARGET_NAME,
    "npc_clause",
    "Clause",
    "Clause, the Analyst: the Claude parody among the bossofthegame's named agents, after Jon's concept sheet. A dark visor with two orange glowing eyes and earpieces, a crown of orange petal fins round the back of his head, a cream poncho cut on a slant with orange edges and his starburst on the breast, over a dark chassis, and cream boots. Thoughtful and methodical; in the Boss's band he keeps time on the drums.",
    ['analyst', 'claude_parody', 'band_drums'],
)
render = make_render(TARGET_NAME, clause_parts, ACTOR_METADATA, grip="blade", own_props={})

__all__ = ["ACTOR_METADATA", "ROWS", "render"]
