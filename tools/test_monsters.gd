extends SceneTree
## Arena tests for monsters, shots and player damage.
## Run: godot --headless --path . --script res://tools/test_monsters.gd
## Pass "-- --only=name" to run the sections whose name contains that text.

const Controls := preload("res://input/controls.gd")
const PlayerScene := preload("res://entities/player/player.tscn")
const EnergyBallScene := preload("res://entities/projectiles/energy_ball.tscn")
const EnemyEnergyBallScene := preload("res://entities/projectiles/enemy_energy_ball.tscn")
const EnergyGrenadeScene := preload("res://entities/projectiles/energy_grenade.tscn")

const FLOOR_Y := 500.0
## Centre height of a radius-16 body resting on the floor.
const REST_Y := FLOOR_Y - 16.0
const PLAYER_REST := Vector2(0, FLOOR_Y - 13.0)

var _failures := 0
var _arena: Node2D
var _entities: Node2D
var _player: RigidBody2D
var _field: Node2D
## One entry per shot fired in the current arena, recorded when it was fired.
var _shot_log: Array[Dictionary] = []
var _saves: Array[Node] = []


func _initialize() -> void:
	_run()


func _run() -> void:
	Controls.setup()
	await process_frame
	var only := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--only="):
			only = arg.trim_prefix("--only=")
	var sections := {
		"every_kind_runs": _test_every_kind_runs,
		"shots_damage_monsters": _test_shots_damage_monsters,
		"touch_damage": _test_touch_damage,
		"powerups": _test_powerups,
		"save_point": _test_save_point,
		"doors": _test_doors,
		"turrets": _test_turrets,
		"enemy_shots": _test_enemy_shots,
		"player_death": _test_player_death,
		"movers": _test_movers,
		"effects": _test_effects,
	}
	for section_name in sections:
		if only == "" or section_name.contains(only):
			var before := _failures
			await sections[section_name].call()
			print("%s: %s" % [section_name, "ok" if _failures == before else "FAILED"])
	print("monster test passed" if _failures == 0 else "monster test FAILED: %d failures" % _failures)
	quit(1 if _failures > 0 else 0)


func _test_every_kind_runs() -> void:
	_new_arena(Vector2(-300, PLAYER_REST.y))
	var world = JSON.parse_string(FileAccess.get_file_as_string("res://tools/zorta.json"))
	var kinds := {}
	for room in world.rooms:
		for m in room.monsters:
			kinds[m[0]] = true
	_expect(kinds.size() == 25, "25 kinds in the world, found %d" % kinds.size())
	var x := 0.0
	for kind in kinds:
		var file := String(kind).to_snake_case()
		if not ResourceLoader.exists("res://entities/monsters/%s.tscn" % file):
			_fail("no scene for %s" % kind)
			continue
		var monster := _spawn(file, Vector2(x, 400))
		_expect(monster.is_in_group("monsters"), "%s is in the monsters group" % kind)
		_expect(monster.hp == monster.max_hp, "%s starts at full hp" % kind)
		x += 120.0
	await _frames(180)


func _test_shots_damage_monsters() -> void:
	_new_arena()
	var ball := _spawn("ball_monster", Vector2(300, REST_Y))
	ball._kick_timer = 10.0
	_launch(EnergyBallScene, Vector2(200, REST_Y), Vector2(500, 0))
	await _frames(30)
	_expect(not is_instance_valid(ball), "one shot kills a ball monster")

	var bot := _spawn("fly_bot", Vector2(300, 300))
	bot.hit()
	bot.hit()
	_expect(bot.hp == 1 and not bot.is_queued_for_deletion(), "fly bot survives two hits")
	bot.hit()
	_expect(bot.is_queued_for_deletion(), "fly bot dies on the third hit")

	var spiky := _spawn("spiky_head_monster", Vector2(500, REST_Y))
	spiky._kick_timer = 10.0
	_launch(EnergyBallScene, Vector2(420, REST_Y), Vector2(500, 0))
	await _frames(30)
	_expect(is_instance_valid(spiky), "spiky head ignores shots")


func _test_touch_damage() -> void:
	_new_arena()
	await _frames(30)
	var ball := _spawn("ball_monster", _player.position + Vector2(28, -3))
	ball._kick_timer = 10.0
	await _frames(20)
	_expect(_player.hp == 5, "ball monsters are harmless, hp %d" % _player.hp)
	ball.free()

	var spiky := _spawn("spiky_ball_monster", _player.position + Vector2(28, -3))
	spiky._kick_timer = 10.0
	await _frames(10)
	_expect(_player.hp == 4, "spiky ball hurts on touch, hp %d" % _player.hp)
	spiky.free()
	spiky = _spawn("spiky_ball_monster", _player.position + Vector2(28, -3))
	spiky._kick_timer = 10.0
	await _frames(20)
	_expect(_player.hp == 4, "player is invulnerable for a second after a hit, hp %d" % _player.hp)


func _test_powerups() -> void:
	_new_arena()
	await _frames(30)
	var beside := Vector2(28, -3)
	_player.hp = 3
	var powerup := _spawn("hp_powerup", _player.position + beside)
	await _frames(10)
	_expect(_player.max_hp == 6 and _player.hp == 6, "hp powerup raises and refills hp")
	_expect(not is_instance_valid(powerup), "a collected powerup is removed")
	_expect(_saves.size() == 1, "a powerup requests a save")

	_spawn("fuel_powerup", _player.position + beside)
	await _frames(10)
	_expect(_player.jetpack.max_fuel == 2500.0, "fuel powerup adds 500 max fuel")

	_spawn("gun_powerup", _player.position + beside)
	await _frames(10)
	_expect(_player.gun_level == 2, "gun powerup raises the gun level")
	_player.gun_level = 4
	_spawn("gun_powerup", _player.position + beside)
	await _frames(10)
	_expect(_player.gun_level == 4, "gun level is capped at 4")

	_spawn("alien_artifact", _player.position + beside)
	await _frames(10)
	_expect(_player.artifacts == 1, "alien artifact is counted")
	_expect(_saves.size() == 5, "every powerup requests a save, got %d" % _saves.size())


func _test_save_point() -> void:
	_new_arena()
	var save_point := _spawn("save_point", Vector2(300, REST_Y))
	_launch(EnergyBallScene, Vector2(200, REST_Y), Vector2(500, 0))
	await _frames(30)
	_expect(_saves.size() == 1 and _saves[0] == save_point, "shooting a save point requests a save")
	_expect(save_point.sprite.frame_coords.y == 1, "an activated save point changes sprite row")
	_launch(EnergyBallScene, Vector2(200, REST_Y), Vector2(500, 0))
	await _frames(30)
	_expect(_saves.size() == 1, "a save point only activates once")
	_expect(is_instance_valid(save_point), "a save point is not destroyed by shots")


func _test_doors() -> void:
	_new_arena()
	var door := _spawn("monster_door", Vector2(300, 400))
	await _frames(3)
	_expect(not is_instance_valid(door), "a monster door alone in the room opens")

	var ball := _spawn("ball_monster", Vector2(500, REST_Y))
	door = _spawn("monster_door", Vector2(300, 400))
	await _frames(10)
	_expect(is_instance_valid(door), "a monster door stays shut while a monster lives")
	ball.hit()
	await _frames(3)
	_expect(not is_instance_valid(door), "a monster door opens when the last monster dies")

	ball = _spawn("ball_monster", Vector2(500, REST_Y))
	door = _spawn("monster_door_2", Vector2(300, 400))
	await _frames(3)
	_expect(not is_instance_valid(door), "monster door 2 opens when two monsters remain")
	ball.free()

	door = _spawn("artifact_door", Vector2(300, 400))
	_player.artifacts = 3
	await _frames(5)
	_expect(is_instance_valid(door), "the artifact door stays shut with 3 artifacts")
	_player.artifacts = 4
	await _frames(3)
	_expect(not is_instance_valid(door), "the artifact door opens with 4 artifacts")


func _test_turrets() -> void:
	_new_arena()
	var turret_pos := Vector2(300, 300)
	_spawn("aimer_turret", turret_pos)
	await _frames(130)
	_expect(_shot_log.size() >= 1, "aimer turret fires within about 2 s")
	if _shot_log.size() >= 1:
		var shot: Dictionary = _shot_log[0]
		_expect(shot.enemy, "turret shots are enemy shots")
		_expect(absf(shot.velocity.length() - 350.0) < 1.0, "aimed shots fly at 350, got %.1f" % shot.velocity.length())
		_expect(shot.velocity.x < 0.0, "the shot is aimed toward the player on its left")

	_new_arena()
	_spawn("defense_turret_vertical", Vector2(300, REST_Y))
	await _frames(190)
	_expect(_shot_log.size() >= 1, "defense turret fires within about 3 s")
	if _shot_log.size() >= 1:
		var grenade: Dictionary = _shot_log[0]
		_expect(grenade.gravity_scale == 1.0, "defense turret lobs grenades")
		_expect(grenade.velocity.y <= -500.0 and grenade.velocity.y >= -750.0, "grenades are lobbed upward, vy %.1f" % grenade.velocity.y)


func _test_enemy_shots() -> void:
	_new_arena()
	await _frames(30)
	var ball := _launch(EnemyEnergyBallScene, _player.position + Vector2(-80, 0), Vector2(350, 0))
	await _frames(20)
	_expect(_player.hp == 4, "an enemy energy ball hurts the player, hp %d" % _player.hp)
	_expect(not is_instance_valid(ball), "an enemy energy ball dies on contact")

	var grenade := _launch(EnergyGrenadeScene, Vector2(400, REST_Y - 30.0), Vector2.ZERO)
	var frames := 0
	while is_instance_valid(grenade) and frames < 300:
		await physics_frame
		frames += 1
	_expect(frames > 175 and frames < 215, "a grenade explodes 3 s after landing, took %d frames" % frames)

	grenade = _launch(EnergyGrenadeScene, _player.position + Vector2(0, -60), Vector2.ZERO)
	await _frames(30)
	_expect(not is_instance_valid(grenade), "a grenade explodes at once on the player")
	_expect(_player.hp == 3, "a grenade hurts the player, hp %d" % _player.hp)


func _test_player_death() -> void:
	_new_arena()
	await _frames(30)
	var died := [0]
	_player.died.connect(func() -> void: died[0] += 1)
	_player.hp = 1
	_player.hit()
	_expect(_player.is_dead(), "the player dies at 0 hp")
	Input.action_press("move_right")
	await _frames(30)
	Input.action_release("move_right")
	_expect(absf(_player.linear_velocity.x) < 5.0, "a dead player cannot move")
	_expect(died[0] == 0, "died is not emitted before the death pause ends")
	await _frames(100)
	_expect(died[0] == 1, "died is emitted after about 2 s, count %d" % died[0])
	await _frames(30)
	_expect(died[0] == 1, "died is emitted once")
	_player.revive()
	_expect(_player.hp == _player.max_hp and not _player.is_dead(), "revive restores full hp")


func _test_movers() -> void:
	_new_arena()
	var home := Vector2(300, 300)
	var block := _spawn("hover_block", home)
	var bot := _spawn("jump_bot", Vector2(600, REST_Y))
	var highest := bot.position.y
	for i in 120:
		await physics_frame
		highest = minf(highest, bot.position.y)
	_expect(block.position.distance_to(home) < 2.0, "a hover block holds its position")
	_expect(highest < REST_Y - 20.0, "a jump bot jumps")


func _test_effects() -> void:
	_new_arena()
	var audio: Node = root.get_node("Audio")
	var bot := _spawn("jump_bot", Vector2(300, REST_Y))
	bot.hit()
	_expect(_field.count() == 40, "a dying jump bot emits 40 particles, got %d" % _field.count())
	_expect(audio.is_playing("explode"), "a dying bot plays explode")
	_field.clear()

	var ball := _spawn("ball_monster", Vector2(400, REST_Y))
	ball.hit()
	_expect(_field.count() == 0, "a dying ball monster emits no particles")
	_expect(audio.is_playing("deadAlien"), "a dying ball monster plays deadAlien")

	var flyer := _spawn("fly_bot", Vector2(600, 300))
	flyer.hit()
	_expect(audio.is_playing("hit"), "a monster that survives a hit plays hit")
	await _frames(10)
	_expect(_field.count() > 0, "a fly bot leaves exhaust")
	flyer.free()

	await _frames(30)
	_field.clear()
	var before_jet := Time.get_ticks_msec()
	Input.action_press("jetpack")
	await _frames(10)
	Input.action_release("jetpack")
	_expect(_field.count() > 0, "the jetpack leaves particles")
	# The jet sound is 0.1 s long, so ask when it last started, not whether
	# it is sounding at this instant.
	_expect(audio.last_played_msec("jet") >= before_jet, "the jetpack plays jet")

	var started := [0]
	_player.death_started.connect(func() -> void: started[0] += 1)
	_player.hp = 1
	_player.hit()
	_expect(started[0] == 1, "death_started is emitted when hp reaches zero")

	_new_arena()
	_launch(EnergyGrenadeScene, Vector2(400, REST_Y - 30.0), Vector2.ZERO)
	await _frames(200)
	_expect(_field.count() >= 10, "an exploding grenade bursts into at least 10 particles, got %d" % _field.count())


func _new_arena(player_pos := PLAYER_REST) -> void:
	if _arena != null:
		root.remove_child(_arena)
		_arena.free()
	_shot_log.clear()
	_saves.clear()
	_arena = Node2D.new()
	var floor_body := StaticBody2D.new()
	var floor_shape := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = Vector2(4000, 40)
	floor_shape.shape = rect
	floor_shape.position = Vector2(0, FLOOR_Y + 20.0)
	floor_body.add_child(floor_shape)
	_arena.add_child(floor_body)
	_entities = Node2D.new()
	_arena.add_child(_entities)
	_player = PlayerScene.instantiate()
	_player.position = player_pos
	_player.shot_fired.connect(_add_shot)
	_arena.add_child(_player)
	_field = load("res://effects/particle_field.gd").new()
	_arena.add_child(_field)
	root.add_child(_arena)


func _spawn(file: String, pos: Vector2) -> RigidBody2D:
	var monster: RigidBody2D = load("res://entities/monsters/%s.tscn" % file).instantiate()
	monster.position = pos
	monster.shot_fired.connect(_add_shot)
	monster.save_requested.connect(func(source: Node) -> void: _saves.append(source))
	_entities.add_child(monster)
	return monster


func _add_shot(shot: RigidBody2D) -> void:
	_arena.add_child(shot)
	_shot_log.append({
		"enemy": shot.is_in_group("enemy_shots"),
		"velocity": shot.linear_velocity,
		"gravity_scale": shot.gravity_scale,
	})


func _launch(scene: PackedScene, pos: Vector2, velocity: Vector2) -> RigidBody2D:
	var shot: RigidBody2D = scene.instantiate()
	shot.position = pos
	shot.linear_velocity = velocity
	_arena.add_child(shot)
	return shot


func _frames(count: int) -> void:
	for i in count:
		await physics_frame


func _expect(condition: bool, message: String) -> void:
	if not condition:
		_fail(message)


func _fail(message: String) -> void:
	_failures += 1
	printerr("FAIL: " + message)
