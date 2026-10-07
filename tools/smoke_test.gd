extends SceneTree
## Loads every generated room and checks it against tools/zorta.json.
## Run: godot --headless --path . --script res://tools/smoke_test.gd

const WORLD_JSON := "res://tools/zorta.json"
const LAYERS := ["background", "midground", "foreground"]

var _failures := 0


func _initialize() -> void:
	_run()


func _run() -> void:
	var world = JSON.parse_string(FileAccess.get_file_as_string(WORLD_JSON))
	if world == null:
		_fail("could not read %s" % WORLD_JSON)
		quit(1)
		return
	for data in world.rooms:
		await _check_room(data)
	if _failures == 0:
		print("smoke test passed: %d rooms" % world.rooms.size())
	else:
		print("smoke test FAILED: %d failures" % _failures)
	quit(1 if _failures > 0 else 0)


func _check_room(data: Dictionary) -> void:
	var x := int(data.x)
	var y := int(data.y)
	var path := "res://world/rooms/room_%d_%d.tscn" % [x, y]
	if not ResourceLoader.exists(path):
		_fail("%s is missing" % path)
		return
	var room: Node2D = load(path).instantiate()
	root.add_child(room)
	await physics_frame
	await physics_frame

	_expect(room.grid_pos == Vector2i(x, y), "%s grid_pos is %s" % [path, room.grid_pos])
	var music: String = "" if data.music == null else data.music
	_expect(room.music == music, "%s music is '%s'" % [path, room.music])
	_expect(room.has_player_start == (data.player_start != null), "%s has_player_start" % path)

	var animated_by_layer := {}
	for a in data.animated:
		animated_by_layer[a.layer] = animated_by_layer.get(a.layer, 0) + 1
	for layer_name in LAYERS:
		var layer: TileMapLayer = room.get_node(layer_name.capitalize())
		_expect(
			layer.get_used_cells().size() == data.layers[layer_name].size(),
			"%s %s has %d cells" % [path, layer_name, layer.get_used_cells().size()]
		)
		var animated := room.get_node(layer_name.capitalize() + "Animated")
		_expect(
			animated.get_child_count() == animated_by_layer.get(layer_name, 0),
			"%s %s animated count is %d" % [path, layer_name, animated.get_child_count()]
		)
	_expect(
		room.get_node("Walls").get_child_count() == data.walls.size(),
		"%s wall count is %d" % [path, room.get_node("Walls").get_child_count()]
	)
	_expect(
		room.get_node("Entities").get_child_count() == data.monsters.size(),
		"%s entity count is %d" % [path, room.get_node("Entities").get_child_count()]
	)

	_expect(room.get_node("Foreground").z_index == 10, "%s Foreground z_index" % path)
	_expect(room.get_node("ForegroundAnimated").z_index == 10, "%s ForegroundAnimated z_index" % path)

	root.remove_child(room)
	room.free()


func _expect(condition: bool, message: String) -> void:
	if not condition:
		_fail(message)


func _fail(message: String) -> void:
	_failures += 1
	printerr("FAIL: " + message)
