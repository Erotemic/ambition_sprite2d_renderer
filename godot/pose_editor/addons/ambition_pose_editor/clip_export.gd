@tool
class_name AmbitionClipExport
extends RefCounted

const EXPORT_SCHEMA := "ambition-godot-clip-export-v2"
const SHEET_SCHEMA := "ambition-godot-clip-sheet-v2"
const EPS := 0.0001


static func _round6(value: float) -> float:
    var rounded := snappedf(value, 0.000001)
    if absf(rounded) < 0.0000005:
        return 0.0
    return rounded


static func _collect_bones(node: Node, out: Dictionary) -> void:
    for child in node.get_children():
        if child is Bone2D and child.has_meta("ambition_bone_id"):
            out[String(child.get_meta("ambition_bone_id"))] = child
        _collect_bones(child, out)


static func _collect_clip_cells(node: Node, out: Array[Node]) -> void:
    if node.has_meta("ambition_clip_id") and node.get_node_or_null("AnimationPlayer") != null:
        out.append(node)
    for child in node.get_children():
        _collect_clip_cells(child, out)


static func _interpolation_name(animation: Animation, track_idx: int) -> String:
    var update_mode := animation.value_track_get_update_mode(track_idx)
    if update_mode == Animation.UPDATE_DISCRETE:
        return "hold"
    if update_mode != Animation.UPDATE_CONTINUOUS:
        push_error(
            "Ambition clip export currently round-trips continuous or discrete value tracks: %s" %
            String(animation.track_get_path(track_idx))
        )
        return ""
    if animation.track_get_interpolation_type(track_idx) == Animation.INTERPOLATION_LINEAR:
        return "linear"
    push_error(
        "Ambition clip export currently round-trips linear interpolation; nearest is not a hold " +
        "(use a Discrete value track), and cubic/custom interpolation is not yet in the IR seam: %s" %
        String(animation.track_get_path(track_idx))
    )
    return ""


static func _validated_track_map(animation: Animation) -> Dictionary:
    var tracks: Dictionary = {}
    for track_idx in range(animation.get_track_count()):
        if animation.track_get_type(track_idx) != Animation.TYPE_VALUE:
            push_error("Ambition clip export currently round-trips ordinary value tracks only")
            return {}
        if _interpolation_name(animation, track_idx).is_empty():
            return {}
        var path := String(animation.track_get_path(track_idx))
        if tracks.has(path):
            push_error("Ambition clip export found duplicate animation track path: %s" % path)
            return {}
        var count := animation.track_get_key_count(track_idx)
        if count <= 0:
            push_error("Ambition clip animation track has no keys: %s" % path)
            return {}
        var previous := -INF
        for key_idx in range(count):
            var at_s := float(animation.track_get_key_time(track_idx, key_idx))
            if at_s < -EPS or at_s > animation.length + EPS:
                push_error("Ambition clip key lies outside animation duration: %s @ %s" % [path, at_s])
                return {}
            if at_s <= previous:
                push_error("Ambition clip track keys must have unique increasing times: %s" % path)
                return {}
            previous = at_s
            if absf(float(animation.track_get_key_transition(track_idx, key_idx)) - 1.0) > EPS:
                push_error(
                    "Ambition clip export does not yet preserve custom key transition/easing values: %s" % path
                )
                return {}
        tracks[path] = track_idx
    return tracks


static func _require_track(track_map: Dictionary, path: String) -> int:
    if not track_map.has(path):
        push_error("Ambition clip animation is missing generated property track: %s" % path)
        return -1
    return int(track_map[path])


static func _scalar_track(target: String, animation: Animation, track_idx: int, transform: Callable) -> Dictionary:
    var keys: Array = []
    for key_idx in range(animation.track_get_key_count(track_idx)):
        var raw_value = animation.track_get_key_value(track_idx, key_idx)
        var value = transform.call(raw_value)
        if typeof(value) not in [TYPE_FLOAT, TYPE_INT]:
            push_error("Ambition scalar animation track has a non-scalar key: %s" % target)
            return {}
        keys.append({
            "at_s": _round6(float(animation.track_get_key_time(track_idx, key_idx))),
            "value": _round6(float(value)),
        })
    return {
        "target": target,
        "interpolation": _interpolation_name(animation, track_idx),
        "keys": keys,
    }


static func _vector_tracks(
    x_target: String,
    y_target: String,
    animation: Animation,
    track_idx: int,
    offset: Vector2,
) -> Array:
    var x_keys: Array = []
    var y_keys: Array = []
    for key_idx in range(animation.track_get_key_count(track_idx)):
        var raw_value = animation.track_get_key_value(track_idx, key_idx)
        if typeof(raw_value) != TYPE_VECTOR2:
            push_error("Ambition position animation track must contain Vector2 keys: %s" % x_target)
            return []
        var value: Vector2 = raw_value - offset
        var at_s := _round6(float(animation.track_get_key_time(track_idx, key_idx)))
        x_keys.append({"at_s": at_s, "value": _round6(value.x)})
        y_keys.append({"at_s": at_s, "value": _round6(value.y)})
    var interpolation := _interpolation_name(animation, track_idx)
    if interpolation.is_empty():
        return []
    return [
        {"target": x_target, "interpolation": interpolation, "keys": x_keys},
        {"target": y_target, "interpolation": interpolation, "keys": y_keys},
    ]


static func _export_clip_cell(cell: Node) -> Dictionary:
    var clip_id := String(cell.get_meta("ambition_clip_id", ""))
    var player := cell.get_node_or_null("AnimationPlayer") as AnimationPlayer
    if player == null or not player.has_animation(clip_id):
        push_error("Ambition clip cell %s lacks animation %s" % [cell.get_path(), clip_id])
        return {}
    var animation := player.get_animation(clip_id)
    if animation == null:
        push_error("Ambition clip animation could not be loaded: %s" % clip_id)
        return {}
    if animation.loop_mode not in [Animation.LOOP_NONE, Animation.LOOP_LINEAR]:
        push_error("Ambition clip export supports non-looping or linear-looping animations only")
        return {}

    var rig_root := cell.get_node_or_null("LayoutAnchor/RigRoot") as Node2D
    var skeleton := cell.get_node_or_null("LayoutAnchor/RigRoot/Skeleton2D") as Skeleton2D
    if rig_root == null or skeleton == null:
        push_error("Ambition clip cell lacks generated rig nodes: %s" % cell.get_path())
        return {}
    var bones: Dictionary = {}
    _collect_bones(skeleton, bones)

    var track_map := _validated_track_map(animation)
    if track_map.is_empty():
        return {}

    var expected_paths: Dictionary = {}
    var tracks: Array = []

    var root_path := "LayoutAnchor/RigRoot:position"
    var root_track := _require_track(track_map, root_path)
    if root_track < 0:
        return {}
    expected_paths[root_path] = true
    var root_tracks := _vector_tracks(
        "root.position.x", "root.position.y", animation, root_track, Vector2.ZERO
    )
    if root_tracks.is_empty():
        return {}
    tracks.append_array(root_tracks)

    var bone_ids: Array = bones.keys()
    bone_ids.sort()
    for bone_id_value in bone_ids:
        var bone_id := String(bone_id_value)
        var bone := bones[bone_id] as Bone2D
        var node_path := String(cell.get_path_to(bone))
        var position_path := node_path + ":position"
        var rotation_path := node_path + ":rotation"
        var position_track := _require_track(track_map, position_path)
        var rotation_track := _require_track(track_map, rotation_path)
        if position_track < 0 or rotation_track < 0:
            return {}
        expected_paths[position_path] = true
        expected_paths[rotation_path] = true

        var position_tracks := _vector_tracks(
            "bone.%s.position.x" % bone_id,
            "bone.%s.position.y" % bone_id,
            animation,
            position_track,
            bone.rest.origin,
        )
        if position_tracks.is_empty():
            return {}
        tracks.append_array(position_tracks)

        var rest_rotation := bone.rest.get_rotation()
        var rotation_track_data := _scalar_track(
            "bone.%s.rotation_deg" % bone_id,
            animation,
            rotation_track,
            func(value):
                if typeof(value) not in [TYPE_FLOAT, TYPE_INT]:
                    return null
                # Deliberately do not normalize the angle.  Ambition preserves
                # authored winding (for example 0 -> 450 degrees).
                return rad_to_deg(float(value) - rest_rotation),
        )
        if rotation_track_data.is_empty():
            return {}
        tracks.append(rotation_track_data)

    for path_value in track_map.keys():
        var path := String(path_value)
        if not expected_paths.has(path):
            push_error("Ambition clip export cannot round-trip added property track: %s" % path)
            return {}

    return {
        "id": clip_id,
        "duration_s": _round6(animation.length),
        "loop": animation.loop_mode == Animation.LOOP_LINEAR,
        "tracks": tracks,
    }


static func export_scene(scene_root: Node) -> Dictionary:
    if String(scene_root.get_meta("ambition_schema", "")) != SHEET_SCHEMA:
        push_error("Current scene is not an Ambition generated clip sheet")
        return {}
    var cells: Array[Node] = []
    _collect_clip_cells(scene_root, cells)
    cells.sort_custom(func(a: Node, b: Node) -> bool:
        return String(a.get_meta("ambition_clip_id")) < String(b.get_meta("ambition_clip_id"))
    )
    var clips: Array = []
    for cell in cells:
        var clip := _export_clip_cell(cell)
        if clip.is_empty():
            return {}
        clips.append(clip)
    return {
        "schema": EXPORT_SCHEMA,
        "character": String(scene_root.get_meta("ambition_character", "")),
        "binding_path": String(scene_root.get_meta("ambition_binding_path", "")),
        "source_scene": scene_root.scene_file_path,
        "clips": clips,
    }


static func write_export(scene_root: Node, output_path: String = "") -> String:
    var payload := export_scene(scene_root)
    if payload.is_empty():
        return ""
    if output_path.is_empty():
        var character := String(payload["character"])
        output_path = "res://generated/exports/%s.clips.json" % character
    DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(output_path.get_base_dir()))
    var file := FileAccess.open(output_path, FileAccess.WRITE)
    if file == null:
        push_error("Cannot write Ambition clip export: %s" % output_path)
        return ""
    file.store_string(JSON.stringify(payload, "  ", false) + "\n")
    file.close()
    return output_path
