"""Assemble the Performer's character rig SVG from the authored art source."""
from __future__ import annotations

from pathlib import Path

from .annotated_side_rig import SideRigSpec, build

REPO = Path(__file__).resolve().parents[2]

SPEC = SideRigSpec(
    name="performer",
    view_id="view-performer-side-east",
    source_label="Character - Performer",
    facing="east",
    # Crown of the skull, NOT of the updo. The piled bun is a hairstyle she can
    # take down; measuring from it would publish her a head shorter than the
    # roster she stands next to.
    head_top_y=83.88,
    rig_root=(100.8, 283.5),
    # `layer5` is an empty authoring layer left over from the drawing, with
    # nothing in it to rig.
    drop_layers=("reference-image", "layer5"),
)


def main() -> None:
    build(SPEC, repo=REPO)


if __name__ == "__main__":
    main()
