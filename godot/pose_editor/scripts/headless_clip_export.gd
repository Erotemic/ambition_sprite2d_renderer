extends SceneTree

const ClipExport = preload("res://addons/ambition_pose_editor/clip_export.gd")


func _initialize() -> void:
    var args := OS.get_cmdline_user_args()
    var scene_path := ""
    var output_path := ""
    var i := 0
    while i < args.size():
        match args[i]:
            "--scene":
                i += 1
                if i < args.size():
                    scene_path = args[i]
            "--output":
                i += 1
                if i < args.size():
                    output_path = args[i]
        i += 1

    if scene_path.is_empty():
        push_error("usage: --script res://scripts/headless_clip_export.gd -- --scene res://generated/<sheet>.tscn [--output res://generated/exports/out.json]")
        quit(2)
        return
    var packed := load(scene_path) as PackedScene
    if packed == null:
        push_error("Cannot load clip sheet: %s" % scene_path)
        quit(2)
        return
    var root := packed.instantiate()
    var written := ClipExport.write_export(root, output_path)
    root.free()
    if written.is_empty():
        quit(2)
        return
    print(ProjectSettings.globalize_path(written))
    quit(0)
