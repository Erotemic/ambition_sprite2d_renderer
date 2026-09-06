"""Build a rigged SVG from art that ALREADY CARRIES the rig vocabulary.

The Officer's builder has to group loose paths and carry a joint table in
Python because his art file knows nothing about rigs. An annotated source
knows everything: each part group declares its ``data-rig-part`` /
``data-rig-bone`` / ``data-rig-z``, and a ``rig-joints`` layer holds one circle
per measured joint. All that is left is what a skeleton needs and a drawing
cannot state -- the pelvis' own pivot, the ground point, and the scale that puts
this character into the shared motion library's units.

⭐ THE SOURCE IS THE ART FILE. Nothing here invents geometry; it derives.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from lxml import etree

from . import build_catalog as bc

SVG = "http://www.w3.org/2000/svg"
INK = "http://www.inkscape.org/namespaces/inkscape"
SODIPODI = "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"

#: Standing height every character in the shared humanoid library is measured
#: against. ⛔ THE LIBRARY'S TRANSLATIONS ARE ABSOLUTE: `space.linear_unit` is
#: "rig_user_unit", so a dash authored as "-276 units left" means units of the
#: rig reading it. This art is drawn in millimetres; without the normalization a
#: dash throws the character clean out of the frame.
LIBRARY_STANDING_HEIGHT = 671.43


@dataclass(frozen=True)
class SideRigSpec:
    """One hand-drawn character's art, and the three facts the art cannot state."""

    name: str
    view_id: str
    source_label: str
    facing: str
    #: Crown of the SKULL in the source's own units — costume above it (a hat, a
    #: piled-up bun) is identity, not standing height, so the roster reads one
    #: size on screen whatever a character wears on their head.
    head_top_y: float
    #: Ground point under the character, in the source's own units.
    rig_root: tuple[float, float]
    #: Layers that are drawing scaffolding rather than the character.
    drop_layers: tuple[str, ...] = ()


def frag(text: str):
    wrapper = f'<svg xmlns="{SVG}" xmlns:inkscape="{INK}">{text}</svg>'
    return etree.fromstring(wrapper.encode())[0]


def install_managed_block(root, meta_text: str, markers_text: str) -> None:
    """Replace the managed rig block, laid out the way `svg_rig_tool` finds it.

    BEGIN comment, the catalog, the editor marker layer, END comment.
    """
    for node in list(root):
        if isinstance(node.tag, type(etree.Comment)) and "AMBITION SVG RIG v1" in (node.text or ""):
            root.remove(node)
    old_meta = next((e for e in root if e.get("id") == "ambition-rig-metadata"), None)
    if old_meta is not None:
        root.remove(old_meta)
    old_markers = next((e for e in root if e.get("id") == "ambition-rig-markers"), None)
    if old_markers is not None:
        root.remove(old_markers)
    for node in (
        etree.Comment(" BEGIN AMBITION SVG RIG v1 "),
        frag(meta_text),
        frag(markers_text),
        etree.Comment(" END AMBITION SVG RIG v1 "),
    ):
        node.tail = "\n"
        root.append(node)


def build(spec: SideRigSpec, *, repo: Path) -> Path:
    src = repo / "assets" / f"{spec.name}.svg"
    dst = repo / "ambition_sprite2d_renderer" / "data" / "characters" / spec.name / f"{spec.name}.svg"

    tree = etree.parse(str(src))
    root = tree.getroot()
    by_id = {e.get("id"): e for e in root.iter() if e.get("id")}

    for layer_id in spec.drop_layers:
        layer = by_id.get(layer_id)
        if layer is not None:
            layer.getparent().remove(layer)

    joints = bc.collect_joints(root, "rig-joints")

    # The two joints the drawing never needed but the skeleton does: the pelvis'
    # own pivot, and the ground point the whole rig hangs from. The pelvis sits
    # most of the way from the waist down to the hips, so a crouch folds at the
    # belt rather than at the navel.
    far_hip, near_hip = joints["far_hip"], joints["near_hip"]
    waist_y = joints["waist"][1]
    hip_y = (far_hip[1] + near_hip[1]) / 2.0
    joints["hip_center"] = (
        round((far_hip[0] + near_hip[0]) / 2.0, 3),
        round(waist_y + 0.7 * (hip_y - waist_y), 3),
    )
    joints["rig_root"] = spec.rig_root

    scale = round(LIBRARY_STANDING_HEIGHT / (spec.rig_root[1] - spec.head_top_y), 4)
    joints = {name: (x * scale, y * scale) for name, (x, y) in joints.items()}

    view = by_id[spec.view_id]
    view.set("transform", f"scale({scale})")
    root.set("viewBox", f"0 0 {210 * scale:.4f} {297 * scale:.4f}")

    parts = bc.collect_parts(root, spec.view_id)

    meta_text, markers_text = bc.build(
        view_id=spec.view_id,
        source_layer=spec.view_id,
        source_label=spec.source_label,
        facing=spec.facing,
        catalog_view="side",
        joints=joints,
        parts=parts,
    )

    # The authored joints become the canonical marker layer: one rest authority,
    # still editable in Inkscape, and no second copy to drift from it.
    by_id["rig-joints"].getparent().remove(by_id["rig-joints"])

    install_managed_block(root, meta_text, markers_text)
    root.set(f"{{{SODIPODI}}}docname", f"{spec.name}.svg")

    dst.parent.mkdir(parents=True, exist_ok=True)
    tree.write(str(dst), encoding="UTF-8", xml_declaration=True)
    print(f"wrote {dst}")
    print(f"scale={scale} parts={len(parts)} joints={len(joints)}")
    return dst
