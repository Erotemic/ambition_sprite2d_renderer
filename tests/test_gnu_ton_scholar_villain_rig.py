"""Structure and real-rig motion invariants for the proposed scholar redesign."""
from __future__ import annotations

import json
from pathlib import Path
import xml.etree.ElementTree as ET

from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.devtools import svg_rig_tool
from ambition_sprite2d_renderer.registry.discovery import discover_module_targets

PACKAGE = Path(__file__).resolve().parents[1] / "ambition_sprite2d_renderer"
RIG = PACKAGE / "targets/characters/rigged/gnu_ton_scholar_villain.rig.json"
SVG = PACKAGE / "data/characters/gnu_ton_scholar_villain/gnu_ton_scholar_villain.svg"
NAME = "gnu_ton_scholar_villain"


def test_generated_scholar_is_a_registered_articulated_svg_rig():
    doc = RigDocument.load(RIG)
    assert NAME in discover_module_targets().targets
    assert svg_rig_tool.validate(SVG) == []
    bones = {bone["name"] for bone in doc.bones}
    assert {"pelvis", "torso", "head", "near_arm_u", "near_arm_l",
            "far_arm_u", "far_arm_l", "near_hand", "far_hand",
            "near_leg_u", "near_leg_l", "far_leg_u", "far_leg_l",
            "tail_near", "tail_far", "wig_queue"} <= bones
    assert all(part["bone"] in bones for part in doc.parts)
    assert len({p["name"] for p in doc.parts}) == len(doc.parts)
    root = ET.parse(SVG).getroot()
    elements = {el.get("id") for el in root.iter() if el.get("id")}
    assert all(set(p.get("include", [])) <= elements for p in doc.parts)
    props = {part["name"]: part for part in doc.parts}
    assert props["principia_book"]["bone"] == "far_hand"
    assert props["quill"]["bone"] == "near_hand"
    assert props["head_face"]["bone"] == "head"
    assert props["wig_queue"]["bone"] == "wig_queue"
    assert props["far_coat_tail"]["bone"] == "tail_far"
    assert props["near_coat_tail"]["bone"] == "tail_near"
    assert props["pelvis_panel"]["bone"] == "pelvis"


def test_scholar_clips_move_real_bones_and_toggle_separate_props():
    doc = RigDocument.load(RIG)
    world_rest, params_rest = doc.solve("rest", 0.0)
    world_point, params_point = doc.solve("point", 0.5)
    world_invoke, params_invoke = doc.solve("invoke", 0.55)
    assert abs(world_rest["near_arm_u"].angle - world_point["near_arm_u"].angle) > 25
    assert abs(world_rest["head"].angle - world_invoke["head"].angle) > 8
    assert params_rest["prop.book"] == 1.0
    assert doc.solve("conduct", 0.5)[1]["prop.book"] == 0.0
    assert doc.solve("tumble", 0.5)[1]["prop.quill"] == 0.0
    assert abs(params_invoke["tail_near"]) > 4


def test_all_animation_frames_fit_inside_the_authored_sprite_canvas():
    doc = RigDocument.load(RIG)
    w, h = int(doc.frame["width"]), int(doc.frame["height"])
    pad = 25
    for row, frame_count, _ms in doc.rows():
        for index in range(frame_count):
            # An overscanned *render*, not just bounds on the cropped frame:
            # clipping can otherwise silently pass visual smoke tests.
            rendered = doc.render_frame(row, index, frame_count, padding=pad)
            bbox = rendered.getbbox()
            assert bbox is not None, (row, index)
            left, top, right, bottom = (v - pad for v in bbox)
            assert 3 <= left < right <= w - 3, (row, index, bbox)
            assert 3 <= top < bottom <= h - 3, (row, index, bbox)


def test_boss_animation_contract_matches_the_shipped_rider():
    """The candidate must not silently drop one of the game's move states."""
    from ambition_sprite2d_renderer.targets.characters.gnu_ton_boss import scholar

    doc = RigDocument.load(RIG)
    assert [(row, count) for row, count, _ in doc.rows()] == [
        (row, count) for row, count, _ in scholar.ROWS
    ]


def test_animated_depth_orders_falling_arm_behind_the_face():
    """The death pose must not cover its face with a forward-sorted forearm."""
    from ambition_sprite2d_renderer.authoring.rigdoc import ordered_parts, visible_parts

    doc = RigDocument.load(RIG)

    def rank(clip, t):
        params = doc.solve(clip, t)[1]
        parts = ordered_parts(visible_parts(doc.parts, doc.features), params)
        return {part["name"]: i for i, part in enumerate(parts)}

    rest = rank("rest", 0)
    dying = rank("death", 0.5)
    tumbling = rank("tumble", 0.5)
    assert rest["near_hand_fist"] > rest["head_face"]
    assert dying["near_hand_fist"] < dying["head_face"]
    assert dying["near_arm_upper"] < dying["head_face"]
    assert tumbling["near_hand_fist"] < tumbling["head_face"]
    assert dying["dizzy_stars"] > dying["head_face"]


def test_open_book_and_reaction_effects_have_independent_motion_channels():
    doc = RigDocument.load(RIG)
    parts = {part["name"]: part for part in doc.parts}
    assert parts["principia_open_cover"]["bone"] == "far_hand"
    assert parts["dizzy_stars"]["bone"] == "star_halo"
    assert parts["flying_apple"]["bone"] == "head"
    assert parts["wig_back_mass"]["bone"] == "head"
    for t in (0.0, 0.25, 0.5, 0.75):
        params = doc.solve("invoke", t)[1]
        assert params["prop.book"] == 0.0
        assert params["prop.book_open"] == 1.0
    for row in ("dazed", "death"):
        assert doc.solve(row, 0.25)[1]["fx.stars"] == 1.0
    assert doc.solve("dazed", 0.25)[1]["prop.apple"] == 1.0
    assert doc.solve("tumble", 0)[1]["prop.apple"] == 1.0
    assert doc.solve("tumble", 0.75)[1]["prop.apple"] == 0.0
    assert doc.solve("dazed", 0.125)[1]["star_halo"] != doc.solve("dazed", 0.375)[1]["star_halo"]


def test_mid_tumble_stays_near_rest_ground_reference():
    """Regression for inverted pose hovering too far above the baseline."""
    doc = RigDocument.load(RIG)
    rest = doc.render_frame("rest", 0, 10).getbbox()
    inverted = doc.render_frame("tumble", 4, 8).getbbox()
    assert rest is not None and inverted is not None
    assert abs(inverted[3] - rest[3]) < 60
    assert inverted[3] < doc.frame["height"] - 3


def test_scholar_specific_facial_channels_are_actually_driven():
    """Humanoid's default channels do not include surprised or wavy."""
    doc = RigDocument.load(RIG)
    brace = doc.solve("brace", 0.5)[1]
    dazed = doc.solve("dazed", 0.5)[1]
    climb = doc.solve("climb", 0.5)[1]
    rest = doc.solve("rest", 0.5)[1]
    assert brace["eye.surprised"] == 1.0
    assert brace["mouth.open"] == 1.0
    assert dazed["eye.dizzy"] == 1.0
    assert dazed["mouth.wavy"] == 1.0
    assert climb["eye.shut"] == 1.0
    assert climb["mouth.grit"] == 1.0
    assert rest["eye.surprised"] == rest["mouth.wavy"] == 0.0


def test_inkscape_parts_have_semantic_names_and_expression_folders():
    """Artist can identify every primitive and find exclusive alternatives."""
    from collections import Counter
    from ambition_sprite2d_renderer.authoring.svg_parts import INK_NS

    root = ET.parse(SVG).getroot()
    ink_label = f"{{{INK_NS}}}label"
    shapes = {'path', 'ellipse', 'circle', 'rect', 'polygon', 'polyline', 'line', 'use'}
    names = [el.get('id') for el in root.iter() if el.tag.rsplit('}', 1)[-1] in shapes]
    assert all(names)
    assert all(n == 1 for n in Counter(names).values()), 'every shape id must be unique'
    assert all(el.get(ink_label) for el in root.iter() if el.tag.rsplit('}', 1)[-1] in shapes)
    art = next(el for el in root.iter() if el.get('id') == 'scholar-three-quarter')
    families = {el.get('id'): el for el in art if el.get('data-rig-editor-family')}
    assert set(families) == {
        'scholar-eye-alternatives', 'scholar-mouth-alternatives',
        'scholar-book-alternatives', 'scholar-optional-effects',
    }
    for family in families.values():
        assert all(el.get('data-rig-part') and el.get('data-rig-editor-visibility') == 'editor-only'
                   for el in family)
    assert [el.get('id') for el in families['scholar-eye-alternatives']] == [
        'eye_angry', 'eye_open', 'eye_surprised', 'eye_shut', 'eye_dead', 'eye_dizzy',
    ]
    assert [el.get('id') for el in families['scholar-mouth-alternatives']] == [
        'mouth_closed', 'mouth_smile', 'mouth_open', 'mouth_wavy', 'mouth_grit',
    ]
    assert not next(el for el in root.iter() if el.get('id') == 'eye_open').get('style')
    assert next(el for el in root.iter() if el.get('id') == 'eye_angry').get('style') == 'display:none'
    assert next(el for el in root.iter() if el.get('id') == 'mouth_open').get('style') == 'display:none'
    marker_layer = next(el for el in root if el.get('id') == 'ambition-rig-markers')
    assert marker_layer.get('style') == 'display:none'
    assert any(el.get('id') == 'head_face--small-triangular-nose' for el in root.iter())
    assert any(el.get('id') == 'head_face--rosy-blush-on-cheek' for el in root.iter())
    assert not any(el.get('id') == 'head_face--nose-tip-skin-highlight' for el in root.iter())
    assert not any(el.get('id') == 'torso_coat--coat-left-shadow-panel' for el in root.iter())


def test_d2_face_eye_perspective_in_canonical_svg():
    """The approved D2 placement must survive all generator rebuilds.

    Character-right is the viewer-near, canvas-left eye in this 3/4 view.
    Character-left is the canvas-right far eye. These are actor-side names.
    """
    root = ET.parse(SVG).getroot()
    by_id = {el.get('id'): el for el in root.iter() if el.get('id')}
    for variant in ('eye_open', 'eye_angry', 'eye_surprised'):
        part = by_id[variant]
        shapes = [el for el in part if el.get('data-art-purpose')]
        near = next(el for el in shapes if 'NEAR eye (canvas-left)' in el.get('data-art-purpose', ''))
        far = next(el for el in shapes if 'FAR eye (canvas-right)' in el.get('data-art-purpose', ''))
        near_x, far_x = float(near.get('cx')), float(far.get('cx'))
        near_y, far_y = float(near.get('cy')), float(far.get('cy'))
        assert near_x < far_x, variant
        assert float(near.get('rx')) >= 1.6 * float(far.get('rx')), variant
        assert near_y > far_y + 2, variant
        assert near.get('data-art-purpose', '').startswith('Actor-right NEAR')
        assert far.get('data-art-purpose', '').startswith('Actor-left FAR')
    doc = RigDocument.load(RIG)
    assert doc.solve('rest', 0.5)[1]['eye.open'] == 1.0
