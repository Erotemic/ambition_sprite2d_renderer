"""The gameplay body of a rigged character, measured from the parts that ARE it.

⛔ **the default body box is the alpha bbox of the sheet's FIRST FRAME**, and a
rig publishes its rows alphabetically, so for every polygon fighter that frame
is `aim` — sword up and arm extended. Their collision box was the size of their
aiming pose: Pointed Polygon's measured 141 x 130 against a 39 x 118 body, so
she collided with the world using a rectangle that was mostly empty air and her
own sword.

The body is the TRUNK — torso, pelvis, legs — from the crown of the head down to
the feet. Arms and weapons set no edge: an outstretched arm is a thing that
reaches, not a thing you run into, which is the same rule every hand-authored
box in this repo already follows.

Measured by rendering the trunk ALONE, because that is a fact about the drawing
rather than about the skeleton: a bone tells you where a joint is, and a body box
has to know where the art ends.
"""

from __future__ import annotations

import copy
from typing import Iterable, Optional, Sequence

#: Part-name fragments that make up the body you collide with.
TRUNK_HINTS: tuple[str, ...] = ("torso", "pelvis", "hip", "leg", "foot", "tail")
#: Part-name fragments whose TOP sets the body's ceiling — and only its top. A
#: crest, beak or antenna makes a character tall; it does not make them wide.
CROWN_HINTS: tuple[str, ...] = ("head", "skull")


def _matching(doc, hints: Sequence[str]) -> list[str]:
    return [
        str(part.get("name", ""))
        for part in doc.parts
        if any(hint in str(part.get("name", "")).lower() for hint in hints)
    ]


def _render_only(doc, names: Iterable[str], animation: str, padding):
    from .rigdoc import RigDocument

    keep = set(names)
    trimmed = RigDocument(copy.deepcopy(doc.data))
    trimmed.data["parts"] = [
        part for part in trimmed.data["parts"] if str(part.get("name", "")) in keep
    ]
    if not trimmed.data["parts"]:
        return None
    return trimmed.render_at(animation, 0.0, padding=padding).getchannel("A").getbbox()


def gameplay_body_metrics(
    doc,
    *,
    padding,
    frame_size: tuple[int, int],
    animation: str = "idle",
    trunk_hints: Sequence[str] = TRUNK_HINTS,
    crown_hints: Sequence[str] = CROWN_HINTS,
) -> Optional[dict]:
    """`body_metrics_fn`-shaped metrics for one rig, or `None` if it has no trunk.

    `frame_size` is the PUBLISHED frame the caller will hand `build_sheet`, so
    the normalized feet anchor is stated against the frame the runtime sees.
    """
    trunk = _render_only(doc, _matching(doc, trunk_hints), animation, padding)
    if trunk is None:
        return None
    crown = _render_only(doc, _matching(doc, crown_hints), animation, padding)
    top = trunk[1] if crown is None else min(trunk[1], crown[1])
    x0, x1, bottom = trunk[0], trunk[2], trunk[3]
    fw, fh = frame_size
    feet_x = (x0 + x1) / 2.0
    feet_y = float(bottom)
    return {
        "body_pixel_bbox": {
            "x": int(x0),
            "y": int(top),
            "w": int(x1 - x0),
            "h": int(bottom - top),
        },
        "feet_pixel": {"x": round(feet_x, 3), "y": round(feet_y, 3)},
        "feet_anchor_norm": {
            "x": round(feet_x / fw - 0.5, 6),
            "y": round(0.5 - feet_y / fh, 6),
        },
    }
