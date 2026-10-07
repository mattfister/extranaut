extends Node2D
## The campaign: owns the current room, the player, shots and the camera, and
## moves between rooms when the player crosses an edge.
## To save a screenshot and quit:
##   godot --path . -- --room=4,2 --shot=C:/some/file.png

const Controls := preload("res://input/controls.gd")

const ROOM_SIZE := Vector2(960, 768)
const GRID_SIZE := Vector2i(10, 10)
const START_ROOM := Vector2i(4, 2)
## Camera centre relative to the room origin: the room fills the left 960 px
## of the 1024 px view and the HUD strip covers the rest.
const VIEW_CENTER := Vector2(512, 384)
const SLIDE_TIME := 0.35

var grid := START_ROOM
var room: Node2D

## False from a transition until the player has left every exit zone, so
## arriving inside the opposite zone does not bounce straight back.
var _exits_armed := false
var _sliding := false

@onready var _world: Node2D = $World
@onready var _player: RigidBody2D = $Player
@onready var _shots: Node2D = $Shots
@onready var _camera: Camera2D = $Camera2D
@onready var _fuel_label: Label = $Hud/Fuel


func _ready() -> void:
	Controls.setup()
	var shot_path := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--room="):
			var parts := arg.trim_prefix("--room=").split(",")
			grid = Vector2i(int(parts[0]), int(parts[1]))
		elif arg.begins_with("--shot="):
			shot_path = arg.trim_prefix("--shot=")

	room = _load_room(grid)
	_world.add_child(room)
	var start: Vector2 = room.player_start if room.has_player_start else ROOM_SIZE / 2.0
	_player.global_position = room.position + start
	_camera.position = room.position + VIEW_CENTER
	_player.shot_fired.connect(_on_shot_fired)

	if shot_path != "":
		await get_tree().create_timer(1.0).timeout
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(shot_path)
		get_tree().quit()


func _process(_delta: float) -> void:
	_fuel_label.text = "FUEL\n%d" % int(_player.jetpack.fuel)


func _physics_process(_delta: float) -> void:
	if _sliding:
		return
	var local := _player.global_position - room.position
	var step := exit_step(local)
	if step == Vector2i.ZERO:
		_exits_armed = true
		return
	if not _exits_armed:
		return
	var next := grid + step
	if next.x < 0 or next.y < 0 or next.x >= GRID_SIZE.x or next.y >= GRID_SIZE.y:
		return
	_enter_room(next, step, local)


## Which way the player is leaving, given its centre in room coordinates.
## Thresholds are the original's, converted from sprite corner to centre. Many
## rooms have walls drawn on their borders to contain monsters and shots; the
## horizontal thresholds sit 1 px inside the point where the player touches
## such a wall, so it never blocks an exit.
static func exit_step(local: Vector2) -> Vector2i:
	if local.x >= 943.0:
		return Vector2i.RIGHT
	if local.x < 17.0:
		return Vector2i.LEFT
	if local.y >= 742.0:
		return Vector2i.DOWN
	if local.y < 27.0:
		return Vector2i.UP
	return Vector2i.ZERO


## Where the player appears in the next room after leaving in direction step.
static func entry_position(step: Vector2i, local: Vector2) -> Vector2:
	match step:
		Vector2i.RIGHT:
			return Vector2(17.0, local.y)
		Vector2i.LEFT:
			return Vector2(943.0, local.y)
		Vector2i.DOWN:
			return Vector2(local.x, 16.0)
		_:
			return Vector2(local.x, 720.0)


func _enter_room(next: Vector2i, step: Vector2i, local: Vector2) -> void:
	_sliding = true
	_exits_armed = false
	var old_room := room
	grid = next
	room = _load_room(grid)
	_world.add_child(room)
	for shot in _shots.get_children():
		shot.queue_free()
	_player.global_position = room.position + entry_position(step, local)

	get_tree().paused = true
	var tween := create_tween()
	tween.set_pause_mode(Tween.TWEEN_PAUSE_PROCESS)
	tween.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tween.tween_property(_camera, "position", room.position + VIEW_CENTER, SLIDE_TIME)
	await tween.finished
	old_room.queue_free()
	get_tree().paused = false
	_sliding = false


func _load_room(at: Vector2i) -> Node2D:
	var loaded: Node2D = load("res://world/rooms/room_%d_%d.tscn" % [at.x, at.y]).instantiate()
	loaded.position = Vector2(at) * ROOM_SIZE
	return loaded


func _on_shot_fired(shot: RigidBody2D) -> void:
	shot.bounds = Rect2(room.position, ROOM_SIZE)
	_shots.add_child(shot)
