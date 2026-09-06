from ambition_sprite2d_renderer.targets.characters import imperfect_cellular_automaton as target


def test_imperfect_cellular_automaton_frames_render_without_clipping():
    for animation, nframes, _duration_ms in target.ROWS:
        for frame_idx in range(nframes):
            frame = target.render_frame(animation, frame_idx, nframes)
            assert frame.size == (target.FRAME_W, target.FRAME_H)
            bbox = frame.getchannel("A").getbbox()
            assert bbox is not None
            x0, y0, x1, y1 = bbox
            assert x0 > 0
            assert y0 > 0
            assert x1 < target.FRAME_W
            assert y1 < target.FRAME_H


def test_imperfect_rule_records_a_fault_and_changes_state():
    board0, fault0 = target._life_state_for_frame("idle", 0)
    board1, fault1 = target._life_state_for_frame("idle", 1)
    assert board0 != board1
    assert fault0 != fault1
    assert 0 <= fault0[0] < 5
    assert 0 <= fault0[1] < 5


def test_imperfect_cellular_automaton_declares_model_lineage():
    provenance = target.ACTOR_METADATA["provenance"]
    assert provenance["variant_family"] == target.TARGET_NAME
    assert provenance["variant_id"] == "gpt_5_6_zorder_polish_2026_07_15"
    assert provenance["lineage"][-1]["creator"] == "gpt-5.6-thinking"
    assert provenance["lineage"][-1]["contribution"] == "arm_visibility_zorder_contract_and_shadow_removal"
    assert provenance["lineage"][-1]["parent_revision_id"] == "gpt_5_6_redesign_2026_07_15"


def test_slash_has_a_distinct_extended_attack_silhouette():
    idle = target.render_frame("idle", 0, 6).getchannel("A").getbbox()
    strike = target.render_frame("slash", 2, 6).getchannel("A").getbbox()
    assert idle is not None and strike is not None
    assert strike[2] > idle[2] + 20


def test_arms_are_contractually_above_every_non_arm_part():
    target._validate_part_z(target.PART_Z)
    assert min(target.PART_Z[name] for name in target.ARM_PARTS) > max(
        target.PART_Z[name] for name in target.NON_ARM_PARTS
    )
    rig_z = {part.name: part.z for part in target._RIG.parts}
    assert rig_z == target.PART_Z


def test_character_left_arm_keeps_an_external_silhouette_in_every_pose():
    for animation, nframes, _duration_ms in target.ROWS:
        for frame_idx in range(nframes):
            if animation in target.LOOPS:
                t = frame_idx / nframes
            else:
                t = frame_idx / max(1, nframes - 1)
            world, _params = target._solve(animation, t)
            left_hand = world["far_arm_l"].tip
            torso_center = world["torso"].origin
            assert left_hand[0] < torso_center[0] - 25.0, (animation, frame_idx, left_hand, torso_center)


def test_target_contains_no_drop_shadow_authoring():
    assert "shadow" not in target.PAL
    assert not hasattr(target, "_draw_soft_shadow")
