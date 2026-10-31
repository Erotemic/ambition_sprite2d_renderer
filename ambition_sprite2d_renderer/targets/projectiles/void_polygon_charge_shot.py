"""The Void Projectile Polygon's charge shot: the Projectile Polygon's shot
(`polygon_charge_shot.py`), made of the void.

Jon, 2026-10-30: "Make void versions of the polygon fighter characters and
have them be enemies to fight in the void." The void's things are a body with
no light in it and a white edge (the Void Lizard's orb, the Void Star), so the
ball is black with a white halo at its rim and a white pinprick at its core;
its rings, arcs and sparks are white and grey. Same five tiers, same rows,
frames and timing as the source: only the paint changes, and the source stays
the one drawing to edit (this module runs it with the void's palette).

No drop shadows: the source's glow is the ball's own light, and here it is
the dark of the void about it.
"""
from __future__ import annotations

import types
from pathlib import Path

from . import polygon_charge_shot as _source

TARGET_NAME = "void_polygon_charge_shot"

#: The source's palette names, in the void's colours.
PALETTE = {
    "CORE": (244, 242, 250),
    "HOT": (44, 42, 52),
    "BODY": (10, 8, 16),
    "RIM": (240, 238, 250),
    "SPARK": (214, 212, 222),
}


def _void_module() -> types.ModuleType:
    """The source module run again with the void's palette and name."""
    module = types.ModuleType(f"{__name__}._painted")
    module.__dict__["__file__"] = _source.__file__
    module.__dict__["__package__"] = _source.__package__
    code = compile(Path(_source.__file__).read_text(encoding="utf8"), _source.__file__, "exec")
    exec(code, module.__dict__)
    module.__dict__.update(PALETTE)
    module.TARGET_NAME = TARGET_NAME
    return module


_PAINTED = _void_module()
ROWS = _PAINTED.ROWS
render_frame = _PAINTED.render_frame

ACTOR_METADATA = {
    **_source.ACTOR_METADATA,
    "actor": {"character_id": TARGET_NAME, "display_name": "Void Polygon Charge Shot"},
    "authoring_description": {
        "concept": "The Projectile Polygon's charge shot, fired by its void version: a ball of the void.",
        "visual_language": [
            "black body, a white halo at the rim, a white pinprick core: the void's own palette",
            "the source's tiers, rows and timing unchanged",
        ],
    },
    "tags": ["projectile", "charge_shot", "void", "void_projectile_polygon"],
}
_PAINTED.ACTOR_METADATA = ACTOR_METADATA


def render(out_dir: str | Path, **opts):
    return _PAINTED.render(out_dir, **opts)


def render_canonical(out_dir: str | Path, **opts):
    return _PAINTED.render_canonical(out_dir, **opts)


__all__ = ["ACTOR_METADATA", "ROWS", "TARGET_NAME", "render", "render_canonical", "render_frame"]
