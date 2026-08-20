@tool
extends EditorPlugin

const PoseExport = preload("res://addons/ambition_pose_editor/pose_export.gd")
const MENU_LABEL := "Export Ambition Pose Sheet"


func _enter_tree() -> void:
    add_tool_menu_item(MENU_LABEL, _export_current_scene)


func _exit_tree() -> void:
    remove_tool_menu_item(MENU_LABEL)


func _export_current_scene() -> void:
    var root := EditorInterface.get_edited_scene_root()
    if root == null:
        push_error("No edited scene is open")
        return
    var output := PoseExport.write_export(root)
    if output.is_empty():
        return
    print("Ambition pose export: %s" % ProjectSettings.globalize_path(output))
