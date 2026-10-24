"""Townsfolk: ordinary residents made by the character generator (``chargen``).

Each resident is one spec file, ``data/townsfolk/<target>.chargen.yaml``. The
file is a chargen spec (``ambition-chargen-v1``; a field it leaves out is
drawn from its ``base`` and ``seed``) with one more section, ``game``:

* ``character_id``: the game's catalog id (``npc_<...>``);
* ``description``: the ``authoring_description`` of the actor sidecar;
* ``rows`` (optional): ``townsfolk`` (the default:
  :data:`~ambition_sprite2d_renderer.chargen.sheets.TOWNSFOLK_ROWS`),
  ``full`` (:data:`~ambition_sprite2d_renderer.chargen.sheets.PUBLISH_ROWS`:
  moving, fighting, holding items) or a list of clip names;
* ``grip`` (optional): the grip class its item rows are posed for
  (``chargen.motion.GRIPS``; default ``blade``).

The target id is the file name. A new resident is a new file: this module
registers each file it finds.

The first residents (2026-10-24) live in the Pirate Port (``port_*``) and the
Ninja Village (``village_*``) of the gate network.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import yaml

from ambition_sprite2d_renderer.chargen.sheets import PUBLISH_ROWS, TOWNSFOLK_ROWS, actor_metadata, publish_sheet
from ambition_sprite2d_renderer.chargen.spec import CharacterSpec, complete

SPECS = Path(__file__).resolve().parents[2] / "data" / "townsfolk"


def load(path: Path) -> Tuple[CharacterSpec, dict]:
    """The spec of a resident file, and its ``game`` section."""
    data = yaml.safe_load(path.read_text(encoding="utf8"))
    game = data.pop("game")
    return complete(data), game


def _metadata(path: Path) -> dict:
    spec, game = load(path)
    return actor_metadata(spec, character_id=game["character_id"], description=game["description"])


def _make(path: Path):
    target = path.name.removesuffix(".chargen.yaml")

    def render(out_dir: str | Path, **opts):
        del opts
        spec, game = load(path)
        meta = actor_metadata(spec, character_id=game["character_id"], description=game["description"])
        rows = game.get("rows", "townsfolk")
        rows = {"townsfolk": TOWNSFOLK_ROWS, "full": PUBLISH_ROWS}.get(rows, rows) if isinstance(rows, str) else rows
        return publish_sheet(spec, Path(out_dir), target=target, metadata=meta, rows=list(rows), grip=game.get("grip", "blade"))

    return target, render


def _targets() -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for path in sorted(SPECS.glob("*.chargen.yaml")):
        target, render = _make(path)
        out[target] = {"render": render, "actor_metadata": _metadata(path)}
    return out


TARGETS = _targets()

__all__ = ["SPECS", "TARGETS", "load"]
