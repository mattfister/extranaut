extends RefCounted
## Everything a save slot remembers.

const VERSION := 1

## The room the player respawns in. Set by save points and powerups. A new
## game's starting room comes from world/planets.gd.
var checkpoint := Vector2i.ZERO
var max_hp := 5
var max_fuel := 2000.0
var gun_level := 1
var artifacts := 0
## Sets of rooms, stored as Vector2i keys with the value true.
var powerups_taken := {}
var visited := {}
var save_points := {}


func to_dict() -> Dictionary:
	return {
		"version": VERSION,
		"checkpoint": [checkpoint.x, checkpoint.y],
		"max_hp": max_hp,
		"max_fuel": max_fuel,
		"gun_level": gun_level,
		"artifacts": artifacts,
		"powerups_taken": _cells_to_array(powerups_taken),
		"visited": _cells_to_array(visited),
		"save_points": _cells_to_array(save_points),
	}


## Returns a Progress, or null if data is not a valid save.
static func from_dict(data: Dictionary) -> RefCounted:
	for key in ["max_hp", "max_fuel", "gun_level", "artifacts"]:
		if not (data.get(key) is float or data.get(key) is int):
			return null
	for key in ["powerups_taken", "visited", "save_points"]:
		if not data.get(key) is Array:
			return null
	if not _is_cell(data.get("checkpoint")):
		return null
	var progress = new()
	progress.checkpoint = _to_cell(data["checkpoint"])
	progress.max_hp = int(data["max_hp"])
	progress.max_fuel = float(data["max_fuel"])
	progress.gun_level = int(data["gun_level"])
	progress.artifacts = int(data["artifacts"])
	progress.powerups_taken = _array_to_cells(data["powerups_taken"])
	progress.visited = _array_to_cells(data["visited"])
	progress.save_points = _array_to_cells(data["save_points"])
	return progress


static func _cells_to_array(cells: Dictionary) -> Array:
	var result := []
	for cell in cells:
		result.append([cell.x, cell.y])
	return result


static func _array_to_cells(array: Array) -> Dictionary:
	var result := {}
	for item in array:
		if _is_cell(item):
			result[_to_cell(item)] = true
	return result


static func _is_cell(value: Variant) -> bool:
	return value is Array and value.size() == 2 and (value[0] is float or value[0] is int) and (value[1] is float or value[1] is int)


static func _to_cell(value: Array) -> Vector2i:
	return Vector2i(int(value[0]), int(value[1]))
