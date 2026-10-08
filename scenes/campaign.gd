extends Node2D
## The campaign: owns the current room, the player, shots and the camera,
## moves between rooms when the player crosses an edge, and records progress.
## Set slot and progress before adding it to the tree.

## The player fell out of the bottom of the world.
signal won
signal quit_to_title

const Controls := preload("res://input/controls.gd")
const Progress := preload("res://save/progress.gd")
const SaveGame := preload("res://save/save_game.gd")

const ROOM_SIZE := Vector2(960, 768)
const GRID_SIZE := Vector2i(10, 10)
## Camera centre relative to the room origin: the room fills the left 960 px
## of the 1024 px view and the HUD strip covers the rest.
const VIEW_CENTER := Vector2(512, 384)
const SLIDE_TIME := 0.35
## How far below a bottom-row room the player must fall to win.
const WIN_DEPTH := 16.0
const MAX_GUN_LEVEL := 4
const RESPAWN_FADE_IN := 0.4

## Save slot 1 to 3, or 0 to play without saving.
var slot := 0
## A save/progress.gd object. A fresh one is made if none is given.
var progress: RefCounted
var grid := Vector2i.ZERO
var room: Node2D

## False from a transition until the player has left every exit zone, so
## arriving inside the opposite zone does not bounce straight back.
var _exits_armed := false
var _sliding := false
var _finished := false

@onready var _world: Node2D = $World
@onready var _player: RigidBody2D = $Player
@onready var _shots: Node2D = $Shots
@onready var _camera: Camera2D = $Camera2D
@onready var _hud: Control = $Hud/Strip
@onready var _mini_map: Control = $Hud/Strip/MiniMap
@onready var _pause_menu: CanvasLayer = $PauseMenu
@onready var _particles: Node2D = $Particles
@onready var _screen_fx: CanvasLayer = $ScreenFx


func _ready() -> void:
	Controls.setup()
	if progress == null:
		progress = Progress.new()
	grid = progress.checkpoint
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--room="):
			var parts := arg.trim_prefix("--room=").split(",")
			grid = Vector2i(int(parts[0]), int(parts[1]))

	_player.max_hp = progress.max_hp
	_player.hp = progress.max_hp
	_player.jetpack.max_fuel = progress.max_fuel
	_player.jetpack.fuel = progress.max_fuel
	_player.gun_level = progress.gun_level
	_player.artifacts = progress.artifacts
	_player.shot_fired.connect(_on_shot_fired)
	_player.died.connect(_respawn)
	_player.death_started.connect(func() -> void: _screen_fx.fade_out(_player.DEATH_TIME))
	_screen_fx.camera = _camera
	_pause_menu.resume_pressed.connect(_set_pause_menu.bind(false))
	_pause_menu.quit_pressed.connect(_quit_to_title)

	room = load_room(grid)
	_world.add_child(room)
	_place_player_at_start()
	_note_room()


func _process(_delta: float) -> void:
	_hud.set_status(_player.hp, _player.jetpack.fuel, _player.artifacts)


func _physics_process(_delta: float) -> void:
	if _sliding or _finished:
		return
	var local := _player.global_position - room.position
	if grid.y == GRID_SIZE.y - 1 and local.y >= ROOM_SIZE.y + WIN_DEPTH:
		_finished = true
		won.emit()
		return
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


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("pause") and not _sliding and not _finished:
		_set_pause_menu(not _pause_menu.visible)


## The original's cheat keys, in debug builds only.
func _unhandled_key_input(event: InputEvent) -> void:
	if not OS.is_debug_build() or not event.pressed or event.echo:
		return
	match event.keycode:
		KEY_F9:
			_player.gun_level = mini(_player.gun_level + 1, MAX_GUN_LEVEL)
		KEY_F10:
			_player.jetpack.max_fuel += 500.0
		KEY_F11:
			_player.max_hp += 1
			_player.hp += 1
		KEY_F12:
			_player.artifacts += 1


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


## Instantiates the room at a grid position, placed in world space, with its
## monsters wired to the campaign and any collected powerup removed.
func load_room(at: Vector2i) -> Node2D:
	var loaded: Node2D = load("res://world/rooms/room_%d_%d.tscn" % [at.x, at.y]).instantiate()
	loaded.position = Vector2(at) * ROOM_SIZE
	for entity in loaded.get_node("Entities").get_children():
		if entity.is_powerup and progress.powerups_taken.has(at):
			entity.free()
			continue
		entity.shot_fired.connect(_on_shot_fired)
		entity.save_requested.connect(_on_save_requested)
	return loaded


func _enter_room(next: Vector2i, step: Vector2i, local: Vector2) -> void:
	_sliding = true
	_exits_armed = false
	var old_room := room
	grid = next
	room = load_room(grid)
	_world.add_child(room)
	_clear_shots()
	_particles.clear()
	_player.global_position = room.position + entry_position(step, local)
	_note_room()

	get_tree().paused = true
	var tween := create_tween()
	tween.set_pause_mode(Tween.TWEEN_PAUSE_PROCESS)
	tween.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tween.tween_property(_camera, "position", room.position + VIEW_CENTER, SLIDE_TIME)
	await tween.finished
	old_room.queue_free()
	get_tree().paused = false
	_sliding = false


## Reloads the checkpoint room and puts a revived player at its start.
func _respawn() -> void:
	_clear_shots()
	_particles.clear()
	_screen_fx.fade_in(RESPAWN_FADE_IN)
	_world.remove_child(room)
	room.queue_free()
	grid = progress.checkpoint
	room = load_room(grid)
	_world.add_child(room)
	_player.revive()
	_place_player_at_start()
	_note_room()


func _place_player_at_start() -> void:
	var start: Vector2 = room.player_start if room.has_player_start else ROOM_SIZE / 2.0
	_player.global_position = room.position + start
	_camera.position = room.position + VIEW_CENTER
	_exits_armed = false


## Records the current room on the map and writes the slot, so the explored
## map survives quitting. Stats and checkpoint change only at save events.
func _note_room() -> void:
	if room.music != "":
		get_tree().call_group("audio", "play_music", room.music)
	progress.visited[grid] = true
	for entity in room.get_node("Entities").get_children():
		if entity.is_save_point:
			progress.save_points[grid] = true
	_mini_map.show_progress(progress, grid)
	_write_slot()


func _write_slot() -> void:
	if slot > 0:
		SaveGame.write(slot, progress)


func _clear_shots() -> void:
	for shot in _shots.get_children():
		shot.queue_free()


func _set_pause_menu(open: bool) -> void:
	_pause_menu.visible = open
	get_tree().paused = open
	if open:
		_pause_menu.open(progress, grid)


func _quit_to_title() -> void:
	_set_pause_menu(false)
	quit_to_title.emit()


func _on_shot_fired(shot: RigidBody2D) -> void:
	shot.bounds = Rect2(room.position, ROOM_SIZE)
	_shots.add_child(shot)


## A save point was activated or a powerup collected in the current room.
func _on_save_requested(source: Node) -> void:
	progress.checkpoint = grid
	_player.hp = _player.max_hp
	if source.is_powerup:
		progress.powerups_taken[grid] = true
	progress.max_hp = _player.max_hp
	progress.max_fuel = _player.jetpack.max_fuel
	progress.gun_level = _player.gun_level
	progress.artifacts = _player.artifacts
	_write_slot()
	_hud.show_saved()
