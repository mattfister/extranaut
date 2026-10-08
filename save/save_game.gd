extends RefCounted
## Reads and writes save slots as JSON files. Each planet has its own slots.

const Progress := preload("res://save/progress.gd")
const Planets := preload("res://world/planets.gd")
const SLOTS := [1, 2, 3]

## Where slot files live. Tests point this somewhere else.
static var directory := "user://"


static func path(planet: String, slot: int) -> String:
	return "%s%s%d.json" % [directory, Planets.DATA[planet].save_prefix, slot]


static func exists(planet: String, slot: int) -> bool:
	return FileAccess.file_exists(path(planet, slot))


## Returns the slot's Progress, or null if the slot is empty or unreadable.
static func read(planet: String, slot: int) -> RefCounted:
	if not exists(planet, slot):
		return null
	var json := JSON.new()
	if json.parse(FileAccess.get_file_as_string(path(planet, slot))) != OK:
		return null
	if not json.data is Dictionary:
		return null
	return Progress.from_dict(json.data)


static func write(planet: String, slot: int, progress: RefCounted) -> bool:
	var file := FileAccess.open(path(planet, slot), FileAccess.WRITE)
	if file == null:
		push_warning("could not write %s" % path(planet, slot))
		return false
	file.store_string(JSON.stringify(progress.to_dict()))
	return true


static func delete(planet: String, slot: int) -> void:
	if exists(planet, slot):
		DirAccess.remove_absolute(path(planet, slot))
