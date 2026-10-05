"""The fish family's anatomy, for ``creature_rig``: a legless swimmer or flyer.

The burning flying shark's body: a ``body`` bone at its centre of mass (the
root; a clip pitches the whole fish with it), a ``head`` forward of the gills
with a hinged ``jaw``, a three-bone tail (``tail1``, ``tail2`` to the
peduncle, ``fluke`` the caudal fin) that undulates, a ``dorsal`` fin, and a
pectoral fin per side (``near_pec`` / ``far_pec``) that beats like a wing.
The SVG marks the joints ``body``, ``head``, ``snout``, ``jaw``, ``tail1``,
``tail2``, ``tail_tip``, ``dorsal``, ``dorsal_tip``, and per side
``<side>_pec`` and ``<side>_pec_tip``.

With no legs there is no IK and no ground contact: ``root_x`` / ``root_y``
move the fish about the drawing's centre and its ground line is only the
frame's reference.
"""

from __future__ import annotations

import math
from typing import Dict, List

from .creature_rig import (  # noqa: F401  (re-exported for builder scripts)
    BoneSpec,
    CreatureSpec,
    Point,
    Pose,
    eyes,
    pulse,
    segment,
    smooth01,
    track,
    write,
)


def skeleton(J: Dict[str, Point], jaw_length: float) -> List[BoneSpec]:
    bones = [("body", None, J["body"], 0.0, 0.0)]
    head = segment("head", "body", J["head"], J["snout"])
    bones.append(head)
    bones.append(("jaw", "head", J["jaw"], head[3], jaw_length))
    bones.append(segment("tail1", "body", J["tail1"], J["tail2"]))
    bones.append(segment("tail2", "tail1", J["tail2"], J["tail_tip"]))
    bones.append(segment("fluke", "tail2", J["tail_tip"], (2 * J["tail_tip"][0] - J["tail2"][0],
                                                           2 * J["tail_tip"][1] - J["tail2"][1])))
    bones.append(segment("dorsal", "body", J["dorsal"], J["dorsal_tip"]))
    for side in ("far", "near"):
        bones.append(segment(f"{side}_pec", "body", J[f"{side}_pec"], J[f"{side}_pec_tip"]))
    return bones


def fish_spec(*, jaw_length: float = 20.0, **fields) -> CreatureSpec:
    """A ``CreatureSpec`` with the fish skeleton and no legs."""
    return CreatureSpec(skeleton=lambda J: skeleton(J, jaw_length), legs=(), **fields)


def swim(t: float, *, beats: float = 1.0, tail: float, fin: float, bob: float, pitch: float = 0.0) -> Pose:
    """An undulating loop: a wave runs back along the tail (each bone a little
    later and further than the last), the pectoral fins beat like wings, the
    body bobs against the beat and the head counters the tail."""
    w = math.tau * t * beats
    p: Pose = {
        "root_y": bob * math.sin(w + 0.4),
        "body": pitch + 0.25 * tail * math.sin(w),
        "head": -0.35 * tail * math.sin(w - 0.4),
        "tail1": 0.5 * tail * math.sin(w - 0.6),
        "tail2": 0.8 * tail * math.sin(w - 1.3),
        "fluke": 1.2 * tail * math.sin(w - 2.0),
        "near_pec": fin * math.sin(w + 1.0),
        "far_pec": -fin * 0.8 * math.sin(w + 1.0),
        "dorsal": -0.25 * tail * math.sin(w - 0.8),
    }
    return p
