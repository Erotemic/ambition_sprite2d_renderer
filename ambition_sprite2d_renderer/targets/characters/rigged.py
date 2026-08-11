"""Auto-register rig documents as sheet targets.

Every ``*.rig.json`` under ``targets/characters/rigged/`` (the GUI
editor's publish directory) becomes a multi-target entry named after the
document's ``name`` field, so GUI-authored characters render and install
through the standard pipeline::

    ./regen_sprites.sh --target <doc name>

Loose rig documents are a fallback publication surface. A dedicated Python
character module with the same target name always wins; the loose document can
remain editable without becoming runtime publication authority.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

RIGGED_DIR = Path(__file__).resolve().parent / "rigged"


def _make_entry(path: Path) -> dict:
    def render(out_dir: Path, **opts) -> List[Path]:
        del opts
        from ...authoring.rigdoc import RigDocument, render_sheet_for_doc

        # Reload per render so edits between CLI invocations are picked up.
        return render_sheet_for_doc(RigDocument.load(path), Path(out_dir))

    def render_canonical(out_dir: Path, **opts) -> Path:
        del opts
        from ...authoring.rigdoc import RigDocument
        from ...authoring.sheet_build import write_canonical

        doc = RigDocument.load(path)
        return write_canonical(doc.name, doc.rows(), doc.render_frame, Path(out_dir))

    return {"render": render, "render_canonical": render_canonical}


def _discover() -> Dict[str, dict]:
    import json

    targets: Dict[str, dict] = {}
    if not RIGGED_DIR.is_dir():
        return targets
    characters_dir = RIGGED_DIR.parent
    for path in sorted(RIGGED_DIR.glob("*.rig.json")):
        try:
            name = str(json.loads(path.read_text(encoding="utf8")).get("name", path.stem))
        except Exception:
            continue  # malformed doc: skip registration, GUI can still open it
        # A dedicated character module is a stronger publication contract than
        # the generic loose-rig adapter (it can freshness-check canonical SVGs,
        # add render overscan, portraits/effects, actor metadata, etc.). Keep the
        # loose document editable, but do not let it shadow that module merely
        # because rigged.py sorts later during discovery.
        if (characters_dir / f"{name}.py").exists():
            continue
        targets[name] = _make_entry(path)
    return targets


TARGETS = _discover()
