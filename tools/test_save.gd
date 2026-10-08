extends SceneTree
## Tests for Progress and SaveGame.
## Run: godot --headless --path . --script res://tools/test_save.gd

const Progress := preload("res://save/progress.gd")
const SaveGame := preload("res://save/save_game.gd")
const Planets := preload("res://world/planets.gd")
const Settings := preload("res://save/settings.gd")

var _failures := 0


func _init() -> void:
	_test_progress()
	_test_save_files()
	print("save test passed" if _failures == 0 else "save test FAILED: %d failures" % _failures)
	quit(1 if _failures > 0 else 0)


func _test_progress() -> void:
	var fresh = Planets.new_progress("zorta")
	_expect(fresh.checkpoint == Vector2i(4, 2), "a new Zorta game starts in room 4,2")
	_expect(Planets.new_progress("korvax").checkpoint == Vector2i(2, 0), "a new Korvax game starts in room 2,0")
	_expect(fresh.max_hp == 5 and fresh.max_fuel == 2000.0, "a new game has 5 hp and 2000 fuel")
	_expect(fresh.gun_level == 1 and fresh.artifacts == 0, "a new game has gun level 1 and no artifacts")

	var progress := Progress.new()
	progress.checkpoint = Vector2i(7, 3)
	progress.max_hp = 7
	progress.max_fuel = 3500.0
	progress.gun_level = 3
	progress.artifacts = 2
	progress.powerups_taken[Vector2i(0, 0)] = true
	progress.visited[Vector2i(4, 2)] = true
	progress.visited[Vector2i(5, 2)] = true
	progress.save_points[Vector2i(4, 2)] = true
	# Through JSON text, as a real save goes.
	var copy = Progress.from_dict(JSON.parse_string(JSON.stringify(progress.to_dict())))
	_expect(copy != null, "a saved dictionary loads")
	if copy != null:
		_expect(copy.checkpoint == Vector2i(7, 3), "checkpoint survives")
		_expect(copy.max_hp == 7 and copy.max_fuel == 3500.0, "hp and fuel survive")
		_expect(copy.gun_level == 3 and copy.artifacts == 2, "gun level and artifacts survive")
		_expect(copy.powerups_taken.has(Vector2i(0, 0)) and copy.powerups_taken.size() == 1, "powerups taken survive")
		_expect(copy.visited.has(Vector2i(5, 2)) and copy.visited.size() == 2, "visited rooms survive")
		_expect(copy.save_points.has(Vector2i(4, 2)), "save points survive")

	_expect(Progress.from_dict({}) == null, "an empty dictionary is rejected")
	var broken := progress.to_dict()
	broken["checkpoint"] = "nowhere"
	_expect(Progress.from_dict(broken) == null, "a malformed checkpoint is rejected")


func _test_save_files() -> void:
	SaveGame.directory = "user://test_saves/"
	DirAccess.make_dir_recursive_absolute(SaveGame.directory)
	for slot in SaveGame.SLOTS:
		for planet: String in Planets.ORDER:
			SaveGame.delete(planet, slot)
	_expect(not SaveGame.exists("zorta", 1), "an unused slot does not exist")
	_expect(SaveGame.read("zorta", 1) == null, "an unused slot reads as null")

	var progress := Progress.new()
	progress.artifacts = 3
	_expect(SaveGame.write("zorta", 2, progress), "writing a slot succeeds")
	_expect(SaveGame.exists("zorta", 2) and not SaveGame.exists("zorta", 1), "only the written slot exists")
	var loaded = SaveGame.read("zorta", 2)
	_expect(loaded != null and loaded.artifacts == 3, "a written slot reads back")

	var file := FileAccess.open(SaveGame.path("zorta", 3), FileAccess.WRITE)
	file.store_string("{ this is not json")
	file.close()
	_expect(SaveGame.read("zorta", 3) == null, "a corrupt slot reads as null")

	SaveGame.delete("zorta", 2)
	SaveGame.delete("zorta", 3)
	_expect(not SaveGame.exists("zorta", 2), "a deleted slot is gone")

	_expect(SaveGame.path("zorta", 1).ends_with("save_1.json"), "Zorta keeps the original file names")
	_expect(SaveGame.path("korvax", 1).ends_with("save_korvax_1.json"), "Korvax has its own files")
	SaveGame.write("korvax", 1, Planets.new_progress("korvax"))
	_expect(SaveGame.exists("korvax", 1) and not SaveGame.exists("zorta", 1), "planets do not share slots")
	loaded = SaveGame.read("korvax", 1)
	_expect(loaded != null and loaded.checkpoint == Vector2i(2, 0), "a Korvax slot reads back")
	SaveGame.delete("korvax", 1)
	_expect(not SaveGame.exists("korvax", 1), "a deleted Korvax slot is gone")

	_expect(Settings.last_planet() == "zorta", "the first planet offered is Zorta")
	Settings.set_last_planet("korvax")
	_expect(Settings.last_planet() == "korvax", "the last planet is remembered")
	file = FileAccess.open(Settings.path(), FileAccess.WRITE)
	file.store_string(JSON.stringify({"planet": "pluto"}))
	file.close()
	_expect(Settings.last_planet() == "zorta", "an unknown planet falls back to Zorta")
	DirAccess.remove_absolute(Settings.path())


func _expect(condition: bool, message: String) -> void:
	if not condition:
		_failures += 1
		printerr("FAIL: " + message)
