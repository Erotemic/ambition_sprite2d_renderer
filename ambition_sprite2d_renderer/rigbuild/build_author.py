"""Assemble the Author's character rig SVG from the authored art source."""
from __future__ import annotations

from pathlib import Path

from lxml import etree

from . import build_catalog as bc
from . import sword_author

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "assets/author-rig-labels-joints.svg"
DST = REPO / "ambition_sprite2d_renderer/data/characters/author/author.svg"

# Crown of the head in the source art's own units, measured from the rendered
# alpha bounds of the view; the standing height it anchors is what puts this
# rig into the shared motion library's scale.
HEAD_TOP_Y = 79.904

SVG = "http://www.w3.org/2000/svg"
INK = "http://www.inkscape.org/namespaces/inkscape"
NS = {"svg": SVG, "inkscape": INK}


def frag(text: str):
    wrapper = f'<svg xmlns="{SVG}" xmlns:inkscape="{INK}">{text}</svg>'
    return etree.fromstring(wrapper.encode())[0]


def main() -> None:
    tree = etree.parse(str(SRC))
    root = tree.getroot()
    by_id = {e.get("id"): e for e in root.iter() if e.get("id")}

    joints = bc.collect_joints(root, "rig-joints")

    # The two joints the art never needed but the skeleton does: the pelvis'
    # own pivot, and the ground point the whole rig is anchored to.
    hips = (joints["far_hip"], joints["near_hip"])
    waist = joints["waist"]
    joints["hip_center"] = (
        round((hips[0][0] + hips[1][0]) / 2.0, 3),
        round(waist[1] + 0.7 * ((hips[0][1] + hips[1][1]) / 2.0 - waist[1]), 3),
    )
    joints["rig_root"] = (90.75, 230.5)

    # ⛔ THE SHARED LIBRARY'S TRANSLATIONS ARE ABSOLUTE. `space.linear_unit` is
    # "rig_user_unit", so a dash authored as "-276 units left" means units of
    # the rig reading it. Jon's art is authored in millimetres (1 user unit =
    # 1 mm, 150.6 units tall); the library was authored against a rig 671.4
    # units tall. Bound unscaled, his dash_attack threw him 227px out of a
    # 128px frame. Standing height is the normalization that keeps the roster
    # one size on screen, so the art view carries the ratio and every marker is
    # authored in the library's space.
    scale = round(671.43 / (joints["rig_root"][1] - HEAD_TOP_Y), 4)
    joints = {name: (x * scale, y * scale) for name, (x, y) in joints.items()}
    view_scale = scale

    # The sword: a rigid part carried by the near hand, drawn along that bone's
    # axis so an authored swing points the blade where the hand points.
    view = by_id["view-author-side-west"]
    sword = etree.SubElement(view, f"{{{SVG}}}g")
    sword.set("id", "part-near-sword")
    sword.set("data-rig-bone", "near_arm_hand")
    sword.set("data-rig-part", "sword")
    sword.set("data-rig-z", "61")
    sword.set(f"{{{INK}}}label", "Sword")
    sword.set(f"{{{INK}}}groupmode", "layer")
    sword.text = "\n        "
    for eid, d, style in sword_author.PATHS:
        path = etree.SubElement(sword, f"{{{SVG}}}path")
        path.set("id", eid)
        path.set("style", style)
        path.set("d", d)
        path.tail = "\n        "
    sword[-1].tail = "\n      "
    sword.tail = "\n    "
    # Paint order in the source follows the catalog's z, so the file reads the
    # way it renders.
    view.remove(sword)
    view.insert(list(view).index(by_id["part-near-hand"]) + 1, sword)

    view.set("transform", f"scale({view_scale})")
    root.set("viewBox", f"0 0 {210 * view_scale:.4f} {297 * view_scale:.4f}")

    parts = bc.collect_parts(root, "view-author-side-west")

    meta_text, markers_text = bc.build(
        view_id="view-author-side-west",
        source_layer="view-author-side-west",
        source_label="Author - Side West",
        facing="west",
        catalog_view="side",
        joints=joints,
        parts=parts,
    )

    # The authored joints move out of the art view and become the canonical
    # marker layer: one rest authority, still editable in Inkscape.
    by_id["rig-joints"].getparent().remove(by_id["rig-joints"])

    # One managed block, laid out the way `svg_rig_tool` expects to find it:
    # BEGIN, the catalog, the editor marker layer, END.
    for node in list(root):
        if isinstance(node.tag, type(etree.Comment)) and "AMBITION SVG RIG v1" in (node.text or ""):
            root.remove(node)
    old_meta = next((e for e in root if e.get("id") == "ambition-rig-metadata"), None)
    if old_meta is not None:
        root.remove(old_meta)
    begin = etree.Comment(" BEGIN AMBITION SVG RIG v1 ")
    begin.tail = "\n"
    root.append(begin)
    meta = frag(meta_text)
    meta.tail = "\n"
    root.append(meta)
    markers = frag(markers_text)
    markers.tail = "\n"
    root.append(markers)
    end = etree.Comment(" END AMBITION SVG RIG v1 ")
    end.tail = "\n"
    root.append(end)

    root.set("sodipodi:docname".replace("sodipodi:", f"{{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}}"), "author.svg")
    DST.parent.mkdir(parents=True, exist_ok=True)
    tree.write(str(DST), encoding="UTF-8", xml_declaration=True)
    print(f"wrote {DST}")
    print(f"parts={len(parts)} joints={len(joints)}")


if __name__ == "__main__":
    main()
