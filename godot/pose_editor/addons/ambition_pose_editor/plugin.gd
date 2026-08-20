@tool
extends EditorPlugin

const PoseExport = preload("res://addons/ambition_pose_editor/pose_export.gd")
const ClipExport = preload("res://addons/ambition_pose_editor/clip_export.gd")
const POSE_MENU_LABEL := "Export Ambition Pose Sheet"
const CLIP_MENU_LABEL := "Export Ambition Clip Sheet"


func _enter_tree() -> void:
    add_tool_menu_item(POSE_MENU_LABEL, _export_current_pose_scene)
    add_tool_menu_item(CLIP_MENU_LABEL, _export_current_clip_scene)


func _exit_tree() -> void:
    remove_tool_menu_item(POSE_MENU_LABEL)
    remove_tool_menu_item(CLIP_MENU_LABEL)


func _export_current_pose_scene() -> void:
    var root := EditorInterface.get_edited_scene_root()
    if root == null:
        push_error("No edited scene is open")
        return
    var output := PoseExport.write_export(root)
    if output.is_empty():
        return
    print("Ambition pose export: %s" % ProjectSettings.globalize_path(output))


func _export_current_clip_scene() -> void:
    var root := EditorInterface.get_edited_scene_root()
    if root == null:
        push_error("No edited scene is open")
        return
    var output := ClipExport.write_export(root)
    if output.is_empty():
        return
    print("Ambition clip export: %s" % ProjectSettings.globalize_path(output))
