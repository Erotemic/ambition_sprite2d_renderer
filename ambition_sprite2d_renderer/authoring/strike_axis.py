"""Where the dangerous part of a fighter is, per frame, in published pixels.

`swing_effects` draws every effect and every hit volume from one input: a
``(base, tip)`` axis per frame. It can INFER that axis from a frame by
luminance, which works for a dark fighter carrying bright steel and fails for
anything else — a character with skin and pale shoes reads as all blade.

The rig already knows the answer, so this module supplies it two ways:

* :func:`from_bones` — the striking LIMB, read straight off the solved
  skeleton. This is the one an unarmed fighter needs: a punch's danger runs
  elbow-to-fist and a kick's knee-to-toe, and no amount of looking at pixels
  will tell you which of the four limbs is throwing this particular move.
* :func:`from_part` — the drawn WEAPON, measured on a render of that part
  alone. A blade's reach is a fact about the art, not about the bone carrying
  it, so a sword is measured rather than derived.

Both return the same shape, in the pixels of the padding they were asked for,
because an axis is a coordinate and a coordinate in another frame is a wrong
answer.
"""

from __future__ import annotations

import copy
import math
from typing import Iterable, Sequence

from . import swing_effects
from .rigdoc import RigDocument, normalize_render_padding, translate_bone_worlds

#: A strike spec names the two ends of the limb: ``base`` is the bone whose
#: ORIGIN the danger starts at, ``tip`` the bone whose far end it reaches to.
#: ``{"base": "near_arm_l", "tip": "near_arm_hand"}`` is a punch — elbow to
#: knuckles. ``{"base": "near_leg_l", "tip": "near_leg_foot"}`` is a kick.
Strike = dict


def bone_tip(world, name: str) -> tuple[float, float]:
    """The far end of one solved bone."""
    bone = world[name]
    return (
        bone.origin[0] + math.cos(math.radians(bone.angle)) * bone.length,
        bone.origin[1] + math.sin(math.radians(bone.angle)) * bone.length,
    )


def from_bones(
    doc: RigDocument,
    animation: str,
    samples: Sequence[float],
    strike: Strike,
    *,
    padding=None,
):
    """Axes for one clip, read off the solved skeleton at each sample.

    Analytic, not rasterized: the bone transforms that place the art already
    say where the fist ends up, so there is nothing to measure and nothing to
    threshold. A limb hidden behind the torso still reports its position, which
    a pixel method cannot do and a hit volume must not lose.
    """
    left, top, _right, _bottom = normalize_render_padding(padding)
    base_name, tip_name = str(strike["base"]), str(strike["tip"])
    axes = []
    for t in samples:
        world, _params = doc.solve(animation, float(t))
        world = translate_bone_worlds(world, float(left), float(top))
        if base_name not in world or tip_name not in world:
            axes.append(None)
            continue
        base = world[base_name].origin
        tip = bone_tip(world, tip_name)
        if math.dist(base, tip) < 1e-6:
            axes.append(None)
            continue
        axes.append(((base[0], base[1]), (tip[0], tip[1])))
    return axes


def part_only_document(doc: RigDocument, part_name: str) -> RigDocument:
    """The same rig with only ``part_name`` painted."""
    data = copy.deepcopy(doc.data)
    data["parts"] = [part for part in data["parts"] if part["name"] == part_name]
    if not data["parts"]:
        raise ValueError(f"rig has no part named {part_name!r} to strike with")
    return RigDocument(data, source_path=doc.source_path)


def silhouette_axis(image, anchor):
    """Long axis of everything opaque, oriented away from ``anchor``.

    ⛔ NO BRIGHTNESS THRESHOLD. `blade_axis` splits blade from anatomy by
    luminance because it is handed a whole character; on a frame holding one
    part there is no anatomy to split from, and thresholding there just asks
    whether the weapon happens to be pale. Carl's telescope is dark brass and
    darker wood — not one pixel of it clears the threshold — so the inference
    returned nothing at all and his swings published no volume.

    ``anchor`` is the hand (or foot) the part is held in, which is what decides
    which end is the grip and which is the business end.
    """
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        return None
    pixels = alpha.load()
    points = [
        (x, y)
        for y in range(bbox[1], bbox[3])
        for x in range(bbox[0], bbox[2])
        if pixels[x, y] > 40
    ]
    if len(points) < 6:
        return None
    count = len(points)
    cx = sum(p[0] for p in points) / count
    cy = sum(p[1] for p in points) / count
    sxx = syy = sxy = 0.0
    for x, y in points:
        dx, dy = x - cx, y - cy
        sxx += dx * dx
        syy += dy * dy
        sxy += dx * dy
    theta = 0.5 * math.atan2(2 * sxy, sxx - syy)
    ux, uy = math.cos(theta), math.sin(theta)
    projected = [(((x - cx) * ux + (y - cy) * uy), (x, y)) for x, y in points]
    low = min(projected)[1]
    high = max(projected)[1]
    near = lambda p: math.dist(p, anchor)
    return (low, high) if near(low) < near(high) else (high, low)


def from_part(
    doc: RigDocument,
    animation: str,
    samples: Sequence[float],
    part_name: str,
    *,
    padding=None,
    anchor_bone: str | None = None,
):
    """Axes measured on a render of one part alone.

    The part IS the weapon, so its whole silhouette is the axis. ``anchor_bone``
    names the joint holding it — defaulting to the bone the part rides — and
    only decides which end is the grip.
    """
    only = part_only_document(doc, part_name)
    if anchor_bone is None:
        part = next(p for p in doc.parts if p["name"] == part_name)
        anchor_bone = str(part.get("bone"))
    left, top, _right, _bottom = normalize_render_padding(padding)
    axes = []
    for t in samples:
        image = only.render_at(animation, float(t), supersample=1, padding=padding)
        world, _params = doc.solve(animation, float(t))
        world = translate_bone_worlds(world, float(left), float(top))
        anchor = world[anchor_bone].origin if anchor_bone in world else (0.0, 0.0)
        axes.append(silhouette_axis(image, anchor))
    return axes


def for_spec(
    doc: RigDocument,
    animation: str,
    samples: Sequence[float],
    spec: dict,
    *,
    padding=None,
):
    """Axes for whichever way this clip's spec declares its danger.

    One entry point so a character's target does not branch on archetype: the
    spec says ``strike`` (a limb) or ``strike_part`` (drawn art), and the caller
    just asks.
    """
    strike = spec.get("strike")
    if isinstance(strike, dict):
        return from_bones(doc, animation, samples, strike, padding=padding)
    part = spec.get("strike_part")
    if part:
        return from_part(doc, animation, samples, str(part), padding=padding)
    return None


__all__ = [
    "bone_tip",
    "silhouette_axis",
    "for_spec",
    "from_bones",
    "from_part",
    "part_only_document",
]
