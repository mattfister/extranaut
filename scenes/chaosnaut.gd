extends Node2D
## Chaosnaut: survive waves of ChaosBots in one walled room full of hover
## blocks, with unlimited fuel.

## The player chose to go back to the title, after dying or from the pause menu.
signal finished

const Controls := preload("res://input/controls.gd")
const ChaosScore := preload("res://save/chaos_score.gd")
const UiKit := preload("res://ui/ui_kit.gd")
const HoverBlockScene := preload("res://entities/monsters/hover_block.tscn")
const ChaosBotScene := preload("res://entities/monsters/chaos_bot.tscn")

const ROOM_SIZE := Vector2(960, 768)
const VIEW_CENTER := Vector2(512, 384)
const WALL_RADIUS := 0.5
const PLAYER_START := Vector2(32, 704)
const GUN_LEVEL := 3
const BLOCK_COUNT := 40
const BLOCK_X_MIN := 128.0
const BLOCK_X_MAX := 800.0
const SPAWN_Y_MAX := 736.0
const BOT_SPAWN_X := 928.0
## A bot at or left of this wraps to BOT_SPAWN_X and turns angry.
const BOT_WRAP_X := 16.0
const FIRST_WAVE_DELAY := 2.0
const WAVE_INTERVAL := 10.0

var wave := 0
var kills := 0
## Seconds until the next wave.
var next_wave_in := FIRST_WAVE_DELAY

var _over := false

@onready var _entities: Node2D = $Entities
@onready var _player: RigidBody2D = $Player
@onready var _shots: Node2D = $Shots
@onready var _camera: Camera2D = $Camera2D
@onready var _hud: Control = $Hud/Strip
@onready var _wave_label: Label = $Hud/Wave
@onready var _screen_fx: CanvasLayer = $ScreenFx
@onready var _pause_menu: CanvasLayer = $PauseMenu
@onready var _game_over: CanvasLayer = $GameOver


func _ready() -> void:
	Controls.setup()
	_build_walls()
	_build_game_over()
	_wave_label.add_theme_font_override("font", UiKit.FONT)
	_wave_label.add_theme_font_size_override("font_size", UiKit.FONT_SIZE)
	_camera.position = VIEW_CENTER
	_screen_fx.camera = _camera
	_player.position = PLAYER_START
	_player.gun_level = GUN_LEVEL
	_player.shot_fired.connect(_on_shot_fired)
	_player.died.connect(_on_player_died)
	_pause_menu.resume_pressed.connect(_set_pause_menu.bind(false))
	_pause_menu.quit_pressed.connect(_leave)
	get_tree().call_group("audio", "play_music", "chaosNaut")
	_top_up_blocks()


func _process(_delta: float) -> void:
	_hud.set_status(_player.hp, _player.jetpack.fuel, 0)
	_wave_label.text = "Wave %d" % wave


func _physics_process(delta: float) -> void:
	if _over:
		return
	_player.jetpack.fuel = _player.jetpack.max_fuel
	next_wave_in -= delta
	if next_wave_in <= 0.0:
		_start_wave()
	for bot in bots():
		if bot.global_position.x <= BOT_WRAP_X:
			bot.global_position.x = BOT_SPAWN_X
			bot.angry = true
	_top_up_blocks()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("pause") and not _over:
		_set_pause_menu(not _pause_menu.visible)


func blocks() -> Array[Node]:
	return _living("chaos_blocks")


func bots() -> Array[Node]:
	return _living("chaos_bots")


func block_count() -> int:
	return blocks().size()


func bot_count() -> int:
	return bots().size()


func _living(group: String) -> Array[Node]:
	var result: Array[Node] = []
	for node in _entities.get_children():
		if node.is_in_group(group) and not node.is_queued_for_deletion():
			result.append(node)
	return result


func _start_wave() -> void:
	wave += 1
	next_wave_in = WAVE_INTERVAL
	get_tree().call_group("audio", "play", "newWave")
	for i in wave / 4 + 1:
		var bot: RigidBody2D = ChaosBotScene.instantiate()
		bot.position = Vector2(BOT_SPAWN_X, randf_range(0.0, SPAWN_Y_MAX))
		bot.add_to_group("chaos_bots")
		bot.died.connect(func() -> void: kills += 1)
		_entities.add_child(bot)


func _top_up_blocks() -> void:
	for i in BLOCK_COUNT - block_count():
		var block: RigidBody2D = HoverBlockScene.instantiate()
		block.position = Vector2(randf_range(BLOCK_X_MIN, BLOCK_X_MAX), randf_range(0.0, SPAWN_Y_MAX))
		block.add_to_group("chaos_blocks")
		_entities.add_child(block)


func _build_walls() -> void:
	var body := StaticBody2D.new()
	body.name = "Walls"
	var material := PhysicsMaterial.new()
	material.friction = 0.5
	body.physics_material_override = material
	var corners := [Vector2.ZERO, Vector2(ROOM_SIZE.x, 0), ROOM_SIZE, Vector2(0, ROOM_SIZE.y)]
	for i in 4:
		var a: Vector2 = corners[i]
		var b: Vector2 = corners[(i + 1) % 4]
		var capsule := CapsuleShape2D.new()
		capsule.radius = WALL_RADIUS
		capsule.height = a.distance_to(b) + WALL_RADIUS * 2.0
		var shape := CollisionShape2D.new()
		shape.shape = capsule
		shape.position = (a + b) / 2.0
		shape.rotation = (b - a).angle() - PI / 2.0
		body.add_child(shape)
	add_child(body)


func _build_game_over() -> void:
	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.8)
	dim.size = Vector2(1024, 768)
	_game_over.add_child(dim)
	var heading := UiKit.make_label("GAME OVER")
	heading.position = Vector2(0, 260)
	heading.size = Vector2(1024, 20)
	heading.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_game_over.add_child(heading)
	var stats := UiKit.make_label("")
	stats.name = "Stats"
	stats.position = Vector2(0, 310)
	stats.size = Vector2(1024, 80)
	stats.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_game_over.add_child(stats)
	var back := UiKit.make_button("Back to Title", Vector2(140, 20))
	back.name = "Back"
	back.position = Vector2(442, 420)
	back.pressed.connect(_leave)
	_game_over.add_child(back)


func _on_player_died() -> void:
	_over = true
	var is_best := ChaosScore.submit(wave, kills)
	var best := ChaosScore.read()
	var stats: Label = _game_over.get_node("Stats")
	stats.text = "Wave %d     Kills %d\n\nBest: Wave %d     Kills %d%s" % [
		wave, kills, best.wave, best.kills, "\n\nNew best!" if is_best else "",
	]
	_game_over.visible = true
	get_tree().paused = true
	(_game_over.get_node("Back") as Button).grab_focus()


func _set_pause_menu(open: bool) -> void:
	_pause_menu.visible = open
	get_tree().paused = open
	if open:
		_pause_menu.open(null, Vector2i.ZERO)


func _leave() -> void:
	_pause_menu.visible = false
	get_tree().paused = false
	finished.emit()


func _on_shot_fired(shot: RigidBody2D) -> void:
	shot.bounds = Rect2(Vector2.ZERO, ROOM_SIZE)
	_shots.add_child(shot)
