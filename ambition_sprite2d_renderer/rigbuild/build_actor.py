"""Assemble the Actor's character rig SVG from the authored art source."""
from __future__ import annotations

from pathlib import Path

from .annotated_side_rig import SideRigSpec, build

REPO = Path(__file__).resolve().parents[2]

SPEC = SideRigSpec(
    name="actor",
    view_id="view-actor-side-east",
    source_label="Character - Actor",
    facing="east",
    # Crown of the skull, NOT of the updo. The piled bun is a hairstyle she can
    # take down; measuring from it would publish her a head shorter than the
    # roster she stands next to.
    head_top_y=83.88,
    rig_root=(100.8, 283.5),
    drop_layers=("reference-image",),
)


def main() -> None:
    build(SPEC, repo=REPO)


if __name__ == "__main__":
    main()
