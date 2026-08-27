"""Assemble the Officer's character rig SVG from the authored art source.

The art already separates every limb onto its own layer; what it lacks is the
rig vocabulary. This groups each layer's paths into rigid parts, names the bone
each part rides, and derives the catalog + marker layer from measured joints.
"""
from __future__ import annotations

from pathlib import Path

from lxml import etree

from . import build_catalog as bc
from .annotated_side_rig import install_managed_block

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "assets/officer.svg"
DST = REPO / "ambition_sprite2d_renderer/data/characters/officer/officer.svg"

SVG = "http://www.w3.org/2000/svg"
INK = "http://www.inkscape.org/namespaces/inkscape"
SODIPODI = "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"

# Crown of the head in the source art's own units — the hat is costume and does
# not set his standing height.
HEAD_TOP_Y = 37.835

# Measured off the art at 5x on a labelled unit grid, in the source's own
# millimetre user units.
JOINTS: dict[str, tuple[float, float]] = {
    "waist": (100.0, 137.0),
    "hip_center": (99.5, 147.0),
    "neck": (101.0, 80.0),
    "far_shoulder": (84.0, 95.0),
    "far_elbow": (79.5, 120.0),
    "far_wrist": (72.5, 141.0),
    "far_handtip": (68.0, 161.0),
    "near_shoulder": (114.0, 95.0),
    "near_elbow": (128.5, 120.0),
    "near_wrist": (129.0, 142.0),
    "near_handtip": (131.0, 162.0),
    "far_hip": (88.0, 151.0),
    "far_knee": (89.0, 180.0),
    "far_ankle": (87.0, 215.0),
    "far_toe": (67.0, 227.0),
    "near_hip": (110.0, 151.0),
    "near_knee": (112.0, 181.0),
    "near_ankle": (115.0, 217.0),
    "near_toe": (103.0, 230.0),
    "rig_root": (101.0, 235.0),
}

# (part group id, part name, bone, z, layer, member element ids). z follows the
# source's own paint order, so the rigged file stacks the way the art did.
PARTS: tuple[tuple[str, str, str, int, str, tuple[str, ...]], ...] = (
    ("part-far-leg-u", "far_leg_u", "far_leg_u", 10, "layer8", ("path16041",)),
    ("part-far-foot", "far_foot", "far_leg_foot", 11, "layer8", ("path16051",)),
    ("part-far-leg-l", "far_leg_l", "far_leg_l", 12, "layer8", ("path16047",)),
    ("part-far-arm-u", "far_arm_u", "far_arm_u", 13, "layer6", ("path16057",)),
    ("part-far-arm-l", "far_arm_l", "far_arm_l", 14, "layer6", ("path16059",)),
    ("part-far-sleeve", "far_sleeve", "far_arm_u", 15, "layer6", ("path16055",)),
    ("part-far-hand", "far_hand", "far_arm_hand", 16, "layer6",
     ("path16062", "path1865", "path1867", "path1869", "path1871")),
    ("part-pelvis", "pelvis", "pelvis", 20, "layer10", ("path16043",)),
    ("part-neck", "neck", "torso", 21, "layer9", ("path16027",)),
    ("part-torso", "torso", "torso", 22, "layer9", ("path16031", "path16029", "path584")),
    ("part-near-foot", "near_foot", "near_leg_foot", 30, "layer11", ("path16053",)),
    ("part-near-leg-u", "near_leg_u", "near_leg_u", 31, "layer11", ("path16045",)),
    ("part-near-leg-l", "near_leg_l", "near_leg_l", 32, "layer11", ("path16049",)),
    ("part-near-arm-u", "near_arm_u", "near_arm_u", 40, "layer7", ("path16035",)),
    ("part-near-arm-l", "near_arm_l", "near_arm_l", 41, "layer7", ("path16037",)),
    ("part-near-hand", "near_hand", "near_arm_hand", 42, "layer7",
     ("path16039", "path1859", "path1861", "path1863")),
    ("part-near-sleeve", "near_sleeve", "near_arm_u", 43, "layer7", ("path16033",)),
    ("part-head", "head", "head", 50, "layer4", ()),
    ("part-hat", "hat", "head", 51, "layer12", ()),
    # ⭐ AUTHORED BY HAND, IN THE SOURCE, and that is the whole point of them
    # being here. The back torso and the fist used to be GENERATED into the
    # rigged file after this script had already written it — which meant the
    # one SVG a person would open showed neither, and a regeneration from
    # source would have deleted both. Art belongs in the art file; this table
    # is what carries it across.
    ("part-torso-back", "torso_back", "torso", 22.1, "layer3", ()),
    ("part-fist", "fist", "near_arm_hand", 42.5, "layer13", ()),
)

LABELS = {
    "part-far-leg-u": "Upper Leg - Far", "part-far-leg-l": "Lower Leg - Far",
    "part-far-foot": "Foot - Far", "part-far-arm-u": "Upper Arm - Far",
    "part-far-arm-l": "Lower Arm - Far", "part-far-sleeve": "Sleeve - Far",
    "part-far-hand": "Hand - Far", "part-pelvis": "Pelvis", "part-neck": "Neck",
    "part-torso": "Torso", "part-near-foot": "Foot - Near",
    "part-near-leg-u": "Upper Leg - Near", "part-near-leg-l": "Lower Leg - Near",
    "part-near-arm-u": "Upper Arm - Near", "part-near-arm-l": "Lower Arm - Near",
    "part-near-hand": "Hand - Near", "part-near-sleeve": "Sleeve - Near",
    "part-head": "Head", "part-hat": "Hat",
    "part-torso-back": "Torso (back)", "part-fist": "Fist",
}

#: Parts that are ALTERNATES: drawn, but invisible until a clip asks for them.
#: `(part name, opacity channel, default)`. A channel a clip never mentions
#: reads as its default, so the front torso and the open hand are what a pose
#: gets for free and the swap is the thing that must be stated.
ALTERNATES = {
    "torso_back": ("torso_back_vis", 0.0),
    # THE FIST IS A HAND SWAP, not an extra hand. It shares
    # `near_arm_hand` with `near_hand`, so exactly one of the two is up in any
    # frame — see `hand_vis` on the open hand below.
    "fist": ("fist_vis", 0.0),
    "near_hand": ("hand_vis", 1.0),
}



def main() -> None:
    tree = etree.parse(str(SRC))
    root = tree.getroot()
    by_id = {e.get("id"): e for e in root.iter() if e.get("id")}

    view = by_id["layer2"]
    # Concept-art tracing references point outside the package; they are the
    # drawing's scaffolding, not the rig's.
    root.remove(by_id["layer1"])
    # The campaign hat is his identity, not an alternate: it joins the character
    # layer so it shares the view's scale and paints with the rest of him.
    hat_layer = by_id["layer12"]
    root.remove(hat_layer)
    hat_layer.set("style", "display:inline")
    view.append(hat_layer)
    # `Rest` is an empty authoring layer with nothing to rig.
    view.remove(by_id["layer5"])
    # The hand-authored alternates join the character layer for the same reason
    # the hat does: they have to share the view's scale, or a torso drawn at
    # millimetre scale lands somewhere else entirely once the view is scaled
    # into library units.
    for alternate_layer in ("layer3", "layer13"):
        layer = by_id[alternate_layer]
        if layer.getparent() is not view:
            layer.getparent().remove(layer)
            layer.set("style", "display:inline")
            view.append(layer)

    for group_id, _name, bone, z, layer_id, members in PARTS:
        layer = by_id[layer_id]
        group = etree.SubElement(layer, f"{{{SVG}}}g")
        group.set("id", group_id)
        group.set("data-rig-bone", bone)
        group.set("data-rig-part", _name)
        group.set("data-rig-z", str(z))
        group.set(f"{{{INK}}}label", LABELS[group_id])
        if _name in ALTERNATES:
            channel, default = ALTERNATES[_name]
            group.set("data-rig-opacity", channel)
            group.set("data-rig-opacity-default", str(default))
        # An empty member list means "everything this layer already holds".
        elements = [by_id[eid] for eid in members] if members else [
            child for child in layer if child is not group
        ]
        for element in elements:
            element.getparent().remove(element)
            group.append(element)
        by_id[group_id] = group

    joints = dict(JOINTS)
    # ⛔ THE SHARED LIBRARY'S TRANSLATIONS ARE ABSOLUTE. `space.linear_unit` is
    # "rig_user_unit", so a dash authored as "-276 units left" means units of
    # the rig reading it, and this art is drawn in millimetres. Standing height
    # is the normalization that keeps the roster one size on screen: the art
    # view carries the ratio and every marker is authored in library space.
    scale = round(671.43 / (joints["rig_root"][1] - HEAD_TOP_Y), 4)
    joints = {name: (x * scale, y * scale) for name, (x, y) in joints.items()}
    view.set("transform", f"scale({scale})")
    root.set("viewBox", f"0 0 {210 * scale:.4f} {297 * scale:.4f}")

    parts = bc.collect_parts(root, "layer2")
    # ⛔⛔ AN ALTERNATE BINDS WHERE THE PART IT REPLACES BINDS. `collect_parts`
    # gives every part its OWN pivot, derived from that art's own geometry —
    # right for a limb, and wrong for a swap: the back torso then hangs off its
    # own centroid instead of the trunk's, which measured as a shirt floating a
    # head's width to the side of the man wearing it. Same for the fist, which
    # has to arrive exactly where the open hand left.
    base_of = {"torso_back": "torso", "fist": "near_hand"}
    by_part = {part["name"]: part for part in parts}
    for alternate, base in base_of.items():
        if alternate in by_part and base in by_part:
            for key in ("pivot", "bind_angle"):
                if key in by_part[base]:
                    by_part[alternate][key] = by_part[base][key]
    meta_text, markers_text = bc.build(
        view_id="layer2",
        source_layer="layer2",
        source_label="Character - Officer",
        facing="west",
        catalog_view="side",
        joints=joints,
        parts=parts,
    )

    install_managed_block(root, meta_text, markers_text)
    root.set(f"{{{SODIPODI}}}docname", "officer.svg")

    DST.parent.mkdir(parents=True, exist_ok=True)
    tree.write(str(DST), encoding="UTF-8", xml_declaration=True)
    print(f"wrote {DST}")
    print(f"scale={scale} parts={len(parts)} joints={len(joints)}")


if __name__ == "__main__":
    main()
