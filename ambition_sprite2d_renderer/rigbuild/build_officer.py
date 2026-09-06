"""Assemble the Officer's character rig SVG from the authored art source.

The art already separates every limb onto its own layer; what it lacks is the
rig vocabulary. This groups each layer's paths into rigid parts, names the bone
each part rides, and derives the catalog + marker layer from measured joints.
"""
from __future__ import annotations

from pathlib import Path

from lxml import etree

from . import build_catalog as bc
from . import sidearm_author
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

#: Art this builder AUTHORS rather than carries across, because no layer in the
#: drawing holds it yet. ⚠ Same stopgap status as `humanoid_torsos`' shell: the
#: moment a person draws either of these, it moves to the art file and this
#: table carries it instead.
#: `(group id, part, bone, z, label, paths)`
GENERATED: tuple[tuple[str, str, str, float, str, list], ...] = (
    # The holster is PERMANENT: a drawn gun that appears from nowhere is worse
    # than no gun, so the belt carries the reason he is armed in every frame.
    # In front of the near thigh, behind the near arm, the way it hangs.
    ("part-holster", "holster", "pelvis", 32.5, "Holster",
     sidearm_author.HOLSTER_PATHS),
    # The pistol is an ALTERNATE, behind the fist so the grip sits INSIDE the
    # hand rather than on top of it.
    ("part-sidearm", "sidearm", "near_arm_hand", 42.4, "Sidearm",
     sidearm_author.PATHS),
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

#: ⛔⛔ THE ALTERNATES ARE DRAWN BESIDE HIM, NOT ON HIM. `Torso-Back-Pivoted` sits
#: off his right shoulder and `Fist` off his left hip -- an exploded authoring
#: layout, which is fine for drawing and fatal for a swap: the moment the swap
#: actually worked, his smash published a shirt hanging in the air a head's width
#: away and a bare chest under his sleeves.
#:
#: Measured alpha bounds, in his own art millimetres: `(alternate, base, fit)`.
#: The alternate is moved so its box lands on the box of the part it REPLACES.
#:
#: ⛔ A TRUNK IN A SWAP SET MUST KEEP THE TRUNK'S WIDTH, so `torso_back` is fitted
#: to the front torso's box rather than merely centred on it -- his hand-drawn
#: back is 87% as wide, and centred alone it left the shoulders a hairline short
#: of the sleeves, which publishes as an arm that has come off.
#:
#: ⛔ AND ITS HEM MUST REACH THE PELVIS. Fitted to the front torso's box exactly,
#: his back separated at the WAIST rather than the shoulder: the trunk rotates in
#: a smash and a hem that only just met the belt at rest swings clear of it. The
#: target box is the front torso's, lengthened to tuck behind.
#:
#: ⛔ AND A HAND IN ONE MUST NOT. A drawn fist is legitimately smaller than an
#: open hand with the fingers spread; fitted to that box it publishes a mitt. It
#: is centred and left at its own size.
PLACEMENT: dict[str, tuple[tuple[float, float, float, float],
                            tuple[float, float, float, float], bool]] = {
    "torso_back": ((148.88, 22.0, 200.75, 85.0), (78.0, 78.75, 123.12, 149.0), True),
    "fist": ((34.5, 111.5, 49.0, 131.5), (120.38, 141.88, 137.62, 164.0), False),
}


def placement_transform(source, target, fit: bool) -> str:
    """SVG transform putting `source`'s box onto `target`'s."""
    sx0, sy0, sx1, sy1 = source
    tx0, ty0, tx1, ty1 = target
    scx, scy = (sx0 + sx1) / 2.0, (sy0 + sy1) / 2.0
    tcx, tcy = (tx0 + tx1) / 2.0, (ty0 + ty1) / 2.0
    if not fit:
        return f"translate({tcx - scx:.4f},{tcy - scy:.4f})"
    kx = (tx1 - tx0) / (sx1 - sx0)
    ky = (ty1 - ty0) / (sy1 - sy0)
    return (f"translate({tcx:.4f},{tcy:.4f}) scale({kx:.6f},{ky:.6f}) "
            f"translate({-scx:.4f},{-scy:.4f})")

#: Parts that are ALTERNATES: drawn, but invisible until a clip asks for them.
#: `(part name, opacity channel, default)`. A channel a clip never mentions
#: reads as its default, so the front torso and the open hand are what a pose
#: gets for free and the swap is the thing that must be stated.
ALTERNATES = {
    "torso_back": ("torso_back_vis", 0.0),
    # ⛔ HE IS NOT DRAWN HOLDING IT. The pistol is in the holster until a clip
    # says otherwise, so its channel defaults to 0 exactly as the fist's does --
    # and `shoot` is the only row that raises it.
    "sidearm": ("sidearm_vis", 0.0),
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

    # The authored parts join the character layer so they share the view's
    # scale; a pistol drawn at millimetre scale lands somewhere else entirely
    # once the view is scaled into library units.
    for group_id, name, bone, z, label, paths in GENERATED:
        group = etree.SubElement(view, f"{{{SVG}}}g")
        group.set("id", group_id)
        group.set("data-rig-bone", bone)
        group.set("data-rig-part", name)
        group.set("data-rig-z", str(z))
        group.set(f"{{{INK}}}label", label)
        group.set(f"{{{INK}}}groupmode", "layer")
        if name in ALTERNATES:
            channel, default = ALTERNATES[name]
            group.set("data-rig-opacity", channel)
            group.set("data-rig-opacity-default", str(default))
        for eid, d, style in paths:
            path = etree.SubElement(group, f"{{{SVG}}}path")
            path.set("id", eid)
            path.set("style", style)
            path.set("d", d)
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

    # ⛔⛔ AN ALTERNATE ARRIVES WHERE THE PART IT REPLACES LEFT. Both alternates
    # share their base's BIND PIVOT already -- `build_catalog` seeds every pivot
    # at the bone origin and both ride `torso` / `near_arm_hand` -- so what was
    # missing was never the pivot, it was the ART's position. (The code that used
    # to sit here copied `pivot` and `bind_angle` between `collect_parts` dicts,
    # which carry neither key: it read as the fix and did nothing for as long as
    # the alternates drew unconditionally and nobody could see the swap.)
    for name, (source, target, fit) in PLACEMENT.items():
        group = next((g for g in view.iter()
                      if g.get("data-rig-part") == name), None)
        if group is None:
            continue
        move = placement_transform(source, target, fit)
        existing = group.get("transform")
        group.set("transform", f"{move} {existing}" if existing else move)

    parts = bc.collect_parts(root, "layer2")
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
