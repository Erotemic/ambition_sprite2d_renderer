"""Fighter posing contracts, using the shared body and rig rather than baked art."""
from __future__ import annotations

import json
import math

from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
from ambition_sprite2d_renderer.chargen import extras
from ambition_sprite2d_renderer.chargen.body import build
from ambition_sprite2d_renderer.chargen.draw import zmap_for
from ambition_sprite2d_renderer.chargen.drawkit import make_ctx
from ambition_sprite2d_renderer.chargen.geometry import VIEW_BY_KEY
from ambition_sprite2d_renderer.chargen.headdraw import head_parts
from ambition_sprite2d_renderer.chargen.motion import Kit, build_library, solve_clip
from ambition_sprite2d_renderer.chargen.pose3d import ViewSolver
from ambition_sprite2d_renderer.chargen.rig import CELL_H, CELL_W, PX_PER_CM, character_svg, draw_views, view_document
from ambition_sprite2d_renderer.chargen.svgout import Canvas
from ambition_sprite2d_renderer.chargen.spec import BASES, generate
from ambition_sprite2d_renderer.targets.characters import alice_v2
from ambition_sprite2d_renderer.targets.characters._alice_v2_gear import alice_parts
from ambition_sprite2d_renderer.targets.characters._alice_v2_motion import ROWS, alice_library


def test_braced_stance_transfers_weight_without_moving_ankle_targets():
    for base in BASES:
        k = Kit(build(generate(base, 7)))
        a, b = k.braced(weight=0.2), k.braced(weight=0.8)
        assert a.feet == b.feet
        assert b.root[2] > a.root[2]
        assert a.root[1] == b.root[1]
        assert all(not f.body for f in a.feet.values())
        assert a.feet['right'].at[2] > a.feet['left'].at[2]


def test_directional_smash_windups_match_release():
    fig = build(generate('average_male', 7))
    lib = build_library(fig)
    winds = []
    for direction in ('forward', 'up', 'down'):
        wind = lib[f'smash_charge_{direction}'].keys[0][1]
        assert wind == lib[f'smash_{direction}'].keys[1][1]
        winds.append(wind)
    assert len({w.hands['right'].at for w in winds}) == 3


def test_alice_grounded_staff_attacks_and_combat_rows(tmp_path):
    spec = alice_v2.load_spec()
    view = VIEW_BY_KEY['side']
    with extras.using(alice_parts):
        fig, views = draw_views(spec, [view])
        svg = character_svg(spec, [view]).replace(
            f'width="{CELL_W:g}mm" height="{CELL_H:g}mm" viewBox="0 0 {CELL_W:g} {CELL_H:g}"',
            f'width="{2 * CELL_W:g}mm" height="{CELL_H:g}mm" viewBox="0 0 {2 * CELL_W:g} {CELL_H:g}"', 1)
        path = tmp_path / 'alice.svg'
        path.write_text(svg, encoding='utf8')
        raw = view_document(spec, fig, views[0], path, tmp_path)
    lib = alice_library(fig)
    new_rows = ('fight_idle', 'fight_walk', 'smash_charge', 'smash_charge_forward', 'smash_charge_up', 'smash_charge_down')
    assert set(new_rows) <= set(ROWS) & set(lib)
    names = ('attack_down', 'smash_forward', 'smash_up', 'smash_down')
    solver = ViewSolver(fig, view, raw, PX_PER_CM)
    raw['clips'] = {name: solve_clip(lib[name], solver) for name in names}
    raw['frame'].update(width=alice_v2.FRAME_W, height=alice_v2.FRAME_H,
                        center_x=alice_v2.FRAME_CX, ground_y=alice_v2.FRAME_GROUND)
    rig_path = tmp_path / 'alice.rig.json'
    rig_path.write_text(json.dumps(raw), encoding='utf8')
    doc = RigDocument(raw, source_path=rig_path)
    pole = alice_v2._pole_local(str(rig_path))
    for name in names:
        for i in range(101):
            world, _ = doc.solve(name, i / 100)
            grip = world['near_grip']
            tip, butt = (grip.to_world(pole[key]) for key in ('tip', 'butt'))
            assert max(tip[1], butt[1]) <= alice_v2.FRAME_GROUND + 0.5, (name, i, tip, butt)
    for name, t, direction in [('smash_forward', 0.45, 1), ('smash_down', 0.4, 1), ('smash_down', 0.6, -1)]:
        world, _ = doc.solve(name, t)
        grip = world['near_grip']
        tip, butt = (grip.to_world(pole[key]) for key in ('tip', 'butt'))
        assert direction * (tip[0] - butt[0]) > 0
        assert abs(tip[1] - butt[1]) < 0.22 * math.dist(tip, butt), (name, t, tip, butt)


def test_turned_views_keep_the_near_arm_in_front_of_the_head():
    fig = build(generate('average_male', 7))
    view = VIEW_BY_KEY['side']
    ctx = make_ctx(fig, view, Canvas(1.0, (0.0, 0.0)))
    zmap = zmap_for(view, tucked=False)
    near_arm = max(z for name, z in zmap.items() if name.startswith('near_arm'))
    head_top = max(part.z for part in head_parts(ctx))
    assert near_arm > head_top


def test_smash_rows_show_real_foot_pivot_and_roll_through():
    fig = build(generate('average_male', 7))
    lib = build_library(fig)
    wind = lib['smash_forward'].keys[1][1]
    hit = lib['smash_forward'].keys[2][1]
    follow = lib['smash_forward'].keys[3][1]
    assert wind.feet['left'].toe < -10
    assert hit.feet['left'].toe < wind.feet['left'].toe
    assert hit.feet['left'].at[1] < wind.feet['left'].at[1]
    assert follow.feet['left'].at[1] > hit.feet['left'].at[1]
    assert hit.feet['right'].toe > wind.feet['right'].toe


def test_alice_staff_attacks_use_the_same_pivot_language():
    fig = build(generate('average_female', 7))
    lib = alice_library(fig)
    wind = lib['attack_side'].keys[1][1]
    hit = lib['attack_side'].keys[2][1]
    follow = lib['attack_side'].keys[3][1]
    assert wind.feet['left'].toe < -10
    assert hit.feet['left'].toe < wind.feet['left'].toe
    assert hit.feet['left'].at[1] < wind.feet['left'].at[1]
    assert follow.feet['left'].at[1] > hit.feet['left'].at[1]
    assert hit.feet['right'].toe > wind.feet['right'].toe
