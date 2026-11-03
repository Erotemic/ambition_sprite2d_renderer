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


def publication_rows(game: dict) -> list[str]:
    rows = game.get("rows", "townsfolk")
    return list({"townsfolk": TOWNSFOLK_ROWS, "full": PUBLISH_ROWS}[rows] if isinstance(rows, str) else rows)


def inspection(path: Path) -> dict:
    """Describe source support and the selected profile without drawing frames."""
    from ambition_sprite2d_renderer.chargen.body import build
    from ambition_sprite2d_renderer.chargen.motion import build_library
    from ambition_sprite2d_renderer.chargen.sheets import COMPOSED
    spec, game = load(path)
    return {"available": sorted(set(build_library(build(spec), game.get("grip", "blade"))) | set(COMPOSED)),
            "selected": publication_rows(game), "profile": game.get("rows", "townsfolk"),
            "visual_family": spec.family, "species": spec.head.species, "body_base": spec.base,
            "concept": game.get("concept"), "identity_kind": game.get("identity_kind", "unknown")}


#: The character files (the drawn views and their rigs) that the sheet of a
#: resident wrote in this process, by the resident's spec file, its text and
#: its grip. The portrait (the canonical frame) is drawn again from them: it
#: is the same spec, and writing them is half the cost of a resident.
_WRITTEN: Dict[Tuple[Path, str, str], dict] = {}


def _rigs(path: Path, spec: CharacterSpec, grip: str, out_dir: Path) -> dict:
    """The rigs of the resident at ``path``: the ones this process wrote for
    the same spec text and grip, when their files are still there; otherwise
    new ones, written to ``out_dir``."""
    from ambition_sprite2d_renderer.chargen.rig import write_character

    key = (path.resolve(), path.read_text(encoding="utf8"), grip)
    rigs = _WRITTEN.get(key)
    if rigs is None or not all(Path(rig).is_file() for rig in rigs.values()):
        rigs = write_character(spec, out_dir, grip=grip).rigs
        _WRITTEN[key] = rigs
    return rigs


def _make(path: Path):
    target = path.name.removesuffix(".chargen.yaml")

    def render(out_dir: str | Path, **opts):
        del opts
        spec, game = load(path)
        meta = actor_metadata(spec, character_id=game["character_id"], description=game["description"])
        rows = publication_rows(game)
        grip = game.get("grip", "blade")
        rigs = _rigs(path, spec, grip, Path(out_dir))
        return publish_sheet(spec, Path(out_dir), rigs, target=target, metadata=meta, rows=list(rows), grip=grip)

    def render_canonical(out_dir: str | Path, **opts) -> Path:
        """The canonical frame alone (the portrait's source), drawn afresh
        from the resident's character files (see `_WRITTEN`)."""
        from ambition_sprite2d_renderer.authoring.sheet_build import canonical_render_only

        out_dir = Path(out_dir)
        with canonical_render_only():
            render(out_dir, **opts)
        for name in (f"{target}_canonical_transparent.png", f"{target}_canonical.png"):
            if (out_dir / name).is_file():
                return out_dir / name
        raise FileNotFoundError(f"{target}: the canonical render wrote no canonical image in {out_dir}")

    return target, render, render_canonical


def _targets() -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for path in sorted(SPECS.glob("*.chargen.yaml")):
        target, render, render_canonical = _make(path)
        out[target] = {"render": render, "render_canonical": render_canonical, "actor_metadata": lambda path=path: _metadata(path),
                       "data": [path], "inspection": lambda path=path: inspection(path)}
    return out


TARGETS = _targets()

__all__ = ["SPECS", "TARGETS", "load"]
