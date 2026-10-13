#!/usr/bin/env python3
"""Build the rig documents of the three house dogs.

    uv run python scripts/svg_art/house_dogs_art.py   # the drawings, once
    uv run python scripts/build_house_dog_rigs.py

Each house dog is drawn with the companion dog's parts about the companion
dog's joints (``scripts/svg_art/house_dogs_art.py``). So its rig document is
the companion dog's, with the dog's own name and drawing, and with NO clips:
the clips stay the companion dog's, and a house dog borrows them when its
document loads (``targets/characters/_house_dog.py``). A change to how the
companion dog moves is then a change to how each of them moves.

The legs of each dog have its own length (``_house_dog.LEG_SCALE``): the
joints of each leg are moved as the drawing moved them, and the bones of the
leg are made again from those joints.

This script never draws. It also refreshes the rig catalog in each SVG.
"""

from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ambition_sprite2d_renderer.devtools.svg_rig_tool import install_repo_metadata  # noqa: E402
from ambition_sprite2d_renderer.targets.characters._house_dog import HIP_Y, LEFT_SIDE, LEG_SCALE, leg_y, rig_path  # noqa: E402

PKG = ROOT / "ambition_sprite2d_renderer"
RIGGED = PKG / "targets" / "characters" / "rigged"
COMPANION_RIG = RIGGED / "companion_dog" / "companion_dog_side.rig.json"

#: name -> the label of the view of its right side in its SVG.
DOGS = {
    "dog_honey": "Honey - Side Right",
    "dog_roadie": "Roadie - Side Right",
    "dog_bezoar": "Bezoar - Side Right",
}
#: name -> the label of the view of its left side, for a dog that has one.
LEFT_VIEWS = {"dog_honey": "Honey - Left Side"}


LEGS = ("far_hind", "far_fore", "near_hind", "near_fore")


def fit_legs(doc: dict, scale: float) -> None:
    """Move the joints of each leg to where a leg ``scale`` as long has them,
    and make the bones of the leg again from the joints."""
    unit = float(doc["svg_source"]["scale"])
    parts = {part["name"]: part for part in doc["parts"]}
    bones = {bone["name"]: bone for bone in doc["bones"]}
    body = parts["body"]["pivot"]
    # The body stands as far over the ground as its legs are long.
    bones["body"]["offset"][1] = round(bones["body"]["offset"][1] * scale, 4)
    for leg in LEGS:
        upper, lower, paw = (parts[f"{leg}_{piece}"] for piece in ("upper", "lower", "paw"))
        for part in (upper, lower, paw):
            part["pivot"] = [part["pivot"][0], round(leg_y(part["pivot"][1], scale), 3)]

        def reach(a: list, b: list) -> tuple:
            dx, dy = b[0] - a[0], b[1] - a[1]
            return math.hypot(dx, dy) * unit, math.degrees(math.atan2(dy, dx))

        upper_len, upper_angle = reach(upper["pivot"], lower["pivot"])
        lower_len, lower_angle = reach(lower["pivot"], paw["pivot"])
        upper["rest_angle"], lower["rest_angle"] = round(upper_angle, 4), round(lower_angle, 4)
        bone = bones[f"{leg}_upper"]
        bone["offset"] = [round((upper["pivot"][0] - body[0]) * unit, 4), round((upper["pivot"][1] - body[1]) * unit, 4)]
        bone["length"], bone["rest_angle"] = round(upper_len, 4), round(upper_angle, 4)
        bone = bones[f"{leg}_lower"]
        bone["offset"] = [round(upper_len, 4), 0]
        bone["length"], bone["rest_angle"] = round(lower_len, 4), round(lower_angle - upper_angle, 4)
        bone = bones[f"{leg}_paw"]
        bone["offset"], bone["rest_angle"] = [round(lower_len, 4), 0], round(-lower_angle, 4)
    assert body[1] == HIP_Y, "the body joint is on the line the legs are measured from"


def give_a_mouth_at_rest(doc: dict) -> None:
    """A house dog has its mouth open, with its tongue out. That mouth is a
    part of its own behind the head (the muzzle is drawn over the root of
    the tongue), and a bark shows the bark mouth in its place, behind the
    head too. The loader gives each clip the channel that hides it."""
    bark = next(part for part in doc["parts"] if part["name"] == "bark_mouth")
    bark["z"] = 39
    rest = copy.deepcopy(bark)
    rest.update(name="rest_mouth", include=["rest-mouth"], opacity_channel="rest_mouth", opacity_default=1)
    doc["parts"].insert(doc["parts"].index(bark), rest)


def main() -> None:
    companion = json.loads(COMPANION_RIG.read_text())
    for name, view in DOGS.items():
        sides = [(False, f"{name}_side", view)]
        if name in LEFT_SIDE:
            sides.append((True, LEFT_SIDE[name], LEFT_VIEWS[name]))
        for left_side, svg_name, label in sides:
            doc = copy.deepcopy(companion)
            doc["name"] = name
            doc["svg_source"]["path"] = f"../../../../data/characters/{name}/{svg_name}.svg"
            doc["svg_source"]["view"] = label
            doc["clips"] = {}
            fit_legs(doc, LEG_SCALE[name])
            give_a_mouth_at_rest(doc)
            if name in LEFT_SIDE:
                # A row of the left side is mirrored about the middle of the
                # frame, so the dog stands at the middle of it.
                doc["frame"]["width"] = 176
                doc["frame"]["center_x"] = 88
            out = rig_path(name, left_side)
            out.parent.mkdir(parents=True, exist_ok=True)
            tmp = out.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf8")
            tmp.replace(out)
            print(f"wrote {out.relative_to(ROOT)}")
    for changed in install_repo_metadata(ROOT):
        print(f"catalog {Path(changed).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
