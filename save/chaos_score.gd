extends RefCounted
## The best Chaosnaut result, stored beside the save slots.

const SaveGame := preload("res://save/save_game.gd")
const FILE_NAME := "chaosnaut.json"


static func path() -> String:
	return SaveGame.directory + FILE_NAME


## Returns {"wave": int, "kills": int}, zeros if nothing is stored.
static func read() -> Dictionary:
	var best := {"wave": 0, "kills": 0}
	if not FileAccess.file_exists(path()):
		return best
	var json := JSON.new()
	if json.parse(FileAccess.get_file_as_string(path())) != OK or not json.data is Dictionary:
		return best
	best.wave = int(json.data.get("wave", 0))
	best.kills = int(json.data.get("kills", 0))
	return best


## Stores the result if it beats the best: a higher wave, or the same wave
## with more kills. Returns true if it did.
static func submit(wave: int, kills: int) -> bool:
	var best := read()
	if wave < best.wave or (wave == best.wave and kills <= best.kills):
		return false
	var file := FileAccess.open(path(), FileAccess.WRITE)
	if file == null:
		push_warning("could not write %s" % path())
		return false
	file.store_string(JSON.stringify({"wave": wave, "kills": kills}))
	return true


static func clear() -> void:
	if FileAccess.file_exists(path()):
		DirAccess.remove_absolute(path())
