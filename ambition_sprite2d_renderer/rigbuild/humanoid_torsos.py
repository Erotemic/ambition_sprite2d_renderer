"""Author side and back torsos for the hand-drawn humanoids (Author, Officer).

Same mechanism as the polygons: three torsos, one visible at a time, sockets
travelling with the trunk. The art is the part that cannot be shared — these are
drawn paths with a real neckline, not faceted slabs.

⛔ THE NECK IS A SEPARATE PART AND DOES NOT MOVE WITH THE SWAP. `neck` is bound
to the torso BONE but drawn as its own part, behind the shirt. So every torso in
the swap set has to keep its opening in the SAME place — an alternate with its
own idea of where the collar goes leaves a skin-coloured wedge floating over the
chest, or swallows the throat entirely. The four neckline vertices below are
shared verbatim between all three shapes, and the Officer's ribbed collar is
copied from the authored path rather than redrawn.

Coordinates are in each character's ART space (millimetres, inside the view's
scale group). The socket file is written in ROOT space, which is what the poses
translate in.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from lxml import etree

SVG = "http://www.w3.org/2000/svg"
INK = "http://www.inkscape.org/namespaces/inkscape"

#: Shoulder travel as a FRACTION OF THE SHOULDER SPAN, by role, along the
#: character's own forward axis. Fractions rather than units so one table serves
#: a 189-unit polygon and a 23-unit hand-drawn shirt.
SOCKET_TRAVEL = {
    "torso_side": {"rear": (0.381, 0.016), "lead": (-0.333, -0.016)},
    "torso_back": {"rear": (1.090, 0.011), "lead": (-0.799, 0.011)},
}


# ⛔ THE BASE ART IS BEZIER AND THESE HAVE TO BE TOO. Straight-sided polygons
# read as planks next to a drawn shirt however good the proportions are, and
# a torso that leaves its shoulders at a hard corner and flares to a flat hem
# reads as a box. Every outline below is: a rounded shoulder cap, a side that
# TAPERS to the waist, and a hem that curves.
#
# Shared verbatim by all three torsos of a character: the two collar peaks and
# the notch between them, MEASURED off the base's own top profile. The `neck`
# part is drawn behind the shirt and does not move with the swap, so the hole it
# comes through must not move either.
AUTHOR_NECK = (
    "M 100.2,118.7 "
    "C 99.6,120.4 99.1,121.5 98.4,122.3 "
    "C 96.8,124.0 95.4,124.7 94,124.7 "
    "C 92.2,124.7 90.7,124.6 89.6,124.4 "
    "C 89.2,123.4 88.9,122.3 88.6,121.3 "
)
OFFICER_NECK = (
    "M 110.9,79.5 "
    "C 110.1,81.4 109.3,82.9 108.2,83.8 "
    "C 105.6,86.2 103,87.7 100.4,88.3 "
    "C 98,88.9 95.8,89 93.9,88.9 "
    "C 93.4,86.4 92.9,84 92.5,81.7 "
)

CHARACTERS = {
    "author": {
        "view": "view-author-side-west",
        "torso_part": "torso",
        "scale": 4.4585,
        "shapes": {
            # Edge-on: a slim trunk, still with a shoulder cap and a waist.
            "side": AUTHOR_NECK + (
                "C 87.4,123.4 86.3,125.7 85.9,128.4 "
                "C 85.4,133.2 85.6,140.2 86.3,147.6 "
                "C 86.7,152.6 87.2,157.2 87.6,161.0 "
                "C 90.9,162.4 95.3,162.4 98.6,161.0 "
                "C 99.2,156.8 100,151.0 100.6,145.2 "
                "C 101.3,138.2 101.9,132.2 101.6,128.6 "
                "C 101.3,125.0 100.8,121.6 100.2,118.7 Z"
            ),
            # Turned through: the driving shoulder swung to the front (-x, he
            # faces west), the lead one behind it, and the hem still centred on
            # the hips rather than travelling with the turn.
            "back": AUTHOR_NECK + (
                "C 86.6,122.6 83.6,124.8 81.4,127.6 "
                "C 80.0,129.6 79.4,132.2 79.8,135.2 "
                "C 80.7,141.2 83.1,151.8 85.2,161.0 "
                "C 89.2,162.4 95.2,162.4 99.1,161.0 "
                "C 100.8,151.8 102.9,141.6 103.8,134.2 "
                "C 104.3,130.6 103.7,127.9 102.4,125.6 "
                "C 101.7,123.1 100.9,120.7 100.2,118.7 Z"
            ),
        },
        "shade": {
            "side": (
                "M 95.4,124.5 C 98.2,124.2 100.2,122.4 100.9,120.6 "
                "C 101.6,128.0 101.0,142.0 99.2,161.6 "
                "C 97.4,162.2 95.6,162.2 94.4,161.8 "
                "C 95.6,146.0 95.9,133.0 95.4,124.5 Z"
            ),
            "back": (
                "M 95.6,124.6 C 98.6,124.2 101.0,122.6 101.9,120.8 "
                "C 103.2,128.4 101.8,144.0 99.3,161.6 "
                "C 97.4,162.2 95.4,162.2 94.1,161.8 "
                "C 96.1,145.0 96.5,132.6 95.6,124.6 Z"
            ),
        },
    },
    "officer": {
        "view": "layer2",
        "torso_part": "torso",
        "scale": 3.4054,
        "shapes": {
            "side": OFFICER_NECK + (
                "C 91.0,85.1 89.7,89.7 89.3,94.5 "
                "C 88.9,104.2 89.7,116.2 91.1,126.2 "
                "C 91.6,131.2 92.1,136.0 92.5,138.9 "
                "C 96.7,140.2 102.5,140.2 106.7,138.9 "
                "C 107.6,133.8 108.6,126.8 109.4,119.8 "
                "C 110.4,109.6 111.2,99.8 111.4,94.0 "
                "C 111.5,88.6 111.2,83.7 110.9,79.5 Z"
            ),
            "back": OFFICER_NECK + (
                "C 89.9,84.4 85.7,88.2 82.7,92.2 "
                "C 80.3,95.4 79.2,99.2 79.4,103.0 "
                "C 79.5,112.1 83.1,124.1 87.6,133.1 "
                "C 88.9,135.6 90.3,137.7 91.6,138.9 "
                "C 96.6,140.2 102.9,140.2 107.4,138.9 "
                "C 109.7,133.8 111.9,126.0 113.2,118.0 "
                "C 114.2,111.0 114.6,103.4 113.8,97.0 "
                "C 113.1,90.8 112.1,84.8 110.9,79.5 Z"
            ),
        },
        "shade": {
            "side": (
                "M 101.6,87.9 C 105.2,86.9 108.2,84.6 109.6,82.4 "
                "C 110.6,92.0 109.6,116.0 106.8,139.0 "
                "C 104.6,139.6 102.4,139.6 100.9,139.2 "
                "C 102.6,116.0 102.8,99.0 101.6,87.9 Z"
            ),
            "back": (
                "M 101.4,88.1 C 105.6,87.0 109.0,84.6 110.4,82.2 "
                "C 112.6,93.0 111.6,118.0 107.6,139.0 "
                "C 105.2,139.6 102.8,139.6 101.2,139.2 "
                "C 103.4,116.0 103.2,99.6 101.4,88.1 Z"
            ),
        },
        "copy_elements": ["path584"],
    },
}


def _style(elem) -> tuple[str, str, str]:
    style = elem.get("style") or ""
    parts = dict(
        piece.split(":", 1) for piece in style.split(";") if ":" in piece
    )
    fill = parts.get("fill") or elem.get("fill") or "#333333"
    stroke = parts.get("stroke") or elem.get("stroke") or "#000000"
    width = parts.get("stroke-width") or elem.get("stroke-width") or "0.26458px"
    return fill, stroke, width


def build(name: str) -> None:
    spec = CHARACTERS[name]
    # ⛔ ANCHORED TO THIS FILE, not to the working directory. As a scratch
    # script this resolved against wherever it was launched from; as a package
    # module it has to find the same rig from anywhere.
    repo = Path(__file__).resolve().parents[2]
    svg = repo / "ambition_sprite2d_renderer" / "data" / "characters" / name / f"{name}.svg"
    tree = etree.parse(str(svg))
    root = tree.getroot()
    catalog = root.xpath("//*[@id='ambition-rig-metadata']")[0]
    view = next(e for e in catalog if e.get("data-rig-view-def"))
    base_part = next(e for e in view if e.get("data-rig-part-def") == spec["torso_part"])
    art_id = (base_part.get("data-rig-elements") or "").split()[0]
    art = root.xpath(f"//*[@id='{art_id}']")[0]
    body = next(
        (e for e in art.iter() if e.get("d") and e is not art),
        art,
    )
    fill, stroke, width = _style(body)
    art_parent = art.getparent()

    # ⛔ ONLY WHAT THE SOURCE DOES NOT ALREADY AUTHOR. A generated shell used to
    # be written for BOTH, over the top of a rig this script does not own — so
    # a hand-drawn back torso in the source file was silently replaced by a
    # computed one on the next run. A part the rig already carries is somebody
    # else's art and is left alone.
    authored = {
        e.get("data-rig-part-def")
        for e in view
        if e.get("data-rig-part-def", "").startswith("torso_")
        and e.get("data-rig-part-def") != spec["torso_part"]
        and not (e.get("id") or "").endswith(("-side", "-back"))
    }
    for kind in ("side", "back"):
        if f"torso_{kind}" in authored:
            print(f"{name}: torso_{kind} is authored in the source; leaving it alone")
            continue
        group_id = f"{art_id}-{kind}"
        for stale in root.xpath(f"//*[@id='{group_id}']"):
            stale.getparent().remove(stale)
        for stale in [e for e in view if e.get("data-rig-part-def") == f"torso_{kind}"]:
            view.remove(stale)

        group = etree.Element(f"{{{SVG}}}g")
        group.set("id", group_id)
        group.set(f"{{{INK}}}label", f"Torso ({kind})")
        shell = etree.SubElement(group, f"{{{SVG}}}path")
        shell.set("id", f"{group_id}-shell")
        shell.set("d", spec["shapes"][kind])
        shell.set("style", f"fill:{fill};stroke:{stroke};stroke-width:{width};stroke-linejoin:round")
        shade = etree.SubElement(group, f"{{{SVG}}}path")
        shade.set("id", f"{group_id}-shade")
        shade.set("d", spec["shade"][kind])
        shade.set("style", "fill:#000000;fill-opacity:0.11;stroke:none")
        for index, source_id in enumerate(spec.get("copy_elements", [])):
            source = root.xpath(f"//*[@id='{source_id}']")[0]
            clone = etree.fromstring(etree.tostring(source))
            clone.set("id", f"{group_id}-carry-{index}")
            group.append(clone)
        art_parent.insert(list(art_parent).index(art) + 1, group)

        entry = etree.SubElement(view, f"{{{SVG}}}g")
        entry.set("id", f"{view.get('data-rig-view-def')}-part-torso_{kind}")
        entry.set("data-rig-part-def", f"torso_{kind}")
        entry.set("data-rig-bone", base_part.get("data-rig-bone"))
        entry.set("data-rig-z", str(float(base_part.get("data-rig-z", "0")) + 0.1))
        entry.set("data-rig-pivot", base_part.get("data-rig-pivot"))
        entry.set("data-rig-bind-angle", base_part.get("data-rig-bind-angle", "0"))
        entry.set("data-rig-elements", group_id)
        entry.set("data-rig-opacity", f"torso_{kind}_vis")

    base_part.set("data-rig-opacity", "torso_front_vis")
    base_part.set("data-rig-opacity-default", "1")
    tree.write(str(svg), encoding="UTF-8", xml_declaration=True)

    # Sockets, resolved by role against this rig's own markers, in ROOT space.
    joints = {
        e.get("data-rig-joint"): (float(e.get("cx")), float(e.get("cy")))
        for e in root.iter()
        if e.get("data-rig-joint") in {"near_shoulder", "far_shoulder"}
    }
    faces_west = (view.get("data-rig-facing") or "").lower() == "west"
    forward = -1.0 if faces_west else 1.0
    near_is_lead = (joints["near_shoulder"][0] - joints["far_shoulder"][0]) * forward > 0
    role_bone = {
        "lead": "near_arm_u" if near_is_lead else "far_arm_u",
        "rear": "far_arm_u" if near_is_lead else "near_arm_u",
    }
    base = {"near_arm_u": joints["near_shoulder"], "far_arm_u": joints["far_shoulder"]}
    span = abs(joints["near_shoulder"][0] - joints["far_shoulder"][0])
    sockets = {"torso": {k: list(v) for k, v in base.items()}}
    for torso, travel in SOCKET_TRAVEL.items():
        sockets[torso] = {
            role_bone[role]: [
                round(base[role_bone[role]][0] + dx * span * forward, 3),
                round(base[role_bone[role]][1] + dy * span, 3),
            ]
            for role, (dx, dy) in travel.items()
        }
    (svg.parent / "torso_sockets.json").write_text(json.dumps(sockets, indent=2) + "\n")
    print(f"{name}: torso_side + torso_back authored, span={span:.1f}u, sockets written")


if __name__ == "__main__":
    for name in sys.argv[1:]:
        build(name)
