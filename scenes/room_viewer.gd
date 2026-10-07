extends Node2D
## Temporary viewer for checking imported rooms. Arrow keys change room.
## To save a screenshot and quit:
##   godot --path . -- --room=4,2 --shot=C:/some/file.png

var _grid := Vector2i(4, 2)
var _room: Node2D
var _shot_path := ""

@onready var _label: Label = $Label


func _ready() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--room="):
			var parts := arg.trim_prefix("--room=").split(",")
			_grid = Vector2i(int(parts[0]), int(parts[1]))
		elif arg.begins_with("--shot="):
			_shot_path = arg.trim_prefix("--shot=")
	get_tree().debug_collisions_hint = true
	_show_room()
	if _shot_path != "":
		await RenderingServer.frame_post_draw
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(_shot_path)
		get_tree().quit()


func _unhandled_key_input(event: InputEvent) -> void:
	if not event.pressed:
		return
	var step := Vector2i.ZERO
	match event.keycode:
		KEY_LEFT:
			step = Vector2i.LEFT
		KEY_RIGHT:
			step = Vector2i.RIGHT
		KEY_UP:
			step = Vector2i.UP
		KEY_DOWN:
			step = Vector2i.DOWN
	if step != Vector2i.ZERO:
		_grid = (_grid + step).clamp(Vector2i.ZERO, Vector2i(9, 9))
		_show_room()


func _show_room() -> void:
	if _room != null:
		_room.queue_free()
	_room = load("res://world/rooms/room_%d_%d.tscn" % [_grid.x, _grid.y]).instantiate()
	add_child(_room)
	move_child(_room, 0)
	_label.text = "%d,%d\n%s" % [_grid.x, _grid.y, _room.music]
