"""The character generator: specs, views and rigs.

These protect the generator's contract, not any one generated look: a spec is
plain data that round-trips; the same spec draws the same bytes; a crowd is
made of measurably different people inside their bases' ranges; every base
draws in every view; a taller spec is a taller sprite; and a generated
character binds to the common humanoid rig, so the posing tools pose it.
"""

from __future__ import annotations

import itertools
import json

import pytest
from PIL import Image, ImageChops, ImageStat

from ambition_sprite2d_renderer.chargen import spec as S
from ambition_sprite2d_renderer.chargen.geometry import VIEW_BY_KEY, VIEWS
from ambition_sprite2d_renderer.chargen.rig import character_svg, write_character
from ambition_sprite2d_renderer.chargen.sheets import RiggedCharacter, render_view


def _alpha_box(img: Image.Image):
    return img.getchannel("A").getbbox()


# ---- the record ------------------------------------------------------------------------------


def test_generation_is_deterministic_and_a_seed_matters():
    a = S.generate("average_female", 11)
    assert a == S.generate("average_female", 11)
    assert a != S.generate("average_female", 12)
    assert S.crowd(6, 4) == S.crowd(6, 4)


def test_spec_round_trips_through_json_and_yaml(tmp_path):
    spec = S.generate("heavy_male", 3)
    assert S.CharacterSpec.from_json(spec.to_json()) == spec
    for name in ("a.json", "a.yaml"):
        path = spec.save(tmp_path / name)
        assert S.CharacterSpec.load(path) == spec


def test_a_hand_edited_partial_spec_is_completed_from_its_base_and_seed(tmp_path):
    path = tmp_path / "partial.json"
    path.write_text(json.dumps({"base": "slim_female", "seed": 9, "hair": {"style": "afro"}, "outfit": {"hat": "bowler"}}))
    spec = S.CharacterSpec.load(path)
    drawn = S.generate("slim_female", 9)
    assert (spec.hair.style, spec.outfit.hat) == ("afro", "bowler")
    # An override changes only the field it names.
    assert spec.body == drawn.body and spec.face == drawn.face and spec.palette == drawn.palette
    assert spec.outfit.top_color == drawn.outfit.top_color


def test_every_generated_spec_is_valid_and_inside_its_base(tmp_path):
    for spec in S.crowd(48, 1):
        assert S.validate(spec) == []
        base = S.BASES[spec.base]
        for name, (lo, hi) in base.ranges.items():
            assert lo <= getattr(spec.body, name) <= hi, (spec.name, name)


@pytest.mark.parametrize(
    "edit, field",
    [
        (lambda s: setattr(s.body, "height_cm", 260.0), "body.height_cm"),
        (lambda s: setattr(s.face, "eye_size", 3.0), "face.eye_size"),
        (lambda s: setattr(s.hair, "style", "mullet"), "hair.style"),
        (lambda s: setattr(s.palette, "skin", "pink"), "palette.skin"),
        (lambda s: s.outfit.accessories.append("monocle"), "outfit.accessories"),
        (lambda s: setattr(s, "base", "giant_male"), "base"),
    ],
)
def test_out_of_bounds_specs_are_rejected(edit, field):
    spec = S.generate("average_male", 2)
    edit(spec)
    errors = S.validate(spec)
    assert any(field in e for e in errors), errors
    with pytest.raises(ValueError):
        S.check(spec)


def test_a_crowd_is_made_of_distinct_people():
    crowd = S.crowd(40, 7)
    distances = [S.spec_distance(a, b) for a, b in itertools.combinations(crowd, 2)]
    assert min(distances) > 1.5
    assert len({s.base for s in crowd}) == len(S.BASES)
    assert len({s.palette.skin for s in crowd}) >= 6
    assert len({s.hair.style for s in crowd}) >= 6


# ---- the drawing ---------------------------------------------------------------------------------


def test_the_same_spec_draws_byte_identical_svg():
    spec = S.generate("broad_female", 5)
    assert character_svg(spec) == character_svg(S.CharacterSpec.from_json(spec.to_json()))


def test_every_base_draws_every_view_on_the_ground():
    for base in sorted(S.BASES):
        spec = S.generate(base, 1)
        bottoms = []
        for view in VIEWS:
            img = render_view(spec, view, px_per_cm=0.5)
            box = _alpha_box(img)
            assert box is not None, (base, view.key)
            bottoms.append(box[3])
        # One ground line for all five views.
        assert max(bottoms) - min(bottoms) <= 2, (base, bottoms)


def test_distinct_people_look_distinct():
    images = [render_view(spec, VIEW_BY_KEY["front_3q"], px_per_cm=0.5).convert("RGBA") for spec in S.crowd(12, 3)]
    for a, b in itertools.combinations(images, 2):
        diff = ImageChops.difference(a, b).convert("L")
        mean = ImageStat.Stat(diff).mean[0]
        assert mean > 2.0


def test_a_taller_spec_is_a_taller_sprite():
    short = S.generate("average_male", 4, {"body": {"height_cm": 160.0}, "outfit": {"hat": "none"}, "hair": {"style": "buzz"}})
    tall = S.generate("average_male", 4, {"body": {"height_cm": 192.0}, "outfit": {"hat": "none"}, "hair": {"style": "buzz"}})
    hs = [(lambda b: b[3] - b[1])(_alpha_box(render_view(s, VIEW_BY_KEY["side"], px_per_cm=1.0))) for s in (short, tall)]
    assert hs[1] / hs[0] == pytest.approx(192.0 / 160.0, rel=0.04)


# ---- the rig ----------------------------------------------------------------------------------


def test_a_generated_character_binds_to_the_humanoid_rig_and_poses(tmp_path):
    from ambition_sprite2d_renderer.authoring.pose_audit import audit_document
    from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
    from ambition_sprite2d_renderer.devtools.svg_rig_tool import install_catalog, validate

    spec = S.generate("average_female", 21, {"outfit": {"outer": "coat", "outer_length": "knee"}})
    files = write_character(spec, tmp_path)
    assert set(files.rigs) == {v.key for v in VIEWS}
    install_catalog(files.svg_path, list(files.rigs.values()))
    assert validate(files.svg_path) == []
    for path in files.rigs.values():
        doc = RigDocument.load(path)
        assert {"pelvis", "torso", "head", "near_arm_u", "far_leg_foot"} <= {b["name"] for b in doc.bones}
        assert {"idle", "walk", "talk"} <= set(doc.clips)
        errors = [(f.animation, fd.code) for f in audit_document(doc).frames for fd in f.findings if fd.severity == "error"]
        assert errors == [], (path.name, errors)
    rc = RiggedCharacter(files.rigs)
    for row in ("idle", "walk", "talk", "walk_away", "turn"):
        frames = {r[0]: r[1] for r in rc.rows()}[row]
        a, b = rc.render_frame(row, 0, frames), rc.render_frame(row, frames // 2, frames)
        assert _alpha_box(a) is not None and _alpha_box(b) is not None
        assert ImageChops.difference(a, b).getbbox() is not None, row
