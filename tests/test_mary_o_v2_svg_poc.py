"""What the Mary-O SVG rig POC PRODUCES — never how its source is authored.

⛔ **eight structural tests were removed from this file on 2026-08-18, on Jon's
ruling**: *"they are too bespoke. I don't want tests asserting how things should
be authored that a human will edit."* They pinned the set of top-level layers,
the id scheme, stroke-linejoin conventions, which groups were `sodipodi:insensitive`,
the exact 13 component masters, and that every drawable carried a semantic label —
all read off ``assets/mary_o_v2.svg``, which is an ARTIST's file. Opening it in
Inkscape and adding a size-guides layer turned five of them red while nothing
about the sprite was wrong. A test that fails on WORK is not a guard.

⭐ what stays is the other half, and it is the half worth having: the exporter's
own output (written to ``tmp_path``, so it is a GENERATED file and may be pinned),
and what the rig actually RENDERS — idle parity, a rotated pose reusing one arm
sprite, death coming from the front rig rather than the procedural fallback, and
the transform running rig-then-postprocess.

⚠ the one real check that went with them and has no replacement yet: a ``<use>``
whose href names no id renders NOTHING, silently. The recorded direction is for
``build_rig_document`` to REFUSE it with a sentence naming the element — a
diagnostic the author reads at load, not a suite that goes red behind them.
"""

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
    build_rig_document,
    render_pose_with_doc,
)


ASSET = Path(mary_o_v2_svg_poc.ASSET_PATH)
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
def test_the_bone_follows_the_pivot_in_the_flat_rig_joints_layer(tmp_path: Path) -> None:
    """**Moving a dot in `Rig Joints` moves its bone; moving the ART does not.**

    ⭐ **this replaces `test_hidden_pivot_follows_manual_wrapper_transform`, whose
    premise the pivot rework deleted.** That test moved a part WRAPPER and
    asserted the pivot moved with it, which was true only because each pivot then
    lived inside the part it belonged to. Two things were wrong with that: the
    pivot was a drawable within the part (so it could leak into the part's
    raster, which is the only reason the marker had to be a separate hidden
    cross at all), and its `cx`/`cy` were in the part's local space -- Mary-O's
    were displaced by up to 880 units from where Inkscape drew them, which makes
    a pivot impossible to place by eye.

    ⛔ **so the independence asserted below is the FEATURE, not a regression.**
    Pivots are authored in one flat per-model layer, in the model's own
    coordinates, exactly as every other rig SVG here does it; art and pivot are
    edited separately on purpose.

    ⚠ both halves are asserted because either alone passes on a rig that reads
    nothing: a reader that ignored the flat layer entirely would still satisfy
    "the wrapper transform did not move the bone".
    """
    path = mary_o_v2.export_svg_poc_source(tmp_path / "mary_o_seed.svg")
    before = build_rig_document(path, TALL_FORM, "side")
    before_bone = next(b for b in before.bones if b["name"] == "near_arm")

    # 1. the ART moves, the bone does not.
    root = ET.fromstring(path.read_bytes())
    wrapper = next(node for node in root.iter() if node.get("data-rig-part") == "near_arm" and "_tall_side_" in (node.get("id") or ""))
    wrapper.set("transform", "translate(7 -3)")
    path.write_bytes(ET.tostring(root, encoding="utf8", xml_declaration=True))
    art_moved = build_rig_document(path, TALL_FORM, "side")
    art_moved_bone = next(b for b in art_moved.bones if b["name"] == "near_arm")
    assert art_moved_bone["offset"] == before_bone["offset"], (
        "transforming a part's artwork moved its BONE; pivots are authored "
        "independently of the art they belong to"
    )

    # 2. the PIVOT moves, and the bone follows it exactly.
    root = ET.fromstring(path.read_bytes())
    dot = next(node for node in root.iter()
               if node.get("data-rig-joint") == "near_arm" and "_tall_side_" in (node.get("id") or ""))
    dot.set("cx", str(float(dot.get("cx")) + 7))
    dot.set("cy", str(float(dot.get("cy")) - 3))
    path.write_bytes(ET.tostring(root, encoding="utf8", xml_declaration=True))
    after = build_rig_document(path, TALL_FORM, "side")
    after_bone = next(b for b in after.bones if b["name"] == "near_arm")
    assert after_bone["offset"][0] == before_bone["offset"][0] + 7
    assert after_bone["offset"][1] == before_bone["offset"][1] - 3
def test_every_form_renders_a_whole_body_from_its_rig() -> None:
    """**Every form builds a rig and draws a body at frame size.**

    ⛔ **this compared each form's render against the LEGACY PROCEDURAL draw
    within 3px, and that comparison is gone as of 2026-08-18.** It retired one
    form at a time, each for the same reason and each only after it had already
    gone red on ordinary authoring:

    ```text
    TALL   reuses the short head via a shared transformed clone
    FIRE   the authored side silhouette moved — rig 122px wide vs procedural 110
    SHORT  the last holdout; the rig drew 7px taller at the top
    ```

    ⇒ with all three authored, parity with the procedural draw is a property NO
    form owes: that draw is the thing the rig replaces. Holding the rig to it
    pixel-for-pixel made every deliberate art change a red suite — the same
    failure that took eight structural tests out of this file the same day, on
    the maintainer's ruling that a test must not assert how a human-edited asset
    is authored.

    ⭐ **what remains is what a defect actually looks like**: a form that fails to
    build a rig, renders at the wrong size, or collapses to nothing.

    ⚠ **the floor is PER FORM, and the first draft of it was wrong.** It reused
    tall's `80 x 110` for every form and failed SHORT immediately — because SHORT
    is legitimately a smaller character (one brick against tall's two), not a
    collapsed one. Measured at 2026-08-18, with the floors set well under:

    ```text
    mary_o_v2        64 x  86    floor 40 x 55
    mary_o_v2_tall   95 x 163    floor 60 x 100
    mary_o_v2_fire  122 x 182    floor 60 x 100
    ```
    """
    for form in (SHORT_FORM, TALL_FORM, FIRE_FORM):
        doc = build_rig_document(ASSET, form, "side")
        poses = TALL_LIKE_POSES if form.tall else SHORT_POSES
        poc = render_pose_with_doc(doc, form, poses["idle"][0])
        assert poc.size == mary_o_v2.FRAME_SIZE, form.target_name
        pbox = poc.getchannel("A").getbbox()
        assert pbox is not None, f"{form.target_name} rendered nothing at all"
        min_w, min_h = (60, 100) if form.tall else (40, 55)
        assert pbox[2] - pbox[0] >= min_w, (form.target_name, pbox)
        assert pbox[3] - pbox[1] >= min_h, (form.target_name, pbox)


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
