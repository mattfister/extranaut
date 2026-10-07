extends SceneTree
## Builds world/tileset.tres and world/rooms/room_X_Y.tscn from tools/zorta.json.
## Re-running overwrites the generated scenes.
## Run: godot --headless --path . --script res://tools/import_world.gd

const WORLD_JSON := "res://tools/zorta.json"
const TILESET_PATH := "res://world/tileset.tres"
const ROOMS_DIR := "res://world/rooms"
const MONSTER_SCENE := "res://entities/monsters/%s.tscn"
const SRC_TILE := 16
const ART_SCALE := Vector2(2, 2)
const FOREGROUND_Z := 10
const WALL_RADIUS := 0.5
const LAYERS := ["background", "midground", "foreground"]

const RoomScript := preload("res://world/room.gd")
const AnimatedTileScript := preload("res://world/animated_tile.gd")
const MonsterSpawnScript := preload("res://world/monster_spawn.gd")


func _init() -> void:
	quit(_run())


func _run() -> int:
	var world = JSON.parse_string(FileAccess.get_file_as_string(WORLD_JSON))
	if world == null:
		printerr("could not read %s" % WORLD_JSON)
		return 1
	DirAccess.make_dir_recursive_absolute(ROOMS_DIR)
	var tileset := _build_tileset(world.sheets)
	for data in world.rooms:
		var room := _build_room(data, tileset)
		var packed := PackedScene.new()
		var err := packed.pack(room)
		if err == OK:
			err = ResourceSaver.save(packed, "%s/room_%d_%d.tscn" % [ROOMS_DIR, int(data.x), int(data.y)])
		room.free()
		if err != OK:
			printerr("failed to save room %d,%d: %s" % [int(data.x), int(data.y), error_string(err)])
			return 1
	print("imported %d rooms" % world.rooms.size())
	return 0


func _build_tileset(sheets: Array) -> TileSet:
	var tileset := TileSet.new()
	tileset.tile_size = Vector2i(SRC_TILE, SRC_TILE)
	for i in sheets.size():
		var source := TileSetAtlasSource.new()
		source.texture = load("res://assets/sprites/%s.png" % sheets[i])
		source.texture_region_size = Vector2i(SRC_TILE, SRC_TILE)
		var grid := source.get_atlas_grid_size()
		for y in grid.y:
			for x in grid.x:
				source.create_tile(Vector2i(x, y))
		tileset.add_source(source, i)
	ResourceSaver.save(tileset, TILESET_PATH)
	# Reload so room scenes reference the saved file instead of embedding a copy.
	return load(TILESET_PATH)


func _build_room(data: Dictionary, tileset: TileSet) -> Node2D:
	var room := Node2D.new()
	room.set_script(RoomScript)
	room.name = "Room_%d_%d" % [int(data.x), int(data.y)]
	room.grid_pos = Vector2i(int(data.x), int(data.y))
	room.music = "" if data.music == null else data.music
	room.has_player_start = data.player_start != null
	if data.player_start != null:
		room.player_start = Vector2(data.player_start[0], data.player_start[1])

	for layer_name in LAYERS:
		var layer := TileMapLayer.new()
		layer.name = layer_name.capitalize()
		layer.tile_set = tileset
		layer.scale = ART_SCALE
		for t in data.layers[layer_name]:
			layer.set_cell(Vector2i(int(t[0]), int(t[1])), int(t[2]), Vector2i(int(t[3]), int(t[4])))
		_add(room, room, layer)

		var animated := Node2D.new()
		animated.name = layer_name.capitalize() + "Animated"
		if layer_name == "foreground":
			layer.z_index = FOREGROUND_Z
			animated.z_index = FOREGROUND_Z
		_add(room, room, animated)
		for a in data.animated:
			if a.layer == layer_name:
				_add(room, animated, _build_animated_tile(a))

		if layer_name == "midground":
			_add(room, room, _build_entities(data.monsters))

	_add(room, room, _build_walls(data.walls))
	return room


func _build_animated_tile(a: Dictionary) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.set_script(AnimatedTileScript)
	var texture: Texture2D = load("res://assets/animations/%s.png" % a.sheet)
	sprite.texture = texture
	sprite.centered = false
	sprite.hframes = texture.get_width() / SRC_TILE
	sprite.vframes = texture.get_height() / SRC_TILE
	sprite.frame_coords = Vector2i(0, int(a.row))
	sprite.scale = ART_SCALE
	sprite.position = Vector2(a.pos[0], a.pos[1])
	sprite.name = "%s_%d_%d" % [a.sheet, int(a.pos[0]), int(a.pos[1])]
	return sprite


func _build_entities(monsters: Array) -> Node2D:
	var entities := Node2D.new()
	entities.name = "Entities"
	for i in monsters.size():
		var kind: String = monsters[i][0]
		var scene_path := MONSTER_SCENE % kind.to_snake_case()
		var node: Node2D
		if ResourceLoader.exists(scene_path):
			node = load(scene_path).instantiate()
		else:
			node = Marker2D.new()
			node.set_script(MonsterSpawnScript)
			node.kind = kind
		node.name = "%s%d" % [kind, i]
		node.position = Vector2(monsters[i][1], monsters[i][2])
		entities.add_child(node)
	return entities


func _build_walls(walls: Array) -> StaticBody2D:
	var body := StaticBody2D.new()
	body.name = "Walls"
	var material := PhysicsMaterial.new()
	material.friction = 0.5
	body.physics_material_override = material
	for w in walls:
		var a := Vector2(w[0], w[1])
		var b := Vector2(w[2], w[3])
		# Thin capsules, not SegmentShape2D: segments report a sideways contact
		# where a wall meets a floor, which stops bodies dead at ledges.
		var capsule := CapsuleShape2D.new()
		capsule.radius = WALL_RADIUS
		capsule.height = a.distance_to(b) + WALL_RADIUS * 2.0
		var shape := CollisionShape2D.new()
		shape.shape = capsule
		shape.position = (a + b) / 2.0
		# A capsule's long axis is its local Y axis.
		shape.rotation = (b - a).angle() - PI / 2.0
		body.add_child(shape, true)
	return body


## Adds node under parent and makes it, and any children it already has,
## owned by the room so that PackedScene.pack() saves them.
func _add(room: Node2D, parent: Node, node: Node) -> void:
	parent.add_child(node, true)
	node.owner = room
	for child in node.get_children():
		child.owner = room
