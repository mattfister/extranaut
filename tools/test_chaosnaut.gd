extends SceneTree
## Tests for ChaosBot, ChaosScore and the Chaosnaut arena.
## Run: godot --headless --path . --script res://tools/test_chaosnaut.gd

const SaveGame := preload("res://save/save_game.gd")
const ChaosScore := preload("res://save/chaos_score.gd")

var _failures := 0


func _initialize() -> void:
	_run()


func _run() -> void:
	await process_frame
	SaveGame.directory = "user://test_saves/"
	DirAccess.make_dir_recursive_absolute(SaveGame.directory)
	_test_score()
	await _test_chaos_bot()
	await _test_arena()
	ChaosScore.clear()
	print("chaosnaut test passed" if _failures == 0 else "chaosnaut test FAILED: %d failures" % _failures)
	quit(1 if _failures > 0 else 0)


func _test_score() -> void:
	ChaosScore.clear()
	var none := ChaosScore.read()
	_expect(none.wave == 0 and none.kills == 0, "no best result at first")
	_expect(ChaosScore.submit(3, 5), "the first result is the best")
	_expect(not ChaosScore.submit(2, 9), "a lower wave is not better, whatever the kills")
	_expect(not ChaosScore.submit(3, 5), "an equal result is not better")
	_expect(ChaosScore.submit(3, 6), "more kills on the same wave is better")
	var best := ChaosScore.read()
	_expect(best.wave == 3 and best.kills == 6, "the best result is stored")


func _test_chaos_bot() -> void:
	var holder := Node2D.new()
	root.add_child(holder)
	var bot: RigidBody2D = load("res://entities/monsters/chaos_bot.tscn").instantiate()
	bot.position = Vector2(500, 300)
	holder.add_child(bot)
	var deaths := [0]
	bot.died.connect(func() -> void: deaths[0] += 1)
	await _frames(20)
	_expect(absf(bot.linear_velocity.x + 100.0) < 1.0, "a chaos bot drifts left at 100, got %.1f" % bot.linear_velocity.x)
	_expect(bot.sprite.frame_coords.y == 1, "a calm chaos bot uses sprite row 1")
	_expect(absf(bot.position.y - 300.0) < 200.0, "a chaos bot is not pulled down by gravity")
	bot.angry = true
	await _frames(5)
	_expect(absf(bot.linear_velocity.x + 300.0) < 1.0, "an angry chaos bot drifts left at 300")
	_expect(bot.sprite.frame_coords.y == 2, "an angry chaos bot uses sprite row 2")
	bot.hit()
	_expect(deaths[0] == 1, "a dying monster emits died")
	root.remove_child(holder)
	holder.free()


func _test_arena() -> void:
	ChaosScore.clear()
	var audio: Node = root.get_node("Audio")
	var arena: Node2D = load("res://scenes/chaosnaut.tscn").instantiate()
	root.add_child(arena)
	var player: RigidBody2D = arena.get_node("Player")
	await _frames(5)

	_expect(arena.block_count() == 40, "the arena starts with 40 hover blocks, got %d" % arena.block_count())
	_expect(arena.bot_count() == 0 and arena.wave == 0, "no bots before the first wave")
	_expect(player.gun_level == 3, "the player has gun level 3")
	_expect(player.position.distance_to(Vector2(32, 704)) < 60.0, "the player starts bottom left, at %s" % player.position)
	_expect(audio.current_music() == "chaosNaut", "the arena plays its music")

	# Fuel never runs out.
	Input.action_press("jetpack")
	await _frames(60)
	Input.action_release("jetpack")
	_expect(player.jetpack.fuel > player.jetpack.max_fuel - 200.0, "fuel is refilled every frame")

	# Waves.
	var before := Time.get_ticks_msec()
	arena.next_wave_in = 0.01
	await _frames(3)
	_expect(arena.wave == 1 and arena.bot_count() == 1, "wave 1 spawns one bot, got wave %d and %d bots" % [arena.wave, arena.bot_count()])
	_expect(audio.last_played_msec("newWave") >= before, "a wave plays newWave")
	_expect(arena.next_wave_in > 9.0, "the next wave is 10 s away")
	arena.wave = 3
	arena.next_wave_in = 0.01
	await _frames(3)
	_expect(arena.wave == 4 and arena.bot_count() == 3, "wave 4 spawns two bots, got %d in total" % arena.bot_count())

	# A bot reaching the left edge wraps round and turns angry.
	var bot: RigidBody2D = arena.bots()[0]
	bot.global_position = Vector2(10, 300)
	await _frames(3)
	_expect(bot.global_position.x > 800.0 and bot.angry, "a bot at the left edge wraps to the right and turns angry")

	# Kills are counted and blocks are replaced.
	bot.hit()
	_expect(arena.kills == 1, "killing a bot counts")
	arena.blocks()[0].hit()
	await _frames(3)
	_expect(arena.block_count() == 40, "a destroyed block is replaced")
	_expect(arena.kills == 1, "destroying a block is not a kill")

	# Game over.
	var game_over: CanvasLayer = arena.get_node("GameOver")
	_expect(not game_over.visible, "no game-over screen while alive")
	player.revive()
	player.hp = 1
	player.hit()
	await _frames(130)
	await _settle()
	_expect(game_over.visible and paused, "the game-over screen shows after the death pause")
	_expect(game_over.get_node("Stats").text.contains("Wave 4"), "the game-over screen shows the wave, text: %s" % game_over.get_node("Stats").text)
	_expect(ChaosScore.read().wave == 4 and ChaosScore.read().kills == 1, "the result is stored as the best")
	var finished := [0]
	arena.finished.connect(func() -> void: finished[0] += 1)
	game_over.get_node("Back").pressed.emit()
	await _settle()
	_expect(finished[0] == 1, "Back to Title finishes the mode")
	_expect(not paused, "leaving unpauses the tree")
	root.remove_child(arena)
	arena.free()


## Waits for deferred work, ending between frames, where real button presses
## arrive.
func _settle() -> void:
	await process_frame
	await process_frame
	await physics_frame
	await process_frame


func _frames(count: int) -> void:
	for i in count:
		await physics_frame


func _expect(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		printerr("FAIL: " + message)
