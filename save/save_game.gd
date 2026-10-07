extends RefCounted
## Reads and writes save slots as JSON files.

const Progress := preload("res://save/progress.gd")
const SLOTS := [1, 2, 3]

## Where slot files live. Tests point this somewhere else.
static var directory := "user://"


static func path(slot: int) -> String:
	return "%ssave_%d.json" % [directory, slot]


static func exists(slot: int) -> bool:
	return FileAccess.file_exists(path(slot))


## Returns the slot's Progress, or null if the slot is empty or unreadable.
static func read(slot: int) -> RefCounted:
	if not exists(slot):
		return null
	var json := JSON.new()
	if json.parse(FileAccess.get_file_as_string(path(slot))) != OK:
		return null
	if not json.data is Dictionary:
		return null
	return Progress.from_dict(json.data)


static func write(slot: int, progress: RefCounted) -> bool:
	var file := FileAccess.open(path(slot), FileAccess.WRITE)
	if file == null:
		push_warning("could not write %s" % path(slot))
		return false
	file.store_string(JSON.stringify(progress.to_dict()))
	return true


static func delete(slot: int) -> void:
	if exists(slot):
		DirAccess.remove_absolute(path(slot))
