from __future__ import annotations

import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from ambition_sprite2d_renderer.devtools import svg_rig_tool


REPO_ROOT = Path(__file__).resolve().parents[1]
SVG_ROOTS = (
    REPO_ROOT / "assets",
    REPO_ROOT / "ambition_sprite2d_renderer" / "data" / "characters",
)


def _svg_paths() -> list[Path]:
    return sorted({path for root in SVG_ROOTS for path in root.rglob("*.svg")})


def _metadata(path: Path) -> ET.Element:
    root = ET.parse(path).getroot()
    return next(elem for elem in root.iter() if elem.get("id") == svg_rig_tool.RIG_METADATA_ID)


def _view(path: Path, view_id: str) -> ET.Element:
    root = ET.parse(path).getroot()
    return next(elem for elem in root.iter() if elem.get("data-rig-view-def") == view_id)


def test_every_svg_declares_its_ambition_role() -> None:
    paths = _svg_paths()
    assert paths
    for path in paths:
        metadata = _metadata(path)
        assert metadata.get("data-ambition-schema") == svg_rig_tool.SCHEMA, path
        assert metadata.get("data-ambition-role") in {"character-rig", "rig-template", "reference"}, path


def test_every_character_rig_catalog_is_self_consistent() -> None:
    for path in _svg_paths():
        if _metadata(path).get("data-ambition-role") == "character-rig":
            assert svg_rig_tool.validate(path) == [], path


def test_articulated_polygon_catalog_exposes_jointed_humanoid_structure() -> None:
    path = (
        REPO_ROOT
        / "ambition_sprite2d_renderer/data/characters/pointed_polygon/pointed_polygon.svg"
    )
    view = _view(path, "side")
    assert view.get("data-rig-profile") == "humanoid-articulated-v1"
    bones = {elem.get("data-rig-bone-def") for elem in view if elem.get("data-rig-bone-def")}
    assert {"near_arm_u", "near_arm_l", "near_leg_u", "near_leg_l"} <= bones

    parts = {
        elem.get("data-rig-part-def"): elem
        for elem in view
        if elem.get("data-rig-part-def")
    }
    # Visual parts can bind to an existing articulated bone without creating
    # another skeletal degree of freedom.
    assert parts["sword"].get("data-rig-bone") == "near_arm_hand"


def test_mary_o_is_encoded_as_rigid_biped_not_fake_humanoid() -> None:
    path = REPO_ROOT / "assets/mary_o_v2.svg"
    root = ET.parse(path).getroot()
    views = [elem for elem in root.iter() if elem.get("data-rig-view-def")]
    assert views
    for view in views:
        assert view.get("data-rig-profile") == "rigid-biped-v1"
        bone_names = {
            elem.get("data-rig-bone-def") or ""
            for elem in view
            if elem.get("data-rig-bone-def")
        }
        assert not any("elbow" in name or "knee" in name for name in bone_names)


def test_nudge_part_moves_art_without_moving_bind_or_skeleton_joint(tmp_path: Path) -> None:
    source = (
        REPO_ROOT
        / "ambition_sprite2d_renderer/data/characters/pointed_polygon/pointed_polygon.svg"
    )
    work = tmp_path / source.name
    shutil.copy2(source, work)

    root = ET.parse(work).getroot()
    view = next(elem for elem in root.iter() if elem.get("data-rig-view-def") == "side")
    part = next(elem for elem in view if elem.get("data-rig-part-def") == "near_arm_u")
    art_id = (part.get("data-rig-elements") or "").split()[0]
    bind_id = part.get("data-rig-pivot")
    assert bind_id
    bind = next(elem for elem in root.iter() if elem.get("id") == bind_id)
    shoulder = next(elem for elem in root.iter() if elem.get("data-rig-joint") == "near_shoulder")
    bind_before = (float(bind.get("cx", "0")), float(bind.get("cy", "0")))
    shoulder_before = (shoulder.get("cx"), shoulder.get("cy"))

    svg_rig_tool.nudge_part(work, view_id="side", part_name="near_arm_u", dx=3.5, dy=-2.0)

    root = ET.parse(work).getroot()
    art = next(elem for elem in root.iter() if elem.get("id") == art_id)
    bind = next(elem for elem in root.iter() if elem.get("id") == bind_id)
    shoulder = next(elem for elem in root.iter() if elem.get("data-rig-joint") == "near_shoulder")
    assert (art.get("transform") or "").startswith("translate(3.5,-2)")
    assert (float(bind.get("cx", "0")), float(bind.get("cy", "0"))) == bind_before
    assert (shoulder.get("cx"), shoulder.get("cy")) == shoulder_before
    assert svg_rig_tool.validate(work) == []


def test_move_joint_keeps_editor_bone_guide_attached(tmp_path: Path) -> None:
    source = (
        REPO_ROOT
        / "ambition_sprite2d_renderer/data/characters/pointed_polygon/pointed_polygon.svg"
    )
    work = tmp_path / source.name
    shutil.copy2(source, work)

    svg_rig_tool.move_marker(
        work,
        view_id="side",
        kind="joint",
        name="near_shoulder",
        x=530.0,
        y=290.0,
    )

    root = ET.parse(work).getroot()
    guide = next(elem for elem in root.iter() if elem.get("data-rig-bone-guide") == "near_arm_u")
    assert guide.get("x1") == "530"
    assert guide.get("y1") == "290"
    assert svg_rig_tool.validate(work) == []


def test_reference_pixel_rig_markers_are_converted_to_root_svg_units() -> None:
    path = REPO_ROOT / "assets/noether.svg"
    root = ET.parse(path).getroot()
    generated = next(
        elem for elem in root.iter()
        if elem.get("id") == "ambition-rig-side-joint-near_shoulder"
    )
    authored = next(
        elem for elem in root.iter()
        if elem.get("{http://www.inkscape.org/namespaces/inkscape}label") == "Shoulder - Near"
    )
    assert abs(float(generated.get("cx", "0")) - float(authored.get("cx", "0"))) < 0.2
    assert abs(float(generated.get("cy", "0")) - float(authored.get("cy", "0"))) < 0.2


def test_validate_rejects_generated_markers_outside_root_viewbox(tmp_path: Path) -> None:
    source = REPO_ROOT / "assets/noether.svg"
    work = tmp_path / source.name
    shutil.copy2(source, work)
    svg_rig_tool.move_marker(
        work,
        view_id="side",
        kind="joint",
        name="near_shoulder",
        x=700.0,
        y=700.0,
    )
    errors = svg_rig_tool.validate(work)
    assert any("coordinate-space mismatch" in error for error in errors)


def test_nudge_part_uses_root_svg_delta_through_parent_scale(tmp_path: Path) -> None:
    source = REPO_ROOT / "assets/noether.svg"
    work = tmp_path / source.name
    shutil.copy2(source, work)

    root = ET.parse(work).getroot()
    view = next(elem for elem in root.iter() if elem.get("data-rig-view-def") == "side")
    part = next(elem for elem in view if elem.get("data-rig-part-def") == "torso_shirt")
    art_id = (part.get("data-rig-elements") or "").split()[0]
    bind_id = part.get("data-rig-pivot")
    assert bind_id
    bind = next(elem for elem in root.iter() if elem.get("id") == bind_id)
    bind_before = (bind.get("cx"), bind.get("cy"))

    svg_rig_tool.nudge_part(work, view_id="side", part_name="torso_shirt", dx=10.4, dy=0.0)

    root = ET.parse(work).getroot()
    art = next(elem for elem in root.iter() if elem.get("id") == art_id)
    bind = next(elem for elem in root.iter() if elem.get("id") == bind_id)
    # The art lives under a 1.04x parent transform, so a 10.4 root-unit move
    # requires a 10-unit translation in that parent's local coordinates.
    assert (art.get("transform") or "").startswith("translate(10,0)")
    assert (bind.get("cx"), bind.get("cy")) == bind_before


def test_translate_part_source_moves_dedicated_bind_pivot(tmp_path: Path) -> None:
    source = (
        REPO_ROOT
        / "ambition_sprite2d_renderer/data/characters/pointed_polygon/pointed_polygon.svg"
    )
    work = tmp_path / source.name
    shutil.copy2(source, work)

    root = ET.parse(work).getroot()
    view = next(elem for elem in root.iter() if elem.get("data-rig-view-def") == "side")
    part = next(elem for elem in view if elem.get("data-rig-part-def") == "near_arm_u")
    bind_id = part.get("data-rig-pivot")
    assert bind_id
    bind = next(elem for elem in root.iter() if elem.get("id") == bind_id)
    before = (float(bind.get("cx", "0")), float(bind.get("cy", "0")))

    svg_rig_tool.translate_part_source(
        work, view_id="side", part_name="near_arm_u", dx=3.5, dy=-2.0
    )

    root = ET.parse(work).getroot()
    bind = next(elem for elem in root.iter() if elem.get("id") == bind_id)
    assert float(bind.get("cx", "0")) == before[0] + 3.5
    assert float(bind.get("cy", "0")) == before[1] - 2.0


def test_catalog_reuses_authored_svg_joint_markers_when_available() -> None:
    path = REPO_ROOT / "assets/patent-clerk.svg"
    root = ET.parse(path).getroot()
    view = next(elem for elem in root.iter() if elem.get("data-rig-view-def") == "side")
    bone = next(
        elem for elem in view
        if elem.get("data-rig-bone-def") == "near_arm_u"
    )
    # Static anatomy already authored in the SVG is the authority.  The
    # generated catalog points at it instead of maintaining a second copy.
    assert bone.get("data-rig-origin") == "joint-near-shoulder"
    assert bone.get("data-rig-tip") == "joint-near-elbow"
    assert not any(
        elem.get("id") == "ambition-rig-side-joint-near_shoulder"
        for elem in root.iter()
    )


def test_move_joint_can_edit_transformed_authored_svg_marker(tmp_path: Path) -> None:
    source = REPO_ROOT / "assets/carl-stargan.svg"
    work = tmp_path / source.name
    shutil.copy2(source, work)

    svg_rig_tool.move_marker(
        work,
        view_id="side",
        kind="joint",
        name="near_shoulder",
        x=133.0,
        y=106.0,
    )

    root = ET.parse(work).getroot()
    marker = next(elem for elem in root.iter() if elem.get("id") == "joint-near-shoulder")
    x, y = svg_rig_tool._element_point_in_root(root, marker)
    assert abs(x - 133.0) < 1e-5
    assert abs(y - 106.0) < 1e-5
    guide = next(elem for elem in root.iter() if elem.get("data-rig-bone-guide") == "near_arm_u")
    assert abs(float(guide.get("x1", "0")) - 133.0) < 1e-5
    assert abs(float(guide.get("y1", "0")) - 106.0) < 1e-5


def test_hunny_custom_rig_anchors_joint_origins_to_art_bind_pivots() -> None:
    path = (
        REPO_ROOT
        / "ambition_sprite2d_renderer/data/characters/hunny_horror_boss/hunny_horror_boss-front.svg"
    )
    root = ET.parse(path).getroot()
    shoulder = next(
        elem for elem in root.iter()
        if elem.get("id") == "ambition-rig-front-joint-left_shoulder"
    )
    elbow = next(
        elem for elem in root.iter()
        if elem.get("id") == "ambition-rig-front-joint-left_elbow"
    )
    assert (float(shoulder.get("cx", "0")), float(shoulder.get("cy", "0"))) == (49.0, 81.0)
    assert (float(elbow.get("cx", "0")), float(elbow.get("cy", "0"))) == (35.0, 102.0)


def test_repo_preview_writes_single_contact_sheet(tmp_path: Path, monkeypatch) -> None:
    from PIL import Image
    import io

    def fake_preview(_path: Path, *, width: int, view_id: str | None = None) -> bytes:
        image = Image.new("RGBA", (max(8, width // 10), 40), (0, 0, 0, 255))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    monkeypatch.setattr(svg_rig_tool, "_preview_svg_bytes", fake_preview)
    output = tmp_path / "layouts.png"
    assert svg_rig_tool.write_repo_preview(
        REPO_ROOT, output, columns=4, tile_width=180, rigs_only=True
    ) == output.resolve()
    with Image.open(output) as image:
        assert image.width == 4 * 180
        assert image.height > 0
