from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

# ⚠ the guard every other SVG-rendering suite here opens with: this one needs
# native resvg-py, and without it the whole file RAISED instead of skipping.
pytest.importorskip("resvg_py")

from PIL import ImageChops

from ambition_sprite2d_renderer.targets.characters import mary_o_v2, mary_o_v2_svg_poc
from ambition_sprite2d_renderer.targets.characters._mary_o_v2_model import (
    FIRE_FORM,
    SHORT_FORM,
    SHORT_POSES,
    TALL_FORM,
    TALL_LIKE_POSES,
)
from ambition_sprite2d_renderer.targets.characters._mary_o_v2_svg_poc import (
    INK_LABEL,
    build_rig_document,
    render_pose_with_doc,
)


ASSET = Path(mary_o_v2_svg_poc.ASSET_PATH)


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _docs() -> dict[str, object]:
    docs = {}
    for form in (SHORT_FORM, TALL_FORM, FIRE_FORM):
        docs[form.target_name] = build_rig_document(ASSET, form, "side")
        docs[f"{form.target_name}:front"] = build_rig_document(ASSET, form, "front")
    return docs


def test_exporter_can_emit_a_fresh_procedural_seed(tmp_path: Path) -> None:
    # The exporter is an explicit bootstrap/reset tool. The checked-in SVG is
    # intentionally NOT compared byte-for-byte so manual Inkscape edits become
    # authoritative without turning the test suite red.
    path = mary_o_v2.export_svg_poc_source(tmp_path / "mary_o_seed.svg")
    text = path.read_text(encoding="utf8")
    assert "Mary-O - Short Side" in text
    assert "Mary-O - Short Front" in text
    assert "data-rig-bone" in text
    assert "rotated_arm" not in text
    assert "rotated_leg" not in text
    root = ET.fromstring(path.read_bytes())
    components = next(node for node in root if node.get("id") == "maryo_primitive_components")
    assert len(list(components)) == 13
    ids = {node.get("id") or "" for node in components}
    assert "maryo_component_normal_side_head" in ids
    assert "maryo_component_normal_front_head" in ids
    assert "maryo_component_shared_front_death_expression" in ids
    assert "maryo_primitive_fire_side_hat_wing" in ids
    assert not any("torso" in item or "_arm" in item or "_leg" in item or "wings" in item for item in ids)


def test_svg_has_side_and_front_component_libraries_for_every_form() -> None:
    root = ET.fromstring(ASSET.read_bytes())
    labels = {group.get(INK_LABEL): group for group in root if group.get(INK_LABEL)}
    assert set(labels) == {
        "Mary-O - Authoring Components",
        "Mary-O - Component Assemblies",
        "Mary-O - Short Side",
        "Mary-O - Short Front",
        "Mary-O - Tall Side",
        "Mary-O - Tall Front",
        "Mary-O - Fire Side",
        "Mary-O - Fire Front",
    }

    primitives = labels["Mary-O - Authoring Components"]
    assemblies = labels["Mary-O - Component Assemblies"]
    primitive_ids = {node.get("id") or "" for node in primitives.iter()}
    assembly_ids = {node.get("id") or "" for node in assemblies.iter()}
    assert {
        "maryo_component_normal_side_head",
        "maryo_component_normal_side_head_hat_dome",
        "maryo_component_normal_side_head_eye",
        "maryo_component_normal_front_head",
        "maryo_component_normal_front_head_pupils",
        "maryo_primitive_big_side_hat_star",
        "maryo_primitive_fire_side_hat_wing",
    } <= primitive_ids
    assert {
        "maryo_assembly_fire_side_head_base",
        "maryo_assembly_short_side_head",
        "maryo_assembly_tall_side_head",
        "maryo_assembly_fire_side_head",
        "maryo_assembly_fire_front_head_base",
        "maryo_assembly_short_front_head",
        "maryo_assembly_tall_front_head",
        "maryo_assembly_fire_front_head",
    } <= assembly_ids

    # The editable normal head is authored as one coherent component so facial
    # edits happen in context, while derived heads still clone from its child
    # groups or the whole group.
    normal_side_head = next(node for node in primitives if node.get("id") == "maryo_component_normal_side_head")
    normal_side_child_ids = {child.get("id") or "" for child in normal_side_head}
    assert {
        "maryo_component_normal_side_head_rear_hair",
        "maryo_component_normal_side_head_skin",
        "maryo_component_normal_side_head_hat_dome",
        "maryo_component_normal_side_head_eye",
        "maryo_component_normal_side_head_face_details",
    } <= normal_side_child_ids

    fire_base = next(node for node in assemblies if node.get("id") == "maryo_assembly_fire_side_head_base")
    fire_xml = ET.tostring(fire_base, encoding="unicode")
    assert "Rear Hair" in fire_xml
    assert "Skin" in fire_xml
    assert "Eye" in fire_xml
    assert "Hat Dome" in fire_xml
    assert "#ec583a" in fire_xml

    tall_head = next(node for node in assemblies if node.get("id") == "maryo_assembly_tall_side_head")
    tall_xml = ET.tostring(tall_head, encoding="unicode")
    assert "#maryo_component_normal_side_head" in tall_xml
    assert "#maryo_primitive_big_side_hat_star" in tall_xml
    fire_head = next(node for node in assemblies if node.get("id") == "maryo_assembly_fire_side_head")
    fire_head_xml = ET.tostring(fire_head, encoding="unicode")
    assert "#maryo_assembly_fire_side_head_base" in fire_head_xml
    assert "#maryo_primitive_fire_side_hat_wing" in fire_head_xml

    for form_name in ("Short", "Tall", "Fire"):
        side = labels[f"Mary-O - {form_name} Side"]
        front = labels[f"Mary-O - {form_name} Front"]
        side_bones = {child.get("data-rig-bone") for child in side if child.get("data-rig-bone")}
        front_bones = {child.get("data-rig-bone") for child in front if child.get("data-rig-bone")}
        assert {"far_arm", "near_arm", "far_leg", "near_leg", "torso", "head"} <= side_bones
        assert {
            "character_right_arm",
            "character_left_arm",
            "character_right_leg",
            "character_left_leg",
            "torso",
            "head",
        } <= front_bones
        front_parts = {child.get("data-rig-part") for child in front if child.get("data-rig-part")}
        assert {"foreground_garment", "death_expression"} <= front_parts

    ids = " ".join((node.get("id") or "") for node in root.iter()).lower()
    assert "rotated_arm" not in ids
    assert "rotated_leg" not in ids
    assert "elbow" not in ids
    assert "knee" not in ids


def test_authoring_helpers_are_hidden_and_geometry_has_semantic_names() -> None:
    root = ET.fromstring(ASSET.read_bytes())
    parent = {child: node for node in root.iter() for child in node}
    guide_groups = [node for node in root.iter() if node.get(INK_LABEL) == "Rig Guides"]
    assert guide_groups
    assert all("display:none" in (node.get("style") or "") for node in guide_groups)

    for node in root.iter():
        if _local(node.tag) not in {"path", "polygon", "rect", "ellipse", "circle", "line"}:
            continue
        chain = []
        cur = node
        while cur in parent:
            chain.append(cur)
            cur = parent[cur]
        if any(ancestor.get(INK_LABEL) == "Rig Guides" for ancestor in chain):
            continue
        assert node.get("id"), ET.tostring(node, encoding="unicode")
        assert node.get(INK_LABEL), node.get("id")


def test_svg_strokes_default_to_angular_mitered_geometry() -> None:
    root = ET.fromstring(ASSET.read_bytes())
    for node in root.iter():
        local = _local(node.tag)
        if not node.get("stroke") or node.get("stroke") == "none":
            continue
        if local == "path" and not (node.get("id") or "").endswith("pivot_cross"):
            assert node.get("stroke-linecap") == "square", node.get("id")
            assert node.get("stroke-linejoin") == "miter", node.get("id")
        if local == "polygon":
            assert node.get("stroke-linejoin") == "miter", node.get("id")


def test_editable_primitive_geometry_is_path_normalized() -> None:
    root = ET.fromstring(ASSET.read_bytes())
    primitives = next(node for node in root if node.get("id") == "maryo_primitive_components")
    drawable = [
        node
        for node in primitives.iter()
        if _local(node.tag) in {"path", "polygon", "rect", "ellipse", "circle", "line", "polyline"}
    ]
    assert drawable
    assert {_local(node.tag) for node in drawable} == {"path"}
    assert all(node.get("d") for node in drawable)

    # The procedural side pupil begins life as a one-pixel Pillow rectangle.
    # The authoring SVG should preserve that visible area while normalizing it
    # to a node-editable path rather than leaving a zero-width or special rect.
    normal_side_head = next(node for node in primitives if node.get("id") == "maryo_component_normal_side_head")
    side_eye = next(node for node in normal_side_head if node.get("id") == "maryo_component_normal_side_head_eye")
    dark_eye_paths = [
        node for node in side_eye if _local(node.tag) == "path" and node.get("fill") == "#1c1613"
    ]
    assert len(dark_eye_paths) == 1
    assert dark_eye_paths[0].get("d")


def test_authoring_dependency_layers_make_edit_authority_explicit() -> None:
    root = ET.fromstring(ASSET.read_bytes())
    insensitive = "{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}insensitive"
    primitives = next(node for node in root if node.get("id") == "maryo_primitive_components")
    assemblies = next(node for node in root if node.get("id") == "maryo_component_assemblies")

    assert primitives.get("data-authoring-role") == "editable-source"
    assert primitives.get(insensitive) is None
    assert assemblies.get("data-authoring-role") == "derived"
    assert assemblies.get("data-authoring-editable") == "false"
    assert assemblies.get(insensitive) == "true"

    for layer in root:
        if not (layer.get("data-rig-form") and layer.get("data-rig-projection")):
            continue
        assert layer.get("data-authoring-role") == "final-view"
        assert layer.get("data-authoring-editable") == "false"
        assert layer.get(insensitive) == "true"

    assert all(
        node.get("data-authoring-editable") == "true"
        for node in primitives.iter()
        if node.get("data-authoring-master") == "true"
    )


def test_authoring_components_have_one_geometry_authority_per_concept() -> None:
    root = ET.fromstring(ASSET.read_bytes())
    components = next(node for node in root if node.get("id") == "maryo_primitive_components")
    top_ids = {node.get("id") or "" for node in components}
    assert len(top_ids) == 13
    assert top_ids == {
        "maryo_component_normal_side_head",
        "maryo_component_normal_front_head",
        "maryo_primitive_big_side_ribbon",
        "maryo_primitive_big_side_hat_star",
        "maryo_primitive_side_ear_star",
        "maryo_primitive_fire_side_ribbon",
        "maryo_primitive_fire_side_extras",
        "maryo_primitive_fire_side_hat_wing",
        "maryo_primitive_big_front_ribbons",
        "maryo_primitive_big_front_hat_star",
        "maryo_primitive_fire_front_ribbons",
        "maryo_primitive_fire_front_extras",
        "maryo_component_shared_front_death_expression",
    }

    assert not any("torso" in item or "_arm" in item or "_leg" in item or "wings" in item for item in top_ids)
    assert "maryo_component_shared_front_death_expression" in top_ids
    assert not any("front_death_expression" in item and item != "maryo_component_shared_front_death_expression" for item in top_ids)

    # Foreground death repaint now stays local to the final views rather than
    # introducing additional authoring masters outside the head-only library.
    for key in ("short", "tall", "fire"):
        view = next(node for node in root if node.get("data-rig-form") == key and node.get("data-rig-projection") == "front")
        fg = next(node for node in view if node.get("data-rig-part") == "foreground_garment")
        assert any(_local(node.tag) == "path" for node in fg.iter())


def test_authoring_components_have_no_duplicate_leaf_paths_or_broken_uses() -> None:
    root = ET.fromstring(ASSET.read_bytes())
    components = next(node for node in root if node.get("id") == "maryo_primitive_components")
    ignored = {"id", INK_LABEL}
    for component in components:
        signatures: set[tuple] = set()
        for node in component.iter():
            if _local(node.tag) != "path":
                continue
            signature = tuple(sorted((key, value) for key, value in node.attrib.items() if key not in ignored))
            assert signature not in signatures, (component.get("id"), node.get("id"))
            signatures.add(signature)

    ids = {node.get("id") for node in root.iter() if node.get("id")}
    xlink_href = "{http://www.w3.org/1999/xlink}href"
    for node in root.iter():
        if _local(node.tag) != "use":
            continue
        href = node.get("href") or node.get(xlink_href) or ""
        assert href.startswith("#"), node.get("id")
        assert href[1:] in ids, (node.get("id"), href)


def test_hidden_pivot_follows_manual_wrapper_transform(tmp_path: Path) -> None:
    path = mary_o_v2.export_svg_poc_source(tmp_path / "mary_o_seed.svg")
    before = build_rig_document(path, TALL_FORM, "side")
    before_bone = next(b for b in before.bones if b["name"] == "near_arm")

    root = ET.fromstring(path.read_bytes())
    wrapper = next(node for node in root.iter() if node.get("data-rig-part") == "near_arm" and "_tall_side_" in (node.get("id") or ""))
    wrapper.set("transform", "translate(7 -3)")
    path.write_bytes(ET.tostring(root, encoding="utf8", xml_declaration=True))

    after = build_rig_document(path, TALL_FORM, "side")
    after_bone = next(b for b in after.bones if b["name"] == "near_arm")
    assert after_bone["offset"][0] == before_bone["offset"][0] + 7
    assert after_bone["offset"][1] == before_bone["offset"][1] - 3


def test_rig_topology_is_rigid_limbs_only() -> None:
    for form in (SHORT_FORM, TALL_FORM, FIRE_FORM):
        side = build_rig_document(ASSET, form, "side")
        front = build_rig_document(ASSET, form, "front")
        for doc in (side, front):
            bones = {bone["name"] for bone in doc.bones}
            assert not any("elbow" in name or "knee" in name for name in bones)
            assert doc.ik_legs == []
            assert doc.ik_chains == []
            for part in doc.parts:
                if "arm" in part["bone"]:
                    assert len(part["include"]) == 1
                    assert part["include"][0].endswith("_art")


def test_idle_seed_renders_close_to_current_idle_without_postprocess() -> None:
    for form in (SHORT_FORM, TALL_FORM, FIRE_FORM):
        doc = build_rig_document(ASSET, form, "side")
        poses = TALL_LIKE_POSES if form.tall else SHORT_POSES
        poc = render_pose_with_doc(doc, form, poses["idle"][0])
        current = mary_o_v2._draw_form(form, "idle", 0, 1)
        assert poc.size == current.size == mary_o_v2.FRAME_SIZE
        pbox = poc.getchannel("A").getbbox()
        cbox = current.getchannel("A").getbbox()
        assert pbox is not None and cbox is not None
        if form is TALL_FORM:
            # Tall now intentionally reuses the short head component via a shared
            # transformed clone, so exact idle parity with the legacy procedural
            # tall head capture is no longer the point of the authoring POC.
            assert pbox[2] - pbox[0] >= 80
            assert pbox[3] - pbox[1] >= 110
            continue
        assert all(abs(a - b) <= 3 for a, b in zip(pbox, cbox)), (form.target_name, pbox, cbox)


def test_rotated_pose_uses_same_arm_sprite_via_bone_rotation() -> None:
    doc = build_rig_document(ASSET, TALL_FORM, "side")
    idle = render_pose_with_doc(doc, TALL_FORM, TALL_LIKE_POSES["idle"][0])
    jump = render_pose_with_doc(doc, TALL_FORM, TALL_LIKE_POSES["jump"][0])
    assert ImageChops.difference(idle, jump).getbbox() is not None
    arm_parts = [part for part in doc.parts if part["bone"] in {"far_arm", "near_arm"}]
    assert len(arm_parts) == 2
    assert all("rotated" not in part["name"] for part in arm_parts)


def test_death_is_built_from_front_svg_rig_not_procedural_fallback(monkeypatch) -> None:
    docs = _docs()

    def fail_fallback(*args, **kwargs):
        raise AssertionError("front death unexpectedly used procedural fallback")

    monkeypatch.setattr(mary_o_v2_svg_poc.procedural, "_draw_form", fail_fallback)
    result = mary_o_v2_svg_poc._draw_poc_form(TALL_FORM, docs, "death", 0, 1)
    assert result.size == mary_o_v2.FRAME_SIZE
    assert result.getbbox() is not None


def test_transform_poc_runs_rig_then_python_effect_postprocess() -> None:
    docs = {
        form.target_name: build_rig_document(ASSET, form, "side")
        for form in (SHORT_FORM, TALL_FORM, FIRE_FORM)
    }
    base = render_pose_with_doc(docs[TALL_FORM.target_name], TALL_FORM, TALL_LIKE_POSES["idle"][0])
    transformed = mary_o_v2_svg_poc._draw_poc_form(FIRE_FORM, docs, "transform", 0, 11)
    assert transformed.size == base.size == mary_o_v2.FRAME_SIZE
    assert ImageChops.difference(base, transformed).getbbox() is not None
