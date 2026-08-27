"""Assemble the Medic's character rig SVG from the authored art source."""
from __future__ import annotations

from pathlib import Path

from .annotated_side_rig import SideRigSpec, build

REPO = Path(__file__).resolve().parents[2]

SPEC = SideRigSpec(
    name="medic",
    view_id="view-medic-side-east",
    source_label="Character - Medic",
    facing="east",
    # Crown of the skull. Her ponytail rides above and behind it and does not
    # set her standing height, the same way the Officer's campaign hat does not.
    head_top_y=33.5,
    rig_root=(104.4, 269.0),
    drop_layers=("reference-image",),
)


def main() -> None:
    build(SPEC, repo=REPO)


if __name__ == "__main__":
    main()
