"""Contracts at the multiview combat publication boundary."""
from __future__ import annotations

import json
import math

from ambition_sprite2d_renderer.chargen import extras
from ambition_sprite2d_renderer.chargen.body import build
from ambition_sprite2d_renderer.chargen.combat_turn import view_at
from ambition_sprite2d_renderer.chargen.geometry import VIEW_BY_KEY, VIEWS
from ambition_sprite2d_renderer.chargen.motion import Kit, build_library, solve_clip
from ambition_sprite2d_renderer.chargen.pose3d import ViewSolver
from ambition_sprite2d_renderer.chargen.rig import PX_PER_CM, character_svg, draw_views, view_document
from ambition_sprite2d_renderer.chargen.spec import generate
from ambition_sprite2d_renderer.targets.characters import alice_v2
from ambition_sprite2d_renderer.targets.characters._alice_v2_motion import alice_library


def test_alice_foreground_arm_includes_every_sleeve_hand_and_prop():
    with extras.using(alice_v2.alice_parts):
        _, drawn = draw_views(alice_v2.load_spec())
    for dv in drawn:
        head = max(p.z for p in dv.parts if p.bone == 'head')
        near = [p for p in dv.parts if p.bone.startswith('near_arm_') or p.bone == 'near_grip']
        assert min(p.z for p in near) > head, dv.view.key
        z = {p.name: p.z for p in dv.parts}
        assert z['near_arm_l'] < z['pole'] < z['near_hand']
        assert z['near_hand_open'] == z['near_hand']
        assert z['far_arm_l'] < head


def test_turn_tracks_keep_gameplay_facing_and_charge_matches_load():
    lib = build_library(build(generate('average_male', 7)))
    path = {'publish_turn': lib['smash_forward'].turn}
    views = ('front_3q', 'side', 'back_3q')
    assert [view_at(path, t, 'side', views) for t in (0., .27, .45, .65, 1.)] == [
        'side', 'front_3q', 'side', 'back_3q', 'side']
    assert view_at(path, .27, 'side', ['side']) == 'side'
    for direction in ('forward', 'up', 'down'):
        release = lib[f'smash_{direction}']
        charge = lib[f'smash_charge_{direction}']
        assert charge.turn[0][1] == release.turn[1][1]
    assert not lib['walk'].turn
    assert not lib['idle'].turn


def test_fixed_stage_root_and_sole_contact(tmp_path):
    spec = generate('average_male', 7)
    views = [VIEW_BY_KEY[n] for n in ('side', 'front_3q', 'back_3q')]
    fig, drawn = draw_views(spec, views)
    path = tmp_path / 'body.svg'
    path.write_text(character_svg(spec, views))
    k = Kit(fig)
    pose = k.braced(front=.30, rear=-.30, weight=.70, drop=.12, front_toe=0, rear_toe=-25)
    roots = []
    for dv in drawn:
        raw = view_document(spec, fig, dv, path, tmp_path)
        solver = ViewSolver(fig, dv.view, raw, PX_PER_CM)
        f = solver.solve(pose, stage=True)
        roots.append(f['root_x'])
        from ambition_sprite2d_renderer.chargen.wear import foot_points
        from ambition_sprite2d_renderer.chargen.pose3d import _rot2
        from ambition_sprite2d_renderer.authoring.rigdoc import RigDocument
        doc = RigDocument(raw)
        world, _ = doc.solve('', 0., sampled_channels=f)
        for depth, side in (('near','right'),('far','left')):
            bone = world[f'{depth}_leg_foot']
            rest = solver.rest_world[f'{depth}_leg_foot']
            ankle = dv.view.project(fig.joints[f'{side}_ankle'])
            sole, _, _ = foot_points(fig, side, 1.14 if spec.outfit.shoe_style == 'chunky' else 1.0)
            points = [_rot2(tuple((x-y)*PX_PER_CM for x,y in zip(dv.view.project(q),ankle)), bone.angle-rest.angle) for q in sole]
            bottom = max(bone.origin[1]+p[1] for p in points)
            assert abs(bottom - raw['frame']['ground_y']) < .75, (dv.view.key, depth, bottom)
    assert max(roots)-min(roots) < 1e-9


def test_alice_turn_sampling_uses_selected_weapon_geometry(tmp_path):
    spec = alice_v2.load_spec()
    views = [VIEW_BY_KEY[n] for n in ('front_3q','side','back_3q')]
    with extras.using(alice_v2.alice_parts):
        fig, drawn = draw_views(spec, views)
        svg = character_svg(spec, views)
    from ambition_sprite2d_renderer.chargen.rig import CELL_W, CELL_H
    w = CELL_W * len(views)
    svg = svg.replace(f'width="{w:g}mm" height="{CELL_H:g}mm" viewBox="0 0 {w:g} {CELL_H:g}"',
                      f'width="{w+CELL_W:g}mm" height="{CELL_H:g}mm" viewBox="0 0 {w+CELL_W:g} {CELL_H:g}"', 1)
    path = tmp_path / 'alice.svg'; path.write_text(svg)
    lib = alice_library(fig)
    names = ('smash_forward', 'smash_up', 'smash_down', 'dash_attack')
    rigs = {}
    for dv in drawn:
        raw = view_document(spec, fig, dv, path, tmp_path)
        solver = ViewSolver(fig, dv.view, raw, PX_PER_CM)
        raw['clips'] = {n: solve_clip(lib[n], solver) for n in names}
        raw['chargen']['publish_views'] = {n: lib[n].view for n in names}
        raw['frame'].update(width=alice_v2.FRAME_W, height=alice_v2.FRAME_H,
                            center_x=alice_v2.FRAME_CX, ground_y=alice_v2.FRAME_GROUND)
        rig = tmp_path / f'{dv.view.key}.rig.json'
        rig.write_text(json.dumps(raw)); rigs[dv.view.key] = rig
    sheet = alice_v2.AliceSheet(rigs, rows=names)
    assert sheet.doc_at('smash_forward', .27)[0].data['chargen']['view'] == 'front_3q'
    assert sheet.doc_at('smash_forward', .65)[0].data['chargen']['view'] == 'back_3q'
    hits = alice_v2.attack_hitboxes(sheet)
    for name, count, _ in sheet.rows():
        for i in range(101):
            t=i/100
            doc, path = sheet.doc_at(name, t)
            world, _ = doc.solve(name, t)
            g = world['near_grip']
            pole = alice_v2._pole_local(path)
            assert max(g.to_world(pole[key])[1] for key in ('tip','butt')) <= alice_v2.FRAME_GROUND + .5
        active=[]
        for i in range(count):
            doc, path=sheet.doc_at(name, i/(count-1))
            world, p=doc.solve(name,i/(count-1))
            if max(p.get('fx.spark',0.),p.get('fx.trail',0.)) < .5:
                continue
            active.append(i)
            tip=world['near_grip'].to_world(alice_v2._pole_local(path)['tip'])
            x,y,w,h=hits[name]['bbox']
            scale=int(doc.frame['render_scale'])
            assert x <= scale*tip[0] <= x+w and y <= scale*tip[1] <= y+h
        assert active == hits[name]['active_frames']
