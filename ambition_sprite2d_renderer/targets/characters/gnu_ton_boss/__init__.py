"""GNU Ton boss character — multi-file tack-on target.

A multi-file character package. Same shape as
[`mockingbird_boss`](../mockingbird_boss/__init__.py): the package
ships its own :mod:`.sprite_generator` and the ``__init__.py``
exposes the discovery API on top of it.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from ....authoring.portrait import (
    PortraitClip,
    render_canonical_portrait,
    write_portrait_sheet,
)
from . import sprite_generator

TARGET_NAME = sprite_generator.TARGET_NAME
SHEET_FILES = list(sprite_generator.OUTPUT_FILES)
ACTOR_METADATA = sprite_generator.ACTOR_METADATA
PORTRAIT_INSTALL_SUBDIR = TARGET_NAME
PORTRAIT_FILES = (
    f"{TARGET_NAME}_portraits.png",
    f"{TARGET_NAME}_portraits.ron",
    f"{sprite_generator.GIANT_TARGET_NAME}_portraits.png",
    f"{sprite_generator.GIANT_TARGET_NAME}_portraits.ron",
    "giant_gnu_hands_portraits.png",
    "giant_gnu_hands_portraits.ron",
)


def render(out_dir: str | Path, **opts) -> List[Path]:
    return list(
        sprite_generator.render_outputs(
            outdir=Path(out_dir),
            quick=bool(opts.get("quick", False)),
        )
    )


def render_portraits(out_dir: str | Path, **opts) -> List[Path]:
    """Publish defaults for the fused boss and its Hall-visible split actors."""

    del opts
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    products = (
        (TARGET_NAME, "full", sprite_generator.ACTOR_METADATA),
        (
            sprite_generator.GIANT_TARGET_NAME,
            "giant_body",
            sprite_generator.GIANT_ACTOR_METADATA,
        ),
        ("giant_gnu_hands", "hands", sprite_generator.GIANT_ACTOR_METADATA),
    )
    outputs: List[Path] = []
    for target, layer, metadata in products:
        source = sprite_generator.draw_frame("rest", 1, 10, layer=layer)
        portrait = render_canonical_portrait(source, actor_metadata=metadata)
        outputs.extend(
            write_portrait_sheet(
                target, {"default": PortraitClip.still(portrait)}, out_dir
            )
        )
    return outputs


def install(render_dir: str | Path, dest_root: str | Path) -> List[Path]:
    render_dir = Path(render_dir)
    install_dir = Path(dest_root) / TARGET_NAME
    return list(
        sprite_generator.install_outputs(
            render_dir=render_dir,
            install_dir=install_dir,
        )
    )
