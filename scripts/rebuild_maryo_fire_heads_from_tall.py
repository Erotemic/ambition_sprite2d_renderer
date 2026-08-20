#!/usr/bin/env python3
"""Normalize Fire Mary-O front head/body/arms against Tall Mary-O.

Policy:
* Fire front head uses the tall front head geometry with fire hat recolor/wings.
* The assembled fire front head is algebraically aligned to the tall front head.
* Fire front arms use the exact tall front arm geometry and placement, recolored
  to the fire palette, plus one centered shoulder spike per arm.
* Fire front arm/head rig pivots match the corresponding tall front pivots.
* Fire front torso clones the working fire side torso.

No raster or image-generation operations are used to modify the SVG.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
import re

from lxml import etree

from svg_geometry_tools import (
    INK_LABEL, SVG_NS, XLINK_HREF, identity, inverse, matrix_text,
    multiply, parse_transform, element_by_id,
)

XLINK_NS = "http://www.w3.org/1999/xlink"
INK_NS = "http://www.inkscape.org/namespaces/inkscape"

FIRE_COLORS = {
    "arm": "#f27038",
    "wrist": "#ffc940",
    "glove": "#fffbf6",
    "shoulder": "#fffaef",
}


def q(ns: str, tag: str) -> str:
    return f"{{{ns}}}{tag}"


def make_use(id_: str, label: str, href: str, transform: str | None = None):
    elem = etree.Element(q(SVG_NS, "use"))
    elem.set("id", id_)
    elem.set(INK_LABEL, label)
    elem.set("href", href)
    elem.set(XLINK_HREF, href)
    if transform:
        elem.set("transform", transform)
    return elem


def rename_ids(elem, prefix: str) -> None:
    if elem.get("id"):
        elem.set("id", prefix + elem.get("id"))
    for child in elem:
        if isinstance(child.tag, str):
            rename_ids(child, prefix)


def replace_children(elem, children) -> None:
    for child in list(elem):
        elem.remove(child)
    for child in children:
        elem.append(child)


def copy_pivot(root, tall_prefix: str, fire_prefix: str) -> None:
    tall_pivot = element_by_id(root, tall_prefix + "_pivot")
    fire_pivot = element_by_id(root, fire_prefix + "_pivot")
    for attr in ("cx", "cy"):
        fire_pivot.set(attr, tall_pivot.get(attr))
    tall_cross = element_by_id(root, tall_prefix + "_pivot_cross")
    fire_cross = element_by_id(root, fire_prefix + "_pivot_cross")
    fire_cross.set("d", tall_cross.get("d"))


def rebuild_fire_front_head(root) -> None:
    fire = element_by_id(root, "maryo_authoring_fire_front_head")
    tall_core = element_by_id(root, "maryo_component_normal_front_head")
    tall_hat = element_by_id(root, "maryo_component_normal_front_head_hat_dome")
    tall_star = element_by_id(root, "maryo_primitive_big_front_hat_star")
    tall_ribbons = element_by_id(root, "maryo_primitive_big_front_ribbons")
    fire_wings = deepcopy(element_by_id(root, "maryo_primitive_fire_front_extras"))

    base_clone_transform = "translate(320.5579,59.73933)"
    tall_outer_transform = element_by_id(root, "maryo_authoring_tall_front_head").get("transform")

    base = make_use(
        "maryo_fire_front_tall_head_clone", "Tall Front Head Clone",
        "#maryo_authoring_tall_front_head", base_clone_transform,
    )

    overlay = etree.Element(q(SVG_NS, "g"))
    overlay.set("id", "maryo_fire_front_hat_overlay_layer")
    overlay.set(INK_LABEL, "Fire Front Hat Overlay Layer")
    overlay.set("transform", f"{base_clone_transform} {tall_outer_transform} {tall_core.get('transform')}")
    hat = deepcopy(tall_hat)
    rename_ids(hat, "maryo_fire_front_overlay_")
    hat.set(INK_LABEL, "Fire Front Hat Dome Overlay")
    hat.set("color", "#ec583a")
    trim_id = "maryo_fire_front_overlay_maryo_component_normal_front_head_hat_trim"
    trim = hat.xpath(f'.//*[@id="{trim_id}"]')
    if trim:
        trim[0].set("color", "#ffdb6c")
        trim[0].set(INK_LABEL, "Fire Front Hat Trim Overlay")
    overlay.append(hat)

    top = etree.Element(q(SVG_NS, "g"))
    top.set("id", "maryo_fire_front_hat_top_details")
    top.set(INK_LABEL, "Fire Front Hat Top Details")
    top.set("transform", f"{base_clone_transform} {tall_outer_transform}")
    star = deepcopy(tall_star); rename_ids(star, "maryo_fire_front_top_")
    star.set(INK_LABEL, "Fire Front Top Hat Star Clone")
    ribbons = deepcopy(tall_ribbons); rename_ids(ribbons, "maryo_fire_front_top_")
    ribbons.set(INK_LABEL, "Fire Front Top Ribbon Clone")
    top.extend([star, ribbons])

    replace_children(fire, [base, overlay, fire_wings, top])


def align_assembled_fire_head(root) -> float:
    tall_head = element_by_id(root, "maryo_tall_front_head")
    fire_head = element_by_id(root, "maryo_fire_front_head")
    tall_art = element_by_id(root, "maryo_tall_front_head_art")
    fire_art = element_by_id(root, "maryo_fire_front_head_art")
    tall_source = next(c for c in tall_art if etree.QName(c).localname == "g")
    fire_source = next(c for c in fire_art if etree.QName(c).localname == "g")
    tall_use = next(c for c in tall_source if etree.QName(c).localname == "use")
    fire_use = next(c for c in fire_source if etree.QName(c).localname == "use")
    tall_authoring = element_by_id(root, "maryo_authoring_tall_front_head")
    fire_authoring = element_by_id(root, "maryo_authoring_fire_front_head")
    fire_clone = element_by_id(root, "maryo_fire_front_tall_head_clone")

    prefix_tall = multiply(parse_transform(tall_head.get("transform")), parse_transform(tall_art.get("transform")))
    prefix_tall = multiply(prefix_tall, parse_transform(tall_source.get("transform")))
    target = multiply(prefix_tall, parse_transform(tall_use.get("transform")))
    target = multiply(target, parse_transform(tall_authoring.get("transform")))

    prefix_fire = multiply(parse_transform(fire_head.get("transform")), parse_transform(fire_art.get("transform")))
    prefix_fire = multiply(prefix_fire, parse_transform(fire_source.get("transform")))
    suffix_fire = multiply(parse_transform(fire_authoring.get("transform")), parse_transform(fire_clone.get("transform")))
    suffix_fire = multiply(suffix_fire, parse_transform(tall_authoring.get("transform")))

    solved = multiply(multiply(inverse(prefix_fire), target), inverse(suffix_fire))
    fire_use.set("transform", matrix_text(solved))

    actual = multiply(prefix_fire, solved)
    actual = multiply(actual, suffix_fire)
    delta = max(abs(a-b) for a,b in zip(actual,target))
    copy_pivot(root, "maryo_tall_front_head", "maryo_fire_front_head")
    return delta


_SHOULDER_RE = re.compile(
    r"m\s*([-+0-9.eE]+)[, ]+([-+0-9.eE]+)\s+a\s*([-+0-9.eE]+)[, ]+([-+0-9.eE]+)"
)


def shoulder_spike_d(shoulder_d: str) -> str:
    match = _SHOULDER_RE.search(shoulder_d)
    if not match:
        raise ValueError(f"unexpected shoulder path: {shoulder_d}")
    left_x, center_y, rx, ry = map(float, match.groups())
    center_x = left_x + rx
    base_y = center_y - ry + (2.0 / 3.0)
    apex_y = base_y - 4.0
    return (
        f"M {center_x-2:.8f},{base_y:.8f} "
        f"L {center_x:.8f},{apex_y:.8f} "
        f"L {center_x+2:.8f},{base_y:.8f} Z"
    )


def materialize_fire_arm(root, side: str) -> None:
    # side is "right" => tall far arm, "left" => tall near arm.
    if side == "right":
        tall_front_art_id = "maryo_tall_front_character_right_arm_art"
        fire_front_art_id = "maryo_fire_front_character_right_arm_art"
        source_id = "maryo_tall_side_far_arm_art"
        common_id = "maryo_fire_front_character_right_arm_common"
        fire_prefix = "maryo_fire_front_right_norm_"
        tall_part_prefix = "maryo_tall_front_character_right_arm"
        fire_part_prefix = "maryo_fire_front_character_right_arm"
    else:
        tall_front_art_id = "maryo_tall_front_character_left_arm_art"
        fire_front_art_id = "maryo_fire_front_character_left_arm_art"
        source_id = "maryo_tall_side_near_arm_art"
        common_id = "maryo_fire_front_character_left_arm_common"
        fire_prefix = "maryo_fire_front_left_norm_"
        tall_part_prefix = "maryo_tall_front_character_left_arm"
        fire_part_prefix = "maryo_fire_front_character_left_arm"

    tall_front_art = element_by_id(root, tall_front_art_id)
    tall_ref = next(c for c in tall_front_art if etree.QName(c).localname == "use")
    source = element_by_id(root, source_id)
    common = etree.Element(q(SVG_NS, "g"))
    common.set("id", common_id)
    common.set(INK_LABEL, f"Normalized Fire Front {side.title()} Arm Common Geometry")
    combined = multiply(parse_transform(tall_ref.get("transform")), parse_transform(source.get("transform")))
    if combined != identity():
        common.set("transform", matrix_text(combined))

    copied_children = [deepcopy(c) for c in source]
    for child in copied_children:
        rename_ids(child, fire_prefix)
        common.append(child)

    # Recolor exact tall geometry into the fire palette.
    shoulder = None
    for path in common.xpath('.//*[local-name()="path"]'):
        label = (path.get(INK_LABEL) or "").strip().lower()
        if label in FIRE_COLORS:
            path.set("fill", FIRE_COLORS[label])
        if label == "shoulder":
            shoulder = path
    if shoulder is None:
        raise RuntimeError(f"no shoulder path found for {side} arm")

    # Keep the fire-only spike outside the common-geometry group so the common
    # subtree remains exactly bbox/geometry-compatible with Tall Mary-O.
    shoulder_parent = shoulder.getparent()
    ancestor_chain = []
    cur = shoulder_parent
    while cur is not None and cur is not common:
        ancestor_chain.append(cur)
        cur = cur.getparent()
    if cur is not common:
        raise RuntimeError("shoulder is not under normalized common-arm group")
    spike_matrix = parse_transform(common.get("transform"))
    for ancestor in reversed(ancestor_chain):
        spike_matrix = multiply(spike_matrix, parse_transform(ancestor.get("transform")))

    spike = etree.Element(q(SVG_NS, "path"))
    spike.set("id", fire_prefix + "shoulder_spike")
    spike.set(INK_LABEL, "sleeve-spike")
    spike.set("d", shoulder_spike_d(shoulder.get("d")))
    spike.set("transform", matrix_text(spike_matrix))
    spike.set("fill", "#ffc940")
    spike.set("stroke", "#1c1613")
    spike.set("stroke-width", "1")
    spike.set("stroke-linejoin", "miter")
    spike.set("stroke-linecap", "square")
    spike.set("stroke-miterlimit", "4")

    fire_front_art = element_by_id(root, fire_front_art_id)
    replace_children(fire_front_art, [common, spike])
    copy_pivot(root, tall_part_prefix, fire_part_prefix)


def restore_fire_front_torso(root) -> None:
    art = element_by_id(root, "maryo_fire_front_torso_art")
    replace_children(art, [make_use(
        "maryo_fire_front_torso_clone_from_side", "Clone of Fire Side Torso",
        "#maryo_fire_side_torso",
    )])


def normalize(input_svg: Path, output_svg: Path) -> float:
    doc = etree.parse(str(input_svg))
    root = doc.getroot()
    rebuild_fire_front_head(root)
    restore_fire_front_torso(root)
    materialize_fire_arm(root, "right")
    materialize_fire_arm(root, "left")
    head_error = align_assembled_fire_head(root)
    doc.write(str(output_svg), encoding="utf-8", xml_declaration=True)
    return head_error


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_svg", type=Path)
    parser.add_argument("output_svg", nargs="?", type=Path)
    args = parser.parse_args()
    output = args.output_svg or args.input_svg
    error = normalize(args.input_svg, output)
    print(output)
    print(f"assembled head matrix max error: {error:.3g}")


if __name__ == "__main__":
    main()
