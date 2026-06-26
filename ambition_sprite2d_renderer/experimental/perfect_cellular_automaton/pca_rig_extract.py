#!/usr/bin/env python3
"""Build a bone rig for the Perfect Cell-ular Automaton from its hand-drawn SVG.

This is the *robust process* for turning ``PCA-multiview.svg`` into an
animatable ``.rig.json``: it never reconstructs the art (the old, failed
approach) — it binds the artist's own vector parts to bones and lets the
existing FK/IK skeleton pose them.

Two things in the SVG are the durable contract (survive id churn and reshaping):

1. **The layer hierarchy** names body regions and segments. Under the
   ``View - Front Right`` layer the six region groups are ``Arm - Right`` /
   ``Arm - Left`` (near/far arm), ``Leg - Right`` / ``Leg - Left`` (near/far
   leg), ``Torso`` and ``Head``. Within a limb each leaf is sorted into a bone
   segment by the *nearest enclosing group label*: ``…Hand…`` → hand,
   ``…Lower…``/``…Forearm…`` → lower, ``…Upper…``/``…Shoulder…`` → upper (legs:
   ``…Foot…`` → foot, ``…Lower…``/``…Shin…`` → lower, ``…Upper…`` → upper).
   Unlabelled detail paths (finger lines, helmet detail, belly grid) inherit
   their parent group's segment, so they ride the right bone for free.

2. **The ``Joints`` layer** carries the skeleton directly: 16 circles labelled
   ``joint-<side>-<a>-<b>`` mark every real articulation (shoulder, elbow,
   wrist, hip, knee, ankle, neck, waist). We read those positions verbatim
   rather than guessing joints from bounding boxes — the artist placed them on
   the art, so the skeleton tracks the art exactly. Hand tips and toe tips are
   *not* joints; they're derived as the farthest point of the hand/foot mask
   from the wrist/ankle, which is orientation-agnostic.

In this view the character faces +x; its **right** side is drawn last and so is
*near* (in front), its **left** side is *far*. Re-run this whenever the SVG
changes — the ``.rig.json`` is a generated artifact:

    PY=.venv/bin/python
    $PY .../pca_rig_extract.py build       # writes the rig into targets/.../rigged/
    $PY .../pca_rig_extract.py validate    # rest pose -> agent-scratch/pca_rig/
    $PY .../pca_rig_extract.py debug idle   # skeleton-on-art overlay -> agent-scratch/pca_rig/
"""
from __future__ import annotations

import argparse
import json
import math
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

# Allow running as a loose script (the experimental dir isn't a package).
import sys
_AUTHORING = Path(__file__).resolve().parents[2]
if str(_AUTHORING) not in sys.path:
    sys.path.insert(0, str(_AUTHORING))

from authoring.svg_parts import (  # noqa: E402
    rasterize_subset, _local, _label,
)

TOOL_ROOT = Path(__file__).resolve().parents[3]
SVG = TOOL_ROOT / "assets/perfect-cellular-automaton/PCA-multiview.svg"
RIGGED_DIR = _AUTHORING / "targets/characters/rigged"
RIG_OUT = RIGGED_DIR / "perfect_cellular_automaton.rig.json"
# Human-reviewable debug renders land in the repo's gitignored scratch dir (NOT
# /tmp, which isn't visible from the dev VM).
SCRATCH_DIR = TOOL_ROOT / "agent-scratch" / "pca_rig"

VIEW = "View - Front Right"
REF_DPI = 96.0
# Output resolution multiplier (geometry stays authored in base-frame units;
# vector source rasterizes crisply, so we can afford a high multiplier).
RENDER_SCALE = 3

# Top region group label -> (region kind, side). "Right" is drawn last in this
# view, so it is the near (front) side; "Left" is far.
REGION = {
    "Arm - Right": ("arm", "near"),
    "Arm - Left": ("arm", "far"),
    "Leg - Right": ("leg", "near"),
    "Leg - Left": ("leg", "far"),
    "Torso": ("torso", None),
    "Head": ("head", None),
}

# Authored joint circles are labelled by one grammar — ``joint-<side>-<a>-<b>``,
# side ∈ {right,left,center}, ``<a>``/``<b>`` the two parts it connects — so the
# skeleton name is *parsed*, not table-matched. ``right``→near, ``left``→far; the
# articulation comes from the (unordered) part pair. Hand/toe tips are derived
# (not joints), and the decorative ``torso-shoulder`` pad pair is unmapped → skipped.
_SIDE = {"right": "near", "left": "far"}
_LIMB_JOINT = {
    frozenset({"shoulder", "upperarm"}): "shoulder",
    frozenset({"upperarm", "lowerarm"}): "elbow",
    frozenset({"lowerarm", "hand"}): "wrist",
    frozenset({"hip", "upperleg"}): "hip",
    frozenset({"upperleg", "lowerleg"}): "knee",
    frozenset({"lowerleg", "foot"}): "ankle",
}
_CENTER_JOINT = {  # spine joints carry no left/right side
    frozenset({"neck", "head"}): "neck",
    frozenset({"hip", "torso"}): "waist",
}


def _joint_name(label: str) -> Optional[str]:
    """``joint-right-shoulder-upperarm`` -> ``near_shoulder`` (or None to skip)."""
    parts = (label or "").split("-")
    if len(parts) != 4 or parts[0] != "joint":
        return None
    side, pair = parts[1], frozenset(parts[2:])
    if side == "center":
        return _CENTER_JOINT.get(pair)
    role = _LIMB_JOINT.get(pair)
    return f"{_SIDE[side]}_{role}" if role and side in _SIDE else None

_SEG_KEY = {"upper": "u", "lower": "l", "hand": "hand", "foot": "foot"}


# ---- SVG -> (bone -> art ids) classification ---------------------------------


def _ancestry(elem: ET.Element, parent: Dict[ET.Element, ET.Element]) -> List[ET.Element]:
    out: List[ET.Element] = []
    cur: Optional[ET.Element] = elem
    while cur is not None:
        out.append(cur)
        cur = parent.get(cur)
    return out  # leaf-first, up to the root


def _top_group(chain: List[ET.Element]) -> Optional[str]:
    """Label of the ``VIEW``'s direct child that contains the leaf."""
    for i, node in enumerate(chain):
        if _label(node) == VIEW and i > 0:
            return _label(chain[i - 1])
    return None


def _segment(kind: str, chain: List[ET.Element]) -> Optional[str]:
    """Bone segment for a leaf, from the nearest enclosing group label."""
    for node in chain:
        t = (_label(node) or "").lower()
        if not t:
            continue
        if kind == "arm":
            if "hand" in t:
                return "hand"
            if "lower" in t or "forearm" in t:
                return "lower"
            if "upper" in t or "shoulder" in t:
                return "upper"
        elif kind == "leg":
            if "foot" in t or "toe" in t:
                return "foot"
            if "lower" in t or "shin" in t:
                return "lower"
            if "upper" in t:
                return "upper"
    return None


def _bone_for_leaf(chain: List[ET.Element]) -> Optional[str]:
    top = _top_group(chain)
    if top not in REGION:
        return None
    kind, side = REGION[top]
    if kind in ("torso", "head"):
        return kind
    seg = _segment(kind, chain)
    if seg is None:
        return None
    limb = "arm" if kind == "arm" else "leg"
    return f"{side}_{limb}_{_SEG_KEY[seg]}"


def _collect() -> Dict[str, List[Tuple[str, ET.Element]]]:
    """Group every drawable leaf under VIEW by bone name -> [(id, elem), ...].

    The ``Joints`` layer is skipped: its circles drive the skeleton, never the
    art (and because each part only ever rasterizes its own ids, the joints can
    never leak into a rendered sprite)."""
    root = ET.fromstring(SVG.read_bytes())
    parent = {c: p for p in root.iter() for c in p}
    bones: Dict[str, List[Tuple[str, ET.Element]]] = {}
    for elem in root.iter():
        if _local(elem.tag) not in ("path", "polygon", "rect", "ellipse", "circle", "line"):
            continue
        chain = _ancestry(elem, parent)
        labels = {_label(n) for n in chain}
        if VIEW not in labels or "Joints" in labels:
            continue
        bone = _bone_for_leaf(chain)
        if bone is None:
            continue
        bones.setdefault(bone, []).append((elem.get("id", ""), elem))
    return bones


def _authored_joints() -> Dict[str, Tuple[float, float]]:
    """Skeleton joints in reference px, read straight from the Joints layer.

    Each joint circle rasterizes in the same full-document frame as every part
    (resvg applies the identical transform chain), so a circle's raster centre
    is its joint position in the parts' coordinate system — no transform math."""
    root = ET.fromstring(SVG.read_bytes())
    out: Dict[str, Tuple[float, float]] = {}
    for elem in root.iter():
        if _local(elem.tag) != "circle":
            continue
        name = _joint_name(_label(elem) or "")
        if name is None:
            continue
        img, (ox, oy), _ = rasterize_subset(SVG, VIEW, [elem.get("id", "")], REF_DPI)
        if img is None:
            continue
        w, h = img.size
        out[name] = (ox + w / 2.0, oy + h / 2.0)
    return out


def _cx(b):  # bbox center x
    return (b[0] + b[2]) / 2.0


def build_skeleton_data() -> dict:
    bones = _collect()
    ids = {name: [i for i, _ in items] for name, items in bones.items()}

    # Rasterize each bone's art once to a full-canvas alpha mask (ref-px). Masks
    # bound the figure (head top, feet) and locate the two non-joint tips.
    masks: Dict[str, Tuple[np.ndarray, int, int]] = {}
    bb: Dict[str, Tuple[float, float, float, float]] = {}
    for name, idlist in ids.items():
        img, (ox, oy), _ = rasterize_subset(SVG, VIEW, idlist, REF_DPI)
        if img is None:
            continue
        a = np.asarray(img.getchannel("A")) > 24
        masks[name] = (a, ox, oy)
        h, w = a.shape
        bb[name] = (ox, oy, ox + w, oy + h)

    def farthest(name: str, frm: Tuple[float, float]) -> Tuple[float, float]:
        """Mask pixel of ``name`` farthest from ``frm`` — a limb's free tip."""
        a, ox, oy = masks[name]
        ys, xs = np.nonzero(a)
        px = xs.astype(float) + ox
        py = ys.astype(float) + oy
        i = int(np.argmax((px - frm[0]) ** 2 + (py - frm[1]) ** 2))
        return (float(px[i]), float(py[i]))

    # --- joints: authored articulations + derived hand/toe tips (ref-px) ---
    J: Dict[str, Tuple[float, float]] = _authored_joints()
    for side in ("near", "far"):
        wrist, hand = f"{side}_wrist", f"{side}_arm_hand"
        if wrist in J and hand in masks:
            J[f"{side}_handtip"] = farthest(hand, J[wrist])
        ankle, foot = f"{side}_ankle", f"{side}_leg_foot"
        if ankle in J and foot in masks:
            J[f"{side}_toe"] = farthest(foot, J[ankle])

    hip_c = (
        (J["near_hip"][0] + J["far_hip"][0]) / 2,
        (J["near_hip"][1] + J["far_hip"][1]) / 2,
    )
    waist = J.get("waist", hip_c)   # torso hinges at the authored spine base
    neck = J.get("neck", waist)
    head_top = bb["head"][1] if "head" in bb else neck[1]

    # --- px -> frame mapping: feet to ground_y, body center to center_x ---
    feet_y = max(bb[k][3] for k in bb if k.endswith("foot")) if any(
        k.endswith("foot") for k in bb) else max(b[3] for b in bb.values())
    char_h = feet_y - head_top
    FRAME_H, FRAME_W = 192, 128
    GROUND_Y, CENTER_X, ANKLE_H = 176.0, 64.0, 2.0
    target_h = 150.0
    K = target_h / char_h
    center_x_px = hip_c[0]

    def m(p):  # ref-px -> frame units
        return ((p[0] - center_x_px) * K + CENTER_X, (p[1] - feet_y) * K + GROUND_Y)

    root = (CENTER_X, GROUND_Y)

    # --- bone tree: (name, parent, proximal joint, distal joint|None) ---
    specs: List[Tuple[str, Optional[str], Tuple[float, float], Optional[Tuple[float, float]]]] = [
        ("pelvis", None, hip_c, None),
        ("torso", "pelvis", waist, None),
        ("head", "torso", neck, None),
    ]
    for side in ("far", "near"):  # far first so near draws over it
        specs += [
            (f"{side}_arm_u", "torso", J[f"{side}_shoulder"], J[f"{side}_elbow"]),
            (f"{side}_arm_l", f"{side}_arm_u", J[f"{side}_elbow"], J[f"{side}_wrist"]),
            (f"{side}_arm_hand", f"{side}_arm_l", J[f"{side}_wrist"], J[f"{side}_handtip"]),
            (f"{side}_leg_u", "pelvis", J[f"{side}_hip"], J[f"{side}_knee"]),
            (f"{side}_leg_l", f"{side}_leg_u", J[f"{side}_knee"], J[f"{side}_ankle"]),
            (f"{side}_leg_foot", f"{side}_leg_l", J[f"{side}_ankle"], J[f"{side}_toe"]),
        ]

    # Build BoneWorld rest transforms, then derive parent-relative offset/rest.
    world: Dict[str, Tuple[Tuple[float, float], float]] = {}  # name -> (origin_frame, angle_deg)
    bone_json: List[dict] = []
    proximal_px: Dict[str, Tuple[float, float]] = {}
    for name, par, jp, jd in specs:
        o = m(jp)
        proximal_px[name] = jp
        if jd is not None:
            d = m(jd)
            ang = math.degrees(math.atan2(d[1] - o[1], d[0] - o[0]))
            length = math.hypot(d[0] - o[0], d[1] - o[1])
        else:
            ang, length = 0.0, 0.0
        if par is None:
            po, pa = root, 0.0
        else:
            po, pa = world[par]
        # offset in parent-local frame; rest_angle relative to parent
        dx, dy = o[0] - po[0], o[1] - po[1]
        ca, sa = math.cos(math.radians(-pa)), math.sin(math.radians(-pa))
        off = (dx * ca - dy * sa, dx * sa + dy * ca)
        bone_json.append({
            "name": name, "parent": par,
            "offset": [round(off[0], 3), round(off[1], 3)],
            "length": round(length, 3), "rest_angle": round(ang - pa, 3),
        })
        world[name] = (o, ang)

    return {
        "bones": bone_json,
        "ids": ids,
        "proximal_px": proximal_px,
        "rest_angle": {n: a for n, (_, a) in world.items()},
        # World-space (frame-unit) rest transform of every bone — used to author
        # IK leg targets that reproduce the *drawn* stance (origin == joint).
        "world": {n: {"origin": list(o), "angle": a} for n, (o, a) in world.items()},
        "frame": dict(width=FRAME_W, height=FRAME_H, ground_y=GROUND_Y,
                      center_x=CENTER_X, ankle_h=ANKLE_H),
        "K": K,
    }


# z-order: far limbs behind torso/head, near limbs in front.
Z = {
    "far_leg_u": 5, "far_leg_l": 6, "far_leg_foot": 7,
    "far_arm_u": 8, "far_arm_l": 9, "far_arm_hand": 10,
    "pelvis": 20, "torso": 22, "head": 30,
    "near_leg_u": 40, "near_leg_l": 41, "near_leg_foot": 42,
    "near_arm_u": 60, "near_arm_l": 61, "near_arm_hand": 62,
}


def _clips(near_rx: float, far_rx: float) -> dict:
    """Animation clips authored against the rig's bones + IK foot channels.

    Channel conventions (see rigdoc): a bone name = pose angle in degrees on top
    of its rest (screen CW-positive); ``root_x``/``root_y`` shift the whole body
    from (center_x, ground_y); ``<side>_foot_x`` is the planted foot's world x
    offset from center_x, ``_lift`` raises it, ``_pitch`` sets its angle. Legs
    are posed by authoring foot trajectories; IK places the knees.

    The rest pose already matches the drawn stance (arms hanging, feet planted),
    so idle/fly only need to layer *subtle* motion on top — the figure breathes,
    it doesn't flail."""
    gait = (near_rx + far_rx) / 2.0  # feet converge under the body when walking
    A = 9.0    # stride half-amplitude (world x)
    H = 7.0    # foot swing lift

    def foot_x(phase):  # planted forward -> back, swing back -> forward
        c = [(0.0, gait + A), (0.5, gait - A), (1.0, gait + A)]
        return {"keys": [[round((t + phase) % 1.0, 3), v, "sine"] for t, v in c]
                if phase == 0 else
                [[0.0, gait - A, "sine"], [0.5, gait + A, "sine"], [1.0, gait - A, "sine"]]}

    def foot_lift(swing_mid):  # single lift bump centered on the swing midpoint
        return {"keys": [[0.0, 0.0, "sine"], [round(swing_mid - 0.25, 3), 0.0, "sine"],
                         [swing_mid, H, "sine"], [round(swing_mid + 0.25, 3), 0.0, "sine"],
                         [1.0, 0.0, "sine"]]}

    def const(**ch):  # a held single-frame pose
        return {"loop": False, "frames": 1, "channels": {k: {"const": v} for k, v in ch.items()}}

    return {
        # Idle: a slow breath — chest rises (root lifts a hair), torso and head
        # counter-sway, arms drift, weight settles. Two-beat asymmetry on the
        # arms keeps it from looking like a metronome.
        "idle": {"loop": True, "frames": 10, "duration_ms": 120, "channels": {
            "root_y": {"expr": "-0.8*sin(tau*t)"},
            "torso": {"expr": "1.6*sin(tau*t)"},
            "head": {"expr": "-1.4*sin(tau*(t-0.12))"},
            "near_arm_u": {"expr": "2.2*sin(tau*t)"},
            "near_arm_l": {"expr": "4.0*sin(tau*(t-0.10))"},
            "far_arm_u": {"expr": "-2.2*sin(tau*t)"},
            "far_arm_l": {"expr": "-4.0*sin(tau*(t-0.10))"},
        }},
        # Contralateral walk: near foot forward when far foot is back; arms swing
        # opposite their legs; body bobs twice per stride (lowest at each contact).
        "walk": {"loop": True, "frames": 8, "duration_ms": 90, "channels": {
            "near_foot_x": foot_x(0.0),
            "far_foot_x": foot_x(0.5),
            "near_foot_lift": foot_lift(0.75),
            "far_foot_lift": foot_lift(0.25),
            "root_y": {"expr": "-1.5*abs(sin(tau*t))"},
            "torso": {"expr": "-2.5*sin(2*tau*t)"},
            "near_arm_u": {"keys": [[0.0, 16, "sine"], [0.5, -16, "sine"], [1.0, 16, "sine"]]},
            "far_arm_u": {"keys": [[0.0, -16, "sine"], [0.5, 16, "sine"], [1.0, -16, "sine"]]},
            "near_arm_l": {"const": 8.0},
            "far_arm_l": {"const": 8.0},
        }},
        # Crouch: hips drop and the feet tuck UNDER the body (the splayed idle
        # stance would make the bent legs sprawl), so the knees fold compactly.
        "crouch": const(root_y=13.0, torso=-7.0,
                        near_foot_x=gait - 4.0, far_foot_x=gait + 4.0,
                        near_arm_u=14.0, near_arm_l=22.0,
                        far_arm_u=14.0, far_arm_l=22.0),
        # Jab: quick straight lead (near) arm — wind back, then snap forward.
        "jab": {"loop": False, "frames": 5, "duration_ms": 45, "channels": {
            "torso": {"keys": [[0.0, 0, "out"], [0.3, 6, "out"], [0.5, -6, "out"], [1.0, 0]]},
            "near_arm_u": {"keys": [[0.0, 10, "out"], [0.3, 30, "out"], [0.5, -82, "out"], [1.0, -78]]},
            "near_arm_l": {"keys": [[0.0, 20, "out"], [0.3, 55, "out"], [0.5, -4, "out"], [1.0, 0]]},
        }},
        # Punch: heavier cross with the far arm + a hip/torso twist and lead step.
        "punch": {"loop": False, "frames": 6, "duration_ms": 55, "channels": {
            "torso": {"keys": [[0.0, 0, "out"], [0.35, 8, "out"], [0.6, -9, "out"], [1.0, -4]]},
            "far_arm_u": {"keys": [[0.0, 18, "out"], [0.35, 38, "out"], [0.6, -86, "out"], [1.0, -82]]},
            "far_arm_l": {"keys": [[0.0, 20, "out"], [0.35, 60, "out"], [0.6, -2, "out"], [1.0, 0]]},
            "near_arm_u": {"keys": [[0.0, -6], [0.6, 26, "out"], [1.0, 22]]},
            "near_arm_l": {"const": 30.0},
        }},
        # Block: both arms swing up into a cross-guard in front of the head/chest.
        # (The far forearm mirrors the near, so its curl takes the opposite sign.)
        "block": const(torso=-3.0, near_arm_u=-72.0, near_arm_l=80.0,
                       far_arm_u=-72.0, far_arm_l=-80.0),
        # Jump: anticipation crouch -> explosive extension (arms up) -> airborne tuck.
        "jump": {"loop": False, "frames": 6, "duration_ms": 70, "channels": {
            "root_y": {"keys": [[0.0, 14, "out"], [0.35, -8, "out"], [1.0, -4]]},
            "torso": {"keys": [[0.0, -6], [0.35, 4], [1.0, 0]]},
            "near_arm_u": {"keys": [[0.0, 12, "out"], [0.35, -120, "out"], [1.0, -110]]},
            "far_arm_u": {"keys": [[0.0, 12, "out"], [0.35, -120, "out"], [1.0, -110]]},
            "near_foot_lift": {"keys": [[0.0, 0], [0.35, 0], [0.6, 14, "out"], [1.0, 10]]},
            "far_foot_lift": {"keys": [[0.0, 0], [0.35, 0], [0.6, 14, "out"], [1.0, 10]]},
        }},
        # Fly / hover: lifted off the ground, legs trailing, arms relaxed and
        # spread symmetrically (mirrored far-side signs), slow torso/arm sway.
        "fly": {"loop": True, "frames": 8, "duration_ms": 130, "channels": {
            "root_y": {"const": -22.0},
            "near_foot_lift": {"const": 22.0},
            "far_foot_lift": {"const": 22.0},
            "torso": {"expr": "3*sin(tau*t)"},
            "near_arm_u": {"expr": "16+5*sin(tau*t)"},
            "far_arm_u": {"expr": "16+5*sin(tau*t)"},
            "near_arm_l": {"const": 20.0},
            "far_arm_l": {"const": -20.0},
        }},
        # Special: kamehameha — charge with both hands cupped back at the hip,
        # then thrust both arms forward (the glider volley fires on the thrust).
        "special": {"loop": False, "frames": 10, "duration_ms": 70, "channels": {
            "torso": {"keys": [[0.0, 10, "out"], [0.55, 12, "out"], [0.7, -8, "out"], [1.0, -4]]},
            "near_arm_u": {"keys": [[0.0, 44, "out"], [0.55, 44, "out"], [0.7, -84, "out"], [1.0, -80]]},
            "near_arm_l": {"keys": [[0.0, 78, "out"], [0.55, 78, "out"], [0.7, 2, "out"], [1.0, 0]]},
            "far_arm_u": {"keys": [[0.0, 44, "out"], [0.55, 44, "out"], [0.7, -84, "out"], [1.0, -80]]},
            "far_arm_l": {"keys": [[0.0, 78, "out"], [0.55, 78, "out"], [0.7, 2, "out"], [1.0, 0]]},
        }},
    }


def build_doc() -> dict:
    sk = build_skeleton_data()
    parts = []
    for b in sk["bones"]:
        name = b["name"]
        ids = sk["ids"].get(name)
        if not ids:
            continue
        jp = sk["proximal_px"][name]
        parts.append({
            "name": name, "bone": name, "z": Z.get(name, 50), "kind": "sprite",
            "include": ids,
            "pivot": [round(jp[0], 2), round(jp[1], 2)],
            "rest_angle": round(sk["rest_angle"][name], 3),
        })
    parts.sort(key=lambda p: p["z"])

    svg_rel = os.path.relpath(SVG, RIGGED_DIR)
    fr = sk["frame"]
    # Source art is vector, so publish at higher pixel resolution (render_scale)
    # without touching the authored geometry or the in-game display size.
    fr.update(supersample=4, render_scale=RENDER_SCALE)

    # IK rest targets measured from the drawn stance so the default pose matches
    # the artwork (no crossed legs, no bent knees). ankle_h is shared, so each
    # foot's height difference is absorbed by a per-leg rest_lift.
    cx, gy = fr["center_x"], fr["ground_y"]
    W = sk["world"]
    ankles = {s: W[f"{s}_leg_foot"]["origin"] for s in ("near", "far")}
    mean_ankle_y = sum(a[1] for a in ankles.values()) / 2.0
    fr["ankle_h"] = round(gy - mean_ankle_y, 3)
    ik_legs = []
    for side in ("near", "far"):
        ax, ay = ankles[side]
        ik_legs.append({
            "upper": f"{side}_leg_u", "lower": f"{side}_leg_l",
            "foot": f"{side}_leg_foot", "channel_prefix": f"{side}_foot",
            "rest_x": round(ax - cx, 3),
            "rest_lift": round(mean_ankle_y - ay, 3),
            "rest_pitch": round(W[f"{side}_leg_foot"]["angle"], 3),
            # Knees bend forward (+x) for this +x-facing view — anatomically and
            # locomotion-correct. (The drawn standing legs are near-straight, so
            # their micro-bow is not a reliable bend signal.)
            "bend": 1.0,
        })

    return {
        "name": "perfect_cellular_automaton",
        "frame": fr,
        "svg_source": {
            "path": svg_rel, "view": VIEW,
            "ref_dpi": REF_DPI, "scale": round(sk["K"], 6),
        },
        "palette": {},
        "bones": sk["bones"],
        "parts": parts,
        "ik_legs": ik_legs,
        "clips": _clips(ik_legs[0]["rest_x"], ik_legs[1]["rest_x"]),
        "sprite_tuning": {"collision_scale": 1.6},
    }


def cmd_build(_args):
    RIGGED_DIR.mkdir(parents=True, exist_ok=True)
    doc = build_doc()
    RIG_OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf8")
    print(f"wrote {RIG_OUT}  ({len(doc['bones'])} bones, {len(doc['parts'])} parts)")


def cmd_validate(_args):
    from authoring.rigdoc import RigDocument
    cmd_build(_args)
    doc = RigDocument.load(RIG_OUT)
    # Pure rest = idle@0 with IK disabled (IK tuning is separate from binding).
    doc.data["ik_legs"] = []
    frame = doc.render_at("idle", 0.0)
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    out = SCRATCH_DIR / "rest.png"
    frame.save(out)
    print(f"rest frame -> {out}  size={frame.size}")


def cmd_debug(args):
    """Render bone-debug overlays (skeleton on dimmed art) for clips -> /tmp."""
    from authoring.rigdoc import RigDocument
    from authoring.debug_overlay import render_clip_strip
    cmd_build(args)
    doc = RigDocument.load(RIG_OUT)
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    clips = args.clips or list(doc.clips.keys())
    for name in clips:
        if name not in doc.clips:
            print(f"  (no clip {name!r})")
            continue
        out = SCRATCH_DIR / f"dbg_{name}.png"
        render_clip_strip(doc, name, scale=args.scale).convert("RGB").save(out)
        print(f"  {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build").set_defaults(fn=cmd_build)
    sub.add_parser("validate").set_defaults(fn=cmd_validate)
    dbg = sub.add_parser("debug")
    dbg.add_argument("clips", nargs="*", help="clip names (default: all)")
    dbg.add_argument("--scale", type=int, default=2)
    dbg.set_defaults(fn=cmd_debug)
    args = ap.parse_args()
    args.fn(args)
