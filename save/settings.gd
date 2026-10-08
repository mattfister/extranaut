extends RefCounted
## Small choices remembered between runs. The file lives beside the save slots.

const SaveGame := preload("res://save/save_game.gd")
const Planets := preload("res://world/planets.gd")


static func path() -> String:
	return SaveGame.directory + "settings.json"


## The planet last chosen on the title, or Zorta.
static func last_planet() -> String:
	if not FileAccess.file_exists(path()):
		return Planets.ZORTA
	var data = JSON.parse_string(FileAccess.get_file_as_string(path()))
	if data is Dictionary and data.get("planet") is String and Planets.exists(data.planet):
		return data.planet
	return Planets.ZORTA


static func set_last_planet(planet: String) -> void:
	var file := FileAccess.open(path(), FileAccess.WRITE)
	if file != null:
		file.store_string(JSON.stringify({"planet": planet}))
