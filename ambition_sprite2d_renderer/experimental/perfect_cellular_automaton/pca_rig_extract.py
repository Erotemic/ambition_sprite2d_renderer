#!/usr/bin/env python3
"""Build a bone rig for the Perfect Cell-ular Automaton from its hand-drawn SVG.

This is the *robust process* for turning ``pca-front-side.svg`` into an
animatable ``.rig.json``: it never reconstructs the art (the old, failed
approach) — it binds the artist's own vector parts to bones and lets the
existing FK/IK skeleton pose them.

How parts map to bones (the durable contract — survives id churn and reshaping
as long as these Inkscape *group labels* and naming keywords hold):

  * The top-level groups under ``VIEW-front-right`` are the body regions:
    ``Right-arm-front-right`` / ``left-arm`` (near/far arm),
    ``right-leg`` / ``left-leg`` (near/far leg), ``body`` (torso), and
    ``Head-front-right`` (head).
  * Within a limb, each leaf is sorted into a segment by keyword — anything
    ``hand``/``claw``/``finger`` → hand, ``lower``/``forearm``/``cuff``/
    ``shin``/``foot``/``toes``/``heel`` → lower/foot, else upper. Unlabelled
    detail paths inherit the label of their nearest labelled group (so
    ``finger-lines``, ``helmet-detail``, ``belly-grid`` resolve correctly).

Joints (shoulder/elbow/wrist, hip/knee/ankle, neck) are measured from the
aggregate bounding box of each segment's art, so the skeleton tracks the art.
Re-run this whenever the SVG changes; the ``.rig.json`` is a generated artifact.

    PY=.venv/bin/python
    $PY .../pca_rig_extract.py build       # writes the rig into targets/.../rigged/
    $PY .../pca_rig_extract.py validate     # rest pose vs full-view raster -> /tmp
"""
from __future__ import annotations

import argparse
import json
import math
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
    INK_NS, SVG_NS, MM_PER_INCH, rasterize_subset, _local, _label,
)

REPO = Path(__file__).resolve().parents[5]
SVG = REPO / "assets/manual-svgs/perfect-cellular-automaton/pca-front-side.svg"
RIGGED_DIR = _AUTHORING / "targets/characters/rigged"
RIG_OUT = RIGGED_DIR / "perfect_cellular_automaton.rig.json"

VIEW = "VIEW-front-right"
REF_DPI = 96.0
# Output resolution multiplier (geometry stays authored in base-frame units;
# vector source rasterizes crisply, so we can afford a high multiplier).
RENDER_SCALE = 3

# top group label -> (region kind, side)
REGION = {
    "Right-arm-front-right": ("arm", "near"),
    "left-arm": ("arm", "far"),
    "right-leg": ("leg", "near"),
    "left-leg": ("leg", "far"),
    "body": ("torso", None),
    "Head-front-right": ("head", None),
}


def _segment(kind: str, label: str) -> str:
    """Which bone segment a leaf's (nearest) label belongs to within a region."""
    t = (label or "").lower()
    if kind == "arm":
        if any(k in t for k in ("hand", "claw", "finger")):
            return "hand"
        if any(k in t for k in ("lower", "forearm", "cuff", "sleeve")):
            return "lower"
        return "upper"
    if kind == "leg":
        if any(k in t for k in ("foot", "toes", "heel")):
            return "foot"
        if any(k in t for k in ("lower", "shin", "knee")):
            return "lower"
        return "upper"
    return kind  # torso / head: single bone


def _bone_name(kind: str, side: Optional[str], seg: str) -> str:
    if kind in ("torso", "head"):
        return kind
    return f"{side}_{kind[:3]}_{ {'upper':'u','lower':'l','hand':'hand','foot':'foot'}[seg] }".replace(" ", "")


def _classify_leaf(leaf: ET.Element, ancestry: List[str], top: str) -> Optional[str]:
    """Bone name for one drawable leaf, or None if its region is unmapped."""
    if top not in REGION:
        return None
    kind, side = REGION[top]
    # nearest non-empty label from leaf up to (not including) the top group
    near = next((l for l in ancestry if l and l != top), top)
    return _bone_name(kind, side, _segment(kind, near))


def _ancestry(elem: ET.Element, parent: Dict[ET.Element, ET.Element]) -> List[str]:
    out: List[str] = []
    cur: Optional[ET.Element] = elem
    while cur is not None:
        lbl = _label(cur)
        if lbl:
            out.append(lbl)
        cur = parent.get(cur)
    return out  # leaf-first


def _collect() -> Dict[str, List[Tuple[str, ET.Element]]]:
    """Group every drawable leaf under VIEW by bone name -> [(id, elem), ...]."""
    root = ET.fromstring(SVG.read_bytes())
    parent = {c: p for p in root.iter() for c in p}
    bones: Dict[str, List[Tuple[str, ET.Element]]] = {}
    for elem in root.iter():
        if _local(elem.tag) not in ("path", "polygon", "rect", "ellipse", "circle"):
            continue
        anc = _ancestry(elem, parent)
        if VIEW not in anc:
            continue
        top = anc[-1] if anc and anc[-1] != "Layer 1" else (anc[-2] if len(anc) > 1 else "")
        # top group = the child of VIEW; find it explicitly
        top = _top_group(elem, parent)
        bone = _classify_leaf(elem, anc, top)
        if bone is None:
            continue
        bones.setdefault(bone, []).append((elem.get("id", ""), elem))
    return bones


def _top_group(elem: ET.Element, parent: Dict[ET.Element, ET.Element]) -> str:
    """Label of the VIEW's direct child that contains ``elem``."""
    chain = []
    cur: Optional[ET.Element] = elem
    while cur is not None:
        chain.append(cur)
        cur = parent.get(cur)
    # chain is leaf..root; find VIEW then take the element just before it
    for i, node in enumerate(chain):
        if _label(node) == VIEW and i > 0:
            return _label(chain[i - 1]) or ""
    return ""


def _cx(b):  # bbox center x
    return (b[0] + b[2]) / 2.0


def build_skeleton_data() -> dict:
    bones = _collect()
    ids = {name: [i for i, _ in items] for name, items in bones.items()}

    # Rasterize each bone's art once to a full-canvas alpha mask (ref-px). The
    # mask drives joint *x* placement: a joint sits at the limb's true pixel
    # centre near the connection, NOT the average of whole-part bbox centres
    # (which drifts to the wide end — e.g. a thigh bbox includes the hip, so its
    # centre lands at the leg's edge at the knee).
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

    def cx_frac(name: str, f_lo: float, f_hi: float) -> float:
        """Centroid x of a bone's mask within a vertical fraction of its bbox
        (0 = top, 1 = bottom) — the limb centre near one end."""
        a, ox, oy = masks[name]
        h, _w = a.shape
        r0 = int(h * f_lo)
        r1 = max(r0 + 1, int(round(h * f_hi)))
        xs = np.nonzero(a[r0:r1])[1]
        return float(xs.mean()) + ox if xs.size else _cx(bb[name])

    def joint_x(prox: str, dist: str) -> float:
        """x where ``prox`` (above) meets ``dist`` (below): mean of the two
        limb centres measured in the bands closest to the shared joint."""
        return (cx_frac(prox, 0.7, 1.0) + cx_frac(dist, 0.0, 0.3)) / 2.0

    # --- joints (ref-px): x from mask band centres, y from bbox boundaries ---
    J: Dict[str, Tuple[float, float]] = {}
    for side in ("near", "far"):
        u, l, h = f"{side}_arm_u", f"{side}_arm_l", f"{side}_arm_hand"
        if u in bb:
            J[f"{side}_shoulder"] = (cx_frac(u, 0.0, 0.3), bb[u][1])
        if u in bb and l in bb:
            J[f"{side}_elbow"] = (joint_x(u, l), (bb[u][3] + bb[l][1]) / 2)
        if l in bb and h in bb:
            J[f"{side}_wrist"] = (joint_x(l, h), (bb[l][3] + bb[h][1]) / 2)
        if h in bb:
            J[f"{side}_handtip"] = (cx_frac(h, 0.7, 1.0), bb[h][3])
        pu, pl, pf = f"{side}_leg_u", f"{side}_leg_l", f"{side}_leg_foot"
        if pu in bb:
            J[f"{side}_hip"] = (cx_frac(pu, 0.0, 0.3), bb[pu][1])
        if pu in bb and pl in bb:
            J[f"{side}_knee"] = (joint_x(pu, pl), (bb[pu][3] + bb[pl][1]) / 2)
        if pl in bb and pf in bb:
            J[f"{side}_ankle"] = (joint_x(pl, pf), (bb[pl][3] + bb[pf][1]) / 2)
        if pf in bb:
            # toe tip: foot far end horizontally from the ankle x
            fb = bb[pf]
            ax = J.get(f"{side}_ankle", (_cx(fb), fb[3]))[0]
            tipx = fb[0] if abs(fb[0] - ax) > abs(fb[2] - ax) else fb[2]
            J[f"{side}_toe"] = (tipx, (fb[1] + fb[3]) / 2)

    hip_c = (
        (J["near_hip"][0] + J["far_hip"][0]) / 2,
        (J["near_hip"][1] + J["far_hip"][1]) / 2,
    )
    neck = (cx_frac("torso", 0.0, 0.3), bb["torso"][1]) if "torso" in bb else hip_c
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
        ("torso", "pelvis", hip_c, None),
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


def build_doc() -> dict:
    sk = build_skeleton_data()
    K = sk["K"]
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

    svg_rel = Path("../../../../../..") / SVG.relative_to(REPO)
    fr = sk["frame"]
    # Source art is vector, so publish at higher pixel resolution (render_scale)
    # without touching the authored geometry or the in-game display size.
    fr.update(supersample=4, render_scale=RENDER_SCALE)

    # IK rest targets measured from the drawn stance so the default pose matches
    # the artwork (no crossed legs, no bent knees). ankle_h is shared, so each
    # foot's height difference is absorbed by a per-leg rest_lift.
    from authoring.skeleton import two_bone_ik

    cx, gy = fr["center_x"], fr["ground_y"]
    W = sk["world"]
    blen = {b["name"]: b["length"] for b in sk["bones"]}
    ankles = {s: W[f"{s}_leg_foot"]["origin"] for s in ("near", "far")}
    mean_ankle_y = sum(a[1] for a in ankles.values()) / 2.0
    fr["ankle_h"] = round(gy - mean_ankle_y, 3)
    ik_legs = []
    for side in ("near", "far"):
        ax, ay = ankles[side]
        hip = W[f"{side}_leg_u"]["origin"]
        knee_drawn = W[f"{side}_leg_l"]["origin"]
        lu, ll = blen[f"{side}_leg_u"], blen[f"{side}_leg_l"]

        # Pick the bend side whose IK knee matches where the leg is DRAWN, so the
        # rest stance reproduces the artwork (one leg may bend opposite the other
        # in a 3/4 view).
        def ik_knee(bend):
            a1, _ = two_bone_ik(tuple(hip), (ax, ay), lu, ll, bend=bend)
            return (hip[0] + lu * math.cos(math.radians(a1)),
                    hip[1] + lu * math.sin(math.radians(a1)))
        bend = min((1.0, -1.0), key=lambda b: math.dist(ik_knee(b), knee_drawn))

        ik_legs.append({
            "upper": f"{side}_leg_u", "lower": f"{side}_leg_l",
            "foot": f"{side}_leg_foot", "channel_prefix": f"{side}_foot",
            "rest_x": round(ax - cx, 3),
            "rest_lift": round(mean_ankle_y - ay, 3),
            "rest_pitch": round(W[f"{side}_leg_foot"]["angle"], 3),
            "bend": bend,
        })

    return {
        "name": "perfect_cellular_automaton",
        "frame": fr,
        "svg_source": {
            "path": str(svg_rel), "view": VIEW,
            "ref_dpi": REF_DPI, "scale": round(K, 6),
        },
        "palette": {},
        "bones": sk["bones"],
        "parts": parts,
        "ik_legs": ik_legs,
        "clips": {
            "idle": {"loop": True, "frames": 8, "duration_ms": 130, "channels": {
                "torso": {"expr": "1.5*sin(tau*t)"},
                "near_arm_l": {"expr": "3*sin(tau*t)"},
                "far_arm_l": {"expr": "-3*sin(tau*t)"},
            }},
        },
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
    out = Path("/tmp/pca_rig_rest.png")
    frame.save(out)
    print(f"rest frame -> {out}  size={frame.size}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build").set_defaults(fn=cmd_build)
    sub.add_parser("validate").set_defaults(fn=cmd_validate)
    args = ap.parse_args()
    args.fn(args)
