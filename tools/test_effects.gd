extends SceneTree
## Tests for the Audio autoload, ParticleField and ScreenFx.
## Run: godot --headless --path . --script res://tools/test_effects.gd

const EFFECTS := [
	"shoot", "hit", "jet", "packEmpty", "deadAlien", "explode", "armorUpgrade",
	"jetpackUpgrade", "gunUpgrade", "alienArtifactAcquired", "extranautTitle",
	"intro", "newWave",
]

var _failures := 0


func _initialize() -> void:
	_run()


func _run() -> void:
	await process_frame
	_test_sounds_exist()
	await _test_audio()
	_test_particle_field()
	await _test_screen_fx()
	print("effects test passed" if _failures == 0 else "effects test FAILED: %d failures" % _failures)
	quit(1 if _failures > 0 else 0)


func _test_sounds_exist() -> void:
	var tracks := {"ruinsCore": true, "chaosNaut": true}
	var world = JSON.parse_string(FileAccess.get_file_as_string("res://tools/zorta.json"))
	for room in world.rooms:
		if room.music != null:
			tracks[room.music] = true
	for sound in EFFECTS + tracks.keys():
		_expect(ResourceLoader.exists("res://assets/sounds/%s.ogg" % sound), "sound %s exists" % sound)


func _test_audio() -> void:
	var audio: Node = root.get_node("Audio")
	audio.play("shoot")
	_expect(audio.is_playing("shoot"), "an effect plays")
	_expect(not audio.is_playing("explode"), "other effects are not reported as playing")
	audio.play("shoot")
	_expect(audio.playing_count("shoot") == 1, "an effect is not restarted within the retrigger gap")
	audio.play("no_such_sound")
	_expect(not audio.is_playing("no_such_sound"), "a missing sound is ignored")

	_expect(audio.current_music() == "", "no music at first")
	audio.play_music("zortaSurface")
	_expect(audio.current_music() == "zortaSurface", "music starts")
	_expect(audio.music_player().playing and audio.music_player().stream.loop, "music plays and loops")
	var first: AudioStreamPlayer = audio.music_player()
	audio.play_music("zortaSurface")
	_expect(audio.music_player() == first, "asking for the current track does not restart it")
	audio.play_music("pyriteZone")
	_expect(audio.current_music() == "pyriteZone" and audio.music_player() != first, "a new track takes over on the other player")
	await create_timer(audio.FADE_TIME + 0.3).timeout
	_expect(not first.playing, "the old track stops after the crossfade")
	_expect(is_equal_approx(audio.music_player().volume_db, audio.MUSIC_VOLUME_DB), "the new track reaches full music volume")


func _test_particle_field() -> void:
	var field: Node2D = load("res://effects/particle_field.gd").new()
	root.add_child(field)
	_expect(field.is_in_group("particle_field"), "the field joins its group")
	field.emit("explosion", Vector2(100, 100), 40)
	_expect(field.count() == 40, "emit adds particles")
	field.advance(0.5)
	_expect(field.count() == 40, "explosion particles live at least 0.8 s")
	field.advance(1.1)
	_expect(field.count() == 0, "explosion particles are gone after 1.5 s")

	field.emit("exhaust", Vector2.ZERO, 5)
	field.advance(0.31)
	_expect(field.count() == 0, "exhaust particles live at most 0.3 s")

	field.emit("jet_smoke", Vector2.ZERO, 1)
	var start_speed: float = field.particle_velocity(0).length()
	field.advance(0.5)
	_expect(field.particle_velocity(0).length() < start_speed or start_speed == 0.0, "smoke slows down")

	field.emit("energy", Vector2.ZERO, 10)
	field.clear()
	_expect(field.count() == 0, "clear removes everything")
	root.remove_child(field)
	field.free()


func _test_screen_fx() -> void:
	var fx: CanvasLayer = load("res://effects/screen_fx.gd").new()
	var camera := Camera2D.new()
	root.add_child(camera)
	root.add_child(fx)
	fx.camera = camera
	_expect(fx.is_in_group("screen_fx"), "screen fx joins its group")
	fx.shake(0.5)
	fx.shake(0.2)
	_expect(fx.trauma == 0.5, "a weaker shake does not reduce a stronger one")
	await process_frame
	await process_frame
	_expect(fx.trauma < 0.5 and fx.trauma > 0.0, "shake decays")
	await create_timer(0.5).timeout
	_expect(fx.trauma == 0.0 and camera.offset == Vector2.ZERO, "the camera settles")

	fx.fade_out(0.1)
	await create_timer(0.2).timeout
	_expect(is_equal_approx(fx.overlay_color().a, 1.0), "fade out ends opaque")
	fx.fade_in(0.1)
	await create_timer(0.2).timeout
	_expect(is_zero_approx(fx.overlay_color().a), "fade in ends clear")
	fx.flash()
	_expect(fx.overlay_color().a > 0.0, "flash shows at once")
	await create_timer(0.3).timeout
	_expect(is_zero_approx(fx.overlay_color().a), "flash fades away")
	root.remove_child(fx)
	fx.free()
	camera.queue_free()


func _expect(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		printerr("FAIL: " + message)
