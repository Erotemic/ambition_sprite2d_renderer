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
from pathlib import Path

import pytest
from PIL import Image, ImageChops, ImageStat

from ambition_sprite2d_renderer.chargen import spec as S
from ambition_sprite2d_renderer.chargen.geometry import VIEW_BY_KEY, VIEWS
from ambition_sprite2d_renderer.chargen.rig import character_svg, write_character
from ambition_sprite2d_renderer.chargen.sheets import RiggedCharacter, render_view


#: The example spec of the alligator head and the geisha wardrobe (not a game target).
GATOR_GEISHA = Path(S.__file__).resolve().parents[1] / "data" / "chargen_examples" / "gator_geisha.chargen.yaml"


def _alpha_box(img: Image.Image):
    return img.getchannel("A").getbbox()


def _differs(a: Image.Image, b: Image.Image) -> bool:
    """Whether two renders differ in any pixel (colour or coverage; an RGBA
    difference's own bbox reads only its alpha)."""
    return ImageChops.difference(a.convert("RGBA"), b.convert("RGBA")).getbbox(alpha_only=False) is not None


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
    for row in ("idle", "walk", "talk", "walk_away", "turnaround"):
        frames = {r[0]: r[1] for r in rc.rows()}[row]
        a, b = rc.render_frame(row, 0, frames), rc.render_frame(row, frames // 2, frames)
        assert _alpha_box(a) is not None and _alpha_box(b) is not None
        assert _differs(a, b), row


# ---- the parameterized rig, the motion library, faces, wardrobe, held items ----------------------

_REST = {"rest": {"loop": False, "frames": 1, "duration_ms": 100, "channels": {}}}


def _rest_rigs(spec, tmp_path):
    from ambition_sprite2d_renderer.chargen.rig import build_rigs

    tmp_path.mkdir(parents=True, exist_ok=True)
    svg = tmp_path / "c.svg"
    svg.write_text(character_svg(spec), encoding="utf8")
    return build_rigs(spec, svg, tmp_path, clips=lambda fig, view, doc: dict(_REST))


def test_the_rig_derives_from_the_spec_for_many_seeds(tmp_path):
    from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
    from ambition_sprite2d_renderer.chargen.rig import CELL_H, CELL_W

    specs = S.crowd(3, 31) + [S.crowd(1, 32 + i, species=sp)[0] for i, sp in enumerate(("horse", "dog", "cat", "bird", "sea_lion", "alligator"))]
    for n, spec in enumerate(specs):
        rigs = _rest_rigs(spec, tmp_path / str(n))
        for view, path in rigs.items():
            doc = RigDocument.load(path)
            bones = {b["name"]: b for b in doc.bones}
            parts = {p["name"]: p for p in doc.data["parts"]}
            assert len(parts) == len(doc.data["parts"]), (spec.name, view)
            assert all(p["bone"] in bones for p in parts.values()), (spec.name, view)
            # Each hand is a fist on a grip bone: the item's socket.
            for depth in ("near", "far"):
                assert bones[f"{depth}_grip"]["parent"] == f"{depth}_arm_hand"
                assert parts[f"{depth}_hand"]["bone"] == f"{depth}_grip"
            assert all(c["pitch_mode"] == "follow_lower" for c in doc.ik_chains)
            # Every pivot is in the view's own cell (pivots are read from the
            # view's pixel origin, not the whole sheet's).
            for p in parts.values():
                assert 0.0 <= p["pivot"][0] <= CELL_W and 0.0 <= p["pivot"][1] <= CELL_H, (spec.name, view, p["name"], p["pivot"])
            if n == 0 and view in ("front", "side"):
                # The drawing lands on its skeleton: centred in the frame, on the ground.
                img = doc.render_frame("rest", 0, 1)
                box = _alpha_box(img)
                k = int(doc.frame.get("render_scale", 1))
                centre = float(doc.frame["center_x"]) * k
                assert abs((box[0] + box[2]) / 2 - centre) < 0.12 * img.width, (spec.name, view, box)
                assert abs(box[3] - float(doc.frame["ground_y"]) * k) < 0.03 * img.height, (spec.name, view, box)


@pytest.mark.parametrize("spec", [
    S.generate("average_female", 21, {"outfit": {"outer": "robe"}}),
    S.crowd(2, 1, species="horse")[1],
    S.crowd(2, 2, species="dog")[1],
    S.crowd(2, 3, species="cat")[1],
    S.crowd(2, 4, species="bird")[1],
    S.crowd(2, 5, species="sea_lion")[1],
    S.generate("broad_male", 7, {"outfit": {"outer": "field_jacket", "outer_open": False, "hat": "helmet", "accessories": ["webbing"]}}),
    S.generate("broad_female", 61, {"family": "crew", "hair": {"style": "bun"}, "outfit": {
        "outer": "field_jacket", "outer_open": False, "hat": "campaign", "shoes": "boots", "accessories": ["webbing"], "wardrobe": ["hat:helmet"]}}),
    S.CharacterSpec.load(GATOR_GEISHA),
], ids=["robe", "horse", "dog", "cat", "bird", "sea_lion", "soldier", "crew_soldier", "gator_geisha"])
def test_every_library_clip_poses_without_audit_errors_in_every_view(spec, tmp_path):
    from ambition_sprite2d_renderer.authoring.pose_audit import audit_document
    from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
    from ambition_sprite2d_renderer.chargen.body import build
    from ambition_sprite2d_renderer.chargen.motion import build_library

    files = write_character(spec, tmp_path)
    names = set(build_library(build(spec)))
    for view, path in files.rigs.items():
        doc = RigDocument.load(path)
        assert set(doc.clips) == names
        errors = sorted({(f.animation, fd.code) for f in audit_document(doc).frames for fd in f.findings if fd.severity == "error"})
        assert errors == [], (view, errors)
        # A held item rides the fist: the grip keeps its place on the hand in
        # every frame of every clip.
        reach = None
        for name, clip in doc.clips.items():
            for i in range(int(clip["frames"])):
                world, _ = doc.solve(name, i / max(1, int(clip["frames"])))
                for depth in ("near", "far"):
                    g, h = world[f"{depth}_grip"].origin, world[f"{depth}_arm_hand"].origin
                    d = ((g[0] - h[0]) ** 2 + (g[1] - h[1]) ** 2) ** 0.5
                    reach = reach or {}
                    assert abs(d - reach.setdefault(depth, d)) < 1e-3, (view, name, i, depth)


def test_expressions_compose_and_show_only_from_the_front(tmp_path):
    from ambition_sprite2d_renderer.chargen import face as F

    for a, b in itertools.combinations(F.EMOTIONS, 2):
        mixed = F.compose(F.EMOTIONS[a], F.EMOTIONS[b], F.LOOKS["look_left"])
        assert F.clamp(mixed) == mixed
    names = set(F.all_face_channel_names())
    for f in F.FACES:
        for vis in F.VISEMES:
            ch = F.face_channels(f, vis, blink=1.0)
            assert set(ch) <= names
            # One eyes, one brows and one mouth part show at a time.
            shown = {n for n in names if ch.get(n, 1.0 if "__neutral" in n and not n.startswith("face_mouth__neutral__") or
                                         n == F.mouth_part("neutral") + "_vis" else 0.0) >= 0.5}
            assert len([n for n in shown if n.startswith("face_eyes__")]) == 1, (f, vis)
            assert len([n for n in shown if n.startswith("face_mouth__")]) == 1, (f, vis)
    spec = S.crowd(1, 4)[0]
    for view in ("front", "front_3q", "side"):
        neutral = render_view(spec, VIEW_BY_KEY[view], 2.0)
        for f in ("happy", "angry", "surprised"):
            other = render_view(spec, VIEW_BY_KEY[view], 2.0, state=F.face_channels(f, "a"))
            assert _differs(neutral, other), (view, f)
    back = render_view(spec, VIEW_BY_KEY["back"], 2.0)
    assert not _differs(back, render_view(spec, VIEW_BY_KEY["back"], 2.0, state=F.face_channels("angry", "o")))


def test_wardrobe_alternates_swap_as_features_and_layer_by_slot():
    from ambition_sprite2d_renderer.chargen.rig import draw_views
    from ambition_sprite2d_renderer.chargen.wear import LAYER

    spec = S.generate("average_male", 8, {"outfit": {"top": "shirt", "outer": "none", "hat": "cap",
                                                      "wardrobe": ["outer:coat", "hat:top_hat", "legwear:skirt", "top:sweater"]}})
    assert S.validate(spec) == []
    _fig, drawn = draw_views(spec)
    for dv in drawn:
        names = [p.name for p in dv.parts]
        assert len(names) == len(set(names))
        for item in spec.outfit.wardrobe:
            slot, _, kind = item.partition(":")
            alts = [p for p in dv.parts if p.name.endswith("@" + kind)]
            if dv.view.key != "back" or slot != "top":
                assert alts, (dv.view.key, item)
            assert all(p.feature == item for p in alts)
        # On one bone, an outer layer draws over a top, a top over legwear.
        for bone in ("torso", "pelvis"):
            z = {}
            for p in dv.parts:
                if p.bone == bone and p.feature and ":" in p.feature:
                    z.setdefault(p.feature.split(":")[0], []).append(p.z)
            for lo, hi in (("legwear", "top"), ("top", "outer")):
                if lo in z and hi in z and bone == "torso":
                    assert max(z[lo]) < min(z[hi]), (dv.view.key, bone, z)
    assert LAYER["legwear"] < LAYER["top"] < LAYER["outer"]
    worn = render_view(spec, VIEW_BY_KEY["front_3q"], 0.8)
    swapped = render_view(spec, VIEW_BY_KEY["front_3q"], 0.8, features={"outer:coat": True, "hat:cap": False, "hat:top_hat": True})
    assert _differs(worn, swapped)


def test_every_species_head_draws_in_every_view():
    from ambition_sprite2d_renderer.chargen.rig import draw_views

    for i, species in enumerate(S.SPECIES):
        spec = S.crowd(1, 50 + i, species=species)[0]
        assert spec.head.species == species
        _fig, drawn = draw_views(spec)
        for dv in drawn:
            assert any(p.name == "head" for p in dv.parts), (species, dv.view.key)
            assert _alpha_box(render_view(spec, dv.view, 0.5)) is not None
        if species == "bird":
            # From behind, the beak is drawn under the head, not over it.
            back = {p.name for p in drawn[-1].parts}
            assert "head_behind" in back


def test_every_grip_class_poses_its_item_clips_cleanly_and_points_the_item(tmp_path):
    import math
    from functools import partial

    from ambition_sprite2d_renderer.authoring.pose_audit import audit_document
    from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
    from ambition_sprite2d_renderer.chargen.motion import GRIPS, library_clips
    from ambition_sprite2d_renderer.chargen.rig import build_rigs

    spec = S.generate("average_male", 6, {"outfit": {"outer": "none"}})
    names = ["item_hold", "item_grip", "item_hold_crouch", "item_pickup", "item_throw", "item_drop", "item_swing", "item_swing_up",
             "item_swing_down", "item_swing_back"]
    svg = tmp_path / "c.svg"
    svg.write_text(character_svg(spec), encoding="utf8")
    for grip in GRIPS:
        rigs = build_rigs(spec, svg, tmp_path / grip, clips=partial(library_clips, names=names, grip=grip), grip=grip)
        for view, path in rigs.items():
            doc = RigDocument.load(path)
            errors = sorted({(f.animation, fd.code) for f in audit_document(doc).frames for fd in f.findings if fd.severity == "error"})
            assert errors == [], (grip, view, errors)
        side = RigDocument.load(rigs["side"])
        world, _ = side.solve("item_hold", 0.0)
        rest = next(p for p in side.data["parts"] if p["name"] == "near_hand")["rest_angle"]
        # The item's screen angle: forward and 24 deg up when the hand is unturned.
        item = -24.0 + (world["near_grip"].angle - rest)
        want = {"gun": 0.0, "staff": -88.0, "blade": -62.0}.get(grip)
        if want is not None:
            assert abs((item - want + 180.0) % 360.0 - 180.0) < 12.0, (grip, item)
        if grip == "two_handed":
            # The far fist closes on the item's line.
            g, f = world["near_grip"].origin, world["far_grip"].origin
            d = (math.cos(math.radians(item)), math.sin(math.radians(item)))
            off_line = abs((f[0] - g[0]) * d[1] - (f[1] - g[1]) * d[0])
            assert off_line < 3.0, off_line


def test_the_head_stays_on_its_neck_and_the_audit_says_when_it_does_not(tmp_path):
    """Every view declares its head-on-neck continuity; a head that comes
    off its neck (moved, or turned past what a neck allows) is an audit
    error, and the rest pose is clean."""
    import copy

    from ambition_sprite2d_renderer.authoring.pose_audit import audit_document
    from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument

    spec = S.crowd(2, 1, species="horse")[1]
    rigs = _rest_rigs(spec, tmp_path)
    for view, path in rigs.items():
        data = RigDocument.load(path).data
        assert [c["name"] for c in data["continuity"]] == ["head_on_neck", "neck_under_head"], view

        def gaps(channels):
            d = copy.deepcopy(data)
            d["clips"] = {"probe": {"loop": False, "frames": 1, "duration_ms": 100,
                                    "channels": {k: {"const": v} for k, v in channels.items()}}}
            return [fd for f in audit_document(RigDocument(d)).frames for fd in f.findings if fd.code == "part_continuity_gap"]

        assert gaps({}) == [], view
        assert gaps({"head": 75.0}), (view, "a head turned past what a neck allows")
        assert gaps({"bone.head.y": -12.0}), (view, "a head lifted off its neck")


# ---- military wardrobe ----------------------------------------------------------------------------

MILITARY_HATS = ("helmet", "beret", "garrison_cap", "peaked_cap", "campaign")


def _hat_heads():
    """A human, a horse and a male sea lion (whose crest rises above the crown)."""
    return [("human", S.generate("average_male", 3, {"hair": {"style": "short"}})),
            ("horse", S.generate("average_male", 3, {"head": {"species": "horse"}})),
            ("sea_lion", S.generate("broad_male", 3, {"head": {"species": "sea_lion"}}))]


@pytest.mark.parametrize("hat", MILITARY_HATS)
def test_military_hats_draw_on_every_species_head_in_every_view(hat):
    from ambition_sprite2d_renderer.chargen.body import build
    from ambition_sprite2d_renderer.chargen.rig import GROUND, UNIT, draw_views

    for label, head in _hat_heads():
        spec = S.generate(head.base, head.seed, {"head": {"species": head.head.species}, "outfit": {"hat": hat, "hat_color": "#5b6136"}})
        bare = S.generate(head.base, head.seed, {"head": {"species": head.head.species}, "outfit": {"hat": "none"}})
        assert S.validate(spec) == []
        _fig, drawn = draw_views(spec)
        for dv in drawn:
            assert any(p.name == f"hat_{hat}" and p.feature == f"hat:{hat}" for p in dv.parts), (label, dv.view.key)
        sk_top = build(bare).skull.top
        for key in ("front", "side", "back"):
            a, b = render_view(spec, VIEW_BY_KEY[key], 1.0), render_view(bare, VIEW_BY_KEY[key], 1.0)
            hat_top = ImageChops.difference(a, b).getbbox(alpha_only=False)[1]
            # The hat covers the top of the skull (a sea lion's crest too):
            # it reaches above it on screen.
            skull_top = (GROUND + sk_top * UNIT) / UNIT
            assert hat_top < skull_top, (label, key, hat_top, skull_top)


def test_the_field_jacket_webbing_and_dog_tags_draw_in_every_view():
    from ambition_sprite2d_renderer.chargen.rig import draw_views

    for open_ in (False, True):
        spec = S.generate("slim_female", 4, {"outfit": {"outer": "field_jacket", "outer_open": open_, "top": "tshirt",
                                                         "accessories": ["webbing", "dog_tags"], "accent_color": "#b8913e"}})
        assert S.validate(spec) == []
        _fig, drawn = draw_views(spec)
        for dv in drawn:
            feats = {p.feature for p in dv.parts}
            assert {"outer:field_jacket", "acc:webbing"} <= feats, (open_, dv.view.key)
            assert any(p.feature == "outer:field_jacket" and p.bone.endswith("arm_l") for p in dv.parts), dv.view.key
            # The webbing is worn over the jacket.
            jacket = max(p.z for p in dv.parts if p.feature == "outer:field_jacket" and p.bone == "torso")
            assert next(p.z for p in dv.parts if p.name == "torso__webbing") > jacket
        front = render_view(spec, VIEW_BY_KEY["front"], 1.0)
        plain = render_view(S.generate("slim_female", 4, {"outfit": {"outer": "jacket", "outer_open": open_, "top": "tshirt",
                                                                      "accessories": []}}), VIEW_BY_KEY["front"], 1.0)
        assert _differs(front, plain)


def test_military_items_are_wardrobe_alternates_and_accessories_add():
    from ambition_sprite2d_renderer.chargen.rig import draw_views

    spec = S.generate("average_male", 9, {"outfit": {"outer": "none", "hat": "beret", "accessories": ["belt"],
                                                      "wardrobe": ["hat:helmet", "outer:field_jacket", "acc:webbing", "hat:peaked_cap"]}})
    assert S.validate(spec) == []
    _fig, drawn = draw_views(spec)
    for dv in drawn:
        for item in spec.outfit.wardrobe:
            kind = item.partition(":")[2]
            alts = [p for p in dv.parts if p.name.endswith("@" + kind)]
            assert alts and all(p.feature == item for p in alts), (dv.view.key, item)
    worn = render_view(spec, VIEW_BY_KEY["front_3q"], 0.8)
    kitted = render_view(spec, VIEW_BY_KEY["front_3q"], 0.8, features={"acc:webbing": True, "acc:belt": True})
    assert _differs(worn, kitted)


def test_the_iron_bastion_soldiers_are_valid_and_distinct():
    from ambition_sprite2d_renderer.targets.characters.townsfolk import SPECS, load

    paths = sorted(SPECS.glob("tower_*.chargen.yaml"))
    assert len(paths) >= 7
    specs = []
    for path in paths:
        spec, game = load(path)
        assert S.validate(spec) == [], path.name
        assert game["character_id"] == "npc_" + path.name.removesuffix(".chargen.yaml")
        # The garrison is drawn in the look of the cryptography crew.
        assert spec.family == "crew", path.name
        specs.append(spec)
    for a, b in itertools.combinations(specs, 2):
        assert (a.outfit.hat, a.outfit.hat_color, a.outfit.outer, a.base) != (b.outfit.hat, b.outfit.hat_color, b.outfit.outer, b.base)


# ---- families ----------------------------------------------------------------------------------


def test_a_family_is_a_spec_field_that_round_trips_and_changes_no_drawn_number(tmp_path):
    crew = S.generate("average_male", 12, {"family": "crew"})
    plain = S.generate("average_male", 12)
    assert crew.family == "crew" and plain.family == "standard"
    assert S.validate(crew) == []
    # The seed draws the same person; the family only changes the drawing.
    assert crew.body == plain.body and crew.face == plain.face and crew.outfit == plain.outfit
    assert S.CharacterSpec.from_json(crew.to_json()) == crew
    assert S.CharacterSpec.load(crew.save(tmp_path / "c.chargen.yaml")) == crew
    # A standard record does not write its family, so it stays as it was.
    assert "family" not in plain.to_dict() and crew.to_dict()["family"] == "crew"
    with pytest.raises(ValueError, match="family"):
        S.generate("average_male", 12, {"family": "nope"})
    bad = S.generate("average_male", 12)
    bad.family = "nope"
    assert any(e.startswith("family") for e in S.validate(bad))
    assert all(s.family == "crew" for s in S.crowd(3, 4, family="crew"))


def test_the_standard_family_is_the_default_and_no_style_leaks_between_drawings():
    from ambition_sprite2d_renderer.chargen.svgout import STANDARD, style

    spec = S.generate("slim_female", 8)
    before = character_svg(spec)
    assert character_svg(S.generate("slim_female", 8, {"family": "standard"})) == before
    crew = character_svg(S.generate("slim_female", 8, {"family": "crew"}))
    assert crew != before
    # The crew style is active only while a crew view is drawn.
    assert style() is STANDARD
    assert character_svg(spec) == before


def test_the_crew_family_draws_its_look_in_every_view():
    import re

    from ambition_sprite2d_renderer.chargen.body import build
    from ambition_sprite2d_renderer.chargen.family import CREW_INK, FAMILIES
    from ambition_sprite2d_renderer.chargen.rig import UNIT, draw_views

    plain = S.generate("average_male", 14, {"outfit": {"hat": "peaked_cap", "accessories": ["webbing"]}})
    crew = S.generate("average_male", 14, {"family": "crew", "outfit": {"hat": "peaked_cap", "accessories": ["webbing"]}})
    fp, fc = build(plain), build(crew)
    # A shorter leg, a wider head and thicker limbs than the standard body.
    assert fc.y_hip > fp.y_hip and fc.skull.section(fc.fy(0.4)).rx > fp.skull.section(fp.fy(0.4)).rx
    assert fc.arm_r[2] > fp.arm_r[2]
    _fig, drawn = draw_views(crew)
    _fig, base = draw_views(plain)
    outline = 2 * FAMILIES["crew"].style.outline * UNIT
    for dv, dp in zip(drawn, base):
        assert {p.name for p in dv.parts} == {p.name for p in dp.parts}, dv.view.key
        inks = [el for p in dv.parts for el in p.els if el.stroke == CREW_INK]
        assert inks and max(el.width for el in inks) >= outline - 1e-6, dv.view.key
        assert _alpha_box(render_view(crew, dv.view, 0.5)) is not None
    assert not re.search(CREW_INK, character_svg(plain))


@pytest.mark.parametrize("species", S.SPECIES)
def test_every_species_head_and_hat_draws_in_the_crew_family(species):
    from ambition_sprite2d_renderer.chargen.rig import draw_views

    for i, hat in enumerate(S.HATS):
        spec = S.generate("average_female" if i % 2 else "broad_male", 70 + i, {"family": "crew", "head": {"species": species},
                                                                                 "outfit": {"hat": hat}})
        _fig, drawn = draw_views(spec)
        for dv in drawn:
            names = {p.name for p in dv.parts}
            assert "head" in names and (hat == "none" or f"hat_{hat}" in names), (species, hat, dv.view.key)


# ---- the alligator head and the geisha wardrobe --------------------------------------------------


def test_the_alligator_head_draws_in_every_view_with_its_teeth_and_faces():
    from ambition_sprite2d_renderer.chargen import face as F
    from ambition_sprite2d_renderer.chargen.rig import draw_views

    for base in ("slim_female", "broad_male"):
        spec = S.generate(base, 5, {"head": {"species": "alligator"}, "outfit": {"hat": "none"}})
        assert S.validate(spec) == []
        _fig, drawn = draw_views(spec)
        for dv in drawn:
            names = {p.name for p in dv.parts}
            assert "head" in names, (base, dv.view.key)
            if dv.view.key != "back":
                # Shut, the upper teeth show along the jaw line.
                mouth = next(p for p in dv.parts if p.name == F.mouth_part("neutral", "rest"))
                assert any(el.fill == "#efe8d2" for el in mouth.els), (base, dv.view.key)
        side = VIEW_BY_KEY["side"]
        neutral = render_view(spec, side, 2.0)
        for f, vis in (("happy", "rest"), ("neutral", "a"), ("angry", "rest")):
            assert _differs(neutral, render_view(spec, side, 2.0, state=F.face_channels(f, vis))), (base, f, vis)
        assert _differs(neutral, render_view(spec, side, 2.0, state=F.face_channels("neutral", blink=1.0)))


def test_the_geisha_wardrobe_draws_in_every_view_and_its_fields_are_optional(tmp_path):
    from ambition_sprite2d_renderer.chargen.rig import draw_views

    spec = S.CharacterSpec.load(GATOR_GEISHA)
    assert S.validate(spec) == []
    assert S.CharacterSpec.load(spec.save(tmp_path / "g.chargen.yaml")) == spec
    _fig, drawn = draw_views(spec)
    for dv in drawn:
        feats = {p.feature for p in dv.parts if p.feature}
        assert {"outer:kimono", "acc:obi", "hair:nihongami", "footwear:geta"} <= feats, dv.view.key
        bones = {p.bone for p in dv.parts if p.feature == "outer:kimono"}
        assert {"torso", "near_arm_u", "near_arm_l", "near_leg_u", "near_leg_l"} <= bones, dv.view.key
        assert any(p.name == "torso__obi_knot" for p in dv.parts), dv.view.key
    # The knot is under the body when the back is turned away.
    z = {dv.view.key: next(p.z for p in dv.parts if p.name == "torso__obi_knot") for dv in drawn}
    assert z["front"] < 2.0 < z["back"]
    # Each part changes the drawing (worn against taken off).
    plain = S.CharacterSpec.load(GATOR_GEISHA)
    plain.outfit.outer, plain.outfit.accessories, plain.hair.style, plain.outfit.shoes = "none", [], "bald", "shoes"
    plain.face.makeup = "none"
    for key in ("front", "side", "back"):
        assert _differs(render_view(spec, VIEW_BY_KEY[key], 0.8), render_view(plain, VIEW_BY_KEY[key], 0.8)), key
    # A record writes the new fields only when they are not at their default.
    d = S.generate("average_male", 3).to_dict()
    assert "makeup" not in d["face"] and "ornaments" not in d["hair"] and "geta_height" not in d["outfit"]
    assert spec.to_dict()["face"]["makeup"] == "geisha"
    bad = S.CharacterSpec.load(GATOR_GEISHA)
    bad.outfit.wardrobe = ["footwear:shoes"]
    assert any("geta" in e for e in S.validate(bad))


def test_geta_raise_the_figure_and_keep_the_feet_on_the_ground(tmp_path):
    from functools import partial

    from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
    from ambition_sprite2d_renderer.chargen.body import build
    from ambition_sprite2d_renderer.chargen.motion import library_clips
    from ambition_sprite2d_renderer.chargen.rig import build_rigs

    over = {"outer": "none", "bottom": "trousers", "hat": "none"}
    shoes = S.generate("slim_female", 1, {"outfit": dict(over, shoes="shoes")})
    geta = S.generate("slim_female", 1, {"outfit": dict(over, shoes="geta", geta_height=10.0)})
    fs, fg = build(shoes), build(geta)
    assert fg.sole_y == -10.0 and fg.crown == pytest.approx(fs.crown - 10.0)
    for key in ("front", "side", "back"):
        bs, bg = (_alpha_box(render_view(sp, VIEW_BY_KEY[key], 1.0)) for sp in (shoes, geta))
        # The same ground line; the figure is the geta's height taller.
        assert abs(bs[3] - bg[3]) <= 1, key
        assert (bs[3] - bs[1]) + 10.0 - 2 <= bg[3] - bg[1] <= (bs[3] - bs[1]) + 10.0 + 2, key
    names = ["idle", "walk", "crouch", "prone", "sit_down"]
    lows = {}
    for label, sp in (("shoes", shoes), ("geta", geta)):
        svg = tmp_path / f"{label}.svg"
        svg.write_text(character_svg(sp), encoding="utf8")
        rigs = build_rigs(sp, svg, tmp_path / label, clips=partial(library_clips, names=names))
        for view in ("side", "front"):
            doc = RigDocument.load(rigs[view])
            for n in names:
                frames = int(doc.clips[n]["frames"])
                lows[(label, view, n)] = [_alpha_box(doc.render_frame(n, i, frames))[3] for i in range(frames)]
    # In every frame the geta stand where the shoes stand: on the ground, and
    # a body on the ground lies on it, not on the geta's height.
    for (label, view, n), bottoms in lows.items():
        if label == "geta":
            ref = lows[("shoes", view, n)]
            assert max(abs(a - b) for a, b in zip(bottoms, ref)) <= 2, (view, n, bottoms, ref)


def test_no_hat_or_wig_covers_the_eyes():
    """A hat or a wig never paints over an eye, on any head, in the views
    where the eyes face the camera. An eye pixel (inside the head's outline)
    is covered when it shows on the bare head and its colour changes when
    the item is put on (a dark lid line over dark hair does not change, and
    is not counted)."""
    import numpy as np

    from ambition_sprite2d_renderer.chargen.face import eyes_part

    hide_eyes = {eyes_part("neutral") + "_vis": 0}

    def px(spec, view, state=None):
        return np.asarray(render_view(spec, VIEW_BY_KEY[view], 3.0, state=state).convert("RGBA"), dtype=np.int16)

    def changed(a, b):
        return np.abs(a - b).sum(axis=2) > 60

    bad = []
    for species in S.SPECIES:
        bare_over = {"head": {"species": species}, "hair": {"style": "bald"}, "outfit": {"hat": "none"}}
        bare = S.generate("slim_female", seed=3, overrides=bare_over)
        looks = [("nihongami", {"hair": {"style": "nihongami"}})] + [(h, {"outfit": {"hat": h}}) for h in S.HATS if h != "none"]
        for view in ("front", "front_3q", "side"):
            with_eyes, no_eyes = px(bare, view), px(bare, view, hide_eyes)
            # Inside the head's outline only: an edge pixel of an eye on the
            # outline also shows what is behind the head.
            eye = changed(with_eyes, no_eyes) & (with_eyes[..., 3] == 255) & (no_eyes[..., 3] == 255)
            # The eye shows in this view at all (not edge-on, not smeared).
            assert eye.sum() >= 10, (species, view, int(eye.sum()))
            for name, over in looks:
                worn = S.generate("slim_female", seed=3, overrides={k: {**v, **over.get(k, {})} for k, v in bare_over.items()})
                covered = (eye & changed(with_eyes, px(worn, view))).sum() / eye.sum()
                if covered > 0.05:
                    bad.append((species, name, view, round(float(covered), 2)))
    assert not bad, bad
