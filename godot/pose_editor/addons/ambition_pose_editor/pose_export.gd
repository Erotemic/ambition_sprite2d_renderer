@tool
class_name AmbitionPoseExport
extends RefCounted

const EXPORT_SCHEMA := "ambition-godot-pose-export-v1"
const SHEET_SCHEMA := "ambition-godot-pose-sheet-v1"
const EPS := 0.0000005


static func _round6(value: float) -> float:
    var rounded := snappedf(value, 0.000001)
    if absf(rounded) < EPS:
        return 0.0
    return rounded


static func _vec2_array(value: Vector2) -> Array:
    return [_round6(value.x), _round6(value.y)]


static func _scale_delta(actual: Vector2, rest: Vector2) -> Vector2:
    if absf(rest.x) < EPS or absf(rest.y) < EPS:
        push_error("Ambition pose export cannot divide by a zero rest scale")
        return Vector2.ONE
    return Vector2(actual.x / rest.x, actual.y / rest.y)


static func _unwrap_degrees_near(value: float, hint: float) -> float:
    while value - hint > 180.0:
        value -= 360.0
    while value - hint < -180.0:
        value += 360.0
    return value


static func _bone_state(bone: Bone2D) -> Dictionary:
    if absf(bone.skew) > EPS:
        push_error("Ambition pose export does not support Bone2D skew: %s" % bone.get_path())
        return {}
    if bone.scale.x <= 0.0 or bone.scale.y <= 0.0:
        push_error("Ambition pose export requires positive Bone2D scale: %s" % bone.get_path())
        return {}

    var rest := bone.rest
    var position_delta := bone.position - rest.origin
    var rotation_delta := rad_to_deg(bone.rotation - rest.get_rotation())
    if bone.has_meta("ambition_source_rotation_delta_deg"):
        rotation_delta = _unwrap_degrees_near(
            rotation_delta,
            float(bone.get_meta("ambition_source_rotation_delta_deg"))
        )
    var scale_delta := _scale_delta(bone.scale, rest.get_scale())
    return {
        "position": _vec2_array(position_delta),
        "rotation_deg": _round6(rotation_delta),
        "scale": _vec2_array(scale_delta),
    }


static func _collect_bones(node: Node, out: Dictionary) -> void:
    for child in node.get_children():
        if child is Bone2D and child.has_meta("ambition_bone_id"):
            out[String(child.get_meta("ambition_bone_id"))] = _bone_state(child)
        _collect_bones(child, out)


static func _pose_state(pose_cell: Node) -> Dictionary:
    var rig_root := pose_cell.get_node_or_null("LayoutAnchor/RigRoot") as Node2D
    if rig_root == null:
        push_error("Ambition pose cell lacks LayoutAnchor/RigRoot: %s" % pose_cell.get_path())
        return {}
    if absf(rig_root.skew) > EPS:
        push_error("Ambition root skew is not supported: %s" % rig_root.get_path())
        return {}
    if rig_root.scale.x <= 0.0 or rig_root.scale.y <= 0.0:
        push_error("Ambition root scale must stay positive: %s" % rig_root.get_path())
        return {}

    var bones: Dictionary = {}
    _collect_bones(rig_root, bones)
    var parameters: Dictionary = {}
    if pose_cell.has_meta("ambition_parameters_json"):
        var parsed = JSON.parse_string(String(pose_cell.get_meta("ambition_parameters_json")))
        if parsed is Dictionary:
            parameters = parsed

    return {
        "root": {
            "position": _vec2_array(rig_root.position),
            "rotation_deg": _round6(rig_root.rotation_degrees),
            "scale": _vec2_array(rig_root.scale),
        },
        "bones": bones,
        "parameters": parameters,
    }


static func _collect_pose_cells(node: Node, out: Array[Node]) -> void:
    if node.has_meta("ambition_pose_id"):
        out.append(node)
    for child in node.get_children():
        _collect_pose_cells(child, out)


static func export_scene(scene_root: Node) -> Dictionary:
    if String(scene_root.get_meta("ambition_schema", "")) != SHEET_SCHEMA:
        push_error("Current scene is not an Ambition generated pose sheet")
        return {}

    var cells: Array[Node] = []
    _collect_pose_cells(scene_root, cells)
    cells.sort_custom(func(a: Node, b: Node) -> bool:
        return String(a.get_meta("ambition_pose_id")) < String(b.get_meta("ambition_pose_id"))
    )

    var poses: Array = []
    for cell in cells:
        poses.append({
            "id": String(cell.get_meta("ambition_pose_id")),
            "state": _pose_state(cell),
        })

    return {
        "schema": EXPORT_SCHEMA,
        "character": String(scene_root.get_meta("ambition_character", "")),
        "binding_path": String(scene_root.get_meta("ambition_binding_path", "")),
        "source_scene": scene_root.scene_file_path,
        "poses": poses,
    }


static func write_export(scene_root: Node, output_path: String = "") -> String:
    var payload := export_scene(scene_root)
    if payload.is_empty():
        return ""
    if output_path.is_empty():
        var character := String(payload["character"])
        output_path = "res://generated/exports/%s.poses.json" % character
    DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(output_path.get_base_dir()))
    var file := FileAccess.open(output_path, FileAccess.WRITE)
    if file == null:
        push_error("Cannot write Ambition pose export: %s" % output_path)
        return ""
    file.store_string(JSON.stringify(payload, "  ", false) + "\n")
    file.close()
    return output_path
